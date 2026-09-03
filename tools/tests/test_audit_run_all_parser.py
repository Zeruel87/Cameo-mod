r"""Unit tests for tools/audit/run_all.py's audit-list parser.

`run_all.py` must never hand-maintain its own audit list — it parses the `for a in …; do` loops
out of `run_all.sh` so the two runners cannot drift. That parser had a real bug: `run_all.sh` is
checked out CRLF, so a line continuation is `\` + CRLF, and the parser stripped only `\` + LF.
Every continuation therefore survived as its own "audit name": 73 entries where 59 are real, and
the runner then tried `tools/audit/audit_\.py` fourteen times and reported fourteen phantom
FAILEDs. It was never noticed because `run_all.sh` is the canonical path (CLAUDE.md rule 8) and
the fallback's output was never compared against it.
"""

from __future__ import annotations

import ast
import pathlib
import re
import unittest

import _bootstrap  # noqa: F401 — sys.path side effect

ROOT = pathlib.Path(__file__).resolve().parents[2]
RUN_ALL_PY = ROOT / "tools" / "audit" / "run_all.py"


def load_parser(shell_path: pathlib.Path):
    """Extract audits_from_shell() and bind it to an arbitrary run_all.sh, without running it.

    Importing run_all.py would execute the whole suite — it is a script, not a module.
    """
    tree = ast.parse(RUN_ALL_PY.read_text(encoding="utf-8"))
    fn = next(n for n in tree.body
              if isinstance(n, ast.FunctionDef) and n.name == "audits_from_shell")
    ns: dict = {"re": re, "SH": shell_path}
    exec(compile(ast.Module(body=[fn], type_ignores=[]), "<parser>", "exec"), ns)
    return ns["audits_from_shell"]


class ParsesTheRealShellScript(unittest.TestCase):
    def setUp(self):
        self.gating, self.advisory = load_parser(ROOT / "tools" / "audit" / "run_all.sh")()

    def test_no_entry_is_a_stray_continuation(self):
        bad = [w for w in self.gating + self.advisory if not re.fullmatch(r"[a-z0-9_]+", w)]
        self.assertEqual(bad, [], f"parser produced non-audit tokens: {bad}")

    def test_every_named_audit_exists_on_disk(self):
        missing = [a for a in self.gating + self.advisory
                   if not (ROOT / "tools" / "audit" / f"audit_{a}.py").is_file()]
        self.assertEqual(missing, [])

    def test_the_advisory_list_is_the_scheduled_family(self):
        # Maintainer ruling 2026-08-24: the periodic.json scans must not gate the per-commit run.
        self.assertEqual(sorted(self.advisory),
                         ["code_duplication", "error_handling", "recent_changes",
                          "security", "test_coverage"])

    def test_advisory_and_gating_do_not_overlap(self):
        self.assertEqual(set(self.gating) & set(self.advisory), set())


class HandlesBothLineEndings(unittest.TestCase):
    # Built from a line list joined with "\n" so the continuation backslash cannot be mangled by
    # escaping: CONT is one literal backslash, the last character of a continued shell line.
    CONT = chr(92)
    SCRIPT = "\n".join([
        "#!/bin/sh",
        "for a in alpha beta " + CONT,
        "         gamma delta " + CONT,
        "         epsilon; do",
        "  echo $a",
        "done",
        "",
        "# ADVISORY audits — not gating.",
        "for a in zeta eta; do",
        "  echo $a",
        "done",
        "",
    ])

    def parse(self, text: str, tmpname: str):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            path = pathlib.Path(tmp) / tmpname
            path.write_bytes(text.encode("utf-8"))
            return load_parser(path)()

    def test_lf_continuations(self):
        gating, advisory = self.parse(self.SCRIPT, "lf.sh")
        self.assertEqual(gating, ["alpha", "beta", "gamma", "delta", "epsilon"])
        self.assertEqual(advisory, ["zeta", "eta"])

    def test_crlf_continuations_are_the_regression(self):
        gating, advisory = self.parse(self.SCRIPT.replace("\n", "\r\n"), "crlf.sh")
        self.assertEqual(gating, ["alpha", "beta", "gamma", "delta", "epsilon"],
                         "CRLF continuations leaked backslashes into the audit list")
        self.assertEqual(advisory, ["zeta", "eta"])

    def test_a_script_with_no_advisory_marker_yields_no_advisory_list(self):
        text = self.SCRIPT.split("# ADVISORY")[0]
        gating, advisory = self.parse(text, "one.sh")
        self.assertEqual(gating, ["alpha", "beta", "gamma", "delta", "epsilon"])
        self.assertEqual(advisory, [])

    def test_the_advisory_loop_is_found_by_marker_not_by_position(self):
        # A loop inserted BETWEEN the two must not be mistaken for the advisory one.
        text = self.SCRIPT.replace(
            "# ADVISORY audits",
            "for a in intruder; do\n  echo $a\ndone\n\n# ADVISORY audits")
        gating, advisory = self.parse(text, "mid.sh")
        self.assertEqual(gating, ["alpha", "beta", "gamma", "delta", "epsilon"])
        self.assertEqual(advisory, ["zeta", "eta"])

    def test_the_extras_name_colon_script_loop_is_ignored(self):
        text = self.SCRIPT + "\nfor a in foo:tools/foo.py bar:tools/bar.py; do\n  :\ndone\n"
        gating, advisory = self.parse(text, "extras.sh")
        self.assertNotIn("foo", gating + advisory)
        self.assertNotIn("bar", gating + advisory)


if __name__ == "__main__":
    unittest.main()
