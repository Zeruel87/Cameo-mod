#!/usr/bin/env python3
"""apply_harvester_durability.py — classic-four harvester durability batch (2026-09-18).

Applies the 2026-09-16 reference-map targets (docs/audit/latest/
Cameo-reference-map-original-four-20260916.html, "chassis-only" rows,
weapon column WITHHELD 0/n sources) for the five classic-four economy
units, per the 2026-09-15 accepted-batch conventions:

    HP -> 1,000 grid; speed -> 1; cost -> 10 grid; heal/repair steps
    scaled by the same ratio so F1/F2 (audit_stat_formulas.py) stay
    exact: Repairable.HpPerStep == HP/20, ChangesHealth@SelfHealing
    .Step == HP/2500, and F8 pins Mobile.TurnSpeed == round(Speed/5).

The shared templates (^TDHARV, ^RAHARV) are NOT edited: ^TDHARV also
feeds the four Tiberian Sun harvesters and ^RAHARV also feeds japan's
japaneseoretruck, neither of which is in the classic-four scope.
Instead each of the five actors receives per-actor child blocks in its
own yaml, the same "materialized override" shape the engine already
uses on td_nod_stealthharvester and ra1_soviets_heavyindustrialminer.

Batch table (unsnapped target -> applied):
    td_gdi_tiberiumharvester   239,813 -> 240,000  speed 69  cost 1,670
    td_nod_tiberiumharvester   239,813 -> 240,000  speed 69  cost 1,670
    td_nod_stealthharvester    175,085 -> 175,000  speed 77  cost 1,520
    ra1_allies_alliedoretruck  209,944 -> 210,000  speed 81  cost 1,560
    ra1_soviets_oretruck       209,944 -> 210,000  speed 81  cost 1,560

Heal/repair scaling keeps time-to-full and repair time-to-full constant:
    td harvesters      Step 60 -> 96   HpPerStep 7,500 -> 12,000
    stealth harvester  Step 50 -> 70   HpPerStep 6,250 ->  8,750
    ra1 ore trucks     Step 40 -> 84   HpPerStep 5,000 -> 10,500
TurnSpeed follows the F8 law: 60->69 => 12->14, 75->77 => 15, 90->81
=> 18->16.

Idempotent: every patched field must land on its listed pre-edit value
(EXPECTED_OLD) or the script exits nonzero WITHOUT writing that file, so
an unexpected yaml state is refused loudly instead of silently clobbered.
This is NOT an apply_balance pass on purpose: inherited-src edits still
need per-actor materialization. The extract/apply pipeline now carries
the named self-heal and repair fields, but it cannot materialize an
inherited field. This standalone writer uses the same transaction layer
as apply_balance and validates every file before any replacement.
 Dry/confirm distinction is not needed: this script only
materializes the batch the reference map already computed; the commit
carries the playtest report and Aedis's review is the gate.
"""
from __future__ import annotations

import pathlib
import re
import sys

from apply_transaction import ApplyError, Transaction

ROOT = pathlib.Path(__file__).resolve().parents[2]

GDI_VEH = ROOT / "mods/cameo/ContentPacks/TiberianDawn/GDI/yaml/vehicles.yaml"
NOD_VEH = ROOT / "mods/cameo/ContentPacks/TiberianDawn/Nod/yaml/vehicles.yaml"
US_VEH = ROOT / "mods/cameo/ContentPacks/RedAlert/Allies/yaml/vehicles.yaml"
SOV_VEH = ROOT / "mods/cameo/ContentPacks/RedAlert/Soviets/yaml/vehicles.yaml"

