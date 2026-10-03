# R14 nuclear-ring versus current AreaDamage

**Read-only exact-equivalence review. No YAML or runtime code is changed.**

Weapons reviewed: **10**; requiring further review: **10**.

## Result

No exact conversion candidate is established by this bounded screen. The measured falloff-shape and target-set differences require full predicate, timing and integer-damage review before any conversion.

Current `AreaDamage` provides one uniform tick interval, one shared falloff profile and one shared target set. The table records sampled differences against those fields. It does not claim an impossibility proof: integer damage rounding, target predicates, same-time or unknown scheduling, and explicit `Range` remain outside this screen.

| weapon | file | status | observed differences | limitations |
|---|---|---|---|---|
| `CabalMagicNuke` | `mods/cameo/ContentPacks/TiberianSun/CABAL/yaml/weapons.yaml` | `requires_review` | `Warhead@1Dam_impact` vs `Warhead@4Dam_areanuke1` at 0/500 WDist: 1000:750 vs 1000:875; `Warhead@1Dam_impact` targets Air, Ground, Water; `Warhead@4Dam_areanuke1` targets Air, Ground, Underwater, Water | incomplete seven-payload evidence (6/7) |
| `CrateNuke` | `mods/cameo/ContentPacks/RedAlert/Shared/yaml/weapons.yaml` | `requires_review` | `Warhead@4Dam_areanuke1` vs `Warhead@1Dam_impact` at 0/512 WDist: 1000:800 vs 1000:684 | incomplete seven-payload evidence (2/7); one or more payload delays are unspecified |
| `ExecutionerDeath` | `mods/cameo/ContentPacks/RedAlert/Japan/yaml/weapons.yaml` | `requires_review` | `Warhead@1Dam_impact` vs `Warhead@4Dam_areanuke1` at 0/250 WDist: 1000:750 vs 1000:875; `Warhead@1Dam_impact` targets Air, Ground, Water; `Warhead@4Dam_areanuke1` targets Air, Ground, Underwater, Water | one or more payload delays are unspecified |
| `HermitExplode` | `mods/cameo/ContentPacks/StarCraft/Zerg/yaml/weapons.yaml` | `requires_review` | `Warhead@1Dam_impact` vs `Warhead@4Dam_areanuke1` at 0/250 WDist: 1000:750 vs 1000:875; `Warhead@1Dam_impact` targets Air, Ground, Water; `Warhead@4Dam_areanuke1` targets Air, Ground, Underwater, Water | one or more payload delays are unspecified |
| `MiniNova` | `mods/cameo/weapons/outpost2.yaml` | `requires_review` | `Warhead@1Dam_impact` vs `Warhead@4Dam_areanuke1` at 0/250 WDist: 1000:750 vs 1000:875; `Warhead@1Dam_impact` targets Air, Ground, Water; `Warhead@4Dam_areanuke1` targets Air, Ground, Underwater, Water | one or more payload delays are unspecified |
| `MiniNuke` | `mods/cameo/ContentPacks/RedAlert/Shared/yaml/weapons.yaml` | `requires_review` | `Warhead@1Dam_impact` vs `Warhead@4Dam_areanuke1` at 0/250 WDist: 1000:750 vs 1000:875; `Warhead@1Dam_impact` targets Air, Ground, Water; `Warhead@4Dam_areanuke1` targets Air, Ground, Underwater, Water | one or more payload delays are unspecified |
| `PulseMissile` | `mods/cameo/weapons/d2k.yaml` | `requires_review` | `Warhead@1Dam_impact` vs `Warhead@4Dam_areanuke1` at 0/500 WDist: 1000:750 vs 1000:875; `Warhead@1Dam_impact` targets Air, Ground, Water; `Warhead@4Dam_areanuke1` targets Air, Ground, Underwater, Water | incomplete seven-payload evidence (6/7) |
| `RA2DemoBomb` | `mods/cameo/ContentPacks/RedAlert2/Shared/yaml/weapons.yaml` | `requires_review` | `Warhead@1Dam_impact` vs `Warhead@4Dam_areanuke1` at 0/250 WDist: 1000:750 vs 1000:875; `Warhead@1Dam_impact` targets Air, Ground, Water; `Warhead@4Dam_areanuke1` targets Air, Ground, Underwater, Water | one or more payload delays are unspecified |
| `ReactorNuke` | `mods/cameo/ContentPacks/RedAlert2/Shared/yaml/weapons.yaml` | `requires_review` | `Warhead@1Dam_impact` vs `Warhead@4Dam_areanuke1` at 0/250 WDist: 1000:750 vs 1000:875; `Warhead@1Dam_impact` targets Air, Ground, Water; `Warhead@4Dam_areanuke1` targets Air, Ground, Underwater, Water | one or more payload delays are unspecified |
| `ReactorNukeWeak` | `mods/cameo/ContentPacks/RedAlert2/Shared/yaml/weapons.yaml` | `requires_review` | `Warhead@1Dam_impact` vs `Warhead@4Dam_areanuke1` at 0/250 WDist: 1000:750 vs 1000:875; `Warhead@1Dam_impact` targets Air, Ground, Water; `Warhead@4Dam_areanuke1` targets Air, Ground, Underwater, Water | one or more payload delays are unspecified |

