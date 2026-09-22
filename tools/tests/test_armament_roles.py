"""The per-armament pairing contract: a cannon's reference is never a missile's.

⛔ THE LOAD-BEARING TEST IS `test_agrees_with_the_missile_role_audit`. This module deliberately
reads a WIDER ValidTargets vocabulary than `audit_missile_role_family.weapon_role`, which fails
closed to "custom" on any token outside {Ground, Water, Air} because it drives four LOWER-ONLY
ratchets. A wider set may only ADD answers — the moment it changes one the audit already gives,
the two files are ruling differently on the same maintainer decision and the ratchets are
measuring something else than they were calibrated on.
"""

from __future__ import annotations

import json
import pathlib
import re
import sys
import tempfile
import unittest
import unittest.mock


ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "audit"))
sys.path.insert(0, str(ROOT / "tools" / "balance"))
sys.path.insert(0, str(ROOT / "tools" / "reference"))

import armament_roles as ar                      # noqa: E402
import miniyaml                                  # noqa: E402
import nominal_condition_context as ncc          # noqa: E402
import reference_distribution as rd              # noqa: E402
from audit_missile_role_family import weapon_role  # noqa: E402


PROJECTILE_EVIDENCE = ROOT / "docs" / "reference" / "ini_projectile_role_evidence.json"


class TargetVocabularyTests(unittest.TestCase):
    def test_absent_valid_targets_is_the_engine_default_and_therefore_ground(self):
        # WeaponInfo.cs:116. 451 of the ~900 peer armaments leave it unwritten, so reading
        # "absent" as "unknown" would abstain on half the corpus.
        self.assertEqual(ar.ROLE_GROUND, ar.role_of_targets(None)[0])
        self.assertEqual(ar.ROLE_GROUND, ar.role_of_targets("")[0])

    def test_the_three_domains(self):
        self.assertEqual(ar.ROLE_AIR, ar.role_of_targets("Air, AirSmall")[0])
        self.assertEqual(ar.ROLE_GROUND, ar.role_of_targets("Ground, Water, Trees")[0])
        self.assertEqual(ar.ROLE_BOTH, ar.role_of_targets("Ground, Water, Air")[0])
        # Red Alert spells its mammoth missile without the word "Air" at all.
        self.assertEqual(ar.ROLE_BOTH, ar.role_of_targets("AirborneActor, Infantry")[0])

    def test_invalid_targets_subtract(self):
        self.assertEqual(ar.ROLE_GROUND, ar.role_of_targets("Ground, Water, Air", "Air")[0])

    def test_a_selector_only_weapon_is_special_not_ground(self):
        # A weapon that can only shoot down rockets belongs to no domain. Calling it ground would
        # hand a real cannon an interceptor as its reference.
        self.assertEqual(ar.ROLE_SPECIAL, ar.role_of_targets("Missile")[0])
        # ...but a point-defence laser that ALSO hits ground is a ground weapon.
        self.assertEqual(ar.ROLE_GROUND, ar.role_of_targets("Ground, Water, Missile")[0])

    def test_an_unclassified_token_makes_the_whole_verdict_abstain(self):
        """SUPERSEDES `..._is_reported_and_stays_neutral` (Astra PR #375 blocker 5).

        The old rule treated an unknown token as neutral and still returned a confident role, so
        `Ground, UnknownFlyingTarget` came back a PROVEN exact ground weapon -- an air weapon
        standing in as ground evidence, the one pairing the maintainer forbade. The vocabulary now
        fails closed; the tokens are still reported so `--audit` can prove coverage.
        """
        role, unknown = ar.role_of_targets("Ground, Water, SomethingNobodyHasSeen")
        self.assertIsNone(role)
        self.assertEqual({"SomethingNobodyHasSeen"}, unknown)
        self.assertIsNone(ar.role_of_targets("Ground, UnknownFlyingTarget")[0])
        self.assertIsNone(ar.role_of_targets("SomethingNobodyHasSeen")[0])
        # A known vocabulary still answers exactly as before.
        self.assertEqual(ar.ROLE_GROUND, ar.role_of_targets("Ground, Water")[0])

    def test_the_three_sets_are_disjoint(self):
        self.assertEqual(set(), ar.AIR_TARGETS & ar.GROUND_TARGETS)
        self.assertEqual(set(), ar.AIR_TARGETS & ar.NEUTRAL_TARGETS)
        self.assertEqual(set(), ar.GROUND_TARGETS & ar.NEUTRAL_TARGETS)


class CycleTests(unittest.TestCase):
    def test_matches_the_existing_burst_cycle_on_the_ledger_shape(self):
        # ONE formula, two parsers (the ledger stores delays as a string, the peer corpus as a
        # list). If these ever disagree the map is drawing an arrow between two rulers.
        for arm in ({"reloaddelay": "72", "burst": "2", "burstdelays": "8"},
                    {"reloaddelay": "68", "burst": "2", "burstdelays": "12"},
                    {"reloaddelay": "50", "burst": "7", "burstdelays": "6"},
                    {"reloaddelay": "80", "burst": "2"},
                    {"reloaddelay": "55", "burst": "1"},
                    {"reloaddelay": "40", "burst": "4", "burstdelays": "3, 5, 7"}):
            raw = str(arm.get("burstdelays") or "").replace(",", " ").split()
            self.assertEqual(
                rd.burst_cycle(arm, rd_num := (lambda v: None if v is None else float(v))),
                ar.cycle_ticks(arm["reloaddelay"], arm["burst"], raw),
                arm)
        del rd_num

    def test_a_burst_without_declared_delays_uses_openras_own_default(self):
        self.assertEqual(80.0 + 5.0, ar.cycle_ticks(80, 2, []))

    def test_the_rate_is_per_cycle_damage_over_the_cycle(self):
        v = ar.view("cameo", "Armament", "w", ar.ROLE_GROUND,
                    damage_per_shot=8000, burst=2, cycle=80.0,
                    weapon_reload=72, weapon_burst=2, weapon_burst_delays=[8])
        self.assertEqual(16000, v["damage_per_cycle"])
        self.assertAlmostEqual(200.0, v["rate"])
        self.assertEqual(72, v["weapon_reload"])
        self.assertEqual(2, v["weapon_burst"])
        self.assertEqual([8], v["weapon_burst_delays"])


class RangeUnitTests(unittest.TestCase):
    def test_ini_ranges_are_cells_and_carry_their_conversion(self):
        # A DTA mammoth reads `5.7` beside a Cameo `6141`. Both are correct and they are not the
        # same unit; the view must say so rather than let a reader compare them.
        views = ar.ini_views({"source": "DTA Enhanced", "weapon": "120mm",
                              "w_range": 5.7, "w_damage": 30, "w_reload": 80})
        self.assertEqual("cells", views[0]["range_unit"])
        self.assertAlmostEqual(5.7 * ar.WDIST_PER_CELL, views[0]["range_wdist"])

    def test_openra_ranges_are_wdist_and_convert_to_themselves(self):
        views = ar.peer_views({"weapon_evidence": [
            {"slot": "Armament", "weapon": "120mm", "range": 4864, "reload_delay": 40,
             "burst": 1, "warheads": [{"damage_num": 4000}]}]})
        self.assertEqual("wdist", views[0]["range_unit"])
        self.assertEqual(4864, views[0]["range_wdist"])


