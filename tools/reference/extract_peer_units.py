#!/usr/bin/env python3
"""Extract per-unit stats from a peer OpenRA mod's checkout, for the balance reference corpus.

PRIOR ART: `tools/reference/extract_versus.py` pulls WARHEAD/Versus profiles out of peer mods
(W13, feeding `versus_raw.json` and `aggregate_archetype.py`). This pulls UNIT stats — HP, Cost,
Speed — which that corpus deliberately does not carry. Different axis, no overlap.

    python tools/reference/extract_peer_units.py            # both mods, write the document
    python tools/reference/extract_peer_units.py --mod ca --dry-run

WHY IT EXISTS
-------------
`BALANCE_SYNTHESIS.md` §15 pools every reference source into a per-unit target, and
`ORIGINAL_UNIT_STATS.md` carries Combined Arms and Shattered Paradise as ROLE BANDS only —
"basic rifle 5000", "heavy trooper 7500-9000" — never as per-unit rows. So the two OpenRA peer
crossovers, the mods closest to Cameo in both engine and intent, could not vote on any named
unit. The single CA per-unit figure anywhere in the tree was the Apocalypse at 130,000 HP,
quoted as prose in §16. This closes that gap with real data.

⚠ THE RESOLVER IS NOT OPTIONAL. CLAUDE.md rule 8e forbids hand-parsing yaml, and an OpenRA actor
is a chain of `Inherits:` — `APOC` alone carries no HP; it comes from `^Tank` several levels up.
So this reads through `miniyaml.Ruleset`, which was parameterized by `mod_id` for exactly this
(it defaults to "cameo", so every existing caller is untouched). A regex over `vehicles.yaml`
would have returned nothing for most units and, worse, plausible numbers for a few.

⚠ EACH MOD SETS ITS OWN POWER LEVEL, so raw HP is meaningless across them. Every row is
normalized to that mod's own basic rifleman before it leaves here. Anchors are VERIFIED against
the checkout rather than trusted from a document — and one of them was wrong:
`ORIGINAL_UNIT_STATS.md` states "SP GDI rifle = 15000", but SP's `E1` (Light Infantry) resolves
to **12,500**. The artifact wins.
"""
import argparse
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "audit"))
import miniyaml  # noqa: E402

OUT = ROOT / "docs" / "design" / "ORIGINAL_UNITS_PEER_OPENRA.md"

# ⚠ THE HEALTH TRAIT IS NOT ALWAYS CALLED `Health`. Crystallized Nexus ships its own
# `CNHealth` (in `.modsdk/OpenRA.Mods.CN`), so a reader hardcoding `Health` finds 610 actors and
# ZERO units with hit points — an empty result that looks like "this mod has no data" rather than
# like a bug. Every peer therefore declares which traits carry its stats.
DEFAULT_TRAITS = {"health": ("Health",), "cost": ("Valued",),
                  "speed": ("Mobile", "Aircraft")}

# ── Unit type ────────────────────────────────────────────────────────────────────────────────
# Per-type distributions are the whole point of the distribution model: a Cameo vehicle must be
# compared against a peer's VEHICLES, not against its whole roster. Every OpenRA mod names its
# production queues differently — RA is plain (`Vehicle`), CA suffixes them (`VehicleSQ,
# VehicleMQ`), RV qualifies them by faction (`Vehicle.Civilian`) — so the queue string is matched
# by TOKEN rather than by equality, and traits are the fallback when a unit has no queue at all.
TYPE_TOKENS = [("aircraft", "aircraft"), ("infantry", "infantry"), ("cyborg", "infantry"),
               ("vehicle", "vehicle"), ("tank", "vehicle"), ("ship", "ship"), ("naval", "ship"),
               ("defense", "defense"), ("building", "building"), ("structure", "building")]


