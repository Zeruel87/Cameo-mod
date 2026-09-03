#!/usr/bin/env python3
"""audit_stat_formulas.py — house stat formulas (project rules, 2026-07).

Reference units that satisfy every rule: TD GDI Archer (gdiarcher) and the
Ordos Raider (raider.ordos).

  F1  Repairable.HpPerStep == Health.HP / 20            (non-infantry)
  F2  ChangesHealth@SelfHealing.Step == HP / 2500       (HP / 1000 for infantry)
  F3  infantry must NOT have Repairable
  F4  upgrade-gated Shielded.RegenAmount == 2 x SelfHealing Step
  F5  defenses: RevealsShroud.Range == max weapon range
  F6  anti-air / advanced defenses: DetectCloaked.Range == weapon range / 2
  F7  defenses: Power.Amount == -(Cost / 20)
  F8  vehicles: Mobile.TurnSpeed == Speed / 5
  F9  turreted vehicles: Turreted.TurnSpeed == Mobile.TurnSpeed
  F10 turretless (AttackFrontal*) vehicles: TurnSpeed == 2 x Speed / 5
      (artillery exception dropped 2026-07-10: data showed no such pattern)
  F11 artillery / fire-support vehicles WITH a turret: must carry the Archer
      firing-slow pattern — GrantConditionOnAttack(firing) with
      RevokeDelay == weapon ReloadDelay / 2 and Speed/TurnSpeed/
      TurretTurnSpeed multipliers at 50
  F12 each faction needs an anti-air tower on its radar tier (Tier 2);
      additional AA towers gated at tech tier or above are legal
      "advanced AA" (Asian Alliance model)
  F13 advanced defenses must be gated ABOVE the radar tier — the tech-tier
      building or anything later (a Tier 4/5 gate like Syndicate's
      cgup.latin is fine)
      Building tiers are computed data-driven from prerequisite chains:
      conyard = 0, barracks/refinery = 1, radar = 2, tech = 3, post-tech = 4+
      (faction-relative; checks anchor on the computed radar tier).
      F12/F13 exemptions: factions with only one armed defense (Protoss
      photon cannon style), promotion-gated defenses (transitional; audited
      once they become regular), an AdvancedDefense with an anti-air weapon
      holding the radar tier when the faction has no dedicated radar-tier AA
      (it doubles as the Tier-2 AA — jballistat model), factions without an
      identifiable radar tier, and Terran/Zerg (non-tiered tech trees).
      Violations whose fix would strip the faction's ONLY pre-radar defense
      are listed as DEFERRED (every faction must keep a Tier-1 defense).
  F14 StartingUnits sets must reference only existing actors (crash class)
  F15 Light Support sets: Tier-1 units only (nothing gated above its
      producer building), total ~2000 (±15%), ~5 infantry per vehicle,
      pricier units never outnumbering cheaper ones
  F16 Heavy Support sets: same cost/ratio/frequency rules at ~10000, and at
      least one above-Tier-1 unit (an all-tier mix)
  F17 fighters and bombers (by class template): Aircraft.TurnSpeed ==
      Speed / 15 (frontal-weapon craft: 2x), e.g. Speed 180 -> TurnSpeed 12
  F19 helicopters and spaceships (by class template): Aircraft.TurnSpeed ==
      Speed / 5, like vehicles (design 2026-07-10)
  F20 AA-capable support vehicles: anti-air weapon range == 1.5 x
      anti-ground weapon range (design 2026-07-10; forgotten_m113adats
      is reference-clean: 5606 ground / 8409 air)
  F22 promotions must carry the same TECH requirement as the unit they
      unlock (tier counted from tech buildings only, transitively;
      production buildings and refineries never count) — the FutureTech
      Prospector Mk2 lockout class
  F18 anti-air weapons: a weapon whose ValidTargets include Air must deliver
      a positive-damage warhead, delayed payload, or cluster chain that can
      affect Air (inherited warheads resolved) — otherwise it fires at
      aircraft but has no gameplay payload

Scope: buildable rosters of real factions. Tolerance ±1 on divisions.
"""

from __future__ import annotations

import re
import sys

from audit_outliers import cell_value
from cameo_model import Model
from report import h1, h2, table

ARTY_TEMPLATES = ("ArtilleryTemplate", "FireSupportTemplate", "ArtilleryShipTemplate")


