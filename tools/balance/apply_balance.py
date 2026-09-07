#!/usr/bin/env python3
"""apply_balance.py — Balance Pipeline Phase 4b (BALANCE_PIPELINE.md §4).

Ledger (docs/balance/*.json) -> yaml, through the provenance anchors.

GATED: without --confirm this is a dry run that prints the diff and
touches nothing. The balance law stands: this command runs on explicit
maintainer order only, and a boot gate + audits follow every real run.

What it writes (prototype scope):
- unit stats whose src is "file#Trait.Field" (written in the actor's
  own block) — Cost, HP, Speed, BuildLimit, sight...;
- weapon ReloadDelay/Burst/BurstDelays/Range/MinRange in the weapon's
  defining block when the field is written there;
- warhead Damage values by tag in the weapon's defining block.
Changed stats whose src is "inherited" REFUSE the entire plan (editing a
template affects the whole class — that is Phase 5 knob territory).
Confirmation stages fresh extraction away from proposal ledgers, verifies all
raw roster requests, and publishes only changed derived artifacts after checked
validation. Failures use optimistic byte checks to preserve detected external
edits during rollback. Exclusive file ownership is required; this is not an OS
lock or atomic compare-and-swap against simultaneous writers.

Usage:
    python tools/balance/apply_balance.py [--faction tkm]           # dry run
    python tools/balance/apply_balance.py --faction tkm --confirm   # write
"""
from __future__ import annotations

import argparse
import json
import pathlib
import re
import subprocess
import sys
import tempfile

from apply_transaction import ApplyError, Transaction

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools/balance"))
sys.path.insert(0, str(ROOT / "tools/audit"))
import formula  # noqa: E402
from miniyaml import load, load_manifest, Ruleset  # noqa: E402

LEDGER = ROOT / "docs/balance"

UNIT_FIELDS = ("cost", "hp", "speed", "speed_air", "turn_speed", "sight",
               "build_limit", "build_duration", "self_heal_step")

# W17 — `FirepowerMultiplier` is RETIRED as a fine-tuning knob, so the pipeline no
# longer WRITES it. `extract_stats` still reads it (167 actors still carry one and
# they must keep pricing correctly), and conditional upgrade FP traits are untouched
# design — this only closes the write path, so a ledger edit can never quietly
# re-introduce the knob. A ledger/yaml disagreement is REPORTED, never applied:
# the fix is to fold the multiplier into the weapon's Damage on the 100 grid.
RETIRED_UNIT_FIELDS = ("firepower_multiplier",)
WEAPON_FIELDS = {"reloaddelay": "ReloadDelay", "burst": "Burst",
                 "burstdelays": "BurstDelays", "range": "Range",
                 "minrange": "MinRange"}


