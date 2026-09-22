#!/usr/bin/env python3
"""Apply the chassis-only transport slice from the 20260916 map.

Cost is intentionally absent: Cargo.InitialUnits pricing is governed by the
passenger-sum law, and the four current authored loads already resolve to
their current carrier costs. Only HP, Aircraft.Speed/TurnSpeed and the F1/F2
heal/repair companions move here. The shared materializer preflights complete
resolved old/target tuples before any per-file replacement.
"""
from __future__ import annotations

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import apply_harvester_durability as Editor  # noqa: E402

ROOT = Editor.ROOT
GDI = ROOT / "mods/cameo/ContentPacks/TiberianDawn/GDI/yaml/aircraft.yaml"
NOD = ROOT / "mods/cameo/ContentPacks/TiberianDawn/Nod/yaml/aircraft.yaml"
ALLIES = ROOT / "mods/cameo/ContentPacks/RedAlert/Allies/yaml/aircraft.yaml"
SOVIETS = ROOT / "mods/cameo/ContentPacks/RedAlert/Soviets/yaml/aircraft.yaml"


def fields(hp: int, speed: int, turn: int, step: int, repair: int):
    return {
        "Aircraft": {"Speed": speed, "TurnSpeed": turn},
        "Health": {"HP": hp},
        "Repairable": {"HpPerStep": repair},
        "ChangesHealth@SelfHealing": {"Step": step},
    }


SPECS = {
    "td_gdi_chinooktransport": (GDI, None, fields(82000, 124, 25, 33, 4100)),
    "td_nod_chinooktransport": (NOD, None, fields(82000, 124, 25, 33, 4100)),
    "ra1_allies_alliedchinooktransport": (ALLIES, None, fields(88000, 120, 24, 35, 4400)),
    "ra1_soviets_hiptransport": (SOVIETS, None, fields(104000, 118, 24, 42, 5200)),
}

EXPECTED_OLD = {
    "td_gdi_chinooktransport": {
        "Aircraft.Speed": "150", "Aircraft.TurnSpeed": "30",
        "Health.HP": "100000", "Repairable.HpPerStep": "5000",
        "ChangesHealth@SelfHealing.Step": "40",
    },
    "td_nod_chinooktransport": {
        "Aircraft.Speed": "150", "Aircraft.TurnSpeed": "30",
        "Health.HP": "100000", "Repairable.HpPerStep": "5000",
        "ChangesHealth@SelfHealing.Step": "40",
    },
    "ra1_allies_alliedchinooktransport": {
        "Aircraft.Speed": "125", "Aircraft.TurnSpeed": "25",
        "Health.HP": "125000", "Repairable.HpPerStep": "6250",
        "ChangesHealth@SelfHealing.Step": "50",
    },
    "ra1_soviets_hiptransport": {
        "Aircraft.Speed": "100", "Aircraft.TurnSpeed": "20",
        "Health.HP": "150000", "Repairable.HpPerStep": "7500",
        "ChangesHealth@SelfHealing.Step": "60",
    },
}

EXPECTED_RESOLVED = {
    "td_gdi_chinooktransport": {
        "Aircraft.Speed": ("150", "124"),
        "Aircraft.TurnSpeed": ("30", "25"),
        "Health.HP": ("100000", "82000"),
        "Repairable.HpPerStep": ("5000", "4100"),
        "ChangesHealth@SelfHealing.Step": ("40", "33"),
    },
    "td_nod_chinooktransport": {
        "Aircraft.Speed": ("150", "124"),
        "Aircraft.TurnSpeed": ("30", "25"),
        "Health.HP": ("100000", "82000"),
        "Repairable.HpPerStep": ("5000", "4100"),
        "ChangesHealth@SelfHealing.Step": ("40", "33"),
    },
    "ra1_allies_alliedchinooktransport": {
        "Aircraft.Speed": ("125", "120"),
        "Aircraft.TurnSpeed": ("25", "24"),
        "Health.HP": ("125000", "88000"),
        "Repairable.HpPerStep": ("6250", "4400"),
        "ChangesHealth@SelfHealing.Step": ("50", "35"),
    },
    "ra1_soviets_hiptransport": {
        "Aircraft.Speed": ("100", "118"),
        "Aircraft.TurnSpeed": ("20", "24"),
        "Health.HP": ("150000", "104000"),
        "Repairable.HpPerStep": ("7500", "5200"),
        "ChangesHealth@SelfHealing.Step": ("60", "42"),
    },
}

EXPECTED_OLD = {
    actor: {field: values[0] for field, values in fields.items()}
    for actor, fields in EXPECTED_RESOLVED.items()
}


def main() -> int:
    old_expected = Editor.EXPECTED_OLD
    old_resolved = Editor.EXPECTED_RESOLVED
    old_specs = Editor.SPECS
    try:
        Editor.EXPECTED_OLD = EXPECTED_OLD
        Editor.EXPECTED_RESOLVED = EXPECTED_RESOLVED
        Editor.SPECS = SPECS
        return Editor.main()
    finally:
        Editor.EXPECTED_OLD = old_expected
        Editor.EXPECTED_RESOLVED = old_resolved
        Editor.SPECS = old_specs


if __name__ == "__main__":
    sys.exit(main())
