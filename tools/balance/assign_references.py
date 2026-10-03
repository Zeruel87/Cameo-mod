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
    """Chassis-only actors need HP and speed alone, so they take a weaker reference test.

    ⛔ AN ARMED ACTOR IS NEVER CHASSIS-ONLY, whatever class it lands in. This guard used to ask the
    class question first, and `class_membership` files armed transports and the GDI Vulcan under
    `support` — so `td_gdi_boxer`, `td_gdi_apc`, `ra1_allies_alliedapc` and `ra1_soviets_btr80` were
    all reported chassis-only while carrying live weapons. The maintainer put it plainly on
    2026-09-08: *"td_gdi_boxer chassis-only but in fact the referenced vulcan does have a weapon!
    ... no they are not chassis only! Also review the other APCs as well since all APCs come with
    weapons!"*

    The weapon is the test, and it comes FIRST. A real support unit — engineer, harvester, MCV —
    carries no armament at all, so it still falls through to the class and word rules below.
    `has_any_armament` rather than `is_armed` for the same reason it is used everywhere else: a
    guard that is wrong in the RESTRICTIVE direction deletes correct candidates.
    """
    if has_any_armament(rec):
        return None
    if cm.classify(rec.get("design") or {})[0] in EXEMPT_CLASSES:
        return "support-class"
    tail = actor.split("_")[-1]
    for word in EXEMPT_WORDS:
        if word in tail:
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

# ⛔ TWO TABLES, BECAUSE AN ALIAS IS EITHER A NAME OR AN ID AND MIXING THEM COSTS REAL MAPPINGS.
# `name_score` is called TWICE per pair — once against the peer's display NAME and once against
# its ID — and a single shared table applies to both, which is how one entry can be right in one
# direction and wrong in the other.
#
# ⭐ THE SSM LAUNCHER IS THE CASE THAT PROVES IT (maintainer, 2026-09-13, twice). First:
# "td_nod_ssmlauncher still uses the wrong references. It should use the SSM launcher and not the
# combined arms MLRS". Then, after I removed the alias outright: "mobile sam was the correct
# reference for the SSM Launcher so your first reference was correct but now that it's removed
# it's wrong". Both are true, and the split is what satisfies both:
#
#   OpenRA TD  id MLRS   name "Mobile SAM"     <- CORRECT, and reachable only through the ID
#   DTA        id MLRS   name "SSM Launcher"   <- correct by NAME anyway
#   Combined   id MLRS   name "SSM Launcher"   <- correct by NAME anyway
#   Combined   id MSAM   name "MLRS"           <- WRONG, and it was reachable only through NAME
#   Romanov's  id mlrs   name "Rocket Launcher"<- WRONG by name
#   Twisted    id MLRSW  name "Bullfrog"       <- WRONG by name
#
# As one table the alias scored ALL of them 1.00 and the tie-break picked by cost. Split, the id
# alias reaches the two rows whose ID is `MLRS` and the name table never sees "MLRS" at all.
NAME_ALIASES = {
    "battletank": ("mediumtank",),
    "mediumtank": ("battletank",),
    # DTA and OpenRA both NAME the MLRS "Rocket Launcher".
    "mlrs": ("rocketlauncher",),
    # DTA writes it out in full where OpenRA and Combined Arms both abbreviate: `AGUN` "AA Gun"
    # and `CRAM` "AA Gun" against DTA's `RAAGUN` "Anti-aircraft Gun". Confirmed by the maintainer
    # as the same unit.
    "aagun": ("antiaircraftgun", "antiaircraft"),
    "alliedaagun": ("antiaircraftgun",),
    # OpenRA Red Alert names the Soviet flame infantry `E4` "Flame Infantry" — the same unit
    # every other source calls a Flamethrower. Verified 2026-09-22: E4 is soviet-tagged,
    # admissible to `ra1_soviets`, and was claimed by nobody; no other admissible row carries
    # the name, and no other Cameo actor tail ends in `flamethrower` within E4's routes.
    "flamethrower": ("flameinfantry",),
}

