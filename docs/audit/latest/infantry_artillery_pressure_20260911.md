# Infantry versus artillery pressure receipt

**STATIC SCENARIO ONLY.** Each row is one explicit current-Cameo center-impact projection against a base infantry target. It is not a live TTK, DPS vote, balance recommendation or gameplay result.

## Summary

- Cases: **4**; resolved: **4**; unresolved: **0**.
- Projection: flat A plus max-HP fraction B at the target's ledger HP, shown for source axes None and Light.
- Center impact assumes 100% selected-record terms; falloff, scatter, cadence, armor changes, target movement and secondary payloads are excluded.

| faction | area weapon | infantry target | target HP | None total | None HP bars | Light total | Light HP bars |
|---|---|---|---:|---:|---:|---:|---:|
| RA Allies | `ra1_allies_alliedartillery_155mm` | `ra1_allies_rifleinfantry` | 27,000 | 40,821 | 1.51× | 34,029 | 1.26× |
| RA Soviets | `ra1_soviets_siegemammothtank_ra120mm2` | `ra1_soviets_rifleinfantry` | 34,000 | 59,442 | 1.75× | 58,857 | 1.73× |
| TD GDI | `td_gdi_archerartillery_archerartilleryshell` | `td_gdi_minigunner` | 31,000 | 95,844 | 3.09× | 79,617 | 2.57× |
| TD Nod | `td_nod_artillery_artilleryshell` | `td_nod_minigunner` | 30,000 | 49,232 | 1.64× | 41,136 | 1.37× |

## Interpretation boundary

A result above 1.00 target-HP bars means the selected arithmetic projection exceeds the target HP before capping. It does not prove a one-shot kill: impact position, armor routing, target eligibility, projectile timing, reload cadence, overlapping units and secondary effects are outside this receipt.

The receipt is evidence for a later infantry-survivability pilot. Possible cover, armor-layer, regeneration or piercing policies must be evaluated separately and approved before any gameplay change.
