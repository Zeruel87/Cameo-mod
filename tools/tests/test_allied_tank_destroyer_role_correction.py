"""AlliedTankDestroyerCannon W24 AP-role correction (maintainer order, 2026-09-10).

Pins the live weapon against the reconstructed pre-correction state: the old
weapon was exactly the two resolved templates ^Warhead_CannonHE_Medium +
^Warhead_CannonAP_Light, each overridden to Damage 12000. All other fields
came from ^Projectile_Shell_Light and ^Effect_CannonAP_Light, which are
unchanged. This change is explicitly NOT gameplay-equivalent: the HE half's
wide blast (Spread 300, Falloff 100, 50, 20, 0) is gone and its armor profile
is redistributed into the AP half.
"""

from __future__ import annotations

import json
import pathlib
import sys
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[2]
BASELINE = ROOT / "docs/reference/release_baseline_playtest_20260709.json"
sys.path[:0] = [str(ROOT / "tools/audit"), str(ROOT / "tools/balance")]

from audit_three_way_split import main_warheads, main_warhead_nodes  # noqa: E402
from miniyaml import Ruleset  # noqa: E402
from percentage_damage import folded_units  # noqa: E402
from reviewed_weapon_history import restore_endpoint_weapon
from effective_heaviness import scale_length

WEAPON = "AlliedTankDestroyerCannon"


def versus_values(node):
    out = {}
    for wh in node.children:
        if not wh.key.startswith("Warhead@"):
            continue
        versus = wh.child("Versus")
        if versus is None:
            continue
        out[wh.key] = {c.key: int(c.value) for c in versus.children}
    return out


class AlliedTankDestroyerRoleCorrectionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rules = Ruleset(ROOT)
        cls.live = cls.rules.resolve_weapon(WEAPON)
        cls.he = cls.rules.resolve_weapon("^Warhead_CannonHE_Medium")
        cls.ap = cls.rules.resolve_weapon("^Warhead_CannonAP_Light")

    def test_live_weapon_is_a_single_ap_main_at_24000(self):
        self.assertEqual(["CannonAP"], main_warheads(self.live))
        node = main_warhead_nodes(self.live)[0]
        self.assertEqual("24000", node.get("Damage"))
        self.assertEqual("AreaDamage", node.value)
        self.assertEqual(80, scale_length(int(node.get("Spread")), int(node.get("Heaviness"))))
        self.assertEqual("100, 0", node.get("Falloff"))
        self.assertEqual("2000", node.get("PercentageScale"))
        self.assertEqual("0", node.get("Heaviness"))
        self.assertEqual("SharedVersus", node.get("HeavinessMode"))
        self.assertIsNone(self.live.child("Warhead@CannonHE_Medium"))

    def test_flattotal_matches_old_sum_and_shipped_release(self):
        old_flat = 12000 + 12000
        baseline = json.loads(BASELINE.read_text(encoding="utf-8"))["weapons"][WEAPON]
        self.assertEqual(24000, old_flat)
        self.assertEqual(24000, baseline["flat"])
        self.assertEqual(2, baseline["mains"])

    def test_he_half_was_the_wide_blast_and_is_gone(self):
        he = self.he.child("Warhead@CannonHE_Medium")
        self.assertEqual("300", he.get("Spread"))
        self.assertEqual("100, 50, 20, 0", he.get("Falloff"))
        ap = self.ap.child("Warhead@CannonAP_Light")
        self.assertEqual("80", ap.get("Spread"))
        self.assertEqual("100, 0", ap.get("Falloff"))
        self.assertEqual(-220, int(ap.get("Spread")) - int(he.get("Spread")))
        self.assertAlmostEqual(-73.3, round(
            (int(ap.get("Spread")) - int(he.get("Spread"))) / int(he.get("Spread")) * 100, 1))
        # Spread is sample spacing, not the full outer radius.
        old_radius = int(he.get("Spread")) * (len(he.get("Falloff").split(",")) - 1)
        new_radius = int(ap.get("Spread")) * (len(ap.get("Falloff").split(",")) - 1)
        self.assertEqual((900, 80), (old_radius, new_radius))
        self.assertEqual(-91.1, round((new_radius / old_radius - 1) * 100, 1))

    def test_ap_armor_table_is_unchanged_from_template(self):
        # Pin the first AP correction separately from the later shared h0 profile.
        live_versus = versus_values(restore_endpoint_weapon(self, self.live))["Warhead@CannonAP_Light"]
        template_versus = versus_values(self.ap)["Warhead@CannonAP_Light"]
        self.assertEqual(template_versus, live_versus)

    def test_armor_delta_extremes_from_removing_the_he_half(self):
        he_v = versus_values(self.he)["Warhead@CannonHE_Medium"]
        ap_v = versus_values(self.ap)["Warhead@CannonAP_Light"]
        self.assertEqual(sorted(he_v), sorted(ap_v))
        old = {a: 12000 * he_v[a] + 12000 * ap_v[a] for a in ap_v}
        new = {a: 24000 * ap_v[a] for a in ap_v}
        delta = {a: (new[a] - old[a]) / old[a] * 100 for a in ap_v}
        self.assertEqual(0.0, round(delta["ARMOR"], 1))
        self.assertEqual(-41.8, round(delta["COMPOSITE"], 1))
        self.assertEqual(+31.7, round(delta["Spaceship"], 1))
        mean = (sum(new.values()) - sum(old.values())) / sum(old.values()) * 100
        self.assertEqual(-0.3, round(mean, 1))

    def test_percentage_profile_change_accounts_for_doubled_ap_damage(self):
        def pct(node, tag):
            wh = next(w for w in node.children if w.key == f"Warhead@{tag}")
            return {c.key: int(c.value) for c in wh.child("PercentageVersus").children}

        he_pct, ap_pct = pct(self.he, "CannonHE_Medium"), pct(self.ap, "CannonAP_Light")
        self.assertEqual(sorted(he_pct), sorted(ap_pct))
        self.assertEqual(225, sum(he_pct.values()))
        self.assertEqual(153, sum(ap_pct.values()))
        old_units = folded_units(12000, 10000)[1]
        historical = restore_endpoint_weapon(self, self.live)
        live_main = historical.child("Warhead@CannonAP_Light")
        new_units = folded_units(int(live_main.get("Damage")),
                                 int(live_main.get("PercentageScale")))[1]
        old_total = old_units * sum(he_pct[a] + ap_pct[a] for a in ap_pct)
        new_total = new_units * sum(ap_pct.values())
        # A centered, equal-armor aggregate diagnostic, not a matchup-weighted
        # damage claim. Doubling AP Damage doubles its percentage magnitude.
        self.assertEqual((378, 306), (old_total / old_units, new_total / old_units))
        self.assertEqual(-19.05, round((new_total / old_total - 1) * 100, 2))
        live_pct = pct(historical, "CannonAP_Light")
        self.assertEqual(ap_pct, live_pct)

    def test_projectile_effects_timing_targets_preserved(self):
        self.assertEqual("60", self.live.get("ReloadDelay"))
        self.assertEqual("6819", self.live.get("Range"))
        self.assertEqual("tank5.aud", self.live.get("Report"))
        self.assertEqual("Ground, Water", self.live.get("ValidTargets"))
        self.assertEqual("true", self.live.get("TargetActorCenter"))
        proj = self.live.child("Projectile")
        self.assertEqual("Bullet", proj.value)
        self.assertEqual("1362", proj.get("Speed"))
        self.assertEqual("120MM", proj.get("Image"))
        self.assertEqual("1", proj.get("InaccuracyPercentage"))
        self.assertEqual("10", proj.get("ProjectileSpeedPercentage"))
        self.assertEqual("true", proj.get("Shadow"))
        effect_keys = {
            wh.key.split("@", 1)[1]
            for wh in self.live.children
            if wh.key.startswith("Warhead@")
            and wh.value not in ("AreaDamage", "AreaDamagePercentage", "SpreadDamage")
        }
        self.assertEqual(
            {"Glow", "Smudge", "DuneRock", "DuneSand", "RA2Crater", "Effect",
             "EffectWater", "EffectAir", "ShieldHit", "Concrete", "ShieldHitEffect"},
            effect_keys)

    def test_cryo_pair_untouched(self):
        cryo = self.rules.resolve_weapon("AlliedTankDestroyerCannonCryo")
        self.assertEqual(["CannonCryo_Medium"], main_warheads(cryo))
        node = main_warhead_nodes(cryo)[0]
        self.assertEqual("24000", node.get("Damage"))
        self.assertEqual("55", node.get("Spread"))
        self.assertEqual("100, 61, 28, 0", node.get("Falloff"))


if __name__ == "__main__":
    unittest.main()
