#!/usr/bin/env python3
"""The role of a Tiberian Sun projectile, read from `AA=` / `AG=` — never from its NAME.

WHY THIS EXISTS. The OpenRA peers declare a weapon's targeting envelope as `ValidTargets`, so
`armament_roles.role_of_targets` can read it straight out of the corpus. The TS/RA2 engine has no
such field: the domain lives on the PROJECTILE, as two booleans, and the corpus rows carry only
the projectile's NAME. Without this file every INI source abstains from per-armament pairing —
which is exactly the source the maintainer named:

    "use DTA for the missile as reference only while using the cannon reference from all 3!"

⛔ AND THE NAME IS A TRAP. DTA's mammoth Tusk flies `[AGHeatSeeker2]` — "AG" right there in the
section name — which declares `$Inherits=AGHeatSeeker` and then `AA=yes`. It is a DUAL-role
missile, so the DTA mammoth's secondary is `both`, which is what makes it the correct partner for
Cameo's `MissileAP_Heavy` and for CA's `MammothTusk` (Air, AirSmall, Infantry). A name classifier
calls it anti-ground and pairs an air missile against a cannon. Measured 2026-09-13.

This extractor remains DTA-specific because its existing elite evidence shares the same two
source files. The other seven pinned sources use `extract_ini_armament_roles.py`, which binds
each exact weapon/projectile link to explicit targeting and per-slot weapon evidence. RA2 missing
defaults and incomplete weapons still abstain there. A source hash is necessary provenance, not
sufficient combat evidence.

    python tools/reference/extract_ini_projectile_roles.py \
        --ini-dir "<reference>/DTA Developer Edition/INI" --write
"""
from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

from extract_ini_units import read_ini, resolve_inherits, merge_overlay, bool_value  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parents[2]
OUT = ROOT / "docs" / "reference" / "ini_projectile_role_evidence.json"
CORPUS = ROOT / "docs" / "reference" / "ini_corpus.json"

# ⚠ THE ENGINE DEFAULT, DECLARED RATHER THAN DISCOVERED. `BulletTypeClass` initialises `AA` false
# and `AG` true, so a projectile that declares neither is anti-ground. It is recorded in the
# output as an explicit assumption with this basis string, the same way the corpus records
# `engine_profile_applicability: unverified` — a default nobody can see in the data is exactly the
# kind of claim that must travel with its provenance.
DEFAULT_AA = False
DEFAULT_AG = True
DEFAULT_BASIS = "TS BulletTypeClass field defaults (AA=no, AG=yes); declared, not observed"

# The two sources whose corpus rows are byte-pinned. `overlay` follows the game's own precedence
# (Enhance.ini wins), identical to `extract_ini_units.merge_overlay`.
PINNED = {
    "DTA Classic": {"rules": "Rules.ini", "overlay": None, "engine": "ts"},
    "DTA Enhanced": {"rules": "Rules.ini", "overlay": "Enhance.ini", "engine": "ts"},
}


