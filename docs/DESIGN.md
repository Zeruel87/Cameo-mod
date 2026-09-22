# OpenRA Cameo — Design Document

_The distilled, binding design contract for this mod. Every AI agent session
and every contributor reads this FIRST. The long-form historical analysis
lives in [MASTER_REPORT.md](history/MASTER_REPORT_2026-07-08.md) (not a live roadmap — active
work belongs in [design/ROADMAP.md](design/ROADMAP.md)); the machine-checkable
state lives in [audit/](audit/) — this document is the rules themselves.
Faction lore, gameplay profiles, and roster details live in
[FACTIONS.md](FACTIONS.md)._

_When code and this document disagree, the document wins unless an audit
baseline explicitly defers the fix (e.g. "DEFERRED" findings). When this
document is silent, check MASTER_REPORT §13, then ask design._

---

## 1. Naming (the RA1-Soviet baseline)

```
unit/building id :=  [game_]faction_nameinonegroup[_variant]
tech item id     :=  [game_]faction_(upgrade|promotion|doctrine)_nameinonegroup
```

- The **name is ONE lowercase group without separators**: `ra_heatraytank`,
  `forgotten_ghoststalker`, `forgotten_experimentalmammothtank`.
- **Underscores separate SECTIONS, never within names** (design 2026-07-16):
  The actor id has exactly three sections — `[game_]faction_actorname[_variant]`.
  Underscores are ONLY used to separate these sections. Faction names and actor
  names are each a single unbroken lowercase group with NO internal underscores.
  - **Correct**: `td_gdi_lighttank`, `ra1_soviets_heavytank`, `wc2_humans_footman`,
    `asianalliance_quasar`, `steelconsortium_manta`, `latinsyndicate_freedomfighter`,
    `schwarzermond_lunarsoldier`.
  - **Wrong**: `asian_alliance_quasar` (underscore inside faction name),
    `steel_consortium_manta`, `latin_syndicate_freedomfighter`.
  - Faction InternalName must match the faction section of the actor prefix
    exactly: actors `td_gdi_*` → faction `td_gdi`; actors `asianalliance_*` →
    faction `asianalliance`.
- **Umlauts and other non-ASCII letters TRANSLITERATE, never drop**
  (design 2026-07-17): ids derive from display names by mapping
  Ü→u, ü→u, Ö→o, ö→o, Ä→a, ä→a, ß→ss — e.g. `Übermensch` →
  `schwarzermond_ubermensch` (the earlier `_bermensch`, with the Ü
  silently dropped, was a bug). Weapon and sequence ids follow the
  same rule (`ÜbermenschLaser` → `UbermenschLaser`). DISPLAY names
  (Tooltip `Name:`, fluent text) keep their proper umlauts.
- **The only separator is the underscore — hyphens are banned in ALL
  naming we own** (design 2026-07-10): actor ids, asset file names
  (`cabal_dissolver_weapon.shp`, never `cabal_dissolver-weapon.shp`),
  fluent keys (`actor_forgotten_scoopertank`, never `actor-…`), and every
  yaml reference to them. Hyphens double as token boundaries in tooling
  and caused the rename crash class. Exception: identifiers the ENGINE
  defines or derives (built-in condition names like `build-incomplete`,
  engine chrome/fluent keys) stay as the engine spells them.
  **C#-derived names count as engine-owned**: fluent keys composed in
  code (`actor-stats-label-prefix.*`, `label-armor-class.*`,
  `checkbox-*` graphics options, `support-power-timer`, ...) and chrome
  collections composed in code (`sidebar-<faction>`) keep their hyphens
  even when defined in our files — scan ALL assemblies (engine mods AND
  OpenRA.Mods.CA/Cameo in-repo) for string literals before renaming any
  key family. A no-exception global rename was considered and rejected
  (2026-07-11): it would require C# changes, which are out of bounds.
- **Game prefix only on actual collisions** (`td_gdi` vs `ts_gdi`,
  `ra1_soviets` vs `ra2_soviets`). Unique factions (cabal, forgotten, yuri,
  ordos, terran…) take no game prefix. Prefixes are added the day a
  collision appears, never preemptively.
- **Tech markers are full words**: `upgrade` (cash research), `promotion`
  (rank-gated), `doctrine` (mutually exclusive picks). Team proxies end
  `_proxy_actor`. Promotions never carry "unlock" in the id.
- **Variants** are structural suffixes: `_husk _sp _r4 _wild _mk2 _elite
  _ai _water _EMP _AA _upgraded _slave _air _backup _segment _bomber
  _paradrop _chrono _hmg _mg _missile _repair _empty _plug _bot _defense
  _deployed` plus dotted variants (`.husk`) and paradrop twins (`para`).
- **The dot rule** (maintainer ruling 2026-09-06). A dot marks a **VARIANT of the
  base actor named before it** — `camera.spysat`, `powerproxy.emp`,
  `ra2gacnst.infiltrated`, `carryall.paradrop`, `fact.colorpicker`, `hack.rank_3`
  are all legal, exactly as `.husk` always was. ⛔ **A dot may NEVER carry a
  faction.** `ptnk.asian` and `rocket_raider.ixian` put the faction in the suffix
  where the grammar requires it as the PREFIX, and those are the only dotted ids
  that are renaming debt: `ptnk.asian` -> `asianalliance_plasmatank`. The rule is
  what makes the two cases distinguishable by a tool rather than by taste, and
  `audit_naming_damage.py` N5 enforces exactly it. (Before this ruling, all 398
  dotted ids read as backlog; 237 were husks, 52 were variants, and only 109 were
  ever real.)
- **Tooltip ↔ id consistency**: the id's name group derives from the
  Tooltip Name and both stay in sync. No two actors of a faction may share
  a Tooltip Name (audit_metadata M1). New display names are a **design
  decision — propose options and let design choose** (the blue Tiberian
  Fiend became "Vinifera Fiend").
- **Asset files follow their actor id**: body sprite `<id>.<ext>`, icon
  `<id>_icon.<ext>`; multi-file bodies keep only their distinguishing
  suffix (`forgotten_warfactory_door.png`). Shared sprite archives
  (DATA.R16-style) and files shared between images are never renamed after
  one unit.
- **Asset suffix words are ALWAYS full words, never abbreviations**
  (design 2026-07-14): construction animations use `_make` (never `_mk`,
  never compressed old-name + `mk` like `ntcnstmk`); building bib overlays
  use `_bib` (never `_bb`); damaged/idle/active/dead sequences use their
  full names. When migrating old assets, strip any compressed old-name
  prefix from the suffix and replace short forms with full words:
  `ra2_soviets_constructionyard_ntcnstmk.shp` →
  `ra2_soviets_constructionyard_make.shp`. The only exception is `_mk2`/
  `_mk3` as unit variant markers (Mark II/III), which are part of the
  actor name, not a sequence suffix.
- **Sequence filenames must match their actor and sequence name**
  (design 2026-07-16):
  - **Idle/body sprite**: the primary body sprite filename MUST be
    `<actor_id>.<ext>` and placed in the `Defaults:` section so all
    sequences that use the same body sprite inherit it automatically.
    Example: `latinsyndicate_topolsilo.shp` goes into `Defaults:`,
    not `latinsyndicate_topolsilo_cg12hit_f.shp` in each idle/damaged-idle/
    critical-idle entry.
  - **Non-idle sequences**: every sequence that is NOT the idle/body
    sprite MUST include the sequence name as a suffix in the filename:
    `<actor_id>_<sequence_name>.<ext>`. Examples:
    `latinsyndicate_topolsilo_bib.shp` (bib sequence),
    `latinsyndicate_topolsilo_make.shp` (make sequence),
    `ra2_soviets_constructionyard_icon.shp` (icon sequence),
    `cabal_tarantula_turret.shp` (turret sequence).
  - **Sequence name suffixes use full words**: `_bib`, `_make`, `_turret`,
    `_muzzle`, `_icon`, `_active`, `_dead`, `_damaged`, `_critical`,
    `_shadow`, `_deploy`, `_up`, `_down`, `_harvest`, etc. These match
    the sequence key names exactly (hyphens in sequence keys like
    `damaged-idle` map to underscores in filenames: `_damaged_idle` or
    are collapsed to the distinguishing word only: `_damaged`).
  - **Shared files are NEVER renamed** (critical safety rule):
    - Files in `shared_sprites|`, `ts_shared_sprites|`, `td_shared_sprites|`
      and other shared namespaces (`invisibleitem.shp`, `gunfire2.shp`,
      `electro.shp`, `frag3.shp`, `parach_shadow.shp`, `ra2_oregath.shp`,
      etc.) are used by many actors and MUST stay with their shared name.
    - Death sequence files defined in inherited templates like
      `^RA2InfantryDeaths`, `^RA2BasicInfantry`, `^RA2ProneInfantry`
      are shared across all inheriting actors and MUST NOT be renamed
      to match any single actor.
    - Template default filenames (e.g., `ra2gi.shp` in `^RA2BasicInfantry`)
      are placeholder defaults that get overridden per-actor; the template
      file itself stays as-is.
    - Muzzle flash files (`gunfire2.shp`, `ra2_gunfire.shp`) shared across
      many actors stay as-is.
    - DATA.R16-style shared sprite archives stay as-is.
    - Voice sets, notifications, and shared art are already protected by
      the cross-actor namespace rule above.
  - **Combine sequences**: sub-images referenced in `Combine:` blocks
    that are unique to one actor should be renamed to
    `<actor_id>_<descriptive_suffix>.<ext>`. Sub-images shared across
    multiple actors stay as-is.
  - **Inherited template defaults**: when an actor inherits from a
    template (e.g., `^RA2ArmedInfantry`) and overrides `Defaults:
    Filename:`, the override filename MUST be `<actor_id>.<ext>`. The
    template's own default filename (e.g., `ra2gi.shp`) is a shared
    baseline and is NOT renamed.
  - **Migration approach**: per faction, curated via
    `tools/rename/rename_map_<faction>.yaml` + `tools/rename/safe_rename.py`,
    verified with `tools/audit/dump_resolved.py` before/after diffs
    (must be empty). A pre-flight audit script must build a complete
    cross-reference of which filenames are used by which actors to
    identify shared files that must NOT be renamed.
- **Shared asset files are NEVER renamed after one user (LAW,
  2026-07-17).** The naming migration renamed `brik.shp` (a TD concrete
  barrier used by several factions) into a nonexistent
  `futuretech_concretebarrier_*` name and broke the menu; the TD GDI
  voice variant keys broke the same way. An asset file may be renamed
  ONLY after a full cross-reference proves exactly one actor uses it.
  Shared assets keep their original names and move to the owning
  Shared pack instead. After every rename batch run
  `audit_asset_files.py` (A1 must be 0). Golden reference for
  pre-rename values: the last Cameo-IFV release install (use for
  regression diffs when a rename regression is suspected).
- **The wall target type is lowercase `wall`** (evidence 2026-07-17:
  all TargetTypes definitions + 345 weapon refs are lowercase; treat
  it as engine-adjacent vocabulary, never capitalize).
- **Cross-actor namespaces are sacred**: voice sets, notifications, shared
  art are NEVER renamed with a unit. `tools/rename/safe_rename.py` protects
  audio files and `VoiceSet:` lines structurally.
- **Weapon names must include the full actor id as a prefix**
  (design 2026-07-16): weapon ids follow the pattern
  `<actor_id>_<weapon_descriptive_name>`. The actor id prefix makes it
  immediately clear which actor owns the weapon and prevents name
  collisions across factions. Examples:
  `td_gdi_commando_sniper`, `cabal_tarantula_cannon`,
  `ra2_soviets_conscript_ak47`, `latinsyndicate_topolsilo_nuclear`.
  - **Weapon class templates keep their PascalCase `^` prefix**:
    `^SmallArms`, `^MediumCannon`, `^HeavyMissile`, `^RA2FlakWeapon`,
    `^LaserWeapon`, etc. These are shared class templates, not actor
    weapons, and are NOT prefixed with an actor id.
  - **Faction-level weapon templates** (shared across multiple actors of
    one faction) use PascalCase with the faction prefix:
    `^CabalMissile`, `^RA2RadShell`, `^RA2EliteEffects`. These are also
    NOT prefixed with a full actor id since they serve multiple actors.
  - **Elite weapon variants** append `_elite` — this is the ONLY accepted
    suffix for elite weapons, regardless of naming style. Legacy PascalCase
    weapons that still use the `E` suffix (e.g. `BorisAKME`) must be
    migrated to `_elite` when touched. See §16.3 for the full convention.
    Example: `ra2_soviets_conscript_ak47_elite`, `BorisAKM_elite`.
  - **EMP weapon variants** append `_EMP`: `steel_consortory_emp_cannon`,
    `ra1_tesla_tank_zap_EMP`. This suffix identifies weapons whose
    primary function is to disable vehicles via EMP effect. It is
    primarily used by Steel Consortium but may appear on other factions.
  - **AA weapon variants** append `_AA`: `RA2HoverMissile_AA`,
    `SWAWingGun_AA`. This suffix marks the air-only sibling of a
    **dual-weapon actor** — an actor/template that equips two separate
    weapons via different `Armament` traits, one ground-capable (e.g.
    `RA2HoverMissile`, `ValidTargets: Ground, Water`) and one air-only
    (e.g. `RA2HoverMissile_AA`, `ValidTargets: Air`), typically the
    latter `Inherits:` the former. An Anti-Air Tank with both a ground
    cannon and an AA missile is the canonical example.
    **Do NOT** apply `_AA` to a weapon just because its own `ValidTargets`
    happens to be `Air`-only — a standalone AA-only weapon used by a
    dedicated AA unit/structure with no ground-capable sibling on the
    same actor (e.g. a SAM Site) stays unsuffixed. A single weapon whose
    own `ValidTargets` already covers both `Ground` and `Air` (one
    combined weapon, not two) also does not get `_AA`.
  - **Upgraded weapon variants** append `_upgraded` or the upgrade name:
    `cabal_artilleryspider_shell_upgraded`.
  - **Combined suffixes** follow this order:
    `<base_name>_<doctrine/upgrade/variant>_EMP_AA_elite`
    (e.g. an elite EMP anti-air weapon). The base descriptive name comes
    first, then doctrine/upgrade/variant suffixes, then `_EMP`, then
    `_AA`, then the rank tier (`_elite`) last.
  - **Migration**: per faction via `tools/rename/rename_map_<faction>.yaml`
    + `tools/rename/safe_rename.py`, verified with
    `tools/audit/dump_resolved.py` before/after diffs (must be empty).
    Weapons shared across multiple factions (in theme Shared/ packs) stay
    as-is and are NOT renamed after any single actor.

Migration is per faction via `tools/rename/rename_map_<faction>.yaml`
(curated, reviewed) + `tools/rename/safe_rename.py`, proven behavior-preserving
with `tools/audit/dump_resolved.py` before/after diffs (must be empty).

## 2. Content pack layout

```
mods/cameo/ContentPacks/<Theme>/<Faction>/
  content.yaml            # the pack's manifest (include list) — root level
  yaml/                   # ALL MiniYaml, split per concern:
    faction.yaml buildings.yaml defenses.yaml infantry.yaml vehicles.yaml
    aircraft.yaml naval.yaml upgrades.yaml promotions.yaml husks.yaml
    templates.yaml        # faction-local ^templates only
    weapons.yaml          # ONE weapons file per faction
    sequences.yaml        # ONE sequences file per faction
    ai.yaml               # per-faction bot data (once the AI split lands)
  files/                  # ALL assets in per-type subfolders:
    icons/ sprites/ voxels/ sounds/
  translations/en.ftl     # Fluent (not MiniYaml, stays its own folder)
```

**Structure decisions (design consultation 2026-07-16):**
- **The `yaml/` folder name STAYS.** It was decided 2026-07-12 and rolled
  out across all 27 packs on 2026-07-14; renaming again is churn without
  behavioral gain. (If it were greenfield, `data/` would be marginally
  more descriptive — not worth a second migration.)
- **The per-concern file split STAYS — do NOT merge rules files.** With
  multiple concurrent contributors (maintainer + 333ggg + two AI agents),
  small per-type files minimize merge conflicts, keep audits targeted,
  and make wrong-section placement detectable. One merged rules.yaml
  would undo all three.
- **The standard file set above is CLOSED.** A pack may omit a file it
  doesn't need, but must not invent new names — `audit_packs.py`
  enforces the set, so tooling can always find everything.
- **content.yaml becomes machine-generated** (`tools/packs/gen_content.py`):
  regenerated from the files on disk, deterministic ordering; the audit
  fails on drift. Nobody hand-edits include lists.
- **Wrong-section rules** (the "actor in the wrong pack/file" bug class):
  every actor id in a pack MUST carry the pack's faction prefix (Shared
  packs excepted); actors live in the file matching their class template
  (naval.yaml holds ships AND naval yards — existing rule; husk variants
  in husks.yaml; upgrade/promotion actors in their marker files).
  `audit_packs.py` checks both.

- **naval.yaml holds ALL naval content: every ship AND the naval yards**,
  even though naval yards normally count as buildings. The lobby option
  that unlocks the naval prerequisite can then also dynamically load (or
  skip) the whole naval asset set based on the lobby setting.
- Weapons move into a pack only when used **exclusively** by that faction
  (computed through warhead sub-weapon and Inherits closure); shared
  weapons stay in the theme/shared files.
- Splits are done with `tools/packs/split_faction.py`, byte-preserving,
  and verified: merged actor/weapon/sequence registries must be identical
  before and after, and the faction's resolved closure diff must be empty.
- mod.yaml `Include:` order defines the lobby faction order.

**End goal — dynamic faction loading.** Content packs exist so the game can
load ONLY the factions picked in the lobby (and only what the active
shellmap needs) instead of every actor at boot: Cameo is the ultimate
crossover RTS and will keep growing — at peak it consumed 12 GB of RAM,
locking out 8 GB and 4 GB players before the main menu. Therefore packs
must become COMPLETELY self-contained, loadable without cross-dependencies:
- a separate ai.yaml per faction inside its pack;
- all game files the faction needs — sprites, voxels, icons, sounds —
  inside the pack, cleanly separated into per-type subfolders;
- shared content lives only in theme Shared/ packs or the core;
- a future audit walks every pack, verifies which files are actually used,
  and deletes the unused ones.

### Content installer architecture

Cameo's optional original-game downloads are owned by the hidden
`mods/cameo-content/` installer mod. The primary `mods/cameo/mod.yaml` uses
`ContentInstallerFileSystem`, keeps boot-critical mounts under
`SystemPackages:`, and leaves `ContentPackages:` empty so content installation
is opt-in through the Manage Content button. Installer manifests live under
`mods/cameo-content/installer/` and are mounted through the hidden mod's
`Downloads:` and `Sources:` entries. The hyphenated `cameo-content` mod
identifier is a deliberate engine-convention exception to Cameo's normal
underscore-only in-mod naming rule.

## 3. House stat formulas (audited as F1–F18, `audit_stat_formulas.py`)

Reference-clean units: **TD GDI Archer** (`gdiarcher`), **Ordos Raider**
(`raider.ordos`).

