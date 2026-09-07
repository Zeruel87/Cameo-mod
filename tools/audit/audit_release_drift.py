#!/usr/bin/env python3
"""audit_release_drift.py - has a weapon drifted from the build players played?

Every other gate in this tree measures the tree against ITSELF. A defect that
lands in one commit silently becomes the baseline for the next, so a weapon can
walk away from its shipped value one self-consistent commit at a time and no
audit ever goes red. That is exactly what happened:

    HydraSpit, shipped playtest-20260709   4 mains x  2000 =  8000 flat + 4% max HP
    HydraSpit, before the W24 collapse     4 mains x 18000 = 72000 flat
    HydraSpit, now                         1 main  x 18000 = 18000 flat + 9% max HP

An earlier sweep inflated the per-main value 9x; the collapse then dropped three
mains and kept one, landing at 2.25x the shipped damage. Both steps were
self-consistent. Only an EXTERNAL baseline can see it.

  D1 INFLATED  a weapon deals MORE than it shipped
  D2 WEAKENED  a weapon deals LESS than it shipped
  D3 EXTREME   |ratio| >= 3x either way - the ones a player will feel immediately
  D4 UNMATCHED a weapon in the baseline that no longer exists under that name
  D5 ACCEPTED  a deliberate value edit, excluded from D1-D3 (informational)

D5 exists because not all drift is damage. 43 weapons differ from the release with their
MAIN COUNT UNCHANGED - nobody collapsed them, somebody edited the number. The maintainer
ruled on 2026-09-07 that those are deliberate and are accepted. They live in
`docs/reference/drift_accepted.json`, and the acceptance is PINNED TO THE VALUE: if such a
weapon's damage moves again it stops matching the pin and returns to D1/D2 as new drift.
Acceptance is per value, never a permanent pass for a weapon.

⛔ D4 is the hole that makes the other three lie. This audit can only compare weapons it
can still FIND, so renaming a weapon silently removes it from the comparison - a naming
sweep could take a 7x weapon out of D1 without changing a single damage value. D4 counts
them so the corpus can never shrink unnoticed. Renames are legitimate; a RISE in D4 means
the gate is now blind to more weapons than it was, and the new ids have to be checked by
hand before the ratchet is lowered.

The baseline is a committed snapshot (docs/reference/release_baseline_*.json),
so this audit needs no worktree and no network. Regenerate it only when a NEW
release ships, with `gen_release_baseline.py` - never to make a red run go green.

⚠ A weapon absent from the baseline is NEW since the release and is not judged.
⚠ The metric is total flat MAIN damage. A percentage half moving on its own is
   not visible here; DESIGN's collapse law covers both.

Usage: python tools/audit/audit_release_drift.py [--list] [--min-ratio 3.0]
"""

from __future__ import annotations

import argparse
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

import miniyaml
from gen_release_baseline import snapshot
from report import h1, h2, table

# Measured 2026-09-07 against playtest-20260709, with the 43 D5-accepted value edits
# excluded (maintainer ruling 2026-09-07). LOWER ONLY.
# ⛔ Never raise one of these to make a batch pass: a rise means a collapse or a
# sweep moved a weapon further from the build players actually played.
D1_BASELINE = 133
D2_BASELINE = 62
D3_BASELINE = 27
D4_BASELINE = 335
D5_BASELINE = 43

BASELINE_DIR = "docs/reference"


def load_accepted(repo: pathlib.Path) -> dict:
    """Deliberate value edits, pinned to the value that was accepted."""
    f = repo / BASELINE_DIR / "drift_accepted.json"
    if not f.exists():
        return {}
    return json.loads(f.read_text(encoding="utf-8")).get("weapons", {})


