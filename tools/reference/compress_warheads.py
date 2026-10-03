#!/usr/bin/env python3
"""compress_warheads.py — collapse a reference mod's warheads into a few meaningful groups.

Maintainer order (2026-09-21): *"we need to compress all the reference mod weapons into groups.
For example 105mm / 120mm / 125mm can all be compressed into the Cannon Warhead ... so we should
try to compress it into as few groups as possible while still thinking about what makes sense.
Like for example the Obelisk Laser and the Laser Turret laser are very different weapons, right?
So they should not be compressed into a single laser ... Starting with CA as a pilot. Don't
compress too much at first ... only compress what is similar enough and you need to apply a
fitting name."*

The Obelisk example is not a new idea — it is DESIGN.md §12.0a, in the maintainer's own words
from 2026-08-15: *"there is a huge difference between the obelisk of light laser (which is a very
big laser) and the small laser from the laser turret."* So PLATFORM is a hard partition here, not
a tiebreak: two warheads never merge across platform bands however similar their shapes look.

THE THREE THINGS THAT DECIDE A MERGE
------------------------------------
1. **SHAPE, with magnitude removed.** Each profile is divided by its own geometric mean and read
   in log space, so `105mm` and `120mm` compare as *patterns* — "strong vs Heavy, weak vs None" —
   rather than as damage numbers. Magnitude is already carried separately by the warhead factor
   (`warhead_factors.json`), so folding it in here would split groups that differ only in how
   hard they hit, which is exactly what we do NOT want.
2. **PLATFORM.** Measured from the actors that actually fire the weapon, never from its name.
3. **COMPLETE LINKAGE.** A group is only formed when EVERY pair inside it is within the
   threshold, not merely every pair to its neighbour. Single-linkage would chain a long thin
   sequence of small differences into one enormous group — the classic way an automatic
   clustering quietly swallows the distinctions it was asked to preserve.

THE THRESHOLD IS SET BY MEASURED PURITY, NOT BY A PERCENTILE
------------------------------------------------------------
The first threshold, `0.50`, was chosen as "well below the 25th percentile" of Combined Arms'
pairwise shape distances (p25 0.351, median 0.542, max 1.820; log units, 0.10 ~ a 10% difference
per armour). That is a reasonable-sounding heuristic and it was too loose, which only became
visible once there was something to score against.

`validate_families.py` scores a grouping against the ONE labelled set in this lane: Cameo's own
904 weapons, each of which states its family by inheriting `^Warhead_<Family>_<Level>` (R37). The
question it asks of a threshold is *purity* — what share of a group belongs to its most common
family. Purity is the CEILING on any single-family label, so a loose threshold caps the review
before a human ever looks at it:

    tau    groups   median purity   >=80% pure   usage-weighted
    0.50      162         61%          11/53           53%
    0.30      241         67%          18/61           67%
    0.20      302         75%          29/71           77%
    0.10      413         89%          47/71           84%

At 0.50 a single group held a MEDIAN OF 3 distinct Cameo families (worst: 15) — no one label can
be right about a group like that. Usage weighting made it WORSE (53%), because the big groups are
the mixed ones, so reviewing "just the important ones" reviewed precisely the groups a single
label fits worst.

`DEFAULT_TAU = 0.20` (R41) buys 75% purity for 1,712 groups across all sources. 0.10 is purer
still and costs another 279 groups for +14 points; 0.20 is the knee, and it is where the maintainer
ruled.

⚠ MOVING THIS NUMBER INVALIDATES GROUP NAMES, NOT DECISIONS. Agglomerative clustering NESTS: a
tighter tau SUBDIVIDES the looser tau's groups rather than reshuffling them, so every reviewed
decision survives as long as it is carried by WEAPON MEMBERSHIP. `retau_assignment.py` does
exactly that — never re-apply an assignment file by group name after changing this.

    python tools/reference/compress_warheads.py --source combined_arms
    python tools/reference/compress_warheads.py --source combined_arms --tau 0.50
    python tools/reference/compress_warheads.py --all --write
"""
from __future__ import annotations

import argparse
import collections
import json
import math
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "reference"))
sys.path.insert(0, str(ROOT / "tools" / "audit"))

import warhead_matrix as wm  # noqa: E402

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

OUT = ROOT / "docs" / "reference" / "warhead_groups.json"

# Shape distance below which two warheads may merge, in log units. See the module docstring:
# this number is set by MEASURED PURITY against Cameo's own labelled weapons, not by taste.
DEFAULT_TAU = 0.20

