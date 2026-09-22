"""The consumers of `ini_corpus.json` honour the extractor's weapon evidence — no
`ini_rows`/`peer_hero_rows` row may turn an INCOMPLETE estimate into an authoritative target.

CONSUMER SIDE of the extractor contract pinned by the same module: `extract_ini_units` never
certifies a fold COMPLETE — `w_evidence` is either the EXACT verdict `nominal_direct` (the
declared CONTRACT that `w_dps` is the plain direct Damage/ROF estimate, vouched by
`w_dps_usable: True`) or `incomplete` with a reason — and keeps the raw channels + slot twins
(`w2_*` secondary, `wdummy_*` demoted primary) diagnostic-only. `reference_distribution`.
`ini_rows` and `peer_hero_rows` used to copy `w_dps` and the armor-adjusted `dps_vs_*` while
DROPPING `w_evidence` — so a weapon whose damage travels channels the direct fold cannot read
arrived downstream as an authoritative DPS target with the caveat deleted.

Contract pinned here:
  * explicit `incomplete`/`unverified` evidence WITHHOLDS `w_dps` and every `dps_vs_*`
    consumer value; the raw direct estimate is kept separately on `w_dps_raw`, where it votes
    on nothing (no distribution, no target projection);
  * hp/speed/cost — and the other weapon fields the matching clause-5 armed test reads —
    survive untouched, so the row still votes on the chassis while abstaining on weapons;
  * rows with NO extractor verdict (the committed corpus predates the field) are labelled
    `legacy-unassessed` and retain their numeric behaviour verbatim — ABSENT STATUS IS
    LEGACY, never certified complete;
  * the extractor's FINAL conventional verdict `nominal_direct` (underscore, EXACT
    STRING — a near-miss like `nominal-direct` is withheld, never silently normalised)
    retains existing behaviour;
  * an explicit `w_dps_usable: False` withholds whatever the label says;
  * a SECONDARY or DEMOTED-PRIMARY status (`w2_*`/`wdummy_*`) can never gate the PRIMARY's
    numbers — the promoted machine gun of DTA's X-O Power Suit keeps its own slot verdict,
    while the slots' relation to each other stays unresolved (Primary/Secondary is
    TARGET-SELECTED) and no unit-level fold is called complete here;
  * an incomplete row — ordinary OR build-limited hero — contributes to NO `build_distributions`
    weapon aggregate, while the hero lane never re-enters the ordinary population;
  * `evidence_counts` reports the honest mix over in-memory rows without a corpus re-read.

⛔ ALL FIXTURES ARE SMALL AND SYNTHETIC. The committed corpus
(`docs/reference/ini_corpus.json`) is NOT read at all — a temp file patches
`rd.INI_CORPUS`/`rd.INI_ARMOR` — and no raw corpus is regenerated here.
"""

from __future__ import annotations

import json
import pathlib
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "balance"))
sys.path.insert(0, str(ROOT / "tools" / "reference"))
sys.path.insert(0, str(ROOT / "tools" / "audit"))
import extract_ini_units as ex     # noqa: E402
import reference_distribution as rd   # noqa: E402
import reference_targets as rt       # noqa: E402


def _write_jsonl(tmp: pathlib.Path, name: str, rows: list[dict]) -> pathlib.Path:
    p = tmp / name
    p.write_text("\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")
    return p


ARMOR_ROW = {"source": "SynthIni", "id": None,   # id patched per test
             "ladders": {"VEH": {"confidence": "high", "values": {"light": 100}}}}

NORMAL_ROW = {
    "source": "SynthIni", "engine": "ra2", "id": "SYNTANK", "name": "Synth Tank",
    "type": "vehicle", "faction": "GDI", "owners": ["GDI"], "hp": 400,
    "cost": 800, "speed": 7, "turn_speed": 5, "turreted": False,
    "buildable": True, "naval": False,
    "weapon": "SynthGun", "w_damage": 20, "w_reload": 10, "w_range": 5,
    "w_burst": 2, "w_dps": 2.0,
}


