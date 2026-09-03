"""Unit tests for the D8 citation check in tools/audit/audit_doc_health.py.

D8 exists because of one real incident: a DESIGN renumber moved MEAN-100 from §12.0a to
§12.0h, and `audit_versus_profile.py` went on PRINTING `## §12.0a MEAN-100` into a
generated report for days. Nothing was broken — the id existed, the heading existed, the
markdown rendered — so no existing gate could see it.

The whole design rests on ONE property, and it is the property a careless edit destroys:
D8 fires on a LABEL (`§12.0a MEAN-100`, an assertion that this id IS that law) and stays
silent on PROSE that merely mentions another law near a citation. A D8 that flags prose
gets muted within a week and then protects nothing, so the negative cases below matter at
least as much as the positive ones.
"""

from __future__ import annotations

import unittest

import _bootstrap  # noqa: F401 — sys.path side effect

import audit_doc_health as dh

# A miniature DESIGN.md. Two sections deliberately share the word "ARMOR" so the
# distinctiveness filter has something to reject.
DESIGN = """
## 12. Balance formula
## 12.0a PLATFORM, NOT JUST FAMILY (maintainer) — binding
## 12.0b HEROIC ARMOR IS A BRIDGE, NOT THE TOP RUNG
## 12.0d THE CLASS TILT (maintainer) — binding
## 12.0e THE ARMOR-PLATING LAYER
## 12.0h THE MEAN-100 LAW (maintainer) — binding
"""


class DesignSections(unittest.TestCase):
    def test_ids_and_titles(self):
        s = dh.design_sections(DESIGN)
        self.assertEqual(s["12.0h"], "THE MEAN-100 LAW (maintainer) — binding")
        self.assertIn("12.0a", s)
        self.assertIn("12", s)


class DistinctiveNames(unittest.TestCase):
    def setUp(self):
        self.names = dh.distinctive_names(dh.design_sections(DESIGN))

    def test_a_word_used_by_one_heading_identifies_it(self):
        self.assertEqual(self.names["MEAN-100"], "12.0h")
        self.assertEqual(self.names["PLATFORM"], "12.0a")
        self.assertEqual(self.names["TILT"], "12.0d")

    def test_a_word_shared_by_two_headings_identifies_neither(self):
        # 12.0b HEROIC ARMOR and 12.0e ARMOR-PLATING both claim it.
        self.assertNotIn("ARMOR", self.names)

    def test_stopwords_and_short_words_are_never_distinctive(self):
        for w in ("THE", "LAW", "NOT", "JUST"):
            self.assertNotIn(w, self.names)


def cites(text: str) -> list[tuple[str, str]]:
    return [(m.group(1), m.group(2)) for m in dh.CITATION.finditer(text)]


class CitationShape(unittest.TestCase):
    """What counts as a LABEL — the assertion "this id is that law"."""

    def test_bare_name_after_the_id(self):
        self.assertEqual(cites("see §12.0h MEAN-100 for"), [("12.0h", "MEAN-100")])

    def test_leading_the_is_part_of_the_label(self):
        self.assertEqual(cites("§12.0d THE CLASS tilt"), [("12.0d", "THE CLASS")])

    def test_punctuation_between_id_and_label(self):
        self.assertEqual(cites("§12.0h: MEAN-100"), [("12.0h", "MEAN-100")])

    def test_lowercase_prose_is_not_a_label(self):
        # "applies" is ordinary sentence text, so there is no label to check at all.
        self.assertEqual(cites("§12.0d applies the MEAN-100 rows"), [])


class D8Detection(unittest.TestCase):
    """The rule as the audit applies it: label word -> owning section -> mismatch?"""

    def setUp(self):
        self.sections = dh.design_sections(DESIGN)
        self.names = dh.distinctive_names(self.sections)
        self.checkable = {i for i in self.sections if not i.isdigit()}

    def findings(self, text: str) -> list[str]:
        out = []
        for m in dh.CITATION.finditer(text):
            sid, label = m.group(1), m.group(2)
            if sid not in self.checkable:
                continue
            for word in dh.re.findall(r"[A-Za-z][A-Za-z0-9]*(?:-[A-Za-z0-9]+)*", label):
                owner = self.names.get(word.upper())
                if owner and owner != sid:
                    out.append(f"{sid}->{owner}")
                    break
        return out

    def test_the_incident_that_motivated_this_check(self):
        self.assertEqual(self.findings("## §12.0a MEAN-100 — 123 of 125 conform"),
                         ["12.0a->12.0h"])

    def test_a_correct_citation_is_silent(self):
        self.assertEqual(self.findings("## §12.0h MEAN-100 — 123 of 125 conform"), [])
        self.assertEqual(self.findings("§12.0d THE CLASS TILT applies"), [])

    def test_prose_near_a_citation_is_silent(self):
        self.assertEqual(self.findings("§12.0d applies the tilt to MEAN-100 rows"), [])

    def test_a_word_two_headings_share_never_fires(self):
        # Would be a false positive if ARMOR were treated as distinctive.
        self.assertEqual(self.findings("§12.0e ARMOR-PLATING layer"), [])

    def test_bare_integer_ids_are_out_of_scope(self):
        # Half the design documents number their own sections; "§12 PLATFORM" in one of
        # them means that document's §12, and D8 must not guess.
        self.assertEqual(self.findings("§12 PLATFORM notes"), [])

    def test_an_unnamed_citation_asserts_nothing(self):
        self.assertEqual(self.findings("restated in §12.0a and elsewhere"), [])


if __name__ == "__main__":
    unittest.main()
