# `rocket_trooper` — NOT READY / UNAPPROVED

> Reviewed pilot snapshot from 9 September 2026, retained with its coordinator notes. The input/code hashes below identify its original evidence; it is not regenerated output from the latest generator. Later generator improvements add selected-faction and per-axis contributors and clearer signed-gap labels. Generate a fresh comparison into an external directory rather than overwriting this annotated snapshot. No calibration or sign-off is implied.

Diagnostic only: current ledger medians are not approved reference-consensus targets.
Faction approval/calibration, weapon structure and maintainer sign-off remain required.

## 1. The proposal

| axis | diagnostic candidate | ruled spec | evidence count | full-class percentile | basis |
|---|--:|--:|--:|--:|---|
| hp0 | 10000 | 10000 | 4 | 6.97674 | reference-backed ledger medians, snapped to step 1000 |
| speed0 | 53 | 55 | 4 | 44.186 | reference-backed ledger medians, snapped to step 1 |
| range0_wdist | 6370 | 6500 | 4 | 51.1628 | reference-backed ledger medians, snapped to step 10 |
| cost0 | 300 | 300 | 4 | 27.907 | reference-backed ledger medians, snapped to step 100 |

Status: UNAPPROVED; BIASED hp — do not sign; NO MODEL — calibrated damage/reload not supplied

## 2. DPS is deferred

No DPS target is proposed while W24 moves. No synthetic damage/reload is assumed; there is no combat verifier or fit command to approve from this dossier.

## 3. Anchor and verifier actors

| role / actor | source | HP | speed | ground-domain range | cost |
|---|---|--:|--:|--:|--:|
| anchor: ra1_allies_alliedrocketsoldier | ledger | 10000 | 55 | 6643 | 300 |
| anchor: ra1_allies_alliedrocketsoldier | live | 10000 | 55 | 6643 | 300 |
| verifier: cabal_rocketcyborg | ledger | 45000 | 40 | 8753 | 650 |
| verifier: cabal_rocketcyborg | live | 45000 | 40 | 8753 | 650 |

Verifier / anchor ratios (HP, speed, range, cost): 4.5 / 0.727273 / 1.31763 / 2.16667

| role | ledger nominal DPS/tick | measured tier factor | derived aggregate K | K fallbacks |
|---|--:|--:|--:|--:|
| anchor | 242 | 1 | 0.62685 | 0 |
| verifier | 320.294 | 1 | 0.419031 | 0 |

Shared TechTier: equal.

Shared aggregate K: DIFFERENT — verifier identity not applicable.

The 2x HP / 2x DPS / 2.5x cost identity is NOT established by stat ratios alone. K is a derived aggregate, not a measured matchup result; any missing sidecar is unavailable. The synthetic verifier remains withheld.

## 4. Membership

Every classified member with its LIVE resolved-YAML stats as it ships today, sorted by live cost, unavailable last. The ledger-based diagnostic candidate in section 1 is NOT recalculated from these rows. REF means STRONG/FAIR assignment, not an approved faction or a completed consensus. FORMULA means no accepted assignment. Rows marked excluded fail fitting eligibility (buildable=False and no explicit balance_include); they are displayed but never added to the candidate calculation. Unresolved members stay unavailable with their issue, never a fallback labeled live.

