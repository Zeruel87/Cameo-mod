#!/usr/bin/env python3
"""ONE armament = ONE reference. The pairing key that stops a cannon being averaged with a missile.

⛔ THE MAINTAINER'S ORDER (2026-09-13), in full, because every line below implements one clause:

    "we need to be careful because those fire bombs and the sidewinder anti air missiles have
     separate ranges ... Those two weapons are so different they should not be mixed. actually
     this should be true for any dual or multi weapon units so the correct weapon is mapped ...
     you need to separate those two weapons, use DTA for the missile as reference only while
     using the cannon reference from all 3! Adjust all the existing units with that logic!"

THE CASE, MEASURED, so nobody has to take the defect on trust (`td_gdi_firehawk`):

    Armament            td_gdi_firehawk_firehawkmissiles_AA   role=air      range 12500
    Armament@BOMBS      td_gdi_firehawk_firehawkbomb          role=ground   range  1250

A TEN-FOLD range gap inside one actor. `armament_profile` reports `max(ranges)`, so whichever
survives the fold hands the other one its number. The same shape sits on every mammoth:

    td_gdi_mammothtank  120mmdual  role=ground  |  mammothmissiles  role=both

⭐ AND THE REFERENCES ALREADY SEPARATE THE SAME WAY, which is why this is a pairing problem and
not an extraction problem — no corpus needs regenerating (measured 2026-09-13):

    CA   4TNK  130mm      ground 4864  |  MammothTusk      Air,AirSmall,Infantry   both 6656
    CnC  HTNK  120mmDual  ground 4864  |  MammothMissiles  Ground,Water,Air        both 4864
    RA   4TNK  120mm      ground 4864  |  MammothTusk      AirborneActor,Infantry  both 6656

Three sources, three cannons, three missiles, and the roles line up without a single name match.

────────────────────────────────────────────────────────────────────────────────────────────────
THE ROLE VOCABULARY IS NOT NEW — IT IS THE MAINTAINER'S MISSILE RULING (2026-09-07), REUSED:

    ground only  ->  MissileHE        air only  ->  MissileAA        both  ->  MissileAP

`audit_missile_role_family.weapon_role` already implements it for the audit. This module does NOT
replace it and must never be merged into it: that audit carries four LOWER-ONLY ratchets, so it
fails CLOSED to "custom" the moment a weapon's ValidTargets holds any token outside
{Ground, Water, Air} — correct for a ratchet, useless for pairing, because "Ground, Water, Trees"
is 31 CA armaments and "AirborneActor, Infantry" is the entire Red Alert mammoth missile.

So this classifier reads a WIDER, explicitly enumerated vocabulary and still fails closed on
anything it has not seen. `test_armament_roles` pins that the two AGREE on every weapon the audit
is willing to judge; the wider set may only add answers, never change one.

⚠ IT ALSO SUPERSEDES `reference_distribution.is_anti_air_armament` FOR PAIRING ONLY. That helper
tests the NAME (`@AA`, `_AA`) and is left exactly as it is — it is load-bearing for the existing
baseline selection. But the name test cannot see 50 air-role armaments spelled otherwise
(`RA2Patriot`, `RA2TURRETFLAKAA`, `AsianPhotonCannon`, `PortableFlak`, `BallistaSingleShotAir`),
measured 2026-09-13, and a name blocklist is the mistake this codebase has paid for repeatedly.
The targeting envelope is the SOURCE; the slot spelling is a convention.
"""
from __future__ import annotations

import math
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "audit"))

ROLE_GROUND = "ground"
ROLE_AIR = "air"
ROLE_BOTH = "both"
ROLE_SPECIAL = "special"          # neither domain survives — an interceptor, a healer, a snare
ROLES = (ROLE_GROUND, ROLE_AIR, ROLE_BOTH, ROLE_SPECIAL)

# ── THE TOKEN SETS, MEASURED 2026-09-13 OVER BOTH CORPORA, NEVER GUESSED ─────────────────────
# Cameo resolves 59 distinct ValidTargets tokens and 37 InvalidTargets tokens; the OpenRA peer
# corpus adds 38 more. Every token either places the weapon in a DOMAIN or it does not; a token
# that does not is NEUTRAL and must not tilt the answer either way, which is why the three sets
# are written out instead of "anything not air is ground".
AIR_TARGETS = frozenset({
    "Air", "AirSmall", "AirborneActor", "Aircraft",
})

GROUND_TARGETS = frozenset({
    "Ground", "Water", "Underwater", "Trees", "GroundActor", "WaterActor",
    "Infantry", "Vehicle", "Structure", "Building", "Ship", "Submarine", "Bridge",
    "Wall", "wall", "Defense", "Barrel", "Husk", "Cyborg", "Monster", "Tank",
    "NavalYard", "TeslaCoil", "Epic", "Garrisoned", "Ant", "Paratrooper", "Hero",
    "MADTank", "Mine", "Broodling",
})

