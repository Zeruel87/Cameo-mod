#!/usr/bin/env python3
"""verify_generator_sync.py — guard that gen_weapon_template.py still reproduces
the ^Warhead_* template families that live in mods/cameo/weapons/weapons.yaml.

Runs the generator, extracts each `^Warhead_<Family>_<Level>:` block from BOTH
the generator output and weapons.yaml, and diffs them line-by-line. Any drift
(generator no longer emits what the file contains, or vice-versa) exits non-zero.

This is the acceptance test for the "regenerate is a no-op" invariant: once the
generator matches the file, a regenerate+splice cannot silently revert the
AreaDamage/universal-FF conversion. ^Warhead_Nuclear_Super and ^Warhead_Sniper_Light
are hand-tuned and are NOT emitted by the generator (HAND_TUNED), so they are
skipped here too.

Usage: python tools/balance/verify_generator_sync.py   (from the repo root)
"""
from __future__ import annotations
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
GEN = ROOT / "tools" / "balance" / "gen_weapon_template.py"
YAML = ROOT / "mods" / "cameo" / "weapons" / "weapons.yaml"


def col0(line: str) -> bool:
    return bool(line) and line[0] not in (" ", "\t")


def blocks(lines):
    """name -> list[str] block body (header + indented lines), keyed by the
    top-level `^Warhead_...:` header. Ignores comments and `######` banners."""
    out = {}
    i, n = 0, len(lines)
    while i < n:
        ln = lines[i].rstrip("\r\n")
        if col0(ln) and ln.startswith("^Warhead_") and ln.rstrip().endswith(":"):
            name = ln.rstrip()[:-1]
            body = [ln]
            i += 1
            while i < n:
                nxt = lines[i].rstrip("\r\n")
                if col0(nxt):  # next top-level node ends the block
                    break
                if nxt.strip():  # keep only non-blank body lines (blank-line agnostic)
                    body.append(nxt)
                i += 1
            out[name] = body
        else:
            i += 1
    return out


def main():
    proc = subprocess.run([sys.executable, str(GEN)], capture_output=True, text=True)
    if proc.returncode != 0:
        print("generator FAILED to run:\n" + proc.stderr, file=sys.stderr)
        return 2
    gen = blocks(proc.stdout.splitlines())
    fil = blocks(YAML.read_text(encoding="utf-8").splitlines())

    drift = 0
    missing = sorted(set(gen) - set(fil))
    HAND_TUNED = {"^Warhead_Nuclear_Super", "^Warhead_Sniper_Light"}
    extra = sorted(n for n in set(fil) - set(gen) if n not in HAND_TUNED)
    if missing:
        drift += len(missing)
        print(f"[X] generator emits {len(missing)} template(s) ABSENT from weapons.yaml:")
        for n in missing:
            print(f"      {n}")
    if extra:
        drift += len(extra)
        print(f"[X] weapons.yaml has {len(extra)} ^Warhead_ template(s) the generator does NOT emit:")
        for n in extra:
            print(f"      {n}")

    for name in sorted(set(gen) & set(fil)):
        g, f = gen[name], fil[name]
        if g == f:
            continue
        drift += 1
        print(f"\n[X] DRIFT in {name}:")
        gl, fl = len(g), len(f)
        for k in range(max(gl, fl)):
            gv = g[k] if k < gl else "<none>"
            fv = f[k] if k < fl else "<none>"
            if gv != fv:
                print(f"      gen : {gv}")
                print(f"      file: {fv}")

    ok = len(set(gen) & set(fil))
    print(f"\nchecked {ok} shared template(s); drift = {drift}")
    if drift == 0:
        print("[OK] generator reproduces every ^Warhead_ family in weapons.yaml (no-op regenerate).")
    return 1 if drift else 0


if __name__ == "__main__":
    sys.exit(main())
