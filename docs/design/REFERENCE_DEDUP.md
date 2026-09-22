# Reference corpus de-duplication — one roster, one vote

**Measured 2026-09-03** by `tools/balance/lineage_dedup.py` over all three reference documents.
Every number regenerates; nothing here is hand-typed.

> ⛔ **This changes no shipped balance number.** It changes which reference sources are allowed to
> vote when the synthesis takes its geometric mean. `class_anchors.json` and Formula V2 still
> decide what Cameo ships.

**Maintainer order, 2026-09-03:** *"You need to use all the reference data and checking if the data
you have is any duplicates like for example the original TD and RA1 rules and the OpenRA rules are
identical and just scaled right? All data needs to be unique and then used as a geometric mean for
the design and then normalized to the new cameo scale."*

So de-duplication is **step 1 of the synthesis, ahead of the mean**. The geometric mean has no
defence against a roster that votes five times.

---

## §0 — The headline

⭐ **The order was right and the effect is large.** On the 128 multi-source units the RA2 lineage
touches, it casts a **median 50% of all votes** and an outright **majority on 45** of them. Giving
it one vote moves the synthesized HP target by **more than 10% on 52%** of those units, more than
25% on 29, and by up to **1.77×**.

⭐ **And it was only half applied.** The chassis layer (`reference_distribution.py`) collapsed the
RA2 lineage; the rifle layer (`synthesize_reference.py`) collapsed nothing at all, because a
2026-08-30 override — *"every source votes once, no collapsing"* — was read as covering duplicates.
It was not: that override is about not curating away sources that **disagree**. Both rules now
hold, and the rifle layer collapses too.

| | before | after |
|---|--:|--:|
| source labels in the corpus | 26 | 26 |
| voting labels, rifle layer | 25 | **19** |
| collapses applied, rifle layer | 1 (a re-extract) | **7** |
| ruled lineages | 1, applied in the chassis layer only | **2, applied in both** |
| ruled labels that matched no source | **1** (`"RA2/YR"`) | 0 |

---

## §1 — ⛔ The three copies, and the one that was broken

The rulings lived in three private lists that had drifted apart:

| where | held | defect |
|---|---|---|
| `synthesize_reference.SUPERSEDED` | 1 entry | covered a re-extract only — no lineage at all |
| `synthesize_reference.NEAR_DUPLICATES` | 6 pairs | reported, never applied |
| `reference_distribution.LINEAGE_MEMBERS` | 5 members | one member **matched no source** |

⛔ **The live bug.** `LINEAGE_MEMBERS` listed `"RA2/YR"`. The parser labels that source
`"RA2/YR (raw INI)"`, so the member never matched and voted all along — in the one list whose own
comment warned *"the value must be the label AS THE POOL SEES IT"*.

**Fixed by consolidation, not by editing the typo.** The rulings now live once, in
`tools/balance/reference_lineages.py`, read by all three consumers; `lineage_dedup.py` fails when a
ruled label is absent from the corpus, so the same typo cannot recur silently.

---

## §2 — The test, and why it is scale-free by construction

Every row is already `×rifle` — the unit's HP over its **own source's** basic rifleman — so two
rosters that are "identical and just scaled" have *identical* coordinates, not merely proportional
ones. On top of that the pair's **median ratio is divided out** before agreement is scored:

```
dev_u = (A_u / B_u) / median_v(A_v / B_v)        # 1.0 when the two agree on unit u
```

* **`w10`** — share of shared units within ±10% of the pair's own median offset.
* **`w25`** — the same at ±25%, which controls the **tail**. `w10` alone passes a pair that agrees
  on the bulk and disagrees 10× on six units, and that is a rebalance, not a copy.

**DUPLICATE** = `n ≥ 15` and `w10 ≥ 85%` and `w25 ≥ 90%`.

⚠ **The cut lands in a gap, and the gap is narrower than it looks.** The nine DUPLICATE pairs read
**91–100%**; the highest pair between sources that stay independent is
`CnC Reloaded ~ RA2/YR (raw INI)` at **83%** — so the gap is 83 → 91, clean but not wide.

