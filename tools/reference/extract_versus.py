#!/usr/bin/env python3
"""extract_versus.py — harvest warhead-vs-armor tables from every reference mod.

Layer 1 of the 3-layer balance framework (`ORIGINAL_UNIT_STATS.md`): what the FIELD
does, before we decide what Cameo should do. The earlier reference pass captured unit
stats (HP / speed / cost / damage) but never the armor-multiplier dimension, which is
the one that decides whether a weapon is a specialist or a generalist.

Two source families, both read-only:

* **OpenRA mods** (Combined Arms, Shattered Paradise, Romanov's Vengeance, and the
  vanilla ra/cnc/ts/d2k trees) write a named `Versus:` block — armor names are explicit,
  so no decoding risk.
* **Westwood-engine mods** (RA2, YR, Mental Omega, CnC Reloaded, DTA) write
  `Verses=100%,70%,...` — a POSITIONAL list against the engine's armor enumeration.

The positional form is the dangerous one: decode it against the wrong enumeration and
every value silently shifts by one armor, producing a table that looks plausible and is
entirely wrong. So arity is a HARD GUARD here — a row whose value count does not match a
known enumeration is recorded as `undecoded` with its raw values kept, never guessed at.
Measured arities (2026-08-11): RA2/YR/MO 11 uniformly; CnCR 353x11 + one 13 + one 15
(Ares can add armor types); DTA a mix of 5/10/9.

Usage:
    python tools/reference/extract_versus.py              # write the dataset
    python tools/reference/extract_versus.py --summary    # print coverage only
"""

from __future__ import annotations

import argparse
import json
import pathlib
import re
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

ROOT = pathlib.Path(__file__).resolve().parents[2]
OUT_DIR = ROOT / "docs/reference"

# --- Armor enumerations -----------------------------------------------------
# Order IS the data for `Verses=`. Each entry is keyed by the number of values, so a
# file that disagrees is refused rather than mis-decoded.
YR_ARMORS = ("none", "flak", "plate", "light", "medium", "heavy",
             "wood", "steel", "concrete", "drone", "special")
TS_ARMORS = ("none", "wood", "light", "heavy", "concrete")

ARMOR_ORDERS = {
    "yr": {11: YR_ARMORS},
    "ts": {5: TS_ARMORS},
}

# --- Sources ----------------------------------------------------------------
# Paths are MACHINE-SPECIFIC (the maintainer's boxes). Missing sources are reported,
# never fatal, so the dataset can be rebuilt with whatever is present.
DOWNLOADS = pathlib.Path.home() / "Downloads"
BACKUP = pathlib.Path("G:/BackUp/AedisToru/Desktop")

SOURCES = [
    # (id, game/lineage, kind, path, engine)
    ("combined_arms", "TD+RA1", "openra", DOWNLOADS / "CAmod-master", None),
    ("shattered_paradise", "TS", "openra", DOWNLOADS / "Shattered-Paradise-SDK-bleed", None),
    ("romanovs_vengeance", "RA2", "openra", DOWNLOADS / "Romanovs-Vengeance-master", None),
    ("openra_ra", "RA1", "openra", DOWNLOADS / "OpenRA-bleed/mods/ra", None),
    ("openra_td", "TD", "openra", DOWNLOADS / "OpenRA-bleed/mods/cnc", None),
    ("openra_ts", "TS", "openra", DOWNLOADS / "OpenRA-bleed/mods/ts", None),
    ("openra_d2k", "D2K", "openra", DOWNLOADS / "OpenRA-bleed/mods/d2k", None),
    ("ra2_vanilla", "RA2", "ini", DOWNLOADS / "RA2inis/rules.ini", "yr"),
    ("yr_vanilla", "YR", "ini", DOWNLOADS / "YRinis/rulesmd.ini", "yr"),
    ("cnc_reloaded", "YR", "ini",
     DOWNLOADS / "CnCReloaded-2.7.0/Tools/Map Editor/rulesmd.ini", "yr"),
    # ⚠ NOT `MentalOmega/rulesmd.ini` — that loose file is vanilla Yuri's Revenge byte
    # for byte (both md5 cf7eb658327aff1fe7e6c4e7400eb87f, 31061 lines, 116 Verses).
    # Harvesting it double-counts vanilla YR and yields zero Mental Omega data. The real
    # ruleset ("Mental Omega 3.3.6 RULES CONTROL FILE", 751 Verses) lives inside
    # expandmo99.mix; extract it with tools/reference/extract_mix_ini.py.
    ("mental_omega", "YR", "ini", BACKUP / "MentalOmega/extracted/rulesmd_MO336.ini", "yr"),
    # Added 2026-08-15 on 333ggg's recommendation. Both hide their real rules inside a
    # MIX exactly like Mental Omega, so both are extracted with extract_mix_ini.py first:
    #   Red Resurrection : rr_update_2213/expandmd99.mix          -> 499 Verses
    #   RA2 Reborn       : .../Resources/INI.mix                  -> 359 Verses
    # The blob names are CRC-derived, not meaningful; the sniffer picks the rules blob.
    ("red_resurrection", "YR", "ini",
     DOWNLOADS / "_extracted_rr/expandmd99_8218f9f4.ini", "yr"),
    ("ra2_reborn", "YR", "ini",
     DOWNLOADS / "_extracted_reborn/INI_c5d7f6ce.ini", "yr"),
    # DTA ships its live balance in the injected GlobalCode, NOT in Rules.ini — every
    # `Verses=` in Rules.ini/Enhance.ini is commented out (186 of them, kept as design
    # history). "Classic" and "Enhanced" are two rule sets and both are wanted.
    # DTA ships TWO rule sets and the maintainer wants both: Rules.ini is CLASSIC mode,
    # Enhance.ini is ENHANCED mode. Both use the named `Modifier.<armor>` dialect
    # (688 and 78 lines); the Release and Developer editions carry identical counts.
    ("dta_classic", "TD", "ini", BACKUP / "DTA/DTA Release/INI/Base/Rules.ini", "ts"),
    ("dta_enhanced", "TD", "ini", BACKUP / "DTA/DTA Release/INI/Base/Enhance.ini", "ts"),
    ("dta_globalcode", "TD", "ini",
     BACKUP / "DTA/DTA Developer Edition/INI/Map Code/GlobalCode - Copy.ini", "ts"),
]