class PairingTests(unittest.TestCase):
    def test_air_and_ground_are_never_paired(self):
        cam = [ar.view("cameo", "Armament", "bomb", ar.ROLE_GROUND, damage_per_shot=1, cycle=1)]
        peer = [ar.view("peer", "Armament", "sam", ar.ROLE_AIR, damage_per_shot=1, cycle=1)]
        pairs, cam_only, peer_only = ar.pair_by_role(cam, peer)
        self.assertEqual([], pairs)
        self.assertEqual(["bomb"], [v["weapon"] for v in cam_only])
        self.assertEqual(["sam"], [v["weapon"] for v in peer_only])

    def test_an_exact_role_claims_its_partner_before_a_both_may_stand_in(self):
        # Without the two-pass order the cannon claims the peer's dual-role missile first and the
        # Cameo missile is left unmatched next to a peer cannon it can never use.
        cam = [ar.view("cameo", "A", "cannon", ar.ROLE_GROUND, damage_per_shot=1, cycle=1),
               ar.view("cameo", "B", "missile", ar.ROLE_BOTH, damage_per_shot=1, cycle=1)]
        peer = [ar.view("peer", "A", "peer_cannon", ar.ROLE_GROUND, damage_per_shot=1, cycle=1),
                ar.view("peer", "B", "peer_missile", ar.ROLE_BOTH, damage_per_shot=1, cycle=1)]
        pairs, cam_only, peer_only = ar.pair_by_role(cam, peer)
        self.assertEqual({("ground", "cannon", "peer_cannon"), ("both", "missile", "peer_missile")},
                         {(r, c["weapon"], p["weapon"]) for r, c, p, _ in pairs})
        self.assertTrue(all(exact for *_x, exact in pairs))
        self.assertEqual(([], []), (cam_only, peer_only))

    def test_a_second_weapon_in_a_compatible_role_is_available_to_the_second_armament(self):
        # ⛔ THE MAINTAINER'S BATTLE TANK. DTA's GDI Medium Tank at elite carries TWO ground-role
        # weapons (the 90 mm cannon and the 70 mm missile launcher — the TS engine puts both on the
        # ground domain), while Cameo's battle tank carries a `ground` cannon and a `both` missile.
        # Keeping only the strongest peer weapon per role let the cannon claim DTA's only candidate
        # and then told the missile no source covered its role.
        cam = [ar.view("cameo", "A", "cannon", ar.ROLE_GROUND, damage_per_shot=8000, cycle=72),
               ar.view("cameo", "B", "missile", ar.ROLE_BOTH, damage_per_shot=8000, cycle=72)]
        peer = [ar.view("peer", "secondary", "90mm", ar.ROLE_GROUND,
                        damage_per_shot=30, cycle=50),
                # THE FIXTURE NOW CARRIES MTNK'S REAL SHAPE. `[MTNK] Primary=90mmDummy` is a
                # zero-damage rate-of-fire stub, so this elite weapon fills a slot that was empty
                # and is ADDITIVE -- which is exactly why an ORIGINAL may still reference it while
                # every same-gun `E`-suffix upgrade is excluded. Without these two fields the
                # fixture modelled a replacement and stopped matching the live artifact.
                ar.view("peer", "elite", "70mmMsl1", ar.ROLE_GROUND,
                        damage_per_shot=30, cycle=50, baseline=False, gate="elite",
                        replaces="90mmDummy", additive=True)]
        pairs, cam_only, _peer_only = ar.pair_by_role(cam, peer)
        got = {c["weapon"]: p["weapon"] for _r, c, p, _e in pairs}
        self.assertEqual({"cannon": "90mm", "missile": "70mmMsl1"}, got)
        self.assertEqual([], cam_only)

    def test_a_zero_damage_dummy_is_never_anybodys_reference(self):
        # ⛔ CLAUSE 5. DTA's `90mmDummy` is a real armament with a real range whose only job is to
        # set the rate of fire for the next slot; the first bench handed it to the Battle Tank's
        # missile as its reference.
        cam = [ar.view("cameo", "A", "cannon", ar.ROLE_GROUND, damage_per_shot=8000, cycle=72),
               ar.view("cameo", "B", "missile", ar.ROLE_BOTH, damage_per_shot=8000, cycle=72)]
        peer = [ar.view("peer", "primary", "90mmDummy", ar.ROLE_GROUND,
                        damage_per_shot=0, cycle=50),
                ar.view("peer", "secondary", "90mm", ar.ROLE_GROUND,
                        damage_per_shot=30, cycle=50)]
        pairs, cam_only, _peer_only = ar.pair_by_role(cam, peer)
        self.assertEqual({"90mm"}, {p["weapon"] for _r, _c, p, _e in pairs})
        self.assertEqual(["missile"], [v["weapon"] for v in cam_only])

    def test_a_rank_gated_weapon_never_displaces_an_ordinary_one(self):
        cam = [ar.view("cameo", "A", "cannon", ar.ROLE_GROUND, damage_per_shot=1, cycle=1)]
        peer = [ar.view("peer", "primary", "gun", ar.ROLE_GROUND, damage_per_shot=10, cycle=1),
                ar.view("peer", "elite", "elitegun", ar.ROLE_GROUND, damage_per_shot=99,
                        cycle=1, baseline=False, gate="elite")]
        pairs, *_ = ar.pair_by_role(cam, peer)
        self.assertEqual([("gun", True)], [(p["weapon"], e) for _r, _c, p, e in pairs])

    def test_a_source_that_cannot_state_a_role_now_abstains_entirely(self):
        """REVERSES `..._still_votes_on_the_main_weapon` on the maintainer's ruling, 2026-09-13:
        *"ambiguous role or identity must abstain."*

        The old fallback bought coverage for the seven INI sources that pin no `source_sha256` by
        guessing that their hardest-hitting role-less weapon was a main gun. Astra falsified the
        guess: a secondary AA gun (`FlakTrackAAGun`, `RA1RedEyeAA`) can out-damage its own
        chassis' main gun and was then reported as GROUND main-gun evidence. The cost is real and
        deliberate -- `ra2_soviets_apocalypsetank` goes from five votes to none -- and it is
        counted in the pairing report's stats rather than hidden.
        """
        cam = [ar.view("cameo", "A", "cannon", ar.ROLE_GROUND, damage_per_shot=24000, cycle=68),
               ar.view("cameo", "B", "aa_missile", ar.ROLE_AIR, damage_per_shot=32000, cycle=73)]
        peer = [ar.view("peer", "primary", "120mmx", None, damage_per_shot=200, cycle=60)]
        pairs, cam_only, _peer_only = ar.pair_by_role(cam, peer)
        self.assertEqual([], pairs)
        self.assertEqual({"cannon", "aa_missile"}, {v["weapon"] for v in cam_only})

    def test_an_unproven_source_never_displaces_a_proven_pairing(self):
        cam = [ar.view("cameo", "A", "cannon", ar.ROLE_GROUND, damage_per_shot=1, cycle=1)]
        peer = [ar.view("peer", "A", "peer_cannon", ar.ROLE_GROUND, damage_per_shot=1, cycle=1),
                ar.view("peer", "B", "mystery", None, damage_per_shot=99, cycle=1)]
        pairs, *_ = ar.pair_by_role(cam, peer)
        self.assertEqual([("ground", "cannon", "peer_cannon", True)],
                         [(r, c["weapon"], p["weapon"], e) for r, c, p, e in pairs])

    def test_an_unproven_source_with_no_damage_does_not_vote(self):
        cam = [ar.view("cameo", "A", "cannon", ar.ROLE_GROUND, damage_per_shot=1, cycle=1)]
        peer = [ar.view("peer", "primary", "dummy", None, damage_per_shot=0, cycle=1)]
        self.assertEqual([], ar.pair_by_role(cam, peer)[0])

    def test_the_strongest_baseline_armament_represents_its_role(self):
        # `td_gdi_lighttankmkii` reports a 1-damage point-defence laser as its gun when the FIRST
        # armament wins; within one role the alternatives are still alternatives.
        views = [ar.view("cameo", "A", "pointdefense", ar.ROLE_GROUND,
                         damage_per_shot=1, cycle=1),
                 ar.view("cameo", "B", "cannon", ar.ROLE_GROUND, damage_per_shot=8000, cycle=1)]
        self.assertEqual("cannon", ar.strongest_by_role(views)[ar.ROLE_GROUND]["weapon"])

    def test_the_peer_baseline_gate_reads_openras_condition_grammar(self):
        # The peer corpus spells conditions as OpenRA expressions; the SHARED evaluator decides,
        # so the CA MLRS's four upgrade tiers cannot be mistaken for four parallel armaments.
        for cond, expected in ((None, True), ("", True),
                               ("!hypersonic-upgrade && !hammerhead-upgrade", True),
                               ("hypersonic-upgrade", False), ("!player-iraq", True),
                               ("player-iraq", False),
                               # ⛔ FAIL CLOSED. An unparsable condition counted as baseline would
                               # double a unit's armament set, which is the defect this lane fixes.
                               ("garbage(((", False)):
            self.assertEqual(expected, ar._peer_baseline({"requires_condition": cond}), cond)

    def test_an_upgrade_gated_armament_is_not_baseline(self):
        views = [ar.view("cameo", "A", "base", ar.ROLE_GROUND, damage_per_shot=1, cycle=1),
                 ar.view("cameo", "B", "upgraded", ar.ROLE_GROUND, damage_per_shot=9,
                         cycle=1, baseline=False)]
        self.assertEqual("base", ar.strongest_by_role(views)[ar.ROLE_GROUND]["weapon"])