# ── Platform bands ────────────────────────────────────────────────────────────────────────────
# A weapon's band is the band of the actors that FIRE it. This is what keeps the Obelisk apart
# from the laser turret: both are "laser", both may even have a similar profile, but one is fired
# by a big defence and the other by a small one, and §12.0a says that is a real difference.
# FOUR BANDS (maintainer ruling, 2026-09-21): infantry / vehicle / defense / aircraft.
#
# ⚠ THIS DELIBERATELY GIVES UP ONE DISTINCTION §12.0a NAMES BY HAND. Merging defense_small into
# defense_big puts the Obelisk and the laser turret in the same band, which is the very pair the
# law uses as its example. It was ruled anyway because the tail is tiny — defense_big carries
# 1.3% of CA's weapon slots — and because the SHAPE clustering may still separate them on its
# own. Where it does not, the split has to be re-introduced by hand. Ships fold into vehicles;
# the naval programme is deferred.
BAND_INF = "infantry"
BAND_VEH = "vehicle"
BAND_DEF = "defense"
BAND_AIR = "aircraft"
BAND_NONE = "unused"

# Retained only so an older grouping file still reads. Nothing produces them any more.
BAND_VEH_LIGHT = BAND_VEH
BAND_VEH_HEAVY = BAND_VEH
BAND_DEF_SMALL = BAND_DEF
BAND_DEF_BIG = BAND_DEF
BAND_SHIP = BAND_VEH

# Cost splits light from heavy within a band. Measured against CA's own roster rather than
# guessed: its vehicle costs run from a 300-credit bike to a 3500-credit Mammoth.
VEH_HEAVY_COST = 1200
DEF_BIG_COST = 1500


def _actor_band(actor, kind: str) -> str:
    """One actor's platform band. Four bands, per the 2026-09-21 ruling."""
    if kind == "INF":
        return BAND_INF
    if kind == "AIR":
        return BAND_AIR
    if kind == "BLD":
        return BAND_DEF
    return BAND_VEH          # vehicles and ships together


_KIND_HINTS = (
    ("infantry", "INF"), ("soldier", "INF"),
    ("ship", "SHIP"), ("boat", "SHIP"), ("submarine", "SHIP"),
    ("plane", "AIR"), ("helicopter", "AIR"), ("aircraft", "AIR"), ("jet", "AIR"),
    ("building", "BLD"), ("defence", "BLD"), ("defense", "BLD"), ("wall", "BLD"),
    ("vehicle", "VEH"), ("tank", "VEH"),
)


def _kind_of(rs, name: str) -> str:
    """Macro kind from the actor's own inheritance chain, not from its id."""
    seen: set[str] = set()
    stack = [name]
    while stack:
        current = stack.pop()
        if current in seen:
            continue
        seen.add(current)
        node = rs.actors.get(current)
        if node is None:
            continue
        for _, parent in rs.inherits_of(node):
            low = parent.lower()
            for hint, kind in _KIND_HINTS:
                if hint in low:
                    return kind
            stack.append(parent)
    return "VEH"


def weapon_bands(rs, slots: list[dict]) -> dict[str, str]:
    """{weapon: dominant platform band}, from the actors that fire it."""
    per_weapon: dict[str, collections.Counter] = collections.defaultdict(collections.Counter)
    cache: dict[str, str] = {}
    for slot in slots:
        actor_name, weapon = slot.get("actor"), slot.get("weapon")
        if not actor_name or not weapon:
            continue
        if actor_name not in cache:
            try:
                actor = rs.resolve(actor_name)
            except Exception:
                actor = None
            cache[actor_name] = (_actor_band(actor, _kind_of(rs, actor_name))
                                 if actor is not None else BAND_NONE)
        per_weapon[weapon][cache[actor_name]] += 1
    return {w: c.most_common(1)[0][0] for w, c in per_weapon.items()}


# ── Shape ─────────────────────────────────────────────────────────────────────────────────────

def shape_of(values: list[float | None]) -> list[float | None]:
    """The profile with its magnitude divided out, in log space.

    Absent for both kinds of missing cell: `0` (immune to this armour) and `None` (cannot target
    this armour's macro class at all — see the Aircraft-148 note in warhead_matrix).
    """
    live = [v for v in values if v is not None and v > 0]
    if not live:
        return [None] * len(values)
    centre = math.exp(sum(math.log(v) for v in live) / len(live))
    return [math.log(v / centre) if (v is not None and v > 0) else None for v in values]


