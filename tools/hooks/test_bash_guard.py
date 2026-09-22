#!/usr/bin/env python3
"""test_bash_guard.py - prove the boot-gate hook inspects the RIGHT index.

`bash_guard.py` resolved the repository from its own file location, so it always
read the MAIN checkout's index.  Once the fleet moved to `git worktree` (one
repository, many working directories) that was wrong in both directions:

  * false BLOCK - it refused a docs-only commit made in a worktree, because
    another agent had 73 sprite files staged in the main tree;
  * false PASS  - the dangerous one - it would wave through engine content
    committed from a worktree whenever the main index happened to be clean.

This test is SELF-CALIBRATING: it reads each worktree's real index and asserts
the guard's verdict follows THAT index, so it cannot go stale as the trees
change.  The invariant it pins down is the unconditional half of the rule:

    a tree with NO staged engine content must ALWAYS be allowed to commit.

(The converse is deliberately not asserted: engine content staged is allowed
when perf.log shows a boot newer than the staged files, and reimplementing that
freshness check here would just duplicate the thing under test.)

Run: python tools/hooks/test_bash_guard.py     (from anywhere)

NOTE: the trigger phrase is assembled at runtime rather than written literally,
because the guard inspects the whole command line and would otherwise intercept
the very command that runs this test.
"""
import json
import pathlib
import subprocess
import sys

GUARD = pathlib.Path(__file__).resolve().parent / "bash_guard.py"
HERE = pathlib.Path(__file__).resolve().parents[2]
VERB = "git " + "commit"
NL = chr(10)
TAB = chr(9)
ENGINE_PREFIXES = ("mods/", "OpenRA.Mods.Cameo/", "engine/")


def worktrees():
    out = subprocess.run(["git", "-C", str(HERE), "worktree", "list", "--porcelain"],
                         capture_output=True, text=True, timeout=60).stdout
    return [ln[len("worktree "):].strip()
            for ln in out.splitlines() if ln.startswith("worktree ")]


def engine_staged(path):
    r = subprocess.run(["git", "-C", path, "diff", "--cached", "--name-only"],
                       capture_output=True, text=True, timeout=60)
    if r.returncode != 0:
        return None
    return [f for f in r.stdout.split() if f.startswith(ENGINE_PREFIXES)]


def verdict(cwd, cmd):
    r = subprocess.run([sys.executable, str(GUARD)],
                       input=json.dumps({"cwd": cwd, "tool_input": {"command": cmd}}),
                       capture_output=True, text=True, timeout=60)
    return "DENY" if r.stdout.strip() else "ALLOW"


def removal_node_rule():
    """Rule 4: deleting a `-Key@X:` removal node needs RESOLVE-VERIFIED evidence.

    Built in a throwaway repo with the yaml OUTSIDE mods/, so the boot gate cannot
    fire and rule 4 is tested in isolation.
    """
    import os
    import shutil
    import tempfile
    wt = pathlib.Path(tempfile.mkdtemp(prefix="cameo_guard_"))
    try:
        (wt / "docs").mkdir()
        def run(*a):
            return subprocess.run(a, cwd=wt, capture_output=True, text=True, timeout=60)
        run("git", "init", "-q")
        run("git", "config", "user.email", "t@t")
        run("git", "config", "user.name", "t")
        f = "docs/w.yaml"
        p = wt / f
        def yaml(*rows):
            return NL.join(rows) + NL

        p.write_text(yaml("Foo:", TAB + "-Warhead@Bullet_Light:",
                          TAB + "Warhead@X: SpreadDamage"), encoding="utf-8")
        run("git", "add", f)
        run("git", "commit", "-qm", "base")

        p.write_text(yaml("Foo:", TAB + "Warhead@X: SpreadDamage"), encoding="utf-8")
        run("git", "add", f)
        cases = [
            ("removal deleted, no evidence",
             VERB + " -m 'cleanup stale nodes'", "DENY"),
            ("removal deleted, RESOLVE-VERIFIED",
             VERB + " -m 'cleanup RESOLVE-VERIFIED: 5 chains'", "ALLOW"),
        ]
        bad = 0
        for name, cmd, expect in cases:
            got = verdict(str(wt), cmd)
            ok = got == expect
            bad += not ok
            print(f"  [{'ok  ' if ok else 'FAIL'}] {name:34s} "
                  f"expect={expect:5s} got={got}")

        run("git", "checkout", "--", f)
        p.write_text(yaml("Foo:", TAB + "-Warhead@Bullet_Light:",
                          TAB + "Warhead@X: SpreadDamage",
                          TAB + "Warhead@Y: SpreadDamage"), encoding="utf-8")
        run("git", "add", f)
        got = verdict(str(wt), VERB + " -m 'add a warhead'")
        ok = got == "ALLOW"
        bad += not ok
        print(f"  [{'ok  ' if ok else 'FAIL'}] {'adds only (control)':34s} "
              f"expect=ALLOW got={got}")
        return bad
    finally:
        shutil.rmtree(wt, ignore_errors=True)


def main():
    fail = clean = dirty = 0
    print("Each worktree, judged against its OWN index:\n")
    for wt in worktrees():
        eng = engine_staged(wt)
        if eng is None:
            continue
        got = verdict(wt, VERB + " -m x")
        label = pathlib.Path(wt).name or wt
        if eng:
            dirty += 1
            print(f"  [--- ] {label:26s} {len(eng):3d} engine file(s) staged "
                  f"-> {got} (either verdict is legal; boot freshness decides)")
        else:
            clean += 1
            ok = got == "ALLOW"
            fail += not ok
            print(f"  [{'ok  ' if ok else 'FAIL'}] {label:26s} "
                  f"no engine staged        -> {got} (must be ALLOW)")

    # `git -C <dir>` must win over cwd: point at a tree with a clean index from a
    # tree that has engine content staged, and the answer must follow the -C tree.
    src = next((w for w in worktrees() if engine_staged(w)), None)
    dst = next((w for w in worktrees() if engine_staged(w) == []), None)
    if src and dst:
        got = verdict(src, "git -C " + dst + " " + VERB[4:] + " -m x")
        ok = got == "ALLOW"
        fail += not ok
        print(f"\n  [{'ok  ' if ok else 'FAIL'}] `git -C <clean tree>` from a dirty "
              f"tree -> {got} (must be ALLOW)")
    else:
        print("\n  [skip] no dirty+clean worktree pair available for the -C case")

    print("\nRule 4 - deleting a removal node needs RESOLVE-VERIFIED:\n")
    fail += removal_node_rule()

    print(f"\n{clean} clean tree(s), {dirty} with engine content staged.")
    print("RESULT:", "all assertions hold" if not fail else f"{fail} FAILED")
    return 1 if fail else 0


if __name__ == "__main__":
    sys.exit(main())
