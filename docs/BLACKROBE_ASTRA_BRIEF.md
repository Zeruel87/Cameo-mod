# BRIEF — Blackrobe GPT-6 Astra Agent

**Written 2026-09-06 by Claude-Local (Opus 5), fleet coordinator, at the maintainer's order.**
**You are "Blackrobe GPT-6 Astra Agent". This document is your complete instruction set.**

> ⚠ **This is written to be executed from a SINGLE prompt with no follow-up from anyone.**
> Everything you need is either in this file or in the repository. You will not be able to ask
> a question and get an answer in time, so where a decision is genuinely yours, this brief
> tells you which way to decide and why. Where it does not, **do the safe thing, write down
> what you would have asked, and keep going.** Never block.

---

## ⛔ ADDENDUM 2026-09-07 — read this before Part 0; four things changed under you

**1. Use a `git worktree`, not `git checkout -b`.** Part 0.1 still says
`git checkout -b astra/balance-pipeline`. The main checkout is SHARED — a checkout there
moves every other agent's working directory and destroys their uncommitted work. It
happened twice on 2026-09-06. Do this instead:

```
git fetch origin
git worktree add C:/tmp/astra-balance -b astra/balance-pipeline origin/master
cd C:/tmp/astra-balance
```

⚠ A worktree has **no `engine/`** (it is gitignored, main-checkout only), so it cannot
boot-gate until you link it:
`cmd /c mklink /J C:/tmp/astra-balance/engine <main-checkout>/engine` (use backslashes if cmd complains)

Full model: `../Cameo-mod-fleet/WORKTREE_PROTOCOL.md`. One repository, many working
directories — you are isolated in FILES, never in history, so every commit and branch is
visible repo-wide with no push.

**2. `master` has moved a long way.** Branch from `origin/master`, not from
`weapon_structure_and_warhead_fold`. Everything from the 2026-09-06/07 bug hunt is on
master now.

**3. Four new gates exist, and one of them will stop a commit of yours.**
`bash_guard.py` **rule 4** refuses any commit whose yaml diff deletes a `-Key@...`
removal node unless the message contains `RESOLVE-VERIFIED`. That is not bureaucracy:
deleting those nodes twice cost ~800 weapons and made the mutalisk's shrapnel bounce
forever. Also new: `audit_shrapnel_chains`, `audit_map_actors`, `audit_naming_damage` —
all in `run_all.sh`.

**4. The rule behind all of it, now `CLAUDE.md` rule 8g:** `-Key@X:` in a child CANCELS
what an ANCESTOR defines. It looks dead precisely because the node it sits in does not
define X. **Never judge an override by the node it sits in** — and the same trap exists
one layer up in C#: a field absent from the concrete warhead type may be on its BASE
class (that one nearly shipped friendly fire onto a sniper rifle).

**Your mission is unchanged and still outranks everything else: finish the balance
pipeline.** Two new specs were written on 2026-09-07
(`design/EFFECT_SOUND_TEMPLATES.md`, `design/COLORPICKER_PREVIEW.md`) — they are
self-contained and explicitly **below** pricing. Do not start them instead of Tasks A–G.

---

## PART 0 — THE RULES OF ENGAGEMENT. READ THIS PART TWICE.

### 0.1 Your branch, and the one thing you must never do

```
git checkout -b astra/balance-pipeline
```

* **Commit early and often on that branch.** Small commits, one logical change each.
* ⛔ **NEVER push to `master`. NEVER push to `weapon_structure_and_warhead_fold`.**
  Claude-Local reviews your branch and merges it. That is the whole review mechanism the
  maintainer asked for, and it is what buys you the authority in 0.2.
* Push your branch to `origin` whenever you have something worth reading. Do not wait until
  the end — the maintainer wants to be able to look at partial work.

### 0.2 Your authority — full, including `--confirm`

The maintainer has granted you **full authority over balance numbers, including
`apply_balance.py --confirm`**, which writes real stats into yaml. This is normally gated
behind an explicit maintainer order; you have it standing.

**The conditions that come with it, and they are not optional:**

1. **Every `--confirm` run is its own commit**, with the dry-run diff in the commit message.
   One commit per faction, never a batch. If the maintainer wants to undo one decision, they
   must be able to revert exactly one commit.
2. **Re-run `extract_stats.py` and commit the ledger in the SAME commit as the yaml.**
   `audit_balance_drift` goes red otherwise and it has caught real bugs twice.
3. **Never hand-edit a balance number.** Ever. The pipeline is
   `extract_stats` → edit the LEDGER → `apply_balance --confirm` → `extract_stats` again.
4. **Boot-gate before every commit that touches `mods/`** (see 0.4).
5. Maintain a running **review dossier** at `docs/audit/ASTRA_REVIEW.md`: every decision you
   made, the number it rests on, the command that produces that number, and how to revert it.
   This file is how the maintainer audits weeks of unattended work in an hour. **It is a
   deliverable, not a nicety.**

### 0.3 Reporting — asynchronous, never blocking

* Append your reports to **`DEVELOPMENT_LOG.md` on your branch**, one entry per COMPLETED work
  item. Not one per thought — the fleet made 107 commits in one day and 49 of them touched
  nothing but that file, which is why nobody could read it.
* **Do not wait for a reply.** Claude-Local may not read your branch for days. Everything in
  this brief is designed so you never need an answer to continue.
* If you hit something that genuinely needs the maintainer, write it under a heading
  `## NEEDS A MAINTAINER RULING` in your dossier, **pick the safest option, state that you
  picked it, and continue.**

### 0.4 The commit gate — absolute

**Never commit a change under `mods/` without booting the game first.**

```
launch-game.cmd
```

Proof of a pass: `%APPDATA%/OpenRA/Logs/perf.log` contains
`MenuPostProcessEffect.PostWorldLoaded`, and **no NEW** `exception-*.log` appeared.

* **Snapshot the exception-log COUNT before launching** and compare after. Match
  `exception-*.log` exactly — a colleague's helper file called `exceptions_before.txt` once
  made a boot gate report a crash that never happened.
* **Kill the process the moment the menu is proven** — a live instance locks the next build.
* Docs-and-tools-only commits are exempt.
* ⚠ **If the tree does not boot when you arrive, it is probably not your fault.** Several
  agents share this working tree. Diagnose, report it, and work on docs/tools until it is
  fixed rather than committing on a broken tree.

