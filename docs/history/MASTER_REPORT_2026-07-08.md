# CAMEO MOD — Master Technical, Balance & Roadmap Report

> **Historical document.** This report is dated 2026-07-08 and reflects the
> state of the repository at that time. Per `docs/README.md`, this is
> historical analysis — not a live roadmap. Active work belongs in
> `docs/design/ROADMAP.md`. Commit counts, PR counts, and release references
> are stale. Consult this document for bug taxonomy (B1–B12) and structural
> analysis, not for current task status.

**Repository:** `cameo-mod/Cameo-mod` (fork of `Zeruel87/Cameo-mod`), OpenRA Mod SDK based
**Report date:** 2026-07-08 · **Latest release analyzed:** Tournament Build 23 (`playtest-20260707`)
**Intended audience:** Maintainers, contributors, and AI coding agents working on the repo

---

## 0. How to use this document

This report was originally designed as a living reference; it is now a **historical document** (see notice above). The structural analysis and bug taxonomy remain useful, but all task status, roadmap, and operating instructions should be sourced from `docs/DESIGN.md`, `docs/design/ROADMAP.md`, and `docs/AGENT_WORKSPACE.md` instead.

- **Humans:** Read §1 (summary) and skim the section relevant to what you're working on. §12 (roadmap) is stale — use `docs/design/ROADMAP.md` instead.
- **AI agents:** §10 (inheritance rules), §9 (naming rules), and §13 (operating guide) may provide useful context, but the binding versions live in `docs/DESIGN.md` and `docs/AGENT_WORKSPACE.md`. When they disagree, the repository docs win.
- **Confidence levels:** Findings are tagged **[VERIFIED]** (directly evidenced in the repository, changelogs, or release notes), **[INFERRED]** (strongly implied by verified evidence plus OpenRA architecture), or **[HYPOTHESIS]** (design/balance judgment that must be validated by playtesting or by running the audit scripts on a local checkout). GitHub blocks automated file-tree crawling, so line-level enumeration of every actor YAML must be produced locally with the Appendix A scripts — this document tells you *what to look for, why it matters, and how to find all of it automatically*.

---

## 1. Executive summary

Cameo is arguably the most ambitious crossover RTS ever attempted: dozens of playable factions from C&C (TD, TS, RA1, RA2-era), Dune 2000, StarCraft, WarCraft 2, plus a full family of original factions (Steel Consortium, FutureTech, Schwarzer Mond, Latin Syndicate, Asian Alliance, Naxis, Empire of Japan, TKM, Forgotten, CABAL…). The project's own README calls it "extremely buggy" — and the release notes prove the honesty of that statement, but they also prove something more important: **the bugs are not random. They cluster into about a dozen repeating structural classes**, nearly all of which trace back to three root causes:

1. **Uncontrolled inheritance.** Actors inherit from other concrete actors, from other factions' actors, and from stale templates. Verified consequences in the last five builds alone: Yuri Slave Miner dealing too much damage from a wrong inherit, Schwarzer Mond Lunar Tiger dealing too much damage from a wrong inherit, a "stale warhead inheritance" in the Forgotten roster, and Nod's SAM Site and Obelisk *leaking into CABAL's buildable roster* as duplicates. **[VERIFIED]**
2. **No naming or file-layout contract.** Some factions use a modern `faction_type_name` scheme; others still carry original-game IDs (`e1`, `4tnk`, `obli`…). This is why cross-faction leaks happen silently, why "Consortium" and "Steel Consortium" are used interchangeably even in your own changelogs, and why tooltips end up mislabeled (Tech Center and CABAL Core both displaying "Radar"). **[VERIFIED]**
3. **No automated invariant checking.** Every recent build fixed a bug a linter could have caught: an upgrade that made reload *slower* instead of faster (Dark Armament), a selection-box scale factor wrong by ~42× "across most rule files," a typo that crashed the game the first time a Runner Shotgal was produced, an `ai.yaml` referencing the wrong building so the Forgotten AI never built aircraft, and a promotion icon pointing at a nonexistent sprite. **[VERIFIED]**

The good news: the team is already moving in the right direction — the template rebalance (TB18), the systemic selection-box fix (TB23), CABAL's research tier being normalized to match GDI/Nod (TB23), and the RAM optimization pass (−51% peak memory) are exactly the kind of *systemic* work this report doubles down on.

**The core recommendation of this report:** stop treating bugs as individual incidents and instead (a) adopt the strict template-only inheritance architecture in §10, (b) adopt the naming scheme in §9, and (c) build the CI/lint harness in §11 + Appendix A so that entire bug classes become impossible to merge. Do this *before* the next big content push (the roadmap in §12 sequences it around the July 2026 Showcase Tournament). Every faction migrated to the new architecture becomes independently loadable, independently testable, and safely editable by AI agents in parallel — which is the force multiplier a 3-person-scale team building a 190-faction game actually needs.

---

## 2. What was audited and how

### 2.1 Sources examined **[VERIFIED]**

- Repository root of `cameo-mod/Cameo-mod` (structure, README, `CLAUDE.md`, `mod.config`).
- Full release notes for Tournament Builds 15–23 (`playtest-20260608` → `playtest-20260707`), including the "CAMEO's Optimization RAMpage" release, plus historical releases from the upstream `Zeruel87/Cameo-mod` (v0.29 era and later playtests).
- Public project descriptions (ModDB, Cameo wiki) for historical faction rosters.

### 2.2 What could not be read remotely, and the remedy

GitHub disallows automated crawling of `/tree/` file listings, and this analysis environment has no ability to `git clone`. Therefore the *exhaustive* actor-by-actor listing (every wrong inherit, every misnamed file, every orphaned weapon) must be generated on a local checkout. **This is not a gap in the plan — it is step one of the plan.** Appendix A contains ready-to-run scripts that produce those exact lists deterministically, which is strictly better than a one-time manual enumeration, because they can run in CI forever. An AI agent with repo access should run `tools/audit/run_all.sh` (Appendix A) as its very first task and commit the output to `docs/audit/baseline/`.

### 2.3 Known repository facts used throughout **[VERIFIED]**

| Fact | Evidence |
|---|---|
| SDK-style layout: `mods/cameo/`, `OpenRA.Mods.CA/`, `OpenRA.Mods.Cameo/`, `ops/`, `packaging/`, `tools/` | Repo root |
| Two custom C# trait DLLs: `OpenRA.Mods.CA` (Combined Arms lineage) and `OpenRA.Mods.Cameo` | Repo root, `mod.config` |
| Engine dependencies: `OpenRA.Mods.Cnc.dll`, `OpenRA.Mods.D2k.dll`, `OpenRA.Mods.AS.dll` (Attacque Supérior), custom engine fork with upstream syncs ("pulling 300+ commits from main OpenRA repository", TB15) | `mod.config`, TB15 notes |
| Language split: C# 78.8%, Python 6.7%, Fluent 6.5%, Lua 4.2%, Shell 2.0% | GitHub language stats |
| `CLAUDE.md` exists but contains only a 3-line memory-file instruction | File contents |
| 2,605 commits, 17 open PRs, 64 releases, active near-daily playtest cadence | Repo metadata |
| MiniYAML validation exists via `utility --check-yaml` (Test-Command in `make.ps1`) | Build scripts |
| Public tournament scheduled July 2026 for the "Cameo 1.0 prototype" | TB16 notes |

---

## 3. Repository architecture today (as-is assessment)

### 3.1 What is already good

- **Standard OpenRA SDK skeleton.** Anyone who has modded OpenRA can find their way around; `make`, `launch-game`, `utility` all behave as expected. Keep this.
- **Custom traits are split into two DLLs.** `OpenRA.Mods.CA` carries battle-tested Combined Arms traits; `OpenRA.Mods.Cameo` carries Cameo-specific ones. This separation is healthy — CA can be periodically re-synced from its upstream without touching Cameo-specific code.
- **Fluent localization is real** (6.5% of the repo) — most mods never get this far. The new Spanish EVA for Latin Syndicate (TB16) shows the pipeline works.
- **The asset optimization pass (RAMpage build) established three concrete asset norms**: downscale sprites to engine-used resolution, trim transparent sprite borders, and standardize WAVs to mono/16-bit/22050 Hz. These must be codified as pre-commit checks (§11.4) so the 12 GB RAM problem can never regrow.
- **Upstream engine syncs are happening** (TB15). This is expensive but essential; §12 Phase 0 schedules them on a fixed cadence.

### 3.2 The structural problems

**P1 — The rules tree is organized by accident of history, not by faction. [INFERRED from verified leak bugs]**
When Nod's SAM Site and Obelisk can silently appear in CABAL's roster, and when fixing Yuri's Slave Miner requires discovering it inherited the *wrong* template, the practical cause is that rule files mix faction content, share concrete actors across factions, and have no ownership boundaries. There is no way to answer "which files define the Forgotten?" without grep archaeology. §10 and §12 Phase 1 fix this with a strict `rules/factions/<game>_<faction>/` layout where each faction folder is self-contained.

