#!/usr/bin/env python3
"""QUARANTINED legacy-template migration tool.

Do not use this writer in the folded-percentage family system. Its conversion body still
expects a separate `HealthPercentageDamage` / `*_Percentage` twin and would create or rename
warheads that current generated families no longer provide. It now refuses every run before
loading or editing rules. Keep the implementation only as migration-history reference until it
is redesigned around `PercentageScale` / `PercentageVersus` and independently reviewed.

Historical contract follows:

Move ONE legacy weapon template into the `^Warhead_*` family system, descendants and all.

DESIGN.md is explicit that **`Versus` lives ONLY in `^Warhead_*` templates**. 47 legacy
templates still declare their own, and 1343 weapons inherit them. This converts one
template per run — template-level, so a single edit fixes every weapon under it.

    python tools/balance/retrofit_legacy_template.py ^SwordWeapon
    python tools/balance/retrofit_legacy_template.py ^SwordWeapon --apply

**Why a dedicated tool and not a sweep.** Four things have to happen together or the
result lints clean, boots clean, and is wrong:

1. **Rename the warhead key everywhere at once.** The template's `Warhead@SmallArms`
   becomes `Warhead@Bullet_Light`. Every descendant that overrides the OLD key would
   otherwise become an ORPHAN node that fires *in addition* to the inherited one —
   double damage, no error. (`LESSONS_LEARNED.md` "Bug B", which cost 107 warheads once.)
2. **Drop the restated type.** A descendant saying `Warhead@X: SpreadDamage` re-declares
   the type and blocks the inherited `AreaDamage`, losing the baked friendly fire.
   (Same file, "Bug A".)
3. **Delete the retired `*FriendlyFire` twins.** `AreaDamage` bakes friendly fire in
   (50% damage / 50% radius); leaving the old twin double-counts it.
4. **Pay for the profile change.** The family profile is not the legacy ladder — the
   measured median gap is **1.28x** (`measure_retrofit_gap.py`). Repointing without
   dividing `Damage` by that ratio makes every weapon under the template ~28% more
   lethal. Toxic's gap was 6.26x, which is what made this failure mode obvious.

Geometry (`Spread`, `Falloff`) is preserved verbatim, including materialising the
engine's implicit `SpreadDamage` default falloff when a node relied on it — otherwise
the family's own falloff would silently take over and change every blast radius. Moving
geometry onto the family curves is a separate, maintainer-owned decision
(`docs/design/SPREAD_FALLOFF_PLAN.md`).
"""
from __future__ import annotations

import argparse
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "audit"))
sys.path.insert(0, str(ROOT / "tools" / "balance"))
import miniyaml  # noqa: E402
from measure_retrofit_gap import AMBIGUOUS, EXCEPTIONS, MAPPING, compare, versus_of  # noqa: E402

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# OpenRA `SpreadDamageWarhead.Falloff` default. A legacy node with no explicit `Falloff`
# is relying on this; once it inherits a family template that DOES declare one, the
# implicit default is gone. Materialise it so the blast shape survives the move.
SPREAD_DAMAGE_DEFAULT_FALLOFF = "100, 37, 14, 5, 0"

WEAPON_DIRS = ("mods/cameo/weapons", "mods/cameo/ContentPacks")

# Templates whose main/percentage warhead keys are NOT named after the template. The
# rename is derived from the template name by default (`^SmallArms` -> `Warhead@SmallArms`),
# which silently finds nothing on the pre-DESIGN-§870 templates that still use the retired
# `Warhead@1Dam` numbering — and "renamed nothing but added the inherit" is exactly the
# double-fire bug. The guard in `main()` catches it; this map is the fix.
LEGACY_KEYS = {
    "^MissileWeapon": ("1Dam", "Percentage"),
}


def weapon_files() -> list[pathlib.Path]:
    out = []
    for d in WEAPON_DIRS:
        for p in sorted((ROOT / d).rglob("*.yaml")):
            if "weapon" in p.name.lower() or "/weapons/" in p.as_posix():
                out.append(p)
    return out