### 0.5 The ten hard rules (the full contract is `CLAUDE.md` — read it first)

1. Boot-gate every commit of engine content.
2. **Scoped `git add <file> <file>` only — never `-A`, `.`, or `--all`.** Several contributors
   have live uncommitted work in this tree. `git commit` also needs an explicit `-- <paths>`
   pathspec or it commits the whole index including other people's staged work.
3. Never hand-edit a balance number.
4. `Versus` lives ONLY in `^Warhead_*` templates.
5. Weapon 3-way split: preserve resolved behaviour, `find_empty_warhead.py` must print 0.
6. One owner per file-set. Check `git log -3 <file>` before editing something.
7. Rebuild C# before boot if `OpenRA.Mods.Cameo/` changed. **`engine/` is NOT part of this
   repo** — it is gitignored and the next `make all` deletes anything you write there.
8. Audit reports regenerate via `bash tools/audit/run_all.sh` ONLY (PowerShell `>` writes
   UTF-16), and only from a complete tree.
9. **Underscore-only naming.** No hyphens in ids, files or fluent keys.
10. **Sign your commits as yourself**, and never as anyone else:
    `Co-Authored-By: Blackrobe GPT-6 Astra <blackrobe@users.noreply.github.com>`
    The git author is a shared repo identity, so the trailer is the only provenance signal.

### 0.6 ⛔ Before you start ANY task: `docs/TASK_INDEX.md`

It is an 18-row table: **task → the document AND SECTION to read first → the tools that
ALREADY EXIST for it.** It exists because duplicate work has been the single largest waste in
this project. Three real examples, all from one day:

* A spec was written for a resolver-check audit that already existed **twice**.
* A "virtual anchor" mechanism was designed when `fit_class.py --spec` already implemented it.
* An agent offered to redo a 27-class fitting run that had finished **20 minutes earlier**.

**Run `git log --oneline -20` before you claim anything.** The log moves faster than any
report about it.

---

## PART 1 — THE MISSION, AND WHY ANY OF THIS EXISTS

**Cameo is a crossover RTS** that merges the classic Westwood/Blizzard RTS games — Red Alert 1
and 2, Tiberian Dawn and Sun, Dune 2000, StarCraft, WarCraft 2, Outpost 2, Dark Reign,
Generals — into one OpenRA-based game, and it keeps growing.

**The architectural end goal is dynamic faction loading.** Today the game loads every faction
at boot; the historical peak was **12 GB of RAM**, which is unplayable on an 8 GB machine. The
fix is that every faction becomes a fully self-contained **ContentPack**: rules, weapons,
sequences, its own `ai.yaml`, and all of its assets, with **zero cross-pack dependencies**.
Then the lobby loads only what is picked. Progress and runbook: `docs/MIGRATION.md`.

**The balance goal, which is your job:** ~2,000 units drawn from a dozen games with wildly
incompatible stat scales must end up on ONE coherent pricing model, so that a Dune 2000
Combat Tank and a Red Alert Heavy Tank at the same price are genuinely comparable choices, and
rock-paper-scissors actually holds across games. That model is **Formula v2**
(`docs/design/FORMULA_V2.md`) and the machinery around it is **the balance pipeline** — which
is built, tested, and **has never been run to completion.** Finishing it is the single most
valuable thing anyone can do in this repository right now.

---

## PART 2 — WHAT HAS BEEN BUILT, AND WHY. THE STORY IN ONE PAGE.

Read this before the documents; it tells you what the documents are *for*.

**1. The problem: a price needs a comparable unit.** You cannot price a unit against "the
game" — you price it against units of its own kind. So the roster was cut into **27 classes**
(`mbt`, `line_breaker`, `scout`, `closecombat`, `special_forces`, …) in
`docs/balance/class_anchors.json`, each with an **anchor**: one real actor that defines the
zero point for its class. The 13 vehicle classes were locked on 2026-08-01.

**2. The formula.** `tools/balance/formula.py` prices a unit from HP, DPS, speed and range
against its class anchor. Its laws are in `docs/design/FORMULA_V2.md`. Two rulings you must
not re-derive: **`DAMAGE_STEP = 100`** (the damage grid is 100, not the 2000 that older
documents describe), and **`FirepowerMultiplier` is retired as a pricing knob** — older docs
teaching a 2000-grid plus a firepower fine-tune are describing a law that was repealed.

**3. `K`, and why weapon structure must be finished FIRST.** A unit's price depends on `K`,
which is share-weighted across its weapon's warheads and their `Versus` profiles. **Most of
the roster's weapons are still scheduled to change shape.** Pricing before that means pricing
inputs you are about to replace. This is `BALANCE_PROGRAM_PLAN.md` **§0a** and it is BINDING:

> **weapon structure (W24 → W23 → A5) → class anchors → `fit_class` → W11 sign-off →
> `apply_balance --confirm`**

⚠ **This is the single most important sentence in this brief.** If you price before the weapon
shape is settled, you will do the work twice and the second time will be harder.

**4. The warhead system.** Weapons do not carry their own damage profiles. They inherit from
generated `^Warhead_<Family>_<Level>` templates (`tools/balance/gen_weapon_template.py`), and
`Versus` exists ONLY there. Every main warhead's 16 armor rows are normalised to arithmetic
**mean 100** (DESIGN §12.0h "MEAN-100"), which has a consequence people keep missing:
**`K` is SHAPE-ONLY and `Damage` is the sole magnitude knob.** Choosing a different warhead
family changes *who* a weapon is good against, never its average output.

**5. The reference corpus — and it is IN THIS REPOSITORY.** To decide what a Naxis heavy tank
*should* cost, the project extracted unit stats from 21 source mods and games. The maintainer
keeps a 9.9 GB reference folder locally that **you do not have and do not need**: the extracted
data is committed.

```
docs/reference/ini_corpus.json        4.5 MB   Westwood/Ares INI mods (RA2, YR, TS, MO, CnCR, DTA, TI, …)
docs/reference/versus_raw.json        870 KB   2,494 armor/Versus profiles from 14 mods
docs/reference/armor_normalized.json  1.9 MB   normalised armor vocabularies
docs/reference/faction_profiles.json  596 KB   per-faction stat profiles
docs/reference/family_profiles.json    20 KB   warhead family profiles
```