class PatchedCorpus:
    """A temp-file `ini_corpus.json`/armor index — the committed corpus is never touched."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)

    def _install(self, corpus_rows, armor_ids):
        tmp = pathlib.Path(self.tmp.name)
        armor = [dict(ARMOR_ROW, id=i) for i in armor_ids]
        corp = _write_jsonl(tmp, "ini_corpus.json", corpus_rows)
        arm = _write_jsonl(tmp, "armor.json", armor)
        stack = patch.multiple(rd, INI_CORPUS=corp, INI_ARMOR=arm)
        stack.start()
        self.addCleanup(stack.stop)
        return corp


class LoaderEvidenceTest(PatchedCorpus, unittest.TestCase):

    def test_explicit_incomplete_withholds_w_dps_and_every_dps_vs(self):
        self._install([dict(NORMAL_ROW, w_evidence="incomplete")], ["SYNTANK"])
        out = {r["id"]: r for r in rd.ini_rows()}
        row = out["SYNTANK"]
        self.assertIsNone(row["w_dps"])
        self.assertEqual(row["w_dps_raw"], 2.0)          # raw direct estimate, kept apart
        self.assertEqual(row["w_evidence"], "incomplete")
        for lad in rd.LADDERS:
            self.assertIsNone(row[f"dps_vs_{lad}"])     # withheld even though a frac exists
        # chassis passes through intact; NO w_dps vote, hp/cost survive
        self.assertEqual(row["hp"], 400)
        self.assertEqual(row["cost"], 800)
        self.assertEqual(row["speed"], 7)
        self.assertEqual(row["w_damage"], 20)           # clause-5 armed test still sees it
        self.assertNotIn("w2_evidence", row)

    def test_both_loaders_share_one_policy_for_heroes(self):
        hero = dict(NORMAL_ROW, id="SYNHERO", name="Synth OneOff", build_limit=1,
                    w_evidence="incomplete")
        self._install([hero], ["SYNHERO"])
        hero_rows = {r["id"]: r for r in rd.peer_hero_rows()}
        ordinary = rd.ini_rows()
        self.assertNotIn("SYNHERO", {r["id"] for r in ordinary})   # population rule intact
        hrow = hero_rows["SYNHERO"]
        self.assertTrue(hrow["hero"])
        self.assertIsNone(hrow["w_dps"])
        self.assertEqual(hrow["w_dps_raw"], 2.0)
        for lad in rd.LADDERS:
            self.assertIsNone(hrow[f"dps_vs_{lad}"])
        self.assertEqual(hrow["hp"], 400)
        self.assertEqual(hrow["cost"], 800)

    def test_missing_legacy_evidence_retains_numeric_and_is_labelled(self):
        self._install([dict(NORMAL_ROW)], ["SYNTANK"])   # no w_evidence at all
        out = {r["id"]: r for r in rd.ini_rows()}
        row = out["SYNTANK"]
        self.assertEqual(row["w_evidence"], rd.LEGACY_EVIDENCE)
        self.assertEqual(row["w_dps"], 2.0)             # compatibility numeric behaviour
        self.assertNotIn("w_dps_raw", row)
        self.assertEqual(row["dps_vs_VEH"], 2.0)        # 2.0 x frac 1.0
        for lad in ("INF", "AIR", "BLD"):
            self.assertIsNone(row[f"dps_vs_{lad}"])

    def test_supported_status_retains_existing_behaviour(self):
        # The extractor's FINAL conventional verdict is `nominal_direct` (ONE token, an
        # underscore): the DECLARED contract that w_dps is the plain direct Damage/ROF
        # estimate — never a proven total, never a "complete" claim. `w_dps_usable: True`
        # vouches for exactly that contract.
        for verdict in ("supported", "conventional", "nominal_direct"):
            rows = self._install([dict(NORMAL_ROW, w_evidence=verdict)], ["SYNTANK"])
            out = {r["id"]: r for r in rd.ini_rows()}
            row = out["SYNTANK"]
            self.assertEqual(row["w_evidence"], verdict)
            self.assertEqual(row["w_dps"], 2.0)
            self.assertEqual(row["dps_vs_VEH"], 2.0)
            self.assertNotIn("w_dps_raw", row)

    def test_unknown_explicit_status_is_refused_not_trusted(self):
        self._install([dict(NORMAL_ROW, w_evidence="unverified")], ["SYNTANK"])
        out = {r["id"]: r for r in rd.ini_rows()}
        row = out["SYNTANK"]
        self.assertIsNone(row["w_dps"])
        self.assertEqual(row["w_dps_raw"], 2.0)
        self.assertEqual(row["w_evidence"], "unverified")

    def test_near_miss_verdict_is_never_normalised(self):
        for wev in ("nominal-direct", "NOMINAL_DIRECT", "nominal ", "directed_nominal"):
            rec = dict(NORMAL_ROW, w_evidence=wev)
            row = dict(NORMAL_ROW)
            dps = rd.apply_weapon_evidence(row, rec)
            self.assertIsNone(dps, wev)
            self.assertIsNone(row["w_dps"])
            self.assertEqual(row["w_dps_raw"], 2.0)
            self.assertEqual(row["w_evidence"], wev)   # exact, UNNORMALISED, self-labelled

    def test_explicit_dps_usable_false_withholds_whatever_the_label_says(self):
        for wev in (None, "supported"):
            rec = dict(NORMAL_ROW, w_dps_usable=False, w_evidence=wev)
            self._install([rec], [])
            out = {r["id"]: r for r in rd.ini_rows()}
            row = out["SYNTANK"]
            self.assertIsNone(row["w_dps"])
            self.assertEqual(row["w_dps_raw"], 2.0)
            self.assertEqual(row["w_dps_usable"], False)
            self.assertIn("dps_unusable", row["w_evidence_reason"])
        # an explicit True keeps the numeric behaviour (the extractor's fail-closed gate
        # read OPEN only here)
        self._install([dict(NORMAL_ROW, w_dps_usable=True)], ["SYNTANK"])
        row = {r["id"]: r for r in rd.ini_rows()}["SYNTANK"]
        self.assertEqual(row["w_dps"], 2.0)

    def test_evolved_extractor_fields_are_carried_through(self):
        rec = dict(NORMAL_ROW, w_evidence="incomplete", w_evidence_reason="exotic_channels",
                   w_dps_usable=False, w_channel_ambiguity=["AmbientDamage<>ambientdamage"],
                   w_attached_particle_system="RailgunSpark", w_fire_particles=True,
                   w_spark_particles=True, w_ambient_damage=80,
                   w_fully_unknown_future_field=1,
                   w_demoted_primary="XORail", w_from_secondary=True,
                   w2_weapon="MachineGun", w2_evidence="incomplete",
                   w2_evidence_reason="exotic_channels", w2_dps_usable=False,
                   w2_channel_ambiguity=["AmbientDamage<>ambientdamage"], w2_fire_particles=True,
                   w_dummy_primary="XORail")
        self._install([rec], [])
        row = {r["id"]: r for r in rd.ini_rows()}["SYNTANK"]
        for key in ("w_evidence", "w_evidence_reason", "w_dps_usable",
                    "w_channel_ambiguity", "w_attached_particle_system",
                    "w_fire_particles", "w_spark_particles", "w_ambient_damage",
                    "w_demoted_primary", "w_from_secondary", "w_dummy_primary",
                    "w2_weapon", "w2_evidence", "w2_evidence_reason", "w2_dps_usable",
                    "w2_channel_ambiguity", "w2_fire_particles"):
            self.assertIn(key, row, key)
        self.assertEqual(row["w_evidence_reason"], "exotic_channels")
        self.assertEqual(row["w2_evidence_reason"], "exotic_channels")
        self.assertNotIn("w_fully_unknown_future_field", row)

    def test_slot_status_cannot_gate_the_primary(self):
        rec = dict(NORMAL_ROW, w2_evidence="incomplete", w2_weapon="GunAA",
                   wdummy_evidence="incomplete", wdummy_weapon="RailDummy",
                   w_dummy_primary="90mmDummy", w_from_secondary=True)
        row = dict(rec)
        dps = rd.apply_weapon_evidence(row, rec)
        self.assertEqual(dps, 2.0)
        self.assertEqual(row["w_dps"], 2.0)
        self.assertNotIn("w_dps_raw", row)
        self.assertEqual(row["w_evidence"], rd.LEGACY_EVIDENCE)
        # and the diagnostics survive the trip through the loader
        self._install([rec], [])
        out = {r["id"]: r for r in rd.ini_rows()}
        row = out["SYNTANK"]
        self.assertEqual(row["wdummy_evidence"], "incomplete")
        self.assertEqual(row["w2_evidence"], "incomplete")
        self.assertEqual(row["w_dummy_primary"], "90mmDummy")

    def test_diagnostics_for_incomplete_primary_are_carried(self):
        rec = dict(NORMAL_ROW, w_dps=None, w_damage=None, w_evidence="incomplete",
                   w_ambient_damage=80, w_railgun=True, w_railgun_projectile=True,
                   w_particle_system="RailgunSpark")
        row = dict(rec)
        self.assertIsNone(rd.apply_weapon_evidence(row, rec))
        self.assertEqual(row["w_ambient_damage"], 80)
        self.assertTrue(row["w_railgun"])
        self.assertEqual(row["w_particle_system"], "RailgunSpark")
        self.assertEqual(row["w_evidence"], "incomplete")


class DistributionInfluenceTest(PatchedCorpus, unittest.TestCase):
    """A withheld positive-DPS estimate votes on NOTHING; hp/cost voting survives."""

    PEERS = [
        # peers in the LOADER-OUTPUT shape: enough points to define a w_dps aggregate
        dict(NORMAL_ROW, id="PEERA", name="Peer A", hp=300, cost=600, w_dps=1.0),
        dict(NORMAL_ROW, id="PEERB", name="Peer B", hp=500, cost=900, w_dps=3.0),
        dict(NORMAL_ROW, id="PEERC", name="Peer C", hp=450, cost=700, w_dps=5.0),
        # the incomplete row exactly as `apply_weapon_evidence` emits it
        dict(NORMAL_ROW, id="SYNTANK", name="Synth Tank", hp=400, cost=800,
             w_evidence="incomplete", w_dps=None, w_dps_raw=2.0),
    ]

    def _filtered(self):
        return [r for r in self.PEERS if r["id"] != "SYNTANK"]

    def test_withheld_row_votes_nowhere_on_weapon_layer_yet_on_hp(self):
        with_all = rd.build_distributions(self.PEERS)["SynthIni"]
        without = rd.build_distributions(self._filtered())["SynthIni"]
        for stat in ("w_dps",) + rd.ARMOR_STATS:
            self.assertEqual(with_all["vehicle"].get(stat), without["vehicle"].get(stat),
                             f"{stat} changed by an incomplete row")
            self.assertEqual(with_all["overall"].get(stat), without["overall"].get(stat))
        for stat in ("hp", "speed"):
            self.assertIn(stat, with_all["vehicle"])
        self.assertIsNotNone(rd.eligible({**NORMAL_ROW, "w_dps": 2.0}, "w_dps"))
        self.assertNotIn("w_dps_raw", NORMAL_ROW)

    def test_withheld_row_is_ineligible_while_chassis_stays_eligible(self):
        withheld = {**NORMAL_ROW, "w_dps": None, "w_dps_raw": 2.0}
        self.assertFalse(rd.eligible(withheld, "w_dps"))
        self.assertFalse(rd.eligible(withheld, "dps_vs_VEH"))
        for stat in ("w_range", "w_damage", "w_burst", "w_reload"):
            self.assertFalse(rd.eligible(withheld, stat))     # requires w_dps > 0
        self.assertTrue(rd.eligible(withheld, "hp"))
        self.assertTrue(rd.eligible(withheld, "speed"))

    def test_hero_lane_never_reenters_ordinary_distributions(self):
        self._install([dict(NORMAL_ROW, id="SYNHERO", build_limit=1)], [])
        candidates = rd.peer_rows()      # the DISTRIBUTION corpus
        self.assertNotIn("SYNHERO", {r["id"] for r in candidates})


class EvidenceCountsTest(unittest.TestCase):
    def test_counts_are_honest_over_in_memory_rows_only(self):
        rows = [
            dict(NORMAL_ROW),                                       # no verdict -> legacy
            dict(NORMAL_ROW, id="B", w_evidence="incomplete"),
            dict(NORMAL_ROW, id="C", w_evidence="supported"),
            dict(NORMAL_ROW, id="D", w_evidence="incomplete"),
        ]
        counts = rd.evidence_counts(rows)
        self.assertEqual(counts[rd.LEGACY_EVIDENCE], 1)
        self.assertEqual(counts["incomplete"], 2)
        self.assertEqual(counts["supported"], 1)

    def test_missing_label_counts_as_legacy_unassessed(self):
        row = {"source": "S", "hp": 10}                              # doc5/doc1 row shape
        self.assertEqual(rd.evidence_counts([row]), {rd.LEGACY_EVIDENCE: 1})


# ── THE BOUNDARY: a REAL extract() call, really written JSONL, the REAL loaders ───────────────
# The consumer unit tests above feed hand-built corpus rows; a synthetic status there can
# drift from what `extract_ini_units` actually emits. These tests push synthetic temporary
# SOURCE FILES through the whole chain — `ex.extract` -> the --json dump shape ->
# `ini_rows`/`peer_hero_rows` -> `build_distributions`/`target_for` — so the contract is
# verified across the boundary, not mocked. The committed corpus is still not touched: the
# reference checkout path `ex.REF` is patched to a temp dir, which is also what lets the
# overlay refusal run without shipping overlay files.


VERSES = "100,95,85,80,70,60,60,60,50,20,20"

BOUNDARY_RULES = """\
[Countries]
0=GDI

