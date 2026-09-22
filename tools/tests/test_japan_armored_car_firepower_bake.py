"""Exact regression coverage for the Armored Car's retired 10% modifier."""

from fractions import Fraction
import hashlib
import json
import pathlib
import sys
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / "tools/audit"), str(ROOT / "tools/balance")]
from miniyaml import Ruleset  # noqa: E402
from percentage_damage import folded_units  # noqa: E402


WEAPONS = (
    "ArmoredCarMG",
    "ArmoredCarMG_AA",
    "ArmoredCarMGWaveforce",
    "ArmoredCarMGAAWaveforce",
)

# Hashes from the resolved pre-bake weapons after removing only Damage and
# PercentageDenominator.  They pin targeting, cadence, projectile behavior,
# versus tables, effects, and every other runtime field across the conversion.
NON_DAMAGE_HASHES = {
    "ArmoredCarMG": "2ac64328ab07b7d2857a0afbb8ba9c35439843757080805b160363ef8387f300",
    "ArmoredCarMG_AA": "7bbcd204e322665260b79004a41b4d11121a62db6ef9193ef820c7f6c97c61ca",
    "ArmoredCarMGWaveforce": "97504ca666924a3a4b6a43a624563e65d647cfd35526eb6412e68ed0f8c9d3d8",
    "ArmoredCarMGAAWaveforce": "87ae9104584945c869e25c655b68ab8a7412d4aac37a334d81616b240bcabe73",
}

OLD_FLAT_DAMAGE = {
    "Bullet_Medium": 16000,
    "Railgun_Heavy": 3000,
    "Railgun_Heavy_ExtraDamage": 1000,
}


def child(node, key):
    return next((item for item in node.children if item.key == key), None)


def non_damage_payload(node):
    payload = {"key": node.key, "value": node.value, "children": []}
    for item in node.children:
        if node.value in {
            "AreaDamage", "SpreadDamage", "TargetDamage", "AreaDamagePercentage"
        } and item.key in {"Damage", "PercentageDenominator"}:
            continue
        payload["children"].append(non_damage_payload(item))
    return payload


class JapanArmoredCarFirepowerBakeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rules = Ruleset(ROOT)

    def test_actor_keeps_only_the_conditional_waveforce_multiplier(self):
        actor = self.rules.resolve("japan_armoredcar")
        multipliers = [c for c in actor.children if c.key.startswith("FirepowerMultiplier")]
        self.assertFalse(any(c.get("RequiresCondition") is None for c in multipliers))
        waveforce = child(actor, "FirepowerMultiplier@japan_upgrade_waveforcebullets")
        self.assertEqual("125", waveforce.get("Modifier"))
        self.assertEqual("japan_upgrade_waveforcebullets", waveforce.get("RequiresCondition"))

    def test_all_damage_channels_encode_the_old_runtime_times_ten_percent(self):
        for weapon_name in WEAPONS:
            with self.subTest(weapon=weapon_name):
                weapon = self.rules.resolve_weapon(weapon_name)
                positives = [c for c in weapon.children
                             if c.key.startswith("Warhead") and int(c.get("Damage") or 0) > 0]
                for warhead in positives:
                    tag = warhead.key.split("@", 1)[-1]
                    if warhead.value in {"AreaDamage", "SpreadDamage", "TargetDamage"}:
                        if tag == "Concrete":
                            self.assertEqual("25", warhead.get("Damage"))
                            continue
                        self.assertIn(tag, OLD_FLAT_DAMAGE)
                        self.assertEqual(
                            Fraction(OLD_FLAT_DAMAGE[tag], 10),
                            Fraction(int(warhead.get("Damage")), 1),
                            tag,
                        )
                    elif warhead.value == "AreaDamagePercentage":
                        self.assertEqual(
                            Fraction(1, 1000),
                            Fraction(
                                int(warhead.get("Damage")),
                                int(warhead.get("PercentageDenominator") or 100),
                            ),
                            tag,
                        )

                railgun = child(weapon, "Warhead@Railgun_Heavy")
                if railgun is not None:
                    old_units = folded_units(3000, 6667)[1]
                    new_units = folded_units(
                        int(railgun.get("Damage")), int(railgun.get("PercentageScale"))
                    )[1]
                    self.assertEqual(
                        Fraction(old_units, 10000) * Fraction(1, 10),
                        Fraction(new_units, int(railgun.get("PercentageDenominator") or 10000)),
                    )

    def test_targeting_cadence_and_all_other_weapon_fields_are_unchanged(self):
        for weapon_name, expected in NON_DAMAGE_HASHES.items():
            with self.subTest(weapon=weapon_name):
                payload = non_damage_payload(self.rules.resolve_weapon(weapon_name))
                digest = hashlib.sha256(json.dumps(
                    payload, sort_keys=True, separators=(",", ":")
                ).encode()).hexdigest()
                self.assertEqual(expected, digest)


if __name__ == "__main__":
    unittest.main()
