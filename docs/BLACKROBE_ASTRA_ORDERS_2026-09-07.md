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
> 42 numbered tasks, C1–C42. **⭐ §13 is a 2026-09-08 addendum: read it FIRST — it records what
> your PR review changed in this document, the maintainer's decision on the PRs, and your order of
> work from here.**
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
