# The layered defence stack — shields, Integrity, plating, and how damage lands

**One document for the whole defence stack.** It replaces five separate analyses that each
covered one slice and repeated the others' premises. `BALANCE_PROGRAM_PLAN.md` had already
cited a `docs/design/ARMOR_LAYERS.md` that never existed; this is it.

| where the LAW lives | |
|---|---|
| the binding rules | `DESIGN.md` §12.0c (shield ladder), §12.0e (plating layer), §12.0f (priced survivability), §12.0g (deploying adds a second armour) |
| how a weapon's `Versus` table is built | [`ARMOR_SYSTEM.md`](ARMOR_SYSTEM.md) |
| what is done / next / owned | [`BALANCE_PROGRAM_PLAN.md`](BALANCE_PROGRAM_PLAN.md) W20, W21, W25, W26 |

**This file is the MEASURED ANALYSIS behind those rules** — why each one is shaped the way it
is, and what breaks if it is changed. Read the law first; come here when you need to know
whether a change is safe.

## The stack, top to bottom

```
Shield      an absorbing pool. Only the TOP surviving layer may absorb (`ShieldHolds`) —
            two intercepting layers each returning modifier 1 MULTIPLY, and 1% x 1% made a
            shielded+plated unit effectively immortal with a clean boot.
Integrity   absorbs NOTHING. `INotifyDamage` runs AFTER the damage has landed on health, so
            it buys no survivability and only gates the EMP disable. It shares the FIELD
            SHAPE of a shield (`MaxStrength` + `MaxPercentageStrength`) and nothing else —
            `Integrity.cs` shipped for months with every `[Desc]` copied from `Shielded.cs`,
            and the wrong word spread into a warhead `[Desc]`, the generator comments and a
            handoff. Corrected 2026-08-17.
Armour      the class armour, plus an overlay PLATING when one is granted, plus a second
            armour when the unit deploys (§12.0g). Layer-SELECTED, not averaged.
Health      what is left.
```

⚠ **A missing `Versus` row is not "no opinion".** Both the engine and Cameo's `DamageVersus`
select with `Versus.ContainsKey(type)`, and an EMPTY match list returns 100. For a
layer-selected armour, omitting a row means the plated unit **loses its armour entirely** —
a superheavy would take 100% from bullets instead of ~20%. Every plating gets a row in EVERY
template. Guard: `audit_armor_upgrade_harm.py` I1.

⚠ **An armour upgrade must never increase incoming damage** (DESIGN §12.0e law 4). When W21
flipped armours from MULTIPLY to AVERAGE without restating the values, 98 of 1152 cells took
MORE damage for wearing armour. Same guard.

---

## Plating, shields and Integrity — measured mechanics and shipped design

_Merged 2026-08-23 from `docs/design/PSEUDO_ARMOR_AND_INTEGRITY.md`, unedited below this line._

**Status: ✅ MOSTLY SHIPPED (2026-08-16/17).** Started as research into three maintainer
questions and became the plating layer. What is LIVE, with the binding summary in
`DESIGN.md §12.0e/§12.0f`:

| shipped | where |
|---|---|
| 5 platings `HAZMAT` `COMPOSITE` `BLAST` `REFLECTOR` `ARMOR`, ALL CAPS, full columns in all 94 templates | §D-bis, §G, §H |
| LAYER SELECTION — a plating replaces the class armor | `AreaDamageWarhead.DamageVersus` |
| the column law: every plating averages **70** | §I |
| `effective_HP = HP + shield x 0.529`, measured live | §I |
| 4 upgrades retagged; the generic ones stay multipliers | §G |
| guards `audit_armor_upgrade_harm.py` + `audit_plating_exclusivity.py` | §F, run_all.sh |
| `Waveforce` IntegrityScale deleted (could never fire) | §B, §D-bis |

**STILL OPEN:** the Integrity options I1–I4 (§B) are analysis only — the pool is still 100%
of max HP, so the EMP disable still lands late; and the `IntegrityScaleMultiplier` design
(§D) is written but NOT built, so 15 sites still hard-code `IntegrityScale: 150`.

⚠ **Sections A–E are preserved as WRITTEN, including options that were later rejected**, so
the reasoning stays auditable. Where a later section supersedes an earlier one it says so.
The most important such correction: **§A1–A4 describe the AVERAGING world**, which still
governs class armors but NO LONGER governs platings — §F replaced that with selection.

Three maintainer questions of 2026-08-16, answered from the artifacts rather than from the
design docs:

1. scale `HAZMAT` **and** `REFLECTOR` by the weapon's thermal / chemical / explosive /
   energy composition — and add `REFLECTOR` to the mixed families that lack it;
2. integrity damage below the disable threshold is useless — what do we do;
3. the Tesla EMP upgrade is hard-coded inline; make it a MULTIPLIER on the base weapon.

Plus the general question: **what is the balance formula still not seeing?**

---

### A. The mechanics, as measured

Every claim here was read out of the code or counted in the resolved ruleset. Several
contradict what the design docs assume, so the numbers matter.

#### A1 — Multiple armor types AVERAGE (they do not multiply)

`AreaDamageWarhead.DamageVersus` overrides the engine's product with
`MultiArmorCombination`, default **Average** (the W21 ruling). An actor carrying a base
armor plus an overlay takes `avg(Versus[base], Versus[overlay])`.

#### A2 — ⚠ A MISSING row is EXCLUDED from the average, NOT treated as 100

Both the engine and the Cameo override filter on `Versus.ContainsKey(a.Info.Type)`. So for
a multi-armor actor:

```
weapon has no REFLECTOR row   ->  REFLECTOR is dropped; only the base armor counts
weapon has REFLECTOR: 100     ->  avg(base, 100)  — which is NOT the same thing
```

**Omitting the row is the only way to say "this weapon does not care about reflective
plating".** Writing 100 is a real change that pulls the result toward 100. This is the
single most important fact for the maintainer's question, because "just add REFLECTOR
everywhere" and "add it only where it means something" are genuinely different designs.

(For a SINGLE-armor actor the two coincide: an empty armor list returns 100. That is why
"a missing row resolves to 100" was true in the W23 retrofit and is false here.)

#### A3 — An overlay armor can never cut damage by more than ~50%

With averaging, `effective = (base + overlay) / 2`. Even at the window floor
(`overlay = 10`) the result is `(base + 10) / 2` — just over half. **The whole HAZMAT /
REFLECTOR design space is bounded at a ~2x damage reduction**, and no choice of row value
can exceed it. Any stronger protection has to come from somewhere else (a
`DamageMultiplier`, a second armor, a shield).

#### A4 — How much an overlay protects depends on the BASE armor

Because it is an average, a flat `HAZMAT: 50` gives wildly different protection:

| target | base Versus (chem weapon) | with HAZMAT 50 | reduction |
|---|--:|--:|--:|
| unarmoured infantry | 200 | 125 | **37%** |
| superheavy tank | 60 | 55 | **8%** |

Thematically that is defensible — suits are for infantry — but it is an accident of the
averaging rule, not a decision. It also means the row value alone does not express intent;
the intent is a *reduction*, and the row that produces it depends on the target.

#### A5 — Integrity does NOT absorb damage

`Integrity` is an ELECTRONICS pool, not a shield (its own `[Desc]` says so). Two things
drain it, and **neither reduces the HP damage**:

* `INotifyDamage.Damaged` — subtracts the damage **1:1**, but only for damage whose types
  overlap `AffectedByDamageTypes` (Cameo uses `Tesla`);
* `AreaDamageWarhead.ApplyIntegrityScale` — subtracts a further `damage x IntegrityScale/100`.

So the drain rate is `(1 if Tesla-typed else 0) + IntegrityScale/100` per point of damage
dealt.

#### A6 — The pool is 100% of max HP, and the disable fires at zero

`^UnitDisable` sets `MaxPercentageStrength: 100` (`^EpicAirUnitTemplate` 200). At
`Strength <= 0` the `electronics` condition is revoked, which grants `empdisable` — the
actor is disabled. Strength then banks down to `-MaxStrength`.

Regen: `DamageRegenDelay: 75` ticks (~3 s, **reset by every hit**), then `RegenAmount: 1000`
every tick. A 20 000-HP unit refills in 20 ticks (~0.8 s).

#### A7 — Census (resolved, transitive through `Inherits`)

| trait / armor | concrete actors | of 3107 |
|---|--:|--:|
| `Shielded` (the real shield layer) | 1592 | 51% |
| `Integrity` (the EMP pool) | 1233 | 40% |
| `HAZMAT` armor | 329 | 11% |
| `REFLECTOR` armor | 16 | 0.5% |

None of these is dead code. `HAZMAT` is the third-commonest armor type in the mod.

---

### B. Question 2 answered: WHY integrity damage is useless — and it is not the scale

Drain rate `x` damage until the pool (= 1x MaxHP) empties:

| family | `IntegrityScale` | carries `Tesla` type? | drain / damage | damage to disable | target HP left |
|---|--:|---|--:|--:|--:|
| Tesla | 100 | ✅ | 2.00x | 0.50 x MaxHP | **50%** |
| Storm | 50 | ✅ | 1.50x | 0.67 x MaxHP | **33%** |
| Quantum | 33 | ✅ | 1.33x | 0.75 x MaxHP | **25%** |
| **Waveforce** | 20 | ❌ | **0.20x** | **5.00 x MaxHP** | **NEVER — dies 5x over** |

**The finding is sharper than the maintainer's framing.** Tesla is fine; the disable lands
at half health, which is a real effect. What kills the axis is the **damage TYPE**, not the
scale value: `Waveforce` never received `Tesla` in its `DamageTypes`, so it loses the 1:1
passive drain and keeps only its 20% scale — a factor of six. Its `IntegrityScale: 20` is
decorative. (Its `_Percentage` twin *does* carry `DamageTypes: Tesla`, but the twin deals
~1% of max HP a hit, so emptying the pool through it alone takes ~80 seconds of sustained
fire.)

Two further structural problems:

* **Overdrain buys almost nothing.** Strength banks to `-MaxStrength`, but regen is
  1000/tick, so a full overdrain holds the disable ~0.8 s longer — against a 3 s
  `DamageRegenDelay` that any hit resets anyway. There is no reward for exceeding the
  threshold, so the axis is a cliff with nothing on either side of it.
* **The pool scales with max HP.** A tank's electronics are not ten times tougher because
  its armour is. Tying the pool to HP makes big units disproportionately EMP-proof, which
  is backwards for what EMP is *for*.

#### Options

| # | change | effect | cost |
|---|---|---|---|
| **I1** | `MaxPercentageStrength` 100 -> **25** | disable lands at 87% HP (Tesla), 81% (Quantum) — the axis starts mattering | one number |
| **I2** | give every integrity family the `Tesla` damage type | fixes Waveforce outright (0.20x -> 1.20x) | generator table |
| **I3** | pool becomes a FLAT `MaxStrength` per class, not %HP | EMP stops scaling with armour; a scout and a mammoth are equally disablable, which is what electronics means | needs per-class values |
| **I4** | slow regen (`RegenAmount` 1000 -> ~2% of max per tick) | overdrain finally buys disable TIME, so the threshold stops being a cliff | one number, but changes every EMP duel |
| **I5** | make the pool absorb damage | rejected — that makes it a second shield, which its own docs forbid, and W21's "two intercepting layers must never share a hit" applies | — |

**Recommendation: I2 first** (it is a correctness fix — a family that declares an EMP role
and cannot deliver it is a bug), then **I1** as the cheap lever that makes the axis live,
with **I3 + I4** as the principled version once units are finished. I3 in particular should
wait: it interacts with the class anchors.

---

### C. Question 1 answered: scaling HAZMAT and REFLECTOR

#### The problem, stated precisely

`HAZMAT: 50` is a **constant** on every family (`family(hazmat=50)`), suppressed only for
Sonic and Magic. A flamethrower and a nerve-gas shell are blunted identically by a hazmat
suit, which is exactly what the maintainer objected to. `REFLECTOR` is worse: it exists on
**one** table — Tesla's `ExtraDamage` chip — so 30 energy and blended-energy families have
no opinion about reflective plating at all, and by A2 that means the plating does nothing
against them.

#### The composition model

Every family already declares its composition; it just is not read as one:

* `FAMILY_PHYSICAL_STATE` says which meter it drives (`Flame`->Temperature 100,
  `Chemical`->Corrosion 100, `Cryo`->Temperature -100);
* `BLEND_FAMILIES` says what a blend is made of (`Plasma = Flame + Chemical`,
  `Waveforce` = all five primitives);
* `PHYSICS_RANK` already ranks field-coupling for the Shield axis.

So a family's `chem_share` (what a suit stops) and `energy_share` (what a mirror stops) are
derivable rather than invented.

#### Options

**Option C1 — share-scaled depth (simplest).**
```
HAZMAT    = round(100 - HAZ_DEPTH   x chem_share)     # omit the row when chem_share == 0
REFLECTOR = round(100 - REFL_DEPTH  x energy_share)   # omit when energy_share == 0
```
With `HAZ_DEPTH = 90`: Chemical/Toxic (1.0) -> 10, Plasma (0.5) -> 55, Flame (0.6) -> 46,
Bullet (0) -> **omitted**. One constant per axis, per-family shares, and A2 respected.

**Option C2 — derive both shares from the physical-state system.** `chem_share` =
`PhysicalStateScale/100` for Temperature/Corrosion families, averaged through
`BLEND_FAMILIES` for blends. Most principled and self-maintaining — a new blend gets a
correct HAZMAT for free — but it leaves the energy axis undefined, because there is no
"photonic" meter. Needs C3 for the other half.

**Option C3 — an explicit `ENERGY_RANK` table for REFLECTOR.** Deliberately **not**
`PHYSICS_RANK`: that ranks coupling to a force FIELD, and a mirror is not a field. A mirror
stops *photons* — so Laser and Prism should be at the top, while Tesla (which
`PHYSICS_RANK` puts at 1.00) should be near the bottom, because a mirror does nothing about
a lightning bolt. Reusing `PHYSICS_RANK` here would be a category error that happens to
look tidy.

