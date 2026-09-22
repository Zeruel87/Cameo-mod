"""Exact, test-only reconciliation of independently reviewed upstream changes.

Never used by a converter. Assert modern values, reverse only the enumerated
delta in a copy, then let the ORIGINAL historical fingerprints check everything
else, including child order. No live data or stored fingerprints are rewritten.
"""
from miniyaml import Node
import json
import hashlib
from functools import lru_cache
import pathlib
import sys

ENDPOINT_COHORT = {
    'NaxiHetzerDestroyer', 'NaxiHetzerDestroyer_elite', 'NaxiHetzerDestroyerCorrosion',
    'NaxiAntiTankCannon', 'NaxiAntiTankCannon_elite', 'NaxiAntiTankCannonCorrosion',
    'RA2120xmm', 'RA2120xmm_elite',
}
EXTENDED_ENDPOINTS = {'AlliedTankDestroyerCannon', 'SkyHawkCannon', 'TSLaser90mm', 'TSLaser90mmDep', '2Inch'}
ORDOS_ENDPOINTS = {'120mm_cobra', '120mm_cobra_deploy', '120mm_python', '120mm_python_deploy'}
ALL_ENDPOINTS = ENDPOINT_COHORT | EXTENDED_ENDPOINTS | ORDOS_ENDPOINTS


OWNED_GUNBOAT = 'ra1_allies_gunboat_cannon'

# Exact PR340 routes in converter_owned_names_20260910.json. These three
# identities intersect the later trajectory/profile checkpoints below.
LATER_OWNED_NAMES = {
    'BlackHandLaser': 'td_nod_lasertrooper_blackhandlaser',
    'HindMissilesThermobaric': 'ra1_soviets_hindattackhelicopter_hindmissilesthermobaric',
    'ThermobaricMaverick': 'ra1_soviets_migattackbomber_thermobaricmaverick',
}
LATER_HISTORICAL_NAMES = {new: old for old, new in LATER_OWNED_NAMES.items()}


@lru_cache(maxsize=1)
def owned_checkpoint_history():
    """Pinned, test-only bridges from owner-renaming checkpoints to current rules."""
    path = pathlib.Path(__file__).parent / 'fixtures' / 'owned_checkpoint_history_20260914.json'
    data = json.loads(path.read_text(encoding='utf-8'))
    if data.get('schema') != 1:
        raise AssertionError('unsupported owned-checkpoint history schema')
    return data['cohorts']


def _ordered_node(node):
    return [node.key, node.value, [_ordered_node(child) for child in node.children]]


def _rebuild_node(row, file=''):
    return Node(row[0], row[1], [_rebuild_node(child, file) for child in row[2]], file)


def restore_owned_checkpoint_node(test, cohort, kind, node):
    """Assert an exact modern node, then expose its reviewed post-owner checkpoint."""
    record = owned_checkpoint_history()[cohort][kind].get(node.key)
    if record is None:
        return node
    digest = hashlib.sha256(json.dumps(_ordered_node(node),
                            separators=(',', ':')).encode()).hexdigest()
    test.assertEqual(record['current_hash'], digest, (cohort, kind, node.key))
    return _rebuild_node(record['checkpoint'], node.file)


def restore_owned_checkpoint_actor(test, rules, cohort, actor):
    """Reverse only the recorded post-owner actor changes in a validated copy."""
    from dump_resolved import node_to_obj
    obj = node_to_obj(rules.resolve(actor))
    record = owned_checkpoint_history()[cohort]['resolved_actors'][actor]
    digest = hashlib.sha256(json.dumps(obj, sort_keys=True,
                            separators=(',', ':')).encode()).hexdigest()
    test.assertEqual(record['current_hash'], digest, (cohort, actor))
    restored = json.loads(json.dumps(obj))
    missing = {'__owned_history_missing__': True}
    for change in record['changes']:
        parent = restored
        for key in change['path'][:-1]:
            parent = parent[key]
        key = change['path'][-1]
        current = parent.get(key, missing)
        test.assertEqual(change['current'], current, (cohort, actor, change['path']))
        if change['checkpoint'] == missing:
            parent.pop(key)
        else:
            parent[key] = change['checkpoint']
    return restored


