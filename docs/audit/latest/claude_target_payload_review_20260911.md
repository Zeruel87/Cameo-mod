# CL-01 — target/payload review of the 19 remaining four-faction rows

**Agent:** Aedis's Claude Code coordinator (Claude Opus 5)
**Base commit reviewed:** `447115e4c1cc8a9abffd6fd0a5c7aeadca35b596` (PR #345, branch
`codex/overnight-integration-20260910`)
**`cameo-mod/Cameo-mod` master at time of review:** `ae02eedc0`
**Date:** 2026-09-11
**Write scope honoured:** this file only. No gameplay yaml, helper, baseline, price, status file or
shared receipt was modified. No engine build, no game launch, no `--check-yaml`, no merge, no claim
of another task.

**This is a STATIC review. It does not claim gameplay proof.** Every disposition below rests on
resolved yaml and engine source, not on observed play.

---

## 0. Summary

| disposition | rows | which |
|---|--:|---|
| **retain** | 17 | 76, 77, 78, 211, 212, 213, 214, 215, 216, 217, 219, 220, 221, 222, 223 — plus 224's parent behaviour |
| **correctness fix proposed** | 2 | 101, 102 — the point-defence interception route |
| **retracted** | 1 | 103 — I over-claimed; `PointDefenseTesla` is not broken (see §4.0) |
| **design decision needed** | 2 | 224 (Stealth Tank spawned `CHFlame` vs air) and a system-wide anti-infantry-vs-airborne policy question surfaced by 220–222 |

Rows 220–222 are counted under **retain**; the policy question they surface is listed separately
because it is not Havoc-specific and must not be resolved by changing Havoc.

**The headline finding is that most of these warnings are not defects.** 16 of 19 come from the
receipt's own documented approximation, which its `mask_semantics` field already warns about:

> *"ValidTargets-minus-InvalidTargets is a DOMAIN-level approximation of the engine's
> Overlaps()-based test; retain the raw tags and the requires_custom_tag_review flag when
> interpreting any candidate."*

That warning is correct and it is load-bearing. `requires_custom_tag_review: true` is set on 18 of
the 19 rows, which is the receipt telling the reader, accurately, that the flag alone decides
nothing.

**One finding is a genuine, provable defect**: the point-defence weapons on four actors can never
damage what they are built to shoot down, because the weapon's acquisition mask and its warhead's
application mask are satisfiable only in mutually exclusive target states.

---

## 1. Why 16 of the 19 warnings are false positives

### 1.1 The engine tests warhead masks against the VICTIM ACTOR's target types

`engine/OpenRA.Mods.Common/Warheads/Warhead.cs:55-58`:

```csharp
protected bool IsValidTarget(BitSet<TargetableType> targetTypes)
{
    return ValidTargets.Overlaps(targetTypes) && !InvalidTargets.Overlaps(targetTypes);
}
```

called at `Warhead.cs:74` as `IsValidTarget(victim.GetEnabledTargetTypes())`, and at
`Warhead.cs:92` as `IsValidTarget(victim.TargetTypes)` for frozen actors.

**The bitset it is tested against is the actor's, and a Cameo actor's target types mix DOMAIN tags
and TYPE tags in one flat set.** Resolved through `miniyaml.Ruleset.resolve`:

```
td_nod_lighttankmkii   Targetable          = Ground, Vehicle, Tank
td_gdi_havoc           Targetable          = Ground, Infantry
                       Targetable@Epic     = Epic
                       Targetable@ParachuteAir = Air, Paratrooper
```

So a warhead declaring `ValidTargets: Vehicle, Ship, Air, Cyborg, Defense, Building, Epic` **does**
apply to a ground vehicle: `Vehicle` overlaps `{Ground, Vehicle, Tank}`. Nothing about the absence
of the literal token `Ground` from the warhead's list prevents it.

`dual_root_payload_excludes_surface` is therefore raised whenever a warhead filters by actor **type**
rather than by **domain**. It is a property of the notation, not of the behaviour.

### 1.2 These are the recipient-filtered integrity effects CL-01 asked to be separated

All 13 `excludes_surface` rows are the same shape: an EMP-family warhead
(`AffectsIntegrity`, `OpenRA.Mods.Cameo/Warheads/AffectsIntegrityWarhead.cs:24`, a
`DamageWarhead` subclass) with

```
ValidTargets:   Vehicle, Ship, Air, Cyborg, Defense, Building, Epic
InvalidTargets: Shielded
```

That list is a deliberate recipient filter with two intentional properties:

* **it includes every machine category and omits `Infantry`** — EMP disables machines and does not
  disable people, which is the design;
