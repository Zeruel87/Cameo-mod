# `scout` — NOT READY / UNAPPROVED

Diagnostic only: current ledger medians are not approved reference-consensus targets.
Faction approval/calibration, weapon structure and maintainer sign-off remain required.

## 1. The proposal

Source pool: selected factions tiberiandawn_gdi, tiberiandawn_nod, redalert_allies, redalert_soviets, redalert_japan — 5 of 27 fit-eligible class members are in the selected factions. The reference preference and members missing a stat give each axis its own contributing set, named below.

| axis | diagnostic candidate | ruled spec | evidence count | fit-eligible class percentile | contributing actors | basis |
|---|--:|--:|--:|--:|---|---|
| hp0 | 31000 | 20000 | 4 | 55.5556 | ra1_soviets_rifleinfantry, ra1_allies_rifleinfantry, td_gdi_minigunner, td_nod_minigunner | reference-backed ledger medians, snapped to step 1000 |
| speed0 | 59 | 60 | 4 | 48.1481 | ra1_soviets_rifleinfantry, ra1_allies_rifleinfantry, td_gdi_minigunner, td_nod_minigunner | reference-backed ledger medians, snapped to step 1 |
| range0_wdist | 5080 | 5000 | 4 | 44.4444 | ra1_soviets_rifleinfantry, ra1_allies_rifleinfantry, td_gdi_minigunner, td_nod_minigunner | reference-backed ledger medians, snapped to step 10 |
| cost0 | 100 | 100 | 4 | 16.6667 | ra1_soviets_rifleinfantry, ra1_allies_rifleinfantry, td_gdi_minigunner, td_nod_minigunner | reference-backed ledger medians, snapped to step 100 |

Status: UNAPPROVED; NO MODEL — calibrated damage/reload not supplied

## 2. DPS is deferred

No DPS target is proposed while W24 moves. No synthetic damage/reload is assumed; there is no combat verifier or fit command to approve from this dossier.

## 3. Anchor and verifier actors

| role / actor | source | HP | speed | ground-domain range | cost |
|---|---|--:|--:|--:|--:|
| anchor: naxis_naxiriflesoldier | ledger | 20000 | 60 | 5000 | 100 |
| anchor: naxis_naxiriflesoldier | live | 20000 | 60 | 5000 | 100 |
| verifier: forgotten_mutantsoldier | ledger | 40000 | 60 | 5000 | 250 |
| verifier: forgotten_mutantsoldier | live | 40000 | 60 | 5000 | 250 |

Verifier / anchor ratios (HP, speed, range, cost): 2 / 1 / 1 / 2.5

| role | ledger nominal DPS/tick | measured tier factor | derived aggregate K | K fallbacks |
|---|--:|--:|--:|--:|
| anchor | 80 | 1 | 0.454125 | 0 |
| verifier | 160 | 1 | 1.10606 | 0 |

Shared TechTier: equal.

Shared aggregate K: DIFFERENT — verifier identity not applicable.

The 2x HP / 2x DPS / 2.5x cost identity is NOT established by stat ratios alone. K is a derived aggregate, not a measured matchup result; any missing sidecar is unavailable. The synthetic verifier remains withheld.

## 4. Membership

Every classified member with its LIVE resolved-YAML stats as it ships today, sorted by live cost, unavailable last. The ledger-based diagnostic candidate in section 1 is NOT recalculated from these rows. REF means STRONG/FAIR assignment, not an approved faction or a completed consensus. FORMULA means no accepted assignment. Rows marked excluded fail fitting eligibility (buildable=False and no explicit balance_include); they are displayed but never added to the candidate calculation. Unresolved members stay unavailable with their issue, never a fallback labeled live.