def ivalue(node, *path) -> int | None:
    v = node.get(*path) if node else None
    if v is None:
        return None
    comps = cell_value(v)
    return comps[0] if comps else None


def close(actual, expected, tol=1) -> bool:
    return actual is not None and expected is not None and abs(actual - expected) <= tol


def max_weapon_range(m, res) -> int | None:
    best = None
    for arm in res.children_named("Armament"):
        wname = arm.get("Weapon")
        if not wname:
            continue
        w = m.rs.resolve_weapon(wname)
        r = ivalue(w, "Range") if w else None
        if r is not None and (best is None or r > best):
            best = r
    return best


def primary_reload(m, res) -> int | None:
    for arm in res.children_named("Armament"):
        wname = arm.get("Weapon")
        if wname:
            w = m.rs.resolve_weapon(wname)
            r = ivalue(w, "ReloadDelay") if w else None
            if r is not None:
                return r
    return None


def inherits_template(m, name, needles) -> bool:
    node = m.rs.actor(name)
    seen = set()

    def walk(n):
        if n is None:
            return False
        for _, t in m.rs.inherits_of(n):
            if any(x.lower() in t.lower() for x in needles):
                return True
            if t.lower() not in seen:
                seen.add(t.lower())
                if walk(m.rs.actor(t)):
                    return True
        return False
    return walk(node)


TIER_EXEMPT_FACTIONS = {"terran", "zerg"}   # non-tiered tech trees


class TierContext:
    """Per-faction building-tier model shared by the tier-based checks.

    Data-driven building tiers: conyard (no building prereqs) = 0,
    barracks/refinery = 1, radar = 2, tech = 3, post-tech = 4/5...
    A token's tier is its CHEAPEST provider (alternate providers like
    advanced power plants must neither inflate nor cycle the chain), so
    tiers are solved as a monotone fixpoint rather than by recursion.
    """

    def __init__(self, m: Model, fac: str):
        rs = m.rs
        self.m, self.fac = m, fac
        self.roster = m.buildable_roster(fac)
        self.buildings: dict[str, set[str]] = {}
        self.radars: set[str] = set()
        self.radar_tokens: set[str] = set()
        self.promo_tokens: set[str] = set()
        for lname in self.roster:
            res = rs.resolve(lname)
            if res is None:
                continue
            b = res.child("Buildable")
            queue = (b.get("Queue") or "").lower() if b else ""
            toks = m._provider_tokens(lname, res)
            if "promotion" in queue:
                self.promo_tokens |= toks
            # D2k-style delivered refineries have no Building trait, so
            # Building-queue membership also qualifies for the tier graph.
            if (res.children_named("Building") or "building" in queue
                    or "defence" in queue or "defense" in queue):
                self.buildings[lname] = toks
                if inherits_template(m, lname, ("RadarBuilding",)):
                    self.radars.add(lname)
                    self.radar_tokens |= toks

        self.token_providers: dict[str, set[str]] = {}
        for bld, toks in self.buildings.items():
            for t in toks:
                self.token_providers.setdefault(t, set()).add(bld)
        bld_prereqs = {bld: [t for t in m.positive_prereqs(rs.resolve(bld))
                             if self.token_providers.get(t, set()) - {bld}]
                       for bld in self.buildings}
        self.tier = {bld: 0 for bld in self.buildings}
        for _ in range(len(self.buildings)):
            changed = False
            for bld, toks in bld_prereqs.items():
                new = 0
                for tok in toks:
                    provs = self.token_providers[tok] - {bld}
                    new = max(new, 1 + min(self.tier[p] for p in provs))
                if new > self.tier[bld]:
                    self.tier[bld] = new
                    changed = True
            if not changed:
                break
        self.radar_tier = min(self.tier[r] for r in self.radars) \
            if self.radars else None

    def gate(self, actor: str) -> tuple[int, bool, bool, set[str]]:
        """(gate tier, radar_gated, promotion_gated, prereqs)."""
        res = self.m.rs.resolve(actor)
        prereqs = set(self.m.positive_prereqs(res))
        gate = 0
        for tok in prereqs:
            providers = self.token_providers.get(tok, ())
            if providers:
                gate = max(gate, min(self.tier[p] for p in providers))
        return (gate, bool(prereqs & self.radar_tokens),
                bool(prereqs & self.promo_tokens), prereqs)

    def producer_tier(self, queue_word: str) -> int:
        """Min tier among buildings producing the given queue type."""
        best = None
        for bld in self.buildings:
            res = self.m.rs.resolve(bld)
            for pr in res.children_named("Production"):
                if queue_word.lower() in (pr.get("Produces") or "").lower():
                    t = self.tier[bld]
                    best = t if best is None or t < best else best
        return best if best is not None else 1


