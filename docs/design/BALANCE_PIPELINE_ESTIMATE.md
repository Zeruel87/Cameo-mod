# Balance Pipeline — full completion estimate (rebuilt 2026-08-07)

> Purpose: a category-by-category, step-by-step estimate of **everything left**
> to finish the Cameo balance program — the weapon 3-way split, the weapon
> foundation laws, the reference data-mining + synthesis, the class anchors,
> the Formula-V2 completion, and the per-faction apply. Supersedes the PERT
> table in `docs/history/handoffs/AI_HANDOFF_2026-08-05.md` §8 (which predates A1 being done and
> under-counted the reference-research and Formula-V2 categories).
>
> Method: **three-point PERT**. For each item, `O` = optimistic, `M` = most
> likely, `P` = pessimistic (hours of focused agent work). Expected
> `E = (O + 4M + P) / 6`; rough uncertainty `σ = (P − O) / 6`. A **session** =
> 5 h of focused agent work (the 4–6 h band from `ROADMAP.md`). These are
> engineer-estimate ranges, **not commitments**.

---

## 0. The two numbers that dominate everything

1. **Maintainer decision latency, not agent throughput, is the real critical
   path.** A large share of the work blocks on a human judgment call:
   `apply_balance --confirm` (required per faction), the vehicle anchor
   confirmation, per-weapon warhead-family/tier calls, faction-identity design,
   and the "is this a legitimate multi-warhead exception" list. Agent-hours are
   estimated below; **wall-clock is throttled by how fast those gates clear.**
2. **Parallelism cuts wall-clock roughly in half.** The weapon-split layer, the
   reference data-mining, and the Formula-V2 code work are largely independent
   and can run on separate agents/worktrees. The serial agent-effort total is
   ~**510 h**; with 2–3 agents on non-dependent tracks the wall-clock critical
   path is ~**250–300 h**.

---

## 1. Current state (what is already DONE — subtracted from the estimate)

- ✅ **Engine warheads**: `AreaDamageWarhead` + `AreaDamagePercentageWarhead`
  built + deployed; AtomicCore 75%-CY superweapon proven.
- ✅ **Universal AreaDamage conversion**: 559-weapon sweep + 54 shared
  `^Warhead_*` templates flipped to `AreaDamage` + baked universal FF (50/50).
- ✅ **A1 generator reconcile** (`48245737e`): `gen_weapon_template.py` emits
  `AreaDamage` + baked FF + `^Warhead_<Family>_<Level>` + `_Percentage`;
  `verify_generator_sync.py` proves **drift = 0** → regenerate is a verified
  no-op. Wired into `run_all.sh` (`gen_sync`).
- ✅ **Template libraries spliced + boot-gated**: 55 warhead, 25 projectile,
  45 effect families above the `DO NOT INHERIT` divider.
- ✅ **3-way split — effect-free clusters largely done**: single-inherit sweep,
  ~15 dual-inherit signature clusters, the 99-weapon single-cannon sweep, and
  the CABAL bespoke pilot. First effect-heavy cluster (`Grenade+LightFlame`)
  proven, de-risking flame/chemical.
- ✅ **Reference library — extraction DONE, synthesis NOT** (`ORIGINAL_UNIT_STATS.md`,
  `ORIGINAL_UNITS_RAW.md`, `FACTION_IDENTITY.md`, `RESEARCH_NOTES.md`,
  `BALANCE_SYNTHESIS.md`). Every peer mod is extracted — Mental Omega, DTA, Combined Arms,
  Shattered Paradise, **CnC Reloaded (324 rows)** and **Romanov's Vengeance (207 rows)**.
  Plus `class_anchors.json` (28 classes), infantry membership auto-classification.
  ⚠ *An earlier revision of this section said CnCR + RV "remain"; it contradicted PHASE R
  in the same file. Verified 2026-08-15 — both are in `ORIGINAL_UNITS_RAW.md`.*
- ✅ **Warhead corpus complete** — `docs/reference/versus_raw.json`, **2494 warhead-vs-armor
  profiles / 14 sources, 0 undecoded** (`extract_versus.py --summary`). This is the input
  to W13 and it is ready to use today.

**Remaining volume — RE-MEASURED 2026-08-15 against the LIVE resolved ruleset**
(the 2026-08-07 figures counted lines in FILES, including the ~30 weapon files that are
commented out in `mod.yaml` and load nothing — `shockwave`, `generals`, `darkreign`,
`wh40k`, `starwars` … Counting dead files overstates the work and hides which of it ships):

