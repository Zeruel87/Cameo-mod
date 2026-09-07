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

# ── Clause 10: the CHASSIS-ONLY roles ─────────────────────────────────────────────────────────
# ⚠ ARMED APCs STAY IN (maintainer 2026-09-03): the test is whether the actor has a damaging
# armament, not what it is called. An unarmed carrier is chassis-only; a troop carrier that shoots
# is a combat unit with real HP, DPS and armour.
#
# ⭐ REVISED 2026-09-07 (maintainer): these roles are no longer SKIPPED, they are CHASSIS-ONLY.
#     "For our support units and mcv or harvesters we just need to extract HP and Speed
#      because that's all they need since they don't have a weapon"
# Skipping them entirely left 122 unarmed actors with no reference at all, and it showed: every
# Mobile Construction Vehicle in the game is 300,000 HP / speed 75 and every Tiberium Harvester
# 150,000 / 60, across more than twenty factions, because nothing was ever measured against them.
# They now match and vote like anything else — on HP and SPEED alone, since they have no weapon
# to compare. The RA2 War Miner and its armed kin are not affected: `is_armed` already keeps a
# support unit that shoots out of this list entirely.
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


def has_any_armament(rec):
    """Does this actor carry a weapon of ANY kind — priced or not?

    ⛔ NOT THE SAME QUESTION AS `is_armed`, and conflating them cost the V3 its references.
    `is_armed` asks whether an armament is PRICED, which is what clause 5 needs. 79 actors carry
    an armament the ledger marks `pricing: False` — engineer defuse kits and kamikaze target
    designators, which really are not weapons, but also `japan_waveforceartillery`,
    `asianalliance_chaostower` and `ra2_soviets_v3rocketlauncher`, which plainly are.

    The unarmed guard must use THIS test. Asking `is_armed` there declared the V3 Rocket Launcher
    unarmed and refused it every armed peer, so it lost `V3` in five separate sources at once and
    fell back on a drone pile, a Lynx and a Hind. A guard that is wrong in the RESTRICTIVE
    direction deletes correct candidates from the pool — the failure this whole cascade is made
    of — so where the two tests disagree, this one lets the actor through.
    """
    return bool(rec.get("armaments"))


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
# ⚠ AN ALIAS IS FOR A UNIT THE SOURCES CALL SOMETHING ELSE, never for two DIFFERENT units.
# The GDI rocket launcher is `MSAM` in DTA ("Rocket Launcher"), `MSAM` in OpenRA TD ("Rocket
# Launcher") and `MSAM` in Combined Arms ("MLRS"). Cameo calls it `td_gdi_mlrs` — and `MLRS` is
# the id all three sources use for NOD'S SSM LAUNCHER. So the id that looks like a perfect match
# is the wrong faction's unit, and the right one shares no word with ours at all. Routing catches
# it (DTA's MLRS is tagged Nod) but only the alias FINDS the correct row.
# ⛔ Do not add `mlrs -> ssmlauncher` here. They are two different units and Cameo ships both.
# The mods that ship an original game and add nothing — so a NAME match against one of them is
# proof the actor is an original, and proof a counterpart exists in every other source too.
ORIGINAL_SOURCES = ("OpenRA Red Alert", "OpenRA Tiberian Dawn",
                    "OpenRA Tiberian Sun", "Romanov's Vengeance")

NAME_ALIASES = {
    "battletank": ("mediumtank",),
    "mediumtank": ("battletank",),
    "mlrs": ("msam", "rocketlauncher"),
    "ssmlauncher": ("mlrs",),
    # DTA writes it out in full where OpenRA and Combined Arms both abbreviate: `AGUN` "AA Gun"
    # and `CRAM` "AA Gun" against DTA's `RAAGUN` "Anti-aircraft Gun". Confirmed by the maintainer
    # as the same unit.
    "aagun": ("antiaircraftgun", "antiaircraft"),
    "alliedaagun": ("antiaircraftgun",),
}