# ── Weapon extraction: the SCALE-FREE half ───────────────────────────────────────────────────
# Range, reload, burst, burst delays and raw damage need no armor taxonomy, so they are extracted
# now. Armor-aware effective DPS is deliberately NOT here: measured across the 13 peers there are
# 76 distinct Versus tags and only FIVE (None, Light, Heavy, Wood, Concrete) are shared by six or
# more mods. Generals Alpha declares 37, several of them per-unit
# (`vehicle.battle_bus.crate-1`); OpenRA Dune II declares none at all; Dune 2000 ships both
# `none` and `None`. A universal mapping is therefore not derivable from the data and must be
# hand-authored with per-source confidence — that is the next layer, and inventing it here would
# be fabricating a taxonomy.
#
# ⚠ `Versus` is a NODE WITH AN EMPTY VALUE whose CHILDREN are the armor rows. A probe using
# `node.get("Versus")` reads the empty value and concludes the mod has no Versus at all — which
# is exactly the wrong answer, and is how this pass nearly recorded "peers expose no Versus".
ARMOR_MAP_FILE = ROOT / "docs" / "reference" / "peer_armor_map.yaml"
_ARMOR_MAP = None


def armor_map(source_label):
    """{peer tag: Cameo ladder} plus the source's confidence, from the hand-authored table.

    Loaded from data rather than hardcoded because every entry is a judgement that has to stay
    inspectable. Only `high` and `medium` sources vote on armor-aware damage; `low` is recorded
    (E2140's four role tags carry no within-ladder information, so admitting them would flatten
    every ladder they touch) and `exclude` cannot participate at all.
    """
    global _ARMOR_MAP
    if _ARMOR_MAP is None:
        try:
            import yaml
            _ARMOR_MAP = yaml.safe_load(ARMOR_MAP_FILE.read_text(encoding="utf-8"))
        except Exception:
            _ARMOR_MAP = {"sources": {}}
    entry = (_ARMOR_MAP.get("sources") or {}).get(source_label) or {}
    return (entry.get("map") or {}), entry.get("confidence", "exclude")


def weapon_stats(rules, node, source_label=""):
    """Primary armament's scale-free weapon numbers, resolved through the weapon chain."""
    weapons = [c.get("Weapon") for c in node.children
               if c.key.split("@")[0] == "Armament" and c.get("Weapon")]
    if not weapons:
        return {}
    try:
        w = rules.resolve_weapon(weapons[0])
    except Exception:
        return {}
    if w is None:
        return {}

    def num(v):
        if v is None:
            return None
        v = str(v).strip()
        # OpenRA ranges are cell distances: "6c0" = 6 cells, "6c512" = 6.5 cells.
        if "c" in v:
            a, _, b = v.partition("c")
            try:
                return int(a) * 1024 + int(b or 0)
            except ValueError:
                return None
        try:
            return float(v)
        except ValueError:
            return None

    # ⚠ `Versus` is a NODE whose VALUE is empty and whose CHILDREN are the armor rows. Reading
    # `warhead.get("Versus")` returns the empty value and looks like "this mod has no Versus" —
    # which is how the first sweep of this corpus reported 0 for all 13 mods.
    amap, conf = armor_map(source_label)
    damage = 0
    mains = 0
    ladder_hits = {}
    for c in w.children:
        if not c.key.startswith("Warhead"):
            continue
        d = num(c.get("Damage"))
        if d and d > 0:
            damage += d
            mains += 1
            for x in c.children:
                if x.key != "Versus":
                    continue
                for row in x.children:
                    ladder = amap.get(row.key)
                    v = num(row.value)
                    if ladder and v is not None:
                        ladder_hits.setdefault(ladder, []).append(v)
    burst = num(w.get("Burst")) or 1
    reload_delay = num(w.get("ReloadDelay"))
    delays = [num(x) for x in (w.get("BurstDelays") or "").replace(",", " ").split() if x]
    delays = [d for d in delays if d]
    burst_time = sum(delays) if delays else (burst - 1) * 5   # OpenRA's default BurstDelays is 5
    cycle = (reload_delay or 0) + burst_time
    # Effective damage vs a LADDER is the mean of that ladder's Versus rows, as a fraction. A
    # peer that expresses the whole AIR ladder with one `Aircraft` tag contributes one number to
    # AIR — correct, because that is the entire precision that source has. A tag absent from the
    # weapon's Versus block means OpenRA's default of 100%, so a missing ladder is left as None
    # rather than 0: absent is not immune.
    eff = {}
    if conf in ("high", "medium"):
        for ladder, vals in ladder_hits.items():
            eff[f"eff_vs_{ladder}"] = sum(vals) / len(vals) / 100.0
    return {"weapon": weapons[0], "w_range": num(w.get("Range")), "armor_conf": conf, **eff,
            "w_min_range": num(w.get("MinRange")), "w_damage": damage or None,
            "w_mains": mains or None, "w_burst": burst,
            "w_reload": reload_delay,
            # Sustained output over the full cycle, in damage per tick. Burst is inside the
            # cycle, not on top of it — a 4-round burst with a 40-tick reload is not 4x a
            # single shot, which is the most common way this number gets inflated.
            "w_dps": ((damage * burst) / cycle) if (damage and cycle) else None}