def sha256(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def corpus_provenance(root=ROOT):
    """{source: (rules_sha256, overlay_sha256)} for every source that pins its bytes."""
    seen = {}
    corpus = pathlib.Path(root) / "docs" / "reference" / "ini_corpus.json"
    for line in corpus.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        seen.setdefault(row["source"], []).append(
            (row.get("source_sha256"), row.get("overlay_sha256")))
    out, dropped = {}, []
    for source, values in seen.items():
        # A source is byte-pinned only when EVERY row carries one identical pin. Accepting the
        # first stamped row would let a partial or conflicting corpus masquerade as verified.
        if any(not isinstance(digest, str) or len(digest) != 64
               or any(ch not in "0123456789abcdef" for ch in digest.lower())
               for digest, _overlay in values):
            if any(digest for digest, _overlay in values):
                dropped.append((source, "source pin is partial"))
            continue
        unique = set(values)
        if len(unique) != 1:
            dropped.append((source, "source pins conflict"))
            continue
        out[source] = unique.pop()
    corpus_provenance.dropped = dropped
    return out


def referenced_projectiles(source):
    """Every projectile name the corpus actually cites for this source, both weapon slots."""
    names = set()
    for line in CORPUS.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        if row.get("source") != source:
            continue
        for key in ("w_projectile", "w2_projectile"):
            value = row.get(key)
            if value:
                names.add(str(value))
    return names


def role_of(aa: bool, ag: bool) -> str:
    """The SAME four-way vocabulary `armament_roles` uses — one ruling, two engines.

    A projectile with neither flag reaches no domain at all; that is `special`, not a silent
    ground weapon, so an interceptor cannot quietly become a cannon's reference.
    """
    if aa and ag:
        return "both"
    if aa:
        return "air"
    if ag:
        return "ground"
    return "special"


def target_bool(raw):
    """(value, state) for one projectile Boolean; invalid text is never false."""
    if raw is None:
        return None, "absent"
    value = bool_value(raw)
    if value is None:
        return None, "invalid"
    return value, "declared"


def projectile_roles(ini: dict, wanted: set) -> tuple[dict, list]:
    """{projectile: verdict} over the FLATTENED ini, plus the names the file does not declare."""
    roles, missing = {}, []
    for name in sorted(wanted):
        section = ini.get(name)
        if section is None:
            missing.append(name)
            continue
        declared_aa = section.get("AA")
        declared_ag = section.get("AG")
        aa, aa_state = target_bool(declared_aa)
        ag, ag_state = target_bool(declared_ag)
        if "invalid" in (aa_state, ag_state):
            raise ValueError(f"{name}: invalid AA/AG boolean")
        aa = DEFAULT_AA if aa_state == "absent" else aa
        ag = DEFAULT_AG if ag_state == "absent" else ag
        roles[name] = {
            "role": role_of(aa, ag),
            "aa": aa,
            "ag": ag,
            # Which half is DECLARED and which is the engine default — a reader must be able to
            # tell a measured `ground` from a defaulted one without re-opening Rules.ini.
            "declared": sorted(k for k, v in (("AA", declared_aa), ("AG", declared_ag))
                               if v is not None),
        }
    return roles, missing


def build(ini_dir: pathlib.Path) -> dict:
    pinned = corpus_provenance()
    sources = []
    for label, spec in PINNED.items():
        if label not in pinned:
            raise SystemExit(f"{label}: the corpus pins no source_sha256 — refusing to guess")
        want_rules, want_overlay = pinned[label]
        rules_path = ini_dir / spec["rules"]
        if not rules_path.exists():
            raise SystemExit(f"{label}: {rules_path} not found")
        got_rules = sha256(rules_path)
        # ⛔ FAIL CLOSED ON THE BYTES. A projectile role extracted from a DIFFERENT Rules.ini than
        # the one the damage numbers came from is not evidence about this corpus, it is a
        # coincidence; `dta_projectile_evidence.py` asserts the same contract.
        if got_rules != want_rules:
            raise SystemExit(f"{label}: Rules.ini is {got_rules}, corpus pins {want_rules}")
        ini = resolve_inherits(read_ini(rules_path))
        overlay_digest = None
        if spec["overlay"]:
            overlay_path = ini_dir / spec["overlay"]
            if not overlay_path.exists():
                raise SystemExit(f"{label}: overlay {spec['overlay']} missing")
            overlay_digest = sha256(overlay_path)
            if overlay_digest != want_overlay:
                raise SystemExit(f"{label}: {spec['overlay']} is {overlay_digest}, "
                                 f"corpus pins {want_overlay}")
            ini = merge_overlay(ini, resolve_inherits(read_ini(overlay_path)))
        elif want_overlay:
            raise SystemExit(f"{label}: corpus pins an overlay this spec does not apply")
        wanted = referenced_projectiles(label)
        roles, missing = projectile_roles(ini, wanted)
        sources.append({
            "source": label,
            "engine": spec["engine"],
            "rules_sha256": got_rules,
            "overlay_sha256": overlay_digest,
            "overlay_precedence": "overlay_over_rules" if overlay_digest else "none",
            "referenced": len(wanted),
            "resolved": len(roles),
            # Undeclared projectiles are NAMED, not counted away. A corpus row citing a projectile
            # the rules file never declares is a real finding about the corpus, not noise here.
            "undeclared": missing,
            "projectiles": roles,
        })
    return {
        "schema": 1,
        "scope": ("Projectile AA/AG domain flags for the byte-pinned INI sources. "
                  "No damage, range, cadence or DPS is read, changed or implied."),
        "engine_default": {"AA": DEFAULT_AA, "AG": DEFAULT_AG, "basis": DEFAULT_BASIS},
        "role_vocabulary": ["ground", "air", "both", "special"],
        "sources": sources,
    }


def _verified_sources(doc, root):
    """The evidence sources whose byte pins STILL match the corpus — fail closed per source.

    ⛔ A HASH RECORDED AT WRITE TIME PROVES NOTHING AT READ TIME (Astra, PR #375 blocker 4:
    *"Evidence hashes are recorded but not enforced when consumed; stale projectile/elite evidence
    and pairing artifacts can be accepted."*). Both extractors refuse to run unless the INI they
    read hashes to the pin the corpus carries — and then wrote a JSON that any later process could
    consume months after the corpus moved underneath it. Re-checking here closes that window with
    the two files the repository actually holds, so it works on a machine without the 9.9 GB
    reference folder.

    Per SOURCE, not per document: a mismatch drops that source's evidence and leaves the rest
    usable, which is the same shape as every other abstention in this lane. The dropped sources
    are returned so a caller can report them rather than discover a silent gap.
    """
    pins = corpus_provenance(root)
    kept, dropped = [], []
    for entry in doc["sources"]:
        source = entry.get("source")
        want = pins.get(source)
        got = (entry.get("rules_sha256"), entry.get("overlay_sha256"))
        if want is None:
            dropped.append((source, "the corpus pins no bytes for this source"))
            continue
        if tuple(want) != got:
            dropped.append((source, "corpus pin moved since this evidence was written"))
            continue
        kept.append(entry)
    return kept, dropped


def load(root=ROOT):
    """{(source, projectile): verdict} for `armament_roles.ini_views`; {} when absent."""
    path = pathlib.Path(root) / "docs" / "reference" / "ini_projectile_role_evidence.json"
    if not path.exists():
        return {}
    doc = json.loads(path.read_text(encoding="utf-8"))
    if doc.get("schema") != 1:
        raise ValueError("unsupported INI projectile role evidence")
    verified, load.dropped = _verified_sources(doc, root)
    out = {}
    for entry in verified:
        for name, verdict in entry["projectiles"].items():
            out[(entry["source"], name)] = verdict
            out[(entry["source"], name.lower())] = verdict
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--ini-dir", required=True, type=pathlib.Path,
                    help="the DTA INI directory holding Rules.ini and Enhance.ini")
    ap.add_argument("--write", action="store_true", help="write the evidence file")
    args = ap.parse_args(argv)
    doc = build(args.ini_dir)
    for entry in doc["sources"]:
        counts = {}
        for verdict in entry["projectiles"].values():
            counts[verdict["role"]] = counts.get(verdict["role"], 0) + 1
        print(f"{entry['source']}: {entry['resolved']}/{entry['referenced']} projectiles "
              f"resolved  {counts}"
              + (f"  UNDECLARED {entry['undeclared']}" if entry["undeclared"] else ""))
    if args.write:
        OUT.write_text(json.dumps(doc, indent=1, sort_keys=True) + "\n", encoding="utf-8")
        print(f"wrote {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
