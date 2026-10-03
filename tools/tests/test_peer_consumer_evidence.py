"""The Doc 5 (OpenRA peers) CONSUMER honours the emitter's weapon evidence — no
`peer_rows`/`peer_hero_rows` row may turn an uncertified estimate into an authoritative target.

The `extract_peer_units` emitter appends `Evidence | Reason` (and may append `Usable`) to
every Doc 5 table. Both loaders must map those headers to the canonical `w_evidence`/
`w_evidence_reason` keys and gate THROUGH the shared `apply_weapon_evidence` BEFORE any
`dps_vs_*` is derived — the exact-string policy, its fail-closed direction and the
`legacy-unassessed` compatibility rule are defined once in `reference_distribution` and are
NOT re-stated here; this file pins the DOC 5 side of the contract:

  * `nominal_direct` keeps the existing numerics, labelled with the verdict itself;
  * `incomplete` (+ reason) withholds `w_dps` and EVERY `dps_vs_*`; the raw direct estimate
    is kept separately on `w_dps_raw`, voting nowhere; hp/speed/cost and the other weapon
    fields survive so the row still votes on the chassis;
  * an explicit UNKNOWN status is refused, never normalised, and withheld as itself;
  * a legacy table WITHOUT the evidence columns (the committed corpus shape today) is
    legacy-unassessed with numeric behaviour VERBATIM — absent status is legacy, never
    certified;
  * a `Usable` column is parsed STRICTLY: string "False" is FALSE — never a truthy string —
    and a malformed token (`yes`, `1`, a typo) fails closed, withholding whatever the label
    says; `—`/blank is no verdict at all, leaving the evidence label in charge;
  * the ordinary lane and the hero lane apply the SAME policy and stay disjoint — heroes
    (Limit 1) never re-enter the ordinary distributions;
  * a withheld row contributes to NO weapon aggregate in `build_distributions` while its
    chassis vote survives;
  * the loaders NEVER mutate the corpus document they read.

⛔ ALL FIXTURES ARE SMALL AND SYNTHETIC. The real Doc 5 corpus
(`docs/design/ORIGINAL_UNITS_PEER_OPENRA.md`), the INI corpus and Document 1 are not read
at all — a temp doc patches `rd.ROOT`, and the INI/Doc1 loaders are pointed at absent temp
paths / stubbed — and no corpus is regenerated here.
"""

from __future__ import annotations

import pathlib
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "balance"))
sys.path.insert(0, str(ROOT / "tools" / "reference"))
sys.path.insert(0, str(ROOT / "tools" / "audit"))
import reference_distribution as rd   # noqa: E402


# ── the synthetic Doc 5 fixture ───────────────────────────────────────────────────────────────
# Column order mirrors the emitter's (`| id | unit | type | ... | vsBLD | Evidence | Reason |`),
# `—` is the emitter's empty-cell convention.

NUM_COLS = ["HP", "×rifle", "Cost", "×rifle cost", "Speed", "Turn", "Turret", "Limit",
            "Range", "Dmg", "Burst", "Reload", "DPS", "vsINF", "vsVEH", "vsAIR", "vsBLD"]


def _header(evidence, usable=False):
    cols = (["id", "unit", "type", "faction"] + NUM_COLS
            + (["Evidence", "Reason"] if evidence else [])
            + (["Usable"] if usable else []))
    sep = ["---"] * len(cols)
    return "| " + " | ".join(cols) + " |\n| " + " | ".join(sep) + " |"


def _row(uid, name, limit=None, evidence=None, reason="—", usable=None):
    # Turret | Limit sit between Turn and Range, exactly as the emitter writes them.
    cells = [f"`{uid}`", name, "vehicle", "SYN", "400", "4.00", "800", "8.00",
             "7", "5", "n", limit or "—", "6", "20", "2", "10", "2.00",
             "—", "1.00", "—", "—"]
    if evidence is not None:
        cells += [evidence, reason]
    if usable is not None:
        cells += [usable]
    return "| " + " | ".join(cells) + " |"


