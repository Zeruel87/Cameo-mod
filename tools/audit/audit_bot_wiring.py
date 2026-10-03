#!/usr/bin/env python3
"""Bot-wiring reachability audit - "can every loaded decision path actually fire?"

Complements `tools/ai/ai_module_map.py` (which inventories loaded instances and the
global provider/consumer graph) by evaluating gates PER BOT TYPE:

* every `ModularBot` type maps to the condition tokens granted to it by
  `GrantConditionOnBotOwner` entries (plus the six runtime `personality-*` tokens
  `BotPersonalityController` grants to `genericbot` players - modelled as
  mutually-exclusive profile states, since the controller revokes the old token);
* every module instance's `RequiresCondition` expression is evaluated against
  each profile - an instance is REACHABLE if it activates under at least one
  profile, under master grants or under the armed-increment regime
  (`tools/ai/increment_switches.yaml` rewrites `GrantConditionOnBotOwner.Bots`);
* seams (IBot* interfaces) are paired provider->consumer WITHIN a profile -
  a provider that only exists on `fransbot` while its consumer only exists on
  `genericbot` is a broken seam the global C1 check cannot see;
* within one profile, two providers of the same seam = an overlapping decision
  authority (DESIGN -19.3 violation candidate).

The map's consumer scan only sees `TraitsImplementing<T>`/`Trait<T>` lookups in
bot-type classes. Three real consumption patterns hide from it, so this audit
adds them:
  - static service locators: `BotUnitLeases.Of(player)` (scanned as `X.Of(`);
  - consumers in helper classes (BotModuleLogic/, states, logs) that are not
    `*BotModule` types;
  - constructor injection (`new RegionMemory(map, cellSize, IBotZoneTopology)`),
    counted when the interface name appears in a consuming file that is neither
    its provider nor its own definition.

Checks:
  R1  loaded instance unreachable in every profile/regime
  R2  gate token never granted to any bot type (typo'd or dead gate)
  R3  seam consumed but no provider inside the same profile
  R4  >1 provider of one seam active in one profile (duplicate authority)
  R5  C# bot type never loaded (dead code), minus documented exceptions:
      merge parents (tools/audit/merged_bot_modules.json), -19.4 held modules,
      classic-only CA stack, update-rule classes miscounted by name
  R6  token granted but required by nothing (dead grant)

Usage:
  python tools/audit/audit_bot_wiring.py           # report
  python tools/audit/audit_bot_wiring.py --json    # machine-readable to stdout
"""
from __future__ import annotations

import argparse
import collections
import json
import pathlib
import re
import sys

REPO = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "tools" / "audit"))
sys.path.insert(0, str(REPO / "tools" / "ai"))
import miniyaml  # noqa: E402
import ai_module_map  # noqa: E402

# Interfaces the ModularBot dispatcher broadcasts to every module - always
# "consumed" (by the dispatcher) and never a broken seam when unpaired.
DISPATCH = {"IBot", "IBotTick", "IBotEnabled", "IBotRespondToAttack",
            "IBotPositionsUpdated", "IBotNotifyIdleBaseUnits", "IBotInfo", "IBotCAInfo",
            # callback seams - a missing implementer means no subscribers, not a break
            "IBotUnitLeaseLost"}

# Seams deliberately provided by more than one module (additive composition -
# consumers Sum/iterate all providers; verified 2026-10-02):
#   IBotRegionThreatProvider - SquadManager sums MasterAi + Scout threat layers
ADDITIVE_SEAMS = {"IBotRegionThreatProvider"}