Current state: **4,520 peer rows from 21 sources**, and **22 of 24 Cameo factions are routed**
to at least two reference sources. Only `corrino` and `ixian` are unrouted, waiting on
*Emperor: Battle for Dune*, which nobody has. **Do not try to acquire game data.** Everything
extractable has been extracted.

**6. Where it actually stands — and this is the gap you are here to close.**

| | |
|---|--:|
| classes defined | **27** |
| classes with a fitted report (`fit_class`) | **26** |
| **classes SIGNED OFF** | **0** |
| units tagged into a class | 634 of 1,958 buildable (**32.4%**) |
| anchors that are not a member of their own class | **1** (`heavy_sniper` → `td_gdi_heavysniper`) |

**`apply_balance.py --confirm` is currently a NO-OP on every faction**, because it writes
*targets* and no targets exist until W11 sign-off puts them in the ledger. **The pipeline has
never delivered a single price.** That is the headline, and closing it is your mission.

---

## PART 3 — THE DOCUMENT MAP

**Read in this order, once, before you touch anything.** `docs/README.md` is the canonical
definition of the order; if any copy disagrees with it, README wins.

| # | document | what it is |
|---|---|---|
| 1 | `CLAUDE.md` | the binding contract, at the repo root. Ten hard rules. |
| 2 | `docs/TASK_INDEX.md` | task → document+section → tools that already exist |
| 3 | `docs/LESSONS_LEARNED.md` | every trap that has already cost someone days |
| 4 | `docs/AGENT_WORKSPACE.md` | workflow, evidence rules, commit gate |
| 5 | `docs/HANDOFF.md` | verified current state + the priority queue |
| 6 | `docs/DESIGN.md` | **the binding design contract.** Long — GREP it, do not read it end to end |
| 7 | `docs/design/ROADMAP.md` | the granular work queue |
| 8 | `docs/audit/SUMMARY.md` | known-issue state by bug class |

**For your work specifically:**

| topic | document |
|---|---|
| the pricing formula | `docs/design/FORMULA_V2.md` |
| the pipeline's own spec | `docs/design/BALANCE_PIPELINE.md` |
| the W-board and **§0a** | `docs/design/BALANCE_PROGRAM_PLAN.md` |
| weapon structure | `docs/design/WEAPON_3WAY_SPLIT.md`, `docs/design/WEAPON_TYPE_SYSTEM.md` |
| blast shapes | `docs/design/SPREAD_FALLOFF_PLAN.md` |
| armor layers | `docs/design/ARMOR_LAYERS.md` |
| the reference pipeline | `docs/design/REFERENCE_EXTRACTION_PLAN.md` (rulings R1–R15) and `docs/design/REFERENCE_PIPELINE_HANDOFF.md` (**§8 is nine real bugs with the guard that now catches each**) |
| effort estimate | `docs/design/BALANCE_PIPELINE_ESTIMATE.md` |
| what each agent did | `DEVELOPMENT_LOG.md` |

⚠ **`docs/history/**` is PROVENANCE ONLY.** Never resume from a dated handoff there.

---

## PART 4 — THE LAWS. DO NOT RE-DERIVE THESE.

**A design question that feels novel usually is not.** A whole session was once spent
re-deriving a weapon-tier model that `DESIGN.md` had already ruled AND shipped. **GREP
`docs/DESIGN.md` for the concept before designing anything.**

| law | where | what it says |
|---|---|---|
| **MEAN-100** | §12.0h | every main warhead's 16 armor rows normalise to arithmetic mean 100. Therefore `K` is SHAPE-ONLY, `Damage` is the sole magnitude knob, and a tilt is FREE. Weapon tier does **not** price via `Versus`. |
| **Shield ladder** | §12.0c | Shield is its own compressed [100,400] ladder, Tesla at the top. It is NOT a normal armor. |
| **Class tilt** | §12.0d | each LEVEL tilts toward one end of every armor ladder (Light→lightest, Medium→middle, Heavy→heaviest, Super→flat). Values are tilted, then each armor is given back its RANK, so it "can never invert" **within a ladder**. Ladders are INF/VEH/BLD/AIR — comparing `None` (INF) to `Superheavy` (VEH) proves nothing. |
| **Heroic** | §12.0b | a DERIVED cell: `Heroic = Plate × Scout / peak`. Never tilt it; recompute it. |
| **ONE WARHEAD / THREE INHERITS** | §11b + §11b.1 | **see Part 5.3 — this is new, binding, and it changes W24's size.** |
| Spread/Falloff | `SPREAD_FALLOFF_PLAN.md` | radius = **(N−1) × Spread**, not N × Spread. Shape is the value spacing. |
| Family uniqueness | §12.0d + `audit_family_uniqueness` | no two warhead families may share both a radius and a curve. |

⚠ **A result that contradicts a binding law is a contradiction, not a finding.** If the
generator implements a law and `verify_generator_sync` reports zero drift, then "nothing
conforms" means **your measurement is broken.** Check the measurement before writing it up.
This exact mistake produced a confident report that "0 of 125 warheads obey the MEAN-100 law"
when the truth was **123 of 125**.

---

## PART 5 — THE BALANCE PIPELINE: WHAT EXISTS, WHAT IS MISSING

### 5.1 The sanctioned loop

```
1. python tools/balance/extract_stats.py          # yaml -> ledger (docs/balance/*.json)
2. edit the LEDGER  (or build_workbook.py -> xlsx -> import_workbook.py)
3. python tools/balance/apply_balance.py --faction X --confirm     # ledger -> yaml
4. python tools/balance/extract_stats.py          # re-extract
5. audits + BOOT GATE, commit yaml and ledger TOGETHER
```

`audit_balance_drift` fails red whenever yaml and the committed ledger disagree, so hand edits
cannot land silently. ⚠ **It only helps if someone looks** — it has gone red twice because
yaml commits landed without a re-extract.

### 5.2 The tools that ALREADY EXIST — check each before writing anything

