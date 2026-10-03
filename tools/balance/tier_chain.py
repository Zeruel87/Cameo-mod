#!/usr/bin/env python3
"""Resolve Buildable prerequisite chains to a building-cost C and a tier multiplier.

The rational tier curve is

    f(C) = 1 / (1 + (C - B) / S)

with B = 9500 (T1/T2 median boundary) and S = 8250 (T4 median - B).  f(C) is
clamped to [0, 1] and returns 1.0 for chains at or below B.

The chain resolver restricts prerequisite *provider* buildings to the actor's
own ContentPack leaf plus the same game's Shared pack.  This prevents the
cross-faction bug where a Nod unit could be priced using a GDI Construction
Yard.  Shared-pack units use only their own Shared pack, matching the existing
``tier_chain_validation.md`` report.

Exported helpers:

* ``tier_multiplier(C, B=9500.0, S=8250.0)`` — the rational curve.
* ``TierChain(model)`` — computes ``chain_cost(actor)`` for any buildable actor.
* ``effective_tier(design_value, derived_value, default=1.0)`` — precedence-aware
  tier multiplier for consumers.
"""
from __future__ import annotations

import json
import math
import pathlib
import sys
from collections.abc import Iterable

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "audit"))
sys.path.insert(0, str(ROOT / "tools" / "balance"))

from cameo_model import Model
from formula import TIER_B, TIER_S, tier_multiplier

PILOT_PROMOTION_FACTIONS = (
    "ra1_allies", "ra1_soviets", "td_gdi", "td_nod",
)
PROMOTION_VIRTUAL_COST_PER_TIER = 1500.0


def promotion_price_context(chain_cost, promotion_tokens, token_depths,
                            per_tier=PROMOTION_VIRTUAL_COST_PER_TIER):
    """Return an explicit pricing-only chain adjustment for one actor."""
    try:
        actual = float(chain_cost)
        rate = float(per_tier)
    except (TypeError, ValueError, OverflowError):
        return {"status": "UNRESOLVED", "reason": "non_numeric_cost_or_rate",
                "chain_cost": chain_cost, "pricing_chain_cost": None}
    if (isinstance(chain_cost, bool) or isinstance(per_tier, bool)
            or not math.isfinite(actual) or actual < 0
            or not math.isfinite(rate) or rate <= 0):
        return {"status": "UNRESOLVED", "reason": "invalid_cost_or_rate",
                "chain_cost": None, "pricing_chain_cost": None}
    tokens = sorted(set(promotion_tokens))
    unknown = [token for token in tokens
               if "_promotion_" in token and token not in token_depths]
    if unknown:
        return {"status": "UNRESOLVED", "reason": "unknown_promotion_tokens",
                "promotion_tokens": unknown, "chain_cost": actual,
                "pricing_chain_cost": None}
    matched = [token for token in tokens if token in token_depths]
    if not matched:
        return {
            "status": "NOT_APPLICABLE",
            "chain_cost": actual,
            "promotion_tokens": [],
            "promotion_tier": None,
            "virtual_promotion_cost": 0.0,
            "pricing_chain_cost": actual,
        }
    if len(matched) != 1:
        return {
            "status": "UNRESOLVED",
            "reason": "multiple_promotion_tokens",
            "chain_cost": actual,
            "promotion_tokens": matched,
            "promotion_tier": None,
            "virtual_promotion_cost": None,
            "pricing_chain_cost": None,
        }
    token = matched[0]
    tier = token_depths[token]
    if isinstance(tier, bool) or not isinstance(tier, int) or tier < 1:
        return {"status": "UNRESOLVED", "reason": "promotion_depth_unresolved",
                "chain_cost": actual, "promotion_tokens": matched,
                "promotion_tier": None, "virtual_promotion_cost": None,
                "pricing_chain_cost": None}
    virtual = rate * tier
    if not math.isfinite(virtual) or not math.isfinite(actual + virtual):
        return {"status": "UNRESOLVED", "reason": "pricing_cost_overflow",
                "chain_cost": actual, "pricing_chain_cost": None}
    return {
        "status": "RESOLVED",
        "chain_cost": actual,
        "promotion_tokens": [token],
        "promotion_tier": tier,
        "virtual_promotion_cost": virtual,
        "pricing_chain_cost": actual + virtual,
    }


def resolve_promotion_depths(parents):
    """Depth of each token, withholding cycles and missing promotion parents."""
    depths = {}

    def depth(token, stack=()):
        if token in depths:
            return depths[token]
        if token in stack or token not in parents:
            return None
        values = [depth(parent, stack + (token,))
                  for parent in parents[token]
                  if parent in parents or "_promotion_" in parent]
        depths[token] = (None if any(value is None for value in values)
                         else 1 + max(values, default=0))
        return depths[token]

    for token in sorted(parents):
        depth(token)
    return depths


