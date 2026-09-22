"""Continuous profiles are unclassified, not mislabeled legacy or tier-approved."""
import unittest
import _bootstrap  # noqa: F401
from miniyaml import load_text
from audit_tier_weapon_class import continuous_only, main_warheads


class ContinuousTierReporting(unittest.TestCase):
    def node(self, h='0', mode='SharedVersus'):
        return load_text('Test:\n\tWarhead@CannonAP: AreaDamage\n'
                         '\t\tDamage: 30000\n\t\tHeaviness: ' + h +
                         '\n\t\tHeavinessMode: ' + mode + '\n')[0]

    def test_explicit_valid_endpoints(self):
        for h in ('0', '1000', '2000'):
            node = self.node(h)
            self.assertTrue(continuous_only(node, main_warheads(node)))

    def test_invalid_or_legacy_cannot_disappear_into_continuous_count(self):
        for h, mode in (('-1', 'SharedVersus'), ('2001', 'SharedVersus'),
                        ('bad', 'SharedVersus'), ('0', 'Legacy'), ('', 'SharedVersus')):
            node = self.node(h, mode)
            self.assertFalse(continuous_only(node, main_warheads(node)))
        node = self.node()
        node.children += load_text('Test:\n\tWarhead@Other: AreaDamage\n\t\tDamage: 10\n')[0].children
        self.assertFalse(continuous_only(node, main_warheads(node)))