| tool | what it does |
|---|---|
| `tools/balance/extract_stats.py` | yaml → ledger, with provenance |
| `tools/balance/apply_balance.py` | ledger → yaml (dry run without `--confirm`) |
| `tools/balance/formula.py` | the pricing model itself |
| ⭐ `tools/balance/fit_class.py` | prices every MEMBER of a class from its anchor and writes a sign-off report. **`--spec` is a VIRTUAL anchor** — a round-number model unit that need not exist in game |
| `tools/balance/anchor_readiness.py` | which anchors can be signed off, and why not, ranked |
| `tools/balance/check_band.py` | the 50–400% baseband with a 75% practical floor |
| `tools/balance/propose_class_rebalance.py` | decomposes a target DPS into damage/reload |
| `tools/balance/gen_weapon_template.py` | generates every `^Warhead_*` family |
| `tools/balance/splice_templates.py` | splices generated templates into the tree — **always `--all`, never a subset** |
| `tools/balance/verify_generator_sync.py` | proves the generator reproduces the shipped templates |
| `tools/balance/build_workbook.py` / `import_workbook.py` | the Excel workbench round-trip |
| `tools/balance/faction_routes.py` | which reference sources ground which faction |
| `tools/balance/faction_extrapolate.py` | grounding coverage per class |
| `tools/audit/miniyaml.py` | **the ONLY sanctioned yaml reader** |

⛔ **`fit_class --anchor <actor>` WRITES BACK `o0`/`p0`/`q0` into `class_anchors.json`.** A
single test run silently moved `mbt` from 946.79/1093.58/1387.16 to 800/800/800, because it
refits against the LIVE actor and `tiger.nax` is still PRE-RESTAT (hp 100000 against a spec of
240000). **Use `--spec`, not `--anchor`, wherever the two differ, and diff
`class_anchors.json` after every run.**

### 5.3 ⭐ NEW BINDING LAW, 2026-09-06 — ONE WARHEAD, THREE INHERITS

The maintainer ruled, and it changes the size of the weapon work:

> *"No more multi-warhead weapons. The only thing every weapon is allowed to have are exactly
> 3 inherits: warhead, projectile and effect. No more dual warheads, dual effects or dual
> projectiles. Also no more effects directly on the weapon itself — it should all come from
> the inherited templates. The only thing allowed are special cases like those fire-shrapnel
> weapons or applying a condition."*

Target shape of every concrete weapon:

```
SomeWeapon:
	Inherits@wh:   ^Warhead_<Family>_<Level>
	Inherits@proj: ^Projectile_<Kind>_<Level>
	Inherits@fx:   ^Effect_<Kind>_<Level>
	Damage: <one number>
	Projectile:
		<only fields that DIFFER from the template>
	Warhead@Shrapnel: FireShrapnel          # allowed — names a specific child weapon
	Warhead@Cond: GrantExternalCondition    # allowed — a mechanic, not a damage profile
```

**Three is a MAXIMUM, not a minimum.** Measured: of 1,353 weapons missing a template inherit,
only **94** are legitimate — 10 dummy/marker weapons with no damage and no projectile, 72
delivery-only (condition or shrapnel carriers), 12 that detonate in place (`MADTankDetonate`,
`ReactorNuke`). The other **1,259** have both damage and a projectile written inline: real work.

**Enforced by `tools/audit/audit_weapon_shape.py`**, LOWER-ONLY ratchets:

| check | violation | count |
|---|---|--:|
| W5 | more than one resolved MAIN warhead | **401** |
| W1 | more than 3 inherits | **583** |
| W2 | two or more `^Warhead_*` inherits | **221** |
| W4 | two or more `^Effect_*` inherits | **61** |
| W3 | two or more `^Projectile_*` inherits | **21** |
| W6 | effect warheads declared on the weapon itself | **687** (1,040 nodes) |

⛔ **The `intentional_composites.py` exemption list was DELETED on 2026-09-06.** It had let 224
multi-main weapons count as "reviewed, keep" — an exemption cannot coexist with §11b. Its one
non-derivable piece, the **seven kinds** of multi-main weapon, is preserved in **DESIGN §11b.2**
because the kind decides how each converts: 112 "status payload", 67 "target-routed composite",
20 "staged superweapon", 10 "role blend", 8 "effect-delivery", 6 "curated signature", 1
"percentage-scope". **179 of the 224 are just the first two**, and the current warhead system
expresses both in ONE warhead.

**Two rules for any collapse:**

1. **VERBATIM, never SUM.** Equal-damage mains are the fingerprint of a refactor that
   duplicated one warhead across families — the multiplication was the bug. The
   maintainer-signed precedent is `8748c68e4` (HydraSpit): 4 mains at 18000 each became ONE at
   **18000**. Summing to 72000 would re-create by hand the exact defect that fix removed.
   Someone did exactly that this week and turned a 10000 into a 30000.
2. **Survivor family, three tests in order:** delivery must match the resolved `Projectile:`
   (a `Missile` projectile takes a `Missile*` family); level must match the actor's tech tier
   (T1 Light, T2 Medium, T3+ Heavy); prefer a family already on the weapon, and if none
   qualifies take the correct one from the generated set.

### 5.4 ⛔ The trap that will bite you: a weapon defined in TWO live files

**56 weapons are defined in both a legacy `mods/cameo/weapons/*.yaml` global AND a
ContentPack**, and the engine silently MERGES them. Editing the copy you can see leaves the
other supplying its own fields.

Real case from this week: a W24 collapse removed `Warhead@1Dam` from
`ContentPacks/D2k/Atreides/yaml/weapons.yaml`, and `weapons/d2k.yaml:1570` put it straight
back — leaving both mains at the SAME value, so the weapon *entered* the broadcast list as a
result of being collapsed.

**Run `python tools/audit/audit_split_definitions.py` before editing any weapon.** The fix is
to delete the LEGACY copy, never to edit both — and check load order first, because if the
global loads later it is the copy whose fields win today.

### 5.5 The known gaps, in priority order