# Selectors and status markers. `Missile` / `ICBM` / `BallisticMissile` are here deliberately: a
# point-defence laser reads `Ground, Water, Missile` and is a GROUND weapon that also swats
# rockets, while a weapon that targets ONLY missiles belongs to neither domain and must land in
# ROLE_SPECIAL rather than be mislabelled as air. Membership here asserts "carries no domain".
NEUTRAL_TARGETS = frozenset({
    "Missile", "ICBM", "BallisticMissile", "Bullet", "BulletAS",
    "Repairable", "Repair", "Repairing", "SpecialRepair", "Heal", "Healable",
    "Healing", "HealableCyborg", "NoCrew", "Resupplying",
    "C4Attached", "C4Plantable", "TNTAttached", "TNTPlantable",
    "MindControllable", "MindControl", "MindControlStructure", "Psionic",
    "Hackable", "HackableRobot", "Chronobeamable", "Temporal", "Shielded", "shielded",
    "TerrorDronable", "terrordroned", "SquidGrab", "SquidGrabbed", "DiskSteal",
    "PrismTowerChargeable", "TeslaBoost", "RobotEnergizable", "PowerDrainable",
    "ResourceDrainable", "DetonateAttack", "WatcherParasiteAttachable",
    "LeechEggLaid", "LeechEggKill", "SlaveFaster", "BlackHole",
    "ivanattached", "ivanattachable", "lockdowned", "lockable", "lockon", "plagued",
    "blindable", "snareable", "demolishable", "bloodlust_target", "haste_target",
    "undeadtarget", "wc2_runes", "plymouth_minv", "StickyFoamed",
    "ToxinImmune", "MCImmune", "DogImmune", "DevourImmune",
})

# ⛔ `WeaponInfo.cs:116` — a weapon that never writes ValidTargets is `Ground, Water`, i.e. GROUND.
# Absence is a VALUE here, not a gap, and both corpora lean on it: 451 of the ~900 peer armaments
# and the majority of Cameo weapons leave it unwritten.
ENGINE_DEFAULT_TARGETS = "Ground, Water"


def _tokens(raw):
    return {t.strip() for t in str(raw or "").split(",") if t.strip()}


def role_of_targets(valid, invalid=None):
    """(role, unknown_tokens) from a weapon's targeting envelope.

    `valid` None/empty means the engine default, NOT "unknown" — see ENGINE_DEFAULT_TARGETS.

    ⛔ AN UNKNOWN TOKEN MAKES THE VERDICT `None`, NOT A CONFIDENT ROLE (Astra, PR #375 blocker 5).
    Unknown tokens used to be returned alongside a role and treated as NEUTRAL, so
    `Ground, UnknownFlyingTarget` came back a proven exact `ground` — the one shape the maintainer
    forbade, an air weapon standing in as ground evidence. Treating an unrecognised token as
    neutral is a guess that a new marker cannot change a weapon's domain, and the whole reason
    this classifier reads FLAGS instead of names is that such guesses are wrong: DTA's
    `AGHeatSeeker2` says "AG" in its name and declares `AA=yes`.

    So the vocabulary now fails CLOSED. A weapon carrying a token this module does not know
    abstains, and `pair_by_role` gives it no vote at all. The tokens are still returned, because
    `--audit` proves the vocabulary covers the corpus and the count must stay visible — it is 0
    today, which is exactly when a guard is cheap to install.

    Maintainer, 2026-09-13: *"ambiguous role or identity must abstain."*
    """
    targets = _tokens(valid) or _tokens(ENGINE_DEFAULT_TARGETS)
    targets -= _tokens(invalid)
    unknown = targets - AIR_TARGETS - GROUND_TARGETS - NEUTRAL_TARGETS
    if unknown:
        return None, unknown
    air = bool(targets & AIR_TARGETS)
    ground = bool(targets & GROUND_TARGETS)
    if air and ground:
        return ROLE_BOTH, unknown
    if air:
        return ROLE_AIR, unknown
    if ground:
        return ROLE_GROUND, unknown
    return ROLE_SPECIAL, unknown


# ── THE ONE RATE FORMULA, ONE IMPLEMENTATION ─────────────────────────────────────────────────
# ⭐ THE BURST FOLD AT THE CONSUMPTION POINT (maintainer ruling, 2026-09-14: *"if there is no
# burst delay you can use the minimal allowed value of 1 ticks between the bursts"*).
#
# ⛔ WHY THE RULING IS APPLIED HERE AND NOT IN THE CORPUS. `burst_unfolded` was never a claim
# that the declaration was unreadable - damage, reload, range and burst are all present and
# certified. It was a refusal to INVENT a cycle for shots the INI engines cannot time, and its
# own comment said it stood "until a cycle model exists". The ruling supplies that model. The
# corpus itself stays frozen: regenerating `ini_corpus.json` today DROPS the dummy-primary
# promotion on 63 rows (see `extract_ini_units.EXPLICIT_DUMMY_WEAPONS`), so the fold is applied
# where the declaration is READ instead of where it is stored. When that reviewed regeneration
# finally lands, the extractor emits `nominal_direct` with the same folded rate and this path
# simply stops firing - the two orders agree by construction.
#
# ⚠ ONE TICK IS THE MINIMUM, so the folded cycle is the SHORTEST the declaration can support
# and the rate is therefore an UPPER bound on the peer cadence. For the population this actually
# unblocks - 321 views, every one of them DTA, a TS-engine source whose rules cannot declare an
# inter-shot delay at all - there is no value being overridden: there is no field.
INI_BURST_DELAY_TICKS = 1