**P2 — Inheritance is used as a copy-paste-avoidance hack rather than as an architecture.**
Verified symptom set: wrong-inherit damage bugs (Slave Miner, Lunar Tiger), stale warhead inheritance (Forgotten), redundant selection-bounds declarations "cleaned up" in TB23, and a global selection-box scaling bug that could propagate "across most rule files" precisely *because* values were duplicated rather than centralized. The rulebook in §10.3 (actors inherit **only** from templates; never actor→actor; never across faction folders) is the single highest-leverage change in this report.

**P3 — mod.yaml is a monolith. [INFERRED]**
With this many factions, the manifest's rule/weapon/sequence include lists are enormous, load-order-sensitive, and the reason startup once peaked at 12 GB. The end-state (§12 Phase 5) is per-faction sub-manifests included by the master `mod.yaml`, which is the prerequisite for the dynamic faction loading you want.

**P4 — Institutional knowledge lives in Discord and changelogs, not in the repo.**
`CLAUDE.md` is 3 lines. There is no `docs/` describing faction designs, balance philosophy, or the template system. For a project explicitly intending AI agents to do heavy lifting, the repo itself must be the knowledge base. §11.6 and Appendix C fix this.

**P5 — Balance is being tuned through stacked global multipliers.**
TB18 alone: all infantry +10% armor and firepower; scout & AT infantry +10% firepower *on top*; grenadiers/snipers +20% *on top*; support vehicles +10%/+10%; flying infantry −50% firepower, −25% range; TB19: all tanks +5% armor; TB22: scout damage multiplier 0.6→0.5; RAMpage: all MBT ranges normalized. Each change is individually reasonable, but multiplicative layers on top of per-unit values make it impossible to know a unit's *actual* stats by reading its YAML. §7.4 and §8 propose making the template layer the single place where class-wide stats live, with per-unit YAML expressing only *deltas with a comment justifying them*.

---

## 4. Bug & inconsistency catalog

Every class below has (a) verified evidence from your own recent builds, (b) the systemic root cause, and (c) an automated detector in Appendix A. The goal is that a class, once fixed, can never regress.

### B1 — Cross-faction actor leaks **[VERIFIED]**
*Evidence:* "Removed duplicate Nod units (SAM site, Obelisk) that had leaked into CABAL's roster" (TB23).
*Root cause:* CABAL's buildables were derived from Nod files (copy or inherit) and Nod-owned actors remained reachable through CABAL prerequisites/queues.
*Where else to expect it:* Every faction bootstrapped by copying a sibling: TS Nod↔CABAL, TD↔TS GDI, RA1↔RA2 Allies/Soviets, Dune houses (shared `d2k` heritage), any faction cloned from another at birth. Also check *support powers* and *defense tabs*, not just unit queues.
*Detector:* `audit_faction_leaks.py` — builds the buildable set per faction from prerequisites/queues and flags actors whose owning folder ≠ producing faction.

### B2 — Wrong / stale inherits changing combat stats **[VERIFIED]**
*Evidence:* Yuri Slave Miner "Weapon damage fixed (was too high from a wrong inherit)" (TB22); Lunar Tiger, same wording (TB22); "a stale warhead inheritance" in Forgotten (TB23).
*Root cause:* Actor→actor and cross-file inherits mean a retune of unit A silently retunes units B…N that nobody remembers inherit from it.
*Detector:* `audit_inherits.py` — flags (1) any `Inherits` target that is not a `^Template`, (2) any inherit crossing faction folders, (3) inherit chains deeper than 3, (4) inherits of removed/renamed parents (dangling).

### B3 — Upgrades with inverted or dead effects **[VERIFIED]**
*Evidence:* "Fixed Dark Armament upgrade making reload *slower* instead of faster" (TB23); WarCraft upgrades not appearing in the research menu at all (TB17); Chromium Ion Plating / Prismatic Barrier preventing units from firing their ability (TB20).
*Root cause:* Multiplier semantics in OpenRA are unintuitive (a reload multiplier above 100 means *slower*), and there is no test asserting the *direction* of an upgrade's effect.
*Detector:* `audit_upgrades.py` — for every upgrade-granted condition, resolve affected traits and assert direction against a small manifest (`upgrades_intent.yaml`, e.g. `dark_armament: reload: faster`). Also flags upgrades granting conditions **no actor consumes** (dead upgrades) and conditions consumed but **never granted** (dead wiring).

### B4 — Upgrade coverage gaps **[VERIFIED]**
*Evidence:* "Extended upgrade coverage to 9 previously-uncovered units, including both attack helicopters" (CABAL, TB23); Pulse/Quantum upgrades retroactively extended to Cargo Ship, White Rabbit, Sky Hammer, Megalodon (RAMpage build).
*Root cause:* Roster-wide upgrades are implemented as per-actor condition hooks; new units get added without the hook.
*Detector:* `audit_upgrade_coverage.py` — for each faction upgrade tagged `roster-wide` in `upgrades_intent.yaml`, diff the faction's buildable roster against actors carrying the hook; print the uncovered set. Run in CI so adding a unit without coverage fails the build.

### B5 — AI wiring drift **[VERIFIED]**
*Evidence:* "Fixed: AI never built a Helipad or any aircraft (wrong building reference in ai.yaml)" (Forgotten, TB23); "Wired CABAL's units/upgrades into the AI's build list" (TB23); historical "XCOM … doesn't have working AI".
*Root cause:* `ai.yaml` is hand-maintained and references actor IDs by string with no validation.
*Detector:* `audit_ai.py` — every actor ID in ai.yaml must exist; every *buildable* actor of a tournament-pool faction should appear in at least one AI squad/build list (warning otherwise); prerequisites referenced by the AI must be producible by that faction.

### B6 — Broken art/sequence references **[VERIFIED]**
*Evidence:* "Fixed Robot Tank's promotion icon pointing at a nonexistent sprite" (TB23); "Fixed a lot of sequences so they are displayed correctly" (TB17); "Visceroid sequence" fix (TB23); "Fix pale/dim unit coloring across various factions" (TB21).
*Detector:* `audit_sequences.py` — cross-check every `Image:`, sequence name, cameo/icon reference against sequences yaml and packaged assets; list missing and orphaned entries. (`utility --check-yaml` catches some; this catches icon/chrome references too.)

### B7 — Copy-paste metadata rot: tooltips, classes, names, flags **[VERIFIED]**
*Evidence:* "Fixed mislabeled tooltips (Tech Center/CABAL Core both said 'Radar')" (TB23); "TKM flag fixed" (TB23); faction-name drift "Consortium" vs "Steel Consortium" within your own release notes (TB21 vs TB22); a unit "class" taxonomy applied ad hoc ("Class changed from Main Battle Tank to Line Breaker") without a canonical class list.
*Detector:* `audit_metadata.py` — flags duplicate Tooltip names within a faction, actors missing Fluent keys, and unit classes not present in a canonical `unit_classes.yaml`.

### B8 — Crash-on-use content **[VERIFIED]**
*Evidence:* CABAL Hunter-Seeker power crashed ruleset loading (TB23); "a unit-data typo that crashed the game the first time a Runner Shotgal was produced" (TB23); Naxis Slave Master crash (TB19); historical cursors.yaml indentation crash.
*Root cause:* Content that only fails when *exercised* — `--check-yaml` passes but the first production/power use crashes.
*Detector:* smoke tests (§11.5): headless bot-vs-bot per tournament faction on every PR, plus a Lua test map that force-spawns every buildable actor and fires every support power once. The single most valuable CI investment for a project that describes itself as crash-prone.

