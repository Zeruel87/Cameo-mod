#!/usr/bin/env python3
"""apply_support_durability.py — classic-four support & MCV batch (2026-09-18, slice 2).

Applies the 2026-09-16 reference-map targets for the chassis-only rows
DeepSeek's survey surfaced after the harvester batch (four MCVs and
RA1's two unarmed support vehicles). Reuses the harvester batch's guarded
ActorEditor and resolved old/target preflight; the module-level tables are
swapped for this batch before use.

Grids follow the accepted-batch conventions: HP -> 1,000 grid, Speed ->
integer, and Cost -> 10 grid. Heal/repair values use the nearest integer
to the existing F1/F2 formulas; the audit's established tolerance covers
the fractional HP/2500 result on a 1,000-grid HP value.
    Speed -> integer (unsnapped rounded half-up)
    Cost -> 10 grid for reference-backed MCVs. The two strategic support
    actors retain their authored 5,000 costs because the reference rows do
    not provide class/special ability inputs for repricing.
    TurnSpeed follows the audit formula the actor currently obeys:
    MCVs are F8 vehicles (TurnSpeed = round(Speed/5), 15 -> 13 / 14),
    the gap generator and radar jammer currently RESOLVE at
    2 x round(Speed/5) (the turretless-frontal branch), so their turns
    follow the doubled rule for the new speeds (30 / 30).

Batch table (unsnapped map target -> applied):
    td_gdi/nod_mobileconstructionvehicle
        HP 293,935 -> 294,000  speed 64.72 -> 65  turn 15 -> 13
        step 120 -> 118  hpp 15,000 -> 14,700  cost 5,000 -> 4,920
    ra1_allies/soviets mobileconstructionvehicle
        HP 252,864 -> 253,000  speed 69.53 -> 70  turn 15 -> 14
        step 120 -> 101  hpp 15,000 -> 12,650  cost 5,000 -> 4,650
    ra1_allies_mobilegapgenerator
        HP 96,282 -> 96,000  speed 75.63 -> 76  turn 30 -> 30
        step 10 -> 38  hpp 1,250 -> 4,800  cost 5,000 (held)
    ra1_allies_mobileradarjammer
        HP 71,989 -> 72,000  speed 73.62 -> 74  turn 40 -> 30
        step 10 -> 29  hpp 1,250 -> 3,600  cost 5,000 (held)

The four chinook/HIP transports and any passenger-carried actor are excluded
from this writer because their chassis rows are handled by the sibling
transport materializer. Their authored costs remain governed by the
passenger-sum cargo contract.
^MCV is NOT edited: it also feeds MCVs in ~20 other packs.
"""
from __future__ import annotations

import sys
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

import apply_harvester_durability as Editor  # noqa: E402  (shares ActorEditor)

ROOT = Editor.ROOT

TD_VEH = ROOT / "mods/cameo/ContentPacks/TiberianDawn/GDI/yaml/vehicles.yaml"
TD_NOD_VEH = ROOT / "mods/cameo/ContentPacks/TiberianDawn/Nod/yaml/vehicles.yaml"
RA_AIR_VEH = ROOT / "mods/cameo/ContentPacks/RedAlert/Allies/yaml/vehicles.yaml"
RA_SOV_VEH = ROOT / "mods/cameo/ContentPacks/RedAlert/Soviets/yaml/vehicles.yaml"


