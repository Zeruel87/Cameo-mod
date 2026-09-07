#!/usr/bin/env python3
"""ONE reference unit per source, used ONCE — the maintainer's matching law, solved.

PRIOR ART: `reference_distribution.py` matches by a prefix test on the actor id's last token and
lets every hit vote, which is what the law forbids; `explain_unit.py` shows one unit's working but
assigns nothing. This is the assignment itself. Neither is duplicated — both are imported.

    python tools/balance/assign_references.py                  # the whole corpus, summary
    python tools/balance/assign_references.py --class scout    # one class, reviewable table
    python tools/balance/assign_references.py --write          # save the assignment

⛔ THE LAW (maintainer 2026-09-03), in full, because every line below implements one clause:
  1. role analogies are allowed — matching is not restricted to names;
  2. at most ONE reference unit per source, per Cameo unit;
  3. a reference unit may be used ONCE, ever;
  4. maximise DISTINCT references — where the natural counterpart is taken, find another;
  5. a zero-damage row never matches a combat unit;
  6. among variants, take the one carrying the Cameo unit's IDENTITY;
  7. contests go to FACTION LINEAGE first, then stats;
  8. a collapsed lineage offers ONE reference, not several;
  9. every fit is assigned — no blanks; confidence carries the warning;
 10. MCV / engineer / harvester / support / transports / detectors are EXEMPT; armed APCs are not.
 11. FACTION ROUTING (2026-09-04, after the scout sheet was rejected): a Cameo unit may only see
     the reference FACTIONS its own faction is routed to — `faction_routes.ROUTES`. A faction with
     no route is formula-only rather than matched against a stranger.

WHY GREEDY AND NOT OPTIMAL
--------------------------
Clause 9 says "assign the best remaining candidate", which IS a greedy descent over the score, not
a global optimum — a maximum-weight matching would move a unit off its best reference to improve
someone else's, and the maintainer asked for the opposite. It is also deterministic and explains
itself, which matters when every row is reviewed by hand.
"""
from __future__ import annotations

import argparse
import collections
import difflib
import json
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "audit"))
import class_membership as cm      # noqa: E402
import explain_unit as eu          # noqa: E402
import faction_routes as fr        # noqa: E402
import reference_distribution as rd  # noqa: E402

ROOT = rd.ROOT
syn = rd.syn
OUT = ROOT / "docs" / "balance" / "derived" / "reference_assignment.json"

# ── Clause 10: the exempt roles ───────────────────────────────────────────────────────────────
# ⚠ ARMED APCs STAY IN (maintainer 2026-09-03): the test is whether the actor has a damaging
# armament, not what it is called. An unarmed carrier is exempt; a troop carrier that shoots is a
# combat unit with real HP, DPS and armour.
EXEMPT_WORDS = ("mobileconstructionvehicle", "mcv", "engineer", "harvester", "miner",
                "transport", "carryall", "chinook", "dropship", "hovercraft", "spy", "detector")
EXEMPT_CLASSES = {"support"}


def ledger():
    """{actor: record} across every pack — the only place cost, class and buildability live."""
    out = {}
    for path in sorted((ROOT / "docs" / "balance").glob("*.json")):
        if path.name == "class_anchors.json":
            continue
        try:
            doc = json.loads(path.read_text(encoding="utf-8"))
        except ValueError:
            continue
        for section in (doc.get("sections") or {}).values():
            if isinstance(section, dict):
                for name, rec in section.items():
                    if isinstance(rec, dict):
                        out[name] = rec
    return out


def is_armed(rec):
    for arm in (rec.get("armaments") or []):
        if isinstance(arm, dict) and arm.get("pricing"):
            return True
    return False


def exempt(actor, rec):
    if cm.classify(rec.get("design") or {})[0] in EXEMPT_CLASSES:
        return "support-class"
    tail = actor.split("_")[-1]
    for word in EXEMPT_WORDS:
        if word in tail:
            # the APC carve-out: a carrier that shoots is not exempt
            if word in ("transport", "carryall", "chinook", "dropship", "hovercraft") and is_armed(rec):
                return None
            return f"role-identical ({word})"
    return None


