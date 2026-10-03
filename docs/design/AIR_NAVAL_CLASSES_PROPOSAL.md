# Air / Naval / Economy class proposal (LANE-5)

**Status: PROPOSAL ONLY.** Nothing here is decided; `class_anchors.json` is unchanged.
The maintainer rules, then someone else writes the anchors.
Author: EMBER (A1), `devin/ember/lane5-classes`. Data: `tools/balance/class_membership.py`
+ all `docs/balance/*.json` ledgers (observed spreads measured 2026-09-07 on
`70b0ddbcf`).

## The problem

`class_anchors.json` holds 27 classes and **none is air, naval, or economy**.
`class_membership.py` reports **222 real units** whose `design.subtype` has a valid
`^<Name>Template` but no class — the pipeline cannot price them.

## Observed member spreads (raw ledger evidence)

DPS is a rough estimate: Σ flat `damage_warheads[].damage` ÷ (`reloaddelay` +
(`burst`-1)·`burstdelays`) ticks × 25. Percentage warheads excluded. Negative DPS =
the armament list carries repair/utility payloads, not real weapons.

| subtype | n | HP (med) | cost (med) | speed (med) | range (med) | dps (med) |
|---|--:|---|---|---|---|---|
| `Helicopter` | 58 | 10k–1350k (70k) | 25–6000 (2000) | 30–200 (125) | 1448–12345 (5514) | ≈0–308k (31.8k) |
| `Bomber` | 34 | 5k–180k (53.7k) | 50–7000 (1450) | 35–250 (180) | 750–12500 (6204) | 4.2k–225k (43.2k) |
| `Fighter` | 22 | 7.5k–90k (37.5k) | 120–3500 (1000) | 75–260 (152) | 2000–9000 (6322) | ≈0–100k (10.1k) |
| `Spaceship` | 21 | 125k–3750k (400k) | 1500–15000 (5000) | 25–145 (45) | 2500–10000 (7030) | 4k–408k (23.3k) |
| `ScoutShip` | 22 | 20k–240k (95k) | 500–3600 (1300) | 55–140 (90) | 1250–24000 (8000) | 1k–118k (19.7k) |
| `AntiAirShip` | 1 | 90k | 1400 | 90 | 9000–10000 | ≈29k |
| `ArtilleryShip` | 16 | 70k–350k (237.5k) | 1750–4500 (3175) | 40–65 (50) | 8940–25000 (15000) | 1.5k–41.7k (32k) |
| `BattleShip` | 10 | 25k–250k (125k) | 600–2600 (1600) | 35–125 (85) | 7168–13500 (8854) | 8.3k–114.7k (31.9k) |
| `Harvester` | 30 | 25k–240k (110k) | 250–1200 (1000) | 38–125 (80) | 1333–5384 (1500) | (unarmed) |
| `UnarmedTransportHelicopter` | 9 | 50k–150k (100k) | 1500–6000 (3100) | 45–150 (125) | 4500–6000 (5250) | (unarmed) |

Outliers to know before setting anchors: `Helicopter` contains at least one 1.35M-HP
epic gunship and `Spaceship` a 3.75M-HP capital ship — medians, not means, are the
honest anchor seed. The `dps` column is indicative only; several members carry burst
payloads the estimate over-reads.

## Proposed classes (one per existing subtype — no invented subtypes)