| actor | faction | evidence | HP | speed | range | cost | basis |
|---|---|---|--:|--:|--:|--:|---|
| steelconsortium_clonetrooper | redalert2mod_consortium | FORMULA | 17000 | 57 | 6463 | 143 | live resolved YAML |
| atreides_rockettrooper | d2k_atreides | FORMULA | 40000 | 42 | 6185 | 200 | live resolved YAML |
| corrino_trooper | d2k_corrino | FORMULA | 40000 | 42 | 6185 | 200 | live resolved YAML |
| harkonnen_rockettrooper | d2k_harkonnen | FORMULA | 40000 | 42 | 6185 | 200 | live resolved YAML |
| tkm_rocketeer | redalert2mod_tkm | FORMULA | 9000 | 60 | 6214 | 200 | live resolved YAML |
| yuri_initiate | redalert2_yuri | REF | 24000 | 66 | 4440 | 200 | live resolved YAML |
| latinsyndicate_tankkiller | redalert2mod_syndicate | FORMULA | 13000 | 53 | 6666 | 270 | live resolved YAML |
| E3 | tiberiandawn_gdi | FORMULA | 9000 | 50 | 6368 | 300 | excluded from fit (buildable=False and no explicit balance_include) |
| asianalliance_asiantankkiller | redalert2mod_asianalliance | REF | 17000 | 51 | 6460 | 300 | live resolved YAML |
| forgotten_rocketinfantry | tiberiansun_forgotten | FORMULA | 12000 | 50 | 6694 | 300 | live resolved YAML |
| ixian_rockettrooper | d2k_ixian | FORMULA | 12000 | 48 | 6185 | 300 | live resolved YAML |
| ordos_rockettrooper | d2k_ordos | FORMULA | 12000 | 48 | 6185 | 300 | live resolved YAML |
| ra1_allies_alliedrocketsoldier | shared_redalert | REF | 10000 | 55 | 6643 | 300 | live resolved YAML |
| ra1_soviets_rocketsoldier | redalert_soviets | REF | 10000 | 55 | 6643 | 300 | live resolved YAML |
| ra2sidewind | shared_redalert2 | FORMULA | 15000 | 45 | 6567 | 300 | excluded from fit (buildable=False and no explicit balance_include) |
| td_gdi_rocketsoldier | tiberiandawn_gdi | REF | 9000 | 50 | 6368 | 300 | live resolved YAML |
| td_nod_rocketsoldier | tiberiandawn_nod | REF | 9000 | 50 | 6368 | 300 | live resolved YAML |
| trooper | shared_d2k | FORMULA | 12000 | 48 | 6185 | 300 | live resolved YAML |
| ts_nod_rocketinfantry | tiberiansun_nod | REF | 12000 | 50 | 6694 | 300 | live resolved YAML |
| schwarzermond_lunarrocket | redalert2mod_schwarzermond | FORMULA | 18000 | 60 | 6055 | 350 | live resolved YAML |
| futuretech_javelinsoldier | redalert2mod_futuretech | FORMULA | 25000 | 50 | 6000 | 400 | live resolved YAML |
| ra1_soviets_firerocketsoldier | redalert_soviets | FORMULA | 16000 | 48 | 6036 | 400 | live resolved YAML |
| ra2_allies_guardiangi | redalert2_allies | REF | 45000 | 45 | 4762 | 400 | live resolved YAML |
| td_nod_chemicalrocketsoldier | tiberiandawn_nod | REF | 18000 | 60 | 6006 | 400 | live resolved YAML |
| ordos_antiairtrooper | d2k_ordos | FORMULA | 15000 | 45 | 6252 | 450 | live resolved YAML |
| harkonnen_sardaukar | d2k_harkonnen | REF | 120000 | 56 | 6185 | 500 | live resolved YAML |
| wc2_orcs_trollaxethrower | warcraft2_orcs | FORMULA | 30000 | 60 | 6445 | 500 | live resolved YAML |
| wc2_orcs_trollberserker | warcraft2_orcs | FORMULA | 30000 | 60 | 6445 | 500 | live resolved YAML |
| corrino_sardaukar_bazooka | d2k_corrino | FORMULA | 120000 | 56 | 6185 | 600 | live resolved YAML |
| corrino_sardaukar_javelin | d2k_corrino | FORMULA | 120000 | 56 | 5120 | 600 | live resolved YAML |
| corrino_sardaukar_laser | d2k_corrino | FORMULA | 120000 | 56 | 5120 | 600 | live resolved YAML |
| ixian_twinrockettrooper | d2k_ixian | FORMULA | 24000 | 48 | 6502 | 600 | live resolved YAML |
| wc2_humans_elvenranger | warcraft2_humans | FORMULA | 25000 | 75 | 6973 | 600 | live resolved YAML |
| cabal_rocketcyborg | tiberiansun_cabal | REF | 45000 | 40 | 8753 | 650 | live resolved YAML |
| terran_marine | starcraft_terran | FORMULA | 41000 | 61 | 6105 | 689 | live resolved YAML |
| futuretech_missiledroid | redalert2mod_futuretech | FORMULA | 67500 | 40 | 8000 | 700 | live resolved YAML |
| cabal_ascended | tiberiansun_cabal | REF | 70000 | 40 | 9000 | 900 | live resolved YAML |
| wc2_orcs_kodobeast | warcraft2_orcs | FORMULA | 125000 | 60 | 6445 | 1000 | live resolved YAML |
| wc2_orcs_trollheadhunter | warcraft2_orcs | FORMULA | 40000 | 75 | 7711 | 1000 | live resolved YAML |
| terran_madcap | starcraft_terran | FORMULA | 60000 | 60 | 5542 | 1003 | live resolved YAML |
| wc2_humans_alleria | warcraft2_humans | FORMULA | 50000 | 100 | 7487 | 2500 | live resolved YAML |
| wc2_orcs_zuljin | warcraft2_orcs | FORMULA | 50000 | 100 | 7711 | 2500 | live resolved YAML |
| zerg_hydralisk | starcraft_zerg | FORMULA | 80000 | 76 | 5979 | 3314 | live resolved YAML |
| wc2_humans_alleria_elite | warcraft2_humans | FORMULA | 75000 | 100 | 7487 | 4500 | live resolved YAML |
| wc2_orcs_zuljin_elite | warcraft2_orcs | FORMULA | 75000 | 100 | 7711 | 4500 | live resolved YAML |

