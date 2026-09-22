# Audit summary — current known-issue state

_One page. Live reports: [`latest/`](latest/) · comparison snapshots: [`baseline/`](baseline/) ·
faction map: [`../factions/MATRIX.md`](../factions/MATRIX.md)._

**Evidence date: 2026-08-23**, from `bash tools/audit/run_all.sh` at `e60aab63`, with
`doc_claims` and `gen_sync` re-measured at `519175ae` (both read only tracked files, so they are
trustworthy from any checkout). `level_ladder` was RETIRED on 2026-08-23 — it enforced a
damage-monotonic rule no law states — and replaced by `heaviness_bell`.
Recurring code-health audits and their cadence: [`PERIODIC.md`](PERIODIC.md) +
[`periodic.json`](periodic.json).

⚠ **`latest/` is currently a MIXTURE of two environments and is owed one clean regenerate.**
A dozen audits read `engine/` C# or full git history — neither of which exists in a fresh
clone — and they respond by reporting *less* and still saying PASS (`dead_warhead_fields` 27071
warhead nodes → 7014, `fluent` 5235 messages → 3640). Alternating Windows and container runs
have been overwriting each other's numbers. `run_all` now refuses to write `latest/` from an
incomplete tree (it diverts to the untracked `docs/audit/degraded/`; `--force-latest`
overrides), so this is a one-time cleanup: **run the suite once on a complete tree and commit
the result whole.**

> **How to use this page.** Every number is a count from a report in `latest/`, named in the
> "report" column. If a number here disagrees with that report, **the report wins** — re-run the
> suite and fix this page in the same commit. Never hand-edit a count in without re-running.

```sh
bash tools/audit/run_all.sh          # regenerates every report in latest/ (UTF-8 enforced)
python tools/audit/audit_<name>.py   # one audit, straight to stdout
```

⚠ **Never regenerate reports with a PowerShell `>` redirect** — it writes UTF-16 and corrupts
the file (CLAUDE.md rule 8).

---

## AI personality wiring

`audit_ai_personalities.py` verifies that the five personality-gated
`SquadManagerBotModuleCA` instances retain byte-identical shared fields and
that their consumed conditions exactly match the `GrantRandomCondition`
selector. Personality-specific differences are restricted to an explicit
tuning allow-list.

The implementation removes the stale `RushInterval` and
`RushAttackScanRadius` keys; neither exists in the vendored CA or pinned engine
SquadManager implementation. Steamroller is intentionally documented as
having at most one harasser because the engine always creates the first
guerrilla squad and YAML cannot express zero guerrilla units.

The reusable `ObserverConditionNotification` trait announces each selected
personality once in the chat feed for spectators and replay viewers after its
condition activates. Live players are intentionally excluded so the indicator
does not leak opponent strategy; no live-player UI decoration is intended.

The five personality managers now use optional time-scaled squad-value
thresholds, preserving their early-game flat-bonus values. Other squad-manager
instances retain the flat `SquadValueRandomBonus` path. The ramp and the
actor-value cache have not been observed in a long match; that is an in-game
verification follow-up.

The unit-builder composition consumer is opt-in through `UseCompositions`.
Without an active composition, each personality's `UnitsToBuild` table remains
the fallback. The pilot compositions are limited to TD vehicle queues and are
gated by their respective tech prerequisites; broader composition coverage is
still a follow-up. Explicit unit requests continue to bypass composition
shares.

## Counts by bug class

