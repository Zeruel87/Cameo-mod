# audit_recent_changes — last 14 day(s) of history

Commits reviewed: **666**, files touched: **4912**

| code | meaning | count | blocking |
|---|---|---|---|
| R1 | balance yaml edited without the ledger | 24 | yes |
| R2 | audit script never run by run_all.sh | 10 | yes |
| R3 | provenance (wrong-identity trailer blocks; missing one on the shared identity is review-only) | 29 | partly |
| R4 | engine/mod.config change (needs boot gate) | 5 | no |


## R1 — hand-edited balance numbers (24)

| commit | date | subject | fields |
|---|---|---|---|
| d300295e | 2026-10-01 | packs: materialize 12 hard cross-pack refs (reso | Damage, Range, ReloadDelay, Speed, Spread |
| 2f440999 | 2026-09-26 | W7 tail-2: 5 more de-parented after collision pr | Burst, BurstDelays, Damage, Range, ReloadDelay, Speed, Spread |
| 5eff1183 | 2026-09-26 | rule-4 Versus remediation: restore weapon-parent | BurstDelays, MinRange |
| 01c89a5a | 2026-09-26 | fix(W7): restore Inherits edges where splices ma | Damage |
| 8e553991 | 2026-09-26 | feat(W7): chain-collapse batch-3 — 57 children o | Burst, BurstDelays, Damage, MinRange, Range, ReloadDelay, Speed, Spread |
| 9ec11477 | 2026-09-26 | feat(W7): collapse 52 more weapon->weapon edges  | Damage, MinRange, Range, ReloadDelay, Speed, Spread |
| e4000127 | 2026-09-26 | feat(W7): collapse 55 weapon->weapon edges onto  | BurstDelays, Damage, MinRange, Range, ReloadDelay, Speed, Spread |
| 1ae9c7d0 | 2026-09-26 | R17 chip folds (W5 batch-1): 20 weapons / 21 chi | Damage |
| 2c0cf719 | 2026-09-26 | W8 batch-2: 13 more legacy edges -> covering edg | Burst, BurstDelays, Damage, MinRange, Range, ReloadDelay, Speed |
| 2ba249f0 | 2026-09-26 | feat(W7): convert YuriGatlingTankMG{1,2,3}[_AA]  | ReloadDelay, Speed |
| bc676e8d | 2026-09-26 | W8 batch-1: 52 legacy-template edges -> covering | Damage, MinRange, Range, ReloadDelay, Speed, Spread |
| 90aef52d | 2026-09-26 | W7: replace 19 concrete-weapon inherits with cov | Damage, Range, ReloadDelay, Speed, Spread |
| 6b0f3fdb | 2026-09-25 | W2 sweep: drop 152 dead ^Warhead_ edges (-77), 4 | Range, ReloadDelay |
| 450dcea5 | 2026-09-26 | feat(W7): materialize held-67 ExtraDamage batch  | BurstDelays, Damage, Range, ReloadDelay, Speed, Spread |
| 434413f0 | 2026-09-26 | W7 packs: restore resolved child-order parity (N | Damage, Range, Spread |
| 5407fd8a | 2026-09-25 | W7 ContentPack batch: 97 pack-level weapon-paren | Burst, BurstDelays, Damage, MinRange, Range, ReloadDelay, Speed, Spread |
| c63c0415 | 2026-09-25 | W7: materialize 33 remaining DAWN-file-set weapo | Burst, BurstDelays, Damage, MinRange, Range, ReloadDelay, Speed, Spread |
| 95e18490 | 2026-09-25 | pack self-containment: eliminate hard value-ref  | Burst, BurstDelays, Damage, HP, MinRange, Range, ReloadDelay, Speed, Spread |
| 72468eb3 | 2026-09-25 | TD/TS/SC self-containment: eliminate cross-pack  | Damage, Range, ReloadDelay, Speed |
| f51320c8 | 2026-09-25 | D2k self-containment: eliminate all cross-pack i | Burst, BurstDelays, Range, ReloadDelay, Spread |
| d46ecd9d | 2026-09-24 | W7/W27/R17: DAWN lane — weapon 3-way conversions | Burst, BurstDelays, Damage, MinRange, Range, ReloadDelay, Speed, Spread |
| 86577a7a | 2026-09-24 | W7: convert unclaimed weapon-parent edges in out | Damage, Range, ReloadDelay, Speed, Spread |
| 004a9cb8 | 2026-09-24 | W7: convert all weapon-parent edges in weapons.y | Burst, BurstDelays, Damage, MinRange, Range, ReloadDelay, Speed, Spread |
| d36f3b0a | 2026-09-24 | W23-RA batch 1: TKM file retrofit (20/21 weapons | Damage, MinRange, Range, ReloadDelay, Speed, Spread |


## R2 — audits missing from run_all.sh (10)

| script | problem |
|---|---|
| tools/audit/audit_bot_insurance.py | not invoked by run_all.sh |
| tools/audit/audit_bot_wiring.py | not invoked by run_all.sh |
| tools/audit/audit_chrome_master_freshness.py | not invoked by run_all.sh |
| tools/audit/audit_chrome_scale_variants.py | not invoked by run_all.sh |
| tools/audit/audit_inline_effects.py | not invoked by run_all.sh |
| tools/audit/audit_orphan_removals.py | not invoked by run_all.sh |
| tools/audit/audit_promotion_superiority.py | not invoked by run_all.sh |
| tools/audit/audit_scaled_bullet_overrides.py | not invoked by run_all.sh |
| tools/audit/audit_upgrade_regression.py | not invoked by run_all.sh |
| tools/audit/audit_weapon_identity.py | not invoked by run_all.sh |


## R3 — commits without provenance (29)

| commit | date | author | problem | severity |
|---|---|---|---|---|
| 8a86238b | 2026-10-01 | AedisToru | no Co-Authored-By trailer (shared identity) | review |
| 27de8684 | 2026-10-01 | AedisToru | no Co-Authored-By trailer (shared identity) | review |
| be34aa6d | 2026-10-01 | AedisToru | no Co-Authored-By trailer (shared identity) | review |
| 3e889dc5 | 2026-09-30 | AedisToru | no Co-Authored-By trailer (shared identity) | review |
| a47642cf | 2026-09-30 | AedisToru | no Co-Authored-By trailer (shared identity) | review |
| 2e52abaf | 2026-09-30 | AedisToru | no Co-Authored-By trailer (shared identity) | review |
| d891992d | 2026-09-28 | AedisToru | no Co-Authored-By trailer (shared identity) | review |
| 2a7e2e29 | 2026-09-28 | AedisToru | no Co-Authored-By trailer (shared identity) | review |
| cefceacd | 2026-09-28 | AedisToru | no Co-Authored-By trailer (shared identity) | review |
| 624348f6 | 2026-09-29 | AedisToru | no Co-Authored-By trailer (shared identity) | review |
| 7b0cd5d7 | 2026-09-28 | AedisToru | no Co-Authored-By trailer (shared identity) | review |
| 5b526e79 | 2026-09-28 | Zan Yewang | agent trailer `Devin AI <158243242+devin-ai-integration[bot]@users.noreply.github.com>` on a non-shared identity | review |
| 86b463d6 | 2026-09-28 | Zan Yewang | agent trailer `Devin AI <158243242+devin-ai-integration[bot]@users.noreply.github.com>` on a non-shared identity | review |
| 58005b41 | 2026-09-28 | Zan Yewang | agent trailer `Devin AI <158243242+devin-ai-integration[bot]@users.noreply.github.com>` on a non-shared identity | review |
| b862072c | 2026-09-28 | Zan Yewang | agent trailer `Devin AI <158243242+devin-ai-integration[bot]@users.noreply.github.com>` on a non-shared identity | review |
| 8f1e5579 | 2026-09-28 | Zan Yewang | agent trailer `Devin AI <158243242+devin-ai-integration[bot]@users.noreply.github.com>` on a non-shared identity | review |
| c6c990b7 | 2026-09-28 | Zan Yewang | agent trailer `Devin AI <158243242+devin-ai-integration[bot]@users.noreply.github.com>` on a non-shared identity | review |
| b92183f3 | 2026-09-28 | Blackrobe | agent trailer `OpenAI GPT-6 Astra <noreply@openai.com>` on a non-shared identity | review |
| cfafbbf0 | 2026-09-28 | Blackrobe | agent trailer `OpenAI GPT-6 Astra <noreply@openai.com>` on a non-shared identity | review |
| 045d0c37 | 2026-09-27 | Zan Yewang | agent trailer `Devin AI <devin@cognition.ai>` on a non-shared identity | review |
| 67b18009 | 2026-09-27 | Zan Yewang | agent trailer `Devin AI <devin@cognition.ai>` on a non-shared identity | review |
| e9d50021 | 2026-09-27 | Zan Yewang | agent trailer `Devin AI <158243242+devin-ai-integration[bot]@users.noreply.github.com>` on a non-shared identity | review |
| 56de7db0 | 2026-09-27 | Zan Yewang | agent trailer `Devin AI <158243242+devin-ai-integration[bot]@users.noreply.github.com>` on a non-shared identity | review |
| 043e6c40 | 2026-09-24 | AedisToru | no Co-Authored-By trailer (shared identity) | review |
| 8f53b8dd | 2026-09-23 | devin-ai-integration[bot] | agent trailer `Zan Yewang <inyucedora@gmail.com>` on a non-shared identity | review |
| c6894f19 | 2026-09-23 | devin-ai-integration[bot] | agent trailer `Zan Yewang <inyucedora@gmail.com>` on a non-shared identity | review |
| d81a1bfd | 2026-09-23 | Blackrobe | agent trailer `Codex GPT-5.6 Luna <noreply@openai.com>` on a non-shared identity | review |
| 1519a758 | 2026-09-22 | devin-ai-integration[bot] | agent trailer `Devin AI <devin@cognition.ai>` on a non-shared identity | review |
| fdbb58ef | 2026-09-22 | devin-ai-integration[bot] | agent trailer `Devin AI <devin@cognition.ai>` on a non-shared identity | review |


## R4 — engine/config changes to re-verify (5)

| commit | date | note |
|---|---|---|
| 11f1825c | 2026-09-29 | mod.config changed (rebuild + boot gate required) |
| 5441ace1 | 2026-09-29 | mod.config changed (rebuild + boot gate required) |
| 5b526e79 | 2026-09-28 | mod.config changed (rebuild + boot gate required) |
| 86b463d6 | 2026-09-28 | mod.config changed (rebuild + boot gate required) |
| 7489f8e9 | 2026-09-28 | mod.config changed (rebuild + boot gate required) |


## R5 — most-churned files (re-read these first)

| file | commits touching it |
|---|---|
| DEVELOPMENT_LOG.md | 206 |
| docs/design/AI_ARCHITECTURE.md | 120 |
| mods/cameo/ai/ai.yaml | 118 |
| docs/HANDOFF.md | 103 |
| OpenRA.Mods.CA/Traits/BotModules/SquadManagerBotModuleCA.cs | 72 |
| docs/LESSONS_LEARNED.md | 68 |
| docs/DESIGN.md | 63 |
| OpenRA.Mods.Cameo/Traits/BotModules/BotSituation.cs | 60 |
| docs/design/ROADMAP.md | 53 |
| tools/ai/increment_switches.yaml | 45 |
| docs/design/AI_MODULE_MAP.md | 34 |
| tools/audit/fog_honesty_manifest.json | 34 |
| docs/audit/doc_claims.yaml | 32 |
| docs/balance/derived/tiberiandawn_nod.json | 32 |
| OpenRA.Mods.Cameo.Test/MasterAiBotModuleTest.cs | 30 |


## Reviewer checklist (not machine-checkable)

- [ ] Every yaml change in the window boot-gated (`launch-game.cmd` reached the menu)?
- [ ] C# changes rebuilt (`dotnet build -c Release -p:TargetPlatform=win-x64`)?
- [ ] New actors/weapons named with underscores only, and Fluent keys added?
- [ ] Generated reports under `docs/audit/latest/` regenerated via run_all.sh, not hand-edited?
- [ ] ROADMAP.md updated for finished/queued work?


## Enforcement

R1/R3 block only for commits on or after **2026-08-12**: 24 R1 and 0 R3 of 24/29 findings are in scope; the rest predate the gate.


## FAIL

- 24 R1, 10 R2, 0 R3 blocking finding(s)

