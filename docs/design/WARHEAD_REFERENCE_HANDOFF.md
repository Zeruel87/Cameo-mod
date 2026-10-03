# Reference warhead pipeline — handoff

**Status (rechecked 2026-09-28): assignment coverage is complete for all 17 sources, with no open weapon assignments. This is not maintainer approval of all sources: the 16 proposed sources still await the R69 review before cross-source averaging.**

This is a LANE handoff, not a dated one. It describes the live state of the WARHEAD and ARMOUR
side of the reference programme and is meant to be edited in place as the lane moves.

⚠ **This is not a second entry point.** `docs/HANDOFF.md` remains THE handoff and outranks this
file everywhere they touch; `AGENT_WORKSPACE.md` forbids a second roadmap or handoff, and this is
not one.

⚠ **Do not confuse it with [`REFERENCE_PIPELINE_HANDOFF.md`](REFERENCE_PIPELINE_HANDOFF.md).**
That file is the FACTION-ROUTING lane — which reference mod's units a Cameo faction draws on,
rulings R1–R15. This file is the WARHEAD/ARMOUR lane — what the Versus tables should be, rulings
R16–R73. Both draw on `REFERENCE_EXTRACTION_PLAN.md`, which is the single home for every ruling in
both; where a handoff and the plan disagree, the plan wins.

The binding rulings for this lane are **R16–R73 in `docs/design/REFERENCE_EXTRACTION_PLAN.md`**.
Read those before changing any tool here — several of them exist because a plausible-looking
shortcut produced confidently wrong numbers, and the numbers looked fine until a human queried
them.

## Contents

