#!/usr/bin/env python3
"""Reference-projected nominal class anchors for review; never write the registry.

Uses fully covered original-unit projections as the initial calibration cohort.
Expanded units, sparse classes and full armor/state calibration remain separate.
"""
import argparse
import collections
import hashlib
import json
import math
from pathlib import Path
import statistics

import check_band
import class_membership
import derive_virtual_anchor as va
import diagnostic_output
import fit_class
import formula
import reference_distribution as rd
import reference_targets as rt

ROOT = Path(__file__).resolve().parents[2]
PREFIXES = ('td_gdi_', 'td_nod_', 'ra1_allies_', 'ra1_soviets_')
STATS = ('hp', 'speed', 'w_range', 'w_dps', 'cost')
PILOT_LEDGERS = ('shared_redalert', 'redalert_allies', 'redalert_soviets',
                 'shared_tiberiandawn', 'tiberiandawn_gdi', 'tiberiandawn_nod')

# R4 and fitting DPS are deliberately kept as separate observations.  R4's
# `armament_profile` sums positive damage warheads over the baseline armament
# set, while `fit_class.unit_inputs` applies the current main-channel reducer
# and actor firepower factors.  This tolerance only filters floating-point
# noise when reporting a numerical mismatch; it does not make the two metrics
# interchangeable or approve a conversion between them.
DPS_MISMATCH_REL_TOLERANCE = 1e-6
DPS_MISMATCH_ABS_TOLERANCE = 1e-9
DPS_BASIS_WARNING = (
    'UNAPPROVED cross-metric DPS comparison: R4 armament_profile sums positive '
    'damage warheads over baseline armaments with burst/cycle; current fitting '
    'uses the main-channel reducer. Values and ratios are '
    'diagnostic only and are not directly comparable.'
)


def finite_number(value):
    """Return a finite float, or None for missing/non-numeric input."""
    try:
        value = float(value)
    except (TypeError, ValueError):
        return None
    return value if math.isfinite(value) else None


def safe_ratio(numerator, denominator):
    """Return ``numerator / denominator`` when the denominator is usable.

    A missing, non-finite or zero denominator makes a ratio unavailable.  A
    zero numerator is retained as the meaningful ratio ``0.0``; negative DPS
    values are invalid and also return None.  Keeping the denominator in each
    output key makes the diagnostic readable without guessing its direction.
    """
    numerator = finite_number(numerator)
    denominator = finite_number(denominator)
    if numerator is None or denominator is None or numerator < 0 or denominator <= 0:
        return None
    return numerator / denominator


def mismatch_status(left, right):
    """True/False for a usable pair, otherwise None for an unavailable pair."""
    left, right = finite_number(left), finite_number(right)
    if left is None or right is None or left <= 0 or right <= 0:
        return None
    return not math.isclose(left, right,
                            rel_tol=DPS_MISMATCH_REL_TOLERANCE,
                            abs_tol=DPS_MISMATCH_ABS_TOLERANCE)


def dps_diagnostics(frozen_r4, current_r4, current_fitting, projected):
    """Describe the four DPS observations without changing any proposal input.

    ``frozen_r4`` is the immutable self-vote used by the existing R4 target;
    ``current_r4`` is the live R4 row; ``current_fitting`` is the reducer used
    to price the proposal; and ``projected`` is the existing R4 target.  The
    function is intentionally pure so callers can attach this evidence to a
    proposal while preserving all existing numerical fields.
    """
    values = {
        'frozen_r4_dps': finite_number(frozen_r4),
        'current_r4_dps': finite_number(current_r4),
        'current_fitting_dps': finite_number(current_fitting),
        'projected_dps': finite_number(projected),
    }
    ratios = {
        'current_r4_over_frozen_r4': safe_ratio(values['current_r4_dps'], values['frozen_r4_dps']),
        'current_fitting_over_frozen_r4': safe_ratio(values['current_fitting_dps'], values['frozen_r4_dps']),
        'projected_over_frozen_r4': safe_ratio(values['projected_dps'], values['frozen_r4_dps']),
        'current_fitting_over_current_r4': safe_ratio(values['current_fitting_dps'], values['current_r4_dps']),
        'projected_over_current_r4': safe_ratio(values['projected_dps'], values['current_r4_dps']),
        'projected_over_current_fitting': safe_ratio(values['projected_dps'], values['current_fitting_dps']),
    }
    mismatches = {
        'current_r4_vs_frozen_r4': mismatch_status(values['current_r4_dps'], values['frozen_r4_dps']),
        'current_r4_vs_current_fitting': mismatch_status(values['current_r4_dps'], values['current_fitting_dps']),
    }
    warnings = []
    if mismatches['current_r4_vs_frozen_r4']:
        warnings.append('CURRENT_R4_DIFFERS_FROM_FROZEN_R4_MAY_REFLECT_AUTHORIZED_FP_BAKE')
    if mismatches['current_r4_vs_current_fitting']:
        warnings.append('R4_VS_FITTING_MISMATCH_NOT_DIRECTLY_COMPARABLE')
    if any(value is None for value in ratios.values()):
        warnings.append('DPS_RATIO_UNAVAILABLE')
    return {
        **values,
        'basis_warning': DPS_BASIS_WARNING,
        'mismatch_tolerance': {
            'relative': DPS_MISMATCH_REL_TOLERANCE,
            'absolute': DPS_MISMATCH_ABS_TOLERANCE,
            'meaning': 'Only floating-point noise is tolerated; no cross-basis conversion is implied.',
        },
        'mismatches': mismatches,
        'ratios': ratios,
        'warnings': warnings,
    }


