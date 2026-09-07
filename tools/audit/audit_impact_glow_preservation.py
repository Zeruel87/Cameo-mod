#!/usr/bin/env python3
"""Enforce explicit emissive-impact glow policy for weapon effects.

``CreateEffect.Explosions`` is OpenRA's generic impact-animation field: it also
contains non-emissive piffs, poofs, and splashes.  Glow eligibility is therefore
an explicit visual decision at each sprite-bearing root effect, never inferred
from the presence of ``Explosions`` or ``Image`` alone.

``GlowImpactWarhead.IsValidAgainst`` currently accepts every actor, so target
filters cannot independently light one ground/air animation while excluding a
water splash in the same root.  Classification is intentionally root-wide.
"""
from __future__ import annotations

import argparse
import sys

from miniyaml import Ruleset, find_repo_root


GLOW_TIERS = {
	"^ImpactGlow_Light": ("0.3", "6"),
	"^ImpactGlow_Medium": ("0.55", "10"),
	"^ImpactGlow": ("0.8", "15"),
}

# Root effects whose impact art is intentionally explosive or emissive.
# Descendant effect templates inherit the same classification.
EMISSIVE_EFFECT_ROOTS = {
	# Explicit faction compositions preserve the authored Apocalypse explosion.
	"^Effect_Apoc_AP_RA2",
	"^Effect_Apoc_Chem_RA2",
	"^Effect_CannonAP_Light",
	"^Effect_CannonAP_Medium",
	"^Effect_CannonAP_Heavy",
	"^Effect_CannonHE_Light",
	"^Effect_CannonHE_Medium",
	"^Effect_CannonHE_Heavy",
	"^Effect_Chem_Light",
	"^Effect_Chem_Medium",
	"^Effect_Chem_Heavy",
	"^Effect_Concussion_Light",
	"^Effect_Concussion_Medium",
	"^Effect_Concussion_Heavy",
	"^Effect_Demolition_Light",
	"^Effect_Demolition_Light_RA2",
	"^Effect_Demolition_Medium",
	"^Effect_Demolition_Heavy",
	"^Effect_Flak_Light",
	"^Effect_Flak_Medium",
	"^Effect_Flak_Heavy",
	"^Effect_Flame_Light",
	"^Effect_Flame_Medium",
	"^Effect_Flame_Heavy",
	"^Effect_Ion_Ring_RA2",
	"^Effect_Laser_Heavy",
	"^Effect_Magic_Light",
	"^Effect_Magic_Medium",
	"^Effect_Magic_Heavy",
	"^Effect_MissileAP_Light",
	"^Effect_MissileAP_Medium",
	"^Effect_MissileAP_Heavy",
	"^Effect_MissileHE_Light",
	"^Effect_MissileHE_Medium",
	"^Effect_MissileHE_Heavy",
	"^Effect_Nuclear_Super",
	"^Effect_Psi_Wave_RA2",
	"^Effect_Railgun_Heavy",
	"^Effect_Sonic_Light",
	"^Effect_Sonic_Medium",
	"^Effect_Sonic_Heavy",
	"^Effect_Sonic_Shell",
	"^Effect_Tesla_Impact_RA2",
}

# These roots have sprite animations, but the art is a non-emissive hit/poof.
NON_EMISSIVE_EFFECT_ROOTS = {
	"^Effect_Arrow_Light",
	"^Effect_Arrow_Medium",
	"^Effect_Arrow_Heavy",
	"^Effect_Bullet_Light",
	"^Effect_Bullet_Medium",
	"^Effect_Bullet_Heavy",
	# These templates historically had no impact glow.  The cryo effect also
	# needs a dedicated cold-colour tier before it can glow without turning orange.
	"^Effect_Cryo",
	"^Effect_Demolition_Heavy_D2K_Orni",
	"^Effect_MissileAP_Heavy_D2K_ORocket",
	"^Effect_Sniper_Light",
}


def direct_parents(ruleset: Ruleset, name: str) -> list[str]:
	node = ruleset.weapon(name)
	if node is None:
		return []
	return [
		child.value for child in node.children
		if child.key == "Inherits" or child.key.startswith("Inherits@")
	]


def has_impact_sprite(node) -> bool:
	return node is not None and any(
		child.key.startswith("Warhead@") and child.value == "CreateEffect" and
		(child.get("Explosions") is not None or child.get("Image") is not None)
		for child in node.children)


def has_impact_glow(node) -> bool:
	return node is not None and any(
		child.key == "Warhead@Glow" and child.value == "GlowImpact"
		for child in node.children)


def sprite_root(
		ruleset: Ruleset, name: str, sprite_effects: set[str], stack: tuple[str, ...] = ()) -> str:
	if name.lower() in {item.lower() for item in stack}:
		return name
	# An explicitly classified descendant is a semantic effect boundary even if
	# it inherits a broader sprite-bearing effect and removes/replaces that art.
	if name in EMISSIVE_EFFECT_ROOTS or name in NON_EMISSIVE_EFFECT_ROOTS:
		return name
	parents = [parent for parent in direct_parents(ruleset, name) if parent in sprite_effects]
	if not parents:
		return name
	# The active effect graph currently has at most one sprite-bearing effect parent.
	return sprite_root(ruleset, parents[-1], sprite_effects, stack + (name,))