# R5: C3 categories that are dead code by the letter but alive by design.
# Keyed by exact type name -> reason.
DEAD_OK = {
    # -19.4 held for content that is coming
    "BevManagerBotModule": "-19.4 held - MCV/behemoth owner pending BEV merge",
    "SharedCargoBotModule": "-19.4 held - shared-cargo pending transport harvest",
    "PlugSpawnerBotModule": "-19.4 held - CA plug spawner pending engine gate",
    "PlugSpawnerBotModuleCA": "-19.4 held - CA plug spawner pending engine gate",
    # classic/CA stack - the A/B reference's own modules; parents of merges or
    # classic-only copies (-19.3: classic runs the CA copy)
    "BaseBuilderBotModule": "classic/OpenRA copy superseded by CA merge",
    "BuildingRepairBotModule": "merged into BaseRepairBotModule (merged_bot_modules.json)",
    "CaptureManagerBotModule": "Common copy; classic uses CA variant",
    "CaptureManagerBotASModule": "AS copy; merged into EngineerBotModule seam",
    "CncEngineerManagerBotModule": "merged into EngineerBotModule (merged_bot_modules.json)",
    "HarvesterBotModule": "Common copy; classic uses CA variant",
    "LoadGarrisonerBotModule": "Common copy; classic uses CA variant",
    "McvManagerBotModule": "Common copy; McvExpansionManagerBotModule owns it",
    "McvManagerBotModuleCA": "CA copy dormant; McvExpansionManagerBotModule owns it",
    "McvManagerASBotModule": "AS copy; McvExpansionManagerBotModule owns it",
    "PowerDownBotModuleCA": "CA copy dormant; AS PowerDownBotModule owns it",
    "SquadManagerBotModule": "Common copy; classic uses CA variant",
    "UnitBuilderBotModule": "Common copy; classic uses CA variant",
    # not modules at all - name collision with update-rule classes
    "RemoveAndRenameDefenseRadiusInBaseBuilderBotModule": "update rule, not a module",
    "RemoveBarracksTypesAndVehiclesTypesInBaseBuilderBotModule": "update rule, not a module",
    "DummyBot": "test/scaffold type",
}

BOT_DIRS = [
    REPO / "OpenRA.Mods.Cameo" / "Traits",
    REPO / "OpenRA.Mods.CA" / "Traits" / "BotModules",
    REPO / "engine" / "OpenRA.Mods.AS" / "Traits" / "BotModules",
    REPO / "engine" / "OpenRA.Mods.Common" / "Traits" / "BotModules",
    REPO / "OpenRA.Mods.Fransbot",
]


class Expr:
    """RequiresCondition boolean evaluator: && || ! parens, token atoms."""

    def __init__(self, expr: str):
        self.tokens = re.findall(r"[A-Za-z0-9_\-]+|&&|\|\||!|\(|\)", expr or "")
        self.pos = 0

    def parse(self):
        node = self._or()
        return node

    def _or(self):
        left = self._and()
        while self._peek() == "||":
            self.pos += 1
            left = ("or", left, self._and())
        return left

    def _and(self):
        left = self._not()
        while self._peek() == "&&":
            self.pos += 1
            left = ("and", left, self._not())
        return left

    def _not(self):
        if self._peek() == "!":
            self.pos += 1
            return ("not", self._not())
        if self._peek() == "(":
            self.pos += 1
            node = self._or()
            if self._peek() == ")":
                self.pos += 1
            return node
        tok = self.tokens[self.pos] if self.pos < len(self.tokens) else ""
        self.pos += 1
        return ("atom", tok)

    def _peek(self):
        return self.tokens[self.pos] if self.pos < len(self.tokens) else None

    def atoms(self):
        return {t for t in self.tokens if t not in ("&&", "||", "!", "(", ")")}


def evaluate(node, granted: set) -> bool:
    op = node[0]
    if op == "atom":
        return node[1] in granted
    if op == "not":
        return not evaluate(node[1], granted)
    if op == "and":
        return evaluate(node[1], granted) and evaluate(node[2], granted)
    return evaluate(node[1], granted) or evaluate(node[2], granted)


def load_profiles(rs):
    """bot type -> granted token set, from GrantConditionOnBotOwner + personalities."""
    player = rs.resolve("Player")
    grants = collections.defaultdict(set)   # bot type -> tokens
    granted_tokens = set()
    for c in player.children:
        if not c.key.startswith("GrantConditionOnBotOwner"):
            continue
        cond = c.get("Condition")
        bots = [b.strip() for b in (c.get("Bots") or "").split(",") if b.strip()]
        if not cond:
            continue
        granted_tokens.add(cond)
        for b in bots:
            grants[b].add(cond)

    bot_types = {}
    for c in player.children:
        if not c.key.startswith("ModularBot"):
            continue
        t = c.get("Type")
        if t:
            bot_types[t] = c.key

    # Runtime personalities: genericbot players get exactly one at a time.
    personalities = []
    bpc = REPO / "OpenRA.Mods.Cameo" / "Traits" / "BotPersonalityController.cs"
    if bpc.exists():
        for m in re.finditer(r'"(personality-\w+)"', bpc.read_text(encoding="utf-8", errors="replace")):
            if m.group(1) not in personalities:
                personalities.append(m.group(1))

    profiles = {}
    for t in bot_types:
        base = set(grants.get(t, ()))
        if "genericbot" in base:
            # one personality state per profile - they're mutually exclusive
            for p in personalities or ["personality-none"]:
                profiles[f"{t}:{p}"] = base | {p}
        else:
            profiles[t] = base
    return profiles, bot_types, grants, granted_tokens, personalities


