"""C21 — the verified legacy identity aliases in docs/balance/name_map.yaml.

Two key kinds:
- SEVEN display aliases pin legacy workbook rows (Infantry!B62, Vehicles!B139,
  Defenses!B15, Tanks!B47, Vehicles!B162, Tanks!B96, Vehicles!B35) to ledger
  actors whose CURRENT display name no longer matches the legacy row, so
  seed_design's normalized-name auto-match can never find them. A read-only
  norm() pass over the five legacy type tabs found exactly one row per key, no
  collisions. The four FutureTech aliases trace through migration
  6dbba3eaa007fcd3d612a37f013fe4854f87de6b (future_robot_* / futu_wheel ->
  *.futu) and header renames db913a5abcb80cbf7489728ed3213e6cf18e96b7; the
  migration did NOT rename tooltips (its parent already used the new droid
  names) — the dormant monolith's old names are legacy-name association only.
- SIX actor-ID aliases pin legacy CABAL column-C ids that commit
  86eee6bcadb5cbe567ec1f470eb5617d5bb9c713 merged (internal underscores
  removed) in mods/cameo/ContentPacks/TiberianSun/CABAL/yaml/aircraft.yaml.
  They are consulted ONLY when the original id is absent from the ledger —
  an existing id is always kept, never redirected.

The aliases are IDENTITY aliases only — not approval to import legacy numbers
and not approval to retire the workbook — so the tests also pin that no
speculative aliases leaked in for still-untriaged rows (Minigunner / AP /
Laser / Freezer Turret / Advanced Soviet Mammoth Tank).

PRIOR ART: seed_design.load_name_map / ledger_docs / all_units are the consumer
side (seed_design.main); docs/balance/discrepancies.md is the triage report the
entries resolve rows in (historical until a full authorized reseed/triage).
"""

from __future__ import annotations

import json
import pathlib
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
LEDGER = ROOT / "docs" / "balance"

try:
    import openpyxl  # noqa: F401
    _HAVE_OPENPYXL = True
except ImportError:
    _HAVE_OPENPYXL = False

if _HAVE_OPENPYXL:
    sys.path.insert(0, str(ROOT / "tools" / "balance"))
    import seed_design as sd  # noqa: E402
else:
    sd = None

# legacy workbook row -> (ledger file, actor id, current display name, content pack)
ALIASES = {
    "Terran Marine": ("starcraft_terran.json", "terran_marine", "Marine", "StarCraft/Terran"),
    "Ordos Tank Destroyer": ("d2k_ordos.json", "ordos_tankdestroyer", "Tank Destroyer", "D2k/Ordos"),
    "Ixian Gun Turret": ("d2k_ixian.json", "ixian_gunturret", "Gun Turret", "D2k/Ixian"),
    # FutureTech identity chain: 6dbba3eaa007fcd3d612a37f013fe4854f87de6b then
    # db913a5abcb80cbf7489728ed3213e6cf18e96b7; no tooltip rename in the migration
    "Cannon Attack Robot": ("redalert2mod_futuretech.json", "futuretech_cannondroid",
                            "Cannon Droid", "RedAlert2Mod/FutureTech"),
    "Missile Attack Robot": ("redalert2mod_futuretech.json", "futuretech_missiledroid",
                             "Missile Droid", "RedAlert2Mod/FutureTech"),
    "Plasma Super Mech": ("redalert2mod_futuretech.json", "futuretech_plasmastrider",
                          "Plasma Strider", "RedAlert2Mod/FutureTech"),
    "Scout Robot": ("redalert2mod_futuretech.json", "futuretech_scoutdroid",
                    "Scout Droid", "RedAlert2Mod/FutureTech"),
}

# legacy CABAL column-C id (underscored) -> active CABAL actor id (merged);
# provenance: 86eee6bcadb5cbe567ec1f470eb5617d5bb9c713, aircraft.yaml headers
ACTOR_ID_ALIASES = {
    "cabal_overkill_gunship": "cabal_overkillgunship",
    "cabal_hunter_drone_carrier": "cabal_hunterdronecarrier",
    "cabal_hunter_drone": "cabal_hunterdrone",
    "cabal_orb_drone": "cabal_orbdrone",
    "cabal_cyborg_assassin": "cabal_cyborgassassin",
    "cabal_repair_drone": "cabal_repairdrone",
}