| measure | live value |
|---|--:|
| concrete weapons the engine loads | **2323** |
| …already on a `^Warhead_<Family>_<Level>` | **720 (31%)** |
| …still inheriting an OLD template | **1920 refs / 106 distinct templates** |
| …still declaring `Warhead@1Dam` locally | **271** |
| balance classes (`class_anchors.json`) | 28 — 23 complete, 4 missing a verifier |
| unit rows in Document 1 (RA2 lineage only) | 1021, **1022 `TODO` cells** = R4 is untouched |

Biggest remaining old templates: `^ShrapnelWeapon` 105 · `^Grenade` 100 · `^FlakWeapon` 97
· `^MediumMissile` 87 · `^MediumChemicalWeapon` 80 · `^TankDestroyerCannon` 78.

⚠ **Document 1 covers the RA2 lineage ONLY** (RA2, YR, MO, CnCR, RV). The TD/RA1/TS peers
(DTA, Combined Arms, Shattered Paradise) are extracted as per-game summary tables in
`ORIGINAL_UNIT_STATS.md` but were never run through the Document-1 generator, whose own
header says "First cut: RA2 family … Scales to all 11 sources by extending `SOURCES`".
Synthesising TD/TS/RA1 classes needs that extension first — it is a generator change, not
a new data pull.

---

## 2. Category-by-category estimate

### PHASE W — Weapon 3-way split (finish the structural retrofit)

The active work. Every weapon becomes `Inherits@wh(+@wh2) / @proj / @fx` with
`Damage` preserved verbatim; `resolve_weapon()` must be byte-identical
before/after except intended changes; `find_empty_warhead.py = 0`; boot-gate
per batch.

| # | Sub-task | Remaining | O | M | P | **E (h)** | Sessions | Depends | Risk |
|---|---|---|--:|--:|--:|--:|--:|---|---|
| W-A | Finish effect-free dual/single clusters | small tail | 2 | 4 | 8 | **4.3** | ~1 | — | low |
| W-B | Effect-heavy clusters (flame/chem/sonic/EMP) — generalize the `PhysicalState`/`GroundFire`-aware converter | ~115 chem + flame | 10 | 20 | 44 | **22.3** | 4–6 | W-A | med — merge-field crashes |
| W-C | Mixed 3+ / bespoke weapons — per-weapon warhead-family + tier judgment (CABAL/Dune/Pulverizer/Siege exceptions) | ~609 | 24 | 48 | 96 | **52.0** | 9–16 | W-B | **high — needs maintainer calls** |
| W-D | Intermediate bundle dissolution (`^RA2Chaingun`, `^TSMG`, `^SteelChaingun`…) | ~10 bundles | 6 | 12 | 24 | **13.0** | 2–3 | W-C | med |
| W-E | Retire `Warhead@1Dam` (per-unit tier/profile reassign) | 328 | 16 | 32 | 64 | **34.7** | 6–12 | W-C | **high — per-unit judgment** |
| W-F | Delete 30 orphaned old templates + `weapon_classes.yaml` rows | 30 | 2 | 4 | 8 | **4.3** | ~1 | W-D,W-E | low |
| W-G | Per-game/faction art templates (RA2 VLS, CABAL/Steel trails, flak/missile FX) | ~20–40 | 12 | 24 | 48 | **26.0** | 4–8 | W-A | low (additive) |
| | **Phase W subtotal** | | | | | **156.6** | **26–47** | | |

### PHASE A — Weapon foundation laws

| # | Sub-task | O | M | P | **E (h)** | Sessions | Depends | Notes |
|---|---|--:|--:|--:|--:|--:|---|---|
| A2 | Cannon AP/HE rebuild + unit↔weapon binding (`TankDestroyerCannon→CannonAP_Light`, split cannons) | 4 | 8 | 16 | **8.7** | 1–2 | A1✅ | unblocks vehicle DPS |
| A4 | Tuning laws: **MissileAA spread → 100/150/200** (decided), energy `ExtraDamage` chips, global spread reduction + `Damage×Spread≈const` pricing term | 6 | 12 | 24 | **13.0** | 2–3 | A1✅ | do via generator, then regen |
| | **Phase A subtotal** | | | | **21.7** | **3–5** | | |

### PHASE R — Reference research & synthesis (data-mining)