def armed_profiles(profiles, grants, rs):
    """Second regime: increment switches rewrite grant Bots lists to generic tiers.

    Each group in tools/ai/increment_switches.yaml names a
    `GrantConditionOnBotOwner@<key>` instance plus the `Bots:` list the arm
    rewrites it to, so the grant's Condition token becomes live on those bot
    types. Model the union: all groups armed at once. A module reachable only
    under this regime is dormant-on-master but has an arm path."""
    key_token = {}
    for c in rs.resolve("Player").children:
        if c.key.startswith("GrantConditionOnBotOwner") and c.get("Condition"):
            key_token[c.key.split("@")[-1]] = c.get("Condition")
    armed = {p: set(toks) for p, toks in profiles.items()}
    sw = REPO / "tools" / "ai" / "increment_switches.yaml"
    if not sw.exists():
        return armed
    txt = sw.read_text(encoding="utf-8", errors="replace")
    for m in re.finditer(r"GrantConditionOnBotOwner@(\w+):\s*\n\s*Bots:\s*([^\n]+)", txt):
        token = key_token.get(m.group(1))
        if not token:
            continue
        for b in m.group(2).split(","):
            b = b.strip()
            for pname in armed:
                if pname == b or pname.startswith(b + ":"):
                    armed[pname].add(token)
    return armed


