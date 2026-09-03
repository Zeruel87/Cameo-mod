# Design decision records

Small, settled decisions that each had their own file until 2026-08-23. Each section records
WHAT was decided and WHY, so the reasoning survives when someone later asks "why is it like
this?".

A decision that becomes a general rule belongs in [`../DESIGN.md`](../DESIGN.md) instead —
these are the ones scoped to one system.

---

## Recolorable hex-shield visuals

_Merged 2026-08-23 from `docs/design/HEX_SHIELD_VISUALS.md`, unedited below this line._

### Decisions

Shield mechanics remain authoritative. Visual changes must not alter shield conditions,
upgrade prerequisites, aura behavior, or hit-state switching.

The retained visual decisions are:

- upright oval for infantry;
- sphere for ordinary vehicles, aircraft, naval units, and large mobile classes;
- camera-correct dome for buildings and defenses;
- directional oval as an explicit geometry opt-in for elongated aircraft;
- fixed faction colors: default/Protoss blue, Ixian silver, Yuri indigo, Consortium cyan;
- Indexed8 art with transparent index 0 and 25% idle / 75% hit palettes.

Actor-specific shield sizing is forbidden. Concrete actors must not define `Sequence` or
`StartSequence` on the shield overlays. A concrete actor may override only `Image` when it
needs a different geometry, such as the directional oval.

### Class and footprint sizing

Mobile sequences are sized from class medians and normal cell occupancy:

| Class | Sequence | Scale |
| --- | --- | ---: |
| Infantry | `infantry-standard` | 1.10 |
| Vehicle and unclassified mobile | `vehicle-standard` | 1.00 |
| Aircraft | `aircraft-standard` | 1.15 |
| Naval | `naval-standard` | 1.30 |
| Dreadnought-scale mobile | `large-mobile-standard` | 1.50 |
| Directional aircraft geometry | `aircraft-standard` | 0.60 |

These are class standards, not promises to cover every sprite pixel. Large or unusually offset
art remains visually exceptional, but it must be addressed through an existing semantic class
template rather than by naming or sizing the individual actor.

### Why the previous sizing was rejected

The previous values optimized for containment: infantry 1.70, ordinary spheres 1.55,
naval/large spheres 2.30, defenses 0.80, and buildings 1.15. Across the prior 1,592-actor
measurement set, the median shield was 1.65 times the padded fitted target; 1,022 actors were
over 1.5 times their fitted target and 458 were over twice their fitted target. In-game review
confirmed this as widespread visual oversizing.

Class and footprint values reduce the overall median ratio to 1.00. The static report still
flags 146 actors above 1.5 times and 278 below 0.75 times the old padded target. Those tails are
an accepted limitation of general sizing, not a queue for actor-by-actor fixes.

### Buildings and selection boxes

Each existing `^NxMShape` selects a matching `dome-NxM` sequence. For the rectangular Cameo
grid, the selection footprint projects to approximately `48N x 48M` screen pixels. Sequence
scale is calculated with one shared 8-pixel padding on every edge:

```text
scale = max((48N + 16) / 261, (48M + 16) / 222)
```

The master dome's visible center is `(-0.5, 1)`, so every footprint sequence uses the derived
centering offset `(0.5, -1)`. Orientation remains significant: 2x3 and 3x2 are separate.

`^NxMShape` inherits one complete, condition-gated overlay pair without palette fields.
Shield-capable buildings merge their fixed faction palette from `^ShieldedShieldable`; 261
non-shield building actors carry the same pair dormant because they never satisfy `shielded`.
This is two disabled animations per live non-shield building, instead of the much larger cost
of defining every footprint alternative on every shielded building.

High-count walls and bridges opt out at their shared semantic templates. Bridges also lack
`RenderSprites`, which makes the opt-out required for trait validity rather than only performance.

The routing audit currently records 22 actors whose final `Selectable.Bounds` was overridden
to a different standard rectangle after their inherited shape. Their `^NxMShape` remains the
authoritative general class; these are warnings, not actor-specific sizing work.

### Performance and maintenance

All actors reuse four Indexed8 PNG atlases and render at most one idle-or-hit overlay. There is no
runtime bounds scan, dynamic scaling, generated actor table, or actor-name lookup. Directional
facings remain authored rather than interpolated.

When adding an actor, inherit its normal unit/building class and do not add shield sizing YAML.
If a whole semantic class is consistently wrong, adjust that shared class or introduce a
reusable class template only after representative in-game review.