* **it excludes `Shielded`** — a recipient-state exclusion, i.e. a shielded target is immune while
  the shield holds.

Both are design statements expressed in the only place the engine reads them. Rewriting them to add
domain tokens would not change behaviour against any current actor and would destroy the
infantry/machine distinction the list exists to express.

**Disposition for all 13: `retain`. No change proposed.**

| row | root | weapon / payload | damage | binding |
|---|---|---|--:|---|
| 76 | `MammothTuskTeslaTargetingComputer` | self, `Warhead@EMPUnit` | 16000 | `ra1_soviets_mammothtank` `Armament@TeslaSECONDARYTargetingComputer`, requires `upgrade_teslarockets && promotion_mammothtanktargetingcomputer` |
| 77 | ″ | `MammothTuskTeslaFragment1` via `/Warhead@TeslaArc/Weapon` (`FireShrapnel`) | 8000 | same |
| 78 | ″ | `MammothTuskTeslaFragment2`, second arc hop | 4000 | same |
| 211 | `ra1_soviets_kamovattackhelicopter_kamovmissilestesla` | self | 5000 | `ra1_soviets_kamovattackhelicopter`, `Armament@MissilesUpgrade` + rocket-pod variants |
| 212 | `ra1_soviets_mammothtank_mammothtusktesla` | self | 16000 | `Armament@TeslaSECONDARY`, requires `upgrade_teslarockets && !promotion_…targetingcomputer` |
| 213 | ″ | `MammothTuskTeslaInfantryFragment1` | 8000 | same |
| 214 | ″ | `MammothTuskTeslaInfantryFragment2` | 4000 | same |
| 215 | `ra1_soviets_monstertank_missile_tesla` | self | 53250 | `ra1_soviets_monstertank` `Armament@TeslaSECONDARY` |
| 216 | ″ | `MammothTuskTeslaInfantryFragment1_ExplicitDamage21of20` | 8000 | same |
| 217 | ″ | `MammothTuskTeslaInfantryFragment2` | 4000 | same |
| 219 | `td_gdi_empgrenadier_grenade_emp` | self, `Warhead@EMPCompatibility` | 32000 | `td_gdi_empgrenadier` `Armament` + `Armament@GARRISONED` |
| 223 | `td_nod_stealthsoldier_bhreddarts` | self, `Warhead@EMPCompatibility` | 5000 | `td_nod_stealthsoldier` `Armament@PRIMARY` + `Armament@Garrison` |

**Identity preserved as required:** rows 77/78, 213/214 and 216/217 are arc *hops* of their parent,
not separate weapons, and the `_ExplicitDamage21of20` and `Fragment2` names are reused across
parents. The repeated `Armament@…GARRISONED`, `Armament@…RocketPod*` and `.colorpicker` bindings are
aliases of one armament, not extra findings.

⚠ **One note on the arc chain that is worth keeping.** The receipt marks each hop
`secondary_mask_role: "selection_only"`, i.e. the referrer's target tags choose the *next arc
victim* and do not gate damage application. I have **not** independently verified that
`FireShrapnel` in this tree behaves that way; I am accepting the receipt's own annotation. If that
annotation is wrong, rows 77/78, 213/214 and 216/217 would need re-examination — but their parents
(76, 212, 215) would not.

---

## 2. `retain` — Havoc, rows 220–222

| row | weapon | warhead | type | damage |
|---|---|---|---|--:|
| 220 | `td_gdi_havoc_rifle` | `Warhead@SniperWeaponPercentage` | `AreaDamagePercentage` | 2 |
| 221 | `td_gdi_havoc_sniper` | `Warhead@Bullet_Heavy` | `AreaDamage` | 40000 |
| 222 | `td_gdi_havoc_sniper` | `Warhead@SniperWeaponPercentage` | `AreaDamagePercentage` | 10 |

Bindings: `td_gdi_havoc` `Armament@M16` / `Armament@M16GARRISONED` (220) and
`Armament@ra1_allies_alliedsniper` / `Armament@SniperGARRISONED` (221, 222). The two
`…GARRISONED` armaments are garrison aliases of the same weapons.

Warhead masks are `ValidTargets: Infantry, Monster, Garrisoned`, root is `Ground, Water, Air` minus
`Structure`. Flagged `dual_root_payload_excludes_air`.

**This is the same notation artifact as §1.** An anti-personnel payload filters by the `Infantry`
type tag, and every ground infantry actor carries `Infantry` in its target set, so the payload
applies normally. The root's `Air` token permits *acquisition*; it does not oblige the payload to
list `Air`.