| class | what | count | report |
|---|---|--:|---|
| **B8** | crash-class content | **0** | — |
| B1 | cross-faction leaks | 435 L1 · 20 L3 · 91 shared | `faction_leaks.md` |
| B2 | illegal inherits | 281 V1 · **0** V2 · **0** V3 dangling · 1863 V4 depth>3 · 95 V5 | `inherits.md` |
| B2b | duplicate inherit paths | 1770 definitions reach a parent by >1 path | `duplicate_inherits.md` |
| B3 | upgrade direction | 594 items · 103 inverted · **0** dead · 19 dead tokens · 568 without an intent entry | `upgrades.md` |
| B4 | upgrade coverage | 23 tagged upgrades · 21 uncovered unit slots | `upgrade_coverage.md` |
| B5 | AI wiring | 1801 refs · **0** defined nowhere · **0** unloaded · **0** unwired pool factions | `ai.md` |
| B6 | art/sequence refs | **0** missing images · **0** missing sequences · 594 unreferenced images | `sequences.md` |
| B7 | metadata rot | 32 duplicate-tooltip groups · **0** missing tooltip names | `metadata.md` |
| B9 | numeric drift | 176 robust outliers · **0** bounds over the 5×5 max | `outliers.md` |
| B10 | dead content | 374 orphan weapons · **0** dangling refs · 15 dead conditions | `orphans.md` |
| B11 | asset norms | 148 / 2006 PNGs over budget · 1817 / 4390 WAVs off-norm | `assets.md` |
| B12 | localization | **0** unresolved fluent refs · 526 orphaned `actor-*` messages | `fluent.md` |
| B13 | basebuilder crate coverage | **29/29** factions covered · 0 missing | `basebuilder_crates.md` |
| R2 | stacked multipliers | 790 units over the 2.0× power budget | `power_budget.md` |
| W | weapon uniqueness (§10) | 34 same-faction · 34 cross-faction · 95 carrier-only | `weapon_uniqueness.md` |
| G | garrison weapons (§11) | **0 G1** · 0 G2 · 0 G3 | `garrison_weapons.md` |
| F | house stat formulas | 615 violations across 1910 roster actors | `stat_formulas.md` |
| E | elite / rank wiring | 197 missing elite armaments · 21 ungated ELITE blocks · 52 decoration issues | `missing_elite.md`, `elite_gating.md`, `rank_decoration.md` |
| Q | build order | **0** prerequisite-order · 1012 build-palette-order violations across 841 buildables | `buildable_order.md` |
| D | duplicate keys | **6 D1 dropped inherits** · 439 D2 merged duplicates | `duplicate_keys.md` |

## Green — and must stay green

`empty_warhead` **0** of 2760 weapons (the boot-NRE class) · dangling weapon refs **0** ·
dangling inherit targets **0** · cross-faction concrete inherits **0** · rename-broken sprite
refs **0** · missing voxels **0** · TS death-palette **0** · D2k rank decorations **0** ·
promotion wiring clean · `MinRange` clean · duplicate uniquely-resolved traits clean ·
armor-plating invariants clean · plating exclusivity clean · physical-state warheads PASS ·
cross-document consistency 73/0 · display text 0 active findings ·
**documentation structure 0** (`doc_health.md`, D1–D8) · **balance-ledger drift 0** ·
**doc claims 19 of 19 match** · **generator sync drift 0** (136 shared templates, no-op
regenerate).

## Red right now

| check | state | what to do |
|---|---|---|
| **level ladder** | **WARN — 9 broken, at ratchet 9** (7 inverted, 2 flat) | no longer failing: `a9f31258` fixed `Demolition`. Still blocked on a maintainer ruling. Full measured table + the diagnosis: [`../design/ROADMAP.md`](../design/ROADMAP.md) "BROKEN LADDERS". These are balance numbers: pipeline only, and **never raise the ratchet**. |
| duplicate keys D1 | 6 dropped inherits | each one silently drops a template — same family as the `Parent type X was already inherited` boot crash |
| warhead-split ratchet | 921 vs baseline 921 | pre-existing W24 debt, not a regression; lower the baseline as W24 lands |

Cleared since the last edition of this page: **doc claims** (was 4 of 19 drifted, now 19 of 19
matching) and **generator sync** (was non-zero, now 0).

## Programme-scale debt

Sequenced on the board, not loose bugs. Status and ownership:
[`../design/BALANCE_PROGRAM_PLAN.md`](../design/BALANCE_PROGRAM_PLAN.md); the order is fixed by
its §0a.

| id | debt | measured |
|---|---|--:|
| W24 | directly fired weapons carrying more than one damage main | **494** |
| W23 | fired weapons reaching a `^Warhead_*` family | **1231** |
| W23 | direct inheritors of the legacy weapon templates | **1162** |
| W26 | live `DamageMultiplier` declarations | **353** |
| W11 | class anchors the maintainer has signed off | **0** — so no price is final |