def hidden_consumers():
    """Interface consumers missed by the map's TraitsImplementing/Trait regex:
    `X.Of(` service locators and any non-provider file referencing the interface."""
    hits = collections.defaultdict(set)  # iface -> files
    of_pat = re.compile(r"\b(\w+)\.Of\(")
    for d in BOT_DIRS:
        if not d.exists():
            continue
        for f in d.rglob("*.cs"):
            txt = f.read_text(encoding="utf-8", errors="replace")
            rel = f.relative_to(REPO).as_posix()
            for m in of_pat.finditer(txt):
                hits[m.group(1)].add(rel)
    return hits


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    rs = miniyaml.Ruleset(REPO)
    classes, bot_interfaces = ai_module_map.scan_csharp()
    loaded = ai_module_map.loaded_instances()
    profiles, bot_types, grants, granted_tokens, personalities = load_profiles(rs)

    # instance rows: only loaded bot-module types (world traits like
    # AmbientSound/ConditionalWorldTint gate on map conditions -- not bot decisions)
    bot_yaml = set()
    for name, defs in classes.items():
        if name.endswith("Info") or not ai_module_map.is_bot_type(name, defs, bot_interfaces):
            continue
        d = sorted(defs, key=lambda x: [a for a, _ in ai_module_map.SOURCES].index(x["asm"]))[0]
        yaml_key = d["info"][:-4] if d.get("info") else name
        bot_yaml.add(yaml_key)
        bot_yaml.add(name)
    rows = []
    for t, insts in sorted(loaded.items()):
        if t not in bot_yaml:
            continue
        for actor, key, gate in insts:
            rows.append({"type": t, "actor": actor, "key": key, "gate": gate})

    # evaluate gates per profile, under master grants and the armed-increment regime
    armed = armed_profiles(profiles, grants, rs)
    reach = {}   # instance key -> reachability per regime
    for inst in rows:
        tree = Expr(inst["gate"]).parse() if inst["gate"] else None
        atoms = Expr(inst["gate"]).atoms() if inst["gate"] else set()
        ok_master, ok_armed = [], []
        ungranted = set(atoms) - granted_tokens - set(personalities)
        for pname, toks in profiles.items():
            if tree is None or evaluate(tree, toks):
                ok_master.append(pname)
        for pname, toks in armed.items():
            if tree is None or evaluate(tree, toks):
                ok_armed.append(pname)
        reach[inst["key"]] = {"gate": inst["gate"], "type": inst["type"],
                              "master_profiles": ok_master,
                              "armed_profiles": ok_armed,
                              "ungranted_tokens": sorted(ungranted)}

    # unreachable = no profile in EITHER regime; armed-only = dormant on master
    # but an increment switch group arms the gate token (by design)
    r1 = [k for k, v in reach.items()
          if not v["master_profiles"] and not v["armed_profiles"]]
    r1_armed = [k for k, v in reach.items()
                if not v["master_profiles"] and v["armed_profiles"]]
    r2 = sorted({t for v in reach.values() for t in v["ungranted_tokens"]})
    r6 = sorted(g for g in granted_tokens
                if not any(g in (Expr(i["gate"]).atoms() if i["gate"] else set())
                           for i in rows))

    # seam pairing within profiles: which modules are active per profile
    def active_types(profile_tokens):
        out = set()
        for inst in rows:
            if inst["gate"]:
                if not evaluate(Expr(inst["gate"]).parse(), profile_tokens):
                    continue  # fresh Expr per instance -- parse() consumes
            out.add(inst["type"])
        return out

    # providers/consumers from the map's class scan
    provides = collections.defaultdict(set)
    consumes = collections.defaultdict(set)
    type_owner = {}
    for name, defs in classes.items():
        if name.endswith("Info") or not ai_module_map.is_bot_type(name, defs, bot_interfaces):
            continue
        d = sorted(defs, key=lambda x: [a for a, _ in ai_module_map.SOURCES].index(x["asm"]))[0]
        type_owner[name] = d["asm"]
        for b in d["bases"]:
            if b in bot_interfaces:
                provides[b].add(name)
        for m in ai_module_map.LOOKUP.finditer(d["body"]):
            t = m.group("t").removesuffix("Info")
            if t in bot_interfaces or t in classes:
                consumes[t].add(name)

    r3 = collections.defaultdict(set)   # (iface, cons, prov) -> profiles broken
    r4 = collections.defaultdict(set)   # (iface, provs) -> profiles duplicated
    for pname, toks in profiles.items():
        act = active_types(toks)
        for iface, cons in consumes.items():
            if iface in DISPATCH or iface not in bot_interfaces:
                continue
            act_cons = cons & act
            if not act_cons:
                continue
            act_prov = provides.get(iface, set()) & act
            if not act_prov:
                prov_gates = {g["type"]: g["gate"] for g in rows
                              if g["type"] in provides.get(iface, set())}
                r3[(iface, tuple(sorted(act_cons)),
                    tuple(sorted(f"{k}[{v or 'always'}]" for k, v in prov_gates.items())))].add(pname)
        for iface, provs in provides.items():
            act_prov = provs & act
            if len(act_prov) > 1 and iface not in DISPATCH and iface not in ADDITIVE_SEAMS:
                r4[(iface, tuple(sorted(act_prov)))].add(pname)

    # hidden consumers: interfaces whose consumers use locators/ctor-injection -
    # any file naming the interface that is neither its definition nor a provider.
    provider_files = {}
    for name, defs in classes.items():
        for d in defs:
            for b in d["bases"]:
                if b in bot_interfaces:
                    provider_files.setdefault(b, set()).add(d["file"])
    mention = collections.defaultdict(set)
    for d in BOT_DIRS:
        if not d.exists():
            continue
        for f in d.rglob("*.cs"):
            rel = f.relative_to(REPO).as_posix()
            txt = f.read_text(encoding="utf-8", errors="replace")
            for ifc in re.findall(r"IBot\w+", txt):
                mention[ifc].add(rel)
    hidden = {}
    for iface in sorted(bot_interfaces):
        if iface in consumes or iface in DISPATCH:
            continue
        others = sorted(mention.get(iface, set()) - provider_files.get(iface, set()))
        others = [o for o in others if not o.endswith(f"/{iface}.cs")]
        if others:
            hidden[iface] = others

    # R7: every `public readonly bool` on loaded module Info classes -
    # C# default, yaml override (if any), switch-manifest entry (if any).
    flag_pat = re.compile(r"public\s+readonly\s+bool\s+(\w+)\s*=\s*(true|false)")
    switch_txt = ""
    sw = REPO / "tools" / "ai" / "increment_switches.yaml"
    if sw.exists():
        switch_txt = sw.read_text(encoding="utf-8", errors="replace")
    yaml_txt = ""
    for y in (REPO / "mods" / "cameo" / "ai").glob("*.yaml"):
        yaml_txt += y.read_text(encoding="utf-8", errors="replace")
    r7 = []
    for name, defs in classes.items():
        if not name.endswith("Info"):
            continue
        mod = name[:-4]
        if mod not in loaded:
            continue
        if not ai_module_map.is_bot_type(mod, classes.get(mod, []), bot_interfaces):
            continue
        for d in defs:
            for m in flag_pat.finditer(d["body"]):
                fname, default = m.group(1), m.group(2)
                ym = re.search(re.escape(fname) + r"\s*:\s*(\w+)", yaml_txt)
                r7.append({"module": mod, "flag": fname, "csharp_default": default,
                           "yaml": ym.group(1) if ym else None,
                           "armed_by_switch_group": fname in switch_txt})

    r5 = sorted(n for n in classes
                if ai_module_map.is_bot_type(n, classes[n], bot_interfaces)
                and not n.endswith("Info") and n not in loaded and n not in DEAD_OK
                and (n + "Info") in classes)  # trait-ness: modules carry an Info class

    report = {
        "profiles": {k: sorted(v) for k, v in profiles.items()},
        "instances": len(rows),
        "R1_unreachable_instances": r1,
        "R1_armed_only_via_increment_switch": r1_armed,
        "R2_ungranted_gate_tokens": r2,
        "R3_missing_provider_in_profile": {
            f"{k[0]} cons={list(k[1])} prov={list(k[2])}": sorted(v) for k, v in r3.items()},
        "R4_duplicate_authority_in_profile": {
            f"{k[0]} prov={list(k[1])}": sorted(v) for k, v in r4.items()},
        "R5_dead_csharp_types": r5,
        "R5_documented_exceptions": {k: v for k, v in DEAD_OK.items() if k in classes and k not in loaded},
        "R6_granted_never_required": r6,
        "R7_info_flags": r7,
        "hidden_consumption_paths": {k: v for k, v in hidden.items() if v},
    }

    if args.json:
        print(json.dumps(report, indent=1))
        return

    print(f"profiles: {len(profiles)} bot-type/personality states across {len(bot_types)} ModularBot types")
    print(f"instances evaluated: {len(rows)}")
    print(f"R1 unreachable instances (master + all increments armed): {len(r1)}")
    for k in r1:
        print(f"   - {k}  gate={reach[k]['gate']!r}")
    print(f"R1 dormant on master, armed by increment switch: {len(r1_armed)}")
    for k in r1_armed:
        print(f"   - {k}  gate={reach[k]['gate']!r}")
    print(f"R2 gate tokens never granted anywhere: {r2 or 'none'}")
    print(f"R3 consumed-without-provider inside a profile:")
    if r3:
        for (iface, cons, provs), profs in sorted(r3.items()):
            print(f"   {iface}: consumers={list(cons)}")
            print(f"      providers={list(provs) or 'NONE'}")
            print(f"      broken in {len(profs)}/{len(profiles)} profiles")
    else:
        print("   none")
    print(f"R4 duplicate-authority candidates inside a profile:")
    if r4:
        for (iface, provs), profs in sorted(r4.items()):
            print(f"   {iface}: {list(provs)}  ({len(profs)}/{len(profiles)} profiles)")
    else:
        print("   none")
    print(f"R5 C# bot types never loaded: {len(r5)}")
    for n in r5:
        print(f"   - {n}")
    print(f"R5 documented exceptions (loaded nowhere, by design): "
          f"{len(report['R5_documented_exceptions'])}")
    print(f"R6 granted-but-never-required tokens: {r6 or 'none'}")
    dormant = [f for f in r7
               if (f["yaml"] or f["csharp_default"]) == "false"
               and not f["armed_by_switch_group"]]
    armed_only = [f for f in r7 if f["armed_by_switch_group"]]
    print(f"R7 info flags: {len(r7)} total; {len(armed_only)} armed by switch groups; "
          f"{len(dormant)} OFF with no arm path:")
    for f in dormant:
        print(f"   - {f['module']}.{f['flag']} (default={f['csharp_default']}, yaml={f['yaml']})")
    if any(hidden.values()):
        print("hidden consumption paths (map's regex cannot see these):")
        for k, v in hidden.items():
            print(f"   {k} <- {v}")


if __name__ == "__main__":
    main()