def ini_burst_delays(burst):
    """The (burst - 1) inter-shot gaps an INI declaration implies, at the engine minimum.

    Passing these explicitly matters: `cycle_ticks` falls back to OpenRA own `BurstDelays`
    default of 5 when it is handed nothing, which is the right ruler for an OpenRA peer and the
    wrong one for a source whose engine has no such field.
    """
    try:
        n = int(burst or 1)
    except (TypeError, ValueError):
        n = 1
    return (INI_BURST_DELAY_TICKS,) * max(0, n - 1)


def folded_burst(evidence, reason):
    """True when the ONLY thing wrong with a row is that its burst was never folded."""
    return evidence == "incomplete" and reason == "burst_unfolded"


def cycle_ticks(reload_delay, burst=1, burst_delays=()):
    """Ticks from the START of one burst to the next: ReloadDelay + (Burst-1) x mean(BurstDelays).

    Identical convention to `reference_distribution.burst_cycle`, OpenRA's own default delay of 5
    included, so a Cameo armament and a peer armament are measured on ONE ruler. It lives here as
    well because the peer corpus hands the delays as a LIST while the ledger hands them as a
    STRING, and a second parser is the only alternative to a second formula.
    """
    try:
        rel = float(reload_delay)
    except (TypeError, ValueError):
        return None
    try:
        n = int(float(burst))
    except (TypeError, ValueError):
        n = 1
    if n <= 1:
        return rel or None
    delays = []
    for d in (burst_delays or ()):
        try:
            delays.append(float(d))
        except (TypeError, ValueError):
            pass
    mean = (sum(delays) / len(delays)) if delays else 5.0
    return rel + (n - 1) * mean


def _num(x):
    try:
        v = float(str(x))
    except (TypeError, ValueError):
        return None
    return v


# ⛔ RANGE IS NOT ONE UNIT ACROSS THE CORPUS AND MUST NEVER BE PRINTED AS IF IT WERE. Cameo and
# the OpenRA peers state range in WDist; the TS/RA2 INI sources state it in CELLS, so a DTA mammoth
# reads `5.7` beside a Cameo `6141`. The distributions never noticed because every coordinate is
# normalised WITHIN its own source — but a side-by-side pairing report is read by a human, and
# `6141 <-> 5.7` is the kind of line that gets believed. Each view therefore carries its unit, and
# the conversion is offered as a SEPARATE derived field that says where it came from.
WDIST_PER_CELL = 1024          # OpenRA's cell size; the TS lepton grid is the same 1/256 cell
RANGE_UNITS = {"wdist": 1.0, "cells": float(WDIST_PER_CELL)}


def view(side, slot, weapon, role, unknown=(), damage_per_shot=None, burst=1,
         cycle=None, rng=None, requires=None, baseline=True, note=None, range_unit="wdist",
         gate=None, replaces=None, additive=False, eligible=True, refusal=None,
         weapon_reload=None, weapon_burst=None, weapon_burst_delays=()):
    """One armament, on EITHER side of the map, in one shape.

    ⛔ `damage_per_cycle` AND `rate` ARE DERIVED HERE AND NOWHERE ELSE. The per-cycle coordinate is
    the comparable magnitude (burst is a delivery choice, not a magnitude), and the rate is the one
    formula: damage_per_shot x burst / cycle. Two call sites deriving them independently is how the
    per-shot / per-burst convention split in the first place.
    """
    burst = int(burst or 1)
    authored_burst = int(weapon_burst or burst)
    authored_delays = [value for value in (_num(v) for v in weapon_burst_delays)
                       if value is not None]
    per_cycle = (damage_per_shot * burst) if damage_per_shot else None
    scale = RANGE_UNITS.get(range_unit)
    if scale is None:
        raise ValueError(f"unknown range unit: {range_unit}")
    return {
        "side": side, "slot": slot, "weapon": weapon, "role": role,
        "unknown_targets": sorted(unknown), "range": rng,
        "range_unit": range_unit,
        "range_wdist": (rng * scale) if rng else None,
        "damage_per_shot": damage_per_shot, "burst": burst,
        "damage_per_cycle": per_cycle, "cycle": cycle,
        "rate": (per_cycle / cycle) if (per_cycle and cycle) else None,
        # Keep authored weapon components separate from the modeled actor cycle. AttackTesla
        # replaces `burst` above with logical charges, and reviewed INI cycles can include
        # jitter/charge beyond reload plus burst gaps. Application code must never reverse the
        # modeled cycle and silently overwrite those authored fields.
        "weapon_reload": _num(weapon_reload),
        "weapon_burst": authored_burst,
        "weapon_burst_delays": authored_delays,
        "requires": requires, "baseline": baseline, "gate": gate, "note": note,
        "eligible": bool(eligible), "refusal": refusal,
        # ⛔ REPLACEMENT IDENTITY, carried rather than inferred (Astra, PR #375 blocker 1). An
        # `Elite=` weapon REPLACES the slot it is declared against. `replaces` names that weapon
        # and `additive` says whether the thing it replaced was a zero-damage dummy — the only
        # case where the elite weapon occupies a slot that was otherwise empty and is therefore a
        # genuinely EXTRA armament. Without these two fields a replacement could be benched
        # alongside the weapon it replaces and the reference would vote twice with one gun.
        "replaces": replaces, "additive": bool(additive),
    }


# ── CAMEO ────────────────────────────────────────────────────────────────────────────────────
def cameo_weapon_role(rs, weapon):
    """(role, unknown) for one Cameo weapon, resolved — never hand-parsed (rule 8e)."""
    try:
        node = rs.resolve_weapon(weapon)
    except Exception:
        return None, ()
    if node is None:
        return None, ()
    get = lambda key: next((c.value for c in node.children if c.key == key), None)  # noqa: E731
    return role_of_targets(get("ValidTargets"), get("InvalidTargets"))


