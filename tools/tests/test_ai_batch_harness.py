"""run_ai_match_batch.py: matchup matrix, variant patching, and record checks.

The harness is the Stage D data tap — its bugs would silently poison the
match-log corpus the aggregator learns from, so the pure pieces (matrix,
map patching, record slicing) get unit tests; the engine launch itself is
smoke-tested separately with a real match.
"""
import pathlib
import re
import shutil
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools/ai"))
sys.path.insert(0, str(ROOT / "tools/audit"))

import run_ai_match_batch as batch
from miniyaml import Ruleset

TEMPLATE = ROOT / "mods" / "cameo" / "maps" / "ai_duel_gate_20260928"


class MatchupMatrixTests(unittest.TestCase):
    def test_unordered_pairs_with_mirrors(self):
        matchups = batch.build_matchups(["td_gdi", "td_nod"], "hard", "hard", repeats=1)
        pairs = {(m["side_a"]["faction"], m["side_b"]["faction"]) for m in matchups}
        self.assertEqual(pairs, {("td_gdi", "td_gdi"), ("td_gdi", "td_nod"), ("td_nod", "td_nod")})

    def test_repeats_alternate_spawn_sides(self):
        matchups = batch.build_matchups(["td_gdi", "td_nod"], "hard", "hard", repeats=2)
        sides = [
            (m["side_a"]["faction"], m["side_b"]["faction"])
            for m in matchups
            if {m["side_a"]["faction"], m["side_b"]["faction"]} == {"td_gdi", "td_nod"}
        ]
        self.assertEqual(sides, [("td_gdi", "td_nod"), ("td_nod", "td_gdi")])

    def test_difficulty_axes_stay_separate(self):
        matchups = batch.build_matchups(["td_gdi"], "easy", "brutal", repeats=1)
        m = matchups[0]
        self.assertEqual(m["side_a"]["bot"], "easy")
        self.assertEqual(m["side_b"]["bot"], "brutal")


class VariantPatchTests(unittest.TestCase):
    def test_patched_variant_resolves_both_bots(self):
        tmp = pathlib.Path(tempfile.mkdtemp(prefix="ai_duel_test_"))
        try:
            dest = tmp / "variant"
            matchup = {
                "side_a": {"faction": "terran", "bot": "medium"},
                "side_b": {"faction": "td_nod", "bot": "brutal"},
            }
            batch.write_variant(TEMPLATE, dest, matchup, time_limit=2)

            text = (dest / "map.yaml").read_text(encoding="utf-8")
            self.assertIn("Faction: terran", text)
            self.assertIn("Faction: td_nod", text)
            self.assertIn("Bot: medium", text)
            self.assertIn("Bot: brutal", text)
            # Enemies stay cross-wired regardless of the patched values.
            self.assertIn("Enemies: BotB", text)
            self.assertIn("Enemies: BotA", text)
            # Starting forces are pre-placed for the map-side bots.
            self.assertIn("BotA_base:", text)
            self.assertIn("BotB_base:", text)
            self.assertIn("Owner: BotA", text)
            self.assertIn("Owner: BotB", text)
            self.assertNotIn("AI_DUEL_BOT_UNITS", text)
            # Identical content shares one Map.ComputeUID — MapCache then keeps
            # a single preview and Launch.Map's name lookup loses twin dirs.
            # The per-dir salt line keeps every variant's uid unique.
            self.assertIn(f"# ai-match-batch variant: {dest.name}", text)

            rules = (dest / "rules.yaml").read_text(encoding="utf-8")
            self.assertIn("TimeLimitDefault: 2", rules)
            self.assertIn("TimeLimitLocked: True", rules)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_patch_rejects_unknown_block(self):
        text = (TEMPLATE / "map.yaml").read_text(encoding="utf-8")
        with self.assertRaises(SystemExit):
            batch.patch_player_block(text, "NotABot", "hard", "td_gdi")

    def test_starting_units_resolve_real_groups(self):
        # The mod ships light-class groups for the TD factions; the resolver
        # must find real actor names, not sentinel placeholders.
        base, supports = batch.starting_unit_group("td_gdi", "light")
        self.assertTrue(base)
        self.assertTrue(supports)

    def test_starting_units_unknown_faction_fails_closed(self):
        self.assertIsNone(batch.starting_unit_group("not_a_faction", "light"))
        with self.assertRaises(SystemExit):
            batch.render_side_actors("BotA", "not_a_faction", (16, 16))


