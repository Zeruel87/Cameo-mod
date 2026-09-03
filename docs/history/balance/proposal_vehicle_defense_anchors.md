> ⚠ **ARCHIVED — provenance, not current truth.**
>
> Deleted by the 83→43 documentation compaction (`20f15194`) and restored here on
> 2026-08-28 after a mechanical re-check found it was **not regenerable**, unlike the
> thirteen `proposal_*.md` reports deleted alongside it. It does not match `propose_class_rebalance.py`'s `proposal_<class>_infantry.md` output pattern, and a repo-wide search finds no generator for it at all.
>
> Its numbers are a snapshot of a **pre-W24 tree**: the weapon rebuild has moved damage
> structure since, so read it for method and for what was measured at the time, never as
> a current statement about the roster.

# PROPOSAL — vehicle + defense class anchors (baseline + verifier)

> **⚠ STALE for LightTank and MBT.** The LightTank anchor was LOCKED by the maintainer
> on 2026-07-25 at **40000 HP / 4000 dmg / 40 reload / cost0 400** (see
> `anchor_decisions_log.md`), superseding the 50000/5000/50/500 proposed below.
> The MBT anchor (Tiger) is also locked at the values shown in
> `anchor_decisions_log.md`. The remaining classes below are still proposals
> pending maintainer confirmation.

_Maintainer asked me to **propose, you confirm** (2026-07-25). Every class gets a **baseline** (the
100% anchor) **and a verifier** (the 250% tripwire = **2× HP + 2× DPS + 2.5× cost**, same range/
speed as the baseline) — because the baseline→verifier band holds ~80% of units. Grounded in the
real Cameo roster + the **Tiger MBT** anchor (100000 HP / 100 spd / 5000 rng / 10000 dmg / 50 reload
/ **cost0 800**, DPS 200). Numbers are round-number **proposals** — edit any cell. Nothing applied;
no yaml/anchors touched until you sign off. Run order after confirm: create the 4 new templates
(boot-gated) → `fit_class` per class → sign._

DPS shown = damage ÷ reload. Verifier target = **2× the baseline's HP and DPS, 2.5× its cost0,
identical range + speed** (so the tier/role cancels and the identity is exact); its named unit is
**restatted** to that target.

## Vehicle classes

| Class | Baseline unit | HP | Spd | Rng | Dmg | Reld | **cost0** | Verifier unit (→ restat 2×/2×/2.5×) |
|---|---|--:|--:|--:|--:|--:|--:|---|
| **LightTank** (NEW) | `ra1_allies_alliedlighttank` | 50000 | 120 | 4500 | 5000 | 50 | **500** | `td_nod_lighttank` → 100000/·/·/10000@50 / **1250** |
| **MBT** (exists = Tiger) | `tiger.nax` | 100000 | 100 | 5000 | 10000 | 50 | **800** | `td_gdi_battletank` → 200000/·/·/20000@50 / **2000** |
| **HighTechTank** | `ra1_allies_alliedtigerheavytank` | 130000 | 90 | 5500 | 14000 | 50 | **1300** | `naxis_kingtigerheavytank` → 260000/·/·/28000@50 / **3250** |
| **TankDestroyer** (NEW) | `ra2_allies_tankdestroyer` | 70000 | 95 | 6500 | 18000 | 60 | **900** | `ra1_allies_alliedtankdestroyer` → 140000/·/·/36000@60 / **2250** |
| **AntiAirTank** (NEW) | `ra2_soviets_flaktrack` | 50000 | 110 | 6000 | 4000 | 20 | **600** | `ra1_allies_alliedheavyaatank` → 100000/·/·/8000@20 / **1500** |
| **ArtilleryTank** (NEW) | `naxis_brummbr` (Brummbär) | 80000 | 80 | 9000 | 12000 | 90 | **1000** | `naxis_sturmtiger` → 160000/·/·/24000@90 / **2500** |
| **Artillery** | `ra1_allies_alliedartillery` | 25000 | 70 | 12000 | 15000 | 100 | **700** | `ra1_soviets_v2rocketlauncher` → 50000/·/·/30000@100 / **1750** |
| **FireSupport** | `td_gdi_archerartillery` | 60000 | 80 | 7000 | 12000 | 60 | **900** | *(needs a clean sibling — flag)* → 120000/·/·/24000@60 / **2250** |
| **LineBreaker** | `cabal_manticore` (dual weapon) | 90000 | 90 | 5500 | 10000 | 50 | **1000** | *(needs a clean sibling — flag)* → 180000/·/·/20000@50 / **2500** |
| **ScoutVehicle** | `td_nod_buggy` | 30000 | 140 | 5000 | 4000 | 40 | **350** | `ra1_soviets_gatlingtank` → 60000/·/·/8000@40 / **875** |
| ~~**SupportVehicle**~~ | **EXEMPT** — no consistent damage ⇒ not in the pipeline at all (maintainer 2026-07-25) | | | | | | | — |

