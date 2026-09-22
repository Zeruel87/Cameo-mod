#!/usr/bin/env python3
"""Physical-state meters: check the FOLDED warhead, and reject double-application.

The Formula V2 Flame and Chemical families raise Temperature/Corrosion in proportion to actual
damage. Checks:

  1. Each `^Warhead_{Flame,Chemical}_{Light,Medium,Heavy}` main warhead carries its meter AND a
     non-zero `PercentageScale`, so the percentage component reaches the same meter.
  2. No resolved weapon combines a damage-scaled meter with a legacy fixed `ApplyPhysicalState`
     for that same meter — both routes apply; their combined effect depends on the authored amounts.
  3. No AreaDamage/AreaDamagePercentage node binds the same enabled state twice.
     Runtime executes both routes and rounds each application separately.

⛔ CHECK (1) USED TO LOOK FOR A SEPARATE `Warhead@<tag>_Percentage` TWIN, AND THAT WAS STALE.
The AreaDamage fold put flat damage, the percentage component and friendly fire into ONE warhead:
`PercentageScale` / `PercentageSpread` / `PercentageVersus` and `FriendlyFireDamage` /
`FriendlyFireSpread` are fields on `AreaDamageWarhead` itself. There are no twins any more, so the
audit reported all six templates as "missing percentage warhead" against a structure the design had
retired — six false failures that turned the whole suite red. Corrected 2026-08-24 after the
maintainer caught it. Verify the shape before trusting a count:

    Warhead@Flame_Light: AreaDamage
        Damage: 2000  Spread: 200  Falloff: ...    <- flat
        PercentageScale: 10000  PercentageSpread: 50 <- percentage, folded in
        FriendlyFireDamage: 50  FriendlyFireSpread: 50
        PhysicalStateName: Temperature  PhysicalStateScale: 100

⚠ The meter comes in TWO forms and both are legal: Flame uses the singular
`PhysicalStateName`/`PhysicalStateScale`, Chemical uses the `PhysicalStates:` MAP (blend families
emit the map). `scaled_states()` and `state_scale()` read both — never grep for one.
"""

from __future__ import annotations

import sys
import re

from miniyaml import Ruleset, find_repo_root


EXPECTED_PERCENTAGE_STATES = {
	"Flame": ("Temperature", "100"),
	"Chemical": ("Corrosion", "100"),
}
LEVELS = ("Light", "Medium", "Heavy")
PERCENTAGE_KEY = re.compile(r"Warhead@(Flame|Chemical)_(Light|Medium|Heavy)_Percentage$")


def state_bindings(warhead):
	"""Keep both runtime applications; zero scales do not apply a state."""
	bindings = []
	name = warhead.get("PhysicalStateName")
	scale = int(warhead.get("PhysicalStateScale") or "0")
	if name and scale:
		bindings.append((name, scale))
	multiple = warhead.child("PhysicalStates")
	if multiple:
		for child in multiple.children:
			scale = int(child.value or "0")
			if scale:
				bindings.append((child.key, scale))
	return bindings


def duplicate_state_problems(warhead):
	if warhead.value not in {"AreaDamage", "AreaDamagePercentage"}:
		return []
	by_state = {}
	for name, scale in state_bindings(warhead):
		by_state.setdefault(name, []).append(scale)
	return [
		f"{warhead.key}: applies {name} through multiple bindings {scales} "
		f"(combined nominal scale {sum(scales)}; runtime rounds each separately)"
		for name, scales in sorted(by_state.items()) if len(scales) > 1
	]


def scaled_states(warhead):
	return {name for name, _scale in state_bindings(warhead)}


def state_scale(warhead, state):
	values = [scale for name, scale in state_bindings(warhead) if name == state]
	return str(sum(values)) if values else None


def main() -> int:
	rs = Ruleset(find_repo_root())
	problems = []

	for family, (expected_state, expected_scale) in EXPECTED_PERCENTAGE_STATES.items():
		for level in LEVELS:
			tag = f"{family}_{level}"
			template_name = f"^Warhead_{tag}"
			# RESOLVED, not source: the meter and the percentage fields can be inherited.
			template = rs.resolve_weapon(template_name)
			main = template.child(f"Warhead@{tag}") if template else None
			if main is None:
				problems.append(f"{template_name}: no Warhead@{tag} main warhead")
				continue

			if main.value != "AreaDamage":
				problems.append(
					f"{template_name}: main warhead is {main.value}, expected AreaDamage")
			if expected_state not in scaled_states(main):
				problems.append(
					f"{template_name}: main warhead does not apply {expected_state}")
			if state_scale(main, expected_state) != expected_scale:
				problems.append(
					f"{template_name}: {expected_state} scale is not {expected_scale}")

			# The fold's whole point: percentage damage rides the SAME warhead, so it reaches the
			# same meter. A zero or absent scale means the percentage component silently does not
			# exist, which is the pre-fold bug wearing the post-fold shape.
			scale = main.get("PercentageScale")
			if scale is None or str(scale).strip() in {"", "0"}:
				problems.append(
					f"{template_name}: PercentageScale is {scale!r} — percentage damage is folded "
					f"into this warhead and must be non-zero")

	for weapon_name in sorted(rs.weapons, key=str.lower):
		if weapon_name.startswith("^"):
			continue

		weapon = rs.resolve_weapon(weapon_name)
		if weapon is None:
			continue

		damage_scaled = set()
		fixed = set()
		for warhead in weapon.children:
			problems.extend(
				f"{weapon_name}: {problem}"
				for problem in duplicate_state_problems(warhead))
			match = PERCENTAGE_KEY.fullmatch(warhead.key)
			if match:
				family = match.group(1)
				expected_state, expected_scale = EXPECTED_PERCENTAGE_STATES[family]
				if (warhead.value != "AreaDamagePercentage"
						or expected_state not in scaled_states(warhead)
						or state_scale(warhead, expected_state) != expected_scale):
					problems.append(
						f"{weapon_name}: {warhead.key} does not feed {expected_state} through AreaDamagePercentage")

			if warhead.value in {"AreaDamage", "AreaDamagePercentage"}:
				damage_scaled.update(scaled_states(warhead))
			elif warhead.value == "ApplyPhysicalState":
				state = warhead.get("PhysicalStateName")
				if state:
					fixed.add(state)

		for state in sorted(damage_scaled & fixed):
			problems.append(
				f"{weapon_name}: combines damage-scaled and fixed ApplyPhysicalState for {state}")

	print("# Physical-state warhead audit\n")
	print(f"Active concrete weapons checked: {sum(not name.startswith('^') for name in rs.weapons)}")
	print(f"Formula percentage templates checked: {len(EXPECTED_PERCENTAGE_STATES) * len(LEVELS)}\n")
	if problems:
		print(f"## FAIL ({len(problems)} problem(s))\n")
		for problem in problems:
			print(f"- {problem}")
		return 1

	print("## PASS\n")
	print("- Flame and Chemical fold percentage damage into the main AreaDamage warhead, and it")
	print("  feeds the matching physical-state meter.")
	print("- No active weapon double-applies a meter through scaled and fixed warheads.")
	return 0


if __name__ == "__main__":
	sys.exit(main())
