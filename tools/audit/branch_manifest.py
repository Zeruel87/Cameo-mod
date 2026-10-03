#!/usr/bin/env python3
"""Which remote branches are fully landed on master, and which still hold work nobody has merged.

Maintainer, 2026-09-23: *"I think it's because of those devin agents that abruptly ended and never
finished their work on some sort of branch ... make sure master/origin ... is always up to date and
we are not creating more chaos in the repository."* The repository had 156 remote branches and 60
worktrees; the 2026-09-13 manifest was written by hand and had gone stale.

Decided by CONTENT, not by commit ancestry. Squash merges give every contributing branch commits
that master never contains, so `git branch --merged` and `git cherry` call almost everything
"unmerged". Instead, for every file a branch changed since it left master:

  * its final state on the branch is compared with EVERY state that path has ever had on master
    (`git log --raw` over master's whole history, blobs only - nothing is checked out);
  * a file the branch deleted counts as landed when master does not have it either.

A branch is LANDED only when every file it touched passes. Anything else is UNLANDED and listed
with the files that exist nowhere on master - that is the work that would be lost. Every error
biases towards keeping a branch: a state master only reached inside a merge resolution is not
seen, so such a branch is reported UNLANDED, never the reverse.

A branch with an OPEN pull request, or checked out in any local worktree, is never deletable,
whatever its content says.

    python tools/audit/branch_manifest.py                 # summary
    python tools/audit/branch_manifest.py --write         # also writes docs/BRANCH_MANIFEST.md
    python tools/audit/branch_manifest.py --deletable     # one branch name per line (for review)
"""
from __future__ import annotations

import argparse
import collections
import datetime
import json
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
OUT = ROOT / "docs" / "BRANCH_MANIFEST.md"
REPO = "cameo-mod/Cameo-mod"
MASTER = "origin/master"
NULL = "0" * 40


def git(*args: str) -> str:
    return subprocess.run(["git", "-C", str(ROOT), "-c", "core.quotepath=off", *args], capture_output=True, text=True,
                          encoding="utf-8", errors="replace", check=True).stdout


def master_history() -> dict[str, set[str]]:
    """path -> every blob that path has held on master, across its whole history."""
    seen: dict[str, set[str]] = collections.defaultdict(set)
    for line in git("log", "--raw", "--no-abbrev", "--no-renames", "--format=", MASTER).splitlines():
        if not line.startswith(":"):
            continue
        meta, _, path = line.partition("\t")
        blob = meta.split()[3]
        if blob != NULL:
            seen[path].add(blob)
    # The current tree too: a file that has not changed since the root commit has no log entry.
    for line in git("ls-tree", "-r", MASTER).splitlines():
        meta, _, path = line.partition("\t")
        seen[path].add(meta.split()[2])
    return seen


def open_pr_heads() -> dict[str, int]:
    try:
        out = subprocess.run(["gh", "pr", "list", "--repo", REPO, "--state", "open", "--limit", "200",
                              "--json", "number,headRefName"], capture_output=True, text=True,
                             encoding="utf-8", check=True).stdout
    except (OSError, subprocess.CalledProcessError) as ex:
        sys.exit(f"cannot list open PRs ({ex}); refusing to classify without them")
    return {p["headRefName"]: p["number"] for p in json.loads(out)}


def worktree_branches() -> set[str]:
    return {line.split("refs/heads/", 1)[1] for line in git("worktree", "list", "--porcelain").splitlines()
            if line.startswith("branch refs/heads/")}