⚠ **Two pairs INSIDE the RA2 lineage do not pass the test on their own** —
`OpenRA RA2 official ~ Yuri's Revenge` (88%) and `~ RA2/YR (raw INI)` (87%), both failing on `w25`.
They join the lineage through **transitivity**, and transitivity is an assumption: A~B and B~C
passing does not prove A~C. It is the right assumption for a *lineage* — descent from one roster is
transitive even when the measurement of it is noisy — but `lineage_dedup.py` prints the per-pair
table precisely so a group held together by one weak link stays visible instead of vanishing into
the union.

⚠ **The `w10` score is computed in LOG space, not as `0.9 ≤ dev ≤ 1/0.9`.** Written that way the
band is mathematically symmetric and numerically is not: the TS Stealth Tank sits exactly on it
(1.60/1.44), passing in one direction and failing in the other, so `compare(a, b)` and
`compare(b, a)` returned **96% and 93% for the same pair**. A verdict that depends on argument
order is not a measurement. Guarded by `test_the_score_does_not_depend_on_argument_order`.

⛔ **HP only, and that is a limit not a choice.** `×rifle` is the only coordinate all three source
documents carry for every row. Two mods can share HP and diverge completely on damage, so a
DUPLICATE verdict means *"the same chassis data"*, not *"the same balance"*.

---

## §3 — ⭐ The maintainer's own example, and what the corpus says

> *"the original TD and RA1 rules and the OpenRA rules are identical and just scaled"*

**Half right, and the half that is wrong is the important half.** Scale is not the issue in either
case — both pairs sit at a median offset of **exactly 1.00×** once normalised to rifle. The
question is whether they agree *after* that, and OpenRA **rebalances TD and RA1 as it ports them**:

| pair | n | offset | `w10` | verdict |
|---|--:|--:|--:|---|
| `Tiberian Sun` ~ `OpenRA Tiberian Sun` | 27 | 1.00× | **96%** | ⭐ **DUPLICATE — newly collapsed** |
| `Tiberian Dawn` ~ `OpenRA Tiberian Dawn` | 17 | 1.00× | 41% | independent — keeps its vote |
| `Red Alert 1` ~ `OpenRA Red Alert` | 23 | 1.00× | 35% | independent — keeps its vote |

The dissenters are not rounding. **TD:** Mammoth 12.0 vs 17.4× rifle, Commando 2.0 vs 3.0, Recon
Bike 3.2 vs 2.2. **RA1:** Tesla Tank 2.2 vs **8.0**, M.A.D. Tank 6.0 vs **18.0**, Submarine 2.4 vs
5.0, Hind 4.5 vs 2.0. **TS:** 26 of 27 agree within 10%, and 25 of those to three decimal places.

⭐ **So the ruling the data supports is the one the maintainer did not name:** OpenRA re-tunes TD
and RA1, and does not re-tune TS. TS is now one lineage; TD and RA1 keep two votes each.

---

## §4 — The lineages, and the one the measurement will not endorse

| lineage | members | representative | why that one |
|---|---|---|---|
| RA2 family | RA2 vanilla · Yuri's Revenge · RA2/YR (raw INI) · OpenRA RA2 official · YR on OpenRA | **Romanov's Vengeance** | maintainer ruling 2026-08-30 |
| TS family | Tiberian Sun | **OpenRA Tiberian Sun** | the live, resolvable codebase over a hand-extracted table |

⚠ **Romanov's Vengeance is elected over the lineage while measuring as a *rebalance* of it** — it
is the sole dissenter on 45% of the units the others agree on (Kirov 32× vs 16×, Aegis Cruiser
3.2× vs 6.4×, Flak Track 2.4× vs 1.4×). Electing it adopts RV's numbers rather than vanilla's
consensus. **That is the maintainer's call and it stands.** What must not happen is the code
quietly re-deriving a different answer, so `lineage_dedup.py` keeps printing the disagreement.

---

## §5 — ⚠ Partials: real overlap, below the cut, still voting

These are not collapsed, and each is a judgement worth a look before the anchors are signed:

| pair | n | offset | `w10` | reading |
|---|--:|--:|--:|---|
| `CnC Reloaded` ~ `Yuri's Revenge` | 86 | 1.00× | 81% | CnCR inherits vanilla YR HP wholesale and re-tunes a minority — 44 of 57 shared units with RA2 vanilla are **exactly** equal |
| `Valiant Shades` ~ `OpenRA RA2 official` | 70 | **0.52×** | 79% | an RA2-lineage mod at ~1.92× the scale — the closest thing in the corpus to "identical and just scaled" that still misses the cut |
| `Crystallized Nexus` ~ `OpenRA Tiberian Sun` | 61 | 1.00× | 67% | a TS-lineage mod that re-tuned a third of its roster |

⚠ **The RA2 family is still over-represented after the collapse.** Nine labels descend from one
game family — vanilla ×3, OpenRA ×2, RV, CnC Reloaded, Mental Omega, Valiant Shades — and the
collapse removes five. The remaining four are genuine rebalances and keep their votes by rule, but
any RA2-era Cameo unit is still hearing four RA2 voices against one each from TD, RA1 and TS.

---

## §6 — ⛔ A source the maintainer named that contributes nothing

**DTA is in the source table, in `DOC4_SOURCES`, and parses to ZERO rows.**

`ORIGINAL_UNIT_STATS.md` §"Dawn of the Tiberium Age" is a **15-row hand-curated Classic-vs-Enhanced
highlight table** with no `HP` column, so every row is skipped by the parser and the section reads
as present while voting on nothing. The full DTA extract went to a scratchpad CSV on a local path
(`G:\...\DTA Release\INI\Rules.ini`) and never landed in the repo.

⚠ **This is the "the tool could not look" / "the tool looked and found nothing" trap again**, and
it is worth fixing before the anchors are set: DTA is one of only three sources covering the TD +
RA1 crossover, which is exactly where OpenRA's rebalance means the originals cannot speak alone.

Of the seven sources the maintainer named on 2026-09-03, six are present and voting:

| source | rows |
|---|--:|
| Romanov's Vengeance | 494 |
| Combined Arms | 331 |
| Mental Omega | 269 |
| CnC Reloaded | 264 |
| Shattered Paradise | 262 |
| Generals Alpha | 145 |
| **DTA** | **0** ⛔ |

---

## §7 — Where this sits in the pipeline

1. **De-duplicate** the corpus → one vote per roster. ← *this document*
2. **Geometric-mean** the dimensionless coordinates across the surviving sources.
3. **Normalize** onto Cameo's own distributions (`REFERENCE_SYNTHESIS_REPORT.md`).
4. **Set each class anchor at the 100% mark** of the 100–250% target band.
5. **Fill the remaining members** relative to that anchor from the synthesized targets.

Steps 4 and 5 are PRIORITY 0 item 1 and are still open for 26 of 27 classes.

---

## §8 — Reproduce

```sh
python tools/balance/lineage_dedup.py                                    # the table + the lineages
python tools/balance/lineage_dedup.py --pair "Red Alert 1" "OpenRA Red Alert"
python tools/balance/lineage_dedup.py --all-pairs                        # incl. the independents
python tools/balance/synthesize_reference.py --dry-run                   # the collapse, applied
python -m unittest discover -s tools/tests -p "test_lineage_dedup.py"
```

---

## §9 — ⭐ The SECOND corpus, and why it needs its own verdicts (measured 2026-09-03)

`docs/reference/versus_raw.json` is a separate reference corpus of **3,150 warheads across 16
sources** — and it holds three sources the unit corpus does not: **Red Resurrection** (480
warheads), **RA2 Reborn** (176) and **all three DTA variants** (228). It carries warhead `Versus`
profiles ONLY — no unit, HP, cost, speed, damage or range — so these sources can vote on the
armour axis and cannot vote on the stat axis.

⚠ **The recorded file paths say why the stat side is missing**, and it is the DTA problem again:

```
dta_enhanced      G:\BackUp\AedisToru\Desktop\DTA\DTA Release\INI\Base\Enhance.ini
red_resurrection  C:\Users\AedisToru\Downloads\_extracted_rr\expandmd99_8218f9f4.ini
ra2_reborn        C:\Users\AedisToru\Downloads\_extracted_reborn\INI_c5d7f6ce.ini
```

