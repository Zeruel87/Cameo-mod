"""Exact, test-only reconciliation of independently reviewed upstream changes.

Never used by a converter. Assert modern values, reverse only the enumerated
delta in a copy, then let the ORIGINAL historical fingerprints check everything
else, including child order. No live data or stored fingerprints are rewritten.
"""
from miniyaml import Node

# e1ab9bb26 removed duplicate singular bindings; the map already applies100.
CORROSION_CLEANUP = {
    "AsianChemical": ("LightChemicalWeaponPercentage", "MediumChemicalWeaponPercentage", "HeavyChemicalWeaponPercentage"),
    "AsianHarbingerPlasma": ("LightChemicalWeaponPercentage", "MediumChemicalWeaponPercentage"),
    "FutureMechPlasma": ("MediumChemicalWeaponPercentage",),
    "SpecterArtilleryShellUpgrade": ("MediumChemicalWeaponPercentage",),
    "SteelQuantumTurretRail": ("HeavyChemicalWeaponPercentage",),
    "WyvernRockets": ("MediumChemicalWeaponPercentage",),
    "PhobosLaser": ("HeavyChemicalWeaponPercentage",),
    "FutureMechPlasma_elite": ("MediumChemicalWeaponPercentage",),
    "AsianChemical_elite": ("LightChemicalWeaponPercentage", "MediumChemicalWeaponPercentage", "HeavyChemicalWeaponPercentage"),
    "SteelQuantumTurretRail_EMP": ("HeavyChemicalWeaponPercentage",),
}

# path, historical value, authored current value. b905d7679 regenerated coupling
# columns; a92ae850f removed LatinSmoker's trailing medium-cannon inheritance.
FIELD_CHANGES = {
    "AAGunBoatFlak": (
        (("Warhead@Flak_Medium", "Versus", "BLAST"), "58", "57"),
        (("Warhead@Flak_Medium", "Versus", "Shield"), "171", "172"),
    ),
    "AAGunBoatFlak_elite": (
        (("Warhead@Flak_Medium", "Versus", "BLAST"), "58", "57"),
        (("Warhead@Flak_Medium", "Versus", "Shield"), "171", "172"),
    ),
    "RA2FlakTrackAAGun": (
        (("Warhead@Flak_Medium", "Versus", "BLAST"), "58", "57"),
        (("Warhead@Flak_Medium", "Versus", "Shield"), "171", "172"),
    ),
    "RA2FlakTrackAAGun_elite": (
        (("Warhead@Flak_Medium", "Versus", "BLAST"), "58", "57"),
        (("Warhead@Flak_Medium", "Versus", "Shield"), "171", "172"),
    ),
    "RA2FlakTrackGun": (
        (("Warhead@Flak_Medium", "Versus", "BLAST"), "58", "57"),
        (("Warhead@Flak_Medium", "Versus", "Shield"), "171", "172"),
    ),
    "TeslaArmorDischargeArc": (
        (("Warhead@MissileAP_Light", "Versus", "COMPOSITE"), "44", "45"),
    ),
    "TeslaArmorDischargeFragment1": (
        (("Warhead@MissileAP_Light", "Versus", "COMPOSITE"), "44", "45"),
    ),
    "TeslaArmorDischargeFragment2": (
        (("Warhead@MissileAP_Light", "Versus", "COMPOSITE"), "44", "45"),
    ),
    "GrenadeRA": (
        (("Warhead@Demolition_Light", "Versus", "COMPOSITE"), "101", "102"),
    ),
    "ASDFKamikazeExplosion": (
        (("Warhead@Demolition_Heavy", "Versus", "COMPOSITE"), "101", "102"),
        (("Warhead@Demolition_Heavy", "Versus", "Shield"), "177", "178"),
    ),
    "AsianHowitzerCannon": (
        (("Warhead@CannonHE_Heavy", "Versus", "BLAST"), "40", "39"),
        (("Warhead@CannonHE_Heavy", "Versus", "COMPOSITE"), "99", "100"),
        (("Warhead@CannonHE_Heavy", "Versus", "Shield"), "168", "169"),
    ),
    "AsianHowitzerCannon_elite": (
        (("Warhead@CannonHE_Heavy", "Versus", "BLAST"), "40", "39"),
        (("Warhead@CannonHE_Heavy", "Versus", "COMPOSITE"), "99", "100"),
        (("Warhead@CannonHE_Heavy", "Versus", "Shield"), "168", "169"),
    ),
    "ConscriptMolotov": (
        (("Warhead@Flame_Light", "Versus", "COMPOSITE"), "76", "77"),
        (("Warhead@Flame_Light", "Versus", "Shield"), "205", "208"),
    ),
    "TSBusMortar": (
        (("Warhead@Concussion_Medium", "Versus", "COMPOSITE"), "106", "107"),
    ),
    "tkm_trooper_gp25": (
        (("Warhead@Demolition_Light", "Versus", "COMPOSITE"), "101", "102"),
    ),
    "RA2FreedomRocket": (
        (("Warhead@MissileAP_Medium", "Versus", "COMPOSITE"), "44", "45"),
    ),
    "RA2FreedomRocket_elite": (
        (("Warhead@MissileAP_Medium", "Versus", "COMPOSITE"), "44", "45"),
    ),
    "PositronBounce1": (
        (("Warhead@CannonHE_Medium", "Versus", "BLAST"), "40", "39"),
        (("Warhead@CannonHE_Medium", "Versus", "COMPOSITE"), "99", "100"),
    ),
    "PositronBounce2": (
        (("Warhead@CannonHE_Medium", "Versus", "BLAST"), "40", "39"),
        (("Warhead@CannonHE_Medium", "Versus", "COMPOSITE"), "99", "100"),
    ),
    "TS155mm_bluenuke": (
        (("Warhead@Concussion_Medium", "Versus", "COMPOSITE"), "106", "107"),
        (("Warhead@Demolition_Heavy", "Versus", "COMPOSITE"), "101", "102"),
        (("Warhead@Demolition_Heavy", "Versus", "Shield"), "177", "178"),
    ),
    "RA2KirovHowitzerSplash": (
        (("Warhead@Concussion_Medium", "Versus", "COMPOSITE"), "106", "107"),
    ),
    "LatinSmokerCannon": (
        (("Warhead@Concrete", "Damage"), "150", "200"),
        (("Warhead@Effect", "Explosions"), "ra2_medium_explosion", "ra2_large_grey_explosion"),
        (("Warhead@Effect", "ImpactSounds"), "gexp14a.wav", "kaboom15.aud"),
        (("Warhead@EffectAir", "Explosions"), "med_explosion_air", "big_explosion_air"),
        (("Warhead@Glow", "FadeFrames"), "10", "15"),
        (("Warhead@Glow", "Scale"), "0.55", "0.8"),
        (("Warhead@ShieldHit", "Duration"), "10", "12"),
    ),
}


