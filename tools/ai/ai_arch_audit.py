#!/usr/bin/env python3
"""Static architecture-coverage audit of the bot stack — the compile-time half of the proof.

`tools/ai/ai_module_map.py` proves what is LOADED and which IBot* seams exist (C1–C4);
`tools/ai/round_trip_check.py` proves which layers left runtime evidence. This audit covers
the static gap between them:

  R1 gate reachability — every RequiresCondition term on a loaded bot-module instance has a
     satisfier: a GrantConditionOnBotOwner whose Bots cover a bot type that can satisfy the
     rest of the gate, an increment-switch group that arms the granter, or a condition the
     C# grants at runtime (personality-*, demand-*, insurance).                     ERROR
  R2 switch wiring — every increment_switches.yaml target exists: the granter instance in
     the resolved Player actor, or the field in the module's C# Info class.         ERROR
  R3 seam liveness — provider-without-consumer (DEAD-END) and consumer-without-provider
     (STARVED), reusing ai_module_map's scan.                                       WARN
  R4 order-issuer overlap — `new Order("NAME"` sites under the three bot-module trees,
     grouped by order; >1 distinct issuing module = shared decision surface.        WARN
  R5 enum reachability — SquadCAType members vs the initial-state switch (SquadCA.cs) and
     RegisterNewSquad drafting sites (SquadManagerBotModuleCA.cs); BotLeasePurpose members
     vs TryClaim/Preempt/Transfer sites.                                            WARN
  R6 dead knobs — `public readonly bool Use*`/`int Max*`/`FrozenSet|string HashSet<string>`
     Info fields never referenced outside their declaration.                       WARN

`--write` emits docs/design/AI_ARCH_COVERAGE.md (fully regenerated); `--check` exits 1 when that
doc is stale or any ERROR finding exists. A missing `engine/` tree is tolerated: the
assembly's modules still appear in the doc (marked `engine`) but C#-side checks skip what
cannot be read.

Usage:
    python tools/ai/ai_arch_audit.py                 # print the findings table
    python tools/ai/ai_arch_audit.py --write         # regenerate docs/design/AI_ARCH_COVERAGE.md
    python tools/ai/ai_arch_audit.py --check         # exit 1 if the doc is stale / ERRORs
"""
from __future__ import annotations

import argparse
import collections
import pathlib
import re
import sys

REPO = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "tools" / "audit"))
sys.path.insert(0, str(REPO / "tools" / "ai"))
import miniyaml  # noqa: E402
import ai_module_map  # noqa: E402
import apply_increment_switches  # noqa: E402

OUT = REPO / "docs" / "design" / "AI_ARCH_COVERAGE.md"
SWITCHES = REPO / "tools" / "ai" / "increment_switches.yaml"

ORDER_ROOTS = [
    REPO / "OpenRA.Mods.Cameo" / "Traits" / "BotModules",
    REPO / "OpenRA.Mods.CA" / "Traits" / "BotModules",
    REPO / "OpenRA.Mods.Fransbot",
]
# Lease purposes are claimed from a few non-module files too (ModularBot lives one dir up).
CLAIM_ROOTS = ORDER_ROOTS + [REPO / "OpenRA.Mods.Cameo" / "Traits"]

LAYERS = ["PERCEPTION", "SITUATION", "STRATEGY", "EXECUTION", "PRODUCTION", "SUPPORT", "TELEMETRY"]