def norm_words(text):
    return [w for w in re.split(r"[^a-z0-9]+", (text or "").lower()) if w]


# ⛔ CAMEO RENAMED UNITS THE WHOLE CORPUS CALLS SOMETHING ELSE, and the docstring below has
# promised "alias matches" since this function was written without any table behind it. The cost
# is invisible and total: `td_gdi_battletank` shares NO word with "GDI Medium Tank", so its name
# score sat at 0.30 — the same score a MOBILE SENSOR ARRAY got — and the sensor array won on
# shape. Every reference for a mainline GDI tank was lost to a naming choice.
#
# Keys are the normalised LAST TOKEN of a Cameo actor id; values are normalised reference names
# it should also be tried as. Add only where the identity is not in dispute — this bypasses the
# name evidence, so a wrong entry is worse than a missing one.
NAME_ALIASES = {
    "battletank": ("mediumtank",),
    "mediumtank": ("battletank",),
}


def name_score(cameo_id, peer_name):
    """0..1. Exact and alias matches sit at the top; a shared distinctive word still counts."""
    tail = syn.norm(cameo_id.split("_")[-1])
    peer = syn.norm(peer_name)
    if not tail or not peer:
        return 0.0
    best = 0.0
    for cand in (tail,) + NAME_ALIASES.get(tail, ()):
        if cand == peer:
            return 1.0
        if cand.startswith(peer) or peer.startswith(cand):
            best = max(best, 0.9)
        # ⚠ CONTAINMENT, NOT JUST PREFIX. A reference row is routinely written with its faction
        # in front — "GDI Medium Tank", "Allied Medium Tank", "Nod Light Tank" — so a prefix test
        # alone misses the exact unit it is looking at. The same defect, in its `startswith` form,
        # is what hides 143 actors from `reference_distribution`. Guarded on length so a short
        # token cannot match half a roster.
        elif len(cand) >= 8 and (cand in peer or peer in cand):
            best = max(best, 0.85)
    ratio = difflib.SequenceMatcher(None, tail, peer).ratio()
    shared = set(norm_words(cameo_id.split("_")[-1])) & set(norm_words(peer_name))
    return max(best, ratio, 0.6 if shared else 0.0)


def pct_rank(value, population):
    """Where a value sits in its OWN population — the only scale-free way to compare costs."""
    if not value or not population:
        return None
    below = sum(1 for v in population if v < value)
    return below / len(population)


# ── The ROLE step, for the thirteen sources that carry no role column ─────────────────────────
# ⛔ NOT AN INVENTED LABEL. Assigning a peer unit a Cameo class would be exactly the "inferred and
# invented data that might be wrong" the maintainer warned about. What IS measurable, and is the
# method's own machinery, is WHERE A UNIT SITS IN ITS OWN ROSTER: a scout is fast, fragile and
# short-ranged relative to its own game, whoever made that game. So the role step compares two
# POSITION VECTORS rather than two labels.
#
#   shape(u) = ( pct_rank(hp), pct_rank(speed), pct_rank(range), pct_rank(dps) )
#              each taken within u's own SOURCE and own TYPE
#   role     = 1 - mean(|shape(cameo) - shape(peer)|)
#
# Dimensionless on both sides, so a 12,500 HP roster and a 205 HP roster are directly comparable —
# the same property that lets the ten relative values work at all.
# ⚠ Where a source DOES carry a real role column (Document 1: Mental Omega, CnC Reloaded), that is
# read rather than derived, and it wins.
SHAPE_FIELDS = ("hp", "speed", "w_range", "w_dps")


def shape_vector(row, pools, key):
    """The unit's position in its own (source, type) population across the role-bearing axes."""
    out = []
    for field in SHAPE_FIELDS:
        out.append(pct_rank(row.get(field), pools.get((key, row.get("type"), field), [])))
    return out


def shape_similarity(a, b):
    """1.0 = same position in its own roster; 0.0 = opposite ends. None if too little overlap."""
    pairs = [(x, y) for x, y in zip(a, b) if x is not None and y is not None]
    if len(pairs) < 2:                      # one axis is not a shape
        return None
    return 1.0 - sum(abs(x - y) for x, y in pairs) / len(pairs)