**Option C4 — express the intent as a REDUCTION, not a row.** Because of A3/A4 the row
value does not mean what it looks like. Author `hazmat_reduction = 0.30` and let the
generator solve the row against a reference base armor. Most honest, most machinery.

**Recommendation: C2 for HAZMAT + C3 for REFLECTOR, emitted through C1's formula**, with
the row OMITTED whenever the share rounds to zero. C4 is the right long-term shape but
should wait until the reduction targets are themselves decided.

#### Sanity bounds to respect

* Never below the window floor (10) — a pseudo-armor is still a Versus row.
* Never above 100 — an overlay that makes a weapon *better* is a different mechanic.
* By A3, the strongest possible suit is ~2x, so `HAZ_DEPTH` above ~90 buys nothing.

---

### D. Question 3 answered: the EMP upgrade should be a MULTIPLIER

#### What it looks like today

```yaml
PortaTesla_EMP:
    Inherits: PortaTesla
    Warhead@Tesla_Heavy:
        IntegrityScale: 150          # hard-coded, x15 across the tree
    Warhead@EMPUnit: AffectsIntegrity
        Damage: 10000                # a SECOND hard-coded number
```

**15 sites** carry `IntegrityScale: 150` inline. The maintainer is right that this is
wrong, and there is a second reason beyond ugliness: **150 is not a multiplier**. On Tesla
(base 100) it is 1.5x; on Quantum (base 33) the same literal would be **4.5x**. The number
means something different on every family, so it cannot be shared — which is precisely why
it got copied fifteen times.

#### The design

Add one field to `AreaDamageWarhead`:

```csharp
[Desc("Percentage MULTIPLIER applied to IntegrityScale, so an upgrade template can say",
      "'twice the EMP' once instead of restating an absolute value per family.")]
public readonly int IntegrityScaleMultiplier = 100;
```
with `ApplyIntegrityScale` using `IntegrityScale * IntegrityScaleMultiplier / 100`.

Then the generator emits one upgrade template per family+level, carrying nothing else:

```yaml
^Upgrade_EMP_Tesla_Heavy:
    Warhead@Tesla_Heavy:
        IntegrityScaleMultiplier: 200
```

and every upgrade weapon becomes exactly the one inherit the maintainer asked for:

```yaml
PortaTesla_EMP:
    Inherits: PortaTesla
    Inherits@emp: ^Upgrade_EMP_Tesla_Heavy
```

200% then means 200 on Tesla and 66 on Quantum automatically — the maintainer's own
example, and the reason the multiplier is the right primitive.

⚠ **`Inherits` POSITION is semantic** (LESSONS_LEARNED, 2026-08-16): the upgrade inherit
must come AFTER the base so the multiplier is not overridden back. The upgrade template
carrying *only* that one field keeps the blast radius of that rule small.

⚠ **The separate `Warhead@EMPUnit: AffectsIntegrity` chips are a different question.** They
are a flat, damage-independent drain and they duplicate what `IntegrityScale` now does
proportionally. They should probably be retired in the same sweep — but that changes
behaviour, so it is a maintainer call, not a refactor.

---

### D-bis. ✅ SHIPPED 2026-08-16 — the maintainer's rulings

#### 1. Waveforce loses `IntegrityScale` entirely

> *"waveforce should remove the integrity damage entirely because it can never actually
> reach a full integrity damage, so that it is not calculated in the balance formula without
> any effect."*

Deleted from `FAMILY_INTEGRITY_SCALE`. The second half of that sentence is the important
half: **a knob that does nothing in play but is still read by the pricing model is worse
than no knob**, because the weapon is charged for an effect it cannot deliver. (E3 says
`IntegrityScale` is not priced *today* — but it is on the fix list, and the moment it is,
Waveforce would have started paying for a disable that needs 5x the target's max HP.)

The alternative — granting Waveforce the `Tesla` damage type so the passive drain fires —
was deliberately NOT taken. That would give a 3/5-kinetic blend the same EMP status as a
Tesla coil, which is a design claim nobody made. If Waveforce should have an EMP role it
needs both halves, chosen on purpose.

#### 2. HAZMAT and REFLECTOR are now derived from composition

> *"before when armors were multiplied a HAZMAT and REFLECTOR versus value of 50 means it
> would also half the incoming damage from those weapon types right? now that it is averaged
> it should be at what?"*

**The answer is ~10, and the reason is that averaging silently halved every overlay.**
Under multiplication a row of 50 meant exactly "half the damage", target-independent. Under
averaging the same 50 gives `(base + 50)/2` — at base 100 that is 75, a **25%** cut, not
50%. Restoring the old feel needs a row of 0, which is immunity; the window floor of 10 is
as close as the mechanic allows (a 45% cut).

So the row is now SOLVED from the reduction it should produce:

```
effective = (100 + x) / 2 = 100 - 100 R        ->        x = 100 - 200 R
```

The reference base of 100 is not an assumption — **W25 S1 pinned every family's Versus mean
to exactly 100**, so 100 *is* the average armor row a weapon writes. That is a second thing
S1 bought that was not planned for: overlay armors became solvable.

With `OVERLAY_DEPTH = 0.45`, `x = 100 - 90 x share`, and two composition tables supply the
shares — `CHEM_SHARE` (what a sealed suit stops) and `ENERGY_SHARE` (what plating stops).
Blends average their parents, so `Waveforce` (Flame + Chemical + Railgun + Laser + Tesla)
gets **both** rows automatically at 68/68, which is exactly the gap the maintainer spotted.

⚠ `ENERGY_SHARE` is deliberately **not** `PHYSICS_RANK`. That table ranks coupling to a
force FIELD, where Tesla is top at 1.00. Plating is a MIRROR: coherent light (Laser, Prism)
is the canonical case, while electrical discharge arcs and conducts rather than reflecting,
so Tesla sits at 0.60. Merging the two would have been a category error that happened to
look tidy.

| family | chem | energy | HAZMAT | REFLECTOR | suit / plating buys |
|---|--:|--:|--:|--:|---|
| Toxic | 1.00 | — | **10** | — | 45% less |
| Chemical | 0.95 | — | 14 | — | 43% less |
| Flame · Inferno | 0.70 | —·0.70 | 37 | —·37 | 32% less |
| Plasma | 0.82 | 0.45 | 26 | 60 | 37% / 20% |
| **Waveforce** | 0.36 | 0.35 | **68** | **68** | 16% / 16% |
| Quantum | 0.05 | 0.58 | — | 48 | — / 26% |
| Tesla | — | 0.60 | — | 46 | — / 27% |
| Laser · Prism | 0.15·0.10 | 1.00 | 86·— | **10** | — / 45% |
| Bullet, Cannon\*, Missile\*, Flak, Melee, Arrow, Concussion | — | — | — | — | **rows omitted** |

Rows below a 5% effect are omitted rather than written (`OVERLAY_MIN_EFFECT`): by A2 a
present row joins the average and moves the result, so a 4% row is a real-but-invisible
change that still costs a line and a reader's attention.

⚠ **This is a real balance shift for the 329 HAZMAT actors.** They used to carry a flat
`HAZMAT: 50` against *every* family, i.e. a general 25% damage reduction from all sources.
Ten kinetic families now omit the row entirely, so hazmat infantry are markedly squishier
against bullets and shells — which is the correct semantics (a sealed suit does not stop a
bullet) and is what the ruling asked for, but it is a nerf and should be watched in play.

The `_ExtraDamage` chip now reads its overlays from the same function instead of the
hand-set `REFLECTOR: 50` it carried: the chip belongs to the same family, and a hazmat suit
cannot care which warhead of a weapon hit it. A second source for one cell is the exact trap
that let Tesla's Shield be contested for months.

### F. ⚠ CONFIRMED BUG — an armor plating can make a unit take MORE damage

> *"now that I think about it would that mean that averaging can also make the unit take MORE
> damage? this is a serious concern and something you need to take a deep look into!"*

**Yes. Measured across the live matrix: 98 of 1152 cells, 8.5%, up to 1.84x MORE damage.**

The arithmetic is unavoidable: `effective = (base + plating) / 2` is an INCREASE whenever
`plating > base`. Any unit whose class armor already resists a weapon better than the plating
does is *punished for wearing the plating*. It hits heavy units hardest, because they are the
ones with low (resistant) class rows — which is precisely backwards.

Narrowing HAZMAT to the maintainer's definition (fire / chemical / radiation only — Laser,
Prism, Demolition and Concussion dropped to zero) removed **the four worst cells outright**
and cut the total to **57 (5.4%), worst case 1.43x**. That is a real improvement and it
carries its own lesson — *a share too small to matter is not harmless; averaged against a
resistant armor it INVERTS* — but 57 inversions is still a broken mechanic. **The taxonomy
fix is not sufficient. The combination rule has to change.**

#### The fix already exists in the tree — for shields

```yaml
    Armor:
        RequiresCondition: !shielded        # base armor DISABLED while shielded
    Armor@shielded:
        Type: Shield
        RequiresCondition: shielded         # shield armor INSTEAD OF, not as well as
```
`mods/cameo/rules/defaults.yaml:7290`. The shield layer already does exactly what the
maintainer proposed — layer SELECTION, not combination — in pure yaml, no C# at all. The
plating armors simply never got the same treatment: they add `Armor@HAZMAT` without ever
disabling the base, so they average.

#### ⚠ But the shield precedent does NOT transfer unchanged, and this is the trap

`Shield` has a row in **every one of the 94 templates**. A plating is SPARSE by design — it
only carries rows for the weapon classes it counters. Under pure layer selection, a plating
with no row for bullets leaves the armor list EMPTY, and both the engine and Cameo's override
`return 100` for an empty list. **A superheavy tank with reactive armor would take 100%
from bullets instead of ~20%.** Layer selection plus sparse rows is a catastrophic failure
mode, not a conservative one.

#### Options for the combination rule

| # | rule | never increases damage? | cost |
|---|---|---|---|
| **R1** | keep averaging | ❌ 57 cells invert | none (status quo, broken) |
| **R2** | layer selection, FULL plating profiles (the shield model, literally) | ✅ | 6 platings x 94 templates = **564 hand-designed rows**, and one missing row silently returns 100 |
| **R3** | layer selection, **falling back to the base when the plating has no row** | ❌ still inverts where `plating > base` | small: one branch in Cameo's `DamageVersus` |
| **R4** | `effective = min(base, plating)` | ✅ **provably** | one new `MultiArmorCombination` mode in Cameo's own warhead — no engine edit |
| **R5** | R3 **plus a generator invariant** that a plating row may never exceed that template's lowest class-armor row | ✅ by construction | R3 + a guard, and it pushes plating values DOWN |

**Recommendation: R5**, which is the maintainer's own model made safe. It keeps the intended
semantics — *the plating is what gets hit, when it has an opinion* — while the invariant
forces R3 and R4 to agree, so the mechanic cannot invert even in principle. The invariant is
also good design on its own terms: **a plating that counters a weapon class should be better
against it than any class armor is**, which is exactly what "reactive armor is the answer to
shaped charges" means. R4 alone is the cheapest correct answer if the maintainer wants this
closed today rather than designed.

#### ✅ The invariant is now enforced (2026-08-16), independently of the ruling

**AN ARMOR UPGRADE MUST NEVER INCREASE INCOMING DAMAGE.** Two changes, both compatible with
all five rules above, so neither can conflict with a later decision:

1. **`tools/audit/audit_armor_upgrade_harm.py`** (in `run_all.sh`) checks every
   (template, plating, class-armor) combination and fails on any that inverts. It encodes
   the INVARIANT rather than today's arithmetic, so if the combination rule moves to R4 or
   R5 it goes green on its own and stays useful as the thing that proves it.
2. **`overlay_rows` now lays the plating into `[VERSUS_FLOOR, min(class rows)]`** instead of
   onto a fixed scale, so the invariant holds BY CONSTRUCTION — a plating is at worst equal
   to the best thing the weapon is already resisted by, and better everywhere else. Under R4
   the clamp is simply redundant.

That took the guard from 57 violations to **0**, and it made the platings meaningfully
stronger rather than weaker, because the clamp only ever lowers a row:

| | before | after | reduction |
|---|--:|--:|--:|
| `Waveforce` HAZMAT / REFLECTOR | 68 / 68 | **38 / 37** | 16% → 31% |
| `Tesla` REFLECTOR | 46 | **24** | 27% → 38% |
| `Laser` REFLECTOR | 10 | **10** | 45% (already at the floor) |
| `Plasma` HAZMAT / REFLECTOR | 26 / 60 | **16 / 29** | 37%/20% → 42%/36% |

⚠ **This is a patch, not the fix.** It removes the defect from the values we ship; it does
not remove it from the MECHANIC. Any hand-written plating row, any new armor type added
without going through the generator, and any future actor carrying two platings at once can
reintroduce it — which is why the audit exists alongside the clamp, and why §F's R4/R5 is
still the answer.

**Why this class of bug deserves the guard.** It was invisible to everything we run: the
yaml is well-formed, every value is inside the window, the resolver is happy,
`find_empty_warhead` is 0, and the game boots — a boot gate cannot see a number that is
merely WRONG. It was invisible by inspection too, because the defect is in neither value but
in their INTERACTION: `HAZMAT: 86` is unremarkable, `Heroic: 32` is unremarkable, and their
average is a 1.84x self-inflicted damage increase.

### G. The plating taxonomy — 4 given, 2 proposed

> *"Hazmat against fire, chemical and radiation, BLAST against all the HE weapons
> like demolition, concussion etc, reflector against energy, composite against AP weapons and
> bullets ... try to find another 1 or 2 that fit the real world armors"*

