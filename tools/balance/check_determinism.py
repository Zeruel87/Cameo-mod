#!/usr/bin/env python3
"""check_determinism.py — does the extract produce the same ledgers twice?

The balance pipeline is supposed to behave like a compiler: the same tree, the same
model and the same tools produce the same numbers. `BALANCE_PIPELINE.md` rests on it —
a raw-ledger diff is only allowed to mean "the game changed", and a derived diff only
"the model changed". If extraction is not deterministic, both sentences are false and
`audit_balance_drift` starts reporting noise as if it were a balance edit.

Nothing measured that. This does.

    python tools/balance/check_determinism.py
    python tools/balance/check_determinism.py --faction ra1_soviets   # fast scope
    python tools/balance/check_determinism.py --keep                  # keep the dumps

HOW
===

Extraction runs twice, in SEPARATE PROCESSES with different `PYTHONHASHSEED` and `TZ`.
Separate processes are the whole point: within one interpreter every run shares a hash
seed, so set and dict iteration order is stable by accident and an ordering leak stays
invisible. Across two seeds it shows up immediately.

Each run builds the ledgers IN MEMORY and dumps them to its own temp directory. Nothing
is written under `docs/balance/`, so this can never be the thing that moved a ledger.

WHAT IT CATCHES
===============

  ordering   a list built by iterating a set or an unordered dict
  hashing    anything whose output depends on `hash()` of a str/bytes/frozenset
  time       a timestamp, date or timezone-dependent value reaching an artifact
  paths      an absolute path baked into output

`serialize()` already writes `sort_keys=True`, so mapping order is not at risk — but
sorting keys does nothing for the order of a LIST, which is exactly where a set leaks.

WHAT IT DOES NOT CATCH
======================

A single green run proves these two configurations agree. It does not prove the
pipeline is deterministic everywhere: a different OS, Python version, filesystem
ordering or locale is a different experiment. It also cannot see nondeterminism that
is stable within a process but varies by machine. Report it as what it is — evidence,
not a theorem.
"""
from __future__ import annotations

import argparse
import hashlib
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parents[2]

# Runs the real extraction in-memory and dumps each artifact to $CAMEO_DUMP.
# It deliberately reuses extract_stats' own serialize(), so a serialization change is
# inside what is being tested rather than beside it.
DRIVER = r"""
import json, os, pathlib, sys
sys.path.insert(0, str(pathlib.Path(os.environ["CAMEO_ROOT"]) / "tools" / "balance"))
import extract_stats as es
from cameo_model import Model

out = pathlib.Path(os.environ["CAMEO_DUMP"]); out.mkdir(parents=True, exist_ok=True)
only = os.environ.get("CAMEO_ONLY") or None

ledgers, sidecars = es.build_both(Model(), only)
for name, doc in ledgers.items():
    (out / f"raw__{name}.json").write_text(es.serialize(doc), encoding="utf-8")
for name, doc in sidecars.items():
    (out / f"derived__{name}.json").write_text(es.serialize(doc), encoding="utf-8")
(out / "model___model.json").write_text(es.serialize(es.model_constants()),
                                        encoding="utf-8")
"""


def one_run(dump: pathlib.Path, seed: str, tz: str, only: str | None) -> None:
    env = dict(os.environ,
               PYTHONHASHSEED=seed,
               TZ=tz,
               LC_ALL="C",
               PYTHONIOENCODING="utf-8",
               CAMEO_ROOT=str(ROOT),
               CAMEO_DUMP=str(dump))
    if only:
        env["CAMEO_ONLY"] = only
    else:
        env.pop("CAMEO_ONLY", None)
    r = subprocess.run([sys.executable, "-c", DRIVER], cwd=ROOT, env=env)
    if r.returncode != 0:
        raise SystemExit(f"extraction failed under PYTHONHASHSEED={seed} "
                         f"(exit {r.returncode}) — fix that before reading determinism")


def digest(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def first_difference(a: pathlib.Path, b: pathlib.Path) -> str:
    """The first line that differs, with its number — not just 'hashes differ'.

    A hash mismatch alone sends someone hunting through a 40 000-line JSON file. The
    line is usually enough to name the leaking field on sight.
    """
    la = a.read_text(encoding="utf-8").splitlines()
    lb = b.read_text(encoding="utf-8").splitlines()
    for i, (x, y) in enumerate(zip(la, lb), 1):
        if x != y:
            return f"line {i}\n      run A: {x.strip()[:100]}\n      run B: {y.strip()[:100]}"
    if len(la) != len(lb):
        return f"identical for {min(len(la), len(lb))} lines, then lengths differ " \
               f"({len(la)} vs {len(lb)})"
    return "no line differs — the bytes differ (line endings or trailing whitespace)"


def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--faction", help="ledger-name substring filter (much faster)")
    ap.add_argument("--keep", action="store_true",
                    help="keep both dump directories for inspection")
    args = ap.parse_args()

    tmp = pathlib.Path(tempfile.mkdtemp(prefix="cameo_determinism_"))
    a, b = tmp / "runA", tmp / "runB"

    print("# balance determinism\n")
    print("Two extractions, separate processes, different hash seed and timezone.")
    print("Nothing is written under `docs/balance/`.\n")
    print("| run | PYTHONHASHSEED | TZ |")
    print("|---|---|---|")
    print("| A | 0 | UTC |")
    print("| B | 524287 | Australia/Eucla |")
    print()

    try:
        one_run(a, "0", "UTC", args.faction)
        # A deliberately awkward zone: +8:45, so a half-hour assumption breaks too.
        one_run(b, "524287", "Australia/Eucla", args.faction)

        names = sorted({p.name for p in a.glob("*.json")} |
                       {p.name for p in b.glob("*.json")})
        if not names:
            print("**FAIL** — the extraction produced no artifacts to compare.")
            return 2

        missing, differing = [], []
        for n in names:
            pa, pb = a / n, b / n
            if not pa.exists() or not pb.exists():
                missing.append(n)
            elif digest(pa) != digest(pb):
                differing.append(n)

        print(f"Artifacts compared: **{len(names)}**\n")
        if not missing and not differing:
            print(f"**PASS** — all {len(names)} artifacts are byte-identical across "
                  "both configurations.\n")
            print("This is evidence, not a proof: it shows these two configurations "
                  "agree.\nA different OS, Python version or filesystem ordering is a "
                  "separate experiment.")
            return 0

        print("**FAIL** — extraction is not reproducible.\n")
        for n in missing:
            print(f"* `{n}` — produced by only one of the two runs")
        for n in differing:
            print(f"* `{n}` — differs at {first_difference(a / n, b / n)}")
        print("\nA difference under a changed hash seed is almost always a LIST built "
              "by iterating\na set or an unordered mapping. `serialize()` sorts dict "
              "keys, so mapping order is\nalready safe — sort the list at the point it "
              "is built, not at the point it is written.")
        if not args.keep:
            print(f"\n_Re-run with `--keep` to inspect both dumps._")
        return 1
    finally:
        if args.keep:
            print(f"\ndumps: {a}\n      {b}")
        else:
            shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())
