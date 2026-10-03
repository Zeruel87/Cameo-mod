# Promotion and cargo implementation batch

This defines the exact GP-05 content scope. It does not apply the batch before
the dependent infantry and unit prices are reviewed.

## Promotion buff removal set

Remove the direct `Inherits@PromotionUnitBuff: ^PromotionUnitBuff` line from
these 40 promotion-token consumers only:

- RA Allies: `ra1_allies_alliedtankdestroyer`,
  `ra1_allies_alliedtigerheavytank`, `ra1_allies_chronotank`,
  `ra1_allies_machinegunner`, `ra1_allies_phasetransport`,
  `ra1_allies_rapierjumpjet`, `ra1_allies_reconranger`,
  `ra1_allies_sheridanassaulttank`.
- RA Soviets: `ra1_soviets_cyberdog`, `ra1_soviets_gatlingtank`,
  `ra1_soviets_monstertank`, `ra1_soviets_mortarsoldier`,
  `ra1_soviets_supersonicnuclearbomber`, `ra1_soviets_volkov`.
- TD GDI: `td_gdi_assaultapc`, `td_gdi_defenserig`,
  `td_gdi_empgrenadier`, `td_gdi_exosuit`, `td_gdi_firehawk`,
  `td_gdi_havoc`, `td_gdi_heavysniper`, `td_gdi_humveemkii`,
  `td_gdi_mammothtankmkiii`, `td_gdi_officer`, `td_gdi_predatortank`,
  `td_gdi_shotgunner`, `td_gdi_sonicmissilesoldier`.
- TD Nod: `td_nod_blackhandflamer`, `td_nod_buggymkii`,
  `td_nod_chemicalattackbike`, `td_nod_chemicalrocketsoldier`,
  `td_nod_chemicalssmlauncher`, `td_nod_chemicalstealthtank`,
  `td_nod_flametankmkii`, `td_nod_lasercommando`,
  `td_nod_lasertrooper`, `td_nod_lighttankmkii`,
  `td_nod_specterartillery`, `td_nod_stealthsoldier`, `td_nod_venom`.

Do not remove the same inherit from these nine non-promotion-token actors:
`ra1_allies_alliedcybertank`, `ra1_soviets_armoredyak`,
`ra1_soviets_commissar`, `ra1_soviets_hammertank`,
`ra1_soviets_heatraytank`, `ra1_soviets_heavyteslatank`,
`ra1_soviets_kotinnucleartank`, `ra1_soviets_nuclearyak` and
`ra1_soviets_teslayak`. They are disabled or upgrade-unlocked units and need a
separate balance decision.

These seven promotion-token consumers have no direct buff inherit and require
no removal: `ra1_allies_bastionartillerybunker`,
`ra1_allies_camopillbox`, `ra1_allies_gapgenerator`,
`ra1_allies_mobilegapgenerator`, `ra1_allies_mobileradarjammer`,
`ra1_allies_reinforcementpad` and `td_nod_stealthharvester`.

## Virtual prerequisite cost

- `TierChain.promotion_pricing_context` now implements this breakdown as a
  non-live helper. It is not yet used by extraction or writeback.
- Use the accepted value `1500 * authored promotion-column depth`.
- Add it once to the pricing-only prerequisite-chain input before
  `formula.tier_multiplier`; do not alter real building costs, build
  prerequisites or the promotion purchase price.
- Preserve the current `C <= B` plateau. Do not change `B` or `S` to force a
  discount.
- Store actual chain cost, virtual promotion cost, pricing chain cost and the
  resulting multiplier separately in the derived evidence.
- Multiple or unresolved promotion tokens fail closed instead of receiving a
  guessed tier. The 2000-per-tier value remains sensitivity evidence only.

The removal and the new pricing input must land in the same guarded content
batch. Removing the buff first would weaken 40 units without the accepted
price compensation.

## Cargo dependency

Apply passenger costs first, then recompute every existing or proposed loaded
transport from the final passenger prices on the 10-credit grid. Preserve:

- no initial naval load and no loaded-price valuation for the two naval
  transports;
- one of each available faction infantry for air transports, including
  promotion infantry;
- varied early-to-late loads for advanced armed transports;
- passenger-weight validation against `Cargo.MaxWeight`;
- armed-carrier `K = 1.25` as a combat budget term, not a purchase-price
  surcharge.

The existing corrected costs stay in place. The later load proposal remains
unapplied until the dependent infantry prices are settled.

## Completion gate

Apply only after GP-04 identifies the final price for every affected passenger
and promotion unit. Then run one guarded extraction/apply cycle, verify the
40-line removal set, confirm no non-promotion inherit changed, check derived
tier breakdowns, and validate every loaded transport once. Runtime playtest
remains GP-07.

The corrected helper rejects nonfinite/negative inputs, unknown promotion
tokens, cycles and unresolved promotion parents. Focused helper checks pass
8/8. An active-rules integration probe resolves all
47 promotion consumers with the expected tier distribution 10/11/11/15 for
tiers 1/2/3/4 and adds the virtual cost exactly once.
