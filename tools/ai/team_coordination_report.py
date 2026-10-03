#!/usr/bin/env python3
"""Score bot team coordination from match telemetry (TC-3 acceptance metrics).

Reads the per-match records a team run leaves in a support dir
(tools/ai/run_ai_match_batch.py --team-size N):

    Logs/cameo-ai-missions.jsonl   one line per mission event/attempt
    Logs/cameo-ai-matches.jsonl    one record per bot per match (allies list)
    batch_results.jsonl            one record per executed match

and reports, per team and per match, the §12.18 acceptance metrics:

    shared_push       windows where >=2 teammates committed attack attempts
                      (raid/recon/secure) against the SAME enemy player —
                      the coalition-main-target effect. raid:* comes from
                      taken provider cards; secure:<player> is emitted when a
                      cardless Rush wave commits against the named enemy
                      (mission target or main-target steering).
    contested_claims  same exclusive-claim `mission_id` with genuinely
                      overlapping open attempts by >=2 teammates — a real race
                      for one capturable. A release-then-recommit is succession
                      (claim timeouts legitimately reopen finished targets);
                      arbitration resolves overlaps via superseded stand-downs.
    defend_answers    defend_kind mission attempts (COMMITTED only). Three
                      sources: `defend:self:rN` = own-base Defend BotMission
                      provider cards; `defend_answer:<requesterKey>:<cell>` =
                      TC-2b/TC-3 ally answers through the protection-squad
                      path — requesterKey is the participant's InternalName
                      (or #ClientIndex), the cell its defended position —
                      direct attribution, not proximity; and
                      `assist_answer:<requesterKey>:<cell>` = the TC-3 assist
                      election's escort answer to a contested expansion claim,
                      same channel, strictly below a defend answer.
    coverage          distinct target players / regions touched per team.

Team membership is inferred from cameo-ai-matches.jsonl `allies` records
(transitive closure of ally names). `--team A=Multi0,Multi1` overrides.

Usage:
    python tools/ai/team_coordination_report.py <support-dir> [--window T]

--window T : tick window for "simultaneous" (default 1500 = 1 min at 25tps).
"""
import collections
import json
import pathlib
import sys

ATTACK_KINDS = {"raid", "recon", "secure"}
DEFEND_KINDS = {"defend", "defend_answer", "assist_answer"}  # defend_answer/assist_answer = TC-2b/TC-3 ally rescue + escort answers (SquadManager, post-merge review instrumentation)


def iter_jsonl(path):
    if not path or not path.is_file():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            try:
                yield json.loads(line)
            except json.JSONDecodeError:
                continue


def teams_from_matches(match_records):
    """Transitive closure over `allies` names -> list of teams (player sets)."""
    parent = {}

    def find(x):
        parent.setdefault(x, x)
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a, b):
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[max(ra, rb)] = min(ra, rb)

    for r in match_records:
        me = (r.get("player") or {}).get("name")
        if not me:
            continue
        for a in r.get("allies") or []:
            name = a.get("name") if isinstance(a, dict) else a
            if name:
                union(me, name)
    groups = collections.defaultdict(set)
    for x in parent:
        groups[find(x)].add(x)
    return sorted((sorted(g) for g in groups.values()), key=lambda g: (len(g), g))


def load_support_dir(support):
    support = pathlib.Path(support)
    logs = support / "Logs"
    missions = list(iter_jsonl(logs / "cameo-ai-missions.jsonl"))
    matches = list(iter_jsonl(logs / "cameo-ai-matches.jsonl"))
    results = list(iter_jsonl(support / "batch_results.jsonl"))
    # matches may also be appended to a global Logs dir; fall back to batch
    # results' bot_outcomes for team inference.
    if not matches:
        for r in results:
            for bo in r.get("bot_outcomes") or []:
                me = bo.get("record_id")
                allies = [{"name": a.get("name")} for a in bo.get("allies") or []]
                # record_id is not the slot name; allies names are slot names.
                matches.append({"player": {"name": me}, "allies": allies})
    return missions, matches, results


def mission_of(rec):
    mid = rec.get("mission_id") or ""
    parts = mid.split(":")
    kind = parts[0]
    target_player = parts[1] if len(parts) > 1 else None
    return kind, mid, target_player