class TemplateMapContractTests(unittest.TestCase):
    def test_template_map_is_well_formed(self):
        text = (TEMPLATE / "map.yaml").read_text(encoding="utf-8")
        self.assertIn("PlayerReference@Referee:", text)
        self.assertIn("NonCombatant: True", text)
        for ref in ("BotA", "BotB"):
            self.assertIn(f"PlayerReference@{ref}:", text)

    def test_bot_slots_are_map_side_bots(self):
        # The whole design rests on this: headless Launch.Map cannot seat bot
        # clients, so duelists are Playable:False map players — client==null
        # keeps IsBot (records) and the writer's IsBot-admitting eligibility
        # lists them in opponents. Playable:True here would mean "unoccupied
        # lobby slot" and no Player would exist at all.
        text = (TEMPLATE / "map.yaml").read_text(encoding="utf-8")
        for ref in ("BotA", "BotB"):
            block = text.split(f"PlayerReference@{ref}:")[1].split("PlayerReference@")[0]
            self.assertIn("Playable: False", block)
            self.assertIn("Bot:", block)
            self.assertIn("HomeLocation:", block)
            self.assertNotIn("NonCombatant", block)

    def test_referee_declares_map_intent_noncombatant(self):
        text = (TEMPLATE / "map.yaml").read_text(encoding="utf-8")
        block = text.split("PlayerReference@Referee:")[1].split("PlayerReference@")[0]
        self.assertIn("NonCombatant: True", block)
        self.assertIn("StartingUnitsClass: empty", block)

    def test_writer_honors_declared_noncombatant(self):
        # Lobby-occupied slots ignore Player.NonCombatant (engine), so the
        # writer must check PlayerReference.NonCombatant or the referee leaks
        # into opponents and every record becomes non-1v1.
        writer = (ROOT / "OpenRA.Mods.Cameo/Traits/AiMatchLogWriter.cs").read_text(encoding="utf-8")
        self.assertIn("PlayerReference.NonCombatant", writer)

    def test_writer_reads_stance_masks_not_post_game_alliance(self):
        # The log is built after the match resolves, when every decided player
        # reports Spectating (WinState != Undefined) and Player.IsAlliedWith
        # short-circuits to ally on non-mission maps — losers then land in
        # "allies" instead of "opponents". Relationships must come from the
        # static stance masks assigned by SetupPlayerMasks.
        writer = (ROOT / "OpenRA.Mods.Cameo/Traits/AiMatchLogWriter.cs").read_text(encoding="utf-8")
        body = writer.split("AppendRelationships(StringBuilder")[1].split("internal static void")[0]
        self.assertIn("AlliedPlayersMask.Overlaps(subject.PlayerMask)", body)
        self.assertNotIn("p.IsAlliedWith(subject)", body)

    def test_template_has_no_lua_or_spawn_dependency(self):
        # Starting units come from SpawnStartingUnits (per-slot class), match
        # end from ConquestVictoryConditions + the locked TimeLimitManager.
        self.assertFalse((TEMPLATE / "test.lua").exists())
        rules = (TEMPLATE / "rules.yaml").read_text(encoding="utf-8")
        self.assertNotIn("LuaScript", rules)
        self.assertIn("MustBeDestroyed:", rules)

    def test_template_rules_lock_a_valid_time_limit(self):
        text = (TEMPLATE / "rules.yaml").read_text(encoding="utf-8")
        import re

        limit = int(re.search(r"TimeLimitDefault: (\d+)", text).group(1))
        self.assertIn(limit, batch.VALID_TIME_LIMITS)
        self.assertIn("TimeLimitLocked: True", text)
        # the engine rejects a TimeLimitDefault outside the fixture's own options, so the
        # harness's --time-limit choices must be exactly those options
        options = {int(v) for v in re.search(r"TimeLimitOptions: ([\d, ]+)", text).group(1).split(",")}
        self.assertEqual(options, batch.VALID_TIME_LIMITS)
        self.assertIn("GameSpeed: maximum", text)


REAL_MAP = ROOT / "mods" / "cameo" / "maps" / "_ra_a-nuclear-winter.oramap"


