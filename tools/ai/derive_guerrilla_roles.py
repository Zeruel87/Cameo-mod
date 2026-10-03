#!/usr/bin/env python3
"""Generate the `guerrilla` bot role on each ContentPack's own actors (AI_ARCHITECTURE.md §2.8a).

Ruled 2026-09-27: guerrilla (raid) units are fast/light only, generated from traits, never
hand-typed (AI_SYNTHESIS.md §3.1). Bands ruled 2026-09-29: a unit is a guerrilla when it is in
the FASTEST THIRD of its own faction's infantry (or vehicles) AND costs at most that group's
median. The faction is the ContentPack (`ContentPacks/<Theme>/<Faction>/`); the bot cannot see
packs at rules load, which is why the band is computed here and written as `BotRoles` on the
actor, and `BotRoleSets` turns the role into `SquadManagerBotModuleCA.GuerrillaTypes`.

The pool, per faction and per infantry/vehicle group, is every actor that is
  * producible: Buildable with a queue that some actor's Production produces,
  * armed with a weapon that can hurt an enemy (not a healer or repairer),
  * mobile on the ground (Mobile, not a naval or subterranean locomotor: ships are their own squads),
  * not artillery or fire support: no ^ArtilleryTemplate / ^ArtilleryTankTemplate / ^FireSupportTemplate
    ancestor (ruled 2026-09-29: those form the artillery and fire-support squads),
  * not an engineer, saboteur or spy (captures buildings, or infiltrates),
  * not a Harvester and not a Building, and has a Valued cost.
Band, over the group's sorted values: speed >= the value at index floor(0.67 n) and
cost <= the value at index floor(0.5 n).

    python tools/ai/derive_guerrilla_roles.py            # report: per faction, what the band selects
    python tools/ai/derive_guerrilla_roles.py --check    # exit 1 if a pack's BotRoles differ from the band
    python tools/ai/derive_guerrilla_roles.py --write    # add/remove `guerrilla` in each actor's BotRoles
"""
from __future__ import annotations

import argparse
import collections
import pathlib
import re
import sys

REPO = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "tools" / "audit"))
import miniyaml  # noqa: E402

ROLE = "guerrilla"
# Ruled 2026-09-29: artillery squads are the artillery and artillery-tank templates ONLY; fire-support units
# form their own squads with tanks, protecting the artillery; ships are their own squads, never mixed into
# ground or air squads. None of them raid.
NOT_GUERRILLA_TEMPLATES = {"^ArtilleryTemplate", "^ArtilleryTankTemplate", "^FireSupportTemplate"}
NON_GROUND_LOCOMOTORS = {"naval", "subterranean"}  # naval = a ship (the navalunit role's own rule)
SPEED_QUANTILE = 0.67  # fastest third
COST_QUANTILE = 0.5  # at most the median
PACK = re.compile(r"ContentPacks[\\/]([^\\/]+)[\\/]([^\\/]+)[\\/]")


def traits(node, name):
    return [c for c in node.children if c.key.split("@", 1)[0] == name and not c.key.startswith("-")]


def field(node, key):
    for c in node.children:
        if c.key == key:
            return c.value
    return None


def wdist(value):
    m = re.fullmatch(r"(-?\d+)c(\d+)", (value or "").strip())
    if m:
        return int(m.group(1)) * 1024 + int(m.group(2))
    v = (value or "").strip()
    return int(v) if v.lstrip("-").isdigit() else 0


def csv(value):
    return [t.strip() for t in (value or "").split(",") if t.strip()]


def quantile(values, q):
    v = sorted(values)
    return v[min(len(v) - 1, int(q * len(v)))]