| actor | faction | evidence | HP | speed | range | cost | basis |
|---|---|---|--:|--:|--:|--:|---|
| naxis_naxiriflerecruit | redalert2mod_naxis | FORMULA | 21000 | 48 | 5227 | 75 | live resolved YAML |
| E1 | tiberiandawn_gdi | FORMULA | 31000 | 63 | 5499 | 100 | excluded from fit (buildable=False and no explicit balance_include) |
| naxis_naxiriflesoldier | redalert2mod_naxis | FORMULA | 20000 | 60 | 5000 | 100 | live resolved YAML |
| naxis_undead | redalert2mod_naxis | FORMULA | 15000 | 50 | 5621 | 100 | live resolved YAML |
| ra1_allies_rifleinfantry | redalert_allies | REF | 27000 | 55 | 5500 | 100 | live resolved YAML |
| ra1_soviets_rifleinfantry | redalert_soviets | REF | 34000 | 54 | 4668 | 100 | live resolved YAML |
| ra2_soviets_conscript | redalert2_soviets | REF | 26000 | 58 | 4500 | 100 | live resolved YAML |
| td_gdi_minigunner | tiberiandawn_gdi | REF | 31000 | 63 | 5499 | 100 | live resolved YAML |
| td_nod_minigunner | tiberiandawn_nod | REF | 30000 | 66 | 4609 | 100 | live resolved YAML |
| asianalliance_asianmilitia | redalert2mod_asianalliance | FORMULA | 24000 | 53 | 4500 | 110 | live resolved YAML |
| ordos_lightinfantry | d2k_ordos | FORMULA | 28000 | 62 | 5475 | 120 | live resolved YAML |
| tkm_rifleman | redalert2mod_tkm | FORMULA | 29000 | 61 | 5042 | 120 | live resolved YAML |
| ts_gdi_lightinfantry | tiberiansun_gdi | REF | 16000 | 60 | 4062 | 120 | live resolved YAML |
| ts_nod_lightinfantry | tiberiansun_nod | REF | 16000 | 60 | 4062 | 120 | live resolved YAML |
| latinsyndicate_latinmilitia | redalert2mod_syndicate | FORMULA | 25000 | 51 | 5395 | 130 | live resolved YAML |
| atreides_lightinfantry | d2k_atreides | FORMULA | 32000 | 56 | 5475 | 150 | live resolved YAML |
| corrino_lightinfantry | d2k_corrino | FORMULA | 32000 | 56 | 5475 | 150 | live resolved YAML |
| harkonnen_lightinfantry | d2k_harkonnen | FORMULA | 32000 | 56 | 5475 | 150 | live resolved YAML |
| ixian_lightinfantry | d2k_ixian | FORMULA | 32000 | 56 | 5475 | 150 | live resolved YAML |
| light_inf | shared_d2k | FORMULA | 40000 | 54 | 5475 | 150 | live resolved YAML |
| ra2e2.black | shared_redalert2 | FORMULA | 25000 | 58 | 4500 | 150 | excluded from fit (buildable=False and no explicit balance_include) |
| forgotten_mutant | tiberiansun_forgotten | REF | 45000 | 65 | 5219 | 160 | live resolved YAML |
| forgotten_mutant_sp | tiberiansun_forgotten | FORMULA | 45000 | 65 | 5219 | 160 | excluded from fit (buildable=False and no explicit balance_include) |
| forgotten_mutant_wild | tiberiansun_forgotten | FORMULA | 45000 | 65 | 5219 | 160 | excluded from fit (buildable=False and no explicit balance_include) |
| futuretech_scoutdroid | redalert2mod_futuretech | FORMULA | 30000 | 70 | 5806 | 200 | live resolved YAML |
| ra1_soviets_ak47conscript | redalert_soviets | FORMULA | 44000 | 71 | 4822 | 200 | live resolved YAML |
| ra2_allies_gi | redalert2_allies | REF | 50000 | 50 | 5500 | 200 | live resolved YAML |
| forgotten_mutantsoldier | tiberiansun_forgotten | FORMULA | 40000 | 60 | 5000 | 250 | live resolved YAML |
| forgotten_mutantsoldier_sp | tiberiansun_forgotten | FORMULA | 40000 | 60 | 5000 | 250 | excluded from fit (buildable=False and no explicit balance_include) |
| tkm_marine | redalert2mod_tkm | FORMULA | 20000 | 60 | 5385 | 300 | live resolved YAML |
| zerg_spithid | starcraft_zerg | FORMULA | 40000 | 110 | 3855 | 300 | live resolved YAML |
| naxis_conehead2 | redalert2mod_naxis | FORMULA | 40000 | 90 | 5222 | 500 | excluded from fit (buildable=False and no explicit balance_include) |
| naxis_coneheadsknights | redalert2mod_naxis | FORMULA | 20000 | 90 | 1555 | 1000 | live resolved YAML |

Classified ledger rows excluded by fitting eligibility: 6.

## 5. Reference consensus

Read-only R4 sensitivity through reference_targets.target_for's with-Cameo result; n counts external sources, plus Cameo's additional equal vote. Source families keep one vote each. Hero actors use their separate frozen hero-only population; they never enter ordinary distributions. Raw cross-game stats are not averaged. These numbers do NOT replace the candidate or constitute calibration.

