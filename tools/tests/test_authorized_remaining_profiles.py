"""Regression boundary for the final authorized live weapon-profile batch."""

from __future__ import annotations

import json
import hashlib
import pathlib
import subprocess
import sys
import unittest
from unittest.mock import patch
from types import SimpleNamespace


ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / "tools/audit"), str(ROOT / "tools/balance")]

from consolidate_authorized_remaining_profiles import inspect
from consolidate_authorized_remaining_profiles import CLEANUP_NAMES
from miniyaml import Ruleset, load_text, merge_children
from reviewed_weapon_history import LaterProfileView
from review_batch_diff import active_health_values, snapshot, snapshot_digest
import review_batch_diff
from survey_weapon_structure import inventory


def frozen_weapon_ruleset(current, commit):
    """Read immutable Git blobs in manifest order using the resolver's merge law."""
    root = current.repo_root
    paths = [p.relative_to(root).as_posix() for p in current.manifest.weapons]
    query = ''.join(f'{commit}:{path}\n' for path in paths).encode()
    data = subprocess.check_output(['git', 'cat-file', '--batch'], input=query, cwd=root)
    weapons, pos = {}, 0
    for path in paths:
        end = data.index(b'\n', pos)
        header = data[pos:end].decode()
        if header.endswith(' missing'):
            raise AssertionError(f'missing historical weapon source: {path}')
        size = int(header.split()[-1])
        pos = end + 1
        blob, pos = data[pos:pos + size], pos + size + 1
        for node in load_text(blob.decode('utf-8-sig')):
            if node.key.startswith('-'):
                weapons.pop(node.key[1:], None)
            elif node.key in weapons:
                previous = weapons[node.key]
                previous.children = merge_children(previous.children, node.children)
                if node.value:
                    previous.value = node.value
            else:
                weapons[node.key] = node.deep_copy()
    frozen = Ruleset.__new__(Ruleset)
    frozen.weapons = weapons
    frozen._weapon_ci = {name.lower(): name for name in weapons}
    frozen._resolve_cache = {}
    return frozen


class AuthorizedRemainingProfileTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rules = Ruleset(ROOT)
        cls.comparison = json.loads((
            ROOT / "docs/audit/latest/authorized_remaining_profile_comparison.json"
        ).read_text(encoding="utf-8"))

    def test_converter_accepts_the_resolved_ruleset(self):
        self.assertFalse(inspect(self.rules))
        self.assertTrue(inspect(LaterProfileView(self, self.rules)))

    def test_comparison_has_no_definition_or_delivery_drift(self):
        self.assertEqual([], self.comparison["added"])
        self.assertEqual([], self.comparison["removed"])
        forbidden = {"cadence", "projectile", "report"}
        observed = {
            change[0]
            for changes in self.comparison["changed"].values()
            for change in changes
        }
        self.assertTrue(forbidden.isdisjoint(observed))

    def test_historical_comparison_metadata_remains_unmodified(self):
        # This artifact records PR #320, not subsequent upstream gameplay edits.
        # Keep its original baseline, head digest and HP matrix as provenance.
        self.assertEqual(
            "8ddfb4e9bc5a5d25765ce635845b4004e3e2a485e015b712192554e333b0393f",
            snapshot_digest(self.comparison["meta"]))

    def test_followup_snapshot_matches_the_explicit_merge_repairs(self):
        # Separate evidence for current upstream648f62f7c6 -> these five repairs;
        # never relabel PR320's historical artifact as current gameplay proof.
        repair = json.loads((ROOT / "docs/audit/latest/merge_payload_repair_comparison.json").read_text(encoding="utf-8"))
        self.assertEqual("978d3bb50a01dcbcd53cfde4aa4142beafbfe1062c7034e11a1cb409d859a6c5",
                         hashlib.sha256(json.dumps(repair, sort_keys=True, separators=(",", ":")).encode()).hexdigest())
        self.assertEqual("21c440193fa1d7e7f667cab3c96b1ce236a184e7e3a6aa2ff556b0acb68a7cfc",
                         repair["meta"]["base_snapshot_sha256"])
        self.assertEqual({"TSScoopDualChem", "RA2120xmm", "RA2120xmm_elite",
                          "RA2120xmm_rad", "RA2120xmm_rad_elite"}, set(repair["changed"]))
        self.assertEqual([], repair["added"])
        self.assertEqual([], repair["removed"])
        health_values = sorted(set(active_health_values(ROOT)))
        self.assertEqual(health_values, repair["meta"]["health_values"])
        self.assertFalse(repair["meta"]["with_concrete"])
        # Recompute the original whole-tree evidence from immutable source blobs;
        # later intentional profiles make a comparison with today's roster invalid.
        frozen = frozen_weapon_ruleset(self.rules, '5bb76c22d7bc3315999a5accdbf6cfdf57321776')
        with patch.object(review_batch_diff, 'Model', return_value=SimpleNamespace(rs=frozen)):
            self.assertEqual(repair['meta']['head_snapshot_sha256'],
                             snapshot_digest(snapshot(ROOT, False, health_values)))
        for name, changes in repair["changed"].items():
            self.assertTrue({"cadence", "report"}.isdisjoint(change[0] for change in changes), name)

    def test_comparison_payload_is_exactly_reviewed(self):
        payload = {
            key: self.comparison[key] for key in ("changed", "removed", "added")
        }
        raw = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
        self.assertEqual(
            "e65496668e328c845f3e86bdbba8360d10a92ffaf678679b9706c1ee119b322b",
            hashlib.sha256(raw).hexdigest())

    def test_only_intentional_flat_total_and_target_route_changed(self):
        main_damage = {
            name: change[1:]
            for name, changes in self.comparison["changed"].items()
            for change in changes
            if change[0] == "main_damage"
        }
        self.assertEqual({"TSBombSonic": [20000.0, 30000.0]}, main_damage)

        top_level = {
            name
            for name, changes in self.comparison["changed"].items()
            if any(change[0] == "top_level" for change in changes)
        }
        self.assertEqual({"TSAegisMissile"}, top_level)

        non_damage = {
            name
            for name, changes in self.comparison["changed"].items()
            if any(change[0] == "non_damage_warheads" for change in changes)
        }
        self.assertEqual({"GrenadeRA"}, non_damage)

    def test_reachable_backlog_keeps_raw_ratchets_without_exemptions(self):
        # Do not retain a fully resolved roster throughout this test class: the
        # snapshot and converter tests otherwise hold another roster concurrently.
        counts = inventory(Ruleset(ROOT))["counts"]
        self.assertLessEqual(counts["stacked_main_transitive_weapon_graph"], 240)
        self.assertEqual(0, counts["reviewed_stacked_main_transitive_weapon_graph"])
        self.assertEqual(counts["stacked_main_transitive_weapon_graph"],
                         counts["unreviewed_stacked_main_transitive_weapon_graph"])
        self.assertEqual(counts["stacked_main_unreached"], counts["unreviewed_stacked_main_unreached"])
        self.assertLessEqual(counts["excess_main_warhead_instances_transitive_weapon_graph"], 452)

    def test_t30_profile_keeps_the_authorized_railgun_geometry(self):
        node = self.rules.resolve_weapon("t30shell").child(
            "Warhead@Railgun_HeavyFlatCompatibility")
        self.assertEqual("80000", node.get("Damage"))
        self.assertEqual("512", node.get("Spread"))
        self.assertEqual("100, 0", node.get("Falloff"))
        self.assertEqual("3000", node.get("PercentageScale"))
        self.assertEqual(1200, (80000 * 3000 + 100000) // 200000)

    def test_hammer_thermobaric_route_does_not_regress_core_vehicle_damage(self):
        armors = ("Scout", "Light", "Medium", "Heavy", "Superheavy")
        for base_name, paid_name in (
                ("ra1_soviets_hammertank_cannon", "ra1_soviets_hammertank_cannon_thermobaric"),):
            base = self.rules.resolve_weapon(base_name).child("Warhead@CannonHE_Heavy")
            paid = self.rules.resolve_weapon(paid_name).child("Warhead@Thermobaric_Heavy")
            base_versus = {node.key: int(node.value) for node in base.child("Versus").children}
            paid_versus = {node.key: int(node.value) for node in paid.child("Versus").children}
            base_damage = int(base.get("Damage"))
            paid_damage = int(paid.get("Damage"))
            for armor in armors:
                self.assertGreaterEqual(
                    paid_damage * paid_versus[armor],
                    base_damage * base_versus[armor],
                    f"{paid_name} regresses {armor}")

    def test_kotin_uses_the_upstream_nuclear_upgrade_for_fire_and_death(self):
        # 4a1479b50 changed this role deliberately; do not impose the retired
        # thermobaric matchup guarantee on the nuclear/radiation replacement.
        weapon = self.rules.resolve_weapon("ra1_soviets_kotinnucleartank_kotincannonnuclearshell")
        self.assertIsNotNone(weapon)
        self.assertEqual("16000", weapon.child("Warhead@CannonNuke_Heavy").get("Damage"))
        self.assertEqual(("96", "6427", "2", "4"), tuple(
            weapon.get(key) for key in ("ReloadDelay", "Range", "Burst", "BurstDelays")))
        radiation = weapon.child("Warhead@Radiation")
        self.assertEqual("CreateTintedCells", radiation.value)
        self.assertEqual("ra2radiation", radiation.get("LayerName"))
        self.assertEqual("30", radiation.get("Level"))
        actor = self.rules.resolve("ra1_soviets_kotinnucleartank")
        for trait in ("Armament", "FireWarheadsOnDeath"):
            base = actor.child(trait)
            upgraded = actor.child(trait + "@Upgrade")
            self.assertEqual("ra1_soviets_kotinnucleartank_kotincannon", base.get("Weapon"))
            self.assertEqual("!ra1_soviets_upgrade_nucleartankshells", base.get("RequiresCondition"))
            self.assertEqual("ra1_soviets_kotinnucleartank_kotincannonnuclearshell", upgraded.get("Weapon"))
            self.assertEqual("ra1_soviets_upgrade_nucleartankshells", upgraded.get("RequiresCondition"))

    def test_converter_default_mode_is_read_only(self):
        paths = {
            pathlib.Path(self.rules.weapons[name].file)
            for name in CLEANUP_NAMES
            if name in self.rules.weapons
        }
        before = {path: path.read_bytes() for path in paths}
        result = subprocess.run(
            [sys.executable, str(ROOT / "tools/balance/consolidate_authorized_remaining_profiles.py")],
            cwd=ROOT, check=False, capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('TSBombSonic: expected source total 10000, found 30000', result.stderr)
        self.assertEqual(before, {path: path.read_bytes() for path in paths})


if __name__ == "__main__":
    unittest.main()
