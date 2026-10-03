"""fight_report — condense A/B batch logs into the decisive fights, for a human or an LLM analyst.

The offline analyst (DESIGN.md §19.2, AI_DEEP_RESEARCH.md §6.4) reads THIS, not the raw JSONL:
a match log is tens of thousands of lines, the decision that lost it is a few hundred ticks. Per
match it prints the outcome, the economy and trade totals, and the DECISIVE WINDOW — the stretch of
`stats.stats_timeline` where the focus bot's kills-minus-deaths moved the most — with what the bot
believed and did around it (posture, urgency, mission, enemy pressure at home) and which roles took
the losses (`own.losses_by_role` delta, home vs away).

    python tools/ai/fight_report.py <batch-dir> [<batch-dir> ...] [--bot hard] [--window 2]

A batch dir is a `--support-dir` of `run_ai_match_batch.py` (it holds `Logs/`). Needs the #617
telemetry (`stats_timeline`, `losses_by_role`); older records print totals only.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys


def read_jsonl(path: pathlib.Path) -> list[dict]:
    if not path.exists():
        return []
    rows = []
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.strip()
        if line:
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                pass
    return rows


def timeline(record: dict) -> list[dict]:
    stats = record.get("stats") or {}
    fields = (stats.get("stats_timeline_fields") or "").split(",")
    return [dict(zip(fields, row)) for row in stats.get("stats_timeline") or [] if len(row) == len(fields)]


def decisive_window(rows: list[dict], width: int) -> tuple[int, int, int] | None:
    """(start index, end index, net swing) of the width-sample stretch with the largest |d(kills - deaths)|."""
    if len(rows) <= width:
        return None
    best = None
    for i in range(len(rows) - width):
        a, b = rows[i], rows[i + width]
        net = (b["kills_cost"] - a["kills_cost"]) - (b["deaths_cost"] - a["deaths_cost"])
        if best is None or abs(net) > abs(best[2]):
            best = (i, i + width, net)
    return best


def snapshot_at(situations: list[dict], tick: int) -> dict | None:
    before = [s for s in situations if s.get("tick", 0) <= tick]
    return before[-1] if before else (situations[0] if situations else None)


def role_delta(a: dict | None, b: dict | None, key: str) -> dict[str, int]:
    if not a or not b:
        return {}
    ra = (a.get("own") or {}).get(key) or {}
    rb = (b.get("own") or {}).get(key) or {}
    return {k: rb.get(k, 0) - ra.get(k, 0) for k in sorted(set(ra) | set(rb)) if rb.get(k, 0) - ra.get(k, 0)}


def describe(snap: dict | None) -> str:
    if not snap:
        return "no situation snapshot"
    own = snap.get("own") or {}
    enemy = (snap.get("enemies") or [{}])[0]
    mission = snap.get("mission")
    mission = mission.get("type") if isinstance(mission, dict) else mission
    return (f"posture {snap.get('personality_current')}, urgency {snap.get('urgency')}, mission {mission}, "
            f"own army {own.get('army_value')} in {own.get('squad_count')} squads, "
            f"enemy army seen {enemy.get('army_value')}, enemy pressure at home {enemy.get('pressure_value')}"
            + (f", predicted ratio {own.get('combat_ratio_pct') / 100:.2f} (with defences {own.get('combat_ratio_defended_pct', 0) / 100:.2f})"
               if own.get("combat_ratio_pct") is not None else ""))


def report(batch_dirs: list[pathlib.Path], bot: str, width: int) -> str:
    out = []
    for d in batch_dirs:
        matches = read_jsonl(d / "Logs" / "cameo-ai-matches.jsonl")
        situations = read_jsonl(d / "Logs" / "cameo-ai-situations.jsonl")
        games: dict[str, dict[str, dict]] = {}
        for r in matches:
            games.setdefault(r.get("game_uid", ""), {})[(r.get("player") or {}).get("bot_type")] = r
        for uid, by_bot in games.items():
            me = by_bot.get(bot)
            if not me:
                continue
            foe = next((r for k, r in by_bot.items() if k != bot), None)
            st, fs = me.get("stats") or {}, (foe or {}).get("stats") or {}
            p = me.get("player") or {}
            out.append(f"## {d.name} · game {uid[:8]} · {bot} {p.get('outcome')} vs "
                       f"{((foe or {}).get('player') or {}).get('bot_type')} · {me.get('duration_ticks')} ticks · home {p.get('home')}")
            out.append(f"- trade: killed {st.get('kills_cost')} / lost {st.get('deaths_cost')} "
                       f"(K/D {st.get('kills_cost', 0) / max(1, st.get('deaths_cost', 0)):.2f}); "
                       f"earned {st.get('resources_earned')} vs {fs.get('resources_earned')}; "
                       f"buildings killed/lost {st.get('buildings_killed')}/{st.get('buildings_lost')}")
            rows = timeline(me)
            win = decisive_window(rows, width)
            if not win:
                out.append("- no stats_timeline (record predates #617)\n")
                continue
            i, j, net = win
            a, b = rows[i], rows[j]
            foe_rows = {r["tick"]: r for r in timeline(foe)} if foe else {}
            fa, fb = foe_rows.get(a["tick"], {}), foe_rows.get(b["tick"], {})
            out.append(f"- decisive window ticks {a['tick']}–{b['tick']}: net {'+' if net >= 0 else ''}{net} "
                       f"(killed {b['kills_cost'] - a['kills_cost']}, lost {b['deaths_cost'] - a['deaths_cost']}); "
                       f"army {a['army_value']}→{b['army_value']} vs enemy {fa.get('army_value', '?')}→{fb.get('army_value', '?')}")
            mine = [s for s in situations if s.get("game_uid") == uid and s.get("player") == p.get("name")]
            sa, sb = snapshot_at(mine, a["tick"]), snapshot_at(mine, b["tick"])
            out.append(f"- before: {describe(sa)}")
            out.append(f"- after:  {describe(sb)}")
            lost = role_delta(sa, sb, "losses_by_role")
            away = role_delta(sa, sb, "away_losses_by_role")
            if lost:
                parts = [f"{k} {v} ({100 * away.get(k, 0) // max(1, v)}% away)" for k, v in sorted(lost.items(), key=lambda kv: -kv[1])]
                out.append("- losses by role in the window: " + ", ".join(parts))
            out.append("")
    return "\n".join(out) if out else "no matches with that bot type"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("batch_dirs", nargs="+", type=pathlib.Path)
    ap.add_argument("--bot", default="hard", help="the bot to analyse (default: hard, the Frankenstein)")
    ap.add_argument("--window", type=int, default=2, help="decisive window width in stats_timeline samples (default 2 = 1500 ticks)")
    args = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")
    print(report(args.batch_dirs, args.bot, max(1, args.window)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