def analyse(missions, team):
    """Per-team coordination metrics from that team's mission records."""
    recs = [r for r in missions if r.get("player") in team]
    attempts = [r for r in recs if r.get("record_kind") == "attempt"]

    # Contested claims: identical mission_id attempted by >=2 teammates.
    # CLAIM_KINDS are races — a capture/garrison claim should have one owner;
    # attack-kind ids (raid:/secure:/recon:) are deterministic (type:enemy:region),
    # so two bots taking the same card is a SHARED STRIKE, not a race — counted
    # as shared_objectives instead, the behaviour the metric wants to see.
    CLAIM_KINDS = {"capture", "garrison_contest"}
    by_mid = collections.defaultdict(set)
    kind_of = {}
    # mid -> [(player, commit_tick, close_tick_or_None)] per claim attempt
    claim_open = collections.defaultdict(list)
    for r in attempts:
        kind, mid, _ = mission_of(r)
        by_mid[mid].add(r.get("player"))
        kind_of[mid] = kind
        if kind not in CLAIM_KINDS:
            continue
        if r.get("state") == "COMMITTED":
            claim_open[mid].append([r.get("player"), r.get("attempt"), r.get("tick") or 0, None])
        elif claim_open.get(mid):
            for o in reversed(claim_open[mid]):
                if o[0] == r.get("player") and o[1] == r.get("attempt") and o[3] is None:
                    o[3] = r.get("tick") or 0
                    break

    shared = {mid: ps for mid, ps in by_mid.items() if len(ps) > 1}
    window = analyse.window

    # Contested = genuinely overlapping opens: two teammates held the same claim
    # open at once. A release-then-recommit is succession, not a race — claim
    # timeouts legitimately reopen a target a teammate already finished with.
    def racing(opens):
        for i, a in enumerate(opens):
            for b in opens[i + 1:]:
                if a[0] == b[0]:
                    continue
                a_end = a[3] if a[3] is not None else 1 << 30
                b_end = b[3] if b[3] is not None else 1 << 30
                if a[2] <= b_end and b[2] <= a_end:
                    return True
        return False

    contested = {m: p for m, p in shared.items()
                 if kind_of[m] in CLAIM_KINDS and racing(claim_open.get(m, []))}
    shared_objectives = {m: p for m, p in shared.items() if kind_of[m] in ATTACK_KINDS}

    # Shared pushes: same enemy target_player attacked by >=2 teammates
    # within `window` ticks — COMMITTED records only: a terminal record in a
    # later window must not extend the push's apparent duration.
    shared_push_windows = 0
    push_events = collections.defaultdict(set)  # (target, bucket) -> players
    for r in attempts:
        kind, _, tgt = mission_of(r)
        if kind in ATTACK_KINDS and tgt and tgt not in team and r.get("state") == "COMMITTED":
            push_events[(tgt, (r.get("tick") or 0) // window)].add(r.get("player"))
    shared_pushes = {k: ps for k, ps in push_events.items() if len(ps) > 1}
    shared_push_windows = len(shared_pushes)

    # Attack breadth: distinct enemy players ever targeted.
    targets_hit = set()
    for r in attempts:
        kind, _, tgt = mission_of(r)
        if kind in ATTACK_KINDS and tgt and tgt not in team:
            targets_hit.add(tgt)

    # Committed only: one answer = one mission, not answer + release.
    defend_count = sum(1 for r in attempts
                       if mission_of(r)[0] in DEFEND_KINDS and r.get("state") == "COMMITTED")
    return {
        "players": sorted(team),
        "attempts": len(attempts),
        "contested_claims": {m: sorted(p) for m, p in contested.items()},
        "shared_objectives": {m: sorted(p) for m, p in shared_objectives.items()},
        "shared_push_windows": shared_push_windows,
        "shared_push_detail": {f"{t}@w{w}": sorted(p) for (t, w), p in sorted(shared_pushes.items())},
        "distinct_enemy_targets": sorted(targets_hit),
        "defend_missions": defend_count,
    }


def main(argv):
    # Collect team specs in both forms: `--team A=Multi0,Multi1` (separate
    # token) and `--team=A=Multi0,Multi1`. Everything else `--` goes to opts,
    # everything else is positional.
    team_specs = []
    args = []
    opts = {}
    i = 1
    while i < len(argv):
        a = argv[i]
        if a == "--team" and i + 1 < len(argv):
            team_specs.append(argv[i + 1])
            i += 2
        elif a.startswith("--team="):
            team_specs.append(a.split("=", 1)[1])
            i += 1
        elif a.startswith("--"):
            if "=" in a:
                k, v = a.split("=", 1)
                opts[k] = v
            i += 1
        else:
            args.append(a)
            i += 1
    if not args:
        sys.exit(__doc__)
    analyse.window = int(opts.get("--window", 1500))
    support = args[0]
    missions, matches, results = load_support_dir(support)
    if not missions:
        sys.exit(f"no mission records under {support}/Logs")

    # Explicit team lists override inference — needed to score a still-running
    # match, before cameo-ai-matches.jsonl is written at match end.
    if team_specs:
        teams = [sorted(s.split("=", 1)[-1].split(",")) for s in team_specs]
    else:
        teams = teams_from_matches(matches)
    if not teams:
        players = sorted({r.get("player") for r in missions})
        teams = [players]
        print("warning: no allies data — treating all players as one team", file=sys.stderr)

    print(f"support={support}  missions={len(missions)}  teams={len(teams)}")
    for i, team in enumerate(teams):
        print(f"\nteam {chr(65 + i)}: {', '.join(team)}")
        rep = analyse(missions, set(team))
        print(f"  attempts={rep['attempts']}  defend_missions={rep['defend_missions']}")
        print(f"  shared_push_windows={rep['shared_push_windows']}  {rep['shared_push_detail']}")
        print(f"  contested_claims={len(rep['contested_claims'])}  shared_objectives={len(rep['shared_objectives'])}")
        for mid, ps in rep["contested_claims"].items():
            print(f"    CONTESTED {mid}: {', '.join(ps)}")
        print(f"  distinct_enemy_targets={rep['distinct_enemy_targets']}")

    # Match outcomes.
    outcomes = collections.Counter()
    for r in results:
        for bo in r.get("bot_outcomes") or []:
            outcomes[(bo.get("bot_type"), bo.get("outcome"))] += 1
    if outcomes:
        print("\noutcomes:")
        for (bot, oc), n in sorted(outcomes.items()):
            print(f"  {bot}: {oc} x{n}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
