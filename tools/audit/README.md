# tools/audit — the Cameo audit suite

Implements the detector specifications from `docs/history/MASTER_REPORT_2026-07-08.md`
Appendix A. Every script reads the live ruleset (mod.yaml include graph,
merged + inheritance-resolved) and prints a markdown report to stdout.

## Running

```sh
bash tools/audit/run_all.sh         # full suite -> docs/audit/latest/   (canonical)
python tools/audit/run_all.py       # same thing, for shells without `sh`
python tools/audit/audit_ai.py      # any single audit
python tools/audit/dump_resolved.py --faction cabal > before.json
```

⚠ **Never redirect an audit through PowerShell's `>`** — it writes UTF-16 and corrupts the
report (CLAUDE.md rule 8). Both runners force `PYTHONIOENCODING=utf-8`.

`run_all.py` parses its audit list out of `run_all.sh` rather than keeping its own copy.
That is deliberate: the two lists DID drift once, and because the Python runner also used a
different filename convention (`audit_<name>.md` vs `<name>.md`), `docs/audit/latest/` ended
up holding two stale copies of every report. **Add new audits to `run_all.sh`.**

Blocking-severity findings (dangling references and similar crash-class
issues) make the owning script — and run_all.sh — exit non-zero, so the
suite can gate CI.

## Scripts

