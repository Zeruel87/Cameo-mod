# audit_recent_changes — last 14 day(s) of history

Commits reviewed: **430**, files touched: **1452**

| code | meaning | count | blocking |
|---|---|---|---|
| R1 | balance yaml edited without the ledger | 18 | yes |
| R2 | audit script never run by run_all.sh | 4 | yes |
| R3 | provenance (wrong-identity trailer blocks; missing one on the shared identity is review-only) | 35 | partly |
| R4 | engine/mod.config change (needs boot gate) | 1 | no |


## R1 — hand-edited balance numbers (18)

| commit | date | subject | fields |
|---|---|---|---|
| 50b7d001 | 2026-09-09 | TS Civilian Buildings and Tilesets for Urban Tem | Range |
| 5fb3fce8 | 2026-09-07 | W24 lane1 batch 4: TSBoatcannon + TSSonicZapWeap | Damage |
| e3730e19 | 2026-09-07 | W24 lane1 batch 3: TSLocustBombChem collapse (Ch | Damage |
| 8c429fa3 | 2026-09-07 | W24 lane1 batch 2: collapse 6 weapons to single  | Damage |
| e779558f | 2026-09-07 | W24 lane1 batch 1: collapse 10 TiberianSun broad | Damage |
| 4c541091 | 2026-09-07 | fix(w24): LANE-3 batch 6 - 15 collapses (1Dam +  | Damage |
| b13f1e41 | 2026-09-07 | fix(w24): LANE-3 batch 5 - 13 collapses (1Dam pl | Damage |
| 22a88fc5 | 2026-09-07 | fix(w24): LANE-3 batch 4 - 8 collapses (autogun_ | Damage |
| 334cff6e | 2026-09-07 | fix(w24): LANE-3 batch 3 - 10 collapses incl. tw | Damage |
| 5ab07259 | 2026-09-07 | fix(w24): LANE-3 batch 2 - 3 shipped-damage repa | Damage |
| 5be0ad30 | 2026-09-07 | fix(w24): LANE-3 batch 1 - collapse 10 multi-mai | Damage |
| 1858d013 | 2026-09-05 | feat: add Corrino siege tank + husk, update heav | Cost, HP, Range, Speed |
| c2b77716 | 2026-09-05 | feat: add Corrino gunship and advanced carryall | Cost, HP, Range, Speed |
| cda4c54e | 2026-09-05 | fix: remove duplicate inherits and restore merge | BurstDelays, Damage, Range, ReloadDelay, Speed, Spread |
| 9f7d2c09 | 2026-09-02 | Polish projectile streaks and defensive fire | Speed |
| d83ed80e | 2026-08-29 | Remove remaining sniper splash and strengthen we | Spread |
| 7de94587 | 2026-08-29 | Repair paid weapon upgrade contracts (#310) | Damage, Range, ReloadDelay |
| 58a3e2d7 | 2026-08-29 | Restore real bullet projectile speeds (#305) | Speed |


## R2 — audits missing from run_all.sh (4)

| script | problem |
|---|---|
| tools/audit/audit_inline_effects.py | not invoked by run_all.sh |
| tools/audit/audit_scaled_bullet_overrides.py | not invoked by run_all.sh |
| tools/audit/audit_upgrade_regression.py | not invoked by run_all.sh |
| tools/audit/audit_weapon_identity.py | not invoked by run_all.sh |


## R3 — commits without provenance (35)

| commit | date | author | problem | severity |
|---|---|---|---|---|
| d21252e4 | 2026-09-10 | Blackrobe | agent trailer `GPT-6 Astra <noreply@openai.com>` on a non-shared identity | review |
| 71393299 | 2026-09-10 | Blackrobe | agent trailer `GPT-6 Astra <noreply@openai.com>` on a non-shared identity | review |
| e785b43a | 2026-09-10 | Blackrobe | agent trailer `GPT-6 Astra <noreply@openai.com>` on a non-shared identity | review |
| 34ca0606 | 2026-09-10 | Blackrobe | agent trailer `GPT-6 Astra <noreply@openai.com>` on a non-shared identity | review |
| 176a1887 | 2026-09-10 | Blackrobe | agent trailer `GPT-6 Astra <noreply@openai.com>` on a non-shared identity | review |
| 810c5440 | 2026-09-10 | Blackrobe | agent trailer `GPT-6 Astra <noreply@openai.com>` on a non-shared identity | review |
| ab4a7a99 | 2026-09-10 | Blackrobe | agent trailer `GPT-6 Astra <noreply@openai.com>` on a non-shared identity | review |
| 4b4b354f | 2026-09-10 | Blackrobe | agent trailer `GPT-6 Astra <noreply@openai.com>` on a non-shared identity | review |
| 0a0b7f3d | 2026-09-10 | Blackrobe | agent trailer `GPT-6 Astra <noreply@openai.com>` on a non-shared identity | review |
| 29462ded | 2026-09-10 | Blackrobe | agent trailer `GPT-6 Astra <noreply@openai.com>` on a non-shared identity | review |
| 86b41c00 | 2026-09-09 | Blackrobe | agent trailer `Codex <noreply@openai.com>` on a non-shared identity | review |
| 8c9457d7 | 2026-09-09 | Blackrobe | agent trailer `Codex GPT-6 Astra <noreply@openai.com>` on a non-shared identity | review |
| 6ade521b | 2026-09-09 | Blackrobe | agent trailer `Codex GPT-6 Astra <noreply@openai.com>` on a non-shared identity | review |
| 21c994a4 | 2026-09-09 | Blackrobe | agent trailer `Codex GPT-6 Astra <noreply@openai.com>` on a non-shared identity | review |
| 0d05b4fb | 2026-09-07 | AedisToru | no Co-Authored-By trailer (shared identity) | review |
| 5bb76c22 | 2026-09-07 | Blackrobe | agent trailer `Codex <noreply@openai.com>` on a non-shared identity | review |
| 29105238 | 2026-09-06 | Blackrobe | agent trailer `Codex <noreply@openai.com>` on a non-shared identity | review |
| 9bc45e66 | 2026-09-06 | AedisToru | no Co-Authored-By trailer (shared identity) | review |
| 08a43574 | 2026-09-06 | AedisToru | no Co-Authored-By trailer (shared identity) | review |
| 15a08466 | 2026-09-06 | devin-ai-integration[bot] | agent trailer `Devin AI <devin@cognition.ai>` on a non-shared identity | review |
| 979d172c | 2026-09-05 | AedisToru | no Co-Authored-By trailer (shared identity) | review |
| c6313f50 | 2026-09-05 | AedisToru | no Co-Authored-By trailer (shared identity) | review |
| 82dd5f70 | 2026-09-01 | Devin AI | agent trailer `Devin AI <devin@cognition.ai>` on a non-shared identity | review |
| e70ab6cd | 2026-09-01 | Devin AI | agent trailer `Devin AI <devin@cognition.ai>` on a non-shared identity | review |
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


## R4 — engine/config changes to re-verify (1)

| commit | date | note |
|---|---|---|
| d219a3cb | 2026-09-03 | mod.config changed (rebuild + boot gate required) |


## R5 — most-churned files (re-read these first)

| file | commits touching it |
|---|---|
| DEVELOPMENT_LOG.md | 151 |
| docs/HANDOFF.md | 64 |
| mods/cameo/ContentPacks/D2k/Ordos/yaml/weapons.yaml | 32 |
| docs/balance/derived/redalert_soviets.json | 26 |
| docs/balance/derived/d2k_ordos.json | 26 |
| mods/cameo/ContentPacks/RedAlert/Soviets/yaml/weapons.yaml | 25 |
| mods/cameo/ContentPacks/TiberianDawn/GDI/yaml/weapons.yaml | 25 |
| tools/audit/audit_warhead_split.py | 25 |
| docs/balance/derived/redalert_allies.json | 24 |
| mods/cameo/ContentPacks/TiberianSun/GDI/yaml/weapons.yaml | 23 |
| mods/cameo/ContentPacks/RedAlert/Shared/yaml/weapons.yaml | 22 |
| docs/balance/derived/shared_redalert.json | 22 |
| docs/balance/derived/redalert2mod_consortium.json | 22 |
| docs/balance/derived/tiberiansun_gdi.json | 22 |
| mods/cameo/ContentPacks/TiberianSun/Forgotten/yaml/weapons.yaml | 22 |


## Reviewer checklist (not machine-checkable)

- [ ] Every yaml change in the window boot-gated (`launch-game.cmd` reached the menu)?
- [ ] C# changes rebuilt (`dotnet build -c Release -p:TargetPlatform=win-x64`)?
- [ ] New actors/weapons named with underscores only, and Fluent keys added?
- [ ] Generated reports under `docs/audit/latest/` regenerated via run_all.sh, not hand-edited?
- [ ] ROADMAP.md updated for finished/queued work?


## Enforcement

R1/R3 block only for commits on or after **2026-08-12**: 18 R1 and 0 R3 of 18/35 findings are in scope; the rest predate the gate.


## FAIL

- 18 R1, 4 R2, 0 R3 blocking finding(s)

