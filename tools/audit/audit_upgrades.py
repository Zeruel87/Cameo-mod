#!/usr/bin/env python3
"""audit_upgrades.py — B3 detector (inverted / dead upgrade effects).

For every buildable upgrade item (Queue contains Upgrades/Research/Promotions):
  1. collect the prerequisite tokens it grants (ProvidesPrerequisite / own name)
  2. find consumers: GrantConditionOnPrerequisite whose Prerequisites reference
     a token, plus Buildable.Prerequisites unlock usage
  3. for every stat trait gated on a granted condition, assert the direction is
     beneficial (per the field-direction table) unless the upgrade's entry in
     docs/design/upgrades_intent.yaml lists that field under `drawbacks`
  4. flag DEAD upgrades (granted tokens nobody consumes) and DEAD WIRING
     (GrantConditionOnPrerequisite tokens no upgrade/actor grants)
"""

from __future__ import annotations

import pathlib
import re
import sys

from cameo_model import Model
from miniyaml import load as load_yaml
from report import h1, h2, relpath, table

# trait base name -> (field, beneficial_predicate, meaning)
DIRECTION = {
    "FirepowerMultiplier":     ("Modifier", lambda v: v >= 100, ">=100 = not weaker"),
    "ReloadDelayMultiplier":   ("Modifier", lambda v: v <= 100, "<=100 = not slower"),
    "DamageMultiplier":        ("Modifier", lambda v: v <= 100, "<=100 = no more damage"),
    "SpeedMultiplier":         ("Modifier", lambda v: v >= 100, ">=100 = not slower"),
    "RangeMultiplier":         ("Modifier", lambda v: v >= 100, ">=100 = not shorter"),
    "RevealsShroudMultiplier": ("Modifier", lambda v: v >= 100, ">=100 = no less vision"),
    "DetectCloakedMultiplier": ("Modifier", lambda v: v >= 100, ">=100 = no worse detection"),
    "InaccuracyMultiplier":    ("Modifier", lambda v: v <= 100, "<=100 = no less accurate"),
    "PowerMultiplier":         ("Modifier", lambda v: v >= 100, ">=100 = no less power"),
    "ProductionCostMultiplier":("Multiplier", lambda v: v <= 100, "<=100 = no dearer"),
    "ProductionTimeMultiplier":("Multiplier", lambda v: v <= 100, "<=100 = no slower build"),
}

UPGRADE_QUEUES = ("upgrade", "research", "promotion")
_ident = re.compile(r"[A-Za-z0-9_.\-]+")

# Aedis deliberately changed this from 160 to 91 together with a production-cost
# rebalance.  Its intended formula cannot be resolved without reopening pricing,
# which is outside this pipeline.  Pin the exact unresolved fingerprint so any
# actor, trait, or value drift becomes a new blocking finding.
DEFERRED_INVERTED = {
    ("steelconsortium_upgrade_pulseweapons", "steelconsortium_clonetrooper",
     "FirepowerMultiplier@steelconsortium_upgrade_pulseweapons", "91"),
}


def is_deferred_inverted(upgrade: str, actor: str, trait: str, value: str) -> bool:
    return (upgrade, actor, trait, value) in DEFERRED_INVERTED


def load_intent(root: pathlib.Path) -> dict[str, dict]:
    path = root / "docs/design/upgrades_intent.yaml"
    if not path.exists():
        return {}
    out: dict[str, dict] = {}
    for top in load_yaml(path):
        entry = {c.key: c.value for c in top.children}
        out[top.key.lower()] = entry
    return out