---

## Splitting the vehicle production queue

_Merged 2026-08-23 from `docs/design/VEHICLE_QUEUE_SPLIT.md`, unedited below this line._

_Research note, 2026-08-22. Maintainer + TheCommando315, Discord: "light factory only for light,
normal factory for light and big, super factory for light, big and super" — and
"only don't make it confusing"._

**Verdict: this is a pure yaml change. No C# and no engine change.** Every mechanism it needs
already exists and is already used elsewhere in the tree. The cost is not difficulty, it is
BREADTH — 1193 `Queue: Vehicle` tags (plus 1160 `RAVehicle`) have to be re-sorted into three
buckets, and the classification for most of them does not exist yet.

---

### 1. Why a super tank currently walks out of a normal war factory

TheCommando315: *"the exits aren't well programmed in cameo — if you have multiple queues you can
exit a giant tank from any factory."* That is not a Cameo bug, it is what the engine is told to do:

```csharp
ProductionQueue.cs:920   if (!local.IsTraitDisabled && local.Info.Produces.Contains(type))
ProductionQueue.cs:926   pair.Trait.Info.Produces.Contains(type))
```

When an item finishes, the queue asks every building the player owns *"does your `Production`
trait's `Produces:` list contain my `Type`?"* and the first match becomes the exit. **Today every
vehicle-producing building declares `Produces: Vehicle`**, so every one of them is a legal exit for
every vehicle. The MonsterTank is not escaping through the wrong door — it is using a door we told
it was correct.

The fix follows directly: **make the `Produces:` sets disjoint** and the exits become disjoint too,
with no code involved.

---

### 2. The four moving parts

| part | where | what it decides |
|---|---|---|
| `ProductionQueue.Type` | player/factory rules | the queue's identity |
| `Production.Produces` | each factory | **which BUILDINGS can serve as an exit** |
| `Buildable.Queue` | each unit | which queue(s) the unit appears in |
| `Exit.ProductionTypes` | each door | **which DOOR on that building the unit uses** |

The last row is the answer to the garage-door question. `Exit` is per-door and already filters by
production type (`defaults.yaml:8057` — the Soviet barracks routes `Infantry, RAInfantry` and
`ra1_soviets_attackdog` through specific cells). So a super factory can carry one wide exit for the
epic units and normal exits for everything else:

```yaml
	Exit@BIGDOOR:
		SpawnOffset: 0,1400,0
		ExitCell: 0,3
		ProductionTypes: SuperVehicle
		Priority: 3
	Exit@NORMAL:
		ExitCell: 0,1
		ProductionTypes: LightVehicle, Vehicle
		Priority: 2
```

---

### 3. Recommended shape — three queues, ONE sidebar button

`ProductionQueueInfo` has both `Type` and `Group`, and they do different jobs:

```
Type   = the queue identity (what Produces: matches)
Group  = "Group queues from separate buildings together into the same tab"
```

`ProductionTabsCAWidget.cs:120` builds one top-level sidebar BUTTON per distinct `Group`, and
`:191` gives each QUEUE inside that group its own tab — shown only when it has buildable items
(`Queue.BuildableItems().Any() || Queue.AlwaysVisible`).

So setting all three queues to **`Group: Vehicle`** gives:

- **one** Vehicle button in the sidebar — no new group icon art needed, since the chrome image is
  looked up from the group name (`ProductionTabsLogicCA.cs:43`, `group.ToLowerInvariant()`);
- **three** tabs inside it: Light / Vehicle / Super;
- the Super tab **disappears entirely** when the player owns no super factory, and the Light tab
  likewise. Nothing empty is ever shown.

That is the "don't make it confusing" answer: the player still clicks one Vehicle button, and the
extra tabs only appear when they are earned.

⚠ Three distinct `Group`s instead would mean three sidebar buttons **and three new chrome icons**,
one per group name. Not recommended.

#### The containment ladder

The maintainer's rule maps onto `Produces:` with no special-casing:

| factory | `Production.Produces` |
|---|---|
| light factory | `LightVehicle` |
| war factory | `LightVehicle, Vehicle` |
| super factory | `LightVehicle, Vehicle, SuperVehicle` |

Each unit stays in **exactly one** queue (`Buildable.Queue: LightVehicle`), and the factory decides
what it can serve. A light vehicle therefore rolls out of any of the three; a super unit only ever
out of the super factory.

---

### 4. Everything doubles — the classic/RA parallel system

