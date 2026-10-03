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


WEAPONS = (
    "ArmoredCarMG",
    "ArmoredCarMG_AA",
    "ArmoredCarMGWaveforce",
    "ArmoredCarMGAAWaveforce",
)

# Every resolved runtime field except Damage and PercentageDenominator: targeting, cadence, projectile,
# versus tables, effects. Re-pinned 2026-09-28 on the post-W24 layout (the pre-bake pins went stale when
# the bullet and railgun warheads folded into one main); change them only with a reviewed resolve diff.
# Re-pinned 2026-09-30 for #650 (DESIGN §12.0l step 1 + the submarine columns): the reviewed resolve diff
# (master 1adffd61d vs the integration) ADDS 124-141 derived-armour Versus rows per weapon and removes or
# changes nothing.
NON_DAMAGE_HASHES = {
    "ArmoredCarMG": "b88693f3f7a6e77e5bde4536d075f242254af9ee1fba345b21ed5aa0336abf79",
    "ArmoredCarMG_AA": "b9ded8122b2fb602531b51d9421b7e5c6dce40e17644d1c5ee9f8f136b1aabab",
    "ArmoredCarMGWaveforce": "0b39132b35bc50d9cba7190fbf688f213c60204dc47511ed7b7e51cc721752ef",
    "ArmoredCarMGAAWaveforce": "cf7b95423fcfcd5346b57eca9217175dca151f1d072cafe85ae278e51b1f3362",
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

    def test_total_flat_damage_retains_the_ten_percent_bake_after_warhead_folds(self):
        for weapon_name in WEAPONS:
            with self.subTest(weapon=weapon_name):
                weapon = self.rules.resolve_weapon(weapon_name)
                # W24 folds the original 16000 bullet + 3000 railgun into
                # one main. Preserve the total, not the retired node split.
                old_total = 16000 + (3000 + 1000 if "Waveforce" in weapon_name else 0)
                flat_total = sum(
                    int(warhead.get("Damage") or 0)
                    for warhead in weapon.children
                    if warhead.key.startswith("Warhead@")
                    and warhead.value in {"AreaDamage", "SpreadDamage", "TargetDamage"}
                )
                self.assertEqual(old_total // 10, flat_total)
                self.assertEqual("25", child(weapon, "Warhead@Concrete").get("Damage"))

                # Standalone percentage channels retain their independent
                # bake. A folded channel follows its current main Damage.
                for warhead in weapon.children:
                    if warhead.value == "AreaDamagePercentage" and warhead.get("Damage"):
                        self.assertEqual(
                            Fraction(1, 1000),
                            Fraction(
                                int(warhead.get("Damage")),
                                int(warhead.get("PercentageDenominator") or 100),
                            ),
                            warhead.key,
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