# ⛔ ORIGINALS OUTRANK VARIANTS (maintainer 2026-09-07). Cameo ships more units than the source
# games do: `ra1_soviets_sovietmammothtank` is RA1's Mammoth, and `ra1_soviets_siegemammothtank`
# is a Cameo ADD-ON built on top of it. Both normalise to something CONTAINING "mammothtank", so
# both land in the same name bucket and the reference went to whichever won on role/cost — which
# was the add-on. The original is the unit the reference IS; the add-on is a unit the reference
# is merely related to, and it must find its own counterpart (Combined Arms fields an Apocalypse
# and an Overlord for exactly this reason) or be placed by rank.
#
# A FACTION word is not a variant: `soviet`/`allied`/`gdi` only say whose Mammoth it is.
FACTION_WORDS = frozenset((
    "soviet", "soviets", "allied", "allies", "gdi", "nod", "japanese", "japan", "german",
    "germany", "russian", "russia", "french", "france", "american", "america", "usa", "asian",
    "latin", "british", "england",
))

# A VARIANT word marks a unit the original game did not ship.
VARIANT_WORDS = frozenset((
    "mkii", "mkiii", "mk2", "mk3", "siege", "heavy", "light", "assault", "advanced", "elite",
    "super", "nuclear", "atomic", "tesla", "laser", "chemical", "flame", "stealth", "sonic",
    "railgun", "rail", "plasma", "cryo", "emp", "veteran", "prototype", "improved", "upgraded",
    "armored", "twin", "multi", "quantum", "hover",
))


def variant_rank(cameo_id, peer_name):
    """1 when the actor is the plain original, 0 when it carries a variant modifier.

    Only consulted when the reference name is a SUBSTRING of the actor's — i.e. when two Cameo
    actors are genuinely competing for the same counterpart. It never suppresses a variant that
    has no competition; it only decides who wins the contest.
    """
    tail = syn.norm(cameo_id.split("_")[-1])
    peer = syn.norm(peer_name)
    if not peer or peer not in tail:
        return 1
    residue = tail.replace(peer, "")
    for w in VARIANT_WORDS:
        if w in residue and w not in FACTION_WORDS:
            return 0
    return 1


