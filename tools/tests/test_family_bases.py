"""The §12.0j family bases: one level-less `^Warhead_<Family>` per generated family.

DESIGN §12.0j (amended 2026-09-26, "retire now, reshape later"): each family's base is
today's HOME-level profile (Medium; Railgun is Heavy-only) WITHOUT the level tilt, which
the C# bell applies at runtime from `Heaviness`. Supersedes the single-family CannonAP
pilot tests; every check they made now runs on all 52 bases.

  F1  APPENDED, NEVER WOUND IN. Default stdout = the finalized legacy output
      (`shield_uniqueness.apply` over phase 1) + the bases section, byte for byte. The
      legacy portion is therefore exactly what it was before bases existed.
  F2  ONE PER FAMILY. Every generated family has exactly one base; Nuclear (hand-tuned)
      and Sniper (hand-made) have none; an explicit `--continuous-family` request adds
      nothing and a bad one fails clear before any shield map is built.
  F3  PROFILE = the home level's construction minus the tilt, through `family()` itself:
      the base's Versus equals `family()` at the home level with `level_tilt` disabled.
      And never the tilted one (the double bell), wherever the tilt moves anything.
  F4  EVERY EXTRA CARRIED. Chips, meters, IntegrityScale, area-state feeds and every other
      field of the home template reach the base; only the fields the ruling changes differ.
      This is the defect that restricted the pilot to one family.
  F5  SHARED PROFILE. SharedVersus + the home h, no PercentageVersus table, and
      PercentageScale = 100 x home top / growth(home h): CannonAP 2000, Magic 4000,
      Sonic 800, Railgun 2000 (Heavy home, growth 1.25).
  F6  GEOMETRY from the MEDIUM slot (the C# scales (h+2)/3), for Railgun too.
  F7  SHIELD = the home template's final phase-2 value, distinct across all bases, and
      the level-less header stays invisible to phase 2.
  F8  SPLICE PLACEMENT. A base sits directly after its family's last levelled template;
      re-splicing is byte-identical.
"""

from __future__ import annotations

import contextlib
import io
import os
import pathlib
import subprocess
import sys
import unittest
from unittest import mock

import _bootstrap  # noqa: F401 — sys.path side effect

ROOT = pathlib.Path(_bootstrap.REPO_ROOT)
BALANCE = ROOT / "tools" / "balance"
GEN = BALANCE / "gen_weapon_template.py"
sys.path.insert(0, str(BALANCE))

# `USE_BELL` is read at import time: import with the switch OFF, then restore the caller's
# environment exactly (absent stays absent), so no other test in the process is affected.
_BELL_ENV = "CAMEO_HEAVINESS_BELL"
_BELL_SAVED = os.environ.pop(_BELL_ENV, None)
try:
    import gen_weapon_template as gen  # noqa: E402
finally:
    if _BELL_SAVED is not None:
        os.environ[_BELL_ENV] = _BELL_SAVED

import shield_uniqueness  # noqa: E402
import splice_templates  # noqa: E402

SUBPROCESS_TIMEOUT = 300


def _run_gen(*args):
    env = dict(os.environ)
    env.pop(_BELL_ENV, None)
    env["PYTHONIOENCODING"] = "utf-8"
    return subprocess.run([sys.executable, str(GEN), *args], cwd=str(ROOT),
                          capture_output=True, timeout=SUBPROCESS_TIMEOUT, env=env)


def _phase1_text():
    old = sys.argv
    sys.argv = [str(GEN)]
    try:
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            gen._generate()
        return buf.getvalue()
    finally:
        sys.argv = old


def _blocks(text):
    return splice_templates.parse_blocks(text.replace("\r\n", "\n"))


def _versus(block):
    """[(armor, value)] under the MAIN warhead's `Versus:` (depth 2), in emitted order."""
    rows, inside = [], False
    for line in block:
        if line == "\t\tVersus:":
            inside = True
            continue
        if inside:
            if line.startswith("\t\t\t") and not line.startswith("\t\t\t\t"):
                armor, _, value = line.strip().rpartition(":")
                rows.append((armor.strip(), int(value)))
            else:
                break
    return rows