# The canonical layer table is AI_SYNTHESIS.md §7.2; this dict maps every LOADED module type
# to its layer. A loaded type missing here lands in UNMAPPED in the generated doc — that diff
# is the stale detection (the doc can never silently drop a module).
LAYER_OF = {
    # PERCEPTION — fog memory, scouts, combat intel, region/threat observers
    "ScoutBotModule": "PERCEPTION",
    "CombatAnalysisBotModule": "PERCEPTION",
    "ResourceMapBotModule": "PERCEPTION",
    "TacticalMapBotModule": "PERCEPTION",
    "FransStrategicMapBotModule": "PERCEPTION",
    "FransCombatIntelBotModule": "PERCEPTION",
    "FransMineClusterBotModule": "PERCEPTION",
    "FransRiskModelBotModule": "PERCEPTION",
    # SITUATION — BotSituation feeds, personality, utility axes, leads, counter-demand
    "BotCounterDemandController": "SITUATION",
    "BotPersonalityController": "SITUATION",
    "BotLearnedPriors": "SITUATION",
    "BotLimits": "SITUATION",
    "BotRoleSets": "SITUATION",
    "BotUnitRoles": "SITUATION",
    "SiegeEvaluatorBotModule": "SITUATION",
    "FransEconomicSaturationBotModule": "SITUATION",
    # STRATEGY — master AI, director, team role split, expansion planner, mission providers
    "MasterAiBotModule": "STRATEGY",
    "ModularBot": "STRATEGY",
    "ExpansionPlannerBotModule": "STRATEGY",
    "DefenseCoveragePlanner": "STRATEGY",
    "FransbotControllerBotModule": "STRATEGY",
    "FransGeneralBotModule": "STRATEGY",
    "FransCommanderCoreBotModule": "STRATEGY",
    "FransCommandBidBotModule": "STRATEGY",
    # EXECUTION — squad manager, mission consumers, engineers/capturers/garrison/repair,
    # crate/beacon, harvesters, MCV drivers, commanders
    "SquadManagerBotModuleCA": "EXECUTION",
    "EngineerBotModule": "EXECUTION",
    "CaptureManagerBotModuleCA": "EXECUTION",
    "GarrisonDefenseBotModule": "EXECUTION",
    "BaseRepairBotModule": "EXECUTION",
    "BuildingRepairBotModuleCA": "EXECUTION",
    "UnitRepairBotModule": "EXECUTION",
    "BridgeRepairBotModule": "EXECUTION",
    "CratePickupBotModule": "EXECUTION",
    "BeaconResponderBotModule": "EXECUTION",
    "DeployBotModule": "EXECUTION",
    "HarvesterBotModuleCA": "EXECUTION",
    "FransHarvesterBotModule": "EXECUTION",
    "McvExpansionManagerBotModule": "EXECUTION",
    "FransMcvExpansionManagerBotModule": "EXECUTION",
    "LoadCargoBotModule": "EXECUTION",
    "LoadGarrisonerBotModuleCA": "EXECUTION",
    "MinelayerBotModule": "EXECUTION",
    "FransMinelayerBotModule": "EXECUTION",
    "SendUnitToAttackBotModule": "EXECUTION",
    "FransAirCommanderBotModule": "EXECUTION",
    "FransGroundCommanderBotModule": "EXECUTION",
    "FransSeaCommanderBotModule": "EXECUTION",
    "FransSpecOpsCommanderBotModule": "EXECUTION",
    "FransDefenseCommanderBotModule": "EXECUTION",
    "FransTransportCommanderBotModule": "EXECUTION",
    "FransGroundTransferBotModule": "EXECUTION",
    "FransSupplyTruckBotModule": "EXECUTION",
    # PRODUCTION — base builder, unit builder, production requesters/pause
    "BaseBuilderBotModuleCA": "PRODUCTION",
    "UnitBuilderBotModuleCA": "PRODUCTION",
    "UnitCompositionsBotModule": "PRODUCTION",
    "FransBaseBuilderBotModule": "PRODUCTION",
    "FransUnitBuilderBotModule": "PRODUCTION",
    "BotGlobalUnitBudget": "PRODUCTION",
    # SUPPORT — support powers, insurance, watchdogs, plumbing
    "SupportPowerBotModule": "SUPPORT",
    "SupportPowerBotASModule": "SUPPORT",
    "FransSupportPowerBotModule": "SUPPORT",
    "FransSupportCoordinatorBotModule": "SUPPORT",
    "BotInsurance": "SUPPORT",
    "DynamicBotInsurance": "SUPPORT",
    "BotOwnershipWatchdog": "SUPPORT",
    "BotUnitLeaseRegistry": "SUPPORT",
    "PowerDownBotModule": "SUPPORT",
    "GrantConditionOnBotOwner": "SUPPORT",
    "ExternalBotOrdersManager": "SUPPORT",
    "HumanPaceBotModule": "SUPPORT",
    # TELEMETRY — log writers, record sinks
    "AiMissionLogWriter": "TELEMETRY",
}

# ----------------------------------------------------------------------------- #
# condition machinery
# ----------------------------------------------------------------------------- #

TERM = re.compile(r"[A-Za-z0-9_.\-]+")


def split_condition(expr: str) -> list[list[tuple[bool, str]]]:
    """`a && b || c` -> [[(negated, term)...], ...] — OpenRA && binds tighter than ||."""
    out = []
    for alt in expr.split("||"):
        terms = []
        for t in alt.split("&&"):
            t = t.strip()
            neg = t.startswith("!")
            if neg:
                t = t[1:].strip()
            terms.append((neg, t))
        out.append(terms)
    return out


def eval_alt(terms, scopes: dict[str, set], bot_types: set) -> set:
    """Bot types for which one conjunction can hold, given cond -> bots scopes."""
    ctx = set(bot_types)
    for neg, t in terms:
        if not TERM.fullmatch(t):
            continue  # value expression (e.g. `ownsbarr == 2`) — not a condition name
        s = scopes.get(t, set())
        ctx = ctx - s if neg else ctx & s
    return ctx


def load_yaml_side():
    """One Ruleset: resolved Player/World children -> loaded instances, granters, bot types."""
    rs = miniyaml.Ruleset(REPO)
    actors = {}
    for actor in ("Player", "World"):
        node = rs.resolve(actor)
        if node is not None:
            actors[actor] = {c.key: c for c in node.children}
    loaded = collections.defaultdict(list)  # base yaml key -> [(actor, instance key, gate)]
    granters = []  # {actor, key, cond, bots(None=all)}
    bot_types = set()
    for actor, children in actors.items():
        for key, c in children.items():
            base = key.split("@", 1)[0]
            if key.startswith("-"):
                continue
            loaded[base].append((actor, key, c.get("RequiresCondition") or ""))
            if base in ("ModularBot", "Bot", "HackyAI") and c.get("Type"):
                bot_types.add(c.get("Type"))
            if base.startswith("GrantCondition") and c.get("Condition"):
                raw = c.get("Bots")
                bots = None if raw is None else {b.strip() for b in raw.split(",") if b.strip()}
                granters.append({"actor": actor, "key": key, "cond": c.get("Condition"),
                                 "bots": bots})
    return rs, actors, loaded, granters, bot_types