@unittest.skipUnless(sd is not None, "openpyxl unavailable (seed_design dependency)")
class LegacyNameAliasTest(unittest.TestCase):
    def test_loader_returns_exactly_the_authorized_aliases(self):
        """The committed file must load to exactly the seven display aliases
        plus the six actor-ID aliases — nothing more.
        load_name_map normalizes keys through norm() and takes values verbatim."""
        self.assertTrue(sd.NAME_MAP.exists(), f"missing: {sd.NAME_MAP}")
        expected = {sd.norm(legacy): actor for legacy, (_, actor, _, _) in ALIASES.items()}
        expected.update({sd.norm(old): new for old, new in ACTOR_ID_ALIASES.items()})
        self.assertEqual(sd.load_name_map(), expected)

    def test_normalized_keys_stay_unique_across_both_key_kinds(self):
        """The registry matches through norm(), not exact strings — a collision
        between a display-name key and an actor-ID key would silently redirect
        one of the two families."""
        keys = list(ALIASES) + list(ACTOR_ID_ALIASES)
        normalized = [sd.norm(k) for k in keys]
        self.assertEqual(len(normalized), len(set(normalized)),
                         "a display alias and an actor-ID alias collide after norm()")
        self.assertEqual(len(keys), 13, "expected exactly 3+6+4 authorized aliases")

    def test_cabal_actor_id_alias_targets_exist_and_originals_are_gone(self):
        """Every actor-ID alias must point at an ACTIVE ledger actor, and the
        old underscored id must be GONE from the ledger — otherwise the alias
        would be dead weight or, worse, never fire (an existing id is kept)."""
        units = sd.all_units(sd.ledger_docs())
        for old, new in ACTOR_ID_ALIASES.items():
            with self.subTest(alias=old):
                self.assertNotIn(old, units,
                                 f"{old} still exists in the ledger — the alias must "
                                 f"be removed (an existing id is never redirected)")
                self.assertIn(new, units,
                              f"{new} missing from the committed ledger")
                self.assertNotEqual(old, new,
                                    f"{old}: alias redirects to the same raw id — dead entry")

    def test_targets_exist_in_the_real_ledger_with_aligned_display_and_faction(self):
        """Every target must exist in seed_design's own ledger view (the exact
        lookup seed_design.main seeds through), under the named faction ledger,
        with the display name the alias rationale cites."""
        units = sd.all_units(sd.ledger_docs())
        for legacy, (fn, actor, display, pack) in ALIASES.items():
            with self.subTest(alias=legacy):
                self.assertIn(actor, units, f"{actor} vanished from the committed ledger")
                ledger_name, _section, u = units[actor]
                self.assertEqual(ledger_name, pathlib.Path(fn).stem,
                                 f"{actor} moved to a different faction ledger")
                self.assertEqual(u.get("name"), display,
                                 f"{actor}: ledger display drifted from the alias rationale")
                doc = json.loads((LEDGER / fn).read_text(encoding="utf-8"))
                self.assertTrue(str(doc.get("pack", "")).endswith(pack),
                                f"{actor}: pack {doc.get('pack')!r} is not the {pack} faction")
                self.assertNotEqual(sd.norm(display), sd.norm(legacy),
                                    f"{actor}: display now matches the legacy row — the "
                                    f"{legacy!r} alias is redundant, drop it")

    def test_no_speculative_aliases_for_still_untriaged_rows(self):
        """Minigunner / AP / Laser legacy rows have NOT been triaged, and
        Freezer Turret / Advanced Soviet Mammoth Tank are deliberately left
        unmapped (conflicting Freezer rows / unproven Mammoth identity) — an inferred alias there would
        silently seed design fields for an unverified match."""
        nmap = sd.load_name_map()
        for legacy in ("Minigunner", "AP", "Laser",
                       "Freezer Turret", "Advanced Soviet Mammoth Tank"):
            self.assertNotIn(sd.norm(legacy), nmap,
                             f"unauthorized alias for still-untriaged row {legacy!r}")

    def test_loader_skips_comments_and_blank_lines(self):
        """Temporary-file fixture (NAME_MAP restored via addCleanup, normalization
        untouched): header/blank/comment lines are ignored and the key is
        normalized — which is exactly why the yaml keeps citations on their own
        comment line above each entry instead of inline after the value."""
        original = sd.NAME_MAP
        self.addCleanup(setattr, sd, "NAME_MAP", original)
        with tempfile.TemporaryDirectory() as td:
            sd.NAME_MAP = pathlib.Path(td) / "name_map.yaml"
            sd.NAME_MAP.write_text(
                "# header comment — ignored\n"
                "\n"
                "# Infantry!B62\n"
                "Terran Marine: terran_marine\n"
                "\n"
                "# trailing comment — ignored\n",
                encoding="utf-8")
            self.assertEqual(sd.load_name_map(), {"terranmarine": "terran_marine"})


