#!/usr/bin/env python3
"""audit_armor_upgrade_harm.py — the ARMOR PLATING layer's invariants.

Incident 2026-08-16. The maintainer asked, while reviewing the plating rework:
*"now that I think about it would that mean that averaging can also make the unit
take MORE damage? this is a serious concern"*. It did — 98 of 1152 cells, worst
1.84x, because a plating was AVERAGED with the class armor and
`(class + plating) / 2` exceeds `class` whenever the plating row does.

**That specific arithmetic is now gone.** Platings are LAYER-SELECTED: while one is
active it REPLACES the class armor (`AreaDamageWarhead.DamageVersus`), so only one
row is ever read and there is nothing to average. Being weak against one damage
axis is then the DESIGN — a plating is a trade, not a free upgrade — which is why
this file no longer checks "is any row above the class armor". It would now flag
the counter-play itself.

What replaced it are three invariants the layer model actually depends on:

  **I1 — NO GAPS.** Every template must carry a row for every plating. This is the
  one that bites hardest: both the engine and Cameo's override select armors with
  `Versus.ContainsKey(type)`, and an EMPTY match list returns 100. So a missing row
  does not mean "no opinion", it means the plated unit loses its armor entirely
  against that weapon — a superheavy tank taking 100% from bullets instead of ~20%.
  A plating is sparse by nature, which is exactly why the columns must be full.

  **I2 — THE COLUMN LAW.** Every plating's mean across all templates is the SAME, so
  no plating is stronger overall; they differ only in WHAT they resist. This is the
  transpose of W25 S1's row law, and the two are independent because platings live
  outside the class-armor set that S1 normalises. The common mean is 70 rather than
  100 because a plating REPLACES the class armor, and six class armors already average
  better than 100 — at 100 a hero or an aircraft got 25-35% WORSE for taking one.

  **I3 — CLOSURE.** Every weapon family has at least one plating that counters it
  (a row below the common mean) and at least one it beats (a row above it). Maintainer:
  *"every weapon family has an armor counter and every armor type has a weapon
  counter"*. Without this a family is either unanswerable or pointless.

Why this needs its own guard at all: none of it is visible to anything else we run.
The yaml is well-formed, every value sits inside the window, the resolver is happy,
and the game boots — a boot gate cannot see a number that is merely WRONG, and a
MISSING row is not even a number.
"""
from __future__ import annotations

import pathlib
import re
import statistics
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "balance"))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

HEADER = re.compile(r"^\^Warhead_(\w+?)_(\w+):$")

# The plating taxonomy and its target column mean, read from the generator so this file
# cannot drift from what actually ships. `Shield` is NOT a plating: it is a layer of its
# own, already selected in yaml via `!shielded`.
import gen_weapon_template as _gen  # noqa: E402

PLATINGS = tuple(_gen.PLATING_CYCLE)
TARGET_MEAN = _gen.PLATING_TARGET_MEAN

# Templates the generator does not emit, so they carry no plating columns yet.
# Listed rather than silently skipped: each is a real gap in the layer.
UNGENERATED = ("^Warhead_Nuclear_Super", "^Warhead_Sniper_Light")


def templates(text: str):
    """`^Warhead_<Family>_<Level>` -> {armor: value} for each MAIN warhead."""
    cur = None
    inmain = invs = False
    rows: dict[str, int] = {}
    out = []
    for line in text.split("\n"):
        m = HEADER.match(line.rstrip())
        if m:
            if cur and rows:
                out.append((cur, rows))
            cur, rows, inmain, invs = m.group(0)[:-1], {}, False, False
            continue
        if cur is None:
            continue
        s = line.strip()
        if s.startswith("Warhead@"):
            inmain = not s.split(":")[0].endswith(
                ("_Percentage", "_ExtraDamage", "_FriendlyFire"))
            invs = False
            continue
        if inmain and s == "Versus:":
            invs = True
            continue
        if invs:
            if line.startswith("\t\t\t") and ":" in s:
                key, value = s.split(":", 1)
                try:
                    rows[key] = int(value)
                    continue
                except ValueError:
                    pass
            invs = False
    if cur and rows:
        out.append((cur, rows))
    return out


def main() -> int:
    path = ROOT / "mods" / "cameo" / "weapons" / "weapons.yaml"
    found = [(n, r) for n, r in templates(path.read_text(encoding="utf-8"))
             if n not in UNGENERATED]

    print("# audit_armor_upgrade_harm — the armor-plating layer's invariants")
    print()
    print(f"Checked **{len(found)}** generated `^Warhead_*` templates against "
          f"**{len(PLATINGS)}** platings "
          f"(skipping {', '.join('`' + u + '`' for u in UNGENERATED)}, which the "
          f"generator does not emit).")
    print()

    gaps = [(n, p) for n, r in found for p in PLATINGS if p not in r]
    means = {p: [r[p] for _n, r in found if p in r] for p in PLATINGS}
    no_counter, no_exposure = [], []
    for n, r in found:
        vals = [r[p] for p in PLATINGS if p in r]
        if not vals:
            continue
        if min(vals) >= TARGET_MEAN:
            no_counter.append((n, min(vals)))
        if max(vals) <= TARGET_MEAN:
            no_exposure.append((n, max(vals)))

    failed = 0

    print("## I1 — no gaps (a missing row makes `DamageVersus` return 100)")
    print()
    if gaps:
        failed = 1
        print(f"**FAIL — {len(gaps)} missing plating row(s).** A plated unit hit by one of")
        print("these weapons loses its armor entirely rather than resisting normally.")
        print()
        print("| template | missing plating |")
        print("|---|---|")
        for n, p in gaps[:40]:
            print(f"| `{n}` | `{p}` |")
        if len(gaps) > 40:
            print(f"\n_... and {len(gaps) - 40} more._")
    else:
        print("_clean_ — every template carries a row for every plating.")
    print()

    print(f"## I2 — the column law (every plating averages {TARGET_MEAN:g} "
          f"across all templates)")
    print()
    print("| plating | mean | min | max |")
    print("|---|--:|--:|--:|")
    for p in PLATINGS:
        v = means[p]
        if not v:
            continue
        mean = statistics.fmean(v)
        flag = "" if abs(mean - TARGET_MEAN) <= 1.0 else " ⚠"
        if abs(mean - TARGET_MEAN) > 1.0:
            failed = 1
        print(f"| `{p}` | **{mean:.2f}**{flag} | {min(v)} | {max(v)} |")
    print()

    print("## I3 — closure (every family has a counter and an exposure)")
    print()
    if no_counter or no_exposure:
        failed = 1
        for n, v in no_counter:
            print(f"- **FAIL** `{n}` has no counter — its lowest plating row is {v}.")
        for n, v in no_exposure:
            print(f"- **FAIL** `{n}` has no exposure — its highest plating row is {v}.")
    else:
        print("_clean_ — every family is countered by at least one plating and beats "
              "at least one.")
    print()

    if failed:
        print("Fix: `docs/design/ARMOR_LAYERS.md` §F/§G. The plating columns "
              "are generated by `gen_weapon_template.plating_rows` — correct the "
              "COMPOSITION table there, never the yaml.")
    return failed


if __name__ == "__main__":
    raise SystemExit(main())