def class_warning_summary(contributors, thin):
    """Summarize review warnings while leaving contributor values untouched."""
    warning_counts = collections.Counter()
    residuals = []
    explicit_template_disagreements = 0
    for contributor in contributors:
        warning_counts.update(contributor.get('warnings') or [])
        residual = finite_number(contributor.get('relative_cost_residual'))
        if residual is not None:
            residuals.append(abs(residual))
        if contributor.get('explicit_template_disagreement'):
            explicit_template_disagreements += 1
    if thin:
        warning_counts['THIN_COHORT'] += 1
    warnings = sorted(warning_counts)
    return {
        'thin_cohort': bool(thin),
        'thin_threshold': 3,
        'warning_counts': dict(sorted(warning_counts.items())),
        'warnings': warnings,
        'explicit_template_disagreements': explicit_template_disagreements,
        'max_abs_cost_residual': max(residuals, default=None),
    }


def proposal_disposition(class_summary, contributor):
    """Route one per-unit proposal without approving or writing a value."""
    warnings = set(contributor.get('warnings') or [])
    class_warnings = set(class_summary.get('warnings') or [])
    if ('R4_VS_FITTING_MISMATCH_NOT_DIRECTLY_COMPARABLE' in class_warnings
            or class_summary.get('warning_counts', {}).get(
                'R4_VS_FITTING_MISMATCH_NOT_DIRECTLY_COMPARABLE', 0)):
        return 'HOLD_CLASS_DPS_METRIC_BASIS'
    if class_summary.get('explicit_template_disagreements'):
        return 'HOLD_CLASS_MEMBERSHIP'
    if class_summary.get('thin_cohort'):
        return 'HOLD_THIN_CLASS_COHORT'
    if 'R4_VS_FITTING_MISMATCH_NOT_DIRECTLY_COMPARABLE' in warnings:
        return 'HOLD_DPS_METRIC_BASIS'
    residual = finite_number(contributor.get('relative_cost_residual'))
    if residual is None or abs(residual) >= 0.25:
        return 'HOLD_CLASS_FIT_RESIDUAL'
    return 'REVIEWABLE_NO_AUTOMATIC_WRITE'


def direction_summary(current, target):
    """Describe proposal direction without treating small float noise as change."""
    result = {}
    for stat in STATS:
        left = finite_number((current or {}).get(stat))
        right = finite_number((target or {}).get(stat))
        if left is None or right is None:
            result[stat] = 'unresolved'
        elif math.isclose(left, right, rel_tol=0.01, abs_tol=1e-9):
            result[stat] = 'same'
        elif right > left:
            result[stat] = 'increase'
        else:
            result[stat] = 'decrease'
    return result


