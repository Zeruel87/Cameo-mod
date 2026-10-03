#!/usr/bin/env python3
"""Four-source armor-shape examples with Cameo's flat + max-HP terms.

Authored base weapon channels only. No combat/shot-to-kill certification or writeback.
"""
import argparse
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools/audit'))
from miniyaml import Ruleset
import percentage_damage as pd
import effective_heaviness as eh
from armor_projection import interpolate_vehicle_endpoints, four_voice_means

ACTORS = ('ra1_soviets_flametower', 'ra1_soviets_teslacoil', 'td_nod_obeliskoflight')
AXES = ('none', 'wood', 'concrete', 'scout', 'light', 'medium', 'heavy', 'superheavy')


def cameo_terms(weapon):
    terms = {a: {'flat': 0.0, 'max_hp_fraction': 0.0} for a in AXES}
    applications = pd.percentage_applications(weapon, 1)
    selected = []
    excluded = []
    for node in weapon.children:
        if node.value in ('AffectsIntegrity', 'DamagesConcrete'):
            excluded.append({'warhead': node.key, 'type': node.value,
                             'reason': 'integrity or terrain effect, outside the HP curve'})
            continue
        if node.value == 'FireShrapnel' or (node.get('Damage') and
                int(node.get('Damage')) > 0 and node.value not in ('AreaDamage', 'SpreadDamage') and
                'FriendlyFire' not in node.key):
            raise ValueError('Example has an additional unmodeled payload: ' + node.key)
        if node.value not in ('AreaDamage', 'SpreadDamage') or not node.get('Damage'):
            continue
        if 'FriendlyFire' in node.key:
            continue
        # These inspected weapons have one folded main plus optional flat chips.
        # This driver must not silently grow into an all-weapon selector.
        selected.append(node.key)
        h = eh.heaviness_of(node) if node.value == 'AreaDamage' else eh.DISABLED
        table = (pd.versus_table(node) if node.value == 'SpreadDamage' else
                 eh.shared_versus_profile(pd.versus_table(node), h)
                 if eh.heaviness_mode_of(node) == eh.MODE_SHARED else
                 eh.versus_profile(pd.versus_table(node), h))
        table = {a.lower(): v for a, v in table.items()}
        pct = next((p for p in applications if p['node'] is node), None)
        ptable = {a.lower(): v for a, v in pct['versus'].items()} if pct else {}
        for axis in AXES:
            terms[axis]['flat'] += int(node.get('Damage')) * table.get(axis, 100) / 100
            if pct:
                terms[axis]['max_hp_fraction'] += (pct['runtime_units'] / pct['denominator']
                                                     * ptable.get(axis, 100) / 100)
    if not 1 <= len(selected) <= 2 or len(applications) != 1:
        raise ValueError('Example baseline channel scope changed: ' + weapon.key)
    return terms, selected, excluded


def reference_curve(channels):
    totals = {a: 0.0 for a in ('none', 'wood', 'concrete', 'light', 'heavy')}
    if not channels:
        raise ValueError('missing selected reference channel')
    for channel in channels:
        damage = float(channel['damage'])
        table = {a.lower(): v for a, v in channel.get('resolved_versus',
                 channel.get('declared_versus', channel.get('versus', {}))).items()}
        fallback = channel.get('undeclared_armor_multiplier')
        fields = {k.lower(): v for k, v in channel.get('fields', {}).items()}
        center = float(fields.get('falloff', '100').split(',')[0]) / 100
        for axis in totals:
            coefficient = table.get(axis, fallback)
            if coefficient is None:
                raise ValueError('unresolved source armor: ' + axis)
            totals[axis] += damage * coefficient / 100 * center
    return {**{a: totals[a] for a in ('none', 'wood', 'concrete')},
            **{a: float(v) for a, v in interpolate_vehicle_endpoints(totals['light'], totals['heavy']).items()}}


