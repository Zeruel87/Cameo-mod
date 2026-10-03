"""Tests for tools/audit/vector_codemod.py (float2/float3 -> System.Numerics, for CA files synced onto
Cameo's bleed engine). Run: python tools/tests/test_vector_codemod.py"""
import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "audit"))
import vector_codemod as vc  # noqa: E402


class VectorCodemodTest(unittest.TestCase):
    def test_types_statics_and_tofloat2(self):
        src = "using System;\nusing OpenRA;\nclass A { float3 a = float3.Ones; float2 b = float2.Zero; var c = p.ToFloat2(); }\n"
        out = vc.convert(src)
        self.assertIn("Vector3 a = Vector3.One;", out)
        self.assertIn("Vector2 b = Vector2.Zero;", out)
        self.assertIn("p.ToVector2()", out)
        self.assertNotRegex(out, r"\bfloat[23]\b")

    def test_using_goes_after_using_system_in_sorted_order(self):
        src = "using System;\nusing System.Linq;\nusing System.Reflection;\nusing OpenRA;\nfloat3 x;\n"
        lines = vc.convert(src).splitlines()
        self.assertEqual(lines[:4], ["using System;", "using System.Linq;", "using System.Numerics;", "using System.Reflection;"])

    def test_keeps_crlf(self):
        out = vc.convert("using System;\r\nfloat3 x;\r\n")
        self.assertIn("using System.Numerics;\r\n", out)
        self.assertNotIn("\n\n", out.replace("\r\n", "\n\x00"))

    def test_no_float_types_is_unchanged_and_idempotent(self):
        src = "using System;\nclass A { int float3ish; }\n"
        self.assertEqual(vc.convert(src), src)
        once = vc.convert("using System;\nfloat3 x;\n")
        self.assertEqual(vc.convert(once), once)

    def test_existing_using_is_not_duplicated(self):
        out = vc.convert("using System;\nusing System.Numerics;\nfloat3 x;\n")
        self.assertEqual(out.count("using System.Numerics;"), 1)


if __name__ == "__main__":
    unittest.main()
