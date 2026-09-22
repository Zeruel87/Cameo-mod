# `line_breaker` — NOT READY / UNAPPROVED

Diagnostic only: current ledger medians are not approved reference-consensus targets.
Faction approval/calibration, weapon structure and maintainer sign-off remain required.

## 1. The proposal

Source pool: selected factions tiberiandawn_gdi, tiberiandawn_nod, redalert_allies, redalert_soviets, redalert_japan — 4 of 33 fit-eligible class members are in the selected factions. The reference preference and members missing a stat give each axis its own contributing set, named below.

| axis | diagnostic candidate | ruled spec | evidence count | fit-eligible class percentile | contributing actors | basis |
|---|--:|--:|--:|--:|---|---|
| hp0 | 125000 | 750000 | 2 | 27.2727 | ra1_soviets_gorynychtank, td_nod_flametank | reference-backed ledger medians, snapped to step 1000 |
| speed0 | 75 | 80 | 2 | 42.4242 | ra1_soviets_gorynychtank, td_nod_flametank | reference-backed ledger medians, snapped to step 1 |
| range0_wdist | 2390 | 2500 | 2 | 19.2308 | ra1_soviets_gorynychtank, td_nod_flametank | reference-backed ledger medians, snapped to step 10 |
| cost0 | 1100 | 1600 | 2 | 12.1212 | ra1_soviets_gorynychtank, td_nod_flametank | reference-backed ledger medians, snapped to step 100 |

Status: UNAPPROVED; THIN hp; THIN speed; THIN range_wdist; THIN cost; NO MODEL — calibrated damage/reload not supplied

## 2. DPS is deferred

No DPS target is proposed while W24 moves. No synthetic damage/reload is assumed; there is no combat verifier or fit command to approve from this dossier.

## 3. Anchor and verifier actors

| role / actor | source | HP | speed | ground-domain range | cost |
|---|---|--:|--:|--:|--:|
| anchor: td_nod_flametank | ledger | 100000 | 80 | 2390 | 800 |
| anchor: td_nod_flametank | live | 100000 | 80 | 2390 | 800 |
| verifier: td_nod_flametankmkii | ledger | 200000 | 75 | 2534 | 1300 |
| verifier: td_nod_flametankmkii | live | 200000 | 75 | 2534 | 1300 |

Verifier / anchor ratios (HP, speed, range, cost): 2 / 0.9375 / 1.06025 / 1.625

| role | ledger nominal DPS/tick | measured tier factor | derived aggregate K | K fallbacks |
|---|--:|--:|--:|--:|
| anchor | 466.667 | 1 | 1.45112 | 0 |
| verifier | 625 | 0.7333 | 2.15235 | 0 |

Shared TechTier: DIFFERENT — verifier identity not applicable.

Shared aggregate K: DIFFERENT — verifier identity not applicable.

The 2x HP / 2x DPS / 2.5x cost identity is NOT established by stat ratios alone. K is a derived aggregate, not a measured matchup result; any missing sidecar is unavailable. The synthetic verifier remains withheld.

## 4. Membership

Every classified member with its LIVE resolved-YAML stats as it ships today, sorted by live cost, unavailable last. The ledger-based diagnostic candidate in section 1 is NOT recalculated from these rows. REF means STRONG/FAIR assignment, not an approved faction or a completed consensus. FORMULA means no accepted assignment. Rows marked excluded fail fitting eligibility (buildable=False and no explicit balance_include); they are displayed but never added to the candidate calculation. Unresolved members stay unavailable with their issue, never a fallback labeled live.

