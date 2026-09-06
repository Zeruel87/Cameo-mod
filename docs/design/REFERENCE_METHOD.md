# The reference method — 10 relative values, geometric mean, normalized to Cameo

**Maintainer session 2026-09-03.** This is the METHOD document: what the reference corpus is, how a
Cameo target is derived from it, and which parts are ruled versus still open.

> ⛔ **This supersedes `BALANCE_SYNTHESIS.md` §5 steps 1 and 3** (the ÷ basic-rifleman transfer key
> and the "rifle anchor = 20000 HP" mapping). Those describe a method retired on 2026-08-30. Any
> document still teaching them is stale — see §7.

**Companions:** [`REFERENCE_DEDUP.md`](REFERENCE_DEDUP.md) (step 1, one roster one vote) ·
[`BALANCE_SYNTHESIS.md`](BALANCE_SYNTHESIS.md) (the source library and the faction map) ·
`docs/balance/REFERENCE_SYNTHESIS_REPORT.md` (the generated output).

---

## §0 — Why the rifle had to go, in the maintainer's words

> *"What if that game doesn't have any infantry and only uses vehicles?"* — 2026-08-30

Anchoring every comparison on one nominated actor has four failure modes and the corpus hits all
four: a source with no infantry has no anchor; "basic rifleman" is a different design object in
each game (a 40 HP Marine, a 12,500 HP Light Infantry, a 125 HP Conscript); one odd anchor silently
rescales everything measured against it; and it answers *"how many riflemen is this worth"*, which
is not a question anyone balances by.

**The replacement is POSITION IN DISTRIBUTION.** A unit is described by where it sits inside its own
source's spread. That description is dimensionless, so it transfers to Cameo without the two games
ever needing to share a scale.

---

## §1 — The ten relative values

For each **source**, each **stat**, and each of **two populations** — the unit's own TYPE
(infantry / vehicle / aircraft / ship / defense) and the OVERALL combat roster — compute five
aggregates and place the unit against them:

| coordinate | meaning |
|---|---|
| `r_med` | x ÷ the population's **median** |
| `r_am` | x ÷ the population's **arithmetic mean** |
| `r_gm` | x ÷ the population's **geometric mean** |
| `r_p05` | x ÷ the population's **low end** |
| `r_p95` | x ÷ the population's **high end** |

**5 coordinates × 2 populations = the 10 relative values.** They say how the unit performs relative
to its own type *and* relative to everything in that game — which is exactly the pair of readings
the class system needs, because a unit can be a heavy infantryman and a light actor overall.

⛔ **THE LOW AND HIGH ENDS ARE THE 5th AND 95th PERCENTILE, NOT THE RAW MIN AND MAX — and that is
measured, not preferred.** Both raw extremes are single actors, so both are hostage to one oddity:
Romanov's Vengeance lists a 100 HP vehicle; a roster's minimum damage is usually a dummy weapon and
its maximum a superweapon. Measured across all 302 matched actors, three variants:

| stat | variant | calibration (target/now, HIGH conf.) | within 2× |
|---|---|--:|--:|
| `hp` | raw min/max | 1.25 | 70% |
| `hp` | **p05/p95** | **1.22** | **70%** |
| `w_damage` | raw min/max | **0.30** ⛔ | **19%** ⛔ |
| `w_damage` | **p05/p95** | **1.08** | **65%** |
| `w_range` | raw min/max | **2.12** ⛔ | **39%** ⛔ |
| `w_range` | **p05/p95** | **1.05** | **92%** |

⭐ **On HP and Speed the choice barely matters** (raw min/max moves HP by a median 1.02×, and not one
unit by more than 2×) — the epic/`BuildLimit` exclusion already removed that distortion. **On the
weapon stats raw extremes destroy the model**: damage targets land 3.3× too low, range 2× too high,
and 85% of damage targets move by more than 2×. The percentile ends preserve the *"where in the
spread does this sit"* reading while denying any single prop or superweapon the power to define it.

⚠ `d_min` and `d_max` — ratios to the raw extremes — are still COMPUTED and kept as **diagnostics**.
When they disagree wildly with the middle three, that source's floor or ceiling is junk. They do
not vote.

**Stats carried:** `hp`, `speed`, `turn_speed`, `turn_ratio`, `w_range`, `w_damage`, `w_burst`,
`w_reload`, `w_dps`, and armor-aware `dps_vs_{INF,VEH,AIR,BLD}`. The four the maintainer named —
HP, Speed, Damage, Range — are all present.

**Population rule** (maintainer 2026-08-30): a row enters a distribution only if it is **buildable
and unlimited**. Not-buildable actors never reach a player; `BuildLimit` rows are one-offs; epics
and heroes are balanced separately. Buildings are excluded from `overall` — they are not mobile
combat units and they outnumber everything else in most rosters.

---

## §2 — The pipeline, in order

1. **De-duplicate the sources.** One roster, one vote — [`REFERENCE_DEDUP.md`](REFERENCE_DEDUP.md).
   Before the mean, always: the geometric mean has no defence against a roster that votes five times.
