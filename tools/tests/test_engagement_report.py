"""EL-0 tests: the python score mirror reproduces the C# vectors of OpenRA.Mods.Cameo.Test/EngagementMathTest.cs."""
import json
import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "ai"))
import ai_log_common as c  # noqa: E402
import engagement_report as er  # noqa: E402


def _total(trade, vs, objective):
    return max(-1000, min(1000, c._tdiv(c.ENGAGEMENT_TRADE_WEIGHT * trade + c.ENGAGEMENT_VS_PREDICTION_WEIGHT * vs
                                        + c.ENGAGEMENT_OBJECTIVE_WEIGHT * objective, 1000)))


@pytest.mark.parametrize("killed,lost,expected", [(600, 200, 500), (0, 0, 0), (100, 300, -500), (100, 200, -333), (500, 0, 1000)])
def test_trade_is_zero_sum(killed, lost, expected):
    assert c.engagement_score("field", killed, lost, 0, 0, 0, False, False)["trade_milli"] == expected
    assert c.engagement_score("field", lost, killed, 0, 0, 0, False, False)["trade_milli"] == -expected


def test_predicted_trade():
    assert c.engagement_predicted_trade(1000, 1000, 600, 0) == 428
    assert c.engagement_predicted_trade(1000, 800, 600, 0) == 333
    assert c.engagement_predicted_trade(0, 0, 0, 0) == 0


def test_building_reward():
    assert c.engagement_building_loss(500, False) == 333
    assert c.engagement_building_loss(1000, True) == 1000
    assert c.engagement_buildings_loss([(1000, 500, False), (3000, 1000, True)]) == 833
    assert c.engagement_buildings_loss([]) == 0


def _obj(kind, own, enemy, own_stake, enemy_stake):
    return c.engagement_score(kind, 0, 0, 0, own, enemy, own_stake, enemy_stake)["objective_milli"]


def test_objective_and_total():
    assert _obj("defend", 333, 0, True, False) == 334
    assert _obj("defend", 333, 0, False, False) == 0
    assert _obj("attack", 0, 1000, False, True) == 1000
    assert _obj("attack", 0, 0, False, True) == -1000
    assert _obj("field", 500, 500, True, True) == 0
    assert _total(500, 250, 334) == 396
    assert _total(1000, 2000, 1000) == 1000
    assert _total(-1000, -2000, -1000) == -1000


def test_full_score_matches_parts():
    s = c.engagement_score("defend", 900, 400, 100, 333, 0, True, False)
    assert s["trade_milli"] == 384 and s["vs_prediction_milli"] == 284 and s["objective_milli"] == 334
    assert s["total_milli"] == _total(384, 284, 334)


def _rec(kind, **kw):
    r = {"record": "engagement", "bot_type": "genericbot", "personality": "rusher", "kind": kind, "skirmish": False,
         "score": {"trade_milli": 500, "vs_prediction_milli": -200, "objective_milli": 100, "total_milli": 300},
         "response": {"response_ticks": 50, "army_dist_at_start_cells": 20},
         "tactics": {"defence_points": 2, "artillery_first": True, "suicide_index_milli": 3000},
         "seen": {"start": {"enemy_unit_value": 100, "enemy_defence_value": 50}},
         "truth": {"start": {"enemy_unit_value": 300, "enemy_defence_value": 50}}}
    r.update(kw)
    return r


def test_report_groups_and_statistics(tmp_path):
    logs = tmp_path / "Logs"
    logs.mkdir()
    recs = [_rec("defend"), _rec("attack"), _rec("attack", skirmish=True), {"record": "posture", "bot_type": "genericbot"}]
    (logs / c.ENGAGEMENT_LOG).write_text("\n".join(json.dumps(r) for r in recs), encoding="utf-8")
    result = er.build(c.load([tmp_path]))
    assert result["postures"] == 1
    by = {g["kind"]: g for g in result["groups"]}
    assert by["defend"]["resp_med"] == pytest.approx(2.0)  # 50 ticks x 40 ms, never the recorded timestep
    assert by["attack"]["n"] == 1 and by["attack"]["skirmish"] == 1
    assert by["attack"]["suicide_gt2"] == 1.0 and by["attack"]["art_first"] == 1.0
    assert by["attack"]["pred_mae"] == 200 and by["attack"]["truth_gap"] == 200
    assert er.main([str(tmp_path), "--json"]) == 0