class YamlFile:
    """Line-oriented view of a tab-indented OpenRA yaml file.

    Deliberately NOT a round-tripping parser: every edit is scoped to a known line
    range, so untouched lines keep their exact bytes. Line endings are per-file (the
    tree mixes CRLF and LF) and are restored on write.
    """

    def __init__(self, path: pathlib.Path):
        self.path = path
        raw = path.read_bytes().decode("utf-8")
        self.crlf = "\r\n" in raw
        self.lines = raw.replace("\r\n", "\n").split("\n")
        self.dirty = False

    def save(self) -> None:
        text = "\n".join(self.lines)
        if self.crlf:
            text = text.replace("\n", "\r\n")
        self.path.write_bytes(text.encode("utf-8"))

    @staticmethod
    def indent(line: str) -> int:
        return len(line) - len(line.lstrip("\t"))

    def is_content(self, i: int) -> bool:
        line = self.lines[i]
        return bool(line.strip()) and not line.lstrip("\t").startswith("#")

    def block(self, name: str) -> tuple[int, int] | None:
        """Line range [start, end) of a top-level definition, body only."""
        for i, line in enumerate(self.lines):
            if line.startswith(name + ":") and self.indent(line) == 0:
                j = i + 1
                while j < len(self.lines) and (not self.lines[j].strip()
                                               or self.indent(self.lines[j]) >= 1):
                    j += 1
                return i + 1, j
        return None

    def node(self, span: tuple[int, int], key: str) -> tuple[int, int] | None:
        """Line range of a depth-1 child node (header line included)."""
        start, end = span
        for i in range(start, end):
            if not self.is_content(i) or self.indent(self.lines[i]) != 1:
                continue
            if self.lines[i].strip().split(":", 1)[0] == key:
                j = i + 1
                while j < end and (not self.lines[j].strip()
                                   or self.indent(self.lines[j]) >= 2):
                    j += 1
                return i, j
        return None

    def nodes_matching(self, span: tuple[int, int], pattern: re.Pattern) -> list[str]:
        start, end = span
        out = []
        for i in range(start, end):
            if self.is_content(i) and self.indent(self.lines[i]) == 1:
                k = self.lines[i].strip().split(":", 1)[0]
                if pattern.match(k):
                    out.append(k)
        return out

    def child(self, node: tuple[int, int], key: str) -> int | None:
        for i in range(node[0] + 1, node[1]):
            if self.is_content(i) and self.indent(self.lines[i]) == 2:
                if self.lines[i].strip().split(":", 1)[0] == key:
                    return i
        return None

    def replace(self, i: int, line: str) -> None:
        if self.lines[i] != line:
            self.lines[i] = line
            self.dirty = True

    def cut(self, lo: int, hi: int) -> None:
        del self.lines[lo:hi]
        self.dirty = True

    def insert(self, i: int, line: str) -> None:
        self.lines.insert(i, line)
        self.dirty = True


def scale_damage(f: YamlFile, node: tuple[int, int], ratio: float) -> str | None:
    """Divide a node's `Damage` by the profile ratio, preserving resolved DPS.

    Not snapped to the 100 grid on purpose: snapping a set of sibling tiers can collapse
    them onto the same number and destroy the ladder they encode (seen on Toxic, where
    all three levels landed on 200).
    """
    i = f.child(node, "Damage")
    if i is None:
        return None
    raw = f.lines[i].split(":", 1)[1].strip()
    try:
        old = int(raw)
    except ValueError:
        return None
    new = max(1, round(old / ratio))
    f.replace(i, f"\t\tDamage: {new}")
    return f"{old}->{new}"


def preserve_falloff(f: YamlFile, node: tuple[int, int], was_spread_damage: bool) -> bool:
    """Materialise the implicit falloff so inheriting a family curve can't change it.

    Only ever called on the LEGACY TEMPLATE itself. A descendant with no `Falloff` was
    never using the engine default — it was inheriting the template's, and it still will
    once the template carries an explicit one. Pinning the engine default on descendants
    overwrites the very value they were inheriting.
    """
    if not was_spread_damage or f.child(node, "Falloff") is not None:
        return False
    anchor = f.child(node, "Damage") or f.child(node, "Spread")
    if anchor is None:
        return False
    f.insert(anchor + 1, f"\t\tFalloff: {SPREAD_DAMAGE_DEFAULT_FALLOFF}")
    return True


