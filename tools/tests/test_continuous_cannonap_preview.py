"""Focused tests for the CannonAP continuous base (legacy preview CLI retained).

DESIGN §12.0i collapses every levelled `^Warhead_<Family>_<Level>` template into ONE
level-less `^Warhead_<Family>` base plus a continuous `Heaviness` scalar the C# bell
(AreaDamageWarhead.cs / HeavinessBell.cs) applies at runtime. The approved CannonAP
base is appended after the finalized legacy output and spliced into active YAML.
Aedis approved the coexistence policy at 2026-09-10 02:10: borrow Medium Shield,
enforce uniqueness between new bases, and keep compatibility duplicates visible.

  B1  LEGACY BYTE IDENTITY. The legacy portion of default stdout must match the
      frozen-baseline generator's, both executed as BOUNDED subprocesses. The comparison
      runs the WHOLE baseline pipeline (generator + shield_uniqueness + the frozen
      profile JSONs) out of a temp copy so the reference cannot be contaminated by
      the worktree. A preview tool that silently rewrites the legacy output would
      strand every audit that diffs generator output against shipped yaml.

  B2  IDEMPOTENT REQUEST. Default and explicit CLI requests contain exactly one
      level-less CannonAP block; a repeated request must not duplicate it.

  B3  PROFILE = the shared pre-tilt Medium construction + band floor + mean-100 +
      plating/shield finalization, and NOTHING else. If the emitted rows ever equal
      the TILTED variant of the same construction, the preview has grown a Python
      tilt — the double bell — which silently pre-applies the transform the C# owns
      (HeavinessBell.Transform would then run on already-tilted data).

  B4  GEOMETRY = the Medium base the C# scales: Spread/Falloff from the family's
      PHYSICS shape at the Medium level (h=1.0 scales radii by exactly 1), Damage
      2000 placeholder, ReloadDelay/Range/ValidTargets as family() emits them.

  B5  SHARED PROFILE. `HeavinessMode: SharedVersus` and `PercentageScale: 2000`
      must be explicit, and NO PercentageVersus* table may exist — the percentage
      half follows the SAME belled flat table (AreaDamageWarhead rejects any
      percentage table in this mode; the anchors are the LEGACY mode's tables).

  B6  SHARED SHIELD FINALIZATION. The preview's Shield row must be the FINAL
      phase-2 value the existing `^Warhead_CannonAP_Medium` template ships in the
      SAME stdout (approved compatibility), read through `shield_final_map`'s reuse of the shield_uniqueness
      records, never through a bespoke yaml parser. The level-less header must also
      stay invisible to `shield_uniqueness.HEADER`, so a preview block can never be
      mistaken for a levelled template by phase 2.

  B7  RESTRICTED TO CannonAP, CLI AND HELPER BOTH, failing CLEAR. The shared
      scaffold is exact for CannonAP but would silently DROP other standard
      families' extras (Flame's PhysicalState, the energy families' chips, the
      Tesla blends' IntegrityScale). Validation must also fire BEFORE the shield
      map is built or indexed, so an unknown or missing name exits with a message,
      never as a KeyError from the `(family, level)` lookup.

⚠ NO yaml is touched by any of this: the tests read generator stdout and the
generator's own module records only. Resolved live migration is checked separately.
"""

from __future__ import annotations

import contextlib
import io
import os
import pathlib
import subprocess
import sys
import tempfile
import unittest

import _bootstrap  # noqa: F401 — sys.path side effect

ROOT = pathlib.Path(_bootstrap.REPO_ROOT)
BALANCE = ROOT / "tools" / "balance"
GEN = BALANCE / "gen_weapon_template.py"
sys.path.insert(0, str(BALANCE))

