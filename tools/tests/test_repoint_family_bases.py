"""repoint_family_bases.py — the mechanics that each broke once while it was built (2026-09-27).

The full dry-run (1,191 owners, 1,662 weapons re-resolved, 0 non-h differences) takes minutes and
is recorded in the PR; these tests pin the small pieces whose failure made that run lie or fail:
a header with a comment, a pin landing after the next def's heading comment, a bare-key cancel
without a colon, a cancel that must not open a node, the truncating radius scale, the percentage
dial ratio, and nested / cancel pins.
"""
from __future__ import annotations

import pathlib
import sys
import tempfile
import types
import unittest

import _bootstrap  # noqa: F401 — sys.path side effect

sys.path.insert(0, str(pathlib.Path(_bootstrap.REPO_ROOT) / "tools" / "balance"))
sys.path.insert(0, str(pathlib.Path(_bootstrap.REPO_ROOT) / "tools" / "audit"))
import effective_heaviness as eh  # noqa: E402
import repoint_family_bases as rp  # noqa: E402


class Block(unittest.TestCase):
    def test_header_may_carry_a_comment(self):
        lines = ["TSIonCannon: ### main beam dummy", "\tRange: 5", "", "Next:"]
        self.assertEqual(rp._block(lines, "TSIonCannon"), (0, 2))

    def test_trailing_comments_belong_to_the_next_def(self):
        lines = ["A:", "\tX: 1", "", "## heading of B", "## more", "", "B:"]
        self.assertEqual(rp._block(lines, "A"), (0, 2))


class Geometry(unittest.TestCase):
    def test_inverse_survives_the_truncating_scale(self):
        # Bullet Medium 100 at h=0 truncates to 66; the legacy Light template said 67.
        self.assertEqual(eh.scale_length(100, 0), 66)
        raw = rp._geom_inverse(67, 0)
        self.assertEqual(eh.scale_length(raw, 0), 67)

    def test_inverse_is_identity_at_h1(self):
        for v in (0, 1, 67, 1234):
            self.assertEqual(rp._geom_inverse(v, 1000), v)

    def test_range_arrays_are_rescaled_element_by_element(self):
        out = rp._rescale_line("Range", "0, 512, 1024", 2000, 2000)
        self.assertEqual([eh.scale_length(int(x), 2000) for x in out.split(", ")], [0, 512, 1024])

    def test_percentage_dial_keeps_its_ratio(self):
        # A 5000 dial against the old default 10000 becomes half of the base's scale.
        self.assertEqual(rp._rescale_line("PercentageScale", "5000", 0, 2000), "1000")
        self.assertEqual(rp._rescale_line("PercentageScale", "10000", 0, 4000), "4000")


def _fake_rs(path, names):
    node = types.SimpleNamespace(file=str(path))
    return types.SimpleNamespace(weapons={n: node for n in names})


class Edits(unittest.TestCase):
    def _run(self, text, owners, names):
        with tempfile.TemporaryDirectory() as tmp:
            p = pathlib.Path(tmp) / "w.yaml"
            p.write_bytes(text.encode("utf-8"))
            texts = rp.edit_texts(_fake_rs(p, names), owners, {"Demolition": 2000})
            return texts[str(p)]

    def test_rename_edge_node_and_bare_cancel(self):
        text = "\n".join([
            "W:",
            "\tInherits@wh: ^Warhead_Demolition_Heavy",
            "\tWarhead@Demolition_Heavy:",
            "\t\tDamage: 9",
            "\t\tSpread: 100",
            "\t-Warhead@Demolition_Heavy",          # bare key, no colon
            "\t\tSpread: 100",                       # would be wrongly rescaled if the cancel opened a node
            ""])
        out = self._run(text, [("W", "Demolition", "Heavy", {"W"})], ["W"]).split("\n")
        self.assertEqual(out[1], "\tInherits@wh: ^Warhead_Demolition")
        self.assertEqual(out[2], "\tWarhead@Demolition:")
        self.assertEqual(out[3], "\t\tDamage: 9")                       # not h-owned: untouched
        self.assertEqual(eh.scale_length(int(out[4].split(": ")[1]), 2000), 100)
        self.assertEqual(out[5], "\t-Warhead@Demolition")
        self.assertEqual(out[6], "\t\tSpread: 100")

    def test_descendant_keys_are_renamed_but_its_edges_are_not(self):
        text = "\n".join(["W:", "\tInherits@wh: ^Warhead_Demolition_Heavy", "",
                          "C:", "\tInherits: W", "\tWarhead@Demolition_Heavy_ExtraDamage:", "\t\tDamage: 1", ""])
        out = self._run(text, [("W", "Demolition", "Heavy", {"W", "C"})], ["W", "C"])
        self.assertIn("\tWarhead@Demolition_ExtraDamage:", out)
        self.assertIn("\tInherits: W", out)


class Pins(unittest.TestCase):
    def test_nested_and_cancel_pins(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = pathlib.Path(tmp) / "w.yaml"
            p.write_bytes("W:\n\tRange: 5\n\n## next\nX:\n".encode("utf-8"))
            pins = {"W": {"Warhead@CannonChem": {
                "PhysicalStates": ("nested", {("Corrosion",): "20"},
                                   {("Corrosion",): "33", ("Heat",): "5"}),
                "FriendlyFireDamage": rp.CANCEL,
                "Heaviness": 0}}}
            out = rp.add_pins({}, _fake_rs(p, ["W"]), pins)[str(p)].split("\n")
        self.assertEqual(out[:8], ["W:", "\tRange: 5",
                                   "\tWarhead@CannonChem:",
                                   "\t\tPhysicalStates:",
                                   "\t\t\tCorrosion: 20",
                                   "\t\t\t-Heat:",
                                   "\t\t-FriendlyFireDamage:",
                                   "\t\tHeaviness: 0"])
        self.assertEqual(out[9], "## next")                      # the pin sits BEFORE the comment


if __name__ == "__main__":
    unittest.main()