_ctx_cache: dict[str, TierContext] = {}


def tier_context(m: Model, fac: str) -> TierContext:
    if fac not in _ctx_cache:
        _ctx_cache[fac] = TierContext(m, fac)
    return _ctx_cache[fac]


def weapon_hits_air(rs, wname: str) -> bool:
    w = rs.resolve_weapon(wname) if wname else None
    if w is None:
        return False
    if "air" in (w.get("ValidTargets") or "").lower():
        return True
    return any(c.key.startswith("Warhead")
               and "air" in (c.get("ValidTargets") or "").lower()
               for c in w.children)


def defense_tier_check(m: Model, rows: dict) -> None:
    """F12/F13 — AA defense gated by radar tier; advanced defense by tech tier."""
    rs = m.rs
    for fac in sorted(f.internal for f in m.real_factions()):
        if fac in TIER_EXEMPT_FACTIONS:
            continue
        ctx = tier_context(m, fac)
        armed_defs = []
        for lname in ctx.roster:
            res = rs.resolve(lname)
            if res is None:
                continue
            b = res.child("Buildable")
            queue = (b.get("Queue") or "").lower() if b else ""
            if ("defence" in queue or "defense" in queue) \
                    and res.children_named("Armament"):
                armed_defs.append(lname)

        # single-armed-defense factions (photon cannon style) are exempt
        if len(armed_defs) <= 1 or ctx.radar_tier is None:
            continue
        radar_tier = ctx.radar_tier
        gate_info = ctx.gate

        def has_aa_weapon(defense: str) -> bool:
            res_d = rs.resolve(defense)
            return any(weapon_hits_air(rs, arm.get("Weapon"))
                       for arm in res_d.children_named("Armament"))

        # F12: at least one AA tower must sit on the radar tier; extra AA
        # towers at tech tier or above are legal "advanced AA". An
        # AdvancedDefense with an anti-air weapon sitting on the radar tier
        # doubles as the faction's Tier-2 AA (jballistat model).
        aa_towers = [d for d in armed_defs
                     if inherits_template(m, d, ("AntiAirDefense",))]
        adv_towers = [d for d in armed_defs
                      if inherits_template(m, d, ("AdvancedDefense",))]
        dual_aa = {d for d in adv_towers if has_aa_weapon(d)
                   and (gate_info(d)[1] or gate_info(d)[0] == radar_tier)}
        if aa_towers:
            infos = {d: gate_info(d) for d in aa_towers}
            baseline_ok = any(radar_gated or gate == radar_tier
                              for _, (gate, radar_gated, promo, _) in infos.items()) \
                or bool(dual_aa)
            for d, (gate, radar_gated, promo, prereqs) in sorted(infos.items()):
                if promo:
                    continue
                if not baseline_ok:
                    rows["F12"].append([f"{fac}: {d}",
                                        f"prereqs: {', '.join(sorted(prereqs)) or '(none)'} (gate {gate}, radar tier {radar_tier})",
                                        f"no AA on radar tier: {', '.join(sorted(ctx.radars))}"])
                elif not radar_gated and gate < radar_tier:
                    rows["F12"].append([f"{fac}: {d}",
                                        f"prereqs: {', '.join(sorted(prereqs)) or '(none)'} (gate {gate}, radar tier {radar_tier})",
                                        "AA below radar tier"])

        # dedicated radar-tier AA present?  (governs the dual-AA exemption)
        dedicated_radar_aa = any(
            gate_info(d)[1] or gate_info(d)[0] == radar_tier for d in aa_towers)

        # F13: advanced defenses must be gated ABOVE the radar tier (the
        # tech-tier building or any later building — Tier 4/5 gates like
        # Syndicate's cgup.latin are fine).
        for d in adv_towers:
            gate, radar_gated, promo, prereqs = gate_info(d)
            if promo:
                continue  # transitional rank-gated defense; re-audited once regular
            if gate > radar_tier:
                continue
            if d in dual_aa and not dedicated_radar_aa:
                continue  # doubles as the faction's Tier-2 AA (jballistat)
            # would the fix strip the faction's only pre-radar defense?
            # (fellow pre-radar AdvancedDefense towers don't count — they
            # are being regated too)
            others_early = [o for o in armed_defs if o != d
                            and gate_info(o)[0] < radar_tier
                            and not (o in adv_towers and gate_info(o)[0] <= radar_tier)]
            note = ("advanced defense must be gated above the radar tier (tech+)"
                    if others_early else
                    "DEFERRED: valid, but faction's only pre-radar defense — "
                    "add a Tier-1 defense before regating")
            rows["F13"].append([f"{fac}: {d}",
                                f"prereqs: {', '.join(sorted(prereqs)) or '(none)'} (gate {gate}, radar tier {radar_tier})",
                                note])


