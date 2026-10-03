"""Explicit historical inputs, never substituted for current active game rules.

Weapon resolved at 819abe10d5858b810c6102a33eeebce42165f6cb, before upstream
8748c68e4 converted HydraSpit to BulletChem. Target/shooter inputs are the original
ordered-impact artifact's serialized scenario, not newly resolved actor stats.
"""
import hashlib
import json
import pathlib
from miniyaml import Node

ROOT = pathlib.Path(__file__).resolve().parents[2]


def weapon():
    data = json.loads((ROOT / 'tools/tests/fixtures/hydra_pre_bulletchem.json').read_text(encoding='utf-8'))
    digest = hashlib.sha256(json.dumps(data, separators=(',', ':')).encode()).hexdigest()
    if digest != '50c133e219282e45ffe130f8a657d61aba40e732aecd9953a19d9098680e4122':
        raise AssertionError('Historical Hydra fixture changed')
    def node(row):
        return Node(row[0], row[1], [node(c) for c in row[2]])
    return node(data)


def scenario(lab):
    data = json.loads((ROOT / 'docs/audit/latest/hydralisk_impact_lab.json').read_text(encoding='utf-8'))
    digest = hashlib.sha256(json.dumps(data, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
    if digest != '5591cd280cb6e097795a2bb6e1fccd9850e47b3245754b03fbd83b35b395d398':
        raise AssertionError('Archived Hydra scenario/evidence changed')
    return [lab.Target(**row) for row in data['targets']], data['shooter_firepower']