def effective_tier(design_value, derived_value, default: float = 1.0) -> float:
    """Return the tier multiplier to use, honouring manual overrides.

    Precedence: a manually set ``design.tech_tier`` value wins, then a
    computed ``tier_multiplier`` from the derived sidecar, then ``default``.
    """
    for v in (design_value, derived_value):
        if v is not None:
            try:
                f = float(v)
            except (TypeError, ValueError):
                continue
            if f > 0.0:
                return f
    return default


class TierChain:
    """Buildable-prerequisite chain resolver with memoization."""

    def __init__(self, model: Model):
        self.model = model
        self._pack_cache: dict[str, tuple[str, str] | None] = {}
        self._building_costs: dict[str, float] = {}
        self._provider_index: dict[str, list[tuple[str, float, tuple[str, str]]]] = {}
        self._closure_cache: dict[tuple[frozenset, str], frozenset[str]] = {}
        self._visiting: set[str] = set()
        self._promotion_depth_cache: dict[str, int | None] | None = None
        self._build_index()

    # ------------------------------------------------------------------ #
    # Pack identification
    # ------------------------------------------------------------------ #
    def _pack_of(self, actor_name: str) -> tuple[str, str] | None:
        """Return (theme, leaf) pack for an actor, or None if undetermined."""
        if actor_name not in self._pack_cache:
            self._pack_cache[actor_name] = self._pack_of_uncached(actor_name)
        return self._pack_cache[actor_name]

    def _pack_of_uncached(self, actor_name: str) -> tuple[str, str] | None:
        owner = self.model.owner_of(actor_name)
        if owner:
            if "/" in owner:
                theme, leaf = owner.split("/", 1)
                return (theme, leaf)
            # Single-token ownership (e.g. monolithic conyard gate tokens).
            # Try to recover a theme from the actor's file path.
            return self._pack_from_path(actor_name, owner)
        return self._pack_from_path(actor_name, None)

    def _pack_from_path(self, actor_name: str, fallback_leaf: str | None) -> tuple[str, str] | None:
        node = self.model.rs.actor(actor_name)
        if node is None:
            return None
        rel = pathlib.PurePosixPath(str(node.file).replace("\\", "/"))
        parts = rel.parts
        if "ContentPacks" in parts:
            i = parts.index("ContentPacks")
            theme = parts[i + 1] if i + 1 < len(parts) else ""
            leaf = parts[i + 2] if i + 2 < len(parts) else ""
            if leaf in ("rules", "content.yaml", "files", "translations"):
                leaf = fallback_leaf or ""
            return (theme.lower(), leaf.lower())
        # Non-ContentPack file (e.g. mods/cameo/rules/<theme>.yaml).
        if parts and len(parts) >= 2:
            fname = parts[-1]
            if "." in fname:
                theme = fname.rsplit(".", 1)[0].lower()
                return (theme, (fallback_leaf or actor_name).lower())
        if fallback_leaf:
            return (fallback_leaf.lower(), fallback_leaf.lower())
        return None

    # ------------------------------------------------------------------ #
    # Index of token -> building providers
    # ------------------------------------------------------------------ #
    def _build_index(self) -> None:
        for actor_name in self.model.rs.actors:
            if actor_name.startswith("^"):
                continue
            try:
                resolved = self.model.rs.resolve(actor_name)
            except Exception:
                continue
            if resolved is None:
                continue
            if resolved.child("Building") is None:
                continue
            valued = resolved.child("Valued")
            if valued is None:
                continue
            raw_cost = valued.get("Cost")
            if raw_cost is None:
                continue
            try:
                cost = float(str(raw_cost).replace(",", ""))
            except (TypeError, ValueError):
                continue
            pack = self._pack_of(actor_name)
            if pack is None:
                continue
            self._building_costs[actor_name] = cost
            # Building plugs (addons placed on a host building) provide their
            # tokens through the host, not by being built as a separate actor,
            # so they do not auto-provide their own actor name.  Other
            # ProvidesPrerequisite tokens they expose are still indexed.
            if resolved.child("Plug") is None:
                self._add_provider(actor_name, actor_name.lower(), cost, pack)
            for c in resolved.children_named("ProvidesPrerequisite"):
                token = c.get("Prerequisite") or actor_name
                token = str(token).strip().lower()
                if token:
                    self._add_provider(actor_name, token, cost, pack)

    def _add_provider(self, actor_name: str, token: str, cost: float, pack: tuple[str, str]) -> None:
        self._provider_index.setdefault(token, []).append((actor_name, cost, pack))

    # ------------------------------------------------------------------ #
    # Chain resolution
    # ------------------------------------------------------------------ #
    def _allowed_packs(self, pack: tuple[str, str]) -> frozenset:
        """Own pack plus the same game's Shared pack."""
        theme, _ = pack
        return frozenset({pack, (theme, "shared")})

    def _cheapest_provider(self, token: str, allowed: frozenset) -> str | None:
        """Cheapest valid building for a token within the allowed packs."""
        candidates = self._provider_index.get(token, [])
        best = None
        best_cost = None
        for actor_name, cost, pack in candidates:
            if pack not in allowed:
                continue
            if best is None or cost < best_cost:
                best = actor_name
                best_cost = cost
            elif cost == best_cost and actor_name < best:
                best = actor_name
        return best

    def _closure(self, actor_name: str, allowed: frozenset) -> frozenset[str]:
        """Unique set of building actors required to build ``actor_name``."""
        key = (allowed, actor_name)
        if key in self._closure_cache:
            return self._closure_cache[key]
        if actor_name in self._visiting:
            return frozenset({actor_name})  # cycle break: keep the actor, stop recursing
        self._visiting.add(actor_name)
        result = {actor_name}
        try:
            resolved = self.model.rs.resolve(actor_name)
        except Exception:
            resolved = None
        if resolved is not None:
            for token in Model.positive_prereqs(resolved):
                if token == actor_name.lower():
                    continue
                provider = self._cheapest_provider(token, allowed)
                if provider and provider != actor_name:
                    result.update(self._closure(provider, allowed))
        self._visiting.discard(actor_name)
        result_f = frozenset(result)
        self._closure_cache[key] = result_f
        return result_f

    def chain_cost(self, actor_name: str) -> float | None:
        """Return the total chain cost C for a buildable actor, or None.

        C is the sum of the Valued.Cost of every unique building actor in the
        prerequisite closure.  The actor's own cost (if it is a building) is
        not included.
        """
        resolved = self.model.rs.resolve(actor_name)
        if resolved is None:
            return None
        buildable = resolved.child("Buildable")
        if buildable is None or not buildable.get("Queue"):
            return None
        pack = self._pack_of(actor_name)
        if pack is None:
            return None
        allowed = self._allowed_packs(pack)
        seen: set[str] = set()
        total = 0.0
        for token in Model.positive_prereqs(resolved):
            provider = self._cheapest_provider(token, allowed)
            if provider is None:
                continue
            for bldg in self._closure(provider, allowed):
                if bldg not in seen:
                    seen.add(bldg)
                    total += self._building_costs.get(bldg, 0.0)
        return total

    def chain_cost_map(self, buildable_actors: Iterable[str] | None = None) -> dict[str, float | None]:
        """Compute chain cost for many actors (default: all buildable actors)."""
        if buildable_actors is None:
            buildable_actors = [a for a in self.model.rs.actors if not a.startswith("^")]
        return {a: self.chain_cost(a) for a in buildable_actors}

    def promotion_depths(self) -> dict[str, int | None]:
        """Return provided pilot promotion token to authored column depth."""
        if self._promotion_depth_cache is not None:
            return dict(self._promotion_depth_cache)
        parents = {}
        for actor in self.model.rs.actors:
            if not any(actor.startswith(faction + "_promotion_")
                       for faction in PILOT_PROMOTION_FACTIONS):
                continue
            resolved = self.model.rs.resolve(actor)
            if resolved is None:
                continue
            provided = [
                (child.get("Prerequisite") or actor).strip().lower()
                for child in resolved.children_named("ProvidesPrerequisite")
            ] or [actor.lower()]
            positive = self.model.positive_prereqs(resolved)
            for token in provided:
                parents[token] = positive

        depths = resolve_promotion_depths(parents)
        self._promotion_depth_cache = depths
        return dict(depths)

    def promotion_pricing_context(self, actor_name: str,
                                  per_tier=PROMOTION_VIRTUAL_COST_PER_TIER):
        """Return actual and pricing-only chain costs without changing tech."""
        actual = self.chain_cost(actor_name)
        resolved = self.model.rs.resolve(actor_name)
        if actual is None or resolved is None:
            return {"status": "UNRESOLVED", "reason": "actor_or_chain_unresolved",
                    "chain_cost": actual, "pricing_chain_cost": None}
        return promotion_price_context(
            actual,
            self.model.positive_prereqs(resolved),
            self.promotion_depths(),
            per_tier,
        )

    def tier_for_actor(self, design_tech_tier, derived_multiplier, default: float = 1.0) -> float:
        return effective_tier(design_tech_tier, derived_multiplier, default)


def load_derived_map(ledger_dir: pathlib.Path | None = None) -> dict[str, dict]:
    """Load all derived sidecars into an actor -> entry map.

    Actor names are unique across the entire ledger namespace; on the rare
    duplicate, the last file wins (deterministic because files are sorted).
    """
    if ledger_dir is None:
        ledger_dir = ROOT / "docs" / "balance"
    derived_dir = ledger_dir / "derived"
    out: dict = {}
    for jf in sorted(derived_dir.glob("*.json")):
        try:
            doc = json.loads(jf.read_text(encoding="utf-8"))
        except Exception:
            continue
        for section, sec in doc.get("sections", {}).items():
            for actor, entry in sec.items():
                out[actor] = entry or {}
    return out
