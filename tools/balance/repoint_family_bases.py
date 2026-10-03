#!/usr/bin/env python3
"""repoint_family_bases.py — DESIGN §12.0j: move weapons off `^Warhead_<F>_<Level>` onto the
level-less `^Warhead_<F>` bases, with `Heaviness` taken from the old level.

    python tools/balance/repoint_family_bases.py                 # report only (default)
    python tools/balance/repoint_family_bases.py --apply         # edit the yaml in place
    python tools/balance/repoint_family_bases.py --apply --only-file <path> ...   # one lane

Maintainer rulings (2026-09-26): the level retires; Heaviness = old level (Light 0, Medium
1000, Heavy 2000); the bell is ACCEPTED as the runtime profile (it is not calibrated to imitate
the retired tilt). So a re-point is NOT resolved-identical by design, and this tool is built to
prove exactly how it differs:

  * `h`-OWNED fields move by design and are transformed, never copied:
      - Versus: the C# bell re-tilts it at runtime (accepted);
      - PercentageVersus: the base has none (shared mode reads Versus);
      - PercentageScale: a weapon's dial against the old default 10000 keeps its RATIO against
        the base's scale (a 5000 dial becomes base/2);
      - Spread / MinRadius / MaxRadius / the warhead Range array: the C# scales them by
        (h+2)/3 (AreaDamageWarhead.cs:310-312, 381-383), so an override is divided back and
        the EFFECTIVE radius stays what it was;
      - Heaviness / HeavinessMode.
  * EVERY OTHER field — Damage, DamageTypes, targets, Falloff, friendly fire, meters, chips,
    weapon-level Range/ReloadDelay — must resolve IDENTICALLY. The tool re-resolves every
    affected weapon after the edit and PINS any such field whose inherited value changed (a
    Light weapon inheriting the Medium base would otherwise get Medium's chip or Falloff),
    then verifies zero differences remain.

Not re-pointed (reported, left on their levelled template): `Super`/`Trace` edges (h stops at
2), non-generated families (Nuclear, Sniper), same-family MIX weapons (two levels of one family
— a between-tier encoding that needs its own ruling), and any closure that carries a LOCAL
PercentageVersus table (shared mode rejects one).

NEVER hand-parses yaml for analysis: every decision reads `miniyaml.Ruleset`. The edits are
line-level renames inside definitions located by that model.
"""
from __future__ import annotations

import argparse
import collections
import pathlib
import re
import shutil
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / "tools" / "audit"), str(ROOT / "tools" / "balance")]
import miniyaml  # noqa: E402
import effective_heaviness as eh  # noqa: E402

LEVEL_H = {"Light": 0, "Medium": 1000, "Heavy": 2000}
SKIP_LEVELS = ("Super", "Trace")
EDGE_RE = re.compile(r"^\^Warhead_([A-Za-z]+)_(Light|Medium|Heavy|Super|Trace)$")
SUFFIXES = ("", "_ExtraDamage", "_Debuff")
GEOMETRY = ("Spread", "MinRadius", "MaxRadius", "Range")        # scaled by (h+2)/3
CANCEL = "__cancel__"                                             # pin meaning `-Field:`
H_OWNED = {"Versus", "PercentageVersus", "PercentageVersusLight", "PercentageVersusHeavy",
           "PercentageScale", "Heaviness", "HeavinessMode"} | set(GEOMETRY)


def base_families(rs):
    return {n[len("^Warhead_"):] for n in rs.weapons
            if n.startswith("^Warhead_") and "_" not in n[len("^Warhead_"):]
            and (rs.resolve_weapon(n) is not None)
            and any(f"{n}_{lv}" in rs.weapons for lv in LEVEL_H)}


def edges(node):
    for c in node.children:
        if c.key.startswith("Inherits"):
            m = EDGE_RE.match(c.value.strip())
            if m:
                yield c, m.group(1), m.group(2)


def children_map(rs):
    kids = collections.defaultdict(set)
    for name, node in rs.weapons.items():
        for c in node.children:
            if c.key.startswith("Inherits") and c.value.strip() in rs.weapons:
                kids[c.value.strip()].add(name)
    return kids


def closure(kids, owner):
    out, todo = {owner}, [owner]
    while todo:
        for k in kids.get(todo.pop(), ()):
            if k not in out:
                out.add(k)
                todo.append(k)
    return out


def local_keys(node):
    return {c.key for c in node.children}


