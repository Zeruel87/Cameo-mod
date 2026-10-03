# Cameo Migration Board — status + runbook

_The living status of the great restructuring. Any agent or contributor can
resume the work from this file alone. Rules live in [DESIGN.md](DESIGN.md);
this file tracks WHERE WE ARE and HOW TO CONTINUE._

## The mission (why all this exists)

Cameo is the ultimate crossover RTS between the classic RTS games, and it
keeps growing. Loading everything at boot peaked at **12 GB RAM**, locking
out 8 GB/4 GB players before the main menu. The end state is **dynamic
faction loading**: the game loads only the factions picked in the lobby
(and only what the active shellmap needs). That requires every faction to
be a **completely self-contained ContentPack** — rules, weapons, sequences,
its own ai.yaml, and all of its assets (sprites, voxels, icons, sounds) in
per-type subfolders — with zero cross-pack dependencies, shared content
only in theme `Shared/` packs or core, and an audit that deletes files
nothing references.

### What "plug and play" means: the acceptance test

A ContentPack is done when **removing its `Include:` line from `mod.yaml`
leaves a game that boots, lints clean and plays**, and adding it back
restores the faction completely, AI included. Nothing outside the pack
names the pack's actors, weapons, sprites or sounds. Three things follow:

* **Memory.** An unpicked faction costs zero RAM and zero load time. This is
  the original reason (the 12 GB peak).
* **Growth.** A new faction is a new folder plus one `Include:` line. Its
  author never edits a shared file, so N contributors can add N factions
  without touching each other's work, and a broken pack breaks only itself.
* **Correctness.** The linter can prove the independence. Any id that
  crosses a pack boundary is a defect the audits can count and ratchet down.

### Why the AI must live in the pack too

Bot configuration is where cross-pack coupling hides best. On 2026-09-27
the central `mods/cameo/ai/ai.yaml` named **7,151 actor ids from every
faction**: 2,680 dictionary rows, such as how many of each unit to build,
and 4,471 list entries, such as which units form raid squads. So:

* a game that doesn't load a faction still carries AI rows for its actors
  (a lint error now, a crash once loading is dynamic);
* adding a unit meant editing the one file every AI agent also edits;
* each pack's `ai.yaml` held only a placeholder comment, whose commented
  copy of the rows drifted from the real ones.

The design that makes the AI plug and play is
[`design/AI_ARCHITECTURE.md`](design/AI_ARCHITECTURE.md) §1.2 (how packs
merge: they can add, never override or remove), §2.7 (dictionary rows move
into the pack) and §2.8 (list membership is derived from each pack's own
actors, never enumerated centrally).

## Target content-pack folder structure (design 2026-07-12)

Every content pack gets the SAME shape — one folder per faction:

```
ContentPacks/<Theme>/<Faction>/
  content.yaml          # the central include dictionary (stays at root)
  yaml/                 # ALL MiniYaml: rules + weapons + sequences merged
                        #   (folder name decided 2026-07-12: `yaml`)
  files/               # ALL assets: sprites, voxels, sounds, icons
                        #   (created empty now; asset migration is later)
```

This replaces the current `rules/ + weapons/ + sequences/` split (they
collapse into the single yaml folder). Shared assets live in a **per-game**
`ContentPacks/<Theme>/Shared/files/` folder if they are shared only between
factions of the same game. Assets shared **across different games** are a
critical architecture error and must move to the top-level
`ContentPacks/Shared/files/` folder, then be duplicated/replaced so each
game owns its own copy. **Do the yaml-folder move first** (create the
folder, move the yaml, keep `content.yaml` at root, update the
`content.yaml` include paths, create an empty `files/`); the asset
migration into `files/` comes later. Research one already-split pack and
apply the identical structure everywhere.

**YAML-folder restructure COMPLETE (2026-07-14):** All ContentPacks now
use the `yaml/` + `files/` structure. The old `rules/`, `weapons/`, and
`sequences/` subdirectories have been removed. `translations/` stays
separate (not MiniYaml).

