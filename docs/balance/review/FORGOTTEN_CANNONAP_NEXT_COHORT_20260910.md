# Forgotten CannonAP next-cohort assessment

Read-only counterfactual on PR341 `0dba5542ff8068179066321ab1aa633a1a4cf82b`.
No additional weapon activation, price, HP, reload, range or actor change.

The three direct Light-CannonAP weapons are plausible next candidates. Their
resolved main can use the existing shared CannonAP base at h=0, retaining Damage
and effective Spread80. All non-profile main fields and every other resolved
weapon field compare equal. The shared candidate explicitly requires Scale2000,
one main, h=0 and zero percentage applications. This is not equivalent gameplay:
removing percentage damage changes scaling against high-HP victims.

| Weapon | Owner | Damage | Reload | Analytical effectiveness change |
|---|---|---:|---:|---:|
| TSHighVelocity | forgotten_tankkiller | 30000 | 90 | -4.3303% |
| TSHighVelocity2 | forgotten_warriortank | 40000 | 55 | -4.3788% |
| TSHighVelocityTur | forgotten_brokenwarriortankturret | 48000 | 30 | -4.5020% |

These are the current pricing model's effectiveness estimates, not final prices,
measured combat DPS, or proof of balanced matchups. Flat coefficients change much
more for some armor: Wood83→123 (+48.2%), Heroic90→63 (-30%), Medium123→136
(+10.6%). Percentage loss is additional to these flat-component changes.
Chemical alternate weapons are separate and are not covered by this counterfactual.

Do not migrate every remaining CannonAP user mechanically: ra1_allies_gunboat_cannon
(formerly 2Inch) has custom geometry; its identity rename does not resolve this hold;
SkyHawk has air targeting and a mixed descendant; TSLaser90mm carries an additional
3% laser damage channel. Those require explicit channel/geometry decisions.

Recommendation: retain the five-weapon live pilot for this integration checkpoint.
Use the three Forgotten weapons as the next bounded cohort after reviewing their
alternate-weapon and matchup consequences. The broader migration remains unfinished.
