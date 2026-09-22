"""Regression for the bounded eight-actor TD naval rename (2026-09-10 order).

Proves the renamed actors exist and keep their resolved stats/weapons, the old
IDs no longer resolve, sprite/sequence/audio namespaces survive unchanged
(explicit old-lowercase-id RenderSprites.Image bindings), production
prerequisites resolve, production-queue/prerequisite context is preserved, and
every affected AI/map/script actor reference resolves to a live actor.
"""

from __future__ import annotations

import json
import pathlib
import re
import sys
import tempfile
import unittest
import zipfile

AUDIT_DIR = pathlib.Path(__file__).resolve().parents[1] / "audit"
ROOT = AUDIT_DIR.parents[1]

for candidate in (str(AUDIT_DIR), str(ROOT)):
    if candidate not in sys.path:
        sys.path.insert(0, candidate)

import miniyaml


RENAME = {
    "gdicarrier": "td_gdi_supercarrier",
    "CNCPT": "td_gdi_missileboat",
    "CNCCA": "td_gdi_railgunbattleship",
    "LST": "td_gdi_landingcraft",
    "CNCSS": "td_nod_attacksubmarine",
    "ssmsub": "td_nod_ballisticmissilesubmarine",
    "nodlasercorvette": "td_nod_lasercorvette",
    "CNCRSS": "td_nod_transportsubmarine",
}

EXPECTED = {
    "td_gdi_supercarrier": {
        "tooltip": "GDI Super Carrier",
        "cost": "4000",
        "hp": "300000",
        "prereq": "~cncsyrd, td_gdi_advancedcommunicationscenter",
        "queue": "Naval, RANaval",
        "image": "gdicarrier",
        "weapons": {"JapanCarrierTarget"},
        "armor": {"Superheavy", "Shield"},
    },
    "td_gdi_missileboat": {
        "tooltip": "Missile Boat",
        "cost": "1600",
        "hp": "75000",
        "prereq": "~cncsyrd",
        "queue": "Naval, RANaval",
        "image": "cncpt",
        "weapons": {"td_gdi_missileboat_gunboatmissile", "td_gdi_missileboat_gunboatmissileamt", "td_gdi_missileboat_depthcharge"},
        "armor": {"Heavy", "Shield"},
    },
    "td_gdi_railgunbattleship": {
        "tooltip": "Railgun Battleship",
        "cost": "2600",
        "hp": "167500",
        "prereq": "~cncsyrd, td_gdi_communicationscenter",
        "queue": "Naval, RANaval",
        "image": "cncca",
        "weapons": {"td_gdi_railgunbattleship_gdibattleshiprailgun"},
        "armor": {"Superheavy", "Shield"},
    },
    "td_gdi_landingcraft": {
        "tooltip": "Landing Craft",
        "cost": "500",
        "hp": "75000",
        "prereq": "~cncsyrd",
        "queue": "Naval, RANaval",
        "image": "lst",
        "weapons": set(),
        "armor": {"Medium", "Shield"},
    },
    "td_nod_attacksubmarine": {
        "tooltip": "Nod Attack Submarine",
        "cost": "1600",
        "hp": "160000",
        "prereq": "~cncspen",
        "queue": "Naval, RANaval",
        "image": "cncss",
        "weapons": {"td_nod_attacksubmarine_nodtorptube", "td_nod_attacksubmarine_nodtorptubeblackmarket"},
        "armor": {"Heavy", "Shield"},
    },
    "td_nod_ballisticmissilesubmarine": {
        "tooltip": "Ballistic Missile Submarine",
        "cost": "2800",
        "hp": "200000",
        "prereq": "~cncspen, td_nod_communicationscenter",
        "queue": "Naval, RANaval",
        "image": "ssmsub",
        "weapons": {"td_nod_ballisticmissilesubmarine_honestjohn"},
        "armor": {"Medium", "Shield"},
    },
    "td_nod_lasercorvette": {
        "tooltip": "Nod Laser Corvette",
        "cost": "2300",
        "hp": "150000",
        "prereq": "~cncspen, td_nod_templeofnod",
        "queue": "Naval, RANaval",
        "image": "nodlasercorvette",
        "weapons": {"td_nod_lasercorvette_corvettelaserobelisk", "td_nod_lasercorvette_corvettedragon"},
        "armor": {"Medium", "Shield"},
    },
    "td_nod_transportsubmarine": {
        "tooltip": "Transport Submarine",
        "cost": "500",
        "hp": "50000",
        "prereq": "~cncspen",
        "queue": "Naval, RANaval",
        "image": "cncrss",
        "weapons": set(),
        "armor": {"Light", "Shield"},
    },
}