def build(matrix, rules):
    rows = []
    for item in matrix['rows']:
        if item['actor'] not in ACTORS:
            continue
        slot = item['cameo_channels'][0]['slot']
        weapon = rules.resolve_weapon(rules.resolve(item['actor']).child(slot).get('Weapon'))
        terms, channels, excluded = cameo_terms(weapon)
        refs = {ref['source']: reference_curve(ref['selected_weapon_channels']) for ref in item['references']}
        if len(refs) != 3:
            raise ValueError('Exactly three external voices required')
        samples = []
        for hp in (10000, 100000, 1000000):
            curves = {'Current Cameo': {a: v['flat'] + hp * v['max_hp_fraction'] for a, v in terms.items()}, **refs}
            ratios = {s: {a: value / c['superheavy'] for a, value in c.items()} for s, c in curves.items()}
            samples.append({'cameo_target_max_hp': hp, 'ratios': ratios,
                            'means': {a: four_voice_means(ratios, ratios.keys(), a) for a in AXES}})
        rows.append({'actor': item['actor'], 'cameo_weapon': weapon.key,
                     'cameo_channels': channels, 'cameo_terms': terms,
                     'excluded_non_hp_channels': excluded,
                     'reference_nominal_curves': refs, 'samples': samples,
                     'additional_limitations': ['DTA Tesla adds zero railgun/particle HP damage under the reviewed OpenTS model; installed-binary applicability remains unverified.']
                     if item['actor'] == 'ra1_soviets_teslacoil' else []})
    if len(rows) != 3:
        raise ValueError('Missing requested defense example')
    return rows


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--matrix', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    rules = Ruleset(ROOT)
    matrix = json.loads(args.matrix.read_text())
    rows = build(matrix, rules)
    flame = next(r for r in rows if r['actor'] == 'ra1_soviets_flametower')
    assert flame['cameo_terms']['scout']['flat'] == 16380
    assert abs(flame['cameo_terms']['scout']['max_hp_fraction'] - 0.0117) < 1e-12
    assert flame['reference_nominal_curves']['Combined Arms']['scout'] == 15000
    tesla = next(r for r in rows if r['actor'] == 'ra1_soviets_teslacoil')
    assert tesla['cameo_terms']['none']['flat'] == 48800
    assert tesla['cameo_terms']['superheavy']['flat'] == 65600
    payload_path = ROOT / 'docs/reference/dta_tesla_payload_evidence.json'
    payload_proof = json.loads(payload_path.read_text())
    assert payload_proof['additional_hp_damage_under_reviewed_model'] == 0
    for field, filename in (('rules_sha256', 'Rules.ini'), ('enhance_sha256', 'Enhance.ini')):
        assert matrix['export_sha256']['DTA Enhanced'][field] == payload_proof['input_sha256'][filename]
    result = {'schema': 1, 'scope': 'Nominal base-weapon armor-shape examples; not full unit combat or an applied proposal.',
              'dta_tesla_payload_evidence_sha256': hashlib.sha256(payload_path.read_bytes()).hexdigest(),
              'current_weapon_inputs': {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
                                       for p in rules.manifest.weapons},
              'matrix_sha256': hashlib.sha256(args.matrix.read_bytes()).hexdigest(),
              'notes': ['Each source is one 25% voice after combining its selected authored flat channels.',
                        'Reference Light maps to Cameo Scout, Heavy to Superheavy; three intermediate positions are linearly interpolated.',
                        'DTA Light uses its actual BaseArmor inheritance, not a renamed Medium value.',
                        'Ratios normalize each source to its own Superheavy endpoint. This differs from the earlier main-channel Heavy comparison.',
                        'Cameo uses flat + max-HP terms with rounded folded units; final per-hit integer truncation is not modeled.',
                        'Single-armor basis, full center impact, base weapon main plus applicable flat chips; no incoming modifiers, shields, upgrades, integrity/terrain effects, status response, timing or overkill.',
                        'DTA coefficients follow reviewed Vinifera semantics; exact installed binary applicability remains unverified.',
                        'Arithmetic/geometric alternatives are shown separately; no blend or gameplay change is selected.'],
              'rows': rows}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'actors': len(rows), 'hp_scenarios_each': 3}))


if __name__ == '__main__':
    main()