@unittest.skipUnless(sd is not None, "openpyxl unavailable (seed_design dependency)")
class FutureTechDisplayAliasResolutionTest(unittest.TestCase):
    """The four FutureTech display aliases must work through the REAL chain:
    seed_design.load_name_map -> active Ruleset actor resolution -> ledger
    target with the cited display — not a string-only key-existence check.
    One shared Ruleset for the whole class (cached fixture, no re-parse)."""

    # legacy key -> (tab, B-cell row)
    WORKBOOK_CELLS = {
        "Cannon Attack Robot": ("Tanks", 47),
        "Missile Attack Robot": ("Vehicles", 162),
        "Plasma Super Mech": ("Tanks", 96),
        "Scout Robot": ("Vehicles", 35),
    }

    @classmethod
    def setUpClass(cls):
        sys.path.insert(0, str(ROOT / "tools" / "audit"))
        from miniyaml import Ruleset
        cls.rules = Ruleset(ROOT)
        cls.units = sd.all_units(sd.ledger_docs())
        cls.nmap = sd.load_name_map()

    @classmethod
    def tearDownClass(cls):
        cls.rules = None
        cls.units = None
        cls.nmap = None

    def test_aliases_resolve_through_loader_ruleset_and_ledger(self):
        for legacy, (fn, actor, display, _pack) in ALIASES.items():
            if legacy not in self.WORKBOOK_CELLS:
                continue  # the three pre-existing aliases are covered elsewhere
            with self.subTest(alias=legacy):
                # real loader (normalized key -> target), not a dict literal
                self.assertEqual(self.nmap[sd.norm(legacy)], actor)
                # ACTIVE ruleset resolution: the target actor exists in the
                # live mod yaml, not only in the balance ledger
                self.assertIsNotNone(self.rules.resolve(actor),
                                     f"{actor} does not resolve in the active rules")
                # ledger target with the cited current display
                ledger_name, _section, u = self.units[actor]
                self.assertEqual(pathlib.Path(fn).stem, ledger_name)
                self.assertEqual(u.get("name"), display)
                # the legacy workbook row still exists at the cited cell
                import openpyxl
                wb = openpyxl.load_workbook(sd.LEGACY, read_only=True, data_only=False)
                try:
                    tab, row = self.WORKBOOK_CELLS[legacy]
                    self.assertEqual(wb[tab].cell(row=row, column=2).value, legacy)
                finally:
                    wb.close()

    def test_old_ids_are_migration_history_not_current_actors(self):
        """The chain's intermediate and old ids must NOT be active — the alias
        must point at the current id only."""
        for old in ("future_robot_cannon", "future_robot_missiles",
                    "future_mech_plasma", "futu_wheel",
                    "robot_cannon.futu", "robot_missiles.futu",
                    "mech_plasma.futu", "wheel.futu"):
            self.assertIsNone(self.rules.resolve(old), f"{old} unexpectedly active")
            self.assertNotIn(old, self.units)


if __name__ == "__main__":
    unittest.main()