class YamlEditor:
    """Line-surgical editor for miniyaml blocks; one instance per file."""

    def __init__(self, path: pathlib.Path):
        self.path = path
        self.original = path.read_bytes()
        self.bom = self.original.startswith(b"\xef\xbb\xbf")
        text = self.original.decode("utf-8-sig")
        self.newline = "\r\n" if "\r\n" in text else "\n"
        self.lines = text.replace("\r\n", "\n").split("\n")
        self.nodes = load(path)
        self.dirty = False

    def validate_target(self, block, *keys):
        nodes = self.nodes
        for key in (block, *keys):
            matches = [node for node in nodes if node.key == key]
            if len(matches) > 1:
                raise ApplyError(f"ambiguous duplicate `{key}` in {self.path}")
            nodes = matches[0].children if matches else []

    def content(self) -> bytes:
        return (b"\xef\xbb\xbf" if self.bom else b"") + self.newline.join(self.lines).encode("utf-8")

    def replace_value(self, index, match, value):
        # Keep inline comments and spacing; only the scalar belongs to this edit.
        raw = match.group(2)
        comment = re.search(r"\s*(?<!\\)#.*$", raw)
        suffix = raw[comment.start():] if comment else ""
        old = raw[:comment.start()].strip() if comment else raw.strip()
        if old == str(value):
            return "unchanged"
        self.lines[index] = match.group(1) + str(value) + suffix
        self.dirty = True
        return f"{old} -> {value}"

    def _block(self, key: str) -> tuple[int, int] | None:
        start = None
        for i, line in enumerate(self.lines):
            if start is None:
                if line.split(":")[0].strip() == key and line and \
                        (line[0].isalnum() or line[0] in "^_"):
                    start = i
            else:
                if line and (line[0].isalnum() or line[0] in "^_") and ":" in line:
                    return start, i
        return (start, len(self.lines)) if start is not None else None

    def set_field(self, block_key: str, trait: str, field: str, value) -> str:
        self.validate_target(block_key, trait, field)
        span = self._block(block_key)
        if span is None:
            return f"block `{block_key}` not found"
        s, e = span
        ti = None
        for i in range(s + 1, e):
            l = self.lines[i]
            if l.startswith("\t") and not l.startswith("\t\t") and \
                    l.strip().split(":")[0] == trait:
                ti = i
            elif ti is not None and l.startswith("\t") and not l.startswith("\t\t"):
                break
            elif ti is not None and l.startswith("\t\t"):
                m = re.match(rf"^(\t\t{re.escape(field)}:\s*)(.*)$", l)
                if m:
                    return self.replace_value(i, m, value)
        # W17 removed the one branch that INSERTED a missing trait block: it existed
        # solely to create a `FirepowerMultiplier` on an actor that had none, i.e. to
        # mint the retired fine-tuning knob. Every other UNIT_FIELD is an edit to a
        # line that already exists, so this path is now uniformly "not written".
        return f"`{trait}.{field}` not written locally"

    def set_weapon_field(self, weapon: str, field: str, value) -> str:
        """Top-level weapon field (single-tab indent). Inserts if missing."""
        self.validate_target(weapon, field)
        span = self._block(weapon)
        if span is None:
            return f"weapon `{weapon}` not found"
        s, e = span
        for i in range(s + 1, e):
            m = re.match(rf"^(\t{re.escape(field)}:\s*)(.*)$", self.lines[i])
            if m:
                return self.replace_value(i, m, value)
        # Field is not defined locally: insert right after the weapon header
        self.lines.insert(s + 1, f"\t{field}: {value}")
        self.dirty = True
        return f"inserted {field} {value}"

    def set_warhead_damage(self, weapon: str, tag: str, value) -> str:
        self.validate_target(weapon, f"Warhead@{tag}", "Damage")
        span = self._block(weapon)
        if span is None:
            return f"weapon `{weapon}` not found"
        s, e = span
        wi = None
        for i in range(s + 1, e):
            l = self.lines[i]
            if re.match(rf"^\tWarhead@{re.escape(tag)}:", l):
                wi = i
            elif wi is not None and l.startswith("\t") and not l.startswith("\t\t"):
                break
            elif wi is not None:
                m = re.match(r"^(\t\tDamage:\s*)(.*)$", l)
                if m:
                    return self.replace_value(i, m, value)
        return f"warhead `{tag}` Damage not found"

    def save(self):
        if self.dirty:
            self.path.write_bytes(self.content())


def fresh_ledgers(only):
    """Fresh in-memory extraction — write-back only writes values whose
    ledger entry differs from the RESOLVED game value, so shadowed or
    order-sensitive definitions (resolved != defining line) are never
    auto-edited; they are reported instead."""
    sys.path.insert(0, str(ROOT / "tools/balance"))
    sys.path.insert(0, str(ROOT / "tools/audit"))
    import extract_stats
    from cameo_model import Model
    return extract_stats.build_ledgers(Model(), only)