def read_versus(f: YamlFile, node: tuple[int, int]) -> dict[str, int]:
    i = f.child(node, "Versus")
    if i is None:
        return {}
    out = {}
    j = i + 1
    while j < len(f.lines) and (not f.lines[j].strip() or f.indent(f.lines[j]) >= 3):
        if f.is_content(j):
            k, _, v = f.lines[j].strip().partition(":")
            try:
                out[k] = int(v.strip())
            except ValueError:
                pass
        j += 1
    return out


def drop_versus(f: YamlFile, node: tuple[int, int]) -> bool:
    i = f.child(node, "Versus")
    if i is None:
        return False
    j = i + 1
    while j < len(f.lines) and (not f.lines[j].strip() or f.indent(f.lines[j]) >= 3):
        j += 1
    f.cut(i, j)
    return True


# Types the family template supplies, so a child restating one is pure Bug A and the
# restatement is dropped. Anything else (`TargetDamage`, `HealthPercentageDamage`, …) is
# a deliberately different warhead and its type is KEPT, or the rename would change what
# the node does on top of where it points.
FAMILY_SUPPLIED_TYPES = {"SpreadDamage", "AreaDamage"}


def drop_valid_relationships(f: YamlFile, node: tuple[int, int]) -> bool:
    """Let the family's baked friendly fire through.

    The retired `*FriendlyFire` twin was the OLD way to hit allies: a second warhead at
    50% damage / 50% spread, with the main warhead restating `ValidRelationships` to
    exclude `Ally`. `AreaDamage` bakes exactly that in (`FriendlyFireDamage: 50`,
    `FriendlyFireSpread: 50`) on `Ally, Neutral, Enemy`. Delete the twin but leave the
    restated relationships and the weapon ends up hitting allies for NOTHING — a silent
    removal of friendly fire rather than a re-expression of it.
    """
    i = f.child(node, "ValidRelationships")
    if i is None:
        return False
    f.cut(i, i + 1)
    return True


