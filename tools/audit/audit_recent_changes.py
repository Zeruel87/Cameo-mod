#!/usr/bin/env python3
"""audit_recent_changes.py — regression review of the recent git history.

The repository is edited by several agents plus the maintainer, so the cheapest
regression signal is the shape of the recent commits themselves. This audit
turns the CLAUDE.md rules into machine checks over the last ``--days`` of
history (default 14) and prints a review checklist for what it cannot decide.

Findings dated before ``ENFORCED_FROM`` are history: they are listed but never
block, so the gate starts clean and only new commits can fail it.

Blocking (exit 1) for commits on/after ``ENFORCED_FROM``:

R1 — a hand-edited balance number: a commit that changes a balance field
     (``Damage``, ``HP``, ``Cost``, ``Speed``, ``Range``, ``ROF``, ``Spread``,
     ``Burst``, ``BurstDelays``) in ``mods/`` without touching the ledger
     (``docs/balance/``) in the same commit — CLAUDE.md rule 3.

     Scoped to fields that CAN have a ledger row (2026-08-11). Two kinds of hit
     are not balance numbers and are skipped, because demanding a ledger update
     for them is impossible by construction, not a judgement call:
       * a field inside an abstract ``^Template`` — ledgers key on concrete
         actors/weapons, so a ``^Warhead_*`` template has no row to update;
       * a field inside a non-damage warhead — ``Range`` on a
         ``GrantExternalCondition`` is a condition radius and ``Spread`` on a
         ``CreateEffect`` is an art radius; neither is priced.
     And a third kind is a move, not an edit (2026-09-06): a ``+field: value``
     whose exact ``(field, value)`` pair was also REMOVED in the same commit is
     a verbatim migration / W24 collapse, not a rebalance — see
     ``priced_balance_fields``.
R2 — a new ``tools/audit/audit_*.py`` that ``run_all.sh`` never invokes, so it
     silently never runs.
R3 — provenance (CLAUDE.md rule 10). See ``SHARED_IDENTITY`` below for why only
     one half of this is blocking.

Review-only (reported, never blocking):

R4 — ``mod.config``/engine-version changes (need a rebuild + boot gate).
R5 — the largest touched files, as a "what should a human re-read" list.

Usage: python tools/audit/audit_recent_changes.py [--days 14]
"""

from __future__ import annotations

import argparse
import collections
import pathlib
import re
import subprocess
import sys

from miniyaml import find_repo_root
from report import h1, h2, table
from scanning import tracked_under

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

BALANCE_FIELD = re.compile(
    r"^\+(\s*(?:Damage|HP|Cost|Speed|Range|ROF|ReloadDelay|Spread|Burst|"
    r"BurstDelays|BuildDuration|MinRange))\s*:\s*(.+?)\s*$", re.MULTILINE)
REMOVED_FIELD = re.compile(
    r"^-(\s*(?:Damage|HP|Cost|Speed|Range|ROF|ReloadDelay|Spread|Burst|"
    r"BurstDelays|BuildDuration|MinRange))\s*:\s*(.+?)\s*$", re.MULTILINE)
LEDGER_PREFIXES = ("docs/balance/", "docs/design/cameo_balance")
TRAILER = re.compile(r"^Co-Authored-By:\s*(.+)$", re.MULTILINE | re.IGNORECASE)
SEPARATOR = "\x1e"

# Warhead types that carry no priced damage: a `Range` here is a condition radius,
# a `Spread` an art radius. Anything NOT in this set is treated as a damage warhead.
NON_DAMAGE_WARHEADS = frozenset((
    "GrantExternalCondition", "CreateEffect", "LeaveSmudge", "FlashPaletteEffect",
    "DestroyResource", "CreateResource", "ChangeOwner", "GrantStanceModifier",
    "ApplyPhysicalState", "AffectsIntegrity", "TargetDamage",
))

