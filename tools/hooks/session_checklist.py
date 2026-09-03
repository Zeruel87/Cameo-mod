#!/usr/bin/env python3
"""SessionStart hook — inject the Cameo must-read + hard-rules checklist into
context every session, so 'read the docs first' and the hard rules don't depend
on the model choosing to read CLAUDE.md. Short and punchy on purpose."""
import json

CHECKLIST = """\
CAMEO — orient before acting this session (verify against the artifacts, don't trust summaries):

MUST-READ, in order: CLAUDE.md · docs/LESSONS_LEARNED.md · docs/AGENT_WORKSPACE.md ·
docs/HANDOFF.md · **docs/DESIGN.md** · docs/design/ROADMAP.md · docs/audit/SUMMARY.md.
docs/README.md defines that order and wins over any copy of it.

docs/HANDOFF.md is THE entry point: verified state + the priority-ordered queue. It supersedes
every dated handoff — those are in docs/history/handoffs/ and must NOT be resumed from.
For weapon work also: docs/design/WEAPON_3WAY_SPLIT.md · docs/design/WEAPON_TYPE_SYSTEM.md ·
docs/design/BALANCE_PROGRAM_PLAN.md (the board + §0a's binding order of operations).

⛔ BEFORE DESIGNING ANYTHING, GREP docs/DESIGN.md FOR THE CONCEPT. It is the BINDING contract
and it is long, so nobody reads it end to end — grep it. On 2026-08-22 a whole session was spent
re-deriving a weapon-tier model that §12.0h/§12.0c/§12.0d had already ruled AND shipped. A design
question that feels novel usually is not. The rulings most often re-invented:

  §12.0h MEAN-100      every ^Warhead_* MAIN warhead has its 16 armor rows normalised to
                       arithmetic MEAN 100. Therefore K is SHAPE-ONLY, `Damage` is the SOLE
                       magnitude knob, and a tilt is FREE. Weapon tier does NOT price via Versus.
  §12.0c SHIELD LADDER Shield is its own compressed [100,400] ladder, Tesla top. NOT a normal armor.
  §12.0d CLASS TILT    each LEVEL tilts toward one end of every armor ladder (Light->lightest rung,
                       Medium->middle, Heavy->heaviest, Super->FLAT generalist). The tilt is applied
                       to the VALUES and each armor is then given back the RANK it held, so it
                       "can never invert" — WITHIN a ladder. LADDERS are INF/VEH/BLD/AIR, so
                       `None` (INF) vs `Superheavy` (VEH) is a CROSS-ladder relation the tilt is
                       DESIGNED to change. Comparing them proves nothing.
  §12.0b HEROIC        a DERIVED cell: Heroic = Plate x Scout / PEAK. Never tilt it; recompute it.

⛔ NEVER HAND-PARSE YAML. Read through `miniyaml.Ruleset.resolve_weapon` / `.resolve`, and pull
Versus with `weapon_efficiency.versus_of(node)`. A bespoke line-scanner opened a dict on `Versus:`
and never CLOSED it, so the `PercentageVersus:` rows sitting in the SAME warhead node overwrote the
profile: every mean, spread, ratio and inversion count came out internally consistent and WRONG
("0 of 125 obey MEAN-100"; the truth was 123 of 125). The near-miss sibling name is the trap — the
OPEN guard was right, the CLOSE was missing. Guarded by tools/audit/audit_versus_profile.py.
[hook-enforced: bash_guard blocks inline Versus scanning]

⚠ A RESULT THAT CONTRADICTS A BINDING LAW IS A CONTRADICTION, NOT A FINDING. If the generator
implements a law and verify_generator_sync reports 0 drift, "nothing conforms" means YOUR MEASURE
is broken. Check the measurement before writing it up.

HARD RULES (several are enforced by hooks — see .claude/settings.json):
 1. Never commit without booting to the main menu (perf.log ends
    MenuPostProcessEffect.PostWorldLoaded; no new %APPDATA%/OpenRA/Logs/exception-*.log). [hook-enforced]
 2. Scoped `git add <files>` only — never -A/./--all (several contributors have live WIP). [hook-enforced]
 3. Don't trust, verify — grep the data / ls the file (incl. ~/Downloads) / run the tool /
    boot-gate before asserting done/pending/blocked/missing. When a summary and the artifact
    disagree, the artifact wins — then fix the stale summary.
 4. Never hand-edit balance numbers — use the pipeline (extract_stats -> ledger ->
    apply_balance --confirm; --confirm needs maintainer order).
 5. Versus lives ONLY in ^Warhead_* templates; never change a warhead / Burst / BurstDelays
    without explicit permission.
 6. Weapon 3-way split: preserve resolved behaviour (Damage verbatim, projectile fields),
    find_empty_warhead.py = 0, boot-gate per batch. Verify with tools/audit/review_resolve_diff.py.
 7. Multi-agent tree: one owner per file-set (boundaries in BALANCE_PROGRAM_PLAN.md §2);
    re-verify others' commits before building on them (check mtimes + git log -3 <file> first).
 8. Audit reports regen via `bash tools/audit/run_all.sh` ONLY (PowerShell > writes UTF-16),
    and ONLY from a COMPLETE tree (engine/ built, clone not shallow) - otherwise a dozen
    audits scan a smaller corpus, report FEWER findings and still say PASS. run_all diverts
    to the untracked docs/audit/degraded/ in that case; --force-latest overrides.
 9. Underscore-only naming — no hyphens in ids/files/fluent keys.
10. Commit trailer = the ACTUAL author, with your REAL model name:
    Co-Authored-By: Claude <your-model> <noreply@anthropic.com>  (a template, not a
    literal - do not copy a version from a previous commit). Other agents sign as
    themselves, e.g. Co-Authored-By: Devin AI <devin@cognition.ai>.

ENGINE CHANGES — `engine/` IS NOT PART OF THIS REPO. It is .gitignored, has no .git and no
.gitmodules, and `git ls-files engine` returns ZERO files; `git` run from inside it silently
operates on the PARENT repo. Editing engine/**  produces work that CANNOT be committed here
and is DELETED by the next `make all`. It is a build output, not source.
Full procedure: docs/LESSONS_LEARNED.md "The canonical engine update pipeline". In short:
 1. Edit C# in the SEPARATE clone of https://github.com/cameo-mod/OpenRA, branch cameo-engine.
 2. Commit + push to origin/cameo-engine (check `git status` for stray nested-clone entries).
 3. `git rev-parse cameo-engine` for the FULL 40-char hash — never hand-type or truncate it.
 4. Set ENGINE_VERSION="<hash>" in **mod.config** (NOT mod.yaml) in this repo.
 5. `make.cmd all` — VERSION mismatch makes the SDK delete engine/, refetch and rebuild.
 6. Verify engine/VERSION == the hash, build has 0 errors, and recreate any engine/glsl/
    shaders (the fetch WIPES them, e.g. postprocess_nuclearflash.frag).
 7. Boot-gate, then commit mod.config with the docs updates.
Before choosing that route, check whether the mod assembly can just SHADOW the engine trait:
ObjectCreator.FindType takes the FIRST assembly in mod.yaml's Assemblies list holding the
name, and the order is AS, CA, Cameo, Cnc, D2k, Common — so an OpenRA.Mods.Cameo type of the
same name wins with ZERO yaml changes (precedent: ColorPickerColorShift, PlayerColorShift,
SelectionDecorations). PROVE a shadow works by giving the Cameo Info a field the engine one
lacks and booting with that field set — `--docs` lists BOTH types and proves nothing.

CURRENT FRONT (2026-08-23): W24 (one damage warhead per weapon) -> W23 (retrofit the 47 legacy
templates) -> A5 -> class anchors. Pricing is deliberately NOT running yet; apply_balance --confirm
is a NO-OP until W11 sign-off writes targets into the ledger (signed-off anchors today: 0).
Work queue: docs/design/ROADMAP.md · effort estimate: docs/design/BALANCE_PIPELINE_ESTIMATE.md.

TWO THINGS YOU CANNOT RESOLVE FROM THE REPO:
 * commit hashes older than 2026-08-10 fail in a shallow checkout — `git fetch --unshallow`,
   or verify the claim against the artifact instead (better).
 * `memory <name>` citations point at a private per-agent store. Provenance only, never
   authority; promote anything binding into DESIGN.md.
"""

print(json.dumps({"hookSpecificOutput": {
    "hookEventName": "SessionStart",
    "additionalContext": CHECKLIST}}))