def _field(block, key, depth=2):
    marker = "\t" * depth + key + ":"
    for line in block:
        if line.startswith(marker):
            return line[len(marker):].strip()
    return None


# The fields the ruling changes between a home template and its base (F4).
RULED = ("Versus", "PercentageVersus", "PercentageScale", "Heaviness", "HeavinessMode",
         "Spread", "Falloff")


def _skeleton(block, tag, name):
    """A block's lines with the tag normalised and every RULED field (and the rows of
    the two tables) removed — what must be IDENTICAL between a base and its home."""
    out, skip_depth = [], None
    for line in block[1:]:
        depth = len(line) - len(line.lstrip("\t"))
        if skip_depth is not None:
            if depth > skip_depth:
                continue
            skip_depth = None
        key = line.strip().split(":", 1)[0]
        if depth == 2 and key in RULED:
            if line.rstrip().endswith(":"):
                skip_depth = depth
            continue
        out.append(line.replace(tag, name))
    return out


class _Built(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.phase1 = _phase1_text()
        cls.final = gen.shield_final_map(cls.phase1, gen.SHIELD_FLOOR_TARGET,
                                         gen.SHIELD_CEIL_TARGET)
        cls.default = _run_gen()
        if cls.default.returncode:
            raise AssertionError(cls.default.stderr.decode("utf-8", "replace"))
        cls.text = cls.default.stdout.decode("utf-8").replace("\r\n", "\n")
        cls.blocks = _blocks(cls.text)
        cls.calls = {nm: (args, kw) for nm, _h, args, kw in gen.family_calls()}

    def home(self, nm):
        return gen.base_home_level(self.calls[nm][0][3])


class F1AppendedNeverWoundIn(_Built):
    def test_default_output_is_legacy_plus_bases_exactly(self):
        legacy = shield_uniqueness.apply(self.phase1, gen.SHIELD_FLOOR_TARGET,
                                         gen.SHIELD_CEIL_TARGET)
        self.assertEqual(self.text, legacy + "\n\n" + gen.family_bases(self.phase1))

    def test_no_base_header_inside_the_legacy_portion(self):
        legacy = self.text[:self.text.index(gen.BASE_NOTES)]
        for nm in gen.BASE_FAMILIES:
            self.assertNotIn(f"\n^Warhead_{nm}:\n", legacy)


class F2OnePerFamily(_Built):
    def test_every_generated_family_has_exactly_one_base(self):
        self.assertEqual(len(gen.BASE_FAMILIES), 52)
        heads = [ln for ln in self.text.split("\n") if ln.startswith("^Warhead_")]
        for nm in gen.BASE_FAMILIES:
            self.assertEqual(heads.count(f"^Warhead_{nm}:"), 1, nm)

    def test_hand_made_families_get_no_base(self):
        for nm in ("Nuclear", "Sniper"):
            self.assertNotIn(nm, gen.BASE_FAMILIES)
            self.assertNotIn(f"^Warhead_{nm}", self.blocks)

    def test_explicit_request_adds_nothing(self):
        proc = _run_gen(gen.CONTINUOUS_FLAG, "CannonAP", "Flame")
        self.assertEqual(proc.returncode, 0)
        self.assertEqual(proc.stdout, self.default.stdout)

    def test_bad_requests_fail_clear_before_any_shield_map(self):
        for bad in (["Nuclear"], ["Sniper"], ["NotAFamily"], ["cannonap"], [], ["--list"]):
            with self.assertRaises(SystemExit):
                gen._validated_continuous([gen.CONTINUOUS_FLAG, *bad])
        proc = _run_gen(gen.CONTINUOUS_FLAG, "Nuclear")
        self.assertNotEqual(proc.returncode, 0)
        self.assertEqual(proc.stdout, b"")

    def test_family_filter_filters_the_bases_too(self):
        proc = _run_gen("Flame")
        self.assertEqual(proc.returncode, 0, proc.stderr.decode("utf-8", "replace"))
        bases = [n for n in _blocks(proc.stdout.decode("utf-8")) if n.count("_") == 1]
        self.assertEqual(bases, ["^Warhead_Flame"])


class F3ProfileIsTheUntiltedHome(_Built):
    def _home_block(self, nm, tilt):
        args, kw = self.calls[nm]
        home = self.home(nm)
        args = (*args[:3], (home,))
        patch = (mock.patch.object(gen, "level_tilt", lambda rows, level: rows)
                 if not tilt else contextlib.nullcontext())
        with patch:
            return family_lines(gen.family(*args, **kw))

    def test_base_versus_is_the_home_construction_without_the_tilt(self):
        for nm in gen.BASE_FAMILIES:
            with self.subTest(nm):
                base = dict(_versus(self.blocks[f"^Warhead_{nm}"]))
                ref = dict(_versus(self._home_block(nm, tilt=False)))
                base.pop("Shield"), ref.pop("Shield")   # F7 checks Shield
                self.assertEqual(base, ref)

    def test_no_double_bell(self):
        moved = 0
        for nm in gen.BASE_FAMILIES:
            untilted = dict(_versus(self._home_block(nm, tilt=False)))
            tilted = dict(_versus(self._home_block(nm, tilt=True)))
            untilted.pop("Shield"), tilted.pop("Shield")
            if untilted == tilted:
                continue                      # flat families: the tilt moves nothing
            moved += 1
            base = dict(_versus(self.blocks[f"^Warhead_{nm}"]))
            base.pop("Shield")
            self.assertNotEqual(base, tilted, f"{nm}: base carries the Python tilt")
        self.assertGreater(moved, 40, "precondition: the tilt should move most families")

    def test_the_r16_stretch_is_applied(self):
        # The pilot predated R16 and skipped `bell_stretch`; the base must not.
        order16 = gen.build_order(*gen.WEAPONS["CannonAP"][:2])
        main = gen.fit_band_floor(gen._untilted_main("CannonAP", order16, "Medium"))
        unstretched = dict(gen.mean_normalise(main))
        base = dict(_versus(self.blocks["^Warhead_CannonAP"]))
        self.assertNotEqual(base["Superheavy"], round(unstretched["Superheavy"]))


def family_lines(text):
    return text.split("\n")


class F4EveryExtraCarried(_Built):
    def test_base_differs_from_its_home_only_in_the_ruled_fields(self):
        for nm in gen.BASE_FAMILIES:
            with self.subTest(nm):
                home = self.home(nm)
                tag = f"{nm}_{home}"
                base = _skeleton(self.blocks[f"^Warhead_{nm}"], nm, nm)
                ref = _skeleton(self.blocks[f"^Warhead_{tag}"], tag, nm)
                self.assertEqual(base, ref)

    def test_named_extras_are_present(self):
        cases = {"Laser": "\tWarhead@Laser_ExtraDamage: SpreadDamage",
                 "Railgun": "\tWarhead@Railgun_ExtraDamage: SpreadDamage",
                 "Tesla": "\tWarhead@Tesla_ExtraDamage: SpreadDamage",
                 "Sonic": "\tWarhead@Sonic_Debuff: ApplyPhysicalState"}
        for nm, line in cases.items():
            self.assertIn(line, self.blocks[f"^Warhead_{nm}"], nm)
        flame = self.blocks["^Warhead_Flame"]
        self.assertTrue(any("PhysicalState" in ln for ln in flame), "Flame meter dropped")
        for nm, integ in gen.FAMILY_INTEGRITY_SCALE.items():
            if nm in gen.BASE_FAMILIES:
                self.assertIn(f"\t\tIntegrityScale: {integ}", self.blocks[f"^Warhead_{nm}"])


class F5SharedProfile(_Built):
    def test_mode_scalar_and_no_percentage_table(self):
        for nm in gen.BASE_FAMILIES:
            with self.subTest(nm):
                b = self.blocks[f"^Warhead_{nm}"]
                self.assertEqual(_field(b, "HeavinessMode"), "SharedVersus")
                self.assertEqual(_field(b, "Heaviness"),
                                 str(gen.BASE_HOME_H[self.home(nm)]))
                for key in ("PercentageVersus", "PercentageVersusLight",
                            "PercentageVersusHeavy"):
                    self.assertIsNone(_field(b, key))

    def test_percentage_scale_pins(self):
        pins = {"CannonAP": 2000, "Bullet": 2000, "Magic": 4000, "Sonic": 800,
                "Railgun": 2000}
        for nm, scale in pins.items():
            self.assertEqual(_field(self.blocks[f"^Warhead_{nm}"], "PercentageScale"),
                             str(scale), nm)

    def test_home_h_reproduces_the_home_top_row(self):
        # The base at its home h deals, per 2000 Damage, what the home template's TOP
        # percentage row dealt at Scale 10000: 2000 x top / 20000 basis points x 100.
        import percentage_damage as pd
        for nm in gen.BASE_FAMILIES:
            with self.subTest(nm):
                home = self.home(nm)
                ref = self.blocks[f"^Warhead_{nm}_{home}"]
                top = max(v for a, v in _pct_rows(ref) if a not in gen.NON_ARMOR_ROWS)
                scale = int(_field(self.blocks[f"^Warhead_{nm}"], "PercentageScale"))
                num, den = pd.shared_growth(gen.BASE_HOME_H[home])
                self.assertAlmostEqual(scale * num / den, 100 * top, delta=1)

    def test_railgun_is_the_only_non_medium_home(self):
        homes = {nm: self.home(nm) for nm in gen.BASE_FAMILIES}
        self.assertEqual({nm for nm, h in homes.items() if h != "Medium"}, {"Railgun"})
        self.assertEqual(homes["Railgun"], "Heavy")


def _pct_rows(block):
    rows, inside = [], False
    for line in block:
        if line == "\t\tPercentageVersus:":
            inside = True
            continue
        if inside:
            if line.startswith("\t\t\t"):
                armor, _, value = line.strip().rpartition(":")
                rows.append((armor.strip(), int(value)))
            else:
                break
    return rows


class F6Geometry(_Built):
    def test_spread_and_falloff_come_from_the_medium_slot(self):
        mi = list(gen.LEVELS).index("Medium")
        for nm in gen.BASE_FAMILIES:
            with self.subTest(nm):
                kw = self.calls[nm][1]
                b = self.blocks[f"^Warhead_{nm}"]
                self.assertEqual(_field(b, "Spread"), str(gen.at(kw["spreads"], mi)))
                self.assertEqual(_field(b, "Falloff"), gen.at(kw["falloffs"], mi))
                if f"^Warhead_{nm}_Medium" in self.blocks:
                    med = self.blocks[f"^Warhead_{nm}_Medium"]
                    self.assertEqual(_field(b, "Spread"), _field(med, "Spread"))

    def test_railgun_heavy_radius_is_medium_times_four_thirds(self):
        base = int(_field(self.blocks["^Warhead_Railgun"], "Spread"))
        heavy = int(_field(self.blocks["^Warhead_Railgun_Heavy"], "Spread"))
        self.assertAlmostEqual(base * 4 / 3, heavy, delta=1.0)


class F7Shield(_Built):
    # Maintainer 2026-09-26: a base at its home h reproduces today's Shield, so the authored
    # value is the home value divided back through the runtime's (2000 + h) / 2000 scaling.
    def _round_trip(self):
        import effective_heaviness as eh
        out = {}
        for nm in gen.BASE_FAMILIES:
            home = self.home(nm)
            base = dict(_versus(self.blocks[f"^Warhead_{nm}"]))["Shield"]
            ref = dict(_versus(self.blocks[f"^Warhead_{nm}_{home}"]))["Shield"]
            self.assertEqual(ref, self.final[(nm, home)])
            out[nm] = (base, ref, eh.shield_coefficient(base, gen.BASE_HOME_H[home]))
        return out

    def test_home_h_reproduces_the_home_templates_shield(self):
        trips = self._round_trip()
        for nm, (_base, ref, eff) in trips.items():
            with self.subTest(nm):
                self.assertLessEqual(abs(eff - ref), 2, "Shield off the home template's")
        # 2 is the MINIMAL worst case (no distinct assignment exists within 1), and 30 exact is
        # the most any assignment reaches at that bound. 33 exact is only reachable by pushing
        # one family 4 points off, which the solver deliberately does not do.
        exact = sum(1 for _b, ref, eff in trips.values() if eff == ref)
        self.assertGreaterEqual(exact, 30)
        entries = [(nm, ref, gen.BASE_HOME_H[self.home(nm)]) for nm, (_b, ref, _e) in trips.items()]
        import effective_heaviness as eh
        solved = gen.base_shield_values(entries)
        worst = max(abs(eh.shield_coefficient(solved[nm], h) - ref) for nm, ref, h in entries)
        self.assertEqual(worst, 2, "the solver must reach the minimal worst case")

    def test_shield_is_divided_back_not_copied(self):
        # The pilot copied Medium's value and so dealt 1.5x at h = 1.
        for nm, (base, ref, _eff) in self._round_trip().items():
            with self.subTest(nm):
                self.assertLess(base, ref)

    def test_base_shields_are_distinct(self):
        vals = [dict(_versus(self.blocks[f"^Warhead_{nm}"]))["Shield"]
                for nm in gen.BASE_FAMILIES]
        self.assertEqual(len(vals), len(set(vals)))

    def test_levelless_header_is_invisible_to_phase2(self):
        self.assertIsNone(shield_uniqueness.HEADER.match("^Warhead_CannonAP:"))
        self.assertIsNotNone(shield_uniqueness.HEADER.match("^Warhead_CannonAP_Medium:"))


class F8SplicePlacement(unittest.TestCase):
    GEN = {"^Warhead_X_Light": ["^Warhead_X_Light:", "\tA: 1"],
           "^Warhead_X_Medium": ["^Warhead_X_Medium:", "\tA: 2"],
           "^Warhead_X": ["^Warhead_X:", "\tA: 3"]}

    def test_base_names(self):
        self.assertEqual(splice_templates.base_names(self.GEN), {"^Warhead_X"})
        self.assertEqual(splice_templates.family_from("^Warhead_X"), "X")
        self.assertEqual(splice_templates.family_from("^Warhead_X_Medium"), "X")

    def test_base_lands_after_the_last_levelled_block_and_is_idempotent(self):
        lines = ["^Warhead_X_Light:", "\tA: 1", "", "^Warhead_X_Medium:", "\tA: 2", "",
                 "^Other:", "\tB: 1", "", "^Warhead_X:", "\tA: 0", ""]
        once = splice_templates.remove_blocks(lines, {"^Warhead_X"})
        self.assertTrue(splice_templates.place_base(once, "^Warhead_X", self.GEN["^Warhead_X"]))
        self.assertEqual(once[3:9], ["^Warhead_X_Medium:", "\tA: 2", "",
                                     "^Warhead_X:", "\tA: 3", ""])
        twice = splice_templates.remove_blocks(once, {"^Warhead_X"})
        splice_templates.place_base(twice, "^Warhead_X", self.GEN["^Warhead_X"])
        self.assertEqual(once, twice)

    def test_a_family_without_levelled_blocks_is_reported(self):
        self.assertFalse(splice_templates.place_base(["^Other:", "\tB: 1"], "^Warhead_X",
                                                     self.GEN["^Warhead_X"]))


if __name__ == "__main__":
    unittest.main()