def score(cam, rec, peer, cam_cost_pct, peer_cost_pct, home, cam_shape=None, peer_shape=None):
    """The LEXICOGRAPHIC cascade (maintainer: name, then tech tier, then type, then role, then cost).

    Returned as a tuple so Python's own ordering does the cascade — a weighted sum would let a large
    cost advantage outvote a name match, which is exactly what the maintainer ruled against.

    ⛔ TECH TIER IS ABSENT FROM EVERY PEER SOURCE. Cameo carries `design.tech_tier`; no reference
    document has a tier column, so the step cannot be evaluated and is recorded as unavailable
    rather than silently satisfied. It sits in the tuple as a constant so the cascade's SHAPE stays
    honest and the step can be filled the day the data exists.
    """
    if cam["type"] != peer["type"]:
        return None                                   # cross-type is refused (§9 cross-type ruling)
    # ⛔ CLAUSE 5, AND *MISSING* DAMAGE COUNTS AS UNARMED. The old guard read
    # `w_damage is not None and not w_damage`, which fires only on an explicit zero — so a row
    # that carries NO damage field at all sailed past it. Every unarmed reference in the corpus is
    # exactly that shape: OpenRA TD's Mobile Construction Vehicle and Combined Arms' Thief both
    # have `w_damage=None`, and both were duly assigned to armed Cameo units (an MCV to
    # `td_gdi_mammothtankmkiii`, a Thief to `ra1_soviets_sovietrocketsoldier`) on shape similarity
    # alone. A support unit sitting in the same place in its roster as a tank does in ours is a
    # coincidence of distribution, not a counterpart.
    # ⚠ AND "UNARMED" MEANS NO WEAPON AT ALL, NOT A MISSING DAMAGE NUMBER. Refusing on
    # `w_damage` alone threw away Combined Arms' E1 — the RIFLE INFANTRY, the single most
    # important reference unit in the corpus — because its damage does not extract, and handed
    # `ra1_allies_rifleinfantry` a Shock Trooper instead. The two cases are distinguishable:
    #   CA MCV   w_range None  w_reload None  w_burst None   <- genuinely unarmed
    #   CA E1    w_range 1024  w_reload 5     w_burst 1      <- armed, damage failed to extract
    # A row carrying any weapon field is a combat unit whose damage is an extraction gap.
    if is_armed(rec) and not any(peer.get(k) for k in
                                 ("w_damage", "w_range", "w_reload", "w_burst")):
        return None
    # ⛔ THE NAME SCORE IS BUCKETED, AND THAT IS WHAT MAKES THE CASCADE A CASCADE.
    # A lexicographic tuple whose first key is a near-continuous float degenerates into "rank by
    # that key alone": exact ties never happen, so tier, type, role and cost are never consulted.
    # Measured before this fix, 38% of assignments had a role score under 0.5 — the role step was
    # computed and then thrown away. Bucketing restores the maintainer's stated intent: name
    # DOMINATES, and the later keys decide among names of comparable quality.
    #   4 exact · 3 prefix/alias · 2 strong similarity · 1 shares a distinctive word · 0 neither
    raw_name = name_score(cam["id"], peer.get("name", ""))
    name = (4 if raw_name >= 1.0 else 3 if raw_name >= 0.9 else
            2 if raw_name >= 0.75 else 1 if raw_name >= 0.6 else 0)
    TIER_UNAVAILABLE = 0.0
    role = 0.0
    if peer.get("role"):                              # a READ role wins over a derived one
        klass = (cm.classify(rec.get("design") or {})[0] or "")
        role = 1.0 if peer["role"].lower() in klass.replace("_", "") else 0.0
    elif cam_shape is not None and peer_shape is not None:
        sim = shape_similarity(cam_shape, peer_shape)
        if sim is not None:
            role = sim
    cost = 0.0
    if cam_cost_pct is not None and peer_cost_pct is not None:
        cost = 1.0 - abs(cam_cost_pct - peer_cost_pct)
    # home lineage sits directly under the name bucket: it decides CONTESTS (§9.4), which is a
    # stronger claim than shape similarity or cost proximity.
    # `variant_rank` sits directly under the name bucket and above HOME: which unit the reference
    # actually IS outranks which faction lineage it came from.
    return (name, variant_rank(cam["id"], peer.get("name", "")), 1 if home else 0,
            TIER_UNAVAILABLE, round(role, 3), round(cost, 3), round(raw_name, 3))