class ProjectileRoleEvidenceTests(unittest.TestCase):
    """The INI half: a TS weapon's domain lives on the PROJECTILE, as `AA=` / `AG=`."""

    @classmethod
    def setUpClass(cls):
        if not PROJECTILE_EVIDENCE.exists():
            raise unittest.SkipTest("ini_projectile_role_evidence.json not generated")
        cls.doc = json.loads(PROJECTILE_EVIDENCE.read_text(encoding="utf-8"))
        cls.dta = {e["source"]: e for e in cls.doc["sources"]}["DTA Enhanced"]["projectiles"]

    def test_the_name_trap_is_read_from_the_flags_not_the_spelling(self):
        # ⛔ `[AGHeatSeeker2]` — "AG" in the name — declares `$Inherits=AGHeatSeeker` and then
        # `AA=yes`. It is the DTA mammoth Tusk and it is DUAL-role, which is what makes it the
        # right partner for Cameo's MissileAP and CA's `MammothTusk` (Air, AirSmall, Infantry).
        # A name classifier calls it anti-ground and pairs an air missile against a cannon.
        self.assertEqual("both", self.dta["AGHeatSeeker2"]["role"])
        self.assertTrue(self.dta["AGHeatSeeker2"]["aa"])
        self.assertTrue(self.dta["AGHeatSeeker2"]["ag"])
        self.assertEqual("air", self.dta["AAHeatSeeker"]["role"])
        self.assertEqual("ground", self.dta["HeatSeeker"]["role"])

    def test_an_undeclared_projectile_takes_the_engine_default_and_says_so(self):
        self.assertEqual("ground", self.dta["TracerM"]["role"])
        self.assertEqual([], self.dta["TracerM"]["declared"])
        self.assertEqual({"AA": False, "AG": True}, {k: self.doc["engine_default"][k]
                                                     for k in ("AA", "AG")})

    def test_every_cited_projectile_resolves(self):
        for entry in self.doc["sources"]:
            self.assertEqual([], entry["undeclared"], entry["source"])
            self.assertEqual(entry["referenced"], entry["resolved"], entry["source"])

    def test_the_vocabulary_is_the_same_one_the_openra_side_uses(self):
        self.assertEqual(list(ar.ROLES), self.doc["role_vocabulary"])


class RulesetTests(unittest.TestCase):
    """The slow half — one Ruleset, shared."""

    @classmethod
    def setUpClass(cls):
        cls.rules = miniyaml.Ruleset(ROOT)

    def test_agrees_with_the_missile_role_audit(self):
        checked = 0
        for name in sorted(self.rules.weapons):
            if name.startswith("^"):
                continue
            try:
                node = self.rules.resolve_weapon(name)
            except Exception:
                continue
            if node is None:
                continue
            audit = weapon_role(node)
            if audit == "custom":
                continue        # the audit declines to rule; this module may still answer
            mine, _unknown = ar.cameo_weapon_role(self.rules, name)
            self.assertEqual(audit, mine, name)
            checked += 1
        # A guard that silently checked nothing is the failure mode this repo has hit four times.
        self.assertGreater(checked, 1500, "the agreement check scanned almost nothing")

    def test_the_fire_hawks_two_weapons_are_separated(self):
        # THE MAINTAINER'S OWN CASE. One actor, two weapons, a TEN-FOLD range gap; the folded
        # model reports `max(ranges)` and hands the bomb the Sidewinders' reach.
        views = {v["weapon"]: v for v in ar.cameo_views(_ledger_row("td_gdi_firehawk"), self.rules)}
        missiles = views["td_gdi_firehawk_firehawkmissiles_AA"]
        bomb = views["td_gdi_firehawk_firehawkbomb"]
        self.assertEqual(ar.ROLE_AIR, missiles["role"])
        self.assertEqual(12500, missiles["range"])
        self.assertEqual(ar.ROLE_GROUND, bomb["role"])
        self.assertEqual(1250, bomb["range"])

    def test_the_mammoths_cannon_and_missile_split(self):
        views = ar.cameo_views(_ledger_row("td_gdi_mammothtank"), self.rules)
        by_role = ar.strongest_by_role(views)
        self.assertEqual("td_gdi_mammothtank_120mmdual", by_role[ar.ROLE_GROUND]["weapon"])
        self.assertEqual("td_gdi_mammothtank_mammothmissiles", by_role[ar.ROLE_BOTH]["weapon"])
        self.assertNotIn(ar.ROLE_AIR, by_role)



def _peer(slot, weapon, role, dmg, *, gate=None, replaces=None, additive=False, baseline=True):
    return ar.view("ini", slot, weapon, role, damage_per_shot=dmg, baseline=baseline,
                   gate=gate, replaces=replaces, additive=additive, range_unit="cells", rng=5)


def _cameo(slot, weapon, role, dmg):
    return ar.view("cameo", slot, weapon, role, damage_per_shot=dmg)


class ReferenceTierTests(unittest.TestCase):
    """Astra PR #375 blocker 1 + the maintainer's rule, 2026-09-13: originals reference the BASE
    weapon, promotion/expanded actors the elite or upgraded replacement, and a replacement never
    counts beside the weapon it replaces. MTNK's dummy is the one additive exception."""

    def setUp(self):
        # A DTA-shaped reference: a base cannon and its `E`-suffix elite REPLACEMENT.
        self.replacement = [_peer("primary", "120mm", ar.ROLE_GROUND, 50),
                            _peer("elite", "120mmE", ar.ROLE_GROUND, 80, gate="elite",
                                  replaces="120mm", baseline=False)]
        # The MTNK shape: a zero-damage dummy primary, a real secondary, an ADDITIVE elite missile.
        self.additive = [_peer("primary", "90mmDummy", ar.ROLE_GROUND, 0),
                         _peer("secondary", "90mm", ar.ROLE_GROUND, 40),
                         _peer("elite", "70mmMsl1", ar.ROLE_BOTH, 30, gate="elite",
                               replaces="90mmDummy", additive=True, baseline=False)]

    def test_an_original_never_sees_the_elite_replacement(self):
        bench = ar.tier_bench(self.replacement, ar.TIER_ORIGINAL)
        self.assertEqual(["120mm"], [v["weapon"] for v in bench])

    def test_an_expanded_actor_sees_the_replacement_INSTEAD_OF_its_base(self):
        """INSTEAD OF, never BESIDE - this is the blocker itself. FRIGATE, BEHEMOTH, YAK and
        HTNKARTY could vote with both the normal weapon and its replacement, so one gun cast two
        votes and the bench looked one weapon deeper than the reference really is."""
        bench = ar.tier_bench(self.replacement, ar.TIER_EXPANDED)
        self.assertEqual(["120mmE"], [v["weapon"] for v in bench])

    def test_the_additive_elite_is_a_real_second_weapon_in_both_tiers(self):
        for tier in ar.TIERS:
            names = [v["weapon"] for v in ar.tier_bench(self.additive, tier)]
            self.assertIn("70mmMsl1", names, tier)
            self.assertIn("90mm", names, tier)          # displaces nothing
            self.assertIn("90mmDummy", names, tier)     # clause 5 drops it later, not here

    def test_the_battle_tank_keeps_dtas_elite_missile_although_it_is_an_original(self):
        """The maintainer's own case, end to end: `[MTNK] Primary=90mmDummy` is a rate-of-fire
        stub, so `Elite=70mmMsl1` fills a slot that was empty and is a genuinely extra weapon."""
        doc = json.loads((ROOT / "docs/balance/derived/armament_pairing.json")
                         .read_text(encoding="utf-8"))
        entry = doc["actors"]["td_gdi_battletank"]
        elite = [p for s in entry["sources"].values() for p in s.get("pairs", ())
                 if p["peer"].get("gate") == "elite"]
        self.assertEqual(1, len(elite))
        self.assertEqual("70mmMsl1", elite[0]["peer"]["weapon"])
        self.assertEqual("td_gdi_battletank_m1a1missiles", elite[0]["cameo"]["weapon"])

    def test_the_tier_rule_agrees_with_the_reports_original_test(self):
        """TWO COPIES OF ONE RULE, PINNED TOGETHER. `armament_roles.reference_tier` duplicates
        `build_reference_report.is_original` rather than importing the whole report stack; this is
        what makes that duplication safe."""
        import build_reference_report as brr
        assignment = json.loads(
            (ROOT / "docs/balance/derived/reference_assignment.json").read_text(encoding="utf-8")
        )["assignment"]
        checked = 0
        for actor, sources in assignment.items():
            checked += 1
            expect = ar.TIER_ORIGINAL if brr.is_original(sources) else ar.TIER_EXPANDED
            self.assertEqual(expect, ar.reference_tier(sources), actor)
        self.assertGreater(checked, 300)


