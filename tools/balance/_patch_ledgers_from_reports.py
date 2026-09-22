#!/usr/bin/env python3
"""Stage explicitly selected class reports in ledgers, never gameplay YAML.

All rows are validated before any output. This is not approval to apply targets;
apply_balance's runtime, provenance and shared-consumer guards still apply.
"""
import argparse
import copy
import json
import pathlib

import apply_balance
import formula
from apply_transaction import Transaction
from proposal_contract import COLUMNS, DAMAGE_COLUMN, parse_damage

ROOT = pathlib.Path(__file__).resolve().parents[2]
LEDGER = ROOT / "docs" / "balance"


def parse_report(path):
    lines = pathlib.Path(path).read_text(encoding="utf-8-sig").splitlines()
    for start, line in enumerate(lines):
        headers = [c.strip() for c in line.split("|")[1:-1]]
        if line.startswith("|") and "actor" in headers:
            break
    else:
        raise ValueError(f"{path}: no proposal table")
    if len(set(headers)) != len(headers) or set(COLUMNS) - set(headers):
        raise ValueError(f"{path}: missing or duplicate proposal columns; regenerate report")
    if start + 1 >= len(lines) or not lines[start + 1].startswith("|---"):
        raise ValueError(f"{path}: missing table separator")
    rows = []
    for line in lines[start + 2:]:
        if not line.startswith("|"):
            break
        cells = [c.strip() for c in line.split("|")[1:-1]]
        if len(cells) != len(headers):
            raise ValueError(f"{path}: malformed proposal row")
        row = dict(zip(headers, cells))
        row["actor"] = row["actor"].strip("`")
        if not row["actor"]:
            raise ValueError(f"{path}: empty actor")
        for key in ("HP", "spd", "rng", "cost", "rl", "burst", "legacy FP%"):
            try:
                row[key] = int(row[key])
            except ValueError as exc:
                raise ValueError(f"{row['actor']}: missing/invalid {key} target") from exc
            if row[key] < 0 or (key in ("HP", "cost", "rl", "burst") and row[key] == 0):
                raise ValueError(f"{row['actor']}: invalid {key} target")
        row["dmg"], row["n_wh"], row["calibration"] = parse_damage(row[DAMAGE_COLUMN])
        calibration = set(row["flags"].split()) & {"anchor", "verifier"}
        if calibration and not row["calibration"]:
            raise ValueError(f"{row['actor']}: calibration rows must display the "
                             "current total, not a target; regenerate the report")
        if row["calibration"]:
            if not calibration:
                raise ValueError(f"{row['actor']}: current-total damage cell is calibration-only")
        elif row["dmg"] % formula.DAMAGE_STEP:
            raise ValueError(f"{row['actor']}: off-grid damage")
        if row["dmg_filter"] not in ("all", "smallarms") or not row["weapon"]:
            raise ValueError(f"{row['actor']}: missing/invalid weapon selection")
        rows.append(row)
    if not rows:
        raise ValueError(f"{path}: empty proposal table")
    return rows


def prepare_ledgers(fresh_docs, rows):
    """Return validated candidates without mutating the caller's documents."""
    docs = copy.deepcopy(fresh_docs)
    actors = {}
    for name, doc in docs.items():
        for section in doc.get("sections", {}).values():
            for actor, unit in section.items():
                if actor in actors:
                    raise ValueError(f"ambiguous ledger actor: {actor}")
                actors[actor] = (name, unit)
    seen, touched = set(), set()
    for row in rows:
        actor = row["actor"]
        if actor in seen:
            raise ValueError(f"duplicate proposal actor: {actor}")
        seen.add(actor)
        if actor not in actors:
            raise ValueError(f"{actor}: not found in any ledger")
        name, unit = actors[actor]
        if set(row["flags"].split()) & {"anchor", "verifier"}:
            continue  # Calibration rows are displayed, never proposed edits.
        if row["legacy FP%"] != 100 or "resolved_firepower_modifiers" in unit:
            raise ValueError(f"{actor}: retained firepower requires an explicit migration")
        if (unit.get("firepower_multiplier") or {}).get("v", 1) != 1:
            raise ValueError(f"{actor}: live firepower differs from proposal")
        for column, key in (("HP", "hp"), ("spd", "speed"), ("cost", "cost")):
            if not isinstance(unit.get(key), dict) or "v" not in unit[key]:
                raise ValueError(f"{actor}: no writable {key} stat")
            unit[key]["v"] = row[column]
        arms = [a for a in unit.get("armaments", []) if a.get("pricing")
                and a.get("slot") in ("Armament", "Armament@PRIMARY")]
        if len(arms) != 1 or arms[0].get("weapon") != row["weapon"]:
            raise ValueError(f"{actor}: missing, ambiguous or stale primary weapon")
        arm = arms[0]
        if not formula.condition_holds_by_default(arm.get("requires")):
            raise ValueError(f"{actor}: primary weapon not active by default")
        mains = formula.main_spread_warheads(arm.get("damage_warheads", []))
        if any(not (w.get("tag") or "") for w in mains):
            raise ValueError(f"{actor}: main warhead without tag; regenerate the ledger")
        if row["dmg_filter"] == "smallarms" and any(
                not w.get("tag", "").lower().startswith("smallarms") for w in mains):
            raise ValueError(f"{actor}: partial damage-family proposals are unsupported")
        if len(mains) != row["n_wh"]:
            raise ValueError(f"{actor}: stale main-warhead count")
        targets = formula.distribute_damage(row["dmg"] * row["n_wh"],
                                            arm.get("damage_warheads", []))
        for warhead in arm.get("damage_warheads", []):
            if warhead.get("tag") in targets:
                warhead["damage"] = targets[warhead["tag"]]
        arm.update(range=row["rng"], reloaddelay=row["rl"], burst=row["burst"])
        touched.add(name)
    return {name: docs[name] for name in sorted(touched)}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("reports", nargs="+", type=pathlib.Path)
    parser.add_argument("--write", action="store_true", help="stage ledger candidates, not YAML")
    args = parser.parse_args(argv)
    rows = [row for path in args.reports for row in parse_report(path)]
    originals = {path.stem: path.read_bytes() for path in LEDGER.glob("*.json")}
    fresh = apply_balance.fresh_ledgers(None)
    candidates = prepare_ledgers(fresh, rows)
    for name in candidates:
        if name not in originals or json.loads(originals[name].decode("utf-8-sig")) != fresh[name]:
            raise ValueError(f"{name}: existing ledger differs from live extraction; preserve or resolve its staged edits first")
    outputs = {name: json.dumps(doc, ensure_ascii=False, indent=1) + "\n"
               for name, doc in candidates.items()}
    if args.write:
        transaction = Transaction({LEDGER / f"{name}.json": originals[name] for name in outputs})
        try:
            transaction.check_unchanged()
            for name, text in outputs.items():
                transaction.write(LEDGER / f"{name}.json", text.encode("utf-8"))
        except BaseException:
            conflicts = transaction.rollback()
            if conflicts:
                print(f"Recovery preserved external changes: {conflicts}")
            raise
    print(f"{'staged' if args.write else 'DRY RUN:'} {len(outputs)} ledger(s); no YAML written")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except ValueError as error:
        raise SystemExit(f"REFUSED: {error}")