| actor | faction | evidence | HP | speed | range | cost | basis |
|---|---|---|--:|--:|--:|--:|---|
| td_nod_flametank | tiberiandawn_nod | REF | 100000 | 80 | 2390 | 800 | live resolved YAML |
| wc2_humans_demolitionsquad | warcraft2_humans | FORMULA | 40000 | 80 | unavailable | 800 | live resolved YAML |
| wc2_orcs_goblinsappers | warcraft2_orcs | FORMULA | 40000 | 80 | unavailable | 800 | live resolved YAML |
| forgotten_closhtank | tiberiansun_forgotten | FORMULA | 120000 | 80 | 2386 | 1000 | live resolved YAML |
| ts_nod_devilstongue | tiberiansun_nod | REF | 100000 | 70 | 4250 | 1150 | live resolved YAML |
| tkm_battlebus | redalert2mod_tkm | FORMULA | 50000 | 100 | 4831 | 1250 | live resolved YAML |
| asianalliance_asianflametank | redalert2mod_asianalliance | REF | 85000 | 85 | 3700 | 1300 | live resolved YAML |
| forgotten_flametank | tiberiansun_forgotten | REF | 200000 | 80 | 2425 | 1300 | live resolved YAML |
| ra1_soviets_gorynychtank | redalert_soviets | REF | 150000 | 70 | 2390 | 1300 | live resolved YAML |
| td_nod_flametankmkii | tiberiandawn_nod | FORMULA | 200000 | 75 | 2534 | 1300 | live resolved YAML |
| ts_gdi_mobileemp | tiberiansun_gdi | REF | 150000 | 100 | 1512 | 1400 | live resolved YAML |
| wc2_humans_knight | warcraft2_humans | FORMULA | 167500 | 115 | unavailable | 1600 | live resolved YAML |
| wc2_humans_paladin | warcraft2_humans | FORMULA | 167500 | 115 | unavailable | 1600 | live resolved YAML |
| wc2_orcs_ogre | warcraft2_orcs | FORMULA | 200000 | 85 | unavailable | 1800 | live resolved YAML |
| wc2_orcs_ogremage | warcraft2_orcs | FORMULA | 200000 | 85 | unavailable | 1800 | live resolved YAML |
| naxis_oldtank | redalert2mod_naxis | REF | 110000 | 50 | 7361 | 2000 | live resolved YAML |
| wc2_humans_warcraft3knight | warcraft2_humans | FORMULA | 180000 | 120 | unavailable | 2200 | live resolved YAML |
| ts_gdi_disruptor | tiberiansun_gdi | REF | 250000 | 50 | 4050 | 2400 | live resolved YAML |
| cabal_beholder | tiberiansun_cabal | FORMULA | 125000 | 125 | 2500 | 2500 | live resolved YAML |
| futuretech_plasmastrider | redalert2mod_futuretech | FORMULA | 240000 | 40 | 7000 | 2600 | live resolved YAML |
| ordos_heavyautoguntank | d2k_ordos | FORMULA | 160000 | 75 | 7480 | 2800 | live resolved YAML |
| latinsyndicate_tortugatank | redalert2mod_syndicate | REF | 875000 | 45 | 6000 | 3000 | live resolved YAML |
| cobra.steel | redalert2mod_consortium | FORMULA | 325000 | 55 | 8888 | 3600 | excluded from fit (buildable=False and no explicit balance_include) |
| td_gdi_assaultapc | tiberiandawn_gdi | FORMULA | 250000 | 100 | 5598 | 3930 | live resolved YAML |
| ra2_allies_battlefortress | redalert2_allies | REF | 320000 | 60 | 5000 | 4000 | live resolved YAML |
| ra2_allies_battlefortress_chrono | redalert2_allies | REF | 320000 | 60 | 5000 | 4000 | live resolved YAML |
| ra2_allies_battlefortress_empty | redalert2_allies | FORMULA | 320000 | 60 | 5000 | 4000 | live resolved YAML |
| steelconsortium_poseidontank | redalert2mod_consortium | FORMULA | 125000 | 50 | 6333 | 4000 | live resolved YAML |
| zerg_ultralisk | starcraft_zerg | FORMULA | 400000 | 80 | 1600 | 4400 | live resolved YAML |
| steelconsortium_megalodon | redalert2mod_consortium | REF | 450000 | 65 | 1600 | 4600 | live resolved YAML |
| asianalliance_warturtle | redalert2mod_asianalliance | FORMULA | 250000 | 75 | 4567 | 5000 | live resolved YAML |
| forgotten_thumperbus | tiberiansun_forgotten | FORMULA | 200000 | 90 | 7850 | 5200 | live resolved YAML |
| protoss_archon | starcraft_protoss | FORMULA | 350000 | 75 | 3152 | 5600 | live resolved YAML |
| latinsyndicate_carteltruck | redalert2mod_syndicate | REF | 167500 | 70 | 5800 | 6000 | live resolved YAML |

