# Per-armament reference pairing

_Maintainer order, 2026-09-13:_

> "we need to be careful because those fire bombs and the sidewinder anti air missiles have
> separate ranges … Those two weapons are so different they should not be mixed. actually this
> should be true for **any dual or multi weapon units** so the correct weapon is mapped … you need
> to separate those two weapons, **use DTA for the missile as reference only while using the
> cannon reference from all 3!** Adjust all the existing units with that logic!"

This document is the ruling, the mechanism and the measurements. The code is
[`tools/balance/armament_roles.py`](../../tools/balance/armament_roles.py),
[`tools/balance/build_armament_pairing_report.py`](../../tools/balance/build_armament_pairing_report.py)
and the INI evidence extractors under [`tools/reference/`](../../tools/reference/). The contracts
are [`test_armament_roles.py`](../../tools/tests/test_armament_roles.py) and
[`test_ini_armament_roles.py`](../../tools/tests/test_ini_armament_roles.py).

---

## 1. The defect, measured

`reference_distribution.armament_profile` folds every baseline armament of an actor into ONE
`w_range` / `w_damage` / `w_dps`, and takes `max(ranges)` for the range. For a single-weapon unit
that is exactly right. For a dual-weapon unit it is a number about no weapon at all:

| actor | armament | role | range |
|---|---|---|---|
| `td_gdi_firehawk` | `…_firehawkmissiles_AA` | air | **12,500** |
| `td_gdi_firehawk` | `…_firehawkbomb` | ground | **1,250** |
| `td_gdi_mammothtank` | `…_120mmdual` | ground | 6,141 |
| `td_gdi_mammothtank` | `…_mammothmissiles` | both | 6,141 |

A ten-fold range gap inside one row. Measured over the whole tree (2026-09-13):

| | |
|---|---|
| priced actors | **940** |
| **actors whose unconditional armaments span more than one role** | **106** |
| …of those, still multi-role after `baseline_armaments` has run | 47 |
| air-role armaments the existing `_AA` NAME test cannot see | **50** |
| assigned actors whose reference row is contaminated by the fold | **39** |

⚠ **106 and 47 are different facts and an earlier draft of this document quoted the 47 as the
scope, understating it by more than half.** `reference_distribution.baseline_armaments` already
drops **59** of the 106 before anything downstream sees them — but it drops them by matching
`@AA` / `_AA` in the slot or weapon NAME, which is the guard §3b shows cannot see 50 real air
weapons. So 106 is the population the ruling covers, 47 is merely what survives a name test that
is itself unreliable. Registered as `armament_multi_role_actors` in `docs/audit/doc_claims.yaml`.

⛔ **THIS FIGURE WAS FIRST PUBLISHED AS 108 AND THAT WAS WRONG.** `audit_doc_claims` measured 106
against the same tree from the day the claim was registered; the 108 came from a hand count taken
while the module was still being written, and it was never re-derived from the artifact. The two
actors are not missing from anything — they were never in the population. Corrected 2026-09-13,
value and prose together, which is the whole reason the registry requires a `measure:` block.

## 2. Why the references can already fix it

Nothing needs re-extracting. All three corpora have carried per-armament data all along; only the
consumer folded it.

| side | where the armaments live | role evidence |
|---|---|---|
| Cameo | ledger `armaments[]` — slot, weapon, range, burst, burstdelays, reloaddelay, `requires` | the weapon's own `ValidTargets` / `InvalidTargets`, resolved |
| OpenRA peers | `weapon_evidence[]` — slot, weapon, range, reload_delay, burst, burst_delays, warheads, `requires_condition` | the armament's `valid_targets` |
| INI peers (DTA …) | `w_*` = `Primary=`, `w2_*` = `Secondary=` | the **projectile's** `AA=` / `AG=` flags |

410 peer rows carry `weapon_evidence`; **217 of them hold more than one armament.**

And the counterparts line up without a single name match:

```
CA   4TNK  130mm      ground 4864  |  MammothTusk      Air,AirSmall,Infantry   both 6656
CnC  HTNK  120mmDual  ground 4864  |  MammothMissiles  Ground,Water,Air        both 4864
RA   4TNK  120mm      ground 4864  |  MammothTusk      AirborneActor,Infantry  both 6656
DTA  HTNK  120mm      ground 5.7c  |  MammothTusk      AGHeatSeeker2           both 5.7c
```