def historical_copy(test, node):
    copy = node.deep_copy()
    if node.key == "TSPulseCannon_EMP":
        # 9bfee2b85 removed an unused field from AffectsIntegrity, not damage.
        warhead = copy.child("Warhead@2Con")
        test.assertEqual("AffectsIntegrity", warhead.value)
        test.assertIsNone(warhead.child("Falloff"))
        test.assertEqual("ValidTargets", warhead.children[0].key)
        test.assertEqual("Damage", warhead.children[1].key)
        warhead.children.insert(1, Node("Falloff", "100, 75, 50, 25"))
    for tag in CORROSION_CLEANUP.get(node.key, ()):
        warhead = copy.child("Warhead@" + tag)
        test.assertIsNotNone(warhead, (node.key, tag))
        test.assertEqual(8, len(warhead.children), (node.key, tag))
        test.assertEqual("PhysicalStates", warhead.children[7].key, (node.key, tag))
        test.assertEqual("100", warhead.child("PhysicalStates").get("Corrosion"))
        test.assertIsNone(warhead.child("PhysicalStateName"))
        test.assertIsNone(warhead.child("PhysicalStateScale"))
        warhead.children.extend([Node("PhysicalStateName", "Corrosion"), Node("PhysicalStateScale", "100")])
    for path, before, after in FIELD_CHANGES.get(node.key, ()):
        field = copy
        for key in path:
            field = field.child(key)
            test.assertIsNotNone(field, (node.key, path))
        test.assertEqual(after, field.value, (node.key, path))
        field.value = before
    return copy


class HistoricalView:
    def __init__(self, test, rules):
        self.test, self.rules = test, rules

    def __getattr__(self, key):
        return getattr(self.rules, key)

    def resolve_weapon(self, name):
        return historical_copy(self.test, self.rules.resolve_weapon(name))
