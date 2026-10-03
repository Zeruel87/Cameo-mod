#!/usr/bin/env python3
"""seed_design.py — Balance Pipeline Phase 3 (BALANCE_PIPELINE.md §6).

Seeds the ledger's design.* judgment fields (special, unit_class,
tech_tier) from the LEGACY workbook (docs/design/cameo_armor_system.xlsx)
and writes the discrepancy report docs/balance/discrepancies.md.

Matching:
- CABAL tab carries actor ids (column C) -> resolved, when the exact id
  exists in the ledger (an existing id is ALWAYS kept, never redirected).
  Historical actor-id reuse (LEGACY_ID_QUARANTINE) is withheld first.
  A missing id consults docs/balance/name_map.yaml by norm(actor id)
  (explicit actor-ID aliases only; the mapped target must exist). No
  automatic normalized actor search — a missing key or a missing target
  stays unresolved; the report says "missing actor ID / unresolved
  identity", never that a unit is proven dead from an absent id.
- Legacy type tabs (Infantry/Tanks/Vehicles/Aircraft/Defenses) carry
  display names only -> normalized-name match against ledger display
  names; ambiguous or unmatched rows are REPORTED, never guessed.
- docs/balance/name_map.yaml (committed, hand-curated) overrides, with
  BOTH display-name keys and actor-ID keys:
      legacy display name or actor id: target_actor_id
  a "-" value ignores type-tab DISPLAY-NAME rows only; on the CABAL
  actor-ID path "-" has no ignore authority — such a row stays unresolved.
Respects the ~$ Excel lock (queues per the balance law).

Quarantined target ids (LEGACY_ID_QUARANTINE) are authoritative for ALL
resolved source rows — the original CABAL row, a type-tab display-name
match, or an explicit alias all get withheld; only the section-derived
fallback stays separate.

Labels are precise: "matched legacy rows" counts rows collected into
target groups (before conflict withholding); "applied design fields"
counts real missing→value transitions; the design import diagnostics
table mixes kept/withheld/fallback records and is NOT an apply count;
direct/mapped are raw resolution counts, not import counts.

Import order (two-phase collection/preflight, deliberately small):
1. COLLECT every resolvable row into groups keyed by TARGET ACTOR,
   across the CABAL tab and ALL type tabs (not per normalized name).
2. PREFLIGHT: if any non-null imported judgment (special, unit_class,
   tech_tier, category, subtype) conflicts inside a target's group, ALL
   workbook-derived changes for that target are withheld and the source
   cells/names/values are reported. Identical duplicates and
   complementary nonconflicting partial rows stay accepted; 0 is a
   populated value and None is missing; costs never conflict (they are
   comparison-only). Existing ledger values do NOT erase a source
   conflict — it is reported even when no field would have been filled.
3. APPLY: fill-only per field (existing values win; conflicts were
   already withheld whole-target).

--dry-run runs the identical collect/preflight/apply logic in memory on
a throwaway copy of the ledger docs, prints every proposal/discrepancy
to stdout, and writes NOTHING — no ledger, no workbook, no
discrepancies.md. Dry-run output never claims anything was seeded.
"""
from __future__ import annotations

import json
import pathlib
import re
import sys

import openpyxl

ROOT = pathlib.Path(__file__).resolve().parents[2]
LEDGER = ROOT / "docs/balance"
LEGACY = ROOT / "docs/design/cameo_armor_system.xlsx"
NAME_MAP = LEDGER / "name_map.yaml"
REPORT = LEDGER / "discrepancies.md"

TYPE_TABS = {"Infantry": ("TD", ), "Tanks": (), "Vehicles": (), "Aircraft": (), "Defenses": ()}
FALLBACK_CATEGORY = {"infantry": "Infantry", "vehicles": "Vehicles", "aircraft": "Aircraft",
                     "naval": "Naval", "defenses": "Defenses"}
# legacy type-tab columns (recon 2026-07-18): B name, D hp, S cost,
# H weapon class, K special, L unit class, M tech tier
# CABAL tab: A mod, B name, C actor, ... K special, L unit class, M tier, R cost