def complete_roster_rows(roster, units, candidates, excluded):
    """Retain every required actor, including rows outside the anchor cohort."""
    contributors = {row['actor']: (candidate, row)
                    for candidate in candidates
                    for row in candidate['contributors']}
    exclusions = {row['actor']: row for row in excluded}
    rows = []
    for actor, kind in sorted(roster.items()):
        unit = units.get(actor)
        if unit is None:
            rows.append({'actor': actor, 'type': kind,
                         'disposition': 'MISSING_LEDGER_ROW', 'target': None})
            continue

        def value(key):
            cell = unit.get(key)
            return finite_number(cell.get('v') if isinstance(cell, dict) else cell)

        cls, membership = class_membership.classify(unit.get('design') or {})
        row = {
            'actor': actor, 'type': kind, 'class': cls,
            'class_membership_basis': membership,
            'current': {'hp': value('hp'), 'speed': value('speed') or value('speed_air'),
                        'cost': value('cost')},
            'target': None, 'candidate_formula_price_10_grid': None,
            'writeback': False,
        }
        if actor in contributors:
            candidate, contributor = contributors[actor]
            review = contributor['proposal_review']
            row.update(current=contributor['current'], target=contributor['target'],
                       disposition=review['disposition'],
                       candidate_formula_price_10_grid=review['candidate_formula_price_10_grid'],
                       reason='Reference-complete anchor-cohort proposal; class sign-off and gameplay remain pending.',
                       external_source_counts=contributor['external_source_counts'])
        elif cls == 'support':
            row.update(disposition='SUPPORT_PRICE_EXEMPT',
                       reason='The support pricing exception applies; no combat formula target is invented.')
        elif value('cargo_capacity') and kind in ('veh', 'air', 'nav'):
            row.update(disposition='NAVAL_NO_INITIAL_LOAD' if kind == 'nav'
                       else 'CARGO_AWAITS_FINAL_PASSENGER_PRICES',
                       reason='No naval initial load/loaded-price valuation.' if kind == 'nav'
                       else 'Apply the passenger-sum rule after the selected infantry prices are settled.')
        elif check_band.band_exempt(unit):
            row.update(disposition='LIMITED_UNIT_SEPARATE_REVIEW',
                       reason='BuildLimit 1 is outside the ordinary anchor population; retain its separate hero/epic or support review.')
        elif value('cargo_capacity'):
            row.update(disposition='GARRISON_DEFENSE_SEPARATE_REVIEW',
                       reason='A garrison defense is outside this mobile-anchor cohort; its occupancy and pricing need explicit treatment.')
        elif kind == 'def':
            row.update(disposition='STATIC_DEFENSE_MODEL_REQUIRED',
                       reason='The mobile-anchor classifier excludes defenses. Use a reviewed HP/range/DPS defense model; no invented movement speed.')
        elif str((unit.get('design') or {}).get('subtype', '')).lower() == 'harvester':
            row.update(disposition='ECONOMY_MANUAL_REVIEW',
                       reason='Harvesters retain the economy/manual-review rule and do not need a combat DPS anchor.')
        elif cls is None and kind in ('air', 'nav'):
            row.update(disposition='AIR_OR_NAVAL_CLASS_DESIGN_REQUIRED',
                       reason='The actor has an air/naval role but no approved corresponding class in the current registry.')
        else:
            exclusion = exclusions.get(actor, {})
            reason = exclusion.get('reason') or 'No reference-complete proposal is available for this actor.'
            if cls is None:
                disposition = 'CLASS_MEMBERSHIP_REQUIRED'
            elif 'five calibration axes' in reason:
                disposition = 'SCALAR_REFERENCE_COVERAGE_REQUIRED'
            else:
                disposition = 'PRICING_INPUT_REVIEW_REQUIRED'
            row.update(disposition=disposition, reason=reason,
                       external_source_counts=exclusion.get('external_source_counts'))
        rows.append(row)
    return rows


def current_candidate_roster(root=ROOT):
    """Active four-faction combat/support roster, excluding superweapons."""
    from cameo_model import Model
    model = Model(root)
    roster, superweapons = {}, []
    for actor in sorted(model.rs.actors):
        if not actor.startswith(PREFIXES):
            continue
        node = model.rs.resolve(actor)
        if node is None or not model.is_buildable(node):
            continue
        kind = model.unit_type(actor)
        if kind not in ('inf', 'veh', 'air', 'nav', 'def'):
            continue
        if 'disabled' in model.positive_prereqs(node):
            continue
        prerequisites = (node.get('Buildable', 'Prerequisites') or '').lower()
        if any(token in prerequisites for token in rd.SUPERWEAPON_TOKENS):
            superweapons.append(actor)
            continue
        roster[actor] = kind
    units = {}
    for ledger in PILOT_LEDGERS:
        document = json.loads((root/'docs/balance'/(ledger+'.json')).read_text(encoding='utf-8'))
        for section in document.get('sections', {}).values():
            units.update(section)
    active_paths = set(model.rs.manifest.sources + model.rs.manifest.rules)
    hashes = {str(path.relative_to(root)): hashlib.sha256(path.read_bytes()).hexdigest()
              for path in sorted(active_paths)}
    return roster, units, {'active_rules_sha256': hashes,
                           'excluded_superweapons': superweapons}


