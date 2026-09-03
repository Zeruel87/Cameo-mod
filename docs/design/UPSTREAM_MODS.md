# Tracking the upstream mods

**Owns:** how Cameo absorbs work from the other OpenRA mods it descends from or wants to follow —
Combined Arms, Crystallized Nexus, Romanov's Vengeance and Shattered Paradise — what may be
adopted automatically, and what may never be. Measured, not assumed — every number below comes from
`python tools/audit/audit_ca_drift.py` and from the two git histories.

> Maintainer, 2026-08-23: *"Cameo is like the Frankenstein Monster of all the OpenRA mods, it
> tries to combine everything into one single mod."* That is the goal this document serves —
> absorb CA's mechanics without losing what Cameo already has.

---

## 1. The lineage, and the one fact that decides the strategy

Cameo began as a fork of CA, which is why `OpenRA.Mods.CA/` sits at the repo ROOT (it is mod
code, exactly like `OpenRA.Mods.Cameo/`, and is **not** part of `engine/`). Cameo's ENGINE later
moved to the Romanov's Vengeance / Shattered Paradise line, which brings `OpenRA.Mods.AS`.
That line is no longer maintained, which is what raises the question of returning to CA.

**Measured against the two engine repositories:**

| | |
|---|---|
| common ancestor | `0eb173e046`, **2024-11-16** (both are forks of upstream OpenRA) |
| Cameo engine ahead of it | **2 581 commits** (`cameo-mod/OpenRA`, branch `cameo-engine`) |
| CA engine ahead of it | **111 commits** (`Inq8/OpenRA`, branch `ca-engine/1.09`) |
| `OpenRA.Mods.AS` in CA's engine | **absent** — CA ships only `Cnc`, `Common`, `D2k` |

⛔ **Therefore: do NOT move Cameo's engine onto `ca-engine`.** It is not an upgrade, it is a
23-fold regression — it would discard 2 581 commits and delete the entire `OpenRA.Mods.AS`
assembly, which Cameo depends on (`mod.yaml` loads it FIRST in the assembly order, ahead of CA).
"Getting back to CA" has to mean the opposite direction of travel:

> **Bring CA's MOD code forward onto Cameo's engine. Never push Cameo's engine back to CA's.**

That also explains the shape of the existing drift. CA's code targets an engine only 111 commits
past the 2024 base; Cameo's is 2 581 past it. So a vendored file usually differs because someone
**forward-ported** it — not because it went stale. A blind `cp -r` from CA would REVERT those
adaptations and break the build. Some files are the other way round (CA fixed a bug after we
copied it), which is exactly why this needs a per-file three-way merge and not a sync script.

## 2. Where we stand today

Run `python tools/audit/audit_ca_drift.py` (set `CA_ROOT` if the clone is not at
`../CAmod`). As of 2026-08-23:

| | files |
|---|--:|
| vendored here | 181 |
| upstream | 471 |
| identical to upstream | 41 |
| drifted | 108 (9 781 lines) |
| ours only | 32 |
| **upstream, never adopted** | **322** |

Of the 108 drifted, **30 differ by ≤6 lines** (a rename or a small fix — cheap to adopt) and
**31 by more than 50** (a different implementation — port by hand or leave alone). The largest
are the bot modules (`BaseBuilderBotModuleCA` 743 lines, `SquadManagerBotModuleCA` 559,
`UnitBuilderBotModuleCA` 542): Cameo's AI has been reworked and those must NOT be overwritten.

⚠ **Adoption is not the bottleneck — usage is.** Of **142** CA trait types already vendored,
only **56** appear in Cameo's rules. Pulling 322 more files would take the catalogue past 400
while leaving ~86 existing ones unused. Wiring traits into yaml is the scarce work, not copying
C#, and §5 puts it first for that reason.

## 3. What to adopt, in order

**Phase 1 — make it measurable and repeatable.** ✅ done: `audit_ca_drift.py` exists and is in
the suite. Nothing else can be judged until the drift is a number anyone can re-derive.

**Phase 2 — the 30 cheap files.** Diffs of ≤6 lines. For each: read the diff, take it if it is
an upstream fix, keep ours if it is our forward-port. Build after each batch of ten; boot-gate
the batch. This is where CA bugfixes we are missing actually live.