def unit_type(node):
    """infantry | vehicle | aircraft | ship | defense | building | other."""
    queue = ""
    for c in node.children:
        if c.key.split("@")[0] == "Buildable":
            queue = (c.get("Queue") or "") + " " + (c.get("BuildAtProductionType") or "")
    q = queue.lower()
    for token, kind in TYPE_TOKENS:
        if token in q:
            return kind
    traits = {c.key.split("@")[0] for c in node.children}
    if "Aircraft" in traits:
        return "aircraft"
    if "Mobile" in traits:
        return "vehicle"          # an unqueued mobile actor; infantry is nearly always queued
    if "Building" in traits:
        return "building"
    return "other"


def turn_speed(node):
    """Turn rate and whether it comes from a TURRET.

    Cameo's turn law is relative to speed and keyed on the turret: a turreted ground unit turns at
    Speed/5 while a turretless one turns at 2xSpeed/5, and aircraft split again (helicopters and
    spaceships Speed/5, planes Speed/15). A peer's raw TurnSpeed is therefore only meaningful
    next to its speed and its turret state, so both travel together.
    """
    turreted = any(c.key.split("@")[0] == "Turreted" for c in node.children)
    for names in (("Turreted",), ("Mobile",), ("Aircraft",)):
        v = trait(node, names, "TurnSpeed")
        if v:
            try:
                return int(str(v)), turreted
            except ValueError:
                return None, turreted
    return None, turreted

