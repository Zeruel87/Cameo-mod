# Explicit four-voice pilot gate

**Review-only.** The manifest supplies every record index and group key.
DTA base-channel admission is explicit and raw status remains visible.
No source join, normalization writeback or gameplay value is produced.

## Summary

- Groups: **29**; assembly resolved: **0**; channel aggregation resolved: **29**; gate resolved: **0**; gate unresolved: **29**.
- Permanent Current Cameo self-vote binding: **UNRESOLVED** (original_channel_reconstruction_not_verified).
- Archived actor-stat inputs verified: **71/71**. This does not certify original per-armor channels.
- Scenario policies:
  - **aircraft** (`AEDIS_AIRCRAFT_LIGHT_HEAVY_LADDER`): Light maps to Fighter and Heavy maps to Spaceship; Bomber and Helicopter are equal linear steps between them.
  - **infantry** (`AEDIS_INFANTRY_NONE_LIGHT_TO_NONE_FLAK_PLATE`): None direct; Light maps to Plate; Flak is the equal midpoint between None and Light.
  - **vehicle** (`AEDIS_VEHICLE_LIGHT_HEAVY_LADDER`): Light and Heavy direct; Medium is the equal midpoint; Scout is one equal step below Light; Superheavy is one equal step above Heavy.
- Voice policy: one Current Cameo row plus exactly three distinct reference voices at equal 0.25 weight.

| comparison | status | voices | reasons |
|---|---|---|---|
| ra1/allies/alliedgunturret/vehicle/base | UNRESOLVED | — | current_cameo_self_vote_unbound:original_channel_reconstruction_not_verified |
| ra1/allies/gunboat/vehicle/base | UNRESOLVED | — | current_cameo_self_vote_unbound:original_channel_reconstruction_not_verified |
| ra1/allies/alliedmediumtank/vehicle/base | UNRESOLVED | — | current_cameo_self_vote_unbound:original_channel_reconstruction_not_verified |
| ra1/soviets/heavytank/vehicle/base | UNRESOLVED | — | current_cameo_self_vote_unbound:original_channel_reconstruction_not_verified |
| ra1/soviets/mammothtank/vehicle/base | UNRESOLVED | — | current_cameo_self_vote_unbound:original_channel_reconstruction_not_verified |
| ra1/soviets/teslacoil/vehicle/base | UNRESOLVED | — | current_cameo_self_vote_unbound:original_channel_reconstruction_not_verified |
| td/gdi/battletank/vehicle/base | UNRESOLVED | — | current_cameo_self_vote_unbound:original_channel_reconstruction_not_verified |
| td/gdi/mammothtank/vehicle/base | UNRESOLVED | — | current_cameo_self_vote_unbound:original_channel_reconstruction_not_verified |
| td/gdi/orca/vehicle/base | UNRESOLVED | — | current_cameo_self_vote_unbound:original_channel_reconstruction_not_verified |
| td/nod/lighttank/vehicle/base | UNRESOLVED | — | current_cameo_self_vote_unbound:original_channel_reconstruction_not_verified |
| td/nod/obeliskoflight/vehicle/base | UNRESOLVED | — | current_cameo_self_vote_unbound:original_channel_reconstruction_not_verified |
| td/nod/stealthtank/vehicle/base | UNRESOLVED | — | current_cameo_self_vote_unbound:original_channel_reconstruction_not_verified |
| ra1/allies/rifleinfantry/infantry/base | UNRESOLVED | — | current_cameo_self_vote_unbound:original_channel_reconstruction_not_verified |
| ra1/allies/ranger/infantry/base | UNRESOLVED | — | current_cameo_self_vote_unbound:original_channel_reconstruction_not_verified |
| ra1/soviets/rifleinfantry/infantry/base | UNRESOLVED | — | current_cameo_self_vote_unbound:original_channel_reconstruction_not_verified |
| ra1/soviets/grenadier/infantry/base | UNRESOLVED | — | current_cameo_self_vote_unbound:original_channel_reconstruction_not_verified |
| ra1/soviets/shocktrooper/infantry/base | UNRESOLVED | — | current_cameo_self_vote_unbound:original_channel_reconstruction_not_verified |
| td/gdi/minigunner/infantry/base | UNRESOLVED | — | current_cameo_self_vote_unbound:original_channel_reconstruction_not_verified |
| td/gdi/grenadier/infantry/base | UNRESOLVED | — | current_cameo_self_vote_unbound:original_channel_reconstruction_not_verified |
| td/nod/minigunner/infantry/base | UNRESOLVED | — | current_cameo_self_vote_unbound:original_channel_reconstruction_not_verified |
| td/nod/chemicalwarrior/infantry/base | UNRESOLVED | — | current_cameo_self_vote_unbound:original_channel_reconstruction_not_verified |
| ra1/allies/alliedaagun/aircraft/base | UNRESOLVED | — | current_cameo_self_vote_unbound:original_channel_reconstruction_not_verified |
| ra1/allies/alliedrocketsoldier/aircraft/base | UNRESOLVED | — | current_cameo_self_vote_unbound:original_channel_reconstruction_not_verified |
| ra1/allies/longbow/aircraft/base | UNRESOLVED | — | current_cameo_self_vote_unbound:original_channel_reconstruction_not_verified |
| ra1/soviets/rocketsoldier/aircraft/base | UNRESOLVED | — | current_cameo_self_vote_unbound:original_channel_reconstruction_not_verified |
| ra1/soviets/samsite/aircraft/base | UNRESOLVED | — | current_cameo_self_vote_unbound:original_channel_reconstruction_not_verified |
| td/gdi/rocketsoldier/aircraft/base | UNRESOLVED | — | current_cameo_self_vote_unbound:original_channel_reconstruction_not_verified |
| td/nod/rocketsoldier/aircraft/base | UNRESOLVED | — | current_cameo_self_vote_unbound:original_channel_reconstruction_not_verified |
| td/nod/samsite/aircraft/base | UNRESOLVED | — | current_cameo_self_vote_unbound:original_channel_reconstruction_not_verified |