def assign(only_class=None, routing=True):
    """{cameo id: {source: proposal}}, plus what was skipped and why.

    ⛔ ROUTING IS THE DEFAULT (clause 11). `routing=False` reproduces the pre-2026-09-04 behaviour
    — every source visible to every unit — and exists ONLY so the two can be compared. It is the
    behaviour the maintainer rejected; do not generate a review sheet with it.
    """
    peers, cameo = rd.peer_rows(), rd.cameo_rows()
    # The id-suffix claim (R15 in its second form) stays INACTIVE until the corpus is
    # registered, so it can never fire on a source whose ids nobody has enumerated.
    fr.register_source_ids(peers)
    led = ledger()
    cam_rows = [c for c in cameo if c["id"] in led]

    # exemptions first, so exempt units never consume a reference
    scope, skipped = [], {}
    for c in cam_rows:
        why = exempt(c["id"], led[c["id"]])
        if why:
            skipped[c["id"]] = why
        else:
            scope.append(c)

    # ── clause 11: route, then match ──────────────────────────────────────────────────────────
    # ⚠ A UNIT WITH NO ROUTE LEAVES SCOPE ENTIRELY rather than falling back to open matching.
    # A fallback would put every unrouted faction back where the rejected sheet was, and it would
    # do it invisibly — the rows would look like ordinary proposals. Formula-only is a ruling, so
    # it is recorded as one.
    formula_only = {}
    if routing:
        kept = []
        for c in scope:
            fac = fr.faction_of(c["id"])
            if fac and fr.routes_for(fac):
                kept.append(c)
            else:
                formula_only[c["id"]] = (f"no route for faction {fac!r}" if fac
                                         else "no declared Cameo faction in the id")
        scope = kept

    cam_costs = collections.defaultdict(list)
    for c in scope:
        v = (led[c["id"]].get("cost") or {})
        v = v.get("v") if isinstance(v, dict) else v
        try:
            cam_costs[c["type"]].append(float(v))
        except (TypeError, ValueError):
            pass
    peer_costs = collections.defaultdict(list)
    for p in peers:
        if p.get("cost"):
            peer_costs[(p["source"], p["type"])].append(p["cost"])

    # populations for the shape vectors: per (source, type, field), and Cameo as its own "source"
    pools = collections.defaultdict(list)
    for p in peers:
        for f in SHAPE_FIELDS:
            if p.get(f):
                pools[(p["source"], p["type"], f)].append(p[f])
    for c in scope:
        for f in SHAPE_FIELDS:
            if c.get(f):
                pools[("Cameo", c["type"], f)].append(c[f])
    cam_shapes = {c["id"]: shape_vector(c, pools, "Cameo") for c in scope}
    peer_shapes = {id(p): shape_vector(p, pools, p["source"]) for p in peers}

    by_source = collections.defaultdict(list)
    for p in peers:
        by_source[p["source"]].append(p)

    # the routed pool, computed once per (faction, source) rather than per candidate pair
    routed_pool = {}
    if routing:
        for fac in {fr.faction_of(c["id"]) for c in scope}:
            for src, _toks in fr.routes_for(fac):
                # ⛔ ASK `allows()`. This used to filter inline on `peer_factions(p) & toks`, a
                # SECOND implementation of routing that silently skipped every ruling `allows`
                # carries: R13 exclusivity, R14's universal carve-out, and R15's name claims —
                # so CnC Reloaded's "CABAL's ..." claims and DTA's id-suffix claims were computed
                # and then ignored. `ra1_soviets_rifleinfantry` drew DTA's ALLIED E1A because
                # nothing here ever asked whether the Allies had claimed it.
                routed_pool[(fac, src)] = [p for p in by_source.get(src, ())
                                           if fr.allows(fac, p)]

    result = collections.defaultdict(dict)
    for source, plist in sorted(by_source.items()):
        cands = []
        for c in scope:
            rec = led[c["id"]]
            if only_class and cm.classify(rec.get("design") or {})[0] != only_class:
                continue
            raw = (rec.get("cost") or {})
            raw = raw.get("v") if isinstance(raw, dict) else raw
            try:
                ccost = float(raw)
            except (TypeError, ValueError):
                ccost = None
            cpct = pct_rank(ccost, cam_costs.get(c["type"], []))
            home = source in eu.HOME.get(eu.family_of(c["id"]) or "", [])
            visible = (routed_pool.get((fr.faction_of(c["id"]), source), ()) if routing
                       else plist)
            for p in visible:
                s = score(c, rec, p, cpct,
                          pct_rank(p.get("cost"), peer_costs.get((source, p["type"]), [])), home,
                          cam_shapes.get(c["id"]), peer_shapes.get(id(p)))
                if s:
                    cands.append((s, c["id"], p))
        # clause 9: greedy descent — best remaining wins, both sides then spoken for
        cands.sort(key=lambda t: (t[0], t[1]), reverse=True)
        used_cam, used_peer = set(), set()
        for s, cid, p in cands:
            # ⛔ CLAUSE 3 IS SCOPED PER CAMEO FACTION, not globally (maintainer 2026-09-07).
            # A shared original exists ONCE in a reference roster and is built by BOTH sides:
            # Tiberian Dawn's E1/E2/E3, APC and Harvester belong to GDI *and* Nod. Spending it
            # globally starved the second faction of a unit the source game plainly gives it —
            # OpenRA TD's Rocket Soldier went to `td_nod_rocketsoldier`, so `td_gdi_rocketsoldier`
            # got nothing, and the same rule left the actual RA1 `sovietmammothtank` without the
            # Mammoth it is named after. Within ONE faction the reference is still spent once, so
            # the anti-duplication intent (clause 4, maximise DISTINCT references) is untouched.
            key = (fr.faction_of(cid), p["source"], syn.norm(p.get("name", "")), p.get("id", ""))
            if cid in used_cam or key in used_peer:
                continue
            used_cam.add(cid)
            used_peer.add(key)
            # ⛔ CONFIDENCE MUST SEPARATE "few sources" FROM "weak fit" (§9.7). Collapsing them
            # into one word is how a bad pairing hides behind a LOW that only ever meant thin
            # evidence. This label is about THIS pairing; the source COUNT is reported separately.
            #   STRONG  an exact/alias name, or a real name overlap backed by a matching shape
            #   FAIR    one of the two holds
            #   WEAK    neither — the greedy assigned the best of a bad field (clause 9 forbids
            #           leaving a blank, so the row exists and must announce itself)
            # ⚠ SHAPE-ONLY IS ITS OWN TIER, added after reading the first review sheet. Folding it
            # into FAIR made FAIR the biggest tier (138 against 34 STRONG in `scout`) and hid what
            # those rows are: `asianalliance_asianmilitia` drew "sspy" at name 0.12 / role 0.93,
            # "Rebel" at 0.12, "Fremen" at 0.11. Each sits in the same place in ITS roster as the
            # militia does in ours, which is real evidence for a DISTRIBUTION method and is not a
            # claim that the two are the same unit. The reviewer has to be able to tell them apart.
            # ⚠ POSITIONAL READS OF THE SCORE TUPLE. `variant_rank` was inserted at index 1,
            # which shifted every later key; reading the old offsets turned role into the
            # TIER constant and collapsed the SHAPE tier to nothing (610 -> 0) while WEAK
            # tripled. Keep these in step with `score()`'s return.
            #   0 name · 1 variant · 2 home · 3 tier · 4 role · 5 cost · 6 raw_name
            bucket, role_score = s[0], s[4]
            if bucket >= 3 or (bucket >= 1 and role_score >= 0.75):
                conf = "STRONG"
            elif bucket >= 1:
                conf = "FAIR"          # a real name overlap, shape unconfirmed
            elif role_score >= 0.75:
                conf = "SHAPE"         # same position in its own roster, name says nothing
            else:
                conf = "WEAK"
            # ⛔ STORE THE ROW'S ID. The name alone is not a key: Combined Arms ships TWO rows
            # called "Mammoth Tank" — `HTNK` (Tiberian Dawn's, routed to GDI) and `4TNK` (Red
            # Alert's, routed to the Soviets) — with IDENTICAL hp and cost, so a consumer
            # re-attaching by name and stats cannot tell them apart and silently took the first.
            # That handed `td_gdi_mammothtank` the SOVIET mammoth and, once variant families were
            # expanded, would have grown the wrong family around it.
            result[cid][source] = {"name": p.get("name"), "id": p.get("id"), "score": s,
                                   "hp": p.get("hp"), "cost": p.get("cost"),
                                   "home": bool(s[2]), "raw_name": s[6], "confidence": conf}
    assign.formula_only = formula_only
    return result, skipped, len(scope)