# mod_id -> dict describing the peer:
#   label     human name used as the source label in the synthesis
#   root      checkout candidates; the FIRST whose mods/<mod_id>/mod.yaml exists wins
#   mod_id    the directory under mods/ (defaults to the key)
#   rifle     actor id of the basic rifleman — the mod's own 1.00x anchor
#   expect    documented anchor HP, checked against the checkout and REPORTED when it differs
#   traits    overrides for DEFAULT_TRAITS
PEERS = {
    "ca": {"label": "Combined Arms", "rifle": "E1", "expect": 5000,
           "root": ["/home/user/inq8/camod", "~/Documents/GitHub/CAmod", "../CAmod"]},
    "sp": {"label": "Shattered Paradise", "rifle": "E1", "expect": 12500,
           "root": ["/home/user/abrandau/shattered-paradise-sdk",
                    "~/Documents/GitHub/Shattered-Paradise-SDK",
                    "../Shattered-Paradise-SDK"]},
    # CN's basic rifleman is GASOL (the GDI "Marine", 125 HP / 120 cr) — it ships no E1, and its
    # HP scale is classic-Westwood-sized rather than OpenRA-sized, which is exactly why the
    # per-mod rifle normalization exists.
    "cn": {"label": "Crystallized Nexus", "rifle": "GASOL", "expect": 125,
           "traits": {"health": ("CNHealth", "Health")},
           # CN keeps its mod under .modsdk/, not at the checkout root.
           "root": ["/home/user/dogyaut/crystallized-nexus/.modsdk",
                    "~/Documents/GitHub/crystallized-nexus/.modsdk",
                    "~/Downloads/crystallized-nexus-main/.modsdk"]},
    # ⚠ FRACTURED REALMS IS DECLARED BUT CANNOT VOTE, and that is a finding, not a gap in this
    # tool. It resolves cleanly — 488 actors, 191 weapons — but only 23 actors carry BOTH Health
    # and Valued, and 18 of those are buildings (walls, gates, power plants, a forge). The mobile
    # remainder is a dozer, a transport ship, an MCV, one bomber and one scout. There is no basic
    # rifleman, so there is nothing to normalize against, and inventing an anchor would fabricate
    # every ratio derived from it. Last pushed 2023-10; it reads as an early prototype rather
    # than a balanced mod. Kept here so the check is recorded and re-runs automatically if the
    # mod ever grows a roster.
    "fnw": {"label": "Fractured Realms", "rifle": "e1", "expect": None,
            "root": ["/home/user/logue-yne/fractured-realms",
                     "~/Documents/GitHub/Fractured-Realms", "../Fractured-Realms"]},
    "rv": {"label": "Romanov's Vengeance", "rifle": "e1", "expect": 12500,
           "root": ["/home/user/mustaphatr/romanovs-vengeance",
                    "~/Documents/GitHub/Romanovs-Vengeance", "../Romanovs-Vengeance"]},
    # C&C Generals in OpenRA. §15.5 rules that SAGE economies do NOT map to credits, so its COST
    # column is identity-only and must not be read as a price; HP normalized to its own basic
    # infantry is still comparable. Its anchor is `infantry.conscript` (12,000 HP / 100) — there
    # is no `E1` in this universe.
    "gen": {"label": "Generals Alpha", "rifle": "infantry.conscript", "expect": 12000,
            "root": ["/home/user/mustaphatr/generals-alpha",
                     "~/Documents/GitHub/Generals-Alpha", "../Generals-Alpha"]},
    # The four OpenRA BASE mods — the original games as the engine ships them. They are the
    # closest thing to a neutral reading of Westwood's own balance, and `versus_raw.json` already
    # samples all four for warheads; these are their unit stats.
    "ra": {"label": "OpenRA Red Alert", "rifle": "E1", "expect": 5000,
           "root": ["/home/user/openra/openra", "~/Documents/GitHub/OpenRA", "../OpenRA", "~/Documents/GitHub/cameo-engine"]},
    "cnc": {"label": "OpenRA Tiberian Dawn", "rifle": "E1", "expect": 5000,
            "root": ["/home/user/openra/openra", "~/Documents/GitHub/OpenRA", "../OpenRA", "~/Documents/GitHub/cameo-engine"]},
    "ts": {"label": "OpenRA Tiberian Sun", "rifle": "E1", "expect": 12500,
           "root": ["/home/user/openra/openra", "~/Documents/GitHub/OpenRA", "../OpenRA", "~/Documents/GitHub/cameo-engine"]},
    "d2k": {"label": "OpenRA Dune 2000", "rifle": "light_inf", "expect": 6000,
            "root": ["/home/user/openra/openra", "~/Documents/GitHub/OpenRA", "../OpenRA", "~/Documents/GitHub/cameo-engine"]},

    # ── Found 2026-08-30 by searching GitHub's `topic:openra`, all cloned from source ────────
    # `e1` (G.I.) and `e2` (Conscript) are both 125 HP in the RA2 family; `e1` is used as the
    # anchor throughout for consistency with the rest of the corpus.
    "ra2": {"label": "OpenRA RA2 official", "rifle": "e1", "expect": 125,
            "root": ["/home/user/openra/ra2", "~/Documents/GitHub/ra2", "../ra2"]},
    "yr": {"label": "Yuri's Revenge on OpenRA", "rifle": "e1", "expect": 125,
           "root": ["/home/user/cookgreen/yuris-revenge",
                    "~/Documents/GitHub/Yuris-Revenge", "../Yuris-Revenge"]},
    # Valiant Shades runs on the Attacque Supérior fork — the same OpenRA.Mods.AS that Cameo's
    # own engine carries — so its power level is the closest of any peer to Cameo's own.
    "ra2vsh": {"label": "Valiant Shades", "rifle": "e1", "expect": 65000,
               "root": ["/home/user/as/valiantshades",
                        "~/Documents/GitHub/ValiantShades", "../ValiantShades"]},
    # OpenHV is original sci-fi IP rather than a C&C crossover, so it shares no unit NAMES with
    # Cameo and will rarely match by name. It is kept for the role/spread reading: a from-scratch
    # OpenRA roster balanced without Westwood's legacy numbers is a genuinely independent voice.
    "hv": {"label": "OpenHV", "rifle": "RIFLEMAN", "expect": 15000,
           "root": ["/home/user/openhv/openhv", "~/Documents/GitHub/OpenHV", "../OpenHV"]},
    "d2": {"label": "OpenRA Dune II", "rifle": "light_inf", "expect": 20,
           "root": ["/home/user/openra/d2", "~/Documents/GitHub/d2", "../d2"]},
    # Earth 2140. §15.5: Earth economies do NOT map to credits, so its cost column is
    # identity-only; HP still normalizes against its own basic infantry.
    "e2140": {"label": "OpenE2140", "rifle": "ed_infantry_a01", "expect": 28,
              "root": ["/home/user/opene2140/opene2140",
                       "~/Documents/GitHub/OpenE2140", "../OpenE2140"]},
}