def shape_distance(a: list[float | None], b: list[float | None]) -> float:
    """RMS log difference over the armours BOTH profiles have an opinion about.

    An armour one profile is immune to and the other is not carries no comparable information,
    so it is skipped rather than scored as an infinite gap. Two profiles that share no comparable
    armour at all are never merged.
    """
    pairs = [(x - y) ** 2 for x, y in zip(a, b) if x is not None and y is not None]
    if not pairs:
        return math.inf
    return math.sqrt(sum(pairs) / len(pairs))


# ── Delivery, from the weapon's PROJECTILE — measured, not guessed from the name ──────────────
# ⛔ THE FIRST VERSION OF THIS FILE GUESSED THE FAMILY FROM THE WEAPON'S NAME, and it was wrong
# in exactly the way CLAUDE.md warns about. A name regex put `InterloperLaser` into a group called
# `Cannon_LightVeh` and `135mm` into one called `Laser_HeavyVeh`, because the group's name was
# voted by whichever member happened to match first. The weapon's `Projectile:` is real data the
# engine acts on, so it is the delivery signal.
DELIVERY = {
    "Bullet": "Bullet", "BulletCA": "Bullet",
    "MissileCA": "Missile", "Missile": "Missile",
    "LaserZapCA": "Laser", "LaserZap": "Laser", "ArcLaserZap": "Laser", "PlasmaBeam": "Laser",
    "TeslaZapCA": "Tesla", "TeslaZap": "Tesla", "ElectricBolt": "Tesla",
    "LinearPulse": "Spray",          # flamers and chem sprays
    "GravityBomb": "Bomb", "NukeLaunch": "Bomb",
    "AreaBeamCA": "Sonic", "AreaBeam": "Sonic",
    "RadBeam": "Radiation",
    "RailgunCA": "Railgun", "Railgun": "Railgun",
    "InstantHit": "Hitscan",
    # ── The other sources' own projectile TRAITS ──────────────────────────────────────────────
    # A mod that ships its own projectile implementation names the trait after itself, not after
    # the weapon class: Shattered Paradise and Romanov's Vengeance use the Attacque Suprême
    # library (`BulletAS`, `MissileTA`), Crystallized Nexus has `InstantHitWithFakeBullets` and
    # `CNLaserZap`, Twisted Insurrection `SpriteRailgun`. Left unmapped they pass through raw and
    # look like 118 brand-new delivery kinds with no precedent anywhere, which is how a purely
    # mechanical propagation ends up asking for rulings it does not need.
    "BulletAS": "Bullet", "ScaledBullet": "Bullet", "Bullet2": "Bullet",
    "MissileTA": "Missile", "MissileAS": "Missile", "Rocket": "Missile",
    "InstantHitWithFakeBullets": "Hitscan", "InstantHitAS": "Hitscan",
    "KKNDLaser": "Laser", "CNLaserZap": "Laser", "LaserZapAS": "Laser",
    "SpriteRailgun": "Railgun",
    "LightningZap": "Tesla",
    "SonicBlast": "Sonic", "Sonic": "Sonic",
}
# Projectiles that are not weapons in any useful sense: support-power explosions, husk debris and
# the cloud spawner. Their "warheads" are crate effects, unit death explosions and targeting
# dummies, and they were the whole content of the first run's `Undifferentiated_*` groups.
DELIVERY_EXCLUDE = {"InstantExplode", "ProjectileHusk", "AthenaProjectile"}

