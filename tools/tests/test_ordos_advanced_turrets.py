"""Focused contracts for the active Ordos laser and chemical defense turrets."""

from pathlib import Path
import hashlib
import struct
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools/audit"))
from miniyaml import Ruleset


TURRETS = ("ordos_laserturret", "ordos_chemturret")
ORDOS = ROOT / "mods/cameo/ContentPacks/D2k/Ordos"
WEAPONS_TEXT = (ORDOS / "yaml/weapons.yaml").read_text(encoding="utf-8")
SEQUENCES_TEXT = (ORDOS / "yaml/sequences.yaml").read_text(encoding="utf-8")

ICON_PINS = {
    "ordos_chemtur_build_icon.png": "0f0a17e59fa181ba0922241bf4c2c934cbb9e4ba88e549f39c42060e3438d815",
    "ordos_lasertur_build_icon.png": "e2f8694fd6377ff223ca0d56af6d294546e14c585b3b97340e54c0b6592e9df1",
}

AUDIO_PINS = {
    "ChemTurretAttack.wav": "9206203411377dd43df81dac61f61ff5fb241b13defd46020154d0c45a0e4559",
    "PopupTurretAttack.wav": "eb0927c6c349c6b19526c9a835c8d65bc00b035447523f6ecd8dbf10c2efc1c1",
}


def csv(value):
    return {item.strip() for item in (value or "").split(",") if item.strip()}


def sequence_block(name):
    marker = f"\n{name}:\n"
    start = SEQUENCES_TEXT.index(marker) + 1
    end = SEQUENCES_TEXT.find("\n\n", start)
    return SEQUENCES_TEXT[start:] if end < 0 else SEQUENCES_TEXT[start:end]


def png_size(path):
    payload = path.read_bytes()
    if payload[:8] != b"\x89PNG\r\n\x1a\n" or payload[12:16] != b"IHDR":
        raise AssertionError(f"{path} is not a PNG with an IHDR header")
    return struct.unpack(">II", payload[16:24])


class OrdosAdvancedTurretTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rules = Ruleset(ROOT)

    def test_active_pack_and_buildability_contract(self):
        mod = (ROOT / "mods/cameo/mod.yaml").read_text(encoding="utf-8")
        content = (ORDOS / "content.yaml").read_text(encoding="utf-8")
        self.assertIn("Include: ContentPacks/D2k/Ordos/content.yaml", mod)
        self.assertIn("ContentPacks|D2k/Ordos/yaml/buildings.yaml", content)
        self.assertIn("ContentPacks|D2k/Ordos/yaml/weapons.yaml", content)
        self.assertIn("ContentPacks|D2k/Ordos/yaml/sequences.yaml", content)

        expected_prerequisites = {
            "ordos_laserturret": "~ordos_constructionyard, ordos_ixresearchcenter",
            "ordos_chemturret": "~ordos_constructionyard, ordos_barracks",
        }
        expected_muzzle_offsets = {
            "ordos_laserturret": "540,0,194",
            "ordos_chemturret": "540,0,450",
        }
        for name in TURRETS:
            with self.subTest(actor=name):
                actor = self.rules.resolve(name)
                buildable = actor.child("Buildable")
                self.assertEqual("ordos", buildable.get("Factions"))
                self.assertEqual("Defence, RADefence", buildable.get("Queue"))
                self.assertEqual(expected_prerequisites[name], buildable.get("Prerequisites"))
                armament = actor.child("Armament")
                self.assertEqual(name, armament.get("Weapon"))
                self.assertEqual(expected_muzzle_offsets[name], armament.get("LocalOffset"))

    def test_sequences_assets_and_construction_gating(self):
        for name, image, icon in (
            ("ordos_laserturret", "ordos_lasertur.png", "ordos_lasertur_build_icon.png"),
            ("ordos_chemturret", "ordos_chemtur.png", "ordos_chemtur_build_icon.png"),
        ):
            with self.subTest(actor=name):
                actor = self.rules.resolve(name)
                self.assertEqual("build-incomplete", actor.child("WithMakeAnimation").get("Condition"))
                self.assertEqual("!build-incomplete", actor.child("WithSpriteTurret").get("RequiresCondition"))
                self.assertEqual("!build-incomplete", actor.child("AttackTurreted").get("RequiresCondition"))
                block = sequence_block(name)
                self.assertIn(f"Filename: {image}", block)
                self.assertIn(f"Filename: {icon}", block)
                sequence = self.rules.sequence_image(name)
                self.assertEqual("0.9", sequence.child("Defaults").get("Scale"))
                self.assertEqual("-2,0", sequence.child("Defaults").get("Offset"))
                self.assertEqual("1", sequence.child("icon").get("Scale"))
                self.assertEqual("0,0", sequence.child("icon").get("Offset"))
                self.assertIn("make:\n\t\tFilename: " + image + "\n\t\tStart: 0\n\t\tLength: 16", block)
                self.assertIn("turret:\n\t\tFilename: " + image + "\n\t\tStart: 16\n\t\tFacings: 64", block)
                self.assertTrue((ROOT / "mods/cameo/bits/d2k" / image).is_file())
                icon_path = ROOT / "mods/cameo/bits/d2k" / icon
                self.assertTrue(icon_path.is_file())
                self.assertEqual((64, 48), png_size(icon_path))
                self.assertEqual(ICON_PINS[icon], hashlib.sha256(icon_path.read_bytes()).hexdigest())

    def test_laser_weapon_and_actor_remain_unchanged(self):
        actor = self.rules.resolve("ordos_laserturret")
        weapon = self.rules.resolve_weapon("ordos_laserturret")
        self.assertEqual("7710", actor.get("RevealsShroud", "Range"))
        self.assertEqual("3855", actor.get("DetectCloaked", "Range"))
        self.assertEqual("-55", actor.get("Power", "Amount"))
        self.assertEqual("55", weapon.get("ReloadDelay"))
        self.assertEqual("3", weapon.get("Burst"))
        self.assertEqual("5", weapon.get("BurstDelays"))
        self.assertEqual("7275", weapon.get("Range"))
        self.assertEqual("PopupTurretAttack.wav", weapon.get("Report"))
        self.assertEqual("LaserZap", weapon.get("Projectile"))
        self.assertEqual("55", weapon.get("Projectile", "Width"))
        self.assertEqual("2047", weapon.get("Projectile", "ZOffset"))
        self.assertEqual("00ffbb", weapon.get("Projectile", "Color"))
        laser = weapon.child("Warhead@Laser_Heavy")
        self.assertEqual("10000", laser.get("Damage"))
        self.assertEqual("Prone75Percent, TriggerProne, ElectricityDeath", laser.get("DamageTypes"))

    def test_chemical_actor_tooltip_is_playtest_copy(self):
        actor = self.rules.resolve("ordos_chemturret")
        tooltip = actor.child("Tooltip")
        self.assertEqual("actor_ordos_chemturret.name", tooltip.get("Name"))
        self.assertEqual("actor_ordos_chemturret.description", actor.get("Buildable", "Description"))

    def test_chemical_resolves_to_bounded_toxic_behavior(self):
        for inherit in (
            "Inherits@wh: ^Warhead_Toxic_AntiInfantryDefense",
            "Inherits@proj: ^Projectile_Shell_Light",
            "Inherits@fx: ^Effect_Chem_Light",
        ):
            self.assertIn(inherit, WEAPONS_TEXT)
        chemical_source = WEAPONS_TEXT[WEAPONS_TEXT.index("ordos_chemturret:"):]
        chemical_source = chemical_source.split("\n\n", 1)[0]
        self.assertNotIn("Warhead@CannonChem_Medium:", chemical_source)
        self.assertNotIn("Warhead@EffectWater:", chemical_source)
        self.assertNotIn("Warhead@Concrete:", chemical_source)
        self.assertNotIn("Warhead@Cloud:", chemical_source)
        self.assertNotIn("RA2CloudSafe", chemical_source)
        self.assertNotIn("D2K_MortarChem", WEAPONS_TEXT)

        weapon = self.rules.resolve_weapon("ordos_chemturret")
        self.assertEqual("90", weapon.get("ReloadDelay"))
        self.assertEqual("14000", weapon.get("Range"))
        self.assertEqual("1985", weapon.get("MinRange"))
        self.assertEqual("ChemTurretAttack.wav", weapon.get("Report"))
        self.assertEqual("true", weapon.get("TargetActorCenter"))
        self.assertEqual("Ground", weapon.get("ValidTargets"))

        projectile = weapon.child("Projectile")
        for key, expected in {
            "Speed": "175",
            "Inaccuracy": "75",
            "LaunchAngle": "125",
            "ContrailLength": "30",
            "ContrailStartWidth": "60",
            "ContrailEndWidth": "15",
            "ContrailStartColor": "FEDCBA98",
            "ContrailEndColor": "87654321",
            "InaccuracyType": "PerCellIncrement",
            "Image": "d2k_155mm",
            "Palette": "effect",
        }.items():
            with self.subTest(projectile_field=key):
                self.assertEqual(expected, projectile.get(key))

        chemical = weapon.child("Warhead@Toxic_Light")
        self.assertEqual("AreaDamage", chemical.get())
        self.assertEqual("20000", chemical.get("Damage"))
        self.assertEqual("0", chemical.get("PercentageScale"))
        self.assertEqual("Prone75Percent, TriggerProne, ToxicDeath", chemical.get("DamageTypes"))
        self.assertEqual("Ground, Water", chemical.get("ValidTargets"))
        self.assertEqual("wall, Mine, ToxinImmune", weapon.get("InvalidTargets"))
        self.assertEqual("wall, Mine, ToxinImmune", chemical.get("InvalidTargets"))
        self.assertEqual("1536", chemical.get("Spread"))
        for armor, expected in {
            "None": "200",
            "Flak": "159",
            "Scout": "100",
            "Light": "40",
            "Medium": "20",
            "Heavy": "20",
            "Superheavy": "20",
        }.items():
            with self.subTest(armor=armor):
                self.assertEqual(expected, chemical.get("Versus", armor))

        center_damage = {
            armor: int(chemical.get("Damage")) * int(chemical.get("Versus", armor)) // 100
            for armor in ("None", "Flak", "Scout", "Light", "Medium", "Heavy", "Superheavy")
        }
        self.assertEqual(
            {"None": 40000, "Flak": 31800, "Scout": 20000, "Light": 8000, "Medium": 4000,
             "Heavy": 4000, "Superheavy": 4000},
            center_damage,
        )
        for armor in ("Medium", "Heavy", "Superheavy"):
            self.assertEqual(center_damage["None"] // 10, center_damage[armor])
        self.assertEqual(center_damage["None"] // 2, center_damage["Scout"])
        self.assertEqual(center_damage["None"] // 5, center_damage["Light"])
        self.assertIsNone(chemical.get("PhysicalStates", "Corrosion"))
        self.assertFalse(any("Corrosion" in child.key for child in weapon.children))

        effect = weapon.child("Warhead@Effect")
        self.assertEqual("d2k_toxic_large_explosion", effect.get("Explosions"))
        self.assertEqual("EXPLMD2.WAV", effect.get("ImpactSounds"))
        self.assertEqual("d2k_toxic_explosion", effect.get("ExplosionPalette"))
        self.assertEqual("Ground, Ship", effect.get("ValidTargets"))
        self.assertEqual("false", effect.get("ImpactActors"))
        self.assertIsNone(effect.get("Delay"))
        self.assertIsNone(effect.get("Weapon"))

        misc_sequences = (ROOT / "mods/cameo/sequences/misc.yaml").read_text(encoding="utf-8")
        self.assertIn(
            "\td2k_toxic_large_explosion:\n"
            "\t\tFilename: data.r8\n"
            "\t\tScale: 2\n"
            "\t\tStart: 4241\n"
            "\t\tLength: 22\n"
            "\t\tBlendMode: Additive\n"
            "\t\tTick: 80",
            misc_sequences,
        )

        toxic_palette = ROOT / "mods/cameo/bits/d2k/d2k_toxic_explosion.pal"
        palette_bytes = toxic_palette.read_bytes()
        self.assertEqual(768, len(palette_bytes))
        self.assertEqual(
            "046724ae18607b2d87be8bfe98c6765eea9dc5563d5c40d14fe5453d7cdad065",
            hashlib.sha256(palette_bytes).hexdigest(),
        )
        colors = [palette_bytes[i:i + 3] for i in range(0, len(palette_bytes), 3)]
        self.assertTrue(all(g >= r and g >= b for r, g, b in colors))

        for filename, expected_hash in AUDIO_PINS.items():
            with self.subTest(audio=filename):
                path = ROOT / "mods/cameo/bits/d2k" / filename
                payload = path.read_bytes()
                self.assertEqual(b"RIFF", payload[:4])
                self.assertEqual(b"WAVE", payload[8:12])
                self.assertEqual(expected_hash, hashlib.sha256(payload).hexdigest())

        infantry = self.rules.resolve("ordos_lightinfantry")
        toxic_deaths = infantry.child("WithDeathAnimation@effect").child("DeathTypes")
        self.assertEqual("6", toxic_deaths.get("ToxicDeath"))
        poisoned_sounds = csv(infantry.get("DeathSounds@POISONED", "DeathTypes"))
        self.assertIn("ToxicDeath", poisoned_sounds)
        virus_explosion = infantry.child("FireWarheadsOnDeath@Virus")
        self.assertEqual("RA2VirusDeath", virus_explosion.get("DeathTypes"))
        self.assertNotIn("ToxicDeath", csv(virus_explosion.get("DeathTypes")))

    def test_chemical_actor_closes_sight_detection_and_power(self):
        actor = self.rules.resolve("ordos_chemturret")
        self.assertEqual("14000", actor.get("RevealsShroud", "Range"))
        self.assertEqual("7000", actor.get("DetectCloaked", "Range"))
        self.assertEqual("-60", actor.get("Power", "Amount"))

    def test_global_ai_membership_and_preserved_ordos_defense_fraction(self):
        player = self.rules.resolve("Player")
        resource = player.child("ResourceMapBotModule")
        builder = player.child("BaseBuilderBotModuleCA@generic")
        for field in ("EnemyBaseBuildingTypes", "DefenseTypes"):
            values = csv(resource.get(field) if field == "EnemyBaseBuildingTypes" else builder.get(field))
            self.assertIn("ordos_laserturret", values)
            self.assertIn("ordos_chemturret", values)
        self.assertIn("ordos_laserturret", csv(builder.get("AntiAirTypes")))

        fractions = builder.child("BuildingFractions")
        defense = {
            name: int(fractions.child(name).get())
            for name in ("ordos_autogunturret", "ordos_artilleryplatform", "ordos_laserturret", "ordos_chemturret")
        }
        self.assertEqual(60, sum(defense.values()))
        self.assertEqual({"ordos_autogunturret": 25, "ordos_artilleryplatform": 15,
                          "ordos_laserturret": 10, "ordos_chemturret": 10}, defense)


if __name__ == "__main__":
    unittest.main()
