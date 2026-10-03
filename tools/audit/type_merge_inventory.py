"""Inventory of duplicate yaml-facing C# types across every assembly (DESIGN §22, maintainer 2026-09-30).

The maintainer ruled that every mechanic has ONE implementation: where OpenRA, AS/RV, CA, Cameo, Cnc, D2k or
Fransbot each carry a variant of the same trait / projectile / warhead / bot module (`Missile` + `MissileCA`,
`BuildingRepairBotModule` + `BuildingRepairBotModuleCA`, ...), they are merged into one type holding every
feature, and only the merged type is used. This tool is step 1 of that programme: it finds the families.

For each family it reports:
  * the variants: yaml name, assembly, file, and which one `ObjectCreator.FindType` picks for a shared name
    (mod.yaml `Assemblies` order);
  * USE: how many resolved actors (traits) or weapons (projectiles, warheads) use each variant;
  * FIELDS: fields only one variant has, and shared fields whose C# defaults differ (a merge must write the
    old default explicitly wherever a user relied on it, or the conversion changes behaviour).

Families are grouped by NAME after stripping the source tags (CA, AS, SP, RV, Cameo, TS, RA2, D2k, Cnc,
the Frans prefix). A name match is a CANDIDATE, not a verdict: two types may share a stem and do different
things, and two types with different names may duplicate one another (e.g. BevManagerBotModule vs
McvExpansionManagerBotModule). The KNOWN_PAIRS table adds the second kind by hand.

  python tools/audit/type_merge_inventory.py                 # writes docs/design/TYPE_MERGE_INVENTORY.md
  python tools/audit/type_merge_inventory.py --stdout        # print instead

Needs a built engine (engine/OpenRA.Mods.*): without it the report says so and covers the mod side only.
"""

from __future__ import annotations

import argparse
import collections
import pathlib
import re
import sys

REPO = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "tools" / "audit"))
import miniyaml  # noqa: E402

OUT = REPO / "docs" / "design" / "TYPE_MERGE_INVENTORY.md"

# mod.yaml Assemblies order: FindType takes the FIRST assembly that has the name.
ASSEMBLIES = [
    ("AS", "engine/OpenRA.Mods.AS"),
    ("CA", "OpenRA.Mods.CA"),
    ("Cameo", "OpenRA.Mods.Cameo"),
    ("Cnc", "engine/OpenRA.Mods.Cnc"),
    ("D2k", "engine/OpenRA.Mods.D2k"),
    ("Common", "engine/OpenRA.Mods.Common"),
    ("Fransbot", "OpenRA.Mods.Fransbot"),
]

# Reference mods (not loaded by Cameo): only their types Cameo does NOT have are listed — features available to
# harvest (e.g. upstream CA's MissileCA / BulletCA, which Cameo's hand-copied CA snapshot never took).
# The reference checkouts sit next to the MAIN checkout (Documents/GitHub), not next to a worktree in C:/tmp.
GITHUB = next((p for p in [pathlib.Path(__import__("os").environ.get("CAMEO_REFERENCE_ROOT", "")),
                           REPO.parent, pathlib.Path.home() / "Documents" / "GitHub"]
               if str(p) not in ("", ".") and (p / "CAmod").is_dir()), REPO.parent)
REFERENCES = [
    ("ref:CA-upstream", GITHUB / "CAmod" / "OpenRA.Mods.CA"),
    ("ref:SP", GITHUB / "Shattered-Paradise-SDK" / "OpenRA.Mods.Sp"),
    ("ref:Generals", GITHUB / "Generals-Alpha" / "OpenRA.Mods.GenSDK"),
    ("ref:RV", GITHUB / "Romanovs-Vengeance" / "OpenRA.Mods.RA2"),
]

# Different names, same job — found by reading, not by the stem (§22 step 1 keeps this list growing).
KNOWN_PAIRS = {
    "mcvexpansion (BEV)": ["BevManagerBotModule", "McvExpansionManagerBotModule", "McvManagerBotModuleCA",
                           "McvManagerBotModule", "McvManagerASBotModule", "FransMcvExpansionManagerBotModule"],
    "engineer capture": ["CaptureManagerBotModuleCA", "CncEngineerBotModule", "CncEngineerManagerBotModule", "CaptureManagerBotModule",
                         "CaptureManagerBotASModule"],
}