def switch_spec():
    """increment_switches.yaml -> (skip list, {group: {target: {field: value}}}).

    The spec file uses 2-space indentation (its own fixed shape, not engine miniyaml), so it
    is read through its canonical parser, tools/ai/apply_increment_switches.py — the same
    code path that applies the arms. Missing file -> no groups."""
    if not SWITCHES.is_file():
        return [], collections.OrderedDict()
    return apply_increment_switches.load_spec(SWITCHES)


# ----------------------------------------------------------------------------- #
# code-granted conditions (personality-*, demand-*, insurance conditions)
# ----------------------------------------------------------------------------- #

GRANT_CALL = re.compile(r"GrantCondition\(\s*(?P<expr>[^;()\n]*(?:\([^)]*\))?[^;()\n]*)\)")
STR_ARR = re.compile(r'public readonly string\[\]\s+(?P<name>\w+)\s*=\s*\{(?P<lits>[^}]*)\}')
STR_FLD = re.compile(r'public readonly string\s+(?P<name>\w+)\s*=\s*"(?P<lit>[^"]*)"')
LIT = re.compile(r'"([^"]+)"')


def code_grants(classes, module_types, inst_fields):
    """Harvest conditions a loaded module type can grant at runtime.
    inst_fields: type -> list of resolved-instance Nodes (for `Info.Condition`-style reads)."""
    grants = collections.defaultdict(set)  # condition -> granting module types
    files = {}
    for name in module_types:
        for d in classes.get(name, []):
            path = REPO / d["file"]
            if path not in files:
                files[path] = path.read_text(encoding="utf-8", errors="replace") \
                    if path.is_file() else ""
            text = files[path]
            if "GrantCondition(" not in text:
                continue
            field_lits = {m.group("name"): m.group("lit") for m in STR_FLD.finditer(text)}
            arr_lits = {m.group("name"): LIT.findall(m.group("lits"))
                        for m in STR_ARR.finditer(text)}
            found = set()
            for call in GRANT_CALL.finditer(text):
                expr = call.group("expr").strip()
                if expr.startswith('"'):
                    found.update(LIT.findall(expr))
                    continue
                fm = re.match(r"(?:\w+\.)?(\w+)\s*\+\s*\w+\s*$", expr)
                if fm and fm.group(1) in field_lits:
                    # Info.DemandPrefix + demand  ->  prefix x each listed value
                    prefix = field_lits[fm.group(1)]
                    cands = set()
                    for lits in arr_lits.values():
                        cands.update(lits)
                    for node in inst_fields.get(name, []):
                        for arr in arr_lits:
                            v = node.get(arr)
                            if v:
                                cands.update(s.strip() for s in v.split(","))
                    found.update(prefix + c for c in cands)
                    continue
                fm = re.match(r"(?:\w+\.)?(\w+)\s*$", expr)
                if fm:
                    # self.GrantCondition(info.Condition) / GrantCondition(condition):
                    # the field's yaml value on each instance plus every string literal a
                    # same-file Info field could hold (covers locals picked from arrays).
                    fld = fm.group(1)
                    fld_yaml = fld[0].upper() + fld[1:]
                    for node in inst_fields.get(name, []):
                        for k in (fld_yaml, "Condition"):
                            v = node.get(k)
                            if v:
                                found.update(s.strip() for s in v.split(",") if s.strip())
                    if fld in field_lits:
                        found.add(field_lits[fld])
                    if fld in arr_lits:
                        found.update(arr_lits[fld])
                    found.update(field_lits.values())
                    for lits in arr_lits.values():
                        found.update(lits)
            for c in found:
                grants[c].add(name)
    return grants


# ----------------------------------------------------------------------------- #
# order issuers (R4)
# ----------------------------------------------------------------------------- #

ORDER_LIT = re.compile(r'new Order\(\s*"(?P<name>\w+)"')
ORDER_VAR = re.compile(r'new Order\(\s*(?P<var>[A-Za-z_]\w*)\s*[,)]')
METHOD = re.compile(
    r"(?m)^[ \t]*(?:public|private|protected|internal|static|readonly|override|virtual|"
    r"new|sealed|async|partial|extern|\s)*[\w<>\[\],.?() ]*?\b(?P<name>\w+)\s*"
    r"\((?P<params>[^;{()]*)\)\s*(?:$|\{|=>)")
LEASE_HINT = re.compile(r"BotUnitLeases|TryClaim|IsClaimedByOther|IBotUnitLeases")


def split_args(text: str, open_paren: int) -> list[str]:
    """Split the argument list starting at `(` index `open_paren` on top-level commas."""
    args, depth, cur = [], 0, []
    for ch in text[open_paren + 1:]:
        if ch in "(<[":
            depth += 1
        elif ch in ")>]":
            depth -= 1
            if depth < 0:
                break
        if ch == "," and depth == 0:
            args.append("".join(cur))
            cur = []
        else:
            cur.append(ch)
    tail = "".join(cur).strip()
    if tail:
        args.append(tail)
    return args


def issuer_module(cls: str, path: pathlib.Path, bot_type_names: set) -> str:
    """Map the containing class to the module it answers to."""
    if cls in bot_type_names:
        return cls
    if "Squads" in path.parts or cls.endswith("StatesCA") or cls == "StateBaseCA":
        return "SquadManagerBotModuleCA"
    if path.stem in bot_type_names or ai_module_map.MODULE_NAME.search(path.stem):
        return path.stem
    return cls


