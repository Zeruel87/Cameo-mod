# D2K Atreides EBFD roster audit — 2026-09-20

The finalized EBFD Atreides archive is identified by SHA-256
`8B3223A8C57505FD2AD7286E2FF391AAA39BFC966EE1B06C1C391C5531DA1224`.
Its nine finalized visual families are already present under
`mods/cameo/bits/d2k/` (`airdrone`, `advancedcarryall`, `APC`, `Minotaurus`,
`Mongoose`, `ornithopter`, `repairtank`, `sandbike`, and `sonictank`). The
focused roster test pins their individual PNG hashes; the imported source bytes
remain identical. The nine 64x48 `*_build_icon.png` production assets are
cropped from the official EBFD icons listed by the
[Emperor Atreides arsenal](https://dunerts.wiki.gg/wiki/Emperor_Atreides_arsenal),
without modifying those archived source files.

The active Atreides pack now uses the unique `atreides_sonictank` sequence
namespace for the actor, husk, and Sonic promotion. The body and idle/move
frames resolve to the archived Atreides PNGs with `player_rgba`; the icon uses
the derived 64x48 production asset, and the actor
explicitly selects the archived `move` sequence through `WithMoveAnimation`.
The global classic `sonic_tank` DATA.R16 sequence is unchanged. The duplicated
local `d2k_atreides_apc` sequence was removed after an active-pack reference scan;
the global dormant legacy sequence and SHP assets remain on disk unchanged.

All five Atreides promotion actors are in the global `Player` `UnitsToBuild`
dictionary in dependency order: Fremen, Sonic Tank, Air Drone, Minotaurus,
Mongoose. Existing unit weights and limits are preserved. Mongoose keeps
`mtank_pri` and now declares the `muzzle`/`d2keffect` presentation and
`WithMuzzleOverlay`; the Ixian `MongooseRocket` weapon and all balance values
are deliberately excluded.

Localization was not expanded here. The Atreides pack translation file remains
the existing placeholder; current actor and promotion display strings retain
their existing YAML/fallback coverage and require a separate localization
pass if new translated keys are desired.

The PNG work is presentation-only: the nine wiki icons and, as the explicit
local-source exception, the Harvester's southwest body frame are fitted into
new 64x48 production assets without changing world art. Directional unit art
uses the southwest convention: Mongoose, Sonic, Repair Vehicle, and Sand Bike
are mirrored horizontally so the isometric perspective remains upright; the already-southwest wiki icons
remain unchanged. Corrino APC uses its southwest body frame, while Harkonnen
Devastator Turret uses the southwest frame of its rotating head. Weapon/balance
changes, engine/build work, and `--check-yaml` remain excluded. The pinned Cameo engine reached
`MenuPostProcessEffect.PostWorldLoaded` in an isolated support directory with
zero new `exception-*.log` files. That is a load gate only and is not an
in-game visual approval claim.

Remaining visual playtest risks are Minotaurus frame clipping, Sonic idle/move/
husk transitions, Mongoose and APC turret/muzzle alignment, advanced carryall
pickup behavior, repair-tank presentation, and ornithopter transitions.
