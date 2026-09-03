# Baseline Audit — Findings by Bug Class

> ⛔ **ARCHIVED 2026-08-23 — not current.** Moved out of the live documentation set: it is either machine-generated (regenerate it rather than reading this copy) or the programme it belonged to is finished or dormant. Kept for provenance. Start at [`docs/HANDOFF.md`](../../HANDOFF.md).

> **Stale-date notice:** This file was generated from a baseline audit run.
> File paths in the tables below reflect the pre-restructure directory layout
> (e.g., `rules/vehicles.yaml` → now `yaml/vehicles.yaml` after the ContentPack
> restructure). Regenerate via `tools/audit/run_all.sh` for current paths.

_Generated from the `tools/audit` baseline run at this commit, curated per
`docs/MASTER_REPORT.md` §4. Severity: **crash** (player-facing failure),
**balance** (silently wrong stats/economy), **cosmetic** (visual/text),
**hygiene** (dead weight, drift risk). Exhaustive machine-generated tables
live in `docs/audit/baseline/` — this file is the human triage layer on top.
The engine's own `utility --check-yaml` output (deduplicated, with per-map
occurrence counts) is committed as `baseline/check_yaml_dedup.txt` and
corroborates the dangling-reference findings below._

Quick artifact map: `inherits.md` (B2) · `faction_leaks.md` (B1) ·
`upgrades.md`/`upgrade_coverage.md` (B3/B4) · `ai.md` (B5) · `sequences.md`
(B6) · `metadata.md` (B7) · `outliers.md` (B9) · `orphans.md` (B10) ·
`assets.md` (B11) · `fluent.md` (B12) · `power_budget.md` (R2) ·
`naming.md` + `tools/rename/rename_map_*.yaml` (§9.1) ·
`damage_matrix.md` (§8.1) · `../factions/MATRIX.md` (§5.1).

---

## B8 — Crash-class content (fix first)

| finding | evidence | severity | minimal fix |
|---|---|---|---|
| `casinocrate` crate action fires nonexistent weapon `TSChemTacticalMissile` | `mods/cameo/rules/misc.yaml`, `ExplodeCrateAction@chem` (orphans.md O2) | **crash** on crate pickup | point at `TSTacticalChemMissile` (exists) or delete the action |
| `fiendspawner` warhead spawns unpositionable actor `tsdoggiew` | check_yaml: "Warhead type fiendspawner tries to spawn unpositionable actor tsdoggiew!" | **crash** when the spawn resolves | give `tsdoggiew` a positionable trait set or spawn `tsdoggie` |
| StartingUnits reference 5 missing actors: `tsbike2`, `tsttnk2`, `steel_qtank`, `steel_qutnk`, `technicaltank` | check_yaml `world.StartingUnitsInfo.SupportActors` (68–136 hits) | **crash/blocked spawn** for those starting-unit lobby options | re-point to the renamed live actors or drop from the lists |
| `tsarnd` (CABAL Eliminator 800) Armament names undefined `muzzle` sequence on image `tsarnd` | check_yaml, 102 hits | cosmetic today, **crash-risk** under strict sequence lookup | add the `muzzle:` sequence or drop `MuzzleSequence` |

`check_yaml_dedup.txt` holds the full engine-side list (~10.6k unique
mod-level errors once map duplication is removed); most are B6-class
sequence/actor references in **unloaded or map-only content** — triage the
subset above first because live gameplay paths reach them.

---

## B1 — Cross-faction actor leaks

**L1 — buildable by faction X, owned by faction Y (10):** the Ordos closure
reaches Harkonnen/Ixian combat units and Syndicate reaches Asian/Naxis
vehicles. If these are intended "market/mercenary" mechanics they need an
explicit shared home (§9.3) — otherwise they are prerequisite-gating bugs.
Severity: **balance**.



| faction | actor | attributed owner | file |
|---|---|---|---|
| syndicate | ptnk.asian | redalert2mod/asianalliance | mods/cameo/ContentPacks/RedAlert2Mod/AsianAlliance/rules/vehicles.yaml |
| syndicate | tiger.nax | redalert2mod/naxis | mods/cameo/ContentPacks/RedAlert2Mod/Naxis/rules/vehicles.yaml |
| syndicate | wirbelwind.nax | redalert2mod/naxis | mods/cameo/ContentPacks/RedAlert2Mod/Naxis/rules/vehicles.yaml |
| ordos | combat_tank.harkonnen | d2k/harkonnen | mods/cameo/ContentPacks/D2k/Harkonnen/rules/vehicles.yaml |
| ordos | combat_tank.ixian | d2k/ixian | mods/cameo/ContentPacks/D2k/Ixian/rules/vehicles.yaml |
| ordos | duelist_tank.ixian | d2k/ixian | mods/cameo/ContentPacks/D2k/Ixian/rules/vehicles.yaml |
| ordos | heavy_inf.ixian | d2k/ixian | mods/cameo/ContentPacks/D2k/Ixian/rules/infantry.yaml |
| ordos | heavy_rocket_raider.ixian | d2k/ixian | mods/cameo/ContentPacks/D2k/Ixian/rules/vehicles.yaml |
| ordos | rocket_raider.ixian | d2k/ixian | mods/cameo/ContentPacks/D2k/Ixian/rules/vehicles.yaml |
| ixian | combat_tank.harkonnen | d2k/harkonnen | mods/cameo/ContentPacks/D2k/Harkonnen/rules/vehicles.yaml |


**L3 — buildable inherits a concrete actor owned by another faction (13):**
the classic reskin pattern (CABAL/Forgotten/TS-Nod service buildings
inheriting GDI/Nod concrete actors). Every one is a latent Slave-Miner bug:
retuning the parent silently retunes the child. Severity: **balance-risk**;
fix = extract shared `^Templates` during the §10.4 migration.



| faction | actor | inherit target | target owner | file |
|---|---|---|---|---|
| tsnod | tsgtdeptnod | tsgtdeptgdi | tsgdi | mods/cameo/rules/tiberiansun.yaml |
| tsnod | tsgtsilonod | TSGTSILO | tsgdi | mods/cameo/rules/tiberiansun.yaml |
| tsnod | tsprocnod | tsprocgdi | tsgdi | mods/cameo/rules/tiberiansun.yaml |
| forgotten | tsgtdeptmutant | tsgtdeptgdi | tsgdi | mods/cameo/rules/tiberiansun.yaml |
| forgotten | tsgthpadmutant | tsgthpad | tsgdi | mods/cameo/rules/tiberiansun.yaml |
| cabal | tscabaltech | tsgttech | tsgdi | mods/cameo/rules/tiberiansun.yaml |
| cabal | tsgtdeptcabal | tsgtdeptgdi | tsgdi | mods/cameo/rules/tiberiansun.yaml |
| cabal | tsgtsilocabal | TSGTSILO | tsgdi | mods/cameo/rules/tiberiansun.yaml |
| cabal | tsnthpad2 | tsnthpad | tsnod | mods/cameo/rules/tiberiansun.yaml |
| cabal | tsntmislcabal | tsntmisl | tsnod | mods/cameo/rules/tiberiansun.yaml |
| cabal | tsntobelcabal | tsntobel | tsnod | mods/cameo/rules/tiberiansun.yaml |
| cabal | tsntradrcabal | tsntradr | tsnod | mods/cameo/rules/tiberiansun.yaml |
| cabal | tsntstlhcabal | tsntstlh | tsnod | mods/cameo/rules/tiberiansun.yaml |


1,106 buildables are shared/unattributed (mostly legitimately neutral or
monolith-file content) — full list in `faction_leaks.md`, **needs human
decision** during Phase-1 folder moves.

---

## B2 — Inherits (§10.3 invariants)