**Asset migration IN PROGRESS (2026-07-15):**
- `mods/cameo/mod.yaml` mounts per-faction, per-game shared, and
cross-game shared packages before `bits/` so new `files/` content shadows
legacy assets.
- CABAL unique assets (128 files) migrated into
`ContentPacks/TiberianSun/CABAL/files/{icons,sprites,voxels}` and
referenced with `cabal_*|<name>` prefixes.
- 38 single-file cross-game shared assets migrated into
`ContentPacks/Shared/files/sprites/` and referenced with
`shared_sprites|<name>` prefixes across D2k, RedAlert2Mod, TiberianDawn,
and TiberianSun.
- TiberianSun intra-game shared assets (21 files) migrated into
`ContentPacks/TiberianSun/Shared/files/{icons,sprites,voxels}` and
referenced with `ts_shared_*|<name>` prefixes.
- Remaining cross-game shared assets with multiple variants or name
  collisions are still in `bits/` and tracked as critical: `gunfire2`
  (generic/RA/TD variants), `electro` (7 tileset variants), `dragon`
  (RA sprite vs WC2 sound collision), and `d2k/DATA.R16` (resource
  package). These must be resolved before `bits/` can be deprecated.

**Cross-faction shared effects — long-term de-sharing.** Factions now
cross-reference each other's effect sprites/weapons heavily. The
end-state needs each faction's effects to be its own, or at minimum
shared only PER GAME (never across games), so a pack loads without
pulling another faction's assets. The top-level `ContentPacks/Shared/files/`
folder is a temporary holding area for cross-game assets that must be
duplicated per-game and then removed.

## AI module split — how it works and where it stands

⚠ **This section used to say the split was blocked**, because "the loader
replaces trait instances and does not deep-merge sub-sections". **That was
wrong.** It was measured on 2026-09-05 (`design/AI_ARCHITECTURE.md` §1.2):
a pack that adds rows to a dictionary field the central file declares gets
them **unioned**. The old recommendation (one module instance per faction,
gated by a faction condition) was also rejected: two enabled squad managers
or unit builders compete for the same units and cash (§2.3). The same wrong
note sat in all 28 pack `ai.yaml` files and has been replaced.

**The rule:** a pack can ADD rows, keys and trait instances. It can never
override a key the central file sets (the central file loads last), and it
can never remove one (a load-time crash).

**Where it stands (2026-09-27):**

| Part | Size | How | State |
|---|---|---|---|
| Dictionary rows (`UnitsToBuild`, `BuildingFractions`, `BuildingLimits`, `UnitLimits`, `AirSquadTargetTypes`, delays and intervals) | 2,680 refs; 2,646 movable | `tools/packs/split_ai_rows.py --pack <Theme/Faction> --apply` | **landed** — all-pack move done for the six genericbot personalities; the last 27 `SquadManagerBotModuleCA@classic` `AirSquadTargetTypes` rows hand-merged into 14 packs (2026-10-01, resolved-identical verified: 12008 keys / 0 diff, boot-gate + ai_squad_gate PASS). `--all` now reports 0 movable |
| List fields (`GuerrillaTypes`, `ExcludeFromSquadsTypes`, `HighValueTargetTypes`, …) | 4,471 refs in 41 fields | derived roles + `BotRoles` on each pack's actors (§2.8) | **ruled 2026-09-27: roles on actors**; C# next (AI architect lane) |
| Module declarations, scalars, personalities, difficulties | — | stay central (one authority per decision) | by design |

**Gate for every move:** dump `utility.cmd cameo --resolved-rules Player`
before and after, and compare with `tools/packs/compare_resolved.py`. It
compares content, because moving rows reorders the dump by design. Then
build, boot and `tools/tests/ai_squad_gate.py`.

**For pack authors:** a new faction's AI rows go in **its own**
`yaml/ai.yaml`, under the same trait instance names as the central file
(e.g. `UnitBuilderBotModuleCA@generic: UnitsToBuild:`), and the file must be
listed in the pack's `content.yaml` `Rules:`. Never add a faction id to a
**dictionary row** in `mods/cameo/ai/ai.yaml` — dictionaries merge from packs,
so a central copy is only a second place to drift. **List fields get their
members from the §2.8 `BotRoleSets` roles once a role is applied**
(`Apply: harvester, refinery, conyard` covers three so far); for a list field
no applied role covers yet, a pack still cannot extend the central list, so a
faction's ids must be appended to the central `*Types` row at rollout —
missing ids = inert bots (fixed on `devin/ember/ai-faction-wiring`, lesson
2026-09-28). `Apply:` unions with the written list, so interim appends dedupe
when the covering role lands and can then be drained from the central file.