def write_review(klass):
    """The per-class review sheet (§9.9: reviewed one class at a time, matching signed with anchor)."""
    result, _, _ = assign(klass)
    routed_out = dict(getattr(assign, "formula_only", {}))
    led = ledger()
    cam = {c["id"]: c for c in rd.cameo_rows()}
    members = sorted(n for n, u in led.items()
                     if cm.classify(u.get("design") or {})[0] == klass)

    def cost_of(n):
        v = (led[n].get("cost") or {})
        v = v.get("v") if isinstance(v, dict) else v
        try:
            return float(v)
        except (TypeError, ValueError):
            return None

    conf = collections.Counter(m["confidence"] for v in result.values() for m in v.values())
    name_backed = sum(1 for v in result.values()
                      if sum(1 for m in v.values() if m["confidence"] in ("STRONG", "FAIR")) >= 2)
    with_shape = sum(1 for v in result.values()
                     if sum(1 for m in v.values()
                            if m["confidence"] in ("STRONG", "FAIR", "SHAPE")) >= 2)
    L = [f"# `{klass}` — reference assignment for review", "",
         f"**Generated** by `python tools/balance/assign_references.py --review {klass}`. "
         "Regenerates — record decisions and re-run rather than hand-editing.", "",
         "> ⛔ **A PROPOSAL LIST, NOT EVIDENCE.** Until this review is done the class has no grounded",
         "> members and therefore no anchor (`REFERENCE_METHOD.md` §9.9).", "",
         "## §0 — State of the class", "", "| | |", "|---|--:|",
         f"| members | **{len(members)}** |",
         f"| assigned at least one reference | **{len(result)}** |",
         f"| **with ≥2 NAME-backed references** | **{name_backed}** |",
         f"| with ≥2 name-or-shape references | {with_shape} |",
         f"| members with NO reference at all | **{len(members) - len(result)}** |",
         f"| of those, FORMULA-ONLY by routing | **{sum(1 for m in members if m in routed_out)}** |",
         "",
         "⭐ **Routed.** Every proposal below comes from a reference FACTION this unit's Cameo "
         "faction is mapped to (`tools/balance/faction_routes.py`), never from the whole corpus. "
         "A member whose faction has no route is formula-only by ruling, not unmatched by "
         "accident.", "",
         "Confidence: " + " · ".join(f"**{k} {v}**" if k in ("STRONG", "WEAK") else f"{k} {v}"
                                     for k, v in sorted(conf.items())), "",
         "* **STRONG** exact/alias name, or name overlap backed by matching shape",
         "* **FAIR** a real name overlap, shape unconfirmed",
         "* **SHAPE** same position in its own roster; the name says nothing — evidence for a "
         "distribution method, NOT a claim the two are the same unit",
         "* **WEAK** neither; the greedy assigned the best of a bad field", ""]
    missing = [m for m in members if m not in result]
    if missing:
        L += ["⚠ **No reference at all** — formula-only unless the review rescues them:", ""]
        L += [f"* `{m}` — cost {cost_of(m) or '?'}"
              + (f" — ⛔ {routed_out[m]}" if m in routed_out else "")
              for m in missing] + [""]
    for tier_set, title, note in (
            (("STRONG", "FAIR"), "§1 — NAME-backed proposals — confirm or strike", ""),
            (("SHAPE",), "§2 — SHAPE-only proposals", "Same position in its own roster, unrelated "
             "name. Real evidence for the distribution method; your call whether it counts."),
            ):
        L += ["---", "", f"## {title}", ""]
        if note:
            L += [note, ""]
        L += ["| ok? | conf | unit | source | reference unit | name | role | cost |",
              "|:--:|---|---|---|---|--:|--:|--:|"]
        for m in members:
            for src, v in sorted((result.get(m) or {}).items(),
                                 key=lambda kv: (-kv[1]["score"][0], -kv[1]["score"][3])):
                if v["confidence"] in tier_set:
                    home = " **(home)**" if v["home"] else ""
                    L.append(f"| ☐ | {v['confidence']} | `{m}` | {src}{home} | {v['name']} | "
                             f"{v['raw_name']:.2f} | {v['score'][3]:.2f} | {v['score'][4]:.2f} |")
        L.append("")
    # ⛔ WEAK ROWS ARE STRUCK BEFORE REVIEW (maintainer 2026-09-04: "I strike the WEAK rows, you
    # check the rest"). They are the greedy taking the best of a bad field — clause 9 forbids a
    # blank — and reading 62 of them to reject 62 of them is the kind of work that does not survive
    # a long session.
    # ⚠ STRUCK, NOT HIDDEN. They are counted per unit below, so a member whose ONLY proposals were
    # weak is visible as such rather than looking unmatched for no stated reason.
    weak = collections.defaultdict(list)
    for m in members:
        for src, v in (result.get(m) or {}).items():
            if v["confidence"] == "WEAK":
                weak[m].append(f"{src}: {v['name']}")
    if weak:
        L += ["---", "", "## §3 — WEAK proposals — STRUCK, not reviewed", "",
              f"**{sum(len(v) for v in weak.values())} rows across {len(weak)} members** were the "
              "greedy taking the best of a bad field. Struck per the maintainer's ruling so this "
              "sheet only asks about proposals worth judging.", "",
              "⚠ Listed so nothing vanishes silently — a member whose only proposals were weak "
              "should look struck, not unmatched.", "",
              "| unit | struck | what they were |", "|---|--:|---|"]
        for m, items in sorted(weak.items(), key=lambda kv: -len(kv[1])):
            shown = "; ".join(items[:3]) + (" …" if len(items) > 3 else "")
            L.append(f"| `{m}` | {len(items)} | {shown} |")
        L.append("")
        only_weak = [m for m in weak if all(v["confidence"] == "WEAK"
                                            for v in (result.get(m) or {}).values())]
        if only_weak:
            L += ["⛔ **Members left with NOTHING after the strike** — formula-only unless the "
                  "review rescues them:", ""]
            L += [f"* `{m}`" for m in sorted(only_weak)] + [""]

    out = ROOT / "docs" / "balance" / "review" / f"{klass}_references.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(L) + "\n", encoding="utf-8")
    print(f"wrote {out.relative_to(ROOT)}")
    print(f"  members {len(members)} · assigned {len(result)} · "
          f"NAME-backed >=2: {name_backed} · with shape: {with_shape}")
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--class", dest="cls", help="restrict to one class and print its review table")
    ap.add_argument("--write", action="store_true", help="save the assignment as JSON")
    ap.add_argument("--limit", type=int, default=25)
    ap.add_argument("--no-routing", action="store_true",
                    help="⛔ compare only: match against every source, the behaviour the "
                         "maintainer rejected on 2026-09-04")
    ap.add_argument("--review", metavar="CLASS",
                    help="write docs/balance/review/<class>_references.md for maintainer review")
    args = ap.parse_args()

    if args.review:
        return write_review(args.review)
    result, skipped, in_scope = assign(args.cls, routing=not args.no_routing)
    counts = collections.Counter(len(v) for v in result.values())
    fo = getattr(assign, "formula_only", {})
    print(f"routing               : {'FACTION (clause 11)' if not args.no_routing else 'OFF ⛔ the rejected behaviour'}")
    print(f"Cameo actors in scope : {in_scope}   exempt: {len(skipped)}   "
          f"formula-only (no route): {len(fo)}")
    print(f"actors assigned >=1   : {len(result)}")
    print(f"actors reaching the >=2 reference floor: "
          f"{sum(1 for v in result.values() if len(v) >= 2)}")
    print(f"sources per actor     : "
          + ", ".join(f"{k}:{v}" for k, v in sorted(counts.items())))
    conf = collections.Counter(m["confidence"] for v in result.values() for m in v.values())
    total = sum(conf.values())
    print(f"assignment confidence : "
          + ", ".join(f"{k} {v} ({v/total:.0%})" for k, v in
                      sorted(conf.items(), key=lambda kv: -kv[1])))
    for tiers, label in ((("STRONG", "FAIR"), "NAME-backed"),
                         (("STRONG", "FAIR", "SHAPE"), "name or shape")):
        n = sum(1 for v in result.values()
                if sum(1 for m in v.values() if m["confidence"] in tiers) >= 2)
        print(f"⭐ actors with >=2 {label} references: {n}")

    if args.cls:
        print(f"\n── {args.cls} — every member and its one reference per source ──")
        for cid in sorted(result):
            got = result[cid]
            print(f"\n  {cid}   ({len(got)} sources)")
            for src, m in sorted(got.items(), key=lambda kv: -kv[1]["score"][0]):
                flag = "HOME" if m["home"] else "    "
                print(f"     {flag} {m['confidence']:<7}{src[:20]:<22}{str(m['name'])[:26]:<28}"
                      f"name={m['raw_name']:.2f}({m['score'][0]}) "
                      f"role={m['score'][3]:.2f} cost={m['score'][4]:.2f}")
    if args.write:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        OUT.write_text(json.dumps({"assignment": result, "exempt": skipped},
                                  indent=1, sort_keys=True) + "\n", encoding="utf-8")
        print(f"\nwrote {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