## 2a. ONE WEAPON, ONE VOTE — the maintainer's model

Maintainer, 2026-09-13, when asked how far to wire this in:

> "the reference map needs to show each weapon per actor and try to find the weapon for each
> reference. **If the reference unit does not have the weapon it should not vote on it.** But yeah.
> Try to always find a reference weapon for each unit. … all 3 references vote on the cannon since
> all 3 references have that but only the DTA reference votes on the missile"

So the electorate is **per weapon, not per unit**. Three patterns fall out, and the counts are the
whole reviewable population (46 multi-weapon units with at least one structured reference):

| | | |
|---|--:|---|
| **A** | every source votes the first weapon, fewer vote the second | Hum-vee Mk II, `td_gdi_apc`, **`td_gdi_battletank`** |
| **B** | every source carries both weapons | the mammoths, `ra1_allies_destroyer` |
| **C** | the second weapon has no voter at all → **abstains** | `td_gdi_firehawk` |

⛔ **I GOT THE BATTLE TANK WRONG FIRST AND THE MAINTAINER CORRECTED IT.** Reading only
`Primary=`/`Secondary=` on DTA's `[MTNK]` shows a dummy and a 90 mm cannon, so I reported that DTA
has no missile and the Battle Tank therefore falls in pattern C. That was reading two of the unit's
**three** weapon declarations — `Elite=70mmMsl1` is a missile launcher, and it replaces the dummy.
§2b is the whole correction. `td_gdi_battletank` is pattern **A** and reads exactly as described:

```
ground  120mm         =  CA 120mm · DTA 90mm · TD 120mm    3 of 3 sources vote
both    m1a1missiles  ~  DTA 70mmMsl1 (elite)              1 of 3 sources vote
```

Maintainer ruling on the uncovered weapons (same exchange): **abstain and say so.** An armament no
source can reference gets no target and is shown as unreferenced, rather than being handed an
averaged number.

### 2b. THREE weapon slots, not two — `Elite=`

⛔ **THE MAINTAINER HAD TO SAY THIS TWICE.** A TS unit declares `Primary=`, `Secondary=` **and**
`Elite=`; `ini_corpus.json` carries only the first two, as `w_*` and `w2_*`. **171 DTA sections
declare `Elite=` and not one of those weapons reached the reference map.**

```
[MTNK]                                   [70mmMsl1]
Name=GDI Medium Tank                     Damage=30      Range=6.14
Primary=90mmDummy   ;ROF ... both        Projectile=AGHeatSeeker
Secondary=90mm                           Warhead=BazAP
Elite=70mmMsl1
```

The primary is a zero-damage **dummy** that exists only to set the rate of fire, so the GDI Medium
Tank's real loadout at elite is the 90 mm cannon **plus a 70 mm missile launcher** — *"on elite it
has one cannon and one missile launcher"*, exactly as stated. Reading two slots made it look like a
single-cannon tank, and that is why my first pass reported the Battle Tank's missile as having no
reference anywhere.

⭐ **`Trainable=` is the gate and the Enhance overlay flips it.** Measured 2026-09-13:

| | sections with `Elite=` | trainable | reachable in the corpus | an ADDITIONAL armament |
|---|--:|--:|--:|--:|
| DTA Classic | 171 | **0** | 0 | 0 |
| DTA Enhanced | 171 | 139 | **131** | **7** |

`[MTNK]` is `Trainable=no` in `Rules.ini` and `Trainable=yes` in `Enhance.ini`. The elite missile
exists in both rulesets and can only ever be FIRED in Enhanced. An extractor ignoring `Trainable`
would hand DTA Classic 159 corpus-referenced weapons no unit in that ruleset can reach.

⚠ **And most elite weapons are not a second weapon at all.** `Elite=` REPLACES the primary, so the
124 `E`-suffix entries (`RaiderCannonE`, `MinigunE`, `HellfireE`, `120mmE`) are the same gun
improved. Only where the primary is a zero-damage dummy does the elite weapon occupy a slot that
was otherwise empty — **7 units** — and only those are genuinely additional. Recorded per row as
`replaces_dummy_primary`. Elite weapons enter the bench as **rank-gated**: they never displace an
ordinary armament, they only fill a place nothing else can. The same weapon-evidence gate now
admits only **39 of 131** reachable elite records. A withheld replacement still suppresses its
base weapon for an expanded Cameo actor, so rejecting the elite cannot silently restore the
superseded lower-tier gun.