### B9 — Systemic numeric drift **[VERIFIED]**
*Evidence:* "Fixed a systemic selection-box scaling bug across most rule files (many units' click/decoration bounds were ~42x too large)"; "Cleaned up redundant selection-bounds declarations" (TB23).
*Root cause:* a scale convention changed at some point and hand-copied values never followed. Any constant duplicated hundreds of times will drift.
*Detector:* `audit_outliers.py` — statistical outlier scan across all numeric fields grouped by trait/field (flag values far outside the field's distribution). This is how you find the *next* 42× bug before players do.

### B10 — Dead content: orphaned weapons, warheads, actors, art **[INFERRED — near-certain at this scale]**
Every removal ("Removed duplicate Nod units…") tends to leave weapons/warheads/sequences behind. Dead content costs RAM (your scarcest resource), load time, and agent confusion.
*Detector:* `audit_orphans.py` — reference-count every weapon, warhead template, condition, sequence and image from the resolved ruleset; list zero-reference entries. Review before deleting (maps/Lua may reference some — the script also greps `maps/` and Lua).

### B11 — Asset format regressions **[VERIFIED as fixed once]**
The RAMpage norms (downscaled sprites, trimmed borders, mono 16-bit 22050 Hz WAV) will silently regress the first time someone drops in a raw 4K sprite sheet or a stereo 44.1 kHz WAV.
*Detector:* `audit_assets.py` in pre-commit/CI — reject oversized PNGs (per-category max dimensions), untrimmed alpha borders beyond a threshold, and non-conforming WAVs; print the exact conversion command to fix each file.

### B12 — Localization drift **[INFERRED]**
With Fluent at 6.5% of the repo and content added weekly, new actors will lack Fluent keys and renamed actors will strand old keys.
*Detector:* `audit_fluent.py` — diff actor/upgrade/power IDs against Fluent message keys; list missing and orphaned keys per locale.

### Priority order for burning these down
1. **B8** (crashes) — player-facing trust; blocks the tournament.
2. **B2 + B1** (inheritance + leaks) — root cause of most other classes; fixed structurally in §10 / §12 Phase 1.
3. **B5** (AI wiring) — a faction the AI can't play is effectively untested content.
4. **B3 + B4** (upgrade correctness/coverage) — balance integrity.
5. **B6, B7, B9** — quality-of-life; heavily automatable, ideal AI-agent work.
6. **B10, B11, B12** — hygiene; recurring maintenance.

---

## 5. Faction roster and the source of truth

### 5.1 The authoritative list must be generated, not written

The real roster is defined by `mods/cameo/mod.yaml` → the rules it includes → the `Faction@` definitions in the player/world rules. Because that list changes weekly, this report mandates a *generated* artifact instead of a hand-written one:

- Add `tools/audit/gen_faction_matrix.py` (Appendix A) producing `docs/factions/MATRIX.md`: for every faction — internal ID, display name, universe/game of origin, selectable?, in Random pool?, in Tournament pool?, owning rules folder(s), unit count, upgrade count, AI support (yes/partial/no), Fluent coverage %.
- CI regenerates it on every merge; the file doubles as the AI agent's map of the game.

### 5.2 Roster as evidenced by releases and project material **[VERIFIED names; grouping partly INFERRED]**

- **C&C Tiberian Dawn:** GDI, Nod.
- **C&C Tiberian Sun:** GDI (TS), Nod (TS), **CABAL**, **Forgotten** (new in TB23; added to Random/Tournament pools).
- **Red Alert 1:** Allies, Soviets.
- **Red Alert 2 era:** Allies (RA2), Soviets (RA2), **Yuri** (plus country subfactions historically).
- **Cameo-original / expanded-universe:** **Steel Consortium** (a.k.a. "Consortium" — see B7), **FutureTech**, **Schwarzer Mond**, **Latin Syndicate**, **Asian Alliance**, **Empire of Japan**, **Naxis**, **TKM**.
- **Dune 2000:** Atreides, Harkonnen, Ordos; Ixian technology present (Ixian superweapon, TB15); Arrakis tilesets + map generator.
- **StarCraft:** Terran, Zerg, Protoss (reintroduced/reworked; Adept added TB18; Shade/Arbiter abilities TB23).
- **WarCraft 2:** Humans, Orcs (upgrade research fixed TB17; sprites rescaled TB16).
- **Legacy/exotic (historically present; verify current status via MATRIX.md):** SimCity, Scavengers, Alpha (Warzone 2100), XCOM, Star Wars (Rebels/Republic/CIS), Advance Wars commanders, Hero Portal heroes, Zombies/Ants event factions.

A strategic question the matrix will force you to answer explicitly: **which factions are Tier-1 (tournament-supported, fully balanced, AI-complete), Tier-2 (playable, best-effort), and Tier-Legacy (parked)?** Publishing that tiering (§12 Phase 0) is free and immediately improves player expectations and contributor focus. "191 factions" is a liability if all of them implicitly promise tournament quality; it is a superpower if 15–20 are gold-standard and the rest are honestly labeled.

---

## 6. Faction-by-faction design & balance analysis

**How to read this section.** For each faction: *Identity* (what should make it unique), *Early / Mid / Late* power assessment, *Verified issues*, and *Direction* (design + balance suggestions). Power ratings use a 1–5 scale per phase and are **[HYPOTHESIS]** unless tied to a verified changelog fact — they encode the archetype each faction occupies plus the trajectory visible in your own patch notes, and they exist to be *falsified by the telemetry pipeline in §8.5*. Treat them as the starting priors for the first balance league, not as gospel.

A phase definition used throughout (align these with in-game timers once telemetry exists):
- **Early** = first ~6 minutes: 1 production structure, tier-1 units, first harass.
- **Mid** = ~6–15 min: tier-2, first upgrades, radar-level powers, 2nd economy.
- **Late** = 15+ min: full tech, superweapons, epic units, stacked upgrades/promotions.

### 6.1 C&C Tiberian Dawn

**TD GDI** — Identity: straightforward combined arms, medium tanks + air support, "the baseline faction."
Early 3 / Mid 3 / Late 2–3.
*Verified:* Boxer cost 1100→1550 with +50% firepower (TB18) — pushed from spam unit to elite pick, correct direction.
*Direction:* As the game's de-facto benchmark faction, GDI should be deliberately kept at "power level 100" and every other faction tuned against it (§8.2). Its late game needs one distinctive capstone beyond the Ion Cannon so it doesn't merely lose to factions with stacked late-game upgrades — lean into the "orbital support" fantasy (targeted mini-strikes, drop-pod reinforcements) rather than raw stats.

**TD Nod** — Identity: speed, stealth, hit-and-run, terror weapons.
Early 4 / Mid 3 / Late 2.
*Direction:* Classic Nod problem in every C&C: excellent harass curve, falls off when opponents field massed armor. Keep it — Nod *should* be a "win by 15 minutes or bleed them dry" faction — but make late-game viability come from stealth-tech force multipliers (cloaked repair, ambush bonuses) rather than giving it a conventional heavy tank, which would blur it into GDI.

### 6.2 C&C Tiberian Sun

**TS GDI** — Identity: walkers, sensor tech, EMP; slow, methodical, premium units.
Early 2 / Mid 4 / Late 4.
*Verified:* rocket weapon types did more damage than intended, fixed TB18 — i.e., its mid-game was recently overperforming.
*Direction:* Its early game should be protected by defensive tools (component towers, cheap Wolverine harass-defense) rather than buffed offensively; the weak early phase is the fair price of Titans/Mammoth MK2 later.

**TS Nod** — Identity: subterranean warfare, lasers, cyborgs, mobility trickery.
Early 4 / Mid 3 / Late 3.
*Verified:* SAM prerequisite bug fixed TB23 (its AA had a broken unlock — a real matchup-warping bug against air factions until then).
*Direction:* Subterranean APC timing attacks are its signature; make sure every other Tier-1 faction has *some* detection/answer by mid game (audit via §8.4 counter matrix) or this becomes a coin-flip faction in tournaments.

**CABAL** — Identity: cybernetic autonomy — units that don't rout, drone-swarm logistics, the "AI plays an AI" faction.
Early 2 / Mid 3 / Late 4 (rising).
*Verified:* just received a full normalization pass in TB23 — research tier matching GDI/Nod, Obelisk of Darkness moved to radar unlock, inverted Dark Armament fixed, 9 units added to upgrade coverage, Nod leaks removed, AI wiring added. This was the report's methodology applied to one faction, and it's the model to replicate.
*Direction:* CABAL's uniqueness should be *automation*: self-repairing structures, units that gain power when networked near each other (the new Networked Combat Protocols upgrade is the perfect seed — extend it into the faction's core mechanic: proximity/network bonuses instead of a hero unit). Watch late-game: promotions + research + roster-wide upgrades now stack three multiplier systems (§7.4 risk).

**Forgotten** — Identity: mutant scavengers, terrain-native (Tiberium immunity/healing), irregular warfare.
Early 3 / Mid 3? / Late ? — brand new (TB23), data needed.
*Verified:* shipped with a big roster (Ghost Stalker, Mutant Hijacker, Reaper variants, Locust Bomber…), a 3-tier Radar→Lab→rank-gated upgrade economy, and immediately needed fixes (crash typo, stale warhead, AI helipad).
*Direction:* The hijacker + scavenging identity is gold for a *crossover* game: the Forgotten can be the faction whose late game is literally "your units, stolen." Lean into capture/salvage as the win condition and keep their own top-tier units modest. Their Tiberium-field advantage must be tuned per-map (maps without heavy Tiberium neuter them — flag such maps out of their tournament pool or give a fallback economy).

### 6.3 Red Alert 1

**RA1 Allies** — Identity: intel + precision (GPS, spies, Chronosphere), naval strength, cheap fast tanks.
Early 3 / Mid 3 / Late 3.
**RA1 Soviets** — Identity: brute force, heavy armor, Tesla, air dominance.
Early 2 / Mid 4 / Late 3.
*Verified:* Soviet Mammoth secondary weapon fixed to target ground (TB15) — a quiet but significant mid-game buff.
*Direction:* RA1's danger in a crossover is being a strictly-worse RA2: same archetypes, fewer toys. Differentiate on *tempo*: make RA1 the leanest, fastest-teching pair in the game (cheapest tier costs, fastest build times, but a hard ceiling — no late-game upgrade stacking). That gives them a tournament niche (punishing greedy factions) instead of being nostalgia picks.

### 6.4 Red Alert 2 era