def starting_units_check(m: Model, rows: dict) -> None:
    """F14/F15/F16 — StartingUnits existence + light/heavy composition.

    Light Support: only Tier-1 units (gated no higher than their producer
    building), total cost ~2000, diverse, ~5 infantry per vehicle, cheaper
    units at least as frequent as pricier ones.
    Heavy Support: all-tier mix, total cost ~10000, same ratio/frequency
    rules, and at least one above-Tier-1 unit.
    """
    rs = m.rs
    world = rs.resolve("World")
    real = {f.internal for f in m.real_factions()}
    COST_TOL = 0.15
    targets = {"light": 2000, "heavy": 10000}

    for node in world.children:
        if not node.key.startswith("StartingUnits"):
            continue
        set_id = node.key.split("@", 1)[-1]
        facs = [x.strip() for x in (node.get("Factions") or "").split(",") if x.strip()]
        fac = next((f for f in facs if f in real), facs[0] if facs else "?")
        cls = (node.get("Class") or "").lower()
        units: list[str] = []
        base = node.get("BaseActor")
        for fieldname in ("SupportActors", "InnerSupportActors"):
            v = node.get(fieldname)
            if v:
                units += [x.strip().lower() for x in v.split(",") if x.strip()]

        # F14 — every referenced actor must exist (crash class)
        for a in ([base.lower()] if base else []) + units:
            if rs.actor(a) is None:
                rows["F14"].append([f"{fac}: {set_id}", a, "actor does not exist"])

        target = targets.get(cls)
        if target is None or not units:
            continue
        units = [u for u in units if rs.actor(u) is not None]
        counts: dict[str, int] = {}
        for u in units:
            counts[u] = counts.get(u, 0) + 1
        cost = {u: int((rs.resolve(u).get("Valued", "Cost") or "0").split(",")[0])
                for u in counts}
        total = sum(cost[u] * n for u, n in counts.items())
        inf = sum(n for u, n in counts.items() if m.unit_type(u) == "inf")
        veh = sum(n for u, n in counts.items()
                  if m.unit_type(u) in ("veh", "air", "nav"))
        key = "F15" if cls == "light" else "F16"
        where = f"{fac}: {set_id}"

        if abs(total - target) > target * COST_TOL:
            rows[key].append([where, f"total cost {total}",
                              f"target ~{target} (±{int(COST_TOL*100)}%)"])
        if veh and inf < 4 * veh:
            rows[key].append([where, f"{inf} infantry : {veh} vehicles",
                              "want ~5 infantry per vehicle"])
        elif veh == 0 and cls == "light" and len(counts) > 2:
            rows[key].append([where, f"{inf} infantry : 0 vehicles",
                              "light set should include a vehicle"])
        for a in counts:
            for b in counts:
                if cost[a] > cost[b] and counts[a] > counts[b]:
                    rows[key].append([where,
                                      f"{a} (cost {cost[a]}) x{counts[a]} vs "
                                      f"{b} (cost {cost[b]}) x{counts[b]}",
                                      "pricier units must not outnumber cheaper ones"])

        if fac in real and fac not in TIER_EXEMPT_FACTIONS:
            ctx = tier_context(m, fac)
            if ctx.radar_tier is not None:
                over_tier1 = []
                for u in sorted(counts):
                    ut = m.unit_type(u)
                    prod = ctx.producer_tier(
                        "Infantry" if ut == "inf"
                        else "Aircraft" if ut == "air" else "Vehicle")
                    if ctx.gate(u)[0] > prod:
                        over_tier1.append(u)
                if cls == "light" and over_tier1:
                    rows["F15"].append([where, ", ".join(over_tier1),
                                        "light support must be Tier-1 only "
                                        "(producer-building prereqs only)"])
                if cls == "heavy" and not over_tier1:
                    rows["F16"].append([where, "all units are Tier 1",
                                        "heavy support should mix all tiers"])