| plating | counters | real-world basis |
|---|---|---|
| **HAZMAT** | Flame, Inferno, Chemical, Toxic, Cryo, Nuclear, + fire/chem blends | NBC suit, sealed overpressure hull |
| **BLAST** | Demolition, Concussion, Thermobaric, CannonHE, MissileHE, Flak, Sonic | spall liner, blast-attenuating V-hull |
| **REFLECTOR** | Laser, Prism, Plasma | ablative / mirrored coating |
| **COMPOSITE** | Bullet, Sniper, CannonAP, Railgun, Arrow | Chobham, ceramic matrix — the anti-KINETIC answer |
| **➕ Reactive** | MissileAP, and the shaped-charge half of the AT families | **ERA / slat armour.** The KE-vs-HEAT split is the actual axis real tank armour is designed around, and it is the one distinction `COMPOSITE` alone cannot express: ceramics beat penetrators, ERA beats shaped charges, and neither does the other's job. |
| **➕ Insulated** | Tesla, Storm, and the electrical share of Quantum / Waveforce | **Faraday cage / grounding mesh.** This also repairs a compromise in §D-bis: I put Tesla on REFLECTOR at 0.60 because the maintainer's ruling said "energy", while noting a mirror does not stop lightning. With `Insulated` in the set, REFLECTOR goes back to being honestly PHOTONIC (Laser/Prism 1.0, Tesla 0) and electricity gets its own real counter. |

Both additions do the same kind of work: they split a category that was hiding two different
physics behind one name. That is the test a seventh type would have to pass too — `Damping`
for Sonic and `Warding` for Magic were considered and rejected, because Sonic is already
served by `BLAST` (both are pressure) and Magic ignores armor by design.

#### Consequences to decide before building

1. **Six platings x 32 families is a real matrix**, but it is generated, not hand-typed — the
   composition shares already exist and each plating reads one axis.
2. **One plating at a time, or several?** If several can stack, every combination rule above
   needs re-checking; R4 (`min`) is the only one that stays safe under stacking.
3. **The 329 HAZMAT actors and 16 REFLECTOR actors need re-tagging** to whichever plating
   their upgrade actually represents — RA2 reactive armor is arguably `Reactive`, not HAZMAT.
4. **E1 grows again**: six plating types priced at zero instead of two.

### H. The plating cycle — real-world reasoning, and what the roster can actually support

#### H1 — every counter and every weakness, with its physical basis

A plating defeats a damage mechanism by a specific physical means; it is weak where that
means does nothing. Both halves are mechanisms, not flavour.

| plating | what it physically IS | COUNTERS because | WEAK TO because |
|---|---|---|---|
| **HAZMAT** | sealed, filtered, overpressured envelope + insulation | thermochemical harm arrives as an AGENT or a heat flux, and a sealed boundary keeps gas and liquid off skin/optics while insulation slows conduction | **kinetic** — a seal has no mass and no hardness; a bullet passes through a rubber suit as if it were not there |
| **COMPOSITE** | hard ceramic tiles in a ductile matrix | a kinetic penetrator is defeated by SHATTERING or eroding it before it reaches the backing plate — ceramic is harder than the rod and destroys it on contact | **shaped charge** — the jet is already liquid metal at 8 km/s; there is nothing to shatter, which is historically why ERA had to be invented on top of composite |
| **Reactive** | explosive sandwich / standoff cage that fires outward | a shaped-charge JET is disrupted by moving plate ACROSS its path, breaking the jet's continuity before it can penetrate | **blast** — ERA bricks are surface-mounted and an HE burst strips or pre-detonates them, leaving the base armour bare |
| **BLAST** | spall liner, V-hull, standoff, energy-absorbing structure | blast is an IMPULSE through the structure; you survive it by spreading it over time and area and by catching the spall the shock throws off the inner wall | **energy** — a liner absorbs mechanical impulse, and a beam delivers none; it deposits heat at a point, which a liner does nothing about |
| **REFLECTOR** | polished / ablative optical coating | radiated energy is defeated by TURNING IT AWAY before absorption — reflectivity is the whole mechanism, and ablation carries away what does couple | **thermochemical** — sustained flame and corrosives foul, soot and etch the surface, and a mirror that is no longer mirror-bright is just thin plate |

The cycle closes: `thermo → kinetic → shaped → blast → energy → thermo`. Every link is a
real defeat mechanism rather than a balance convenience, and an odd cycle cannot collapse
into two mirrored pairs.

#### H2 — ⚠ MEASURED: the roster cannot support five EVEN categories

> *"try to make it balanced for amount of weapon types so each category covers about the same
> number of weapons"*

Total composition share per axis, across all 33 families:

| axis | share of the roster | families it counters |
|---|--:|--:|
| thermochemical | **27.4%** | 8 |
| kinetic | **23.4%** | 6 |
| blast | **22.7%** | 8 |
| energy | **20.1%** | 6 |
| **shaped charge** | **6.4%** | **3** |

**Four of the axes are beautifully even at 20–27%. The fifth is not, and it cannot be made
even without lying about what the weapons are** — only six families carry ANY shaped share,
and only `MissileAP` is shaped-led. Shaped charge fails the maintainer's own niche test, the
one that retired `Insulated`, `Damping` and `Warding`: *"only a few factions have tesla but
everyone has something like energy, AP, HE, fire / chemical"*.

So the honest answer to "find another 1 or 2, but keep it balanced" is: **you can have
balanced, or you can have five, not both.** Three ways out, in preference order:

1. **Ship FOUR** — HAZMAT / COMPOSITE / BLAST / REFLECTOR, at 20–27% each. The
   maintainer's original set, and the measurement says it was right. `COMPOSITE` then
   counters kinetic AND shaped (ceramic and ERA are both anti-armour), which is how a real
   modern tank is built anyway — it carries both at once.
2. **Keep five and accept `Reactive` as a SPECIALIST** — narrow but deep. It should then be
   cheaper or stronger than the other four, because it answers 6% of the roster.
3. **Five by splitting kinetic instead** — `Ballistic` (small arms, fragments, blades) vs
   `COMPOSITE` (penetrators, slugs, jets). Both real, but each lands near 12%, which trades
   one uneven category for two undersized ones.

**Recommendation: option 1.** The four-way split is what the roster actually is, and it is
the maintainer's own first instinct — *"I think those 4 seem to be good for now"*.

#### H3 — corrections made to the composition table

Two families were credited to the wrong counter in the first draft:

* **`Flak` and `MissileAA` were blast-led.** Fragments are METAL MOVING FAST, not
  overpressure — which is exactly why "flak jacket" is a real garment rated in ballistic
  terms. Both are now kinetic-led (0.60 / 0.55), which moves them to `COMPOSITE`.
* **`Sonic` 0.60 → 0.70 blast.** A pressure wave IS overpressure; the energy share was
  overstated by treating "it is a wave" as "it is radiation".

### I. Priced survivability — shields and platings as effective HP (VERIFIED)

> *"since everything deals more damage to shields you can count the 200% shield strength like
> an extra 100% HP ... but right now you also made the average versus value to armor platings
> to 100 right? so it evens out"*

**Both halves verified against the shipped matrix.**

| layer | column mean | 1 point is worth | maintainer's estimate |
|---|--:|--:|---|
| `Shield` | **189.09** | **0.529 HP** | "200% shield ≈ 100% extra HP" — i.e. 0.5. **Confirmed to 9%.** |
| all five platings | **100.0** | **1.000 HP** | "it evens out" — **confirmed exactly**, by construction |

So the pricing rule is:

```
effective_HP = HP + shield_strength x (100 / mean_versus_shield)      # x0.529 today
```

and a plating contributes **nothing** to effective HP on average — it redistributes only.
That is the column law doing exactly the job it was designed for.

#### ⚠ But the plating column mean of 100 is the WRONG target, and the matrix says so

A plating REPLACES the class armor, so what matters is how its column compares to the column
it displaces. Measured per class armor:

| class armor | column mean | a plating at 100 is... |
|---|--:|---|
| `Heroic` | 74.3 | **35% WORSE** |
| `Spaceship` · `Helicopter` · `Bomber` · `Fighter` | 76–80 | **25–31% WORSE** |
| `Concrete` | 97.8 | ~neutral |
| `Steel` … `None` | 102–129 | 2–22% better |

**Six of the sixteen class armors are already better than any plating**, so an aircraft or a
hero that takes a plating gets *worse* — and `td_gdi_upgrade_heavyaircraftarmorplating` is a
live aircraft plating. This is the same failure the averaging bug had, arriving by a
different route: it is not that the plating stacks badly, it is that it displaces something
better.

