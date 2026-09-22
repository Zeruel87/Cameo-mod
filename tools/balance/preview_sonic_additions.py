"""Generate only the four Sonic additions, preserving the live family's calibration.

This writes a review artifact, never live rules. Existing shield slots are reserved;
new slots use the generator's upward-then-downward collision rule. Existing plating
normalization is retained, so this is intentionally not a full-family rebalance.
"""
import argparse
from contextlib import redirect_stdout
import io
import math
from pathlib import Path
import sys

import gen_weapon_template as gen
import shield_uniqueness as shield

ROOT = Path(__file__).resolve().parents[2]
FAMILIES = ('BulletSonic', 'MissileSonic', 'CannonSonic', 'BlastSonic')


def generate(live_text):
    saved_families = gen.BLEND_FAMILIES.copy()
    saved_scales = gen._PLATING_SCALES
    saved_argv = sys.argv
    try:
        for name in FAMILIES:
            gen.BLEND_FAMILIES.pop(name)
        gen._PLATING_SCALES = None
        sys.argv = ['gen_weapon_template.py']
        baseline = io.StringIO()
        with redirect_stdout(baseline):
            gen._generate()
        # Keep the baseline scale cache while the new families are emitted.
        gen.BLEND_FAMILIES.update(saved_families)
        parts = []
        for name in FAMILIES:
            parents, states, levels = gen.BLEND_FAMILIES[name]
            spreads, falloffs = gen.shape_for(name)
            air_share = sum(bool(gen.WEAPONS[p][2]) for p in parents) / len(parents)
            parts.append(gen.family(name, None, gen.valid_targets(air_share >= 1 / 3), levels,
                versus_override=gen.blend_versus(parents), physical_states=states,
                spreads=spreads, falloffs=falloffs))
        lines = '\n\n'.join(parts).splitlines()
        raw_base = shield.find_main_shields(baseline.getvalue().splitlines())
        additions = shield.find_main_shields(lines)
        lo_raw, hi_raw = min(x[3] for x in raw_base), max(x[3] for x in raw_base)
        if any(not lo_raw <= row[3] <= hi_raw for row in additions):
            raise ValueError('new Sonic shield outside existing calibration; review required')
        lo, hi = gen.SHIELD_FLOOR_TARGET, gen.SHIELD_CEIL_TARGET
        alpha = math.log(hi / lo) / math.log(hi_raw / lo_raw)
        targets = [(i, family, level, round(lo * (raw / lo_raw) ** alpha))
                   for i, family, level, raw in additions]
        reserved = {v for _, f, _, v in shield.find_main_shields(live_text.splitlines())
                    if f not in FAMILIES}
        used = set(reserved)
        chosen = {}
        for _, family, level, value in sorted(targets,
                key=lambda row: (row[3], shield.LEVEL_RANK[row[2]], row[1])):
            v = value
            while v in used and v < hi:
                v += 1
            while v in used and v > lo:
                v -= 1
            if v in used:
                raise ValueError('no free shield slot; refusing duplicate')
            used.add(v)
            chosen[family, level] = v
        for family in FAMILIES:
            levels = sorted(gen.BLEND_FAMILIES[family][2], key=shield.LEVEL_RANK.get)
            values = sorted(chosen[family, level] for level in levels)
            for level, value in zip(levels, values):
                chosen[family, level] = value
        for i, family, level, _ in additions:
            lines[i] = '\t\t\tShield: ' + str(chosen[family, level])
        return '# Scoped Sonic additions; existing shield/plating calibration retained.\n' + '\n'.join(lines) + '\n'
    finally:
        gen.BLEND_FAMILIES.clear()
        gen.BLEND_FAMILIES.update(saved_families)
        gen._PLATING_SCALES = saved_scales
        sys.argv = saved_argv


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    live = (ROOT / 'mods/cameo/weapons/weapons.yaml').read_text(encoding='utf-8')
    candidate = generate(live)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(candidate, encoding='utf-8')
    print('Wrote 12 Sonic templates to', args.output)


if __name__ == '__main__':
    main()
