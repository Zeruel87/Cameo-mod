#!/usr/bin/env python3
"""ContentPack asset migration: census + apply.

Phase 1 (census): collect every file-token reference (ext-matched, pkg|name aware)
in a theme's yaml, locate each file under bits/, classify ownership
(theme-exclusive vs shared-with-other-themes), and emit a move plan.

Phase 2 (--apply): shadow-copy theme-exclusive files into the owning pack's
files/<type>/ dir, add `~cameo|.../files/<type>: <pkg>` mounts to mod.yaml
(before the `cameo|bits` line), and rewrite bare refs to `pkg|name`.

Type dirs: icons (basename has 'icon'/'icnh' OR .png referenced... rule below),
sprites (shp/tem/sno/int/pal/png), voxels (vxl/hva), sounds (wav/aud).
Mounted packages that are single files (.bag/.idx/.mix) move by mount swap,
not by file tokens (handled by --move-packages).

Usage:
    python tools/packs/migrate_assets.py --theme RedAlert2            # census
    python tools/packs/migrate_assets.py --theme RedAlert2 --apply    # do it
"""
import argparse, json, os, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MOD = ROOT / "mods" / "cameo"
FILE_EXT = re.compile(r"\.(shp|tem|sno|int|vxl|hva|wav|aud|png|pal)$", re.I)
ICON_NAME = re.compile(r"(icon|icnh|iconv|_icn)", re.I)

def norm(p): return str(p).replace("\\", "/").lower()

def yaml_files_under(dirpath):
    return sorted(dirpath.rglob("*.yaml")) if dirpath.is_dir() else []

def theme_of(path):
    """Owning theme name for a yaml path, else None."""
    r = norm(path)
    m = re.search(r"contentpacks/([^/]+)/", r)
    if m: return "ContentPacks:" + m.group(1)
    if "/rules/" in r or "/sequences/" in r or "/weapons/" in r or "/audio/" in r:
        return "core:" + r.split("/")[-1]
    return "other"

def collect_refs(path):
    """All ext-matching tokens in a yaml file -> [(rawtoken, name, pkg_or_None)]."""
    out = []
    try: text = path.read_text(encoding="utf-8", errors="replace")
    except OSError: return out
    for line in text.splitlines():
        # strip comments
        s = line.split("#", 1)[0]
        for tok in re.split(r"[\s,'\"]+", s):
            if not FILE_EXT.search(tok):
                continue
            base = tok.rsplit("|", 1)[-1]
            if not base.rsplit(".", 1)[0]:   # bare extension like ".WAV"
                continue
            if "|" in tok:
                pkg, name = tok.split("|", 1)
                out.append((tok, name, pkg))
            else:
                out.append((tok, tok, None))
    return out

def collect_voxel_models(path):
    """Actors whose node carries an uncommented RenderVoxels (directly or via
    Inherits@*: ^RenderVoxel) -> [(actorid, image_name, has_tur, has_barl)].
    Voxels resolve by NAME CONVENTION: <img>.vxl/.hva, <img>tur.*, <img>barl.*."""
    out = []
    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return out
    actor = None; in_rv = False; img = None; tur = False; barl = False
    has_rv = False

    def flush():
        if actor and has_rv:
            out.append((actor, img or actor, tur, barl))

    for raw in lines:
        s = raw.split("#", 1)[0].rstrip()
        if not s.strip():
            continue
        indent = len(raw) - len(raw.lstrip("\t "))
        toks = s.strip()
        if indent == 0:
            flush()
            actor = toks.split(":")[0].strip()
            img, tur, barl, has_rv = None, False, False, False
            in_rv = False
            continue
        if indent == 1:
            in_rv = toks.startswith("RenderVoxels:")
            if toks.startswith("RenderVoxels:"):
                has_rv = True
            if re.match(r"Inherits@\w+: *\^RenderVoxel", toks):
                has_rv = True
            if toks.startswith("WithVoxelTurret"):
                tur = True
            if toks.startswith("WithVoxelBarrel"):
                barl = True
            continue
        if in_rv and indent == 2 and toks.startswith("Image:"):
            img = toks.split(":", 1)[1].strip()
    flush()
    return out

