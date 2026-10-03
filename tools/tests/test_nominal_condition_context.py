import sys
from pathlib import Path
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'tools/reference'))
from nominal_condition_context import empty_context, evaluate_context


class EmptyContextTest(unittest.TestCase):
    def test_reviewed_base_and_upgrade_conditions(self):
        for expression in (None, '!lastnk-upgrade', '!frenzy && !frenzyinit', 'rank-veteran == 0', 'true'):
            self.assertIs(empty_context(expression), True, expression)
        for expression in ('lastnk-upgrade', '!frenzy && frenzyinit', 'rank-veteran == 1',
                           'rank-elite && !development-policy3', 'anathema >= 4', 'false'):
            self.assertIs(empty_context(expression), False, expression)

    def test_ammo_context_does_not_enable_upgrades(self):
        self.assertTrue(evaluate_context('ammo && !laser-upgrade', {'ammo': 6}))
        self.assertFalse(evaluate_context('!ammo', {'ammo': 6}))
        self.assertFalse(evaluate_context('laser-upgrade', {'ammo': 6}))

    def test_unknown_is_not_silently_false(self):
        for expression in ('x + 1', 'f(x)', 'x[0]', 'x / 0', 'x ^^ y', 'x ==', '"x"', 'x < y < z'):
            self.assertIsNone(empty_context(expression), expression)


if __name__ == '__main__':
    unittest.main()