def _display_number(value, digits=3):
    value = finite_number(value)
    return '—' if value is None else f'{value:,.{digits}f}'


def _display_ratio(value):
    value = finite_number(value)
    return '—' if value is None else f'{value:.3f}x'


def _display_percent(value):
    value = finite_number(value)
    return '—' if value is None else f'{value:.1%}'


def render_markdown(result):
    """Render a compact, review-oriented companion for one proposal JSON."""
    lines = [
        '# Reference anchor proposal review',
        '',
        '**UNAPPROVED diagnostic only.** The JSON proposal values and existing R4 contributors are carried through unchanged; this report adds review evidence and writes no registry or gameplay values.',
        '',
        '## Caveats',
        '',
        f'- {DPS_BASIS_WARNING}',
        '- Current-vs-frozen R4 differences may reflect an already-authorized firepower bake; they are not regression proof.',
        '- The mismatch tolerance is relative 1e-6 with absolute 1e-9 and only suppresses floating-point noise.',
        '- Equal DPS does not prove full combat equivalence: armor, range, accuracy, splash, burst timing, states and target access still matter.',
        '',
        '## Class summary',
        '',
        '| class | contributors | thin | HP0 | speed0 | range0 | DPS0 | C0 | max abs cost residual | explicit/template disagreements | warning counts |',
        '|---|---:|:---:|---:|---:|---:|---:|---:|---:|---:|---|',
    ]
    for candidate in result.get('candidates', []):
        summary = candidate.get('warning_summary') or {}
        counts = summary.get('warning_counts') or {}
        count_text = ', '.join(f'{key}={value}' for key, value in counts.items()) or 'none'
        spec = candidate.get('spec') or {}
        lines.append('| `{}` | {} | {} | {} | {} | {} | {} | {} | {} | {} | {} |'.format(
            candidate.get('class', '—'), candidate.get('contributor_count', 0),
            'yes' if summary.get('thin_cohort', candidate.get('thin')) else 'no',
            _display_number(spec.get('hp0'), 0), _display_number(spec.get('speed0'), 0),
            _display_number(spec.get('range0_wdist'), 0), _display_number(spec.get('dps0')),
            _display_number(spec.get('cost0'), 0),
            _display_percent(summary.get('max_abs_cost_residual')),
            summary.get('explicit_template_disagreements', 0), count_text))
    lines += [
        '',
        '## Contributors',
        '',
        '| class | actor | frozen R4 DPS | current R4 DPS | current fitting DPS | projected DPS | current/frozen | fitting/current R4 | warnings |',
        '|---|---|---:|---:|---:|---:|---:|---:|---|',
    ]
    for candidate in result.get('candidates', []):
        for contributor in candidate.get('contributors', []):
            dps = contributor.get('dps_diagnostics') or {}
            warnings = contributor.get('warnings') or []
            lines.append('| `{}` | `{}` | {} | {} | {} | {} | {} | {} | {} |'.format(
                candidate.get('class', '—'), contributor.get('actor', '—'),
                _display_number(dps.get('frozen_r4_dps')),
                _display_number(dps.get('current_r4_dps')),
                _display_number(dps.get('current_fitting_dps')),
                _display_number(dps.get('projected_dps')),
                _display_ratio((dps.get('ratios') or {}).get('current_r4_over_frozen_r4')),
                _display_ratio((dps.get('ratios') or {}).get('current_fitting_over_current_r4')),
                '<br>'.join(warnings) or 'none'))
    lines += [
        '',
        '## Per-unit proposal routing',
        '',
        '| class | actor | HP current→target | speed current→target | range current→target | nominal DPS current→target | cost current→reference | candidate formula price | disposition |',
        '|---|---|---:|---:|---:|---:|---:|---:|---|',
    ]
    for candidate in result.get('candidates', []):
        for contributor in candidate.get('contributors', []):
            current = contributor.get('current') or {}
            target = contributor.get('target') or {}
            review = contributor.get('proposal_review') or {}
            pair = lambda stat, digits=0: '{}→{}'.format(
                _display_number(current.get(stat), digits),
                _display_number(target.get(stat), digits))
            lines.append('| `{}` | `{}` | {} | {} | {} | {} | {} | {} | {} |'.format(
                candidate.get('class', '—'), contributor.get('actor', '—'),
                pair('hp'), pair('speed'), pair('w_range'), pair('w_dps', 3),
                pair('cost'),
                _display_number(review.get('candidate_formula_price_10_grid'), 0),
                review.get('disposition', 'UNRESOLVED')))
    if result.get('roster_rows'):
        coverage = result['roster_summary']
        lines += ['', '## Complete candidate roster', '',
                  f"All {coverage['required_actors']} active candidate actors are listed. Blank targets are deliberately unresolved or subject to a separate pricing rule; they are not zero prices.", '',
                  '| actor | type | class | current HP | current speed | current cost | proposal/disposition | reason |',
                  '|---|---|---|---:|---:|---:|---|---|']
        for row in result['roster_rows']:
            current = row.get('current') or {}
            lines.append('| `{}` | {} | {} | {} | {} | {} | {} | {} |'.format(
                row['actor'], row.get('type'), row.get('class') or '—',
                _display_number(current.get('hp'), 0), _display_number(current.get('speed'), 0),
                _display_number(current.get('cost'), 0), row['disposition'],
                row.get('reason', 'Ledger row missing').replace('|', '\\|')))
    lines += ['', 'All class candidates remain **UNAPPROVED**. Review warnings before any calibration or anchor decision.']
    return '\n'.join(lines) + '\n'