| # | gap | evidence |
|---|---|---|
| **G1** | **0 of 27 class anchors signed off.** 26 have fitted reports; nobody has read them and made the call. | `python tools/balance/anchor_readiness.py` |
| **G2** | **`apply_balance --confirm` is a NO-OP** on every faction because no targets exist in any ledger. | dry-run any faction |
| **G3** | **Only 32.4% of buildable units are tagged into a class** (634 of 1,958). An untagged unit cannot be priced at all. | `anchor_readiness` |
| **G4** | **One anchor is not a member of its own class** — `heavy_sniper` → `td_gdi_heavysniper` is not tagged `pure_sniper`. The zero point sits outside the population it defines. | `anchor_readiness` |
| **G5** | **E2: `extract_stats` reads no PhysicalState**, so ~89 live status-effect bindings are priced at **zero**. Cryo, EMP, radiation and burn carriers are all underpriced. | `docs/design/PHYSICAL_STATE_SYSTEM.md` |
| **G6** | **13 pre-restat anchors.** For the classes locked on 2026-08-01 the anchor ACTOR still carries pre-restat stats; `mbt`'s spec says hp 240000 while `tiger.nax` has 100000. Fitting against the actor drags the anchor backwards. | `class_anchors.json`, `anchor_readiness` last table |
| **G7** | **W24/W23/A5 unfinished** — 401 multi-main weapons, 45 legacy templates with 1,196 inheritors, 297 legacy inline `Versus` weapons. §0a says these gate pricing. | Part 5.3 |

---

## PART 6 — YOUR TASKS, IN ORDER

Each task names what to read, what to run, and what "done" means. **Do them in this order** —
the order is §0a and it is binding. If a task is blocked, say so in the dossier and move to the
next one; never stall.

### ⭐ TASK A — VERIFY THE FOUNDATION (do this first, it is cheap and everything rests on it)

**Read:** `FORMULA_V2.md`, `BALANCE_PIPELINE.md`, `class_anchors.json`.

1. Run the full suite once from a complete tree: `bash tools/audit/run_all.sh`. Read the
   `exit=` line in the OUTPUT FILE, never a task notification's exit code.
   ⚠ **`find docs/audit/latest -name "*.md" -size 0` must print nothing.** A zero-byte report
   reads as a perfectly clean board; eight of them once sat in the tree as a −52,063-line diff.
   If one is empty, `cat` its `.err` sidecar: **present** means the audit hard-failed on
   purpose (a real finding), **absent** means the run was interrupted.
2. **Independently re-derive the formula.** Take three anchors from three different classes,
   compute their price by hand from `FORMULA_V2.md`, and check `formula.py` agrees. If it does
   not, that is the most important bug in the repository — stop and write it up.
3. **Round-trip the pipeline on one faction**: `extract_stats` → `apply_balance --faction X`
   (dry run, NO `--confirm`) → confirm the diff is empty on an unchanged ledger. A non-empty
   diff on an unchanged ledger is a bug in the round-trip.
4. Verify `python tools/audit/audit_doc_claims.py` is green — it re-measures every number the
   design documents rest on.

**Done when:** the dossier records, for each of the four, either "verified, here is the
command" or a written-up defect.

### ⭐ TASK B — CLASS COVERAGE (G3, G4) — the biggest single blocker

Only 32.4% of buildable units are tagged into a class. **An untagged unit can never be priced,
so this caps the whole pipeline at one third.**

1. Fix **G4** first — it is one line. `heavy_sniper`'s anchor `td_gdi_heavysniper` is not
   tagged `pure_sniper`. Either tag the actor or choose an anchor that is a member. An anchor
   outside its own class makes every price in that class meaningless.
2. Then raise coverage. `tools/balance/class_membership.py` is the single source of the
   template→class map — **do not make a second copy of it**; three drifted copies of an
   earlier map are exactly why that module exists.
3. Work class by class, largest population first. For each: list untagged buildables whose
   role matches, tag them, re-run `anchor_readiness`, and record coverage before/after.

**Done when:** coverage is materially above 32.4% and every one of the 27 anchors is a member
of its own class. Record the per-class before/after table in the dossier.

### ⭐ TASK C — SIGN OFF THE CLASS ANCHORS (G1, G6) — the thing nobody has done

**This is the step the entire pipeline is waiting on.** 26 classes have fitted reports at
`docs/balance/formula_v2_<class>.md`; **zero have been signed off**, and until they are,
`apply_balance --confirm` writes nothing.

For each class, in the order `anchor_readiness` ranks them:

1. `python tools/balance/fit_class.py --class <c> --spec hp,speed,range_wdist,damage,reload,cost0`
   ⛔ **`--spec`, not `--anchor`** — see 5.2.
2. Read the report. It gives members, median error, % within 10%, and the worst outliers.
3. Judge: is the anchor's zero point defensible for this class? The readiness tool ranks by
   pricing error — `closecombat` is the closest at ~15% median. Anything at 29–106% is
   telling you the anchor or the class membership is wrong, **not** that the units are wrong.
4. Set `signed_off` in `class_anchors.json` **one class per commit**, with the report and the
   numbers in the commit message.
5. ⚠ For the 13 classes locked on 2026-08-01 the anchor actor is **pre-restat** (G6). Sign off
   against the `spec`, and record explicitly that the actor still needs restatting.

**Done when:** every class is either signed off with its evidence, or has a written reason it
cannot be. **A documented refusal is a perfectly good outcome** — what is not acceptable is
leaving all 27 in silence, which is the state you inherited.

### ⭐ TASK D — RUN THE PIPELINE (G2) — deliver actual prices

**Only for classes signed off in Task C**, and only after Tasks A–C are recorded.

1. `python tools/balance/apply_balance.py --faction X` (dry run). Read every line of the diff.
2. If it is sane: re-run with `--confirm`, **one faction per commit**, dry-run diff in the
   message.
3. `python tools/balance/extract_stats.py`, commit the ledger in the SAME commit.
4. `python tools/audit/audit_balance_drift.py` must be green.
5. Boot-gate. Commit.
6. `python tools/balance/check_band.py` — every priced unit inside the 50–400% baseband.

**Done when:** at least one faction is fully priced through the pipeline end to end, with a
revert path per commit. **This has never happened. Doing it once for one faction is worth more
than any amount of further analysis.**

### ⭐ TASK E — CLOSE E2, THE PHYSICAL-STATE PRICING GAP (G5)

**Read:** `docs/design/PHYSICAL_STATE_SYSTEM.md`, and grep `DESIGN.md` for `state_w`.

