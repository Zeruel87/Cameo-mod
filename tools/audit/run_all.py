#!/usr/bin/env python3
"""Windows-friendly Python equivalent of ``tools/audit/run_all.sh``.

Runs the full Cameo audit suite, writes one markdown report per audit to
docs/audit/latest/, regenerates docs/factions/MATRIX.md, and exits non-zero
if any blocking audit fails.

``run_all.sh`` is the CANONICAL entry point (CLAUDE.md rule 8). This module
exists for shells without ``sh`` and MUST produce byte-identical output:

* the same audit list — parsed straight out of ``run_all.sh`` so the two
  cannot drift, which is how the tree ended up with a duplicate report set
  (``docs/audit/latest/audit_<name>.md`` *and* ``<name>.md``) in the first
  place: this script used to prefix every report with ``audit_``;
* the same report FILENAMES (``<name>.md``, no ``audit_`` prefix).

Never hand-maintain a second audit list here. Add audits to ``run_all.sh``.
"""
import os
import pathlib
import re
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "audit"))
import environment  # noqa: E402  (must follow the sys.path insert)

# Same guard as run_all.sh: docs/audit/latest/ is TRACKED evidence and several audits
# read engine/ C# or full git history. Without them those audits report LESS and still
# say PASS, so regenerating from an incomplete tree silently deletes real findings.
FORCE_LATEST = "--force-latest" in sys.argv
PASSTHROUGH = [a for a in sys.argv[1:] if a != "--force-latest"]
_dest, _reasons = environment.out_dir(FORCE_LATEST)
if _reasons:
    print(environment.banner(_dest, _reasons), file=sys.stderr)

OUT = ROOT / _dest
OUT.mkdir(parents=True, exist_ok=True)
(ROOT / "docs" / "factions").mkdir(parents=True, exist_ok=True)

SH = ROOT / "tools" / "audit" / "run_all.sh"

PYTHON = sys.executable
failed = 0

# Force child processes to emit UTF-8 regardless of the OS console codepage
# (Windows defaults to cp1252, which corrupts §, —, etc. in audit output —
# see LESSONS_LEARNED.md). Passing a file object directly as stdout= to
# subprocess.run() writes raw bytes from the child at the OS level, bypassing
# the parent file object's own encoding, so this must be set via env instead.
CHILD_ENV = dict(os.environ, PYTHONIOENCODING="utf-8")


def audits_from_shell() -> tuple[list[str], list[str]]:
    """Read BOTH ``for a in … ; do`` audit loops out of run_all.sh.

    Returns (gating, advisory). Parsing the shell script is deliberate: a hand-copied list in
    this file is exactly the drift that produced the duplicate report set.

    ⚠ There are TWO loops since 2026-08-24. The first gates the suite's exit code; the second is
    ADVISORY — the five scheduled scans from periodic.json, which must not turn the per-commit
    gate red (see the comment above that loop). A parser that grabbed only the first would
    silently stop running five audits, which is the same drift wearing a new costume.
    """
    text = SH.read_text(encoding="utf-8")

    def names(body: str) -> list[str]:
        # ⚠ run_all.sh is checked out CRLF, so a line continuation is `\` + CRLF. Replacing only
        # `\` + LF left every `\` in the list as its own "audit name": this parser yielded 73
        # entries where 59 are real, and the runner then tried `tools/audit/audit_\.py` fourteen
        # times and reported fourteen phantom FAILEDs. Normalise the line endings FIRST.
        # (Latent since the file gained continuations — run_all.sh is the canonical path, so the
        # Python fallback's output was never compared against it. Found 2026-08-24.)
        body = body.replace("\r\n", "\n").replace("\r", "\n").replace("\\\n", " ")
        # Drop comment lines that the DOTALL match may have swallowed.
        body = "\n".join(ln for ln in body.splitlines() if not ln.lstrip().startswith("#"))
        # The `name:script` loop for audits outside tools/audit/ is covered by EXTRAS.
        return [w for w in body.split() if ":" not in w and w != "\\"]

    # The GATING loop is the first one. The ADVISORY loop is found by its marker comment rather
    # than by index: indexing blocks[1] would silently pick up any loop inserted between them.
    first = re.search(r"^for a in (.*?); do$", text, re.MULTILINE | re.DOTALL)
    if not first:
        raise SystemExit(f"cannot find the audit list in {SH}")
    gating = names(first.group(1))
    if not gating:
        raise SystemExit(f"the gating audit list in {SH} parsed empty")

    advisory: list[str] = []
    marker = re.search(r"^# ADVISORY audits\b.*?^for a in (.*?); do$",
                       text, re.MULTILINE | re.DOTALL)
    if marker:
        advisory = names(marker.group(1))
    return gating, [a for a in advisory if a not in gating]