# Hermetic import WITHOUT mutating the shell's environment: `USE_BELL` is read at
# import time, so the switch must be OFF while the generator module loads — but a bare
# `os.environ.pop` at module scope would leak the change into every other test sharing
# this process. Save the caller's value, import, then restore exactly what was there
# (absent stays absent; present is put back).
_BELL_ENV = "CAMEO_HEAVINESS_BELL"
_BELL_SAVED = os.environ.pop(_BELL_ENV, None)
try:
    import gen_weapon_template as gen  # noqa: E402
finally:
    if _BELL_SAVED is not None:
        os.environ[_BELL_ENV] = _BELL_SAVED

import gen_weapon_template as gen  # noqa: E402

# Bounded subprocess: a generator that hangs must fail the test, not the session.
SUBPROCESS_TIMEOUT = 300
FAMILY = "CannonAP"


def _run_gen(*args, cwd=ROOT, program=None):
    """Run a generator as a BOUNDED subprocess with a pinned default environment.

    ⚠ `program` must point at the SNAPSHOT copy when comparing against git HEAD —
    defaulting to the worktree generator with a different cwd does NOT run the
    snapshot (its path is absolute), which once made this test pass without ever
    executing the HEAD reference. A reference that is not executed guards nothing.

    `CAMEO_HEAVINESS_BELL` is stripped from the SUBPROCESS-ONLY copy of the
    environment (the parent shell's own environment is never mutated), and
    `PYTHONIOENCODING` is pinned so both sides of a byte comparison are comparable.
    """
    env = dict(os.environ)
    env.pop("CAMEO_HEAVINESS_BELL", None)
    env["PYTHONIOENCODING"] = "utf-8"
    return subprocess.run([sys.executable, str(program or GEN), *args], cwd=str(cwd),
                          capture_output=True, timeout=SUBPROCESS_TIMEOUT, env=env)


# The pre-migration baseline must not move when this test itself is committed.
LEGACY_BASELINE = "50b7d001be845e0ac5a0812d2591e154148c94dc"


def _git_show(rev_path):
    proc = subprocess.run(["git", "show", f"{LEGACY_BASELINE}:{rev_path}"], cwd=str(ROOT),
                          capture_output=True, timeout=SUBPROCESS_TIMEOUT)
    if proc.returncode != 0:
        raise AssertionError(f"git show {LEGACY_BASELINE}:{rev_path} failed: "
                             f"{proc.stderr.decode('utf-8', 'replace')}")
    return proc.stdout


def _head_pipeline_stdout():
    """The frozen pipeline's default stdout, run out of a self-contained temp copy.

    The generator locates its frozen profile data at `__file__/../../..` — the temp
    copy reproduces that layout (docs/reference, docs/design, tools/balance) so the
    The baseline generator measures against the same revision's corpus.
    Git history must include LEGACY_BASELINE; shallow clones fail explicitly.
    """
    with tempfile.TemporaryDirectory() as td:
        tmp = pathlib.Path(td)
        (tmp / "tools" / "balance").mkdir(parents=True)
        (tmp / "docs" / "reference").mkdir(parents=True)
        (tmp / "docs" / "design").mkdir(parents=True)
        (tmp / "tools" / "balance" / "gen_weapon_template.py").write_bytes(
            _git_show("tools/balance/gen_weapon_template.py"))
        (tmp / "tools" / "balance" / "shield_uniqueness.py").write_bytes(
            _git_show("tools/balance/shield_uniqueness.py"))
        (tmp / "docs" / "reference" / "family_profiles.json").write_bytes(
            _git_show("docs/reference/family_profiles.json"))
        (tmp / "docs" / "design" / "invented_family_profiles.json").write_bytes(
            _git_show("docs/design/invented_family_profiles.json"))
        proc = _run_gen(cwd=tmp, program=tmp / "tools" / "balance" / "gen_weapon_template.py")
    if proc.returncode != 0:
        raise AssertionError("Frozen baseline generator failed: "
                             + proc.stderr.decode("utf-8", "replace"))
    return proc.stdout


def _phase1_text():
    """The generator's phase-1 text, produced in-process exactly as __main__ does."""
    old = sys.argv
    sys.argv = [str(GEN)]
    try:
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            gen._generate()
        return buf.getvalue()
    finally:
        sys.argv = old