class UnprovenRoleTests(unittest.TestCase):
    """Astra PR #375 blocker 3 + maintainer: "ambiguous role or identity must abstain"."""

    def test_a_role_less_peer_weapon_never_pairs(self):
        cam = [_cameo("Armament", "cannon", ar.ROLE_GROUND, 100)]
        peer = [_peer("primary", "MysteryGun", None, 90)]
        pairs, cam_only, _ = ar.pair_by_role(cam, peer)
        self.assertEqual([], pairs)
        self.assertEqual(["cannon"], [v["weapon"] for v in cam_only])

    def test_a_secondary_AA_gun_can_no_longer_stand_in_as_ground_evidence(self):
        """The measured shape Astra named: an unproven AA gun OUT-DAMAGES its own chassis' main
        gun, so a max-damage fallback reported it as the ground main-gun reference."""
        cam = [_cameo("Armament", "cannon", ar.ROLE_GROUND, 100)]
        peer = [_peer("primary", "MainGun", None, 40),
                _peer("secondary", "FlakTrackAAGun", None, 120)]
        pairs, _cam_only, _ = ar.pair_by_role(cam, peer)
        self.assertEqual([], pairs)

    def test_the_apocalypse_only_uses_the_explicitly_proven_missile(self):
        doc = json.loads((ROOT / "docs/balance/derived/armament_pairing.json")
                         .read_text(encoding="utf-8"))
        entry = doc["actors"]["ra2_soviets_apocalypsetank"]
        pairs = [(source, pair) for source, data in entry["sources"].items()
                 for pair in data.get("pairs", ())]
        self.assertEqual(1, len(pairs))
        self.assertEqual("Mental Omega", pairs[0][0])
        self.assertEqual("RA2MammothTusk_AA", pairs[0][1]["cameo"]["weapon"])
        self.assertEqual("air", pairs[0][1]["role"])
        self.assertIn({"weapon": "RA2120xmm", "role": "ground"},
                      doc["uncovered_armaments"]["ra2_soviets_apocalypsetank"])


class EveryArmamentPairsTests(unittest.TestCase):
    """Astra PR #375 blocker 2: same-role weapons must not disappear into one 'strongest'."""

    def test_three_ground_weapons_are_three_armaments(self):
        cam = [_cameo("Armament", "flamer", ar.ROLE_GROUND, 400),
               _cameo("Armament@B", "bigcannon", ar.ROLE_GROUND, 240),
               _cameo("Armament@S", "smallcannon", ar.ROLE_GROUND, 80)]
        self.assertEqual(["flamer", "bigcannon", "smallcannon"],
                         [v["weapon"] for v in ar.cameo_armaments(cam)])

    def test_the_same_gun_in_two_slots_is_one_armament(self):
        cam = [_cameo("Armament", "gun", ar.ROLE_GROUND, 100),
               _cameo("Armament@GARRISONED", "gun", ar.ROLE_GROUND, 100)]
        self.assertEqual(1, len(ar.cameo_armaments(cam)))

    def test_a_second_cameo_gun_claims_the_references_second_gun(self):
        cam = [_cameo("Armament", "main", ar.ROLE_GROUND, 200),
               _cameo("Armament@B", "second", ar.ROLE_GROUND, 100)]
        peer = [_peer("primary", "PeerMain", ar.ROLE_GROUND, 50),
                _peer("secondary", "PeerSecond", ar.ROLE_GROUND, 20)]
        pairs, cam_only, _ = ar.pair_by_role(cam, peer)
        self.assertEqual([], cam_only)
        self.assertEqual({("main", "PeerMain"), ("second", "PeerSecond")},
                         {(c["weapon"], p["weapon"]) for _r, c, p, _e in pairs})


class EvidenceFingerprintTests(unittest.TestCase):
    """Astra PR #375 blocker 4: hashes must be enforced where the evidence is CONSUMED."""

    def test_a_source_whose_corpus_pin_moved_contributes_nothing(self):
        import extract_ini_projectile_roles as ipr
        doc = {"schema": 1, "sources": [{"source": "DTA Enhanced",
                                         "rules_sha256": "0" * 64, "overlay_sha256": None,
                                         "projectiles": {"X": {"role": "ground"}}}]}
        kept, dropped = ipr._verified_sources(doc, ROOT)
        self.assertEqual([], kept)
        self.assertEqual(1, len(dropped))

    def test_source_verification_reads_the_requested_root(self):
        import extract_ini_projectile_roles as ipr
        with tempfile.TemporaryDirectory() as temp:
            root = pathlib.Path(temp)
            corpus = root / "docs" / "reference" / "ini_corpus.json"
            corpus.parent.mkdir(parents=True)
            corpus.write_text(json.dumps({
                "source": "DTA Enhanced",
                "source_sha256": "a" * 64,
                "overlay_sha256": "b" * 64,
            }) + "\n", encoding="utf-8")
            doc = {"sources": [{"source": "DTA Enhanced",
                                "rules_sha256": "a" * 64,
                                "overlay_sha256": "b" * 64}]}
            kept, dropped = ipr._verified_sources(doc, root)
            self.assertEqual(doc["sources"], kept)
            self.assertEqual([], dropped)

    def test_the_real_evidence_still_verifies(self):
        import extract_ini_projectile_roles as ipr
        import extract_ini_elite_weapons as ielite
        self.assertTrue(ipr.load(ROOT))
        self.assertEqual([], ipr.load.dropped)
        self.assertTrue(ielite.load(ROOT))
        self.assertEqual([], ielite.load.dropped)

    def test_the_pairing_artifact_records_what_it_was_built_from(self):
        import build_armament_pairing_report as bap
        doc = json.loads((ROOT / "docs/balance/derived/armament_pairing.json")
                         .read_text(encoding="utf-8"))
        self.assertEqual(bap.input_fingerprints(ROOT), doc["inputs"])

    def test_pairing_fingerprints_are_stable_across_lf_and_crlf_checkouts(self):
        import build_armament_pairing_report as bap
        with tempfile.TemporaryDirectory() as temp:
            path = pathlib.Path(temp) / "input.txt"
            path.write_bytes(b"alpha\nbeta\n")
            lf = bap.canonical_text_sha256(path)
            path.write_bytes(b"alpha\r\nbeta\r\n")
            self.assertEqual(lf, bap.canonical_text_sha256(path))
            path.write_bytes(b"alpha\r\nchanged\r\n")
            self.assertNotEqual(lf, bap.canonical_text_sha256(path))

    def test_a_stale_pairing_artifact_is_refused_not_rendered(self):
        import build_reference_report as brr
        doc = json.loads((ROOT / "docs/balance/derived/armament_pairing.json")
                         .read_text(encoding="utf-8"))
        stale = dict(doc, inputs=dict.fromkeys(doc["inputs"], "0" * 64))
        brr._PAIRING.clear()
        try:
            with unittest.mock.patch.object(
                    pathlib.Path, "read_text", return_value=json.dumps(stale)):
                with self.assertRaises(ValueError):
                    brr.pairing_document()
        finally:
            brr._PAIRING.clear()

    def test_malformed_missing_empty_and_incomplete_artifacts_are_refused(self):
        import build_armament_pairing_report as bap
        import build_reference_report as brr
        path = ROOT / "docs/balance/derived/armament_pairing.json"
        doc = json.loads(path.read_text(encoding="utf-8"))
        expected = bap.input_fingerprints(ROOT)

        for change in (
                lambda bad: bad.update(schema=999),
                lambda bad: bad.update(actors={}),
                lambda bad: bad.update(inputs=dict(list(expected.items())[:1])),
                lambda bad: bad.update(stats={"actors": len(bad["actors"]) + 1})):
            bad = json.loads(json.dumps(doc))
            change(bad)
            with self.assertRaises(ValueError):
                brr._validate_pairing_document(bad, expected)

        brr._PAIRING.clear()
        try:
            with unittest.mock.patch.object(pathlib.Path, "read_text", return_value="{"):
                with self.assertRaisesRegex(ValueError, "malformed"):
                    brr.pairing_document()
        finally:
            brr._PAIRING.clear()

    def test_structured_zero_match_rows_are_not_called_structureless(self):
        doc = json.loads((ROOT / "docs/balance/derived/armament_pairing.json")
                         .read_text(encoding="utf-8"))
        for actor in ("asianalliance_asiancommando", "asianalliance_quasar"):
            self.assertNotIn(actor, doc["no_structured_reference"])
            self.assertIn(actor, doc["uncovered_armaments"])


