# BALANCE PIPELINE — the mega plan (v2, 2026-07-18)

_Balance changes become MECHANICAL. No agent (or human) can silently
drift the game's stats, because the pipeline — not discipline, not
document-reading — enforces consistency._

v2 incorporates the maintainer's refinements (2026-07-18): the ledger
holds RAW yaml stats only (no derived values), the workbook consumes
raw stats directly, Range is solved from Cost in-sheet, and the
Formula-v2 per-unit-type program (DESIGN §12 second iteration) rides
the same pipeline.

## 0. The core loop (maintainer's target workflow)

**One command runs the verifying half of this loop in order:**

```sh
python tools/balance/run_pipeline.py              # verify — writes nothing
python tools/balance/run_pipeline.py --extract    # + step 1, refresh the ledgers
python tools/balance/run_pipeline.py --workbook   # + step 3, rebuild the workbooks
python tools/balance/run_pipeline.py --dry-run    # print the plan, run nothing
```

It executes steps 1, 3, 7 and 8 plus the structural gates, reports each stage's real
exit code, and **stops at step 6**. It cannot apply: there is no flag that reaches
`--confirm`, because an approval gate a tool can open by itself is not a gate. When the
verify stage is clean it prints the command for the maintainer to type.

Steps 2, 4 and 6 are human by definition — a balance decision is not a transformation —
and the runner lists them as such instead of skipping them quietly.

**The compiler property is measured, not assumed:**

```sh
python tools/balance/check_determinism.py                  # all ledgers
python tools/balance/check_determinism.py --faction d2k_ordos
python tools/balance/run_pipeline.py --determinism         # as a pipeline stage
```

It extracts twice in **separate processes** under different `PYTHONHASHSEED` and `TZ`,
builds the ledgers in memory, and compares every artifact byte for byte. Separate
processes are the point: inside one interpreter the hash seed is fixed, so set and dict
iteration order is stable by accident and an ordering leak stays invisible.

Nothing is written under `docs/balance/` — a tool that verifies the ledgers must never
be able to be the thing that moved them. `serialize()` already writes `sort_keys=True`,
so mapping order is safe; what this catches is a **list** built by iterating a set,
plus timestamps, timezone-dependent values and absolute paths reaching an artifact.

```
1. pull    yaml ──► JSON ledger          python tools/balance/extract_stats.py
2. edit    change values in the ledger (or in the generated sheet)
3. sheet   JSON ──► cameo_balance_by_faction.xlsx + cameo_balance_by_type.xlsx
                                         python tools/balance/build_workbook.py
4. tune    set Cost, the sheet solves Range (or check O/P/Q deltas)
5. import  xlsx ──► JSON                 python tools/balance/import_workbook.py --workbook faction|type
6. push    JSON ──► yaml                 python tools/balance/apply_balance.py --confirm
7. verify  drift audit: yaml ≡ ledger    python tools/balance/extract_stats.py --check
8. verify  multiplier audit: all `*Multiplier Modifier` values are integer percentages    python tools/audit/audit_multiplier_modifiers.py
9. decode  audit reports (if UTF-16)     — no longer needed; `run_all.sh` forces UTF-8
```

`cameo_balance_v2.xlsx` is the frozen pre-split prototype. It remains tracked
for historical comparison, but the builder and importer no longer read or write
it; only the faction/type workbooks above are active.

Class rebalances add two extra proposal steps before the normal push:

```
A. propose  class report (markdown)    python tools/balance/propose_class_rebalance.py --class <scout|closecombat|special_forces>
B. patch    ledger from reports        python tools/balance/_patch_ledgers_from_reports.py
   then run steps 3–8 above.
```

## 1. ARCHITECTURE CORRECTION (the honest-opinion part, agreed with maintainer intent)

"All 4 documents always mirrored and all writable" is the one part
that cannot work as stated — four independently-writable copies of the
same numbers is how drift is CREATED, not prevented. The goal (never
manually checking mirrors) is kept, but through two rules:

- **Single writer at any moment.** ⚠ **PROPOSED, NEVER BUILT.** The v2 plan called for
  a state file (`docs/balance/.session`) recording which representation is "open"
  (yaml | ledger | sheet), so a command run against a stale state would abort. No such
  file exists and no tool reads one — this paragraph described it in the present tense
  for long enough that it read as shipped. What actually enforces the invariant is the
  weaker but real pair below: one direction per command, and the drift audit catching
  disagreement after the fact rather than preventing it during the write.