| actor | exact source IDs used | HP target | speed target | range target | cost target | nominal damage/tick | issues |
|---|---|--:|--:|--:|--:|--:|---|
| ra2_allies_gi | CnC Reloaded/E1; Mental Omega/E1; RA2 0XX/GGI; RA2 Reborn/E1; Red Resurrection/E1; Romanov's Vengeance/e1; Valiant Shades/e1 | 27648.9 (n=7) | 54.2708 (n=7) | 4435.16 (n=7) | 205.346 (n=7) | 360.57 (n=7) | unapproved |
| ra2_soviets_conscript | CnC Reloaded/E2; Mental Omega/E2; RA2 0XX/E2; Red Resurrection/E2; Romanov's Vengeance/e2; Valiant Shades/e2 | 24105.5 (n=6) | 57.3566 (n=6) | 4251.78 (n=6) | 108.488 (n=6) | 243.662 (n=6) | unapproved |
| naxis_undead |  | unavailable (n=0) | unavailable (n=0) | unavailable (n=0) | unavailable (n=0) | unavailable (n=0) | absent from ordinary reference population; hero/eligibility lane requires review |
| ra1_soviets_rifleinfantry | Combined Arms/E1; DTA Enhanced/E1S; OpenRA Red Alert/E1 | 21062.5 (n=3) | 55.4073 (n=3) | 4610.9 (n=3) | 138.266 (n=3) | 188.688 (n=3) | unapproved |
| ra1_allies_rifleinfantry | Combined Arms/E1; DTA Enhanced/E1A; OpenRA Red Alert/E1 | 19882.9 (n=3) | 55.662 (n=3) | 4803.9 (n=3) | 138.266 (n=3) | 190.294 (n=3) | unapproved |
| td_gdi_minigunner | Combined Arms/N1; DTA Enhanced/E1; OpenRA Tiberian Dawn/E1 | 22375.9 (n=3) | 58.3928 (n=3) | 4417.43 (n=3) | 132.348 (n=3) | 251.288 (n=3) | unapproved |
| td_nod_minigunner | Combined Arms/N1; DTA Enhanced/E1; OpenRA Tiberian Dawn/E1 | 22193.3 (n=3) | 59.0759 (n=3) | 4226.69 (n=3) | 132.348 (n=3) | 254.588 (n=3) | unapproved |
| forgotten_mutant | Shattered Paradise/SEER; Twisted Insurrection/MUTANT | 29285.9 (n=2) | 61.9789 (n=2) | 5484.1 (n=2) | 463.39 (n=2) | 413.562 (n=2) | unapproved |
| ts_gdi_lightinfantry | OpenRA Tiberian Sun/E1; Twisted Insurrection/E1 | 20134.4 (n=2) | 66.3773 (n=2) | 4081.9 (n=1) | 136.655 (n=2) | 259.728 (n=1) | unapproved |
| ts_nod_lightinfantry | OpenRA Tiberian Sun/E1 | 20464 (n=1) | 66.0925 (n=1) | unavailable (n=0) | 136.229 (n=1) | unavailable (n=0) | unapproved |

## 6. Disagreements and gates

Anchor versus ruled spec (anchor actor only; the ruled spec is NOT applied to the verifier or to members):

| axis | anchor live | ruled spec | signed gap | gap % |
|---|--:|--:|--:|--:|
| hp | 20000 | 20000 | +0 | +0.0% |
| speed | 60 | 60 | +0 | +0.0% |
| range_wdist | 5000 | 5000 | +0 | +0.0% |
| cost | 100 | 100 | +0 | +0.0% |

Live resolved YAML versus the diagnostic candidate (unchanged, ledger-based):

| actor / axis | ledger | resolved YAML | candidate | live / candidate gap |
|---|--:|--:|--:|--:|
| naxis_naxiriflesoldier / hp | 20000 | 20000 | 31000 | -35.5% |
| naxis_naxiriflesoldier / speed | 60 | 60 | 59 | +1.7% |
| naxis_naxiriflesoldier / range_wdist | 5000 | 5000 | 5080 | -1.6% |
| naxis_naxiriflesoldier / cost | 100 | 100 | 100 | +0.0% |
| forgotten_mutantsoldier / hp | 40000 | 40000 | 31000 | +29.0% |
| forgotten_mutantsoldier / speed | 60 | 60 | 59 | +1.7% |
| forgotten_mutantsoldier / range_wdist | 5000 | 5000 | 5080 | -1.6% |
| forgotten_mutantsoldier / cost | 250 | 250 | 100 | +150.0% |

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