def pool(rs):
    """Every guerrilla candidate as a dict, plus the actors outside any pack that would qualify."""
    resolved = {a: rs.resolve(a) for a in rs.actors if not a.startswith("^")}
    # A queue is real when a factory lists it (Production, MaterializingProduction, ProductionAirdropCA, ...:
    # any trait with Produces) or a player queue declares it (ProductionQueue Type: SCZergInfantry, larva-morphed).
    produced = set()
    for n in resolved.values():
        for t in (n.children if n is not None else []):
            if t.key.startswith("-"):
                continue
            produced.update(csv(field(t, "Produces")))
            if t.key.split("@", 1)[0].endswith("ProductionQueue"):
                produced.update(csv(field(t, "Type")))
    out = []
    for a, n in resolved.items():
        if n is None:
            continue
        buildable = traits(n, "Buildable")
        if not buildable or not set(csv(field(buildable[0], "Queue"))) & produced:
            continue
        arms, mobile, valued = traits(n, "Armament"), traits(n, "Mobile"), traits(n, "Valued")
        if not arms or not mobile or not valued or traits(n, "Harvester") or traits(n, "Building"):
            continue
        if field(mobile[0], "Locomotor") in NON_GROUND_LOCOMOTORS:
            continue
        if ancestors(rs, a) & NOT_GUERRILLA_TEMPLATES:
            continue
        hostile = False
        for arm in arms:
            weapon = field(arm, "Weapon")
            w = rs.resolve_weapon(weapon) if weapon else None
            hostile |= w is not None and hurts_enemies(w)
        if not hostile:
            continue  # a healer / repairer: ally-only warheads
        try:
            speed, cost = int(field(mobile[0], "Speed")), int(field(valued[0], "Cost"))
        except (TypeError, ValueError):
            continue
        # engineers and saboteurs (they capture BUILDINGS) and spies are not raiders; every infantryman
        # also Captures ra2garrison / driverless_vehicle, so the building type is the discriminator
        if traits(n, "Infiltrates") or any("building" in csv(field(t, "CaptureTypes")) for t in traits(n, "Captures")):
            continue
        src = rs.actors[a]
        out.append({
            "id": a, "speed": speed, "cost": cost,
            "infantry": bool(traits(n, "TakeCover") or traits(n, "WithInfantryBody")),
            "faction": faction_of(a, src.file), "file": src.file, "line": src.line,
        })
    return out


_ANCESTORS: dict[str, set[str]] = {}


def ancestors(rs, name, _stack=()):
    """Every template the actor inherits, transitively (the resolved node no longer shows them)."""
    if name not in _ANCESTORS:
        out = set()
        node = rs.actors.get(name)
        if node is not None and name not in _stack:
            for c in node.children:
                if c.key.split("@", 1)[0] == "Inherits" and not c.key.startswith("-") and c.value:
                    parent = c.value.strip()
                    out |= {parent} | ancestors(rs, parent, _stack + (name,))
        _ANCESTORS[name] = out
    return _ANCESTORS[name]


def hurts_enemies(weapon):
    """Some warhead of the weapon may hit an enemy (ValidRelationships unset means Enemy, Neutral)."""
    for wh in weapon.children:
        if wh.key.split("@", 1)[0] == "Warhead" and not wh.key.startswith("-"):
            rel = csv(field(wh, "ValidRelationships"))
            if not rel or "Enemy" in rel:
                return True
    return False


def faction_of(actor, path):
    """The ContentPack; for an actor still defined in a central rules file, `<file stem>/<id prefix>`
    (rules/outpost2.yaml holds both EDEN_* and PLYMOUTH_*), or `<file stem>/shared` without a prefix."""
    m = PACK.search(path or "")
    if m:
        return f"{m.group(1)}/{m.group(2)}"
    stem = pathlib.Path(path or "unknown").stem
    return f"{stem}/{actor.split('_', 1)[0].lower() if '_' in actor else 'shared'}"


def band(candidates):
    groups = collections.defaultdict(list)
    for c in candidates:
        groups[(c["faction"], c["infantry"])].append(c)
    chosen = {}
    for (_, _), g in sorted(groups.items()):
        fast = quantile([c["speed"] for c in g], SPEED_QUANTILE)
        cheap = quantile([c["cost"] for c in g], COST_QUANTILE)
        for c in g:
            if c["speed"] >= fast and c["cost"] <= cheap:
                chosen[c["id"]] = c
    return chosen


# --- the actor's own BotRoles block in its pack file ---------------------------------------------

def block_span(lines, header):
    """Indices [header, end) of the actor's block: the header and every indented or blank line after it."""
    end = header + 1
    while end < len(lines) and (lines[end].startswith("\t") or not lines[end].strip()):
        end += 1
    while end > header + 1 and not lines[end - 1].strip():
        end -= 1
    return end


def own_lines(lines, header, end):
    """Line indices of the actor's own `BotRoles:` block (header + its `Roles:` child) or `-BotRoles:` cancel."""
    out = []
    for i in range(header + 1, end):
        if lines[i].rstrip() in ("\tBotRoles:", "\t-BotRoles:"):
            out.append(i)
            j = i + 1
            while j < end and lines[j].startswith("\t\t"):
                out.append(j)
                j += 1
    return out


def roles_of(node):
    """Resolved roles; None when the node has no BotRoles trait at all."""
    t = traits(node, "BotRoles") if node is not None else []
    return set(csv(field(t[0], "Roles"))) if t else None


def parent_roles(rs, actor):
    """What the actor would inherit with no BotRoles of its own: the last parent carrying BotRoles wins,
    as MiniYaml merges later Inherits over earlier ones."""
    got = None
    for c in rs.actors[actor].children:
        if c.key.split("@", 1)[0] == "Inherits" and not c.key.startswith("-") and c.value:
            r = roles_of(rs.resolve(c.value.strip()))
            if r is not None:
                got = r
    return got


