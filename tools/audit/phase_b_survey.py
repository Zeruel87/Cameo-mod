"""Generate Phase B survey: all weapons still inheriting old full-stack
templates, grouped by inherited families and dominant damage.

Output: a markdown report at docs/audit/latest/phase_b_survey.md with:
- per old-family group: weapons, concrete only, families inherited,
  dominant warhead (highest Damage), total DPS-ish, recommended collapse
  target (just a heuristic suggestion, needs maintainer sign-off).
"""
import re
import sys
from datetime import date
from pathlib import Path
from collections import defaultdict

# CENTRAL / OLD_FAMILIES live in weapon_families.py — they were copy-pasted across
# the weapon-split tools (audit_code_duplication C3), so a family added to one copy
# went missing from the others.
from weapon_families import MOD, OLD_FAMILIES, weapon_files  # noqa: E402,F401
from cameo_model import Model  # noqa: E402

FILES = weapon_files()
RULESET = Model(MOD.parents[1]).rs


def inherited_flat_warhead_keys(family):
    """Positive flat hits supplied by one resolved legacy family."""
    node = RULESET.resolve_weapon(family)
    if node is None:
        return {family.lstrip("^")}
    keys = set()
    for warhead in node.children:
        if not warhead.key.startswith("Warhead"):
            continue
        if "Percentage" in warhead.key or "Concrete" in warhead.key:
            continue
        if warhead.value not in {"AreaDamage", "SpreadDamage"}:
            continue
        try:
            damage = int(str(warhead.get("Damage") or "0").strip())
        except ValueError:
            continue
        if damage > 0:
            keys.add(warhead.key.split("@", 1)[1])
    return keys or {family.lstrip("^")}


FAMILY_FLAT_WARHEADS = {
    family: inherited_flat_warhead_keys(family) for family in OLD_FAMILIES
}
RE_INHERITS_OLD = re.compile(r"^\s*Inherits(?:@\w+)?\s*:\s*\^\w+")
# MiniYAML template names begin with ``^`` and concrete weapon names may contain
# punctuation.  ``\w+`` silently merged a concrete block with the following
# template block, attributing that template's retired inherits to the concrete
# weapon above it.
RE_TOPNAME = re.compile(r"^([^\s:#][^:]*):\s*$")
RE_WARHEAD = re.compile(r"^\s*Warhead@(\w+)\s*:\s*(\S*)")
RE_DAMAGE = re.compile(r"^\s*Damage\s*:\s*(\d+)")

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
        # Several active files repeat the same weapon name. MiniYAML keeps only
        # the winning definition, so counting every source block inflates the
        # remaining debt and can recommend editing a shadowed definition.
        winner = RULESET.weapons.get(name)
        if winner is None:
            continue
        winner_path = (MOD.parents[1] / winner.file).resolve()
        if winner_path != path.resolve() or winner.line != start + 1:
            continue
        block = lines[start:end]
        old_inherits = set()
        deleted_warheads = set()
        has_new_wh = False
        warheads = []  # (key, type, damage, has_children)
        cur_wh = None
        cur_type = ""
        cur_dmg = None
        cur_has_children = False
        for j, ln in enumerate(block):
            raw = ln.rstrip("\r\n")
            m_inh = re.match(r"^\s*Inherits(?:@\w+)?\s*:\s*(\^\w+)", raw)
            if m_inh and m_inh.group(1) in OLD_FAMILIES:
                old_inherits.add(m_inh.group(1))
            m_delete = re.match(r"^\s*-Warhead@(\w+)\s*:", raw)
            if m_delete:
                deleted_warheads.add(m_delete.group(1))
            if re.match(r"^\s*Inherits@wh\d?\s*:\s*\^Warhead_", raw):
                has_new_wh = True
            m_w = RE_WARHEAD.match(raw)
            if m_w:
                deleted_warheads.discard(m_w.group(1))
                if cur_wh is not None:
                    warheads.append((cur_wh, cur_type, cur_dmg, cur_has_children))
                cur_wh = m_w.group(1)
                cur_type = m_w.group(2)
                cur_dmg = None
                cur_has_children = False
            if cur_wh is not None:
                if RE_DAMAGE.match(raw):
                    cur_dmg = int(RE_DAMAGE.match(raw).group(1))
                    cur_has_children = True
                else:
                    cur_has_children = True
        if cur_wh is not None:
            warheads.append((cur_wh, cur_type, cur_dmg, cur_has_children))
        # An old wrapper is no longer a full-stack legacy family only when every
        # positive flat hit supplied by that resolved family is explicitly deleted.
        # It may remain temporarily to carry independently rounded percentage or
        # presentation compatibility fields.
        old_inherits = {
            family for family in old_inherits
            if not FAMILY_FLAT_WARHEADS[family].issubset(deleted_warheads)
        }
        nodes.append({"name": name, "old_inherits": old_inherits, "has_new_wh": has_new_wh,
                      "warheads": warheads, "file": str(path.relative_to(MOD))})
    return nodes

