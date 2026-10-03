#!/usr/bin/env python3
"""Preview BotRoleSets role derivation against the resolved ruleset — the §2.8
review gate without booting the game (bot-roles.log needs a match; this needs
only the tree).

Mirrors `BotRoleSetsInfo.ResolveMembers` (OpenRA.Mods.Cameo/Traits/BotModules/
BotRoleSets.cs): an actor derives into a role when it is buildable, has every
DeriveHas trait type (C# base-class names count — `AttackAircraft` satisfies
`AttackBase`), satisfies every DeriveHasField predicate, no DeriveNotField
predicate, and is not Excluded. Trait type names are expanded by walking the
`class XInfo : YInfo` declarations in the C# sources, and the virtual
`Weapons.ValidTargets` is the union of the ValidTargets of the weapons on the
actor's enabled armaments, and the sibling virtual `Weapons.AirArmament`
classes each actor `dedicated` (an enabled armament whose weapon may ONLY hit
air), `auxiliary` (air-capable but no pure-AA armament) or nothing. An armament
counts as enabled exactly when its
RequiresCondition BooleanExpression evaluates true under
`VariableExpression.NoVariables` — every identifier resolves false, so
`!token` is true while a bare token, `a && b` and `a || b` are all false.
Expressions using operators outside the boolean subset (arithmetic,
relational, `~`, unary `-`) are treated as undecidable: the armament is
included and the actor is counted in the approximation report.

Usage: python tools/ai/derive_roles_preview.py [--role fighter] [--show 30] [--compare]
                                            [--allow-degraded]

Requires a COMPLETE tree (engine/ sources present — same completeness rule as
tools/audit/run_all.sh). Without them it refuses (exit 2) rather than printing
numbers a missing corpus would falsify.

Resolving every actor's inherit chain takes a few minutes on the full
ruleset (~3.5k actors) — still far cheaper than booting a match for
bot-roles.log.

For every role defined in mods/cameo/ai/ai.yaml's BotRoleSets block it prints
the derived member list (explicit `BotRoles.Roles` members included, as the
engine collects them). `--compare` diffs each role against the written lists
its `Targets` fields name — the both / written-only / derived-only split that
the §2.8 review wants before a role lands in `Apply:`. A predicate field no
actor could resolve prints an ERROR and the exit code is 1 (the engine would
throw YamlException at rules load for the same typo).
"""
from __future__ import annotations

import argparse
import glob
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "audit"))
import miniyaml  # noqa: E402

REPO = miniyaml.find_repo_root(pathlib.Path(__file__))

CS_GLOBS = (
    "engine/OpenRA.Mods.Common/**/*.cs",
    "engine/OpenRA.Mods.CA/**/*.cs",
    "engine/OpenRA.Mods.D2k/**/*.cs",
    "engine/OpenRA.Mods.AS/**/*.cs",
    "engine/OpenRA.Game/**/*.cs",
    "OpenRA.Mods.CA/**/*.cs",
    "OpenRA.Mods.Cameo/**/*.cs",
)

# WeaponInfo.ValidTargets default when a weapon declares none.
VALID_TARGETS_DEFAULT = {"ground", "water"}

# Target classes that count as "air" for Weapons.AirArmament (mirrors
# BotRoleSets.AirClasses): a weapon whose ValidTargets is a subset is a
# `dedicated` AA armament; merely overlapping makes it `auxiliary`.
AIR_CLASSES = {"air", "aircraft"}


