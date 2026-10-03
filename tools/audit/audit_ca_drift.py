#!/usr/bin/env python3
"""audit_ca_drift — which of Cameo's hand-copied CA files are behind upstream CA, and why.

Rewritten 2026-09-27 on top of the 2026-08-23 version, which diffed working trees two ways and
therefore could not tell whether CAMEO or CA had changed a file ("the drift runs in BOTH
directions"). This version answers that from CA's git history.

Cameo's `OpenRA.Mods.CA/` is a MANUAL copy of Combined Arms (github.com/Inq8/CAmod). It never
updates on its own, so every upstream bug fix and feature is missing until someone copies it.
On 2026-09-27 a latent crash in `HuntCA.cs` turned out to be fixed upstream already, and the
class looked "unused" only because its caller (the Lua binding `Scripting/CombatCAProperties.cs`)
had never been copied. This audit makes that check routine instead of something to remember.

Every Cameo file is compared, by line-ending-normalised content hash, against EVERY version of
every CA file in upstream history, which is what separates "an old upstream copy" from "a Cameo
edit":

  IDENTICAL        same content as upstream HEAD
  STALE            an OLD upstream version, no Cameo edits -> upstream fixes are missing and a
                   verbatim sync is safe (still build + boot it)
  MODIFIED         Cameo edited it; upstream has NOT changed since Cameo's base version
  MODIFIED+STALE   Cameo edited it AND upstream changed it since -> port the upstream diff by
                   hand, keeping Cameo's edits
  MOVED/REMOVED    the path no longer exists upstream (renamed, moved or deleted)
  CAMEO_ONLY       never existed in CA
  MISSING          an upstream file Cameo never copied (under any path in this repo)

"Base version" for a MODIFIED file = the upstream version of that path with the smallest line
diff to Cameo's copy.

Needs a FULL (not shallow) clone of CAmod: `git fetch --unshallow`. A shallow clone hides old
versions, and STALE files then look like Cameo edits. The audit refuses to run on one.

INFORMATIONAL: it never fails a build (it sits in run_all.sh's loop, so it always exits 0;
an unusable CA clone is reported as NOT a clean result). Usage:
    CA_ROOT=~/Documents/GitHub/CAmod python tools/audit/audit_ca_drift.py [--json OUT] [--limit N]
Sync tool that acts on this report: tools/audit/ca_vendor_sync.py.
"""

from __future__ import annotations

import argparse
import difflib
import hashlib
import json
import os
import pathlib
import subprocess
import sys
from collections import Counter, defaultdict

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import vector_codemod  # noqa: E402

REPO = pathlib.Path(__file__).resolve().parents[2]
CANDIDATES = [os.environ.get("CA_ROOT"), os.environ.get("CAMOD_DIR"), str(REPO.parent / "CAmod"),
              str(pathlib.Path.home() / "Documents" / "GitHub" / "CAmod")]


def find_ca() -> pathlib.Path | None:
    for c in CANDIDATES:
        if c and (pathlib.Path(c).expanduser() / ".git").exists():
            return pathlib.Path(c).expanduser()
    return None
PREFIX = "OpenRA.Mods.CA/"
CODE_DIRS = ("OpenRA.Mods.CA/", "OpenRA.Mods.Cameo/")


def git(repo: pathlib.Path, *args: str) -> str:
    return subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True,
                          text=True, encoding="utf-8", errors="replace").stdout


def normalise(data: bytes) -> str:
    text = data.decode("utf-8", errors="replace")
    if text.startswith("﻿"):
        text = text[1:]
    return text.replace("\r\n", "\n").replace("\r", "\n")


def norm_hash(text: str) -> str:
    return hashlib.sha1(text.encode("utf-8")).hexdigest()


def cat_blobs(repo: pathlib.Path, specs: list[str]) -> dict[str, bytes]:
    """Read many objects (`<rev>:<path>` or blob ids) in one `git cat-file --batch`.
    subprocess.run(input=...) services both pipes at once; a hand-rolled write-then-read
    deadlocks (and broke the pipe) once git's stdout buffer fills."""
    out: dict[str, bytes] = {}
    if not specs:
        return out
    raw = subprocess.run(["git", "-C", str(repo), "cat-file", "--batch"],
                         input=("\n".join(specs) + "\n").encode("utf-8"),
                         capture_output=True, check=True).stdout
    pos = 0
    for spec in specs:
        nl = raw.index(b"\n", pos)
        header = raw[pos:nl].decode("utf-8", errors="replace").split()
        pos = nl + 1
        if len(header) < 3 or header[-1] == "missing":
            continue
        size = int(header[2])
        out[spec] = raw[pos:pos + size]
        pos += size + 1
    return out