## Ring evidence

### `CabalMagicNuke`

| warhead | Delay | Damage | Spread | derived outer radius | Falloff | ValidTargets |
|---|---:|---:|---:|---:|---|---|
| `Warhead@1Dam_impact` | 0 | 20000 | 1000 | 7000 | 1000, 500, 250, 125, 50, 25, 5, 0 | Ground, Water, Air |
| `Warhead@4Dam_areanuke1` | 3 | 17500 | 2000 | 12000 | 1000, 500, 250, 125, 50, 25, 0 | Ground, Water, Underwater, Air |
| `Warhead@7Dam_areanuke2` | 6 | 15000 | 3000 | 15000 | 1000, 500, 250, 125, 50, 0 | Ground, Water, Underwater, Air |
| `Warhead@8Dam_areanuke2` | 9 | 12500 | 4000 | 16000 | 1000, 500, 250, 125, 0 | Ground, Water, Underwater, Air |
| `Warhead@10Dam_areanuke3` | 12 | 10000 | 5000 | 15000 | 1000, 500, 250, 0 | Ground, Water, Underwater, Air |
| `Warhead@11Dam_areanuke3` | 15 | 7500 | 6000 | 12000 | 1000, 500, 0 | Ground, Water, Underwater, Air |

### `CrateNuke`

| warhead | Delay | Damage | Spread | derived outer radius | Falloff | ValidTargets |
|---|---:|---:|---:|---:|---|---|
| `Warhead@4Dam_areanuke1` | 5 | 6000 | 1024 | 6144 | 1000, 600, 400, 250, 150, 100, 0 | Ground, Water, Air |
| `Warhead@1Dam_impact` | unspecified | 10000 | 1024 | 6144 | 1000, 368, 135, 50, 18, 7, 0 | Ground, Water, Air |

### `ExecutionerDeath`

| warhead | Delay | Damage | Spread | derived outer radius | Falloff | ValidTargets |
|---|---:|---:|---:|---:|---|---|
| `Warhead@1Dam_impact` | 2 | 80000 | 500 | 3000 | 1000, 500, 250, 125, 50, 25, 5 | Ground, Water, Air |
| `Warhead@4Dam_areanuke1` | 4 | 40000 | 1000 | 5000 | 1000, 500, 250, 125, 50, 25 | Ground, Water, Underwater, Air |
| `Warhead@7Dam_areanuke2` | 6 | 20000 | 1500 | 6000 | 1000, 500, 250, 125, 50 | Ground, Water, Underwater, Air |
| `Warhead@8Dam_areanuke2` | 8 | 10000 | 2000 | 6000 | 1000, 500, 250, 125 | Ground, Water, Underwater, Air |
| `Warhead@10Dam_areanuke3` | 10 | 5000 | 2500 | 5000 | 1000, 500, 250 | Ground, Water, Underwater, Air |
| `Warhead@11Dam_areanuke3` | 12 | 2500 | 3000 | 3000 | 1000, 500 | Ground, Water, Underwater, Air |
| `Warhead@Damage` | unspecified | 160000 | 1600 | 6400 | 160, 80, 40, 20, 10 | Ground, Water, Air |

### `HermitExplode`

