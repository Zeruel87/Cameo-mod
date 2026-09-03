#!/usr/bin/env python3
"""audit_weapon_identity.py — does a weapon's WARHEAD FAMILY match what its NAME says it is?

    python tools/audit/audit_weapon_identity.py [--baseline N]

⛔ WHY THIS EXISTS (maintainer, 2026-08-19). Reviewing a 39-commit W24 batch:

    *"TS70mmChem is obviously a chemical cannon from the name alone that is easy to see but
    instead of making it that he made it into a Warhead_CannonHE_Medium … JapanesePlasmaBomb is
    obviously a plasma weapon right? can you read it from the name? and what did it give instead?
    See this is exactly the mess up i've been talking about!"*

Every automated guard passed on that batch. The suite counts broadcasts, catches NREs, proves the
mod boots and pins totals — **none of it reads the weapon's name.** A human spotted it in seconds.
This makes that reading mechanical.

WHAT IT FLAGS: a weapon whose NAME carries a payload token (`Chem`, `Plasma`, `Tesla`, `Cryo`, …)
while none of its inherited `^Warhead_*` families expresses that payload. `TS70mmChem` carrying
`CannonHE` + `Chemical` is still flagged as **UNCOLLAPSED**, because the right answer is the ONE
family `CannonChem` — two mains is the W24 defect, not the fix.

⚠ IT IS A SMELL DETECTOR, NOT A PROOF. A name is evidence about intent, not the contract, so this
reports for review rather than failing hard. Real exemptions exist and are listed in `EXEMPT`
below — `PhotonCannon` is a proper noun, `Fremen_RPG` has no payload token at all. Add to `EXEMPT`
with a REASON, never silence a token globally.

RATCHET: pass `--baseline N` to fail when the count exceeds N. Left unset by default because the
count must be measured on a SETTLED tree — taking a baseline while a batch is mid-regeneration
pins garbage. Set it once, then only ever lower it.
"""
from __future__ import annotations

import argparse
import pathlib
import re
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import miniyaml  # noqa: E402

# A payload token in a weapon NAME -> the warhead families that legitimately express it.
# Delivery words (Missile/Cannon/Rocket/Gun) are deliberately absent: this audit is about the
# PAYLOAD half, which is the half that gets lost in a conversion.
TOKENS: dict[str, tuple[str, ...]] = {
    "chem":        ("Chem", "Chemical", "Toxic"),
    "acid":        ("Chem", "Chemical", "Toxic"),
    "toxin":       ("Chemical", "Toxic"),
    "plasma":      ("Plasma",),
    "nuke":        ("Nuke", "Nuclear"),
    "nuclear":     ("Nuke", "Nuclear"),
    "atomic":      ("Nuke", "Nuclear"),
    "tesla":       ("Tesla", "Storm"),
    "napalm":      ("Fire", "Flame", "Inferno"),
    "incendiary":  ("Fire", "Flame", "Inferno"),
    "flame":       ("Fire", "Flame", "Inferno"),
    "inferno":     ("Inferno", "Flame", "Fire"),
    "laser":       ("Laser",),
    "prism":       ("Prism", "Inferno", "Cryo"),
    "cryo":        ("Cryo",),
    "frost":       ("Cryo",),
    "freeze":      ("Cryo",),
    "quantum":     ("Quantum",),
    "sonic":       ("Sonic",),
    "railgun":     ("Railgun",),
    "thermobaric": ("Thermobaric", "Nuke", "Nuclear"),
    "waveforce":   ("Waveforce",),
    "photon":      ("PhotonCannon", "Waveforce"),
    "sniper":      ("Sniper",),
    "flak":        ("Flak", "MissileAA"),
    "magic":       ("Magic",),
}

# Tokens that are part of a LONGER word meaning something else. Checked before TOKENS.
FALSE_FRIENDS = ("firebat", "firestorm", "firefly", "ceasefire", "firing", "misfire")

EXEMPT: dict[str, str] = {
    # weapon name -> why the name/family mismatch is correct
}


def families_of(rs, name: str) -> set[str]:
    """The `^Warhead_<Family>_<Level>` families a weapon inherits, by source (not resolved)."""
    node = rs.weapons.get(name)
    if node is None:
        return set()
    out = set()
    for c in node.children:
        if not c.key.startswith("Inherits") or not c.value:
            continue
        m = re.match(r"\^Warhead_([A-Za-z0-9]+)_(Light|Medium|Heavy|Super|Trace)\b",
                     c.value.strip())
        if m:
            out.add(m.group(1))
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--baseline", type=int, default=None,
                    help="fail when the finding count exceeds N (measure on a SETTLED tree)")
    a = ap.parse_args()

    rs = miniyaml.Ruleset(miniyaml.find_repo_root())
    missing, uncollapsed = [], []

    for name in sorted(rs.weapons):
        if name.startswith("^") or name in EXEMPT:
            continue
        low = name.lower()
        for ff in FALSE_FRIENDS:
            low = low.replace(ff, "")
        fams = families_of(rs, name)
        if not fams:
            continue                      # legacy weapon, not yet on the family system
        for token, ok in TOKENS.items():
            if token not in low:
                continue
            if any(any(o.lower() in f.lower() for o in ok) for f in fams):
                # payload IS expressed — but is it the only main?
                if len(fams) > 1:
                    uncollapsed.append((name, token, sorted(fams)))
            else:
                missing.append((name, token, sorted(fams)))
            break                          # one token per weapon is enough signal

    print("# audit_weapon_identity — does the warhead family match the name?\n")
    print(f"Concrete weapons on the family system: "
          f"{sum(1 for n in rs.weapons if not n.startswith('^') and families_of(rs, n))}\n")

    print(f"## ⛔ PAYLOAD MISSING — the name says it, no warhead family expresses it "
          f"({len(missing)})\n")
    if missing:
        print("| weapon | name says | families it actually has |")
        print("|---|---|---|")
        for n, t, f in missing:
            print(f"| `{n}` | **{t}** | {', '.join(f) or '—'} |")
    else:
        print("_none_")

    print(f"\n## ⚠ UNCOLLAPSED — payload present, but the weapon still has several warhead "
          f"families ({len(uncollapsed)})\n")
    print("One weapon, one damage warhead (DESIGN §11b). A payload blend family — `CannonChem`, "
          "`MissileFire` — is how a weapon is BOTH its delivery and its payload in ONE main.\n")
    if uncollapsed:
        print("| weapon | name says | families |")
        print("|---|---|---|")
        for n, t, f in uncollapsed[:60]:
            print(f"| `{n}` | **{t}** | {', '.join(f)} |")
        if len(uncollapsed) > 60:
            print(f"\n_… {len(uncollapsed) - 60} more_")
    else:
        print("_none_")

    total = len(missing) + len(uncollapsed)
    print(f"\n**total findings: {total}**")
    if a.baseline is None:
        print("\n_no baseline set — reporting only. Measure on a settled tree, then ratchet DOWN._")
        return 0
    if total > a.baseline:
        print(f"\n**FAIL — {total} exceeds the baseline of {a.baseline}.**")
        return 1
    print(f"\n_at or below baseline ({a.baseline})._")
    return 0


if __name__ == "__main__":
    sys.exit(main())