Cameo runs **two** queue systems side by side, switched by the `classicproductionqueues` condition
(`actiblizz.yaml:287-292`):

```yaml
	Production@NORMAL:
		Produces: Vehicle
		RequiresCondition: !classicproductionqueues
	Production@CLASSICPRODUCTIONQUEUES:
		Produces: RAVehicle
		RequiresCondition: classicproductionqueues
```

So this is not 3 new queues, it is **6**: `LightVehicle`/`RALightVehicle`,
`Vehicle`/`RAVehicle`, `SuperVehicle`/`RASuperVehicle`. Every unit tag becomes
`Queue: LightVehicle, RALightVehicle`, matching the existing `Queue: Vehicle, RAVehicle` pattern.

---

### 5. The three steps that are easy to forget

1. **The AI stops building anything in a queue it has never heard of.** `ai.yaml:4488`:
   ```
   UnitQueues: Infantry, RAInfantry, SCZergInfantry, Vehicle, RAVehicle, Starport, Aircraft, …
   ```
   The four new names must be added or every bot silently stops producing light and super vehicles.
   This produces no error and no crash — just an AI that never fields a tank again.
2. **`ProductionBar`** is per production type (`ProductionBar@VEHICLEGDI: ProductionType: Vehicle`),
   so each factory needs bars for the types it now produces, in both condition variants.
3. **`ProductionQueue` needs its audio block repeated** — `ReadyAudio`, `BlockedAudio`,
   `QueuedAudio` etc. are per-queue, not inherited from a sibling. Copy the block or the new
   queues go silent.

---

### 6. Scope

| item | count |
|---|---|
| `Queue: Vehicle` tags to re-sort | **1193** |
| `Queue: RAVehicle` tags to re-sort | **1160** |
| vehicle-producing buildings needing new `Produces:` | ~85 `Produces: Vehicle` + 79 `RAVehicle` |
| new `ProductionQueue` trait blocks | 6 (3 × 2 systems) |

**The classification is the real work, not the plumbing.** The ledger already carries a
`class_anchor` per actor under `["design"]["class_anchor"]`, and it already has the right buckets:

    epic_vehicle    24     <- the Super queue
    scout_vehicle   28     <- the Light queue
    light_tank      16     <- the Light queue
    mbt             42
    high_tech_tank  26
    line_breaker    30
    ...             total 346 tagged

But only **346 actors are tagged at all**, and **122 `Vehicles` + 4 `Tanks` carry a `design` block
with no `class_anchor`** — with well over a thousand `Queue: Vehicle` tags in yaml, most vehicles
have no class assignment to sort on. So the honest order is:

1. finish `class_anchor` tagging for vehicles (a balance-ledger job, and useful on its own);
2. generate the `Buildable.Queue` rewrite mechanically from the tag — never hand-sort 1193 entries;
3. hand-author only the ~164 `Produces:` lines and the 6 queue blocks.

---

### 7. Open decisions for the maintainer

1. ✅ **RULED 2026-08-22 — `scout_vehicle` ONLY, for now.** Maintainer: *"the rule should be
   that scout vehicles, support vehicles and maybe light tanks are part of the light queue ...
   I'm not yet sure about anything else than the scout vehicle class so let's try it only with
   those and keep the other two in mind for later once we have figured it out."*

   So the Light queue opens with the **28 tagged `scout_vehicle`s** and nothing else.
   `support` and `light_tank` are the two candidates held back deliberately — decide them after
   the three-queue split is in and playable, not before. Starting narrow is also the cheap
   option: 28 retags instead of 44+, and widening later is one more mechanical pass over the
   `class_anchor` tag, whereas narrowing after release takes a unit away from players who have
   already learned to build it there.
2. **Harvesters, MCVs and support vehicles** — one of `Light`, `Vehicle`, or left where they are.
   An MCV in the Light queue would let a light factory rebuild a base.
3. **Does the super factory replace the war factory or stack with it?** The containment ladder
   above means a super factory alone can build everything, which makes the war factory redundant
   once you have one. If they should stack, the super factory produces `SuperVehicle` **only**.
4. **Naming.** `LightVehicle` / `Vehicle` / `SuperVehicle` keeps the existing `Vehicle` string
   untouched, so nothing already tagged has to move except the units that change bucket. Underscore
   law is satisfied (no hyphens); the queue strings are engine tokens either way.

---

## Which stats are DERIVED in traits rather than authored

