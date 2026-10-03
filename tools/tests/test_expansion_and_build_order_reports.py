"""expansion_report + build_order_report on a tiny synthetic batch (AI_ARCHITECTURE 12.24 FE-0, 12.25 BO-0)."""
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "ai"))
import build_order_report as bor  # noqa: E402
import expansion_report as exr  # noqa: E402
import ai_log_common as c  # noqa: E402

TICKS_PER_MIN = 1500  # timestep 40 ms


def expansion(harvested, refineries, excess, angle, coverage, yards=1, dist_mean=3.0, dist_max=5.0):
    return {"fields_known": 4, "fields_in_reach": 2, "fields_served": 1, "fields_harvested": harvested,
            "refineries": refineries, "excess_refineries": excess, "anchor_dist_mean": dist_mean,
            "anchor_dist_max": dist_max, "conyards": yards, "crawl_mcv_angle": angle, "coverage_milli": coverage}


def snap(player, tick, exp, personality="rush"):
    return {"game_uid": "g1", "player": player, "bot_type": "hard", "tick": tick, "personality_current": personality,
            "expansion": exp}


def place(player, tick, actor, category, reason, personality="rush"):
    return {"game_uid": "g1", "player": player, "bot_type": "hard", "personality": personality, "tick": tick,
            "queued_tick": tick - 100, "placed_tick": tick, "actor": actor, "category": category, "reason": reason}


def match(player, outcome, minutes, killed, lost, personality="rush", knobs=None):
    p = {"name": player, "bot_type": "hard", "outcome": outcome, "personality": personality}
    if knobs:
        p["knobs"] = knobs
    return {"game_uid": "g1", "timestep": 40, "duration_ticks": int(minutes * TICKS_PER_MIN), "player": p,
            "stats": {"kills_cost": killed, "deaths_cost": lost}}


def write(tmp_path, name, rows):
    logs = tmp_path / "batch" / "Logs"
    logs.mkdir(parents=True, exist_ok=True)
    (logs / name).write_text("\n".join(json.dumps(r) for r in rows), encoding="utf-8")
    return tmp_path / "batch"


def fixture(tmp_path):
    snaps = [snap("Multi0", t * TICKS_PER_MIN, e) for t, e in [
        (1, expansion(0, 0, 0, -1, 0)),
        (5, expansion(1, 2, 1, 30, 500)),
        (10, expansion(3, 3, 2, 50, 750, yards=2, dist_mean=6.0, dist_max=11.0)),
        (21, expansion(2, 3, 1, 120, 600))]]
    places = [place("Multi0", 900, "powr", "power", "base"), place("Multi0", 1800, "proc", "refinery", "base"),
              place("Multi0", 3000, "proc", "refinery", "refinery_claim"), place("Multi0", 2400, "barr", "production", "base")]
    matches = [match("Multi0", "won", 12, 8000, 2000, knobs={"tempo": 1.1}), match("Multi1", "lost", 12, 1000, 1000)]
    path = write(tmp_path, "cameo-ai-situations.jsonl", snaps)
    write(tmp_path, "cameo-ai-placements.jsonl", places)
    write(tmp_path, "cameo-ai-matches.jsonl", matches)
    return path


def test_expansion_report_metrics(tmp_path):
    result = exr.build(exr.c.load([fixture(tmp_path)]))
    row = result["matches"][0]
    assert row["first_refinery_tick"] == 1800
    assert (row["harvested_5"], row["harvested_10"], row["harvested_20"]) == (1, 3, 3)  # minute 20 reads the last snapshot at or before it
    assert row["peak_harvested"] == 3
    assert row["peak_coverage"] == 750
    assert row["max_excess"] == 2
    assert row["anchor_dist_max"] == 11.0
    assert row["angle_median"] == 50  # angles 30, 50, 120
    assert abs(row["angle_lt45"] - 1 / 3) < 1e-9
    assert row["conyards_peak"] == 2
    assert result["aggregate"][0]["matches"] == 1
    assert "rush" in exr.render(result)


def test_expansion_report_short_match_has_no_late_minutes(tmp_path):
    snaps = [snap("Multi0", 1 * TICKS_PER_MIN, expansion(1, 1, 0, -1, 100))]
    row = exr.build({"matches": [], "situations": snaps, "placements": []})["matches"][0]
    assert row["harvested_5"] is None and row["harvested_20"] is None
    assert row["angle_median"] is None


def test_build_order_orders_by_time_and_scores(tmp_path):
    result = bor.build(bor.c.load([fixture(tmp_path)]))
    row = result["matches"][0]
    assert [b["actor"] for b in row["order"]] == ["powr", "proc", "barr", "proc"]
    assert [b["time"] for b in row["order"]] == ["00:36", "01:12", "01:36", "02:00"]
    assert row["first_by_category"]["refinery"] == 1.2
    o = row["outcome"]
    assert o["win"] == 1
    assert abs(o["margin"] - 0.6) < 1e-9  # (8000 - 2000) / 10000
    bonus = c.SCORE_SPEED_WEIGHT * (1 - 12 * TICKS_PER_MIN / c.SCORE_SPEED_REF_TICKS)
    assert abs(o["speed_bonus"] - bonus) < 1e-3
    assert abs(o["score"] - (1 + 0.6 + bonus)) < 1e-3
    assert row["knobs"] == '{"tempo": 1.1}'
    assert result["by_personality"][0]["win_rate"] == 1.0
    assert "score" in bor.render(result)


def test_score_formula_edges():
    ms = c.match_score
    assert ms("lost", 0, 0, 40)["score"] == 0
    assert ms("lost", 1000, 3000, 10)["score"] == -0.5
    assert ms("won", 0, 0, c.SCORE_SPEED_REF_TICKS)["speed_bonus"] == 0


def test_game_time_ignores_the_recorded_timestep(tmp_path):
    """Fast-speed batches record `timestep: 1`; minutes are still the nominal 40 ms game clock (tick 7500 = 5 min)."""
    snaps = [snap("Multi0", 7500, expansion(2, 1, 0, 30, 500)), snap("Multi0", 7600, expansion(3, 1, 0, 30, 500))]
    places = [place("Multi0", 1500, "proc", "refinery", "base")]
    m = match("Multi0", "won", 12, 8000, 2000)
    m["timestep"] = 1
    path = write(tmp_path, "cameo-ai-situations.jsonl", snaps)
    write(tmp_path, "cameo-ai-placements.jsonl", places)
    write(tmp_path, "cameo-ai-matches.jsonl", [m])
    [row_] = exr.build(exr.c.load([path]))["matches"]
    assert row_["harvested_5"] == 2
    assert abs(row_["first_refinery_min"] - 1.0) < 0.01
    rep = bor.build(bor.c.load([path]))
    assert rep is not None