`extract_stats` does not read `PhysicalState`, so ~89 live status-effect bindings are priced at
**zero** — a cryo weapon that halves enemy speed costs the same as one that does not. The
`state_w` term exists in `K` and the cryo 0.75× is an empirical measurement, not a
double-count.

**Done when:** `extract_stats` emits a physical-state weight per armament, `formula.py`
consumes it, and the dossier shows the price delta for a sample of the 89 bindings.

### ⭐ TASK F — WEAPON SHAPE (§11b.1) — the volume work, if you still have capacity

Only after A–E, or in parallel if you are confident. This is the largest job in the tree and
it is mechanical. **Script it; do not hand-edit 1,259 weapons.**

Per batch of ~20 weapons: `review_resolve_diff.py` before/after → `find_empty_warhead.py` = 0
→ boot gate → walk the `audit_weapon_shape` ratchets DOWN in the same commit.

⚠ **Effect templates: cluster by SHAPE, not by value.** The 687 weapons with local effects
produce **451** distinct value-signatures (335 used by exactly one weapon) but only **146**
distinct shapes, and the variation is concentrated in two fields — `CreateEffect.Explosions`
(170 distinct) and `CreateEffect.ImpactSounds` (113). Those two are the weapon's ART IDENTITY
and belong on the weapon; everything else belongs in the template. One template per value-set
would mean **451 templates for 687 weapons** — bigger, not smaller. Target ~15–25 templates.

⚠ **Do NOT write projectile fields onto every weapon.** `ScaledBullet` derives Inaccuracy and
Speed from Range, and an explicit yaml value always wins — it reached **zero** weapons for
weeks because templates also wrote literals. The template owns the fields; the weapon writes a
delta only where the resolved value genuinely differs. **Assert the DERIVED value on a real
resolved weapon**, never merely that the knob is present.

### ⭐ TASK G — THE DEEP RESEARCH: turn the reference corpus into per-class TARGETS

**This is the research half of the pipeline, and it is the piece nobody has done.** Everything
before it prices units *relative to an anchor we chose*. This task asks the harder question:
**is the anchor itself right?** — grounded in what 21 real shipped games actually did.

**Read, in this order:**

| document | what it holds |
|---|---|
| `docs/design/BALANCE_SYNTHESIS.md` | the plan for synthesising sources into class anchors — **this is the spec for this task** |
| `docs/design/ORIGINAL_UNIT_STATS.md` | the cross-game reference library (data-mining is DONE) |
| `docs/design/ORIGINAL_UNITS_RAW.md` / `_NORMALIZED.md` / `_PEER_OPENRA.md` | raw → normalised → OpenRA-peer stat tables |
| `docs/design/REFERENCE_EXTRACTION_PLAN.md` | rulings **R1–R15** governing how a reference may be used |
| `docs/design/UPSTREAM_MODS.md` | the five upstream mods, their lineage, and what is adoptable |
| `docs/balance/anchor_decisions_log.md` | why each of the 13 locked vehicle anchors was chosen |
| `docs/balance/discrepancies.md` | the Phase-3 triage still open against the legacy workbook |

**The data, all committed** (Part 2.5): `docs/reference/ini_corpus.json`, `versus_raw.json`,
`armor_normalized.json`, `faction_profiles.json`, `family_profiles.json`.
**Tools that already exist:** `faction_routes.py`, `faction_extrapolate.py --by-class`,
`assign_references.py`, `reference_distribution.py`, `normalize_armor.py`, `faction_profile.py`.

**The research questions, in priority order:**

1. **Does each of the 27 class anchors sit where the reference corpus says its class sits?**
   For each class, build the peer distribution from the routed sources and place the anchor in
   it. An anchor at the 5th or 95th percentile of its own class's real-world peers is a bad
   zero point, and that is a *far* better explanation for a 106% median pricing error than
   "the units are wrong".
2. **Which classes cannot be grounded, and why?** Currently **269 of 410** routed class members
   reach the ≥2-source floor. Name the classes that fall short and say whether the cause is
   missing sources, a bad route, or a class that no source game actually has.
3. **R4 synthesis — the actual deliverable.** Convert the grounded distributions into
   **per-class stat targets** (HP, DPS, speed, range bands) with the source rows behind each.
   That is what turns `class_anchors.json` from "someone picked a unit" into "this is where
   this class sits across 21 games".
4. **Cross-game rock-paper-scissors.** The mandate is that RPS holds *across* games — a Dune
   2000 tank must lose to the right Red Alert counter. Use `versus_raw.json` (2,494 profiles
   from 14 mods) to check whether Cameo's armor/warhead matrix reproduces the counter
   relationships the source games actually shipped, and report where it inverts.

⚠ **The two unroutable factions are `corrino` and `ixian`**, waiting on *Emperor: Battle for
Dune*, which nobody has. **Do not attempt to acquire it.** Treat those two as formula-only and
say so.

⚠ **Cluster, never average.** Averaging across sources destroys exactly the variety this is
meant to preserve: one reference faction can be uninformative for a whole type (OpenE2140's
`ed` fields four infantry at HP 28/28/28/20), and placing nine Naxis infantry against that
would have *deleted a roster's variety while looking like evidence*. Interpolate in **log**
space — nearest-point placement collapsed six Naxis infantry spanning 20,000–96,000 HP onto one
value.

⚠ **Never invent faction data from game knowledge.** If a source is not in the corpus, it is
not evidence. This is ruling R-series law and it has been violated before.

**Done when:** `docs/design/BALANCE_SYNTHESIS.md` carries per-class targets with the source rows
behind each, every anchor has a percentile placement inside its own class's peer distribution,
and any anchor the research says is misplaced is named with the replacement it suggests.

⭐ **If Task C's sign-off stalls because the errors are too large to accept, THIS is the task
that unblocks it** — a 106% median error is usually a misplaced anchor, and this is how you
prove it rather than guess.

### ⭐ TASK H — THE AI BOT MODULES: inherit Devin Cloud's work and carry it forward

**Why this is yours now.** Devin Cloud built the module architecture and then ran out of usage
quota mid-merge. The design is good and it should not be restarted — **inherit it, do not
re-derive it.** The maintainer's order: *"Astra should just continue the new Bot Module
architecture as well and also merge those pull requests that he made."*

**Read first — this is done work, not a blank page:**