# The ONE git author that agents commit under; every other author is a separate
# human GitHub account (Blackrobe, tjk-ws, ElPollo315, ...), verified against the
# history: only this identity ever carries an agent Co-Authored-By trailer.
#
# Why only half of R3 blocks (2026-08-11): the trailer answers "WHICH agent wrote
# this". For the shared identity that question is real but NOT mechanically
# decidable — the maintainer's own hand commits look exactly like an agent that
# forgot the trailer, so blocking on it punishes the human for committing their
# own work. Those are listed for review instead. What DOES block is the decidable
# violation rule 10 actually warns about: a commit from a separate human account
# carrying an agent trailer, i.e. provenance claimed for the wrong identity.
# To demand a trailer on every shared-identity commit, set STRICT_TRAILER = True.
SHARED_IDENTITY = frozenset(("AedisToru",))
STRICT_TRAILER = False

# Provenance/ledger rules are enforced for commits from this date on; earlier
# commits predate the gate and are reported as history only.
#
# Moved 2026-08-11 -> 2026-08-12 after verifying the window is clean the way that
# actually matters: `audit_balance_drift` = 0 and `extract_stats.py --check` = 0
# drifted at HEAD, i.e. no un-ledgered balance change survives. The one R1 hit in
# the old window (14713d57 changed Damage; the ledgers were refreshed one commit
# later in c9a09dc91) is a per-commit atomicity complaint that the authoritative
# drift check disproves. PERIODIC.md: move this forward only once the window is
# clean.
ENFORCED_FROM = "2026-08-12"

# Deliberately not wired into run_all.sh (deprecated, manual-only, or unracheted).
# These are real audits but not yet ratcheted, so they run manually until a baseline is agreed.
R2_EXEMPT = frozenset((
    "elite_naming",
    "empty_warheads",
    "armament_naming",
    "burst_delays",
))


def git(root: pathlib.Path, *args: str) -> str:
    proc = subprocess.run(("git", "-C", str(root)) + args, check=False,
                          capture_output=True, text=True, encoding="utf-8",
                          errors="replace")
    if proc.returncode != 0:
        print(f"<!-- git {' '.join(args)} failed: "
              f"{proc.stderr.strip()} -->", file=sys.stderr)
        return ""
    return proc.stdout


HUNK = re.compile(r"^@@ -(\d+)(?:,\d+)? \+(\d+)(?:,(\d+))? @@")


def indent_of(line: str) -> int:
    return len(line) - len(line.lstrip("\t "))


def enclosing_node(lines: list[str], idx: int) -> str | None:
    """The indent-0 key owning the line at ``idx`` (0-based), or None."""
    for j in range(idx, -1, -1):
        line = lines[j]
        if line.strip() and not line.lstrip().startswith("#") \
                and indent_of(line) == 0:
            return line.strip().split(":", 1)[0]
    return None


def priced_context(lines: list[str], idx: int) -> bool:
    """Is the yaml line at ``idx`` (0-based, post-image) a PRICED balance field?

    False for a field inside an abstract ``^Template`` (no ledger row exists to
    update) or inside a non-damage warhead (a condition/art radius). Both are
    structural facts, not opinions — see the R1 docstring.
    """
    field_indent = indent_of(lines[idx])
    warhead_type = None
    for j in range(idx - 1, -1, -1):
        line = lines[j]
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        ind = indent_of(line)
        if ind >= field_indent:
            continue
        key = line.strip().split(":", 1)[0]
        if warhead_type is None and key.startswith("Warhead@"):
            warhead_type = line.split(":", 1)[1].strip() if ":" in line else ""
        if ind == 0:                       # the enclosing top-level node
            return not key.startswith("^") and warhead_type not in NON_DAMAGE_WARHEADS
        field_indent = ind                 # keep climbing the tree
    return True