Classified ledger rows excluded by fitting eligibility: 1.

## 5. Reference consensus

Read-only R4 sensitivity through reference_targets.target_for's with-Cameo result; n counts external sources, plus Cameo's additional equal vote. Source families keep one vote each. Hero actors use their separate frozen hero-only population; they never enter ordinary distributions. Raw cross-game stats are not averaged. These numbers do NOT replace the candidate or constitute calibration.

| actor | exact source IDs used | HP target | speed target | range target | cost target | nominal damage/tick | issues |
|---|---|--:|--:|--:|--:|--:|---|
| ra2_allies_battlefortress | CnC Reloaded/BFRT; Mental Omega/BFRT; RA2 0XX/BFRT; RA2 Reborn/BFRT; Red Resurrection/BFRT; Romanov's Vengeance/bfrt; Valiant Shades/bfrt | 184860 (n=7) | 58.4608 (n=7) | 5478.61 (n=5) | 2713.29 (n=7) | 945.508 (n=5) | unapproved |
| ra2_allies_battlefortress_chrono | Mental Omega/CHRTNK; RA2 Reborn/CHRTNK; Red Resurrection/CTNK; Romanov's Vengeance/ctnk; Valiant Shades/chrp | 130497 (n=5) | 58.4604 (n=5) | 6832.38 (n=4) | 3326.21 (n=5) | 564.056 (n=4) | unapproved |
| asianalliance_asianflametank | RA2 Reborn/FLTNK; Rise of the East/FTNK | 80297.1 (n=2) | 77.0233 (n=2) | 4100.88 (n=1) | 1140.24 (n=2) | 963.372 (n=1) | unapproved |
| steelconsortium_megalodon | Mental Omega/MEGA | 275231 (n=1) | 77.7487 (n=1) | 1943.24 (n=1) | 3439.72 (n=1) | 593.212 (n=1) | unapproved |
| naxis_oldtank | RA2 0XX/ROLAND | 63249 (n=1) | 60.5857 (n=1) | 11085.4 (n=1) | 1520.28 (n=1) | 183.439 (n=1) | unapproved |
| latinsyndicate_carteltruck | Mental Omega/HTK; RA2 Reborn/HTK | 69268.4 (n=2) | 83.1349 (n=2) | 5303.1 (n=2) | 1267.01 (n=2) | 584.333 (n=2) | unapproved |
| latinsyndicate_tortugatank | RA2 Reborn/TZAR | 437217 (n=1) | 43.8197 (n=1) | 6671.35 (n=1) | 2928.03 (n=1) | 571.392 (n=1) | unapproved |
| ra1_soviets_gorynychtank | Combined Arms/HFTK | 147480 (n=1) | 67.9168 (n=1) | 2238.23 (n=1) | 1542.2 (n=1) | 759.423 (n=1) | unapproved |
| td_nod_flametank | Combined Arms/FTNK; DTA Enhanced/FTNK; OpenRA Tiberian Dawn/FTNK | 119237 (n=3) | 83.0855 (n=3) | 2547.04 (n=3) | 1103.53 (n=3) | 1187.08 (n=3) | unapproved |
| forgotten_flametank | Twisted Insurrection/BRAWL | 130703 (n=1) | 82.4964 (n=1) | 3945.69 (n=1) | 1317.39 (n=1) | 615.989 (n=1) | unapproved |
| ts_gdi_disruptor | CnC Reloaded/TSSONIC; OpenRA Tiberian Sun/SONIC; Shattered Paradise/SONIC | 153410 (n=3) | 56.8276 (n=3) | 5368.26 (n=1) | 1944.46 (n=3) | unavailable (n=0) | unapproved |
| ts_gdi_mobileemp | Shattered Paradise/M_EMP | 110394 (n=1) | 83.723 (n=1) | unavailable (n=0) | 1341.62 (n=1) | unavailable (n=0) | unapproved |
| ts_nod_devilstongue | CnC Reloaded/SUBTANK; Crystallized Nexus/SUBTANK; OpenRA Tiberian Sun/SUBTANK; Shattered Paradise/SUBTANK | 68599.4 (n=4) | 75.3838 (n=4) | 4079.37 (n=2) | 1133.43 (n=4) | 1207.15 (n=2) | unapproved |