2. **Build each source's distributions** (§1), per stat, per population.
3. **Match** each Cameo actor to reference units — by name, then by role and design analogy.
4. **Place** each match → its 10 relative values.
5. **Pool across sources with the GEOMETRIC mean**, per coordinate. These are ratios: a source 2×
   high and one 2× low must cancel to exactly 1.0, and only the geometric mean does that (the
   arithmetic mean returns 1.25 and biases every target upward). It is also the only mean under
   which *normalize-then-average* and *average-then-normalize* agree.
   ⛔ **Raw stats are NEVER averaged across sources.** 125 HP and 12,500 HP are one design intent at
   two scales; their mean belongs to no game. Only dimensionless coordinates are pooled.
6. **Normalize to Cameo.** Multiply each pooled coordinate by **Cameo's own** matching aggregate →
   one candidate absolute per coordinate → the target is the geometric mean of those candidates. A
   unit sitting at 2.2× its source's vehicle median lands at 2.2× *Cameo's* vehicle median. **This
   is what makes Cameo's larger numbers automatic rather than hand-scaled.**
7. **Set the class anchor at the 100% mark** of the 100–250% target band, from a member that has a
   grounded target.
8. **Fill the rest of the class from the anchor via the formula** — see §5.

---

## §3 — Cameo's own value votes, capped at one third

**Maintainer ruling 2026-09-03:** *"Yes it votes but make sure there are always at least 2 reference
actors so the cameo stats are always 33% weighting or less!"*

So Cameo's current stat is **one vote among at least three**: a target may only be computed when
**≥2 independent reference sources** matched. A unit with one reference voice gets **no target** —
it is not synthesized at all, rather than synthesized from a single opinion plus itself.

⚠ This is a **change from both existing layers**. The distribution layer pools peers only and never
lets Cameo vote; the retired rifle layer lets Cameo vote with no minimum-source floor, which is how
LOW-confidence single-source rows were produced. Neither implements the ruling as stated.

⚠ **It also shrinks the corpus.** Today 302 actors carry a signature and only **161** reach ≥3
sources on HP; the ≥2-reference floor is what the ruling requires, and the count of units that
clear it must be reported every run rather than assumed.

---

## §4 — ⛔ Source routing and the duplication checks (measured 2026-09-03)

**Maintainer ruling:** *"make sure you don't duplicate stats from similar sources... better check
everything!"* Every pair below is measured by `tools/balance/lineage_dedup.py`; `w10` is the share
of shared units agreeing within 10% after the pair's median scale offset is divided out.

### The four the maintainer asked about

| check | result | verdict |
|---|--:|---|
| **CnC Reloaded ~ Romanov's Vengeance** | 49 shared, offset 1.00×, **47%** | ⭐ **NOT duplicates — both vote** |
| **Mental Omega ~ anything** | best match is 33% (OpenRA RA2); vs CnCR only **17%** | ⭐ **unique, as suspected — its own vote** |
| **Valiant Shades** | 79 / 76 / 73 / 72 / 67% against five RA2 sources, all at offset **1.92×** | ⚠ an RA2-lineage mod at ~1.92× scale; every pair below the 85% cut, so it votes — but it is the corpus's closest near-miss |
| **Crystallized Nexus** | **67%** vs OpenRA TS at offset 1.00; only 20% vs Shattered Paradise | ⭐ **TS-themed, confirmed** — and an independent rebalance, so it votes |

⭐ **Every one of the maintainer's instincts checked out**: MO is different enough to justify a
unique vote, CnCR and RV are not the same data, and Crystallized Nexus is the other TS-themed mod.

### The rest of the routing checks

| pair | n | offset | `w10` | verdict |
|---|--:|--:|--:|---|
| Combined Arms ~ OpenRA Red Alert | 76 | 1.00× | 63% | independent |
| Combined Arms ~ OpenRA Tiberian Dawn | 33 | 1.00× | 36% | independent |
| Shattered Paradise ~ OpenRA Tiberian Sun | 46 | 1.00× | 35% | independent |
| Romanov's Vengeance ~ Combined Arms | 64 | 0.40× | 20% | independent |
| Valiant Shades ~ Romanov's Vengeance | 89 | 1.92× | 42% | independent |

**Already collapsed** (`REFERENCE_DEDUP.md`): the five RA2-family copies into Romanov's Vengeance,
and `Tiberian Sun` into `OpenRA Tiberian Sun` (96%). So the maintainer's *"all the Yuri's Revenge
and RA2 implementations might also be the same"* is **confirmed and already applied** — RA2 vanilla,
Yuri's Revenge, RA2/YR (raw INI), OpenRA RA2 official and YR-on-OpenRA no longer vote separately.

### ⚠ OPEN — routing vs the cross-reference principle

The 2026-09-03 ruling names per-family source sets (RA2 → CnCR + RV + MO + CA; TD/RA1 → DTA +
OpenRA TD/RA1 + CA; TS → mostly Shattered Paradise + Crystallized Nexus). The 2026-07-25 ruling in
`BALANCE_SYNTHESIS.md` §2 says the opposite: *"synthesize from ALL source material... never restrict
a mod to only its 'primary' factions."*

⛔ **These cannot both be law and the maintainer has to pick.** Reading the newer one as a
*de-duplication* instruction rather than a routing rule reconciles them — but the measurements above
show the named sources are NOT duplicates of each other, so de-duplication does not by itself
produce those per-family sets. **Unresolved; nothing is routed until it is ruled.**

---

## §5 — ⛔ The hard part: the reference has TYPES, Cameo has CLASSES