# ── ELEMENT, from the warhead's own `DamageTypes` — the second half of a Cameo warhead ────────
#
# Maintainer, 2026-09-21: *"a lot of the groups mixed many different deliveries and elements
# together so they couldn't be used at all"* — and *"there were several cameo warheads I could not
# realistically map like cryo or prism because there simply was no group with those even though
# they exist."*
#
# Both are the same omission. Delivery came from `Projectile:`, which says HOW a weapon reaches
# its target and nothing about WHAT it does on arrival — so `ChemicalMortar`, `CryoMortar` and
# `105mm` all read as `Bullet` and landed in one group. A Cameo warhead is delivery x ELEMENT
# (CannonAP, MissileCryo, BulletTesla), so the element has to be in the key.
#
# `DamageTypes` is where the engine records it, and it is unusually clean: `FrozenDeath` is the
# Cryo the maintainer could not find, `RadiationDeath` the Radiation they want as a new family,
# and `TankBuster` is literally the armour-piercing marker. Ordered specific-first, because a
# warhead legitimately carries several (`ExplosionDeath, TankBuster` is AP, not HE).
# ⚠ MOST `*Death` TOKENS ARE DEATH ANIMATIONS, NOT ELEMENTS. `FireDeath` means "the victim plays
# the burning death sequence", which CA's `HonestJohn` rocket artillery and `155mmSpec` both use —
# neither is a fire weapon. Reading it as an element produced a group called `LaserFire_Veh`
# containing `PointLaser` and `AvatarLaser`. So Fire requires the real tag, `Incendiary`.
#
# The tokens below split into STRONG signals — tags the engine acts on, or death types no ordinary
# weapon would claim — and WEAK ones, which only separate an explosive payload from a solid slug
# and are allowed to stand in when nothing stronger is present.
ELEMENT_ORDER = [
    # strong: a real damage tag, or a death type unique to that element
    ("Cryo", "FrozenDeath"),
    ("Radiation", "RadiationDeath"),
    # R54 - the same animation in a different palette. RV pairs them explicitly, warhead by
    # warhead: NukePayload/NukePayloadOrange, atomic/atomicOrange, FalloutBomb/FalloutBombOrange,
    # RadBeamWeapon/RadBeamWeaponOrange. All 8 carriers are the Orange twin of a RadiationDeath
    # weapon, so the pair read as two different elements until now.
    ("Radiation", "OrangeRadiationDeath"),
    ("Toxin", "ToxinDeath"),
    # R45 - THE SAME ELEMENT IS SPELLED DIFFERENTLY IN DIFFERENT MODS. Combined Arms writes
    # `ToxinDeath` (20 uses, `TiberiumDeath` 0); Cameo writes `TiberiumDeath` (381 uses across
    # resolved warheads, `ToxinDeath` 0). Mapping only one spelling meant NEITHER labelled source
    # ever produced a single group classified Toxin -- including the `*Chem` families whose whole
    # identity is that element. `RA2VirusDeath` joins them because defaults.yaml groups all three
    # under one death voice (`DeathSounds@POISONED`), which is the mod stating they are one thing.
    ("Toxin", "TiberiumDeath"),
    ("Toxin", "RA2VirusDeath"),
    # R54 - a FOURTH and FIFTH spelling of the same element, found the same way R45 found the
    # third: by censusing every `*Death` token in every source against the two lists below.
    # Romanov's Vengeance writes `VirusDeath` (36 nodes / 24 weapons) and Combined Arms writes
    # `PoisonDeath` (10 / 8). Every RV carrier is a toxin weapon without exception -- ToxinSprayer,
    # Virusgun, PoisonSting, ToxinBomb, ToxinSplash, CloudDamage, GasCrateExplode, MosquitoMissile
    # -- and RV had ZERO Toxin groups before this, which is the giveaway: a mod with a whole Yuri
    # chemical arsenal cannot have no chemical weapons. CA's carriers are ChemDebris, CorrupterSpew,
    # VirusCloud, UnitExplodeChemSmall and `SNIPER.ASSA`, the Assassin, whose own warhead spawns a
    # `viruscloud` actor -- read, not assumed. ⚠ ONE doubtful row: CA's `FireDebris`, a napalm
    # debris shard sitting directly beside `ChemDebris` in the same file, carries `PoisonDeath`
    # too and now reads Toxin. It looks like an authoring slip in CA rather than a design
    # statement, and it is left alone here because CA's review is the MAINTAINER's.
    ("Toxin", "VirusDeath"),
    ("Toxin", "PoisonDeath"),
    ("Tesla", "ElectricityDeath"),
    ("Atomized", "AtomizedDeath"),
    ("Fire", "Incendiary"),
    ("AP", "TankBuster"),
    # weak: explosive payload vs solid slug, used only when no strong signal is present
    ("HE", "ExplosionDeath"),
    ("HE", "SmallExplosionDeath"),
    ("Kinetic", "BulletDeath"),
]
# Carried by most warheads and saying nothing about the element: prone modifiers, the generic and
# the burning death animations, the flak-vest interaction, and the air-to-ground marker.
# R45 - CENSUSED, not guessed. Every token in the corpus was counted against this table; the
# ones below say nothing about the element. An UNMAPPED token is not harmless: `element_of`
# subtracts the noise and then takes the first ELEMENT_ORDER hit, so a warhead carrying an
# unmapped element token ALONGSIDE a mapped one is actively MISLABELLED as the mapped one
# (a chem shell with `TiberiumDeath, ExplosionDeath` read as HE), not merely missed.
# The prone variants were the biggest omission: `Prone75Percent` alone occurs 8,055 times and
# only `Prone50Percent` was listed. `RippedApartDeath` is `Sniper`'s death ANIMATION, and the
# spawn/infection/mutate tokens are gameplay mechanics.
#
# R54 - ⚠ ADDING A TOKEN HERE CHANGES NO CLASSIFICATION. `element_of` subtracts this set and then
# looks for an ELEMENT_ORDER hit, so a token that is in NEITHER list already loses every time;
# NOISE and UNMAPPED are behaviourally identical. What this set records is that a token was
# CENSUSED AND JUDGED, which is the only thing that stops the next census redoing the work. The
# second block below is that census, taken across all eight OpenRA rulesets:
#   `FlameDeath` (RV, 61 weapons) is the single most tempting miss in the corpus and it is NOT an
#   element. It is on the flamethrowers, yes — but also on CurtainRifle, PsychicJab, MirageGun,
#   IonCannon, DerrickExplode and every barrel explosion: 17 of 61 carriers do not burn anything.
#   It is the burned-corpse animation, exactly like `FireDeath` one line above, and RV's fire
#   weapons are identified by profile and name instead (R55).
#   `ElectroDeath` (RV, 73) is the same trap wearing the opposite element: ElectricBolt, CoilBolt,
#   TeslaFence — and PrismShot, PrismSupport, Comet, DiskLaser. Mapping it to Tesla would have
#   bought nothing (every real tesla weapon already reads Tesla from its DELIVERY) and cost the
#   Prism tower, which is not an electric weapon by any reading.
#   `EnergyDeath` (SP 70, CN 10, TS 4) spans lasers, plasma, ion, railgun, tesla AND artillery —
#   one animation over four elements, so it names none of them.
#   `PsychicDeath` (RV 24, Cameo 17) is carried by PsiWave and PsychicDomination but also by
#   CRNuke, IvanBomber, SealC4 and TanyaC4: the no-corpse animation, not mind control.
#   `BruteDeath` (12) is melee — Punch, Smash, SlimeAttack — the `RippedApartDeath` of this mod.
#   `MutationDeath`/`MutatedDeath`/`CabalDeath*`/`ChronoDeath` are mechanics or one-weapon
#   animations, each under 6 carriers; `AtomizedDeath` already carries the signal ChronoDeath
#   might be mistaken for.
ELEMENT_NOISE = {"Prone50Percent", "Prone60Percent", "Prone75Percent", "Prone100Percent",
                 "TriggerProne", "DefaultDeath", "DefaultDeathwc2", "FireDeath",
                 "FlakVestMitigated", "FlakVestMitigatedMinor", "AirToGround", "Repairable",
                 "RippedApartDeath", "SoundDeath",
                 "KillsDrone", "DroneInfection", "SuppressDrone", "RemovesSquid",
                 "SwarmlingSpawn", "QueenBroodlingSpawn", "ContaminatorMutate", "QuestionMutate",
                 # R54 census - death ANIMATIONS and mechanics, verified against their carriers
                 "FlameDeath", "ElectroDeath", "EnergyDeath", "PsychicDeath", "BruteDeath",
                 "MutationDeath", "MutatedDeath", "ChronoDeath", "CabalDeath", "CabalDeathUpg"}


