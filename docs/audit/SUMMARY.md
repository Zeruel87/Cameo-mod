# Audit summary — current known-issue state

_One page. Live reports: [`latest/`](latest/) · comparison snapshots: [`baseline/`](baseline/) ·
faction map: [`../factions/MATRIX.md`](../factions/MATRIX.md)._

**Evidence date: 2026-09-24**, from `bash tools/audit/run_all.sh` on a complete tree (engine
present) at the post-merge-wave master. `level_ladder` was RETIRED on 2026-08-23 — it enforced a
damage-monotonic rule no law states — and replaced by `heaviness_bell`.
Recurring code-health audits and their cadence: [`PERIODIC.md`](PERIODIC.md) +
[`periodic.json`](periodic.json).

✅ The two-environment mixture is RESOLVED: `latest/` was regenerated whole on a complete tree
(2026-09-24) and this page was rewritten from those reports in the same pass. `run_all` still
refuses to write `latest/` from an incomplete tree (it diverts to `docs/audit/degraded/`), so
keep it that way — never commit a degraded run as `latest/`.

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
that their consumed conditions exactly match the synchronized
`BotPersonalityController`. Personality-specific differences are restricted to an explicit
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
Without an active composition, the single shared unit builder's `UnitsToBuild`
table remains the fallback. The pilot compositions are limited to TD vehicle queues and are
gated by their respective tech prerequisites; broader composition coverage is
still a follow-up. Explicit unit requests continue to bypass composition
shares.

## Counts by bug class

| class | what | count | report |
|---|---|--:|---|
| **B8** | crash-class content | **0** | — |
| B1 | cross-faction leaks | 6 L1 · 0 L3 · 91 shared | `faction_leaks.md` |
| B2 | illegal inherits | 276 V1 · **0** V2 · **0** V3 dangling · 2094 V4 depth>3 · 102 V5 | `inherits.md` |
| B2b | duplicate inherit paths | 1990 definitions reach a parent by >1 path | `duplicate_inherits.md` |
| B3 | upgrade direction | 624 items · **0** inverted · 1 deferred · 10 dead · 20 dead tokens · 587 without an intent entry | `upgrades.md` |
| B4 | upgrade coverage | 24 tagged upgrades · 21 uncovered unit slots | `upgrade_coverage.md` |
| B5 | AI wiring | 1867 refs · **0** defined nowhere · **0** unloaded · 2 unwired pool factions | `ai.md` |
| B6 | art/sequence refs | **0** missing images · **0** missing sequences · 582 unreferenced images (of 3304) | `sequences.md` |
| B7 | metadata rot | 38 duplicate-tooltip groups · **0** missing tooltip names | `metadata.md` |
| B9 | numeric drift | 165 robust outliers · **0** bounds over the 5×5 max | `outliers.md` |
| B10 | dead content | 395 orphan weapons · **0** dangling refs · 18 dead conditions | `orphans.md` |
| B11 | asset norms | 127 / 1942 PNGs over budget · 3628 / 8540 WAVs off-norm | `assets.md` |
| B12 | localization | **0** unresolved fluent refs · 534 orphaned `actor-*` messages | `fluent.md` |
| B13 | basebuilder crate coverage | **31/31** factions covered | `basebuilder_crates.md` |
| R2 | stacked multipliers | 823 units over the 2.0× power budget | `power_budget.md` |
| W | weapon uniqueness (§10) | 37 same-faction · 31 cross-faction · 89 carrier-only | `weapon_uniqueness.md` |
| G | garrison weapons (§11) | **7 G1** · 0 G2 · 0 G3 · **1 G4** | `garrison_weapons.md` |
| F | house stat formulas | 685 violations across 2009 roster actors | `stat_formulas.md` |
| E | elite / rank wiring | 197 missing elite armaments · 21 ungated ELITE blocks · 60 decoration issues | `missing_elite.md`, `elite_gating.md`, `rank_decoration.md` |
| Q | build order | **1** prerequisite-order · 985 build-palette-order violations across 910 buildables | `buildable_order.md` |
| D | duplicate keys | **0 D1 ambiguous labels** · 158 D2 merged duplicates (was 4,965; residual = `Inherits`-separated generations + value-differing overrides) | `duplicate_keys.md` |

## Green — and must stay green

`empty_warhead` **0** across 2995 nodes (the boot-NRE class) · dangling weapon refs **0** ·
dangling inherit targets **0** · cross-faction concrete inherits **0** · rename-broken sprite
refs **0** · missing voxels **0** · TS death-palette **0** · D2k rank decorations **0** ·
promotion wiring clean · duplicate uniquely-resolved traits clean ·
armor-plating invariants clean · plating exclusivity clean · physical-state warheads PASS ·
cross-document consistency 73/0 · display text 0 active findings ·
**documentation structure 0** (`doc_health.md`, D1–D8) ·
**generator sync drift 41** of 158 shared templates — improved from 184 after the W7 re-syncs;
the remaining 41 `^Warhead_*` templates are generator-unemitted (mostly `*_Flat` and bespoke
bespoke-family blocks), owned by the generator lane.

## Red right now

