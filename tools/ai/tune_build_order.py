"""tune_build_order — the offline half of the build-order lab (AI_ARCHITECTURE.md 12.25, DESIGN.md 19.2).

Route 2 ("tuned", coordinate descent over the BO-1 knobs) and route 3 ("chosen", the opening bandit).
Reads match directories (each a `run_ai_match_batch.py --support-dir`, holding `Logs/`) and:

1. **Scores** every 1v1 match of a bot with a `build_order` situation record as **win + margin (+ speed bonus)**:
       score = win + margin + speed
       win    = 1 for a win, 0 for a loss (undecided matches are dropped)
       margin = (killed - lost) / (killed + lost), the destroyed-to-lost value, in [-1, 1]
       speed  = SPEED_WEIGHT x (1 - duration / SPEED_REF_TICKS), clamped to [0, 1], wins only (a faster win scores more)
2. **Reports** per (personality, own faction): the arms (the batch directory name minus its `_N` suffix), their n, win rate and
   mean score, and per opening the n / wins.
3. **Proposes** (`--propose OUT_DIR`) the next paired experiment per (personality, faction): ONE knob +/- DELTA against the
   current best (the committed learned file), as a base arm and one perturbed arm. Each arm is a learned-file copy
   (`<arm>.yaml`) plus a group in `<OUT_DIR>/experiment_switches.yaml`, which `apply_increment_switches.py --spec` arms next to
   `AK_build_order_knobs` (UseLearnedBuildOrder + LearnedFile). The harness names each arm's batch directory after the arm:
       bo__<personality>__<faction>__base
       bo__<personality>__<faction>__<knob>__up<delta>   /   ...__dn<delta>
4. **Writes** (`--write`) `mods/cameo/ai/learned/build_order_knobs.yaml`, bounded and only with enough evidence:
   * knobs: an arm replaces the base only when BOTH arms have >= MIN_MATCHES matches AND the mean-score gain is significant.
     The test is PAIRED when the arm and base matches can be matched one-to-one by experimental cell (same enemy faction, map and
     spawn side; the k-th replicate of a cell in the arm against the k-th in the base) with >= MIN_MATCHES pairs:
     z = mean_d / (sd_d / sqrt(n_pairs)) on the per-pair score differences (this cancels the map / spawn-side effect). Otherwise it
     falls back to Welch z = (mean_arm - mean_base) / sqrt(var_arm/n_arm + var_base/n_base). Each decision says which (`test`).
     z is one-sided, by the normal approximation (the n >= MIN_MATCHES floor keeps that honest). Several candidate arms of one
     (personality, faction) are tested against the SAME base, so the family is Holm-Bonferroni corrected at one-sided alpha =
     1 - Phi(Z_CRIT) (0.025): the k-th best z must reach the critical z of alpha / (m - k); m == 1 is plain Z_CRIT (1.96).
     Per (personality, faction) at most the single best significant arm is accepted per write (coordinate descent: one step, then
     re-measure). The learned multiplier is the old one x (1 +/- delta) clamped to [LEARN_MIN, LEARN_MAX] thousandths: a bounded
     multiplier on the default.
   * openings: Beta(alpha, beta) per (personality, own faction, enemy faction, opening); only matches played at the current-best
     knobs (the base / control arm, never a knob-perturbed experiment arm, whose result is confounded by the knob change) are
     folded in: a matchup with >= MIN_MATCHES such matches adds wins to alpha and losses to beta; when alpha + beta exceeds
     POSTERIOR_CAP both halve (recency discount). Each game is used once (the file keeps the processed game ids; perturbed-arm
     games are recorded there as skipped), so a re-run on the same directories changes nothing.
   Without --write nothing is changed.

Pure python (stdlib only). The yaml is a committed, reviewed data file (DESIGN 19.2: frozen in release, trained on dev).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import statistics
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import ai_log_common as c  # noqa: E402

REPO = pathlib.Path(__file__).resolve().parents[2]
LEARNED_PATH = REPO / "mods" / "cameo" / "ai" / "learned" / "build_order_knobs.yaml"

KNOBS = ["tempo", "greed", "production", "tech", "defence", "power_margin", "expansion", "support"]
# `expansion` is published for the expansion planner but no consumer reads it yet, so an experiment on it could only measure noise.
TUNABLE = [k for k in KNOBS if k != "expansion"]
# The objective is shared: ai_log_common.match_score (SCORE_SPEED_WEIGHT/SCORE_SPEED_REF_TICKS) - the
# build-order report displays the same number this gate optimizes (review 2026-10-02 §6.2).
SPEED_WEIGHT = c.SCORE_SPEED_WEIGHT
SPEED_REF_TICKS = c.SCORE_SPEED_REF_TICKS
MIN_MATCHES = 20
Z_CRIT = 1.96
DELTA = 100  # thousandths: one coordinate step is +-10%
LEARN_MIN = 800
LEARN_MAX = 1250
POSTERIOR_CAP = 200
MIN_DURATION_TICKS = 3000  # a match that ended before the bots did anything carries no signal

ARM_RE = re.compile(r"^bo__(?P<personality>[a-z0-9]+)__(?P<faction>[a-z0-9_]+?)__(?:base|(?P<knob>[a-z_]+?)__(?P<dir>up|dn)(?P<delta>\d+))$")


# ---------------------------------------------------------------- reading the logs

def read_jsonl(path: pathlib.Path) -> list[dict]:
    if not path.exists():
        return []
    rows = []
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            pass
    return rows


def arm_of(batch_dir: pathlib.Path) -> str:
    return re.sub(r"_\d+$", "", batch_dir.name)


def score_match(outcome: str, killed: float, lost: float, duration_ticks: int) -> tuple[float, float] | None:
    """(score, win) of one match, or None when it carries no signal (undecided, too short)."""
    if outcome not in ("won", "lost") or duration_ticks < MIN_DURATION_TICKS:
        return None
    s = c.match_score(outcome, killed, lost, duration_ticks)
    return s["score"], s["win"]


def build_order_of(situation: dict) -> dict | None:
    bo = situation.get("build_order")
    if bo is None:
        bo = (situation.get("own") or {}).get("build_order")
    return bo if isinstance(bo, dict) else None


def load_matches(batch_dirs: list[pathlib.Path]) -> list[dict]:
    """One row per scored 1v1 bot match: arm, personality, faction, enemy faction, opening, base knob vector, score, win."""
    rows: list[dict] = []
    for d in batch_dirs:
        records = read_jsonl(d / "Logs" / "cameo-ai-matches.jsonl")
        situations = read_jsonl(d / "Logs" / "cameo-ai-situations.jsonl")

        first_bo: dict[tuple[str, str], dict] = {}
        last_bo: dict[tuple[str, str], dict] = {}
        for s in sorted(situations, key=lambda r: r.get("tick", 0)):
            bo = build_order_of(s)
            if bo is None:
                continue
            key = (s.get("game_uid", ""), s.get("player", ""))
            first_bo.setdefault(key, bo)
            last_bo[key] = bo

        for r in records:
            player = r.get("player") or {}
            opponents = r.get("opponents") or []
            if len(opponents) != 1 or r.get("allies"):
                continue  # a team result says nothing about one bot's build order
            key = (r.get("game_uid", ""), player.get("name", ""))
            if key not in first_bo:
                continue
            stats = r.get("stats") or {}
            scored = score_match(player.get("outcome", ""), stats.get("kills_cost", 0), stats.get("deaths_cost", 0),
                                 r.get("duration_ticks", 0))
            if scored is None:
                continue
            first, last = first_bo[key], last_bo[key]
            personality = first.get("personality") or player.get("personality") or ""
            if not personality:
                continue
            rows.append({
                "game_uid": key[0],
                "arm": arm_of(d),
                "personality": personality,
                "faction": player.get("faction", ""),
                "enemy_faction": opponents[0].get("faction", ""),
                "map": r.get("map_uid", "") or "",
                "spawn": player.get("spawn", -1),
                "opening": last.get("opening", "") or "",
                "knobs": {k: first.get(f"base_{k}", 1000) for k in KNOBS},
                "score": scored[0],
                "win": scored[1],
            })
    return rows


# ---------------------------------------------------------------- statistics

class Stats:
    """Running mean and variance (Welford)."""

    def __init__(self) -> None:
        self.n = 0
        self.mean = 0.0
        self.m2 = 0.0

    def add(self, x: float) -> None:
        self.n += 1
        d = x - self.mean
        self.mean += d / self.n
        self.m2 += d * (x - self.mean)

    @property
    def var(self) -> float:
        return self.m2 / (self.n - 1) if self.n > 1 else 0.0


def welch_z(arm: Stats, base: Stats) -> float:
    """Welch z of (arm - base) on mean score; +-inf when both variances are zero but the means differ."""
    diff = arm.mean - base.mean
    se = math.sqrt(arm.var / max(1, arm.n) + base.var / max(1, base.n))
    if se == 0:
        return 0.0 if diff == 0 else math.copysign(math.inf, diff)
    return diff / se


def paired_z(arm_rows: list[dict], base_rows: list[dict], min_pairs: int) -> tuple[float, int] | None:
    """Paired z of (arm - base) on score, or None when fewer than `min_pairs` matches can be paired one-to-one.

    A pair is the k-th replicate (in log order) of one experimental cell - (enemy faction, map, spawn side) - in each arm. The
    harness records no per-match seed, so replicates of a cell are exchangeable; pairing removes the cell effect (a spawn-side or
    matchup advantage) that the unpaired Welch test leaves in its variance. Returns (z, n_pairs).
    """
    def by_cell(rows: list[dict]) -> dict[tuple, list[float]]:
        cells: dict[tuple, list[float]] = {}
        for r in rows:
            cells.setdefault((r.get("enemy_faction", ""), r.get("map", ""), r.get("spawn", -1)), []).append(r["score"])
        return cells

    a, b = by_cell(arm_rows), by_cell(base_rows)
    diffs = [x - y for cell in sorted(a.keys() & b.keys(), key=repr) for x, y in zip(a[cell], b[cell])]
    if len(diffs) < max(2, min_pairs):
        return None
    n = len(diffs)
    mean_d = sum(diffs) / n
    sd = math.sqrt(sum((d - mean_d) ** 2 for d in diffs) / (n - 1))
    if sd == 0:
        return (0.0 if mean_d == 0 else math.copysign(math.inf, mean_d)), n
    return mean_d / (sd / math.sqrt(n)), n


def holm_critical_z(m: int, z_crit: float = Z_CRIT) -> list[float]:
    """Critical z per rank (best z first) for m comparisons, Holm-Bonferroni at the one-sided alpha 1 - Phi(z_crit).

    m == 1 is exactly `z_crit`. Rank k (0-based) uses alpha / (m - k); reject down the ranking until one fails.
    """
    nd = statistics.NormalDist()
    alpha = 1 - nd.cdf(z_crit)
    return [z_crit if m - k == 1 else nd.inv_cdf(1 - alpha / (m - k)) for k in range(m)]


def arm_stats(rows: list[dict]) -> dict[tuple[str, str, str], Stats]:
    """(personality, faction, arm) -> score stats."""
    out: dict[tuple[str, str, str], Stats] = {}
    for r in rows:
        out.setdefault((r["personality"], r["faction"], r["arm"]), Stats()).add(r["score"])
    return out


# ---------------------------------------------------------------- the learned file

def empty_learned() -> dict:
    return {"knobs": {}, "openings": {}, "processed_knobs": [], "processed_openings": []}


def parse_learned(text: str) -> dict:
    """Read the file this script writes (tab-indented MiniYaml, fixed shape); unknown nodes are ignored."""
    learned = empty_learned()
    scope: tuple | None = None
    kind = ""
    in_root = False
    for raw in text.splitlines():
        line = raw.rstrip("\r")
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        depth = len(line) - len(line.lstrip("\t"))
        key, _, value = line.strip().partition(":")
        value = value.strip()
        if depth == 0:
            in_root = key == "BotBuildOrderKnobs"
            scope = None
        elif in_root and depth == 1:
            scope, kind = None, ""
            if key.startswith("Knobs@"):
                personality, _, sc = key[len("Knobs@"):].partition("__")
                scope, kind = (personality, sc), "knobs"
                learned["knobs"].setdefault(scope, {})
            elif key.startswith("Openings@"):
                left, _, enemy = key[len("Openings@"):].partition("__vs__")
                personality, _, own = left.partition("__")
                scope, kind = (personality, own, enemy), "openings"
                learned["openings"].setdefault(scope, {})
            elif key == "ProcessedKnobs":
                learned["processed_knobs"] = [v for v in value.split(",") if v]
            elif key == "ProcessedOpenings":
                learned["processed_openings"] = [v for v in value.split(",") if v]
        elif in_root and depth == 2 and scope is not None:
            if kind == "knobs":
                learned["knobs"][scope][key] = int(value)
            else:
                alpha, beta = value.split()
                learned["openings"][scope][key] = [int(alpha), int(beta)]
    return learned


def format_learned(learned: dict) -> str:
    lines = [
        "# GENERATED by tools/ai/tune_build_order.py --write - do not edit by hand; regenerate and review.",
        "# Offline build-order knobs (AI_ARCHITECTURE.md 12.25, DESIGN.md 19.2): read at match start, frozen in release.",
        "#   Knobs@<personality>__<scope>: knob: thousandths      scope = <own faction> | family_<family> | any",
        "#   Openings@<personality>__<own faction>__vs__<enemy faction>: <opening>: <alpha> <beta>",
        "BotBuildOrderKnobs:",
    ]
    for (personality, scope), values in sorted(learned["knobs"].items()):
        if not values:
            continue
        lines.append(f"\tKnobs@{personality}__{scope}:")
        for knob in KNOBS:
            if knob in values:
                lines.append(f"\t\t{knob}: {values[knob]}")
    for (personality, own, enemy), values in sorted(learned["openings"].items()):
        if not values:
            continue
        lines.append(f"\tOpenings@{personality}__{own}__vs__{enemy}:")
        for opening, (alpha, beta) in sorted(values.items()):
            lines.append(f"\t\t{opening}: {alpha} {beta}")
    if learned["processed_knobs"]:
        lines.append("\tProcessedKnobs: " + ",".join(sorted(set(learned["processed_knobs"]))))
    if learned["processed_openings"]:
        lines.append("\tProcessedOpenings: " + ",".join(sorted(set(learned["processed_openings"]))))
    return "\n".join(lines) + "\n"


def game_key(row: dict) -> str:
    """A short stable id of one bot's game (the file would otherwise list full game uids)."""
    return hashlib.sha1(f"{row['game_uid']}|{row['personality']}|{row['faction']}".encode()).hexdigest()[:10]


