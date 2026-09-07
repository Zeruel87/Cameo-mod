#!/usr/bin/env python3
"""LANE-4: Assign correct design.subtype to the 130 units with no template.

This script updates docs/balance/*.json ledger files, setting design.subtype
for units that currently have generic placeholders (Misc, Aircraft, Vehicle,
Infantry, Ship).

Constraint from Claude's orders: use only templates that already exist in
class_membership.py's SUBTYPE_TO_CLASS map. If nothing fits, report it.
"""
import json, glob, os, sys
from collections import defaultdict

# The mapping: actor -> new subtype
# Only use subtypes that exist in SUBTYPE_TO_CLASS or NEEDS_A_NEW_CLASS
ASSIGNMENTS = {
    # === Infantry: Engineers ===
    # All engineers inherit ^SelectableSupportUnit or ^EngineerInfantryTemplate
    # SupportInfantry maps to 'support' class
    "atreides_engineer": "SupportInfantry",
    "corrino_engineer": "SupportInfantry",
    "harkonnen_engineer": "SupportInfantry",
    "ra2_allies_engineer": "SupportInfantry",
    "ra2_soviets_engineer": "SupportInfantry",
    "yuri_engineer": "SupportInfantry",
    "asianalliance_engineer": "SupportInfantry",
    "steelconsortium_engineer": "SupportInfantry",
    "futuretech_engineer": "SupportInfantry",
    "latinsyndicate_engineer": "SupportInfantry",
    "tkm_engineer": "SupportInfantry",
    "ra1_engineer": "SupportInfantry",
    "engineer": "SupportInfantry",  # shared_d2k engineer
    "E6": "SupportInfantry",  # TD engineer

    # === Infantry: Fremen / Saboteur ===
    # atreides_fremen inherits ^D2KInfantry, is a stealthy combat unit
    "atreides_fremen": "SpecialForcesInfantry",
    # fremen_creep is a Fremen Warrior variant
    "fremen_creep": "SpecialForcesInfantry",
    # ordos_saboteur is a cloaked saboteur
    "ordos_saboteur": "SpecialForcesInfantry",

    # === Infantry: Civilians (non-buildable, but still need subtype) ===
    # All inherit ^CivInfantry - support class
    "ra1_agentdelphi": "SupportInfantry",
    "ra1_einstein": "SupportInfantry",
    "ra1_general": "SupportInfantry",
    "ra1_scientist": "SupportInfantry",
    "ra1_technician": "SupportInfantry",

    # === Infantry: Schwarzermond holes ===
    # Energy entities, not real infantry - support
    "schwarzermond_hole": "SupportInfantry",
    "schwarzermond_hole_small": "SupportInfantry",

    # === Aircraft: Carryalls (unarmed transport) ===
    # All carryalls inherit ^RANeutralPlane or ^Helicopter, no weapons
    "atreides_advancedcarryall": "UnarmedTransportHelicopter",
    "corrino_carryall": "UnarmedTransportHelicopter",
    "corrino_advancedcarryall": "UnarmedTransportHelicopter",
    "harkonnen_carryall": "UnarmedTransportHelicopter",
    "harkonnen_advancedcarryall": "UnarmedTransportHelicopter",
    "ordos_advancedcarryall": "UnarmedTransportHelicopter",
    "carryall": "UnarmedTransportHelicopter",
    "carryall.paradrop": "UnarmedTransportHelicopter",
    "carryall.reinforce": "UnarmedTransportHelicopter",
    "carryall_reinforce.ordos": "UnarmedTransportHelicopter",
    "forgotten_carryall": "UnarmedTransportHelicopter",
    "forgotten_chinook": "UnarmedTransportHelicopter",
    "ts_gdi_carryall": "UnarmedTransportHelicopter",

    # === Aircraft: Combat aircraft ===
    # Ornithopter, airdrone, gunship inherit ^RANeutralPlane with weapons
    "atreides_ornithopter": "Fighter",
    "atreides_airdrone": "Fighter",
    "corrino_gunship": "Fighter",
    "harkonnen_gunship": "Fighter",

    # === Aircraft: Bombers / spy planes ===
    # Badgers, cargo planes, spy planes inherit ^AirstrikePlane
    "ra1_allies_badger": "Bomber",
    "ra1_soviets_badger": "Bomber",
    "ra1_badger": "Bomber",
    "ra1_badger_bomber": "Bomber",
    "japan_badger": "Bomber",
    "japan_japanesesuperbomber": "Bomber",
    "ra1_allies_cargoplanebomber": "Bomber",
    "ra1_allies_cargoplaneparadrop": "UnarmedTransportHelicopter",
    "ra1_soviets_spyplane": "Fighter",
    "ra1_soviets_superspyplane": "Fighter",
    "yuriinvisibleplane": "Fighter",
    "naxis_cplane": "Fighter",
    "naxis_horten_bomber": "Bomber",
    "bomber_minebomb.asian": "Bomber",
    "bomber_minebomb2.asian": "Bomber",
    "yrspyp": "Fighter",  # Spy Plane
    "ra2cplane": "Fighter",
    "ra2cplanesov": "Fighter",

    # === Aircraft: Frigate (D2k support aircraft) ===
    "frigate": "UnarmedTransportHelicopter",
    "frigate.paradrop": "UnarmedTransportHelicopter",

    # === Aircraft: TSDPOD (drop pod, not a real aircraft) ===
    "TSDPOD": "SupportInfantry",  # It's a support deployable

    # === Vehicles: APCs (transport) ===
    "atreides_apc": "SupportVehicle",
    "corrino_apc": "SupportVehicle",

    # === Vehicles: Tanks ===
    # devastator inherits ^D2KTank, has weapons - heavy tank
    "devastator": "MainBattleTank",
    "harkonnen_devastatormech": "MainBattleTank",
    # gorynych is a heavy assault tank
    "ra1_soviets_gorynychtank": "MainBattleTank",

    # === Vehicles: Support vehicles ===
    "ra1_allies_minelayer": "SupportVehicle",
    "ra1_allies_mobilegapgenerator": "SupportVehicle",
    "ra1_allies_mobileradarjammer": "SupportVehicle",
    "asianalliance_oiltruck": "SupportVehicle",
    "latinsyndicate_demolitiontruck": "SupportVehicle",
    "ra1_soviets_nukedemotruck": "SupportVehicle",
    "ts_gdi_mobilesensorarray": "SupportVehicle",
    "ts_nod_mobilerepairvehicle": "SupportVehicle",
    "ts_nod_mobilestealthgenerator": "SupportVehicle",

    # === Vehicles: Japan core units (mobile buildings) ===
    "japan_coreairfield": "SupportVehicle",
    "japan_corebarracks": "SupportVehicle",
    "japan_corepowerplant": "SupportVehicle",
    "japan_coreradar": "SupportVehicle",
    "japan_corerefinery": "SupportVehicle",
    "japan_coreservicedepot": "SupportVehicle",
    "japan_coretechcenter": "SupportVehicle",
    "japan_corewarfactory": "SupportVehicle",

    # === Vehicles: Scrap cars (non-buildable civilians) ===
    "scrapcar.latin": "SupportVehicle",
    "scrapcar2.latin": "SupportVehicle",
    "scrapcar_demo.latin": "SupportVehicle",
    "scrapcar2_demo.latin": "SupportVehicle",

    # === Ships: Transports (unarmed) ===
    "ra1_navaltransport": "ScoutShip",
    "LST": "ScoutShip",
    "cabal_lcraft": "ScoutShip",
    "ts_gdi_hover": "ScoutShip",
    "ts_nod_hover": "ScoutShip",

    # === Ships: Combat ===
    # CNCRSS is a submarine - combat ship
    "CNCRSS": "BattleShip",

    # === Misc: Naval transports (amphibious) ===
    "ra2lcrf": "ScoutShip",  # Amphibious Transport
    "ra2sapc": "ScoutShip",  # Amphibious Transport
    "yrhovr": "ScoutShip",   # Hover Transport

    # === Misc: Spy planes (already in aircraft above) ===
    # (handled above)

    # === Misc: Buildings (NOT units - should not be in the unit ledger) ===
    # OILB.RA2, ra2gayard, ra2nayard, yrygyard - these are buildings, not units
    # ra2_awall, ra2_swall, ra2_ywall - walls, not units
    # These will be reported as "not units" rather than assigned a subtype

    # === Misc: Civilian cars (non-buildable, not units) ===
    # ra2_ambu, ra2_bus, ra2_car, etc. - civilian vehicles, not military units
    # These will be reported as "not units"
}

