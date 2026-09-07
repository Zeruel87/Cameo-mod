#!/usr/bin/env python3
"""PreToolUse Bash guard for Cameo-mod. Reads the hook JSON on stdin and enforces
four hard rules deterministically (so they don't depend on the model remembering):

  1. SCOPED ADDS ONLY — block `git add -A` / `--all` / `.` (the maintainer + Devin
     have live uncommitted WIP; a wide add captures or clobbers it).
  2. NEVER HAND-PARSE `Versus:` — a line-scanner cannot see where the block ends.
  3. BOOT-GATE BEFORE COMMITTING ENGINE CONTENT — block `git commit` when a staged
     file under mods/ , OpenRA.Mods.Cameo/ , or engine/ is newer than the last
     successful boot (perf.log ending in MenuPostProcessEffect.PostWorldLoaded).
     Docs/tools-only commits are exempt (no engine content parsed at boot).
  4. DELETING A REMOVAL NODE NEEDS EVIDENCE — `-Key@X:` in a child CANCELS what an
     ANCESTOR defines, so it looks dead while being load-bearing. Requires
     RESOLVE-VERIFIED in the commit message. A boot gate cannot see this class:
     it shipped once already (the mutalisk bounced forever).

⚠ Rules 3 and 4 resolve the repo from the COMMAND's cwd, not from this file, so they
work in every `git worktree`. See tools/hooks/test_bash_guard.py.

Emits a PreToolUse permissionDecision. No output = allow.
"""
import sys
import os
import re
import json
import subprocess
import pathlib


def deny(reason):
    print(json.dumps({"hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "permissionDecision": "deny",
        "permissionDecisionReason": reason}}))
    sys.exit(0)