class ArmamentRenderingTests(unittest.TestCase):
    def test_hero_armaments_select_the_hero_population(self):
        import build_reference_report as brr
        ordinary = (object(), object())
        hero = (object(), object())
        crows = {"hero": {"hero": True}, "ordinary": {"hero": False}}
        self.assertEqual(hero, brr._projection_context("hero", crows, *ordinary, hero))
        self.assertEqual(ordinary, brr._projection_context("ordinary", crows, *ordinary, hero))

    def test_unknown_cameo_role_renders_an_explicit_abstention(self):
        import build_reference_report as brr

        class Distribution:
            cameo_votes = {"mystery": {"weapon_model_eligible": False}}

        doc = {"actors": {"mystery": {
            "roles": [None],
            "armaments": [{"weapon": "MysteryGun", "role": None, "baseline": True,
                            "range_wdist": 1024, "range_unit": "wdist",
                            "damage_per_cycle": 100}],
            "sources": {"Peer": {"peer": "X", "pairs": []}},
        }}}
        body = []
        brr._PAIRING[:] = [doc]
        try:
            brr.emit_armament_pairing(body, ["mystery"], {"mystery": []},
                                       object(), Distribution(),
                                       {"mystery": {"type": "vehicle"}})
        finally:
            brr._PAIRING.clear()
        rendered = "".join(body)
        self.assertIn("unknown / unproven", rendered)
        self.assertIn("abstains", rendered)


class PerArmamentComponentTargetTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import build_armament_pairing_report as bap
        import build_reference_report as brr
        import reference_targets as rt

        cls.bap = bap
        cls.brr = brr
        cls.rt = rt
        cls.peers = rd.peer_rows()
        cls.dist = rd.build_distributions(cls.peers)
        rt.add_cost_distribution(cls.dist, cls.peers)
        cls.cdist = rt.cameo_context()
        assignment = json.loads(
            (ROOT / "docs/balance/derived/reference_assignment.json").read_text(
                encoding="utf-8"
            )
        )["assignment"]
        index_rows = cls.peers + rd.peer_variant_rows() + rd.peer_hero_rows()
        cls.attached = rt.expand_families(
            rt.attach(assignment, rt.peer_index(index_rows)), cls.peers
        )
        cls.doc = json.loads(
            (ROOT / "docs/balance/derived/armament_pairing.json").read_text(
                encoding="utf-8"
            )
        )

    def rocket_targets(self, actor):
        entry = self.doc["actors"][actor]
        main = self.brr._armament_rows(entry)[0]
        cast = [
            (source, pair)
            for source, source_data in entry["sources"].items()
            for pair in source_data.get("pairs", ())
            if pair["cameo"].get("weapon") == main["weapon"]
        ]
        self_vote = self.cdist.cameo_votes[actor]
        targets = {}
        for stat in ("w_range", "w_damage", "w_reload", "w_burst", "w_dps"):
            targets[stat], used = self.brr._armament_component_target(
                entry,
                cast,
                self.attached[actor],
                self.dist,
                self.cdist,
                "infantry",
                stat,
                self_vote.get(stat),
            )
            self.assertEqual(3, used, stat)
        return main, targets

    def test_pairing_schema_retains_authored_components(self):
        self.assertEqual(self.bap.PAIRING_SCHEMA, self.doc["schema"])
        main = self.doc["actors"]["td_gdi_rocketsoldier"]["armaments"][0]
        self.assertEqual(56.0, main["weapon_reload"])
        self.assertEqual(1, main["weapon_burst"])
        self.assertEqual([], main["weapon_burst_delays"])

    def test_frozen_self_vote_receipt_binds_only_the_td_pair(self):
        bindings = self.brr.singleton_self_vote_bindings()
        self.assertEqual(
            {"td_gdi_rocketsoldier", "td_nod_rocketsoldier"},
            set(bindings),
        )
        for actor, binding in bindings.items():
            self.assertEqual(
                self.doc["actors"][actor]["armaments"][0]["weapon"],
                binding["weapon"],
            )
            self.assertEqual(
                self.cdist.cameo_votes[actor]["w_damage"],
                binding["snapshot_values"]["w_damage"],
            )

    def test_frozen_self_vote_receipt_rejects_incomplete_or_unbound_evidence(self):
        receipt_path = ROOT / "docs/reference/cameo_singleton_armament_self_votes_20260914.json"
        original = json.loads(receipt_path.read_text(encoding="utf-8"))
        bad_docs = []
        bad_hash = json.loads(json.dumps(original))
        bad_hash["source_ledgers"]["tiberiandawn_gdi.json"]["sha256"] = "0" * 64
        bad_docs.append(bad_hash)
        missing_value = json.loads(json.dumps(original))
        del missing_value["bindings"]["td_gdi_rocketsoldier"]["snapshot_values"]["w_reload"]
        bad_docs.append(missing_value)

        for bad in bad_docs:
            with self.subTest(kind=len(json.dumps(bad))):
                with tempfile.TemporaryDirectory() as temp:
                    path = pathlib.Path(temp) / "receipt.json"
                    path.write_text(json.dumps(bad), encoding="utf-8")
                    self.brr._SINGLETON_BINDINGS.clear()
                    with unittest.mock.patch.object(self.brr, "SINGLETON_SELF_VOTES", path):
                        with self.assertRaises(ValueError):
                            self.brr.singleton_self_vote_bindings()
        self.brr._SINGLETON_BINDINGS.clear()
        self.brr.singleton_self_vote_bindings()

    def test_bound_actor_refuses_a_second_baseline_armament(self):
        entry = self.doc["actors"]["td_gdi_rocketsoldier"]
        main = self.brr._armament_rows(entry)[0]
        with self.assertRaisesRegex(ValueError, "armament count moved"):
            self.brr.singleton_self_vote_row(
                "td_gdi_rocketsoldier", [main, dict(main)], self.cdist
            )

    def test_burst_is_directly_pooled_and_ignores_the_self_vote(self):
        target, used = self.rt.armament_target(
            [({"source": "A"}, 1), ({"source": "A"}, 3), ({"source": "B"}, 4)],
            None,
            None,
            "infantry",
            "w_burst",
            cameo_vote=99,
        )
        self.assertEqual(3, target)  # median(A=2, B=4)
        self.assertEqual(2, used)

    def test_td_rocket_pair_uses_role_paired_four_voice_components(self):
        expected = {
            "w_range": 6264.360092626203,
            "w_damage": 16341.2549997169,
            "w_reload": 55.650643641621535,
            "w_burst": 1.0,
            "w_dps": 294.23802589174227,
        }
        for actor in ("td_gdi_rocketsoldier", "td_nod_rocketsoldier"):
            with self.subTest(actor=actor):
                main, targets = self.rocket_targets(actor)
                for stat, value in expected.items():
                    self.assertAlmostEqual(value, targets[stat], places=8, msg=stat)

                proposal = {
                    stat: self.brr._snap_armament_component(stat, targets[stat])
                    for stat in ("w_range", "w_damage", "w_reload", "w_burst")
                }
                guard = self.rt.dps_guard(
                    {
                        "w_damage": main["damage_per_cycle"],
                        "w_burst": main["weapon_burst"],
                        "w_reload": main["weapon_reload"],
                        "w_dps": main["rate"],
                    },
                    proposal,
                    targets["w_dps"],
                )
                self.assertEqual("ok", guard["verdict"])
                self.assertAlmostEqual(16341 / 56, guard["composed_dps"])
                self.assertLess(abs(guard["disagreement"] - 1), 0.01)

    def test_fractional_burst_is_withheld_instead_of_rounded_into_the_guard(self):
        self.assertIsNone(self.brr._snap_armament_component("w_burst", 1.5))
        self.assertIn("HOLD 1.5", self.brr._armament_component_cell(
            1, 1.5, None, 3, 3, "w_burst", False
        ))
        main = self.doc["actors"]["td_gdi_rocketsoldier"]["armaments"][0]
        self.assertIn("WITHHELD", self.brr._armament_dps_guard_cell(
            main, {}, None, None, rejected_component=True
        ))

    def test_modeled_charge_cycle_is_not_reconstructed_from_weapon_fields(self):
        main = self.doc["actors"]["ra1_soviets_teslacoil"]["armaments"][0]
        self.assertEqual(131.0, main["cycle"])
        self.assertEqual(3.0, main["weapon_reload"])
        self.assertEqual(1, main["weapon_burst"])
        self.assertEqual(3.0, ar.cycle_ticks(
            main["weapon_reload"], main["weapon_burst"], main["weapon_burst_delays"]
        ))
        self.assertIn("WITHHELD", self.brr._armament_dps_guard_cell(
            main, {}, None, None
        ))

    def test_main_actor_row_routes_weapon_values_to_the_component_table(self):
        page = (ROOT / "docs/audit/latest/reference_map_playtest_20260914.html").read_text(
            encoding="utf-8"
        )
        rows = [
            row
            for row in re.findall(r"<tr>.*?</tr>", page, re.DOTALL)
            if "<code>td_gdi_rocketsoldier</code>" in row
        ]
        self.assertTrue(rows)
        self.assertIn("see per-armament components", rows[0])
        self.assertNotIn('data-v="15461.', rows[0])



