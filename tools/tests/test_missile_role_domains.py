import pathlib
import sys
import unittest

sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'audit'))
from miniyaml import Node
from audit_missile_role_family import weapon_role


class MissileRoleDomains(unittest.TestCase):
    def test_custom_tags_are_not_assumed_ground_only(self):
        for valid in ['lockon','Ground, lockon']:
            root=Node('weapon','',[Node('ValidTargets',valid)])
            self.assertEqual(weapon_role(root),'custom')

    def test_explicit_air_exclusion_is_respected(self):
        root=Node('weapon','',[Node('ValidTargets','Ground, Water, Air'),Node('InvalidTargets','Air')])
        self.assertEqual(weapon_role(root),'ground')

    def test_empty_domain_is_not_certified_as_ground(self):
        root=Node('weapon','',[Node('ValidTargets','Air'),Node('InvalidTargets','Air')])
        self.assertEqual(weapon_role(root),'custom')
