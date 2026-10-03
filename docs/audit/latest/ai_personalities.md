# AI personality audit

- Selector conditions: `personality-expansion, personality-guerrilla, personality-rush, personality-steamroller, personality-tech, personality-turtle`
- Consumed conditions: `personality-expansion, personality-guerrilla, personality-rush, personality-steamroller, personality-tech, personality-turtle`
- Personality blocks: 6/6
- Personality notifications: 6/6
- BotLimits reaction delays: `7500, 6750, 6000, 5250, 4500, 3750, 3000, 2250, 1500, 750`
- Explicit tuning allow-list: `AttackForceInterval, DangerScanRadius, FormationMaxLeadCells, FormationMaxStalledLeadCells, FormationMovement, FormationTrailCells, HarasserTypes, HighValueTargetPriority, IdleScanRadius, IndirectRouteChance, JoinGuerrilla, MaxBaseRadius, MaxGuerrillaSize, MaxGuerrillaSquads, MaxGuerrillaSquadsLate, MaxIdleUnits, MinimumAttackForceDelay, PreferMainTarget, ProtectUnitScanRadius, ProtectionScanRadius, RoleMix, RoleMixRoleFloorPct, SquadSize, SquadSizeRandomBonus, SquadValue, SquadValueMaxEarlyBonus, SquadValueMaxLateBonus, SquadValueMinLateBonus, StageBeforeAssault, StageCompositionTicks, StageRequiredRoles`

## PASS
- Shared non-tuning fields are byte-identical across all personality instances.
- BotPersonalityController and squad-manager condition sets match exactly.
- Personality conditions have exactly one matching notification block each.
- No dead RushInterval/RushAttackScanRadius keys remain.
- Every per-tier BotLimits number and production multiplier lies on one equal-step line (DESIGN §19.1).
- ScaleTargetsBotModule writes every category and field, Min <= Max, the tech line is 1 1 1 1 2 2 2 2 3 3 and minute 0 equals the DESIGN 19.1 table (AI_ARCHITECTURE 12.22).
- No module gates on a difficulty-tier condition (DESIGN §19.1); strength scales via BotLimits.
