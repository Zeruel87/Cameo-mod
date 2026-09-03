"""Detect bug B (refined): children of converted weapons that keep OLD
warhead keys WHERE THE PARENT HAS THE CORRESPONDING NEW KEY.

The bug: parent P was converted — its `Warhead@TeslaWeapon` was renamed
to `Warhead@Tesla_Heavy`. Child C inherits P and still has
`Warhead@TeslaWeapon`. Since P no longer has that key, C's node is a
NEW orphaned warhead → double fire.

False positive to EXCLUDE: child adds a warhead the parent NEVER had
(e.g. a chem variant adding `Warhead@MediumChemicalWeapon` to a base
missile parent that has no chemical warhead). That's intentional.

Detection: for each child old-key, check if the parent has the NEW key
that corresponds to the old key (per the rename map). If yes → real bug.
If no → false positive (child is adding a new warhead type)."""
import re
from pathlib import Path

MOD = Path(__file__).resolve().parents[2] / "mods" / "cameo"
CENTRAL = ["weapons/weapons.yaml", "weapons/redalert2.yaml",
           "weapons/redalert2mod.yaml", "weapons/tiberiansun.yaml",
           "weapons/tiberiandawn.yaml", "weapons/warcraft2.yaml",
           "weapons/missiles.yaml"]
FILES = [MOD / p for p in CENTRAL] + sorted((MOD / "ContentPacks").glob("*/*/yaml/weapons.yaml"))

# old key -> new key (the rename map from the 3-way split)
OLD_TO_NEW = {
    "SmallArms": "Bullet_Light", "Chaingun": "Bullet_Medium",
    "TankDestroyerCannon": "CannonAP_Light", "MediumCannon": "CannonHE_Medium",
    "HeavyCannon": "CannonHE_Heavy", "LightMissile": "MissileAP_Light",
    "MediumMissile": "MissileAP_Medium", "HeavyMissile": "MissileAP_Heavy",
    "FlakWeapon": "Flak_Medium", "HeavyAAWeapon": "MissileAA_Heavy",
    "Grenade": "Demolition_Light", "ShrapnelWeapon": "Concussion_Medium",
    "HeavyBomb": "Demolition_Heavy", "LaserWeapon": "Laser_Heavy",
    "RailgunWeapon": "Railgun_Heavy", "TeslaWeapon": "Tesla_Heavy",
    "TeslaChargedWeapon": "TeslaCharged_Super", "SwordWeapon": "Melee_Medium",
    "ArrowWeapon": "Arrow_Light", "MagicWeapon": "Magic_Heavy",
    "LightFlameWeapon": "Flame_Light", "MediumFlameWeapon": "Flame_Medium",
    "HeavyFlameWeapon": "Flame_Heavy", "LightChemicalWeapon": "Chemical_Light",
    "MediumChemicalWeapon": "Chemical_Medium", "HeavyChemicalWeapon": "Chemical_Heavy",
    "NuclearWarhead": "Nuclear_Super",
}
OLD_KEYS = set(OLD_TO_NEW)
RE_OLD_WH = re.compile(r"^Warhead@(\w+?)((?:FriendlyFire|Percentage|ExtraDamage)?)\s*:")
RE_NEW_WH = re.compile(r"^Warhead@(\w+?)((?:FriendlyFire|Percentage|ExtraDamage)?)\s*:")
RE_INHERITS_WH = re.compile(r"^\s*Inherits@wh\d?\s*:\s*\^Warhead_")
RE_TOPNAME = re.compile(r"^(\w+):\s*$")
RE_INHERITS_PLAIN = re.compile(r"^\s*Inherits(?:@(\w+))?\s*:\s*(\S+)")

def indent_of(s):
    return len(s) - len(s.lstrip("\t "))

