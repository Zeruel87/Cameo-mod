# The AreaDamage warhead — design, rebalance and the unified node

Two documents until 2026-08-23. The universal `SpreadDamage` -> `AreaDamage` conversion is
COMPLETE; what remains here is the design rationale and the unified-node shape, which the
3-way split and every new warhead template still build on.

Related: [`WEAPON_3WAY_SPLIT.md`](WEAPON_3WAY_SPLIT.md), `DESIGN.md` §11b (one damage warhead
per weapon).

---

## Warhead design + energy chips

_Merged 2026-08-23 from `docs/design/AREADAMAGE_WARHEAD_REBALANCE.md`, unedited below this line._

Maintainer design session, 2026-08-03. This doc is the **canonical capture** of the
AreaDamage warhead decision and the wider weapon/warhead/projectile rebalance that
surrounds it. It is not yet threaded into `DESIGN.md` / `ROADMAP.md` (the maintainer had
live uncommitted edits there); fold the binding parts in on the next clean commit pass.

Related: `ARMOR_SYSTEM.md` (Versus/step law), `WEAPON_TYPE_SYSTEM.md`,
`WEAPON_3WAY_SPLIT.md`, `FORMULA_V2.md` (SUM law)
(→ now the AreaDamage decision), `cameo-versus-only-in-templates`.

---

### 1. The `AreaDamage` warhead (C# — MOD code, not the engine submodule)

**File:** `OpenRA.Mods.Cameo/Warheads/AreaDamageWarhead.cs` (repo root — the Cameo assembly
lives at the root, NOT in `engine/`; so this is a normal `dotnet build`, NO engine mirror).
Extends `DamageWarhead` (from `OpenRA.Mods.Common.Warheads`), mirrors `SpreadDamageWarhead`'s
spatial pass, and adds the ring/DoT + baked friendly-fire.

**At defaults (`Ticks: 1`, `MaxRadius: 0`) it is byte-behaviour-identical to `SpreadDamage`**
plus baked FF — so it can safely become the universal main-warhead type.

Fields:
- Spatial (same as SpreadDamage): `Spread`, `Falloff[]`, `Range[]`, `DamageCalculationType`.
- `Ticks` (default 1) — number of damage applications. >1 = damage over time.
- `TickDelay` (default 0) — engine ticks between applications.
- `MinRadius` / `MaxRadius` (default 0) — when `MaxRadius>0`, the damaged radius GROWS from
  MinRadius to MaxRadius across the ticks (expanding shockwave); when 0, every tick covers the
  full Falloff range (a **static DoT cloud**).
- `TickDamage[]` (optional, length == Ticks) — relative per-tick damage weights, integer-normalised
  against the authored `Damage` (truncation can leave a small remainder). A DECREASING profile (`5,4,3,2,1`) + expanding
  radius = the **nuclear shockwave** the maintainer wants: *small area / high damage first → each
  tick larger area / weaker damage*. INCREASING builds up instead. Omit for an even split.
- **Baked friendly fire** (replaces the `_FriendlyFire` twin): `FriendlyFireDamage` (default 50 =
  Cameo law; 0 disables FF), `FriendlyFireSpread` (default 50 = allies only hit within half radius).

**Balance invariant:** the authored `Damage` is always the TOTAL before per-tick integer
modifiers, so the balance pipeline reads ONE number on the current 100-damage grid. Runtime
integer division can leave a small remainder (three even ticks apply 33% each); the pricing
model mirrors those exact modifiers instead of silently redistributing the remainder.

### 2. Conversion scope — ALL 55 template main warheads → AreaDamage