NEW_IDS = sorted(EXPECTED)
OLD_ID_WORDS = re.compile(
    r"\b(" + "|".join(re.escape(k) for k in sorted(RENAME, key=len, reverse=True)) + r")\b",
    re.IGNORECASE,
)
FORBIDDEN_IMAGE = re.compile(
    r"^[ \t]*Image:\s*(?:"
    + "|".join(re.escape(v) for v in sorted(NEW_IDS))
    + r")\s*$",
    re.M,
)


def forbidden_image_offenders(paths):
    """Paths whose yaml assigns a renamed actor id as a RenderSprites image."""
    return [str(p) for p in paths if FORBIDDEN_IMAGE.search(p.read_text(encoding="utf-8-sig", errors="replace"))]


def node_form(node):
    """Canonical recursive payload form for a resolved MiniYaml node:
    children-dict tree, plain strings as values, '' and {} both unified."""
    r = {}
    for t in node.children:
        if t.key.startswith("Inherits"):
            continue
        r[t.key] = node_form(t)
    if node.value and node.children:
        r["#value"] = node.value
    if node.value and not node.children:
        return node.value
    return r


def unify(x):
    """'' and {} are the same empty node in every position."""
    if x == "" or x == {}:
        return {}
    if isinstance(x, dict):
        return {k: unify(v) for k, v in x.items()}
    return x


def inject(old_id, payload):
    """Make implicit old-id RenderSprites image bindings explicit."""
    for k, v in list(payload.items()):
        if k.startswith("RenderSprites") and isinstance(v, dict) and "Image" not in v:
            v["Image"] = old_id.lower()
    return payload


def armament_weapons(resolved):
    return {c.value for arm in resolved.children_named("Armament") for c in arm.children
            if c.key == "Weapon" and c.value}


def armor_types(resolved):
    return {c.get("Type") for c in resolved.children_named("Armor") if c.get("Type")}


class TdNavalRenameTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rules = miniyaml.Ruleset(ROOT)

    def test_new_actors_exist_with_preserved_names_and_stats(self):
        for actor, spec in sorted(EXPECTED.items()):
            with self.subTest(actor=actor):
                resolved = self.rules.resolve(actor)
                self.assertIsNotNone(resolved)
                self.assertEqual(spec["tooltip"], resolved.get("Tooltip", "Name"))
                self.assertEqual(spec["cost"], resolved.get("Valued", "Cost"))
                self.assertEqual(spec["hp"], resolved.get("Health", "HP"))
                self.assertEqual(spec["queue"], resolved.get("Buildable", "Queue"))
                self.assertEqual(spec["weapons"], armament_weapons(resolved))
                self.assertEqual(spec["armor"], armor_types(resolved))

    def test_old_actor_ids_are_absent(self):
        for old in sorted(RENAME):
            self.assertIsNone(self.rules.resolve(old), f"old actor id {old} still resolves")

    # Complete normalized-resolved comparison evidence lives in this fixture:
    # the captured pre-rename payload of each of the eight actors (source:
    # validation/td-naval-baseline.json shipped beside the implementation
    # order), canonicalized with the same functions used on the live tree, so
    # the fixture and the test cannot drift apart.
    FIXTURE = ROOT / "tools/tests/fixtures/td_naval_rename_baseline_normalized.json"

    @classmethod
    def load_baseline_fixture(cls):
        data = json.loads(cls.FIXTURE.read_text(encoding="utf-8-sig"))
        return data

    @staticmethod
    def tree_diff(before, after, path="", out=None):
        out = [] if out is None else out
        if isinstance(before, dict) and isinstance(after, dict):
            for k in sorted(set(before) | set(after)):
                if k not in before:
                    out.append(f"{path}/{k}: added {json.dumps(after[k])[:120]}")
                elif k not in after:
                    out.append(f"{path}/{k}: removed (baseline {json.dumps(before[k])[:120]})")
                else:
                    TdNavalRenameTests.tree_diff(before[k], after[k], f"{path}/{k}", out)
        elif before != after:
            out.append(f"{path}: baseline {json.dumps(before)[:120]} != live {json.dumps(after)[:120]}")
        return out

    def test_baseline_fixture_is_pre_rename(self):
        """Destinations absent in the captured baseline: no renamed actor id
        appears anywhere in the pre-rename payload snapshot (key or value)."""
        data = self.load_baseline_fixture()
        self.assertEqual(sorted(data["keys"]), sorted(RENAME))
        for new_id in NEW_IDS:
            found = self._fixture_contains(data, new_id)
            self.assertFalse(found, f"new id {new_id} present in captured baseline")

    @staticmethod
    def _fixture_contains(data, needle):
        def walk(x):
            if isinstance(x, str):
                return needle in x
            if isinstance(x, dict):
                return any(walk(k) or walk(v) for k, v in x.items())
            if isinstance(x, list):
                return any(walk(v) for v in x)
            return False

        return walk(data["actors"])

    def test_complete_normalized_resolved_payloads_match_baseline(self):
        """Whole-payload comparison (every field, not selected stats), with
        actor-ID references normalized and implicit old-image bindings made
        explicit; reverse only separately pinned owner Weapon identities."""
        data = self.load_baseline_fixture()
        owned = json.loads((ROOT / 'tools/tests/fixtures/test_lookup_owned_names_20260910.json').read_text())['routes']
        wrappers = json.loads((ROOT / 'tools/tests/fixtures/shared_owner_wrappers_20260910.json').read_text())['routes']
        for old, new in sorted(RENAME.items()):
            with self.subTest(actor=f"{old} -> {new}"):
                before = inject(old, unify(data["actors"][old]))
                after = unify(node_form(self.rules.resolve(new)))
                reverse = {current: previous for previous, current in owned.get(new, {}).items()}
                reverse.update({current: previous for previous, current in wrappers.get(new, {}).items()})
                for key, value in after.items():
                    if key.split('@')[0] == 'Armament' and isinstance(value, dict):
                        current = value.get('Weapon')
                        if current in reverse:
                            value['Weapon'] = reverse[current]
                self.assertEqual([], self.tree_diff(before, after))

    def test_sprite_bindings_use_old_lowercase_ids(self):
        for actor, spec in sorted(EXPECTED.items()):
            with self.subTest(actor=actor):
                self.assertEqual(spec["image"], self.rules.resolve(actor).get("RenderSprites", "Image"))

    def test_sequence_namespaces_unchanged(self):
        for _, new_id in sorted(RENAME.items()):
            image = self.rules.resolve(new_id).get("RenderSprites", "Image")
            with self.subTest(sequence=image):
                self.assertIsNotNone(self.rules.sequence_image(image))

    def test_no_forbidden_image_value_uses_new_ids(self):
        offenders = forbidden_image_offenders(
            p for p in sorted((ROOT / "mods/cameo").rglob("*.yaml"))
            if "engine" not in p.parts)
        self.assertEqual([], offenders)

    def test_forbidden_image_check_flags_indented_new_ids(self):
        """Negative fixture: the scanner must catch a NEW id written as a
        tab-indented RenderSprites Image child (the common yaml shape), and
        must keep accepting the preserved old-id bindings."""
        with tempfile.TemporaryDirectory() as tmp:
            p = pathlib.Path(tmp) / "naval.yaml"
            p.write_text(
                "td_gdi_missileboat:\n\tRenderSprites:\n\t\tImage: td_gdi_supercarrier\n",
                encoding="utf-8",
            )
            self.assertEqual([str(p)], forbidden_image_offenders([p]))
            p.write_text(
                "td_gdi_missileboat:\n\tRenderSprites:\n\t\tImage: cncpt\n",
                encoding="utf-8",
            )
            self.assertEqual([], forbidden_image_offenders([p]))

    def test_production_prerequisites_resolve(self):
        for actor, spec in sorted(EXPECTED.items()):
            for token in [t.strip().lstrip("~!") for t in spec["prereq"].split(",") if t.strip()]:
                with self.subTest(actor=actor, prereq=token):
                    self.assertIsNotNone(self.rules.resolve(token), token)

    def test_carrier_daughter_actors_resolve(self):
        resolved = self.rules.resolve("td_gdi_supercarrier")
        master = resolved.child("CarrierMaster")
        self.assertIsNotNone(master)
        for name in {a.strip() for a in master.get("Actors").split(",")}:
            with self.subTest(daughter=name):
                self.assertIsNotNone(self.rules.resolve(name), name)

    def test_ai_naval_references_resolve(self):
        text = (ROOT / "mods/cameo/ai/ai.yaml").read_text(encoding="utf-8-sig")
        old_hits = OLD_ID_WORDS.findall(text)
        self.assertEqual([], old_hits, f"old actor ids retained in ai.yaml: {old_hits}")
        naval_types_ids = {"td_gdi_missileboat", "td_gdi_railgunbattleship",
                           "td_nod_attacksubmarine", "td_nod_ballisticmissilesubmarine",
                           "td_nod_lasercorvette"}
        lines = [line for line in text.splitlines() if "NavalUnitsTypes" in line]
        self.assertTrue(lines, "no NavalUnitsTypes lines found")
        for actor in sorted(naval_types_ids):
            hits = [line for line in lines if actor in line]
            self.assertEqual(len(lines), len(hits),
                             f"{actor} missing from some NavalUnitsTypes lines")
        for actor in naval_types_ids:
            self.assertIsNotNone(self.rules.resolve(actor), actor)

    def test_ai_unit_value_dictionaries_use_new_ids(self):
        text = (ROOT / "mods/cameo/ai/ai.yaml").read_text(encoding="utf-8-sig")
        for actor in ("td_gdi_missileboat", "td_gdi_railgunbattleship",
                      "td_nod_attacksubmarine", "td_nod_ballisticmissilesubmarine",
                      "td_nod_lasercorvette"):
            self.assertGreaterEqual(len(re.findall(rf"^\s+{actor}: \d+", text, re.M)), 1, actor)

    # Pre-existing broken placements (present at the rename baseline, untouched
    # by this rename): kept visible here so a NEW break still fails this test.
    PREEXISTING_MISSING = {"heavy_factory"}

    def test_affected_map_placements_resolve(self):
        loose = ROOT / "mods/cameo/maps/iris-ally-hb/map.yaml"
        for path, text, archive in (
            (loose, loose.read_text(encoding="utf-8-sig"), None),
            (ROOT / "mods/cameo/maps/thelake6people.oramap", None,
             ROOT / "mods/cameo/maps/thelake6people.oramap"),
        ):
            if archive is not None:
                with zipfile.ZipFile(archive) as zf:
                    text = zf.read("map.yaml").decode("utf-8-sig")
            nodes = {n.key: n for n in miniyaml.load_text(text, str(path))}
            old_hits = OLD_ID_WORDS.findall(text)
            self.assertEqual([], old_hits, f"old actor ids retained in {path}: {old_hits}")
            actors = nodes.get("Actors")
            self.assertIsNotNone(actors)
            for placement in actors.children:
                if placement.value.lower() in self.PREEXISTING_MISSING:
                    continue
                with self.subTest(map=path.name, placement=placement.key):
                    self.assertIsNotNone(self.rules.resolve(placement.value),
                                         f"{placement.key}: {placement.value}")
        lake = {n.key: n for n in miniyaml.load_text(
            zipfile.ZipFile(ROOT / "mods/cameo/maps/thelake6people.oramap").read("map.yaml").decode("utf-8-sig"),
            "thelake6people/map.yaml")}
        self.assertEqual("td_gdi_landingcraft", lake["Actors"].child("Actor723").value)

    def test_quoted_script_actor_ids_resolve(self):
        lua_paths = [
            ROOT / "mods/cameo/maps/iris-ally-hb/allyhb.lua",
            ROOT / "mods/cameo/maps/delivery/campaign.lua",
            ROOT / "mods/cameo/maps/deliverycoop/campaign.lua",
        ]
        text = "\n".join(p.read_text(encoding="utf-8-sig") for p in lua_paths)
        self.assertEqual([], OLD_ID_WORDS.findall(text), "old actor ids in script literals")
        self.assertIsNotNone(self.rules.resolve("td_gdi_landingcraft"))
        self.assertGreaterEqual(text.count('"td_gdi_landingcraft"'), 4,
                                "expected four quoted landing-craft script references")


if __name__ == "__main__":
    unittest.main()
