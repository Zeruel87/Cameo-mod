# audit_template_conformance — template values are law (2026-07-19)

## T1 — conyards must use the template Power (100)

_clean_

## T2 — icons under a nonzero Defaults Offset must set Offset: 0,0

_clean_

### T2b — explicit non-zero icon offsets (maintainer visual pass pending; D2k legacy pattern)

- mods/cameo/ContentPacks/D2k/Atreides/yaml/sequences.yaml:709: `hightech.atreides` icon has explicit Offset -30,-24
- mods/cameo/ContentPacks/D2k/Ordos/yaml/sequences.yaml:565: `hightech.ordos` icon has explicit Offset -30,-24
- mods/cameo/ContentPacks/TiberianSun/CABAL/yaml/sequences.yaml:1149: `tscrys` icon has explicit Offset 0, 0, 25
- mods/cameo/ContentPacks/TiberianSun/Forgotten/yaml/sequences.yaml:840: `forgotten_crystalpowerextractor` icon has explicit Offset 0, 0, 25
- mods/cameo/ContentPacks/TiberianSun/Nod/yaml/sequences.yaml:380: `ts_nod_powerplant` icon has explicit Offset 0, 0, 25
- mods/cameo/sequences/d2k.yaml:495: `hightech.atreides` icon has explicit Offset -30,-24
- mods/cameo/sequences/d2k.yaml:1363: `hightech.harkonnen` icon has explicit Offset -30,-24

Total blocking findings: 0 (T2b informational: 7)