**Maintainer, 2026-09-03:** *"we can only relatively easily and accurately check for unit types but
not classes since the reference data doesn't have any classes like we have so there could be a lot
of inferred and invented data that might be wrong."*

**Correct, and measured.** Reference coverage of the 660 classed Cameo units:

| | |
|---|--:|
| units with a class | 660 |
| **carrying a reference signature** | **205 (31%)** |
| classes with **zero** coverage | **6** — `commando`, `epic_vehicle`, `dreadnought`, `closecombat`, `archer` (+`heavy_sniper` at 1) |
| `scout` | 11 of 30 (37%) |

Best covered: `mortar` 80%, `heavy_sniper` 50%, `support` 47%, `high_tech_tank` 46%.

⚠ And a prior measurement forbids the obvious shortcut: median distance from a unit to its **own**
class anchor is **2.94**, while median distance **between** anchors is **1.21**. Units sit further
from their own anchor than the anchors sit from each other, so **class boundaries are not
recoverable from stats.** Any attempt to infer a class from reference numbers will be wrong.

### THE RULING (maintainer 2026-09-03): a grounded anchor, then the formula

**Never synthesize a class target.**

1. Synthesize **per-unit** targets only for units with ≥2 reference sources.
2. Choose each class's **anchor from among those grounded members**, placed at the 100% mark.
3. Derive **every unmatched member from the anchor via the formula** — not from invented reference
   data.

⭐ **This keeps invented data at exactly zero.** A unit either has a reference voice, or it is priced
by the formula from a grounded anchor. Nothing is interpolated from a class-level profile that the
data does not support.

⛔ **The cost, stated plainly:** the **6 zero-coverage classes have no grounded anchor candidate at
all**, and must be resolved by better matching or a hand ruling. They cannot be synthesized.

---

## §6 — ⛔ What is missing from the corpus, and what it blocks

Only **13 of 26** source labels are in the distribution layer. The other 13 are hand-typed markdown
tables, and the split is not arbitrary — the 13 are exactly the **OpenRA clones on disk**, resolvable
by the resolver. Mental Omega, CnC Reloaded and DTA are Westwood/Ares INI mods; no checkout exists.

| group | rows | has a type column? | can do the OVERALL 5 | can do the TYPE 5 |
|---|--:|---|---|---|
| the 13 OpenRA clones | 2,256 | ✅ `type` | ✅ | ✅ |
| **Mental Omega + CnC Reloaded** (+RA2v, YR) | 1,021 | ✅ `kind` | ✅ | ✅ — **ruled IN, not yet wired** |
| StarCraft, Warcraft 2, RA1, TD, TS, RA2/YR raw | 188 | ❌ | ✅ | ❌ needs a type column |
| **DTA** | **0** | ❌ | ❌ | ❌ |

**Ruled 2026-09-03:** wire Mental Omega and CnC Reloaded into the distribution layer now; the
Westwood originals wait for a type column.

### ⛔ DTA is registered, contributes zero rows, and blocks the TD/RA1 routing

`DOC4_SOURCES` registers `Dawn of the Tiberium Age`, and it votes on nothing. Two separate faults:

1. **Parser:** its table is `| Unit | Classic | Enhanced | DTA's intent |` — no `HP` column, so
   `parse_doc4` skips every row. It reads as present while voting on nothing.
2. **Data, and this one cannot be parsed around:** that section is **15 hand-picked highlight rows**,
   not a roster. A source's median cannot be computed from 15 cherry-picked units, so DTA could not
   enter the distribution layer even with the column fixed.

⛔ **The 2026-09-03 routing ruling requires DTA for the TD and RA1 factions, so that half of the
ruling is BLOCKED** until `INI/Rules.ini` + `INI/Enhance.ini` reach the repository (HP ÷10 for the
TS engine). Searched and confirmed absent from the working environment: no `~/Downloads`, no
`*_units.csv`, no DTA INI anywhere on disk.

---

## §7 — Documents still teaching the retired rifle method

⛔ **`DESIGN.md` — the binding contract — describes NEITHER method.** That is the root cause of the
drift: with no binding statement, nothing can be checked against it, and a retired method survived
in seven documents and one live tool. **Fixing that is step 0.**

| document | what is stale |
|---|---|
| `BALANCE_SYNTHESIS.md` §5 | steps 1 and 3 teach ÷rifleman and "rifle anchor = 20000 HP" |
| `SYNTHESIS_DELTA.md` | auto-generated by the rifle tool; its "How each target is reached" is the retired method |
| `REFERENCE_SYNTHESIS_REPORT.md` | says *"five ratios plus `p_rng`"* — six per population; the code votes four |
| `BALANCE_PIPELINE_ESTIMATE.md`, `ORIGINAL_UNITS_*.md`, `HANDOFF.md` | rifle-relative framing |
| `tools/balance/synthesize_reference.py` | **still produces the per-unit HP/cost targets**, by the retired method |

⚠ **`lineage_dedup.py` scores duplication on `×rifle` HP** — the only coordinate all three documents
share. Once this method is law, the de-duplication test should be re-scored on `r_med`/`r_gm`.

---

## §8 — Reproduce

```sh
python tools/balance/reference_distribution.py         # the 10 relative values + targets
python tools/balance/lineage_dedup.py                  # source duplication, every pair
python tools/balance/lineage_dedup.py --pair "CnC Reloaded" "Romanov's Vengeance"
python tools/balance/anchor_readiness.py               # per-class anchor integrity
```