def _substantial_containment(a, b):
    """One string inside the other, and enough of it to mean something.

    ⛔ THE OLD GUARD MEASURED THE WRONG STRING. It asked `len(cand) >= 8` — the length of the
    CAMEO id — while the danger is a SHORT PEER matching inside a long Cameo name. OpenRA Red
    Alert's `Ant` (Giant Ant) therefore scored 0.85 against
    `ra1_soviets_dragunovantimaterialsniper`, because "ant" is sitting in the middle of
    "...antimaterialsniper", and the sniper was assigned a giant ant with a straight face.

    Both sides must now carry weight: the shorter string has to be at least five characters and
    at least 40% of the longer. That keeps the matches this rule exists for — "Rocket Soldier"
    inside `sovietrocketsoldier`, "AA Gun" inside `alliedaagun`, faction-prefixed names like
    "GDI Medium Tank" — and refuses the accidental ones.
    """
    if a not in b and b not in a:
        return False
    lo, hi = sorted((len(a), len(b)))
    return lo >= 5 and lo / hi >= 0.4


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
        elif _substantial_containment(cand, peer):
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
    # ⛔ THE TEST IS INVERTED FROM WHAT IT WAS, and the old form was whack-a-mole. It asked
    # whether the leftover text appears in a hand-kept VARIANT_WORDS list — which holds "flame"
    # but not "fire", so `ra1_soviets_firerocketsoldier` was ranked a base unit and beat the
    # actual `ra1_soviets_sovietrocketsoldier` to Combined Arms' E3 and DTA's E3S. The real RA1
    # rocket soldier was left holding an Impaler and a Grenadier.
    #
    # A closed list of variant words can never be complete; the list of FACTION words can, because
    # the factions are ours and we know them. So: after removing the reference's own name,
    # anything left that is not a faction prefix makes this a VARIANT. `sovietrocketsoldier`
    # leaves "soviet" and is the base; `firerocketsoldier` leaves "fire" and is not.
    residue = tail.replace(peer, "")
    for w in FACTION_WORDS:
        residue = residue.replace(w, "")
    return 1 if not residue else 0


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
    # ⛔ AND THE MIRROR OF IT, which matters the moment chassis-only actors enter scope: an
    # UNARMED Cameo actor must not consume an ARMED peer. Without this a harvester can outbid a
    # tank for a tank's reference on shape alone and the tank is left with the leftovers — the
    # exact "the right candidate was deleted from the pool" failure, run in reverse. An MCV is
    # only ever comparable to another MCV.
    if not has_any_armament(rec) and any(peer.get(k) for k in
                                         ("w_damage", "w_range", "w_reload", "w_burst")):
        return None
    # ⛔ THE NAME SCORE IS BUCKETED, AND THAT IS WHAT MAKES THE CASCADE A CASCADE.
    # A lexicographic tuple whose first key is a near-continuous float degenerates into "rank by
    # that key alone": exact ties never happen, so tier, type, role and cost are never consulted.
    # Measured before this fix, 38% of assignments had a role score under 0.5 — the role step was
    # computed and then thrown away. Bucketing restores the maintainer's stated intent: name
    # DOMINATES, and the later keys decide among names of comparable quality.
    #   4 exact · 3 prefix/alias · 2 strong similarity · 1 shares a distinctive word · 0 neither
    # ⛔ SCORE THE PEER'S ID AS WELL AS ITS NAME, and take the better of the two. A mod's id is
    # frequently the only place the unit's common name survives — its display name having been
    # localised, expanded or renamed outright:
    #
    #   td_gdi_apc   -> CA `APC2`  "Armored Personnel Carrier"   name 0.231   id 0.900
    #   td_gdi_mlrs  -> DTA `MLRS` "SSM Launcher"                name 0.400   id 1.000
    #
    # Reading the name alone sent `td_gdi_apc` to an RA1 Allied IFV while CA's actual GDI APC sat
    # unused, and handed `td_gdi_mlrs` a Drone Launcher while DTA's real MLRS went unclaimed. Both
    # were then recorded as SHAPE matches — the scorer knew they were bad and the assignment kept
    # them anyway, which is the other half of this bug.
    raw_name = max(name_score(cam["id"], peer.get("name", "")),
                   name_score(cam["id"], peer.get("id", "")))
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

    # Chassis-only roles stay IN scope; the symmetric unarmed guard in the matcher is what keeps
    # them from consuming a combat unit's reference, so they no longer have to be dropped to be
    # safe. `skipped` keeps its name and its place in the output: it is now the record of WHICH
    # actors carry hp/speed only, not of actors that were thrown away.
    scope, skipped = [], {}
    for c in cam_rows:
        why = exempt(c["id"], led[c["id"]])
        if why:
            skipped[c["id"]] = why
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

    # ⛔ AN ORIGINAL CLAIMS BEFORE AN EXPANSION EVER BIDS (maintainer, 2026-09-07).
    #
    # `ra1_soviets_firerocketsoldier` — a Cameo addition — took Combined Arms' `E3` and DTA's
    # `E3S`, both Rocket Soldiers, while `ra1_soviets_sovietrocketsoldier`, the actual RA1 unit
    # those rows ARE, was left with an Impaler and a Grenadier. The greedy did nothing wrong by
    # its own lights: string similarity has no idea that "soviet" is a faction prefix and "fire"
    # is a variant prefix, so the expansion scores 0.867 against "Rocket Soldier" and the original
    # scores 0.850. The expansion is literally the closer string.
    #
    # No amount of scorer tuning fixes that, because the two names really are similar and the
    # tie-break has to come from OUTSIDE the string. The maintainer's rule supplies it: a unit
    # that exists in the original game has first claim on that game's row, and everything else
    # bids for what is left. Deciding it BEFORE the greedy runs is what makes it a rule rather
    # than another heuristic competing with the others.
    originals = original_actors(scope, by_source, routed_pool, routing)
    assign.originals = originals

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
        # Originals first, then score. `reverse=True` puts True ahead of False.
        cands.sort(key=lambda t: (t[1] in originals, t[0], t[1]), reverse=True)
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
            # ⛔ SHAPE AND WEAK ARE NOT EVIDENCE (maintainer ruling, 2026-09-07). A reference
            # must be backed by a NAME, never by shape alone.
            #
            # Measured on the ten mappings the maintainer called junk: 8 SHAPE, 2 WEAK, ZERO
            # STRONG. On the ones they called correct: 20 STRONG out of 21. The scorer separates
            # good from junk almost perfectly and the assignment then RECORDED THE JUNK ANYWAY,
            # as if a weak reference were a weak form of evidence. It is not — a Velociraptor is
            # not a poor sniper reference, it is not a reference. `td_gdi_officer` drew a
            # Triceratops, `td_gdi_shotgunner` a Stegosaurus, `td_gdi_sonicmissilesoldier` the
            # Commando (a hero Cameo already fields).
            #
            # ⚠ WHY THE JUNK IS SPECIFICALLY WEIRD UNITS, which is the part worth remembering:
            # the greedy matches originals first, so by the time an EXPANSION unit is reached the
            # ordinary units are taken and what is left in the pool is critters, heroes and
            # one-offs. An expansion did not draw a random reference — it drew one biased toward
            # junk. Dropping shape-only matches is what stops an actor with no true counterpart
            # from being handed the leftovers; it falls through to the formula instead, which is
            # where a unit nobody else ships belongs.
            result[cid][source] = {"name": p.get("name"), "id": p.get("id"), "score": s,
                                   "hp": p.get("hp"), "cost": p.get("cost"),
                                   "home": bool(s[2]), "raw_name": s[6], "confidence": conf}
    assign.formula_only = formula_only
    result = promote_by_id_agreement(result, by_source, routed_pool, routing)
    result = apply_overrides(result, by_source, routed_pool, routing)
    result, shape_only = drop_unbacked_shape(result)
    assign.shape_only = shape_only
    return result, skipped, len(scope)


