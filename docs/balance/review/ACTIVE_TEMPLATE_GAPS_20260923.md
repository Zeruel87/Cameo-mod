# Static faction-roster candidates without a balance role template — 2026-09-23

Read-only triage on `master` at `d81a1bfdea2960d14314405588ea4c741fa718bd`.
This note makes no class, anchor, or gameplay decision. PRs #424, #428, #437,
#439, and #440 were open when measured; rerun after their relevant changes land.

## Method and scope

- Followed the active `mods/cameo/mod.yaml` includes through
  `tools/audit/cameo_model.py::Model` and its prerequisite-closure
  `buildable_roster` for 31 selectable, non-meta factions.
- Kept distinct actor IDs classified by `Model.unit_type` as infantry, vehicle,
  aircraft, or naval. Derived the nearest active role template with
  `tools/balance/extract_stats.py::actor_subtype`, then applied
  `tools/balance/class_membership.py::classify` without ledger hand tags.
- `buildable_roster` includes actors obtained from starting units and powers,
  not only actors directly enabled in a production queue. Of the 52 template
  gaps, 50 have prerequisites satisfied in at least one faction's static
  closure; `atreides_fremen` and `ordos_saboteur` enter the candidate set by
  another route. Five entries have no Health value. None of these checks is an
  in-game menu test. Counts are distinct actors, not faction-actor combinations.

Result: **865** distinct roster candidate actor IDs: **657** map from a role template to
an existing class, **156** have a recognized subtype without a class mapping,
and **52** have no recognized role template. The 52 split into 13 infantry,
29 vehicles, and 10 aircraft. This is a narrower active-roster denominator than
the 155 template-less rows in the full balance ledgers, which use a different
denominator and can include non-buildable and dormant variants.

## Provisional triage of the 52

These buckets identify the review needed, not the pricing outcome. Do not add
combat templates or Formula V2 prices to every row automatically.

| Review bucket | Count | Actor IDs |
|---|---:|---|
| Technical or structure-like entries | 5 | `camera.gpssat`, `concreteabuilding`, `concreteadefense`, `concretebbuilding`, `concretebdefense` |
| Deployable building cores | 9 | `japan_coreairfield`, `japan_corebarracks`, `japan_corepowerplant`, `japan_coreradar`, `japan_corerefinery`, `japan_coreservicedepot`, `japan_coretechcenter`, `japan_corewarfactory`, `plymouth_convec_structure_factory` |
| One-HP impulse items | 3 | `eden_impulseitems`, `eden_impulseitems_2`, `eden_impulseitems_3` |
| Engineers and capture specialists | 11 | `asianalliance_engineer`, `e6`, `engineer`, `futuretech_engineer`, `latinsyndicate_engineer`, `ra1_engineer`, `ra2_allies_engineer`, `ra2_soviets_engineer`, `steelconsortium_engineer`, `tkm_engineer`, `yuri_engineer` |
| Transports and carryalls | 9 | `atreides_advancedcarryall`, `atreides_apc`, `carryall`, `corrino_apc`, `forgotten_carryall`, `harkonnen_advancedcarryall`, `harkonnen_carryall`, `ordos_advancedcarryall`, `ts_gdi_carryall` |
| Utility or economy vehicles | 6 | `asianalliance_oiltruck`, `ra1_allies_mobilegapgenerator`, `ra1_allies_mobileradarjammer`, `ts_gdi_mobilesensorarray`, `ts_nod_mobilerepairvehicle`, `ts_nod_mobilestealthgenerator` |
| Combat or special-attack candidates | 9 | `atreides_fremen`, `atreides_ornithopter`, `devastator`, `harkonnen_devastatormech`, `harkonnen_gunship`, `latinsyndicate_demolitiontruck`, `ordos_saboteur`, `ra1_soviets_nukedemotruck`, `tsprobe` |

## Next disposition

1. Exclude technical/structure-like rows from the combat-unit denominator when
   their actual use confirms they are not purchasable field units. Check the
   three impulse items separately; they have one HP and an Infantry queue but
   are not ordinary infantry.
2. Route engineers, transports, building cores, and utility actors to their
   existing support, cargo, economy, or ability-pricing rules as appropriate.
   A role template may still be useful for data consistency, but should not
   silently force the combat cost formula onto them.
3. Review the nine combat/special candidates actor by actor. Determine whether
   each inherits an existing role, needs a distinct class, or is an explicit
   exception. Treat suicide and power-spawned units as special cases.

This file is separate from PR #428's air/naval/economy class proposal and PR
#437's generated ledgers. Those PRs neither classify these 52 candidates nor
approve their prices.