def element_of(damage_types: str) -> str:
    tokens = {t.strip() for t in (damage_types or "").split(",") if t.strip()}
    tokens -= ELEMENT_NOISE
    for element, token in ELEMENT_ORDER:
        if token in tokens:
            return element
    return "Plain"

BAND_SHORT = {
    BAND_INF: "Inf", BAND_VEH: "Veh", BAND_DEF: "Def",
    BAND_AIR: "Air", BAND_NONE: "Unused",
}


def group_name(delivery: str, element: str, band: str, flat: bool) -> str:
    """`<Delivery><Element>_<Band>` — the same grammar a Cameo warhead family uses."""
    # `Radiation` delivery carrying a `Radiation` element must not become "RadiationRadiation".
    if element in ("Plain", "") or element == delivery:
        core = delivery
    else:
        core = f"{delivery}{element}"
    return f"{core}_{BAND_SHORT.get(band, band)}"


# ── Clustering ────────────────────────────────────────────────────────────────────────────────

def cluster(rows: list[dict], tau: float) -> list[list[dict]]:
    """Complete-linkage agglomeration: every pair inside a group is within `tau`.

    Greedy and order-independent because rows are pre-sorted by usage then name, so the same
    input always yields the same groups — a clustering a maintainer has to review by hand must
    not move between runs.
    """
    ordered = sorted(rows, key=lambda r: (-r["uses"], r["name"].lower()))
    groups: list[list[dict]] = []
    for row in ordered:
        placed = False
        for group in groups:
            if all(shape_distance(row["_shape"], other["_shape"]) <= tau for other in group):
                group.append(row)
                placed = True
                break
        if not placed:
            groups.append([row])
    return groups


