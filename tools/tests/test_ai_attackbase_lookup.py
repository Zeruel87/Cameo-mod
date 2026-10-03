"""No CA/Cameo code may look up AttackBase as a single trait (bot modules first of all).

76 mobile ground actors carry two or more AttackBase-derived traits (e.g.
AttackFrontal + AttackFollow on ts_nod_attackbuggy), and TraitOrDefault<T> /
Trait<T> throw "Actor X has multiple traits of type AttackBase" on them. In bot
code that ends the match: phase 6f shipped IsArtilleryUnit with
TraitOrDefault<AttackBase> and crashed the first time a bot owning an attack
buggy formed an attack force. The runtime gate cannot see this class (its bot
never owns an army), so it is checked statically here. Iterate
TraitsImplementing<AttackBase>() and skip disabled traits instead.
"""

import re
import unittest
from pathlib import Path


ROOT = Path(__file__).parents[2]
# All of CA and Cameo, not just bot modules: HuntCA (Lua hunt) and TargetedAttackAbility
# (created with the actor) carried the same latent bug until 2026-09-27.
BOT_DIRS = [
    ROOT / "OpenRA.Mods.CA",
    ROOT / "OpenRA.Mods.Cameo",
]
SINGLE_LOOKUP = re.compile(r"\b(?:TraitOrDefault|Trait)<AttackBase>\s*\(")


class AttackBaseLookupTest(unittest.TestCase):
    def test_no_single_attackbase_lookup(self):
        offenders = []
        for directory in BOT_DIRS:
            for path in sorted(directory.rglob("*.cs")):
                if "obj" in path.parts:
                    continue
                for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
                    code = line.split("//", 1)[0]  # comments may name the forbidden call
                    if SINGLE_LOOKUP.search(code):
                        offenders.append(f"{path.relative_to(ROOT)}:{number}: {line.strip()}")

        self.assertEqual([], offenders, "use TraitsImplementing<AttackBase>() instead:\n" + "\n".join(offenders))


if __name__ == "__main__":
    unittest.main()