**Phase 3 — adopt by CAPABILITY, never by directory.** The 322 unadopted files are not a backlog
to burn down; they are a menu. Order by what Cameo wants:

| area | files | why it is interesting |
|---|--:|---|
| `Traits/SupportPowers` | 26 | the largest single block of mechanics Cameo does not have |
| `Widgets/Logic` | 24 | UI; low gameplay risk, and the observer work already proved the pattern |
| `Traits/Conditions` | 22 | small, self-contained, composes with everything |
| `Traits/Player` | 19 | economy/tech mechanics |
| `Traits/Render` | 17 | visual only; safe to trial |

For each capability: copy the file(s), fix the namespace, build, add a Cameo-only field to prove
the type resolves to OUR assembly, wire one concrete actor, boot-gate. That is the same
procedure the CA observer widgets went through, and it caught real problems each time
(`OpenRA.Player` shadowed by a nested namespace; `TooltipContainerWidget` implicit under CA's
`namespace OpenRA.Mods.Common.Widgets`).

**Phase 4 — the 31 heavily diverged files.** Case by case, and the default answer is NO. The AI
modules in particular carry Cameo-specific behaviour.

## 4. Staying current, permanently

Fully automatic adoption is not safe — the engines differ by 2 581 commits, so any CA change can
fail to compile here. What can be automated is **noticing**, and that is the part that decays:

1. **Three audits run in the suite** (`tools/audit/run_all.sh`), all INFORMATIONAL — adopting
   upstream code is a maintainer decision, never a gate:
   * `audit_ca_drift` — per-FILE drift against CA, and every upstream file not adopted;
   * `audit_upstream_adoption` — what is left across all five mods by TYPE, with duplicates
     paired off by `[Desc]` text (§7);
   * `audit_engine_freshness` — the gap to `openra/bleed` and to `mtr/rv-engine`, plus whether
     `engine/VERSION` matches `mod.config`. It does not fetch; refresh the `cameo-engine` clone
     first or the number is as stale as the last fetch.
2. **Record provenance.** When a file is adopted, note the CA commit it came from in its header,
   the way the ported observer widgets do. Without that, a future three-way merge has no base
   and every re-sync is guesswork.
3. **Refresh the clone before judging.** `git -C ../CAmod pull` first; a stale checkout reports
   stale drift. This has already burned one session — a `~/Downloads` copy of CA was old enough
   to be missing a whole tab, and produced a confident, wrong "CA doesn't have this".
4. **Compatibility is proven by BUILD + BOOT, not by reading.** `dotnet build -c Release
   -p:TargetPlatform=win-x64` then `launch-game.cmd` to the main menu. A file can compile and
   still not resolve to the intended assembly — `ObjectCreator.FindType` takes the FIRST match in
   `mod.yaml`'s `Assemblies:` order, which is **AS, CA, Cameo, Cnc, D2k, Common**. A Cameo type
   cannot shadow an AS one; a CA type cannot shadow an AS one either.

## 5. The honest bottleneck

The scarce resource is not C# — it is deciding which mechanics Cameo wants and wiring them into
yaml. 86 of the 142 vendored CA trait types are already unused. Before adopting another 322,
the higher-value pass is over what is already here: pick the unused traits worth having, wire
them, and let that tell us what kind of CA mechanics are actually wanted.

**Related:** `docs/design/PROJECTILE_AND_EFFECT_LAYER.md` (weapon layer),
`docs/LESSONS_LEARNED.md` (the engine pipeline and the assembly-order trap).


---

## 6. The other upstreams (2026-08-23)

> Maintainer: *"we not only want RV and CA but basically ALL the OpenRA mods included … Cameo is
> like the Frankenstein Monster of all the OpenRA mods."* Generals Alpha added on request,
> 2026-08-23: *"another high profile OpenRA mod … a lot of interesting game mechanics we also
> want to use."*

All five are cloned beside this repo under `~/Documents/GitHub/`, so every number here is
re-derivable. **`git -C <clone> pull` before trusting any of it** — a stale checkout produced a
confident, wrong "CA doesn't have this" earlier in the same programme.