def _expected_base_tail():
    """The bytes the default output appends after its legacy portion: the separator
    plus the `^Warhead_CannonAP` base built from the generator's own records.

    subprocess pipes run text mode, so Python's default newline translation turns
    every \\n into \\r\\n on Windows before capture; the expected tail is normalized
    with the SAME translation the legacy portion already passed through (that is
    why the `startswith` legacy comparison holds byte-for-byte at all).
    """
    shield_final = gen.shield_final_map(
        _phase1_text(), gen.SHIELD_FLOOR_TARGET, gen.SHIELD_CEIL_TARGET)
    tail = "\n\n" + gen.continuous_family_preview(
        FAMILY, shield_final[(FAMILY, gen.CONTINUOUS_PREVIEW_LEVEL)])
    return tail.replace("\n", "\r\n")


def _blocks(text):
    """Top-level `^Warhead_...:` blocks of the generator's stdout, verbatim.

    Same scan shape as verify_generator_sync.blocks: a col-0 header starts a block,
    the next col-0 line ends it. Subprocess pipes translate newlines on Windows, so
    carriage returns are normalized before scanning (byte comparisons elsewhere use
    the raw bytes).
    """
    out, cur = {}, None
    for line in text.replace("\r\n", "\n").split("\n"):
        if line and not line.startswith(("\t", " ")) and line.startswith("^Warhead_"):
            cur = line.rstrip().rstrip(":")
            out[cur] = [line]
        elif cur is not None:
            if line and not line.startswith(("\t", " ")):
                cur = None
            elif line.strip():
                out[cur].append(line)
    return out


def _sub_table(block_lines, key, depth):
    """The [(armor, value)] rows under the `depth`-tab-indented `key:` line."""
    marker = "\t" * depth + key + ":"
    rows, started = [], False
    for line in block_lines:
        if not started:
            started = line.rstrip() == marker
            continue
        ind = len(line) - len(line.lstrip("\t"))
        if ind <= depth or not line.strip():
            if started and line.strip():
                break
            if ind <= depth:
                break
            continue
        armor, _, value = line.strip().rpartition(":")
        rows.append((armor.strip(), int(value)))
    return rows


def _field(block_lines, key, depth):
    """The value of the `depth`-tab-indented `key: value` line, or None."""
    marker = "\t" * depth + key + ":"
    for line in block_lines:
        if line.rstrip() == marker:
            return ""
        if line.startswith(marker):
            return line[len(marker):].strip()
    return None


def _levelled_shield(block_lines):
    for line in block_lines:
        s = line.strip()
        if s.startswith("Shield: "):
            return int(s[len("Shield: "):])
    return None


class DefaultByteIdentity(unittest.TestCase):
    """B1 — the default output is HEAD's legacy output PLUS the explicit new base.

    Historical helper/test names say HEAD; the reference is now the immutable
    LEGACY_BASELINE commit, including its profile JSON inputs, not current HEAD.
    The base is LIVE in the default output now (Aedis 2026-09-10 02:10/02:14), so
    byte identity is asserted SPLIT: the legacy portion before the base must be
    byte-identical to the git-HEAD pipeline's whole output, and the appended tail
    must be exactly the expected `^Warhead_CannonAP` base — nothing else.
    """

    @classmethod
    def setUpClass(cls):
        cls.head = _head_pipeline_stdout()
        cls.cur = _run_gen()
        cls.expected_tail = _expected_base_tail()

    def test_legacy_portion_is_still_byte_identical_to_git_HEAD(self):
        self.assertEqual(self.cur.returncode, 0, "current generator failed: "
                         + self.cur.stderr.decode("utf-8", "replace"))
        self.assertTrue(
            self.cur.stdout.startswith(self.head),
            "the legacy portion of the default output drifted from git HEAD — the "
            "new base must be APPENDED, never wound into the legacy bytes")

    def test_the_appended_tail_is_exactly_the_new_base(self):
        self.assertEqual(
            self.cur.stdout[len(self.head):],
            self.expected_tail.encode("utf-8"),
            "after the legacy portion the default output must contain exactly the "
            "^Warhead_CannonAP base block and nothing else")

    def test_the_head_reference_covers_both_pipeline_files(self):
        # The comparison is HEAD-generator + HEAD-shield_uniqueness: snapshotting only
        # one of the two would let a worktree-side module edit masquerade as identity.
        for rel in ("tools/balance/gen_weapon_template.py",
                    "tools/balance/shield_uniqueness.py"):
            self.assertTrue(_git_show(rel).startswith(b"#!/usr/bin/env python3")
                            or b"python" in _git_show(rel)[:64])