All five are pinned in [`doc_claims.yaml`](doc_claims.yaml) and re-measured on every suite run,
so they cannot rot in prose again.

## Recommended fix order

1. **One clean suite run on a complete tree** — cheapest, and until `latest/` stops mixing two
   environments no count on this page can be fully trusted.
2. **The 9 broken level ladders** — a heavier level dealing less damage than a lighter one is
   player-visible nonsense. Back at the ratchet rather than over it, so it no longer fails the
   suite, but nothing about the nine has been ruled on.
3. **B2b duplicate inherit paths / D1 dropped inherits** — the class that produces
   `Parent type X was already inherited` boot crashes and silently-dropped templates. Only the
   boot and `audit_duplicate_inherits` can see it.
4. **G1 garrison weapons (0)**, **B6 missing images (0)**, **B12 fluent (0)**,
   and **B13 basebuilder crate coverage (29/29)** — small, bounded, player-visible.
5. **B1 cross-faction leaks (435 L1)** — the count grew because the audit's faction coverage
   grew, not only because the tree got worse. Triage before treating it as 435 bugs.
6. **B3/B4 upgrade direction and coverage**, plus transcribing the remaining 568
   `upgrades_intent.yaml` entries so the audit can tell an intended drawback from a bug.
7. **B10/B11 hygiene** — orphan purge, per-directory WAV normalisation. Good batch work.
8. **R2 stacked multipliers (790)** — folds into W26; do not touch it separately.

---

## Standing incident notes

Closed, but each is a bug class the ordinary gates cannot see.

### Empty warhead type = boot NRE (2026-08-04, CLOSED)

A `Warhead@X:` line with **no type value** parses to `null`; `WeaponInfo.LoadWarheads` calls
`Game.CreateObject<IWarhead>(null + "Warhead")`, that resolves to the abstract `Warhead` base
class, and `ObjectCreator.CreateBasic` throws before the main menu. It happens for **every**
top-level weapon node in the resolved ruleset, including unused `^templates`.
**`utility --check-yaml` does not catch this class.** Guard:
`python tools/audit/find_empty_warhead.py`. Run it after any bulk warhead edit.

### Conditional multipliers ignore `Prerequisites:` (2026-08-04, CLOSED)

Every `ConditionalTrait`-based multiplier (`FirepowerMultiplier`, `DamageMultiplier`,
`SpeedMultiplier`, …) has **no `Prerequisites` field**. A `Prerequisites:` line inside such a
block is silently ignored by the loader, making the multiplier **permanently active**. Found via
the War Economy speed bug, then swept mod-wide: 4 fixed, 0 remaining.
`ProductionCostMultiplier` / `ProductionTimeMultiplier` legitimately support it.

### Superweapon documentation audit (2026-07-25, CLOSED)

Every superweapon/support-power trait cross-referenced against `FACTIONS.md`: 14 findings, all
documentation discrepancies, all fixed. The one substantive finding stands: **Harkonnen Palace**
carries `^PrimarySuperweapon` + `SupportPowerChargeBar` but **no power trait** — the Death Hand
Missile is unimplemented (parked faction, not a regression). Superweapons also exist in the WIP
factions (Warzone 2100, Worms, Win98, Warcraft 1, WH40K); document them in `FACTIONS.md` only
when those factions go active.

⚠ The raw cross-reference was written to `latest/superweapon_audit.yaml` and **no longer
exists**: `run_all.sh` regenerates `latest/` wholesale. Put one-off artifacts anywhere else.

### TD GDI release regression (2026-07-17, CLOSED)

See [`INCIDENT_TD_GDI_RELEASE_REGRESSION.md`](INCIDENT_TD_GDI_RELEASE_REGRESSION.md).

### The 2026-07-08 baseline audit

The original long-form findings (the B1–B12 taxonomy, per-class tables) are archived at
[`../history/audits/BASELINE_FINDINGS.md`](../history/audits/BASELINE_FINDINGS.md) and
[`../history/MASTER_REPORT_2026-07-08.md`](../history/MASTER_REPORT_2026-07-08.md). Their file
paths predate the ContentPack restructure and their counts predate everything above — read them
for the taxonomy, never for numbers.
