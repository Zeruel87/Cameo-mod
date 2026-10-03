# D2K Harkonnen EBFD roster audit — 2026-09-20

The finalized Discord archives were checked against the repository before this
batch. The HarkSprites archive SHA-256 is
`14A02C2215A0347890ACA9163BDE557071F3B22AD2D5D2E3C7C38FDB24004F61` and the
FinalizedHarkAtr archive SHA-256 is
`8B3223A8C57505FD2AD7286E2FF391AAA39BFC966EE1B06C1C391C5531DA1224`.
Every corresponding repository PNG was byte-identical, so this change does not
re-import or alter asset bytes.

The identity repair keeps `combat_tank.harkonnen`, `missile_tank`, and
`devastator` on their classic DATA.R16 sources and exact starts. The reserved
Assault Tank hull is now the distinct `harkonnen_assaulttank` actor and
sequence, using the reviewed Phase 4 implementation from `94cd582bd` with
frontal `80mm_H` fire. The live Harkonnen rocket gameplay is cloned into
`harkonnen_rockettank`; removing only the Harkonnen-local `missile_tank`
sequence override restores the classic global Missile Tank DATA.R16 sequence.
The dead `devastator_husk.harkonnen` sequence was removed after active parsed
references were exhausted. The live misspelled `harkonnen_devestator*` assets
remain unchanged.

Nine Harkonnen EBFD actors are gated one-to-one by Promotions queue tokens in
three independent branches:

- Brute force: Assault Tank -> Flame Tank -> Devastator Mech
- Siege/control: Buzzsaw -> Rocket Tank -> Inkvine Catapult
- Air: Gunship -> Air Defense Platform -> Advanced Carryall

The global AI dictionary lists all nine promotion actors before their consumers,
adds the two new unit IDs, and retains classic `missile_tank` plus the existing
Harkonnen weights. The local AI file remains a non-merging marker because the
global bot dictionaries cannot be deep-merged.

## Upgrade-palette crash repair

The Harkonnen playtest produced
`TypeDictionary does not contain ... RenderSpritesInfo` in
`ProductionPaletteWidget.RefreshIcons` when selecting the Upgrades queue. The
five Harkonnen building-upgrade actors were buildable but had no
`RenderSprites` trait. The same latent defect existed in the equivalent five
Atreides and five Corrino actors. All 15 now point at their faction's existing
construction-yard, barracks, light-factory, heavy-factory, or outpost icon
sequence. The focused contract resolves every actor, confirms the Upgrades
queue, and confirms the selected sequence defines `icon`. Runtime confirmation
is pending because the maintainer requested no automatic relaunch.

The production-icon geometry audit also found the 256x256 Devastator Turret
icon as a confirmed overflow. Its source PNG remains unchanged; the active
sequence now uses a fitted 64x48 `harkonnen_devastatorturret_build_icon.png`
derived from relative turret facing 24 (absolute sheet frame 40), with the
rotating head visibly aimed southwest.

The final tree was re-extracted with the full balance pipeline. The nine new
promotion rows and two unit rows are in `docs/balance/d2k_harkonnen.json`.
Adding Heavy and Medium actors changes the shared versus-model counts, so the
deterministic derived sidecars were regenerated across all 34 ledgers; this is
required for `extract_stats.py --check` to remain at zero drift.

Visual risk remains playtest-only: verify the frontal assault silhouette and
player palette, Rocket Tank/Assault Tank icon and facing alignment, restored
DATA.R16 classic Missile Tank art, Devastator Mech animation, and all death and
muzzle effects. Playtest should also confirm promotion ordering and branch
availability in the Harkonnen production and Promotions palettes, AI promotion
purchase behavior, and menu boot with zero new exception logs. A fresh launch
was attempted with an isolated support directory, but this worktree has no
`engine/bin/OpenRA.exe`; `launch-game.cmd` therefore stopped at its required
engine-files gate. No menu or exception-log result is claimed here. This report
does not claim in-game visual approval.
