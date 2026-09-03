# Vehicle classification — DECISIONS NEEDED (curated review)

> ⛔ **ARCHIVED 2026-08-23 — not current.** Moved out of the live documentation set: it is either machine-generated (regenerate it rather than reading this copy) or the programme it belonged to is finished or dormant. Kept for provenance. Start at [`docs/HANDOFF.md`](../../HANDOFF.md).

_266 combat vehicles across 13 existing templates. Only REAL classification concerns below; pure intra-class stat spread is intentional (per-unit uniqueness) and handled in the stat-synthesis pass, not here._


## A. Baseline / verifier misplacement

- **scout_vehicle** verifier_actor: `terran_vulture` is on `LightTank` template — move to `ScoutVehicle`, or change the anchor pick.

## B. Misclassification candidates (need a class decision)

- **scout_vehicle** / `ra2_soviets_terrordrone` (Terror Drone) — scout without AA (§9: scouts fill AA role)
- **scout_vehicle** / `japan_grenadebuggy` (Grenade Buggy) — scout without AA (§9: scouts fill AA role)
- **scout_vehicle** / `protoss_positron` (Positron) — scout without AA (§9: scouts fill AA role)
- **artillery_tank** / `naxis_sturmtiger` (Sturm Tiger) — turretless → artillery (arty_tank is turreted)?
- **artillery_tank** / `ts_gdi_juggernautmkii` (Juggernaut MK II) — turretless → artillery (arty_tank is turreted)?
- **anti_air_vehicle** / `tkm_flakbus` (Flak Bus) — dedicated AA/missile but does NOT hit air
- **fire_support** / `ordos_dustdrone` (Dust Drone) — FireSupport hits air w/ missiles (rng6500) → missile_vehicle candidate
- **fire_support** / `futuretech_beehivedronecarrier` (Beehive Drone Carrier) — FireSupport hits air w/ missiles (rng17500) → missile_vehicle candidate
- **fire_support** / `naxis_nokana` (Nokana) — BuildLimit:1 → epic candidate (§18.1) [hp450000 cost3000]
- **fire_support** / `naxis_nokana` (Nokana) — FireSupport hits air w/ missiles (rng7000) → missile_vehicle candidate
- **fire_support** / `tkm_stryker` (TKM Stryker) — FireSupport hits air w/ missiles (rng7880) → missile_vehicle candidate
- **fire_support** / `zerg_lurker` (Lurker) — FireSupport hits air w/ missiles (rng6666) → missile_vehicle candidate
- **fire_support** / `td_nod_stealthtank` (Stealth Tank) — FireSupport hits air w/ missiles (rng7432) → missile_vehicle candidate
- **line_breaker** / `cabal_berserker` (Berserker) — BuildLimit:1 → epic candidate (§18.1) [hp800000 cost10000]

## C. §9 AA-gating backlog (DEFERRED — unit stays in class, but has an AA weapon to strip later; needs warhead permission) — 30 units

- **artillery** (2): `naxis_donnerschlag`, `cabal_artilleryspider`
- **artillery_tank** (1): `schwarzermond_mars`
- **mbt** (11): `ixian_mongoose`, `ordos_combatautoguntank`, `ordos_heavycombattank`, `latinsyndicate_smokertank`, `tkm_t72m`, `tkm_technicaltank`, `protoss_dragoon`, `terran_matador`, `td_gdi_battletank`, `td_gdi_predatortank`, `ts_nod_ticktank`
- **fire_support** (8): `ixian_stormraider`, `yuri_magnetron`, `futuretech_gunstrider`, `schwarzermond_korruptesbiest`, `japan_waveforcetank`, `zerg_sporemaw`, `ts_gdi_wolverine`, `ts_gdi_wolverinemkii`
- **line_breaker** (5): `ordos_heavyautoguntank`, `latinsyndicate_tortugatank`, `protoss_archon`, `td_gdi_assaultapc`, `ts_gdi_disruptor`
- **dreadnought** (3): `ixian_neocymek`, `asianalliance_pulverizermecha`, `terran_warhound`
