#!/usr/bin/env python3
"""retire_flat_shims.py — delete the `^Warhead_*_Flat` shims (DESIGN.md §11b.0 R4).

MAINTAINER RULING R4, 2026-09-12: "Delete all 26, point users at the plain twin", and
"the 23 that genuinely resolve `PercentageScale: 0` declare it locally".

WHY THEY ARE WRONG TO KEEP. "Flat" in these names never meant a flat Versus profile —
R5 settled that no flat warhead exists in this mod (min spread 2.00x, median 4.62x over
190 templates). It meant `PercentageScale: 0`: no percentage-damage half. So the name
describes an implementation detail of ONE field, and it bought a full duplicate of an
entire 22-row armor profile to carry it.

⚠ THE DELETION IS NOT A RENAME. Measured, not assumed: ZERO of the 26 shims are copies of
their plain twin. They differ in four separate ways, and only one is `PercentageScale`:

  1. `Damage: 0` vs the twin's `2000`     -- moot, all 46 users declare their own Damage.
  2. WEAPON-LEVEL fields the twin has and the shim does not (`Range`, `ReloadDelay`,
     `TargetActorCenter`, `ValidTargets`). This is the trap that once stripped
     `TargetActorCenter` off 60+ weapons in the other direction: a `^Warhead_*` template
     is NOT only warheads. Only `TargetActorCenter` on 2 users actually lands.
  3. EXTRA warhead nodes only the twin ships (`*_ExtraDamage`, `*_Percentage`) -- 7 user
     instances. Suppressed per-user with `-Warhead@`, never at template level: doing it at
     template level killed a LIVE twin main on `25mm` and left a bare override with no
     type, which is the boot-NRE class.
  4. Versus rows differing by +/-1..4 (COMPOSITE 35 vs 36, Shield 224 vs 227).

(4) cannot be compensated, because `Versus` may live ONLY in a `^Warhead_*` template, and
it does not need to be: `gen_weapon_template.py` does not emit `_Flat` AT ALL -- grep it.
The shims are legacy orphans outside the generator's authority, which is precisely why
their profiles drifted from the regenerated plain twins. Adopting the twin profile is
convergence ONTO the generator, not a regression away from it. Every such delta is listed
under VERSUS CONVERGENCE so the size of the change is visible rather than implied.

Everything else must verify behaviour-identical through `resolved_gate.compare`, which
checks the field SET *and* the warhead firing ORDER.

⚠ WHERE COMPENSATIONS GO. Always AFTER the weapon last `Inherits` line, never at the top of
the block. Two separate reasons, both load-bearing:
  * a local `Warhead@X:` declared BEFORE the inherit is appended to the accumulator first,
    so the parent node merges into that early slot and the FIRING ORDER changes -- exactly
    the Wraith class this tool is gated against;
  * a `-Warhead@X:` removal only removes what is already present, so placed before the
    inherit that brings the node in it silently does nothing.

Usage:  python tools/balance/retire_flat_shims.py --base <pristine-worktree> [--apply]
        (dry run restores the tree; --apply leaves it dirty -- BOOT GATE before committing)
"""
from __future__ import annotations

import collections
import pathlib
import subprocess
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "audit"))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

import miniyaml  # noqa: E402
import resolved_gate  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parents[2]
SUFFIX = "_Flat"
# Fields that can never be written outside a ^Warhead_* template (rule 4 / DESIGN §11b).
TEMPLATE_ONLY = ("Versus", "PercentageVersus")


def shims(weapons) -> list[str]:
    return sorted(n for n in weapons if n.startswith("^Warhead_") and n.endswith(SUFFIX))


def twin_of(flat: str) -> str:
    return flat[:-len(SUFFIX)]


def kv(node) -> dict[str, str]:
    return {c.key: str(c.value).strip() for c in node.children}


def block_extent(path: pathlib.Path, start: int) -> int:
    """Last line (1-based, inclusive) of the top-level block beginning at `start`.

    A block runs to the line before the next column-0 non-blank line; trailing blank
    lines belong to the separator, not the block, so they are given back.
    """
    lines = path.read_bytes().decode("utf-8").splitlines()
    end = len(lines)
    for i in range(start, len(lines)):          # start is 1-based -> lines[start] is the next line
        ln = lines[i]
        if ln.strip() and not ln[0].isspace():
            end = i                              # 1-based inclusive == 0-based exclusive
            break
    while end > start and not lines[end - 1].strip():
        end -= 1
    return end


