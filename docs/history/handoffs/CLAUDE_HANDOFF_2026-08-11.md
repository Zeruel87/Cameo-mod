# Letter to Devin — Claude (Opus 4.8), 2026-08-11

> ⛔ **ARCHIVED — SUPERSEDED by [`docs/HANDOFF.md`](../../HANDOFF.md) (2026-08-23).**
> This is a dated session record, kept for provenance and for the technique notes in it.
> It is **not** current state: statuses, branch names, counts and "next steps" below were
> true on 2026-08-11 and have moved since. Never resume work from this file — read
> `docs/HANDOFF.md`, then verify against the artifact. Agent-to-agent letter. Its plan became W15–W19 on the board in `docs/design/BALANCE_PROGRAM_PLAN.md`.

Hey Devin. Long session — EMP auto-scaling, %-twin unification, the falloff overhaul, and a new
pricing metric all landed, and I read your `AI_HANDOFF_2026-08-05.md` end-to-end. Here's everything,
plus the plan for the big conversion program the maintainer wants us to finally close out.

Boot-gate every engine commit (`perf.log` → `MenuPostProcessEffect.PostWorldLoaded`, no new
`exception-*.log`; baseline was 169). Scoped `git add <files>` only. Sign your commits
`Co-Authored-By: Devin AI <devin@cognition.ai>` — never the Claude trailer.

---

## 1. What I shipped this session (all on `master`, all boot-gated)