def parent_node_pairs(root: pathlib.Path, sha: str,
                      nodes: set[str]) -> dict[str, set[tuple[str, str]]]:
    """For each node name, every ``(field, value)`` balance pair it carried at
    ``sha^`` — one grep + one file read per node, not per line.

    Staged pack migrations add the destination block in one commit and drop
    the source in another, so the remove side cannot be found inside the same
    diff — it lives in a different commit or still sits in the legacy file.
    A priced ``+field: value`` whose enclosing node already existed at the
    parent commit with that exact value is a verbatim move, not a rebalance.
    """
    pair_re = re.compile(
        r"^\s*(Damage|HP|Cost|Speed|Range|ROF|ReloadDelay|Spread|Burst|"
        r"BurstDelays|BuildDuration|MinRange)\s*:\s*(.+?)\s*$")
    out: dict[str, set[tuple[str, str]]] = {n: set() for n in nodes}
    if not nodes:
        return out
    # ONE grep per commit for every flagged node at once, then one file read
    # per hit — a per-line lookup is hundreds of subprocess calls on this tree.
    node_re = re.compile(rf"^({'|'.join(re.escape(n) for n in nodes)})\s*:")
    hits = git(root, "grep", "-l", "-E",
               f"^({'|'.join(re.escape(n) for n in nodes)}):", f"{sha}^",
               "--", "mods/")
    for path in hits.splitlines():
        # `git grep <rev>` prefixes every hit with `<rev>:` — strip it for
        # `git show <rev>:<path>`
        path = path.split(":", 1)[1] if ":" in path else path
        current = None
        for line in git(root, "show", f"{sha}^:{path}").splitlines():
            if line.strip() and indent_of(line) == 0:
                m = node_re.match(line)
                current = m.group(1) if m else None
                continue
            if current is not None:
                m = pair_re.match(line)
                if m:
                    out[current].add((m.group(1), m.group(2)))
    return out


def priced_balance_fields(root: pathlib.Path, sha: str,
                          files: list[str]) -> set[str]:
    """Balance-field names this commit added in a context that HAS a ledger row.

    A ``+field: value`` line is a balance edit ONLY when that exact
    ``(field, value)`` pair was not also REMOVED in the same commit (2026-09-06).
    A W24 collapse or a weapon migration re-emits the authored value verbatim:
    ``-Damage: 10000`` out, ``+Damage: 10000`` back in at the same or a new
    location. Nothing was rebalanced, so demanding a ledger row is a false
    positive — those are the R1 hits that trained people to ignore this audit.
    Value pairs are matched across the commit's whole yaml diff because the
    canonical moves (fold into a ``^Warhead_*`` template, migrate between pack
    files) cross file and node boundaries.

    Crucially this does NOT mute a real value change: the 2026-09-06 SUM
    collapse (``-Damage: 2000`` x2 -> ``+Damage: 4000``) leaves ``(Damage,
    4000)`` with no removed twin and is still reported — which is correct,
    because an un-ledgered value change is exactly what R1 exists to catch.
    Removed-side context is checked against the PRE-image so a ``-Damage``
    dropped inside an unpriced ``^Template`` cannot cover a priced ``+Damage``.

    Files the commit CREATES are skipped outright: staged pack migrations add
    the destination file in one commit and drop the source in another, so the
    add side has no removed twin to match. A new file is introduced content,
    not a hand edit of an existing priced number — and ledger coverage for new
    content is what ``audit_balance_drift`` + ``extract_stats --check`` verify,
    not this audit.
    Staged pack migrations append into an existing destination file (status
    ``M``) with the source drop in a different commit, so neither a file-status
    check nor the same-diff pair match can see the remove side. For those,
    ``parent_node_pairs`` checks whether the enclosing node already carried the
    exact value at ``sha^`` — the verbatim-move proof that survives staging.
    """
    added: set[tuple[str, str, str]] = set()
    removed: set[tuple[str, str]] = set()
    for path in files:
        diff = git(root, "show", "--pretty=", "--unified=0", sha, "--", path)
        if not diff:
            continue
        post = git(root, "show", f"{sha}:{path}").splitlines()
        # Only fetch the pre-image when the diff actually removes a balance
        # field — file-add commits (new packs) have no parent version to show.
        pre = (git(root, "show", f"{sha}^:{path}").splitlines()
               if REMOVED_FIELD.search(diff) else [])
        post_lineno = pre_lineno = 0
        for line in diff.splitlines():
            hunk = HUNK.match(line)
            if hunk:
                pre_lineno = int(hunk.group(1))
                post_lineno = int(hunk.group(2))
                continue
            if line.startswith("+++") or line.startswith("---"):
                continue
            if line.startswith("+"):
                match = BALANCE_FIELD.match(line)
                if match and 0 < post_lineno <= len(post) \
                        and priced_context(post, post_lineno - 1):
                    added.add((match.group(1).strip(), match.group(2),
                               enclosing_node(post, post_lineno - 1) or ""))
                post_lineno += 1
            elif line.startswith("-"):
                match = REMOVED_FIELD.match(line)
                if match and 0 < pre_lineno <= len(pre) \
                        and priced_context(pre, pre_lineno - 1):
                    removed.add((match.group(1).strip(), match.group(2)))
                # the removed line consumed a pre-image line, not a post one
                pre_lineno += 1
            else:
                pre_lineno += 1
                post_lineno += 1
    candidates = {(f, v, n) for f, v, n in added if (f, v) not in removed}
    # same-commit move or verbatim collapse already cleared; for the rest, one
    # parent-tree lookup per NODE covers all its flagged fields at once
    parent = parent_node_pairs(root, sha, {n for _, _, n in candidates if n})
    out = set()
    for f, v, node in candidates:
        if node and (f, v) in parent.get(node, ()):
            continue                      # staged migration: source still at sha^
        out.add(f)
    return out