| script | bug class | checks |
|---|---|---|
| `audit_inherits.py` | B2 | concrete/cross-faction/dangling/deep inherits, removal abuse |
| `audit_faction_leaks.py` | B1 | buildables owned by another faction; cross-faction concrete inherits in rosters |
| `audit_upgrades.py` | B3 | inverted multiplier directions, dead upgrades, dead wiring (needs `docs/design/upgrades_intent.yaml`) |
| `audit_upgrade_coverage.py` | B4 | roster-wide upgrade coverage gaps |
| `audit_ai.py` | B5 | ai.yaml refs to nonexistent/unloaded actors; unwired combat units |
| `audit_ai_personalities.py` | AI wiring | personality selector/consumer condition parity and byte-identical shared squad-manager fields |
| `audit_sequences.py` | B6 | missing render images/sequences; orphaned sequence images |
| `audit_metadata.py` | B7 | duplicate/missing tooltips per faction |
| `audit_outliers.py` | B9 | robust-z numeric drift per (trait, field); bounds hard screen |
| `audit_orphans.py` | B10 | orphan weapons; dangling weapon refs; dead conditions |
| `audit_assets.py` | B11 | PNG budget; WAV mono/16-bit/22050 Hz norm |
| `audit_fluent.py` | B12 | unresolved fluent refs; orphaned actor-* keys; coverage |
| `audit_power_budget.py` | R2 | worst-case stacked multipliers > 2.0× |
| `audit_stat_formulas.py` | house rules | HpPerStep=HP/20, SelfHeal=HP/2500 (inf /1000), shield regen=2×heal, defense vision=weapon range + DetectCloaked=range/2 + power=-cost/20, vehicle TurnSpeed=Speed/5 (turretless 2×, artillery Archer firing-slow), fighter/bomber TurnSpeed=Speed/15, AA defense gated by radar tier + advanced defense by tech tier, StartingUnits existence + light(~2000)/heavy(~10000) composition at 5:1 inf:veh, AA weapons must have Air-capable damage warheads |
| `audit_weapon_uniqueness.py` | §10 | actors sharing the same weapon (violates per-actor weapon ownership) |
| `audit_garrison_weapons.py` | §11 | garrisonable actors missing garrison weapon overrides |
| `audit_asset_files.py` | §1, §8 | asset filenames not matching actor id convention |
| `audit_promotion_gating.py` | §15 | promotion units not strictly stronger than base |
| `audit_min_range.py` | §3 | weapons with range below minimum threshold |
| `audit_basebuilder_crates.py` | B5 | crate action references to nonexistent actors |
| `audit_buildable_order.py` | §5 | build palette ordering and tech tier inference |
| `audit_display_text.py` | B7 | display names containing raw actor IDs or stale references |
| `audit_rename_safety.py` | §1 | pre-rename safety checks (shared assets, voice sets) |
| `audit_missing_elite.py` | §16.3 | RA2-styled actors (`^GainsExperienceRA2`) missing elite armaments |
| `audit_elite_gating.py` | §16.3 | elite armaments missing `RequiresCondition: rank-elite` |
| `audit_rank_decoration.py` | §16.2 | `^GainsExperienceTD` actors missing/wrong `^*RankDecoration` |
| `audit_dune_rank_decoration.py` | §16.2 | D2k actors specifically missing `^DuneRankDecoration` |
| `audit_effect_warhead_names.py` | §8 | CreateEffect warhead naming violations |
| `audit_nuclear_flash_bindings.py` | visual regression | active RA1, Ixian, and CABAL launchers retain the directional flash warhead and approved tuning |
| `audit_empty_warheads.py` | crash | resolved `Warhead*` nodes without a type value (boot NRE in `WeaponInfo.LoadWarheads`); run after bulk warhead/weapon edits |
| `audit_weapon_suffixes.py` | §1 | weapon suffix conventions: `_elite`, `_EMP`, `_AA` |
| `audit_balance_sheet.py` | §12 | cross-reference cameo_armor_system.xlsx vs in-game stats |
| `audit_createeffect_image.py` *(in tools/)* | §8 | CreateEffect warheads carrying explicit `Image:` field |
| `audit_ce_image_usage.py` *(in tools/)* | §8 | classifies CE-only vs shared images |
| `audit_consistency_report.py` | meta | verifies fixes from `docs/audit/CONSISTENCY_REPORT.md` are not regressed |
| `gen_faction_matrix.py` | §2 | regenerates `docs/factions/MATRIX.md` |
| `gen_damage_matrix.py` | §8, ARMOR_SYSTEM.md | armor classes + Versus aggregates |
| `gen_rename_maps.py` | §1 | naming compliance; writes `tools/rename/rename_map_<faction>.yaml` |
| `audit_duplicate_inherits.py` | crash | a definition reaching the same parent twice on ONE chain — the `Parent type X was already inherited` boot crash. Grep cannot find it; the boot reports only the FIRST one |
| `audit_duplicate_keys.py` | crash-risk | duplicate keys inside one node (silent overrides). D1 = a dropped `Inherits`, i.e. a template that is quietly not applied |
| `audit_unique_traits.py` | crash | duplicate traits the engine resolves with `.Trait<T>()` — these crash at PRODUCTION time, not at boot |
| `audit_physical_state_warheads.py` | correctness | physical-state warhead combinations that double-apply a meter |
| `audit_warhead_split.py` | W24 | the multi-warhead over-damage guard. A RATCHET: the baseline may fall, never rise |
| `audit_unconverted_templates.py` | W23 | legacy weapon templates still outside the `^Warhead_*` family system. **Writes its own report with `--write`** — its stdout is only a summary |
| `audit_impact_glow_preservation.py` | §8 | universal glow coverage for sprite-backed weapon effects |
| `audit_template_conformance.py` | §12 | template values are law (conyard power, etc.) |
| `audit_multiplier_modifiers.py` | §12 | every `*Multiplier` `Modifier` is an integer percent (`89`, never `0.89`) |
| `audit_armor_upgrade_harm.py` | §12.0e | the armor-plating invariants — above all, **an armor upgrade must never increase incoming damage** |
| `audit_plating_exclusivity.py` | §12.0e | no actor may ever wear two armor platings at once |
| `audit_hex_shield_routing.py` | §12.0f | actor-specific shield sizing and invalid resolved shield routes |
| `audit_survivability_pricing.py` | E1 | what a baseline shield SHOULD cost and currently does not (informational) |
| `audit_k_linearity.py` | pricing | scalable K must stay damage-independent; inventories folded hits, standalone floors, and rounding |
| `audit_balance_drift.py` | pipeline | yaml vs the committed ledger. **Red means a balance commit skipped `extract_stats.py`** |
| `audit_packs.py` | §2 | content-pack conversion and placement |
| `audit_ts_death_palette.py` | B6 | TS actors whose `PlayerPalette` and `DeathSequencePalette` disagree |
| `audit_doc_claims.py` | meta | re-measures every numeric claim in `docs/audit/doc_claims.yaml`. A number in prose is true only on the day it is written |
| `audit_doc_health.py` | meta | the documentation's own gate: control characters, mojibake, broken links/anchors, references to moved documents, duplicate DESIGN section ids |
| `audit_code_duplication.py` | periodic | copy-paste detector for the tooling and the C# mods |
| `audit_test_coverage.py` | periodic | test-coverage floor for the C# mod code and the tooling |
| `audit_error_handling.py` | periodic | error-handling lint for the Python tooling |
| `audit_security.py` | periodic | repo security scan (no network required) |
| `audit_recent_changes.py` | periodic | regression review of recent git history: balance yaml without a ledger, unregistered audits, missing provenance trailers. **Needs full history — a shallow clone limits it** |
| `audit_periodic_freshness.py` | meta | staleness gate for `docs/audit/periodic.json`. `--warn-only` in the per-commit suite; strict in the scheduled run |
| `dump_resolved.py` | §10 | canonical resolved-ruleset JSON (refactor safety net) |

Shared infrastructure: `miniyaml.py` (parser/merger/inheritance resolver),
`cameo_model.py` (faction registry, prerequisite-closure rosters, ownership
attribution, unit typing), `report.py` (markdown helpers).

## Parser validation

`miniyaml.py` was validated against engine behavior two ways:

1. `make.cmd test` (`utility --check-yaml`) passing on the same tree the
   loader reports as reference-clean (0 dangling inherits, 1 dangling
   weapon ref in unreachable content).
2. Spot checks of resolved actors against hand-verified ground truth
   (inheritance chains, `-Trait` removals, same-actor block re-opening,
   `Inherits@` mixin merging: `tsobl2`, `tsttnkcabal`, `tsshotmut`,
   `tsprobe`, `TSNTHAND2`).

Known approximations (fine for auditing, not for shipping a game):

- indentation is compared by raw leading-whitespace length, not tab stops;
- `Inherits` nodes are expanded at their document position, then later
  same-key nodes merge over earlier ones (matches observed engine behavior);
- faction ownership before the §12 Phase-1 folder migration is heuristic
  (ContentPack folder, `~fact.X` gates, conyard gate tokens) — shared actors
  report as "needs human decision" rather than guessed.