The fix is not to abandon the column law — the maintainer's stated purpose for it was that
platings be equally good *as each other* (*"so all weapon types combined deal the same
damage"*), which any common mean satisfies. **Lower the common mean to ~70**, just under
`Heroic`'s 74.3, and a plating becomes a genuine upgrade for every armor it can replace while
staying exactly equal across the five. The ~30% durability gain then has to be PRICED, which
is E1's job and is the correct place for it.

### E. What the balance formula still does not see

Measured against `formula.py`, `weapon_efficiency.py` and `target_model.py`.

| # | gap | why it matters | severity |
|---|---|---|---|
| **E1** | ✅ **FIXED 2026-08-17 (both halves).** Weapon side: `armor_weights()` now carries a 17th `Shield` row at its measured damage share, and `weighted_versus` iterates the weights instead of `ARMORS`. Unit side: `extract_stats.survivability()` publishes `effective_hp` for actors that SPAWN with a pool. | ⚠ **The "51% of the roster" figure was wrong** — it counted the 1592 actors carrying `Shielded`, but 1318 of those hold an EMPTY capacity behind `shieldgen >= 1`. Only **58** spawn with a pool, so baseline Shield exposure is **1.432%**, and the weapon-side correction is +0.65% (Bullet) to +3.47% (Tesla), not a repricing. The real hole is the unit side: those 58 carry **+57.8% effective HP at zero cost**. Report: `audit_survivability_pricing.py`. | ~~high~~ **done** |
| **E2** | `PhysicalState` (heat / cold / corrosion) is priced at zero — `extract_stats` contains **0** references to it. | ⚠ **"~89 live bindings" was wrong by 8×. Measured 2026-08-18: 722 bindings on 453 weapons, of which 367 are actually FIRED, carried by 578 armaments** — roughly a quarter of the damaging roster delivers a status meter for free. It is also TWO mechanisms, not one (see below), and the earlier count saw only part of one. Design work exists, the extractor does not. | **high** |
| **E3** | `IntegrityScale` is priced at zero. | 1233 actors carry the pool; a disable at 50% HP is worth real money. | medium |
| **E4** | ✅ **CORRECTED 2026-08-25 — percentage damage has two shapes.** Standalone percentage warheads are absolute at the reference HP; folded `PercentageScale` damage derives from the main Damage and is scalable. The first E4 fix recognized only specially named standalone twins and missed most standalone nodes plus every folded hit. | The model now discovers percentage applications by warhead type. `k_flat_context` includes flat, chip and folded damage; `pct_absolute_context`/`dps_floor` contain standalone damage only; folded basis-point rounding is a separate current-shot residual. Full burst cadence also includes every inter-shot delay and the engine default. Guard: `audit_k_linearity.py`; fixtures: `test_percentage_damage_model.py`. | ~~high~~ **done** |
| **E5** | Upgrades are priced at zero — there is no ΔP report, so a weapon swap is free. | The maintainer has already flagged this; it is the whole upgrade-rebalance prerequisite. | high (deferred by design) |
| **E6** | Inaccuracy and projectile speed are not priced. | A weapon that misses is worth less than one that does not; `reliability` covers spatial falloff, not aim. | medium |
| **E7** | `MinRange` is not priced. | A real artillery drawback that costs nothing. | low |
| **E8** | A5's asymmetry is undocumented in the balance docs: an omitted Versus row and a row of 100 differ for multi-armor actors. | Any future sweep that "fills in missing rows for completeness" would silently rebalance every shielded and hazmat unit. | **trap** |
| **E9** | 23 macro ladders are non-monotone — blend families average their parents and `finish_blend` never re-imposes the ordering law. | The ordering law is "the most important part"; blends quietly opt out of it. Pre-existing, unrelated to W25. | medium |
| **E10** | ✅ **FIXED 2026-08-17** alongside E1 — the comment now says what the tuple is (16 CLASS armors) and why `Shield` and the platings are layers with their own weight rather than rungs on the ladder. | It would have misled exactly the fix E1 needed, which is how it got found. | ~~trivial~~ **done** |

**E1 and E4 were fixed first** (2026-08-17), because both distorted prices *systematically*
rather than for one weapon. Both turned out to be a different size than this table first
claimed, in opposite directions, and the corrections are recorded below rather than quietly
edited away — a severity estimate that moves by 30x is itself a finding.

#### E2 measured — and it is TWO mechanisms, which is why the old count was small

```
Temperature, damage-SCALED   396 bindings   PhysicalStateName + PhysicalStateScale on an AreaDamage warhead
Temperature, discrete APPLY  242 bindings   Warhead@X: ApplyPhysicalState + Amount
Corrosion,   damage-SCALED    84 bindings
                             ---
                             722 bindings on 453 weapons — 367 of them FIRED, on 578 armaments
```

⚠ **Counting only one mechanism is how "~89" happened, and I repeated the mistake mid-measurement**
— a first pass that looked only for `ApplyPhysicalState` reported 242, which is also wrong. The
damage-scaled meters (`PhysicalStateScale`, the larger half) ride on the *damage* warhead and
carry no `ApplyPhysicalState` marker at all.

Two consequences for the fix:

* **The scale units are NOT comparable across mechanisms.** `Amount` is an absolute meter delta
  per hit (`800`, `1200`, `-30000` for cryo — the sign is the direction, heat vs cold), while
  `PhysicalStateScale` is a PERCENTAGE of the damage dealt (`100`, `75`). A pricing term has to
  normalise them before it can add them up.
* **Only two states are live: Temperature and Corrosion.** Everything else in
  `PHYSICAL_STATE_SYSTEM.md` (Sonic, ArmorBreach, Hex, Knockback) is design, not shipped content,
  so E2's scope is exactly these two.

⛔ **What is still owed before the extractor can price it: what a meter is WORTH.** Recording the
bindings is mechanical and needs no ruling; converting them into a `state_w` term does — the
existing note has cryo at 0.75× as an empirical measurement, and
nothing equivalent exists for heat or corrosion. Claim: `physical_state_fired_weapons`.

#### ✅ E2 ANSWERED (2026-08-18) — `tools/balance/physical_state_price.py`

The maintainer's ruling supplies the worth: **1.25× cost, but only for delivery** — *"Cryo seems as
strong as Fire IF it is able to completely freeze a unit BEFORE it dies"*. Built as

```
weight     = clamp01( exposure × delivery(ratio, effect curve) / delivery(bar, cryo curve) )
multiplier = 1 + 0.25 × weight            formula.physical_state_price_multiplier
```

with all three inputs measured from the resolved tree, never assumed. Full derivation in
`PHYSICAL_STATE_SYSTEM.md`; the three findings that matter here:

Building it uncovered **three defects that made the axes behave differently** — all fixed in
`defaults.yaml` on maintainer order (*"the absolute maximum and minimum values are the same!"*):

* ⛔ **D1 — one `Scale` meant two fill rates.** The engine divides by the meter's `range`
  (`MaxValue − MinValue`), not by the `10000` its own `[Desc]` advertises. `Corrosion` shipped
  `MinValue: 0`, so its range was half `Temperature`'s and the same Scale filled heat **twice as
  fast**. Fixed by making Corrosion signed. Corrected count: **223 of 376 bindings** reach full
  effect, not the 124 or the 1 this document previously carried — both were wrong-formula values;
* ⛔ **D2 — corrosion delivered nothing below HALF the meter** (`Corroding: LowerValue 10000`)
  while heat opened at 1%: a 50× gate difference inside one system. Now both open at 1%;
* ⛔ **D3 — every DoT opened at half strength**, because
  `ChangesHealthProportionalToPhysicalState` normalises over the full *signed* range with no
  deviation option. `DamageAtMinimum: -DamageAtMaximum` puts the zero back at a relaxed meter;
* ⭐ **exposure is now the ONLY thing separating the axes** — `Corrosion` sits on **45.0%** of
  priced actors against `Temperature`'s 98.6%, so a corrosion weapon caps at **1.165×** where a
  flame weapon reaches 1.25× despite an identical meter and an identical fill rate. That is what
  separates Flame from Chemical, and nothing in the price model saw it before.

Result: 190 bindings pay the full 1.25×, 174 partially, 12 nothing; **+15.7%** across 276 actors.
Guards: `tools/tests/test_physical_state_price.py` (17 tests) + claims
`meters_filling_before_death`, `corrosion_meter_actors`, `physical_state_fired_weapons`.

⛔ **Still owed by the maintainer:** whether `PhysicalStateScale` stays at **300**. It was chosen
against the wrong arithmetic — `Scale: 100` already cleared the bar at ratio 0.50 — so 300 is a 3×
faster fill that the 1.25× ceiling cannot charge for.

#### E1, as measured and fixed (2026-08-17)

**The premise was wrong, and checking it was the whole job.** "Tesla's `Shield: 400` is free
against 51% of the roster" came from counting the 1592 actors whose resolved ruleset contains a
`Shielded` trait. But `^ShieldedShieldable` (`defaults.yaml:7230`) sets
`MaxPercentageStrength: 100` together with `InitialStrength: 0`, and the regen sits behind
`RequiresCondition: shieldgen >= 1`. That is a **capacity**, not a shield: it starts empty and
stays empty until something fills it.

| bucket | actors | is it durability? | who prices it |
|---|--:|---|---|
| spawns with a pool, ungated | **58** | yes | **E1** |
| empty capacity, needs `shieldgen` | 1318 | no | nobody — correctly |
| pool behind an upgrade | ~216 | yes, but not baseline | **E5** |

The maintainer's own qualifier decides the split — *"that's only if the unit already has armor
or shield included in them"*. A shield the unit spawns with is baseline durability; one an
upgrade grants is not, and charging the base cost for it would overprice every un-upgraded
unit.

⚠ **`!disabled` is not a gate.** It is the standard not-EMP'd/not-captured guard and is TRUE on
a healthy unit. An early version of the classifier treated any `RequiresCondition` as a gate,
which put every Protoss unit (`InitialPercentageStrength: 100`, `RequiresCondition: !disabled`)
in the "needs an upgrade" bucket and reported that the roster had **no** always-on shields at
all — contradicting the maintainer, who was right. Only a POSITIVE token gates.

**The two halves, and their true sizes:**

* **Weapon side — small.** Baseline Shield exposure is **1.432%** of all roster raw damage, so
  adding the row moves a family's `versus` by **+0.65%** (Bullet, `Shield: 165`) to **+3.47%**
  (Tesla, `Shield: 369`). Correctly ordered — energy families pay most, kinetic least — but a
  correction, not a repricing. `armor_weights()` takes the share OUT of the class rows so the
  weights still sum to 1.0 and `versus` stays comparable.
* **Unit side — the real hole.** Those 58 actors hold **12 872 500 HP that is really 20 316 495
  effective HP, +57.8%, priced at zero**. Implied price change: median **×1.378**, up to
  **×1.752**. At a 200% pool the multiplier is **×2.080**, so the maintainer's "count the 200%
  shield strength like an extra 100% HP" was right to **8%**.

⚠ **The Protoss carry a 150% damage multiplier to compensate for their shields.** Pricing the
shield is the prerequisite for retiring that multiplier — they have to land in ONE pass, or the
faction is charged twice for the same thing.

**Why the weapon side stayed on the baseline world.** Counting upgrade-granted shields would
raise the Shield weight from 1.4% to roughly 30% and reprice every energy weapon. That is a
design ruling about whether K prices the baseline or the post-upgrade game, so it is left as a
one-predicate change in `shield_damage_share()` for the maintainer, not decided here.

**Platings need no weight of their own.** Every plating is upgrade-granted, so baseline
exposure is zero and they belong to E5 with the conditional shields. Their columns are also
pinned to a common mean by construction (§F), so once E5 does price them, a plating changes
*where* damage lands, not how much on average.

#### E4, as measured and corrected (2026-08-17; percentage-shape repair 2026-08-25)

Two things had to be separated that the single `k` conflated, and getting the severity right
mattered as much as the fix:

* **`k` as a MEASUREMENT is sound only when every runtime application is counted.** The
  corrected identity is `k == k_flat + (pct_absolute + folded_rounding) / damage_total`.
  `k_flat` contains flat, chip and folded `PercentageScale` damage; `pct_absolute` contains
  standalone `AreaDamagePercentage` / `HealthPercentageDamage`; `folded_rounding` is the
  tiny current basis-point residual. `audit_k_linearity` now compares modeled parts against
  every runtime percentage node by TYPE, not a `_Percentage` naming convention.
* **`k` as a SHAPE COEFFICIENT was false**, and that is what six documents told the reader
  to invert. Measured on the worst case, `AnthraxCloudLarge` (twin = 75% of output):

  | want | old prescription | old actually delivers | error | new |
  |--:|--:|--:|--:|--:|
  | 2.0× | 354 | 1225 vs 1961 asked | **−37.5%** | 887 → exact |
  | 1.5× | 266 | 1103 vs 1471 asked | −25.0% | 532 → exact |
  | 1.0× | 177 | 981 vs 981 asked | 0.0% | 177 → exact |
  | 0.6× | 106 | 883 vs 588 asked | **+50.0%** | UNREACHABLE |
  | 0.4× | 71 | 834 vs 392 asked | **+112.6%** | UNREACHABLE |

  The old form is exact **only at λ=1**, its own fixed point — which is exactly why nothing
  caught it: every check that re-derived a weapon's current Damage passed.

**A standalone percentage warhead is a DPS FLOOR; a folded hit is not.** A weapon delivers
`pct_absolute_context` from standalone percentage nodes at `Damage: 0`, so lowering flat
Damage cannot price it below that. `required_damage()` returns `None` there and `dps_floor`
publishes the bound. Folded `PercentageScale` damage becomes zero with its main Damage and
therefore stays in `k_flat`; putting it in the floor would create damage the engine does not.

**Unit handling is per node.** `HealthPercentageDamage` always uses fixed whole-percent
units; its C# type has no denominator field. Legacy `AreaDamagePercentage` defaults to
`PercentageDenominator: 100` and may author a different positive denominator, including
basis points. Folded `AreaDamage.PercentageScale` defaults to denominator 10000 and uses
the engine's rounded derived units. The shared evaluator reads each form directly; no tag
spelling or global denominator guess is allowed.

---

## Versus normalisation and the Shield ladder — the analysis behind §12.0c

_Merged 2026-08-23 from `docs/design/SHIELD_AND_NORMALISATION_PLAN.md`, unedited below this line._

**Status: PLAN. No code written yet.** Maintainer ordered a full analysis before
implementation. This file is the analysis, the options, and the execution order.

---

### 0. What actually broke, measured

`ARMOR_SYSTEM.md:43` sets the law **`Shield = top + floor`**. It was written when every
profile peaked at exactly **100**, so Shield landed at `100 + {10,25,40}` = **110 / 125 /
140** — always just above the ceiling every other armor obeyed. Clean, and it encoded a
real idea: *shields are the softest layer, so the one value allowed past the cap.*

W13 renormalised profiles to **median = 100**. "Top" stopped being a constant and became a
function of each family's **sharpness**. The rule silently changed meaning:

| template | Shield | top (non-Shield) |
|---|--:|--:|
| `^Warhead_Tesla_Heavy` | **151** | 106 |
| `^Warhead_Tesla_Super` | **160** | 114 |
| `^Warhead_Melee_Medium` | **200** | 174 |
| `^Warhead_Flame_Heavy` | **200** | 161 |
| `^Warhead_Bullet_Light` | 199 | 162 |

**The anti-shield identity is inverted.** A sword now out-damages a Tesla coil against an
energy shield, because Melee's profile is sharp and Tesla's is deliberately flat.

Two further causes compounded it:

1. **The carrier was deleted.** Tesla's 300% / 400% anti-shield lived in a *separate*
   `ExtraDamage` warhead. The universal AreaDamage conversion merged those chips into the
   main warhead — so the identity did not merely dilute, its vehicle was removed.
2. **Two rules contest one cell.** `gen_weapon_template.py` holds the design intent
   (`Tesla: Shield 300`, `Tesla_Super: Shield 400`), but that path only runs for
   hand-designed families. Tesla is *measured*, so `reference_main()` recomputes Shield
   from the corpus profile and the 300/400 is never used.

---

### 1. The maintainer's correction (2026-08-16) — and why it is right

> *"the maximum allowed value is 200 so do 200 + bottom value right? shield is allowed to
> be beyond the 200 limit right? ... basically the shield values just roughly double from
> before."*

Correct, and it is the *same* law, not a new one. The original rule was never "top + floor"
in the sense of "this family's peak" — it was **"the ceiling + floor"**, and under peak-100
normalisation those happened to be the same number. Restoring the intent under the new
window means:

```
Shield = CEILING (200) + floor          # 210 / 225 / 240 …
```

Shield is explicitly exempt from the `[10, 200]` window, exactly as it was exempt from the
old 100 cap. Everything roughly doubles, which is the correct consequence of the window
doubling.

**But `CEILING + floor` alone cannot express anti-shield identity** — it depends only on
the family's floor, so Tesla and a rifle land within ~30 points of each other. Hence the
second half of the maintainer's proposal.

---

### 2. The three inputs — with a measured verdict on each

Maintainer's proposal: derive Shield from three independent sources and average them.
The idea is sound. The weights, however, must follow the data:

#### Input 1 — the reference corpus ⚠ **EMPTY FOR THIS CELL**

`docs/reference/versus_raw.json`: **3150 profiles / 16 mods**, 34 distinct armor names.

| armor | rows | mods |
|---|--:|--:|
| `heavy`, `wood`, `none`, `concrete`, `light` | ~2650–2850 each | 16 |
| **`shield`** | **13** | **1** |

**Verdict: the corpus cannot produce a per-family Shield ladder.** 13 rows from one mod
across 32 families × 4 levels is noise. Averaging it in as a third of the answer would
dress up an invention as a measurement — the exact failure mode
was built to prevent.

**What the corpus IS for here:** the other 33 armors have thousands of rows, so it fully
supports the *normalisation* work in §3 — which is the prerequisite for input 3 anyway.

#### Input 2 — design intent + real-world physics ✅ **carries the weight**

The only input with genuine per-family signal. Framework in §4.

#### Input 3 — `CEILING + floor`, after mean-normalisation ✅ **structural**

Always computable, ties Shield to the family's own ladder, and reduces exactly to the
historical rule. Its weakness is that it is identity-blind, which input 2 supplies.

#### Recommended weighting

**Shield = mean(input 2, input 3)**, with input 1 used only as a sanity bound where its 13
rows apply. Presented as a 3-way average this would be dishonest arithmetic; presented as
"design × structure, checked against what little evidence exists" it is defensible. If the
maintainer prefers a literal 3-way average, input 1 must first be widened — see §6 Option C.

---

### 3. The prerequisite — normalise every family's Versus MEAN to 100

> *"all warheads average all versus values at 100 to make them comparable"*

This is the most consequential idea in the whole discussion and it should land **first**,
because Shield depends on it and so does everything else.

**Today:** profiles are normalised to **median = 100**. Their *means* differ (Bullet_Light
87, Melee ~74, Concussion ~85), so a family's mean is a hidden magnitude multiplier.

**Consequence of switching to mean = 100:** since `K` is a share-weighted average of the
profile, a family's mean IS its contribution to priced DPS. Pin every mean to 100 and:

- **`K` becomes shape-only.** Choosing a family no longer changes a weapon's total output,
  only *how that output is distributed across armors*.
- **`Damage` becomes the sole magnitude knob** — which is exactly what the balance pipeline
  wants, and it removes the "profile change must be paid for" coupling that made the W23
  retrofit need a `Damage` rescale at all.
- **Families become directly comparable**, which is the maintainer's stated goal.

⚠ **This supersedes the W13 median-normalisation** and re-derives all 88 templates. It is a
one-line change in `aggregate_archetype.py` (`NORMALISE_REFERENCE`) plus a re-run — but it
moves every profile, so it must be paired with a `report_versus_change.py` pass and a
pipeline re-price.

#### The class-tilt law (also new)

> *"light weapons have a bigger damage to light armor types while heavy weapons have a
> bigger damage to heavy armor types with medium weapons having bigger damage to medium
> armor types ... the super type should be the generalized type that deals good damage
> against everything."*

With the mean pinned at 100, tilt is free — it costs nothing in total output, it only moves
where the output lands. Formalised:

| level | tilt | shape |
|---|---|---|
| Light | toward light armors (None, Flak, Plate, Scout, Wood) | sharp, front-loaded |
| Medium | toward mid armors (Light, Medium, Steel, Heroic) | sharp, centred |
| Heavy | toward heavy armors (Heavy, Superheavy, Concrete) | sharp, back-loaded |
| **Super** | **flat** — good vs everything | **the generalist; lowest spread** |

This gives the 2×/4×/8× band a *meaning* per level rather than a free parameter, and it
makes Super's identity structural rather than just "bigger numbers".

⚠ **Tension to resolve:** the existing `^Warhead_Nuclear_Super` is deliberately ordered
`BLD > VEH > AIR > INF`, which is a tilt, not a generalist. Either Nuclear is an explicit
exception or the Super law needs softening. **Maintainer decision.**

---

### 4. Input 2 — the physics framework for Shield, per family

An energy shield stops **energy and momentum at a boundary**. What matters is whether the
weapon's mechanism couples to a field or bypasses it. Proposed reasoning, to be reviewed
family by family rather than accepted wholesale:

| mechanism | vs an energy shield | families | rationale |
|---|---|---|---|
| **Direct electrical / EM** | **strongest** | Tesla, Storm | current couples straight into the field; the shield IS the conductor. This is the maintainer's stated law and the anchor of the scale. |
| **Coherent energy** | strong | Quantum, Railgun, Prism, Laser | delivers energy the emitter must absorb; scales with coherence |
| **Blended energy** | above average | Plasma, **Waveforce**, Inferno | part field-coupling, part thermal |
| **Thermal / chemical** | average | Flame, Chemical, Toxic | a shield stops heat and reagents well; little field coupling |
| **Kinetic / explosive** | below average | Bullet, Cannon*, Missile*, Flak, Concussion, Demolition | momentum is what shields are designed for |
| **Physical contact** | **weakest** | Melee, Arrow | a blade is the canonical thing a shield stops |

Note this **exactly inverts today's table** — Melee is currently top and Tesla bottom.

Level scaling within a family: shields are an *energy budget*, so a bigger discharge
depletes more. Suggested `Light < Medium < Heavy < Super`, with Super highest.

⚠ **Hard constraint (maintainer): no two families may share a Shield value.** Enforceable
with the same `MIN_GAP` machinery the armor ladder already uses. With 32 families × 4
levels = 128 distinct values needed, spread across roughly 210–400, gaps land ~1.5 apart —
tight but feasible. **If it proves too tight, widen the Shield range rather than allow ties.**

---

### 5. Execution order

Each step has a VERIFY and is independently boot-gateable.

| # | step | verify |
|---|---|---|
| **S1** | Switch normalisation median → **mean = 100** in `aggregate_archetype.py`; re-derive `family_profiles.json` | every family's mean == 100 ± 1 |
| **S2** | Implement the class-tilt law (Light/Medium/Heavy tilt, Super flat) | tilt direction matches the level for all 88 templates |
| **S3** | Rebuild Shield: `mean(physics_table, CEILING + floor)`, uniqueness-enforced | Tesla top, Melee bottom, 0 duplicate Shield values |
| **S4** | Regenerate all 88 templates; report the movement | `report_versus_change.py` + `verify_generator_sync.py` drift = 0 |
| **S5** | Re-price through the pipeline | `extract_stats --check` 0 drifted; needs `apply_balance --confirm` (maintainer order) |

**S1–S3 are pure generator work** — no yaml hand-edits, consistent with CLAUDE.md rule 3.

---

### 5b. MEASURED: neither structural formula can carry the identity (2026-08-16)

Maintainer asked whether `top` could be kept via a geometric mean:
`sqrt((200 + floor) x (100 + top))`. Computed over all 96 live templates:

| formula | range | spread | distinct values |
|---|---|--:|---|
| `200 + floor` | 210 – 265 | **1.26x** | **41 / 96** |
| `sqrt((200+floor)(100+top))` | 165 – 253 | **1.54x** | **44 / 96** |

The geometric mean IS better — wider spread, fewer ties — but both fail, and the reason is
mathematically interesting: **`floor` and `top` are anti-correlated by construction.** Every
profile is normalised, so a sharp family necessarily has a low floor and a high top, and a
flat family the reverse. Multiplying the two therefore CANCELS most of the variation — the
product is close to an invariant of the normalisation rather than a property of the weapon.
`Sonic_Medium` (top 55, floor 55) and `Melee_Heavy` (top 165, floor 35) land 199 vs 250.

Both formulas also violate the **no-two-families-share-a-Shield-value** rule outright: 41
and 44 distinct values across 96 templates means more than half are ties.

**Conclusion, now with numbers:** a structural rule can set the SCALE (where the Shield band
sits, and that it tracks weapon strength) but it cannot set the RANK. Anti-shield identity
is not recoverable from a normalised profile's own shape, because normalisation is exactly
what removes it. So:

```
Shield = physics_rank (input 2)  x  structural_scale (input 3)   then uniqueness-spread
```

`input 3` = `sqrt((200+floor)(100+top))` is the better of the two structural terms and is
recommended as the scale factor — it keeps `top` in the formula as the maintainer wanted,
and its near-invariance is a virtue in that role: it anchors the band without fighting the
physics rank for control of the ordering.

Tesla must end up several times a sword, not 1.2x. Only input 2 can do that.

---

### 6. Options for the maintainer

**Option A — full programme (recommended).** S1–S5 as above. Fixes the root cause
(normalisation), gives every level a structural identity, and restores Tesla. Largest
change; every profile moves.

**Option B — Shield only.** Just S3 with `CEILING + floor` plus the physics table, leaving
median-normalisation in place. Much smaller and fixes the reported bug, but leaves the mean
as a hidden magnitude multiplier, so families stay non-comparable and W23-style "pay for
the profile change" rescales remain necessary forever.

**Option C — widen input 1 first.** Before deciding, mine the 16 mods for *shield-like*
armor types under other names (`plasma_shield`, `energy`, `barrier`, forcefield analogues)
and for the SC/SC2 lineage where shields are a first-class mechanic. Would turn input 1
from 13 rows into something real and make a genuine 3-way average possible. Costs a
data-mining pass; delays S3.

**Recommendation: A, with C run in parallel** as a check on the physics table rather than a
blocker — the physics ordering is confident enough to proceed, and the corpus can confirm
or correct it afterwards.

---

### 6b. ✅ ALL FOUR DECISIONS TAKEN (maintainer, 2026-08-16)

1. **Tesla reaches 400** — *"if the formula allows it then yes but you need to calculate the
   exact value"*. It does. Calibrating `Shield = physics_rank x level x geometric_scale` so
   that `Tesla_Super` lands exactly on 400 gives **K = 1.39186**.
2. **Nuclear becomes a generalist** — *"nuclear can be changed now to be a generalist"*. No
   exception; the Super-is-flat law applies universally. The `BLD > VEH > AIR > INF` tilt is
   retired and `HAND_TUNED` comes off Nuclear.
3. **Options A + B + C combined** — full normalisation + tilt + Shield rebuild, with the
   corpus mining run as a parallel check on the physics table rather than as a blocker.
4. **Shield STAYS a `Versus` row.** Maintainer: *"shields have their own armor type so they
   feel unique. Energy weapons deal more damage to shields than physical weapons but
   physical weapons deal more damage to vehicle armor than energy weapons"* — i.e. Shield is
   a genuine rock-paper-scissors axis, not a redundant expression of the W21 layer.

#### The computed ladder

| template | rank x level | geometric scale | Shield NOW | **Shield NEW** |
|---|--:|--:|--:|--:|
| `Tesla_Super` | 1.25 | 230 | 160 | **400** |
| `Storm_Super` | 1.19 | 235 | 199 | 388 |
| `Tesla_Heavy` | 1.12 | 225 | 151 | **350** |
| `Railgun_Heavy` | 0.87 | 249 | 200 | 302 |
| `Quantum_Heavy` | 0.92 | 234 | 160 | 299 |
| … | | | | |
| `Melee_Medium` | 0.22 | 249 | 200 | **76** |
| `Melee_Light` | 0.20 | 249 | 200 | 69 |

**Range 69–400 (5.80x). `Tesla / Melee` moves from 0.76x (inverted) to 4.60x.**
Distinct values: **77 of 93** — the remaining 16 ties are resolved by the existing `MIN_GAP`
uniqueness pass, exactly as the armor ladder already does.

⚠ **This restates a historical invariant and that is deliberate.** Shield used to be "the one
value always allowed ABOVE the cap", because shields were assumed uniformly soft. Under the
maintainer's ruling they are not — they are soft to energy and *hard to kinetics*. So
physical families land BELOW 100 (a sword at 76 is the canonical thing a shield stops) and
Shield is now exempt from the window in **both** directions. The old invariant was a
consequence of the old assumption, not a law in its own right.

### 6c. S2 CLASS TILT — the exact armor grouping (maintainer 2026-08-16, CONFIRMED)

The tilt is **within a family**, comparing that family's own levels against each other (e.g.
Flame Light vs Flame Medium vs Flame Heavy), NOT across families.