def cameo_views(rec, rs):
    """Every PRICED armament of one ledger record, one view each.

    Baseline membership uses the SHARED built-state evaluator (`formula.condition_holds_by_default`
    via `reference_distribution.is_upgrade_gated`) so an upgraded barrel, an elite rank and an IFV
    passenger mode are all recognised as alternatives rather than parallel weapons — the same rule
    `baseline_armaments` applies, not a second opinion about it.
    """
    import formula
    import reference_distribution as rd
    out = []
    priced = [arm for arm in (rec.get("armaments") or []) if arm.get("pricing")]
    active = rd.default_active_armaments(priced)
    baseline = rd.baseline_armaments(priced) if priced else []
    charge_owner_is_unambiguous = (len(active) == 1 and len(baseline) == 1
                                   and active[0] is baseline[0])
    for arm in priced:
        role, unknown = cameo_weapon_role(rs, arm.get("weapon"))
        mains = [w for w in (arm.get("damage_warheads") or []) if (_num(w.get("damage")) or 0) > 0]
        dmg = sum(_num(w.get("damage")) or 0 for w in mains) or None
        raw = str(arm.get("burstdelays") or "").replace(",", " ").split()
        authored_burst = int(_num(arm.get("burst")) or 1)
        burst = authored_burst
        weapon_reload = _num(arm.get("reloaddelay"))
        cycle = cycle_ticks(weapon_reload, burst, raw)
        charged_cycle = (formula.charge_attack_cycle(rec.get("charge_up"), weapon_reload)
                         if charge_owner_is_unambiguous else None)
        if charged_cycle is not None:
            cycle, burst = charged_cycle
        out.append(view(
            "cameo", arm.get("slot"), arm.get("weapon"), role, unknown,
            damage_per_shot=dmg, burst=burst, cycle=cycle,
            rng=_num(arm.get("range")), requires=arm.get("requires"),
            baseline=not rd.is_upgrade_gated(arm),
            note=",".join(sorted({w.get("tag") for w in mains if w.get("tag")})) or None,
            weapon_reload=weapon_reload, weapon_burst=authored_burst,
            weapon_burst_delays=raw))
    return out


# ── OPENRA PEERS (`weapon_evidence`) ─────────────────────────────────────────────────────────
def peer_views(row):
    """Every armament of one OpenRA peer row, from the evidence the extractor already captured.

    ⭐ NOTHING IS RE-EXTRACTED. `weapon_evidence` has carried slot, weapon, range, reload_delay,
    burst, burst_delays, valid_targets, requires_condition and each warhead's damage + versus
    since the Doc 5 emitter shipped; the consumer simply folded them. 410 peer rows carry it, 217
    of those hold more than one armament (measured 2026-09-13).
    """
    out = []
    for arm in (row.get("weapon_evidence") or []):
        role, unknown = role_of_targets(arm.get("valid_targets"))
        dmg = sum(_num(w.get("damage_num")) or 0
                  for w in (arm.get("warheads") or [])
                  if (_num(w.get("damage_num")) or 0) > 0) or None
        authored_burst = int(_num(arm.get("burst")) or 1)
        authored_delays = arm.get("burst_delays") or ()
        authored_reload = _num(arm.get("reload_delay"))
        out.append(view(
            "peer", arm.get("slot"), arm.get("weapon"), role, unknown,
            damage_per_shot=dmg, burst=authored_burst,
            cycle=cycle_ticks(authored_reload, authored_burst, authored_delays),
            rng=_num(arm.get("range")), requires=arm.get("requires_condition"),
            baseline=_peer_baseline(arm), note=arm.get("cadence_reason"),
            weapon_reload=authored_reload, weapon_burst=authored_burst,
            weapon_burst_delays=authored_delays))
    return out


def _peer_baseline(arm):
    """An armament with no requirement, or one gated on the ABSENCE of an upgrade, is baseline.

    The peer corpus spells conditions as OpenRA expressions (`!hypersonic-upgrade && ...`), the
    same grammar `formula.condition_holds_by_default` evaluates, so the shared evaluator decides.
    A condition it cannot parse FAILS CLOSED to non-baseline — an upgraded barrel counted as
    baseline would double a unit's armament set, which is the error this whole lane exists to fix.
    """
    cond = arm.get("requires_condition")
    if not cond:
        return True
    import formula
    try:
        return bool(formula.condition_holds_by_default(cond))
    except Exception:
        return False