**Data-mining is DONE — only synthesis remains.** `ORIGINAL_UNIT_STATS.md` +
`ORIGINAL_UNITS_RAW.md` already hold raw stats for the whole base-game catalogue
(StarCraft BW, Warcraft 2, RA1+Aftermath, TD, TS+Firestorm, RA2+YR) **and every
peer mod**: Mental Omega, DTA (Classic+Enhanced), Combined Arms, Shattered
Paradise, **CnC Reloaded (325 units)** and **Romanov's Vengeance (208 units)** —
all extracted with full stats (sources in `Downloads/`). Normalized ×rifle tables
+ the synthesis framework are in `BALANCE_SYNTHESIS.md`. Faction identity is
covered in `FACTION_IDENTITY.md` + `RESEARCH_NOTES.md`. Only the
items below remain.

| # | Sub-task | O | M | P | **E (h)** | Sessions | Depends | Notes |
|---|---|--:|--:|--:|--:|--:|---|---|
| R1/R2 | Extract + normalize peer mods (incl. CnCR + RV) | — | — | — | **0 (done)** | — | — | ✅ complete |
| R3 | Fill remaining identity stubs (Dune II/2000/Emperor, Outpost2, Cosmonarchy) — **future factions, optional** | 4 | 8 | 16 | **8.7** | 1–3 | — | base identity done |
| R4 | Synthesize per-class/faction TARGETS + categorize the extracted units into Cameo classes (the `Category`/`Desc` "TODO" columns) — the real remaining analysis | 10 | 20 | 40 | **21.7** | 4–7 | — | feeds anchors |
| | **Phase R subtotal** | | | | **30.4** | **5–10** | | was 87.3, then 45.6 — extraction is done |

### PHASE C — Class anchors (baseline + verifier per class, members interpolated)

| # | Sub-task | O | M | P | **E (h)** | Sessions | Depends | Notes |
|---|---|--:|--:|--:|--:|--:|---|---|
| C-inf | Finish 14 infantry classes: restat baselines + verifiers, `^AntiTankAntiAir` split, scout-tier fix, membership open-calls | 12 | 24 | 48 | **26.0** | 4–8 | R4 | several started |
| C-veh | 13 vehicle baselines restat + per-member synthesis (blocked on the anchor REVISION confirm) | 8 | 16 | 32 | **17.3** | 3–5 | A2,A4,maintainer | structure locked |
| C-def | Defense anchors (uses the new no-speed formula) | 6 | 12 | 24 | **13.0** | 2–4 | D-def | |
| C-air | Aircraft anchors (uses the new reload formula) | 6 | 12 | 24 | **13.0** | 2–4 | D-air | fighters already scale |
| C-naval | Naval anchors | 4 | 8 | 16 | **8.7** | 1–2 | R4 | smallest roster |
| | **Phase C subtotal** | | | | **78.0** | **12–23** | | |

### PHASE D — Formula-V2 completion (the maths + dispatcher)

| # | Sub-task | O | M | P | **E (h)** | Sessions | Depends | Notes |
|---|---|--:|--:|--:|--:|--:|---|---|
| D-def | Defenses formula (no `speed` stat — new baseline maths) | 6 | 12 | 24 | **13.0** | 2–4 | — | maintainer design exists |
| D-air | Aircraft reload formula (replace fixed 250-tick) | 6 | 12 | 24 | **13.0** | 2–4 | — | |
| D-price | Pricing terms: spread pricing, AA pricing, AoE pricing, **bake out per-class multipliers into baselines**, tech-tier RELATIVE-to-anchor fix | 10 | 20 | 40 | **21.7** | 4–7 | — | |
| D-disp | `rebalance_classes.py` dispatcher + catch-all-specials audit + populate `design.special`(K)/`tech_tier` across roster | 10 | 20 | 40 | **21.7** | 4–7 | D-price | |
| | **Phase D subtotal** | | | | **69.4** | **12–22** | | |

### PHASE F — Per-faction synthesize + apply (the payoff)

| # | Sub-task | O | M | P | **E (h)** | Sessions | Depends | Notes |
|---|---|--:|--:|--:|--:|--:|---|---|
| F | For each of ~20 factions / 48 packs: refresh ledger → workbook/ledger edit → `apply_balance --confirm` → re-extract → audits → boot-gate → commit yaml+ledger | 24 | 48 | 96 | **52.0** | 9–16 | W,A,C,D | **each `--confirm` is maintainer-gated**; shared-weapon fork pass folded in |
| | **Phase F subtotal** | | | | **52.0** | **9–16** | | |

