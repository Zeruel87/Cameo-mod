# audit_recent_changes — last 14 day(s) of history

Commits reviewed: **199**, files touched: **881**

| code | meaning | count | blocking |
|---|---|---|---|
| R1 | balance yaml edited without the ledger | 22 | yes |
| R2 | audit script never run by run_all.sh | 4 | yes |
| R3 | provenance (wrong-identity trailer blocks; missing one on the shared identity is review-only) | 19 | partly |
| R4 | engine/mod.config change (needs boot gate) | 0 | no |


## R1 — hand-edited balance numbers (22)

| commit | date | subject | fields |
|---|---|---|---|
| 1858d013 | 2026-09-05 | feat: add Corrino siege tank + husk, update heav | Cost, HP, Range, Speed |
| c2b77716 | 2026-09-05 | feat: add Corrino gunship and advanced carryall | Cost, HP, Range, Speed |
| cda4c54e | 2026-09-05 | fix: remove duplicate inherits and restore merge | BurstDelays, Damage, Range, ReloadDelay, Speed, Spread |
| 9f7d2c09 | 2026-09-02 | Polish projectile streaks and defensive fire | Speed |
| d83ed80e | 2026-08-29 | Remove remaining sniper splash and strengthen we | Spread |
| 7de94587 | 2026-08-29 | Repair paid weapon upgrade contracts (#310) | Damage, Range, ReloadDelay |
| 58a3e2d7 | 2026-08-29 | Restore real bullet projectile speeds (#305) | Speed |
| 5a8669b7 | 2026-08-26 | feat(weapons): W24 collapse 4 same-family weapon | Damage |
| 05d70935 | 2026-08-26 | feat(weapons): W24 collapse StarCraft/Zerg Infes | Damage |
| 40f74a47 | 2026-08-25 | feat(weapons): W24 collapse 12 same-family weapo | Damage |
| 9ebd13c2 | 2026-08-25 | feat(weapons): W24 collapse 3 StarCraft/Terran s | Damage |
| 0bd58c2a | 2026-08-25 | feat(weapons): W24 collapse 3 Consortium Bullet_ | Damage |
| 94cd582b | 2026-08-25 | D2k Phase 4: Atreides/Harkonnen/Corrino expansio | Cost, Damage, HP, Range, ReloadDelay, Speed |
| 3498a54e | 2026-08-25 | D2k Corrino APC + trooper + Ordos sequence fixes | Cost, HP, Speed |
| b5e439cb | 2026-08-25 | W24 TiberianDawn/GDI bullet collapses + Ordos bu | Damage |
| d519ceaf | 2026-08-25 | D2k Corrino: corrino_cannon weapon, heavyfactory | ReloadDelay |
| af3ff5f9 | 2026-08-25 | D2k Corrino pack expansion: infantry, aircraft,  | Cost, HP, Range, Speed |
| 07135e6f | 2026-08-25 | D2k Corrino pack expansion: buggy vehicle + miss | Cost, Damage, HP, Range, ReloadDelay, Speed |
| afdaae46 | 2026-08-25 | D2k Harkonnen pack completion: infantry, aircraf | Cost, HP, Range, Speed |
| f07d8d35 | 2026-08-25 | D2k faction rollout: Atreides completion + Corri | BuildDuration, Cost, HP, Range, ReloadDelay, Speed |
| d11b9072 | 2026-08-25 | feat(warcraft2): port 4 hero weapon pairs from w | Cost, Damage, HP, Range, ReloadDelay, Speed |
| 5a74091b | 2026-08-25 | W24 A12: collapse ATMine (RedAlert Shared) onto  | Damage |


## R2 — audits missing from run_all.sh (4)

| script | problem |
|---|---|
| tools/audit/audit_inline_effects.py | not invoked by run_all.sh |
| tools/audit/audit_scaled_bullet_overrides.py | not invoked by run_all.sh |
| tools/audit/audit_upgrade_regression.py | not invoked by run_all.sh |
| tools/audit/audit_weapon_identity.py | not invoked by run_all.sh |


## R3 — commits without provenance (19)

| commit | date | author | problem | severity |
|---|---|---|---|---|
| 3256bb36 | 2026-08-31 | Devin AI | agent trailer `Devin AI <devin@cognition.ai>` on a non-shared identity | review |
| d3f188d0 | 2026-08-31 | Devin AI | agent trailer `Devin AI <devin@cognition.ai>` on a non-shared identity | review |
| c91de468 | 2026-08-31 | Devin AI | agent trailer `Devin AI <devin@cognition.ai>` on a non-shared identity | review |
| e2ed9716 | 2026-08-28 | Claude | agent trailer `Claude Opus 5 <noreply@anthropic.com>` on a non-shared identity | review |
| 485dfc9a | 2026-08-28 | Claude | agent trailer `Claude Opus 5 <noreply@anthropic.com>` on a non-shared identity | review |
| 1173d0bf | 2026-08-28 | Claude | agent trailer `Claude Opus 5 <noreply@anthropic.com>` on a non-shared identity | review |
| 7033824c | 2026-08-28 | Claude | agent trailer `Claude Opus 5 <noreply@anthropic.com>` on a non-shared identity | review |
| 018e7fe6 | 2026-08-28 | Claude | agent trailer `Claude Opus 5 <noreply@anthropic.com>` on a non-shared identity | review |
| c4c6744c | 2026-08-28 | Claude | agent trailer `Claude Opus 5 <noreply@anthropic.com>` on a non-shared identity | review |
| 1a00da5f | 2026-08-28 | Claude | agent trailer `Claude Opus 5 <noreply@anthropic.com>` on a non-shared identity | review |
| a3aaa7ec | 2026-08-28 | Claude | agent trailer `Claude Opus 5 <noreply@anthropic.com>` on a non-shared identity | review |
| 5d807dc6 | 2026-08-26 | AedisToru | no Co-Authored-By trailer (shared identity) | review |
| c71bde9d | 2026-08-25 | AedisToru | no Co-Authored-By trailer (shared identity) | review |
| ec2457c0 | 2026-08-25 | AedisToru | no Co-Authored-By trailer (shared identity) | review |
| ccace5a5 | 2026-08-25 | AedisToru | no Co-Authored-By trailer (shared identity) | review |
| 36ee102c | 2026-08-24 | Devin AI | agent trailer `Devin AI <devin@cognition.ai>` on a non-shared identity | review |
| 75238eb3 | 2026-08-24 | Devin AI | agent trailer `Devin AI <devin@cognition.ai>` on a non-shared identity | review |
| 5f0f2828 | 2026-08-24 | Devin AI | agent trailer `Devin AI <devin@cognition.ai>` on a non-shared identity | review |
| 1d18d5d4 | 2026-08-23 | Claude | agent trailer `Claude Opus 5 <noreply@anthropic.com>` on a non-shared identity | review |


## R4 — engine/config changes to re-verify (0)

_none found_


## R5 — most-churned files (re-read these first)

| file | commits touching it |
|---|---|
| DEVELOPMENT_LOG.md | 79 |
| docs/HANDOFF.md | 49 |
| tools/audit/audit_warhead_split.py | 40 |
| docs/design/BALANCE_PROGRAM_PLAN.md | 40 |
| docs/balance/derived/redalert_soviets.json | 33 |
| docs/balance/derived/tiberiansun_forgotten.json | 29 |
| docs/balance/derived/d2k_ixian.json | 28 |
| docs/audit/doc_claims.yaml | 27 |
| docs/balance/derived/tiberiansun_nod.json | 27 |
| docs/audit/SUMMARY.md | 27 |
| docs/balance/derived/tiberiansun_gdi.json | 26 |
| mods/cameo/ContentPacks/RedAlert/Soviets/yaml/weapons.yaml | 26 |
| docs/balance/derived/redalert2_yuri.json | 25 |
| docs/balance/derived/redalert2mod_asianalliance.json | 25 |
| docs/balance/derived/redalert2mod_futuretech.json | 25 |


## Reviewer checklist (not machine-checkable)

- [ ] Every yaml change in the window boot-gated (`launch-game.cmd` reached the menu)?
- [ ] C# changes rebuilt (`dotnet build -c Release -p:TargetPlatform=win-x64`)?
- [ ] New actors/weapons named with underscores only, and Fluent keys added?
- [ ] Generated reports under `docs/audit/latest/` regenerated via run_all.sh, not hand-edited?
- [ ] ROADMAP.md updated for finished/queued work?


## Enforcement

R1/R3 block only for commits on or after **2026-08-12**: 22 R1 and 0 R3 of 22/19 findings are in scope; the rest predate the gate.


## FAIL

- 22 R1, 4 R2, 0 R3 blocking finding(s)