def order_matrix(bot_type_names: set):
    """-> {order: {module: {'files': set, 'lease': bool}}}, plus per-file text corpus."""
    sites = collections.defaultdict(lambda: collections.defaultdict(
        lambda: {"files": set(), "lease": False, "squad": False}))
    for root in ORDER_ROOTS:
        if not root.is_dir():
            continue
        for p in sorted(root.rglob("*.cs")):
            if any(part in ("obj", "bin") for part in p.parts):
                continue
            text = p.read_text(encoding="utf-8", errors="replace")
            class_spans = [(m.start(), m.group("name")) for m in ai_module_map.CLASS.finditer(text)]

            def enclosing(pos):
                cur = p.stem
                for start, name in class_spans:
                    if start <= pos:
                        cur = name
                    else:
                        break
                return cur

            leased = bool(LEASE_HINT.search(text))
            squad_file = "Squads" in p.parts

            def record(order, pos):
                mod = issuer_module(enclosing(pos), p, bot_type_names)
                e = sites[order][mod]
                e["files"].add(p.relative_to(REPO).as_posix())
                e["lease"] = e["lease"] or leased
                e["squad"] = e["squad"] or squad_file

            for m in ORDER_LIT.finditer(text):
                record(m.group("name"), m.start())

            # `new Order(orderString, ...)` — the literal arrives via the enclosing method's
            # callers (EngineerBotModule.SendOneRepairer) or a local assignment.
            for m in ORDER_VAR.finditer(text):
                var = m.group("var")
                meth = None
                for mm in METHOD.finditer(text, 0, m.start()):
                    if mm.group("name") not in ("if", "for", "foreach", "while", "switch",
                                                "return", "using", "lock", "catch",
                                                "when", "else", "do"):
                        meth = mm
                if meth is None:
                    continue
                # param decls are `in/out/ref Type name`; the name is always last
                params = [pp.strip().split()[-1]
                          for pp in meth.group("params").split(",") if pp.strip()]
                if var in params:
                    idx = params.index(var)
                    call_re = re.compile(rf"\b{re.escape(meth.group('name'))}\s*\(")
                    for cm in call_re.finditer(text):
                        if cm.start() == meth.start():
                            continue
                        args = split_args(text, cm.end() - 1)
                        if idx < len(args):
                            for lit in LIT.findall(args[idx]):
                                record(lit, cm.start())
                # `orderString = "X"` locals in the same file
                for am in re.finditer(rf"\b{re.escape(var)}\s*=\s*\"(\w+)\"", text):
                    record(am.group(1), am.start())
    return sites


# ----------------------------------------------------------------------------- #
# R6 dead knobs
# ----------------------------------------------------------------------------- #

KNOB = re.compile(
    r"public readonly (?:bool\s+(?P<b>Use\w+)|int\s+(?P<i>Max\w+)|"
    r"(?:(?:FrozenSet|HashSet)<string>|string\[\])\s+(?P<s>\w+))")


def cs_corpus():
    corpus = {}
    for root in (REPO / "OpenRA.Mods.Cameo", REPO / "OpenRA.Mods.CA", REPO / "OpenRA.Mods.Fransbot"):
        if not root.is_dir():
            continue
        for p in root.rglob("*.cs"):
            if any(part in ("obj", "bin") for part in p.parts):
                continue
            corpus[p] = p.read_text(encoding="utf-8", errors="replace")
    return corpus


# ----------------------------------------------------------------------------- #
# audit
# ----------------------------------------------------------------------------- #