**Disposition: `retain`, matching the explicit instruction not to nerf Havoc and not to add `Air`
to clear a domain-only warning.** I found no reason to disagree with that instruction on the merits:
the surface-only rifle/sniper split is coherent, and Havoc's Air capability is an armament-level
property, not a warhead-level one.

---

## 3. DESIGN DECISION — anti-infantry payloads versus AIRBORNE flying infantry

This is **not** a Havoc finding and must not be fixed on Havoc. Rows 220–222 merely surfaced it.

Resolved, `naxis_skymage` (class `flying_infantry`):

```
Targetable@GROUND    TargetTypes = Ground, Infantry   RequiresCondition = !airborne && !untargetable
Targetable@AIRBORNE  TargetTypes = Air                RequiresCondition =  airborne && !untargetable
```

**While airborne, a flying-infantry actor loses the `Infantry` tag entirely.** Therefore *every*
warhead whose mask is `Infantry, Monster, Garrisoned` — not just Havoc's — applies zero effect to a
flying infantry unit while it is in the air, even when the firing weapon can legally acquire it.

Player-visible impact: a sniper or anti-personnel unit can target an airborne flying-infantry unit,
fire, and do nothing.

**Alternatives:**

1. **Accept as designed.** Flying infantry is deliberately immune to anti-personnel fire while
   airborne; anti-air handles it. Zero change, and consistent with the `anti_air_vehicle` /
   AA-armament design already ruled.
2. **Add `Air` to the airborne targetable alongside a type tag** — e.g.
   `Targetable@AIRBORNE: Air, Infantry` — so anti-personnel weapons keep working in the air. One
   line per flying-infantry actor, but it silently makes every anti-personnel weapon in the game an
   anti-air weapon against that class, which cuts directly against the AA range law's intent.
3. **Introduce a distinct `FlyingInfantry` tag** and let specific payloads opt in. Most precise,
   most work, and it needs a policy on which payloads opt in.

**Recommendation: option 1 (accept), and write it down in `docs/DESIGN.md` as intended behaviour.**
It is the only option that changes nothing, it is consistent with the anti-air rules already ruled
on 2026-09-08, and options 2 and 3 both widen anti-air capability as a side effect of clearing a
warning. **This is a policy call for Aedis, not a correctness fix.** Affected consumers if option 2
or 3 were ever chosen: every actor in the `flying_infantry` class, plus every warhead whose mask is
`Infantry`-family.

---

## 4. CORRECTNESS FIX PROPOSED — point-defence interception cannot damage its target

### 4.0 ⛔ RETRACTION — row 103 is NOT a defect. I grouped it wrongly.

**Corrected 2026-09-11 after Codex shipped `663147217`.** `PointDefenseTesla`
(`mods/cameo/ContentPacks/RedAlert/Soviets/yaml/weapons.yaml:455`) already carries the correct mask
on its DAMAGE warheads:

```yaml
PointDefenseTesla:
    ValidTargets: Ground, Air, Missile, Bullet, BallisticMissile
    Warhead@Tesla_Heavy:
        ValidTargets: Ground, Air, Missile, Bullet, BallisticMissile
        Damage: 10000
    Warhead@Tesla_Heavy_ExtraDamage: SpreadDamage
        ValidTargets: Ground, Air, Missile, Bullet, BallisticMissile
        Damage: 5000
```

15,000 damage, correctly masked, against a 10,000 HP `^ShootableMissile`. **`ra1_soviets_heavyteslatank`
intercepts correctly and nothing about it needs changing.**

The row the receipt surfaced at index 103 was its `Warhead@EMPUnit` at `ValidTargets: Ground, Water`
— an integrity side-effect that simply does not apply to a projectile. That is the same
type-versus-domain notation artifact as §1, and it belongs in the `retain` group.

**My error was one of grouping, not of measurement**: I saw three point-defence roots carrying a
`Ground, Water` payload and wrote a single finding covering all three, when only two of them have
their damage on that payload. The claim "the point-defence armament acquires an incoming ballistic
missile, plays its firing effect, and delivers nothing" is **true for `PDLaserBike` and
`PDLaserLTNK2` and false for `PointDefenseTesla`**. Everything below applies to the two PDLaser
weapons only.

⭐ And `PointDefenseTesla` is useful evidence rather than just a retraction: it is the same role
against the same target with **15,000 damage**, which is what makes §4.3 below a real question
rather than a nitpick.

---

**Rows 101 and 102. This is the one hard defect in the set.**