def write_own(lines, header, target, inherited):
    """Make the actor's own lines give it exactly `target` roles. Returns True if the lines changed."""
    end = block_span(lines, header)
    old = own_lines(lines, header, end)
    if set(target) == (inherited or set()):
        new = []  # the parents already give exactly this (or nothing, and nothing is wanted)
    elif not target:
        new = ["\t-BotRoles:"]  # cancel an inherited guerrilla that has nothing left
    else:
        # a child `Roles:` REPLACES the parent's value, so the block repeats every role the actor keeps
        new = ["\tBotRoles:", "\t\tRoles: " + ", ".join(sorted(target))]
    if [lines[i] for i in old] == new:
        return False
    for i in reversed(old):
        del lines[i]
    at = old[0] if old else header + 1
    if not old:
        while at < end and re.match(r"\tInherits(@\S+)?:", lines[at]):
            at += 1
    lines[at:at] = new
    return True


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    mode = ap.add_mutually_exclusive_group()
    mode.add_argument("--check", action="store_true", help="exit 1 if any pack's guerrilla BotRoles differ from the band")
    mode.add_argument("--write", action="store_true", help="add/remove the guerrilla role in the packs")
    ap.add_argument("--show", action="store_true", help="list the chosen ids per faction")
    args = ap.parse_args()

    # A tag written on a parent actor reaches its children only on the next resolve, so --write repeats.
    for _ in range(4):
        rs, candidates, chosen, adds, removes, changed_files = sync(args.write)
        if not args.write or not changed_files:
            break
    report(args, candidates, chosen, adds, removes)
    return 1 if args.check and (adds or removes) else 0


def sync(write):
    _ANCESTORS.clear()
    rs = miniyaml.Ruleset(REPO)
    candidates = pool(rs)
    chosen = band(candidates)

    # what the rules declare today (any actor, not only candidates: a stale tag must be removed too)
    by_file = collections.defaultdict(list)
    for a, src in rs.actors.items():
        if not a.startswith("^") and src.file:
            by_file[src.file].append((a, src.line))

    changed_files, adds, removes = 0, [], []
    for path, entries in sorted(by_file.items()):
        p = REPO / path if not pathlib.Path(path).is_absolute() else pathlib.Path(path)
        raw = p.read_bytes().decode("utf-8")
        eol = "\r\n" if "\r\n" in raw else "\n"
        lines = raw.split(eol)
        dirty = False
        # bottom-up so inserted lines never shift a header still to be visited
        for a, line in sorted(entries, key=lambda e: -e[1]):
            header = line - 1
            if header >= len(lines) or lines[header].rstrip() != f"{a}:":
                if a in chosen:
                    print(f"SKIP {a}: header not found at {path}:{line}", file=sys.stderr)
                continue
            # the RESOLVED roles decide: a guerrilla parent actor would otherwise pass the tag to its children
            resolved = roles_of(rs.resolve(a)) or set()
            want = a in chosen
            if (ROLE in resolved) != want:
                (adds if want else removes).append(a)
                if write:
                    target = (resolved - {ROLE}) | ({ROLE} if want else set())
                    dirty |= write_own(lines, header, target, parent_roles(rs, a))
        if dirty:
            p.write_bytes(eol.join(lines).encode("utf-8"))
            changed_files += 1
    return rs, candidates, chosen, adds, removes, changed_files


def report(args, candidates, chosen, adds, removes):
    factions = sorted({c["faction"] for c in candidates})
    per = collections.Counter(c["faction"] for c in chosen.values())
    print(f"guerrilla band: {len(chosen)} actors in {len(factions)} factions "
          f"(infantry {sum(c['infantry'] for c in chosen.values())}, vehicles {sum(not c['infantry'] for c in chosen.values())}); "
          f"per faction min {min(per.get(f, 0) for f in factions)}, max {max(per.values())}; pool {len(candidates)}")
    central = sorted(a for a, c in chosen.items() if not PACK.search(c["file"] or ""))
    if central:
        print(f"tagged in a central rules file (not yet in a ContentPack): {len(central)}")
    if args.show:
        for f in factions:
            print(f"  {f}: " + ", ".join(sorted(a for a, c in chosen.items() if c["faction"] == f)))
    print(f"actors still to change: +{len(adds)} -{len(removes)}")
    if args.check and (adds or removes):
        for a in adds[:20]:
            print(f"  missing guerrilla: {a}")
        for a in removes[:20]:
            print(f"  guerrilla outside the band (own tag or inherited from a parent actor): {a}")
        print("FAIL: run tools/ai/derive_guerrilla_roles.py --write")


if __name__ == "__main__":
    sys.exit(main())
