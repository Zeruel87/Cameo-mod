# Promotion replacement superiority audit

**REVIEW ONLY.** Replacement pairs are taken from authored negative promotion prerequisites. This receipt does not remove `^PromotionUnitBuff`, edit costs or YAML, or certify gameplay balance.

## Scope

- Promotion tokens: **48**; tokens with an explicit base-disable marker: **23**.
- Promotion consumers: **47**; replacement pairs evaluated: **26**.
- Promotion consumers without a base-disable marker: **21**. These remain mapping/design questions.
- HP, speed and armor use the resolved active ruleset. Range, nominal DPS and warhead class use the existing default primary priced armament from the balance ledger; upgrades, secondary payloads, status uptime and gameplay are excluded.

## Replacement pairs

| faction | base → promotion | HP | speed | range | nominal DPS | armor | warhead class | status | findings |
|---|---|---|---|---|---|---|---|---|---|
| `ra1_allies` | `ra1_allies_pillbox` → `ra1_allies_camopillbox` | UP (90000→122500) | NOT_APPLICABLE (—→—) | NOT_APPLICABLE (—→—) | NOT_APPLICABLE (—→—) | SAME (Concrete→Concrete) | NOT_APPLICABLE | NO_STATIC_DEFECT_SEEN | — |
| `ra1_allies` | `ra1_allies_alliedapc` → `ra1_allies_phasetransport` | DOWN (50000→30000) | UP (105→125) | DOWN (5978→5038) | UP (400→1067) | DOWN (Medium→Light) | UP | REVIEW_REQUIRED | ARMOR_WEAKER; HP_NOT_STRICTLY_HIGHER; RANGE_LOWER |
| `ra1_allies` | `ra1_allies_alliedlighttank` → `ra1_allies_sheridanassaulttank` | UP (50000→85000) | DOWN (120→85) | UP (4720→5023) | DOWN (162→62) | SAME (Medium→Medium) | SAME | REVIEW_REQUIRED | DPS_NOT_HIGHER; SPEED_LOWER_REQUIRES_REVIEW; WARHEAD_CLASS_NOT_STRONGER |
| `ra1_allies` | `ra1_allies_alliedmediumtank` → `ra1_allies_alliedtigerheavytank` | UP (90000→160000) | DOWN (100→75) | UP (5159→5915) | UP (170→267) | SAME (Heavy→Heavy) | UP | REVIEW_REQUIRED | SPEED_LOWER_REQUIRES_REVIEW |
| `ra1_soviets` | `ra1_soviets_dog` → `ra1_soviets_cyberdog` | UP (5000→50000) | SAME (100→100) | UP (2000→2500) | UNRESOLVED (—→—) | UP (None→Plate) | UNRESOLVED | UNRESOLVED | UNRESOLVED_DPS; UNRESOLVED_WARHEAD_CLASS |
| `td_gdi` | `td_gdi_apc` → `td_gdi_assaultapc` | UP (47500→250000) | SAME (100→100) | DOWN (5668→5598) | DOWN (400→190) | UP (Medium→Superheavy) | DOWN | REVIEW_REQUIRED | DPS_NOT_HIGHER; RANGE_LOWER; WARHEAD_CLASS_NOT_STRONGER |
| `td_gdi` | `td_gdi_grenadier` → `td_gdi_empgrenadier` | UP (8000→32000) | DOWN (75→60) | DOWN (6097→5694) | UP (381→649) | SAME (None→None) | UP | REVIEW_REQUIRED | RANGE_LOWER; SPEED_LOWER_REQUIRES_REVIEW |
| `td_gdi` | `td_gdi_commando` → `td_gdi_exosuit` | DOWN (80000→50000) | UP (65→100) | DOWN (8086→6806) | DOWN (1600→500) | CROSS_TYPE (Heroic→Light) | UP | REVIEW_REQUIRED | DPS_NOT_HIGHER; HP_NOT_STRICTLY_HIGHER; RANGE_LOWER |
| `td_gdi` | `td_gdi_commando` → `td_gdi_havoc` | UP (80000→100000) | UP (65→75) | DOWN (8086→7750) | DOWN (1600→400) | SAME (Heroic→Heroic) | UP | REVIEW_REQUIRED | DPS_NOT_HIGHER; RANGE_LOWER |
| `td_gdi` | `td_gdi_humvee` → `td_gdi_humveemkii` | UP (27500→37500) | DOWN (150→115) | UP (4792→5598) | DOWN (857→95) | SAME (Scout→Scout) | SAME | REVIEW_REQUIRED | DPS_NOT_HIGHER; SPEED_LOWER_REQUIRES_REVIEW; WARHEAD_CLASS_NOT_STRONGER |
| `td_gdi` | `td_gdi_mammothtank` → `td_gdi_mammothtankmkiii` | UP (225000→500000) | DOWN (60→55) | UP (6141→6340) | UP (200→218) | SAME (Superheavy→Superheavy) | SAME | REVIEW_REQUIRED | SPEED_LOWER_REQUIRES_REVIEW; WARHEAD_CLASS_NOT_STRONGER |
| `td_gdi` | `td_gdi_rocketsoldier` → `td_gdi_sonicmissilesoldier` | UP (9000→25000) | SAME (50→50) | UP (6368→7500) | UP (286→408) | UP (Flak→Plate) | UP | NO_STATIC_DEFECT_SEEN | — |
| `td_gdi` | `td_gdi_battletank` → `td_gdi_predatortank` | UP (125000→170000) | DOWN (80→70) | UP (5438→5880) | UP (111→114) | SAME (Heavy→Heavy) | SAME | REVIEW_REQUIRED | SPEED_LOWER_REQUIRES_REVIEW; WARHEAD_CLASS_NOT_STRONGER |
| `td_nod` | `td_nod_flamethrower` → `td_nod_blackhandflamer` | UP (20000→36000) | UP (60→66) | UP (2085→4988) | UP (333→364) | SAME (Plate→Plate) | UP | NO_STATIC_DEFECT_SEEN | — |
| `td_nod` | `td_nod_buggy` → `td_nod_buggymkii` | UP (20000→25000) | DOWN (200→120) | UP (4540→5274) | DOWN (600→132) | SAME (Scout→Scout) | UP | REVIEW_REQUIRED | DPS_NOT_HIGHER; SPEED_LOWER_REQUIRES_REVIEW |
| `td_nod` | `td_nod_reconbike` → `td_nod_chemicalattackbike` | UP (17500→22500) | DOWN (200→175) | SAME (6000→6000) | UP (492→800) | SAME (Light→Light) | SAME | REVIEW_REQUIRED | SPEED_LOWER_REQUIRES_REVIEW; WARHEAD_CLASS_NOT_STRONGER |
| `td_nod` | `td_nod_rocketsoldier` → `td_nod_chemicalrocketsoldier` | UP (9000→18000) | UP (50→60) | DOWN (6368→6006) | UP (286→667) | SAME (Flak→Flak) | SAME | REVIEW_REQUIRED | RANGE_LOWER; WARHEAD_CLASS_NOT_STRONGER |
| `td_nod` | `td_nod_ssmlauncher` → `td_nod_chemicalssmlauncher` | UP (20000→32500) | DOWN (100→75) | UP (8940→12345) | UP (400→845) | SAME (Light→Light) | SAME | REVIEW_REQUIRED | SPEED_LOWER_REQUIRES_REVIEW; WARHEAD_CLASS_NOT_STRONGER |
| `td_nod` | `td_nod_stealthtank` → `td_nod_chemicalstealthtank` | UP (25000→90000) | DOWN (150→120) | DOWN (7432→6962) | UP (364→500) | UP (Light→Superheavy) | SAME | REVIEW_REQUIRED | RANGE_LOWER; SPEED_LOWER_REQUIRES_REVIEW; WARHEAD_CLASS_NOT_STRONGER |
| `td_nod` | `td_nod_flametank` → `td_nod_flametankmkii` | UP (100000→200000) | DOWN (80→75) | UP (2390→2534) | UP (467→625) | SAME (Superheavy→Superheavy) | UP | REVIEW_REQUIRED | SPEED_LOWER_REQUIRES_REVIEW |
| `td_nod` | `td_nod_lighttank` → `td_nod_lighttankmkii` | SAME (80000→80000) | DOWN (110→100) | DOWN (4993→4903) | DOWN (133→0) | SAME (Medium→Medium) | SAME | REVIEW_REQUIRED | DPS_NOT_HIGHER; HP_NOT_STRICTLY_HIGHER; RANGE_LOWER; SPEED_LOWER_REQUIRES_REVIEW; WARHEAD_CLASS_NOT_STRONGER |
| `td_nod` | `td_nod_artillery` → `td_nod_specterartillery` | UP (17500→22500) | UP (55→100) | UP (12345→12640) | UP (286→410) | SAME (Light→Light) | SAME | REVIEW_REQUIRED | WARHEAD_CLASS_NOT_STRONGER |
| `td_nod` | `td_nod_tiberiumharvester` → `td_nod_stealthharvester` | DOWN (150000→125000) | UP (60→75) | NOT_APPLICABLE (—→—) | NOT_APPLICABLE (—→—) | SAME (Heavy→Heavy) | NOT_APPLICABLE | REVIEW_REQUIRED | HP_NOT_STRICTLY_HIGHER |
| `td_nod` | `td_nod_tiberiumharvester` → `td_nod_stealthsoldier` | DOWN (150000→25000) | UP (60→72) | UNRESOLVED (—→6480) | UNRESOLVED (—→679) | CROSS_TYPE (Heavy→Plate) | UNRESOLVED | UNRESOLVED | HP_NOT_STRICTLY_HIGHER; UNRESOLVED_DPS; UNRESOLVED_RANGE; UNRESOLVED_WARHEAD_CLASS |
| `td_nod` | `td_nod_commando` → `td_nod_lasercommando` | DOWN (80000→57000) | UP (65→79) | DOWN (8086→6030) | DOWN (1600→250) | SAME (Heroic→Heroic) | UP | REVIEW_REQUIRED | DPS_NOT_HIGHER; HP_NOT_STRICTLY_HIGHER; RANGE_LOWER |
| `td_nod` | `td_nod_commando` → `td_nod_venom` | DOWN (80000→27500) | UP (65→200) | DOWN (8086→4000) | DOWN (1600→444) | CROSS_TYPE (Heroic→Helicopter) | UP | REVIEW_REQUIRED | DPS_NOT_HIGHER; HP_NOT_STRICTLY_HIGHER; RANGE_LOWER |

## Promotion consumers without an explicit replacement marker

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
| `td_gdi` | `td_gdi_promotion_shotgunner` | `td_gdi_shotgunner` | no active actor carries a negative ~!promotion prerequisite for this token |
| `td_gdi` | `td_gdi_promotion_sniper` | `td_gdi_heavysniper` | no active actor carries a negative ~!promotion prerequisite for this token |
| `td_nod` | `td_nod_promotion_lasertrooper` | `td_nod_lasertrooper` | no active actor carries a negative ~!promotion prerequisite for this token |

The unpaired list is not a claim that these units are wrong; it records where the current YAML does not identify a base unit to compare. Specialized roles, multiple units unlocked by one token and cross-type replacements require an explicit policy or mapping before the hidden buff can be removed safely.