_Merged 2026-08-23 from `docs/design/DERIVED_STATS_IN_TRAITS.md`, unedited below this line._

_Feasibility analysis, 2026-08-19. Maintainer: "I want the turn rate to be automatically set as
speed/5 for both the mobile trait and the turreted trait … Also the self healing, shield recharge and
the repairable traits should be scaled with the health … I want to see if everything we have already
discussed is already implemented."_

Same principle as [`AREADAMAGE_WARHEAD.md`](AREADAMAGE_WARHEAD.md): **the template is
the big brain, the inline entry is one brain cell.** That document does it for weapons; this one does
it for actors.

---

### 1. Status — what is actually implemented today

| rule | documented | implemented? |
|---|---|---|
| `Mobile.TurnSpeed = Speed / 5` (turreted) | DESIGN §307 | ⬜ hand-set in yaml, checked by `audit_stat_formulas` |
| `Turreted.TurnSpeed` equals it | DESIGN §307 | ⬜ hand-set |
| turretless / frontal = `2 × Speed / 5` (= Speed ÷ 2.5) | DESIGN §308 | ⬜ hand-set |
| fighters & bombers = `Speed / 15` (frontal 2×) | DESIGN §310 | ⬜ hand-set |
| helicopters & spaceships = `Speed / 5` | DESIGN §311 | ⬜ hand-set |
| self-heal `Step = HP / 2500`, infantry `HP / 1000` | DESIGN §302 | ⬜ hand-set as a FLAT `Step:` |
| shield regen = `2 × self-heal` | DESIGN §303 | 🟡 **partly — already scales with max HP** |
| **ramp-up over time** | discussed | 🟡 **BUILT, but only for ArmorPlating** |
| **per-tick resolution** instead of per-25-ticks | requested | ⛔ not implemented |
| **never heal 0 on a tick** | requested | ⛔ not implemented |
| `Repairable` = `HP / 20` | DESIGN §1318 | ⬜ hand-set |

Two pleasant surprises and one gap worth naming:

- **`GrantsShield` already scales with health.** It is a **Cameo** trait and carries
  `PercentageRegenAmount = 2` — *"Percentage OF MAX HEALTH refilled each interval"*. So "shield
  recharge should scale with health" is **already true**; what is missing is the resolution and the ramp.
- **The ramp is already built and proven** — `ArmorPlating.cs` (W21 R7):
  `rate = base * min(1, ticks_since_damage / RampTicks)`, `RampTicks = 125`, and its own `[Desc]`
  already says *"50 for infantry; shields use 250"*. The pattern exists; it simply was never applied
  to self-heal or to the shield.
- **`ChangesHealth` has `PercentageStep`** — so percentage self-heal needs no new code *in principle*.
  But it is **integer percent**, and `HP / 2500` is **0.04%**, which integer percent cannot express.
  That single fact is why self-heal needs a Cameo trait and the shield does not.

---

### 2. Turn rate — hooks exist, but they are the wrong shape

Both hooks are real:

```csharp
Mobile.cs:332    TurnSpeedModifiers = self.TraitsImplementing<ITurnSpeedModifier>()…
Turreted.cs:189  turnSpeedModifiers  = self.TraitsImplementing<ITurretTurnSpeedModifier>()…
```

⚠ **But they are INTEGER PERCENTAGE modifiers, not setters**, and that loses the value. To express
`TurnSpeed = Speed / 5` for a Speed-100 unit you want 20; from a base of 512 that is
`20 × 100 / 512 = 3%`, and 3% of 512 is **15, not 20** — a 25% error, worse at low speeds. Percentage
hooks are right for *"the Archer turns at 50% while firing"* and wrong for *"derive the absolute
value"*.

**Three routes, and the boring one is best:**

| route | exact? | risk |
|---|---|---|
| **(a) generate the values into yaml** | ✅ exact | none — no C#, reviewable in the diff, already audited |
| (b) Cameo trait reflectively setting `MobileInfo.TurnSpeed` at `IRulesetLoaded` | ✅ exact | writes a `readonly` field; load-order fragile; invisible in yaml |
| (c) shadow `Mobile`/`Turreted` in `OpenRA.Mods.Cameo` | ✅ exact | ~900-line trait forked from upstream forever |

**Recommendation: (a).** Turn rate is a *static* value with no runtime input — there is nothing to
compute per tick, so computing it at runtime buys nothing and costs precision. Generating it puts the
formula in exactly one place (the generator), makes every value exact, keeps it visible in review,
and `audit_stat_formulas` already fails when yaml drifts from the rule. That IS the "big brain in the
template" model — the same one `gen_weapon_template.py` already uses for warheads.