def upstream_versions(ca: pathlib.Path, ref: str):
    """Every blob that ever lived under OpenRA.Mods.CA/, newest first, with the commit that
    introduced it. Returns {path: [(blob, commit, date)]}."""
    log = git(ca, "log", ref, "--raw", "--no-abbrev", "--no-renames", "--format=@%H %cs",
              "--", PREFIX)
    versions: dict[str, list[tuple[str, str, str]]] = defaultdict(list)
    commit = date = ""
    for line in log.splitlines():
        if line.startswith("@"):
            commit, date = line[1:].split()
        elif line.startswith(":"):
            meta, path = line.split("\t", 1)
            new_blob = meta.split()[3]
            if path.endswith(".cs") and set(new_blob) != {"0"}:
                versions[path].append((new_blob, commit, date))
    return versions


def main() -> int:
    # Windows consoles default to cp1252; report text contains non-Latin-1 marks.
    sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--ca", type=pathlib.Path, default=None)
    parser.add_argument("--ref", default="origin/HEAD")
    parser.add_argument("--json", type=pathlib.Path)
    parser.add_argument("--limit", type=int, default=5, help="upstream commit subjects shown per file")
    args, _unknown = parser.parse_known_args()  # run_all.sh forwards its own flags

    print("# audit_ca_drift: vendored OpenRA.Mods.CA vs upstream Combined Arms\n")
    ca = args.ca or find_ca()
    if ca is None or not (ca / ".git").exists():
        print("_no CA clone found_: set `CA_ROOT` to a FULL clone of https://github.com/Inq8/CAmod.")
        print("\nNOT a clean result: this audit could not run.")
        return 0
    if git(ca, "rev-parse", "--is-shallow-repository").strip() == "true":
        print(f"_CA clone at `{ca}` is SHALLOW_: run `git -C {ca} fetch --unshallow`. A shallow clone hides")
        print("old upstream versions, so STALE files would be misreported as Cameo edits.")
        print("\nNOT a clean result: this audit could not run.")
        return 0

    head = git(ca, "rev-parse", args.ref).strip()
    versions = upstream_versions(ca, head)

    # Cameo's engine is on System.Numerics vectors (bleed, #569) and upstream CA is not: compare
    # upstream in the engine's vocabulary, or every converted-but-unedited copy reads as a Cameo edit.
    vectors = vector_codemod.is_vector_engine(REPO)
    upstream = vector_codemod.convert if vectors else (lambda s: s)
    if vectors:
        print("_Engine uses System.Numerics vectors: upstream text is compared after the float2/float3 -> "
              "Vector2/Vector3 conversion (tools/audit/vector_codemod.py)._\n")

    # Normalised hash of every upstream version, and where it sits in its path's history.
    all_blobs = sorted({b for vs in versions.values() for b, _, _ in vs})
    blob_text = {b: upstream(normalise(d)) for b, d in cat_blobs(ca, all_blobs).items()}
    hash_to_versions: dict[str, list[tuple[str, str, str]]] = defaultdict(list)
    for path, vs in versions.items():
        for blob, commit, date in vs:
            if blob in blob_text:
                hash_to_versions[norm_hash(blob_text[blob])].append((path, commit, date))

    head_files = {p for p in git(ca, "ls-tree", "-r", "--name-only", head, PREFIX).splitlines() if p.endswith(".cs")}
    head_text = {p[len(head) + 1:]: upstream(normalise(d)) for p, d in
                 cat_blobs(ca, [f"{head}:{p}" for p in sorted(head_files)]).items()}

    cameo_files = [p for p in git(REPO, "ls-files", PREFIX).splitlines() if p.endswith(".cs")]
    cameo_text = {p[5:]: normalise(d) for p, d in cat_blobs(REPO, [f"HEAD:{p}" for p in cameo_files]).items()}
    cameo_all_names = {pathlib.PurePosixPath(p).name for d in CODE_DIRS
                       for p in git(REPO, "ls-files", d).splitlines() if p.endswith(".cs")}
    head_names = defaultdict(list)
    for p in head_files:
        head_names[pathlib.PurePosixPath(p).name].append(p)

    def commits_since(path: str, commit: str) -> list[str]:
        out = git(ca, "log", "--format=%cs %s", f"{commit}..{head}", "--", path)
        return [line for line in out.splitlines() if line]

    rows = []
    for path in sorted(cameo_text):
        text = cameo_text[path]
        h = norm_hash(text)
        row = {"path": path, "status": "", "base_date": "", "base_blob": "", "upstream_since": [], "diff_lines": 0}
        if path in head_text and norm_hash(head_text[path]) == h:
            row["status"] = "IDENTICAL"
        elif h in hash_to_versions:
            same_path = [v for v in hash_to_versions[h] if v[0] == path] or hash_to_versions[h]
            vpath, commit, date = same_path[0]
            row["base_date"] = date
            row["upstream_path"] = vpath
            if vpath in head_text:
                row["status"] = "STALE"
                row["upstream_since"] = commits_since(vpath, commit)
            else:
                row["status"] = "MOVED/REMOVED"
        elif path in head_text:
            # Closest upstream version of this path = Cameo's likely base.
            # Cheap multiset score over every version, exact diff only for the closest few:
            # difflib against hundreds of versions of a 4000-line file takes minutes.
            best = None
            lines = text.splitlines()
            ours = Counter(lines)
            scored = []
            for blob, commit, date in versions.get(path, []):
                if blob in blob_text:
                    theirs = Counter(blob_text[blob].splitlines())
                    scored.append((sum(((ours - theirs) + (theirs - ours)).values()), blob, commit, date))
            for _, blob, commit, date in sorted(scored)[:3]:
                n = sum(1 for d in difflib.unified_diff(blob_text[blob].splitlines(), lines, lineterm="", n=0)
                        if d[:1] in "+-" and not d.startswith(("+++", "---")))
                if best is None or n < best[0]:
                    best = (n, blob, commit, date)
            if best is None:
                row["status"] = "MODIFIED"
            else:
                n, blob, commit, date = best
                row["diff_lines"], row["base_date"], row["base_blob"] = n, date, blob
                upstream_moved = norm_hash(blob_text[blob]) != norm_hash(head_text[path])
                row["status"] = "MODIFIED+STALE" if upstream_moved else "MODIFIED"
                if upstream_moved:
                    row["upstream_since"] = commits_since(path, commit)
        else:
            name = pathlib.PurePosixPath(path).name
            row["status"] = "MOVED/REMOVED" if (path in versions or name in head_names) else "CAMEO_ONLY"
            if name in head_names:
                row["upstream_since"] = [f"now at {p}" for p in head_names[name]]
        rows.append(row)

    missing = sorted(p for p in head_files
                     if p not in cameo_text and pathlib.PurePosixPath(p).name not in cameo_all_names)

    counts = defaultdict(int)
    for r in rows:
        counts[r["status"]] += 1

    print(f"Upstream: `{ca}` at `{head[:9]}` (`{args.ref}`; `git fetch` the clone first)\n")
    print("| status | files |\n|---|--:|")
    for status in ("IDENTICAL", "STALE", "MODIFIED", "MODIFIED+STALE", "MOVED/REMOVED", "CAMEO_ONLY"):
        print(f"| {status} | {counts[status]} |")
    print(f"| MISSING (upstream files never copied) | {len(missing)} |\n")

    for status, title in (("STALE", "STALE: safe verbatim syncs (upstream changes, no Cameo edits)"),
                          ("MODIFIED+STALE", "MODIFIED+STALE: port the upstream diff by hand"),
                          ("MOVED/REMOVED", "MOVED/REMOVED upstream")):
        chosen = [r for r in rows if r["status"] == status]
        if not chosen:
            continue
        print(f"## {title} ({len(chosen)})\n")
        for r in sorted(chosen, key=lambda r: -len(r["upstream_since"])):
            extra = f", Cameo diff {r['diff_lines']} lines" if r["diff_lines"] else ""
            print(f"- `{r['path']}`: base {r['base_date'] or '?'}, {len(r['upstream_since'])} upstream commits since{extra}")
            for s in r["upstream_since"][:args.limit]:
                print(f"    - {s}")
        print()

    print(f"## MISSING: upstream files never adopted ({len(missing)}), by area\n")
    areas: dict[str, list[str]] = defaultdict(list)
    for p in missing:
        parts = p[len(PREFIX):].split("/")
        areas["/".join(parts[:2]) if len(parts) > 2 else parts[0]].append(p)
    for area, files in sorted(areas.items(), key=lambda kv: -len(kv[1])):
        print(f"- `{area}`: **{len(files)}**")
    print("\n### Every missing file\n")
    for p in missing:
        print(f"- `{p}`")

    print("\n_Informational: this audit never fails. Act on it with `tools/audit/ca_vendor_sync.py`; "
          "bot modules are protected by `tools/audit/audit_ai_frankenstein.py`. See "
          "`docs/design/UPSTREAM_MODS.md`._")

    if args.json:
        args.json.write_text(json.dumps({"ca_head": head, "rows": rows, "missing": missing}, indent=1), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