| mod | clone | mod assembly | .cs | engine it pins | last push |
|---|---|---|--:|---|---|
| Combined Arms | `CAmod` | `OpenRA.Mods.CA` | 471 | `Inq8/OpenRA` `ca-engine/1.09` | 2026-07-30 **live** |
| Crystallized Nexus | `crystallized-nexus` | `.modsdk/OpenRA.Mods.CN` | 134 (+21 launcher) | `DoGyAUT/crystallized-nexus-engine` `cn-20260820` | 2026-08-19 **live** |
| Generals Alpha | `Generals-Alpha` | `OpenRA.Mods.GenSDK` | 33 | `MustaphaTR/OpenRA` `40065d3e58` = tip of `rv-engine` | 2026-07-25 **live** |
| Shattered Paradise | `Shattered-Paradise-SDK` | `OpenRA.Mods.Sp` | 50 | `MustaphaTR/OpenRA` `ab187a38c2` | 2025-09-27 dormant |
| Romanov's Vengeance | `Romanovs-Vengeance` | `OpenRA.Mods.RA2` | 32 | `MustaphaTR/OpenRA` `ac7864a16d` | 2025-07-26 dormant |

⭐ **RV and SP need no engine work at all, and that is measured, not assumed.** Both pin commits
of `MustaphaTR/OpenRA`, and **both are ANCESTORS of `cameo-engine`** — checked with
`git merge-base --is-ancestor`. Cameo's engine already contains everything their engines had; it
is 2 581 commits past the 2024 base while they are frozen at points behind it. So for RV and SP
the entire question is their MOD assemblies, and those are small: 32 and 50 files.

That is also the answer to *"follow CA without losing what we got from RV"* — there is nothing to
lose. The RV/SP inheritance lives in Cameo's ENGINE (`OpenRA.Mods.AS` above all), which CA does
not have and which adopting CA mod code does not touch.

### The engine picture, once everything is measured

Every "N commits ahead" figure in this document is measured against the point where
**`cameo-engine` last took upstream OpenRA**: `b0b0544d4a`, **2026-05-11**, which is a commit on
`openra/bleed`. That point is also why `bleed` itself belongs on this page — see the next
section. Stated from there, the whole landscape is small:

| | |
|---|---|
| Cameo's OWN engine work since that point | **1 975** commits |
| Cameo behind `openra/bleed` | **70** commits |
| CN past that point | its own 170, on top of newer bleed |
| Generals Alpha past that point | **49**, of which only **8** are its author's own |

So Cameo is not far from anyone: it is **70 upstream commits behind bleed**, and each sibling mod
sits a different distance past that same sync point. A number like "CN is 8 227 ahead" is an
artifact of history shape, not of work — see the CN section below.

### OpenRA bleed — the sixth upstream, and the only one that is not a mod

> Maintainer, 2026-08-23: *"add the OpenRA bleed to the repository list because we also want to
> update from there as well … It should always try to keep it up to date there as well."*

`OpenRA/OpenRA` branch `bleed` is where all five mods ultimately descend from, Cameo included.
It belongs on this page, but it is a different KIND of upstream and the difference matters:

* the five mods are absorbed by **copying types into a mod assembly** — reversible, inert until
  yaml references them, and gated by nothing heavier than a build;
* bleed is absorbed by **moving the engine**, which is the multi-step pipeline in
  `docs/LESSONS_LEARNED.md` (merge in the separate `cameo-engine` clone → push → set
  `ENGINE_VERSION` in `mod.config` → `make.cmd all` → **recreate `engine/glsl/` shaders, which the
  refetch wipes** → boot-gate) and touches every faction at once.

**Measured 2026-08-23:** Cameo is **70 non-merge commits behind `openra/bleed`**, and 47 behind
`mtr/rv-engine`, its direct parent. What is in that gap:

| | |
|---|---|
| rendering + performance (Gustas, 22 commits) | SIMD colour, matrix quad/text rotation, batched interleaved blend modes, texture subdata uploads, `float2/3` → `Vector2/3`, trigonometry and dedup speedups |
| allocation + language (RoosterDragon, 8) | `MiniYaml.FromLines` via `GetAlternateLookup`, `AggregateBy`/`CountBy`, C# 13 |
| build + platform (Mailänder, michaeldgg2) | **.NET 10**, ARM packaging, x86 and Mono dropped |
| pathfinding / gameplay fixes | units not moving aside to avoid deadlocks, `Move.UnblockDestination`, saboteur stuck, dock closest-path search, veins vs submerged units |
| ⭐ one real feature | **"Implement the Tiberian Sun Firestorm Defense"** (Matthias Hoste) — directly relevant, Cameo ships TS factions |

