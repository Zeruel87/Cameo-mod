"""Bounded P0/P1 weapon-evidence tests for `extract_peer_units.weapon_stats`.

Synthetic MiniYAML fixtures in a temp mods/ tree only — nothing here reads a
real peer checkout, runs the game, or regenerates any corpus document.
Each blocker from the 2026-09-10 independent review has its regression:
(1) the exact warhead-TYPE allowlist, (2) cadence validity including declared
zero BurstDelays, (3) the default-100 versus fold (never a partial weighted
mean), (4) the percent convention for FirepowerMultiplier (1 = 1 percent),
(5) actor activation/cadence suspects beyond the weapon, and (6) AmmoPool
binding: by Name, missing/empty Armaments unresolvable.
"""

from __future__ import annotations

import pathlib
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "audit"))
sys.path.insert(0, str(ROOT / "tools" / "reference"))
import miniyaml  # noqa: E402
import extract_peer_units as epu  # noqa: E402


def build(tmp, actors, weapons):
    base = tmp / "mods" / "test"
    (base / "rules").mkdir(parents=True, exist_ok=True)
    (base / "weapons").mkdir(parents=True, exist_ok=True)
    (base / "mod.yaml").write_text(
        "Rules:\n    rules/actors.yaml\nWeapons:\n    weapons/weapons.yaml\n", encoding="utf-8")
    (base / "rules" / "actors.yaml").write_text(actors, encoding="utf-8")
    (base / "weapons" / "weapons.yaml").write_text(weapons, encoding="utf-8")
    return miniyaml.Ruleset(tmp, "test")


def ws(rules, actor_id, label=""):
    return epu.weapon_stats(rules, rules.resolve(actor_id), label)


class WeaponEvidenceTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = pathlib.Path(self._tmp.name)
        self._armor = epu._ARMOR_MAP
        epu._ARMOR_MAP = {"sources": {"t": {"map": {"Heavy": "VEH", "Light": "VEH",
                                                    "Medium": "VEH"}, "confidence": "high"}}}

    def tearDown(self):
        epu._ARMOR_MAP = self._armor
        self._tmp.cleanup()

    # ---- shared fixtures -------------------------------------------------- #

    WEAPONS = """\
M60:
    Range: 6c0
    ReloadDelay: 38
    Burst: 5
    BurstDelays: 5, 5, 6, 6
    Warhead@1: SpreadDamage
        Damage: 1000
TOW:
    ReloadDelay: 50
    Warhead@1: SpreadDamage
        Damage: 600
Gun:
    Range: 6c0
    ReloadDelay: 30
    Warhead@1: SpreadDamage
        Damage: 100
"""

    ACTORS_TOW = """\
HMMV:
    Armament:
        Weapon: M60
    AttackTurreted:
HMMV.TOW:
    Inherits: HMMV
    Armament@SECONDARY:
        Name: secondary
        Weapon: TOW
        PauseOnCondition: !ammo
    AmmoPool:
        Armaments: secondary
        Ammo: 1
        AmmoCondition: ammo
    ReloadAmmoPoolCA:
        Delay: 200
        Count: 1
"""

    # ---- inherited secondary slot, retained conditions, raw numbers -------- #

    def test_inherited_secondary_tow(self):
        r = build(self.tmp, self.ACTORS_TOW, self.WEAPONS)
        t = ws(r, "HMMV.TOW")
        self.assertEqual(t["w_evidence"], "incomplete")
        reason = t["w_evidence_reason"]
        self.assertIn("multi_armament: 2 slots", reason)
        self.assertIn("conditional_armament: Armament@SECONDARY (pause_on_condition)", reason)
        self.assertIn("ammo_pool: AmmoPool -> secondary", reason)
        self.assertIn("cadence_trait: ReloadAmmoPoolCA", reason)
        self.assertIsNone(t["w_dps"])
        self.assertFalse(t["w_dps_usable"])
        # the old first-weapon diagnostic is preserved raw
        self.assertAlmostEqual(t["w_dps_raw"], (1000 * 5) / (38 + sum([5, 5, 6, 6])))
        slots = t["weapon_evidence"]
        self.assertEqual([s["weapon"] for s in slots], ["M60", "TOW"])
        gun, tow = slots
        self.assertEqual(gun["ammo_pool"]["binding"], "other")   # recorded, proven inert here
        self.assertEqual(tow["ammo_pool"]["binding"], "bound")
        self.assertEqual(tow["pause_on_condition"], "!ammo")
        # NO all-conditions-false assumption: the gated slot keeps its own
        # raw weapon numbers.
        self.assertEqual(tow["reload_delay"], 50)
        self.assertEqual(tow["burst"], 1)
        self.assertEqual(t["ammo_rearm"][0]["trait"], "ReloadAmmoPoolCA")
        self.assertEqual(t["ammo_rearm"][0]["delay"], "200")   # RAW evidence keeps the source string
        # the base actor alone stays nominal with its unchanged fold
        b = ws(r, "HMMV")
        self.assertEqual(b["w_evidence"], "nominal_direct")
        self.assertAlmostEqual(b["w_dps"], (1000 * 5) / (38 + 22))

    # ---- B4/B6: binding follows Name, not @suffix ------------------------- #

    def test_ammo_binding_uses_name_not_suffix(self):
        actors = """\
SNG:
    Armament:
        Weapon: Gun
    Armament@ALT:
        Name: secondary
        Weapon: Gun
    AmmoPool:
        Armaments: primary
"""
        r = build(self.tmp, actors, self.WEAPONS)
        t = ws(r, "SNG")
        slots = {s["slot"]: s for s in t["weapon_evidence"]}
        self.assertEqual(slots["Armament"]["ammo_pool"]["binding"], "bound")
        self.assertEqual(slots["Armament@ALT"]["ammo_pool"]["binding"], "other")
        self.assertIn("ammo_pool: AmmoPool -> primary", t["w_evidence_reason"])

    # ---- B4: missing / empty Armaments is UNRESOLVABLE -------------------- #

    def test_ammo_pool_missing_or_empty_armaments_unknown(self):
        actors = """\
PoolEmpty:
    Armament:
        Weapon: Gun
    AmmoPool:
        Armaments:
        Ammo: 1
PoolNone:
    Armament:
        Weapon: Gun
    AmmoPool:
        Ammo: 1
"""
        r = build(self.tmp, actors, self.WEAPONS)
        empty = ws(r, "PoolEmpty")
        self.assertIn("ammo_pool_binding_unknown: AmmoPool (empty Armaments)",
                      empty["w_evidence_reason"])
        self.assertIsNone(empty["w_dps"])
        missing = ws(r, "PoolNone")
        self.assertIn(
            "ammo_pool_binding_unknown: AmmoPool (Armaments missing;"
            " engine default differs per source)", missing["w_evidence_reason"])
        self.assertIsNone(missing["w_dps"])

    # ---- B2: repeat-last cadence, declared zeros preserved ---------------- #

    def test_burst_array_repeat_and_zero_semantics(self):
        actors = """\
REP:
    Armament:
        Weapon: B4
ZER:
    Armament:
        Weapon: Z3
"""
        weapons = """\
B4:
    ReloadDelay: 50
    Burst: 4
    BurstDelays: 5, 8
    Warhead@1: SpreadDamage
        Damage: 100
Z3:
    ReloadDelay: 50
    Burst: 3
    BurstDelays: 0, 8
    Warhead@1: SpreadDamage
        Damage: 100
"""
        r = build(self.tmp, actors, weapons)
        rep = ws(r, "REP")
        self.assertEqual(rep["w_evidence"], "nominal_direct")
        self.assertAlmostEqual(rep["w_dps"], (100 * 4) / (50 + (5 + 8 + 8)))
        self.assertEqual(rep["weapon_evidence"][0]["burst_delays"], [5, 8])
        zer = ws(r, "ZER")
        self.assertEqual(zer["w_evidence"], "nominal_direct")
        self.assertAlmostEqual(zer["w_dps"], (100 * 3) / (50 + (0 + 8)))
        self.assertEqual(zer["weapon_evidence"][0]["burst_delays"], [0, 8])

    # ---- B2: invalid / unresolved cadence refused ------------------------- #

    def test_cadence_invalid_values_refused(self):
        actors = """\
FRAC:
    Armament:
        Weapon: WFr
NEG:
    Armament:
        Weapon: WNeg
ZERB:
    Armament:
        Weapon: WZb
NANB:
    Armament:
        Weapon: WNan
INFB:
    Armament:
        Weapon: WInf
BADTOK:
    Armament:
        Weapon: WBad
RLFRAC:
    Armament:
        Weapon: WRf
RLZER:
    Armament:
        Weapon: WRz
RLNEG:
    Armament:
        Weapon: WRn
MISSREL:
    Armament:
        Weapon: WRm
BUNODEL:
    Armament:
        Weapon: WBu
"""
        weapons = """\
WFr:
    ReloadDelay: 50
    Burst: 2.5
    Warhead@1: SpreadDamage
        Damage: 100
WNeg:
    ReloadDelay: 50
    Burst: -2
    Warhead@1: SpreadDamage
        Damage: 100
WZb:
    ReloadDelay: 50
    Burst: 0
    Warhead@1: SpreadDamage
        Damage: 100
WNan:
    ReloadDelay: 50
    Burst: nan
    Warhead@1: SpreadDamage
        Damage: 100
WInf:
    ReloadDelay: 50
    Burst: inf
    Warhead@1: SpreadDamage
        Damage: 100
WBad:
    ReloadDelay: 50
    Burst: 3
    BurstDelays: x, 5
    Warhead@1: SpreadDamage
        Damage: 100
WRf:
    ReloadDelay: 2.5
    Warhead@1: SpreadDamage
        Damage: 100
WRz:
    ReloadDelay: 0
    Warhead@1: SpreadDamage
        Damage: 100
WRn:
    ReloadDelay: -5
    Warhead@1: SpreadDamage
        Damage: 100
WRm:
    Warhead@1: SpreadDamage
        Damage: 100
WBu:
    ReloadDelay: 50
    Burst: 2
    Warhead@1: SpreadDamage
        Damage: 100
"""
        r = build(self.tmp, actors, weapons)
        cases = {
            "FRAC": "invalid_burst: Burst 2.5", "NEG": "invalid_burst: Burst -2",
            "ZERB": "invalid_burst: Burst 0", "NANB": "invalid_burst: Burst nan",
            "INFB": "invalid_burst: Burst inf", "BADTOK": "invalid_burst_delay: x",
            "RLFRAC": "invalid_reload: ReloadDelay 2.5", "RLZER": "invalid_reload: ReloadDelay 0",
            "RLNEG": "invalid_reload: ReloadDelay -5",
            "MISSREL": "unresolved_reload_delay",
            "BUNODEL": "unresolved_burst_cadence: Burst 2 without BurstDelays",
        }
        for aid, frag in cases.items():
            t = ws(r, aid)
            self.assertEqual(t["w_evidence"], "incomplete", aid)
            self.assertIn(frag, t["w_evidence_reason"], aid)
            self.assertIsNone(t["w_dps"], aid)
        # the legacy default-5 diagnostic survives for the plain-unresolved case
        self.assertAlmostEqual(ws(r, "BUNODEL")["w_dps_raw"], (100 * 2) / (50 + 5))

    # ---- B1: the exact warhead TYPE allowlist ----------------------------- #

    def test_warhead_type_allowlist(self):
        actors = """\
NOTYP:
    Armament:
        Weapon: WNoT
PCT:
    Armament:
        Weapon: WPct
CUSTOM:
    Armament:
        Weapon: WCond
"""
        weapons = """\
WNoT:
    ReloadDelay: 30
    Warhead@1:
        Damage: 100
WPct:
    ReloadDelay: 30
    Warhead@1: HealthPercentageDamage
        Damage: 100
WCond:
    ReloadDelay: 30
    Warhead@1: GrantExternalConditionCA
        Condition: decoy
"""
        r = build(self.tmp, actors, weapons)
        notyp = ws(r, "NOTYP")
        self.assertIn("missing_warhead_type", notyp["w_evidence_reason"])
        self.assertIsNone(notyp["w_dps"])
        self.assertEqual(notyp["weapon_evidence"][0]["warheads"][0]["type"], "")
        pct = ws(r, "PCT")
        self.assertIn("unknown_warhead_type: HealthPercentageDamage", pct["w_evidence_reason"])
        self.assertIsNone(pct["w_dps"])
        custom = ws(r, "CUSTOM")
        self.assertIn("unknown_warhead_type: GrantExternalConditionCA",
                      custom["w_evidence_reason"])
        # raw type + fields + all channels retained
        wh = custom["weapon_evidence"][0]["warheads"][0]
        self.assertEqual(wh["type"], "GrantExternalConditionCA")
        self.assertEqual(wh["fields"], {"Condition": "decoy"})
        self.assertNotEqual(wh["channels"], [])
        r_ok = build(self.tmp, "OK:\n    Armament:\n        Weapon: Gun\n", self.WEAPONS)
        self.assertEqual(ws(r_ok, "OK")["w_evidence"], "nominal_direct")

    # ---- B3r: intra-ladder coverage; partial rungs WITHHOLD, never default - #

    def test_ladder_fold_full_coverage_weighted_partial_withheld(self):
        full = """\
FULL:
    Armament:
        Weapon: MIXFULL
PART:
    Armament:
        Weapon: MIXPART
ONEWH:
    Armament:
        Weapon: MIXONE
"""
        weapons = """\
MIXFULL:
    ReloadDelay: 30
    Warhead@1: SpreadDamage
        Damage: 100
        Versus:
            Heavy: 50
            Light: 100
            Medium: 100
    Warhead@2: SpreadDamage
        Damage: 900
        Versus:
            Heavy: 100
            Light: 100
            Medium: 100
MIXPART:
    ReloadDelay: 30
    Warhead@1: SpreadDamage
        Damage: 100
        Versus:
            Heavy: 50
            Light: 100
            Medium: 100
    Warhead@2: SpreadDamage
        Damage: 900
        Versus:
            Heavy: 100
MIXONE:
    ReloadDelay: 30
    Warhead@1: SpreadDamage
        Damage: 100
        Versus:
            Heavy: 50
"""
        r = build(self.tmp, full, weapons)
        f = ws(r, "FULL", "t")
        # both mains declare EVERY mapped rung: per-warhead ladder mean,
        # damage-weighted — exact, not flat
        self.assertAlmostEqual(f["eff_vs_VEH"], (100 * 83.33333333333 + 900 * 100) / 1000 / 100)
        for aid in ("PART", "ONEWH"):
            p = ws(r, aid, "t")
            # an undeclared mapped armor would sit at the engine's 100% only
            # under an UNVERIFIED roster assumption -> withheld, even when the
            # amap may be a superset
            self.assertNotIn("eff_vs_VEH", p, aid)
            self.assertEqual(p["ladders_withheld"], {"VEH": "partial_versus_coverage"}, aid)
            # raw per-armor declared rungs stay visible in the evidence
            one = ws(r, "ONEWH", "t")
            self.assertEqual(one["weapon_evidence"][0]["warheads"][0]["versus"],
                             {"Heavy": "50"})

    # ---- B2r: malformed / nonfinite Damage and Versus never become defaults #

    def test_malformed_and_nonfinite_damage_or_versus_refused(self):
        actors = """\
DMGNAN:
    Armament:
        Weapon: DN
DMGINF:
    Armament:
        Weapon: DI
VSX:
    Armament:
        Weapon: VX
VSINF:
    Armament:
        Weapon: VI
VSNAN:
    Armament:
        Weapon: VN
"""
        weapons = """\
DN:
    ReloadDelay: 30
    Warhead@1: SpreadDamage
        Damage: nan
DI:
    ReloadDelay: 30
    Warhead@1: SpreadDamage
        Damage: inf
VX:
    ReloadDelay: 30
    Warhead@1: SpreadDamage
        Damage: 100
        Versus:
            Heavy: x
VI:
    ReloadDelay: 30
    Warhead@1: SpreadDamage
        Damage: 100
        Versus:
            Heavy: inf
VN:
    ReloadDelay: 30
    Warhead@1: SpreadDamage
        Damage: 100
        Versus:
            Heavy: nan
"""
        r = build(self.tmp, actors, weapons)
        self.assertIn("unresolved_damage: nan", ws(r, "DMGNAN")["w_evidence_reason"])
        self.assertIn("unresolved_damage: inf", ws(r, "DMGINF")["w_evidence_reason"])
        for aid in ("VSX", "VSINF", "VSNAN"):
            t = ws(r, aid, "t")
            self.assertIn("unresolved_versus", t["w_evidence_reason"], aid)
            self.assertIsNone(t["w_dps"], aid)               # refuses nominal certification
            self.assertNotIn("eff_vs_VEH", t, aid)           # never defaults either

    # ---- B4: Modifier is a PERCENT; 1 is a 99% nerf ----------------------- #

    def test_modifier_percent_convention(self):
        actors = """\
TINY:
    Armament:
        Weapon: Gun
    FirepowerMultiplier@tiny:
        Modifier: 1
ELITE:
    Armament:
        Weapon: Gun
    FirepowerMultiplier@elite:
        UpgradeTypes: elite
        Modifier: 140
"""
        r = build(self.tmp, actors, self.WEAPONS)
        tiny = ws(r, "TINY")
        self.assertIn("weapon_modifier: FirepowerMultiplier@tiny", tiny["w_evidence_reason"])
        self.assertIsNone(tiny["w_dps"])
        m = tiny["weapon_modifiers"][0]
        self.assertEqual(m["modifier"], "1")
        self.assertFalse(m["conditional"])
        self.assertTrue(m["nontrivial"])          # 1 = 1 percent, a power change
        elite = ws(r, "ELITE")
        self.assertIn("weapon_modifier: FirepowerMultiplier@elite", elite["w_evidence_reason"])
        me = elite["weapon_modifiers"][0]
        self.assertEqual(me["upgrade_types"], "elite")
        self.assertTrue(me["conditional"])
        self.assertTrue(me["nontrivial"])
        # the conditioned elite state is retained raw and NEVER summed in
        self.assertAlmostEqual(elite["w_dps_raw"], 100 / 30)

    # ---- B5: actor activation / cadence suspects --------------------------- #

    def test_activation_and_cadence_suspects(self):
        actors = """\
TESLA:
    Armament:
        Weapon: Gun
    AttackTesla:
PAUSED:
    Armament:
        Weapon: Gun
    AttackTurreted:
        PauseOnCondition: empdisable
RELOADMOD:
    Armament:
        Weapon: Gun
    AttackTurreted:
    ReloadModifier@slow:
        Modifier: 130
INERT:
    Armament:
        Weapon: Gun
    AttackTurreted:
    ReloadAmmoPoolCA:
        Delay: 200
        Count: 1
"""
        r = build(self.tmp, actors, self.WEAPONS)
        tesla = ws(r, "TESLA")
        self.assertIn("activation_trait: AttackTesla", tesla["w_evidence_reason"])
        self.assertIsNone(tesla["w_dps"])
        self.assertEqual(tesla["activation_traits"][0]["kind"], "activation")
        paused = ws(r, "PAUSED")
        self.assertIn("activation_trait: AttackTurreted", paused["w_evidence_reason"])
        self.assertEqual(paused["activation_traits"][0]["pause_on_condition"], "empdisable")
        reloadmod = ws(r, "RELOADMOD")
        self.assertIn("cadence_trait: ReloadModifier@slow", reloadmod["w_evidence_reason"])
        self.assertIsNone(reloadmod["w_dps"])
        inert = ws(r, "INERT")
        self.assertEqual(inert["w_evidence"], "nominal_direct")   # proven inert, 0 AmmoPools
        self.assertNotIn("cadence_trait", (inert["w_evidence_reason"] or ""))

    # ---- incoming damage + AttackMove: safe false-positive exemptions ----- #

    def test_defensive_incoming_damage_and_attack_move_exemptions(self):
        actors = """\
PROTECTED:
    Armament:
        Weapon: Gun
    DamageMultiplier@shield:
        UpgradeTypes: shielded
        Modifier: 60
ORDMOVE:
    Armament:
        Weapon: Gun
    AttackMove:
        MoveIntoShroud: True
ADMINGRANT:
    Armament:
        Weapon: Gun
    AttackMove:
        AttackMoveCondition: attackmoving
TWOPOL:
    Armament:
        Weapon: Gun
    AmmoPool:
        Armaments: primary
        Ammo: 2
    AmmoPool@extra:
        Armaments: spare
        Ammo: 1
        AmmoCondition: busy
"""
        r = build(self.tmp, actors, self.WEAPONS)
        prot = ws(r, "PROTECTED")
        self.assertEqual(prot["w_evidence"], "nominal_direct")
        self.assertAlmostEqual(prot["w_dps"], 100 / 30)
        d = prot["defensive_modifiers"]
        self.assertEqual(d[0]["trait"], "DamageMultiplier@shield")   # INCOMING protection,
        self.assertEqual(d[0]["modifier"], "60")                     # retained raw, never
        self.assertTrue(d[0]["conditional"])                         # a weapon multiplier
        self.assertEqual(prot["weapon_modifiers"], [])
        move = ws(r, "ORDMOVE")
        self.assertEqual(move["w_evidence"], "nominal_direct")
        self.assertEqual(move["activation_traits"], [])
        granted = ws(r, "ADMINGRANT")
        self.assertIn("activation_trait: AttackMove", granted["w_evidence_reason"])
        self.assertIsNone(granted["w_dps"])
        self.assertEqual(granted["activation_traits"][0]["attack_move_condition"],
                         "attackmoving")
        twopol = ws(r, "TWOPOL")
        self.assertEqual(len(twopol["ammo_pools"]), 2)               # ALL raw pools retained
        self.assertEqual(twopol["ammo_pools"][1]["fields"]["AmmoCondition"], "busy")
        self.assertEqual(twopol["weapon_evidence"][0]["ammo_pool"]["binding"], "bound")

    # ---- simple unconditional case: numeric compatibility ------------------ #

    def test_simple_unconditional_numerical_compat(self):
        r = build(self.tmp, "PLAIN:\n    Armament:\n        Weapon: Gun\n", self.WEAPONS)
        t = ws(r, "PLAIN")
        self.assertEqual(t["w_evidence"], "nominal_direct")
        self.assertIsNone(t["w_evidence_reason"])
        burst = 1
        reload = 30
        old_cycle = reload + 0                     # the old fold, verbatim
        self.assertAlmostEqual(t["w_dps"], (100 * burst) / old_cycle)
        self.assertEqual(t["w_burst"], 1)
        self.assertEqual(t["w_reload"], 30)
        self.assertEqual(t["w_damage"], 100)
        self.assertEqual(t["w_mains"], 1)
        self.assertEqual(t["w_range"], 6144)
        self.assertTrue(t["w_dps_usable"])

    def test_unarmed_and_missing_weapon_fail_closed(self):
        r = build(self.tmp, """\
BARE:
    Turreted:
MISSW:
    Armament:
        Weapon: Ghost
""", self.WEAPONS)
        self.assertEqual(ws(r, "BARE"), {})
        t = ws(r, "MISSW")
        self.assertEqual(t["w_evidence"], "incomplete")
        self.assertIn("weapon_unresolved: Ghost", t["w_evidence_reason"])
        self.assertIsNone(t["w_dps"])
        self.assertFalse(t["w_dps_usable"])
        self.assertNotIn("w_damage", t)
        self.assertFalse(t["weapon_evidence"][0]["weapon_resolved"])
        self.assertEqual(t["weapon_evidence"][0]["weapon"], "Ghost")


if __name__ == "__main__":
    unittest.main()