Classified ledger rows excluded by fitting eligibility: 2.

## 5. Reference consensus

Read-only R4 sensitivity through reference_targets.target_for's with-Cameo result; n counts external sources, plus Cameo's additional equal vote. Source families keep one vote each. Raw cross-game stats are not averaged. These numbers do NOT replace the candidate or constitute calibration.

| actor | exact source IDs used | HP target | speed target | range target | cost target | issues |
|---|---|--:|--:|--:|--:|---|
| harkonnen_sardaukar | OpenRA Dune 2000/mpsardaukar; OpenRA Dune II/sardaukar | 119164 (n=2) | 46.777 (n=2) | 5597.74 (n=2) | 518.385 (n=2) | unapproved |
| ra2_allies_guardiangi | CnC Reloaded/GGI; Mental Omega/GGI; RA2 Reborn/GGI; Red Resurrection/GGI; Romanov's Vengeance/ggi; Valiant Shades/ggi | 26404.6 (n=6) | 49.3609 (n=6) | 4527.09 (n=6) | 379.103 (n=6) | unapproved |
| yuri_initiate | CnC Reloaded/INIT; Combined Arms/SAB; Mental Omega/INIT; RA2 0XX/INIT; RA2 Reborn/INIT; Red Resurrection/INIT | 22195.9 (n=6) | 55.9111 (n=6) | 4242.85 (n=6) | 226.014 (n=6) | unapproved |
| asianalliance_asiantankkiller | Rise of the East/THUND | 19495.3 (n=1) | 59.5064 (n=1) | 6109.35 (n=1) | 380.722 (n=1) | unapproved |
| ra1_soviets_rocketsoldier | Combined Arms/E3; DTA Enhanced/E3S; OpenRA Red Alert/E3 | 13698 (n=3) | 50.2715 (n=3) | 7157.2 (n=3) | 430.449 (n=3) | unapproved |
| ra1_allies_alliedrocketsoldier | Combined Arms/E3; DTA Enhanced/E3A; OpenRA Red Alert/E3 | 13698 (n=3) | 50.2715 (n=3) | 7157.2 (n=3) | 430.449 (n=3) | unapproved |
| td_gdi_rocketsoldier | Combined Arms/N3; DTA Enhanced/E3; OpenRA Tiberian Dawn/E3 | 13906.3 (n=3) | 45.2703 (n=3) | 6569.48 (n=3) | 399.798 (n=3) | unapproved |
| td_nod_chemicalrocketsoldier | Combined Arms/N3C | 24938 (n=1) | 54.5121 (n=1) | 6611 (n=1) | 457.511 (n=1) | unapproved |
| td_nod_rocketsoldier | Combined Arms/N3; DTA Enhanced/E3N; OpenRA Tiberian Dawn/E3 | 13906.3 (n=3) | 45.2703 (n=3) | 6569.48 (n=3) | 399.798 (n=3) | unapproved |
| cabal_ascended | CnC Reloaded/ASCENDED | 55431.7 (n=1) | 47.9259 (n=1) | 7020.05 (n=1) | 621.596 (n=1) | unapproved |
| cabal_rocketcyborg | CnC Reloaded/ROBOTTSCYBORG | 58015.2 (n=1) | 47.9259 (n=1) | 6051.27 (n=1) | 651.148 (n=1) | unapproved |
| ts_nod_rocketinfantry | CnC Reloaded/TSE3; Crystallized Nexus/E3; OpenRA Tiberian Sun/E3 | 16727.4 (n=3) | 52.6235 (n=3) | 5938.69 (n=3) | 330.41 (n=3) | unapproved |
| wc2_humans_alleria |  | unavailable (n=0) | unavailable (n=0) | unavailable (n=0) | unavailable (n=0) | absent from ordinary reference population; hero/eligibility lane requires review |
| wc2_humans_alleria_elite |  | unavailable (n=0) | unavailable (n=0) | unavailable (n=0) | unavailable (n=0) | absent from ordinary reference population; hero/eligibility lane requires review |
| wc2_orcs_zuljin |  | unavailable (n=0) | unavailable (n=0) | unavailable (n=0) | unavailable (n=0) | absent from ordinary reference population; hero/eligibility lane requires review |
| wc2_orcs_zuljin_elite |  | unavailable (n=0) | unavailable (n=0) | unavailable (n=0) | unavailable (n=0) | absent from ordinary reference population; hero/eligibility lane requires review |