def weapon_damage_types(rs) -> dict[tuple[str, str], str]:
    """{(weapon, warhead node key): its `DamageTypes`}, resolved through inheritance."""
    out: dict[tuple[str, str], str] = {}
    for name in rs.weapons:
        if name.startswith("^") or name.startswith("-"):
            continue
        try:
            weapon = rs.resolve_weapon(name)
        except Exception:
            continue
        if weapon is None:
            continue
        for node in weapon.children:
            if node.key == "Warhead" or node.key.startswith("Warhead@"):
                out[(name, node.key)] = node.get("DamageTypes") or ""
    return out


def weapon_projectiles(rs) -> dict[str, str]:
    """{weapon: its `Projectile:` type}, resolved through inheritance."""
    out: dict[str, str] = {}
    for name in rs.weapons:
        if name.startswith("^") or name.startswith("-"):
            continue
        try:
            weapon = rs.resolve_weapon(name)
        except Exception:
            continue
        if weapon is None:
            continue
        node = weapon.child("Projectile")
        out[name] = (node.value or "").strip() if node is not None else ""
    return out


def compress(sid: str, entry: dict, tau: float) -> dict:
    from miniyaml import Ruleset
    bands: dict[str, str] = {}
    projectiles: dict[str, str] = {}
    damage_types: dict[tuple[str, str], str] = {}
    # ⚠ CAMEO IS A SOURCE TOO and it is not in `OPENRA_SOURCES` — that list is the REFERENCE mods,
    # and looking the sid up there silently left Cameo's own groups with delivery `Unknown` and
    # band `unused`, i.e. uncompressible. R20 and R30 both give Cameo a vote, so it needs the same
    # signal extraction as everyone else, from this repository's own ruleset.
    lookups = [(source_id, root, mod_id) for source_id, _, root, mod_id in wm.OPENRA_SOURCES]
    lookups += [("cameo", wm.ROOT, "cameo"), ("cameo_resolved", wm.ROOT, "cameo")]
    for source_id, root, mod_id in lookups:
        if source_id == sid:
            rs = Ruleset(root, mod_id)
            bands = weapon_bands(rs, entry.get("slots", []))
            projectiles = weapon_projectiles(rs)
            damage_types = weapon_damage_types(rs)
            break

    # ── ONE ROW PER WEAPON — now done UPSTREAM, by folding ───────────────────────────────────
    #
    # Maintainer, 2026-09-21, on several groups: *"these are many different things that have
    # nothing to do with each other"*. A large part of that was not clustering at all — it was
    # every warhead NODE entering as if it were a separate weapon. 116 of Combined Arms' 466
    # armed weapons carry more than one damage warhead; entering all of them put one weapon in
    # three groups and filled the generalist buckets with fragments. Cameo's own §11b says the
    # same thing about our side: one warhead per weapon.
    #
    # ⚠ THIS USED TO PICK ONE WARHEAD AND DISCARD THE REST, keyed on the name `Warhead@1Dam`,
    # and that was wrong in a way the maintainer caught four times in one review ("why is light
    # immune? … how is the damage so low against None? … none immune is a bug"). In Combined
    # Arms the extra warheads are routinely COMPLEMENTARY rather than twins — each covers the
    # armour classes the other zeroes out — so discarding them reported false immunities.
    # `warhead_matrix.fold_by_weapon` now sums them by effective damage BEFORE normalisation,
    # and the rows arriving here are already one per weapon. Do not re-introduce a picker.
    armors = entry["armors"]
    kept, skipped = [], collections.Counter()
    for row in entry["rows"]:
        # ⛔ ONLY WEAPONS SOMETHING ACTUALLY FIRES. A warhead with no buildable actor behind it is
        # a crate effect, a death explosion, a targeting dummy or a support power — it has no
        # place in a roster's damage vocabulary, and including it produced groups of 50 whose
        # members were `Heal`, `EnslaveInfantry` and `MineDefuser`.
        if row["uses"] <= 0:
            skipped["no firing actor"] += 1
            continue
        raw_projectile = projectiles.get(row["weapon"], "")
        if raw_projectile in DELIVERY_EXCLUDE:
            skipped[f"projectile {raw_projectile}"] += 1
            continue
        row["_shape"] = shape_of(row["values"])
        row["_band"] = (row.get("band")
                        or (bands.get(row["weapon"], BAND_NONE) if row["weapon"] else BAND_NONE))
        # ⚠ FLAT ONLY COUNTS WHEN THERE WAS SOMETHING TO BE FLAT ACROSS.
        # An anti-air weapon now has every ground cell marked N/A, so its surviving Aircraft
        # cells are trivially equal and the row reads as "flat" — which would sweep every AA
        # weapon in the mod into one Generalist bucket. The maintainer called that out directly:
        # *"this seems like a lazy approach to have all the anti air defenses have the same versus
        # values which we will not do! We want it unique for each type."* Flatness is only a
        # design statement when the warhead actually spans more than one macro class; otherwise
        # the row keeps its delivery and element and is separated by those.
        live_macros = {wm.ARMOR_MACRO.get(a.lower(), "GND")
                       for a, v in zip(armors, row["_shape"]) if v is not None}
        row["_flat"] = (len(live_macros) >= 2
                        and all(v is None or abs(v) < 1e-9 for v in row["_shape"]))
        row["_single_class"] = len(live_macros) < 2
        # A row that already KNOWS its delivery states it — that is the INI path, where the
        # signal comes from weapon flags and projectile behaviour rather than a `Projectile:`
        # node (warhead_matrix.ini_delivery). OpenRA rows leave it unset and are read here.
        row["_delivery"] = (row.get("delivery")
                            or DELIVERY.get(raw_projectile, raw_projectile or "Unknown"))
        # The element comes from `DamageTypes`, keyed by (weapon, NODE). A FOLDED row stands for
        # several nodes at once and has no node of its own, so union their damage types and let
        # ELEMENT_ORDER's priority decide — a weapon whose warheads are Incendiary and
        # ExplosionDeath is a fire weapon, not a generic explosive one.
        if row.get("element"):
            row["_element"] = row["element"]
        else:
            nodes = row.get("folded_from") or [row["node"]]
            row["_element"] = element_of(
                ", ".join(damage_types.get((row["weapon"], n), "") for n in nodes))
        kept.append(row)

    # ── DELIVERY x PLATFORM is the primary key; shape only SPLITS within it ───────────────────
    # This is the order the maintainer described: "105mm / 120mm / 125mm can all be compressed
    # into the Cannon Warhead" (one delivery, one platform) but "the Obelisk Laser and the Laser
    # Turret laser are very different weapons" (one delivery, two platforms — DESIGN.md §12.0a).
    # Shape-first did the opposite: it merged a cannon with a laser because their armour profiles
    # happened to agree, which is not a thing either of them would recognise.
    # ── Flat profiles collapse to ONE generalist group per band (ruling, 2026-09-21) ──────────
    # A warhead that states no `Versus` deals 100 to everything, which IS a design statement:
    # "this weapon does not care what it hits". But it says nothing about DELIVERY, so splitting
    # it by delivery invents a distinction the data does not contain — CA was producing
    # Missile_Veh_Flat (47), Bullet_Veh_Flat (14), Laser_Veh_Flat (8) and Hitscan_Veh_Flat (14)
    # as four separate groups with byte-identical profiles. One `Generalist_<band>` instead.
    groups: list[dict] = []
    buckets: dict[tuple[str, str, str, bool], list[dict]] = collections.defaultdict(list)
    for row in kept:
        delivery = "Generalist" if row["_flat"] else row["_delivery"]
        buckets[(delivery, row["_element"], row["_band"], row["_flat"])].append(row)

    for (delivery, element, band, flat), rows in sorted(buckets.items()):
        for members in cluster(rows, tau):
            groups.append({
                "name": group_name(delivery, element, band, flat),
                "delivery": delivery,
                "element": element,
                "band": band,
                "flat": flat,
                "members": len(members),
                "uses": sum(m["uses"] for m in members),
                "factor": wm.gmean([m["factor"] for m in members if m["factor"] > 0]),
                # ⚠ weapon AND node: a weapon with two damage warheads legitimately lands in
                # two groups, and showing only the weapon makes those look like duplicates.
                "examples": [f'{m["weapon"]}:{m["node"]}' if m["weapon"] else m["node"]
                             for m in members[:8]],
                "weapons": sorted({m["weapon"] or m["node"] for m in members}),
                # The group's own armour row, and the thing a reviewer actually reads. Geometric
                # mean per column, because these are multipliers; `None` only where EVERY member
                # is n/a, so a group stays honest about what it cannot target (R16).
                # ⚠ FILTER TO POSITIVE, not merely to non-None. `gmean` treats a zero as an
                # ABSENCE (the maintainer's ruling: zeros are "not applicable") and returns NaN
                # when every value it is handed is absent. A column whose members all deal a
                # literal zero is non-empty but carries no multiplier, so guarding only on
                # emptiness wrote NaN into four groups' profiles and it propagated downstream.
                "profile": [
                    (round(wm.gmean(col), 1) if (col := [m["scaled"][i] for m in members
                                                         if (m["scaled"][i] or 0) > 0]) else None)
                    for i in range(len(armors))
                ],
                "armors": armors,
            })

    # A name can legitimately come up twice (two distinct Cannon shapes on heavy vehicles).
    # Number them rather than merging, which would undo the split the clustering just made.
    seen: collections.Counter = collections.Counter()
    for group in sorted(groups, key=lambda g: -g["uses"]):
        seen[group["name"]] += 1
        if seen[group["name"]] > 1:
            group["name"] = f"{group['name']}_{seen[group['name']]}"

    groups.sort(key=lambda g: (-g["uses"], g["name"]))
    return {"source": sid, "tau": tau, "rows": len(entry["rows"]),
            "compressed": len(kept), "skipped": dict(skipped),
            "groups": groups, "group_count": len(groups)}