Counts on the live tree: **V1 = 328** concrete→concrete inherits,
**V2 = 24** crossing faction ownership, **V3 = 0 dangling** (the engine
would not boot otherwise), V4 = 1,639 chains deeper than 3 (informational
until Phase 1 — today's template stacks are legitimately deep), V5 = 91
actors with >2 trait removals (template-mismatch smell).

### V2 — every cross-faction inherit (full list)



| actor | actor faction | target | target faction | file |
|---|---|---|---|---|
| TSGTSILOCABAL | cabal | TSGTSILO | tsgdi | mods/cameo/rules/tiberiansun.yaml |
| TSGTSILONOD | tsnod | TSGTSILO | tsgdi | mods/cameo/rules/tiberiansun.yaml |
| awall.asian | redalert2mod/asianalliance | BRIK | tiberiandawn/shared | mods/cameo/ContentPacks/RedAlert2Mod/AsianAlliance/rules/buildings.yaml |
| carryall.ordos | d2k/ordos | carryall | d2k/shared | mods/cameo/ContentPacks/D2k/Ordos/rules/aircraft.yaml |
| carryall_reinforce.ordos | d2k/ordos | carryall.reinforce | d2k/shared | mods/cameo/ContentPacks/D2k/Ordos/rules/aircraft.yaml |
| engineer | d2k/shared | E6 | tiberiandawn/shared | mods/cameo/ContentPacks/D2k/Shared/rules/infantry.yaml |
| heavy_factory.ixian | d2k/ixian | heavy_factory | d2k/shared | mods/cameo/ContentPacks/D2k/Ixian/rules/buildings.yaml |
| heavy_factory.ordos | d2k/ordos | heavy_factory | d2k/shared | mods/cameo/ContentPacks/D2k/Ordos/rules/buildings.yaml |
| light_factory.ordos | d2k/ordos | light_factory | d2k/shared | mods/cameo/ContentPacks/D2k/Ordos/rules/buildings.yaml |
| tran.gdi | tiberiandawn/gdi | TRAN | tiberiandawn/shared | mods/cameo/ContentPacks/TiberianDawn/GDI/rules/aircraft.yaml |
| tran.nod | tiberiandawn/nod | TRAN | tiberiandawn/shared | mods/cameo/ContentPacks/TiberianDawn/Nod/rules/aircraft.yaml |
| tscabaltech | cabal | tsgttech | tsgdi | mods/cameo/rules/tiberiansun.yaml |
| tsgtdeptcabal | cabal | tsgtdeptgdi | tsgdi | mods/cameo/rules/tiberiansun.yaml |
| tsgtdeptmutant | forgotten | tsgtdeptgdi | tsgdi | mods/cameo/rules/tiberiansun.yaml |
| tsgtdeptnod | tsnod | tsgtdeptgdi | tsgdi | mods/cameo/rules/tiberiansun.yaml |
| tsgthpadmutant | forgotten | tsgthpad | tsgdi | mods/cameo/rules/tiberiansun.yaml |
| tsnthpad2 | cabal | tsnthpad | tsnod | mods/cameo/rules/tiberiansun.yaml |
| tsntlasrcabal | cabal | tsntlasr | tsnod | mods/cameo/rules/tiberiansun.yaml |
| tsntmislcabal | cabal | tsntmisl | tsnod | mods/cameo/rules/tiberiansun.yaml |
| tsntobelcabal | cabal | tsntobel | tsnod | mods/cameo/rules/tiberiansun.yaml |
| tsntradrcabal | cabal | tsntradr | tsnod | mods/cameo/rules/tiberiansun.yaml |
| tsntstlhcabal | cabal | tsntstlh | tsnod | mods/cameo/rules/tiberiansun.yaml |
| tsprocnod | tsnod | tsprocgdi | tsgdi | mods/cameo/rules/tiberiansun.yaml |


### V1 — every concrete→concrete inherit (full list, grouped by owner)

Severity: **balance-risk** as a class. These are the §12 Phase-1 work queue —
each one gets replaced by a `^Template` extraction, verified by
`dump_resolved.py` before/after diffs.


**?** (264):

| actor | inherits | target faction | file |
|---|---|---|---|
| A10.Husk | MIG.Husk | ? | mods/cameo/rules/husks.yaml |
| A10Carrier.Husk | A10.Husk | ? | mods/cameo/rules/husks.yaml |
| BADR.Allies | BADR | ? | mods/cameo/rules/redalert.yaml |
| BADR.Bomber | BADR.Soviet | ? | mods/cameo/rules/redalert.yaml |
| BADR.Japan | BADR | ? | mods/cameo/rules/redalert.yaml |
| BADR.Soviet | BADR | ? | mods/cameo/rules/redalert.yaml |
| C17.Bomber | BADR.Bomber | ? | mods/cameo/rules/redalert.yaml |
| C17.Paradrop | BADR | ? | mods/cameo/rules/redalert.yaml |
| CAMERA.sw | CAMERA.small | ? | mods/cameo/rules/misc.yaml |
| ChronoVortexFade | ChronoVortex | ? | mods/cameo/rules/redalert.yaml |
| EDEN_TIGER_ACIDCLOUD | EDEN_LYNX_ACIDCLOUD | ? | mods/cameo/rules/outpost2.yaml |
| ForceShieldDrainer | CAMERA.small | ? | mods/cameo/rules/shared.yaml |
| INVISIBLEPLANE | BADR | ? | mods/cameo/rules/tiberiansun.yaml |
| MODCORE1 | MODCORE | ? | mods/cameo/rules/redalert.yaml |
| MODCORE2 | MODCORE | ? | mods/cameo/rules/redalert.yaml |
| MODCORE3 | MODCORE | ? | mods/cameo/rules/redalert.yaml |
| MODCORE4 | MODCORE | ? | mods/cameo/rules/redalert.yaml |
| MODCORE5 | MODCORE | ? | mods/cameo/rules/redalert.yaml |
| MODCORE6 | MODCORE | ? | mods/cameo/rules/redalert.yaml |
| MODCORE7 | MODCORE | ? | mods/cameo/rules/redalert.yaml |
| MODRAAFLD | RAAFLD | ? | mods/cameo/rules/redalert.yaml |
| MODRAWEAPJ | RAWEAP | ? | mods/cameo/rules/redalert.yaml |
| MONEYCRATE.LARGE | MONEYCRATE | ? | mods/cameo/rules/misc.yaml |
| OILB.TS | OILB.Building | ? | mods/cameo/rules/tiberiansun.yaml |
| PLYMOUTH_TIGER_EMP | PLYMOUTH_LYNX_EMP | ? | mods/cameo/rules/outpost2.yaml |
| PLYMOUTH_TIGER_ESG | PLYMOUTH_LYNX_ESG | ? | mods/cameo/rules/outpost2.yaml |
| PLYMOUTH_TIGER_MICROWAVE | PLYMOUTH_LYNX_MICROWAVE | ? | mods/cameo/rules/outpost2.yaml |
| PLYMOUTH_TIGER_RPG | PLYMOUTH_LYNX_RPG | ? | mods/cameo/rules/outpost2.yaml |
| PLYMOUTH_TIGER_STARFLARE | PLYMOUTH_LYNX_STARFLARE | ? | mods/cameo/rules/outpost2.yaml |
| PLYMOUTH_TIGER_STICKYFOAM | PLYMOUTH_LYNX_STICKYFOAM | ? | mods/cameo/rules/outpost2.yaml |
| PLYMOUTH_TIGER_SUPERNOVA | PLYMOUTH_LYNX_SUPERNOVA | ? | mods/cameo/rules/outpost2.yaml |
| RA2BRIK | BRIK | tiberiandawn/shared | mods/cameo/rules/redalert2.yaml |
| RA2ENGINEER | E6 | tiberiandawn/shared | mods/cameo/rules/redalert2.yaml |
| RA2FVBOTCHRONO | RA2FVBOTMG | ? | mods/cameo/rules/redalert2.yaml |
| RA2FVBOTHMG | RA2FV | ? | mods/cameo/rules/redalert2.yaml |
| RA2FVBOTMG | RA2FV | ? | mods/cameo/rules/redalert2.yaml |
| RA2FVBOTMISS | RA2FV | ? | mods/cameo/rules/redalert2.yaml |
| RA2FVBOTREP | RA2FVBOTMG | ? | mods/cameo/rules/redalert2.yaml |
| RABIO | bio | ? | mods/cameo/rules/tech.yaml |
| RAE6 | E6 | tiberiandawn/shared | mods/cameo/rules/redalert.yaml |
| RAMAID | RAJE3 | ? | mods/cameo/rules/redalert.yaml |
| RAMISS | MISS | ? | mods/cameo/rules/tech.yaml |
| SCBARRACKSM | SCCOMMANDCENTERM | ? | mods/cameo/rules/starcraft.yaml |
| SCCREEPCOLONYDEFENSE | SCCREEPCOLONY | ? | mods/cameo/rules/starcraft.yaml |
| SCENGINEERINGBAYM | SCCOMMANDCENTERM | ? | mods/cameo/rules/starcraft.yaml |
| SCFACTORYM | SCCOMMANDCENTERM | ? | mods/cameo/rules/starcraft.yaml |
| SCSCIENCEFACILITYM | SCCOMMANDCENTERM | ? | mods/cameo/rules/starcraft.yaml |
| SCSCOURGEDRONE | SCSCOURGE | ? | mods/cameo/rules/starcraft.yaml |
| SCSENTINELM | SCCOMMANDCENTERM | ? | mods/cameo/rules/starcraft.yaml |
| SCSTARPORTM | SCCOMMANDCENTERM | ? | mods/cameo/rules/starcraft.yaml |
| TECHBCANNON2 | TECHBCANNON | ? | mods/cameo/rules/tech.yaml |
| TSCYC2 | TSCYBORG | ? | mods/cameo/rules/tiberiansun.yaml |
| TSE1.GDI | TSE1 | ? | mods/cameo/rules/tiberiansun.yaml |
| TSE1.NOD | TSE1 | ? | mods/cameo/rules/tiberiansun.yaml |
| TSE1PARA | TSE1 | ? | mods/cameo/rules/tiberiansun.yaml |
| TSE2PARA | TSE2 | ? | mods/cameo/rules/tiberiansun.yaml |
| TSE3.Nod | TSE3 | ? | mods/cameo/rules/tiberiansun.yaml |
| TSENGINEECABAL | TSENGINEER | ? | mods/cameo/rules/tiberiansun.yaml |
| TSENGINEER | E6 | tiberiandawn/shared | mods/cameo/rules/tiberiansun.yaml |
| TSENGINEER2 | TSENGINEER | ? | mods/cameo/rules/tiberiansun.yaml |
| TSENGINEERMUTANT | TSENGINEER | ? | mods/cameo/rules/tiberiansun.yaml |
| TSGHOSTSP | TSGHOST | ? | mods/cameo/rules/tiberiansun.yaml |
| TSMCVCABAL | TSMCVGDI | ? | mods/cameo/rules/tiberiansun.yaml |
| TSMCVMUTANT | TSMCVGDI | ? | mods/cameo/rules/tiberiansun.yaml |
| TSMCVNOD | TSMCVGDI | ? | mods/cameo/rules/tiberiansun.yaml |
| TSMEDIC | MEDI | ? | mods/cameo/rules/tiberiansun.yaml |
| TSMUTANTSP | TSMUTANT | ? | mods/cameo/rules/tiberiansun.yaml |
| TSMUTANTW | TSMUTANT | ? | mods/cameo/rules/tiberiansun.yaml |
| TSMWMNSP | TSMWMN | ? | mods/cameo/rules/tiberiansun.yaml |
| TSREPAIRCABAL | TSREPAIR | ? | mods/cameo/rules/tiberiansun.yaml |
| TSUMAGON | TSMUTANT | ? | mods/cameo/rules/tiberiansun.yaml |
| TSUMAGONSP | TSUMAGON | ? | mods/cameo/rules/tiberiansun.yaml |
| U3 | U2 | ? | mods/cameo/rules/redalert.yaml |
| WWCRATE | CRATE | ? | mods/cameo/rules/misc.yaml |
| ambiance_battle | ambiance_wind | ? | mods/cameo/rules/misc.yaml |
| ambiance_bird | ambiance_wind | ? | mods/cameo/rules/misc.yaml |
| ambiance_bird_robin | ambiance_wind | ? | mods/cameo/rules/misc.yaml |
| ambiance_ocean_calm | ambiance_wind | ? | mods/cameo/rules/misc.yaml |
| ambiance_ocean_waves | ambiance_wind | ? | mods/cameo/rules/misc.yaml |
| ambiance_rumbling | ambiance_wind | ? | mods/cameo/rules/misc.yaml |
| camera.paradrop | RACAMERA | ? | mods/cameo/rules/misc.yaml |
| camera.placeholderhack | CAMERA.small | ? | mods/cameo/rules/misc.yaml |
| camera.psireveal | camera.scan | ? | mods/cameo/rules/misc.yaml |
| camera.ra2spy | CAMERA.small | ? | mods/cameo/rules/shared.yaml |
| camera.radarvan | camera.scan | ? | mods/cameo/rules/misc.yaml |
| camera.sathack | camera.paradrop | ? | mods/cameo/rules/misc.yaml |
| camera.spyplane | camera.scan | ? | mods/cameo/rules/misc.yaml |
| camera.spysat | camera.scan | ? | mods/cameo/rules/misc.yaml |
| jsuperbomber | BADR | ? | mods/cameo/rules/redalert.yaml |
| jsuperbomber.Husk | BADR.Husk | ? | mods/cameo/rules/husks.yaml |
| modbomber.Husk | YAK.Husk | ? | mods/cameo/rules/husks.yaml |
| modkami.Husk | YAK.Husk | ? | mods/cameo/rules/husks.yaml |
| modkamimini.Husk | YAK.Husk | ? | mods/cameo/rules/husks.yaml |
| ra2_awall | BRIK | tiberiandawn/shared | mods/cameo/rules/redalert2.yaml |
| ra2_c_hum2 | ra2_c_hum | ? | mods/cameo/rules/redalert2.yaml |
| ra2_city01 | ra2ctchig01 | ? | mods/cameo/rules/redalert2.yaml |
| ra2_city02 | ra2ctchig01 | ? | mods/cameo/rules/redalert2.yaml |
| ra2_city03 | ra2ctchig01 | ? | mods/cameo/rules/redalert2.yaml |
| ra2_city04 | ra2ctchig01 | ? | mods/cameo/rules/redalert2.yaml |
| ra2_city06 | ra2ctchig01 | ? | mods/cameo/rules/redalert2.yaml |
| ra2_crate | CRATE | ? | mods/cameo/rules/misc.yaml |
| ra2_ctfrmb | ra2ctbunk01 | ? | mods/cameo/rules/redalert2.yaml |
| ra2_ctgard01 | ra2ctbunk01 | ? | mods/cameo/rules/redalert2.yaml |
| ra2_ctgard03 | ra2ctbunk01 | ? | mods/cameo/rules/redalert2.yaml |
| ra2_ctnwy09 | ra2ctchig01 | ? | mods/cameo/rules/redalert2.yaml |
| ra2_ctnwy22 | ra2ctchig01 | ? | mods/cameo/rules/redalert2.yaml |
| ra2_ctnwy23 | ra2ctchig01 | ? | mods/cameo/rules/redalert2.yaml |
| ra2_ctnwy24 | ra2ctchig01 | ? | mods/cameo/rules/redalert2.yaml |
| ra2_ctnwy25 | ra2ctchig01 | ? | mods/cameo/rules/redalert2.yaml |
| ra2_ctpars02 | ra2ctchig01 | ? | mods/cameo/rules/redalert2.yaml |
| ra2_ctpars04 | ra2ctchig01 | ? | mods/cameo/rules/redalert2.yaml |
| ra2_ctpars05 | ra2ctchig01 | ? | mods/cameo/rules/redalert2.yaml |
| ra2_ctpars06 | ra2ctchig01 | ? | mods/cameo/rules/redalert2.yaml |
| ra2_ctpars07 | ra2ctbunk01 | ? | mods/cameo/rules/redalert2.yaml |
| ra2_ctpars08 | ra2ctchig01 | ? | mods/cameo/rules/redalert2.yaml |
| ra2_ctpars09 | ra2ctchig01 | ? | mods/cameo/rules/redalert2.yaml |
| ra2_ctpars10 | ra2ctchig01 | ? | mods/cameo/rules/redalert2.yaml |
| ra2_ctpars12 | ra2ctchig01 | ? | mods/cameo/rules/redalert2.yaml |
| ra2_ctpars13 | ra2ctchig01 | ? | mods/cameo/rules/redalert2.yaml |
| ra2_ctpars14 | ra2ctchig01 | ? | mods/cameo/rules/redalert2.yaml |
| ra2_ctrus03 | ra2ctchig01 | ? | mods/cameo/rules/redalert2.yaml |
| ra2_ctrus04 | ra2ctchig01 | ? | mods/cameo/rules/redalert2.yaml |
| ra2_ctrus05 | ra2ctchig01 | ? | mods/cameo/rules/redalert2.yaml |
| ra2_ctrus06 | ra2ctchig01 | ? | mods/cameo/rules/redalert2.yaml |
| ra2_ctrus07 | ra2ctchig01 | ? | mods/cameo/rules/redalert2.yaml |
| ra2_ctrus08 | ra2ctchig01 | ? | mods/cameo/rules/redalert2.yaml |
| ra2_ctrus09 | ra2ctchig01 | ? | mods/cameo/rules/redalert2.yaml |
| ra2_ctrus10 | ra2ctchig01 | ? | mods/cameo/rules/redalert2.yaml |
| ra2_ctrus11 | ra2ctchig01 | ? | mods/cameo/rules/redalert2.yaml |
| ra2_ctsanf01 | ra2ctchig01 | ? | mods/cameo/rules/redalert2.yaml |
| ra2_ctsanf02 | ra2ctchig01 | ? | mods/cameo/rules/redalert2.yaml |
| ra2_ctsanf03 | ra2ctchig01 | ? | mods/cameo/rules/redalert2.yaml |
| ra2_ctsanf05 | ra2ctchig01 | ? | mods/cameo/rules/redalert2.yaml |
| ra2_ctsanf06 | ra2ctchig01 | ? | mods/cameo/rules/redalert2.yaml |
| ra2_ctsanf07 | ra2ctchig01 | ? | mods/cameo/rules/redalert2.yaml |
| ra2_ctsanf08 | ra2ctchig01 | ? | mods/cameo/rules/redalert2.yaml |
| ra2_ctsanf16 | ra2ctchig01 | ? | mods/cameo/rules/redalert2.yaml |
| ra2_ctsanf17 | ra2ctchig01 | ? | mods/cameo/rules/redalert2.yaml |
| ra2_ctsanf18 | ra2ctchig01 | ? | mods/cameo/rules/redalert2.yaml |
| ra2_cttexs01 | ra2ctchig01 | ? | mods/cameo/rules/redalert2.yaml |
| ra2_cttexs02 | ra2ctchig01 | ? | mods/cameo/rules/redalert2.yaml |
| ra2_cttexs03 | ra2ctchig01 | ? | mods/cameo/rules/redalert2.yaml |
| ra2_cttexs04 | ra2ctchig01 | ? | mods/cameo/rules/redalert2.yaml |
| ra2_cttexs05 | ra2ctchig01 | ? | mods/cameo/rules/redalert2.yaml |
| ra2_cttexs06 | ra2ctchig01 | ? | mods/cameo/rules/redalert2.yaml |
| ra2_cttexs07 | ra2ctchig01 | ? | mods/cameo/rules/redalert2.yaml |
| ra2_cttexs08 | ra2ctchig01 | ? | mods/cameo/rules/redalert2.yaml |
| ra2_ctwash03 | ra2ctchig01 | ? | mods/cameo/rules/redalert2.yaml |
| ra2_ctwash04 | ra2ctchig01 | ? | mods/cameo/rules/redalert2.yaml |
| ra2_ctwash05 | ra2ctchig01 | ? | mods/cameo/rules/redalert2.yaml |
| ra2_ctwash06 | ra2ctchig01 | ? | mods/cameo/rules/redalert2.yaml |
| ra2_ctwash07 | ra2ctchig01 | ? | mods/cameo/rules/redalert2.yaml |
| ra2_ctwash08 | ra2ctchig01 | ? | mods/cameo/rules/redalert2.yaml |
| ra2_ctwash09 | ra2ctchig01 | ? | mods/cameo/rules/redalert2.yaml |
| ra2_ctwash10 | ra2ctchig01 | ? | mods/cameo/rules/redalert2.yaml |
| ra2_ctwash11 | ra2ctchig01 | ? | mods/cameo/rules/redalert2.yaml |
| ra2_ctwash13 | ra2ctchig01 | ? | mods/cameo/rules/redalert2.yaml |
| ra2_ctwash17 | ra2ctchig01 | ? | mods/cameo/rules/redalert2.yaml |
| ra2_swall | BRIK | tiberiandawn/shared | mods/cameo/rules/redalert2.yaml |
| ra2_ywall | BRIK | tiberiandawn/shared | mods/cameo/rules/redalert2.yaml |
| ra2caairpv | ra2caairp | ? | mods/cameo/rules/redalert2.yaml |
| ra2ctarmy01 | ra2ctbunk01 | ? | mods/cameo/rules/redalert2.yaml |
| ra2ctarmy02 | ra2ctbunk01 | ? | mods/cameo/rules/redalert2.yaml |
| ra2ctarmy03 | ra2ctarmy02 | ? | mods/cameo/rules/redalert2.yaml |
| ra2ctarmy04 | ra2ctarmy02 | ? | mods/cameo/rules/redalert2.yaml |
| ra2ctbarn02 | ra2ctbunk01 | ? | mods/cameo/rules/redalert2.yaml |
| ra2ctbunk02 | ra2ctbunk01 | ? | mods/cameo/rules/redalert2.yaml |
| ra2ctchig01 | ra2ctbunk01 | ? | mods/cameo/rules/redalert2.yaml |
| ra2ctchig02 | ra2ctchig01 | ? | mods/cameo/rules/redalert2.yaml |
| ra2ctchig03 | ra2ctchig01 | ? | mods/cameo/rules/redalert2.yaml |
| ra2cteur01 | ra2ctbunk01 | ? | mods/cameo/rules/redalert2.yaml |
| ra2cteur02 | ra2ctbunk01 | ? | mods/cameo/rules/redalert2.yaml |
| ra2cteur04 | ra2ctchig01 | ? | mods/cameo/rules/redalert2.yaml |
| ra2ctfarm01 | ra2ctbunk01 | ? | mods/cameo/rules/redalert2.yaml |
| ra2ctfarm06 | ra2ctbunk01 | ? | mods/cameo/rules/redalert2.yaml |
| ra2ctfrma | ra2ctbunk01 | ? | mods/cameo/rules/redalert2.yaml |
| ra2ctgas01 | ra2ctchig01 | ? | mods/cameo/rules/redalert2.yaml |
| ra2cthse01 | ra2ctbunk01 | ? | mods/cameo/rules/redalert2.yaml |
| ra2cthse02 | ra2ctbunk01 | ? | mods/cameo/rules/redalert2.yaml |
| ra2cthse03 | ra2ctchig01 | ? | mods/cameo/rules/redalert2.yaml |
| ra2cthse04 | ra2ctbunk01 | ? | mods/cameo/rules/redalert2.yaml |
| ra2cthse05 | ra2ctbunk01 | ? | mods/cameo/rules/redalert2.yaml |
| ra2cthse06 | ra2cthse05 | ? | mods/cameo/rules/redalert2.yaml |
| ra2cthse07 | ra2ctbunk01 | ? | mods/cameo/rules/redalert2.yaml |
| ra2ctind01 | ra2ctchig01 | ? | mods/cameo/rules/redalert2.yaml |
| ra2ctlab | ra2ctchig01 | ? | mods/cameo/rules/redalert2.yaml |
| ra2ctmiam01 | ra2ctchig01 | ? | mods/cameo/rules/redalert2.yaml |
| ra2ctmiam02 | ra2ctchig01 | ? | mods/cameo/rules/redalert2.yaml |
| ra2ctmiam03 | ra2ctchig01 | ? | mods/cameo/rules/redalert2.yaml |
| ra2ctmiam04 | ra2ctbunk01 | ? | mods/cameo/rules/redalert2.yaml |
| ra2ctmiam05 | ra2ctchig01 | ? | mods/cameo/rules/redalert2.yaml |
| ra2ctmiam06 | ra2ctmiam05 | ? | mods/cameo/rules/redalert2.yaml |
| ra2ctmiam07 | ra2ctmiam05 | ? | mods/cameo/rules/redalert2.yaml |
| ra2ctmiam08 | ra2ctbunk01 | ? | mods/cameo/rules/redalert2.yaml |
| ra2ctmsc07 | ra2ctbunk01 | ? | mods/cameo/rules/redalert2.yaml |
| ra2ctmsc08 | ra2ctarmy02 | ? | mods/cameo/rules/redalert2.yaml |
| ra2ctmsc09 | ra2ctmsc08 | ? | mods/cameo/rules/redalert2.yaml |
| ra2ctmsc10 | ra2ctchig01 | ? | mods/cameo/rules/redalert2.yaml |
| ra2ctnewy01 | ra2ctchig01 | ? | mods/cameo/rules/redalert2.yaml |
| ra2ctnewy06 | ra2ctchig01 | ? | mods/cameo/rules/redalert2.yaml |
| ra2ctnewy07 | ra2ctchig01 | ? | mods/cameo/rules/redalert2.yaml |
| ra2ctnewy08 | ra2ctchig01 | ? | mods/cameo/rules/redalert2.yaml |
| ra2ctnewy10 | ra2ctchig01 | ? | mods/cameo/rules/redalert2.yaml |
| ra2ctnewy11 | ra2ctchig01 | ? | mods/cameo/rules/redalert2.yaml |
| ra2ctnewy12 | ra2ctnewy08 | ? | mods/cameo/rules/redalert2.yaml |
| ra2ctnewy13 | ra2ctnewy08 | ? | mods/cameo/rules/redalert2.yaml |
| ra2ctnewy14 | ra2ctnewy08 | ? | mods/cameo/rules/redalert2.yaml |
| ra2ctnewy15 | ra2ctnewy07 | ? | mods/cameo/rules/redalert2.yaml |
| ra2ctnewy16 | ra2ctnewy08 | ? | mods/cameo/rules/redalert2.yaml |
| ra2ctnewy17 | ra2ctnewy16 | ? | mods/cameo/rules/redalert2.yaml |
| ra2ctnewy18 | ra2ctnewy17 | ? | mods/cameo/rules/redalert2.yaml |
| ra2ctnewy20 | ra2ctchig01 | ? | mods/cameo/rules/redalert2.yaml |
| ra2ctnewy21 | ra2ctnewy20 | ? | mods/cameo/rules/redalert2.yaml |
| ra2ctnewy26 | ra2ctchig01 | ? | mods/cameo/rules/redalert2.yaml |
| ra2e2.black | RA2E2 | ? | mods/cameo/rules/redalert2.yaml |
| ra2engineer.soviet | RA2ENGINEER | ? | mods/cameo/rules/redalert2.yaml |
| ra2engineer.yuri | RA2ENGINEER | ? | mods/cameo/rules/redalert2.yaml |
| ra2nacnst | ra2gacnst | ? | mods/cameo/rules/redalert2.yaml |
| ra2shk.bot | ra2shk | ? | mods/cameo/rules/redalert2.yaml |
| ra2shkhero | ra2shk | ? | mods/cameo/rules/redalert2.yaml |
| ra2v3rocketelite | ra2v3rocket | ? | mods/cameo/rules/redalert2.yaml |
| ra_gigafactory | RAWEAP | ? | mods/cameo/rules/redalert.yaml |
| ra_industrialminer | RAHARV.SOVIET | ? | mods/cameo/rules/redalert.yaml |
| ra_largeairfield | RAAFLD | ? | mods/cameo/rules/redalert.yaml |
| scadept.shade | SCADEPT | ? | mods/cameo/rules/starcraft.yaml |
| scsporecolony | SCCREEPCOLONY | ? | mods/cameo/rules/starcraft.yaml |
| scsunkencolony | SCCREEPCOLONY | ? | mods/cameo/rules/starcraft.yaml |
| sonar | camera.spyplane | ? | mods/cameo/rules/misc.yaml |
| tkmabramspoint | tkmabrams | ? | mods/cameo/rules/tkm.yaml |
| tkmengineer | E6 | tiberiandawn/shared | mods/cameo/rules/tkm.yaml |
| tkmworker | YRSLAV | ? | mods/cameo/rules/tkm.yaml |
| ts_crate | CRATE | ? | mods/cameo/rules/misc.yaml |
| tsart2cabal_backup | TSART2CABAL | ? | mods/cameo/rules/tiberiansun.yaml |
| tsccommando | TSCYBORG | ? | mods/cameo/rules/tiberiansun.yaml |
| tscheavyspider_backup | tscheavyspider | ? | mods/cameo/rules/tiberiansun.yaml |
| tse3.mutant | TSE3 | ? | mods/cameo/rules/tiberiansun.yaml |
| tsfsmoker.bomber | tsfsmoker | ? | mods/cameo/rules/tiberiansun.yaml |
| tsghost.r4 | TSGHOST | ? | mods/cameo/rules/tiberiansun.yaml |
| tsmonstermaker1 | VICE | ? | mods/cameo/rules/tiberiansun.yaml |
| tssapc.mut | TSSAPC | ? | mods/cameo/rules/tiberiansun.yaml |
| tssgencabal | tssgen | ? | mods/cameo/rules/tiberiansun.yaml |
| tsttnkcabal_backup | TSTTNKCABAL | ? | mods/cameo/rules/tiberiansun.yaml |
| tsumagon.r4 | TSUMAGON | ? | mods/cameo/rules/tiberiansun.yaml |
| wc2_camera_scanner | camera.scan | ? | mods/cameo/rules/warcraft2.yaml |
| wc2_human_cannon_tower | wc2_human_scout_tower | ? | mods/cameo/rules/warcraft2.yaml |
| wc2_human_elven_ranger | wc2_human_elven_archer | ? | mods/cameo/rules/warcraft2.yaml |
| wc2_human_goldmine.bot | wc2_human_goldmine | ? | mods/cameo/rules/warcraft2.yaml |
| wc2_human_guard_tower | wc2_human_scout_tower | ? | mods/cameo/rules/warcraft2.yaml |
| wc2_human_paladin | wc2_human_knight | ? | mods/cameo/rules/warcraft2.yaml |
| wc2_orc_cannon_tower | wc2_orc_watch_tower | ? | mods/cameo/rules/warcraft2.yaml |
| wc2_orc_goldmine.bot | wc2_orc_goldmine | ? | mods/cameo/rules/warcraft2.yaml |
| wc2_orc_guard_tower | wc2_orc_watch_tower | ? | mods/cameo/rules/warcraft2.yaml |
| wc2_orc_ogremage | wc2_orc_ogre | ? | mods/cameo/rules/warcraft2.yaml |
| wc2_orc_skeleton | wc2_orc_grunt | ? | mods/cameo/rules/warcraft2.yaml |
| wc2_orc_troll_berserker | wc2_orc_troll_axethrower | ? | mods/cameo/rules/warcraft2.yaml |
| wc2_orc_wall | wc2_human_wall | ? | mods/cameo/rules/warcraft2.yaml |
| yakarmored.Husk | YAK.Husk | ? | mods/cameo/rules/husks.yaml |
| yaktesla.Husk | YAK.Husk | ? | mods/cameo/rules/husks.yaml |
| yrbfrt.bot | yrbfrt | ? | mods/cameo/rules/redalert2.yaml |
| yrbfrt.bot2 | yrbfrt | ? | mods/cameo/rules/redalert2.yaml |
| yrlunr.husk | ra2rock.husk | ? | mods/cameo/rules/redalert2.yaml |
| yrnacnst | ra2gacnst | ? | mods/cameo/rules/redalert2.yaml |
| yrsmin.empy | YRSMIN | ? | mods/cameo/rules/redalert2.yaml |
| yuriinvisibleplane | U2 | ? | mods/cameo/rules/redalert2.yaml |

**cabal** (9):

| actor | inherits | target faction | file |
|---|---|---|---|
| TSGTSILOCABAL | TSGTSILO | tsgdi | mods/cameo/rules/tiberiansun.yaml |
| tscabaltech | tsgttech | tsgdi | mods/cameo/rules/tiberiansun.yaml |
| tsgtdeptcabal | tsgtdeptgdi | tsgdi | mods/cameo/rules/tiberiansun.yaml |
| tsnthpad2 | tsnthpad | tsnod | mods/cameo/rules/tiberiansun.yaml |
| tsntlasrcabal | tsntlasr | tsnod | mods/cameo/rules/tiberiansun.yaml |
| tsntmislcabal | tsntmisl | tsnod | mods/cameo/rules/tiberiansun.yaml |
| tsntobelcabal | tsntobel | tsnod | mods/cameo/rules/tiberiansun.yaml |
| tsntradrcabal | tsntradr | tsnod | mods/cameo/rules/tiberiansun.yaml |
| tsntstlhcabal | tsntstlh | tsnod | mods/cameo/rules/tiberiansun.yaml |

**d2k/ixian** (1):

| actor | inherits | target faction | file |
|---|---|---|---|
| heavy_factory.ixian | heavy_factory | d2k/shared | mods/cameo/ContentPacks/D2k/Ixian/rules/buildings.yaml |

**d2k/ordos** (5):

| actor | inherits | target faction | file |
|---|---|---|---|
| carryall.ordos | carryall | d2k/shared | mods/cameo/ContentPacks/D2k/Ordos/rules/aircraft.yaml |
| carryall_reinforce.ordos | carryall.reinforce | d2k/shared | mods/cameo/ContentPacks/D2k/Ordos/rules/aircraft.yaml |
| heavy_factory.ordos | heavy_factory | d2k/shared | mods/cameo/ContentPacks/D2k/Ordos/rules/buildings.yaml |
| light_factory.ordos | light_factory | d2k/shared | mods/cameo/ContentPacks/D2k/Ordos/rules/buildings.yaml |
| stealth_raider.ordos | raider.ordos | d2k/ordos | mods/cameo/ContentPacks/D2k/Ordos/rules/vehicles.yaml |

**d2k/shared** (9):

| actor | inherits | target faction | file |
|---|---|---|---|
| OILB.d2k | OILB.Building | ? | mods/cameo/ContentPacks/D2k/Shared/rules/buildings.yaml |
| carryall | carryall.reinforce | d2k/shared | mods/cameo/ContentPacks/D2k/Shared/rules/aircraft.yaml |
| carryall.paradrop | carryall.reinforce | d2k/shared | mods/cameo/ContentPacks/D2k/Shared/rules/aircraft.yaml |
| concreteadefense | concreteabuilding | d2k/shared | mods/cameo/ContentPacks/D2k/Shared/rules/buildings.yaml |
| concretebbuilding | concreteabuilding | d2k/shared | mods/cameo/ContentPacks/D2k/Shared/rules/buildings.yaml |
| concretebdefense | concretebbuilding | d2k/shared | mods/cameo/ContentPacks/D2k/Shared/rules/buildings.yaml |
| engineer | E6 | tiberiandawn/shared | mods/cameo/ContentPacks/D2k/Shared/rules/infantry.yaml |
| frigate.paradrop | frigate | d2k/shared | mods/cameo/ContentPacks/D2k/Shared/rules/aircraft.yaml |
| sietch_creep_disabled | sietch_creep | d2k/shared | mods/cameo/ContentPacks/D2k/Shared/rules/buildings.yaml |

**forgotten** (3):

| actor | inherits | target faction | file |
|---|---|---|---|
| OILB.TS.MUTANT | OILB.TS | ? | mods/cameo/rules/tiberiansun.yaml |
| tsgtdeptmutant | tsgtdeptgdi | tsgdi | mods/cameo/rules/tiberiansun.yaml |
| tsgthpadmutant | tsgthpad | tsgdi | mods/cameo/rules/tiberiansun.yaml |

**redalert2mod/asianalliance** (9):

| actor | inherits | target faction | file |
|---|---|---|---|
| awall.asian | BRIK | tiberiandawn/shared | mods/cameo/ContentPacks/RedAlert2Mod/AsianAlliance/rules/buildings.yaml |
| bomber_husk.asian | BADR.Husk | ? | mods/cameo/ContentPacks/RedAlert2Mod/AsianAlliance/rules/aircraft.yaml |
| bomber_minebomb.asian | BADR | ? | mods/cameo/ContentPacks/RedAlert2Mod/AsianAlliance/rules/aircraft.yaml |
| bomber_minebomb2.asian | bomber_minebomb.asian | redalert2mod/asianalliance | mods/cameo/ContentPacks/RedAlert2Mod/AsianAlliance/rules/aircraft.yaml |
| kami_asdf.asian | kami.asian | redalert2mod/asianalliance | mods/cameo/ContentPacks/RedAlert2Mod/AsianAlliance/rules/aircraft.yaml |
| kami_chemical.asian | kami.asian | redalert2mod/asianalliance | mods/cameo/ContentPacks/RedAlert2Mod/AsianAlliance/rules/aircraft.yaml |
| oilt.asian | DTRK | ? | mods/cameo/ContentPacks/RedAlert2Mod/AsianAlliance/rules/vehicles.yaml |
| ra2engineer.asian | RA2ENGINEER | ? | mods/cameo/ContentPacks/RedAlert2Mod/AsianAlliance/rules/infantry.yaml |
| railt2.asian | railt.asian | redalert2mod/asianalliance | mods/cameo/ContentPacks/RedAlert2Mod/AsianAlliance/rules/vehicles.yaml |

**redalert2mod/consortium** (2):

| actor | inherits | target faction | file |
|---|---|---|---|
| fedeng.steel | RA2ENGINEER | ? | mods/cameo/ContentPacks/RedAlert2Mod/Consortium/rules/infantry.yaml |
| qacst.steel | ra2gacnst | ? | mods/cameo/ContentPacks/RedAlert2Mod/Consortium/rules/buildings.yaml |

**redalert2mod/futuretech** (3):

| actor | inherits | target faction | file |
|---|---|---|---|
| fedeng.futu | RA2ENGINEER | ? | mods/cameo/ContentPacks/RedAlert2Mod/FutureTech/rules/infantry.yaml |
| ifv.futu | RA2FV | ? | mods/cameo/ContentPacks/RedAlert2Mod/FutureTech/rules/vehicles.yaml |
| landcarr_drone.futu | ra2hornet | ? | mods/cameo/ContentPacks/RedAlert2Mod/FutureTech/rules/aircraft.yaml |

**redalert2mod/naxis** (3):

| actor | inherits | target faction | file |
|---|---|---|---|
| corpse_big.nax | corpse.nax | redalert2mod/naxis | mods/cameo/ContentPacks/RedAlert2Mod/Naxis/rules/vehicles.yaml |
| horten_bomber.nax | BADR.Soviet | ? | mods/cameo/ContentPacks/RedAlert2Mod/Naxis/rules/aircraft.yaml |
| slav.nax | YRSLAV | ? | mods/cameo/ContentPacks/RedAlert2Mod/Naxis/rules/infantry.yaml |

**redalert2mod/schwarzermond** (3):

| actor | inherits | target faction | file |
|---|---|---|---|
| bbomb2_husk.nax2 | bbomb_husk.nax2 | redalert2mod/schwarzermond | mods/cameo/ContentPacks/RedAlert2Mod/SchwarzerMond/rules/aircraft.yaml |
| bbomb3_husk.nax2 | bbomb_husk.nax2 | redalert2mod/schwarzermond | mods/cameo/ContentPacks/RedAlert2Mod/SchwarzerMond/rules/aircraft.yaml |
| hole_small.nax2 | hole.nax2 | redalert2mod/schwarzermond | mods/cameo/ContentPacks/RedAlert2Mod/SchwarzerMond/rules/infantry.yaml |

**redalert2mod/syndicate** (6):

| actor | inherits | target faction | file |
|---|---|---|---|
| cgcnst.latin | ra2gacnst | ? | mods/cameo/ContentPacks/RedAlert2Mod/Syndicate/rules/buildings.yaml |
| deathcash.latin | RACAMERA | ? | mods/cameo/ContentPacks/RedAlert2Mod/Syndicate/rules/upgrades.yaml |
| deathcash_small.latin | RACAMERA | ? | mods/cameo/ContentPacks/RedAlert2Mod/Syndicate/rules/upgrades.yaml |
| nuketruk.latin | DTRK | ? | mods/cameo/ContentPacks/RedAlert2Mod/Syndicate/rules/vehicles.yaml |
| ra2dtruck.latin | DTRK | ? | mods/cameo/ContentPacks/RedAlert2Mod/Syndicate/rules/vehicles.yaml |
| ra2engineer.latin | RA2ENGINEER | ? | mods/cameo/ContentPacks/RedAlert2Mod/Syndicate/rules/infantry.yaml |

**tiberiandawn/gdi** (5):

| actor | inherits | target faction | file |
|---|---|---|---|
| CNCSYRD | RA1SYRD | ? | mods/cameo/ContentPacks/TiberianDawn/GDI/rules/buildings.yaml |
| E1 | E1.GDI | tiberiandawn/gdi | mods/cameo/ContentPacks/TiberianDawn/GDI/rules/infantry.yaml |
| E3 | E3.GDI | tiberiandawn/gdi | mods/cameo/ContentPacks/TiberianDawn/GDI/rules/infantry.yaml |
| gdihumvee | JEEP | tiberiandawn/gdi | mods/cameo/ContentPacks/TiberianDawn/GDI/rules/vehicles.yaml |
| tran.gdi | TRAN | tiberiandawn/shared | mods/cameo/ContentPacks/TiberianDawn/GDI/rules/aircraft.yaml |

**tiberiandawn/nod** (3):

| actor | inherits | target faction | file |
|---|---|---|---|
| CNCSPEN | RASPEN | ? | mods/cameo/ContentPacks/TiberianDawn/Nod/rules/buildings.yaml |
| nodbuggy2 | BGGY | tiberiandawn/nod | mods/cameo/ContentPacks/TiberianDawn/Nod/rules/vehicles.yaml |
| tran.nod | TRAN | tiberiandawn/shared | mods/cameo/ContentPacks/TiberianDawn/Nod/rules/aircraft.yaml |

**tsnod** (3):

| actor | inherits | target faction | file |
|---|---|---|---|
| TSGTSILONOD | TSGTSILO | tsgdi | mods/cameo/rules/tiberiansun.yaml |
| tsgtdeptnod | tsgtdeptgdi | tsgdi | mods/cameo/rules/tiberiansun.yaml |
| tsprocnod | tsprocgdi | tsgdi | mods/cameo/rules/tiberiansun.yaml |


---

## B5 — AI wiring (ai.yaml)

**A1 — referenced ids defined NOWHERE (200, blocking class):** the exact
Forgotten-helipad bug shape. Live-faction standouts: `tsgtcnstcabalb`
(CABAL ConstructionYardTypes), `tsntpulscabal` (BuildingFractions TS CABAL —
the live actor is `tsntpulsgdi`-style), `ra2naclon`, `nax2_chrono`,
`high_tech_factory`/`d2k_silo` and the whole "BuildingFractions Dune
Universe" block (lines ~4443-4477), which still uses pre-ContentPacks D2k
names — the D2k houses' live sections exist separately, so this block is
dead weight steering nothing. Severity: **balance** (AI plays without parts
of its tree). Full 200-row table: `ai.md` §A1.

**A2 — combat units the AI never builds (Random/Tournament factions):**



| faction | count | unwired units |
|---|---|---|
| allies | 1 | tsprobe |
| asianalliance | 1 | tsprobe |
| cabal | 4 | tscarrycabal, tsengineecabal, tsprobe, tsrepaircabal |
| consortium | 2 | runner.steel, tsprobe |
| forgotten | 3 | tsengineermutant, tsprobe, tstrnsportmutant |
| futuretech | 3 | orion.futu, tsprobe, yrrobo.futu |
| gdi | 1 | tsprobe |
| human2 | 2 | tsprobe, wc2_human_gyrocopter2 |
| ixian | 1 | tsprobe |
| lnaxis | 1 | tsprobe |
| modjapan | 1 | tsprobe |
| naxis | 5 | fcons.nax, hmg.nax, quadflak.nax, tsprobe, zombietank.nax |
| nod | 1 | tsprobe |
| orc2 | 1 | tsprobe |
| ordos | 4 | heavycombattank.ordos, raider.ordos, saboteur.ordos, tsprobe |
| protoss | 1 | tsprobe |
| ra2america | 1 | tsprobe |
| ra2russia | 1 | tsprobe |
| soviet | 1 | tsprobe |
| syndicate | 1 | tsprobe |
| terran | 1 | tsprobe |
| tkm | 3 | tkmmarine, tkmsniper, tsprobe |
| tsgdi | 6 | tse1.gdi, tsjumpjet2, tslpst, tsmedic, tsprobe, tstrnsport |
| tsnod | 3 | tschamspy, tse3.nod, tsprobe |
| yuri | 1 | tsprobe |
| zerg | 1 | tsprobe |


_`tsprobe` rows are noise (it is the Hunter-Seeker munition, not an
AI-buildable); the real gaps are `raider.ordos` (the freshly reworked Ordos
Raider!), `runner.steel`, `orion.futu`, `yrrobo.futu`, the 5 Naxis units,
and `wc2_human_gyrocopter2`._

**A3 — 620 references to unloaded content** (Generals, Dawn-of-Tomorrow,
315custom, old D2k names…): hygiene; delete the dead sections or fence them
with comments naming the content pack that must load first.

---

## B3 — Upgrade direction / dead upgrades

**Inverted-direction candidates (curated).** The detector flags every
anti-buff multiplier gated on an upgrade condition; curation separates
intended drawbacks from Dark-Armament-class bugs:

| upgrade | trait | verdict |
|---|---|---|
| ra_doctrine_teslatech ReloadDelayMultiplier=200 (2 actors) | reload DOUBLED by a tech doctrine | **suspicious — verify** (Dark-Armament class unless the doctrine swaps in a stronger weapon) |
| up_energizedarrows ReloadDelayMultiplier=125 (1 actor) | slower reload on a weapon buff | **suspicious — verify** |
| up_advancedplasmaweapons FirepowerMultiplier=50/66 | halved firepower on a "plasma" upgrade | **verify** weapon-swap compensation exists on all 3 actors |
| up_cryomissiles FirepowerMultiplier=75 (12) | freeze-for-damage tradeoff | intended (documented tradeoff) — add `drawbacks:` intent entry |
| up_resonanceammo.steel FirepowerMultiplier=50 (5) | ricochet tradeoff | intended — add intent entry |
| up_pulverizer.asian FirepowerMultiplier=75 (2) | range-for-damage tradeoff | intended — add intent entry |
| ra2_soviets heavy/reactive/tesla armors SpeedMultiplier=85–95 (43) | armor slows you | intended — add intent entries |
| up_cyberneticmodifications DamageMultiplier=200 (25) | shield-for-HP tradeoff | intended (TD Nod design) — add intent entry |

**Dead upgrades (4):** `ra2teslaupgrade`, `tsgtplug2`, `tsgtplug3`,
`uptsdummy4`. The two `tsgtplug*` are plug-socket actors — **needs human
decision** whether the Pluggable system consumes them outside prerequisites;
`uptsdummy4` is an explicit placeholder (its siblings 1–3 are `disabled`).

**Dead wiring:** `usabombardament` / `usaholdtheline` / `usasearchndestroy` /
`upsubliminal(2)` hooks sit on **1,042 actors each** and `upra2deso` on 302,
granted by nothing in the live tree (Generals-era leftovers) — the single
biggest mechanical cleanup available (B10 overlap). `base-reveal`,
`classicproductionqueues`, `scaledprices`… look like lobby-option tokens the
detector's whitelist should learn (**needs human decision**). Full table:
`upgrades.md`. 526 upgrades still lack `upgrades_intent.yaml` entries — the
transcription TODO.

---

## B4 — Upgrade coverage gaps



| upgrade | faction | declared coverage | covered | uncovered actors |
|---|---|---|---|---|
| cabaldarkarmament | cabal | infantry | 8/13 | tsdefender, tsdissolver, tsengineecabal, tshacker, tsreaper |
| cabalfirewallprotocol | cabal | roster_wide | 21/27 | tsdissolver, tsengineecabal, tsharvcabal, tsmcvcabal, tsprobe, tsrepaircabal |
| cabalnetworkprotocols | cabal | roster_wide | 21/27 | tsdissolver, tsengineecabal, tsharvcabal, tsmcvcabal, tsprobe, tsrepaircabal |
| up_advancedtiberiumrefinement | tsnod | vehicles | 10/11 | tsmcvnod |
| up_chemicalfuel | forgotten | vehicles | 18/19 | tsmcvmutant |
| up_genomemapping | forgotten | infantry | 13/13 | — |
| up_junkarmor | forgotten | vehicles | 18/19 | tsmcvmutant |
| up_mechanicalreliability | tsgdi | vehicles | 16/16 | — |
| up_modernfirecontrolsystems | tsgdi | roster_wide | 15/31 | tse1.gdi, tse2, tsenforcer, tshammerhead, tsjumpjet2, tskodk, tslpst, tsmedic, tsorca, tsorcab, tsprobe, tsrailcom, tsriott, tstrnsport, tszoneorca, tszonetrooper |
| up_mypet | forgotten | roster_wide | 31/39 | tsapachemutant, tscropplane, tsflocust, tsheli, tshind, tsmcvmutant, tsprobe, tstrnsportmutant |
| up_seretraining | tsgdi | infantry | 7/7 | — |
| up_tiberiumadaptability | forgotten | roster_wide | 37/39 | tsprobe, tstrnsportmutant |
| up_unity | forgotten | roster_wide | 37/39 | tsmcvmutant, tsprobe |
| up_willofkane | tsnod | infantry | 7/7 | — |
| upcabalfullassimilation | cabal | roster_wide | 21/27 | tsdissolver, tsengineecabal, tsharvcabal, tsmcvcabal, tsprobe, tsrepaircabal |


_Support units (MCV/harvester/engineer/transports) in the uncovered lists
are judgment calls; the unambiguous gaps are combat units: Modern Fire
Control Systems missing ALL TS-GDI aircraft + half its infantry, Dark
Armament missing tshacker/tsreaper/tsdefender, up_mypet missing every
Forgotten aircraft._

---

## B6 — Broken art/sequence references

S1 (missing render image, 11) and S2 (missing sequence in image, 11) inline
below; plus `tsarnd`'s missing `muzzle` (B8 table). 542 sequence images are
referenced by no live actor/weapon (feeds B10). Severity: **cosmetic** to
**crash-risk**.



| actor | image | rules file |
|---|---|---|
| INVISIBLEPLANE | invisibleplane | mods/cameo/rules/tiberiansun.yaml |
| MSAM.Husk | msam.destroyed | mods/cameo/rules/husks.yaml |
| TECH1 | tech1 | mods/cameo/rules/redalert.yaml |
| TECHBCANNON | techbcannon | mods/cameo/rules/tech.yaml |
| TECHBCANNON2 | techbcannon2 | mods/cameo/rules/tech.yaml |
| TRAN.Husk1 | tran1husk | mods/cameo/rules/husks.yaml |
| TRAN.Husk2 | tran2husk | mods/cameo/rules/husks.yaml |
| ra2ctnewy26 | ra2ctnewy26 | mods/cameo/rules/redalert2.yaml |
| techcementffact | techcementffact | mods/cameo/rules/tech.yaml |
| techmetalffact | techmetalffact | mods/cameo/rules/tech.yaml |
| tsnafnce | tsnafnce | mods/cameo/rules/tiberiansun.yaml |


## S2 — trait sequence missing from image

| actor | trait | sequence | image | rules file |
|---|---|---|---|---|
| ra2ctarmy01 | WithIdleOverlay@Bunkered | idle-bunkered | ra2ctarmy01 | mods/cameo/rules/redalert2.yaml |
| ra2ctarmy02 | WithIdleOverlay@Bunkered | idle-bunkered | ra2ctarmy02 | mods/cameo/rules/redalert2.yaml |
| ra2ctarmy03 | WithIdleOverlay@Bunkered | idle-bunkered | ra2ctarmy03 | mods/cameo/rules/redalert2.yaml |
| ra2ctarmy04 | WithIdleOverlay@Bunkered | idle-bunkered | ra2ctarmy04 | mods/cameo/rules/redalert2.yaml |
| ra2ctbarn02 | WithIdleOverlay@Bunkered | idle-bunkered | ra2ctbarn02 | mods/cameo/rules/redalert2.yaml |
| ra2ctbunk02 | WithIdleOverlay@Bunkered | idle-bunkered | ra2ctbunk02 | mods/cameo/rules/redalert2.yaml |
| ra2ctfrma | WithIdleOverlay@Bunkered | idle-bunkered | ra2ctfrma | mods/cameo/rules/redalert2.yaml |
| ra2ctgas01 | WithIdleOverlay@Bunkered | idle-bunkered | ra2ctgas01 | mods/cameo/rules/redalert2.yaml |
| ra2ctmsc07 | WithIdleOverlay@Bunkered | idle-bunkered | ra2ctmsc07 | mods/cameo/rules/redalert2.yaml |
| ra2ctmsc08 | WithIdleOverlay@Bunkered | idle-bunkered | ra2ctmsc08 | mods/cameo/rules/redalert2.yaml |
| ra2ctmsc09 | WithIdleOverlay@Bunkered | idle-bunkered | ra2ctmsc09 | mods/cameo/rules/redalert2.yaml |


---

## B7 — Metadata rot

**M1 duplicate tooltips (31 groups)** — standouts: WarCraft-2's tower
upgrades have **swapped names** (`wchumanguardtowerupgrade` is called
"Cannon Tower" and `wchumancannontowerupgrade` "Guard Tower"), and TD
GDI/Nod each field two distinct "Engineer" actors (`e6` + `tsengineer`).
**M2:** 5 buildables have no tooltip at all. Severity: **cosmetic**.



| faction | tooltip name | actors |
|---|---|---|
| consortium | katy tank | katy.steel, up_katy.steel |
| consortium | quantum tank | quantumtank.steel, up_quantumtank.steel |
| edenl | impulse items | consumer_items_impulse, consumer_items_luxury_wares, consumer_items_wares |
| forgotten | tiberian fiend | tsdoggie, tsdoggieblue |
| gdi | engineer | e6, tsengineer |
| gdi | ion cannon uplink | eye.ionc, tsgtplug2 |
| human2 | cannon tower | wc2_human_cannon_tower, wchumanguardtowerupgrade |
| human2 | guard tower | wc2_human_guard_tower, wchumancannontowerupgrade |
| human2 | high elven archer | wc2_human_high_elf_archer, wc2_upgrade_high_elf_archer |
| human2 | human gold mine | wc2_human_goldmine, wc2_human_goldmine.bot |
| human2 | paladin | wc2_h_paladinupg, wc2_human_paladin |
| human2 | warcraft 3 footman | wc2_human_footman2, wc2_upgrade_footman |
| ixian | concrete slab | concreteabuilding, concreteadefense |
| ixian | large concrete slab | concretebbuilding, concretebdefense |
| naxis | horten bomber strike | up_nax_horten.nax, up_nax_horten2.nax |
| nod | engineer | e6, tsengineer |
| orc2 | cannon tower | wc2_orc_cannon_tower, wcorccannontowerupgrade |
| orc2 | guard tower | wc2_orc_guard_tower, wcorcguardtowerupgrade |
| orc2 | ogre-mage | wc2_o_ogremageupg, wc2_orc_ogremage |
| orc2 | orc gold mine | wc2_orc_goldmine, wc2_orc_goldmine.bot |
| orc2 | troll headhunter | wc2_orc_troll_spearthrower, wc2_upgrade_troll_spearthrower |
| orc2 | warcraft 3 grunt | wc2_orc_grunt2, wc2_upgrade_grunt |
| ordos | concrete slab | concreteabuilding, concreteadefense |
| ordos | large concrete slab | concretebbuilding, concretebdefense |
| ra2america | actor-fv.name | ra2fv, ra2fvbotchrono, ra2fvbothmg, ra2fvbotmg, ra2fvbotmiss, ra2fvbotrep |
| ra2america | battle fortress | yrbfrt, yrbfrt.bot, yrbfrt.bot2 |
| soviet | rifle infantry | rae1, rare1 |
| yuri | slave miner | yrsmin, yryarefn |
| zerg | creep colony | sccreepcolony, sccreepcolonydefense |
| zerg | spore colony | scsporecolony, scsunkencolonyupgrade |
| zerg | sunken colony | scsporecolonyupgrade, scsunkencolony |


## M2 — buildable actors without a Tooltip name

| faction | actor |
|---|---|
| allies | raspy |
| futuretech | spy.futu |
| ixian | refinery.ixian |
| ordos | refinery.ordos |
| ra2america | ra2spy |


---

## B9 — Numeric drift

The TB23 selection-bounds fix **held**: zero components above the 5,120
(5-cell) maximum tree-wide. Robust-z screening (163 leads, full table in
`outliers.md`) surfaces: `wc2_orc_eye_of_kilrogg` Aircraft.TurnSpeed **2048**
(median 20 — clearly a stale-scale value), a consistent husk family at
TurnSpeed 80–160 (probably intended tumble), and clusters in
ChangesHealth.Step / RevealsShroud.Range worth a scan. Severity: mostly
**cosmetic/balance-minor**; the value of this detector is catching the NEXT
42× drift, so it stays in CI.

---

## B10 — Dead content

**345 orphan weapons** (no live actor/weapon/map/Lua reference), **542
orphan sequence images**, 16 granted-never-consumed conditions, and the
1,042-actor dead-wiring families from B3. Severity: **hygiene** (RAM, load
time, agent confusion). Full lists: `orphans.md`, `sequences.md` §S3.
Review before deleting — the audit already greps `maps/` and `bits/lua`, but
third-party maps may reference more.

---

## B11 — Asset norms (RAMpage)

Norm: **mono / 16-bit / 22050 Hz** WAVs. 3,632 of 8,776 WAVs are
non-conforming — i.e. the norm has not yet been applied tree-wide; treat as
one batch-conversion task per directory (per-directory counts + exact
ffmpeg commands in `assets.md`). 131 PNGs exceed the generous whole-file
budget (8 MiB / 8192px) — mostly UI/tileset sheets, worth a category budget
in `docs/design/asset_budget.md`.

---

## B12 — Localization drift

**F1 — player-visible raw keys (3):** `SCvoidray` + `upvoidray`
(`actor-scvoidray/upvoidray.description`) and `up_blitzkrieg.nax`
(`upgrade-blitzkrieg.description`) reference Fluent messages that don't
exist. Severity: **cosmetic, player-visible**. **F2:** 233 orphaned
`actor-*` messages for actors that no longer exist. Fluent tooltip coverage
is 0–10% per faction (matrix column) — localization is effectively
literal-string-based today; the §12 Phase-2 rename tooling should emit
Fluent keys as it goes.

---

## Naming (§9.1, RA1-Soviet baseline) & rename maps

Compliance measured on faction-exclusive buildables; proposals written to
`tools/rename/rename_map_<faction>.yaml` (`actors:` + `files:` sections,
including the `_icon` filename rule). Only Outpost-2 (`plymouthl`/`edenl`,
93–100%) and parts of RA2 Allies (27%) are compliant today; the exemplar
scheme itself lives in RA1 (`ra_upgrade_*`, `ra_promotion_*`,
`ra_doctrine_*`). Do NOT apply maps outside a §9.6 freeze window.



| faction | compliant | % | proposal collisions | asset files to rename |
|---|---|---|---|---|
| allies | 0/62 | 0% | 0 | 124 |
| asianalliance | 0/72 | 0% | 0 | 242 |
| cabal | 0/57 | 0% | 0 | 136 |
| consortium | 0/61 | 0% | 0 | 145 |
| edenl | 40/43 | 93% | 0 | 59 |
| forgotten | 0/76 | 0% | 0 | 131 |
| futuretech | 0/57 | 0% | 0 | 134 |
| gdi | 2/60 | 3% | 0 | 101 |
| human2 | 0/69 | 0% | 0 | 57 |
| ixian | 0/57 | 0% | 0 | 59 |
| lnaxis | 0/41 | 0% | 0 | 81 |
| modjapan | 1/69 | 1% | 0 | 106 |
| naxis | 0/73 | 0% | 0 | 118 |
| nod | 1/64 | 1% | 0 | 113 |
| orc2 | 0/60 | 0% | 0 | 40 |
| ordos | 0/65 | 0% | 0 | 57 |
| plymouthl | 44/44 | 100% | 0 | 58 |
| protoss | 0/72 | 0% | 0 | 116 |
| ra2america | 18/66 | 27% | 0 | 217 |
| ra2russia | 0/56 | 0% | 0 | 141 |
| soviet | 0/104 | 0% | 0 | 177 |
| syndicate | 0/65 | 0% | 0 | 153 |
| terran | 0/77 | 0% | 0 | 136 |
| tkm | 0/72 | 0% | 0 | 119 |
| tsgdi | 0/62 | 0% | 0 | 140 |
| tsnod | 0/46 | 0% | 0 | 128 |
| yuri | 0/64 | 0% | 0 | 137 |
| zerg | 0/74 | 0% | 0 | 142 |


## Icon filename compliance (_icon suffix rule)

| faction | icons compliant | % |
|---|---|---|
| allies | 0/61 | 0% |
| asianalliance | 32/71 | 45% |
| cabal | 10/57 | 17% |
| consortium | 59/61 | 96% |
| edenl | 0/43 | 0% |
| forgotten | 53/76 | 69% |
| futuretech | 9/57 | 15% |
| gdi | 7/60 | 11% |
| human2 | 14/16 | 87% |
| ixian | 19/41 | 46% |
| lnaxis | 34/41 | 82% |
| modjapan | 3/68 | 4% |
| naxis | 63/72 | 87% |
| nod | 4/64 | 6% |
| orc2 | 1/6 | 16% |
| ordos | 31/45 | 68% |
| plymouthl | 0/44 | 0% |
| protoss | 1/72 | 1% |
| ra2america | 15/64 | 23% |
| ra2russia | 15/54 | 27% |
| soviet | 1/103 | 0% |
| syndicate | 34/65 | 52% |
| terran | 1/77 | 1% |
| tkm | 0/72 | 0% |
| tsgdi | 0/61 | 0% |
| tsnod | 0/46 | 0% |
| yuri | 30/64 | 46% |
| zerg | 0/74 | 0% |


| faction | icons compliant | % |
|---|---|---|
| allies | 0/61 | 0% |
| asianalliance | 32/71 | 45% |
| cabal | 10/57 | 17% |
| consortium | 59/61 | 96% |
| edenl | 0/43 | 0% |
| forgotten | 53/76 | 69% |
| futuretech | 9/57 | 15% |
| gdi | 7/60 | 11% |
| human2 | 14/16 | 87% |
| ixian | 19/41 | 46% |
| lnaxis | 34/41 | 82% |
| modjapan | 3/68 | 4% |
| naxis | 63/72 | 87% |
| nod | 4/64 | 6% |
| orc2 | 1/6 | 16% |
| ordos | 31/45 | 68% |
| plymouthl | 0/44 | 0% |
| protoss | 1/72 | 1% |
| ra2america | 15/64 | 23% |
| ra2russia | 15/54 | 27% |
| soviet | 1/103 | 0% |
| syndicate | 34/65 | 52% |
| terran | 1/77 | 1% |
| tkm | 0/72 | 0% |
| tsgdi | 0/61 | 0% |
| tsnod | 0/46 | 0% |
| yuri | 30/64 | 46% |
| zerg | 0/74 | 0% |


---

## R2 — Worst-case stacked multipliers (§7.4)

757 units exceed the 2.0× effective-power budget (full ranked table in
`power_budget.md`). Modelling notes: exclusive veterancy ladders
(`rank-veteran == N`) count once at best rank; only conditions attainable by
the owning faction count; temporary auras are excluded, so real peaks are
higher.

**The §7.4 suspects, measured:**

| suspect | measured worst case | reading |
|---|---|---|
| RA2 Allies infantry (Chromium/Prismatic + doctrine stack) | `ra2seal`/`ra2snipe`/`ra2tany` **36.0×** (12.9× damage · 2.8× surv) | the single worst stack in the game — doctrine + battle-lab + hero-infantry lines all multiply |
| Yuri late stack | `yrinit` **30.3×**, `yrltnk` 18.1× | confirms §6.4's "balance problem child" prior |
| CABAL post-TB23 full stack | walkers/aircraft **3.9×** | over budget but sane; trim one Research multiplier or cap ranks |
| Steel Consortium | below RA2/Yuri tier on this metric | its late-game strength is upgrade breadth + unit quality, not stack depth — telemetry still required |

Top of the ranked table:


| faction | unit | damage× | surv× | power× | contributing multipliers |
| ra2america | ra2seal | 12.94 | 2.78 | 36.03 | FirepowerMultiplier@ra2_allies_upgrade_assaultsquadtraining=125; ReloadDelayMultiplier@ra2_allies_upgrade_assaultsquadtraining=80; DamageMultiplier@ra2_allies_upgrade_assaultsquadtraining=90; DamageMultiplier@ra2_allies_upgrade_vanguardtraining=70; FirepowerMultiplier@ra2_allies_upgrade_vanguardtraining=115; FirepowerMultiplier@ra2_allies_upgrade_infiltratorstraining=200; ReloadDelayMultiplier@ra2_allies_upgrade_infiltratorstraining=50; DamageMultiplier@ra2_allies_upgrade_infiltratorstraining=95 |
| ra2america | ra2snipe | 12.94 | 2.78 | 36.03 | FirepowerMultiplier@ra2_allies_upgrade_assaultsquadtraining=125; ReloadDelayMultiplier@ra2_allies_upgrade_assaultsquadtraining=80; DamageMultiplier@ra2_allies_upgrade_assaultsquadtraining=90; DamageMultiplier@ra2_allies_upgrade_vanguardtraining=70; FirepowerMultiplier@ra2_allies_upgrade_vanguardtraining=115; FirepowerMultiplier@ra2_allies_upgrade_infiltratorstraining=200; ReloadDelayMultiplier@ra2_allies_upgrade_infiltratorstraining=50; DamageMultiplier@ra2_allies_upgrade_infiltratorstraining=95 |
| ra2america | ra2tany | 12.94 | 2.78 | 36.03 | FirepowerMultiplier@ra2_allies_upgrade_assaultsquadtraining=125; ReloadDelayMultiplier@ra2_allies_upgrade_assaultsquadtraining=80; DamageMultiplier@ra2_allies_upgrade_assaultsquadtraining=90; DamageMultiplier@ra2_allies_upgrade_vanguardtraining=70; FirepowerMultiplier@ra2_allies_upgrade_vanguardtraining=115; FirepowerMultiplier@ra2_allies_upgrade_infiltratorstraining=200; ReloadDelayMultiplier@ra2_allies_upgrade_infiltratorstraining=50; DamageMultiplier@ra2_allies_upgrade_infiltratorstraining=95 |
| yuri | yrinit | 5.93 | 5.10 | 30.27 | FirepowerMultiplier@global_conscription_buff=110; DamageMultiplier@global_conscription_buff=90; ReloadDelayMultiplier@global_conscription_buff=90; DamageMultiplier@ra2_yuri_upgrade_geneticboost=80; DamageMultiplier@ra2_yuri_upgrade_stealthsuits=90; DamageMultiplier@ra2_yuri_upgrade_psionicfanatics=80; ReloadDelayMultiplier@ra2_yuri_upgrade_psionicfanatics=80; FirepowerMultiplier@ra2_yuri_upgrade_psionicelite=110 |
| yuri | yrlunr | 5.88 | 4.02 | 23.64 | FirepowerMultiplier@global_conscription_buff=110; DamageMultiplier@global_conscription_buff=90; ReloadDelayMultiplier@global_conscription_buff=90; DamageMultiplier@ra2_yuri_upgrade_geneticboost=80; DamageMultiplier@ra2_yuri_upgrade_psionicfanatics=80; ReloadDelayMultiplier@ra2_yuri_upgrade_psionicfanatics=80; FirepowerMultiplier@ra2_yuri_upgrade_psionicelite=110; ReloadDelayMultiplier@ra2_yuri_upgrade_psionicelite=90 |
| yuri | yrgtrp | 5.76 | 3.57 | 20.58 | FirepowerMultiplier@global_conscription_buff=110; DamageMultiplier@global_conscription_buff=90; ReloadDelayMultiplier@global_conscription_buff=90; DamageMultiplier@ra2_yuri_upgrade_geneticboost=80; DamageMultiplier@ra2_yuri_upgrade_stealthsuits=90; FirepowerMultiplier@ra2_yuri_upgrade_gatlingpower=120; ReloadDelayMultiplier@ra2_yuri_upgrade_gatlingspeed=70; DamageMultiplier@ra2_yuri_upgrade_psionicfanatics=80 |
| yuri | yrbrute | 4.71 | 4.02 | 18.91 | FirepowerMultiplier@global_conscription_buff=110; DamageMultiplier@global_conscription_buff=90; ReloadDelayMultiplier@global_conscription_buff=90; DamageMultiplier@ra2_yuri_upgrade_geneticboost=80; DamageMultiplier@ra2_yuri_upgrade_psionicfanatics=80; ReloadDelayMultiplier@ra2_yuri_upgrade_psionicfanatics=80; FirepowerMultiplier@ra2_yuri_upgrade_psionicelite=110; ReloadDelayMultiplier@ra2_yuri_upgrade_psionicelite=90 |
| yuri | yrltnk | 3.60 | 5.03 | 18.10 | DamageMultiplier@ra2_yuri_upgrade_scraparmor=85; DamageMultiplier@ra2_yuri_upgrade_psionicshields=75; DamageMultiplier@ra2_yuri_upgrade_toxicengines=80; FirepowerMultiplier@ra2_yuri_upgrade_lashercannon=200; DamageMultiplier@ra2_yuri_upgrade_lasherarmor=65; DamageMultiplier@RANK-4=60; FirepowerMultiplier@RANK-4=180 |
| yuri | yryuri | 3.36 | 5.10 | 17.15 | FirepowerMultiplier@global_conscription_buff=110; DamageMultiplier@global_conscription_buff=90; ReloadDelayMultiplier@global_conscription_buff=90; DamageMultiplier@ra2_yuri_upgrade_geneticboost=80; DamageMultiplier@ra2_yuri_upgrade_stealthsuits=90; DamageMultiplier@ra2_yuri_upgrade_psionicarmor=70; DamageMultiplier@ra2_yuri_upgrade_psionicfanatics=80; ReloadDelayMultiplier@ra2_yuri_upgrade_psionicfanatics=80 |
| ra2america | ra2rock | 4.84 | 3.28 | 15.85 | FirepowerMultiplier@ra2_allies_upgrade_assaultsquadtraining=125; ReloadDelayMultiplier@ra2_allies_upgrade_assaultsquadtraining=80; DamageMultiplier@ra2_allies_upgrade_assaultsquadtraining=90; DamageMultiplier@ra2_allies_upgrade_vanguardtraining=70; FirepowerMultiplier@ra2_allies_upgrade_vanguardtraining=115; FirepowerMultiplier@ra2_allies_upgrade_infiltratorstraining=105; ReloadDelayMultiplier@ra2_allies_upgrade_infiltratorstraining=95; DamageMultiplier@ra2_allies_upgrade_infiltratorstraining=95 |
| yuri | yryurix | 3.36 | 4.59 | 15.44 | FirepowerMultiplier@global_conscription_buff=110; DamageMultiplier@global_conscription_buff=90; ReloadDelayMultiplier@global_conscription_buff=90; DamageMultiplier@ra2_yuri_upgrade_geneticboost=80; DamageMultiplier@ra2_yuri_upgrade_psionicarmor=70; DamageMultiplier@ra2_yuri_upgrade_psionicfanatics=80; ReloadDelayMultiplier@ra2_yuri_upgrade_psionicfanatics=80; FirepowerMultiplier@ra2_yuri_upgrade_psionicelite=110 |
| ra2america | yrggi | 5.36 | 2.78 | 14.93 | FirepowerMultiplier@ra2_allies_upgrade_assaultsquadtraining=125; ReloadDelayMultiplier@ra2_allies_upgrade_assaultsquadtraining=80; DamageMultiplier@ra2_allies_upgrade_assaultsquadtraining=90; DamageMultiplier@ra2_allies_upgrade_vanguardtraining=70; FirepowerMultiplier@ra2_allies_upgrade_vanguardtraining=115; FirepowerMultiplier@ra2_allies_upgrade_infiltratorstraining=105; ReloadDelayMultiplier@ra2_allies_upgrade_infiltratorstraining=95; DamageMultiplier@ra2_allies_upgrade_infiltratorstraining=95 |
| ra2russia | ra2e2 | 3.51 | 4.17 | 14.63 | FirepowerMultiplier@global_conscription_buff=120; DamageMultiplier@global_conscription_buff=80; ReloadDelayMultiplier@global_conscription_buff=80; DamageMultiplier@ra2_soviets_upgrade_infantryconditioning=50; FirepowerMultiplier@ra2_soviets_upgrade_shocktroopertraining=130; DamageMultiplier@RANK-4=60; FirepowerMultiplier@RANK-4=180 |
| ra2america | yrbfrt | 3.57 | 4.07 | 14.55 | FirepowerMultiplier@ra2_allies_upgrade_assaultsquadtraining=125; ReloadDelayMultiplier@ra2_allies_upgrade_assaultsquadtraining=80; DamageMultiplier@ra2_allies_upgrade_assaultsquadtraining=90; DamageMultiplier@ra2_allies_upgrade_vanguardtraining=70; FirepowerMultiplier@ra2_allies_upgrade_vanguardtraining=115; FirepowerMultiplier@ra2_allies_upgrade_infiltratorstraining=105; ReloadDelayMultiplier@ra2_allies_upgrade_infiltratorstraining=95; DamageMultiplier@ra2_allies_upgrade_infiltratorstraining=95 |
| ra2america | yrbfrt.bot | 3.57 | 4.07 | 14.55 | FirepowerMultiplier@ra2_allies_upgrade_assaultsquadtraining=125; ReloadDelayMultiplier@ra2_allies_upgrade_assaultsquadtraining=80; DamageMultiplier@ra2_allies_upgrade_assaultsquadtraining=90; DamageMultiplier@ra2_allies_upgrade_vanguardtraining=70; FirepowerMultiplier@ra2_allies_upgrade_vanguardtraining=115; FirepowerMultiplier@ra2_allies_upgrade_infiltratorstraining=105; ReloadDelayMultiplier@ra2_allies_upgrade_infiltratorstraining=95; DamageMultiplier@ra2_allies_upgrade_infiltratorstraining=95 |
| ra2america | yrbfrt.bot2 | 3.57 | 4.07 | 14.55 | FirepowerMultiplier@ra2_allies_upgrade_assaultsquadtraining=125; ReloadDelayMultiplier@ra2_allies_upgrade_assaultsquadtraining=80; DamageMultiplier@ra2_allies_upgrade_assaultsquadtraining=90; DamageMultiplier@ra2_allies_upgrade_vanguardtraining=70; FirepowerMultiplier@ra2_allies_upgrade_vanguardtraining=115; FirepowerMultiplier@ra2_allies_upgrade_infiltratorstraining=105; ReloadDelayMultiplier@ra2_allies_upgrade_infiltratorstraining=95; DamageMultiplier@ra2_allies_upgrade_infiltratorstraining=95 |
| nod | obli | 10.00 | 1.43 | 14.29 | FirepowerMultiplier@up_elitecapacitors=160; ReloadDelayMultiplier@up_elitecapacitors=40; DamageMultiplier@RANK-3=70; FirepowerMultiplier@RANK-3=175; ReloadDelayMultiplier@RANK-3=70 |
| human2 | wc2_human_footman | 4.58 | 3.06 | 13.99 | FirepowerMultiplier@WC2SwordUpg=130; FirepowerMultiplier@WC2SwordUpg2=170; DamageMultiplier@WC2HShieldUpg=85; DamageMultiplier@WC2HShieldUpg2=70; DamageMultiplier@RANK-3=55; FirepowerMultiplier@RANK-3=145; ReloadDelayMultiplier@RANK-3=70 |
| human2 | wc2_human_footman2 | 4.58 | 3.06 | 13.99 | FirepowerMultiplier@WC2SwordUpg=130; FirepowerMultiplier@WC2SwordUpg2=170; DamageMultiplier@WC2HShieldUpg=85; DamageMultiplier@WC2HShieldUpg2=70; DamageMultiplier@RANK-3=55; FirepowerMultiplier@RANK-3=145; ReloadDelayMultiplier@RANK-3=70 |
| orc2 | wc2_orc_grunt | 4.58 | 3.06 | 13.99 | FirepowerMultiplier@WC2AxeUpg=130; FirepowerMultiplier@WC2AxeUpg2=170; DamageMultiplier@WC2OShieldUpg=85; DamageMultiplier@WC2OShieldUpg2=70; DamageMultiplier@RANK-3=55; FirepowerMultiplier@RANK-3=145; ReloadDelayMultiplier@RANK-3=70 |
| orc2 | wc2_orc_grunt2 | 4.58 | 3.06 | 13.99 | FirepowerMultiplier@WC2AxeUpg=130; FirepowerMultiplier@WC2AxeUpg2=170; DamageMultiplier@WC2OShieldUpg=85; DamageMultiplier@WC2OShieldUpg2=70; DamageMultiplier@RANK-3=55; FirepowerMultiplier@RANK-3=145; ReloadDelayMultiplier@RANK-3=70 |

---

## Needs human decision

1. The 1,106 shared/unattributed buildables (B1) — neutral vs faction-owned,
   during Phase-1 folder moves.
2. `tsgtplug2`/`tsgtplug3` — dead upgrades or plug-socket consumption?
3. Ordos reaching Harkonnen/Ixian units, Syndicate reaching Asian/Naxis
   units — intended mercenary/market mechanics or gating bugs?
4. Lobby-option tokens (`base-reveal`, `classicproductionqueues`,
   `scaledprices`…) — confirm and whitelist in the detectors.
5. The stale "BuildingFractions Dune Universe" ai.yaml block — delete or
   migrate to ContentPacks names.
6. **CABAL is absent from both the Random and Tournament pools** and still
   titled "CABAL TS (WIP)" (see MATRIX.md) — intentional gating or
   oversight, given Forgotten was just added to both?

