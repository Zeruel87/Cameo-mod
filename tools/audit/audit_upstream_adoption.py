#!/usr/bin/env python3
"""audit_upstream_adoption — which upstream-mod C# types Cameo already has, and which are new.

Cameo's stated goal is to absorb the other OpenRA mods (docs/design/UPSTREAM_MODS.md). The
question that decides every port is not "how many files does that mod have" but "how many of
its yaml-visible TYPES does Cameo already provide" — because Cameo loads six assemblies
(AS, CA, Cameo, Cnc, D2k, Common) and a large share of any mod assembly is a type one of those
already implements under the same name.

⚠ `ObjectCreator.FindType` takes the FIRST assembly in mod.yaml's `Assemblies:` order. A name
that already exists in AS or CA therefore CANNOT be shadowed by a copy placed in
OpenRA.Mods.Cameo — porting it is not merely redundant, it would not even be reachable.

⛔ A NEW NAME IS NOT A NEW MECHANIC. This audit matches by NAME, and the same mechanic
routinely arrives under two names: RV's `Temporal` warhead + `AffectedByTemporal` trait ARE CA's
`WarpDamage` + `Warpable`, which are already vendored here and already wired to the Chrono
Legionnaire's `ChronoBeam`. A port decided on the NEW column alone duplicates live code. So this
audit also compares the `[Desc(...)]` text of every new type against ours and reports the matches
separately — that pair's trait descriptions are word for word identical, so the check catches it.
Read the DUPLICATE section as a stop sign, and the rest as "not obviously duplicated" rather
than as "new".

Yaml-visible names, not file names:
    class FooInfo     -> trait/projectile `Foo`
    class FooWarhead  -> warhead `Foo`

INFORMATIONAL — it never fails a build. What to adopt is a maintainer decision.

Clones are expected beside this repo under the parent directory; override with
RV_ROOT / SP_ROOT / CN_ROOT / CA_ROOT / GEN_ROOT.
"""
from __future__ import annotations

import os
import pathlib
import re
import sys

if hasattr(sys.stdout, "reconfigure"):          # Windows consoles default to cp1252
    sys.stdout.reconfigure(encoding="utf-8")

ROOT = pathlib.Path(__file__).resolve().parents[2]

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from environment import ENGINE_ASSEMBLIES  # noqa: E402

# The assemblies the running game resolves names through, in mod.yaml order.
OURS = [ROOT / a for a in ENGINE_ASSEMBLIES] + [ROOT / "OpenRA.Mods.Cameo"]

# (label, env var, clone dir, assembly subdir, yaml roots to measure usage in)
UPSTREAMS = [
    ("Romanov's Vengeance", "RV_ROOT", "Romanovs-Vengeance", "OpenRA.Mods.RA2", ["mods"]),
    ("Shattered Paradise", "SP_ROOT", "Shattered-Paradise-SDK", "OpenRA.Mods.Sp", ["mods"]),
    ("Crystallized Nexus", "CN_ROOT", "crystallized-nexus", ".modsdk/OpenRA.Mods.CN",
     [".modsdk/mods"]),
    ("Combined Arms", "CA_ROOT", "CAmod", "OpenRA.Mods.CA", ["mods"]),
    ("Generals Alpha", "GEN_ROOT", "Generals-Alpha", "OpenRA.Mods.GenSDK", ["mods"]),
]

INFO_RE = re.compile(r"\bclass\s+([A-Za-z0-9_]+)Info\b")
WARHEAD_RE = re.compile(r"\bclass\s+([A-Za-z0-9_]+)Warhead\b")
# The first string literal of a [Desc(...)] — the mechanic stated in prose.
DESC_RE = re.compile(r'\[Desc\(\s*"((?:[^"\\]|\\.)*)"')

# Same mechanic, different name, where the prose does NOT pair them up. Each entry is a
# conclusion from reading both implementations, never a guess from the names.
KNOWN_EQUIVALENTS = {
    # RV's temporal erasure IS CA's warp erasure: both are TargetDamageWarhead subclasses
    # routing damage into a separate meter on a companion trait. CA's is the richer of the
    # two (it adds RevokeRate and ScaleWithCurrentHealthPercentage) and is already live on
    # ChronoBeam / IFVChronoBeam — exactly the weapons RV points Temporal at.
    "Temporal": "WarpDamage (OpenRA.Mods.CA)",
    "AffectedByTemporal": "Warpable (OpenRA.Mods.CA)",
    # The slave half of the pair whose MASTER the [Desc] match already flags: both derive
    # BaseSpawnerSlaveInfo, and we carry MissileSpawnerSlave. Only the wording differs
    # ("...to a missile spawner OLD master"), which is why the text match misses it.
    "MissileSpawnerOldSlave": "MissileSpawnerSlave",
}


def norm(desc: str) -> str:
    return " ".join(desc.lower().replace(".", " ").split())


def scan(root: pathlib.Path) -> tuple[dict[str, str], dict[str, str]]:
    """(yaml-visible type name -> declaring file, type name -> its [Desc] first line)."""
    found: dict[str, str] = {}
    descs: dict[str, str] = {}
    if not root.is_dir():
        return found, descs
    for path in root.rglob("*.cs"):
        p = path.as_posix()
        if "/obj/" in p or "/bin/" in p:
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        rel = path.relative_to(root).as_posix()
        # Walk the file in order so each class takes the [Desc] most recently seen above it.
        last_desc = ""
        for line in text.splitlines():
            m = DESC_RE.search(line)
            if m:
                last_desc = m.group(1)
                continue
            for regex in (INFO_RE, WARHEAD_RE):
                cm = regex.search(line)
                if cm:
                    name = cm.group(1)
                    found.setdefault(name, rel)
                    if last_desc:
                        descs.setdefault(name, last_desc)
                    last_desc = ""
    return found, descs