# ── INI PEERS (`w_*` / `w2_*`) ───────────────────────────────────────────────────────────────
# ⛔ DTA AND ITS SIBLINGS ALREADY SHIP TWO SLOTS PER ROW — `w_*` is Primary=, `w2_*` is Secondary=.
# Their role does NOT come from ValidTargets (the TS/RA2 engine has no such field) but from the
# PROJECTILE's `AA=` / `AG=` flags, which live in each source's Rules.ini and are captured by
# `extract_ini_projectile_roles.py` into `docs/reference/ini_projectile_role_evidence.json`.
#
# ⚠ AND THE NAME IS A TRAP, WHICH IS WHY THE FLAGS ARE READ AND NOT THE SPELLING. DTA's
# `[AGHeatSeeker2]` — the mammoth Tusk's projectile, "AG" right there in the name — declares
# `$Inherits=AGHeatSeeker` and then `AA=yes`. It is a DUAL-role missile. A name classifier calls
# it anti-ground and pairs the mammoth's air missile against a peer cannon.
def ini_views(rec, projectile_roles=None, elite_weapons=None):
    """Every INI weapon slot as a view; role None when the projectile evidence has no verdict.

    ⛔ THERE ARE THREE SLOTS, NOT TWO — `Primary=`, `Secondary=` AND `Elite=`. The corpus carries
    only the first two and the maintainer had to point that out twice: *"it's the elite weapon
    which replaces the dummy weapon so on elite it has one cannon and one missile launcher."* DTA's
    `[MTNK]` is `Primary=90mmDummy` (zero damage, it only sets the rate of fire), `Secondary=90mm`,
    `Elite=70mmMsl1` — so its real loadout is a cannon AND a missile launcher, and reading two
    slots made it look like a single-cannon tank. `extract_ini_elite_weapons` supplies the third.
    """
    out = []
    roles = projectile_roles or {}
    source = rec.get("source")
    for prefix, slot in (("w_", "primary"), ("w2_", "secondary")):
        weapon = rec.get("weapon" if prefix == "w_" else "w2_weapon")
        dmg = _num(rec.get(prefix + "damage"))
        if not weapon and dmg is None:
            continue
        proj = rec.get(prefix + "projectile")
        exact = roles.get((source, weapon, str(proj or "")))
        verdict = exact or roles.get((source, proj)) or roles.get((source, str(proj).lower()))

        # The seven newly pinned sources use exact sidecar values.  DTA's older projectile-only
        # evidence remains usable only when this exact corpus slot carries the extractor's final
        # nominal-direct verdict.  One slot never authorises its sibling.
        if exact:
            dmg = _num(exact.get("damage"))
            reload = _num(exact.get("reload"))
            rng = _num(exact.get("range"))
            burst_was_bool = isinstance(exact.get("burst"), bool)
            raw_burst = _num(exact.get("burst"))
            folded = folded_burst(exact.get("weapon_evidence"),
                                  exact.get("weapon_evidence_reason"))
            # ⛔ STATUS STILL GATES. The fold excuses one REASON (`burst_unfolded`), never the
            # sidecar own verdict: an `abstained` record was judged unusable for reasons this
            # fold knows nothing about, and six named elite weapons rely on exactly that
            # (`test_known_unsafe_elite_weapons_are_withheld_from_every_pair`). In practice the
            # seven pinned sources publish `burst` only on RESOLVED rows, so an abstained
            # `burst_unfolded` row has no burst to fold with anyway - folding it would be
            # inventing the shot count, not bounding the gap between shots.
            evidence_ok = (exact.get("status") == "resolved"
                           and (folded or (exact.get("weapon_evidence") == "nominal_direct"
                                           and exact.get("w_dps_usable") is True)))
            refusal = None if folded else exact.get("reason")
        else:
            reload = _num(rec.get(prefix + "reload"))
            rng = _num(rec.get(prefix + "range"))
            burst_was_bool = isinstance(rec.get(prefix + "burst"), bool)
            raw_burst = _num(rec.get(prefix + "burst"))
            folded = folded_burst(rec.get(prefix + "evidence"),
                                  rec.get(prefix + "evidence_reason"))
            evidence_ok = folded or (rec.get(prefix + "evidence") == "nominal_direct"
                                     and rec.get(prefix + "dps_usable") is True)
            refusal = None if folded else (rec.get(prefix + "evidence_reason") or (
                None if evidence_ok else "weapon_evidence_absent_or_incomplete"))

        role = verdict.get("role") if verdict else None
        burst_ok = (not burst_was_bool and (raw_burst is None or
                    (math.isfinite(raw_burst) and raw_burst >= 1 and raw_burst.is_integer()))
                    )
        burst = int(1 if raw_burst is None else raw_burst) if burst_ok else 1
        numbers_ok = all(value is not None and math.isfinite(value) and value > 0
                         for value in (dmg, reload, rng))
        # ⭐ `burst == 1` WAS A CONDITION HERE AND IS GONE: a burst is folded now, not refused.
        eligible = evidence_ok and verdict is not None and burst_ok and numbers_ok
        if not eligible and refusal is None:
            if verdict is None:
                refusal = "projectile_role_unresolved"
            elif not burst_ok:
                refusal = "invalid_burst"
            elif not numbers_ok:
                refusal = "invalid_direct_weapon_numbers"
        out.append(view(
            "ini", slot, weapon, role, (),
            damage_per_shot=dmg, burst=burst,
            # ⭐ THE CYCLE IS FOLDED NOW (see INI_BURST_DELAY_TICKS). This read `cycle_ticks(
            # reload, 1, ())` under the note "THE 694 UNFOLDED RATES STAY BLOCKED ... the cycle is
            # left None rather than invented". The ruling replaces "invented" with "bounded": the
            # gap is the engine minimum, so the cycle is the shortest the declaration supports.
            cycle=cycle_ticks(reload, burst, ini_burst_delays(burst)) if eligible else None,
            rng=rng, requires=None, baseline=True,
            range_unit="cells",
            note=("projectile=%s" % proj) if proj else None,
            eligible=eligible, refusal=refusal,
            weapon_reload=reload, weapon_burst=burst, weapon_burst_delays=()))
    elite = (elite_weapons or {}).get((source, str(rec.get("id") or "")))
    if elite:
        burst_was_bool = isinstance(elite.get("burst"), bool)
        raw_burst = _num(elite.get("burst"))
        burst_ok = (not burst_was_bool and (raw_burst is None or
                    (math.isfinite(raw_burst) and raw_burst >= 1 and raw_burst.is_integer()))
                    )
        burst = int(1 if raw_burst is None else raw_burst) if burst_ok else 1
        damage = _num(elite.get("damage"))
        reload = _num(elite.get("reload"))
        rng = _num(elite.get("range"))
        numbers_ok = all(value is not None and math.isfinite(value) and value > 0
                         for value in (damage, reload, rng))
        folded = folded_burst(elite.get("weapon_evidence"), elite.get("weapon_evidence_reason"))
        # ⛔ STATUS STILL GATES here too - see the note in the slot branch above.
        evidence_ok = (elite.get("status") == "resolved"
                       and (folded or (elite.get("weapon_evidence") == "nominal_direct"
                                       and elite.get("w_dps_usable") is True)))
        # ⭐ The elite slot folds on the same ruling as the other two - an `Elite=` weapon is a
        # weapon, and letting it abstain while its own primary votes would price one DTA tank
        # against another with a different rule.
        eligible = (evidence_ok and elite.get("role") is not None and burst_ok and numbers_ok)
        refusal = None if folded else (elite.get("weapon_evidence_reason")
                                       or elite.get("reason"))
        if not eligible and refusal is None:
            refusal = ("projectile_role_unresolved" if elite.get("role") is None
                       else "invalid_burst" if not burst_ok
                       else "invalid_direct_weapon_numbers" if not numbers_ok
                       else "weapon_evidence_absent_or_incomplete")
        out.append(view(
            "ini", "elite", elite.get("weapon"), elite.get("role"), (),
            damage_per_shot=damage, burst=burst,
            cycle=cycle_ticks(reload, burst, ini_burst_delays(burst)) if eligible else None,
            rng=rng, requires="rank-elite",
            # ⚠ NOT BASELINE — it is rank-gated, exactly like Cameo's own `_elite` armaments and
            # the peer mods' upgrade barrels, and `strongest_by_role` therefore skips it for any
            # role a baseline weapon already fills. `pair_by_role` lets it cover a role that would
            # otherwise be EMPTY, which is the whole point: the reference does carry that weapon.
            baseline=False, range_unit="cells", gate="elite",
            replaces=elite.get("replaces"),
            additive=bool(elite.get("replaces_dummy_primary")),
            note=("elite, replaces %s%s" % (elite.get("replaces"),
                                            "" if elite.get("replaces_dummy_primary")
                                            else " (an upgrade of it, not an extra weapon)")),
            eligible=eligible, refusal=refusal,
            weapon_reload=reload, weapon_burst=burst, weapon_burst_delays=()))
    return out