def find_checkout(cands, mod_id):
    """First candidate that actually holds this mod's manifest.

    Checking `mods/<mod_id>/mod.yaml` rather than just `mods/` matters: Crystallized Nexus keeps
    its mod under `.modsdk/`, so the repository root has no `mods/` at all.
    """
    for c in cands:
        p = pathlib.Path(c).expanduser()
        if (p / "mods" / mod_id / "mod.yaml").is_file():
            return p
    return None


def trait(node, names, field):
    """First value of `field` on any of `names` (matching `Name` or `Name@suffix`)."""
    if isinstance(names, str):
        names = (names,)
    for child in node.children:
        if child.key.split("@")[0] in names:
            v = child.get(field)
            if v:
                return v
    return None


def traits_for(spec):
    t = dict(DEFAULT_TRAITS)
    t.update(spec.get("traits") or {})
    return t


def load_fluent(root, mod_id):
    """{key: text} from the mod's .ftl files.

    SP and CN name their units by fluent key rather than literally, and the two use different
    Fluent shapes — SP writes `e1-name = Light Infantry` on one line, CN writes an ATTRIBUTE
    block:

        actor-gasol =
            .name = Marine
            .description =
            General-purpose infantry.

    so both forms are read. Getting this wrong is not cosmetic: the display name is what matches
    a peer unit to a Cameo actor, and an unresolved `actor-gasol.name` matches nothing.
    """
    out = {}
    for f in (root / "mods" / mod_id).rglob("*.ftl"):
        text = f.read_text(encoding="utf-8", errors="replace")
        key = None
        for line in text.splitlines():
            m = re.match(r"^([A-Za-z0-9_.-]+)\s*=\s*(.*)$", line)
            if m:
                key = m.group(1)
                if m.group(2).strip():
                    out[key] = m.group(2).strip()
                continue
            a = re.match(r"^\s+\.([A-Za-z0-9_-]+)\s*=\s*(.+)$", line)
            if a and key:
                out[f"{key}.{a.group(1)}"] = a.group(2).strip()
    return out


def unit_name(actor_id, node, fluent):
    """Display name, tried in the order that actually resolves across these mods."""
    raw = trait(node, "Tooltip", "Name") or ""
    if raw in fluent:
        return fluent[raw]
    # OpenRA's convention when a Tooltip carries no explicit Name.
    for guess in (f"actor-{actor_id.lower()}.name", f"{actor_id.lower()}-name"):
        if guess in fluent:
            return fluent[guess]
    return raw or actor_id


