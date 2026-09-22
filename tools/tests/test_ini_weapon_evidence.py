"""Weapon-evidence extraction — the final contract, pinned.

REGRESSION (Aedis, 2026-09-09): DTA's X-O Power Suit carries Primary=XORail — a Tiberian Sun
railgun (`IsRailgun=yes`, `AmbientDamage=...`, `Damage` absent/zero) — plus
Secondary=XOMachineGun. `extract_ini_units` read the missing `Damage` as a proven zero and
promoted the machine gun into the primary slot (`w_dummy_primary: "XORail"`), so the corpus
held a 3.0-dps "machine gun" row for a railgun unit while the railgun's warhead, versus
profile and beam channel were gone.

THE FINAL CONTRACT, each clause pinned by a test:
  * NAMES are raw bytes, case-sensitive (opents code/ini.h:144): the profile keys
    (`AmbientDamage`, `IsRailgun`, `UseFireParticles`, `UseSparkParticles`,
    `AttachedParticleSystem`, warhead `Particle`) are read EXACT-case from the engine's own
    ini.Get_* calls; near-miss spellings are EXPOSED (`w_channel_ambiguity`), never folded;
  * a declared marker (railgun identity — even beside a positive `Damage` literal —
    non-zero `AmbientDamage`, fire/spark particles) keeps the verdict `incomplete`;
  * `w_evidence` is `nominal_direct` for the plain Damage/ROF contract — a NOMINAL DIRECT
    estimate, never worded "complete" — and `w_dps_usable` True vouches for that contract
    ONLY; the gate fails closed (absent/None) for every `incomplete` verdict;
  * `incomplete` reasons: `exotic_channels`, `missing_dependency` (dangling/absent warhead;
    the projectile is NOT checked — TS declares projectiles in art.ini too),
    `burst_unfolded` (Burst > 1, no cycle model), `effect_reference`
    (AttachedParticleSystem / warhead `Particle`), `direct_undeclared` (missing/zero
    `Damage` — the absence of known markers is NOT proof that all channels are supported);
  * NO AUTO-PROMOTION: the original primary keeps `w_*` and the raw secondary stays whole
    in `w2_*` even when the primary is missing, zero-damage, or unassessed. The ONLY
    promotion path is `EXPLICIT_DUMMY_WEAPONS` — an empty-by-default per-source profile of
    weapon names the source itself proves — and when it fires it emits the historical
    compatibility keys (`w_from_secondary`, `w_dummy_primary`, `wdummy_*`) unrenamed;
  * a missing Enhanced overlay FAILS CLOSED: no rows, one clear REFUSED note — the base
    file is never silently labelled as the overlay's identity.

⛔ EVERY FIXTURE HERE IS SMALL AND SYNTHETIC. The exact DTA INI archive was received by the
parent OUTSIDE this repo and is never read, downloaded or run here; the committed corpus
(`docs/reference/ini_corpus.json`) is NOT regenerated — legacy rows keep their old shape.
These tests pin the extractor's reproducible export/provenance contract; certifying complete
damage evidence or a release version stays with the parent and reviewer.
"""

from __future__ import annotations

import contextlib
import hashlib
import io
import json
import pathlib
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "reference"))
import extract_ini_units as ex   # noqa: E402


# Synthetic DTA-shaped rules: TS engine (`Modifier.*` warheads), `[Countries]` for ownership,
# one unit per slot arrangement the contract distinguishes. `[SparkRail]` carries BOTH the
# canonical channel keys and deliberate near-miss spellings (`israilgun=YES`,
# `ambientdamage=25`) — the canonical ones are evidence, the near-misses must surface as
# ambiguity and must NOT be folded into evidence.
SYNTHETIC_RULES = """\
[Countries]
0=GDI

[VehicleTypes]
0=XO
1=MTNK
2=GUNWALL
3=PWALL
4=CARRIER

[XO]
Name=X-O Power Suit
Primary=XORail
Secondary=XOMachineGun
Strength=7000
Cost=2000
Owner=GDI
Speed=6
Armor=heavy

[XORail]
ROF=60
Range=8
Projectile=InvisibleHigh
Warhead=XORailWH
IsRailgun=yes
AmbientDamage=80
AttachedParticleSystem=RailBeamSys

[XORailWH]
Particle=RailgunSpark
Modifier.Light=100
Modifier.Heavy=140
Modifier.Concrete=60

[XOMachineGun]
Damage=15
ROF=5
Range=6
Projectile=Invisible
Warhead=GC

[GC]
Modifier.None=1000

[MTNK]
Name=Medium Tank
Primary=90mmDummy
Secondary=120mmAP
Strength=4000
Cost=800
Owner=GDI

[90mmDummy]
Damage=0
Range=4
Projectile=Invisible
Warhead=DummyWH

[DummyWH]
Modifier.None=100

[120mmAP]
Damage=50
ROF=40
Range=6
Projectile=Invisible
Warhead=APWH

[APWH]
Modifier.Heavy=100

[GUNWALL]
Name=Rail Gunwall
Primary=GunTurret
Secondary=SparkRail
Strength=9000
Cost=3000
Owner=GDI

[GunTurret]
Damage=30
ROF=20
Range=7
Projectile=Invisible
Warhead=GunWH

[GunWH]
Modifier.Wood=120

[SparkRail]
ROF=70
Range=9
Projectile=RailSlug
Warhead=SparkWH
IsRailgun=yes
AmbientDamage=25
UseSparkParticles=1
israilgun=YES
ambientdamage=25

[RailSlug]
Speed=400

[SparkWH]
Modifier.Heavy=110

[PWALL]
Name=Spark Cannon Wall
Primary=SparkCannon
Secondary=GunTurret
Strength=5000
Cost=1500
Owner=GDI

[SparkCannon]
ROF=50
Range=6
Projectile=Invisible
Warhead=SparkCloudWH

[SparkCloudWH]
Particle=SparkCloud
Modifier.Light=80

[CARRIER]
Name=Unprimed Carrier
Secondary=GunTurret
Strength=3000
Cost=900
Owner=GDI
"""