# Historical CABAL actor-id reuse, quarantined from automatic LEGACY seeding.
#
# Provenance — commit 833f7123e9978918730bbcf8ce716dfed5d9dc2d (2026-07-15,
# "Rename Legion to Widow (replace old Widow)"): the OLD cabal_widow definition
# (^HighTechTankTemplate, HP 80000, Cost 3000, weapon CabalWidowPlasma) was
# removed and the `cabal_widow` id was replaced/reused for the former
# cabal_legion unit (renamed Widow, main-battle-tank body, Cost 3500);
# `cabal_legion` itself ceased to exist under that id. This is an identity
# replacement, not an alias.
#
# The retained CABAL identity rows in the LEGACY workbook still describe the
# older lineup (the workbook has later updates, so this is NOT a claim about
# the whole workbook): its CABAL row keyed `cabal_widow` (B29/C29) describes
# the OLD HighTechTank definition, while today's `cabal_widow` actor is the
# former Legion. Seeding that row's special/unit_class/tier into the
# replacement actor would import another definition's judgment values, so the
# row is WITHHELD from automatic seeding until a maintainer re-judges it.
# Existing ledger values are fill-only and stay untouched — today's tier1 on
# cabal_widow is NOT proven wrongly imported and is NOT repaired here. The
# unresolved `cabal_legion` row (missing actor ID) stays unresolved: reported,
# never auto-mapped, never substituted.
#
# Deliberately a tiny constant keyed by (sheet, actor id lowercased/stripped).
LEGACY_ID_QUARANTINE = {
    ("CABAL", "cabal_widow"): (
        "commit 833f7123e9978918730bbcf8ce716dfed5d9dc2d removed and replaced "
        "the old cabal_widow definition (HighTechTank/80kHP/3000-cost/"
        "CabalWidowPlasma) under the id of the former cabal_legion; this "
        "retained CABAL identity row still describes the older lineup, not "
        "today's cabal_widow actor"
    ),
}

JUDGMENT_FIELDS = ("special", "unit_class", "tech_tier")

# Blocked TARGET ids derived from LEGACY_ID_QUARANTINE (same provenance, no
# second registry): a historically replaced/reused id must not be filled by
# ANY resolved source row — the original CABAL row, a type-tab display-name
# match, or an explicit alias — independent of whether the original CABAL row
# still exists. Section-derived fallback is not affected.
QUARANTINED_TARGETS = {
    orig_id: reason for (_sheet, orig_id), reason in LEGACY_ID_QUARANTINE.items()
}


def norm(s: str) -> str:
    s = re.sub(r"\(.*?\)", "", str(s)).lower()
    return re.sub(r"[^a-z0-9]", "", s)


def load_name_map(path=None) -> dict[str, str]:
    base = pathlib.Path(path) if path is not None else NAME_MAP
    out = {}
    if base.exists():
        for line in base.read_text(encoding="utf-8").splitlines():
            s = line.strip()
            if not s or s.startswith("#"):
                continue
            k, _, v = s.partition(":")
            out[norm(k)] = v.strip()
    return out


def ledger_docs(ledger_dir=None) -> dict[str, dict]:
    base = pathlib.Path(ledger_dir) if ledger_dir is not None else LEDGER
    out = {}
    for p in sorted(base.glob("*.json")):
        doc = json.loads(p.read_text(encoding="utf-8"))
        if "sections" in doc:  # skip registry files (class_anchors.json …)
            out[p.stem] = doc
    return out


def all_units(docs) -> dict[str, tuple[str, str, dict]]:
    """actor -> (ledger, section, unit)"""
    out = {}
    for name, doc in docs.items():
        for section, sec in doc["sections"].items():
            for actor, u in sec.items():
                out[actor] = (name, section, u)
    return out