| warhead | Delay | Damage | Spread | derived outer radius | Falloff | ValidTargets |
|---|---:|---:|---:|---:|---|---|
| `Warhead@1Dam_impact` | 2 | 80000 | 500 | 3000 | 1000, 500, 250, 125, 50, 25, 5 | Ground, Water, Air |
| `Warhead@4Dam_areanuke1` | 4 | 40000 | 1000 | 5000 | 1000, 500, 250, 125, 50, 25 | Ground, Water, Underwater, Air |
| `Warhead@7Dam_areanuke2` | 6 | 20000 | 1500 | 6000 | 1000, 500, 250, 125, 50 | Ground, Water, Underwater, Air |
| `Warhead@8Dam_areanuke2` | 8 | 10000 | 2000 | 6000 | 1000, 500, 250, 125 | Ground, Water, Underwater, Air |
| `Warhead@10Dam_areanuke3` | 10 | 5000 | 2500 | 5000 | 1000, 500, 250 | Ground, Water, Underwater, Air |
| `Warhead@11Dam_areanuke3` | 12 | 2500 | 3000 | 3000 | 1000, 500 | Ground, Water, Underwater, Air |
| `Warhead@Damage` | unspecified | 160000 | 1600 | 6400 | 160, 80, 40, 20, 10 | Ground, Water, Air |

### `MiniNova`

| warhead | Delay | Damage | Spread | derived outer radius | Falloff | ValidTargets |
|---|---:|---:|---:|---:|---|---|
| `Warhead@1Dam_impact` | 2 | 80000 | 500 | 3000 | 1000, 500, 250, 125, 50, 25, 5 | Ground, Water, Air |
| `Warhead@4Dam_areanuke1` | 4 | 40000 | 1000 | 5000 | 1000, 500, 250, 125, 50, 25 | Ground, Water, Underwater, Air |
| `Warhead@7Dam_areanuke2` | 6 | 20000 | 1500 | 6000 | 1000, 500, 250, 125, 50 | Ground, Water, Underwater, Air |
| `Warhead@8Dam_areanuke2` | 8 | 10000 | 2000 | 6000 | 1000, 500, 250, 125 | Ground, Water, Underwater, Air |
| `Warhead@10Dam_areanuke3` | 10 | 5000 | 2500 | 5000 | 1000, 500, 250 | Ground, Water, Underwater, Air |
| `Warhead@11Dam_areanuke3` | 12 | 2500 | 3000 | 3000 | 1000, 500 | Ground, Water, Underwater, Air |
| `Warhead@Damage` | unspecified | 160000 | 1600 | 6400 | 160, 80, 40, 20, 10 | Ground, Water, Air |

### `MiniNuke`

| warhead | Delay | Damage | Spread | derived outer radius | Falloff | ValidTargets |
|---|---:|---:|---:|---:|---|---|
| `Warhead@1Dam_impact` | 2 | 80000 | 500 | 3000 | 1000, 500, 250, 125, 50, 25, 5 | Ground, Water, Air |
| `Warhead@4Dam_areanuke1` | 4 | 40000 | 1000 | 5000 | 1000, 500, 250, 125, 50, 25 | Ground, Water, Underwater, Air |
| `Warhead@7Dam_areanuke2` | 6 | 20000 | 1500 | 6000 | 1000, 500, 250, 125, 50 | Ground, Water, Underwater, Air |
| `Warhead@8Dam_areanuke2` | 8 | 10000 | 2000 | 6000 | 1000, 500, 250, 125 | Ground, Water, Underwater, Air |
| `Warhead@10Dam_areanuke3` | 10 | 5000 | 2500 | 5000 | 1000, 500, 250 | Ground, Water, Underwater, Air |
| `Warhead@11Dam_areanuke3` | 12 | 2500 | 3000 | 3000 | 1000, 500 | Ground, Water, Underwater, Air |
| `Warhead@Damage` | unspecified | 160000 | 1600 | 6400 | 160, 80, 40, 20, 10 | Ground, Water, Air |

### `PulseMissile`

| warhead | Delay | Damage | Spread | derived outer radius | Falloff | ValidTargets |
|---|---:|---:|---:|---:|---|---|
| `Warhead@1Dam_impact` | 0 | 20000 | 1000 | 7000 | 1000, 500, 250, 125, 50, 25, 5, 0 | Ground, Water, Air |
| `Warhead@4Dam_areanuke1` | 3 | 17500 | 2000 | 12000 | 1000, 500, 250, 125, 50, 25, 0 | Ground, Water, Underwater, Air |
| `Warhead@7Dam_areanuke2` | 6 | 15000 | 3000 | 15000 | 1000, 500, 250, 125, 50, 0 | Ground, Water, Underwater, Air |
| `Warhead@8Dam_areanuke2` | 9 | 12500 | 4000 | 16000 | 1000, 500, 250, 125, 0 | Ground, Water, Underwater, Air |
| `Warhead@10Dam_areanuke3` | 12 | 10000 | 5000 | 15000 | 1000, 500, 250, 0 | Ground, Water, Underwater, Air |
| `Warhead@11Dam_areanuke3` | 15 | 7500 | 6000 | 12000 | 1000, 500, 0 | Ground, Water, Underwater, Air |