class OwnedCheckpointView:
    """Ruleset facade for tests frozen at one reviewed owner-renaming checkpoint."""
    def __init__(self, test, rules, cohort):
        self.test, self.rules, self.cohort = test, rules, cohort

    def __getattr__(self, key):
        return getattr(self.rules, key)

    def weapon(self, name):
        node = self.rules.weapon(name)
        return (None if node is None else
                restore_owned_checkpoint_node(self.test, self.cohort, 'source_weapons', node))

    def resolve_weapon(self, name):
        node = self.rules.resolve_weapon(name)
        return (None if node is None else
                restore_owned_checkpoint_node(self.test, self.cohort, 'resolved_weapons', node))


@lru_cache(maxsize=1)
def r12_inverse_name_map():
    """Exact landed R12 name map, inverted for historical test fixtures only."""
    proof = json.loads((pathlib.Path(__file__).parents[2] / 'docs' / 'audit' / 'latest' /
                        'r12_pure_rename_proof_20260913.json').read_text(encoding='utf-8'))
    inverse = {new: old for old, new in proof['template_renames'].items()}
    for old, new in proof['payload_renames'].items():
        inverse['Warhead@' + new] = 'Warhead@' + old
        inverse['-Warhead@' + new] = '-Warhead@' + old
    return inverse


def restore_r12_names(node):
    """Return a copy with only the approved R12 template/payload rename reversed."""
    inverse = r12_inverse_name_map()
    copy = node.deep_copy()

    def restore(current):
        current.key = inverse.get(str(current.key), current.key)
        current.value = inverse.get(str(current.value or '').strip(), current.value)
        for child in current.children:
            restore(child)

    restore(copy)
    return copy


@lru_cache(maxsize=1)
def r12_forward_name_map():
    return {old: new for new, old in r12_inverse_name_map().items()}


def current_profile_name(rules, name):
    return name if name in rules.weapons else LATER_OWNED_NAMES.get(name, name)


def current_endpoint_name(rules, name):
    """Resolve the exact ownership rename without changing historical fixtures."""
    return OWNED_GUNBOAT if name == '2Inch' and name not in rules.weapons else name


def restore_endpoint_weapon(test, node):
    """Validate the exact h0 replacement, then restore the ordered historical view."""
    node = restore_target_policy_fields(test, node)
    from dump_resolved import node_to_obj
    from miniyaml import load_text
    historical_name = '2Inch' if node.key == OWNED_GUNBOAT else node.key
    directory = pathlib.Path(__file__).parent / 'fixtures'
    filename = ('cannonap_extended_before_20260910.json' if historical_name in EXTENDED_ENDPOINTS else
                'cannonap_ordos_before_20260910.json' if node.key in ORDOS_ENDPOINTS else
                'cannonap_endpoint_before_20260910.json')
    fixture = json.loads((directory / filename).read_text(encoding='utf-8'))
    def rebuild(row):
        return Node(row[0], row[1], [rebuild(c) for c in row[2]])
    before = rebuild(fixture['weapons'][historical_name])
    generated = load_text((directory / 'cannonap_continuous_generated.yaml').read_text(encoding='utf-8'))[0]
    old_tag = ('Warhead@CannonAP_LightFlatCompatibility' if node.key in ORDOS_ENDPOINTS else
               'Warhead@CannonAP_Medium' if node.key.startswith('TSLaser90mm') else
               'Warhead@CannonAP_Light')
    main = before.child(old_tag).deep_copy()
    main.key = 'Warhead@CannonAP'
    profile = {'Versus', 'PercentageVersus', 'PercentageVersusLight', 'PercentageVersusHeavy',
               'Spread', 'Heaviness', 'HeavinessMode', 'PercentageScale'}
    main.children = [n for n in main.children if n.key not in profile]
    main.children += [n.deep_copy() for n in generated.child('Warhead@CannonAP').children if n.key in profile]
    main.child('Heaviness').value = '1000' if node.key.startswith('TSLaser90mm') else '0'
    if historical_name == '2Inch':
        main.child('Spread').value = '450'
    test.assertEqual(
        [n.key.replace(old_tag, 'Warhead@CannonAP') for n in before.children
         if n.key.startswith('Warhead@')],
        [n.key for n in node.children if n.key.startswith('Warhead@')], node.key)
    expected = node_to_obj(before)
    expected.pop(old_tag)
    expected['Warhead@CannonAP'] = node_to_obj(main)
    test.assertEqual(expected, node_to_obj(node), node.key)
    before.key = node.key
    return before


