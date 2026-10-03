#!/usr/bin/env python3
"""audit_ammo_cadence.py — an AMMO POOL makes `ReloadDelay` the wrong clock, and every carrier
slave must have a pool, an explicit ammo-dependent firing gate, and a reload policy.

MAINTAINER RULINGS, 2026-09-12:
  * "the SSM launcher reload delay in cameo doesn't matter since it requires ammo to shoot
     which regenerates on the actor itself"
  * "our helicopters ... are designed to shoot for 5 seconds at full speed and then after that
     at half speed" / "we take into account how much damage they can deal from full to empty
     ammo pool and in what time and calculate that as the DPS"
  * "For planes that need to reload on the airfield ... reload delay means nothing there so we
     only compare the maximum damage per sortie"
  * "All carrier slaves must have an ammo pool and reload, so what you have discovered with the
     A10 carrier is a real bug"

A1  cadence regime census. `ammo_cadence.cadence()` classifies each ammo-pool actor and says
    what the comparable figure actually is. The ledger publishes ONE number for everybody —
    `damage x burst / (reload + burst delays)` — and nothing in `extract_stats`,
    `reference_distribution` or `formula` mentions `AmmoPool`, so for every actor counted here
    the published DPS is measuring a cadence the unit does not have.

A2  CARRIER SLAVES. Every `CarrierSlave` must carry an `AmmoPool` and a reload trait. The two
    failure modes are OPPOSITE and both are live:

      * NO POOL AT ALL -> the engine grants UNLIMITED AMMO. `CarrierSlave.cs:59-65`:
            if (ammoPools.Length == 0)
                return false;   // "The unit may not have ammo but will have unlimited ammunitions."
        so the slave never expends, never needs to dock, and the carrier's launch/expend/return
        cycle never runs. It is a permanent free attacker.

      * POOL BUT NO RELOAD -> the slave has no explicit in-flight reload policy. The carrier
        engine refills every pool when a slave re-enters its carrier; the reload trait is the
        separate policy for recovery while the slave is deployed.

      * POOL WITHOUT A FIRING GATE -> `AmmoPool` spends ammo from its attack notification after
        the attack is selected, so a newly added pool alone does not stop an empty slave from
        firing. `AmmoCondition` plus `AttackAircraft.RequiresCondition` (and armament pause
        gates where needed) is required.

⚠ READ BOTH RELOAD TRAIT SPELLINGS. `ReloadAmmoPool` (92 actors) and `ReloadAmmoPoolCA` (25)
are both in use. The first version of this measurement read only the former and misclassified
25 actors — the same one-spelling mistake that hid burst delays behind `BurstDelay0..8` and the
DTA `$Inherits` directive behind a regex. When a trait has a CA twin, match the STEM.

Ratchets are LOWER-ONLY, as everywhere else.
"""
from __future__ import annotations

import collections
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "balance"))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

import ammo_cadence as ac  # noqa: E402
import carrier_slave_ammo as slave_law  # noqa: E402
import miniyaml  # noqa: E402
from report import h1, h2, table  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parents[2]

# CLEARED 2026-09-12 by tools/balance/apply_carrier_slave_ammo.py: all 14 in-scope slaves now
# carry a sized pool and a reload. LOWER ONLY.
#
# ⚠ The 5 SUICIDE slaves are out of scope, not fixed, and are reported separately below. A
# reload trait is dead weight on a unit that dies when it attacks. The maintainer named two of
# them (`tkmsuicidedrone`, `farasha_drone_ixian`) — whose self-destruct is in the WEAPON and so
# appears in no trait — and `carrier_slave_ammo.is_suicide` finds three more under the same
# rule. Counting them as defects would have left this ratchet stuck at 5 forever, reporting a
# backlog that the ruling says should not be worked.
A2_BASELINE = 0           # CarrierSlave actors IN SCOPE missing a pool or a reload
MAIN = ("AreaDamage", "SpreadDamage")
NOT_A_MAIN = ("percentage", "friendlyfire", "extradamage")
RELOAD_STEMS = ("ReloadAmmoPool",)   # matches ReloadAmmoPool AND ReloadAmmoPoolCA


def kv(node):
    return {c.key: str(c.value).strip() for c in node.children}


def num(v, default=None):
    try:
        return int(str(v).split(",")[0])
    except (TypeError, ValueError):
        return default


