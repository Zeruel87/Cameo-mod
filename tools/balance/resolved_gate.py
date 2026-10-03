#!/usr/bin/env python3
"""resolved_gate.py — the ONE comparator for "did this refactor change behaviour?".

Two separate incidents in this repo proved that a single comparison cannot answer that
question, because a resolved weapon carries TWO kinds of information and each blinds the
naive check for the other:

  ORDER-INSENSITIVE (the fields).  A rename moves a key in any sorted dump, so a line diff
  of two sorted snapshots reports every renamed weapon as changed. That is how a 1-weapon
  change was first reported as 470: `tools/balance/promote_compatibility_warheads.py`
  compared sorted text. Fields must be compared as a SET of `path = value` pairs, with the
  rename map applied to the baseline.

  ORDER-SENSITIVE (the warhead sequence).  Warheads fire in declaration order, and that is
  SEMANTIC whenever the payload contains `ChangeOwner`: reordering the Wraith's warheads put
  its 60,000-damage main at index 18, AFTER `Warhead@OwnerChange` at 17, so the Wraith
  captured a unit and then shot the unit it had just captured. A set comparison cannot see
  that, and mine did not — Codex found it in review (PR #356). The top-level warhead KEY
  SEQUENCE must be compared as a LIST.

So the gate is a hybrid: a SET over the fields, a LIST over the warhead order. Neither half
is optional and neither half subsumes the other.

⚠ The rename map is applied to the BASELINE, never to the candidate — the point is to ask
"is the new tree what the old tree would have been called under the new names", and mapping
the candidate instead would silently accept a name the map does not cover.
"""
from __future__ import annotations

WARHEAD = "Warhead@"


def pairs(node, prefix: str = "") -> set[str]:
    """A node as an order-insensitive set of `path = value`, recursively."""
    out: set[str] = set()
    for c in node.children:
        p = prefix + "/" + c.key
        out.add(p + " = " + str(c.value).strip())
        out |= pairs(c, p)
    return out


def warhead_order(node) -> list[str]:
    """The top-level warhead keys IN DECLARATION ORDER — the firing sequence.

    Only the top level: nesting under a warhead is field data, not a firing sequence.
    """
    return [c.key for c in node.children if c.key.startswith(WARHEAD)]


def apply_map(text: str, name_map: dict[str, str]) -> str:
    """Rewrite every mapped name inside one string, longest name first.

    Longest-first matters: `^Warhead_Laser_Medium` is a PREFIX of
    `^Warhead_Laser_Medium_Flat`, so a shortest-first pass would rewrite the stem of the
    longer name and leave a `_Flat` tail welded onto the new name.
    """
    for old in sorted(name_map, key=len, reverse=True):
        if old in text:
            text = text.replace(old, name_map[old])
    return text


def compare(before, after, name_map: dict[str, str] | None = None) -> dict:
    """Compare two resolved nodes. Returns {} when behaviour is preserved.

    `name_map` is applied to BEFORE, so the question asked is "does the old weapon, renamed,
    equal the new one".
    """
    nm = name_map or {}
    b_pairs = {apply_map(x, nm) for x in pairs(before)}
    a_pairs = pairs(after)
    b_order = [apply_map(x, nm) for x in warhead_order(before)]
    a_order = warhead_order(after)

    out: dict[str, object] = {}
    if b_pairs != a_pairs:
        out["lost"] = sorted(b_pairs - a_pairs)
        out["gained"] = sorted(a_pairs - b_pairs)
    if b_order != a_order:
        # Same members in a different sequence is the ChangeOwner class; different members
        # is a plain add/drop. Say which, because the two have very different severity.
        out["order_before"] = b_order
        out["order_after"] = a_order
        out["reordered_only"] = sorted(b_order) == sorted(a_order)
    return out


def describe(name: str, diff: dict, limit: int = 6) -> list[str]:
    """One weapon's diff as printable lines."""
    if not diff:
        return []
    lines = [f"  {name}"]
    for x in list(diff.get("lost", []))[:limit]:
        lines.append(f"      lost:   {x}")
    for x in list(diff.get("gained", []))[:limit]:
        lines.append(f"      gained: {x}")
    if "order_before" in diff:
        kind = ("WARHEAD ORDER CHANGED (same members) — the ChangeOwner class"
                if diff.get("reordered_only") else "warhead members changed")
        lines.append(f"      {kind}")
        lines.append(f"        before: {' '.join(diff['order_before'])}")
        lines.append(f"        after:  {' '.join(diff['order_after'])}")
    return lines


def _self_test() -> int:
    class N:
        def __init__(self, key, value="", children=()):
            self.key, self.value, self.children = key, value, list(children)

    def weapon(order, dmg="100"):
        return N("w", "", [N(k, "AreaDamage", [N("Damage", dmg)]) for k in order])

    a = weapon(["Warhead@Main", "Warhead@OwnerChange"])
    b = weapon(["Warhead@OwnerChange", "Warhead@Main"])
    assert compare(a, a) == {}, "identical must pass"
    d = compare(a, b)
    assert d and d.get("reordered_only") is True, "reorder must FAIL and be labelled"
    assert "lost" not in d, "a pure reorder must not report field loss"

    # a rename is not a change, once the map is applied
    r1 = weapon(["Warhead@Laser_Medium_Flat"])
    r2 = weapon(["Warhead@Laser_Medium"])
    assert compare(r1, r2) != {}, "without the map a rename must look like a change"
    assert compare(r1, r2, {"Laser_Medium_Flat": "Laser_Medium"}) == {}, "map must absorb it"

    # longest-first: the short name must not eat the long one's stem
    assert apply_map("^Warhead_Laser_Medium_Flat",
                     {"^Warhead_Laser_Medium": "^Warhead_Laser_Medium",
                      "^Warhead_Laser_Medium_Flat": "^Warhead_Laser_Medium"}) \
        == "^Warhead_Laser_Medium", "longest-first replacement"

    # a real field change must be caught
    assert compare(weapon(["Warhead@Main"], "100"), weapon(["Warhead@Main"], "200")) != {}
    print("resolved_gate self-test: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(_self_test())
