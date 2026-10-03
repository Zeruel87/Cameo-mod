#!/usr/bin/env python3
"""B3 transcription drafter — emit intent entries for upgrades missing one.

`audit_upgrades.py` reports 587 upgrade actors without a
`docs/design/upgrades_intent.yaml` entry (the file's own header calls that
list "the transcription TODO"). This tool drafts each missing entry from the
resolved tree so a human (or lane owner) only has to review, not re-derive:

  faction:   longest real-faction-name prefix in the id (`ra1_allies_*` →
             ra1_allies); `unknown` when no prefix matches — flagged for review.
  effect:    the actor's Tooltip.Description (falling back to Name); verbatim,
             so the entry literally transcribes the tooltip promise.
  coverage:  consumer-macro split — `infantry`/`vehicles`/`aircraft` when every
             consuming actor is one macro class, `listed` when <=4 consumers,
             `roster_wide` for broad mixes, `narrow` when nothing consumes the
             token yet (dead-upgrade overlap; still drafted so the row exists).
  phase:     Valued.Cost bands — <1500 early, <4000 mid, else late; missing
             cost falls back to prereq depth (>=2 gates → mid).
  drawbacks: trait bases gated on the upgrade's conditions whose value runs
             AGAINST the owner (audit_upgrades.DIRECTION inverted) — exactly
             the set the audit would otherwise call "inverted".

Read-only for game data; writes a yaml block to stdout (or --out).
The appended block is marked machine-drafted so reviewers know provenance.

Usage:
    python tools/balance/b3_intent_draft.py [--out docs/design/_b3_draft.yaml]
"""
from __future__ import annotations

import argparse
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "audit"))

import miniyaml  # noqa: E402
from cameo_model import Model  # noqa: E402
from audit_upgrades import (  # noqa: E402
    DEFERRED_INVERTED, DIRECTION, UPGRADE_QUEUES, load_intent,
)

ROOT = pathlib.Path(__file__).resolve().parents[2]
_ident = re.compile(r"[A-Za-z0-9_.\-]+")

# armor class -> macro bucket (mirrors target_model macros, minimal set)
INF_ARMORS = {"none", "flak", "plate", "scout", "heroic"}
VEH_ARMORS = {"light", "medium", "heavy", "superheavy", "steel", "concrete",
              "composite", "reflector", "hazmat", "armor"}
AIR_ARMORS = {"fighter", "bomber", "helicopter", "spaceship", "flak_air",
              "vtol"}


def _macro(node) -> str:
    for c in node.children:
        if c.key == "Armor" or c.key.startswith("Armor@"):
            t = (c.get("Type") or "").strip().lower()
            if t in INF_ARMORS:
                return "infantry"
            if t in AIR_ARMORS:
                return "aircraft"
            if t in VEH_ARMORS:
                return "vehicles"
            return "other"
    # unarmored defs (buildings etc.) still count as their own thing
    for c in node.children:
        if c.key.startswith("Building") or c.key == "Building":
            return "buildings"
    return "other"


def _cost(node) -> int | None:
    v = node.child("Valued")
    if v is None:
        return None
    raw = v.get("Cost")
    try:
        return int(float(str(raw))) if raw is not None else None
    except (TypeError, ValueError):
        return None


_FTL_KEY = re.compile(r"^[a-z0-9_.]+$")
_FTL: dict[str, str] | None = None


