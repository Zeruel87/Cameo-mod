"""The Katyusha identity (Aedis DM 2026-09-09, under Blackrobe's overnight authority).

The V1 Rocket Truck maps to Combined Arms' `KATY` and is renamed Katyusha for players, while
everything internal — actor id, assets, weapons, AI, maps — stays exactly as it is. These tests
pin the three things that could silently regress:

  1. the RESOLVED player-facing name on the live actor;
  2. the internal id, unchanged;
  3. the maintainer override: its source, its peer id, and the routing that admits it — plus the
     guarantee that it displaced nobody (no other actor holds CA KATY).

The assignment assertions run against BOTH the live `assign()` pass and the committed
`docs/balance/derived/reference_assignment.json`: the live pass is the guarantee that the
override displaces nobody, and the committed file is asserted because the generator is now
deterministic (`variant_rank` replaced in a stable longest-first order as of 2026-09-09 — it
used to iterate a frozenset and flip per process) and is regenerated with this change.
"""

from __future__ import annotations

import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "balance"))
sys.path.insert(0, str(ROOT / "tools" / "audit"))

import assign_references as ar          # noqa: E402
import faction_routes as fr             # noqa: E402
import reference_distribution as rd     # noqa: E402
from miniyaml import Ruleset            # noqa: E402

ACTOR = "ra1_soviets_v1rockettruck"
SOURCE = "Combined Arms"
PEER_ID = "KATY"
COMMITTED = ROOT / "docs" / "balance" / "derived" / "reference_assignment.json"


class KatyushaIdentityTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rules = Ruleset(ROOT)
        cls.peers = [p for p in rd.peer_rows()
                     if p.get("source") == SOURCE and (p.get("id") or "").upper() == PEER_ID]
        result, skipped, _ = ar.assign()
        cls.assignment = result
        cls.skipped = skipped

    def test_resolved_active_actor_is_named_katyusha(self):
        node = self.rules.resolve(ACTOR)
        self.assertIsNotNone(node, f"{ACTOR} does not resolve")
        self.assertEqual(node.get("Tooltip", "Name"), "Katyusha")

    def test_the_actor_is_active_and_buildable(self):
        node = self.rules.resolve(ACTOR)
        self.assertIsNotNone(node.child("Buildable"), "actor has no Buildable")
        self.assertIn("Vehicle", (node.get("Buildable", "Queue") or "").split(","))

    def test_internal_id_is_unchanged(self):
        raw = self.rules.actor(ACTOR)
        self.assertIsNotNone(raw, f"{ACTOR} missing from the ruleset")
        self.assertEqual(raw.key, ACTOR)
        self.assertIn("vehicles.yaml", (raw.file or "").replace("\\", "/"),
                      f"{ACTOR} moved out of the Soviet vehicle file-set: {raw.file}")
        resolved = self.rules.resolve(ACTOR)
        self.assertEqual(resolved.key, ACTOR)

    def test_the_override_is_registered_with_source_and_id(self):
        self.assertEqual(ar.REFERENCE_OVERRIDES.get((ACTOR, SOURCE)), PEER_ID)

    def test_the_peer_row_exists_and_is_routed(self):
        self.assertEqual(len(self.peers), 1, "expected exactly one Combined Arms KATY row")
        row = self.peers[0]
        self.assertEqual(row.get("name"), "Katyusha")
        self.assertEqual(row.get("type"), "vehicle")
        self.assertTrue(fr.allows("ra1_soviets", row),
                        "ra1_soviets -> Combined Arms (soviet) does not admit KATY")

    def test_the_assignment_holds_katy_and_displaced_nobody(self):
        row = self.assignment.get(ACTOR, {}).get(SOURCE)
        self.assertIsNotNone(row, f"{ACTOR} holds no {SOURCE} reference")
        self.assertEqual((row.get("id") or "").upper(), PEER_ID)
        self.assertEqual(row.get("confidence"), "STRONG")
        holders = [cid for cid, srcs in self.assignment.items()
                   for src, d in srcs.items()
                   if src == SOURCE and (d.get("id") or "").upper() == PEER_ID]
        self.assertEqual(holders, [ACTOR], f"CA KATY leaked to other actors: {holders}")
        self.assertEqual(list(getattr(ar.apply_overrides, "missing", ())), [],
                         "the override no longer resolves against the routed pool")

    def test_the_committed_assignment_carries_the_mapping(self):
        """The regenerated file must agree with the live pass — the generator is deterministic
        now, so a stale or missing row here means the JSON was not regenerated with the change."""
        import json
        doc = json.loads(COMMITTED.read_text(encoding="utf-8"))
        row = (doc.get("assignment") or {}).get(ACTOR, {}).get(SOURCE)
        self.assertIsNotNone(row, f"committed reference_assignment.json has no {SOURCE} row "
                                  f"for {ACTOR} — regenerate with assign_references.py --write")
        self.assertEqual((row.get("id") or "").upper(), PEER_ID)
        self.assertEqual(row.get("name"), "Katyusha")
        self.assertEqual(row.get("confidence"), "STRONG")


if __name__ == "__main__":
    unittest.main()