SPECS = {
    "td_gdi_tiberiumharvester": (
        GDI_VEH,
        None,
        {"Valued": {"Cost": 1670},
         "Mobile": {"Speed": 69, "TurnSpeed": 14},
         "Health": {"HP": 240000},
         "Repairable": {"HpPerStep": 12000},
         "ChangesHealth@SelfHealing": {"Step": 96}},
    ),
    "td_nod_tiberiumharvester": (
        NOD_VEH,
        None,
        {"Valued": {"Cost": 1670},
         "Mobile": {"Speed": 69, "TurnSpeed": 14},
         "Health": {"HP": 240000},
         "Repairable": {"HpPerStep": 12000},
         "ChangesHealth@SelfHealing": {"Step": 96}},
    ),
    "td_nod_stealthharvester": (
        NOD_VEH,
        None,
        {"Valued": {"Cost": 1520},
         "Mobile": {"Speed": 77},
         "Health": {"HP": 175000},
         "Repairable": {"HpPerStep": 8750},
         "ChangesHealth@SelfHealing": {"Step": 70}},
    ),
    "ra1_allies_alliedoretruck": (
        US_VEH,
        None,
        {"Valued": {"Cost": 1560},
         "Mobile": {"Speed": 81, "TurnSpeed": 16},
         "Health": {"HP": 210000},
         "Repairable": {"HpPerStep": 10500},
         "ChangesHealth@SelfHealing": {"Step": 84}},
    ),
    "ra1_soviets_oretruck": (
        SOV_VEH,
        None,
        {"Valued": {"Cost": 1560},
         "Mobile": {"Speed": 81, "TurnSpeed": 16},
         "Health": {"HP": 210000},
         "Repairable": {"HpPerStep": 10500},
         "ChangesHealth@SelfHealing": {"Step": 84}},
    ),
}


# Every targeted resolved field is declared as (complete old value,
# complete target value).  The materializer validates this resolved vector
# before it constructs an editor, which covers inherited template baselines as
# well as fields already owned by an actor.  A target that is already at its
# target tuple is idempotent; any other value refuses the whole batch.
EXPECTED_RESOLVED = {
    "td_gdi_tiberiumharvester": {
        "Valued.Cost": ("1000", "1670"),
        "Mobile.Speed": ("60", "69"),
        "Mobile.TurnSpeed": ("12", "14"),
        "Health.HP": ("150000", "240000"),
        "Repairable.HpPerStep": ("7500", "12000"),
        "ChangesHealth@SelfHealing.Step": ("60", "96"),
    },
    "td_nod_tiberiumharvester": {
        "Valued.Cost": ("1000", "1670"),
        "Mobile.Speed": ("60", "69"),
        "Mobile.TurnSpeed": ("12", "14"),
        "Health.HP": ("150000", "240000"),
        "Repairable.HpPerStep": ("7500", "12000"),
        "ChangesHealth@SelfHealing.Step": ("60", "96"),
    },
    "td_nod_stealthharvester": {
        "Valued.Cost": ("1000", "1520"),
        "Mobile.Speed": ("75", "77"),
        "Health.HP": ("125000", "175000"),
        "Repairable.HpPerStep": ("6250", "8750"),
        "ChangesHealth@SelfHealing.Step": ("50", "70"),
    },
    "ra1_allies_alliedoretruck": {
        "Valued.Cost": ("1000", "1560"),
        "Mobile.Speed": ("90", "81"),
        "Mobile.TurnSpeed": ("18", "16"),
        "Health.HP": ("100000", "210000"),
        "Repairable.HpPerStep": ("5000", "10500"),
        "ChangesHealth@SelfHealing.Step": ("40", "84"),
    },
    "ra1_soviets_oretruck": {
        "Valued.Cost": ("1000", "1560"),
        "Mobile.Speed": ("90", "81"),
        "Mobile.TurnSpeed": ("18", "16"),
        "Health.HP": ("100000", "210000"),
        "Repairable.HpPerStep": ("5000", "10500"),
        "ChangesHealth@SelfHealing.Step": ("40", "84"),
    },
}

# Local child guards use the same complete old tuple.  Inherited fields do not
# have a local line yet, so insertion is allowed after resolved preflight.
EXPECTED_OLD = {
    actor: {field: values[0] for field, values in fields.items()}
    for actor, fields in EXPECTED_RESOLVED.items()
}


def load_rules():
    """Resolve active Cameo actors before any target file can be edited."""
    sys.path.insert(0, str(ROOT / "tools" / "audit"))
    from cameo_model import Model
    return Model(ROOT).rs


def _target_fields(fields):
    return {
        f"{trait}.{field}": str(value)
        for trait, children in fields.items()
        for field, value in children.items()
    }