def restore_freedom_elite(test, node):
    """Assert the exact new contract before presenting the frozen old converter view."""
    from dump_resolved import node_to_obj
    from miniyaml import load_text
    sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / 'balance'))
    from consolidate_rule_driven_energy_ordnance import companion_lines
    fixture = json.loads((pathlib.Path(__file__).parent / 'fixtures' /
                          'freedom_elite_before_20260910.json').read_text(encoding='utf-8'))
    def rebuild(row):
        return Node(row[0], row[1], [rebuild(c) for c in row[2]])
    before = rebuild(fixture['ordered_weapon'])
    expected = node_to_obj(before)
    expected.pop('Warhead@MissileAP_MediumFlatCompatibility')
    expected['Warhead@MissileAP_Medium']['Damage'] = '360000'
    expected['Warhead@MissileAP_Medium']['PercentageScale'] = '0'
    source = before.child('Warhead@MissileAP_Medium')
    text = 'Weapon:\n' + ''.join(companion_lines(source, 'FreedomElitePreservedPercentage',
                                               {'units': 6000, 'denominator': 10000}))
    companion = load_text(text)[0].children[0]
    companion.child('Falloff').value = '100, 50, 0'
    companion.child('Range').value = '0, 32, 33'
    expected[companion.key] = node_to_obj(companion)
    # Removing the compatibility parent leaves every surviving inherited event
    # in its original position; the explicit companion is appended by the elite.
    expected_order = [n.key for n in before.children if n.key.startswith('Warhead@')
                      and n.key != 'Warhead@MissileAP_MediumFlatCompatibility']
    expected_order.append(companion.key)
    test.assertEqual(expected_order,
                     [n.key for n in node.children if n.key.startswith('Warhead@')])
    test.assertEqual(expected, node_to_obj(node))
    return before

# e1ab9bb26 removed duplicate singular bindings; the map already applies100.
CORROSION_CLEANUP = {
    "AsianChemical": ("LightChemicalWeaponPercentage", "MediumChemicalWeaponPercentage", "HeavyChemicalWeaponPercentage"),
    "AsianHarbingerPlasma": ("LightChemicalWeaponPercentage", "MediumChemicalWeaponPercentage"),
    "FutureMechPlasma": ("MediumChemicalWeaponPercentage",),
    "td_nod_specterartillery_specterartilleryshellupgrade": ("MediumChemicalWeaponPercentage",),
    "SteelQuantumTurretRail": ("HeavyChemicalWeaponPercentage",),
    "WyvernRockets": ("MediumChemicalWeaponPercentage",),
    "PhobosLaser": ("HeavyChemicalWeaponPercentage",),
    "FutureMechPlasma_elite": ("MediumChemicalWeaponPercentage",),
    "AsianChemical_elite": ("LightChemicalWeaponPercentage", "MediumChemicalWeaponPercentage", "HeavyChemicalWeaponPercentage"),
    "SteelQuantumTurretRail_EMP": ("HeavyChemicalWeaponPercentage",),
}

