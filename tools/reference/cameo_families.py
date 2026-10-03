#!/usr/bin/env python3
"""What Cameo's own warhead families ARE — the one labelled set in this lane.

Every other source in the reference corpus is unlabelled: a mod ships a weapon, we measure its
Versus row, and which Cameo family it should map to is a judgement. Cameo itself is different. A
Cameo weapon that inherits `^Warhead_<Family>_<Level>` HAS a family, stated in the yaml, by
construction (R37). That makes this module the ground truth for scoring any assignment method,
and the row-list for the family-outward pipeline.

⚠ THE NAME PARSER IS THE WHOLE POINT OF THIS FILE. `^Warhead_CannonHE_Heavy_D2K_DevBullet` is
family `CannonHE`, level `Heavy`, variant `D2K_DevBullet`. Splitting on the LAST underscore —
the obvious reading, and the one two tools shipped — gives family `CannonHE_Heavy_D2K`, and
invents a family per variant: 53 where there are 51. The family is whatever precedes the LEVEL
token, so find the level first and never count underscores.

    python tools/reference/cameo_families.py            # the 51 families and their levels
    python tools/reference/cameo_families.py --weapons  # the labelled weapons, family by family
"""
from __future__ import annotations

import argparse
import collections
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "audit"))

from miniyaml import Ruleset  # noqa: E402

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

PREFIX = "^Warhead_"

# The level vocabulary of DESIGN §12.0d. The family is everything before one of these; the
# variant (a mod-specific respin like `_D2K_DevBullet`) is everything after.
LEVELS = ("Light", "Medium", "Heavy", "Super")


def split_template(name: str) -> tuple[str, str, str]:
    """`^Warhead_CannonHE_Heavy_D2K_DevBullet` -> ("CannonHE", "Heavy", "D2K_DevBullet").

    A template with no level token at all returns ("", "") for level and variant and the whole
    remainder as the family, which is how the handful of unlevelled legacy templates read.
    """
    if name.startswith(PREFIX):
        name = name[len(PREFIX):]
    parts = name.split("_")
    for i, part in enumerate(parts):
        if part in LEVELS:
            return "_".join(parts[:i]), part, "_".join(parts[i + 1:])
    return "_".join(parts), "", ""


def _ruleset() -> Ruleset:
    return Ruleset(ROOT, "cameo")


def templates(rs: Ruleset | None = None) -> dict:
    """{template name: (family, level, variant)} for every `^Warhead_*` template that ships."""
    rs = rs or _ruleset()
    return {name: split_template(name) for name in rs.weapons
            if name.startswith(PREFIX)}


def families(rs: Ruleset | None = None) -> dict:
    """{family: {level: [template names]}} — the live family list, 51 rows."""
    out: dict = collections.defaultdict(lambda: collections.defaultdict(list))
    for name, (family, level, _variant) in templates(rs).items():
        out[family][level].append(name)
    return {f: dict(levels) for f, levels in out.items()}


def labelled_weapons(rs: Ruleset | None = None) -> dict:
    """{weapon: {family: weight}} — CONCRETE weapons whose inherit chain names a family.

    A weapon inheriting two templates of the SAME family (`Bullet_Light` + `Bullet_Medium` — the
    legal between-tier mix, see LESSONS_LEARNED) votes once for `Bullet`. One inheriting two
    DIFFERENT families splits its vote, because which of them is "the" family is exactly the
    judgement under test.

    Pinned by the `cameo_family_labelled_weapons` doc claim.
    """
    rs = rs or _ruleset()
    out: dict = {}
    for name, raw in rs.weapons.items():
        if name.startswith("^") or name.startswith("-"):
            continue
        found = set()
        for _, parent in rs.inherits_of(raw):
            if parent.startswith(PREFIX):
                family, _level, _variant = split_template(parent)
                if family:
                    found.add(family)
        if found:
            out[name] = {f: 1.0 / len(found) for f in found}
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--weapons", action="store_true",
                    help="list the labelled weapons per family instead of the templates")
    args = ap.parse_args()

    rs = _ruleset()
    fams = families(rs)
    if not args.weapons:
        print(f"{len(fams)} families over "
              f"{sum(len(t) for lv in fams.values() for t in lv.values())} templates\n")
        for family in sorted(fams):
            levels = fams[family]
            shown = ", ".join(f"{lv or '(none)'}x{len(t)}" for lv, t in sorted(levels.items()))
            print(f"  {family:<22} {shown}")
        return 0

    weapons = labelled_weapons(rs)
    per: dict = collections.defaultdict(list)
    for weapon, votes in weapons.items():
        for family in votes:
            per[family].append(weapon)
    print(f"{len(weapons)} labelled weapons over {len(per)} families\n")
    for family in sorted(per, key=lambda f: -len(per[f])):
        print(f"  {family:<22} {len(per[family]):>4}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