def parse_file(path):
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines(keepends=True)
    nodes = []
    headers = []
    for idx, ln in enumerate(lines):
        raw = ln.rstrip("\r\n")
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        if indent_of(raw) == 0 and RE_TOPNAME.match(raw):
            headers.append(idx)
    for h_i, start in enumerate(headers):
        end = headers[h_i + 1] if h_i + 1 < len(headers) else len(lines)
        name = RE_TOPNAME.match(lines[start].rstrip("\r\n")).group(1).strip()
        block = lines[start:end]
        parents = []
        has_new_wh = False
        old_keys_found = []  # (oldkey, suffix, line_no, text)
        new_keys_present = set()  # base new keys present in this node
        warhead_slots = set()  # exact (base key, suffix) slots authored here
        for j, ln in enumerate(block):
            raw = ln.rstrip("\r\n")
            mi = RE_INHERITS_PLAIN.match(raw)
            if mi:
                tag, parent = mi.group(1), mi.group(2)
                if not parent.startswith("^"):
                    parents.append(parent)
            if RE_INHERITS_WH.match(raw):
                has_new_wh = True
            stripped = raw.lstrip()
            m = RE_OLD_WH.match(stripped)
            if m:
                key, suffix = m.group(1), m.group(2)
                warhead_slots.add((key, suffix))
                if key in OLD_KEYS:
                    old_keys_found.append((key, suffix, start + j + 1, raw.strip()))
                # record all warhead base keys present (new or old)
                new_keys_present.add(key)
        nodes.append({"name": name, "parents": parents, "has_new_wh": has_new_wh,
                      "old_keys": old_keys_found, "new_keys_present": new_keys_present,
                      "warhead_slots": warhead_slots,
                      "file": str(path.relative_to(MOD))})
    return nodes

all_nodes = {}
for path in FILES:
    if not path.exists():
        continue
    for nd in parse_file(path):
        all_nodes.setdefault(nd["name"], []).append(nd)

converted = {nm for nm, lst in all_nodes.items() if any(n["has_new_wh"] for n in lst)}

def find_children(name, visited):
    result = set()
    for nm, lst in all_nodes.items():
        if nm in visited or nm == name:
            continue
        for nd in lst:
            if any(p == name for p in nd["parents"]):
                if nm not in visited:
                    result.add(nm)
                    visited.add(nm)
                    result |= find_children(nm, visited)
    return result

children_of = {cv: find_children(cv, {cv}) for cv in converted}

# For each child old-key, check if ANY parent in the chain (that is converted)
# has the corresponding NEW key. We check the immediate converted ancestor's
# new_keys_present, but also walk the chain.
def ancestors_of(name, visited=None):
    if visited is None:
        visited = set()
    result = set()
    for nd in all_nodes.get(name, []):
        for p in nd["parents"]:
            if p in visited:
                continue
            visited.add(p)
            result.add(p)
            result |= ancestors_of(p, visited)
    return result

bugs = []
false_positives = []
for cv, kids in children_of.items():
    cv_nodes = all_nodes.get(cv, [])
    if not cv_nodes:
        continue
    cv_new_keys = set()
    for nd in cv_nodes:
        cv_new_keys |= nd["new_keys_present"]
    for kid in kids:
        for nd in all_nodes.get(kid, []):
            for oldkey, suffix, ln, txt in nd["old_keys"]:
                newkey = OLD_TO_NEW[oldkey]
                # is the new key present in the converted ancestor (cv)?
                # check cv and all converted ancestors in the chain
                chain = {cv} | {a for a in ancestors_of(kid) if a in converted}
                # A retained percentage/friendly-fire slot is still a live inherited
                # warhead. A child using that exact slot overrides it; it does not add an
                # orphan beside the new main warhead.
                retains_old_slot = any(
                    (oldkey, suffix) in all_nodes[a][0]["warhead_slots"]
                    for a in chain if all_nodes.get(a)
                )
                if retains_old_slot:
                    continue
                has_new = any(newkey in all_nodes[a][0]["new_keys_present"] for a in chain if all_nodes.get(a))
                if has_new:
                    bugs.append((nd["file"], ln, kid, cv, oldkey, newkey, txt))
                else:
                    false_positives.append((nd["file"], ln, kid, cv, oldkey, newkey, txt))

print(f"Converted weapons: {len(converted)}")
print(f"Bug B REAL (parent has new key, child has orphaned old key): {len(bugs)}")
for rel, ln, kid, parent, ok, nk, txt in sorted(bugs):
    print(f"  {rel}:{ln}  {kid} (<= {parent})  {ok}->{nk}  {txt}")
print()
print(f"False positives (child adds warhead parent never had): {len(false_positives)}")