class OptInAppendsPreview(unittest.TestCase):
    """B2 — the preview is appended AFTER the untouched legacy output."""

    @classmethod
    def setUpClass(cls):
        cls.default = _run_gen()
        cls.optin = _run_gen(gen.CONTINUOUS_FLAG, FAMILY)
        if cls.optin.returncode != 0:
            raise AssertionError("opt-in run failed: "
                                 + cls.optin.stderr.decode("utf-8", "replace"))
        cls.text = cls.optin.stdout.decode("utf-8")
        cls.blocks = _blocks(cls.text)

    def test_optin_request_emits_the_same_bytes_as_the_default(self):
        # The base is live in the DEFAULT output now; an explicit --continuous-family
        # CannonAP request is validated but must NOT append it a second time.
        self.assertTrue(self.optin.stdout.startswith(self.default.stdout),
                        "the explicit request must append after the normal finalized "
                        "legacy output, not replace or interleave with it")
        self.assertEqual(self.optin.stdout, self.default.stdout)

    def test_preview_block_is_present_exactly_once(self):
        self.assertEqual([n for n in self.blocks if n == f"^Warhead_{FAMILY}"],
                         [f"^Warhead_{FAMILY}"])

    def test_default_output_carries_the_live_base_once(self):
        self.assertEqual(self.default.returncode, 0)
        default_blocks = _blocks(self.default.stdout.decode("utf-8"))
        self.assertEqual(1, sum(1 for n in default_blocks if n == f"^Warhead_{FAMILY}"))

    def test_rejected_families_fail_clear(self):
        for nm in ("Nuclear", "Sonic", "PhotonCannon"):
            with self.assertRaises(SystemExit):
                gen.continuous_family_preview(nm, 100)