## 6. Disagreements and gates

Anchor versus ruled spec (anchor actor only; the ruled spec is NOT applied to the verifier or to members):

| axis | anchor live | ruled spec | abs gap | gap % |
|---|--:|--:|--:|--:|
| hp | 10000 | 10000 | +0 | +0.0% |
| speed | 55 | 55 | +0 | +0.0% |
| range_wdist | 6643 | 6500 | +143 | +2.2% |
| cost | 300 | 300 | +0 | +0.0% |

Live resolved YAML versus the diagnostic candidate (unchanged, ledger-based):

| actor / axis | ledger | resolved YAML | candidate | live / candidate gap |
|---|--:|--:|--:|--:|
| ra1_allies_alliedrocketsoldier / hp | 10000 | 10000 | 10000 | +0.0% |
| ra1_allies_alliedrocketsoldier / speed | 55 | 55 | 53 | +3.8% |
| ra1_allies_alliedrocketsoldier / range_wdist | 6643 | 6643 | 6370 | +4.3% |
| ra1_allies_alliedrocketsoldier / cost | 300 | 300 | 300 | +0.0% |
| cabal_rocketcyborg / hp | 45000 | 45000 | 10000 | +350.0% |
| cabal_rocketcyborg / speed | 40 | 40 | 53 | -24.5% |
| cabal_rocketcyborg / range_wdist | 8753 | 8753 | 6370 | +37.4% |
| cabal_rocketcyborg / cost | 650 | 650 | 300 | +116.7% |

