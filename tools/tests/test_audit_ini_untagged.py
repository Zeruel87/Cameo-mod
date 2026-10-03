"""Regressions for the INI untagged-row diagnostic."""

import json
import pathlib
import sys


ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "reference"))

import audit_ini_untagged as audit  # noqa: E402


def corpus_rows():
    return [json.loads(line) for line in audit.CORPUS.read_text(encoding="utf-8").splitlines()
            if line.strip()]


def test_labels_report_fields_without_inventing_identity():
    assert audit.classify({"cost": 0, "name": "Armed unit"}) == "zero_cost"
    assert audit.classify({"cost": 100, "tech_level": 11}) == "tech11_low_cost"
    assert audit.classify({"buildable": True}) == "buildable_untagged"
    assert audit.classify({"prerequisite": "FACTORY"}) == "prerequisite_no_owner"


def test_current_bucket_totals_include_actionable_and_prerequisite_rows():
    by_source, summary = audit.summarize_untagged(corpus_rows())
    assert sum(len(buckets["buildable_untagged"]) for buckets in summary.values()) == 468
    assert sum(len(buckets["prerequisite_no_owner"]) for buckets in summary.values()) == 138
    for source, rows in by_source.items():
        assert sum(len(summary[source][bucket]) for bucket in audit.BUCKETS) == len(rows)


if __name__ == "__main__":
    test_labels_report_fields_without_inventing_identity()
    test_current_bucket_totals_include_actionable_and_prerequisite_rows()
    print("INI untagged audit fixtures: PASS")
