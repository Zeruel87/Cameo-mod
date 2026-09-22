# Forgotten CannonAP continuous-profile follow-up

Status: implemented in the PR341 draft; not merged. This is an intentional
profile migration under the continuous-heaviness design, not proof that the three
units are optimally balanced. Prices, HP, movement and actor configuration are unchanged.

| Weapon | Owner | Damage | Reload | Range | Heaviness |
|---|---|---:|---:|---:|---:|
| TSHighVelocity | forgotten_tankkiller | 30000 | 90 | 7701 | 0 |
| TSHighVelocity2 | forgotten_warriortank | 40000 | 55 | 8207 | 0 |
| TSHighVelocityTur | forgotten_brokenwarriortankturret | 48000 | 30 | 9483 | 0 |

The existing Light CannonAP role maps to h0. No new role was invented. The shared
base uses Scale2000; its h/2 percentage contribution is zero at this endpoint.
Effective spread remains80 (authored120 scaled at h0). Projectile speed, effects,
targeting and all other non-profile payloads are unchanged. Armor coefficients
change intentionally: Medium123 to136, Wood83 to123, Heroic90 to63. The earlier
counterfactual estimated analytical effectiveness reductions4.33–4.50%; this is
not a matchup measurement or justification to change prices.

The two chemical alternatives remain byte-equivalent resolved payloads. Owner
primary/upgrade conditions are unchanged. No matching resolved Condition provider
was found on these two actors; this is not proof that external grants are impossible.
The turret has no active chemical alternate. Active raw references are exactly
the three named owners, with no global weapon inheritance descendants. The
isolated test map deliberately adds three probe descendants.

## Earlier three-weapon checkpoint evidence

- Compared all2897 resolved weapons against source5a931844a3c6184fbfdd9f50fc8724b37543c5e0:
  exactly these three changed; the strict comparator accepted only profile fields,
  matching runtime spread and unchanged non-profile fields. No other weapon changed.
- Five resolved-inheritance tests pin damage/operation, shared mode, zero percentage
  contribution at three target-HP levels, non-profile baseline hashes, chemical
  baseline hashes, third-owner closure and no weapon descendants.
- One automated game run: all12 lanes passed, including nine prior controls and
  real Forgotten Bullet projectiles. Medium direct-hit totals40800/54400/65280,
  one flat damage event each. Peak system RAM65.34%, no new exception log, owned
  process closed. No build or engine-pin change was needed.
- Full33-ledger regeneration completed. Only Forgotten raw/derived payloads change.
  Diagnostic design class moves0.75 to1.0 with the level-less base; this does not
  apply prices or actor stats. Authored spread in raw ledgers is120, runtime80.
- Final full-suite and canonical-audit results pending; known baseline failures
  must remain disclosed. The regenerated structure survey also refreshes stale
  pre-existing entries; its large count reduction is not caused by these three
  single-main weapons. Reviewed exceptions remain in raw counts.

The earlier three-weapon independent review found no production blocker; requested durability/third-owner
coverage was added. Wider CannonAP migration, chemical-family conversion and
whole-unit matchup recommendations remain separate work, not implied by this batch.

## Current source candidate

The evidence above records the earlier Forgotten-only checkpoint, not the final
PR341 payload. The current source candidate contains twenty CannonAP migrations,
Freedom elite consolidation and one exact SkyHawk legacy clone. A fresh whole-
weapon comparison on 10 September accepted exactly those changes among 2,898
resolved weapons, with no unexplained remainder. All 33 current ledgers pass the
drift check; nine raw/derived faction pairs differ from the published source HEAD.
See [the full candidate report](CONTINUOUS_CANNONAP_CLOSURE_20260910.md) for current
source audit evidence and remaining policy holds. Combined validation remains
a separate result, and the earlier review does not cover the expanded candidate.
