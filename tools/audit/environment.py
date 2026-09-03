#!/usr/bin/env python3
"""environment.py — can THIS tree produce a truthful audit evidence set?

`docs/audit/latest/` is tracked, and several audits read things that are not in this
repository. Run the suite in a tree that is missing them and the reports come back
*smaller* rather than *failing* — the audit reports what it can see and says PASS.
Commit that and the tracked evidence silently loses real findings:

    audit_unique_traits         125 trait types -> 11      (needs engine/**.cs)
    audit_dead_warhead_fields   27071 nodes     -> 7014     (needs engine/**.cs)
    audit_fluent                5235 messages   -> 3640     (needs engine/ fluent)
    audit_recent_changes        663 files       -> 31523    (shallow clone: the
                                                             boundary commit looks
                                                             like it touched the world)

Those numbers are measured, not hypothetical: every one of them was produced by a
cloud container in August 2026 and came within one `git add` of being committed over
the true values.

So the runners ask here first. A tree that cannot see everything still runs the whole
suite — the answers are useful — but it writes to `docs/audit/degraded/` (untracked)
instead of over the tracked set, and says why.

`--force-latest` overrides, for the case where you genuinely want a partial refresh and
have read the diff.

This module has no dependencies beyond the standard library and never imports the
audit scripts, so it is safe to call before anything else in the run.
"""
from __future__ import annotations

import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]

LATEST = "docs/audit/latest"
DEGRADED = "docs/audit/degraded"

# Assemblies audit_unique_traits and audit_dead_warhead_fields walk for `public` fields
# and `.Trait<T>()` calls. engine/ is a BUILD OUTPUT — .gitignored, not part of this
# repo, recreated by `make all` (CLAUDE.md rule 7) — so a fresh clone never has it.
ENGINE_ASSEMBLIES = (
    "engine/OpenRA.Game",
    "engine/OpenRA.Mods.Common",
    "engine/OpenRA.Mods.AS",
    # ⚠ CA is vendored at the REPO ROOT, like OpenRA.Mods.Cameo — it is not part of the
    # engine and `engine/OpenRA.Mods.CA` can never exist. Pointing there made incomplete()
    # return a reason on EVERY machine, so every run diverted to degraded/ and the tracked
    # docs/audit/latest/ could never be rewritten by anyone. (Found 2026-08-23.)
    "OpenRA.Mods.CA",
    "engine/OpenRA.Mods.Cnc",
    "engine/OpenRA.Mods.D2k",
)


def incomplete(root: pathlib.Path | None = None) -> list[str]:
    """Reasons this tree cannot faithfully rewrite the tracked evidence set.

    Empty list = complete environment. Each entry names the defect AND the audits it
    degrades, because "your environment is incomplete" on its own tells nobody what to
    distrust.
    """
    root = root or ROOT
    reasons: list[str] = []

    missing = [a for a in ENGINE_ASSEMBLIES if not any((root / a).glob("**/*.cs"))]
    if missing:
        reasons.append(
            f"engine/ C# sources absent ({len(missing)} of {len(ENGINE_ASSEMBLIES)} "
            f"assemblies, e.g. {missing[0]}) — audit_unique_traits, "
            "audit_dead_warhead_fields and audit_fluent under-report instead of failing. "
            "`make.cmd all` populates engine/."
        )

    if (root / ".git" / "shallow").exists():
        reasons.append(
            "shallow git clone — audit_recent_changes reads the grafted boundary commit "
            "as touching every file in the tree. `git fetch --unshallow` fixes it."
        )

    return reasons


def out_dir(force_latest: bool = False) -> tuple[str, list[str]]:
    """Where this run may write, and why. Returns (path relative to root, reasons)."""
    reasons = incomplete()
    if reasons and not force_latest:
        return DEGRADED, reasons
    return LATEST, reasons


def banner(dest: str, reasons: list[str]) -> str:
    if not reasons:
        return ""
    lines = ["", "=" * 78]
    if dest == DEGRADED:
        lines.append("INCOMPLETE ENVIRONMENT — writing to %s/, NOT %s/" % (DEGRADED, LATEST))
    else:
        lines.append("INCOMPLETE ENVIRONMENT — --force-latest given, writing %s/ anyway" % LATEST)
    for r in reasons:
        lines.append("  * " + r)
    lines.append("Reports here are still useful; they are just not the tracked evidence.")
    lines.append("=" * 78)
    lines.append("")
    return "\n".join(lines)


if __name__ == "__main__":
    import sys

    force = "--force-latest" in sys.argv
    dest, why = out_dir(force)
    if "--print-dir" in sys.argv:
        print(dest)
        raise SystemExit(0)
    print(banner(dest, why) or "complete environment — %s/ is writable evidence" % LATEST)
    raise SystemExit(1 if why else 0)