def trait_table() -> tuple[dict[str, str], dict[str, dict[str, tuple[str, str | None]]]]:
    """Scan the C# sources for `class XInfo : BaseInfo` declarations and their
    public field declarations.

    Returns (parents, field_decls): `XInfo -> YInfo` and
    `XInfo -> {Field -> (TypeName, initializer_text_or_None)}`. Class bodies
    are found by scanning to the next `class` keyword (or EOF window) —
    heuristic, but TraitInfo classes are flat and field-less bodies simply
    yield no entries.
    """
    parents: dict[str, str] = {}
    decls: dict[str, dict[str, tuple[str, str | None]]] = {}
    cls_re = re.compile(r"class\s+(\w+Info)\s*:\s*([^\n{]+)")
    fld_re = re.compile(
        r"\bpublic\s+(?:readonly\s+)?([\w<>\[\],.]+)\s+(\w+)\s*(?:=\s*([^;]+?))?\s*;")
    for pat in CS_GLOBS:
        for f in glob.glob(str(REPO / pat), recursive=True):
            try:
                text = open(f, encoding="utf-8", errors="replace").read()
            except OSError:
                continue
            for m in cls_re.finditer(text):
                base = re.sub(r"<[^>]*>", "", m.group(2)).split(",")[0].strip()
                if base.endswith("Info"):
                    parents[m.group(1)] = base
                brace = text.find("{", m.end())
                if brace < 0:
                    continue
                nxt = re.search(r"\b(?:class|struct|interface|enum)\s+\w+",
                                text[m.end():m.end() + 60000])
                end = m.end() + (nxt.start() if nxt else 60000)
                d = decls.setdefault(m.group(1), {})
                for fm in fld_re.finditer(text[brace:end]):
                    d.setdefault(fm.group(2),
                                 (fm.group(1), fm.group(3).strip() if fm.group(3) else None))
    return parents, decls


def expanded_field_decl(cls: str, field: str,
                        decls: dict[str, dict[str, tuple[str, str | None]]],
                        parents: dict[str, str]) -> tuple[str, str | None] | None:
    """(TypeName, initializer) for `field` on `cls` or an ancestor; None if
    the field is not declared anywhere in the chain."""
    t = cls
    while t and t not in ("TraitInfo", "ConditionalTraitInfo", "object"):
        d = decls.get(t, {})
        if field in d:
            return d[field]
        t = parents.get(t)
    return None


def default_tokens(ftype: str, init: str | None) -> set[str]:
    """Tokenize a field's compile-time default the way Tokens(value) does:
    explicit literal initializers, else the implicit `default(T)` (false/0/
    null/empty collection)."""
    if init is None:
        if ftype == "bool":
            return {"False"}
        if re.fullmatch(r"int|long|short|byte|float|double|decimal", ftype):
            return {"0"}
        return set()
    v = init.strip()
    if not v or v.startswith("new") or "Set" in ftype or "[]" in ftype or v.startswith("default"):
        return set()  # empty collections, fresh objects, `default` — no tokens
    if v == "true":
        return {"True"}
    if v == "false":
        return {"False"}
    if v.startswith('"') and v.endswith('"'):
        return {v[1:-1]}
    if re.fullmatch(r"-?\d+", v):
        return {v}
    return set()  # non-literal initializer — no tokens


def expand_type_names(node_name: str, parents: dict[str, str]) -> set[str]:
    """Trait type names including base classes, sans the `Info` suffix — the
    mirror of BotRoleSets' TraitTypeNames base-class walk."""
    out, t = set(), node_name + "Info"
    while t and t not in ("TraitInfo", "ConditionalTraitInfo", "object") and t not in out:
        out.add(t[:-4] if t.endswith("Info") else t)
        t = parents.get(t)
    return out


_COND_TOK = re.compile(r"&&|\|\||==|!=|<=|>=|<|>|!|\(|\)|\d+|[A-Za-z_][\w.-]*")