OVERLAY_BASE = """\
[Countries]
0=GDI

[VehicleTypes]
0=BASE1

[BASE1]
Name=Base Unit
Primary=GunTurret
Strength=1000
Cost=100
Owner=GDI

[GunTurret]
Damage=30
ROF=20
Range=7
Warhead=GunWH

[GunWH]
Modifier.Wood=120
"""

OVERLAY_PATCH = """\
[BASE1]
Cost=150
"""


class ExtractEndToEndTests(unittest.TestCase):
    """One synthetic rules file, exercised through the real `extract()` path."""

    @classmethod
    def setUpClass(cls):
        cls._tmp = tempfile.TemporaryDirectory()
        tmp = pathlib.Path(cls._tmp.name)
        (tmp / "rules_synthetic.ini").write_text(SYNTHETIC_RULES, encoding="ascii")
        (tmp / "rules_base.ini").write_text(OVERLAY_BASE, encoding="ascii")
        (tmp / "rules_overlay.ini").write_text(OVERLAY_PATCH, encoding="ascii")
        with patch.object(ex, "REF", tmp):
            rows, notes = ex.extract("Synthetic DTA",
                                     {"file": "rules_synthetic.ini", "engine": "ts"})
        cls.notes = notes
        cls.rows = {r["id"]: r for r in rows}

    @classmethod
    def tearDownClass(cls):
        cls._tmp.cleanup()

    # ── the X-O railgun ──────────────────────────────────────────────────────────────────

    def test_rail_primary_keeps_its_identity_and_is_never_demoted(self):
        row = self.rows["XO"]
        self.assertEqual(row["weapon"], "XORail")
        self.assertNotIn("w_dummy_primary", row)
        self.assertNotIn("w_from_secondary", row)

    def test_rail_primary_declares_incomplete_evidence_instead_of_zero_damage(self):
        row = self.rows["XO"]
        self.assertEqual(row["w_evidence"], "incomplete")
        self.assertEqual(row["w_evidence_reason"], "exotic_channels")
        self.assertIsNone(row["w_damage"])
        self.assertIsNone(row["w_dps"])
        self.assertIsNone(row.get("w_dps_usable"))

    def test_raw_damage_channels_are_retained_verbatim(self):
        row = self.rows["XO"]
        self.assertEqual(row["w_ambient_damage"], 80)
        self.assertIs(row["w_railgun"], True)
        self.assertEqual(row["w_attached_particle_system"], "RailBeamSys")
        self.assertEqual(row["w_particle_system"], "RailgunSpark")
        self.assertEqual(row["w_warhead"], "XORailWH")
        self.assertEqual(row["w_versus"], {"light": 100, "heavy": 140, "concrete": 60})

    def test_secondary_carries_the_nominal_direct_contract_in_its_own_slot(self):
        row = self.rows["XO"]
        self.assertEqual(row["w2_weapon"], "XOMachineGun")
        self.assertEqual(row["w2_damage"], 15)
        self.assertEqual(row["w2_dps"], 3.0)
        self.assertEqual(row["w2_evidence"], "nominal_direct")
        self.assertIs(row["w2_dps_usable"], True)

    def test_secondary_dps_is_never_summed_into_the_primary(self):
        row = self.rows["XO"]
        self.assertIsNone(row["w_dps"])
        self.assertEqual(row["w2_dps"], 3.0)

    # ── no auto-promotion ────────────────────────────────────────────────────────────────

    def test_direct_zero_damage_primary_is_kept_secondary_never_authoritative(self):
        # 90mmDummy reads direct_undeclared; the original primary keeps its slot and the
        # raw secondary stays whole in w2_* — the secondary never becomes authoritative.
        row = self.rows["MTNK"]
        self.assertEqual(row["weapon"], "90mmDummy")
        self.assertEqual(row["w_evidence"], "incomplete")
        self.assertEqual(row["w_evidence_reason"], "direct_undeclared")
        self.assertEqual(row["w2_weapon"], "120mmAP")
        self.assertEqual(row["w2_damage"], 50)
        self.assertEqual(row["w2_evidence"], "nominal_direct")
        self.assertIs(row["w2_dps_usable"], True)
        self.assertNotIn("w_from_secondary", row)
        self.assertNotIn("w_dummy_primary", row)
        self.assertNotIn("wdummy_weapon", row)

    def test_missing_primary_is_kept_secondary_never_authoritative(self):
        row = self.rows["CARRIER"]
        self.assertIsNone(row.get("weapon"))
        self.assertEqual(row["w2_weapon"], "GunTurret")
        self.assertNotIn("w_from_secondary", row)
        self.assertNotIn("w_dummy_primary", row)

    def test_unassessed_effect_reference_primary_is_kept_too(self):
        # A warhead `Particle` is an effect the fold cannot model — incomplete, but still the
        # primary's own verdict, and still no promotion.
        row = self.rows["PWALL"]
        self.assertEqual(row["weapon"], "SparkCannon")
        self.assertEqual(row["w_evidence"], "incomplete")
        self.assertEqual(row["w_evidence_reason"], "effect_reference")
        self.assertEqual(row["w_particle_system"], "SparkCloud")
        self.assertEqual(row["w2_weapon"], "GunTurret")
        self.assertNotIn("w_from_secondary", row)

    def test_explicit_source_profile_is_the_only_promotion_path(self):
        # EXPLICIT_DUMMY_WEAPONS is empty by default; populated from a source's own proof it
        # fires the historical compatibility shape, old key names unrenamed.
        self.assertEqual(ex.EXPLICIT_DUMMY_WEAPONS, {})
        with patch.object(ex, "EXPLICIT_DUMMY_WEAPONS",
                          {"Synthetic DTA": {"90mmDummy"}}), \
             patch.object(ex, "REF", pathlib.Path(self._tmp.name)):
            rows, _ = ex.extract("Synthetic DTA",
                                 {"file": "rules_synthetic.ini", "engine": "ts"})
        row = {r["id"]: r for r in rows}["MTNK"]
        self.assertEqual(row["weapon"], "120mmAP")
        self.assertEqual(row["w_damage"], 50)
        self.assertIs(row["w_from_secondary"], True)
        self.assertEqual(row["w_dummy_primary"], "90mmDummy")
        self.assertEqual(row["wdummy_weapon"], "90mmDummy")
        self.assertEqual(row["wdummy_evidence"], "incomplete")
        self.assertEqual(row["wdummy_evidence_reason"], "direct_undeclared")
        self.assertEqual(row["w2_weapon"], "120mmAP")

    # ── the nominal-direct contract ──────────────────────────────────────────────────────

    def test_single_conventional_weapon_emits_the_nominal_direct_fields(self):
        row = self.rows["GUNWALL"]
        self.assertEqual(row["weapon"], "GunTurret")
        self.assertEqual(row["w_damage"], 30)
        self.assertEqual(row["w_dps"], 1.5)
        self.assertEqual(row["w_evidence"], "nominal_direct")
        self.assertIsNone(row["w_evidence_reason"])
        self.assertIs(row["w_dps_usable"], True)

    def test_exotic_secondary_keeps_evidence_and_gate_in_the_w2_slot(self):
        row = self.rows["GUNWALL"]
        self.assertEqual(row["w2_weapon"], "SparkRail")
        self.assertEqual(row["w2_railgun"], True)
        self.assertEqual(row["w2_spark_particles"], True)
        self.assertEqual(row["w2_ambient_damage"], 25)
        self.assertEqual(row["w2_evidence"], "incomplete")
        self.assertEqual(row["w2_evidence_reason"], "exotic_channels")
        self.assertIsNone(row.get("w2_dps_usable"))

    def test_near_miss_spellings_are_exposed_and_never_folded_into_evidence(self):
        row = self.rows["GUNWALL"]
        self.assertEqual(row["w2_channel_ambiguity"],
                         ["AmbientDamage<>ambientdamage", "IsRailgun<>israilgun"])
        self.assertEqual(row["w2_ambient_damage"], 25)
        self.assertIs(row["w2_railgun"], True)

    # ── the missing overlay fails closed ─────────────────────────────────────────────────

    def test_missing_overlay_returns_no_rows_with_a_refused_note(self):
        with patch.object(ex, "REF", pathlib.Path(self._tmp.name)):
            rows, notes = ex.extract("Synthetic DTA",
                                     {"file": "rules_base.ini", "engine": "ts",
                                      "overlay": "rules_missing_overlay.ini"})
        self.assertEqual(rows, [])
        self.assertTrue(any("REFUSED" in n and "rules_missing_overlay.ini" in n
                            for n in notes), notes)

    def test_present_overlay_is_applied_and_noted(self):
        with patch.object(ex, "REF", pathlib.Path(self._tmp.name)):
            rows, notes = ex.extract("Synthetic DTA",
                                     {"file": "rules_base.ini", "engine": "ts",
                                      "overlay": "rules_overlay.ini"})
        row = {r["id"]: r for r in rows}["BASE1"]
        self.assertEqual(row["cost"], 150)
        self.assertTrue(any("applied overlay rules_overlay.ini" in n for n in notes), notes)