## Candidate roster disposition

- Actor rows accounted: **163/163**; explicit manifest groups: **29** across **29** actors.
- Explicit N/A dispositions: **0**. Missing channels or scenarios remain unresolved rather than inferred as N/A.

| actor | disposition | explicit groups | current channels | reference voices |
|---|---|---|---:|---:|
| `ra1_allies_alliedaagun` | EXPLICIT_GROUPS_SELF_VOTE_UNBOUND | ra1/allies/alliedaagun/aircraft/base | 2 | 3 |
| `ra1_allies_alliedapc` | THREE_REFERENCE_CANDIDATE_NEEDS_EXPLICIT_GROUP | — | 2 | 3 |
| `ra1_allies_alliedartillery` | THREE_REFERENCE_CANDIDATE_NEEDS_EXPLICIT_GROUP | — | 2 | 3 |
| `ra1_allies_alliedchinooktransport` | UNRESOLVED_CURRENT_CAMEO_HP_CHANNEL | — | 0 | 2 |
| `ra1_allies_alliedgunturret` | EXPLICIT_GROUPS_SELF_VOTE_UNBOUND | ra1/allies/alliedgunturret/vehicle/base | 1 | 3 |
| `ra1_allies_alliedheavyaatank` | UNRESOLVED_REFERENCE_COVERAGE | — | 2 | 1 |
| `ra1_allies_alliedlighttank` | THREE_REFERENCE_CANDIDATE_NEEDS_EXPLICIT_GROUP | — | 1 | 3 |
| `ra1_allies_alliedmediumtank` | EXPLICIT_GROUPS_SELF_VOTE_UNBOUND | ra1/allies/alliedmediumtank/vehicle/base | 2 | 3 |
| `ra1_allies_alliedmobileconstructionvehicle` | UNRESOLVED_CURRENT_CAMEO_HP_CHANNEL | — | 0 | 2 |
| `ra1_allies_alliedoretruck` | UNRESOLVED_CURRENT_CAMEO_HP_CHANNEL | — | 0 | 2 |
| `ra1_allies_alliedrocketsoldier` | EXPLICIT_GROUPS_SELF_VOTE_UNBOUND | ra1/allies/alliedrocketsoldier/aircraft/base | 4 | 3 |
| `ra1_allies_alliedsniper` | UNRESOLVED_REFERENCE_COVERAGE | — | 4 | 1 |
| `ra1_allies_alliedtankdestroyer` | UNRESOLVED_REFERENCE_COVERAGE | — | 2 | 2 |
| `ra1_allies_alliedtigerheavytank` | UNRESOLVED_REFERENCE_COVERAGE | — | 2 | 1 |
| `ra1_allies_bastionartillerybunker` | UNRESOLVED_REFERENCE_COVERAGE | — | 2 | 1 |
| `ra1_allies_blackhawk` | UNRESOLVED_REFERENCE_COVERAGE | — | 4 | 1 |
| `ra1_allies_camopillbox` | UNRESOLVED_CURRENT_CAMEO_HP_CHANNEL | — | 0 | 3 |
| `ra1_allies_chronotank` | UNRESOLVED_REFERENCE_COVERAGE | — | 4 | 0 |
| `ra1_allies_cruiser` | THREE_REFERENCE_CANDIDATE_NEEDS_EXPLICIT_GROUP | — | 4 | 3 |
| `ra1_allies_destroyer` | THREE_REFERENCE_CANDIDATE_NEEDS_EXPLICIT_GROUP | — | 6 | 3 |
| `ra1_allies_gapgenerator` | UNRESOLVED_CURRENT_CAMEO_HP_CHANNEL | — | 0 | 0 |
| `ra1_allies_gunboat` | EXPLICIT_GROUPS_SELF_VOTE_UNBOUND | ra1/allies/gunboat/vehicle/base | 4 | 3 |
| `ra1_allies_longbow` | EXPLICIT_GROUPS_SELF_VOTE_UNBOUND | ra1/allies/longbow/aircraft/base | 2 | 3 |
| `ra1_allies_machinegunner` | UNRESOLVED_REFERENCE_COVERAGE | — | 4 | 1 |
| `ra1_allies_mechanic` | THREE_REFERENCE_CANDIDATE_NEEDS_EXPLICIT_GROUP | — | 3 | 3 |
| `ra1_allies_medic` | THREE_REFERENCE_CANDIDATE_NEEDS_EXPLICIT_GROUP | — | 3 | 3 |
| `ra1_allies_minelayer` | UNRESOLVED_CURRENT_CAMEO_HP_CHANNEL | — | 0 | 0 |
| `ra1_allies_mobilegapgenerator` | UNRESOLVED_REFERENCE_COVERAGE | — | 1 | 0 |
| `ra1_allies_mobileradarjammer` | UNRESOLVED_REFERENCE_COVERAGE | — | 1 | 0 |
| `ra1_allies_phasetransport` | UNRESOLVED_REFERENCE_COVERAGE | — | 2 | 0 |
| `ra1_allies_pillbox` | UNRESOLVED_CURRENT_CAMEO_HP_CHANNEL | — | 0 | 3 |
| `ra1_allies_ranger` | EXPLICIT_GROUPS_SELF_VOTE_UNBOUND | ra1/allies/ranger/infantry/base | 2 | 3 |
| `ra1_allies_rapierjumpjet` | UNRESOLVED_REFERENCE_COVERAGE | — | 4 | 1 |
| `ra1_allies_raspy` | THREE_REFERENCE_CANDIDATE_NEEDS_EXPLICIT_GROUP | — | 1 | 3 |
| `ra1_allies_reconranger` | UNRESOLVED_REFERENCE_COVERAGE | — | 2 | 1 |
| `ra1_allies_rifleinfantry` | EXPLICIT_GROUPS_SELF_VOTE_UNBOUND | ra1/allies/rifleinfantry/infantry/base | 4 | 3 |
| `ra1_allies_sheridanassaulttank` | UNRESOLVED_REFERENCE_COVERAGE | — | 6 | 1 |
| `ra1_allies_tanya` | THREE_REFERENCE_CANDIDATE_NEEDS_EXPLICIT_GROUP | — | 6 | 3 |
| `ra1_soviets_ak47conscript` | UNRESOLVED_REFERENCE_COVERAGE | — | 2 | 0 |
| `ra1_soviets_armoredyak` | UNRESOLVED_REFERENCE_COVERAGE | — | 4 | 0 |
| `ra1_soviets_btr80` | UNRESOLVED_REFERENCE_COVERAGE | — | 6 | 1 |
| `ra1_soviets_commissar` | UNRESOLVED_REFERENCE_COVERAGE | — | 2 | 1 |
| `ra1_soviets_cyberdog` | UNRESOLVED_REFERENCE_COVERAGE | — | 1 | 0 |
| `ra1_soviets_dog` | THREE_REFERENCE_CANDIDATE_NEEDS_EXPLICIT_GROUP | — | 1 | 3 |
| `ra1_soviets_dragunovantimaterialsniper` | UNRESOLVED_REFERENCE_COVERAGE | — | 2 | 0 |
| `ra1_soviets_firerocketsoldier` | UNRESOLVED_REFERENCE_COVERAGE | — | 4 | 0 |
| `ra1_soviets_flaktruck` | UNRESOLVED_REFERENCE_COVERAGE | — | 2 | 0 |
| `ra1_soviets_flamethrower` | UNRESOLVED_REFERENCE_COVERAGE | — | 4 | 2 |
| `ra1_soviets_flametower` | THREE_REFERENCE_CANDIDATE_NEEDS_EXPLICIT_GROUP | — | 2 | 3 |
| `ra1_soviets_gatlingtank` | UNRESOLVED_REFERENCE_COVERAGE | — | 8 | 1 |
| `ra1_soviets_gorynychtank` | UNRESOLVED_REFERENCE_COVERAGE | — | 1 | 1 |
| `ra1_soviets_grad` | UNRESOLVED_REFERENCE_COVERAGE | — | 2 | 1 |
| `ra1_soviets_grenadier` | EXPLICIT_GROUPS_SELF_VOTE_UNBOUND | ra1/soviets/grenadier/infantry/base | 4 | 3 |
| `ra1_soviets_hammertank` | UNRESOLVED_REFERENCE_COVERAGE | — | 3 | 1 |
| `ra1_soviets_heatraytank` | UNRESOLVED_REFERENCE_COVERAGE | — | 4 | 1 |
| `ra1_soviets_heavyindustrialminer` | UNRESOLVED_CURRENT_CAMEO_HP_CHANNEL | — | 0 | 0 |
| `ra1_soviets_heavytank` | EXPLICIT_GROUPS_SELF_VOTE_UNBOUND | ra1/soviets/heavytank/vehicle/base | 2 | 3 |
| `ra1_soviets_heavyteslatank` | UNRESOLVED_REFERENCE_COVERAGE | — | 3 | 1 |
| `ra1_soviets_hindattackhelicopter` | UNRESOLVED_REFERENCE_COVERAGE | — | 13 | 1 |
| `ra1_soviets_hiptransport` | UNRESOLVED_CURRENT_CAMEO_HP_CHANNEL | — | 0 | 2 |
| `ra1_soviets_kamovattackhelicopter` | UNRESOLVED_REFERENCE_COVERAGE | — | 12 | 1 |
| `ra1_soviets_kotinnucleartank` | UNRESOLVED_REFERENCE_COVERAGE | — | 2 | 1 |
| `ra1_soviets_madtank` | UNRESOLVED_REFERENCE_COVERAGE | — | 1 | 1 |
| `ra1_soviets_mammothtank` | EXPLICIT_GROUPS_SELF_VOTE_UNBOUND | ra1/soviets/mammothtank/vehicle/base | 10 | 3 |
| `ra1_soviets_migattackbomber` | THREE_REFERENCE_CANDIDATE_NEEDS_EXPLICIT_GROUP | — | 6 | 3 |
| `ra1_soviets_missilesubmarine` | THREE_REFERENCE_CANDIDATE_NEEDS_EXPLICIT_GROUP | — | 1 | 3 |
| `ra1_soviets_mobileconstructionvehicle` | UNRESOLVED_CURRENT_CAMEO_HP_CHANNEL | — | 0 | 2 |
| `ra1_soviets_monstertank` | UNRESOLVED_REFERENCE_COVERAGE | — | 5 | 1 |
| `ra1_soviets_mortarsoldier` | UNRESOLVED_REFERENCE_COVERAGE | — | 4 | 1 |
| `ra1_soviets_nuclearv2launcher` | UNRESOLVED_REFERENCE_COVERAGE | — | 2 | 1 |
| `ra1_soviets_nuclearyak` | UNRESOLVED_REFERENCE_COVERAGE | — | 5 | 0 |
| `ra1_soviets_nukedemotruck` | UNRESOLVED_REFERENCE_COVERAGE | — | 1 | 2 |
| `ra1_soviets_oretruck` | UNRESOLVED_CURRENT_CAMEO_HP_CHANNEL | — | 0 | 2 |
| `ra1_soviets_rifleinfantry` | EXPLICIT_GROUPS_SELF_VOTE_UNBOUND | ra1/soviets/rifleinfantry/infantry/base | 4 | 3 |
| `ra1_soviets_rocketsoldier` | EXPLICIT_GROUPS_SELF_VOTE_UNBOUND | ra1/soviets/rocketsoldier/aircraft/base | 2 | 3 |
| `ra1_soviets_samsite` | EXPLICIT_GROUPS_SELF_VOTE_UNBOUND | ra1/soviets/samsite/aircraft/base | 1 | 3 |
| `ra1_soviets_shocktrooper` | EXPLICIT_GROUPS_SELF_VOTE_UNBOUND | ra1/soviets/shocktrooper/infantry/base | 6 | 3 |
| `ra1_soviets_siegemammothtank` | UNRESOLVED_REFERENCE_COVERAGE | — | 8 | 1 |
| `ra1_soviets_stalinfist` | UNRESOLVED_CURRENT_CAMEO_HP_CHANNEL | — | 0 | 0 |
| `ra1_soviets_su57attackbomber` | UNRESOLVED_REFERENCE_COVERAGE | — | 6 | 1 |
| `ra1_soviets_submarine` | THREE_REFERENCE_CANDIDATE_NEEDS_EXPLICIT_GROUP | — | 2 | 3 |
| `ra1_soviets_supersonicnuclearbomber` | UNRESOLVED_REFERENCE_COVERAGE | — | 1 | 0 |
| `ra1_soviets_teslacoil` | EXPLICIT_GROUPS_SELF_VOTE_UNBOUND | ra1/soviets/teslacoil/vehicle/base | 3 | 3 |
| `ra1_soviets_teslatank` | UNRESOLVED_REFERENCE_COVERAGE | — | 3 | 2 |
| `ra1_soviets_teslayak` | UNRESOLVED_REFERENCE_COVERAGE | — | 7 | 0 |
| `ra1_soviets_v1rockettruck` | UNRESOLVED_REFERENCE_COVERAGE | — | 2 | 1 |
| `ra1_soviets_v2rocketlauncher` | THREE_REFERENCE_CANDIDATE_NEEDS_EXPLICIT_GROUP | — | 3 | 3 |
| `ra1_soviets_volkov` | UNRESOLVED_REFERENCE_COVERAGE | — | 12 | 1 |
| `ra1_soviets_yakscoutplane` | THREE_REFERENCE_CANDIDATE_NEEDS_EXPLICIT_GROUP | — | 5 | 3 |
| `ra1_soviets_zapper` | UNRESOLVED_REFERENCE_COVERAGE | — | 4 | 1 |
| `td_gdi_advancedguardtower` | THREE_REFERENCE_CANDIDATE_NEEDS_EXPLICIT_GROUP | — | 2 | 3 |
| `td_gdi_apc` | THREE_REFERENCE_CANDIDATE_NEEDS_EXPLICIT_GROUP | — | 2 | 3 |
| `td_gdi_archerartillery` | UNRESOLVED_REFERENCE_COVERAGE | — | 1 | 2 |
| `td_gdi_assaultapc` | UNRESOLVED_REFERENCE_COVERAGE | — | 4 | 0 |
| `td_gdi_battletank` | EXPLICIT_GROUPS_SELF_VOTE_UNBOUND | td/gdi/battletank/vehicle/base | 5 | 3 |
| `td_gdi_boxer` | UNRESOLVED_REFERENCE_COVERAGE | — | 2 | 1 |
| `td_gdi_chinooktransport` | UNRESOLVED_CURRENT_CAMEO_HP_CHANNEL | — | 0 | 3 |
| `td_gdi_commando` | THREE_REFERENCE_CANDIDATE_NEEDS_EXPLICIT_GROUP | — | 6 | 3 |
| `td_gdi_defenserig` | UNRESOLVED_REFERENCE_COVERAGE | — | 9 | 0 |
| `td_gdi_empgrenadier` | UNRESOLVED_REFERENCE_COVERAGE | — | 2 | 2 |
| `td_gdi_exosuit` | UNRESOLVED_REFERENCE_COVERAGE | — | 1 | 2 |
| `td_gdi_firehawk` | UNRESOLVED_REFERENCE_COVERAGE | — | 3 | 2 |
| `td_gdi_grenadier` | EXPLICIT_GROUPS_SELF_VOTE_UNBOUND | td/gdi/grenadier/infantry/base | 2 | 3 |
| `td_gdi_guardtower` | THREE_REFERENCE_CANDIDATE_NEEDS_EXPLICIT_GROUP | — | 2 | 3 |
| `td_gdi_havoc` | UNRESOLVED_REFERENCE_COVERAGE | — | 9 | 0 |
| `td_gdi_heavysniper` | UNRESOLVED_REFERENCE_COVERAGE | — | 2 | 1 |
| `td_gdi_humvee` | THREE_REFERENCE_CANDIDATE_NEEDS_EXPLICIT_GROUP | — | 2 | 3 |
| `td_gdi_humveemkii` | UNRESOLVED_REFERENCE_COVERAGE | — | 8 | 1 |
| `td_gdi_landingcraft` | UNRESOLVED_CURRENT_CAMEO_HP_CHANNEL | — | 0 | 0 |
| `td_gdi_mammothtank` | EXPLICIT_GROUPS_SELF_VOTE_UNBOUND | td/gdi/mammothtank/vehicle/base | 4 | 3 |
| `td_gdi_mammothtankmkiii` | UNRESOLVED_REFERENCE_COVERAGE | — | 4 | 1 |
| `td_gdi_minigunner` | EXPLICIT_GROUPS_SELF_VOTE_UNBOUND | td/gdi/minigunner/infantry/base | 4 | 3 |
| `td_gdi_missileboat` | UNRESOLVED_REFERENCE_COVERAGE | — | 4 | 1 |
| `td_gdi_mlrs` | THREE_REFERENCE_CANDIDATE_NEEDS_EXPLICIT_GROUP | — | 2 | 3 |
| `td_gdi_mobileconstructionvehicle` | UNRESOLVED_CURRENT_CAMEO_HP_CHANNEL | — | 0 | 3 |
| `td_gdi_officer` | UNRESOLVED_REFERENCE_COVERAGE | — | 4 | 0 |
| `td_gdi_orca` | EXPLICIT_GROUPS_SELF_VOTE_UNBOUND | td/gdi/orca/vehicle/base | 2 | 3 |
| `td_gdi_predatortank` | UNRESOLVED_REFERENCE_COVERAGE | — | 6 | 1 |
| `td_gdi_railgunbattleship` | UNRESOLVED_REFERENCE_COVERAGE | — | 2 | 0 |
| `td_gdi_rocketsoldier` | EXPLICIT_GROUPS_SELF_VOTE_UNBOUND | td/gdi/rocketsoldier/aircraft/base | 4 | 3 |
| `td_gdi_shotgunner` | UNRESOLVED_REFERENCE_COVERAGE | — | 2 | 0 |
| `td_gdi_skyshield` | UNRESOLVED_REFERENCE_COVERAGE | — | 1 | 1 |
| `td_gdi_sonicmissilesoldier` | UNRESOLVED_REFERENCE_COVERAGE | — | 2 | 0 |
| `td_gdi_supercarrier` | UNRESOLVED_REFERENCE_COVERAGE | — | 1 | 2 |
| `td_gdi_tiberiumharvester` | UNRESOLVED_CURRENT_CAMEO_HP_CHANNEL | — | 0 | 3 |
| `td_nod_apacheattackhelicopter` | THREE_REFERENCE_CANDIDATE_NEEDS_EXPLICIT_GROUP | — | 2 | 3 |
| `td_nod_artillery` | THREE_REFERENCE_CANDIDATE_NEEDS_EXPLICIT_GROUP | — | 2 | 3 |
| `td_nod_attacksubmarine` | UNRESOLVED_REFERENCE_COVERAGE | — | 2 | 1 |
| `td_nod_ballisticmissilesubmarine` | UNRESOLVED_REFERENCE_COVERAGE | — | 1 | 1 |
| `td_nod_blackhandflamer` | UNRESOLVED_REFERENCE_COVERAGE | — | 2 | 1 |
| `td_nod_buggy` | THREE_REFERENCE_CANDIDATE_NEEDS_EXPLICIT_GROUP | — | 2 | 3 |
| `td_nod_buggymkii` | UNRESOLVED_REFERENCE_COVERAGE | — | 9 | 1 |
| `td_nod_chemicalattackbike` | UNRESOLVED_REFERENCE_COVERAGE | — | 2 | 0 |
| `td_nod_chemicalrocketsoldier` | UNRESOLVED_REFERENCE_COVERAGE | — | 2 | 1 |
| `td_nod_chemicalssmlauncher` | UNRESOLVED_REFERENCE_COVERAGE | — | 1 | 0 |
| `td_nod_chemicalstealthtank` | UNRESOLVED_REFERENCE_COVERAGE | — | 1 | 1 |
| `td_nod_chemicalwarrior` | EXPLICIT_GROUPS_SELF_VOTE_UNBOUND | td/nod/chemicalwarrior/infantry/base | 2 | 3 |
| `td_nod_chinooktransport` | UNRESOLVED_CURRENT_CAMEO_HP_CHANNEL | — | 0 | 3 |
| `td_nod_commando` | THREE_REFERENCE_CANDIDATE_NEEDS_EXPLICIT_GROUP | — | 4 | 3 |
| `td_nod_flametank` | THREE_REFERENCE_CANDIDATE_NEEDS_EXPLICIT_GROUP | — | 1 | 3 |
| `td_nod_flametankmkii` | UNRESOLVED_REFERENCE_COVERAGE | — | 1 | 0 |
| `td_nod_flamethrower` | THREE_REFERENCE_CANDIDATE_NEEDS_EXPLICIT_GROUP | — | 2 | 3 |
| `td_nod_gunturret` | THREE_REFERENCE_CANDIDATE_NEEDS_EXPLICIT_GROUP | — | 2 | 3 |
| `td_nod_lasercommando` | UNRESOLVED_REFERENCE_COVERAGE | — | 4 | 0 |
| `td_nod_lasercorvette` | UNRESOLVED_REFERENCE_COVERAGE | — | 2 | 1 |
| `td_nod_lasertrooper` | UNRESOLVED_REFERENCE_COVERAGE | — | 2 | 1 |
| `td_nod_laserturret` | UNRESOLVED_REFERENCE_COVERAGE | — | 3 | 1 |
| `td_nod_lighttank` | EXPLICIT_GROUPS_SELF_VOTE_UNBOUND | td/nod/lighttank/vehicle/base | 2 | 3 |
| `td_nod_lighttankmkii` | UNRESOLVED_REFERENCE_COVERAGE | — | 3 | 1 |
| `td_nod_minigunner` | EXPLICIT_GROUPS_SELF_VOTE_UNBOUND | td/nod/minigunner/infantry/base | 4 | 3 |
| `td_nod_mobileconstructionvehicle` | UNRESOLVED_CURRENT_CAMEO_HP_CHANNEL | — | 0 | 3 |
| `td_nod_obeliskoflight` | EXPLICIT_GROUPS_SELF_VOTE_UNBOUND | td/nod/obeliskoflight/vehicle/base | 3 | 3 |
| `td_nod_reconbike` | THREE_REFERENCE_CANDIDATE_NEEDS_EXPLICIT_GROUP | — | 2 | 3 |
| `td_nod_rocketsoldier` | EXPLICIT_GROUPS_SELF_VOTE_UNBOUND | td/nod/rocketsoldier/aircraft/base | 2 | 3 |
| `td_nod_samsite` | EXPLICIT_GROUPS_SELF_VOTE_UNBOUND | td/nod/samsite/aircraft/base | 1 | 3 |
| `td_nod_specterartillery` | UNRESOLVED_REFERENCE_COVERAGE | — | 2 | 0 |
| `td_nod_ssmlauncher` | THREE_REFERENCE_CANDIDATE_NEEDS_EXPLICIT_GROUP | — | 1 | 3 |
| `td_nod_stealthharvester` | UNRESOLVED_CURRENT_CAMEO_HP_CHANNEL | — | 0 | 1 |
| `td_nod_stealthsoldier` | UNRESOLVED_REFERENCE_COVERAGE | — | 2 | 0 |
| `td_nod_stealthtank` | EXPLICIT_GROUPS_SELF_VOTE_UNBOUND | td/nod/stealthtank/vehicle/base | 2 | 3 |
| `td_nod_tiberiumharvester` | UNRESOLVED_CURRENT_CAMEO_HP_CHANNEL | — | 0 | 3 |
| `td_nod_transportsubmarine` | UNRESOLVED_CURRENT_CAMEO_HP_CHANNEL | — | 0 | 0 |
| `td_nod_venom` | UNRESOLVED_REFERENCE_COVERAGE | — | 3 | 1 |

Resolved means are diagnostic only; target eligibility, cadence, secondary payloads, runtime applicability and gameplay review remain separate.
