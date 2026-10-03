"""Regenerate the CannonAP continuous-heaviness fixtures.

Runs the approved generator command and rebuilds the JSON fixture with the
same helpers the test uses (effective_heaviness model + shared miniyaml):

    python tools/tests/gen_cannonap_fixture.py

The two artifacts are written in lockstep:
    tools/tests/fixtures/cannonap_continuous_generated.yaml
    tools/tests/fixtures/cannonap_continuous_fixture.json
"""

from __future__ import annotations

import json
import pathlib
import subprocess
import sys

import _bootstrap  # noqa: F401 — sys.path side effect

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "audit"))
sys.path.insert(0, str(ROOT / "tools" / "balance"))

import effective_heaviness as eh  # noqa: E402
from miniyaml import load_text  # noqa: E402

GENERATED = ROOT / "tools/tests/fixtures/cannonap_continuous_generated.yaml"
FIXTURE = ROOT / "tools/tests/fixtures/cannonap_continuous_fixture.json"
HEAVINESS_CASES = [0, 500, 1000, 1500, 2000]
NUMERIC_FIELDS = frozenset({
    "Damage", "Spread", "PercentageScale", "PercentageSpread", "Heaviness",
    "MinRadius", "MaxRadius",
})


def parse_generated_warhead(text):
    nodes = load_text(text)
    weapon = next(n for n in nodes if n.key == "^Warhead_CannonAP")
    warhead = next(n for n in weapon.children if n.key.startswith("Warhead@"))
    fields = {}
    for child in warhead.children:
        if child.children:
            fields[child.key] = {row.key: int(row.value)
                                 for row in child.children}
        elif child.key in NUMERIC_FIELDS:
            fields[child.key] = int(child.value)
        else:
            fields[child.key] = child.value
    return warhead.value, fields


def effective_geometry(fields, heaviness):
    spread_eff = eh.scale_length(fields["Spread"], heaviness)
    falloff_len = len(str(fields["Falloff"]).split(","))
    return {
        "effective_spread": spread_eff,
        "effective_range": [i * spread_eff for i in range(falloff_len)],
        "effective_min_radius": eh.scale_length(fields.get("MinRadius", 0), heaviness),
        "effective_max_radius": eh.scale_length(fields.get("MaxRadius", 0), heaviness),
    }


def effective_block(fields, heaviness):
    shared = eh.shared_versus_profile(fields["Versus"], heaviness)
    block = effective_geometry(fields, heaviness)
    block["effective_versus"] = shared
    block["effective_percentage_versus"] = shared
    return block


def main() -> int:
    result = subprocess.run(
        [sys.executable, str(ROOT / "tools/balance/gen_weapon_template.py"),
         "--continuous-family", "CannonAP"],
        capture_output=True, text=True, check=True, cwd=ROOT)

    GENERATED.write_text(result.stdout, encoding="utf-8")
    warhead_type, authored = parse_generated_warhead(result.stdout)

    # Disabled runs the legacy mode: authored tables verbatim, geometry only scaled.
    disabled = effective_geometry(authored, eh.DISABLED)
    disabled["effective_versus"] = dict(authored["Versus"])
    disabled["effective_percentage_versus"] = dict(authored["Versus"])

    fixture = {
        "generated_by": "gen_weapon_template.py --continuous-family CannonAP (stdout)",
        "warhead_type": warhead_type,
        "authored": authored,
        "disabled": disabled,
        "per_heaviness": {str(h): effective_block(authored, h) for h in HEAVINESS_CASES},
    }
    FIXTURE.write_text(json.dumps(fixture, indent=2, sort_keys=True) + "\n",
                       encoding="utf-8")
    print(f"wrote {GENERATED.name} + {FIXTURE.name}: "
          f"{len(authored['Versus'])} versus columns")
    return 0


if __name__ == "__main__":
    sys.exit(main())