**RA2 Allies** — Identity: technology and trickery — Prism, Chrono, Mirage, spies, air mobility.
Early 3 / Mid 4 / Late 4.
*Verified:* Chromium Ion Plating / Prismatic Barrier upgrades were blocking ability fire (fixed TB20; condition retuned) — their late-game upgrade layer is actively evolving.
**RA2 Soviets** — Identity: overwhelming armor + Tesla attrition; Kirov finisher.
Early 3 / Mid 4 / Late 4.
*Verified:* Tesla Armor discharge nerfed 50% dmg, range 6.6→4.5 (TB20) — evidence it was warping mid-game engagements. Sabot rounds rebalanced (TB23), Flak Track buffed (TB23).
**Yuri** — Identity: mind control, economy parasitism (Slave Miner, Grinder), denial.
Early 2 / Mid 4 / Late 5 (historically the balance problem child in every RA2 environment).
*Verified:* Slave Miner nerfed hard in TB22 (300k→200k HP, armor rework, damage fixed from wrong inherit) — consistent with Yuri overperformance.
*Direction:* Mind control scales terrifyingly in a game where enemy units can be *any* faction's units. Cap simultaneous controlled units, make epic/hero units immune-by-class (define it once in the class taxonomy, §9.4), and price Mastermind-type units against the *best* stealable roster, not the average one. Yuri is the faction most likely to create cross-universe degenerate combos — give it a standing line-item in every balance pass.

### 6.5 The Cameo-original bloc

These are your crown jewels — the factions no other game has — and the changelogs show they get the most love. That's correct, but it creates a *fairness optics* problem: three of the last five builds shipped Steel Consortium buffs/content.

**Steel Consortium** — Identity: high-tech mercenary industry — pulse/quantum tech, heavy air (Sky Hammer, Cloudbreakers), elite heroes (Stalker, White Rabbit, Steel Runner).
Early 2 / Mid 3 / Late **5 — watch closely**.
*Verified:* In three consecutive builds it gained: four new upgrades (Pulse Rifles, Nanite Infusion, Ferrocrete Curtain, Resonance Ammo — TB21), a new anti-ground-and-air hero with ricochet lasers (Steel Runner), a Sky Hammer rework to no-ammo + more damage at 4500 cost, Quantum/Pulse coverage extended to more units (RAMpage), then Manta HP doubled, Stalker/White Rabbit made tankier, Stalker added to Quantum coverage (TB22). Individually justified; cumulatively this is the strongest late-game upgrade suite in the game's recent history.
*Direction:* Freeze Consortium buffs for two builds and gather tournament data. Its counterweight should be *cost and fragility of tempo*: expensive everything, weak map control early. If telemetry confirms late dominance, tune by raising upgrade prices/research times rather than nerfing unit stats (preserves feel). Also: settle the name — `steel_consortium` everywhere (B7).

**FutureTech** — Identity: experimental prototypes, drones/striders (Droid/Armor/Strider promotion chains added TB23).
Early 2 / Mid 3 / Late 4.
*Direction:* Its uniqueness overlaps with Steel Consortium ("high-tech toys"). Sharpen the split: FutureTech = *prototype gambit* faction (few, weird, rule-breaking units; promotion-driven), Consortium = *industrial elite* (upgrade-driven, conventional-but-superior). Write both one-pagers (Appendix C) and prune units that violate the split.

**Schwarzer Mond** — Identity: lunar/occult exotics (Lunar Tiger, Daleks).
Early ? / Mid 3 / Late 4.
*Verified:* Lunar Tiger damage was wrong from a bad inherit (TB22); Dalek lost anti-air (TB22).
*Direction:* Needs a design one-pager most of all — from the outside its identity reads as "cool units we had," which is exactly what §12 Phase 3 exists to fix.

**Latin Syndicate** — Identity: guerrilla economy — smoke, rushes, cheap mixed forces, stolen tech.
Early 4–5 / Mid 3 / Late 2–3.
*Verified:* soldier-cargo-in-tanks removed to force real combined arms; Rusher 850→650; Smoker rebalanced (RAMpage). Spanish EVA added (TB16) — great identity work.
*Direction:* The intended aggression curve is clear and healthy. Its late game should stay weak *but* its stolen-tech mechanic (historically present) should mature into the comeback lever — a Syndicate that survives to late game earns enemy tech. That's unique, thematic, and self-balancing.