def main() -> int:
    m = Model()
    rs = m.rs
    intent = load_intent(m.root)

    # ---- gather upgrade items -------------------------------------------- #
    upgrades: dict[str, set[str]] = {}      # upgrade actor -> granted tokens
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

    # ---- gather consumers -------------------------------------------------- #
    # token -> [(actor, granted condition)]
    grant_consumers: dict[str, list[tuple[str, str]]] = {}
    # token -> [actors unlocked via Buildable.Prerequisites]
    unlock_consumers: dict[str, list[str]] = {}
    # condition -> [(actor, trait_key, value_field, value)]
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
                prereqs = [t.strip().lstrip("~!").lower()
                           for t in (c.get("Prerequisites") or "").split(",") if t.strip()]
                for t in prereqs:
                    grant_consumers.setdefault(t, []).append((name.lower(), cond))
            rc = c.get("RequiresCondition") or ""
            if rc:
                base = c.key.split("@", 1)[0]
                spec = DIRECTION.get(base)
                for ident in _ident.findall(rc):
                    entry = (name.lower(), c.key,
                             spec[0] if spec else "", c.get(spec[0]) if spec else "")
                    cond_traits.setdefault(ident.lower(), []).append(entry)
            # any trait-level Prerequisites (support powers, ProducibleWithLevel,
            # ProvidesPrerequisite gates …) is unlock-style consumption too
            if not c.key.startswith("GrantConditionOnPrerequisite"):
                tp = c.get("Prerequisites") or ""
                for tok in tp.split(","):
                    tok = tok.strip().lstrip("~!").strip().lower()
                    if tok:
                        unlock_consumers.setdefault(tok, []).append(name.lower())
        for tok in m.positive_prereqs(res):
            unlock_consumers.setdefault(tok, []).append(name.lower())

    # ---- checks ------------------------------------------------------------ #
    inverted, deferred_inverted, dead_upgrades, no_intent = [], [], [], []
    for uname, toks in sorted(upgrades.items()):
        entry = intent.get(uname, None)
        drawbacks = set((entry or {}).get("drawbacks", "").replace(",", " ").split())
        conditions = set()
        consumed = False
        for t in toks:
            for actor, cond in grant_consumers.get(t, []):
                conditions.add(cond)
                consumed = True
            if unlock_consumers.get(t):
                consumed = True
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
                if not spec[1](v) and base.lower() not in drawbacks:
                    row = [uname, actor, trait_key, str(v), spec[2],
                           "declared drawback?" if entry else "no intent entry"]
                    if is_deferred_inverted(uname, actor, trait_key, str(v)):
                        deferred_inverted.append(row)
                    else:
                        inverted.append(row)
        if not consumed:
            node = rs.actor(uname)
            dead_upgrades.append([uname, ", ".join(sorted(toks - {uname})) or "(own name only)",
                                  relpath(node.file, m.root)])
        if entry is None:
            no_intent.append(uname)

    # dead wiring: GrantConditionOnPrerequisite tokens granted by nothing
    all_granted_tokens: set[str] = set()
    for name in rs.actors:
        if name.startswith("^"):
            continue
        res = rs.resolve(name)
        if res is None:
            continue
        all_granted_tokens.add(name.lower())
        for c in res.children_named("ProvidesPrerequisite"):
            all_granted_tokens.add((c.get("Prerequisite") or name).lower())
    dead_wiring = []
    for tok, consumers in sorted(grant_consumers.items()):
        if tok in all_granted_tokens:
            continue
        if tok.startswith(Model.OPTION_TOKEN_PREFIXES):
            continue
        sample = ", ".join(sorted({a for a, _ in consumers})[:4])
        dead_wiring.append([tok, str(len(consumers)), sample])

    print(h1("audit_upgrades — inverted / dead upgrade effects (B3)"))
    print(f"Upgrade items found: **{len(upgrades)}** — inverted-direction traits: "
          f"**{len(inverted)}**, exact deferred traits: **{len(deferred_inverted)}**, "
          f"dead upgrades: **{len(dead_upgrades)}**, "
          f"dead wiring tokens: **{len(dead_wiring)}**, "
          f"without intent entries: **{len(no_intent)}**\n")
    print(h2("Inverted-direction stat traits gated on upgrade conditions"))
    print(table(["upgrade", "affected actor", "trait", "value", "beneficial means", "note"],
                inverted))
    print(h2("Exact deferred inverted traits (pricing-linked review boundary)"))
    print(table(["upgrade", "affected actor", "trait", "value", "beneficial means", "note"],
                deferred_inverted))
    print(h2("Dead upgrades (granted tokens nobody consumes)"))
    print(table(["upgrade", "extra tokens", "file"], dead_upgrades))
    print(h2("Dead wiring (GrantConditionOnPrerequisite tokens granted by nothing)"))
    print(table(["token", "#consumer traits", "sample consumers"], dead_wiring))
    print(h2("Upgrades without an upgrades_intent.yaml entry"))
    print(", ".join(sorted(no_intent)) or "_none_")
    print()
    return 1 if inverted else 0


if __name__ == "__main__":
    sys.exit(main())