CLASS_RE = re.compile(r"\b(?:public\s+|internal\s+)?(?:sealed\s+|abstract\s+)*class\s+(\w+)(?:<[^>]*>)?\s*:\s*([^{]+)\{", re.S)
FIELD_RE = re.compile(r"^\s*public\s+(?:readonly\s+)?(?!class|static|override|const|event|abstract|virtual)([\w<>\[\],. ?]+?)\s+(\w+)\s*(?:=\s*([^;]+))?;", re.M)
TAG_SUFFIX = re.compile(r"(CA|AS|SP|Sp|RV|TA|Cameo|TS|RA2|D2k|Cnc|Gen)$")
TAG_INFIX = re.compile(r"(CA|AS|SP|RV|Cameo)(?=(BotModule|Module|Warhead|Info)$)")


def stem(yaml_name: str) -> str:
    s = re.sub(r"^Frans", "", yaml_name)
    for _ in range(2):
        s = TAG_INFIX.sub("", s)
        s = TAG_SUFFIX.sub("", s)
    return s.lower()


def class_body(text: str, start: int) -> str:
    depth, i = 0, text.index("{", start)
    for j in range(i, len(text)):
        if text[j] == "{":
            depth += 1
        elif text[j] == "}":
            depth -= 1
            if depth == 0:
                return text[i + 1:j]
    return text[i + 1:]


def scan():
    """yaml-facing types: trait/projectile Infos (yaml name = class minus Info) and warheads (minus Warhead)."""
    types = {}   # yaml name -> list of variants
    missing = []
    sources = [(asm, REPO / root, False) for asm, root in ASSEMBLIES] + [(asm, path, True) for asm, path in REFERENCES]
    loaded_classes = set()
    for asm, base, is_ref in sources:
        if not base.is_dir():
            missing.append(base.as_posix())
            continue
        for path in base.rglob("*.cs"):
            if "/obj/" in path.as_posix() or "/bin/" in path.as_posix():
                continue
            text = path.read_text(encoding="utf-8", errors="replace")
            for m in CLASS_RE.finditer(text):
                name, bases = m.group(1), m.group(2)
                if is_ref and name in loaded_classes:
                    continue
                if not is_ref:
                    loaded_classes.add(name)
                kind = None
                if name.endswith("Info") and re.search(r"TraitInfo|IProjectileInfo|Info\b|IRulesetLoaded", bases):
                    yaml = name[:-4]
                    kind = "projectile" if "IProjectileInfo" in bases else "trait"
                elif name.endswith("Warhead") and "Warhead" in bases:
                    yaml = name[:-7]
                    kind = "warhead"
                if not kind or not yaml or "abstract" in text[max(0, m.start() - 40):m.start() + 20]:
                    continue
                body = class_body(text, m.end() - 1)
                fields = {fm.group(2): (fm.group(1).strip(), (fm.group(3) or "").strip())
                          for fm in FIELD_RE.finditer(body)}
                types.setdefault(yaml, []).append({
                    "yaml": yaml, "class": name, "asm": asm, "kind": kind, "bases": bases.strip(), "ref": is_ref,
                    "file": (path.relative_to(GITHUB) if is_ref else path.relative_to(REPO)).as_posix(), "fields": fields})
    return types, missing


def usage():
    """Resolved use counts: trait keys on actors, Projectile / Warhead values on weapons."""
    rs = miniyaml.Ruleset(REPO)
    trait_use, proj_use, wh_use = collections.Counter(), collections.Counter(), collections.Counter()
    for name in rs.actors:
        if name.startswith("^"):
            continue
        node = rs.resolve(name)
        if node is None:
            continue
        for c in node.children:
            if not c.key.startswith("-"):
                trait_use[c.key.split("@", 1)[0]] += 1
    for name in rs.weapons:
        if name.startswith("^"):
            continue
        node = rs.resolve_weapon(name)
        if node is None:
            continue
        for c in node.children:
            base = c.key.split("@", 1)[0]
            if base == "Projectile" and c.value:
                proj_use[c.value.strip()] += 1
            elif base == "Warhead" and c.value:
                wh_use[c.value.strip()] += 1
    return trait_use, proj_use, wh_use


ORDER = [a for a, _ in ASSEMBLIES]


def use_of(v, trait_use, proj_use, wh_use, types=None):
    """Resolved uses. A shared yaml name belongs to the FindType winner only; a shadowed sibling and a reference
    type are never loaded, so they count 0."""
    if v.get("ref"):
        return 0
    if types is not None:
        loaded = [x for x in types.get(v["yaml"], []) if not x.get("ref") and x["kind"] == v["kind"]]
        if len(loaded) > 1 and min(loaded, key=lambda x: ORDER.index(x["asm"])) is not v:
            return 0
    return {"trait": trait_use, "projectile": proj_use, "warhead": wh_use}[v["kind"]].get(v["yaml"], 0)