def audit():
    classes, bot_interfaces = ai_module_map.scan_csharp()
    rows, loaded_rows, provides, consumers, c1, c2, _c3, _c4 = ai_module_map.build()
    rs, actors, loaded, granters, bot_types = load_yaml_side()
    skip, groups = switch_spec()

    bot_type_names = {r["name"] for r in rows}

    # yaml key -> C# type name (Info-derived keys can differ from the class name).
    yamlkey_to_type = {}
    for name, defs in classes.items():
        if name.endswith("Info") or not ai_module_map.is_bot_type(name, defs, bot_interfaces):
            continue
        order = [a for a, _ in ai_module_map.SOURCES]
        d = sorted(defs, key=lambda x: order.index(x["asm"]))[0]
        yamlkey_to_type[d["info"][:-4] if d.get("info") else name] = name

    # The loaded module set: every resolved Player/World child that names a bot module —
    # C# types (by their yaml key) plus MODULE_NAME-matching keys (covers engine modules
    # whose sources are absent from this worktree).
    modules = collections.OrderedDict()  # type name -> {asm, file, insts, impl, cons, source}
    for r in loaded_rows:
        modules[r["name"]] = {"asm": r["asm"], "file": r["file"], "insts": r["inst"],
                              "impl": r["impl"], "cons": r["cons"], "source": True}
    for key, insts in loaded.items():
        if yamlkey_to_type.get(key):
            continue  # already covered by its C# row
        if not ai_module_map.MODULE_NAME.search(key):
            continue
        modules[key] = {"asm": "engine", "file": "", "insts": insts,
                        "impl": [], "cons": [], "source": False}

    findings = []  # (check, severity, text)

    # ---- granter scopes -------------------------------------------------------
    static_scope = collections.defaultdict(set)   # condition -> bot types (in-tree yaml)
    armed_extra = collections.defaultdict(set)    # condition -> bot types (switch-armed)
    cond_granter = collections.defaultdict(set)   # condition -> granter keys
    for g in granters:
        bots = set(bot_types) if not g["bots"] else set(g["bots"])
        if not g["bots"]:
            if g["bots"] is not None:
                findings.append(("R1", "WARN",
                                 f"granter `{g['key']}` has an empty `Bots:` list; "
                                 "treated as granting to every bot type"))
        static_scope[g["cond"]] |= bots
        cond_granter[g["cond"]].add(g["key"])

    granter_keys = {g["key"] for g in granters}
    granter_bases = collections.defaultdict(list)
    for g in granters:
        granter_bases[g["key"].split("@", 1)[0]].append(g)
    arm_note = collections.defaultdict(set)  # condition -> groups that arm it
    for gname, targets in groups.items():
        for tkey, fields in targets.items():
            base, _, suff = tkey.partition("@")
            if not base.startswith("GrantCondition") or "Bots" not in fields:
                continue
            armed_bots = {b.strip() for b in fields["Bots"].split(",") if b.strip()}
            for g in granter_bases.get(base, []):
                if suff and g["key"] != tkey:
                    continue
                if not suff and g["key"] in skip:
                    continue
                armed_extra[g["cond"]] |= armed_bots
                arm_note[g["cond"]].add(gname)

    # ---- code grants ----------------------------------------------------------
    inst_fields = collections.defaultdict(list)  # module type -> resolved instance Nodes
    for key, insts in loaded.items():
        t = yamlkey_to_type.get(key, key)
        for actor, ikey, _gate in insts:
            if ikey in actors.get(actor, {}):
                inst_fields[t].append(actors[actor][ikey])
    grants = code_grants(classes, set(modules), inst_fields)

    code_scope = collections.defaultdict(set)    # condition -> bot types (C#-granted)
    scope_static = {k: set(v) for k, v in static_scope.items()}
    grant_src = collections.defaultdict(set,
                                        {k: set(v) for k, v in cond_granter.items()})
    for _ in range(8):  # fixpoint: a granting module's own gate may need another grant
        changed = False
        for cond, mods in grants.items():
            for mod in mods:
                gates = [g for _, _, g in modules.get(mod, {}).get("insts", [])]
                mb = set(bot_types) if not gates or any(not g.strip() for g in gates) \
                    else set().union(*(eval_alt(a, scope_static, bot_types)
                                       for g in gates if g.strip()
                                       for a in split_condition(g)))
                if mb - code_scope[cond]:
                    code_scope[cond] |= mb
                    changed = True
        for cond, bots in code_scope.items():
            if bots - scope_static.get(cond, set()):
                scope_static.setdefault(cond, set()).update(bots)
        if not changed:
            break
    for cond, mods in grants.items():
        grant_src[cond].update(f"code:{m}" for m in mods)
    scope_armed = {k: set(v) for k, v in scope_static.items()}
    for cond, bots in armed_extra.items():
        scope_armed.setdefault(cond, set()).update(bots)

    # ---- R1: gate reachability ------------------------------------------------
    seen_r1 = set()
    reachable_note = {}  # instance key -> "master" | "armed" | None
    n_gated = 0
    for name, mod in modules.items():
        for actor, ikey, gate in mod["insts"]:
            if not gate.strip():
                continue
            n_gated += 1
            status = None
            culprits, armed_terms = [], []
            for alt in split_condition(gate):
                terms = [(n, t) for n, t in alt if TERM.fullmatch(t)]
                if eval_alt(terms, scope_static, bot_types):
                    status = status or "master"
                    break
                ctx_a = eval_alt(terms, scope_armed, bot_types)
                if ctx_a:
                    status = "armed"
                    armed_terms = [t for n, t in terms if not n
                                   and not (scope_static.get(t, set()) & ctx_a)
                                   and (scope_armed.get(t, set()) & ctx_a)]
                    break
                culprits.extend(t for n, t in terms if not n and not scope_armed.get(t))
            reachable_note[ikey] = status
            if status == "armed":
                tag = (name, gate)
                if tag in seen_r1:
                    continue
                seen_r1.add(tag)
                arms = sorted({g for t in armed_terms for g in arm_note.get(t, ())})
                findings.append(("R1", "ok",
                                 f"`{ikey}` dormant on master: {', '.join(f'`{t}`' for t in armed_terms)} "
                                 f"reach it only via increment arm {', '.join(arms) or '(unknown group)'} "
                                 f"({gate})"))
            if status is None:
                tag = (name, gate, tuple(sorted(set(culprits))))
                if tag in seen_r1:
                    continue
                seen_r1.add(tag)
                if culprits:
                    findings.append(("R1", "ERROR",
                                     f"`{ikey}` gate `{gate}`: nothing grants "
                                     f"{', '.join(f'`{t}`' for t in sorted(set(culprits)))} "
                                     "(no granter, no code grant, no switch arm) — unreachable"))
                else:
                    findings.append(("R1", "ERROR",
                                     f"`{ikey}` gate `{gate}`: terms never co-hold for any "
                                     "bot type — unreachable"))

    # ---- R2: switch wiring ----------------------------------------------------
    inst_keys = {ikey for insts in loaded.values() for _, ikey, _ in insts}
    FIELD_DECL = lambda f: re.compile(  # noqa: E731
        rf"\bpublic\s+(?:readonly\s+)?[\w<>\[\],.?]+\s+{re.escape(f)}\b")
    n_targets = 0
    for gname, targets in groups.items():
        for tkey, fields in targets.items():
            n_targets += 1
            base, _, suff = tkey.partition("@")
            if base.startswith("GrantCondition"):
                ok = (g for g in granter_bases.get(base, [])
                      if (not suff or g["key"] == tkey) and (suff or g["key"] not in skip))
                if not any(ok):
                    findings.append(("R2", "ERROR",
                                     f"switch `{gname}`: granter `{tkey}` not in resolved "
                                     "Player/World — the arm writes nothing"))
                # granter field names (Bots/Condition) live in the engine sources; when
                # engine/ is absent the field check is skipped rather than faked.
                continue
            if suff and tkey not in inst_keys:
                findings.append(("R2", "ERROR",
                                 f"switch `{gname}`: no loaded instance `{tkey}`"))
                continue
            if not suff and not any(k == base or k.startswith(base + "@")
                                    for k in inst_keys if k not in skip):
                findings.append(("R2", "ERROR",
                                 f"switch `{gname}`: no instance of `{base}` in ai yaml"))
                continue
            defs = classes.get(base, [])
            if not defs:
                findings.append(("R2", "WARN",
                                 f"switch `{gname}`: `{base}` has no C# source in this "
                                 "worktree — target unverifiable"))
                continue
            info_names = {d["info"] for d in defs if d.get("info")} or {base + "Info"}
            bodies = [d["body"] for n in info_names for d in classes.get(n, [])]
            for f in fields:
                if bodies and not any(FIELD_DECL(f).search(b) for b in bodies):
                    findings.append(("R2", "ERROR",
                                     f"switch `{gname}`: `{tkey}` sets `{f}` — no such "
                                     f"public field on {sorted(info_names)[0]}"))

    # ---- R3: seam liveness ----------------------------------------------------
    for i in c1:
        findings.append(("R3", "WARN",
                         f"STARVED `{i}`: consumed by {', '.join(f'`{c}`' for c in sorted(consumers[i]))}; "
                         "no loaded provider"))
    for i in c2:
        findings.append(("R3", "WARN",
                         f"DEAD-END `{i}`: provided by {', '.join(f'`{p}`' for p in sorted(provides[i]))}; "
                         "no consumer"))

    # ---- R4: order-issuer overlap ----------------------------------------------
    sites = order_matrix(bot_type_names)
    loaded_names = set(modules)
    bots_of = {}  # module -> bot types able to run it (armed view)

    def module_bots(name):
        if name in bots_of:
            return bots_of[name]
        insts = modules.get(name, {}).get("insts")
        if insts is None:
            return None
        out = set()
        for _, _, gate in insts:
            if not gate.strip():
                out |= set(bot_types)
                continue
            for alt in split_condition(gate):
                out |= eval_alt([(n, t) for n, t in alt if TERM.fullmatch(t)],
                                scope_armed, bot_types)
        bots_of[name] = out
        return out

    def unseparated_corunners(issuers):
        """Pairs that can co-run (armed view) with NEITHER side claiming via lease/squad —
        the decision-tree duplication the maintainer actually has to review."""
        names = sorted(issuers)
        bad = []
        for i, a in enumerate(names):
            for b in names[i + 1:]:
                ba, bb = module_bots(a), module_bots(b)
                if ba is None or bb is None:
                    continue  # issuer not loaded (helper/unused type) — cannot fire at all
                if not (ba & bb):
                    continue  # gated apart — can never fire on the same bot
                ea, eb = issuers[a], issuers[b]
                if not (ea["lease"] or ea["squad"]) and not (eb["lease"] or eb["squad"]):
                    bad.append((a, b))
        return bad

    overlaps = {}
    for order, issuers in sorted(sites.items()):
        if len(issuers) < 2:
            continue
        coords = []
        for m in sorted(issuers):
            e = issuers[m]
            tag = "lease" if e["lease"] else "squad" if e["squad"] else "no-lease"
            if m not in loaded_names:
                tag += ",not loaded" if m in bot_type_names else ",helper"
            coords.append(f"{m} ({tag})")
        bad = unseparated_corunners(issuers)
        overlaps[order] = {"issuers": issuers, "unseparated": bad}
        verdict = ("; UNSEPARATED co-runners: " + ", ".join(f"{a}+{b}" for a, b in bad)
                   if bad else "; all co-running pairs are lease- or gate-separated")
        findings.append(("R4", "WARN",
                         f"`{order}` — {len(issuers)} issuers: {'; '.join(coords)}{verdict}"))

    # ---- R5: enum reachability -------------------------------------------------
    def src(rel):
        p = REPO / rel
        return p.read_text(encoding="utf-8", errors="replace") if p.is_file() else ""

    squadca = src("OpenRA.Mods.CA/Traits/BotModules/Squads/SquadCA.cs")
    squadmgr = src("OpenRA.Mods.CA/Traits/BotModules/SquadManagerBotModuleCA.cs")
    leases_h = src("OpenRA.Mods.CA/Traits/BotModules/IBotUnitLeases.cs")
    em = re.search(r"enum\s+SquadCAType\s*\{(?P<members>[^}]*)\}", squadca)
    if em:
        members = [x.strip() for x in em.group("members").split(",") if x.strip()]
        in_switch = set(re.findall(r"case\s+SquadCAType\.(\w+)|SquadCAType\.(\w+)\s*=>",
                                   squadca))
        in_switch = {a or b for a, b in in_switch}
        drafted = set(re.findall(r"RegisterNewSquad\([^)]*?SquadCAType\.(\w+)", squadmgr))
        # air-family types arrive through a picked variable; a `return SquadCAType.X` in a
        # helper the manager calls counts as a drafting site for static purposes.
        drafted |= set(re.findall(r"\breturn\s+SquadCAType\.(\w+)", squadmgr))
        for m in members:
            missing = []
            if m not in in_switch:
                missing.append("no initial state in SquadCA")
            if m not in drafted:
                missing.append("never drafted in SquadManagerBotModuleCA")
            if missing:
                findings.append(("R5", "WARN",
                                 f"SquadCAType.{m}: {'; '.join(missing)}"))
    else:
        findings.append(("R5", "WARN", "SquadCAType enum not found in SquadCA.cs"))
    lm = re.search(r"enum\s+BotLeasePurpose\s*\{(?P<members>[^}]*)\}", leases_h)
    if lm:
        members = [x.strip() for x in lm.group("members").split(",") if x.strip()]
        # A purpose counts as claimed when its literal appears in a file that performs a
        # claim operation — helpers like EngineerBotModule.PurposeOf(job) keep the literal
        # off the TryClaim line itself.
        claimed = set()
        for root in CLAIM_ROOTS:
            if not root.is_dir():
                continue
            for p in root.rglob("*.cs"):
                if any(part in ("obj", "bin") for part in p.parts):
                    continue
                text = p.read_text(encoding="utf-8", errors="replace")
                if re.search(r"TryClaim|Preempt|Transfer", text):
                    claimed.update(re.findall(r"BotLeasePurpose\.(\w+)", text))
        for m in members:
            if m not in claimed:
                findings.append(("R5", "WARN",
                                 f"BotLeasePurpose.{m}: no TryClaim/Preempt/Transfer site"))
    else:
        findings.append(("R5", "WARN", "BotLeasePurpose enum not found in IBotUnitLeases.cs"))

    # ---- R6: dead knobs ---------------------------------------------------------
    corpus = cs_corpus()
    dead = []
    for name, defs in classes.items():
        if not name.endswith("Info"):
            continue
        for d in defs:
            p = REPO / d["file"]
            if not any(str(root) in str(p) for root in ORDER_ROOTS):
                continue
            for km in KNOB.finditer(d["body"]):
                fld = km.group("b") or km.group("i") or km.group("s")
                if len(re.findall(rf"\b{re.escape(fld)}\b", corpus.get(p, ""))) > 1:
                    continue
                if any(len(re.findall(rf"\b{re.escape(fld)}\b", t)) for op, t in corpus.items()
                       if op != p):
                    continue
                dead.append((fld, d["file"]))
    if len(dead) > 5:
        findings.append(("R6", "WARN",
                         f"{len(dead)} never-read Info fields — over the 5-hit noise cap; "
                         "check marked needs-improvement, review manually: "
                         + ", ".join(f"`{f}` ({fl})" for f, fl in dead[:10])))
    else:
        for f, fl in dead:
            findings.append(("R6", "WARN", f"`{f}` in {fl}: declared, never read anywhere"))

    # coverage rows: even a clean check states what it looked at
    n_armed = sum(1 for v in reachable_note.values() if v == "armed")
    findings.append(("R1", "ok", f"{n_gated} gated instances checked; {n_armed} dormant "
                                 "on master until their increment arm"))
    findings.append(("R2", "ok", f"{n_targets} switch targets verified"))
    findings.append(("R5", "ok", "SquadCAType/BotLeasePurpose members checked against "
                                 "their switch/draft/claim sites"))
    return {
        "findings": findings, "modules": modules, "provides": provides,
        "consumers": consumers, "bot_interfaces": bot_interfaces, "c1": c1, "c2": c2,
        "sites": sites, "overlaps": overlaps, "reachable_note": reachable_note,
        "n_gated": n_gated, "n_targets": n_targets, "granters": granters,
        "arm_note": arm_note, "loaded_rows": loaded_rows, "rows": rows,
        "bot_type_names": bot_type_names,
    }