| proposed class | members | analogue (existing ground class) | reasoning |
|---|--:|---|---|
| `helicopter` | 58 | `missile_vehicle` | mobile fire support, medium HP, weapon range ~5–6k; faster than its ground analogue — speed is the air premium |
| `bomber` | 34 | `artillery` | high-alpha delivery on a fragile platform; range/speed profile mirrors artillery's stand-off role |
| `fighter` | 22 | `scout_vehicle` | fast, cheap, light — the air interceptor; nearest analogue by cost/speed |
| `scout_ship` | 22 | `scout_vehicle` | cheap fast naval picket; the naval scout |
| `anti_air_ship` | 1 | `archer`/`scout_ship` | sole member is `gunb.asian` (Asian Gun Boat — becomes `asianalliance_gunb` if #424 lands): 1400 cost, 90k HP, ~9k-range flak + heavy cannon. A one-member class is degenerate — either grant it `anti_air_ship` seeded at its own stats, or explicitly fold `AntiAirShip` into `scout_ship` (its values sit inside that envelope either way) |
| `artillery_ship` | 16 | `artillery_tank` | long-range (15k med) slow naval bombardment — same role, water |
| `battleship` | 10 | `mbt` | the naval line unit: medium HP, medium range, does the fighting |
| `spaceship` | 21 | `dreadnought`/`high_tech_tank` | capital-tier: 400k-HP median, 5k-cost median — the late-game anchor class |
| `transport` | 9 | `support` | unarmed by definition; `support` already has `dps0: 0` — either reuse `support` or add `transport` for the higher HP/cost band |
| `harvester` | 30 | **none — economy** | FORMULA_V2 §6c does not cover economy units; propose either a `harvester` class priced on HP/speed/cost only (dps0=0) or an explicit pipeline exemption for economy units |

### Suggested anchor seeds (medians, for `fit_class.py` to validate)

| class | cost0 | dps0 | hp0 | range0 | speed0 | notes |
|---|--:|--:|--:|--:|--:|---|
| `helicopter` | 2000 | 30000 | 70000 | 5500 | 125 | trim epic outliers first |
| `bomber` | 1500 | 43000 | 55000 | 6200 | 180 | alpha, not sustained — verify against tick model |
| `fighter` | 1000 | 10000 | 37500 | 6300 | 150 | |
| `scout_ship` | 1300 | 20000 | 95000 | 8000 | 90 | |
| `anti_air_ship` | 1400 | 29000 | 90000 | 9000 | 90 | sole member's own stats; or fold into `scout_ship` per above |
| `artillery_ship` | 3200 | 32000 | 240000 | 15000 | 50 | |
| `battleship` | 1600 | 32000 | 125000 | 8850 | 85 | |
| `spaceship` | 5000 | 23000 | 400000 | 7000 | 45 | two cost bands visible (1.5k vs 15k) — possibly two classes |
| `transport` | 3000 | 0 | 100000 | 0 | 125 | `dps0=0` like `support` |
| `harvester` | 1000 | 0 | 110000 | 1500 | 80 | economy — pricing law TBD by maintainer |

## The 39 hand-tag-vs-template disagreements

`class_membership.py` reports them; explicit tags win by design. The disagreement
clusters tell their own story:

| cluster | rows | pattern |
|---|--:|---|
| `ScoutInfantry` tagged `support` (template: scout) | 6 | hand tag is one tier more passive than the template |
| `HeavyInfantry` → `special_forces`/`support` (template: heavy_infantry) | 7 | same direction |
| `AntiTankAntiAirInfantry` → `special_forces`/`archer`/`support`/`heavy_sniper` (template: rocket_trooper) | 10 | the largest cluster — hand tags scatter across four classes while the template says one |
| `SniperInfantry` → `support`/`special_forces`/`heavy_sniper`/`archer` (template: pure_sniper) | 8 | hand tags split across four classes |
| singles: `MeleeInfantry`, `MainBattleTank`→heavy_infantry, `FireSupport`→rocket_trooper, `ScoutVehicle`→scout, `LineBreaker`→closecombat, `Dreadnought`→high_tech_tank, `HeroInfantry`→commando | 8 | each a one-off |

**Recommendation: a per-row list, not a blanket rule.** The clusters look like drift
from the 18%-tag era — the same subtype getting 3–4 different hand tags
(`AntiTankAntiAirInfantry`, `SniperInfantry`) is what copy-paste divergence looks
like, not intent. But `MainBattleTank`→`heavy_infantry` and `HeroInfantry`→`commando`
smell like deliberate overrides (a unit that *behaves* heavier/stronger than its
template implies). Blanket-reverting to the template would silently erase real
judgment calls; blanket-keeping the tags preserves drift. The 39 rows need one
maintainer pass — the report lists each unit.

## What this does NOT propose

- No `class_anchors.json` edit — the anchor table is the maintainer's signature.
- No new subtype names — every proposed class name is an existing `design.subtype`.
- No change to `FORMULA_V2` — the `harvester`/economy gap is flagged for a ruling,
  not solved here.
