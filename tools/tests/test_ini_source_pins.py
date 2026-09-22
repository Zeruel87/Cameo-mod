import hashlib
import json
import pathlib
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "reference"))

import ini_source_pins as pins  # noqa: E402
import extract_ini_projectile_roles as projectile_roles  # noqa: E402


EXPECTED = {
    "Rise of the East",
    "RA2 0XX",
    "Mental Omega",
    "CnC Reloaded",
    "Red Resurrection",
    "RA2 Reborn",
    "Twisted Insurrection",
}


class RepositoryPins(unittest.TestCase):
    def test_all_seven_previously_unpinned_sources_are_covered(self):
        loaded = pins.load(ROOT)
        self.assertEqual(EXPECTED, set(loaded))
        self.assertEqual(10144, sum(entry["row_count"] for entry in loaded.values()))
        self.assertEqual(64, sum(entry["preserved_secondary_occurrences"]
                                 for entry in loaded.values()))
        self.assertEqual(63, sum(entry["preserved_secondary_identities"]
                                 for entry in loaded.values()))

    def test_sidecar_is_bound_to_the_current_corpus_links(self):
        for source, entry in pins.load(ROOT).items():
            rows = pins.source_rows(source, ROOT)
            self.assertEqual(len(rows), entry["row_count"])
            self.assertEqual(pins.weapon_link_fingerprint(rows),
                             entry["corpus_weapon_links_sha256"])


class ExternalVerification(unittest.TestCase):
    def fixture(self, root, *, source="Fixture", actor_secondary="RealGun"):
        ini_dir = root / "external"
        ini_dir.mkdir()
        rules = ini_dir / "rules.ini"
        rules.write_text(
            "[VehicleTypes]\n0=TANK\n[TANK]\nPrimary=Dummy\n"
            f"Secondary={actor_secondary}\n[Dummy]\nDamage=0\nProjectile=Invisible\n"
            "[RealGun]\nDamage=10\nProjectile=Shell\n[Shell]\nAA=no\nAG=yes\n",
            encoding="latin-1")
        corpus = root / "docs" / "reference" / "ini_corpus.json"
        corpus.parent.mkdir(parents=True)
        row = {"source": source, "id": "TANK", "secondary": "RealGun",
               "weapon": "RealGun", "w_projectile": "Shell",
               "w_from_secondary": True, "w_dummy_primary": "Dummy"}
        corpus.write_text(json.dumps(row, sort_keys=True) + "\n", encoding="utf-8")
        entry = {"source": source, "file": "rules.ini", "engine": "ra2",
                 "rules_sha256": hashlib.sha256(rules.read_bytes()).hexdigest(),
                 "row_count": 1,
                 "corpus_weapon_links_sha256": pins.weapon_link_fingerprint([row]),
                 "preserved_secondary_occurrences": 1,
                 "preserved_secondary_identities": 1}
        sidecar = root / pins.RELATIVE
        sidecar.write_text(json.dumps({"schema": 1, "sources": [entry]}),
                           encoding="utf-8")
        return ini_dir, entry

    def test_exact_bytes_and_promoted_slot_chain_verify(self):
        with tempfile.TemporaryDirectory() as temp:
            root = pathlib.Path(temp)
            ini_dir, entry = self.fixture(root)
            self.assertEqual(1, pins.verify_entry(entry, ini_dir, root)["rows"])

    def test_changed_bytes_fail_closed(self):
        with tempfile.TemporaryDirectory() as temp:
            root = pathlib.Path(temp)
            ini_dir, entry = self.fixture(root)
            (ini_dir / "rules.ini").write_text("changed", encoding="latin-1")
            with self.assertRaisesRegex(ValueError, "SHA-256"):
                pins.verify_entry(entry, ini_dir, root)

    def test_changed_corpus_slot_fails_closed(self):
        with tempfile.TemporaryDirectory() as temp:
            root = pathlib.Path(temp)
            ini_dir, entry = self.fixture(root, actor_secondary="OtherGun")
            with self.assertRaisesRegex(ValueError, "Secondary link moved"):
                pins.verify_entry(entry, ini_dir, root)

    def test_stamping_adds_only_the_source_hash(self):
        with tempfile.TemporaryDirectory() as temp:
            root = pathlib.Path(temp)
            ini_dir, entry = self.fixture(root)
            corpus = root / pins.CORPUS_RELATIVE
            before = json.loads(corpus.read_text(encoding="utf-8"))
            changed, verified = pins.stamp_corpus(ini_dir, root)
            self.assertEqual(1, changed)
            self.assertEqual(1, len(verified))
            after = json.loads(corpus.read_text(encoding="utf-8"))
            digest = after.pop("source_sha256")
            self.assertEqual(entry["rules_sha256"], digest)
            self.assertEqual(before, after)
            self.assertEqual(0, pins.stamp_corpus(ini_dir, root)[0])


class ConsumerPinRefusals(unittest.TestCase):
    def write_corpus(self, root, rows):
        path = root / pins.CORPUS_RELATIVE
        path.parent.mkdir(parents=True)
        path.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")

    def test_partial_source_pin_is_not_consumed(self):
        with tempfile.TemporaryDirectory() as temp:
            root = pathlib.Path(temp)
            self.write_corpus(root, [
                {"source": "S", "source_sha256": "a" * 64},
                {"source": "S"},
            ])
            self.assertNotIn("S", projectile_roles.corpus_provenance(root))
            self.assertIn(("S", "source pin is partial"),
                          projectile_roles.corpus_provenance.dropped)

    def test_conflicting_source_pins_are_not_consumed(self):
        with tempfile.TemporaryDirectory() as temp:
            root = pathlib.Path(temp)
            self.write_corpus(root, [
                {"source": "S", "source_sha256": "a" * 64},
                {"source": "S", "source_sha256": "b" * 64},
            ])
            self.assertNotIn("S", projectile_roles.corpus_provenance(root))
            self.assertIn(("S", "source pins conflict"),
                          projectile_roles.corpus_provenance.dropped)


if __name__ == "__main__":
    unittest.main()
