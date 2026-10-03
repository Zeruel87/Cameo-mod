"""ai_log_common.py - shared readers for the AI report tools (expansion_report, build_order_report).

A "match dir" is a batch support dir (it holds `Logs/`), a `Logs` dir itself, or one of the jsonl files.
"""
from __future__ import annotations

import json
import pathlib
import statistics
import sys

MATCH_LOG = "cameo-ai-matches.jsonl"
SITUATION_LOG = "cameo-ai-situations.jsonl"
PLACEMENT_LOG = "cameo-ai-placements.jsonl"
ENGAGEMENT_LOG = "cameo-ai-engagements.jsonl"
DEFAULT_TIMESTEP_MS = 40


def read_jsonl(path: pathlib.Path) -> list[dict]:
    if not path.is_file():
        return []
    out = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError:
                print(f"warning: skipped a malformed line in {path}", file=sys.stderr)
    return out


def logs_dir(d: pathlib.Path) -> pathlib.Path:
    if d.is_file():
        return d.parent
    return d / "Logs" if (d / "Logs").is_dir() else d


def load(dirs: list[pathlib.Path]) -> dict[str, list[dict]]:
    """All four logs of every dir, concatenated."""
    out = {"matches": [], "situations": [], "placements": [], "engagements": []}
    for d in dirs:
        logs = logs_dir(d)
        out["matches"] += read_jsonl(logs / MATCH_LOG)
        out["situations"] += read_jsonl(logs / SITUATION_LOG)
        out["placements"] += read_jsonl(logs / PLACEMENT_LOG)
        out["engagements"] += read_jsonl(logs / ENGAGEMENT_LOG)
    return out


def minutes(ticks: float, timestep_ms: int = DEFAULT_TIMESTEP_MS) -> float:
    return ticks * timestep_ms / 60000.0


def mmss(ticks: float, timestep_ms: int = DEFAULT_TIMESTEP_MS) -> str:
    seconds = int(round(ticks * timestep_ms / 1000.0))
    return f"{seconds // 60:02d}:{seconds % 60:02d}"


# ── the ONE match-score objective (AI_ARCHITECTURE §12.25, review 2026-10-02 §6.2) ──
# score = win + margin + speed_bonus, on raw ticks so every caller scores identically
# regardless of how it displays time. The report and the tuner must agree or a human
# can see arm A win the report while the tuner applies a different objective. The
# tuner's constants are canonical - it is the gate that accepts an arm.
SCORE_SPEED_WEIGHT = 0.25
SCORE_SPEED_REF_TICKS = 54000  # ~36 game minutes at DEFAULT_TIMESTEP_MS; a slower win earns no bonus


def match_score(outcome: str, killed: float, lost: float, duration_ticks: int) -> dict:
    """win + margin + speed_bonus for one match. Callers decide which matches carry signal
    (the tuner drops undecided/too-short ones before calling)."""
    win = 1.0 if outcome == "won" else 0.0
    total = killed + lost
    margin = (killed - lost) / total if total > 0 else 0.0
    speed = SCORE_SPEED_WEIGHT * min(1.0, max(0.0, 1.0 - duration_ticks / SCORE_SPEED_REF_TICKS)) if win else 0.0
    return {"win": win, "margin": round(margin, 4), "speed_bonus": round(speed, 4),
            "score": round(win + margin + speed, 4)}


# EL-0 (AI_ARCHITECTURE 12.30): the engagement score. Integer thousandths, mirror of OpenRA.Mods.Cameo
# EngagementScore (EngagementMath.cs); tools/tests/test_engagement_report.py reproduces the C# test vectors.
ENGAGEMENT_TRADE_WEIGHT = 500
ENGAGEMENT_VS_PREDICTION_WEIGHT = 250
ENGAGEMENT_OBJECTIVE_WEIGHT = 250


def _tdiv(a: int, b: int) -> int:
    """C# integer division (truncates toward zero)."""
    q = abs(a) // abs(b)
    return q if (a >= 0) == (b >= 0) else -q


def _clamp(v: int, lo: int, hi: int) -> int:
    return lo if v < lo else hi if v > hi else v


def engagement_score(kind: str, killed: int, lost: int, predicted_trade: int, own_loss_milli: int,
                     enemy_loss_milli: int, own_stake: bool, enemy_stake: bool) -> dict:
    """trade / vs_prediction / objective / total of one engagement, all in -1000..1000."""
    trade = _tdiv(1000 * (killed - lost), max(1, killed + lost))
    vs_prediction = trade - predicted_trade
    if kind == "defend" and own_stake:
        objective = 1000 - 2 * own_loss_milli
    elif kind == "attack" and enemy_stake:
        objective = 2 * enemy_loss_milli - 1000
    else:
        objective = 0
    total = _clamp(_tdiv(ENGAGEMENT_TRADE_WEIGHT * trade + ENGAGEMENT_VS_PREDICTION_WEIGHT * vs_prediction
                         + ENGAGEMENT_OBJECTIVE_WEIGHT * objective, 1000), -1000, 1000)
    return {"trade_milli": trade, "vs_prediction_milli": vs_prediction, "objective_milli": objective,
            "total_milli": total}


def engagement_predicted_trade(own_value: int, enemy_value: int, own_surviving_permille: int,
                               enemy_surviving_permille: int) -> int:
    lost = _tdiv(own_value * (1000 - _clamp(own_surviving_permille, 0, 1000)), 1000)
    killed = _tdiv(enemy_value * (1000 - _clamp(enemy_surviving_permille, 0, 1000)), 1000)
    return _tdiv(1000 * (killed - lost), max(1, killed + lost))


def engagement_building_loss(hp_lost_milli: int, dead: bool) -> int:
    """Two thirds by HP fraction lost, one third on death."""
    return _tdiv(2 * hp_lost_milli + (1000 if dead else 0), 3)


def engagement_buildings_loss(buildings: list[tuple[int, int, bool]]) -> int:
    """Value-weighted building loss; buildings = [(value, hp_lost_milli, dead)]."""
    weighted = sum(max(1, v) * engagement_building_loss(h, d) for v, h, d in buildings)
    total = sum(max(1, v) for v, _, _ in buildings)
    return _tdiv(weighted, max(1, total))


def mean(values):
    values = [v for v in values if v is not None]
    return sum(values) / len(values) if values else None


def median(values):
    values = [v for v in values if v is not None]
    return statistics.median(values) if values else None


def fmt(value, digits: int = 1) -> str:
    if value is None:
        return "-"
    if isinstance(value, float):
        return f"{value:.{digits}f}"
    return str(value)


def table(rows: list[list[str]]) -> str:
    if not rows:
        return ""
    widths = [max(len(str(r[i])) for r in rows) for i in range(len(rows[0]))]
    return "\n".join("  ".join(str(c).ljust(w) for c, w in zip(r, widths)).rstrip() for r in rows)