---

## §9 — ⛔ THE MATCHING LAW (maintainer 2026-09-03)

Matching is step 3 of §2 and it is what limits everything: **521 of 823 Cameo actors match nothing
today**, and coverage — not source count, not the vote floor — is the binding constraint on how
many anchors can be grounded. The maintainer's ruling turns it from a per-unit search into a
**one-to-one assignment**.

### §9.1 — The four rules

> *"you can use the mental omega Chinese assault tank (I think it's called Qiling) as reference!
> Same for the Latin Syndicate rusher tank use the Latin confederation jaguar tank which is also
> supposed to be a fast light tank right? ... The rule is one unit that fits best per mod / game
> but never use the same unit twice for different units and never use different units from the
> same game for one unit!"*

1. **Role analogies are allowed.** `asianalliance_lynxtank ≈ an MBT` is legitimate — both are main
   battle tanks. Matching is not restricted to names.
2. ⛔ **At most ONE reference unit per source, per Cameo unit.** Never two units from the same game
   for one Cameo unit. *"you are not allowed to use two different tanks like grizzly and rhino for
   the same unit as reference since they are completely different."*
3. ⛔ **A reference unit may be used ONCE, ever.** Never the same reference for two Cameo units.
   *"This is to make each reference chain clean and not muddy."*
4. ⭐ **Maximise DISTINCT references.** Where a natural counterpart is already taken, find a
   different one from a mod not yet drawn on for that role — that is the point of the rule, not a
   side effect of it.

**Together these make it a bipartite one-to-one assignment, computed per source** (the sources are
independent of each other, which is what keeps it tractable). It cannot be done greedily per unit.

### §9.2 — How badly the current matcher breaks it

| | |
|---|--:|
| Cameo units with any match | 302 |
| distinct reference rows in use | 478 |
| ⛔ reference rows feeding **several** Cameo units | **192 (40%)** |
| ⛔ Cameo units drawing **2+ rows from one source** | **95** |
| ⭐ matches already law-abiding | **~35 of 302** |

The worst case: **one Combined Arms MCV row feeds 17 different Cameo MCVs**, and six other sources
do the same. `ra2_allies_battlefortress` pulls four separate Valiant Shades units at once.

### §9.3 — Exempt: the role-identical units

**Ruling:** MCVs, engineers, harvesters/miners and the whole `support` class are **exempt from
reference matching**. They are the same design in every faction, they are not what the reference
corpus is for, `support` is already ability-priced and hand-tuned by ruling, and harvesters need a
throughput formula rather than a DPS one.

**Widened 2026-09-03 to include transports and detectors** — their value is capacity or an
ability, not HP and DPS, so a reference target for them means little.

| | count |
|---|--:|
| role-identical by name (MCV · engineer · harvester · miner) | 61 |
| `class == support` | 110 |
| transports / detectors by name | 47 |
| transports by template subtype | 9 |
| **union exempted** | **166** |
| of the 302 matched actors, now exempt | 64 |
| **matched actors that remain in scope** | **238** |

⚠ **One boundary needs a ruling: the APCs.** The keyword sweep catches `cabal_scarabapc` and
`forgotten_apctruck`. An unarmed transport clearly belongs out; an ARMED troop carrier is a combat
unit with real stats. Currently they are exempted with the rest — flagged rather than settled.

⭐ This also dissolves the capacity problem the one-to-one rule would otherwise create: 17 MCVs
competing for ~13 MCV references, with at least 4 guaranteed to lose.

### §9.4 — Who wins a contested reference: FACTION LINEAGE first, then stats

When several Cameo units can claim one reference, **faction lineage outranks statistical fit**,
then cost and HP proximity break ties. This follows the inspiration map already recorded in
`BALANCE_SYNTHESIS.md` §3 and the maintainer's own worked examples:

| Cameo unit | reference | why |
|---|---|---|
| `ra2_soviets_rhinoheavytank` | Mental Omega **Russia MBT** | same faction lineage |
| `ra2_allies_grizzlytank` | Mental Omega **Euro Alliance Cavalier** | same faction lineage |
| `asianalliance_lynxtank` | Mental Omega **Qiling** (Chinese assault tank) | Asian Alliance ← MO China |
| `latinsyndicate_rushertank` | Mental Omega **Jaguar** (fast light tank) | Latin Syndicate ← MO Latin Confederation |

⚠ **A purely statistical scorer would hand a Soviet reference to a Dune unit** whenever the numbers
happened to line up better. Lineage-first prevents that.

### §9.5 — A collapsed lineage offers ONE reference, not several

For rule 2's per-source cap, a de-duplicated lineage counts as **one source** — only the
representative may offer a unit. RV's Rhino and vanilla YR's Rhino are the same design, so allowing
both to be assigned would re-introduce through the matching layer the duplicate vote that
`REFERENCE_DEDUP.md` removed.

### §9.6 — ⛔ Blocked on Mental Omega

**Every reference the maintainer named for the modded factions is Mental Omega** — Qiling, Jaguar,
Cavalier, Russia MBT. MO is ruled into the distribution layer and **not yet wired**, so Latin
Syndicate, Asian Alliance and the other MO-inspired factions currently have nothing to match
against. **Wiring MO and CnC Reloaded comes before the assignment is built**, or it would be
computed and immediately redone.