def _main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--faction", help="ledger-name substring filter")
    ap.add_argument("--confirm", action="store_true", help="actually write yaml")
    args = ap.parse_args()

    # Compare the entire raw roster after applying, including unchanged consumers
    # of a shared weapon and unselected factions. Never erase their proposals.
    manifest = load_manifest(ROOT)
    source_bytes = {path.resolve(): path.read_bytes() for path in
                    [*manifest.sources, *manifest.rules, *manifest.weapons]}
    ledger_bytes = {path: path.read_bytes() for path in LEDGER.glob("*.json")}
    fresh = fresh_ledgers(None)
    desired = {}

    def resolved_unit(ledger_name, section, actor):
        return ((fresh.get(ledger_name) or {}).get("sections", {})
                .get(section, {}).get(actor))

    editors: dict[pathlib.Path, YamlEditor] = {}
    planned_targets = {}

    def already_planned(target, value):
        if target not in planned_targets:
            planned_targets[target] = str(value)
            return False
        if planned_targets[target] != str(value):
            raise ApplyError(f"conflicting values for {target}")
        return True

    def editor(relfile: str) -> YamlEditor:
        p = (ROOT / relfile).resolve()
        if not p.is_relative_to((ROOT / "mods/cameo").resolve()) or p.suffix != ".yaml":
            raise ApplyError(f"provenance is not Cameo YAML: {relfile}")
        if p not in editors:
            editors[p] = YamlEditor(p)
        return editors[p]

    changed, skipped_inherited, problems = 0, 0, []
    changed_actors, changed_weapons = set(), set()
    for jf in sorted(LEDGER.glob("*.json")):
        if jf.name == "class_anchors.json":
            continue
        doc = json.loads(ledger_bytes[jf].decode("utf-8-sig"))
        if not isinstance(doc, dict) or "ledger" not in doc or "sections" not in doc:
            continue  # class metadata and reference aggregates are not actor ledgers
        if doc["ledger"] not in fresh:
            problems.append(f"{jf.name}: no current extracted ledger")
            continue
        desired[doc["ledger"]] = doc
        if args.faction and args.faction not in doc["ledger"]:
            if doc != fresh[doc["ledger"]]:
                problems.append(f"{jf.name}: unselected ledger has pending changes; preserve them and apply separately")
            continue
        for path in changed_paths(fresh[doc["ledger"]], doc):
            if not writable_path(path):
                problems.append(f"{jf.name}: unsupported ledger edit at {'/'.join(map(str, path))}")
        for section, sec in doc["sections"].items():
            for actor, u in sec.items():
                ru = resolved_unit(doc["ledger"], section, actor)
                if ru is None:
                    problems.append(f"{actor}: no current resolved actor in this ledger section")
                    continue
                for field in RETIRED_UNIT_FIELDS:
                    slot, rslot = u.get(field), (ru.get(field) or {})
                    if not isinstance(slot, dict):
                        continue
                    if str(slot.get("v")) == str(rslot.get("v")):
                        continue
                    problems.append(
                        f"{actor}.{field}: RETIRED KNOB (W17) — ledger asks for "
                        f"{slot.get('v')}, yaml has {rslot.get('v')}. NOT applied. "
                        f"Fold the multiplier into the weapon's Damage on the "
                        f"{formula.DAMAGE_STEP} grid and delete the trait.")
                for field in UNIT_FIELDS:
                    slot = u.get(field)
                    if not isinstance(slot, dict):
                        continue
                    rslot = ru.get(field) or {}
                    if str(slot.get("v")) == str(rslot.get("v")):
                        continue  # ledger == resolved game value: nothing to do
                    src = slot.get("src", "")
                    if src == "inherited":
                        skipped_inherited += 1
                        problems.append(f"{actor}.{field}: inherited edit is unsupported")
                        continue
                    if "#" not in src or src != rslot.get("src"):
                        problems.append(f"{actor}.{field}: missing or stale provenance")
                        continue
                    if not scalar_value(slot.get("v"), field):
                        problems.append(f"{actor}.{field}: unsupported scalar value")
                        continue
                    relfile, anchor = src.split("#", 1)
                    trait, _, tfield = anchor.partition(".")
                    if already_planned((relfile, actor, trait, tfield), slot["v"]):
                        continue
                    # Every remaining UNIT_FIELD is written in the unit the ledger
                    # stores it in. The one that was not — firepower_multiplier,
                    # a float the engine writes as an integer percentage — is
                    # retired (W17) and handled above.
                    res = editor(relfile).set_field(actor, trait, tfield, slot["v"])
                    if res == "unchanged":
                        problems.append(f"{actor}.{field}: SHADOWED — resolved "
                                        f"{rslot.get('v')} != defining line {slot['v']} "
                                        f"(duplicate definition? fix by hand)")
                        continue
                    if "->" in res:
                        print(f"  {actor}.{field} [{relfile}]: {res}")
                        changed += 1
                        changed_actors.add(actor)
                    else:
                        problems.append(f"{actor}.{field}: {res}")
                rarms = {a.get("slot"): a for a in ru.get("armaments", [])}
                for arm in u.get("armaments", []):
                    wfile, wname = arm.get("defined_in"), arm.get("weapon")
                    rarm = rarms.get(arm.get("slot")) or {}
                    if not wfile or not wname:
                        if arm != rarm:
                            problems.append(f"{actor}: changed armament has no writable provenance")
                        continue
                    if wname != rarm.get("weapon") or wfile != rarm.get("defined_in"):
                        problems.append(f"{actor}/{wname}: missing or stale armament provenance")
                        continue
                    if arm != rarm:
                        cadence_error = weapon_cadence_error(arm)
                        if cadence_error:
                            problems.append(f"{actor}/{wname}: {cadence_error}")
                            continue
                    for lkey, ykey in WEAPON_FIELDS.items():
                        if lkey not in arm:
                            continue
                        if str(arm.get(lkey)) == str(rarm.get(lkey)):
                            continue
                        if not scalar_value(arm[lkey], lkey):
                            problems.append(f"{actor}/{wname}.{ykey}: unsupported scalar value")
                            continue
                        if already_planned((wfile, wname, ykey), arm[lkey]):
                            continue
                        res = editor(wfile).set_weapon_field(wname, ykey, arm[lkey])
                        if res == "unchanged":
                            problems.append(f"{actor}/{wname}.{ykey}: SHADOWED "
                                            f"(resolved {rarm.get(lkey)} != defining line)")
                            continue
                        if "->" in res or res.startswith("inserted "):
                            print(f"  {actor}/{wname}.{ykey} [{wfile}]: {res}")
                            changed += 1
                            changed_weapons.add(wname)
                        else:
                            problems.append(f"{actor}/{wname}.{ykey}: {res}")
                    rwh = {w.get("tag"): w for w in rarm.get("damage_warheads", [])}
                    for w in arm.get("damage_warheads", []):
                        if str(w.get("damage")) == str((rwh.get(w["tag"]) or {}).get("damage")):
                            continue
                        if not scalar_value(w.get("damage"), "damage"):
                            problems.append(f"{actor}/{wname}/{w['tag']}: unsupported scalar value")
                            continue
                        if already_planned((wfile, wname, w["tag"], "Damage"), w["damage"]):
                            continue
                        res = editor(wfile).set_warhead_damage(wname, w["tag"], w["damage"])
                        if res == "unchanged":
                            problems.append(f"{actor}/{wname} Warhead@{w['tag']}: SHADOWED")
                            continue
                        if "->" in res:
                            print(f"  {actor}/{wname} Warhead@{w['tag']}.Damage [{wfile}]: {res}")
                            changed += 1
                            changed_weapons.add(wname)
                        else:
                            problems.append(f"{actor}/{wname} Warhead@{w['tag']}: {res}")

    if not any(not args.faction or args.faction in name for name in desired):
        problems.append("no actor ledger matches the requested faction")
    for missing in sorted(fresh.keys() - desired.keys()):
        problems.append(f"{missing}: extracted ledger is missing from disk; refresh the baseline first")
    if changed:
        problems.extend(shared_constraints(desired, changed_weapons))
        problems.extend(reference_problems(desired, changed_actors, changed_weapons))
    for p in problems:
        print(f"  WARN {p}")
    if problems:
        print(f"REFUSED: {len(problems)} problem(s); no YAML or ledger files written.")
        return 1
    if args.confirm:
        if not changed:
            print("NO CHANGES: no YAML or ledger files written.")
            return 0
        if not apply_checked(editors, ledger_bytes, desired, source_bytes):
            return 1
        print(f"APPLIED AND VERIFIED: {changed} planned values written.")
        print("Re-run the full audit suite (tools/audit/run_all.sh or tools/audit/run_all.py) "
              "and the boot gate before committing.")
    else:
        print(f"DRY RUN: {changed} values would change "
              f"({skipped_inherited} inherited stats skipped). "
              f"Re-run with --confirm on maintainer order.")
    return 0


