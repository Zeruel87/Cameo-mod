#!/usr/bin/env python3
"""audit_weapon_shape.py ΓÇö THE ONE-WARHEAD / THREE-INHERIT LAW.

Γ¡É MAINTAINER RULING, 2026-09-06 (night). Binding, and it SUPERSEDES the
"intentional composite" exemption:

    "From now on we will no longer allow any more multi-warhead weapons. The only
     thing every weapon is allowed to have are exactly 3 inherits: warhead,
     projectile and effect. No more dual warheads, dual effects or dual projectiles
     or anything else. Also no more effects directly on the weapon itself ΓÇö it
     should all come from the inherited templates. The only thing allowed are
     special cases like those fire-shrapnel weapons or applying a condition."

So the target shape of EVERY concrete weapon is exactly:

    SomeWeapon:
        Inherits@wh:   ^Warhead_<Family>_<Level>
        Inherits@proj: ^Projectile_<Kind>_<Level>
        Inherits@fx:   ^Effect_<Kind>_<Level>
        <scalars only: Range, ReloadDelay, Report, Damage override, ...>

Γ¢ö WHAT THIS REPEALS. `tools/audit/intentional_composites.py` recorded 224 multi-main
weapons as REVIEWED AND DELIBERATELY KEPT. Under this ruling they are no longer
exempt ΓÇö they are the WORKLIST. The registry is still the right data (it says which
multi-main shapes were deliberate and what their mains are); only its MEANING flips,
from "leave alone" to "convert, and mind that someone chose these mains on purpose."

ΓÜá LEGITIMATE EXCEPTIONS, and they are narrow. A warhead is NOT a violation when it
delivers a MECHANIC rather than a second damage profile:
  * `FireShrapnel` / `FireFragment` / `FireCluster` ΓÇö spawn-another-weapon mechanics.
  * `GrantExternalCondition` ΓÇö applies a condition (shields, status meters).
  * `AreaDamagePercentage` / `*Percentage` twins ΓÇö the percentage half of one main.
  * `*FriendlyFire` / `*ExtraDamage` ΓÇö the baked halves of one main.
These are counted and shown, never failed on.

Buckets, each on its own LOWER-ONLY ratchet:

  W1  more than 3 inherits
  W2  two or more `^Warhead_*` inherits
  W3  two or more `^Projectile_*` inherits
  W4  two or more `^Effect_*` inherits
  W5  more than one resolved MAIN warhead   (the damage half of the law)
  W6  effect warheads declared LOCALLY on a concrete weapon
  I7  informational: weapons missing one of the three template inherits

ΓÜá I7 is INFORMATIONAL ON PURPOSE. A weapon with no `^Projectile_*` may legitimately
be an instant/utility weapon, so the number is a review queue, not a defect count.
Do not turn it into a ratchet without a per-weapon pass.
"""

from __future__ import annotations

import collections
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

import miniyaml  # noqa: E402
from report import h1, h2, table  # noqa: E402

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

ROOT = pathlib.Path(__file__).resolve().parents[2]

# Ratchets established 2026-09-06 by THIS script's own first run. LOWER ONLY.
# (An earlier throwaway scan said 602/237/30/72; its regex was looser. Always set
#  a ratchet from the audit that enforces it, never from a scratch measurement.)
W1_BASELINE = 583   # more than 3 inherits
W2_BASELINE = 211   # dual ^Warhead_ inherit (213->211: D2K_Rocket_Trooper AA+AGOnly collapsed by maintainer ffdec98b7)
W3_BASELINE = 12    # dual ^Projectile_ inherit (21->12: same collapse)
W4_BASELINE = 52    # dual ^Effect_ inherit (61->52: same collapse)
W5_BASELINE = 394   # more than one resolved MAIN warhead (was 401; 394 after the
                    # ad7c5e232 removal-node restore, which was the last of the
                    # resurrected-warhead damage)
W6_BASELINE = 694   # weapons declaring an effect warhead locally
                    # 687 -> 694: the TOP_LEVEL regex was fixed to match
                    # digit-starting keys (120mm_*, 8Inch, etc.), exposing
                    # 7 weapons previously hidden. LOWER ONLY.

MAIN_TYPES = ("SpreadDamage", "AreaDamage")
EFFECT_TYPES = {
    "CreateEffect", "LeaveSmudge", "GlowImpact", "FlashPaletteEffect",
    "DamagesConcrete",
}
# Suffixes that mark a warhead as a HALF of one main, not a second main.
NOT_A_MAIN = ("percentage", "friendlyfire", "extradamage")

TOP_LEVEL = re.compile(r"^([A-Za-z0-9_^][A-Za-z0-9_.^]*):")
INHERIT = re.compile(r"^\t(Inherits(?:@[A-Za-z0-9_]+)?):\s*(\S+)")
WARHEAD = re.compile(r"^\t(Warhead@[A-Za-z0-9_]+):\s*(\S*)")


def scan_source():
    """Per concrete weapon: its inherit list and its LOCALLY declared warheads."""
    man = miniyaml.load_manifest(ROOT)
    inherits: dict[str, list[str]] = collections.defaultdict(list)
    local_fx: dict[str, list[str]] = collections.defaultdict(list)
    for entry in man.weapons:
        path = pathlib.Path(str(entry))
        if not path.is_absolute():
            path = ROOT / path
        if not path.exists():
            continue
        current = None
        for line in path.read_text(encoding="utf-8-sig", errors="replace").splitlines():
            top = TOP_LEVEL.match(line)
            if top:
                current = top.group(1)
                continue
            if not current or current.startswith("^"):
                continue
            mi = INHERIT.match(line)
            if mi:
                inherits[current].append(mi.group(2))
                continue
            mw = WARHEAD.match(line)
            if mw and mw.group(2) in EFFECT_TYPES:
                local_fx[current].append(f"{mw.group(1)}: {mw.group(2)}")
    return inherits, local_fx