**Asian Alliance** — Identity: amphibious/terrain-crossing warfare (underwater-cloaking Alligators, TB22).
Early 3 / Mid 3 / Late ?.
*Direction:* Own the water/terrain-denial niche completely — the only faction for whom coastlines are highways. On land-locked maps it needs a compensating mechanic or map-pool flagging (same issue class as Forgotten's Tiberium dependency; solve both with one "terrain-dependency" metadata field per faction consumed by the map/tournament tooling).

**Empire of Japan** — Identity: transformation/tempo (RA3 lineage), promotion-gated elites.
Early 4 / Mid 3–4 / Late 3.
*Verified:* Shrine Minitank added as promotion-unlocked T2 harasser; Bomber normalized to regular unit (RAMpage).
*Direction:* Healthy. Its differentiator should be *unit transformation and tempo choices*, not raw stats.

**Naxis / TKM** — Identity unclear from public material; both recently needed fixes (Slave Master crash TB19; TKM flag TB23).
*Direction:* Candidates for Tier-2 until each has a one-pager, AI wiring, and upgrade coverage. Don't let half-integrated factions into the Random pool — they become the game's worst first impression.

### 6.6 Dune 2000 (Atreides, Harkonnen, Ordos + Ixian tech)

Early: Ordos 4 / Atreides 3 / Harkonnen 2. Mid: 3/3/4. Late: 2–3 / 3 / 4.
*Verified:* Ordos Raider reworked into faster, tankier buggy with new weapon (TB23); Dune MCV facing and type-select-exclusivity fixes (TB21); Arrakis map generator + sandstorm weather (TB15).
*Direction:* The Dune trio's shared uniqueness is *the environment*: spice-only economy, worm danger, terrain rules. Make that the headline — on Arrakis maps they're at home while others fear the sand; off Arrakis they operate with a compact, disciplined roster. House identities: Atreides = air + allies (Fremen), Harkonnen = heavy + devastating (Devastator, Death Hand), Ordos = speed + deception (stealth raiders, Deviator conversion — note the Deviator/Yuri overlap: differentiate by making Deviation *temporary* control only). Ixian superweapon/tech should become a shared neutral tech lab on Arrakis maps rather than one house's toy — instant map-level drama.

### 6.7 StarCraft (Terran, Zerg, Protoss)

Early: Zerg 4 / Terran 3 / Protoss 2. Mid: 3/3/4. Late: 4/3/4.
*Verified trajectory:* Protoss received sustained attention — historical rebalance (Dragoon +50% HP, High Templar 1400→800 rework, Reaver 3000→1600 + HP up) and current additions (Adept TB18; Shade + Arbiter recall abilities TB23; AI uses Shade).
*Direction:* This trio's crossover challenge is *economy-model mismatch*: SC factions were designed around worker-based mining and supply. Whatever adaptation you've made, the design principle should be: **preserve the fantasy, adapt the numbers.** Protoss = few, expensive, shielded (shields must be a real second HP layer with EMP/anti-shield interactions defined vs every universe's weapons — a perfect table for `docs/design/damage_model.md`); Zerg = mass + regeneration + creep-as-territory; Terran = positional (bunkers pre-loaded — verified historical change — siege lines, repair). Zerg's larva/queue adaptation determines their entire balance; document it explicitly so tuning isn't folk knowledge.

### 6.8 WarCraft 2 (Humans, Orcs)

*Verified:* upgrades only recently became researchable at all (TB17 — meaning both factions played *without their upgrade layer* for some time, so any pre-TB17 balance impression of WC2 is invalid); sprites rescaled (TB16).
*Direction:* Fantasy-melee factions in a gunpowder crossover need a survivability rule for closing distance (damage reduction vs small arms while charging, or cheap massed HP). Their magic layer (Ogre-Magi, Death Knights, Paladins) is their ranged equalizer — treat spells as this pair's "upgrade economy" and balance mana costs like ammo. Early 4 (rush) / Mid 2 / Late 2 until proven otherwise — they're the pair most likely to need structural help rather than number tweaks.

### 6.9 Legacy/exotic bloc (SimCity, Scavengers, Alpha/WZ2100, XCOM, Star Wars, Advance Wars, Heroes)

Recommendation: formally park these as **Tier-Legacy** (excluded from Random/Tournament pools, labeled "Experimental" in the lobby) until each passes the Definition of Done (Appendix D). SimCity-as-support-AI is a genuinely novel co-op idea worth reviving *as a game mode*, not a ladder faction.

### 6.10 Cross-cutting balance findings

1. **The Consortium-family late game is the current outlier risk** (three builds of compounding buffs) — freeze and measure. **[VERIFIED trend / HYPOTHESIS on magnitude]**
2. **Global class multipliers are drifting upward** (infantry +10%, tanks +5%, support +10% within two builds) — power inflation that quietly devalues untouched factions (WC2, legacy bloc). Establish the GDI-100 benchmark (§8.2) before any further global changes.
3. **Air balance is being tuned by hammer blows** (flying infantry −50% firepower; helicopter build-time modifier 50→75) — symptoms of missing per-faction AA guarantees. Adopt the rule: *every Tier-1 faction must have accessible AA at tier 1.5 and mobile AA at tier 2*, then re-tune air units against that guarantee instead of nerfing them globally.
4. **Faction dependencies on map features** (Forgotten↔Tiberium, Asian Alliance↔water, Dune↔Arrakis) need first-class metadata so tournament map pools can be validated automatically.
5. **Mind control / conversion / hijack mechanics** (Yuri, Deviator, Mutant Hijacker) are the highest cross-universe combo risk in the game — one shared design doc with hard caps and immunity classes.

---

## 7. Upgrades, promotions & the power curve

### 7.1 The three stacking systems **[VERIFIED to coexist]**

Cameo currently has (at least) three orthogonal progression systems:
1. **Veterancy/promotions** — expanded from 8 to 11 ranks with a smoother XP curve (TB23); per-unit promotion trees with insignia UI (TB15), promotion-unlocked units (Shrine Minitank, Prospector MK2, Black Widow, FutureTech chains).
2. **Faction research/upgrade tiers** — cash-priced research (CABAL's new tier "matches GDI/Nod's tech tree"), Forgotten's Radar→Lab→rank-gated 3-tier economy, Consortium's upgrade suite, WC2 research, RA2 late-game upgrades (Chromium Ion Plating etc.).
3. **Global class templates** — the TB18/TB19 class-wide combat multipliers.

A unit's real strength = base × class template × research upgrades × promotion rank (× situational conditions). Four multiplier layers is fine *if* each layer is centrally defined and auditable; it is chaos if layers live scattered in per-actor YAML.

### 7.2 Rules for a sane power curve

- **R1: One source of truth per layer.** Class multipliers live only in `templates_combat.yaml`; research effects only in the faction's `upgrades.yaml`; promotion effects only in `promotions.yaml`. An actor file may never restate a layer's value.
- **R2: Budget the total late-game multiplier.** Decide the maximum stacked multiplier a fully-upgraded, max-rank unit may reach relative to its fresh self — recommended **≤ 2.0× effective combat power** (damage × survivability). Anything above ~2× makes late-game armies unreadable and comebacks impossible. Add `audit_power_budget.py` (Appendix A) to compute worst-case stacks per unit and flag breaches.
- **R3: Price upgrades on ROI.** An upgrade's cost should approximate the credits-equivalent of the stat gain across the units it affects at the time it's available: `cost ≈ Σ(affected fielded value × % gain) × 0.6` (the 0.6 discount because you must survive the research time). Roster-wide upgrades (Nanite Infusion, Networked Combat Protocols) must be priced against *late* rosters, not the roster size at unlock.
- **R4: Every upgrade has an intent line.** `upgrades_intent.yaml` (B3/B4 detectors feed on it) records direction, coverage tag, and phase (early/mid/late). This file is one line per upgrade and pays for itself the first time it catches another Dark Armament.
- **R5: Promotions grant *options*, research grants *stats*.** Keep the two systems feeling different: ranks unlock abilities/units (Shrine Minitank is the model), research raises numbers. Where both raise numbers, players can't attribute power and balancing becomes guesswork.

### 7.3 Phase-power targets per faction

Adopt an explicit curve declaration in each faction one-pager: e.g. Latin Syndicate `E5/M3/L2 + comeback-mechanic`, TS GDI `E2/M4/L4`, Consortium `E2/M3/L5-capped`. The tournament telemetry (§8.5) then measures actual win probability by game-length bucket and diffs it against the declared curve. Balance work becomes "make reality match the declaration or change the declaration" — a tractable loop instead of vibes.

### 7.4 Immediate power-curve action items

1. Compute the worst-case stacked multiplier for: Consortium Sky Hammer + Quantum + promotions; CABAL post-TB23 full stack; any RA2 Allied unit with Chromium Ion Plating + Prismatic Barrier + max rank. **[These three are the likeliest current breaches of R2.]**
2. Re-express the TB18/TB19 global changes as named template values with comments, deleting any per-actor restatements found by `audit_outliers.py`.
3. Write `upgrades_intent.yaml` for the Tier-1 factions (roughly an afternoon of work, mostly transcribing changelogs).

---

## 8. Balance methodology going forward

### 8.1 The counter-triangle contract
Define once, globally: Infantry ↔ Vehicles ↔ Aircraft plus armor classes (None/Flak/Plate/Light/Medium/Heavy/Concrete/Hero — you already use hybrid armors like "Hero+Medium", TB22, and combination armors like the Slave Miner's "Heavy and Concrete"). Publish the full damage-vs-armor matrix in `docs/design/damage_model.md` and generate it from the actual warhead YAML (script in Appendix A) so the doc can never lie.

### 8.2 The GDI-100 benchmark
Pick TD GDI as the reference. Define reference engagements (equal-cost army A vs army B on flat ground) and compute cost-normalized effectiveness for each faction's core roster at each phase using a headless-sim harness (OpenRA supports headless runs; a Lua harness that spawns armies and reports survivors is ~200 lines). Every balance PR must include the harness diff for touched units. This converts "Manta HP 27500→55000" from a guess into "Manta cost-efficiency vs reference AA moves from 0.71 to 0.98."

### 8.3 Matchup matrix
With ~15–20 Tier-1 factions there are ~150–190 matchups; nobody can hand-balance that. Balance to *archetypes* instead: rush, tempo, tech, swarm, fortress, economy, denial. Each faction declares its archetype(s) in its one-pager; you balance the 7×7 archetype matrix and then verify per-faction outliers with data.

### 8.4 Hard guarantees every Tier-1 faction must satisfy (checklist, CI-enforceable where marked)
- Tier-1 AA and mid-game mobile AA exist (CI: roster query).
- Detection for stealth/subterranean/underwater by mid game (CI).
- At least one anti-heavy-armor line (CI).
- A harass answer at early game (design review).
- Comeback lever OR declared as a "close-out" faction in its curve (design review).
- AI can build every roster unit (CI: audit_ai).
- All roster-wide upgrades cover the full roster (CI: audit_upgrade_coverage).

### 8.5 Telemetry
The July tournament is a data goldmine: collect per-game faction pick, map, duration, winner, and (if feasible via replay parsing) units built. Even a spreadsheet of 200 tournament games gives you win-rate-by-faction-by-duration — the single most important balance chart. A replay-parsing script belongs in `tools/telemetry/` (OpenRA replays are parseable; start with outcome+duration+factions which is trivial, expand later).

### 8.6 Balance change hygiene
- One faction's numbers per PR (mod-wide template changes are their own PR type with mandatory harness report).
- Changelog entries auto-generated from YAML diffs (`tools/gen_changelog.py`) so notes like "damage fixed (was too high)" always carry exact numbers.
- A `balance/` label + two-build cooldown rule: a faction buffed in build N is frozen in N+1 unless a crash/exploit is involved (this rule alone would have caught the Consortium compounding pattern).

---

## 9. Actor & file naming scheme (specification)

### 9.1 The grammar

The baseline is the scheme RA1 Soviet content already uses (`ra_commissar`,
`ra_grad`, `ra_upgrade_autoloaders`, `ra_promotion_superoptics`,
`ra_doctrine_conscription`): a faction prefix plus the name — **no structural
type word in unit ids**. A type marker appears only on tech-tree items
(upgrades / promotions / doctrines).

```
unit/building id :=  [game_]faction_name[_variant]
tech item id     :=  [game_]faction_(upgrade|promotion|doctrine)_name
file name        :=  same as the asset's owning actor id, plus suffixes
icon file        :=  <actor_id>_icon.<ext>
```

- **`game`** — required ONLY when the same faction name exists in multiple source games. Registry of game prefixes (fixed, lowercase): `td`, `ts`, `ra1`, `ra2` (+ future prefixes as collisions appear). Examples: `td_gdi_*` vs `ts_gdi_*`; `ra1_soviets_*` vs `ra2_soviets_*`. Every faction that exists once (yuri, cabal, forgotten, steelconsortium, futuretech, schwarzermond, latinsyndicate, asianalliance, japan, naxis, tkm, atreides, harkonnen, ordos, ixian, terran, zerg, protoss, humans, orcs…) omits the game prefix; a prefix is added the day a collision actually appears, not preemptively.
- **`faction`** — the canonical faction slug from the registry (§9.2). Never abbreviate ad hoc; never two spellings (this kills the Consortium/Steel Consortium drift — use full words, `steelconsortium`; abbreviations are how drift starts).
- **`upgrade|promotion|doctrine`** — full words, only on tech-tree items: `upgrade` for cash research, `promotion` for rank-gated unlocks, `doctrine` for mutually-exclusive doctrine picks. Team-proxy dummies append `_proxy_actor` (existing RA1 convention).
- **`name`** — the unit's display-ish name as ONE lowercase group without separators (RA1 baseline: `heatraytank`, `nuclearshells`): `titan`, `slaveminer`, `skyhammer`, `ghoststalker`.
- **`variant`** — optional: `_mk2`, `_elite`, `_husk`, `_water` (movement variants), `_ai` (AI-only variants — historical "Special Bot variants" should be explicit), `_sp`, `_r4`, `_wild`, `_EMP` (EMP weapons), `_AA` (anti-air weapons), `_upgraded` (upgrade variants), plus dotted variants (`.husk`) and paradrop twins (`para`). See DESIGN.md §1 for the full list.
- **Tooltip consistency** — the id's name group derives from the Tooltip Name and both must stay in sync: when an id is disambiguated, the Tooltip is renamed too, so no two actors of a faction share a display name (audit_metadata M1 enforces). New display names are a design decision — propose options and let design pick (e.g. the blue Tiberian Fiend became "Vinifera Fiend"). Shared cross-actor namespaces (voice sets, shared sprites) are never renamed with a unit; tools/rename/safe_rename.py protects audio files and VoiceSet lines.

**Examples**
```
ts_gdi_titan                ts_gdi_titan_husk
ts_nod_obelisk              cabal_obeliskofdarkness
yuri_slaveminer             steelconsortium_skyhammer
forgotten_ghoststalker      ra2_allies_upgrade_chromiumionplating
protoss_adept               ordos_raider
cabal_upgrade_darkarmament  forgotten_promotion_bowler
```
Icons: `ts_gdi_titan_icon.png`. Portraits/cameos, if distinct from icons: `_cameo`. Build palettes/other per-actor art keep the actor id as stem.

### 9.2 The faction slug registry
Create `docs/design/faction_registry.yaml` — the single authority mapping `slug → display name, game prefix, tier, terrain-dependency, archetypes`. Every tool (naming lint, matrix generator, leak audit) reads it. Rule: **a faction slug appears in exactly one place in the repo as a definition; everywhere else it is a reference.**

### 9.3 Shared and neutral content
- Cross-faction *templates* use the `^` MiniYAML convention and live only in `rules/templates/`: `^cameo_tank_medium`, `^cameo_production_building`.
- Truly shared concrete actors (crates, civilians, critters, husks-generic, map props) use the `neutral_` prefix: `neutral_rock_01`, `neutral_supply_truck` (the historical "every faction has Supply Truck & Engineer" content). Engineers/MCVs that are per-faction *skins* of shared behavior should be per-faction actors inheriting the shared template — not one shared actor with per-faction render hacks.

### 9.4 Tech-item markers & class vocabulary (closed lists, versioned)
Tech-item markers (the only type words that appear in IDs): `upgrade, promotion, doctrine` (+ `_proxy_actor` suffix for team proxies). Structural type words (`inf/veh/air/…`) do NOT appear in IDs — they remain internal audit-tool vocabulary only.
`class` (gameplay taxonomy, in YAML metadata not the ID — this is your "Main Battle Tank"/"Line Breaker" system): define `docs/design/unit_classes.yaml` with the canonical list and one-line definitions (e.g., `scout, rifle, at_infantry, sniper, grenadier, engineer, harvester, mbt, line_breaker, harass_buggy, artillery, aa_mobile, transport, epic, commando, support_caster…`). B7's audit enforces membership. Classes are what global template multipliers key off — which is why the list must be closed and reviewed.

### 9.5 File layout naming
```
mods/cameo/rules/
  templates/                     # ^Templates only — the ONLY legal Inherits targets
    core.yaml                    #   world/player/palette plumbing
    combat_classes.yaml          #   per-class combat templates (the TB18 layer lives HERE)
    structures.yaml  units.yaml  #   structural templates
  factions/
    ts_gdi/                      # one folder per faction slug
      manifest.yaml              #   this faction's include list (future dynamic loading)
      structures.yaml units_infantry.yaml units_vehicles.yaml units_aircraft.yaml
      defenses.yaml upgrades.yaml support_powers.yaml ai.yaml
    steel_consortium/ …
  neutral/                       # neutral_* actors, critters, props
  system/                        # queues, lobby options, game modes
weapons/   -> same faction-folder split; shared warhead templates in weapons/templates/
sequences/ -> same split; art files named per §9.1
```

### 9.6 Migration plan (this is the risky one — do it right)

Renaming actors breaks: map files (actor IDs are baked into every `.oramap`), Lua scripts, ai.yaml, Fluent keys, sequence image references, saved player hotkey/type-select behavior, and *replay compatibility* (acceptable to break between playtests; never mid-tournament).

1. **Freeze window.** Do renames only in a dedicated window between playtests, never mixed with balance changes.
2. **Build the map, once:** `tools/rename/rename_map.yaml` — old_id → new_id, generated per faction folder as it's migrated.
3. **Mechanical apply:** `tools/rename/apply.py` _(now deprecated; replaced by `tools/rename/safe_rename.py` — see MIGRATION.md)_ rewrites rules/weapons/sequences/ai/Fluent + renames asset files (`git mv`) + rewrites every map in `maps/` (unpack `.oramap` zips, string-replace actor IDs in `map.yaml`/binary where applicable, repack) + Lua scripts. Everything in one commit per faction.
4. **Compatibility shim (temporary):** OpenRA supports rule aliasing poorly, so instead keep a `legacy_aliases.yaml` consumed by a small custom trait/utility update rule that maps old→new when loading *third-party* maps; drop it at 1.0.
5. **Verify:** full audit suite + smoke tests + load every shipped map headlessly.
6. **Order:** migrate faction-by-faction, starting with the *newest, cleanest* faction (Forgotten — likely already close to compliant) to bed in the tooling, then one faction per build. Do **not** attempt a big-bang rename of the whole tree.

---

## 10. Template & inheritance architecture

### 10.1 Why templates, precisely
Your stated goal — dynamically loadable, independent factions — has one hard requirement: **a faction folder's rules may reference nothing outside itself except `rules/templates/` and `rules/neutral/`.** Every current cross-faction inherit is a landmine for that goal (and, per B1/B2, already a live source of bugs).

### 10.2 The three-layer model
```
Layer 0  ^CoreTemplates        (engine plumbing: selectable, targetable, husk transforms…)
Layer 1  ^ClassTemplates       (per unit-class combat baselines — THE balance layer)
Layer 2  Faction actors        (concrete actors; deltas + flavor + faction mechanics only)
```
Faction-specific shared behavior (e.g., all CABAL units get Networked Combat Protocols hooks) is expressed as **Layer-1.5 faction templates living inside the faction folder** (`^cabal_unit_base`), which themselves inherit only from Layer 1.

### 10.3 The invariants (enforced by `audit_inherits.py`, non-negotiable)
1. Concrete actors never inherit from concrete actors — only from `^Templates`. *(Same-faction actor→actor inheritance is also banned, per project policy.)*
2. `^Templates` live in `rules/templates/` or in the owning faction's folder; a faction's actors may inherit only its own faction templates + global templates.
3. No `Inherits` may cross faction folders. Shared behavior gets promoted to a global template instead.
4. Inheritance depth ≤ 3 from actor to Layer 0.
5. `Inherits@` (named multi-inheritance) is preferred for mixins (e.g., `Inherits@Upgrades: ^cabal_upgrade_hooks`) so removals are grep-able.
6. `-Trait:` removals in an actor are a smell: if you must remove an inherited trait, the actor is inheriting the wrong template — create/choose a leaner template instead. Budget: ≤ 2 removals per actor, flagged in review above that.
7. A weapon/warhead follows the same rules within `weapons/`.

### 10.4 Refactor recipe per faction (repeatable unit of work — ideal AI-agent task)
1. Run audits; snapshot the faction's fully-resolved ruleset: `utility --check-yaml` + a resolver dump (Appendix A `dump_resolved.py`) → `before.json`.
2. Move all faction files into `rules/factions/<slug>/`; update mod.yaml includes.
3. Break every illegal inherit: replace with the correct template; where the template doesn't exist, extract it (from the *most canonical* current user, not from whichever actor happened to be the parent).
4. Apply naming migration (§9.6) for this faction.
5. Re-dump resolved ruleset → `after.json`; **diff must be empty** except for intended fixes (each intended diff line gets a changelog entry — this is how you find more Slave-Miner-style latent bugs safely: the diff *shows* you every stat that was silently wrong).
6. Smoke test; ship in the next playtest with a clear "no intended balance changes / fixed stats: X, Y" note.

The resolved-diff technique in step 5 is the crown move: it makes an inherently terrifying refactor *provably* behavior-preserving, and every non-empty diff line is a bug you just found.

---

## 11. Repository hygiene & contributor workflow

### 11.1 Directory layout (top level)
Keep the SDK skeleton; add:
```
docs/            MASTER_REPORT.md, design/ (one-pagers, damage model, registries), audit/baseline/
tools/audit/     all Appendix A scripts + run_all.sh
tools/rename/    §9.6 tooling
tools/telemetry/ replay parsing
tools/assets/    downscale/trim/wav-normalize scripts (codify the RAMpage pass)
```

### 11.2 CI pipeline (GitHub Actions — you already have `.github/`)
Per PR, in order (fail fast): 1) build; 2) `utility --check-yaml`; 3) `tools/audit/run_all.sh --changed-files` (full run nightly); 4) headless smoke tests for touched factions; 5) asset lint on added/modified assets; 6) regenerate `docs/factions/MATRIX.md` and fail if uncommitted drift.
Nightly: full audit suite + full smoke matrix + RAM/load-time budget check (fail if peak load RAM > 6.5 GB or load > 45 s on the reference runner — locks in the RAMpage win).