def convert_node(f: YamlFile, span: tuple[int, int], old_key: str, new_key: str,
                 ratio: float, stats: dict, area: bool, pin_falloff: bool,
                 free_relationships: bool, block_name: str,
                 family_versus: dict[str, int] | None = None,
                 inherited_damage: int | None = None) -> None:
    """Rename one warhead node, strip its inline Versus, and pay for the profile change.

    `area` says whether this node participates in the AreaDamage geometry (falloff
    rings). The %-twins do NOT: `HealthPercentageDamageWarhead` derives from
    `TargetDamageWarhead`, which has `Spread` but no `Falloff` at all — flat damage
    inside a radius. Pinning a falloff there would be meaningless, and blanking the type
    so it inherits `AreaDamagePercentage` would silently give every %-twin in the mod a
    damage curve it never had. That flip is W18's atomic change, not this one's.
    """
    node = f.node(span, old_key)
    if node is None:
        return

    # COLLISION: this block already carries the target key as a SEPARATE warhead. A
    # "kitchen sink" weapon can inherit both the legacy template and the family one, so
    # `Warhead@SmallArms: 6000` and `Warhead@Bullet_Light: 16000` are two independent
    # damage sources under the SUM law. Renaming one onto the other makes MiniYaml merge
    # them and the smaller one simply vanishes — AsianSniperAP silently lost 6000 damage,
    # GladiusCannon lost 30000. Merge the scaled damage instead of dropping it.
    existing = f.node(span, new_key)
    if existing is None and inherited_damage is not None:
        # The clash is not in this block: the weapon INHERITS the family warhead from one
        # parent and the legacy warhead from another, so it only appears once MiniYaml
        # resolves the chain. Materialise the merged node here, overriding the inherited
        # damage with the sum, then drop the legacy node.
        add = 0
        di = f.child(node, "Damage")
        if di is not None:
            try:
                add = round(int(f.lines[di].split(":", 1)[1].strip()) / ratio)
            except ValueError:
                add = 0
        f.cut(node[0], node[1])
        span = f.block(block_name)
        if span is not None and add:
            f.insert(span[0], f"\t\tDamage: {inherited_damage + add}")
            f.insert(span[0], f"\t{new_key}:")
        stats["merged"] += 1
        return
    if existing is not None and existing[0] != node[0]:
        add = 0
        di = f.child(node, "Damage")
        if di is not None:
            try:
                add = round(int(f.lines[di].split(":", 1)[1].strip()) / ratio)
            except ValueError:
                add = 0
        f.cut(node[0], node[1])
        # The cut shifted every line after it, so the span is stale — re-derive it.
        span = f.block(block_name)
        existing = f.node(span, new_key) if span else None
        if existing is not None and add:
            ei = f.child(existing, "Damage")
            if ei is not None:
                try:
                    cur = int(f.lines[ei].split(":", 1)[1].strip())
                    f.replace(ei, f"\t\tDamage: {cur + add}")
                except ValueError:
                    pass
        stats["merged"] += 1
        return

    declared = f.lines[node[0]].split(":", 1)[1].strip()
    if area and declared in FAMILY_SUPPLIED_TYPES:
        # Bare header: the concrete type now comes from the `^Warhead_*` parent. Safe
        # only because that parent is added in the same pass (LESSONS_LEARNED: a bare
        # `Warhead@X:` with no same-key ancestor is a boot NRE, not a lint warning).
        f.replace(node[0], f"\t{new_key}:")
        stats["type_dropped"] += 1
    else:
        f.replace(node[0], f"\t{new_key}: {declared}" if declared else f"\t{new_key}:")
    # A node with its OWN inline ladder must be paid for against THAT ladder, not the
    # template's. 134 concrete weapons override `Versus` locally; billing them at the
    # template's ratio leaves each one mis-scaled by however far its custom ladder sat
    # from the template's — which is the whole reason it was written by hand.
    own = read_versus(f, node)
    if own and family_versus:
        ratio = compare(own, family_versus)["ratio"]
        stats["own_ladder"] += 1
    node = f.node(span, new_key)
    if drop_versus(f, node):
        stats["versus_dropped"] += 1
    node = f.node(span, new_key)
    if area and free_relationships and drop_valid_relationships(f, node):
        stats["relationships_freed"] += 1
    node = f.node(span, new_key)
    if area and pin_falloff and preserve_falloff(f, node,
                                                 declared in FAMILY_SUPPLIED_TYPES):
        stats["falloff_pinned"] += 1
    node = f.node(span, new_key)
    d = scale_damage(f, node, ratio)
    if d:
        stats["damage_scaled"].append(d)
    stats["renamed"] += 1


def delete_node(f: YamlFile, span: tuple[int, int], key: str) -> bool:
    node = f.node(span, key)
    if node is None:
        return False
    f.cut(node[0], node[1])
    return True


def ensure_inherits(f: YamlFile, span: tuple[int, int], target: str) -> bool:
    """Add the family parent at the TOP of the block, before any of its own nodes.

    ⚠ `Inherits` POSITION IS SEMANTIC IN OPENRA, NOT COSMETIC. `MiniYaml` walks a
    definition's children in document order and splices the parent's resolved nodes in
    *at the point the `Inherits` line appears*; nodes that come later override earlier
    ones. So a node declared BEFORE an `Inherits` is overridden BY THE PARENT.

    This cost a full debugging round. `^HeavyCannon`, `^MediumCannon` and
    `^TankDestroyerCannon` each already carry `Inherits@glow: ^ImpactGlow` near the END
    of the block (~line 81) while their warheads sit at line 9. Appending the family
    inherit after the last existing one therefore placed it *below* the warheads, and
    the family's `Damage: 2000` / `Spread: 250` / `Falloff` silently overrode the
    template's own rescaled `Damage: 838` and preserved geometry. It lints clean, boots
    clean, and `find_empty_warhead` stays 0 — only a resolve diff shows it.

    Inserting at the top is also the tree's own convention, and it is what makes the
    retrofit's whole contract work: the family supplies the profile, the template keeps
    everything it explicitly restates.
    """
    start, end = span
    for i in range(start, end):
        if not (f.is_content(i) and f.indent(f.lines[i]) == 1):
            continue
        if f.lines[i].strip().startswith("Inherits") \
                and f.lines[i].split(":", 1)[1].strip() == target:
            return False
    f.insert(start, f"\tInherits@wh: {target}")
    return True