def plan(rs):
    """(owners, skipped). owners: [(def, family, level, closure)]."""
    fams = base_families(rs)
    kids = children_map(rs)
    owners, skipped = [], collections.defaultdict(list)
    per_def_family = collections.defaultdict(set)      # (def, family) -> levels reaching it
    candidates = []
    for name, node in rs.weapons.items():
        if EDGE_RE.match(name) or (name.startswith("^Warhead_") and "_" not in name[9:]):
            continue                                     # the templates and bases themselves
        for c, fam, lv in edges(node):
            if fam not in fams:
                skipped["non-generated family"].append((name, fam, lv))
                continue
            if lv in SKIP_LEVELS:
                skipped[f"{lv} level (h stops at 2)"].append((name, fam, lv))
                continue
            cl = closure(kids, name)
            candidates.append((name, fam, lv, cl))
            for d in cl:
                per_def_family[(d, fam)].add(lv)
    for name, fam, lv, cl in candidates:
        if any(len(per_def_family[(d, fam)]) > 1 for d in cl):
            skipped["same-family MIX (two levels of one family)"].append((name, fam, lv))
            continue
        pv = [d for d in cl for key in (f"Warhead@{fam}_{lv}",)
              if (n := rs.weapons[d].child(key)) is not None
              and any(k.key.startswith("PercentageVersus") for k in n.children)]
        if pv:
            skipped["local PercentageVersus (shared mode rejects it)"].append((name, fam, lv))
            continue
        owners.append((name, fam, lv, cl))
    return owners, skipped, fams


# ---------------------------------------------------------------------------------------------
# text edits
# ---------------------------------------------------------------------------------------------
def _block(lines, name):
    """(start, end) line indices of top-level def `name` (header .. before next col-0 line)."""
    head = re.compile(rf"^{re.escape(name)}:\s*(#.*)?$")   # a header may carry a comment
    for i, ln in enumerate(lines):
        if head.match(ln.rstrip()):
            j = i + 1
            while j < len(lines) and (not lines[j].strip() or lines[j][0] in " \t#"):
                j += 1
            # Trailing blanks AND col-0 comments belong to whatever follows (usually the next
            # def's heading comment), so a pin is inserted before them, not after.
            while j > i + 1 and (not lines[j - 1].strip() or lines[j - 1].startswith("#")):
                j -= 1
            return i, j
    raise KeyError(name)


def _geom_inverse(value, h):
    """Smallest-error authored length whose (h+2)/3 scaling returns `value`."""
    guess = round(value * 3 / (h / 1000 + 2))
    return min(range(guess - 3, guess + 4), key=lambda x: (abs(eh.scale_length(x, h) - value), abs(x - guess)))


def _rescale_line(key, raw, h, base_ps):
    if key == "PercentageScale":
        return str(round(int(raw) * base_ps / 10000))
    parts = [p.strip() for p in raw.split(",")]
    if not all(re.fullmatch(r"-?\d+", p) for p in parts):
        return None                                    # a WDist with units: leave for review
    return ", ".join(str(_geom_inverse(int(p), h)) for p in parts)


def edit_texts(rs, owners, base_ps, only_files=None):
    """-> {path: new text}. Renames edges and keys, rescales h-owned overrides."""
    texts = {}
    todo = collections.defaultdict(list)                # file -> [(def, fam, lv, is_owner)]
    for owner, fam, lv, cl in owners:
        for d in cl:
            todo[rs.weapons[d].file].append((d, fam, lv, d == owner))
    for path, jobs in todo.items():
        if only_files and not any(pathlib.Path(path).resolve() == pathlib.Path(f).resolve() for f in only_files):
            continue
        raw = pathlib.Path(path).read_bytes().decode("utf-8")
        nl = "\r\n" if "\r\n" in raw else "\n"
        lines = raw.split(nl)
        for d, fam, lv, is_owner in jobs:
            h = LEVEL_H[lv]
            s, e = _block(lines, d)
            node_key = None
            for i in range(s + 1, e):
                ln = lines[i]
                if is_owner and ln.startswith("\tInherits") and ln.split(":", 1)[1].strip() == f"^Warhead_{fam}_{lv}":
                    lines[i] = ln.replace(f"^Warhead_{fam}_{lv}", f"^Warhead_{fam}")
                    continue
                # The colon is OPTIONAL: `-Warhead@X` with no colon is a valid bare-key cancel
                # (D2k Shared's `^Warhead_*_D2K_*` templates write it that way).
                m = re.match(rf"^\t(-?)Warhead@{fam}_{lv}({'|'.join(x for x in SUFFIXES if x)})?(:.*)?\s*$", ln)
                if m:
                    suffix = m.group(2) or ""
                    lines[i] = f"\t{m.group(1)}Warhead@{fam}{suffix}{m.group(3) or ''}"
                    node_key = None if m.group(1) else suffix   # a cancel opens no node
                    continue
                if ln.startswith("\t") and not ln.startswith("\t\t"):
                    node_key = None
                    continue
                if node_key is not None and ln.startswith("\t\t") and not ln.startswith("\t\t\t"):
                    key, _, val = ln.strip().partition(":")
                    if key in GEOMETRY or (key == "PercentageScale" and node_key == ""):
                        new = _rescale_line(key, val.strip(), h, base_ps[fam])
                        if new is not None:
                            lines[i] = f"\t\t{key}: {new}"
        texts[path] = nl.join(lines)
    return texts