All read on the maintainer's machine; only the derived Versus rows were ever committed.

### ⛔ The same source gets DIFFERENT verdicts in the two corpora

| pair | warheads | `w10` | `w25` | armour verdict | stat verdict |
|---|--:|--:|--:|---|---|
| `ra2_reborn ~ yr_vanilla` | 106 | **97%** | 98% | ⛔ **DUPLICATE** | — |
| `cnc_reloaded ~ ra2_reborn` | 109 | **87%** | 90% | ⛔ **DUPLICATE** | — |
| `cnc_reloaded ~ yr_vanilla` | 116 | 88% | 90% | partial (borderline) | — |
| `cnc_reloaded ~ romanovs_vengeance` | — | — | — | — | ⭐ **47% — independent** |
| `mental_omega ~ anything` | 65–86 | **52–66%** | — | ⭐ independent | ⭐ independent (17–33%) |
| `red_resurrection ~ anything` | 70–78 | **52–68%** | — | ⭐ independent | (no stat rows) |
| `dta_classic ~ dta_enhanced` | 17 | 38% | 57% | ⭐ genuinely different tables | — |

⭐ **CnC Reloaded is INDEPENDENT on unit stats (47%) and a NEAR-DUPLICATE on armour (88%).** A mod
can rebalance its roster while keeping vanilla's `Versus` tables almost untouched — and RA2 Reborn
does exactly that at **97%**. So a de-duplication ruling **cannot be shared between the two
corpora**: each axis needs its own verdict, from its own measurement.

⭐ **Mental Omega and Red Resurrection are independent on BOTH axes** — the maintainer's instinct
that *"Mental omega might be different enough so it justifies a unique vote"* holds twice over.

---

## §10 — New peer candidates, surveyed (2026-09-03)

⭐ **Public GitHub clones work from the working environment** (verified), so any OpenRA-based mod
can become a full source with units and weapons. Red Resurrection and RA2 Reborn cannot — they are
Ares/YR INI mods, and their data lives in MIX archives.

Four candidates cloned and resolved. `usable` = actors carrying both `Health` and `Valued`:

| candidate | actors | usable | combat | closest existing source | verdict |
|---|--:|--:|--:|---|---|
| **RA Unplugged** (`RAunplugged/uRA`) | 651 | **400** | **309** | OpenRA Red Alert — 80% / 92% | ⚠ partial, just under the cut |
| **Red Alert Plus** (`MlemandPurrs/raplusmod`) | 668 | 229 | 202 | OpenRA Red Alert — 82% / 89% | ⚠ partial, just under the cut |
| **OpenRA2 fork** (`hel1o-wor1d/OpenRA2`) | 587 | 141 | 92 | Valiant Shades — 76% / 78% | ⚠ partial |
| **Red Alert .5** (`MustaphaTR/Red-Alert-.5`) | 370 | 157 | 121 | OpenRA Red Alert — **90% / 96%** | ⛔ **DUPLICATE — must not vote** |

⭐ **The test earned its keep immediately**: Red Alert .5 is a prequel-campaign mod that reuses RA's
roster wholesale, and it would have entered the pool as a third RA voice. RA Unplugged's 309 combat
units would be the third-largest roster in the corpus after Combined Arms and Romanov's Vengeance.

⚠ All three surviving candidates sit at 76–82% against an existing source — real overlap, below the
cut. Adding them strengthens the thin TD/RA1 home set, at the cost of tilting the pool further
toward the RA lineage. **That is a maintainer call, not a measurement.**

⚠ **`extract_peer_units.extract()` still refuses a mod that has no named rifle actor** — Red Alert
Plus failed with `rifle actor e1 not present`. That is the retired transfer key blocking an
adoption the distribution method does not need one for; it has to go before any candidate lands.

---

## §11 — ⛔ RA2 and YR are ONE game, and the corpus counted them as two