⚠ **This is not a free update.** The .NET 10 upgrade and the Mono/x86 removals change the build,
and `engine/glsl/` shaders must be recreated after the refetch. Schedule it deliberately, not as a
side effect of another task.

⭐ **`python tools/audit/audit_engine_freshness.py` (in `run_all.sh`) keeps the number honest.**
It reads the `cameo-engine` clone — never `engine/`, which is a gitignored build output — and
reports the gap to both `upstream/bleed` and `mtr/rv-engine`, plus whether `engine/VERSION`
matches `mod.config`. It deliberately does **not** fetch: it prints each ref's own date so a stale
answer is visible instead of silently wrong. Refresh with
`git -C ~/Documents/GitHub/cameo-engine fetch upstream mtr --no-tags` before reading it.

⚠ `engine/VERSION` is **UTF-16 LE with a BOM** — the SDK writes it from PowerShell, the same
hazard that forces `bash run_all.sh`. Reading it as UTF-8 gives NUL-separated digits that match
nothing; the first cut of this audit reported a permanent, false "the built engine is not the
pinned one" because of exactly that.

### Generals Alpha — measured 2026-08-23

⭐ **All three MustaphaTR mods pin points on ONE branch — `rv-engine` — and Cameo is a fork of
it.** Checked with `git merge-base --is-ancestor` against `MustaphaTR/OpenRA`:

| pin | on `rv-engine`? | relative to `cameo-engine` |
|---|---|---|
| RV `ac7864a16d` | yes | **ancestor** — we already contain it |
| SP `ab187a38c2` | yes | **ancestor** — we already contain it |
| Generals Alpha `40065d3e58` | yes — it IS the branch **tip** | **not** an ancestor: 49 commits past our fork point |

So the branch has four marks on it in order: RV, SP, the point Cameo forked at (`b0b0544d4a`,
2026-05-11), and `rv-engine`'s current tip, which is what Generals Alpha pins. Cameo then has
**278** commits of its own past that fork point.

⛔ **That corrects a premise this programme has been carrying.** "The RV engine is no longer
updated" is true of the RV *mod* (last pushed 2025-07-26) and **false of the branch**: `rv-engine`
was last touched **2026-07-25**, and Generals Alpha is what keeps it alive. The engine lineage
Cameo descends from is still maintained upstream — a different situation from the one that
motivated looking at CA at all.

⚠ Generals Alpha's README still points at `MustaphaTR/OpenRA/tree/generals-alpha-engine`. That
branch was last touched **2018-09-05**; the mod moved to `rv-engine` and the README did not.
Read `mod.config`, never the README, for the pin.

Of the 49 commits its pin has that we lack, **41 are upstream OpenRA bleed** merged into
`rv-engine` (Paul Chote, RoosterDragon, Matthias Mailänder, Gustas…) and only **8** are
MustaphaTR's own non-merge commits — all maintenance: style fixes, the `.slnx` migration, a
`FluentReference` location fix in `SupportPowerInfo>Names`, an `ISync` cleanup in the AS dll, and
a `ProductionQueue.Build` wrong-queue fix.

**So Generals Alpha needs no engine work for its features.** There are no gen-specific engine
patches to take; its engine is simply a fresher checkout of our own upstream branch. Everything
interesting is in `OpenRA.Mods.GenSDK` — 33 files, and §7 shows what that actually amounts to.

⭐ **It has the highest signal of any of the five.** All 20 of its candidate types are used by its
own rules — no dead code at all — and they cluster into whole MECHANICS rather than scattered
helpers:

| cluster | types | what it is |
|---|--:|---|
| **The supply economy** | 9 | `SupplyDock`, `SupplyCenter`, `SupplyCollector`, `ResupplyDock`, plus pips, collection/delivery overlays and two condition grants. Generals' supply-dock model — an ALTERNATIVE resource economy to harvesting, and Cameo has **no** equivalent type at all. |
| **Cash hacking** | 2 | `CashHack` warhead + `CashHackPower` (the Hacker / Black Market) |
| **`LaysMinefield`** | 1 | 20 uses, its most-used type. NOT our `Minelayer`: it *"places mines around itself, and replenishes them after a while"* — passive and self-refilling, where ours is ordered to lay. |
| **`ConditionIconOverlay`** | 1 | 15 uses; status icons drawn over a unit |
| **`PilotChamber`, `FakePower`, `RadarIcon`, `WithTerrainDependantSpriteBody`** | 4 | pilot ejection, decoy support powers, custom radar blips, terrain-dependent bodies |
| **Bot modules** | 2 | `InitialBaseAndWorkerBotModule`, `GeneralCollectorBotModule` — ⚠ Cameo's AI is reworked; treat as reference, not as a drop-in |