class ChargeAttackCycleTests(unittest.TestCase):
    """The charge law, and the part of it that is deliberately NOT implemented.

    Maintainer law, 2026-09-14: *"charged weapons come at a discount but the attack cycle duration
    is reload delay plus charge delay"* - BOTH, never either - with the full rate identity

        DPS = damage x burst / attack cycle
        attack cycle = reload delay + sum of ALL burst delays + charge delay

    and "DPS" a NAME, not a unit: it is damage per TICK.

    ⛔ THESE TESTS PIN THE IMPLEMENTED NUMBERS, NOT THE RULED ONES, ON PURPOSE. The trait's
    override of the weapon reload IS applied (#385). The CHARGE term is withheld, because Astra's
    engine trace found three shapes where a naive `cycle + ticks` is not what the engine runs:

      * multi-shot ChargeLevel - the burning Obelisk is Burst 10 / BurstDelays 1 and its
        AttackCharges notifier resets ChargeLevel on every projectile, so later shots recharge;
      * interleaved AttackTesla - the Rail Tower's INITIAL charge is 12; the 3 is its post-shot
        ChargeFire wait, which resumes while the armament is still inside its 10-tick reload,
        exits, and is reacquired through the initial charge again. That restart/reacquisition
        schedule is unresolved, so both 160 and 172 are provisional;
      * random ChargeLevel - `ChargeLevel: 25, 50` is a RANGE and extract_stats keeps the lower
        bound only. Ruled 2026-09-14: take the MEAN of min and max (37.5 here; the dwarf's
        `0, 4` becomes 2, not zero). Four actors carry one; the extractor change is pending.

    The unblock is three extractor fields - ChargeDelay, ShotsPerCharge, range-ness - plus
    recharge-overlap modelling. When that lands, these expectations move to the ruled values in
    ONE deliberate commit, together with `tesla_coil_attack_period`. Until then the gap is pinned
    here and in the claim registry rather than left invisible.

    ⚠ I shipped the withheld version once and Astra held it (PR #386). Two of the figures I
    published were never re-measured after adopting #385's ownership guard: I claimed
    terran_siegetank at 62 (it is 37) and the burning Obelisk at 155 (it is 105).
    """

    @classmethod
    def setUpClass(cls):
        cls.rules = miniyaml.Ruleset(ROOT)

    def test_the_tesla_coil_fires_three_zaps_per_trait_cycle(self):
        views = ar.cameo_views(_ledger_row("ra1_soviets_teslacoil"), self.rules)
        self.assertTrue(views)
        for v in views:
            self.assertEqual(3, v["burst"], v["weapon"])       # AttackTesla MaxCharges
            # ⭐ 100 trait reload + 3 x (3 - 1) inter-zap gaps + the 25-tick wind-up.
            # This was 106 while the charge term was withheld; the ruled 131 is now what
            # `charge_attack_cycle` returns, so the gap this class used to assert is closed.
            self.assertEqual(131.0, v["cycle"], v["weapon"])

    def test_ignoring_the_trait_cycle_overstates_the_rate_14_6x(self):
        """The number DESIGN names, recomputed from the tree rather than quoted.

        ⚠ It MOVED from 11.8x to 14.6x when the wind-up entered the cycle, and that is the
        right direction: a longer true cycle makes reading the weapon alone a bigger lie.
        """
        view = ar.cameo_views(_ledger_row("ra1_soviets_teslacoil"), self.rules)[0]
        naive = view["damage_per_shot"] / 3.0        # the weapon's own 3-tick reload, burst 1
        self.assertAlmostEqual(14.6, naive / view["rate"], places=1)

    def test_the_rate_identity_holds_for_every_implemented_term(self):
        """`DPS = damage x burst / cycle` is asserted as an identity, not described."""
        v = ar.cameo_views(_ledger_row("ra1_soviets_teslacoil"), self.rules)[0]
        # reload + inter-zap gaps + charge - the maintainer's cycle, in full.
        self.assertEqual(100.0 + 3.0 * (3 - 1) + 25.0, v["cycle"])
        self.assertEqual(v["damage_per_shot"] * v["burst"], v["damage_per_cycle"])
        self.assertAlmostEqual(v["damage_per_shot"] * v["burst"] / v["cycle"], v["rate"])

    def test_the_charge_term_is_applied_and_the_cycle_carries_the_whole_wind_up(self):
        """⭐ THE GAP THIS USED TO ASSERT IS CLOSED. It said: "if someone lands the extractor
        work, this fails too - and that is the signal to move every expectation here to the ruled
        values at once." The extractor work landed, so it did, and this is the moved form.

        The wind-up is now counted ONCE for a charge-once actor and once PER SHOT for a
        charge-per-shot one, and the test asserts the decomposition rather than the total, so a
        future change cannot reach the right number by the wrong route.
        """
        row = _ledger_row("ra1_soviets_teslacoil")
        wind_up = row["charge_up"]["ticks"]
        self.assertEqual(25.0, wind_up)
        # ChargeDelay is now recorded - without it the two machines are indistinguishable.
        self.assertEqual(3.0, row["charge_up"]["charge_delay"])
        view = ar.cameo_views(row, self.rules)[0]
        self.assertEqual(131.0, view["cycle"], "the RULED period, now implemented")
        self.assertEqual(106.0, view["cycle"] - wind_up, "and it is 106 plus the wind-up")

    def test_the_rail_tower_pays_its_wind_up_once_per_shot(self):
        """⛔ THE MODE TEST, end to end: charge-per-shot is worth a factor of MaxCharges.

        Weapon reload 10 > ChargeDelay 3, so `ChargeFire` meets a reloading armament, exits, and
        the tower re-enters through `ChargeAttack` - paying `InitialChargeDelay` every shot, as
        the maintainer ruled. 4 x (10 + 10) + 120 + 10 = 210.
        """
        row = _ledger_row("asianalliance_railtower")
        charge = row["charge_up"]
        self.assertEqual(10.0, charge["ticks"])
        self.assertEqual(3.0, charge["charge_delay"])
        self.assertEqual(5, charge["burst"])
        view = ar.cameo_views(row, self.rules)[0]
        self.assertEqual(210.0, view["cycle"])
        # Charge-once would have been 4 x 3 + 120 + 10 = 142. The modes are not close.
        self.assertNotEqual(142.0, view["cycle"])

    def test_the_chargelevel_family_gets_no_cycle_change_at_all(self):
        """`formula.charge_attack_cycle` returns None here - the trait does not own the RELOAD.

        ⛔ That is NOT the same as "the charge costs no time", and reading it that way is what
        produced my withdrawn 146/155 figures. ⚠ The `AttackTesla` charge term is now APPLIED,
        and this family deliberately did NOT move with it: `AttackTesla` owns its actor's reload
        and can therefore say what a cycle is, while a `ChargeLevel` trait only delays a gun that
        keeps its own. The base Obelisk stays 96 and the burning one 105.
        """
        views = ar.cameo_views(_ledger_row("td_nod_obeliskoflight"), self.rules)
        main = [v for v in views if v["weapon"] == "td_nod_obeliskoflight_laserobelisk"]
        self.assertTrue(main)
        for v in main:
            self.assertEqual(1, v["burst"], v["weapon"])
            self.assertEqual(96.0, v["cycle"], v["weapon"])
        burning = [v for v in views
                   if v["weapon"] == "td_nod_obeliskoflight_laserobeliskburning"][0]
        self.assertEqual(10, burning["burst"])
        self.assertEqual(105.0, burning["cycle"], "NOT 155 - I published that and it was wrong")

    def test_a_charge_record_is_not_the_same_as_a_changed_cadence(self):
        """⚠ COUNTING RECORDS IS NOT COUNTING EFFECTS, which is how two wrong figures reached
        DESIGN.md. The jammer has no priced armament view at all, and the dwarf's charge is zero.
        """
        self.assertEqual([], ar.cameo_views(_ledger_row("ra1_allies_mobileradarjammer"),
                                            self.rules))
        # ⭐ THE EXTRACTOR CHANGE LANDED, so this expectation moved with it, as its previous
        # form promised it would: `ChargeLevel: 0, 4` averages to 2, not to the zero the lower
        # bound used to report. The actor still earns no cadence change - 2 ticks against a
        # 60-tick reload - which is the point: a MEASURED near-zero and an UNMEASURED zero are
        # different facts, and only one of them is allowed to claim the flat discount.
        self.assertEqual(2.0, _ledger_row("wc2_humans_dwarvenrifleman")["charge_up"]["ticks"])

    def test_an_ordinary_unit_is_untouched(self):
        view = ar.cameo_views(_ledger_row("td_gdi_grenadier"), self.rules)[0]
        self.assertEqual(1, view["burst"])
        self.assertEqual(42.0, view["cycle"])


