# R8 runtime contract — 2026-09-13

The original R8 batch sized pools and added reload traits, but the engine consumes ammo from `AmmoPool`'s attack notification after an attack is selected. A pool without an ammo-dependent firing gate therefore still permits empty-pool shots. Carrier re-entry also refills every slave pool through `EnterCarrierMaster`; the reload trait is an explicit deployed/in-flight recovery policy.

The follow-up contract adds, for every in-scope carrier slave:

- `AmmoPool.AmmoCondition: ammo`;
- `AttackAircraft.RequiresCondition: ammo`;
- a per-armament minimum-ammo pause gate (`!ammo` for one ammo, `ammo < N` for `AmmoUsage: N`) where an existing armament gate was absent or too weak.

The generated apply tool now emits and checks this contract. The static audit reports 0 defects across 14 in-scope slaves and keeps five suicide slaves out of scope. The rule arithmetic still reports one full attack draining the planned pool and a nominal empty-to-full reload rate of 100 ticks; those calculations are separate from runtime elapsed-time proof.

Validation for this candidate:

- `python tools/audit/audit_ammo_cadence.py` — exit 0, A2 0/14;
- `python tools/balance/apply_carrier_slave_ammo.py --apply` — generated contract, invariants pass;
- menu boot reached `MenuPostProcessEffect.PostWorldLoaded` after the YAML gate change, with 0 exception logs.

No ledger or INI corpus changes are included in this runtime-contract follow-up.