## Defense classes

Defenses are static → the formula's "speed" term needs a convention (legacy = speed 100; pipeline
§5 wants a **footprint/power-draw** substitute). **Using speed 100 as a placeholder here — needs a
ruling.** Also note the §7 building damage-exemption (defenses effectively tankier than HP alone).

| Class | Baseline unit | HP | Spd* | Rng | Dmg | Reld | **cost0** | Verifier unit (→ restat 2×/2×/2.5×) |
|---|---|--:|--:|--:|--:|--:|--:|---|
| **BasicDefense** | `ra2_allies_pillbox` | 80000 | 100 | 5000 | 8000 | 40 | **600** | `ra2_soviets_sentrygun`/`flakcannon` → 160000/·/·/16000@40 / **1500** |
| **AdvancedDefense** | `ra2_soviets_teslacoil` | 120000 | 100 | 6500 | 16000 | 50 | **1400** | `ra2_allies_prismtower` → 240000/·/·/32000@50 / **3500** |
| **SuperDefense** | `ra2_allies_grandcannon` | 200000 | 100 | 8000 | 25000 | 60 | **3000** | *(faction super-defense sibling)* → 400000/·/·/50000@60 / **7500** |
| **AntiAirDefense** | `ra2_allies_patriotmissilesystem` | 90000 | 100 | 7000 | 6000 | 25 | **900** | `ra1_soviets_samsite` → 180000/·/·/12000@25 / **2250** |
| **Bunker** | `ra2_soviets_battlebunker` | 100000 | 100 | (garrison) | — | — | **600** | `yuri_tankbunker` — garrison-damage, likely baseline-only / special |

\* placeholder — resolve the defense mobility-term convention first.

## Open flags (need your call)

1. **Defense mobility term** — speed 100 placeholder, or the footprint/power-draw substitute (pipeline §5)?
2. **FireSupport + LineBreaker verifiers** — thin candidates in the RA2/TD/RA1 pull (both are more TS/
   CABAL concepts). Name the intended baseline/verifier, or I pull the TS/CABAL ledgers.
3. **Support (medics / mechanics / casters / mind-control / spies) = FULLY EXEMPT** (maintainer
   2026-07-25): no consistent (or no) damage ⇒ nothing to calculate ⇒ **not in the balance pipeline
   at all.** The ONE class outside every balancing effort. `check_band.py` already skips them.
3b. **★ CARGO-PRICING RULE (maintainer 2026-07-25) — cargo units ARE balanced, deterministically.**
   Any **cargo vehicle or aircraft** (APC, troop transport, Battle Fortress, etc.) is priced at the
   **SUM of the infantry it carries at full capacity** — *even if it has no weapon.* This is a FIXED
   rule, separate from the damage formula. Verified: Battle Fortress `Cargo.MaxWeight 6` @ 4000¢,
   GDI APC `MaxWeight 8`. So an **unarmed transport is NOT exempt** (that's the passenger-sum rule);
   only NON-cargo support (medics/casters) is exempt (#3). **New pipeline rule** (encode into
   `check_band`/pricing): if an actor has a `Cargo:` trait, its cost target = Σ(passenger costs at
   capacity), and it is checked against THAT, not the class formula. *(Confirm the per-slot reference
   infantry cost — capacity 6 → 4000¢ implies ~667¢/slot, i.e. an elite loadout assumption.)*
4. **Bunker** — damage comes from garrisoned infantry, so it may be baseline-only (HP + cost only).
5. **commando (infantry)** — needs a verifier (currently null). Propose: commando verifier =
   a 2×/2×/2.5× hero sibling. (Support is exempt per #3 — no verifier.)
6. All **cost0** values default toward the unit's **original/current price** (the nostalgia default,
   §20) — flag any you want moved.