ORIGINAL_NAME_FLOOR = 0.85


def original_actors(scope, by_source, routed_pool, routing):
    """Cameo actors that exist in an original game — decided BEFORE the greedy runs.

    The test is deliberately narrow: some ORIGINAL-shipping source must hold a row this actor
    matches by NAME or ID at `ORIGINAL_NAME_FLOOR`, and routing must allow it. 0.85 is the
    containment tier — "Rocket Soldier" inside `sovietrocketsoldier`, "Light Tank" inside
    `alliedlighttank` — which is where real originals land once the containment guard stops
    matching three-letter fragments.

    ⚠ This must NOT be derived from the finished assignment. That is circular, and it is also
    too late: the whole point is to decide who bids first.
    """
    out = set()
    for c in scope:
        cid = c["id"]
        fac = fr.faction_of(cid)
        for src in ORIGINAL_SOURCES:
            visible = (routed_pool.get((fac, src), ()) if routing else by_source.get(src, ()))
            for p in visible:
                if max(name_score(cid, p.get("name", "")),
                       name_score(cid, p.get("id", ""))) >= ORIGINAL_NAME_FLOOR:
                    out.add(cid)
                    break
            if cid in out:
                break
    return out


# ⛔ MAINTAINER-RULED PAIRINGS, for ambiguities no rule can resolve (2026-09-07).
#
# DTA's Allied navy is Corvette (id `DESTROYER`, 750cr) -> Frigate (1200) -> Cruiser (2500).
# Cameo's is Gunboat (1300) -> Destroyer (1600) -> Cruiser (3000). The IDS and the ROLES point
# opposite ways: DTA's id `DESTROYER` belongs to a ship they renamed "Corvette", which sits where
# RA1's Gunboat sits. Id agreement — normally strong evidence — is a FALSE FRIEND here.
#
# The maintainer ruled the LADDER wins: cheapest maps to cheapest, and all three Allied warships
# are used exactly once. Recorded as data rather than folded into the scorer, because it is a
# judgement about one mod's renaming, not a general principle — and a rule inferred from a single
# case is how the reference map got into trouble in the first place.
REFERENCE_OVERRIDES = {
    ("ra1_allies_gunboat", "DTA Enhanced"): "DESTROYER",   # DTA "Corvette"
    ("ra1_allies_destroyer", "DTA Enhanced"): "FRIGATE",
    # ── Combined Arms, ruled by the maintainer 2026-09-07 on review of the map ──────────────
    # Where a Cameo unit and a CA unit are the same THING under different names, and no rule can
    # see it. Each was named explicitly; none is inferred.
    ("ra1_soviets_flaktruck", "Combined Arms"): "BTR",     # not the Tesla Track
    ("ra1_soviets_teslatank", "Combined Arms"): "TTRA",    # CA's "Tesla Track" IS our tesla tank
    ("ra1_soviets_heavyteslatank", "Combined Arms"): "TTNK",   # and CA's "Tesla Tank" the heavy
    ("td_gdi_boxer", "Combined Arms"): "VULC",             # GDI Vulcan
    # `td_nod_lasertrooper`: Cyborg Elite over Enlightened. Both are routed to Nod and both are
    # elite Nod infantry, but the Enlightened's DPS is 40 against the Cyborg Elite's 260 — it is a
    # psionic support unit, and averaging its damage into a LASER trooper would import a number
    # that describes nothing about the unit. Range and role match too (7168 vs our 5524).
    ("td_nod_lasertrooper", "Combined Arms"): "RMBC",
    # CA ships TWO rows named "AA Gun" with identical stats. `AGUN` is the id OpenRA Red Alert
    # uses, so id agreement gives it to the Allied gun and frees `CRAM` for GDI's Skyshield.
    ("td_gdi_skyshield", "Combined Arms"): "CRAM",
    ("ra1_allies_alliedaagun", "Combined Arms"): "AGUN",
}