## The per-faction pipeline (proven, verified, repeatable)

```
1. RENAME   python tools/rename/curate_map.py <faction> [--slugtag <tag>]
            # stops and asks design if display names collide (DESIGN.md §1)
            python tools/audit/dump_resolved.py --faction <f> > before.json
            python tools/rename/safe_rename.py tools/rename/rename_map_<f>.yaml
            # verify: map before.json through the map, diff resolved trees
            # -> MUST be empty; zero old ids; assets on disk.  Commit.
2. SPLIT    python tools/packs/split_faction.py --theme <T> --faction <F> \
                --prefix <id_prefix> --rules <mono>.yaml --weapons ... \
                --sequences ...
            # verify: actor/weapon/sequence registries identical, resolved
            # closure diff empty.  Commit.
3. DESCRIBE  Part of EVERY faction split: rework the faction's actor,
   upgrade, and promotion descriptions into Fluent (DESIGN.md §7 — the
   Tarantula model: derived from resolved traits/weapons/upgrades, RA1
   layout, Strong/Weak vs). One sample actor goes to design review first,
   then the faction is batched.
4. LATER PHASES (per pack): own ai.yaml; move assets into the pack in
   per-type subfolders; unused-file audit + deletion.
```

Every step is behavior-preserving by proof, never by hope. Balance changes
are never mixed in; typo-class bugs found on the way are fixed in separate
commits and reported.

## Status board

| faction | rename | pack split | own ai.yaml | assets in pack | fluent descriptions |
|---|---|---|---|---|---|
| Forgotten (TS) | DONE `d7b86798d` | DONE `03ce7e96c` | — | — | DONE `d723a6b78` |
| TS GDI | DONE `9d901fb45` | DONE `dfa00f20f` | — | — | — |
| TS Nod | DONE `8c82ad950` | DONE `a34c80678` | — | — | — |
| CABAL | DONE | DONE | — | DONE `68cdd5ebb`/`472209150` | DONE `68cdd5ebb` |
| TS Shared | — | — | — | DONE `6835a04` | — |
| Top-level Shared | — | — | — | DONE `e1b153d9c`/`472209150` | — |
| TD GDI / TD Nod | DONE (ids renamed to `td_gdi_*`/`td_nod_*`) | DONE incl. weapons+sequences | — | — | — |
| RA2Mod six (original) | DONE (ids renamed to `asianalliance_*`, `steelconsortium_*`, `latinsyndicate_*`, `naxis_*`, `schwarzermond_*`, `futuretech_*`) | DONE incl. weapons+sequences | — | PARTIAL (1032+47 files copied to `files/{icons,sprites,sounds}` with `ra2m_<pack>_<type>|` refs incl. the live sequences/weapons/audio monoliths; 107 cross-theme refs stay in `bits/`, 37 dangling) | — |
| D2k four (atreides/harkonnen/ixian/ordos) | PARTIAL (new-style `atreides_*` etc. for some actors; old-style dotted names like `combat_tank.atreides` remain) | DONE incl. weapons+sequences | — | PARTIAL (packs already held 529 files; 144 exclusives copied from `bits/d2k`, 382 refs qualified to `d2k_<pack>_<type>|` incl. live sequences/weapons/audio monoliths; 32 resolve inside SOUND.RS/DATA.R16; 10 dangling, 60 shared stay) | — |
| RA1 (allies/soviets/japan) | DONE incl. 52 legacy ids 2026-07-17 (RAE1→ra1_allies_rifleinfantry etc.; only `japan` unprefixed; map: rename_map_ra1_legacy.yaml) | DONE 2026-07-16 (yaml/ layout, registry-identical, boot-verified) | — | PARTIAL (528 exclusive files copied to `files/{icons,sprites,sounds}` with `ra1_<pack>_<type>|` refs, 12 mounts; 90 shared stay bare; 26 dangling — RA1 `.aud` never shipped in `bits/`) | — |
| RA2 (america/russia/yuri) | maps drafted | DONE (Allies/Soviets/Yuri/Shared packs own their yaml; `rules/redalert2.yaml` remains mounted as the shared monolith via the wrapper) | — | PARTIAL (397 faction-exclusive files → `files/{icons,sprites,sounds}` with `ra2_<faction>_<type>|` refs; `audio.bag`+`.idx` and `bits/ra2/tileset` moved into the Shared pack; 458 cross-theme refs stay in `bits/`) | — |
| StarCraft (terran/zerg/protoss) | DONE (ids) | DONE 2026-07-17 (registry-identical, boot-verified) | — | — | — |
| WC2 (humans/orcs) | DONE (ids) | DONE 2026-07-17 (registry-identical, boot-verified) | — | PARTIAL (189 refs qualified / 189 files in `wc2_<pack>_<type>` packages incl. live sequences+weapons monoliths; 22 shared stay bare; 1 dangling `aacanon3.aud`) | — |
| TKM | DONE (ids) | DONE 2026-07-18 (moved into `RedAlert2Mod/TKM/`) | — | — | — |
| Outpost2 (eden/plymouth, WIP factions) | maps drafted (~compliant) | monolith/wrapper | | | |