def report(result: dict, limit: int = 40) -> str:
    skipped = sum(result["skipped"].values())
    lines = [f"## {result['source']}  —  {result['rows']} warheads, "
             f"{result['compressed']} compressible ({skipped} skipped) → "
             f"**{result['group_count']} groups**  (tau {result['tau']})", "",
             "skipped: " + ", ".join(f"{k} {v}" for k, v in
                                     sorted(result["skipped"].items(), key=lambda x: -x[1])), "",
             "| group | band | members | uses | factor | examples |",
             "|---|---|--:|--:|--:|---|"]
    for group in result["groups"][:limit]:
        examples = ", ".join(group["examples"][:5])
        factor = f"{group['factor']:.2f}" if group["factor"] == group["factor"] else "-"
        lines.append(f"| `{group['name']}` | {group['band']} | {group['members']} | "
                     f"{group['uses']} | {factor} | {examples} |")
    if len(result["groups"]) > limit:
        lines.append(f"| … | | | | | _{len(result['groups']) - limit} more groups_ |")
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", default="combined_arms")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--tau", type=float, default=DEFAULT_TAU)
    ap.add_argument("--limit", type=int, default=40)
    ap.add_argument("--write", action="store_true")
    args = ap.parse_args()

    data = wm.collect()
    targets = list(data) if args.all else [args.source]
    out = {}
    for sid in targets:
        if sid not in data:
            print(f"unknown source {sid}; known: {', '.join(data)}")
            return 2
        result = compress(sid, data[sid], args.tau)
        out[sid] = result
        print(report(result, args.limit))
        print()

    if args.write:
        # ⚠ R54 - `--write` REPLACES the file, it does not merge, and `--source` DEFAULTS to
        # combined_arms. So a bare `--write` wrote one source's 182 groups over all twenty and
        # said only "wrote docs/reference/warhead_groups.json" — 1,499 groups and every other
        # source's measured payload gone, with a zero exit code. The same defect class as the
        # splice writer and the `tolerance`-as-a-fraction claims: a destructive default that
        # cannot report that it did something unintended. `--write` now requires `--all`.
        if not args.all:
            raise SystemExit(
                f"refusing to write: --write replaces every source in {OUT.name}, and this run "
                f"measured only {args.source!r}. Re-run with --all --write, or drop --write.")
        OUT.write_text(json.dumps(out, indent=1, sort_keys=True, default=float) + "\n",
                       encoding="utf-8")
        print(f"wrote {OUT.relative_to(ROOT)}  ({sum(len(v['groups']) for v in out.values())} "
              f"groups across {len(out)} sources)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