INI_SECTION = re.compile(r"^\s*\[([^\]]+)\]")
INI_VERSES = re.compile(r"^\s*Verses\s*=\s*(.+?)\s*(?:;.*)?$", re.IGNORECASE)
# DTA (TS + Vinifera) writes NAMED per-armor keys instead of the positional list:
#     Modifier.none=1000%
#     Modifier.heavy=250%
# Every `Verses=` in DTA is commented out, so looking only for the positional form
# finds nothing and wrongly concludes DTA has no armor profiles. Named keys are also
# safer — there is no ordering to get wrong.
INI_MODIFIER = re.compile(r"^\s*Modifier\.([A-Za-z_]+)\s*=\s*(.+?)\s*(?:;.*)?$",
                          re.IGNORECASE)


def _pct(token: str):
    """"70%" -> 70.0. Returns None for a value that is not a number."""
    token = token.strip().rstrip("%").strip()
    try:
        return float(token)
    except ValueError:
        return None


def parse_ini(path: pathlib.Path, engine: str) -> list[dict]:
    """[Warhead] sections carrying ACTIVE armor multipliers (comments are skipped).

    Handles both dialects: the positional `Verses=` list and DTA's named
    `Modifier.<armor>=` keys, which accumulate per section.
    """
    orders = ARMOR_ORDERS[engine]
    rows, section = [], None
    named: dict[str, dict[str, float]] = {}
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if line.lstrip().startswith(";"):
            continue                                    # commented-out history
        head = INI_SECTION.match(line)
        if head:
            section = head.group(1)
            continue
        named_hit = INI_MODIFIER.match(line)
        if named_hit and section is not None:
            value = _pct(named_hit.group(2))
            if value is not None:
                named.setdefault(section, {})[named_hit.group(1).lower()] = value
            continue
        hit = INI_VERSES.match(line)
        if not hit or section is None:
            continue
        raw = [t for t in hit.group(1).split(",")]
        values = [_pct(t) for t in raw]
        order = orders.get(len(values))
        row = {"warhead": section, "arity": len(values)}
        if order and all(v is not None for v in values):
            row["versus"] = dict(zip(order, values))
        else:
            # Refuse to guess: an unknown arity means an engine-extended armor list.
            row["undecoded"] = [t.strip() for t in raw]
        rows.append(row)
    seen = {r["warhead"] for r in rows}
    for warhead, versus in named.items():
        if warhead not in seen:
            rows.append({"warhead": warhead, "arity": len(versus), "versus": versus})
    return rows