def snap(value, step):
    return max(step, math.floor(value / step + .5) * step)


def price(unit, derived, inputs, spec):
    # Reload=1 is only an algebraic adapter for the existing fitting API.
    # The proposal stores DPS directly; it does not invent an authored weapon.
    numeric = (spec['hp0'], spec['speed0'], spec['range0_wdist'], spec['dps0'], 1, spec['cost0'])
    return fit_class.virtual_price(unit, derived, inputs, numeric)


def fingerprints():
    paths = list((ROOT/'docs/reference').rglob('*.json'))
    paths += list((ROOT/'docs/reference').rglob('*.jsonl'))
    paths += list((ROOT/'docs/reference').rglob('*.yaml'))
    paths += list((ROOT/'tools/balance').glob('*.py'))
    legacy = ROOT/'docs/design/ORIGINAL_UNITS_PEER_OPENRA.md'
    if legacy.exists():
        paths.append(legacy)
    return {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(paths)}


def build():
    before = fingerprints()
    members, assignment, ledger_provenance = va.load_evidence(ROOT/'docs/balance')
    member_index = {m['actor']: m for m in members}
    assignment_doc = json.loads((ROOT/'docs/balance/derived/reference_assignment.json').read_text())
    peers = rd.peer_rows()
    dist = rd.build_distributions(peers)
    rt.add_cost_distribution(dist, peers)
    frozen = rt.cameo_context()
    attached = rt.expand_families(rt.attach(assignment, rt.peer_index(peers)), peers)
    groups, excluded = {}, []
    for current in rd.cameo_rows():
        actor = current['id']
        if not actor.startswith(PREFIXES):
            continue
        member = member_index.get(actor)
        if member is None:
            excluded.append({'actor': actor, 'reason': 'No eligible mapped class member'})
            continue
        unit = member['unit']
        cargo = unit.get('cargo_capacity')
        cargo = check_band.fnum(cargo.get('v') if isinstance(cargo, dict) else cargo) or 0
        if member['cls'] == 'support' or cargo > 0 or check_band.band_exempt(unit) or actor in assignment_doc.get('chassis_only', {}):
            excluded.append({'actor': actor, 'reason': 'Support/cargo/hero or chassis-only pricing scope'})
            continue
        if class_membership.is_folded(actor):
            excluded.append({'actor': actor, 'reason': 'Duplicate folded into parent'})
            continue
        refs = attached.get(actor, [])
        values = {s: rt.target_for(refs, current, s, dist, frozen) if refs else (None,None,0) for s in STATS}
        self_vote = frozen.cameo_votes.get(actor)
        complete = (self_vote is not None and all(values[s][1] is not None and values[s][2] >= 3
                    and rd.eligible(self_vote, s) for s in STATS))
        if not complete:
            excluded.append({'actor': actor, 'reason': 'Not full external-plus-frozen-self coverage on all five calibration axes',
                             'external_source_counts': {s: values[s][2] for s in STATS}})
            continue
        inputs = fit_class.unit_inputs(unit, member['derived'])[0]
        if inputs is None:
            excluded.append({'actor': actor, 'reason': 'No compatible nominal fitting inputs'})
            continue
        target = {s: values[s][1] for s in STATS}
        projected = (target['hp'], target['speed'], target['w_range'], target['w_dps'], *inputs[4:])
        implied = class_membership.subtype_to_anchor((unit.get('design') or {}).get('subtype'))
        design = unit.get('design') or {}
        explicit = design.get('class_anchor')
        dps = dps_diagnostics((self_vote or {}).get('w_dps'), current.get('w_dps'),
                              inputs[3], target['w_dps'])
        contributor_warnings = list(dps['warnings'])
        explicit_template_disagreement = bool(explicit and implied and explicit != implied)
        if explicit_template_disagreement:
            contributor_warnings.append('EXPLICIT_CLASS_DISAGREES_WITH_TEMPLATE')
        groups.setdefault(member['cls'], []).append({'actor': actor, 'target': target,
            'current': {stat: current.get(stat) for stat in STATS},
            'projected_inputs': projected, 'unit': unit, 'derived': member['derived'],
            'template_class': implied, 'explicit_class': member['cls'],
            'explicit_class_tag': explicit,
            'external_source_counts': {s: values[s][2] for s in STATS},
            'dps_diagnostics': dps, 'warnings': sorted(set(contributor_warnings)),
            'explicit_template_disagreement': explicit_template_disagreement})
    candidates = []
    for cls, group in sorted(groups.items()):
        median = lambda stat: statistics.median(m['target'][stat] for m in group)
        # Grids come from formula.STAT_GRID, never re-literalised here: range used to be
        # snapped to 10 WDist in this line alone, which no other file knew about.
        G = formula.STAT_GRID
        spec = {'hp0': snap(median('hp'), G['hp']), 'speed0': snap(median('speed'), G['speed']),
                'range0_wdist': snap(median('w_range'), G['range_wdist']),
                'dps0': median('w_dps'), 'cost0': 1}
        cost_normalizers = []
        for m in group:
            factor = price(m['unit'], m['derived'], m['projected_inputs'], spec)
            if not math.isfinite(factor) or factor <= 0:
                raise ValueError('Invalid price normalizer: ' + m['actor'])
            cost_normalizers.append(m['target']['cost'] / factor)
        raw_c0 = statistics.median(cost_normalizers)
        spec['cost0'] = snap(raw_c0, G['cost'])
        base = (spec['hp0'], spec['speed0'], spec['range0_wdist'], spec['dps0'], 1, 1, 1)
        verifier = (2*base[0], base[1], base[2], 2*base[3], 1, 1, 1)
        baseline_price, verifier_price = price({}, {}, base, spec), price({}, {}, verifier, spec)
        assert math.isclose(baseline_price, spec['cost0'])
        assert math.isclose(verifier_price, 2.5*spec['cost0'])
        proposals = []
        for m in group:
            estimate = price(m['unit'], m['derived'], m['projected_inputs'], spec)
            proposals.append({k:v for k,v in m.items() if k not in ('unit','derived')}
                             | {'candidate_price_at_projected_stats': estimate,
                                'relative_cost_residual': estimate/m['target']['cost']-1})
        warning_summary = class_warning_summary(proposals, len(group) < 3)
        for proposal in proposals:
            proposal['proposal_review'] = {
                'disposition': proposal_disposition(warning_summary, proposal),
                'candidate_formula_price_10_grid': snap(
                    proposal['candidate_price_at_projected_stats'], 10),
                'direction': direction_summary(
                    proposal.get('current'), proposal.get('target')),
                'meaning': ('Reference-projected inputs and candidate class formula are '
                            'review evidence only; no actor or anchor write is authorized.'),
            }
        candidates.append({'class': cls, 'status': 'UNAPPROVED', 'contributor_count': len(group),
            'thin': len(group)<3, 'spec': spec, 'unsnapped_cost0': raw_c0,
            'baseline_identity': baseline_price, 'verifier_250_percent': verifier_price,
            'warning_summary': warning_summary, 'contributors': proposals})
    roster, all_units, roster_evidence = current_candidate_roster()
    roster_rows = complete_roster_rows(roster, all_units, candidates, excluded)
    roster_summary = {
        'required_actors': len(roster), 'reported_actors': len(roster_rows),
        'disposition_counts': dict(sorted(collections.Counter(row['disposition'] for row in roster_rows).items())),
    }
    if fingerprints() != before or va.input_fingerprints(ROOT/'docs/balance') != ledger_provenance:
        raise ValueError('Calibration inputs changed during collection')
    return {'schema':1, 'scope':'Unapproved nominal class-anchor proposals from existing reference projections; no registry or gameplay writeback.',
        'method':['Use the existing per-source reference projection and frozen Cameo self-vote; require full external coverage on HP, speed, range, nominal DPS and cost.',
                  'Use medians of projected HP/speed/range/DPS, with existing stat grids. Store DPS directly, not a synthetic weapon damage/reload target.',
                  'Fit class C0 from projected costs after current fitting tier/feature factors; snap C0 to 100 credits.',
                  'Current charge/physical-state factors are held fixed during this initial proposal and require iteration after any stat changes.',
                  'Thin classes and explicit/template disagreements are exposed, not silently repaired or signed off.',
                  'R4 DPS and current fitting DPS use different reducers; cross-metric ratios are diagnostic only, with a tight 1e-6 relative / 1e-9 absolute mismatch tolerance.',
                  'Excluded expanded/sparse units still require calibration; this initial reference-complete cohort is not the full deliverable.'],
        'dps_basis': {'r4': 'armament_profile sums all positive damage warheads over baseline armaments with burst/cycle.',
                      'current_fitting': 'fit_class.unit_inputs uses the current main-channel reducer and actor firepower factors.',
                      'cross_metric_status': 'UNAPPROVED — mismatches are not directly comparable.',
                      'mismatch_tolerance': {'relative': DPS_MISMATCH_REL_TOLERANCE,
                                             'absolute': DPS_MISMATCH_ABS_TOLERANCE}},
        'summary': {'classes':len(candidates),'contributors':sum(c['contributor_count'] for c in candidates),
                    'classes_with_at_least_three_contributors':sum(not c['thin'] for c in candidates),
                    'classes_with_warnings':sum(bool(c['warning_summary']['warnings']) for c in candidates),
                    'dps_basis_mismatch_contributors':sum(
                        c['warning_summary']['warning_counts'].get('R4_VS_FITTING_MISMATCH_NOT_DIRECTLY_COMPARABLE', 0)
                        for c in candidates),
                    'excluded':len(excluded)},
        'reference_and_tool_inputs': before, 'ledger_inputs': ledger_provenance,
        'candidates': candidates, 'excluded': excluded,
        'roster_summary': roster_summary, 'roster_evidence': roster_evidence,
        'roster_rows': roster_rows}


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',type=Path,required=True)
    parser.add_argument('--markdown', type=Path,
                        help='optional readable review companion (.md)')
    args=parser.parse_args(argv)
    try:
        json_path = diagnostic_output.validate_path(ROOT, args.out)
        markdown_path = (diagnostic_output.validate_path(ROOT, args.markdown)
                         if args.markdown else None)
        # Check after resolving both paths and before constructing the output
        # mapping: a normal dict would otherwise silently collapse aliases.
        if markdown_path is not None and markdown_path == json_path:
            raise ValueError('JSON and Markdown diagnostics must use different resolved output paths')
    except ValueError as error:
        parser.error(str(error))
    result=build()
    json_text = json.dumps(result, indent=2, allow_nan=False) + '\n'
    outputs = {json_path: json_text}
    if markdown_path is not None:
        outputs[markdown_path] = render_markdown(result)
    try:
        diagnostic_output.write_outputs(ROOT, outputs)
    except (OSError, ValueError) as error:
        parser.error(str(error))
    print(json.dumps(result['summary']))


if __name__ == '__main__':
    main()