def shared_constraints(desired, changed_weapons):
    """Unchanged rows are constraints too, not permission to change their weapon."""
    wanted, problems = {}, []
    for doc in desired.values():
        for units in doc["sections"].values():
            for actor, unit in units.items():
                for arm in unit.get("armaments", []):
                    weapon = arm.get("weapon")
                    if weapon not in changed_weapons:
                        continue
                    fields = {key: str(arm.get(key)) for key in WEAPON_FIELDS}
                    fields.update({"Warhead@" + wh["tag"]: str(wh.get("damage"))
                                   for wh in arm.get("damage_warheads", [])})
                    if weapon in wanted and wanted[weapon] != fields:
                        problems.append(f"{actor}/{weapon}: conflicting shared-weapon ledger requests")
                    wanted[weapon] = fields
    return problems


def changed_paths(before, after, path=()):
    """Structural changes are not scalar writes; expose deletions as well as adds."""
    if isinstance(before, dict) and isinstance(after, dict):
        for key in sorted(before.keys() | after.keys()):
            if key not in after:
                yield path + (key, "<removed>")
            elif key not in before:
                yield path + (key,)
            else:
                yield from changed_paths(before[key], after[key], path + (key,))
    elif isinstance(before, list) and isinstance(after, list) and len(before) == len(after):
        for index, (old, new) in enumerate(zip(before, after)):
            yield from changed_paths(old, new, path + (index,))
    elif before != after:
        yield path