def fnum(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def fmt_val(v):
    return "<missing>" if v is None else v


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    unknown = [a for a in args if a != "--dry-run"]
    if unknown:
        print(f"unknown argument(s): {' '.join(unknown)}; supported: --dry-run")
        return 2
    return run(dry_run="--dry-run" in args)


def run(dry_run: bool = False, ledger_dir=None, legacy_path=None,
        name_map_path=None, report_path=None) -> int:
    """Seed design fields from the legacy workbook.

    Default paths are the module constants (real repository). Tests and
    inspections MUST pass explicit temp paths — never the defaults.
    dry_run=True mutates nothing on disk: the fill-only logic runs on the
    in-memory docs (already private copies from json.loads) and every
    proposed change is printed instead of written.
    """
    ledger_dir = pathlib.Path(ledger_dir) if ledger_dir is not None else LEDGER
    legacy_path = pathlib.Path(legacy_path) if legacy_path is not None else LEGACY
    name_map_path = pathlib.Path(name_map_path) if name_map_path is not None else NAME_MAP
    report_path = pathlib.Path(report_path) if report_path is not None else REPORT

    if (legacy_path.parent / ("~$" + legacy_path.name)).exists():
        print("legacy workbook is OPEN in Excel (~$ lock) — queueing per the balance law; rerun later.")
        return 2
    docs = ledger_docs(ledger_dir)
    units = all_units(docs)
    by_norm_name: dict[str, list[str]] = {}
    for actor, (_, _, u) in units.items():
        if u.get("name"):
            by_norm_name.setdefault(norm(u["name"]), []).append(actor)
    nmap = load_name_map(name_map_path)

    wb = openpyxl.load_workbook(legacy_path, data_only=False)
    try:
        direct, mapped = 0, 0
        matched_rows, applied = 0, 0
        unmatched, ambiguous, unresolved = [], [], []
        withheld, alias_lines, conflicts, proposals, mismatches = [], [], [], [], []
        conflict_targets: set[str] = set()
        groups: dict[str, list[dict]] = {}

        def design_of(actor):
            entry = units.get(actor)
            return (entry[2].get("design") or {}) if entry else {}

        def record(src, key, existing, val, disposition):
            proposals.append((src, key, fmt_val(existing), val, disposition))

        # --- phase 1: COLLECT resolved rows, grouped by target actor ---
        def collect(target, orig, special, unit_class, tier, legacy_cost,
                    sheet, row, rowname, alias=False, category=None, subtype=None):
            """Collect one resolved row; returns False if the TARGET id is
            quarantined (withheld for every source path, no group entry)."""
            nonlocal matched_rows
            u = units[target][2]
            vals = {"special": fnum(special), "unit_class": fnum(unit_class),
                    "tech_tier": fnum(tier), "category": category, "subtype": subtype}
            if alias:
                src = (f"{sheet} row {row}: name `{rowname}`, actor `{orig}` "
                       f"-> target `{target}` (actor-ID alias)")
            else:
                src = f"{sheet} row {row}: name `{rowname}`, actor `{orig or target}`"
            # quarantined target ids are authoritative for ALL resolved rows
            blocked_reason = QUARANTINED_TARGETS.get(target.lower())
            if blocked_reason is not None:
                d = design_of(target)
                for field in ("special", "unit_class", "tech_tier"):
                    val = vals[field]
                    if val is not None:
                        record(src, field, d.get(field), val,
                               "WITHHELD (historical actor-id reuse — see withheld section)")
                withheld.append(f"{src} — special/unit_class/tier withheld from automatic "
                                f"seeding (quarantined target id): {blocked_reason}")
                return False
            groups.setdefault(target, []).append(
                {"src": src, "vals": vals, "sheet": sheet, "row": row,
                 "name": rowname, "cost": legacy_cost})
            matched_rows += 1
            cost = fnum((u.get("cost") or {}).get("v"))
            lcost = fnum(legacy_cost)
            if cost is not None and lcost is not None and abs(cost - lcost) > 0.5:
                mismatches.append(f"`{target}`: yaml cost {cost:.0f} vs legacy sheet {lcost:.0f} ({sheet})")
            return True

        # --- CABAL tab: direct actor ids, then explicit actor-ID aliases ---
        ws = wb["CABAL"]
        for r in range(2, ws.max_row + 1):
            actor = ws.cell(row=r, column=3).value
            if not actor:
                continue
            actor_id = str(actor).strip()
            rowname = ws.cell(row=r, column=2).value
            # 1. quarantine is authoritative and comes first
            quarantine = LEGACY_ID_QUARANTINE.get(("CABAL", actor_id.lower()))
            if quarantine is not None:
                src = f"CABAL row {r}: name `{rowname}`, actor `{actor_id}`"
                d = design_of(actor_id)
                for col, key in ((11, "special"), (12, "unit_class"), (13, "tech_tier")):
                    val = fnum(ws.cell(row=r, column=col).value)
                    if val is None:
                        continue
                    record(src, key, d.get(key), val,
                           "WITHHELD (historical actor-id reuse — see withheld section)")
                withheld.append(f"CABAL row {r} (C{r}=`{actor_id}`, B{r}=`{rowname}`) — "
                                f"special/unit_class/tier withheld from automatic seeding: "
                                f"{quarantine}")
                continue
            direct += 1
            # 2. an existing original id is ALWAYS kept — never redirected
            if actor_id in units:
                collect(actor_id, actor_id, ws.cell(row=r, column=11).value,
                        ws.cell(row=r, column=12).value, ws.cell(row=r, column=13).value,
                        ws.cell(row=r, column=18).value, "CABAL", r, rowname)
                continue
            # 3. only when the id is absent: explicit actor-ID alias from name_map
            alias_target = nmap.get(norm(actor_id))
            if alias_target and alias_target != "-" and alias_target in units:
                alias_lines.append(f"CABAL row {r} (C{r}=`{actor_id}`) — actor-ID alias "
                                   f"-> `{alias_target}`")
                collect(alias_target, actor_id, ws.cell(row=r, column=11).value,
                        ws.cell(row=r, column=12).value, ws.cell(row=r, column=13).value,
                        ws.cell(row=r, column=18).value, "CABAL", r, rowname,
                        alias=True)
                continue
            unresolved.append(f"CABAL: `{rowname}` -> `{actor_id}` "
                              f"(missing actor ID — unresolved identity)")

        # --- legacy type tabs: name matching (scan starts at row 2 so the
        # first-group subtype header in B2 is honored by the same heuristic) ---
        for tab in ("Infantry", "Tanks", "Vehicles", "Aircraft", "Defenses"):
            if tab not in wb.sheetnames:
                continue
            ws = wb[tab]
            subtype = "Unclassified"
            for r in range(2, ws.max_row + 1):
                rowname = ws.cell(row=r, column=2).value
                hp = ws.cell(row=r, column=4).value
                if rowname and fnum(hp) is None:
                    subtype = str(rowname).strip()
                    continue
                if not rowname or fnum(hp) is None:
                    continue
                key = norm(rowname)
                if key in nmap:
                    target = nmap[key]
                    if target == "-":
                        continue
                    if target in units:
                        collect(target, None, ws.cell(row=r, column=11).value,
                                ws.cell(row=r, column=12).value, ws.cell(row=r, column=13).value,
                                ws.cell(row=r, column=19).value, tab, r, rowname,
                                category=tab, subtype=subtype)
                    else:
                        unresolved.append(f"{tab}: `{rowname}` -> `{target}` "
                                          f"(missing actor ID — unresolved identity)")
                    mapped += 1
                    continue
                cands = by_norm_name.get(key, [])
                if len(cands) == 1:
                    collect(cands[0], None, ws.cell(row=r, column=11).value,
                            ws.cell(row=r, column=12).value, ws.cell(row=r, column=13).value,
                            ws.cell(row=r, column=19).value, tab, r, rowname,
                            category=tab, subtype=subtype)
                    mapped += 1
                elif len(cands) > 1:
                    ambiguous.append(f"{tab}: `{rowname}` -> {cands}")
                else:
                    unmatched.append(f"{tab}: `{rowname}`")

        # --- phase 2: PREFLIGHT target-level conflicts ---
        for target, rows in groups.items():
            for field in ("special", "unit_class", "tech_tier", "category", "subtype"):
                by_val: dict = {}
                for rowrec in rows:
                    v = rowrec["vals"][field]
                    if v is None:
                        continue
                    by_val.setdefault(v, []).append(rowrec)
                if len(by_val) > 1:
                    conflict_targets.add(target)
                    detail = " vs ".join(
                        f"{vrows[0]['sheet']} row {vrows[0]['row']} `{vrows[0]['name']}`={v}"
                        for v, vrows in by_val.items())
                    conflicts.append(f"`{target}` design.{field}: {detail}")

        # --- phase 3: APPLY fill-only per field (conflicts already withheld) ---
        for target, rows in groups.items():
            if target in conflict_targets:
                continue
            _, _, u = units[target]
            for rowrec in rows:
                d = u.setdefault("design", {})
                for field, kind in (("special", "legacy sheet"), ("unit_class", "legacy sheet"),
                                    ("tech_tier", "legacy sheet"), ("category", "row context"),
                                    ("subtype", "row context")):
                    val = rowrec["vals"][field]
                    if val is None:
                        continue
                    existing = d.get(field)
                    if existing is None:
                        if dry_run:
                            record(rowrec["src"], field, None, val, f"propose fill ({kind})")
                        d[field] = val
                        applied += 1  # a real missing->value transition
                    elif dry_run:
                        record(rowrec["src"], field, existing, val, "existing value kept (fill-only)")

        for actor, (_, section, u) in units.items():
            category = FALLBACK_CATEGORY.get(section)
            if category:
                d = u.setdefault("design", {})
                for key, val in (("category", category), ("subtype", "Unclassified")):
                    if d.get(key) is None:
                        if dry_run:
                            record(f"ledger section `{section}`: actor `{actor}`", key, None, val,
                                   "propose fallback (section-derived — NOT a legacy numeric import)")
                        d[key] = val
                        applied += 1  # a real missing->value transition (section-derived)
    finally:
        wb.close()

    # ledger units whose design JUDGMENTS were never populated (special,
    # unit_class, tech_tier all missing — 0 counts as populated; category/
    # subtype fallback metadata does not hide them)
    no_judgments = [a for a, (_, sec, u) in sorted(units.items())
                    if sec in ("infantry", "vehicles", "aircraft", "naval", "defenses")
                    and all((u.get("design") or {}).get(k) is None for k in JUDGMENT_FIELDS)]

    fill_action = "would fill" if dry_run else "applied"
    lines = ["# Balance ledger — legacy-sheet discrepancy report",
             "", f"_generated by seed_design.py; matched {matched_rows} legacy rows "
             f"across {len(groups)} unique targets; {fill_action} {applied} design fields_"
             + (" — DRY-RUN: nothing seeded, nothing written" if dry_run else ""),
             "",
             "## Unresolved legacy rows (missing actor ID or unmatched display name — extend name_map.yaml)", ""]
    lines += [f"- {x}" for x in unmatched + unresolved] or ["- none"]
    lines += ["", "## Ambiguous name matches (resolve in name_map.yaml)", ""]
    lines += [f"- {x}" for x in ambiguous] or ["- none"]
    lines += ["", f"## CABAL actor-ID aliases resolved via name_map ({len(alias_lines)})", ""]
    lines += [f"- {x}" for x in alias_lines] or ["- none"]
    lines += ["", "## Withheld legacy rows (historical actor-id reuse — needs a maintainer decision, NOT auto-seeded)", ""]
    lines += [f"- {x}" for x in withheld] or ["- none"]
    lines += ["", "## Conflicting source rows (ALL workbook-derived values withheld for the target)", ""]
    lines += [f"- {x}" for x in conflicts] or ["- none"]
    lines += ["", "## Cost mismatches (yaml vs legacy sheet — maintainer picks the law)", ""]
    lines += [f"- {x}" for x in mismatches] or ["- none"]
    if dry_run:
        lines += ["", f"## Design import diagnostics ({len(proposals)} records — includes kept/withheld "
                      f"records and section fallback; the record count is NOT an apply count)", ""]
        lines += [f"- {src} — design.{key}: {existing} -> {proposed} [{disposition}]"
                  for src, key, existing, proposed, disposition in proposals]
    lines += ["", f"## Ledger units with no design judgments populated ({len(no_judgments)})", ""]
    lines += [f"- `{a}`" for a in no_judgments[:200]]
    if len(no_judgments) > 200:
        lines.append(f"- … and {len(no_judgments) - 200} more")

    if dry_run:
        print("\n".join(lines))
        print(f"DRY-RUN complete: {len(proposals)} diagnostic records (not an apply count), "
              f"would fill {applied} design fields, "
              f"{len(alias_lines)} alias-resolved, {len(conflict_targets)} conflict targets, "
              f"unmatched {len(unmatched)}, ambiguous {len(ambiguous)}, "
              f"unresolved {len(unresolved)}, withheld {len(withheld)}, "
              f"cost mismatches {len(mismatches)}, no design judgments {len(no_judgments)}; "
              f"NO ledger, workbook or report was written.")
        return 0

    # write ledgers back (design fields only changed)
    for name, doc in docs.items():
        p = ledger_dir / f"{name}.json"
        p.write_text(json.dumps(doc, sort_keys=True, indent=1, ensure_ascii=False) + "\n",
                     encoding="utf-8", newline="\n")

    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    print(f"matched {matched_rows} legacy rows across {len(groups)} unique targets "
          f"(resolution: {direct} by CABAL actor id, {mapped} by display name — "
          f"resolution counts, not import counts); aliases {len(alias_lines)}; "
          f"applied {applied} design fields; "
          f"unmatched {len(unmatched)}, ambiguous {len(ambiguous)}, "
          f"unresolved {len(unresolved)}, conflicts {len(conflict_targets)}, "
          f"withheld {len(withheld)}, cost mismatches {len(mismatches)}, "
          f"no design judgments {len(no_judgments)}")
    try:
        where = report_path.relative_to(ROOT)
    except ValueError:
        where = report_path
    print(f"report -> {where}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