def resolved_mains():
    """{weapon: [main warhead tags]} for weapons resolving to more than one main."""
    rs = miniyaml.Ruleset(ROOT)
    out = {}
    for name in sorted(rs.weapons):
        if name.startswith("^"):
            continue
        node = rs.resolve_weapon(name)
        if node is None:
            continue
        mains = [
            c.key.split("@", 1)[1] for c in node.children
            if c.key.startswith("Warhead@") and c.value in MAIN_TYPES
            and not c.key.lower().endswith(NOT_A_MAIN)
        ]
        if len(mains) > 1:
            out[name] = sorted(mains)
    return out


def main() -> int:
    inherits, local_fx = scan_source()
    multi = resolved_mains()

    w1, w2, w3, w4, w6 = [], [], [], [], []
    missing = collections.Counter()
    for name, parents in sorted(inherits.items()):
        wh = [p for p in parents if p.startswith("^Warhead_")]
        pr = [p for p in parents if p.startswith("^Projectile_")]
        fx = [p for p in parents if p.startswith("^Effect_")]
        if len(parents) > 3:
            w1.append([f"`{name}`", str(len(parents)), " ┬╖ ".join(f"`{p}`" for p in parents[:4])])
        if len(wh) > 1:
            w2.append([f"`{name}`", " ┬╖ ".join(f"`{p}`" for p in wh)])
        if len(pr) > 1:
            w3.append([f"`{name}`", " ┬╖ ".join(f"`{p}`" for p in pr)])
        if len(fx) > 1:
            w4.append([f"`{name}`", " ┬╖ ".join(f"`{p}`" for p in fx)])
        if not wh:
            missing["^Warhead_*"] += 1
        if not pr:
            missing["^Projectile_*"] += 1
        if not fx:
            missing["^Effect_*"] += 1
    for name, nodes in sorted(local_fx.items()):
        w6.append([f"`{name}`", str(len(nodes)), " ┬╖ ".join(f"`{n}`" for n in nodes[:3])])

    w5 = [[f"`{k}`", str(len(v)), " ┬╖ ".join(f"`{x}`" for x in v[:4])]
          for k, v in sorted(multi.items())]

    counts = {
        "W1": (len(w1), W1_BASELINE, "more than 3 inherits"),
        "W2": (len(w2), W2_BASELINE, "two or more `^Warhead_*` inherits"),
        "W3": (len(w3), W3_BASELINE, "two or more `^Projectile_*` inherits"),
        "W4": (len(w4), W4_BASELINE, "two or more `^Effect_*` inherits"),
        "W5": (len(w5), W5_BASELINE, "more than one resolved MAIN warhead"),
        "W6": (len(w6), W6_BASELINE, "effect warheads declared LOCALLY"),
    }

    out = [h1("Weapon shape ΓÇö the ONE-WARHEAD / THREE-INHERIT law")]
    out.append(
        "**Maintainer ruling, 2026-09-06.** Every concrete weapon ends with exactly three "
        "inherits ΓÇö `^Warhead_*`, `^Projectile_*`, `^Effect_*` ΓÇö one main warhead, and no "
        "effect warheads of its own. Mechanic warheads (`FireShrapnel`, "
        "`GrantExternalCondition`) and the `*Percentage` / `*FriendlyFire` / `*ExtraDamage` "
        "halves of one main are NOT violations.\n")
    out.append(
        "Γ¢ö This **repeals the exemption** in `tools/audit/intentional_composites.py`. Its "
        "224 entries are no longer 'reviewed, keep' ΓÇö they are the worklist. The registry "
        "data stays useful: it says which mains someone chose on purpose.\n")
    out.append(f"concrete weapons with inherits: **{len(inherits)}**\n")
    out.append("| check | what | count | ratchet |\n|---|---|--:|--:|")
    for code, (n, base, what) in counts.items():
        flag = " Γ¢ö" if n > base else ""
        out.append(f"| {code} | {what} | **{n}**{flag} | {base} |")
    out.append("")
    out.append("| I7 informational ΓÇö missing template | weapons |\n|---|--:|")
    for k, v in sorted(missing.items()):
        out.append(f"| no `{k}` inherit | {v} |")
    out.append(
        "\n_I7 is a REVIEW QUEUE, not a defect count ΓÇö an instant or utility weapon may "
        "legitimately have no projectile. Do not ratchet it without a per-weapon pass._\n")

    for code, rows, cols in (
        ("W1", w1, ["weapon", "inherits", "first four"]),
        ("W2", w2, ["weapon", "warhead templates"]),
        ("W3", w3, ["weapon", "projectile templates"]),
        ("W4", w4, ["weapon", "effect templates"]),
        ("W5", w5, ["weapon", "mains", "which"]),
        ("W6", w6, ["weapon", "nodes", "first three"]),
    ):
        n, base, what = counts[code]
        out.append(h2(f"{code} ΓÇö {what} ({n} vs ratchet {base})"))
        out.append(table(cols, rows[:40]))
        if len(rows) > 40:
            out.append(f"\n_... and {len(rows) - 40} more._\n")

    failed = [c for c, (n, base, _) in counts.items() if n > base]
    if failed:
        out.append(f"\n**FAIL ΓÇö {', '.join(failed)} rose above baseline.** A weapon was given "
                   "a second warhead, projectile or effect. The law allows exactly three "
                   "inherits and one main.\n")
    else:
        out.append("\n_all buckets at or below their ratchets_ ΓÇö this is the pre-existing "
                   "conversion backlog. **Lower each baseline as you convert; never raise "
                   "one.**\n")

    print("\n".join(out))
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