# path, historical value, authored current value. b905d7679 regenerated coupling
# columns; a92ae850f removed LatinSmoker's trailing medium-cannon inheritance.
FIELD_CHANGES = {
    "AAGunBoatFlak": (
        (("Warhead@Flak_Medium", "Versus", "BLAST"), "58", "57"),
        (("Warhead@Flak_Medium", "Versus", "Shield"), "171", "172"),
    ),
    "AAGunBoatFlak_elite": (
        (("Warhead@Flak_Medium", "Versus", "BLAST"), "58", "57"),
        (("Warhead@Flak_Medium", "Versus", "Shield"), "171", "172"),
    ),
    "RA2FlakTrackAAGun": (
        (("Warhead@Flak_Medium", "Versus", "BLAST"), "58", "57"),
        (("Warhead@Flak_Medium", "Versus", "Shield"), "171", "172"),
    ),
    "RA2FlakTrackAAGun_elite": (
        (("Warhead@Flak_Medium", "Versus", "BLAST"), "58", "57"),
        (("Warhead@Flak_Medium", "Versus", "Shield"), "171", "172"),
    ),
    "RA2FlakTrackGun": (
        (("Warhead@Flak_Medium", "Versus", "BLAST"), "58", "57"),
        (("Warhead@Flak_Medium", "Versus", "Shield"), "171", "172"),
    ),
    "TeslaArmorDischargeArc": (
        (("Warhead@MissileAP_Light", "Versus", "COMPOSITE"), "44", "45"),
    ),
    "TeslaArmorDischargeFragment1": (
        (("Warhead@MissileAP_Light", "Versus", "COMPOSITE"), "44", "45"),
    ),
    "TeslaArmorDischargeFragment2": (
        (("Warhead@MissileAP_Light", "Versus", "COMPOSITE"), "44", "45"),
    ),
    "GrenadeRA": (
        (("Warhead@Demolition_Light", "Versus", "COMPOSITE"), "101", "102"),
    ),
    "ASDFKamikazeExplosion": (
        (("Warhead@Demolition_Heavy", "Versus", "COMPOSITE"), "101", "102"),
        (("Warhead@Demolition_Heavy", "Versus", "Shield"), "177", "178"),
    ),
    "AsianHowitzerCannon": (
        (("Warhead@CannonHE_Heavy", "Versus", "BLAST"), "40", "39"),
        (("Warhead@CannonHE_Heavy", "Versus", "COMPOSITE"), "99", "100"),
        (("Warhead@CannonHE_Heavy", "Versus", "Shield"), "168", "169"),
    ),
    "AsianHowitzerCannon_elite": (
        (("Warhead@CannonHE_Heavy", "Versus", "BLAST"), "40", "39"),
        (("Warhead@CannonHE_Heavy", "Versus", "COMPOSITE"), "99", "100"),
        (("Warhead@CannonHE_Heavy", "Versus", "Shield"), "168", "169"),
    ),
    "ra1_soviets_molotovconscript_conscriptmolotov": (
        (("Warhead@Flame_Light", "Versus", "COMPOSITE"), "76", "77"),
        (("Warhead@Flame_Light", "Versus", "Shield"), "205", "208"),
    ),
    "TSBusMortar": (
        (("Warhead@Concussion_Medium", "Versus", "COMPOSITE"), "106", "107"),
    ),
    "tkm_trooper_gp25": (
        (("Warhead@Demolition_Light", "Versus", "COMPOSITE"), "101", "102"),
    ),
    "RA2FreedomRocket": (
        (("Warhead@MissileAP_Medium", "Versus", "COMPOSITE"), "44", "45"),
    ),
    "RA2FreedomRocket_elite": (
        (("Warhead@MissileAP_Medium", "Versus", "COMPOSITE"), "44", "45"),
    ),
    "PositronBounce1": (
        (("Warhead@CannonHE_Medium", "Versus", "BLAST"), "40", "39"),
        (("Warhead@CannonHE_Medium", "Versus", "COMPOSITE"), "99", "100"),
    ),
    "PositronBounce2": (
        (("Warhead@CannonHE_Medium", "Versus", "BLAST"), "40", "39"),
        (("Warhead@CannonHE_Medium", "Versus", "COMPOSITE"), "99", "100"),
    ),
    "TS155mm_bluenuke": (
        (("Warhead@Concussion_Medium", "Versus", "COMPOSITE"), "106", "107"),
        (("Warhead@Demolition_Heavy", "Versus", "COMPOSITE"), "101", "102"),
        (("Warhead@Demolition_Heavy", "Versus", "Shield"), "177", "178"),
    ),
    "RA2KirovHowitzerSplash": (
        (("Warhead@Concussion_Medium", "Versus", "COMPOSITE"), "106", "107"),
    ),
    "LatinSmokerCannon": (
        (("Warhead@Concrete", "Damage"), "150", "200"),
        (("Warhead@Effect", "Explosions"), "ra2_medium_explosion", "ra2_large_grey_explosion"),
        (("Warhead@Effect", "ImpactSounds"), "gexp14a.wav", "kaboom15.aud"),
        (("Warhead@EffectAir", "Explosions"), "med_explosion_air", "big_explosion_air"),
        (("Warhead@Glow", "FadeFrames"), "10", "15"),
        (("Warhead@Glow", "Scale"), "0.55", "0.8"),
        (("Warhead@ShieldHit", "Duration"), "10", "12"),
    ),
}