def declared_factions(rules):
    """{internal name: is a PLAYABLE subfaction} from the mod's own World actor.

    ⛔ THE WHITELIST HAS TO COME FROM THE MOD, NOT FROM A GUESS. Faction tokens sit in the same
    `Prerequisites` string as unit tokens — Combined Arms writes `~vehicles.soviet` beside
    `~vehicles.mtnk`, and `mtnk` is a Medium Tank, not a faction. A regex over `word.word` tagged
    only 20% of CA's roster and would have invented factions out of unit names. Every OpenRA mod
    declares its factions on `World`, so that list is read and used as the filter.

    ⚠ `Selectable: False` marks a PARENT faction — `allies`, `soviet`, `gdi` — that groups the
    playable subfactions beneath it. Both are kept: the parent is what a Cameo faction maps to
    (RA2 Allies), the subfaction is what a unit is usually tagged with (england, france, usa).
    """
    world = rules.resolve("World") or rules.resolve("world")
    if world is None:
        return {}
    out = {}
    for c in world.children:
        if c.key == "Faction" or c.key.startswith("Faction@"):
            d = {k.key: k.value for k in c.children}
            name = (d.get("InternalName") or c.key.split("@")[-1] or "").strip().lower()
            if not name or name == "random":
                continue
            # ⭐ `random-allies` DECLARES that `allies` is a real faction GROUP. Romanov's Vengeance
            # names 31 subfactions (america, england, russia, cuba…) and gates its units on the
            # PARENT (`Infantry.Allies`, `Infantry.Soviets`) — parents that appear nowhere else in
            # the mod except as these random-* entries. Reading them recovers the grouping a Cameo
            # faction actually maps to, which is RA2 Allies rather than RA2 France.
            if name.startswith("random-"):
                out[name[len("random-"):]] = True
            else:
                out[name] = (d.get("Selectable", "") or "").strip().lower() != "false"
    return out


# How many prerequisite hops to follow when resolving a faction. 2 covers the real chains
# (unit -> barracks -> `structures.<faction>`); deeper mostly reaches shared infrastructure and
# risks attaching a faction through a building both sides can build.
PREREQ_DEPTH = 2


def _faction_tokens(text, known):
    """The faction tokens inside one comma-separated Queue/Prerequisites string."""
    found = set()
    for chunk in (text or "").split(","):
        tok = chunk.strip().lstrip("~!").strip().lower()
        # `Infantry.Allies` -> allies · `~infantry.england` -> england · bare `yuri` -> yuri
        for part in (tok.split(".")[-1], tok):
            if not part or part.isdigit():
                continue
            if part in known:
                found.add(part)
                continue
            # ⚠ Mods abbreviate their own faction names inconsistently: Shattered Paradise
            # DECLARES `mut`, `cab`, `scr` and then gates units on `mutant`, `cabal`, `scrin`.
            # A prefix match in either direction reconciles them; 3 characters is the floor so
            # short unit tokens cannot masquerade as a faction.
            for k in known:
                if len(part) >= 3 and len(k) >= 3 and (part.startswith(k) or k.startswith(part)):
                    found.add(k)
                    break
    return found


def _buildable(node):
    return next((c for c in node.children
                 if c.key == "Buildable" or c.key.startswith("Buildable@")), None)


def factions_of(node, known, rules=None, _depth=PREREQ_DEPTH, _seen=None):
    """The faction tokens an actor is gated on, filtered by what the mod actually declares.

    ⛔ THE FACTION IS OFTEN ONE HOP AWAY, IN THE PREREQUISITE BUILDING. OpenRA gates most infantry
    on a barracks rather than on a faction:

        E2 (Grenadier):  Prerequisites: ~barr, ~techlevel.infonly
        BARR:            Prerequisites: anypower, ~structures.soviet, ~techlevel.infonly

    Reading only the unit's own line finds no faction and returns nothing, which is why infantry
    was the WORST-tagged type in the corpus at 25% against defence's 80% — and why
    `ra1_soviets` routed to ZERO reference infantry while OpenRA Red Alert plainly ships Soviet
    infantry. `heavy_sniper`, a SIGNED class, had both its members ground to nothing for exactly
    this reason.

    ⚠ Depth is capped at `PREREQ_DEPTH`. Following the chain forever eventually reaches
    infrastructure both sides build (`anypower` -> any power plant), and a faction attached
    through shared infrastructure is worse than no faction at all.

    `rules` is optional so existing callers and tests keep working; without it the resolution is
    the original single-level read.
    """
    b = _buildable(node)
    if b is None:
        return []
    found = set()
    for field in ("Queue", "Prerequisites"):
        found |= _faction_tokens(b.get(field), known)
    # Already decided at this level — do not dilute a direct gate with an inherited one.
    if found or rules is None or _depth <= 0:
        return sorted(found)
    _seen = set() if _seen is None else _seen
    for chunk in (b.get("Prerequisites") or "").split(","):
        tok = chunk.strip().lstrip("~!").strip()
        if not tok or tok.lower() in _seen:
            continue
        _seen.add(tok.lower())
        key = rules._actor_ci.get(tok.lower())
        if not key:
            continue
        try:
            parent = rules.resolve(key)
        except Exception:                       # a prerequisite that does not resolve is not fatal
            continue
        found |= set(factions_of(parent, known, rules, _depth - 1, _seen))
    return sorted(found)