| tier | tilts toward | sub-ladder positions |
|---|---|---|
| **Light** | `None`, `Wood`, `Scout`, `Light`, `Fighter` | INF0, BLD0, VEH0, VEH1, AIR0 |
| **Medium** | `Flak`, `Steel`, `Medium`, `Bomber`, `Helicopter` | INF1, BLD1, VEH2, AIR1, AIR2 |
| **Heavy** | `Plate`, `Concrete`, `Heavy`, `Superheavy`, `Spaceship` | INF2, BLD2, VEH3, VEH4, AIR3 |
| **Super** | nothing — **FLAT**, good against everything | the generalist |

Validated: 15 of 16 armors assigned, no armor in two tiers. The 16th is **`Heroic`**, and its
absence is CORRECT — Heroic is a DERIVED armor (`Plate x Scout / peak`, DESIGN.md §12.0b), so
it must fall out of the finished profile rather than be assigned a tier of its own.

⚠ **Super is flat, not uniform.** The no-two-values-identical ladder law still applies — Super
has the *shallowest curve*, not equal numbers. Nuclear is now included (its `BLD>VEH>AIR>INF`
tilt and `HAND_TUNED` exemption are retired).

### 6d. SHIELD TIE-BREAK — the ordering rule (maintainer 2026-08-16)

> *"the old rule still holds: heavy deals more damage to shields than light. Actually if
> something has the same value always prioritize it like that light->medium->heavy->super
> with super dealing the most damage to shields and light the least"*

So the uniqueness pass is not an arbitrary nudge — it has a defined direction:

1. **Within a family, Shield MUST ascend** `Trace < Light < Medium < Heavy < Super`.
2. **Across families**, ties are broken by that same level order, Super winning.
3. Only then spread the remainder onto free integer slots.

With 96 templates in the closed range **[100, 400]** there are 301 integer slots, so a
collision-free assignment always exists — the maintainer's point that fitting 96 values in
that band is not a problem is correct, and it means the pass never needs to widen the range.

⚠ **Implementation note:** this is a GLOBAL pass and `shield_for()` is per-family, so it
cannot see cross-family collisions. It needs a two-phase generation — compute every raw
Shield first, then assign final values — which is a small refactor of the generator's main
loop, NOT another per-family formula tweak. That refactor is the next step.

### 6e. ✅ S1 SHIPPED — mean-normalisation to 100 (2026-08-16)

`gen_weapon_template.mean_normalise()`, applied to every MAIN warhead on every branch
(measured, designed, flat, pct and blend) immediately before `shield_for`.

**Measured before:** family means ran **22.0** (`Magic_Light`) to **106.1**
(`MissileAA_Light`), averaging **75.0** — a hidden magnitude multiplier of up to 4.8x
between two families that both looked "normalised". **After: every one of the 94 templates
sits at 100.0 ± 0.2.**

#### The constraint nobody had priced

A plain `v x 100/mean` rescale breaks the ceiling on **11 of 94** templates, worst
`Melee_Medium` at **316**. This is arithmetic, not a bug: with the mean pinned at 100,
`max <= 200` *means* `max <= 2 x mean`, so a profile that is brilliant against three armors
and useless against thirteen cannot keep its peak — the thirteen drag the mean down.

Those 11 are brought back by the POWER LAW about the geometric mean, never a clamp. Beyond
the two reasons the profile fitter already used it (monotone, preserves the geometric
centre), there is a third that is specific to this step: **it preserves the derived-armor
relation exactly.** `G(P/G)^a x G(S/G)^a / G(peak/G)^a == G(H/G)^a` identically, so
`Heroic = Plate x Scout / peak` (§12.0b) survives without being recomputed. An affine
squeeze onto the window does not.

| | before | after |
|---|--:|--:|
| median spread across all 94 | 3.06x | **3.00x** |
| sharpest family | 7.33x (`Railgun_Heavy`) | 6.41x (`Melee_Light`) |
| `Melee_Medium` | 6.69x | **2.86x** |
| `Arrow_Medium` | 4.71x | **3.01x** |

