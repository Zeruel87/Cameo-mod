#!/usr/bin/env python3
"""Generate mods/cameo/ai/fransbot_lists.yaml from resolved ruleset traits.

Fransbot's module Info classes carry ~110 [ActorReference] fields that upstream
fills from a Red-Alert ruleset (harv/mcv/lst/...). None of those ids exist in
Cameo, and no single actor is guaranteed loaded in the ContentPack world, so the
lists are generated per-faction from TRAITS instead of hand-typed:

  HarvesterTypes        <- Harvester trait
  McvTypes              <- Transforms.IntoActor -> a construction yard
  DefenseTypes          <- Building + any Attack* trait (not AttackMove)
  AntiAirDefenseTypes   <- defense whose armament weapon targets 'air'
  LandingCraftTypes     <- Cargo + locomotor 'lcraft'
  ...                   see FIELD_MAP below.

Everything lands in one generated file the game merges after ai/fransbot.yaml.
Regenerate:  python tools/ai/gen_fransbot_lists.py
Check drift: python tools/ai/gen_fransbot_lists.py --check
"""

import argparse
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "audit"))
from miniyaml import Ruleset  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
OUT = ROOT / "mods" / "cameo" / "ai" / "fransbot_lists.yaml"

NAVAL_LOCOMOTORS = {"naval", "lcraft", "amphibius", "swimsuit"}
LAND_LOCOMOTORS = {"foot", "tracked", "wheeled", "heavytracked", "heavywheeled",
                   "lighttracked", "chem", "subterranean"}
ATTACK_TRAITS = {"AttackFrontal", "AttackTurreted", "AttackAircraft", "AttackOpenTopped",
                 "AttackFollow", "AttackGarrisoned", "AttackFrontalCharged", "AttackCharges",
                 "AttackLeap", "AttackOmni", "AttackPopupTurreted", "AttackTesla",
                 "AttackTurretedCharged", "AttackWander", "AttackInfectCA", "AttackBomber",
                 "AttackFollowFrontal", "AttackPrismSupportedCA"}
BUILDING_QUEUES = {"building", "rabuilding", "construction", "defence", "radefence"}
INFANTRY_QUEUES = {"infantry", "rainfantry", "soldier"}
VEHICLE_QUEUES = {"vehicle", "ravehicle", "starport", "mech", "walker"}
AIR_QUEUES = {"aircraft", "raaircraft", "plane", "helicopter", "rahelicopter", "scrinarcraft", "scrinwarpaircraft"}
NAVAL_QUEUES = {"ship", "naval", "ranaval", "submarine", "raship"}
DEFENSE_QUEUES = {"defence", "radefence"}


def traits_of(node):
    return {c.key.split("@")[0]: c for c in node.children}


def field(node, trait, key):
    for c in node.children:
        if c.key == trait or c.key.startswith(trait + "@"):
            for ch in c.children:
                if ch.key == key:
                    return ch.value or ""
    return ""


def fields(node, trait, key):
    out = []
    for c in node.children:
        if c.key == trait or c.key.startswith(trait + "@"):
            out.extend(ch.value or "" for ch in c.children if ch.key == key)
    return out


def csv_set(v):
    return {x.strip().lower() for x in v.split(",") if x.strip()}