| check | state | what to do |
|---|---|---|
| duplicate keys D1 | **0 ambiguous labels** (was 7 — cleared by the merge wave) | keep watching: this is the `Parent type X was already inherited` boot-crash family |
| warhead-split ratchet | 14 vs baseline 69 | pre-existing W24 debt, much reduced (was 921); the 14 remaining are listed in `warhead_split.md`. Lower the baseline as W24 lands — never raise it. |
| **MinRange** | **7 mismatches** | `min_range.md` — weapons whose `MinRange` ≠ round(Range/5) step 5 (e.g. `ra1_allies_alliedartillery_155mm` 2670 vs 2365). This row was wrongly listed under Green in the previous edition. |
| **B13 crate coverage** | **fixed 2026-09-26 — 31/31** | `basebuilder_crates.md` — corrino `GiveBaseBuilderCrateAction` added in `rules/misc.yaml`. |
| **G1 garrison weapons** | **7 missing** | `garrison_weapons.md` — armed garrison-capable infantry without a garrison weapon (e.g. `ra1_soviets_dog`). Was 0 in the previous edition. |
| **G4 garrison acceptance** | **1 non-garrisonable** | `garrison_weapons.md` — ruling 2026-09-26: ALL infantry can garrison (`Garrisoner.GarrisonType: Infantry` vs `Garrisonable.Types`). 9 infantry-queue defects fixed 2026-09-26 (trait added; ranged got `Armament@GARRISONED` mirrors; melee knight/ogre → exceptions). Class ruling 2026-09-26: "all infantry garrison" means units BUILT in the Infantry queue — 6 Vehicle-queue mechs exempted via `vehicle_queue` in `garrison_exceptions.yaml` (pulverizermecha, plasmastrider, megalodon, poseidontank, stalker, whiterabbit). Remaining: `cabal_ravager` — moves to the Infantry queue in Claude's armour PR and then garrisons. 9 pure aircraft excluded. |
| **Q prerequisite order** | **1 violation** | `buildable_order.md` — one buildable is gated by a prerequisite ordered after it. Was 0. |
| **balance-ledger drift** | **25 ledgers drifted** | `balance_drift.md` — yaml moved without re-extraction, or sanctioned applies missing their `extract_stats.py` follow-up. Was 0 — flagged to lane owners. |
| **doc claims** | **36 of 43 match — 7 MISMATCHED** | `doc_claims.md` — `shield_versus_mean`, `shield_hp_factor`, `shield_damage_share`, `percentage_denominator_unset`, `physical_state_fired_weapons`, `unconverted_template_inheritors`, `ledgers_drifted`. Several are pipeline-moved numbers needing re-pin, not bugs. |

Retired since the last edition: **level_ladder** (RETIRED 2026-08-23 — enforced a
damage-monotonic rule no law states; replaced by `heaviness_bell`). Its former WARN row is
removed; the nine measured anomalies remain documented in
[`../design/ROADMAP.md`](../design/ROADMAP.md) "BROKEN LADDERS" for the maintainer.

## Programme-scale debt

Sequenced on the board, not loose bugs. Status and ownership:
[`../design/BALANCE_PROGRAM_PLAN.md`](../design/BALANCE_PROGRAM_PLAN.md); the order is fixed by
its §0a.

| id | debt | measured |
|---|---|--:|
| W24 | directly fired weapons carrying more than one damage main | **14** (broadcast ratchet, `warhead_split.md`) |
| W23 | fired weapons reaching a `^Warhead_*` family | **1530** (`warhead_family_reach`) |
| W23 | direct inheritors of the legacy weapon templates | **385** (`unconverted_template_inheritors`) |
| W26 | live `DamageMultiplier` declarations | **326** (`live_damage_multipliers`) |
| W11 | class anchors the maintainer has signed off | **0** — so no price is final |

All five are pinned in [`doc_claims.yaml`](doc_claims.yaml) and re-measured on every suite run,
so they cannot rot in prose again.

## Recommended fix order

1. **B2b duplicate inherit paths (1,952)** — the diamond-path class; D1 ambiguous labels
   are at 0 as of 2026-09-26. The class produces `Parent type X was already inherited`
   boot crashes and silently-dropped templates. Only the boot and
   `audit_duplicate_inherits` can see it.
2. **G1 garrison weapons (7)**,
   **Q prerequisite order (1)**, **MinRange (7)** —
   small, bounded, player-visible. (B13 corrino crate: fixed 2026-09-26.)
3. **balance-ledger drift (25) + doc-claims re-pins (7)** — mechanical hygiene; each drifted
   ledger needs an `extract_stats.py` run from its owning lane.
4. **B1 cross-faction leaks (6 L1)** — attribution fixed 2026-09-26 (`audit_faction_leaks.py`
   aliased bare theme names only; pack owners arrive as `theme/subdir`). The old 433 were
   namespace artifacts; the 6 survivors are real and listed in `faction_leaks.md` — each is a
   per-lane intended-sharing decision (e.g. latinsyndicate building `naxis_*` units).
5. **B3/B4 upgrade direction and coverage**, plus transcribing the remaining 587
   `upgrades_intent.yaml` entries so the audit can tell an intended drawback from a bug.
6. **B10/B11 hygiene** — orphan purge, per-directory WAV normalisation. Good batch work.
7. **R2 stacked multipliers (823)** — folds into W26; do not touch it separately.

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