def type_dir(name, ext):
    ext = ext.lower()
    if ext in (".vxl", ".hva"): return "voxels"
    if ext in (".wav", ".aud"): return "sounds"
    if ICON_NAME.search(name): return "icons"
    return "sprites"

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--theme", required=True, help="e.g. RedAlert2")
    ap.add_argument("--voxels", action="store_true",
                    help="also collect RenderVoxels name-convention files")
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--prefix-existing", action="store_true",
                    help="also rewrite bare refs for files already inside "
                         "the theme's files/ dirs (half-done migrations)")
    ap.add_argument("--pkg-prefix", default=None, help="default ra2")
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    theme_dir = MOD / "ContentPacks" / args.theme
    if not theme_dir.is_dir():
        sys.exit(f"no such theme dir: {theme_dir}")
    prefix = args.pkg_prefix or args.theme.lower()

    # pack dirs under the theme (canonical casing), plus shared fallbacks
    CANON = {d.name.lower(): d.name for d in theme_dir.iterdir()
             if d.is_dir() and d.name not in ("yaml", "files", "translations")}
    CANON["yaml"] = "Shared"      # theme-level yaml/ dir -> Shared pack
    CANON.setdefault("shared", "Shared")
    def canon(o):
        return CANON.get(str(o).lower(), "Shared")

    theme_yamls = yaml_files_under(theme_dir)
    # theme monoliths living outside the pack dir:
    #  (a) files the theme's own content.yaml(s) declare (e.g. wrapper packs
    #      include cameo|rules/<theme>.yaml)
    #  (b) LIVE core-dir entries in mod.yaml named <theme>.yaml
    #      (sequences/, weapons/, audio/, tilesets/ monoliths)
    CORE_DIRS = ("rules", "sequences", "weapons", "audio", "tilesets")
    for cy in theme_dir.rglob("content.yaml"):
        for m in re.finditer(r"^\s*cameo\|(\S+\.ya?ml)", cy.read_text(errors="replace"), re.M):
            p = MOD / m.group(1)
            if p.exists() and p not in theme_yamls:
                theme_yamls.append(p)
    my_lines = (MOD / "mod.yaml").read_text(encoding="utf-8", errors="replace").splitlines()
    mono_name = args.theme.lower() + ".yaml"
    for line in my_lines:
        s = line.strip()
        if s.startswith("#") or "|" not in s:
            continue
        path = s.split("|", 1)[1].split()[0]
        parts = path.split("/")
        if len(parts) == 2 and parts[0] in CORE_DIRS and parts[1].lower() == mono_name:
            p = MOD / path
            if p.exists() and p not in theme_yamls:
                theme_yamls.append(p)

    all_yamls = [p for p in MOD.rglob("*.yaml")
                 if "/bits/" not in norm(p)]
    theme_set = {norm(p) for p in theme_yamls}

    # 1. refs in theme yaml, grouped by file token
    refs = {}          # name(lower) -> {"refs": set(yaml), "pkg": pkg|None}
    for y in theme_yamls:
        for raw, name, pkg in collect_refs(y):
            e = refs.setdefault(name.lower(), {"name": name, "refs": set(), "pkg": pkg})
            e["refs"].add(norm(y))

    # 2. refs in non-theme yaml (for exclusivity)
    foreign = {}
    for y in all_yamls:
        if norm(y) in theme_set: continue
        for raw, name, pkg in collect_refs(y):
            foreign.setdefault(name.lower(), set()).add(norm(y))

    # 2b. voxel name-convention files (RenderVoxels actors)
    if args.voxels:
        theme_models = {}   # image(lower) -> (actor, yaml, tur, barl)
        for y in theme_yamls:
            for actor, img, tur, barl in collect_voxel_models(y):
                theme_models.setdefault(img.lower(), (actor, norm(y), tur, barl))
        # foreign themes' voxel image names (for exclusivity)
        foreign_models = set()
        for y in all_yamls:
            if norm(y) in theme_set: continue
            for actor, img, tur, barl in collect_voxel_models(y):
                foreign_models.add(img.lower())
        for img, (actor, yr, tur, barl) in theme_models.items():
            sufs = ["", "tur" if tur else None, "barl" if barl else None]
            for suf in [s for s in sufs if s is not None]:
                for ext in (".vxl", ".hva"):
                    fname = f"{img}{suf}{ext}"
                e = refs.setdefault(fname, {"name": fname, "refs": {yr},
                                            "pkg": None})
                e["refs"].add(yr)
                # foreign exclusivity: same image name in another theme
                if img in foreign_models:
                    foreign.setdefault(fname, set()).add("voxel-name-collision")

    # 3. bits file index + .idx (AudPackage) name indexes
    bits_index = {}    # basename(lower) -> [relpaths]
    bag_index = {}     # bag relpath -> set(names inside, no ext)
    for p in (MOD / "bits").rglob("*"):
        if p.is_file():
            bits_index.setdefault(p.name.lower(), []).append(norm(p.relative_to(MOD)))
            if p.suffix.lower() in (".idx", ".rs", ".r8", ".r16"):
                try:
                    data = p.read_bytes()
                    names = {m.group(0).rstrip(b"\x00").decode().lower()
                             for m in re.finditer(rb"[a-z0-9_]{3,}\x00", data)}
                    # RS/R8/R16 embed full names with extensions (often
                    # uppercase), so match case-insensitively.
                    names |= {m.group(0).decode().lower()
                              for m in re.finditer(
                                  rb"[a-zA-Z0-9_]{2,}\.(wav|aud|shp|png|tem)",
                                  data, re.IGNORECASE)}
                    bag_index[norm(p.relative_to(MOD))] = names
                except OSError:
                    pass
    in_bag = {}        # bare name(lower) -> bag relpath
    for bag, names in bag_index.items():
        for n in names:
            in_bag.setdefault(n, bag)

    # 4. classify
    plan, shared, missing, qualified, packaged = [], [], [], [], []
    for key, e in refs.items():
        name, yrefs = e["name"], e["refs"]
        if e["pkg"]:
            qualified.append({"name": name, "pkg": e["pkg"], "refs": len(yrefs)})
            continue
        srcs = bits_index.get(key, [])
        if not srcs:
            stem = key.rsplit(".", 1)[0]
            bag = in_bag.get(key) or in_bag.get(stem)
            if bag:
                packaged.append({"name": name, "bag": bag,
                                 "refs": len(yrefs)})
            else:
                missing.append({"name": name, "refs": len(yrefs)})
            continue
        foreign_refs = [f for f in foreign.get(key, [])]
        if foreign_refs:
            shared.append({"name": name, "src": srcs, "foreign": foreign_refs})
            continue
        if len(srcs) > 1:
            # ambiguity: prefer one under bits/<prefix>*
            pref = [s for s in srcs if s.startswith(f"bits/{prefix}")]
            src = pref[0] if len(pref) == 1 else None
            if src is None:
                shared.append({"name": name, "src": srcs, "foreign": [],
                               "note": "ambiguous-multi"})
                continue
        else:
            src = srcs[0]
        # owning subpack: packs (dirs) of referencing yamls
        owners = set()
        for yr in yrefs:
            m = re.search(r"contentpacks/[^/]+/([^/]+)/", yr)
            owners.add(CANON.get(m.group(1), "Shared") if m else "Shared")
        owner = "Shared" if len(owners) != 1 else sorted(owners)[0]
        ext = os.path.splitext(name)[1]
        plan.append({"name": name, "src": src, "owner": owner,
                     "type": type_dir(name, ext), "refs": len(yrefs)})

    pkgs = {(p["owner"], p["type"]) for p in plan}
    report = {
        "theme": args.theme, "refs": len(refs),
        "migrate": len(plan), "shared": len(shared),
        "missing": len(missing), "qualified": len(qualified),
        "packaged": len(packaged),
        "packages_needed": sorted(f"{prefix}_{o.lower()}_{t}" for o, t in pkgs),
        "plan": plan,
        "shared_detail": shared[:50], "missing_detail": missing[:50],
        "qualified_detail": qualified[:50],
        "packaged_detail": packaged[:50],
    }
    out = args.out or f"docs/migration/{args.theme.lower()}_assets.json"
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    Path(out).write_text(json.dumps(report, indent=1))
    print(f"refs={len(refs)} migrate={len(plan)} shared={len(shared)} "
          f"missing={len(missing)} qualified={len(qualified)} "
          f"packaged={len(packaged)}")
    print("pkgs:", *report["packages_needed"], sep="\n  ")
    by = {}
    for p in plan: by[(p["owner"], p["type"])] = by.get((p["owner"], p["type"]), 0) + 1
    for k, v in sorted(by.items()): print(f"  {k}: {v}")
    if missing:
        print("MISSING:", *(m["name"] for m in missing[:20]), sep=" ")
    if not args.apply:
        return

    # --- apply: copy + mounts + rewrite ---
    import shutil
    copied = []
    for p in plan:
        dest_dir = theme_dir / canon(p["owner"]) / "files" / p["type"]
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest = dest_dir / p["name"]
        shutil.copy2(MOD / p["src"], dest)
        copied.append((p["name"], str(dest.relative_to(ROOT))))
    print(f"copied {len(copied)} files")

    # mod.yaml mounts, derived from the files/ dirs that now exist (idempotent):
    # ~cameo|ContentPacks/<T>/<O>/files/<t>: <prefix>_<o>_<t>
    modyaml = ROOT / "mods" / "cameo" / "mod.yaml"
    lines = modyaml.read_text(encoding="utf-8").splitlines()
    anchors = [i for i, l in enumerate(lines) if "cameo|bits:" in l]
    if not anchors:
        sys.exit("no `cameo|bits:` anchor in mod.yaml")
    anchor = anchors[0]
    existing = set(lines)
    mounts = []
    for o in sorted(set(CANON.values())):
        fd = theme_dir / o / "files"
        if not fd.is_dir():
            continue
        for t in sorted(fd.iterdir()):
            if t.is_dir() and any(t.iterdir()):
                pkg = f"{prefix}_{o.lower()}_{t.name}"
                line = f"\t\t~cameo|ContentPacks/{args.theme}/{o}/files/{t.name}: {pkg}"
                if line not in existing:
                    mounts.append(line)
    if mounts:
        lines[anchor:anchor] = mounts
        modyaml.write_text("\n".join(lines) + "\n", encoding="utf-8")
        print(f"added {len(mounts)} mounts to mod.yaml")

    # rewrite refs in theme yaml: bare name -> pkg|name
    name_pkg = {}
    for p in plan:
        name_pkg[p["name"].lower()] = (
            p["name"], f"{prefix}_{canon(p['owner']).lower()}_{p['type']}")

    # files already in the theme's packs (half-done migrations): prefix their
    # bare refs too, preferring the referencing yaml's own pack, then Shared.
    if args.prefix_existing:
        pack_index = {}   # name(lower) -> [(pack, type)]
        for packdir in theme_dir.iterdir():
            fd = packdir / "files" if packdir.is_dir() else None
            if not fd or not fd.is_dir():
                continue
            for td in fd.iterdir():
                if not td.is_dir():
                    continue
                for f in td.iterdir():
                    if f.is_file():
                        pack_index.setdefault(f.name.lower(), []).append(
                            (packdir.name, td.name))
        for y in theme_yamls:
            m = re.search(r"contentpacks/[^/]+/([^/]+)/", norm(y))
            ypack = canon(m.group(1)) if m else "Shared"
            for raw, name, pkg in collect_refs(y):
                if pkg:
                    continue
                cands = pack_index.get(name.lower())
                if not cands or name.lower() in name_pkg:
                    continue
                pick = ([c for c in cands if c[0] == ypack]
                        or [c for c in cands if c[0] == "Shared"]
                        or ([cands[0]] if len(cands) == 1 else []))
                if pick:
                    pk, t = pick[0]
                    name_pkg[name.lower()] = (
                        name, f"{prefix}_{pk.lower()}_{t}")
        n_prefixed = len(name_pkg) - len(plan)
        print(f"prefix-existing: +{n_prefixed} refs qualify against pack files")
    n_repl = 0
    for y in theme_yamls:
        text = y.read_text(encoding="utf-8", errors="replace")
        orig = text
        # file tokens present in THIS file
        for raw, name, pkg in collect_refs(y):
            if pkg:
                continue
            ent = name_pkg.get(name.lower())
            if ent is None:
                continue
            fname, pkgname = ent
            # whole-token replace of the bare name (case-insensitive; the
            # replacement uses the on-disk filename casing)
            pat = re.compile(r"(?<![\w.|/])" + re.escape(name) + r"(?![\w.])",
                             re.IGNORECASE)
            text = pat.sub(f"{pkgname}|{fname}", text)
        if text != orig:
            y.write_text(text, encoding="utf-8")
            n_repl += 1
    print(f"rewrote refs in {n_repl} yaml files")


if __name__ == "__main__":
    main()