def load_baseline(repo: pathlib.Path) -> tuple[dict, dict]:
    """Newest committed release baseline, as (meta, {weapon: {flat, mains}})."""
    files = sorted((repo / BASELINE_DIR).glob("release_baseline_*.json"))
    if not files:
        raise SystemExit(f"no release baseline in {BASELINE_DIR}/ - "
                         "run tools/audit/gen_release_baseline.py --tag <release>")
    raw = json.loads(files[-1].read_text(encoding="utf-8"))
    return raw, raw["weapons"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--list", action="store_true", help="print every drifted weapon")
    ap.add_argument("--min-ratio", type=float, default=3.0,
                    help="the D3 EXTREME threshold, either direction (default 3.0)")
    args = ap.parse_args()

    repo = pathlib.Path(__file__).resolve().parents[2]
    meta, base = load_baseline(repo)
    accepted = load_accepted(repo)
    now = snapshot(repo)

    rows = []
    unmatched = []
    still_accepted = []
    for name, was in base.items():
        if name not in now:
            unmatched.append(name)        # renamed or deleted: INVISIBLE to D1-D3, so count it
            continue
        old, new = was["flat"], now[name]["flat"]
        if old <= 0:
            continue
        ratio = new / old
        if abs(ratio - 1.0) < 0.01:
            continue
        pin = accepted.get(name)
        if pin is not None and pin.get("accepted") == new:
            still_accepted.append(name)     # unchanged since the ruling - not drift
            continue
        rows.append((ratio, name, old, was["mains"], new, now[name]["mains"]))

    rows.sort(key=lambda r: -r[0])
    inflated = [r for r in rows if r[0] > 1]
    weakened = [r for r in rows if r[0] < 1]
    extreme = [r for r in rows if r[0] >= args.min_ratio or r[0] <= 1 / args.min_ratio]
    shared = len(set(base) & set(now))

    print(h1("audit_release_drift - measured against the build players played"))
    print(f"\nbaseline: **{meta['_release_tag']}** (`{meta['_release_commit']}`), "
          f"{meta['_weapons']} weapons · {shared} shared with the tree · "
          f"**{shared - len(rows)} unchanged**\n")

    checks = [
        ["D1", "INFLATED - deals more than it shipped", len(inflated), D1_BASELINE],
        ["D2", "WEAKENED - deals less than it shipped", len(weakened), D2_BASELINE],
        ["D3", f"EXTREME - {args.min_ratio:g}x or worse, either way", len(extreme), D3_BASELINE],
        ["D4", "UNMATCHED - in the release, gone under that name", len(unmatched), D4_BASELINE],
        ["D5", "ACCEPTED value edit (informational)", len(still_accepted), D5_BASELINE],
    ]
    print(table(["code", "check", "count", "ratchet", ""],
                [[c, d, str(n), str(b), "PASS" if n <= b else "FAIL"] for c, d, n, b in checks]))

    if extreme:
        print(h2(f"D3 EXTREME - {len(extreme)} weapon(s) a player will feel"))
        print(table(["weapon", "shipped", "now", "x", "mains"],
                    [[n, str(o), str(w), f"{r:.2f}", f"{om} -> {nm}"]
                     for r, n, o, om, w, nm in extreme]))
        print()

    if args.list:
        print(h2(f"every drifted weapon - {len(rows)}"))
        print(table(["weapon", "shipped", "now", "x", "mains"],
                    [[n, str(o), str(w), f"{r:.2f}", f"{om} -> {nm}"]
                     for r, n, o, om, w, nm in rows]))
        print()

    if args.list and unmatched:
        print(h2(f"D4 UNMATCHED - {len(unmatched)} weapon(s) the gate can no longer see"))
        print(chr(10).join("- `" + n + "`" for n in sorted(unmatched)[:400]))
        print()

    over = [c for c, _d, n, b in checks if n > b and c != "D5"]
    if over:
        print(f"\n**FAIL: {', '.join(over)} above ratchet.** A rise means a weapon moved "
              "FURTHER from the shipped build, or that the gate went BLIND to more of them. "
              "Lower a baseline as the repair lands; never raise one.\n")
        return 1
    print("\n_within ratchet_ — but every row above is still a weapon that does not "
          "deal what it shipped.\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
