#!/usr/bin/env python3
"""Round-trip check of the AI learning loop (DESIGN 19.2, AI_MASTER_PLAN): did every layer leave evidence?

Reads one or more batch support dirs (each has Logs/ with debug.log, cameo-ai-matches.jsonl,
cameo-ai-missions.jsonl, cameo-ai-situations.jsonl) and prints one PASS/WARN/FAIL row per layer with the
evidence count: load, perception, missions, ownership, order gate, outcomes, execution, storm, write-back, team, fog, learning, tools.
Exit 1 on any FAIL. A genericbot player is any player whose bot_type is not a reference bot (classic, classic_hard).

Usage:
    python tools/ai/round_trip_check.py <support-dir> [<support-dir> ...]

Perception note: BotSituation writes no debug line, so the master AI's snapshots are counted from the
situation archive (cameo-ai-situations.jsonl), which AiSituationLogWriter fills from the same snapshots.
"""
from __future__ import annotations

import contextlib
import io
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

import ab_summary  # noqa: E402
import fit_arsenal_priors  # noqa: E402
import mission_story  # noqa: E402

REFERENCE_BOTS = fit_arsenal_priors.REFERENCE_BOTS
PASS, WARN, FAIL = "PASS", "WARN", "FAIL"


def logs_of(dirs: list[pathlib.Path]) -> list[pathlib.Path]:
    return [d / "Logs" for d in dirs if (d / "Logs").is_dir()]


def debug_lines(dirs: list[pathlib.Path]) -> list[str]:
    out = []
    for logs in logs_of(dirs):
        f = logs / "debug.log"
        if f.exists():
            out.extend(f.read_text(encoding="utf-8", errors="replace").splitlines())
    return out


def jsonl(dirs: list[pathlib.Path], name: str) -> list[dict]:
    rows = []
    for logs in logs_of(dirs):
        rows.extend(fit_arsenal_priors.read_jsonl(logs / name))
    return rows


def generic_players(matches: list[dict]) -> list[dict]:
    return [m for m in matches if (m.get("player") or {}).get("bot_type") not in REFERENCE_BOTS]


def count_sum(matches: list[dict], block: str, key: str) -> int:
    return sum(m[block].get(key, 0) for m in matches
               if isinstance(m.get(block), dict) and isinstance(m[block].get(key), int))


def run_quietly(fn, *args):
    with contextlib.redirect_stdout(io.StringIO()):
        return fn(*args)