def _ftl_lookup(root: pathlib.Path, key: str) -> str:
    """key like `upgrade_x.description` -> resolved English from mods/**/ *.ftl."""
    global _FTL
    if _FTL is None:
        # key.attr -> text; `.attr =` lines inside a `key =` block, indented
        # continuation lines append to the current attribute (fluent syntax).
        _FTL = {}
        for ftl in root.rglob("*.ftl"):
            cur_key, cur_attr = None, None
            for raw in ftl.read_text(encoding="utf-8", errors="replace").splitlines():
                if raw and not raw.startswith((" ", "\t")) and "=" in raw:
                    cur_key, cur_attr = raw.split("=", 1)[0].strip(), None
                elif cur_key and raw.startswith((" ", "\t")):
                    s = raw.strip()
                    if s.startswith(".") and "=" in s:
                        attr, _, txt = s.partition("=")
                        cur_attr = f"{cur_key}.{attr.lstrip('.').strip()}"
                        _FTL[cur_attr] = txt.strip()
                    elif cur_attr and s:
                        _FTL[cur_attr] += " " + s
    return _FTL.get(key, "")


def _tooltip(node, root: pathlib.Path) -> str:
    b = node.child("Buildable")
    if b is not None:
        v = b.get("Description")
        if v and str(v).strip():
            txt = str(v).strip()
            if _FTL_KEY.match(txt):
                resolved = _ftl_lookup(root, txt)
                if resolved:
                    return " ".join(resolved.split())[:220]
            else:
                return " ".join(txt.split())[:220]
    for key in ("Tooltip", "TooltipDescription", "Description"):
        t = node.child(key)
        if t is None:
            continue
        for f in ("Description", "Name"):
            v = t.get(f)
            if v and str(v).strip():
                return " ".join(str(v).split())[:220]
    for f in ("Description", "Name"):
        v = node.get(f)
        if v and str(v).strip():
            return " ".join(str(v).split())[:220]
    return ""


def _phase(node, m: Model) -> str:
    c = _cost(node) or 0
    if c >= 4000:
        return "late"
    if c >= 1500:
        return "mid"
    if c > 0:
        return "early"
    # unpriced (promotions etc.) — prereq-depth proxy
    return "mid" if len(m.positive_prereqs(node)) >= 2 else "early"