# Units that are NOT units (buildings, walls, civilian props) - skip
NOT_UNITS = {
    "OILB.RA2", "ra2gayard", "ra2nayard", "yrygyard",
    "ra2_awall", "ra2_swall", "ra2_ywall",
    "ra2_ambu", "ra2_ambu_demo", "ra2_bcab", "ra2_bcab_demo",
    "ra2_bus", "ra2_bus_demo", "ra2_car", "ra2_car_demo",
    "ra2_cona", "ra2_cona_demo", "ra2_cop", "ra2_cop_demo",
    "ra2_ddbx", "ra2_ddbx_demo", "ra2_euroc", "ra2_euroc_demo",
    "ra2_jeep", "ra2_jeep_demo", "ra2_limo", "ra2_limo_demo",
    "ra2_ptruck", "ra2_ptruck_demo", "ra2_stang", "ra2_stang_demo",
    "ra2_suvb", "ra2_suvb_demo", "ra2_suvw", "ra2_suvw_demo",
    "ra2_taxi", "ra2_taxi_demo", "ra2_tractor", "ra2_tractor_demo",
    "ra2_trucka", "ra2_trucka_demo", "ra2_truckb", "ra2_truckb_demo",
    "ra2_ycab", "ra2_ycab_demo",
}


def main():
    ledgers = glob.glob('docs/balance/*.json')
    updated = defaultdict(int)
    skipped = []
    not_units_found = []

    for lf in sorted(ledgers):
        if 'derived' in lf or 'class_anchors' in lf:
            continue
        with open(lf, encoding='utf-8') as f:
            data = json.load(f)

        changed = False
        for sec_name, sec in data.get('sections', {}).items():
            for actor, info in sec.items():
                if not isinstance(info, dict):
                    continue
                design = info.get('design', {})
                sub = design.get('subtype', '')
                if sub not in ('Misc', 'Aircraft', 'Vehicle', 'Infantry', 'Ship'):
                    continue

                if actor in NOT_UNITS:
                    not_units_found.append((os.path.basename(lf), actor, sub))
                    continue

                if actor in ASSIGNMENTS:
                    new_sub = ASSIGNMENTS[actor]
                    design['subtype'] = new_sub
                    changed = True
                    updated[os.path.basename(lf)] += 1
                else:
                    skipped.append((os.path.basename(lf), actor, sub))

        if changed:
            with open(lf, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=1, ensure_ascii=False)
                f.write('\n')

    print(f"Updated {sum(updated.values())} units across {len(updated)} ledgers:")
    for lf, n in sorted(updated.items()):
        print(f"  {lf}: {n}")
    print()
    if skipped:
        print(f"SKIPPED (no assignment): {len(skipped)}")
        for lf, actor, sub in sorted(skipped):
            print(f"  {actor} (sub={sub}) in {lf}")
    print()
    if not_units_found:
        print(f"NOT UNITS (buildings/walls/civilians, skipped): {len(not_units_found)}")
        for lf, actor, sub in sorted(not_units_found):
            print(f"  {actor} (sub={sub}) in {lf}")


if __name__ == '__main__':
    main()