class RestrictedToCannonAP(unittest.TestCase):
    """B7 — the gate holds at BOTH layers and fails clear, never with a KeyError.

    Rationale: `emit_main_warhead` is exact for CannonAP but would silently DROP
    other standard families' extras — Flame's PhysicalState meter, the energy
    families' paid ExtraDamage chips, the Tesla blends' IntegrityScale. Until the
    preview emits those, no other family may pass the gate.
    """

    def test_helper_rejects_other_standard_families(self):
        # Flame (PhysicalState) and Laser (chip) are the two named review cases;
        # Nuclear/Sonic/Bullet/PhotonCannon stand for chip/integrity/special modes.
        for nm in ("Flame", "Laser", "Nuclear", "Sonic", "Bullet", "PhotonCannon"):
            with self.assertRaises(SystemExit):
                gen.continuous_family_preview(nm, 144)

    def test_helper_rejects_unknown_and_mangled_names(self):
        for nm in ("NotAFamily", "cannonap", "CannonAP_Light", ""):
            with self.assertRaises(SystemExit):
                gen.continuous_family_preview(nm, 144)

    def test_validator_rejects_before_any_shield_map_is_built(self):
        # `__main__` calls `_validated_continuous` BEFORE `shield_final_map`, so a bad
        # name must exit with a message here — the map (and its KeyError-prone
        # `(family, level)` index) is never even constructed.
        for nm in ("Flame", "Laser", "NotAFamily"):
            with self.assertRaises(SystemExit):
                gen._validated_continuous([gen.CONTINUOUS_FLAG, nm])

    def test_validator_rejects_a_bare_flag_with_no_value(self):
        with self.assertRaises(SystemExit):
            gen._validated_continuous([gen.CONTINUOUS_FLAG])
        with self.assertRaises(SystemExit):
            gen._validated_continuous([gen.CONTINUOUS_FLAG, "--list"])

    def test_validator_accepts_exactly_the_allowed_family(self):
        self.assertEqual(gen._validated_continuous([gen.CONTINUOUS_FLAG, "CannonAP"]),
                         ["CannonAP"])
        self.assertEqual(gen.CONTINUOUS_PREVIEW_FAMILIES, ("CannonAP",))

    def test_cli_fails_clear_writing_nothing_on_a_rejected_name(self):
        for nm in ("Flame", "Laser", "NotAFamily"):
            proc = _run_gen(gen.CONTINUOUS_FLAG, nm)
            self.assertNotEqual(proc.returncode, 0)
            self.assertIn("CannonAP", proc.stderr.decode("utf-8", "replace"))
            self.assertEqual(proc.stdout, b"",
                             "a rejected preview request must not emit any stdout")

    def test_cli_fails_clear_on_a_bare_flag(self):
        proc = _run_gen(gen.CONTINUOUS_FLAG)
        self.assertNotEqual(proc.returncode, 0)
        self.assertIn("family name is required", proc.stderr.decode("utf-8", "replace"))
        self.assertEqual(proc.stdout, b"")