def promotion_tier_check(m, rows):
    """F22: a promotion's tech gates must match its unlocked unit's."""
    rs = m.rs

    def is_tech(bld):
        res = rs.resolve(bld)
        if res is None:
            return False
        for c in res.children:
            base = c.key.split("@")[0]
            if base in ("ProductionQueue", "Production", "Refinery"):
                return False
        return True

    for fac in sorted(f.internal for f in m.real_factions()):
        if fac in TIER_EXEMPT_FACTIONS:
            continue
        tc = TierContext(m, fac)
        if not tc.radars:
            continue

        def tech_tier(res):
            best = 0
            for tok in m.positive_prereqs(res):
                provs = [b for b in tc.token_providers.get(tok, set())
                         if is_tech(b)]
                if provs:
                    best = max(best, min(tc.tier[b] for b in provs))
            return best

        roster = m.buildable_roster(fac)
        promos = {}
        for lname in roster:
            res = rs.resolve(lname)
            if res is None:
                continue
            b = res.child("Buildable")
            if b and "promotion" in (b.get("Queue") or "").lower():
                for c in res.children:
                    if c.key.split("@")[0] == "ProvidesPrerequisite":
                        tok = c.get("Prerequisite") or lname
                        promos[tok.lower()] = (lname, tech_tier(res))
        for lname in sorted(roster):
            res = rs.resolve(lname)
            if res is None or lname.lower() in promos.values():
                continue
            b = res.child("Buildable")
            if b is None:
                continue
            toks = [t.lower() for t in m.positive_prereqs(res)]
            for tok in toks:
                if tok in promos:
                    pname, ptier = promos[tok]
                    utier = tech_tier(res)
                    if utier != ptier:
                        rows["F22"].append(
                            [f"{fac}: {lname}",
                             f"unit tech tier {utier}",
                             f"promotion {pname} tier {ptier} — must match"])


def targets_air(node, *, default_all: bool = False) -> bool:
    raw = node.get("ValidTargets")
    if raw is None:
        return default_all
    return "air" in {v.strip().lower() for v in raw.split(",")}


def positive_damage(node) -> bool:
    if node.value == "DamagesConcrete":
        return False
    damage = ivalue(node, "Damage")
    return damage is not None and damage > 0


def is_point_defense(weapon) -> bool:
    targets = {v.strip().lower()
               for v in (weapon.get("ValidTargets") or "").split(",")}
    invalid = {v.strip().lower()
               for v in (weapon.get("InvalidTargets") or "").split(",")}
    projectile_targets = {"missile", "ballisticmissile", "bulletas", "bulletca"}
    excluded_units = {"infantry", "vehicle", "structure"}
    return bool(targets & projectile_targets) and excluded_units <= invalid


def has_air_payload(rs, weapon, seen: set[str] | None = None) -> bool:
    """Return whether a resolved weapon delivers a gameplay payload to Air.

    Delivery chains are followed because the carrier weapon can intentionally
    use a token impact while a spawned or delayed weapon owns the real damage.
    AttachDelayedWeapon must itself accept Air before its nested chain counts.
    """
    seen = set() if seen is None else seen
    key = weapon.key.lower()
    if key in seen:
        return False
    seen.add(key)
    for child in weapon.children:
        if not child.key.startswith("Warhead"):
            continue
        if positive_damage(child) and targets_air(child, default_all=True):
            return True
        if child.value in ("AttachDelayedWeapon", "FireCluster",
                           "SpawnSmokeParticle"):
            if child.value == "AttachDelayedWeapon" and not targets_air(
                    child, default_all=True):
                continue
            nested_name = child.get("Weapon")
            nested = rs.resolve_weapon(nested_name) if nested_name else None
            if nested is not None and has_air_payload(rs, nested, set(seen)):
                return True
    return False