# ── PAIRING ──────────────────────────────────────────────────────────────────────────────────
# ⭐ `both` IS ADJACENT TO EVERY DOMAIN, and that is the whole reason a strict equality key fails.
# The Cameo mammoth's missile is `both` (Ground, Water, Air); CnC's MammothMissiles is `both` too,
# but RA's Tusk is `AirborneActor, Infantry` — also `both` — while a Cameo MissileHE rocket is
# `ground`. Pairing must therefore prefer an exact role and ACCEPT a `both` on either side as the
# nearest legal partner, never pair `air` with `ground`. That single forbidden pair is the
# maintainer's rule: "those two weapons are so different they should not be mixed."

# ⛔ `UNPROVEN_PREFERENCE` WAS HERE AND IS DELETED WITH `_unproven_pair` (2026-09-13). It ordered
# the roles a role-less peer weapon could stand against, so a source that could not state a domain
# still voted on the main gun. The maintainer ruled the other way — *"ambiguous role or identity
# must abstain"* — after Astra showed the fallback promoting secondary AA guns to ground evidence.
# The ordering rule it encoded is NOT lost: it still lives where it came from, DESIGN's
# `anti_air_vehicle` anchor and `reference_distribution.baseline_armaments`.

COMPATIBLE = {
    ROLE_GROUND: (ROLE_GROUND, ROLE_BOTH),
    ROLE_AIR: (ROLE_AIR, ROLE_BOTH),
    ROLE_BOTH: (ROLE_BOTH, ROLE_GROUND, ROLE_AIR),
    ROLE_SPECIAL: (ROLE_SPECIAL,),
}


def strongest_overall(views, baseline_only=True):
    """The single hardest-hitting baseline armament, role or no role."""
    pool = [v for v in views if v.get("eligible", True)
            and (not baseline_only or v["baseline"])]
    if not pool:
        return None
    return max(pool, key=lambda v: v["damage_per_cycle"] or 0)


