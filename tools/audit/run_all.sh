#!/bin/sh
# run_all.sh — execute the full Cameo audit suite (MASTER_REPORT Appendix A).
# Writes one markdown report per audit to docs/audit/latest/, regenerates
# docs/factions/MATRIX.md, and exits non-zero if any blocking audit failed.
#
# Usage: tools/audit/run_all.sh            (from the repo root)
#        PYTHON=python3 tools/audit/run_all.sh
set -u
cd "$(dirname "$0")/../.."

PYTHON="${PYTHON:-python}"
if ! "$PYTHON" -c 'import sys' 2>/dev/null; then
  for cand in python3 py \
      "$LOCALAPPDATA/Programs/Python/Python312/python.exe"; do
    if "$cand" -c 'import sys' 2>/dev/null; then PYTHON="$cand"; break; fi
  done
fi

# Where may this run write?  docs/audit/latest/ is TRACKED evidence, and several
# audits read engine/ C# or full git history — neither of which exists in a fresh
# clone or a cloud container.  Missing them makes those audits report LESS and still
# say PASS, so a regenerate from an incomplete tree silently deletes real findings.
# tools/audit/environment.py owns the check and the exact list; pass --force-latest
# to override.  See docs/LESSONS_LEARNED.md "audit/latest is environment-bound".
FORCE_LATEST=""
ARGS=""
for arg in "$@"; do
  case "$arg" in
    --force-latest) FORCE_LATEST="--force-latest" ;;
    *) ARGS="$ARGS $arg" ;;
  esac
done
# shellcheck disable=SC2086
set -- $ARGS

OUT="$("$PYTHON" tools/audit/environment.py --print-dir $FORCE_LATEST)"
if [ -z "$OUT" ]; then
  # Fail loudly rather than defaulting: defaulting to latest/ is exactly the write
  # this guard exists to prevent, and defaulting to anywhere else scatters 60 reports.
  echo "run_all.sh: tools/audit/environment.py reported no output directory" >&2
  exit 2
fi
"$PYTHON" tools/audit/environment.py $FORCE_LATEST >&2 || true

mkdir -p "$OUT" docs/factions
failed=0

# Force child processes to emit UTF-8 regardless of OS console codepage
# (Windows git-bash defaults to cp1252, which corrupts §, —, etc.)
export PYTHONIOENCODING=utf-8

# NOTE: "elite_naming" is intentionally excluded — audit_elite_naming.py is
# deprecated, fully superseded by audit_weapon_suffixes.py X1 section
# (same check: rank-elite gated armaments not ending _elite).
# NOTE: "damage_grid" is intentionally excluded — audit_damage_grid.py WAS
# re-derived 2026-08-25 from the live law (formula.DAMAGE_STEP = 100 +
# formula.percentage_twin); it is excluded not because it is stale but because
# its counts are moving targets while W24 collapses and the fold are in flight.
# Wire it in once that work settles; see docs/HANDOFF.md and the audit header.
for a in inherits duplicate_inherits faction_leaks upgrades upgrade_coverage ai ai_personalities sequences \
         metadata outliers orphans assets fluent power_budget stat_formulas \
         weapon_uniqueness garrison_weapons asset_files promotion_gating min_range \
         basebuilder_crates buildable_order display_text rename_safety \
         missing_elite elite_gating rank_decoration \
         dune_rank_decoration effect_warhead_names weapon_suffixes \
         balance_sheet consistency_report packs balance_drift \
         duplicate_keys \
         template_conformance multiplier_modifiers nuclear_flash_bindings \
         ts_death_palette warhead_split physical_state_warheads \
         unique_traits armor_upgrade_harm plating_exclusivity k_linearity percentage_runtime \
         survivability_pricing doc_claims doc_health task_index hex_shield_routing \
         impact_glow_preservation dead_warhead_fields family_uniqueness \
         three_way_split tier_weapon_class heaviness_bell versus_profile \
         meter_dilution ca_drift upstream_adoption engine_freshness; do
  echo "== audit_$a"
  "$PYTHON" "tools/audit/audit_$a.py" "$@" > "$OUT/$a.md" 2> "$OUT/$a.err" \
    || failed=1
  [ -s "$OUT/$a.err" ] || rm -f "$OUT/$a.err"