### PHASE G — Triage, cleanup, regression

| # | Sub-task | O | M | P | **E (h)** | Sessions | Depends | Notes |
|---|---|--:|--:|--:|--:|--:|---|---|
| G1 | Phase-3 discrepancy triage (`discrepancies.md`) + legacy-workbook retirement | 8 | 16 | 32 | **17.3** | 3–5 | F | |
| G2 | Regression sweep (fluent/description-ref breakages since ~07-24) | 8 | 16 | 32 | **17.3** | 3–5 | — | can parallelize |
| G3 | Repo cleanup (dup scripts/docs, pre-existing content issues: husk `ArmamentInfo`, `ShortGameEnabled`, voice-set gaps) | 6 | 12 | 24 | **13.0** | 2–4 | — | no deletes w/o sign-off |
| | **Phase G subtotal** | | | | **47.6** | **8–14** | | |

---

## 3. Roll-up

| Phase | Expected effort (h) | Sessions | Notes |
|---|--:|--:|---|
| W — Weapon 3-way split | 156.6 | 26–47 | active; the near-term bulk |
| A — Weapon foundation laws | 21.7 | 3–5 | A1 done |
| R — Reference research & synthesis | 30.4 | 5–10 | **data-mining DONE**; only R4 synthesis (+ optional stubs) |
| C — Class anchors | 78.0 | 12–23 | |
| D — Formula-V2 completion | 69.4 | 12–22 | |
| F — Per-faction apply | 52.0 | 9–16 | maintainer-gated per faction |
| G — Triage & cleanup | 47.6 | 8–14 | |
| **TOTAL (serial agent-effort)** | **≈ 455 h** | **≈ 80–135 sessions** | |
| **+25 % contingency** (bespoke/judgment tail) | **≈ 570 h** | **≈ 95–115 sessions** | recommended planning figure |

**Wall-clock with 2–3 parallel agents + maintainer availability:** the three
independent tracks — **W+A** (weapon layer, ~178 h), **R+D** (research + formula
maths, ~115 h now that R is mostly done), and **C** (anchors, ~78 h, partly
gated on R4+D) — overlap, so the critical path is roughly
**W → C-veh/C-inf → F → G**. Estimated wall-clock critical path ≈ **230–300 h**,
i.e. **~45–60 sessions** if the maintainer gates clear promptly, stretching to
**~85 sessions** if `--confirm` and design calls are the bottleneck.

---

## 4. Recommended sequencing (critical path first)

1. **Finish PHASE W** — it blocks every DPS/range number. Order: W-A tail →
   W-B effect-heavy converter → W-C mixed/bespoke (maintainer calls in batches)
   → W-D bundles → W-E `1Dam` → W-F delete orphans. (W-G art can run in
   parallel on a second agent.)
2. **PHASE A** (A2 cannon AP/HE, A4 MissileAA spread + spread pricing) as soon
   as W's cannon/missile families are stable — unblocks vehicle DPS.
3. **PHASE R + PHASE D in parallel** on separate agents/worktrees (independent
   of the weapon YAML churn). R1 needs you to drop the CnCR/RV source files in.
4. **PHASE C** anchors once R4 targets + D formulas land.
5. **PHASE F** per-faction apply — the long, maintainer-gated payoff.
6. **PHASE G** triage/cleanup/regression, partly overlappable throughout.

## 5. Confidence & the biggest risks

- **σ is large on W-C, W-E, D-disp, F** (bespoke/judgment-heavy). Treat their
  numbers as ranges, not points.
- **R's data-gathering is done** (see §1 — CnCR and RV are both extracted; the earlier
  "only CnCR + RV remain" line here was stale and is corrected). The real remaining
  research work is **R4 synthesis** — turning the library into per-class/faction targets.
  Measured 2026-08-15: **1022 `TODO` cells against 1021 unit rows**, i.e. the
  `Category`/`Desc` columns are essentially untouched. R4 is analysis, not data-gathering,
  and it is the single biggest un-started item that other work depends on.
- **The multi-agent shared working tree is a process risk**, not an effort one:
  two agents on the same `weapons.yaml` = lost work. Use scoped commits, one
  owner per file-set, or separate worktrees.
- **Boot-gate + `--confirm` discipline is non-negotiable** and is baked into
  every W/F session's time.