**Two things its yaml teaches, one of them a warning.** 33 files is a small assembly for a mod
this size because much of Generals is expressed in rules — and one of those rule systems we
already run:

* ⛔ **The generals-power tree is ALREADY HERE — it is Cameo's promotions system**, and ours is
  the more developed of the two. Do not "adopt" it. The lineage is visible in the actor names:
  both `rules/promotions.yaml` and GenSDK's `rules/generals_powers.yaml` declare
  `hack.has_points`, `hack.rank_3` and `hack.rank_5`, each `ProvidesPrerequisite` onto a
  tooltip-only prerequisite actor (`rank1`/`rank3`/`rank5` here, `prerequisite.has_points`/
  `.3_stars`/`.5_stars` there), feeding a dedicated `ClassicProductionQueue` of buildable
  upgrade actors. Cameo even kept the Generals vocabulary: `canselectfrenzy` reads *"OF-3 or
  Infantry General"* and `canselectrepair` *"OF-3 or Stealth, Nuclear, Tank Generals"*.

  What Cameo added on top is real C#: `PlayerPromotions` (XP thresholds, `PointsPerRank` presets
  default/classic/double/allatstart/none, lobby option, level-up notifications) and
  `UsePointsOnProduction`, both in `OpenRA.Mods.Cameo`. **GenSDK has no promotions trait at all**
  — 33 source files, none of them about ranks; it uses stock `PlayerExperience`.

  ⭐ The ONE delta worth taking is not a port: GenSDK puts `WithProductionIconOverlay` on each
  power so a taken icon greys out. That trait is stock `OpenRA.Mods.Common`, already available
  here, and Cameo uses it **0 times** — wiring it into `^PromotionUpgradeTemplate` is a yaml-only
  change.
* **`FullnessConditions` drives artwork from a stored amount.** `SupplyDock` takes a
  threshold → condition map (`834: one_third`, `1667: two_thirds`), and the sprite bodies switch on
  those conditions while `KillsSelf: RemoveInstead` clears the husk at zero. That threshold→
  condition shape is directly applicable to Cameo's physical-state meters.

Also sizeable and worth reading before designing anything similar: `rules/upgrades.yaml` (1 409
lines) and `rules/fakes.yaml` (1 021) — Generals' fake-structure system.

⭐ **And it exposes a half-wired mechanic we already have.** CA's `CashHackable` is vendored here
and applied to two actors (`rules/defaults.yaml:7913`, `rules/simcity.yaml:1252`) — but its own
`[Desc]` says *"Tag trait for Cash Hack support power"*, and **no assembly Cameo loads contains
that power.** Upstream CA has `Traits/SupportPowers/CashHackPower.cs`; we took the tag and not the
power. Two implementations are now available (CA's and GenSDK's), and adopting either turns a dead
tag into a working mechanic. That is the cheapest real win on this page.

**Three live upstreams, two frozen ones.** CA, CN and Generals Alpha are still moving, so they
need the recurring drift check of §4. RV and SP are dormant: mine them ONCE, record what was
taken, and stop watching them.

### Crystallized Nexus — measured 2026-08-23

CN is the newest and the most active, and unlike the others it **ships its own feature list**:
`crystallized-nexus/FEATURES.txt` enumerates what it adds over the stock TS mod, which makes it
the cheapest upstream to evaluate — read the list, pick, then look at the code. Its opening
section alone offers `VoxelDynamics` (spring-based impact/recoil/roll tilt on voxel units, with a
graphics toggle), drop-in `CNWithVoxelBody`/`Turret`/`Barrel`/`WalkerBody` replacements,
`AlphaGradientPalette`, `CharredPalette`, `DamageSmoke`, `PeriodicSpriteEffect` and a full-screen
`AtmosphericGradingRenderer`.

**CN pins its OWN engine fork** (`DoGyAUT/crystallized-nexus-engine`, tag `cn-20260820`), and
`FEATURES.txt` refers to "ENGINE PATCHES" — so some CN features are engine-side. That question is
now **measured**, and the answer is much better than the CA one:

| | |
|---|---|
| CN's pinned engine | `cn-20260820` = `d323caa350967b4b5769e1a5815adc7155c8aaee` |
| shared base with `cameo-engine` | `b0b0544d4a`, **2026-05-11** ("Add a heal debug command") |
| CN's own fork point | tag `openra-base` = `febbbfebe6`, 2026-04-24, *"Initial CN engine fork based on OpenRA bleed"* |
| **CN-authored commits** not in `openra/bleed` | **170** (DoGyAUT + dnqbob, all since 2026-04-24) |
| Cameo's own commits not in `openra/bleed`, for scale | 1 516 |

⭐ **CN's engine patches are cherry-pickable, and CA's are not.** CN and Cameo share a base only
**three months** old — against CA's 2024-11-16 — and CN's divergence is not a fork that drifted,
it is 170 enumerable commits on top of recent OpenRA bleed. `git log cn-20260820 --not
upstream/bleed --author=DoGyAUT` lists every one, and most are self-contained rendering work:
the bloom-glow pipeline, water reflections, cloud shadows, `VoxelDynamics`, per-projectile
`BeamBloomIntensity`, railgun distortion, Armament casing ejection, a zoom-scaled audio listener.

⚠ **Do not read the raw `rev-list --left-right` count.** It reports `cameo 1975 / CN 8227`, and
the CN side is history-shape noise: CN's history absorbs a legacy branch reaching back to 2017 and
has been re-based onto bleed twice, so the count measures ancestry bookkeeping, not work. The
`--not upstream/bleed --author=` figure above is the honest one. (`git log --format=%an ... | sort
| uniq -c` shows the top authors are Paul Chote, reaperrr and RoosterDragon — i.e. upstream OpenRA.)

So a CN feature is a mod-side copy if its type lives in `.modsdk/OpenRA.Mods.CN`, and a
`cameo-engine` cherry-pick otherwise — both are cheap. The pipeline for the second is in
`docs/LESSONS_LEARNED.md`.

### Order of work

1. **Generals Alpha first** — 20 live candidates, no engine work needed, no dead code, and the
   clusters are whole mechanics. Start with the two that cost one file each: adopt a
   `CashHackPower` so the `CashHackable` tag we already apply stops being dead, and `LaysMinefield`
   (20 uses upstream, and NOT our `Minelayer`).
2. **RV + SP** — 37 live candidates between them (§7), frozen upstreams, and no engine
   risk. Closes two upstreams permanently.
3. **CN** — 90 live mod-side candidates (§7) plus 170 cherry-pickable engine commits. The
   engine lineage is measured; nothing here is blocked on research any more.
4. **CA by capability** — §3, the largest and slowest, and the one where usage rather than
   adoption is the bottleneck.

Running alongside all four, on its own schedule: **catching `openra/bleed` up** (70 commits,
above). It is independent of every mod-side port — different mechanism, different risk, and it
touches every faction at once, so it wants a session of its own rather than a slot in this queue.
`audit_engine_freshness.py` reports the gap on every suite run so it cannot quietly grow.

⚠ The same trap applies to all five: `ObjectCreator.FindType` takes the FIRST assembly in
`mod.yaml`'s `Assemblies:` order — **AS, CA, Cameo, Cnc, D2k, Common**. A ported type placed in
`OpenRA.Mods.Cameo` cannot shadow one that already exists in AS or CA. Prove a port resolves to
the assembly you intended by giving it a field the other one lacks and booting with that field
set; `--docs` lists both types and proves nothing.

---

## 7. The only number that decides a port: TYPES, not files

File counts mislead. Cameo resolves names through **six** assemblies, so a large share of any
upstream mod is a type one of them already provides under the same name — and because
`ObjectCreator.FindType` takes the FIRST match in `mod.yaml`'s order (**AS, CA, Cameo, Cnc, D2k,
Common**), such a type cannot even be shadowed from `OpenRA.Mods.Cameo`. Porting it is not
redundant, it is unreachable.

`python tools/audit/audit_upstream_adoption.py` measures that directly. It reads the
yaml-VISIBLE name (`class FooInfo` -> trait `Foo`, `class FooWarhead` -> warhead `Foo`), not the
file name, and it counts how often the upstream mod's own rules use each remaining type — because
a type its own mod never references is dead code there too, and is not a porting candidate.

