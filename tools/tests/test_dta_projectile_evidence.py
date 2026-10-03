import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'reference'))
from dta_projectile_evidence import decode_speed


class SpeedTests(unittest.TestCase):
    def test_percentage_scale_truncation_and_light_speed_cap(self):
        self.assertEqual(decode_speed('40'), 102)
        self.assertEqual(decode_speed('16'), 40)
        self.assertEqual(decode_speed('100'), 255)
        self.assertEqual(decode_speed('200'), 255)
        self.assertEqual(decode_speed(None), 0)


if __name__ == '__main__':
    unittest.main()
