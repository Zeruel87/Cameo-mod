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
import json
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
# W1 IS A RATE, NOT A COUNT (maintainer ruled 2026-09-12, after I explained the trade-off).
# Why: between ae02eedc0 and b235c698 the corpus grew 84 weapons (2061 -> 2145 concrete
# weapons with inherits). W1's absolute count rose 574 -> 585 and broke the ratchet, while its
# SHARE of the corpus FELL 27.85% -> 27.27%. The tree got proportionally cleaner and the gate
# went red anyway, purely because adding units adds violations at the prevailing rate. An
# absolute ratchet cannot tell "someone wrote a bad weapon" from "someone added a faction".
# W2 stays ABSOLUTE because its rate genuinely worsened (9.75% -> 10.54%) — that is a real
# regression and re-basing it would hide it.
#
# Stored in BASIS POINTS to keep the comparison integer-exact: fail iff
#   count * 10000 > W1_RATE_BP * corpus
# 585/2145 = 2727.3 bp, so 2728 is the current rate rounded up to the next basis point.
# LOWER ONLY — same rule as every count ratchet.
W1_RATE_BP = 2616   # 561/2145 = 2615.4 bp; 2630 before the compatibility promotion,
                    # 2728 before the dead-inherit slice
W1_BASELINE = 576   # historical count ratchet, kept for provenance; W1_RATE_BP is what gates
# Checks gated on a SHARE of the corpus instead of an absolute count.
RATE_CHECKS: dict[str, int] = {"W1": W1_RATE_BP}
RED = ' Γ¢ö'
W2_BASELINE = 177   # dual ^Warhead_ inherit; 226 -> 177 by the dead-inherit slice
                    # (was 210 before; the 226 regression is repaid and then some)
W3_BASELINE = 12    # dual ^Projectile_ inherit (21->12: same collapse)
W4_BASELINE = 51    # dual ^Effect_ inherit; Apocalypse effect composition owns its overrides
W5_BASELINE = 389   # more than one resolved MAIN warhead; merge-payload repairs
W6_BASELINE = 694   # weapons declaring an effect warhead locally
# W7/W8 added 2026-09-12 after the maintainer restated the law: the three inherits must come
# from a TEMPLATE, "and NEVER from another weapon". Nothing measured that clause before, so
# W1 could pass a weapon that inherits all three of its parents from other weapons. Both
# ratchets are set by THIS script's own first run, never from a scratch scan.
W7_BASELINE = 957   # inherits from another WEAPON (655 distinct weapon-parents)
W8_BASELINE = 858   # inherits a ^Template outside the three kinds; 874 -> 858 by promoting
                    # 33 ^Compatibility_* shims into real ^Warhead_* templates
                    # 687 -> 694: the TOP_LEVEL regex was fixed to match
                    # digit-starting keys (120mm_*, 8Inch, etc.), exposing
                    # 7 weapons previously hidden. LOWER ONLY.

KIND_PREFIXES = ("^Warhead_", "^Projectile_", "^Effect_")
SEP = " " + chr(0x00B7) + " "

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


def shape_main_nodes(node):
    """W5's structural flat nodes, including zero/healing/ally-only nodes.

    Unlike audit_three_way_split this is not a positive enemy-damage count.
    Keep the historical definition explicit; --compare-split explains the delta.
    """
    return [c for c in node.children
            if c.key.startswith("Warhead@") and c.value in MAIN_TYPES
            and not c.key.lower().endswith(NOT_A_MAIN)]


def resolved_mains(rs=None):
    """{weapon: [main warhead tags]} for weapons resolving to more than one main."""
    if rs is None:
        rs = miniyaml.Ruleset(ROOT)
    out = {}
    for name in sorted(rs.weapons):
        if name.startswith("^"):
            continue
        node = rs.resolve_weapon(name)
        if node is None:
            continue
        mains = [c.key.split("@", 1)[1] for c in shape_main_nodes(node)]
        if len(mains) > 1:
            out[name] = sorted(mains)
    return out