done

# ADVISORY audits — they RUN and write full reports, but they must NOT set the suite's exit
# code. Maintainer ruling 2026-08-24.
#
# Every one is a SCHEDULED scan registered in docs/audit/periodic.json on a 14- or 30-day
# cadence, and this suite is the PER-COMMIT gate — the same argument made a few lines below for
# passing --warn-only to audit_periodic_freshness. All five had been red since 2026-08-16
# (test_coverage alone drifted 223 -> 235 -> 249 -> 257 -> 270 untested modules), so run_all.sh
# exited 1 on every clean tree for a week and the gate's "suite is green" signal was dead: a
# genuinely NEW failure looked identical to the stale ones.
#
# ⚠ The calendar is still enforced, just not here: `python tools/audit/audit_periodic_freshness.py`
#   with NO flag exits 1 when a scan is overdue. That is where lateness belongs.
# ⚠ Each script still exits 1 on its own findings, so CI may gate on one deliberately.
# ⚠ tools/audit/run_all.py parses BOTH loops out of this file — keep the `for a in ...; do`
#   shape so the two runners cannot drift apart.
for a in code_duplication test_coverage recent_changes error_handling security; do
  echo "== audit_$a (advisory)"
  "$PYTHON" "tools/audit/audit_$a.py" "$@" > "$OUT/$a.md" 2> "$OUT/$a.err" || true
  [ -s "$OUT/$a.err" ] || rm -f "$OUT/$a.err"
done

# Audits that live in tools/ rather than tools/audit/
for a in createeffect_image:tools/audit_createeffect_image.py \
         ce_image_usage:tools/audit_ce_image_usage.py \
         empty_warhead:tools/audit/find_empty_warhead.py \
         gen_sync:tools/balance/verify_generator_sync.py; do
  name="${a%%:*}"
  script="${a##*:}"
  echo "== $name"
  "$PYTHON" "$script" "$@" > "$OUT/$name.md" 2> "$OUT/$name.err" \
    || failed=1
  [ -s "$OUT/$name.err" ] || rm -f "$OUT/$name.err"
done

# audit_unconverted_templates writes its OWN report with --write; its stdout is only a
# short summary, so redirecting stdout into the report file would clobber the real one.
echo "== unconverted_templates"
"$PYTHON" tools/audit/audit_unconverted_templates.py --write $FORCE_LATEST > /dev/null 2> "$OUT/unconverted_templates.err" \
  || failed=1
[ -s "$OUT/unconverted_templates.err" ] || rm -f "$OUT/unconverted_templates.err"

# Staleness gate for the mandatory recurring audits (docs/audit/periodic.json):
# runs last so its report reflects this run's evidence files.
# --warn-only: this suite is the PER-COMMIT gate, so a late scheduled scan must not
# turn it red for a reason unrelated to the commit being made. BROKEN entries (a
# registered script or evidence file is missing) still fail, because that is a real
# defect in the tree. Enforce the calendar in the scheduled run instead:
#   python tools/audit/audit_periodic_freshness.py     (no flag -> exit 1 when late)
echo "== periodic_freshness"
"$PYTHON" tools/audit/audit_periodic_freshness.py --warn-only \
  > "$OUT/periodic_freshness.md" 2> "$OUT/periodic_freshness.err" || failed=1
[ -s "$OUT/periodic_freshness.err" ] || rm -f "$OUT/periodic_freshness.err"

echo "== gen_damage_matrix"
"$PYTHON" tools/audit/gen_damage_matrix.py > "$OUT/damage_matrix.md" || failed=1
echo "== gen_rename_maps"
"$PYTHON" tools/audit/gen_rename_maps.py > "$OUT/naming.md" || failed=1
echo "== gen_faction_matrix"
MATRIX="docs/factions/MATRIX.md"
[ "$OUT" = "docs/audit/latest" ] || MATRIX="$OUT/MATRIX.md"
"$PYTHON" tools/audit/gen_faction_matrix.py > "$MATRIX" || failed=1

echo "reports in $OUT/ ; matrix in $MATRIX"
exit $failed
