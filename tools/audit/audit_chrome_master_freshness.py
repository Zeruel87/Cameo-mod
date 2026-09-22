#!/usr/bin/env python3
"""audit_chrome_master_freshness — did anyone edit the 4x master and forget to regenerate?

    python tools/audit/audit_chrome_master_freshness.py          # report
    python tools/audit/audit_chrome_master_freshness.py --fix    # report, then regenerate

⛔ WHY THIS EXISTS, AND WHY THE OTHER CHROME AUDIT CANNOT DO IT.
`audit_chrome_scale_variants.py` measures each sheet's ARTWORK EXTENT against its declared density.
That catches the original bug — a sheet laid out at 4x sitting in the 3x slot — because the extent
is wrong. It cannot catch the far more likely everyday mistake: someone edits one faction icon
inside `flags_4x.png`, commits, and the 1x/2x/3x sheets keep the OLD icon. Every extent still
matches, every dimension is right, both audits pass, and the game shows stale art at three of its
four scales.

⭐ SO THIS ONE IS ABOUT CONTENT, NOT SHAPE. `tools/art/generate_chrome_scales.py --write` records
the master's SHA-256 and each derived sheet's SHA-256 in `tools/art/chrome_masters.json`. This
audit re-hashes them and reports which side moved:

| master | derived | meaning |
|---|---|---|
| changed | unchanged | ⛔ the master was edited and never regenerated — `--fix` handles it |
| unchanged | changed | ⛔ a GENERATED sheet was hand-edited; the next run silently destroys it |
| changed | changed | ⚠ both moved — regenerated but not stamped, or edited by hand together |
| unchanged | unchanged | ✅ |

⚠ HASHES, NOT MTIMES. A checkout, a stash pop or a rebase rewrites mtimes without changing a
pixel, and git does not preserve them at all, so "the master is newer" is not a fact about content.

⚠ THE STAMP IS TOOLING METADATA, NOT ENGINE CONTENT. It lives under `tools/art/` deliberately:
the PNGs it describes are under `mods/` and carry the boot gate (CLAUDE.md rule 1), the stamp does
not, so the guard can be committed in a tree that cannot boot.

⛔ `--fix` REGENERATES ENGINE CONTENT and therefore does NOT clear the boot gate. It writes PNGs
under `mods/cameo/uibits/` and says so; you still have to launch the game before committing.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import subprocess
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

ROOT = pathlib.Path(__file__).resolve().parents[2]
STAMP = ROOT / "tools" / "art" / "chrome_masters.json"
UIBITS = ROOT / "mods" / "cameo" / "uibits"
GENERATOR = "tools/art/generate_chrome_scales.py"


def sha(path: pathlib.Path) -> str | None:
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError:
        return None


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--fix", action="store_true",
                    help="regenerate the derived sheets for any collection whose master moved")
    args, _unknown = ap.parse_known_args()

    print("# audit_chrome_master_freshness — are the generated sheets current with their master?\n")
    print("Compares SHA-256 against `tools/art/chrome_masters.json`. Catches an edited master whose")
    print("derived sheets were never regenerated — which every dimension-based check passes.\n")

    try:
        stamp = json.loads(STAMP.read_text(encoding="utf-8"))
    except OSError:
        print(f"⚠ No stamp at `{STAMP.relative_to(ROOT)}` — nothing is being guarded yet.\n")
        print("Seed it for a collection whose sheets are already correct:\n")
        print(f"    python {GENERATOR} flags --master flags_4x.png --emit 1,2,3 --stamp\n")
        print("**PASS** — vacuously; there is nothing to check.")
        return 0
    except ValueError as e:
        print(f"⛔ `{STAMP.relative_to(ROOT)}` is not valid JSON: {e}\n")
        print("**FAIL** — the stamp is the only state this guard has; repair or re-seed it.")
        return 1

    findings, stale = [], []
    print("| collection | master | derived sheets | verdict |")
    print("|---|---|---|---|")
    for name, rec in sorted(stamp.items()):
        master = UIBITS / rec["master"]
        now = sha(master)
        master_moved = now != rec.get("master_sha256")
        moved = [f for f, want in sorted(rec.get("derived", {}).items())
                 if sha(UIBITS / f) != want]
        gone = [f for f in sorted(rec.get("derived", {})) if not (UIBITS / f).exists()]

        if now is None:
            verdict = f"⛔ master `{rec['master']}` is missing"
            findings.append((name, verdict))
        elif gone:
            verdict = f"⛔ generated sheet(s) missing: {', '.join(gone)}"
            findings.append((name, verdict))
        elif master_moved and not moved:
            verdict = "⛔ **master edited, sheets NOT regenerated**"
            findings.append((name, verdict))
            stale.append((name, rec))
        elif moved and not master_moved:
            verdict = f"⛔ **generated sheet hand-edited**: {', '.join(moved)}"
            findings.append((name, verdict))
        elif master_moved and moved:
            verdict = "⚠ both moved — regenerated without re-stamping, or edited together"
            findings.append((name, verdict))
            stale.append((name, rec))
        else:
            verdict = "✅ current"
        print(f"| {name} | `{rec['master']}` | {len(rec.get('derived', {}))} | {verdict} |")

    print()
    if not findings:
        print("**PASS** — every generated sheet matches the master it was derived from.")
        return 0

    for name, verdict in findings:
        print(f"- **{name}** — {verdict}")
    print()

    if stale and args.fix:
        print("## --fix\n")
        for name, rec in stale:
            emit = ",".join(sorted({
                "1" if f == pathlib.Path(rec["master"]).stem.rsplit("_", 1)[0] + ".png"
                else f.rsplit("_", 1)[-1].removesuffix("x.png")
                for f in rec.get("derived", {})
            }, key=int))
            cmd = [sys.executable, GENERATOR, name, "--master", rec["master"],
                   "--emit", emit, "--write"]
            print(f"```\n{' '.join(cmd[1:])}\n```")
            r = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
            print(r.stdout[-1500:] or r.stderr[-1500:])
            if r.returncode != 0:
                print(f"**FAIL** — the generator exited {r.returncode}.")
                return 1
        print("⛔ **Regenerated sheets are engine content.** Run "
              "`python tools/audit/audit_chrome_scale_variants.py`, then BOOT GATE before "
              "committing (CLAUDE.md rule 1).\n")
        print("**FIXED** — re-run this audit to confirm.")
        return 1

    if stale:
        print(f"**FAIL — {len(findings)} collection(s) out of date.** Re-run with `--fix`, or by hand:\n")
        print(f"    python {GENERATOR} <collection> --master <master.png> --emit 1,2,3 --write\n")
        print("⛔ Regenerating writes engine content — BOOT GATE before committing "
              "(CLAUDE.md rule 1).")
    else:
        # ⛔ DO NOT OFFER --fix HERE. When only a DERIVED sheet moved, regenerating overwrites it
        # from an unchanged master and the hand edit is gone — the audit would have destroyed the
        # very work it flagged. The edit has to go into the master first.
        print(f"**FAIL — {len(findings)} collection(s) out of date.**\n")
        print("⛔ **Do not run `--fix` for this.** A generated sheet moved while its master did")
        print("not, so regenerating would overwrite the edit from the unchanged master and lose")
        print("it. Port the change into the master, regenerate, then re-stamp:\n")
        print(f"    python {GENERATOR} <collection> --master <master.png> --emit 1,2,3 --write\n")
        print("If the sheet is correct and the stamp is simply stale (a re-generation that was")
        print(f"never recorded), re-seed it with `--stamp` instead — it writes no pixels.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
