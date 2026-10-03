#!/usr/bin/env python3
"""audit_security.py — repo security scan (no network required).

Cameo ships build tooling, launchers and a mod that other people run, so the
attack surface is: what the scripts execute, what they download, and what
credentials end up committed.

Findings:

S1 (BLOCKING) — committed credential shapes: private keys, AWS keys, GitHub /
    Slack / Discord tokens, ``password =``-style literals.
S2 (BLOCKING) — code execution from data: ``eval`` / ``exec`` /
    ``pickle.load`` / ``yaml.load`` without ``SafeLoader`` /
    ``subprocess(..., shell=True)`` with a non-literal command.
S3 — plaintext ``http://`` downloads in scripts (a MITM can replace an engine
    or asset payload); GitHub/nuget URLs must be https.
S4 — pinned-by-tag or unpinned third-party GitHub Actions
    (``uses: owner/action@main``) — a moved tag re-defines CI.
S5 — NuGet ``PackageReference`` without a pinned version, or a floating
    version range (``*``, ``$(...)``-less wildcards).
S6 — installer download with no integrity field: a package in
    ``mods/cameo-content/installer/downloads.yaml`` that has a ``URL``/``MirrorList``
    but no ``SHA1``/``SHA256``, so whatever the mirror serves is unpacked into
    the player's content directory unverified.

Exit code 1 when a count rises above its baseline (ratchet).

Usage: python tools/audit/audit_security.py
"""

from __future__ import annotations

import ast
import pathlib
import re
import sys

from miniyaml import find_repo_root, load
from report import h1, h2, relpath, table

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

SKIP_PARTS = ("engine", ".git", "__pycache__", "archive", "bits", "maps", "docs")
TEXT_SUFFIXES = (".py", ".sh", ".ps1", ".cmd", ".bat", ".yml", ".yaml",
                 ".csproj", ".props", ".config", ".json", ".cs")

# Ratchet baselines, measured 2026-08-10. Lower as findings are fixed.
BASELINES = {"S1": 0, "S2": 0, "S3": 0, "S4": 0, "S5": 0, "S6": 0}

