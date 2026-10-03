# Promotion replacement superiority audit

**REVIEW ONLY.** Replacement pairs are taken from authored negative promotion prerequisites and explicit shared-token dispositions. This receipt does not remove `^PromotionUnitBuff`, edit costs or YAML, apply a global strict-superiority rule, or certify gameplay balance.

## Scope

- Promotion tokens: **48**; tokens with an explicit base-disable marker: **23**.
- Promotion consumers: **47**; explicit replacement pairs evaluated: **23**; additional shared-token options excluded from pair comparisons: **3**.
- Promotion consumers without a base-disable marker: **21**. These remain mapping/design questions.
- HP, speed, armor and cost use the resolved active ruleset. Weapon identity, range, nominal DPS and class labels come from one selected factory-state offensive record in the hashed balance ledger. Point defense and utility slots are excluded; ledger armaments are hash-disclosed rather than independently reconstructed here.

## Replacement pairs

| faction | base → promotion | selected weapons | HP | speed | range | nominal DPS | armor | warhead labels | status | findings |
|---|---|---|---|---|---|---|---|---|---|---|
| `ra1_allies` | `ra1_allies_pillbox` → `ra1_allies_camopillbox` | `—` → `—` | UP (90000→122500) | NOT_APPLICABLE (—→—) | NOT_APPLICABLE (—→—) | NOT_APPLICABLE (—→—) | SAME (Concrete→Concrete) | NOT_APPLICABLE | MEASURED_NO_LISTED_DIFFERENCE | — |
| `ra1_allies` | `ra1_allies_alliedapc` → `ra1_allies_phasetransport` | `ra1_allies_alliedapc_gun` → `ra1_allies_phasetransport_missile` | DOWN (50000→30000) | UP (105→125) | DOWN (5978→5038) | UP (400→1067) | DOWN (Medium→Light) | DIFFERENT_LABELS | STATIC_DIFFERENCES | ARMOR_WEAKER; HP_LOWER; RANGE_LOWER; WARHEAD_LABELS_DIFFER |
| `ra1_allies` | `ra1_allies_alliedlighttank` → `ra1_allies_sheridanassaulttank` | `ra1_allies_alliedlighttank_25mm` → `ra1_allies_sheridanassaulttank_cannon` | UP (50000→85000) | DOWN (120→85) | UP (4720→5023) | DOWN (162→62) | SAME (Medium→Medium) | DIFFERENT_LABELS | STATIC_DIFFERENCES | DPS_LOWER; SPEED_LOWER; WARHEAD_LABELS_DIFFER |
| `ra1_allies` | `ra1_allies_alliedmediumtank` → `ra1_allies_alliedtigerheavytank` | `ra1_allies_alliedmediumtank_cannon` → `ra1_allies_alliedtigerheavytank_cannon` | UP (90000→160000) | DOWN (100→75) | UP (5159→5915) | UP (170→267) | SAME (Heavy→Heavy) | DIFFERENT_LABELS | STATIC_DIFFERENCES | SPEED_LOWER; WARHEAD_LABELS_DIFFER |
| `ra1_soviets` | `ra1_soviets_dog` → `ra1_soviets_cyberdog` | `ra1_soviets_dog_bite` → `ra1_soviets_cyberdog_bite` | UP (5000→50000) | SAME (100→100) | UP (2000→2500) | UNRESOLVED (—→—) | UP (None→Plate) | SAME_LABELS | UNRESOLVED | UNRESOLVED_DPS |
| `td_gdi` | `td_gdi_apc` → `td_gdi_assaultapc` | `td_gdi_apc_apcgun` → `td_gdi_assaultapc_machinegunhumvee2` | UP (47500→250000) | SAME (100→100) | DOWN (5668→5598) | DOWN (400→190) | UP (Medium→Superheavy) | DIFFERENT_LABELS | STATIC_DIFFERENCES | DPS_LOWER; RANGE_LOWER; WARHEAD_LABELS_DIFFER |
| `td_gdi` | `td_gdi_grenadier` → `td_gdi_empgrenadier` | `td_gdi_grenadier_grenade` → `td_gdi_empgrenadier_grenade_emp` | UP (8000→32000) | DOWN (75→60) | DOWN (6097→5694) | UP (381→649) | SAME (None→None) | DIFFERENT_LABELS | STATIC_DIFFERENCES | RANGE_LOWER; SPEED_LOWER; WARHEAD_LABELS_DIFFER |
| `td_gdi` | `td_gdi_commando` → `td_gdi_havoc` | `td_gdi_commando_sniper` → `td_gdi_havoc_sniper` | UP (80000→100000) | UP (65→75) | DOWN (8086→7750) | DOWN (1600→400) | SAME (Heroic→Heroic) | DIFFERENT_LABELS | STATIC_DIFFERENCES | DPS_LOWER; RANGE_LOWER; WARHEAD_LABELS_DIFFER |
| `td_gdi` | `td_gdi_humvee` → `td_gdi_humveemkii` | `td_gdi_humvee_machinegun` → `td_gdi_humveemkii_machinegunhumvee2` | UP (27500→37500) | DOWN (150→115) | UP (4792→5598) | DOWN (857→95) | SAME (Scout→Scout) | SAME_LABELS | STATIC_DIFFERENCES | DPS_LOWER; SPEED_LOWER |
| `td_gdi` | `td_gdi_mammothtank` → `td_gdi_mammothtankmkiii` | `td_gdi_mammothtank_120mmdual` → `td_gdi_mammothtankmkiii_mammothtank3cannons` | UP (225000→500000) | DOWN (60→55) | UP (6141→6340) | UP (200→218) | SAME (Superheavy→Superheavy) | SAME_LABELS | STATIC_DIFFERENCES | SPEED_LOWER |
| `td_gdi` | `td_gdi_rocketsoldier` → `td_gdi_sonicmissilesoldier` | `td_gdi_rocketsoldier_rockets` → `td_gdi_sonicmissilesoldier_missilesoldierweapon` | UP (9000→25000) | SAME (50→50) | UP (6368→7500) | UP (286→408) | UP (Flak→Plate) | DIFFERENT_LABELS | STATIC_DIFFERENCES | WARHEAD_LABELS_DIFFER |
| `td_gdi` | `td_gdi_battletank` → `td_gdi_predatortank` | `td_gdi_battletank_120mm` → `td_gdi_predatortank_gdipredatortankcannon` | UP (125000→170000) | DOWN (80→70) | UP (5438→5880) | UP (111→114) | SAME (Heavy→Heavy) | SAME_LABELS | STATIC_DIFFERENCES | SPEED_LOWER |
| `td_nod` | `td_nod_flamethrower` → `td_nod_blackhandflamer` | `td_nod_flamethrower_flamethrower` → `td_nod_blackhandflamer_blackhandflamer` | UP (20000→36000) | UP (60→66) | UP (2085→4988) | UP (333→364) | SAME (Plate→Plate) | DIFFERENT_LABELS | STATIC_DIFFERENCES | WARHEAD_LABELS_DIFFER |
| `td_nod` | `td_nod_buggy` → `td_nod_buggymkii` | `td_nod_buggy_machinegun` → `td_nod_buggymkii_machinegunbuggy2` | UP (20000→25000) | DOWN (200→120) | UP (4540→5274) | DOWN (600→132) | SAME (Scout→Scout) | DIFFERENT_LABELS | STATIC_DIFFERENCES | DPS_LOWER; SPEED_LOWER; WARHEAD_LABELS_DIFFER |
| `td_nod` | `td_nod_reconbike` → `td_nod_chemicalattackbike` | `td_nod_reconbike_rocket` → `td_nod_chemicalattackbike_chemicalbikerockets` | UP (17500→22500) | DOWN (200→175) | SAME (6000→6000) | UP (492→800) | SAME (Light→Light) | DIFFERENT_LABELS | STATIC_DIFFERENCES | SPEED_LOWER; WARHEAD_LABELS_DIFFER |
| `td_nod` | `td_nod_rocketsoldier` → `td_nod_chemicalrocketsoldier` | `td_nod_rocketsoldier_rockets` → `td_nod_chemicalrocketsoldier_chemrockets` | UP (9000→18000) | UP (50→60) | DOWN (6368→6006) | UP (286→667) | SAME (Flak→Flak) | DIFFERENT_LABELS | STATIC_DIFFERENCES | RANGE_LOWER; WARHEAD_LABELS_DIFFER |
| `td_nod` | `td_nod_ssmlauncher` → `td_nod_chemicalssmlauncher` | `td_nod_ssmlauncher_honestjohn` → `td_nod_chemicalssmlauncher_chemicalhonestjohn` | UP (20000→32500) | DOWN (100→75) | UP (8940→12345) | UP (400→845) | SAME (Light→Light) | DIFFERENT_LABELS | STATIC_DIFFERENCES | SPEED_LOWER; WARHEAD_LABELS_DIFFER |
| `td_nod` | `td_nod_stealthtank` → `td_nod_chemicalstealthtank` | `td_nod_stealthtank_stealthtankmissiles` → `td_nod_chemicalstealthtank_chemicalstealthtankmissiles` | UP (25000→90000) | DOWN (150→120) | DOWN (7432→6962) | UP (364→500) | UP (Light→Superheavy) | DIFFERENT_LABELS | STATIC_DIFFERENCES | RANGE_LOWER; SPEED_LOWER; WARHEAD_LABELS_DIFFER |
| `td_nod` | `td_nod_flametank` → `td_nod_flametankmkii` | `td_nod_flametank_bigflamer` → `td_nod_flametankmkii_bigflamer2` | UP (100000→200000) | DOWN (80→75) | UP (2390→2534) | UP (467→625) | SAME (Superheavy→Superheavy) | DIFFERENT_LABELS | STATIC_DIFFERENCES | SPEED_LOWER; WARHEAD_LABELS_DIFFER |
| `td_nod` | `td_nod_lighttank` → `td_nod_lighttankmkii` | `td_nod_lighttank_70mm` → `td_nod_lighttankmkii_lighttank2cannon` | SAME (80000→80000) | DOWN (110→100) | DOWN (4993→4903) | UP (133→229) | SAME (Medium→Medium) | SAME_LABELS | STATIC_DIFFERENCES | HP_SAME; RANGE_LOWER; SPEED_LOWER |
| `td_nod` | `td_nod_artillery` → `td_nod_specterartillery` | `td_nod_artillery_artilleryshell` → `td_nod_specterartillery_specterartilleryshell` | UP (17500→22500) | UP (55→100) | UP (12345→12640) | UP (286→410) | SAME (Light→Light) | SAME_LABELS | MEASURED_NO_LISTED_DIFFERENCE | — |
| `td_nod` | `td_nod_tiberiumharvester` → `td_nod_stealthharvester` | `—` → `—` | DOWN (150000→125000) | UP (60→75) | NOT_APPLICABLE (—→—) | NOT_APPLICABLE (—→—) | SAME (Heavy→Heavy) | NOT_APPLICABLE | STATIC_DIFFERENCES | HP_LOWER |
| `td_nod` | `td_nod_commando` → `td_nod_lasercommando` | `td_nod_commando_td_gdi_commando_sniper` → `td_nod_lasercommando_nodcommandolaser` | DOWN (80000→57000) | UP (65→79) | DOWN (8086→6030) | DOWN (1600→250) | SAME (Heroic→Heroic) | DIFFERENT_LABELS | STATIC_DIFFERENCES | DPS_LOWER; HP_LOWER; RANGE_LOWER; WARHEAD_LABELS_DIFFER |