# Audits that live outside tools/audit/, mirroring the second loop in run_all.sh.
EXTRAS = [
    ("createeffect_image", ROOT / "tools" / "audit_createeffect_image.py"),
    ("ce_image_usage", ROOT / "tools" / "audit_ce_image_usage.py"),
    ("empty_warhead", ROOT / "tools" / "audit" / "find_empty_warhead.py"),
    ("gen_sync", ROOT / "tools" / "balance" / "verify_generator_sync.py"),
]


def run(name, script, extra_args=None, advisory=False):
    global failed
    print(f"== {name}{' (advisory)' if advisory else ''}")
    md = OUT / f"{name}.md"
    err = OUT / f"{name}.err"
    cmd = [PYTHON, str(script)] + (extra_args or PASSTHROUGH)
    with md.open("w", encoding="utf-8") as out, err.open("w", encoding="utf-8") as e:
        result = subprocess.run(cmd, cwd=ROOT, stdout=out, stderr=e, text=True, env=CHILD_ENV)
    if result.returncode != 0:
        if advisory:
            print(f"   advisory findings: {name} (exit {result.returncode}) - not gating")
        else:
            failed = 1
            print(f"   FAILED: {name} (exit {result.returncode})")
    if err.stat().st_size == 0:
        err.unlink()


_gating, _advisory = audits_from_shell()
for a in _gating:
    run(a, ROOT / "tools" / "audit" / f"audit_{a}.py")

for a in _advisory:
    run(a, ROOT / "tools" / "audit" / f"audit_{a}.py", advisory=True)

for name, path in EXTRAS:
    run(name, path)

# audit_unconverted_templates writes its OWN report with --write; its stdout is only a
# short summary, so routing it through run() would clobber the real report.
print("== unconverted_templates")
_r = subprocess.run([PYTHON, str(ROOT / "tools" / "audit" / "audit_unconverted_templates.py"),
                     "--write"] + (["--force-latest"] if FORCE_LATEST else []),
                    cwd=ROOT, capture_output=True, text=True, env=CHILD_ENV)
if _r.returncode != 0:
    failed = 1
    print(f"   FAILED: unconverted_templates (exit {_r.returncode})")

# Staleness gate for the mandatory recurring audits (docs/audit/periodic.json).
# --warn-only: this suite is the PER-COMMIT gate, so a late scheduled scan must
# not turn it red for a reason unrelated to the commit being made. See
# docs/audit/PERIODIC.md.
run("periodic_freshness", ROOT / "tools" / "audit" / "audit_periodic_freshness.py",
    ["--warn-only"])

# docs/factions/MATRIX.md is tracked too, so an incomplete run diverts it alongside
# the reports rather than overwriting it.
MATRIX = (ROOT / "docs" / "factions" / "MATRIX.md"
          if _dest == environment.LATEST else OUT / "MATRIX.md")

for name, script, dest in [
    ("gen_damage_matrix", ROOT / "tools" / "audit" / "gen_damage_matrix.py", OUT / "damage_matrix.md"),
    ("gen_rename_maps", ROOT / "tools" / "audit" / "gen_rename_maps.py", OUT / "naming.md"),
    ("gen_faction_matrix", ROOT / "tools" / "audit" / "gen_faction_matrix.py", MATRIX),
]:
    print(f"== {name}")
    with dest.open("w", encoding="utf-8") as out:
        result = subprocess.run([PYTHON, str(script)], cwd=ROOT, stdout=out, text=True, env=CHILD_ENV)
    if result.returncode != 0:
        failed = 1
        print(f"   FAILED: {name} (exit {result.returncode})")

print(f"reports in {OUT}/ ; matrix in {MATRIX}")
sys.exit(failed)
