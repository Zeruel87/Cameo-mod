#!/usr/bin/env python3
"""Tell each mission's story from the mission-card archive (MC2, AI_MISSION_CARDS §3).

Reads cameo-ai-missions.jsonl written by AiMissionLogWriter (schema `mission-card/1`;
tools/ai/run_ai_match_batch.py collects it in <support-dir>/Logs/). Post-#691 there are
two record kinds on the same line stream (fransotto's boundary):

  record_kind="mission" — mission-level events: PUBLISHED / DENIED / DORMANT / REOPENED
                          (the dormant shelf, visible as mission state, not an attempt)
  record_kind="attempt" — attempt transitions: COMMITTED / PROGRESSING / STALLED / RECOVER /
                          SUCCESS / FAILED / RELEASED  (an attempt exists only from COMMIT)

For every match the tool replays each mission as a short story — the mission-event line,
then each attempt chain ordered by tick with the executor named on every transition —
then the per-type success rate, and finally the attempts that never reached a terminal
state: those are the ownership bugs (an executor went quiet and the last line says which).

Usage:
    python tools/ai/mission_story.py <support-dir-or-jsonl> [...] [--match <game_uid>] [--mission <id>]

The archive is record-only (DESIGN §21.1): the game never reads it back, so this tool is the
whole read path. `terminal` comes from the writer; the name set below is only the fallback.
Records without `record_kind` are pre-#691: every line is an attempt transition.
"""
import collections
import json
import pathlib
import sys

TERMINAL_STATES = {"DENIED", "SUCCESS", "FAILED", "RELEASED", "ABANDONED"}


def records(paths: list[str]):
    for arg in paths:
        p = pathlib.Path(arg)
        files = [p] if p.is_file() else sorted(p.rglob("cameo-ai-missions.jsonl"))
        for f in files:
            for line in f.read_text(encoding="utf-8").splitlines():
                if line.strip():
                    yield json.loads(line)


def is_terminal(rec: dict) -> bool:
    if "terminal" in rec:
        return bool(rec["terminal"])
    return str(rec.get("state", "")).upper() in TERMINAL_STATES


def state_line(r: dict) -> str:
    s = f"{r.get('state', '?')}@{r.get('tick', '?')}"
    if r.get("reason"):
        s += f" {r['reason']}"
    return s


def event_line(r: dict) -> str:
    s = f"{r.get('event', '?')}@{r.get('tick', '?')}"
    if r.get("reason"):
        s += f" {r['reason']}"
    return s


def story(paths: list[str], match=None, mission=None):
    """Group into games -> missions -> (events, attempts), tick-ordered."""
    games = collections.defaultdict(list)
    for r in records(paths):
        if match is not None and r.get("game_uid") != match:
            continue
        if mission is not None and r.get("mission_id") != mission:
            continue
        games[r.get("game_uid")].append(r)

    out = []
    for uid, recs in games.items():
        missions = collections.defaultdict(lambda: {"events": [], "attempts": collections.defaultdict(list)})
        for r in recs:
            m = missions[r.get("mission_id")]
            if r.get("record_kind") == "mission":
                m["events"].append(r)
            else:
                # "attempt" kind, or pre-#691 records with no kind at all
                m["attempts"][r.get("attempt")].append(r)
        ordered = []
        for mid, m in missions.items():
            m["events"].sort(key=lambda r: r.get("tick", 0))
            m["attempts"] = {a: sorted(rs, key=lambda r: r.get("tick", 0))
                             for a, rs in sorted(m["attempts"].items(), key=lambda kv: kv[0] or 0)}
            ordered.append((mid, m))
        out.append((uid, recs, ordered))
    return out