def aa_warhead_check(m: Model, rows: dict) -> None:
    """F18 — weapons that target Air but deliver no gameplay payload to it."""
    rs = m.rs
    used_by: dict[str, set[str]] = {}
    roster_all: set[str] = set()
    for f in m.real_factions():
        roster_all |= m.buildable_roster(f.internal)
    for lname in roster_all:
        res = rs.resolve(lname)
        if res is None:
            continue
        for arm in res.children_named("Armament"):
            w = arm.get("Weapon")
            if w:
                used_by.setdefault(w.lower(), set()).add(lname)

    for wname in sorted(used_by):
        w = rs.resolve_weapon(wname)
        if w is None:
            continue
        if not targets_air(w):
            continue
        # Point-defense beams carry Air alongside projectile target types, but
        # explicitly exclude normal unit classes. Their token damage destroys
        # intercepted projectile actors and is not an anti-air unit contract.
        if is_point_defense(w):
            continue
        dmg_warheads = [c for c in w.children
                        if c.key.startswith("Warhead") and positive_damage(c)]
        if not dmg_warheads:
            continue
        if not has_air_payload(rs, w):
            airless = [c.key for c in dmg_warheads
                       if not targets_air(c, default_all=True)]
            users = ", ".join(sorted(used_by[wname])[:5])
            rows["F18"].append([wname, ", ".join(airless[:4]),
                                f"targets Air but no gameplay payload hits Air (used by {users})"])


