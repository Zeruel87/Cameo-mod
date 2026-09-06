# Cameo Roadmap — the live work queue

_Entry point for a new session: **[`docs/HANDOFF.md`](../HANDOFF.md)**. This file is the
granular, resumable task queue that the handoff points into._

## AI PERSONALITY SELECTOR (2026-08-21)

- [x] Add synchronized random Rush/Turtle/Tech/Expansion/Steamroller selection
  (`cdd04e5a1`).
- [x] Gate independent squad-manager instances on the selected condition
  (`cdd04e5a1`).
- [x] Add audit coverage for shared-field duplication and condition parity
  (`cdd04e5a1`).
- [ ] Observe long-match squad-value ramp behavior in-game; this branch makes no
  long-match gameplay claim.
- [x] Add an observer/replay-only chat notification so spectators can see the
  selected personality; live players intentionally receive no UI decoration
  because the indicator would leak opponent strategy.
- [ ] Consider personality-specific base-builder behavior without duplicating
  the full base-builder configuration.

## AI UNIT COMPOSITIONS (2026-08-24)

- [~] Port the opt-in unit-composition mechanism and two TD pilot compositions;
  extend the pilot to other universes and factions as a follow-up.

## AI ARCHITECTURE (2026-08-31)

Design: [`AI_ARCHITECTURE.md`](AI_ARCHITECTURE.md). Nothing here is implemented; the
design document is the deliverable so far. Ordered so each item is independently
verifiable.

- [x] Measure how ContentPack `ai.yaml` merges with the global AI file
  (add-only, packs load first, removal is a load-time crash).
- [ ] **S** Migrate one pack's `UnitsToBuild` rows out of `ai/ai.yaml` into
  `ContentPacks/TiberianDawn/GDI/yaml/ai.yaml`. **BLOCKED on merge order**
  (Devin AI, 2026-09-05): `MiniYaml.MergePartial` appends ContentPack
  `UnitsToBuild` rows BEFORE the global `ai.yaml` rows (packs load first),
  so the `td_gdi_*` rows would jump to the top of `UnitsToBuild` instead of
  their original interleaved position. A byte-identical
  `--resolved-rules Player` dump is impossible; the resolved *content*
  (same keys + values) is identical. The gate must be relaxed to
  content-identical, or the migration needs a different approach (e.g.
  keep the rows in the global file and mark them faction-owned via a
  `RequiresCondition` on the trait, not on the rows).
- [ ] **M** Repeat per pack, then per dictionary (`UnitLimits`,
  `BuildingFractions`).
- [ ] **S** Personality-specific compositions via condition-gated
  `ProvidesPrerequisite` tokens plus group tokens for OR - zero C#.
- [ ] **M** Guerrilla as the sixth personality (many small simultaneous raids).
- [ ] **M** `MasterAiBotModule`: fogged per-enemy signals, main-target scoring,
  personality choice. Switches travel as a `SetBotPersonality` order resolved by
  a synced controller trait, because bot logic may not touch synced state.
- [ ] **M** Per-enemy pairwise damage ledger (`PlayerStatistics` is aggregate and
  cannot attribute losses to a specific opponent).
- [ ] **M** JSONL match logging: match / decision / outcome records, the episode
  as the unit of learning. Record-only, no behaviour change - this is the
  proof-of-concept deliverable.
- [ ] **M** Offline aggregation tool: personality and composition performance per
  faction matchup, with a minimum sample threshold.
- [ ] **L** Bandit-style (UCB1/Thompson) personality priors per matchup, fitted
  offline and committed as reviewed data.
- [ ] **L** Headless AI-vs-AI batch harness to produce the data volume.
- [ ] **DEFERRED** Anything neural - blocked on factions and balance being
  finished, per the maintainer's own sequencing.
- [ ] **OPEN DESIGN** Fogged bot observation. Bots currently scan `World.Actors`
  and filter only cloak, never shroud, so they know the whole map from tick zero.
  This is the only real cheat left (difficulty is `BotLimits` throttling, not
  resources), and fixing it will make bots temporarily weaker and requires a
  scouting module. Maintainer's call - see AI_ARCHITECTURE.md section 9,
  decision 1.

**Rule zero: crashes and player-visible regressions ALWAYS jump the queue.** Ordering inside a
section: quickest wins first, then by severity. Effort: **S** < 1 h · **M** = one session ·
**L** = multi-session. Every completed item carries its commit hash; every new order lands here
first. Faction reference: [`FACTIONS.md`](../FACTIONS.md).

> ⚠ **Commit hashes are not resolvable in a shallow clone.** Cloud/CI checkouts of this repo are
> shallow (`git log` starts 2026-08-10), so `git show <older-hash>` fails there. Run
> `git fetch --unshallow` first, or verify the claim against the artifact instead — which is the
> better habit anyway.

> **Multi-agent repo — one owner per file-set.** Committing into this tree, by git author:
> **AedisToru** (maintainer; also lands most agent work under the shared repo identity),
> **Blackrobe** (co-maintainer), **Elpollo315**, **Zan Yewang**, and **Devin AI**. The commit
> TRAILER, not the author line, records which agent wrote a change (CLAUDE.md rule 10).
> Always `git add <files>` scoped, never `-A`. Check a file's mtime and `git log -3 <file>`
> for a live agent before editing, and re-verify others' commits before building on them.

**Closed July → early-August items** were lifted out of this file on 2026-08-23 and live in
[`docs/history/ROADMAP_ARCHIVE_2026-07.md`](../history/ROADMAP_ARCHIVE_2026-07.md). Nothing with
an open checkbox was moved.

---

## ⭐ START HERE — [`BALANCE_PROGRAM_PLAN.md`](BALANCE_PROGRAM_PLAN.md)

**The balance program's board, ownership and acceptance criteria live in ONE file:
[`docs/design/BALANCE_PROGRAM_PLAN.md`](BALANCE_PROGRAM_PLAN.md).** Work items W1–W26, one
`VERIFY` command each, file-set ownership so two agents can run in parallel, and the universal
commit gate. Any agent resuming after a compaction reads §0 and §0a of that file first.
**Do not duplicate its status here** — this ROADMAP links to it on purpose, and a status
copied into two files is how they start disagreeing.

The current front is **W24** (one damage warhead per weapon) → **W23** (retrofit the 47 legacy
templates) → **A5** → class anchors. §0a of that file is the binding order; it is why pricing
is deliberately NOT running yet.

## ⭐ PHYSICAL STATES — dilution, Magnetism, and the IFV problem (2026-08-22)

Maintainer: *"we need to rework all units that can only apply physical states from one weapon"*
and *"the IFV kind of things need their own logic so you should skip them"*.

### 1. METER DILUTION — 34 actors — **now guarded: `audit_meter_dilution.py` (ratchet 34)**

The meter fills from ONE weapon's damage but the target dies to the actor's WHOLE output, so the
effect lands far later than the per-weapon `fill_ratio` says. `physical_state_price.fill_ratio` has
a `fed_share` term for exactly this, but it works WITHIN a weapon and stops at the weapon boundary;
the actor level is not modelled at all.

⛔ **The number was 58 here and it was wrong — twice over, in opposite directions.** The measure
now lives in a committed audit instead of a scratchpad script, because both errors were invisible
in the output:

  1. counting EVERY `Armament` gave 170 and put every RA2 IFV at 10.92x — an IFV's 42 armaments
     are each gated on a distinct `ifv-<passenger>` condition, so exactly ONE ever fires.
  2. dividing meter-feeding damage by the actor's total gave 81 and scored `cobra.steel` at 5.20x
     on a ONE-gun loadout. That formula DOUBLE-COUNTS: `fed_share` already prices the dilution
     inside the state weapon. The factor the pricing cannot see is only the OTHER guns' damage,
     `actor_total / carrier_total`.

**34 actors** fire a state weapon alongside unconditional non-state weapons:

| actor | guns | with state | state guns' share | dilution |
|---|--:|--:|--:|--:|
| `japan_exorcistoitank` | 5 | 3 | 6.2% | **16.12x** |
| `cabal_hunterdronecarrier` | 3 | 1 | 10.4% | **9.60x** |
| `ra1_allies_destroyer` | 2 | 1 | 14.5% | **6.89x** |
| `cabal_manticore` / `_backup` | 2 | 1 | 18.7% | **5.35x** |
| `ra1_allies_sheridanassaulttank` | 3 | 1 | 44.4% | **2.25x** |

Distribution: 10 above 3x, 3 at 2-3x, 11 at 1.5-2x, 10 below 1.5x. `EDEN_LYNX_EMP`/`EDEN_TIGER_EMP`
are NOT on the list — both their guns carry the state, so there is nothing to dilute.

⚠ **`SheridanMissilesCryo`'s extreme Scale is a COMPENSATION for this, not an outlier.** The
Sheridan fires Cannon + Vulcan + (Missiles XOR MissilesCryo); the cryo half is 44.4% of output, so
the true ratio is 0.378, not the 0.168 the pricing sees — it is **OVER-charged 1.41x**.

**MAINTAINER'S FIX (preferred): make every weapon on a state unit apply the state** — cryo cannon,
cryo bullet, cryo rocket. Dilution becomes 1.0 by construction, no per-weapon compensation is
needed, and `Scale 100` means the same thing everywhere. Strictly better than teaching the pricing
to model actor-level dilution, because it removes the problem instead of measuring it.

### 2. ⛔ DEFERRED — the IFV class needs its own logic

`ra2_allies_ifv` and friends carry **42 armaments**, each gated on a distinct `ifv-<passenger>`
condition, so exactly ONE fires at a time. They are NOT diluted and must never be counted as such
— a first measurement did exactly that and reported 10.92x for every IFV variant. Any
per-armament analysis has to collapse condition-gated variants first. Deferred by maintainer
ruling; needs a variant-aware model.

### 3. ✅ DONE — `^Magnefreezable` → a `Magnetism` meter

The 10 `SpeedMultiplier` + 10 `WithColoredOverlay` bands became 5 meter traits, on all **739**
actors that inherit the template (`^Vehicle`, `^RANeutralPlane`, `^ShootableMissile`). The nine
overlapping band boundaries (`<= 20` and `>= 20` both hold at 20 → 90%×80% = **72%**, 60%×50% =
**30%**) are now structurally impossible: `SlowsProportionalToPhysicalState` interpolates between
two endpoints. `Burst 100 / BurstDelays 1` swept every one of those boundaries on every volley.

⚠ **NOT the sole carrier** — a first pass said `yuri_magnetron` only. `AAHyperionMagnet`
(`asianalliance_hyperionprojector`, anti-air) grants the same condition and was converted too;
so did `RA2MagnetAA` / `RA2MagnetAA_elite`, which RE-DECLARE the warhead type and would have
silently kept `GrantExternalCondition` if only the base had been edited.

Behaviour preserved deliberately: `RelativeToHealth: false` (the old stack counted SHOTS, so a
scout and a superheavy were pinned by the same 100 hits), firepower and damage modifiers OFF (the
magnetron carries `FirepowerMultiplier@MultiWeapon: 50` while not elite), and turn/turret/reload
pinned at 100 at BOTH ends — the trait defaults them to 50, and omitting them would have quietly
added three effects the magnetron never had.

⚠ **The full lock is still nearly unreachable, and that is unchanged, not introduced.** 100 shots
fill the bar; `physical_state_price` puts the fill/kill ratio at **15.1**, so the magnetron's own
laser kills long before `magnetfreeze` is granted. That was equally true of the 100-token stack.
Whether the grip should complete faster is a BALANCE question for the ledger, not a conversion bug.

### 4. More axes to convert