class EvidenceVerdictTests(unittest.TestCase):
    """`weapon_of` verdict boundaries on direct dict fixtures (warhead sections included —
    a dangling warhead is itself a verdict)."""

    def test_railgun_flag_with_positive_damage_is_still_incomplete(self):
        rec = ex.weapon_of(
            {"RW": {"Damage": "100", "ROF": "50", "IsRailgun": "yes", "Warhead": "RWH"},
             "RWH": {}},
            "RW", "ts")
        self.assertEqual(rec["w_damage"], 100)
        self.assertEqual(rec["w_dps"], 2.0)
        self.assertEqual(rec["w_evidence"], "incomplete")
        self.assertEqual(rec["w_evidence_reason"], "exotic_channels")
        self.assertIsNone(rec.get("w_dps_usable"))

    def test_nonzero_ambient_beside_damage_is_a_marker(self):
        rec = ex.weapon_of(
            {"RW": {"Damage": "100", "ROF": "50", "AmbientDamage": "80", "Warhead": "RWH"},
             "RWH": {}},
            "RW", "ts")
        self.assertEqual(rec["w_evidence_reason"], "exotic_channels")
        self.assertIsNone(rec.get("w_dps_usable"))

    def test_explicit_zero_ambient_is_a_cancellation_not_a_marker(self):
        rec = ex.weapon_of(
            {"RW": {"Damage": "100", "ROF": "50", "AmbientDamage": "0", "Warhead": "RWH"},
             "RWH": {}},
            "RW", "ts")
        self.assertEqual(rec["w_ambient_damage"], 0)
        self.assertEqual(rec["w_evidence"], "nominal_direct")
        self.assertIs(rec["w_dps_usable"], True)

    def test_engine_bool_values_fold_exactly_as_Get_Bool_does(self):
        # opents code/ini.cpp:1390 decides on toupper(Value[0]): Y/T/1 true, N/F/0 false.
        for value, marker in (("TRUE", True), ("1", True), ("y", True),
                              ("no", False), ("0", False), ("", None)):
            rec = ex.weapon_of(
                {"RW": {"Damage": "100", "ROF": "50", "IsRailgun": value, "Warhead": "RWH"},
                 "RWH": {}},
                "RW", "ts")
            self.assertEqual(rec["w_evidence_reason"],
                             "exotic_channels" if marker else None, value)

    def test_missing_damage_without_markers_is_direct_undeclared(self):
        rec = ex.weapon_of({"DUM": {"ROF": "20", "Range": "4", "Warhead": "WH"}, "WH": {}},
                           "DUM", "ts")
        self.assertIsNone(rec["w_damage"])
        self.assertIsNone(rec["w_dps"])
        self.assertEqual(rec["w_evidence"], "incomplete")
        self.assertEqual(rec["w_evidence_reason"], "direct_undeclared")
        self.assertIsNone(rec.get("w_dps_usable"))

    def test_single_conventional_weapon_is_nominal_direct_not_complete(self):
        rec = ex.weapon_of({"GUN": {"Damage": "100", "ROF": "50", "Warhead": "WH"}, "WH": {}},
                           "GUN", "ts")
        self.assertEqual(rec["w_evidence"], "nominal_direct")
        self.assertIsNone(rec["w_evidence_reason"])
        self.assertIs(rec["w_dps_usable"], True)

    def test_burst_2_is_withheld_from_the_usable_gate(self):
        rec = ex.weapon_of(
            {"RW": {"Damage": "100", "ROF": "50", "Burst": "2", "Warhead": "RWH"},
             "RWH": {}},
            "RW", "ts")
        self.assertEqual(rec["w_burst"], 2)
        self.assertEqual(rec["w_dps"], 2.0)
        self.assertEqual(rec["w_evidence"], "incomplete")
        self.assertEqual(rec["w_evidence_reason"], "burst_unfolded")
        self.assertIsNone(rec.get("w_dps_usable"))

    def test_dangling_warhead_is_a_missing_dependency(self):
        rec = ex.weapon_of(
            {"RW": {"Damage": "100", "ROF": "50", "Warhead": "NOWHERE"}}, "RW", "ts")
        self.assertEqual(rec["w_evidence_reason"], "missing_dependency")
        self.assertIsNone(rec.get("w_dps_usable"))

    def test_absent_warhead_key_is_a_missing_dependency(self):
        rec = ex.weapon_of({"RW": {"Damage": "100", "ROF": "50"}}, "RW", "ts")
        self.assertEqual(rec["w_evidence_reason"], "missing_dependency")

    def test_warhead_particle_reference_is_an_unmodelled_effect(self):
        rec = ex.weapon_of(
            {"RW": {"Damage": "100", "ROF": "50", "Warhead": "WH"},
             "WH": {"Particle": "SparkCloud"}},
            "RW", "ts")
        self.assertEqual(rec["w_particle_system"], "SparkCloud")
        self.assertEqual(rec["w_evidence_reason"], "effect_reference")
        self.assertIsNone(rec.get("w_dps_usable"))

    def test_attached_particle_system_reference_is_an_unmodelled_effect(self):
        rec = ex.weapon_of(
            {"RW": {"Damage": "100", "ROF": "50", "AttachedParticleSystem": "FireStream",
                    "Warhead": "RWH"}, "RWH": {}},
            "RW", "ts")
        self.assertEqual(rec["w_attached_particle_system"], "FireStream")
        self.assertEqual(rec["w_evidence_reason"], "effect_reference")

    def test_fire_particles_marker(self):
        rec = ex.weapon_of(
            {"RW": {"Damage": "100", "ROF": "50", "UseFireParticles": "yes",
                    "Warhead": "RWH"}, "RWH": {}},
            "RW", "ts")
        self.assertEqual(rec["w_evidence_reason"], "exotic_channels")

    def test_near_miss_spellings_are_exposed_not_evidence(self):
        # Raw-byte lookup (opents code/ini.h:144): the engine never reads these keys, so they
        # are neither channels nor gate-closers — they are surfaced for review.
        rec = ex.weapon_of(
            {"RW": {"Damage": "50", "ROF": "10", "ambientDamage": "80", "Warhead": "RWH"},
             "RWH": {"particle": "X"}},
            "RW", "ts")
        self.assertNotIn("w_ambient_damage", rec)
        self.assertNotIn("w_particle_system", rec)
        self.assertEqual(rec["w_channel_ambiguity"],
                         ["AmbientDamage<>ambientDamage", "Particle<>particle"])
        self.assertEqual(rec["w_evidence"], "nominal_direct")
        self.assertIs(rec["w_dps_usable"], True)

    def test_unparsable_ambient_round_trips_raw_and_is_not_a_marker(self):
        # The engine's Get_Int would read its default (0); the raw text is kept for review.
        rec = ex.weapon_of(
            {"RW": {"Damage": "100", "ROF": "50", "AmbientDamage": "80x", "Warhead": "RWH"},
             "RWH": {}},
            "RW", "ts")
        self.assertEqual(rec["w_ambient_damage"], "80x")
        self.assertEqual(rec["w_evidence"], "nominal_direct")
        self.assertIs(rec["w_dps_usable"], True)

    def test_missing_weapon_section_has_no_evidence_claims(self):
        rec = ex.weapon_of({}, "NOWHERE", "ts")
        self.assertEqual(rec, {"weapon": "NOWHERE"})


