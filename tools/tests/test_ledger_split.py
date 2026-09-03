"""Unit tests for the W3 ledger split (tools/balance/extract_stats.py).

The split exists so that each tree answers exactly ONE review question:

    docs/balance/<faction>.json          a diff means THE GAME changed
    docs/balance/derived/<faction>.json  a diff means THE MODEL changed

That guarantee is only worth anything if it cannot rot back. These tests pin both
halves: the mechanical split, and the committed artifacts that prove it held.
"""

from __future__ import annotations

import json
import pathlib
import sys
import unittest

import _bootstrap  # noqa: F401 — sys.path side effect

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "balance"))
import extract_stats as es  # noqa: E402

LEDGERS = ROOT / "docs" / "balance"
DERIVED = LEDGERS / "derived"

# Every key the model produces. A raw ledger containing ANY of these is the
# regression this suite exists to catch — including the pre-split names, so an old
# branch cannot quietly reintroduce them.
MODEL_KEYS = {
    "k", "avg_versus", "effective_per_shot", "eff_reload", "effective_dps",
    "k_context", "k_flat", "k_flat_context", "pct_absolute",
    "pct_absolute_context", "folded_rounding", "folded_rounding_context",
    "dps_floor", "factor_targets", "factor_range", "factor_deadzone", "overkill",
    "effective_damage", "damage_total", "footprint", "reliability", "sigma",
    "effective_base_total", "effective_footprint_cells2",
    "effective_avg_reliability", "effective_sigma",
}


def _doc(**armament):
    """A one-actor, one-armament ledger doc."""
    return {"schema": 2, "ledger": "test", "pack": "p",
            "sections": {"vehicles": {"tank": {"armaments": [armament]}}}}


class SplitDerivedTest(unittest.TestCase):
    def test_moves_model_output_and_keeps_raw(self):
        raw, derived = es.split_derived(_doc(
            slot="Armament", weapon="Gun", range="6000", reloaddelay="10",
            **{es.DERIVED_KEY: {"k": 1.5, "effective_dps": 300.0}}))

        arm = raw["sections"]["vehicles"]["tank"]["armaments"][0]
        self.assertNotIn(es.DERIVED_KEY, arm)
        self.assertEqual(arm["range"], "6000")          # raw stats untouched

        got = derived["sections"]["vehicles"]["tank"]["armaments"][0]
        self.assertEqual(got["k"], 1.5)
        self.assertEqual(got["slot"], "Armament")       # join keys repeated
        self.assertEqual(got["weapon"], "Gun")

    def test_derived_side_repeats_no_raw_stat(self):
        """Join keys only — two copies of a stat is how drift gets created."""
        _raw, derived = es.split_derived(_doc(
            slot="Armament", weapon="Gun", range="6000", reloaddelay="10",
            damage_warheads=[{"damage": "2000"}],
            **{es.DERIVED_KEY: {"k": 1.5}}))
        got = derived["sections"]["vehicles"]["tank"]["armaments"][0]
        self.assertEqual(set(got), {"slot", "weapon", "k"})

    def test_armament_without_metrics_is_dropped(self):
        """A weapon the model cannot score leaves no empty husk in the sidecar."""
        _raw, derived = es.split_derived(_doc(slot="Armament", weapon="Dummy",
                                              **{es.DERIVED_KEY: None}))
        self.assertEqual(derived["sections"], {})

    def test_header_is_carried_over(self):
        _raw, derived = es.split_derived(_doc(slot="Armament", weapon="Gun",
                                              **{es.DERIVED_KEY: {"k": 1.0}}))
        self.assertEqual(derived["ledger"], "test")
        self.assertEqual(derived["pack"], "p")
        self.assertEqual(derived["schema"], 2)


class FnumTest(unittest.TestCase):
    def test_takes_the_first_of_a_list(self):
        # fnum is for scalar fields; burst cadence passes the raw list to
        # formula.eff_reload instead of using this convenience parser.
        self.assertEqual(es.fnum("15, 15, 15"), 15.0)

    def test_bad_input_is_none_not_a_crash(self):
        for bad in (None, "", "abc", "-"):
            self.assertIsNone(es.fnum(bad), bad)


class CommittedLedgerTest(unittest.TestCase):
    """The artifacts themselves — CLAUDE.md rule 3, don't trust, verify."""

    def test_no_raw_ledger_carries_model_output(self):
        offenders = []
        for path in sorted(LEDGERS.glob("*.json")):
            doc = json.loads(path.read_text(encoding="utf-8"))
            for section in doc.get("sections", {}).values():
                for actor, unit in section.items():
                    for arm in unit.get("armaments", []):
                        for key in MODEL_KEYS & set(arm):
                            offenders.append(f"{path.name}:{actor}.{key}")
        self.assertEqual(offenders[:10], [],
                         f"{len(offenders)} raw ledger rows carry model output; "
                         "derived values belong in docs/balance/derived/")

    def test_every_sidecar_has_a_raw_counterpart(self):
        for path in sorted(DERIVED.glob("*.json")):
            if path.name.startswith("_"):
                continue
            self.assertTrue((LEDGERS / path.name).exists(),
                            f"{path.name} has no raw ledger")

    def test_model_constants_are_committed(self):
        """_model.json is what makes a retune show up as a readable diff."""
        doc = json.loads((DERIVED / "_model.json").read_text(encoding="utf-8"))
        self.assertIn("BLOB_UPTIME", doc["target_model"])
        self.assertGreater(doc["target_model"]["reference_hp"], 0)
        self.assertGreater(sum(doc["target_model"]["armor_census"].values()), 0)
        self.assertEqual(doc["weapon_timing"]["ENGINE_DEFAULT_BURST_DELAY"], 5.0)
        self.assertGreater(doc["percentage_damage"]["FOLDED_SCALE_DENOMINATOR"], 0)


if __name__ == "__main__":
    unittest.main()
