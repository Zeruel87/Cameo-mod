# audit_upgrade_coverage — roster-wide upgrade gaps (B4)

Coverage-tagged upgrades checked: **24** — uncovered unit slots: **21**


## Coverage by upgrade

| upgrade | faction | declared coverage | covered | uncovered actors |
|---|---|---|---|---|
| cabal_upgrade_darkarmament | cabal | infantry | 10/16 | cabal_beholder, cabal_cyborgassassin, cabal_dissolver, cabal_engineer, cabal_hackercyborg, cabal_orbdrone |
| cabal_upgrade_firewallprotocol | cabal | roster_wide | 33/38 | cabal_constructionyard, cabal_dissolver, cabal_mobileconstructionvehicle, cabal_tiberiumharvester, tsprobe |
| cabal_upgrade_fullassimilation | cabal | roster_wide | 33/38 | cabal_constructionyard, cabal_dissolver, cabal_mobileconstructionvehicle, cabal_tiberiumharvester, tsprobe |
| cabal_upgrade_networkedcombatprotocols | cabal | roster_wide | 33/38 | cabal_constructionyard, cabal_dissolver, cabal_mobileconstructionvehicle, cabal_tiberiumharvester, tsprobe |
| cabaldarkarmament | cabal | infantry | UPGRADE ACTOR MISSING |  |
| cabalfirewallprotocol | cabal | roster_wide | UPGRADE ACTOR MISSING |  |
| cabalnetworkprotocols | cabal | roster_wide | UPGRADE ACTOR MISSING |  |
| schwarzer_mond_upgrade_cryptofascism | lnaxis | roster_wide | UPGRADE ACTOR MISSING |  |
| schwarzer_mond_upgrade_lunaralloys | lnaxis | roster_wide | UPGRADE ACTOR MISSING |  |
| schwarzer_mond_upgrade_moonpropaganda | lnaxis | infantry | UPGRADE ACTOR MISSING |  |
| schwarzer_mond_upgrade_vrilinfusion | lnaxis | infantry | UPGRADE ACTOR MISSING |  |
| td_nod_upgrade_cyberneticmodifications | td_nod | infantry | 11/11 | — |
| up_advancedtiberiumrefinement | tsnod | vehicles | UPGRADE ACTOR MISSING |  |
| up_chemicalfuel | forgotten | vehicles | UPGRADE ACTOR MISSING |  |
| up_genomemapping | forgotten | infantry | UPGRADE ACTOR MISSING |  |
| up_junkarmor | forgotten | vehicles | UPGRADE ACTOR MISSING |  |
| up_mechanicalreliability | tsgdi | vehicles | UPGRADE ACTOR MISSING |  |
| up_modernfirecontrolsystems | tsgdi | roster_wide | UPGRADE ACTOR MISSING |  |
| up_mypet | forgotten | roster_wide | UPGRADE ACTOR MISSING |  |
| up_seretraining | tsgdi | infantry | UPGRADE ACTOR MISSING |  |
| up_tiberiumadaptability | forgotten | roster_wide | UPGRADE ACTOR MISSING |  |
| up_unity | forgotten | roster_wide | UPGRADE ACTOR MISSING |  |
| up_willofkane | tsnod | infantry | UPGRADE ACTOR MISSING |  |
| upcabalfullassimilation | cabal | roster_wide | UPGRADE ACTOR MISSING |  |


_Note: 'covered' means the actor carries a GrantConditionOnPrerequisite hook for the upgrade. Upgrades applied globally through a shared decoration/rank template count as covered because the hook is inherited into the resolved actor._

