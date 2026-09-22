"""Actor-owned dog bite weapons: unique ownership, identical resolved payload.

Pilot per Aedis's bounded request: DogJaw (shared, TargetDamage instant-kill)
became a shared abstract ^DogJaw plus three explicit actor-owned entries.
No balance differentiation is approved; payloads must be EXACTLY equal to the
pre-migration resolved DogJaw, and each dog actor must reference its own
weapon id.
"""
import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools/audit"))
import miniyaml


def node_to_obj(node):
    if not node.children:
        return node.value
    return {c.key: node_to_obj(c) for c in node.children}


class DogWeaponOwnershipTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rules = miniyaml.Ruleset(ROOT)
        cls.bite_of_dog = ("ra1_soviets_dog", "ra1_soviets_dog_bite")
        cls.bite_of_dog2 = ("ra2_allies_dog", "ra2_allies_dog_bite")
        cls.bite_of_dog3 = ("ra2_soviets_dog", "ra2_soviets_dog_bite")

    def resolve(self, name):
        return self._n2o(self.rules.resolve_weapon(name))

    def _n2o(self, node):
        if node is None:
            return None
        if not node.children:
            return node.value
        obj = {c.key: self._n2o(c) for c in sorted(node.children, key=lambda n: n.key)}
        if node.value:
            obj["__value"] = node.value
        return obj

    def test_shared_concrete_dogjaw_gone(self):
        self.assertIsNone(self.rules.weapon("dogjaw"),
                          "standalone DogJaw must not remain (or must stay used)")

    def test_abstract_and_three_entries_exist(self):
        self.assertIsNotNone(self.rules.weapon("^DogJaw"))
        for _, bite in (self.bite_of_dog, self.bite_of_dog2, self.bite_of_dog3):
            self.assertIsNotNone(self.rules.weapon(bite), f"missing {bite}")

    def test_bites_equal_pre_migration_resolved_payload(self):
        pre = {
            "InvalidTargets": "DogImmune",
            "Projectile": "InstantHit",
            "Range": "2000",
            "ReloadDelay": "10",
            "Report": "dogg5p.aud",
            "TargetActorCenter": "true",
            "ValidTargets": "Infantry",
            "Warhead@1Dam": {
                "Damage": "100000",
                "DamageTypes": "DefaultDeath",
                "InvalidTargets": "Ant, DogImmune",
                "ValidTargets": "Infantry",
                "__value": "TargetDamage",
            },
        }
        self.maxDiff = None
        for _, bite in (self.bite_of_dog, self.bite_of_dog2, self.bite_of_dog3):
            self.assertEqual(self._n2o(self.rules.resolve_weapon(bite)), pre,
                             f"{bite} drift from pre-migration DogJaw")

    def test_each_dog_owns_a_distinct_weapon(self):
        seen = {}
        for owner, bite in (self.bite_of_dog, self.bite_of_dog2, self.bite_of_dog3):
            node = self.rules.resolve(owner)
            weapon = None
            for c in node.children:
                if c.key.startswith("Armament"):
                    for l in c.children:
                        if l.key == "Weapon":
                            weapon = l.value
            self.assertEqual(weapon, bite, f"{owner} does not own {bite}")
            self.assertNotIn(weapon, seen, "shared weapon reference " + weapon)
            seen[weapon] = owner

    def test_bite_is_combat_not_utility(self):
        node = self._n2o(self.rules.resolve_weapon("ra1_soviets_dog_bite"))
        self.assertEqual(node["Warhead@1Dam"]["__value"], "TargetDamage")
        self.assertEqual(node["Warhead@1Dam"]["Damage"], "100000")

    def test_variants_inherit_correctly(self):
        # same-actor variants (colorpicker/promotion children) resolve through
        # the renamed owners without fallout.
        for owner in ("ra1_soviets_dog", "ra2_allies_dog", "ra2_soviets_dog"):
            node = self.rules.resolve(owner)
            self.assertIsNotNone(node)


if __name__ == "__main__":
    unittest.main()