def add_pins(texts, rs, pins):
    """pins: {owner: {node_key: {field: value}}} appended as override nodes at the owner's end."""
    for owner, nodes in pins.items():
        path = rs.weapons[owner].file
        raw = texts.get(path) or pathlib.Path(path).read_bytes().decode("utf-8")
        nl = "\r\n" if "\r\n" in raw else "\n"
        lines = raw.split(nl)
        s, e = _block(lines, owner)
        add = []
        for key, fields in nodes.items():
            if key == "":                               # weapon-level fields
                add += [f"\t{f}: {v}" for f, v in fields.items()]
            else:
                add.append(f"\t{key}:")
                for f, v in fields.items():
                    if isinstance(v, tuple) and v[0] == "nested":
                        # Override only the leaves that differ; cancel leaves the base adds.
                        _tag, legacy, now = v
                        add.append(f"\t\t{f}:")
                        for leaf in sorted(set(legacy) | set(now)):   # NOT `path`: that is the file
                            ind = "\t" * (2 + len(leaf))
                            if leaf not in legacy:
                                add.append(f"{ind}-{leaf[-1]}:")
                            elif legacy[leaf] != now.get(leaf):
                                add.append(f"{ind}{leaf[-1]}: {legacy[leaf]}")
                    elif v == CANCEL:
                        add.append(f"\t\t-{f}:")
                    else:
                        add.append(f"\t\t{f}: {v}")
        lines[e:e] = add
        texts[path] = nl.join(lines)
    return texts


# ---------------------------------------------------------------------------------------------
# resolution on a scratch copy
# ---------------------------------------------------------------------------------------------
def scratch_ruleset(texts):
    tmp = pathlib.Path(tempfile.mkdtemp(prefix="repoint_"))
    src = ROOT / "mods" / "cameo"
    for p in src.rglob("*.yaml"):
        dst = tmp / "mods" / "cameo" / p.relative_to(src)
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(p, dst)
    for path, text in texts.items():
        rel = pathlib.Path(path).resolve().relative_to(ROOT.resolve())
        (tmp / rel).write_bytes(text.encode("utf-8"))
    return miniyaml.Ruleset(tmp), tmp


def flat(node, path=()):
    out = {}
    for c in node.children:
        k = path + (c.key,)
        out[k] = (c.value or "").strip()
        out.update(flat(c, k))
    return out


_FIELD_INDEX = None


def heaviness_capable(wtype):
    """True when the C# warhead class behind yaml type `wtype` has a `Heaviness` field — read
    from the same assembly index `audit_dead_warhead_fields` builds, never assumed."""
    global _FIELD_INDEX
    import audit_dead_warhead_fields as ad
    if _FIELD_INDEX is None:
        _FIELD_INDEX = ad.build_index(ROOT)
    got = ad.resolve_fields(_FIELD_INDEX, wtype + "Warhead")
    return bool(got and got[2] and "Heaviness" in got[0])


def _eff(raw, h):
    parts = [p.strip() for p in raw.split(",")]
    if not all(re.fullmatch(r"-?\d+", p) for p in parts):
        return None
    return [eh.scale_length(int(p), h) for p in parts]