class RealMapVariantTests(unittest.TestCase):
    """The maintainer-mandated duel map ("A Nuclear Winter") is a shipped
    .oramap: the harness extracts it and converts the Multi slots into
    map-side bots. These tests pin the conversion contract — referee seat,
    spawn binding, enemy wiring — and the EOF-bleed bug where the last
    PlayerReference's patched fields could leak into the Actors section."""

    def _write(self, matchup):
        tmp = pathlib.Path(tempfile.mkdtemp(prefix="nw_variant_test_"))
        dest = tmp / "variant"
        batch.write_variant(REAL_MAP, dest, matchup, time_limit=2)
        return tmp, dest

    def test_oramap_variant_converts_multi_slots(self):
        matchup = {
            "side_a": {"faction": "td_gdi", "bot": "fransbot"},
            "side_b": {"faction": "ra1_allies", "bot": "hard"},
        }
        tmp, dest = self._write(matchup)
        try:
            text = (dest / "map.yaml").read_text(encoding="utf-8")

            # Referee seat added for the local client, before the duelists.
            self.assertEqual(text.count("PlayerReference@Referee:"), 1)

            blocks = {
                m.group(1): m.group(2)
                for m in re.finditer(r"PlayerReference@(\w+):\n((?:\t\t[^\n]+\n)*)", text)
            }
            for ref, bot, faction in (("Multi0", "fransbot", "td_gdi"), ("Multi1", "hard", "ra1_allies")):
                block = blocks[ref]
                self.assertIn("Playable: False", block)
                self.assertIn(f"Bot: {bot}", block)
                self.assertIn(f"Faction: {faction}", block)
                self.assertIn("HomeLocation:", block)

            # Duelists are enemies of each other AND still hostile to Creeps.
            self.assertIn("Multi1", blocks["Multi0"])
            self.assertIn("Multi0", blocks["Multi1"])
            self.assertIn("Enemies: Creeps", blocks["Multi0"])

            # HomeLocations bind to the map's real mpspawn cells.
            self.assertIn("HomeLocation: 11,45", blocks["Multi0"])
            self.assertIn("HomeLocation: 90,24", blocks["Multi1"])

            # Starting forces injected for both sides.
            self.assertIn("Multi0_base:", text)
            self.assertIn("Multi1_base:", text)

            # No patched field may leak into the Actors section (EOF bleed).
            actors = text.split("\nActors:\n", 1)[1]
            self.assertNotIn("\t\tBot:", actors)
            self.assertNotIn("\t\tHomeLocation:", actors)

            # Rules key + file wired (maximum speed, locked time cap).
            self.assertRegex(text, r"(?m)^Rules: rules\.yaml$")
            rules = (dest / "rules.yaml").read_text(encoding="utf-8")
            self.assertIn("GameSpeed: maximum", rules)
            self.assertIn("TimeLimitDefault: 2", rules)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_mp_spawn_cells_from_real_map(self):
        import zipfile
        with zipfile.ZipFile(REAL_MAP) as z:
            text = z.read("map.yaml").decode("utf-8", "replace")
        cells = batch.mp_spawn_cells(text)
        self.assertGreaterEqual(len(cells), 2)
        self.assertEqual(cells[0], (11, 45))
        self.assertEqual(cells[1], (90, 24))

    def test_swap_bots_alternates_spawn_ownership(self):
        matchups = batch.build_matchups(["td_gdi"], "fransbot", "hard", repeats=4, swap_bots=True)
        side_a_bots = [m["side_a"]["bot"] for m in matchups]
        self.assertEqual(side_a_bots, ["fransbot", "hard", "fransbot", "hard"])

    def test_swap_bots_off_keeps_assignment(self):
        matchups = batch.build_matchups(["td_gdi"], "fransbot", "hard", repeats=2)
        self.assertEqual([m["side_a"]["bot"] for m in matchups], ["fransbot", "fransbot"])


class RecordSliceTests(unittest.TestCase):
    def test_appended_records_skip_garbage(self):
        tmp = pathlib.Path(tempfile.mkdtemp(prefix="ai_log_test_"))
        try:
            log = tmp / "cameo-ai-matches.jsonl"
            prefix = '{"schema": 1}\n'
            log.write_text(prefix, encoding="utf-8")
            before = log.stat().st_size
            with log.open("a", encoding="utf-8") as f:
                f.write('{"schema": 2, "player": {"name": "BotA"}}\n')
                f.write("not json\n")
                f.write('{"schema": 2, "player": {"name": "BotB"}}\n')
            records = batch.read_appended_records(log, before)
            self.assertEqual(len(records), 2)
            self.assertEqual(records[0]["player"]["name"], "BotA")
        finally:
            shutil.rmtree(tmp, ignore_errors=True)


