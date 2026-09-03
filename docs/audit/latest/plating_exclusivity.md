# audit_plating_exclusivity — one plating per actor, and a plating is a TYPE

Found **7** plating grant(s) across **7** definition(s), over the 5 platings (ARMOR, BLAST, COMPOSITE, HAZMAT, REFLECTOR).

## X1 — every actor's platings must be gated apart

32 actor(s) can reach more than one plating — normal, as long as one exclusion group covers them all.

_clean_ — every multi-plating actor's upgrades share one exclusion group.

## X2 — a plating is a type, not an amount

_clean_ — no plating is stacked with a modifier below 90.

## The plating layer as it ships

| definition | plating | condition |
|---|---|---|
| `^DefaultInfantry` | **HAZMAT** | `hazmatsuits` |
| `^JunkArmor` | **ARMOR** | `forgotten_upgrade_junkarmor` |
| `^RA2AlliedCompositeArmorPlatings` | **COMPOSITE** | `ra2_allies_upgrade_compositearmorplating` |
| `^RA2AlliedReflectiveArmorPlatings` | **REFLECTOR** | `ra2_allies_upgrade_reflectivearmorplating` |
| `^RA2SovietsReactiveArmor` | **HAZMAT** | `ra2_soviets_doctrine_reactivearmor` |
| `^RA2SovietsTeslaDischargeArmor` | **REFLECTOR** | `ra2_soviets_doctrine_tesladischargearmor` |
| `^RA2YuriScrapArmor` | **ARMOR** | `yuri_doctrine_scrapvehiclearmor` |