def validate_resolved_targets():
    """Return all preflight failures without mutating any target file."""
    problems = []
    if set(EXPECTED_RESOLVED) != set(SPECS):
        problems.append("declared resolved guard does not cover exactly SPECS")
    if set(EXPECTED_OLD) != set(EXPECTED_RESOLVED):
        problems.append("declared local old guard does not cover exactly resolved guards")
    # Keep the resolved vector and the local optimistic guard tied to the same
    # complete (old, target) declaration.  Without this check a stale local
    # guard could pass preflight against an inherited baseline and only fail
    # after an editor had been opened.
    for actor, declared in EXPECTED_RESOLVED.items():
        old_guard = EXPECTED_OLD.get(actor, {})
        if set(old_guard) != set(declared):
            missing = sorted(set(declared) - set(old_guard))
            extra = sorted(set(old_guard) - set(declared))
            problems.append(
                f"{actor}: old guard field mismatch; missing={missing}, extra={extra}"
            )
            continue
        for path, pair in declared.items():
            if not isinstance(pair, (tuple, list)) or len(pair) != 2:
                problems.append(
                    f"{actor}.{path}: resolved guard must declare a complete old/target pair"
                )
                continue
            if str(old_guard[path]) != str(pair[0]):
                problems.append(
                    f"{actor}.{path}: local old guard {old_guard[path]!r} disagrees "
                    f"with resolved old value {pair[0]!r}"
                )
    if problems:
        return problems
    rules = load_rules()
    for actor, (_, _, fields) in SPECS.items():
        declared = EXPECTED_RESOLVED.get(actor, {})
        targets = _target_fields(fields)
        if set(declared) != set(targets):
            missing = sorted(set(targets) - set(declared))
            extra = sorted(set(declared) - set(targets))
            problems.append(
                f"{actor}: resolved guard field mismatch; missing={missing}, extra={extra}"
            )
            continue
        node = rules.resolve(actor)
        if node is None:
            problems.append(f"{actor}: target actor does not resolve")
            continue
        for path, target in targets.items():
            trait, _, field = path.partition(".")
            child = node.child(trait)
            actual = child.get(field) if child is not None else None
            old, declared_target = (str(v) for v in declared[path])
            if declared_target != target:
                problems.append(
                    f"{actor}.{path}: SPECS target {target!r} disagrees with guard {declared_target!r}"
                )
            if actual is None or str(actual) not in {old, declared_target}:
                problems.append(
                    f"{actor}.{path}: refusing unexpected resolved value {actual!r}; "
                    f"expected {old!r} or {declared_target!r}"
                )
    return problems


