"""Small offline Hydra screen; no gameplay edits and no whole-roster resolution.

Candidate rows transcribed from PR325 e42eb991's staged BulletChem_Light patch.
This is a nominal armor/HP screen, NOT a combat simulator or pricing model.
"""
import argparse
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools/audit'))
from miniyaml import Ruleset, Node
import percentage_damage as pd
from effective_damage import falloff_and_radii, runtime_falloff

MAIN = dict(zip('Shield None Flak Scout Light Plate Wood Medium Heroic Fighter Heavy Superheavy Steel Bomber Concrete Helicopter Spaceship'.split(),
                [162,191,155,146,126,124,103,102,95,94,91,80,74,63,58,53,45]))
PCT = dict(zip('Shield Heroic Flak Plate None Scout Light Medium Heavy Superheavy Wood Steel Fighter Concrete Bomber Helicopter Spaceship'.split(),
               [17,14,13,13,12,10,9,9,8,8,7,6,6,5,5,4,3]))
TARGETS = ('td_nod_minigunner', 'terran_marine', 'zerg_hydralisk',
           'ra1_allies_alliedmediumtank', 'terran_siegetank',
           'terran_wraith', 'terran_battlecruiser')


def nominal(weapon, armor, hp):
    """Before falloff, actor modifiers and defenses; percentage integer core retained."""
    flat = state = 0
    for node in weapon.children:
        if node.value not in ('AreaDamage', 'SpreadDamage'):
            continue
        damage = int(node.get('Damage') or 0) * pd.versus_table(node).get(armor, 100) // 100
        flat += damage
        if node.value == 'AreaDamage':
            if node.get('PhysicalStateName') == 'Corrosion':
                state += damage * int(node.get('PhysicalStateScale') or 0) // 100
            state += damage * int(node.get('PhysicalStates', 'Corrosion') or 0) // 100
    pct = sum(a['runtime_hp'] * a['versus'].get(armor, 100) // 100
              for a in pd.percentage_applications(weapon, hp))
    return flat, pct, state


def candidate(damage, scale):
    return Node('candidate', '', [Node('Warhead@BulletChem_Light', 'AreaDamage', [
        Node('Damage', str(damage)), Node('PercentageScale', str(scale)),
        Node('Versus', '', [Node(k, str(v)) for k,v in MAIN.items()]),
        Node('PercentageVersus', '', [Node(k, str(v)) for k,v in PCT.items()]),
        Node('PhysicalStates', '', [Node('Corrosion', '20')]),
        Node('Spread', '55'), Node('Falloff', '100, 82, 61, 38, 0')])])


def report():
    rules = Ruleset(ROOT)
    hydra = rules.resolve_weapon('HydraSpit')
    lines = ['# Hydralisk candidate screening', '',
        'Source: upstream 4deaee086; candidate template from PR325 e42eb991 staged patch.',
        'No candidate is applied. Cost, HP, speed, range, reload and projectile remain unchanged.', '',
        '## Nominal per-shot budgets', '',
        'Each cell is **flat / percentage / flat-derived Corrosion** in engine health units.',
        'Uses real resolved HP and base Armor (not deployed/shielded variants). Excludes actor',
        'firepower, target damage modifiers, targeting eligibility, state clamping/DoT and falloff.',
        'Corrosion excludes percentage-derived feed, so is not total state delivery.',
        'This isolates profile tradeoffs; it is not actual damage, DPS or shots-to-kill.', '',
        '| Target | HP / armor | Current | Staged 72000 | Flak anchor 33000 | Fighter-row anchor 42000 |',
        '|---|---|---|---|---|---|']
    variants = [hydra, candidate(72000,10000), candidate(33000,2098), candidate(42000,1648)]
    for name in TARGETS:
        actor = rules.resolve(name)
        hp = int(actor.get('Health','HP'))
        armor = actor.get('Armor','Type')
        cells = [' / '.join(map(str,nominal(v,armor,hp))) for v in variants]
        lines.append(f'| {name} | {hp} / {armor} | ' + ' | '.join(cells) + ' |')
    cells = [' / '.join(map(str,nominal(v,'Fighter',50000))) for v in variants]
    lines.append('| Synthetic Fighter reference (not an actor) | 50000 / Fighter | ' + ' | '.join(cells) + ' |')
    lines += ['', 'The 33000 and 42000 values are rounded screening anchors, not recommendations.',
        'Their PercentageScale values 2098 and 1648 approximately retain the current nominal',
        'Flak percentage coefficient (0.45% max HP), instead of retaining the staged buff.',
        'They do not preserve every armor row or small-HP rounding. Corrosion stays at the staged',
        '20% only to expose its consequences; it has not been calibrated.', '',
        '## Flat-only distance sensitivity', '',
        'Flak damage at distance from the hit-shape edge, without actor modifiers. This is',
        'one target at a chosen distance, not a crowd simulation or projectile hit probability.', '',
        'Current nominal Flak damage is 51480; at distance zero it is 51332 because this',
        'table includes the existing authored falloff (the chemical main starts at 99%).', '',
        '| Distance (world units) | Current | 33000 | 42000 |', '|---|---|---|---|']
    for distance in (0,55,110,220,350,700):
        values=[]
        for weapon in (hydra,variants[2],variants[3]):
            total=0
            for node in weapon.children:
                if node.value not in ('AreaDamage','SpreadDamage'):
                    continue
                fo,radii,_ = falloff_and_radii(node)
                total += int(node.get('Damage')) * pd.versus_table(node).get('Flak',100) * runtime_falloff(fo,radii,distance) // 10000
            values.append(str(total))
        lines.append(f'| {distance} | ' + ' | '.join(values) + ' |')
    lines += ['', '## Screening conclusion', '',
        'Neither candidate is ready to implement. 33000 roughly retains Flak flat damage but',
        'raises None damage by 22%; 42000 roughly retains Fighter flat damage but still cuts',
        'Helicopter and Spaceship flat damage by about 40-46%. Reducing raw damage alone',
        'cannot preserve the existing mixed anti-air role. Percentage and Corrosion delivery',
        'also change independently. Choose the desired armor response before tuning magnitude.', '',
        'Next gate: choose acceptable infantry-versus-air tradeoffs, then model full',
        'actor modifiers, percentage geometry and total state delivery before selecting a build.',
        'No broad family regeneration, game launch or publication is authorized by this screen.', '']
    return '\n'.join(lines)


if __name__ == '__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--write', action='store_true')
    args=parser.parse_args()
    result=report()
    if args.write:
        (ROOT/'docs/design/HYDRALISK_CANDIDATE_SCREEN.md').write_text(result,encoding='utf-8')
    else:
        print(result)