weapons = []
for path in FILES:
    if not path.exists():
        continue
    weapons.extend(parse_file(path))

# group by old inherit families (frozengset of old families)
groups = defaultdict(list)
for w in weapons:
    if w["old_inherits"]:
        key = tuple(sorted(w["old_inherits"]))
        groups[key].append(w)

out = ["# Phase B Mixed-Weapon Survey", "", f"Generated: {date.today().isoformat()}"]

# split templates (^) vs concrete
concrete_groups = {k: [w for w in v if not w["name"].startswith("^")] for k, v in groups.items()}
concrete_groups = {k: v for k, v in concrete_groups.items() if v}
single = {k: v for k, v in concrete_groups.items() if len(k) == 1}
mixed = {k: v for k, v in concrete_groups.items() if len(k) > 1}
# truly single old family, no new warhead inheritance (safe mechanical Phase A)
true_phase_a = [w for k, v in single.items() for w in v if not w["has_new_wh"]]

total = sum(len(v) for v in concrete_groups.values())
out += [
    f"Total concrete weapons on old families: {total}",
    f"Single old-family with new inherits (Phase B completion): {sum(len(v) for v in single.values()) - len(true_phase_a)}",
    f"Pure single old-family (mechanical Phase A candidates): {len(true_phase_a)}",
    f"Mixed old-family (Phase B maintainer sign-off): {sum(len(v) for v in mixed.values())} in {len(mixed)} groups",
    "",
]

out.append("## Pure single old-family (mechanical Phase A candidates)")
for w in sorted(true_phase_a, key=lambda x: (x["file"], x["name"])):
    dom = max(w["warheads"], key=lambda x: x[2] if x[2] is not None else 0) if w["warheads"] else (None, "", 0, False)
    wh_list = ", ".join(f"{k}={d or 0}" for k, t, d, _ in w["warheads"])
    out.append(f"- `{w['name']}` ({w['file']}) | old: {list(w['old_inherits'])[0].lstrip('^')} | {wh_list}")
out.append("")

out.append("## Single old-family with new inherits (finish conversion)")
for key in sorted(single, key=lambda k: (-len([w for w in single[k] if w["has_new_wh"]]), k)):
    fam = key[0].lstrip("^")
    items = [w for w in single[key] if w["has_new_wh"]]
    if not items:
        continue
    out.append(f"### {fam} ({len(items)} weapons)")
    for w in sorted(items, key=lambda x: x["name"]):
        dom = max(w["warheads"], key=lambda x: x[2] if x[2] is not None else 0) if w["warheads"] else (None, "", 0, False)
        wh_list = ", ".join(f"{k}={d or 0}" for k, t, d, _ in w["warheads"])
        out.append(f"- `{w['name']}` ({w['file']}) | {wh_list}")
    out.append("")


out.append("## Mixed-inherit (Phase B) — dominant-damage analysis for maintainer sign-off")
for key in sorted(mixed, key=lambda k: (-len(k), -len(mixed[k]), k)):
    fams = ", ".join(k.lstrip("^") for k in key)
    out.append(f"### {fams} ({len(mixed[key])} weapons)")
    for w in sorted(mixed[key], key=lambda x: x["name"]):
        dom = max(w["warheads"], key=lambda x: x[2] if x[2] is not None else 0) if w["warheads"] else (None, "", 0, False)
        wh_list = ", ".join(f"{k}={d or 0}" for k, t, d, _ in w["warheads"])
        rec = f"collapse to {dom[0]}" if dom[0] else "needs review"
        out.append(f"- `{w['name']}` ({w['file']}) | dominant: {dom[0]}({dom[2] or 0}) | {wh_list} | → {rec}")
    out.append("")

OUTDIR = MOD.parents[1] / "docs" / "audit" / "latest"
OUTDIR.mkdir(parents=True, exist_ok=True)
OUTFILE = OUTDIR / "phase_b_survey.md"
OUTFILE.write_text("\n".join(out), encoding="utf-8")
print(f"Wrote {OUTFILE}")
print(f"Total concrete: {total}")
print(f"Pure single (Phase A): {len(true_phase_a)}")
print(f"Single with new (finish): {sum(len(v) for v in single.values()) - len(true_phase_a)}")
print(f"Mixed (Phase B): {sum(len(v) for v in mixed.values())} in {len(mixed)} groups")