def field_diff(variants):
    names = [set(v["fields"]) for v in variants]
    shared = set.intersection(*names) if names else set()
    only = {v["class"]: sorted(set(v["fields"]) - shared) for v in variants}
    differ = []
    for f in sorted(shared):
        defaults = {v["class"]: v["fields"][f][1] for v in variants}
        if len(set(defaults.values())) > 1:
            differ.append((f, defaults))
    return only, differ


def families(types):
    by_stem = collections.defaultdict(list)
    for yaml, vs in types.items():
        for v in vs:
            by_stem[(v["kind"], stem(yaml))].append(v)
    fams = {f"{k[1]} ({k[0]})": vs for k, vs in by_stem.items()
            if len({(v['asm'], v['class']) for v in vs}) > 1 and any(not v.get("ref") for v in vs)}
    flat = {v["yaml"]: v for vs in types.values() for v in vs}
    for label, members in KNOWN_PAIRS.items():
        vs = [flat[m] for m in members if m in flat]
        if len(vs) > 1:
            fams[label] = vs
    return fams


def render(fams, missing, trait_use, proj_use, wh_use, types):
    order = [a for a, _ in ASSEMBLIES]
    rows = []
    for label, vs in fams.items():
        uses = [use_of(v, trait_use, proj_use, wh_use, types) for v in vs]
        live = sum(1 for u in uses if u > 0)
        rows.append((label, vs, uses, live))
    rows.sort(key=lambda r: (-r[3], -sum(r[2]), r[0]))

    live2 = sum(1 for r in rows if r[3] >= 2)
    out = ["# Type merge inventory — every mechanic with more than one implementation",
           "",
           "_Generated by `python tools/audit/type_merge_inventory.py` (DESIGN §22). Do not edit by hand._",
           ""]
    if missing:
        out += [f"⚠ **INCOMPLETE:** not scanned (engine not built?): {', '.join(missing)}.", ""]
    out += [f"**{len(rows)} families** with 2+ variants; **{live2}** have two or more variants IN USE at once "
            "(merge first: those run side by side today); the rest have one live variant and dead siblings "
            "(merge the siblings' features in, then delete them).",
            "",
            "USE = resolved actors (traits) or weapons (projectiles, warheads) using the variant. FindType = the "
            "variant a shared yaml name resolves to (first assembly in `mod.yaml` Assemblies: "
            + " → ".join(order) + ").",
            "",
            "| family | variants in use | total USE | variants (assembly: yaml name = USE) | fields only in one | shared fields, different default |",
            "|---|--:|--:|---|--:|--:|"]
    for label, vs, uses, live in rows:
        only, differ = field_diff(vs)
        desc = "<br>".join(f"{v['asm']}: `{v['yaml']}` = {u}" + (" (shadowed)" if not v.get("ref") and u == 0 and any(
            x is not v and x["yaml"] == v["yaml"] and not x.get("ref") for x in vs) else "") for v, u in zip(vs, uses))
        out.append(f"| {label} | {live} | {sum(uses)} | {desc} | {sum(len(x) for x in only.values())} | {len(differ)} |")

    out += ["", "## Field detail for the families with 2+ variants in use", ""]
    for label, vs, uses, live in rows:
        if live < 2:
            continue
        only, differ = field_diff(vs)
        out += [f"### {label}", ""]
        for v, u in zip(vs, uses):
            out.append(f"* `{v['class']}` ({v['asm']}, `{v['file']}`), USE {u}: only here: "
                       + (", ".join(f"`{f}`" for f in only[v['class']][:30]) or "—")
                       + (" …" if len(only[v['class']]) > 30 else ""))
        if differ:
            out.append("* shared, different defaults: " + "; ".join(
                f"`{f}` (" + ", ".join(f"{c}={d or '∅'}" for c, d in ds.items()) + ")" for f, ds in differ[:20]))
        out.append("")
    return "\n".join(out) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--stdout", action="store_true")
    args = ap.parse_args()
    types, missing = scan()
    trait_use, proj_use, wh_use = usage()
    text = render(families(types), missing, trait_use, proj_use, wh_use, types)
    if args.stdout:
        print(text)
    else:
        OUT.write_text(text, encoding="utf-8")
        print(f"wrote {OUT.relative_to(REPO).as_posix()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