def classify() -> list[dict]:
    history = master_history()
    master_tree = set(git("ls-tree", "-r", "--name-only", MASTER).splitlines())
    prs, active = open_pr_heads(), worktree_branches()
    rows = []
    refs = git("for-each-ref", "refs/remotes/origin", "--format=%(refname:short)|%(objectname)|%(committerdate:short)|%(subject)")
    for line in refs.splitlines():
        ref, tip, date, subject = line.split("|", 3)
        name = ref.removeprefix("origin/")
        if name in ("HEAD", "master") or ref == "origin":
            continue
        base = git("merge-base", MASTER, ref).strip()
        unlanded = []
        touched = git("diff", "--no-renames", "--name-status", base, ref).splitlines()
        tree = {}
        if touched:  # one ls-tree per branch, not one rev-parse per file
            for t in git("ls-tree", "-r", ref).splitlines():
                meta, _, path = t.partition("\t")
                tree[path] = meta.split()[2]
        for entry in touched:
            status, _, path = entry.partition("\t")
            if status.startswith("D"):
                if path in master_tree:
                    unlanded.append(path)
                continue
            if tree.get(path) not in history.get(path, ()):
                unlanded.append(path)
        if name in prs:
            verdict = f"OPEN PR #{prs[name]}"
        elif name in active:
            verdict = "ACTIVE (checked out in a worktree)"
        elif unlanded:
            verdict = "UNLANDED"
        else:
            verdict = "LANDED"
        behind = int(git("rev-list", "--count", f"{ref}..{MASTER}").strip())
        rows.append({"branch": name, "tip": tip, "date": date, "subject": subject, "touched": len(touched),
                     "unlanded": unlanded, "behind": behind, "verdict": verdict})
    return sorted(rows, key=lambda r: (r["verdict"], r["branch"]))


def render(rows: list[dict]) -> str:
    today = datetime.date.today().isoformat()
    master = git("rev-parse", "--short", MASTER).strip()
    by = collections.defaultdict(list)
    for r in rows:
        by["OPEN PR" if r["verdict"].startswith("OPEN PR") else r["verdict"].split(" (")[0]].append(r)
    out = [f"# Branch manifest — {today}", "",
           f"Generated by `tools/audit/branch_manifest.py` against master `{master}` — **do not edit by hand**.",
           "Decided by CONTENT: a branch is LANDED when the final state of every file it changed exists somewhere",
           "in master's history (squash merges make commit ancestry useless). Tip hashes are kept so any deleted",
           "branch can be restored: `git push origin <tip>:refs/heads/<branch>`.", "",
           f"**{len(rows)} remote branches:** " + ", ".join(f"{k} {len(v)}" for k, v in sorted(by.items())), ""]
    for key, title in (("UNLANDED", "UNLANDED — work that exists nowhere on master (maintainer decides)"),
                       ("OPEN PR", "OPEN PULL REQUEST — kept"),
                       ("ACTIVE", "ACTIVE — checked out in a local worktree, kept"),
                       ("LANDED", "LANDED — every change is on master (safe to delete)")):
        if not by.get(key):
            continue
        out += [f"## {title} — {len(by[key])}", "", "| branch | tip | last commit | behind master | files unlanded | last subject |",
                "|---|---|---|---:|---:|---|"]
        for r in by[key]:
            subj = r["subject"].replace("|", "\\|")[:80]
            out.append(f"| `{r['branch']}` | `{r['tip'][:10]}` | {r['date']} | {r['behind']} | "
                       f"{len(r['unlanded'])} of {r['touched']} | {subj} |")
        out.append("")
    return "\n".join(out) + "\n"


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--write", action="store_true", help="write docs/BRANCH_MANIFEST.md")
    ap.add_argument("--deletable", action="store_true", help="print only the LANDED branch names")
    ap.add_argument("--json", type=pathlib.Path, help="also dump the rows as JSON here")
    args = ap.parse_args()
    rows = classify()
    if args.json:
        args.json.write_text(json.dumps(rows, indent=1), encoding="utf-8")
    if args.deletable:
        print("\n".join(r["branch"] for r in rows if r["verdict"] == "LANDED"))
        return 0
    counts = collections.Counter(r["verdict"].split(" (")[0] if not r["verdict"].startswith("OPEN") else "OPEN PR"
                                 for r in rows)
    print(f"{len(rows)} remote branches: {dict(counts)}")
    if args.write:
        OUT.write_text(render(rows), encoding="utf-8", newline="\n")
        print(f"wrote {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