# Applied to the peer's ID ONLY. A mod's id frequently preserves the unit's original identity
# while its display name has been localised, expanded or renamed outright.
ID_ALIASES = {
    # Tiberian Dawn's SSM Launcher ships under the id `MLRS`, whatever the display says.
    "ssmlauncher": ("mlrs",),
    # Combined Arms and OpenRA both id the MLRS `MSAM`.
    "mlrs": ("msam",),
    # Two Tiberian-Sun-descendant mods independently rename GDI's Light Infantry "Marine" —
    # Shattered Paradise `GDIE1` and Crystallized Nexus `GASOL`, both gdi-tagged and admissible
    # to `ts_gdi` only (verified 2026-09-22: these are the only exact "Marine" rows in the
    # corpus, and both were unclaimed). Scoped to ids so the generic word can never fire on a
    # different unit; the `ts_nod` light infantry reaches SP/TI through REFERENCE_OVERRIDES
    # below instead, because those sources give the Nod side to other ids entirely.
    "lightinfantry": ("gdie1", "gasol"),
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


def name_score(cameo_id, peer_name, aliases=None):
    """0..1. Exact and alias matches sit at the top; a shared distinctive word still counts.

    `aliases` selects WHICH table applies — `NAME_ALIASES` when comparing against the peer's
    display name, `ID_ALIASES` when comparing against its id. Defaults to the name table so an
    existing caller keeps its behaviour.
    """
    aliases = NAME_ALIASES if aliases is None else aliases
    tail = syn.norm(cameo_id.split("_")[-1])
    peer = syn.norm(peer_name)
    if not tail or not peer:
        return 0.0
    best = 0.0
    for cand in (tail,) + aliases.get(tail, ()):
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
# games do: `ra1_soviets_mammothtank` is RA1's Mammoth, and `ra1_soviets_siegemammothtank`
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
    # actual `ra1_soviets_rocketsoldier` to Combined Arms' E3 and DTA's E3S. The real RA1
    # rocket soldier was left holding an Impaler and a Grenadier.
    #
    # A closed list of variant words can never be complete; the list of FACTION words can, because
    # the factions are ours and we know them. So: after removing the reference's own name,
    # anything left that is not a faction prefix makes this a VARIANT. `sovietrocketsoldier`
    # leaves "soviet" and is the base; `firerocketsoldier` leaves "fire" and is not.
    residue = tail.replace(peer, "")
    # ⛔ DETERMINISM (found 2026-09-09, regenerating for the Katyusha override). FACTION_WORDS is
    # a frozenset, so iteration order is hash-randomized PER PROCESS — and the words OVERLAP:
    # "japan" is a prefix of "japanese", likewise soviet/soviets, german/germany, america/american
    # and russia/russian. Removing the shorter one first eats the longer's tail ("japanese" ->
    # "ese", "germany" -> "y"), so the same (actor, peer) pair scored variant 1 in one process and
    # variant 0 in the next; `japan_japaneseflamethrower | RA2 Reborn` is the row it was caught on.
    # Sort longest-first, lexical among equals, so the longest word always consumes first and the
    # answer is stable whatever the seed. This cannot invent a third outcome: for any overlapping
    # pair the only two orders that ever existed are shortest-first and longest-first, so the
    # fixed order is one of the two the data has already been flipping between.
    for w in sorted(FACTION_WORDS, key=lambda word: (-len(word), word)):
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
    # HERO-TO-HERO ONLY (maintainer ruling, 2026-09-07). Heroes and epics are balanced
    # separately, so a hero may ONLY match a hero and a non-hero may ONLY match a
    # non-hero. Without this, the 3,000,000 HP epic would match a normal vehicle on
    # shape alone and a normal unit would claim a hero's peer. The flag is carried
    # on the row, never a drop.
    cam_hero = cam.get("hero", False)
    peer_hero = peer.get("hero", False)
    if cam_hero != peer_hero:
        return None
    if cam["type"] != peer["type"]:
        return None                                   # cross-type is refused (§9 cross-type ruling)
    # ⛔ CLAUSE 5, AND *MISSING* DAMAGE COUNTS AS UNARMED. The old guard read
    # `w_damage is not None and not w_damage`, which fires only on an explicit zero — so a row
    # that carries NO damage field at all sailed past it. Every unarmed reference in the corpus is
    # exactly that shape: OpenRA TD's Mobile Construction Vehicle and Combined Arms' Thief both
    # have `w_damage=None`, and both were duly assigned to armed Cameo units (an MCV to
    # `td_gdi_mammothtankmkiii`, a Thief to `ra1_soviets_rocketsoldier`) on shape similarity
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
    raw_name = max(name_score(cam["id"], peer.get("name", ""), NAME_ALIASES),
                   name_score(cam["id"], peer.get("id", ""), ID_ALIASES))
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


VARIANT_MARKER = re.compile(r"_(?:elite|veteran|deployed|empty|undeployed|husk)$", re.I)


def cameo_variant_ids(scope):
    """Cameo actors that are a VARIANT of another Cameo actor — the mirror of `variant_pool`.

    Same test as the peer side, which is the point: an id that EXTENDS a sibling's id inside the
    same faction. `td_gdi_humvee` -> `td_gdi_humveemkii`, `td_nod_lighttank` ->
    `td_nod_lighttankmkii`, `ts_gdi_titan` -> `ts_gdi_titanmkii`. Applying one test to both sides
    is what keeps this a rule; a hand-kept list of "promotion units" would go stale the first time
    somebody added one.

    ⚠ THE SUFFIX EXCLUSIONS ARE THE SAME EXCLUSIONS, TOO. `_elite` is a veterancy rank and
    `_deployed` / `_empty` are stances or cargo states — the same two populations `variant_pool`
    refuses on the peer side (`MARATNK2` "(Elite)", `THRASHERD` "(Deployed)"). A rank is not a
    chassis on either side of the map.

    ⚠ A FALSE POSITIVE HERE IS CHEAP AND A FALSE NEGATIVE IS NOT. `forgotten_mutant` ->
    `forgotten_mutantsniper` is not really a variant — a Mutant Sniper is its own unit — but all
    this list does is decide who may BID. The scorer and `drop_unbacked_shape` still require a
    NAME-backed match, and no peer variant is called "Mutant Sniper", so the row simply never
    appears. Excluding a real variant, by contrast, silently restores the gap this lane exists to
    close.
    """
    by_faction = collections.defaultdict(set)
    for c in scope:
        by_faction[fr.faction_of(c["id"])].add(c["id"])
    out = {}
    for fac, ids in by_faction.items():
        prefix = len(fac) + 1 if fac else 0
        for cid in ids:
            if VARIANT_MARKER.search(cid):
                continue
            # The base must be a real unit name, not just the faction prefix plus a letter.
            bases = [b for b in ids if b != cid and cid.startswith(b) and len(b) - prefix >= 4]
            if bases:
                out[cid] = max(bases, key=len)
    return out


def assign(only_class=None, routing=True):
    """{cameo id: {source: proposal}}, plus what was skipped and why.

    ⛔ ROUTING IS THE DEFAULT (clause 11). `routing=False` reproduces the pre-2026-09-04 behaviour
    — every source visible to every unit — and exists ONLY so the two can be compared. It is the
    behaviour the maintainer rejected; do not generate a review sheet with it.
    """
    peers, cameo = rd.peer_rows(), rd.cameo_rows()
    # HERO LANE (maintainer, 2026-09-07). Heroes stay OUT of distributions (peer_rows()
    # and cameo_rows() still exclude them), but the ASSIGNMENT may see them so a Cameo
    # hero matches a peer hero. The hero-to-hero-only rule in score() prevents a hero
    # from matching a non-hero and vice versa. 83 Cameo heroes + 424 peer heroes in scope.
    #
    # ⛔ TWO-PASS DESIGN. The hero lane runs as a SEPARATE pass after the non-hero
    # assignment is complete. Mixing hero and non-hero rows in the same greedy pool
    # changed 9 non-hero mappings (the hero cameos shifted the sort order and stole
    # peers from non-hero cameos). The two-pass approach guarantees "no non-hero
    # mapping changes at all" — the acceptance criterion from FLEET_ORDERS_2026-09-08.
    hero_peers = rd.peer_hero_rows()
    hero_cameo = rd.cameo_hero_rows()
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
    # `E3S`, both Rocket Soldiers, while `ra1_soviets_rocketsoldier`, the actual RA1 unit
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

    # ⛔ HERO PEERS DO NOT JOIN THE NON-HERO GREEDY. The two-pass design runs the
    # hero lane separately after this function returns, so hero peers never enter
    # `by_source` or `routed_pool` here. This is the guarantee that no non-hero
    # mapping changes when the hero lane is enabled.

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
        # clause 9: greedy descent — best remaining wins, both sides then spoken for.
        #
        # ⛔ THE ORIGINALS PREFERENCE SITS INSIDE THE NAME BUCKET, NOT ABOVE IT (fixed 2026-09-12).
        # It used to be the outermost key — `(t[1] in originals, t[0], t[1])` — which made it a
        # hard precedence rather than a tie-break: EVERY bid by an original actor, including a
        # worthless shape-only one, was processed before ANY bid by an expansion actor, including
        # an exact name match. Measured cost of that:
        #
        #   `ra2_allies_nighthawk` (an original) took Valiant Shades' `beag` and CnC Reloaded's
        #   `BEAG` — both named "Black Eagle" — at name 0.154, SHAPE. `ra2_allies_blackeagle`
        #   scored 1.0 on both and was refused them because the rows were already spent. Then
        #   `drop_unbacked_shape` correctly binned the nighthawk rows for being shape-only, and
        #   the two Black Eagles ended the run held by NOBODY.
        #
        # That is the "right candidate was deleted from the pool" failure in a new shape: the row
        # was not deleted, it was consumed by an actor that then had it taken away again.
        #
        # ⭐ AND THE MAINTAINER'S RULE STILL HOLDS, which is why this is a fix and not a reversal.
        # The case it was written for — `ra1_soviets_firerocketsoldier` scoring 0.867 against
        # "Rocket Soldier" while `ra1_soviets_rocketsoldier`, the actual RA1 unit, scored 0.850 —
        # is a contest WITHIN one name bucket (both >= 0.75, so both bucket 2). Ordering by bucket
        # first and originals second still hands that row to the original. What no longer happens
        # is a 0.15 beating a 1.0 because of who bid it.
        cands.sort(key=lambda t: (t[0][0], t[1] in originals, t[0][1:], t[1]), reverse=True)
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
            # those rows are: `asianalliance_militia` drew "sspy" at name 0.12 / role 0.93,
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

    # ── HERO PASS (maintainer ruling 2026-09-07) ──────────────────────────────
    # A separate greedy for hero/epic cameos against hero/epic peers only. This
    # runs AFTER the non-hero assignment is complete, so it cannot change any
    # non-hero mapping. The hero-to-hero-only rule in score() prevents a hero
    # from matching a non-hero and vice versa, and this pass only sees heroes
    # on both sides, so every match is hero-to-hero by construction.
    if hero_cameo and hero_peers:
        hero_led = {c["id"]: led[c["id"]] for c in hero_cameo if c["id"] in led}
        hero_scope = [c for c in hero_cameo if c["id"] in hero_led
                      and (not only_class or cm.classify(hero_led[c["id"]].get("design") or {})[0] == only_class)]
        # Skip exempted hero cameos (same exempt() as non-hero pass)
        hero_scope = [c for c in hero_scope if not exempt(c["id"], hero_led[c["id"]])]
        # Route hero cameos
        if routing:
            hero_scope = [c for c in hero_scope
                          if fr.faction_of(c["id"]) and fr.routes_for(fr.faction_of(c["id"]))]
        # Build hero peer pool
        hero_by_source = collections.defaultdict(list)
        for p in hero_peers:
            hero_by_source[p["source"]].append(p)
        hero_routed_pool = {}
        if routing:
            for fac in {fr.faction_of(c["id"]) for c in hero_scope}:
                for src, _toks in fr.routes_for(fac):
                    hero_routed_pool[(fac, src)] = [p for p in hero_by_source.get(src, ())
                                                    if fr.allows(fac, p)]
        # Hero shape vectors
        hero_pools = collections.defaultdict(list)
        for p in hero_peers:
            for f in SHAPE_FIELDS:
                if p.get(f):
                    hero_pools[(p["source"], p["type"], f)].append(p[f])
        for c in hero_scope:
            for f in SHAPE_FIELDS:
                if c.get(f):
                    hero_pools[("Cameo", c["type"], f)].append(c[f])
        hero_cam_shapes = {c["id"]: shape_vector(c, hero_pools, "Cameo") for c in hero_scope}
        hero_peer_shapes = {id(p): shape_vector(p, hero_pools, p["source"]) for p in hero_peers}
        # Hero costs
        hero_cam_costs = collections.defaultdict(list)
        for c in hero_scope:
            v = (hero_led[c["id"]].get("cost") or {})
            v = v.get("v") if isinstance(v, dict) else v
            try:
                hero_cam_costs[c["type"]].append(float(v))
            except (TypeError, ValueError):
                pass
        hero_peer_costs = collections.defaultdict(list)
        for p in hero_peers:
            if p.get("cost"):
                hero_peer_costs[(p["source"], p["type"])].append(p["cost"])
        # Hero greedy
        for source, plist in sorted(hero_by_source.items()):
            cands = []
            for c in hero_scope:
                rec = hero_led[c["id"]]
                raw = (rec.get("cost") or {})
                raw = raw.get("v") if isinstance(raw, dict) else raw
                try:
                    ccost = float(raw)
                except (TypeError, ValueError):
                    ccost = None
                cpct = pct_rank(ccost, hero_cam_costs.get(c["type"], []))
                home = source in eu.HOME.get(eu.family_of(c["id"]) or "", [])
                visible = (hero_routed_pool.get((fr.faction_of(c["id"]), source), ()) if routing
                           else plist)
                for p in visible:
                    s = score(c, rec, p, cpct,
                              pct_rank(p.get("cost"), hero_peer_costs.get((source, p["type"]), [])), home,
                              hero_cam_shapes.get(c["id"]), hero_peer_shapes.get(id(p)))
                    if s:
                        cands.append((s, c["id"], p))
            cands.sort(key=lambda t: (t[0], t[1]), reverse=True)
            used_cam, used_peer = set(), set()
            for s, cid, p in cands:
                key = (fr.faction_of(cid), p["source"], syn.norm(p.get("name", "")), p.get("id", ""))
                if cid in used_cam or key in used_peer:
                    continue
                used_cam.add(cid)
                used_peer.add(key)
                bucket, role_score = s[0], s[4]
                if bucket >= 3 or (bucket >= 1 and role_score >= 0.75):
                    conf = "STRONG"
                elif bucket >= 1:
                    conf = "FAIR"
                elif role_score >= 0.75:
                    conf = "SHAPE"
                else:
                    conf = "WEAK"
                if bucket >= 1 or role_score >= 0.75:
                    result.setdefault(cid, {})[source] = {"name": p.get("name"), "id": p.get("id"), "score": s,
                                           "hp": p.get("hp"), "cost": p.get("cost"),
                                           "home": bool(s[2]), "raw_name": s[6], "confidence": conf}
        assign.hero_count = sum(1 for k in result if any(c.get("hero") for c in hero_cameo if c["id"] == k))

    # ── VARIANT PASS (maintainer, 2026-09-12) ────────────────────────────────────────────────
    #
    #     "there are some additional units from DTA that might be unbuildable. What are those and
    #      can some of them be mapped? Like I've seen a drone carrier and a missile humvee.
    #      Maybe useful for our promotion units?"
    #
    # A third lane, built exactly like the hero lane and for the same reason: the population rule
    # ("only buildable units, no epic units with build limits") is a rule about DISTRIBUTIONS that
    # the ASSIGNMENT kept inheriting by accident. DTA ships `JEEPPTNK` "Rocket Hum-vee" — a Hum-vee
    # hull carrying `APTusk` — at TechLevel -1. Cameo ships `td_gdi_humveemkii`. That is a
    # counterpart and the population rule had hidden it.
    #
    # ⛔ VARIANT-TO-VARIANT ONLY, and the test is SYMMETRIC — the same test on both sides, which
    # is what makes it a rule rather than a heuristic. A variant is an id that EXTENDS a sibling's
    # id within the same roster: `JEEP` -> `JEEPPTNK` on the peer side, `td_gdi_humvee` ->
    # `td_gdi_humveemkii` on ours. Letting a BASE Cameo unit bid would be the defect this is meant
    # to fix, running backwards: `td_gdi_humvee` scores against "Rocket Hum-vee" just as well as
    # `td_gdi_humveemkii` does, so the base would take the variant's reference and the MkII would
    # be left with the leftovers — "the right candidate was deleted from the pool" again.
    #
    # ⛔ THE PAIRING IS DERIVED, NOT SCORED — and the first attempt at this lane is why.
    #
    # Scoring variant against variant does not work, and it fails in a way worth writing down.
    # `name_score("td_gdi_humveemkii", "Rocket Hum-vee")` is 0.545: the scorer RANKS it first of
    # DTA's six, correctly, but 0.545 sits under the 0.6 floor of name bucket 1. So every pair in
    # the lane tied at bucket 0, the cascade fell through to shape and cost, and the Hum-vee MkII
    # was handed a HEAVY ARTILLERY while the Rocket Hum-vee sat unused two rows away. The reason
    # is structural rather than a bad threshold: a variant's name carries the MODIFIER and drops
    # the chassis ("Rocket" vs "mkii"), so the two names genuinely do not look alike.
    #
    # But the map already knows the answer. `td_gdi_humvee` holds DTA's `JEEP`, and `JEEPPTNK`
    # records that it is a variant OF `JEEP`. Both sides state their base, so the pairing is a
    # lookup:
    #
    #     Cameo variant V (base B)  +  B already references peer row R in source S
    #     +  peer variant P in S with variant_of == R        =>        V references P
    #
    # That is how a person reads it — "DTA's Hum-vee is our Hum-vee, so DTA's variant of the
    # Hum-vee is our variant of the Hum-vee" — and it cannot invent junk: with no assigned base
    # there is no candidate, so the slot stays empty and O1 reports it as work, exactly as
    # `drop_unbacked_shape` intends. Name score is used ONLY to break a tie when one base carries
    # two variants (`HTNK` -> both `HTNKARTY` "Mammoth Artillery" and `HTNKMSAM` "Disruptor").
    #
    # ⛔ STRICTLY ADDITIVE: it writes ONLY into an empty (actor, source) slot. The hero lane used
    # `setdefault(cid, {})[source] = ...`, which overwrites, and needed a two-pass design plus an
    # acceptance test to prove it changed no non-hero mapping. Refusing to overwrite makes that
    # guarantee structural instead of measured — no existing mapping can change, because none is
    # ever written over.
    variant_peers = rd.peer_variant_rows()
    variant_cameo = cameo_variant_ids(scope)
    assign.variant_cameo = variant_cameo
    assign.variant_filled = filled = []
    assign.variant_unmatched = unmatched = []
    by_base = collections.defaultdict(list)
    for p in variant_peers:
        by_base[(p["source"], (p.get("variant_of") or "").upper())].append(p)
    used_peer = set()
    for cid, base in sorted(variant_cameo.items()):
        if cid not in led or base not in result:
            continue
        if only_class and cm.classify(led[cid].get("design") or {})[0] != only_class:
            continue
        fac = fr.faction_of(cid)
        for source, base_row in sorted(result[base].items()):
            if result.get(cid, {}).get(source):
                continue                                  # additive only
            cands = [p for p in by_base.get((source, (base_row.get("id") or "").upper()), ())
                     if (not routing or fr.allows(fac, p))
                     and (fac, p["source"], p.get("id", "")) not in used_peer]
            if not cands:
                continue
            # Tie-break only: one base can carry two variants, and the NAME decides which is
            # which. `HTNK` -> `HTNKARTY` (0.562) beats `HTNKMSAM` (0.417) for a Mammoth MkIII.
            p = max(cands, key=lambda p: (max(name_score(cid, p.get("name", "")),
                                              name_score(cid, p.get("id", ""))), p.get("id", "")))
            used_peer.add((fac, p["source"], p.get("id", "")))
            raw = max(name_score(cid, p.get("name", "")), name_score(cid, p.get("id", "")))
            # ⚠ THE CONFIDENCE IS THE BASE'S, CAPPED AT FAIR — never invented and never promoted.
            # The evidence for this row is the base pairing (which IS name-backed, or it would
            # have been dropped) plus a structural variant link on both sides. That is real, and
            # it is weaker than an outright name match, so it must never present as STRONG.
            conf = "FAIR" if base_row.get("confidence") in ("STRONG", "FAIR") else "WEAK"
            result.setdefault(cid, {})[source] = {
                "name": p.get("name"), "id": p.get("id"),
                "score": (1, 0, 0, 0.0, 0.0, 0.0, round(raw, 3)),
                "hp": p.get("hp"), "cost": p.get("cost"), "home": False,
                "raw_name": round(raw, 3), "confidence": conf, "variant": True,
                "variant_of": p.get("variant_of"), "derived_from": base}
            filled.append((cid, source, p.get("id"), p.get("name"), base, base_row.get("id")))
    for cid, base in sorted(variant_cameo.items()):
        if not any(f[0] == cid for f in filled):
            unmatched.append((cid, base, "base has no reference" if base not in result
                              else "no peer variant of the base's row"))

    # ⛔ THE HERO PASS RUNS AFTER `apply_overrides` AND `drop_unbacked_shape`, so on its own it
    # bypasses BOTH. Measured when the lane first landed: 12 SHAPE rows came back into a map that
    # had been 100% name-backed for a day, and the maintainer's own overrides for DTA's `A10` and
    # `XO` could not resolve because the hero rows were absent from the override index. Both rules
    # are re-applied here over the combined pool. A rule that the last pass in a pipeline skips is
    # not a rule.
    hero_by_source = collections.defaultdict(list)
    for p in (hero_peers or ()):
        hero_by_source[p["source"]].append(p)
    variant_by_source = collections.defaultdict(list)
    for p in (variant_peers or ()):
        variant_by_source[p["source"]].append(p)
    combined = collections.defaultdict(list)
    for src, rows_ in (list(by_source.items()) + list(hero_by_source.items())
                       + list(variant_by_source.items())):
        combined[src].extend(rows_)
    # ── ORIGINALS CROSS-LANE PASS (maintainer, 2026-09-13) ───────────────────────────────────
    #
    #     "Can you please also use it as reference or what?"  — on DTA Enhanced's `CTNK`
    #     "Chrono Tank", which was sitting unclaimed while `ra1_allies_chronotank` held only two.
    #
    # ⛔ THE PROBLEM IS NOT SCORING, IT IS VISIBILITY — the failure mode this repo keeps paying
    # for. DTA caps its Chrono Tank at `build_limit 2`, so `is_hero_limit` puts it in the HERO
    # pool; the maintainer removed Cameo's own limit so the actor could match, which put the Cameo
    # side in the ORDINARY pool; and the two lanes are impermeable on purpose. A name-exact,
    # id-exact original was therefore visible to a human and unreachable by every pass.
    #
    # ⚠ LOOSENING `is_hero_limit` IS THE WRONG FIX and was measured before this one was written:
    # `> 0` -> `> 1` releases this row and ALSO releases CnC Reloaded's `NODCOMMANDO` (Nod
    # Commando, limit 2) into the ordinary vehicle population — 29 corpus rows move, including
    # commandos, Slave Miners and Grand Cannons. The lane rule is right; what it needed was a
    # narrow, derived exception rather than a wider threshold.
    #
    # THE RULE, and every clause is load-bearing:
    #   * the actor must already hold an ORIGINAL-source row whose `raw_name` is EXACTLY 1.0 —
    #     an exact-name anchor, never a merely good one;
    #   * the candidate must match that anchor on BOTH id and normalised name;
    #   * the source must be routed for the actor's faction and not already filled;
    #   * the candidate must be unclaimed by any actor, in any lane.
    #
    # ⛔ THE `raw_name == 1.0` GATE IS WHAT STOPS IT PROPAGATING A BAD BASE. Without it the pass
    # extends whatever the greedy already got wrong: `ra2_allies_grandcannon` holds Romanov's
    # Vengeance `yaggun` "Gatling Cannon" at raw_name 0.75, and the ungated rule dutifully handed
    # it Mental Omega's `YAGGUN` as well — the same mistake, twice, now looking corroborated. With
    # the gate the additions fall 34 -> 26 and every survivor is unmistakable: `DOG` "Attack Dog",
    # `SONIC` "Disruptor", `TESLA` "Tesla Coil", `MMCH` "Titan".
    #
    # ⭐ AND IT TURNED OUT TO BE MORE THAN A HERO-LANE PATCH: 24 of the 26 recovered rows are in
    # the ORDINARY lane — rows the greedy simply never reached, because it takes one peer per
    # actor per source and these sat below the winner in their bucket.
    #
    # ⛔ STRICTLY ADDITIVE, exactly as the variant pass above: it writes ONLY into an empty
    # (actor, source) slot and claims each peer row once, so no existing mapping can change. It
    # runs BEFORE `apply_overrides`/`drop_unbacked_shape` so both still govern its output.
    # Confidence is FAIR, never STRONG — the evidence is real but it bypassed the greedy, and a
    # lane that promotes itself is how a map stops being checkable.
    assign.crosslane = crosslane = []
    claimed_rows = {(src, (m.get("id") or "").upper())
                    for srcs in result.values() for src, m in srcs.items()}
    for cid in sorted(result):
        fac = fr.faction_of(cid)
        if not fac:
            continue
        anchors = [m for src, m in result[cid].items()
                   if src in ORIGINAL_SOURCES and m.get("raw_name") == 1.0]
        if not anchors:
            continue
        for src in sorted({s for s, _ in (fr.ROUTES.get(fac) or ())} - set(result[cid])):
            for pr in combined.get(src, ()):
                pid = (pr.get("id") or "").upper()
                if not pid or (src, pid) in claimed_rows:
                    continue
                if routing and not fr.allows(fac, pr):
                    continue
                if not any(pid == (m.get("id") or "").upper()
                           and syn.norm(pr.get("name", "")) == syn.norm(m.get("name", ""))
                           for m in anchors):
                    continue
                claimed_rows.add((src, pid))
                result[cid][src] = {
                    "name": pr.get("name"), "id": pr.get("id"),
                    "score": (1, 0, 0, 0.0, 0.0, 0.0, 1.0),
                    "hp": pr.get("hp"), "cost": pr.get("cost"), "home": False,
                    "raw_name": 1.0, "confidence": "FAIR", "cross_lane": True}
                crosslane.append((cid, src, pr.get("id"), pr.get("name")))
                break

    result = apply_overrides(result, combined, routed_pool, routing)
    result, hero_dropped = drop_unbacked_shape(result)
    assign.shape_only = {**getattr(assign, "shape_only", {}), **hero_dropped}

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
SHARED_COMMANDO_ACTORS = frozenset(('td_gdi_commando', 'td_nod_commando'))
SHARED_COMMANDO_SOURCES = frozenset(('Combined Arms', 'DTA Enhanced', 'OpenRA Tiberian Dawn'))

REFERENCE_OVERRIDES = {
    # Aedis 2026-09-11 00:07: same base Commando, different Cameo upgrades.
    **{(actor, source): 'RMBO' for actor in SHARED_COMMANDO_ACTORS for source in SHARED_COMMANDO_SOURCES},
    # Original-unit gaps: renamed Scout Tank and RA-prefixed camouflaged pillbox.
    ('ra1_allies_alliedlighttank', 'Combined Arms'): '1TNK',
    ('ra1_allies_camopillbox', 'DTA Enhanced'): 'RAHBOX',
    # 2026-09-14 original-coverage review. These are exact identity rows that the automatic
    # matcher cannot use because their source ownership is untagged/shared, or because a display
    # name adds a faction prefix. Every row was verified unclaimed before admission.
    ('ra2_allies_engineer', 'Valiant Shades'): 'AENGINEER',
    ('ra2_soviets_engineer', 'Valiant Shades'): 'SENGINEER',
    ('ra2_soviets_sentrygun', 'Mental Omega'): 'NALASR',
    ('ra2_soviets_sentrygun', 'CnC Reloaded'): 'NALASR',
    ('ra2_soviets_sentrygun', 'RA2 Reborn'): 'NALASR',
    ('ra2_soviets_sentrygun', 'Red Resurrection'): 'NALASR',
    ('ts_gdi_mobileconstructionvehicle', 'Shattered Paradise'): 'MCV',
    ('ts_gdi_mobilesensorarray', 'Crystallized Nexus'): 'LPST',
    ('ts_nod_lightinfantry', 'Shattered Paradise'): 'ALTNODE1',
    ('ts_nod_lightinfantry', 'Twisted Insurrection'): 'E1NOD',
    # Aedis 2026-09-10: original Soviet Mammoth, not the Siege expansion.
    ("ra1_soviets_mammothtank", "DTA Enhanced"): "4TNK",
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
    # ⛔ NEVER REFERENCE ACROSS FACTIONS (maintainer, 2026-09-14): *"the GDI emp grenadier was
    # mapped to the CA marauder which is a scrin unit so that is wrong! Never ever reference from
    # other factions without my instructions! What we need is the CA zone raider with the sonic
    # grenades which is much closer to the EMP grenadier and also from a gdi sub faction called
    # ZOCOM."* The Zone Raider throws sonic grenades from ZOCOM, a GDI sub-faction; the Marauder
    # is Scrin infantry that happens to sit at a similar cost and HP.
    #
    # ⚠ THE FACTION GATE CANNOT CATCH THIS ONE, and that is the finding worth keeping. CA tags
    # `MRDR` and `ZRAI` with the SAME 25-faction string - "allies/arc/.../gdi/.../scrin/.../zocom",
    # every faction in the mod - so `home: true` was recorded for a Scrin unit truthfully as far
    # as the data goes. 156 of CA's 377 units carry ten or more faction tags (median 5), against a
    # median of 1 in OpenRA Tiberian Dawn. So for CA the routing gate is not merely weak, it is
    # INERT, and a cross-faction pick cannot be detected from the corpus at all. Until CA lineage
    # is derived from something other than `Buildable.Factions`, every CA pairing is a name-and-
    # stats match with no faction check behind it, and the maintainer eye is the only gate.
    ("td_gdi_empgrenadier", "Combined Arms"): "ZRAI",      # Zone Raider (ZOCOM), sonic grenades
    # CA ships TWO rows named "AA Gun" with identical stats. `AGUN` is the id OpenRA Red Alert
    # uses, so id agreement gives it to the Allied gun and frees `CRAM` for GDI's Skyshield.
    ("td_gdi_skyshield", "Combined Arms"): "CRAM",
    ("ra1_allies_alliedaagun", "Combined Arms"): "AGUN",

    # ── Maintainer review round FOUR, 2026-09-08. Every id below was verified present in the
    # routed pool before it was written here; `apply_overrides` now WARNS on one that is not,
    # because a typo used to vanish silently and read as "the matcher chose badly".
    #
    # Regressions first — mappings that existed and were lost:
    ("td_gdi_rocketsoldier", "DTA Enhanced"): "E3",        # DTA calls it "Bazooka"; no shared word
    ("td_nod_rocketsoldier", "DTA Enhanced"): "E3N",       # the Nod-side row of the same pair
    ("td_nod_apacheattackhelicopter", "OpenRA Tiberian Dawn"): "HELI",   # named "Apache Longbow"
    ("ra1_soviets_dog", "Combined Arms"): "DOG",
    ("ra1_soviets_dog", "OpenRA Red Alert"): "DOG",
    ("ra1_soviets_dog", "DTA Enhanced"): "DOG",
    # Tiberian Dawn:
    ("td_gdi_archerartillery", "DTA Enhanced"): "DISCARTY",   # "Disc Launcher", GDI
    ("td_gdi_archerartillery", "Combined Arms"): "THWK",      # Tomahawk Launcher
    ("td_gdi_exosuit", "Combined Arms"): "XO",                # X-O Powersuit
    ("td_gdi_predatortank", "Combined Arms"): "MTNK.Laser",   # the GDI Battle Tank replacement
    # ⭐ THE A-10, NOT THE AURORA (maintainer, 2026-09-13): "CA has the A10 warthog right? Can
    # you use it instead of the aurora for the fire hawk as reference." CA ships `A10` "Warthog"
    # (plus `A10.GAU` and `A10.SW` variants) for arc/eagle/gdi/talon/zocom, and DTA's row for this
    # actor is already its own `A10` — so the two references now describe the same aircraft.
    # ⚠ The old comment here promised "A10 joins via FAMILY_EXTRA". There is no FAMILY_EXTRA in
    # this file; the mechanism it named does not exist, so the A-10 never joined anything and the
    # Aurora stood alone. A comment naming a mechanism is not the mechanism.
    ("td_gdi_firehawk", "Combined Arms"): "A10",              # Warthog — the Aurora is a bomber, not this
    ("td_nod_venom", "Combined Arms"): "VENM",
    # Red Alert, Allies:
    ("ra1_allies_rapierjumpjet", "Combined Arms"): "BEAG",    # Black Eagle — NOT the Blackhawk
    ("ra1_allies_alliedapc", "Combined Arms"): "APC",         # the Allied APC, not GDI's APC2
    ("ra1_allies_alliedapc", "DTA Enhanced"): "RAAPC",        # DTA prefixes RA-era actors with RA
    ("ra1_allies_alliedapc", "OpenRA Red Alert"): "APC",
    ("ra1_allies_reconranger", "Combined Arms"): "PBUL",      # Pitbull — a jeep that shoots rockets
    ("ra1_allies_sheridanassaulttank", "Combined Arms"): "RTNK",   # Mirage Tank
    # ⛔ NOT ("ra1_allies_alliedtigerheavytank", "Combined Arms"): "2TNK".
    # The maintainer asked which other 2TNK variants CA ships. The answer is NONE — there is
    # exactly one `2TNK`, and it is the Allied MEDIUM tank. Binding it to the Tiger took the
    # medium tank's own reference, which then took `1TNK` from the light tank, and BOTH fell out
    # of O1 while `1TNK` ended up assigned to nobody. One override, three units worse off.
    # The Tiger is a Cameo expansion with no CA counterpart, so it gets none: an empty slot is a
    # question, a stolen row is a wrong answer that also breaks two correct mappings.
    ("ra1_allies_bastionartillerybunker", "Combined Arms"): "HTUR",  # Grand Cannon
    # Red Alert, Soviets:
    # ⚠ CA ships TWO rows named "SAM Site" with identical faction lists — `NSAM` (Nod's) and `SAM`
    # (the Soviet one). The NAME cannot separate them and the id can, exactly like the AA Gun pair.
    ("ra1_soviets_samsite", "Combined Arms"): "SAM",
    ("td_nod_samsite", "Combined Arms"): "NSAM",
    ("ra1_soviets_zapper", "Combined Arms"): "TTRP",         # Tesla Trooper
    ("ra1_soviets_btr80", "Combined Arms"): "BTR",           # see the note below on flaktruck
    ("ra1_soviets_gatlingtank", "Combined Arms"): "BTR.YURI",   # the Gattling BTR
    ("ra1_soviets_gorynychtank", "Combined Arms"): "HFTK",      # Heavy Flame Tank
    ("ra1_soviets_hammertank", "Combined Arms"): "3TNK.RHINO",  # Rhino, not a flame tank
    ("ra1_soviets_nuclearv2launcher", "Combined Arms"): "NUKC", # Nuke Cannon
    ("ra1_soviets_hiptransport", "Combined Arms"): "HALO",
    ("ra1_soviets_su57attackbomber", "Combined Arms"): "SUK",   # Sukhoi Attack Plane

    # ── Round five, 2026-09-08. The maintainer named five rows I had reported as non-existent.
    # They all existed; they were invisible because the pool dropped every build-limited row.
    # `A10` is capped at 3 and `XO` at 1 — a cap is not a one-off, and only the second is a hero.
    ("td_gdi_firehawk", "DTA Enhanced"): "A10",       # A-10 Warthog, GDI, BuildLimit 3
    ("td_gdi_exosuit", "DTA Enhanced"): "XO",         # X-O Power Suit, GDI, BuildLimit 1
    ("td_gdi_empgrenadier", "DTA Enhanced"): "GRENL", # "Grenade Launcher", GDI
    ("td_nod_buggymkii", "DTA Enhanced"): "RAIDER",   # "Heavy Raider", Nod
    # MFLAK frees SHILKA for the Soviet gatling tank, so both get a real row and the
    # one-row-one-actor rule holds. The maintainer named this one; it is not a workaround.
    ("ra1_allies_alliedheavyaatank", "DTA Enhanced"): "MFLAK",   # "Anti-Aircraft Truck", Allies
    # …and the freed row lands on the unit it was freed for. `SHILKA` "Quad Tank" is the same
    # quad-AA chassis as the Gattling Tank; Soviet-tagged, admissible, and verified unclaimed
    # 2026-09-22 (the earlier `alliedheavyaatank -> SHILKA` line above this block was dead —
    # the dict kept only the maintainer's MFLAK ruling; the stale key has been removed).
    ("ra1_soviets_gatlingtank", "DTA Enhanced"): "SHILKA",

    # ── Round six, 2026-09-09. Aedis's DM 22:33 under Blackrobe's overnight authority: the
    # V1 Rocket Truck maps to Combined Arms' KATY and is renamed Katyusha for players. The
    # matcher can never find this pairing by itself — CA names the row "Katyusha", which shares
    # no word with `v1rockettruck` — and the actor currently holds no name-backed reference at
    # all (its greedy proposals were all struck). Verified before writing, per the override
    # contract: the row exists in the de-duplicated pool (Combined Arms, vehicle, hp 13000,
    # cost 750, factions include `soviet`), `faction_routes.allows("ra1_soviets", row)` admits
    # it, and NO actor held CA KATY in the regenerated assignment — so this displaces nobody.
    ("ra1_soviets_v1rockettruck", "Combined Arms"): "KATY",
}


def apply_overrides(result, by_source, routed_pool, routing):
    """Force the maintainer-ruled pairings, displacing whatever the greedy chose."""
    index = {}
    for src, plist in by_source.items():
        for p in plist:
            index[(src, (p.get("id") or "").upper())] = p
    apply_overrides.missing = missing = []
    for (cid, src), pid in REFERENCE_OVERRIDES.items():
        p = index.get((src, pid.upper()))
        if p is None:
            # ⛔ NEVER SILENT. A maintainer-ruled pairing whose peer id is absent from the routed
            # pool used to `continue` without a word, so a typo — or a row the routing refuses —
            # looked exactly like the matcher having chosen badly. Every override in the table was
            # verified present when written; if one stops resolving, that is a finding about the
            # POOL and it has to surface.
            missing.append((cid, src, pid))
            continue
        for other, srcs in result.items():
            d = srcs.get(src)
            if other != cid and d and (d.get("id") or "").upper() == pid.upper():
                if (pid.upper() == 'RMBO' and src in SHARED_COMMANDO_SOURCES
                        and cid in SHARED_COMMANDO_ACTORS and other in SHARED_COMMANDO_ACTORS):
                    continue
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
    # Global explicit overrides can survive assign(klass). They must not inflate
    # this class's summary while the actual table only displays its members.
    result = {actor: sources for actor, sources in result.items() if actor in members}

    def cost_of(n):
        v = (led[n].get("cost") or {})
        v = v.get("v") if isinstance(v, dict) else v
        try:
            return float(v)
        except (TypeError, ValueError):
            return None

    def display_score(value):
        return "—" if value is None else f"{value:.2f}"

    def display_order(pair):
        # Explicit overrides / id-agreement promotions need not have a computed
        # match score. Keep them visible without inventing numerical evidence.
        score = pair[1].get("score")
        return (score is None, -(score[0] or 0) if score else 0,
                -(score[3] or 0) if score else 0)

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
                                 key=display_order):
                if v["confidence"] in tier_set:
                    home = " **(home)**" if v["home"] else ""
                    score = v.get('score') or (None,) * 5
                    L.append(f"| ☐ | {v['confidence']} | `{m}` | {src}{home} | {v['name']} | "
                             f"{display_score(v.get('raw_name'))} | {display_score(score[3])} | {display_score(score[4])} |")
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
    filled = getattr(assign, "variant_filled", [])
    vc = getattr(assign, "variant_cameo", {})
    print(f"variant lane           : {len(filled)} filled of {len(vc)} Cameo variant actors "
          f"(chassis variants the population rule drops; derived from the base's pairing)")
    for cid, src, pid, pname, base, bid in filled:
        print(f"   + {cid:34s} {src:16s} {pid:12s} {str(pname)[:24]:24s} "
              f"via {base} -> {bid}")
    for cid, src, pid in getattr(apply_overrides, "missing", ()):
        print(f"⛔ OVERRIDE UNRESOLVED  {cid:38s} {src:24s} {pid}  — not in the routed pool")

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