def compare(old_rs, new_rs, weapon, renames):
    """Non-h-owned differences between the legacy and the re-pointed resolution of `weapon`.

    `renames` = every (family, level) re-pointed on the weapon's chain, so a multi-family
    weapon is compared once with all its renames. Returns {new node key: {field: pin}} where a
    pin is the value to author at the owner: a scalar string, a searched geometry inverse, or
    ("nested", legacy flat, new flat) for a nested field such as PhysicalStates."""
    a, b = old_rs.resolve_weapon(weapon), new_rs.resolve_weapon(weapon)
    rename = {f"Warhead@{f}_{l}{s}": f"Warhead@{f}{s}" for f, l in renames for s in SUFFIXES}
    diffs = collections.defaultdict(dict)
    na = {rename.get(c.key, c.key): c for c in a.children}
    nb = {c.key: c for c in b.children}
    # A main the weapon RETYPED (e.g. to SpreadDamage) cannot carry Heaviness: the base's h
    # fields would be dead there (FieldLoader drops them silently). Such a weapon stays levelled.
    for f, _l in renames:
        y = nb.get(f"Warhead@{f}")
        if y is not None and not heaviness_capable((y.value or "").strip()):
            diffs[f"Warhead@{f}"]["__type__"] = (y.value or "").strip()
    for key in set(na) | set(nb):
        if key.startswith("Inherits"):
            continue
        x, y = na.get(key), nb.get(key)
        if x is None or y is None:
            diffs[key]["__node__"] = "missing" if y is None else "extra"
            continue
        if not x.children and not y.children:              # weapon-level scalar
            if (x.value or "").strip() != (y.value or "").strip():
                diffs[""][key] = (x.value or "").strip()
            continue
        h = int(y.get("Heaviness")) if y.get("Heaviness") is not None else -1
        fx, fy = {c.key: c for c in x.children}, {c.key: c for c in y.children}
        for f in set(fx) | set(fy):
            if f in GEOMETRY:
                vx, vy = fx.get(f), fy.get(f)
                if vx is None or vy is None:
                    if vx is not vy:
                        diffs[key][f] = None                 # appears/disappears: review
                    continue
                legacy = [int(p) for p in vx.value.split(",")] if _eff(vx.value, -1) else None
                if legacy is None:
                    if vx.value.strip() != vy.value.strip():
                        diffs[key][f] = None
                    continue
                if _eff(vy.value, h) != legacy:
                    diffs[key][f] = ", ".join(str(_geom_inverse(v, h)) if h >= 0 else str(v) for v in legacy)
                continue
            if f in H_OWNED:
                continue
            if f in fx and f in fy and (fx[f].children or fy[f].children):
                ox, oy = flat(fx[f]), flat(fy[f])
                if ox != oy:
                    diffs[key][f] = ("nested", ox, oy)
                continue
            vx = (fx[f].value or "").strip() if f in fx else None
            vy = (fy[f].value or "").strip() if f in fy else None
            if vx != vy:
                # A field the BASE adds that the legacy resolution lacked is pinned as a
                # cancel (`-Field:`); its provider is the base, so it is never an orphan.
                diffs[key][f] = CANCEL if vx is None else vx
    return diffs


def geometry_ok(old_rs, new_rs, weapon, fam, lv):
    a, b = old_rs.resolve_weapon(weapon), new_rs.resolve_weapon(weapon)
    x = a.child(f"Warhead@{fam}_{lv}")
    y = b.child(f"Warhead@{fam}")
    if x is None or y is None:
        return True
    h = int(y.get("Heaviness") or LEVEL_H[lv])
    for f in GEOMETRY:
        vx, vy = x.get(f), y.get(f)
        if vx is None and vy is None:
            continue
        if vx is None or vy is None:
            return False
        px = [int(p) for p in vx.split(",")] if re.fullmatch(r"[\d, -]+", vx) else None
        py = [int(p) for p in vy.split(",")] if re.fullmatch(r"[\d, -]+", vy) else None
        if px is None or py is None or [eh.scale_length(p, h) for p in py] != px:
            return False
    return True