- **The workbook is a WORKBENCH, not a source.** xlsx is binary —
  concurrent agents + git = unmergeable conflicts. The committed
  truths are exactly two: yaml (runtime) and the JSON ledger (balance).
  The sheet is regenerated on demand from the ledger and read back
  through a validating import; a lost sheet costs one command.
- The **drift audit** re-extracts yaml and diffs against the ledger on
  every run_all: any hand-edited stat = red finding with file + line.
  THIS is the "always mirrored without me checking" guarantee.

## 2. Ledger: RAW STATS ONLY (maintainer order — no derived values)

No DPS, no combined Damage, no effective-anything in the JSON. Every
number appears exactly as the yaml states it, with provenance:

> **SETTLED 2026-08-11 (W3).** The law briefly broke: `c9a09dc91` put five DERIVED
> fields in every ledger row, and a derived field moves when the **formula** moves,
> with no yaml change at all — correcting the metric's scatter model rewrote **4 136
> ledger lines while `mods/` was untouched**, i.e. model noise inside the very artifact
> whose job is to prove yaml ↔ ledger equality.
>
> The fields now live in a second tree, written by the **same** `extract_stats.py` run
> off the same resolve, so the two can never desync:
>
> | tree | contents | a diff means |
> |---|---|---|
> | `docs/balance/<faction>.json` | raw stats + provenance | **the game changed** — yaml was edited |
> | `docs/balance/derived/<faction>.json` | scalable `k_flat`, measured `k`, standalone percentage floor, folded rounding residual, `effective_per_shot`, full-cycle `eff_reload` / `effective_dps`, and spatial diagnostics | **the model changed** — a tool was edited |
> | `docs/balance/derived/_model.json` | the constants every derived number depends on (`SWARM_W`, `BLOB_UPTIME`, `DENSITY`, `ENGAGEMENT`, `reference_hp`, the armor census …) | the model was **retuned** |
>
> Each diff now answers exactly one question. `audit_balance_drift` reads only the raw
> tree (`extract_stats.build_ledgers()` returns raw by construction, so it cannot start
> diffing model output by accident); `extract_stats.py --check` verifies both and labels
> the finding `DRIFT (raw)` or `DRIFT (model)`. The derived rows repeat only `slot` and
> `weapon` as join keys — never a raw stat, so there is still exactly one copy of every
> number. Spec: [`EFFECTIVE_DAMAGE.md`](EFFECTIVE_DAMAGE.md).
>
> ⚠ Nothing consumes the derived tree yet — it is a read-only sidecar. `build_workbook.py`
> never read the old in-ledger fields either. Wiring K into pricing is **W11**, behind a
> flag and with a maintainer sign-off; do not let `apply_balance` write `Damage` from a
> derived number before then.

```json
{
  "schema": 2,
  "faction": "tkm",
  "pack": "ContentPacks/RedAlert2Mod/TKM",
  "sections": {
    "vehicles": {
      "tkm_abrams": {
        "name": "Abrams",
        "cost":  {"v": 1500,  "src": "yaml/vehicles.yaml#Valued.Cost"},
        "hp":    {"v": 125000,"src": "yaml/vehicles.yaml#Health.HP"},
        "speed": {"v": 80,    "src": "yaml/vehicles.yaml#Mobile.Speed"},
        "armor": {"v": "Heavy","src": "yaml/vehicles.yaml#Armor.Type"},
        "armaments": [
          {"slot": "Armament@PRIMARY", "weapon": "tkm120mm",
           "requires": null,
           "stats": {
             "damage":      {"v": 16000, "src": "yaml/weapons.yaml#tkm120mm.Warhead@...Damage"},
             "reload_delay":{"v": 65,    "src": "yaml/weapons.yaml#tkm120mm.ReloadDelay"},
             "burst":       {"v": 1,     "src": "..."},
             "burst_delays":{"v": null,  "src": "..."},
             "range":       {"v": 6500,  "src": "yaml/weapons.yaml#tkm120mm.Range"},
             "spread":      {"v": 426,   "src": "..."},
             "versus_template": "^MediumCannon"
           }}
        ],
        "design": {
          "unit_class": 1.0, "special": 1.0, "weapon_class": 1.0,
          "tech_tier": 1.0, "class_anchor": "mbt"
        },
        "prerequisites": ["~tkm_warfactory"], "build_limit": null
      }
    }
  }
}
```