@lru_cache(maxsize=1)
def trajectory_changes():
    rollout = json.loads((pathlib.Path(__file__).resolve().parents[2] /
                          'docs/audit/missile-trajectory-rollout.json').read_text(encoding='utf-8'))
    digest = hashlib.sha256(json.dumps(rollout, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
    if digest != '4f29f189969ff26e80666561572c4530ab51558443925ceae0dec912b71ef697':
        raise AssertionError('published9a80607fe trajectory evidence changed')
    return {row['weapon']: row['fields'] for row in rollout['changes']}


@lru_cache(maxsize=1)
def target_policy_field_changes():
    return json.loads((pathlib.Path(__file__).parent / 'fixtures' /
                       'target_policy_field_history_20260910.json').read_text(encoding='utf-8'))


@lru_cache(maxsize=1)
def sonic_family_changes():
    return json.loads((pathlib.Path(__file__).parent / 'fixtures' /
                       'sonic_family_history_20260910.json').read_text(encoding='utf-8'))


@lru_cache(maxsize=1)
def missile_role_changes():
    return json.loads((pathlib.Path(__file__).parent / 'fixtures' /
                       'missile_role_history_20260910.json').read_text(encoding='utf-8'))


@lru_cache(maxsize=1)
def missile_parent_role_changes():
    return json.loads((pathlib.Path(__file__).parent / 'fixtures' /
                       'missile_parent_role_history_20260910.json').read_text(encoding='utf-8'))


def restore_missile_role(test, node, source=False):
    """Validate the complete new role checkpoint before exposing its predecessor."""
    def ordered(n):
        return [n.key, n.value, [ordered(c) for c in n.children]]
    def rebuild(row):
        return Node(row[0], row[1], [rebuild(c) for c in row[2]])
    copy = node.deep_copy()
    for history in (missile_parent_role_changes(), missile_role_changes()):
        record = history.get(copy.key)
        if record is None:
            continue
        digest = hashlib.sha256(json.dumps(ordered(copy), separators=(',', ':')).encode()).hexdigest()
        test.assertEqual(record['source_current_hash' if source else 'current_hash'], digest, copy.key)
        copy = rebuild(record['source_before' if source else 'before'])
    return copy


@lru_cache(maxsize=1)
def secondary_target_policy_changes():
    return json.loads((pathlib.Path(__file__).parent / 'fixtures' /
                       'secondary_target_policy_history_20260910.json').read_text(encoding='utf-8'))


def restore_secondary_target_policy(test, node):
    record = secondary_target_policy_changes().get(node.key)
    if record is None:
        return node
    def ordered(n):
        return [n.key, n.value, [ordered(c) for c in n.children]]
    def rebuild(row):
        return Node(row[0], row[1], [rebuild(c) for c in row[2]])
    digest = hashlib.sha256(json.dumps(ordered(node), separators=(',', ':')).encode()).hexdigest()
    test.assertEqual(record['current_hash'], digest, node.key)
    return rebuild(record['before'])


def restore_sonic_family(test, node):
    """Restore only the exact pre-Sonic-family checkpoint in a test copy."""
    copy = restore_secondary_target_policy(test, restore_missile_role(test, node))
    sonic = sonic_family_changes()
    if node.key in sonic:
        def ordered(n):
            return [n.key, n.value, [ordered(c) for c in n.children]]
        test.assertEqual(sonic[node.key]['current'], ordered(node), node.key)
        def rebuild(row):
            return Node(row[0], row[1], [rebuild(c) for c in row[2]])
        copy = rebuild(sonic[node.key]['before'])
    return copy


def restore_target_policy_fields(test, node):
    """Assert current target masks; restore only exact recorded historical fields."""
    copy = restore_sonic_family(test, node)
    if node.key == 'SCDevourerAA':
        cloud = copy.child('Warhead@Cloud').child('Weapon')
        test.assertEqual('sc_zerg_devourer_acidcloud_aa', cloud.value)
        cloud.value = 'AnthraxCloudPurpleLarge'
    if node.key == 'RA2PatriotThunderboltMissile':
        damage = copy.child('Warhead@MissileAA_Heavy').child('Damage')
        test.assertEqual('12100', damage.value, node.key)
        damage.value = '10000'
    # Aedis's delivery-first rename is numerical/behavioral identity. Keep old
    # converter fingerprints intact, including their historical warhead names.
    if node.key in {
        'ra1_allies_cargoplanebomber_parabombcryo', 'DepthChargeCryo',
        'ra1_allies_cruiser_8inchcryo', 'ra1_allies_longbow_missile_cryo',
        'ra1_allies_rapierjumpjet_bomb_cryo', 'ra1_allies_rapierjumpjet_missile_cryo_AA',
        'ra1_allies_gunboat_depthchargecryo', 'ra1_allies_destroyer_depthchargecryo',
    }:
        for child in copy.children:
            if child.key.startswith('Warhead@BlastCryo_'):
                child.key = child.key.replace('Warhead@BlastCryo_', 'Warhead@CryoBlast_', 1)
    for tag, key, before, after in target_policy_field_changes().get(node.key, ()):
        warhead = copy.child(tag)
        if warhead is None:
            warhead = copy.child(r12_forward_name_map().get(tag, tag))
        test.assertIsNotNone(warhead, (node.key, tag))
        field = warhead.child(key)
        test.assertEqual(after, field.value if field else None, (node.key, tag, key))
        if before is None:
            warhead.children = [c for c in warhead.children if c.key != key]
        elif field is not None:
            field.value = before
        else:
            raise AssertionError(('unexpected removed historical field', node.key, tag, key))
    return copy


@lru_cache(maxsize=1)
def full_air_payload_changes():
    """The reviewed full-air payload mask additions (three dual-target leaves)."""
    return json.loads((pathlib.Path(__file__).parent / 'fixtures' /
                       'dual_target_payload_history_20260910.json').read_text(encoding='utf-8'))


def restore_full_air_payload(test, node):
    """Assert the reviewed mask additions, then reverse ONLY those in a test copy.

    Test-only reconciliation, same contract as the other reviewed upstream deltas
    here: the production converter's preserved fingerprint and its expected hashes
    are untouched and still see the pre-review value.
    """
    record = full_air_payload_changes()['changed_fields'].get(node.key)
    if not record:
        return node
    copy = node.deep_copy()
    for path, before, after in record:
        keys = [part for part in path.split('/') if part]
        parent = copy
        for key in keys[:-1]:
            parent = parent.child(key)
            test.assertIsNotNone(parent, (node.key, path))
        field = keys[-1]
        current = parent.child(field)
        test.assertEqual(after, current.value if current is not None else None, (node.key, path))
        if before is None:
            parent.children = [c for c in parent.children if c.key != field]
        elif current is not None:
            current.value = before
        else:
            parent.children.append(Node(field, before))
    return copy


def historical_copy(test, node):
    if node.key in ALL_ENDPOINTS or node.key == OWNED_GUNBOAT:
        node = restore_endpoint_weapon(test, node)
    else:
        node = restore_target_policy_fields(test, node)
    node = restore_full_air_payload(test, node)
    if node.key == 'RA2FreedomRocket_elite':
        node = restore_freedom_elite(test, node)
    copy = node.deep_copy()
    # Blackrobe's9a80607fe trajectory rollout is independent of older profile
    # converters. Reverse only its exact recorded scalar deltas in this test view.
    changes = trajectory_changes().get(LATER_HISTORICAL_NAMES.get(node.key, node.key), {})
    if changes:
        projectile = copy.child('Projectile')
        test.assertEqual('Missile', projectile.value, node.key)
        for key, change in changes.items():
            field = projectile.child(key)
            test.assertIsNotNone(field, (node.key, key))
            test.assertEqual(change['after'], field.value, (node.key, key))
            field.value = change['before']
    if node.key == "TSPulseCannon_EMP":
        # 9bfee2b85 removed an unused field from AffectsIntegrity, not damage.
        warhead = copy.child("Warhead@2Con")
        test.assertEqual("AffectsIntegrity", warhead.value)
        test.assertIsNone(warhead.child("Falloff"))
        test.assertEqual("ValidTargets", warhead.children[0].key)
        test.assertEqual("Damage", warhead.children[1].key)
        warhead.children.insert(1, Node("Falloff", "100, 75, 50, 25"))
    for tag in CORROSION_CLEANUP.get(node.key, ()):
        warhead = copy.child("Warhead@" + tag)
        test.assertIsNotNone(warhead, (node.key, tag))
        test.assertEqual(8, len(warhead.children), (node.key, tag))
        test.assertEqual("PhysicalStates", warhead.children[7].key, (node.key, tag))
        test.assertEqual("100", warhead.child("PhysicalStates").get("Corrosion"))
        test.assertIsNone(warhead.child("PhysicalStateName"))
        test.assertIsNone(warhead.child("PhysicalStateScale"))
        warhead.children.extend([Node("PhysicalStateName", "Corrosion"), Node("PhysicalStateScale", "100")])
    for path, before, after in FIELD_CHANGES.get(node.key, ()):
        field = copy
        for key in path:
            field = field.child(key)
            test.assertIsNotNone(field, (node.key, path))
        test.assertEqual(after, field.value, (node.key, path))
        field.value = before
    return copy


class HistoricalView:
    def __init__(self, test, rules):
        self.test, self.rules = test, rules

    def __getattr__(self, key):
        return getattr(self.rules, key)

    def weapon(self, name):
        return restore_missile_role(self.test, self.rules.weapon(name), source=True)

    def resolve_weapon(self, name):
        return restore_r12_names(historical_copy(self.test, self.rules.resolve_weapon(name)))


class SonicFamilyView(HistoricalView):
    def resolve_weapon(self, name):
        return restore_sonic_family(self.test, self.rules.resolve_weapon(name))

    def weapon(self, name):
        source = super().weapon(name)
        if source.key not in sonic_family_changes():
            return source
        # Older converter selection also examines the authored family reference.
        # Validate the complete current payload before restoring that identity.
        old = self.resolve_weapon(name)
        current = self.rules.resolve_weapon(name)
        old_main = next(c for c in old.children if c.key.startswith('Warhead@Sonic_')
                        and c.value in ('AreaDamage', 'SpreadDamage'))
        new_main = next(c for c in current.children if c.value == 'AreaDamage'
                        and 'Sonic_' in c.key)
        copy = source.deep_copy()
        family = copy.child('Inherits@sonicfamily')
        self.test.assertIsNotNone(family, name)
        self.test.assertEqual('^Warhead_' + new_main.key.split('@')[1], family.value)
        family.value = '^Warhead_' + old_main.key.split('@')[1].replace('FlatCompatibility', '')
        return copy


def restore_later_profile(test, node):
    """Assert the complete modern ordered payload before an older lane checkpoint."""
    fixture = json.loads((pathlib.Path(__file__).parent / 'fixtures' /
                          'later_profile_history_20260910.json').read_text(encoding='utf-8'))
    historical_name = LATER_HISTORICAL_NAMES.get(node.key, node.key)
    if historical_name not in fixture:
        return node
    node = restore_r12_names(restore_target_policy_fields(test, node))
    record = fixture[historical_name]
    def ordered(n):
        return [n.key, n.value, [ordered(c) for c in n.children]]
    actual = ordered(node)
    actual[0] = historical_name  # Normalize only the exact reviewed root identity.
    test.assertEqual(record['current'], actual, node.key)
    def rebuild(row):
        return Node(row[0], row[1], [rebuild(c) for c in row[2]])
    before = rebuild(record['before'])
    before.key = node.key
    return before


class LaterProfileView(HistoricalView):
    def resolve_weapon(self, name):
        node = self.rules.resolve_weapon(name)
        # Later lane payloads are independently frozen; do not mix their source
        # checkpoint with the older coupling/trajectory converter view.
        restored = restore_later_profile(self.test, node)
        return restored if restored is not node else super().resolve_weapon(name)