[VehicleTypes]
0=E1CONV
1=E2CONV
2=E3CONV
3=NRHERO
4=BURST2N
5=UNKPRIM
6=CHERO
7=RAILH

[E1CONV]
Name=Conv One
Primary=GunA
Strength=400
Cost=800
Speed=7
ROT=5
Owner=GDI

[E2CONV]
Name=Conv Two
Primary=GunA
Strength=500
Cost=900
Speed=7
ROT=5
Owner=GDI

[E3CONV]
Name=Conv Three
Primary=GunA
Strength=450
Cost=700
Speed=7
ROT=5
Owner=GDI

[GunA]
Damage=20
ROF=10
Range=6
Burst=1
Warhead=GunWH

[GunWH]
Verses=%s

[GunB]
Damage=10
ROF=5
Burst=2
Range=6
Warhead=GunWH

[RealGun]
Damage=15
ROF=5
Range=5
Warhead=GunWH

[RailGun]
Damage=10
ROF=5
Range=8
Burst=2
IsRailgun=yes
Warhead=GunWH

[NRHERO]
Name=Rail Hero
Primary=RailGun
Strength=500
Cost=1200
BuildLimit=1
Speed=6
ROT=5
Owner=GDI

[BURST2N]
Name=Burst Two
Primary=GunB
Strength=480
Cost=900
Speed=7
ROT=5
Owner=GDI