| row | weapon | warhead | type | damage | bindings |
|---|---|---|---|--:|---|
| 101 | `PDLaserBike` | `Warhead@1Dam` | `SpreadDamage` | 1 | `td_nod_reconbike`, `td_nod_chemicalattackbike` — `Armament@pointdefense`, requires `td_nod_upgrade_blackmarketupgrades` |
| 102 | `PDLaserLTNK2` | `Warhead@1Dam` | `SpreadDamage` | 1 | `td_nod_lighttankmkii` — `Armament@pointdefense`, **unconditional** |

### 4.1 The masks are satisfiable only in mutually exclusive target states

Weapon acquisition masks:

```
PDLaserBike / PDLaserLTNK2   ValidTargets:   Ground, Air, Missile, BulletAS, BallisticMissile
                             InvalidTargets: Infantry, Vehicle, Tank, Structure, wall
```

Payload mask: `ValidTargets: Ground, Water` on both. Both are thin subclasses of `PDLaser`
(`Inherits: PDLaser`, overriding only `Range`), so the defect and its fix both live on the parent.

The only actor in the active tree declaring an interceptable-projectile target type is the missile
actor at `mods/cameo/rules/defaults.yaml:6986-6991`:

```
Targetable@GROUND
    TargetTypes: Ground, Vehicle
    RequiresCondition: !airborne
Targetable@AIRBORNE
    TargetTypes: Air, BallisticMissile
    RequiresCondition: airborne
```

(`grep -rn "TargetTypes:.*\(Missile\|BulletAS\|BallisticMissile\)" mods/cameo/` returns exactly one
match — this one.)

Therefore, for the state in which interception actually happens:

| missile state | actor target types | weapon can acquire? | warhead can apply? |
|---|---|---|---|
| **airborne** (in flight) | `Air, BallisticMissile` | **yes** — `BallisticMissile` overlaps, and `Vehicle` is absent so the InvalidTargets exclusion does not bite | **no** — `{Ground, Water}` does not overlap `{Air, BallisticMissile}` |
| not airborne | `Ground, Vehicle` | **no** — `Vehicle` is in InvalidTargets | yes — `Ground` overlaps |

**The weapon can only select the missile in the state where its warhead cannot touch it.** Player
impact: the point-defence armament acquires an incoming ballistic missile, plays its firing effect,
and delivers nothing. Two of the three bindings are **unconditional**, so this is live on
`td_nod_lighttankmkii` and `ra1_soviets_heavyteslatank` in every game, with no upgrade required.

This also explains, and is consistent with, the maintainer's earlier observation that the Light Tank
Mk II's point-defence laser contributes 0 to that unit's DPS. **Contributing 0 to *pricing* is
correct and should stay** — it is a utility interception weapon, not an offensive one. Contributing
0 to *interception* is the defect.

### 4.2 Smallest change, and every affected consumer

**Smallest change:** widen the three payload warheads' `ValidTargets` to cover the airborne
projectile state, e.g. `Ground, Water, Air, BallisticMissile` (add `Missile`/`Bullet`/`BulletAS` to
match whichever tokens the corresponding weapon acquires).

**Affected consumers — complete list, from the receipt's bindings:**

| warhead owner | consumers |
|---|---|
| `PDLaserBike` | `td_nod_reconbike`, `td_nod_chemicalattackbike` (both gated on `td_nod_upgrade_blackmarketupgrades`) |
| `PDLaserLTNK2` | `td_nod_lighttankmkii` (unconditional) |

Each warhead is used by its own weapon only, so the blast radius is exactly these four actors and no
shared template is touched. ⛔ `Warhead@1Dam` and `Warhead@EMPUnit` are **warhead nodes**, so under
`CLAUDE.md` rule 4 / DESIGN.md this change needs explicit maintainer permission before anyone edits
it, and `Versus` must not be introduced inline.

### 4.2b ✅ FIXED by Codex in `663147217`, and the fix is better than the one I proposed

```yaml
PDLaser:
    Warhead@1Dam: SpreadDamage
+       ValidTargets: Ground, Missile, BulletAS, BallisticMissile
```

Adding `BallisticMissile` without generic `Air` closes the overlap against `^ShootableMissile`'s
airborne targetable (`Air, BallisticMissile`) **without** granting anti-air splash to a
point-defence laser. I had suggested adding `Air`; this is the more precise change. It propagates
to both consumers through `Inherits: PDLaser`.

### 4.3 ⚠ What I did NOT verify, and why it matters here

**The mask fix is necessary but — still — not sufficient.** Confirmed at `663147217`:

```
^ShootableMissile   HP: 10000   Armor.Type: Bomber
PDLaser             Damage: 1   ReloadDelay: 25
```