class Ctx:
    def __init__(self, rs):
        self.rs = rs
        self.cache = {}

    def resolve(self, name):
        if name not in self.cache:
            n = self.rs.actor(name)
            self.cache[name] = self.rs.resolve(name) if n is not None else None
        return self.cache[name]

    def weapon_targets_air(self, node):
        """Any armament weapon whose resolved ValidTargets includes 'air'
        (and isn't explicitly -air)."""
        for c in node.children:
            if not (c.key == "Armament" or c.key.startswith("Armament@")):
                continue
            wname = next((ch.value for ch in c.children if ch.key == "Weapon"), None)
            if not wname:
                continue
            w = self.rs.resolve_weapon(wname.split(".")[0])
            if w is None:
                continue
            valid = set()
            invalid = set()
            for ch in w.children:
                if ch.key == "ValidTargets":
                    valid |= csv_set(ch.value)
                elif ch.key == "InvalidTargets":
                    invalid |= csv_set(ch.value)
            if "air" in valid and "air" not in invalid:
                return True
        return False

    def weapon_targets_ground(self, node):
        for c in node.children:
            if not (c.key == "Armament" or c.key.startswith("Armament@")):
                continue
            wname = next((ch.value for ch in c.children if ch.key == "Weapon"), None)
            if not wname:
                continue
            w = self.rs.resolve_weapon(wname.split(".")[0])
            if w is None:
                continue
            valid = set()
            for ch in w.children:
                if ch.key == "ValidTargets":
                    valid |= csv_set(ch.value)
            if valid & {"ground", "infantry", "vehicle", "structure", "ship", "water"}:
                return True
        return False

    def max_weapon_range(self, node):
        best = 0
        for c in node.children:
            if not (c.key == "Armament" or c.key.startswith("Armament@")):
                continue
            wname = next((ch.value for ch in c.children if ch.key == "Weapon"), None)
            if not wname:
                continue
            w = self.rs.resolve_weapon(wname.split(".")[0])
            if w is None:
                continue
            for ch in w.children:
                if ch.key == "Range":
                    try:
                        # WDist is in cells*1024 for range values; keep raw int
                        best = max(best, int((ch.value or "0").split(",")[0].strip()))
                    except ValueError:
                        pass
        return best


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="verify the file matches a fresh generate")
    args = ap.parse_args()

    rs = Ruleset(str(ROOT))
    ctx = Ctx(rs)

    actors = {}
    for name in rs.actors:
        if name.startswith("^") or name.startswith("-") or name.startswith("("):
            continue
        r = ctx.resolve(name)
        if r is not None:
            actors[name] = r

    def tset(node):
        return {c.key.split("@")[0] for c in node.children}

    def has(node, *ts):
        ks = tset(node)
        return any(t in ks for t in ts)

    def has_attack(node):
        return bool(tset(node) & ATTACK_TRAITS)

    def loco(node):
        return field(node, "Mobile", "Locomotor").lower()

    def cost(node):
        try:
            return int(field(node, "Valued", "Cost") or 0)
        except ValueError:
            return 0

    def speed(node):
        try:
            return int(field(node, "Mobile", "Speed") or field(node, "Aircraft", "Speed") or 0)
        except ValueError:
            return 0

    def queues(node):
        q = set()
        for v in fields(node, "Buildable", "Queue"):
            q |= csv_set(v)
        return q

    def queues_raw(node):
        q = set()
        for v in fields(node, "Buildable", "Queue"):
            q |= {x.strip() for x in v.split(",") if x.strip()}
        return q

    def produces(node):
        p = set()
        for v in fields(node, "Production", "Produces"):
            p |= csv_set(v)
        return p

    buildable = {n: r for n, r in actors.items() if "Buildable" in tset(r)}
    is_building = {n for n, r in buildable.items() if has(r, "Building")}
    is_mobile = {n for n, r in buildable.items() if has(r, "Mobile") and not has(r, "Building")}
    is_air = {n for n, r in buildable.items() if has(r, "Aircraft")}
    is_naval = {n for n, r in buildable.items() if loco(r) in NAVAL_LOCOMOTORS}
    is_ground = {n for n, r in buildable.items() if loco(r) in LAND_LOCOMOTORS}
    is_infantry = {n for n, r in buildable.items() if has(r, "WithInfantryBody", "TakeCover")
                   or queues(r) & INFANTRY_QUEUES}
    is_vtol = {n for n, r in actors.items() if n in is_air and
               (field(r, "Aircraft", "VTOL").lower() == "true" or
                field(r, "Aircraft", "CanHover").lower() == "true")}
    is_fixed = is_air - is_vtol
    has_combat = {n for n, r in buildable.items() if has_attack(r)}
    is_conyard = {n for n, r in buildable.items()
                  if has(r, "Building", "BaseBuilding") and produces(r) & BUILDING_QUEUES}
    is_mcv = {n for n, r in buildable.items()
              if has(r, "Transforms") and not has(r, "Building")
              and any(ctx.resolve(t) is not None and tset(ctx.resolve(t)) & {"Building", "BaseBuilding"}
                      and produces(ctx.resolve(t)) & BUILDING_QUEUES
                      for t in csv_set(field(r, "Transforms", "IntoActor")))}
    is_defense = {n for n in is_building if n in has_combat}
    # walls: defence-queue building with no attack trait and a tiny footprint
    is_wall = set()
    for n in is_building:
        r = actors[n]
        if n in has_combat or not (queues(r) & DEFENSE_QUEUES):
            continue
        dims = field(r, "Building", "Dimensions") or ""
        try:
            d = [int(x) for x in dims.split(",")]
            tiny = max(d) <= 2
        except ValueError:
            tiny = False
        if tiny or has(r, "BlocksProjectiles"):
            is_wall.add(n)
    is_refinery = {n for n, r in buildable.items() if has(r, "Refinery")}
    is_harvester = {n for n, r in buildable.items() if has(r, "Harvester")}
    is_producer = {n for n, r in buildable.items() if has(r, "Building") and produces(r)}
    is_inf_prod = {n for n in is_producer if produces(actors[n]) & INFANTRY_QUEUES}
    is_veh_prod = {n for n in is_producer if produces(actors[n]) & VEHICLE_QUEUES}
    is_air_prod = {n for n in is_producer if produces(actors[n]) & AIR_QUEUES}
    is_nav_prod = {n for n in is_producer if produces(actors[n]) & NAVAL_QUEUES}
    is_landing_craft = {n for n in is_naval if has(actors[n], "Cargo")}
    is_ground_transport = {n for n, r in buildable.items()
                           if has(r, "Cargo") and loco(r) in LAND_LOCOMOTORS}
    is_air_transport = {n for n in is_air if has(actors[n], "Cargo")}
    is_passenger = {n for n, r in buildable.items() if has(r, "Passenger")}
    is_capture = {n for n, r in buildable.items() if has(r, "Captures")}
    is_engineer = {n for n, r in buildable.items() if has(r, "RepairsBridges")}
    is_minelayer = {n for n, r in buildable.items() if has(r, "Minelayer")}
    is_resource_creator = {n for n, r in actors.items() if has(r, "SeedsResource", "LobbyScaledSeedsResource")}
    # Capturable neutral economy (oil derricks etc.): CashTrickler without Buildable,
    # or capturable + trickler
    is_derrick = {n for n, r in actors.items()
                  if has(r, "Capturable") and has(r, "CashTrickler")
                  and "Buildable" not in tset(r)}
    is_aa_defense = {n for n in is_defense if ctx.weapon_targets_air(actors[n])}
    is_ground_defense = {n for n in is_defense if ctx.weapon_targets_ground(actors[n])}
    is_aa_aircraft = {n for n in is_air if ctx.weapon_targets_air(actors[n])}
    # strategic superweapons: buildings hosting a strike/strategic power trait
    SUPERWEAPON_TRAITS = {"NukePower", "NukePowerCA", "IonCannonPower",
                          "DetonateWeaponPower", "DetonateWeaponPowerCA",
                          "FireArmamentPower", "GrantExternalConditionPower"}
    is_superweapon = {n for n, r in buildable.items()
                      if has(r, "Building") and tset(r) & SUPERWEAPON_TRAITS}

    # tech centers: buildings granting a *tech* prerequisite (atek/stek analogues)
    def grants_tech(r):
        for c in r.children:
            if c.key.split("@")[0] != "ProvidesPrerequisite":
                continue
            if "tech" in c.key.lower():
                return True
            for ch in c.children:
                if ch.key == "Prerequisite" and ch.value and any(
                        t in v.strip().lower()
                        for v in ch.value.split(",")
                        for t in ("tech", "tek", "hq", "lab")):
                    return True
        return False
    is_tech = {n for n, r in buildable.items()
               if has(r, "Building") and grants_tech(r)}
    is_economy = {n for n in is_building
                  if has(actors[n], "CashTrickler", "Refinery", "SeedsResource", "LobbyScaledSeedsResource")}
    is_artillery = {n for n in has_combat
                    if n in is_mobile and ctx.max_weapon_range(actors[n]) >= 10240}
    is_combat_ground = {n for n in is_ground if n in has_combat and n not in is_harvester}
    is_combat_naval = {n for n in is_naval if n in has_combat}
    is_combat_air = {n for n in is_air if n in has_combat}
    is_cheap_fast_ground = {n for n in is_combat_ground
                            if 0 < cost(actors[n]) <= 700 and speed(actors[n]) >= 70}
    is_prosperous = {n for n in has_combat if cost(actors[n]) >= 2000}
    is_rocket_infantry = {n for n in is_infantry
                          if n in has_combat and ctx.weapon_targets_air(actors[n])}
    is_rifle_infantry = {n for n in is_infantry if n in has_combat and n not in is_rocket_infantry}
    # PowerTypes must hold dedicated power plants only: the BaseBuilder opening
    # checks CountOwned(PowerTypes) >= 1 to pass the Power1 stage. Construction
    # yards and other base hubs supply a little power too — including them lets
    # the opening skip the real plant, after which every later building fails
    # its prereq check and production stalls forever. Exclude anything that
    # itself produces on a building queue (conyards, townhalls, nexuses).
    is_power = {n for n, r in buildable.items()
                if has(r, "Building") and has(r, "Power")
                and not produces(r) & BUILDING_QUEUES
                and any((ch.value or "0").strip().lstrip("-").isdigit()
                        and int(ch.value) > 0
                        for c in r.children if c.key.split("@")[0] == "Power"
                        for ch in c.children if ch.key == "Amount")}
    is_radar = {n for n, r in buildable.items()
                if has(r, "Building") and has(r, "ProvidesRadar")}
    is_silo = {n for n, r in buildable.items()
               if has(r, "Building") and has(r, "StoresPlayerResources")}
    is_repair = {n for n, r in buildable.items()
                 if has(r, "Building") and has(r, "RepairsUnits")}
    # neutral capturable structures (oil derricks, hospitals, tech buildings)
    is_capturable_neutral = {n for n, r in actors.items()
                             if has(r, "Capturable") and has(r, "Building")
                             and "Buildable" not in tset(r)}
    is_any_transport = is_ground_transport | is_air_transport | is_landing_craft
    is_specialist = is_capture | is_engineer
    building_queue_names = {q for n in is_building for q in queues_raw(actors[n])}
    # Queues that produce non-building actors, minus meta queues that never hold
    # unit build items and minus building-queue names reused by oddball actors.
    META_QUEUES = {"Promotions", "Research", "Upgrades", "Disabled"}
    unit_queue_names = {q for n, r in buildable.items()
                        if n not in is_building
                        for q in queues_raw(actors[n])} - building_queue_names - META_QUEUES
    WATER_TERRAINS = {"Water", "River"}
    SHORE_TERRAINS = {"Beach"}

    units_to_build = {}
    for n in sorted(has_combat | is_harvester | is_mcv | is_ground_transport |
                    is_air_transport | is_landing_craft | is_capture | is_engineer |
                    is_minelayer | is_ground | is_air | is_naval):
        if n in is_building:
            continue
        units_to_build[n] = 1

    # field -> (yaml trait block, field name, id set)
    F = {}

    # ActorInfo.Name is lowercased at ruleset load (Ruleset.cs); every emitted
    # actor id must match. Non-actor string fields (terrain/queue names) use put_raw.
    def put(mod, field_name, values):
        F.setdefault(mod, {})[field_name] = sorted(v.lower() for v in values)

    def put_raw(mod, field_name, values):
        F.setdefault(mod, {})[field_name] = sorted(values)

    put("FransHarvesterBotModule", "HarvesterTypes", is_harvester)
    put("FransHarvesterBotModule", "RefineryTypes", is_refinery)
    put("FransHarvesterBotModule", "ResourceCreatorTypes", is_resource_creator)
    put("FransMineClusterBotModule", "ResourceCreatorTypes", is_resource_creator)
    put("FransStrategicMapBotModule", "ResourceCreatorTypes", is_resource_creator)

    # ResourceMapBotModule@fransbot: the sole genericbot-gated instance is
    # disabled under enable-fransbot, so FransMcvExpansionManagerBotModule's
    # Requires<ResourceMapBotModuleInfo> resolves an inert module. A named
    # second instance carries the fransbot lists; every consumer resolves
    # TraitsImplementing().FirstOrDefault(IsTraitEnabled), which is
    # multi-instance safe.
    put("ResourceMapBotModule@fransbot", "ResourceCreatorTypes", is_resource_creator)
    put("ResourceMapBotModule@fransbot", "RefineryTypes", is_refinery)
    put("ResourceMapBotModule@fransbot", "HarvesterTypes", is_harvester)
    put("ResourceMapBotModule@fransbot", "EnemyBaseBuildingTypes",
        is_conyard | is_refinery | is_producer | is_defense)
    # Derived from SeedsResource.ResourceType, unioned with the classic module's
    # curated list so map-preplaced resources with no seeding actor (SCMinerals,
    # Spice) still index as valuable.
    valuable_resources = {rt.strip() for n in is_resource_creator
                          for rt in fields(actors[n], "SeedsResource", "ResourceType")
                          + fields(actors[n], "LobbyScaledSeedsResource", "ResourceType")
                          if rt and rt.strip()}
    valuable_resources |= {"Tiberium", "BlueTiberium", "RedTiberium",
                           "GoldTiberium", "Ore", "Gems", "RA2Ore", "RA2Gems",
                           "RA2Silver", "RA2Copper", "SCMinerals", "SCGas",
                           "SCGas2", "SCGas3", "Spice", "OP2Ore", "OP2Ore2"}
    put_raw("ResourceMapBotModule@fransbot", "ValuableResourceTypes", valuable_resources)

    put("FransMcvExpansionManagerBotModule", "McvTypes", is_mcv)
    put("FransMcvExpansionManagerBotModule", "ConstructionYardTypes", is_conyard)
    put("FransMcvExpansionManagerBotModule", "McvFactoryTypes", is_conyard | is_producer)
    put("FransMcvExpansionManagerBotModule", "LandingCraftTypes", is_landing_craft)
    put("FransMcvExpansionManagerBotModule", "LandingCraftProducerTypes", is_nav_prod)
    put("FransMcvExpansionManagerBotModule", "EarlyNavalOpeningCompletionTypes", is_nav_prod)
    put("FransMcvExpansionManagerBotModule", "ExploredMapResourceObjectiveTypes",
        is_refinery | is_derrick)
    put("FransMcvExpansionManagerBotModule", "ExpansionRefineryTypes", is_refinery)
    put("FransMcvExpansionManagerBotModule", "ExistingBaseCoverageTypes", is_conyard)

    put("FransBaseBuilderBotModule", "ConstructionYardTypes", is_conyard)
    put("FransBaseBuilderBotModule", "RefineryTypes", is_refinery)
    put("FransBaseBuilderBotModule", "ProductionTypes", is_producer)
    put("FransBaseBuilderBotModule", "HarvesterTypes", is_harvester)
    put("FransBaseBuilderBotModule", "McvTypes", is_mcv)
    put("FransBaseBuilderBotModule", "TechTypes", is_tech)
    put("FransBaseBuilderBotModule", "NavalProductionTypes", is_nav_prod)
    put_raw("FransBaseBuilderBotModule", "WaterTerrainTypes", WATER_TERRAINS)
    put_raw("FransMcvExpansionManagerBotModule", "SeaShoreTerrainTypes", SHORE_TERRAINS)
    put_raw("FransStrategicMapBotModule", "BeachTerrainTypes", SHORE_TERRAINS)
    put_raw("FransSupportPowerBotModule", "DeliveryRejectedTerrainTypes", WATER_TERRAINS)
    put_raw("FransUnitBuilderBotModule", "UnitQueues", unit_queue_names)
    put_raw("FransEconomicSaturationBotModule", "ProductionQueueCategories", unit_queue_names)
    put_raw("FransEconomicSaturationBotModule", "BuildingQueueCategories", building_queue_names)
    put("FransBaseBuilderBotModule", "BarracksTypes", is_inf_prod)
    put("FransBaseBuilderBotModule", "WarFactoryTypes", is_veh_prod)
    put("FransBaseBuilderBotModule", "PowerTypes", is_power)
    put("FransBaseBuilderBotModule", "RadarTypes", is_radar)
    put("FransBaseBuilderBotModule", "SiloTypes", is_silo)
    put("FransBaseBuilderBotModule", "RepairTypes", is_repair)
    put_raw("FransBaseBuilderBotModule", "BuildingQueues", building_queue_names)
    put("FransBaseBuilderBotModule", "BuildingDelays", {})
    put("FransBaseBuilderBotModule", "BuildingLimits", {})
    put("FransBaseBuilderBotModule", "SurplusProductionBuildingTypes", is_producer)
    put("FransBaseBuilderBotModule", "SurplusAirProductionTypes", is_air_prod)
    put("FransBaseBuilderBotModule", "AdvancedTechCenterTypes", is_tech)
    put("FransBaseBuilderBotModule", "StrategicSuperweaponTypes", is_superweapon)
    put("FransBaseBuilderBotModule", "RadarEnemyTechTypes", is_tech)
    put("FransBaseBuilderBotModule", "RadarEnemyAirThreatTypes", is_combat_air)
    put("FransBaseBuilderBotModule", "RadarEnemyDefenseTypes", is_defense)
    put("FransBaseBuilderBotModule", "RadarFollowupAirProductionTypes", is_air_prod)
    put("FransBaseBuilderBotModule", "FootprintClearanceBuildingTypes", is_wall)
    put("FransBaseBuilderBotModule", "ForwardStructureTypes", is_defense)
    put("FransBaseBuilderBotModule", "NavalCapitalTechTypes", is_tech)

    put("FransDefenseCommanderBotModule", "ConstructionYardTypes", is_conyard)
    put("FransDefenseCommanderBotModule", "DefenseTypes", is_defense)
    put("FransDefenseCommanderBotModule", "GroundDefenseTypes", is_ground_defense)
    put("FransDefenseCommanderBotModule", "AntiAirDefenseTypes", is_aa_defense)
    put("FransDefenseCommanderBotModule", "WallTypes", is_wall)
    put("FransDefenseCommanderBotModule", "AirThreatTypes", is_combat_air | is_aa_aircraft)
    put("FransDefenseCommanderBotModule", "WallKeepClearBuildingTypes",
        is_refinery | is_producer | is_conyard)

    put("FransCombatIntelBotModule", "StaticGroundDefenseTypes", is_ground_defense)

    put("FransStrategicMapBotModule", "StrategicObjectiveTypes",
        is_conyard | is_superweapon | is_tech)
    put("FransStrategicMapBotModule", "PrimaryBaseTypes", is_conyard)
    put("FransStrategicMapBotModule", "RefineryTypes", is_refinery)
    put("FransStrategicMapBotModule", "VehicleProductionTypes", is_veh_prod)
    put("FransStrategicMapBotModule", "InfantryProductionTypes", is_inf_prod)
    put("FransStrategicMapBotModule", "HelicopterProductionTypes", is_air_prod)
    put("FransStrategicMapBotModule", "PlaneProductionTypes", is_air_prod)
    put("FransStrategicMapBotModule", "NavalProductionTypes", is_nav_prod)
    put("FransStrategicMapBotModule", "EnemyConstructionTypes", is_conyard | is_producer)
    put("FransStrategicMapBotModule", "EnemyEconomyTypes", is_economy | is_derrick | is_harvester)
    put("FransStrategicMapBotModule", "EnemyProductionTypes", is_producer)
    put("FransStrategicMapBotModule", "EnemyDefenseTypes", is_defense)
    put("FransStrategicMapBotModule", "EnemyStrategicTypes", is_superweapon | is_tech)

    put("FransGeneralBotModule", "RaidEligibleMobileTargetTypes",
        is_combat_ground | is_combat_air)
    put("FransGeneralBotModule", "TransportLossActorTypes",
        is_ground_transport | is_air_transport | is_landing_craft)
    put("FransGeneralBotModule", "SecureAlliedClaimStructureTypes", is_derrick | is_economy)
    put("FransGeneralBotModule", "SupportAssetTypes", is_refinery | is_conyard)
    put("FransGeneralBotModule", "CommandTargetTypes", is_conyard)
    put("FransGeneralBotModule", "SuperweaponTargetTypes", is_superweapon)
    put("FransGeneralBotModule", "EconomyTargetTypes", is_economy | is_refinery | is_derrick | is_harvester)
    put("FransGeneralBotModule", "ProductionTargetTypes", is_producer)
    put("FransGeneralBotModule", "TechTargetTypes", is_tech)

    # Ground commanders run as parallel bid capacities: each BidderKey owns one
    # committed mission, so fransbot.yaml wires six named instances
    # (@ground1..@ground6) mirroring upstream's @ground1-10 personalities file.
    # Every instance needs the same list fields — emit them per instance name.
    GROUND_COMMANDER_INSTANCES = [f"FransGroundCommanderBotModule@ground{i}"
                                  for i in range(1, 7)]
    for ground_module in GROUND_COMMANDER_INSTANCES:
        put(ground_module, "StandbyTrafficStructureTypes",
            is_refinery | is_producer)
        put(ground_module, "ExcludedGroundTypes",
            is_harvester | is_mcv | is_ground_transport)
        put(ground_module, "RaidExcludedInfantryTypes", is_capture | is_engineer)
        put(ground_module, "ReconEligibleGroundTypes", is_cheap_fast_ground)
        put(ground_module, "RaidEligibleMobileTargetTypes", is_combat_ground)
        put(ground_module, "RaidStaticDefenseBreakerTypes", is_artillery)
        put(ground_module, "RaidStaticDefenseAlwaysAllowedTypes", set())
        put(ground_module, "NavalTypes", is_naval)
        put(ground_module, "AirTypes", is_air)

    put("FransGroundTransferBotModule", "LandingCraftTypes", is_landing_craft)
    put("FransGroundTransferBotModule", "SourceBaseAnchorTypes", is_conyard)

    put("FransAirCommanderBotModule", "ManagedAircraftTypes", is_air)
    put("FransAirCommanderBotModule", "RaidEligibleMobileTargetTypes",
        is_combat_ground | is_combat_naval)
    put("FransAirCommanderBotModule", "KnownAntiAirStructureTypes", is_aa_defense)

    put("FransSeaCommanderBotModule", "ManagedNavalCombatTypes", is_combat_naval)
    put("FransSeaCommanderBotModule", "SecureShoreBombardmentTypes",
        {n for n in is_combat_naval if ctx.weapon_targets_ground(actors[n])})

    put("FransSpecOpsCommanderBotModule", "ManagedActorTypes", is_specialist)
    put("FransSpecOpsCommanderBotModule", "CapturableActorTypes", is_capturable_neutral)
    put("FransSpecOpsCommanderBotModule", "RaidTargetTypes", is_tech | is_superweapon | is_conyard)
    put("FransSpecOpsCommanderBotModule", "AutonomousNeutralCaptureTargetTypes", is_derrick)
    put("FransSpecOpsCommanderBotModule", "ConstructionYardCaptureTypes", is_conyard)
    put("FransSpecOpsCommanderBotModule", "OilDerrickTypes", is_derrick)
    put("FransSpecOpsCommanderBotModule", "DemandProductionTargetTypes", is_engineer | is_capture)
    put("FransSpecOpsCommanderBotModule", "TransportTargetTypes", is_derrick | is_tech)
    put("FransSpecOpsCommanderBotModule", "StrategicSecurityTargetTypes", is_superweapon | is_tech)

    put("FransSupplyTruckBotModule", "SupplyTruckTypes", set())
    put("FransSupplyTruckBotModule", "DeliveryTargetTypes", is_refinery)

    put("FransSupportPowerBotModule", "NukeIntelPriorityStructureTypes",
        is_superweapon | is_tech | is_conyard)

    put("FransTransportCommanderBotModule", "PassengerTypes", is_passenger)
    put("FransTransportCommanderBotModule", "AirTransportTypes", is_air_transport)
    put("FransTransportCommanderBotModule", "GroundTransportTypes", is_ground_transport)
    put("FransTransportCommanderBotModule", "LandingCraftTypes", is_landing_craft)

    put("FransTransportCommanderBotModule", "PreferredTransportTypes", is_any_transport)
    put("FransTransportCommanderBotModule", "ReusablePreferredTransportTypes", is_any_transport)

    put("FransMinelayerBotModule", "FriendlyBaseStructureTypes", is_building)
    put("FransMinelayerBotModule", "MinelayingActorTypes", is_minelayer)
    put("FransMinelayerBotModule", "AircraftPriorityRepairActorTypes", is_air)

    put("FransCommanderCoreBotModule", "ReconActorOpportunityCostPercent", {})

    put("FransRiskModelBotModule", "AircraftSoftAntiAirThreatTypes",
        is_aa_aircraft | is_aa_defense)

    put("FransUnitBuilderBotModule", "UnitsToBuild", units_to_build)
    put("FransUnitBuilderBotModule", "UnitLimits", {})
    put("FransUnitBuilderBotModule", "UnitDelays", {})
    put("FransUnitBuilderBotModule", "OpeningLightVehicleTypes", is_cheap_fast_ground - is_infantry)
    put("FransUnitBuilderBotModule", "HardDisabledUnitTypes", set())
    # Delay-until-opening-MCV is for units the opening should not buy early
    # (upstream: the mobile AA vehicle ftrk). MCVs must never appear here —
    # the gate keys on OpeningMcvCompleted, so an MCV in the list self-deadlocks.
    is_aa_vehicle = {n for n in is_combat_ground
                     if n not in is_infantry and n not in is_mcv and n not in is_harvester
                     and ctx.weapon_targets_air(actors[n])}
    put("FransUnitBuilderBotModule", "DelayUntilOpeningMcvCompletedUnitTypes", is_aa_vehicle)
    put("FransUnitBuilderBotModule", "OpeningCaptureSpecialistTypes", is_capture)
    put("FransUnitBuilderBotModule", "OpeningRifleTypes", is_rifle_infantry)
    put("FransUnitBuilderBotModule", "OpeningRocketTypes", is_rocket_infantry)
    put("FransUnitBuilderBotModule", "PreferredVehicleProducerTypes", is_veh_prod)
    put("FransUnitBuilderBotModule", "MultiFactoryGatedVehicleTypes", set())
    put("FransUnitBuilderBotModule", "PreferredInfantryProducerTypes", is_inf_prod)
    put("FransUnitBuilderBotModule", "PriorityRequestedUnitTypes", is_capture | is_engineer | is_mcv)
    put("FransUnitBuilderBotModule", "HarvesterTypes", is_harvester)
    put("FransUnitBuilderBotModule", "ResourceControlStructureTypes", is_refinery | is_derrick)
    put("FransUnitBuilderBotModule", "AirFixedWingPrimaryTypes",
        {n for n in is_fixed if n in has_combat})
    put("FransUnitBuilderBotModule", "AirFixedWingSecondaryTypes", set())
    put("FransUnitBuilderBotModule", "AirRotaryWingPrimaryTypes",
        {n for n in is_vtol if n in has_combat})
    put("FransUnitBuilderBotModule", "AirRotaryWingSecondaryTypes", is_air_transport & is_vtol)
    put("FransUnitBuilderBotModule", "AlliedSeaCombatTypes", is_combat_naval)
    put("FransUnitBuilderBotModule", "SovietSeaCombatTypes", is_combat_naval)
    put("FransUnitBuilderBotModule", "ProsperousUnitTypes", is_prosperous)
    put("FransUnitBuilderBotModule", "GroundVehicleArtilleryTypes", is_artillery)
    put("FransUnitBuilderBotModule", "IntelGatedMinelayerTypes", is_minelayer)

    # miniyaml csv sets parse as one comma-separated value under the field key.
    lines = ["# GENERATED by tools/ai/gen_fransbot_lists.py — do not hand-edit.",
             "# Union actor-id lists derived from traits across the resolved ruleset;",
             "# see the module [ActorReference] fields in OpenRA.Mods.Fransbot/Traits/.",
             "Player:"]
    for mod in sorted(F):
        lines.append(f"\t{mod}:")
        for fname in sorted(F[mod]):
            vals = F[mod][fname]
            if fname in ("UnitsToBuild", "UnitLimits", "UnitDelays",
                         "BuildingDelays", "BuildingLimits",
                         "ReconActorOpportunityCostPercent"):
                # FrozenDictionary: child nodes, one "id: weight" per line.
                if vals:
                    lines.append(f"\t\t{fname}:")
                    lines.extend(f"\t\t\t{v}: 1" for v in vals)
                else:
                    lines.append(f"\t\t{fname}:")
            else:
                lines.append(f"\t\t{fname}: " + ", ".join(vals) if vals else f"\t\t{fname}:")
    text = "\n".join(lines) + "\n"

    if args.check:
        existing = OUT.read_text(encoding="utf8") if OUT.exists() else ""
        if existing == text:
            print("fransbot_lists.yaml: UP TO DATE")
            return 0
        print("fransbot_lists.yaml: STALE — rerun tools/ai/gen_fransbot_lists.py")
        return 1

    OUT.write_text(text, encoding="utf8")
    total = sum(len(v) for m in F.values() for v in m.values())
    print(f"wrote {OUT.relative_to(ROOT)}: {total} ids across {sum(len(m) for m in F.values())} fields")
    for mod in sorted(F):
        for fname in sorted(F[mod]):
            print(f"  {mod}.{fname}: {len(F[mod][fname])}")
    return 0


def _chunks(seq, n):
    for i in range(0, len(seq), n):
        yield seq[i:i + n]


if __name__ == "__main__":
    sys.exit(main())