class ChargeRangeAveragingTests(unittest.TestCase):
    """⭐ A RANDOM CHARGE RANGE COSTS ITS MEAN (maintainer, 2026-09-14).

        *"regarding the charge with random charge level make it so it counts the average
        between max and min delay ... for the consortium dagger, the charge range from 25 to
        50 so you add 37.5 to the reload delay as attack cycle"*

    `ChargeLevel: 25, 50` is ONE uniform roll the engine makes on every wind-up, not two
    settings. `extract_stats` used to keep `split(",")[0]`, which priced every charged shot as
    though it always rolled the luckiest value.

    ⛔ THE DWARF IS THE CASE THAT MATTERS, and it moves the price the OPPOSITE way from what
    "give it a charge time" suggests. `charge_price_multiplier` treats `share <= 0` as *charges,
    but we cannot see by how much* and hands out the FLAT 0.75 floor. So the dwarf's misparsed
    zero was quietly collecting the deepest discount in the table; measuring its real 2 ticks
    against a 60-tick reload moves it to 0.9758 and makes it dearer, not cheaper.
    """

    CASES = {
        "steelconsortium_dagger": 37.5,      # 25, 50 - the maintainer's worked example
        "wc2_humans_dwarvenrifleman": 2.0,   # 0, 4  - a range whose floor is zero
        "wc2_humans_siegeengine": 30.0,      # 20, 40
        "wc2_orcs_siegeengine": 30.0,        # 20, 40
    }

    def test_the_parser_averages_min_and_max(self):
        from extract_stats import charge_scalar
        self.assertEqual(37.5, charge_scalar("25, 50"))
        self.assertEqual(2.0, charge_scalar("0, 4"))
        self.assertEqual(30.0, charge_scalar(" 20 , 40 "))
        self.assertEqual(50.0, charge_scalar("50"), "a scalar is its own mean")
        # MIN and MAX, exactly as ruled - not the mean of every element, which a third
        # value would silently redefine. No such field exists in the tree today.
        self.assertEqual(30.0, charge_scalar("20, 25, 40"))

    def test_the_parser_falls_back_rather_than_inventing_a_number(self):
        from extract_stats import charge_scalar
        for junk in ("", "   ", ",", "fast", "25, soon"):
            self.assertEqual(99, charge_scalar(junk, 99), junk)

    def test_the_four_ranged_actors_carry_their_mean(self):
        for actor, ticks in self.CASES.items():
            self.assertEqual(ticks, _ledger_row(actor)["charge_up"]["ticks"], actor)

    def test_the_charge_population_is_pinned_around_the_four(self):
        """⚠ COUNTING RECORDS IS NOT COUNTING EFFECTS - the trap this lane keeps re-learning.

        14 actors carry a `charge_up` record and only these FOUR declare a range, so the other
        ten must be byte-identical across this change. Pinning both numbers means neither a new
        ranged declaration nor a silent revert of the parser can land unnoticed.
        """
        import assign_references as asg
        charged = {a: r["charge_up"] for a, r in asg.ledger().items() if r.get("charge_up")}
        self.assertEqual(14, len(charged))
        self.assertLessEqual(set(self.CASES), set(charged))
        # The ten untouched records still read whole ticks straight from a scalar field.
        for actor, rec in charged.items():
            if actor in self.CASES:
                continue
            ticks = rec.get("ticks")
            if ticks is not None:
                self.assertEqual(float(ticks), float(int(ticks)), actor)

    def test_the_dwarf_no_longer_claims_the_unmeasurable_discount(self):
        """⛔ The finding this change exists for: a zero was buying the FLOOR discount."""
        import formula
        import fit_class
        row = _ledger_row("wc2_humans_dwarvenrifleman")
        cycle = fit_class.charge_cycle_fallback(row)
        self.assertEqual(60.0, cycle)
        was = formula.charge_price_multiplier(dict(row["charge_up"], ticks=0.0), cycle)
        now = formula.charge_price_multiplier(row["charge_up"], cycle)
        self.assertEqual(formula.CHARGE_UP_PRICE_MULTIPLIER, was, "the zero took the flat floor")
        self.assertGreater(now, was)
        self.assertAlmostEqual(0.9758, now, places=4)