Maintainer escalated the scope (2026-08-03): **every central-template main warhead becomes
`AreaDamage`**, not just the AoE families. What stays behind:
- **`_Percentage` twin** stays `HealthPercentageDamage` — it is a different damage channel (% of
  max HP) with its OWN per-template Versus ladder (Bullet_Light %None:16, Bullet_Medium %None:20,
  vs the main's None:100). Cannot be baked in. Present on all 55 templates.
- **`_ExtraDamage` warhead** stays `SpreadDamage` (bespoke per-weapon Versus — see §3). Per-weapon
  on energy/special weapons, NOT in the templates.
- **`_FriendlyFire` twin is DELETED** everywhere — folded into AreaDamage's FF fields.

**Friendly fire — UNIVERSAL (maintainer 2026-08-03, supersedes the earlier small/big-spread split):**
EVERY template's main warhead is AreaDamage with baked FF `FriendlyFireDamage: 50` + `FriendlyFireSpread: 50`
(50% damage within 50% radius). This INCLUDES precise / energy / AA weapons — at 50%/50% the ally
damage is minor for thin-spread weapons, and the maintainer chose it over a pile of per-weapon
overrides. Even **aircraft AA missiles keep FF** (fighter self-splash is acceptable at 50%/50%; NO
fighter-AA override). `ValidRelationships` opens to `Ally, Neutral, Enemy` so the trait can apply FF.
The energy **ExtraDamage** chips (§3) are a SEPARATE mechanic (thematic anti-class bonus), independent
of FF; "compensate small spread" belongs in the formula (§4), not the chip.

Scope confirmed for the AoE/FF families: **Flame, Chemical, Demolition, Concussion, Sonic,
Melee(=Sword), Nuclear, +Magic** (maintainer added Magic; Magic is the %-equalizer, ground-only —
it gets AreaDamage + FF too). Sonic + Sword confirmed IN.

### 3. ExtraDamage investigation (maintainer asked: meaningful or redundant?)

Grep of the live tree: ExtraDamage appears on ~250 weapon nodes across 36 files. **Three
genuinely different profiles** (so "they all work differently per warhead" — confirmed):

1. **Meaningful RPS profile — KEEP.** `TeslaExtraDamage`: Shield 300, Heroic 200, Plate 175,
   Flak 150, None 125 (infantry HIGH), vehicles 75/50/25, buildings/aircraft 10. A real
   **anti-infantry + anti-shield** bonus that defines Tesla's identity. NOT redundant.
2. **Near-inert anti-shield chip — DECIDE.** `LaserExtraDamage` / `RailgunExtraDamage` /
   `MagicExtraDamage`: `Shield 100, everything else 1` (Damage 1 → floors to ~0 vs non-shielded).
   Contributes **nothing against ~90% of targets** — only vs Shield/Reflector. It is pure
   rock-paper-scissors "energy beats shields," NOT the "compensate small spread" the maintainer
   intended (it does not raise damage vs normal armor at all).
3. **Different mechanic — KEEP.** `SniperWeaponExtraDamage: OpenToppedDamage` — hits garrisoned /
   transport passengers (`Infantry, Monster, Garrisoned`). Unrelated to shields.

**Decision (maintainer 2026-08-03):**
- **OpenTopped garrison-hit CONFIRMED KEEP.** Verified in engine: `OpenToppedDamageWarhead`
  (`OpenRA.Mods.AS`) calls `DamagePassengers()` on every `INotifyPassengersDamage` trait —
  implemented by `Cargo` (transports), `Garrisonable` (garrisoned buildings) and `SharedCargo`
  (bunkers). It damages the passengers INSIDE, bypassing the transport's armor (Versus targets
  `Infantry, Monster, Garrisoned`). A real special; keep on the sniper (and any anti-garrison unit).