⚠ And `td_gdi_mammothtank` vs `ra1_soviets_mammothtank` are two different units that DTA gives
different stats — *"but you need the enhanced ini for it first right?"* Correct: DTA contributes
zero unit rows (§6), so that distinction cannot be honoured until the INIs arrive.

### §9.7 — Every fit is assigned; confidence carries the warning

**Ruling:** the optimiser does **not** leave blanks. It assigns the best remaining candidate in
every source and marks anything below the fit threshold, letting the existing LOW / MEDIUM / HIGH
confidence level carry the caveat downstream rather than dropping the row.

⚠ **Consequence to watch:** the tail of each source's assignment is made of leftovers, and those
are exactly the units with no natural counterpart. A LOW-confidence match is therefore not merely
"one source" — it may also be a poor pairing. The confidence label has to distinguish *few sources*
from *weak fit*, or the two collapse into one word and the second becomes invisible.

### §9.8 — The assignment is recomputed, never pinned

**Ruling:** always compute the globally best assignment, and **report every match that changed and
every target that moved by more than 10%**.

⚠ **This interacts with §9.7 and the interaction is the risk.** Because a reference may be used
only once, adding a single new source can cascade: the newcomer takes a unit, freeing the one it
displaced, which displaces another, and so on down the chain. **A signed anchor can therefore move
because an unrelated mod was added.** The change report is not a nicety here — it is the only thing
standing between a recomputed assignment and a silently re-based class. It must diff *targets*, not
just matches.

### §9.9 — Reviewed one class at a time

**Ruling:** one reviewable table per class — members down the side, sources across, the proposed
reference in each cell with its fit reason. That matches the class-by-class workflow, and lets a
class's **matching and its anchor be signed together**.

⛔ Which means: **a class cannot be signed while its matching is unreviewed**, because the anchor is
chosen from among the grounded members and the matching decides which those are.

### §9.10 — The fit score is LEXICOGRAPHIC, not weighted

**Ruling 2026-09-03:** *"All of the above should be considered! Name similarity first, then tech
Tier confirmed, then type, then role then cost."*

So it is an ordered cascade, not a weighted sum — each criterion only breaks ties left by the one
above it:

1. **name similarity** — an exact or alias name match wins outright
2. **tech tier** — confirmed, not assumed
3. **type** — infantry / vehicle / aircraft / ship / defense
4. **role** — the class archetype
5. **cost** — the final tie-break

⚠ A weighted score would let a large cost advantage outvote a name match. A cascade cannot, which
is why it is the stricter and more predictable reading. **Faction lineage (§9.4) sits above all
five** — it decides who wins a contested reference; this cascade decides how well any one pairing
fits.

### §9.11 — ARMED APCs stay in the pool

An unarmed carrier is exempt (§9.3); an **armed** troop carrier is a combat unit with real HP, DPS
and armour and stays in. The test is mechanical — *does the actor have a damaging armament* — not
the name, so `cabal_scarabapc` and `forgotten_apctruck` are judged by their guns.

### §9.12 — ⛔ Class definitions, from the maintainer (2026-09-03)

I reported these six classes as having zero *reference coverage*. That is a different claim from
having no *definition*, and I should have quoted the definitions that exist. **`archer` and
`heavy_sniper` are both defined in `FORMULA_V2.md` §6b** and always were:

* **archer** — *"projectile-arc infantry; uses the MISSILE projectile; arrow speed = maxRange/10;
  hits air (wc2 archers, japan/asian maidens)"*. Maintainer's roster: archer maiden, veteran
  archer, Warcraft archers and axe throwers, rangers, headhunters.
* **heavy sniper** — *"all GROUND, NO air; loses to pure snipers as the trade"*. Anti-tank snipers
  that target all ground units and deal good damage; they lose the anti-air ability.

⛔ **`dreadnought` genuinely had no definition** — only a validation table. Now defined in
`FORMULA_V2.md`: heavy, slow, **frontal-facing (no turret)**, more range and damage than a regular
tank. ⭐ **That is mechanically testable** — the corpus carries a `Turret` column — and it already
finds its match: **Crystallized Nexus' Mammoth Mk. II**, the only turretless Mammoth in the corpus,
with the longest range of any (10,240 against 4,864–6,912) at a low speed. Shattered Paradise's
turretless Juggernaut is the second candidate.

The remaining three, as ruled:

* **commando** — any HERO infantry: RA1/RA2 Tanya, Boris, TD commando, TS railgun and shotgun
  commandos, RA1 Japan exorcist, RA1 Soviet Volkov, StarCraft Jim Raynor, Kerrigan, Zeratul.
* **closecombat** — any SHORT-RANGE infantry: shotgunners and SMG troops, e.g. the Naxis SS soldier
  and the mutant shotgun gal.
* **epic_vehicle** — ⛔ **build-limited vehicles, EXEMPT from the balance pipeline**, same standing
  as `support`. It should stop being reported as an unfitted failure.

⭐ **So of the six "empty" classes, only three are genuinely blocked**: `epic_vehicle` is exempt,
`dreadnought` has a measurable definition and a corpus match, and `heavy_sniper`/`archer` have
documented rosters to match against. `commando` and `closecombat` have wide, named rosters that
should match well once Mental Omega is wired.

---

## §10 — Mental Omega and CnC Reloaded are WIRED (2026-09-03) — and it broke the targets