# ---------------------------------------------------------------- tuning

def clamp(value: int, lo: int, hi: int) -> int:
    return max(lo, min(hi, value))


def current_multiplier(learned: dict, personality: str, faction: str, knob: str) -> int:
    """The learned multiplier the game would apply: faction -> family_<family> -> any scopes of the same personality; missing = 1000."""
    for scope in (faction, "family_" + faction.partition("_")[0], "any"):
        v = learned["knobs"].get((personality, scope), {}).get(knob)
        if v is not None:
            return v
    return 1000


def decisions(rows: list[dict], learned: dict, min_matches: int = MIN_MATCHES, z_crit: float = Z_CRIT) -> list[dict]:
    """For every (personality, faction): each perturbed arm vs its base arm, with the accept verdict.

    Paired z where the matches pair up by cell, Welch otherwise (`test`); the arms of one scope share the base, so their
    significance is Holm-Bonferroni corrected over the arms that have enough matches (`z_crit_used` is the threshold applied).
    """
    stats = arm_stats(rows)
    by_arm: dict[tuple[str, str, str], list[dict]] = {}
    for r in rows:
        by_arm.setdefault((r["personality"], r["faction"], r["arm"]), []).append(r)
    out = []
    for (personality, faction, arm), s in sorted(stats.items()):
        m = ARM_RE.match(arm)
        if not m or not m.group("knob") or (m.group("personality"), m.group("faction")) != (personality, faction):
            continue
        base_arm = f"bo__{personality}__{faction}__base"
        base = stats.get((personality, faction, base_arm))
        if base is None:
            continue
        knob, direction, delta = m.group("knob"), m.group("dir"), int(m.group("delta"))
        if knob not in KNOBS:
            continue
        enough = s.n >= min_matches and base.n >= min_matches
        z, test, n_pairs = welch_z(s, base), "welch", 0
        paired = paired_z(by_arm[(personality, faction, arm)], by_arm[(personality, faction, base_arm)], min_matches) if enough else None
        if paired is not None:
            z, n_pairs = paired
            test = "paired"
        old = current_multiplier(learned, personality, faction, knob)
        step = delta if direction == "up" else -delta
        new = clamp(old * (1000 + step) // 1000, LEARN_MIN, LEARN_MAX)
        out.append({
            "personality": personality, "faction": faction, "arm": arm, "knob": knob, "direction": direction, "delta": delta,
            "n_arm": s.n, "n_base": base.n, "mean_arm": s.mean, "mean_base": base.mean, "z": z, "test": test, "n_pairs": n_pairs,
            "enough": enough, "significant": False, "z_crit_used": z_crit, "old": old, "new": new,
        })

    scopes: dict[tuple[str, str], list[dict]] = {}
    for d in out:
        if d["enough"]:
            scopes.setdefault((d["personality"], d["faction"]), []).append(d)
    for family in scopes.values():
        family.sort(key=lambda d: -d["z"])
        for d, crit in zip(family, holm_critical_z(len(family), z_crit)):
            d["z_crit_used"] = crit
        for d in family:  # Holm step-down: stop at the first failure
            if d["z"] < d["z_crit_used"]:
                break
            d["significant"] = True
    return out


def accepted(decs: list[dict]) -> dict[tuple[str, str], dict]:
    """The single best significant, actually-changing arm per (personality, faction)."""
    best: dict[tuple[str, str], dict] = {}
    for d in decs:
        if not d["significant"] or d["new"] == d["old"]:
            continue
        key = (d["personality"], d["faction"])
        if key not in best or d["z"] > best[key]["z"]:
            best[key] = d
    return best


def is_perturbed_arm(arm: str) -> bool:
    """True for a knob-experiment arm (`bo__<p>__<f>__<knob>__up/dn<delta>`); the base arm and plain batches are controls."""
    m = ARM_RE.match(arm)
    return bool(m and m.group("knob"))


def update_openings(learned: dict, rows: list[dict], min_matches: int = MIN_MATCHES) -> list[tuple]:
    """Fold unprocessed matches into the opening posteriors, one matchup at a time. Returns the matchups updated.

    Only matches at the current-best knobs (the base / control arm) count: a perturbed-arm match mixes the opening's effect with a
    deliberate knob change. Those are recorded as processed (skipped) so they are never reconsidered.
    """
    done = set(learned["processed_openings"])
    by_matchup: dict[tuple[str, str, str], list[dict]] = {}
    for r in rows:
        if not r["opening"] or game_key(r) in done:
            continue
        if is_perturbed_arm(r["arm"]):
            learned["processed_openings"].append(game_key(r))
            done.add(game_key(r))
            continue
        by_matchup.setdefault((r["personality"], r["faction"], r["enemy_faction"]), []).append(r)

    updated = []
    for matchup, group in sorted(by_matchup.items()):
        if len(group) < min_matches:
            continue
        posteriors = learned["openings"].setdefault(matchup, {})
        for r in group:
            alpha, beta = posteriors.get(r["opening"], [1, 1])
            alpha, beta = alpha + int(r["win"]), beta + int(1 - r["win"])
            if alpha + beta > POSTERIOR_CAP:
                alpha, beta = max(1, alpha // 2), max(1, beta // 2)
            posteriors[r["opening"]] = [alpha, beta]
            learned["processed_openings"].append(game_key(r))
        updated.append(matchup)
    return updated


def write_update(rows: list[dict], learned: dict, min_matches: int = MIN_MATCHES, z_crit: float = Z_CRIT) -> dict:
    """Apply the bounded, significance-checked update to `learned` in place; returns what changed."""
    done = set(learned["processed_knobs"])
    fresh = [r for r in rows if game_key(r) not in done]
    decs = decisions(fresh, learned, min_matches, z_crit)
    changes = {"knobs": [], "openings": []}
    for (personality, faction), d in sorted(accepted(decs).items()):
        learned["knobs"].setdefault((personality, faction), {})[d["knob"]] = d["new"]
        changes["knobs"].append(d)
    # Every game of a (personality, faction) that reached a verdict is consumed: its arms were measured against each other.
    decided = {(d["personality"], d["faction"]) for d in decs if d["enough"]}
    for r in fresh:
        if (r["personality"], r["faction"]) in decided:
            learned["processed_knobs"].append(game_key(r))
    changes["openings"] = update_openings(learned, rows, min_matches)
    return changes


def next_experiment(rows: list[dict], learned: dict, personality: str, faction: str, min_matches: int = MIN_MATCHES) -> dict | None:
    """The first (knob, direction) in fixed order whose arm or base is under-sampled; None when every pair is measured."""
    stats = arm_stats(rows)
    base = stats.get((personality, faction, f"bo__{personality}__{faction}__base"))
    for knob in TUNABLE:
        for direction in ("up", "dn"):
            arm = f"bo__{personality}__{faction}__{knob}__{direction}{DELTA}"
            s = stats.get((personality, faction, arm))
            if s is None or s.n < min_matches or base is None or base.n < min_matches:
                old = current_multiplier(learned, personality, faction, knob)
                new = clamp(old * (1000 + (DELTA if direction == "up" else -DELTA)) // 1000, LEARN_MIN, LEARN_MAX)
                if new == old:
                    continue  # at the bound: nothing to test in that direction
                return {"arm": arm, "base_arm": f"bo__{personality}__{faction}__base", "knob": knob, "direction": direction,
                        "old": old, "new": new, "n_arm": s.n if s else 0, "n_base": base.n if base else 0}
    return None


def experiment_files(learned: dict, personality: str, faction: str, exp: dict) -> dict[str, str]:
    """Learned-file text per arm (base = the current file, arm = the one knob moved) at the arm's name."""
    perturbed = {"knobs": {k: dict(v) for k, v in learned["knobs"].items()}, "openings": learned["openings"],
                 "processed_knobs": [], "processed_openings": []}
    perturbed["knobs"].setdefault((personality, faction), {})[exp["knob"]] = exp["new"]
    base = {"knobs": learned["knobs"], "openings": learned["openings"], "processed_knobs": [], "processed_openings": []}
    return {exp["base_arm"]: format_learned(base), exp["arm"]: format_learned(perturbed)}


def switches_text(arms: list[str]) -> str:
    """An increment_switches-style spec: one group per arm, arming the learned file of that arm."""
    lines = ["# GENERATED by tools/ai/tune_build_order.py --propose: one group per experiment arm.",
             "# Arm with: python tools/ai/apply_increment_switches.py <worktree> --spec <this file> --groups AK_build_order_knobs_arm",
             "# (AK_build_order_knobs from the main spec arms the provider; each arm adds its learned file). Copy <arm>.yaml to",
             "# <worktree>/mods/cameo/ai/learned/ first.",
             "skip: [SquadManagerBotModuleCA@classic]", "", "groups:"]
    for arm in arms:
        lines += [f"  {arm}:", "    BuildOrderKnobsBotModule:", "      UseLearnedBuildOrder: true",
                  f"      LearnedFile: ai/learned/{arm}.yaml"]
    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------- reporting

def report(rows: list[dict], learned: dict, min_matches: int = MIN_MATCHES) -> str:
    out = [f"{len(rows)} scored matches (score = win + margin + speed; speed weight {SPEED_WEIGHT}, ref {SPEED_REF_TICKS} ticks)"]
    stats = arm_stats(rows)
    wins: dict[tuple[str, str, str], int] = {}
    for r in rows:
        wins[(r["personality"], r["faction"], r["arm"])] = wins.get((r["personality"], r["faction"], r["arm"]), 0) + int(r["win"])
    out.append("\n## Arms (personality, faction, arm): n, wins, mean score, mean base knob vector")
    for key, s in sorted(stats.items()):
        group = [r for r in rows if (r["personality"], r["faction"], r["arm"]) == key]
        vec = " ".join(f"{k}={round(sum(r['knobs'][k] for r in group) / len(group))}" for k in KNOBS)
        out.append(f"- {key[0]} {key[1]} {key[2]}: n={s.n} wins={wins[key]} mean={s.mean:.3f}  [{vec}]")
    out.append("\n## Openings (personality, faction vs enemy faction, opening): n, wins")
    per: dict[tuple, list[int]] = {}
    for r in rows:
        p = per.setdefault((r["personality"], r["faction"], r["enemy_faction"], r["opening"] or "none"), [0, 0])
        p[0] += 1
        p[1] += int(r["win"])
    for key, (n, w) in sorted(per.items()):
        out.append(f"- {key[0]} {key[1]} vs {key[2]} {key[3]}: n={n} wins={w}")
    out.append(f"\n## Knob experiments (need >= {min_matches} matches per arm and z >= {Z_CRIT})")
    decs = decisions(rows, learned, min_matches)
    for d in decs:
        verdict = "ACCEPT" if d["significant"] and d["new"] != d["old"] else ("under-sampled" if not d["enough"] else "reject")
        out.append(f"- {d['personality']} {d['faction']} {d['knob']} {d['direction']}{d['delta']}: arm n={d['n_arm']} mean={d['mean_arm']:.3f} "
                   f"vs base n={d['n_base']} mean={d['mean_base']:.3f} z={d['z']:.2f} ({d['test']}) -> {verdict} ({d['old']} -> {d['new']})")
    if not decs:
        out.append("- none: no arm named bo__<personality>__<faction>__<knob>__up|dn<delta> with a base arm in these directories")
    return "\n".join(out)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("batch_dirs", nargs="*", type=pathlib.Path)
    ap.add_argument("--learned", type=pathlib.Path, default=LEARNED_PATH, help="the learned file to read (and write with --write)")
    ap.add_argument("--write", action="store_true", help="apply the bounded, significance-checked update to the learned file")
    ap.add_argument("--propose", type=pathlib.Path, metavar="OUT_DIR", help="write the next paired experiment per --pair to OUT_DIR")
    ap.add_argument("--pair", action="append", default=[], metavar="PERSONALITY:FACTION", help="a (personality, faction) to propose for; repeatable")
    ap.add_argument("--min-matches", type=int, default=MIN_MATCHES)
    ap.add_argument("--z", type=float, default=Z_CRIT)
    args = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")

    learned = parse_learned(args.learned.read_text(encoding="utf-8")) if args.learned.exists() else empty_learned()
    rows = load_matches([d for d in args.batch_dirs if d.is_dir()])
    print(report(rows, learned, args.min_matches))

    if args.propose:
        args.propose.mkdir(parents=True, exist_ok=True)
        arms: list[str] = []
        for pair in args.pair:
            personality, _, faction = pair.partition(":")
            exp = next_experiment(rows, learned, personality, faction, args.min_matches)
            if exp is None:
                print(f"\npropose {pair}: every pair is measured; run --write")
                continue
            for arm, text in experiment_files(learned, personality, faction, exp).items():
                (args.propose / f"{arm}.yaml").write_text(text, encoding="utf-8", newline="\n")
                arms.append(arm)
            print(f"\npropose {pair}: {exp['knob']} {exp['direction']}{DELTA} ({exp['old']} -> {exp['new']}) vs base; arms {exp['base_arm']}, {exp['arm']}")
        (args.propose / "experiment_switches.yaml").write_text(switches_text(arms), encoding="utf-8", newline="\n")
        print(f"\nwrote {args.propose / 'experiment_switches.yaml'}")

    if args.write:
        changes = write_update(rows, learned, args.min_matches, args.z)
        args.learned.parent.mkdir(parents=True, exist_ok=True)
        args.learned.write_text(format_learned(learned), encoding="utf-8", newline="\n")
        print(f"\nwrote {args.learned}: {len(changes['knobs'])} knob change(s), {len(changes['openings'])} matchup posterior update(s)")
        for d in changes["knobs"]:
            print(f"- {d['personality']} {d['faction']} {d['knob']}: {d['old']} -> {d['new']} (z={d['z']:.2f}, n={d['n_arm']}/{d['n_base']})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