## 6. Disagreements and gates

Anchor versus ruled spec (anchor actor only; the ruled spec is NOT applied to the verifier or to members):

| axis | anchor live | ruled spec | signed gap | gap % |
|---|--:|--:|--:|--:|
| hp | 100000 | 750000 | -650000 | -86.7% |
| speed | 80 | 80 | +0 | +0.0% |
| range_wdist | 2390 | 2500 | -110 | -4.4% |
| cost | 800 | 1600 | -800 | -50.0% |

Live resolved YAML versus the diagnostic candidate (unchanged, ledger-based):

| actor / axis | ledger | resolved YAML | candidate | live / candidate gap |
|---|--:|--:|--:|--:|
| td_nod_flametank / hp | 100000 | 100000 | 125000 | -20.0% |
| td_nod_flametank / speed | 80 | 80 | 75 | +6.7% |
| td_nod_flametank / range_wdist | 2390 | 2390 | 2390 | +0.0% |
| td_nod_flametank / cost | 800 | 800 | 1100 | -27.3% |
| td_nod_flametankmkii / hp | 200000 | 200000 | 125000 | +60.0% |
| td_nod_flametankmkii / speed | 75 | 75 | 75 | +0.0% |
| td_nod_flametankmkii / range_wdist | 2534 | 2534 | 2390 | +6.0% |
| td_nod_flametankmkii / cost | 1300 | 1300 | 1100 | +18.2% |

Ledger versus live discrepancies for classified members (signed gaps, live minus ledger, and percentage gaps; the percentage needs a finite positive ledger baseline; differing or unavailable axes only):

| actor / axis | ledger | live | signed gap | gap % |
|---|--:|--:|--:|--:|

W24: 0 class members with stacked mains (raw, no exemptions).

A zero stacked-main count is not full weapon clearance. Pending class migrations are not silently applied; an empty class stays NO SOURCE. Limited actors need hero-lane evidence, not admission into ordinary distributions.

## 7. What would make this wrong

These candidates are wrong if the selected current-stat pool is unrepresentative, its reference assignments are rejected, or its ledger differs from resolved YAML; approval and calibration must resolve those questions before any number is applied.

Evidence hashes (inputs, not approval):