class SingleSourceCliTests(unittest.TestCase):
    """The single-source CLI (--rules / --overlay / --engine / --label): reproducible,
    source-identified export with provenance. Synthetic fixtures only — the received DTA
    archive is parent-owned outside the repo and is never read, downloaded or run here."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        tmp = pathlib.Path(self._tmp.name)
        # sources live in their own directory, so `export/` is a legal outside-repo,
        # outside-source output location — exactly the layout the CLI is meant to serve.
        src = tmp / "source"
        src.mkdir()
        (src / "Rules.ini").write_text(SYNTHETIC_RULES, encoding="ascii")
        (src / "Enhance.ini").write_text("[XO]\nCost=2500\n", encoding="ascii")
        (tmp / "export").mkdir()
        self.tmp = tmp
        self.rules = src / "Rules.ini"
        self.rules_sha = hashlib.sha256(self.rules.read_bytes()).hexdigest()
        self.overlay_sha = hashlib.sha256((src / "Enhance.ini").read_bytes()).hexdigest()

    def tearDown(self):
        self._tmp.cleanup()

    def run_cli(self, *argv):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = ex.main(list(argv))
        return code, out.getvalue(), err.getvalue()

    def test_vinifera_inherits_resolves_parent_before_overlay(self):
        base = {
            "ARTY": {"Damage": "25", "Armor": "heavy"},
            "RAARTY": {"$Inherits": "ARTY", "Damage": "30"},
        }
        overlay = {"ARTY": {"$Inherits": "RAARTY", "Damage": "40"}}
        resolved_base = ex.resolve_inherits(base)
        resolved_overlay = ex.resolve_inherits(overlay)
        merged = ex.merge_overlay(resolved_base, resolved_overlay)
        self.assertEqual(resolved_base["RAARTY"], {"Damage": "30", "Armor": "heavy"})
        self.assertEqual(resolved_overlay["ARTY"], {"Damage": "40"})
        self.assertEqual(merged["ARTY"], {"Damage": "40", "Armor": "heavy"})

    def test_vinifera_inherits_cycle_is_refused(self):
        cyclic = {
            "A": {"$Inherits": "B", "Value": "a"},
            "B": {"$Inherits": "A", "Value": "b"},
        }
        with self.assertRaisesRegex(ValueError, r"cyclic \$Inherits chain: A -> B -> A"):
            ex.resolve_inherits(cyclic)

    def test_named_partial_export_refuses_to_delete_other_sources(self):
        target = self.tmp / "export" / "corpus.jsonl"
        target.write_text(
            json.dumps({"source": "DTA Classic", "id": "old"}) + "\n"
            + json.dumps({"source": "Other Source", "id": "keep"}) + "\n",
            encoding="utf-8",
        )
        named = self.tmp / "named"
        named.mkdir()
        (named / "rules_DTA_Classic.ini").write_text(SYNTHETIC_RULES, encoding="ascii")
        with patch.object(ex, "REF", named):
            code, _, err = self.run_cli("--source", "DTA Classic", "--json", str(target))
        self.assertEqual(code, 1)
        self.assertIn("--force-partial", err)
        self.assertIn("Other Source", target.read_text(encoding="utf-8"))

    def test_named_partial_export_refuses_unreadable_existing_jsonl(self):
        named = self.tmp / "named-unreadable"
        named.mkdir()
        (named / "rules_DTA_Classic.ini").write_text(SYNTHETIC_RULES, encoding="ascii")
        for existing in ("{not json}\n", "[]\n"):
            target = self.tmp / ("export-" + str(len(existing)) + ".jsonl")
            target.write_text(existing, encoding="utf-8")
            with patch.object(ex, "REF", named):
                code, _, err = self.run_cli("--source", "DTA Classic", "--json", str(target))
            self.assertEqual(code, 1)
            self.assertIn("use --force-partial", err)
            self.assertEqual(target.read_text(encoding="utf-8"), existing)

    # ── argument contract ────────────────────────────────────────────────────────────────

    def test_engine_is_required_with_rules(self):
        code, _, err = self.run_cli("--rules", str(self.rules))
        self.assertEqual(code, 1)
        self.assertIn("--engine", err)

    def test_explicit_nonblank_label_is_required_with_rules(self):
        # two source variants must never silently share one label
        code, _, err = self.run_cli("--rules", str(self.rules), "--engine", "ts")
        self.assertEqual(code, 1)
        self.assertIn("--label", err)
        code, _, err = self.run_cli("--rules", str(self.rules), "--engine", "ts",
                                    "--label", "   ")
        self.assertEqual(code, 1)
        self.assertIn("--label", err)

    def test_engine_without_rules_is_rejected_not_ignored(self):
        code, _, err = self.run_cli("--engine", "ts")
        self.assertEqual(code, 1)
        self.assertIn("--rules", err)
        code, _, err = self.run_cli("--source", "Mental Omega", "--engine", "ts")
        self.assertEqual(code, 1)
        self.assertIn("--rules", err)

    def test_source_and_list_are_conflicting_in_named_mode(self):
        code, _, err = self.run_cli("--source", "Mental Omega", "--list")
        self.assertEqual(code, 1)
        self.assertIn("conflicting", err)

    def test_rules_rejects_source_and_list_combination(self):
        self.assertEqual(self.run_cli("--rules", str(self.rules),
                                      "--source", "Mental Omega")[0], 1)
        self.assertEqual(self.run_cli("--rules", str(self.rules), "--list")[0], 1)

    def test_overlay_and_label_require_rules(self):
        self.assertEqual(self.run_cli("--overlay", "x.ini")[0], 1)
        self.assertEqual(self.run_cli("--label", "y")[0], 1)

    def test_named_list_mode_still_works(self):
        self.assertEqual(self.run_cli("--list")[0], 0)

    # ── fail-closed behavior ─────────────────────────────────────────────────────────────

    def test_missing_overlay_refused(self):
        code, _, err = self.run_cli("--rules", str(self.rules), "--engine", "ts",
                                    "--label", "DTA",
                                    "--overlay", str(self.tmp / "nope.ini"))
        self.assertEqual(code, 1)
        self.assertIn("REFUSED", err)
        self.assertIn("nope.ini", err)

    def test_input_changed_during_extraction_fails(self):
        original = ex.read_ini

        def mutating_read_ini(path):
            result = original(path)
            if pathlib.Path(path).name == "Rules.ini":
                self.rules.write_text(SYNTHETIC_RULES + "\n[EXTRA]\n0=1\n", encoding="ascii")
            return result

        target = self.tmp / "export" / "changed.jsonl"
        with patch.object(ex, "read_ini", mutating_read_ini):
            code, _, err = self.run_cli("--rules", str(self.rules), "--engine", "ts",
                                        "--label", "DTA", "--json", str(target))
        self.assertEqual(code, 1)
        self.assertIn("changed during extraction", err)
        self.assertFalse(target.exists())

    def test_output_refused_inside_a_git_repo(self):
        (self.tmp / "repo").mkdir()
        (self.tmp / "repo" / ".git").write_text("gitdir: elsewhere\n", encoding="ascii")
        code, _, err = self.run_cli("--rules", str(self.rules), "--engine", "ts",
                                    "--label", "DTA",
                                    "--json", str(self.tmp / "repo" / "out.jsonl"))
        self.assertEqual(code, 1)
        self.assertIn("git repo", err)
        self.assertFalse((self.tmp / "repo" / "out.jsonl").exists())

    def test_output_refused_inside_source_directory(self):
        code, _, err = self.run_cli("--rules", str(self.rules), "--engine", "ts",
                                    "--label", "DTA",
                                    "--json", str(self.tmp / "source" / "out.jsonl"))
        self.assertEqual(code, 1)
        self.assertIn("source directory", err)
        # ...and so is a subdirectory OF the source directory.
        code, _, _ = self.run_cli("--rules", str(self.rules), "--engine", "ts",
                                  "--label", "DTA",
                                  "--json", str(self.tmp / "source" / "nested" / "out.jsonl"))
        self.assertEqual(code, 1)

    def test_output_never_overwrites(self):
        target = self.tmp / "export" / "existing.jsonl"
        target.write_text("keep", encoding="ascii")
        code, _, err = self.run_cli("--rules", str(self.rules), "--engine", "ts",
                                    "--label", "DTA", "--json", str(target))
        self.assertEqual(code, 1)
        self.assertIn("never overwrites", err)
        self.assertEqual(target.read_text(encoding="ascii"), "keep")

    def test_nonfinite_row_never_leaves_a_partial_artifact(self):
        # allow_nan=False: serialization must fail BEFORE the output file exists.
        original_core = ex.extract_rows_from_ini

        def poisoned_core(ini, label, engine):
            rows = original_core(ini, label, engine)
            rows[0]["hp"] = float("nan")
            return rows

        target = self.tmp / "export" / "nan.jsonl"
        with patch.object(ex, "extract_rows_from_ini", poisoned_core):
            code, _, err = self.run_cli("--rules", str(self.rules), "--engine", "ts",
                                        "--label", "DTA", "--json", str(target))
        self.assertEqual(code, 1)
        self.assertIn("serialization failed", err)
        self.assertFalse(target.exists())

    def test_output_safety_runs_on_resolved_paths(self):
        # `export/../source/out.jsonl` literally names the allowed `export` dir but RESOLVES
        # into the source directory — the check must refuse the resolved location, not the
        # raw string (the same resolution that de-fangs junctions).
        code, _, err = self.run_cli(
            "--rules", str(self.rules), "--engine", "ts", "--label", "DTA",
            "--json", str(self.tmp / "export" / ".." / "source" / "out.jsonl"))
        self.assertEqual(code, 1)
        self.assertIn("source directory", err)
        # And the inverse traversal resolves OUT of the source directory and is allowed.
        (self.tmp / "source" / "alias").mkdir()
        ok = self.tmp / "source" / "alias" / ".." / ".." / "export" / "resolved.jsonl"
        code, out, _ = self.run_cli("--rules", str(self.rules), "--engine", "ts",
                                    "--label", "DTA", "--json", str(ok))
        self.assertEqual(code, 0)
        self.assertTrue((self.tmp / "export" / "resolved.jsonl").exists())

    # ── provenance ───────────────────────────────────────────────────────────────────────

    def test_source_identity_and_provenance_per_row(self):
        target = self.tmp / "export" / "prov.jsonl"
        code, out, _ = self.run_cli("--rules", str(self.rules), "--engine", "ts",
                                    "--label", "DTA",
                                    "--overlay", str(self.tmp / "source" / "Enhance.ini"),
                                    "--json", str(target))
        self.assertEqual(code, 0)
        text = target.read_text(encoding="utf-8")
        rows = [json.loads(line) for line in text.splitlines() if line.strip()]
        self.assertTrue(rows)
        xo = next(r for r in rows if r["id"] == "XO")
        self.assertEqual(xo["source"], "DTA")              # explicit, never a stem default
        self.assertEqual(xo["source_label"], "DTA")
        self.assertEqual(xo["source_sha256"], self.rules_sha)
        self.assertEqual(xo["overlay_sha256"], self.overlay_sha)
        self.assertEqual(xo["overlay_precedence"], "overlay_over_rules")
        self.assertEqual(xo["engine"], "ts")               # SELECTED engine, own field
        self.assertEqual(xo["engine_profile"], "opents_weapon_channels_v1")
        # ⛔ user-declared --engine ts is NOT proof the exact game engine implements OpenTS
        self.assertEqual(xo["engine_profile_applicability"], "unverified")
        self.assertEqual(xo["profile_selection"], "user_declared")
        self.assertEqual(xo["source_runtime_version_status"], "unverified")
        self.assertEqual(xo["extractor_python_version"], sys.version.split()[0])
        self.assertNotIn("runtime_version_unverified", xo)
        self.assertEqual(xo["cost"], 2500)                 # overlay won over the base
        # no raw source embedding: sections and raw assignments must not appear
        self.assertNotIn("[Countries]", text)
        self.assertNotIn("Primary=", text)
        self.assertNotIn("[XORail]", text)

    def test_ra2_selects_its_engine_and_marks_the_profile_unverified(self):
        target = self.tmp / "export" / "ra2.jsonl"
        code, _, _ = self.run_cli("--rules", str(self.rules), "--engine", "ra2",
                                  "--label", "DTA_ra2", "--json", str(target))
        self.assertEqual(code, 0)
        rows = [json.loads(line) for line in
                target.read_text(encoding="utf-8").splitlines() if line.strip()]
        xo = next(r for r in rows if r["id"] == "XO")
        self.assertEqual(xo["engine"], "ra2")              # selected engine, recorded as-is
        self.assertEqual(xo["engine_profile"], "opents_weapon_channels_v1")
        self.assertEqual(xo["engine_profile_applicability"], "unverified")
        self.assertEqual(xo["profile_selection"], "user_declared")

    def test_output_makes_no_executable_fidelity_claim(self):
        # THE provenance blocker, pinned: for BOTH engines every exported row must carry
        # unverified applicability, unverified source-runtime status, and must not contain
        # any "verified"/"fidelity" claim a reader could mistake for engine proof.
        targets = []
        for engine, name in (("ts", "fidelity_ts.jsonl"), ("ra2", "fidelity_ra2.jsonl")):
            target = self.tmp / "export" / name
            code, _, _ = self.run_cli("--rules", str(self.rules), "--engine", engine,
                                      "--label", "DTA", "--json", str(target))
            self.assertEqual(code, 0)
            targets.append(target)
        for target in targets:
            rows = [json.loads(line) for line in
                    target.read_text(encoding="utf-8").splitlines() if line.strip()]
            self.assertTrue(rows)
            for row in rows:
                self.assertEqual(row["engine_profile_applicability"], "unverified")
                self.assertEqual(row["source_runtime_version_status"], "unverified")
                for k, v in row.items():
                    self.assertNotIn("fidelity", k.lower())
                    if isinstance(v, str):
                        self.assertNotIn("fidelity", v.lower())
                        self.assertNotEqual(v, "verified")

    def test_label_and_rules_only_provenance(self):
        target = self.tmp / "export" / "plain.jsonl"
        code, _, _ = self.run_cli("--rules", str(self.rules), "--engine", "ts",
                                  "--label", "DTA_Classic", "--json", str(target))
        self.assertEqual(code, 0)
        rows = [json.loads(line) for line in
                target.read_text(encoding="utf-8").splitlines() if line.strip()]
        for row in rows:
            self.assertEqual(row["source"], "DTA_Classic")
            self.assertEqual(row["source_label"], "DTA_Classic")
            self.assertEqual(row["overlay_precedence"], "none")
            self.assertNotIn("overlay_sha256", row)
            self.assertEqual(row["engine_profile_applicability"], "unverified")
        self.assertEqual(next(r for r in rows if r["id"] == "XO")["cost"], 2000)


if __name__ == "__main__":
    unittest.main()
