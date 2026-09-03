# Session checkpoint — 2026-08-03 (weapon 3-way split + balance-pipeline roadmap)

> ⛔ **ARCHIVED — SUPERSEDED by [`docs/HANDOFF.md`](../../HANDOFF.md) (2026-08-23).**
> This is a dated session record, kept for provenance and for the technique notes in it.
> It is **not** current state: statuses, branch names, counts and "next steps" below were
> true on 2026-08-03 and have moved since. Never resume work from this file — read
> `docs/HANDOFF.md`, then verify against the artifact. The branch it names (`fix/production-queue-crash`) was merged long ago. Still useful for: the LIVE-vs-DEAD weapon-file list.

Resume anchor for after `/compact`. Branch: **`fix/production-queue-crash`** (NOT master).
Everything below is committed and boots to menu.

---

## ⚠ CRITICAL GOTCHAS (read first)

1. **LIVE vs DEAD weapon files.** `mods/cameo/mod.yaml` `Weapons:` list is authoritative.
   - **DEAD (migrated, commented out — do NOT edit for real effect):**
     `weapons/redalert.yaml` (→ RA1 Shared), `weapons/redalert2.yaml` (→ RA2 Shared),
     `weapons/xcom.yaml`, and many never-enabled ones.
   - **LIVE central:** `weapons.yaml`, `tiberiandawn.yaml`, `redalert2mod.yaml`, `d2k.yaml`,
     `starcraft.yaml`, `warcraft2.yaml`, `tiberiansun.yaml`, `outpost2.yaml`.
   - **LIVE RA1/RA2 content lives in `ContentPacks/RedAlert{,2}/…/yaml/`** (loaded via each
     pack's `content.yaml` Include). The dead central RA1/RA2/xcom files are stale
     duplicates → **should be deleted** (migration cleanup TODO). My family retrofits walked
     the whole tree so both live and dead copies got edited (dead ones harmless).
2. **Boot gate must require a FRESH perf.log** (LastWriteTime > cutoff) — a fast crash
   leaves a stale menu marker and false-passes. See the PowerShell poll used all session.
3. **Never hand-edit balance numbers** — use the pipeline (`docs/design/BALANCE_PIPELINE.md`).

---

## What this session finished (committed)

- **Weapon 3-way split — mechanical Phase-2 COMPLETE.** All non-energy families retrofitted
  to `Inherits@wh ^Warhead_… + @proj ^Projectile_… + @fx ^Effect_…`: Bullet, Cannon, Missile,
  Flak, Flame, Chemical, Explosions (Grenade/Shrapnel/HeavyBomb), Melee/Arrow/Magic, Nuclear.
  Tool: `tools/balance/retrofit_weapon_family.py` (resolution-based repair, now **fixpoint-
  iterated**). Damage values preserved verbatim throughout.
- **Underscore-section naming** (`^Warhead_/^Projectile_/^Effect_<Fam>_<Level>`, twins
  `_Percentage/_FriendlyFire`) via `rename_3way_underscore.py`.
- **Report policy:** default firing sound stays on the projectile template;
  `strip_orphan_report.py` drops orphaned `-Report:` in projectile-less families.
- **Correctness fix (`c8d2b671e`):** the one-pass repair had left ~110 stale-key
  **double-warheads** (grandchildren of converted templates); `fix_stale_warhead_keys.py`
  repaired all, iterated to fixpoint. Audit now clean at 0.
- **Swarmer Drone burst fix (`b2eab4889`)** per the burst-report law.
- **RA2 bullet effect templates on the LIVE Shared pack (`a38259a12`)** —
  `^Effect_Bullet_{Light,Medium,Heavy}_RA2` (ra2_piff/ra2_piffs), first slice of the art layer.
- **Research + laws committed:** `GAME_SPECIFIC_WEAPON_BASES.md`, `PROJECTILE_EFFECT_SOURCING.md`
  (from Romanov's Vengeance = RA2 + Shattered Paradise = TS), Tier↔WeaponClass + warhead-budget
  law, burst-report law (memories), art-architecture decisions.

## Decided laws to apply going forward
- **Every weapon = exactly 1 `@proj` + 1 `@fx` + N warheads** (N = TYPES×LEVELS budget:
  1 normal / 2 hybrid-or-between-tier / 4 only a between-tier lore hybrid).
- **Tier↔WeaponClass:** T1→Light(0.75), T2→Medium(1.0), T3+→Heavy(1.25), super→1.5;
  between-tier units mix two adjacent levels; specialized units case-by-case.
- **Art = 3 tiers:** central classic (piff/piffs) fallback → per-game original
  (RA2 ra2_piff; TS art shared by GDI+Nod) → per-faction unique (CABAL blue trail;
  Steel Consortium **blue piffs** L/M/H; Forgotten; etc.). Name `^Effect_<Fam>_<Level>_RA2`
  (game/faction = last section). Templates live in the game's Shared pack (or faction pack).
- **Launch angle → projectile SUBTYPES** by launch style (vertical-VLS / ballistic-arc /
  direct), not one global value.
- **Burst sound driven by the sound FILE:** already-a-burst sound → `StartBurstReport` only;
  single-shot sound → per-shot `Report`.

---

## REMAINING WORK — the full balance pipeline, honest estimate

Framing: "sessions" ≈ one focused work block like today. The dominant cost is **maintainer
per-unit decisions** (tier/identity/warhead judgments, `apply_balance --confirm` orders) and
the sheer count (~20 factions × dozens of units; ~8 source games of art). Weapon templates
(this session) were an EARLY phase; the unit rebalance is the bulk.

| Phase | Scope | Est. sessions |
|---|---|---|
| **W1. Energy families** | Laser/Railgun/Tesla/TeslaCharged 3-way — BLOCKED on ExtraDamage rework decision | ~0.5 (after decision) |
| **W2. Per-game/faction art** | projectile+effect templates for ~8 games + ~20 faction uniques (RA2 effects 2/9 done; projectiles 0; TS/others 0) | 4–8 |
| **W3. Bundle dissolution** | ^RA2SmallArms-style bundles → atomic 3-inherit, rewire hundreds of weapons across ~20 bases | 2–3 |
| **W4. Mixed collapse + `1Dam` retirement (Phase 3)** | ~609 mixed weapons incl. ^TSDefaultMissile per-tier, PLUS **297 live weapons still on the deprecated `Warhead@1Dam` inline pattern** (DESIGN.md §870 — retired; a bare 1Dam is a bug). Each must be reassigned to the correct `^Warhead_*` template (per-weapon tier/profile judgment); moving onto a template removes its inline `1Dam` + `Versus` together. Maintainer-directed. | 4–7 |
| **W5. Old-template deletion (Phase 4) + migration cleanup** | delete legacy `^SmallArms…` + dead central RA1/RA2/xcom files | ~1 |
| **C1. Expanding-damage C# trait** | new warhead trait (min→max radius, N ticks, per-tick delay, single template Versus) to replace the ~10-stacked-warhead nuke/cluster bandaid; then migrate nuke/area weapons onto it. Nuke/cluster custom keys are EXEMPT from the Versus/1Dam rule until this exists. See memory cameo-expanding-damage-trait. | 1–2 |
| **U1. Unit-class templates** | vehicles DONE; infantry (4 templates + members), defense/aircraft/naval classes | 3–6 |
| **B1. Balance synthesis/research** | class anchors from aggregated mods (MO/CnCR/RV/SP/DTA/CA…) + ORIGINAL_UNIT_STATS + BALANCE_SYNTHESIS; vehicles anchored, rest TODO | 2–4 |
| **B2. Apply balance (THE bulk)** | restat every unit+weapon via formula → ledgers → `apply_balance --confirm` → boot, per faction; hundreds of units, each maintainer-signed | 8–15 |
| **B3. Excel workbook** | `extract_stats` → json ledgers → `build_workbook.py` → xlsx (tooling exists; run once yaml is final) | ~0.5 |

**Honest total: ~25–45 focused sessions.** In calendar terms with an available maintainer,
realistically **~2–4 months** of active collaborative work — longer if scope grows (it is an
ever-growing crossover) or decisions are slower. The single biggest lever on the timeline is
how fast per-unit balance decisions + `--confirm` sign-offs happen; that work cannot be fully
automated (per-unit identity/tier judgment is inherently human-in-the-loop).

---

## EXACT RESUME (next concrete steps, in order)

1. **Decide ExtraDamage rework** (unblocks W1). Recommendation: spread-deficit-via-tiers —
   energy weapons get tight spread (~100) + a defined anti-shield ExtraDamage folded into the
   later spread rebalance. Then run `retrofit_weapon_family.py --old LaserWeapon,RailgunWeapon,
   TeslaWeapon,TeslaChargedWeapon` → self-check → boot → commit.
2. **Continue RA2 art (W2)** on the LIVE Shared pack: extract the remaining RA2 effects
   (Flak/Missile L/M/H/Cannon L/M/H — inline blocks are in `ContentPacks/RedAlert2/Shared/yaml/
   weapons.yaml`) into `^Effect_<Fam>_<Level>_RA2`; then RA2 **projectile** templates
   (`^Projectile_Missile_RA2` vertical-VLS + `^Projectile_BallisticMissile_RA2` for V3/
   Dreadnought/Boomer; ra2_dragon/patriot images + contrail-colour variants). Then Steel
   Consortium **blue-piff** per-faction effects (L/M/H). Boot-gate each.
3. **Migration cleanup:** delete dead central `weapons/redalert.yaml`, `weapons/redalert2.yaml`,
   `weapons/xcom.yaml` (confirm nothing live inherits them first).
4. Then W3 → W4 → U1 → B1 → B2 → B3 per the table.

Self-check recipe per weapon change (used all session):
`git diff -U0 -- 'mods/cameo/**/*.yaml' | grep '^[+-]\s*Damage:'` must be EMPTY;
`python tools/balance/fix_stale_warhead_keys.py` and `strip_orphan_report.py` must report 0;
boot gate with the fresh-perf.log poll; scoped `git add`, never `-A`.
