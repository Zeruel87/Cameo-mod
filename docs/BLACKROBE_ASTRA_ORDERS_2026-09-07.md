# ORDERS — Codex / GPT-6 Astra · 2026-09-07

**From Claude-Local (Opus 5), fleet coordinator, at the maintainer's order.**
**This supersedes the two copies that lived outside the repo** (`Cameo-mod-fleet/ORDERS_2026-09-07_codex*.md`).
It lives in the repository on purpose: it must be readable by you from a cold start, with no one
to hand you a file. Companion documents: `docs/BLACKROBE_ASTRA_BRIEF.md` (your standing brief),
`docs/HANDOFF.md` (verified state), `docs/design/BALANCE_PROGRAM_PLAN.md` (the board and §0a's
binding order of operations).

> **How to use this document.** §1 is absolute and comes before everything. §3 is the ownership
> map — breaking it costs another agent a day. §4 is your lane and it is large on purpose: it is
> the single thing standing between this project and its first applied balance number, and it is
> measurement and reconciliation work, which is what you are good at. §5–§8 are real follow-on
> work, ordered. Do not start §8 before §4 is signed. **§9 is the maintainer's two open pull
> requests and should be done EARLY — one finding there is time-sensitive.** §10 is everything the
> fleet has started and cannot land on its own; it is analysis and reconciliation, never conversion.
> 42 numbered tasks, C1–C42. **⛔⛔ §14 (2026-09-08b) OVERRIDES the deliverable of every task here: a task is DONE when CODE
> lands on master, boot-gated, with a test. Read §14 and §13 FIRST. §13 records what
> your PR review changed in this document; §14 is the priority order, the balance-pipeline code, the
> bot modules, and the RA2/TS maps.** — (§13 also — the maintainer's decision on the PRs and your order of work from here.)
>
> Every number below was measured on master `545ff414a` on 2026-09-07 with the command shown
> beside it. Re-measure before you rely on any of them — that is the house rule, not a courtesy.

---

## 1. ⛔⛔ SUPERWEAPONS ARE NEVER TOUCHED

Maintainer, verbatim, 2026-09-07:

> *"exclude super weapons from this balance formula since they are all fixed HP! NEVER CHANGE
> THEM!! SO EXCLUDE THEM BEFORE ANYTHING IS CHANGED ON ACCIDENT!!!"*

32 actors are gated on `~techlevel.superweapons` (or a `_swlimit` negation), and every one whose
HP is recorded holds **exactly 1,000,000**. That uniformity is the tell: it is a deliberate
constant, not a balance figure. A pipeline that treated it as a stat to normalise would drag it
toward a building average and quietly destroy it.

Two locks exist:

* `reference_distribution.cameo_rows()` drops them from the priced population;
* `apply_balance` **refuses** — not skips — a ledger edit that touches one.

**Do not weaken, bypass, or "improve" either lock.** If a task appears to need a superweapon's
stats, that is the signal to stop and write the question down, not to route around the guard.

Regression coverage is `SuperweaponLockTests` in `tools/tests/test_apply_balance.py`. It asserts
**both** directions. Keep it that way — see §2.

---

## 1a. ⛔ THE BLOCKER CHAIN — why the pipeline is stopped, in order

Read this before §4. Everything in your lane sits behind it, and §0a of
`docs/design/BALANCE_PROGRAM_PLAN.md` is binding: **weapon STRUCTURE comes before pricing.**
Changing a weapon's armor profile moves `K` even when total damage is preserved, so a price
computed today against a weapon that is about to be split is a number that will have to be
recomputed. All figures measured on master, 2026-09-07.

```
  W24  one damage warhead per weapon      322 weapons still stack 2+ mains   (NOVA)
  W23  retrofit the legacy templates      122 templates outside ^Warhead_*   (NOVA)
                                          1596 weapons inherit them directly
  A5   Versus only in ^Warhead_*          those same 122 are live rule violations
  W11  class anchors signed                 0 of 27                          (YOU)
  ->   pricing                            apply_balance: 0 values would change
```

### B1 — W24 is the front, and it is NOT yours

`python tools/audit/audit_three_way_split.py`:

```
   1728  correct — exactly one main warhead
    317  none — utility / effect-only weapons
    322  STACKS — all debt (the intentional_composites exemption was DELETED 2026-09-06, §11b.1)

  mains  weapons          2:197   3:77   4:23   5:11   6:5   7:8   8:1
```

**NOVA owns every conversion.** You may report, count and cross-reference; you may not convert a
single weapon. What it means for you is §4's rule: `dps0` is excluded from every dossier because
DPS is the stat W24 moves.

### B2 — ⚠ TWO AUDITS DISAGREE ABOUT THE SAME LAW, AND NOBODY HAS RECONCILED THEM

`audit_three_way_split` reports **322** weapons with more than one resolved main.
`audit_weapon_shape` check **W5**, the same law, reports **389** — on a SMALLER corpus (2,061
concrete weapons with inherits, against 2,367 scanned). A smaller corpus finding 67 MORE
violations is not a rounding difference; one of the two definitions is wrong, or one is counting
something the other deliberately excludes (the `*Percentage` / `*FriendlyFire` / `*ExtraDamage`
halves of a single main are the obvious suspect).

**This is yours, and it is high value for one day's work.** It is the `A 0% row is a bug in the
CHECK` class: a ratchet nobody trusts is a ratchet nobody lowers, and W24's whole progress is
measured through these two numbers. Deliverable: which definition is correct, the exact set of 67,
and a one-line note in both scripts saying what each counts and why they differ. ⛔ Do not silently
change either ratchet — report first.

### B3 — The `weapon_shape` ratchets are the real size of the structural debt

```
| W1 | more than 3 inherits                | 576 |
| W2 | two or more ^Warhead_*  inherits    | 210 |
| W3 | two or more ^Projectile_* inherits  |  12 |
| W4 | two or more ^Effect_*   inherits    |  51 |
| W5 | more than one resolved MAIN warhead | 389 |
| W6 | effect warheads declared LOCALLY    | 694 |
```

⚠ **W3 is the dangerous one despite being the smallest.** A weapon inheriting TWO `^Projectile_*`
templates merges into ONE node whose TYPE is the last template's and whose FIELDS are the union of
both — the engine drops nothing and warns about nothing. Twelve weapons are currently in that
state. Flag them by name in your report; NOVA fixes them.

The I7 informational rows (1,244 with no `^Effect_*`, 1,362 with no `^Projectile_*`, 1,156 with no
`^Warhead_*`) are a REVIEW QUEUE, not a defect count — an instant or utility weapon may legitimately
have no projectile. **Do not ratchet I7.**

### B4 — 1,090 weapons cannot even be judged yet

`audit_tier_weapon_class`: 43 of 1,063 classifiable weapons break the TYPES × LEVELS budget — but
**1,090 more are skipped entirely** because at least one main warhead still carries a LEGACY name
with no `Family_Level`, so the budget is unjudgeable until they are 3-way split.

That is the single clearest statement of why pricing waits: **a bit over half the arsenal has no
readable weapon class at all.** Quote this number in your dossiers wherever a class's `K` inputs
are not yet stable.

⛔ And remember the rule that nearly cost 79 correct weapons: **two ADJACENT levels of one family
is LEGAL** — it encodes a between-tier unit. The budget is TYPES × LEVELS with a ceiling of 4.

### B5 — `FieldLoader` drops unknown yaml fields in SILENCE

`FieldLoader.Load` iterates the TYPE's fields and never reads the leftover keys, and both traits
and warheads go through it. A misplaced field therefore costs nothing at boot and everything in
play. Currently live (`audit_dead_warhead_fields.py`, a LOWER-ONLY ratchet):

```
  37 weapons  OpenToppedDamage.Falloff       6 weapons  FireShrapnel.TargetActorCenter
  10 weapons  DetachDelayedWeapon.Spread     4 weapons  AffectsIntegrity.Falloff
  10 weapons  DetachDelayedWeapon.Falloff    3 weapons  FireFragment.AimChance
```

⚠ If you ever build a field set from C# source, match `public`, **not** `public readonly` — some
AS warheads declare mutable public fields, and matching the stricter pattern under-reports.

### B6 — What this means for YOUR lane, concretely

* You cannot unblock W24/W23/A5. Do not try; NOVA owns them and five-way collisions are how this
  week was lost.
* You CAN unblock W11, and it is the only one of the five that is pure measurement.
* B2 is yours and it is worth doing early: it makes the two numbers everyone quotes about W24
  trustworthy.
* Everywhere a dossier's inputs depend on a weapon in the 322 or the 1,090, say so in that
  dossier's §6 and mark the class `NOT READY (W24)` rather than guessing.

---

## 2. What your work bought, measured — and one bug I put in your file

Your writer hardening is genuinely careful: preflight, source/proposal provenance, shared-consumer
checks, engine-typed scalar and cadence validation, staged extraction, recovery that preserves
detected external edits. 933 Python tests, 70 C# tests, 33 ledgers at zero drift.

Measured on master, 2026-09-07:

```
class_anchors.json                              27 classes defined, signed_off: 0
apply_balance.py --faction <any>                DRY RUN: 0 values would change
```

**The pipeline has never been blocked on the writer's safety.** It is blocked because the ledger
holds no target numbers. Every additional guard is a stronger gate on a road with no traffic.

PR #328 was **99 documentation files, +104,391 lines, zero code**, mostly regenerated audit
reports. A diff that size cannot be reviewed, so in practice it is not reviewed. See §11.

One duplication, which was my failure as coordinator and not yours: you built
`CameoMatchLog`/`CameoMatchRecorder` while the fleet built `AiMatchLogWriter`. Yours was deleted.
You were not told what was in flight. **Ask before building anything larger than a day.**

### ⚠ And a bug I introduced into your file, so you neither trip over it nor repeat it

The superweapon lock I added to `apply_balance.py` on 2026-09-07 was written as:

```python
if _is_superweapon(ru) and changed_paths(before, after):
```

`changed_paths` is a **generator function**, so that tests a generator *object* — truthy even when
it yields nothing. The lock fired on every superweapon row whether the ledger had touched it or
not, and `--faction tiberiandawn_gdi` reported `REFUSED: 1 problem(s)` on a tree with **zero**
pending edits. Every faction shipping a superweapon was permanently unappliable — the guard was an
outage. Fixed in `545ff414a` with `any(...)` and pinned by two tests.

The general form is worth carrying: **a guard that can never pass is indistinguishable from a
guard that works, until someone runs it on a clean tree.** Every new refusal you write needs a
test proving it PASSES on the negative case, not only that it fires on the positive one.

---

## 3. Ownership map — what you may and may not touch

**Yours.**
`tools/balance/apply_balance.py` · `apply_transaction.py` · `anchor_readiness.py` ·
`extract_stats.py` · `fit_class.py` · `formula.py` · `check_band.py` · `class_membership.py` ·
`docs/balance/class_anchors.json` (spec fields only — never `signed_off`) ·
`docs/balance/anchor_decisions_log.md` · `docs/balance/formula_v2_*.md` · your own tests.

**⛔ NOT yours — the fleet's reference tree.** `tools/reference/**`,
`tools/balance/assign_references.py`, `reference_distribution.py`, `reference_targets.py`,
`faction_routes.py`, `build_reference_report.py`, `docs/reference/**`,
`docs/balance/derived/reference_*.json`. Five agents were colliding in there this week. Read the
committed JSON; do not edit the producers. If you need a field the corpus does not carry, write
the request down and hand it to me.

**⛔ NOT yours — weapons.** `mods/cameo/**/weapons.yaml` and the `^Warhead_*` / `^Projectile_*`
templates belong to NOVA under W24. `Versus` lives ONLY in `^Warhead_*` templates, and no warhead,
`Burst` or `BurstDelays` changes without explicit maintainer permission.

**⛔ Never.** `signed_off: true` on any anchor. `apply_balance --confirm`. Any hand-edited balance
number in yaml. All three require a maintainer order that is not in this document.

---

## 4. YOUR LANE — make the 27 anchors signable

The maintainer must be able to sign or reject each class **in one pass**. That means one dossier
per class, in a fixed shape, with the evidence attached and the disagreements stated rather than
smoothed away.

### The measured starting position

`python tools/balance/anchor_readiness.py`, master, 2026-09-07:

```
classes defined                                   27
signed off                                         0
anchors tagged into the class they anchor      27 of 27
classified rows (excl. structures/upgrades)   635 of 886  (71.7%)
buildable rows with NO defined class              199
buildable rows with no unit template               52
anchor actor OFF its ruled spec                23 of 27
satisfying the baseline identity o0=p0=q0=cost0  0 of 27
missing a fitted cost baseline                     25
classes with LOW pricing residuals                  0     (26 need review, 1 unfittable)
median distance to OWN anchor                    3.18
median distance BETWEEN anchors                  1.21
class-tagged members still firing 2+ main warheads 89
```

Read the last two lines together before you touch anything. **Units sit further from their own
class anchor than the anchors sit from each other.** The class boundaries are therefore *not*
recoverable from stats — they are role judgements, and any check that tries to police membership
numerically will be wrong. `anchor_readiness` already says this; believe it.

### C1 — Build the dossier generator before you write a single dossier

`tools/balance/propose_anchor_spec.py`, **read-only**. It must not write yaml, must not write
`class_anchors.json`, and must not set `signed_off`. Given `--class <name>` it emits one Markdown
dossier to stdout (and with `--all`, one file per class under `docs/balance/anchors/`).

Reason: 27 hand-written dossiers will drift in shape by the fifth one, and the maintainer's review
cost is dominated by inconsistency. Generate the skeleton, then write the judgement into it.

### C2 — The dossier shape, fixed for all 27

Each dossier carries exactly these sections, in this order:

1. **The proposal.** `hp0`, `speed0`, `range0_wdist`, `cost0`. Four numbers, on the nice-number
   grid (`docs/DESIGN.md`, the nice-number law).
2. **⛔ NOT `dps0`.** DPS moves under W24, and pricing an input that is about to change is how a
   ledger rots. If a class's identity genuinely depends on DPS, say so in §6 of the dossier and
   leave the number alone.
3. **The anchor actor and the verifier actor**, each with its live yaml stats and its ledger row,
   and the ratio between them. The 2×/2×/2.5× verifier identity only holds when baseline and
   verifier share a TechTier bucket **and** `K` — check it and say which.
4. **Membership.** Every Cameo actor in the class, with `hp / speed / range / cost` as it ships
   today, sorted by cost. Mark each row `REF` if it holds a STRONG or FAIR reference, `FORMULA` if
   it has none.
5. **The reference consensus**, for the `REF` rows only, from
   `docs/balance/derived/reference_assignment.json` and `reference_targets`. Name the source rows
   by **id**, never by name alone — Combined Arms ships two rows called "Mammoth Tank".
6. **Every disagreement with live yaml, with the size of the gap.** `mbt` spec `hp0` is 240,000
   against 100,000 live; `line_breaker` is 750,000 against 100,000. These gaps are the entire
   point of the review. Do not smooth them.
7. **One line: what would have to be true for this number to be wrong.** If you cannot write that
   line, the number is not ready and the dossier says `NOT READY` at the top.

### C3 — Pilot on the four classes whose anchor is already on spec

`closecombat`, `commando`, `rocket_trooper`, `special_forces` are the only four whose anchor actor
matches its ruled stats today. Do these first, get them in front of the maintainer, and let the
review shape the template before you spend 23 more.

### C4 — ⚠ `commando`'s anchor is a hero, and heroes are invisible to the population

`commando`'s anchor actor is `td_gdi_commando`, which carries a `BuildLimit`. The POPULATION RULE
(maintainer, 2026-08-30) excludes every build-limited actor from `cameo_rows()`, so **the commando
anchor cannot be validated against a population at all** — 83 Cameo hero/epic combat rows sit
outside every distribution. The maintainer ruled on 2026-09-07 that heroes get a **hero-only
reference lane** (they stay out of the ordinary distributions and match only other heroes); the
fleet implements that, not you. Your job is to **flag it in the dossier** so the class is never
signed on evidence that does not exist.

### C5 — Explain the "unavailable" fitted cost baseline, 25 of 27

Only `mbt` (1.00×) and `line_breaker` (0.50×) produce a fitted `cost0`. The other 25 report
`unavailable`. Find out why — missing `o0/p0/q0`, a member count below the fit floor, or an input
the extractor never filled? Report the cause per class. **This is a measurement task, not a fix
task**: do not paper over it by inventing a baseline.

### C6 — Explain the baseline identity failing 27 of 27

`o0 = p0 = q0 = cost0` holds at the baseline by construction in Formula V2 (`FORMULA_V2.md`,
`docs/DESIGN.md` §12). **Zero of 27 classes satisfy it.** For each class say which of the two
possible causes applies, with evidence:

* the anchor actor drifted off the ruled spec and step 2c of the decisions log's application law
  (restat the baseline actors to the table) has never run — 23 classes are candidates; or
* the ruled spec itself is wrong.

They need different fixes and only the maintainer can choose. Present the choice; do not make it.

### C7 — The `support` class cannot be fitted at all

`support`: 0 scored members, anchor `engineer`, `dps0` 0, `range0_wdist` unavailable, and 115
tagged members — the largest class in the game. `anchor_readiness` reports
`⛔ not fitted — no anchor, or the anchor has no stats`. Diagnose it. The maintainer has already
ruled that support units and harvesters need **only HP and Speed** extracted (2026-09-07,
*"they don't have a weapon right? Aside from the RA2 war miner of course"*), so a class of unarmed
units failing a DPS-bearing fit may be correct behaviour badly reported rather than a defect.
Say which.

### C8 — The 8 statistically indistinguishable anchor pairs

```
0.024  anti_air_vehicle <-> missile_vehicle      0.063  archer <-> special_forces
0.048  archer <-> flying_infantry               0.072  flying_infantry <-> special_forces
0.053  rocket_trooper <-> special_forces        0.076  heavy_sniper <-> mortar
0.055  missile_vehicle <-> tank_destroyer       0.092  pure_sniper <-> rocket_trooper
```

These are separated by **what they shoot at**, not by their stats. For each pair, write the role
test in one sentence a human can apply ("hits air and only air", "arcs over obstacles"). That
sentence is what membership is policed by; no numeric check can do it. Put the eight sentences in
`docs/balance/formula_v2_classes.md`.

### C9 — Anchors at extreme member percentiles

17 anchors sit outside the middle half of their class's HP distribution — `scout_vehicle` at the
4th percentile of 52 members, `artillery` and `pure_sniper` at the 6th. **This is descriptive, not
a failure.** The intended anchor is a typical *entry* unit, not the median.
⛔ **Do not move an anchor on a percentile alone.** For each of the 17, recommend keep-or-move with
a role reason, and mark it `KEEP (by design)` where the low percentile is exactly what an entry
unit should look like.

### C10 — Per-class TechTier confirmation

Every anchor carries `tech_tier_flag: "DEFAULT 1.0 — per-class tier needs confirmation
(high_tech/dreadnought/epic likely 0.75/0.5)"`. Confirm or challenge the default per class, and
remember the binding constraint: **baseline and verifier must share the tier bucket and `K`**, or
the 2.5× identity breaks. Epics are `UnitClass L = 0.3, TechTier M = 1.0` regardless of actual
tier (DESIGN.md, design 2026-07-11) and are never re-discounted when tiers move.

### C11 — Cross-check every proposed number against the nice-number law

HP in clean steps, speed on the step-1 grid, damage on the **100** grid
(`formula.DAMAGE_STEP = 100`, W15). ⚠ Older documents teach a 2,000-step damage grid plus a
`FirepowerMultiplier` fine-tune; **that is a retired law** — W17 retired FP as a pricing knob,
`apply_balance` cannot write it, and `propose_class_rebalance.decompose_dps` always solves at
`fp = 1.0`. If you find a live document still teaching it, fix the document in the same commit.

### C12 — Deliverable and done-when

**Deliverable:** `docs/balance/anchors/<class>.md` × 27, plus a one-page index
`docs/balance/anchors/README.md` with a 27-row table: class · proposed hp0/speed0/range0/cost0 ·
members · `REF` members · residual · READY / NOT READY · the one-line "what would make this wrong".

**Done when:** all 27 dossiers exist, the index is complete, `anchor_readiness.py` runs clean, and
**not one `signed_off` has been changed.** You are preparing specs for signature, not signing them.

---

## 5. Membership — the 251 rows that have no class

### ⛔ BEFORE C13 AND C14 — THE FLEET ALREADY DID BOTH, AND NEITHER LANDED

I nearly had you redo a week of someone else's work. Read these branches FIRST:

| branch | what is on it |
|---|---|
| `devin/aurora/lane5-proposal` | `docs(lane5): air/naval/economy class proposal for 268 unclassed units` |
| `devin/ember/lane5-classes` | `docs(lane5): air/naval/economy class proposal + 39-tag analysis` — a SECOND proposal for the same units |
| `devin/aurora/lane4-templates` and `-v2` | `balance(lane4): classify 97 units with no unit template` — same 29-file set on both branches |
| `devin/aurora/fix-anchor-readiness` | `fix(tools): anchor_readiness.py crash from deleted intentional_composites` + `balance(lane4): classify 9 no-template units + fix extract_stats preservation` |

⚠ **The last row is in YOUR file-set** — `anchor_readiness.py` and `extract_stats.py`. Read it
before you touch either, or you will collide with AURORA exactly the way five agents collided in
the reference tree this week.

⚠ And the counts disagree with mine: they say **268** unclassed and **97** without a template;
`anchor_readiness` on master today says **199** and **52**. Reconciling that difference is part of
the task — it is either progress since those branches were cut, or a different definition, and you
must say which before you use either number.

### C13 — The 199 buildable rows with no defined class

**Start from AURORA's and EMBER's two competing proposals, not from scratch.** Reconcile them: where
they agree, that is the proposal; where they disagree, present both readings with the role reason
for each and let the maintainer pick. Then produce `docs/balance/anchors/unclassified.md`: every row, its faction, section, hp/speed/cost, and
a **proposed** class with a one-line role reason. Group by proposed class so the maintainer reviews
a class at a time. Flag anything you cannot place at all as `NEEDS RULING`, with the question
written out.

### C14 — The 52 buildable rows with no unit template

**AURORA classified 97 of these on `lane4-templates`; take that branch as the starting point.**
These are rows the extractor sees but that inherit no `^*Template`. Establish whether each is (a) a
genuine gap, (b) an actor that should not be in a combat section, or (c) an extraction defect.
Report counts per cause before proposing any change.

### C15 — Do NOT build a numeric membership checker

`anchor_readiness` already proves why: median distance to own anchor 3.18, between anchors 1.21.
Any stat-based membership police will be wrong more often than right. Membership is a role
judgement recorded in `design.class_anchor`. If you want a check, check that every buildable combat
row **has** a class — never that its stats justify the one it has.

---

## 6. The §0a gate — weapon structure before pricing

`docs/design/BALANCE_PROGRAM_PLAN.md` §0a is binding: **weapon structure comes before pricing.**
Changing armor profiles can move `K` even when total damage is preserved, so a class whose anchor
still fires stacked mains cannot be priced yet.

### C16 — The blocked list

89 class-tagged members still resolve to 2+ main warheads. Worst offenders by class:

| class | stacked | of tagged | largest stack |
|---|--:|--:|---|
| `artillery` | 10 | 35 | `ra1_soviets_v2rocketlauncher` via `SCUDThermobaric` (5 mains) |
| `scout_vehicle` | 10 | 52 | `ordos_raider` via `HMGo_upgrade` (3) |
| `commando` | 9 | 30 | `asianalliance_asiancommando` via `AsianSniperLockdown` (6) |
| `mbt` | 7 | 51 | `ordos_combatautoguntank` via `autogun_tank_small` (3) |
| `melee` | 5 | 49 | `futuretech_enforcer` via `FutureEnforcerShotgun` (5) |
| `high_tech_tank` | 5 | 26 | `duelist_tank.ixian` via `DuelistTankCannon` (5) |
| `epic_vehicle` | 5 | 24 | `tkm_bigshiee` via `SandmarineTuskTwin` (5) |

Only `dreadnought`, `flying_infantry`, `mortar` and `scout` have no stacked-main finding — and that
is **not** weapon-structure clearance, only the absence of this one finding.

### C17 — The rule that matters for your lane

**A class must not be marked READY while its ANCHOR or its VERIFIER is one of the 89.** Check those
54 actors specifically and list which classes are blocked by their own baseline. That is a much
smaller and much more decision-relevant list than the 89.

⛔ A stacked main is a **finding, not an automatic collapse** — some are reviewed composites. NOVA
owns the conversions under W24. You report; you do not convert.

---

## 7. Ledger and tooling health

### C18 — Re-extract before every commit that moves a balance number

`audit_balance_drift` fails red whenever yaml and the committed ledger disagree. It has gone red
twice because yaml commits landed without a re-extract. Re-extract at the point of change, not at
the end of a session.

### C19 — `release_drift` D4: 335 weapons in the shipped release, gone under that name

```
D1 INFLATED 131 · D2 WEAKENED 62 · D3 EXTREME 27 · D4 UNMATCHED 335 · D5 ACCEPTED 42
```

All are at ratchet and PASS, so nothing is failing — but **D4 is the interesting one and nobody has
read it.** 335 names that existed in the build players actually played no longer exist. Some are
renames from the consolidations, some are genuine deletions. Classify them: `RENAMED -> <new>`,
`MERGED INTO <weapon>`, or `DELETED`. A rename is harmless; a deletion of something a player used
is a regression nobody has looked at. Report counts per class before proposing anything.

### C20 — `doc_claims`: pin the numbers this document rests on

`tools/audit/audit_doc_claims.py` + `docs/audit/doc_claims.yaml` hold every numeric claim a
DECISION rests on, with its re-measure command. Add the §4 starting-position numbers (27/0,
23-of-27, 0-of-27, 89, 199, 52). When a claim legitimately changes, update `value` **and every doc
listed under `docs:` in the same commit**.

### C21 — The legacy workbook triage (`docs/balance/discrepancies.md`)

`docs/design/cameo_armor_system.xlsx` stays the reference for design judgements until the Phase-3
discrepancy triage completes. The report lists legacy rows with no matching actor —
`Minigunner (AP Bullets)`, `Rocket Soldier TD`, `Dune Rocket Trooper`, `Terran Marine` and dozens
more. Each is either a rename (extend `name_map.yaml`) or a genuinely dead row. Clearing it is what
lets the legacy workbook be retired. ⚠ If `~$cameo_armor_system.xlsx` exists, the workbook is open
in Excel: do not write it — queue it and say so.

### C22 — A test for every refusal you own

Sweep `apply_balance.py` for every `problems.append(...)` and confirm each has a test asserting
**both** that it fires on the positive case and that it does **not** fire on the negative one. §2
is why. Report the list with a ✓/✗ per refusal before writing any new tests.

---

## 8. The faction calibration — Japan first. ⛔ NOT BEFORE §4 IS SIGNED

### C23 — READ `tools/balance/faction_extrapolate.py` FIRST. It already exists.

504 lines, and it already implements the method: the **exchange rate**
`k = geometric mean over pairs of (cameo_stat / reference_stat)` per route and per stat; unpaired
reference rows becoming virtual members at Cameo scale; and a `--report` mode that measures the
roster mismatch in both directions (447 routed Cameo units · 325 paired · 557 reference rows
unused). It imports `reference_distribution`'s aggregates rather than reimplementing them.

**Do not rebuild it.** This is exactly the failure `docs/TASK_INDEX.md` exists to prevent — a
virtual-anchor mechanism was once re-designed when `fit_class.py --spec` already implemented it.
Read it, run `--report`, and write down what it does NOT yet do.

### C24 — The method, once anchors are signed

1. Per faction per stat, compute the calibration factor from the units that HAVE trustworthy
   references.
2. Place each expansion unit from **class anchor × tech tier × faction factor**.
3. Let the formula compute the price from the placed stats, as it always has.

### C25 — Japan is the test case, by maintainer request

> *"I think we should add Japan even right now and just extrapolate all their stats from what we
> have so far! ... we can extrapolate the data to our japanese units now as a test to see how well
> that works!"*

Japan has **no reference data at all**, which is the point: if extrapolation produces a sane
Japanese roster, it works for every expansion unit in the game. Produce the proposed roster as a
**report**, not as a ledger edit. The maintainer looks at it and says yes or no.

### C26 — The magnitude of the faction identity modifier has never been set

There is no ruled number for how far a faction may sit from the class anchor. Propose a range with
evidence from the paired units, and mark it `NEEDS RULING`. Do not pick it yourself.

---

## 9. The maintainer's two open pull requests — #325 and #321

Maintainer, 2026-09-07:

> *"if you have time can you review my two open pull requests #325 and #321?"*

Do this **early** — ahead of §5 onward — because one finding below is time-sensitive and the rest
of your lane does not depend on it.

* https://github.com/cameo-mod/Cameo-mod/pull/325 — "Bot insurance rewrite + the high-DPI flag bug"
* https://github.com/cameo-mod/Cameo-mod/pull/321 — "balance pipeline: stat grids, converter fixes, W24 batch prep, and two guard hooks"

### C27 — ⛔ Start from these three measurements, because they change what the review IS

```
git rev-parse origin/claude/bot_insurance_dynamic_trait     -> e42eb9914...
git rev-parse origin/claude/docs-audit-reorganize-xgzwhr    -> e42eb9914...   THE SAME COMMIT
git rev-list --left-right --count origin/master...e42eb9914 -> 405   155
git diff --stat 4deaee086 e42eb9914                         -> 250 files, +130904, -2872
```

**1. #325 and #321 are the same branch content under two names.** Both PR heads resolve to the
identical commit `e42eb9914`, both show 250 files / +130,904 / −2,872, and both were last updated
in the same second. Two different titles, one diff. Whichever is reviewed, the other is a
duplicate — say so first, before any line-level comment.

**2. They are 405 commits behind master and diverged at `4deaee086` ("Add archon merging").** The
diff is measured against that ancient merge base, which is why it looks enormous.

**3. ⚠ CORRECTED 2026-09-08 — ASTRA WAS RIGHT AND THIS SECTION WAS TOO STRONG.**

What this document originally said: *"merging either one as-is would DELETE the superweapon lock."*
That is overstated, and Astra caught it. Re-measured against the same SHAs:

```
git merge-tree --write-tree --name-only 4328e6818 e42eb9914   ->  exit 1, 72 conflicting paths
  tools/balance/reference_distribution.py   CONFLICT (add/add)   <- it CONFLICTS, it does not
                                                                    silently take the branch side
  docs/balance/class_anchors.json           Auto-merging         <- CLEAN
```

`reference_distribution.py` conflicts, so a merge stops and a human resolves it. **A correct
resolution keeps the superweapon exclusion.** The real risk is blanket branch-side conflict
resolution, not the merge itself. Branch age is not by itself proof of a regression. The rest of
the table below is still accurate and still the reason a wholesale copy is dangerous:

**3b. ⛔⛔ AND THE ACTUAL SILENT REGRESSION IS THE ONE THAT MERGES CLEANLY.** Astra found it and it
is a better finding than mine: `docs/balance/class_anchors.json` **auto-merges with no conflict**,
and the merged result carries **eight `signed_off: true`** where master has zero —

```
archer · closecombat · flying_infantry · grenadier · heavy_sniper · missile_vehicle · mortar · special_forces
```

Verified independently: `git cat-file -p <merge-tree>:docs/balance/class_anchors.json` returns
exactly those eight. §3 of this document forbids you to set a single one of them, and a clean
merge would set eight without a conflict marker to warn anyone. **A file that conflicts is safer
than a file that does not** — the conflict is the warning. That inversion is the finding worth
carrying out of this review.

The line-count table below stands, and is why no file here may be taken wholesale:

| marker | on the PR branch | on master |
|---|--:|--:|
| `SUPERWEAPON_TOKENS` / `is_superweapon` (`reference_distribution.py`) | **0** | 2 |
| `ORIGINAL_NAME_FLOOR` (originals claim first) | **0** | 3 |
| `REFERENCE_OVERRIDES` | **0** | 2 |
| `tools/balance/assign_references.py` | 507 lines | **948** |
| `tools/balance/reference_distribution.py` | 751 lines | **970** |
| `tools/reference/extract_peer_units.py` | 626 lines | **733** |

The branch carries an OLDER copy of the entire reference pipeline. A merge that takes the branch
side on any of those files silently reverts the superweapon exclusion the maintainer declared
absolute on 2026-09-07, plus every reference fix from three review rounds. **This is the headline
of your review.**

### C28 — What the review must actually deliver

Not a line-by-line pass over 130,904 lines — that is not reviewable, and pretending otherwise is
how #328 happened. Deliver:

1. **The duplicate finding and the supersession finding, up front**, with the commands above so
   the maintainer can re-run them in ten seconds.
2. **A salvage list.** Work on that branch that is genuinely NOT on master and is still wanted.
   `OpenRA.Mods.Cameo/Traits/DynamicBotInsurance.cs` (631 lines) and the high-DPI flag fix are the
   obvious candidates — check whether each already landed by another route before listing it. For
   each: does master have it, and if not, is it still correct against today's code?
3. **A recommendation per PR**, one sentence each, from exactly three options: *close as
   superseded*, *close and re-open a small PR carrying only the salvage list*, or *rebase onto
   master* — and if you say rebase, say how many conflicts you MEASURED, not how many you expect.
4. **⛔ Do not merge, close, or force-push anything.** These are the maintainer's PRs. You write
   the review; they decide.

### C29 — The general lesson to write into the review

A PR whose diff is measured against a 405-commit-old base is not a proposal, it is an
archaeological record. **The reviewable unit is `git diff origin/master...HEAD` on a rebased
branch, and nothing else.** Recommend a house rule: any PR more than ~50 commits behind master gets
rebased before review, or gets closed and re-cut. Put the sentence in `docs/AGENT_WORKSPACE.md` if
the maintainer agrees.

---

## 10. What the fleet has started and cannot finish alone

Maintainer, 2026-09-07: *"add many more things that codex needs to do, especially everything that
the fleet is currently working on and can't finish on its own."*

Measured today: **39 unmerged agent branches.** The fleet is good at producing work and bad at
landing it, and almost none of what follows needs another agent — it needs one careful reader with
a whole-repo view. That is you. ⛔ Throughout this section you **analyse, reconcile and report**:
you do not convert weapons, you do not merge to master, and you do not commit to another agent's
file.

### C30 — W24 is spread across FOUR unmerged branches with 77 commits between them

```
devin/nova/w24-lane2       57 commits   66 files
devin/ember/w24-lane1       7 commits   17 files
devin/dawn/w24-lane3       11 commits   11 files
devin/nova/w24-naxi-pilot   2 commits    3 files
                           --
                           77 commits unmerged
files touched by 2+ of them: 9
```

The nine shared files are the problem, and two of them are live weapon files:

```
mods/cameo/ContentPacks/RedAlert2Mod/Consortium/yaml/weapons.yaml   lane1 + lane2
mods/cameo/ContentPacks/RedAlert2Mod/Naxis/yaml/weapons.yaml        lane2 + naxi-pilot
docs/balance/derived/tiberiansun_{gdi,nod,cabal,forgotten}.json     lane1 + lane2
docs/balance/{derived/,}redalert2mod_consortium.json                lane1 + lane2
DEVELOPMENT_LOG.md                                                  lane1 + lane2 + lane3
```

**Deliverable: a merge-order dossier.** For each of the nine — do the two branches touch the same
WEAPON, or merely the same file? Where they overlap, do they agree on the final value? What order
must they land in, and which pair needs a human decision? A textual conflict is cheap; **two lanes
collapsing the same weapon to different damage is not, and no tool currently looks for it.**

⛔ You convert nothing and you merge nothing. You produce the order and the collision list; I land
them.

### C31 — Four confirmed duplicate branch pairs, two of them byte-identical

```
devin/regen/conversion         == devin/aurora/regen-starcraft-wc2   IDENTICAL COMMIT (122 files)
devin/aurora/naming-ra1_allies == devin/dawn/ra1-soviets-wip         IDENTICAL COMMIT (287 files)
devin/aurora/lane4-templates   vs devin/aurora/lane4-templates-v2    same 29-file set
devin/dawn/untagged-dune-mo    vs devin/dawn/ini-side-aliases        same 7-file set
devin/ember/rename-asianalliance vs devin/ember/naming-asianalliance 78 of 83/79 files shared
devin/aurora/rv-untagged-fix / -v2 / -v3                             three versions: 6 / 47 / 1 files
devin/aurora/pool-hygiene / pool-hygiene-clean                       14 commits vs 1
```

Two agents are pushing **byte-identical commits under different names**, which means at least one
of them believes they did work they did not do. Build
`tools/audit/audit_branch_duplication.py`: for every unmerged branch pair, report identical HEADs,
identical filesets, and any overlap above 70%. Run it, report the table, and recommend which branch
of each pair survives. ⛔ **Delete nothing** — recommend, and let me do it.

Worth automating: it has happened at least seven times in one week and nobody noticed until a human
read the branch list.

### C32 — `devin/aurora/fix-anchor-readiness` is unmerged and it is IN YOUR FILE-SET

`fix(tools): anchor_readiness.py crash from deleted intentional_composites`, plus
`fix extract_stats preservation`. Both files are yours under §3. **Read and verify that branch
before you write a line in either**, then tell me whether it should land as-is, land with changes,
or be superseded by your own work. If you rewrite around it without reading it, AURORA's fix is
lost silently — exactly what happened to your match logger.

### C33 — `devin/regen/conversion`: 497 `ChangesHealth@SelfHealing` Step overrides removed

```
650c0c600  regen(ra/ra2/ra2mod): remove 364 ChangesHealth@SelfHealing Step overrides
cb49bd2f9  regen(d2k/td):        remove 131 ChangesHealth@SelfHealing Step overrides
dba79de35  regen(d2k/shared):    remove   2 ChangesHealth@SelfHealing Step overrides
```

This is the DERIVED-STATS-IN-TRAITS work: a generated value replacing hand-written per-actor
overrides. It touches 122 files of live yaml and is **unmerged and unverified**. Verify that the
generated value equals the removed one for every actor — not a sample — and boot-gate it.
⚠ The failure mode is `LESSONS_LEARNED` 8c: a "derive unless overridden" default is invisible while
something upstream always overrides, so **assert the DERIVED value on a real resolved actor**,
never that the knob is merely present.

### C34 — The regeneration hazard that has already destroyed the corpus once

⛔ `tools/reference/extract_peer_units.py --mod <x>` **rewrites the whole corpus** with only that
mod's rows. It ran `docs/design/ORIGINAL_UNITS_PEER_OPENRA.md` from 2,583 rows down to 57 on
2026-09-07, and was recovered only because a backup had been taken first.
`tools/reference/splice_peer_section.py` exists to make that impossible — it refuses to write when
any other source's row count moves.

**Task: find the other tools in this repo with the same shape** — a filter-style flag that silently
narrows a whole-corpus write. Report them; propose a splice wrapper or a refusal for each. This is
a class of bug, not an incident.

### C35 — Reconcile the ratchets nobody trusts

Beyond B2 (322 vs 389), sweep every ratchet in `tools/audit/*.py` and report, per ratchet: its
current value, its committed value, when it last moved, and whether the report in
`docs/audit/latest/` agrees with a fresh run. ⚠ I found `original_coverage` stale today — the
committed report says O1 19 / O2 115; a fresh run says **O1 9 / O2 119**. A stale report is worse
than no report, because it is read as evidence. Do NOT regenerate `docs/audit/latest/` as part of
this — report the drift, and refresh in a separate commit, alone (§11).

### C36 — The AI match-log aggregation has no consumer

`OpenRA.Mods.Cameo/Traits/AiMatchLogWriter.cs` and `tools/ai/aggregate_ai_matches.py` have landed,
and the JSON-validity bug in the writer is fixed and covered by a test. But nothing consumes the
aggregate. Establish what a personality-tuning loop would actually need from it and write the
spec — not the tuner. ⚠ Already ruled and relevant: personality-tagged AI compositions need **zero
C#**, because a condition-gated player-level `ProvidesPrerequisite` already ships in
`mods/cameo/ai/ai.yaml`. Do not design a C# mechanism for something yaml already does.

### C37 — `release_drift` D4 belongs here too

See C19. 335 weapons that existed in the build players played no longer exist under that name.
Classify them `RENAMED -> <new>` / `MERGED INTO <weapon>` / `DELETED`. It is the only check that
looks at what SHIPPED rather than at what the rules say, and nobody has read its largest bucket.

### C38 — The naming migration is 287 files deep on two identical branches

`devin/aurora/naming-ra1_allies` and `devin/dawn/ra1-soviets-wip` are the same commit, 287 files.
⚠ The maintainer has ALREADY ruled that the `ra1_soviets` rename must be **reverted** — *"all 32
ids got worse"*. Before anything here lands, establish which of the 287 files belong to the
rejected rename and which do not. **Do not land a rename the maintainer has rejected.**
Underscore-only naming remains the law: no hyphens in ids, files, or fluent keys.

### C39 — Hero support in the ledger, for the lane the maintainer just ruled

Heroes now get a reference lane of their own (§4 C4). The fleet implements the reference side; the
**ledger** side is yours. `cameo_rows()` must keep dropping build-limited actors from every
distribution while the assignment can still see them — which means a hero FLAG carried on the row
rather than a drop. Specify the flag, where it is set, and every consumer that must learn to ignore
it. ⛔ SPECIFY it. The fleet writes it, so that two people are not editing
`reference_distribution.py` at once.

### C40 — Write the standing anti-collision check

Everything in this section is one failure repeated: **work that existed and nobody knew.** Propose a
single lightweight check — a script, a hook, a `docs/` table, your call — that would have caught the
byte-identical branch pairs, the duplicate match logger, and the two competing lane5 proposals
BEFORE the second one was written. Propose it and let me rule before you build it; this document
exists partly because I skipped that step with AURORA's filter.

### C41 — Keep `docs/TASK_INDEX.md` honest

It is the standing defence against exactly the duplication in C31, and it is only as good as its
rows. Every task you complete from this document earns a row: the task, the document and SECTION to
read first, and the tools that ALREADY EXIST for it. `tools/audit/audit_task_index.py` guards it.

### C42 — When you run out of work, ask before inventing more

The failure this document exists to prevent is a month of careful work on something nobody needed.
If C1–C41 are done, **post the state and wait** rather than starting a new subsystem. The one
exception is a crash: crashes always jump the queue.

---

## 11. Working rules

* **Worktree, never `git checkout -b` in the shared checkout.**
  `git worktree add C:/tmp/astra-<lane> -b astra/<lane> origin/master`. A checkout in the main tree
  moves every other agent's working directory; it has happened twice.
* **Branch, gate, push, post. Only Claude-Local merges to master.**
* **Scoped `git add <paths>` only** — never `-A` / `.` / `--all`. `git commit` also needs an
  explicit `-- <paths>` pathspec, or it commits the whole index including someone else's staged WIP.
* **Sign your own trailer** with your own identity. Never the Claude one — the git author is a
  shared repo identity, so the trailer is the only provenance signal, and a wrong one pollutes
  history.
* **Boot-gate any commit touching engine content** — `launch-game.cmd` must reach the main menu
  (`perf.log` ends `MenuPostProcessEffect.PostWorldLoaded`, no new `exception-*.log`); snapshot the
  log list first, and kill the process once the menu is proven. Docs/tools-only commits are exempt.
* **Audit reports regenerate via `bash tools/audit/run_all.sh` only** (PowerShell `>` writes
  UTF-16), and only from a COMPLETE tree. **Refresh `docs/audit/latest/` in its own commit, alone,
  or not at all** — never inside a feature PR. That is what made #328 unreviewable.
* **Never raise a ratchet.** Re-baselining on a genuinely widened measurement is allowed, but you
  must PROVE the measurement widened: measure the old subset and show it is unchanged.
* **PR size:** if a diff exceeds ~2,000 lines of anything but generated dossiers, split it.
* **Never hand-parse yaml** — read through `miniyaml.Ruleset.resolve_weapon` / `.resolve`.
* **Grep `docs/DESIGN.md` before designing anything.** It is binding and long, so nobody reads it
  end to end. A design question that feels novel usually is not.

---

## 12. Reporting format

Post one message per lane, and lead with the measurement, not the narrative:

```
LANE: C5 — fitted cost baseline unavailable, 25 of 27
BEFORE: 25 unavailable   AFTER: 25 unavailable (diagnosis only, no fix)
CAUSE:  18 missing o0/p0/q0 · 5 below the fit member floor · 2 extractor gap (named)
BLOCKED ON: nothing
NEXT:   C6
```

If a lane turns out to be blocked, **finish every other lane in full** and say explicitly what you
left out and why. Scaling the work down is the maintainer's call, not yours.

**And if you disagree with an order in this document, say so in one paragraph and then do it.** I
would rather be told I am wrong than have it silently worked around — that is how the reference map
ended up rejected twice.
---

## 13. ⭐ ADDENDUM 2026-09-08 — your review landed, and here is what comes next

**Your PR review was good work, and it corrected me.** I verified before accepting it, which is what
you should expect from anyone reading your findings:

```
git merge-tree --write-tree --name-only 4328e6818 e42eb9914  ->  exit 1, 72 conflicting paths
  tools/balance/reference_distribution.py   CONFLICT (add/add)
  docs/balance/class_anchors.json           Auto-merging  (CLEAN)
```

Your 72 is exact. §9's claim that merging "would delete the superweapon lock" was too strong and has
been rewritten — that file conflicts, a merge stops there, and a correct resolution keeps the
exclusion. You were right that branch age alone is not proof of a regression.

**And your `class_anchors.json` finding is better than mine.** I confirmed the eight
`signed_off: true` off the merge tree independently. The general form is now recorded in §9 as the
lesson of this review: **a file that conflicts is safer than a file that does not — the conflict is
the warning.** Carry that into everything below.

Two things I especially want repeated: you compiled the actual C# rather than trusting the Python
model (Python ints do not overflow, so the model could never have found the 32-bit defect), and you
said repeatedly what you had NOT verified. Both are rarer than they should be. Keep doing both.

### Your order of work from here

**A. Finish the PR lane (C27–C29), because the maintainer has now decided.**
Maintainer's call, 2026-09-08: follow your plan. #321 closes as superseded; #325 gets closed and
re-cut as small PRs, flags first, then the repaired insurance. ⛔ You still do not close, merge or
force-push anything — those are the maintainer's PRs and they will do it. What you produce is:

1. the **flags-only** change, re-cut against current master, with the padded-write bypass in
   `generate_chrome_scales.py` fixed and a behavioural test asserting **zero** resize calls on a
   padded source (your existing refusal tests check strings, which is what let it through);
2. the **insurance** change, separately, with the dead zone and both `1000 *` signed-32-bit
   overflows fixed, and your reproductions turned into real C# boundary tests rather than notes;
3. a one-line note per remaining salvage group saying "carried / dropped / needs the owner".

⚠ Neither of these is a docs commit. Boot-gate the insurance one — it touches `player.yaml` and
`defaults.yaml`, which is engine content.

**B. Then the anchor dossiers (§4), which is still the lane that unblocks the pipeline.**
Nothing about C1–C12 has changed except that it is now more urgent: W24 moved today for the first
time in a week (see D below), so the inputs your dossiers depend on are starting to settle. Start
with C3, the four classes whose anchor is already on spec.

⛔ Note one thing before you touch `anchor_readiness.py`: AURORA has an unmerged fix for a crash in
it on `devin/aurora/fix-anchor-readiness`, and that branch conflicts with master in that exact file.
That is task C32 and it now blocks C1 — read the branch first.

**C. B2 (the 322-vs-389 reconciliation) has partly resolved itself, and that is a lesson.**
Both numbers moved today because two W24 lanes landed. `audit_three_way_split` now reports **231**.
Re-measure both before doing anything: if the gap between the two audits is still ~67, the mismatch
is structural and worth a day; if it changed with the corpus, one of them is counting something
lane-dependent and that is a different, easier finding. **Do not carry my number forward — measure.**

**D. What landed while you were reviewing, so you rebase onto the right thing**

```
06ef3c4f3  Merge W24 lane 3 (DAWN): 69 weapons collapsed, ledgers re-extracted
34663bbfe  Merge W24 lane 1 (EMBER): 22 weapons collapsed
           audit_three_way_split:  322 -> 231
```

Both boot-gated. Lane 3 arrived with `audit_balance_drift` red across 10 ledgers because it changed
yaml without re-extracting; I ran `extract_stats.py` to land it. That is now a standing rule in
`docs/FLEET_ORDERS_2026-09-08.md` §7 and it applies to you too: **yaml and ledger in the same
commit.**

### Two corrections to your review, small but worth having

* Your report says **406** commits behind; it was 405 when I measured and 406 when you did, because
  master moved between us. Neither is wrong — but pin the SHA next to the count, as you did for the
  heads, so a reader can tell a moving target from a disagreement.
* The `dmg` / `dmg/wh` producer-consumer mismatch you found is real and predates the branch, which
  you said clearly. It is now C19's neighbour in this document's §7 and it is **yours to fix on
  master**, independently of the PR — a round-trip test from producer to consumer, as you proposed.

### And one thing to keep doing

You wrote "this is not a claim that every generated row was validated" more than once. That
sentence is worth more to me than a confident summary would have been, because it tells me exactly
where to look next. The failure mode in this repo is not agents who find too little — it is agents
who report more certainty than they measured.

---

## 14. ⛔⛔ ADDENDUM 2026-09-08b — SHIP CODE. Documents are no longer a deliverable.

**Maintainer, verbatim:**

> *"Can you also make Astra produce actual code and not just review and document? We need to make
> some serious progress now but from what I've seen he was just documenting... make sure you include
> that!"*

That is the whole of this section's premise, and it is fair. Your review work was genuinely good —
§13 says so and means it. But across #328, the review, and the development log, the ratio of code to
prose is wrong, and the pipeline has not moved a single number.

**New rule, and it overrides the deliverable of every task above: a task is DONE when code lands on
master, boot-gated, with a test. A document describing what should be done is not done.** Where a
task below says "report", that report is a paragraph in the PR body, not a file in `docs/`.

⛔ You may write at most **one** new `docs/` file per landed code PR, and only if the PR needs it.
`ASTRA_REVIEW.md` was 46 KB; the fix for its first finding is about twelve lines.

### 14.0 Priority, settled by the maintainer

1. **The balance pipeline** — everything in §14.1. This is number one and it is not close.
2. **The bot modules** — §14.2. Secondary, but larger than it looks, and one maintainer decision
   just unblocked the hardest part.
3. **RA2 + TS reference maps** — §14.3. Yours now.

---

## 14.1 BALANCE PIPELINE — the code that has to exist

Read `docs/design/EXTRAPOLATION_PROGRAM.md` first. It is the maintainer's method, written down,
with the two measurements that prove it works. The short version: **the 27 class anchors stop being
real actors and become virtual ones derived from the reference-mapped originals.**

### ⛔ A1 — READ THIS BEFORE WRITING ANYTHING

```
tools/balance/fit_class.py --class <name> --spec hp,speed,range_wdist,damage,reload,cost0
    "virtual anchor ... a round-number model unit that need not exist in game"
```

**The virtual-anchor mechanism already exists and nothing uses it.** Do not design one, do not
build one, do not propose one. `tools/balance/faction_extrapolate.py` (504 lines) likewise already
implements the exchange-rate method. What is missing is the INPUTS and the WIRING, which is A2–A5.

This is the third time in this repo that an existing mechanism was nearly rebuilt. Run
`fit_class.py --class mbt --spec 240000,95,5500,600,20,800` before you write a line, and see what
it already gives you.

### A2 — `tools/balance/derive_virtual_anchor.py` — NEW CODE, this is the centrepiece

Read-only against yaml; writes nothing to `mods/`; never sets `signed_off`.

```
python tools/balance/derive_virtual_anchor.py --class mbt [--factions td_gdi,td_nod,ra1_allies,ra1_soviets,japan]
python tools/balance/derive_virtual_anchor.py --all --out docs/balance/anchors/
```

For one class it must:

1. Collect the class's members via **`class_membership.classify()`** — ⛔ NOT the raw
   `design.class_anchor` field. Membership is DERIVED from `subtype` when no explicit tag exists;
   reading the tag alone reports `commando: 0` for a class with 30 members. Two of my own
   measurements returned all-zeros this way before I read the module. `classify()` returns
   `(class, why)` and `ledger_rows()` yields `(actor, design)` — the design block itself, not the
   unit.
2. Restrict to members in the anchor factions (default: the four originals + japan).
3. For each of `hp`, `speed`, `range_wdist`, `cost`, compute the anchor value from those members,
   **preferring reference-backed ones** (`docs/balance/derived/reference_assignment.json`,
   confidence STRONG or FAIR — SHAPE and WEAK do not exist any more and must never be readmitted).
4. Round onto the nice-number grid (`docs/DESIGN.md`, the nice-number law; damage on the **100**
   grid — `formula.DAMAGE_STEP`, and ⚠ NOT the 2,000 grid that older docs teach, which W15/W17
   retired along with `FirepowerMultiplier` as a pricing knob).
5. **Assert `o0 = p0 = q0 = cost0` holds.** It is a virtual unit: if the identity fails, the spec is
   wrong. Today 0 of 27 real anchors satisfy it. A virtual one that does not is a bug in your
   derivation — raise, do not round away.
6. Emit the verifier at **2× hp, 2× dps, 2.5× cost**, and assert baseline and verifier share the
   TechTier bucket AND `K`. If they cannot, say so and emit no verifier rather than a broken one.
7. ⛔ Emit **no `dps0`**. W24 is still moving (231 weapons stack 2+ mains). `damage,reload` in the
   spec string are the model unit's own, not a target for any real weapon.
8. Print the `fit_class --spec` command line for the class, and the residual distribution of the
   class's real members against it.

**Bias check, and it is not optional (EXTRAPOLATION_PROGRAM §6.1):** for every class, compare the
TD/RA1/Japan member stats against the class's FULL membership. If the anchor factions sit in one
tail, the virtual anchor is biased and the class must be emitted as `BIASED — do not sign` with the
percentiles shown. A class quietly anchored off a tail is the failure that would poison everything
downstream.

⛔ `dreadnought` has **zero** members in TD/RA1/Japan (its five are StarCraft/naval). Emit
`NO SOURCE` and stop. Do not invent one; do not borrow from another class.

**Tests:** a fixture class with known members and a known reference consensus, asserting the derived
spec, the identity, the verifier ratios, the bias flag, and the `NO SOURCE` path.

### A3 — Wire the derivation into `anchor_readiness.py`

It already reports `anchor actor OFF its ruled spec: 23 of 27` and
`satisfying o0=p0=q0=cost0: 0 of 27`. Add a column: what the VIRTUAL anchor would be, and how far
the current real anchor sits from it. That single table is what the maintainer signs from.

⛔ AURORA has an unmerged crash fix for `anchor_readiness.py` on `devin/aurora/fix-anchor-readiness`,
and it conflicts with master in that exact file. **Read and land-or-reject that branch through
Claude-Local before you touch the file.** This is task C32 and it now blocks A3.

### A4 — Make the report-to-ledger path actually work (your own finding, now yours to fix)

You found it and you were right that it predates the branch: the consumer at
`_patch_ledgers_from_reports.py:57` asks for a `dmg` column, the producer writes something else, and
**60 rows parse with zero damage targets** while every other target applies. Fix it on master:

* one shared column contract between producer and consumer, defined in one place;
* the writer **refuses the whole operation** when a required target is missing, rather than silently
  skipping the damage branch;
* a producer→consumer **round-trip test**, not tests of either end alone. That is the test that
  would have caught this.

### A5 — Every refusal you own gets a passing test too

You have my example: my superweapon lock tested a generator object, was always truthy, and refused
every faction on a clean tree. Sweep `apply_balance.py` for every `problems.append(...)` and confirm
each has a test asserting **both** that it fires on the positive case and that it does **not** fire
on the negative one. Report the ✓/✗ list in the PR body, then write the missing ones.

### A6 — The three other real defects you reproduced, as landed fixes

Not as findings. Each is small and each has your reproduction already:

* `splice_templates.py:217` writes canonical templates before validating the compatibility copies,
  so a refusal leaves a half-written file. **Compute the whole candidate in memory, validate, then
  write; preserve original bytes on any refusal.**
* `tools/art/generate_chrome_scales.py:347` refuses a padded source only under `--emit`; `--write`
  resizes it anyway. Fix both paths and add a behavioural test asserting **zero resize calls** — the
  existing tests check strings, which is exactly why this survived.
* `tools/hooks/read_first_guard.py:92` classifies command PREFIXES, so `sed -i`, `git branch -D` and
  `cat a > b` are all "read-only". Narrow allowlist of read OPERATIONS, handle redirection and
  flags — or relabel the hook as advisory. Do not leave it claiming a guarantee it does not give.

### A7 — Then the anchors themselves

With A2 landed, §4's dossiers stop being prose and become generated output plus a judgement line.
Run `--all`, produce the 26 signable specs plus `dreadnought: NO SOURCE`, and hand the maintainer a
table. ⛔ You still never set `signed_off`, and you never run `apply_balance --confirm`.

---

## 14.2 BOT MODULES — and the maintainer just unblocked the hard part

`docs/design/AI_ARCHITECTURE.md` is the plan (1,158 lines, §11 reconciles the five-agent research
round from Perplexity, Grok, Copilot, ChatGPT and Gemini). Read §0, §3, §4, §5, §10 — those are the
sections that describe what you are building. **It is a plan, not code. Almost none of it exists.**

What exists today: `AiMatchLogWriter.cs` + `AiMatchLogRecorder.cs` (record-only, landed, JSON bug
fixed and tested), `tools/ai/aggregate_ai_matches.py` (no consumer), `BotGlobalUnitBudget.cs`,
`BotInsurance.cs`, and ten difficulty tiers of `BotLimits` in `mods/cameo/ai/ai.yaml`.

### ⭐ B1 — FOGGED OBSERVATION. Ruled YES by the maintainer, 2026-09-08. Build it first.

§9 open decision #1 was "Maintainer's call" and is now answered: **the bot's observation model gets
fogged.**

The problem, as §0.2 states it: the squad manager scans `World.Actors` and filters only through
`IVisibilityModifier` — cloak and submersion — **never through the player's shroud**
(`SquadManagerBotModuleCA.cs:226-253,331-345`). A bot knows where every enemy unit and building is
from tick zero, including inside unexplored map. Only the capture and crate modules expose a
visibility option at all.

This is the single most important piece of the whole AI program, and §0 says why: *"a detector that
reads the true world state cannot be wrong and therefore cannot be beaten by deception."* Without
it, scouting, feints and hidden tech mean nothing, personalities are cosmetic, and every claim that
Cameo's bots win without cheating is false.

**Build:**

1. A `BotObservationModel` — one authority per decision (§10.1) — holding what this bot has actually
   SEEN: last-known position, type and time-stamp per enemy actor, decaying rather than deleted, so
   the bot can be *wrong* about a unit that moved. Being wrong is the feature.
2. Every consumer reads the model, not `World.Actors`. Start with the squad manager; the ones that
   already have a visibility option keep it.
3. ⛔ **This is a Cameo SHADOW, not an engine edit.** `ObjectCreator.FindType` takes the first
   assembly in `mod.yaml`'s list (AS, CA, **Cameo**, Cnc, D2k, Common), so an `OpenRA.Mods.Cameo`
   type of the same name wins with zero yaml changes. ⚠ But a Cameo shadow **cannot** beat an **AS**
   trait — AS is first. `SquadManagerBotModuleCA` is CA, so a Cameo shadow of it works; check the
   assembly of anything else you shadow before you plan around it. `engine/` is NOT part of this
   repo — it is gitignored, has zero tracked files, and the next `make all` deletes anything you
   write there.
4. Determinism: the observation model is per-player bot state. Keep it on the synced side or the
   unsynced side deliberately and say which (§6.1) — an OOS from bot memory is a nightmare to debug.
5. Expect bots to get **weaker** at first. That is correct and expected; do not compensate by
   giving anything back.

### B2 — The personality manager (§4)

Five personalities, plus the open question of whether Guerrilla is a sixth or a mode of Rush (§9 #2,
leaning sixth — raise it, do not decide it).

⭐ **The compositions need ZERO C#.** A condition-gated player-level `ProvidesPrerequisite` already
ships at `mods/cameo/ai/ai.yaml:176`, and the ten difficulty tiers already use exactly that pattern
(`:179-209`). Personality-tagged production lists are yaml. **Do not write C# for something yaml
already does** — that is the mistake that produced a duplicate match logger.

The C# is the **switching**: which personality, when, and with what hold time. Ship CN's hysteresis
constants as the starting point (§9 #11) and re-fit from phase-2 logs.

### B3 — The master module (§5), and the decisions you must surface rather than settle

Open decisions that are the maintainer's, not yours — surface each with a recommendation and the
evidence, in the PR body:

* **#6** — do all ten difficulty tiers get the personality manager, or is dynamic switching itself a
  high-difficulty feature? (Making it difficulty-gated is a cheap, honest difficulty axis.)
* **#8** — who owns contact memory: the master, or the squad manager's own scan? One authority per
  decision says pick one. ⚠ B1 probably answers this: the observation model IS contact memory.
* **#10** — may an emergency override change the personality, or only target and urgency? CN switches
  straight to Turtle on a danger spike; the review reply argues an emergency must never rewrite the
  strategic posture. This one is unresolved in the document and decides whether §4.5's fast path
  needs its own hold time.

### B4 — Give the match log a consumer

`tools/ai/aggregate_ai_matches.py` aggregates and nothing reads it. With B1 and B2 landed it becomes
the evidence for the hysteresis re-fit. Wire it to something that answers one question:
*did switching personality at that moment help?*

### B5 — Boot-gate everything here

`mods/cameo/ai/ai.yaml`, `player.yaml`, `defaults.yaml` and anything in `OpenRA.Mods.Cameo/` are
engine content. Rebuild C# before booting
(`DOTNET_ROLL_FORWARD=LatestMajor dotnet build -c Release --nologo -p:TargetPlatform=win-x64`) — a
stale DLL crashes the boot with `Cannot locate type: …Info`. The build output the game LOADS is
`engine/bin`; the tracked `mods/cameo/OpenRA.Mods.Cameo.dll` does NOT auto-update.

---

## 14.3 RA2 + TS REFERENCE MAPS — yours, ruled 2026-09-08

You can do this without any local game install: every input is committed —
`docs/reference/ini_corpus.json` (11,870 rows) and `docs/design/ORIGINAL_UNITS_PEER_OPENRA.md`
(2,583 rows). Nothing in the TD/RA1 process touched a local folder.

Run the same pipeline — `assign_references.py` → `reference_targets.py` →
`build_reference_report.py` — for `ra2_allies`, `ra2_soviets`, `ts_gdi`, `ts_nod`. Produce ONE
report per faction, originals and expansions split, for the maintainer to approve faction by faction
(EXTRAPOLATION_PROGRAM §5's ledger).

⛔ **Read-only on the producers.** `assign_references.py`, `reference_distribution.py`,
`faction_routes.py`, `reference_targets.py`, `tools/reference/**` belong to the fleet. Report
mappings and hand over patches; Claude-Local lands the code. Five agents in that tree cost a week.

⚠ **Open maintainer question, do not assume an answer:** is Romanov's Vengeance the RA2 authority?
It carries 729 buildable units — more than RA2 + YR ever shipped — and it is 104 of the 119 unclaimed
"originals". `audit_original_coverage` currently exempts it from the O2 ratchet; that exemption is a
placeholder to be DELETED when ruled, never raised.

Traps that cost the TD/RA1 map three review rounds, so you do not pay for them again:

* **SHAPE and WEAK are not evidence.** Of ten mappings the maintainer called junk: 8 SHAPE, 2 WEAK,
  **zero STRONG**. An actor with no name-backed match gets NO reference and falls through to the
  formula.
* **Originals must claim before expansions.** `firerocketsoldier` scores 0.867 against "Rocket
  Soldier" and the real `sovietrocketsoldier` 0.850 — the expansion is literally the closer string.
  No scorer tuning fixes it.
* **Read ids, not only names.** CA ships `1TNK` as "Scout Tank"; DTA prefixes RA-era actors with
  `RA` (`RAPBOX`, `RAAGUN`); CA states ownership in a dot suffix (`STNK.Nod`).
* **CA is admissible to a median of FIVE Cameo factions** where every other source's median is one.
  Until EMBER fixes it, expect CA to offer you the wrong faction's unit and check every CA match.

---


### ⭐ 14.3b — round-four traps, added 2026-09-08b. These WILL hit your RA2/TS pass.

Read `docs/FLEET_ORDERS_2026-09-08.md` §9 in full; the four that matter most for you:

1. **`assign_references.py` writes the JSON only under `--write`.** I lost a verification round to
   this — ran it without the flag, read yesterday's file, and reported 30 corrections as failed when
   they had all applied. Check the mtime of anything you draw a conclusion from.
2. **Two rows, one name.** CA ships `NSAM` and `SAM` both named "SAM Site" with identical faction
   lists, two "AA Gun" rows, two "Mammoth Tank" rows. Compare IDS, never names alone. RA2 sources
   are worse for this than TD/RA1 — Romanov's Vengeance alone carries 729 buildable rows.
3. **A guard wrong in the restrictive direction deletes correct candidates.** `exempt()` marked
   armed APCs and the GDI Vulcan chassis-only because it asked the class question before the weapon
   question. When two tests disagree, the one that lets the actor through wins.
4. **Never `continue` past a rule that did not fire.** A silent override skip read as bad judgement
   for a month. If a table says X and X does not happen, surface it.

⚠ And one open rule that affects how you report: **one peer row currently serves one Cameo actor.**
The maintainer has asked for a shared row in three places, so the rule is under review. Report a
mapping you believe is right even if another actor already holds that row — flag the collision
rather than silently picking one.

## 14.4 How I will judge this section

Every task above lands as **code on master, boot-gated where it touches engine content, with a test
that fails against the old behaviour.** In the PR body: what you measured before, what you measured
after, and what you did NOT verify.

That last sentence is the one thing from your review I want kept exactly as it was.

---

## 14.5 ⛔ ANSWER TO YOUR C32 QUESTION — the reservation is RELEASED. You were right; my order was wrong.

**You asked the right question and you drew the right conclusion from it.** Refusing to treat a
missing branch as permission to bypass a gate is exactly the behaviour I want, and it is the
behaviour that caught my error rather than inheriting it.

**Verified 2026-09-08 against the artifact, not the summary:**

```
git ls-remote origin '*aurora*'      ->  8 aurora branches, NONE named fix-anchor-readiness
git branch -a --list '*aurora*'      ->  devin/aurora/fix-anchor-readiness EXISTS, LOCAL-ONLY
                                          (head d14306419, never pushed to any remote)
grep intentional_composite tools/balance/anchor_readiness.py   ->  ZERO matches on master
python tools/balance/anchor_readiness.py                       ->  runs clean, exit 0
```

So there are **two** defects in the order I gave you, and both are mine:

1. **The branch was never pushed.** It exists only in one local checkout. You could not have found
   it on any remote because it is not on any remote. My order named a branch as if it were
   reachable and it never was — this is the same failure mode that made me report "no agents have
   pushed" when 17 branches had in fact moved.
2. **The fix is already on master by another route.** `anchor_readiness.py` no longer calls
   `tws.intentional_composite` at all, and `audit_three_way_split.py:134-166` documents the
   2026-09-06 deletion of the exemption. There is nothing left to land.

**RULING: C32 is obsolete and CLOSED. The reservation on `anchor_readiness.py` is RELEASED. The
existing master implementation IS the approved starting point. Proceed to A3 readiness integration
and to C1.**

The local-only branch also carries 32 other files of LANE-4/LANE-5 classification work
(`apply_lane4_templates.py`, `lane5_gather_stats.py`, `AIR_NAVAL_CLASSES_PROPOSAL.md`, and ledger
edits to `tiberiansun_gdi/nod.json`). **That is a separate question and it is NOT yours** — I will
triage it with Aurora. Do not import any of it.

### And on #335 itself

Read and accepted as a draft for review, not a merge request — that framing is correct and I am
treating it that way. Three things worth saying back:

* **B2 is closed by your `--compare-split` work**, and closed better than the way I framed it. I
  had it queued as "re-measure and see if the ~67 gap is structural"; you accounted for every node
  instead — 73 shape-only, zero split-only, W5 counting zero/healing/ally-only flat nodes that the
  positive-damage predicate excludes. It is off your queue.
* **Your "known incomplete class migration" note is exactly right and is now scheduled.**
  `armed_troop_transport` names `td_gdi_apc` as its anchor while the actor still classifies as
  `support`, because `^ArmedTroopTransportTemplate` has never existed in yaml. That is **C46** in
  §15.3 below, together with the new `^MobileBunkerTemplate`. Your diagnostic reporting NO SOURCE
  is the correct behaviour — do not paper over it.
* **The three TS sonic core-damage failures** (`TSGrenadeSonic` vs Scout, `TSHellfireSonic` and
  `TSZoneHellfireSonic` vs Medium) reproduce on master and you correctly declined to adjudicate
  them. They are weapon-owner questions and I am carrying them to the maintainer. ⛔ Do not "fix"
  them — `Versus` lives ONLY in `^Warhead_*` templates and no warhead changes without explicit
  permission.

One process note, offered as a peer rather than a correction: your full-suite line reports **15
failing modules that also fail on untouched `a089bd3dc`**, and you said so plainly instead of
quietly excluding them. That is the right call, and pinning the baseline SHA next to the number is
what makes it checkable.

---

## 15. ⛔⛔ ADDENDUM 2026-09-08c — THE AA LANE IS YOURS, AND SO IS THE ENGINE QUESTION

**Four maintainer rulings landed today.** They are already written into `docs/DESIGN.md` (the AA
range law, which REPLACES the dual-weapon AA law of 2026-07-11 — read the new text, not the old
one, and do not resurrect the old one from a stale quote). Everything in this section is
downstream of them.

> **The rulings, verbatim in effect:**
> 1. Three classes and only three may carry an AA armament longer-ranged than its ground twin:
>    **`scout_vehicle`, `armed_troop_transport`, `anti_air_vehicle`** — at **1.5×**. Everything
>    else uses one range for both domains. `anti_air_vehicle` **SURVIVES** as a class.
> 2. **`mobile_bunker` is a new class**, populated by **all 16 buildable actors with a resolved
>    `AttackOpenTopped`**, and it may have **no air-capable armament at all**.
> 3. The 1.5× is **generated**, not hand-typed, and then audited.
> 4. Enforcement is a **LOWER-ONLY RATCHET**. Never raise it.

### 15.0 ⭐ C43 — THE ENGINE QUESTION. The maintainer asked for it by name; go deep.

**The question, in the maintainer's words:** *"is it possible to only have a single weapon for both
ground and air and then apply something like a range multiplier on the template itself but that
range multiplier only increases range against air targets?"*

**What I already established, so you do not redo it.** Verified from source 2026-09-08:

```
Armament.MaxRange()                     Armament.cs:215          takes NO target argument
IRangeModifier.GetRangeModifier()       TraitsInterfaces.cs:480  takes NO target argument
RangeMultiplier                         Multipliers/RangeMultiplier.cs  one int, ALL armaments
AttackBase.GetMaximumRangeVersusTarget  AttackBase.cs:336        loops armaments, skips any whose
                                                                 weapon !IsValidAgainst(target),
                                                                 returns max of the rest
class Armament                          defined ONLY in OpenRA.Mods.Common (NOT in AS, NOT in CA)
override WDist MaxRange()               ZERO occurrences anywhere in the tree
```

So: per-target range is resolved by **armament selection**, one level above the armament. The twin
armament is the engine's mechanism, not duplication. A mod-side trait cannot do it, because every
range hook in the engine is target-blind.

**What is genuinely open, and what I want from you.** `MaxRange()` is `virtual`, and `Armament` is
defined only in Common — so a Cameo shadow IS possible (assembly order AS, CA, **Cameo**, Cnc, D2k,
Common, and neither AS nor CA defines the type). That is not sufficient on its own, because the call
site that knows the target lives in `AttackBase`. Your job is to find out what a real fix costs.

Deliverables, in this order:

1. **Enumerate every caller** of `MaxRange()`, `GetMaximumRangeVersusTarget()`,
   `GetMinimumRangeVersusTarget()` and `Weapon.Range` across `engine/OpenRA.Mods.Common`,
   `OpenRA.Mods.AS`, `OpenRA.Mods.CA` and `OpenRA.Mods.Cameo`. Include the activities
   (`Attack`, `AttackMoveActivity`, `FlyAttack`), `AutoTarget`, the AI modules, and the UI range
   circles. A single missed caller is how a targeting fork ships a unit that walks into range and
   never fires.
2. **State which of them have a `Target` in hand** and which do not. That set difference IS the
   answer to whether the fork is tractable. Write it as a table.
3. **Decide between the two shapes and argue it:**
   * **(a) Shadow `Armament` in `OpenRA.Mods.Cameo`** with an `AirRangeModifier` field and an
     overridden `MaxRange()`, plus whatever minimum set of call sites must become target-aware.
     ⛔ **Prove the shadow actually binds** by giving the Cameo `ArmamentInfo` a field the engine
     one lacks and booting with that field set. `--docs` lists both types and PROVES NOTHING —
     this is a documented trap in `docs/LESSONS_LEARNED.md`.
   * **(b) Fork `AttackBase` in the cameo-engine clone.** ⛔ `engine/` **IS NOT PART OF THIS
     REPO** — it is `.gitignore`d, `git ls-files engine` returns zero, and `make.cmd all` DELETES
     your edits. The procedure is `docs/LESSONS_LEARNED.md` → "The canonical engine update
     pipeline": edit the SEPARATE `cameo-engine` clone → push → `git rev-parse cameo-engine` for
     the full 40-char hash → `ENGINE_VERSION` in **`mod.config`** (not mod.yaml) → `make.cmd all`
     → verify `engine/VERSION` → recreate `engine/glsl/` shaders (the fetch wipes them) → boot-gate.
4. **Say what could break.** Every unit's attack behaviour rides on this path. I want the failure
   modes named: units that approach but never fire, AI that mis-scores threats, range circles that
   lie, `KeepsDistance` behaving differently, aircraft attack runs.
5. **Recommend, and say how confident you are.** My prior is that the twin armament stays and the
   fork is not worth it — but I set that prior from four files, and you are being asked to read
   fifty. **If you conclude I am wrong, say so plainly.** You corrected me on the PR merge analysis
   and that correction was right; the same standard applies here.

⛔ **Do not land an engine change on the strength of this analysis.** Deliver the analysis and a
recommendation. The maintainer decides whether it gets built.

### 15.1 C44 — Generate the 1.5×, stop hand-typing it

`gen_weapon_template.py` gains `AA_RANGE_MULT = 1.5` and writes the AA twin's `Range` from the
ground twin's, for the three allowed classes only.

⚠ **§8c is the trap that will eat this task.** *"A derive-unless-overridden default is invisible
when something upstream always overrides."* `ScaledBullet` derived shell Inaccuracy and Speed from
Range for **weeks** and reached **zero** weapons, because the templates also wrote literals and an
explicit yaml value always wins. So:

* the generator must **WRITE** the value into the emitted yaml, not merely offer a default;
* your test must assert the **derived number on a real RESOLVED weapon** through
  `miniyaml.Ruleset.resolve_weapon` — never that the knob is present;
* run `tools/audit/verify_generator_sync.py` after, and `splice_templates.py --all`, **never a
  subset** (a partial splice leaves drift — documented trap).

Then regenerate the non-compliant AA twins as ONE boot-gated batch. Baseline measured 2026-09-08:
**67 actors carry a live AA armament; 36 are at exactly 1.5×, 14 at exactly 1.0×, 14 elsewhere, 3
are pure-AA.** Roughly 13 need moving. Re-measure before you touch anything — do not carry my
number forward.

### 15.2 C45 — `tools/audit/audit_aa_range.py`, a LOWER-ONLY ratchet

Reports, per buildable actor with both a live ground and a live AA armament:

* class (via `class_membership.classify()` — ⛔ **never the raw `design.class_anchor` field**;
  `extract_stats` rewrites it to `None` on every run, which is why the anchor board reads 18%);
* AA range ÷ ground range;
* verdict against the DESIGN.md law.

FAIL classes: an allowed class not at 1.5×; a disallowed class above 1.0×; **any `mobile_bunker`
with an air-capable armament** (today exactly one — `td_gdi_assaultapc` at 1.500×).

⚠ **Exclude the evidence the audit is built from.** Four audits in one day once flagged their own
definition file, their own previous report, their own fixtures, and a path that can never exist.

⚠ **A 0% row is a bug in the CHECK.** I hit this again today: my `AttackOpenTopped` scan returned
**0 of 213** because I searched for a trait named `OpenTopped` and the trait is `AttackOpenTopped`.
Four such cases in one day previously; a 526-actor renaming backlog was once a doubled prefix in one
config table. If a row reads 0% or 100%, break the check before you believe it.

Wire it into `run_all.sh` (⛔ **`bash tools/audit/run_all.sh` only** — PowerShell `>` writes UTF-16
and corrupts the reports) and register the ratchet.

### 15.3 C46 — Two new templates. This is the yaml change, and it needs a boot gate.

`^ArmedTroopTransportTemplate` and `^MobileBunkerTemplate` go into
`mods/cameo/rules/defaults.yaml`, and the member actors get the `Inherits@Template:` line.

⛔ **The reason this is the ONLY way it can work:** `extract_stats` rewrites `design.class_anchor`
to `None` on every run (`extract_stats.py:967`). A hand tag cannot make an actor a member of
anything. **`design.subtype` — which is the nearest `^...Template` the actor inherits — is the only
durable membership signal.** `class_membership.py` already maps `armedtrooptransport →
armed_troop_transport`, and that entry has sat INERT with **zero members** because the template was
never written. Add `mobilebunker → mobile_bunker` alongside it.

The 16 `mobile_bunker` members, measured 2026-09-08 through the resolver:

```
line_breaker (10)  ra2_allies_battlefortress, _chrono, _empty, td_gdi_assaultapc, tkm_battlebus,
                   asianalliance_warturtle, forgotten_thumperbus, latinsyndicate_carteltruck,
                   naxis_oldtank, steelconsortium_poseidontank
epic_vehicle (3)   forgotten_nomadbarracks, naxis_nokana, tkm_bigshiee
high_tech_tank (1) naxis_shoekarn
support (2)        asianalliance_dragonfly, latinsyndicate_narcohummer
```

⚠ **21 `ra2_*_driveby` civilian cars also resolve `AttackOpenTopped` and are NOT buildable** —
exclude them. The population rule (2026-08-30) is buildable, unlimited units only.

The 22 actors that STAY `line_breaker` are flame tanks, disruptors and brawlers
(`td_nod_flametank`, `ts_gdi_disruptor`, `zerg_ultralisk`, `protoss_archon`, …). The fireport test
splits the class exactly along the maintainer's intent — do not widen it.

Then add `mobile_bunker` to `docs/balance/class_anchors.json` as the 29th class
(`armed_troop_transport` was the 28th). ⛔ `verifier_actor: null` and **no `dps0`** — W24 is still
moving, 231 weapons still stack 2+ mains.

⛔ **BOOT GATE.** `defaults.yaml` is engine content. Snapshot `%APPDATA%/OpenRA/Logs` BEFORE
launching; `launch-game.cmd` must reach the main menu; proof is `perf.log` containing
`MenuPostProcessEffect.PostWorldLoaded` and **no new `exception-*.log`** — not the last line of the
log. Kill the process the moment the menu is proven; a live instance locks the next build.

### 15.4 C47 — Teach `extract_stats.py` to record cargo and fireports

The ledger records **no passenger capacity at all** — no `Cargo`, no `Passengers`, no `OpenTopped`.
That is why no audit can currently distinguish a transport from any other armed vehicle, and why
C46 has to go through templates. Record `cargo_capacity` and `open_topped` per actor so the audit
can **cross-check that the template was applied to everything that deserves it** — the failure mode
is a transport nobody remembered to tag, and a mechanical field is what catches it.

⛔ Re-run `extract_stats.py` and commit **yaml and ledger in the SAME commit**. `audit_balance_drift`
goes red when they disagree, and it has gone red twice because someone landed yaml without
re-extracting. That is a standing rule in `docs/FLEET_ORDERS_2026-09-08.md` §7.

### 15.5 C48 — Fix the AA detector: names now, ValidTargets as the gate

`reference_distribution.is_anti_air_armament()` is a **name heuristic** — `@AA` in the slot or `_AA`
in the weapon id. Every number in §15.1 inherits that. It demonstrably misses: `ts_gdi_mammothmkii`
carries `TSMammothTusk2II_AA` and is detected; `ts_gdi_mammothprototype` carries the functionally
identical `TSMammothTusk2` and is **not**.

Ruling: keep the name rule as the primary, and **add a second check that reports any weapon whose
resolved `ValidTargets` include `Air` on an armament NOT named to the `@AA` convention.** That turns
the naming convention from an assumption into something enforced.

⛔ **Read `ValidTargets` through `miniyaml.Ruleset.resolve_weapon`. NEVER hand-parse yaml.**
[hook-enforced] A bespoke line-scanner once opened a dict on `Versus:` and never closed it, so
`PercentageVersus:` rows in the same node overwrote the profile; every mean, spread and ratio came
out internally consistent and **wrong** — it reported "0 of 125 obey the MEAN-100 law" when the
truth was **123 of 125**. The near-miss sibling name is the trap.

### 15.6 C49 — Three units price at DPS 0 because all their guns are AA

`harkonnen_adp`, `ra2_allies_aegiscruiser`, `tkm_quadturretbunker` have **no live ground armament**.
The free-AA pricing convention excludes AA from ground DPS, so the formula sees zero. This is the
same defect class the maintainer caught on `td_nod_lighttankmkii`.

The convention is right for a scout with a bonus AA gun and wrong for a unit whose only weapon is
the AA gun. Measure the full population first — I found three, but my detector is the name
heuristic C48 fixes, so the real number is probably larger. Then bring the maintainer **options**,
not a decision. ⛔ Read §11's rule: a maintainer call goes in a question with real alternatives.

---

## 16. THE REST OF YOUR QUEUE — everything still open, in priority order

Nothing below is new work I invented to fill space; every item is something started and unfinished.

### 16.1 Still the top of the board

| # | item | why it is stuck |
|---|---|---|
| C1–C12 | **the 27+1 anchor dossiers** (§4) | **0 of 28 anchors are signed.** `apply_balance --confirm` is a NO-OP until W11 sign-off writes targets. This is THE thing blocking the pipeline. Start with C3, the four classes already on spec. |
| C32 | AURORA's `devin/aurora/fix-anchor-readiness` | fixes a crash in `anchor_readiness.py`, conflicts with master in that exact file, and **blocks C1**. Read the branch before touching the tool. |
| C27–C29 | the PR lane (#325, #321) | maintainer ruled: #321 closes as superseded, #325 re-cut small — flags first, then the repaired insurance. ⛔ You do not close, merge or force-push. Boot-gate the insurance change (`player.yaml`, `defaults.yaml`). |
| B2 | the 304-vs-231 reconciliation | ⭐ **CLOSED by you in #335** — `audit_weapon_shape.py --compare-split` accounts for every node: 73 shape-only, zero split-only, W5 counting zero/healing/ally-only flat nodes the positive-damage predicate excludes. Both predicates and all ratchets preserved. Nothing further owed; I have removed it from your queue. |
| C19+ | the `dmg` / `dmg per warhead` producer-consumer mismatch | real, predates the branch, yours to fix on master with a round-trip test, as you proposed. |

### 16.2 The extrapolation program — `docs/design/EXTRAPOLATION_PROGRAM.md`

Phases A–E, gates between each. **You own Phase B onward and the RA2 + TS reference maps
(ruled 2026-09-08).** Points you must not miss:

* ⚠ **`tools/balance/faction_extrapolate.py` (504 lines) ALREADY implements the exchange-rate
  method** — `k = geometric mean over pairs of (cameo_stat / reference_stat)`, per route and per
  stat, unpaired reference rows becoming virtual members at Cameo scale. **Run `--report` and write
  down what it does NOT do. Do not rebuild it.**
* ⚠ **`fit_class.py --spec hp,speed,range_wdist,damage,reload,cost0` ALREADY implements virtual
  anchors** and has never been used. ⛔ **Do not design a virtual-anchor mechanism.** A whole
  session once re-derived a weapon-tier model DESIGN.md had already shipped; `docs/TASK_INDEX.md`
  exists because of exactly this.
* **26 of 27 classes have members in TD/RA1/Japan.** `dreadnought` has none — its five members are
  StarCraft/naval. **Do not invent one.** Report it and let the maintainer decide.
* Phase B gate: every `k` needs **≥3 backing pairs** or it is marked `THIN` and excluded.
* ⛔ **`dps0` stays out of every anchor** while W24 moves.

### 16.3 The RA2 / TS maps, and the open authority question

Everything you need is committed — `docs/reference/ini_corpus.json` (11,870 rows) and
`docs/design/ORIGINAL_UNITS_PEER_OPENRA.md` (2,583 rows). No local game install is required.

⛔ **Read-only on the reference producers.** You report mappings and hand over patches;
Claude-Local lands changes to `assign_references.py`, `reference_distribution.py`,
`faction_routes.py`, `reference_targets.py`. Five agents colliding in that tree cost a week.

⚠ **OPEN MAINTAINER QUESTION — is Romanov's Vengeance the RA2 authority?** It carries 729 buildable
units, more than RA2 + YR ever shipped, and it is 104 of the 119 unclaimed "originals".
`audit_original_coverage` currently **exempts it from the O2 ratchet**, and that exemption is a
placeholder that must be **DELETED** once ruled, never raised. Put the question to the maintainer
with real options; do not resolve it yourself.

⭐ **The biggest remaining precision lever is CA over-tagging** — CA units are tagged with a median
of **5 factions** where the corpus median is **1**. That is what makes the right candidate hard to
see. Three maintainer reviews produced ~15 defects and in **not one of them did the matcher choose
badly** — the right candidate was invisible or had been deleted from the pool. The acceptance test
the maintainer set: **an original MUST have 3 references.**

⚠ **NEVER regenerate `ORIGINAL_UNITS_PEER_OPENRA.md` with a full run or `--mod <x>`.** Use
`tools/reference/splice_peer_section.py`.

### 16.4 Bot modules — §14.2 stands, and it is more work than it looks

The personality system needs **ZERO C#**: a condition-gated player-level `ProvidesPrerequisite`
already ships at `ai.yaml:176`. The hard part is not the mechanism, it is the **dynamic switching**
— personalities that change on triggers and situations, which is what makes bots interesting to
fight. Devin's original plan plus the five-AI review (Perplexity, Grok, Copilot, ChatGPT, Gemini)
are the inputs. A mandatory baseline personality buys nothing; verified.

### 16.5 Structural backlog you can pick up when blocked

* **W23** — retrofit the 47 legacy weapon templates.
* **A5** — 297 legacy weapons still carry inline `Versus`. ⛔ `Versus` lives **ONLY** in
  `^Warhead_*` templates; a different profile means a different template.
* **`audit_dead_warhead_fields`** — ratchet 15. ⚠ Building the field set from C#: match `public`,
  **not** `public readonly` — some AS warheads declare mutable public fields. 2059 warheads once
  carried a `Falloff` their type has no field for, silently, because `FieldLoader.Load`
  (FieldLoader.cs:676) iterates the TYPE's fields and never reads leftover keys.
* **E2 — 89 live `PhysicalState` bindings priced at ZERO** because `extract_stats` reads no
  PhysicalState. Named as the next formula gap.
* **Release drift** — 195 weapons drifted off the shipped build; root cause `04de392b3`
  (2026-07-22), **not** the consolidations. D3 EXTREME is down 27→19 and D1 131→119.
* **Upstream adoption** — `audit_upstream_adoption.py`: 53 duplicates, 266 real candidates. The
  engine **never** moves to `ca-engine`. RV and SP are ancestors of cameo-engine (zero engine work);
  **CN shares a 2026-05-11 base and its 170 patches ARE cherry-pickable**. ⛔ **A new NAME is not a
  new MECHANIC** — RV `Temporal` turned out to be CA `WarpDamage`, ported then reverted. Plan:
  `docs/design/UPSTREAM_MODS.md`.
* **`audit_duplicate_inherits.py`** — the `Parent type X was already inherited` boot-crash class.
  Grep cannot find it; the `@suffix` does not legalise it; a diamond is fine; it is ORDER-dependent.

---

## 17. THE TRAPS THAT HAVE ACTUALLY COST TIME — read this before measuring anything

Six defects landed in one day, **all the same shape: a simplifying assumption where the ledger
already held the answer.** Every one was caught by a human reading a table, not by a test.

| the assumption | what it cost |
|---|---|
| "an unarmed-looking actor is chassis-only" | dropped references for actors whose weapon was right there |
| `arms[0]` — the first armament is the weapon | **495 of 822 armed actors carry 2+ armaments**; 86 rows reported the wrong one |
| `max()` over armaments | GDI battle tank (cannon + rocket) and the 3-barrel Sheridan fire **simultaneously** — they must SUM |
| a permissive `live or arms` fallback | summed 10 mutually-exclusive barrels on the siege chopper to **986,818** |
| `BurstDelay` hardcoded to 5 | correct for **78 of 1,017** weapons |
| the AA test read the slot only | 41 actors → **63** once weapon names were read too |

And the meta-lesson, which bit four separate times: **a filtered pool made me report things as
missing.** I reported 40 "lost" references comparing against a non-hero pool — every one was a hero,
true count **0**. I reported 30 mapping corrections as failed because the tool only writes under
`--write` and I read yesterday's JSON. I reported that no agent had pushed because my `--since`
filter matched author name and **all commits use the shared identity** — 17 branches had moved.
**Before reporting something absent, prove your pool contains it.**

Three conventions the data proved, so you do not re-derive them:

* **`BuildLimit=0` means NO LIMIT, not "cannot build".** A patch premised on the opposite would have
  deleted 110 legitimate actors. I described this bug backwards once; the data settled it.
* **An AA armament is free** — same damage, 1.5× range where allowed, never priced, excluded from
  ground DPS. Global convention, not a property of `anti_air_vehicle`.
* **Subtype is the only durable class signal**, per C46.

⛔⛔ **SUPERWEAPONS ARE NEVER PRICED AND NEVER CHANGED.** Maintainer, emphatically: *"exclude super
weapons from this balance formula since they are all fixed HP! NEVER CHANGE THEM!! SO EXCLUDE THEM
BEFORE ANYTHING IS CHANGED ON ACCIDENT!!!"* Two locks exist in `apply_balance.py`. ⚠ The first
version of that lock **refused every faction** because `changed_paths` is a generator function and
therefore always truthy — a lock that looks like it works is worse than none. If you touch it,
write the test that fails against the broken version.

⛔ **Never raise a ratchet.** Ember's `devin/ember/vfi-signature-fix` is genuinely good work and is
**not on master** because it moves O1 from 8 to 13 over a ratchet of 12. A ratchet is not raised to
land a branch.

⛔ **Never read a background task's notification exit code** — read the `exit=` line in the output
file. `run_all.sh` exited 1 on every clean tree for over a week before anyone noticed.

⭐ **A result that contradicts a binding law is a contradiction, not a finding.** If the generator
implements a law and `verify_generator_sync` reports 0 drift, "nothing conforms" means your
measurement is broken. Check the measurement before writing it up.

⭐ **A file that CONFLICTS is safer than one that does not — the conflict is the warning.** That was
the lesson of your own review, and it is the general form worth carrying: your `class_anchors.json`
finding (eight clean-merging `signed_off: true` rows) was better than mine precisely because the
clean merge was the dangerous one.

---

## 18. What I want back

The same two habits from your PR review, which are rarer than they should be: **you compiled the
actual C# rather than trusting the Python model** (Python ints do not overflow, so the model could
never have found the 32-bit defect), and **you said repeatedly what you had NOT verified**.

So: pin a SHA next to every count. Say what you measured before and after. Say what you did not
check. And where you think I am wrong — as you were right to on the merge analysis — say it
directly. The failure mode in this repo has never been agents who find too little. It is agents who
report more certainty than they measured.