def writable_path(path):
    if len(path) < 5 or path[0] != "sections":
        return False
    if len(path) == 5 and path[3] in (*UNIT_FIELDS, *RETIRED_UNIT_FIELDS) and path[4] == "v":
        return True
    if path[3] != "armaments" or not isinstance(path[4], int):
        return False
    return ((len(path) == 6 and path[5] in WEAPON_FIELDS) or
            (len(path) == 8 and path[5] == "damage_warheads" and
             isinstance(path[6], int) and path[7] == "damage"))


def reference_problems(desired, changed_actors, changed_weapons):
    """Block inherited and non-roster consumers, not just other selected rows."""
    rules = Ruleset(ROOT)
    problems = []
    parents = {name.lower() for name in changed_actors}
    for name, node in rules.actors.items():
        if any((c.value or "").lower() in parents for c in node.children_named("Inherits")):
            problems.append(f"{name}: inherits an edited actor; shared actor edits are unsupported")
    if not changed_weapons:
        return problems
    from propose_retained_firepower import reference_index
    allowed = {name.lower(): set() for name in changed_weapons}
    for doc in desired.values():
        for units in doc["sections"].values():
            for actor, unit in units.items():
                for arm in unit.get("armaments", []):
                    name = (arm.get("weapon") or "").lower()
                    if name in allowed:
                        allowed[name].add((actor.lower(), (arm["slot"], "Weapon")))
    for weapon, uses in reference_index(rules, changed_weapons).items():
        for kind, name, path in uses:
            if kind != "actor" or (name.lower(), path) not in allowed[weapon]:
                problems.append(f"{weapon}: unsupported consumer {kind}:{name}/{'/'.join(path)}")
    return problems


def main() -> int:
    try:
        return _main()
    except (OSError, ValueError, KeyError, TypeError) as error:
        print(f"REFUSED: {error}; no successful apply reported.")
        return 1


def int32_value(value) -> bool:
    """Engine integer fields do not accept floats, distances, lists or overflow."""
    if isinstance(value, bool) or not isinstance(value, (int, str)):
        return False
    text = str(value)
    return (len(text) <= 11 and re.fullmatch(r"[+-]?[0-9]+", text) is not None
            and -(2 ** 31) <= int(text) < 2 ** 31)


def scalar_value(value, field) -> bool:
    """Validate writable scalars against engine types, before touching YAML.

    WAngle (turn_speed) uses an Int32 representation. WDist supports raw world
    units or cells/subcells; reject overflow instead of allowing engine wrapping.
    Signed healing damage and the BuildDuration=-1 sentinel remain legitimate.
    """
    if field in ("sight", "range", "minrange"):
        if int32_value(value):
            return True
        if not isinstance(value, str):
            return False
        parts = value.lower().split("c")
        if len(parts) != 2 or not all(int32_value(part) for part in parts):
            return False
        cells, subcells = map(int, parts)
        subcells = -subcells if cells < 0 else subcells
        return (-(2 ** 31) <= cells * 1024 < 2 ** 31
                and -(2 ** 31) <= subcells < 2 ** 31
                and -(2 ** 31) <= cells * 1024 + subcells < 2 ** 31)
    if field == "burstdelays":
        if not isinstance(value, (str, int)) or isinstance(value, bool):
            return False
        return all(int32_value(part.strip()) for part in str(value).split(","))
    if field in (*UNIT_FIELDS, "reloaddelay", "burst", "damage"):
        return int32_value(value)
    return False