| Commit | What |
|---|---|
| `0d2cd6e82` | **IntegrityScale auto-drain** (C# `AreaDamage.IntegrityScale`, mirrors `ApplyPhysicalState`) + **all 85 %-twins unified on `AreaDamagePercentage`** + Ixian Storm collapses (LightningStorm, ShockGun family). |
| `ea72d259e` | **Falloff restructure** — 6-wide `DEFAULT_FALLOFFS` all ending in 0, `Bullet = 100,0`, `EVEN_FALLOFFS` available, Nuclear 11-value. 85 families re-spliced, drift=1. |
| `af348a8b3` | **`tools/balance/effective_damage.py`** — read-only AoE-integrated pricing metric (see §3). |
| `a2d06f0a2` | effective_damage fix: instant hits → reliability 1.0 (global-range superweapons were mis-scored). |

The maintainer separately committed the **Tesla 4-tier** migration (`14713d579`, `145c6861c`):
`^Warhead_Tesla_Super` now exists, `^Warhead_TeslaCharged_Super` is retired (0 refs), Quantum carries
`Tesla` in its DamageTypes, and the extra-damage chips passively drain integrity. I verified drift=1.

## 2. EMP / Integrity system (full detail in `EMP_INTEGRITY_SYSTEM.md`)
`AreaDamage.IntegrityScale` drains the victim's `Integrity` ELECTRONICS pool (**not** a shield) by
`damage × Scale/100` on hit —
Tesla 100 / Storm 50 / Quantum 33 (= 100 × Tesla-parents / total-parents). Integrity pool = 100% MaxHP,
`AffectedByDamageTypes: Tesla`, so Tesla-typed weapons drain it **twice** (passive 1:1 + IntegrityScale)
→ Tesla disables at 50% HP, Storm ~67%, Quantum ~75%. Flat `Warhead@EMPUnit` is now **upgrade-only**.
⚠ **§4 follow-up still open (your lane):** the effect-layer `^Effect_Tesla_Heavy/Super` still carry a
flat EMP that now triple-counts. Audit the ~100 `^Effect_Tesla` inheritors (confirm each also inherits a
Tesla/Storm/Quantum warhead) before stripping it.

## 3. The `effective_damage` pricing metric — USE THIS for balance
`python tools/balance/effective_damage.py [--top N] [NAMES...]`. Read-only, resolves the live ruleset.
It puts single-target energy warheads and wide AoE warheads on ONE axis:
```
effective = Σ(main + *_ExtraDamage)  base × ( reliability + 0.25 × footprint_cells² )
  footprint   = 2π·Spread²·∫(F/100)·r dr / 1024²
  reliability = avg falloff over a scatter disc σ   (instant hits → 1.0)
  σ           = Inaccuracy + 0.20 × 100 × Range / min(Speed, 10000)
  clamps: Spread ≥ 100, Falloff ≥ 100,0
```
Validated: TeslaZap (instant) = 1.01× base; D2K_155mm (slow arc, wide) = 1.64× base off the same 48k.
Five tuning constants at the top of the file. **This is the number to price against once the pipeline
below is fixed.**

## 4. ⚠ The pipeline is stale — fix before pricing
`extract_stats.py` line ~339 only recognizes `SpreadDamage/HealthPercentageDamage/TargetDamage`, **not
`AreaDamage`**. So every `docs/balance/*.json` ledger still holds pre-migration data, and
`formula.py` / `audit_balance_drift` read stale numbers. **First real balance task:** add `AreaDamage`
+ `AreaDamagePercentage` to that recognizer, capture `Spread`/`Falloff` per warhead, re-extract all
ledgers, then wire `effective_damage` in as a real column. `effective_damage.py` already sidesteps this
(it recognizes AreaDamage), so its numbers are correct today — mirror its `flat_damage_warheads()` logic.

## 5. The conversion program (current counts, 2026-08-11)
- **1381** old-family inherit sites (`^SmallArms/^Grenade/^*Cannon/^*FlameWeapon/...`).
- **2434** `SpreadDamage`-typed warhead lines in live files.
- **1445** `Warhead@1Dam` legacy sites.
- **phase_b_survey:** 360 weapons on old families — 21 pure-single (mechanical), 337 mixed in 242 groups.

### Plan (phased, boot-gate per cluster, preserve `Damage` verbatim)
1. **SpreadDamage → AreaDamage is NOT a blanket rename.** Categorize each `: SpreadDamage`:
   - **main** warhead that inherits a matching `^Warhead_*` → make it **bare** (drop the type; inherits AreaDamage).
   - **main** with no matching template → explicit **AreaDamage**.
   - **`*_ExtraDamage` chip** → keep `SpreadDamage` (chips are legitimately SpreadDamage).
   - **`*FriendlyFire` twin** at 50% → **delete** (baked FF replaces it).
   Script it, `find_empty_warhead.py = 0`, boot-gate.
2. **Phase 3 mixed collapse** (337 weapons, biggest chunk) — cluster-by-cluster per your `cluster-convert`
   skill. Effect-free clusters first; then flame/chem using the **inject-`PhysicalStateName: Temperature`**
   pattern from your §14.7 (the fix for the `MissingFieldsException` you hit) — that's the key unlock for
   the effect-heavy families you had to revert.
3. **Missing templates**: 251 weapons reference families with no 3-way template. Several now DO exist
   (Sonic, Flak, Demolition, Concussion) — re-map those; genuinely-missing ones (Sniper, Toxic, Healing,
   Repair) need a template built or a maintainer mapping call.
4. **Phase 4**: delete the ~30 orphaned old templates once their inherit count hits 0.
5. **W4** (1445 `Warhead@1Dam`): per-unit tier/profile judgment — needs maintainer input, do last.

Use `effective_damage.py` before/after a cluster to confirm you didn't change resolved behavior beyond
the intended structural swap.

## 6. Division of labor + suggestions
- **You (Devin):** the mechanical Phase 3 clusters (your converter + skills are built for it), the
  extract_stats AreaDamage fix (§4), and the §4 effect-layer EMP sweep. All disjoint from design.
- **Me (Claude):** design shifts (blends, calibration, family/falloff/tier decisions), the
  `effective_damage`/pricing model, and any new C#. I own `gen_weapon_template.py` + the template section
  of `weapons.yaml`; **serialize with me before regenerating** (a splice touches all 85 families).
- **Suggestion:** knock out the **21 pure-single mechanical** weapons first (cheap, unblocks
  phase_b_survey), then the largest effect-free 2-inherit signature. Leave energy/flame/chem clusters
  until the PhysicalState-aware converter is proven on a small batch.

## 7. Open decisions parked with the maintainer
- Which weapon families should use the `EVEN` falloff (`100,80,60,40,20,0`) — wired, unassigned.
- 6-value falloffs grew the outer radius 4S→5S (a low-damage skirt) — spreads unchanged, flag for playtest.
- 68 weapons footprint > 50 cell² + 7 with σ > 5000 — mostly legit superweapons, a few may be over-scaled.

— Claude (Opus 4.8)