Ledger versus live discrepancies for classified members (absolute and percentage gaps; the percentage needs a finite positive ledger baseline; differing or unavailable axes only):

| actor / axis | ledger | live | abs gap | gap % |
|---|--:|--:|--:|--:|

W24: 3 class members with stacked mains (raw, no exemptions).
- `ixian_twinrockettrooper` / `D2K_Rocket_Trooper1`: 3 mains
- `tkm_rocketeer` / `tkmfirerockets`: 2 mains
- `cabal_ascended` / `CabalAscendedRockets`: 2 mains

A zero stacked-main count is not full weapon clearance. Pending class migrations are not silently applied; an empty class stays NO SOURCE. Limited actors need hero-lane evidence, not admission into ordinary distributions.

**Coordinator pilot judgement — not sign-off.** Keep the entry-anchor nomination (`ra1_allies_alliedrocketsoldier`) pending weapon/reference review; the low full-class HP percentile (6.98) alone is not a reason to raise HP or move the class anchor (C9). The raw range gap (6643 live versus ruled 6500, +143) remains visible. The current verifier differs from the 2x / 2x / 2.5x template — HP 4.5x, nominal DPS 320.294 / 242 (~1.324x), cost 650 / 300 (~2.167x), with different speed, range and derived K — so no verifier restat is proposed while W24 raw debt 3 stands. The diagnostic medians are not approved targets. Keeping the nomination is neither approval nor permission to apply prices.

## 7. What would make this wrong

These candidates are wrong if the selected current-stat pool is unrepresentative, its reference assignments are rejected, its ledger differs from resolved YAML, or the low full-class HP percentile alone is used to raise HP or move the class anchor (C9); approval and calibration must resolve those questions before any number is applied.

Evidence hashes (inputs, not approval):