**Ruled and done.** `reference_distribution.doc1_rows()` reads Document 1's hand-extracted tables
into the peer-row shape, so the distribution layer runs on **15 sources, 2,878 rows**, with MO (306)
and CnCR (316) third and fourth largest. Cameo actors carrying a reference signature: **302 → 324**.

⭐ **No unit conversion was needed.** Every coordinate is dimensionless and every distribution is
built from one source's own values, so MO's damage in Westwood points never meets Combined Arms' in
OpenRA points. DOC1 measures range in CELLS and reload in FRAMES; the ratios are identical either
way.

**Three limits, declared rather than papered over:** no `Turret`, `Burst` or armour columns, so
these two abstain on `turn_ratio`, `w_burst` and every `dps_vs_*` coordinate; `w_dps` is derived as
Damage/Reload, proportional to real DPS within a source but not comparable to DOC5's measured DPS
as a raw number; and ⛔ **no build-limit column, so the population rule cannot be fully applied** —
`cost > 0` removes the decoys (MO lists a *"Decoy Quetzal Eyes"* at cost 0, damage 1, range 1) but a
one-off hero may still sit in their distributions.

### ⛔ AND THE TARGETS GOT WORSE, WHICH IS THE POINT

| worked example | HP target before | after |
|---|--:|--:|
| `ra2_soviets_apocalypsetank` | 0.98× of current | **0.52×** |
| `ra2_soviets_conscript` | 0.93× | **0.69×** |

Not because the new sources are bad — **because the matching law (§9) is not implemented yet.**
Mental Omega lists three "Apocalypse Tank" rows (1050, 1575 and 620 HP, the last with zero damage)
and two "Conscript" rows. The pooling appends **once per ROW**, so:

* Mental Omega casts **3 of the Apocalypse's 7 votes (43%)** and 2 of the Conscript's 6 (33%);
* across the corpus, **114 of 324 matched actors (35%) now draw 2+ rows from a single source**,
  up from 95 of 302 before;
* the worst are extreme — `cabal_avatar` takes **8 rows from CnC Reloaded alone**,
  `ts_nod_mobilerepairvehicle` 5, `yuri_virus` and `ra2_allies_harrier` 4 each from Mental Omega.

⛔ **So a source's weight is currently decided by how many rows happen to share a unit's name**, and
adding evidence makes that worse rather than better. §9 rule 2 — *at most ONE reference unit per
source, per Cameo unit* — is exactly the fix, and it is now **blocking rather than optional**.

> ⛔ **DO NOT USE THE CURRENT TARGETS.** `REFERENCE_SYNTHESIS_REPORT.md` and
> `reference_signatures.json` are regenerated with all 15 sources and are correct in method, but
> every multi-row match is mis-weighted until the one-to-one assignment lands. No anchor should be
> set from them in the meantime.

### §9.13 — Choosing between VARIANTS of the same reference unit (maintainer 2026-09-03)

The one-to-one law says one reference unit per source. When a source lists the same unit several
times, something has to choose. The worked case — Mental Omega's four Apocalypse rows:

| unit | HP | cost | spd | weapon | dmg | rng | role |
|---|--:|--:|--:|---|--:|--:|---|
| Apocalypse | 620 | 1600 | 4 | `CatastropheGre` | **0** | 7.5 | ? |
| Apocalypse Tank | 1050 | 2000 | 5 | `120mmx` | 130 | 8 | general |
| **Apocalypse Tank** | **1575** | 2000 | 4 | `120mmx` | 130 | 8 | general |
| Apocalypse Prototype | 3600 | 1500 | 5 | `120mmMammoth` | 120 | 7 | anti-inf |

**Rule A — a zero-damage row never matches a combat unit.** *"Obviously the zero damage one should
be excluded."* The 620 HP row carries `CatastropheGre` and deals 0 damage: it is a different
device, not a weaker Apocalypse.

**Rule B — among true variants, take the one carrying the Cameo unit's IDENTITY.** The 1050 and
1575 rows are identical in cost, weapon, damage, reload and range and differ only in HP (1.5×) and
speed — the signature of a subfaction variant. Ruling: *"for the apocalypse tank I would use the
bigger number simply because it's the biggest tank in the game"*. So where a Cameo unit's identity
is *the heaviest of its kind*, the heaviest variant is the match; the fit cascade (§9.10) decides
the rest.

⚠ **The premise checks out for TANKS and not for the population**, which matters because every
coordinate is measured against that population. 1575 sits at the **89th percentile** of Mental
Omega's armed `vehicle` rows, not the top. Above it: the Paradox Engine (5,000 — MO's epic), a
Kirov Airship (3,000), the Apocalypse *Prototype* (3,600), an Enterprise Aircraft Carrier and a
Tigr APC. Among genuine tanks it is the top, exactly as ruled.

### §9.15 — ⭐ AN ARMED BUILDING IS A DEFENCE — 94 votes were being thrown away

The maintainer pushed back on §9.14: *"Both mental omega and cnc reloaded have defenses! Search for
tesla coil and you will find it! Maybe it is using a different category!"*

**Half right, and the half that was right is much bigger than the question.**