SYNTH_DOC = "\n".join([
    "# Original units — OpenRA peer crossovers (synthetic consumer fixture)",
    "",
    "## SynthPeer  (8 buildable units)",
    "",
    _header(evidence=True),
    _row("NOM", "Synth Nominal", evidence="nominal_direct"),
    _row("NOM2", "Synth Nominal Two", evidence="nominal_direct"),
    _row("INC", "Synth Incomplete", evidence="incomplete", reason="exotic_channels"),
    _row("UNK", "Synth Unknown", evidence="brand_new_verdict"),
    _row("PHEV", "Synth Empty Verdict", evidence="—"),
    _row("NOMHERO", "Synth Nominal OneOff", limit="1", evidence="nominal_direct"),
    _row("INCHERO", "Synth Incomplete OneOff", limit="1",
         evidence="incomplete", reason="exotic_channels"),
    _row("UNKHERO", "Synth Unknown OneOff", limit="1", evidence="brand_new_verdict"),
    "",
    "## SynthPeerUsable  (8 buildable units)",
    "",
    _header(evidence=True, usable=True),
    _row("NOMT", "Synth Vouched", evidence="nominal_direct", usable="True"),
    _row("NOMT2", "Synth Vouched Two", evidence="nominal_direct", usable="true"),
    _row("NOMU", "Synth Unvouched", evidence="nominal_direct", usable="—"),
    _row("FAUS", "Synth False Usable", evidence="nominal_direct", usable="False"),
    _row("MAL", "Synth Malformed Usable", evidence="nominal_direct", usable="yes"),
    _row("NOMTHERO", "Synth Vouched OneOff", limit="1",
         evidence="nominal_direct", usable="True"),
    _row("FAUSHERO", "Synth False Usable OneOff", limit="1",
         evidence="nominal_direct", usable="False"),
    _row("MALHERO", "Synth Malformed Usable OneOff", limit="1",
         evidence="nominal_direct", usable="yes"),
    "",
    "## SynthLegacy  (2 buildable units)",
    "",
    _header(evidence=False),
    _row("LEG", "Synth Legacy"),
    _row("LEGHERO", "Synth Legacy OneOff", limit="1"),
    "",
])