```json
{
  "active_yaml_files": 398,
  "active_yaml_sha256": "53fc196bc1142b9fcc7d048de651ac42e701411a935a32ebe8be586d35d5bd48",
  "assignment_sha256": "f05ba67f35445c83982cd7d4fa3edfa230562371621927e77efe928a4730fcfb",
  "code_sha256": {
    "tools/audit/audit_three_way_split.py": "42381d12a85ea1045ce0807f6199853228397e374d971f59c5a9a345cf630254",
    "tools/audit/miniyaml.py": "4b11e4e54c5630a4474f5284096dff5286de37248f857a0b07b2860925bb8010",
    "tools/balance/anchor_readiness.py": "858f4c38c74e2cbfa022e7cd81923ad267673ce96c7eee3d2c9b57f8fb08de0f",
    "tools/balance/class_membership.py": "d1009482032368278faf246ed4808ae9755a50d34d75b8d8d3b8e3ce74542dba",
    "tools/balance/derive_virtual_anchor.py": "6552c109dfbe2a1377ba7e624de91ebb0bd03ff0ea58abbb5864546b1b7f11d9",
    "tools/balance/diagnostic_output.py": "98678adc2e9a2756ddcdb671b4319981f64487a561982b87e0b7030e6bf29f8f",
    "tools/balance/extract_stats.py": "d853ac01928a02b9deff265cc6e8763328b47a4c9fa773f6a9091a0a51419d00",
    "tools/balance/faction_routes.py": "8d7ef545961c416bb201019e560b4a94077aa5652366b231ce6fea8df0d851d1",
    "tools/balance/firepower.py": "85718bd8f72b0226cc3997e12c6450fa9ce269e63a7095e9bf5021506110e604",
    "tools/balance/fit_class.py": "9c8952f0a63ff706bf1b9263ca75412646fb6a96150b0d36260c3aae4a784419",
    "tools/balance/formula.py": "0e705b53a239719d64a614628bf3760e2d3fb6eafbe362b6dd17f62f38e6c3d2",
    "tools/balance/propose_anchor_spec.py": "b33febd31dec75488d2cbd2addbbcc92cb7c23d9109e5b15cc8d3181355d3ee3",
    "tools/balance/reference_distribution.py": "1c695f5a41cead8064e4c715ccd955a4daf05832dba87b9a5f8953be0b7a9959",
    "tools/balance/reference_lineages.py": "dbc14d5f84909becaadee3be6b30f5ed84d9364d844b9bd063325ae07a59bf62",
    "tools/balance/reference_targets.py": "d14181d9103304e7b4fffb3743c14ce47cf7dde0db18f1f6fc85b7f0f084f865",
    "tools/balance/synthesize_reference.py": "f09d822fcd40474b54f86a0c9f719ac8bbf49de0af1934f4cb7fa467d678841c",
    "tools/balance/tier_chain.py": "bf5cd376e7bad3857d4c61646600709e784a6141f8a7f5769977115dcaa4f888"
  },
  "ledger_sha256": {
    "class_anchors.json": "192a55c76658266afbcd50a60f3fbaad0942e5d2dc3012abb78c94a4e3cf3ae5",
    "d2k_atreides.json": "70c6356ad2e2d6fcab814a012f24941c8a0c4158ad9f05a806f29e02150b24d2",
    "d2k_corrino.json": "0d082324939c24a51e1a819d10d68732b21f792dd2efc059914821a3445e1b9d",
    "d2k_harkonnen.json": "ff8fe6b14b46609e379ec19b44974300c128b9a10f6d850b8bf826a3db2b0cbe",
    "d2k_ixian.json": "4ab1b0670c251d3de78471873beb83837c9e65db548ba7f3d4b0e4e06c27103b",
    "d2k_ordos.json": "58ac4ad9dcf0a24426faca1b881403c16695b1b7ad66a25ce6cb25abc286ea4a",
    "redalert2_allies.json": "71993248467cd952a964f59ebbc961c2642b8f8a6638842ad36df038c944a663",
    "redalert2_soviets.json": "e0a26f2c481639840239fc1b9dd80792668096e2d8f339e052a72a60b349db53",
    "redalert2_yuri.json": "8bfc152528365192c25edb27d9cd00dc654c8a2aaeb609789b2beeceb0034f36",
    "redalert2mod_asianalliance.json": "1ab4b716daab0b7774bce108b046bfd598868a60a21d3b863861232621a7ed66",
    "redalert2mod_consortium.json": "8199dad7553e3c7034b9095dadc6a4d746216ca1e8bd0c45d824642a4b7a3b19",
    "redalert2mod_futuretech.json": "343d07e60d83ce19db82a48aaeabc4ac6650071abee9280c48a48af0d6276f9a",
    "redalert2mod_naxis.json": "4db6704ce6180504d667cbfd420be62c002f6ecdd605f61e7f709777e2971ae9",
    "redalert2mod_schwarzermond.json": "334daa5706528b4718ed3745a284a5304fef8d2b5eb6b3f447af1a76f0e1b76e",
    "redalert2mod_syndicate.json": "965bb02d5906bce7c6193f181f80fc6703a47f6744bab655035d3b93caede136",
    "redalert2mod_tkm.json": "df6698481cef433ea4404c1019d03fefd04dd9a272dbb9775620f2950f735042",
    "redalert_allies.json": "03aac47fa2b81c4aa9a99f4862c40ff5d8891c1d149cd6d947bb3965bd368365",
    "redalert_japan.json": "6524ec2268d7634a58baabbbc96bac127153c1e1d6f8ec4b9201de22349eb298",
    "redalert_soviets.json": "9d110d112bce46c9a5e325ede14d1b9bea66e3eddebc85096dce3bef5149d9ea",
    "shared_d2k.json": "5ac45903a65b08bd2ee4f5a1f694dffdca1deeb0bbe915dfbd5844fe206cba6c",
    "shared_redalert.json": "31fe88ca6742ece62e198685ecdbf4938407b7d3154034e22aedb24a6a2d68eb",
    "shared_redalert2.json": "44e66f0de587fd2a7699edd157d64308eab1172aa37245e3548e73cbe102df10",
    "shared_tiberiandawn.json": "84f72db56a4a987fb22cd9e159ac60988697fa9b103c92e2e66692705a0c95b2",
    "starcraft_protoss.json": "699fc8056894d96854141aa16b330a638f4cd6846fc656da0979f31864d7c015",
    "starcraft_terran.json": "4b859c621b5b3a87b1bfec1aabfd482ff39e6841c1520c2695121a6615e30dd8",
    "starcraft_zerg.json": "678bb46e0d0011681d8dcce244cb701c54d48be50307189d79a3f417b2810e1b",
    "tiberiandawn_gdi.json": "c782e6a88aba46680f654e09113ee60cea0a0e40f58990aea4807fc10123fb76",
    "tiberiandawn_nod.json": "7cb0b1e91711526f78b5ccd004cf89879393437f2c22e6280bef73cfdd70bba1",
    "tiberiansun_cabal.json": "e605ed362b8c96dac0416fcfcec7643aa22fe07cb89800ebc1ab0df8ff4d3e13",
    "tiberiansun_forgotten.json": "02d452bd61fea4b9519c3cd175343b97eac7eedb4c837a3d12e32ddfae4c386a",
    "tiberiansun_gdi.json": "853695f77fb72d011480149ea90053d10164efd6702e3328915071ffe257e333",
    "tiberiansun_nod.json": "56fd0456bb91a89c0bbe8a99a9a4fb4c3dcb826fbd0820ba0caf0959355d270c",
    "warcraft2_humans.json": "4facd0c05fe4ab4f806593a998aaa1fda4481762f8c19b20729abdf4708a3732",
    "warcraft2_orcs.json": "94c97d6584bd8fd9ea7b659465e16291dd7c6d67496147e9099d1a1ee5c9e553"
  },
  "reference_input_sha256": {
    "docs/design/ORIGINAL_UNITS_PEER_OPENRA.md": "d37db59f883bbfd62b3faa555788f4ac79970eae675f273eb0b89f8b9c22e36c",
    "docs/design/ORIGINAL_UNITS_RAW.md": "7624e5567f674cdfc86c160fd029157b495f124bbc0ea8d10c8c4869d3a48523",
    "docs/reference/armor_normalized.json": "70f0aa2a71539c2b96889fe35a0ba23559db8dff4788791915281934a7d9e84b",
    "docs/reference/ini_corpus.json": "204391b21a95b3c5409b9d146a33f07b8b1404e5c4e0369976ab9859db1081b1"
  },
  "revision": "eb3cb60a3e6f2b872422c9c4df4145a16810e515",
  "sidecar_sha256": {
    "d2k_atreides.json": "0ae0fa7115b9ceecb0ee81fe079105677c8f6c20201d1809cf3a891915c6ed1a",
    "d2k_corrino.json": "dd5fe56fa5a3e401ef311e0de0ca096b7d3a15aa4c041a9877ae7497667c8e08",
    "d2k_harkonnen.json": "e2700508e84d82c80c7e20c71f2e922409ea9d2284427a127da826fb151b3a8a",
    "d2k_ixian.json": "0a8f3d87c90283432fc9b5e8bd41a4ceef8e4b34393117e24700afa59a7080d2",
    "d2k_ordos.json": "456b36e595b188dff22ace5689aa934e2d474991c44e366e8ab7cbba81095375",
    "redalert2_allies.json": "6677cb0d6264d57b56ff144f1182908f61d5036ac24eb7edb71fb6b9d12a1b91",
    "redalert2_soviets.json": "d6ab1d6c9f808d2cd085192982b580d36221e28542ccd86d2310750e95f02b14",
    "redalert2_yuri.json": "c5242d1b90d62721091af95dd487cd8c5b7d8f30f272f1f4d5e969faf2c4fd61",
    "redalert2mod_asianalliance.json": "9e97be1005c137772bffbae92fc9250a4bc5f58e50b92392ebcee5a917586deb",
    "redalert2mod_consortium.json": "a3fe4e2bcf143757c0cb5cb5f4d01c7ed15a938d1afa42a7fae21cb81361878b",
    "redalert2mod_futuretech.json": "3c7eb8ede69e126eb60915f3aca9192db5e013787fcaab85cab6b9486f76d716",
    "redalert2mod_naxis.json": "33b73ea6aa84b537f63a5ffcab0ec9a1d2d22c3b888a5338ab40dd72adaf39a2",
    "redalert2mod_schwarzermond.json": "37de347398b07d91a7399bea35b2ddf3836bbc07b11246ea01ca697f5d56787d",
    "redalert2mod_syndicate.json": "3ae052a52db08f39df727d41d67c88d3615494e7c91dd1d4d516e66edf228a94",
    "redalert2mod_tkm.json": "c3c22ef14251498b80e628395e5e1df10229ad199f72b9ea4ce0a81b2e8099e8",
    "redalert_allies.json": "6692a9287c2216baf03c84745e3709ba663b8667f47362112886e5df322ab627",
    "redalert_japan.json": "d4b1bfb194ae5a1cd1be575364333da6e68509c4ada00dbb40a665286826e9d8",
    "redalert_soviets.json": "13f4f995175efef31e2f0be75dec89d9d0ceab6e0539c2b826f961dc07f10295",
    "shared_d2k.json": "8a5602c4a7cabfc4a9e9481639bb2d7500d836564f5bd14b6becb67aef2f6795",
    "shared_redalert.json": "90a39f8280c2bfc6ce6c48c51b39dc958152638abf55852281b7c7b4a7e8c07d",
    "shared_redalert2.json": "64e67b4272c46d17f3880bc633171a2bb5ab6cd83dece85752b8013d279f77eb",
    "shared_tiberiandawn.json": "c14608cdb9dc319c3b8bcee9f8a679e65b350743568aff2cf9826cf0489b6a05",
    "starcraft_protoss.json": "35b49975976d819967c677d6d450ac98beaf8f9ab6b2c1a4c89f95666a24c1f5",
    "starcraft_terran.json": "df1d387e222fe3c2baa3e038647f689742453a856aea43498d5453af36d33feb",
    "starcraft_zerg.json": "cdf8f762fa4405887206316ca94c917337458304fa63fb3c353e0bff2be5481e",
    "tiberiandawn_gdi.json": "61809830693ef2178c89180748f5e6027bc2c90c1f20f81cc70fab013b7215aa",
    "tiberiandawn_nod.json": "6c00b2161116885e8c3801a82fb4b081acc7c242fe4aec4af17b872912145c46",
    "tiberiansun_cabal.json": "f45f9f9aa14172415f85c8c8b3123c39caa923ca7c9b56ddf0c5c19e00b10648",
    "tiberiansun_forgotten.json": "e3bb9cfcdd24f26044eaafd5466ee0a15cf8f08fe3fc516930b547b466d5fab8",
    "tiberiansun_gdi.json": "2ee11054e3b5912d6a8655ea819bc7469baf56d0d529636d77be07e700ebcd04",
    "tiberiansun_nod.json": "06702eda5947373f5c0d18f3f53c09f8b8a6e5fc0d9a8cef8d755513407d49a8",
    "warcraft2_humans.json": "27ab3b97783e05040830466d1dd538157743ad785a981f2178040d04f7bfd1a5",
    "warcraft2_orcs.json": "e389507fe42385b506921ab4ce3d9e3439a293489c5501f37bf7215220623a0e"
  }
}
```