def _mcv(hp: int, speed: int, turn: int, cost: int) -> dict[str, dict[str, int]]:
    return {
        "Valued": {"Cost": cost},
        "Mobile": {"Speed": speed, "TurnSpeed": turn},
        "Health": {"HP": hp},
        "Repairable": {"HpPerStep": hp // 20},
        "ChangesHealth@SelfHealing": {"Step": round(hp / 2500)},
    }


SPECS = {
    "td_gdi_mobileconstructionvehicle": (TD_VEH, None, _mcv(294000, 65, 13, 4920)),
    "td_nod_mobileconstructionvehicle": (TD_NOD_VEH, None, _mcv(294000, 65, 13, 4920)),
    "ra1_allies_alliedmobileconstructionvehicle": (RA_AIR_VEH, None, _mcv(253000, 70, 14, 4650)),
    "ra1_soviets_mobileconstructionvehicle": (RA_SOV_VEH, None, _mcv(253000, 70, 14, 4650)),
    "ra1_allies_mobilegapgenerator": (
        RA_AIR_VEH,
        None,
        {"Mobile": {"Speed": 76, "TurnSpeed": 30},
         "Health": {"HP": 96000},
         "Repairable": {"HpPerStep": 4800},
         "ChangesHealth@SelfHealing": {"Step": 38},
         "Valued": {"Cost": 5000}},
    ),
    "ra1_allies_mobileradarjammer": (
        RA_AIR_VEH,
        None,
        {"Mobile": {"Speed": 74, "TurnSpeed": 30},
         "Health": {"HP": 72000},
         "Repairable": {"HpPerStep": 3600},
         "ChangesHealth@SelfHealing": {"Step": 29},
         "Valued": {"Cost": 5000}},
    ),
}

EXPECTED_OLD = {
    "ra1_allies_mobilegapgenerator": {
        "Mobile.Speed": "75",
        "Mobile.TurnSpeed": "30",
        "Health.HP": "25000",
        "Repairable.HpPerStep": "1250",
        "ChangesHealth@SelfHealing.Step": "10",
        "Valued.Cost": "5000",
    },
    "ra1_allies_mobileradarjammer": {
        "Mobile.Speed": "100",
        "Mobile.TurnSpeed": "40",
        "Health.HP": "25000",
        "Repairable.HpPerStep": "1250",
        "ChangesHealth@SelfHealing.Step": "10",
        "Valued.Cost": "5000",
    },
}

EXPECTED_RESOLVED = {
    "td_gdi_mobileconstructionvehicle": {
        "Valued.Cost": ("5000", "4920"),
        "Mobile.Speed": ("75", "65"),
        "Mobile.TurnSpeed": ("15", "13"),
        "Health.HP": ("300000", "294000"),
        "Repairable.HpPerStep": ("15000", "14700"),
        "ChangesHealth@SelfHealing.Step": ("120", "118"),
    },
    "td_nod_mobileconstructionvehicle": {
        "Valued.Cost": ("5000", "4920"),
        "Mobile.Speed": ("75", "65"),
        "Mobile.TurnSpeed": ("15", "13"),
        "Health.HP": ("300000", "294000"),
        "Repairable.HpPerStep": ("15000", "14700"),
        "ChangesHealth@SelfHealing.Step": ("120", "118"),
    },
    "ra1_allies_alliedmobileconstructionvehicle": {
        "Valued.Cost": ("5000", "4650"),
        "Mobile.Speed": ("75", "70"),
        "Mobile.TurnSpeed": ("15", "14"),
        "Health.HP": ("300000", "253000"),
        "Repairable.HpPerStep": ("15000", "12650"),
        "ChangesHealth@SelfHealing.Step": ("120", "101"),
    },
    "ra1_soviets_mobileconstructionvehicle": {
        "Valued.Cost": ("5000", "4650"),
        "Mobile.Speed": ("75", "70"),
        "Mobile.TurnSpeed": ("15", "14"),
        "Health.HP": ("300000", "253000"),
        "Repairable.HpPerStep": ("15000", "12650"),
        "ChangesHealth@SelfHealing.Step": ("120", "101"),
    },
    "ra1_allies_mobilegapgenerator": {
        "Valued.Cost": ("5000", "5000"),
        "Mobile.Speed": ("75", "76"),
        "Mobile.TurnSpeed": ("30", "30"),
        "Health.HP": ("25000", "96000"),
        "Repairable.HpPerStep": ("1250", "4800"),
        "ChangesHealth@SelfHealing.Step": ("10", "38"),
    },
    "ra1_allies_mobileradarjammer": {
        "Valued.Cost": ("5000", "5000"),
        "Mobile.Speed": ("100", "74"),
        "Mobile.TurnSpeed": ("40", "30"),
        "Health.HP": ("25000", "72000"),
        "Repairable.HpPerStep": ("1250", "3600"),
        "ChangesHealth@SelfHealing.Step": ("10", "29"),
    },
}

# Keep the reusable editor's local optimistic guards complete for this batch.
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
    import sys as _sys
    _sys.exit(main())
