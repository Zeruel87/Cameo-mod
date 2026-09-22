# Physical-state warhead audit

Read-only execution of `tools/audit/audit_physical_state_warheads.py` against
the active `mods/cameo/mod.yaml` include graph.

- Active concrete weapons checked: **2,448**.
- Formula percentage templates checked: **6**.
- Result: **PASS**.

The Flame and Chemical percentage components remain folded into their main
`AreaDamage` warheads and feed the matching physical-state meter. No active
weapon combines a damage-scaled meter with a fixed `ApplyPhysicalState` route
for the same meter. This is structural evidence only; it does not value status
uptime, resistance or pricing.