### 11.3 Git workflow
- Branch protection on `master`; PRs only; at least the audit suite green.
- PR template with checkboxes: *faction(s) touched · balance intent · audits green · smoke green · changelog line added · one-pager updated?*
- Labels: `faction:<slug>`, `bug-class:B1..B12`, `balance`, `refactor`, `ai-agent` (PRs authored by agents get an extra human review).
- CODEOWNERS per faction folder once Phase 1 lands — this also gives AI agents an unambiguous "who to ask."
- Work through the 17 open PRs: anything older than 2 builds gets rebased-or-closed; stale PRs against a refactoring tree rot fast.

### 11.4 Asset pipeline rules (codifying RAMpage)
`tools/assets/normalize.sh <file>` applies: PNG downscale to category max, alpha-border trim, WAV → mono 16-bit 22050 Hz. Pre-commit hook runs it in check mode. Document category max resolutions in `docs/design/asset_budget.md` (infantry sprite ≤ X, building ≤ Y, UI ≤ Z…). Add a licensing ledger `docs/CREDITS.yaml` (source game/author/license per asset pack — the Cosmonarchy loan and CC BY-NC originals need traceability before 1.0).

### 11.5 Test strategy
- **Smoke:** headless bot-vs-bot, 5 in-game minutes, per Tier-1 faction (catches B8-class crashes).
- **Spawn-all map:** Lua map that creates every buildable actor of a target faction and fires each support power once; assert no crash, no error log lines.
- **Resolved-ruleset golden files:** per faction, the `dump_resolved.py` output is committed; PRs show stat diffs *explicitly* (reviewers see "this PR changes Titan damage 60→66" even when the YAML diff only touched a template).
- **C# unit tests** for OpenRA.Mods.CA/Cameo traits with tricky math (the reload-multiplier family especially).