def apply_overrides(result, by_source, routed_pool, routing):
    """Force the maintainer-ruled pairings, displacing whatever the greedy chose."""
    index = {}
    for src, plist in by_source.items():
        for p in plist:
            index[(src, (p.get("id") or "").upper())] = p
    for (cid, src), pid in REFERENCE_OVERRIDES.items():
        p = index.get((src, pid.upper()))
        if p is None:
            continue
        for other, srcs in result.items():
            d = srcs.get(src)
            if other != cid and d and (d.get("id") or "").upper() == pid.upper():
                del srcs[src]
        result.setdefault(cid, {})[src] = {
            "name": p.get("name"), "id": p.get("id"), "score": None, "hp": p.get("hp"),
            "cost": p.get("cost"), "home": False, "raw_name": None, "confidence": "STRONG"}
    return result


def promote_by_id_agreement(result, by_source, routed_pool, routing):
    """When the sources AGREE ON AN ID, that id is the unit — whatever a source chose to call it.

    ⭐ THE SIGNAL NOBODY WAS READING. These mods descend from the same Westwood originals, so they
    share the original's id long after they have renamed the unit for flavour:

        ra1_allies_alliedlighttank    OpenRA `1TNK` "Light Tank"   DTA `1TNK` "Allied Light Tank"
                                      Combined Arms `1TNK` "SCOUT TANK"  <- name matches nothing

    Two sources had already agreed by name that this actor is `1TNK`. The third ships `1TNK` too
    and was passed over for a Mini Drone, because "Scout Tank" resembles nothing in our id and the
    matcher had no way to say "but it is the same unit".

    So: once an actor holds a NAME-backed reference, its id becomes evidence in its own right. Any
    source with no name-backed match, but which ships a row with that exact id, gets promoted to
    it. This only ever fills a slot that name matching failed on, never overrides one it won, and
    it respects the per-faction exclusivity — a row another actor already holds is not taken.
    """
    claimed = {(fr.faction_of(cid), src, (d.get("id") or "").upper())
               for cid, srcs in result.items() for src, d in srcs.items()}
    promoted = 0
    for cid, srcs in result.items():
        backed = {(d.get("id") or "").upper() for d in srcs.values()
                  if d["confidence"] in ("STRONG", "FAIR") and d.get("id")}
        if not backed:
            continue
        fac = fr.faction_of(cid)
        for src in by_source:
            cur = srcs.get(src)
            if cur and cur["confidence"] in ("STRONG", "FAIR"):
                continue
            visible = (routed_pool.get((fac, src), ()) if routing else by_source.get(src, ()))
            for p in visible:
                pid = (p.get("id") or "").upper()
                # ⭐ DTA PREFIXES ITS RED-ALERT-ERA ACTORS WITH `RA`, and it is a convention, not
                # a coincidence: `RAPBOX`, `RAAGUN`, `RASAM`, `RATSLA`, `RAFTUR`, `RAGUN`,
                # `RAARTY`, `RAPROC` — the Tiberian-era actor keeps the bare id, the Red Alert one
                # is prefixed, because DTA carries both rosters in one mod. Combined Arms and
                # OpenRA had already agreed `ra1_allies_pillbox` is `PBOX`; DTA ships `RAPBOX` and
                # was passed over, so the pillbox came out with two references instead of three.
                if pid not in backed and pid.removeprefix("RA") not in backed:
                    continue
                if (fac, src, pid) in claimed:
                    continue
                if cur:
                    claimed.discard((fac, src, (cur.get("id") or "").upper()))
                srcs[src] = {"name": p.get("name"), "id": p.get("id"),
                             "score": (cur or {}).get("score"), "hp": p.get("hp"),
                             "cost": p.get("cost"), "home": False,
                             "raw_name": None, "confidence": "FAIR"}
                claimed.add((fac, src, pid))
                promoted += 1
                break
    promote_by_id_agreement.count = promoted
    return result