⚠ For MO and CnCR specifically the original reading holds: Document 1's Mental Omega section (lines
196–523) and CnC Reloaded section (523–852) contain **no structures at all** — zero blank-`kind`
rows, no defence rows, and the `Category` column has no defensive category either. The `tesla`,
`atesla`, `tesla-tr` and `atesla-tr` rows at lines 888–900 are in the **Romanov's Vengeance**
section, and RV is the one DOC1 source with 49 blank-`kind` rows — its structures.

⛔ **But the corpus-wide check the question prompted found a real defect.** Defences were in the
corpus all along, typed **`building`**:

| | before | after |
|---|--:|--:|
| defence-named ARMED rows typed `building` | **73** | 0 |
| rows in the `defense` population | **85** | **179** |
| sources contributing any defence | **5 of 15** | **13 of 15** |
| Romanov's Vengeance defences | **0** | **27** |
| Shattered Paradise defences | 2 | **23** |

**And a `building` row was not merely misfiled — it voted on NOTHING.** Buildings are excluded from
the `overall` population by design, and `defense` is its own population, so an Obelisk of Light
filed as `building` was measured against neither. **94 armed rows were silent.**

The cause is that type comes from the mod's QUEUE NAME (`TYPE_TOKENS` in `extract_peer_units.py`),
so any mod filing turrets under a "Building" queue lost every one of them — Crystallized Nexus,
Generals Alpha, OpenRA TD/TS/D2K and Dune II all contributed zero defences for that reason.

**The rule now applied in `peer_rows()`: a structure that shoots is a defence.** The test is the
weapon, not the name. ⚠ It is applied at READ time as a population rule; `extract_peer_units.py`
still writes `building`, and should follow.

⭐ **41 of Cameo's own defence actors now carry a reference signature.**

### §9.14 — ⛔ MO and CnC Reloaded have NO ship type, so their vehicle population is contaminated

Found while checking the above. Their `kind` column uses only **infantry / vehicle / aircraft**:

| source | infantry | vehicle | aircraft | ship | defense |
|---|--:|--:|--:|--:|--:|
| Mental Omega | 130 | 151 | 41 | **0** | **0** |
| CnC Reloaded | 111 | 191 | 22 | **0** | **0** |
| Romanov's Vengeance | 50 | 48 | 13 | 18 | 29 |

**Every naval unit is therefore typed `vehicle`.** Unambiguous cases: MO's Tesla Cruiser, Siren
Frigate, Reaper Corvette, Mosquito Demoboat; CnCR's Hydra Submarine, Mini-Sub, Aircraft Carrier.
Counted by name, **13% of MO's and 18% of CnCR's `vehicle` rows** look naval or airborne.

Two consequences, both real:

1. ⛔ **MO and CnCR cannot contribute to the `ship` or `defense` populations at all** — they have
   none, so they silently abstain there. Only Romanov's Vengeance and the OpenRA sources carry
   naval and defensive rows.
2. ⛔ **Their `vehicle` distributions are stretched by submarines and cruisers**, which are tanky,
   so every MO/CnCR vehicle coordinate is measured against a population that is partly not
   vehicles.

⚠ **Unruled.** The options are to leave it and record the caveat, to EXCLUDE the unambiguous naval
rows so those sources abstain rather than distort, or to retype them as `ship` — which would build
a partial naval population out of name guesses. Nothing is applied.

---

## §11 — The assignment is built (2026-09-03) — and its coverage number is inflated

`tools/balance/assign_references.py` implements the §9 law: a lexicographic cascade, a greedy
descent (clause 9 says *"assign the best remaining"*, which is a greedy, not a global optimum),
one reference per source per unit, each reference used once, exemptions applied first so an exempt
unit never consumes a reference.

| | |
|---|--:|
| Cameo actors in scope | **695** (128 exempt) |
| assigned at least one reference | **595** |
| reaching the ≥2 reference floor | **448** |
| total assignments made | **1,850** |

⭐ Against 221 actors clearing the floor before, that looks like a doubling. **It is not, and the
quality distribution says why.**

### ⛔ 43% of the assignments are weak or unrelated

| name score | meaning | count | share |
|---|---|--:|--:|
| 1.00 | exact name match | 449 | 24% |
| 0.90–1.00 | prefix / alias | 93 | 5% |
| 0.75–0.90 | strong similarity | 131 | 7% |
| 0.60–0.75 | shares a distinctive word | 374 | 20% |
| **0.40–0.60** | **weak** | **730** | **39%** |
| **0.00–0.40** | **unrelated** | **73** | **4%** |

Median name score **0.62**. Real examples from `scout`: `forgotten_mutant_wild` drew *"Pilot"*,
*"Bodybuilder"*, *"Warrior"*, *"Red Devil"*, *"Civilian"* and *"Virus"* — six sources, not one of
them a match. `asianalliance_asianmilitia` drew *"Assimilator"* and *"Civilian Male White"*.

**Coverage against quality:**

| minimum name score | assignments | actors ≥2 |
|---|--:|--:|
| none (today) | 1,850 | **448** |
| ≥ 0.60 | 1,047 | **261** |
| ≥ 0.75 | 673 | 171 |
| ≥ 0.90 | 542 | 141 |
| exact only | 449 | 122 |

### ⛔ The root cause is the missing ROLE step, not the greedy

The cascade is *name → tech tier → type → role → cost*. Measured against the corpus:

* **tech tier: unavailable in EVERY peer source.** Cameo carries `design.tech_tier`; no reference
  document has a tier column. The step is recorded as unavailable rather than silently satisfied.