def trait(resolved, stem):
    """Every trait whose key STEM matches, so a CA twin is never missed."""
    return [c for c in resolved.children
            if c.key.split("@")[0] == stem or c.key.split("@")[0] == stem + "CA"]


def main_damage(weapon):
    total = 0
    for ch in weapon.children:
        if (ch.key.startswith("Warhead@") and ch.value.strip() in MAIN
                and not any(s in ch.key.lower() for s in NOT_A_MAIN)):
            total += num(next((g.value for g in ch.children if g.key == "Damage"), 0), 0) or 0
    return total


def main() -> int:
    rs = miniyaml.Ruleset(str(ROOT))
    rows, slaves = [], []
    for name in sorted(rs.actors):
        if name.startswith(("^", "-")):
            continue
        res = rs.resolve(name)
        if res is None:
            continue
        pools = trait(res, "AmmoPool")
        reloads = [c for c in res.children
                   if any(c.key.split("@")[0].startswith(s) for s in RELOAD_STEMS)]
        rearmable = bool(trait(res, "Rearmable"))
        is_slave = any(c.key.split("@")[0] == "CarrierSlave" for c in res.children)
        if is_slave:
            stems = {c.key.split("@")[0] for c in res.children}
            weapons = [next((str(g.value).strip() for g in c.children if g.key == "Weapon"), "")
                       for c in res.children if c.key.split("@")[0] == "Armament"]
            gate_defect = None
            if pools:
                pool_values = kv(pools[0])
                ammo_condition = pool_values.get("AmmoCondition")
                if not ammo_condition:
                    gate_defect = "missing AmmoCondition"
                else:
                    attack = next((c for c in res.children if c.key == "AttackAircraft"), None)
                    attack_values = kv(attack) if attack is not None else {}
                    global_gate = ammo_condition in {
                        token.strip() for token in attack_values.get("RequiresCondition", "").split(",")
                    }
                    pool_names = set(pool_values.get("Armaments", "primary, secondary").replace(" ", "").split(","))
                    for arm in [c for c in res.children if c.key.split("@")[0] == "Armament"]:
                        arm_values = kv(arm)
                        if arm_values.get("Name", "primary") not in pool_names:
                            continue
                        if num(arm_values.get("AmmoUsage"), 1) <= 0:
                            continue
                        usage = num(arm_values.get("AmmoUsage"), 1)
                        if not slave_law.pause_gate_sufficient(
                                ammo_condition, usage,
                                arm_values.get("PauseOnCondition"),
                                arm_values.get("RequiresCondition"),
                                global_gate=global_gate):
                            gate_defect = f"no minimum-ammo gate for {arm.key}"
                            break
            slaves.append((name, bool(pools), num(kv(pools[0]).get("Ammo")) if pools else None,
                           bool(reloads), rearmable,
                           slave_law.is_suicide(name, stems, weapons), gate_defect))
        if not pools:
            continue
        pool, rl = kv(pools[0]), (kv(reloads[0]) if reloads else None)
        best = None
        for arm in [c for c in res.children if c.key.split("@")[0] == "Armament"]:
            a = kv(arm)
            weapon = rs.resolve_weapon(a.get("Weapon") or "")
            if weapon is None:
                continue
            w = kv(weapon)
            dmg = main_damage(weapon)
            if dmg <= 0:
                continue
            burst = num(w.get("Burst"), 1)
            out = ac.cadence(
                dmg, burst, num(w.get("ReloadDelay"), 25),
                [num(x, 0) for x in str(w.get("BurstDelays", "5")).split(",")],
                ammo=num(pool.get("Ammo"), 1), ammo_usage=num(a.get("AmmoUsage"), 1),
                reload_count=(num(rl.get("Count"), 1) if rl else None),
                reload_delay_pool=(num(rl.get("Delay"), 50) if rl else None),
                rearmable=rearmable)
            ledger = dmg * max(burst, 1) / out["cycle"]
            if best is None or ledger > best[0]:
                best = (ledger, out, a.get("Weapon"))
        if best:
            rows.append((name,) + best)

    out = [h1("Ammo cadence — the published DPS measures a clock these actors do not use"), ""]
    census = collections.Counter(r[2]["regime"] for r in rows)
    single = sum(1 for r in rows if r[2].get("single_shot"))
    out += [f"ammo-pool actors with a measurable weapon: **{len(rows)}**", "",
            table(["regime", "actors", "the comparable figure"],
                  [[ac.SELF_RELOADING, census[ac.SELF_RELOADING],
                    "pool damage / time to empty (a RATE)"],
                   [ac.AIRFIELD_REARM, census[ac.AIRFIELD_REARM],
                    "damage per sortie (a TOTAL; no rate exists)"],
                   [ac.FINITE_UNCLASSIFIED, census[ac.FINITE_UNCLASSIFIED],
                    "no replenishment mechanism found — reported, never scored"]]),
            "",
            f"Of those, **{single}** hold only ONE shot, so no rate exists for them either.", ""]

    sr = [r for r in rows if r[2]["regime"] == ac.SELF_RELOADING and r[2]["dps"]]
    cannot = [r for r in sr if (r[2]["sustain_factor"] or 1) < 0.98]
    out += [h2("A1 — self-reloading: the ruled DPS against the published one"),
            f"{len(sr)} actors. **{len(cannot)}** cannot sustain their own weapon's rate; the "
            "pool bounds how long they fire at it.", "",
            table(["actor", "weapon", "published dps", "ruled dps", "full-rate window",
                   "sustain"],
                  [[a, w, f"{l:,.0f}", f"{o['dps']:,.0f}",
                    f"{o['seconds_at_full_rate']:.1f} s", f"{o['sustain_factor']:.2f}"]
                   for a, l, o, w in sorted(sr, key=lambda x: x[2]["sustain_factor"] or 1)[:25]]),
            ""]

    af = [r for r in rows if r[2]["regime"] == ac.AIRFIELD_REARM]
    out += [h2("A1 — airfield rearm: a rate is published today and should not be"),
            table(["actor", "weapon", "published dps", "damage per sortie", "window"],
                  [[a, w, f"{l:,.0f}", f"{o['sortie_damage']:,.0f}",
                    f"{o['seconds_at_full_rate']:.1f} s"]
                   for a, l, o, w in sorted(af, key=lambda x: -x[2]["sortie_damage"])[:20]]),
            ""]

    in_scope = [s for s in slaves if not s[5]]
    suicide = [s for s in slaves if s[5]]
    bad = [s for s in in_scope if not (s[1] and s[3]) or s[6]]
    out += [h2(f"A2 — carrier slaves: {len(bad)} of {len(in_scope)} in scope break the rule "
               f"(ratchet {A2_BASELINE})"),
            "Every `CarrierSlave` must have an `AmmoPool`, an empty-pool firing gate, and a reload. The failures are "
            "opposite: no pool means the engine grants unlimited ammo (`CarrierSlave.cs:59-65`) "
            "so the carrier cycle never runs; a pool without a gate still permits an empty shot "
            "because ammo is consumed after attack selection. Carrier re-entry refills pools; "
            "`ReloadAmmoPool` is the explicit in-flight recovery policy.", ""]
    if bad:
        out += [table(["actor", "pool", "ammo", "reload", "rearmable", "defect"],
                      [[a, str(p), str(am or "—"), str(r), str(re_),
                        ("unlimited ammo — no pool" if not p else
                         "missing reload" if not r else _gate)]
                       for a, p, am, r, re_, _s, _gate in bad]), ""]
    else:
        out += ["_All in-scope slaves carry a sized pool and a reload_ — sized by "
                "`tools/balance/carrier_slave_ammo.py` (R8: one full burst attack empties the "
                "pool, empty to full in exactly 100 ticks).", ""]
    out += [f"**{len(suicide)} suicide slaves are OUT OF SCOPE**, not a backlog — a reload is "
            "dead weight on a unit that dies when it attacks. Two were named by the maintainer; "
            "their self-destruct lives in the WEAPON and appears in no trait, which is why the "
            "detector alone would miss them.", "",
            table(["actor", "why out of scope", "pool", "reload"],
                  [[a, s, str(p), str(r)] for a, p, _am, r, _re, s, _gate in suicide]),
            ""]

    (ROOT / "docs" / "audit" / "latest").mkdir(parents=True, exist_ok=True)
    text = "\n".join(out)
    print(text)
    fail = len(bad) > A2_BASELINE
    if fail:
        print(f"\nFAIL — carrier-slave defects {len(bad)} > ratchet {A2_BASELINE}")
    return 1 if fail else 0


if __name__ == "__main__":
    sys.exit(main())