**Maintainer ruling 2026-09-03:** *"RA2 and YR are the same! YR is just the add on for RA2 so if
anything only YR should be used! But Romanov's Vengeance is already YR but scaled to OpenRA! Which
means neither vanilla RA2 nor YR are needed anymore! Only Romanov's Vengeance, and of course the
other RA2 mods like cnc reloaded, mental omega, RA2 reborn and red resurrection!"*

⭐ **Confirmed by measurement before applying:** `ra2_vanilla ~ yr_vanilla` agree on **98%** of
shared Versus cells (761 cells over 79 warheads), `w25` 99%. They are one source wearing two names,
and `extract_versus.SOURCES` labelled them as two lineages — "RA2" and "YR" — so the vanilla table
counted as two independent voices in every lineage tally downstream. **Now relabelled `RA2/YR`.**

⭐ **The unit corpus already implements this ruling** — RA2 vanilla, Yuri's Revenge, RA2/YR (raw
INI), OpenRA RA2 official and YR-on-OpenRA all collapse into Romanov's Vengeance
(`reference_lineages.py`). Only the Versus corpus was still splitting them.

### ⚠ Two consequences the ruling did not anticipate

**1. Dropping the vanillas does NOT remove vanilla's armour table from the pool.**

| pair | warheads | `w10` | `w25` |
|---|--:|--:|--:|
| `ra2_reborn ~ yr_vanilla` | 106 | **97%** | 98% |
| `ra2_reborn ~ ra2_vanilla` | 69 | **94%** | 95% |
| `cnc_reloaded ~ ra2_reborn` | 109 | **87%** | 90% |
| `cnc_reloaded ~ yr_vanilla` | 116 | 88% | 90% |

**RA2 Reborn *is* vanilla YR's armour table**, and CnC Reloaded is close behind. At the 85% cut the
transitive group is `{ra2_vanilla, yr_vanilla, ra2_reborn, cnc_reloaded}` — **one voice, four
labels.** So removing the two vanillas leaves vanilla's data still voting, under RA2 Reborn's name.

⚠ Note this does NOT contradict §9: CnC Reloaded is **independent on unit stats** (47% against
Romanov's Vengeance) and a **near-duplicate on armour**. Same source, different verdict per axis.

**2. "Romanov's Vengeance is already YR" cannot be verified on the armour axis.** RV shares
**ZERO** warhead names with any INI source — it names warheads by calibre (`105mm`, `120mmxrad`,
`155mm`) where the Westwood mods name them by role (`ap`, `antiperson`, `artyhe`). It is an OpenRA
reimplementation with an entirely different warhead vocabulary, so whether it carries vanilla's
profile or its own **cannot be told from the data**. It keeps its vote by default, not by evidence.

**So the honest post-ruling picture of the armour axis is four voices, not five:**

| voice | sources | status |
|---|---|---|
| vanilla RA2/YR | `ra2_vanilla` · `yr_vanilla` · `ra2_reborn` · `cnc_reloaded` | 84–98% mutually — **needs a representative** |
| Mental Omega | `mental_omega` (731) | ⭐ independent, 52–66% |
| Red Resurrection | `red_resurrection` (480) | ⭐ independent, 52–68% |
| Romanov's Vengeance | `romanovs_vengeance` (148) | ⚠ unverifiable — 0 shared names |

### ⛔ What this broke, and what survives

`aggregate_archetype.py` published, in seven places in `WARHEAD_REFERENCE.md`:

> *"For AP that is not a data error — **six independent RA2-lineage mods** all write
> `none 25 · flak 25 · plate 15`."*

**That count was an overcount of exactly the kind this ruling exposes.** Four of the six are one
voice. Corrected to **three independent RA2/YR voices** in the tool and in all seven places.

⭐ **The finding itself survives at reduced strength** — three independent voices agreeing is still
evidence that the plate inversion is Westwood's design rather than one mod's quirk, so
`lawful_profile`'s reason for existing is unchanged. It is the *strength* claim that was wrong, and
it was wrong because the corpus split one game into two.

⚠ **`versus_raw.json`'s committed `lineage` fields are now stale** — `extract_versus.py` reads from
paths on the maintainer's machine and cannot re-run here, so the relabel takes effect on the next
extraction. The measurements above read the warhead rows directly and are unaffected.