Documented in `PHYSICAL_STATE_SYSTEM.md` §5 but not built: **Sonic → `Resonance`** (W7, needs no
new C#), **Hex** (Magic: −firepower/−accuracy/disable specials), **ArmorBreach**, **Knockback**
(needs new C#). Only **Temperature** (98.6% exposure) and **Corrosion** (45.0%) exist today.

## ✅ RULED — the "broken ladders" were never broken (2026-08-23)

Superseded the `⛔ BROKEN LADDERS` section that stood here and had been re-reported as an open
maintainer question for days. **`audit_level_ladder` is retired.** It required a family's
EFFECTIVE damage to rise Light -> Medium -> Heavy -> Super, and no law ever said so:

* **DESIGN §12.0d** makes the LEVEL a TILT — which armor the weapon is good against — not a
  magnitude.
* **DESIGN §12.0h** makes `Damage` a separate, free knob, and normalises every profile to MEAN 100
  precisely so the tilt costs nothing.
* Structurally decisive: **145 of the `^Warhead_*` templates carry only a placeholder
  `Damage: 2000`.** The template holds the SHAPE, the weapon holds the MAGNITUDE. A family's damage
  ladder is emergent from per-weapon values, and collapsing the levels into a continuous `h` never
  touches a damage number.

So nine families sat in a standing WARN against a rule that did not exist, and it was listed as
blocker #1 of `WEAPON_HEAVINESS.md` §9.6 — blocking the bell for no reason.

> **Maintainer, 2026-08-23**, restating the model in their own words: *"the weapon family should be
> the most important and the heaviness level should only nudge it a little … a low level CannonAP
> will lean stronger towards lighter armor types but still deal more damage to heavy armor … Flame
> weapons will be the opposite … but still more damage to light, because that's their identity."*

That is §12.0d's sharpen-or-flatten sentence, and it is now **DESIGN §12.0i**, COMPLETE as of
2026-08-24: one global 13-slot armor axis 0..2 (every ladder centred on 1.000, one deliberate
three-way tie at 1.0), `mu = (h + centre_of_mass) / 2`, `LO` 0.667 (swing 1.50x = 1/`TILT_RATIO`),
`sigma` 0.75, and **heaviness has no price effect** (`Versus` = WHAT, `Damage` = HOW). The
2026-08-23 constants (`SHIFT` 0.25, `LO` 0.80, three buckets) are all retired — the axis twice, and
`SHIFT` entirely.

**Replaced by `tools/audit/audit_heaviness_bell.py`**, which simulates the bell before it exists so
§9.6 step 6 has its test waiting. Measured across 48 families, checking each ladder's FULL rank
order: **0 orderings changed, 0 mean drift**, and 2 families with no gradient (`Sonic`, `Magic` —
down from the 6 §9.2 predicted, since `fit_band_floor` gave `Cryo`/`Railgun`/`Waveforce`/`Storm`
real gradients).

⛔ **An earlier version of this section recorded two permanent "known inversions" and a gap in
§9.4 that called for authoring new gradients. Both are RETRACTED.** They were artifacts of the
audit skipping §12.0d's rank restore — the tilt is applied to the VALUES and each armor is then
given back the RANK it held. Without that step the bell reorders ladders in **127** cases across 60
family/ladder pairs; with it, **zero**. Nothing needs authoring.

⛔ **The x-axis is NOT settled.** The maintainer wants every armor to carry its OWN unique
continuous value; the interim per-ladder form is unique within a ladder but collides across them.
Recorded as an explicit OPEN block in DESIGN §12.0i — think it through before changing anything.

⭐ **The bell is unblocked.** §9.6's blockers 1 and 2 are both gone — blocker 2 (every family in the
spread band) was already finished on 2026-08-22 and the document had not noticed
(`audit_versus_profile`: 46 in band, `SPREAD_OFFENDERS_BASELINE = 0`). Next action is §9.6 step 5:
implement the family-anchored bell in `AreaDamageWarhead`, **inert at h=1**, and prove the resolved
profiles are byte-identical before any weapon sets a different `h`.

## ✅ RULED AND SHIPPED — the Cryo families are adopted (2026-08-23, `a9f31258a`)

Superseded the "OPEN DECISION" that stood here. The maintainer ruled a **fourth** shape, better
than the three that had been costed:

> *"their regular weapons are upgraded into cryo versions: MissileAP and MissileHE become
> MissileCryo warheads and the Missile Projectile changes into the Missile Cryo projectile with
> the cryo trails and the Missile effect changes into the cryo explosion effect. The apply
> physical state is removed and the cryo physical state is applied directly from the warhead …
> This is the same for bullets, cannons, missiles, bombs, etc. — a GLOBAL change for all the RA1
> Allies weapons, not only those that already have it … even the snipers have cryo, everything
> else should too (except those that don't deal any damage, or heal, or repair)."*
> — and: *"both Demolition and Concussion become CryoBlast, because CryoBlast is
> Demolition × Concussion × Cryo."*

That is neither ADD nor FOLD: the cryo weapon is a SEPARATE weapon on a **condition-gated
armament slot**, so the upgrade SWAPS the armament instead of layering a warhead. No main warhead
is added to any weapon, so the `three_way_split` ratchet does not move — the objection that
disqualified the ADD shape never applies.

**Shipped by `a9f31258a`:** **14** new `*Cryo` weapon definitions and **21** new armament slots,
a delivery-agnostic `^Effect_Cryo` template (cryo impact with no `Projectile` and no
`ApplyPhysicalState`), and a `FlakCryo` family in `gen_weapon_template.py`. Tree-wide totals are
now 27 cryo weapons on 39 slots across 12 files — **37 of the 39 are condition-gated**; the two
that are not are FutureTech's Cryocopter and cryo turret, which are cryo by identity rather than
by upgrade and were never in this ruling's scope. The conversion map:

| non-cryo | becomes |
|---|---|
| `Bullet`, `Sniper` | `BulletCryo` |
| `CannonAP`, `CannonHE` | `CannonCryo` |
| `MissileAP`, `MissileHE` | `MissileCryo` |
| `Demolition`, `Concussion` | `CryoBlast` |
| `Flak` | `FlakCryo` |
| `Flame` | *dropped* — fire and cryo cancel; `ParaBombCryo` is `CryoBlast_Heavy` alone |

Adoption today: `BulletCryo` 8 weapons, `CryoBlast` 6, `CannonCryo` 5, `MissileCryo` 3,
`FlakCryo` 1. (Was 0 for every family when this section said "OPEN".)

### The remainder — 4 weapons, blocked on their PARENTS, not on cryo

`CryoReconRangerRecoillessGun`, `APTuskCryo`, `ChronoTuskCryo` and `155mmCryo`
(`ContentPacks/RedAlert/Allies/yaml/weapons.yaml`) still run the legacy
`^CryoMissileProjectile` + `Warhead@PhysicalStateCryo: ApplyPhysicalState` path. Each is a thin
child whose parent is a legacy MULTI-MAIN weapon — `APTusk` resolves **4** mains
(`^TankDestroyerCannon` + `^Grenade` + `^FlakWeapon` + `^MediumMissile`), `ChronoTusk` **5**. A
cryo child cannot be pointed at one `^Warhead_*Cryo` template until its parent has been reduced
to one main warhead, so these are **W24 work on the parents**, not cryo work. Converting them
also needs warhead permission (hard rule 4).

⚠ The other `PhysicalStateCryo` sites are NOT this backlog and must not be swept in:
`RedAlert/Shared` (13) is the `^CryoMissileProjectile` template itself plus a deliberate
hand-built 12-ring cryo falloff on a bomb; `RedAlert2Mod/FutureTech` (11) and `StarCraft/Protoss`
(6) belong to other factions and were never in the ruling's scope, which was RA1 Allies.

## ⭐ FROM THE DISCORD PLAYTEST THREAD (2026-08-22)

### 1. TS Nod tick tank — the complaint is real, the diagnosis pointed at the wrong upgrade

Destined: *"They are supposed to be aggravatingly tanky once deployed … They shouldn't be good
against infantry, at least not until t3 upgrade."* Plus: *"it's crazy that in this mod they
become hard to counter at radar upgrade instead of tech center upgrade."*

⛔ **Tiberium Lenses is ALREADY at T3.** Measured: `~ts_nod_techcenter`, cost 10,000 — exactly
where Shattered Paradise has it. The T2 upgrade doing the damage is a different one:

| upgrade | tier | cost | what it adds |
|---|---|--:|---|
| **Auxiliary Weapon** | **T2 `~ts_nod_radar`** | 4,000 | `TS25mmDep` — `Ground, Water, Air`, **None 200** / Flak 149 / Plate 117 |
| Tiberium Lenses | T3 `~ts_nod_techcenter` | 10,000 | swaps to lasers |

So the **Auxiliary Weapon** is both the anti-infantry AND the anti-air spike, at T2. Without it
the tick tank has **no anti-air at all** and its cannon is `Ground, Water` only. And the T3 laser
is a NERF, not a spike: `TSLaser25mmDep` drops None 200 → 80 and Heavy 49 → 45.

**Levers, with collateral measured:**

| lever | collateral |
|---|---|
| drop `Air` from `TS25mmDep` `ValidTargets` | none — per weapon |
| move Auxiliary Weapon T2 → T3 | none — per upgrade |
| cannon `^Warhead_CannonHE_Medium` → `^Warhead_CannonAP_Medium` | **1** other inherit site |
| lower the anti-infantry Versus directly | ⛔ not viable — Flak_Medium is 32 weapons, CannonHE_Medium is 73, and Versus lives only in templates |

⭐ The cannon swap is the precise answer to *"only good against tanks/buildings"*:
None **0.51x**, Wood 0.69x, Scout 0.78x — but Heavy **1.27x**, Concrete **1.72x**,
Superheavy **1.91x**. `CannonAP_Medium` has only ONE inherit site today, so adoption is cheap.

⚠ 333ggg wants a dedicated TS Nod anti-air unit; removing the tick tank's AA is gated on that.

### 2. "Very tanky" via an armour BAR — supported, and it is the R1 law

Maintainer: *"give them an additional armor plating when deployed (armor bar shows up so they
need to destroy the armor bar first) … will that cause any problems?"*

`OpenRA.Mods.Cameo/Traits/ArmorPlating.cs` is exactly this and its own [Desc] states the rule:
*"Every 'this unit is tougher now' effect in Cameo is meant to be one of these … toughness is a
visible bar rather than an invisible DamageMultiplier."* It is a `PausableConditionalTrait`, so
`RequiresCondition: deployed` is all it takes. Two properties fit the tick fantasy exactly:

- **`RampTicks: 125`** — the pool repairs NOTHING while under fire and winds up to full rate once
  left alone. It heals back between engagements, not during them.
- **`BypassDamageTypes`** — damage types that pass straight THROUGH the plating to health. Point
  it at artillery/siege types and the unit is countered by exactly what Destined says should
  counter it, by construction rather than by tuning.

⚠ Two things to get right:
1. `MaxPercentageStrength: 50` (the default) is a pool worth 50% of max HP = **1.5x** effective
   HP — LESS than the ×0.5 multiplier it replaces (2x). If "very tanky" is the target the pool
   has to be bigger; the difference is that a bar is visible and priced, a multiplier was neither.
2. Grant the plating **without** a `FullCondition` armour type. The trait's docs tell you to gate
   the body `Armor` on `EmptyCondition` when the plating carries its own type — that is for the
   armor-swap pattern and would fight §12.0g's deploy averaging. A pure pool has no Versus
   interaction and composes cleanly.

### 3. Spectator tabs ported from Combined Arms (request: Demeow Cat Hans) — ✅ SHIPPED AND VERIFIED

Shipped: **Economy Damage** (harvesters/refineries killed and lost), **Units Produced** (count +
value per unit type), **Build Order** (initial order with timestamps), **Team Army** and **Team
Earnings** graphs, per-player **selected-unit value**, and CA's five-speed replay bar with MAX
capped at the Insane timestep rather than the uncapped one. Upgrades and Promotions already
existed. An in-game encyclopedia was raised and deferred as too large.

⭐ **VERIFIED IN A LIVE REPLAY 2026-08-23** — previously this whole surface rested on boot-gating
alone, which never draws observer chrome. It has now been exercised for real:

| what | result |
|---|---|
| all 17 stats dropdown options constructed + `DisplayStats` run, with real players | no exception |
| `Earnings` / `Army` / `Team Army` / `Team Earnings` graphs left **visible and drawing** 45 s each | no exception |
| selected-unit value forced to a **2-owner** selection so the per-player grouping path runs | no exception |

⭐ **HOW TO TEST OBSERVER UI WITHOUT PLAYING A GAME** — this is the reusable part. The main menu
never loads observer chrome, but the engine will drive straight into a replay:

    engine\bin\OpenRA.exe Game.Mod=cameo Engine.EngineDir=".." ^
        Engine.ModSearchPaths="<repo>\mods,./mods" ^
        Launch.Replay="%APPDATA%\OpenRA\Replays\cameo\{DEV_VERSION}\<file>.orarep" ^
        Launch.AllowIncompatibleReplay=true

(`LaunchArguments.cs` → `BlankLoadScreen.cs`; `AllowIncompatibleReplay` skips the version prompt,
which matters because the replays predate the current rules.) **147 cameo replays already exist**
in that folder, newest 2026-08-19. ⚠ Do NOT invoke `launch-game.cmd` for this — it wraps `"%*"`
in one pair of quotes and collapses the arguments into a single token.

`CameoObserverStatsLogic` selects `statsDropDownOptions[1]` (Minimal) at load, so a plain replay
run draws exactly one panel. To exercise the rest, temporarily loop `OnClick()` over every option
in the constructor and rest on the index you want drawn — the sweep proves construction and
`DisplayStats`, resting on an index proves `Draw`. Revert the harness before committing.

⭐ **`ScrollableLineGraphWidget` ported 2026-08-23** — all four graphs now use it. Stock
`LineGraphWidget` divides the panel width by the sample count, so a long game squeezes every sample
into a couple of pixels and the graph stops being readable exactly when it gets interesting. The
scrollable one keeps the x step FIXED (`XAxisSize` samples visible) and scrolls instead,
auto-following the right edge until the viewer scrolls away from it. All four verified drawing in
the same replay. That closes the CA observer widget set — Cameo now has every one of them.

**Still unexercised:** the replay-speed buttons, the stats hotkeys and the new graph scrollbar are
only reachable by a real click or keypress, which the replay harness cannot synthesise.

### 4. Deploy-abuse bugs (reporter: ws) — UNVERIFIED, needs reproduction

- redeploying a **nexus** appears to refill its shield — a free full shield on demand.
- **hatcheries** appear to lose their upgrades when redeployed.

Both are `GrantConditionOnDeploy` state-reset bugs; neither has been reproduced against the tree
yet, so they are reports, not findings.

## ⭐ NEXT MAJOR — continuous weapon heaviness — see [`WEAPON_HEAVINESS.md`](WEAPON_HEAVINESS.md) (2026-08-22)

Resolves the 3-way-split vs between-tier-mix collision: ONE warhead template per family plus a
continuous `Heaviness` scalar, instead of a discrete level ladder. Measured: a level is already a
pure transform (`Versus = base + offset(h)`, offset 0/+4/+9, plating 0, Shield 2x; `Spread` ramps
1 : 1.5 : 2) on 39 of 40 families. Collapses ~600 future templates to ~100 and fixes the 33
between-tier weapons that currently out-damage the tier ABOVE them.

⛔ **CORRECTED 2026-08-22 — MOST OF THIS WAS ALREADY LAW AND ALREADY SHIPPED.**

`DESIGN.md` §12.0h (THE MEAN-100 LAW), §12.0c (THE SHIELD LADDER) and §12.0d (THE CLASS TILT)
already rule this design, and all three are live in `gen_weapon_template.py` (`mean_normalise`,
`class_tilt`, `TILT_RATIO 1.5`, `MEAN_TARGET 100`). §12.0d IS the bell curve, and it already
solves inversion: the tilt is applied to the VALUES and each armor is then given back the RANK it
held, so it *"can never invert"*.

The blockers previously listed here were measured with a broken hand parser that read
`PercentageVersus` instead of `Versus` — see the correction banner in
`WEAPON_HEAVINESS.md`. Re-measured through the resolver:

| previously claimed | truth |
|---|---|
| 0 of 125 obey MEAN-100 | **123 of 125** (the 2 are HAND_TUNED) |
| every family breaks the 2x-8x band | **39 of 42 in band**, median 4.17x vs a 4x target |
| a Heavy weapon self-prices at ~2x a Light one | Heavy/Light weighted-mean Versus is **1.00x** — tier does NOT price through Versus, exactly as §12.0h intends |

**What is genuinely still open:**

1. Make the class tilt **CONTINUOUS** — driven by `h` from `tier_chain` (already computed and
   stored per actor) instead of four discrete levels. This is the whole remaining idea.
2. Collapse the level templates to **one per family + a per-weapon `h`**.
3. ✅ CLEARED — the 4 orientation flips were **one real flip** (`Cryo`) plus 3 false positives from
   comparing `None` (INF ladder) against `Superheavy` (VEH); §12.0d only orders WITHIN a ladder.
   `Cryo` flipped because its blend tiebreak was decided per LEVEL on a one-point margin — the
   tiebreak is now family-wide (`1af72a3c1`). `audit_versus_profile.py` ratchet **0**.
4. ✅ CLEARED — `CannonAP` 1.81x and `Cryo` 1.97x were too flat because the 2x band floor lived
   inside `finish_blend()` (blend families only) and ran BEFORE `class_tilt` reshaped the profile.
   It is now applied to every family, after the tilt (`edd1c4597`). Ratchet **0**.
5. ✅ CLEARED — the "broken DAMAGE ladders" were never a defect. `audit_level_ladder.py` is
   retired: it enforced a damage-monotonic rule no law states, while §12.0d makes the level a
   TILT and the templates carry only a placeholder `Damage: 2000`. Replaced by
   `audit_heaviness_bell.py`; see the RULED section above.

## ▶ ACTIVE — CAMEO CONTENT INSTALLER

- [x] **Manage Content downloads:** hidden `cameo-content` installer mod,
  Cameo switched to `ContentInstallerFileSystem`, `ContentPackages:` empty so
  installation stays opt-in; disc-source outputs corrected from `Content/ca/`
  to `Content/cameo/` (PR #260).
- [ ] **Disc-source gaps surfaced by the installer going live:** `tsmusic` /
  `fsmusic` `TestFiles` are not produced by their declared disc sources
  (Firestorm writes `scores01.mix`), and `Content/cameo/{cnc/desert.mix,
  ra2/theme.mix, ra2/thememd.mix, expand/*}` are written by disc installs but
  not mounted by `mods/cameo/mod.yaml`.

## ▶ ACTIVE — VEHICLE BALANCE APPLY + BACKLOG (2026-07-31)

**Vehicle ladder DESIGN is being re-tuned** — latest table = `docs/balance/anchor_decisions_log.md`
"⚠ REVISION 2026-07-31" (PENDING maintainer "did it fix the problems?" confirm). STRUCTURAL work DONE +
committed: `^MissileVehicleTemplate` + 10 reassignments (missile-MLRS family + Nod bikes) + `EpicBuff`
removal (`43df39235`); 5 earlier templates + buff-strip (`090d3d997`).

**Queue (priority order):**
- [x] **P1 BUG — 77 live weapons deal NO flame damage] `^LightFlameWeapon` dead warhead
  RESOLVED** (2026-08-18). The `ApplyPhysicalState` → damage-scaled conversion replaced
  `^LightFlameWeapon`'s `SpreadDamage` with `AreaDamage`, which also removed the `Range: 500`
  footgun, and propagated the same fix to all `^*FlameWeapon`/`^*ChemicalWeapon` concrete
  overrides (34 YAML files). `audit_physical_state_warheads` PASS, `find_empty_warhead.py = 0`,
  boot-gated. The one `Range: 5000` / `Falloff: 100, 100` shape is unaffected.
- **[DECISION NEEDED] `effective_damage`: two open rulings.** (a) Do
  `*_ExtraDamage` chips count? `formula.spread_damage_sum` excludes them (they are paid
  for by K / charge delay); the metric includes them — both cannot be right once the
  column is priced on. (b) Derived fields now sit in the RAW-STATS-ONLY ledger,
  contradicting `BALANCE_PIPELINE.md` §2; recommendation is to split them into
  `docs/balance/derived/`. Full spec + improvement roadmap:
  [`EFFECTIVE_DAMAGE.md`](EFFECTIVE_DAMAGE.md).
- **[NEXT — needs a maintainer warhead order] Adopt the Sonic family.** `^Warhead_Sonic_*` now bakes
  the `SonicDebuff` mark (`5a14355e6`), but **nothing inherits it**, so it is inert. Candidates:
  TS GDI `TSSonicZapWeapon` / `TSSonicZapWeaponSonic` (the Disruptor — currently Tesla + Magic),
  the sonic UPGRADE variants `TSVulcanGunSonic` / `TSAssaultCannonSonic` / `TSAssaultCannonTalSonic` /
  `TSHellfireSonic` / `TSZoneHellfireSonic` / `TSBombSonic` / `TSGrenadeSonic` / `KodiakCannonSonic`
  (all still on the legacy `^SmallArms` / `^Chaingun` / `^TeslaWeapon` / `^MagicWeapon` inline
  templates = Phase B territory), and RA2 `SonicZap`. **Law:** an effect upgrade ADDS
  `^Warhead_Sonic_*` as an extra warhead — it never replaces the base damage TYPE
  (`PHYSICAL_STATE_SYSTEM.md` §3b, same shape as the cryo retrofit). Warhead changes need explicit
  permission (CLAUDE.md rule 4), so this is queued, not done.
- **[RESOLVED 2026-08-11] BUILD 3 — Sonic mark.** Global rename `CommandoDebuff → SonicDebuff`
  (29 lines / 8 yaml files; the `2100commandodebuff` asset + palette + sequences keep their names,
  `^CommandoCall`/`^CommandoCallable` untouched) and the mark baked into all three
  `^Warhead_Sonic_*` levels by `gen_weapon_template.py` (`FAMILY_CONDITION` → a zero-damage
  `Warhead@<tag>_Debuff: GrantExternalCondition`; `Duration = 2 × ReloadDelay` = 50 ticks,
  `Range = 2 × Spread` = 800/1200/1600, Enemy/Neutral only). `verify_generator_sync.py` reports drift = 0, empty-warhead 0,
  `audit_physical_state_warheads` PASS. Boot-gated, `5a14355e6`. Spec: `PHYSICAL_STATE_SYSTEM.md` §5.
- **[RESOLVED 2026-08-10, Devin] Upgraded Tesla weapons drained integrity at the same ratio as their
  un-upgraded base** — RA1 Tesla Doctrine (`PortaTesla_EMP`/`TTankZap_EMP`/`TTankZap2_EMP`/
  `TeslaZap_EMP`) and RA2 Tesla Overload (`RA2CoilBolt2`/`RA2OPCoilBolt2`/`RA2TankBolt2`/
  `RA2PortaTesla2`) variants add extra HP damage via arc fragments but stayed at the same ~150%
  integrity-drain ratio as the base weapon. Root cause + fix: see
  `docs/design/EMP_INTEGRITY_SYSTEM.md` §3c (missing `DamageTypes: Tesla` on several
  `TeslaExtraDamage` chips, and no `IntegrityScale` bump on upgraded main warheads/fragments).
  Fixed by adding `DamageTypes: Tesla` to the affected chips + `IntegrityScale: 150` to the
  upgraded variants and their fragments; generator updated to keep future templates in sync.
  Boot-gated, `87512a045`. Always-on EMP weapons (not upgrade-gated) left untouched.
- **[P0 RESOLVED 2026-08-04] Empty-warhead-type NRE on load** — two typeless `Warhead@` nodes
  (`RA2MirageGun` `Warhead@Effect:` in `mods/cameo/weapons/redalert2.yaml`,
  `TSSAPCMissiles` `Warhead@GrenadeFriendlyFire:` in `mods/cameo/weapons/tiberiansun.yaml`)
  crashed boot (`NullReferenceException` in `WeaponInfo.LoadWarheads`, abstract `Warhead` base
  instantiated). Fixed by giving each node its concrete type (`CreateEffect` / `SpreadDamage`).
  New regression audit `tools/audit/audit_empty_warheads.py` sweeps the full resolved ruleset
  (4,202 weapons incl. `^templates`): 0 remaining. Boot-gate PASSED (menu `PostWorldLoaded`,
  no new exception log). `--check-yaml` does NOT catch this class — run the audit after bulk
  warhead edits. See `docs/audit/SUMMARY.md` § "Empty warhead type NRE (2026-08-04)".
- **2026-08-04:** `sweep_areadamage.py --apply` converted 134 main-warhead `SpreadDamage`
  overrides to bare inheritance (now `AreaDamage`) across 23 `weapons.yaml` files; stripped
  12 stale `ValidRelationships: Neutral, Enemy` blocks. `extract_stats.py` refreshed
  32 `docs/balance/*.json` ledgers. Boot-gated `MenuPostProcessEffect.PostWorldLoaded`,
  no new `exception-*.log`.
- **2026-08-04:** audit quick-fix bundle — added `MinimumExposure: 0.45` to `RAAtomic` and
  `CabalMagicNuke`; corrected `MinRange` for `RA2REVENANTAA`/`RA28Inch`; renamed `DropPodExplode`
  `Warhead@1Eff` to `Warhead@Effect`; fixed `TSDPOD` render image (`tsdpod` → `tsdroppod`) and
  `sietch_creep_disabled` image (`sietch_creep_disabled` → `sietch`). Boot-gated, no new exceptions.
0. **[DONE 2026-08-01, `59c77f444`] Armor normalization** — armor is now a per-CLASS property (single
   source in `^<Class>Template`). Fixed 3 templates (MBT→Heavy, HighTechTank→Superheavy,
   LineBreaker→Superheavy) + stripped 215 flat per-actor `Armor: Type:` overrides + dropped stale Medium
   from `^CombatTank`. Verified 273/274 class vehicles resolve to class armor; boot-gated. **OPEN items
   left for later:** (a) `wc2_humans_paladin` is tagged `line_breaker` but is a vehicle inheriting the
   *infantry* `wc2_humans_knight` — suspected mis-tag, resolves Medium not Superheavy; re-classify in a
   tagging pass. (b) 4 conditional-armor actors intentionally KEPT their `Armor: RequiresCondition:`
   deploy/shield swaps and were NOT normalized: `terran_siegetank` (Heavy), `terran_matador` (Medium),
   `td_gdi_defenserig` (Superheavy — already correct), `cabal_ravager` (Plate) — decide per-unit whether
   the base-state armor should match class.
1. **[BLOCKED on maintainer confirm + `--confirm`] Apply VEHICLE stats** — once the REVISION table is
   confirmed: baselines → `apply_balance --confirm` (fit_class scales members 0.5–4.0×, verifier 2.5×) →
   self-heal Step → epic 4×HP + MonsterTank DPS→10000 → re-extract → audits + BOOT →
   commit yaml+ledger. THEN **infantry** (build the same big class table first, then apply). NOTE: the
   HP/Speed/Cost/DPS restat of the 13 baselines + per-member synthesis is still pending here; DPS/range
   are blocked on the weapon/cannon rebuild (#4).
2. **[L] Regression sweep** — review all commits since ~2026-07-24; hunt fluent/description-reference
   breakages like the RA1-Soviet upgrade regression (broke in `53fb10725`, fixed `f68a01833`). Pattern:
   renames that update Fluent keys but leave live `Buildable.Description` refs pointing at the old key.
3. **[L] Repo cleanup** — audit duplicate/overlapping python scripts (multiple balance + rename scripts)
   and docs; propose merge/generalize/delete plan. NO deletes without maintainer sign-off.
4. **[M] New weapon templates** (AFTER vehicles) — kill warhead-mixing, **HARD LIMIT 2 inherits/weapon**
   (special >2 only if justified, bar TBD); then weapon-class pipeline + unit↔weapon binding. Maintainer
   names them + I propose. See +.
   DESIGNED + SIGNED OFF 2026-08-01/02 (survives /compact via docs+memory): two-level ordering law
   (ARMOR_SYSTEM "PROFILE construction" + `cameo-weapon-ordering-law`); 4-dimensional differentiation
   model + flat/% orthogonal axis + Super tier + AoE-FF rule + CORRECTED %-warhead
   (WEAPON_TYPE_SYSTEM §13 + `cameo-weapon-differentiation`). `gen_weapon_template.py` rebuilt —
   **55 templates**, unified `^<Family>_<Level>` naming, modes sloped/FLAT(Sonic)/PCT(Magic):
   Bullet/CannonAP/CannonHE/MissileAP/HE/AA/Flak/Laser/Prism/Flame/Chemical/Melee/Arrow/Demolition/
   Concussion/Sonic (L/M/H) + Railgun/Tesla (Heavy) + TeslaCharged/Nuclear (Super, WC1.5) +
   Magic (%-equalizer, ground-only). ✅ **SPLICED + BOOT-GATED 2026-08-02**: the 55 templates now live
   ABOVE the `DO NOT INHERIT` divider in `weapons.yaml` (replacing the 6 stale provisional
   `^*Demolition`/`^*Concussion`, which carried the old `Wood>Concrete>Steel` building bug); the 55
   `^<Family>_<Level>` WeaponClass scalars are recorded in `docs/balance/weapon_classes.yaml`. Verified:
   key-set diff = only 6 provisional removed / 55 added, rest byte-identical; all weapon audits green;
   game reached main menu (`PostWorldLoaded`, no new exception log). Old bespoke templates
   (`^Grenade`/`^ShrapnelWeapon`/`^HeavyBomb`/`^SmallArms`/etc.) intentionally KEPT until repoint.
   **GENERATOR RECONCILED 2026-08-04** (A1 of BALANCE_MEGAPLAN) — `gen_weapon_template.py` now emits
   `^Warhead_<Family>_<Level>` naming + `AreaDamage` main + universal baked FF (`Ally, Neutral, Enemy` +
   `FriendlyFireDamage/Spread 50`) + `_Percentage` suffix, matching the swept/converted templates in
   `weapons.yaml`. Regenerating is now a no-op diff against the file. Fixed `AOE_FAMILIES` `NameError`
   (leftover from removed `aoe` param). Spot-verified Bullet + Tesla templates match byte-for-byte.
   **REPOINT REFRAMED AS THE FULL 3-WAY SPLIT (#4b), maintainer 2026-08-02.** A bare reparent onto the
   warhead-only families is UNSAFE: survey found 392/437 single-inherit weapons override a warhead by the
   OLD key (`Warhead@SmallArms:` → orphaned/double-fire) + 253 rely on the old template's bundled FX (go
   silent). Root cause: old templates are FULL-STACK; the 55 new families are warhead-only BY DESIGN. So
   the repoint = build the projectile + effect layers first, then retrofit weapons to the 4-inherit model.
   Progress (docs: `WEAPON_3WAY_SPLIT.md`):
   - ✅ **Layer 2 (PROJECTILE) + Layer 3 (EFFECT) libraries BUILT + SPLICED + BOOT-GATED 2026-08-02** —
     `gen_projectiles.py` (24 `^Projectile<Family>_<Level>`) + `gen_effects.py` (27 `^Effect<Family>_<Level>`),
     extracted verbatim from the 30 old full-stack templates, additive/0-usage above the divider. Boot OK.
   - ✅ **Warhead FF twins BUILT + BOOT-GATED 2026-08-02** (`956cf1ecb`) — 19 FriendlyFire twins for the
     7 AoE families (Demolition/Concussion/Flame/Chemical/Nuclear/Sonic/Melee). ExtraDamage twin (energy)
     stays per-weapon (bespoke +vs-shield). All 3 layers now exist (55 wh + 24 proj + 27 fx).
   - **RETROFIT Phase A (SmallArms/Chaingun pilot) — historical 2026-08-02 record; its
     2000-grid/FirepowerMultiplier tuning rule is superseded by the current 100-grid/no-FP law.** Repoint weapons to
     `Inherits@wh + @proj + @fx`, renaming `Warhead@<Old>` keys → new key while **PRESERVING each
     weapon's existing on-grid `Damage` verbatim** (damage law = 2000-grid, all mains identical, fine-tune
     ONLY via one unconditional actor `FirepowerMultiplier` — DESIGN.md §nice-number). Handle INTERMEDIATE
     templates (`^RA2Chaingun`→`^Chaingun`). Pilot = **SmallArms→Bullet_Light + Chaingun→Bullet_Medium**,
     boot-gate, then roll out; energy families in a small ExtraDamage-aware pass; **609 MIXED = Phase B**
     kill-mixing (≤2 warheads, honor the exception allow-list — Dune 3-cannon, Siege Tank/Engine).
     **Bullet_Heavy → the Pulverizer mecha** (Asian Alliance, currently mixed → Phase B). Then delete the
     30 orphaned old templates + their `weapon_classes.yaml` rows. This unblocks the vehicle DPS restat (#1).
   - **RETROFIT mechanical clusters 2026-08-05/07** — `HeavyBomb+ShrapnelWeapon`
     (`Demolition_Heavy+Concussion_Medium`), `LightMissile+MediumMissile` (`MissileHE_Light+MissileHE_Medium`),
     `Grenade+HeavyMissile` (`Concussion_Light+MissileHE_Heavy`), `ShrapnelWeapon+HeavyCannon`
     (`Concussion_Medium+CannonHE_Heavy`), `MediumCannon+HeavyCannon`
     (`CannonHE_Medium+CannonHE_Heavy`), `Grenade+HeavyBomb`
     (`Demolition_Light+Demolition_Heavy`), `Grenade+ShrapnelWeapon`
     (`Demolition_Light+Concussion_Medium`), `MediumCannon+TankDestroyerCannon`
     (`CannonHE_Medium+CannonAP_Light`), `HeavyMissile+ShrapnelWeapon`
     (`MissileHE_Heavy+Concussion_Medium`), `Chaingun+FlakWeapon`
     (`Bullet_Medium+Flak_Medium`), `SmallArms+FlakWeapon`
     (`Bullet_Light+Flak_Medium`), `FlakWeapon+MediumMissile`
     (`Flak_Medium+MissileHE_Medium`) plus the generic sweeps of
     effect-free dual pairs (13 + 3 + 1 = 17 weapons) converted and
     boot-gated. Total dual-inherit live weapons reduced by ~82.
   - **Single-inherit sweep 2026-08-07:** 26 pure single-inherit effect-free
     weapons (no `Inherits@2`/addons) across 15 files repointed to the 3-way
     `wh/proj/fx` model. A broader attempt that included multi-addon `Steel`/
     `RA2` weapons produced 46 empty-type warheads and was reverted before
     boot. Strict single-inherit-only filter passed `find_empty_warhead.py = 0`.
   - **Effect-heavy clusters (flame/chemical/sonic/energy) are now partially unblocked.**
     The `Grenade+LightFlameWeapon` (`Demolition_Light+Flame_Light`) test cluster
     converted cleanly by keeping local `PhysicalState` overrides minimal
     (`Amount` only) and dropping `FriendlyFire` nodes that the new `^Warhead_*`
     templates already provide. The remaining effect-heavy families can use the
     same pattern once the converter is generalized.
     `EMP`/ExtraDamage-aware converter is built — see `docs/LESSONS_LEARNED.md` § "Effect-warhead merge safety".
     **Phase A progress (2026-08-02):** `tools/archive/retrofit_v3.py` repointed ~130 single-inherit
     weapons from `^SmallArms`→`^Bullet_Light`/`^ProjectileBullet_Light`/`^EffectBullet_Light` and
     `^Chaingun`→`^Bullet_Medium`/`^ProjectileBullet_Medium`/`^EffectBullet_Medium`, including intermediate
     templates (`^RA2SmallArms`, `^RA2Chaingun`, `^RA2MG`, `^TSMG`, `^SteelChaingun`). Warhead override
     keys renamed (`Warhead@SmallArms`→`Warhead@Bullet_Light`, `Warhead@Chaingun`→`Warhead@Bullet_Medium`,
     etc.). Dual-inherit weapons skipped (Phase B). `Report: gun8.aud` added to `^Bullet_Light` and
     `^Bullet_Medium` to preserve default sound from old templates. `check-yaml` verified: no new
     retrofit-related errors. **REMAINING:** boot-gate, then roll out to remaining weapon families.
     - **2026-08-04:** `tools/balance/retrofit_weapon_family.py --old LaserWeapon` repointed 34
       single-inherit weapons across 14 files to `^Warhead_Laser_Heavy`/`^Projectile_Laser_Heavy`/
       `^Effect_Laser_Heavy`; boot-gated with no new exception log.
     - **2026-08-04:** `--old TeslaWeapon,TeslaChargedWeapon,RailgunWeapon` repointed 85
       single-inherit weapons across 27 files to `^Warhead_Tesla_Heavy`, `^Warhead_TeslaCharged_Super`,
       and `^Warhead_Railgun_Heavy` (plus matching projectile/effect layers); boot-gated clean.
     - **2026-08-08:** Sniper 3-way family built + `SniperWeapon` repointed 21 single-inherit
       weapons across 16 files to `^Warhead_Sniper_Light`/`^Projectile_Sniper_Light`/`^Effect_Sniper_Light`;
       sweep + boot-gated clean. Remaining 6 mixed Sniper children + all other old families are
       Phase B (maintainer sign-off per `docs/design/WEAPON_3WAY_SPLIT.md` §PHASE 3).
   - **[FUTURE, reason later] SPREAD REBALANCE** (maintainer 2026-08-02) — spreads must be UNIQUE per weapon
     but balanced so **`Damage × Spread ≈ constant`** (inverse trade); a small spread MUST carry a unique
     extra effect (energy's +vs-shield chip is the model). Folded into the restat; do NOT hand-tune yet.
4b. **[L, FUTURE] 3-WAY weapon-template split** (maintainer 2026-08-02) — decompose every weapon into
   THREE independent composable templates: (1) WARHEAD/weapon-class (Versus+damage — the §12 families
   already ARE this layer, projectile/effect-agnostic by design), (2) PROJECTILE (speed/homing — so a
   fast projectile can carry a heavy warhead), (3) EFFECTS (impact/muzzle/trail/sound). MASSIVE:
   retrofitting thousands of inline weapons + the 2-inherit rule must widen to 3 (warhead+projectile+
   effects). Best folded INTO the repoint pass (#4) rather than a separate sweep, since that already
   touches every weapon. Not quick — deferred.
5. **Weapons-hygiene batch** — folds into #4 (also fix the duplicate `227mm` weapon def in
   `weapons/tiberiandawn.yaml` vs `weapons/missiles.yaml`).
6. **[L] Actor-to-actor inheritance audit (DEFERRED, maintainer 2026-07-31)** — prefer `^Templates`
   over `Inherits: <actor>` for ContentPack self-containment. **199 existing instances reviewed &
   deemed fine/grandfathered** (116 = RA2 civ-terrain `ra2ct*`; ~83 variant/husk: `*mkii`←base,
   `ifv_*`←ifv, `E1`←minigunner, badger family, WC2 towers). NOT a must-fix — do it as its own pass
   later; resolution = inline (cross-pack/one-off) or hoist to `^Template` (same-pack). Memory:
. Audit cmd in the memory. Don't stop pipeline work for it.

**ENGINE workflow.** ⚠ **CORRECTED 2026-08-15 — `engine/` is NOT a submodule of this repo.**
Verified: no `.gitmodules`, no `engine/.git`, `.gitignore` lists `engine`/`engine*`, and
`git ls-files engine` returns **0 tracked files**. `git` run from inside `engine/` silently
operates on the PARENT repo, which is what made it look like a submodule on `master`.
**Editing `engine/**` from this repo produces work that cannot be committed and is wiped by
the next `make all`.** (The earlier wording here — "submodule … MIRROR changes both ways" —
cost a session's worth of planning before anyone checked.)

The engine is a **SEPARATE clone** of `https://github.com/cameo-mod/OpenRA`, branch
`cameo-engine`. The binding, step-by-step procedure is
**`docs/LESSONS_LEARNED.md` → "The canonical engine update pipeline"**: edit + push there →
`git rev-parse cameo-engine` for the full 40-char hash → `ENGINE_VERSION` in **`mod.config`**
(not `mod.yaml`) → `make.cmd all` → verify `engine/VERSION` and recreate `engine/glsl/`
shaders → boot-gate → commit `mod.config`. Also in `CLAUDE.md` and the SessionStart hook.

⭐ **Check for a mod-side SHADOW first** — it avoids the whole round trip.
`ObjectCreator.FindType` returns the first assembly in `mod.yaml`'s `Assemblies` list holding
the type name, and that order is AS, CA, **Cameo**, Cnc, D2k, Common, so an
`OpenRA.Mods.Cameo` class of the same name replaces the engine's with **zero yaml changes**.
Precedent: `ColorPickerColorShift`, `PlayerColorShift`, and `SelectionDecorations`
(`57685c3a3`). Prove it with a Cameo-only field — `--docs` lists both types and proves nothing.
Memory: `cameo-engine-submodule`.

---

## ❓ OPEN DESIGN — Schwarzer Mond team upgrade + faction lore pass (2026-08-15)

Two maintainer questions raised while reworking the SM upgrades (`d58cd8603`).

### 1. Does Moon Propaganda become SM's team upgrade?

Every faction is eventually meant to have one; SM has none. The maintainer's own
difficulty is real: *"it's very hard to make something unique that is also
teamwide."*

**~~Recommendation: split Moon Propaganda, fanaticism goes team-wide.~~ REJECTED
by the maintainer, 2026-08-15 — and rightly:**

> *"Schwarzer Mond is more high tech and more about vehicles and aircraft than
> infantry so I think the team upgrade should also reflect that a bit."*

Fanaticism is an INFANTRY-morale effect on a faction that is not infantry-focused.
It fits the Asian Alliance — whose Banzai upgrade already **is** that effect,
faction-only — or the Naxis. The mistake was reasoning from an available mechanic
instead of from faction identity; that is now a binding rule in
[`DESIGN.md` §6](../DESIGN.md), together with the measured
**team ≈ half of faction** magnitude law.

**Moon Propaganda therefore STAYS a normal faction upgrade** (fanaticism +
defection, shipped in `d58cd8603`). SM's team upgrade is a SEPARATE, still
unbuilt upgrade, and it must be **high-tech, vehicles and aircraft**.

**Candidates (maintainer's pick outstanding):**

| # | upgrade | effect | why it fits |
|---|---|---|---|
| **A** | **Anti-Gravity Plating** *(recommended)* | allied **vehicles + aircraft** get an `ArmorPlating` bar worth **10% of health** | SM's lunar alloys and anti-grav tech, exactly HALF of SM's own Lunar Alloys (20%) so the team-is-weaker law is visible in the number; reuses the additive plating pool, so an SM ally already carrying plating sees ONE bigger bar rather than a second one |
| **B** | **Helium-3 Distribution** | allied vehicles + aircraft **+10% speed/turn**, allied power plants **+15% output** | SM already mines Helium-3 for fusion reactors and propulsion; sharing the fuel IS what a team upgrade is, and it is literally half of SM's own Helium-3 (+25% speed, +50% power) |
| **C** | **Die Glocke Resonance** | allied vehicles + aircraft **resist disabling** (shorter EMP/disable) | the most distinct option — every existing team upgrade in the tree is a ± multiplier, this one is utility; needs a check of what EMP/disable traits support first |

**A** is the pick: it is a NEW effect for allies rather than a diluted copy of an
SM upgrade, it produces a visible BAR instead of another invisible percentage
(the maintainer's standing complaint about generic upgrades), and it demonstrates
the additive one-pool law. **B** expresses the weaker-shared-version law most
legibly but is a stat multiplier. **C** is the most interesting and the least
scoped.

**Cost of building, once picked:** `^TeamUpgradeTemplate` (cost 10000) + an
`up_<name>_proxy_actor.schwarzermond` + an effects template gated on the proxy's
condition, inherited by allied vehicles/aircraft via `^GlobalBuffs`. No new C#
for A or B.

### 2. Magic-the-Gathering-style lore for every unit and upgrade

Maintainer, 2026-08-15: *"I want each unit and upgrade to have their own unique
lore behind them, like the Magic the Gathering cards … But yeah that's more like
a thing for the future maybe?"* — recorded as a FUTURE pass, not queued now.

Shape when it happens: descriptions already carry a mechanical line plus a
flavour line (see `schwarzermond_upgrade_cryptofascism`, whose flavour text is
the MoonCoin rug-pull). That two-line split IS the MTG card layout — rules text
then italic flavour — so the CONTENT pass is a sweep over existing
`Description:` fields rather than a new system.

**ESTIMATE (2026-08-15), split into the cheap half and the expensive half:**

*Styling mechanism — small, and doable MOD-SIDE.* Checked:
- **No inline markup exists today.** Zero `.ftl` files use colour/style tags, and
  OpenRA's `LabelWidget` has no per-span styling — colour is a per-WIDGET
  property. So "italic flavour" cannot be a tag inside one string; the tooltip
  has to render **two labels**, one per style.
- **No italic font is registered.** `mod.yaml` `Fonts:` declares Regular and Bold
  variants of JudouSansHans only. Italics need an italic TTF added (or the
  flavour text distinguished by COLOUR/dimming instead, which costs nothing).
- **The tooltip logic can be shadowed** rather than forked into the engine:
  chrome `Logic:` classes resolve through `ObjectCreator` exactly like traits, so
  a Cameo `ProductionTooltipLogic` overrides Common's with no engine round trip
  (same trick as `SelectionDecorations`, `57685c3a3`). This matters because the
  widget lives in `engine/`, which **cannot be committed from this repo**.
- Data model: add a second fluent key per actor (`.flavor` next to
  `.description`) rather than a separator convention inside one string, so
  translators and audits can treat them independently.

*Content pass — this is the real cost.* **2021 `Description:` fields** in
ContentPacks alone: **1159 already fluent keys**, **853 still inline prose**.
Flavour text is a new line for each, and it is writing, not scripting — there is
no way to generate it. Sequence it AFTER the balance program: the rules line
states final numbers, so writing it earlier means writing it twice. The 853
inline ones should migrate to `.ftl` first (DESIGN.md §7 already requires that),
which makes the flavour pass a pure `.ftl` job checked by `audit_display_text` +
`audit_fluent`.

**Recommendation:** build the styling mechanism whenever it is wanted (it is
self-contained and improves every existing description immediately), but do the
flavour-writing in faction-sized batches after balance settles.

## ★ MAJOR PROGRAM (2026-07-25): mod-synthesis balance overhaul — see [`BALANCE_SYNTHESIS.md`](BALANCE_SYNTHESIS.md)

Big multi-session effort to fix Cameo's extreme-value balance by synthesizing extracted mods into
class anchors. Full plan + the new binding laws (spread-width, baseline-only, class↔weapon binding,
AA-gating, rock-paper-scissors) are captured in `BALANCE_SYNTHESIS.md` + `ORIGINAL_UNIT_STATS.md`
(reference map + extracted data) + memory. Work items, in order:
1. **Extract remaining sources** — CnC Reloaded (`Tools/Map Editor/rulesmd.ini`), Romanov's Vengeance
   (`mods/rv/rules`+`weapons`), Dune games, Outpost 2. **Extend tooling to weapons/warheads/versus**
   (currently HP/Cost/Speed only) — the full spreadsheet stat set.
2. **Normalized full reference tables** per mod per faction (÷ each mod's basic rifleman).
3. **Synthesize per-class/faction targets** → **re-derive class anchors** (tightened spread band).
4. **Weapon/warhead rework** — class↔weapon binding matrix, grow the warhead library, remove wild
   mixes (audit `weapons.yaml` vs mod versus-values + `ARMOR_SYSTEM.md`).
5. **AA class-gating** (§9) + **bake out per-class multipliers** into baselines (§7).
6. **Promote the §6–§10 laws into `DESIGN.md`** (binding). Then rerun the formula per class → apply.

## Active documentation maintenance

- [x] **Documentation architecture quick wins** — owner: Cascade. Added `docs/README.md`; reduced `README.md` to orientation and canonical links; kept the complete startup, evidence, incident, and commit-gate protocol in `AGENT_WORKSPACE.md`. Validation: checked links in the entry documents and ran `git diff --check`.
- [x] **Documentation architecture continuation** — owner: Cascade. De-mixed `MEGAPLAN.md` into a short rebalance index and moved the Dynamic Campaign vision into non-binding `VISION.md`; Formula V2, balance-pipeline, and ARMOR_SYSTEM remain canonical linked sources. Excludes the ROADMAP history split and Formula V2 roster-log migration. Validation: internal-link check and `git diff --check`.

## Code health program

Five recurring tracks run with a 7-day grace period. Each track's *script* is a
ratchet that blocks `run_all.sh` on a regression. Being merely **overdue** does
NOT block the per-commit suite (it is reported loudly; `run_all.sh` passes
`--warn-only`) — enforce the calendar with the strict
`python tools/audit/audit_periodic_freshness.py` in a scheduled run. A **BROKEN**
entry (registered script or evidence file missing) blocks unconditionally.
Registry and procedures: [`docs/audit/PERIODIC.md`](../audit/PERIODIC.md)
and [`docs/audit/periodic.json`](../audit/periodic.json).

- **Code duplication** — `python tools/audit/audit_code_duplication.py`; every 30 days; baseline C1/C2/C3: **10/14/10**.
- **Test coverage** — `python tools/audit/audit_test_coverage.py`; every 30 days; baseline T1/T2/T3: **24/54/221**.
- **Recent-changes review** — `python tools/audit/audit_recent_changes.py --days 30`; every 14 days; baseline R1/R2/R3/R4: **145/2/502/15**.
- **Error handling** — `python tools/audit/audit_error_handling.py`; every 30 days; baseline E1/E2/E3/E4: **2/30/90/9**.
- **Security scan** — `python tools/audit/audit_security.py`; every 14 days; baseline S1–S6: **0/0/0/0/0/0**.

Follow-up: establish measured ratchet baselines for `audit_armament_naming` and
`audit_burst_delays`, then wire them into `run_all.sh`; they are currently
exempt from the R2 check.

## Balance — universal class-formula program (2026-07-22, ACTIVE)

**Goal:** ONE balance formula for every class; a class is re-weighted only
by dropping in a **baseline actor** + **verifier actor** (the two calibrate
the weights). `UnitClass` scalar is deprecated → set to 1.0 once all anchors
are picked, then delete. Order: infantry → tanks/vehicles → aircraft →
defenses → naval. All DPS/cost below are PROVISIONAL (maintainer tunes
in-game); actors + stats + structure are LOCKED. Full anchor store:
`docs/balance/class_anchors.json` (14 classes as of 2026-07-22).

**Laws locked this session (bake into pre-flight + audits so they can't be skipped):**
- **SUM law** — effective damage = Σ offensive SpreadDamage warheads (excl.
  `*ExtraDamage`/`*Percentage`/`*FriendlyFire`), never MAX. Canonical reducer
  `formula.spread_damage_sum` (done: propose_class_rebalance/fit_class/update_ranges route through it).
- **DPS tuning** — identical main-warhead `Damage` on the 100 grid, with
  reload/range used for the remaining fit. Unconditional actor
  `FirepowerMultiplier` is retired as a fine-tuning knob.
- **Baseline @ band middle**; **verifier ≡ baseline on range+speed, exactly
  2×HP / 2×DPS / 2.5×cost**; same tech tier as baseline so it cancels.
- **WC/StarCraft unit costs = multiples of 20** (power = Cost/20).
- **RevealsShroud per class = baseline range, floored to 5000** for
  scout/closecombat/melee (helps snipers scout). Apply to each `^…Template`.
- **Melee range IS priced** (FORMULA_V2 §6b corrected).
- [x] **Physical-state delivery surcharge (E2)** — 1.25× ceiling scaled by delivery
  weight; computed by `physical_state_price.actor_multipliers()`, stored in the
  derived sidecar (`docs/balance/derived/*.json`), and applied by `fit_class.price_unit()`
  after the charge-up discount. Flame/chemical units now pay the surcharge; cryo and
  non-state units price at 1.0.

**To do (in order):**
- [x] **BUILDABILITY LAW** (maintainer 2026-07-22): a unit is balance-relevant
  ONLY if buildable — has a `Buildable` trait with a non-empty `Queue` and NO
  disabling prereq (`~disabled`/`~wip`/…). Non-buildable units (legacy tokens
  E1/E3 = no Queue; spawn/veterancy `_sp`/`_r4` = no Buildable; ~disabled units;
  cost-10 XP-bag civilians) are EXCLUDED from balancing AND every audit — their
  cost is just an XP-on-kill value. DONE: `extract_stats._is_balance_buildable`
  writes `u["buildable"]`; `propose_class_rebalance` skips non-buildable (keeps
  anchor/verifier). 23/280 infantry excluded. STILL TODO: apply the same filter
  to the standalone audits (uniqueness, outliers, stat_formulas, etc.).
- [x] **Infantry membership auto-classified** (2026-07-22, "auto-classify + review"):
  membership = the `^…InfantryTemplate` each unit inherits (design.subtype),
  mapped by `subtype_to_anchor` (now all 14 classes), + explicit
  `design.class_anchor` overrides for pollutants. 257 buildable infantry classed:
  melee 41, heavy 39, rocket 35, support 34, scout 24, commando 24, SF 16,
  pure_sniper 16, grenadier 10, flying 7, closecombat 4, heavy_sniper 2. See
  `docs/history/balance/membership_review.md`. Reclassified: engineers/medics/spies/
  casters→support; dogs→melee; dragunov+virus→heavy_sniper; futuretech droids
  (shotgun→closecombat, cannon→heavy, missile→rocket, scout→scout, repair→support);
  zerg_ultralisk/wc2 knight+ogre→melee (were on the tank template); marauder→heavy.
  OPEN CALLS: (a) terran_marine/zerg_hydralisk/terran_madcap fell to rocket_trooper
  via their AntiTankAntiAir subtype — confirm or redirect; (b) terran_ghost/specter
  still SF (subtype SniperInfantry) — SF or sniper?; (c) grenadier VERIFIER
  ra1_soviets_molotovconscript is ~disabled (non-buildable) — pick a buildable
  verifier or confirm it's upgrade-reachable; (d) 5 buildable vehicles sit in the
  infantry section (leech/bmwbike/antitankcannon/noidharvester/engineeringarmor) —
  handle in the vehicle pass.
- [x] **Computed tech-tier from prerequisite building chains** (done): new
  `tools/balance/tier_chain.py` resolves each buildable actor's chain cost `C`
  using only its own ContentPack leaf + the same game's Shared pack, computes
  `f(C) = 1 / (1 + (C - 9500) / 8250)`, and writes `tier_chain_cost` +
  `tier_multiplier` to the derived sidecar. Manual `design.tech_tier` values are
  preserved as overrides.
- [ ] Build `tools/balance/rebalance_classes.py` dispatcher: SUM price →
  100-grid warheads → range-solve to band (mult-of-10) →
  uniqueness within broad TYPE → Δ (goal ≤1). Consolidates the scout/
  closecombat/SF one-offs (LESSONS §172-176).
- [x] **Fix uniqueness in code** (done 2026-07-22, commit pending):
  `propose_class_rebalance.resolve_dps_uniqueness` now keys on effective
  damage-per-shot at the baseline actor state; the report checks the 5 raw stats — HP, Speed,
  Range, RAW ReloadDelay, effective-damage-per-shot — with damage-per-shot and
  reload as SEPARATE dimensions (reload dupes flagged, never auto-nudged). STILL
  TODO: apply the same 5-stat metric to the standalone uniqueness AUDIT.
- [x] **Speed-step in code** (done 2026-07-22, refined): step is PER-UNIT, not
  per-class — 1 for foot infantry (turn instantly), 5 for vehicle-turn-rate units
  (turn = speed/5, snapped to a multiple of 5). Detected by a defined
  `Mobile.TurnSpeed` (`row["vehicle_turnrate"]`): catches actual vehicles AND the
  Cabal cyborgs / FutureTech droids, while foot units (incl. zerglings, chem
  locomotor but no TurnSpeed) stay step-1. Foot infantry also get a Speed±1
  fine-tune as a Δ lever (maintainer 2026-07-22). `VEHICLE_TYPE_CLASSES` still
  forces the class default where every member is a vehicle (mbt).
- [x] Between-cell movement responsiveness: `^DefaultInfantry` opts in; infantry
  with a defined `Mobile.TurnSpeed` opt out through `^VehicleTurnRateInfantry`,
  preserving the documented vehicle-turn-rate marker.
- [x] Apply **closecombat ReloadDelay 75→70** (anchor DPS 250 / verifier 500) —
  done as part of the 4-anchor restat below.
- [x] Fix the 4 anchor units to grid (shotgunner/fanatic 4000→2000×2, reload
  75→70; japan 12000→4000×3; lunar 24000→8000×3) via ledger→apply_balance→boot
  gate. Verified Δ0: anchors price to cost0, verifiers to 2.5×cost0. (2026-07-22)
- [x] **Tech-tier is applied RELATIVE to the anchor's tier** (done 2026-08-17):
  `propose_class_rebalance.py`, `build_workbook.py`, and `check_band.py` now pass
  `f(C_unit) / f(C_anchor)` to `class_baseline_price`; `fit_class.py` and the
  `class_anchor_price` path still use the absolute multiplier because the anchor
  cancels. The `TechTier` workbook column is absolute so a maintainer override is
  readable; the class-baseline formulas divide by the anchor's absolute tier.
- [~] Reconvert the ~20 MAX-era-hot closecombat+SF members (each warhead was
  set = intended total → 2–3× hot under SUM). BLOCKED on membership cleanup
  first — the current subtype rosters pull in snipers/casters/spies/core-combat
  units (scout: spies+zerg_defiler; SF: dragunov sniper, terran_*, zerg_hydralisk).
  PROGRESS 2026-07-22: **closecombat 3/4 at Δ≤1** — shotgunner/fanatic anchors
  (Δ0), naxis_sssoldier (range 4500, FP 95%, Δ−0.8). `alien.nax` DEFERRED (Δ+67):
  its weapon `NaxiAlienPistol` is defined in shared `mods/cameo/weapons/redalert2mod.yaml`
  and inherited cross-pack (Naxis + SchwarzerMond) — editing it would leak.
- [ ] **Shared-weapon ownership pass** (systemic, found 2026-07-22): many members
  share a weapon via cross-pack `Inherits:` (e.g. NaxiAlienPistol → Naxis+SchwarzerMond).
  Per-unit balance edits leak. Before converting such a unit, FORK it a per-unit
  weapon (+ its `…E`/elite + garrison variants) in its own pack, repoint the
  actor, then balance the fork. Aligns with the self-contained-pack mission goal.
  Detect them: `apply_balance` writing to a weapon whose block lives in a shared
  file / is inherited elsewhere.
- [ ] **PIPELINE LAW — never hand-calc DPS; use the tools** (learned 2026-07-22):
  effective DPS depends on ReloadDelay, Burst AND **BurstDelays** (+ FirepowerMultiplier).
  A hand calc that skipped BurstDelays mis-set naxis_sssoldier (prescribed FP 88
  instead of ~95). Always derive base DPS via `propose_class_rebalance.unit_dps`
  (or armament_dps), which reads every knob; then solve FP for Δ0. Validate the
  APPLIED state by pricing the ledger stats directly — the proposal RE-SOLVES
  range/FP and is a generator, not a validator.
- [ ] Restat + reconvert each infantry class to its anchor (class_anchors.json).
- [ ] NEW BUILDING: RA1 Soviets Tier-4 dummy (forward-command-center sprite,
  placeholder `ra1_soviets_experimentaltechcenter`) unlocking the heavy-infantry
  shocktrooper; ladder T3=tech center, T4=experimental. (Needs a real name.)
- [x] Rocket troopers: raise td_nod + td_gdi to 300 (weak at 200). DONE
  2026-07-30: changed ^E3 template Cost from 200 to 300 in
  ContentPacks/TiberianDawn/Shared/yaml/templates.yaml. RA1 rocket
  soldiers already at 300 via ^RA1AlliesAlliedRocketSoldier.
- [ ] Heavy-sniper verifier warhead recipe (yuri_virus/ts_nod_toxintrooper):
  sniper+chaingun+railgun templates, equal warheads; virus upgrade 1 = +light
  chemical, upgrade 2 = +medium chemical; spawned gas = special K+0.25 (1.25×).
- [ ] **Catch-all-specials audit** (maintainer flagged): detect EVERY special
  reliably — granted-condition effects, FireShrapnel-spawned warheads/gas,
  charge-delay/frontal-facing negatives — so K is never under/over-counted.
- [ ] Then vehicle anchor proposal (MBT live; light tank / heavy / tank
  destroyer / artillery / AA / scout / battlefortress / APC).
- [ ] DEFERRED to elite-weapon audit: elite weapon range = base + 1000
  (naxis elite is 6500, should be 6000).
- [ ] **Class descriptions rework** (maintainer 2026-07-22): every unit CLASS
  needs its own fluent `.description` (only a few exist so far —
  scout/antitank/mbt/commando + the 4 added today: heavy_sniper/rocket_trooper/
  archer/support). Descriptions live in `mods/cameo/fluent/rules/en.ftl`
  (Buildable.Description is a `[FluentReference]` key, NEVER inline text; use
  real line breaks, never `\n`). ALSO: the "Strong vs / Weak vs" matchup lines
  belong at the END of the description, after the flavour text — needs a design
  pass on wording/order. Support-type units get NO Strong/Weak line.
- [x] **Naming: dots → underscores** (maintainer 2026-07-22 — actor/template
  names must ALWAYS use `_`, NEVER `.`): renamed `^upgrade.template` → `^upgrade_template`,
  `^researched_upgrade.template` → `^researched_upgrade_template`, `^promotion_upgrade.template`
  → `^promotion_upgrade_template`, `^default.angry_mob` → `^default_angry_mob`,
  `^default.alien_mob` → `^default_alien_mob` mod-wide (76 files, 1183 replacements,
  commit `7f704c981`). `unit_upgrade` already fixed 2026-07-22. No dotted husk templates
  remain (all ground husks removed in prior commit). Boot-gate clean.
- [x] **Engine 910e50de → 2cfb751694 → ba153be0c6 → 1f71ccde9 migration** — engine pin
  updated to `1f71ccde90c1194fe908702f2e915807b2f0f3fd` (2026-07-31, fixes
  `InvalidOperationException` crash in `ClassicProductionQueueProperties` when
  an actor with no production queue is produced via Lua). Previous pin
  `ba153be0c6` (2026-07-30, fixes cargo pips showing 0). The stricter parser
  issues from the earlier `910e50de` bump were fixed 2026-07-22 (4 template
  Description indents → fluent keys, `unit_upgrade_template` rename). Current
  engine is clean; master boots. If a future engine bump surfaces new parser
  rejections, fix as found (master must always boot).

## P0 — Crashes (always first)

- [x] **P0 CRASH: InvalidOperationException in ClassicProductionQueueProperties**
  (2026-07-31, fixed): `System.InvalidOperationException: Sequence contains no
  elements` at `ProductionProperties.cs:line 226` —
  `GlobalProductionHandler` calls `.First()` on `BuildableInfo.Queue`,
  crashing when an actor with no production queue is produced (e.g. via
  Lua `Actor.Create` on survival maps). Engine fix in
  `cameo-engine` commit `1f71ccde90`: replaced `.First()` with
  `.FirstOrDefault()` + null guard in `GlobalProductionHandler`,
  `Build()`, and `IsProducing()`. `mod.config` updated to
  `1f71ccde90c1194fe908702f2e915807b2f0f3fd`. Boot-gate passed (menu
  reached, 0 new exceptions).
- [x] **P0 CRASH: InvalidOperationException in InfectCA.OnEnterComplete**
  (2026-08-02, map Terra Cotta): `Attempted to get trait from destroyed
  object (ra2dron 521 (not in world))` at `TraitDictionary.CheckDestroyed`
  called from `World.Remove` → `InfectCA.OnEnterComplete` frame-end task.
  The infector actor (`self`) was already disposed by the time the
  frame-end task ran, so `w.Remove(self)` crashed when iterating
  `INotifyRemovedFromWorld` traits. Fix: added `self.IsDead` guard before
  `w.Remove(self)` in `OpenRA.Mods.Cameo/Activities/InfectCA.cs` — if
  dead, revoke `BeingInfectedCondition` on target and return early.

- [x] Voice-set rename crashes (`1616a26d2`); pink menu (`e956d2280`);
  boot crashes crab-junk/shadowteam/stale-DLL (`28ae47612`). LAW:
  launch-game.cmd to menu before EVERY commit (CLAUDE.md gate).
- [x] **ts_nod_ticktank voxel sequence crash** (`4bfd1bcaf`): `ts_nod_ticktank`
  and `ts_nod_attackcycle` had no `idle:` sequence filename — the voxel files
  are `tsttnk.vxl` and `tsbike.vxl` (old TS names), but the sequence entries
  only had `idle:` with no filename. Fixed by adding `idle: tsttnk` and
  `idle: tsbike` respectively in `voxels.yaml`.
- [x] **magicnuke sequence crash** (`4bfd1bcaf`): CABAL neutron weapons
  (`CabalCommandoPlasmaNeutron`, `CabalCommandoPlasmaMk2Neutron`,
  `CabalRavagerPlasmaNeutron`) had `Image: magicnuke` in their
  `CreateEffect` warheads. The `magicnuke` image has sequences `magicnuke`,
  `magicnuke_med`, `magicnuke_small`, `magicnuke_micro` — but `Image:
  magicnuke` makes the engine look for a sequence named `magicnuke_med`
  inside image `magicnuke`, which doesn't exist (the sequences are defined
  under the `magicnuke` image key with those names). Removing `Image:
  magicnuke` lets the engine use the `Explosions:` field directly against
  the sequence set. The `CabalMagicNuke` weapon (line ~1847) already
  worked correctly because it only had `Explosions: magicnuke` without
  `Image:`.
- [x] **ra2_cgtbnkbb.shp not found crash** (`4bfd1bcaf`): Asset was renamed
  to `ra2_cgtbnkbib.shp` (bb→bib convention) but YAML references in
  `redalert2.yaml` were not updated. Fixed all 3 references.
- [x] **ra2_ctoutpbb.shp not found** (`4bfd1bcaf`): Renamed to
  `ra2_ctoutp_bib.shp`, updated 4 YAML references in `redalert2.yaml`.
- [x] **tamrefbb.shp reference** (`4bfd1bcaf`): Renamed to `tamref_bib.shp`,
  updated reference in Forgotten `sequences.yaml`.
- [x] **mk→make asset renames** (`4bfd1bcaf`): 8 construction animation
  files renamed from `_mk.shp` to `_make.shp` (ra2_cgoildmk, ra2_ntyardmk,
  tambarmk, tampowrmk, tamradrmk, tamrefmk, tamtechmk, tsnttmplmk) with
  all YAML references updated.
- [x] **Weapon rename task backlogged** (`4bfd1bcaf`): Full research and
  tooling documented in `docs/history/backlog_weapon_rename.md` for future
  continuation.
- [x] **CABAL Orb Drone carrier-slave crash** (`ec63784bd`):
  `cabal_orb_drone` had `CarrierSlave`+`HasParent` traits while also being
  buildable from the cyborg factory. When built independently, no master is
  linked, causing `NullReferenceException` in `CarrierSlave.EnterSpawner`.
  Split into `cabal_orb_drone` (standalone, no slave traits) and
  `cabal_orb_drone_slave` (non-buildable, inherits base + CarrierSlave).
  Updated `CarrierMaster` on `cabal_hunter_drone_carrier` to spawn the slave.
  Pattern follows RA1 Japan `zerofighter`/`japancarrier`.
- [x] **RA2 corpse death_d crash** (`ac3ba04b7`): `RA2CorpseSpawner` and
  `RA2FlyingBody` CreateEffect warheads lost `Image: ra2corpse` during CE2
  cleanup, causing engine to look for `death_a`-`death_f` sequences in the
  default `explosion` image where they don't exist. Restored `Image: ra2corpse`
  per corpse-spawner exception in DESIGN.md §8.

### P0 — Completed (2026-07-14 session)

- [x] **CABAL Backup Systems upgrade coverage (avatar, widow)**
  (`d4be72f8f`): Added `SpawnActorOnDeath@backup` to `cabal_avatar` and
  `cabal_widow`; added `Inherits@BACKUP` to `cabal_avatar`; created
  `cabal_avatar_backup` and `cabal_widow_backup` actors in
  `rules/tiberiansun.yaml`; added `Repairable` trait to
  `cabal_artilleryspider_backup`.
  **NOTE (2026-07-16):** The original session plan referenced `cabal_legion`
  and `cabal_legion_backup`, but no `cabal_legion` actor exists in the
  current tree (it was likely renamed or removed during the N9 rebalance).
  `cabal_widow_backup` was created instead. If a `cabal_legion` actor is
  re-added later, it will need its own backup actor.
- [x] **Backup husk repair/reanimate** (`d4be72f8f`): `Repairable` trait
  added to `cabal_artilleryspider_backup` (was missing — present on
  manticore and tarantula backups already).
- [x] **CABAL infantry death palette break** (`a2b4de333`): All 8 CABAL
  infantry actors and the `^TSInfantry` template had `WithDeathAnimation`
  with `PlayerPalette: playerra2` but no `DeathSequencePalette`. The
  `DeathSequencePalette` field controls which palette the death sequence
  frames render with; without it, the engine defaults to a non-player
  palette, causing visible color breakage on death. Fixed by adding
  `DeathSequencePalette: ra2player` to `^TSInfantry` template and all 8
  CABAL infantry overrides (cyborginfantry, rocketcyborg, devout,
  ascended, hackercyborg, cyborgcommando, cyborgcommandov2,
  eliminator800).
- [x] **TS GDI building death palette break** (`b417c6f96`): The
  `^BaseBuilding` template in `defaults.yaml` had `WithDeathAnimation`
  with `DeathSequence: dead` but no `DeathSequencePalette` — same root
  cause as the infantry palette bug. Fixed by adding
  `DeathSequencePalette: ra2player` to `^BaseBuilding` and to the
  `WithDeathAnimation@BIB` overrides on GDI and CABAL service depots.
- [x] **TD building death palette fix** (`d72194748`): `^BaseBuilding`
  template sets `DeathSequencePalette: ra2player` globally, but TD
  buildings use `PlayerPalette: player_rgba` — mismatch causes wrong
  colors on death. Fixed by overriding `DeathSequencePalette: player_rgba`
  in `^TDBuilding` and `^TDDefense` templates. Also fixed 3 CABAL infantry
  (rocketcyborg, hackercyborg, eliminator800) that had `ra2player` instead
  of `playerra2` as their death palette (mismatch with their
  `PlayerPalette: playerra2`).
- [x] **TS-only death palette audit** (`54816b1f3`, 2026-07-27): Wrote
  `tools/audit/audit_ts_death_palette.py` — checks all 56 YAML files in
  TiberianSun ContentPacks for DeathSequencePalette vs PlayerPalette
  mismatches. Found and fixed 2 issues: `cabal_cyborgreaper` and
  `cabal_heavyreaper` were missing `DeathSequencePalette: playerra2`.
  Audit now passes with 0 issues. Did NOT touch TD, D2k, RA1, RA2, TKM.

- [x] **Railgun NullReferenceException crash** (2026-07-27): Weapons
  inheriting both `^LaserWeapon` (which sets `HitAnim: laserfire` on its
  `Projectile: LaserZap` node) and `^RailgunWeapon`/`^RA2RailgunWeapon`
  (`Projectile: Railgun`) caused a `NullReferenceException` in
  `Railgun.Render` → `Animation.Render` because OpenRA's deep YAML merge
  carried `HitAnim: laserfire` into the Railgun projectile node. The
  Railgun constructor creates an `Animation` but `Render()` can be called
  before `Tick()` initializes `CurrentSequence`. Affected weapons:
  `SteelQuantumCannon`, `SteelStalkerRailgun`, `SteelFighterRailgun`,
  `RA2Robotmm`, `DalekCannon`, and their elite/EMP variants. Fixed by
  adding `HitAnim:` (empty value) to `^RailgunWeapon`'s `Projectile:
  Railgun` block, which overrides the inherited value. The engine checks
  `!string.IsNullOrEmpty(info.HitAnim)` so empty string prevents the
  Animation from being created. Also removed the redundant empty
  `HitAnim:` from the unused `^TSRailgun` template. Boot verified.

- [x] **Shellmap boot crash: "No valid shellmaps available"** (`6a74333d5`):
  the fix-oramap.ps1 rename pass used CASE-INSENSITIVE replaces on map.yaml
  inside the .oramap zips, corrupting shellmap_v2's PlayerReference
  `Allies:` field keys into `ra1_allies:` (invalid field → map excluded
  from the shellmap pool), and renamed display player names without
  updating the lua inside the zips (`Player.GetPlayer("Allies")` → nil →
  lua fatal). desert-shellmap-2 also kept nonexistent factions `soviet`
  (singular, missing from the tool's rename list) and `modjapan`. Fixed
  both maps + hardened the tool (`-creplace`, added soviet/modjapan
  entries). LESSON: .oramap rewrites must be case-sensitive and must
  update embedded lua player/actor strings in the same pass; a mod-wide
  GetPlayer↔player-name scan now shows 0 mismatches.
- [x] **12 more maps broken by the renames** (`2df758574`): mod-wide sweep
  of all 364 maps (invalid Faction values, unknown actor types, orphaned
  Owners, stale lua ids). Fixed: 5 mission maps (ch1-e1, ch1-e1c,
  delivery, deliverycoop, iris-ally-hb) with 25 stale `Faction:` values +
  1 lua id; 5 .oramaps with singular `ra1/ra2_soviet_*` actor types
  (Border conflict, _ra_ore-gardens, _ra_temperal, thelake6people,
  chernobyl); survival.oramap lua (21 ids pluralized);
  desert-shellmap-2-playable orphaned GDI/Nod owners → Neutral.
- [ ] **Pre-existing broken maps found by the sweep (design decisions
  needed, NOT rename-caused)**: (a) ~70 imported maps carry
  `Faction: england`/`ukraine` — factions that never existed in Cameo
  (decide: bulk-rewrite to `Random` or leave — engine may fall back);
  (b) `troublerebels.oramap` references `heavy_inf` (only
  `heavy_inf.ixian` exists — ambiguous); (c) `tiberium-split.oramap`
  references never-defined `split0a/0b/0c/4/8/9` terrain actors (split2/3
  exist); (d) `_d2k_Centerbase` + `_d2k_tournament_spice` reference
  base-D2K generics (`refinery`, `harvester`, `artillery_platform`,
  `combat_siege_tank`, `medium_gun_turret`, `combat_tank_ixian`) that
  Cameo never defined; (e) survival.oramap still has 13 ancient
  `aa_*`/`steel_*` compressed ids — proposed mappings:
  `aa_phoenix→asianalliance_phoenix`,
  `steel_quantumtank→steelconsortium_quantumtank`,
  `steel_katy→steelconsortium_katytank`,
  `steel_mega→steelconsortium_megalodon`,
  `steel_defender→steelconsortium_defenderbot`,
  `aa_samurai→asianalliance_japanesesamurai`,
  `aa_lynx→asianalliance_lynxtank`, `aa_mecha→asianalliance_pulverizermecha`,
  `aa_flam→asianalliance_asiansentryflamer`; unresolved: `aa_archer`,
  `aa_ftnk`, `steel_fedinf`, `steel_qinf`. Effort: S–M once decided.

### P0/P1 — User-reported issues (2026-07-15/17)

> Golden reference (pre-rename, everything working):
> the last Cameo-IFV release install —
> diff against it when a rename regression is suspected. Tester reports
> (NFWRambo) need verification before fixing.

- [x] **SHARED-ASSET RENAME CLASS sweep** (2026-07-17) — audit_asset_files
  re-run on the full tree: A1 rename-broken refs = 0, A2 missing voxels
  = 0 (the brik/chainlink fixes cleared the class in the loaded tree).
  56 A3 informational refs remain in UNLOADED legacy rules (actiblizz,
  darkreign, iok, starwars) + a few possibly-in-mix refs — no action
  while unloaded. Rule added to DESIGN §1: rename only after crossref
  proves ONE user; shared assets keep their names.
- [x] **RA1 Allies reinforcement pad** (2026-07-17) — chain VERIFIED
  intact: pad needs conyard + techcenter + the promotion + derricklimit;
  the promotion itself needs the Rapier Jumpjet promotion + rank1.
  Tester most likely hadn't completed the two-step promotion chain or
  hit the lobby derrick limit. Not a code bug; maintainer to confirm
  in-game.
- [x] **RA1 Allies description listed SOVIET doctrines** (2026-07-17)
  — CONFIRMED + FIXED: `faction_ra_allies.description` in
  fluent/rules/en.ftl carried the 6 Soviet doctrines and doctrine
  feature bullets; replaced with the real Allied research tree
  (Advanced Radar Systems ... GPS Satellite Support).
- [x] **TD GDI APC described as amphibious** (2026-07-17) — CONFIRMED
  + FIXED in FACTIONS.md: locomotor is `tracked` (not amphibious); the
  AA capability is real (APCGunAA).
- [x] **Schwarzer Mond promotions missing** (tester, second report) —
  FIXED 2026-07-17: implemented the 3-column SM promotion grid from the
  maintainer's image in `SchwarzerMond/yaml/promotions.yaml`, wired all
  unit prerequisites, and verified `^PromotionUnitBuff` on promotion units.
  Boot test passed.
- [x] **Warhead wall-capitalization** (2026-07-17) — evidence reversed
  the call: lowercase `wall` IS the standard (all 3 TargetTypes
  definitions + 345 weapon refs lowercase; only 2 refs used `Wall`).
  Normalized the 2 outliers (starcraft, starwars) to lowercase instead
  of churning 348 lines. Convention documented in DESIGN §1.
- [x] **P0 CRASH: missing `futuretech_concretebarrier_brik.shp` during menu load**
  (2026-07-17) — FIXED: corrected `brik:` sequence in `sequences/tiberiandawn.yaml`
  to use `brik.shp` / `brikicon.png` matching release. Boot verified.
- [x] **P0 CRASH: `japan_chainlinkfence_icon.tem` not found in `cycl` sequence**
  (2026-07-17) — FIXED: replaced with `cyclicon.png` matching release in
  `sequences/tiberiandawn.yaml`. Boot verified.
- [x] **P0 BUG: TD GDI vehicle palette issues** — RESOLVED by user confirmation
  (2026-07-17): palettes are correct in current build; tester was likely on an
  older commit without fixes.
- [x] **P0 BUG: All renamed factions missing voice/notification variants** (2026-07-17)
  — ROOT CAUSE: faction rename migration changed `InternalName` values (e.g.
  `gdi`→`td_gdi`, `nod`→`td_nod`, `allies`→`ra1_allies`/`ra2_allies`,
  `soviets`→`ra1_soviets`/`ra2_soviets`, `tsgdi`→`ts_gdi`, `tsnod`→`ts_nod`),
  but audio variant/prefix keys in `voices.yaml`, `notifications.yaml`, and
  `redalert2.yaml` still used the old names. Without a matching key, the engine
  falls back to `DefaultVariant`/`DefaultPrefix` with no faction suffix,
  producing filenames like `vehic1.aud` instead of `vehic1v00.aud` — which
  don't exist, so voices/notifications are silently skipped.
  FIX: added variant entries for all renamed factions to:
  - `voices.yaml`: `GenericVoice`, `VehicleVoice` (td_gdi, td_nod);
    `RAGenericVoice`, `RAVehicleVoice` (ra1_allies, ra2_allies);
    `RussianVehicleVoice` (ra1_soviets, ra2_soviets)
  - `notifications.yaml`: Prefixes section (td_gdi, td_nod, ra1_allies,
    ra1_soviets, ra2_allies, ra2_soviets, ts_gdi, ts_nod)
  - `redalert2.yaml`: `RA2EngineerVoice`, `RA2MCVVoice`, `RA2LanderVoice`
    Prefixes (ra2_allies, ra2_soviets, ra1_allies, ra1_soviets, td_gdi, td_nod)
  Units with explicit `Voiced` traits using non-variant voice sets (e.g.
  `TSVehicle`, `CommandoVoice`, `BattleFortressVoice`) were unaffected.
  Boot verified, no new exceptions.
- [x] **CRASH: ixian_koda_tank missing icon sequence** — VERIFIED 2026-07-16:
  the `icon` sequence already exists in `Ixian/yaml/sequences.yaml` (line 1372,
  `Filename: DATA.R16, Start: 4028`). `audit_sequences.py` reports 0 S2 missing
  sequences. Crash may have been fixed in a prior session.
- [x] **BUG: Repair drone not repairing** — root cause: `AutoTarget:
  EnableTargeting: false` prevented auto-acquisition of repair targets.
  Fixed by removing the override and restoring `InitialStance: Defend,
  ScanRadius: 12` from `^HelicopterTemplate`. Also set
  `PersistentTargeting: true` on `AttackAircraft` to maintain repair
  targeting. Matches working Ixian repair drone pattern.
- [x] **BUG: Tarantula firing offset** (2026-07-17) — FIXED: restored
  release values. `Turreted: Offset` from `-500,0,0` to `-500,1,1`;
  `LocalOffset` from `500,0,250` to `800,300,700` on both armaments.
  The offset had been changed during the CABAL rebalance and broke
  projectile origin alignment.
- [x] **BUG: Artillery spider firing offset** (2026-07-17) — FIXED:
  restored release values. `LocalOffset` from `300,0,800` to
  `-125,1,250,-125,1,250` (dual barrels) on both armaments.
- [x] **BUG: Tarantula upgraded weapon missing correct magicnuke explosion**
  (2026-07-17) — FIXED: `TS120mm_bluenuke` was using `magicnuke_small`
  (Scale 0.25) instead of `magicnuke_med` (Scale 0.5). Per the scaling
  system: `magicnuke` (1.0) = superweapon, `magicnuke_med` (0.5) =
  second biggest (artillery/heavy units), `magicnuke_small` (0.25) =
  third, `magicnuke_micro` (0.2) = fourth. The Tarantula deals the
  most damage among units, so it gets `magicnuke_med`. The Artillery
  Spider's `CabalArtilleryWalkerShellUpgraded` already correctly used
  `magicnuke_med`.
- [x] **RENAME: interceptor.nax → naxis_interceptor** — renamed
  `nax_interceptor.shp` to `naxis_interceptor.shp` in `bits/ra2/mod/`,
  updated all references in Naxis `sequences.yaml`.
- [x] **RENAME/MOVE: drone.nax → schwarzermond_drone** — renamed
  `nax_drone.shp` to `schwarzermond_drone.shp` and `nax_drone_icon.png`
  to `schwarzermond_drone_icon.png`. Updated SchwarzerMond `sequences.yaml`
  and Naxis `sequences.yaml` (interceptor icon reference).
- [x] **BUG: CABAL Obelisk range/detection** — weapon range set to 12288,
  `WithRangeCircle: Range: 12c0` added, `RevealsShroud: Range: 7c0` matches
  Nod obelisk. All three items already present in working copy.
- [x] **BUG: Starcraft alien ranks applied to all SC factions** (2026-07-17)
  — FIXED: verified that separate decorations already exist in code:
  `^ZergRankDecoration` (alienrank), `^TerranRankDecoration` (terranrank),
  `^ProtossRankDecoration` (protossrank). All three sequence definitions
  exist in `sequences/misc.yaml` using `alienranks.png` as placeholder.
  Found and fixed 7 actors missing their faction's decoration:
  `protoss_corsair`, `protoss_positron`, `terran_madcap`,
  `terran_jimraynor`, `terran_goliathmk2`, `zerg_guardian`,
  `zerg_gorekraken`, and `SCINTERCEPTOR`. Updated
  `audit_rank_decoration.py` to recognize the new decoration names and
  correct `StarCraft` path casing. Audit now reports 0 StarCraft issues.
- [x] **RULE: ActorStatValues upgrade list limit** — documented in DESIGN.md §6
  (design 2026-07-17): `ActorStatValues.Upgrades` maximum expanded from 5 to 10.
  Every unit must list all faction upgrades that affect it; team upgrades from
  other factions must never appear. Applied to `ra1_soviets_monstertank`.
- [x] **RULE: Promotion-unit prerequisite formula** — documented in DESIGN.md §15:
  `Buildable.Prerequisites: ~productionbuilding, techbuilding, ~promotion`.
  The `~promotion` token hides the unit until the promotion is bought; tech
  buildings disable but do not hide. Applied the `~promotion` change to ~144
  promotion units across all factions; reverted accidental `~promotion` changes
  in promotion-actor prerequisite chains.
- [x] **RA1 Soviet Monster Tank upgrade coverage** — added all tank/vehicle doctrine
  and upgrade inherits: `^InfernoDoctrineRA1`, `^TeslaExperimentalTechDoctrineRA1`,
  `^TeslaRocketsUpgradeRA1`, `^NuclearRocketsUpgradeRA1`, `^NuclearShellsTeamUpgradeRA1`,
  plus modest `FirepowerMultiplier` traits for the rocket conditions. Added the
  full `ActorStatValues` upgrade list (10 entries). Note: combined firepower
  stack may exceed the 2.0× power-budget rule for an epic unit; monitor in
  playtesting.
- [x] **All-faction promotion construction-yard gates restored** — corrected an
  earlier mistake: promotion actors MUST keep their `~constructionyard`
  prerequisite. Re-added `~constructionyard` to all promotion actors across all
  factions and updated `tools/audit/audit_promotion_gating.py` and DESIGN.md §15
  to enforce this rule. Promotion-units themselves still use
  `~productionbuilding, techbuilding, ~promotion`.
- [x] **Yuri Mastermind turret attack** — added missing `AttackTurreted:` trait to
  `yuri_mastermind`. The actor already had `Turreted:` and `Armament@PRIMARY`,
  but no turret attack activity, so it defaulted to frontal behavior.
- [ ] **BALANCE: Eliminator 800 overpowered** — 7 Eliminator 800s
  destroyed AI base with only 1 loss. Needs rebalancing (part of full
  CABAL rebalance). Effort: M. **Do NOT auto-apply — requires user
  approval per balance policy.**
- [ ] **BALANCE: Warcraft anti-air damage** — Warcraft anti-air damage is
  reportedly too low/unsatisfying. Needs investigation and balance pass
  (warhead values, weapon targeting, or unit stats). Effort: M. **Do NOT
  auto-apply — requires user approval per balance policy.**

### P0 — TKM CONTRIBUTOR PORT (ordered 2026-07-18, jumps the queue)

A community contributor updated TKM (new upgrades and/or rebalance) but
can't merge anymore after our renames. He sent his ENTIRE repo as a zip,
extracted from a contributor's zip (base version UNKNOWN). Plan: (1) inventory his tree; (2) find his base by matching his
files against our git history / the golden reference release; (3) his
real changes = diff(his tree, base); (4) port onto master through the
rename maps (old ids → tkm_*) into ContentPacks/TKM/TKM/yaml; (5)
audits + boot + commit. Balance numbers he changed are the
contributor's design — port faithfully, flag anything that contradicts
DESIGN formulas instead of silently "fixing".

### New orders 2026-07-19 (template-conformance + classic rifles)

- [x] **RULE + AUDIT: conyard power** — VERIFIED 2026-07-30:
  `audit_template_conformance.py` T1 reports 0 findings. All conyards
  already use the template's 100 power. No overrides found.
- [x] **RULE + AUDIT: icon offsets** — VERIFIED 2026-07-30:
  `audit_template_conformance.py` T2 reports 0 blocking findings.
  6 informational T2b items (D2k legacy + TS 0,0,25 Z-offset patterns)
  flagged for maintainer visual pass — not violations.
- [ ] **LAW: range bands** — every unit stays within ±10% of its class
  baseline range (scouts: 4500–5500 around 5000); lower edge = cheapest
  units, upper edge = most expensive. Applies to ALL templates.
- [x] **Classic rifles get unique characters** — DONE 2026-07-19 (Formula
  v2 scout conversion): TD GDI/Nod minigunners burst 4, RA1 Allies/Soviets
  rifle infantry burst 3, FP multiplier compensation, cost 100 from
  templates. Each has unique HP/speed/range/burst-delays/FP-mult:
  GDI (31k HP, 63 spd, 5499 rng, BD 3, FP 24), Nod (30k HP, 66 spd,
  4609 rng, BD 2, FP 29), Allies (27k HP, 55 spd, 5500 rng, BD 4, FP 47),
  Soviets (34k HP, 54 spd, 4668 rng, BD 5, FP 42). Verified 2026-07-30.

### New orders 2026-07-18 (third batch — crash + SM polish)

- [x] **P0 CRASH (TheCommando315): `KeyNotFoundException 'badr'` in
  ProductionParadropCA.Produce** — VERIFIED 2026-07-27: already fixed.
  C# default is `ra1_badger` (not `badr`), and both YAML usages in
  `ContentPacks/RedAlert/Allies/yaml/buildings.yaml` have explicit
  `ActorType: ra1_badger`. No remaining references to `badr` exist.
- [x] **BUG (Blackrobe follow-up): replaced SM units stay VISIBLE
  (greyed) after their replacement promotion** — VERIFIED 2026-07-27:
  already fixed. All four affected units use `~!` prefix correctly:
  Laser Beetle (`~!schwarzermond_promotion_lasertank`), Lunar Panzer
  (`~!schwarzermond_promotion_lunartiger`), Jagerline
  (`~!schwarzermond_promotion_mars`), Haunebu II
  (`~!schwarzermond_promotion_haunebuiii`).
- [ ] **RENAME ORDER (maintainer): "Jagerline" is fake German** — the
  unit is a ROCKET anti-air vehicle (maintainer 2026-07-18), so the
  gun-flakpanzer names (Kugelblitz/Wirbelwind/Ostwind) do NOT fit.
  Historically correct German AA-ROCKET names to pick from:
  **Wasserfall** (guided AA missile — recommended), **Taifun**
  (salvo-fired unguided AA rocket — fits a line vehicle),
  **Rheintochter** (AA missile, most distinctive sound). Awaiting the
  maintainer's pick; then one pass: id
  (schwarzermond_m200bjagerline -> schwarzermond_<name>), display name
  (drop the American-sounding "M200B" or Germanize it), ftl, MARS
  replacement description, sheet row.

### New orders 2026-07-18 (second batch — Blackrobe report + maintainer)

- [ ] **BUG (Blackrobe): SM passive income building missing** — being fixed in the maintainer's OTHER session (uncommitted WIP adds ra2oilderrick/ra2ywall provisions to the SM conyard); moondairyfarm itself verified wired (techcenter+derricklimit). Do not double-fix. on latest
  dev commit — find what removed/hid it and restore.
- [x] VERIFIED 2026-07-18 **"laser car" + M200B report**: wiring is
  correct both ways (before purchase Beetle/Jagerline buildable; after,
  retired and Laser Tank/MARS appear). If Blackrobe means the
  REPLACEMENTS never appear even after buying the promotions, the rank1
  prerequisite may not be granted by the lobby points option — needs an
  in-game check by the team.
- [x] DONE 2026-07-18 **TKM moved into ContentPacks/RedAlert2Mod** (Blackrobe: do
  the move, postpone the theme-folder rename decision — CnCUniverse /
  CnCExtended / RA2Expanded still open, "not wise to rush").
- [x] DONE 2026-07-18 (superlinear ramp RampFactor 0.08, min-count dip fix, wave veterancy floor(idx/4)) **Survival difficulty (maintainer order):** steepen the ramp so
  late waves outscale early ones, fix the tier-3/4 dip (min unit
  count), and make waves elite over time (veterancy/upgrades — "apply
  upgrades over time or all available from the start").
- [x] DONE 2026-07-18 (MonsterTankTuskTesla/Thermobaric weapons, armament swaps, flat multipliers removed) **Monster tank rockets (maintainer order): apply the MAMMOTH TANK
  logic** — real weapon swaps for Tesla Rockets, (Thermo)Nuclear
  Rockets etc., not the current flat +10% firepower multiplier.

### New orders 2026-07-18 (mid-turn batch)

- [ ] **Theme-folder rename + TKM move (DECISION PENDING — maintainer
  picks the name first).** TKM belongs inside the RA2-mod theme folder
  (it presents in-game as an RA2 modded faction), but
  `ContentPacks/RedAlert2Mod/` shall be renamed first: the folder holds
  RA2-mod factions AND Cameo originals AND other-mod imports; maintainer
  floated "CnCExpandedUniverse", wants alternatives + effort estimate.
  No split into two folders. Move TKM only AFTER the rename so paths
  churn once.
- [x] **BUG (tester, maintainer-confirmed "add to the list"): Tesla
  Rockets upgrade has no visible effect on the monster tank.** VERIFIED
  2026-07-27: wiring is correct. `ra1_soviets_monstertank` inherits
  `^TeslaRocketsUpgradeRA1` which grants the condition; armament
  conditions properly switch between `MonsterTankTusk` (base) and
  `MonsterTankTuskTesla` (upgraded). The Tesla weapon has different
  damage (26750 vs 20000), Tesla damage type, EMP, arc shrapnel, and
  `ra2_tesla_impact` visual. Issue is subtle visual feedback, not
  wiring. Also tester: doctrine upgrades "don't have very descriptive
  descriptions" — separate issue, needs description text improvements.
- [ ] **Survival map (unpacked at maps/survival/ by maintainer/tester —
  do NOT clobber; NFWRambo makes his own `survival 2` copy):
  (a) BUG: game does not end when all waves are cleared — FIXED
  2026-07-29: Implemented CA-style `InitObjectives` (speech notifications +
  objective feedback), centralized `ResolveMission` function, `GameLost`
  guards on ALL perpetual systems (verified zero unguarded), `PendingSpawns`
  counter to prevent premature victory from async reinforcements, and coop
  player elimination handling. Research documented in
  `docs/design/RESEARCH_NOTES.md`.
  (b) difficulty dip waves 12–15 — ADDRESSED 2026-07-27: randomized
  wave system now pads waves with cheapest unit to meet minUnits floor.
  (c) maintainer idea: waves spawn with all upgrades ("elite force") —
  IMPLEMENTED: veteran levels scale with wave index (1 per 4 waves).
  (d) pacing — UPDATED 2026-07-29: max game time capped at 60 min.
  Prep 2.5-3.5 min (150-210s), wave gaps 35-135s (10% short/10% long/80%
  normal). Worst case: 210 + 25*135 = 3585s < 3600s. Budget variance
  reduced from -50%/+80% to -50%/+50% (0.5x-1.5x) to compensate for
  higher max difficulty multiplier. Difficulty reworked from 5 tiers to
  7: TRIVIAL 0.5x, EASY 0.75x, MEDIUM 1.0x, HARD 1.25x, BRUTAL 1.5x,
  UNBEATABLE 1.75x, NIGHTMARE 2.0x. Min/max thresholds unchanged, 2 new
  intermediate tiers (BRUTAL, UNBEATABLE) spread evenly between HARD and
  NIGHTMARE. All taunt lines, hysteresis, and event commentary updated.
  (e) RANDOMIZED WAVES — IMPLEMENTED 2026-07-27: each wave now randomly
  picks a faction from a tier-appropriate pool (22 factions across T1-T4),
  fills an increasing budget with random units from that faction, and
  spawns faction-specific power plants + airfields every wave (old
  buildings are destroyed and replaced). Every playthrough is now
  different.**
  (f) COST & ACTOR VERIFICATION — COMPLETED 2026-07-27: all 22 factions'
  unit, aircraft, and epic costs verified against YAML definitions.
  Fixed 4 cost mismatches (ra1_allies_machinegunner 400→557,
  zerg_hydralisk 500→3314, ra2_soviets_flaktrooper 300→416,
  yuri_gatlingtrooper 300→431). Fixed 1 wrong building reference
  (japan_corepowerplant→japan_waveforcereactor: the former is a
  deployable vehicle, not a ^PowerPlant building). All powerplant
  buildings verified to have ^PowerPlant trait; all airfield buildings
  verified to have ^IsAircraftFactory + Reservable traits.**
  (g) GENERAL TAUNT SYSTEM — IMPLEMENTED 2026-07-27: each wave now picks
  a random general from the faction's roster (3 generals per faction,
  66 total). Each general has a doctrine (infantry/tank/aircraft) that
  biases unit selection 60% toward their specialty, and 6+ unique
  taunt lines in the style of Generals Zero Hour Challenge mode.
  Taunts play at wave start, mid-wave (15-25s later), and final wave
  gets a third taunt. Lines reference faction lore, unit costs, memes,
  and internet culture. Database in maps/survival/generals.lua.**
  (h) STARTING DEFENSES — IMPLEMENTED 2026-07-31: human players now
  receive faction-specific power sources (~500 power) and defensive
  turrets in 4-fold symmetric rings around their base. Turrets are
  strictly own-faction and exclude garrisonable bunkers; the placement
  budget targets ~10k cost per player, using the most expensive turrets
  first and falling back to cheaper ones until the target is met.
  `FactionTurrets`, `DefenseCosts`, and `FactionPowerPlantData` are
  defined in `mods/cameo/maps/survival_work/script.lua`. Heavy support
  starting army is wired but left disabled (`HeavySupport = false`) until
  a map option is added.

### P1a — FORMULA V2 CLASS 1: SCOUT INFANTRY (maintainer 2026-07-18)

Maintainer picked the scout class first; proposed anchor 20000 HP /
50 Speed / 5.0 Range / 4000 Damage / 50 Reload / Cost 100 with the
2x-health bake replacing the ScoutInfantryBuff damage reduction.
⚠ **The bake is HALF APPLIED (measured 2026-08-17): 19 of 35 scouts
cancel the template's `DamageMultiplier@ScoutInfantryBuff: 50` with a
local `Modifier: 100`; 16 still resolve to 50 and are therefore twice
as durable as their price. Finishing this class means finishing that
migration, not just setting the anchor** — W26 / FORMULA_V2.md.
Assessment + simulation: docs/balance/formula_v2_classes.md — anchor
structure confirmed, speed 60 recommended over 50, bake endorsed;
BLOCKED ON: (1) garrisoned/pricing armament flag in the extractor,
(2) WeaponClass seeding for the class weapons, then bake -> anchor ->
sign-off. Awaiting maintainer GO on the refined spec.

### P1 — BALANCE PIPELINE (ordered 2026-07-18 — "very important long term goal")

Full plan: **docs/design/BALANCE_PIPELINE.md**. PHASE 1 DONE
2026-07-18: `tools/balance/extract_stats.py` + committed baseline
ledger (32 faction files, 2025 actors, raw stats + provenance,
deterministic, `--check` drift mode). PHASE 2 DONE 2026-07-18:
`formula.py` (Tiger identity exact, symbolic equivalence vs the
legacy cell formulas exact, closed-form Range solver) +
`build_workbook.py` -> the tracked `cameo_balance_by_faction.xlsx` and
`cameo_balance_by_type.xlsx` workbenches (`cameo_balance_v2.xlsx` is the frozen
pre-split prototype; 32 faction tabs, weapon sub-rows, live formulas, locked non-input
cells, delta traffic lights). PHASES 3+4 DONE 2026-07-18 — WORKING
PROTOTYPE: seed_design.py (437 units seeded from the legacy sheet,
discrepancies.md: 22 cost mismatches, 581 never-priced combat units,
180 unmatched legacy rows for name_map.yaml), import_workbook.py
(xlsx -> ledger, input cells only, proportional warhead scaling),
apply_balance.py (ledger -> yaml via provenance, resolved-value
diffing, SHADOWED-definition detection, --confirm gate). Loop PROVEN:
fixed point exact (0 changes on untouched ledger), live demo
1000->1050->1000 through ledger+push with yaml byte-identical after.
Bonus: the fixed-point test exposed and fixed a resolver cache
poisoning bug affecting ALL audits. Next: Phase 5 Formula v2 +
Phase 6 enforcement (balance check into run_all). yaml → per-faction JSON
ledger (committed) → generated faction/type workbooks (formulas live in the
sheet, locked cells) → legacy-sheet comparator +
discrepancy triage → gated write-back (apply_balance.py, maintainer
order only) → drift audit in run_all so hand-edited balance numbers
become red findings mechanically. Phases 1-3 first (extractor,
workbook builder, comparator); the SM rebalance below is the
pipeline's first customer.

- Jagerline rename: new candidate from maintainer "Alter Peter" (the
  Munich bell tower) — parked with Wasserfall / Taifun / Rheintochter;
  maintainer explicitly wants to think more before deciding.

### P1b — FULL SCHWARZER MOND REBALANCE (ordered 2026-07-17 — now the balance pipeline's first customer)

Maintainer order: "we also need a full rebalance on the schwarzer mond
faction." Rules of engagement:
- **Sheet first** (absolute law): every price/tier lands in
  `docs/design/cameo_armor_system.xlsx` (M in its cell, O/P/Q
  recompute) BEFORE yaml; both edits in the same pass. If the `~$` lock
  file exists the workbook is open — queue the sheet edit and say so.
- **Sequencing**: the rebalance prices the POST-buff-strip stats (the
  10 base units just lost the unintended ^PromotionUnitBuff — their
  effective firepower/durability changed ~10%, so old prices are stale).
- **Workplan**: extract all schwarzermond_* rows from
  `docs/audit/latest/stat_formulas.md` (formula deviations) +
  `power_budget.md`; propose per-unit price/tier corrections; maintainer
  approves the numbers; then sheet + yaml dual-write, §15 superiority
  check on the 4 replacement pairs (Beetle→Laser Tank, Panzer→Lunar
  Tiger, Jagerline→MARS, H2→H3), boot + audits.
- Include: fluent-ification of the 12 promotion tooltips/descriptions
  (raw strings today) and the SM upgrades/defenses columns.

## CABAL — new orders 2026-07-13 (the big batch)

### N1. Green-plasma / neutron-shell gating (`7a0d0025d`)
- [x] New art: `cabal_greenplasma.png` (weak green plasma projectile) +
  `cabal_greenplasmaimpact.png` (green impact burst), both border-safe
  RGBA PngSheets.
- [x] **Neutron-shell gates every magicnuke weapon.** Non-upgraded
  (`!cabal_upgrade_neutronnuclearcatalyst`) = green plasma projectile +
  green impact; upgraded = the blue magicnuke. Pattern already on
  Artillery Spider + Tarantula (basic armament `!cond`, `Armament@Upgraded`
  `cond`); extend the same split to Cyborg Commando, Commando Mk2, and
  the Ravager. Consider updating the upgrade description (it now empowers
  the whole plasma line, not just Artillery+Tarantula).
- [x] **Magicnuke sizes scaled to power, all 4 used** (`magicnuke_micro`
  0.2 < `_small` 0.25 < `_med` 0.5 < `magicnuke` 1.0):
  - micro → TS90mm_bluenuke (~12k)
  - small → TS120mm_bluenuke (Tarantula, ~24k), CabalRavagerPlasma (~32k)
  - med   → Commando plasma (~50k), TS155mm_bluenuke (Artillery, ~60k)
  - **magicnuke (biggest) → the new CABAL superweapon ONLY** (below).
- [x] **Artillery Spider projectile rework** (`901a9018f`): Archer/Specter-style
  ballistic shell with visible blue contrail; upgraded version uses CABAL
  purple → dark-blue thicker contrail and adds Tesla/Magic/Railgun/Chemical
  warheads. Spreadsheet synced.

### N2. CABAL superweapon (biggest magicnuke) (`1f8b58820`)
- [x] New nuke support power, **same values as the Ixian EMP Nuke**
  (`supercomputer.ixian` `NukePowerCA` firing `PulseMissile`:
  ChargeInterval 10500, MissileWeapons PulseMissile, MissileDelay 25,
  CameraRange/CircleRanges 10000, etc.) but with the **biggest magicnuke**
  as the missile/impact animation (+ a new sound, see S-rules).
- [x] **Fired from the CABAL Core**, using **TD Nod Temple of Nod logic**,
  **plus an add-on that adds the missile silo**. (Find the Temple-of-Nod
  NukePower pattern; the "add-on = missile silo" is a prerequisite
  building/attachment that unlocks or houses the silo.)

### N3. CABAL Core = money structure (`7a0d0025d`)
- [x] Turn the CABAL Core into a **special money-generator structure like
  the Asian Military Academy**: **double the income of the Oil Derrick**,
  and it **also counts as an Oil Derrick** (provides that prerequisite /
  captured-tech behavior). It also launches the N2 superweapon.

### N4. Commando plasma weapons + CABAL Obelisk plasma-laser (high-impact + warhead combos)
- [x] DarkObeliskLaser, CabalCommandoPlasma, CabalCommandoPlasmaMk2: keep
  **obelcor3.aud** (do NOT change the sound). All three already use **long
  ReloadDelay + heavy Damage**.
- [x] The **two Commando plasma weapons** already carry the large-AoE triad:
  base = **Cannon + Flame + Chemical**; on the **neutron-shell upgrade**
  they add **Tesla + Magic + Railgun** warheads.
- [x] **CABAL Heavy Obelisk** (`TSCABALObeliskLaserFire`) made unique from
  TS Nod Obelisk: converted to **plasma-laser** = **Laser + Flame + Chemical**
  with matching percentage twins; removed inherited TS Nod upgrade armament;
  paired `cabal_laserimpact_l` effect + `obelmod1.aud`/`drtelectro.wav` sound.
- [x] Warhead audit pass: fixed `CabalMagicNuke`/`TS90mm_bluenuke` effect
  warhead naming, duplicate `Warhead@1Dam` in `TSCyCannon`, and incorrect
  `HealthPercentageDamage` twin on `TSHunterKillerLasers`.

### N5. Laser beam visual rework (DESIGN law — see below) (`6f43f5639`)
- [x] Every CABAL laser: **two beam colors** (inner + outer), a **mix of
  purple + dark blue**, **not too thin**. Beam **width scales with
  damage** (Mantis + all others currently too thin; Core Defender a touch
  too thick but must still scale). **Color also scales with damage**
  (scale BOTH colors so bigger damage looks more dangerous).
- [x] **Laser Spider → obelmod1.aud** (TS Obelisk sound) — FIX from the
  obelray1.aud I set. Smaller lasers → **laser turret sounds** (lastur1.aud).
- [x] **Manticore double laser**: too thin → **spread the two beams out
  more**; rebalance with **more range + more armor** (range/armor deferred to
  balance sheet per DESIGN §3).
- [x] **3 levels of laser ground-impact effect** (purple/blue, scaled by
  damage), applied to ALL laser weapons; each needs a new sound.

### N6. New CABAL effects + sounds
- [x] Audio audit: all CABAL weapons have Report + ImpactSounds (via
  inheritance or direct). Only CabalOverkillDroneLauncher was missing
  a Report — fixed (`5437d4f63`).
- [x] Effect-warhead naming: CABAL had 1 violation (CabalBerserkerBlades
  @3Eff -> @Effect) — fixed (`63c859fde`).
- [ ] New explosion effect for ALL CABAL missiles (+ new sound) — needs
  custom art/audio from maintainer.
- [ ] Plasma-weapon sounds: prefer NEW/unique; cross-check Shattered
  Paradise references. (Cannot synthesize quality .wav here — assign
  unique existing mod sounds and flag any that truly need new custom
  audio for the maintainer to source.)

### N7. Weapon-mount offsets (`7a0d0025d`)
- [x] **Ascended + Devout**: increase the **second (Y) value** of each
  triple offset ~**2×** so their weapons sit further left/right.

### N8. Armor combo (was CC; DONE)
- [x] Cyborg Commando + V2: Heroic/Superheavy dual-armor applied.
- [x] Eliminator 800: Flak/Heavy dual-armor applied.
- [x] Berserker: Heroic/Superheavy via `^HeroInfantryTemplate` + `^TSCyborgDualArmorHeavy`.
- [x] All 11 CABAL infantry verified: every unit has Armor@Secondary +
  DamageMultiplier@Secondary: 200 (some via `^TSCyborgDualArmor*` templates).

### N9. Role + tier + promotion rebalance (L, sheet-first) — MOSTLY DONE
- [x] **3×4 promotion grid fully populated**: Devout, Ascended, Beholder,
  CCV2 (infantry); Spider CNC4, Heavy Reaper, Widow, Core Defender
  (vehicles); Wasp Striker, Super Hunter Killer, Overkill Fortress,
  Mothership (aircraft).
- [x] **T1000 removed**; Beholder moved from Consortium to CABAL.
- [x] **All Omega variants removed** (HK2 Omega, Mothership Omega).
- [x] **Berserker refactored** to hero infantry (`^HeroInfantryTemplate`),
  T4, HP 800k, DPS 7500, cost 10000, from Cyborg Factory, requires Core.
- [x] **Overkill Fortress rebuilt** as Farasha-style carrier with drones.
- [x] **HK1 + Super Hunter Killer**: dual rockets + dual lasers.
- [x] **Carryall renamed**, unarmed transport.
- [x] **Spreadsheet synced**: 35 rows, all TechTier/UnitClass/Special
  values legal per DESIGN.md (1.0/0.75/0.5, epic=1.0/0.3), obsolete rows
  deleted, missing units added, names updated.
- [x] **Husk names fixed** (Carryall, Hunter Killer, Overkill Fortress,
  Overkill Drone).
- [x] **Design doc updated** (CABAL_FACTION_DESIGN.md reflects all changes).
- [x] **Template role audit**: fixed Engineer→^MechanicTemplate,
  Eliminator 800→^HeavyInfantryTemplate, Carryall→^UnarmedTransportHelicopterTemplate,
  Scarab APC→^SupportVehicleTemplate + ^CargoVehicle (`81bad88d2`).
- [x] **Balance formula audit**: all 30 CABAL units [OK] — 0 ABSURD, 0 HIGH,
  0 formula-broken. Fixed 7 problem units (Legion, Mothership, RocketCyborg,
  Wasp, WaspStriker, Ascended, Beholder) + dissolver crash (missing crippled
  sequences + wrong icon palette) (`50f3db5e4`); fixed 3 formula-broken
  workbook rows 27-29 (`160a6491a`).
- [x] **Repair Drone** added as buildable support aircraft (`94a58b2a7`);
  spreadsheet row added, icon uses carrier icon placeholder.
- [x] **Open question**: Overkill Fortress vs Overkill Carrier final name.

### N10. Upgrades audit
- [x] Reviewed every CABAL upgrade for meaningful consumption. Removed the
  meaningless `cabal_upgrade_clusterwarhead` (no actor, building, or template
  consumed it; also removed its Fluent description and AI entry).
  All other upgrades are wired: conditions granted by templates are
  inherited and used by at least one actor or support power. Kept the
  neutron-shell twins untouched.

### N11. Descriptions + AI
- [x] All CABAL units have Fluent descriptions (converted 8 inline \n
  descriptions to Fluent keys per DESIGN.md §7, `1f580f6e0`; plus 2 more
  fixed: cabal_refinery + cabal_mobileconstructionvehicle).
- [x] AI wiring: all CABAL units in UnitsToBuild list with weights.
  cabal_engineer added to CapturingActorTypes; stale tscyc2.cabal removed.
- [x] CABAL added to global Random + RandomTournament faction pools;
  "(WIP)" suffix removed from faction name.
- [x] Fluent key naming fixed: actor-cabal_core/actor-cabal_techcenter
  → underscores (actor_cabal_core/actor_cabal_techcenter).
- [x] Building name capitalization fixed: "Cabal Tech Center" → "CABAL
  Tech Center", "Heavy Cabal Obelisk" → "Heavy CABAL Obelisk".
- [x] Manticore description updated: removed trap net references (trap
  weapon removed from unit).

### CE (carried). Effect-warhead naming sweep, mod-wide
- [x] CABAL: 1 violation fixed (CabalBerserkerBlades @3Eff -> @Effect,
  `63c859fde`). CABAL is fully compliant.
- [x] Mod-wide: 202 renames across 40 files via scripted sweep
  (`2ad0f35e1`). Audit: `tools/audit/audit_effect_warhead_names.py`
  (0 violations). Template override names preserved; suffixed variants
  (@Effect2, @EffectAir2, etc.) recognized as canonical.

### CE2. CreateEffect Image field audit + explosion sequence consolidation
- [x] **CABAL CreateEffect Image: removal** (2026-07-15): Removed explicit
  `Image:` fields from all CABAL `CreateEffect` warheads in
  `CABAL/yaml/weapons.yaml`. All impact animations now use the default
  `explosion` image (engine default when `Image:` is omitted).
- [x] **CABAL impact animations moved to misc.yaml** (2026-07-15):
  `cabal_greenplasmaimpact`, `cabal_missileexplosion`,
  `cabal_laserimpact_s`, `cabal_laserimpact_m`, `cabal_laserimpact_l`,
  `cabal_dissolveimpact` moved from `CABAL/yaml/sequences.yaml` to
  `sequences/misc.yaml` under the `explosion:` key. Removed the old
  top-level definitions from the CABAL sequences file.
- [x] **Mod-wide CE-only Image: fixes** (2026-07-15): Moved CE-only
  image `wc2_building_collapse` under `explosion:` in misc.yaml; removed
  `Image:` from 7 CE warheads in `weapons/warcraft2.yaml`. Removed
  redundant `Image: explosion` from `weapons/halloween.yaml`. Shared
  images (used by both CE and other traits) keep their `Image:` field
  per the shared-image exception in DESIGN.md §8. `ra2corpse` reverted —
  corpse spawner needs `Image:` for random-pick from its own
  sub-sequences (corpse-spawner exception, DESIGN.md §8).
- [x] **DESIGN.md updated** (2026-07-15): Added rules to §8 documenting
  that `CreateEffect` must never carry `Image:` (CE-only), the
  shared-image exception, and that all impact animations must live in
  `misc.yaml` under `explosion:`.
- [x] **Audit tooling** (2026-07-15): `tools/audit_createeffect_image.py`
  flags all CE `Image:` fields; `tools/audit_ce_image_usage.py`
  classifies CE-only vs shared.
- [ ] **Future**: If a shared image's non-CE references are ever removed,
  it becomes CE-only and should be moved under `explosion:` at that time.

### CE3. Map actor renaming (delivery + deliverycoop)
- [x] **Actor rename in new maps** (2026-07-15): Commit
  `e6ad4ded5fa08c6b41fde63a256f2f5c15917241` added new maps
  (`delivery/map.yaml`, `deliverycoop/map.yaml`) with old compressed
  actor names. All 2257 actor references in both map.yaml files and 90
  string references in lua scripts renamed to new §1-compliant ids using
  `tools/rename_map_actors.py` with the `tools/rename/rename_map_*.yaml`
  mapping files. Terrain decorations (t01, v01, boxes01, brik, etc.) left
  as-is since they still exist with those names.
- [x] **DESIGN.md updated** (2026-07-15): Added §14 documenting map actor
  naming rules and the rename procedure.

---

## Content-pack completion — TOP PRIORITY (ordered 2026-07-16)

_User order (verbatim intent): "Move everything to the new content packs
and verify that everything has been converted correctly! Try your best
reasoning to make sure every actor you move is in the right content
pack. It happened before that some ended up in the wrong section. Also
start moving all the necessary game files into the content packs as
well."_

- [ ] **PACK-RA1: Split RA1 (Allies / Soviets / Japan) out of
  rules/redalert.yaml** into ContentPacks/RedAlert/{Shared,Allies,
  Soviets,Japan} using tools/packs/split_faction.py. Shared concrete
  actors (`RAE1`, `RARE1`, shared `^RA*` templates) go to
  RedAlert/Shared. Verify: registry identity + resolved-closure diff
  empty + boot. NOTE: `RAE1` IS the Allied basic rifleman (user
  correction 2026-07-16) — legacy short ids like RAE1/RARE1 get their
  §1-compliant names during this split's rename step.
- [ ] **PACK-RA2: Split RA2 (Allies / Soviets / Yuri)** from
  rules/redalert2.yaml the same way.
- [x] **PACK-SC** (`4fe295183`): Terran/Zerg/Protoss split, registry-identical, boot-verified.
- [x] **PACK-WC2** (2026-07-17): Humans/Orcs split, registry-identical, boot-verified.
- [x] **PACK-TKM** (2026-07-17): split (ContentPacks/TKM/TKM), registry-identical, boot-verified.
- [ ] **PACK-OP2**: split the Outpost2 monolith (eden/plymouth, WIP factions) — last loaded monolith.
- [ ] **PACK-AUDIT (wrong-section detector)**: new
  `tools/audit/audit_packs.py` that verifies per pack: (a) every actor
  id carries the pack's faction prefix (catches actors landing in the
  wrong pack); (b) actors sit in the correct per-type file (trait
  heuristic: Building→buildings/defenses, Aircraft→aircraft, naval
  Locomotor→naval, husk→husks, upgrade/promotion markers→their files);
  (c) content.yaml lists exactly the yaml files on disk (no drift, no
  nonstandard filenames); (d) pack references resolve inside
  pack+Shared+core only. Run after every split.
- [ ] **PACK-ASSETS: per-faction asset migration** — repeat the CABAL
  pilot for every split pack (identify faction-unique files, move to
  files/{sprites,icons,voxels,sounds}, reference via package prefix,
  boot). Order: follow the pack splits; the four cross-game blockers
  (gunfire2, electro, dragon, DATA.R16) stay tracked above.
- [ ] **PACK-GEN (automatic maintenance)**: `tools/packs/gen_content.py`
  regenerates every pack's content.yaml deterministically from the
  files on disk (sorted, grouped Rules/Weapons/Sequences/FluentMessages);
  audit mode fails on drift. content.yaml becomes machine-maintained.

## Content-pack folder restructure (P2/P3, L)

- [x] Every content pack: `content.yaml` at root + one **`yaml`** folder
  (rules+weapons+sequences merged) + an empty **`files`** folder. Shared
  assets → per-GAME `Shared/files/`. DONE 2026-07-14: all packs
  restructured, boot-tested, committed.
- [x] **`mod.yaml` package hierarchy** (2026-07-15): per-faction
  `files/` packages are mounted first, then per-game `Shared/files/`,
  then top-level `ContentPacks/Shared/files/`, then legacy `bits/`. This
  lets new content shadow old content without breaking old cameo fallback.
- [x] **CABAL asset migration** (2026-07-15, `68cdd5ebb`/`472209150`): 128
  CABAL-unique assets moved into
  `ContentPacks/TiberianSun/CABAL/files/{icons,sprites,voxels}` and
  referenced with package prefixes.
- [x] **Cross-game shared asset migration** (2026-07-15, `e1b153d9c`/`472209150`):
  38 single-file cross-game shared assets moved into
  `ContentPacks/Shared/files/sprites/` and referenced with
  `shared_sprites|<name>` across all affected ContentPacks.
- [x] **TiberianSun intra-game shared asset migration** (2026-07-15,
  `6835a04`): 21 TS-only shared assets moved into
  `ContentPacks/TiberianSun/Shared/files/{icons,sprites,voxels}` and
  referenced with `ts_shared_*|<name>` prefixes.
- [ ] **Remaining critical cross-game shared assets**: `gunfire2`
  (generic/RA/TD variants), `electro` (7 tileset variants), `dragon`
  (RA sprite vs WC2 sound name collision), and `d2k/DATA.R16` (resource
  package). These must be resolved before `bits/` can be deprecated.
  → active work: cross-game sharing is a release blocker for dynamic
  faction loading, so this jumps the queue within the content-pack section.
- [ ] **AI module split**: per-faction `ai.yaml` is currently blocked by
  OpenRA's YAML merge behavior (trait instances with the same `@name`
  are replaced, not deep-merged). Needs custom trait or engine change.
  → backlog until architecture is designed.
- [ ] **Unused-file audit**: once all referenced assets are out of `bits/`,
  run an audit to identify and delete the ~25,000 unreferenced legacy
  files left in `bits/`.

## Cross-faction shared-effect independence (LONG-TERM, L)

- [x] Top-level `ContentPacks/Shared/files/` created as a temporary
  holding area for cross-game assets (2026-07-15).
- [ ] Duplicate or replace every cross-game shared asset so each game
  owns its own copy, then remove the top-level `Shared/files/` entries.
- [ ] Give each faction its own effects, or share only PER GAME. Prereq
  for true dynamic per-faction loading. DESIGN + MIGRATION.

---

## D2k wall+turret system expansion (LONG-TERM, L)

**Current state:** The D2k wall (`ContentPacks/D2k/Shared/yaml/buildings.yaml`)
already has `Replaceable: Types: Tower` and all D2k turrets (Ordos + Ixian)
have `Replacement: ReplaceableTypes: Tower`. This means turrets can be
built on top of wall segments, replacing them — the core D2k mechanic
works. The wall's `LineBuild` includes `turret` in `NodeTypes`, so walls
connect to turrets visually.

**Goal:** Expand this mechanic to all factions and add new turret-on-wall
types, creating a unified wall+turret defense system across the mod.

### Plan

1. **Audit existing wall+turret pairs** — identify which factions have
   walls with `Replaceable` and which turrets have `Replacement`. Currently
   only D2k (Ordos + Ixian) has this. TS Nod has laser fences but no
   turret replacement. TD/RA factions have plain walls with no replacement.

2. **Design faction-specific wall+turret pairs** — each faction that gets
   a concrete wall should also get a turret that can mount on wall
   segments. Examples:
   - TD GDI: Guard Tower → mountable on BRIK walls
   - TD Nod: Turret → mountable on BRIK walls
   - RA1 Allies: Gun Turret → mountable on BRIK walls
   - RA1 Soviets: Tesla Coil → mountable on BRIK walls (or a smaller turret)
   - TS GDI/Nod: Component Tower style → mountable on concrete walls
   - CABAL: unique turret type → mountable on concrete walls

3. **Add `Replaceable` to all wall actors** — add `Replaceable: Types: Tower`
   (or faction-specific type) to BRIK, SBAG, CYCL, FENC, BARB, and the
   RA2/D2k walls. Use multiple `Replaceable@` traits if a wall should
   accept multiple turret types.

4. **Add `Replacement` to turret actors** — add
   `Replacement: ReplaceableTypes: Tower` (or matching type) to each
   faction's base defense turret.

5. **Add `turret` to wall `LineBuild.NodeTypes`** — so walls visually
   connect to turrets. Currently only the D2k wall has this.

6. **Balance pass** — wall-mounted turrets should cost less than
   free-standing turrets but require the wall to exist first. This
   matches D2k's design where walls are cheap and turrets are expensive.

7. **Art pass** — ensure turret sprites align visually when placed on
   wall segments. May need wall+turret composite sprites for some factions.

8. **Future: D2k faction wall variants** — when Atreides and Harkonnen
   are added, give them faction-specific wall sprites (concrete wall
   variants per house color/style).

### Dependencies
- Must be done after barrier type assignment is finalized per faction.
- Requires balance workbook updates (new turret costs, wall costs).
- May need new C# traits if the existing `Replaceable`/`Replacement`
  system doesn't support all desired behaviors (e.g. conditional
  replacement based on tech level).

---

## Phase B — CABAL effects & art polish
- SP-recipe projectiles/contrails (art our own); dark-blue/purple identity;
  promotion icons for placeholders; SP-like reports from TS material.

## Phase C — Balance & consistency (other factions)
- Infantry offset sweep beyond TS; TS rocket launch-angle sweep beyond
  CABAL; clean workbook (port CABAL rows); 165 sheet↔game mismatches;
  [x] FutureTech .futu→futuretech_ rename — 32 asset files renamed, 8
  YAML/FTL files updated (voxels, sequences, ContentPack rules, Fluent).
  Soviet Gorynych/Stalin Fist.

## Phase D — SP-ification of the other TS factions (after CABAL)
- TS GDI, Nod, Forgotten, then Scrin — SP-recipe weapons/effects, workbook stats.

## Phase E — Platform & engine (background, L)
- [x] **Port `AttackGarrisonedSP`** (one fire port per passenger) + convert all
  `AttackGarrisoned`/`AttackOpenTopped` units to per-passenger independent
  targeting. New `AttackGarrisonedSP` trait in `OpenRA.Mods.CA/Traits/Attack/`
  inherits `AttackFollow`, supports both `Cargo`/`Passengers` and
  `Garrisonable`/`Garrisoners`, and adds per-passenger opportunity fire via
  each passenger's `AutoTarget` trait. All 26 YAML usages across rules +
  ContentPacks converted from `AttackGarrisoned`/`AttackOpenTopped` to
  `AttackGarrisonedSP`. `PortYaws`/`PortCones` made optional (default 360°).
  **REVERTED** (`cfa117c78`): AttackGarrisonedSP caused a major regression —
  garrisoned passengers could no longer independently auto-target because
  passenger AutoTarget traits don't function while inside cargo. All 56 YAML
  trait renames reverted to vanilla `AttackGarrisoned`/`AttackOpenTopped`.
  The C# source file is kept for future reference but unreferenced.
- SP engine-trait ports; TS Shared pack move; Formula v2; dynamic faction
  loading end-game (per-pack ai.yaml, assets into packs, unused-file audit).

---

## Standing rules recorded (see DESIGN.md / memory)

- **CreateEffect Image: field** (DESIGN §8, 2026-07-15): a weapon
  `CreateEffect` must NEVER carry an `Image:` field — omit it and the
  engine defaults to the `explosion` image in `misc.yaml`. All impact
  animations live as sub-sequences under `explosion:` in
  `sequences/misc.yaml`, never in faction sequence files.
- **Map actor naming** (DESIGN §14, 2026-07-15): maps must use renamed
  actor ids, not old compressed names. Rename maps in
  `tools/rename/rename_map_*.yaml` are the source of truth. Lua scripts
  must also be updated. Tool: `tools/rename_map_actors.py`.
- **No weapon inheritance between units** (DESIGN §15, reinforced
  2026-07-15): unit-unique weapons must never `Inherits:` from another
  unit's weapon. Copy stats or use a shared `^`-prefixed template. This
  was the root cause of the CreateEffect crash class.
- **CABAL Avatar = 50% Core Defender** (DESIGN §15, 2026-07-15): the
  avatar is a 50%-scaled copy of the Core Defender, not a spider.
- **CABAL husk recovery** (DESIGN §15, 2026-07-15): backup husks are
  immobile, high-HP, repairable, auto-reanimate via
  GrantPeriodicCondition + TransformOnCondition.
- **Effect + sound are always defined together** (DESIGN §8): every new
  impact/projectile effect gets BOTH a new effect sprite AND a new Report/
  ImpactSound — never fall back to the template's default for either.
  Unique-per-faction is the goal.
- **Effect frame-fit**: every rendered effect must sit INSIDE its frame
  (2px border alpha 0) or it clips to a square. Verify with a bordered
  preview. (memory: cameo-custom-effects-pngsheet)
- **Laser beams (DESIGN §3)**: two colors (inner+outer), width AND color
  scale with damage; CABAL = purple + dark blue, never too thin.
- **Obelisk/laser sound map (DESIGN §3)**: obelmod1.aud = TS Obelisk of
  Light / Obelisk of Darkness / CABAL Obelisk; obelcor3.aud = Core
  Defender + DarkObeliskLaser + Commando plasma; obelray1.aud = Tiberian
  DAWN obelisk — NOT allowed on TS units unless specified (SP `^LaserWeapon`
  inherit = the TD version); smaller lasers = lastur1.aud turret sounds.
- **Effect-warhead naming**: one `CreateEffect` per impact surface.
- **Per-frame randomness** on new animated effects.
- **Content-pack structure**: yaml folder + files folder + content.yaml.

### Backlog — Rank decorations & elite weapons (DESIGN §16, 2026-07-15)

- [x] **Fix TS Nod rank decoration** — 13 TS Nod actors were using
  `^GDIRankDecoration` instead of `^NodRankDecoration`. FIXED in this
  session. Also fixed 4 TS Forgotten actors in `defenses.yaml` and 2
  core `tiberiansun.yaml` Nod units (`ts_nod_attackcycle`,
  `ts_nod_ticktank`).
- [x] **Wire D2k factions to `^DuneRankDecoration`** (`5ff288c5c`) — Added
  `Inherits@decoration: ^DuneRankDecoration` to 64 D2k actors across Ixian,
  Ordos, Harkonnen, and Shared yaml files. Audit tool:
  `tools/audit/audit_dune_rank_decoration.py` (0 remaining).
- [x] **Create `^AlienRankDecoration` template** (`b95f5e7f3`) — Created
  template in `rules/starcraft.yaml` using existing `alienrank` sequence
  from `misc.yaml`. Wired to 79 StarCraft actors (Terran, Protoss, Zerg)
  that use `^GainsExperienceTD`. Warcraft2 actors still need a custom
  `wc2rank` image (no sequence exists yet — out of scope).
  **NOTE (2026-07-16):** This commit incorrectly applied `^AlienRankDecoration`
  to ALL Starcraft factions. It should only apply to Zerg. Terran and
  Protoss need separate decorations. See SC-RANKS below for the fix plan.
- [ ] **Create per-faction rank decorations for RA2Mod factions** —
  currently all RA2Mod factions share `ra2rank` via
  `^GainsExperienceRA2`. Eventually each could have a unique rank image
  for faction identity (low priority — shared `ra2rank` is functional).
- [x] **Write `audit_rank_decoration.py`** (`10220c0ee`) — verifies every
  `^GainsExperienceTD` actor has the correct `^*RankDecoration` for its
  faction, verifies `^GainsExperienceRA2` actors do NOT have a separate
  decoration, and checks that rank image sequences exist in `misc.yaml`.
  Current state: 135 issues (mostly SC/WC2/RA2Mod factions that share
  `ra2rank` or lack faction-specific decorations — low priority).
- [ ] **E1: Add missing elite weapons** — Audit (`tools/audit/audit_missing_elite.py`,
  `4d0e8ec85`) found **1256** buildable actors with `GainsExperience` but no
  `Armament@*ELITE*` block. Top factions: rules/redalert (100), rules/starcraft
  (79), rules/wh40k (75), rules/darkreign (68), rules/shockwave (67),
  rules/generals (55), rules/advancewars (52), rules/starwars (45),
  rules/redalert2 (41), TS/Forgotten (37), rules/tkm (36), TS/CABAL (34).
  This is a large multi-session design effort — each elite weapon needs unique
  stats, not a mechanical rename. Needs user direction on scope/priority.
  **NOTE (2026-07-16):** The audit script was updated to only flag
  `^GainsExperienceRA2` actors (per DESIGN.md §16.3 "RA2 system only").
  The count of 1256 was from the old scope — re-run the audit for the
  current RA2-only count. TD/D2k/SC/WC2 actors no longer flagged.
- [x] **E2: Fix missing `rank-elite` conditions** (`ac3ba04b7`) — Only 2
  genuine bugs found (out of 18 flagged; rest use Generals `scrap_create_bonus`
  rank system or upgrade-switch naming). Fixed:
  `asianalliance_plasmatrooper` GARRISONEDELITE and
  `asianalliance_heavyrailguntank` ELITE. Added audit tool
  `tools/audit/audit_elite_gating.py`.
- [x] **E3: Normalize elite weapon naming** (`ab870ddb3`) — Renamed 10
  non-standard elite weapons to `<base>E` convention (38 references across
  12 files): `NaxPlanegun`→`NaxPlanegunE`, `NaxPlaneRockets`→`NaxPlaneRocketsE`,
  `NaxiWW2MachinegunnerElite`→`NaxiWW2MachinegunnerE`, `NaxiBeetleLaser`→`NaxiBeetleLaserE`,
  `NaxiBeetleLaserAA`→`NaxiBeetleLaserAAE`, `NaxCorrosionRocketTrooper`→`NaxCorrosionRocketTrooperE`,
  `TSBikeMissileNashwaElite`→`TSBikeMissileNashwaE`, `V3LaunchElite`→`V3LaunchE`,
  `RA2KirovBomb_nuclear_Elite`→`RA2KirovBomb_nuclear_E`, `CuteKirovBombElite`→`CuteKirovBombE`.
  Remaining 44 are doctrine variants (`_rad`/`_fire`/`_tesla`), upgrade combos,
  or gatling spin-ups — intentionally non-standard. Audit tool:
  `tools/audit/audit_weapon_suffixes.py` (X1 section).
  **NOTE (2026-07-16):** The `E` suffix convention has been superseded —
  ALL elite weapons must now use `_elite` per DESIGN.md §16.3. The renames
  done here will need to be re-done as `<base>_elite` in WEAPON-SUFFIX-ELITE.
- [x] **E4: Verify base weapon gating** (`ac3ba04b7`) — Fixed the 2 actors
  from E2: added `RequiresCondition: !rank-elite` to
  `asianalliance_heavyrailguntank` PRIMARY and
  `asianalliance_plasmatrooper` GARRISONED so elite replaces, not stacks.

## D2K Sprite Conversion Pipeline

- [x] **D2K-CONV: Conversion script** — `tools/d2k_to_openra.py` written
  and documented in DESIGN.md §17. Combines BMP frames → PNG spritesheet,
  pink→transparent, hue-shift green player color to target hue, embeds
  FrameAmount/FrameSize PNG metadata for OpenRA.
- [x] **D2K-KODA: Koda Tank** — replaced `combat_tank.ixian` with
  `ixian_koda_tank` using new PNG spritesheets (chassis + turret).
  Updated all references in Ixian/Ordos faction.yaml, upgrades.yaml,
  ai.yaml. Muzzle flash still uses DATA.R16. Pending in-game visual
  confirmation.
- [ ] **D2K-CONV-FUTURE: Convert more D2K units** — other D2K units that
  could benefit from custom PNG sprites instead of DATA.R16 remapping.
  Use the same script with appropriate `--hue` per faction.

## Schwarzer Mond Faction Design & Upgrades

- [x] **SM-RESEARCH: Finalize promotion intent** — promotions will upgrade
  existing units via `^PromotionUnitBuff` rather than unlocking new actor
  variants. The `Bradley` unit in the promotion image is resolved as the MARS
  hover artillery (`schwarzer_mond_mars`). Added the buff to all combat
  infantry, vehicles, and aircraft. Updated DESIGN.md §18.7 / §18.11.
- [x] **SM-UPGRADE-1: Add upgrade templates** — create `^NaxiCryptofascism`,
  `^NaxiLunarAlloys`, `^NaxiMoonPropaganda` in the appropriate Shared or
  Schwarzer Mond templates file. Update DESIGN.md §18.6 if the template set
  changes.
- [x] **SM-UPGRADE-2: Split laser upgrade** — turn Crystal Lens into a +1-burst
  radar-tier upgrade for all yellow laser weapons; add Amplified Lens as the
  tech-tier +1-burst upgrade for all yellow laser weapons. Update all weapon
  variants and actor armament conditions per DESIGN.md §18.4.
- [x] **SM-UPGRADE-3: Move cannon upgrade to tech tier / rename to Vril Powered
  Weapons** — change `schwarzer_mond_upgrade_vrilpoweredweapons` prerequisite
  from radar to `~schwarzer_mond_techcenter`, keep it in the `Research` queue,
  and rename the display name/template/icon from Green Plasma Shells to Vril
  Powered Weapons.
- [x] **SM-UPGRADE-4: Add Cryptofascism upgrade** — create
  `schwarzer_mond_upgrade_cryptofascism` (tech tier, Research queue) with
  `CashTrickler` 1 credit per 25 ticks per unit. Add icon sequence for
  `nax2_cryptofascismicon.png` in `mods/cameo/bits/ra2/mod/`. Inherit on
  every Schwarzer Mond actor.
- [x] **SM-UPGRADE-5: Wire upgrades to every unit** — ensure every Schwarzer
  Mond actor has at least two relevant upgrade hooks (Cryptofascism + either
  Lunar Alloys, Crystal Lens, Vril Powered Weapons, Moon Propaganda, or
  Helium-3). Do not change unit stats without a spreadsheet pass.
- [x] **SM-DESC: Normalize faction and unit descriptions** — rewrite the
  Schwarzer Mond `faction_ra2_lnaxis` description in the point-based format
  (Difficulty, Early/Mid/Late Game, Playstyle, etc.) and add/update unit
  descriptions for new upgrades. Normalize other RA2Mod factions when touched.
- [x] **SM-LORE: Add Iron Sky / Nazi Moon lore** — document Vril, Helium-3,
  MoonCoin/Reichsmark 2.0 parody in DESIGN.md §18.12 and update upgrade names
  and descriptions to match.
- [x] **SM-HELIUM3: Add Helium-3 Enrichment upgrade** — create
  `schwarzer_mond_upgrade_helium3` (radar tier, Upgrades queue) that increases
  Hydrogen Plant power output by 50% and vehicle/aircraft speed by 25%. Add
  template, icon, and sequence; wire to all vehicles and aircraft.
- [x] **SM-VRILINFUSION: Add Vril Infusion upgrade** — create
  `schwarzer_mond_upgrade_vrilinfusion` (tech tier, Research queue) that gives
  all Schwarzer Mond infantry +25% firepower, +25% speed/turn rate, and 15%
  damage reduction. Add template, icon, sequence, and wire to every infantry
  actor. Update descriptions and intent.
- [x] **SM-1BURST: Re-enable laser upgrades on 1-burst weapons** — add Lunar
  Soldier and Laser Tower to the Crystal Lens / Amplified Lens switch and
  recreate the 1-burst yellow/amplified weapon variants.
- [x] **SM-AUDIT: Run audit suite and rebuild** — audit suite run
  2026-07-15. Schwarzer Mond upgrades: cryptofascism 26/27, lunaralloys
  26/27, moonpropaganda 5/5, vrilinfusion 5/5 (only uncovered: tsprobe
  shared unit). No orphaned SM actors/weapons. No faction leaks. Game
  boots to menu clean.
- [ ] **SM-BALANCE: Spreadsheet pass** — if any base stats change (e.g.
  raising base burst of Lunar Soldier or Laser Tower), update
  `docs/design/cameo_armor_system.xlsx` and the yaml in the same pass.
  Queue if the Excel lock file is present.
- [x] **SM-ARTWORK: Replace copy-pasted icons** — create unique placeholder
  icons for `schwarzer_mond_mars`, `schwarzer_mond_m200bjagerline`,
  `schwarzer_mond_gravitycoretank`, and `schwarzer_mond_blackbomb`. See
  `docs/design/RESEARCH_NOTES.md` for the full status. Final
  production-quality cameo art can replace the placeholders later.

## Sequence Filename Standardization

- [ ] **SEQ-RESEARCH: Cross-reference audit** — build a complete map of
  which sequence filenames are used by which actors across all sequence
  YAML files. Identify:
  (a) files used by only one actor (safe to rename),
  (b) files shared across multiple actors (MUST NOT be renamed),
  (c) files in shared namespaces (`shared_sprites|`, `ts_shared_sprites|`,
      `td_shared_sprites|` — never renamed),
  (d) template default filenames in inherited `^` templates (never renamed),
  (e) death/muzzle/parachute files defined in templates (never renamed).
  Output: `tools/audit/sequence_file_crossref.json`.
  Effort: M.
- [ ] **SEQ-MIGRATE: Rename sequence files to match actor + sequence name**
  — per faction, rename actor-owned files so that:
  (a) the idle/body sprite is `<actor_id>.<ext>` and moved to `Defaults:`,
  (b) non-idle sequences use `<actor_id>_<sequence_name>.<ext>` (e.g.,
      `_bib`, `_make`, `_turret`, `_icon`, `_muzzle`, `_active`, `_dead`,
      `_damaged`, `_deploy`, etc.),
  (c) shared files are left untouched,
  (d) Combine sub-images unique to one actor are renamed to
      `<actor_id>_<descriptive_suffix>.<ext>`,
  (e) inherited template defaults are left untouched.
  Use `tools/rename/rename_map_<faction>.yaml` + `tools/rename/safe_rename.py`.
  Verify with `tools/audit/dump_resolved.py` before/after diffs (empty).
  Update `.oramap` files with `tools/fix-oramap.ps1` if needed.
  Effort: L (multi-session, ~18,500 asset files across all factions).
  **Risk assessment**: HIGH — missing a reference causes a crash. Must
  be done one faction at a time with boot tests between each. Shared
  file detection is the critical safety gate. See DESIGN.md §1
  "Sequence filenames must match their actor and sequence name".

- [ ] **WPN-MIGRATE: Rename weapons to include full actor id prefix**
  — per faction, rename actor-specific weapons from PascalCase to
  `<actor_id>_<weapon_descriptive_name>` (e.g., `CabalTarantulaCannon` →
  `cabal_tarantula_cannon`, `RA2KirovBomb` → `ra2_soviets_kirov_bomb`).
  Weapon class templates (`^SmallArms`, `^MediumCannon`, etc.) and
  faction-level templates (`^CabalMissile`, `^RA2RadShell`) keep their
  PascalCase `^` names. Elite variants append `_elite`, EMP variants
  append `_EMP`, AA variants append `_AA`, upgraded variants append
  `_upgraded`. Weapons shared across factions (in Shared/ packs) stay as-is.
  Use `tools/rename/rename_map_<faction>.yaml` + `tools/rename/safe_rename.py`.
  Verify with `tools/audit/dump_resolved.py` before/after diffs (empty).
  Effort: L (multi-session). See DESIGN.md §1 "Weapon names must include
  the full actor id as a prefix".

## Long-term goals

- [ ] **ZERO YAML ERRORS & WARNINGS** — achieve zero errors and zero warnings
  from `utility.cmd cameo --check-yaml`. Latest report: 2026-07-24
  (check_yaml_v8.txt, ~89,392 errors, ~69,325 warnings).
  Full phased plan in `docs/history/MEGAPLAN_YAML_CLEANUP.md`.
  Analysis tool: `tools/audit/analyze_check_yaml.py`. Effort: L (multi-session).

  **Fixes applied this session (2026-07-24):**
  - [x] LaunchAngle (363→0): Converted LaunchAngle↔Min/MaxLaunchAngle per
    projectile type; removed LaunchAngle from WarheadTrailProjectileCA; added
    missing MaximumLaunchAngle where Min>Max.
  - [x] UndefinedCursor chrono-target (195→0): Added `chrono-target` cursor
    sequence alias in cursors.yaml (hyphen variant of `chrono_target`).
  - [x] NegativeRemoval (64→0): Stripped values from `-Trait: value` removal
    lines across 15 weapon YAML files.
  - [x] InvalidWeaponField (55→0): Removed `WeaponClass` (40 lines, deprecated);
    fixed `Burstdelays`→`BurstDelays` (9); `BurstDelay`→`BurstDelays` (4);
    `Angle`→`LaunchAngle` on Bullet (1); removed weapon-level `ValidStances` (4);
    `ChangeOwnerValidStances`→`ValidStances` (2).
  - [x] DuplicateInteractable (234→0): Added `-Selectable:` to all bridge actors
    to remove inherited Selectable (which includes InteractableInfo), keeping
    only the explicit `Interactable:` with custom Bounds.
  - [x] MissingTooltip (39→0): Added `Tooltip` trait to `camera.gpssat`.
  - [x] OverrideActor on Tooltip (2→0): Removed invalid `OverrideActor` field
    from Tooltip traits in TD GDI vehicles and TD Shared aircraft.
  - [x] ProductionCost/TimeMultiplier RequiresCondition (10→0): Converted
    `RequiresCondition`→`Prerequisites` on ProductionCostMultiplier and
    ProductionTimeMultiplier in ^ScaledProducer template and 9 other instances.
    These traits use `Prerequisites:` not `RequiresCondition:`.
  - [x] ValidStances on AutoTargetPriority (3→0): Removed invalid `ValidStances`
    fields from AutoTargetPriority traits in outpost2.yaml.
  - [x] BadIndent (39): Investigated chrome/lobby_music.yaml — no actual
    indentation issues found. Likely false positive from engine miniyaml parser.

  **Error breakdown (2026-07-24, post-fixes):**
  - 72,813 UngrantedConditions — actors consume conditions not granted (biggest)
  - ~700 InvalidField — trait fields that don't exist on their trait (reduced
    from 761 after OverrideActor, ValidStances, RequiresCondition fixes)
  - 209 MissingSequences — images with no sequence definitions
  - 39 UndefinedNotification — missing notification references
  - 12 CannotParse — Cannot parse `Random` into LockFaction.Boolean
  - 11 UndefinedActor — husk actors not defined by any rule
  - 9 InvalidOwner — map actors with wrong owner
  - 4 InvalidChildNodes — traits with invalid child nodes
  - 2 MissingPrereq — buildable actors with unprovided prerequisites
  - 2 UnknownTrait — unknown traits in player.yaml
  - 1 MissingFluentVariable — missing fluent variable

  **Warning breakdown (2026-07-24):**
  - 62,640 UnconsumedConditions — actors grant conditions not consumed (biggest)
  - 375 UnusedFluentAttribute — unused fluent attributes in en.ftl files
  - 1 UnusedFluentVariable — unused fluent variable

  Phases: (1) palette fixes, (2) Interactable/Selectable conflicts, (3) missing
  FTL keys, (4) missing actor definitions [biggest], (5) unresolved prerequisites,
  (6) unused granted conditions [biggest warnings], (7) VisibilityType.Footprint,
  (8) invalid map factions, (9) MuzzleSequence/LaunchAngle/misc, (10) sequence
  warnings, (11) unused field/trait.

  **NOTE:** `utility.cmd cameo --check-yaml` takes 10+ minutes. Only run it
  after completing ALL connected fixes and expecting 0 errors/warnings. Do NOT
  run it repeatedly. Keep findings above updated in this section.

---

## D2k Faction Rollout — Atreides / Harkonnen / Corrino (2026-08-25)

**Coordinator:** Devin-Aurora.
**Canonical plan:** `docs/HANDOFF.md` §3.B.
**Driving requirement:** new Atreides and Harkonnen harvester sprites supplied by the maintainer; each of the three factions must have a completely unique tech tree and no shared units/assets with each other or with Ixian/Ordos.

### Phase 0 — Foundation (Devin-Aurora)
- [x] Add `mods/cameo/bits/d2k/atreides_harvester.png` and `mods/cameo/bits/d2k/harkonnen_harvester.png`.
- [x] Create `atreides_spiceharvester` and `harkonnen_spiceharvester` actors + sequences.
- [x] Update `refinery.atreides` and `harkonnen_refinery` `FreeActor` to spawn the new harvesters.
- [x] Create empty `Atreides/yaml/weapons.yaml` and load it from `Atreides/content.yaml`.
- [x] Boot-gate passes (`launch-game.cmd` reaches menu; `MenuPostProcessEffect.PostWorldLoaded` in `perf.log`; no new `exception-*.log`).
- [x] Scoped Phase 0 commit: `f07d8d35e` (D2k faction rollout: Atreides completion + Corrino creation + Ordos/Harkonnen additions + boot-gate fixes).

> **Phase 0 incident:** `ContentPacks/D2k/Ordos/yaml/sequences.yaml` had `ordos_laserturret` / `ordos_chemturret` `turret` sequences using `Length: 64` with `Facings: -64`, which requested 4096 frames from PNGs with 96 and 80 frames respectively. The turret definitions were corrected to `Facings: 32` (default `Length: 1`), which fits the PNGs' `FrameAmount` metadata. The new `ordos_lasertur.png` / `ordos_chemtur.png` assets and weapon definitions are owned by Devin-Echo; Devin-Echo should confirm the 32 facing turret layout.

> **Phase 0 out-of-scope addition:** Devin-Dawn created the `ContentPacks/D2k/Corrino/` skeleton and added it to `mods/cameo/mod.yaml`. This accelerates Phase 3 but is not part of the Phase 0 commit.

### Phase 1 — Harkonnen (Devin-Blaze)
- [x] Complete Harkonnen tech tree (infantry: lightinfantry, rockettrooper, engineer; vehicles; aircraft: carryall; defenses; upgrades; weapons; sequences).
- [x] Replace shared art references with unique `harkonnen_*` assets/actors where art exists; remaining placeholders flagged for art pass.
- [x] Enable `FactionCA@Harkonnen` and add `StartingUnits` (MCV/Light/Heavy) in `afdaae46c`.
- [x] Boot-gate + menu reached with zero new exceptions.

### Phase 2 — Atreides (Devin-Aurora) — COMPLETE in `f07d8d35e`
- [x] Complete Atreides tech tree: 15 buildings, 4 infantry, 5 vehicles, 1 aircraft, 5 upgrades, sequences.
- [x] Theme: noble house, air superiority, Fremen, faster construction.
- [x] Uncomment `FactionCA@Atreides`, add `StartingUnits` (MCV/Light/Heavy).
- [x] Boot-gate passed (menu in 60s, 0 new exceptions).
- [ ] Final `utility.cmd cameo --check-yaml` clean run (advisory lint remaining).

### Phase 3 — Corrino (Devin-Cyrus, then Devin-Aurora) — COMPLETE as of `af3ff5f9d`
- [x] Create `ContentPacks/D2k/Corrino/` skeleton (content.yaml, all yaml files, translations, mod.yaml include).
- [x] Theme: imperial Sardaukars, elite heavy infantry, uparmored harvesters, Death Hand support power.
- [x] Add `StartingUnits@corrino` once the full roster is in place (Ixian `faction.yaml` already references `corrino_mobileconstructionvehicle` and `corrino_sardaukar_bazooka`).
- [x] Boot-gate + `utility.cmd cameo --check-yaml`.
- [x] Add four Corrino Sardaukar variants: Berserker (melee axe), Swordmaster (melee blade), Javelin (ranged spear), and Laser (laser rifle), with sequences, weapons, and boot-gate.

### Phase 4 — Shared/global pass (Devin-Blaze + Devin-Echo) — IN PROGRESS
- [ ] Add shared D2k templates, fix cross-faction prerequisites, walls/turrets/superweapons/promotions.
- [ ] Remove dead legacy blocks from `mods/cameo/weapons/d2k.yaml` and `mods/cameo/rules/d2k.yaml` once their content has moved.
- [ ] Run `find_empty_warhead.py`, `review_resolve_diff`, `audit_warhead_split`, `extract_stats --check`, and the full `tools/audit/run_all.py` suite.
- [ ] Boot-gate; update all doc claims.

### Cross-phase rules
- Prefix every new actor/weapon/sequence/building with the faction name.
- No references to `ixian_*`, `ordos_*`, or generic global actors inside the new faction packs.
- All assets live in the repo (`mods/cameo/bits/d2k/<faction>/` or the pack's `files/`).
- Every new weapon follows W24 one-main-damage pattern; no duplicate same-family mains.
- Boot-gate before every commit.