```json
{
  "active_yaml_files": 399,
  "active_yaml_sha256": "b7d5ced1ce4194e0ffb23f728aabb661ad19951d3dc295b8f7adeb3895ba5069",
  "assignment_sha256": "6a16ad71a1f5e1e90705370f8c5bda8e4eb32b996fa4eec00a0f327eae9cac3a",
  "code_sha256": {
    "tools/audit/audit_three_way_split.py": "59ec52782cff2c2bfd5ad115c43a97a9318987319d80c92e9e209ab87994d2c8",
    "tools/audit/miniyaml.py": "2acfe7f8f427120f5199a175263ac5de7cfc560d1e67363a9be5df5f5822c6d9",
    "tools/balance/anchor_readiness.py": "0c1651d766e027068e1d92779211a59df61b8d6628e5b28749ed475b897d8518",
    "tools/balance/class_membership.py": "95fa24502b50e16d0dcff93c007fddd1b8e4af83271dd5818d5544615d90f431",
    "tools/balance/derive_virtual_anchor.py": "7ced2bc946868fa97c686bf6ec4969b8dfbf7247166f3e4b8ef73e964091ebb4",
    "tools/balance/diagnostic_output.py": "4baba0e3f3b3815341d84d7944d2539f19b6617a9ac4e86b80e731c15df9c409",
    "tools/balance/extract_stats.py": "0f6a9248432ed8708492587a8f1df9cf16de40834fee516957a2e62ebb3e609f",
    "tools/balance/faction_routes.py": "8d7ef545961c416bb201019e560b4a94077aa5652366b231ce6fea8df0d851d1",
    "tools/balance/firepower.py": "85718bd8f72b0226cc3997e12c6450fa9ce269e63a7095e9bf5021506110e604",
    "tools/balance/fit_class.py": "b6654767b3d643a9f7f3eeeb0882734302e28026acbcf18705a038f9a9f166a3",
    "tools/balance/formula.py": "645836856da5505dfc2b85da5cab2762753fabe11e6c35ccdfa5c2eca29ed8a4",
    "tools/balance/ini_cycle_evidence.py": "f2e14073c653222b0bf9eb955c0a70ab7c44c6dfce50926bde098a351ed90242",
    "tools/balance/ini_range_evidence.py": "814c48af8a6a54fc0cc351143a3aaebb5cf61e96e5a9ef0c756a28158f502f3f",
    "tools/balance/ini_weapon_selection.py": "10e4aa712cd5dfbd46413dec3cf69783716982149d69922a34eb831ed2850de2",
    "tools/balance/peer_base_state.py": "0c19301dec417d26a114342b2d242bfcc9bc800590437ad52ecd5dae3381ec86",
    "tools/balance/peer_corpus.py": "d798972f0b5e2b1301f054952d0d70e369376233f143e6f07fca14d2e7e94166",
    "tools/balance/peer_nominal_evidence.py": "d8b080670fc2ca10ee7a8a8f68d66e1cf8d61165b246602df3b8e1d044c57c1f",
    "tools/balance/peer_range_evidence.py": "05fe2aa2287008a9bf9498c9dc1e60fa25762a134837176593e5c1ae6a7f63e9",
    "tools/balance/propose_anchor_spec.py": "3253e367ecc43372458c71f567eb8d85a64546b2ad8fcb9b12dd6c6f13667223",
    "tools/balance/reference_distribution.py": "441567b01b57d2f0de377962d848e47f34943b63c544f17347bb17ae040fcad3",
    "tools/balance/reference_lineages.py": "dbc14d5f84909becaadee3be6b30f5ed84d9364d844b9bd063325ae07a59bf62",
    "tools/balance/reference_targets.py": "9216ae522a04ce61639652e089f81e9486c82ae3687398585659bbdb4f8dbc8b",
    "tools/balance/synthesize_reference.py": "e0e3f78d794743524a4b95164cbf32f883bd39b3c38442ebdd4aec787620b695",
    "tools/balance/tier_chain.py": "b23296dedcdf713d9cb20abb8a81792f8c35cb0ee5eb3c6b019b507af7f03d3a"
  },
  "ledger_sha256": {
    "band-scope-20260911.json": "c751e78ecb932eeda1faa1db6b072d1888ec2e71a7ec152f25d51714b836ae98",
    "building-shape-review-20260911.json": "b964fa9408bcbf5458eaf944791a665b048fe811fc1feac8973df14f512fd275",
    "cargo-load-proposal-20260911.json": "8bd26b318068bb171ebef0321f2c15f07d90c4c7a8e79aac68b2289c0f6559c7",
    "class_anchors.json": "c815917c536ddf7c695133a482279b7a320281542243d9f8d2a17153ecafd393",
    "d2k_atreides.json": "a3f8dc73f8778bfe664d521ae4aee162e8668b13585a2338432b33c062513ad3",
    "d2k_corrino.json": "639743286516a8ce5979075106f1f9b7be4701a81447a0c1f57801ea036b154d",
    "d2k_harkonnen.json": "1f20eda22c9a34b31938933a2813a8c40832abd3fae98ce0ac7c6fc086e53725",
    "d2k_ixian.json": "64b56133e5803d6cef8c9b31305479e029657efa7c346768b971cec496c004f2",
    "d2k_ordos.json": "a574b3559c30d6bc20ea4292600aae4e68243d4eb1283e8a7cbcae1a54735953",
    "defense-armor-curves-20260911.json": "7a196ee55d46c04d3ebbf684f123172bfffd638fe1507fedffbe16175bd05f05",
    "four_voice_selection_pilot_20260911.json": "560b106eb0800459b28ce5bcc10908f16b25ef1b10cf81ced8cc5bf715f6752c",
    "four_voice_selection_pilot_aircraft_20260911.json": "2778deb4ae05a5913bd333b88148e762785ce1c1c1bdde320cdc858f7bea5ce7",
    "four_voice_selection_pilot_infantry_20260911.json": "4a056be11792d5aa57693f27858f09a507b422e3c5405242eb01f1d53764d41b",
    "infantry_artillery_pressure_manifest_20260911.json": "6ca42db4ff43f57c61a76a9c455c788f60e7c99fdf6c0c07558c62a37a6103a4",
    "redalert2_allies.json": "57919bf72fd8ab52a73bea84fe887de4088f94cc6e847ca66da21766740e604d",
    "redalert2_soviets.json": "1426a49ca0eea4026469544c74892fd8169d269184f11eb8942813ab72d5be47",
    "redalert2_yuri.json": "031732e0559e60305c3849f4c14a30b2892198a8e78e6d479ed60c2a6d51b610",
    "redalert2mod_asianalliance.json": "3acc219976b1826fbdf4526f41e02f9398bf22ce630e04e335774516050f6daf",
    "redalert2mod_consortium.json": "c9affe4d4bd1b0146b7c0710d687243c3f66f491715142463e021e48c9911179",
    "redalert2mod_futuretech.json": "a11e2459d51b7884fdcf03fa5ea7ad527dbb5dd621b74f9364ff6ed92b3ac588",
    "redalert2mod_naxis.json": "f95893b7bf039f158bda9392b7cf87559edb42deaedcc038bf54c9ccdc921190",
    "redalert2mod_schwarzermond.json": "4aef8c2cdb2ff95db20ee3938e2429b733fef36715af3c511ab0422b05536dc3",
    "redalert2mod_syndicate.json": "5e448653c63cc395095fd1291b92663fd6d5154b7b6d826adfc7332110e3c440",
    "redalert2mod_tkm.json": "743af59b4b865b194246de6da376aae59f1b510399659f91bfa6aa6d46621dff",
    "redalert_allies.json": "543e8e1e6841ef8608eb297745c42781d09655b88379f2c3f9d018605d5c21d1",
    "redalert_japan.json": "01aac7ff7d4922f7466da202d53b21e721e608bce2d7236c59c16a4bd097716d",
    "redalert_soviets.json": "47cddf93e69aef15b0c293087e81215c0d6081f501dd67ebb62a847fc26c007a",
    "shared_d2k.json": "b9ab18229ac3b0ff3fc0bda77b950d5461dbbd4199773a0d341426a3b681397d",
    "shared_redalert.json": "c148516908aad81d153944af1dd1f93d13fd97a35dd580eebf1f20390dcf0d51",
    "shared_redalert2.json": "615eb16f66009ba83ba115f9f91fcf5e909397af4e6277253d49024cdfb4cea2",
    "shared_tiberiandawn.json": "4777a1f27ac21f1d0aaa62da562b2f1a27bfa7e0c460e10147c0f2ce8abab87f",
    "starcraft_protoss.json": "98e5f156618f49c77d025f30b7a0b92c918f0d7abe377ece76f14ae37e0e3b0f",
    "starcraft_terran.json": "eca1fa75315f6051372e04b600fa0916163a2d42a5b587afa1b56239d74c2841",
    "starcraft_zerg.json": "d64dceb6adf752f93e87a2a9523356f5818255e7da2a0272f5f736db4f718795",
    "tiberiandawn_gdi.json": "199d196e1f5fdb7d18c042e2344e7cafd7d0a106061c8f39888f204344302824",
    "tiberiandawn_nod.json": "c9edca9c08f72b3dac78a8dbffcfb4641a3ca8df66ec69eb06ebc872fffbfde9",
    "tiberiansun_cabal.json": "9d370bf0263215827d738cdc416b8f25b0a8fa7596c4ca65aee6e1a19221b6bb",
    "tiberiansun_forgotten.json": "e2dc5a9ff37f80cdc784bbeb1fd81f8912b9bf27a2315a5109c82137dcfefe99",
    "tiberiansun_gdi.json": "bffafcabb4512312320692f9dc1beb6f21329790823e192cfb524291066a2fac",
    "tiberiansun_nod.json": "7d47f9df0813efbdd5d8cf0e91c44ee953137e35581f18e92386bbebfc97ea9e",
    "warcraft2_humans.json": "c27fdcf9dbbe3e88030d774eca37730306ef701f60eb563561d182c703a52514",
    "warcraft2_orcs.json": "03435d2a65fad3359c820a7084acf3b57451f80890953d04088da81f2bdbec3c"
  },
  "reference_input_sha256": {
    "docs/design/ORIGINAL_UNITS_PEER_OPENRA.md": "d37db59f883bbfd62b3faa555788f4ac79970eae675f273eb0b89f8b9c22e36c",
    "docs/design/ORIGINAL_UNITS_RAW.md": "7624e5567f674cdfc86c160fd029157b495f124bbc0ea8d10c8c4869d3a48523",
    "docs/reference/armor_normalized.json": "a5d50611bf1946971e75b6309a11fdde9f2b9d09664c21f900e30c21aaec37e4",
    "docs/reference/cameo_baselines/pre_reference_20260910.json": "726ada6afec708f8c6e9798ecbfb2758c842195f66755c2d5e683432c4a86f95",
    "docs/reference/cameo_baselines/pre_reference_heroes_20260910.json": "101a934792713dd6ccf5fbeb99629db0379af7b1f9a51d52d02a010795e5365c",
    "docs/reference/ini_corpus.json": "c1883cb04d2b42b370aa1dba3bdd12c080d909c61a3d3adf92156f5f931ed92a",
    "docs/reference/ini_cycle_evidence.json": "e371c371a08a6726025e61771c1ecd497b6917a2b03a849c63193104647a664f",
    "docs/reference/ini_range_evidence.json": "445de219cd5a5c07643373651a7c5403a67730f40b1049d2b794792fc6619832",
    "docs/reference/ini_weapon_selection.json": "d6ade15287b13515f4dec95bebee061c0139e44a68b2bd4f9c4262b838702f0b",
    "docs/reference/peer_base_state.json": "8a52f664d4b84feca0b121e4da199b902b1c5279c8eefbf106836ce11b4d1b80",
    "docs/reference/peer_corpus/ca_ab9e477c.jsonl": "e80f02b6ae603adfb5c3015045f94011a4af77ac4336f34bb35e153c30f1956f",
    "docs/reference/peer_corpus/cnc_bbd36d9e.jsonl": "1dc3c1e1ccde2b16e550d044eea0874019cc517d6cbc3d8a89113646725d117e",
    "docs/reference/peer_corpus/d2k_bbd36d9e.jsonl": "7a4c72f4d7f3aa9cd8f58ebed6149e8dff75eb9ed31bc1b8bb3157d6f4d1933b",
    "docs/reference/peer_corpus/index.json": "7928f8b30c2268746a0272f0d51b5876ffd8a95d2f7f8d7ddb43949ceef35686",
    "docs/reference/peer_corpus/ra_bbd36d9e.jsonl": "d417f8af2ae7766901a9538aa5a9ebb3d3f33cd744c7cf25e3270d9d5367bf4e",
    "docs/reference/peer_corpus/ts_bbd36d9e.jsonl": "f3a46a072568227b7c1cf2524a86d082dc94d5f72452d2eb064f6031575130b7",
    "docs/reference/peer_nominal_evidence.json": "e9c57cb3d7f039c35c37b2c94c24ac8f337461527e689607098ebb8bf7cb3910",
    "docs/reference/peer_range_evidence.json": "3124ae2a157fa1b5ef3af5c5031f5013eeb3d4e07f48a5ccdd089f85183de298"
  },
  "revision": "4f104c4181db524ef3aec630870ab5b2ff47776d",
  "sidecar_sha256": {
    "d2k_atreides.json": "1dac8d0c8b888027a42362789c1f4077f57aec4377d0bd258d063986f0dcd9e3",
    "d2k_corrino.json": "1b05fde600929651b97e13a13e2137dffa2659467f9821f07544af09d404cf26",
    "d2k_harkonnen.json": "e2409c2bc7519ff905e56e05240faa8f58f4c216ad718c784b9314a17d2b3b25",
    "d2k_ixian.json": "79053375fe4381984afe529f2111b04da6461f16dc29ade33d53eeeddf7dd150",
    "d2k_ordos.json": "93827facfd01ff60e236273ad7ce51a3d57ccdfd58c7bcbeaca21dbede2aeba9",
    "redalert2_allies.json": "77630285c22d7909af8d50a7f00ba2470ab1124f157516b7541b6d819e5db89c",
    "redalert2_soviets.json": "e4394c22f0e2015f0734cfcc34134d91a001c1349f551a46ee3f03be71398196",
    "redalert2_yuri.json": "bd8c3958fcaac24463d70260e9a5bcb0059a87dd0abcd726e8502bd0e02c4bb4",
    "redalert2mod_asianalliance.json": "f13bd1e640c836bab59496415844b7ac5511adcc679bd5a83322b9054442c611",
    "redalert2mod_consortium.json": "5ec00969ee310468e2a70508f99e6d320411b4cae61852d391de2d3364d405e1",
    "redalert2mod_futuretech.json": "23b405877d2c7f052a17c1fb164a1815e85155ed69aaf4fe0e3a45df30f7fdcc",
    "redalert2mod_naxis.json": "d1dd02f4f0eea2342fe489c8a8daec83790f8fe7dd58b445fca18651a4dd4255",
    "redalert2mod_schwarzermond.json": "9e7e1473d09ef620a574730923d8e1e591a1b11f2fa6cbefe2cfce15c3420052",
    "redalert2mod_syndicate.json": "a18730c9b70824cbc1309cde5c8e01cbcc5f792674f9b3f89ff9b7862827f7e0",
    "redalert2mod_tkm.json": "a626d6fcbf8c394741e8adc5241d01cdba50e0cd0c4fbb855316467ef6702713",
    "redalert_allies.json": "0e68615d776543fd205b2874bb47729973e1014b6c42d4fe0ca6397b8173f019",
    "redalert_japan.json": "db29f072b77c7bc468e6e52004313b248dc1e2f6a26ebf9dde13a9c2b23b26e8",
    "redalert_soviets.json": "fa430c730ae496bf8ba416a4af5c3f98a4bc0dbdbbdc09497e047e5602a94070",
    "shared_d2k.json": "bddd30b21ebb2e111cbfe360a4f7e44155eac9b4cfd3876c4d3b228469c076d9",
    "shared_redalert.json": "46c3d4527db98553db4520e0e254874c4e21b8c3974a19aab023d768935ab82b",
    "shared_redalert2.json": "6c5bb363459144f070344dc67b65d392d7fcd22ed0f75da765c1fb9bcd2c8c81",
    "shared_tiberiandawn.json": "c14608cdb9dc319c3b8bcee9f8a679e65b350743568aff2cf9826cf0489b6a05",
    "starcraft_protoss.json": "5bc117ffff188916eced4864dac5112b93a03933c5a8044f6893bdd12632982e",
    "starcraft_terran.json": "1f6da6b0f66d2c8e1187283ad19a9a863546f947f3ed0cfb8d3eee005bf79097",
    "starcraft_zerg.json": "eb1b3c359080fb19b800269cc5e7c1fd3ff6c0a6bb8c57e40182d143ebfc1138",
    "tiberiandawn_gdi.json": "d8f52e3cb5556d96cf30484a1956ceb9671b1f47a2424310c57e81d9da574bbc",
    "tiberiandawn_nod.json": "3c670968dfbc015739c68b2079d30fe28411d8fcb26baae6b3beb7886f2c71cf",
    "tiberiansun_cabal.json": "591ce5f66507d2fd1aad619b96066b1df2650ce9d4b994e50dc9802fede29457",
    "tiberiansun_forgotten.json": "6de8ff78921941ea091e9d55700bff97796589a037e813a4c418c03a99fb6415",
    "tiberiansun_gdi.json": "821ba585f3586628952a5c3d47ea154b938111a7785e540cfa6bb3880edda3c1",
    "tiberiansun_nod.json": "4cb6220f136496d881d84c418e86fab59fc9306fcfaa91cf1d098518dd789c96",
    "warcraft2_humans.json": "2c4201cf291242dd5d990c46f92675b59e9be6c40930e0576c8587526538cb78",
    "warcraft2_orcs.json": "c1af8a1cc246be562aee045bcd69f5fe668dadba13656dc88a76ffc30f079ca5"
  }
}
```
