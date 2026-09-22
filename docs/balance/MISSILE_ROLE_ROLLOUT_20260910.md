# Missile target-role correction: local candidate

Ground-only missiles use MissileHE, air-only missiles use MissileAA, and missiles targeting both use MissileAP, as Aedis specified on September 10. This corrects armor response and blast shape; it is a gameplay change. The afternoon candidate is uncommitted and is not included in the earlier draft PRs.

## Implemented scope

The first 45 strict Missile-projectile leaves and 25 parent roots with 50 closure members cover 77 unique weapon definitions. Their nominal flat damage and every resolved non-main field are preserved. Their main armor/percentage profiles and blast shapes change to the appropriate role. Already-correct child families retain their existing profile overrides when an ancestor changes role. Five child overrides contain only the few plating rows that actually differ from their new inherited profile.

Seven parent roots remain outside this batch because their descendants include mixed, custom, or extra-damage payloads: TSSAPCMissiles, MigMissiles, MigMissiles_fire, MigMissiles_tesla, MigMissiles_elite, AsianPunisherAG and CycloneRockets. LatinAADefenderCannon uses a Bullet projectile and is not silently treated as a missile.

## Upgrade consequences

The corrected AA Patriot base exposed a Thunderbolt direct-damage regression. Its raw damage increases from 10000 to 12100, the smallest round hundred above the measured 12099 parity threshold. Its firing settings stay unchanged.

Sheridan Cryo's combined loadout can fall 22.3% below the corrected base in the checked centered-damage cases. A raw-damage-only parity proposal would increase its Cryo missile from 16000 to 28100 and would also increase damage-scaled cooling. That proposal is **not applied**. At 18:52 Aedis accepted that Cryo can trade direct damage for stronger control, while requiring status valuation before settling Cryo and Sonic's final damage tradeoffs. The earlier unconditional Sonic no-loss rule is therefore provisional, not a mandate to buff every status upgrade. Current Sonic values remain pending that broader valuation.

Longbow Cryo and SU57 Thermobaric already had direct-damage tradeoffs; some worsen with the base corrections. SU57's Thermobaric weapon was already ground-only while its base is dual-target. Air-table arithmetic is not proof that its upgraded weapon can target aircraft. Upgrade pricing remains deferred.

## Evidence and limits

- Exact source and resolved before/current records: `tools/tests/fixtures/missile_role_history_20260910.json` and `missile_parent_role_history_20260910.json`.
- The 77-definition role/preservation contract and its unrecorded-change guard pass. Existing current upgrade contracts pass after the Patriot correction.
- Grouped historical run: 205 tests, 203 passed and two stale test expectations. Both corrective focused reruns pass. The original pricing golden is unchanged; its test restores its original authored source census. No full-suite-green claim.
- Fresh extraction reconciled 50 changed files out of 67 outputs. Raw differences are limited to 52 armament lists across 17 ledgers; 32 derived sidecars and the global diagnostic context also changed. No HP, cost or movement edits.
- These are static configuration and model checks. No new engine build, game run, publication or merge is claimed.

## Secondary-route follow-up

`tools/audit/target_payload_routes.py` extends the direct-weapon inventory through declared weapon references. It records provenance and custom target tags; candidates still require engine activation, geometry and eligibility review. It does not cover map-local rules, scripts, spawned-actor weapons or support powers.

The Devourer's AA shot previously spawned the shared all-domain AnthraxCloudPurpleLarge. A new actor-owned AA child changes only weapon and Toxic_Light ValidTargets to Air; the shared parent and other consumers retain their behavior. SmokeParticle impacts its own weapon independently, so the parent shot's mask was insufficient. Eight target-policy tests pass, including exact cloud-value preservation. DeepSeek Harness is independently reviewing this follow-up before further rollout.

The Devourer follow-up was checked with a filtered extraction into an external directory: its Zerg raw ledger, derived sidecar and global model constants remain byte-identical. This required no ledger rewrite or repeated whole-roster extraction. Ground-only cloud routes and partial dual-target payloads remain open rather than being declared fixed by the direct-weapon tests.