class ActorEditor:
    def __init__(self, path: pathlib.Path):
        raw = path.read_bytes()
        self.original = raw
        self.bom = raw.startswith(b"\xef\xbb\xbf")
        text = raw.decode("utf-8-sig")
        self.crlf = "\r\n" in text
        self.lines = text.replace("\r\n", "\n").split("\n")
        self.problems: list[str] = []

    def content(self) -> bytes:
        out = "\n".join(self.lines)
        if self.crlf:
            out = out.replace("\n", "\r\n")
        return (b"\xef\xbb\xbf" if self.bom else b"") + out.encode()

    def span(self, actor: str) -> tuple[int, int, int]:
        """Return (header_index, end_index_exclusive, child_indent_tabs)."""
        start = None
        for i, line in enumerate(self.lines):
            if line.rstrip() == f"{actor}:" :
                start = i
                break
        if start is None:
            raise SystemExit(f"actor {actor} not found")
        end = len(self.lines)
        indent = None
        for j in range(start + 1, len(self.lines)):
            line = self.lines[j]
            if not line.strip():
                continue
            tabs = len(line) - len(line.lstrip("\t"))
            if tabs == 0:
                end = j
                break
            if indent is None:
                indent = tabs
        return start, end, (indent if indent is not None else 1)

    def child_span(self, block, end, child: str, indent: int):
        """Return (child_index, child_end) or None."""
        pat = re.compile(f"^\t{{{indent}}}{re.escape(child)}:")
        i = block
        while i < end:
            m = pat.match(self.lines[i])
            if m:
                j = i + 1
                while j < end:
                    nxt = self.lines[j]
                    if not nxt.strip():
                        j += 1
                        continue
                    t = len(nxt) - len(nxt.lstrip("\t"))
                    if t <= indent:
                        break
                    j += 1
                return i, j
            i += 1
        return None

    def patch_child(self, block, end, indent, name, fields, report, allowed_old):
        span = self.child_span(block, end, name, indent)
        if span is None:
            return False
        ci, ce = span
        sub_indent = indent + 1
        for key, want in fields.items():
            pat = re.compile(f"^(\t{{{sub_indent}}}{re.escape(key)}:)\\s*(.*?)\\s*(#.*)?$")
            hit = None
            for k in range(ci + 1, ce):
                m = pat.match(self.lines[k])
                if m:
                    hit = (k, m)
                    break
            if hit is None:
                self.problems.append(f"{name}.{key}: key absent inside existing child")
                continue
            k, m = hit
            old = m.group(2)
            if old == str(want):
                report.append(f"{name}.{key}: already {want}")
                continue
            # allowed_old is keyed by the SHORT field name (the caller builds
            # it per (actor, child) from the actor-level EXPECTED_OLD rows);
            # deriving the key back to `Actor.Field` here again would look up
            # a key the caller never stored and refuse every pre-vector.
            if old not in allowed_old.get(key, ()):
                self.problems.append(
                    f"{name}.{key}: refusing to overwrite unexpected value {old!r}"
                )
                continue
            self.lines[k] = f"{m.group(1)} {want}"
            report.append(f"{name}.{key}: {old} -> {want}")
        return True

    def insert_child(self, actor, block, end, indent, name, fields, report):
        pad = "\t" * indent
        sub = "\t" * (indent + 1)
        lines = [f"{pad}{name}:"] + [f"{sub}{k}: {v}" for k, v in fields.items()]
        # Insert at the END of the actor block: siblings later in the block
        # win same-key merges, and templates merge in at the `Inherits:`
        # position, so a child placed before `Inherits:` would be silently
        # overridden by the template (seen on this batch: before-Inherits
        # placement failed to resolve). Keep the phantom trailing newline
        # element ("" after split) last, so the file keeps its final
        # newline when the actor is the last one in the file.
        at = min(end, len(self.lines))
        if at == len(self.lines):
            if self.lines and self.lines[-1] == "":
                at -= 1
            else:
                self.lines.append("")
        self.lines[at:at] = lines
        for key, want in fields.items():
            report.append(f"{name}.{key}: added {want}")
        return len(lines)

    def apply(self, actor: str, fields: dict[str, dict[str, int]]):
        allowed = EXPECTED_OLD.get(actor, {})
        report: list[str] = []
        block, end, indent = self.span(actor)
        # Patch existing children first (order-independent).
        remaining = dict(fields)
        for name in list(remaining):
            allow: dict[str, tuple] = {}
            for key in remaining[name]:
                pre = allowed.get(f"{name}.{key}")
                if pre is not None:
                    allow[key] = (pre,)
            if self.child_span(block, end, name, indent) is not None:
                self.patch_child(block, end, indent, name, remaining.pop(name), report, allow)
        # Insert the children the actor does not own yet.
        for name, vals in remaining.items():
            end += self.insert_child(actor, block, end, indent, name, vals, report)
        return report


def main() -> int:
    # Resolve every actor and validate the complete old/target vector before
    # opening an editor.  This is the all-or-nothing boundary for inherited
    # baselines and locally-owned fields alike.
    preflight = validate_resolved_targets()
    if preflight:
        for problem in preflight:
            print(f"   PROBLEM {problem}")
        print("REFUSED WRITING: resolved preflight failed; no batch files were written")
        return 1

    by_file: dict[pathlib.Path, list[tuple[str, dict]]] = {}
    for actor, (path, _, fields) in SPECS.items():
        by_file.setdefault(path, []).append((actor, fields))
    rc = 0
    pending: list[tuple[pathlib.Path, bytes, bytes]] = []
    for path, actors in by_file.items():
        ed = ActorEditor(path)
        for actor, fields in by_file[path]:
            report = ed.apply(actor, fields)
            print(f"-- {actor}")
            for line in report:
                print(f"   {line}")
        if ed.problems:
            rc = 1
            for p in ed.problems:
                print(f"   PROBLEM {p}")
            print(f"   REFUSED WRITING {path}")
            continue
        pending.append((path, ed.original, ed.content()))
    if rc:
        print("REFUSED WRITING: at least one file failed validation; no batch files were written")
        return rc
    transaction = Transaction({path: original for path, original, _ in pending})
    try:
        for path, _, content in pending:
            transaction.write(path, content)
    except BaseException as error:
        conflicts = transaction.rollback()
        print(f"REFUSED WRITING: transaction failed: {error}")
        if conflicts:
            print("ROLLBACK CONFLICTS:", ", ".join(conflicts))
        return 1
    return rc


if __name__ == "__main__":
    sys.exit(main())