### 2c. The bench — a reference's SECOND weapon in a compatible role

Keeping only the strongest peer weapon per role lost the Battle Tank even after the elite slot
arrived. DTA's medium tank at elite has **two ground-role weapons** (the TS engine puts both the
90 mm cannon and the 70 mm missile launcher on the ground domain), while Cameo's battle tank has a
`ground` cannon and a `both` missile. The cannon claimed DTA's only ground candidate, and the
missile was then told no source covered its role.

⚠ **A DELIVERY AXIS WOULD NOT HAVE FIXED THIS HONESTLY.** The obvious idea — classify guided vs
unguided, match missile to missile — has no reliable source signal on the INI side. `ROT` (rate of
turn) reads like the homing field, but `TracerM`, an ordinary gun tracer, declares `ROT=1`, and
**426 of 433** sections that declare `ROT` are above zero. `Image=DRAGON` and `Warhead=BazAP` are
names, which is the trap this whole module exists to avoid.

So `candidates_by_role` keeps the whole bench, ranked by the per-cycle coordinate, and a Cameo
armament falling back to a compatible role takes the next unclaimed weapon there. No semantics
required. The result is the maintainer's own sentence:

```
td_gdi_battletank
  ground  120mm            =  CA 120mm  ·  DTA 90mm  ·  TD 120mm      3 of 3 vote
  both    m1a1missiles     ~  DTA 70mmMsl1 (elite)                    1 of 3 vote
```

⛔ **Clause 5 still binds: a zero-damage dummy is never anybody's reference.** The first bench
handed `90mmDummy` — a real armament with a real range whose only job is to set the next slot's
rate of fire — to the Battle Tank's missile.

### 2d. ⛔ STRUCK — a source that cannot state a role now ABSTAINS

**This section used to say the opposite, and the reversal is the ruling, not a bug fix.**

The original text: seven of the nine INI sources pin no `source_sha256`, so §4 refuses to state
their projectiles' domains and every one of their armaments arrives with `role = None`. Dropping
those views left `ra2_soviets_apocalypsetank` (5 sources), `ra2_allies_ifv` (5) and
`yuri_gatlingtank` (5) with zero votes, so a fallback let such a source vote on the main gun only,
ordered ground → both → air. That recovered 317 votes.