class PreviewConstruction(unittest.TestCase):
    """B3–B6 — what the emitted base contains, against the generator's own records."""

    @classmethod
    def setUpClass(cls):
        # In-process phase 1, exactly as __main__ runs it, so the expected values come
        # from the generator's own computed records rather than a yaml re-read.
        old = sys.argv
        sys.argv = [str(GEN)]
        try:
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                gen._generate()
            cls.phase1 = buf.getvalue()
        finally:
            sys.argv = old
        cls.shield_final = gen.shield_final_map(
            cls.phase1, gen.SHIELD_FLOOR_TARGET, gen.SHIELD_CEIL_TARGET)
        cls.shield_medium = cls.shield_final[(FAMILY, "Medium")]
        cls.block_text = gen.continuous_family_preview(FAMILY, cls.shield_medium)
        cls.block = [ln for ln in cls.block_text.split("\n")]
        cls.optin_stdout = _run_gen(gen.CONTINUOUS_FLAG, FAMILY).stdout.decode("utf-8")

    def test_heaviness_scalar_is_explicit_and_active(self):
        # Omitted = the disabled sentinel (-1) in AreaDamageWarhead.cs, and a disabled
        # warhead REJECTS the anchors — so the scalar must be authored, at h = 1.0.
        self.assertEqual(_field(self.block, "Heaviness", 2), str(gen.CONTINUOUS_HEAVINESS))
        self.assertEqual(gen.CONTINUOUS_HEAVINESS, 1000)

    def _expected_rows(self, tilted):
        order16 = gen.build_order(*gen.WEAPONS[FAMILY][:2])
        main = gen._untilted_main(FAMILY, order16, gen.CONTINUOUS_PREVIEW_LEVEL)
        if tilted:
            main = gen.level_tilt(main, gen.CONTINUOUS_PREVIEW_LEVEL)
        main = gen.fit_band_floor(main)
        main = gen.mean_normalise(main)
        main = [("Shield", self.shield_medium)] + [(a, v) for a, v in main if a != "Shield"]
        main = [r for r in main if r[0] not in gen.PLATING_CYCLE]
        return gen.plating_rows(FAMILY) + main

    def test_profile_is_the_untilted_medium_construction_plus_shared_finalization(self):
        rows = _sub_table(self.block, "Versus", 2)
        self.assertEqual(rows, self._expected_rows(tilted=False),
                         "the base profile must be exactly the shared pre-tilt Medium "
                         "construction + band floor + mean-100 + platings + final Shield")

    def test_no_double_bell(self):
        untilted = self._expected_rows(tilted=False)
        tilted = self._expected_rows(tilted=True)
        self.assertNotEqual(
            untilted, tilted,
            "precondition broke: tilt no longer moves the Medium construction — "
            "the no-double-bell guard below is measuring nothing")
        rows = _sub_table(self.block, "Versus", 2)
        self.assertNotEqual(
            rows, tilted,
            "the preview emitted a TILTED profile: the C# bell owns the tilt and "
            "would run on already-tilted data (the double bell)")

    def test_geometry_is_the_medium_base_the_csharp_scales(self):
        self.assertEqual(_field(self.block, "ValidTargets", 1), "Ground, Water")
        self.assertEqual(_field(self.block, "ReloadDelay", 1), "25")
        self.assertEqual(_field(self.block, "Range", 1), "5120")
        self.assertEqual(_field(self.block, "Spread", 2), "120")
        self.assertEqual(_field(self.block, "Damage", 2), "2000")
        self.assertEqual(_field(self.block, "Falloff", 2), "100, 0")
        # And the numbers must come from the shared physics shape, not be literals:
        physics = gen.shape_for(FAMILY)
        li = list(gen.LEVELS).index(gen.CONTINUOUS_PREVIEW_LEVEL)
        self.assertEqual(gen.at(physics[0], li), 120)
        self.assertEqual(gen.at(physics[1], li), "100, 0")

    def test_shared_profile_has_no_percentage_tables_and_ships_scale_2000(self):
        # THE SHARED PROFILE (Aedis 2026-09-10 03:17): the percentage half follows
        # the SAME belled table as the flat half (HeavinessMode SharedVersus), so
        # NO percentage table may be emitted (the C# rejects every
        # PercentageVersus* table in that mode) and the Scale dial is 2000 —
        # Damage 100 -> 0.01% max HP BEFORE the h/2 heaviness scaling and armor.
        self.assertEqual(_field(self.block, "HeavinessMode", 2), "SharedVersus")
        self.assertEqual(_field(self.block, "PercentageScale", 2), "2000")
        for key in ("PercentageVersus", "PercentageVersusLight",
                    "PercentageVersusHeavy"):
            self.assertIsNone(_field(self.block, key, 2),
                              f"{key} must be ABSENT in the shared profile")

    def test_plating_finalization_is_the_shared_column_source(self):
        rows = _sub_table(self.block, "Versus", 2)
        self.assertEqual(dict(rows), dict(self._expected_rows(tilted=False)))
        lead = [a for a, _v in rows[:len(gen.PLATING_CYCLE)]]
        self.assertEqual(lead, list(gen.PLATING_CYCLE),
                         "the five platings must sit pinned ahead of the ladder, "
                         "exactly as family() emits them")

    def test_shield_is_the_final_medium_value_shipped_in_the_same_stdout(self):
        rows = _sub_table(self.block, "Versus", 2)
        shield = dict(rows)["Shield"]
        self.assertEqual(shield, self.shield_medium)
        # Cross-check against the LEGACY block of the same opt-in stdout — reuse of the
        # phase-2 records must agree with what phase 2 actually shipped, per run.
        legacy = _blocks(self.optin_stdout)[f"^Warhead_{FAMILY}_Medium"]
        self.assertEqual(shield, _levelled_shield(legacy))

    def test_levelless_header_is_invisible_to_phase2(self):
        # If phase 2 ever matched `^Warhead_CannonAP:`, piping a preview back through
        # `apply` would treat it as a levelled template and re-write its Shield.
        import shield_uniqueness
        self.assertIsNone(shield_uniqueness.HEADER.match(f"^Warhead_{FAMILY}:"))
        self.assertIsNotNone(shield_uniqueness.HEADER.match(f"^Warhead_{FAMILY}_Medium:"))


if __name__ == "__main__":
    unittest.main()