def main(argv: list[str]) -> int:
    paths, match, mission = [], None, None
    it = iter(argv)
    for arg in it:
        if arg == "--match":
            match = next(it, None)
        elif arg == "--mission":
            mission = next(it, None)
        else:
            paths.append(arg)
    if not paths:
        print(__doc__)
        return 2

    games = story(paths, match, mission)
    total_attempts = 0
    dangling = []
    denied_missions = 0
    type_stats = collections.defaultdict(lambda: collections.Counter())
    print(f"{len(games)} match(es), {sum(len(m) for _, _, m in games)} mission(s)")
    for uid, recs, missions in games:
        meta = recs[0] if recs else {}
        game_max_tick = max((r.get("tick") or 0) for r in recs)
        print(f"\n== {meta.get('map_title', '?')} — {meta.get('bot', '?')} ({meta.get('player', '?')}, {meta.get('faction', '?')}) — {str(uid)[:8]}")
        for mid, m in missions:
            # Mission meta comes from any record carrying it (attempts first, else events).
            first = next(iter(m["attempts"].values()), m["events"] or [{}])[0]
            extra = []
            if first.get("type"):
                extra.append(first["type"])
            if first.get("target_cell"):
                extra.append(f"cell {first['target_cell']}")
            if first.get("region") is not None:
                extra.append(f"region {first['region']}")
            print(f"  {mid or '?'}" + (f" ({', '.join(extra)})" if extra else ""))
            if m["events"]:
                print(f"    shelf: " + "  ->  ".join(event_line(e) for e in m["events"]))
            denied_missions += sum(1 for e in m["events"] if e.get("event") == "DENIED")

            for a, trans in m["attempts"].items():
                total_attempts += 1
                last = trans[-1]
                term = is_terminal(last)
                span = last.get("tick", 0) - trans[0].get("tick", 0)
                units = f", {trans[0].get('units')}u" if trans[0].get("units") else ""
                chain = "  ->  ".join(state_line(t) for t in trans)
                print(f"    A{a} {trans[0].get('by', '?')}: {chain}   [{span}t{units}]{'  *open*' if not term else ''}")
                t = first.get("type") or (mid.split(":", 1)[0] if mid else "?")
                if term:
                    type_stats[t][str(last.get("state")).lower()] += 1
                else:
                    type_stats[t]["open"] += 1
                    # Within ~2 game-minutes of the last logged tick the match simply
                    # ended mid-attempt (a straggler); going quiet earlier is a dropped
                    # terminal. Absolute window: a fraction mislabels short matches.
                    straggler = last.get("tick", 0) >= game_max_tick - 3000
                    dangling.append((mid, a, last, straggler))
            if not m["attempts"]:
                # A mission that only ever published/denied/dormant — the shelf, not a bug.
                t = first.get("type") or (mid.split(":", 1)[0] if mid else "?")
                type_stats[t]["shelf_only"] += 1

    print("\n== by type ==")
    for t, c in sorted(type_stats.items()):
        resolved = c.get("success", 0) + c.get("failed", 0) + c.get("released", 0) + c.get("abandoned", 0)
        rate = f"{100 * c.get('success', 0) / resolved:.0f}%" if resolved else "n/a"
        print(f"  {t:<10} {resolved} resolved — success {c.get('success', 0)} ({rate}), "
              f"failed {c.get('failed', 0)}, released {c.get('released', 0)}, "
              f"abandoned {c.get('abandoned', 0)}"
              + (f"; {c.get('open', 0)} OPEN" if c.get("open") else "")
              + (f"; {c.get('shelf_only', 0)} never-attempted" if c.get("shelf_only") else ""))
    if denied_missions:
        print(f"  ({denied_missions} mission-level DENIED event(s) — refused before any attempt existed)")

    if dangling:
        drops = [(mid, a, last) for mid, a, last, s in dangling if not s]
        strays = [(mid, a, last) for mid, a, last, s in dangling if s]
        print(f"\n== {len(dangling)} attempt(s) with no terminal line "
              f"({len(drops)} dropped mid-match, {len(strays)} match-end stragglers) ==")
        for mid, a, last in drops:
            print(f"  {mid} A{a}: last {state_line(last)} by {last.get('by', '?')}  *dropped*")
        for mid, a, last in strays:
            print(f"  {mid} A{a}: last {state_line(last)} by {last.get('by', '?')}  (ended in flight)")
    else:
        print("\nno dangling attempts — every attempt reached a terminal state")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