- `design.*` fields are judgment inputs (they never exist in yaml);
  they seed from the legacy sheet once (Phase 3) and live here after.
- Range stays in **raw wdist** (5000, not 5.0) — DESIGN §12 note; the
  sheet divides by 1000 in a helper column, the ledger never does.
- Multi-armament units keep EVERY armament with its condition
  (`requires`) — the old single-Damage flattening is retired; which
  armaments count toward pricing is a design flag per armament
  (default: unconditional + primary-upgrade ones).
- **Multi-warhead damage convention.** Cameo weapons stack several
  offensive `Warhead@X: SpreadDamage` nodes (one per inherited weapon-class
  template); the engine detonates ALL of them, so the effective per-shot
  damage is the SUM (`formula.spread_damage_sum`), never the max. The
  workbook's **Damage cell is that per-shot TOTAL** — the same quantity
  pricing/DPS use — so the sheet and the price never disagree. Editing it
  writes per-warhead Damage through the ONE canonical reducer
  `formula.distribute_damage`, which applies the fixed DESIGN.md law:
  **every main class warhead gets the IDENTICAL value `total ÷ N` snapped
  to the 100-damage grid** ("all class warheads carry the identical
  value" — never proportional, never off-grid), `*FriendlyFire` and
  `*ExtraDamage` twins = **50%** of the main. Standalone `*Percentage`
  companions track **0.01% per 100 flat Damage** in their own denominator;
  folded `PercentageScale` damage derives from the main Damage. The calculator mirrors
  the Cameo runtime: both positional and direct-Actor `AreaDamage` impacts apply the
  folded hit exactly once, with wide intermediate arithmetic and checked final results.
  `*ExtraDamage` (the energy-weapon shield/AoE-compensation chip) is
  always 50% of the main but is **excluded from the damage total**.
  Fine-tuning is done on the 100-Damage grid or with reload timing;
  unconditional actor `FirepowerMultiplier` is retired as a tuning knob. A single number can therefore never be
  broadcast identically onto every warhead (the 2026-07-22 over-damage
  regression, commit `04de392b3`). `audit_warhead_split` fails the suite if
  that fingerprint ever reappears.
- All derived quantities (DPS, effective reload, price) exist ONLY as
  formula cells in the sheet and as `formula.py` functions — computed,
  never stored.

## 3. Workbook v2 format (raw stats in, formulas visible)

Per-faction tabs (CABAL-tab lineage), one UNIT row followed by one
indented WEAPON row per armament (mirroring yaml structure):

| col | content | kind |
|---|---|---|
| A–C | Mod, Actor id, Name | identity (locked) |
| D | Class | design input |
| E–G | HP, Speed, Armor | raw values; Armor is locked |
| H–J | TechTier, UnitClass, Special | design inputs |
| K | FirepowerMultiplier | compatibility value (locked; retired as a tuning input) |
| L–Q (weapon rows) | Damage, Reload, Burst, BurstDel, Range(wd), WeapClass | raw + design inputs |
| R | EffReload `= Reload + sum(all Burst-1 gaps)`; one delay repeats, blank uses engine default 5 | helper formula |
| S | DPS `= Damage*Burst/EffReload*FirepowerMultiplier` (summed to the unit row; WeapClass is design-only) | helper formula |
| T–V | O, P, Q estimators (burst-aware, from raw cells) | formula |
| W | Price `=(O+P+Q)/3` — Formula v2 swaps in the class-anchor form | formula |
| X | Cost (actual, from ledger) | raw input |
| Y–Z | Δ = Price − Cost; absolute Δ% with traffic-light formatting | formula |
| AA | **Range-solver**: Range required for Price = Cost (closed form — the estimator mean is linear in Range, so the legacy inverse survives the raw-stat refactor) | formula |
| AB | WeaponTypes | resolved classification (locked) |

- Helper columns instead of monster formulas: every intermediate is a
  visible, debuggable cell (maintainer's "all stats included" rule).
- Constants tab: armor ladder, weapon-class tables, class-anchor
  baselines (Formula v2), rounding conventions. All formulas reference
  it by named range — tune the law in ONE place.
- Missing Reload, Burst, and Range fields display their engine defaults (1, 1,
  and 0). Editing one creates the top-level weapon field; an unchanged default
  remains absent. Blank BurstDel means the engine's five-tick default.
- Cells stay locked when there is no safe backing field to edit, such as a
  synthetic defense Speed or a weapon row with no main damage warhead.
- `formula.py` implements the identical math; equivalence-tested
  against the sheet on every build (legacy workbook's own computed
  values are the ground truth for the overlap set).

## 4. Sync commands (tools/balance/)

| command | direction | gate / notes |
|---|---|---|
| `python tools/balance/extract_stats.py [--faction X]` | yaml → ledger | overwrites `docs/balance/*.json`; run `--check` to detect drift |
| `python tools/balance/build_workbook.py` | ledger → `docs/design/cameo_balance_*.xlsx` | tracked generated workbenches; regenerate and review the binary diff |
| `python tools/balance/import_workbook.py` | xlsx → ledger | validates and prints every input-cell diff |
| `python tools/balance/apply_balance.py [--faction X]` | ledger → yaml (dry-run) | prints diff; **does not write** |
| `python tools/balance/apply_balance.py --confirm [--faction X]` | ledger → yaml | **maintainer order only**; auto-runs `extract_stats.py` + `tools/audit/audit_multiplier_modifiers.py`; full `run_all.sh` + boot gate before commit |
| `python tools/balance/propose_class_rebalance.py --class <cls>` | ledger → `docs/balance/proposal_<cls>_infantry.md` | generates a markdown report; does not touch yaml/ledger |
| `python tools/balance/_patch_ledgers_from_reports.py` | `proposal_*.md` → ledger | patches `docs/balance/*.json` from the three class reports |

Round-trip invariants tested in CI-style: `extract_stats.py` ∘ `apply_balance.py --confirm` = identity, `build_workbook.py` ∘ `import_workbook.py` = identity.
Each generated workbook also carries a SHA-256 fingerprint of the builder,
formula/tier helpers, active ordering files, and raw/derived ledgers. `--check`
rejects a workbook that predates any of those inputs; manual formula edits still
require the normal regeneration/review gate.

## 5. Formula v2 — per-unit-type baselines (DESIGN §12 second iteration)

Already designed in DESIGN §12 (looked up 2026-07-18): everything is
anchored on the **Naxis Tiger Tank** (100000 HP / 100 speed / 10000
damage / range 5000 / reload 50 → O=P=Q=Cost=800 exactly), which
breaks at the low end (no intercept) and forces conventions like
defenses-speed-100 and bombers-reload-250. The documented fix — now
implemented through the pipeline:

- **One baseline unit per unit class**, each with Tiger-style round
  numbers; price by normalized deviation from the class anchor:
  `Cost = Cost₀ × (O/O₀ + P/P₀ + Q/Q₀) / 3` (exact at each anchor).
- Class list & anchor candidates (maintainer confirms each):
  - `mbt` (exists): Naxis Tiger Tank, Cost₀ 800 — unchanged.
  - `fighter` (exists): port the current separate fighter formula
    into the registry unchanged, then re-express on raw stats.
  - `bomber` (NEW): replace the reload=250 convention with real
    ReloadDelay from raw stats; anchor = a maintainer-picked bomber.
  - `defense` (NEW): replace speed=100 convention with a defense term
    (footprint + power draw are the natural "mobility" substitutes);
    keep DESIGN's charge-delay −0.25 rule as a K modifier.
  - `infantry` classes (NEW): scout / basic / heavy / hero anchors —
    absorbs the UnitClass column per DESIGN §12.
  - later: naval, harvester/economy, epic/BuildLimit-1 units.
- Fitting workflow per class: maintainer names 3–5 units they consider
  correctly priced → `fit_anchor.py` does least-squares on the class
  coefficients → validation table across the whole class → maintainer
  signs → the class formula becomes law in the Constants tab and
  `formula.py`. One class at a time, sheet stays usable throughout
  (unfitted classes keep the Tiger formula until replaced).

## 5b. Class tuning knobs & the modifier normalization program (2026-07-18)

Survey result: 83 templates in defaults.yaml carry multiplier traits.
They split into three kinds with three different fates:

1. **Cross-cutting systems — KEEP, out of pipeline scope.** Veterancy
   ranks (^GainsExperience*), crate buffs, debuff mechanics
   (^TerrorDronable, ^SquidGrabbable), melee cooldowns, fire-actor
   rules. These are gameplay mechanics, not balance knobs.
2. **The sanctioned knob hierarchy — KEEP, becomes PIPELINE-OWNED.**
   `^GlobalBuffs` → per-class (`^InfantryBuffs`, `^VehicleBuffs`,
   `^TankBuffs`, `^AircraftBuffs`, `^DefenseBuffs`) → per-subclass
   (Scout/Grenadier/AntiTankAntiAir/Heavy/Melee/Sniper…Buff). This
   already-existing structure IS the maintainer's one-value correction
   system and it SURVIVES normalization:
   - knob values live in the ledger + Constants tab (`class_tuning`);
     `balance push` writes them into the defaults.yaml traits via
     provenance anchors like any other stat;
   - **pricing formulas become knob-aware**: the sheet computes
     EffDamage = Damage × ∏Firepower-knobs and EffHP = HP ÷
     ∏Damage-knobs along the Global→class→subclass chain, and O/P/Q
     consume the EFFECTIVE values — so while a knob ≠ 100 the prices
     stay honest and the Δ column shows the price consequence of the
     knob turn immediately (better than today, where a knob turn
     silently invalidates the sheet);
   - the one-value workflow is unchanged in feel: edit ONE Constants
     cell → push → the whole class shifts in game.
3. **Ad-hoc formula-gap patches — BAKE & DELETE via Formula v2.**
   Knobs that exist only to paper over the Tiger formula's low-end
   failure (the ScoutInfantry damage-reduction stopgap is DESIGN §12's
   own example) become redundant once per-class anchors price small
   units correctly — they are folded into raw stats and removed.

**The bake operation** (maintainer-ordered, per knob): fold an
accepted long-term knob into raw stats and reset it to 100 —
Firepower×0.9 becomes every class member's Damage ×0.9 (rounded per
conventions; clean), Damage-taken knobs become HP adjustments (CAVEAT:
subtly shifts self-heal/repair proportions — when equivalence is
imperfect the knob simply stays live; nothing forces a bake). Baking
keeps effective power constant, so costs do not move.

## 6. Phases (revised, in execution order)

| phase | deliverable | effort |
|---|---|---|
| 1 | Extractor: raw-stat ledger, multi-armament, provenance, deterministic; `balance check` mode | M |
| 2 | Workbook builder: raw columns + helpers + solver + locks + Constants; equivalence test vs formula.py | M |
| 3 | Legacy comparator: name→id map, seed `design.*` inputs from old sheet, discrepancy report, maintainer triage | M–L |
| 4 | Sync commands + session state + round-trip invariants + gated push | M |
| 5 | Formula v2 program: class registry, anchor fitting, per-class sign-off (mbt → fighter → bomber → defense → infantry → rest) | L (per-class S) |
| 6 | Enforcement: `balance check` in run_all, DESIGN/CLAUDE law update, retire audit_stat_formulas + audit_balance_sheet into the pipeline | S |

First customer: the SM full rebalance (ROADMAP P1b) runs on Phases
1–4 the moment they land.

## 7. Risks & mitigations (v2 delta)

- Multi-armament pricing is the hardest format problem (the old
  one-Damage flattening is why sheet and yaml drifted); the
  weapon-sub-row layout + per-armament pricing flags solve it
  explicitly rather than implicitly.
- Solving Range from Cost stays closed-form only while price is
  linear in Range; Formula-v2 class variants must preserve that (they
  do — Range appears linearly in O, P and Q alike). The solver cell
  is regenerated per class formula.
- Versus tables: mirrored into the ledger read-only (from the ~30
  weapon-class templates per DESIGN's weapon-construction law); the
  sheet's WeaponClass stays the design scalar. Formalizing versus
  into pricing is a Formula-v3 question, deliberately out of scope.
- The active xlsx workbenches are tracked generated artifacts; regenerate them
  from the ledger and review binary conflicts instead of treating them as sources.

## 8. HARDENING — deterministic, agent-independent, memory-free (2026-07-25)

Maintainer directive: the pipeline must **run identically no matter who starts it or which AI agent
is used**, be **absolutely stable**, and **never be disrupted by wrong memories.** The architecture
above already resists silent drift; this section closes the remaining gaps so the pipeline is truly
foolproof, and fixes the ORDER of operations. Reference data behind the anchor targets:
`BALANCE_SYNTHESIS.md` §12–§19.

### 8.1 The BASEBAND law — encode it, stop trusting it to discipline

The class **baseline** (100% cost) and **verifier** (250% cost = 2× HP + 2× DPS) bound a *band where
most units live*. Distribution is deliberately uneven:
- **Sweet spot 100%–250% cost** — ~**80% of all units**, skewed toward the **baseline (100%)**.
- **Hard caps 50%–400%** — only a few units below baseline or above the verifier.
- **★ The formula BREAKS DOWN below ~75% cost** — units become too weak for their price (a
  600¢ tank vs an 800¢ base; the Naxis Rifle Recruit at 75¢). **75% is the practical FLOOR**, not 50.
- **★ Price ⇒ tech-tier GATE mapping (maintainer 2026-07-25).** Cost above the baseline must be
  *earned* by a gate (the 2.5× verifier already is — e.g. the Forgotten Soldier is an upgrade-unlock
  on Tier-2/Radar while its baseline is a plain Tier-1 unit). The rule:
  - **100%–200% cost** — allowed **ungated** (plain Tier-1, no promotion/upgrade).
  - **200%–300% cost** — MUST have **≥1 gate**: a promotion, an upgrade-unlock, **or** Tier 3+.
  - **> 300% cost** — **end-game**: MUST be gated by a promotion, upgrade-unlock, **or** the latest
    tech tier (3+). (Power is allowed to scale with tier; the gate scales with the price.)
- **→ NEW VALIDATOR (`tools/balance/check_band.py`):** for every unit, compute its class-formula
  price ratio price/cost0. **Findings:** priced **< 75%** (breakdown risk); priced **> 200% while
  ungated** (plain Tier-1, no promotion/upgrade → must gate); priced **> 300%** not end-game-gated.
  Report the **100–200% ungated occupancy** (target ≥ 80%). Gate detection = `design.tech_tier ≥ 3`,
  a promotion/upgrade token in `prerequisites`, or `build_limit`/hero template. Wire into
  `run_all.sh`. This turns the baseband + tier-gate from remembered rules into an **enforced gate**.

### 8.2 Determinism & agent-independence (the anti-"wrong memory" rules)

1. **Three authorities, and ONLY three:** `formula.py` (the math), `class_anchors.json` (the
   numbers), and this doc + `DESIGN.md` (the laws). **Memories are hints, never authority.** If a
   memory and these disagree, these win — always verify against them before acting.
2. **Every command is idempotent + guarded.** `extract_stats.py --check`, the single-writer
   `.session` state, and the drift audit mean a re-run or a wrong-state run **aborts with
   instructions** rather than half-applying. Same inputs → same outputs, every agent, every time.
3. **The guardrails catch mistakes regardless of belief:** drift audit (yaml≡ledger) + the new band
   validator (§8.1) + anchor-completeness (§8.5) + the boot gate. An agent acting on a wrong memory
   **cannot land** an inconsistent state silently — a guard goes red.
4. **No step requires judgment that isn't recorded.** Anchor picks, `design.*` inputs, and sign-offs
   live in the ledger/anchors JSON, not in an agent's head — so the next agent reproduces them.

### 8.3 ORDER OF OPERATIONS (maintainer law) — base units + defenses FIRST, upgrades LAST

**Upgrades are priced ON TOP of finished unit stats.** If a unit's stats change, every upgrade's
effect (armor mult, regen, weapon swap) changes too — so pricing upgrades before units are final
means re-doing them. Therefore the strict sequence:

1. **Rebalance all BASE units + DEFENSES** (this whole §8.4 anchor pass) → validate band → apply →
   boot-gate → commit.
2. **THEN** price upgrades on the finished baselines (incl. the defensive-upgrade-stacking fix,
   `BALANCE_SYNTHESIS.md` §18.2 — the actual "unkillable" cause). **Do not start upgrades early.**

### 8.4 Anchor-finalization sequence (grounded in §12–§19, one class at a time)

Most `class_anchors.json` entries are still `signed_off: false`. Finalize them using the synthesis
data, each via `fit_class.py` + a maintainer-confirmed anchor unit + sign-off:

- **Infantry anchors → keep** (§19: infantry are on-scale, ~1× rifle). Confirm + sign the existing
  provisional infantry anchors.
- **Vehicle / aircraft anchors → REVIEW, don't presume (maintainer 2026-07-25).** §19 shows Cameo
  tanks ~2× / aircraft ~2.5× the RA2 *reference* ratio, BUT the maintainer judges the **baselines
  fair** (scout 20k/100¢ vs Tiger 100k/800¢ = 5× is intended). So **do NOT cut the class baselines**;
  the reference is context, not a target. The real suspect is **specific later-game units scaling too
  much with HP** — handle per-case, **test in-game**, keep the Tiger MBT anchor (100k, cost0 800)
  unless testing says otherwise. (`BALANCE_SYNTHESIS.md` §19.3.)
- **Defenses → roughly keep** (§19: near reference) — but account for the §7 building damage-exemption
  so effective durability isn't double-counted.
- **Price default = ORIGINAL price** (`BALANCE_SYNTHESIS.md` §20): each unit defaults to its
  source-game cost; deviate only for real power enhancements or faction economy-identity, always
  in-band. Uniqueness rides the **stat-mix** (formula-stable), not the role/silhouette.
- **Epic / hero → not band-limited** (`BuildLimit: 1`, §18.1) — priced separately, deliberately extreme.
- Each class: `fit_class.py --class X --anchor <unit>` → review `formula_v2_X.md` + `check_band.py`
  → maintainer sets `signed_off: true`. **One class at a time**; unfitted classes keep the Tiger
  formula meanwhile. Suggested order: **mbt → high-tech → light/TD/AA/arty tanks → aircraft →
  defenses → infantry confirmations.**

### 8.4b Fixed pricing rules that BYPASS the class formula (maintainer laws)

Two unit kinds are NOT priced by the class-baseline formula:
- **Support** (medics / mechanics / casters / mind-control / spies) — **fully EXEMPT.** No consistent
  or no damage ⇒ nothing to compute. Never anchor/verify/band-check. The one class outside balancing.
- **Cargo vehicles + aircraft** (any actor with a `Cargo:` trait — APC, transport, Battle Fortress) —
  priced at the **SUM of the infantry carried at full capacity**, *even if unarmed.* A FIXED rule:
  `cost target = Σ(passenger costs at Cargo.MaxWeight)`. `check_band` must detect `Cargo:` and check
  the passenger-sum, not the class formula. (Verified: Battle Fortress MaxWeight 6 @ 4000¢.) So an
  unarmed transport is *balanced* (passenger-sum), unlike exempt support.

### 8.5 New guards to build (wire all into `run_all.sh`)

- **`check_band.py`** — the §8.1 baseband validator.
- **anchor-completeness** — fail if any ledger unit tagged `design.class_anchor = X` belongs to a
  class whose anchor is missing or `signed_off: false` once that class is declared "done" (prevents
  half-finalized classes shipping).
- **new-template registration** — the 4 new vehicle templates (`^LightTank`, `^TankDestroyer`,
  `^AntiAirTank`, `^ArtilleryTank`) + the `^SupportVehicle` redefinition must exist in
  `defaults.yaml` before their class anchors can sign off (boot-gated yaml task).

### 8.6 The one-command runbook (what "anyone can run it" means)

The end-state: a single guarded entry (e.g. `balance` wrapper) runs
`extract_stats --check → check_band → audit_balance_drift → (report)` read-only for a **status**, and
the gated `apply_balance --confirm` for a **write** — both fully deterministic, both refusing to
proceed on a stale `.session` or a red guard. No memory, no tribal knowledge, no per-agent variance.