* **role: available for 2 of 15 sources.** Only Document 1 (Mental Omega, CnC Reloaded) carries a
  `Role` column — 622 of 2,878 rows. DOC5 has none.
* type and cost work everywhere (cost on 86% of rows, after it was carried through from a column
  that was being dropped on read).

**So for 13 of 15 sources the cascade ranks on name and cost alone — and name plus cost cannot
tell a legitimate role analogy from a random pairing.** A name threshold would cut the junk and
also cut exactly the analogies the maintainer asked for (`asianalliance_lynxtank` ← MO's Qiling
scores low on name and is a good match).

⭐ **Which is why the ruled workflow is the answer, not a threshold.** The assignment PROPOSES; the
per-class review disposes. The table above sizes that job honestly: ~1,850 proposals, of which
roughly 800 are weak enough to strike on sight.

> ⛔ **The 448 figure must not be quoted as coverage.** Until a class has been reviewed, its
> assignment is a proposal list, and the ≥2 floor counts proposals rather than evidence.

---

## §12 — The role step, the cascade bug, and an honest coverage number (2026-09-03)

§11 left the assignment ranking on name and cost alone, because the cascade's ROLE step had data
for 2 of 15 sources. Two fixes, and one of them was a bug in my own tuple.

### §12.1 — A derived role that invents nothing

⛔ **Assigning a peer unit a Cameo class would be exactly the *"inferred and invented data that
might be wrong"* the maintainer warned about.** What is measurable — and is the method's own
machinery — is **where a unit sits in its own roster**: a scout is fast, fragile and short-ranged
*relative to its own game*, whoever made that game. So the role step compares position vectors, not
labels:

```
shape(u) = ( pct_rank(hp), pct_rank(speed), pct_rank(range), pct_rank(dps) )
           each within u's own SOURCE and own TYPE
role     = 1 − mean| shape(cameo) − shape(peer) |
```

Dimensionless on both sides, so a 12,500 HP roster and a 205 HP roster compare directly — the same
property that makes the ten relative values work at all. ⚠ Where a source carries a **real** role
column (Document 1), that is read and it wins.

### §12.2 — ⛔ THE CASCADE WAS NOT A CASCADE

A lexicographic tuple whose first key is a **near-continuous float** degenerates into *"rank by that
key alone"* — exact ties never occur, so tier, role and cost are computed and thrown away. Measured:
**38% of assignments had a role score below 0.5 while the role step ran on every one of them.**

Fixed by bucketing the name key — `4` exact · `3` prefix/alias · `2` strong · `1` shares a
distinctive word · `0` neither — which restores the stated intent: **name dominates, and the later
keys decide among names of comparable quality.**

| | before bucketing | after |
|---|--:|--:|
| median role score of what was assigned | 0.64 | **0.74** |
| assignments with a good shape (≥0.75) | 31% | **48%** |
| assignments with a different shape (<0.5) | 38% | **34%** |

### §12.3 — Confidence separates a weak FIT from thin EVIDENCE

§9.7 warned that one label for both makes the second invisible. Now emitted per assignment:

* **STRONG** — an exact/alias name, or a real name overlap backed by a matching shape
* **FAIR** — one of the two holds
* **WEAK** — neither; the greedy assigned the best of a bad field, because clause 9 forbids a blank

| | |
|---|--:|
| STRONG | **721 (39%)** |
| FAIR | 753 (41%) |
| WEAK | **378 (20%)** |

### §12.4 — ⭐ The number that can be quoted

| measure | value |
|---|--:|
| actors reaching ≥2 references of any quality | 454 |
| **actors reaching ≥2 NON-WEAK references** | **370** |
| (for comparison, before this session) | 221 |

**370 is the honest floor** — and it is still a proposal count, not evidence, until each class is
reviewed. ⚠ The residual WEAK rows are not a defect to fix: they are clause 9 working as ruled
(*"assign, but flag low-confidence"*). `asianalliance_asianmilitia` drawing *"Animal Alligator"*
from CnC Reloaded is the greedy taking the best of what was left after better-matched militia units
claimed the good candidates. **It is flagged WEAK, which is the whole point.**

---

## §13 — ⛔ FACTION ROUTING SUPERSEDES OPEN MATCHING (2026-09-04)

**Maintainer, after reviewing the `scout` sheet §9–§12 produced:** *"most of the references are
bullshit… instead of trying to match something completely unrelated we now try to map reference
faction to our cameo factions."*

**Everything in §9–§12 still describes the CASCADE — how two candidates are ranked. What changed is
the CANDIDATE SET.** A Cameo unit may now only see the reference factions its own faction is routed
to (`tools/balance/faction_routes.py`, clause 11 of the matching law). The cascade then decides
among those, exactly as before.

⛔ **The measurement that justifies it: of the 1,852 proposals the open matcher produced, 1,708
(92.2%) were cross-faction — and 599 of those carried the STRONG label.** The name score was doing
its job and answering the wrong question.

⚠ **Read [`FACTION_REFERENCE_MATRIX.md`](FACTION_REFERENCE_MATRIX.md) PART IV** for the route map,
what routing costs (447 in scope rather than 693; most units now hold ONE reference, not two), and
the extrapolation layer that covers units with no counterpart at all. This section exists so that
nobody reads §9–§12 as current practice without it.
