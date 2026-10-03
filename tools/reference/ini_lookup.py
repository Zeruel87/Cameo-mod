"""Read an INI reference source one WARHEAD at a time: its keys, the weapons that use it, and who fires them.

Read-only. Built for the per-weapon reads that INI sources force on the warhead-family assignment
(R62): when a source's element axis carries nothing machine-readable, the family is decided from
each weapon's projectile, report and firer, and this prints exactly those.

    python tools/reference/ini_lookup.py twisted_insurrection Gas PollyWH ShockwaveWH
    python tools/reference/ini_lookup.py dta_enhanced AP HollowPoint

DTA is read the way `warhead_matrix.read_dta` reads it: `Rules.ini`, with `Enhance.ini` layered on
top for `dta_enhanced`. Its warheads state `Modifier.<armor>` keys, and an armor that is not stated
inherits through `BaseArmor` (naval_light -> light -> wood), so equal columns are genuine.

⚠ TS-engine tank guns fire `Projectile=InvisibleMissile`, so they measure as Missile delivery;
check the firer before believing the delivery.
"""
import argparse
import collections
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import warhead_matrix as wm  # noqa: E402

WEAPON_SLOTS = ("Primary", "Secondary", "ElitePrimary", "EliteSecondary", "DeathWeapon") + tuple(
    f"Weapon{i}" for i in range(1, 9))
WEAPON_KEYS = ("Damage", "ROF", "Range", "Projectile", "Report", "Burst", "IsLaser", "IsRailgun",
               "IsElectricBolt", "IsRadBeam", "IsSonic", "IsMagBeam", "AmbientDamage", "Anim")


DTA_SOURCES = ("dta_enhanced", "dta_classic")


def load(source: str) -> tuple[dict[str, dict[str, str]], str]:
    """The source's merged INI sections and a label for its file."""
    if source in DTA_SOURCES:
        overlay = wm.DTA_INI / "Enhance.ini" if source == "dta_enhanced" else None
        ini = wm.load_dta_ini(wm.DTA_INI / "Rules.ini", overlay)
        return ini, "Rules.ini" + (" + Enhance.ini" if source == "dta_enhanced" else "")
    src = next(s for s in wm.INI_SOURCES if s[0] == source)
    return wm.parse_ini(src[2]), src[2].name


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("source", choices=[s[0] for s in wm.INI_SOURCES] + list(DTA_SOURCES))
    ap.add_argument("warheads", nargs="+")
    ap.add_argument("--max-weapons", type=int, default=4)
    args = ap.parse_args()

    ini, label = load(args.source)
    by_lower = {k.lower(): k for k in ini}
    users = collections.defaultdict(list)
    firers = collections.defaultdict(set)
    for section, kv in ini.items():
        if "Warhead" in kv and ("Damage" in kv or "Projectile" in kv):
            users[kv["Warhead"].lower()].append(section)
        for slot in WEAPON_SLOTS:
            if slot in kv:
                firers[kv[slot].lower()].add(section)

    for name in args.warheads:
        key = by_lower.get(name.lower())
        if key is None:
            print(f"\n##### {name}: NOT a section of {label}")
            continue
        keys = "; ".join(f"{k}={v}" for k, v in ini[key].items() if not k.startswith("Versus"))
        print(f"\n##### {key}: {keys}")
        for weapon in users.get(name.lower(), [])[:args.max_weapons]:
            kv = ini[weapon]
            proj = ini.get(by_lower.get(kv.get("Projectile", "").lower(), ""), {})
            who = sorted(firers.get(weapon.lower(), []))
            label = ini.get(who[0], {}).get("Name", "") if who else ""
            fields = " ".join(f"{k}={kv[k]}" for k in WEAPON_KEYS if k in kv)
            pfields = ", ".join(f"{k}={v}" for k, v in list(proj.items())[:6])
            print(f"   weapon {weapon}: {fields} | projectile [{pfields}] | fired by {who[:5]} {label!r}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
