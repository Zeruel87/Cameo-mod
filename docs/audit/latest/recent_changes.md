# audit_recent_changes — last 14 day(s) of history

Commits reviewed: **376**, files touched: **876**

| code | meaning | count | blocking |
|---|---|---|---|
| R1 | balance yaml edited without the ledger | 16 | yes |
| R2 | audit script never run by run_all.sh | 3 | yes |
| R3 | provenance (wrong-identity trailer blocks; missing one on the shared identity is review-only) | 12 | partly |
| R4 | engine/mod.config change (needs boot gate) | 8 | no |


## R1 — hand-edited balance numbers (16)

| commit | date | subject | fields |
|---|---|---|---|
| 71ea9200 | 2026-08-23 | separate AI chrono from chrono reinforcements an | Range, ReloadDelay |
| c49a8f20 | 2026-08-23 | Add drop pods to the dropship bay and rework scr | Range, Speed |
| 924e4f68 | 2026-08-23 | Add the dropship bay | BuildDuration, Cost, HP, Speed |
| 47a66b6c | 2026-08-21 | fix(w24): the nuclear batch collapsed 15 warhead | Damage |
| 33959758 | 2026-08-21 | HeatRayBeam1-4: complete Inferno 3-way split + s | Range, ReloadDelay |
| 89c94c89 | 2026-08-20 | D2K: 3-way split OrniBomb and OrniBombC | Range |
| 86634636 | 2026-08-20 | W24: D2K ^ORocket/^OMissile 3-way split | MinRange |
| bd215785 | 2026-08-18 | feat(weapons): convert legacy flame/chemical App | Damage |
| b010cc6e | 2026-08-18 | Hover Transport Added | Cost, HP, Range, Speed |
| 786bb2f2 | 2026-08-18 | Added all Combat ships for GDI/Nod | Burst, BurstDelays, Cost, Damage, HP, Range, ReloadDelay, Speed |
| a20cda71 | 2026-08-12 | W2: convert wc2deathknightDeathAndDecay_Hit to I | Damage |
| 086efefc | 2026-08-11 | feat(balance): convert HonestJohn to 3-way split | Damage |
| 14713d57 | 2026-08-11 | fix(tesla): rename extra-damage chips and restor | Damage |
| 0d2cd6e8 | 2026-08-10 | feat(warhead): auto-scaling Integrity/EMP + unif | Damage, Spread |
| 39995bba | 2026-08-10 | balance(weapons): wire D2K_StormGunInf/Cymek to  | Damage |
| 4e9c3198 | 2026-08-10 | balance(weapons): collapse Exorcist family + Shr | Damage |


## R2 — audits missing from run_all.sh (3)

| script | problem |
|---|---|
| tools/audit/audit_inline_effects.py | not invoked by run_all.sh |
| tools/audit/audit_upgrade_regression.py | not invoked by run_all.sh |
| tools/audit/audit_weapon_identity.py | not invoked by run_all.sh |


## R3 — commits without provenance (12)

| commit | date | author | problem | severity |
|---|---|---|---|---|
| 1d18d5d4 | 2026-08-23 | Claude | agent trailer `Claude Opus 5 <noreply@anthropic.com>` on a non-shared identity | review |
| 4ec4fd1c | 2026-08-23 | Claude | agent trailer `Claude Opus 5 <noreply@anthropic.com>` on a non-shared identity | review |
| 20f15194 | 2026-08-23 | Claude | agent trailer `Claude Opus 5 <noreply@anthropic.com>` on a non-shared identity | review |
| 026963fd | 2026-08-23 | Claude | agent trailer `Claude Opus 5 <noreply@anthropic.com>` on a non-shared identity | review |
| 2bb046ae | 2026-08-20 | Zan Yewang | agent trailer `Devin AI <devin@cognition.ai>` on a non-shared identity | review |
| 7800eaab | 2026-08-17 | Zan Yewang | agent trailer `Devin AI <devin@cognition.ai>` on a non-shared identity | review |
| 519105d4 | 2026-08-16 | Zan Yewang | agent trailer `Devin AI <devin@cognition.ai>` on a non-shared identity | review |
| e62ac4ea | 2026-08-16 | Zan Yewang | agent trailer `Devin AI <devin@cognition.ai>` on a non-shared identity | review |
| 988a7580 | 2026-08-11 | Devin AI | agent trailer `Devin AI <devin@cognition.ai>` on a non-shared identity | review |
| 1d5d5e55 | 2026-08-11 | Zan Yewang | agent trailer `Devin AI <devin@cognition.ai>` on a non-shared identity | review |
| 7155a0f1 | 2026-08-11 | AedisToru | no Co-Authored-By trailer (shared identity) | review |
| 59ade89e | 2026-08-11 | AedisToru | no Co-Authored-By trailer (shared identity) | review |


## R4 — engine/config changes to re-verify (8)

| commit | date | note |
|---|---|---|
| f1c64e93 | 2026-08-22 | mod.config changed (rebuild + boot gate required) |
| c69604be | 2026-08-17 | mod.config changed (rebuild + boot gate required) |
| a74638de | 2026-08-16 | mod.config changed (rebuild + boot gate required) |
| 41f2870b | 2026-08-16 | mod.config changed (rebuild + boot gate required) |
| d6e8712c | 2026-08-15 | mod.config changed (rebuild + boot gate required) |
| 988a7580 | 2026-08-11 | mod.config changed (rebuild + boot gate required) |
| 1d5d5e55 | 2026-08-11 | mod.config changed (rebuild + boot gate required) |
| f2284b1c | 2026-08-11 | mod.config changed (rebuild + boot gate required) |


## R5 — most-churned files (re-read these first)

| file | commits touching it |
|---|---|
| docs/design/BALANCE_PROGRAM_PLAN.md | 104 |
| mods/cameo/weapons/weapons.yaml | 66 |
| tools/balance/gen_weapon_template.py | 51 |
| docs/balance/derived/redalert_soviets.json | 46 |
| docs/design/ROADMAP.md | 42 |
| docs/balance/derived/d2k_ixian.json | 38 |
| docs/balance/derived/redalert2mod_consortium.json | 38 |
| docs/balance/derived/redalert2mod_futuretech.json | 38 |
| docs/balance/derived/tiberiandawn_nod.json | 38 |
| docs/balance/derived/tiberiansun_forgotten.json | 38 |
| DEVELOPMENT_LOG.md | 38 |
| docs/balance/derived/shared_redalert.json | 36 |
| docs/balance/derived/starcraft_protoss.json | 36 |
| docs/balance/derived/tiberiansun_nod.json | 36 |
| docs/balance/derived/d2k_ordos.json | 35 |


## Reviewer checklist (not machine-checkable)

- [ ] Every yaml change in the window boot-gated (`launch-game.cmd` reached the menu)?
- [ ] C# changes rebuilt (`dotnet build -c Release -p:TargetPlatform=win-x64`)?
- [ ] New actors/weapons named with underscores only, and Fluent keys added?
- [ ] Generated reports under `docs/audit/latest/` regenerated via run_all.sh, not hand-edited?
- [ ] ROADMAP.md updated for finished/queued work?


## Enforcement

R1/R3 block only for commits on or after **2026-08-12**: 11 R1 and 0 R3 of 16/12 findings are in scope; the rest predate the gate.


## FAIL

- 11 R1, 3 R2, 0 R3 blocking finding(s)