def check(dirs: list[pathlib.Path]) -> list[tuple[str, str, str]]:
    lines = debug_lines(dirs)
    matches = jsonl(dirs, "cameo-ai-matches.jsonl")
    generic = generic_players(matches)
    rows: list[tuple[str, str, str]] = []

    # 1. load
    names = {m["player"].get("name") for m in generic if m.get("player")}
    watchdog = {n for n in names if any("LC5 ownership watchdog active" in ln and f"AI {n}:" in ln for ln in lines)}
    blocks = sum(1 for m in generic if isinstance(m.get("ownership"), dict) and isinstance(m.get("order_gate"), dict))
    ok = bool(generic) and watchdog == names and blocks == len(generic)
    rows.append(("load", PASS if ok else FAIL,
                 f"{len(watchdog)}/{len(names)} genericbot players with the LC5 line, "
                 f"{blocks}/{len(generic)} records with ownership+order_gate"))

    # 2. perception / situation
    situations = jsonl(dirs, "cameo-ai-situations.jsonl")
    rows.append(("perception", PASS if situations else FAIL, f"{len(situations)} situation snapshot(s)"))

    # 3. missions
    missions = jsonl(dirs, "cameo-ai-missions.jsonl")
    pub = [r for r in missions if r.get("event") == "PUBLISHED" or str(r.get("state", "")).upper() == "COMMITTED"]
    rows.append(("missions", PASS if pub else FAIL, f"{len(pub)} PUBLISHED/COMMITTED record(s) of {len(missions)}"))

    # 4. ownership
    leases = sum(1 for ln in lines if "LC1 leases" in ln)
    double = count_sum(generic, "ownership", "double_owner")
    state = FAIL if not leases else WARN if double else PASS
    rows.append(("ownership", state, f"{leases} LC1 lease line(s), double_owner={double}"))

    # 5. order gate
    missing = [m for m in generic if not isinstance(m.get("order_gate"), dict)]
    refused, crossed = count_sum(generic, "order_gate", "refused"), count_sum(generic, "order_gate", "crossed")
    state = FAIL if missing or not generic else WARN if refused or crossed else PASS
    rows.append(("order gate", state,
                 f"{len(generic) - len(missing)}/{len(generic)} records with the block, refused={refused}, crossed={crossed}"))

    # 6. outcomes — an attempt still open at match end is truncation, not an ownership bug: only count
    # it dangling if the executor went quiet long before the match's last mission record.
    last_tick = max((r.get("tick") or 0) for r in missions) if missions else 0
    quiet_ticks = 5000
    dangling = in_flight = attempts = 0
    for _uid, _recs, ordered in mission_story.story([str(d) for d in dirs]):
        for _mid, m in ordered:
            for trans in m["attempts"].values():
                attempts += 1
                if not mission_story.is_terminal(trans[-1]):
                    if last_tick - (trans[-1].get("tick") or 0) > quiet_ticks:
                        dangling += 1
                    else:
                        in_flight += 1
    rows.append(("outcomes", FAIL if dangling else PASS,
                 f"{attempts} attempt(s), {dangling} dangling, {in_flight} in flight at match end"))

    # 6b. execution coverage — a published card with no attempt, no denial and no terminal event
    # that sat open past the executors' resolution horizon was produced but never consumed
    # (provider dead-end; unaffordable/unreachable cards legitimately sit open). Cards younger
    # than the horizon at the last record are in-flight work, same grace as open attempts.
    open_grace_ticks = 7500
    last_tick_of = {}
    for r in missions:
        g = r.get("game_uid")
        last_tick_of[g] = max(last_tick_of.get(g, 0), r.get("tick") or 0)
    published_tick = {(r.get("game_uid"), r.get("mission_id")): r.get("tick") or 0
                      for r in missions if r.get("event") == "PUBLISHED"}
    closed_or_taken = {(r.get("game_uid"), r.get("mission_id")) for r in missions
                       if r.get("event") in ("DENIED", "DORMANT") or (r.get("event") is None and r.get("state"))}
    unclaimed = [m for g, m in published_tick
                 if (g, m) not in closed_or_taken and last_tick_of.get(g, 0) - published_tick[g, m] > open_grace_ticks]
    live_at_end = [m for g, m in published_tick
                   if (g, m) not in closed_or_taken and last_tick_of.get(g, 0) - published_tick[g, m] <= open_grace_ticks]
    rows.append(("execution", WARN if unclaimed else PASS,
                 f"{len(unclaimed)} published card(s) dead-ended past the {open_grace_ticks}t open horizon, "
                 f"{len(live_at_end)} still live at match end (of {len(published_tick)})"))

    # 6c. republish storm — consecutive bleeding closes on the same mission arriving FASTER than a sane
    # backoff would allow. Executor-agnostic: catches the killbox pattern (claim -> walkers die ->
    # republish -> repeat) wherever it appears, not just garrison contests. GC-1's ContestRetryCooldownTicks
    # spaces retries to >=2500t per streak step, so rate, not raw streak, is the suicide measure.
    bleed_reasons = {"lost_units", "x_contest_lost", "stuck", "timeout"}
    storm_gap_ticks = 2000
    per_mission: dict = {}
    for r in missions:
        if r.get("record_kind") == "attempt" or r.get("event") in ("DORMANT",):
            per_mission.setdefault((r.get("game_uid"), r.get("mission_id")), []).append(
                (r.get("tick") or 0, r.get("reason")))
    worst = None
    storms = 0
    for (_g, _mid), evs in per_mission.items():
        evs.sort(key=lambda e: e[0])
        streak = 0
        last_bleed = None
        stormed = False
        for t, reason in evs:
            if reason in bleed_reasons:
                if last_bleed is None or t - last_bleed <= storm_gap_ticks:
                    streak += 1
                else:
                    streak = 1  # slow retry after a backoff is persistence, not a storm
                last_bleed = t
                if streak >= 3:
                    stormed = True
                    if worst is None or streak > worst[0]:
                        worst = (streak, _mid)
            elif reason:
                streak = 0
                last_bleed = None
        if stormed:
            storms += 1
    detail = f"{storms} mission(s) with >=3 fast-consecutive bleeding closes"
    if worst:
        detail += f" (worst {worst[1]} x{worst[0]})"
    rows.append(("storm", WARN if storms else PASS, detail))

    # 7. write-back — dormant-shelf events only become expected once cards exist; a match with
    # no published cards shelves nothing (team matches can run entirely on attempt records).
    shelf = [r for r in missions if r.get("record_kind") == "mission" and r.get("event") in ("DORMANT", "REOPENED")]
    rows.append(("write-back", WARN if not shelf and published_tick else PASS,
                 f"{len(shelf)} DORMANT/REOPENED event(s)"))

    # 7b. team — a match with >=2 genericbot players on one side should leave SOME team-stack
    # artifact: an assist/defend answer, a superseded claim close, or a shared secure push.
    # Zero artifacts on a team game means the blackboard/election path never fired at all.
    team_games = {m["game_uid"] for m in generic
                  if any(a.get("is_bot") for a in (m.get("allies") or []))}
    team_artifacts = {r.get("game_uid") for r in missions
                      if str(r.get("mission_id", "")).startswith(("assist_answer:", "defend_answer:", "secure:"))
                      or r.get("reason") == "superseded"}
    silent = team_games - team_artifacts
    rows.append(("team", WARN if silent else PASS,
                 f"{len(team_games)} team game(s), {len(team_games) - len(silent)} with team-stack artifacts"
                 + (f" — silent: {sorted(silent)}" if silent else "")))

    # 8. fog
    violations = sum(1 for ln in lines if "FOGCANARY-VIOLATION" in ln)
    rows.append(("fog", FAIL if violations else PASS, f"{violations} FOGCANARY-VIOLATION line(s)"))

    # 9. learning
    learned = [ln for ln in lines if "LEARNED priors:" in ln]
    try:
        fit = fit_arsenal_priors.fit([d for d in dirs if d.is_dir()])
        fit_note = f"fit() over {fit['matches']} match(es)"
        fit_ok = True
    except Exception as e:  # any failure of the offline fit is the finding
        fit_note, fit_ok = f"fit() raised {type(e).__name__}: {e}", False
    if not fit_ok:
        state = FAIL
    elif not learned or any("no priors" in ln for ln in learned):
        state = WARN
    else:
        state = PASS
    rows.append(("learning", state, f"{len(learned)} LEARNED line(s), {fit_note}"))

    # 10. tools
    failures = []
    for label, fn in (("ab_summary", ab_summary.main), ("mission_story", mission_story.main)):
        try:
            run_quietly(fn, [str(d) for d in dirs])
        except Exception as e:
            failures.append(f"{label} raised {type(e).__name__}: {e}")
    rows.append(("tools", FAIL if failures else PASS, "; ".join(failures) or "ab_summary and mission_story ran"))
    return rows


def main(argv: list[str]) -> int:
    dirs = [pathlib.Path(a) for a in argv]
    if not dirs:
        print(__doc__)
        return 2
    rows = check(dirs)
    print("| layer | result | evidence |")
    print("|---|---|---|")
    for layer, state, evidence in rows:
        print(f"| {layer} | {state} | {evidence} |")
    return 1 if any(s == FAIL for _, s, _ in rows) else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