def candidates_by_role(views, baseline_only=True):
    """{role: [views, hardest-hitting first]} — the full bench, not just the starter.

    ⛔ ONLY THE STRONGEST WAS KEPT AND THAT LOST THE MAINTAINER'S OWN CASE. DTA's GDI Medium Tank
    at elite carries TWO ground-role weapons — `90mm` (a cannon, `Warhead=AP`) and `70mmMsl1` (a
    missile launcher, `Warhead=BazAP`) — because the TS engine puts BOTH on the ground domain.
    Cameo's `td_gdi_battletank` carries a `ground` cannon and a `both` missile. The cannon claimed
    DTA's only ground candidate and the missile was then told no source covers its role, when the
    source plainly has a second weapon it could stand against.

    ⚠ AND A DELIVERY AXIS WOULD NOT HAVE FIXED IT HONESTLY. The obvious idea — classify guided vs
    unguided and match missile to missile — has no reliable source signal on the INI side: `ROT`
    (rate of turn) reads as the homing field but `TracerM`, an ordinary gun tracer, declares
    `ROT=1`, and 426 of 433 sections that declare it are above zero. `Image=DRAGON` and
    `Warhead=BazAP` are names, which is the trap this whole module exists to avoid. A bench needs
    no semantics at all: the reference's SECOND weapon in a compatible role stands for the Cameo
    unit's second weapon, ranked by the per-cycle coordinate.
    """
    bench = {}
    for v in views:
        if baseline_only and not v["baseline"]:
            continue
        if not v.get("eligible", True):
            continue
        if v["role"] is None:
            continue
        # ⛔ CLAUSE 5 OF THE MATCHING LAW — "a zero-damage row never matches a combat unit." The
        # first bench let DTA's `90mmDummy` stand as the Battle Tank's missile reference: it is a
        # real armament with a real range, and its only job is to set the rate of fire for the
        # weapon in the next slot. A dummy is never anybody's reference.
        if not v["damage_per_cycle"]:
            continue
        bench.setdefault(v["role"], []).append(v)
    for role in bench:
        bench[role].sort(key=lambda v: v["damage_per_cycle"] or 0, reverse=True)
    return bench


def strongest_by_role(views, baseline_only=True):
    """{role: view} — the hardest-hitting BASELINE armament in each role.

    ⚠ MAX WITHIN A ROLE, NEVER SUM ACROSS ONE. `td_gdi_lighttankmkii` reports a 1-damage point
    defence laser as its gun when the first armament wins, and `ra2_allies_ifv` sums 39 mutually
    exclusive passenger weapons when the set does; within ONE role the alternatives are still
    alternatives, so the representative is the strongest, ranked on the per-cycle coordinate.
    """
    best = {}
    for v in views:
        if baseline_only and not v["baseline"]:
            continue
        if not v.get("eligible", True):
            continue
        if v["role"] is None or not v["damage_per_cycle"]:
            continue                       # clause 5 — see `candidates_by_role`
        cur = best.get(v["role"])
        if cur is None or (v["damage_per_cycle"] or 0) > (cur["damage_per_cycle"] or 0):
            best[v["role"]] = v
    return best


# ── WHICH TIER AN ACTOR REFERENCES ───────────────────────────────────────────────────────────
# ⛔ THE SAME RULE `build_reference_report.is_original` USES, AND A TEST PINS THEM TOGETHER.
# It is duplicated rather than imported because that module pulls the whole report stack; the
# duplication is safe only because `test_armament_roles` asserts the two agree on every actor in
# the assignment, and that test is the reason this comment can be trusted.
# COPIED VERBATIM, NOT RECONSTRUCTED. I wrote "OpenRA Dune 2000" here from memory and the
# agreement test caught it on `atreides_combattank`: the fourth member is Romanov's Vengeance.
# Do not "correct" this list -- it is the report's list, and the test is what keeps them equal.
ORIGINAL_SOURCES = ("OpenRA Red Alert", "OpenRA Tiberian Dawn",
                    "OpenRA Tiberian Sun", "Romanov's Vengeance")
ORIGINAL_CONFIDENCE = ("STRONG", "FAIR")


def reference_tier(sources):
    """`original` when an original-shipping mod matched this actor BY NAME, else `expanded`.

    OpenRA Red Alert / Tiberian Dawn / Tiberian Sun / Dune 2000 ship the original rosters and
    nothing else, so a name-backed match against one of them proves the unit existed in the
    original game. Everything else — promotion units, Cameo's own additions, CA and DTA
    inventions — is EXPANDED and references the elite/upgraded weapon instead.
    """
    return (TIER_ORIGINAL
            if any(d.get("confidence") in ORIGINAL_CONFIDENCE and s in ORIGINAL_SOURCES
                   for s, d in (sources or {}).items())
            else TIER_EXPANDED)


TIER_ORIGINAL = "original"
TIER_EXPANDED = "expanded"
TIERS = (TIER_ORIGINAL, TIER_EXPANDED)