def run_once(rs, owners, base_ps, home_h, only_files):
    """One edit + pin + verify pass -> (texts, pins, residual, conflicts, checked, owner_of, renames)."""
    texts = edit_texts(rs, owners, base_ps, only_files)
    # Heaviness: every owner whose level is not its base's home gets an explicit value.
    pins = collections.defaultdict(lambda: collections.defaultdict(dict))
    for owner, fam, lv, _cl in owners:
        # ⛔ Never pin onto a node the owner CANCELS: pins are appended at the end of the def,
        # i.e. after a `-Warhead@F:`, so a pin there would resurrect the main warhead the weapon
        # removed on purpose (the W24 `_Flat` pattern — 8Inch, ArtilleryShell, ...).
        if LEVEL_H[lv] != home_h[fam] and rs.resolve_weapon(owner).child(f"Warhead@{fam}_{lv}") is not None:
            pins[owner][f"Warhead@{fam}"]["Heaviness"] = LEVEL_H[lv]
    texts = add_pins(texts, rs, pins)
    new_rs, tmp = scratch_ruleset(texts)

    # Every (family, level) re-pointed on each weapon's chain, and which owner carries it.
    renames = collections.defaultdict(set)
    owner_of = {}
    for owner, fam, lv, cl in owners:
        for w in cl:
            renames[w].add((fam, lv))
            owner_of[(w, fam)] = owner
    weapons = sorted(w for w in renames if not w.startswith("^"))

    def attribute(w, key):
        fam = next((f for f, _l in renames[w] if key.startswith(f"Warhead@{f}")
                    and key[len(f"Warhead@{f}"):] in SUFFIXES), None)
        if fam is None:
            fam = sorted(renames[w])[0][0]
        return owner_of[(w, fam)]

    # Pin every non-h field whose INHERITED value moved, at the owner (uniform across its
    # closure) — then re-resolve and require zero differences.
    extra = collections.defaultdict(lambda: collections.defaultdict(dict))
    conflicts = []
    for w in weapons:
        for key, fields in compare(rs, new_rs, w, renames[w]).items():
            owner = attribute(w, key)
            for f, v in fields.items():
                if f in ("__node__", "__type__") or v is None:
                    conflicts.append((w, key, f, v))
                    continue
                have = extra[owner][key].get(f)
                if have is not None and have != v:
                    conflicts.append((w, key, f, "disagrees across the closure"))
                extra[owner][key][f] = v
    for owner, nodes in extra.items():
        for key, fields in nodes.items():
            pins[owner][key].update(fields)
    texts = edit_texts(rs, owners, base_ps, only_files)
    texts = add_pins(texts, rs, pins)
    new_rs, tmp = scratch_ruleset(texts)

    residual, geom_bad, checked = [], [], 0
    for w in weapons:
        checked += 1
        d = compare(rs, new_rs, w, renames[w])
        if d:
            residual.append((w, dict(d)))
    shutil.rmtree(tmp, ignore_errors=True)
    return texts, pins, residual, conflicts, checked, owner_of, renames


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--only-file", nargs="*", default=None)
    args = ap.parse_args(argv)
    rs = miniyaml.Ruleset(ROOT)
    owners, skipped, fams = plan(rs)
    base_ps = {f: int(rs.resolve_weapon(f"^Warhead_{f}").child(f"Warhead@{f}").get("PercentageScale")) for f in fams}
    home_h = {f: int(rs.resolve_weapon(f"^Warhead_{f}").child(f"Warhead@{f}").get("Heaviness")) for f in fams}
    print(f"re-point owners: {len(owners)} definitions "
          f"({sum(len(c) for *_x, c in owners)} with descendants)")
    for why, rows in sorted(skipped.items()):
        print(f"  skipped — {why}: {len(rows)}")

    excluded = {}
    for _round in range(10):
        texts, pins, residual, conflicts, checked, owner_of, renames = run_once(
            rs, owners, base_ps, home_h, args.only_file)
        failing = {w for w, _d in residual} | {c[0] for c in conflicts}
        bad = {owner_of[(w, f)] for w in failing for f, _l in renames[w]}
        if not bad:
            break
        for o in bad:
            excluded[o] = sorted(w for w in failing
                                 if any(owner_of.get((w, f)) == o for f, _l in renames[w]))
        owners = [o for o in owners if o[0] not in bad]
    print(f"re-pointed after verification: {len(owners)} owner(s); verified {checked} concrete "
          f"weapons: non-h differences {len(residual)}, pin conflicts {len(conflicts)}")
    print(f"pins: {sum(len(f) for n in pins.values() for f in n.values())} field(s) on {len(pins)} owner(s)")
    print(f"excluded (left on their levelled template, need review): {len(excluded)} owner(s)")
    for o, ws in sorted(excluded.items())[:20]:
        print(f"  EXCLUDED {o}: {', '.join(ws[:4])}{' ...' if len(ws) > 4 else ''}")
    if residual or conflicts:
        print("NOT APPLIED — verification did not converge.")
        return 1
    if args.apply:
        for path, text in texts.items():
            pathlib.Path(path).write_bytes(text.encode("utf-8"))
        print(f"applied to {len(texts)} file(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