def parse_dta_overlay(rules: pathlib.Path, overlay: pathlib.Path | None = None) -> list[dict]:
    """Named DTA fields after section/key overlay merging.

    Already generated DTA files retain BaseSection after copying parent keys.
    Audit that closure; do not re-inherit after overlay merging or certify runtime.
    """
    from extract_ini_units import read_ini, merge_overlay
    from dta_preprocessing import audit
    data = read_ini(rules)
    inherited = audit(rules)['inherited']
    if overlay is not None:
        data = merge_overlay(data, read_ini(overlay))
        inherited.update(audit(overlay)['inherited'])
    rows = []
    for name, section in data.items():
        fields = {k.split('.', 1)[1].lower(): v for k, v in section.items()
                  if k.lower().startswith('modifier.')}
        if not fields:
            continue
        values = {armor: _pct(value) for armor, value in fields.items()}
        row = {"warhead": name, "arity": len(values)}
        if all(v is not None for v in values.values()):
            row["versus"] = values
        else:
            row["undecoded"] = [f"{k}={v}" for k, v in fields.items()]
        if section.get('BaseSection'):
            row["base_section"] = section['BaseSection']
            row["inheritance_status"] = inherited.get(name, {}).get('status', 'not resolved')
        rows.append(row)
    return rows


def parse_openra(root: pathlib.Path) -> list[dict]:
    """`Versus:` blocks from a foreign OpenRA tree.

    Deliberately a small indentation reader rather than Cameo's `miniyaml`: these are
    other mods' trees with their own layouts, and this only needs the block that
    follows a `Versus:` line.
    """
    rows = []
    for path in sorted(root.rglob("*.yaml")):
        try:
            lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
        except OSError:
            continue
        owner = None                                    # nearest non-indented key
        for i, line in enumerate(lines):
            if line and not line[0].isspace() and not line.lstrip().startswith("#"):
                owner = line.split(":", 1)[0].strip()
            if line.strip().rstrip(":") != "Versus" or not line.strip().endswith(":"):
                continue
            indent = len(line) - len(line.lstrip())
            versus = {}
            for child in lines[i + 1:]:
                if not child.strip() or child.lstrip().startswith("#"):
                    continue
                child_indent = len(child) - len(child.lstrip())
                if child_indent <= indent:
                    break
                if ":" not in child:
                    break
                key, _, value = child.strip().partition(":")
                pct = _pct(value)
                if pct is None:
                    break
                versus[key.strip().lower()] = pct
            if versus:
                rows.append({"warhead": owner or path.stem, "arity": len(versus),
                             "versus": versus,
                             "file": str(path.relative_to(root)).replace("\\", "/")})
    return rows


def collect() -> dict:
    dataset, missing = {}, []
    for sid, lineage, kind, path, engine in SOURCES:
        if not path.exists():
            missing.append((sid, str(path)))
            continue
        if sid == "dta_enhanced":
            base = path.with_name("Rules.ini")
            if not base.exists():
                missing.append((sid, str(base)))
                continue
            rows = parse_dta_overlay(base, path)
        elif sid == "dta_classic":
            rows = parse_dta_overlay(path)
        else:
            rows = parse_ini(path, engine) if kind == "ini" else parse_openra(path)
        dataset[sid] = {"lineage": lineage, "kind": kind, "path": str(path),
                        "rows": rows}
        if sid == "dta_enhanced":
            dataset[sid]["base_path"] = str(base)
            dataset[sid]["overlay_merged"] = True
    return {"sources": dataset, "missing": missing}


def summarise(data: dict) -> str:
    out = ["| source | lineage | kind | warheads | decoded | undecoded |",
           "|---|---|---|---|---|---|"]
    total = decoded_total = 0
    for sid, entry in sorted(data["sources"].items()):
        rows = entry["rows"]
        decoded = sum(1 for r in rows if "versus" in r)
        total += len(rows)
        decoded_total += decoded
        out.append(f"| `{sid}` | {entry['lineage']} | {entry['kind']} | {len(rows)} | "
                   f"{decoded} | {len(rows) - decoded} |")
    out.append(f"| **TOTAL** | | | **{total}** | **{decoded_total}** | "
               f"**{total - decoded_total}** |")
    if data["missing"]:
        out.append("\n**Missing sources** (not fatal — rebuild when present):\n")
        for sid, path in data["missing"]:
            out.append(f"- `{sid}` → `{path}`")
    return "\n".join(out)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--summary", action="store_true", help="print coverage, write nothing")
    args = ap.parse_args()

    data = collect()
    print(summarise(data))
    if args.summary:
        return 0

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    target = OUT_DIR / "versus_raw.json"
    target.write_text(json.dumps(data, indent=1, sort_keys=True) + "\n",
                      encoding="utf-8", newline="\n")
    print(f"\nwrote {target.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