### 11.6 Documentation set (small, mandatory)
`CLAUDE.md` (expanded — §13), `docs/design/faction_registry.yaml`, one-pagers (Appendix C) for Tier-1 factions, `damage_model.md` (generated), `unit_classes.yaml`, `upgrades_intent.yaml`, `asset_budget.md`, `BALANCE_PHILOSOPHY.md` (one page: counter-triangle, GDI-100, R1–R5, the two-build cooldown rule).

---

## 12. Long-term roadmap

Ordering rationale: **stop the bleeding → make change safe → make structure right → make factions distinct → make balance measurable → make loading modular → ship 1.0.** Each phase has an exit criterion; do not start the next phase's bulk work before the previous exit is green (overlap of *preparation* is fine).

### Phase 0 — Tooling & Tournament Readiness (now → July tournament)
1. Commit this report to `docs/`; expand `CLAUDE.md` (§13).
2. Land `tools/audit/` with B8-relevant checks first (dangling references, ai.yaml validation, sequence refs); run full baseline, commit to `docs/audit/baseline/`, file issues by bug-class label.
3. CI: build + check-yaml + smoke tests for the tournament faction pool. **Nothing merges that crashes a tournament faction.**
4. Publish the faction tier list (Tier-1/2/Legacy) and the tournament pool; add terrain-dependency flags to the registry and validate the tournament map pool against them.
5. Freeze: no Consortium-family buffs, no global class multipliers until post-tournament data.
6. Telemetry-lite: record every tournament game's factions/map/duration/winner.
*Exit:* tournament runs a full day with zero crashes; baseline audit issues filed.

### Phase 1 — Template consolidation & faction isolation (≈ builds +1 to +6)
1. Create `rules/templates/` Layer 0/1; move the TB18-era class multipliers into `combat_classes.yaml` as the single source (R1).
2. Migrate factions one per build using the §10.4 recipe (resolved-diff-verified). Order: Forgotten → CABAL (freshly normalized) → TD GDI/Nod → TS pair → RA2 trio → Consortium/FutureTech → the rest of Tier-1 → Tier-2 opportunistically.
3. Each migration PR also fixes the latent stat bugs its resolved-diff exposes (expect several Slave-Miner-class finds — this is where the "very detailed list of all inherit bugs" you asked for actually gets produced, exhaustively and safely).
4. Turn on the `audit_inherits.py` invariants as *blocking* CI the moment the last Tier-1 faction lands.
*Exit:* zero cross-faction inherits among Tier-1; zero actor→actor inherits; CI blocks regressions.

### Phase 2 — Naming migration (interleaved with late Phase 1, same per-faction PRs where possible)
1. Land `faction_registry.yaml`, `unit_classes.yaml`, the naming linter, and `tools/rename/`.
2. Rename per faction per build (§9.6), including maps and Fluent. Settle `steel_consortium` naming everywhere, including UI strings.
3. Add `legacy_aliases.yaml` shim for community maps; announce deprecation for 1.0.
*Exit:* naming linter blocking in CI; all Tier-1 factions compliant; asset files match actor IDs; `_icon` suffix universal.

### Phase 3 — Faction identity & anti-copy design pass (builds +6 to +12)
1. Write one-pagers (Appendix C) for all Tier-1 factions; workshop the overlap pairs explicitly: Consortium↔FutureTech, Yuri↔Ordos(Deviator)↔Forgotten(Hijacker), RA1↔RA2 pairs, Schwarzer Mond↔everything-exotic.
2. For each faction, implement exactly **one signature mechanic** that no other faction has (CABAL networking, Forgotten salvage, Syndicate stolen-tech comeback, Japan transformation, Zerg creep territory, Dune environment mastery, RA1 tempo ceiling…). Prune units that duplicate a sibling faction's role with different art.
3. Enforce the §8.4 hard guarantees across Tier-1 (CI where possible).
4. Fold Tier-2 factions up one at a time *only* through the Definition of Done gate (Appendix D) — Naxis, TKM, Asian Alliance, WC2 pair are the queue.
*Exit:* every Tier-1 faction has a committed one-pager, a signature mechanic, and passes the guarantees checklist.

### Phase 4 — Measured balance (continuous from tournament onward, hard focus builds +12 to +18)
1. Stand up the headless engagement harness + GDI-100 benchmarks; commit reference reports.
2. Replay telemetry parsing; publish win-rate-by-duration per faction after each event.
3. Power-budget audit (R2) — bring the three §7.4 suspects inside the 2.0× cap.
4. Balance league cadence: playtest → data → one balance build → repeat; two-build cooldown rule in force.
*Exit:* every Tier-1 faction within 45–55% win rate in tournament data, and measured phase curves match declared curves within tolerance.

