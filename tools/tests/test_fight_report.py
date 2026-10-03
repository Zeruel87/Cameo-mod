"""fight_report: the decisive window is the stretch with the largest net trade swing."""
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "ai"))
import fight_report  # noqa: E402

FIELDS = "tick,earned,spent,army_value,assets_value,kills_cost,deaths_cost"


def record(bot, name, outcome, rows):
    return {"game_uid": "g1", "duration_ticks": rows[-1][0],
            "player": {"name": name, "bot_type": bot, "outcome": outcome, "home": "1,1"},
            "stats": {"kills_cost": rows[-1][5], "deaths_cost": rows[-1][6], "resources_earned": rows[-1][1],
                      "stats_timeline_fields": FIELDS, "stats_timeline": rows}}


def test_decisive_window_picks_the_biggest_swing():
    rows = [dict(zip(FIELDS.split(","), r)) for r in [
        [750, 0, 0, 0, 0, 0, 0], [1500, 0, 0, 0, 0, 100, 0], [2250, 0, 0, 0, 0, 200, 5000], [3000, 0, 0, 0, 0, 300, 5100]]]
    i, j, net = fight_report.decisive_window(rows, 1)
    assert (rows[i]["tick"], rows[j]["tick"], net) == (1500, 2250, -4900)


def test_report_reads_a_batch_dir(tmp_path):
    logs = tmp_path / "batch" / "Logs"
    logs.mkdir(parents=True)
    hard = record("hard", "Multi0", "lost", [[750, 10, 10, 1000, 2000, 0, 0], [1500, 20, 20, 500, 1500, 100, 3000]])
    classic = record("classic", "Multi1", "won", [[750, 10, 10, 1000, 2000, 0, 0], [1500, 30, 30, 4000, 5000, 3000, 100]])
    (logs / "cameo-ai-matches.jsonl").write_text("\n".join(json.dumps(r) for r in (hard, classic)), encoding="utf-8")
    snap = {"game_uid": "g1", "player": "Multi0", "tick": 1, "personality_current": "rush", "urgency": "normal",
            "own": {"army_value": 1000, "squad_count": 1, "losses_by_role": {}, "away_losses_by_role": {}}, "enemies": [{}]}
    later = dict(snap, tick=1500, own={"army_value": 500, "squad_count": 0,
                                       "losses_by_role": {"rush": 3000}, "away_losses_by_role": {"rush": 2400}})
    (logs / "cameo-ai-situations.jsonl").write_text(json.dumps(snap) + "\n" + json.dumps(later), encoding="utf-8")
    text = fight_report.report([tmp_path / "batch"], "hard", 1)
    assert "hard lost vs classic" in text
    assert "net -2900" in text
    assert "rush 3000 (80% away)" in text