class ScoreboardTests(unittest.TestCase):
    def _record(self, game_uid, slot, bot, outcome, enemy, spawn):
        return {
            "record_id": f"{game_uid}|{slot}",
            "bot_type": bot,
            "outcome": outcome,
            "spawn": spawn,
            "opponent": {"bot_type": enemy},
        }

    def test_scoreboard_pairs_both_perspectives(self):
        results = [{"bot_outcomes": [
            self._record("g1", "Multi0", "fransbot", "lost", "classic", 0),
            self._record("g1", "Multi1", "classic", "won", "fransbot", 1),
            self._record("g2", "Multi0", "classic", "won", "fransbot", 0),
            self._record("g2", "Multi1", "fransbot", "lost", "classic", 1),
        ]}]
        board = batch.ab_scoreboard(results)
        self.assertEqual(board["fransbot vs classic"], {"won": 0, "lost": 2, "spawn": {"0": [0, 1], "1": [0, 1]}})
        self.assertEqual(board["classic vs fransbot"], {"won": 2, "lost": 0, "spawn": {"1": [1, 0], "0": [1, 0]}})

    def test_scoreboard_skips_undecided(self):
        results = [{"bot_outcomes": [self._record("g1", "Multi0", "fransbot", "undecided", "classic", 0)]}]
        self.assertEqual(batch.ab_scoreboard(results), {})


if __name__ == "__main__":
    unittest.main()


class FingerprintTests(unittest.TestCase):
    """LC7: the batch fingerprint freezes the arms — mod commit, engine build,
    AI yaml, map source, batch spec — and any drift aborts the batch."""

    def _tree(self):
        tmp = pathlib.Path(tempfile.mkdtemp(prefix="fingerprint_test_"))
        (tmp / "mods" / "cameo" / "ai").mkdir(parents=True)
        (tmp / "mods" / "cameo" / "ai" / "ai.yaml").write_text("players: {}\n", encoding="utf-8")
        (tmp / "engine" / "bin").mkdir(parents=True)
        (tmp / "engine" / "bin" / "OpenRA.Game.dll").write_bytes(b"fake-dll-a")
        (tmp / "engine" / "bin" / "OpenRA.Mods.Cameo.dll").write_bytes(b"fake-dll-b")
        (tmp / "engine" / "VERSION").write_text("abc123\n", encoding="utf-8")
        (tmp / "map.oramap").write_bytes(b"map-bytes")
        return tmp

    def _fingerprint(self, tmp, config=None):
        return batch.compute_fingerprint(
            tmp / "map.oramap", tmp / "engine",
            config or {"bot_a": "hard", "bot_b": "classic"},
            repo_root=tmp)

    def test_stable_across_calls(self):
        tmp = self._tree()
        try:
            a, b = self._fingerprint(tmp), self._fingerprint(tmp)
            self.assertEqual(batch.fingerprint_drift(a, b), {})
            self.assertEqual(batch.fingerprint_id(a), batch.fingerprint_id(b))
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_nongit_tree_records_null_commit(self):
        tmp = self._tree()
        try:
            fp = self._fingerprint(tmp)
            self.assertIsNone(fp["mod_commit"])
            self.assertIsNone(fp["mod_dirty"])
            self.assertEqual(fp["engine_version"], "abc123")
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_ai_yaml_drift_detected(self):
        tmp = self._tree()
        try:
            a = self._fingerprint(tmp)
            (tmp / "mods" / "cameo" / "ai" / "ai.yaml").write_text("players: {changed: true}\n", encoding="utf-8")
            drift = batch.fingerprint_drift(a, self._fingerprint(tmp))
            self.assertIn("ai_yaml_sha256", drift)
            self.assertNotIn("map_sha256", drift)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_rules_yaml_drift_detected(self):
        """A weapon/rules edit mid-batch moves mod_yaml_sha256 — the class the
        auto-sync service actually caused (league-3)."""
        tmp = self._tree()
        try:
            a = self._fingerprint(tmp)
            (tmp / "mods" / "cameo" / "weapons.yaml").write_text("weapon: x\n", encoding="utf-8")
            drift = batch.fingerprint_drift(a, self._fingerprint(tmp))
            self.assertIn("mod_yaml_sha256", drift)
            self.assertNotIn("ai_yaml_sha256", drift)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_dll_rebuild_drift_detected(self):
        tmp = self._tree()
        try:
            a = self._fingerprint(tmp)
            (tmp / "engine" / "bin" / "OpenRA.Mods.Cameo.dll").write_bytes(b"rebuilt-dll")
            drift = batch.fingerprint_drift(a, self._fingerprint(tmp))
            self.assertIn("mod_dlls_sha256", drift)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_map_file_and_dir_both_hash(self):
        tmp = self._tree()
        try:
            file_fp = self._fingerprint(tmp)
            map_dir = tmp / "mapdir"
            map_dir.mkdir()
            (map_dir / "map.yaml").write_text("map: x\n", encoding="utf-8")
            dir_fp = batch.compute_fingerprint(
                map_dir, tmp / "engine", {"bot_a": "h"}, repo_root=tmp)
            self.assertNotEqual(file_fp["map_sha256"], dir_fp["map_sha256"])
            self.assertIsNotNone(dir_fp["map_sha256"])
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_fingerprint_id_is_compact_hex(self):
        tmp = self._tree()
        try:
            fp_id = batch.fingerprint_id(self._fingerprint(tmp))
            self.assertRegex(fp_id, r"^[0-9a-f]{12}$")
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_config_moves_the_fingerprint(self):
        tmp = self._tree()
        try:
            a = self._fingerprint(tmp, {"bot_a": "hard"})
            b = self._fingerprint(tmp, {"bot_a": "easy"})
            self.assertIn("config", batch.fingerprint_drift(a, b))
        finally:
            shutil.rmtree(tmp, ignore_errors=True)