## Promotion consumers outside an explicit replacement pair

| faction | promotion token | promotion unit | reason |
|---|---|---|---|
| `ra1_allies` | `ra1_allies_promotion_bastion` | `ra1_allies_bastionartillerybunker` | no active actor carries a negative ~!promotion prerequisite for this token |
| `ra1_allies` | `ra1_allies_promotion_chronotank` | `ra1_allies_chronotank` | no active actor carries a negative ~!promotion prerequisite for this token |
| `ra1_allies` | `ra1_allies_promotion_gapgeneratorandradarjammer` | `ra1_allies_gapgenerator` | no active actor carries a negative ~!promotion prerequisite for this token |
| `ra1_allies` | `ra1_allies_promotion_gapgeneratorandradarjammer` | `ra1_allies_mobilegapgenerator` | no active actor carries a negative ~!promotion prerequisite for this token |
| `ra1_allies` | `ra1_allies_promotion_gapgeneratorandradarjammer` | `ra1_allies_mobileradarjammer` | no active actor carries a negative ~!promotion prerequisite for this token |
| `ra1_allies` | `ra1_allies_promotion_machinegunner` | `ra1_allies_machinegunner` | no active actor carries a negative ~!promotion prerequisite for this token |
| `ra1_allies` | `ra1_allies_promotion_rapierjumpjet` | `ra1_allies_rapierjumpjet` | no active actor carries a negative ~!promotion prerequisite for this token |
| `ra1_allies` | `ra1_allies_promotion_reconranger` | `ra1_allies_reconranger` | no active actor carries a negative ~!promotion prerequisite for this token |
| `ra1_allies` | `ra1_allies_promotion_reinforcementpad` | `ra1_allies_reinforcementpad` | no active actor carries a negative ~!promotion prerequisite for this token |
| `ra1_allies` | `ra1_allies_promotion_tankdestroyer` | `ra1_allies_alliedtankdestroyer` | no active actor carries a negative ~!promotion prerequisite for this token |
| `ra1_soviets` | `ra1_soviets_promotion_gatlingtank` | `ra1_soviets_gatlingtank` | no active actor carries a negative ~!promotion prerequisite for this token |
| `ra1_soviets` | `ra1_soviets_promotion_monstertank` | `ra1_soviets_monstertank` | no active actor carries a negative ~!promotion prerequisite for this token |
| `ra1_soviets` | `ra1_soviets_promotion_mortarsoldier` | `ra1_soviets_mortarsoldier` | no active actor carries a negative ~!promotion prerequisite for this token |
| `ra1_soviets` | `ra1_soviets_promotion_supersonicnuclearbomber` | `ra1_soviets_supersonicnuclearbomber` | no active actor carries a negative ~!promotion prerequisite for this token |
| `ra1_soviets` | `ra1_soviets_promotion_volkov` | `ra1_soviets_volkov` | no active actor carries a negative ~!promotion prerequisite for this token |
| `td_gdi` | `td_gdi_promotion_firehawk` | `td_gdi_firehawk` | no active actor carries a negative ~!promotion prerequisite for this token |
| `td_gdi` | `td_gdi_promotion_gdidefenserig` | `td_gdi_defenserig` | no active actor carries a negative ~!promotion prerequisite for this token |
| `td_gdi` | `td_gdi_promotion_gdiofficer` | `td_gdi_officer` | no active actor carries a negative ~!promotion prerequisite for this token |
| `td_gdi` | `td_gdi_promotion_havocandexosuit` | `td_gdi_exosuit` | additional option unlocked by a shared token; not a replacement edge |
| `td_gdi` | `td_gdi_promotion_shotgunner` | `td_gdi_shotgunner` | no active actor carries a negative ~!promotion prerequisite for this token |
| `td_gdi` | `td_gdi_promotion_sniper` | `td_gdi_heavysniper` | no active actor carries a negative ~!promotion prerequisite for this token |
| `td_nod` | `td_nod_promotion_lasertrooper` | `td_nod_lasertrooper` | no active actor carries a negative ~!promotion prerequisite for this token |
| `td_nod` | `td_nod_promotion_upgradeupnodstealthname` | `td_nod_stealthsoldier` | additional option unlocked by a shared token; not a replacement edge |
| `td_nod` | `td_nod_promotion_upgradeupnodvenomname` | `td_nod_venom` | additional option unlocked by a shared token; not a replacement edge |

This list is not a claim that these units are wrong. It separates consumers with no base marker from additional options that share a token with a genuine replacement, preventing false harvester-to-soldier, commando-to-aircraft and commando-to-vehicle comparisons.