def find_clone(env: str, default_dir: str) -> pathlib.Path | None:
    for c in (os.environ.get(env), ROOT.parent / default_dir,
              pathlib.Path.home() / "Documents" / "GitHub" / default_dir):
        if c and pathlib.Path(c).expanduser().is_dir():
            return pathlib.Path(c).expanduser()
    return None


def usage_count(clone: pathlib.Path, yaml_dirs: list[str], names: set[str]) -> dict[str, int]:
    """How often each name appears in the upstream mod's own rules."""
    counts = dict.fromkeys(names, 0)
    alternation = "|".join(re.escape(n) for n in sorted(names, key=len, reverse=True))
    value_re = re.compile(r":\s*(" + alternation + r")\s*$")
    for d in yaml_dirs:
        base = clone / d
        if not base.is_dir():
            continue
        for path in base.rglob("*.yaml"):
            try:
                text = path.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            for line in text.splitlines():
                stripped = line.rstrip()
                m = value_re.search(stripped)
                if m:
                    counts[m.group(1)] += 1
                elif stripped.endswith(":"):
                    # a bare trait declaration: TraitName: or TraitName@suffix:
                    key = stripped.strip().rstrip(":").split("@", 1)[0]
                    if key in counts:
                        counts[key] += 1
    return counts


def main() -> int:
    print("# audit_upstream_adoption — upstream mod types Cameo already has, and what is new\n")
    ours: dict[str, str] = {}
    our_descs: dict[str, str] = {}
    for root in OURS:
        names, descs = scan(root)
        for name, rel in names.items():
            ours.setdefault(name, f"{root.name}/{rel}")
        for name, d in descs.items():
            our_descs.setdefault(name, d)
    if not ours:
        print("_no Cameo/engine sources found_ — `make.cmd all` populates engine/.")
        print("\nNOT a clean result: this audit could not run.")
        return 0

    by_desc: dict[str, list[str]] = {}
    for name, d in our_descs.items():
        by_desc.setdefault(norm(d), []).append(name)

    print(f"Cameo resolves **{len(ours)}** yaml-visible type names across "
          f"{len([r for r in OURS if r.is_dir()])} assemblies.\n")

    rows, details = [], []
    for label, env, clone_dir, sub, yaml_dirs in UPSTREAMS:
        clone = find_clone(env, clone_dir)
        if clone is None:
            rows.append((label, "—", "—", "—", "—", f"no clone (set `{env}`)"))
            continue
        theirs, their_descs = scan(clone / sub)
        if not theirs:
            rows.append((label, "—", "—", "—", "—", f"no sources at `{sub}`"))
            continue
        shared = sorted(set(theirs) & set(ours))
        new = sorted(set(theirs) - set(ours))

        dupes: dict[str, str] = {}
        for n in new:
            if n in KNOWN_EQUIVALENTS:
                dupes[n] = KNOWN_EQUIVALENTS[n] + " — read both, same mechanic"
                continue
            match = by_desc.get(norm(their_descs.get(n, "")), [])
            if their_descs.get(n) and match:
                dupes[n] = ", ".join(match) + " — identical `[Desc]` text"
        candidates = [n for n in new if n not in dupes]

        used = usage_count(clone, yaml_dirs, set(candidates)) if candidates else {}
        live = [n for n in candidates if used.get(n, 0) > 0]
        rows.append((label, len(theirs), len(shared), len(dupes), len(candidates),
                     f"{len(live)} used in its own yaml"))
        details.append((label, sub, theirs, dupes, candidates, used, live))

    print("| mod | types | already in Cameo | same mechanic, other name | candidates "
          "| of the candidates |")
    print("|---|--:|--:|--:|--:|---|")
    for label, t, s, d, c, note in rows:
        print(f"| {label} | {t} | {s} | {d} | {c} | {note} |")

    for label, sub, theirs, dupes, candidates, used, live in details:
        print(f"\n## {label} — `{sub}`\n")
        if dupes:
            print("⛔ **Already implemented here under another name — read before porting:**\n")
            print("A `[Desc]` match is EVIDENCE, not proof, and it misleads in both directions. "
                  "`LeaveSmudgeSP` repeats Common `LeaveSmudge`'s description word for word and is "
                  "a genuine SUPERSET of it — smudge levels, ring size, a max level, and its own "
                  "`SmudgeLayerSP`. Read both implementations before concluding either way.\n")
            print("| upstream type | Cameo already has | evidence |")
            print("|---|---|---|")
            for n in sorted(dupes):
                already, _, why = dupes[n].partition(" — ")
                print(f"| `{n}` | `{already}` | {why} |")
            print()
        if not candidates:
            print("Nothing left: every type it declares either exists here or duplicates one.")
            continue
        print(f"**{len(live)} of {len(candidates)}** candidates are used by the mod's own rules "
              "(the rest are dead code there too, and are not worth porting first).\n")
        print("| type | file | uses in its yaml |")
        print("|---|---|--:|")
        for n in sorted(candidates, key=lambda x: (-used.get(x, 0), x)):
            print(f"| `{n}` | `{theirs[n]}` | {used.get(n, 0)} |")

    print("\n_Informational: adopting upstream code is a maintainer decision, never a gate._")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
