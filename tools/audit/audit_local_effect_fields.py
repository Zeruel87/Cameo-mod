#!/usr/bin/env python3
"""Guard audit: flag weapons that declare local Explosions/ImpactSounds in a
CreateEffect warhead instead of inheriting the pairing from a canonical
^<game>_<effect> template.

The effect+sound template spec (docs/design/EFFECT_SOUND_TEMPLATES.md) says:
  - One template per real effect, named ^<game>_<effect_file_stem>
  - Every template sets BOTH the visual (Explosions) and ImpactSounds
  - Weapons inherit the effect exactly once: Inherits@fx: ^<game>_<effect>
  - Neither half is ever set on a weapon directly

This audit scans all live weapon files for local Explosions or ImpactSounds
declarations inside CreateEffect warheads and reports them. Templates
(nodes starting with ^) are exempt — they are the canonical definitions.

Ratchet: L1 (local Explosions) and L2 (local ImpactSounds) are LOWER-ONLY.
The counts can only decrease as weapons are converted to inherit templates.
"""
from __future__ import annotations
import re
import sys
from pathlib import Path

MOD = Path(__file__).resolve().parents[2] / "mods" / "cameo"
CENTRAL = ["weapons/weapons.yaml", "weapons/tiberiandawn.yaml", "weapons/redalert2mod.yaml",
           "weapons/d2k.yaml", "weapons/starcraft.yaml", "weapons/warcraft2.yaml",
           "weapons/tiberiansun.yaml", "weapons/outpost2.yaml"]
FILES = [MOD / p for p in CENTRAL] + sorted((MOD / "ContentPacks").glob("*/*/yaml/weapons.yaml"))

RE_TOP = re.compile(r"^([^\s#][^:]*):\s*$")
RE_WARHEAD = re.compile(r"^(-?)Warhead@(\S+?):\s*(\S*)\s*$")
RE_INHERITS = re.compile(r"^Inherits(?:@\S+)?:\s*(\S+)")
RE_FIELD = re.compile(r"^\t\t(\S+):\s*(.*)$")


def indent_of(s):
    n = 0
    for ch in s:
        if ch == "\t":
            n += 8 - (n % 8)
        elif ch == " ":
            n += 1
        else:
            break
    return n


def is_template(name):
    return name.startswith("^")


def scan_file(path):
    """Yield (file, weapon_name, warhead_key, has_explosions, has_impact_sounds, line_no)."""
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except Exception:
        return

    headers = [i for i, ln in enumerate(lines)
               if ln.strip() and not ln.lstrip().startswith("#")
               and indent_of(ln) == 0 and RE_TOP.match(ln)]

    for h, start in enumerate(headers):
        end = headers[h + 1] if h + 1 < len(headers) else len(lines)
        name = RE_TOP.match(lines[start]).group(1).strip()

        # Skip templates — they are the canonical definitions
        if is_template(name):
            continue

        # Scan warheads
        i = start + 1
        while i < end:
            ln = lines[i]
            m = RE_WARHEAD.match(ln.lstrip("\t"))
            if m and not m.group(1):  # not a removal
                wh_key = m.group(2)
                wh_type = m.group(3).strip()
                if wh_type == "CreateEffect":
                    has_explosions = False
                    has_impact_sounds = False
                    wh_line = i + 1
                    j = i + 1
                    while j < end:
                        fl = lines[j]
                        if not fl.strip() or fl.lstrip().startswith("#"):
                            j += 1
                            continue
                        if indent_of(fl) <= indent_of(ln):
                            break
                        fm = RE_FIELD.match(fl)
                        if fm:
                            field_name = fm.group(1)
                            if field_name == "Explosions":
                                has_explosions = True
                            elif field_name == "ImpactSounds":
                                has_impact_sounds = True
                        j += 1
                    if has_explosions or has_impact_sounds:
                        yield (str(path.relative_to(MOD)), name, wh_key,
                               has_explosions, has_impact_sounds, wh_line)
            i += 1


def main():
    findings = []
    for path in FILES:
        if not path.exists():
            continue
        for f, weapon, wh, has_expl, has_snd, line in scan_file(path):
            findings.append((f, weapon, wh, has_expl, has_snd, line))

    # Report
    l1 = sum(1 for f in findings if f[3])  # local Explosions
    l2 = sum(1 for f in findings if f[4])  # local ImpactSounds

    print("# Local effect field guard — weapons declaring Explosions/ImpactSounds")
    print("# instead of inheriting from ^<game>_<effect> templates")
    print()
    print(f"Files scanned: {len(FILES)}")
    print(f"Concrete weapons with local Explosions (L1): {l1}")
    print(f"Concrete weapons with local ImpactSounds (L2): {l2}")
    print()

    if findings:
        print("| file | weapon | warhead | Explosions | ImpactSounds | line |")
        print("|---|---|---|---|---|---|")
        for f, weapon, wh, has_expl, has_snd, line in sorted(findings):
            print(f"| {f} | {weapon} | {wh} | {'YES' if has_expl else '-'} | {'YES' if has_snd else '-'} | {line} |")

    # Ratchet check (LOWER-ONLY)
    ratchet_path = Path(__file__).parent / "ratchet_local_effect_fields.json"
    if ratchet_path.exists():
        import json
        ratchet = json.loads(ratchet_path.read_text(encoding="utf-8"))
        old_l1 = ratchet.get("L1", l1)
        old_l2 = ratchet.get("L2", l2)
        if l1 > old_l1:
            print(f"\nFAIL: L1 {l1} > ratchet {old_l1}")
            sys.exit(1)
        if l2 > old_l2:
            print(f"\nFAIL: L2 {l2} > ratchet {old_l2}")
            sys.exit(1)
        print(f"\nPASS: L1 {l1} <= {old_l1}, L2 {l2} <= {old_l2}")
    else:
        print(f"\nNo ratchet file — first run. L1={l1}, L2={l2}")

    sys.exit(0)


if __name__ == "__main__":
    main()