def eval_no_variables(expr: str) -> bool | None:
    """`BooleanExpression.Evaluate(VariableExpression.NoVariables)` — evaluate
    a RequiresCondition with every identifier = 0. Supports `!`, `&&`, `||`,
    `==`, `!=`, `<`, `<=`, `>`, `>=`, parens, `true`/`false` and integer
    literals (the whole decidable core — `x > 1` is `0 > 1` = false with no
    variables). Returns None for anything else (`~`, arithmetic, single
    `&`/`|`) instead of guessing."""
    # Linear lexer — a repeated alternation fullmatch backtracks
    # catastrophically on long nested conditions (the teslacoil armaments).
    toks, pos0, n = [], 0, len(expr)
    while pos0 < n:
        if expr[pos0].isspace():
            pos0 += 1
            continue
        m = _COND_TOK.match(expr, pos0)
        if not m:
            return None
        toks.append(m.group(0))
        pos0 = m.end()
    pos = [0]

    def peek():
        return toks[pos[0]] if pos[0] < len(toks) else None

    def parse_or():
        v = parse_and()
        while peek() == "||":
            pos[0] += 1
            r = parse_and()
            v = int(bool(v) or bool(r))
        return v

    def parse_and():
        v = parse_eq()
        while peek() == "&&":
            pos[0] += 1
            r = parse_eq()
            v = int(bool(v) and bool(r))
        return v

    def parse_eq():
        v = parse_rel()
        while peek() in ("==", "!="):
            op = toks[pos[0]]
            pos[0] += 1
            r = parse_rel()
            v = int((v == r) if op == "==" else (v != r))
        return v

    def parse_rel():
        v = parse_unary()
        while peek() in ("<", "<=", ">", ">="):
            op = toks[pos[0]]
            pos[0] += 1
            r = parse_unary()
            v = int({"<": v < r, "<=": v <= r, ">": v > r, ">=": v >= r}[op])
        return v

    def parse_unary():
        t = peek()
        if t == "!":
            pos[0] += 1
            return int(not parse_unary())
        if t == "(":
            pos[0] += 1
            v = parse_or()
            if peek() != ")":
                raise ValueError("unbalanced parens")
            pos[0] += 1
            return v
        pos[0] += 1
        if t is None:
            raise ValueError("unexpected end")
        tl = t.lower()
        if tl == "true":
            return 1
        if tl == "false":
            return 0
        if t.isdigit():
            return int(t)
        if re.fullmatch(r"[A-Za-z_][\w.-]*", t):
            return 0  # any identifier evaluates 0 with no variables
        raise ValueError(f"undecidable token: {t}")

    try:
        v = parse_or()
    except (ValueError, IndexError):
        return None
    return bool(v) if pos[0] == len(toks) else None


def armament_enabled(node) -> bool | None:
    """Whether the armament is enabled under NoVariables; None when the
    RequiresCondition uses operators beyond the decidable boolean subset."""
    rc = (node.get("RequiresCondition") or "").strip()
    return True if not rc else eval_no_variables(rc)


def collect_actors(rs: miniyaml.Ruleset, parents, decls, field_keys) -> tuple[dict[str, dict], set]:
    """Build RoleCandidates for every concrete actor. Field values mirror
    ReadField: for each declared (trait, field) key, every trait node whose
    expanded type names include `trait` contributes its yaml value or, when
    the key is unset, the C# field default. Returns (actors, field_seen) —
    a key no actor could resolve is a typo the engine would reject."""
    actors: dict[str, dict] = {}
    field_seen: set[tuple[str, str]] = set()
    exp_cache: dict[str, set] = {}
    decl_cache: dict[tuple[str, str], object] = {}
    for name in [k for k in rs.actors if not k.startswith("^")]:
        try:
            node = rs.resolve(name)
        except Exception:
            continue
        if node is None:
            continue
        types = set()
        expanded_by_child: dict[object, set] = {}
        for c in node.children:
            if not c.key.startswith("-"):
                base = c.key.split("@", 1)[0]
                ex = exp_cache.get(base)
                if ex is None:
                    ex = exp_cache[base] = expand_type_names(base, parents)
                expanded_by_child[id(c)] = ex
                types |= ex
        fields: dict[str, set[str]] = {}
        targets, approx, armed = set(), 0, False
        air_capable = dedicated_aa = False
        for c in node.children:
            if c.key.split("@", 1)[0] != "Armament":
                continue
            en = armament_enabled(c)
            if en is False:
                continue
            armed = True
            if en is None:
                approx += 1
            wname = (c.get("Weapon") or "").strip()
            weapon = rs.resolve_weapon(wname) if wname else None
            if weapon is None:
                continue
            raw = weapon.get("ValidTargets")
            vt = {x.strip() for x in raw.split(",") if x.strip()} if raw else set(VALID_TARGETS_DEFAULT)
            targets |= vt
            if {t.lower() for t in vt} & AIR_CLASSES:
                air_capable = True
                if {t.lower() for t in vt} <= AIR_CLASSES:
                    dedicated_aa = True
        if armed:
            field_seen.add(("Weapons", "ValidTargets"))
            field_seen.add(("Weapons", "AirArmament"))
        air_class = {"dedicated"} if dedicated_aa else ({"auxiliary"} if air_capable else set())
        for trait, field in field_keys:
            if (trait, field) == ("Weapons", "ValidTargets"):
                fields[f"{trait}.{field}"] = targets
                continue
            if (trait, field) == ("Weapons", "AirArmament"):
                fields[f"{trait}.{field}"] = air_class
                continue
            vals: set[str] = set()
            for c in node.children:
                if c.key.startswith("-"):
                    continue
                base = c.key.split("@", 1)[0]
                if trait not in expanded_by_child.get(id(c), set()):
                    continue
                decl_key = (base, field)
                decl = decl_cache.get(decl_key, False)
                if decl is False:
                    decl = decl_cache[decl_key] = expanded_field_decl(
                        base + "Info", field, decls, parents)
                if decl is None:
                    continue
                field_seen.add((trait, field))
                raw = c.get(field)
                if raw is not None and raw.strip() != "":
                    vals |= {x.strip() for x in raw.split(",") if x.strip()}
                else:
                    vals |= default_tokens(*decl)
            fields[f"{trait}.{field}"] = vals
        explicit = {x.strip() for x in
                    (node.get("BotRoles", "Roles") or "").split(",") if x.strip()}
        buildable = "Buildable" in types and bool((node.get("Buildable", "Queue") or "").strip())
        actors[name] = {"types": types, "fields": fields, "explicit": explicit,
                        "buildable": buildable, "approx_arms": approx}
    return actors, field_seen