SECRET_PATTERNS = (
    ("private key block", re.compile(r"-----BEGIN (?:RSA |OPENSSH |EC |PGP )?PRIVATE KEY-----")),
    ("AWS access key id", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("GitHub token", re.compile(r"\bgh[pousr]_[A-Za-z0-9]{36,}\b")),
    ("Slack token", re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{10,}\b")),
    ("Discord bot token", re.compile(r"\b[MNO][A-Za-z\d]{23}\.[\w-]{6}\.[\w-]{27}\b")),
    ("hardcoded password", re.compile(
        r"(?i)\b(?:password|passwd|secret|api_key|apikey|token)\s*[=:]\s*"
        r"['\"][^'\"\s${}<>]{8,}['\"]")),
)

HTTP_URL = re.compile(r"http://(?!localhost|127\.0\.0\.1|0\.0\.0\.0|schemas?\.|www\.w3\.org)"
                      r"[A-Za-z0-9.-]+")
ACTION_USES = re.compile(r"^\s*uses:\s*([^\s#]+)")
PACKAGE_REF = re.compile(r"<PackageReference\s+([^>]*)>")
DOWNLOADS_YAML = "mods/cameo-content/installer/downloads.yaml"


def iter_files(root: pathlib.Path):
    for path in sorted(root.rglob("*")):
        if not path.is_file() or path.suffix not in TEXT_SUFFIXES:
            continue
        rel_parts = path.relative_to(root).parts
        if any(part in SKIP_PARTS for part in rel_parts):
            continue
        # A top-level directory containing `.git` (file or dir) is a nested
        # checkout — a linked worktree like wt_base/ — not repo content.
        # Scanning it double-counts every finding.
        if len(rel_parts) > 1 and (root / rel_parts[0] / ".git").exists():
            continue
        yield path


def scan_python_exec(rel: str, source: str) -> list[list[str]]:
    rows: list[list[str]] = []
    try:
        tree = ast.parse(source, filename=rel)
    except SyntaxError:
        return rows

    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        name = ""
        if isinstance(func, ast.Name):
            name = func.id
        elif isinstance(func, ast.Attribute):
            base = func.value.id if isinstance(func.value, ast.Name) else ""
            name = f"{base}.{func.attr}" if base else func.attr

        if name in ("eval", "exec"):
            rows.append([rel, str(node.lineno), f"`{name}()`"])
        elif name in ("pickle.load", "pickle.loads"):
            rows.append([rel, str(node.lineno), "`pickle` deserialisation"])
        elif name in ("yaml.load", "yaml.load_all"):
            safe = any(kw.arg == "Loader" for kw in node.keywords) or len(node.args) > 1
            if not safe:
                rows.append([rel, str(node.lineno), "`yaml.load()` without Loader="])
        else:
            shell = next((kw for kw in node.keywords
                          if kw.arg == "shell" and isinstance(kw.value, ast.Constant)
                          and kw.value.value is True), None)
            if shell is not None and node.args and not isinstance(node.args[0], ast.Constant):
                rows.append([rel, str(node.lineno),
                             f"`{name}(shell=True)` with a built-up command"])
    return rows


def scan_downloads(root: pathlib.Path) -> list[list[str]]:
    """Installer packages that are fetched without an integrity field."""
    path = root / DOWNLOADS_YAML
    if not path.exists():
        return []

    rows: list[list[str]] = []
    for top in load(path):
        keys = {child.key for child in top.children}
        if not keys & {"URL", "MirrorList"}:
            continue
        if keys & {"SHA1", "SHA256"}:
            continue
        rows.append([DOWNLOADS_YAML, str(top.line),
                     f"{top.key}: no SHA1/SHA256"])
    return rows


def main() -> int:
    root = find_repo_root()
    rows: dict[str, list[list[str]]] = {k: [] for k in BASELINES}
    scanned = 0

    for path in iter_files(root):
        scanned += 1
        rel = relpath(str(path), root)
        text = path.read_text(encoding="utf-8", errors="replace")
        lines = text.splitlines()

        for label, pattern in SECRET_PATTERNS:
            for match in pattern.finditer(text):
                line = text.count("\n", 0, match.start()) + 1
                rows["S1"].append([rel, str(line), label])

        if path.suffix == ".py":
            rows["S2"].extend(scan_python_exec(rel, text))

        for i, line in enumerate(lines, 1):
            if HTTP_URL.search(line) and not line.lstrip().startswith(("#", "//", "*")):
                rows["S3"].append([rel, str(i), line.strip()[:120]])
            if path.suffix in (".yml", ".yaml") and ".github" in rel:
                m = ACTION_USES.match(line)
                if m and "/" in m.group(1) and "@" in m.group(1):
                    ref = m.group(1).split("@")[1]
                    owner = m.group(1).split("/")[0]
                    if owner not in ("actions", "github") and not re.fullmatch(r"[0-9a-f]{40}", ref):
                        rows["S4"].append([rel, str(i), m.group(1)])
            if path.suffix in (".csproj", ".props"):
                for attrs in PACKAGE_REF.findall(line):
                    version = re.search(r'Version="([^"]*)"', attrs)
                    include = re.search(r'Include="([^"]*)"', attrs)
                    if version is None:
                        rows["S5"].append([rel, str(i),
                                           f"{include.group(1) if include else '?'}: no Version"])
                    elif "*" in version.group(1):
                        rows["S5"].append([rel, str(i),
                                           f"{include.group(1) if include else '?'}: "
                                           f"floating {version.group(1)}"])

    rows["S6"].extend(scan_downloads(root))

    print(h1("audit_security — credentials, code execution, supply chain"))
    print(f"Files scanned: **{scanned}**\n")
    print(table(["code", "meaning", "count", "baseline"], [
        ["S1", "committed credential shapes", len(rows["S1"]), BASELINES["S1"]],
        ["S2", "code execution from data", len(rows["S2"]), BASELINES["S2"]],
        ["S3", "plaintext http:// download", len(rows["S3"]), BASELINES["S3"]],
        ["S4", "unpinned third-party GitHub Action", len(rows["S4"]), BASELINES["S4"]],
        ["S5", "unpinned/floating NuGet package", len(rows["S5"]), BASELINES["S5"]],
        ["S6", "installer download without SHA", len(rows["S6"]), BASELINES["S6"]],
    ]))

    for code in ("S1", "S2", "S3", "S4", "S5", "S6"):
        print(h2(f"{code} — {len(rows[code])} finding(s)"))
        print(table(["file", "line", "detail"], rows[code]))

    print(h2("Not covered here"))
    print("- Known-vulnerable NuGet/npm advisories: needs network; run\n"
          "  `dotnet list CameoMod.sln package --vulnerable --include-transitive`\n"
          "  as part of the periodic security run and paste the output into the\n"
          "  evidence file.\n")

    regressions = [f"{code}: {len(rows[code])} > baseline {BASELINES[code]}"
                   for code in BASELINES if len(rows[code]) > BASELINES[code]]
    if regressions:
        print(h2("FAIL"))
        for line in regressions:
            print(f"- {line}")
        print()
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