| rule | formula |
|---|---|
| Repair | `Repairable.HpPerStep = HP / 20` (non-infantry) |
| Self-heal | **TICKS TO FULL, not a per-step amount** (maintainer 2026-09-07): every unit fully self-heals in **2500 ticks (100 s)**; **infantry in 1250 ticks (50 s)** — exactly 2x. Applied EVERY tick with a fractional accumulator, so HP is no longer constrained by the divisor. Always active while damaged (`StartIfBelow: 100`). Infantry never has Repairable. See §Regeneration. |
| Upgrade shields | **Shield regen is ALWAYS 2x the HP regen rate**, measured as %-of-max-HP per tick (`GrantsShield.PercentageRegenAmount 2` per `RegenInterval 25` = 0.08%/tick against HP's 0.04%/tick — the rule already holds in the shipped trait). Shield ramp is **2x as long** as the HP ramp. |
| Defense vision | `RevealsShroud.Range = weapon range` |
| AA / advanced defense detection | `DetectCloaked.Range = weapon range / 2` |
| Defense power | `Power.Amount = -(Cost / 20)` |
| Vehicle turning | `TurnSpeed = Speed / 5`, `Turreted.TurnSpeed` equals it. The value is generated into YAML by the balance tooling and consumed as an authored integer `WAngle`; it is not derived at runtime. Speed is now on a step of 1, so the generator rounds the derived target and the audit records the permitted tolerance. |
| Turretless (AttackFrontal) vehicles | `TurnSpeed = 2 × Speed / 5` — the former artillery exception was dropped 2026-07-10 (data check: turretless artillery split 24 at 2×, 18 at 1× — no real pattern) |
| Stationary defenses | **`Turreted.TurnSpeed = 2 × Speed / 5` applied to the TURRET, not a chassis** (maintainer 2026-09-07). A defense has no hull to turn, so the turretless doubling lands on the turret instead — a defense therefore tracks as fast as a frontal-weapon tank, and markedly faster than a tank TURRET. `Speed` here is the speed the emplacement would have as a mobile unit of its class. |
| Units that DEPLOY into an immobile form | **rotation DOUBLES while deployed** (maintainer 2026-09-07) — the deployed state is a stationary defense and takes the defense rule. Applies to `td_gdi_defenserig`, the Terran siege tank, the Matador and every other deploy-to-immobile unit. |
| Husks | **the only actors with no turn rate at all.** Everything else that can face a direction has one. |
| Turreted artillery / fire support | Archer firing-slow: `GrantConditionOnAttack(firing)`, 50% Speed/Turn/TurretTurn multipliers, `RevokeDelay = weapon ReloadDelay / 2` |
| Fighters & bombers (by template) | `Aircraft.TurnSpeed = Speed / 15` (frontal-weapon craft 2×) |
| Helicopters & spaceships (by template) | `Aircraft.TurnSpeed = Speed / 5`, like vehicles (design 2026-07-10; 45 of ~55 helicopters already comply) |
| AA range bonus | **ONLY** `scout_vehicle`, `armed_troop_transport`, `anti_air_vehicle`: AA range = **1.5 × ground range**, generated by `gen_weapon_template.py`. Every other class: same range both domains. `mobile_bunker`: no air-capable armament at all. (maintainer 2026-09-08; forgotten_m113adats is reference-clean at 5606 / 8409) |
| AA weapons | a weapon whose ValidTargets include Air must have ≥1 damage warhead that hits Air (inheritance-resolved) |

**Building stat templates (design 2026-07-13).** All non-defense
buildings must derive their core stats from the appropriate template in
`mods/cameo/rules/defaults.yaml` (`^BaseBuilding`, `^RadarBuilding`,
`^IsTechnoBuilding`, `^IsAircraftFactory`, `^RepairFacility`, etc.). A
child actor must **not** duplicate a value that its template already
provides (e.g., `Armor`, `Power`, `Health`, `RevealsShroud`,
`DetectCloaked`). Overrides are allowed **only when justified by a
special faction mechanic** (for example, the TD Nod Temple of Nod or the
GDI Advanced Communications Center count as a tech building but gain an
add-on that turns them into a superweapon, so they use the lower
`^IsTechnoBuilding` health and then apply a 50% damage reduction to end
up equivalent to the `^Superweapon` template). Defenses are exempt because
each faction's defenses are individually balanced against their
weapons and roles, but they still obey the **defense power** rule above.

**The AA range law (design 2026-09-08 — REPLACES the dual-weapon AA law
of 2026-07-11, which granted the bonus to `^SupportVehicleTemplate` and
said nothing about scouts).** THREE classes, and only these three, may
carry an anti-air armament whose range exceeds its ground twin's:
**`scout_vehicle`, `armed_troop_transport`, `anti_air_vehicle`**. For
those, AA range = **1.5 × ground range**. Every other class uses the
SAME range against both domains — a Mammoth-class `high_tech_tank` gets
no AA range bonus, and the shipped tree already obeys that (measured
2026-09-08: every mammoth's cannon and missile pod share one range,
6412/6412, 6141/6141, 6340/6340). Sole legacy exception: the Ordos Anti
Air Trooper, a dedicated AA special.

**`mobile_bunker` may not have an air-capable armament at all** — a
fireport transport's anti-air is the infantry riding inside it. Members
are identified by a resolved `AttackOpenTopped` trait (maintainer
2026-09-08); 16 buildable vehicles qualify, ten of them the former
`line_breaker` Battle-Fortress family.

⛔ **The 1.5× is NOT a template property and CANNOT be made one.**
`Armament.MaxRange()` (Armament.cs:215) takes no target, and
`IRangeModifier.GetRangeModifier()` (TraitsInterfaces.cs:480) takes no
target either — `RangeMultiplier` scales EVERY armament on the actor.
Per-target range is resolved one level up, in
`AttackBase.GetMaximumRangeVersusTarget` (AttackBase.cs:336), which
loops the armaments and SKIPS any whose weapon is not valid against
that target. **The twin armament IS the engine's mechanism for a
different range vs air — it is not duplication to be collapsed.**
Collapsing the twins into one weapon yields ONE range for both domains,
the opposite of the intent. Making a single armament vary by target
requires forking `AttackBase` through the cameo-engine pipeline; that
investigation is queued to Astra, not assumed.

The number itself is GENERATED, never hand-typed: `AA_RANGE_MULT` in
`gen_weapon_template.py` writes the AA twin's `Range` from the ground
twin's. ⚠ §8c applies — the generator must WRITE the value and the
audit must assert it on a RESOLVED weapon, because `ScaledBullet`
derived Inaccuracy/Speed for weeks and reached zero weapons when
templates also wrote literals. Enforced by `audit_aa_range.py` as a
LOWER-ONLY ratchet.

Whenever a unit carries both a ground weapon and an AA weapon, the two
must remain **mutually exclusive in ValidTargets** (ground weapon:
`Ground, Water` only — never Air; AA weapon: `Air` only), otherwise the
missile templates (whose ValidTargets already include Air) double-dip
and the unit deals twice the intended anti-air damage. Reference-clean
pattern: the RA1 Soviet Flak Truck. Rocket INFANTRY never gets a second
AA weapon — the missile class templates already target Ground+Air with
one weapon (TS rocket infantry pattern).

**AA weapon construction — always inherit the ground twin (house
rule, codified 2026-07-12; 76 existing AA weapons follow it).** An AA
weapon is NEVER redefined from scratch. It `Inherits: <the ground
weapon>` and then only overrides what differs: `ValidTargets: Air`,
the AA `Range`, and each damage warhead flipped to `ValidTargets:
Air` (the DamagesConcrete / CreateEffect / smudge warheads are left
alone). This keeps the AA's damage, class mix, reload, projectile and
trail identical to the ground weapon by construction — never
hand-copied. Reference: `ArmoredCarMGAA: Inherits: ArmoredCarMG`.
Corollary: shared projectile behaviour (launch angle, turn rate,
trail — §3 rocket rules) belongs in ONE faction/family missile
template that the ground weapons inherit last, so the AA twin picks it
up automatically through the ground weapon (e.g. `^CabalMissile`).
Never copy a projectile block across weapons.

**Weapon grouping order in YAML (design 2026-07-13).** Within a
faction's `weapons.yaml`, every weapon family must be kept in a strict
order so upgrades and twins are easy to audit and impossible to miss:

1. **Basic weapon** (the unupgraded ground version).
2. **Elite / veteran twin** if any.
3. **Anti-air twin** (inherits the basic weapon, only changes
   `ValidTargets` and AA range).
4. **Upgrade variants** in the order they are unlocked — if a unit has
   multiple upgrades, list the combined versions after the single
   upgrades. Reference pattern: the Consortium Quantum Missile Trooper
   weapons show the full progression of basic → elite → anti-air →
   upgrade → combined upgrade.

The same rule applies inside an actor's `Armament` blocks: the basic
`Armament@PRIMARY` must come first, then the upgraded armament directly
below it (e.g., `Armament@UPGRADE` right after `Armament@PRIMARY`), then
garrison variants, then anti-air variants. Never scatter related weapons
across the file.

**Weapon mount offsets (design 2026-07-11 — always apply).** Every
firing armament needs a `LocalOffset` so the muzzle sits at the barrel,
not the actor's ground-center. For INFANTRY the default is
**`LocalOffset: 128,0,256`** (128 forward, 0 sideways, 256 up ≈ chest
height) — the mod-wide most common value. Apply it to every non-garrison
infantry armament that has no offset of its own; garrison armaments
(`Name: garrisoned`) keep none (they fire from the building's port).
A missing offset is not cosmetic for arcing/launched projectiles: the
round spawns at ground level and can explode under the unit's feet —
this is why the CABAL Rocket Cyborg could not shoot. When creating or
editing ANY infantry, set the offset. Vehicles/aircraft use
weapon-specific `LocalOffset`s at their barrels (not this default).

**Alternating (twin-muzzle) offsets.** A `LocalOffset` with TWO triplets
(six values), e.g. **`LocalOffset: 128,-64,256, 128,64,256`**, gives two
fire points that the weapon alternates between — the left barrel
(`-64` sideways) then the right (`+64`). Use it for any dual-weapon /
twin-barrel unit (the CABAL Devout's twin chainguns, gatling arms, etc.)
so bursts visibly alternate left/right instead of stacking on one point.
The single-triplet default `128,0,256` is for one centred muzzle.
**Match a unit to its analogue.** When two units share a weapon family,
copy the reference unit's offset AND muzzle setup wholesale (the CABAL
T800 gatling was aligned to the Yuri Gatling Trooper's `544,100,256`).
Note the muzzle style can differ: the Gatling Trooper shows a visible
tracer projectile and no `WithMuzzleOverlay`, whereas the T800 carries
`WithMuzzleOverlay` + `MuzzleSequence: muzzle` (a sprite muzzle flash) —
pick one style per look and keep the pair consistent.

**Preserve a unit's unique projectile when reforging its weapon.** A new
weapon that only `Inherits:` a class template (e.g. `^LightChemical
Weapon`) takes that template's plain projectile and DROPS any custom
`Projectile:` the old weapon had (Image/Speed/Palette/Inaccuracy). The
CABAL Dissolver lost its `tsdissolvereffect` spray this way in the Batch
2a rebuild. Always carry the old `Projectile:` block over (or restore it
from git) when replacing a unit's signature weapon.

**Laser beams — two colours, scaled by damage (design 2026-07-13).**
Every `LaserZap`/beam weapon uses **two colours**: a `Color` (outer beam)
and a `SecondaryBeam` (`SecondaryBeamColor`, inner core). Never a single
thin line. **Both the beam width AND the colours scale with the weapon's
damage** — a bigger-damage beam is thicker and reads as more dangerous
(brighter/hotter core, deeper outer). Rough CABAL ladder: turret-class
lasers `Width ~18–24` / secondary `~8–12`; heavy single-shot lasers
(Core Defender) thicker still, but even the heaviest keeps scaling rather
than maxing out. **CABAL beams are a mix of purple + dark blue** (e.g.
outer `~6622CCCC`, inner `~9977FFEE`) — never too thin. Dual-beam units
(Manticore) must **spread the two beam offsets apart** so the pair reads
as two beams, not one. Pair every beam with a colour-matched impact
effect (3 damage-scaled ground-impact levels for CABAL lasers) + a sound.

**Obelisk / laser sound map (design 2026-07-13).** The three obelisk
reports are NOT interchangeable:
- **`obelmod1.aud`** = Tiberian **Sun** obelisk — the Obelisk of Light,
  the Obelisk of Darkness, and the CABAL Obelisk building weapon, and the
  Laser Spider.
- **`obelcor3.aud`** = the Core Defender's weapon; also DarkObeliskLaser
  and both Commando plasma weapons (do not change these).
- **`obelray1.aud`** = Tiberian **Dawn** obelisk — **NOT allowed on any
  TS unit** unless explicitly specified. A weapon that only
  `Inherits: ^LaserWeapon` is using this TD version; override it for TS.
- Smaller/turret lasers use the laser-turret report **`lastur1.aud`**.

**TS rocket projectiles — launch straight up (design 2026-07-11,
replicating Shattered Paradise).** Tiberian-Sun-style rockets fire
near-vertically then home down onto the target. On the `Missile`
projectile set **`MinimumLaunchAngle: 255` and `MaximumLaunchAngle:
255`** (255 ≈ 90° in our WAngle scale; SP uses the same 255 = "90
degrees"). A steep launch overshoots close targets unless the missile
can turn fast enough, so ALWAYS pair it with a high turn rate —
**`HorizontalRateOfTurn: 128` / `VerticalRateOfTurn: 128`** (SP's
value; our `^LightMissile` default of 40 is too slow and causes the
overshoot). The Guardian GI's rocket was the reference bug: launch 200
with the default turn 40 always overshot at short range; fixed by
raising its turn to 128. Set both angle and turn per-weapon (never edit
the shared `^*Missile` templates, which serve all factions).

Unit classification is authoritative from the **class templates in
defaults.yaml** (`^HighTechTankTemplate` ⇒ vehicle, whatever the render
traits say). Power plant vision currently: 4c0 small / 5c0 advanced —
a project-wide size/cost scaling rule is TODO.

## 3a. The dual-armament laws (maintainer, 2026-09-14)

Four rulings about actors that carry more than one weapon. They were prompted by the
per-armament reference map, which showed the GDI APC, Battle Tank and Mammoth Tank carrying two
weapons whose targets came out within a few percent of each other.

### 3a.1 An AA split is ONE weapon; its free bonus is scoped by class

> *"the APC anti ground and anti air flak should not have any different damage since it's the
> same weapon (the only reason why we had to split it was a necessity because we can't otherwise
> have 1.5x range against air) so yes for those dual weapons that are only anti ground and anti
> air versions they must be identical except for the 1.5x range"*

A `_AA` weapon that exists only because OpenRA cannot give one armament a longer reach against
air is **not a second weapon**. `ReloadDelay`, `Burst`, `BurstDelays` and `MinRange` match its
ground twin. Maximum AA range is normally 1.5x ground range. AA damage is equal for
`scout_vehicle` and `armed_troop_transport`, and doubled for `anti_air_vehicle` and
`anti_air_ship`. The Yuri staged-range exception below remains explicitly scoped to its two
actors.

⛔ **`MinRange` NEVER SCALES** (maintainer, same ruling): *"Min Range never scales! That one is
always constant - because no range multiplier changes min range."* A range multiplier moves the
maximum reach and nothing else, so the AA half must carry the SAME `MinRange` as its ground twin.
Scaling it by 1.5x alongside `Range` looks tidy and is wrong; it silently widens the dead zone
the unit cannot shoot into.

⚠ **MEASURED 2026-09-14: the tree does not obey this.** 63 `_AA`/ground pairs exist:

| | pairs | |
|---|--:|---|
| compliant | **36** | identical apart from a 1.5x maximum range |
| **value violations** | **21** | the halves are not the same weapon at all |
| range-ratio violations | 6 | same weapon, reach is not 1.5x |

⛔ And the violations do not even share a direction. `RA2GattlingMG1/2/3` and
`YuriGatlingCannonMG1/2/3` give the AA half **double** damage (4000 vs 8000); the Lunar and Naxi
laser family gives it **half** (8000 vs 4000); `SteelMantaHunterCannons` scales damage AND reload
by 1.5x; `Rocket_stealth` makes AA weaker (14500 vs 12000) on a 1.19x range. Reach ratios of
1.0x, 1.35x, 1.429x, 1.688x, 1.808x and 2.0x all appear. Four pairs - `Naxis_Komet`, `eden_EMP`,
`edenTiger_EMP` and `plymouth_EMP` - scale `MinRange` by 1.5x as well, which is the specific
mistake ruled against above. There is no convention here to preserve; pinned by
`aa_split_pairs_compliant`.

**⚠ THE GATLING EXCEPTION** (maintainer, 2026-09-14): *"This is only for the gatling tank and
the gatling cannon right? Those have their own unique gatling behavior and are an exception.
Anything else follows the rule."* Their AA reach RAMPS with the spin-up stage instead of holding
a flat 1.5x - **MG1 1.350x, MG2 1.429x, MG3 1.500x** - and that ramp is deliberate, so those
weapons are exempt from 3a.1's flat ratio. Their doubled AA damage is correct: both actors are
the dedicated-AA role.

**⭐ WHY THE THREE STAGES EXIST AT ALL** (maintainer): *"It's because the Yuri gatling switches
weapons that can play a different sound effect between the 3 states so it's only for the two
things."* The stages are a SOUND mechanism - three weapons so the spin-up can be heard - not a
balance device. ⚠ Which is worth keeping in mind when the ramping reach is eventually reviewed:
the ramp is a side effect of a presentation feature, so it was probably never chosen as a
balance value. It stands as an approved exception either way, but that is the reason it should
not be copied onto anything else.

⛔ **THE EXEMPTION IS PER ACTOR, NOT PER WEAPON - RULED 2026-09-14.** *"Only the Yuri gatling
tank and the Yuri gatling cannon! Anything else is not approved and requires their own weapon."*

`YuriGatlingCannonMG1/2/3` and the six `YuriGatlingTankMG*` wrappers are private to their actors.
PR #402 (`102645047`) completed the split: it pinned effective range and damage on both private
families, rewired the Tank's six armaments, and removed the historical unconditional actor
multipliers. `RA2GattlingMG1/2/3` remain shared by `ra2_c_abram`, `ra2_c_hum`, `ra2_c_hum2`,
`ra2_c_ifv` and `ra2leopard`; those consumers remain outside the Yuri exception.

⛔ **THE RUNTIME RANGE AND FIREPOWER DIFFERENTIATION WAS PRESENT BUT INVISIBLE TO THE LEDGERS -
CORRECTED 2026-09-15.** `yuri_gatlingcannon` carried an unconditional 150% `RangeMultiplier`,
while `yuri_gatlingtank` carried 108% range and 75% firepower. The Cannon had no equivalent
unconditional firepower modifier. Runtime therefore already produced different effective reach
and Tank damage. The balance ledgers read weapon-local `Range` and `Damage` and ignored these
actor multipliers, so they reported the shared base values for both actors. Private wrappers
preserve the existing effective values directly on each weapon and make the distinction visible
to the pipeline; the actor multipliers can then be removed without changing runtime behavior.

⚠ They do not even use the same stages: `ra2_c_ifv` carries MG1 and MG2 only, `ra2leopard` carries
MG1 alone beside its `RA2120mm` cannon, and only `yuri_gatlingtank` uses all three.

**⭐⭐ THE AA BONUS IS SCOPED BY CLASS** (maintainer, 2026-09-14). The question was whether the
AA half carries +100% damage; the answer depends on whose job anti-air is:

| class | the AA half gets | why |
|---|---|---|
| `anti_air_vehicle` | **+50% range AND +100% damage**, priced at zero | anti-air IS the role |
| the **anti-air SHIP** template (Sea Scorpion, Aegis Cruiser) | **the same as anti_air_vehicle** | the naval form of that role |
| `scout_vehicle` | **+50% range, SAME damage** | it carries AA; it is not the AA |
| `armed_troop_transport` | **+50% range, SAME damage** | likewise |
| any other class | may not carry an AA split at all | |

> *"Dedicated anti air vehicle will get the +100% damage against air because that's their role,
> scout vehicle and armed troop transport should only have the +50% range but the same damage ...
> don't forget we also have the anti air ship template like for the sea scorpion, aegis cruiser
> etc, they should get the same bonus as the anti air vehicle class."*

⚠ **THE MEASUREMENT THAT SHAPED THIS.** Of 63 pairs, **36** comply with identical damage and
only **2** with double; 46 carry identical damage today. A blanket +100% would have made 36
correct pairs wrong, required editing 61 of 63, and INVERTED the rise-only
`aa_split_pairs_compliant` ratchet. Scoping it by class keeps the common case intact and gives
the dedicated AA classes something the others do not have - which is the point, because a free
double-damage air weapon on every APC would leave `anti_air_vehicle` with no identity.

⚠ `class_anchors.json` now contains a provisional `anti_air_ship` anchor. Remaining work is
fitting and maintainer sign-off, plus separately reviewed Aegis/Sea Scorpion weapon corrections.
Do not recreate the class or treat its provisional specification as approved.

⚠ **THE AEGIS CRUISER, ordered the same day**: *"remove the upgrade that unlocks the anti ground
weapon and just make it the default AG / AA pair with the +50% range and +100% damage"*. Measured:
`RA2Medusa_AA` 13,500 (Air) against `RA2MedusaAG` 9,000 (Ground/Water) is **already exactly 1.5x**,
the damage is **identical at 30,000**, and the AG armament is gated behind `upra2aegismissiles`.
So the change is precisely two things - drop that condition, and double the AA half's damage to
60,000 - both yaml, both needing the pipeline and a boot gate. ⚠ The **Sea Scorpion is not a
clean pair**: `SeaScorpion_AA` 13,500 against `RA2FlakTrackGun` 5,528 is **2.44x**, and its ground
weapon is SHARED with the flak track, so it cannot be renamed or rescaled without touching another
unit. It needs its own decision.

**⭐ WHICH CLASSES MAY CARRY AN AA SPLIT AT ALL** (maintainer, 2026-09-14: *"anti air vehicle,
scout vehicle and armed troop transports get this bonus anti air range ... It should have been
written down into the documentation"*). Exactly **three**:

| class | examples named by the maintainer |
|---|---|
| `anti_air_vehicle` | Allied heavy anti-air tank, Soviet gatling tank, flak truck |
| `scout_vehicle` | Nod buggy, Japanese armored car |
| `armed_troop_transport` | GDI APC, BTR-80 |

⚠ **`scout_vehicle`'s class anchor currently says the opposite** - *"Fast recon. MG/autocannon.
Never the AA (that's anti_air_vehicle)"* - which is now superseded: a scout vehicle may carry the
bonus AA reach. The comment is corrected in `class_anchors.json` in the same commit as this line,
because a stale statement left standing somewhere else is exactly how two documents come to look
equally authoritative.

⛔ **AN OPEN QUESTION SITS ON TOP OF THIS ONE - see the box at the end of 3a.1.**

### 3a.1b ⭐ THE APPROVED AA FIXES (maintainer, 2026-09-14)

Every one of these was put to the maintainer with its numbers and approved:

| finding | count | ruling |
|---|--:|---|
| AA half at **0.5x** damage - the Lunar/Naxi laser family | 5 | *"maybe it was accidentally reversed? but yeah this is not intended"* → **fix** |
| identical damage but the reach ratio is not 1.5x | 6 | *"yes always"* → **fix to exactly 1.5x** |
| `apparition.ixian` at **2.0x** reach, `ixian_farasha` at **1.0x** | 2 | *"yes"* → **same treatment** |
| gatling spin-up ramp (1.350x / 1.429x / 1.500x) | 6 weapons | **exempt**, but only on `yuri_gatlingtank` and `yuri_gatlingcannon` |

⚠ All are yaml balance numbers: pipeline and boot gate, never a hand edit.

**⭐ IS THE BONUS AA REACH MANDATORY?** *"it should be mandatory where possible but it might be
that the units from scout or transport classes have a weapon that cannot attack air at all, or get
an additional weapon that can't attack air like the nod buggy that gets a flamethrower as an extra
weapon which can never hit air. Or a tank cannon like for the japanese hovercraft APC which only
has one weapon that can attack air while it has another that is only anti ground."* So: mandatory
for a weapon that CAN engage air, and simply inapplicable to one that cannot. A unit in those
three classes may carry extra ground-only weapons without breaking the rule.

### 3a.2 Weapons that can hit the same target MUST share one range

**⭐ THE EXEMPTION IS RULED: FIXED-WING AIRCRAFT ONLY** (maintainer, 2026-09-14): *"only for
fixed wing aircraft because they will always fly in range since they can't stop mid air unlike
helicopters so they will always use the long range and the short range weapon together by flying
over the target. So for fighters and bombers that rule doesn't exist but anything else that stops
to attack it must be the same range."*

The mechanism is the reason: a unit that STOPS to attack fires from the range of its longest gun,
so a shorter gun on it is dead yaml. A fighter or bomber cannot stop - it flies over the target -
so it necessarily closes to the short weapon's range and both weapons land. Unequal ranges are
therefore meaningful on a fixed-wing aircraft and meaningless on everything else, **helicopters
included** (a Hind can hover, so it obeys the rule).

⚠ This is what makes `ra1_soviets_yakscoutplane` (1,840 bomb / 7,000 chaingun) and
`ra1_soviets_su57attackbomber` legal, and it hands them to 3a.9's DISJOINTED-same-target case:
separate ranges, both hitting the victim, so each is solved on its own and then takes 1/n.



> *"the unit will always try to fire at maximum range so if they are different it will mostly use
> one but not both weapons so to maximize effectiveness it is imperative that ALL WEAPONS THAT
> CAN HIT THE SAME TARGET MUST ALWAYS HAVE THE EXACT SAME RANGE AND THE ONLY EXCEPTIONS ARE THOSE
> ANTI GROUND ANTI AIR COMBOS WITH THE 1.5X RANGE"*

This is a project consistency rule with a mechanical purpose: same-target armaments should
participate together predictably instead of depending on the attack trait and order path.
`AttackFrontal` deliberately approaches the shortest active maximum range, so a shorter weapon
is not universally inert; other attack paths can open fire at the longer range and delay the
shorter armament. Equal range removes that mode-dependent split and makes the combined value
model match the intended simultaneous use.

⚠ **This law deliberately DEPARTS from the source material.** Measured across the 935 reference
actors that carry two weapons, only **31.9%** give them equal range - the originals routinely
split reach. Cameo chooses predictable simultaneous use across its attack traits instead.
Fidelity loses to function here, and that is a decision, not an oversight.

⚠ **MEASURED on the tree**: of 522 actors with 2+ priced armaments, **387 same-target groups
share one range (54.0%) and 330 carry a spread**, the worst 409x. ⛔ The 330 is an UPPER bound,
not a defect count: it still includes aircraft bombs (`TSBomb`, `OrniBomb`, `NaxiCowDrop`) and
condition-gated `elite` replacements, neither of which competes for a target at maximum range.
**The exemption list is an open design question** - see `same_target_range_groups`.

### 3a.3 Simultaneous armaments SUM - the actor-level cell must not be WITHHELD

> *"for the balance formula you need to count both weapons if they are truly activated at the
> same time at the same ground target like the mammoth tank cannons and missiles so the combined
> DPS is what counts and it is what should be displayed in the reference data instead of the
> WITHHELD status"*

Where two armaments genuinely fire together at one target, the priced quantity is their SUM, and
the reference map must show it rather than abstain. Abstention is for armaments that cannot be
compared, not for ones that add.

**APPLIED 2026-09-14** (`build_reference_report.firing_together`). The maintainer read the map
again and the verdict was blunt - *"all withheld!"* - so the combined figure is now computed and
displayed. `td_gdi_mammothtank` reads **32,000 combined, 2 guns -> 82,526**; `td_gdi_battletank`
**16,000 -> 36,705**. Thirteen actors in the classic four qualify.

⛔ **FOUR THINGS MUST BE TRUE BEFORE A SUM IS PRINTED**, and each one exists because skipping it
produces a number that is wrong in a specific, checkable way:

1. **AS BUILT.** Upgrade-gated armaments are excluded. `td_gdi_battletank` carries five armaments
   and its machine gun is gated on `td_gdi_upgrade_armorpiercingbullets` with no `!` twin, so it
   is an EXTRA gun bought later rather than a swap: the maximum is three and the as-built loadout
   is two. Both numbers are true and only one of them describes the unit being priced.
2. ⛔ **AN AA SPLIT IS ONE WEAPON** (3a.1). `td_gdi_apc_apcgun` and `td_gdi_apc_apcgun_AA` are a
   single gun that OpenRA forced into two armaments, and adding them would double the APC's
   firepower outright. Five actors in the classic four carry such a twin - both APCs, the Allied
   heavy AA tank, the flak truck, and the Humvee Mk II with two of them.
3. ⛔ **THEY MUST REACH A COMMON TARGET.** The test is that the INTERSECTION of every armament's
   domain is non-empty: `ground` + `both` share the ground and sum; `ground` + `air` share nothing
   and abstain, because a bomb and an anti-air missile are never over the same target
   (`ra1_allies_rapierjumpjet`, `td_gdi_firehawk`). ⚠ Connectivity is the WRONG test - ground,
   air and both form a connected chain with no target all three can hit.
4. **EVERY ARMAMENT MUST HAVE A REFERENCE.** A PARTIAL sum is the worst outcome available: it
   looks complete and reads low, so the unit would be priced as though one of its guns were free.

⚠ **CADENCE DOES NOT SUM.** Reload, burst and burst delay stay WITHHELD on a multi-gun row and
that is correct - two guns firing together have two reload delays and no single one describes
them. Only DAMAGE adds. The range cell shows the shared reach when 3a.2 holds and withholds when
it does not, which turns that column into a live compliance check: **six of the thirteen combined
actors disagree on range**, `td_gdi_battletank` by 38 WDist (5,438 vs 5,400) - too small to be
deliberate, which is exactly the kind of drift 3a.2 exists to catch.

### 3a.4 Why a cannon and a missile land on almost the same target

> *"compare 41,528 for the missiles with 40,997 with the cannons! ... Both weapons even when they
> use different references have almost the same damage ... So what exactly is going on here?"*

⛔ **FIRST, A CORRECTION I OWE THIS SECTION.** An earlier draft answered this with "the sources
say 1.71x" - a median cannon-vs-missile DPS ratio measured across every reference Mammoth Tank in
the **INI corpus** (CnC Reloaded, Twisted Insurrection, Mental Omega, RA2, DTA Classic, Rise of the
East). That number is real, and it is **the wrong population**: none of those sources votes on
`td_gdi_mammothtank`. Its voters are OpenRA peers. Quoting a corpus-wide statistic to explain a
specific actor's pairing is the same class of error as reasoning from a trait's name instead of its
source - see `mammoth_named_dual_slot_separation_ratio`, which now says so on its face.

**THE ACTUAL VOTERS, read out of `armament_pairing.json`:**

| source | cannon | missile | missile:cannon |
|---|---|---|--:|
| Combined Arms | `130mmTD` 12,000 / 85t | `MammothTusk` 14,000 / 75t | 1.17x |
| OpenRA Tiberian Dawn | `120mmDual` 8,000 / 48t | `MammothMissiles` 10,000 / 60t | 1.25x |
| **geometric mean** | **9,798** | **11,832** | **1.21x** |

By RATE rather than per cycle it is smaller still - CA 141.2 vs 186.7 (1.32x), Tiberian Dawn
**166.7 vs 166.7 (exactly 1.00x)**, geometric mean **1.15x**.

⭐ **THE ANSWER, AFTER REGENERATING THE MAP: THE SOURCES WERE CANCELLING EACH OTHER OUT.**

An earlier draft of this section said the projection COMPRESSES the difference. That was also
wrong, and the regeneration disproves it. With DTA Enhanced's unusable rows correctly gated out,
the Mammoth's two targets move to:

| | old map (stale) | regenerated | peers |
|---|--:|--:|--:|
| `mammothmissiles` | 41,528 (3 of 3) | **51,580** (2 of 3) | 11,832 |
| `120mmdual` | 40,997 (3 of 3) | **42,275** (2 of 3) | 9,798 |
| **ratio** | **1.013x** | **1.220x** | **1.208x** |

**1.208x in the peers becomes 1.220x in the targets.** The projection carries the difference
through almost exactly; it does not compress it. What produced the old 1.013x was a
**CANCELLATION BETWEEN SOURCES POINTING IN OPPOSITE DIRECTIONS**:

* Combined Arms and Tiberian Dawn both make the **missile** stronger (1.17x, 1.25x);
* DTA Enhanced makes the **cannon** stronger - `HTNK` carries cannon 30 against missile 20, a
  1.5x inversion.

Blending three sources, two saying "missile" and one saying "cannon" nearly as loudly, lands on
"about equal". The near-equality was never evidence that the two weapons are alike; it was two
opposite claims averaging to nothing.

⛔ **AND DTA SHOULD NEVER HAVE BEEN IN THAT AVERAGE.** Its `HTNK` declares `Burst: 2` on BOTH
armaments with no burst delays, so neither cycle can be folded: both rows are
`incomplete / burst_unfolded` and carry no `dps_usable`. They are part of the blocked
unfolded-rate population (170 rows tree-wide, 84 of them DTA Enhanced). The current gate excludes
them correctly - and the moment it did, the real 1.22x separation appeared.

⭐⭐ **THE BATTLE TANK IS A DIFFERENT STORY, AND IT DID NOT MOVE.** 18,870 vs 17,835 before and
after. Its missile has exactly one voter:

| source | cannon | missile |
|---|---|---|
| Combined Arms | `120mm` 4,600 | *(unpaired)* |
| DTA Enhanced | `90mm` **30** | `70mmMsl1` **30** |
| OpenRA Tiberian Dawn | `120mm` 4,000 | *(unpaired)* |

**In DTA Enhanced - the missile's ONLY voter - the cannon and the missile carry the identical
number, 30.** The missile's reference IS the cannon's reference, so the two targets cannot
separate on evidence; the 5.8% that survives is entirely the cannon's extra Combined Arms and
Tiberian Dawn blend. Asymmetric voter counts (1 vs 3) are what move these two apart at all.

⚠ **THREE DIFFERENT CAUSES, AND THEY LOOK IDENTICAL ON THE PAGE.** A near-1.0x spread between two
armaments can mean *the sources agree they are alike*, *the sources disagree and cancelled*, or
*one armament's only voter is the other armament's weapon*. Only the Mammoth's was the second and
only the Battle Tank's is the third. **Read the voters, never the spread.**


⚠ **THE MAP THAT PROMPTED THIS WAS STALE, AND HAS BEEN REGENERATED.** It reported "3 of 3
sources" for both Mammoth weapons including `DTA Enhanced · MammothTusk`; DTA Enhanced now pairs
0 of the Mammoth's 2 armaments. Regenerated 2026-09-14 across all 31 faction tokens:
**161 originals · 709 expanded · 925 references · 514 priced by formula · 8 originals under three
sources.**

⭐ **WHAT THIS DOES AND DOES NOT JUSTIFY.** The Mammoth's guns are NOT alike after all - the
evidence separates them by 1.22x once the unusable votes are gone, so the maintainer's instinct
that a cannon and a missile should differ noticeably is supported here by our own map, not only by
the wider corpus. The Battle Tank is the opposite case: its missile has no independent evidence at
all, so applying one averaged value to both costs nothing and is exactly the maintainer's own
corollary. ⚠ The `td_gdi_apc` pair (6,239 vs 6,138, a 1.6% spread) is a THIRD case and is settled
by 3a.1 rather than by evidence: it is one weapon split for reach, so the two must be made
identical regardless of what their separate votes say.

⚠ For the record, the wider-corpus number stands as a non-directional separation statistic.
Across all 930 dual-weapon reference actors only **29.2%** sit inside 1.05x and **45.4%** exceed
3x. Among the 15 INI rows whose actor name contains `mammoth` and whose two slots both have DPS,
the median stronger:weaker ratio is **1.71x** (1.11x-2.93x). The selection includes Mammoth-named
walkers and no RA2 Apocalypse row, so it must not be described as a directional cannon:missile
measurement. It shows that differentiated slots are common in that population; it does not say
which slot should be stronger or what `td_gdi_mammothtank` should be.


### 3a.5 ⛔ NEVER reference across factions AUTOMATICALLY

**Refined 2026-09-14:** *"unless approved by the maintainer and manually set, never match it
automatically"*. A cross-faction pairing is legal only as an explicit entry in
`assign_references.REFERENCE_OVERRIDES`, where the ruling is visible and attributable. The MATCHER
may never produce one on its own.



> *"the GDI emp grenadier was mapped to the CA marauder which is a scrin unit so that is wrong!
> Never ever reference from other factions without my instructions! What we need is the CA zone
> raider with the sonic grenades which is much closer to the EMP grenadier and also from a gdi
> sub faction called ZOCOM"* (maintainer, 2026-09-14)

A Cameo actor takes its reference from its OWN faction's lineage in the source mod. A
cross-faction pairing needs an explicit maintainer instruction, and is recorded in
`assign_references.REFERENCE_OVERRIDES` where the next reader can see who ruled it.

⚠ **THE FACTION GATE CANNOT CATCH THIS, AND THAT IS THE FINDING.** Combined Arms tags `MRDR`
(Scrin) and `ZRAI` (GDI/ZOCOM) with the SAME 25-faction string - `allies/arc/.../gdi/.../scrin/
.../zocom`, every faction in the mod - so the map recorded `home: true` for a Scrin unit and was
telling the truth as far as the data goes. **156 of CA's 377 units carry ten or more faction
tags** (median 5), against a median of **1** in OpenRA Tiberian Dawn. For CA the routing gate is
therefore not merely weak, it is INERT: a cross-faction pick cannot be detected from the corpus at
all. Until CA lineage comes from something other than `Buildable.Factions`, every CA pairing is a
name-and-stats match with no faction check behind it, and the maintainer's eye is the only gate.
⚠ One more sits in the tree unruled: `yuri_gatlingtrooper` references CA's `ZTRP` Zone Trooper,
GDI/ZOCOM again. It is outside the classic four, so it is reported rather than changed - inventing
a cross-faction correction is the same mistake in the other direction.

### 3a.6 ONE CYCLE PER ACTOR - and then the total DPS is just a sum

> *"Take a look at how our current mammoth tank works with dual weapons and different reload
> delays and different burst delays! The cycle time is the same for both! Reload delay + sum of
> burst delays must be identical between weapons ... So the secret is to give each weapon the same
> cycle, then DPS = damage per shot * burst / cycle time should also be identical ... which means
> to calculate the total damage you just need add the individual DPS from each weapon"*
> (maintainer, 2026-09-14)

**THE LAW.** Every armament on one actor shares ONE attack cycle: `ReloadDelay + sum(BurstDelays)`
is identical across the actor's weapons, whatever each weapon's burst and per-shot damage. A
weapon that fires four shots simply spaces them inside the same interval.

**VERIFIED IN THE TREE**, on the three actors the maintainer named:

| actor | weapons | cycle | dmg/cycle each | rate each | **total DPS** |
|---|---|--:|--:|--:|--:|
| `td_gdi_mammothtank` | cannon, missiles | **80 / 80** | 16,000 | 200.00 | **400.00** |
| `ra1_allies_sheridanassaulttank` | cannon, missile, Burst-4 chaingun | **64 / 64 / 64** | 4,000 | 62.50 | **187.50** |
| `td_gdi_battletank` | cannon, missiles | **72 / 72** | 8,000 | 111.11 | **222.22** |

**WHAT FOLLOWS, and it is the whole point:** with one cycle and one range (3a.2), the balance
formula needs nothing special for a multi-weapon actor. **Total DPS = the sum of the per-weapon
DPS**, range is the shared range, HP and speed come from the chassis. There is no blocker and no
composition problem - the per-cycle damages add directly, because they are damages over the SAME
interval.

⛔ **TWO THINGS THE SUM MUST STILL RESPECT**, neither of them a blocker:

1. **An AA split is not a second gun** (3a.1). `td_gdi_humveemkii` declares
   `machinegunhumvee2` + `machinegunhumvee2_AA` + `rocketshumvee2` + `rocketshumvee2_AA`: that is
   TWO weapons, not four, and adding all four doubles the unit.
2. **A cycle that is not shared has nothing to add over.** Damage per cycle is only additive when
   the cycles are equal; otherwise the two figures describe different intervals.

**MEASURED COMPLIANCE, classic four:** of 23 as-built multi-weapon actors, **15 share one cycle**
and 8 do not (`ra1_allies_destroyer` 34/60, `ra1_allies_gunboat` 30/60, `td_gdi_missileboat`
44/60, `ra1_soviets_su57attackbomber` 54/121, `ra1_soviets_yakscoutplane` 119/121,
`td_gdi_firehawk` 55/52, `td_gdi_humveemkii` 42/84, `td_nod_lasercorvette` 90/42). The reference
map prints **WITHHELD - cycles differ** for those rather than a meaningless sum, which makes the
damage column a live compliance check exactly as the range column is for 3a.2. ⚠ The naval
depth-charge rows and the two bombers are the same population as 3a.2's open bomb exemption -
rule the exemption first, then fix what remains.

**⭐ THE DRIFT RULE - average the near-misses, leave the wide gaps alone** (maintainer,
2026-09-14): *"please use the same value for both: average of 119 and 121 = 120. That's how you
fix any of these very close drifts but the larger ones are likely on design. Only the smaller
drifts like these should be corrected."* A spread of a couple of percent is somebody's arithmetic
slipping and is repaired by averaging; a spread of 100% is a design decision and must be left to
a design ruling. ⚠ **THE THRESHOLD IS 10%, not 5%** (maintainer, 2026-09-14: *"I would say even 10% instead
of 5%"*). Measured across the classic four, the whole corrective list is ONE row:

| actor | quantity | values | spread | action |
|---|---|--:|--:|---|
| `td_gdi_battletank` | range | 5,400 / 5,438 | **0.7%** | average to **5,419** |

⛔ **THE YAK IS NO LONGER ON THIS LIST.** Its 119/121 cycle looked like the clearest drift in the
tree, and it was not drift at all: its two weapons have SEPARATE RANGES, which makes them
disjointed (3a.9), and a disjointed pair has no reason to share a cycle. The averaging order was
withdrawn by the maintainer once that was seen. ⚠ A near-miss is only drift when the two weapons
were supposed to match in the first place - check 3a.9's 2x2 BEFORE averaging anything.

Everything else measures 12.7% or wider - the Yak's bomb against its chaingun at 280%, the Humvee
Mk II's two cycles at exactly 100%, the Laser Corvette's charged laser at 114% - and those are
design questions, not drift. ⚠ Both corrections are yaml balance numbers and therefore belong to
the pipeline (`extract_stats` -> ledger -> `apply_balance --confirm`) with a boot gate, never to a
hand edit.

### 3a.7 Mutually exclusive weapons resolve INDEPENDENTLY - and their DPS is never summed

> *"Those should be regarded like the anti air weapons since they are mutually exclusive with
> their other weapon ... It's not the same weapon that's firing but a different weapon with
> different range, damage and attack cycle but overall it must resolve to the same cost for both
> weapons for the same actor individually as if they were twin units (imagine one ship with only
> rockets and the same ship with only depth charges) then you have to use the balance formula to
> individually resolve DPS and range for both weapons so that the HP, speed and cost can be the
> same for both variants and then merge it back together to a single unit right? ... the DPS is
> never summed up for those!"* (maintainer, 2026-09-14)

**THE LAW.** When two armaments on one actor can never engage the same target, they are not a
combined weapon system - they are **two virtual twin units sharing one chassis**. Price each one
on its own through the balance formula, require both to resolve to the SAME HP, speed and cost,
then merge back to one actor. **Never sum their DPS, and never expect them to share a range** -
a depth charge is deliberately short-ranged and the missile beside it is not, so 3a.2 does not
apply between them and neither does 3a.6.

⛔ **THE TEST IS `ValidTargets`, NOT THE PAIRING ROLE.** The role vocabulary is ground / air /
both and has **no underwater domain**, so a depth charge declaring `Underwater, Submarine` is
filed as "ground" and looks like it shares a target with the ship's cannon. It cannot. Read the
weapon's own declaration and intersect:

| actor | weapon A | weapon B | verdict |
|---|---|---|---|
| `ra1_allies_destroyer` | missile `Ground, Water, Air` | depth charge `Underwater, Submarine` | **exclusive** |
| `ra1_allies_gunboat` | cannon `Ground, Water` | depth charge `Underwater, Submarine` | **exclusive** |
| `td_gdi_missileboat` | missile `Ground, Water` | depth charge `Underwater, Submarine` | **exclusive** |
| `td_gdi_firehawk` | missiles `Air` | bomb `Ground, Water` | **exclusive** |
| `td_gdi_boxer` | cannon_AA `Air` | cannon `Ground, Water` | **exclusive** (an AA split) |
| `td_gdi_humveemkii` | MG `Ground, Water` | rockets `Ground, Water` | **simultaneous** |

**MEASURED, classic four:** of the multi-weapon actors, **6 sum**, **5 are exclusive**, and **4
genuinely break 3a.6** - `ra1_soviets_su57attackbomber` 54/121, `ra1_soviets_yakscoutplane`
119/121, `td_gdi_humveemkii` 42/84, `td_nod_lasercorvette` 42/90. That last list is the fix
queue; the exclusive five are correct as they stand.

⚠ `ra1_soviets_yakscoutplane` is worth its own line because it looks like the boats and is not:
its napalm bomb is `Ground, Water` and its chaingun `Ground, Water, Air`, so against any ground
target **both fire** and they must share a cycle. They miss by **2 ticks** - bomb
`ReloadDelay 110 + 3 x Burst-4 delays = 119`, chaingun `100 + 7 x 3 = 121` - which is drift, not
design, exactly like `td_gdi_battletank`'s 38-WDist range gap. ⚠ Its 1,840 vs 7,000 range gap is
the unruled BOMB exemption to 3a.2 and must be ruled before it is "fixed".

**⭐ THE DISJOINT PAIR DOES NOT SHARE A DPS EITHER** (maintainer, 2026-09-14): *"Each is a full
unit but keep in mind that the range for both will vary and resolving the balance formula means
the DPS of the higher range one will be lower than the shorter range one. That's just how the
balance formula works. So they will not have the same DPS if they have two separate ranges and
that's the important part here!"*

So the two cases have OPPOSITE fingerprints, and that is how to tell them apart on sight:

| case | cycle | range | per-weapon DPS |
|---|---|---|---|
| same target (3a.6, 3a.9) | **shared** | **shared** | **equal** - each is 1/n of one budget |
| disjoint (3a.7) | independent | **independent** | **deliberately unequal** - longer reach buys less DPS |

⛔ So an unequal DPS on a disjoint pair is not drift and must never be "corrected" toward
equality: `ra1_allies_destroyer`'s 8,000-range missile SHOULD out-range and under-damage its
6,000-range depth charge. Each is a FULL unit at the same HP, speed and cost - the hull is both
specialists in one, and that is the intended deal.

⚠ **THE ORDOS AA TROOPER IS THIS CASE, NOT AN AA SPLIT** (maintainer, on being shown the
numbers): *"it's not actually the 1.5x rule, this one uses two independent weapons like we said
earlier for the ships so yes range and DPS just solve independently for this unit."* Its
`D2K_Rocket_Trooper_AA` (Air, 9,716, 10,000 dmg) and `D2K_Rocket_Trooper_AGOnly` (Ground/Water,
6,252, 30,000 dmg) are two real weapons - longer reach, lower damage, exactly as the rule
predicts - and 3a.1's ratio law does not apply to them.

⛔ **WHICH CREATES A NAMING CONFLICT THAT MUST BE RESOLVED BEFORE THE RENAME RUNS.** 3a.8 has
the balance formula DROP every `_AA` weapon by name. That is safe only while `_AA` means "the
free, unpriced air half of a split". The Ordos trooper's air missile is NOT that - it is a full
virtual unit that must be PRICED - so leaving it called `_AA` would delete a real weapon from the
formula. Either it stops being called `_AA`, or 3a.8's rule gains the exception it was written to
avoid. **The rename map must not be executed until this is settled.**

### 3a.8 ⛔ The balance formula IGNORES the `_AA` half - but only when it HAS an AG twin

> *"the easiest way is to rename all those AA twin weapons with the _AA Suffix and then ignoring
> it for the balance formula! The only thing that matters here is that the AA weapons have 1.5x
> range from their AG version and that should only be part of the audit but never by the balance
> formula"* (maintainer, 2026-09-14)

**THE LAW.** An `_AA` half that exists only to give one gun 1.5x reach against air is **not a
second weapon**: the formula prices the ground half and ignores the `_AA` half entirely. The
1.5x relationship and the identical Damage/Reload/Burst/BurstDelays/MinRange are an **AUDIT**
matter (`aa_split_pairs_compliant`), never a pricing input.

⛔ **"IGNORE EVERY `_AA` WEAPON" WOULD PRICE REAL UNITS AT ZERO.** The suffix currently means
three different things in this tree, and only the first may be ignored:

1. **The AA half of a split** - 63 weapons whose exact base twin `X` also exists. Ignore these.
2. **A standalone AA weapon** - `ra1_soviets_samsite` carries exactly ONE armament,
   `ra1_soviets_samsite_missile_AA`, and `harkonnen_adp` carries `D2K_Rocket_AA`. That weapon IS
   the unit. Ignoring it prices a SAM site at **zero DPS**.
3. **A general weapon that merely also hits air** - `ra1_allies_rapierjumpjet_missile_AA`
   declares `Ground, Water, Air` and has no AG twin at all. It is the Rapier's main gun wearing
   the wrong name.

So the rule is conditional: **ignore `X_AA` when `X` exists as another armament on the same
actor.** Anything else is priced normally.

**THE NAMING CONVENTION - BOTH HALVES CARRY A SUFFIX.** Maintainer, 2026-09-14: *"The pair
should have the _AA and the _AG pair where the AA variant is the one with 1.5x range and anti
air right?"* So a split is **`X_AG` + `X_AA`**, never a bare `X` against an `X_AA`. With both
halves marked, the formula drops the `_AA` half by NAME and the audit checks the pair by name,
and neither has to infer anything.

⚠ **THE SLOT ORDER IS READ FROM THE TREE, NOT CHOSEN**: `MigMissiles_AA_elite` and ten more
like it already exist, so the AA/AG marker sits directly after the base and any state modifier
follows it - `MigMissiles_AG_elite`, not `MigMissiles_elite_AG`.

The full proposal is generated into **`docs/design/AA_SPLIT_RENAME_MAP.md`**: **84 weapons**
across **63 split pairs**, with one collision flagged for a human. ⚠ It is NOT applied - executing
it is a `safe_rename.py` migration needing a boot gate and a quiet tree, and master is currently
staged for a controlled playtest.

⛔ **TWO TRAPS THE GENERATOR HAD TO BE TAUGHT**, both caught by reading its output:

* **A shared prefix is not a family.** The first cut proposed `D2K_Rocket_Buggy ->
  D2K_Rocket_AG_Buggy`. `D2K_Rocket_Buggy`, `D2K_Rocket_Trooper` and `D2K_Rocket_Fremen` are
  DIFFERENT units' weapons that merely start with the same words. Only a known state modifier
  (`elite`, `cryo`, `rad`, `fire`, `tesla`) travels with the base.
* **"Frag" is not an "AG" suffix.** A regex for a ground half ending in `AG` also matches
  `Future_MultiMissile_Frag` and `TS155mmFrag`. The cure is to require the `_AA` partner to
  EXIST before believing any name is half of a split.

⚠ **ONE COLLISION NEEDS A RULING**: `D2K_Rocket_Trooper` and `D2K_Rocket_Trooper_AGOnly` both
want to become `D2K_Rocket_Trooper_AG`, because the AA twin `D2K_Rocket_Trooper_AA` has TWO
ground-side candidates. Which one is the real half is a question about that unit, not a naming
question, so the generator refuses rather than picking.


**⚠ THE IXIAN TWIN BAZOOKA IS A THIRD SHAPE, and it is unique** (maintainer, 2026-09-14):
*"It's on the twin bazooka, the upgrade to the rocket trooper for the Ixians! And yes this unit
shoots one straight rocket that is like a Bullet and one targeted Missile ... But it's unique to
that unit with that logic."* `ixian_twinrockettrooper` fires `D2K_Rocket_Trooper1` (a **Missile**
projectile) and `D2K_Rocket_Trooper2` (a **Bullet** projectile) from two armaments, both at range
6,502 and both `Ground, Water, Air`. So it is neither a twin split nor a disjoint pair: it is TWO
SYSTEMS THAT SHARE EVERY TARGET, differing only in how the projectile flies - which makes it a
3a.6/3a.9 unit (one cycle, one range, the firepower split between the two systems). It takes no
AA/AG suffix. ⚠ Do not generalise it: the maintainer marked it as unique to that unit.

### 3a.10 ⭐ `Only` MARKS A DISJOINT PAIR - the suffix that overrides the twin rule

> *"The two weapons should be renamed and I think the key to this is simply the Only at the end
> which should override the AG / AA same weapon twin rule! So if you name it _AGOnly and _AAOnly
> that will tell our formula that those are indeed disjointed weapons and not a twin!"*
> (maintainer, 2026-09-14)

**THE LAW.** The suffix says which of the two mechanisms a weapon belongs to, so no tool has to
infer it:

| naming | meaning | the formula |
|---|---|---|
| `X_AG` + `X_AA` | **one weapon** split for reach (3a.1) | prices `X_AG`, **drops `X_AA`** |
| `X_AGOnly` + `X_AAOnly` | **two independent weapons** (3a.7) | prices **BOTH**, as virtual units, never summed |
| no suffix | hits everything, or is the actor's only weapon | priced normally |

⛔ **THIS IS WHAT UNBLOCKS THE RENAME.** 3a.8 has the formula drop every `_AA` by name, which
would have deleted the Ordos AA trooper's air missile - a full weapon that must be priced. With
`Only` the two cases are distinguishable at a glance and the drop rule stays unconditional. The
Ordos trooper therefore becomes `D2K_Rocket_Trooper_AGOnly` (already correct) and
`D2K_Rocket_Trooper_AAOnly`, and its 1.554x reach with 3x damage difference is not a violation of
anything - it is 3a.7 working as designed: longer reach, lower DPS.

⚠ A disjoint pair's ground half may carry a name of its own that has nothing to do with the air
half - the Sea Scorpion's ground weapon is `RA2FlakTrackGun`, shared with the flak track - so the
`Only` convention cannot always be applied to BOTH halves. Where the ground weapon is shared with
another unit it must not be renamed; only the air half takes `_AAOnly`.

### 3a.9 THE FIREPOWER SHARE - the 2x2 that decides how a multi-weapon unit is priced

⛔⛔ **CORRECTED BY THE MAINTAINER, 2026-09-14, AND THIS SUPERSEDES THE EARLIER READING.** The
first version of this section keyed everything on whether two weapons can hit the same TARGET.
That is only half of it. The other half - the half that explains the cases that would not fit -
is whether they share a RANGE:

> *"disjointed means separate ranges! Write that down because that is important! And remember
> disjointed against the same target still counts both! which means you need to adjust the final
> DPS of each weapon by 1/n. While disjointed against different targets like the AA Trooper
> having one AG and one AA disjointed weapon means both keep their full DPS!"*

|  | **same range** | **different ranges (DISJOINTED)** |
|---|---|---|
| **same target** | one cycle, **DPS sums**, each weapon is **1/n** of the budget | each solved on its own (longer reach buys less DPS), then each scaled by **1/n** - they still both hit the victim |
| **different targets** | - | each keeps its **FULL** DPS and they are **never summed** - only one is ever engaging |

**READ IT AS TWO INDEPENDENT QUESTIONS.** *Do they both reach the victim?* decides whether the
budget is SHARED (1/n) or not. *Do they have the same range?* decides whether their DPS can be
ADDED or must be solved separately. The first question is about paying; the second is about
arithmetic.

⭐ **THE CASE THAT FORCED THE CORRECTION.** `ra1_soviets_yakscoutplane` carries a napalm bomb at
1,840 range and a chaingun at 7,000, and its cycles differ (119 against 121). Under the old
reading that was a 3a.6 violation to be averaged away. It is not: the two weapons have separate
RANGES, so they are disjointed, and a disjointed pair has no reason to share a cycle. *"So yes
this was wrong on my part ... that's why the short range weapon has the high damage and the long
range weapon has the low damage, it all makes sense now!"* ⚠ **The ruling to average the Yak's
cycle to 120 is therefore WITHDRAWN** - there was never a drift to fix.

⭐ **AND IT EXPLAINS THE YAK'S 72/28.** Measured: bomb 336.81 DPS at 1,840 reach, chaingun 66.12
at 7,000. That is not a broken 50/50 split - it is the range/DPS trade-off doing exactly what it
should, with each weapon then taking half the budget. The "50% bombs, 50% dual chainguns" the
maintainer described is the BUDGET share, never a claim that the two would show equal DPS.

**WHERE 1/n WITH A PLAIN SUM APPLIES:** *"only counts for same range weapons like for helicopters
like the hind, kamov, sky hawk etc with multi weapons and all weapons with identical range where
you can simply sum up DPS with no problem!"* - helicopters and ground units, which stop to
attack and therefore obey 3a.2's equal-range law.



> *"you need to count them as individual units in the balance formula, one with one weapon and
> the other with the other weapon. But here it's important that they are indeed not counted as
> separate units cost wise because chaingun and bomb can target the same target right? so in this
> case what you need to do is create those two units separately first as virtual units, then give
> each only 1/n firepower and then combine them. For the Yak what was used was actually 50% Bombs
> and 50% dual chainguns which means 25% single chaingun (since these are two weapons right?) ...
> a lot of units have this logic like also the hind and the sky hawk"* (maintainer, 2026-09-14)

**THE MECHANISM.** A multi-weapon actor is priced by splitting it into **virtual single-weapon
units**, pricing each with the balance formula, and merging them back. The 2x2 above decides
what share each virtual unit carries and whether the results may be added.

⭐ **THE TREE ALREADY OBEYS THIS, AND IT IS VISIBLE AS A FINGERPRINT.** If every weapon carries
`1/n`, then with one shared cycle (3a.6) **every weapon on the actor shows the SAME DPS**. That is
exactly what the classic four show, and it is not a coincidence - it is the rule leaving a mark:

| actor | weapons | DPS each | total | share |
|---|--:|--:|--:|--:|
| `td_gdi_mammothtank` | 2 | 200.00 | 400.00 | 1/2 |
| `td_gdi_mammothtankmkiii` | 2 | 218.18 | 436.36 | 1/2 |
| `td_gdi_battletank` | 2 | 111.11 | 222.22 | 1/2 |
| `td_gdi_humveemkii` | 2 | 95.24 | 190.48 | 1/2 |
| `ra1_allies_sheridanassaulttank` | 3 | 62.50 | 187.50 | 1/3 |
| `ra1_soviets_heatraytank` | 4 | 187.50 | 750.00 | 1/4 |

**n COUNTS GUNS, NOT ARMAMENT ENTRIES**, and the tree writes that two different ways - this is
the subtlety the Yak exists to teach:

* `td_gdi_mammothtank` declares ONE armament per weapon whose `LocalOffset` lists TWO barrels
  (`900,180,340, 900,-180,340`). Two barrels, one armament, one share.
* `ra1_soviets_yakscoutplane` declares TWO armaments of the same weapon at the two wing offsets
  (`256,-213,0` and `256,213,0`). Two guns, two armaments - and **the pair shares 50%, so each
  single chaingun is 25%**, which is precisely the maintainer's arithmetic.

⛔ **SO A DUPLICATE ARMAMENT IS NOT ALWAYS A DUPLICATE.** `Armament@PRIMARY` and
`Armament@GARRISONED` are the same gun fired from two places and must be counted ONCE; the Yak's
two wing mounts are two guns and must be counted TWICE. The evidence that separates them is the
`LocalOffset`: same weapon, DIFFERENT offset, same condition = a real second mount. ⚠ The
reference map currently de-duplicates on `(weapon, role)` alone and therefore UNDER-counts a dual
mount. Two actors are affected, `ra1_soviets_yakscoutplane` and `ra1_soviets_su57attackbomber`,
and **neither publishes a wrong number today** only because both are withheld for a different
reason (their cycles differ). It becomes a live error the moment those cycles are fixed.

**THE YAK IS OFF ITS OWN DESIGN TODAY.** Intended 50% bomb / 50% chainguns; measured:

    napalm bomb   40,080 per cycle / 119 = 336.81   72%
    chaingun x2    8,000 per cycle / 121 =  66.12   14% each, 28% together

⚠ Fixing that is a firepower re-split, not a cadence tweak, and it needs the pipeline and an
explicit order. What IS ruled is the cadence: the two cycles are averaged to **120** (3a.6).

⭐ **ANSWERED BY THE MAINTAINER, 2026-09-14:**

1. **THE SHARE IS NOT FORCED EQUAL.** *"Yes exactly design can weight a type more!"* So `1/n` is
   the DEFAULT and a deliberate design may give one system a larger slice. Equal is what every
   measured classic-four actor happens to be, which makes an UNequal split a design statement
   worth being able to point at - not automatically a defect. ⚠ It also means an unequal split
   can never be auto-corrected; it can only be flagged for a human.
2. **`n` COUNTS WEAPON SYSTEMS - all weapons of the same type count as ONE.** *"Weapon systems
   (all weapons of the same type count as one)."* The Yak therefore has **n = 2**: one bomb
   system and one chaingun system, 50% each, and the chaingun system's 50% is then divided
   between its two barrels at 25% apiece.

   ⛔ **THE TWO STATEMENTS LIVE AT DIFFERENT LEVELS AND BOTH MATTER.** The SHARE is counted per
   system (n = 2 for the Yak), but the DELIVERED DPS is the sum over every BARREL, because both
   wing guns really do fire. So a tool must group by system to compute the share and sum all
   armaments to compute the total. Collapsing the Yak's two chainguns into one gives the right
   `n` and the WRONG total - which is exactly the bug recorded above.
⚠ **STILL OPEN** - for the 3a.7 disjoint case, both virtual units must resolve to the same HP,
speed and cost, but at what DPS LEVEL? Take `ra1_allies_destroyer`: virtual unit A is the hull
with only the anti-ship missile, virtual unit B the hull with only the depth charge. Should A's
DPS equal that of a dedicated single-weapon anti-ship destroyer at that cost (and B's that of a
dedicated sub-hunter) - so the real ship is BOTH specialists in one hull for one price - or
should each be reduced, so that carrying both is paid for in firepower and building a specialist
still makes sense? ⚠ Unlike the same-target case, `1/n` does NOT answer this: the two weapons
never add up against anything, so nothing forces them to share a budget.


## 4. Tech tier rules (F12/F13)

Building tiers are data-driven from prerequisite chains (conyard 0,
barracks/refinery 1, radar 2, tech 3, post-tech 4+; faction-relative,
cheapest provider wins).

- Every faction has an **anti-air tower on its radar tier**. Additional AA
  at tech tier or above is legal "advanced AA".
- An AdvancedDefense with an AA weapon may HOLD the radar tier when the
  faction has no dedicated radar-tier AA (jballistat, Ixian Rocket Turret).
- **Advanced defenses gate ABOVE the radar tier** — tech building or later
  (Tier 4/5 gates are fine).
- **Every faction always keeps a Tier-1 defense**; violations whose fix
  would remove the last pre-radar defense are DEFERRED until a Tier-1
  defense is added.
- Exemptions: single-armed-defense factions (Protoss photon cannon),
  promotion-gated defenses (transitional), Terran/Zerg (non-tiered).

## 5. Starting units (F14–F16)

- Every referenced actor must exist (crash class).
- **Light Support**: Tier-1 only (nothing gated above its producer
  building), total ≈ **2000**, diverse, ≈ **5 infantry : 1 vehicle**,
  pricier units never outnumber cheaper ones.
- **Heavy Support**: same ratio/frequency rules at ≈ **10000**, mixing all
  tiers (at least one above-Tier-1 unit).

### Transport cargo pricing (proposal policy, 2026-09-11)

Ordinary unit and passenger prices use the **10-credit grid for now**. A
loaded carrier is an explicit exception: its `Valued.Cost` is the exact
integer sum of its authored passenger prices after capacity validation, so a
carrier total may be off the 10-credit grid (for example, the current Nod
Chinook is 3,853). Naval
transports have no `InitialUnits` payload and are excluded from the loaded-price
rule; an empty starting naval payload does **not** authorize changing an
existing `MaxWeight` value. Air transports such as Chinooks use one of each
available infantry for their faction, including promotion variants, with early
units listed before later and promoted options. Advanced armed transports favor
varied infantry in that order. A modeled transport's declared capacity must
match the actual `InitialUnits` weight before its passenger prices are summed
into the transport price. Any capacity interpretation that would alter existing
YAML remains an explicit design decision.

## 6. Upgrades, promotions, power curve

- One source of truth per layer (class templates / faction upgrades /
  promotions); actors never restate a layer's values.
- Every upgrade has an intent line in `docs/design/upgrades_intent.yaml`
  (direction, coverage, phase, intended drawbacks) — feeds B3/B4 audits.
- Multiplier semantics: reload/build <100 = faster; damage taken <100 =
  tankier; firepower/range/speed >100 = stronger.
- **Promotions grant options (units/abilities); research grants stats.**
- Roster-wide upgrades must cover the full roster (audit_upgrade_coverage).
- Worst-case stack budget ≤ 2.0× fresh-self effective power
  (audit_power_budget; veterancy ladders are exclusive, count best rank).
- **Stat-modifier philosophy** (design 2026-07-11, modeled by
  ^PromotionUnitBuff's +5%/+10% steps): speed and range are only ever
  increased MODERATELY (never big jumps); damage-taken multipliers may
  stack, but the COMBINED product must never drop below **50%** — below
  that units feel undamageable. Hard floor; audit extension TODO
  (worst-case stacked DamageMultiplier per unit < 0.5 = finding).
- ⭐ **CHARGE-UP DISCOUNT — the 50% anchor** (maintainer law, 2026-08-15). A charging
  unit is nerfed twice (the delay inflates its effective reload AND it is helpless
  while winding up), so it is priced at a discount. The discount is PROPORTIONAL to
  the real burden, never flat:
  - **A unit whose charge is 50% of its reload earns the full 0.75× discount.**
    Reload 100, charge 50 — as a share of the cycle, `0.5/1.5` = **1/3**
    (`formula.CHARGE_ANCHOR_SHARE`). Less charge earns proportionally less discount;
    a zero-charge unit pays 1.0. Clamped to [0.75, 1.0].
  - **`charge_share = charge / (charge + cycle)` is a RATIO, not a duration.** The RA1
    Tesla Coil charges LONGER than the RA2 one (25 vs 20) yet earns a SMALLER
    discount, because its three zaps stretch the cycle.
  - ⚠ **`AttackTesla` overrides the weapon's reload.** Its own `ReloadDelay` is the
    cycle, `MaxCharges` is the burst, and the WEAPON's reload is the burst delay —
    NOT `ChargeDelay`. Reading the weapon's reload as the cycle overstated Tesla DPS
    by **11.8×**. See `BALANCE_PROGRAM_PLAN.md` W16.
  - ⭐⭐ **THE CYCLE IS RELOAD PLUS CHARGE, AND THE DISCOUNT STILL APPLIES** (maintainer
    law, 2026-09-14): *"charged weapons come at a discount but the attack cycle
    duration is reload delay plus charge delay"*. **BOTH, never either** — the K
    discount prices the DRAWBACK of being helpless while winding up; the longer cycle
    measures the OUTPUT that the wind-up costs.

    This is not new arithmetic. The discount's own denominator already said so:
    `charge_share = charge / (charge + cycle)` treats `charge + cycle` as the whole
    period. And the full rate law is:

        DPS = damage x burst / attack cycle
        attack cycle = reload delay + sum of ALL burst delays + charge delay

    ⚠ **"DPS" is a NAME, not a unit — it is damage per TICK**, everywhere in this
    repository. Nothing here is per second.

    ⭐⭐ **HOW MANY TIMES THE CHARGE IS PAID** (maintainer, 2026-09-14). This is the
    fact that decides the whole arithmetic, and it is NOT derivable from the trait name:

    > *"for the tesla coil the attack cycle is initial charge delay + reload delay but for
    > the asian alliance railgun tower it needs to charge for every shot unlike the tesla
    > coil! So at 5 shots the initial charge delay is used 5 times! For the tesla coil it
    > is only used once!"*

    | actor | base cycle | charge | paid | attack cycle |
    |---|--:|--:|:--:|--:|
    | `ra1_soviets_teslacoil` | 106 | 25 | **x1** | **131** |
    | `ra2_soviets_teslacoil` | 75 | 20 | x1 | **95** |
    | `asianalliance_railtower` | 160 | 12 | **x5** (`MaxCharges`) | **220 ruled immediate-reacquisition model** |

    So a charged weapon is one of two machines, and they differ by a factor of `MaxCharges`:
    **charge-once** (one wind-up, then the whole burst) or **charge-per-shot** (every shot
    pays). Astra's engine trace found the mechanism that separates them — the Rail Tower's
    post-shot `ChargeFire` wait (3) expires while its weapon is still in a 10-tick reload,
    so the trait exits and must reacquire through `InitialChargeDelay` for the next shot.
    The Tesla Coil's zaps are uninterrupted. The detectable condition is therefore
    **`ChargeDelay` against the WEAPON's reload**, which is exactly the field
    `extract_stats` does not yet record.

    ⚠ The same question is open for multi-shot `ChargeLevel` — the burning Obelisk is
    Burst 10 and its notifier resets on every projectile, which reads as charge-per-shot and
    would make its period very large. **Do not assume it**; it needs the same evidence and a
    ruling of its own.

    ⭐ **RANDOM RANGES TAKE THE MEAN** (same ruling) — **IMPLEMENTED**: `ChargeLevel: 25, 50`
    is not two settings but ONE uniform roll the engine makes on every wind-up, so it contributes
    **37.5**. `extract_stats.charge_scalar` now averages min and max; it used to keep
    `split(",")[0]`, which priced every charged shot as if it always rolled the luckiest value.
    **Exactly four actors declare a range**, and all four moved:

    | actor | declared | ticks | price multiplier |
    |---|---|--:|---|
    | `steelconsortium_dagger` | `25, 50` | 25 → **37.5** | 0.750 → 0.750 (already at the floor) |
    | `wc2_humans_dwarvenrifleman` | `0, 4` | 0 → **2.0** | 0.750 → **0.976** |
    | `wc2_humans_siegeengine` | `20, 40` | 20 → **30.0** | 0.875 → 0.827 |
    | `wc2_orcs_siegeengine` | `20, 40` | 20 → **30.0** | 0.875 → 0.827 |

    ⛔ **THE DWARF MOVES THE PRICE THE OPPOSITE WAY FROM INTUITION, AND THAT IS THE POINT.**
    `charge_price_multiplier` reads `share <= 0` as *charges, but we cannot see by how much* and
    hands out the FLAT 0.75 floor. So the misparsed zero was quietly collecting the deepest
    discount in the table; measuring its real 2 ticks against a 60-tick reload makes it **dearer**,
    not cheaper. A MEASURED near-zero and an UNMEASURED zero are different facts, and only one of
    them may claim the floor.

    ⚠ Nothing in the REFERENCE path moved: `formula.charge_attack_cycle` returns `None` for the
    whole `ChargeLevel` family, so the regenerated `armament_pairing.json` changed only its three
    input fingerprints. The ruling is MIN and MAX, not the mean of every element — they coincide
    for the two-element ranges the tree has, and a third value would need its own measurement.
    Pinned by `ranged_charge_actors`.

    ⭐⭐⭐ **THE ENGINE TRACE, AND THE RULED IMMEDIATE-REACQUISITION MODEL** (`AttackTesla.cs`, read
    2026-09-14 at the maintainer's request to *"verify why that is in game and then adjust
    our formula so it will detect that behavior automatically"*).

    ⛔ **I PUBLISHED TWO TRACES HERE AND BOTH WERE WRONG.** The first used
    `max(ChargeDelay, weapon ReloadDelay)` and gave 172; the second quantised that to
    `ChargeDelay x ceil(reload / ChargeDelay)` and gave 180. They share one false premise —
    that `ChargeFire` keeps ticking while the weapon reloads. **Codex and Astra caught it.**
    It does not tick; it EXITS:

        ChargeFire.Tick:  if (IsCanceling || !attack.CanAttack(self, target)) return true;

    and `AttackBase.CanAttack` calls `HasAnyValidWeapons(target, reloadingIsInvalid: true)`,
    whose loop sets `reloadingStateIsValid = !reloadingIsInvalid || !armament.IsReloading`.
    **A reloading armament makes `CanAttack` false**, so `ChargeFire` returns true and unwinds.
    `ChargeAttack` carries the identical guard, so it ends too — the whole attack activity
    finishes, the actor reacquires, and it comes back in through `ChargeAttack`, **which pays
    `InitialChargeDelay` all over again.**

    ⭐⭐ **THAT CONFIRMS THE CHARGE-PER-SHOT MODE, BUT NOT A FIXED RUNTIME PERIOD.** No
    trait-name special case is needed: `ChargeDelay` against the weapon reload establishes
    whether the activity is interrupted. The time before the parent schedules a replacement
    attack activity is a separate input:

        weapon reload <= ChargeDelay   CHARGE-ONCE      gap = ChargeDelay
        weapon reload >  ChargeDelay   CHARGE-PER-SHOT  gap = weapon reload + reacquisition + InitialChargeDelay

        attack cycle = (MaxCharges - 1) x gap + trait ReloadDelay + InitialChargeDelay

    | actor | ChargeDelay | weapon reload | mode | gap | (n-1) x gap | trait reload | charge | cycle |
    |---|--:|--:|---|--:|--:|--:|--:|--:|
    | `ra1_soviets_teslacoil` | 3 | 3 | once | 3 | 6 | 100 | 25 | **131** |
    | `ra2_soviets_teslacoil` | 3 | 3 | once | — | 0 | 75 | 20 | **95** |
    | `asianalliance_railtower` | 3 | 10 | **per-shot** | 10+0+12=**22** | 88 | 120 | 12 | **220 modeled** |

    ⭐ **`tools/balance/sim_attack_tesla.py` reproduces all three ruled figures under explicit
    immediate reacquisition** — including the
    maintainer's *"for the asian alliance railgun tower it needs to charge for every shot
    unlike the tesla coil! So at 5 shots the initial charge delay is used 5 times!"*, which is
    charge-per-shot behavior the reloading guard produces. It exposes `--reacquire` because the
    surrounding `AutoTarget` activity, with randomized 3–7 tick scan intervals, is not simulated.

    ⚠ `ChargeDelay` is the ENGINE DEFAULT 3 on all three actors — no yaml writes it — so the
    comparison that decides the mode is invisible in the rules. This is why the mode cannot be
    read off the yaml today: the extractor records neither `ChargeDelay` nor the weapon reload
    beside the charge record.

    | number | where it came from | what it got wrong |
    |--:|---|---|
    | 160 | #385 | never pays the wind-up at all |
    | 172 | my spin trace — **withdrawn** | `ChargeFire` exits, it does not spin |
    | 180 | my quantised trace — **withdrawn** | same false premise, quantised |
    | **220** | the 2026-09-14 ruling | reproduced by the immediate-reacquisition model; runtime timing remains unmeasured |

    ⚠ **TWO ASSUMPTIONS THE MODEL STILL CARRIES.** (1) Reacquisition after the activity ends
    is modelled as immediate; that is what produces 220. The real actor's randomized AutoTarget
    scan can lengthen the period, while leaving both coils untouched because they never exit.
    (2) `DoAttack` calls `CheckFire` on EVERY armament and `Attacking` decrements
    `charges` once per firing armament; the RA1 coil declares 3 armaments and the RA2 coil 6,
    all condition-gated, and the model assumes exactly one is enabled — which is what
    reproduces 131 and 95.

    ⭐⭐ **APPLIED 2026-09-14**, on the maintainer's instruction *"make sure the charge
    between every shot is counted correctly for the burst cycle"*. The last unblock is
    closed: `extract_stats` records `ChargeDelay` — the engine default 3, written by no actor
    in the tree, which is exactly why the mode was undecidable — and
    `formula.charge_attack_cycle` counts the wind-up once or per shot accordingly.
    `tesla_coil_attack_period` moved from the implemented 106 to the ruled **131**.

    ⚠ **THE CORRECTION IS NOT SMALL.** These defences were priced on a cycle that omitted the
    wind-up entirely, so their rates fell when it was added:

    | actor | cycle | rate | |
    |---|---|---|--:|
    | `asianalliance_railtower` | 160 → **210** | 968.75 → **738.10** | **-24%** |
    | `ra1_soviets_teslacoil` | 106 → **131** | 1358.49 → **1099.24** | **-19%** |

    ⛔ **WHAT IS PRICED IS THE FLOOR, AND ONLY THE FLOOR.** A charge-per-shot actor goes idle
    between shots, so it re-enters through `AutoTarget`, whose scan re-arms with
    `SharedRandom.Next(MinimumScanTimeInterval 3, MaximumScanTimeInterval 8)` — and `Next`
    EXCLUDES its upper bound, so the interval is **U{3..7}, mean 5**, with no Cameo yaml
    overriding either field. A 300-seed sample reports **210 minimum / 218 mean / 232 maximum**;
    a valid repeating scan path produces 234, so 232 is not a ceiling. The baseline Tesla Coil
    cases are invariant when exactly one condition-gated armament is enabled. The floor is priced
    deliberately: it follows from the fields
    alone, it is what the maintainer ruled, and it errs toward pricing the actor slightly
    strong rather than weak. The spread above it is recorded, not applied.

    ⭐ **THE LAW IS RULED AND, SINCE 2026-09-14, APPLIED.** The evidence the extractor did
    not record — `ChargeDelay` — is now recorded, so `reference_distribution`/`armament_roles`
    report the cycle WITH the charge term (Tesla Coil **131**, Rail Tower **210**). The
    `ChargeLevel` family is deliberately unchanged (Obelisk still 96): it only delays a gun
    that keeps its own reload, so it cannot say what a cycle is. Astra's engine trace, 2026-09-14, found three cases where naively
    adding the wind-up produces a number the engine does not run:

    | case | why a naive `+ charge` is wrong |
    |---|---|
    | multi-shot `ChargeLevel` | the burning Obelisk is Burst 10 / BurstDelays 1 and its `AttackCharges` notifier resets `ChargeLevel` on **every projectile** — later shots must recharge, so the period is not `105 + 50` |
    | interleaved `AttackTesla` | ⭐ **CLOSED.** `ChargeFire` exits when the armament is reloading, so the Rail Tower re-enters through `ChargeAttack` and pays the wind-up again — charge-per-shot, exactly as ruled. Detection is `ChargeDelay` vs the weapon reload, both now available, and AutoTarget's `Next(3, 8)` scan is sampled by the simulator. The tower prices at its ideal floor **210** (its wind-up is 10 since 2026-09-14); 300 seeds average 218 and a legal path reaches 234. My 172 and 180 are withdrawn; #385's 160 never paid the charge |
    | random `ChargeLevel` | ⭐ **CLOSED.** `ChargeLevel: 25, 50` is a RANGE and `extract_stats` kept only its lower bound; ruled 2026-09-14 to take the MEAN of min and max, and `charge_scalar` now does — 37.5 here, and `0, 4` is 2 rather than zero. All four ranged actors re-extracted |

    ⭐ **All three unblocks are closed.** Range-ness resolves at extraction; `ChargeDelay` is
    recorded, which is what makes the mode decidable; and the reacquisition variability is
    explicitly modelled and sampled. `ShotsPerCharge` remains unrecorded and matters only to the
    `ChargeLevel` family, which does not own a cycle. `tesla_coil_attack_period` has moved
    from the implemented 106 to the ruled **131** — the gap it existed to keep auditable is
    shut.

    ⛔ **`formula.charge_attack_cycle` returning `None` does NOT mean "no charge time".**
    It means only that the trait does not override the weapon's RELOAD. That misreading
    is what produced the withdrawn Obelisk figure.
  - Charge values are DECISIONS: write `InitialChargeDelay` out rather than inheriting
    the engine's default of 22. An absent key means DEFAULT, never zero.
- ⭐ **TEAM UPGRADES ARE ALWAYS WEAKER THAN FACTION UPGRADES** (maintainer law,
  2026-08-15). A team upgrade buffs every allied army, so it must never be the
  strongest thing a faction can research — the faction's own upgrades are what
  make it feel distinct. Measured practice in the tree already follows this, and
  the ratio is roughly **HALF**:

  | upgrade | scope | magnitude |
  |---|---|---|
  | `^WayOfTheDragon` (Asian Alliance) | team | ±5% |
  | `^MenOfSteelTeamUpgradeRA1` | team | ±10% |
  | `^WarEconomyTeamUpgradeRA1` | team | +10% |
  | `^AfterburnersUpgradeRA1` | faction | ±15% |
  | `^UnstableIsotopes`, `^InfernoDoctrine` | faction | +20–25% |
  | Vril Infusion (Schwarzer Mond) | faction | +25% and a 25%-of-HP shield |

  So: **team ≈ 5–10%, faction ≈ 15–25%.** When a team upgrade shares a mechanic
  with a faction upgrade, give it half the number so the law is visible in the
  yaml itself. (`^StaliniumTeamUpgradeRA1` at `Modifier: 80` is the one outlier
  and should be revisited.)
- ⭐ **A TEAM UPGRADE MUST FIT THE FACTION'S IDENTITY, not just be a good effect**
  (maintainer, 2026-08-15). The team upgrade is a statement about what the
  faction IS, so it has to reflect that faction's focus — Schwarzer Mond is
  high-tech, vehicles and aircraft, so an infantry-morale effect belongs to the
  Asian Alliance (whose Banzai upgrade already is one) or to the Naxis, not to
  SM. Check identity BEFORE mechanics: a mechanic that already exists and works
  is not a reason to attach it to the wrong faction.
- **ActorStatValues upgrade list** (design 2026-07-17): the `Upgrades:`
  field on `ActorStatValues` was expanded from a maximum of 5 entries to
  **10**. Every unit must list all faction upgrades (and only faction
  upgrades, never team upgrades) that affect it so the actor-stat widget
  can display the full set of upgrade icons. Gaps are bugs; additions or
  removals of upgrade inherits must be mirrored in the ActorStatValues list.
- AA gating, defense tiers, and tech trees per §4.

## 7. Descriptions & localization (rollout in progress)

- `\n` in yaml descriptions does not work anymore. **All names and
  descriptions live in Fluent files**; yaml references
  `actor-<id>.name` / `actor-<id>.description`.
- Scheme = RA1 Soviet style: one-line role summary; ability lines as
  separate indented lines; `Strong vs …` / `Weak vs …` at the end.
- Upgrade descriptions open with the tier tag ("Tech Upgrade (Only affects
  units of own faction)" / "Team Upgrade (…)" / "Promotion Upgrade (…)"),
  then one effect per line with exact stats and affected units (grouped
  when many). Promotion descriptions give a one-line summary of the
  unlocked unit.
- Every description is **verified against resolved traits, weapons, and
  upgrades** — it says what the unit does and the unit does what it says.
  Trait PRESENCE is not ability: a trait gated on RequiresCondition
  (crate cloaks, stealth-gen fields, spell states) is not an innate
  capability and must not be described as one. Weapon claims come from the
  weapon definition (inherits, warheads, reports), never from source-game
  lore — the Ghost Stalker's "railgun" was a lore error the code refuted.
- Rollout is incremental: one actor → review → one faction → review → all.
  Renames come FIRST so fluent keys are minted against final ids.

## 8. Assets & audio

- WAV norm: **mono / 16-bit / 22050 Hz** (audit_assets prints ffmpeg fixes).
- Sprites named per §1; icons end `_icon`.
- **Cameo/build/upgrade icons are always 64×48 px** (RGBA or RGB PNG;
  the mod-wide dominant size — design 2026-07-11). Any new icon,
  including upgrade research icons, is authored at 64×48. An upgrade
  actor's icon comes from a `sequences` entry named for the actor with
  an `icon:` sub-node (`Filename: <name>.png`), and the actor's
  `RenderSprites.Image` points at that same name — do not leave an
  upgrade borrowing a unit cameo.
- Voice sets are shared resources named for the VOICE, not a unit.
- **Custom animated effects (explosions, muzzle flashes, projectile
  trails) are authored as RGBA PngSheets** (design 2026-07-12; the
  proven pattern used by the neutron-shell `magicnuke.png` and the
  CABAL rocket trail `cabal_rockettrail.png`). A single horizontal PNG
  strip of equal-size frames carries two PNG `tEXt` chunks —
  `FrameSize: W,H` and `FrameAmount: N` — and a sequence references it
  with `Filename:`, `Length: N`, optional `Scale`, `Tick`. **An RGBA
  sheet renders in true colour with NO palette** — omit
  `TrailPalette`/`ExplosionPalette` entirely (this is why magicnuke
  looks right and why the smoke below broke when a palette was forced
  onto it). Keep effect frame counts small for trails (≤10, fading to
  transparent so each puff dies on its own).
- **Palette pitfall for indexed `x_smokey` trails**: they use the
  **`effect`** palette. `effect75alpha` is a D2K/Dune alpha palette
  (`PaletteFromPaletteWithAlpha`) — forcing it onto a non-Dune sprite
  like `blue_smokey` re-tints it (blue → dark green). Use `effect` for
  indexed trails, or an RGBA PngSheet (no palette) for full colour.
- **Per-frame randomness in animated effects (design 2026-07-12).** A
  new effect must NOT be identical geometry every frame — the first
  CABAL rocket trail came out as near-perfect spheres and read as
  low-quality. Give each frame small random offsets, distortion, and
  lobe variation (seeded, so it's reproducible) while still expanding
  and fading over time. Build soft fields with numpy gaussians, not PIL
  ImageDraw (which replaces pixels), and VERIFY the rendered preview
  before committing — a blank or bland sprite loads without error.
- **Effect-warhead naming LAW (design 2026-07-12).** The principle is
  **ONE `CreateEffect` warhead per impact surface**, named by that
  surface — because OpenRA overwrites same-named warhead nodes across
  inheritance, a canonical per-surface name guarantees exactly one
  effect survives and a weapon can never stack two overlapping impacts
  on the same surface. The legal names are:
  - **`Warhead@Effect`** — the ground/default impact (always this name,
    never `@2Eff`, `@3Eff`, `@DissolveEffect`, …).
  - **`Warhead@EffectAir`** — only when the weapon can hit air.
  - **`Warhead@EffectWater`** — only when the weapon can hit water.
  - **`Warhead@ShieldHitEffect`** — the `ValidTargets: Shielded` hit
    effect (shield-impact sound), present in the class templates.
  - The HeavyBomb template's two effects are the last sanctioned case.
  Rename anything outside this set to the matching surface name.
- **Effect + sound are always defined TOGETHER (design 2026-07-13).**
  A weapon with a bespoke impact/projectile effect must ALSO define its
  own `Report`/`ImpactSounds` — never leave either the effect or the
  sound to fall back to the class template's default. Falling back makes
  two different weapons look/sound identical and erodes each faction's
  identity; the goal is for every weapon (and especially every NEW impact
  animation) to be as unique as possible. When authoring a new effect,
  author (or assign a unique existing) sound in the same pass. Prefer new
  custom audio; cross-check Shattered Paradise for a fitting reference;
  only reuse a generic template sound as a last resort, and flag it.
- **Effect frame-fit check (design 2026-07-13).** An expanding effect
  drawn larger than its frame is clipped to a hard square in game
  (`cabal_dissolveimpact` v1 did this). Size radii/sigmas to fit, clamp
  each gaussian centre so `2.5*sigma` stays within a margin of the edge,
  and ASSERT the 2px border alpha is 0 on every frame. Render the preview
  with the frame border drawn (a red box) and Read it before committing.
- **CreateEffect `Image:` field — ALWAYS OMIT for the default explosion
  image (design 2026-07-15).** The `Warhead@Effect: CreateEffect` trait
  looks up its `Explosions:` sequence inside the image named by `Image:`.
  When `Image:` is omitted, the engine defaults to the `explosion` image
  defined in `sequences/misc.yaml`. All weapon impact animations
  (`magicnuke`, `magicnuke_med`, `magicnuke_small`, `magicnuke_micro`,
  `cabal_greenplasmaimpact`, `cabal_missileexplosion`,
  `cabal_laserimpact_s`, `cabal_laserimpact_m`, `cabal_laserimpact_l`,
  `cabal_dissolveimpact`, `poof`, `drplasmaex2`, …) are defined as
  sub-sequences under the `explosion:` key in `sequences/misc.yaml`.
  Setting `Image: explosion` explicitly is redundant but harmless; setting
  `Image: <custom>` for a sequence that lives under `explosion:` causes
  the engine to look for it inside the wrong image and **crashes with a
  missing-sequence exception**. The rule: **a weapon `CreateEffect` must
  never carry an `Image:` field** — leave it out and let the engine
  default to `explosion`. If a truly custom impact image is needed (one
  that does NOT live under `explosion:` in misc.yaml), define a new
  sub-sequence under `explosion:` instead and reference it by name in
  `Explosions:`.
- **Impact animations live in `misc.yaml` under `explosion:`, never in
  faction sequence files (design 2026-07-15).** All weapon impact/explosion
  animations — regardless of faction — are defined as sub-sequences under
  the `explosion:` image key in `sequences/misc.yaml`. This centralizes
  explosion rendering (full brightness, `IgnoreWorldTint: true`,
  `ZOffset: 2047` via the `Defaults:` block) and ensures the default
  `Image:` lookup works. Faction-specific sequence files (e.g.
  `CABAL/yaml/sequences.yaml`) must NOT define top-level image keys for
  impact animations. When a new impact animation is created, add it under
  `explosion:` in `misc.yaml` and reference it by name in the weapon's
  `CreateEffect` `Explosions:` field with no `Image:`.
- **Shared-image exception (design 2026-07-15).** When an image is used
  BOTH by a `CreateEffect` warhead AND by other traits (building
  `Effect:`, projectile `Image:`/`TrailImage:`,
  `SubterraneanTransitionImage:`, `HelixAnimSequence:`, `RingImage:`,
  etc.), the top-level image definition MUST stay in its sequence file
  for the non-CE traits. In this case the `CreateEffect` warhead KEEPS
  its `Image:` field — do NOT duplicate the sequence under `explosion:`.
  Only images used EXCLUSIVELY by `CreateEffect` warheads are moved
  under `explosion:` and have their `Image:` field removed. The audit
  tool `tools/audit_createeffect_image.py` flags all CE `Image:` fields;
  `tools/audit_ce_image_usage.py` determines which are CE-only vs shared.
  Known CE-only images already moved: `wc2_building_collapse`.
  Known shared images that keep `Image:`:
  `tsdig`, `tsioncannon`, `ionsfx`, `tspodring`, `tsmcnealmechdrop`,
  `tsdroppod`, `hakurei_giphy`, `hakurei_dream`, `wc2_effect_sparkle`,
  `wc2_effect_sparkle_circle`, `wc2_effect_heal`, `wc2_exorcism`,
  `wc2_catapult_impact`, `wc2_lightng`, `wc2_effect_blizzard`,
  `wc2_catapult_stone_projectile_medium`, `wc2_effect_death_and_decay`,
  `wc2_effect_daemon_attack`, `wc2_cannon_impact`, `wh40kcapsule`.
- **Corpse-spawner exception (design 2026-07-15).** `ra2corpse` is NOT
  an explosion — it is a corpse spawner that uses `CreateEffect` with
  multiple `Explosions:` entries (`death_a`–`death_f`) to pick a RANDOM
  corpse animation each time. The `Image:` field MUST be kept because
  the engine needs to resolve the random sequence from the `ra2corpse`
  image's own sub-sequences, not from the `explosion:` image. Moving
  these under `explosion:` would break the random-pick behaviour.
  `ra2corpse` stays as a top-level image in `sequences/redalert2.yaml`.

## 9. Operating rules for agents

1. **Read the ENTIRE DESIGN.md into your context before touching ANY yaml
   file.** Not a grep, not a search, not a summary — the full file, every
   session, every time. This is non-negotiable. Skipping this step causes
   violations of stat rules (Speed steps — 5 for vehicles/aircraft/ships,
   1 for infantry, HP steps, TurnSpeed formulas, price quantization) that
   are all documented here. If you find yourself
   about to edit a yaml file and you have not read this document in full
   this session, STOP and read it first.
2. Read this document, then `docs/audit/SUMMARY.md` for current state.
3. **Changing ANY unit stat (HP, Speed, Damage, ReloadDelay, Range, Cost)
   requires a FULL REBALANCE of that unit using the balance formula (§12).**
   You cannot change one stat in isolation — the formula ties all stats
   together, so changing Speed changes the unit's power, which changes the
   correct price or requires adjusting other stats to hold the price. The
   rebalance MUST move through the raw ledger (`docs/balance/*.json`) or an
   unlocked cell in one of the two active generated workbenches, then land in
   yaml through the guarded balance pipeline. Regenerate both
   `cameo_balance_by_faction.xlsx` and `cameo_balance_by_type.xlsx` in the same
   pass. The legacy `cameo_armor_system.xlsx` is reference-only and is not a
   required second write. Never change a stat without updating the ledger and
   verifying the formula still holds. If the range is beautiful (6.000, 7.500), adjust
   HP/Damage instead of Range. If the new Range would violate promotion
   superiority, adjust HP or Price instead.
4. Run the relevant audit before and after your change
   (`tools/audit/run_all.sh`, or a single `audit_*.py`).
5. Classify bugs as B1–B12 (MASTER_REPORT §4); if the class detector
   missed your bug, improve the detector in the same change.
6. Small typo-class fixes (wrong condition name, weapon-as-voice, swapped
   tooltips): **fix immediately and report it** so design knows.
7. Display-name changes and balance-affecting decisions: propose options,
   let design choose first.
8. Renames/refactors are proven behavior-preserving with resolved-diff
   snapshots; balance changes are never mixed into them.
9. Clean commits, one concern each; commit when design says so. Always
   update ALL relevant documentation files (ROADMAP.md, audit summaries,
   lessons learned, etc.) BEFORE committing — check old docs for outdated
   info, inconsistencies, and contradictions, and fix them. A commit
   without updated docs is an incomplete commit. Boot-gate with
   `launch-game.cmd` before every commit: launch the game, wait for main
   menu, kill process, check for new exception logs. `utility.cmd cameo
   --check-yaml` is a separate linting tool (not a boot-gate substitute) —
   use it for verifying cosmetic refactors, checking broken prerequisites,
   and detecting gameplay-relevant YAML issues. Goal: 0 errors AND 0
   warnings. The utility takes a very long time — only run it when all
   connected tasks are done and you expect 0 errors/warnings to confirm.
10. Every new unit ships with: naming-compliant id + `_icon`, Fluent keys,
   ai.yaml wiring, roster-wide upgrade hooks, class template, sequences
   that resolve, and a changelog line (Definition of Done,
   MASTER_REPORT Appendix D).
11. **Always separate top-level elements with a single blank line** —
   every actor, weapon, template, and sequence block is followed by an
   empty line before the next one, so it is easy to see where one ends
   and the next begins. A comment block stays attached (no blank line)
   to the element it documents. Scripted edits must preserve the blank
   line (a common bug: a block-replace that drops the trailing blank).
12. **All icons carry the `_icon` suffix** (§1/§8), including upgrade
   research icons: `ordos_upgrade_hoverdrive_icon.png`, never
   `ordos_upgrade_hoverdrive.png`.

## 10. Actor & faction uniqueness (design north star)

- **No two units or defenses use identical weapons.** Every armed actor
  owns its own weapon entries (`audit_weapon_uniqueness.py`). Sharing is
  legal only inside one actor's own variant family (`_sp`/`_elite`/husk/
  paradrop twins, garrisoned armaments of the same actor) and for
  systemic utility weapons (C4, DefuseKit, capture/heal/repair tools).
- Beyond weapons, every actor should be **unique in its own stats and its
  weapons' stats** — each actor has its own character and feeling. No two
  actors of a faction may feel the same, and especially no two actors of
  DIFFERENT factions may feel the same. Factions express identity through
  themed actors; uniqueness is a faction-identity feature, not polish.
- **NO mirror factions; no shared stats (Warcraft 3 approach).** Cameo
  deliberately never mirrors one faction against another — vanilla Warcraft 2
  makes Humans/Orcs stat-identical and that is boring. Every faction has a
  distinct identity, AND **every individual unit has its own stats: no two
  units may share the same value of a balance stat** (HP, Speed, effective
  damage-per-shot = Σwarheads×FirepowerMultiplier, RAW ReloadDelay, Range)
  within their comparison class. WC2 Human/Orc counterparts (Footman↔Grunt,
  Knight↔Ogre) are therefore re-statted apart, never mirrored. The lore-directed
  DIRECTION of each faction's stat lean is in `design/FACTION_IDENTITY.md`
  (source-cited); the 5-stat uniqueness is enforced mechanically by the balance
  pipeline.
- Weapon-dedup findings are **balance/design work**, never mechanical
  auto-fixes: propose per-actor stat divergence options, let design
  choose, then implement.

## 11. Garrison weapons (audit_garrison_weapons.py)

- **Every garrison-capable infantry with a damaging weapon carries a
  garrisoned armament** (`Name: garrisoned`) — commandos included (the
  Ordos Face Dancer is a commando in Cameo, so he fires from garrisons).
- Design exceptions live in `docs/design/garrison_exceptions.yaml`:
  melee, suicide/bomb attackers, and casters/mind-control do not fire
  from garrisons. Engineers without combat weapons and units garrisons
  cannot accept (non-Infantry CargoType) are auto-exempt.
- **G2 miswire class**: an `Armament@GARRISONED`-style block WITHOUT
  `Name: garrisoned` silently becomes a second primary — double-fire in
  the open, silence in bunkers (live cases: TS engineer pistol, RA1
  Imperial Scoutsman, M113 Adats-style condition typos).
- **G3: garrisoned armaments never carry a FireDelay.**

## 11b. ONE WARHEAD PER WEAPON (binding, maintainer 2026-08-16)

**A weapon has exactly ONE damage warhead.** This is the damage half of the 3-way split
(**1 warhead + 1 projectile + 1 effect**) and it is a fixed rule, not a target to drift
toward. It was practised but never written down, which is how the tree accumulated the
debt below.

Measured 2026-08-16 across every concrete weapon:

| main damage warheads | weapons | |
|---|--:|---|
| **1** | 805 | **39% — compliant** |
| 2 | 457 | |
| 3 | 284 | |
| 4 | 248 | |
| 5–15 | 258 | worst case: 15 |

**Not counted as damage warheads** (these may coexist with the one main warhead):
`*_Percentage` (the %-twin), `*_ExtraDamage` (the shield chip), and every non-damage
warhead — `CreateEffect`, `LeaveSmudge`, `GrantExternalCondition`, `ApplyPhysicalState`,
`SpawnActor`, `AffectsIntegrity`.

### 11b.1 TIGHTENED AND ENFORCED (binding, maintainer 2026-09-06)

The 2026-08-16 rule above was practised but never *enforced*, and an exemption grew up
beside it that quietly contradicted it. The maintainer restated and tightened it:

> *"From now on we will no longer allow any more multi-warhead weapons. The only thing
> every weapon is allowed to have are exactly 3 inherits: warhead, projectile and effect.
> No more dual warheads, dual effects or dual projectiles or anything else. Also no more
> effects directly on the weapon itself — it should all come from the inherited templates.
> The only thing allowed are special cases like those fire-shrapnel weapons or applying a
> condition."*

Three clauses, beyond the one-main-warhead rule already stated:

1. **Exactly three inherits.** `^Warhead_*`, `^Projectile_*`, `^Effect_*` — one of each, and
   nothing else. A weapon inheriting two warhead templates, two projectile templates or two
   effect templates is a defect, and so is a fourth inherit of any kind.
2. **No effect warheads declared on the weapon itself.** `CreateEffect`, `LeaveSmudge`,
   `GlowImpact`, `FlashPaletteEffect` and `DamagesConcrete` come from `^Effect_*`, never from
   the concrete weapon's own body. The weapon body carries scalars only.
3. **The narrow exceptions**, and only these: a warhead delivering a MECHANIC rather than a
   second damage profile — `FireShrapnel` / `FireFragment` / `FireCluster`,
   `GrantExternalCondition` — plus the `*Percentage`, `*FriendlyFire` and `*ExtraDamage`
   halves of one main.

⛔ **This REPEALS the `intentional_composites.py` exemption.** That registry recorded 224
multi-main weapons as reviewed and deliberately kept, and `audit_three_way_split` excluded
them from its backlog. Under this ruling they are not exempt — they are the worklist. The
registry's DATA stays useful (it records which mains were chosen on purpose, which informs
the survivor choice); only its meaning flips.

**Measured 2026-09-06 by `tools/audit/audit_weapon_shape.py`**, which enforces all of this
on LOWER-ONLY ratchets — 2,031 concrete weapons carry inherits:

| check | violation | count |
|---|---|--:|
| W5 | more than one resolved MAIN warhead | 401 |
| W1 | more than 3 inherits | 583 |
| W2 | two or more `^Warhead_*` inherits | 221 |
| W4 | two or more `^Effect_*` inherits | 61 |
| W3 | two or more `^Projectile_*` inherits | 21 |
| W6 | effect warheads declared locally | 687 weapons / 1,040 nodes |

⚠ The audit also reports an INFORMATIONAL count of weapons missing one of the three
inherits (1,142 no `^Warhead_*`, 1,348 no `^Projectile_*`, 1,230 no `^Effect_*`). That is a
**review queue, not a defect count** — an instant or utility weapon may legitimately have no
projectile — and it must not be bulk-converted or ratcheted without a per-weapon design pass.

⚠ **The value rule when collapsing is TOTAL OUTPUT PRESERVED.** Maintainer, 2026-09-07:
*"make it so the total damage output remains the same after the collapse."* There is ONE rule, not two.

The survivor's `Damage` = Σ of the weapon's **RESOLVED MAIN** warheads
(`formula.spread_damage_sum`, each first mapped through its family ratio). **"Verbatim" is not
a second rule** — it is what that sum degenerates to when the weapon resolves to exactly ONE
main, no matter how many templates it inherits. That is why the earlier "VERBATIM, never the
SUM" phrasing was wrong as a general law: it read a one-main case as if it were the rule.

* **Many inherits, ONE resolved main.** `D2K_APC_Rocket` carries SIX inherits and resolves to a
  single `MissileAP_Medium` main at 24000. Cutting it to three inherits moves no damage,
  because Σ over one main is that one number. This is the case people call "verbatim".
* **Several resolved MAINS.** `TSZoneHellfireSonic` resolves to `MissileAP_Heavy` 24000 **plus**
  `Sonic_Heavy` 16000. The engine applies both warheads, so the weapon delivers 40000 and the
  survivor must be 40000. Equal-damage mains are no exception — if it really lands twice today,
  the survivor lands the total.

⛔ **Count the RESOLVED MAINS, never the inherits.** The two cases are indistinguishable in the
source and differ by a factor of N in what the weapon actually does.

⚠ **The HydraSpit conversion (`8748c68e4`) is cited in older notes as the "verbatim" precedent.
It is not** — and measuring it against the last SHIPPED build shows why a collapse must never be
judged on the tree's own numbers alone. Measured 2026-09-07 against `playtest-20260709`
(Tournament Build 24):

| | flat per shot | percentage half |
|---|--:|--:|
| shipped release | 4 mains x 2000 = **8000** | 4 x 1% = **4%** |
| pre-collapse (`8748c68e4^`) | 4 mains x 18000 = **72000** | — |
| now | 1 main x 18000 = **18000** | **9%** |

The collapse was NOT the origin of the defect: an earlier sweep had inflated the per-main value
**2000 -> 18000 (9x)**, and the collapse took the weapon from 9x the shipped damage down to
**2.25x**. It is a partial repair of an upstream inflation, not a clean conversion — and the
weapon still deals 2.25x what shipped, on BOTH halves.

⛔ **A collapse is only verifiable against a baseline outside the tree.** 1321 of 1559 weapons
shared with `playtest-20260709` carry byte-identical total main damage, so the damage scale did
NOT move and the comparison is valid — but **238 weapons have drifted from the shipped build**,
in both directions (`AsianTSIonCannon` 7.67x, `MarineMG` 6.00x; `wc2ogremageRunes_Hit` 0.11x
after 10 mains became 1). Re-check a conversion against the release tag, not against the commit
before it.

### 11b.1a TEMPLATE ONLY — never from another weapon (binding, maintainer 2026-09-12)

The maintainer restated the law and closed the one hole in it:

> *"every weapon needs to have exactly 1 warhead, 1 projectile, 1 effect inherited from a
> template only and **NEVER from another weapon**"*

`§11b.1` constrained the COUNT of inherits. It did not say where they must come from, so a
weapon could satisfy it with exactly three parents and inherit all three from other weapons.
Nothing measured that: `audit_weapon_shape.py` W1 counts arity only. Measured 2026-09-12 over
2,448 concrete weapons:

```
W7  inherits from ANOTHER WEAPON              957   (655 distinct weapon-parents)
W8  inherits a ^Template outside the 3 kinds  874   (198 distinct legacy templates)
```

**THIS OVERRIDES §10's variant-family exemption, for inheritance only** (maintainer ruled
2026-09-12, asked explicitly). §10 permits two weapons in one actor's variant family to SHARE
a weapon; it does not permit a variant to INHERIT its structure from the base weapon. So
`X_elite: Inherits: X` is a violation and must be rewritten to carry the three `^Template`
inherits itself. That is 481 of the 957 — `_elite` 168, `_aa` 43, `2` 24, `_emp` 13,
`_upgrade` 11 — and it is the drift-prone half, because each variant must also reproduce
whatever its base declared LOCALLY. Prove every batch with
`tools/audit/review_resolve_diff.py`; a missed local override is a silent behaviour change.

### 11b.0 MAINTAINER RULINGS, 2026-09-12 (the reference/pricing/ammo session)

Nine decisions, all asked and answered the same day. They supersede anything earlier that
disagrees, and several of them CANCEL work that was already specified.

**R1 — Weapon stats are referenced SEPARATELY; total DPS is a VERIFIER, not a target.**
> *"each individual stat like damage per shot, burst, burst delay, reload delay should be
> referenced separately but also at the same time the total DPS should kept as a verifier so
> nothing suddenly becomes too extreme"*

So `w_damage`, `w_burst`, `w_reload` (and burst delay, once referenced) are each applied from
their own projection, and `w_dps` becomes a **guard rail**: if the composed result drifts far
from the DPS target, that is a flag to look at, not a number to overwrite the components with.
⛔ This CANCELS the "DPS is authoritative, decompose_dps solves the rest" reading. The five
targets never composed — 1.42x apart on `td_gdi_mammothtank`, 1.64x on `td_gdi_mlrs` — and the
resolution is that four of them are inputs and the fifth is a check.

### R1 implemented, 2026-09-12

`reference_targets.COMPONENT_STATS` / `VERIFIER_STATS`, `compose_dps`, `recover_burst_time`,
`dps_guard` (+ `_guard_self_test`), and a **DPS verifier column** in the reference map, which
now also carries the **source damage coordinate** and **Reload** as their own columns. Burst delay stays OUT of
the map, as ruled. The verifier is diagnostic-only and is withheld unless the row carries an
explicit damage convention plus a complete burst-delay sequence; the current peer corpus does
not provide that compatible evidence.

`EXTREME_RATIO` 2.00, `DISAGREE_RATIO` 1.25 remain the proposed diagnostic thresholds; they are
not currently producing verifier claims because the compatible convention and delay evidence is
missing from the peer corpus.

⛔ **`w_damage` MEANS DIFFERENT THINGS IN DIFFERENT SOURCES, and reading it wrong
double-counts burst.** `extract_peer_units` sets `w_damage = audit["damage_pos"]` — damage per
SHOT — with `w_dps = damage_pos x burst / cycle`. The frozen Cameo snapshot's `w_damage` is
**burst-INCLUSIVE**, with `w_dps = w_damage / cycle` and no burst factor at all. Proven on the
shipped rows: mammoth `32000/400 = 80` ticks against `w_reload 72`; MLRS
`48000/352.94 = 136` against `w_reload 111`.

The cycle is recoverable only after the row's damage convention is explicit: per-shot rows
multiply by `Burst`, while burst-inclusive rows do not. A complete delay sequence is still
required for composition because burst delays may vary. The first implementation inferred the
convention from `damage / DPS` and could silently compare unlike rows; the corrected guard now
withholds that case instead of manufacturing a verifier result.

⚠ **A burst change alone barely moves DPS, and must not read as extreme.** Burst reaches DPS
only by lengthening the cycle through burst delays; under a burst-inclusive `w_damage` it is
not a multiplier. The MLRS target drops burst 6 → 2, which SHORTENS the cycle and nudges DPS
*up*. `_guard_self_test` asserts this case permanently.

**R2 — Reference everything first, INCLUDING price; then fit to the formula, and BOTH may move.**
> *"we first reference everything including prices and then try to fit everything inside the
> balance formula as good as possible which means prices can move but so can the stats to
> reduce the delta as much as possible"*

**R3 — But the VIRTUAL BASELINE ACTORS COME FIRST, and the formula cannot do anything until
they exist.** The binding order of operations:

1. Reference every actor — stats AND price (done for 186; `reference_assignment.json`).
2. Derive a **virtual baseline actor per class** from that reference data
   (`derive_virtual_anchor.py`, `EXTRAPOLATION_PROGRAM.md`).
3. **Fit the base band**: every member of a class must land inside the documented
   **100%–250% price band**. ⭐ **The BASELINE is the free parameter, not the actors**
   (maintainer, asked explicitly): choose the baseline so the real members already fall in
   band. Nothing about a live unit changes to make the band fit — a member still outside
   afterwards is a genuine outlier to look at, and that is the point of the exercise.
4. **Parameterise the formula for that class** from the fitted baseline.
5. **Only then price**, letting price and stats both move to shrink the reference-vs-formula
   delta (R2).

⛔ Steps 4 and 5 are IMPOSSIBLE before 2 and 3. `apply_balance --confirm` being a no-op is not
a bug to route around; it is this ordering being enforced. Signed-off anchors today: **0**.

### R3 measured, 2026-09-12 — `tools/balance/fit_baseband.py`, report `docs/balance/baseband_fit.md`

Step 3 is governed by two facts about the band that are geometric, not statistical, and both
change what "fit the band" can mean.

⛔ **`cost0` CANNOT MOVE THE BAND.** The ratio is `class price / cost0`, and
`class_baseline_estimators` multiplies every estimator BY `cost0`, so it cancels exactly:
ratio = `[(h+s+r+d)/4 + (h·s+r·d)/2 + h·s·r·d] / 3`. Re-pricing a baseline changes what the
class costs and moves **nothing** into band. Only `hp0`, `speed0`, `range0_wdist` and `dps0`
do, through `h = hp/hp0` and its siblings.

⛔ **THE BAND DOES NOT SURROUND THE BASELINE — IT STARTS AT IT.** At the baseline
h=s=r=d=1, so the ratio is exactly **1.000**; the 2×HP/2×DPS verifier is exactly **2.500**. So
100%–250% means *"from the baseline to its verifier"*, and "every member in band" requires the
baseline to sit at or **below** the weakest member. The decay is steep and has no shoulder: a
member weaker by 10% on every axis already prices at **78.9%**, under the 75% floor.

⚠ **Therefore a MEDIAN-derived baseline can never satisfy the band** — it puts half the class
below 100% by construction. `derive_virtual_anchor.py` proposes reference-backed class medians,
which correctly answers *"what is typical"* and cannot answer *"where does the band start"*.
Those are different questions; step 2 currently supplies the first to step 3.

**Measured over 404 priced members in 24 formula-priced classes:** 115 (28%) in the sweet spot
today; re-scaling every class baseline uniformly reaches only **271 (67%)**, short of the ≥80%
target. **21 of 24 classes span more than the 2.5× envelope** — up to **33.7×** (`melee`).

⭐ **But the spread is concentrated, and that is the finding.** Every class has a current-anchor
ratio window — the largest observed subset inside the 2.5× envelope — and those windows span
**1.4×–2.5×**, holding **290 of 404** members. The remaining **114** sit outside those
current-anchor windows. The extremes are triage signals, not proofs of a role or pricing defect:
`futuretech_blackwidow` is in **`melee`** with `Range: 9000`;
`corrino_buggy` is in **`mbt`** (25k HP, 100 DPS, cost 300); `cabal_enlighted` carries
**11,184 DPS** in `heavy_infantry` against a flamer's 181. `steelconsortium_hoverboardgrenadier`
prices at **3080%** of its class baseline.

**So the band is a CURRENT-ANCHOR TRIAGE SIGNAL, and step 3 is blocked on membership triage, not
on arithmetic alone.** Each of the 114 is one of three things and only a maintainer can say
which: misclassified, a legitimate higher tier needing a tech-tier gate, or genuinely
mis-stated. Uniform rescaling can change the nonlinear ratio spread, and an anisotropic baseline
could change it further; both need their own evidence before the window is treated as a fit.
`anchor_readiness.py` says the same from the other end — its "statistically
indistinguishable" class pairs are *"separated by what they SHOOT AT, not by their stats"*.

**The 114 triaged, 2026-09-12 (`fit_baseband.py --triage`).** ⛔ **A stat-based test does not
determine class membership or baseline feasibility.** Measured: the median member
is accepted by **6 of the 27** class baselines (mean 5.6, max 9), so "another class would take
it" is true of nearly everything and is worth nothing as evidence. The first version of the
triage used the best-fitting class as its deciding signal and labelled **81 of 114
MISCLASSIFIED**, which put `terran_ghost` in `artillery` on one arbitrary pick out of six.
Those labels would have read as authoritative and carried no information. `anchor_readiness.py`
already states the limit: these classes are *"separated by what they SHOOT AT, not by their
stats. No stat-based check can police these boundaries."*

What the band CAN contribute honestly: **80 AXIS OUTLIER** (one stat more than 2x off its class
core — a checkable fact), **30 ROLE REVIEW** (stats genuinely cannot decide), **2 NO CLASS
ACCEPTS** (`harkonnen_inkvine` at `raw_dps` 0.0x, `naxis_slave` at 0.1x — data defects, not
class questions), **1 ONE CLASS ACCEPTS** (`naxis_naximercenarysniper`, only `scout`, at 110%),
**1 LATER TECH** (`naxis_skymage` 390% at tier 0.75 vs a core of 1.00).

⭐ **61 of the 114 are driven by `raw_dps`** (41 hp, 9 range, 2 speed) — and that AGREES with the
binding order of operations instead of fighting it. `BALANCE_PROGRAM_PLAN.md` §0a puts weapon
STRUCTURE before pricing, W24 is still moving, and every anchor dossier already says *"No DPS
target is proposed while W24 moves"*. So the majority of band failures are attributable to the
one axis the pipeline has deliberately not settled: **the band cannot be fitted before W24
closes**, and the DPS-driven outliers are not yet evidence about class membership at all.

⚠ **`fit_baseband.py` cross-checks its own recomputation against `check_band.py` and refuses
to be believed without it.** The first run disagreed on **257 of 404** ratios: the anchor's
tier must come from the tier map via `anchor_actor`, not from the anchor's own `tech_tier`
field. Every number above is from the run that matches 404/404.

**R4 — Delete the `^Warhead_*_Flat` shims; the existing templates already cover it.** DONE and
boot-gated, via `tools/balance/retire_flat_shims.py`. Of 46 users **only 23 resolve
`PercentageScale: 0`** — the other 23 override it back to ~9990, so the shim's defining property
is cancelled for half of them. Users moved to the plain `^Warhead_<fam>_<level>`.
⚠ This REPLACES §11b.1b's "second template per family" plan, which is cancelled.

⚠ **Three numbers in the first draft of this ruling were wrong, and the corrections are worth
more than the ruling.** All three came from describing the shims rather than resolving them.

* **27 shims, not 26.** `^Warhead_TS30mmRail_Unscoped_Flat` is a legacy shape with no plain
  twin and no user — deleted outright.
* **"Near-clones differing only by `PercentageScale`" was false: ZERO of the 26 were clones,**
  so the deletion was never a rename. Four independent differences: `Damage: 0` vs `2000`
  (moot — all 46 users set their own); **weapon-level** fields present only in the twin
  (`Range`, `ReloadDelay`, `TargetActorCenter`, `ValidTargets` — a `^Warhead_*` template is
  NOT only warheads, the same trap that once stripped `TargetActorCenter` off 60+ weapons);
  extra warhead nodes only the twin ships (`*_ExtraDamage`, `*_Percentage`, 7 user instances);
  and Versus rows off by up to 4.
* **The Versus delta is convergence, not regression.** `gen_weapon_template.py` never emitted
  `_Flat` — grep it. The shims were legacy orphans outside the generator's authority, which is
  precisely why they drifted from the regenerated twins. 34 distinct armor rows moved, worst by
  **4 points** on a mean-100 scale. Local compensation is impossible anyway: `Versus` may live
  only in a template.

**The load-bearing discovery: 11 weapons declare `Warhead@X` and then delete it again with
`-Warhead@X`.** That is dead code only while the live node is named `Warhead@X_Flat`. Rename it
to `Warhead@X` and the dormant removal deletes the real main, which is then re-added at the END
of the warhead list — a **firing-order change**, the same class as the Wraith. Any future
rename of this shape must check whether the target name is already mentioned in the weapon.

**R5 — "Flat warhead" means a profile that does not discriminate, and none exist.** The shape
law is the **2x–8x Versus spread band with 4x the target** (§ the target-band rule). Measured
over 190 `^Warhead_*` templates: minimum ratio **2.00x**, median 4.62x — **zero flat warheads**.
The `_Flat` NAME was the problem, not the shape.

**R6 — corrected: TWO templates exceed 8x, not nine, and only ONE is real work.**
⛔ **The "nine" came from computing max:min over ALL 22 Versus rows, including `Shield`.**
`Shield` is not a normal armor — §12.0c gives it its own compressed [100,400] ladder — and
`audit_versus_profile.py` has always excluded it, along with the five physical-state
pseudo-armors: `NON_ARMOR = {Shield, HAZMAT, COMPOSITE, BLAST, REFLECTOR, ARMOR}`. Measured on
the 16 real armor rows over 167 templates:

| template | armor-only | with `Shield` folded in | verdict |
|---|---|---|---|
| `MissileAP_Heavy_D2K_ORocket` | **12.50x** | 12.50x | genuinely out of band — pull it in |
| `Sniper_Light` | 10.00x | 11.00x | `HAND_TUNED`, ratified, generator skips it |
| `MissileAA_Medium` | 7.35x | 7.35x | in band (next highest) |
| `Laser_Medium` | **4.84x** | 8.44x | **in band, on the 4x target — do nothing** |

`Storm_*` and `Tesla_Heavy` are likewise in band and were ratified against inflated figures.
`audit_versus_profile.py` reports **spread 0/0** and has done so since 2026-08-22 — a tool
already implementing the law disagreed with the measurement, which by the standing rule makes
it a contradiction to check, not a finding to act on. The ratified specialists may still be
recorded in `aggregate_archetype.SPECIALIST_RATIOS`, but as authored exceptions, not as band
violations. **Never fold `Shield` into a spread-band ratio.**

**R7 — The heaviness bell stays OFF until W24 closes.** Re-confirmed after being asked directly.
`USE_BELL` remains false; W24 is not closed (W7 **957**, W8 **858**). Finish W24, then flip the
bell as its own boot-gated change. ⛔ Do not enable it to fix R6 — and after R6's correction
there is exactly **one** template to pull in by hand, not two.

**R8 — CARRIER SLAVE AMMO, exactly specified.** Every `CarrierSlave` gets `AmmoPool` +
`ReloadAmmoPool`. All 19 break this today (8 have no pool at all, which `CarrierSlave.cs:59-65`
turns into *unlimited ammo*; 11 have a pool nothing ever refills). Fix 17 — skip
`tkmsuicidedrone` and `farasha_drone_ixian`, which die on impact.

> *"ammo pool should be made so that firing all weapons on the target in a single burst attack
> will empty the ammo completely ... reloading from empty to full should always take 100 ticks
> ... If the unit has more than one weapons you need to make the ammo pool and the ammo
> consumption per weapon so that both consume the ammo pool equally fast."*

The rule, mechanically:
* **one concurrent armament:** `Ammo = Burst`, `AmmoUsage = 1`. A burst-10 MG gets `Ammo: 10`.
* **N concurrent armaments:** give each an EQUAL share. `share = lcm(Burst_i)`,
  `AmmoUsage_i = share / Burst_i`, `Ammo = N x share`. The worked example: MG burst 10 and a
  dual rocket burst 2 -> share 10, MG usage 1, rocket usage 5, `Ammo: 20`.
* **refill is ALWAYS 100 ticks empty-to-full:** `Count / Delay = Ammo / 100`. `Ammo: 10` ->
  `Delay: 10, Count: 1`; `Ammo: 20` -> `Delay: 5, Count: 1`; a pool that does not divide 100
  evenly uses `Count > 1` (`Ammo: 6` -> `Count: 3, Delay: 50`).
* **upgrade-granted weapons take `AmmoUsage: 0`** so they never interfere; only CONCURRENT
  weapons enter the share calculation.

✅ **DONE 2026-09-12, boot-gated** — `tools/balance/carrier_slave_ammo.py` (the law, with both
worked examples as its self-test) + `apply_carrier_slave_ammo.py` (placement only).
`audit_ammo_cadence` A2 ratchet **19 → 0**. Two refinements the data forced, both of which the
ruling as written would have got wrong:

* ⛔ **A REPLACEMENT PAIR IS ONE SLOT, AND BOTH SIDES MUST SPEND AMMO.** "Upgrade weapons take
  `AmmoUsage: 0`" is right for an ADDITIVE upgrade (`RequiresCondition: X` with no sibling on
  `!X`) — `cruiser_f.steel`'s quantum secondary. It is WRONG when siblings carry `X` and `!X`,
  which is a swap, not an addition: `japan_zerofighter_slave` runs both its live armaments on
  the `X` side, so zeroing them would leave the upgraded unit consuming **no ammo at all** and
  firing forever. Detect the negated sibling; give both sides the same usage; count the slot
  once.
* ⛔ **N IS NOT THE ARMAMENT COUNT — it is the largest group sharing a target class.**
  `A10Carrier`'s `Armament@AA` is `ValidTargets: Air` and its `@BOMBS` is `Ground, Water`; they
  can never fire at one target, so N=3 would build a pool no single attack could empty. With
  N=2 both engagements empty it exactly: ground `10x1 + 1x10 = 20`, air `10x1 + 2x5 = 20`.
* **Scope is 14, not 17.** 19 − 2 assumed the maintainer's two names were all the suicide
  drones; three more qualify under the same rule (`SCSCOURGEDRONE` self-destruct weapon,
  `kami.asian` and `tsprobe` via `SpawnedExplodes`). The two NAMED ones carry no suicide trait
  at all — their self-destruct is in the weapon — so the explicit list and the detector are
  both required, and neither alone suffices.
* ⚠ **`AmmoPool.Armaments` defaults to `primary, secondary`** and `AmmoPool.Attacking` only
  calls `TakeAmmo` when the list contains the armament's `Name`. An armament named anything
  else spends nothing and the pool never empties. Write the list whenever the default does not
  cover every armament.
* ⭐ **Preferred long-term solution, and the most complicated:** a condition-driven multiplier
  that dynamically DOUBLES the pool while an upgrade is active, so upgrade weapons can consume
  ammo properly instead of being zeroed. Maintainer's stated preference; not yet designed.

**R9 — An AMMO POOL MAKES `ReloadDelay` THE WRONG CLOCK.** See `tools/balance/ammo_cadence.py`
for the four regimes and `audit_ammo_cadence.py` for the census. 145 actors have a pool and
nothing in `extract_stats` / `reference_distribution` / `formula` mentioned it. Helicopters are
compared on *pool damage / time to empty*; airfield planes on **damage per sortie with no rate
at all**; 12 single-shot pools have no rate either.

### R10-R15 — the DEPRECATED-NAME sweep (maintainer, 2026-09-12)

> *"those names are already deprecated and weapons like those should no longer exist. If you
> find anything like that it is a bug"* — and, asked which cohort first: **"all of the above"**.

⛔ **Finding a deprecated warhead name is a BUG REPORT, not a balance question.** The framing
that treats `1Dam` or `*FlatCompatibility` as "a legacy main we might fold" is wrong: these
names were retired, so their presence is debt to be cleared, not a trade-off to be priced.

Measured 2026-09-12 across the resolved ruleset — **~983 deprecated warhead-node instances**:

| cohort | instances | note |
|---|--:|---|
| `*Compatibility` nodes | **586** (43 distinct) | `Bullet_MediumFlatCompatibility` 130, `Laser_Heavy…` 47, `Flak_Medium…` 46 |
| legacy `<n>Dam` / `Damage` / `IonCannon` / `Temperature…` | **397** (17 distinct) | **`1Dam` alone on 277 weapons** |
| `^Compatibility_*` templates | **36** defined | 35 have users, 369 (weapon, shim) pairs |

**R10 — A PURE RENAME NEEDS NO WARHEAD PERMISSION.** Rule 4 governs changes to a warhead; it
does not govern its NAME. When the resolved node is identical except for its key, this is
naming work (rule 9). Every batch is still gated by `resolved_gate` (field SET **and** firing
ORDER) and boot-gated. A fold or merge that actually moves per-armor damage still needs
explicit permission.

**R11 — `1Dam` is RENAMED to the family the weapon already inherits.** On the ~229 weapons
where it is the only main: `Warhead@1Dam` -> `Warhead@<Family>_<Level>` matching the
`^Warhead_` the weapon already has. The name is a legacy damage index from the source game, not
a family. ⚠ `1Dam` is NOT a 1-damage marker — the 48 stacked ones carry 1,200-50,000 damage.

**R12 — DELETE the 36 `^Compatibility_*` templates; the 214 exposed users get a per-weapon
suppression line.** Of 369 (weapon, shim) pairs: **139** already inherit the matching twin (chain
it, drop the weapon's duplicate direct inherit or that parent sits on one root-to-ancestor path
twice and the boot crashes); **214** do not and would silently GAIN the twin's content — up to
132 extra warhead nodes and 378 weapon-level field instances (`TargetActorCenter` 200,
`ValidTargets` 91, `ReloadDelay` 48, `Range` 39). Each of those gets a local line instead.
⭐ **MEASURE the suppressions, never predict them:** the same prediction on the `_Flat` shims
said 78 and the measured answer was **2**, because a later inherit already supplied the value.
⚠ This SUPERSEDES §11b.1b's "second template per family" blocker below, which was written when
56 of 64 families had both kinds of user; re-measured today it is **28 of 35**, and R12 resolves
it without new templates.

**R13 — the 16 orphan shims get their MISSING TEMPLATE GENERATED.** Where a
`^Compatibility_*` has no matching `^Warhead_<fam>_<level>` at all, run `gen_weapon_template`
for that family/level rather than inventing a local profile.

**R14 — the 7-main nuke cohort: check whether `AreaDamage` already expresses it.**
`4Dam_areanuke1` + `7/8Dam_areanuke2` + `10/11Dam_areanuke3` + `1Dam_impact` + `Damage` looks
like an imported three-ring blast. The maintainer's instruction is explicit: *"investigate if
that behavior can already be done with our new area damage warhead that we created to replace
those legacy things and if so do that then"*. So: read the real `Spread`/`Falloff` on each of
the seven, and if `AreaDamage`'s expanding rings reproduce it, convert — do not merely rename.

**R15 — boot-gate cadence: ONE PER COHORT.** Batch a whole cohort, verify with `resolved_gate`,
then one boot gate and one commit; bisect within the batch if boot fails.

#### 11b.1b `^Compatibility_*` — what it is, and why the collapse is not arithmetic

> *"Any of those silly compatibility warheads must be resolved and replaced by an actual new
> warhead"* — maintainer, 2026-09-12

**What it actually is.** `^Compatibility_<fam>Flat` is the **landing zone of an earlier W24
pass**, not scaffolding. Read `YamatoCannon`:

```yaml
Warhead@Demolition_Heavy:  Damage: 20000
Warhead@CannonHE_Heavy:    Damage: 20000
-Warhead@CannonHE_Heavy:
-Warhead@Demolition_Heavy:
Warhead@CannonHE_HeavyFlatCompatibility:
	Damage: 40000            # the two mains, already folded into one, parked on the shim
```

Someone collapsed two mains into one and parked the survivor on the shim. Those weapons are
already single-main and already correct; their only defect is that the template they inherit is
not spelled `^Warhead_`. Measured against its real twin, the shim's ladder is **identical on 10
families and differs by ±1 on one or two of 16 armor rows on 49** — MEAN-100 rounding drift, not
design. **So the fix is a RENAME and no `Versus` row, `Damage` or `Burst` changes: no warhead
permission is needed, because no warhead changes.**

⛔ **THE SHIM'S W8 VIOLATION IS LOAD-BEARING.** A blanket rename does not reduce the defect
count, it MOVES it: 240 of the 416 users also inherit a real `^Warhead_`, so spelling the shim
`^Warhead_` converts one W8 violation into one **W2** violation each (W2 177 -> ~400). The
rename is only worth anything together with the structural fix, and the structural fix is where
the difficulty sits.

⛔ **AND THE `^Warhead_` INHERIT IS NOT DEAD JUST BECAUSE ITS NODE IS.** The obvious follow-up —
"the weapon deletes `Warhead@<fam>` locally, so drop the inherit" — is wrong. A `^Warhead_`
template also carries **weapon-level** fields (`ValidTargets`, `ReloadDelay`, `Range`,
`TargetActorCenter`) and the shim carries **none**. Dropping the inherit silently stripped
`TargetActorCenter` off 60+ weapons and left three warheads with an EMPTY TYPE — the boot-NRE
class. A node-level deadness test cannot see either failure.

**The shape that does work** is a new template that CHAINS the twin, so the weapon-level fields
keep arriving once the weapon's duplicate inherit is dropped:

```yaml
^Warhead_Flame_Heavy_Flat:
	Inherits: ^Warhead_Flame_Heavy      # weapon-level fields arrive through the chain
	Warhead@Flame_Heavy_Flat: AreaDamage
		...                             # the shim's own body, verbatim
```

The weapon's `-Warhead@Flame_Heavy:` line **stays where it is** — putting the removal in the
template killed a LIVE twin main on `25mm`. The weapon's direct `Inherits: ^Warhead_Flame_Heavy`
**must go**, or that parent sits on one root-to-ancestor path twice and the boot crashes.

⛔ **ONE TEMPLATE CANNOT SERVE BOTH POPULATIONS, and that is the blocker.** A user that already
inherits the twin needs the chain; a user that inherits NO `^Warhead_` at all would **gain**
those weapon-level fields from it (measured: 112 weapons newly gained `Warhead@Bullet_Medium`,
11 gained `TargetActorCenter`). **56 of 64 families have BOTH kinds of user**, so those families
need a SECOND template each — the chained one and the standalone one — and a per-weapon routing
decision. That is the outstanding work, and it is template-count growth, so it needs a ruling.

**Landed 2026-09-12, provably behaviour-identical** (`tools/balance/promote_compatibility_warheads.py`,
which refuses to write unless every weapon's resolved node is unchanged through the name map):
33 of 69 templates, 55 weapons — 4 chained, 29 renamed, 36 mixed families skipped.
W8 874 -> 858, W1 26.30% -> 26.16%, W2 held at 177.

### 11b.2 The SEVEN kinds of multi-main weapon (the codemod's taxonomy)

`tools/audit/intentional_composites.py` was DELETED on 2026-09-06 — an exemption list cannot
coexist with §11b. Before deleting it, its one piece of non-derivable content was preserved
here: its 224 entries were not one problem but **seven**, and the split decides how each is
converted. Everything else in that file was redundant (`mains` is derivable from the yaml)
or self-referential (digests that only detected staleness of the registry itself).

| kind | weapons | what it actually is | conversion |
|---|--:|---|---|
| status payload | **112** | a damage main plus a state/meter warhead riding along | fold the payload into the one main; the meter stays if it is a `GrantExternalCondition` |
| target-routed composite | **67** | one weapon, several mains split by `ValidTargets` / armor route | ONE main; the routing belongs in the warhead template's Versus row, not in extra warheads |
| staged superweapon | **20** | multi-stage detonation (rings, delays) | `AreaDamage` already does rings and delays — one main with the ring profile |
| maintainer-approved role blend | **10** | a deliberate two-role gun (MG + cannon) | pick the family matching the resolved `Projectile:`; the second role becomes a separate weapon if it must survive |
| effect-delivery composite | **8** | a main plus a warhead that exists only to draw something | the drawing half moves into `^Effect_*` |
| maintainer-curated signature | **6** | a hand-picked main set (the `D2K_Rocket_Trooper*` pairs) | convert like any other; read the old set for intent when picking the survivor |
| percentage-scope compatibility | **1** | a `*Percentage` twin scoped differently from its main | already legal — the twin is not a second main |

⚠ **179 of the 224 are just the first two kinds.** The bulk of "intentional" multi-main was
never a design flourish; it was state payloads and target routing, both of which the current
warhead system expresses in ONE warhead.

### Collapsing a multi-warhead weapon

1. **Total output is preserved.** The survivor's `Damage` = Σ of the old MAIN warheads'
   damage, each first mapped through its own family ratio (`formula.spread_damage_sum`).
   Where the weapon had only ONE main and merely inherited several templates, that sum is that
   one number — i.e. verbatim. Collapsing must never change what the weapon deals in total.
2. **Pick the family that matches the weapon's IDENTITY**, not the one with the largest
   damage — check what it actually is (its projectile, its lore, its role).
3. ⚠ **If no existing family fits, CREATE A NEW ONE — do not force a bad fit.**
   Maintainer, 2026-08-16: *"every time you don't know how to collapse them you should
   suggest to create a new warhead family."* Blends are cheap: `^Warhead_MissileChem`,
   `CannonFire` and `CannonChem` are all blends of two parents, and a new family is a few
   lines in `gen_weapon_template.py`.

**Worked examples (both found by the W23 retrofit):**

- `japan_imperialscoutsman_rifle_waveforce` inherits `^WaveforceBulletWarhead` and is not
  a railgun. Mapping it to `Railgun_Heavy` was wrong — it needs a **`Waveforce`** family,
  proposed as a Plasma × Quantum blend (Plasma = Flame × Chemical; Quantum = Railgun +
  Laser + Tesla), i.e. anti-infantry from the thermal half and armour-piercing +
  anti-shield from the coherent-energy half, delivered wide with a shallow falloff.
- `GladiusCannon` carries four legacy warheads and inherits `PhotonCannon`, so it is an
  energy weapon. `Plasma` fits its "good against infantry and tanks alike" role directly.

**A weapon that cannot be collapsed is a design question, not a conversion blocker** — file
it, propose the family, and do not merge warheads by damage arithmetic alone.

## 11c. THE FACTION CROSS-WARHEAD LAW (binding, maintainer 2026-08-22)

**Basic warheads are what an un-upgraded unit fires. A faction's weapon UPGRADE swaps them
for that faction's CROSS warhead.** In the maintainer's words:

> *"every cross warhead needs to be based on the faction's specific technology — for example
> CannonTesla or MissileTesla for Soviet tech and CannonCryo or MissileCryo for Allied tech
> and CannonQuantum and MissileQuantum for Steel Consortium and so on, so that we have the
> tech for each faction to apply after the upgrades. Every faction should start with the basic
> warheads like CannonAP and CannonHE and MissileAP and MissileHE but later on the faction
> specific cross warheads are used for upgrades … Upgrades change warheads to faction specific
> cross warheads! Basic warheads are used for unupgraded units."*

This is the reason the `<Delivery><Tech>` blend grid exists. It is **not** a catalogue of
combinations observed in the tree — it is the **faction upgrade matrix**, and a missing cell
is a faction upgrade that cannot be built.

### The two halves

| | warhead family | example |
|---|---|---|
| **un-upgraded** | the PRIMITIVE delivery family | `CannonAP`, `CannonHE`, `MissileAP`, `MissileHE`, `Bullet`, `Demolition` |
| **upgraded** | `<Delivery><FactionTech>` | `CannonTesla`, `MissileCryo`, `BulletQuantum` |

### Which missile family — the ROLE decides (maintainer 2026-09-07) — binding

> *"If the unit is using the weapon against ground it will be missile he, and if the weapon is
> anti air then missile aa, but if the same missile is used against both then only missile AP.
> And missile he should never be used for anti air — that one is for anti ground rockets only."*

The weapon's own `ValidTargets` decides its family, and there is exactly one right answer:

| the weapon can hit | family | why that delivery |
|---|---|---|
| Ground / Water only | `^Warhead_MissileHE_*` | blast rocket, no reason to carry a fuze it never uses |
| Air only | `^Warhead_MissileAA_*` | **proximity fuze** — `PHYSICS_SHAPES` gives it Spread 300 / `Falloff 100, 70, 30, 0`, a blast radius of 900, because an AA missile has to detonate NEAR a moving target |
| both | `^Warhead_MissileAP_*` | shaped charge, Spread 64 / `Falloff 100, 0` — one direct-hit rocket that works either way |

⛔ **`MissileHE` may never be reachable against `Air`.** That clause is absolute; the other
three rows are the positive form of the same rule.

⚠ **This is a DELIVERY difference, not a label.** Swapping an AA mount from `MissileAA` to
`MissileAP` does not retag it — it removes the proximity blast, i.e. the mechanism that lets
the missile connect at all. Never "simplify" an AA weapon onto AP because the ladder looks
better; read `PHYSICS_SHAPES` first.

The **payload blends** (`MissileChem`, `MissileCryo`, `MissileFire`, `MissileNuke`,
`MissileQuantum`, `MissileTesla`, `MissileThermobaric`) are OUT of scope: a blend carries a
payload identity that outranks the role tag, and the ruling did not cover them.

**Measured 2026-09-07** by `tools/audit/audit_missile_role_family.py` (LOWER-ONLY ratchets) —
358 concrete weapons fly a `Missile*` main, **190 already conform**:

| code | violation | count |
|---|---|--:|
| R1 | ground-only not flying `MissileHE` | 51 |
| R2 | air-only not flying `MissileAA` | 33 |
| R3 | dual-role not flying `MissileAP` | 47 |
| R4 | `MissileHE` reachable against Air — the hard clause | 50 |

⚠ `df01cb590` set `D2K_Rocket_Trooper_AGOnly` to `MissileAP` the day before this ruling. Under
the rule it is ground-only and belongs on `MissileHE`; it is one of the 51.

### The mechanism already exists — do not invent a new one

The Steel Consortium quantum upgrade is the reference implementation: a pair of armaments
gated on the upgrade condition and its negation, swapping the WEAPON, which carries the
different warhead.

```
Armament@PRIMARY:
    Weapon: SteelQuantumTurretRail
    RequiresCondition: !steelconsortium_upgrade_quantumweaponpower
Armament@Upgrade:
    Weapon: SteelQuantumTurretRail_EMP
    RequiresCondition: steelconsortium_upgrade_quantumweaponpower
```

**55 armaments** in the Consortium pack already use exactly this shape. An upgrade that is
meant to convert a faction's whole arsenal ("this one should replace all the weapons with the
quantum versions") is that pattern applied across the pack, not a `FirepowerMultiplier`.

⚠ A condition/negation armament pair is ONE gun, not two. `audit_meter_dilution` and any
per-armament analysis must collapse the pair before counting, or an upgraded unit reads as
carrying double the weapons it fires.

### Named tech bindings (maintainer 2026-08-22)

| faction | signature tech | cross families |
|---|---|---|
| Soviet | **Tesla** | `CannonTesla`, `MissileTesla`, `BulletTesla` |
| Allied | **Cryo** | `CannonCryo`, `MissileCryo`, `BulletCryo`, `DemolitionCryo` |
| Steel Consortium | **Quantum** | `CannonQuantum`, `MissileQuantum`, `BulletQuantum` |
| *(resonance ammo upgrade)* | **Sonic** | `CannonSonic`, `MissileSonic`, `BulletSonic` |

Every other faction's tech binding is still OPEN and needs a maintainer ruling before its
cells are generated — inventing one would ship a faction identity nobody asked for.

### Grid coverage, measured 2026-08-22

4 deliveries × 8 techs = 32 cells; **16 exist**.

| | Fire | Chem | Cryo | Tesla | Quantum | Nuke | Sonic | Thermobaric |
|---|---|---|---|---|---|---|---|---|
| **Bullet** | ✅ | — | ✅ | ✅ | — | — | — | ✅ |
| **Cannon** | ✅ | ✅ | ✅ | — | — | ✅ | — | — |
| **Missile** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | — | ✅ |
| **Demolition** | — | — | ✅ *(`CryoBlast`)* | — | — | — | — | ✅ *(`Thermobaric`)* |

⚠ `Sonic` has **no** cell at all, so the resonance-ammo upgrade cannot be built today.

⭐ The Demolition row shows the naming exception worth knowing: a blast cell built from
`Demolition + Concussion + <element>` gets its OWN name rather than a `<Delivery><Tech>`
one, because it is not a delivery carrying a payload — it IS the explosion. `Thermobaric`
(fire) and `CryoBlast` (cold) are exact siblings of that construction, and `Concussion` is
what makes them read as detonations: radius 2100, the widest of any family, on a seven-point
curve that still does half damage at half its radius.

### Sharing is allowed — uniqueness is the goal, not a quota (maintainer 2026-08-22)

> *"sometimes the cross warheads can be reused by other factions IF it makes sense for them to
> have it. Not everything CAN be completely unique. There are not that many different types of
> Fire we can use … make it as unique as possible while still trying to keep our warheads down
> to a minimum without bloating it or making new nonsensical warheads just for the sake of
> uniqueness … Still try to keep it unique as the primary objective."*

So the faction→tech mapping is **many-to-one**. Two factions may share a cross family when the
tech genuinely fits both; what is forbidden is minting a near-duplicate family so that each
faction can own one.

**The test, in order:**

1. Does an existing family fit this faction's tech? → **reuse it.**
2. Does the faction's tech name a genuinely different physical mechanism? → build the cell.
3. Is the only argument "faction X should have its own"? → **reuse.** That is the bloat case.

The fire families are the worked example of the ceiling: `Flame` (the primitive),
`Thermobaric` = Flame × Demolition × Concussion, `Inferno` = Flame × Prism, `Plasma` =
Flame × Chemical. Four distinct fire mechanisms is close to everything the physics offers — a
fifth would be a relabel, not a weapon.

⚠ This does **not** relax `audit_family_uniqueness` (rule 8d): no two FAMILIES may share both a
radius and a curve. That guard is about the families being distinguishable in play, and it is
untouched by two factions pointing at the same family. Reuse costs nothing there; duplication
is exactly what it catches.

### Consequences for the splice programme

1. A cross family is justified by a FACTION UPGRADE, not by weapon-combination frequency.
   The `Concussion × Demolition` cluster (27 weapons) is a 3-way-split problem; `CannonTesla`
   (0 weapons today) is a REQUIRED cell. Frequency and necessity are different questions.
2. Cells are built from `BLEND_FAMILIES` with the delivery half averaging **AP and HE**
   together (§ the Cryo ruling: *"an in between blend of HE and AP so it fits with both
   versions"*), so one cell serves both an AP and an HE base weapon.
3. Always `splice_templates.py --all` — a new cell re-ranks the shield-coupling ladder.
4. **The generator owns every row it emits** (Claude ruling `47ba8bc25`, the CannonAP
   REFLECTOR row): a hand-edit to generated output has a countdown on it — the next
   `splice_templates.py --all` rewrites it. If a cell must differ, the fix belongs in the
   GENERATOR (spec, composition, or a ruling that changes the formula), never in the file.
   No `DERIVED_OVERRIDES` table, no composition nudge to force one cell, no ±1 tolerance
   whitelist — each of those hides real drift. `verify_generator_sync.py` drift is therefore
   always a generator-side bug or an un-landed splice, never a reason to "fix" the yaml.

## 12. Balance formula — the Cameo Armor System workbook

**Weapon Versus construction: see `docs/design/ARMOR_SYSTEM.md`** — the
step 6/5/4 = light/medium/heavy law (floor 10/25/40, Shield = 100+floor,
percentage warhead its own 1-step window), profile = armor order.

⚠ **That even-step law now applies only to the families Cameo INVENTED.** Since
W13 step 4 the ten families with reference coverage (Bullet, CannonHE/AP,
MissileHE/AP/AA, Laser, Prism, Flame, Tesla) take their magnitudes from the
measured corpus instead — `docs/reference/family_profiles.json`, consumed by
`tools/balance/gen_weapon_template.py`. Their floors come from §12.0's 10–25
band by level (25/20/15/10), not from the 10/25/40 above. The ORDER is unchanged: the
corpus supplies magnitudes, the ordering law supplies order.

⚠ **`Shield = top + floor` is RETIRED** (W25, 2026-08-16). It was written when every
profile peaked at exactly 100, so it produced the ceiling + floor; once profiles were
renormalised, "top" became a function of each family's SHARPNESS and the rule started
rewarding sharpness instead of anti-shield design — a sword read 200 while a Tesla coil
read 151. It is replaced by §12.0c below.

### 12.0 THE PROFILE SHAPE LAW (maintainer, 2026-08-15) — binding

Supersedes the "even step" half of the step law. Three rules, in force for every
`^Warhead_*` family:

1. **The profile's CENTRE is 100, and values above 100 are legal** (revised
   2026-08-15 from *"peak is 100"*; the centre statistic was revised again on
   2026-08-16 from the MEDIAN to the arithmetic **MEAN** — see §12.0h, which is
   the binding normaliser. The reasoning below is why a centre statistic beats
   the peak at all, and it holds for either one). Every profile is normalised so its
   own centre is 100, which is also how reference profiles from other mods are
   read — a source that writes 200/100 and one that writes 100/50 are recognised
   as the SAME design. Absolute lethality still lives in `Damage`, never in the
   armor profile.
   **Why the peak was wrong:** normalising to the maximum lets ONE outlier cell
   halve the entire rest of the profile. RA2's `Electric` warhead carries a 200
   against a single armor to tune one unit; read peak-first, Tesla came out at
   ~50 against infantry — a weapon that one-shots infantry, scored as mediocre
   against them. The median is robust to that, and a peak of 200 is no longer
   free: **K prices the profile**, so a weapon that is twice as good against its
   best target is priced as twice as good. The old cap existed only because the
   pricing formula could not yet see the profile. Ceiling: 300.
2. **It is still a LADDER — no two values identical, anywhere in the profile.**
   A tie is a wasted rung and makes the weapon unreadable. This is absolute: it
   applies to the DERIVED armors too, so it must be the LAST thing enforced —
   `Heroic` and `Airborne` are computed from other cells and can land exactly on
   one (measured: `missile_he` produced two 15.0s before the check moved last).
   The field's own profiles DO plateau — the canonical `HE` warhead sits at 100
   across the entire infantry ladder — and **Cameo does not copy that**; we take
   the field's plateau as "these are all near the top" and still separate them.
3. **But it need NOT be linear.** Equal steps were an artifact of the generator,
   and an even ramp is exactly the "moderate middle" the warhead rebuild exists
   to escape. Measured across 16 reference mods, real profiles use **plateaus
   and cliffs** — the canonical HE warhead sits at ~100 across the whole
   infantry ladder and then falls off to 35 at Heavy and 15 at Superheavy.
   Uneven steps are how a weapon says where it actually bites.
4. **THE WINDOW: every Versus value sits in `[10, 200]`** (maintainer,
   2026-08-15). Nothing outside, ever — including the DERIVED armors, which are
   products and can otherwise land arbitrarily low. That is a **20:1** maximum
   span, and it is the SAME extreme this law always allowed: peak 100 against a
   floor of 5 is also 20:1. Moving normalisation from the peak to the median
   (rule 1) left the scale open-ended; the window closes it.
   **The floor band is 10–25** for the value a family actually uses. 25 is a
   generalist; **10 marks a deliberately hyper-specialised weapon** — `CannonAP`
   against unarmoured infantry is the archetype. It is the exception, not the
   pattern; if several families want a 10, they are not all special.

5. **MAXIMUM LEGAL SPREAD ≠ TARGET SPREAD** (maintainer, 2026-08-15). The window
   above says what MAY ship. This says what ships by default, and the two must
   never be confused — 20:1 as a target would invent counter-play no source mod
   expresses.

   **The target band is `2x · 4x · 8x`** — flattest, centre, sharpest. That is
   the field's own distribution snapped to a doubling ladder, measured over
   **2402 individual reference warheads** with a real damage profile:

   | | measured | adopted |
   |---|--:|--:|
   | flattest (p25) | 1.9x | **2x** |
   | centre (median) | 4.0x | **4x** |
   | sharpest (p75) | 7.5x | **8x** |
   | p90 · legal max | 15x · 20x is p94 | — |

   The ladder continues 2 · 4 · 8 · 16, and the legal maximum of 20:1 sits just
   past 16 — the window is *one doubling beyond the sharpest default*.

   **Anything automatic stays inside `2x–8x`. Going outside is a design decision
   and belongs to the maintainer**, recorded in
   `aggregate_archetype.SPECIALIST_RATIOS`, never to a default.

   ⚠ **Measure the band on INDIVIDUAL warheads, not on aggregated families.** The
   per-family aggregate spans only 1.3x–7.2x, because averaging across mods that
   disagree about a family's direction CANCELS the disagreement. That aggregate is
   an artifact of averaging, not a design any mod shipped, and targeting it would
   chase a sharpness no real warhead has.

   ⚠ The band is waived for the **derived** armors (§12.0b) and only for them:
   they are products, the source profiles contain no derived armor so the field
   has no opinion to respect, and clamping the product would break the rule that
   produces it. The `[10, 200]` window still binds on every cell.

⚠ The ordering law (§ARMOR_SYSTEM "PROFILE construction") still decides WHICH
armor gets which value. The corpus supplies magnitudes, the law supplies order.

### 12.0a PLATFORM, NOT JUST FAMILY (maintainer, 2026-08-15) — binding

*"There is a huge difference between the obelisk of light laser (a very big
laser) and the small laser from the laser turret and infantry laser weapons …
light lasers are good against light and heavy lasers are good against heavy."*

**A reference profile is only comparable to a Cameo family if the unit firing it
plays the same role.** This is why Cameo splits `HE` into `CannonHE` /
`MissileHE` / `BulletHE` instead of keeping one `HE`, and the same split must be
applied to the reference data BEFORE anything is averaged.

**Measured** (`tools/reference/survey_platforms.py`, INI sources, warheads traced
from the firing actor and normalised to peak 100 — medians):

| family | platform | vs INF | vs LIGHT | vs HEAVY | majority direction |
|---|---|--:|--:|--:|---|
| laser | infantry | 100 | 48 | **33** | anti-LIGHT 55 / 96 |
| laser | defense_small | 100 | 50 | **50** | flat 21 / 33 |
| laser | **defense_big** (Obelisk) | 100 | 67 | **55** | flat 21 / 36 |
| laser | vehicle_heavy | 100 | 80 | **67** | anti-LIGHT 40 / 74 |
| tesla | **defense_big** (Coil) | 50 | 42 | 50 | **anti-HEAVY 27 / 30** |
| tesla | vehicle_light | 100 | 100 | 80 | anti-LIGHT 9 / 14 |
| cannon | infantry | 100 | 40 | 20 | anti-LIGHT / flat |
| cannon | vehicle_heavy | 100 | 75 | **87** | the only cannon tier trending anti-HEAVY |
| missile | infantry | 20 | 83 | **100** | the AT-infantry profile |
| bullet | every platform | 100 | 23–55 | 13–25 | anti-LIGHT everywhere |

**The hypothesis holds.** Laser lethality against heavy armour climbs with the
platform — infantry 33 → small turret 50 → Obelisk 55 → heavy vehicle 67 — so a
family's LEVEL (Light/Medium/Heavy) should track the platform tier, and the
levels must NOT share one profile shape. It also means `^Warhead_Laser_*` cannot
be filled from an average over "everything called laser": that mixes a rifle with
an Obelisk and produces precisely the mush the rebuild exists to remove.

Corollary already banked: **Tesla's big-defence profile is anti-HEAVY in 27 of 30
measured rows**, which independently validates Cameo's current Tesla direction.

### 12.0b HEROIC ARMOR IS A BRIDGE, NOT THE TOP RUNG (maintainer, 2026-08-15)

**Heroic is NOT the heavy end of the infantry ladder.** Placing it there
backfires: an elite unit would take the MOST damage from every anti-armour
weapon, which is the opposite of what "heroic" should feel like. The infantry
ladder is therefore `None < Flak < Plate`, and **Heroic sits BETWEEN Plate and
Scout** — a hybrid of infantry and vehicle, of light and heavy.

**Its value is the PRODUCT of the weapon's Plate and Scout values**, as
fractions of the profile's own PEAK: `Heroic = Plate × Scout / peak`.

⚠ **The divisor is the peak, not the constant 100** — they stopped being the
same thing when rule 1 above moved normalisation from the peak to the median and
values over 100 became legal. Dividing by 100 while a parent sits at 137
AMPLIFIES instead of collapsing: `^Warhead_Bullet_Light` produced `Plate 137 ·
Scout 106 · **Heroic 145**`, i.e. heroes taking MORE than either half — the exact
inversion this section exists to prevent. It hit **36 of 60** derived cells
before it was caught. Against the peak the product can never exceed either
parent, and whenever a profile does peak at 100 the formula is unchanged.

**The pattern generalises — a derived armor replaces every dual-`Armor` stack.**
`^FlyingInfantryTemplate` carries TWO `Armor` traits today (`Scout` + `Fighter`)
for exactly the reason Heroic wanted two: a jetpack trooper is both infantry and
aircraft, and multiplying the pair meant only a weapon good at BOTH threatened
it. W20's switch to averaging silently deleted that. So:

| derived armor | = parent × parent / 100 | replaces |
|---|---|---|
| **Heroic** | `Plate × Scout` | the elite-infantry stack |
| **Airborne** *(name provisional)* | `Helicopter × Scout` | `^FlyingInfantryTemplate`'s Scout+Fighter |

This is how W20 ("two `Armor` traits must never multiply at runtime") and the
hybrid-armor design stop being in conflict: **one trait per actor, the product
baked into the armor type at generation time.**
⚠ Follow-up: collapse `^FlyingInfantryTemplate`'s two `Armor` traits to the
single derived type — only after the warhead families carry the new column.

That reproduces exactly what the old multiplied-armor stack gave, and averaging
cannot:

| weapon | Plate | Scout | average | **product** |
|---|--:|--:|--:|--:|
| anti-infantry specialist | 100 | 30 | 65 | **30** |
| anti-vehicle specialist | 20 | 90 | 55 | **18** |
| good against both | 80 | 80 | 80 | **64** |

The average says a specialist is nearly as good against a hero as a generalist.
The product says what is intended: **specialists fall off a cliff against
heroes; only a weapon strong against BOTH infantry and vehicles stays strong.**

⚠ This does **not** reintroduce the W20 squaring bug. W20 was two `Armor`
*traits* multiplying at runtime on one actor, which nobody designed. This is a
single armor type whose numbers are computed once, at generation time, from a
formula the designer chose. Exactly one armor trait is still enabled per hit.

Implementation: `tools/reference/aggregate_archetype.py` (`HEROIC_FROM`,
`FLOOR_BAND`, `shape_profile`); it must be mirrored into
`gen_weapon_template.py` when the families are regenerated (W13 step 3).

**LAW (2026-07-18): balance numbers move ONLY through the balance
pipeline** — `docs/design/BALANCE_PIPELINE.md` (raw-stat JSON ledger in
`docs/balance/`, generated `cameo_balance_by_faction.xlsx` and
`cameo_balance_by_type.xlsx` workbenches, gated
`apply_balance.py`, `audit_balance_drift` enforcement in run_all).
Hand-editing a stat in yaml is a red audit finding. The subsections
below remain the FORMULA reference; the legacy workbook stays the
design-judgment reference until the Phase-3 triage
(`docs/balance/discrepancies.md`) completes.

_Historical design-judgment reference: **`docs/design/cameo_armor_system.xlsx`** (sheets:
Armor Types, Weapon Types, Infantry, Tanks, Vehicles, Aircraft,
Defenses; Tabelle2/3 are scratch). 333ggg's CABAL concept
(`Downloads\cabal.xlsx`) uses the same sheet layout. It is not the current
numeric source of truth and must not overwrite the ledger or the generated
faction/type workbenches. The formulas below document the historical design
reference. Research 2026-07-11; open questions marked ❓._

**The cost identity.** Every unit sheet computes three cost estimates
from the stats and averages them; the design workflow INVERTS this:

```
DPS  = Damage / ReloadDelay × WeaponClass                 (column J)
O    = (HP/100000 + Speed/100 + Range·K/5 + DPS/200) × 200 × L × M
P    = (HP·Speed/25000 + Range·K·DPS/2.5) × L × M
Q    = HP·Speed·Range·K·DPS·L·M / 12 500 000
Cost = (O + P + Q) / 3                                    (column R = S)
```

O is linear in each stat, P pairwise — by design intent the CHASSIS
(HP·Speed) plus the TURRET (Range·DPS) — Q the full product. Pure
linear made one-weak-stat units undercosted, pure product made the
same units overcosted, so the average of all three was chosen. This is
the FIRST iteration: it does not yet price anti-air capability,
projectile speed, or area of effect — those must be added in a future
revision (how is an open design question). **Workflow: the price S is
set FIRST** (last column); Range is then solved from the identity
(column F formula), so tuning HP/Speed/Damage/Reload auto-rebalances
Range to hold the price. Range and DPS cells are never hand-edited.

**Sheet-and-yaml dual write (LAW, design 2026-07-11).** Every balance
change lands in BOTH the workbook and the yaml in the same pass —
never in only one of them. Prices are outputs, never inputs: to
re-price a unit (e.g. after a tier move), edit the tier multiplier M
in the unit's row FIRST, let O/P/Q recompute, compare every stat
column against the yaml, then make the yaml match the sheet. Scaling
an existing yaml cost by a relative factor (old × new_M/old_M) is
FORBIDDEN — it bakes in whatever error the old value had (this
produced the Cannon Attack Robot 400-vs-350 miss). If the Excel lock
file `~$cameo_armor_system.xlsx` exists the workbook is open on
design's machine: queue the sheet edit, do not write the file.
Standing long-term goal: a fresh, clean workbook whose row names are
the exact in-game tooltips and whose stat cells are exactly the values
the formula consumes.

**Column semantics** (confirmed by design 2026-07-11):
- `WeaponClass` H — from the weapons yaml warhead classes. Every weapon
  family exists as **Light / Medium / Heavy** warheads: Light = 0.75,
  Medium = 1.0, Heavy = 1.25. Combining warheads AVERAGES the classes:
  Light+Medium = 0.875, Medium+Heavy = 1.125. **Prefer balanced class
  combinations**: 3×Light, or 2×Light + 2×Medium, or 1×Light + 1×Medium +
  1×Heavy. Avoid lopsided mixes such as 1×Heavy + 2×Medium. The final
  weapon class is the arithmetic mean of the individual class values.
- `Special` K — **+0.25 per special ability** (C4, EMP, stealth, point
  defense laser, …). Example: Nod laser commando = C4 + Stealth + PDL =
  1.75. Some over-strong kits are simply set to 2. FUTURE: replace the
  flat +0.25 with per-ability values that represent each ability's real
  power.
- `TechTier` M — cost discount for late tech: **Tier 3 = 0.75, Tier 4/5
  = 0.5** (rewards the tech-center investment). The rule was introduced
  late, so many rows are missing it — correcting those gaps is standing
  work; always cross-reference sheet vs in-game stats and ASK on any
  mismatch.
- **Burst rule**: sheet Damage = single-burst damage × bursts; sheet
  ReloadDelay = weapon ReloadDelay + (bursts − 1) × BurstDelay (the
  weapon only reloads after the full burst).
- `UnitClass` L — per-section class factor (infantry sections 0.4–1,
  vehicles 0.25–1.25, defenses 0.225/0.325/0.35). ❓ table of sections.
- **Epic units (design 2026-07-11): UnitClass L = 0.3, TechTier M = 1.0,
  regardless of actual tech tier.** Historically epic rows carried
  L = 0.4 × M = 0.75 (same product 0.3); the new convention folds the
  whole epic effect into L so that M stays a pure function of the tech
  tier everywhere (no "0.75 at T5" rows that look like mistakes).
  Relabeling legacy epic rows (Core, GDI Rig, Future Tank, …) is
  price-neutral — only the two cells change. Epics are never
  re-discounted when tiers move.
- **Defenses use Speed = 100 always** — immobility is priced through
  their LOW UnitClass factors instead, keeping the formula uniform.

**The nice-number law (design 2026-07-11).** Every stat moves in fixed
steps so the house formulas stay integral:
- **Prices: 10-credit steps** (was 25) — never 387-style numbers. If the
  target cost is not already occupied by another unit of the same class
  (same UnitClass/template role), prefer coarser **100-credit steps**. Use
  10-credit granularity only when the 100-grid slot is already taken by a
  sibling unit. If many units of the same class converge on the same price,
  equally spread them across the available 100-grid slots first, then fall
  back to 10-grid only when necessary. Prices are outputs, never inputs.
- **Damage: 10-steps** (Aedis, 2026-09-11). All main class warheads carry the **identical**
  (even-spread) value `total ÷ N` on the 10 grid — never unequal, never
  off-grid. (The grid was 2000 until 2026-08-12, then 100 until 2026-09-11; finer steps let the
  pipeline lands on the exact value instead of handing a remainder to
  `FirepowerMultiplier`, whose role as a fine-tuning knob is being retired.)
  Their twins are FIXED fractions of that main value:
  - **FriendlyFire** twins = always **50% damage** (and 50% spread).
  - **ExtraDamage** twins = always **50%** of the main (any warhead type —
    SpreadDamage or OpenToppedDamage; energy weapons trade area-of-effect
    for this shield/bonus chip) but are **EXCLUDED from the damage total**.
    ⚠ Being RETIRED: the 195 `SpreadDamage` chips collapse into the main
    warhead (the K model now prices what they compensated for), while the 34
    sniper `OpenToppedDamage` ones STAY — those are how a sniper hits
    passengers, not a damage bonus. See BALANCE_PROGRAM_PLAN W19.
  - **Folded percentage hit** = the normal family path. `AreaDamage` derives
    its second hit from the same authored `Damage` through `PercentageScale`
    and `PercentageDenominator: 10000`; it therefore scales to zero with the
    main hit and cannot drift as a separately authored twin. Percentage
    `Versus` values remain multiples of **5** in [5, 100]. Current direct-Actor
    impacts skip this folded second hit; the pipeline mirrors that shipped
    behavior until the separate runtime repair is reviewed and merged.
  - **Standalone percentage warheads** (`AreaDamagePercentage` and
    `HealthPercentageDamage`) are reserved for bespoke effects whose damage
    must remain independent of flat `Damage`. They are additive floors, not
    family twins, and their explicit denominator defines the unit.
  - The ONE code implementation is `formula.distribute_damage` /
    `formula.spread_damage_sum`; guard `audit_warhead_split`.
- **Only template-inherited warheads may exist.** Every `Warhead@X` on a
  weapon must be one the weapon inherits from a `^`-template in
  `weapons.yaml` (the main warhead is named after its template —
  `Warhead@SmallArms`, `Warhead@TankDestroyerCannon`, …). The legacy
  generic `Warhead@1Dam` is RETIRED — it was renamed to the per-template
  warhead name; a bare `1Dam` (or stray non-template warhead) is a bug.
#### The stat grids, complete (one table, one code home)

⭐ **`formula.STAT_GRID` is the single source of truth** — four files used to carry their own
quantum (`propose_class_rebalance.nudge_hp_spd` for HP and speed, `propose_reference_anchors`
inline for range and cost, `formula.DAMAGE_STEP` for damage, and nothing at all for reload and
burst). They all read the table now. **Never re-literalise a grid.**

| stat | grid | why that number |
|---|--:|---|
| HP | **1000** | the only grid NOT at 1, and not by omission: `RepairsUnits` steps at `HP/20`, so HP must stay a multiple of 20; 1000 keeps that free and still gives ~100 slots per class |
| Speed | **1** | was 5, only so `TurnSpeed = Speed/5` stayed integral; the derived-turn-rate trait handles that now |
| Range (WDist) | **1** | was 10; 1024 WDist per cell, so a step of 1 is ~1/1000 of a cell |
| Damage | **1** | was 2000 → 200 → 100 → 10 → 1 |
| ReloadDelay (ticks) | **1** | always was — integer ticks, never snapped by any tool |
| Burst | **1** | always was — a count |
| BurstDelays (ticks) | **1** | always was |
| Cost (credits) | **100** | with **10** permitted when the 100-slot is already taken |

**The ruling behind all of it, applied over and over: a coarse grid buys nothing once the
thing it protected is expressed differently, and it costs UNIQUENESS.** Speed stepped by 5 gave
13 slots for 51 `mbt` units — speed 75 shared by 9 of them, and no assignment of 51 units to 13
values can be unique. HP stepped by 2500 gave 24 distinct values for those 51 units, with HP
100,000 shared by 10. Damage stepped by 2000 so `FirepowerMultiplier` could absorb the
remainder — and `FirepowerMultiplier` is retired (W17), so there is nothing left to absorb.

Dates: damage 2000→200→100 on 2026-08-11 (W15); HP 2500→1000 and speed 5→1 on 2026-09-07;
damage 100→10 on 2026-09-11; **damage 10→1 and range 10→1 on 2026-09-12**, the same ruling that
put reload / burst / burst-delay on the record at 1.

⚠ **The percentage twin did NOT follow the flat grid down, and must not be inferred from it.**
100 flat is still 0.01% HP (`DAMAGE_PER_PERCENT`), so 1 damage is 0.0001% HP — finer than even
`FINE_PERCENT_DENOMINATOR` (100000ths) can write. `percentage_twin` returns its never-zero
floor of 1 there, so **Damage 1..99 all twin to the same 1 basis point**. The flat grid is now
finer than the percentage grid can follow; that is a known consequence, not a bug, and it is why
`percentage_twin` is threaded from the resolved node rather than assumed.

- **HP: 1000-steps for EVERY type** (maintainer 2026-09-07; was 2500 for
  vehicles/aircraft/ships and 1000 for infantry). The old 2500 existed only so
  `Step = HP/2500` divided evenly; once regeneration is expressed as TICKS TO FULL
  and accumulated fractionally, nothing constrains HP and the finer step is free.
  Repair stays `HP/20` (every 1000-step is a multiple of 20).
  ⭐ **Why it changed: the coarse steps made the uniqueness law impossible.** Measured
  2026-09-07, the `mbt` class has **51 members but only 24 distinct HP values** — HP
  100,000 is shared by **10 units**.
- **Speed: steps of 1 for EVERY type** (was 5 for vehicles/aircraft/ships). Steps of 5
  over a 60-120 range give **13 slots for 51 mbt units** — speed 75 is shared by 9 of
  them, and no assignment of 51 units to 13 values can satisfy uniqueness. The step of 5
  existed only to keep `TurnSpeed = Speed/5` an integer, which the derived-turn-rate
  trait now handles.
- **TurnSpeed (vehicles & fixed-weapon units):** units without a turret or
  with a forward-facing fixed weapon turn at **`TurnSpeed = 2 × Speed / 5`**;
  turreted units turn at **`TurnSpeed = Speed / 5`**. Infantry normally turns
  instantly, but CABAL cyborg infantry use the vehicle fixed-weapon rule
  because they carry forward-facing weapons.
- **TurnSpeed (aircraft):** helicopters and spaceships both use
  **`Speed / 5`**.
- ⛔ **A TURRET ALWAYS FOLLOWS ITS HULL** (maintainer 2026-09-07). `Turreted.TurnSpeed` equals
  `Mobile.TurnSpeed`; **every disagreement is a bug**, with no per-class exemption. Measured
  2026-09-07: 233 of 260 turreted vehicles already comply, and the 27 that do not are not a
  design — they are two accidental families plus two outright errors (`nodlasercorvette` turret
  1000 against a hull of 12; `td_gdi_defenserig` 128 against 12). The naval group sitting at
  0.4–0.7x and the light/IFV group at 2–3x are **not** ratified; they are drift that happened to
  be consistent. Guarded by `audit_turn_speed.py` T3.
- **Turn rate is GENERATED into yaml, never derived at runtime** — `audit_turn_speed.py` guards
  it. Turn speed is an integer `WAngle` at every layer and both runtime hooks
  (`ITurnSpeedModifier`, `ITurretTurnSpeedModifier`) take an integer PERCENTAGE, so the
  generator produces the authored values consumed by the engine. `Aircraft` exposes no hook
  at all, so its `Aircraft.TurnSpeed` must likewise be authored and ledger-covered.
### Regeneration — one global rule, no per-actor numbers

**Maintainer ruling 2026-09-07.** Regeneration is stated as **TICKS TO FULL**, never as a
per-step amount, and it is applied **every tick**:

| | ticks to full | seconds | ramp after damage |
|---|--:|--:|--:|
| infantry | **1250** | 50 | 125 ticks (5 s) |
| vehicles / aircraft / ships / defenses | **2500** | 100 | 125 ticks (5 s) |
| **shields** | **2x the HP rate** | half the HP time | **250 ticks (10 s)** |

* **Per tick, with a fractional accumulator.** At 0.04%/tick a 1,000 HP unit heals 0.4 HP per
  tick, which truncates to zero as an `int` — the remainder is carried, so the rate is exact at
  every HP value. This is what frees HP from any step constraint.
* **`ChangesHealth.PercentageStep` cannot express this** (it is an `int`, minimum 1% per step),
  so the rate lives in a Cameo trait. Only `Common` declares `ChangesHealth` — CA's is
  `ChangesHealthVersus`, a different name — so a Cameo type shadows it with no yaml churn.
* **The ramp replaces the hard cooldown.** Rate is `full x min(1, t / 125)` where `t` is ticks
  since the last damage: 0 at the moment of the hit, full at 5 s, linear between. Shields use
  250. The old `DamageCooldown` (10 vehicles / 20 infantry) is retired.
* **Always on while damaged** — `StartIfBelow: 100`, as `defaults.yaml` already sets.
* **ONE global inherit is the target state, not the current migration state.** The rate
  belongs to `^InfantryBuffs` / `^VehicleBuffs` / `^AircraftBuffs` / `^ShipBuffs` in
  `defaults.yaml`. The current tree still carries **836 authored
  `ChangesHealth@SelfHealing` nodes** (measured 2026-09-18); their conversion remains
  open in the roadmap. Do not delete those overrides until the conversion batch has
  landed and its playtest proves the global trait is active. The raw ledger now records
  the named Step and `Repairable.HpPerStep` so interim batches cannot lose them.

⚠ **What was already correct, and was nearly "fixed" by mistake.** `defaults.yaml` sets
`Delay: 1` for vehicles/aircraft/ships and `Delay: 2` for infantry. Reading only the ContentPack
templates — which set `Step` and no `Delay` — suggests the engine default of 5 and yields a
"500 s" self-heal that does not exist. Vehicles really do heal in **100 s** and the shipped
shield trait really is **exactly 2x** the HP rate. The one real gap was infantry, which
`Delay: 2` put at **80 s (1.25x)** rather than the intended 2x; that is what moves to 1250 ticks.

- ReloadDelay: any integer.
- **Beautiful ranges are kept**: if Range is exactly 6.000 or 7.500,
  adjust the other stats, not the range.
- **Preserve the unit's feel**: never double damage and reload together
  just to make the math easy.

**UnitClass L is bound to the defaults.yaml class template** — one value
per class, identical for every unit of that class:

| class (sheet section) | L |
|---|---|
| Scout Infantry 0.5 · Grenadier 0.4 · Mortar 0.6 · Anti-Tank/Anti-Air 0.5 | infantry |
| Heavy Infantry 0.8 · Melee 0.75 · Sniper 0.75 · Hero 1.0 | infantry |
| Main Battle Tank 1.0 · High Tech Tank 1.0 · Epic 0.4 | tanks |
| Scout Vehicle 0.333 · Advanced Scout 0.5 · Transport/Support 1.25 | vehicles |
| AA Support 1.0 · Fire Support 1.0 · Artillery 0.5 | vehicles |
| Helicopter 1.0 · Fighter 1.0 · Spaceship 1.0 | aircraft |
| Basic Defense 0.35 · AA Defense 0.225 · Advanced Defense 0.325 | defenses |

**Tier counting for the M discount**: the tier is set ONLY by TECH
building requirements — production buildings (barracks, war factory,
helipad, naval yard) and refineries NEVER count. No tech requirement =
Tier 1 (war-factory units without a radar requirement are still T1);
radar tech (or equivalent) = Tier 2; tech center = Tier 3; beyond =
Tier 4/5. Tech gates count TRANSITIVELY through the production chain:
the helipad/airfield itself requires radar, so **ALL aircraft are at
least Tier 2**. M: T1/T2 = 1.0, T3 = 0.75, T4/5 = 0.5. Auto-correcting the
missing discounts across the sheets is approved — under the nice-number
law above.

**Early-vs-late philosophy**: upgrades boost cheap early-game units
proportionally MORE than late units; late units are compensated through
the tech-tier discount instead. Tier 2 is the stopgap tier — units too
strong for T1 but not strong enough for T3.

**Tier placement themes** (initial; deep research ongoing): artillery
is ALWAYS at least Tier 2 (some Tier 3, e.g. the GDI Archer); fire
supports and line breakers usually Tier 2; flamethrower infantry
Tier 2 (exception: Japan); heavy infantry and snipers usually Tier 2.

**Repair/engineering units (design 2026-07-11):** the repair beam is
its own weapon class — **H = 1.5** — and engineering kits (capture +
repair + defuse) are the maxed special **K = 2**. Reference trio in the
workbook: IFV (Engineer), Engineering Armor, Engineering Truck (all
20000 @ 50, H 1.5, K 2, L 0.5); the CABAL repair engineer added its own
unique row (16000 @ eff. 40, HP 20000, Cost 800). H above 1.5 exists
once by design: the **TOPOL-M (H = 5) is a mobile superweapon**. The
"Consortium Artillery Tank" workbook row is the HAMMERHEAD (stale name)
— one of the sacred meme units.

**Promotion units carry a hidden yaml-side buff** the spreadsheet does
NOT model: every promotion-gated unit inherits `^PromotionUnitBuff`
(defaults.yaml) — +10% firepower, −10% damage taken, −10% reload, +5%
speed/range/vision/cloak detection, −10% inaccuracy. The sheet always
holds the unbuffed base stats; the buff is the promotions' flat bonus
on top, applied only through the yaml inner workings.

**Special ability catalog (K = 1 + 0.25 per special; overpowered kits
set straight to 2 until per-ability values exist):**
- COUNTS: cloak; auras (propaganda effect); vampire heal-on-attack
  (the Dissolver's `ChangesHealth` on `GrantConditionOnAttack`).
- DOES NOT COUNT: cloak detection (near-ubiquitous); deploy/transform;
  anti-air capability — AA belongs in a future formula term, not in K.
- **Charge-delay drawback −0.25 — DEFENSES ONLY** (design 2026-07-11):
  a defense that must charge before firing (others shoot instantly) may
  carry K below 1 (TD Obelisk of Light K=0.75, CABAL Obelisk Prime
  K=0.75). Mobile units with charge delays do NOT get the discount.
  The discount applies only to LONG charge-ups (Obelisk-class); brief
  charges (Tesla Coil, Prism, Waveforce) are not significant enough.
  The Tesla Coil's K=1.25 is its inherent EMP effect counting as the
  special (+0.25), undiscounted by its short charge.

**The baseline unit (design 2026-07-11): the Naxis Tiger Tank** —
100 000 HP, 100 Speed, 10 000 damage, range 5.0 (= 5000 wdist,
written literally as `Range: 5000` in the weapons yaml — Cameo uses
plain wdist integers, never OpenRA's `4c904` c-notation; the sheet's
Range unit is wdist/1000, NOT cells since a cell is 1024),
50 reload, all modifiers 1 → DPS 200 and **O = P = Q = Cost = 800
exactly**. Every stat trade in the system is anchored on these round
numbers.

**Known limitation — the low end breaks (second iteration planned).**
The formula has no intercept: cost → 0 forces every stat toward 0
simultaneously, so very cheap units (Minigunner at 100, Naxi Rifle
Recruit at 50) come out unusably weak — a unit's fixed "cost of
existing" (pathing, pop slot, minimum viable rifle) is not priced.
Stopgap in game: strong damage-reduction multipliers on the scout
infantry template. Design direction instead: **one baseline unit per
unit class** (scout/basic/heavy/hero infantry, each with Tiger-style
round numbers), and price by normalized deviation from the class
anchor: `Cost = Cost₀ × (O/O₀ + P/P₀ + Q/Q₀) / 3`. At each anchor the
identity is exact (like the Tiger's 800); below it, stats degrade far
more gently than the global formula, which fixes the low end. The
UnitClass column is then absorbed into the class baselines.

**Armor & versus system (hypothesis to verify in yaml).** 20 armor
classes in 4 categories (Infantry: None/Flak/Plate/Hero; Vehicles:
Scout/Light/Medium/Heavy/Superheavy; Aircraft: Fighter/Bomber/
Helicopter/Spaceship; Buildings: Wood/Concrete/Steel) with a base
ladder in ~4% steps (None 100 … Wood 56 … Spaceship 4?) and two armor
ORDERINGS. Weapon Types carry: effectiveness ranks 1–4 vs
Infantry/Vehicle/Aircraft/Building, a weapon band (light/medium/heavy),
and SCALING tables — six bands (SmallArms/Light/Medium/Heavy/
Superheavy/Superweapon) with per-rank percentage columns starting at
100 and stepping by 6/5/4/3/2/1 per rank, plus a low table starting at
15–40. The scaling tables are the DESIGN REFERENCE that generated the
in-yaml Versus tables; in the game they are realized once inside the
weapon class templates and never re-derived per weapon.

**Weapon construction law (design 2026-07-11, updated 2026-08-02).** The
Versus tables live ONLY in the class templates of the central
`weapons/weapons.yaml`. The original ~30 full-stack templates
(`^SmallArms ^Chaingun ^FlakWeapon ^MediumCannon ^HeavyMissile
^LaserWeapon ^LightChemicalWeapon …`) are being supplemented by 55 new
warhead-only families (`^Bullet_Light`, `^Bullet_Medium`, `^CannonAP_Light`,
…) plus 24 projectile templates (`^ProjectileBullet_Light`, …) and 27
effect templates (`^EffectBullet_Light`, …), for a total of ~85+ templates.
New dedicated artillery families `^Projectile_ArtilleryShell_Medium` and
`^Projectile_ArtilleryRocket_Medium` live in `weapons/weapons.yaml`; the
latter replaces an earlier copy in `ContentPacks/RedAlert2/Shared`.
All templates are **never modified without an explicit design order**.

**Old 2-inherit model (still valid for unretrofitted weapons):**

```
MyWeapon:
	Inherits: ^MediumCannon          # contributes its class warhead (versus)
	Inherits@2: ^HeavyCannon         # LAST inherit WINS for the shared fields:
	                                 # projectile, sounds, effects, defaults
	                                 # all come from ^HeavyCannon here; the
	                                 # warheads of BOTH accumulate
	ReloadDelay: 50                  # own overrides beat every template
	Range: 5000
	Warhead@MediumCannon: SpreadDamage
		Damage: 8000
	Warhead@HeavyCannon: SpreadDamage
		Damage: 8000                  # EVEN SPREAD — always identical values
```

Order the inherits so the template whose projectile/sound/feel you want
comes LAST; the earlier inherits only contribute their warheads.

**New 3-layer model (retrofitted weapons, 2026-08-02):** Weapons are
repointed to a 4-inherit model using the new warhead-only families plus
projectile and effect templates:

```
MyWeapon:
	Inherits@wh: ^Bullet_Light          # warhead layer (Versus + damage)
	Inherits@proj: ^ProjectileBullet_Light  # projectile layer (speed/homing)
	Inherits@fx: ^EffectBullet_Light     # effect layer (impact/muzzle/trail/sound)
	ReloadDelay: 50                       # own overrides beat every template
	Range: 5000
	Warhead@Bullet_Light: SpreadDamage
		Damage: 8000
```

Each layer is independently composable: a fast projectile can carry a
heavy warhead, a unique effect can be paired with any warhead family.
The warhead key is named after the warhead template
(`Warhead@Bullet_Light`, `Warhead@Bullet_Medium`, …). See
`docs/design/ROADMAP.md` §4 and `docs/design/WEAPON_3WAY_SPLIT.md` for
the full migration plan and progress.

- **Mixed class warheads always carry the SAME Damage** (even spread;
  1,023 weapons comply, 49 violations flagged — mostly the imported
  chem-upgrade weapons like TSChemBazooka 6000/24000; fix on order).
- Template auxiliaries (`LaserExtraDamage` 600, `RailgunExtraDamage`,
  `ShrapnelWeapon`, Tesla charged twins) ride along at fixed values and
  are NOT part of the even-spread accounting or the sheet Damage.
- ❓ FriendlyFire twins: some templates default them EQUAL to the main
  damage (^MediumChemicalWeapon 1000/1000), some HALF (^LightFlameWeapon
  2000/1000); the override convention needs a design ruling.
- **MEME UNITS ARE SACRED (design 2026-07-11).** `NanoArtilleryAG` /
  `NanoSmokeAG` (everything 7s and 3s) and `HammerheadArtillery`
  (everything 1s) are deliberate joke stat lines and are NEVER touched
  by any formula, rule sweep or rebalance — no matter how the balance
  formula changes. Audits list them as exempt, never as findings.
- **Multi-weapon units**: the sheet Damage is the SUM over the baseline
  loadout — every `primary` armament not gated behind an upgrade (GDI
  Battle Tank: cannon 8000 + missiles 8000 = sheet 16000).

**Plasma weapons (design 2026-07-13).** A CABAL "plasma" weapon is a
signature triad: a base weapon class plus a **Fire** warhead and a
**Chemical** warhead. The base class determines the projectile look and
report; the flame and chemical warheads add the plasma burn/corrosion
signature. Examples:
- **Plasma cannon** = Cannon + Fire + Chemical.
- **Plasma rocket** = Missile + Fire + Chemical.
- **Plasma laser** = Laser + Fire + Chemical.
All class warheads follow the even-spread law (same damage) and carry
matching percentage twins. The impact effect and sound are authored or
assigned together and kept unique to the weapon.

**Definition of Done for a formula unit:** stats from the sheet map to
yaml as HP→`Health.HP`, Speed→`Mobile.Speed`, Range (wdist/1000)→weapon
`Range` (×1000, written as a plain integer like `5000`), Damage→class
warheads per the even-spread law, ReloadDelay→weapon `ReloadDelay`
(ticks, burst rule applied); every new unit gets its own unique weapon
(§10) inheriting the sealed class templates. **On any sheet↔game
mismatch the balance sheet wins**; audit_balance_sheet.py is the
detector and fixes land as ordered batches, never silently.

### 12.0c THE SHIELD LADDER (maintainer 2026-08-16) — binding

**Continuous migration ruling (Aedis, 2026-09-10 02:10):** uniqueness applies
between the new family bases. Old Light/Medium/Heavy templates remain temporary
compatibility definitions; their duplicate Shield values must remain visible in raw
audits. The first CannonAP base reuses its existing finalized Medium Shield (144),
as proposed and approved, without re-ranking legacy templates. This is a staged
coexistence policy, not evidence that a one-family pilot spans the full legacy band.
Shield remains outside the heaviness bell. The level-based specification below
continues to describe the retained legacy generator, not a requirement to invent a
new Shield value solely to avoid an approved compatibility duplicate.

> *"the only thing that should deal extreme amount of damage to shields is tesla"*

```
Shield = PHYSICS_RANK[family] x SHIELD_LEVEL[level] x damped structural scale
```
compressed onto **exactly [100, 400] = 4.000x**, every value DISTINCT, ascending within
each family, with **Tesla the top family at every level** (312/338/369/400).

⚠ **No structural formula can carry this identity** and that is measured, not assumed:
`floor` and `top` are ANTI-CORRELATED by normalisation, so any product of them cancels to
an invariant of the normalisation rather than a property of the weapon (`200+floor` spans
1.26x, the geometric mean 1.54x, both with >50% ties). The structural term therefore sets
the BAND and `PHYSICS_RANK` sets the ORDER — and the term is DAMPED so it can only
separate families of EQUAL rank, never reorder unequal ones.

⚠ **The compression is DERIVED every run** (`shield_uniqueness.compress`), not calibrated.
Three hand-set constants were correct for exactly one profile set and went silently wrong
the moment §12.0h renormalised everything.

### 12.0d THE CLASS TILT (maintainer 2026-08-16) — binding

Within a family, each LEVEL tilts toward one end of every armor ladder:

| level | tilts toward | |
|---|---|---|
| Light (and Trace) | `None` `Wood` `Scout` `Light` `Fighter` | the lightest rung of each ladder |
| Medium | `Flak` `Steel` `Medium` `Bomber` `Helicopter` | the middle rung |
| Heavy | `Plate` `Concrete` `Heavy` `Superheavy` `Spaceship` | the heaviest rung |
| **Super** | nothing — **FLAT**, the generalist | actively compressed to the band's flat end |

Implemented as ladder POSITION, not as a literal armor set, because position is what those
sets ARE. ⚠ **The tilt MUST NEVER reorder a ladder**: it is applied to the VALUES and each
armor is then given back the RANK it held, so where the tilt agrees with the family's
direction it sharpens, where it disagrees it flattens, and it can never invert
`None > Flak > Plate`. That also removes any need for a `direction` argument, which is what
makes it work for the blends.

⭐ **This is the DISCRETE form, and it is what `gen_weapon_template.class_tilt` ships today.**
Its continuous successor is **§12.0i**, which replaces the three armor sets above with one global
armor axis and the four levels with a continuous `h`. Two things to carry across when reading this
section: the tilt's span here is `TILT_RATIO = 1.5`, which is why §12.0i's `LO` was re-ruled to
0.667 (= 1/1.5) rather than 0.80; and the three sets above are the LIGHTEST / MIDDLE / HEAVIEST
rung of each ladder, which on §12.0i's axis is `h = 0 / 1 / 2` — every ladder is centred on 1.000
precisely so that mapping is exact.

### 12.0e THE ARMOR-PLATING LAYER (maintainer 2026-08-16/17) — binding

Five overlay armors, granted by upgrades, **ALWAYS ALL CAPS** so the case alone distinguishes
them from the TitleCase class armors:

| plating | counters | weak to | real basis |
|---|---|---|---|
| `HAZMAT` | thermochemical | kinetic | sealed/filtered envelope; no mass, so a bullet ignores it |
| `COMPOSITE` | kinetic **+ shaped** | blast | ceramic shatters a penetrator, ERA breaks a jet; neither spreads an impulse |
| `BLAST` | blast | energy | spall liner absorbs impulse; a beam delivers none |
| `REFLECTOR` | energy | thermochemical | mirror-bright coating; flame and corrosives foul it |
| `ARMOR` | nothing | nothing | the GENERIC hedge — flat, for scrap/junk and non-branching upgrades |

Laws:

1. **LAYER SELECTION, not combination.** A plating REPLACES the class armor while active
   (`AreaDamageWarhead.DamageVersus`), exactly as `Shield` already does in yaml
   (`Armor: RequiresCondition: !shielded`). This is what makes "weak against" safe: only one
   row is ever read, so a weak row is a chosen exposure rather than a penalty stacked on top.
2. **EVERY template carries EVERY plating row, with no exceptions** — Sonic and Magic
   included. A MISSING row is not "no opinion": both the engine and Cameo's override select
   on `Versus.ContainsKey`, and an EMPTY match list returns **100**, so a gap makes the
   weapon hit PLATED units harder than unplated ones.
3. **THE COLUMN LAW.** Every plating's mean across all templates is the same (**70**), so no
   plating is stronger overall — they differ only in WHAT they resist. This is the TRANSPOSE
   of §12.0h and cannot conflict with it: platings sit outside the class-armor set.
   ⚠ 70 rather than 100 because a plating displaces the class armor, and six class armors
   already average better than 100 (`Heroic` 74.3, the four aircraft 76–80) — at 100 a hero
   or an aircraft got 25–35% WORSE for taking an upgrade.
4. **AN ARMOR UPGRADE MUST NEVER INCREASE INCOMING DAMAGE.** Guard:
   `audit_armor_upgrade_harm.py`. Nothing else can see this class of bug — the yaml is valid,
   every value is in the window, and a boot gate cannot catch a number that is merely wrong.
5. **PLATINGS ARE MUTUALLY EXCLUSIVE; TEAM UPGRADES ARE NOT.** A plating changes the TYPE
   and must share one `ProductionIconMutualExclusion` group with its siblings; a team/tech
   upgrade changes the AMOUNT (`DamageMultiplier`) and must NOT grant a type — giving one to
   a stacking tech would erase the unit's class identity as a side effect. Guard:
   `audit_plating_exclusivity.py`. Carrying two plating TRAITS is normal and correct; both
   CONDITIONS being true is not.

### 12.0f PRICED SURVIVABILITY (E1, 2026-08-16; SHIPPED 2026-08-17)

```
effective_HP = HP + shield_pool x (100 / mean Versus-vs-Shield)      # x0.555 measured
```
The factor is MEASURED from the live ruleset, never frozen — the Shield ladder is generated
and has moved repeatedly. ⚠ **`Integrity` is NOT a shield and is NOT counted**: it absorbs
nothing (`INotifyDamage` runs after the damage lands), so it buys no survivability at all
and only gates the EMP disable. Platings contribute 0 net by construction (law 3).

**LAW — only a shield the unit SPAWNS with is priced.** The maintainer's qualifier *"that's
only if the unit already has armor or shield included in them"* is binding, and it decides
three buckets:

| the unit has | count | priced into base cost |
|---|--:|---|
| a pool present at spawn, no positive gate | **58** | **YES** — `effective_HP` |
| `MaxPercentageStrength` but `InitialStrength: 0` behind `shieldgen` | 1318 | no — it is an empty CAPACITY, not a shield |
| a pool granted by an upgrade (incl. every plating) | ~216 | no — that is upgrade pricing (E5) |

⚠ **`!disabled` is NOT a gate.** It is the standard not-EMP'd/not-captured guard and is true
on a healthy unit. Any classifier that treats every `RequiresCondition` as a gate will hide
all 43 Protoss shields (`InitialPercentageStrength: 100`, `RequiresCondition: !disabled`) and
report a shield-free roster. Only a POSITIVE token gates.

**The weapon side gets its own weight, not a rung.** `armor_weights()` carries a 17th `Shield`
row at the measured baseline damage share (**1.432%**), taken OUT of the 16 class rows so the
weights still sum to 1.0; `weighted_versus` iterates the weights, never `ARMORS`. Effect:
+0.65% (Bullet) to +3.47% (Tesla). `effective_density` deliberately stays on `ARMORS` — it
counts BODIES, and a shield sits on a body the class row already counted.

⚠ **The Protoss 150% damage multiplier compensates for their shields.** Pricing the shield and
retiring that multiplier must land in ONE pass, or the faction pays twice.

Report: `tools/audit/audit_survivability_pricing.py` (informational — these actors are
mis-priced until `apply_balance --confirm` runs, so it must not gate commits).

### 12.0g DEPLOYING ADDS A SECOND ARMOUR (maintainer 2026-08-22) — binding

> *"We don't want damage multipliers anymore because they are bad for exactly the reason
> described. Instead deploying should change the armor type … it should turn into the Steel
> armor type because that's what defenses use … But the problem with this is: it still needs
> the underlying armor intact. So give it the secondary armor type steel and keep the primary
> armor type, then use that multi armor scaling."*

A unit that deploys becomes a static defence, and **Steel is what defences wear**. So deploying
grants `Armor@deployed: Steel` **in addition to** the class armour — never instead of it, and
never as a `DamageMultiplier`.

```
Armor:                                  # class armour — NO deploy gate
    Type: Heavy
    RequiresCondition: !shielded
Armor@deployed:
    Type: Steel
    RequiresCondition: !shielded && deployed
```

Both traits are enabled together, and `AreaDamageWarhead.MultiArmorCombination` (default
`Average`) makes the two rows meet in the middle. This is the same mechanism as the CABAL
cyborg dual-armour rule, and it is why the class armour must NOT be gated on `undeployed`:
that makes Steel a REPLACEMENT and throws the unit's own class away.

**Why not a `DamageMultiplier`.** R1 abolishes them generally, and the tick tank is the worked
example of the harm: `Modifier: 50` on `deployed` was the strongest deploy bonus in the tree,
it MULTIPLIED with the whole veterancy ladder (deployed + rank-elite = ×0.30, a realistic stack
reached ~613,000 effective HP on an 800-credit tank), and `extract_stats` could not see it at
all — it only reads a `DamageMultiplier` gated on the SHIELD-up condition, so the survivability
was free.

**Measured effect** — average(class, Steel) / class, over all 137 generated profiles:

| class armour | median | toughest | softest |
|---|--:|--:|--:|
| None | 0.95× | 0.60× | 1.95× |
| Light | 0.94× | 0.69× | 1.58× |
| Medium | 0.98× | 0.67× | 1.70× |
| Heavy | 1.00× | 0.66× | 1.92× |
| Superheavy | 1.01× | 0.64× | 2.12× |

Near-neutral in the median, so it is a RESHAPE and not a buff: anti-armour fire gets weaker
against a deployed unit, siege and fire get stronger. Deploy to hold a line against tanks; do
not deploy under artillery.

⚠ **Scope is the units that FIRE from a deployed mode — 20 of the 74 that carry
`GrantConditionOnDeploy`.** The rest detonate (the ~20 civilian car bombs), transform, or
burrow; "becomes a static defence" is not true of them and Steel would be meaningless.

⚠ **Air units are excluded.** Averaging Steel into `Fighter` (1.23× median) or `Helicopter`
(1.21×) makes them SOFTER overall, and a ground-defence armour on an aircraft is incoherent
anyway. Neither air deployer fires from its deployed mode, so the exclusion costs nothing.

⚠ **Only warheads routing through `AreaDamage` average — 62.9% of the tree.** The remaining
37.1% still declare inline `Versus` on `SpreadDamage`/`TargetDamage` and MULTIPLY, and under
multiplication the class row cancels out entirely (the ratio collapses to `Steel/100`), so the
"meet in the middle" does not happen for them. Those weapons see a flatter effect than designed
until item A5 retires them onto `^Warhead_*` templates. This is a reason to finish A5, not a
reason to avoid the rule.

### 12.0h THE MEAN-100 LAW (maintainer, 2026-08-16) — binding, supersedes median-100

> *"all warheads average all versus values at 100 to make them comparable"*

Every `^Warhead_*` family's MAIN warhead has its 16 armor rows normalised so their
**arithmetic MEAN is 100** (`gen_weapon_template.mean_normalise`). W13's median-100 left
the mean free, and the mean is not a shape statistic but a MAGNITUDE: `K` is a
share-weighted average of the profile, so the mean IS the family's contribution to priced
DPS. Measured before the change, family means ran 22.0 to 106.1 — up to a 4.8x hidden
multiplier between two families that both looked "normalised".

Consequences, all binding:

* **`K` is SHAPE-ONLY.** Choosing a family redistributes output across armors without
  changing how much there is. `Damage` is the sole magnitude knob.
* **`max <= 200` now MEANS `max <= 2 x mean`.** A profile brilliant against three armors
  and useless against thirteen cannot keep its peak. 11 of 94 templates breached and are
  compressed by the POWER LAW about the geometric mean — never a clamp, because the power
  law is the only transform that also preserves `Heroic = Plate x Scout / peak` exactly.
* **A tilt is FREE.** Moving output between armors costs nothing in total, which is what
  makes §12.0d expressible at all.
* **Scope: MAIN warheads only.** A `_Percentage` twin's `Versus` is a MAGNITUDE until W18
  rebases it; normalising it would multiply every %-effect by ~5x.

## 13. Map props (Obstacle target type)

- Trees, rocks, utility poles and other decorations carry
  `TargetTypes: Ground, Obstacle` (templates `^Tree ^TreeHusk ^Rock ^Box`).
- `Obstacle` exists for AI logic (minelayer bot ignores it), **never for
  weapons**: no weapon lists Obstacle in Valid/InvalidTargets — props are
  hit as plain Ground.

## 14. Map actor naming (compatibility with renamed actors)

- **Maps must use the current renamed actor ids, not the original
  compressed names** (design 2026-07-15). When a map is added or updated,
  every `ActorNN: <type>` line in `map.yaml` and every actor-type string
  in lua scripts must use the new §1-compliant actor id (e.g.
  `td_nod_minigunner`, not `e1.nod`). The old compressed names no longer
  exist as actor definitions and will crash the game on map load.
- **Rename maps are the source of truth.** The mapping from old → new
  actor ids lives in `tools/rename/rename_map_<faction>.yaml` files.
  When renaming actors in a map, look up each old name in these files to
  find the new id. Actors that already exist with their old name (terrain
  decorations like `t01`, `v01`, `boxes01`, `brik`, `fenc`, `gmine`,
  `tanktrap1`, `split2`, `silo`, `nuk2`, `nuke`, `sbag`, `fcom`, etc.)
  are NOT renamed and stay as-is.
- **Lua scripts must also be updated.** Actor-type strings in lua
  (reinforcement lists, `Actor.Create` calls, `GetActorsByType` checks,
  `Reinforcements.ReinforceWithTransport` unit lists) must use the new
  ids. A map's `campaign.lua` may reference actor types in utility
  functions (e.g. `GetAirstrikeTarget` checking for `"sam"`) — these must
  also be renamed.
- **Tooling.** `tools/rename_map_actors.py` applies the rename maps to
  map.yaml and lua files in bulk. It matches `ActorNN: <type>` lines in
  yaml and quoted `"oldname"` strings in lua, replacing them with the
  new ids from the rename maps.

---

## 15. CABAL faction design rules

The full CABAL faction design lives in a local document
(`CABAL_FACTION_DESIGN.md` in the external DevinCameoProject folder).
This section binds the rules that affect YAML-level auditing.

**Faction identity.** CABAL is a self-contained cybernetic collective: every
unit is a machine, cyborg, or drone. No cross-faction inheritance. The
faction owns two ground production queues — the Cyborg Factory builds
infantry and light walkers, the Mech Factory builds heavier vehicles.

**No dead tiers.** Infantry, vehicles, and aircraft must each have a
meaningful, non-limited, buildable unit at every tier in the regular tech
tree. Promotions are *better* versions of those base units, not the only
option at a tier. A promotion tier maps directly to a tech tier (rank 1–4
= Tier 1–4) and chains from the previous promotion in its column.

**3×4 promotion grid.** CABAL uses three promotion columns: Infantry,
Vehicles, Aircraft. Each column has four tiers. The aircraft column is
filled by adding a Tier-1 flying drone (`cabal_wasp`) produced from the
Cyborg Factory and a Tier-4 command ship (`cabal_mothership`), because the
Helipad is gated behind Radar and cannot provide a T1 aircraft by itself.
The **CABAL Core** is the Tier 4 technology unlock; all T4 units (base
and promotion) and the Core Defender require it.

**Class-template mapping.** Every CABAL actor must map to a single
`defaults.yaml` class template. Known mismatches to fix are bugs, not
style: `cabal_dissolver` must be `^HeavyInfantryTemplate`, `cabal_artilleryspider`
must be `^ArtilleryTemplate`, `cabal_cyborgreaper` and `cabal_manticore` must be
`^SupportVehicleTemplate`, `cabal_coredefender` must be `^EpicVehicleTemplate`.

**Cyborg dual-armor rule.** All CABAL cyborg infantry use the Future Tech
droid recipe: the base `Armor` from the infantry class template stays active
and a secondary vehicle `Armor@<role>` is added, so cyborgs count as both
infantry and vehicles for weapon Versus tables. True vehicles and walkers do
not use this pattern.

⚠ **The two armors are AVERAGED, not multiplied** (W20/W21 R5, live since
2026-08-15): `AreaDamageWarhead.MultiArmorCombination` defaults to `Average`,
so `Plate` 88 with `Superheavy` 10 resolves to 49, not 8. **Never add a
`DamageMultiplier@<role>: Modifier: 200` to compensate** — that was the old
recipe, it fought the ENGINE's multiplication rather than the design, and all
7 instances were deleted when averaging landed. R1 abolishes `DamageMultiplier`
generally; toughness is a visible `ArmorPlating` bar, never an invisible knob.
⚠ Warheads still declaring inline `Versus` on `SpreadDamage` keep multiplying
until item A5 retires them onto `^Warhead_*` templates.

**Cybernetic Plating shield rule.** CABAL cyborg infantry do NOT have an
innate `Shielded` trait. Instead, the `cabal_upgrade_cyberneticplating`
research upgrade (Tier 3, Tech Center) grants every cyborg infantry unit a
yellow shield bar (`SelectionBarColor: FFFF88FF`). The shield is gated by the
upgrade condition, uses `ShieldsUpCondition: armored`, and recharges slowly
with a low flat `RegenAmount` equal to twice the unit's self-heal step. The
base `Armor` type never changes: the upgrade adds plating as a shield pool,
not as an armor-type swap. This mirrors the Tiberian Dawn Nod cybernetics
upgrade behavior and must not be reverted to unconditional shields.

**Upgrade tiers.** Tier 2 (Radar, `Upgrades` queue): Overcharged Servos,
Dark Armament, Radar Hack. Tier 3 (Tech Center, `Research`):
Mobility Matrix, Neutron Nuclear Catalyst, Cybernetic Plating, Reinforced Chassis, Neural Uplink,
Reclamation Protocols, Networked Combat Protocols. Tier 4 (Tech Center + Core,
`Research`): Backup Systems, Hand of CABAL, Data Worm, Firewall Protocol, and
Full Assimilation as the team upgrade. The strongest and team-wide upgrades
sit at Tier 4.

**Weapon identity.** CABAL plasma weapons are the signature triad from
§12: Cannon/Missile/Laser + Fire + Chemical warheads with even spread.
CABAL lasers are purple/dark-blue outer beams with a near-white cyan core,
scaled by damage. Weapon sounds follow the obelisk/laser sound map in §3.

**Promotion visibility rule.** Promotions must be globally visible in the
Promotions tab as soon as the player has the faction's construction yard
and `rank1`. A promotion's `Buildable.Prerequisites` must always start with
`~constructionyard` so the promotion grid is only available while the
player still has a base; it also contains `rank1`, the prerequisite that
unlocks the promotion (`!self`), and the previous promotion in its column.
Production buildings and tech structures (other than the construction
yard) must NEVER gate whether a promotion appears in the Promotions tab —
those buildings belong on the *unit* that the promotion unlocks.

**Promotion-unit prerequisite formula.** A unit unlocked by a promotion uses
`Buildable.Prerequisites: ~productionbuilding, techbuilding, ~promotion`.
`~productionbuilding` hides the unit when the producer is missing; the
`~promotion` token hides the unit entirely when the promotion has not been
bought; tech buildings are positive prerequisites that disable the unit but
still show it in the build list. Replaced base units additionally carry
`!promotion` so they are disabled once the promotion is bought. Every
promotion-gated unit must include its `~promotion` token, otherwise it will
appear before the promotion is unlocked.

**Weapon minimum-range rule.** Any weapon with a `MinRange` must keep
`MinRange = round(Range / 5)` rounded to the nearest multiple of 5
(`expected = round(Range / 25.0) * 5`). This applies to artillery,
aircraft, and any other actor that uses a minimum firing distance.
Violations are caught by `tools/audit/audit_min_range.py`.

**Unique stat rule.** Every CABAL actor must carry at least one stat or
ability that no other actor shares (cost, speed, range, weapon class,
special K, or role). Two units may not feel identical.

**Armament naming and count.** Every unit uses only three canonical
armament slots: `Armament` (or `Armament@PRIMARY`), `Armament@SECONDARY`,
and `Armament@GARRISONED` for garrison logic. Never create `Armament@AA`,
`Armament@AntiAir`, or role-specific names; anti-air capability is handled
by `ValidTargets` on the same primary/secondary weapon, not by a separate
armament node. A unit that has a primary weapon should not receive a
separate garrison-only pistol; the garrison armament reuses the same weapon
as the primary.

**No weapon inheritance between units (reinforced 2026-07-15).** A
weapon definition must never `Inherits:` from another unit-unique weapon
(e.g. `CabalAvatarLaser` inheriting `CabalCoreDefenderLaser`,
`CabalReaperMissilesAA` inheriting `CabalReaperMissiles`,
`CabalHeavyReaperMissilesAA` inheriting `CabalHeavyReaperMissiles`,
`CabalHeavyReaperTrap` inheriting `CabalReaperTrap`,
`CabalRocketCyborgRocketsUpgraded` inheriting `CabalRocketCyborgRockets`,
`CabalWaspLaserStriker` inheriting `CabalWaspLaser`,
`CabalWidowPlasma` inheriting `CabalRavagerPlasma`,
`CabalCommandoPlasmaNeutron` inheriting `CabalCommandoPlasma`,
`CabalCommandoPlasmaMk2Neutron` inheriting `CabalCommandoPlasmaMk2`,
`CabalRavagerPlasmaNeutron` inheriting `CabalRavagerPlasma`). If two
units need similar firepower, create a shared `^`-prefixed base weapon
template in the faction weapons file and inherit from that template, or
copy the stats explicitly. Unit-unique weapons are not stable extension
points. **This was the root cause of the CreateEffect crash class**:
inheriting a weapon also inherits its `CreateEffect` warhead, and if the
parent's explosion sequence was moved or changed, the child silently
breaks. Copy stats, do not inherit between units.

**Effect inheritance order.** Visual effect templates such as
`^TSLaserEffect`, `^TSSparkEffect`, or faction laser-trail templates
must be inherited **last** in the `Inherits@` chain, after all weapon and
armor templates. Otherwise their trait definitions are overwritten by
later inherits and the intended effect is lost.

**Reusable engineer rule.** Engineers that can capture structures must not
be consumed on capture. Use an engineer armor template that grants the
`CaptureManager` / `Captures` behavior without `Consumed:` true, matching
the Schwarzer Mond "Engineering armor" pattern. CABAL's `cabal_engineer`
uses this reusable pattern.

**Promotion unit stat superiority.** A promotion-unlocked unit must be
strictly better than the base unit it replaces in every meaningful stat.
Allowed exceptions: (a) Speed may be lower only if HP increases
significantly to convey a heavier chassis; (b) ReloadDelay may be longer
only if total damage per salvo increases significantly. **Range must never
be lower** on a promotion unit. Promotion weapons must use stronger
warhead classes than the base unit (e.g. base medium → promotion heavy).
Audit this with `tools/audit/audit_promotion_superiority.py`.

**Linebreaker / mutual-weapon design (CABAL Manticore).** A unit whose
primary and anti-air weapons are mutually exclusive (e.g. a turret that
switches modes or a unit that fires only one weapon at a time) does NOT
add their DPS for balance purposes. Both weapons must be tuned to the
same final values (damage, reload, range) so the spreadsheet sees two
equivalent options, not a doubled output. For the Manticore this means a
ground laser and an air missile with identical range and comparable
throughput, using laser+railgun warheads on the ground weapon and heavy
missile+heavy AA warheads on the air weapon.

**Reaper net weapon (CABAL).** The Cyborg Reaper's net weapon copies the
Zerg Corruptor snare effect: a missile projectile that applies a slow/
snare condition to all valid snareable targets. The net shares the ground
weapon's range; the dedicated anti-air weapon receives the standard +50%
range increase over the ground weapon.

**Hunter Killer weapon identity.** Hunter Killer aircraft are powerful
attackers, not light infantry. Their weapon must use laser / missile
warheads appropriate to their role, never `^SmallArms`.

**Balance workflow.** A CABAL concept sheet may supply design judgment, but numeric
rebalance changes enter the same raw ledger / active faction-or-type workbench pipeline
as every other faction and land in YAML through the guarded apply step. On mismatch,
current ledger extraction and generator rules win over the legacy workbook. Promotions
add `^PromotionUnitBuff` on top of the ledger stats.

**CABAL Avatar — 50% scaled Core Defender (design 2026-07-15).** The
`cabal_avatar` is a mass-produced variant of the Core Defender, NOT a
spider. It is the Core Defender at 50% scale: all visual offsets, weapon
damage, HP, and stats are halved from the `cabal_coredefender` reference.
The avatar uses its own weapon (`CabalAvatarLaser`) which is a copy of
`CabalCoreDefenderLaser` with damage and offsets scaled to 50%, NOT an
inherits-from relationship (§15 no weapon inheritance between units).
The avatar's sequence scale, muzzle offsets, and visual effects are all
50% of the Core Defender's values. This makes the avatar a smaller,
faster-to-produce walker that retains the Core Defender's identity.

**CABAL husk recovery (design 2026-07-15).** CABAL vehicles with the
Backup Systems upgrade leave a `_backup` husk on death. The husk is
immobile (Speed/TurnSpeed = 0), has 2–5× the base unit's HP, is
Repairable, and auto-reanimates after a delay via
`GrantPeriodicCondition@rebuild` + `TransformOnCondition@buildingrebirth`
back into the original unit. The recovery time is currently a fixed
delay (not scalable with remaining/max health in YAML-only — a C# trait
would be needed for health-scaled recovery). The husk carries
`WithColoredOverlay@backup` for a visual indicator. Each CABAL vehicle
needs three things for backup systems:
1. `Inherits@BACKUP: ^cabal_upgrade_backupsystems` (in vehicles.yaml)
   — grants the condition.
2. `SpawnActorOnDeath@backup` trait with
   `RequiresCondition: cabal_upgrade_backupsystems` and
   `Actor: <unit>_backup`.
3. A `<unit>_backup` actor definition in the faction pack's
   `yaml/husks.yaml` (moved from rules/tiberiansun.yaml 2026-07-17) that
   inherits the base unit, sets Speed/TurnSpeed=0, high HP, Repairable,
   removes `SpawnActorOnDeath@backup`, adds
   `GrantPeriodicCondition@rebuild` + `TransformOnCondition@buildingrebirth`
   for auto-reanimation, and `WithColoredOverlay@backup` for the visual.

### 12.0i CONTINUOUS HEAVINESS — the global armor axis and the bell (maintainer 2026-08-23/24) — binding

Replaces the discrete `Light/Medium/Heavy/Super` LEVEL with a continuous heaviness `h`. Full
derivation and the measurements behind every constant: `docs/design/WEAPON_HEAVINESS.md` §9.

> *"the weapon family should be the most important and the heaviness level should only nudge it a
> little … a low level CannonAP will lean stronger towards lighter armor types but still deal more
> damage to heavy armor, the difference just is not too much … Flame weapons will be the opposite
> … but still more damage to light, because that's their identity."*

> *"h=0 leans towards damage against light, h=1 leans towards damage against medium and h=2 leans
> towards damage against heavy — each h value should shift the damage distribution, but on a
> continuous scale."* (maintainer, 2026-08-24)

    x(armor)      = ONE GLOBAL SCALE, 0..2, 13 evenly spaced slots, step 1/6
    mu(family, h) = ( h + centre_of_mass(base_profile) ) / 2
    curve(x)      = LO + (1 - LO) * exp( -(x - mu)^2 / (2*sigma^2) )
    Versus(a, h)  = base(a) * curve(x(a), mu)
                    then renormalised to a constant arithmetic mean over tiltable rows
                    then RANK-RESTORED per ladder (§12.0d) — see law 5

#### The axis (maintainer, 2026-08-24)

> *"scout -> none -> fighter -> light -> wood -> bomber -> medium = flak = steel -> helicopter ->
> concrete -> heavy -> spaceship -> plate -> superheavy … symmetrical armor types that are always
> evenly distributed from 0 to 2.0, and the 3 medium / flak / steel armor types in the middle with
> exactly 1.0."*

| slot | 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 | 12 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `x` | 0.000 | 0.167 | 0.333 | 0.500 | 0.667 | 0.833 | **1.000** | 1.167 | 1.333 | 1.500 | 1.667 | 1.833 | 2.000 |
| armor | Scout | None | Fighter | Light | Wood | Bomber | **Flak · Medium · Steel** | Helicopter | Concrete | Heavy | Spaceship | Plate | Superheavy |

⭐ **EVERY LADDER IS CENTRED EXACTLY ON 1.000.** That is the property the whole model rests on:

| ladder | rungs | width |
|---|---|---|
| VEH | Scout 0.000 · Light 0.500 · **Medium 1.000** · Heavy 1.500 · Superheavy 2.000 | 2.000 |
| INF | None 0.167 · **Flak 1.000** · Plate 1.833 | 1.667 |
| AIR | Fighter 0.333 · Bomber 0.833 · Helicopter 1.167 · Spaceship 1.667 | 1.333 |
| BLD | Wood 0.667 · **Steel 1.000** · Concrete 1.333 | 0.667 |

so `h=1` means "medium" in all four domains at once, `h=0` the lightest rung of every ladder and
`h=2` the heaviest — literally what the maintainer asked for. The WIDTHS are the design claim:
infantry armour varies nearly as much as vehicle armour (a rifleman to power armour), buildings
least — they compensate with HP, and a narrow ladder keeps every anti-light weapon usable against
bunkers (ruled 2026-08-24; wider buildings were offered and declined).

⛔ **THE THREE-WAY TIE AT 1.0 IS DELIBERATE AND IT IS THE ONLY TIE.** `Flak`, `Medium` and `Steel`
sit in three DIFFERENT ladders, and the rank restore is per-ladder, so they are never in
competition. De-tying them (Flak 0.95 / Medium 1.00 / Steel 1.05) moves no row by more than
**0.89%** — measured across 45 families × 5 heaviness values. The tie buys perfect symmetry and
costs nothing. A tie **within** one ladder stays forbidden: that was the 2026-08-24 bucket bug,
where `Bomber` and `Helicopter` shared a coordinate and heaviness could not tell them apart at all.

⛔ **TWO EARLIER FORMS ARE RETIRED.** §12.0d's three coarse buckets tied armors inside a ladder.
The per-ladder 0..2 normalisation that replaced them was unique within a ladder but collided four
ways across ladders (`None`/`Scout`/`Wood`/`Fighter` all at 0.0), which is what the maintainer
rejected: *"I want a continuous value for all of them and all of them should have their own unique
value."*

⚠ **The axis is a DESIGN RULING, not a measurement, and it cannot be one.** Two attempts to derive
it from the 45 authored profiles both failed for structural reasons, and the negative result is
worth keeping: (1) the cross-ladder OFFSETS are provably not identifiable — remove each family's
macro-type priority (the confound: `Bullet` favours infantry whatever its heaviness) and the
per-ladder means of the residual are exactly zero by construction; (2) the within-ladder SPACING
that survives correlates **0.979** with mean `build_order` rank, i.e. it re-reads
`gen_weapon_template`'s own interleave rule rather than confirming it. The corpus can confirm the
rung ORDER — all four ladders come out monotone, independently — and nothing else.

#### The constants

| | value | why |
|---|---|---|
| `LO` | **0.667** (swing 1.50x) | RE-RULED 2026-08-24. 0.80 was measured against the retired family-anchored peak, which moved only 0.25; under the blend the peak sweeps a full 1.0 and 0.80 came out much gentler than the tilt that already ships (per-ladder 0.68–0.84 vs 0.50–0.52). 0.667 = `1/TILT_RATIO`, the same 1.5x span `class_tilt` uses, so collapsing three templates into one preserves today's differentiation. Mismatch against the shipped tilt: 0.089 → 0.056 (no tilt at all = 0.139). |
| `sigma` | **0.75** | RULED 2026-08-24 — it had been an assumed 1.0 inherited from an audit. 0.75 gives the strongest consistent tilt; below ~0.5 the effect starts to INVERT, because only the rung nearest the peak still moves. |
| `mu` | **`(h + centre_of_mass) / 2`** | the BLEND, ruled 2026-08-24 — see law 1. |
| `SHIFT` | **deleted** | it belonged to the family-anchored peak. |
| price effect | **actual effects enter normal pricing; no extra surcharge** | clarified by maintainer 2026-09-10 at 01:19; see law 2. |
| historical check | `audit_heaviness_bell.py`, 2026-08-24 | 48 families, h ∈ {0, 0.5, 1, 1.5, 2}: **0** ladder orderings changed, **0** arithmetic-mean drift, **2** flat families (`Sonic`, `Magic`) at the ratchet. This did not test roster-weighted price invariance. |

#### The laws

1. **THE PEAK IS THE BLEND OF THE HEAVINESS AND THE FAMILY'S OWN MASS.** ⛔ This REPLACES the
   earlier law 1, *"the peak is anchored to the family, never to the tier"*. That law rejected a
   tier-anchored peak because it *"inverted 26 of 42 families"* — but that was measured **before
   the rank restore existed**, the same omission that produced two false "known inversions" (see
   law 5). Re-measured with the restore in place, a pure `mu = h` reorders **nothing**, at any
   sigma, across 44 families × 5 heaviness values. Both pure forms were therefore available and
   the maintainer ruled the blend: `mu = h` gives the family no formal say beyond the restore,
   while `mu = centre_of_mass + SHIFT*(h-1)` made `h=1` mean *"wherever this family already sits"*
   rather than "medium". The blend halves the distance and keeps `h` meaningful.

   The shift still SHARPENS where it agrees with the family's centre of mass (CannonAP,
   heavy-ward) and FLATTENS where it disagrees (Flame, light-ward) — the two halves of §12.0d's
   sentence. Worked example, `CannonAP`, `Versus` at h=0 / 1 / 2: `Superheavy` 160.1 → 174.1 →
   205.0, `Scout` 108.9 → 89.4 → 81.4. At h=0 `Superheavy` is still the largest value in the whole
   profile — the weapon leans lighter without ever ceasing to be anti-heavy.
2. **NO SEPARATE HEAVINESS SURCHARGE.** Clarified by the maintainer on 2026-09-10 at 01:19:
   normal pricing includes actual percentage damage and splash, and roster-weighted armor
   redistribution can also change price. The bell preserves an arithmetic table mean, not
   the target-population-weighted result; `K` is therefore not invariant in `h`. Do not add
   a separate tier term for power already represented by these effects. Preserve source
   placement separately from the final joint stats/price fit. The earlier invariance claim
   is superseded; this does not revive the retired additive model in WEAPON_HEAVINESS §1.
3. **THE LEVEL IS NOT A DAMAGE LADDER, and never was.** 145 `^Warhead_*` templates carry only a
   placeholder `Damage: 2000`: the template holds the SHAPE, the weapon holds the MAGNITUDE. A
   family's effective damage across its rungs is emergent, orthogonal to the bell, and no law
   requires it to rise. `audit_level_ladder`'s monotonic check was retired on 2026-08-23.
4. **EXCLUDED FROM THE AXIS:** `Shield` (§12.0c — its own compressed ladder), the five ALL-CAPS
   platings (§12.0e — they replace the class armor rather than sit on the axis), and `Heroic`
   (§12.0b — a derived cell, recomputed rather than tilted).
5. ⛔ **THE RANK RESTORE IS A STEP OF THE PIPELINE, NOT A FOOTNOTE.** §12.0d already says the tilt
   "is applied to the VALUES and each armor is then given back the RANK it held", and that step is
   what makes "can never invert" TRUE rather than merely hoped for. Measured across 48 families:
   without it the bell changes a ladder's internal order in **127** cases spanning 60
   family/ladder pairs; with it, **zero**. It permutes values inside one ladder, so the multiset
   and therefore its arithmetic mean are untouched. Roster-weighted effectiveness can
   change because weights remain attached to armor identities; see law 2.

   A flat armor table (`Sonic`, `Magic`) takes the implementation's early return and does not
   acquire a bell gradient. Separate percentage-magnitude and radius interpolation can still
   change its power. The earlier claim of a tie-break gradient did not describe the code.

⚠ **"Inert at h=1" is a DEPLOYMENT property, not a design one, and it needs proving separately.**
The intent was the discipline `AreaDamage` shipped under: turn the code on with every weapon at
h=1 and show no resolved number moved. It was unachievable under the old formula — anchored to the
family's mass, the bell reshaped all 48 families at h=1, worst row **13.5%**. Under the ruled model
h=1 peaks at the middle rung of every ladder, i.e. exactly §12.0d's Medium tilt, so the right
acceptance test is: **regenerate the templates through the bell at h ∈ {0, 1, 2} and diff against
today's Light / Medium / Heavy yaml.** Do NOT test it by comparing the bell against the shipped
TEMPLATES directly — the level also changes the body's `step` and `floor` (`LEVELS` in
`gen_weapon_template.py`), so even the shipped `class_tilt` itself scores **+18.7% worse than doing
nothing** on that comparison. Compare tilt to tilt, on the same base.

#### Shared percentage and Shield rule (maintainer 2026-09-10, 03:17 Jakarta)

For newly migrated warheads, `HeavinessMode: SharedVersus` explicitly opts into
one armor table for flat and percentage damage. The bell transforms `Versus`
once. Its Shield row is then multiplied once by `1 + h/2`; both damage halves
read that resulting table. Shield remains outside the bell axis. At equal `h`,
new family bases must have distinct Shield coefficients; retained legacy-level
templates remain visible compatibility duplicates, not hidden exceptions.

The new base conversion is 100 raw damage to 0.01% maximum HP **before** heaviness
and armor. With the existing field units, migrated CannonAP explicitly sets
`PercentageScale: 2000`. The percentage magnitude is multiplied by `h/2`:
zero at h=0, half at h=1, full at h=2. Thus h=0 retains flat damage and the Shield
coefficient floor, but has no percentage component. Integer basis-point units
are rounded half-up once from `Damage * PercentageScale * Heaviness / 400000000`,
where YAML Heaviness is h times 1000. Small hits are quantized; do not describe
the unrounded formula as exact observed damage for every Damage value.

Shared mode rejects separate percentage tables/endpoints and requires active
Heaviness 0..2000. Omitted mode keeps legacy behavior, including existing healing
and standalone percentage warheads. This is an intentional gameplay change,
not an equivalence-preserving refactor. Initial activation is limited to five
CannonAP pilot definitions; it does not authorize automatic whole-roster fitting.

## 16. Rank decorations, experience systems & elite weapons

Cameo uses **two distinct experience systems** with different rank counts,
stat curves, and decoration images. Every faction must use exactly one
system consistently across all its actors.

### 16.1 The two experience systems

**TD/TS system** (`^GainsExperienceTD` in
`ContentPacks/TiberianDawn/Shared/yaml/templates.yaml`):
- 4 veteran ranks + elite (5 pips total).
- XP thresholds: 200, 400, 600, 800. Elite at `rank-veteran >= 4`.
- `^GainsExperienceTD` does NOT include `WithDecoration` — rank icons
  come from a separate `^*RankDecoration` template that the actor must
  also inherit via `Inherits@decoration`.
- No elite weapons by design — stat multipliers scale progression.
- Building variant: `^GainsExperienceTDBuilding` (250/500/750/1000 XP).

**RA2 system** (`^GainsExperienceRA2` in `rules/redalert2.yaml`):
- 5 veteran ranks + elite (6 pips total).
- XP thresholds: 100, 250, 450, 700, 1000. Elite at `rank-veteran >= 5`.
- `^GainsExperienceRA2` includes `WithDecoration` with `Image: ra2rank`
  and a `rank-veteran-4` sequence — rank icons are built-in, no separate
  decoration template needed.
- **Elite weapons**: every RA2-styled actor with a primary armament must
  also have an `Armament@ELITE` block gated on `RequiresCondition:
  rank-elite` (see §16.3).
- Stronger multipliers than TD/TS: damage reduction to 50%, firepower to
  200%, speed to 125%. Reload/Range/Detect multipliers stay at 100 (RA2
  favors raw damage/speed over utility scaling).
- Building variant: `^GainsExperienceBuildings` (inherits
  `^GainsExperience`, adds firepower multipliers).

The default `^GainsExperience` in `defaults.yaml` is a third variant used
by RA1 and other non-TD/TS/RA2 factions. It has 4 veteran ranks (like
TD/TS) but includes `WithDecoration` with `Image: rank` (the generic
rank sprite) and crate-powerup decorations. Factions using this system
do not need a separate `^*RankDecoration` inherit.

### 16.2 Rank decoration images

Every faction should eventually have its own rank decoration image and
`^*RankDecoration` template. The sequence images are defined in
`sequences/misc.yaml` under their respective keys.

| Image key | Template | Used by |
|---|---|---|
| `rank` | (built into `^GainsExperience`) | RA1, default factions |
| `gdirank` | `^GDIRankDecoration` | TD GDI, TS GDI (shared) |
| `nodrank` | `^NodRankDecoration` | TD Nod, TS Nod (shared) |
| `cabalrank` | `^CABALRankDecoration` | TS CABAL |
| `forgotrank` | `^ForgottenRankDecoration` | TS Forgotten |
| `dunerank` | `^DuneRankDecoration` | D2k factions (Atreides, Harkonnen, Ixian, Ordos) |
| `alienrank` | `^AlienRankDecoration` | StarCraft Zerg (TODO — split per-faction: Zerg keep `alienrank`, Protoss and Terran need separate decorations) |
| `ra2rank` | (built into `^GainsExperienceRA2`) | RA2, RA2Mod factions, TKM |

**Rules:**
- TD and TS share rank images per side: both TD GDI and TS GDI use
  `gdirank`, both TD Nod and TS Nod use `nodrank`.
- RA2 factions all share `ra2rank` (baked into `^GainsExperienceRA2`).
  RA2Mod factions (AsianAlliance, Consortium, FutureTech, Naxis,
  SchwarzerMond, Syndicate) also use `ra2rank` via `^GainsExperienceRA2`.
- `^*RankDecoration` templates use `Palette: greyscale` (not `effect`)
  for TD/TS/CABAL/Forgotten/Dune factions. The RA2 system uses
  `Palette: effect`.
- Actors using `^GainsExperienceTD` MUST also inherit the appropriate
  `^*RankDecoration` via `Inherits@decoration` — otherwise they show no
  rank pips at all.
- Actors using `^GainsExperienceRA2` or `^GainsExperience` do NOT need
  a separate `^*RankDecoration` — their rank icons are built-in.

**Audit rule** (`audit_rank_decoration.py`, TODO): every actor with
`Inherits@EXPERIENCE: ^GainsExperienceTD` must also have
`Inherits@decoration: ^*RankDecoration` matching its faction. Actors
with `^GainsExperienceRA2` must NOT have a separate `^*RankDecoration`
(it would conflict with the built-in decorations).

### 16.3 Elite weapons (RA2 system only)

**Every RA2-styled actor with a primary armament must have an elite
weapon.** When a unit reaches elite rank, its primary weapon is
replaced by an upgraded version via `Armament@ELITE`.

**Pattern:**
```yaml
Armament@PRIMARY:
    Weapon: <baseWeapon>
    RequiresCondition: !rank-elite
Armament@ELITE:
    Weapon: <baseWeapon>_elite
    RequiresCondition: rank-elite
```

**Naming convention:** ALL elite weapons append `_elite` — this is the
only accepted suffix, regardless of the weapon's naming style.
- **Legacy PascalCase weapons** (not yet migrated to actor-prefixed
  names): the elite weapon name is the base weapon name with `_elite`
  appended (e.g. `BorisAKM` → `BorisAKM_elite`). The legacy `E` suffix
  (e.g. `BorisAKME`) is deprecated and must be migrated to `_elite` when
  the weapon is touched. Non-standard names (e.g. `AsianRailTank2`,
  `NaxPlanegun`) are bugs and must be renamed to follow the `_elite`
  suffix convention.
- **New actor-prefixed weapons** (lowercase, per §1 weapon naming rule):
  the elite weapon name appends `_elite` (e.g.
  `ra2_soviets_conscript_ak47` → `ra2_soviets_conscript_ak47_elite`).
  This is consistent with the lowercase underscore convention.

**Critical distinction — EMP weapons are NOT elite weapons:**
Weapons whose primary function is EMP disable (e.g. `SteelEmpBomb`,
`TSEMPZapWeapon`, `CorsairEMP`) must NOT be confused with elite
variants. EMP weapons use the `_EMP` suffix (see §1), not `_elite`.
The previous bulk rename (reverted) incorrectly treated EMP weapons as
elite weapons — this must never happen again. The audit script
(`audit_weapon_suffixes.py` X1 section) only checks weapons gated by
`RequiresCondition: rank-elite`, so EMP weapons are never flagged.

**Audit rules** (`audit_elite_weapons.py`, TODO):
1. **E1 — Missing elite weapon**: every actor using
   `^GainsExperienceRA2` with at least one `Armament@PRIMARY` (or
   `Armament@PRIMARY`-equivalent without `RequiresCondition: rank-elite`)
   must also have an `Armament@ELITE` block. 217 actors currently fail
   this check.
2. **E2 — Missing rank-elite condition**: every `Armament@ELITE` block
   must have `RequiresCondition: rank-elite` (or a condition that
   includes `rank-elite`). 77 of 143 elite armaments currently fail
   this check — they fire at all ranks, not just elite.
3. **E3 — Non-standard naming**: elite weapon names must end with
   `_elite`. The legacy `E` suffix is deprecated. Weapons ending with
   `E` that are NOT elite variants (e.g. EMP weapons, `PrismChargeE`)
   must not be flagged — only weapons gated by `rank-elite` are checked.
4. **E4 — Base weapon must not fire at elite**: the primary armament
   must have `RequiresCondition: !rank-elite` (or equivalent) so the
   elite weapon replaces it, not stacks with it.

## 17. Dune 2000 to OpenRA Sprite Conversion

When converting individual Dune 2000 BMP frames to OpenRA PNG spritesheets,
use the `tools/d2k_to_openra.py` script. This is the standard pipeline for
all D2K asset conversions (e.g. Koda Tank).

### Conversion Steps

1. **Source frames**: Individual BMP files extracted from Dune 2000 `.R16`
   archives, numbered `Prefix_0.bmp` through `Prefix_N.bmp` (e.g.
   `KodaBody_0.bmp` ... `KodaBody_31.bmp`).

2. **Run the script**:
   ```
   python tools/d2k_to_openra.py <input_dir> <output.png> [--prefix Prefix] [--hue HUE] [--no-hue-shift]
   ```
   - `--prefix`: filter frames by filename prefix (e.g. `KodaBody`)
   - `--hue`: target hue for player-color remap (default 300 = magenta)
   - `--no-hue-shift`: skip hue shifting (for chassis frames with no player color)
   - `--remap-hue-min` / `--remap-hue-max`: customize the source hue range
     (default 140–190°, covering the D2K green ramp)

3. **What the script does**:
   - Combines all BMP frames into a single horizontal PNG strip
   - Normalizes frame sizes to the largest frame (smaller frames centered)
   - Converts pink background (RGB 255,0,255) to transparent alpha
   - Hue-shifts the green player-color ramp (~163°) to the target hue
   - Embeds PNG metadata (`FrameAmount`, `FrameSize`) so OpenRA can split
     the strip into individual frames at load time

4. **Output placement**: PNG spritesheets go in `mods/cameo/bits/d2k/`
   (not in ContentPack `files/` directories — the engine's file system
   resolves sequence assets from the global `bits/` folder).

5. **Sequence wiring**: Use `Facings: -32` (for 32-frame D2K sprites) with
   `Filename: <name>.png` and `Start: 0`. No `Remap` or `Scale` fields
   needed — the PNG already has transparency and player color baked in.
   Muzzle flashes can still reference `DATA.R16` with `Remap: 54F94B`.

### PNG Metadata Format

OpenRA recognizes PNG spritesheets by two text chunks:
- `FrameAmount`: number of frames in the strip (e.g. `32`)
- `FrameSize`: frame dimensions in pixels as `W,H` (e.g. `39,30`)

The strip width must equal `FrameAmount * FrameSize_W`.
The strip height must equal `FrameSize_H`.

### Hue Shifting Rules

- **Chassis/body frames**: Use `--no-hue-shift` (no player color in body)
- **Turret frames**: Use `--hue 300` (shift green ramp to magenta for Ixian)
- Other factions may use different target hues (e.g. Atreides blue, Harkonnen red)
- The script preserves saturation and value; only hue changes
- Pixels outside the remap hue range are left untouched

## 18. Schwarzer Mond Faction Design

### 18.1 Faction identity

Schwarzer Mond is the **space-faring, occult-science branch** of the Naxis.
Where the base Naxis faction is a clanking WWII pastiche, Schwarzer Mond is
its lunarpunk extension: gravity manipulation, crystal leech fields, yellow
lasers, green plasma shells, and flying saucers. Its intended power curve is
**early-game fragile, mid-game timing attack, late-game tank/artillery/space
superiority**, with a known weakness to aircraft and early rushes.

### 18.2 Roster (current)

**Infantry**
- `schwarzer_mond_lunarsoldier` — basic scout rifle (T1, laser, burst 1)
- `schwarzer_mond_lunarrocket` — rocket trooper (T1, anti-ground/anti-air)
- `schwarzer_mond_bermensch` — heavy infantry (T3, laser, burst 2)
- `schwarzer_mond_parzival` — hero black-hole caster (T3, buildlimit 1)
- `schwarzer_mond_noidmgarmor` — walker with MP40 laser (T2, burst 5)
- `schwarzer_mond_noidharvester` — harvester walker (T1, laser)
- `schwarzer_mond_engineeringarmor` — engineer/capture walker (T1)

**Vehicles**
- `schwarzer_mond_laserbeetle` — light laser support tank (T1, burst 2)
- `schwarzer_mond_lunarpanzer` — hover MBT (T1, cannon)
- `schwarzer_mond_lunartiger` — heavy hover MBT (T2, cannon)
- `schwarzer_mond_neojagdpanzer` — line-breaker TD (T3, cannon)
- `schwarzer_mond_lunargrille` — hover artillery (T2, cannon)
- `schwarzer_mond_korruptesbiest` — fire-support walker (T3, corrosion)
- `schwarzer_mond_crystaltank` — fire-support leech tank (T3)
- `schwarzer_mond_mars` — missile artillery (T2)
- `schwarzer_mond_m200bjagerline` — AA/artillery hybrid (T2)
- `schwarzer_mond_lasertank` — medium laser tank (T1, burst 4)
- `schwarzer_mond_gravitycoretank` — gravity debuff tank (T3)

**Aircraft**
- `schwarzer_mond_spacezeppelin` — heavy transport/gunship (T2, laser)
- `schwarzer_mond_blackbomb` — kamikaze plane (T3)
- `schwarzer_mond_haunebuii` — spaceship (T2, cannon/flak)
- `schwarzer_mond_haunebuiii` — heavy spaceship (T3, cannon/cow drop)
- `schwarzer_mond_corruptorpiercer` — rocket fighter (T3)
- `schwarzer_mond_dieglocke` — epic superweapon saucer (T3, buildlimit 1)

**Defenses**
- `schwarzer_mond_lasertower` — anti-infantry laser tower (T1, burst 1)
- `schwarzer_mond_sturmcannon` — artillery cannon defense (T2)
- `schwarzer_mond_gravitycore` — gravity superweapon building (T3)
- `schwarzer_mond_meteortractionray` — meteor superweapon (T4)

**Economy**
- `schwarzer_mond_moondairyfarm` — passive income building (T3)

### 18.3 Current upgrade audit

Two upgrades exist today:
- `schwarzer_mond_upgrade_crystallens` — **radar-tier** (wrong: should stay radar,
  but it currently doubles laser burst)
- `schwarzer_mond_upgrade_greenplasmashells` — **radar-tier** (wrong: should be
  **tech-tier** because it is a +25% firepower cannon upgrade for the whole tank
  line)

**Coverage gaps** (every unit must eventually be affected by at least two
upgrades, see §18.6):
- Crystal Lens only affects laser units; many non-laser units receive nothing.
- Green Plasma Shells only affects cannon units; the rest of the roster receives
  nothing.
- No team-wide economy, survivability, or utility upgrade exists yet.

### 18.4 Laser upgrade split (the +1-burst rule)

The current Crystal Lens upgrade **doubles** the burst of every laser weapon.
This is a ~2× damage spike and breaks the power-budget rule (§6: worst-case
stack ≤ 2× fresh-self). The upgrade must be split into two **+1-burst** steps:

- **Tier 1 — Crystal Lens** (`schwarzer_mond_upgrade_crystallens`, radar tier):
  +1 burst for **all** yellow laser weapons.
- **Tier 2 — Amplified Lens** (`schwarzer_mond_upgrade_amplifiedlens`, tech tier,
  requires Crystal Lens): another +1 burst for all yellow laser weapons.

Weapons with base burst 1 (`NaxiRifleLaser` on the Lunar Soldier, `NaxLaserT`
on the Laser Tower) are intentionally weak and therefore **do** benefit from the
+1-burst steps. The progression for a 1-burst weapon is 1 → 2 → 3, which is still
bounded by the +2 total cap and keeps the weakest lasers relevant.

Resulting burst progression:
| weapon | base | +Crystal Lens | +Amplified Lens |
|---|---|---|---|
| NaxiRifleLaser / NaxiRifleLaserE | 1 | 2 | 3 |
| NaxLaserT | 1 | 2 | 3 |
| NaxiBeetleLaser / AA | 2 | 3 | 4 |
| ÜbermenschLaser | 2 | 3 | 4 |
| NaxiTank2Laser / AA | 4 | 5 | 6 |
| NaxiMP40Laser | 5 | 6 | 7 |
| NaxiMP40LaserE | 10 | 11 | 12 |
| ÜbermenschLaserE | 4 | 5 | 6 |

The two upgrades **must not stack to double** any weapon. The total effect is
+2 bursts instead of ×2, which is much closer to the power-budget target.

### 18.5 Cannon upgrade tier move

`schwarzer_mond_upgrade_vrilpoweredweapons` (formerly *Green Plasma Shells*) must
move from `~schwarzer_mond_radar` to `~schwarzer_mond_techcenter`. The Vril energy
core gives cannon vehicles +25% firepower and converts their damage to a
Tesla-type discharge. This is a tech-tier effect (compare Naxis
`naxis_upgrade_wunderwaffe` at tech tier). The `Queue` stays `Research`.

### 18.6 Proposed upgrade framework

Every Schwarzer Mond unit must inherit at least two upgrade templates. The
following templates are the canonical set:

- `^NaxiCryptofascism` — economy trickler (1 credit per 25 ticks per unit).
  Tech tier, `Research` queue. Every Schwarzer Mond unit inherits this.
- `^NaxiCrystalLens` — radar-tier laser burst +1 for ALL yellow laser
  weapons (including 1-burst weapons). Laser units inherit this.
- `^NaxiAmplifiedLens` — tech-tier laser burst +1 for ALL yellow laser
  weapons (including 1-burst weapons). Laser units inherit this
  (requires Crystal Lens).
- `^NaxiVrilPoweredWeapons` — tech-tier +25% firepower and Tesla-type damage
  for cannon vehicles. Named after the Vril energy core from the Black Sun
  occult-science program.
- `^NaxiLunarAlloys` — radar-tier +10% damage reduction for all Schwarzer Mond
  units. Fills the survivability gap for non-laser, non-cannon units.
- `^NaxiMoonPropaganda` — tech-tier +10% firepower for all Schwarzer Mond
  infantry. The morale campaign is funded by **MoonCoin**, the official
  cryptocurrency of the Reichsmark 2.0 blockchain.
- `^NaxiHelium3` — radar-tier +50% power output for Hydrogen Plants and +25%
  speed/turn rate for all vehicles and aircraft. The Moon's regolith is rich in
  Helium-3, the isotope that fuels the Fourth Reich's fusion reactors and the
  Götterdämmerung-class warships; enriched Helium-3 is also used as a high-
  specific-impulse propellant for lunar vehicles and saucers.
- `^NaxiVrilInfusion` — tech-tier +25% firepower, +25% speed/turn rate and +15%
  damage reduction (Modifier 85) for all Schwarzer Mond infantry. Vril energy
  from the Black Sun program is spliced into the troopers, creating true
  Übermenschen on the battlefield.

Upgrade queue layout:
- **Radar tier (`Upgrades`)**: Crystal Lens, Lunar Alloys, Helium-3 Enrichment.
- **Tech tier (`Research`)**: Amplified Lens, Vril Powered Weapons, Vril Infusion,
  Cryptofascism, Moon Propaganda.

### 18.7 Promotion grid proposal

Schwarzer Mond uses the RA2 experience system (`^GainsExperienceRA2`) and can
support a 3-column promotion grid. The image proposal groups units into three
rough columns; this is refined into a **unit-improvement** promotion tree
because the listed units already exist in the regular tech tree.

| column | rank 1 | rank 2 | rank 3 | rank 4 |
|---|---|---|---|---|
| **Lunar Infantry** | Heavy Lunar Soldier | Übermensch Mk2 | Parzival (already hero) | — |
| **Lunar Armor** | Laser Beetle Mk2 | Lunar Tiger Mk2 | Neo Jagdpanzer Mk2 | Dalek (already epic) |
| **Lunar Flight** | Haunebu II (rebalanced) | Corruptor Piercer Mk2 | Haunebu III Mk2 | Die Glocke (already epic) |

Notes on the image proposal:
- The image lists **12 units** but the faction has **~25 buildable units**.
  The grid must cover the full roster or be supplemented by non-promotion
  upgrades.
- `Bradley` does not exist in the Schwarzer Mond roster; the closest unit is
  `MARS` (missile artillery) or `M-200B Jagerline` (AA/artillery). Either the
  image uses an old name or it refers to a different faction.
- `Noid MG`, `Neo Jagdpanzer`, `Korruptes Biest`, `Dalek` are a coherent heavy
  column.
- `Übermensch`, `Laser Tank`, `Crystal Tank`, `Parzival` are a coherent elite
  column.
- `Piercer`, `Haunebu 3`, `Die Glocke` are a coherent aircraft column, but
  `Bradley` is out of place.

If promotions are meant to **unlock** units, the base versions must be placed at
the appropriate tech tiers and the promotion versions must be strictly stronger
(§15 promotion superiority rule). If promotions are meant to **upgrade**
existing units, use the `^PromotionUnitBuff` template and add new upgrade
variants.

### 18.8 Cryptofascism upgrade

- ID: `schwarzer_mond_upgrade_cryptofascism`
- Name: Cryptofascism
- Tier: tech center, `Research` queue
- Cost: placeholder (rebalance with spreadsheet)
- Effect: grants every Schwarzer Mond unit a `CashTrickler` of 1 credit per
  25 ticks while the unit is alive.
- Icon: `nax2_cryptofascismicon.png` (64×48 px, placed in the faction's
  `files/` folder and wired via a sequence icon entry).
- Template: `^NaxiCryptofascism` added to every Schwarzer Mond actor's
  `Inherits` chain.

Because the effect scales with army size, it is a late-game snowball upgrade.
Cost and placement must be tuned so it pays back only after a large army exists.

### 18.9 Faction description normalization

The Schwarzer Mond description in `ContentPacks/RedAlert2Mod/SchwarzerMond/
translations/en.ftl` should follow the same point-based format used by Ixians,
Ordos, and Naxis:

```
Difficulty: ©©©
Early Game: ©©
Mid Game: ©©©©©
Late Game: ©©©©
Playstyle: Timing Attack
Strength: Mid to Lategame Tanks and Artillery
Weakness: Aircraft
Countered by: Early Game Rush, Aircraft
Special Units: Parzival, Dalek, Die Glocke
Special Buildings: Moon Dairy Farm, Gravity Core
Team Upgrades: Cryptofascism, Lunar Alloys
Support powers: Gravity Core, Meteor Blitzkrieg
```

Other RA2Mod factions (Consortium, Asian Alliance, Syndicate, FutureTech,
Naxis) should be normalized to the same format when touched; Schwarzer Mond is
the first to receive the full template because it is the focus faction.

### 18.10 Implementation order

1. [DONE] Add the new templates to `ContentPacks/RedAlert2Mod/Shared/yaml/
   templates.yaml` (Crystal Lens, Amplified Lens, Vril Powered Weapons, Lunar
   Alloys, Moon Propaganda, Cryptofascism, Helium-3, Vril Infusion).
2. [DONE] Add the four new upgrade actors to `ContentPacks/RedAlert2Mod/SchwarzerMond/
   yaml/upgrades.yaml`.
3. [DONE] Move Green Plasma Shells to tech center; split Crystal Lens; add
   Amplified Lens.
4. [DONE] Add the icon sequence for Cryptofascism and place the PNG in
   `mods/cameo/bits/ra2/mod/` (the same location used by the existing upgrade
   icons).
5. [DONE] Wire every Schwarzer Mond actor to the appropriate upgrade templates.
6. [DONE] Update weapon variants for the new +1-burst laser tiers.
7. [DONE] Update the faction description and individual unit descriptions.
8. [IN PROGRESS] Run the full audit suite (`tools/audit/run_all.sh`) and rebuild.
9. [TODO] Update the balance spreadsheet for any stat changes that affect cost or
   tier placement.
10. [DONE] Rename Green Plasma Shells to Vril Powered Weapons and add Helium-3
    Enrichment upgrade.
11. [DONE] Re-enable Crystal Lens / Amplified Lens on 1-burst laser weapons.
12. [DONE] Replace copy-pasted unit icons with unique placeholders per
    `docs/design/RESEARCH_NOTES.md`.
13. [DONE] Finalize promotion intent: use existing `^PromotionUnitBuff` on all
    combat units instead of unlocking new actor variants.
14. [TODO] Boot-test the mod and verify the overhaul in-game.

### 18.11 Open questions for design

- Promotions will **upgrade existing units** via `^PromotionUnitBuff` rather than
  unlocking new actor variants. The existing RA2 experience system already
  provides veteran/elite ranks; the promotion grid proposal is flavor-only and
  does not require new Mk2 actors. All combat units now inherit the buff.
- The unit formerly referred to as `Bradley` in the promotion image is the
  hover artillery unit now named **MARS** (`schwarzer_mond_mars`). The name is
  an acronym (MARS = MRLS / mobile artillery rocket system) and follows the
  convention: actor id `schwarzer_mond_mars` (lowercase, underscore), display
  name `MARS` (uppercase acronym). The unit uses the `NaxisBradleyTarget`
  weapon, which is a legacy internal name that does not need to change unless
  we want to fully purge the old label.
- **MARS is AA-capable** (ground + air, long range). Laser Beetle and Laser
  Tank are also AA. SM does NOT lose all mobile AA when MARS replaces Jagerline
  — MARS is a direct upgrade with AA capability. The "no mobile AA" concern is
  invalid.
- Moon Dairy Farm passive income and Cryptofascism are independent: the dairy
  farm is a building income source, Cryptofascism only generates cash from living
  units. They can stack without special capping.
- **Promotion grid tier-mismatch (DESIGN DECISION NEEDED):** The current 3×4
  grid has row 1 unlocking T3 units (Übermensch, Piercer) while row 2 unlocks
  a T1 unit (Laser Tank). Five solution options are documented in
  `docs/design/ROADMAP.md` under "P2 — SM promotion grid tier-mismatch".
  Recommended: Option C (CABAL pattern — promotion gates visibility, tech
  gates power) or Option D (hybrid — soft tier sorting + CABAL gating).
  **CABAL has the same problem** — see "P2b — CABAL promotion grid
  tier-mismatch" in ROADMAP. FutureTech solved it by making all
  promotion-units T3 (every unit requires high-tier buildings). Awaiting
  maintainer decision on which pattern to apply to both SM and CABAL.

### 18.12 Lore research — Iron Sky, Nazi Moon, and conspiracy-parody sources

Schwarzer Mond is built on the *Moon Nazi* conspiracy/parody trope, most famously
presented in the 2012 film *Iron Sky* and its 2019 sequel *Iron Sky: The Coming
Race*. Key motifs that can be mined for upgrades, unit names, and faction flavor:

- **Nazi Moon base**: In 1945 the Third Reich evacuates to the far side of the
  Moon, builds a swastika-shaped fortress, and waits decades to launch an
  invasion fleet of flying saucers and zeppelins. This is the core origin of
  Schwarzer Mond.
- **Helium-3**: The Moon's regolith is rich in Helium-3, a fusion fuel. In *Iron
  Sky* the Nazis mine it to power their ships, reactors, and the giant
  warship *Götterdämmerung*. This justifies a Helium-3 power/economy upgrade.
- **Vril and the Black Sun**: The sequel ties Nazi UFO technology to the Vril,
  a reptilian subterranean race that allegedly gave the Nazis advanced energy
  technology. "Vril Powered Weapons" replaces the generic "Green Plasma Shells"
  name and grounds the cannon upgrade in occult-science lore.
- **Die Glocke / Haunebu / Reichsflugscheibe**: Classic Nazi UFO conspiracy
  craft names (the Bell, the flying disc) that already appear in the roster as
  units (Haunebu II/III, Die Glocke).
- **MoonCoin / Reichsmark 2.0**: A crypto-currency parody fits the satirical
  tone. The Moon Propaganda upgrade is described as funded by MoonCoin on the
  Reichsmark 2.0 blockchain.
- **Jobsism and modern cults**: *Iron Sky 2* satirizes tech cults. This is
  optional flavor for future support powers or upgrades.

These sources are used only as parody/satire references; the faction remains a
fictional sci-fi faction, not an endorsement of any real-world ideology.

## 19. AI bot personalities

Each bot draws one of five squad-manager personalities per match: Rush,
Turtle, Tech, Expansion, or Steamroller. Hard-and-above bots can switch
dynamically through a `SetBotPersonality` order; the synced controller keeps
exactly one personality condition active at a time. Switching observes a
`PersonalityHoldTicks` minimum hold and bypasses it when entering Emergency.
Lower tiers retain the fixed random personality because
`AllowPersonalitySwitching` defaults to false.

The personality effect is currently confined to the squad manager. Each
personality has its own `SquadManagerBotModuleCA` instance gated by
`genericbot && personality-*`, while base building, unit production, budgets,
and difficulty definitions remain shared. The Steamroller profile is documented
as having **at most one harasser**: the engine short-circuits creation of the
first guerrilla squad, and zero guerrilla units is not expressible in YAML.

When a personality condition becomes active, the reusable
`ObserverConditionNotification` trait announces the selected profile in the
chat feed for spectators and replay viewers. Live players do not see this
indicator because revealing an opponent's strategy would leak information.
The notification is delayed by 25 ticks by default, appears once per trait
instance, and is display-only and client-local. It is intentionally chat-only;
there is no live-player UI decoration for the personality.

`RushInterval` and `RushAttackScanRadius` are deliberately absent from the
personality blocks. They are stale keys from an older squad manager and are not
declared by either the vendored CA implementation or the pinned engine.

Only the attack-force value threshold gains a time ramp. The five personality
blocks replace their flat `SquadValueRandomBonus` with ramp values that preserve
the same early-game maximum, while the flat bonus path remains supported for
other squad-manager instances. The ramp reaches its late-match range over the
first 20 minutes using the default 25 ticks per second. Long-match ramp
behavior has not been observed in-game; that verification is a follow-up.

## 20. AI bot unit compositions

Unit compositions are opt-in through `UseCompositions: true` on
`UnitBuilderBotModuleCA`; existing unit builders continue to use their
`UnitsToBuild` shares by default. Cameo has no separate baseline composition:
the single shared `UnitsToBuild` table on the one unit builder is the fallback
whenever no active composition applies. Compositions are therefore not
personality-specific today.

An active composition only biases the production queue categories named by its
`UnitQueues` field; an empty list applies to every category. The current pilot
contains two 50%-chance, vehicle-focused TD compositions: a GDI armor push
gated by `td_gdi_weaponsfactory` and a Nod stealth push gated by
`td_nod_templeofnod`. Both become eligible after 9000 ticks, have a 15000-tick
per-composition reselection interval, and expire after 4500 ticks.

Explicit unit requests, including harvester and MCV requests, continue through
the bypass path and do not use composition share filtering. Only boot
verification has been performed for this system; no long-match in-game
composition behavior is claimed.

## 21. AI architecture (forward design)

### 21.1 Record-only AI match logging

AI match logging is record-only: it never changes gameplay and the game never
reads the log back. The writer runs on the host only and emits schema version 1
JSONL records.

The phase-2 master publishes an observe-only per-enemy snapshot and computes
candidate personality and target values for logging only. It queues no orders,
grants no conditions, touches no synced state, and remains pre-fog by design.
The situation records use schema version 1 in the same record-only boundary.

The forward design for bot modules, per-ContentPack AI splitting, the dynamic
personality manager, the master AI module, and match logging lives in
[`design/AI_ARCHITECTURE.md`](design/AI_ARCHITECTURE.md). Sections 19 and 20
above remain the binding rules for what ships today; record-only match logging
and the observe-only phase-2 master snapshot are implemented as described.

Two measured constraints from that document are binding on any AI yaml edit,
because both fail in ways that reading the yaml will not reveal:

* **A ContentPack can add to a bot module, never override or remove.**
  `ContentPacks/**/yaml/ai.yaml` resolves BEFORE `cameo|ai/ai.yaml`, so any key
  the global AI file sets wins permanently, and `-TraitName` removal syntax in
  a pack for a trait the global file declares is a load-time `YamlException`, not
  a no-op. Moving faction data into a pack therefore requires deleting it from
  the global file in the same change, verified by an unchanged
  `--resolved-rules Player` dump.
* **`UnitCompositionsBotModule` must stay a single instance.**
  `UnitBuilderBotModuleCA` resolves it with `TraitOrDefault`, which throws on
  the second instance, and a disabled `ConditionalTrait` still occupies the
  trait dictionary - so condition-gating multiple composition modules crashes
  on the first bot tick rather than degrading. Personality-specific compositions use
  condition-gated `ProvidesPrerequisite` tokens instead.