def parse_predicates(spec: str) -> tuple[str, str, bool, set[str]]:
    """`Trait.Field any v|v` / `Trait.Field only v|v` ->
    (trait, field, only, values) — the same 3-part grammar FieldPredicate.Parse
    enforces (a `Trait` name may itself contain dots, so split on the LAST dot)."""
    parts = spec.strip().split()
    if len(parts) != 3 or parts[1] not in ("any", "only"):
        raise ValueError(f"not a `Trait.Field any|only v|v` FieldPredicate: {spec!r}")
    trait, dot, field = parts[0].rpartition(".")
    if not dot or not trait:
        raise ValueError(f"not a `Trait.Field any|only v|v` FieldPredicate: {spec!r}")
    return trait, field, parts[1] == "only", {x.strip() for x in parts[2].split("|") if x.strip()}


def predicate_match(values, only, wanted) -> bool:
    if not values:
        return False
    low = {v.lower() for v in values}
    want = {v.lower() for v in wanted}
    return low <= want if only else bool(low & want)


def read_ai(ai_yaml: pathlib.Path):
    """Load ai.yaml; return (BotRoleSets block, every ModularBot trait node)."""
    ai = miniyaml.load(ai_yaml)
    player = next(n for n in ai if n.key == "Player")
    brs = next(n for n in player.children if n.key.split("@", 1)[0] == "BotRoleSets")
    block = {}
    for section in ("Roles", "DeriveHas", "DeriveNot", "DeriveHasField",
                    "DeriveNotField", "Exclude", "Targets"):
        n = brs.child(section)
        if n is None:
            continue
        block[section] = {c.key: (c.value or "") for c in n.children}
    block["Apply"] = brs.get("Apply") or ""  # scalar comma-list leaf
    modules = [c for c in player.children]
    return block, modules


def csv(text: str) -> list[str]:
    return [x.strip() for x in (text or "").split(",") if x.strip()]