⚠ **The cost is real and belongs to the maintainer, not to me.** Melee and Arrow lose about
half their skew; the other nine move by less than 1.0x. The field band (2/4/8) still holds
at the median. **If that skew should come back, the lever is the CEILING, not the
normaliser** — under mean-100 a peak of twice the average is arithmetic, not policy.

⚠ **Scope: MAIN warheads only.** The `_Percentage` twin encodes its magnitude IN its Versus
rows, so normalising it would multiply every %-effect by ~5x. Rebasing the twins is W18.

#### What S1 did to the Shield ladder — and the fix that outlives it

Exactly the drift §6b warned about: the three hand-calibrated constants
(`SHIELD_GEOMEAN` / `SHIELD_ALPHA` / `SHIELD_ANCHOR`) were correct for the pre-S1 profiles
and silently wrong the moment those moved — the ladder landed on **110..420 = 3.82x**
against its stated targets of 100..400 = 4.00x.

Worse, it inverted the anchor law. The structural term swings **1.198x** across the set
while `Tesla -> Storm` is only a **1.053x** rank gap, so `Storm_Super` (rank 0.95) overtook
`Tesla_Super` (1.00), 425.3 to 420.5 — and did the same at Heavy and Medium. §5b had
promised the structural term would "anchor the band without fighting the physics rank for
control of the ordering"; post-S1 that was measurably false.

Two changes, and both are structural rather than a re-calibration:

1. **The structural term is DAMPED** to the one job §5b actually left it — separating
   families whose physics rank is EQUAL (`CannonChem`/`MissileChem` both 0.50). The
   exponent is derived, not chosen: `ln(smallest distinct rank ratio) / ln(the term's own
   swing)`, i.e. exactly the largest damping under which the smallest genuine rank gap
   still wins. Both inputs are stable — `PHYSICS_RANK` is a design table, and the swing is
   bounded by the WINDOW, not by the current profiles.
2. **The compression moved into phase 2** (`shield_uniqueness.compress`), where the whole
   set is visible, and is DERIVED on every run. The three stale-able constants are retired.
   A calibration that cannot go stale beats a comment warning that it might.

**Result: 100..400 = exactly 4.000x, 94 of 94 distinct, Shield ascends within every family,
and Tesla is the top family at every level it exists** — `Tesla` 312 / 338 / 368 / 400 with
`Storm` just under at 301 / 326 / 355 / 385.

⚠ **Two templates float outside the pass** because the generator does not emit them:
`^Warhead_Nuclear_Super` (`HAND_TUNED`, Shield 155) and `^Warhead_Sniper_Light` (110).
Nuclear now collides with `CannonAP_Heavy` at 155 — and it resolves in S2, which retires
`HAND_TUNED` and brings Nuclear into the generator as a generalist. `Sniper_Light` is a
standing hazard: it can collide at any regeneration and nothing would catch it.

#### Also shipped: descending Versus order everywhere

Maintainer, 2026-08-16: *"the percentage versus values are not ordered by power like they
are for the normal variants ... enforce this rule so percentage values are also always
ordered by descending value (except for hazmat and shield which are always first)"*.

The main warhead already arrived sorted; the `_Percentage` twin and the `_ExtraDamage` chip
did not — they shipped in the ORDERING LAW's sequence (macro blocks INF, VEH, BLD, AIR),
which reads `9 10 11 13 · 7 9 10 12 13`, restarting at every block. The law decides which
armor gets which VALUE; it was never meant to decide the print order.

Sorting now happens inside `emit_versus`, so the invariant is unconditional for every node
the generator emits, whoever built the rows. The sort is STABLE, so ties keep the ordering
law's sequence. **All 201 `^Warhead_*` template Versus nodes are now descending.**

⚠ **524 non-descending Versus nodes remain outside the templates** — almost all on legacy
`Warhead@1Dam` / `2Dam` / `3Eff` weapons carrying their own inline `Versus`, which
DESIGN.md forbids outright (`Versus` lives only in `^Warhead_*`). They are not worth sorting:
the retired-naming purge and W23/W24 delete or convert them wholesale.

### 7. Open decisions

1. **Shield range** — `CEILING + floor` gives 210/225/240. Should Tesla reach ~400 as it
   did before the chips were merged? That sets the scale's top.
2. **Nuclear vs the Super-is-a-generalist law** (§3) — exception, or soften the law?
3. **Option A / B / C.**
4. **Does `Shield` stay a `Versus` row at all**, now that W21 made shields a real health
   LAYER? If damage-to-shields is better expressed on the layer, this whole ladder may be
   the wrong mechanism. Worth answering before S3 rather than after.

---

## Should platings MULTIPLY with the class armour, or REPLACE it?

_Merged 2026-08-23 from `docs/design/PLATING_COMBINATION.md`, unedited below this line._

**Maintainer 2026-08-17:** *"now that you have made it 70% on average I think we can go back to
multiplying the damage values with the underlying armor from the HP? Can you find good reasons for
and against it first before you do anything?"*

Nothing has been changed. This is the analysis, measured.

Under multiplication, `effective = class_row × plating_row / 100`. So **a plating helps iff its
row is below 100 and hurts iff it is above** — the class row cancels out of that test, which makes
the question exactly answerable rather than a matter of taste.

---

### The measurements

**1. Harm, per cell (155 cells: 31 families × 5 platings)**

| | cells that INCREASE damage | worst case |
|---|--:|--:|
| the old AVERAGING world | 98 of 1152 | **×1.84 (+84%)** |
| MULTIPLYING mean-70 rows | **5 of 155** | **×1.06 (+6%)** |

The 5: `Arrow` × HAZMAT 106, `Concussion` × COMPOSITE 106, `Prism` × BLAST 103, `Bullet` ×
HAZMAT 102, `Toxic` × REFLECTOR 102.

⚠ These figures are POST-`e7fa2d57b` (the per-family uniqueness pass) and they replace an
earlier "13 of 100 at ×1.07" measured while four groups of families still shared a row. Both the
count and the worst case improved, for a structural reason worth keeping: giving each family a
second mechanism in another group pulls its extremes toward the middle of every column.

⚠ **So "mean 70" does not mean "never hurts".** The mean is a COLUMN property (across families);
the harm test is per CELL. The maintainer's premise is right in aggregate and wrong in detail —
but the detail turns out to be small.

**2. Spread compounding — the objection that killed multiplication in W20**

```
class armor rows span    65.3 .. 114.7  =  1.76:1
plating rows span        35.0 .. 106.0  =  3.03:1
MULTIPLIED               22.9 .. 121.6  =  5.32:1
SELECTED (plating only)                 =  3.03:1
```

⭐ **5.32:1 sits INSIDE the documented 2–8× target band** (DESIGN §12.0 rule 5). W20's disaster
was `40% × 30% = 12%`, turning a 17:1 weapon into ~289:1 — but that was **two full ladders**
multiplied. A plating row is a SHALLOW modifier (35–107, mean 70), not a second ladder. **The
original objection does not apply to this case**, and that is the substantive change since W21.

---

### FOR multiplying

1. ⭐ **Selection ERASES the class armor, and that is a bigger loss than it sounds.** A plated
   Heroic unit stops being Heroic: only the plating row is read, so the unit-class ladder — the
   entire reason the armor system exists — is switched OFF by installing an upgrade. A Superheavy
   tank and a Scout car with the same plating take identical damage. Multiplication keeps both
   dimensions live.
2. **Harm is now ≤6% in 3% of matchups**, against +84% in the averaging world.
3. **The compounded spread lands in the target band** (5.32:1 vs the 2–8× design range).
4. **Both design axes stay simultaneously live** — the class ladder AND the plating cycle. Under
   selection they are mutually exclusive, so the cycle's rock-paper-scissors replaces the class
   ladder instead of layering on it.

### AGAINST multiplying

1. **5 cells still increase damage.** Real, but ≤6% — see the ruling below.
2. ⚠ **The two factors are CORRELATED, not independent, and multiplication assumes independence.**
   Both the class ladder and the plating row are projections of the **same** `COMPOSITION`: a
   thermal weapon is anti-infantry-sharp in its class ladder *and* countered by HAZMAT. Multiplying
   applies the weapon's identity **twice** to a plated unit. This is the strongest objection and it
   is conceptual rather than numeric — the numbers above stay in band, but they are in band for a
   reason that is partly luck.
3. **It reintroduces a multiply path.** Safe only while a unit can wear exactly ONE plating —
   `audit_plating_exclusivity` (X1) is what holds that, and it must stay green.
4. **The pricing model prices ROWS, not products.** `armor_exposure.py` and `K` read a weapon's
   Versus row; with multiplication a plated unit's effective armor is a product, so exposure needs
   to know about the plating distribution.

---

### Recommendation — multiply, and do NOT clamp

Multiplication, because argument 1 is decisive: an upgrade that deletes a unit's class identity is
a worse outcome than an upgrade that is 6% unhelpful against one damage axis.

**And deliberately no clamp at 100.** Clamping would remove the 5 harm cells — but those cells
*are the cycle's weaknesses*. The closed cycle (thermo → kinetic → blast → energy → thermo) is
built so each plating is strong against one axis and **weak against the next**; a clamp deletes
half of that design and turns every plating into a strict upgrade, which is exactly the "free
upgrade" the cycle exists to avoid. A +6% penalty against your counter-weapon is a trade a player
can read and plan around.

### ✅ SHIPPED 2026-08-17 — and it was NOT a one-field flip

Measured before the change: **`MultiArmorCombination` is set NOWHERE in yaml** (0 occurrences), so
every warhead ran the default `Average`, and under `Average` the Cameo override did
`if (plating.Count > 0) return plating.Min();` — **the class armor was discarded outright**. That
is layer SELECTION, confirmed in code rather than assumed.

⚠ **Setting the field to `Multiply` would NOT have implemented this ruling.** That value
short-circuits to the engine's `DamageWarhead.DamageVersus`, which takes the product of **every**
matched armor — including two CLASS armors, i.e. W20's squaring bug (40% × 30% = 12%) — and it
also bypasses the `plating.Min()` protection. So the ruling needed a code change, in
`AreaDamageWarhead.DamageVersus`:

```csharp
var classRow = armor.Count == 0 ? 100 : /* MultiArmorCombination over CLASS armors only */;
return plating.Count > 0 ? classRow * plating.Min() / 100 : classRow;
```

`MultiArmorCombination` now governs the **class** armors only (still `Average`, so the dual-armor
cyborgs are untouched) and the plating layer always multiplies on top — the two rules in one field
that this document called for. No clamp, deliberately.

⭐ **Cheap moment to land it:** only **7 plating grants** exist across the whole roster today, all
conditional, so the law is set before the platings roll out rather than after. Boot-gated with the
rebuilt assembly (menu 21:47:41, no new exception log).

⚠ **But do not read "7 grants" as "no gameplay change" — for those seven it is large, and it is
the whole point.** A HAZMAT-suited infantryman (class armor `None`) under `^Warhead_Flame_Light`,
which reads `None: 200 / HAZMAT: 40`:

| | vs light flamer | what it means |
|---|--:|---|
| SELECTION (before) | **40** | the suit ERASED the unit's flammability class — 5× tougher than an unsuited rifleman, and identically tough to a plated tank |
| MULTIPLY (after) | **80** | still 2.5× better than unprotected, but infantry stays infantry |

That is the argument in one cell: a hazmat suit should make you resist fire, not stop being a
soft target. The same unit is now also correctly *worse* off wearing HAZMAT against kinetic fire,
which is what the closed cycle is for.

**What must still be true:**
* `audit_plating_exclusivity` X1 stays green (one active plating, always) — it is what keeps
  `plating.Min()` from being load-bearing.
* `armor_exposure.py` learns the plating distribution before prices are set (E1).
* Re-measure the harm cells after any composition change — they moved from 13 to 5 the first time
  the compositions were touched, so this is a live coupling, not a one-off check.
* ⚠ The ~878 legacy warhead nodes still declaring inline `Versus` on `SpreadDamage` do **not**
  route through `AreaDamage` and therefore keep the engine's blanket multiply. The layer rule
  reaches a weapon only once it is on a `^Warhead_*` template (A5 / W24).

---

### Appendix — where the matrix lives, and why rows no longer tie

*"why do they both have the exact same values for composite and armor? shouldn't they be unique?"*

⚠ **This appendix used to hold a copy of the matrix and an argument that the ties were
unavoidable. Both are superseded.** The full 31-family × 5-plating matrix is maintained in
**`PLATING_COMPOSITION_REFINEMENT.md`** — one owner, so the two documents cannot drift — and as of
`e7fa2d57b` **every emitted family has a distinct row** (`tools/tests/test_plating_composition.py`
pins it; `doc_claims.yaml` re-measures the count every audit run).

What survives from the old argument, because it is still true and still governs any future edit:

* **Five axes, but only FOUR distinguishable groups.** `HAZMAT` counters `{thermo}`, `COMPOSITE`
  counters `{kinetic, shaped}`, `BLAST` counters `{blast}`, `REFLECTOR` counters `{energy}` — so
  `kinetic` and `shaped` are read as one SET and refining *within* a group is arithmetically
  INERT. `Bullet` 0.90/0.10 against `Arrow` 0.65/0.35 was measured as byte-identical.