⚠ Routes (b) and (c) also hide the number from `extract_stats`, which reads yaml. Pricing would stop
seeing turn rate entirely.

---

### 3. Self-heal — needs one new Cameo trait; the per-tick maths turned out fine

`ChangesHealth` is `sealed` and internal in `OpenRA.Mods.Common`, so it cannot be subclassed; the
answer is a small Cameo trait (`ScaledSelfHeal`) and a yaml key swap. Fully mod-side — no `engine/`.

**What it needs:**

1. **Basis-point percentage** (`PercentageStepBasisPoints`), because `HP / 2500` = 0.04% and integer
   percent cannot hold it. 2500-HP steps make `HP / 2500` land exactly on integers, so the rate is
   clean once the unit is fine enough.
2. **Per-tick application** — `Delay: 1`, with the rate divided by 25 to keep the *same* total rate.
   The maintainer's ask is a **resolution** change, not a rate change: `1% / 25` per tick over 25
   ticks is still 1% per second, just smooth instead of a step.
3. **A floor of 1**, so a tick can never heal nothing — see the measurement below.

✅ **RESOLVED BY MEASUREMENT — a plain floor is enough, no accumulator.** I argued for a remainder
accumulator on the grounds that a 1000-HP infantryman heals 0.4/tick and would floor to 0. The
maintainer pushed back — *"no infantry has 1000 HP, I think the lowest is the engineer and medic at
5000"* — and the data says they are right and my example was imaginary. It came from DESIGN's 1000-HP
*step*, not from any actual unit:

    actors carrying ChangesHealth@SelfHealing        1043
    MINIMUM HP among them                            5000   (spies, attack dogs, yuri_clone)
    median HP among them                           67 500
    self-healers below 1 hp/tick at 0.04%               0   <-- none. lowest is 2.00/tick

So plain integer per-tick maths is already exact for every unit that self-heals, and a **floor of 1**
costs nothing because it never fires. Keep the floor anyway: it is the guard rail for the day someone
adds a sub-2500-HP self-healer, and it makes "never heals" structurally impossible.

⚠ The floor DOES over-heal if a self-healer below 2500 HP is ever added (at 2500 HP the rate is
exactly 1.00/tick — that is the break-even). If the roster ever goes below it, revisit the
accumulator; do not silently accept a unit healing at up to 2.5x its specified rate. An
`audit_stat_formulas` check on `min(HP) >= 2500 for self-healers` would catch it mechanically.

---

### 4. Shield — the smallest job of the three

`GrantsShield` is already Cameo and already percentage-of-max-HP. It needs exactly what self-heal
needs, minus the scaling that is already there:

- `RegenInterval: 25` → per tick, rate ÷ 25, same floor-of-1;
- basis points, for the same 0.04% reason;
- **the ramp**, copied from `ArmorPlating.RampTicks` — and `ArmorPlating`'s own `[Desc]` already
  prescribes **250 for shields**, so the number is chosen, just not wired;
- keep `DamageCooldown = 250` (a hard "no regen for N ticks after damage"); the ramp then governs how
  fast it returns to full rate afterwards. Cooldown and ramp are complementary, not duplicates.

Design rule §303 (`shield regen = 2 × self-heal`) then becomes derivable rather than typed.

---

### 5. Repairable

`Repairable`/repair rate is documented as `HP / 20` (DESIGN §1318) and is an engine trait. Same
verdict as turn rate: **generate it into yaml.** Static value, no runtime input, and pricing reads it.

---

### 6. Recommended order

1. **`ScaledSelfHeal`** (new Cameo trait): basis points + per-tick + floor + ramp.
2. **`GrantsShield`**: same three changes on a trait we already own.
3. **Generator pass** for the static values — turn rates (all four cases) and repair rate — plus a
   `doc_claims` entry so drift is caught.
4. **Then the weapon half**, `AREADAMAGE_WARHEAD.md` (weapon half) — same principle, much larger blast
   radius (3243 yaml nodes), and it shares the basis-point unit with this work. Do it after the
   per-tick + basis-point pattern is proven here on something small.

⚠ Every one of these changes what units actually do in play. Each needs `extract_stats` re-run, the
ledger committed WITH the yaml, and a boot gate — and the self-heal/shield changes are **balance
changes**, so they need a maintainer order, not just this document.