class ArmFingerprintSummaryTests(unittest.TestCase):
    """ab_summary's arm check: fingerprints live in batch_results.jsonl; a
    single arm file must hold exactly one fingerprint over its real results."""

    def _arm_dir(self, td, rows):
        import json as _json
        p = pathlib.Path(td) / "support"
        p.mkdir(parents=True, exist_ok=True)
        with open(p / "batch_results.jsonl", "w", encoding="utf-8") as f:
            for r in rows:
                f.write(_json.dumps(r) + "\n")
        return td

    def _run(self, td):
        import contextlib
        import io
        sys.path.insert(0, str(ROOT / "tools" / "ai"))
        import ab_summary
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            rc = ab_summary.main([td])
        return rc, out.getvalue()

    def test_single_fingerprint_arm_prints_id(self):
        with tempfile.TemporaryDirectory() as td:
            self._arm_dir(td, [
                {"variant": "v", "status": "ok", "fingerprint": "aaaa1111bbbb"},
                {"variant": "v", "status": "ok", "fingerprint": "aaaa1111bbbb"},
            ])
            rc, out = self._run(td)
        self.assertEqual(rc, 0)
        self.assertIn("arm fingerprint aaaa1111bbbb (2 results)", out)
        self.assertNotIn("FAIL", out)

    def test_mixed_real_fingerprints_fail(self):
        with tempfile.TemporaryDirectory() as td:
            self._arm_dir(td, [
                {"variant": "v", "status": "ok", "fingerprint": "aaaa1111bbbb"},
                {"variant": "v", "status": "ok", "fingerprint": "cccc2222dddd"},
            ])
            rc, out = self._run(td)
        self.assertEqual(rc, 1)
        self.assertIn("FAIL: mixed fingerprints within one arm", out)

    def test_drift_tombstone_tail_does_not_fail(self):
        # An aborted batch records the NEW fingerprint on its drift tombstone;
        # that file is the abort working as designed, not a mixed arm.
        with tempfile.TemporaryDirectory() as td:
            self._arm_dir(td, [
                {"variant": "v", "status": "ok", "fingerprint": "aaaa1111bbbb"},
                {"variant": "v", "status": "fingerprint_drift", "fingerprint": "cccc2222dddd"},
            ])
            rc, out = self._run(td)
        self.assertEqual(rc, 0)
        self.assertIn("cccc2222dddd", out)
        self.assertNotIn("FAIL", out)

    def test_pre_lc7_file_reports_none(self):
        with tempfile.TemporaryDirectory() as td:
            self._arm_dir(td, [{"variant": "v", "status": "ok"}])
            rc, out = self._run(td)
        self.assertEqual(rc, 0)
        self.assertIn("none recorded (pre-LC7)", out)
