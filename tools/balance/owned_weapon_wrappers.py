"""Exact transparent identities, only for frozen converter closure checks.

Raw structure/sharing audits must keep counting these concrete definitions.
Unlisted wrappers and any modified wrapper are never excluded.
"""

IDENTITY_WRAPPERS = {
    "td_gdi_grenadier_grenade": "Grenade",
    "td_gdi_rocketsoldier_rockets": "Rockets",
    "td_gdi_rocketsoldier_rocketsamt": "RocketsAMT",
    "td_gdi_apc_apcgun": "APCGun",
    "td_gdi_battletank_120mm": "120mm",
    "td_gdi_mlrs_227mm": "227mm",
    "td_gdi_assaultapc_machinegunhumvee2": "MachineGunHumvee2",
    "td_gdi_assaultapc_machinegunhumvee2_AA": "MachineGunHumvee2_AA",
    "td_gdi_assaultapc_machinegunhumvee2ap": "MachineGunHumvee2AP",
    "td_gdi_assaultapc_machinegunhumvee2ap_AA": "MachineGunHumvee2AP_AA",
    "td_gdi_humveemkii_machinegunhumvee2": "MachineGunHumvee2",
    "td_gdi_humveemkii_machinegunhumvee2ap": "MachineGunHumvee2AP",
    "td_gdi_humveemkii_machinegunhumvee2_AA": "MachineGunHumvee2_AA",
    "td_gdi_humveemkii_machinegunhumvee2ap_AA": "MachineGunHumvee2AP_AA",
    "td_gdi_missileboat_depthcharge": "DepthCharge",
    "td_nod_samsite_dragon": "Dragon",
    "td_nod_rocketsoldier_rockets": "Rockets",
    "td_nod_flamethrower_flamethrower": "Flamethrower",
    "td_nod_chemicalwarrior_chemspray": "Chemspray",
    "td_nod_commando_td_gdi_commando_sniper": "td_gdi_commando_sniper",
    "td_nod_artillery_artilleryshell": "ArtilleryShell",
    "td_nod_flametank_bigflamer": "BigFlamer",
    "td_nod_buggy_machinegun": "MachineGun",
    "td_nod_ssmlauncher_honestjohn": "HonestJohn",
    "td_nod_ballisticmissilesubmarine_honestjohn": "HonestJohn",
    "ra1_allies_alliedrocketsoldier_rocketsra": "RocketsRA",
    "ra1_allies_cargoplanebomber_parabomb": "ParaBomb",
    "ra1_allies_gunboat_depthcharge": "DepthCharge",
    "ra1_allies_gunboat_depthchargecryo": "DepthChargeCryo",
    "ra1_allies_destroyer_depthcharge": "DepthCharge",
    "ra1_allies_destroyer_depthchargecryo": "DepthChargeCryo",
    "ra1_allies_cruiser_8inch": "8Inch",
    "ra1_soviets_missilesubmarine_227mm": "227mm",
    "ra1_soviets_hindattackhelicopter_hindmissiles": "HindMissiles",
    "ra1_soviets_hindattackhelicopter_chaingun": "ChainGun",
    "ra1_soviets_hindattackhelicopter_incendiarychaingun": "IncendiaryChainGun",
    "ra1_soviets_kamovattackhelicopter_hindmissiles": "HindMissiles",
    "ra1_soviets_kamovattackhelicopter_chaingun": "ChainGun",
    "ra1_soviets_kamovattackhelicopter_incendiarychaingun": "IncendiaryChainGun",
    "ra1_soviets_supersonicnuclearbomber_parabombnuke": "ParaBombNuke",
    "ra1_soviets_teslacoil_teslazap": "TeslaZap",
    "ra1_soviets_rocketsoldier_rocketsra": "RocketsRA",
    "ra1_soviets_dragunovantimaterialsniper_dragunovsniper": "DragunovSniper",
    "ra1_soviets_shocktrooper_portatesla": "PortaTesla",
    "ra1_soviets_v2rocketlauncher_scud": "SCUD",
    "ra1_soviets_heavytank_105mm": "105mm",
    "ra1_soviets_gorynychtank_bigflamer": "BigFlamer",
    "ra1_soviets_mammothtank_ra120mm": "ra120mm",
    "ra1_soviets_mammothtank_ra120mmthermobaric": "ra120mmThermobaric",
    "ra1_soviets_mammothtank_mammothtusk": "MammothTusk",
    "ra1_soviets_mammothtank_mammothtusktesla": "MammothTuskTesla",
    "ra1_soviets_mammothtank_mammothtuskthermobaric": "MammothTuskThermobaric",
    "ra1_soviets_teslatank_ttankzap": "TTankZap",
    "ra1_allies_alliedsniper_lightsniper": "LightSniper",
    "ra1_allies_alliedlighttank_25mm": "25mm",
    "ra1_allies_alliedartillery_155mm": "155mm",
    "ra1_allies_alliedartillery_155mmcryo": "155mmCryo"
}


def is_reviewed_owner_wrapper(rules, name):
    parent = IDENTITY_WRAPPERS.get(name)
    if parent is None:
        return False
    node = rules.weapons.get(name)
    if node is None or node.value or len(node.children) != 1:
        return False
    child = node.children[0]
    return child.key == 'Inherits' and child.value == parent and not child.children