def build_plan(rs, pins=None):
    """(ops, meta). Ops are keyed file -> line -> [op], applied bottom-up.

    TWO PASSES, and the split is the point. Pass one (`pins=None`) makes only the STRUCTURAL
    edits: re-point the inherit, rename the local override, delete the dead declare-then-
    remove pair, suppress the warheads the twin adds. Pass two is handed `pins` — the field
    values measured as actually having MOVED — and writes only those.

    ⚠ Predicting the pins instead of measuring them over-compensates badly. The first version
    reasoned "the twin supplies `Range`, the user does not declare it, therefore pin it" and
    wrote **78** local field pins. Almost all were redundant: these weapons list a SECOND
    inherit after the twin, and a later inherit overrides an earlier one, so the value already
    resolved correctly. Worse, a pinned value stops tracking the parent it was copied from, so
    the redundant pins were a real maintenance hazard rather than harmless noise.
    """
    ops: dict[str, dict[int, list]] = collections.defaultdict(
        lambda: collections.defaultdict(list))
    flats = shims(rs.weapons)
    tmap, imap = {}, {}
    for f in flats:
        t = twin_of(f)
        if t in rs.weapons:
            tmap[f] = t
        for c in rs.weapons[f].children:
            if c.key.startswith("Warhead@"):
                inner = c.key[len("Warhead@"):]
                if inner.endswith(SUFFIX):
                    imap[inner] = inner[:-len(SUFFIX)]

    users: dict[str, list[str]] = collections.defaultdict(list)
    comp = collections.Counter()
    versus_drift: list[tuple[str, str, str, str]] = []
    orphans = [f for f in flats if f not in tmap]
    # Per-weapon allowances the gate may ignore. Kept per weapon and as EXACT
    # `path = value` strings, never prefixes, so one ruled-acceptable delta can never
    # wave through a second unrelated change to the same field.
    allow_lost: dict[str, set[str]] = collections.defaultdict(set)
    allow_gained: dict[str, set[str]] = collections.defaultdict(set)
    dead_pairs: list[tuple[str, str]] = []

    # ---- rename every LOCAL `Warhead@<inner>_Flat` key, corpus-wide ------- #
    # Forgetting this is not cosmetic and the gate proved it: a user override keyed
    # `Warhead@Cryo_Light_Flat` stops merging onto the twin's `Warhead@Cryo_Light`, so the
    # user's own Damage and its `-PhysicalStateName` removals silently stop applying AND
    # the stale key survives as a bare node with no warhead type -- the boot-NRE class.
    def walk(node, depth=0):
        for c in node.children:
            base = c.key.lstrip("-")
            if base.startswith("Warhead@"):
                nn = imap.get(base[len("Warhead@"):])
                if nn:
                    ops[c.file][c.line].append(("sub", base[len("Warhead@"):], nn))
            if depth < 1:
                walk(c, depth + 1)

    for _w, _node in rs.weapons.items():
        walk(_node)

    for w, node in rs.weapons.items():
        mine = [(c, c.value.strip()) for c in node.children
                if c.key.split("@")[0] == "Inherits" and c.value.strip() in tmap]
        if not mine:
            continue
        if w.startswith("^"):
            # A template inheriting a shim would need its own compensation strategy.
            # Measured today: zero exist. Refuse rather than guess if that ever changes.
            raise SystemExit(f"ABORT: template {w} inherits a shim - unhandled case")

        before = rs.resolve_weapon(w)
        local = kv(node)
        insert_at = max(c.line for c in node.children
                        if c.key.split("@")[0] == "Inherits")
        ins1: list[str] = []

        for c, flat in mine:
            twin = tmap[flat]
            users[flat].append(w)
            ops[c.file][c.line].append(("sub", flat, twin))

            # ---- THE RENAME CAN COLLIDE WITH A NAME THE WEAPON ALREADY USES ---- #
            # 11 weapons declare `Warhead@X` and then delete it again with `-Warhead@X`,
            # which is dead code while the live node is called `Warhead@X_Flat`. Rename the
            # override to `Warhead@X` and that dormant removal suddenly deletes the real
            # main, which is then re-added at the END of the list -- a firing-order change
            # of exactly the kind that broke the Wraith. So delete the dead pair. If the
            # removal was in fact live (killing a node from some OTHER parent), the gate
            # reports the resurrected node as `gained` and this run fails. Proven, not
            # assumed.
            tgt = "Warhead@" + twin[len("^Warhead_"):]
            seq = [g for g in node.children if g.key.lstrip("-") == tgt]
            if seq:
                keys = [g.key for g in seq]
                if keys == [tgt, "-" + tgt]:
                    for g in seq:
                        ops[g.file][g.line].append(("delsub",))
                    dead_pairs.append((w, tgt))
                    comp["dead declare-then-remove pair deleted"] += 1
                else:
                    raise SystemExit(
                        f"ABORT: {w} mentions {tgt} as {keys} - the rename would collide "
                        f"in a shape this tool has not been taught. Handle it by hand.")

            tr, fr = rs.resolve_weapon(twin), rs.resolve_weapon(flat)
            tf, ff = kv(tr), kv(fr)
            inner = twin[len("^Warhead_"):]

            # (2) extra warhead nodes only the twin ships
            fwh = {k[len("Warhead@"):] for k in ff if k.startswith("Warhead@")}
            fwh = {imap.get(x, x) for x in fwh}
            for k in tf:
                if not k.startswith("Warhead@"):
                    continue
                if k[len("Warhead@"):] in fwh:
                    continue
                ins1.append(f"\t-{k}:")
                comp["suppressed extra warhead"] += 1

            # (3) the Versus rows that converge onto the generator's profile
            fmain = fr.child("Warhead@" + inner + SUFFIX)
            tmain = tr.child("Warhead@" + inner)
            if fmain is None or tmain is None:
                continue
            for f in TEMPLATE_ONLY:
                # ⚠ NEVER compare these by node VALUE. `Versus:` is a block node whose own
                # value is the empty string, so a `kv()`-level test finds every armor row
                # equal -- the first version of this tool printed "VERSUS CONVERGENCE:
                # 0 rows" while 64 weapons were genuinely drifting. Walk the CHILDREN.
                t_block, f_block = tmain.child(f), fmain.child(f)
                if f_block is None:
                    continue
                for row in f_block.children:
                    t_row = t_block.child(row.key) if t_block is not None else None
                    was = str(row.value).strip()
                    tv = str(t_row.value).strip() if t_row is not None else "-"
                    if tv == was:
                        continue
                    versus_drift.append((twin, f + "/" + row.key, was, tv))
                    # Registered GLOBALLY, not against `w`: a shim user can itself be
                    # inherited by further CONCRETE weapons (W7's 957 weapon-parent
                    # inherits), and those carry the profile without ever naming the shim.
                    # Keying the allowance to the direct user left 24 such descendants
                    # failing the gate. Safe because every key is an exact `path = value`
                    # whose path is asserted to sit inside TEMPLATE_ONLY in verify().
                    path = f"/Warhead@{inner}/{f}/{row.key}"
                    allow_lost["*"].add(f"{path} = {was}")
                    allow_gained["*"].add(f"{path} = {tv}")

        # ---- pass two: only the values MEASURED as having moved ------------- #
        for line in (pins or {}).get(w, ()):
            ins1.append(line)
            comp["measured field pin"] += 1
        for pair in (pins or {}).get("allow:" + w, ()):
            allow_gained[w].add(pair)

        if ins1:
            ops[node.file][insert_at].append(("ins", ins1))

    # the shim blocks themselves, deleted whole
    for f in flats:
        n = rs.weapons[f]
        ops[n.file][n.line].append(("delblock", block_extent(ROOT / n.file, n.line)))

    return ops, {"tmap": tmap, "imap": imap, "users": users, "comp": comp,
                 "orphans": orphans, "versus_drift": versus_drift, "flats": flats,
                 "allow_lost": allow_lost, "allow_gained": allow_gained,
                 "dead_pairs": dead_pairs}