def tier_bench(peer_views_, tier):
    """The peer weapons a Cameo actor of this TIER may reference. The maintainer's rule, 2026-09-13:

        "base version only for original units (with the exception for that dummy weapon of the
         MTNK) and elite versions or upgraded weapons for promotion units to get some power creep
         for late game"

    and, restating it as a constraint: *"A replacement must not also count beside its base
    weapon."* So:

      ORIGINAL  the base weapon, and nothing rank-gated. A non-additive `Elite=` is the SAME gun
                improved (`MinigunE`, `120mmE`, `RaiderCannonE` — 130 of DTA Enhanced's 139), so
                benching it next to its base weapon lets one gun vote twice. Astra found exactly
                that on FRIGATE, BEHEMOTH, YAK and HTNKARTY (PR #375 blocker 1).
      EXPANDED  the elite/upgraded replacement STANDS IN PLACE OF the weapon it replaces, which
                leaves the bench the same size. A promotion unit is a late-game design and gets a
                late-game reference — power creep that is referenced rather than invented.

    ⭐ MTNK'S DUMMY IS THE EXCEPTION AND IT IS NOT A SPECIAL CASE IN THE CODE — it falls out of
    `additive`. `[MTNK] Primary=90mmDummy` is a zero-damage rate-of-fire stub, so `Elite=70mmMsl1`
    fills a slot that was empty and IS a second weapon. Nine DTA units are in that state; for them
    the elite weapon joins BOTH tiers because it displaces nothing.
    """
    if tier not in TIERS:
        raise ValueError(f"unknown reference tier: {tier}")
    superseded = set()
    if tier == TIER_EXPANDED:
        for v in peer_views_:
            if v.get("gate") == "elite" and not v.get("additive") and v.get("replaces"):
                superseded.add(str(v["replaces"]).strip().lower())
    out = []
    for v in peer_views_:
        if v.get("gate") == "elite":
            if v.get("additive") or tier == TIER_EXPANDED:
                out.append(dict(v, baseline=True))
            continue                       # original tier: a same-gun upgrade is not evidence
        if str(v.get("weapon") or "").strip().lower() in superseded:
            continue                       # its replacement is on the bench in its place
        out.append(v)
    return out


def cameo_armaments(cameo_views_, baseline_only=True):
    """EVERY Cameo armament that can be referenced, hardest-hitting first — not one per role.

    ⛔ ONE PER ROLE WAS A SECOND FOLD (Astra, PR #375 blocker 2: *"Same-role weapons disappear
    because Cameo is reduced to the strongest weapon per role"*). `japan_oitank` carries OIFlamer,
    OIBigCannon and OISmallCannon — three GROUND weapons — and reporting only the flamer is the
    same defect the whole lane exists to remove, one level down. `ra1_allies_destroyer` has four.

    Deduplicated on (weapon, role) rather than on the slot, because `Armament@PRIMARY` and
    `Armament@GARRISONED` are the same gun fired from two places and are not two armaments.
    Clause 5 applies here too: a zero-damage row is never anybody's reference.
    """
    best = {}
    for v in cameo_views_:
        if baseline_only and not v["baseline"]:
            continue
        if not v.get("eligible", True):
            continue
        if v["role"] is None or not v["damage_per_cycle"]:
            continue
        key = (str(v.get("weapon") or "").strip().lower(), v["role"])
        cur = best.get(key)
        if cur is None or (v["damage_per_cycle"] or 0) > (cur["damage_per_cycle"] or 0):
            best[key] = v
    return sorted(best.values(),
                  key=lambda v: (-(v["damage_per_cycle"] or 0), str(v.get("weapon") or "")))


def pair_by_role(cameo_views_, peer_views_, baseline_only=True, tier=TIER_ORIGINAL):
    """([(role, cameo_view, peer_view, exact)], cameo_unmatched, peer_unmatched).

    One chosen peer weapon per source contributes one candidate for ONE Cameo armament — the
    maintainer's definition of a vote, 2026-09-13. Exact role matches are claimed FIRST across
    every armament, and only then may a `both` stand in; otherwise a unit carrying a `both` missile
    and a `ground` cannon could see its cannon claim the peer's `both` missile before the missile
    ever got a turn. Armaments are served hardest-hitting first, so when a reference has fewer guns
    than Cameo does, the main weapon is the one that gets the evidence.

    ⛔ AN UNPROVEN PEER WEAPON NO LONGER VOTES AT ALL, and `_unproven_pair` IS DELETED (Astra,
    PR #375 blocker 3; maintainer: *"ambiguous role or identity must abstain"*). It used to fall
    back to the peer's hardest-hitting role-less weapon so that the seven INI sources without a
    byte-pinned corpus could still say something. That bought coverage with a guess, and the guess
    was falsifiable: a secondary AA gun such as `FlakTrackAAGun` or `RA1RedEyeAA` outranks its
    own chassis' main gun on damage and was then reported as GROUND main-gun evidence — the one
    pairing the maintainer forbade. Abstaining costs votes and states the truth; the cost is
    measured in the pairing report's own stats rather than hidden.
    """
    cam = cameo_armaments(cameo_views_, baseline_only)
    bench = candidates_by_role(tier_bench(peer_views_, tier), baseline_only)

    taken, pairs = set(), []

    def claim(want):
        for candidate in bench.get(want, ()):
            key = (want, candidate["slot"], candidate["weapon"])
            if key not in taken:
                taken.add(key)
                return candidate
        return None

    unmatched = []
    for armament in cam:                     # exact matches first, across every armament
        partner = claim(armament["role"])
        if partner is not None:
            pairs.append((armament["role"], armament, partner, True))
        else:
            unmatched.append(armament)
    still = []
    for armament in unmatched:               # then the nearest legal stand-in
        for want in COMPATIBLE[armament["role"]]:
            partner = claim(want)
            if partner is not None:
                pairs.append((armament["role"], armament, partner, False))
                break
        else:
            still.append(armament)
    matched_peer = {(p[2]["slot"], p[2]["weapon"]) for p in pairs}
    return (pairs, still,
            [v for _r, v in sorted(strongest_by_role(
                tier_bench(peer_views_, tier), baseline_only).items())
             if (v["slot"], v["weapon"]) not in matched_peer])