def percentage_ratio(rules, legacy: str, target: str, old_tag: str,
                     new_tag: str) -> float:
    """The %-twin carries its OWN small ladder, so it needs its own gap measurement.

    Most legacy twins happen to match their family counterpart exactly (both were
    generated from the same pattern), but assuming that silently mis-scales the ones
    that don't.
    """
    def twin(name, tag, suffix):
        n = rules.weapons.get(name)
        if n is None:
            return None
        for c in n.children:
            if c.key in (f"Warhead@{tag}{suffix}", f"Warhead@{tag}_Percentage"):
                v = c.child("Versus")
                if v is None:
                    return None
                out = {}
                for a in v.children:
                    try:
                        out[a.key] = int((a.value or "").strip())
                    except ValueError:
                        pass
                return out or None
        return None

    old = twin(legacy, old_tag, "Percentage")
    new = twin(target, new_tag, "Percentage")
    if not old or not new:
        return 1.0
    return compare(old, new)["ratio"]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("template", help="legacy template, e.g. ^SwordWeapon")
    ap.add_argument("--apply", action="store_true", help="write the files")
    args = ap.parse_args()

    print("REFUSED: retrofit_legacy_template.py is quarantined.")
    print("It still assumes a separate percentage twin; current families fold percentage "
          "damage into AreaDamage with PercentageScale/PercentageVersus.")
    print("Redesign and independently review the migration before enabling dry-run or --apply.")
    return 2

    legacy = args.template
    if legacy in EXCEPTIONS:
        print(f"REFUSED: {legacy} is a design exception — {EXCEPTIONS[legacy][1]}")
        print("It needs a maintainer ruling, not a mechanical repoint.")
        return 2

    rules = miniyaml.Ruleset(ROOT)
    node = rules.weapons.get(legacy)
    if node is None:
        print(f"{legacy}: not found")
        return 2
    old_versus = versus_of(node)
    if not old_versus:
        print(f"{legacy}: no inline Versus — already converted?")
        return 2

    # Resolve the target the same way the measurement does, so the two can never drift.
    if legacy in AMBIGUOUS:
        scored = []
        for cand in AMBIGUOUS[legacy]:
            fam = rules.weapons.get(f"^Warhead_{cand}")
            if fam and (nv := versus_of(fam)):
                scored.append((cand, compare(old_versus, nv)))
        scored.sort(key=lambda s: -s[1]["corr"])
        target_short, stats0 = scored[0]
    else:
        target_short = MAPPING[legacy]
        fam = rules.weapons.get(f"^Warhead_{target_short}")
        stats0 = compare(old_versus, versus_of(fam))
    target = f"^Warhead_{target_short}"
    ratio = stats0["ratio"]

    old_tag, pct_suffix = LEGACY_KEYS.get(legacy, (legacy.lstrip("^"), None))
    new_tag = target_short
    print(f"{legacy}  ->  {target}")
    print(f"  profile gap {ratio:.3f}x (corr {stats0['corr']:.3f}) "
          f"-> every Damage divided by {ratio:.3f}")

    ff_pat = re.compile(rf"^-?Warhead@{re.escape(old_tag)}.*[Ff]riendly[Ff]ire.*$")
    stats = {"renamed": 0, "versus_dropped": 0, "damage_scaled": [],
             "falloff_pinned": 0, "ff_deleted": 0, "blocks": 0, "files": set(),
             "commented": 0, "type_dropped": 0, "relationships_freed": 0,
             "own_ladder": 0, "merged": 0, "chips": 0}

    # Everything under the template, direct and indirect: an intermediate template that
    # merely relays the inherit still has children overriding the original keys.
    family = {legacy}
    changed = True
    while changed:
        changed = False
        for name, n in rules.weapons.items():
            if name in family:
                continue
            for c in n.children:
                if c.key.startswith("Inherits") and c.value \
                        and c.value.strip() in family:
                    family.add(name)
                    changed = True
                    break

    # The family's own ladders, used to re-price any node that carries a custom one.
    fam_versus = versus_of(rules.weapons[target]) or {}
    fam_pct_versus: dict[str, int] = {}
    for c in rules.weapons[target].children:
        if c.key == f"Warhead@{new_tag}_Percentage":
            v = c.child("Versus")
            if v is not None:
                for a in v.children:
                    try:
                        fam_pct_versus[a.key] = int((a.value or "").strip())
                    except ValueError:
                        pass

    pct_ratio = percentage_ratio(rules, legacy, target, old_tag, new_tag)
    if abs(pct_ratio - 1.0) > 0.001:
        print(f"  %-twin gap {pct_ratio:.3f}x -> its Damage divided separately")

    # Edits are buffered and only flushed once every file has been processed without
    # aborting, so a refusal leaves the tree exactly as it was.
    # Weapons that ALREADY resolve `Warhead@<new_tag>` from some other parent. For these
    # the rename would collide at merge time and MiniYaml would keep only one node, so
    # the legacy warhead's damage would vanish silently. Recorded here as the damage the
    # merged node has to preserve.
    inherited: dict[str, int] = {}
    merge_targets: dict[str, int] = {}
    for name in family:
        if name == legacy:
            continue
        try:
            res = rules.resolve_weapon(name)
        except Exception:
            continue
        if res is None:
            continue
        old_d = new_d = None
        for c in res.children:
            d = c.child("Damage")
            if d is None:
                continue
            try:
                val = int((d.value or "").strip())
            except ValueError:
                continue
            if c.key == f"Warhead@{old_tag}":
                old_d = val
            elif c.key == f"Warhead@{new_tag}":
                new_d = val
        if old_d is not None and new_d is not None:
            # Both resolve, so after the rename MiniYaml merges them into ONE node and
            # the legacy damage is simply lost. Preserve the SUM law by writing the total
            # into this weapon's own block.
            merge_targets[name] = new_d + round(old_d / ratio)

    pending: list[YamlFile] = []
    # Judged across ALL files, never per-file: a name can be defined twice in this tree
    # (`^MissileWeapon` lives in both the live weapons.yaml and the dead missiles.yaml),
    # and the dead copy is often an empty stub.
    converted_template = False
    comment_pat = re.compile(rf"^#?\s*\t*-?Warhead@{re.escape(old_tag)}")
    for path in weapon_files():
        f = YamlFile(path)
        # Index the file's top-level names once; scanning every family member against
        # every file is ~14k full-file scans otherwise.
        present = {f.lines[i][:-1] for i in range(len(f.lines))
                   if f.lines[i].endswith(":") and YamlFile.indent(f.lines[i]) == 0}
        for name in sorted(family & present):
            span = f.block(name)
            if span is None:
                continue
            # Count commented-out references so a later revival can't silently
            # resurrect a key that no longer exists anywhere.
            for i in range(*span):
                if f.lines[i].lstrip("\t").startswith("#") and comment_pat.match(
                        f.lines[i].lstrip("\t")):
                    stats["commented"] += 1

            had_ff = False
            for key in f.nodes_matching(span, ff_pat):
                if delete_node(f, span, key):
                    stats["ff_deleted"] += 1
                    had_ff = True
                    span = f.block(name)

            before = stats["renamed"]
            pct_key = f"Warhead@{pct_suffix}" if pct_suffix \
                else f"Warhead@{old_tag}Percentage"
            convert_node(f, span, pct_key,
                         f"Warhead@{new_tag}_Percentage", pct_ratio, stats,
                         area=False, pin_falloff=False, free_relationships=False,
                         block_name=name, family_versus=fam_pct_versus)
            span = f.block(name)
            convert_node(f, span, f"Warhead@{old_tag}", f"Warhead@{new_tag}",
                         ratio, stats, area=True,
                         # Only the template can be relying on the ENGINE default; every
                         # descendant inherits the template's explicit value.
                         pin_falloff=(name == legacy),
                         # Only where a twin actually existed — a node that restates
                         # `ValidRelationships` with no twin never had friendly fire, and
                         # granting it some is a design change, not a retrofit.
                         free_relationships=had_ff,
                         block_name=name, family_versus=fam_versus,
                         inherited_damage=inherited.get(name))
            span = f.block(name)
            # The shield-only `*ExtraDamage` chip is a THIRD key, and its legacy name
            # sometimes drops the "Weapon" suffix (`TeslaChargedWeapon` -> the chip is
            # `TeslaChargedExtraDamage`). Leaving it un-renamed puts it alongside the
            # family's own chip, so the weapon fires BOTH — EMPGrenadeExplode ended up
            # with 2000 + 1000 of chip damage where it had 2000.
            for chip_tag in {old_tag, old_tag.removesuffix("Weapon")}:
                convert_node(f, span, f"Warhead@{chip_tag}ExtraDamage",
                             f"Warhead@{new_tag}_ExtraDamage", 1.0, stats,
                             area=False, pin_falloff=False, free_relationships=False,
                             block_name=name)
                span = f.block(name)
                if span is None:
                    break
            if span is None:
                continue
            if name in merge_targets:
                total = merge_targets[name]
                node = f.node(span, f"Warhead@{new_tag}")
                if node is None:
                    f.insert(span[0], f"\t\tDamage: {total}")
                    f.insert(span[0], f"\tWarhead@{new_tag}:")
                else:
                    di = f.child(node, "Damage")
                    if di is not None:
                        f.replace(di, f"\t\tDamage: {total}")
                    else:
                        f.insert(node[0] + 1, f"\t\tDamage: {total}")
                stats["merged"] += 1
                span = f.block(name)
            if name == legacy:
                ensure_inherits(f, span, target)
            if name == legacy and stats["renamed"] > before:
                converted_template = True
            if stats["renamed"] != before or name == legacy:
                stats["blocks"] += 1
                stats["files"].add(path.relative_to(ROOT).as_posix())
        pending.append(f)

    if not converted_template:
        # Adding the family inherit while leaving the legacy main warhead in place gives
        # the template TWO damage warheads that both fire. It lints clean, it boots
        # clean, and it doubles the weapon's damage. Refuse rather than write it.
        print(f"  ABORT: found no `Warhead@{old_tag}` in {legacy}, so adding "
              f"`Inherits@wh: {target}` would leave its existing damage warhead in "
              f"place alongside the inherited one — DOUBLE damage.")
        print(f"  Fix: add {legacy!r} to LEGACY_KEYS with its real key names.")
        return 2

    for f in pending:
        if f.dirty and args.apply:
            f.save()

    print(f"  blocks touched      : {stats['blocks']} in {len(stats['files'])} files")
    print(f"  warhead keys renamed: {stats['renamed']}")
    print(f"  restated types cut  : {stats['type_dropped']} (now inherit AreaDamage)")
    print(f"  inline Versus gone  : {stats['versus_dropped']}")
    print(f"  retired FF twins cut: {stats['ff_deleted']} "
          f"({stats['relationships_freed']} mains freed to the baked FF)")
    print(f"  falloff pinned      : {stats['falloff_pinned']} (template only)")
    print(f"  Damage rescaled     : {len(stats['damage_scaled'])} "
          f"({stats['own_ladder']} priced against their OWN custom ladder)")
    if stats["commented"]:
        print(f"  ! commented-out refs to the old key left alone: {stats['commented']}")
    if stats["damage_scaled"][:6]:
        print(f"    e.g. {', '.join(stats['damage_scaled'][:6])}")
    print("  (dry run — pass --apply to write)" if not args.apply else "  WRITTEN")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