- **Anti-shield chips (Laser/Railgun/Magic) → REPURPOSE into thematic GAP-FILL bonuses** (the Tesla
  model). CORRECTION (2026-08-03, maintainer caught it): the earlier "railgun is weak vs heavy, the
  chip fixes it" was WRONG — reasoned from the Bullet (anti-light) ladder. The ACTUAL energy mains
  already carry identity + shields (verified from templates):
  - Railgun main: `Superheavy 100 › Heavy 96 › Medium 92 … infantry 68–80 … air 40–52`, `Shield 140`
    → anti-heavy VEHICLE, ground-only.
  - Tesla main: `Superheavy 100 › Heroic 96 › Heavy 92 › Plate 88 …` → anti-heavy INF+VEH, ground-only.
  - Laser main: `Superheavy 100 › Heroic 94 › Spaceship 88 › Heavy 76 …` → anti-heavy, HITS AIR.
  - Prism main: `Scout 100 › None 94 › Wood 88 › Light 82 … Superheavy 34` → anti-LIGHT infantry (inverted).
  So the chip is REDUNDANT as anti-shield (the main already does `Shield 110/140`). Its ONLY real job
  is **thin-spread compensation** (`50% of main, EXCLUDED from price`), best spent as a THEMATIC
  gap-fill (cover the class the main is weakest vs). PLUS: **thin the energy main Spread 800 → ~150**
  (near single-target — that IS "almost only hits one target"), tighter falloff.
  **FINAL Versus ladders (maintainer 2026-08-03) — Damage = 50% of main, thin spread, excluded from price:**
  - **Laser** → anti-INFANTRY (light-focused): `None 200, Flak 175, Plate 150, Heroic 125, Shield 100,
    Scout 75, Light 50, Medium 25, Heavy 10, Superheavy 10, buildings 10, air 10`. (Laser main still
    hits air; the chip is the ground anti-infantry burn — best vs LIGHT infantry `None`.)
  - **Railgun** → anti-BUILDING + superheavy (siege): `Concrete 200, Steel 175, Wood 150, Superheavy 125,
    Heavy 100, Medium 75, Light 50, Scout 25, infantry 10, air 10, Shield 10`. Building order is
    toughest-first (Concrete > Steel > Wood). Shield 10 CONFIRMED (kinetic ≠ anti-shield; the railgun
    MAIN still does Shield 140).
  - **Tesla** → anti-INFANTRY (armor-focused) + shield (KEEP): `Shield 300, Heroic 200, Plate 175,
    Flak 150, None 125, Superheavy 100, Heavy 75, Medium 50, Light 25, Scout 10, buildings 10, air 10`.
  - Laser vs Tesla are INVERTED on the infantry ladder (Laser best vs None/light, Tesla best vs
    Heroic/armored) + Tesla is the big anti-shield (300 vs Laser's 100) — deliberately distinct.
  - **Prism** → NO chip (dedicated anti-light beam). **Magic** → DROP the chip (%-HP equalizer is its
    special). CONFIRMED.
  Net: each energy weapon = a thin-spread single-target specialist, main = what it kills, chip = a
  distinct thematic secondary; none overlap. Chip stays `SpreadDamage`, bespoke Versus, excluded from
  price. Fallback if minimal is preferred: delete all chips, let the main Shield Versus carry shields.
- **Sniper OpenTopped is ANTI-GARRISON, not anti-transport.** Verified: `Warhead@SniperWeapon`
  `ValidTargets: Infantry, Monster, Garrisoned` cannot target vehicles, so it never fires at an APC —
  but it CAN target a garrisoned building (`Garrisoned` target type) and `Garrisonable` takes the
  passenger damage. Keep it as the anti-garrison tool. Anti-transport passenger damage would have to
  ride on a weapon that can target vehicles (not the sniper).
- **"Compensate small spread with extra damage" belongs in the FORMULA, not a chip** — a warhead
  that is inert vs most targets compensates nothing in general combat (§4). Separate the two ideas:
  ExtraDamage = deliberate anti-class RPS; spread compensation = pricing.

#### ★ REVISION 2026-08-08 (maintainer + reasoning pass — supersedes the "chip on Laser/Railgun/Magic per fixed thematic ladders + fallback delete-all" framing above)

**Governing law (replaces "chip excluded from price, fallback delete all"):** a chip is allowed
**only if it is PAID FOR** — never free power. The payment is one of: the K=1.25 multiplier, a
weapon downside (charge delay), or a structural handicap (thin spread + wasted air-ladder slots).
No handicap ⇒ no chip. This keeps every uniqueness source *accountable* (role = warhead class;
combos = a second priced warhead; ability = K; delivery = projectile/effect layer).

**Chips survive on exactly five weapons, each with its payment:**

| weapon | chip | pays for it |
|---|---|---|
| **Tesla** | keep old `TeslaExtraDamage` (Shield 300, Heroic 200, None 125, Superheavy 100, Concrete 10) | K=1.25 (EMP weak, so K covers EMP+chip) — its *original* reason for existing |
| **TeslaCharged** | keep old `TeslaChargedExtraDamage` — **STRONGER** (Shield 400, Heroic 300, None 225, Superheavy 200, Concrete 50) | Super tier + K |
| **Sniper** | `SniperWeaponExtraDamage: OpenToppedDamage` | genuine engine mechanic (garrison passenger hit), not a Versus tweak |
| **Laser** | **anti-LIGHT flat chip** = the Laser `%`-warhead Versus ladder REVERSED (anti-heavy→anti-light), materialised as SpreadDamage, restricted to infantry+vehicles (buildings/air ≈10), Damage = 50% of main (~5–12% effective) | thin energy spread + the 4 air slots pushing ground damage down |
| **Railgun** | keep anti-building siege chip (Concrete 200 > Steel 175 > Wood 150 …) | a **charge delay** on every railgun (CannonAP fires instantly = the pure tank-killer, no chip) |
| Prism / all non-energy | **NONE** | Prism = utility (cryo/scatter, K); others have no handicap |

**Unified energy law:** every energy weapon = thin single-target spread + ONE paid compensation
(a chip paid by K / charge-delay / air-handicap, OR utility for Prism). No energy weapon gets free power.

**Magic vs Sonic — VERIFIED NOT REVERSED (2026-08-08, real HP).** With the current baselines
(infantry 20–60k, MBT 100k, Mammoth 500–600k, Epic 1–5M), shots-to-kill proves the mirror:
Sonic (flat) scales with HP → anti-low-HP / anti-swarm (2 shots vs infantry, 256 vs an epic);
Magic (%HP) converges to ~11 shots regardless of HP/armor → anti-high-HP / giant-killer. The
oppressive giant-killer belongs on the *rare* weapon (Magic), not the common Sonic. Keep as-is;
they are damage-calculation TYPES, not chips. (Matches.)

### 4. Spread pricing + spread reduction (open formula work)

- **How spread enters the balance formula (OPEN):** bigger spread = higher *potential* damage when
  fighting many small units, but it does **not** scale linearly — against a single target, spread
  is irrelevant. So spread must be priced with **diminishing returns** (an expected-targets-hit
  model), never a flat multiplier. Needs a proper term in FORMULA_V2. Take the total-damage-over-
  the-spread-area into account, capped by the single-target case.
- **Reduce spreads overall** — many weapons have too much spread. Old pre-split model tied
  projectile **Inaccuracy = Spread**; the SpreadDamage falloff is ~3–4 concentric circles where the
  Spread value is the radius step (e.g. 100 @100%, 200 @34%, 300 @17%, 400 @5%). Even small weapons
  ended up with a big footprint. Normalise smaller. Lever: **raise projectile speed → lower
  inaccuracy → lower spread** (see §5). Reason each family individually; don't bulk-shrink blindly.

### 5. Projectile speed / tank-shell rules (write down; apply later)

- **Regular tank:** projectile speed = `maxRange / 10`; warhead **CannonHE**; **2× the spread** of
  CannonAP (HE = area, less targeted — bigger spread is correct).
- **Tank destroyer + any cannon TURRET (gun turret):** projectile speed = `maxRange / 5` (double);
  warhead **CannonAP only** (targeted); **smaller spread**. Faster shell → hits reliably without a
  big spread.
- **CannonHE spread > CannonAP spread** — deliberate (HE splashes, AP is a targeted penetrator).
- **Hybrid tanks (in-between: Light Tank, High Tech Tank, and case-by-case units):** **50% CannonAP
  + 50% CannonHE** (damage split evenly between the two warheads), projectile speed =
  `maxRange / 10 * 1.5` (between a normal tank and a TD). Apply the hybrid scaling only to units
  that are genuinely between a TD and a normal tank; keep it a per-unit choice, but the **logic is
  now recorded** so hybrids can be built consistently.
- Bullets are the fastest (small spread), cannons slower (bigger spread), **missiles slowest but
  can hit air** — slower projectiles may warrant a small compensating bonus for travel delay
  (relates to the ExtraDamage/formula question in §3–§4).

### 6. Epic vehicle template rework (mirror the epic AIR template)

Make `^EpicVehicleTemplate` work like the epic **aircraft** template: it only **advances** a unit
(build-limit, faster build time, commando/epic decoration) and **no longer defines the unit type
OR the armor**. An epic vehicle then inherits **both** its underlying class template **and** the
epic template — e.g. the **Chrono Tank = `^FireSupportVehicleTemplate` + `^EpicVehicleTemplate`**
(both required, since epic no longer supplies type/armor). Mirrors how epic aircraft can be a
spaceship or a bomber underneath. Balancing epic units is hard (they are very different from each
other) — attempt per-unit; no clean class anchor yet. This changes the current epic model where
`L=0.3, M=1.0` folds the whole epic effect into UnitClass (DESIGN §12) — keep that pricing, just
split the *template* responsibilities.

### 7. Build / rollout plan (the order to execute)

1. **Build the trait** — `AreaDamageWarhead.cs` is written (+ per-tick `TickDamage` shaping).
   `dotnet build -c Release --nologo -p:TargetPlatform=win-x64`; fix compile errors; boot-gate.
2. **Pipeline updates** (Python): `formula.spread_damage_sum` + `audit_warhead_split` must treat
   `AreaDamage` exactly like `SpreadDamage` (sum its `Damage`; still skip `_Percentage`,
   `_ExtraDamage`; the `_FriendlyFire` twin is gone). One-line type-name additions.
3. **Convert the 55 templates** — `Warhead@X: SpreadDamage` → `Warhead@X: AreaDamage`; delete the
   19 `_FriendlyFire` twins; set `FriendlyFireDamage` per §2 (50 for AoE, 0 for precise/energy);
   `_Percentage` / `_ExtraDamage` untouched. Scripted over the template block, boot-gate.
4. **Nuclear + cluster** — migrate the ~10-stacked-warhead bandaid onto one AreaDamage with
   `Ticks`/`TickDelay`/`MinRadius`/`MaxRadius`/`TickDamage` (decreasing). Retire the stacked nodes.
5. **Spread reduction + projectile-speed pass** (§4–§5) — after the type conversion, as balance.
6. **Epic vehicle template split** (§6) — independent; can run in parallel.

Everything after step 1 is boot-gated per commit; scoped `git add`; the C# needs a rebuild before
the boot gate.

### 8. The universal conversion CASCADES to retrofitted weapons (discovered + reverted 2026-08-03)

Splicing all 55 templates to AreaDamage **crashes the boot** — because ~hundreds of weapons across
~50 files were ALREADY retrofitted onto these `^Warhead_*` templates (Phase-2) and override the
inherited warheads in ways that clash with the new type. Attempted, boot-gated (crashed), REVERTED to
the known-good Nuclear-pilot state. The three clash classes:

1. **`-Warhead@X_FriendlyFire:` REMOVAL nodes** (e.g. `RedAlert2/Yuri/weapons.yaml:853` removing
   `Warhead@Chemical_Medium_FriendlyFire`) → `no elements with key ... to remove` at ResolveInherits.
   The template no longer provides the twin (baked in), so the removal is invalid. **This is the FIRST
   crash hit** (fails during inherit resolution, before field-loading).
2. **`Warhead@X: SpreadDamage` main RESTATEMENTS** (e.g. `CHFlame` → `Warhead@Flame_Medium: SpreadDamage`).
   MiniYaml keeps the child's `SpreadDamage` type but inherits the template's AreaDamage-only fields
   (`FriendlyFireDamage`/`FriendlyFireSpread`) → FieldLoader "unknown field on SpreadDamageWarhead"
   crash. (Not reached before #1, but would follow.)
3. **`Warhead@X_FriendlyFire: SpreadDamage` REDEFINITIONS** (~150) → become STANDALONE double-FF
   warheads (the main's baked FF + this leftover twin). Not a crash, but wrong (double ally damage).

**Resolution-awareness is mandatory.** Some `Warhead@X` keys are defined by LOCAL templates, NOT the
`^Warhead_*` family — e.g. `Warhead@Demolition_Light` on `^DamagingExplosionHE` (which inherits
`^Explosion`, defines its OWN twin). Weapons like `RockExplode` inherit those and their removals stay
VALID → must NOT be touched. The sweep only acts on a `Warhead@X` node when the weapon's resolved
`@wh`/inherit chain provides that key from a `^Warhead_*` template (not a closer local template).

**Staged sweep plan (the correct next operation — one boot-gated unit):**
1. Resolution-aware script (PROVIDES graph, like the earlier retrofit repairs): for every weapon whose
   `Warhead@X` resolves to a `^Warhead_*` template — (a) delete `-Warhead@X_FriendlyFire:` removal
   lines; (b) delete `Warhead@X_FriendlyFire: …` twin blocks; (c) strip ` SpreadDamage` from the
   `Warhead@X:` main override → bare (inherits the AreaDamage type); (d) if that main override also
   restates `ValidRelationships: Neutral, Enemy`, strip it too (so the template's `Ally, Neutral, Enemy`
   + baked FF stands). Dry-run counts first.

   **No separate per-weapon AA FF override exists to remove** (maintainer asked 2026-08-03): AA damage
   weapons just inherit the template's enemy-only default, so the universal AreaDamage+FF conversion
   (plus step (d)) gives them FF automatically. The `ValidRelationships: Enemy` overrides that DO exist
   in the tree are on **condition warheads** (snare / lock-on / corroded `GrantExternalCondition`) —
   correctly enemy-only, MUST NOT be touched.

   **Reduce the MissileAA template spread** (maintainer 2026-08-03): so the now-universal FF on anti-air
   is well-contained (fighters can dodge the 50%/50% ally splash). Add a per-family spread override for
   `MissileAA` in the generator, tighter than the default `400/600/800` (e.g. ~`250/350/450` — tune).
2. Re-apply the generator changes (main → `AreaDamage`; `ValidRelationships: Ally, Neutral, Enemy`;
   add `FriendlyFireDamage: 50` + `FriendlyFireSpread: 50`; remove the FF twin; naming `^Warhead_{tag}`
   + `Warhead@{tag}_Percentage`; `AREA_RINGS = {Nuclear: ticks5/delay6/max4000/5,4,3,2,1}`;
   `AA_ENEMY_ONLY = set()` — universal FF). These 4-ish edits are documented here + were verified to
   regenerate the Nuclear pilot byte-for-byte.
3. Regenerate + splice the 55 templates (anchor-based region replace, spot-check one template diff).
4. **Boot-gate.** 5. Pipeline: `spread_damage_sum` / `audit_warhead_split` recognize `AreaDamage`.
6. Commit generator + weapons + the weapon sweep TOGETHER.

Until then: the Nuclear pilot (committed `851537a03`) is the ONLY live `AreaDamage`; the 55 templates
stay `SpreadDamage`; the generator is reverted to `SpreadDamage` so it stays consistent with the file.

### 9. AreaDamagePercentage + AtomicCore = the first real in-game proof (2026-08-04)

The Nuclear pilot (`^Warhead_Nuclear_Super`) is an ABSTRACT `^`-template → **never
instantiated** → the AreaDamage trait was compiled but NEVER actually constructed at
runtime (the "pilot boot" was a false pass). AtomicCore is the first concrete instantiation.

**`AreaDamagePercentage` warhead (BUILT + BOOTS, uncommitted).** `OpenRA.Mods.Cameo/Warheads/
AreaDamagePercentageWarhead.cs` — a one-method subclass of `AreaDamageWarhead` overriding
`InflictDamage` to deal a **percentage of the victim's max HP** (mirrors `HealthPercentageDamage`).
It REUSES the entire ring/tick/baked-FF spatial pass; its `Falloff` collapses a whole STACK of
concentric `HealthPercentageDamage` rings into ONE smooth % gradient. Degrades to a single-hit
%-with-falloff at `Ticks:1`/`MaxRadius:0`.

**AtomicCore / Atomic / RA2Atomic converted (uncommitted, boot-gated to menu).**
- AtomicCore now `Inherits@nuke: ^Warhead_Nuclear_Super` and uses that AreaDamage nuke **as-is**
  (maintainer: "no override — superweapons ignore ReloadDelay"). Its 6 stacked `SpreadDamage`
  rings deleted; its 10 `NuclearMissilePercentage` rings → **one** `AreaDamagePercentage`
  (`Spread 1000, Damage 100, Falloff 100..0`, radiation/fire types, `UpdatesUnitStatistics: false`).
  Tesla-shield layers + effects/smudge/shake/flash kept.
- `RA2Atomic` (inherits Atomic) re-skinned the 6 rings with `RadiationDeath`; consolidated onto a
  single `Warhead@Nuclear_Super:` override carrying the radiation DamageTypes.

**⚠ Cascade lesson — the empty-type warhead boot crash.** Deleting `Warhead@X` from a `^template`
orphans any CHILD weapon with a **bare** `Warhead@X:` override (it relied on inheriting the type).
The bare override then resolves to an **empty type** → the engine builds the abstract base `Warhead`
→ `GetConstructor([])` null → **NullReferenceException in `ObjectCreator.CreateBasic`** during
`LoadDefaults` — and the stack **names no weapon**. Here `RA2Atomic`'s bare `Warhead@1Dam_impact:`
crashed every boot until fixed. Guard: `scratchpad/find_empty_warhead.py` resolves all 37 live
weapon files and names the offending weapon (0 = safe); `check-yaml` reproduces it fast without a
full boot. **Run the empty-type scan after ANY template warhead deletion/rename.** (Memory:
`cameo-empty-warhead-crash`.)

**Build/deploy fact:** `dotnet build` → `engine/bin`
(gitignored, what the running `engine/bin/OpenRA.exe` loads). `mods/cameo/OpenRA.Mods.Cameo.dll`
is a git-TRACKED copy that does NOT auto-update (was a month stale) — refresh it from engine/bin
only for release/commit.

---

## The unified AreaDamage node

_Merged 2026-08-23 from `docs/design/UNIFIED_AREADAMAGE_WARHEAD.md`, unedited below this line._

_Feasibility analysis, 2026-08-19. Maintainer proposal:_

> *"can we do the same for the percentage twin? … one trait that combines both. You have Versus and
> you have percentage versus, then you have the normal damage and the percentage damage. And you can
> set a scaler of how much percentage damage the weapon does compared to the flat damage … Only ONE
> number inline, everything else in the templates. The templates will be like the big brain and the
> inline weapon like an individual brain cell."*

**Verdict: yes, and the tree is already shaped for it.** The percentage twin is not an independent
warhead — it is the flat warhead with three constants applied, and the tree agrees on all three.

---

### 1. Why it works: the twin is already a subclass with ONE differing expression

`AreaDamagePercentageWarhead` is **65 lines** and inherits everything from `AreaDamageWarhead`.
It overrides exactly one method, and the only real difference is what the damage is a percentage OF:

```csharp
// AreaDamagePercentageWarhead.InflictDamage
var damage = Util.ApplyPercentageModifiers(healthInfo.HP,        // <-- flat half passes `Damage`
                args.DamageModifiers.Append(Damage, DamageVersus(victim, shape, args)));
```

Spread, Falloff, Ticks, MinRadius/MaxRadius, friendly fire, `PhysicalState`, `IntegrityScale` —
all inherited, all already shared. There is no second mechanism to merge, only a second *base
quantity*. `DamageVersus` is `protected virtual` and already overridden in `AreaDamageWarhead`, so a
second lookup table is a normal extension, not surgery.

### 2. The three constants are already the convention — and 2544 hand-typed numbers drift from them

Measured across every resolved weapon carrying a flat/percentage pair:

| relationship | measured | conformance |
|---|---|--:|
| `percentage = flat / N` | **N = 2000, median, in ALL 22 families** | 2544 pairs |
| `percentage Spread = flat Spread / 2` | ratio **0.50** | **2381 / 2487 (96%)** |
| `percentage Falloff = flat Falloff` | identical | **2499 / 2544 (98%)** |

The rule already exists — `WEAPON_3WAY_SPLIT.md` calls it *"% = 1-per-2000"*. What does **not** exist
is enforcement, and the per-family min/max shows what that costs:

    Bullet_Medium    250 … 12000   (48x spread around the intended 2000)
    Railgun_Heavy   2000 … 80000   (40x)
    Demolition_Light 167 …  4000   (24x)

Every one of those is a weapon whose percentage chip is silently 5x or 40x off intent, and **nothing
in the audit suite can see it**, because each value is individually plausible. Baking the ratio into
the warhead does not just remove typing — it removes the entire error class.

### 3. The design

Everything below lives in the **template**. The weapon inline sets `Damage:` and nothing else.

```yaml
^Warhead_CannonHE_Heavy:
    Warhead@CannonHE_Heavy: AreaDamage
        Damage: 2000                      # ← the ONLY number an inline weapon overrides
        Spread: 800
        Falloff: 100, 50, 25, 10, 5, 0
        Versus:                           # flat table
            Heavy: 108
            ...
        # ---- percentage half, folded in ----
        PercentageScale: 10000            # Damage 2000 -> 100 basis points = 1.00% max HP.
                                          #   10000 is today's "1% per 2000". THIS is the per-family
                                          #   dial: a chemical family scales harder, a kinetic one
                                          #   softer, without touching a single weapon.
        PercentageSpread: 50              # % of the main Spread — mirrors FriendlyFireSpread: 50
        PercentageVersus:                 # its own table; falls back to Versus when omitted
            Heavy: 90
            ...
        # ---- concrete half, folded in ----
        DamagesConcrete: true             # slab damage = Damage x Versus[Concrete] / 100, 1:1.
                                          #   NO scale knob — ruling 2026-08-19: a wall, a building
                                          #   and a slab all take the same Concrete damage.
        # ---- already folded in (the friendly-fire precedent) ----
        FriendlyFireDamage: 50
        FriendlyFireSpread: 50
```

and the weapon becomes:

```yaml
SomeCannon:
    Inherits@wh: ^Warhead_CannonHE_Heavy
    Inherits@proj: ^Projectile_Shell_Heavy
    Inherits@fx: ^Effect_CannonHE_Heavy
    ReloadDelay: 40
    Range: 6144
    Warhead@CannonHE_Heavy:
        Damage: 40000                     # one number. The percentage and the slab damage follow.
```

`PercentageDenominator` moves to **10000** (0.01% steps) so the derived value has room: today's
integer percentages run 1–42, which is a 42-step ladder for the entire game. At 0.01% steps the same
range is 100–4200 and the derived number is never forced to round.

### 4. The concrete half is reachable mod-side — no engine change

`DamagesConcreteWarhead` (in `OpenRA.Mods.D2k`) is **twelve lines**:

```csharp
var layer = world.WorldActor.Trait<BuildableTerrainLayer>();
var cell = world.Map.CellContaining(target.CenterPosition);
layer.HitTile(cell, Damage);
```

and `OpenRA.Mods.Cameo.csproj` **already references `OpenRA.Mods.D2k`** (line 16), so `AreaDamage`
can call `HitTile` directly. This does not touch `engine/` and needs none of the engine-update
pipeline. Routing it through `Versus[Concrete]` is the maintainer's proposal and is self-consistent:
a weapon that is good against concrete *buildings* is good against concrete *slabs*.

### 5. What it removes

| | nodes |
|---|--:|
| `*_Percentage` warheads on concrete weapons (1235 weapons) | **2946** |
| `*_Percentage` warheads in templates | 166 |
| `DamagesConcrete` warheads on concrete weapons (55 weapons) | 56 |
| `DamagesConcrete` warheads in templates | 75 |
| **total yaml nodes deleted** | **3243** |

⛔ **EVERY pure concrete warhead is DELETED, not kept alongside** (maintainer: *"you need to remove any
pure concrete damage warheads now because it's all included into the main area damage warhead right?
so no more duplicates right?"* — yes). A surviving `Warhead@Concrete: DamagesConcrete` next to a folded
`AreaDamage` would hit the slab twice. `audit_weapon_identity` and `review_batch_diff` both run per
batch, and a leftover is exactly the kind of double-application that neither the boot gate nor a
damage-total check would flag.

It also halves the `multi_main_fired_weapons` accounting problem: a percentage twin is a second
`Warhead@` node on 1235 weapons.

---

### 6. Risks and open questions — the honest list

**R1 — RESOLVED BY RULING (maintainer, 2026-08-19).** *"I want 1:1 any damage to concrete to go to
the concrete slabs. So doesn't matter if the target is a wall or a building or a concrete slab, the
damage it deals to concrete is definitely going to all of them equally and if we need we should
increase the concrete slab health. So I say do it!"*

So there is no `ConcreteScale` at all — **slab damage IS `Damage × Versus[Concrete] / 100`, 1:1**, the
same number a concrete wall or building would take. One rule, no third knob, and the `Concrete` Versus
row means exactly what it says everywhere it appears.

⚠ The compensation moves to the SLABS, not the weapons. Current `DamagesConcrete` values are tiny and
unrelated to main damage (sampled ratios `oHMG` 1:1, `GoliathRockets_AA` 40:1, `Debris` 53:1,
`SCUDNUKE` 300:1), so routing full damage at 1:1 makes slabs melt unless `BuildableTerrainLayer`'s
per-cell health is raised to match.

#### ⭐ RULED: `BuildableTerrainLayer.MaxStrength` 9000 → **6 000 000**

`MaxStrength` is currently the engine default 9000 — `mods/cameo/rules/world.yaml:1056` declares
`BuildableTerrainLayer:` with no override at all. Maintainer 2026-08-19 asked first for 200x, then *"make it a nice 2 million"* — and the
percentage term below rules out both.

**Two measurements, and they disagree — which is why 200 is better than either.**

    effective main damage : current concrete damage      (1495 weapons carrying both)
        lower quartile     68 : 1
        MEDIAN            166 : 1
        upper quartile    352 : 1
        ratio of medians  144 : 1        <- 14 400 effective main vs 100 concrete

Median-of-ratios (166) and ratio-of-medians (144) are both defensible and neither is the whole story,
because **the fold also widens the attacker pool**:

| | weapons |
|---|--:|
| damage slabs TODAY (carry a concrete warhead) | 1504 |
| have a `Concrete` Versus row, so damage slabs AFTER | **1987** |
| **gain the ability** | **+483** (×1.32) |

⛔ **AND THEN THE PERCENTAGE HALF CHANGES THE ANSWER AGAIN.** Maintainer: *"don't forget the percentage
damage is still there so at that high value they should be kind of quickly destroyed from the
percentage values alone right?"* — correct, and it is decisive. Median effective percentage vs
`Concrete` is **0.9%**, and a percentage is a fraction of MAX strength, so it does not care how big
that maximum is:

    slab HP       flat-only weapon      weapon carrying percentage
     1 800 000        143 shots                  62
     2 000 000        159                        65
     3 000 000        238                        76
     6 000 000        476                        90      <-- today's 90
    10 000 000        794                        97
    20 000 000       1587                       104
    ceiling             --                      111      <-- UNREACHABLE at any HP

**Percentage damage CAPS slab durability no matter how high the HP goes.** At 0.9% per shot nothing
can ever take more than ~111 median shots, so past ~3M more HP buys almost nothing.

That kills 200× (1 800 000): with percentage applied it gives **62 shots — 1.4× SOFTER than today's
90** — and 483 more weapons can hit it on top. The exact opposite of "really tanky".

**6 000 000 is the number.** It is the parity point exactly
(`90 × 12600 / (1 − 90 × 0.009) = 5 968 421`) and it produces the design the ruling was reaching for:

- a weapon with **no** percentage half needs **476 shots** — concrete really is a fortification;
- a weapon **carrying** percentage clears it in **90** — exactly today's feel.

Percentage becomes *the* answer to concrete and flat damage alone effectively cannot break it, so the
rock-paper-scissors is structural rather than tuned. The quartile spread 68…352 is the noise the 131
hand-set values encode; after the fold it collapses into one honest number.

⚠ **The percentage half MUST therefore apply to slabs**, as a fraction of `MaxStrength`. If it stays
flat-only, 6 000 000 means 476 shots for every weapon and concrete becomes near-immortal.

⚠ Still a balance change: `world.yaml` + boot gate + a play check on D2k concrete-heavy maps, where
slab durability is a real strategic layer rather than a detail.

**R2 — ~106 pairs do not use the 0.50 spread rule** (56 at 1.00, 28 at 10.00, 9 at 5.00) and **45 use
a different Falloff.** They need either an explicit per-weapon escape hatch or individual conversion.
Do NOT let the migration quietly normalise them; that is exactly how the nuclear batch lost 93%.

**R3 — `Ticks` can differ between the halves.** `ThermobaricNuclearMaverick` ran the flat half at 10
ticks and the percentage half at **7**. A merged warhead shares one tick count unless a
`PercentageTicks` is added. Decide before migrating, not during.

**R4 — the meter may currently be fed TWICE.** Both `InflictDamage` paths call `ApplyPhysicalState`
and `ApplyIntegrityScale`. If a template sets `PhysicalStateScale` on both halves, the physical-state
meter and the integrity layer receive two contributions per hit. Merging makes that structurally
impossible — which is a **fix**, but it will move E2's delivery numbers, so re-measure after.

**R5 — scale of the mechanical change.** 3243 nodes across 1235 weapons. This must be a scripted
migration verified with `review_batch_diff.py` (main damage AND blast shape) plus a boot gate, in
batches. `PercentageScale` must be calibrated per family from the *measured* current ratio, not set
to a uniform 100, or families that legitimately drifted get re-priced by accident.

---

**R6 — ⛔ THE PREREQUISITE I MISSED, and it is most of the work.** §1's "65-line subclass, easy
merge" is only true for the twins that are already the Cameo type. Measured on the live tree:

    resolved *_Percentage warhead nodes
        HealthPercentageDamage (stock engine)   3378     <-- NOT foldable as-is
        AreaDamagePercentage   (Cameo)          1426
    `PercentageDenominator` anywhere in mods/      0     <-- the basis-point rollout never landed

`HealthPercentageDamage` is a different warhead with no `PercentageDenominator`, no `Ticks`, no
`Spread`/`Falloff` — there is nothing to fold it INTO until it is migrated. **So the fold is gated on
W18**, which already specs exactly this migration plus `PercentageDenominator: 10000` (the 0.01% steps
this design needs) and is marked READY on the board. Do W18 first and the fold becomes mechanical;
skip it and 3378 nodes have no path.

---

### 7. Suggested order

0. ⛔ **W18 FIRST** — migrate the 3378 `HealthPercentageDamage` twins to `AreaDamagePercentage` and
   roll out `PercentageDenominator: 10000`. Behaviour-preserving, already specced, already READY, and
   without it 3378 of 4804 nodes cannot be folded at all (R6).
1. **C# next, behind compatibility.** Add `PercentageScale` / `PercentageSpread` / `PercentageVersus`
   / `PercentageTicks` and the 1:1 concrete routing to `AreaDamageWarhead`, defaulting to **off** so
   nothing changes. Keep `AreaDamagePercentageWarhead` working.
2. **Calibrate per family** from the measured medians; write them into the generator
   (`gen_weapon_template.py`), never by hand.
3. **Migrate in batches**, `review_batch_diff` clean per batch, boot gate per batch.
4. **Then** delete `AreaDamagePercentageWarhead` and the orphaned nodes.
5. **R1 (concrete) is a separate, later item** gated on a maintainer ruling, because it is the only
   half that cannot preserve current behaviour.