def weapon_cadence_error(arm):
    """Mirror armament load constraints and reject empty burst-delay arrays."""
    reload_ = arm.get("reloaddelay", 1)
    burst = arm.get("burst", 1)
    delays = arm.get("burstdelays", "5")
    if not int32_value(reload_) or int(reload_) <= 0:
        return "ReloadDelay must be a positive Int32"
    if not int32_value(burst) or int(burst) <= 0:
        return "Burst must be a positive Int32"
    if not scalar_value(delays, "burstdelays"):
        return "BurstDelays must be a nonempty Int32 list"
    count = len(str(delays).split(","))
    if int(burst) > 1 and count not in (1, int(burst) - 1):
        return "BurstDelays must have one entry or Burst - 1 entries"
    return None


def apply_checked(editors, ledger_bytes, desired, source_bytes=None) -> bool:
    """Stage extraction away from proposal ledgers; roll back on any failed gate."""
    originals = dict(ledger_bytes)
    originals.update({path: ed.original for path, ed in editors.items()})
    originals.update({path: path.read_bytes() for path in (LEDGER / "derived").glob("*.json")})
    # Earlier graph snapshots win: a writer changing an input during initial
    # extraction or planning must be detected, not adopted as our baseline.
    originals.update(source_bytes or {})
    transaction = Transaction(originals)
    with tempfile.TemporaryDirectory(prefix="cameo_balance_apply_") as temporary:
        staging = pathlib.Path(temporary) / "ledgers"
        recovery = pathlib.Path(temporary) / "originals"
        recovery.mkdir()
        for index, (path, data) in enumerate(originals.items()):
            (recovery / f"{index}.original").write_bytes(data)
        (recovery / "paths.json").write_text(json.dumps(
            {str(index): str(path) for index, path in enumerate(originals)}, indent=2), encoding="utf-8")
        print(f"Recovery originals (retained if the process is forcibly killed): {recovery}")
        success = False
        try:
            transaction.check_unchanged()
            for path, ed in editors.items():
                if ed.dirty:
                    transaction.write(path, ed.content())
            subprocess.run([sys.executable, str(ROOT / "tools/balance/extract_stats.py"),
                            "--output-dir", str(staging)], cwd=ROOT, check=True, timeout=900)
            for name, doc in desired.items():
                actual = json.loads((staging / f"{name}.json").read_text(encoding="utf-8"))
                if actual != doc:
                    raise ApplyError(f"{name}: resulting raw ledger differs from requested ledger; "
                                     "shared/inherited effects, skipped edits or unrelated pending proposals")
            subprocess.run([sys.executable, str(ROOT / "tools/audit/audit_multiplier_modifiers.py")],
                           cwd=ROOT, check=True, timeout=300)
            transaction.check_unchanged()
            for path in sorted(staging.rglob("*.json")):
                target = LEDGER / path.relative_to(staging)
                if target not in originals:
                    raise ApplyError(f"new ledger artifact {target}; refresh the baseline first")
                data = path.read_bytes()
                # Git may check out JSON as CRLF. Do not churn unchanged ledgers
                # merely because staged generation uses canonical LF formatting.
                if json.loads(data) != json.loads(originals[target]):
                    transaction.write(target, data)
            transaction.check_unchanged()
            success = True
        except (OSError, ValueError, subprocess.SubprocessError) as error:
            print(f"FAILED: {error}")
            return False
        finally:
            # Includes KeyboardInterrupt and unexpected exceptions. Those are
            # propagated after cleanup, never converted into successful output.
            if not success:
                conflicts = transaction.rollback()
                print("Transaction-owned changes rolled back where ownership still matches.")
                if conflicts:
                    retained = pathlib.Path(tempfile.mkdtemp(prefix="cameo_balance_recovery_"))
                    for file in recovery.iterdir():
                        (retained / file.name).write_bytes(file.read_bytes())
                    print(f"ROLLBACK CONFLICT: {conflicts}; original bytes retained at {retained}")
    return True


if __name__ == "__main__":
    sys.exit(main())