def collect(m: Model):
    rs = m.rs
    intent = load_intent(m.root)

    upgrades: dict[str, set[str]] = {}
    for name in rs.actors:
        if name.startswith("^"):
            continue
        res = rs.resolve(name)
        if res is None:
            continue
        b = res.child("Buildable")
        queue = (b.get("Queue") or "").lower() if b else ""
        if not any(q in queue for q in UPGRADE_QUEUES):
            continue
        toks = {name.lower()}
        for c in res.children_named("ProvidesPrerequisite"):
            toks.add((c.get("Prerequisite") or name).lower())
        for c in res.children_named("ProvidesTeamProxyActor"):
            proxy = c.get("Actor")
            if proxy:
                pres = rs.resolve(proxy)
                if pres is not None:
                    for pc in pres.children_named("ProvidesPrerequisite"):
                        toks.add((pc.get("Prerequisite") or proxy).lower())
        upgrades[name.lower()] = toks

    grant_consumers: dict[str, list[tuple[str, str]]] = {}
    unlock_consumers: dict[str, list[str]] = {}
    cond_traits: dict[str, list[tuple[str, str, str, str]]] = {}
    for name in rs.actors:
        if name.startswith("^"):
            continue
        res = rs.resolve(name)
        if res is None:
            continue
        for c in res.children:
            if c.key.startswith("GrantConditionOnPrerequisite"):
                cond = (c.get("Condition") or "").lower()
                for t in (c.get("Prerequisites") or "").split(","):
                    t = t.strip().lstrip("~!").lower()
                    if t:
                        grant_consumers.setdefault(t, []).append((name.lower(), cond))
            rc = c.get("RequiresCondition") or ""
            if rc:
                base = c.key.split("@", 1)[0]
                spec = DIRECTION.get(base)
                for ident in _ident.findall(rc):
                    cond_traits.setdefault(ident.lower(), []).append(
                        (name.lower(), c.key,
                         spec[0] if spec else "", c.get(spec[0]) if spec else ""))
            if not c.key.startswith("GrantConditionOnPrerequisite"):
                for tok in (c.get("Prerequisites") or "").split(","):
                    tok = tok.strip().lstrip("~!").strip().lower()
                    if tok:
                        unlock_consumers.setdefault(tok, []).append(name.lower())
        for tok in m.positive_prereqs(res):
            unlock_consumers.setdefault(tok, []).append(name.lower())

    real_factions = sorted((f.internal for f in m.real_factions()),
                           key=len, reverse=True)
    drafts = []
    for uname, toks in sorted(upgrades.items()):
        if uname in intent:
            continue
        node = rs.actor(uname)
        res = rs.resolve(uname)
        if res is None:
            continue

        conditions = set()
        consumers: set[str] = set()
        for t in toks:
            for actor, cond in grant_consumers.get(t, []):
                conditions.add(cond)
                consumers.add(actor)
            for actor in unlock_consumers.get(t, []):
                if actor != uname:
                    consumers.add(actor)

        drawbacks: set[str] = set()
        for cond in conditions:
            for actor, trait_key, fieldname, value in cond_traits.get(cond, []):
                base = trait_key.split("@", 1)[0]
                spec = DIRECTION.get(base)
                if spec is None or not value:
                    continue
                try:
                    v = int(str(value).split(",")[0])
                except ValueError:
                    continue
                if not spec[1](v) and (uname, actor, trait_key, str(v)) in DEFERRED_INVERTED:
                    # Drafting this drawback would re-mask a deferred pin the
                    # audit deliberately keeps visible — never emit it.
                    continue
                if not spec[1](v):
                    drawbacks.add(base.lower())

        # faction = longest matching real-faction prefix in the id
        faction = next((f for f in real_factions
                        if uname == f or uname.startswith(f + "_")), "unknown")

        # Drafted entries never assert enforced coverage — consumer inference
        # cannot prove roster intent, and audit_upgrade_coverage.py treats
        # roster_wide|infantry|vehicles|aircraft as an enforcement contract.
        # `listed` = consumer-driven subset; `narrow` = no detected consumers.
        # Hand-review promotes a drafted row to an enforced value.
        cov = "listed" if consumers else "narrow"

        drafts.append({
            "id": uname,
            "faction": faction,
            "effect": _tooltip(res, m.root) or "(no tooltip text — review)",
            "coverage": cov,
            "phase": _phase(res, m),
            "drawbacks": " ".join(sorted(drawbacks)),
            "consumers": len(consumers),
            "file": str(getattr(node, "file", "?")),
        })
    return drafts


def emit_yaml(drafts) -> str:
    out = []
    by_faction: dict[str, list[dict]] = {}
    for d in drafts:
        by_faction.setdefault(d["faction"], []).append(d)
    for faction in sorted(by_faction):
        out.append(f"######################## {faction} #######################")
        for d in by_faction[faction]:
            out.append(f"{d['id']}:")
            out.append(f"\tfaction: {d['faction']}")
            out.append(f"\teffect: {d['effect']}")
            out.append(f"\tcoverage: {d['coverage']}")
            out.append(f"\tphase: {d['phase']}")
            if d["drawbacks"]:
                out.append(f"\tdrawbacks: {d['drawbacks']}")
            else:
                out.append("\tdrawbacks: ")
            out.append("")
    return "\n".join(out)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", help="write draft yaml here instead of stdout")
    args = ap.parse_args()
    m = Model()
    drafts = collect(m)
    text = emit_yaml(drafts)
    if args.out:
        pathlib.Path(args.out).write_text(text + "\n", encoding="utf-8")
        print(f"wrote {args.out} ({len(drafts)} draft entries)")
    else:
        print(text)
    unknown = sum(1 for d in drafts if d["faction"] == "unknown")
    narrow = sum(1 for d in drafts if d["coverage"] == "narrow")
    print(f"drafted={len(drafts)} unknown_faction={unknown} "
          f"narrow(dead)={narrow}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