def tier_path_count(
		ruleset: Ruleset, name: str, memo: dict[str, int], stack: tuple[str, ...] = ()) -> int:
	key = name.lower()
	if key in memo:
		return memo[key]
	if key in {item.lower() for item in stack}:
		return 0
	if name in NON_EMISSIVE_EFFECT_ROOTS:
		memo[key] = 0
		return 0
	total = 0
	for parent in direct_parents(ruleset, name):
		if parent in GLOW_TIERS:
			total += 1
		total += tier_path_count(ruleset, parent, memo, stack + (name,))
	memo[key] = total
	return total


def show(label: str, names: set[str], details: bool) -> None:
	print(f"{label}: {len(names)}")
	if details:
		for name in sorted(names):
			print(f"  {name}")


def main() -> int:
	parser = argparse.ArgumentParser()
	parser.add_argument("--details", action="store_true")
	args = parser.parse_args()

	ruleset = Ruleset(find_repo_root())
	effects = sorted(name for name in ruleset.weapons if name.startswith("^Effect"))
	resolved = {name: ruleset.resolve_weapon(name) for name in effects}
	sprite_effects = {name for name in effects if has_impact_sprite(resolved[name])}
	non_sprite_effects = set(effects) - sprite_effects
	glowing_effects = {name for name in effects if has_impact_glow(resolved[name])}

	root_for = {name: sprite_root(ruleset, name, sprite_effects) for name in sprite_effects}
	active_sprite_roots = set(root_for.values())
	classified_roots = EMISSIVE_EFFECT_ROOTS | NON_EMISSIVE_EFFECT_ROOTS
	unclassified_roots = active_sprite_roots - classified_roots
	stale_classifications = classified_roots - active_sprite_roots
	overlapping_classifications = EMISSIVE_EFFECT_ROOTS & NON_EMISSIVE_EFFECT_ROOTS

	expected_glow = {
		name for name, root in root_for.items() if root in EMISSIVE_EFFECT_ROOTS
	}
	expected_no_glow = set(effects) - expected_glow
	missing_glow = expected_glow - glowing_effects
	unexpected_glow = expected_no_glow & glowing_effects

	tier_memo: dict[str, int] = {}
	bad_tier_paths = {
		name for name in effects
		if tier_path_count(ruleset, name, tier_memo) != (1 if name in expected_glow else 0)
	}
	obsolete_variants = {
		name for name in effects if name.endswith("_Glow") or name.endswith("_NoGlow")
	}

	inline_threeway: set[str] = set()
	legacy_inline: set[str] = set()
	for name in ruleset.weapons:
		if name.startswith("^"):
			continue
		parents = direct_parents(ruleset, name)
		if "^ImpactGlow" not in parents:
			continue
		if any(parent.startswith("^Effect") for parent in parents):
			inline_threeway.add(name)
		else:
			legacy_inline.add(name)

	bad_tier_config: set[str] = set()
	for tier, (scale, fade) in GLOW_TIERS.items():
		node = ruleset.resolve_weapon(tier)
		glow = None if node is None else next(
			(child for child in node.children if child.key == "Warhead@Glow"), None)
		if (glow is None or glow.value != "GlowImpact" or glow.get("Scale") != scale or
				glow.get("FadeFrames") != fade):
			bad_tier_config.add(tier)

	print("# Explicit emissive-impact glow audit")
	print(f"active ^Effect* templates: {len(effects)}")
	print(f"sprite-backed effect roots: {len(active_sprite_roots)}")
	print(f"emissive roots: {len(EMISSIVE_EFFECT_ROOTS)}")
	print(f"non-emissive sprite roots: {len(NON_EMISSIVE_EFFECT_ROOTS)}")
	print(f"resolved emissive effects: {len(expected_glow)}")
	show("unclassified sprite roots", unclassified_roots, args.details)
	show("stale root classifications", stale_classifications, args.details)
	show("overlapping root classifications", overlapping_classifications, args.details)
	show("emissive effects missing glow", missing_glow, args.details)
	show("non-emissive effects with glow", unexpected_glow, args.details)
	show("effects with invalid tier-path count", bad_tier_paths, args.details)
	show("obsolete glow/no-glow effect variants", obsolete_variants, args.details)
	show("three-way weapons with inline ^ImpactGlow", inline_threeway, args.details)
	show("bad glow-tier configuration", bad_tier_config, args.details)
	show("informational non-sprite effects", non_sprite_effects, args.details)
	show("informational legacy inline glows", legacy_inline, args.details)

	failed = bool(
		unclassified_roots or stale_classifications or overlapping_classifications or
		missing_glow or unexpected_glow or bad_tier_paths or obsolete_variants or
		inline_threeway or bad_tier_config)
	print("result: " + ("FAIL" if failed else "PASS"))
	return 1 if failed else 0


if __name__ == "__main__":
	sys.exit(main())