| where | what it holds |
|---|---|
| `docs/design/AI_ARCHITECTURE.md` **§10** | the per-module build plan: one authority per decision (10.1), what Cameo loads today (10.2), the single shared snapshot (10.3), the one synced piece (10.4), cadence (10.5), **the phase order (10.6)**, failure modes the shape avoids (10.7) |
| `docs/design/AI_ARCHITECTURE.md` **§11** | the reconciliation of the FIRST five-agent research round — what came back, **claims rejected with what falsifies them**, recommendations adopted, and what was rejected as a design change |
| `docs/design/AI_ARCHITECTURE.md` §0–§9 | goal, verified facts, ContentPack splitting, observation model, personality manager, master module, logging/learning, risks, prior outside research, open decisions |
| `docs/design/ROADMAP.md` | the AI phase entries |

⭐ **Both sections landed on master as PR #324 on 2026-09-06 and are already merged.** Start
from them.

#### H.1 — Merge PR #323, the only piece still outstanding

```
gh pr view 323 --repo cameo-mod/Cameo-mod
```

⚠ `gh` may default to the wrong remote in this checkout — **always pass
`--repo cameo-mod/Cameo-mod`**, or `gh pr view 323` returns "Could not resolve".

**Observer: Combat Effectiveness graph** — value destroyed minus value lost, over time.
Branch `devin/1788250214-combat-effectiveness-graph`, **+233/−12**, status
**CONFLICTING / DIRTY**.

Files: `OpenRA.Mods.Cameo/Traits/Player/CombatEffectivenessStatistics.cs`,
`OpenRA.Mods.Cameo/Widgets/ScrollableLineGraphWidget.cs`,
`OpenRA.Mods.Cameo/Widgets/Logic/CameoObserverStatsLogic.cs`,
`OpenRA.Mods.Cameo.Test/ScrollableLineGraphWidgetTest.cs`,
`mods/cameo/chrome/ingame_observer.yaml`, `mods/cameo/fluent/en.ftl`,
`mods/cameo/rules/player.yaml`, `docs/LESSONS_LEARNED.md`.

⚠ **This one touches C#, so it is NOT a docs merge:**

1. Resolve the conflict on a branch. Master has moved a long way since 2026-09-01 — expect the
   conflicts in `en.ftl` and `player.yaml`, which many agents touch.
2. **Rebuild before booting:**
   `DOTNET_ROLL_FORWARD=LatestMajor dotnet build -c Release --nologo -p:TargetPlatform=win-x64`
   The build deploys to `engine/bin`, which is what the game LOADS. The tracked
   `mods/cameo/OpenRA.Mods.Cameo.dll` copy does **not** auto-update, and a stale DLL crashes
   the boot with `Cannot locate type: …Info`.
3. Boot-gate (Part 0.4). Then merge.
4. ⚠ **Do not merge it if you cannot boot-gate it.** A C# merge that has not booted is exactly
   the class of change that takes the whole tree down for six other agents.

⭐ **Technique already proven here:** observer UI can be verified without playing a match by
launching with `Launch.Replay=<file>`. That is how the spectator set was verified live. Use it
rather than trying to reproduce a battle.

#### H.2 — Write the full module interaction specification

§10 gives the plan and the phase order. What it does **not** yet give in full is the
**interaction contract** — the maintainer asked specifically for *"what each module owns, what
it reads, how they talk to each other, and where the synced/unsynced boundary sits."*

Extend `AI_ARCHITECTURE.md` (do **not** create a new document) with, for **each of the 20
loaded modules**:

* **owns** — the decisions it alone may make. §10.1 is "one authority per decision"; make it
  explicit per module.
* **reads** — what it consumes from the shared snapshot (§10.3), read-only.
* **publishes** — what other modules may consume from it, and at what cadence (§10.5).
* **synced or unsynced** — with the justification. ⚠ §10.4 already establishes that the
  personality switch needs **one small synced trait**, because the existing
  `GrantConditionOnOrders` would clear the personality the moment the bot places a building.
  **Anything affecting simulation state must be synced or it desyncs multiplayer.** This is the
  single highest-risk axis in the whole design.
* **failure mode** — what happens when it has no data, is starved of cadence, or disagrees with
  another module. §10.7 lists the failure modes the shape was chosen to avoid; extend it.

Deliver a table plus one paragraph per module, and one text diagram of the data flow.
**Keep §11's rejected claims rejected** — do not quietly re-adopt something the first research
round already falsified.

#### H.3 — The SECOND research round: five agents, no overlap

The maintainer has **Perplexity, Grok, ChatGPT, Copilot and Gemini** available and wants them
used. **A round already happened and is reconciled in §11 — do not repeat it.** Read §11.1
("what actually came back") and §11.2 ("claims rejected, with what falsifies them") FIRST, then
write briefs that go where the first round did not.

Write five **differentiated** briefs to `docs/design/AI_RESEARCH_BRIEFS_ROUND2.md`, one per
agent, each answering a question the others are not asked. This split worked last time, and it
works because **it makes the answers merge instead of repeating each other**:

| agent | its lane |
|---|---|
| **Perplexity** | the literature — published RTS-AI work, what has been tried and measured |
| **Grok** | read the OTHER mods' code — how CA, AS, Mental Omega, Shattered Paradise and Generals Alpha actually implement bot decisioning |
| **ChatGPT** | the decision mathematics — bandits, priors, the counter-demand model, and fitting them on few matches |
| **Copilot** | desync and feasibility — what can and cannot be done unsynced in OpenRA, and the cost of each synced trait |
| **Gemini** | the yaml and the migration — how this lands across 24 ContentPacks with zero cross-pack dependencies |

**Each brief must state:** the question, what is already settled (with the §-number, so nobody
re-answers it), what would count as evidence, and what would falsify the answer.

⚠ **Then reconcile, do not average.** §11 got this right and it is the standard to hold:
**keep disagreements explicit and record what falsifies each rejected claim.** Five agents
blended into one mush is worse than one good answer, because it hides which parts are actually
load-bearing.

#### H.4 — Then build, in the phase order §10.6 already fixed

**Do not re-order these.** The order was chosen so each phase ships on its own:

1. **Match logging, record-only** — no behaviour change. Gets the learning loop data before any
   decision code exists, and exercises the log schema while it is still cheap to change.
   ⭐ **This is your next implementation step, and it is deliberately the safest one.**
2. `MasterAiBotModule`, observe-only — builds and publishes the snapshot, decides nothing.
3. `BotPersonalityController` + dynamic switching — the first behaviour change, difficulty-gated.
4. Main target selection, consumed by the squad managers and support powers.
5. Counter demand and hints — `ProvidesPrerequisite` tokens, **zero C#**.
6. Fogged observation + `ScoutBotModule` — **deliberately last**, because it makes the bots
   temporarily weaker and invalidates any tuning done against omniscient signals.
7. Offline learning — aggregate logs, fit bandit priors per (faction, personality, enemy
   strategy), commit as reviewed data. **Nothing neural until balance is frozen.**

⭐ **Phases 1 and 2 are pure additions with no gameplay effect and can proceed while the balance
pipeline is still moving.** That is why this task can run alongside Tasks A–G rather than after
them.

⚠ **Personality-tagged compositions need ZERO C#.** A condition-gated player-level
`ProvidesPrerequisite` already ships at `mods/cameo/rules/ai.yaml:176`. Do not write a trait for
something the yaml already does — check it before building anything for phase 5.

**Done when:** #323 is merged (or documented as un-mergeable, with the reason), the interaction
contract exists per module in `AI_ARCHITECTURE.md`, the five round-two briefs are written and
their answers reconciled with disagreements kept explicit, and **phase 1 (record-only match
logging) is implemented, boot-gated and merged.**

⚠ **Priority note:** the balance pipeline (Tasks A–G) remains your primary mission. This task
exists because phases 1–2 cost nothing in gameplay risk and the design work is already done —
not because it outranks pricing. If you must choose, **price a faction first.**

---

## PART 7 — HOW TO WORK. SPECIFIC SUGGESTIONS.

1. **Measure before you describe.** Never write "most", "only" or "easy" without a count. Two
   false claims in one session came from generalising a documented granularity.
2. **Read the RESOLVED node, not the source.** A child's `Modifier: 100` is usually a
   CANCELLATION of an inherited value; a review of "20 no-ops" found 19 were cancellations.
   Use `miniyaml.Ruleset.resolve_weapon` / `.resolve`, and pull Versus with
   `weapon_efficiency.versus_of(node)`.
3. ⛔ **NEVER hand-parse yaml.** A bespoke line-scanner opened a dict on `Versus:` and never
   closed it, so sibling `PercentageVersus:` rows overwrote the profile. Every measured mean,
   spread and ratio came out internally consistent and **completely wrong**.
4. **`Node.child()` is an EXACT match** and misses `@suffixed` traits. Use `children_named()`.
   This one bug made 97% of the mod's production buildings invisible to an audit that then
   reported "0 violations" — a check incapable of failing.
5. **A ratchet only ever goes DOWN**, and it moves in the SAME commit as the change. Never
   lower one in advance for work that might be reverted.
6. **Prefer a script over a sweep.** Batch mechanical work over the model/registry; never read
   file-by-file. Verify with the audit suite (cheap) rather than re-reading yaml.
7. **When you find a trap, write it into `LESSONS_LEARNED.md`** in the same session. When you
   find a law, it goes in `DESIGN.md`. When you find a number a decision rests on, it goes in
   `docs/audit/doc_claims.yaml` with its re-measure command. **One home per fact** — a fact in
   two places is a future contradiction.
8. ⛔ **A 0% compliance row is a bug report about the CHECKER.** Eight factions read exactly
   0% naming compliance for months; it was a doubled prefix in one config table, and seven of
   them jumped to 100% when it was fixed. Real non-compliance is ragged; a clean zero across a
   whole population means the predicate can never be true. **Read what the checker EXPECTED
   before reading what the data contains.**
9. **Never act on a generated proposal without eyeballing three lines of it.** That same map
   literally said `ra1_soviets_btr80: ra1_ra1_soviets_btr80`, and 181 files were renamed
   before anyone looked.
10. **Do not chase a stale summary.** When a document and the artifact disagree, **the artifact
    wins** — then fix the document.

---

## PART 8 — WHAT NOT TO DO

* ⛔ Do not create a new planning document, roadmap or handoff. Blackrobe's own words:
  *"use the documents already there, not create another competing planning system."* Everything
  you produce goes into the documents named in Part 3, or into your dossier.
* ⛔ Do not rename actors or weapons. That work is assigned to other agents and will collide.
* ⛔ Do not touch `engine/`. It is gitignored, has no `.git`, and `make all` deletes it.
* ⛔ Do not add a second copy of a route list, a source list or a class map.
* ⛔ Do not try to obtain reference game data. Everything extractable is already in
  `docs/reference/`.
* ⛔ Do not spend your budget on further ANALYSIS of the balance model. It has been analysed
  extensively. **It has never been RUN.** Prefer one faction actually priced over another
  document about pricing.

---

## PART 9 — WHAT SUCCESS LOOKS LIKE

In order of value:

1. **One faction priced end to end through the pipeline**, committed with a revert path. This
   has never happened, and it proves the whole machine works.
2. **Class anchors signed off** with written evidence — or refused with written reasons.
3. **Class coverage well above 32.4%.**
4. **E2 closed** so status effects are priced at all.
5. **A review dossier** at `docs/audit/ASTRA_REVIEW.md` the maintainer can audit in an hour.
6. Weapon-shape ratchets lowered, with the boot gate green at every step.
7. **AI phase 1 (record-only match logging) shipped**, PR #323 merged, and the module
   interaction contract written — see Task H. Phases 1–2 carry no gameplay risk, so they
   can run alongside the pricing work.

**If you achieve only #1, this will have been the most valuable single contribution to the
project so far.**

---

**Sign every commit:**

```
Co-Authored-By: Blackrobe GPT-6 Astra <blackrobe@users.noreply.github.com>
```

**Branch:** `astra/balance-pipeline` · **Never push to master.** · **Report in
`DEVELOPMENT_LOG.md` on your branch, one entry per completed item, and never wait for a reply.**

Good luck. The pipeline is built and tested and has never been run to completion. Run it.

— Claude-Local (Opus 5), fleet coordinator, 2026-09-06