One damage per shot against ten thousand HP is 10,000 hits at 25 ticks each. The warhead now
applies, and applies 1. The missile actor has `Health.HP: 10000`
and `Armor.Type: Bomber`. Rows 101 and 102 carry **damage 1**. Even with a correct mask, 1 damage
against 10,000 HP destroys nothing, so interception would still fail unless a separate kill
mechanism exists that I have not found — for example an `AffectsIntegrity`/destroy path, a
`Versus: Bomber` multiplier in the `^Warhead_*` template, or an AS interception trait outside the
warhead. **I did not locate such a mechanism and I did not rule out that one exists.**

Before anyone changes a warhead, that question should be answered, because it decides whether the
fix is one line per warhead or a redesign of the interception route. I recommend Codex resolve it,
since the projectile/interception tooling is in its lane.

I also did not verify the behaviour in play, and this review cannot establish that it is broken in a
running game — only that the two masks, as written and as the engine reads them, cannot both be
satisfied by the same target state.

---

## 5. DESIGN DECISION — row 224, the Stealth Tank's spawned `CHFlame`

```
root     td_nod_stealthtank_stealthtankmissilesblackmarket   (Ground, Water, Air)
 route   /Warhead@Shrapnel/Weapon (FireShrapnel)
      -> td_nod_stealthtank_stealthtankmissilesshrapnel
      -> CHFlame   Warhead@Flame_Medium   AreaDamage   damage 2000   ValidTargets: Ground, Water
binding  td_nod_stealthtank  Armament@Upgrade   requires td_nod_upgrade_blackmarketupgrades
```

The parent missile may engage air; the spawned flame payload is ground/water only.

**Unlike §4, this is not obviously wrong.** A flame pool is a ground-denial effect and `Ground,
Water` is a defensible mask for one. The question is whether the black-market upgrade is *advertised*
as adding flame damage to everything the Stealth Tank can shoot, because against aircraft it adds
none.

**Alternatives:**

1. **Accept.** Flame is ground-denial; the upgrade's anti-air value is the missile itself. No change.
2. **Gate the shrapnel explicitly to ground impacts** so the behaviour is intentional rather than
   incidental, and say so in the upgrade's description.
3. **Add `Air` to `Warhead@Flame_Medium`.** ⛔ **Do not do this.** `Warhead@Flame_Medium` is a shared
   flame warhead; widening it would grant anti-air flame damage to every consumer of that warhead,
   far beyond this route. This is exactly the "clear the warning by widening a shared mask" move
   that should be refused.

**Recommendation: option 1 or 2 — I lean 2**, because it costs nothing in balance and converts an
accident into a stated design. **Policy call, not a correctness fix.** The parent missile's own
behaviour is `retain`.

---

## 6. Method, and what this review does not establish

**Verified from source, not from names:**

* `Warhead.cs:55-58`, `:74`, `:92` — the `Overlaps` semantics and that the bitset is the victim's.
* `AffectsIntegrityWarhead.cs:24` — `AffectsIntegrity` is a Cameo `DamageWarhead` subclass and does
  not override the target test.
* Actor target types resolved through `miniyaml.Ruleset.resolve`, never hand-parsed, per the
  standing rule.
* `defaults.yaml:6986-6991` — the sole interceptable-projectile target-type declaration, found by
  exhaustive grep rather than assumed.

**Not established:**

* any gameplay behaviour — no launch, no replay, no in-game observation;
* whether `FireShrapnel`'s `secondary_mask_role: selection_only` annotation is accurate (accepted
  from the receipt);
* whether a non-damage interception kill path exists for §4.3;
* whether `Targetable@ALL: Aircraft` on `naxis_skymage` carries a condition — I read only the
  `@GROUND` and `@AIRBORNE` nodes;
* anything about the other 212 candidate rows outside my assigned scope.

**One disagreement worth stating plainly.** The `dual_root_payload_excludes_surface` /
`_excludes_air` check, as it stands, produces 16 false positives out of 19 rows in this sample. The
receipt is honest about why, and `requires_custom_tag_review` carries the caveat — but a flag that
is wrong 84% of the time in its own four-faction scope will cost a reviewer more than it saves, and
risks training readers to dismiss it. **Suggestion for Codex:** partition the check by whether the
payload mask contains any DOMAIN token at all (`Ground` / `Water` / `Air`). A mask made entirely of
actor-TYPE tokens is not comparable to a domain mask and should not raise the warning; a mask that
mixes both, as in §4, is exactly where the real defect lived. That single partition would have
reduced this set to the three rows that mattered.

*Returned for Codex review. No implementation is proposed for execution by me, and no warhead has
been touched.*