**Astra falsified the premise (PR #375 review, blocker 3).** The fallback picked the hardest-hitting
role-less weapon, and a *secondary* AA gun can out-damage its own chassis' main gun —
`FlakTrackAAGun` and `RA1RedEyeAA` were both being reported as **ground main-gun evidence**. That is
the one pairing this whole document exists to forbid, arrived at from the other direction: not by
mixing a cannon with a missile on the Cameo side, but by taking an anti-air gun as the reference.

Maintainer's ruling, 2026-09-13: *"ambiguous role or identity must abstain."*

So `_unproven_pair` and `UNPROVEN_PREFERENCE` are **deleted**. An unproven peer weapon never votes.
The cost is real, deliberate and counted rather than hidden:

| | before ruling | after ruling | current pinned evidence |
|---|--:|--:|--:|
| pairs | 607 | **308** | **332** |
| exact pairs | 213 | **215** | **226** |
| `both` stand-ins | 94 | 93 | 106 |
| unproven pairs | 300 | **0** | **0** |

The current increase is evidence, not a fallback returning: 59 exact-source pairs were admitted
and 35 old DTA pairs were withdrawn by the per-slot weapon gate, for a net +24. The Apocalypse
tank now gets one explicit Mental Omega vote for its AA missile; its ground cannon still abstains.
The ordering rule the deleted fallback encoded still lives where it came from, DESIGN's
`anti_air_vehicle` anchor and `reference_distribution.baseline_armaments`.

### 2e. WHICH weapon a reference offers depends on the Cameo actor's TIER

Maintainer, 2026-09-13:

> *"base version only for original units (with the exception for that dummy weapon of the MTNK)
> and elite versions or upgraded weapons for promotion units to get some power creep for late game
> or upgraded promotion units"*

and, stated as a constraint: *"A replacement must not also count beside its base weapon."*

| tier | who | which peer weapons are on the bench |
|---|---|---|
| `original` | an original-shipping mod matched it BY NAME | the **base** weapon only |
| `expanded` | promotion units, Cameo additions, CA/DTA inventions | the **elite/upgraded replacement**, *in place of* the weapon it replaces |

Measured: **140 original, 174 expanded** of the 314 priced actors with an assignment.

⛔ **`Elite=` REPLACES the slot it is declared against, so benching it beside its base weapon lets
one gun vote twice.** Astra found exactly that on FRIGATE, BEHEMOTH, YAK and HTNKARTY (blocker 1).
124 of DTA Enhanced's 131 reachable elite weapons are the `E`-suffix upgrade of a gun the unit
already fires — `MinigunE`, `120mmE`, `RaiderCannonE` — the same weapon, improved.

⭐ **MTNK's dummy is the exception and it is not a special case in the code.** It falls out of
`replaces_dummy_primary`: `[MTNK] Primary=90mmDummy` is a zero-damage rate-of-fire stub, so
`Elite=70mmMsl1` fills a slot that was otherwise empty and IS a second weapon. **Nine** DTA units
are in that state, and for them the elite weapon joins **both** tiers because it displaces nothing.
That is why `td_gdi_battletank` — an original — still references DTA's elite missile.

### 2f. Every Cameo armament pairs, not one per role

⛔ **Reducing Cameo to the strongest weapon per role was a second fold wearing the first one's
clothes** (Astra, blocker 2). `japan_oitank` carries OIFlamer, OIBigCannon and OISmallCannon — three
GROUND weapons — and reporting only the flamer is the same defect this lane exists to remove, one
level down. `ra1_allies_destroyer` has four. `cameo_armaments()` returns every referenceable
armament, hardest-hitting first, deduplicated on **(weapon, role)** rather than on the slot, because
`Armament@PRIMARY` and `Armament@GARRISONED` are one gun fired from two places.

The same gate was wrong in the report: the actor-level cell is withheld for carrying more than one
ARMAMENT, not more than one ROLE, so 17 withheld actors were blanked above and had no per-armament
block below either.

### 2g. Unknown target tokens FAIL CLOSED

⛔ Astra, blocker 5: `Ground, UnknownFlyingTarget` came back a **proven exact ground** vote. The
classifier used to return a confident role alongside the unrecognised tokens, treating them as
neutral on the theory that a new marker must never silently flip a domain. That theory is a guess,
and guessing from tokens is the exact failure this module was built to avoid — DTA's
`AGHeatSeeker2` says "AG" in its name and declares `AA=yes`.

`role_of_targets` now returns `None` whenever any token is unrecognised, and an unproven weapon
does not vote (§2d). The tokens are still reported, because `--audit` proves the vocabulary covers
the corpus: it is **0 today**, which is exactly when this guard is cheap to install.

### 2h. Evidence fingerprints are enforced where the evidence is CONSUMED

⛔ Astra, blocker 4: *"Evidence hashes are recorded but not enforced when consumed."* Both
extractors refuse to run unless the INI they read hashes to the pin the corpus carries — and then
wrote a JSON that any later process could consume months after the corpus moved underneath it.
**A recorded hash that nobody re-checks is a comment.**

Two layers now check, and both work without the 9.9 GB reference folder, using only files the
repository holds:

* `extract_ini_projectile_roles.load()`, `extract_ini_armament_roles.load()` and
  `extract_ini_elite_weapons.load()` re-verify each source's byte pin against `ini_corpus.json`.
  The seven-source armament loader also rechecks the corpus weapon-link fingerprint. A moved pin
  or binding drops that source, per source, and is exposed on `load.dropped`.
* `armament_pairing.json` records an `inputs` block for the complete reproducibility closure: the
  INI corpus and extracted evidence, selected OpenRA peer corpora, Cameo balance ledgers, active
  manifest/rules/weapons, and direct tool dependencies. `build_reference_report.pairing_document()`
  rebuilds that exact set and **raises** on a missing, extra, or changed input rather than rendering
  stale evidence as current. Missing, malformed, empty, or unsupported artifacts are refused for
  the same reason — they cannot prove they are fresh. Repository text is hashed after canonicalising
  LF/CRLF so the same commit verifies across checkout policies; the peer-corpus and INI extractors
  still enforce their separate raw-byte source pins.

Stale evidence is worse than missing evidence, because it looks exactly like the real thing.

### 2i. The attack cycle includes the CHARGE — ruled, and NOT yet applied

The law, as the maintainer states it (2026-09-14):

```
DPS = damage x burst / attack cycle
attack cycle = reload delay + sum of ALL burst delays + charge delay
```

⚠ **"DPS" is a name, not a unit — it is damage per TICK.** Every rate in this lane, in the ledger
and on the map is per tick.

One thing DOES reach the cycle from outside the weapon today: **the trait can override the reload.**
`AttackTesla`'s own `ReloadDelay` is the cycle, `MaxCharges` is the burst, and the WEAPON's reload
is the gap between zaps (`formula.charge_attack_cycle`, shipped in #385). Reading the weapon alone
reported a Tesla Coil, whose weapon reloads every 3 ticks, as firing twenty times a second.

⛔ **THE CHARGE TERM ITSELF IS WITHHELD, AND THAT IS A DECISION, NOT AN OVERSIGHT.** I implemented
it and Astra's engine trace held it (PR #386), correctly. Three shapes break a naive `cycle + ticks`:

* **multi-shot `ChargeLevel`** — the burning Obelisk is Burst 10 / BurstDelays 1, and its
  `AttackCharges` notifier resets `ChargeLevel` on every projectile, so later shots must recharge.
  Its period is not `105 + 50`.
* **interleaved `AttackTesla`** — the maintainer ruled that the Rail
  Tower *"needs to charge for every shot unlike the tesla coil ... at 5 shots the initial charge
  delay is used 5 times"*. The immediate-reacquisition model gives `160 + 5 x 12 = **220**` — #385's 160 never paid the
  charge and my 172 paid it once; both were wrong. A charged weapon is one of two machines,
  **charge-once** or **charge-per-shot**, differing by a factor of `MaxCharges`.
  `ChargeFire` does not spin while the
  weapon reloads — it EXITS, because `AttackBase.CanAttack` calls
  `HasAnyValidWeapons(reloadingIsInvalid: true)` and a reloading armament makes it false.
  `ChargeAttack` has the same guard, so the activity ends and the actor re-enters through
  `ChargeAttack`, paying `InitialChargeDelay` again. The detection is therefore exactly the
  comparison Astra named: **`ChargeDelay` against the weapon's reload** — `reload <= ChargeDelay`
  is charge-once with `gap = ChargeDelay`; `reload > ChargeDelay` is charge-per-shot. The latter
  gap is `reload + reacquisition + InitialChargeDelay`. `tools/balance/sim_attack_tesla.py`
  reproduces 131, 95 and **220** only with explicit zero-tick reacquisition. The real Rail Tower
  inherits randomized 3–7 tick AutoTarget scans, which the simulator does not model, so its fixed
  runtime period remains unmeasured.
  ⛔ **My 172 and 180 are both WITHDRAWN** — they shared the false premise that `ChargeFire`
  keeps ticking through the reload, and Codex and Astra caught it. #385's 160 never paid the
  charge. Applying any of this still needs `ChargeDelay` and the weapon reload in the extractor.
* **random `ChargeLevel`** — ⭐ **CLOSED, and it shipped.** `steelconsortium_dagger` declares
  `ChargeLevel: 25, 50`; `extract_stats` kept only the lower bound. Maintainer ruled 2026-09-14 to
  **use the MEAN of min and max**, added to the reload, so the Dagger contributes **37.5** and
  `wc2_humans_dwarvenrifleman`'s `0, 4` becomes **2**, not zero. `extract_stats.charge_scalar`
  implements it and all four ranged actors were re-extracted.
  ⛔ **The dwarf is the case that mattered, and it made the unit DEARER.**
  `charge_price_multiplier` treats `share <= 0` as *charges, but we cannot see by how much* and
  returns the FLAT 0.75 floor — so the misparsed zero was collecting the deepest discount in the
  table. Its real 2 ticks against a 60-tick reload move it to **0.976**. The Dagger's own figure
  does not move (0.750, already clamped at the floor) and the two siege engines go 0.875 → 0.827.
  ⚠ The reference path is untouched: `charge_attack_cycle` returns `None` for the whole
  `ChargeLevel` family, so the regenerated `armament_pairing.json` changed only its three input
  fingerprints.

⭐⭐ **CLOSED, AND THE CHARGE TERM IS APPLIED (2026-09-14).** Range-ness resolves at
extraction, and `ChargeDelay` is now recorded too — the engine default 3, written by no actor,
which is precisely why the mode was undecidable. `charge_attack_cycle` therefore tells
charge-once from charge-per-shot by comparing it against the WEAPON's reload, and prices
**131 / 95 / 210**. Counting the wind-up cut the Tesla Coil's rate 19% and the Rail Tower's
24%: both had been read as firing faster than they do.

⚠ `ShotsPerCharge` stays unrecorded and matters only to the `ChargeLevel` family, which
deliberately did NOT move — it delays a gun that keeps its own reload, so it cannot say what a
cycle is. ⛔ And what is priced is the FLOOR: a charge-per-shot actor goes idle between shots
and re-enters on `AutoTarget`'s `Next(3, 8)` = U{3..7} scan. A 300-seed sample reports
210 minimum / 218 mean / 232 maximum, but a legal scan path reaches 234, so the sample maximum
is not a ceiling. Baseline coil states are invariant when exactly one armament is enabled.
Withholding is the same answer this lane gives
everywhere else: an unprovable quantity abstains.

⛔ **THE POPULATION IS SMALLER THAN IT LOOKS, AND I OVERSTATED IT.** 14 actors carry a `charge_up`
record, but that is not 14 actors whose reported cadence would move. **Three are `AttackTesla`; the
other eleven are `ChargeLevel`-family records** — a different trait with a different schedule, not
units inheriting an engine default, which is how I first explained it and was wrong.
`ra1_allies_mobileradarjammer` has **no priced armament view at all**,
`wc2_humans_dwarvenrifleman` winds up for **2** ticks against a 60-tick reload (it declares
`0, 4`; the averaging ruling has landed, so this is no longer the zero it used to read), and
`terran_siegetank` keeps 37 under the ownership guard. I published a table claiming the siege
tank at 62 and the burning Obelisk at 155; **both were wrong** — measured before I adopted #385's
guard, and never re-measured after. Counting records is not counting effects.

⛔ **AND `charge_attack_cycle` RETURNING `None` DOES NOT MEAN "NO CHARGE TIME".** It says only that
the trait does not override the weapon's RELOAD. Both #385 and I read it the other way first.

## 3. The pairing key is the targeting envelope

Not the weapon's name. The vocabulary is **the maintainer's own missile ruling of 2026-09-07**,
reused rather than re-derived:

| ValidTargets | role | missile family (DESIGN, §missile role law) |
|---|---|---|
| ground only | `ground` | `^Warhead_MissileHE_*` |
| air only | `air` | `^Warhead_MissileAA_*` |
| both | `both` | `^Warhead_MissileAP_*` |
| neither (an interceptor, a healer, a snare) | `special` | — |

Three rules make it safe:

* **Absent `ValidTargets` is `Ground, Water`,** the engine default (`WeaponInfo.cs:116`) — 451 of
  the ~900 peer armaments leave it unwritten, so reading absence as "unknown" would abstain on half
  the corpus.
* **`InvalidTargets` subtracts** before the domains are read.
* **An unclassified token fails closed AND is reported.** The weapon abstains rather than deriving
  a role from the recognised subset, and `armament_pairing.json` lists every unknown token. Today
  that list is **empty**: the three measured token sets cover both corpora completely.

`air` and `ground` are the one forbidden pair. `both` is adjacent to everything, so an exact role
claims its partner first and only then may a `both` stand in — otherwise a cannon claims the peer's
dual-role missile before the missile gets a turn.

### 3a. Why this does not replace `audit_missile_role_family.weapon_role`

That function fails closed to `custom` on any token outside `{Ground, Water, Air}`, which is right
for a check driving four LOWER-ONLY ratchets and useless for pairing — `Ground, Water, Trees` is 31
CA armaments and `AirborneActor, Infantry` is the entire Red Alert mammoth missile. The pairing
classifier reads a wider, explicitly enumerated vocabulary and still fails closed on the unknown.
`test_agrees_with_the_missile_role_audit` pins that the two never disagree on a weapon the audit is
willing to judge: **the wider set may only add answers.**

### 3b. Why it does not replace `is_anti_air_armament` either

That helper tests the slot/weapon NAME (`@AA`, `_AA`) and is load-bearing for the existing baseline
selection, so it is untouched. But it cannot see 50 air-role armaments spelled otherwise —
`RA2Patriot`, `RA2TURRETFLAKAA`, `AsianPhotonCannon`, `PortableFlak`, `BallistaSingleShotAir` — and
a name blocklist is the mistake this codebase has paid for repeatedly. **The envelope is the
source; the spelling is a convention.**

## 4. The INI half: `AA=` / `AG=`, never the name

The TS/RA2 engine has no `ValidTargets`. A weapon's domain lives on its **projectile**, as two
booleans, and the corpus rows carry only the projectile's name. `extract_ini_projectile_roles.py`
reads the real flags out of `Rules.ini` with `$Inherits=` flattened, and writes
`docs/reference/ini_projectile_role_evidence.json`.

⛔ **The name is a trap, and it is the exact case the maintainer asked about.** DTA's mammoth Tusk
flies `[AGHeatSeeker2]` — "AG" right there in the section name — which declares
`$Inherits=AGHeatSeeker` and then `AA=yes`. It is a **dual-role** missile, which is what makes it
the correct partner for Cameo's `MissileAP_Heavy` and CA's `MammothTusk`. A name classifier calls
it anti-ground and pairs an air missile against a cannon.

Coverage: **DTA Classic 57/57 and DTA Enhanced 60/60** cited projectiles resolved, nothing
undeclared. A projectile declaring neither flag takes the engine default (`AA=no`, `AG=yes`), which
is recorded in the file as an explicit assumption with its basis — and each verdict says which half
was declared and which was defaulted.

The other seven exact INIs are SHA-256 pinned, and `ini_source_pins.py` verifies all **10,144**
existing corpus rows against their actor Primary/Secondary slots and weapon-to-projectile links.
It preserves the historical 64 promoted-secondary occurrences (63 identities) without approving
those selections. The third-party text remains outside git.

`extract_ini_armament_roles.py` adds the missing evidence gate without regenerating the corpus.
For each cited weapon it binds the exact weapon/projectile link to freshly read range, damage,
reload, burst and targeting flags. RA2/YR contributes only when **both** resolved `AA` and `AG`
values are explicit and valid; missing defaults abstain because no authoritative RA2 default is
pinned. Twisted Insurrection uses the documented TS defaults. Invalid booleans never coerce to
false. A weapon must also be `nominal_direct` and carry usable positive finite numbers. The
consumption path admits otherwise-proven `burst_unfolded` records with one tick per inter-shot gap;
resolved sidecar status, targeting and integral positive burst remain required. Other incomplete
or effect records abstain. Preserve the frozen corpus and its promoted-secondary selections.

The exact extractor disposition remains in the evidence sidecar. DTA keeps its independently
pinned projectile evidence, while its primary, secondary and elite slots pass the same
`nominal_direct`/usable/numeric gate and the reviewed `burst_unfolded` consumption rule. The DTA hashes remain
`786f0ae5…` for `Rules.ini` and `d836d5a9…` for `Enhance.ini`.

### 2j. Application components stay per armament, and frozen self-votes are explicit

`armament_pairing.json` schema 3 retains each matched weapon's authored reload, burst and burst
delays beside its modeled cycle. These are different facts: `AttackTesla` can model three logical
zaps while the weapon itself remains Burst 1, and reviewed INI cycles can include charge or jitter
that must not be reverse-engineered into authored YAML fields.

The reference map now projects range, damage per cycle and reload from the same role-paired weapon.
Burst keeps the existing discrete law: median within each external source, then median across
sources, without a Cameo self-vote. Continuous component targets add the immutable Cameo value as
one equal vote only when a hash-pinned singleton receipt identifies the historical priced slot and
weapon. The first such receipt is
`docs/reference/cameo_singleton_armament_self_votes_20260914.json`, limited to the TD GDI and Nod
Rocket Soldiers. A current one-armament count is not historical proof and cannot create a new
self-vote by itself.

The component DPS verifier is withheld when the modeled actor cycle differs from the authored
weapon reload plus burst gaps. This prevents charge, reacquisition or reviewed source jitter from
being flattened back into weapon fields during application. A fractional burst or burst-delay
target is also held and withholds the verifier; it never falls back to the current integer while
the same row displays a rejected proposal.

## 5. What the pairing currently reports

`python tools/balance/build_armament_pairing_report.py --write`

| | |
|---|---|
| actors with a priced armament in the assignment | 314 |
| …referencing a peer's BASE weapon (original) | 140 |
| …referencing the elite/upgraded replacement (expanded) | 174 |
| actors firing in more than one role | 45 |
| **reference rows contaminated by the fold** | **44** |
| armament pairs formed | **353** |
| …proven exact role matches | 238 |
| …a dual-role `both` weapon stood in | 115 |
| …source could not state a role | **0 — they abstain** (§2d) |
| …the reference carries that weapon only at ELITE rank | 4 |
| pairs by role | ground 194 · both 131 · air 28 |
| Cameo armaments with no reference | 378 |
| actors with at least one uncovered armament | **119** |
| uncovered armaments despite structured references | ground 93 · both 36 · air 18 · special 2 |
| actors with no structured reference at all | 16 |
| unknown target tokens | **0** |

The historical 2026-09-14 all-faction review page is
`docs/audit/latest/reference_map_clean_20260911.html`. That snapshot covers **29** non-WIP
faction prefixes and excludes the two explicitly WIP Dark Reign factions (`plymouth`, `eden`);
it contains 161 original and 709 expanded actors, 925 attached references, 514 formula-priced
actors and 8 rendered originals with fewer than three sources. It was not regenerated in this
batch. The current classic-four review is
`docs/audit/latest/Cameo-reference-map-original-four-20260916.html`: 76 original and 87 expanded
actors, 297 attached references, 27 formula-priced actors and 4 originals with fewer than three
sources, generated from the current branch.

The 2026-09-14 missing-reference review added ten exact, previously unclaimed mappings: the
Valiant Shades Allied/Soviet Engineers, four source-specific Soviet Sentry Guns, Shattered
Paradise's GDI MCV, Crystallized Nexus's Mobile Sensor Array, and the Shattered Paradise/Twisted
Insurrection Nod Militants for TS Nod Light Infantry. Four original actors reached the
three-source floor; the engineers improved from one to two references. The bot-only empty
Battle Fortress variant did not take the `BFRT` rows already owned by the real Battle Fortress.
The O1 audit now lists each faction's actual routed candidates rather than incorrectly reporting
Combined Arms and DTA as missing sources for every RA2 and Tiberian Sun actor.

⚠ **THE PAIR COUNT REMAINS FAR BELOW 607 BECAUSE THE UNPROVEN FALLBACK STAYS DELETED.** The current
artifact on this branch, based on master `102645047`, has 353 pairs: 238 exact and 115 via the legal `both` fallback.
`cameo_armaments_without_a_reference` remains large (378) because every armament is counted rather
than one per role, so a four-gun destroyer reports four gaps where it used to report one.

⚠ **TWO REASONS A WEAPON ENDS UP UNREFERENCED, AND COUNTING THEM TOGETHER MAKES THE NUMBER LIE.**
The report separates actors whose assigned peers expose no structured armament rows at all from
weapons left uncovered despite at least one structured peer row. Structure exists independently of
whether a particular weapon found a compatible match: a structured zero-match row is evidence of a
gap, not missing structure.

Coverage is also tracked by **weapon identity**, not merely by role. The earlier role-level count
said only seven actors were uncovered because one successful ground match could hide another ground
weapon on the same actor. The current report exposes 149 structured-reference gaps on 119 actors
(ground 93, both 36, air 18, special 2). That
is an honest inventory for later reference work, not a licence to invent votes. For example,
`td_gdi_firehawk` remains correctly uncovered for its Sidewinders when its A-10 references carry no
anti-air weapon; the source abstains instead of averaging those missiles with a napalm bomb.

## 6. What this deliberately does NOT do

* It does not re-score or re-assign anything. Clause 2 of the matching law (one reference unit per
  source, per Cameo unit) is untouched — this splits what a pair MEANS, not which pair it is.
* It writes **no balance number**. Rules 3 and 4 stand: the ledger is the only route, and
  `apply_balance --confirm` needs a maintainer order.
* It does not change `armament_profile`, `baseline_armaments` or `is_anti_air_armament`. Retiring
  the fold in favour of per-role targets is the next step and it is a **model change**, so it needs
  the maintainer's word before it lands.
* ⛔ **Superweapons are excluded everywhere upstream and nothing here reaches them.**