def extract(mod_id):
    spec = PEERS[mod_id]
    label, cands, rifle_id, expect = spec["label"], spec["root"], spec["rifle"], spec["expect"]
    T = traits_for(spec)
    root = find_checkout(cands, mod_id)
    if root is None:
        return label, None, f"no checkout found (looked in {', '.join(cands)})"
    rules = miniyaml.Ruleset(root, mod_id)
    fluent = load_fluent(root, mod_id)
    known_factions = declared_factions(rules)

    key = rules._actor_ci.get(rifle_id.lower())
    if not key:
        return label, None, f"rifle actor {rifle_id} not present"
    rifle = rules.resolve(key)
    rhp = trait(rifle, T["health"], "HP")
    rcost = trait(rifle, T["cost"], "Cost")
    if not rhp:
        return label, None, f"{rifle_id} has no resolvable HP"
    rhp, rcost = int(rhp), int(rcost or 0)
    note = ""
    if expect and rhp != expect:
        note = (f"⚠ documented anchor was {expect:,}; the checkout resolves **{rhp:,}** — "
                "the artifact wins")

    rows = []
    for actor in sorted(rules.actors):
        if actor.startswith(("^", "-")):
            continue
        node = rules.resolve(actor)
        if node is None:
            continue
        if not any(c.key.split("@")[0] == "Buildable" for c in node.children):
            continue
        hp = trait(node, T["health"], "HP")
        if not hp:
            continue
        cost = trait(node, T["cost"], "Cost")
        speed = trait(node, T["speed"], "Speed")
        # BuildLimit marks a mod's one-off epic/hero. It is emitted rather than dropped here so
        # the reference document stays a COMPLETE record of each mod; the distribution engine
        # filters it, where the choice is visible and auditable.
        limit = trait(node, ("Buildable",), "BuildLimit")
        ts, turreted = turn_speed(node)
        wep = weapon_stats(rules, node, label)
        rows.append({
            "id": actor, "name": unit_name(actor, node, fluent),
            "type": unit_type(node), "turn_speed": ts, "turreted": turreted,
            # ⭐ THE FACTION COLUMN (maintainer 2026-09-04). Reference routing needs it: an Asian
            # Alliance unit may only draw on Mental Omega China, which is what stops
            # "Animal Alligator" from ever being a candidate.
            "faction": "/".join(factions_of(node, known_factions, rules)) or "",
            "limit": int(limit) if (limit and str(limit).strip().isdigit()) else None,
            **wep,
            "hp": int(hp), "cost": int(cost) if cost else None,
            "speed": int(speed) if speed else None,
            "x_hp": int(hp) / rhp,
            "x_cost": (int(cost) / rcost) if (cost and rcost) else None,
        })
    return label, {"root": root, "rifle": (rifle_id, rhp, rcost), "rows": rows,
                   "note": note}, None