### `RA2DemoBomb`

| warhead | Delay | Damage | Spread | derived outer radius | Falloff | ValidTargets |
|---|---:|---:|---:|---:|---|---|
| `Warhead@1Dam_impact` | 2 | 80000 | 500 | 3000 | 1000, 500, 250, 125, 50, 25, 5 | Ground, Water, Air |
| `Warhead@4Dam_areanuke1` | 4 | 40000 | 1000 | 5000 | 1000, 500, 250, 125, 50, 25 | Ground, Water, Underwater, Air |
| `Warhead@7Dam_areanuke2` | 6 | 20000 | 1500 | 6000 | 1000, 500, 250, 125, 50 | Ground, Water, Underwater, Air |
| `Warhead@8Dam_areanuke2` | 8 | 10000 | 2000 | 6000 | 1000, 500, 250, 125 | Ground, Water, Underwater, Air |
| `Warhead@10Dam_areanuke3` | 10 | 5000 | 2500 | 5000 | 1000, 500, 250 | Ground, Water, Underwater, Air |
| `Warhead@11Dam_areanuke3` | 12 | 2500 | 3000 | 3000 | 1000, 500 | Ground, Water, Underwater, Air |
| `Warhead@Damage` | unspecified | 160000 | 1600 | 6400 | 160, 80, 40, 20, 10 | Ground, Water, Air |

### `ReactorNuke`

| warhead | Delay | Damage | Spread | derived outer radius | Falloff | ValidTargets |
|---|---:|---:|---:|---:|---|---|
| `Warhead@1Dam_impact` | 2 | 80000 | 500 | 3000 | 1000, 500, 250, 125, 50, 25, 5 | Ground, Water, Air |
| `Warhead@4Dam_areanuke1` | 4 | 40000 | 1000 | 5000 | 1000, 500, 250, 125, 50, 25 | Ground, Water, Underwater, Air |
| `Warhead@7Dam_areanuke2` | 6 | 20000 | 1500 | 6000 | 1000, 500, 250, 125, 50 | Ground, Water, Underwater, Air |
| `Warhead@8Dam_areanuke2` | 8 | 10000 | 2000 | 6000 | 1000, 500, 250, 125 | Ground, Water, Underwater, Air |
| `Warhead@10Dam_areanuke3` | 10 | 5000 | 2500 | 5000 | 1000, 500, 250 | Ground, Water, Underwater, Air |
| `Warhead@11Dam_areanuke3` | 12 | 2500 | 3000 | 3000 | 1000, 500 | Ground, Water, Underwater, Air |
| `Warhead@Damage` | unspecified | 160000 | 1600 | 6400 | 160, 80, 40, 20, 10 | Ground, Water, Air |

### `ReactorNukeWeak`

| warhead | Delay | Damage | Spread | derived outer radius | Falloff | ValidTargets |
|---|---:|---:|---:|---:|---|---|
| `Warhead@1Dam_impact` | 2 | 80000 | 500 | 3000 | 1000, 500, 250, 125, 50, 25, 5 | Ground, Water, Air |
| `Warhead@4Dam_areanuke1` | 4 | 40000 | 1000 | 5000 | 1000, 500, 250, 125, 50, 25 | Ground, Water, Underwater, Air |
| `Warhead@7Dam_areanuke2` | 6 | 20000 | 1500 | 6000 | 1000, 500, 250, 125, 50 | Ground, Water, Underwater, Air |
| `Warhead@8Dam_areanuke2` | 8 | 10000 | 2000 | 6000 | 1000, 500, 250, 125 | Ground, Water, Underwater, Air |
| `Warhead@10Dam_areanuke3` | 10 | 5000 | 2500 | 5000 | 1000, 500, 250 | Ground, Water, Underwater, Air |
| `Warhead@11Dam_areanuke3` | 12 | 2500 | 3000 | 3000 | 1000, 500 | Ground, Water, Underwater, Air |
| `Warhead@Damage` | unspecified | 160000 | 1600 | 6400 | 160, 80, 40, 20, 10 | Ground, Water, Air |

## Decision boundary

R14 remains open. These measurements do not certify a conversion or prove impossibility. Any candidate must still compare resolved predicates, timing, integer damage and complete spatial behavior; an approximation or new per-tick semantics is a separate engine/design decision and needs its own gameplay review.