- [What this pipeline is for](#what-this-pipeline-is-for)
- [The five stages, and where each one stands](#the-five-stages-and-where-each-one-stands)
- [Run it](#run-it)
- [Where the data lives](#where-the-data-lives)
- [The next task, concretely](#the-next-task-concretely)
- [Open questions the maintainer has not ruled on](#open-questions-the-maintainer-has-not-ruled-on)
- [Traps that have already cost a session](#traps-that-have-already-cost-a-session)
- [Verification](#verification)

## What this pipeline is for

Cameo's warhead vocabulary should be **an average of the C&C-family mods it draws from**, so that
unit-versus-unit time-to-kill feels like those mods while the warhead list stays small and tidy.
The maintainer's own framing: *"in the end unit behaviour must be approximately identical — like
how many shots of a minigunner it takes to destroy a medium tank and vice versa… But we also try
to cleanly organize it with only a few warheads."*

Two numbers come out of it:

* an **armour matrix** — what our 16 armour rows should be worth, averaged over 20 sources;
* a **per-warhead Versus profile** for each Cameo warhead family.

Cameo currently ships **50 families**; Combined Arms alone needs **32**. Closing that gap is the
consolidation target, and the maintainer ruled it waits until every source has voted.

## The five stages, and where each one stands

| # | stage | tool | state |
|---|---|---|---|
| 1 | Read 20 sources into one normalised matrix | `warhead_matrix.py` | **done**, 0 degenerate |
| 2 | Map each source's armours onto our 16 rows, and average | `armor_interpolate.py` | **done**, all 20 mapped |
| 3 | Compress each source's weapons into review groups | `compress_warheads.py` | **done**, 17 of 20 |
| 4 | Assign each group to a Cameo warhead family | `warhead_family_assignment*.yaml` | **17 of 17 sources, 2,542 of 2,542 weapons (100%) — assignment COMPLETE; next = averaging** (CA reviewed; Mental Omega, Red Resurrection, Rise of the East, Romanov's Vengeance, CnC Reloaded, Shattered Paradise, RA2 Reborn, RA 20XX, Twisted Insurrection, DTA Enhanced, DTA Classic, OpenRA RA, Crystallized Nexus, OpenRA TS/TD/D2k proposed) |
| 5 | Collapse to one row per Cameo warhead | `family_matrix.py` | per-source collapse implemented for all dialects; cross-source averaging remains held by R69 |

Assignment coverage and human approval are separate gates. The next decision is
the maintainer's review of the proposed source assignments, not another automatic
family-matching pass.

### Stage 1 — the measurement

20 sources across three dialects (OpenRA MiniYAML, Westwood INI, one transcribed table). Every
source normalises to a geometric mean of 100 inside a 20:1 window, so the matrices can be
multiplied together. `--check` compares each source's window centre against its own positive
median and reports **0 degenerate sources**.

Four corrections live in here that were each found by the maintainer reading output, not by a
test:

* **R23 — a weapon's profile is the SUM of its warheads, not its biggest one.** OpenRA fires every
  warhead on every hit and Combined Arms' extras are complementary, not twins: `FireballLauncher`
  states `Light: 0` on one warhead and `Light: 50` on another. Picking one reported false
  immunities. Fold by effective damage instead.
* **R24 — a percentage warhead is priced through the typical unit it hits.**
  `HealthPercentageDamage` resolves as `HP x Damage/100 x Versus/100`, so `Damage: 300` is a
  3x-overkill one-shot. Priced against the geometric-mean HP of each armour class.
* **R25 — reachability and coverage are per ARMOUR CLASS, not per GND/AIR macro.** `380mm`'s
  second warhead deals 70,000 with `ValidTargets: Infantry`; summing that into Heavy and Wood
  turned a siege gun into a tank killer.
* **R27 — an AA armament is not a separate weapon.** 39 of `MissileAA`'s 43 members were the air
  half of a dual-purpose unit. Folding the pair shrank the dedicated-AA families to what they
  should mean and gave every ground warhead a real Aircraft figure.

### Stage 2 — the armour matrix

Each source armour is anchored to a POSITION on one of our four ladders — exactly, fractionally
(`combined_arms.Light` sits at VEH 0.5), flat across a ladder, or excluded. Unpinned rungs fill by
log-linear interpolation, clamped to the §12.0 window. The averaged target, one mod one vote:

| ladder | | | | | |
|---|--:|--:|--:|--:|--:|
| **INF** | None 112.8 | Flak 108.7 | Plate 99.3 | | |
| **VEH** | Scout 132.7 | Light 116.7 | Medium 100.9 | Heavy 88.4 | Superheavy 77.4 |
| **BLD** | Wood 105.8 | Steel 85.9 | Concrete 66.5 | | |
| **AIR** | Fighter 118.1 | Bomber 114.5 | Helicopter 110.5 | Spaceship 106.3 | |

All four are monotonic, and that was **not** imposed — it emerged from 18 independent sources
after two averaging defects were fixed (R34, R35). `Heroic` stays derived per §12.0b.

### Stage 3 — compression

**1,674 groups across 20 sources, at `tau = 0.20` (R41), with the element vocabulary censused corpus-wide (R45, R54).** The threshold was 0.50 until
2026-09-22, chosen as "well below the 25th percentile" of the pairwise distances — a heuristic
with nothing scoring it. `validate_families.py` scores a grouping against Cameo's own 904
labelled weapons, and at 0.50 a group held a MEDIAN OF 3 distinct Cameo families: 61% purity,
which is the CEILING on any single-family label. 0.20 buys 75%. See R39/R41. The Westwood INI dialects needed their own signal extraction
(R38): they have no `Projectile:` or `DamageTypes:`, and their projectile NAMES are useless
(`InvisibleWork`, `CannonInviso` are rendering variants). Delivery comes from weapon flags plus
the `[Projectile]` section's behaviour; element from warhead flags with `InfDeath` only as a
guarded fallback.

Three sources do not compress, all by construction: `cameo` needs no compression (a
`^Warhead_<Family>_<Level>` template IS its family, R37), `cameo_resolved` reaches 173 of 174, and
`d2k_mod` is a transcribed table with no actors so it votes on the armour ladder only.

### Stage 4 — family assignment

**Combined Arms is complete and maintainer-reviewed**, and it SURVIVED the tau change intact:
118 groups became **182** at tau 0.20 and all 182 inherited a reviewed decision — 74 carried, 72
split, 36 all-overridden, **0 straddle, 0 unreviewed**. The acceptance test is not the counts but
that **all 360 CA weapons resolve to the same family before and after (0 changed)**. The 72
`split` rows are re-opened as `proposed`: the old review saw those weapons mixed in with others,
so their label is inherited rather than re-confirmed.

That worked only because the review is recorded per WEAPON, not per group — group names carry a
`_2`/`_3` suffix assigned by clustering order and shift whenever the compressor is re-run. Use
`retau_assignment.py` for any future threshold change; never re-apply this file by group name.

The other sources carry 1,498 groups. `propagate_families.py` inherits a family wherever the
Combined Arms review fixed one for the same delivery x element x band triple:

| | groups |
|---|--:|
| inherited cleanly | 298 |
| inherited, but CA split that triple | 249 |
| **no usable precedent — needs a ruling** | **512** |

## Run it

```
python tools/reference/warhead_matrix.py --check          # 0 degenerate sources
python tools/reference/warhead_matrix.py --write          # docs/reference/warhead_matrix.json
python tools/reference/warhead_workbook.py                # the 25-sheet xlsx
python tools/reference/armor_interpolate.py               # armour mapping + averaged target
python tools/reference/compress_warheads.py --all --write # 1,059 groups
python tools/reference/propagate_families.py --write      # family proposals for 16 sources
python tools/reference/family_matrix.py --write           # one row per Cameo warhead
python tools/reference/build_family_page.py               # the reviewable page
python tools/reference/assignment_store.py                # who is reviewed, and how far
```

The full chain takes a few minutes; `--all` compression is the slow part.

⚠ **Order matters.** `family_matrix` reads the groups file AND re-reads the matrix, so re-run
`compress_warheads --all --write` after any change to `warhead_matrix.py`, then `family_matrix`,
then `build_family_page`.

## Where the data lives

| path | what | hand-edited? |
|---|---|---|
| `docs/reference/warhead_family_assignment*.yaml` | the reviews — ONE FILE PER SOURCE, keyed by the `source:` field inside it, not by filename. Groups + per-weapon overrides. Load through `assignment_store.py`, never by path | **yes, no generator** |
| `docs/reference/warhead_groups.json` | compression output, all sources | generated |
| `docs/reference/warhead_families.json` | one row per Cameo warhead | generated |
| `docs/reference/warhead_family_proposals.json` | propagated proposals for the other 16 | generated |
| `docs/reference/warhead_matrix.xlsx` | the per-source workbook | generated |
| `docs/reference/warhead_map.html` | the reviewable page | generated |

`warhead_family_assignment.yaml` deliberately has **no generator**, the same as
`peer_armor_map.yaml`: it is a series of judgements and every one has to be arguable. A generator
would invite someone to rebuild the decisions mechanically, which R21 forbids.

The review page is published at **https://claude.ai/artifact/2b4mMZydFnKiox9XKGB8s3** — update
that URL, never publish a new one.

## The next task, concretely

⭐ **REFRESH THE 10 BASE PROFILES FROM THE 20-SOURCE CORPUS.** This is the family-outward half of
the maintainer's 2026-09-22 ruling, and R42 measured why it is the whole job:

Every shaped family in the mod rests on ten measured ones — `Bullet`, `CannonAP`, `CannonHE`,
`Flame`, `Laser`, `MissileAA`, `MissileAP`, `MissileHE`, `Prism`, `Tesla` — because the other 27
live families are `BLEND_FAMILIES` and average their PARENTS' real profiles. Refreshing the ten
therefore propagates to all 47 at once.

And they are stale in a specific, checkable way. `docs/reference/family_profiles.json` was
generated on **2026-08-15** by `propose_family_profiles.py` over `survey_platforms.py` — the
OLD single-machine extractor that traces INI files out of `~/Downloads`, which nobody else has.
Its 31 entries carry **1 to 9 mods each**, gated at `min_rows: 8, min_mods: 3`. The pipeline in
this document carries **20 sources and 1,674 groups** and is hermetic. The numbers that ship were
never exposed to most of the corpus.

So: point the profile proposal at `warhead_groups.json` + `warhead_family_assignment.yaml`
instead of `survey_platforms`, re-derive the ten, and diff against what ships before writing
anything. ⚠ `gen_weapon_template` consumes `family_profiles.json` directly, so a re-derivation
moves live Versus tables — it is a `Versus` change and needs explicit permission (rule 4) and a
boot gate.

⚠ **THERE IS NO RAMP GAP TO FILL — do not go looking for one.** R42 measured the shipped
templates: 47 shaped, 2 flat BY DESIGN (`Magic`, `Sonic`, which ignore armour and are
special-cased in `class_tilt` AND the heaviness bell), 2 hand-tuned (`Nuclear_Super`,
`Sniper_Light`). Three separate estimates of a "33 ramp" gap were wrong because they inferred a
family's provenance from which JSON it appears in. Measure the template that ships.

### The other half — assignment for the remaining sources

⛔ **DO NOT GO LOOKING FOR A MATCHER. FOUR HAVE BEEN MEASURED AND THEY ALL SCORE ~20%.** R46 has
the numbers, scored against Cameo's 904 self-labelled weapons and the 337 maintainer-reviewed
Combined Arms ones:

| method | top-1 | shortlist |
|---|--:|--:|
| propagation by delivery x element x band | 17% | 34% |
| direct categorical construction | 20% | 38% |
| name evidence | 17% | — (40% precision on 42% coverage) |
| nearest Versus shape | 3–11% | 19% |

against a **75% median-purity ceiling**. The one that *should* have worked is the direct
construction — Cameo's vocabulary IS delivery x element, so `(Missile, Fire)` ought to be
`MissileFire`. It fails because the map is not injective: `Bullet`, `CannonHE`, `CannonAP`,
`Demolition`, `Concussion`, `Flak` and `Arrow` all measure as roughly `(Bullet, HE)`, and the
thing that separates them is the profile shape, which is the 3–11% method.

**So the 1,498 unassigned groups are a judgement task.** The maintainer authorised it being done
here for later review — *"fit everything from all mods into that reference table yourself and I
should try to review everything"* — but it cannot be automated and declared finished.

How to actually work a source:

1. `python tools/reference/propagate_families.py` and read that source's rows. Treat every
   proposal as a SHORTLIST entry (34–38% containment), never as an answer.
2. For each group, weigh the measured signals together — delivery, element, band, profile shape,
   `uses`, and the example weapon names. No single one decides it; that is what R46 measured.
3. Record the decision per WEAPON in `overrides:`, never per group name. Group names are an
   artefact of one compression run.
4. Re-run `compress_warheads --all --write` and confirm nothing was lost.

⚠ A per-weapon override BEATS its group, and an overridden weapon does not vote for its group in
any later migration (R41). That is what makes per-weapon records safe across re-clustering.

⭐ **THE LAYOUT IS DECIDED AND BUILT** (R47): one file per source, globbed as `warhead_family_assignment*.yaml`
and keyed by the `source:` field inside it rather than by filename — a file can be renamed, a review
cannot. `assignment_store.py` is the only loader; it also implements override-beats-group precedence
in one place, which is the rule every consumer previously reimplemented.

⚠ Answering that question surfaced three blockers that would each have wasted a review: the collapse
stage was OpenRA-only (and the three largest unreviewed sources are INI), `--write` overwrote rather
than merged, and `family_matrix` was NONDETERMINISTIC. All three are fixed — see R47.

⭐ **DONE (17 — all):** `combined_arms` 182 (REVIEWED), `mental_omega` 156, `red_resurrection` 138,
`rise_of_the_east` 133, `romanovs_vengeance` 99, `cnc_reloaded` 94,
`shattered_paradise` 92, `ra2_reborn` 80, `ra20xx` 77, `twisted_insurrection` 70, `dta_enhanced` 50,
`dta_classic` 38, `openra_ra` 33, `crystallized_nexus` 28, `openra_ts` 22, `openra_td` 20, `openra_d2k` 15 — 1,327 groups,
2,542 weapons.

**REMAINING: none.** ⛔ **Averaging is ON HOLD until the maintainer reviews the proposed sources (R69), and `Nuclear` must not be averaged as assigned (R69).** The next stage is the AVERAGING: one profile per Cameo family from every
source's decided weapons. ⚠ Read R68 first — OpenRA TS carries five lowercase armour columns that
are neutral for every family and must not be averaged as signal. Sixteen of the seventeen
sources are still `status: proposed`; only Combined Arms is maintainer-reviewed.

⛔ **GROUP-LEVEL READS IN THE AUTHORING AID ARE NOW MEMBERSHIP-CHECKED (R60).** `by_group()`
refuses a group whose current weapons differ from the ones the committed file recorded. If
it refuses, re-key that decision per weapon — do not "fix" it by renaming the group read.

⭐ **EXPECT NO FIRE ELEMENT.** Three of the seven sources done so far (Romanov's Vengeance,
Shattered Paradise, and Twisted Insurrection when it comes) have NO machine-readable fire
signal — `FireDeath`/`FlameDeath` are animations (R54) and only `Incendiary` and `Fire=yes`
are real. Their flamethrowers are read from profile and name, and the collapsed `Flame` row
has verified the call every time. Budget for it rather than being surprised by it.

✅ **`twisted_insurrection` was read ENTIRELY per weapon (R62)** — its element axis carries almost
nothing. Expect the same of the two DTA sources and `crystallized_nexus`, which are TS/RA-engine
INI mods too: read each weapon's projectile, report and firer (`tools/reference/ini_lookup.py`), and
remember TS tank guns fire `Projectile=InvisibleMissile`, so they measure as MISSILES.

⛔ **AFTER ANY REGROUPING, RE-KEY THE REVIEWS (R54).** Snapshot `warhead_groups.json` FIRST,
then `retau_assignment.py --old <snapshot> --source <sid> --write` for every reviewed source,
then confirm `assignment_store.py` exits 0. Group names renumber; a surviving name is not a
surviving decision, and the coverage report cannot see the difference on its own.

## Open questions the maintainer has not ruled on

* ~~**The 50 → 32 consolidation.**~~ **SUPERSEDED 2026-09-23:** the maintainer reversed it — the
  vocabulary GROWS (DESIGN §12.0k: `AntiAir` armour, `<Family>Air` variants, `LaserAA`/`TeslaAA`,
  `Radiation`, `Torpedo`/`AntiSub`, anti-infantry-only `Sniper`, `AntiMaterielSniper`, `ScoutRifle`).
* **Uniqueness.** 14 family pairs sit within 0.20 RMS log distance (`Laser`/`Tesla` 0.084,
  `Flame`/`Plasma` 0.088, `Bullet`/`Arrow` 0.105). The maintainer's rule: averaging sets position,
  separation applies only on collision, along the axis where the sources disagree most — and only
  after all 20 have voted.
* **`AA_GROUND_RATIO = 0.5`** in `family_matrix.py`. Where an entire family is air-only its ground
  rows are DERIVED at half the measured air value (R31, the landed-aircraft rule). Most reference
  mods give their SAM sites real ground rows, so these cells should be replaced by measurement as
  sources are assigned. Anything still carrying `derived_ground` at the end is something no source
  had an opinion about.
* **The naval ladder.** `DepthCharge`, `DoubleDepthCharge`, `SubMissile`, `TorpTube` are parked as
  `(park: naval)`. Their measured profiles are unusable anyway — all four read flat 100 because
  `ValidTargets: Submarine` makes every other armour unreachable.
* **Spread and Falloff: EXTRACTED (R73)** — `python tools/reference/warhead_geometry.py [--write]`, per weapon and
  per family, compared with Cameo's `PHYSICS_SHAPES`. TD/TS-era `Spread` (DTA, TI) is kept verbatim until its
  engine formula is verified. For review only; nothing is applied.

## Traps that have already cost a session

* **A name is not a measurement.** `BazAP` classified as Tesla because `Ba`**`zAP`** contains
  "zap"; `ChronoBeam` matched "Laser" and has no damage profile at all. Delivery comes from the
  projectile, element from damage types, platform from the firing actors. R21.
* **`*Death` tokens and `InfDeath` codes are DEATH ANIMATIONS**, not elements. CA's `HonestJohn`
  rocket artillery carries `FireDeath` and is not a fire weapon.
* **Group names shift on every re-run.** Record decisions per weapon. This saved the Combined Arms
  review four times.
* **An invariant that holds by construction cannot fail.** "gmean = 100, range [10,200]" is true
  because the normaliser makes it true; it proves nothing. `--check` compares against the positive
  median instead.
* **`children_named`, never `child`.** An actor can carry several `Armor` traits and the engine
  honours all of them. `child("Armor")` once made every plating look dead.
* **Read the exit code of PYTHON, not of `tail`.** `python … | tail -4; echo $?` reports `tail`'s
  status. `audit_doc_claims` was reported clean for a whole session that way while it was failing.

## Verification

```
python tools/reference/warhead_matrix.py --check     # expect: 0 degenerate source(s)
python tools/audit/audit_doc_health.py               # expect: PASS
python -m py_compile tools/reference/*.py
```

⚠ `audit_doc_claims` currently **FAILS on 6 claims** and none of them belong to this lane: they
are the `ra1_soviets` / `ra1_allies` rename whose ledger was never re-extracted
(`multi_main_fired_weapons` 192 vs 856, `ledgers_drifted` 0 vs 7, and four more). That failure
predates this work and is for the rename lane to clear.