class PatchedDoc:
    """A temp-file Doc 5 corpus — the committed document is never touched."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        tmp = pathlib.Path(self.tmp.name)
        (tmp / "docs" / "design").mkdir(parents=True)
        self.doc = tmp / "docs" / "design" / "ORIGINAL_UNITS_PEER_OPENRA.md"
        self.doc.write_text(SYNTH_DOC, encoding="utf-8")
        stack = patch.multiple(rd, ROOT=tmp,
                               INI_CORPUS=tmp / "absent_ini_corpus.json",
                               INI_ARMOR=tmp / "absent_armor.json")
        stack.start()
        self.addCleanup(stack.stop)
        stub = patch.multiple(rd, doc1_rows=lambda: [])
        stub.start()
        self.addCleanup(stub.stop)

    def _loaders(self):
        return ({r["id"]: r for r in rd.peer_rows()},
                {r["id"]: r for r in rd.peer_hero_rows()})


class Doc5ConsumerEvidenceTest(PatchedDoc, unittest.TestCase):
    """Every verdict scenario, in BOTH the ordinary and the hero lane."""

    def test_nominal_direct_keeps_numerics_and_is_labelled(self):
        out, heroes = self._loaders()
        for row in (out["NOM"], heroes["NOMHERO"]):
            self.assertEqual(row["w_evidence"], "nominal_direct")
            self.assertNotIn("w_evidence_reason", row)
            self.assertEqual(row["w_dps"], 2.0)
            self.assertNotIn("w_dps_raw", row)
            self.assertEqual(row["dps_vs_VEH"], 2.0)      # 2.0 x frac 1.0
            for lad in ("INF", "AIR", "BLD"):
                self.assertIsNone(row[f"dps_vs_{lad}"])
            self.assertEqual(row["hp"], 400)
            self.assertEqual(row["cost"], 800)
            # ⛔ PER CYCLE since 2026-09-13: the fixture declares Burst 2, so the referenced
            # coordinate is 20 x 2 and the per-shot figure rides alongside. See
            # `reference_distribution.to_per_cycle`.
            self.assertEqual(row["w_damage_per_shot"], 20)
            self.assertEqual(row["w_damage"], 20 * float(row.get("w_burst") or 1))

    def test_incomplete_withholds_w_dps_and_every_dps_vs(self):
        out, heroes = self._loaders()
        for row in (out["INC"], heroes["INCHERO"]):
            self.assertIsNone(row["w_dps"])
            self.assertEqual(row["w_dps_raw"], 2.0)       # raw direct estimate, kept apart
            self.assertEqual(row["w_evidence"], "incomplete")
            self.assertEqual(row["w_evidence_reason"], "exotic_channels")
            for lad in rd.LADDERS:
                self.assertIsNone(row[f"dps_vs_{lad}"])   # withheld even though a frac exists
            self.assertEqual(row["hp"], 400)              # chassis intact
            self.assertEqual(row["cost"], 800)
            # clause-5's armed test still sees the damage; it is now the PER-CYCLE total.
            self.assertEqual(row["w_damage_per_shot"], 20)
            self.assertEqual(row["w_damage"], 20 * float(row.get("w_burst") or 1))

    def test_unknown_explicit_status_is_refused_not_trusted(self):
        out, heroes = self._loaders()
        for row in (out["UNK"], heroes["UNKHERO"]):
            self.assertIsNone(row["w_dps"])
            self.assertEqual(row["w_dps_raw"], 2.0)
            self.assertEqual(row["w_evidence"], "brand_new_verdict")   # exact, UNNORMALIZED
            for lad in rd.LADDERS:
                self.assertIsNone(row[f"dps_vs_{lad}"])

    def test_empty_verdict_cell_is_legacy_not_a_status(self):
        out, heroes = self._loaders()
        for row in (out["PHEV"],):
            self.assertEqual(row["w_evidence"], rd.LEGACY_EVIDENCE)
            self.assertEqual(row["w_dps"], 2.0)
            self.assertNotIn("w_dps_raw", row)
            self.assertEqual(row["dps_vs_VEH"], 2.0)

    def test_absent_evidence_column_is_legacy_unassessed_numeric_verbatim(self):
        out, heroes = self._loaders()
        for row in (out["LEG"], heroes["LEGHERO"]):
            self.assertEqual(row["w_evidence"], rd.LEGACY_EVIDENCE)
            self.assertEqual(row["w_dps"], 2.0)           # compatibility numeric behaviour
            self.assertNotIn("w_dps_raw", row)
            self.assertEqual(row["dps_vs_VEH"], 2.0)
            for lad in ("INF", "AIR", "BLD"):
                self.assertIsNone(row[f"dps_vs_{lad}"])

    def test_usable_string_false_is_false_never_truthy(self):
        out, heroes = self._loaders()
        for row in (out["FAUS"], heroes["FAUSHERO"]):
            self.assertIs(row["w_dps_usable"], False)
            self.assertIsNone(row["w_dps"])               # withheld whatever the label says
            self.assertEqual(row["w_dps_raw"], 2.0)
            self.assertEqual(row["w_evidence"], "nominal_direct")
            self.assertIn("dps_unusable", row["w_evidence_reason"])
            for lad in rd.LADDERS:
                self.assertIsNone(row[f"dps_vs_{lad}"])

    def test_malformed_usable_cell_fails_closed(self):
        out, heroes = self._loaders()
        for row in (out["MAL"], heroes["MALHERO"]):
            self.assertIs(row["w_dps_usable"], False)
            self.assertIsNone(row["w_dps"])
            self.assertEqual(row["w_dps_raw"], 2.0)
            self.assertIn("dps_unusable", row["w_evidence_reason"])
            self.assertIn("malformed_usable_cell", row["w_evidence_reason"])
            for lad in rd.LADDERS:
                self.assertIsNone(row[f"dps_vs_{lad}"])

    def test_usable_true_keeps_nominal_numerics(self):
        out, heroes = self._loaders()
        for row in (out["NOMT"], heroes["NOMTHERO"]):
            self.assertIs(row["w_dps_usable"], True)
            self.assertEqual(row["w_dps"], 2.0)
            self.assertNotIn("w_dps_raw", row)
            self.assertEqual(row["dps_vs_VEH"], 2.0)

    def test_hero_lane_and_ordinary_lane_are_disjoint(self):
        out, heroes = self._loaders()
        hero_ids = {r for r in heroes}
        self.assertEqual(hero_ids, {"NOMHERO", "INCHERO", "UNKHERO",
                                    "NOMTHERO", "FAUSHERO", "MALHERO", "LEGHERO"})
        self.assertEqual(set(out), {"NOM", "NOM2", "INC", "UNK", "PHEV",
                                    "NOMT", "NOMT2", "NOMU", "FAUS", "MAL", "LEG"})
        for row in heroes.values():
            self.assertTrue(row["hero"])                  # population rule intact both ways


class Doc5RecordMappingTest(unittest.TestCase):
    """The header mapper itself: placeholders are absent; malformed fails closed."""

    def test_placeholder_and_blank_cells_map_to_absent(self):
        rec = rd.doc5_evidence_record({"evidence": "—", "reason": "—"})
        self.assertEqual(rec, {})
        self.assertEqual(rd.doc5_evidence_record({"evidence": "", "reason": ""}), {})
        self.assertEqual(rd.doc5_evidence_record({}), {})

    def test_placeholder_usable_carries_no_verdict(self):
        self.assertEqual(rd.doc5_evidence_record({"evidence": "nominal_direct",
                                                  "usable": "—"}), {"w_evidence": "nominal_direct"})

    def test_malformed_usable_fails_closed_and_keeps_the_extracted_reason(self):
        rec = rd.doc5_evidence_record({"evidence": "incomplete",
                                       "reason": "exotic_channels", "usable": "1"})
        self.assertIs(rec["w_dps_usable"], False)
        self.assertEqual(rec["w_evidence_reason"], "exotic_channels; "
                                                   "dps_unusable: malformed_usable_cell '1'")

    def test_strict_boolean_tokens(self):
        self.assertIs(rd.doc5_evidence_record({"usable": "False"})["w_dps_usable"], False)
        self.assertIs(rd.doc5_evidence_record({"usable": "true"})["w_dps_usable"], True)


class Doc5DistributionTest(PatchedDoc, unittest.TestCase):
    """A withheld row votes on NO weapon aggregate; the chassis vote survives."""

    WITHHELD = {"INC", "UNK", "FAUS", "MAL"}

    def test_withheld_rows_vote_nowhere_on_weapons_yet_on_chassis(self):
        peers = rd.peer_rows()
        d_all = rd.build_distributions(peers)
        d_kept = rd.build_distributions([r for r in peers if r["id"] not in self.WITHHELD])
        for src in ("SynthPeer", "SynthPeerUsable"):
            self.assertIsNotNone(d_kept[src]["vehicle"].get("w_dps"))
            for stat in ("w_dps", "w_range", "w_damage", "dps_vs_VEH") + rd.ARMOR_STATS:
                self.assertEqual(d_all[src]["vehicle"].get(stat), d_kept[src]["vehicle"].get(stat),
                                 f"{src}/{stat} changed by a withheld row")
            for stat in ("hp", "speed"):
                self.assertIn(stat, d_all[src]["vehicle"])   # chassis still voted

    def test_evidence_counts_are_honest_over_the_loaders_rows(self):
        counts = rd.evidence_counts(rd.peer_rows())
        self.assertEqual(counts[rd.LEGACY_EVIDENCE], 2)      # PHEV (—) + LEG (no column)
        self.assertEqual(counts["nominal_direct"], 7)     # NOM, NOM2, NOMT, NOMT2, NOMU,
        #                                                   FAUS, MAL (usable gate withholds
        #                                                   the NUMBERS, not the label)
        self.assertEqual(counts["incomplete"], 1)
        self.assertEqual(counts["brand_new_verdict"], 1)


class Doc5NoCorpusMutationTest(PatchedDoc, unittest.TestCase):
    def test_loaders_never_mutate_the_corpus_document(self):
        before = self.doc.read_bytes()
        rd.peer_rows()
        rd.peer_hero_rows()
        self.assertEqual(before, self.doc.read_bytes())


if __name__ == "__main__":
    unittest.main()