class ChargedActorPeriodTests(unittest.TestCase):
    """⛔ FOUR NUMBERS WERE PUBLISHED FOR ONE BUILDING'S ATTACK PERIOD. TWO OF THEM WERE MINE.

    `asianalliance_railtower` has been claimed at 160 (#385), 172 and 180 (two traces of mine,
    both withdrawn) and 220 (the maintainer's 2026-09-14 ruling and immediate-reacquisition
    model). Both
    of my figures failed for ONE reason: they assumed `ChargeFire` keeps ticking while the
    weapon reloads. It does not.

        ChargeFire.Tick:  if (IsCanceling || !attack.CanAttack(self, target)) return true;

    `AttackBase.CanAttack` calls `HasAnyValidWeapons(target, reloadingIsInvalid: true)`, whose
    loop sets `reloadingStateIsValid = !reloadingIsInvalid || !armament.IsReloading` - so a
    reloading armament makes `CanAttack` false and `ChargeFire` EXITS. `ChargeAttack` carries
    the identical guard, so the whole activity ends, the actor reacquires, and it comes back in
    through `ChargeAttack`, paying `InitialChargeDelay` again. That is the mode test:

        weapon reload <= ChargeDelay   charge-once      gap = ChargeDelay
        weapon reload >  ChargeDelay   charge-per-shot  gap = weapon reload + InitialChargeDelay

    ⚠ Both wrong traces gave the RIGHT answer for the two Tesla Coils, whose reload equals
    their `ChargeDelay` and which therefore never exit. Only the Rail Tower separates them,
    which is exactly how both survived review - so this class asserts the MECHANISM as well as
    the totals, and pins the resolved inputs the whole argument depends on.
    """

    # (MaxCharges, trait ReloadDelay, InitialChargeDelay, ChargeDelay, weapon ReloadDelay)
    FIELDS = {
        "ra1_soviets_teslacoil": (3, 100, 25, 3, 3),
        "ra2_soviets_teslacoil": (1, 75, 20, 3, 3),
        "asianalliance_railtower": (5, 120, 10, 3, 10),
    }
    RULED = {"ra1_soviets_teslacoil": 131,
             "ra2_soviets_teslacoil": 95,
             "asianalliance_railtower": 210}

    @classmethod
    def setUpClass(cls):
        cls.rules = miniyaml.Ruleset(ROOT)

    def test_the_resolved_fields_are_what_every_published_number_assumed(self):
        """⚠ Every one of the four numbers is a function of these five fields. If a yaml edit
        moves one, the argument rots and the documents keep quoting a period the tree no longer
        produces - so they are read back off the RESOLVED ruleset, not a remembered table."""
        import sim_attack_tesla as sim
        # AttackTeslaInfo's own defaults - an ABSENT key means the default, never zero.
        defaults = {"MaxCharges": 1, "ReloadDelay": 120, "InitialChargeDelay": 22,
                    "ChargeDelay": 3}
        for actor, expected in self.FIELDS.items():
            node = self.rules.resolve(actor)
            self.assertIsNotNone(node, actor)
            trait = next((c for c in node.children
                          if c.key.split("@", 1)[0] == "AttackTesla"), None)
            self.assertIsNotNone(trait, f"{actor} no longer has AttackTesla")

            def field(key, _t=trait, _d=defaults):
                got = next((c for c in _t.children if c.key == key), None)
                return int(got.value) if got is not None else _d[key]

            arm = next(c for c in node.children if c.key.split("@", 1)[0] == "Armament")
            weapon = self.rules.resolve_weapon(
                str(next(c for c in arm.children if c.key == "Weapon").value))
            reload_node = next((c for c in weapon.children if c.key == "ReloadDelay"), None)
            resolved = (field("MaxCharges"), field("ReloadDelay"), field("InitialChargeDelay"),
                        field("ChargeDelay"), int(reload_node.value) if reload_node else 1)
            self.assertEqual(expected, resolved, actor)
            self.assertEqual(expected, sim.ACTORS[actor],
                             f"{actor}: sim_attack_tesla is out of step with the tree")

    def test_the_immediate_reacquisition_model_reproduces_all_three_rulings(self):
        """This pins the ruled model, not an independently measured runtime period."""
        import sim_attack_tesla as sim
        for actor, spec in self.FIELDS.items():
            period, closed, _, _ = sim.analyse(actor, spec)
            self.assertEqual(closed, period, f"{actor}: simulation and closed form disagree")
            self.assertEqual(self.RULED[actor], period, f"{actor}: ruled value not reproduced")

    def test_reacquisition_delay_lengthens_only_the_interrupted_rail_tower(self):
        import sim_attack_tesla as sim
        for actor, spec in self.FIELDS.items():
            immediate = sim.analyse(actor, spec, reacquire=0)[0]
            delayed = sim.analyse(actor, spec, reacquire=3)[0]
            if actor == "asianalliance_railtower":
                self.assertGreater(delayed, immediate)
            else:
                self.assertEqual(immediate, delayed)

    def test_chargefire_exits_on_a_reloading_armament_rather_than_spinning(self):
        """⛔ THE PREMISE BOTH WITHDRAWN TRACES GOT WRONG, asserted so it cannot come back."""
        import sim_attack_tesla as sim
        mc, tr, ic, cd, wr = self.FIELDS["asianalliance_railtower"]
        shots = sim.simulate(mc, tr, ic, cd, wr)
        gaps = {b - a for a, b in zip(shots, shots[1:])}
        self.assertIn(wr + ic, gaps, "a per-shot actor pays reload PLUS the wind-up each shot")
        # The two shapes the spin premise produced, neither of which the engine does.
        self.assertNotIn(max(cd, wr), gaps, "172's max(ChargeDelay, reload) is not the gap")
        self.assertNotIn(cd * -(-wr // cd), gaps, "180's quantised gap is not the gap either")

    def test_the_mode_test_needs_no_trait_name(self):
        """The detection the maintainer asked for: ChargeDelay against the WEAPON's reload."""
        import sim_attack_tesla as sim
        self.assertEqual("per-shot", sim.charge_mode(3, 10))
        self.assertEqual("once", sim.charge_mode(3, 3))
        self.assertEqual("once", sim.charge_mode(10, 3))
        for actor, (_, _, _, cd, wr) in self.FIELDS.items():
            expected = "per-shot" if actor == "asianalliance_railtower" else "once"
            self.assertEqual(expected, sim.charge_mode(cd, wr), actor)

    def test_ra2_coil_has_one_enabled_armament_in_every_powered_mode(self):
        """The baseline model assumes one firing armament, so the yaml must enforce it.

        The old elite/no-overload expressions left their final ``or`` outside the
        charge-state gate. That enabled both ``Armament@2`` and ``Armament@Charged2``
        together and made ``AttackTesla`` decrement its single charge twice.
        """
        node = self.rules.resolve("ra2_soviets_teslacoil")
        arms = [c for c in node.children if c.key.split("@", 1)[0] == "Armament"]
        self.assertEqual(6, len(arms))
        for charge in range(4):
            for upgrade in (0, 1):
                for elite in (0, 1):
                    context = {
                        "TeslaCoilCharge": charge,
                        "unpowered": 0,
                        "ra2_soviets_upgrade_teslaoverload": upgrade,
                        "rank-elite": elite,
                    }
                    active = [a.key for a in arms
                              if ncc.evaluate_context(a.get("RequiresCondition"), context)]
                    self.assertEqual(1, len(active), (context, active))

    def test_both_wrong_traces_agreed_with_the_coils_which_is_why_they_survived(self):
        """⚠ Why two reviews passed a wrong formula: the coils cannot tell the models apart."""
        for coil in ("ra1_soviets_teslacoil", "ra2_soviets_teslacoil"):
            mc, tr, ic, cd, wr = self.FIELDS[coil]
            spin = (mc - 1) * max(cd, wr) + tr + ic            # the 172 model
            quantised = (mc - 1) * (cd * -(-wr // cd)) + tr + ic   # the 180 model
            self.assertEqual(self.RULED[coil], spin, coil)
            self.assertEqual(self.RULED[coil], quantised, coil)
        # ...and why the Rail Tower is the only actor that discriminates. The three models are
        # computed from the CURRENT fields rather than quoting 172/180/220, which were measured
        # when its wind-up was 12; the point being asserted is that they DIVERGE here and agree
        # on the coils, not the historical constants themselves.
        mc, tr, ic, cd, wr = self.FIELDS["asianalliance_railtower"]
        spin = (mc - 1) * max(cd, wr) + tr + ic
        quantised = (mc - 1) * (cd * -(-wr // cd)) + tr + ic
        per_shot = (mc - 1) * (wr + ic) + tr + ic
        self.assertEqual(3, len({spin, quantised, per_shot}), "the tower separates all three")
        self.assertEqual(self.RULED["asianalliance_railtower"], per_shot)
        # The engine does charge-per-shot here, so the other two are the withdrawn ones.
        self.assertLess(spin, per_shot)
        self.assertLess(quantised, per_shot)

    def test_the_ruled_period_is_now_what_the_pipeline_prices(self):
        """⭐ The extractor records `ChargeDelay`, so the mode is decidable and the term is
        APPLIED. Every ruled figure is now the priced figure - asserted through the pricing path,
        not just the simulator, so the two cannot drift apart."""
        for actor, ruled in self.RULED.items():
            view = ar.cameo_views(_ledger_row(actor), self.rules)[0]
            self.assertEqual(float(ruled), view["cycle"], actor)

    def test_the_autotarget_spread_sits_above_the_priced_floor(self):
        """⚠ What is priced is the FLOOR, and only the floor. A charge-per-shot actor goes idle
        between shots and re-enters on AutoTarget's U{3..7} scan, so its runtime cadence is a
        distribution - measured here so nobody mistakes the priced number for the whole truth."""
        import statistics
        import sim_attack_tesla as sim
        spec = self.FIELDS["asianalliance_railtower"]
        ps = sim.periods_autotarget(spec, seeds=120)
        self.assertEqual(210, min(ps), "the floor is what the pipeline prices")
        self.assertGreater(statistics.mean(ps), 210)
        self.assertLessEqual(max(ps), 210 + 4 * (sim.SCAN_MAX - 1))
        # A charge-once actor never goes idle, so its cadence carries no spread at all.
        for coil in ("ra1_soviets_teslacoil", "ra2_soviets_teslacoil"):
            cps = sim.periods_autotarget(self.FIELDS[coil], seeds=40)
            self.assertEqual({self.RULED[coil]}, set(cps), coil)


def _ledger_row(actor):
    import assign_references as asg
    row = asg.ledger().get(actor)
    if row is None:
        raise AssertionError(f"{actor} is absent from the ledger")
    return row


if __name__ == "__main__":
    unittest.main()