def main():
    # ⚠ A LABEL MUST NOT CONTAIN "(". Document 5's section headings are `## <label>  (N units)`,
    # and the synthesis reads them back with `line[3:].split("(")[0]` — so a parenthesised label
    # is TRUNCATED on the way in. That has bitten twice: "Romanov's Vengeance (live)" silently
    # failed to match a de-duplication rule, and "Yuri's Revenge (OpenRA)" would have collapsed
    # into Document 1's separate "Yuri's Revenge" source, merging two different mods without a
    # word. Fail loudly here instead.
    bad = {k: v["label"] for k, v in PEERS.items() if "(" in v["label"]}
    if bad:
        raise SystemExit(f"peer labels must not contain '(' — they are truncated by the "
                         f"Document 5 heading parser: {bad}")

    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--mod", choices=sorted(PEERS), action="append")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    out = ["# Original units — OpenRA peer crossovers (Combined Arms, Shattered Paradise)", "",
           "_AUTO-GENERATED by `tools/reference/extract_peer_units.py` from each mod's own "
           "checkout, read through `miniyaml.Ruleset` so the `Inherits:` chains actually "
           "resolve. Do not hand-edit._", "",
           "Companion to [`ORIGINAL_UNITS_RAW.md`](ORIGINAL_UNITS_RAW.md) (the RA2 family) and "
           "[`ORIGINAL_UNIT_STATS.md`](ORIGINAL_UNIT_STATS.md) (the source games). Those two "
           "carry CA and SP as ROLE BANDS only, so before this document neither could vote on a "
           "named unit in the synthesis.", "",
           "**Each mod sets its own power level**, so `×rifle` is the only comparable column. "
           "Anchors are verified against the checkout, never trusted from a document.", ""]

    total = 0
    for mod_id in (args.mod or sorted(PEERS)):
        label, data, err = extract(mod_id)
        if err:
            print(f"{label}: {err}")
            out += [f"## {label}", "", f"⚠ not extracted — {err}", ""]
            continue
        rid, rhp, rcost = data["rifle"]
        total += len(data["rows"])
        print(f"{label}: {len(data['rows'])} buildable units "
              f"(rifle {rid} = {rhp:,} HP / {rcost} cr){'  ' + data['note'] if data['note'] else ''}")
        out += [f"## {label}  ({len(data['rows'])} buildable units)", "",
                f"Checkout: `{data['root']}` · rifle anchor **`{rid}` = {rhp:,} HP / "
                f"{rcost} credits = 1.00×**"]
        if data["note"]:
            out += ["", data["note"]]
        out += ["", "| id | unit | type | faction | HP | ×rifle | Cost | ×rifle cost | Speed | "
                "Turn | Turret | Limit | Range | Dmg | Burst | Reload | DPS | vsINF | vsVEH | "
                "vsAIR | vsBLD |",
                "|---|---|---|---|--:|--:|--:|--:|--:|--:|:-:|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|"]
        for r in sorted(data["rows"], key=lambda x: -x["x_hp"]):
            xc = f"{r['x_cost']:.2f}" if r["x_cost"] else "—"
            cost = f"{r['cost']:,}" if r["cost"] else "—"
            spd = r["speed"] if r["speed"] else "—"
            out.append(f"| `{r['id']}` | {r['name']} | {r['type']} | "
                       f"{r.get('faction') or '—'} | {r['hp']:,} | "
                       f"{r['x_hp']:.2f} | {cost} | {xc} | {spd} | "
                       f"{r['turn_speed'] if r['turn_speed'] else '—'} | "
                       f"{'Y' if r['turreted'] else 'n'} | "
                       f"{r['limit'] if r['limit'] else '—'} | "
                       + " | ".join(
                           (f"{r.get(k):,.0f}" if isinstance(r.get(k), (int, float)) else "—")
                           for k in ("w_range", "w_damage", "w_burst", "w_reload", "w_dps"))
                       + " | " + " | ".join(
                           (f"{r.get(k):.2f}" if isinstance(r.get(k), (int, float)) else "—")
                           for k in ("eff_vs_INF", "eff_vs_VEH", "eff_vs_AIR", "eff_vs_BLD"))
                       + " |")
        out.append("")

    if args.dry_run:
        print(f"DRY RUN: {total} rows, nothing written")
        return 0
    OUT.write_text("\n".join(out) + "\n", encoding="utf-8")
    print(f"wrote {OUT.relative_to(ROOT)} ({total} rows)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