def main() -> int:
    m = Model()
    rs = m.rs
    rows = {k: [] for k in
            ("F1", "F2", "F3", "F4", "F5", "F6", "F7", "F8", "F9", "F10",
             "F11", "F12", "F13", "F14", "F15", "F16", "F17", "F18",
             "F19", "F20", "F22")}

    names: set[str] = set()
    for f in m.real_factions():
        names |= m.buildable_roster(f.internal)
    inherited_f3: set[str] = set()

    for lname in sorted(names):
        res = rs.resolve(lname)
        if res is None or res.child("Health") is None:
            continue
        ut = m.unit_type(lname)
        hp = ivalue(res, "Health", "HP")
        b = res.child("Buildable")
        queue = (b.get("Queue") or "").lower() if b else ""
        is_def = "defence" in queue or "defense" in queue

        # F1/F2/F3 heal & repair maths
        rep = ivalue(res, "Repairable", "HpPerStep")
        heal = None
        for c in res.children:
            if c.key == "ChangesHealth@SelfHealing":
                comps = cell_value(c.get("Step") or "")
                heal = comps[0] if comps else None
        if hp:
            if ut == "inf":
                if res.child("Repairable") is not None:
                    local = rs.actor(lname).child("Repairable") is not None
                    if local:
                        rows["F3"].append([lname, "infantry declares Repairable locally", ""])
                    else:
                        inherited_f3.add(lname)
                if heal is not None and not close(heal, round(hp / 1000)):
                    rows["F2"].append([lname, f"Step {heal}", f"expected {round(hp/1000)} (HP {hp}/1000)"])
            elif ut in ("veh", "air", "nav"):
                if rep is not None and not close(rep, round(hp / 20)):
                    rows["F1"].append([lname, f"HpPerStep {rep}", f"expected {round(hp/20)} (HP {hp}/20)"])
                if heal is not None and not close(heal, round(hp / 2500)):
                    rows["F2"].append([lname, f"Step {heal}", f"expected {round(hp/2500)} (HP {hp}/2500)"])

        # F4 shields gated on upgrades
        for c in res.children:
            if c.key.split("@")[0] != "Shielded":
                continue
            rc = (c.get("RequiresCondition") or "")
            if not any(t.startswith("up") or "upgrade" in t for t in re.findall(r"[\w.]+", rc)):
                continue
            regen = ivalue(c, "RegenAmount") if False else None
            v = c.get("RegenAmount")
            regen = cell_value(v)[0] if v else None
            if heal is not None and regen is not None and not close(regen, 2 * heal):
                rows["F4"].append([lname, f"RegenAmount {regen}",
                                   f"expected {2*heal} (2 x SelfHealing {heal})"])

        # F5/F6/F7 defenses
        if is_def:
            wr = max_weapon_range(m, res)
            rsr = ivalue(res, "RevealsShroud", "Range")
            if wr is not None and rsr is not None and not close(rsr, wr, tol=32):
                rows["F5"].append([lname, f"RevealsShroud {rsr}", f"weapon range {wr}"])
            if inherits_template(m, lname, ("AntiAirDefense", "AdvancedDefense")):
                dc = ivalue(res, "DetectCloaked", "Range")
                if wr is not None:
                    if dc is None:
                        rows["F6"].append([lname, "DetectCloaked missing", f"expected {wr//2}"])
                    elif not close(dc, wr // 2, tol=32):
                        rows["F6"].append([lname, f"DetectCloaked {dc}", f"expected {wr//2} (range/2)"])
            cost = ivalue(res, "Valued", "Cost")
            pwr = ivalue(res, "Power", "Amount")
            if cost:
                if pwr is None:
                    rows["F7"].append([lname, "Power missing", f"expected {-(cost//20)}"])
                elif not close(pwr, -(cost // 20), tol=2):
                    rows["F7"].append([lname, f"Power {pwr}", f"expected {-(cost//20)} (-Cost/20)"])

        # F8-F11 vehicle turn maths
        if ut == "veh":
            mob = res.child("Mobile")
            spd = ivalue(res, "Mobile", "Speed")
            ts = ivalue(res, "Mobile", "TurnSpeed")
            turret = res.child("Turreted")
            frontal = any(c.key.split("@")[0].startswith("AttackFrontal")
                          for c in res.children)
            arty = inherits_template(m, lname, ARTY_TEMPLATES)
            if spd:
                base = round(spd / 5)
                if turret is None and frontal:
                    # artillery exception dropped 2026-07-10: data showed
                    # turretless artillery split 24 (2x) vs 18 (1x) — no rule
                    want = 2 * base
                    if ts is not None and not close(ts, want):
                        rows["F10"].append([lname, f"TurnSpeed {ts} (Speed {spd})",
                                            f"expected {want} = 2 x Speed/5 (turretless)"])
                elif ts is not None and not close(ts, base):
                    rows["F8"].append([lname, f"TurnSpeed {ts} (Speed {spd})",
                                       f"expected {base} = Speed/5"])
                if turret is not None:
                    tts = ivalue(res, "Turreted", "TurnSpeed") or ivalue(turret, "TurnSpeed")
                    v = turret.get("TurnSpeed")
                    tts = cell_value(v)[0] if v else None
                    if tts is not None and ts is not None and tts != ts:
                        rows["F9"].append([lname, f"Turreted {tts} vs Mobile {ts}",
                                           "must match"])
            if arty and turret is not None:
                gca = None
                for c in res.children:
                    if c.key.split("@")[0] == "GrantConditionOnAttack":
                        gca = c
                slow = any(c.key.startswith("SpeedMultiplier@") and c.get("Modifier") == "50"
                           and "firing" in (c.get("RequiresCondition") or "")
                           for c in res.children)
                reload_d = primary_reload(m, res)
                if gca is None or not slow:
                    rows["F11"].append([lname, "firing-slow pattern missing",
                                        "see gdiarcher (GrantConditionOnAttack + 50% multipliers)"])
                else:
                    rd = cell_value(gca.get("RevokeDelay") or "")
                    rd = rd[0] if rd else None
                    if reload_d and rd is not None and not close(rd, reload_d // 2, tol=5):
                        rows["F11"].append([lname, f"RevokeDelay {rd}",
                                            f"expected {reload_d//2} (ReloadDelay {reload_d}/2)"])

        # F17: fighters/bombers turn at Speed/15 (frontal-weapon craft 2x)
        if ut == "air" and inherits_template(m, lname, ("FighterTemplate", "BomberTemplate")):
            spd = ivalue(res, "Aircraft", "Speed")
            ats = ivalue(res, "Aircraft", "TurnSpeed")
            if spd and ats is not None:
                frontal = any(c.key.split("@")[0].startswith("AttackFrontal")
                              for c in res.children)
                want = round(spd / 15) * (2 if frontal else 1)
                label = "2 x Speed/15 (frontal)" if frontal else "Speed/15"
                if not close(ats, want):
                    rows["F17"].append([lname, f"TurnSpeed {ats} (Speed {spd})",
                                        f"expected {want} = {label}"])

        # F19: helicopters & spaceships turn like vehicles (Speed/5)
        if ut == "air" and inherits_template(
                m, lname, ("HelicopterTemplate",
                           "UnarmedTransportHelicopterTemplate",
                           "SpaceshipTemplate")):
            spd = ivalue(res, "Aircraft", "Speed")
            ats = ivalue(res, "Aircraft", "TurnSpeed")
            if spd and ats is not None and not close(ats, round(spd / 5)):
                rows["F19"].append([lname, f"TurnSpeed {ats} (Speed {spd})",
                                    f"expected {round(spd/5)} = Speed/5"])

        # F20: AA support vehicles: anti-air range = 1.5 x anti-ground range
        if ut == "veh" and inherits_template(m, lname, ("SupportVehicleTemplate",)):
            air_r, gnd_r = [], []
            for arm in res.children_named("Armament"):
                w = arm.get("Weapon")
                ww = m.rs.resolve_weapon(w) if w else None
                if ww is None:
                    continue
                vt = (ww.get("ValidTargets") or "").lower()
                r = cell_value(ww.get("Range") or "")
                r = r[0] if r else None
                if r is None:
                    continue
                if "air" in vt and "ground" not in vt:
                    air_r.append(r)
                elif "ground" in vt and "air" not in vt:
                    gnd_r.append(r)
            if air_r and gnd_r:
                want = round(max(gnd_r) * 3 / 2)
                if not close(max(air_r), want, tol=10):
                    rows["F20"].append([lname,
                                        f"AA range {max(air_r)} vs ground {max(gnd_r)}",
                                        f"expected {want} = 1.5 x ground range"])

    defense_tier_check(m, rows)
    starting_units_check(m, rows)
    promotion_tier_check(m, rows)
    aa_warhead_check(m, rows)

    total = sum(len(v) for v in rows.values())
    print(h1("audit_stat_formulas — house stat formulas"))
    print(f"Violations: **{total}** across {len(names)} roster actors "
          f"(reference-clean units: gdiarcher, raider.ordos)\n")
    titles = {
        "F1": "F1 — Repairable.HpPerStep ≠ HP/20",
        "F2": "F2 — SelfHealing Step ≠ HP/2500 (inf: HP/1000)",
        "F3": "F3 — infantry with Repairable",
        "F4": "F4 — upgrade shield RegenAmount ≠ 2×SelfHealing Step",
        "F5": "F5 — defense RevealsShroud.Range ≠ weapon range",
        "F6": "F6 — AA/advanced defense DetectCloaked.Range ≠ weapon range/2",
        "F7": "F7 — defense Power.Amount ≠ -Cost/20",
        "F8": "F8 — vehicle TurnSpeed ≠ Speed/5",
        "F9": "F9 — Turreted.TurnSpeed ≠ Mobile.TurnSpeed",
        "F10": "F10 — turretless TurnSpeed ≠ 2×Speed/5 (artillery: Speed/5)",
        "F11": "F11 — turreted artillery missing/incorrect firing-slow (Archer pattern)",
        "F12": "F12 — anti-air defense not gated by the faction's radar tier",
        "F13": "F13 — advanced defense not gated by the faction's tech tier",
        "F14": "F14 — StartingUnits referencing nonexistent actors (crash class)",
        "F15": "F15 — Light Support composition (Tier-1 only, ~2000, 5:1 inf:veh)",
        "F16": "F16 — Heavy Support composition (all tiers, ~10000, 5:1 inf:veh)",
        "F17": "F17 — fighter/bomber TurnSpeed ≠ Speed/15 (frontal: 2×)",
        "F18": "F18 — weapons targeting Air whose gameplay payload can't hit Air",
        "F19": "F19 — helicopter/spaceship TurnSpeed ≠ Speed/5",
        "F20": "F20 — AA support vehicle: air range ≠ 1.5 × ground range",
        "F22": "F22 — promotion tech gate ≠ unlocked unit's tech gate",
    }
    for k in rows:
        print(h2(f"{titles[k]}  ({len(rows[k])})"))
        print(table(["actor", "actual", "expected"], rows[k]))
        if k == "F3" and inherited_f3:
            print(f"\n_{len(inherited_f3)} further infantry inherit Repairable "
                  "from the infantry base template (^DefaultInfantry "
                  "RepairActors: drfghosp… — unloaded Dark Reign hospitals). "
                  "One template-line fix covers them all._\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