**Cross-pack self-containment (2026-09-24):** the hard-reference layer is
clean for D2k, TiberianDawn, TiberianSun and StarCraft — every `Inherits`,
`Weapon:`, `IconImage:`, `Actor:`, `ActorTypes:` and sequence-name override in
those packs resolves to a def mounted by their own `content.yaml` chain or a
core `mod.yaml` mount (PRs #497/#498 + the value-ref batch). The remaining
known contamination is *soft*: `Condition:`/`RequiresCondition:` strings and
`ActorTypes:` spawn lists in `Shared/yaml/*.yaml` pointing into foreign
namespaces — dormant without the foreign pack, awaiting a fleet ruling on
whether they are intentional cross-faction gates. The census tooling lives in
`tools/` (`pack_reach.py`-style mount-topology check): a def is a leak only if
ALL its definitions sit in files the consumer's pack never mounts.
Verbatim-copy trap: copying a foreign def re-adds its W2/W6/W7/W8 findings in
the merged corpus — copies must be made audit-clean (effect nodes into
per-weapon `^<pk>_<w>` families, dropped edges materialized inline,
resolved-identical verified).

Proposal maps for every faction: `tools/rename/rename_map_<faction>.yaml`
(regenerate: `python tools/audit/gen_rename_maps.py`).

**Asset migration tooling (2026-09-26):** `tools/packs/migrate_assets.py`
automates the CABAL pilot's mechanics for any theme —
`python tools/packs/migrate_assets.py --theme <Theme> --pkg-prefix <pfx>`
censuses every extension-matching file token in the theme's yaml, locates it
under `bits/` (or inside a mounted `.bag`/`.idx` package — those names are
reported as `packaged` and left to resolve from the bag), and classifies each
as theme-exclusive (migrate), foreign-referenced (leave in `bits/`), or
dangling (report only). `--apply` shadow-copies exclusives into the owning
pack's `files/{icons,sprites,voxels,sounds}` (icon/`icnh` basenames → icons,
`vxl`/`hva` → voxels, `wav`/`aud` → sounds, rest → sprites), inserts
`~cameo|.../files/<type>: <prefix>_<pack>_<type>` mounts in `mod.yaml` before
the `cameo|bits` line, and rewrites the theme's bare refs to `pkg|name`.
Re-running is idempotent (refs report as `qualified`). Monolith discovery: theme yaml includes (a) every
file the theme's content.yaml(s) declare (`cameo|rules/<theme>.yaml` wrapper
packs) and (b) LIVE mod.yaml core entries named `<theme>.yaml` under
rules/sequences/weapons/audio/tilesets. Dormant monoliths (commented-out
mounts) are NOT scanned or rewritten.
 RA2 census report:
`docs/migration/ra2_assets.json`. Known RA2 dangling refs found by the census
(pre-existing, NOT introduced by the migration): `ra2htanyaicon.shp`,
`cra2cmin.shp`, `ra2ltnk.shp`, `ra2howi.shp`, `ra2arty.shp`,
`yuri_chaosdrone.shp`, `splash9.aud`, `kaboom25.aud`, `kaboom15.aud`,
`cannon1.aud`, `turret1.aud`, `tesla1.aud`, `zulhit00.aud`, `aacanon3.aud`,
`chute1.aud`, `expnew13.wav`, `expnew09.wav`, `spysreve.wav`.

RA2 follow-up: `bits/ra2/audio.bag`+`.idx` moved to
`ContentPacks/RedAlert2/Shared/files/sounds/` with the mount redirected
(the 184 bag-resident names keep resolving; the bits copies remain as the
unmounted shadow archive). Voxel caveat found while collecting: RA2
`RenderVoxels` actors reference image names equal to the (renamed) actor ids,
but `bits/ra2/voxel/` files still carry LEGACY names (`ra2aegis.vxl` vs actor
`ra2_allies_aegiscruiser`) — the faction rename never renamed the voxel
files, so those voxel renderers have been dead since the rename. That is a
pre-existing defect needing a voxel rename pass (names, not moves), logged
here so the voxel migration slice does not paper over it.

D2k follow-up (prefix-existing slice): D2k's packs were already
half-migrated by hand — 529 files sat in `files/` dirs while the yaml kept
bare references that only resolved through the bare-name fallback.
`--prefix-existing` qualified 222 refs (`d2k_atreides_sprites|…` etc. across
13 yaml files), 7 genuinely-missing exclusives were copied out of `bits/d2k`
(harkonnen/ordos/ixian/shared sounds + ixian sprites), and 4 mounts were
added. Re-census: `migrate=0, qualified=234, packaged=31` (24 of them inside
`bits/d2k/SOUND.RS`, now indexed), `shared=52` left bare, `missing=8`
(`REARM1.WAV`, `splash9.aud`, `tesla1.aud`, `missile6.aud`, `missile7.aud`,
`zhyfir00.aud`, `chute1.aud`, `kaboom12.aud` — dangling, reported only).
`DATA.R16`/`BLOXBASE.R16` remain in `bits/d2k` unextracted — same deferred
call as `audio.bag` had been: internal shp/wav resources would need a
package-aware extraction pass, not a file move.

bits/ usage census (audit_bits_refs.py): 28,052 files under `bits/`;
4,858 referenced by live yaml, 5,403 referenced only by dormant yaml,
17,791 referenced nowhere (largest pools: generals 2320, ts 1605, wh40k
1334, notifications 997, ra2/mod 923, darkreign 919, shockwave 907,
ep315 780, ra2 754). `unref` is evidence, not a delete list — engine-
hardcoded names, Lua spawns and tileset frames still resolve without a
yaml token. Report: `docs/migration/bits_refs.json`.

## Standing decisions (design)

- Names: one lowercase group, RA1 baseline; tooltip <-> id in sync; unique
  tooltips per faction; **new display names are design's pick — propose
  options first** (blue fiend -> "Vinifera Fiend").
- Voice sets & shared namespaces are never renamed with a unit (safe_rename.py
  protects them; `tsmedic` collision caught live).
- Pack layout: rules split per actor type; exactly ONE weapons.yaml and ONE
  sequences.yaml per faction.
- Every faction keeps a Tier-1 defense; DEFERRED audit findings list what
  waits on that.
- **Keep `bits/` until all factions are ContentPacked.** The legacy `bits/`
  folder is the archive for the old 0.31 ("classic cameo") factions and
  shared assets that have not yet been migrated. It stays mounted after all
  ContentPack packages so migrated assets shadow the legacy copies. Only
  remove `bits/` after (a) every referenced asset has been moved to a faction,
  per-game Shared, or top-level Shared pack; (b) the remaining cross-game
  shared assets have been duplicated per-game; and (c) an unused-file audit
  has been run and the old factions are either restored as ContentPacks or
  formally dropped.
- Commit policy: clean commits, one concern each; commit when design says.