def _sub_extent(lines: list[str], idx: int) -> int:
    """0-based exclusive end of the child block starting at `lines[idx]`.

    The block is the node line plus every following line indented DEEPER than it. A blank
    line inside is only swallowed when a deeper-indented line follows, so a block never
    eats the separator that ends it.
    """
    depth = len(lines[idx]) - len(lines[idx].lstrip("\t"))
    end = idx + 1
    i = idx + 1
    while i < len(lines):
        ln = lines[i]
        if not ln.strip():
            i += 1
            continue
        if len(ln) - len(ln.lstrip("\t")) <= depth:
            break
        end = i + 1
        i += 1
    return end


def apply_ops(ops) -> int:
    n = 0
    for f, per_line in ops.items():
        p = ROOT / f
        raw = p.read_bytes().decode("utf-8")
        nl = "\r\n" if "\r\n" in raw else "\n"
        lines = raw.split(nl)
        # bottom-up, so every line number above the edit stays valid
        for line in sorted(per_line, reverse=True):
            idx = line - 1
            ins, cut = [], None
            for op in per_line[line]:
                if op[0] == "sub":
                    if op[1] in lines[idx]:
                        lines[idx] = lines[idx].replace(op[1], op[2])
                        n += 1
                elif op[0] == "ins":
                    ins.extend(op[1])
                elif op[0] == "delblock":
                    cut = op[1]
                elif op[0] == "delsub":
                    cut = _sub_extent(lines, idx)
            if ins:
                lines[idx:idx + 1] = [lines[idx]] + ins
                n += len(ins)
            if cut is not None:
                del lines[idx:cut]
                n += cut - idx
        p.write_bytes(nl.join(lines).encode("utf-8"))
    return n


