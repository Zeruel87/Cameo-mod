# Lessons Learned — read before every task

**Read this file, `AGENT_WORKSPACE.md`, `HANDOFF.md` and the relevant sections of `DESIGN.md`
before touching any code, YAML, asset or balance value.**

This is the repository-owned record of hard-won lessons, safe defaults and recurring pitfalls.
Every entry was paid for once — the point of the file is that it is not paid for twice.
**Add new lessons here**, not in a session log and not in a memory. When you add a `##` section,
add it to the Contents below: `audit_doc_health` D7 fails if the index misses one.

---

## Required reading order for every new task

**`docs/README.md` is the canonical definition of the reading order.** The list below is a
convenience copy; if they disagree, README wins and this copy gets fixed.

1. `CLAUDE.md` (repo root) — the hard rules, loaded every session.
2. `docs/LESSONS_LEARNED.md` (this file) — safe defaults and pitfalls.
3. `docs/AGENT_WORKSPACE.md` — source-of-truth map, operating sequence, incident protocol, commit gate.
4. `docs/HANDOFF.md` — verified current state and the priority-ordered queue.
5. `docs/DESIGN.md` — binding rules; read the sections your change touches.
6. `docs/design/ROADMAP.md` — the granular work queue.
7. `docs/audit/SUMMARY.md` — known issue classes and current audit counts.
8. `docs/Cameo_Knowledge_Base_Manual.md` — engine and custom-trait reference, as needed.

When this document and `DESIGN.md` conflict with code or old notes, the repository documents
win — **unless the artifact says otherwise, and then the artifact wins and you fix the document.**

---

## Contents

**Crash classes — these end a boot, and most gates cannot see them**