def main():
    try:
        data = json.load(sys.stdin)
    except Exception:
        return  # can't parse -> allow
    cmd = (data.get("tool_input") or {}).get("command", "") or ""

    # (1) scoped adds only. Anchor at a COMMAND POSITION (start of string, or after a
    # shell separator / newline) so the rule doesn't false-positive when a commit
    # message or other prose merely MENTIONS `git add -A` (e.g. inside backticks).
    if re.search(r"(?:^|[\n;&|(])\s*git\s+add\s+(?:-A\b|--all\b|\.(?:\s|$))", cmd):
        deny("Scoped adds only — never `git add -A/--all/.` (the maintainer and Devin "
             "have live uncommitted WIP that a wide add would capture or clobber). "
             "Stage explicit paths instead: `git add <file> [<file> ...]`.")

    # (2) NEVER HAND-PARSE VERSUS. A bespoke line-scanner that opens a dict on `Versus:` and
    # scans following `Key: <int>` lines cannot see where the block ENDS, so the
    # `PercentageVersus:` rows that live in the SAME warhead node silently overwrite the real
    # profile. That produced a full session of internally-consistent, wrong numbers on
    # 2026-08-22 ("0 of 125 obey the MEAN-100 law"; the truth was 123 of 125). The project has
    # correct readers; use them.
    if re.search(r"""["']Versus:["']""", cmd) and re.search(r"startswith|split\(|re\.match", cmd):
        if "versus_of" not in cmd and "resolve_weapon" not in cmd:
            deny("Never hand-parse a `Versus:` block. A line-scanner cannot tell where the block "
                 "ENDS, so `PercentageVersus:` in the same warhead node silently overwrites the "
                 "profile — that is exactly how a whole session of weapon-profile numbers came "
                 "out wrong. Use the project's readers: "
                 "`miniyaml.Ruleset.resolve_weapon(name)` for the node, then "
                 "`weapon_efficiency.versus_of(warhead_node)` for the {armor: percent} dict. "
                 "See CLAUDE.md rule 8e and tools/audit/audit_versus_profile.py.")

    # (3) boot-gate before committing engine-loaded content.
    #     Exempt: a MERGE that only carries engine files through unchanged from one
    #     of its parents. That content was gated on the branch it came from, and
    #     demanding a boot for it makes `git merge origin/master` impossible for
    #     anyone whose branch is docs-only. A merge that RESOLVES an engine file
    #     (content differing from both parents) is still gated.
    if re.search(r"\bgit\s+commit\b", cmd):
        # ⛔ Resolve the repo from the COMMAND's working directory, not from this
        # file's location. The fleet now works in `git worktree`s (one repository,
        # many working directories), and a hook that always inspected the MAIN
        # checkout validated the WRONG INDEX in both directions:
        #   * false BLOCK — a docs-only commit in a worktree was refused because
        #     another agent had 73 sprite files staged in the main tree;
        #   * false PASS — the dangerous one — engine content committed from a
        #     worktree sails through ungated whenever the main index is clean.
        # `rev-parse --show-toplevel` gives the worktree actually being committed
        # to; every check below then keys off that.
        root = pathlib.Path(__file__).resolve().parents[2]
        where = data.get("cwd") or str(root)
        # The shell cwd resets between tool calls, so an agent working in a worktree
        # writes `cd <worktree> && git commit ...`. That `cd` is INSIDE the command
        # string and invisible to the hook's own `cwd` field — without reading it,
        # every worktree commit is judged against the main tree's index.
        # ⚠ Anchor BOTH at a COMMAND POSITION, for the same reason rule (1) does:
        # a commit message that merely MENTIONS `git -C <dir>` in prose must not be
        # read as a real flag. It happened immediately — the message documenting this
        # very fix contained the words `git -C <dir>`, the guard took `<dir>` as a
        # path, git could not resolve it, and the check fell back to the main tree
        # and refused the commit.
        cmd_pos = r"(?:^|[\n;&|(]|&&|\|\|)\s*"
        m_cd = re.search(cmd_pos + r"cd\s+(\"[^\"]+\"|'[^']+'|\S+)", cmd)
        if m_cd:
            where = m_cd.group(1).strip("\"'")
        m_c = re.search(cmd_pos + r"git\s+-C\s+(\S+)", cmd)   # `git -C <dir> commit`
        if m_c:                                               # explicit -C wins
            where = m_c.group(1).strip("\"'")
        # git-bash hands out MSYS paths (`/c/tmp/x`) but git.exe only understands
        # `C:/tmp/x`, so an unnormalised path silently fails to resolve and the
        # check falls back to the main tree — the false BLOCK all over again.
        m_msys = re.match(r"^/([a-zA-Z])/(.*)$", where)
        if m_msys:
            where = f"{m_msys.group(1).upper()}:/{m_msys.group(2)}"
        try:
            top = subprocess.run(
                ["git", "-C", str(where), "rev-parse", "--show-toplevel"],
                capture_output=True, text=True, timeout=15)
            if top.returncode == 0 and top.stdout.strip():
                root = pathlib.Path(top.stdout.strip())
        except Exception:
            pass  # fall back to the main checkout — never less strict than before
        try:
            staged = subprocess.run(
                ["git", "-C", str(root), "diff", "--cached", "--name-only"],
                capture_output=True, text=True, timeout=15).stdout.split()
        except Exception:
            return  # git unavailable -> don't block
        # (4) DELETING A REMOVAL NODE IS A BEHAVIOUR CHANGE, NOT A CLEANUP.
        #     `-Warhead@X:` in a child CANCELS something an ANCESTOR defines. It looks
        #     dead because the node it sits in does not define X — that is the whole
        #     point of it. d818aec40 deleted 2248 of them as "stale" and resurrected
        #     every cancelled warhead: 461 -> 1103 weapons with more than one main
        #     warhead, and 14 deleted `-Warhead@shrapnel:` terminators turned the
        #     mutalisk's 3-bounce spore into an infinite loop. NOTHING CRASHED, so the
        #     boot gate passed and it shipped.
        #     This does not forbid the edit — it demands the evidence.
        removed_nodes = []
        try:
            diff = subprocess.run(
                ["git", "-C", str(root), "diff", "--cached", "-U0", "--", "*.yaml"],
                capture_output=True, text=True, timeout=30).stdout
            removed_nodes = re.findall(r"^-\s*-([A-Za-z]\w*)@", diff, re.M)
        except Exception:
            pass
        if removed_nodes:
            msg = ""
            m_m = re.search(r"-m\s+(\"[^\"]*\"|'[^']*')", cmd)
            if m_m:
                msg = m_m.group(1)
            m_f = re.search(r"-F\s+(\S+)", cmd)
            if m_f:
                try:
                    fp = pathlib.Path(m_f.group(1).strip("\"'"))
                    if not fp.is_absolute():
                        fp = root / fp
                    msg = fp.read_text(encoding="utf-8", errors="replace")
                except Exception:
                    pass
            if "RESOLVE-VERIFIED" not in msg:
                kinds = ", ".join(sorted(set(removed_nodes))[:5])
                deny(
                    f"This commit deletes {len(removed_nodes)} removal node(s) "
                    f"(-{kinds}@...) from yaml. A `-Key@X:` in a child CANCELS "
                    "something an ANCESTOR defines - it looks dead precisely because "
                    "the node it sits in does not define X. Deleting 2248 of them on "
                    "2026-09-06 resurrected every cancelled warhead (461 -> 1103 "
                    "multi-main weapons) and turned the mutalisk's 3-bounce spore into "
                    "an infinite loop. Nothing crashed, so the boot gate passed and it "
                    "shipped. "
                    "Before committing: for EACH deleted node, resolve the parent chain "
                    "and keep it unless NO ancestor defines that key. Then run "
                    "`python tools/audit/review_resolve_diff.py` (before/after resolve), "
                    "`python tools/audit/audit_shrapnel_chains.py` (S1a must stay 0) and "
                    "`python tools/audit/audit_weapon_shape.py` (W5 must not rise), and "
                    "put RESOLVE-VERIFIED in the commit message with what you checked. "
                    "A boot gate cannot see this class of bug.")

        engine_prefixes = ("mods/", "OpenRA.Mods.Cameo/", "engine/")
        eng = [f for f in staged if f.startswith(engine_prefixes)]

        # A MERGE stages every file the other side brought in, so merging an
        # already-gated upstream branch would demand a boot for content this
        # commit did not author. Keep only the engine files whose merged content
        # differs from BOTH parents — those are the ones this commit resolved,
        # and they are the only ones a boot could say anything about.
        # In a worktree `root/.git` is a FILE pointing at the real git dir, so
        # `root/.git/MERGE_HEAD` can never exist there. Ask git for the path.
        try:
            gd = subprocess.run(["git", "-C", str(root), "rev-parse", "--git-dir"],
                                capture_output=True, text=True,
                                timeout=15).stdout.strip()
            gitdir = pathlib.Path(gd) if gd and pathlib.Path(gd).is_absolute() \
                else (root / gd if gd else root / ".git")
        except Exception:
            gitdir = root / ".git"

        if eng and (gitdir / "MERGE_HEAD").exists():
            def blob(rev, path):
                r = subprocess.run(["git", "-C", str(root), "show", f"{rev}:{path}"],
                                   capture_output=True, timeout=15)
                return r.stdout if r.returncode == 0 else None

            def staged_blob(path):
                r = subprocess.run(["git", "-C", str(root), "show", f":0:{path}"],
                                   capture_output=True, timeout=15)
                return r.stdout if r.returncode == 0 else None

            try:
                parents = ["HEAD", (gitdir / "MERGE_HEAD").read_text().split()[0]]
                authored = []
                for f in eng:
                    mine = staged_blob(f)
                    if mine is not None and any(blob(par, f) == mine for par in parents):
                        continue  # identical to a parent -> inherited, not authored here
                    authored.append(f)
                eng = authored
            except Exception:
                pass  # can't tell -> fall through and demand the gate

        if not eng:
            return  # docs/tools-only commit (or a pure merge) — boot not required
        newest = 0.0
        for f in eng:
            p = root / f
            if p.exists():
                newest = max(newest, p.stat().st_mtime)
        perf = pathlib.Path(os.environ.get("APPDATA", "")) / "OpenRA" / "Logs" / "perf.log"
        if not perf.exists():
            deny("Boot-gate required: you are committing engine content (" + eng[0]
                 + (" +%d more" % (len(eng) - 1) if len(eng) > 1 else "")
                 + ") but no perf.log was found. Run launch-game.cmd to the main menu "
                 "(perf.log must end with MenuPostProcessEffect.PostWorldLoaded), confirm "
                 "no new exception-*.log, then commit.")
        try:
            tail = perf.read_text(errors="ignore").splitlines()[-40:]
        except Exception:
            tail = []
        booted = any("MenuPostProcessEffect.PostWorldLoaded" in ln for ln in tail)
        fresh = perf.stat().st_mtime >= newest - 1  # 1s slack
        if not (booted and fresh):
            why = []
            if not booted:
                why.append("perf.log's last lines don't show MenuPostProcessEffect.PostWorldLoaded")
            if not fresh:
                why.append("perf.log is older than your staged engine changes (the boot is stale)")
            deny("Boot-gate required before committing engine content — " + "; ".join(why)
                 + ". Run launch-game.cmd to the menu, confirm no new exception-*.log, then "
                 "commit. (Docs/tools-only commits are exempt from this check.)")


if __name__ == "__main__":
    main()