def drop_unbacked_shape(result):
    """Shape-only references are evidence for an ORIGINAL and noise for an EXPANSION.

    ⛔ THE MAINTAINER'S RULE IS THE WHOLE ARGUMENT (2026-09-07):

        "All the original units are in OpenRA. DTA, CA and Cameo all expand the unit roster, so
         if it doesn't exist in OpenRA or OpenTD then it is an extra unit and those can't always
         have 3 references."

    Read it as a statement about PRIORS and the rule writes itself. For an original, the
    probability that a counterpart exists in a given source is 1 — so when the name match fails
    there (DTA calls its rocket soldier "Bazooka", its MLRS "SSM Launcher") a shape match is very
    likely to be that counterpart, and dropping it costs the actor a voice it is entitled to. For
    an expansion, no counterpart exists at all, and a shape match is only ever the best of the
    leftovers — which, because the greedy takes the originals first, means critters, heroes and
    one-offs. `td_gdi_officer` drew a Triceratops. `td_gdi_shotgunner` a Stegosaurus.

    So: an actor may keep its shape-only references ONLY if some ORIGINAL source matched it BY
    NAME. That one test separates the two populations exactly, and it is the maintainer's own rule
    restated — not a threshold anyone tuned.

    ⚠ Measured before this: of ten mappings the maintainer called junk, 8 were SHAPE and 2 WEAK,
    and ZERO were STRONG; of the ones they called correct, 20 of 21 were STRONG.

    ⛔ REVISED 2026-09-07, SAME DAY: shape references are now dropped for ORIGINALS TOO. Keeping
    them for originals was defensible in theory — a counterpart provably exists, so a shape match
    is probably it — and indefensible in practice. It is what left `ra1_allies_gunboat` holding a
    Mobile Repair Ship, `ra1_allies_alliedaagun` a Pill Box, `ra1_allies_pillbox` a Silo and
    `ra1_allies_alliedheavyaatank` a Heavy Flame Tank. The maintainer's verdict was "we need to
    increase our confidence here", and PRECISION IS THE THING BEING ASKED FOR: a source with no
    name-backed match should record NOTHING, and the O1 audit should then show that gap as work
    to do. An empty slot is a question. A Mobile Repair Ship is a wrong answer that will be
    silently averaged into a price.
    """
    kept, dropped = {}, {}
    for cid, srcs in result.items():
        keep, drop = {}, {}
        for s, d in srcs.items():
            if d["confidence"] in ("STRONG", "FAIR"):
                keep[s] = d
            else:
                drop[s] = {"id": d.get("id"), "name": d.get("name"),
                           "confidence": d["confidence"]}
        if keep:
            kept[cid] = keep
        if drop:
            dropped[cid] = drop
    return kept, dropped


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
    print(f"Cameo actors in scope : {in_scope}   chassis-only (hp+speed): {len(skipped)}   "
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
        OUT.write_text(json.dumps({"assignment": result, "chassis_only": skipped},
                                  indent=1, sort_keys=True) + "\n", encoding="utf-8")
        print(f"\nwrote {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