def restore(paths: list[str]) -> None:
    subprocess.run(["git", "checkout", "--"] + paths, cwd=ROOT, check=True,
                   capture_output=True)


def verify(base_root: str, meta):
    """Behaviour comparison against a pristine worktree: field SET plus warhead ORDER."""
    base = miniyaml.Ruleset(base_root)
    cur = miniyaml.Ruleset(str(ROOT))
    ren = dict(meta["tmap"])
    for a, b in meta["imap"].items():
        ren["Warhead@" + a] = "Warhead@" + b
        ren["-Warhead@" + a] = "-Warhead@" + b
    # Two classes of delta are ruled acceptable and are allowed PER WEAPON, as exact
    # `path = value` strings -- never a prefix, so one ruled delta cannot wave through an
    # unrelated second change to the same field:
    #   * Versus convergence  -- the generator owns the twin, and never emitted the shim.
    #   * a stated engine default where the field was previously absent.
    # The firing ORDER is never allowed to move, for any reason.
    #
    # The global allowance is the one with real blast radius, so prove its scope rather than
    # trusting where it was built: every globally-allowed pair MUST address a row inside a
    # TEMPLATE_ONLY block. Without this, a bug in the plan could quietly widen the waiver to
    # `Damage`, and the run would still report VERIFIED.
    for pair in set(meta["allow_lost"].get("*", ())) | set(meta["allow_gained"].get("*", ())):
        if not any(f"/{t}/" in pair for t in TEMPLATE_ONLY):
            raise SystemExit(f"ABORT: global allowance outside {TEMPLATE_ONLY}: {pair}")

    out = []
    for w in sorted(base.weapons):
        if w.startswith("^"):
            continue
        if w not in cur.weapons:
            out.append((w, {"lost": ["THE WHOLE WEAPON"], "gained": []}))
            continue
        d = resolved_gate.compare(base.resolve_weapon(w), cur.resolve_weapon(w), ren)
        if not d:
            continue
        al = set(meta["allow_lost"].get(w, ())) | set(meta["allow_lost"].get("*", ()))
        ag = set(meta["allow_gained"].get(w, ())) | set(meta["allow_gained"].get("*", ()))
        d["lost"] = [x for x in d.get("lost", []) if x not in al]
        d["gained"] = [x for x in d.get("gained", []) if x not in ag]
        if d.get("lost") or d.get("gained") or "order_before" in d:
            out.append((w, d))
    return out


# Engine defaults for fields a weapon may gain from the twin while the baseline had none.
# Stating the default explicitly is the only way to neutralise an inherited scalar -- MiniYaml
# has no "unset a field" form. Anything not listed here aborts rather than being guessed.
ENGINE_DEFAULTS = {"TargetActorCenter": "false"}


