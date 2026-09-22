"""Regression for R3's nonlinear baseline scaling."""

import math
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "balance"))

import fit_baseband as fit  # noqa: E402


def test_uniform_rescale_changes_current_anchor_span():
    spec = {"hp0": 2.0, "speed0": 2.0, "range0_wdist": 2.0, "dps0": 2.0, "cost0": 1.0}
    members = [(10.0, 0.1, 10.0, 0.1, False, 1.0), (1.0, 1.0, 1.0, 1.0, False, 1.0)]
    at_anchor = [fit.ratio_of(member, spec, 1.0, 1.0) for member in members]
    rescaled = [fit.ratio_of(member, spec, 1.0, 0.5) for member in members]
    span_at_anchor = max(at_anchor) / min(at_anchor)
    span_rescaled = max(rescaled) / min(rescaled)
    assert not math.isclose(span_at_anchor, span_rescaled), (at_anchor, rescaled)


if __name__ == "__main__":
    test_uniform_rescale_changes_current_anchor_span()
    print("fit_baseband R3 scaling regression: PASS")