- [`Parent type X was already inherited` — the crash class nothing but the boot could see (2026-08-17)](#parent-type-x-was-already-inherited--the-crash-class-nothing-but-the-boot-could-see-2026-08-17)
- [Interactable trait and upgrade actors (2026-07-24)](#interactable-trait-and-upgrade-actors-2026-07-24)
- [ClassicProductionQueueProperties crash on actors with no queue (2026-07-31)](#classicproductionqueueproperties-crash-on-actors-with-no-queue-2026-07-31)
- [Empty warhead type = boot NRE; check-yaml does not catch it (2026-08-04)](#empty-warhead-type--boot-nre-check-yaml-does-not-catch-it-2026-08-04)

**Silent-corruption classes — valid yaml, clean boot, wrong game**

- [⛔ NEVER HAND-PARSE YAML — a sibling node silently overwrote every Versus number (2026-08-22)](#-never-hand-parse-yaml--a-sibling-node-silently-overwrote-every-versus-number-2026-08-22)
- [Five bug classes from the W25 armor/Versus rebuild (2026-08-16/17)](#five-bug-classes-from-the-w25-armorversus-rebuild-2026-08-1617)
- [3-way split retrofits: two recurring child-weapon bugs (2026-08-08)](#3-way-split-retrofits-two-recurring-child-weapon-bugs-2026-08-08)
- [Bulk YAML rename scripts: safety lessons (2026-07-31)](#bulk-yaml-rename-scripts-safety-lessons-2026-07-31)
- [Loose-extracted .oramap maps must always be repacked before finishing a task (2026-07-31)](#loose-extracted-oramap-maps-must-always-be-repacked-before-finishing-a-task-2026-07-31)
- [Effect-warhead merge safety during 3-way split (2026-08-07)](#effect-warhead-merge-safety-during-3-way-split-2026-08-07)
- [Measure the law's OWN pipeline, and never validate a rule against the corpus it generated (2026-08-24)](#measure-the-laws-own-pipeline-and-never-validate-a-rule-against-the-corpus-it-generated-2026-08-24)
- [An audit is not evidence of a law — two guards enforced retired designs (2026-08-24)](#an-audit-is-not-evidence-of-a-law--two-guards-enforced-retired-designs-2026-08-24)
- [Porting from an upstream mod: a NEW NAME is not a NEW MECHANIC (2026-08-23)](#porting-from-an-upstream-mod-a-new-name-is-not-a-new-mechanic-2026-08-23)
- [`Inherits` POSITION is semantic, not cosmetic (2026-08-16)](#inherits-position-is-semantic-not-cosmetic-2026-08-16)
- [Upgrade regressions feel like downgrades (2026-08-19)](#upgrade-regressions-feel-like-downgrades-2026-08-19)

**Weapon templates, the 3-way split and the effect layer**

- [Weapon effect-layer `DamagesConcrete` handling (2026-08-20)](#weapon-effect-layer-damagesconcrete-handling-2026-08-20)
- [Weapon template retrofit — Phase A lessons (2026-08-02)](#weapon-template-retrofit--phase-a-lessons-2026-08-02)
- [Weapon 3-way split — effect/projectile pitfalls found during the effects-table pass (2026-08-05)](#weapon-3-way-split--effectprojectile-pitfalls-found-during-the-effects-table-pass-2026-08-05)
- [Weapon 3-way split: projectile family naming (2026-08-07)](#weapon-3-way-split-projectile-family-naming-2026-08-07)
- [Template location and PhysicalStates forms (2026-08-20)](#template-location-and-physicalstates-forms-2026-08-20)
- [Contrail fields are projectile, not warhead, and can survive a projectile type swap (2026-08-20)](#contrail-fields-are-projectile-not-warhead-and-can-survive-a-projectile-type-swap-2026-08-20)
- [Inline effect warheads should be inherited, not inline (2026-08-19)](#inline-effect-warheads-should-be-inherited-not-inline-2026-08-19)

**Balance pipeline and formula**

- [Latest lessons from the July 2026 infantry rebalance pass](#latest-lessons-from-the-july-2026-infantry-rebalance-pass)
- [Class-specific notes](#class-specific-notes)
- [Uniqueness enforcement](#uniqueness-enforcement)
- [Dual-weapon units](#dual-weapon-units)
- [Audit and pipeline findings from 2026-07-22](#audit-and-pipeline-findings-from-2026-07-22)
- [Tooling fixes discovered during W24 A1a (2026-08-22)](#tooling-fixes-discovered-during-w24-a1a-2026-08-22)

**Process, tooling and platform**

- [YAML-only AI personalities and dead squad-manager keys (2026-08-21)](#yaml-only-ai-personalities-and-dead-squad-manager-keys-2026-08-21)
- [Opt-in AI unit compositions (2026-08-24)](#opt-in-ai-unit-compositions-2026-08-24)
- [A ContentPack can only ADD to a bot module - and a partial migration fails silently (2026-08-31)](#a-contentpack-can-only-add-to-a-bot-module---and-a-partial-migration-fails-silently-2026-08-31)
- [Content installer and music filesystem plumbing (2026-08-11)](#content-installer-and-music-filesystem-plumbing-2026-08-11)
- [Git workflow and commit rules (2026-07-24)](#git-workflow-and-commit-rules-2026-07-24)
- [YAML lint rules learned (2026-07-24)](#yaml-lint-rules-learned-2026-07-24)
- [OpenRA Lua `Map` API: there is no `Map.Contains` (2026-07-31)](#openra-lua-map-api-there-is-no-mapcontains-2026-07-31)
- [Between-cell movement responsiveness (2026-08-11)](#between-cell-movement-responsiveness-2026-08-11)
- [`docs/audit/latest/` is environment-bound — an incomplete tree reports LESS and still says PASS (2026-08-23)](#docsauditlatest-is-environment-bound--an-incomplete-tree-reports-less-and-still-says-pass-2026-08-23)
- [Two ways a gate passes its own verification and is still broken (2026-08-23)](#two-ways-a-gate-passes-its-own-verification-and-is-still-broken-2026-08-23)
- ["Regenerable" is a claim about a tool, and it needs running (2026-08-28)](#regenerable-is-a-claim-about-a-tool-and-it-needs-running-2026-08-28)
- ["Not found" is not "not there" — three ways a grep lies (2026-08-28)](#not-found-is-not-not-there--three-ways-a-grep-lies-2026-08-28)

---

## YAML-only AI personalities and dead squad-manager keys (2026-08-21)

The Cameo AI personality selector uses `GrantRandomCondition` on the inherited
`Player` actor and gates five independent `SquadManagerBotModuleCA` instances
with mutually exclusive personality conditions. The instances must duplicate
their shared fields: YAML trait inheritance is keyed by the trait suffix, so a
shared fallback can leave live managers with different or incomplete values.
`tools/audit/audit_ai_personalities.py` compares every non-tuning field
byte-for-byte and checks selector/consumer condition parity.

`RushInterval` and `RushAttackScanRadius` are stale squad-manager keys. They
are absent from both the vendored CA trait and the pinned engine, and must not
be copied into new instances. Steamroller cannot express zero guerrilla units
in YAML: the engine's `guerrillaForce == null` short-circuit creates the first
guerrilla squad regardless of `JoinGuerrilla`, so its documented behavior is
at most one harasser.

The personality indicator uses a reusable `ObserverConditionNotification`
trait rather than a personality-specific UI path. It announces once after a
short delay to spectators and replay viewers through the local chat feed, while
live players are excluded so opponent strategy is not revealed. Keep this
observer-only behavior display-local and out of synchronized game state.

## Opt-in AI unit compositions (2026-08-24)

When porting a composition selector into a divergent unit builder, keep the
consumer opt-in and preserve the existing `UnitsToBuild` table as the fallback
rather than introducing a second baseline configuration. Resolve shares by
production queue category, and keep explicit unit requests on their existing
bypass path so harvesters and MCVs are not blocked by composition filtering.
Composition candidates must be gated by time, per-composition interval,
technology prerequisites, and whether their units are producible in the
player's queues. Parallel production queues must count every queued unit
toward produced-value expiry.

When a squad manager gains optional time-scaled value thresholds, retain the
flat `SquadValueRandomBonus` path for existing consumers and reject configuring
both modes on one instance. Cache `ValuedInfo.Cost` by actor type when summing
idle units; missing `ValuedInfo` must remain a cached zero rather than changing
the threshold behavior.

## Content installer and music filesystem plumbing (2026-08-11)

- Mounting `^SupportDir|Content/cameo/` does not recursively mount nested
  packages. A nested `scores.mix` must be mounted explicitly, while the
  Firestorm directory can be mounted because its `.aud` files are direct
  children.
- `Music:` in `mods/cameo/mod.yaml` loads `mods/cameo/music.yaml`; the
  similarly named `mods/cameo/audio/music.yaml` is not loaded automatically.
- `ModContent.TestFiles` must match the exact extraction destinations in the
  download manifest, including every file required for a complete package.
- Keep `ContentPackages:` empty and omit `RequiredContentFiles:` when content
  installation must remain opt-in through Manage Content. Installer package
  `Required` flags do not replace those filesystem-loader checks.
- `cameo-content` is deliberately hyphenated to match the engine's
  `*-content` mod convention; it is an explicit exception to Cameo's
  underscore-only in-mod naming rule.

## Weapon effect-layer `DamagesConcrete` handling (2026-08-20)

- `DamagesConcrete` is a separate warhead trait. It is NOT automatically
  redundant with `SpreadDamage` or `AreaDamage`; it must be preserved unless the
  source behavior proves it is accidental or duplicate.
- When a weapon inherits multiple effect templates (e.g. old full-stack or
  3-way-split intermediates), the same `DamagesConcrete` node can be inherited
  more than once. Use `tools/audit/effect_audit.py` (or `scratchpad/`) to scan
  all resolved weapons; the target is **0 weapons with >1 `DamagesConcrete`**.
- Effect templates should remove inherited generic concrete with
  `-Warhead@Concrete` and re-add a single `Warhead@Concrete: DamagesConcrete`
  with the intended local value when the effect is meant to be standalone.
- Weapon children that need a different concrete value should override with a
  single `Warhead@Concrete:` key; matching keys merge, so only the last value
  survives.

## ⛔ NEVER HAND-PARSE YAML — a sibling node silently overwrote every Versus number (2026-08-22)

A whole day of weapon-profile analysis produced confident, internally consistent, WRONG numbers,
because the reader was a bespoke line-scanner instead of the project's resolver.

The scanner opened a dict on `Versus:` and then kept absorbing any `Key: <int>` line. It never
CLOSED the block. The AreaDamage fold had since added `PercentageVersus:` INSIDE the same warhead
node, so the twin's rank ladder overwrote the real profile row by row:

```
Warhead@Bullet_Light: AreaDamage
    Versus:            None: 200 ... Superheavy 48   <- the real profile, mean 100
    PercentageVersus:  None: 16  ... Superheavy  1   <- what got read, mean 8.5
```

**What it cost.** Reported "0 of 125 profiles obey the MEAN-100 law" (truth: **123 of 125**),
"every family violates the 2x-8x spread band" (truth: **39 of 42 in band, median 4.17x**),
an additive `+4/+5` level offset that was really the rank ladder stepping 1/5/10, "26 of 42
families invert", and "a Heavy weapon self-prices at ~2x a Light one" (truth: the Heavy/Light
weighted-mean Versus ratio is **1.00x** — the level does not price through Versus at all, exactly
as §12.0h intends). Two design documents were written and committed on those numbers.

**The rules:**

1. **Read through `miniyaml.Ruleset.resolve_weapon` / `.resolve`**, and pull Versus with
   `weapon_efficiency.versus_of(node)`. They return structured nodes and cannot confuse siblings.
2. If a hand parser is genuinely unavoidable, **CLOSE every block on indentation** — the moment
   indentation returns to the opening key's level or shallower, the block is over.
3. **A near-miss name is the danger**: `PercentageVersus` does not `startswith("Versus:")`, so the
   opening guard looked correct. The bug was the missing CLOSE, not the missing open.
4. **Sanity-check against a stated law before believing a result.** "0 of 125 conform to a binding
   law that the generator implements and `verify_generator_sync` reports 0 drift on" is not a
   finding, it is a contradiction — and the contradiction was visible immediately.

Guarded by `tools/audit/audit_versus_profile.py`, which reads through the resolver on purpose.

**And the deeper miss:** `docs/DESIGN.md` is required reading #4 in CLAUDE.md ("the binding design
contract ... Read it before touching any yaml"), and it already contained §12.0h (MEAN-100),
§12.0c (the Shield ladder) and §12.0d (the class tilt). Days of design work re-derived rulings
that were already made and already shipped. **Before designing anything, grep DESIGN.md for the
concept.** A design question that feels novel usually is not.


## Five bug classes from the W25 armor/Versus rebuild (2026-08-16/17)

All five were **invisible to every gate we run** — valid yaml, values inside the window, the
resolver happy, `find_empty_warhead` 0, and the game booting to the menu. A boot gate cannot
see a number that is merely WRONG. Each now has a guard, because each was found by accident.

### 1. A PSEUDO-ARMOR ROW DRIVING A WINDOW SCALE (the worst one)

`finish_blend` scaled a blend back into `[10, 200]` with `max(values.values())` — which
included **`Shield`**, a row deliberately OUTSIDE the window in both directions. So the
shield value, not the armor ladder, set the scale for the whole profile. A quiet ~2x crush
while Shield ran 100..400; **catastrophic** once Shield began being emitted in centi-units:
`Quantum_Light` scaled by `200/18535 = 0.011`, every armor rounded to 0 or 1, and
`distinct_ints`' floor-repair pass then **FABRICATED the entire ladder** from the emit order.

It hid because `mean_normalise` runs afterwards and scaled the garbage back to a mean of 100.
The profiles looked plausible and passed every check. The only trace was "23 non-monotone
ladders", which read like a cosmetic ordering issue and was actually a ladder that had
stopped carrying data.

**Rule: any statistic over a Versus node must state which rows it excludes.** Use
`NON_ARMOR_ROWS`, never `max(values)`.

### 2. FILTERING BY NAME WHERE THE TYPE IS AUTHORITATIVE

Excluding %-twins by an `endswith("_Percentage")` KEY suffix silently let ~50 legacy
templates through — they name theirs `Warhead@SmallArmsPercentage`, no underscore. Their
`Versus` is a MAGNITUDE (17, 25), so a mean came out 157 instead of 209: a **34% error**.

**Rule: filter warheads on the TYPE (`"Percentage" in child.value`), never on the key name.**
A naming convention is not an invariant; the type is.

### 3. SCANNING DEAD FILES

`mods/cameo/**/*.yaml` includes files mod.yaml does NOT load — `rules/redalert2.yaml` and
siblings are dead copies ("now loaded via include-only wrapper packs … not loaded here to
avoid duplicate keys", mod.yaml:176). A new audit reported a stale flat modifier on a
template whose LIVE copy had already been fixed.

**Rule: audits read `Ruleset(ROOT).manifest.rules`, not a glob.** A dead file is not
evidence about what ships.

### 4. A COMBINATION RULE THAT MADE AN UPGRADE HARMFUL

W21 flipped multiple armors from MULTIPLY to AVERAGE and **nobody restated the values**.
Under multiplication a row of 50 meant "half the damage", target-independent; averaged it
gives `(base+50)/2` — at base 100 a **25%** cut, not 50%. So every overlay's effect was
silently halved, and worse, `(base + plating)/2 > base` whenever the plating row exceeded the
class row: **98 of 1152 cells took MORE damage for wearing armor**, worst 1.84x, hitting
HEAVY units hardest because they have the low class rows.

**Rule: AN ARMOR UPGRADE MUST NEVER INCREASE INCOMING DAMAGE** (DESIGN §12.0e law 4).
Guard: `audit_armor_upgrade_harm.py`. And when a combination rule changes, re-derive every
value that was authored against the old one.

### 5. A MISSING ROW IS NOT "NO OPINION"

Both the engine and Cameo's `DamageVersus` select armors with `Versus.ContainsKey(type)`, and
an EMPTY match list `return 100`. So for a LAYER-SELECTED armor, omitting a row does not mean
"this weapon ignores the plating" — it means the plated unit **loses its armor entirely**. A
superheavy tank would take 100% from bullets instead of ~20%. I wrote this warning and then
made the exact mistake in my own code by skipping the flat families.

**Rule: every plating gets a row in EVERY template, no exceptions.** Guard:
`audit_armor_upgrade_harm.py` I1.

### And a process slip worth its own line

`audit_balance_drift` went RED with all 32 ledgers drifted, because seven yaml commits landed
without re-running `extract_stats`. CLAUDE.md requires committing **yaml and ledger
TOGETHER**. Re-extract before every commit that moves a balance number, not at the end of a
session.

### The naming trap that keeps recurring: Integrity is NOT a shield

`Integrity.cs` shipped for months with every `[Desc]` copied verbatim from `Shielded.cs`, and
the wrong word spread into the warhead's `[Desc]`, the generator's comments and a handoff doc.
**`Integrity` absorbs NOTHING** — `INotifyDamage` runs after the damage has landed on health —
so it buys no survivability and only gates the EMP disable. The only thing it shares with a
shield is the FIELD SHAPE (`MaxStrength + MaxPercentageStrength`). Corrected 2026-08-17.

---

## `Parent type X was already inherited` — the crash class nothing but the boot could see (2026-08-17)

The engine refuses to load a node that reaches the **same parent twice along one ancestor chain**
(`engine/OpenRA.Game/MiniYaml.cs` → `ResolveInherits`; `inherited.Add(name, loc)` throws). The RA2
effect-template refactor produced **30** of these at once — a weapon inheriting `^Effect_X_Heavy`
directly *and* a new `^Effect_*_RA2` wrapper that inherits the same parent.

Three properties, each counter-intuitive enough to have cost real time:

* ⛔ **The `@suffix` does NOT make it legal.** The guard is keyed on the parent **TYPE**. The
  crashing lines were `Inherits@4:` and `Inherits@fx:` — both suffixed. A previous handoff of mine
  claimed the suffix "is what makes repeated inherits legal"; that is **false**, and it sent
  another agent hunting for bare `Inherits:` lines — a search that finds nothing while 30
  collisions are live. **Grep is not a test for this class.**
* **A diamond is legal.** Two sibling parents that each inherit a common grandparent are fine:
  the accumulated set is passed BY VALUE, so additions inside one sibling's recursion do not escape.
* ⚠ **It is ORDER-DEPENDENT.** `Inherits: A` then `Inherits@2: B` where `B` inherits `A` crashes;
  the same two lines swapped load fine. **Reordering an inherit block can break a working weapon**
  — a direct hazard for W24's inherit collapse.

Two process lessons on top of the engine one:

1. **The boot is a terrible detector for a class it can only report ONE instance of.** It throws on
   the first collision and stops, so N collisions cost N launch cycles (~40 s each plus diagnosis).
   `audit_duplicate_inherits.py` (in `run_all.sh`) reports all of them in one pass: **D1** the crash,
   **D2** a redundant parent that only line ORDER is saving, **D3** a dangling target.
2. **A MiniYaml load failure can leave a zero-length `perf.log` and no obvious window.** The
   exception log does appear, but the fast path to the diagnosis is running the engine binary
   directly and reading **stderr** — `launch-game.cmd` swallows it behind `pause`.

**Fix:** delete the redundant DIRECT inherit (the other parent already provides it). Reordering
also silences the crash but leaves the redundancy behind as a D2.

---

## 3-way split retrofits: two recurring child-weapon bugs (2026-08-08)

Discovered during a deep review of conversion commits made 2026-08-07/08.
Both are silent (no boot crash, no audit red) but corrupt gameplay. The
canonical retrofit tool does NOT catch either; both require a manual
post-conversion sweep of every weapon that inherits a CONVERTED parent.

### Bug A — main warhead type left as `SpreadDamage` (should be bare)

When a weapon's parent template was flipped from `SpreadDamage` to
`AreaDamage` (the universal conversion, `3dac92ee8`), every concrete
override of the main warhead key that still says `Warhead@X: SpreadDamage`
RE-DECLARES the type, blocking the inherited `AreaDamage` and its baked
friendly fire. The weapon fires `SpreadDamage` with NO friendly fire.

**Detection:** `python tools/balance/sweep_areadamage.py` (dry-run) lists
every `Warhead@X: SpreadDamage -> bare` candidate. The sweep is
resolution-aware (only touches keys a weapon actually inherits from a
`^Warhead_*` template) — apply with `--apply`. **Caveat:** the sweep
misses some `@wh2` dual-inherit patterns; re-run the dry-run after
applying and hand-fix any remaining `SpreadDamage -> bare` lines.

### Bug B — child weapons keep OLD warhead keys (orphaned double-fire)

When a parent weapon's `Warhead@<OldKey>` was renamed to
`Warhead@<NewKey>` (e.g. `Warhead@TeslaWeapon` -> `Warhead@Tesla_Heavy`),
every CHILD that inherits the parent and overrides the OLD key
(`Warhead@TeslaWeapon: SpreadDamage\n  Damage: 4000`) now creates a NEW
orphaned warhead node — the parent's new key fires AND the child's old
key fires. **Result: double damage.**

**Detection:** after converting a parent, grep every child (weapons that
`Inherits: <ParentName>` or `Inherits: <ParentName>_elite`) for the OLD
warhead key names. The subagent review pattern: `git show <commit>^:<file>`
to see pre-conversion keys, then check every child of every converted
parent for the same old keys.

**Both bugs** are caused by the retrofit tool only editing the converted
weapon itself, not its children. The fix is a post-conversion sweep:
1. `sweep_areadamage.py --apply` (bug A);
2. for each converted parent, grep its children for old keys (bug B).

**Comprehensive sweep done 2026-08-08** (`tools/audit/find_orphan_old_keys.py`
+ `tools/balance/fix_orphan_old_keys.py --apply`): found and fixed **107
orphaned old-key warheads** across 12 files (41 mains renamed, 41
percentages renamed, 25 FriendlyFire twin blocks deleted). Detector is
resolution-aware (only flags old keys where the converted parent has the
corresponding new key — excludes legitimate "child adds new warhead
type" cases). Re-run the detector after any future conversion batch;
it exits 0 candidates when clean. Bug B is now CLOSED across the
codebase.

### Effect/water preservation when moving to ^Effect_MissileHE_*

The new `^Effect_MissileHE_Light/Medium/Heavy` templates do **not** include `Warhead@EffectWater`. A weapon that previously resolved with a water splash (via `^FlakWeapon`, `^Grenade`, `^MediumMissile`, `^HeavyMissile`, etc.) will silently lose it unless a local `Warhead@EffectWater: CreateEffect` is kept. `review_resolve_diff.py` compares resolved `CreateEffect` fields, but `EffectWater` is a separate node; always inspect the full resolved FX dump for both `Effect` and `EffectWater` blocks.

Likewise, `ImpactActors: false` on `Warhead@Effect` can come from an old full-stack family (`^Grenade` sets it). The new `^Effect_MissileHE_*` templates do not, so the resolved effect must carry a local `ImpactActors: false` override where the old stack had it.

**Rule:** after reparenting a weapon, run `review_resolve_diff.py` and explicitly verify `EffectWater` and `ImpactActors` against the pre-conversion baseline; add local overrides when the new effect family drops them.

### D2KRocket contrail visuals also need preserving

The `^D2KRocket` archetype inherits `^Projectile_Missile_Heavy`, which does **not** carry the flak-bullet contrail visual fields (`ContrailZOffset`, `ContrailStartColor`, `ContrailEndColor`, `ContrailStartWidth`, `ContrailEndWidth`) that the old `^Chaingun`/`^FlakWeapon` stack contributed. A weapon that previously resolved with those colours will revert to no contrail visuals unless they are added as local `Projectile` overrides. `review_resolve_diff.py` checks `Proj.CStart`/`CEnd`, so the loss is caught, but `ContrailZOffset`/`StartWidth`/`EndWidth` must be inspected manually.

**Rule:** when collapsing a mixed-stack weapon to `^D2KRocket`, dump the resolved `Projectile` block before and after, and copy any missing visual fields into the local `Projectile` override.

---

## Latest lessons from the July 2026 infantry rebalance pass

### Ledger patching safety

- When patching ledger JSONs from generated markdown balance reports, only overwrite primary damage warheads.
  - Skip `HealthPercentageDamage` warheads entirely.
  - Skip warheads whose tag contains `Friendly` (e.g., `GrenadeFriendlyFire`) to avoid corrupting friendly-fire or self-damage values.
  - Update only `SpreadDamage` / `TargetDamage` primary warheads with the report's damage value (the report table column is `dmg`; it maps to the YAML `Damage` field / ledger warhead `damage`).

### Zero-delta formula-price pipeline

- To keep the formula price delta `Δ` at `0` or `±1`:
  - Round solved `Range` to the nearest **10** (range is ALWAYS a multiple of 10) inside the class band.
  - Solve `Range` with `solve_class_baseline_range` to hit the cost, then clamp to the band. (Uniqueness is a separate concern and is NOT about `FirepowerMultiplier` — see [Uniqueness enforcement](#uniqueness-enforcement).)
  - For auto-cost units, set `Cost` to `round(formula_price)` after the final `Range` is chosen.
  - If the solved `Range` falls outside the band, do NOT just clamp `Range`. Re-balance the unit's stats **together** while preserving its feel; if several actors of the class fall outside, preserve their **relative** range order within the class. Burst count, `BurstDelays`, `ReloadDelay`, `Speed`, and `Range` are the most *memorable* stats (change sparingly); HP and damage-per-shot can be tuned more freely (especially with the fine-grained `FirepowerMultiplier`).

### Multiplier formatting

- All OpenRA `*Multiplier` traits (`FirepowerMultiplier`, `DamageMultiplier`, `RangeMultiplier`, `ReloadDelayMultiplier`, `SpeedMultiplier`, `InaccuracyMultiplier`, etc.) use `Modifier` as an **integer percentage in 1 % steps**.
- `89` means 89 %, `100` means 100 %, `125` means 125 %.
- Decimal `Modifier` values such as `0.89` are wrong and must be converted to `89`.
- `tools/balance/apply_balance.py` and `tools/balance/extract_stats.py` now convert between the ledger fraction (`0.89`) and the YAML integer (`89`) automatically.
- `tools/audit/audit_multiplier_modifiers.py` flags any non-integer `*Multiplier Modifier` value.

### Balance tooling discipline

- **Always syntax-check a script before running it** — `python -m py_compile <script>` catches typos that would otherwise leave the pipeline half-finished.
- Then run Python balance scripts through `tools/balance/run_with_guard.py` (syntax pre-check + 60 s timeout guard) or, when the guard is not yet available, `python -m py_compile` + the script directly.
- `propose_class_rebalance.py` is now the generalized dispatcher for ALL 14 classes (reads `class_anchors.json`, uses the SUM engine `formula.spread_damage_sum`). It only prices units already tagged `design.class_anchor`; membership tagging is still pending, so classify a class's units before trusting its full roster output. The old per-class `*_rebalance_proposal_final.py` one-offs are superseded and slated for archival.
- **After every `apply_balance.py --confirm` run, `extract_stats.py` and `audit_multiplier_modifiers.py` execute automatically**. A full audit (`tools/audit/run_all.py` or `tools/audit/run_all.sh`) is still mandatory before commit.

### Data hygiene

- Ledger `design.tech_tier` and `design.class_anchor` are stale.
  - Derive `TechTier` M from YAML `Buildable.Prerequisites` chains, ignoring production buildings.
  - M = `1.0` for T1/T2, `0.75` for T3 (tech center / lab / facility), `0.5` for T4/T5 (superweapon / epic).
- Ledger weapon `Damage`, `ReloadDelay`, and `Burst` values cannot be trusted for curated classes; verify against YAML and faction intent.

### Stat granularity

- **Speed step depends on the domain:** infantry use **steps of 1**; vehicles, aircraft, AND ships use **steps of 5** (their speed is divided by 5 to derive the turn-rate, so it must be a multiple of 5).
- `Range` is always a **multiple of 10**.
- `FirepowerMultiplier` is the **fine-tuning** lever (1 % integer steps, 5 %–200 %): after coarse-tuning warhead `Damage` on the 2000-step grid, use the FP multiplier to land the exact intended DPS. It is a multiplier and is **meaningless on its own** — it is never a uniqueness key (see [Uniqueness enforcement](#uniqueness-enforcement)).
- Raw `Damage` should be kept in 2000-step increments for the balance pipeline (percentage warheads in 1-steps).

### DPS and formula rules

- Effective DPS = `base_dps * FirepowerMultiplier`, where `base_dps` uses the SUM of all offensive warheads (SUM law).
- `base_dps` must **not** include `FirepowerMultiplier`; compute raw base DPS first, then apply the multiplier once.
- If `solve_class_baseline_range` returns a value outside the class band, re-balance the unit's stats together (preserving feel + relative range) rather than blindly clamping — see [Zero-delta formula-price pipeline](#zero-delta-formula-price-pipeline).

## Class-specific notes

### Scout

- Anchor: `naxis_naxiriflesoldier` — HP 20000, Speed 60, Range 5000, DPS 60, Cost 100.
- Verifier: `forgotten_mutantsoldier` 2×/2× at Cost 250.
- Band: range 4500–5500.

### Closecombat

- Anchor: `td_gdi_shotgunner` — HP 50000, Speed 75, Range 3500, **eff-DPS 250**, Cost 200. Weapon SA 2000 + CG 2000 (WC 0.875), Burst 5, **ReloadDelay 70** → 4000×5/70×0.875 = 250.0 (round, damage on the 2000-grid, no FP multiplier needed).
- Verifier: `asianalliance_fanatic` — HP 100000, Speed 75, Range 3500, **eff-DPS 500**, Cost 500. Same SA 2000 + CG 2000, **Burst 10**, ReloadDelay 70 → 4000×10/70×0.875 = 500.0 (exactly 2×).
- Band: range [2500,4500).

### Special Forces

- Anchor: `japan_imperialscoutsman` — HP 15000, Speed 50, Range 6000, DPS 240, Cost 200.
- Verifier: `schwarzermond_lunarsoldier` 2×/2× at Cost 500.
- `td_nod_lasertrooper` is a T4/0.5× heavy trooper: HP 60000, Speed 50, Cost 750, Range 6000. Weapon = CannonAP + Flak + Laser triad, each warhead **16000** → SUM **48000** @ ReloadDelay 50 → DPS **960** (4× the SF baseline's 240, and 4× HP). Under the SUM law the 48000 is the *sum* of three 16000 warheads, not 48000-per-warhead.
- `cabal_eliminator800` rebalance: Damage 4000, ReloadDelay 5, Burst 1, no gatling, Cost ~1450.
- Band: range 5500–6500.

## Uniqueness enforcement

- **Exactly 5 stats must be unique within a class** — checked against each other; the uniqueness audit must enforce THESE AND ONLY THESE:
  1. `HP`
  2. `Speed`
  3. **uniqueness damage per shot** = Σ(all offensive warhead `Damage`) × `FirepowerMultiplier`
  4. `ReloadDelay` — the RAW value, **NOT** the effective/burst-adjusted reload
  5. `Range`

> ⚠ **Do not confuse #3 with the ledger column `effective_damage`.** They are different
> quantities that were both called "effective damage" until 2026-08-11. #3 is the
> uniqueness stat above (chips EXCLUDED, FirepowerMultiplier APPLIED). The ledger's
> `effective_damage` is the area-integrated metric (chips INCLUDED, FirepowerMultiplier
> NOT applied, weighted by blast footprint and hit reliability) — spec:
> [`docs/design/EFFECTIVE_DAMAGE.md`](design/EFFECTIVE_DAMAGE.md). Never feed one to the
> other's consumer.
- `FirepowerMultiplier` alone — or any single one of these values in isolation — need NOT be unique; on its own it is meaningless. This **supersedes** any earlier "make effective DPS unique via FirepowerMultiplier" rule: DPS is derived, and uniqueness lives on the 5 raw stats above, with #3 (damage×FP) and #4 (raw ReloadDelay) checked **separately** (two units may share one if they differ on the other).
- Break ties by nudging a stat on its own grid: `Speed` steps of **1** (infantry) / **5** (vehicles, aircraft, ships), `Range` steps of **10**, `Damage` steps of **2000** (then FP-multiplier fine-tune), `HP` steps of **1000**.
- **CODE NOTE:** `propose_class_rebalance.resolve_dps_uniqueness` and the uniqueness audit currently key on *effective DPS* — they must be updated to key on the 5 stats above (raw damage×FP and raw ReloadDelay separately).

## Dual-weapon units

- Units with two weapons (e.g. `ra2_soviets_flaktrooper`: short anti-ground + long anti-air) are balanced **independently — as if each weapon were its own actor**: one anti-ground-only actor and one anti-air-only actor, sharing the same `HP` and `Speed` but each with its own `Damage`, `Range`, `ReloadDelay`, and `Burst` fitted to its weapon.
- **Range is relative between the two weapons** (e.g. anti-air range = anti-ground range × 1.5). The RATIO is the rule, so if one weapon's range must change, change **both** to preserve the ratio.
- `FirepowerMultiplier` is **shared** — it scales BOTH weapons at once. So tune each weapon's other stats (`Damage` on the 2000-grid, `ReloadDelay`, `Burst`, `Range`) FIRST, and use the FP multiplier only for final fine-tuning, remembering every FP change hits both weapons together.

## Audit and pipeline findings from 2026-07-22

### Audit report encoding

- `docs/audit/latest/*.md` files can be written in UTF-16 with embedded null bytes.
- Decode them to clean UTF-8 before reading or processing (e.g. `tools/balance/_decode_audit.py` or an equivalent one-shot script).
- Never commit `.safe.md` decoded copies; regenerate them on demand.

### `MinRange` rule and intentional exceptions

- The default rule is `MinRange = round(Range / 5)` rounded to the nearest 5.
- **Never apply blindly.** Keep the following categories as exceptions:
  - Super-weapon / global-spawner weapons: `*Spawner*`, `*SCUD*`, `*TacticalMissile*`, and any weapon with `Range > 100 000`.
  - Linear-pulse projectiles `WaveArtilleryImpact`, `WaveTurretImpact`, `LurkerSpinesImpact`: `MinRange` is **removed entirely** (maintainer 2026-07-22 — they no longer carry any minimum range; do NOT force `MinRange 1`).
  - Meme/intentional numeric pairs: e.g. `RA160mm` family (`Range 11111`, `MinRange 2222`), `YakovlevCannon` (`Range 4444`, `MinRange 888`).
  - Elite weapons should inherit `MinRange` from their base weapon unless a specific exception is documented.
  - `RA2DiskDrain` / `RA2DiskSteal`: `MinRange` is **removed entirely** (maintainer 2026-07-22 — no minimum range; do NOT force 25).

### Weapon uniqueness

- Same-faction duplicate weapons (`W1` in `audit_weapon_uniqueness`) should usually be split so each actor can be rebalanced independently.
- **Keep shared** when the weapon is intentionally identical: `pdlaserbike`, `spore`, `tentacle`, `asianrailtank2` triad, plus all healing/repair beams.
- **Carrier-borrowed weapons (`W3`)** must never be split; the whole point is IFV/Salamander-style weapon borrowing.
- Naming convention for new unique weapons: `<actor>_<base_weapon>` (e.g. `ixian_lightinfantry_light_inf_lmg`).

### `buildable_order` audit

- The audit flags two separate things:
  1. **Prerequisite-token order** inside a single `Prerequisites` list: tech-building tokens should appear before `~..._promotion_unlock...` tokens.
  2. **`BuildPaletteOrder` sort order** per faction and per build queue, ordered by tier then cost.
- The two checks are independent; fixes are applied faction-by-faction, ignoring actors from other factions.

### `stat_formulas` audit decisions ( maintainer-confirmed )

- **F1** `Repairable.HpPerStep` and **F2** `SelfHealing Step` are formula candidates but were not explicitly approved yet.
- **F3** `Repairable` on infantry-slot mechs/vehicles: keep the trait for units that use the infantry body for animation but are mechanically vehicles/mechs.
- **F4** shield `RegenAmount`: the TD Nod cybernetics upgrade intentionally uses a flat shield/armor-plating bonus; do not overwrite it with the generic `2 × SelfHealing Step` rule. Fix outliers such as `ixian_stormlasher` individually.
- **F5/F6** defense `RevealsShroud` and `DetectCloaked`: apply the formula but cap extreme super-weapon ranges (e.g. `steelconsortium_bfg10000`).
- **F7** `Power.Amount`: apply `-Cost/20` except for walls, fences, and bunkers, which never consume power.
- **F8–F10** vehicle and turret `TurnSpeed`: safe to apply.
- **F11** turreted artillery firing-slow pattern: deferred; put on the roadmap for a future audit rework.
- **F15/F16** Light/Heavy Support composition: apply.
- **F17/F18** fighter/bomber `TurnSpeed` and AA-without-air warhead: apply; F18 is a genuine bug find.

### `propose_class_rebalance.py` / `_patch_ledgers_from_reports.py` fixes

- **SUM LAW (maintainer 2026-07-22, supersedes the earlier MAX rule):** effective
  per-shot damage = the **SUM** of every offensive `SpreadDamage` warhead on the
  weapon, **never** the max. A multi-warhead weapon deals the ADDED damage of all
  its warheads to a target; pricing on the max would let a 10-warhead weapon deal
  10× the damage for the price of one. The one canonical reducer is
  `formula.spread_damage_sum()`; `propose_class_rebalance.spread_damages`,
  `fit_class`, and `update_ranges` all call it so MAX can never creep back.
- `spread_damage_sum()` skips `*ExtraDamage` (shield-only chip), `*Percentage`
  (`HealthPercentageDamage`), and `*FriendlyFire` (own-side splash) warheads.
- The ledger stores `firepower_multiplier` as a fraction (e.g. `1.03`); do **not** divide by 100 again inside the proposal script.
- `_patch_ledgers_from_reports.py` must select exactly the same primary armament (`Armament` or `Armament@PRIMARY`) as `propose_class_rebalance.py`.
- Multi-warhead weapons carry each warhead at its OWN intended damage; the weapon's
  effective damage is their sum. (The by-type/by-faction workbooks already model
  this — one sub-row per warhead, `DPS = Σ sub-rows`.) Do NOT set every warhead
  equal to the intended total — that was the MAX-era mistake that left 20
  closecombat/SF units 2–3× hot.
- Include a `dmg_filter` column (`smallarms` / `all`) in the report for scout small-arms-only pricing.

### Script hygiene (pending)

- Multiple `scout_rebalance_*.py`, `closecombat_rebalance_*.py`, and `special_forces_rebalance_*.py` scripts are redundant with the generic `propose_class_rebalance.py`.
- Plan: consolidate the helpers into one `tools/balance/rebalance_classes.py` dispatcher that calls `extract` → `propose` → `patch` → `apply` (dry-run/confirm) → `build_workbook`.
- Do this after the current audit batch is finished and the pipeline is trusted.

## Interactable trait and upgrade actors (2026-07-24)

### The crash

- **Removing the `Interactable` trait from upgrade actors crashes the game.** `Interactable` provides the hit-testing/mouse-interaction bounds that the engine needs for any actor that exists in the game world. Without it, the engine cannot process clicks or selection on the actor and crashes.
- All upgrade actors inherit `Interactable` from `^upgrade.template` (`mods/cameo/rules/defaults.yaml` line 8759). This is the canonical source — do NOT remove it or add `-Interactable:` to upgrade actors.

### The audit lint rule conflict

- `tools/audit/audit_yaml_lint_rules.py` check 4 (`find_interactable_selectable_conflicts`) flags any actor that has BOTH `Interactable` and `Selectable` traits in the same YAML block as a "conflict".
- However, `Interactable` and `Selectable` serve **complementary** purposes in OpenRA:
  - `Interactable` provides the click/hit-test bounds (required for the actor to be interactive at all).
  - `Selectable` provides selection visual feedback (selection box, health bar, decoration bounds) and **depends on** `Interactable` to function.
- `^promotion_upgrade.template` (line 8771) previously inherited `Interactable` from `^upgrade.template` AND added `Selectable` with `DecorationBounds`. This caused duplicate `InteractableInfo` errors in `--check-yaml` for all promotion upgrades across all factions. **Resolved 2026-07-24:** `Selectable` was removed from `^promotion_upgrade.template`, eliminating ~9k errors and ~9k warnings. The remaining `Interactable + Selectable` warnings are only from 6 engine-level bridge actors (`bridge1`–`bridge4`, `sbridge1`, `sbridge2`).
- The audit script only checks literal trait text within the same YAML block, not resolved inheritance. So `^promotion_upgrade.template` is NOT flagged (because `Interactable:` doesn't appear in its own block, only in the parent). But any actor that explicitly writes both traits in the same block would be flagged.

### What needs future research

- **Is the audit lint rule correct?** The rule assumes `Interactable` and `Selectable` are mutually exclusive, but the engine appears to treat them as complementary. Need to verify:
  1. Whether OpenRA engine actually forbids both traits on the same actor (it doesn't seem to — `Selectable` requires `Interactable`).
  2. Whether the rule should be relaxed to only flag cases where both traits are explicitly defined with conflicting `Bounds`/`DecorationBounds` values.
  3. Whether the rule should be removed entirely or changed to a warning instead of a failure.
- **Goal:** Be completely warnings-and-errors free without crashing the game. The current situation is: the audit flags a false-positive conflict, but removing `Interactable` to satisfy the audit crashes the game. The audit rule needs to be fixed, not the actors.

## Git workflow and commit rules (2026-07-24)

### Binding rules from user and co-maintainer Blackrobe

- **Always fetch, pull, and merge before any commit.** The remote may have changes from other developers. If the engine pin (`mod.config` `ENGINE_VERSION`) changed, always run `make all` to fetch and build the new engine before boot-gating. Never skip the boot-gate.
- **Always boot-gate before committing.** Launch the game with `launch-game.cmd`, wait for the main menu (perf.log ends with `MenuPostProcessEffect.PostWorldLoaded`), kill the process, then check for NEW `exception-*.log` files in `%APPDATA%/OpenRA/Logs`. A commit that breaks the boot is not acceptable.
- **`utility.cmd cameo --check-yaml` is a linting/YAML validation tool, NOT a boot-gate substitute.** Use it for: verifying cosmetic refactors (actor/template renames), checking broken prerequisites, and detecting gameplay-relevant YAML issues. **Goal: 0 errors AND 0 warnings.** The utility takes a VERY LONG TIME (10+ minutes) — only run it when you have completed ALL connected tasks from the last report and expect 0 errors/warnings to confirm. Do NOT run it repeatedly. Keep findings from the last report in ROADMAP and docs so they can be fixed without re-running. It is ABSOLUTELY NECESSARY — just choose wisely WHEN to run it.
- **Always update ALL relevant documentation files BEFORE committing.** This includes `docs/design/ROADMAP.md`, `docs/DESIGN.md`, `docs/audit/SUMMARY.md`, `docs/LESSONS_LEARNED.md`, and any other docs affected by the change. Check old docs for outdated information, inconsistencies, and contradictions — fix them. A commit without updated docs is an incomplete commit.
- **Do not spam commits on upstream master.** Use a pull request (PR) for cleaner commit history. Create a feature branch, push it, open a PR, and merge only after verification.
- **Only merge a PR if either:** (a) you no longer detect regression caused by the changes, or (b) launching the game no longer results in a crash. Commits that do not break the master branch are a naturally acceptable outcome.
- **Commit titles must be self-explanatory to all developers.** Terms like "Phase 5", "A2 audit", "Fix B5", or "X/Y law" are only understood internally by Aedis and their agent. If such internal pointers are necessary, elaborate where to find the definition (e.g. "see docs/audit/SUMMARY.md bug class B5") and what kind of project it links to.
- **When a task is completely done, merge the feature branch to master.** Do not leave completed work stranded on a feature branch. Ensure boot-gate passes and docs are updated before merging.
- See also: `docs/AGENT_WORKSPACE.md` § Git workflow and commit rules.

## YAML lint rules learned (2026-07-24)

### ProductionCostMultiplier / ProductionTimeMultiplier use Prerequisites, not RequiresCondition

These two traits do NOT support `RequiresCondition`. They use `Prerequisites:` instead. The pattern is:
- `GrantConditionOnPrerequisite` grants a condition when a prerequisite is met
- Other multipliers (SpeedMultiplier, DamageMultiplier, etc.) use `RequiresCondition:` with the granted condition
- `ProductionCostMultiplier` and `ProductionTimeMultiplier` use `Prerequisites:` directly with the prerequisite name

Example (correct):
```yaml
GrantConditionOnPrerequisite@myupgrade:
    Condition: myupgrade
    Prerequisites: myupgrade
ProductionCostMultiplier@myupgrade:
    Multiplier: 90
    Prerequisites: myupgrade          # NOT RequiresCondition
SpeedMultiplier@myupgrade:
    Modifier: 110
    RequiresCondition: myupgrade      # This is correct for SpeedMultiplier
```

### Other YAML lint fixes applied
- **WeaponClass**: Deprecated/removed weapon field. Remove all `WeaponClass:` lines from weapon definitions.
- **Burstdelays**: Case typo — should be `BurstDelays` (capital B, capital D).
- **BurstDelay**: Singular form invalid — should be `BurstDelays` (plural).
- **Angle on Bullet**: Use `LaunchAngle` instead of `Angle` on Bullet projectiles.
- **ValidStances on weapons**: Not a valid weapon-level field. Remove it; use `ValidRelationships` on warheads instead.
- **ChangeOwnerValidStances**: Not a valid field on ChangeOwner warhead. Use `ValidStances` instead.
- **ValidStances on AutoTargetPriority**: Not a valid field. Remove it; `ValidStances` belongs on `AutoTarget` trait.
- **OverrideActor on Tooltip**: Not a valid field. Remove it.
- **NegativeRemoval**: `-Trait: value` is invalid — removals must be empty: `-Trait:` (no value).
- **DuplicateInteractable on bridges**: `Selectable` inherits from `Interactable` in the engine. Having both `Selectable:` (inherited from `^1x1Shape`) and `Interactable:` on the same actor creates duplicate `InteractableInfo`. Fix: add `-Selectable:` to remove the inherited one, keeping only the explicit `Interactable:` with custom Bounds.
- **UndefinedCursor chrono-target**: Cursor sequences use underscores in definition (`chrono_target`) but traits reference hyphens (`chrono-target`). Add a hyphen-variant sequence alias in cursors.yaml.

### YAML lint cleanup header-removal bug (2026-07-24)

- **The NegativeRemoval lint fix (commit d42ad53a1) accidentally removed weapon/warhead HEADERS, not just values.** When stripping values from `-Trait: value` lines, the lint script also deleted adjacent header lines (e.g., `RA2DiskSteal:`, `Warhead@Cloud: SpawnSmokeParticle`, `Warhead@LaserWeapon: SpreadDamage`). The bodies remained as orphaned child nodes, causing YAML parse errors and `MissingFieldsException` crashes.
- **Always verify after lint cleanup**: After any bulk NegativeRemoval fix, run `utility.cmd cameo --check-yaml` and boot-gate test. The lint tool catches field errors but the game boot catches orphaned nodes.
- **ContentPack migration must be complete**: When migrating weapons from `mods/cameo/weapons/*.yaml` to ContentPacks, ALL weapon definitions must be copied, not just templates. The RA2 ContentPack only had `^RA2*` templates but was missing 134 concrete weapon definitions, causing `Parent type not found` errors for weapons like `RA2CarrierTarget` that other weapons inherit from.
- **UTF-8 encoding in YAML weapon names**: Weapon names with non-ASCII characters (e.g., `ü` in `Kübelwagen`) can become double-encoded (mojibake `Ã¼`) during file operations. Always verify encoding when files contain non-ASCII characters. The engine's YAML parser uses the file's byte-level encoding, so `NaxiWW2KÃ¼belwagenMachinegun` does not match `NaxiWW2KübelwagenMachinegun`.
- **Engine shader files not tracked by mod git**: Custom shader files in `engine/glsl/` (e.g., `postprocess_nuclearflash.frag`) are inside the .gitignored engine directory. They must be recreated after `make all` fetches the engine. Document any custom shader requirements in the mod repo for post-fetch setup.

### Superweapon documentation audit (2026-07-25)

- **FACTIONS.md can be stale — YAML is ground truth**: A full cross-reference of all superweapon and support power YAML traits against `FACTIONS.md` found 14 discrepancies. The docs had incorrect names (e.g., "Tiberian Wildlife Rampage" for Forgotten's actual nuclear missile, "Satellite Hack" for CABAL which was unimplemented), missing support powers (Force Shield, Chrono Reinforcements, EMP Disable, Traitors, Slow, Invisibility, Bloodlust, Haste), and missing reference table entries (Drop Pods, Federation Support Teleport). Always verify against YAML before trusting documentation.
- **Harkonnen Palace has `^PrimarySuperweapon` but NO power trait**: The building inherits the superweapon template and has `SupportPowerChargeBar` but no actual `NukePower`/`DetonateWeaponPower`/etc. The Death Hand Missile described in faction YAML is unimplemented. This is a parked faction, not a regression.
- **WIP faction superweapons exist in `rules/` YAML**: Warzone 2100, Worms, Win98, Warcraft 1, and WH40K all have superweapon traits in `rules/*.yaml` (not yet migrated to ContentPacks). These should be documented in FACTIONS.md only when the factions become active.
- **Outpost 2 superweapon is in `rules/outpost2.yaml`, not ContentPacks**: The Supernova Missile uses `NukePower` with `supernova_missile_super` weapon, charge 9000, on `EDEN_OBSERVATORY` and `PLYMOUTH_OBSERVATORY`. FACTIONS.md was already correct for this.
- **Audit raw data location**: `docs/audit/latest/superweapon_audit.yaml` contains the full cross-reference with all primary/secondary superweapons, support powers, critical findings, and WIP faction discoveries.

### Engine update pipeline and Smart App Control findings (2026-07-30, updated with deep research)

#### The canonical engine update pipeline (binding, uniform process)

The engine lives in TWO places that must stay in sync. Follow these steps IN ORDER for every engine change:

1. **Edit** engine C# source only in the local dev clone of the engine repository (the `cameo-engine` clone of `https://github.com/cameo-mod/OpenRA`, branch `cameo-engine`).
2. **Commit and push** to `origin/cameo-engine`. Check `git status` for stray entries before committing (see the nested-clone pitfall below).
3. **Get the full commit hash** with `git rev-parse cameo-engine` — never hand-type or truncate/pad a hash.
4. **Update `mod.config`** in the mod repository: set `ENGINE_VERSION="<full-40-char-hash>"`. The engine pin lives in `mod.config`, NOT `mod.yaml`.
5. **Run `make all`** (Windows: `make.cmd all`). Because `engine/VERSION` no longer matches, the SDK deletes `engine/`, downloads the source zip for the pinned commit from GitHub, and rebuilds everything.
6. **Verify**: `engine/VERSION` must contain the new hash; the build must have 0 errors.
7. **Boot-gate with `launch-game.cmd`** before committing the `mod.config` change (see AGENT_WORKSPACE.md git rules).
   ⚠ **The old "recreate any custom `engine/glsl/` shaders, they are wiped" step is STALE — verified 2026-08-22.**
   All 16 shaders (including `postprocess_nuclearflash.frag`) are now TRACKED in the engine repo, so the source
   zipball carries them and the fetch restores them untouched. Measured by md5-summing `engine/glsl/*` before and
   after a full `make.cmd all` on pin `462fc1fc4b`: identical, all 16. Still worth a `md5sum` before/after rather
   than trusting either version of this line — if a shader is ever added WITHOUT committing it to the engine repo,
   the wipe becomes real again.
8. **Commit `mod.config`** together with the change's docs updates.

Key facts verified 2026-07-30:

- `fetch-engine.sh` downloads a GitHub **source** zipball (never pre-built binaries) and stamps `engine/VERSION`. All `engine/bin/*.dll` files are always locally compiled and unsigned.
- Building ONLY `OpenRA.Mods.CA.csproj` still touches `engine/bin/OpenRA.dll` (project references + shared output dir). There is no build scoping that avoids rewriting engine binaries.
- GitHub zipballs do NOT include submodule/gitlink content — a gitlink in the engine repo appears as an empty folder in the fetched `engine/` copy.

- SAC's WDAC policy ID is `{0283ac0f-fff1-49ae-ada1-8a933130cad6}` (`VerifiedAndReputableDesktop`).
- Block events: `Microsoft-Windows-CodeIntegrity/Operational` Event ID 3033 (audit) + 3077 (enforcement block), reason "did not meet the Enterprise signing level requirements".
- The ISG cloud verdict is **asynchronous**: the first launch of a fresh build may succeed because the verdict hasn't arrived yet. Subsequent launches are blocked after the ISG returns "unknown" for the new hash.
- There is NO per-app exception, registry allowlist, or `Unblock-File` workaround. MOTW removal does not help — SAC is reputation-based, not MOTW-based.

**The EA (Extended Attribute) cache mechanism (key discovery 2026-07-30)**:
- WDAC uses NTFS Extended Attributes (EAs) to cache trust decisions on binaries. When a binary passes WDAC evaluation, an EA (120 bytes) is written to the file. On subsequent launches, WDAC checks the EA and reuses the cached result — **no cloud query, no Code Integrity event, no block**.
- The ISG (part of Microsoft Defender) runs **independently of SAC's WDAC policy**. When SAC is off, Defender's ISG can still evaluate binaries and write trust EAs. When SAC is re-enabled, WDAC finds the cached EAs and allows the binary without re-evaluating.
- **Verified on this machine**: SAC was briefly turned off → game launched once → ISG wrote EAs to all loaded DLLs → SAC re-enabled → game launches successfully with ZERO Code Integrity events (cache hits are not logged). DLLs not loaded during gameplay (`OpenRA.Server.dll`, `OpenRA.Utility.dll`) have 0 bytes EAs and would still be blocked if loaded.
- **EA persistence**: EAs can be invalidated by (1) reboot if the SAC policy has `Enabled:Invalidate EAs on Reboot`, (2) ISG periodic re-query returning "unknown", or (3) recompilation (new MVID = new hash = no cached EA).

**SAC registry values** (kernel-protected, cannot be edited while Windows is running):
- `HKLM\SYSTEM\CurrentControlSet\Control\CI\Policy\VerifiedAndReputablePolicyState`: 0 = Off, 1 = Enforcement, 2 = Evaluation.
- `HKLM\SYSTEM\CurrentControlSet\Control\CI\Protected\VerifiedAndReputablePolicyStateMinValueSeen`: tracks the minimum value ever set (prevents downgrade attacks). Must also be set when changing modes via WinRE.
- The `CI\Policy` key is kernel-protected — even Administrator cannot modify it while Windows is running. Use WinRE (see below) or Windows Settings.

**Four options for developers (corrected from earlier "only three")**:

1. **EA cache workaround** (current, accidental): Turn SAC off → launch game once (ISG writes EAs) → re-enable SAC. EAs persist until invalidated. **Not reliable** — breaks on recompilation and possibly on reboot. Use only as a short-term stopgap.

2. **SAC Evaluation mode** (Microsoft-documented testing mode): SAC stays active, evaluates all binaries, logs audit events to Event Viewer, but **does not block**. This is NOT "turning off SAC" — the evaluation engine still runs. Set via WinRE (see below). Can switch back to Enforcement via Windows Settings. **Recommended for development.**

3. **VM / SAC-free machine**: Develop and boot-gate on a machine where SAC is not enforcing. SAC is off by default in Windows Sandbox and fresh VMs.

4. **Code signing**: Sign builds with a certificate from a CA in Microsoft's Trusted Root Program (e.g., Azure Trusted Signing, ~$9.99/month). Signed binaries pass SAC even in Enforcement mode, permanently. This is the only permanent solution for Enforcement mode.

**How to set SAC to Evaluation mode via WinRE** (the `CI\Policy` key is kernel-protected, so WinRE is required):
1. Settings > System > Recovery > "Restart now" (Advanced startup).
2. Troubleshoot > Advanced options > Command Prompt.
3. Run `regedit`, click HKEY_LOCAL_MACHINE, then File > Load Hive.
4. Browse to `C:\Windows\System32\config\SYSTEM`, name it `OFFLINE`.
5. Set `OFFLINE\ControlSet001\Control\CI\Policy\VerifiedAndReputablePolicyState` to `2`.
6. Set `OFFLINE\ControlSet001\Control\CI\Protected\VerifiedAndReputablePolicyStateMinValueSeen` to `2`.
7. Select `OFFLINE` node, File > Unload Hive (critical — do not skip).
8. Close regedit, type `exit`, reboot.
9. Verify: `Get-ItemProperty "HKLM:\SYSTEM\CurrentControlSet\Control\CI\Policy" -Name VerifiedAndReputablePolicyState` should show `2`.
10. To return to Enforcement: Windows Settings > Privacy & security > Windows Security > App & browser control > Smart App Control settings > On.

**Boot-gate implication**: With the EA cache workaround or Evaluation mode, local boot-gating IS possible. If SAC is in Enforcement mode AND the EAs have been invalidated (e.g., after a rebuild), the boot-gate will fail. In that case, record the SAC state explicitly in the commit/PR description, use one of the four options above to enable testing, and do NOT silently skip or claim the boot-gate passed.

## Bulk YAML rename scripts: safety lessons (2026-07-31)

Applies to any script that renames a weapon/actor/condition identifier across the whole mod tree (see `tools/rename_aa_weapons.py`, `tools/rename_emp_weapons.py`).

- **Never do a blind file-wide word-boundary substitution of a bare identifier.** An early draft renamed `Dragon` → `Dragon_AA` via `re.sub(r'\bDragon\b', ...)` across every YAML file. This also mangled unrelated `Tooltip: Name: Way of the Dragon`, a Warcraft2 `Dragon Roost` building name, and a commented-out `# Image: DRAGON` sprite reference — none of which are weapon references. The same bug hit `Spore` (a Zerg building's `RequiresCondition`/`Armament Name:` field coincidentally shares the literal string with the weapon name). **Root cause of the corruption class**: identifiers in this codebase are reused across completely different namespaces (weapon names, condition names, armament trait `Name:` identifiers, tooltip display text, sprite/image names), so any substring or bare-identifier match is unsafe. Always match on the **exact YAML field** (`Weapon:`, `Weapons:`, `Inherits:`, the top-level definition key) with an **exact full-token value comparison**, never a regex substring/word-boundary match against arbitrary line content.
- **The same literal name can be a weapon, an actor, AND a sequence.** E.g. `sow_mech_avenger` is simultaneously an actor id (`rules/sow.yaml`), a weapon (`weapons/sow.yaml`), and a sequence (`sequences/sow.yaml`); `d2k_aircraft_eater` is both a weapon and a (commented-out) actor + sequence. Renaming the top-level definition key, or an `Inherits:` value, requires first classifying **which specific block** the identifier belongs to (`is_weapon_definition_body`-style marker-key heuristics) — do not rename just because the name string matches; verify the containing block is actually a weapon.
- **Comments use `#` BEFORE the indentation tabs in this codebase** (e.g. `# \t\tWeapon: Foo`), not after. A regex anchored `^\t+#` will silently skip every commented-out field, which then goes stale (references the old, now-nonexistent name) if the comment is ever restored. Match `^(#\s*)?\t+` (or the reverse order) to catch both stylings. Per explicit user instruction: commented-out weapon/actor definitions and their internal `Weapon:`/`Inherits:` references SHOULD be kept in sync with a rename (so re-enabling old commented-out content doesn't silently reference a stale name) — but a comment that merely *mentions* a name in prose or an unrelated field (`# Image: DRAGON`, `# Class: d2k_aircraft_eater`) must NOT be touched.
- **`ValidTargets` is frequently declared only on a `^Template` ancestor**, not on the concrete weapon (e.g. `TSMechRailgun: Inherits: ^RailgunWeapon` with no direct `ValidTargets:` line). Any audit/rename logic that reasons about a weapon's targets must resolve `ValidTargets` through the full `Inherits:` chain, not just read the weapon's own body. When even the chain resolves to nothing (some helper/sub-weapons truly never declare it), treat it as **unknown**, not as a default — guessing "ground" or "air" for unresolved cases risks false positives; a missed rename (false negative) is the safe failure direction.
- **Duplicate weapon definitions with the same name exist across legacy and migrated files** (e.g. `MammothTusk` differs between `weapons/missiles.yaml` and `ContentPacks/RedAlert/Shared/yaml/weapons.yaml`). A `name -> data` dict keyed purely by weapon name is not reliable when multiple non-identical bodies share a name; last-write-wins depends on filesystem walk order. This didn't corrupt the AA-suffix task specifically (both duplicate bodies happened to be dual-purpose and excluded either way), but it's a latent correctness risk for any future name-keyed weapon analysis. Flagged as legacy-file cleanup debt, not fixed in this pass.
- **A naming-convention exclusion keyword list must not include a substring of the very marker it's trying to detect.** `AA_LEGACY_KEYWORDS` originally included the bare string `"aa"` to avoid re-flagging compliant names — but that silently excluded every weapon that already contained "AA" without the required underscore (`SWAWingGunAA`, `RA2HoverMissileAA_elite`), which is exactly the case the rule needs to catch and fix. Use precise legacy keywords (`flak`, `sam`, `interceptor`, `patriot`, ...) instead of a substring that overlaps the target pattern.
- **The actual `_AA` suffix rule is about paired weapons on one actor, not a weapon's own `ValidTargets`.** Corrected DESIGN.md §1: `_AA` marks the air-only sibling of a **dual-weapon actor/template** — one `Armament` trait equips a ground-capable weapon, another equips an air-only weapon (typically `Inherits:` from the ground one), e.g. an Anti-Air Tank. A standalone AA-only weapon on a single-weapon actor (a SAM Site, a dedicated AA turret) does **not** get `_AA` — there's nothing to disambiguate it from. A single weapon whose own `ValidTargets` already spans both `Ground` and `Air` (one combined weapon, not two) also doesn't get `_AA`. Verify by finding actors/templates with ≥2 `Armament` traits where at least one referenced weapon is air-only and at least one other is ground-capable — only the air-only one(s) qualify. This is the same "dual-weapon unit" pattern already documented in [Dual-weapon units](#dual-weapon-units) for balance purposes, applied here to naming.
- **After any bulk structural rename, verify with the existing audits, not just eyeballing a diff sample**: `tools/audit/audit_orphans.py` (dangling weapon refs must stay 0), `tools/audit/audit_inherits.py` (dangling inherit targets must stay 0), and re-running the rename script itself should report nothing left to do (idempotency check). A clean `git diff --stat` with exactly N insertions / N deletions (1:1 line replacement, no stray additions) is also a fast sanity signal that the script only ever replaced tokens in place.

## Loose-extracted .oramap maps must always be repacked before finishing a task (2026-07-31)

`.oramap` files are zip archives; editing a map means extracting it to a loose folder, editing `map.yaml`/`rules.yaml`/`*.lua`/etc., then **repacking it back into the same `.oramap`**. Found `mods/cameo/maps/survival_extracted/` sitting untracked in the tree with real, dated design edits in `script.lua` (2026-07-29: `RandomEventUnitScale` halving chaos/random-event spawn counts, simplified `SpawnAIBase` to MCV-only) that were **never repacked** — `survival.oramap` in the tree was a stale pre-2026-07-29 build the whole time, meaning the actual shipped map silently lacked the intended difficulty tuning.

- **Always repack and delete the extraction folder in the same session as the edit.** Never leave a loose `*_extracted/` (or similarly named) folder next to its `.oramap` — OpenRA does not merge them; whichever one the engine picks up (the `.oramap`, per the packaging docs in `Cameo_Knowledge_Base_Manual.md` §"Package the map as an `.oramap`") is the only one that's actually live in-game, silently shadowing any edits left in the loose folder.
- **Use `tools/repack-oramap.ps1 -dir <extracted_dir> -oramap <target.oramap>`, then always validate with `./utility.cmd cameo --check-yaml <absolute path to .oramap>`** before trusting the repack. Compare the error/warning counts against a `check-yaml` run on the untouched original — identical counts confirm no regression; a new `"Not a valid map"` / `InvalidDataException` means the repack corrupted the zip structure.
- **Bug fixed in `tools/repack-oramap.ps1`**: it computed each zip entry's relative path as `$f.FullName.Substring($dir.Length + 1)`, but `Get-ChildItem`'s `.FullName` is always an absolute path while `$dir` was whatever string the caller passed in. Calling the script with a **relative** `-dir` (e.g. `mods/cameo/maps/survival_extracted` instead of the full `C:\...\survival_extracted`) silently produced zip entries with a garbage prefix baked in (e.g. `/Cameo-mod/mods/cameo/maps/survival_extracted/script.lua` instead of `script.lua`), which OpenRA's `Map` loader rejects outright as `"Not a valid map"` with no indication of why. Fixed by resolving both `-dir` and `-oramap` to absolute paths via `Resolve-Path` before computing the substring. **Always pass either path style now — the script normalizes internally — but still validate with `check-yaml` after every repack**, since a silent zip-entry corruption has no compile-time signal.

## OpenRA Lua `Map` API: there is no `Map.Contains` (2026-07-31)

The `Map` global exposed to map Lua does **not** define a `Contains` method. Calling `Map.Contains(pos)` raises `Fatal Lua Error: Table 'Map' does not define a property 'Contains'`. To validate whether a `CPos` is inside the map, check against `Map.TopLeft`/`Map.BottomRight` world positions, or simply wrap `Actor.Create` in `pcall()` and let a position outside the visible map fail safely. In `mods/cameo/maps/survival_work/script.lua`, `SpawnBuildingForPlayer` now relies on `pcall(Actor.Create, ...)` to skip off-map cells instead of a non-existent `Map.Contains` guard.
- **A second, unrelated loose/packaged duplicate was found and left for maintainer review**: `mods/cameo/maps/hegemony-or-survival/` (a tracked loose folder, committed in `4877a61b7`) sits alongside `mods/cameo/maps/hegemony-or-survival.oramap` with the same `Title:` and identical `map.bin`, differing only in `MapFormat` (11 packaged vs. 12 loose) and a regenerated `map.png` thumbnail — consistent with an incidental map-editor re-save rather than deliberate content edits. Unlike the `survival` case there was no design-intent comment or dated diff to justify carrying the edit forward, so this was **not** unilaterally resolved; flagged for the maintainer to decide which copy is canonical and delete the other (or confirm both are intentionally tracked, e.g. as an editable source + shippable package pair).

## ClassicProductionQueueProperties crash on actors with no queue (2026-07-31)

`ClassicProductionQueueProperties.GlobalProductionHandler` (engine `ProductionProperties.cs:226`) called `.First()` on `BuildableInfo.Queue`, crashing with `System.InvalidOperationException: Sequence contains no elements` when an actor with no production queue assigned was produced (e.g. via Lua `Actor.Create` on survival maps like "Crazy Survival Alpha"). The same bug existed in `Build()` (line 246) and `IsProducing()` (line 293).

- **Fix**: replaced all three `.First()` calls with `.FirstOrDefault()` + null guard. Engine commit `1f71ccde90` on `cameo-engine` branch. `mod.config` updated to `1f71ccde90c1194fe908702f2e915807b2f0f3fd`.
- **Root cause**: the `GlobalProductionHandler` fires for ALL actors produced by any player (it's hooked into `OnOtherProducedInternal`), not just actors explicitly built via production queues. Any actor spawned without a `BuildableInfo.Queue` entry (common in Lua scripts that use `Actor.Create` directly) would trigger the crash.
- **Lesson**: engine code that handles production events must be defensive against actors that aren't part of the classic production system, since map scripts can create arbitrary actors outside the production queue framework.

## Weapon template retrofit — Phase A lessons (2026-08-02)

The 3-way weapon-template split requires retrofitting weapons from the old full-stack templates (`^SmallArms`, `^Chaingun`) to the new 3-layer system (`^Bullet_Light`/`^ProjectileBullet_Light`/`^EffectBullet_Light`, `^Bullet_Medium`/`^ProjectileBullet_Medium`/`^EffectBullet_Medium`). Script: `tools/archive/retrofit_v3.py`.

- **Missing `Report` field causes `-Report:` lint errors.** Old templates (`^SmallArms`, `^Chaingun`) carried `Report: gun8.aud`; the new warhead-only templates (`^Bullet_Light`, `^Bullet_Medium`) did not. When a child weapon has `-Report:` (removal node) but the parent template lacks the field, `check-yaml` flags it. Fix: add `Report: gun8.aud` to the new templates to match the old defaults. Always check for fields that child weapons attempt to remove (`-FieldName:`) when creating replacement templates — the new template must carry any inherited field that children override or remove.
- **Warhead key renaming must happen in the same pass as inherit repointing.** The first script version (`retrofit_v2.py`) classified weapons for warhead key renaming BEFORE repointing inherits, then repointed in a separate step. After repointing, the classification no longer held (the weapon no longer inherited from `^SmallArms`), causing missed warhead key renames. Fix (`retrofit_v3.py`): rename warhead keys and repoint inherits in a single pass per weapon.
- **Dual-inherit weapons must be skipped in Phase A.** Weapons inheriting from BOTH `^SmallArms` and `^Chaingun` (e.g. `HMG_turret`, `TSTurretLaserFire`) have ambiguous warhead key mappings and require special handling in Phase B. The script correctly skips them.
- **Intermediate templates are repointed, not their children.** Templates like `^RA2SmallArms`, `^RA2Chaingun`, `^RA2MG`, `^TSMG`, `^SteelChaingun` inherit from `^SmallArms`/`^Chaingun` and were repointed directly. Their concrete weapon children (e.g. `ra2_soviets_conscript_carbine`) inherit from the intermediate template and were NOT directly modified — correct behavior.
- **Warhead key renaming is selective.** The script only renames `Warhead@SmallArms:` and `Warhead@Chaingun:` (and their `Percentage` variants), NOT custom warhead keys like `Warhead@TSMG:`. This is correct — custom keys are weapon-specific and don't follow the template name pattern.

## Weapon 3-way split — effect/projectile pitfalls found during the effects-table pass (2026-08-05)

Session doing the `^Effect_*`/`^Projectile_*` library rebuild + CABAL missile pilot surfaced several repeatable mistakes — read this before touching any more weapon templates.

- **"Share the same effect/sound" is NOT "point both families at one template."** The maintainer's instruction "MissileAP should share the same effects and sounds as CannonAP" meant *duplicate the same visual/sound values* into two templates, because the families still diverge on water behavior (cannon shells splash via a dedicated `Warhead@EffectWater`; missiles just explode over water the same as over ground, folded into the ground `Warhead@Effect`'s `ValidTargets`). Collapsing two families onto one shared template because their *values* match is wrong whenever *any* other field (water behavior, air behavior, tier granularity) can differ. When in doubt, build two templates with identical bodies rather than one shared inherit — cheap now, avoids an incorrect merge later.
- **Never describe a "before" state from your own recent edit history — verify it against the actual resolved output (or git history) first.** Twice in one session an incorrect "before" value was stated (once assuming a just-changed intermediate state was the original, once assuming the wrong template tier) because the check was "what did I just have it set to" instead of "what does `resolve_weapon()` (or `git log -p`/`git show <commit>^:<path>`) actually say." Always resolve or diff against the real historical state, not memory.
- **A field that "matches the world you want" isn't safe until you check for a silent zeroing field nearby.** `^Projectile_Missile_Heavy` had `ContrailLength: 0`, which silently disabled a weapon's own inline `ContrailStartColor`/`ContrailEndColor` override — the colors were being set but never rendered. Don't just check that the fields you're setting exist on the target template; check for a sibling field that gates whether they do anything.
- **Every weapon needs its OWN explicit `Report:` — checked back to the actor's very first commit, `RA2PatriotThunderboltMissile` never had one and silently inherited a classic-CnC fallback for its entire existence** (a sibling weapon on the same launcher, `RA2Patriot`, had the correct RA2-styled `vifvatta.wav` the whole time). This class of bug (silently-inherited default sound/effect, DESIGN.md §8's "never fall back to the class template's default" rule) is very likely present on other weapons that have gone through multiple template-repoint passes — a dedicated Report resolve-and-strip audit (every weapon gets an explicit `Report:`, then strip `Report:` from `^Projectile_*` templates so nothing can fall back again) is still pending, see ROADMAP.
- **The `illegal_mix`-style "no more than 2 warheads" audits need an exception allow-list before they're trustworthy.** The maintainer's rule (confirmed 2026-08-05) is up to **4** warhead inherits for a deliberate two-theme × two-tier combo (e.g. CABAL missiles combining Missile Light+Medium with Demolition/Concussion). Converting those combos to explicit `Inherits@wh/@wh2/@wh3/@wh4` made the narrow 2-cap audit's count go *up*, not down — that's the audit being stale, not new damage. Fix the audit's allow-list before trusting its number as a progress metric.
- **Tooling win worth repeating: `tools/audit/miniyaml.py`'s `Ruleset.resolve_weapon(name)` faithfully replicates the engine's actual inheritance/merge (including OpenRA's quirk where two inherited `Projectile:` nodes of *different* concrete types (`Bullet` vs `Missile`) still merge their child fields, with only the final node's *value* determining the resolved class).** Use it to compute the ground-truth resolved state before AND after any multi-inherit weapon conversion — do not hand-simulate the merge order, and do not guess a diff against a template without resolving first.

## Empty warhead type = boot NRE; check-yaml does not catch it (2026-08-04)

A `Warhead@X:` line with **no value** is a boot crash, not a lint warning. `WeaponInfo.LoadWarheads` runs for **every** top-level weapon node in the resolved ruleset — including unused `^templates` — and calls `Game.CreateObject<IWarhead>(node.Value.Value + "Warhead")`. An empty value parses to `null`, so the lookup resolves to the abstract `Warhead` base class and `ObjectCreator.CreateBasic` throws `NullReferenceException` during `Ruleset.LoadDefaults`; the game never reaches the main menu.

- **Why inheritance doesn't save you**: `MiniYaml.MergePartial` falls back to the parent value only when a **same-key** ancestor carries one (`overrideNodes.Value ?? existingNodes.Value`). Both crash sites (`RA2MirageGun` `Warhead@Effect:` in `mods/cameo/weapons/redalert2.yaml`, `TSSAPCMissiles` `Warhead@GrenadeFriendlyFire:` in `mods/cameo/weapons/tiberiansun.yaml`) had no same-key ancestor, so nothing rescued the null. Fix = give the node its concrete type (`CreateEffect` / `SpreadDamage`), don't leave the line dangling "to be filled in".
- **`utility --check-yaml` does NOT catch this class** — typeless warhead nodes lint clean. The permanent guard is `python tools/balance/run_with_guard.py tools/audit/audit_empty_warheads.py`, which resolves the full manifest weapon set via `miniyaml.Ruleset` and flags any resolved node whose key starts with `Warhead` but has no type (plus empty `Projectile:` as a suspect). **Run it after any bulk warhead/weapon edit** (retrofits, key renames, template repointing). Post-fix sweep: 4,202 weapons, 0 findings; boot-gate passed.
- **Same crash class, other keys**: any engine-loaded node keyed by class name behaves this way. `Projectile:` with no value is the adjacent suspect (flagged by the same audit); trait nodes are safe because they carry their type in the key name itself.
- **A bare `Warhead@X:` (no type) is only safe when a same-key ancestor in the resolved chain already provides the type.** During the 3-way split we stripped `SpreadDamage` from `Warhead@Bullet_Light:` / `Warhead@Bullet_Medium:` nodes because the new `^Warhead_Bullet_*` templates carry those same keys with `AreaDamage`; that works. But the same strip applied to weapons that do **not** inherit `^Warhead_Bullet_*` (e.g. an old `d2k_air_drone_guns` child that gets its warhead shape from a non-Bullet ancestor) left 52 typeless nodes that `audit_empty_warheads.py` flagged as NRE risks. Fix: restore `SpreadDamage` for nodes whose parent does **not** provide the same key. Rule of thumb: strip the restated type only if `Inherits@wh*:` covers that exact `^Warhead_<key>`; otherwise keep the explicit concrete type.

## Effect-warhead merge safety during 3-way split (2026-08-07)

- **Do not bulk-insert required fields into `ApplyPhysicalState` / `CreateEffect` / `SpawnActor` nodes that a `^Effect_*` template already provides.** Adding `PhysicalStateName` to every `PhysicalState*FlameWeapon` node without checking whether the field already exists locally or will be inherited from `^Effect_Flame_*` produces `MiniYaml.Merge` "duplicate value for key: PhysicalStateName" boot crashes. This happened on the `HeavyFlame + MediumFlame` retrofit and forced a full revert.
- **A local `PhysicalState...` or `GroundFire` override must only carry fields that actually differ from the inherited `^Effect_*` template.** If `Inherits@fx: ^Effect_Flame_*` is present, the local `Warhead@PhysicalStateXFlameWeapon:` should keep only `Amount` (and maybe `Range` if different). `PhysicalStateName`, `ValidRelationships`, and the default `Range` must come from the template. For a weapon that has two different flame tiers, the effect template only supplies the matching tier's `PhysicalState...` key; the other tier's `PhysicalState...` key must either be dropped entirely (if the effect template's range/amount are acceptable) or be fully self-contained, because it no longer has a same-key ancestor.
- **Effect-free clusters are the safest next conversion targets.** `ShrapnelWeapon + HeavyCannon` → `Concussion_Medium + CannonHE_Heavy` (3 weapons) converted cleanly because neither warhead drags in `PhysicalState`/`GroundFire`/`SpawnActor` effects. This makes the bare `Inherits@wh/@wh2/@proj/@fx` pattern safe.
- **Removal markers (`-Key:` or `-Sub/Key:`) crash if the removed key no longer exists in the resolved chain.** `8Inch` had `-Warhead@Effect2:` inherited from the old `^Grenade`/`^HeavyBomb` stack. After repointing to `^Effect_Demolition_Light`, `Effect2` was gone and the game threw "There are no elements with key `Warhead@Effect2` to remove". `JHindChainGun` had `-		-LaunchAngle:` nested under `Projectile: Bullet` to remove `LaunchAngle` from the old `^Chaingun`/`^Grenade` `Bullet` projectile; the new `^Projectile_Bullet_Medium` does not contain `LaunchAngle`, so the same crash occurred. Any conversion must strip **all** stale removal markers — top-level and nested, not just `-Warhead@*` — before boot-gating.
- **Single-inherit repoint is only safe when the weapon has exactly one `Inherits` tag and no other addon inherits.** A mechanical sweep that included multi-addon `Steel`/`RA2` weapons produced 46 empty-type warheads because `^SteelLightMissile`, `^RA2FlakWeapon`, and other intermediate addons still supply the non-converted warheads. Filter for blocks with exactly one `Inherits` line and no `Inherits@2`/`Inherits@3` addons; the first broad run must be reverted.

## Weapon 3-way split: projectile family naming (2026-08-07)

- **The new projectile family for cannons is `Shell_`, not `Cannon_`.** `^Projectile_Shell_Light/Medium/Heavy` exists; `^Projectile_Cannon*` does not. `CannonHE_Heavy` and `CannonAP_*` weapons use `^Projectile_Shell_*` for delivery and `^Effect_CannonHE_*` / `^Effect_CannonAP_*` for impact.

## Between-cell movement responsiveness (2026-08-11)

- `^DefaultInfantry` enables `ResponsiveBetweenCells` for responsive foot infantry.
- A defined `Mobile.TurnSpeed` remains the documented marker for infantry that deliberately turn like vehicles; those actors inherit `^VehicleTurnRateInfantry`, which only sets `Mobile.ResponsiveBetweenCells: false` so their balance values and movement tuning remain unchanged.


## `docs/audit/latest/` is environment-bound — an incomplete tree reports LESS and still says PASS (2026-08-23)

**The failure is not that the audit breaks. It is that the audit succeeds.**

`docs/audit/latest/` is TRACKED evidence, and a dozen audits read things that are not in this
repository — `engine/` C# sources (a build output, `.gitignore`d, CLAUDE.md rule 7) and full git
history. Run the suite where those are missing and nothing errors: the scripts scan a smaller
corpus, find fewer problems, print a smaller number and say **PASS**. Commit that and real
findings are deleted from the tracked evidence with a clean diff and a green run.

Measured in a cloud container on 2026-08-23, one `git add` away from being committed:

| report | complete tree | incomplete tree | why |
|---|--:|--:|---|
| `unique_traits.md` | 125 trait types † | **11** | no `engine/**/*.cs` to resolve `.Trait<T>()` |
| `dead_warhead_fields.md` | 27071 warhead nodes | **7014** | no C# field sets, so most types are "not checked" |
| `fluent.md` | 5235 messages | **3640** | the engine ships fluent files too |
| `assets.md` | 8780 WAVs | **4390** | the engine's own mods are not there |
| `recent_changes.md` | 663 files touched | **31523** | shallow clone: the grafted boundary commit looks like it touched the world |

† 125 was itself an under-report. `audit_unique_traits.py` looked for CA under `engine/OpenRA.Mods.CA`, but `OpenRA.Mods.CA` is **vendored at the repo root** — so 14 CA trait types had never been scanned on ANY machine. The complete-tree figure is **139**. A denominator can be wrong on the good tree too.

`git log` showed `latest/` had been ping-ponging between a Windows checkout and a container for
several commits — each run overwriting the other's numbers, `unique_traits.md` flipping 125 ↔ 11
in commit after commit — so the committed set was a MIXTURE, some rows true and some degraded,
with nothing on the page saying which.

**The guard.** `tools/audit/environment.py` names the defects and the audits each one degrades.
Both runners call it first: an incomplete tree still runs the whole suite (the answers are
useful) but writes to the untracked `docs/audit/degraded/` and prints why. `--force-latest`
overrides for a deliberate partial refresh. `docs/factions/MATRIX.md` is diverted the same way.

⭐ **The general shape, worth more than this instance:** a tool that measures a corpus will report
the corpus it can see, and "fewer findings" and "fixed" produce the identical green. Before
believing a count fell, check that the DENOMINATOR did not. Every row above is a denominator
that moved.

⚠ Even on two complete trees the reports are not byte-identical: Windows writes `mods\cameo\…`
and Linux writes `mods/cameo/…`, and a few audits emit unordered rows. So a cross-platform
regenerate is never a clean diff, and `latest/` should be refreshed **whole, from one machine**,
not file by file.

⚠ And the suite writes TRACKED files outside `latest/`: `docs/factions/MATRIX.md`, plus
`tools/rename/rename_map_*.yaml`, which `gen_rename_maps.py` emits as a side effect of the
naming report. `git status` after a suite run is therefore *expected* to be dirty in places the
run never mentions — check what moved before assuming a stray edit.


## Measure the law's OWN pipeline, and never validate a rule against the corpus it generated (2026-08-24)

Two failure modes from one session designing DESIGN §12.0i's armor axis. Both produced results that
were internally consistent, plausible, and wrong — the hardest kind to catch.

**1. A measurement of an INCOMPLETE pipeline is not evidence about the design.**

§12.0d says the class tilt "is applied to the VALUES and each armor is then given back the RANK it
held". `audit_heaviness_bell.py` skipped that restore and compared only each ladder's first-vs-last
rung. Everything measured against it was wrong:

| conclusion drawn | reality with the restore in place |
|---|---|
| 2 permanent `KNOWN_INVERSIONS`, "a gap in §9.4, author new gradients under rule 4" | 0 inversions; nothing needs authoring |
| a tier-anchored peak "inverts 26 of 42 families", so §12.0i law 1 must anchor to the family | `mu = h` inverts **nothing**, at any sigma, across 44 families × 5 heaviness values |
| ladder orderings changed by the bell: 0 (endpoints only) | **127**, across 60 family/ladder pairs |

The endpoint check was ALSO blind to 125 reorderings it should have caught, so the same omission
produced both a false positive and a false negative. **When a binding law names a pipeline STEP,
implement the step before measuring against the law.**

**2. A GENERATED corpus cannot confirm the rule that generated it.**

The maintainer asked for a continuous heaviness value per armor, and the tempting move was to
derive it from the 45 authored `^Warhead_*_Medium` profiles rather than hand-type 15 numbers. PC1
of those profiles looked like a triumph: every ladder monotone lightest→heaviest, and it reproduced
the maintainer's own independent statement (*"bomber is between light and medium, helicopter
between medium and heavy"*) to two decimals. It was not a measurement of heaviness:

* **56% of PC1 was ladder MEMBERSHIP, not heaviness** — macro-type priority in disguise (`Bullet`
  favours infantry whatever its heaviness). PC2 was 93% ladder membership.
* Remove the macro-type term and the cross-ladder OFFSETS vanish with it: each ladder's residual
  mean is exactly zero **by construction**. They are not identifiable, at all, from any corpus.
* The within-ladder SPACING that survives correlates **0.979** with mean `build_order` rank — it
  re-reads `gen_weapon_template`'s interleave rule rather than confirming it.

What the corpus legitimately confirms is the rung ORDER (with macro-type removed, one axis explains
92.3% of the residual and all four ladders come out monotone independently) — which was never in
doubt. **Reporting "this is a ruling, not a measurement, and here is why it cannot be one" is what
got the numbers ruled.** Dressing a design decision as a fit would have shipped 15 numbers nobody
had actually chosen.

**3. The corollary for acceptance tests: compare like with like.** "Can the bell reproduce the
shipped Light/Heavy templates from one base?" scored the bell at 2% better than doing nothing, and
that nearly went in the notes as evidence against the model. The control killed it: the **shipped**
`class_tilt` scores **+18.7% WORSE than doing nothing** on the same comparison, because the level
also changes the body's `step` and `floor` (`LEVELS` in `gen_weapon_template.py`), not just the
tilt. Compared tilt-to-tilt on the same base, the bell recovers ~60% of the shipped tilt. Always run
the shipped implementation through your own acceptance test first — if it fails, the test is wrong.

## An audit is not evidence of a law — two guards enforced retired designs (2026-08-24)

A failing audit feels like a finding about the tree. Twice in one session it was a finding about
the AUDIT, and in one of those cases believing it would have meant **changing shipped content to
satisfy a rule that no longer existed.**

**1. `audit_physical_state_warheads` demanded warheads the AreaDamage fold had folded away.**

It looked for a separate `Warhead@{Flame,Chemical}_{Light,Medium,Heavy}_Percentage` twin of type
`AreaDamagePercentage`. All six reported "missing percentage warhead", it had been red for days,
and the drafted fix was *"make `gen_weapon_template.py` emit the six twins its own comment already
promises."* That would have added six warheads to satisfy a retired structure.

The fold put all of it in ONE node — `AreaDamageWarhead` carries `PercentageScale`,
`PercentageSpread`, `PercentageVersus`, `FriendlyFireDamage` and `FriendlyFireSpread` as fields:

```
Warhead@Flame_Light: AreaDamage
    Damage: 2000  Spread: 200  Falloff: 100, 90, 78, 60, 0   <- flat
    PercentageScale: 10000   PercentageSpread: 50            <- percentage, folded in
    FriendlyFireDamage: 50   FriendlyFireSpread: 50          <- friendly fire, folded in
    PhysicalStateName: Temperature   PhysicalStateScale: 100 <- the meter
```

⛔ **The tell that was walked straight past: `verify_generator_sync` reported 0 drift.** The
generator and the yaml agreed. When two independent artifacts agree and a THIRD checker disagrees,
**the checker is the suspect** — the same rule already written down as *"a result that contradicts
a binding law is a contradiction, not a finding"*, and it still lost to the instinct to fix the
data.

⚠ Second trap inside the first: the meter has **two legal forms**. Flame uses singular
`PhysicalStateName` + `PhysicalStateScale`; **Chemical uses the `PhysicalStates:` MAP**
(`Corrosion: 100`), which is what blend families emit. Reading only the singular form makes
Chemical look like it has no meter at all.

**2. `audit_level_ladder` enforced a damage ladder no law states.** It required a family's
effective damage to rise Light -> Medium -> Heavy -> Super. DESIGN §12.0d makes the level a TILT,
§12.0h makes `Damage` a free knob, and 145 `^Warhead_*` templates carry only a placeholder
`Damage: 2000` — the template holds the SHAPE, the weapon holds the MAGNITUDE. Nine families sat
in a standing WARN for weeks, and it was `WEAPON_HEAVINESS.md` §9.6's "blocker #1", holding up the
continuous-heaviness bell for nothing. Retired by maintainer ruling.

**The habit both cases needed:** before acting on an audit's findings, ask **what design era it was
written for**, and grep `docs/DESIGN.md` for the structure it demands to confirm that structure is
still current. An audit encodes a law as of the day it was written; DESIGN.md is the law now.

⚠ And the corollary for authors: when a design supersedes a structure, **the guards that enforced
the old one are part of the change**. Both of these outlived their designs because the yaml moved
and nobody swept the audits.


## Porting from an upstream mod: a NEW NAME is not a NEW MECHANIC (2026-08-23)

Cameo is absorbing four upstream mods (`docs/design/UPSTREAM_MODS.md`). The obvious way to decide
what to take is "which of their types do we not have" — and it is wrong, because **the same
mechanic arrives under different names in different mods**, and a name comparison cannot see that.

The case that proved it. `audit_upstream_adoption.py` listed Romanov's Vengeance's `Temporal`
warhead and `AffectedByTemporal` trait as NEW, and a grep for `Temporal` across every assembly
Cameo loads returned nothing — so they were ported into `OpenRA.Mods.Cameo`, adapted for the
one engine API difference, built clean, and confirmed registered in `--docs`. Every step passed.

They were duplicates. Combined Arms' `WarpDamage` + `Warpable`, vendored here for months, are the
same design — a `TargetDamageWarhead` subclass routing damage into a meter on a companion trait —
and are **already wired to `ChronoBeam` and `IFVChronoBeam`**, exactly the weapons RV points
`Temporal` at. CA's is the richer version (`RevokeRate`, `ScaleWithCurrentHealthPercentage`).
The two traits even carry a word-for-word identical `[Desc]`. The port was reverted before
anything was built on it.

**Nothing on the C# side could have caught this.** The grep was correct, the build was correct,
the registration was correct. What caught it was opening the DESTINATION — the actor that would
use the new trait — and seeing a working implementation already there.

So, before porting any upstream type:

1. **Find the actor or weapon it would serve, and read it.** `ra2_allies_chronolegionnaire` fires
   `ChronoBeam`; one look at that weapon ends the question. This is the only reliable step.
2. **Search by MECHANIC, not by name** — the damage-routing base class, the companion trait, the
   yaml field names — and search `OpenRA.Mods.CA` explicitly, since it is vendored at the repo
   ROOT and a search rooted at `engine/` will miss all 181 files of it.
3. **Let the audit pair the descriptions.** `audit_upstream_adoption.py` now compares `[Desc(...)]`
   text and reports matches as a stop sign instead of a candidate. It found **52** such pairs
   across the four upstreams — RV alone drops from 15 "new" types to 7. But the match is evidence,
   not proof, and it misleads **both** ways: it missed `MissileSpawnerOldSlave`, a real duplicate
   whose wording differs by one word, and it flags `LeaveSmudgeSP`, which repeats Common
   `LeaveSmudge`'s description verbatim while being a genuine superset of it. The pairing narrows
   the reading list; it does not replace it.

⚠ The cost of getting this wrong is not a broken build — it is a second implementation of a live
mechanic sitting unused in the assembly, which is exactly the bloat `UPSTREAM_MODS.md` §5 warns
about (86 of the 142 CA trait types already vendored here are unused).


## Two ways a gate passes its own verification and is still broken (2026-08-23)

The commit that added `tools/audit/environment.py` and the D8 citation check shipped with two
defects, both in the new code, both "verified" before landing. The verifications were real —
they were just aimed slightly off the thing that mattered.

**1. A grep whose filter excluded exactly the counter-evidence.**

`environment.py` needed the list of assemblies whose C# the audits read. The list was copied in
spirit from `audit_unique_traits.py`, then sanity-checked with:

    grep -n "engine" tools/audit/audit_dead_warhead_fields.py

which printed the `AS`, `Cnc`, `D2k` and `Common` rows and looked like confirmation. It was not.
`audit_dead_warhead_fields.py`'s table is:

    ("AS",     "engine/OpenRA.Mods.AS"),
    ("CA",     "OpenRA.Mods.CA"),        <- no "engine", so the grep hid it
    ("Cameo",  "OpenRA.Mods.Cameo"),     <- likewise
    ("Cnc",    "engine/OpenRA.Mods.Cnc"),

**`OpenRA.Mods.CA` and `OpenRA.Mods.Cameo` are VENDORED AT THE REPO ROOT**, not under `engine/`.
The two rows that disproved the assumption were precisely the two the filter removed, and the
filter was the word the assumption was built on. So the new gate listed `engine/OpenRA.Mods.CA`,
a path that cannot exist on any machine, and `incomplete()` returned a reason even on a fully
built Windows tree — the gate could never say "complete", and diverted a legitimate run's 65
reports to `degraded/`. The same wrong path had been sitting in `audit_unique_traits.py` for
much longer, silently: 125 trait types scanned instead of 139.

⭐ **When you grep for the word your belief is made of, matches confirm nothing** — the
counter-examples are the lines that lack the word. Either read the whole structure, or grep for
the FIELD (`OpenRA.Mods`) rather than the value you expect (`engine`). `ls` would also have
settled it in one call.

**2. A tracked-file scan run while the new file was still untracked.**

`audit_doc_health` enumerates files with `git ls-files`. The D8 check was added along with
`tools/tests/test_audit_doc_health.py`, whose fixtures deliberately contain a wrong citation
label so the detector can be tested against the real bug. Running the audit at that moment
reported **0 findings** and exit 0 — correctly, because the test file was still UNTRACKED and
therefore invisible to `git ls-files`. `git add` made it visible; the very next run of the suite
reported 3 findings and exited 1 on a clean tree.

⭐ **Any check that enumerates via `git ls-files` must be re-run AFTER staging**, never before.
Otherwise the last thing you verify is a tree that does not contain your change. This is the
third instance of the self-reference class in this one audit — D5 needed the same exclusion for
its own `GONE` table, and D4 for its own example anchor. A detector that scans the repository
will eventually scan itself and its tests; write the exclusion when you add the check, not after
it fires.


## "Regenerable" is a claim about a tool, and it needs running (2026-08-28)

The 83→43 documentation compaction deleted 40 files. Its commit message said **nothing was
summarised away** and that every merged file's content lines had been checked for presence
in the target — verified mechanically, 0 lines lost.

That claim was true, and it covered the wrong set.

It described the files that were **merged**. Alongside them, fifteen files were **deleted
outright** on the grounds that they were generated and could be rebuilt on demand. That
second claim was asserted, not tested.

Re-checking it later, by diffing every deleted file's content lines against the whole live
corpus:

| outcome | count |
|---|--:|
| carried across into a merge target | 24 |
| deleted, regeneration **verified by running the generator** | 13 |
| deleted, **not regenerable** | 2 |

The two that were not:

* `docs/balance/BALANCE_AUDIT.md` — a per-unit formula-price-vs-cost delta report. Its
  generator, `tools/balance/_balance_audit_report.py`, raises `ModuleNotFoundError: No
  module named 'scout_rebalance_proposal_final'`. The module was removed long ago;
  `propose_class_rebalance.py` even carries a comment saying those modules no longer
  exist. The script is dead, nothing runs it, and nobody noticed because nobody ran it.
* `docs/balance/proposal_vehicle_defense_anchors.md` — deleted with thirteen
  `proposal_*.md` siblings, but it is not one of them. The proposer writes
  `proposal_<class>_infantry.md`; this name matches no pattern and a repo-wide search
  finds no generator at all. It was deleted by resemblance.

Both are restored under `docs/history/balance/` with banners, because their numbers
predate W24 and are provenance rather than current truth.

⭐ **Deleting a generated artifact is safe exactly when the generator runs.** That is one
command, and skipping it converts a reversible cleanup into permanent loss that a green
verification report actively conceals — the check that ran measured merges, and the files
at risk were the ones it did not cover. Run the generator, or keep the file.

⭐ **Group deletions inherit the safety of the group's weakest member.** Fourteen files
were removed under one justification; thirteen deserved it. A filename that merely looks
like the others is the one to check individually, because resemblance is not provenance.

## "Not found" is not "not there" — three ways a grep lies (2026-08-28)

Three separate disagreements in one week, between careful people looking at the same
project, all with the same shape: someone searched, found nothing, and concluded the thing
did not exist. Every time, it did.

**1. Wrong commit.** Five outside reviews declared seven documents missing —
`MASTER_REPORT`, `audit/FINDINGS`, `BALANCE_MEGAPLAN`, `PROJECT_CONTEXT` and others. All
seven had been merged away by the 83→43 compaction. The reviewers were not describing this
repository; they were describing it on an earlier date, and disagreeing with each other
about *when* rather than about *what*.

> `git log --all -- <path>` separates **moved** from **never existed**. A path with commits
> behind it and none at HEAD was relocated, and the report's substance may still be sound.

**2. Wrong load state.** Four USA doctrine conditions in `defaults.yaml` looked like dead
wiring: nothing on master grants them, so five multipliers hang off conditions that can
never fire. The provider exists and works — `usacommand` in `rules/generals.yaml`, which
`mod.yaml` has commented out. Dormant content can be the sole provider for live wiring, so
the defect is real on master and invisible to anyone working with that pack enabled.

> Check `mod.yaml` before calling wiring dead. State which files were loaded when reporting
> it.

**3. Wrong namespace.** The same four tokens then vanished from a contributor's tree
entirely. That tree had renamed 874 actors plus every id that doubles as a string match, so
`usabombardament` had become `usa_doctrine_bombardmentbattleplan` — locally, and nowhere
else. Searching master's names against a renamed tree returns nothing, and nothing looks
identical to deleted.

> Before concluding a rename removed something, search for what it was renamed *to*. A
> rename map is the fastest way to translate between naming generations.

⭐ **A finding is scoped to a commit, a load state, and a namespace.** All three must be
established before "I could not find it" becomes "it is not there" — and each failure is
invisible from inside, because a search that returns nothing looks the same in every case.

⭐ **Trace a mechanism end to end rather than inferring its absence from an empty grep.**
The load-state case took four links to settle — production grant, prerequisite, condition,
multiplier — and stopping at any one of them produced a confident wrong answer. Two of the
three disagreements above were resolved only by walking the whole chain; none was resolved
by a better search term.

The worked instances, with line numbers, are in
[`design/BALANCE_PIPELINE_GAPS.md`](design/BALANCE_PIPELINE_GAPS.md) §0–§0b.

## `Inherits` POSITION is semantic, not cosmetic (2026-08-16)

**The last node wins, and `Inherits` is a node.** `MiniYaml` walks a definition's children
in document order; when it reaches an `Inherits`/`Inherits@X` line it splices the parent's
resolved children in **at that point**, and anything later overrides anything earlier
(`tools/audit/miniyaml.py` `_resolve_generic` reproduces this faithfully). Therefore:

- `Inherits` at the **TOP** → the definition's own nodes win over the parent. This is what
  almost every definition intends, and it is the tree's convention.
- `Inherits` at the **BOTTOM** → **the parent silently overrides the definition's own values.**

**How it bit us.** The W23 retrofit appended `Inherits@wh: ^Warhead_<Family>_<Level>` after
the *last* existing `Inherits`. `^HeavyCannon`, `^MediumCannon` and `^TankDestroyerCannon`
each already carried `Inherits@glow: ^ImpactGlow` near the END of their block (~line 81)
while their warheads sit at line 9 — so the family inherit landed *below* the warheads and
the family's `Damage: 2000`, `Spread: 250` and `Falloff` overrode the template's own
carefully rescaled `Damage: 838` and its preserved geometry.

**Nothing catches this.** It lints clean under `--check-yaml`, it boots to the menu, and
`find_empty_warhead` stays 0. The only signal is a before/after resolve diff
(`tools/balance/verify_retrofit.py`). Cost: a full debugging round, during which the yaml
was reverted twice.

**Rules:**
1. Any tool that ADDS an `Inherits` line must insert it at the TOP of the block, never
   append it after existing ones, unless the parent is deliberately meant to win.
2. When a definition's own value mysteriously "doesn't apply", check where its `Inherits`
   lines sit relative to that value BEFORE suspecting the merge engine.
3. A weapon whose own `Warhead@X` is declared ABOVE its `Inherits` lines is already relying
   on the parent to win — e.g. `japan_imperialscoutsman_rifle_waveforce` declares
   `Warhead@Railgun_Heavy` at line 0 and three `Inherits` at lines 2-4.

## Template location and PhysicalStates forms (2026-08-20)

Two resolver/tooling gotchas from the chemical-weapon and artillery-projectile pass:

1. **Do not duplicate a ^Projectile_* template across weapons/weapons.yaml and a ContentPack Shared pack.** mod.yaml loads weapons/weapons.yaml after the ContentPack Weapons list, so the global copy silently shadows the pack copy and any weapon that only inherited the pack copy changes behaviour. If a template needs to be global, put it in weapons/weapons.yaml and remove the pack copy; if it needs pack-local defaults, use a pack-scoped name.

2. **Chemical percentage warheads can declare physical-state meters in two forms:** a direct PhysicalStateName / PhysicalStateScale pair, OR a nested PhysicalStates: map (e.g. Corrosion: 100). tools/audit/audit_physical_state_warheads.py now resolves both forms; any future audit touching physical states must do the same or it will falsely report that Corrosion is not being fed.

## Contrail fields are projectile, not warhead, and can survive a projectile type swap (2026-08-20)

The legacy mixed-stack missile weapons (`227mm`, `GDIRigMissilePod`, `MammothTusk`) inherited `^FlakWeapon` — a `Bullet` projectile with `ContrailStartColor: FF884400` and `ContrailEndColor: 000000FF` — and then a `^*Missile` template that switched the projectile to `Missile`. Because `ContrailStartColor`/`ContrailEndColor` were not re-declared in the missile template, the resolved `Projectile: Missile` still carried the flak bullet colors.

A naive 3-way split onto `^Projectile_Missile_*` drops those colors and `review_resolve_diff.py` flags `Proj.CStart`/`Proj.CEnd`. Preserve them as local `Projectile:` overrides on the concrete weapon whenever the resolved baseline had them and the new family does not.

---

## Tooling fixes discovered during W24 A1a (2026-08-22)

- tools/rename/safe_rename.py lower-cased every replacement. It now preserves the exact case written in the rename map, so mixed-case OpenRA ids stay canonical.
- tools/balance/splice_templates.py ran gen_weapon_template.py with a family filter, which caused shield_uniqueness to see only a subset and emit wrong compressed Shield values. It now always runs the full generator and splices only the requested blocks, preserving the original newline style (CRLF/LF).
- The A1a delivery-first rename proved that verify_generator_sync.py is the real source of truth for ^Warhead_* blocks: the Flame and MissileChem blocks had drifted by one Shield point and were re-synced by splicing.

## Upgrade regressions feel like downgrades (2026-08-19)

A W24 collapse can move an upgrade pair onto families with **opposite Versus profiles** and still pass every damage check, because the on-grid `Damage` total is preserved on both sides. `audit_upgrade_regression.py` was added to catch this:

- **314 gated armament pairs** scanned (`Armament` with `RequiresCondition`, one half `!cond` and the other `cond`).
- **59 findings** in the first pass:
  - **12 STRICTLY WEAKER** — the upgrade loses on every core armor (e.g. `RA2PatriotThunderboltMissile` vs `RA2Patriot` is 0.13× on vehicles, `TSHellfireSonic` vs `TSHellfire` is 0.11× vs Superheavy).
  - **42 ROLE-SHIFTED** — wins on some armor, loses on others (legitimate for a specialist, a regression when the loss is on the armor the unit exists to fight).
  - **5 THIN MARGIN** — the upgrade never loses, but is worth only ~1.03–1.10× where it matters while multiplying on another class. `MonsterTank120mm -> MonsterTank120mmThermobaric` is the poster case: same geometry, 1.5× damage, but the Versus shift means it is **+4% vs Scout / +7% vs Light / +16% vs Medium** and **+126% vs infantry**.

⚠ **A2 was NOT the root cause.** Measured before vs after A2: **54 findings before, 54 after.** A2 deepened the pre-existing `Su57` case from 0.92× to 0.87×. This is pre-existing debt the W24 collapse made visible.

**Rule:** every upgrade must be verified with `python tools/audit/audit_upgrade_regression.py` after any family repoint that touches an armament pair. Do not rely on a damage-preservation check alone.

## Inline effect warheads should be inherited, not inline (2026-08-19)

Maintainer ruling: **Effect warheads (`Warhead@Effect*`) should live in `^Effect_*` templates and be inherited, not declared inline on a concrete weapon.** The only legitimate exception is superweapons, which may need multiple bespoke animations.

First scan: **665 concrete weapons carry 815 inline effect warhead nodes** (`Warhead@Effect`, `Warhead@EffectAir`, `Warhead@EffectWater`, etc.) instead of using `Inherits@fx:`. This is a structural-debt class: it duplicates FX definitions across the tree and makes the 3-way split harder to reason about.

**Rule:**
- A concrete weapon should use `Inherits@fx: ^Effect_<Family>` for its visuals.
- Local `Warhead@Effect*` entries should be reserved for **exceptional overrides** (e.g. a custom sound, a one-off `Explosions` list) and should be rare.
- Superweapons are exempt from the inherit rule because their effects are often unique and multi-animated.
- Add new effect families to `gen_weapon_template.py` / `weapons.yaml` instead of copy-pasting `CreateEffect` nodes.

**Guard:** `tools/audit/audit_inline_effects.py` is now implemented. Current baseline: **665 concrete weapons carry 815 inline effect nodes**; after auto-detecting superweapons, **628 weapons with 771 nodes** remain as non-exempt debt. Run it after any conversion batch to watch the count fall.

## A ContentPack can only ADD to a bot module - and a partial migration fails silently (2026-08-31)

`ContentPacks/**/yaml/ai.yaml` resolves BEFORE the global `Rules:` block, so
`cameo|ai/ai.yaml` is the LATER file and wins every leaf collision. Measured with
`--resolved-rules Player`, one case at a time, against a 1375-row baseline:

| what a pack does | what happens |
|---|---|
| adds a NEW dictionary row | unions - 1375 to 1376 rows |
| sets a scalar the global file also sets | global wins; the pack's value leaves no trace |
| declares a NEW trait instance (`@suffix`) | works, no warning |
| removes a trait the global file declares | `YamlException: There are no elements with key ... to remove` |

Three traps follow. First, "split the AI per ContentPack" is a SUBTRACTIVE job on
`ai/ai.yaml`: whatever the global file still declares is permanently unownable by
any pack. Second, a half-finished migration is SILENT - the global value simply
keeps winning, so the yaml looks split and behaves as if it never was. Gate every
step on a byte-identical resolved-rules dump, not on reading the file. Third,
"add, never remove": a pack cannot opt out of a global default, and reaching for
`-TraitName` to do it is a load-time crash. Express opt-out as a value the pack
ADDS - a condition, a prerequisite token, or a zero-weight row the consumer
treats as "never".

The corollary for multi-instance modules: `@suffix` instances load fine, so the
resolver will not stop you creating a second decision authority. Whether that is
safe is a property of the CONSUMER, not of the yaml -
`UnitBuilderBotModuleCA` resolves `UnitCompositionsBotModule` with
`TraitOrDefault`, which throws on the second instance, and a disabled
`ConditionalTrait` still occupies the trait dictionary - so gating five
composition modules by condition crashes on the first bot tick instead of
degrading.