[UNKPRIM]
Name=Unknown Primary
Primary=Ghost
Secondary=RealGun
Strength=420
Cost=650
Speed=7
ROT=5
Owner=GDI

[CHERO]
Name=Conv Hero
Primary=GunA
Strength=380
Cost=1100
BuildLimit=1
Speed=6
ROT=5
Owner=GDI
""" % VERSES


class BoundaryTest(unittest.TestCase):
    """Real `extract` -> temp JSONL -> real loaders -> `target_for`, one chain, no mocks."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        tmp = pathlib.Path(self.tmp.name)
        rules = _write_jsonl(tmp, "rules_SynthIni.ini", [])  # helper renamed below; plain file
        rules.write_text(BOUNDARY_RULES, encoding="latin-1")
        corp = tmp / "ini_corpus.json"
        arm = tmp / "armor.json"
        stack = patch.multiple(ex, REF=tmp)
        stack.start()
        self.addCleanup(stack.stop)
        self.ex_rows, self.notes = ex.extract("SynthIni", {"file": "rules_SynthIni.ini",
                                                           "engine": "ra2"})
        corp.write_text(_extract_dump(self.ex_rows), encoding="utf-8")
        armor = [dict(ARMOR_ROW, id=i) for i in ("E1CONV", "CHERO")]
        arm.write_text("\n".join(json.dumps(r) for r in armor) + "\n", encoding="utf-8")
        stack2 = patch.multiple(rd, INI_CORPUS=corp, INI_ARMOR=arm)
        stack2.start()
        self.addCleanup(stack2.stop)
        self.cameo = [
            {"source": "Cameo", "id": "c1", "name": "c1", "type": "vehicle",
             "hp": 350, "speed": 7, "turn_speed": 5, "cost": 800, "w_dps": 2.5},
            {"source": "Cameo", "id": "c2", "name": "c2", "type": "vehicle",
             "hp": 500, "speed": 7, "turn_speed": 5, "cost": 900, "w_dps": 4.5},
            {"source": "Cameo", "id": "c3", "name": "c3", "type": "vehicle",
             "hp": 420, "speed": 7, "turn_speed": 5, "cost": 700, "w_dps": 3.5},
        ]

    def test_conventional_nominal_direct_passes_with_precise_basis(self):
        out = {r["id"]: r for r in rd.ini_rows()}
        self.assertEqual({r["id"] for r in out.values()},
                         {"E1CONV", "E2CONV", "E3CONV", "BURST2N", "UNKPRIM"})
        conv = out["E1CONV"]
        self.assertEqual(conv["w_evidence"], "nominal_direct")
        self.assertNotIn("w_evidence_reason", conv)
        self.assertIs(conv["w_dps_usable"], True)       # vouches for the DIRECT contract ONLY
        self.assertEqual(conv["w_dps"], 2.0)            # 20/10, the declared nominal-direct
        self.assertEqual(conv["dps_vs_VEH"], 2.0)       # armor map frac 1.0
        self.assertEqual(conv["hp"], 400)
        self.assertEqual(conv["cost"], 800)
        self.assertNotIn("w_dps_raw", conv)

    def test_railgun_and_burst2_withhold_everything_dps_derived(self):
        out = {r["id"]: r for r in rd.ini_rows()}
        rail = out["RAILHERO"] if "RAILHERO" in out else None
        # the rail hero is build-limit 1: it withholds in the HERO loader, the ordinary lane
        burst = out["BURST2N"]
        self.assertIsNone(burst["w_dps"])
        self.assertEqual(burst["w_dps_raw"], 2.0)       # the direct-channel diagnostic
        self.assertEqual(burst["w_evidence"], "incomplete")
        self.assertEqual(burst["w_evidence_reason"], "burst_unfolded")
        self.assertEqual(burst["w_burst"], 2)           # raw cadence survives for the later fold
        for lad in rd.LADDERS:
            self.assertIsNone(burst[f"dps_vs_{lad}"])
        self.assertEqual(burst["hp"], 480)              # chassis intact
        self.assertEqual(burst["cost"], 900)
        hero = {r["id"]: r for r in rd.peer_hero_rows()}["NRHERO"]
        self.assertTrue(hero["hero"])
        self.assertEqual(hero["w_evidence_reason"], "exotic_channels")
        self.assertIsNone(hero["w_dps"])
        self.assertEqual(hero["w_dps_raw"], 2.0)
        for lad in rd.LADDERS:
            self.assertIsNone(hero[f"dps_vs_{lad}"])
        # and a conventional HERO keeps its numeric behaviour on the same boundary
        self.assertEqual({r["id"]: r for r in rd.peer_hero_rows()}["CHERO"]["w_dps"], 2.0)

    def test_unknown_primary_is_not_replaced_by_the_secondary(self):
        out = {r["id"]: r for r in rd.ini_rows()}
        row = out["UNKPRIM"]
        self.assertEqual(row["weapon"], "Ghost")        # the ORIGINAL primary stays primary
        self.assertIsNone(row.get("w_from_secondary"))
        self.assertNotIn("wdummy_weapon", row)
        self.assertEqual(row["w2_weapon"], "RealGun")   # raw secondary slot stays explicit
        self.assertEqual(row["w2_evidence"], "nominal_direct")
        self.assertIsNone(row.get("w_dps"))             # nothing votes from the UNKNOWN slot
        # The secondary's verdict rides under its OWN prefix and never gates the primary —
        # the top-level label stays legacy (absent status), never certified.
        self.assertEqual(row["w_evidence"], rd.LEGACY_EVIDENCE)
        conv = {r["id"]: r for r in rd.ini_rows()}["E1CONV"]
        self.assertEqual(conv["w_evidence"], "nominal_direct")

    def test_target_for_sees_withheld_rows_not_at_all(self):
        rows = rd.ini_rows()
        dist = rd.build_distributions(rows)
        cdist = rd.build_distributions(self.cameo)["Cameo"]
        for stat, gate in (("w_dps", True), ("hp", False)):
            all_target = rt.target_for(rows, self.cameo[0], stat, dist, cdist)
            conv_only = [r for r in rows if r["w_evidence"] == "nominal_direct"]
            clean_target = rt.target_for(conv_only, self.cameo[0], stat, dist, cdist)
            if gate:
                self.assertEqual(all_target, clean_target)  # withheld votes NOWHERE
            else:
                self.assertIsNotNone(all_target[0])         # hp target survives
                self.assertTrue(conv_only[0]["w_evidence"] != rd.LEGACY_EVIDENCE)
        window = rt.target_for(rows, self.cameo[0], "w_dps", dist, cdist)
        self.assertEqual(window[2], 1)

    def test_missing_overlay_refuses_instead_of_mislabelling(self):
        rows, notes = ex.extract("SynthEnh", {"file": "rules_SynthIni.ini",
                                              "engine": "ts",
                                              "overlay": "overlay_absent.ini"})
        self.assertEqual(rows, [])
        self.assertTrue(any("REFUSED" in n and "missing" in n for n in notes))
        # and the consumer never sees the base file under the ENHANCED identity
        ids = {r["id"] for r in rd.ini_rows()}
        self.assertFalse(any(r["source"] == "SynthEnh" for r in rd.ini_rows()))
        self.assertIn("E1CONV", ids)                    # base source carries its own label


def _extract_dump(rows):
    """Mirrors `extract_ini_units --json`'s one-row-per-line dump (its shape is the contract
    the consumer reads); None/""/[] dropped, `buildable` always explicit."""
    return "\n".join(
        json.dumps({k: v for k, v in r.items() if k == "buildable" or v not in (None, "", [])})
        for r in rows) + "\n"


if __name__ == "__main__":
    unittest.main()
