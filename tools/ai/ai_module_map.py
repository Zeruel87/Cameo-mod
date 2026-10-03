#!/usr/bin/env python3
"""Generate the bot-module map: what is loaded, who provides which interface, who consumes it.

The hand-written module table in AI_ARCHITECTURE.md fell behind within days (26 loaded types,
~21 rows). This builds the same picture from the artifacts, so it cannot go stale silently:

* LOADED   - every bot trait instance on the resolved Player / World actors (tools/audit/miniyaml),
             with its RequiresCondition gate;
* PROVIDES - the bot interfaces (IBot*, plus any interface declared in a BotModules folder) each
             bot type's C# class implements;
* CONSUMES - the bot interfaces and concrete bot types each class looks up through
             TraitsImplementing<> / TraitOrDefault<> / Trait<> / TraitInfo(s)<> / TraitInfoOrDefault<>.

Checks (reported, never auto-fixed):
  C1 an interface that is consumed but has no LOADED provider   -> a consumer reads nothing
  C2 an interface with a loaded provider but no consumer         -> a producer awaiting its consumer
  C3 a bot type that exists in C# but is not loaded               -> unused code (see audit_ca_unused)
  C4 a type name declared in more than one assembly               -> shadowing; the first assembly wins

Usage:
  python tools/ai/ai_module_map.py                 # print the map
  python tools/ai/ai_module_map.py --write         # write docs/design/AI_MODULE_MAP.md
  python tools/ai/ai_module_map.py --check         # exit 1 if the written map is stale
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

OUT = REPO / "docs" / "design" / "AI_MODULE_MAP.md"

# Assembly order in mod.yaml decides which same-named type wins (CLAUDE.md rule 7).
SOURCES = [
    ("AS", REPO / "engine" / "OpenRA.Mods.AS"),
    ("CA", REPO / "OpenRA.Mods.CA"),
    ("Cameo", REPO / "OpenRA.Mods.Cameo"),
    ("Common", REPO / "engine" / "OpenRA.Mods.Common"),
    # Last in mod.yaml's Assemblies; its 24 modules serve the hidden `fransbot` donor type
    # (AI_SYNTHESIS.md §7) and were invisible to this map until 2026-09-28.
    ("Fransbot", REPO / "OpenRA.Mods.Fransbot"),
    ("Game", REPO / "engine" / "OpenRA.Game"),
]

CLASS = re.compile(
    r"(?:^|\n)[ \t]*(?:\[[^\]\n]*\][ \t\r\n]*)*(?:(?:public|internal|sealed|abstract|partial|static)\s+)*"
    r"class\s+(?P<name>\w+)\s*(?:<[^>{]*>)?\s*(?::\s*(?P<bases>[^{]+))?\{", re.S)
INTERFACE = re.compile(r"\binterface\s+(?P<name>I\w+)")
LOOKUP = re.compile(r"\b(?:TraitsImplementing|TraitOrDefault|Trait|TraitInfos|TraitInfo|TraitInfoOrDefault|"
                    r"ActorsWithTrait|ActorsHavingTrait)<(?P<t>\w+)>")


def strip_generics(s: str) -> str:
    depth, out = 0, []
    for ch in s:
        if ch == "<":
            depth += 1
        elif ch == ">":
            depth -= 1
        elif depth == 0:
            out.append(ch)
    return "".join(out)


def scan_csharp():
    """Return (classes, interfaces). classes: name -> list of dict(asm, file, bases, body)."""
    classes = collections.defaultdict(list)
    bot_interfaces = set()
    for asm, root in SOURCES:
        if not root.is_dir():
            continue
        for p in root.rglob("*.cs"):
            if any(part in ("obj", "bin") for part in p.parts):
                continue
            text = p.read_text(encoding="utf-8", errors="replace")
            in_bot_dir = "BotModules" in p.parts or "Bot" in p.stem
            for m in INTERFACE.finditer(text):
                n = m.group("name")
                # IBot* plus other interfaces a bot-module file declares with "Bot" in the name;
                # the squad state machine's IState is plumbing inside one module, not a contract
                if n.startswith("IBot") or (in_bot_dir and "Bot" in n):
                    bot_interfaces.add(n)
            matches = list(CLASS.finditer(text))
            for i, m in enumerate(matches):
                end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
                raw_bases = m.group("bases") or ""
                bases = [b.strip() for b in strip_generics(raw_bases).split(",") if b.strip()]
                # the yaml key is the INFO class minus "Info"; the trait class may be named differently
                # (CncEngineerBotModuleInfo -> CncEngineerManagerBotModule), so remember which Info it takes
                info = re.search(r"<\s*(\w+Info)\s*>", raw_bases)
                classes[m.group("name")].append({
                    "asm": asm, "file": p.relative_to(REPO).as_posix(), "bases": bases,
                    "info": info.group(1) if info else None,
                    "body": text[m.start():end], "bot_dir": "BotModules" in p.parts,
                })
    return classes, bot_interfaces


MODULE_NAME = re.compile(
    r"Bot(?:AS)?Module(?:CA)?$|BotManager$|^ModularBot$|^BotLimits$|^BotGlobalUnitBudget$|^ExternalBotOrdersManager$"
    # the Cameo coordination layer: synced controllers, insurance and the bot-owner condition
    r"|^Bot\w*Controller$|BotInsurance$|^GrantConditionOnBotOwner$|^BotRoleSets$")


def is_bot_type(name, defs, bot_interfaces):
    """A bot MODULE: named like one, or implementing a bot interface. Squad states, wrappers and
    helper classes in the BotModules folders are not modules (they are not traits)."""
    return bool(MODULE_NAME.search(name)) or any(
        b in bot_interfaces and b not in ("IBotInfo", "IBotCAInfo") for d in defs for b in d["bases"])


def loaded_instances():
    rs = miniyaml.Ruleset(REPO)
    out = collections.defaultdict(list)  # type -> [(actor, instance key, condition)]
    for actor in ("Player", "World"):
        node = rs.resolve(actor)
        if node is None:
            continue
        for c in node.children:
            if c.key.startswith("-"):
                continue
            base = c.key.split("@", 1)[0]
            out[base].append((actor, c.key, c.get("RequiresCondition") or ""))
    return out


def build():
    classes, bot_interfaces = scan_csharp()
    loaded = loaded_instances()

    # bot types = implementation classes (…BotModule / anything implementing a bot interface)
    bot_types = {}
    for name, defs in classes.items():
        if name.endswith("Info") or not is_bot_type(name, defs, bot_interfaces):
            continue
        bot_types[name] = defs

    def winner(name):
        order = [a for a, _ in SOURCES]
        return sorted(bot_types[name], key=lambda d: order.index(d["asm"]))[0]

    rows = []
    provides = collections.defaultdict(set)   # interface -> loaded providers
    consumers = collections.defaultdict(set)  # interface/type -> consumers (loaded)
    for name in sorted(bot_types):
        d = winner(name)
        yaml_key = d["info"][:-4] if d.get("info") else name
        inst = loaded.get(yaml_key, []) or (loaded.get(name, []) if yaml_key != name else [])
        impl = sorted(b for b in d["bases"] if b in bot_interfaces)
        cons = sorted({m.group("t") for m in LOOKUP.finditer(d["body"])
                       if m.group("t") in bot_interfaces or m.group("t") in bot_types
                       or m.group("t").removesuffix("Info") in bot_types} - {name, name + "Info"})
        rows.append({"name": name, "asm": d["asm"], "file": d["file"], "inst": inst,
                     "impl": impl, "cons": cons, "shadow": sorted({x["asm"] for x in bot_types[name]})})
        if inst:
            for i in impl:
                provides[i].add(name)
            for c in cons:
                consumers[c.removesuffix("Info")].add(name)

    loaded_rows = [r for r in rows if r["inst"]]
    c1 = sorted(i for i in consumers if i in bot_interfaces and i not in provides
                and i not in ("IBot", "IBotInfo", "IBotCA", "IBotCAInfo", "IBotTick", "IBotEnabled"))
    c2 = sorted(i for i in provides if i not in consumers
                and i not in ("IBot", "IBotTick", "IBotEnabled", "IBotRespondToAttack", "IBotPositionsUpdated",
                              "IBotNotifyIdleBaseUnits", "IBotRequestUnitProduction",
                              "IBotRequestPauseUnitProduction", "IBotSuggestRefineryProduction",
                              "IBotBaseExpansion", "IBotAircraftBuilder"))
    c3 = sorted(r["name"] for r in rows if not r["inst"])
    c4 = sorted(r["name"] for r in rows if len(r["shadow"]) > 1)
    return rows, loaded_rows, provides, consumers, c1, c2, c3, c4


def render(rows, loaded_rows, provides, consumers, c1, c2, c3, c4):
    L = []
    L.append("# AI module map (generated)")
    L.append("")
    L.append("_Generated by `python tools/ai/ai_module_map.py --write` from the resolved `Player`/`World`"
             " actors and the C# sources. **Do not edit by hand**; regenerate. `--check` fails when this"
             " file is stale. The binding rules (one authority per decision, absence degrades) are in"
             " [`AI_ARCHITECTURE.md`](AI_ARCHITECTURE.md) §10.1; the pack split is in §2._")
    L.append("")
    n_inst = sum(len(r["inst"]) for r in loaded_rows)
    L.append(f"**{len(loaded_rows)} bot types loaded, {n_inst} instances.** "
             f"{len(rows) - len(loaded_rows)} further bot types exist in C# and are not loaded (C3).")
    L.append("")
    L.append("## Loaded modules")
    L.append("")
    L.append("| Type | Asm | Instances (gate) | Provides | Consumes |")
    L.append("|---|---|---|---|---|")
    for r in loaded_rows:
        inst = "<br>".join(f"`{k}`" + (f" ({c})" if c else "") for _, k, c in r["inst"][:6])
        if len(r["inst"]) > 6:
            inst += f"<br>… {len(r['inst'])} total"
        L.append(f"| `{r['name']}` | {r['asm']} | {inst} | {', '.join(f'`{i}`' for i in r['impl']) or '—'} "
                 f"| {', '.join(f'`{c}`' for c in r['cons']) or '—'} |")
    L.append("")
    L.append("## Interfaces: providers and consumers (loaded modules only)")
    L.append("")
    L.append("| Interface / type | Provided by | Consumed by |")
    L.append("|---|---|---|")
    keys = sorted(set(provides) | {k for k in consumers})
    for k in keys:
        L.append(f"| `{k}` | {', '.join(f'`{x}`' for x in sorted(provides.get(k, []))) or '—'} "
                 f"| {', '.join(f'`{x}`' for x in sorted(consumers.get(k, []))) or '—'} |")
    L.append("")
    L.append("## Checks")
    L.append("")
    L.append(f"* **C1 consumed, no loaded provider ({len(c1)}):** " + (", ".join(f"`{x}`" for x in c1) or "none"))
    L.append(f"* **C2 provided, no consumer yet ({len(c2)}):** " + (", ".join(f"`{x}`" for x in c2) or "none")
             + " (a producer-only landing is expected here until its consumer lane lands)")
    L.append(f"* **C3 bot types in C#, not loaded ({len(c3)}):** " + (", ".join(f"`{x}`" for x in c3) or "none"))
    L.append(f"* **C4 declared in more than one assembly ({len(c4)}):** " + (", ".join(f"`{x}`" for x in c4) or "none"))
    L.append("")
    return "\n".join(L)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    if not (REPO / "engine" / "OpenRA.Mods.Common").is_dir():
        print("engine/ is missing: run make.cmd all first (the map would miss every engine bot module)")
        return 2
    text = render(*build())
    if a.check:
        cur = OUT.read_text(encoding="utf-8") if OUT.is_file() else ""
        if cur != text:
            print(f"STALE: {OUT.relative_to(REPO)} differs; run with --write")
            return 1
        print("AI module map is current.")
        return 0
    if a.write:
        OUT.write_text(text, encoding="utf-8", newline="\n")
        print(f"wrote {OUT.relative_to(REPO)}")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