* ⭐ **A row earns its difference only by moving mass ACROSS a group boundary**, and the honest way
  to do that is to name a SECOND real defeat mechanism (spall behind the plate, a pyrophoric
  penetrator, a deflagrating fuel, an arc's thunderclap). That is how the four tie groups were
  broken without inventing a number.
* ⛔ **Never break a tie with ±1 noise.** The rows are derived from physics; a fabricated
  difference is a lie about the model (`b182fd228` — *"blend ladders were FABRICATED, not
  measured"*).
* **`ARMOR` is 70 for every family BY DESIGN** and must stay flat — it is the generic hedge that
  *"receives 100% damage from everything"*. It is the one column where a tie is the specification.
* **The no-ties ladder law (DESIGN §12.0 rule 2) governs values WITHIN one weapon's profile**, not
  a column across weapons. Those are different claims and only the first is a law.

---

## Making each weapon family's plating row unique

_Merged 2026-08-23 from `docs/design/PLATING_COMPOSITION_REFINEMENT.md`, unedited below this line._

**Maintainer 2026-08-17:** *"maybe more reasoning to make each one a finer rating against each
armor type? like you said sword, arrow and rifle might impact the armors slightly differently even
though they are in the same kinetic family right? But you need to use your best real world
reasoning for this to get it right!"* … *"I want all weapon families to be a bit more unique so
don't put 3 energy weapons exactly on the same versus value but slightly different"*

**STATUS: DONE** — shipped in `e7fa2d57b`. **48 emitted families** (`plating_families`, re-measured 2026-09-05). ⚠ The matrix below still lists 37 rows — the families added since (the Cryo cells among them) have no row yet; `audit_doc_claims` holds this red until the table is regenerated. Four groups
of ties are gone: `Laser/Prism/Tesla`, `Chemical/Cryo/Flame/Toxic`, `Concussion/Demolition`, and
`Arrow/Bullet/CannonAP/Melee`. Pinned by `tools/tests/test_plating_composition.py`.

---

### ⚠ FIRST: the kinetic/shaped split is INVISIBLE to every plating

The obvious approach — refine a sword against an arrow against a bullet *within* the kinetic
family — **does nothing at all**. Measured before anything was applied:

| family | proposed composition | HAZMAT | COMPOSITE | BLAST | REFLECTOR |
|---|---|--:|--:|--:|--:|
| Bullet | kinetic 0.90, shaped 0.10 | 150 | 50 | 100 | 100 |
| Arrow | kinetic 0.65, shaped 0.35 | 150 | 50 | 100 | 100 |
| CannonAP | kinetic 0.75, shaped 0.25 | 150 | 50 | 100 | 100 |

**Byte-identical.** The reason is in the cycle itself:

```
HAZMAT      counters {thermo}            weak {kinetic, shaped}
COMPOSITE   counters {kinetic, shaped}   weak {blast}
BLAST       counters {blast}             weak {energy}
REFLECTOR   counters {energy}            weak {thermo}
```

`kinetic` and `shaped` **always appear together as a set**, so `sum(kinetic, shaped)` is all the
formula ever sees. **Five axes, but only FOUR distinguishable groups:** `{thermo}`,
`{kinetic + shaped}`, `{blast}`, `{energy}`.

⭐ **So a row can only earn its difference by moving mass ACROSS a group boundary.** Within-group
refinement is arithmetically inert. That is also why the original ties were a structural limit
rather than an oversight — and why the fix is *not* finer shares but a **second defeat mechanism**
for each family, in a different group. Four groups still give a continuum, so 32 unique rows are
reachable; what is unreachable is 32 unique rows built out of kinetic-vs-shaped hair-splitting.

⛔ **What must NOT be done is adding ±1 noise to break a tie.** The rows are derived from physics;
a fabricated difference is a lie about the model, and this project has already been burned by
exactly that (`b182fd228` — *"blend ladders were FABRICATED, not measured"*).

---

### The secondary shares, one family at a time

#### Kinetic cluster — what happens BEHIND the plate

A solid projectile's only honest non-kinetic share is its **spall**: a penetration event throws
fragments, and a spall liner (`BLAST`) is the real-world answer to it — that is what spall liners
are *for*. So the share tracks how violent the event is.

| family | share | why |
|---|---|---|
| `Arrow` | kinetic 1.00 | the pure point: a slow sharp penetrator, no spall and no flash |
| `Sniper` | blast 0.05 | one round, one channel, very little behind-plate debris |
| `Bullet` | blast 0.10 | deforms, cavitates, sprays spall |
| `Melee` | blast 0.25 | ⭐ blunt trauma is **shock through** rigid armour, i.e. overpressure — a mace beats plate where a sword does not, and *not* by penetrating |
| `CannonAP` | thermo 0.15 | a DU dart is **pyrophoric**; the documented behind-armour effect is incendiary as much as mechanical |
| `Railgun` | energy 0.15 | unchanged — the EM launch and plasma sheath (this is why Railgun was never tied) |
| `MissileAP` | thermo 0.05 | behind-armour incendiary from the jet |

`Melee` now reads correctly in both directions: a composite plate helps *less* against a mace
than against a rifle (53 vs 42), and padding helps *more* (62 vs 68).

#### Blast cluster

`Concussion` keeps `blast 1.00` as the pure overpressure archetype. `Demolition` takes
`thermo 0.15` for the detonation flash a contact charge delivers — which is what incendiary
cutting charges exploit. A sealed suit now gives a little protection against one (65) and none
against the other (70).

#### Thermochemical cluster

A sealed insulated suit really is the right counter to all four, so they keep a thermo **lead**
and separate on their second mechanism:

* `Toxic` **1.00 thermo** — an agent attacking the **crew** is exactly what a hazmat suit is for,
  so this is the pure case. It is also the only family a REFLECTOR still makes *worse* (102):
  the purest agent is the one that fouls a mirror.
* `Flame` **blast 0.15** — fuel **deflagrates**: a pressure pulse and oxygen depletion.
* `Chemical` **shaped 0.25** — corrosion (per `PHYSICAL_STATE_SYSTEM.md`, *not* gas) eats a
  channel through the material, i.e. localised material removal. **Ceramics are chemically
  inert** where steel and reactive armour are not, so `COMPOSITE` earns a partial answer (62).
* `Cryo` **energy 0.55, thermo 0.25, kinetic 0.20** — Laser×Prism coldray. The shield table
  sees mostly coherent energy field-coupling (rank 0.75); the thermal load is still real
  (insulation stops it), and the small kinetic share is cryogenic **embrittlement**: what breaks
  is frozen material fracturing.

#### Energy cluster — how much of the delivered damage is THERMAL

That share is also the order in which a mirrored coating stops being the right idea:

| family | composition | REFLECTOR | why |
|---|---|--:|---|
| `Prism` | energy 0.90, thermo 0.10 | 41 | focused visible light: the purest radiant beam, and a mirror is its exact counter |
| `Tesla` | energy 0.75, thermo 0.20, blast 0.05 | 49 | a conducted arc; the thermal part is resistive heating and the blast part is the **thunderclap** — thunder is literally an overpressure wave |
| `Laser` | energy 0.65, thermo 0.35 | 58 | coherent IR, but the **kill** is ablation |

---

### ⚠ Two of my own claims were wrong, and are corrected here

**1. "A mirror does not stop lightning."** I argued REFLECTOR should barely help Tesla
(`energy 0.60 / thermo 0.40`), because reflection defeats *radiant* energy while an arc needs a
Faraday cage. **Overruled** — maintainer: *"the tesla is the opposite [of Inferno]: it's mostly
energy and a bit of thermal"* — and the ruling is defensible on physics I had missed: a mirrored
plating is a **metal skin**, i.e. a conductor, which spreads and grounds an arc. Same benefit,
different mechanism. `PHYSICS_RANK` also already called Tesla the field-coupling champion at 1.00,
so "mostly energy" is what the other table had been saying all along.

**2. "Energy must EXCEED thermo or a 50/50 blend cancels."** True of the **raw** row, false of the
**shipped** one. Every column is pinned to `PLATING_TARGET_MEAN`, so at mean 70 a value only stops
being a benefit above ~143 raw. A thermo-LED heat ray still gets a real reflector benefit:

```
Inferno  thermo 0.65 / energy 0.35  ->  HAZMAT 47   REFLECTOR 79
```

Both reduce it, HAZMAT far more — which is exactly the earlier request (*"reduced by both hazmat
and reflector armor then? But maybe more by hazmat"*). **The mean-70 ruling is what made the
maintainer's "mostly thermal" reading available**; under the old mean of 100 a 50/50 really did
land on ~97, i.e. nothing.

---

### The anti-drift guard: `_rank_blend` is retired

`_rank_blend` derived Inferno's thermo/energy split from `PHYSICS_RANK` arithmetically. That
**over-reached**: the two tables answer different questions — rank asks how much of a discharge a
**force field** absorbs, composition asks what reaches **matter** — and `Railgun` has always been
the standing proof that they are not one axis (rank 0.78, a nearly pure kinetic slug). Deriving
one from the other therefore had to be overruled the moment a ruling touched either table, which
is precisely what happened.

`rank_composition_conflicts()` keeps only what the two tables genuinely share, and constrains no
share:

> a family the shield table calls **field-coupling** (`PHYSICS_RANK >= 0.56`, the table's own band
> boundary) must have **some** energy share; one it calls thermal/kinetic must have **none**.

That catches exactly the drift that shipped twice (`Inferno` 0.57 (Flame×Prism) and `Cryo` 0.75 (Laser×Prism), with explicit thermo/energy/kinetic shares) without pretending to know the exact split.

---

### The shipped matrix

45 families emitted; the table below still lists 37 rows (ARMOR excluded — it is flat by definition).

| family | HAZMAT | COMPOSITE | BLAST | REFLECTOR | ARMOR | composition |
|---|--:|--:|--:|--:|--:|---|
| Arrow | 104 | 35 | 71 | 69 | 70 | kinetic 1.00 |
| Bullet | 101 | 42 | 68 | 69 | 70 | kinetic 0.90, blast 0.10 |
| Railgun | 99 | 41 | 77 | 63 | 70 | kinetic 0.85, energy 0.15 |
| MissileAP | 97 | 44 | 68 | 70 | 70 | shaped 0.85, blast 0.10, thermo 0.05 |
| Melee | 96 | 53 | 62 | 69 | 70 | kinetic 0.75, blast 0.25 |
| CannonAP | 94 | 41 | 71 | 74 | 70 | kinetic 0.70, thermo 0.15, shaped 0.15 |
| Flak | 90 | 63 | 57 | 69 | 70 | kinetic 0.60, blast 0.40 |
| MissileAA | 89 | 67 | 55 | 69 | 70 | kinetic 0.55, blast 0.45 |
| MissileHE | 78 | 88 | 45 | 69 | 70 | blast 0.75, shaped 0.25 |
| PhotonCannon | 78 | 74 | 58 | 70 | 70 | blast 0.46, kinetic 0.34, thermo 0.11, energy 0.08, shaped 0.01 |
| MissileChem | 75 | 53 | 70 | 82 | 70 | shaped 0.55, thermo 0.40, blast 0.05 |
| CannonHE | 73 | 99 | 39 | 69 | 70 | blast 0.90, kinetic 0.10 |
| Quantum | 73 | 61 | 89 | 57 | 70 | energy 0.52, kinetic 0.28, thermo 0.18, blast 0.02 |
| CannonChem | 73 | 51 | 71 | 84 | 70 | thermo 0.45, kinetic 0.35, shaped 0.20 |
| Concussion | 70 | 106 | 36 | 69 | 70 | blast 1.00 |
| Sonic | 70 | 95 | 57 | 58 | 70 | blast 0.70, energy 0.30 |
| Cryo | 68 | 63 | 91 | 58 | 70 | energy 0.55, thermo 0.25, kinetic 0.20 |
| Storm | 66 | 74 | 96 | 45 | 70 | energy 0.80, thermo 0.10, blast 0.10 |
| Prism | 66 | 70 | 103 | 41 | 70 | energy 0.90, thermo 0.10 |
| Demolition | 64 | 100 | 41 | 74 | 70 | blast 0.85, thermo 0.15 |
| Magic | 63 | 78 | 86 | 55 | 70 | energy 0.60, thermo 0.20, blast 0.20 |
| Tesla | 63 | 72 | 96 | 50 | 70 | energy 0.75, thermo 0.20, blast 0.05 |
| Waveforce | 62 | 64 | 81 | 73 | 70 | thermo 0.43, energy 0.31, kinetic 0.17, shaped 0.05, blast 0.04 |
| MissileFire | 59 | 82 | 55 | 83 | 70 | blast 0.45, thermo 0.42, shaped 0.12 |
| CannonFire | 57 | 87 | 53 | 83 | 70 | blast 0.53, thermo 0.42, kinetic 0.05 |
| Laser | 57 | 70 | 95 | 58 | 70 | energy 0.65, thermo 0.35 |
| Thermobaric | 56 | 92 | 50 | 82 | 70 | blast 0.60, thermo 0.40 |
| Chemical | 52 | 62 | 71 | 94 | 70 | thermo 0.75, shaped 0.25 |
| Plasma | 50 | 70 | 87 | 72 | 70 | thermo 0.55, energy 0.45 |
| Inferno | 47 | 70 | 84 | 79 | 70 | thermo 0.65, energy 0.35 |
| Flame | 40 | 76 | 66 | 98 | 70 | thermo 0.85, blast 0.15 |
| Toxic | 35 | 70 | 71 | 103 | 70 | thermo 1.00 |

| CannonNuke | 62 | 91 | 51 | 75 | 70 | blast 0.65, thermo 0.25, kinetic 0.05, energy 0.05 |
| MissileNuke | 74 | 64 | 65 | 76 | 70 | shaped 0.43, thermo 0.28, blast 0.25, energy 0.05 |
| MissileQuantum | 85 | 52 | 79 | 64 | 70 | shaped 0.43, energy 0.26, kinetic 0.14, thermo 0.12, blast 0.06 |
| MissileTesla | 79 | 58 | 83 | 60 | 70 | shaped 0.43, energy 0.38, thermo 0.13, blast 0.08 |
| MissileThermobaric | 68 | 91 | 47 | 74 | 70 | blast 0.71, thermo 0.17, shaped 0.13 |
| BulletFire | 69 | 59 | 68 | 83 | 70 | kinetic 0.45, thermo 0.42, blast 0.12 |
| BulletHE | 81 | 72 | 55 | 71 | 70 | blast 0.47, kinetic 0.45, thermo 0.07 |
| BulletThermobaric | 78 | 69 | 59 | 74 | 70 | kinetic 0.45, blast 0.38, thermo 0.17 |
| BulletTesla | 80 | 58 | 83 | 59 | 70 | kinetic 0.45, energy 0.38, thermo 0.10, blast 0.08 |

**`ARMOR` is 70 for every family BY DESIGN** — it is the generic hedge that *"receives 100% damage
from everything"*, so it must be flat. Varying it would contradict its purpose, and
`test_the_generic_plating_stays_flat` pins that.

#### "evenly distributed among all the axis" — measured

| | axis share | group share (what the cycle READS) |
|---|---|---|
| before | thermo 25.8, energy 25.0, blast 22.9, kinetic 19.7, shaped 6.7 | 1.15× spread |
| **after** | thermo 27.4, blast 24.9, energy 21.4, kinetic 18.6, shaped 7.7 | **1.28× spread** |

Groups after: `thermo 27.4%`, `kinetic+shaped 26.4%`, `blast 24.9%`, `energy 21.4%`.

⚠ **Honest trade:** group evenness got slightly *worse* (1.15× → 1.28×), because the energy
families gave mass to thermo. Each plating still faces a quarter of the roster ±3 points, which is
well inside "even" — the ties were the bigger problem and this is what buying uniqueness cost.
The raw `shaped` figure stays low (7.7%) and always will: only `MissileAP` is shaped-led, and the
cycle folds shaped into `COMPOSITE` anyway, which is how a real tank is built.

#### Under multiplication

**6 cells of 185 increase damage, worst ×1.06** (was 13 of 100 at ×1.07 — better on both counts):
`Arrow`/`Concussion` 106, `Prism` 103, `Bullet`/`Toxic` 102. Rows span 3.03:1; multiplied by the
class ladder that is **5.32:1**, inside the documented 2–8× band (DESIGN §12.0 rule 5).

---

### Still open: if EVERY CELL must be unique, re-cut the cycle

Full-row uniqueness is done. Individual **cells** still coincide (`REFLECTOR` has 23 distinct
values across 37 families), and the honest route to more is not finer shares but **cutting the
cycle differently**, because `COMPOSITE` currently merges two platings that behave oppositely in
reality:

> **Explosive reactive armour defeats shaped charges specifically** — it disrupts the jet before it
> forms — **and does very little against a long-rod kinetic penetrator.** Spaced armour is the same
> story. Composite/ceramic armour is the reverse: excellent against kinetic rods, less so against a
> focused jet.

Splitting that counter would separate `Bullet` (kinetic) from `MissileAP` (shaped 0.85) from
`CannonAP` (0.70/0.15) **with no invented numbers** — the shares already exist and would simply
become visible. ⚠ Cost: a **sixth plating**, and the closed cycle has to be re-cut so every
plating still has exactly one counter-axis and one weakness. That needs its own ruling.

---

### Separately — the hybrid-armor confirmation needs one clarification

*"the hybrid armors like heroic = plate x scout and the jumpjet = fighter x scout and the cabal
infantry x vehicle armors should be averaged while the armor layer on top should be multiplied
right?"*

Agreed on the outcome, but these are **two different mechanisms** and only one of them is
`MultiArmorCombination`:

| | mechanism | where it happens | rule |
|---|---|---|---|
| `Heroic = Plate × Scout / peak`, `Airborne = Helicopter × Scout / peak` | a **DERIVED Versus COLUMN**, computed once per warhead by the generator | `gen_weapon_template`, DESIGN §12.0b | already a product; `MultiArmorCombination` never sees it |
| CABAL cyborgs / droids carrying **two Armor traits** | runtime multi-armor | `AreaDamageWarhead.MultiArmorCombination` | **Average** — keep |
| a **plating** over the class armor | runtime, one plating at a time | same field | **Multiply** — the change |

So: **Heroic and Airborne are not affected by this decision at all** — they are columns, not
runtime combinations. The dual-armor CABAL units stay on `Average` (multiplying two full ladders is
W20's squaring bug, 40% × 30% = 12%). Platings multiply. That does give each mechanic its own
behaviour, as intended — it just needs implementing as *two* rules in one field, which is why the
plating set is checked by name in `DamageVersus`.

---

## Superweapons vs the layered stack — why "75%" is not 75%

_Merged 2026-08-23 from `docs/design/SUPERWEAPON_LAYER_DAMAGE.md`, unedited below this line._

**Maintainer 2026-08-17:** *"we need to make sure that any super weapon deals the same total
damage to shielded and unshielded buildings. That is the AtomicCore. It is supposed to destroy
75% of the target HP but with shields that is more complex ... Instead the Versus Values of the
Atomic Core which uses the Nuclear Warhead must be adjusted so the total damage it deals to
shields and then down to HP is the same, right? Do you know how to do that?"*

Short answer: **yes — but not with Versus values.** Versus can fix one weapon against one
building at one HP, and it breaks the moment any of those three change. There is a mechanism
that is invariant to all of them, and it is a small mod-side change. The algebra below is why.

---

### 1. What AtomicCore does today

`^Warhead_Nuclear_Super` (`mods/cameo/weapons/weapons.yaml:9243`) carries TWO damage warheads:

| component | value | scales with |
|---|---|---|
| `Warhead@Nuclear_Super: AreaDamage` | weapon sets `Damage: 500000` | nothing — a FLAT number |
| `AreaDamagePercentage` twin | `Damage: 25` = 25% of max health | the target's max HP |

Relevant Versus rows: `Concrete: 100`, `Shield: 155`.

The comment in the file states the intent: *"AtomicCore = 500000 flat + 25% → 500k + 250k =
750k (75%) on a 1,000,000-HP Concrete construction yard."*

#### ⚠ Bug 1 — "75%" is true at exactly ONE building size, and shields have nothing to do with it

A flat term plus a percentage term is only a fixed percentage at one HP value:

| target max HP | flat | 25% | total | fraction destroyed |
|--:|--:|--:|--:|--:|
| 200 000 | 500 000 | 50 000 | 550 000 | **275% — guaranteed kill** |
| 1 000 000 | 500 000 | 250 000 | 750 000 | 75% ✅ the design point |
| 2 000 000 | 500 000 | 500 000 | 1 000 000 | **50%** |

So the "destroys 75%" contract already fails on every building that is not exactly 1M HP. **A
percentage contract can only be met by a pure percentage.**

#### ⚠ Bug 2 — against a converted shielded building it does not even reach the health bar

Take the §W26 conversion (half HP, 200% shield of the halved HP), so health = 500 000 and the
shield pool = 1 000 000:

```
flat : 500 000 x (Shield 155/100)              = 775 000
pct  : 500 000 x 25/100 x (Shield 155/100)     = 193 750      <- % is of max HEALTH (500k), not the pool
total                                          = 968 750   applied to a 1 000 000 pool
```

The shield **survives with 31 250 left. Health is untouched — the structure is at 100%.**

In raw-damage currency (what the attacker must spend):

| | raw durability | nuke spends | destroyed |
|---|--:|--:|--:|
| unshielded 1M Concrete | 1 000 000 | 750 000 | **75%** |
| converted shielded | 1 145 161 | 625 000 | **54.6%** |

---

### 2. Why adjusting Versus CANNOT solve this in general

For the 50%-HP/200%-shield conversion to be **durability-neutral** against a given weapon, that
weapon needs

```
Versus[Shield] = 2 x Versus[the building's armor row]
```

*Derivation.* Raw damage to kill an unshielded building is `H x 100/V_c`. After conversion it is
`(H/2) x 100/V_c` for the health plus `H x 100/V_s` for the pool. Setting them equal gives
`0.5/V_c + 1/V_s = 1/V_c`, i.e. `V_s = 2 V_c`.

⭐ This is the same fact as the **189.1% break-even pool** (`100 / shield_hp_factor`): both say
that converting HP into an equal-value shield means undoing exactly the Shield row's average
penalty. AtomicCore has `Shield 155` against `Concrete 100`, i.e. 1.55x where neutrality needs
2.0x — which is precisely why the converted building came out *tougher*.

**And this is why Versus is the wrong tool:** neutrality would have to hold for **every**
weapon, which forces the entire `Shield` column to be exactly 2x the building columns. That
column is the mod's anti-shield rock-paper-scissors axis (Tesla 369, Melee ~76, DESIGN §12.0c).
Pinning it to 2x the building rows **destroys the axis**. Fixing AtomicCore alone with a Versus
tweak is possible (`V_s = 2 x V_c = 200`) but it is a hard-coded coincidence: it silently breaks
if the 50/200 split changes, if the building's armor row is Steel or Wood rather than Concrete,
or if the 75% target moves.

---

### 3. The mechanism that IS invariant — apply the percentage PER LAYER

**The contract "remove 75% of the target" should be read as "remove 75% of every layer".**

```
unshielded : 75% of health                       = 75% of durability ✅
shielded   : 75% of shield  +  75% of health     = 75% of durability ✅   (any split ratio)
```

This is invariant to **the HP scale, the shield/health split, the Versus rows, and any future
layer** (plating, Integrity). It needs no Versus coordination at all, which is exactly what
makes it maintainable.

#### What changes

`OpenRA.Mods.Cameo/Warheads/AreaDamagePercentageWarhead.cs` currently computes

```csharp
var damage = Util.ApplyPercentageModifiers(healthInfo.HP,
    args.DamageModifiers.Append(Damage, DamageVersus(victim, shape, args)));
```

`healthInfo.HP` is the **health layer's** maximum, so on a shielded target the percentage is
taken against half the durability and then spent on the wrong bar. Two additions:

1. **`PerLayer: true`** — resolve the percentage against each layer's OWN maximum (shield pool
   max, then health max) and apply to each, instead of one number cascading.
2. **`IgnoreVersus: true`** — for a superweapon the percentage is a contract, not a damage
   type. A nuke removing "75% of what you are" should not care that the outer layer happens to
   be a shield. (Keep Versus on the FLAT component, where armor type belongs.)

Both are mod-side; `engine/` is untouched.

#### AtomicCore afterwards

```
Warhead@Nuclear_Super_Percentage: AreaDamagePercentage
    Damage: 75            # 75% of EVERY layer
    PerLayer: true
    IgnoreVersus: true
```

and the flat 500 000 either goes away or shrinks to a splash value for units — its only current
job is to make the percentage come out right on one specific building, which the percentage now
does by itself.

⚠ **Ordering:** this must land before superweapons are priced. It changes what AtomicCore does
to 1016 buildings.

---

### 3a. The maintainer's follow-up: `Versus[Shield] = 200` + spread over ticks

*"those rules should not change anymore. 75% is a good value. So if the value for versus shields
is 200% it would even out nicely? Remember this needs to be applied over several ticks ... This
prevents the higher damage to shields being propagated to the HP bar if it's only one extremely
powerful hit."*

**The tick half is exactly right, and it is load-bearing.** With ONE big hit, damage computed at
`Shield 200` that overflows the pool cascades its excess into health *carrying the shield's 2×
multiplier* — health would take double the damage it should. Ticks re-resolve which layer is
active on every application, so post-shield ticks use `Concrete 100`. AtomicCore already carries
`Ticks: 10`, so the machinery is in place. **Any layer-crossing weapon needs this**; a
single-shot version is wrong by construction.

**`Shield: 200` also gives exactly the durability neutrality it should** — that is the
`V_s = 2 × V_c` condition from §2.

⚠ **But it does NOT restore the 75% contract, and this is worth seeing in full.** Take the
converted building (health 500 000, pool 1 000 000) with `Shield 200`, `Concrete 100`:

```
nominal per shot = flat 500 000  +  25% of max HEALTH (500 000) = 125 000   ->  625 000
over 10 ticks    = 62 500 nominal per tick

ticks 1-8  shield up, x2.00  -> 125 000 actual/tick  -> pool 1 000 000 exactly gone
ticks 9-10 health,   x1.00   ->  62 500 actual/tick  -> 125 000 onto health
```

| | raw durability | raw destroyed | fraction |
|---|--:|--:|--:|
| unshielded 1M Concrete | 1 000 000 | 750 000 | **75%** ✅ |
| converted, `Shield: 200` | 1 000 000 ✅ neutral | 625 000 | **62.5%** ❌ |

Durability is now neutral (1 000 000 both sides — the fix worked), yet the nuke destroys 62.5%
instead of 75%, and the building ends at **75% health** where the unshielded one ends at 25%.

**The missing 12.5 points is the percentage term's BASE.** `AreaDamagePercentage` takes its
percentage of `healthInfo.HP`, and halving the building's health halved that term from 250 000 to
125 000. No Versus value can restore it, because Versus multiplies what the percentage produced —
it cannot un-halve the base. Two checks confirm the base is the culprit rather than the flat/pct
mix:

* **pure 75% percentage, `maxHealth` base:** 375 000 nominal × 2.00 = 750 000 on a 1 000 000
  pool → 75% of the shield only, health untouched → **37.5%** of durability. Worse.
* **per-layer 75%:** 0.75 × 500 000 (shield, in raw) + 0.75 × 500 000 (health) = 750 000 →
  **75%** ✅, and it lands there for *any* `V_s`, any split, any building size.

**So: adopt both of the maintainer's points AND the per-layer base.** `Shield: 200` for
neutrality, `Ticks` for correct layer crossing, `PerLayer` for the 75% contract. They are three
different problems and each needs its own fix.

### 4. Open question for the maintainer

Per-layer 75% on a shielded building destroys 75% of the shield **and** 75% of the health, so
the building survives at 25% with a 25% shield. The old behaviour (*"kills the shield first
before applying damage to the HP"*) left the structure at 25% health with **no** shield. Both
destroy 75% of durability; they differ in what is left standing:

* **per-layer** (recommended) — proportional, keeps the shield's identity, trivially invariant;
* **strip-then-cascade** — more dramatic, matches the old feel, but the amount that reaches
  health depends on the Versus rows again, which is the coupling this document exists to remove.