def compare_split(rs=None):
    """Exact set difference, without changing either predicate or ratchet."""
    import audit_three_way_split as split
    if rs is None:
        rs = miniyaml.Ruleset(ROOT)
    shape, positive, differences = {}, {}, []
    for name in sorted(rs.weapons):
        if name.startswith("^"):
            continue
        node = rs.resolve_weapon(name)
        if node is None:
            continue
        shape_nodes = {c.key: c for c in shape_main_nodes(node)}
        split_nodes = {c.key: c for c in split.main_warhead_nodes(node)}
        if len(shape_nodes) > 1:
            shape[name] = sorted(shape_nodes)
        if len(split_nodes) > 1:
            positive[name] = sorted(split_nodes)
        if (len(shape_nodes) > 1) == (len(split_nodes) > 1):
            continue
        nodes = []
        for key in sorted(shape_nodes.keys() ^ split_nodes.keys()):
            wh = shape_nodes.get(key) or split_nodes[key]
            reasons = []
            if not wh.key.startswith("Warhead@"):
                reasons.append("W5 requires a named Warhead@ node")
            if wh.value not in MAIN_TYPES:
                reasons.append("type outside W5 flat-damage types")
            if wh.key.lower().endswith(NOT_A_MAIN):
                reasons.append("W5 companion-suffix exclusion")
            if any(marker in wh.key for marker in split.COMPANION_MARKERS):
                reasons.append("split companion-name exclusion")
            if split.is_friendly_fire(wh):
                reasons.append("split friendly-fire/ally-only exclusion")
            try:
                if int(str(wh.get("Damage"))) <= 0:
                    reasons.append("non-positive damage")
            except ValueError:
                reasons.append("missing or non-integer damage")
            nodes.append(dict(key=key, type=wh.value, damage=wh.get("Damage"),
                              relationships=wh.get("ValidRelationships"), reasons=reasons))
        differences.append(dict(weapon=name, shape_mains=sorted(shape_nodes),
                                split_mains=sorted(split_nodes), differing_nodes=nodes))
    return dict(shape_count=len(shape), split_count=len(positive),
                shape_only=sorted(shape.keys() - positive.keys()),
                split_only=sorted(positive.keys() - shape.keys()), differences=differences,
                policy="informational reconciliation; neither raw count nor ratchet is changed")


def main() -> int:
    inherits, local_fx = scan_source()
    multi = resolved_mains()

    w1, w2, w3, w4, w6, w7, w8 = [], [], [], [], [], [], []
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
        # W7/W8 - the maintainer restated the law 2026-09-12: the three inherits must come
        # from a TEMPLATE, "and NEVER from another weapon". Nothing measured that clause, so
        # weapon-to-weapon inheritance had no ratchet at all while W1 counted only ARITY.
        # A weapon can satisfy W1-W4 with exactly three parents and still inherit all three
        # from other weapons.
        from_weapon = [pp for pp in parents if not pp.startswith("^")]
        legacy = [pp for pp in parents
                  if pp.startswith("^") and not pp.startswith(KIND_PREFIXES)]
        if from_weapon:
            w7.append([f"`{name}`", str(len(from_weapon)),
                       SEP.join(f"`{pp}`" for pp in from_weapon[:4])])
        if legacy:
            w8.append([f"`{name}`", str(len(legacy)),
                       SEP.join(f"`{pp}`" for pp in legacy[:4])])
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
        "W7": (len(w7), W7_BASELINE, "inherits from ANOTHER WEAPON, not a template"),
        "W8": (len(w8), W8_BASELINE, "inherits a `^Template` that is not one of the three kinds"),
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
    out.append("W5 counts structural flat-damage nodes, including zero/healing/ally-only nodes; "
               "the split audit counts positive non-companion damage. Both resolve the full "
               "concrete weapon corpus. Use `--compare-split` for exact differences.\n")
    out.append("| check | what | count | ratchet |\n|---|---|--:|--:|")
    corpus = len(inherits)
    for code, (n, base, what) in counts.items():
        if code in RATE_CHECKS:
            bp = (n * 10000 + corpus - 1) // corpus if corpus else 0
            over = n * 10000 > RATE_CHECKS[code] * corpus
            out.append(f"| {code} | {what} | **{n}** ({bp / 100:.2f}% of {corpus})"
                       + (RED if over else "")
                       + f" | {RATE_CHECKS[code] / 100:.2f}% |")
        else:
            out.append(f"| {code} | {what} | **{n}**" + (RED if n > base else "")
                       + f" | {base} |")
    out.append("")
    out.append("| I7 informational ΓÇö missing template | weapons |\n|---|--:|")
    for k, v in sorted(missing.items()):
        out.append(f"| no `{k}` inherit | {v} |")
    out.append(
        "\n_I7 is a REVIEW QUEUE, not a defect count ΓÇö an instant or utility weapon may "
        "legitimately have no projectile. Do not ratchet it without a per-weapon pass._\n")

    for code, rows, cols in (
        ("W7", w7, ["weapon", "weapon-parents", "first four"]),
        ("W8", w8, ["weapon", "legacy templates", "first four"]),
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

    def over_ratchet(code, n, base):
        """Rate checks compare a SHARE of the corpus; the rest compare an absolute count."""
        if code in RATE_CHECKS:
            return n * 10000 > RATE_CHECKS[code] * corpus
        return n > base

    failed = [c for c, (n, base, _) in counts.items() if over_ratchet(c, n, base)]
    if failed:
        out.append(f"\n**FAIL ΓÇö {', '.join(failed)} rose above baseline.** A weapon was given "
                   "a second warhead, projectile or effect. The law allows exactly three "
                   "inherits and one main.\n")
    else:
        out.append("\n_all buckets at or below their ratchets_ ΓÇö this is the pre-existing "
                   "conversion backlog. **Lower each baseline as you convert; never raise "
                   "one.**\n")

    print("\n".join(out).rstrip())
    return 1 if failed else 0


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Weapon structure audit")
    parser.add_argument("--compare-split", action="store_true", help="explain the exact W5/split inventory difference as JSON")
    args = parser.parse_args()
    if args.compare_split:
        print(json.dumps(compare_split(), indent=2, ensure_ascii=False))
    else:
        raise SystemExit(main())