def written_lists(modules, trait_field: str) -> dict[str, set[str]]:
    """`Trait.Field` -> {bot node key -> written actor set} over every bot
    module node in ai.yaml (per-personality hand-maintained lists)."""
    trait, _, field = trait_field.rpartition(".")
    out: dict[str, set[str]] = {}
    for n in modules:
        if n.key.split("@", 1)[0] != trait:
            continue
        raw = n.get(field)
        if raw is not None:
            out[n.key] = set(csv(raw))
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--role", help="only report this role")
    ap.add_argument("--show", type=int, default=40, help="members to print per role")
    ap.add_argument("--allow-degraded", action="store_true",
                    help="run without engine/ sources (results are NOT faithful: "
                         "engine-side trait subclasses and field declarations are invisible)")
    ap.add_argument("--compare", action="store_true",
                    help="also diff each role against the written Targets lists")
    args = ap.parse_args()

    block, modules = read_ai(REPO / "mods" / "cameo" / "ai" / "ai.yaml")
    has, not_ = block.get("DeriveHas", {}), block.get("DeriveNot", {})
    has_f, not_f = block.get("DeriveHasField", {}), block.get("DeriveNotField", {})
    exclude = {r: set(csv(v)) for r, v in block.get("Exclude", {}).items()}
    applied = set(csv(block.get("Apply", "")))
    targets = {r: csv(v) for r, v in (block.get("Targets") or {}).items()}

    preds: dict[str, dict[str, list]] = {}
    field_keys: set[tuple[str, str]] = set()
    for role in set(has_f) | set(not_f):
        hp = [parse_predicates(p) for p in csv(has_f.get(role, ""))]
        np_ = [parse_predicates(p) for p in csv(not_f.get(role, ""))]
        preds[role] = {"has": hp, "not": np_}
        field_keys |= {(t, f) for t, f, _, _ in hp} | {(t, f) for t, f, _, _ in np_}

    # A tree without engine/ sources cannot answer the two questions this gate
    # exists for — engine-side trait subclasses (AttackAircraft -> AttackBase)
    # and engine field declarations (Aircraft.CanHover) are both invisible, so
    # every report would be wrong AND the typo guard would fire on its own
    # missing evidence. Refuse like tools/audit/environment.py diverts run_all;
    # --allow-degraded is the documented escape hatch.
    if not (REPO / "engine" / "OpenRA.Mods.Common").is_dir() and not args.allow_degraded:
        print("refusing: engine/ sources not in this tree — derived memberships "
              "would be wrong (engine trait subclasses and fields are invisible). "
              "Run from a complete checkout, or pass --allow-degraded for a "
              "known-degraded result.", file=sys.stderr)
        return 2
    if args.allow_degraded:
        print("warning: --allow-degraded — engine/ sources may be missing; "
              "results are not faithful", file=sys.stderr)

    parents, decls = trait_table()
    actors, field_seen = collect_actors(miniyaml.Ruleset(str(REPO)), parents, decls, field_keys)

    bad = sorted(k for k in field_keys if k not in field_seen)
    for t, f in bad:
        print(f"ERROR: no actor has a `{t}` trait declaring `{f}` — "
              f"the engine throws YamlException at rules load ({t}.{f} is a typo or the field is not public)")

    # Only roles named in DeriveHas or DeriveHasField derive members; an
    # explicit-only role (artillery, firesupport) collects BotRoles members
    # alone — it does not pass every buildable actor through empty specs.
    derived_roles = set(has) | set(has_f)
    roles = sorted(derived_roles |
                   {r for a in actors.values() for r in a["explicit"]})
    if args.role:
        roles = [r for r in roles if r == args.role]

    for role in roles:
        hp = preds.get(role, {}).get("has", [])
        np_ = preds.get(role, {}).get("not", [])
        excl = exclude.get(role, set())
        members: set[str] = set()
        for name, a in actors.items():
            if role in a["explicit"]:
                members.add(name)
            if role not in derived_roles or not a["buildable"]:
                continue
            if not all(h in a["types"] for h in csv(has.get(role, ""))):
                continue
            if any(n in a["types"] for n in csv(not_.get(role, ""))):
                continue
            vals = a["fields"]
            if not all(predicate_match(vals.get(f"{t}.{f}", set()), o, w) for t, f, o, w in hp):
                continue
            if any(predicate_match(vals.get(f"{t}.{f}", set()), o, w) for t, f, o, w in np_):
                continue
            if name in excl:
                continue
            members.add(name)
        state = "APPLIED" if role in applied else "report-only"
        print(f"{role}: {len(members)} members ({state})")
        for m in sorted(members)[: args.show]:
            print(f"    {m}")
        if len(members) > args.show:
            print(f"    … +{len(members) - args.show} more")

        if args.compare:
            for tf in targets.get(role, []):
                lists = written_lists(modules, tf)
                if not lists:
                    print(f"    [{tf}] no written lists found")
                    continue
                written = set().union(*lists.values())
                both = sorted(written & members)
                only_written = sorted(written - members)
                only_derived = sorted(members - written)
                print(f"    [{tf}] {len(lists)} written lists: "
                      f"both={len(both)} written-only={len(only_written)} derived-only={len(only_derived)}")
                for m in only_written[: args.show]:
                    print(f"      - {m}  (written, not derived)")
                for m in only_derived[: args.show]:
                    print(f"      + {m}  (derived, not written)")

    approx = sum(1 for a in actors.values() if a["approx_arms"])
    print(f"\nactors with an undecidable RequiresCondition armament (targets approximated): {approx}")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