def derive_pins(bad) -> dict[str, list[str]]:
    """Turn measured diffs into the minimal set of local declarations that restores them.

    Measuring beats predicting here: a pin is written only where the resolved value really
    moved, so a field another inherit already supplies correctly is left alone.
    """
    pins: dict[str, list[str]] = collections.defaultdict(list)
    for w, d in bad:
        if "order_before" in d:
            raise SystemExit(f"ABORT: {w} changed warhead ORDER - a pin cannot fix that.")
        lost = dict(x.rsplit(" = ", 1) for x in d.get("lost", []))
        gained = dict(x.rsplit(" = ", 1) for x in d.get("gained", []))
        for path, was in lost.items():
            parts = path.lstrip("/").split("/")
            if len(parts) == 1:                       # weapon-level scalar
                pins[w].append(f"\t{parts[0]}: {was}")
            elif len(parts) == 2 and parts[0].startswith("Warhead@"):
                pins[w].append(f"\t{parts[0]}:")
                pins[w].append(f"\t\t{parts[1]}: {was}")
            else:
                raise SystemExit(f"ABORT: {w} lost {path} = {was} - no pin shape for it.")
        for path, now in gained.items():
            if path in lost:                          # already handled by the pin above
                continue
            parts = path.lstrip("/").split("/")
            if len(parts) != 1 or parts[0] not in ENGINE_DEFAULTS:
                raise SystemExit(
                    f"ABORT: {w} gained {path} = {now} with nothing lost, and no engine "
                    f"default is recorded for it. Add one to ENGINE_DEFAULTS or handle by hand.")
            dflt = ENGINE_DEFAULTS[parts[0]]
            pins[w].append(f"\t{parts[0]}: {dflt}")
            pins["allow:" + w].append(f"{path} = {dflt}")
    return pins


def main() -> int:
    if "--base" not in sys.argv:
        print(__doc__.strip())
        return 2
    base_root = sys.argv[sys.argv.index("--base") + 1]
    apply_it = "--apply" in sys.argv

    rs0 = miniyaml.Ruleset(str(ROOT))
    paths = sorted({str(p.relative_to(ROOT)).replace("\\", "/") for p in rs0.manifest.weapons})

    # pass one: structure only, then MEASURE what moved
    ops, meta = build_plan(rs0)
    apply_ops(ops)
    moved = verify(base_root, meta)
    pins = derive_pins(moved)
    restore(paths)
    print(f"pass 1 (structure only): {len(moved)} weapons moved -> "
          f"{sum(len(v) for k, v in pins.items() if not k.startswith('allow:'))} pins needed")

    # pass two: structure plus exactly those pins
    ops, meta = build_plan(miniyaml.Ruleset(str(ROOT)), pins)
    n = apply_ops(ops)
    bad = verify(base_root, meta)

    nusers = sum(len(v) for v in meta["users"].values())
    print(f"shims: {len(meta['flats'])}   with a plain twin: {len(meta['tmap'])}   "
          f"users re-pointed: {nusers}   edits: {n}")
    print(f"dead shims with NO user at all: {len(meta['flats']) - len(meta['users'])}")
    if meta["orphans"]:
        print(f"no plain twin (deleted outright): {', '.join(meta['orphans'])}")
    print("\ncompensations written to preserve behaviour:")
    for k, v in sorted(meta["comp"].items()):
        print(f"   {k:34s} {v}")

    # Deduped: the plan visits a template once per USER, so the raw list counts a
    # 4-user template's row four times. Report the distinct armor rows that move.
    rows = sorted(set(meta["versus_drift"]))
    drift = collections.Counter(t for t, _p, _a, _b in rows)

    def delta(r):
        return abs(int(r[2]) - int(r[3])) if r[3].lstrip("-").isdigit() else 0

    print(f"\nVERSUS CONVERGENCE onto the generator: {len(rows)} distinct armor rows "
          f"across {len(drift)} templates (worst row moves "
          f"{max((delta(r) for r in rows), default=0)} points)")
    for t, path, was, now in sorted(rows, key=lambda r: -delta(r))[:6]:
        print(f"   {t:38s} {path:26s} {was} -> {now}")

    print(f"\nweapons whose behaviour moved: {len(bad)}")
    for w, d in bad[:12]:
        for line in resolved_gate.describe(w, d):
            print(line)

    ok = not bad
    print("\nVERIFIED behaviour-identical." if ok else "\nFAILED - not written.")
    if not apply_it or not ok:
        restore(paths)
        print("tree restored." + ("" if ok else " Fix the plan, not the gate."))
        if ok:
            print("dry run only - re-run with --apply, then BOOT GATE.")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