### Phase 5 — Modularization & dynamic faction loading (builds +18 →)
1. Per-faction `manifest.yaml` include files; master mod.yaml becomes a thin includer (possible with plain MiniYAML includes once folders are self-contained).
2. Engine work (OpenRA.Mods.Cameo): a faction-pack loader that reads manifests at startup, enabling install-time faction selection — this also attacks RAM/load time (only load selected factions' assets; the biggest remaining performance lever after RAMpage).
3. Definition of a "faction pack" format → community faction packs become possible without touching core.
*Exit:* the game boots with an arbitrary subset of faction packs enabled; RAM scales with enabled factions.

### Phase 6 — 1.0 polish
Campaign/co-op scaffolding (SimCity-support-AI revived as a mode), licensing ledger complete, localization coverage for Tier-1, onboarding docs, drop `legacy_aliases.yaml`, 1.0 release.

**Standing weekly rhythm across all phases:** upstream engine sync monthly (TB15 cadence); nightly full audit; triage by bug-class label; one refactor PR + one content/balance PR per build max until Phase 1 completes.

---

## 13. AI agent operating guide

Put a condensed version of this section into `CLAUDE.md` — it currently contains only a memory-file note and must become the agent's real contract.

**Context to load first, always:** `docs/MASTER_REPORT.md` (§9, §10 at minimum), `docs/design/faction_registry.yaml`, the one-pager of any faction being touched, and `docs/audit/baseline/` for the current known-issue state.

**Hard rules for agents**
1. Never add an `Inherits` that targets a non-`^` actor or crosses a faction folder (§10.3). If tempted, extract a template instead.
2. Never create an actor/file that fails the naming linter (§9.1).
3. Any new unit PR must include: Fluent keys, icon named `<id>_icon`, ai.yaml wiring, upgrade-coverage hooks for roster-wide upgrades, `unit_classes` membership, and a changelog line. (Appendix D checklist — copy it into the PR body and tick it.)
4. Any balance change must state before→after numbers in the PR description and touch only one faction (or only `templates/`).
5. Run `tools/audit/run_all.sh --changed-files` and the faction smoke test locally before proposing the PR; paste the summary.
6. When fixing a bug, first classify it B1–B12 and check whether the class detector would have caught it; if not, improve the detector *in the same PR*. This is how the audit suite compounds.
7. Prefer many small single-purpose PRs over one large one; refactors never mix with balance changes.
8. When uncertain about design intent, the one-pager wins over existing YAML (existing YAML may embody a bug).

**Ideal agent task queue (in order, each is well-scoped):** run baseline audits and file issues → dangling-reference fixes (B6) → ai.yaml completion per faction (B5) → `upgrades_intent.yaml` transcription then B3/B4 fixes → per-faction §10.4 migrations → naming migrations → orphan purges (B10) → Fluent gap fill (B12).

---

## 14. Additional recommendations (things not explicitly asked for)

1. **Licensing before visibility.** A 1.0 with tournament coverage will draw attention; the asset provenance ledger (§11.4) protects the project. The Cosmonarchy loan shows you already handle this socially — write it down.
2. **Version the balance ruleset in-game.** Show `Balance vX` in the lobby; replays and bug reports become interpretable.
3. **In-game encyclopedia generated from YAML.** With the registry + resolved dumps you can auto-generate faction/unit pages (and the Fandom wiki content) — huge for a 20-faction learning curve, zero marginal writing cost.
4. **Crash reporting hook.** Even opt-in "copy exception + last 50 log lines" to Discord webhook would shortcut the report-reproduce loop that currently runs through Discord chat.
5. **Performance budget as a product feature.** You cut RAM 12→5.8 GB; publish min-spec targets and defend them in CI (§11.2). Dynamic faction loading (Phase 5) can plausibly reach ~2–3 GB for a 2-faction match.
6. **Community faction-pack program (post-Phase 5).** The template+manifest architecture makes "submit a faction pack" a real contribution path — the sustainable way to keep 100+ factions alive without core-team burnout.
7. **Type-select & control polish per faction** (the Dune exclusivity fix in TB21 is the model) — audit class-select groups for all Tier-1 factions; it's cheap and tournament players feel it immediately.
8. **Name the AI difficulty personalities per universe** (you historically had Cabal/Watson/HAL 9001 — lean back into that; it's free charm).
9. **Map-generator per theatre** (Arrakis exists; temperate/snow next) — procedurally guaranteed-fair tournament maps reduce map-balance disputes.
10. **Decide the canon economy model.** Harvester-based (C&C) vs adapted SC/WC economies — one page in `BALANCE_PHILOSOPHY.md` on how foreign economies map to credits, so future imports (WC3? AoE-likes?) have a recipe.

---

## Appendix A — Audit scripts (specifications + skeletons)

All scripts live in `tools/audit/`, run against a local checkout, read `mods/cameo/`, and share a tiny MiniYAML loader (`miniyaml.py`, ~80 lines: indentation-based parse into (key, value, children); handle `^`, `@suffix`, `-removal` keys). `run_all.sh` executes every audit and writes `docs/audit/latest/*.md`. Exit non-zero on blocking-severity findings. Skeletons below are intentionally compact — an agent should flesh them out as its first repo task.

```python
# miniyaml.py — shared loader
import re, pathlib
def load(path):
    root, stack = [], [(-1, None)]
    for raw in pathlib.Path(path).read_text(encoding='utf-8-sig').splitlines():
        if not raw.strip() or raw.lstrip().startswith('#'): continue
        indent = len(raw) - len(raw.lstrip('\t '))
        key, _, val = raw.strip().partition(':')
        node = {'key': key, 'value': val.strip(), 'children': [], 'file': str(path)}
        while stack and stack[-1][0] >= indent: stack.pop()
        (stack[-1][1]['children'] if stack[-1][1] else root).append(node)
        stack.append((indent, node))
    return root
```

```python
# audit_inherits.py — enforces §10.3
# For every rules file: map actor -> [(inherit_target, file)]
# Violations:
#   V1 target does not start with '^'
#   V2 target defined in a different faction folder than the actor's file
#   V3 target not defined anywhere (dangling)
#   V4 chain depth > 3
#   V5 '-Trait' removals per actor > 2 (warning)
# Output: markdown table per faction, severity column, and a summary count by violation type.
```

```python
# audit_faction_leaks.py — B1
# 1. Parse Faction@ definitions + Buildable/Prerequisites/Queues from resolved rules.
# 2. For each faction, compute reachable buildable actor set (BFS over prerequisites & production).
# 3. Flag actors whose defining file lies outside rules/factions/<slug>/ (post-Phase-1)
#    or whose id prefix (§9.1) mismatches the producing faction (pre/post migration both work).
# Include support powers and defense tabs, not just unit queues.
```

```python
# dump_resolved.py — the refactor safety net (§10.4 step 5)
# Fully resolve inheritance (+ removals, @-merging) for one faction's actors and
# emit canonical sorted JSON of every actor's final trait tree.
# Usage: dump_resolved.py --faction ts_gdi > before.json ; refactor ; diff.
```

```python
# audit_upgrades.py / audit_upgrade_coverage.py — B3/B4
# Input: docs/design/upgrades_intent.yaml, e.g.
#   dark_armament: {faction: cabal, effect: reload, direction: faster, coverage: roster_wide}
# Checks: condition granted somewhere; consumed somewhere; multiplier direction matches
# (reload/build-time multipliers <100 = faster; damage/range >100 = stronger — encode the
# per-field direction table once); roster_wide upgrades cover all faction combat actors.
```

```python
# audit_ai.py — B5: every ID in ai.yaml exists; buildables of tournament factions appear in
#   some squad/build list; AI-referenced prerequisites are producible by that faction.
# audit_sequences.py — B6: Image/sequence/icon refs resolve; orphan sequences listed.
# audit_metadata.py — B7: duplicate tooltip names per faction; class not in unit_classes.yaml;
#   missing Fluent keys (with audit_fluent.py, B12).
# audit_outliers.py — B9: for each (trait,field) collect numeric values across all actors,
#   report entries beyond robust z-score threshold, grouped so 42x-style systemic drift pops.
# audit_orphans.py — B10: refcount weapons/warheads/conditions/sequences/images from resolved
#   ruleset + maps/ + lua/; list zero-ref items.
# audit_assets.py — B11: PNG dimension/border budget per category; WAV format check.
# audit_power_budget.py — R2: per actor compute max stacked multiplier (class template ×
#   research × top rank) for damage and effective HP; flag product > 2.0.
# gen_faction_matrix.py — §5.1 matrix; gen_damage_matrix.py — §8.1 doc from warheads.
```

```bash
# run_all.sh
set -e; mkdir -p docs/audit/latest
for a in inherits faction_leaks upgrades upgrade_coverage ai sequences metadata \
         outliers orphans assets fluent power_budget; do
  python tools/audit/audit_$a.py "$@" > docs/audit/latest/$a.md || failed=1
done
python tools/audit/gen_faction_matrix.py > docs/factions/MATRIX.md
exit ${failed:-0}
```

---

## Appendix B — Naming vocabulary quick reference

Baseline: the RA1 Soviet scheme (`ra_grad`, `ra_upgrade_autoloaders`, `ra_promotion_superoptics`, `ra_doctrine_conscription`).
Unit/building ids: `[game_]faction_name[_variant]` — no structural type words.
Tech items only: `upgrade | promotion | doctrine` marker between faction and name; team proxies end `_proxy_actor`.
Game prefixes: only on actual collisions — `td ts ra1 ra2` today (+ future prefixes the day a new collision appears).
Suffixes: `_icon _cameo _husk _mk2 _elite _ai _water`.
Collision rule: two factions share a name → both take game prefixes (`td_gdi`, `ts_gdi` — never leave one bare).
Slug spelling: full words, snake_case, no abbreviations (`steel_consortium`, not `scon`/`steelconsortium`).
Asset files follow their owning actor id as stem (sequence `Filename:` entries included); icons are `<actor_id>_icon.<ext>`. Shared sprite archives (e.g. `DATA.R16`) referenced by many images are exempt.

## Appendix C — Faction design one-pager template (`docs/design/factions/<slug>.md`)

```
# <Display Name> (<slug>)  —  Tier: 1|2|Legacy   Universe: <game>
Fantasy (2 sentences): what it FEELS like to play/fight against.
Archetypes: e.g. tech + denial.       Terrain dependency: none|water|tiberium|arrakis
Power curve declaration: E_/M_/L_  (+ comeback lever: yes/what | close-out faction)
Signature mechanic (exactly one, unique in the game): …
Roster pillars: 5-8 units that define it; everything else is support.
Hard-guarantee checklist (§8.4): AA t1.5 ☐  mobile AA t2 ☐  detection ☐  anti-heavy ☐ …
Explicit NON-goals: what this faction must never become (its overlap guardrails).
Known matchup concerns: …
```

## Appendix D — Definition of Done

**New unit:** template-only inherits ☐ · naming compliant + `_icon` ☐ · Fluent keys ☐ · class assigned ☐ · ai.yaml wired ☐ · roster-wide upgrade hooks ☐ · sequences resolve ☐ · smoke test pass ☐ · changelog line with numbers ☐ · one-pager roster updated ☐

**Faction promotion Tier-2 → Tier-1:** one-pager committed ☐ · §10.3 invariants clean ☐ · naming migrated ☐ · AI plays full roster ☐ · hard guarantees (§8.4) ☐ · upgrade intent file complete ☐ · smoke + spawn-all map green ☐ · Fluent coverage 100% (en) ☐ · added to matrix/tournament pool ☐

**Balance PR:** one faction or templates-only ☐ · before→after numbers in description ☐ · harness report attached ☐ · cooldown rule respected ☐ · intent file updated ☐

---

*End of report. Regenerate §5's matrix and Appendix-A outputs from the repo on every build; revise §6 ratings after each tournament's telemetry. This document should be edited like code: via PRs, with the roadmap phase status kept current at the top of §12.*