⛔ **A NEW NAME IS NOT A NEW MECHANIC, and this is the trap that actually bites.** RV's `Temporal`
warhead and `AffectedByTemporal` trait are CA's `WarpDamage` and `Warpable` — same
`TargetDamageWarhead` subclass routing damage into a separate meter on a companion trait, already
vendored here, already wired to the Chrono Legionnaire's `ChronoBeam` and `IFVChronoBeam`, which
are exactly the weapons RV points `Temporal` at. CA's version is the RICHER of the two (it adds
`RevokeRate` and `ScaleWithCurrentHealthPercentage`). Both types were ported into
`OpenRA.Mods.Cameo` on 2026-08-23, built clean, registered in `--docs` — and were reverted
unbuilt-upon once `ChronoBeam` was read. Nothing but reading the destination would have stopped it.

So the audit now also compares `[Desc(...)]` text: those two traits carry the **identical**
description, and so do five more RV types. Anything it pairs up is reported as a stop sign
instead of as a candidate.

⚠ **That match is evidence, not proof, and it misleads in both directions.** It missed
`MissileSpawnerOldSlave` (a duplicate whose wording differs by one word), and it flags
`LeaveSmudgeSP`, which repeats Common `LeaveSmudge`'s description verbatim while being a genuine
SUPERSET of it — smudge levels, ring size, a max level, its own `SmudgeLayerSP`. Read both
implementations before concluding either way; the pairing narrows the reading list, it does not
replace it.

As of 2026-08-23 (Cameo resolves **1 101** yaml-visible names):

| mod | types | already in Cameo | same mechanic, other name | candidates | live in its own yaml |
|---|--:|--:|--:|--:|--:|
| Romanov's Vengeance | 26 | 11 | 8 | 7 | **6** |
| Shattered Paradise | 46 | 7 | 7 | 32 | **31** |
| Crystallized Nexus | 107 | 5 | 2 | 100 | **90** |
| Combined Arms | 348 | 182 | 35 | 131 | **119** |
| Generals Alpha | 23 | 2 | 1 | 20 | **20** |
| | | | **53** | | **266 total** |

Four things fall straight out of that table:

* **53 upstream types are duplicates of something we already run.** That column did not exist in
  the first version of this audit, and without it RV looked like 15 new types when it has 7.
* **Generals Alpha is the densest of the five.** 20 candidates and **20 of 20 are used by its own
  rules** — the only upstream with no dead code in its candidate list — and they group into whole
  mechanics (a 9-type supply economy, cash hacking, self-replenishing minefields) rather than
  scattered helpers. Smallest assembly, highest signal. Detail in §6.
* **RV is nearly done, and the adoption was selective.** 11 of its 26 types resolve here today:
  8 vendored file-by-file into `OpenRA.Mods.Cameo` (`InfectableOld`, `InfectorOld`,
  `SpawnActorOrWeapon`, `StealResource`, `WithCargoBuilding`, `SoundAnnouncement`,
  `HeliGrantConditionOnDeploy`) and 3 free from CA (the `Mirage` family). Another 7 are duplicates
  — including BOTH halves of its infect rewrite, `AttackInfectRV` and `InfectableRV`, which
  duplicate `AttackInfect`/`Infectable` and their CA variants, and both halves of its old missile
  spawner. What is genuinely left is **7** small types, and only one of them is a mechanic:
  `SpawnBuildingOrWeapon`, which fills the case our own `SpawnActorOrWeapon` explicitly excludes
  (*"Don't use this with buildings"*). The other six are a capture sound, a support-power charge
  overlay, a palette flash, an owner-lost condition, a delivered-cash sound, and `LegacySpread`,
  which RV's own rules never reference.
* **CA is 52% adopted by type** (182 of 348) while only 41 of 181 vendored FILES are byte-identical
  — the gap between those two numbers is the forward-porting described in §1, and it is the reason
  a `cp -r` sync would break the build.

⚠ A high use-count is evidence the mechanic matters to that mod, **not** that Cameo wants it.
`ExplodesAlsoTransported` at 112 uses and `CNHealth` at 223 are load-bearing in SP and CN
respectively; whether Cameo wants either is a maintainer call, and §5's bottleneck still applies —
86 of the 142 CA trait types already vendored here are unused.