# ----------------------------------------------------------------------------- #
# output
# ----------------------------------------------------------------------------- #

def render_report(res):
    L = ["| check | severity | finding |", "|---|---|---|"]
    n_err = n_warn = 0
    order = {"ERROR": 0, "WARN": 1, "ok": 2}
    for check, sev, text in sorted(res["findings"],
                                   key=lambda f: (f[0], order.get(f[1], 3), f[2])):
        if sev == "ERROR":
            n_err += 1
        elif sev == "WARN":
            n_warn += 1
        L.append(f"| {check} | {sev} | {text} |")
    L.append("")
    L.append(f"{n_err} ERROR, {n_warn} WARN")
    return "\n".join(L), n_err, n_warn


def render_doc(res):
    modules = res["modules"]
    L = []
    L.append("# AI dataflow (generated)")
    L.append("")
    L.append("_Generated by `python tools/ai/ai_arch_audit.py --write` from the resolved "
             "`Player`/`World` actors, `tools/ai/increment_switches.yaml` and the C# sources. "
             "**Do not edit by hand**; regenerate. `--check` fails when this file is stale or "
             "an ERROR-class finding exists. Layering follows [`AI_SYNTHESIS.md`]"
             "(AI_SYNTHESIS.md) §7.2; the module map is [`AI_MODULE_MAP.md`](AI_MODULE_MAP.md)._")
    L.append("")
    L.append("Dataflow direction: `PERCEPTION -> SITUATION -> STRATEGY -> EXECUTION` with "
             "`PRODUCTION` beside execution and `SUPPORT`/`TELEMETRY` underneath. A module not "
             "in the tool's `LAYER_OF` table lands in **UNMAPPED** — that is the stale "
             "detection, not a default.")
    L.append("")
    L.append("## Layered dataflow")
    by_layer = collections.defaultdict(list)
    for name, m in modules.items():
        by_layer[LAYER_OF.get(name, "UNMAPPED")].append((name, m))
    for layer in LAYERS + ["UNMAPPED"]:
        ms = sorted(by_layer.get(layer, []))
        L.append("")
        L.append(f"### {layer} ({len(ms)})")
        L.append("")
        if not ms:
            L.append("_none_")
            continue
        L.append("| Module | Asm | Instances (gate) | Provides | Consumes |")
        L.append("|---|---|---|---|---|")
        for name, m in ms:
            inst = "<br>".join(f"`{k}`" + (f" ({g})" if g else "")
                               for _, k, g in m["insts"][:6])
            if len(m["insts"]) > 6:
                inst += f"<br>… {len(m['insts'])} total"
            src = "" if m["source"] else " *(no source)*"
            L.append(f"| `{name}`{src} | {m['asm']} | {inst or '—'} "
                     f"| {', '.join(f'`{i}`' for i in m['impl']) or '—'} "
                     f"| {', '.join(f'`{c}`' for c in m['cons']) or '—'} |")
    L.append("")
    L.append("## Interface seams")
    L.append("")
    L.append("Each `IBot*` seam: who provides it, who consumes it. `STARVED` = consumed but no "
             "loaded provider (R3/C1); `DEAD-END` = provided but no consumer (R3/C2).")
    L.append("")
    L.append("| Interface | Provided by | Consumed by | Status |")
    L.append("|---|---|---|---|")
    provides, consumers = res["provides"], res["consumers"]
    for i in sorted(k for k in set(provides) | set(consumers)
                    if k in res["bot_interfaces"]):
        status = "STARVED" if i in res["c1"] else "DEAD-END" if i in res["c2"] else "ok"
        L.append(f"| `{i}` | {', '.join(f'`{x}`' for x in sorted(provides.get(i, []))) or '—'} "
                 f"| {', '.join(f'`{x}`' for x in sorted(consumers.get(i, []))) or '—'} "
                 f"| {status} |")
    L.append("")
    L.append("## Order-issuer matrix")
    L.append("")
    L.append("`new Order(\"NAME\"` sites under `OpenRA.Mods.Cameo/Traits/BotModules/`, "
             "`OpenRA.Mods.CA/Traits/BotModules/`, `OpenRA.Mods.Fransbot/` (indirect literals "
             "resolved through their helper, e.g. `SendOneRepairer(..., \"RepairBridge\")`). "
             "Squad-state classes fold into `SquadManagerBotModuleCA`. Coordination: `lease` = "
             "file claims via BotUnitLeases; `squad` = squad-owned units; `no-lease` = "
             "decision-tree duplication to review.")
    L.append("")
    L.append("### Overlapped orders (issued by >1 module)")
    L.append("")
    L.append("| Order | Issuers (coordination) | Live overlap |")
    L.append("|---|---|---|")
    for order, o in res["overlaps"].items():
        cells = []
        for m in sorted(o["issuers"]):
            e = o["issuers"][m]
            tag = "lease" if e["lease"] else "squad" if e["squad"] else "no-lease"
            if m not in modules:
                tag += ", not loaded" if m in res["bot_type_names"] else ", helper"
            cells.append(f"`{m}` ({tag})")
        bad = o["unseparated"]
        verdict = ("**unseparated co-runners:** " + ", ".join(f"{a} + {b}" for a, b in bad)
                   if bad else "none — all co-running pairs lease- or gate-separated")
        L.append(f"| `{order}` | {'<br>'.join(cells)} | {verdict} |")
    L.append("")
    L.append("### Single-issuer orders")
    L.append("")
    singles = [(o, next(iter(ms))) for o, ms in res["sites"].items() if len(ms) == 1]
    if singles:
        L.append("| Order | Issuer |")
        L.append("|---|---|")
        for o, m in sorted(singles):
            L.append(f"| `{o}` | `{m}` |")
    else:
        L.append("_none_")
    L.append("")
    L.append("## Findings")
    L.append("")
    table, n_err, n_warn = render_report(res)
    L.append(table)
    L.append("")
    L.append(f"R1 checked {res['n_gated']} gated bot-module instances; R2 checked "
             f"{res['n_targets']} switch targets. Modules marked *(no source)* live in "
             "`engine/` assemblies absent from this worktree — they are listed from yaml "
             "only, and C#-side checks skip them rather than fail.")
    L.append("")
    return "\n".join(L)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    res = audit()
    table, n_err, _ = render_report(res)
    if a.check:
        cur = OUT.read_text(encoding="utf-8") if OUT.is_file() else ""
        stale = cur != render_doc(res)
        if stale:
            print(f"STALE: {OUT.relative_to(REPO)} differs; run with --write")
        print(table)
        return 1 if (stale or n_err) else 0
    if a.write:
        OUT.write_text(render_doc(res), encoding="utf-8", newline="\n")
        print(f"wrote {OUT.relative_to(REPO)}")
    else:
        print(table)
    return 1 if n_err else 0


if __name__ == "__main__":
    sys.exit(main())