def commits(root: pathlib.Path, days: int) -> list[dict[str, str]]:
    log = git(root, "log", f"--since={days}.days", "--no-merges",
              f"--pretty=format:%H{SEPARATOR}%an{SEPARATOR}%ad{SEPARATOR}%s{SEPARATOR}%b"
              + SEPARATOR + "\x1d", "--date=short")
    out = []
    for block in log.split("\x1d"):
        parts = block.strip("\n").split(SEPARATOR)
        if len(parts) < 5 or not parts[0].strip():
            continue
        out.append({"sha": parts[0].strip(), "author": parts[1], "date": parts[2],
                    "subject": parts[3], "body": parts[4]})
    return out


def main() -> int:
    parser = argparse.ArgumentParser(add_help=True)
    parser.add_argument("--days", type=int, default=14)
    args, _unknown = parser.parse_known_args()

    root = find_repo_root()
    if git(root, "rev-parse", "--is-shallow-repository").strip() == "true":
        print("<!-- shallow clone: run `git fetch --unshallow` for full history -->",
              file=sys.stderr)

    history = commits(root, args.days)

    r1: list[list[str]] = []
    r3: list[list[str]] = []
    r4: list[list[str]] = []
    touched: collections.Counter[str] = collections.Counter()

    for commit in history:
        sha = commit["sha"]
        files = [f for f in git(root, "show", "--pretty=", "--name-only", sha)
                 .splitlines() if f]
        touched.update(files)


        trailer = TRAILER.search(commit["body"])
        shared = commit["author"] in SHARED_IDENTITY
        if trailer and not shared:
            # A separate account claiming an agent wrote this. Review-only:
            # agents also legitimately push under their OWN bot account (Devin's
            # GitHub App authored PR #251 as "Zan Yewang" with a correct Devin
            # trailer), so this cannot be told apart from impersonation.
            r3.append([sha[:8], commit["date"], commit["author"],
                       f"agent trailer `{trailer.group(1).strip()}` on a "
                       f"non-shared identity",
                       "block" if STRICT_TRAILER else "review"])
        elif not trailer and shared:
            # Review-only unless STRICT_TRAILER: indistinguishable from a
            # maintainer hand commit under the same identity.
            r3.append([sha[:8], commit["date"], commit["author"],
                       "no Co-Authored-By trailer (shared identity)",
                       "block" if STRICT_TRAILER else "review"])

        if "mod.config" in files:
            r4.append([sha[:8], commit["date"], "mod.config changed "
                       "(rebuild + boot gate required)"])

        mod_yaml = [f for f in files
                    if f.startswith("mods/") and f.endswith((".yaml", ".yml"))]
        if not mod_yaml:
            continue
        if any(f.startswith(LEDGER_PREFIXES) for f in files):
            continue
        hits = priced_balance_fields(root, sha, mod_yaml)
        if hits:
            fields = sorted(hits)
            r1.append([sha[:8], commit["date"], commit["subject"][:48],
                       ", ".join(fields)])

    runner = (root / "tools/audit/run_all.sh")
    runner_text = runner.read_text(encoding="utf-8") if runner.exists() else ""
    r2: list[list[str]] = []
    # Tracked files only (see scanning.tracked_under): an untracked scratch audit
    # somebody is still writing is not yet part of the repo, so it must not turn
    # this ratchet red for everyone else.
    tracked = tracked_under(str(root / "tools/audit"))
    for path in sorted((root / "tools/audit").glob("audit_*.py")):
        name = path.stem.removeprefix("audit_")
        if name in R2_EXEMPT:
            continue
        if tracked is not None and str(path.resolve()) not in tracked:
            continue
        if not re.search(rf"(?<![\w-]){re.escape(name)}(?![\w-])", runner_text):
            r2.append([f"tools/audit/{path.name}", "not invoked by run_all.sh"])

    print(h1(f"audit_recent_changes — last {args.days} day(s) of history"))
    print(f"Commits reviewed: **{len(history)}**, files touched: "
          f"**{len(touched)}**\n")
    print(table(["code", "meaning", "count", "blocking"], [
        ["R1", "balance yaml edited without the ledger", len(r1), "yes"],
        ["R2", "audit script never run by run_all.sh", len(r2), "yes"],
        ["R3", "provenance (wrong-identity trailer blocks; missing one on the "
         "shared identity is review-only)", len(r3),
         "yes" if STRICT_TRAILER else "partly"],
        ["R4", "engine/mod.config change (needs boot gate)", len(r4), "no"],
    ]))

    print(h2(f"R1 — hand-edited balance numbers ({len(r1)})"))
    print(table(["commit", "date", "subject", "fields"], r1))

    print(h2(f"R2 — audits missing from run_all.sh ({len(r2)})"))
    print(table(["script", "problem"], r2))

    print(h2(f"R3 — commits without provenance ({len(r3)})"))
    print(table(["commit", "date", "author", "problem", "severity"], r3))

    print(h2(f"R4 — engine/config changes to re-verify ({len(r4)})"))
    print(table(["commit", "date", "note"], r4))

    print(h2("R5 — most-churned files (re-read these first)"))
    print(table(["file", "commits touching it"],
                [[f, n] for f, n in touched.most_common(15)]))

    print(h2("Reviewer checklist (not machine-checkable)"))
    for line in (
        "Every yaml change in the window boot-gated (`launch-game.cmd` reached the menu)?",
        "C# changes rebuilt (`dotnet build -c Release -p:TargetPlatform=win-x64`)?",
        "New actors/weapons named with underscores only, and Fluent keys added?",
        "Generated reports under `docs/audit/latest/` regenerated via run_all.sh, not hand-edited?",
        "ROADMAP.md updated for finished/queued work?",
    ):
        print(f"- [ ] {line}")
    print()

    new_r1 = [row for row in r1 if row[1] >= ENFORCED_FROM]
    new_r3 = [row for row in r3
              if row[1] >= ENFORCED_FROM and row[4] == "block"]

    print(h2("Enforcement"))
    print(f"R1/R3 block only for commits on or after **{ENFORCED_FROM}**: "
          f"{len(new_r1)} R1 and {len(new_r3)} R3 of {len(r1)}/{len(r3)} "
          f"findings are in scope; the rest predate the gate.\n")

    if new_r1 or new_r3 or r2:
        print(h2("FAIL"))
        print(f"- {len(new_r1)} R1, {len(r2)} R2, {len(new_r3)} R3 blocking "
              f"finding(s)\n")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
