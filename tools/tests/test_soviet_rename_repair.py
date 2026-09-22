"""Focused resolved before/after regression for the Soviet actor-ID repair.

Baseline: dump_resolved --all taken BEFORE the repair (parent evidence,
exported to tools/tests/fixtures/soviet_rename_baseline_subset.json via the
34 changed pre-repair actor keys). After: the live worktree ruleset.

Every changed actor must resolve to exactly its pre-repair resolved payload,
except the authorized identity-mapping classes:
  - exact token renames of the 34 IDs (and only those) in references
    (prerequisites, conditions, repair lists, drop items, transforms, keys),
  - explicit old-id RenderSprites.Image bindings replacing a default
    actor-id lookup (image preservation),
  - the dog display repair (broken GenericName actor-ID literal) ONLY on
    the three dogs.
Old IDs must be absent, destinations must not collide, all new IDs exist,
and the Fluent message keys must follow the same identity mapping.
"""
import json
import pathlib
import re
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools/audit"))
import miniyaml
from owned_weapon_history import restore_chained_identity_fields

FIXTURE = ROOT / "tools/tests/fixtures/soviet_rename_baseline_subset.json"
RENAMES = {  # pre-repair key -> post-repair key
    "ra1_soviets_sovietconstructionyard": "ra1_soviets_constructionyard",
    "ra1_soviets_sovietbarracks": "ra1_soviets_barracks",
    "ra1_soviets_sovietorerefinery": "ra1_soviets_orerefinery",
    "ra1_soviets_sovietwarfactory": "ra1_soviets_warfactory",
    "ra1_soviets_sovietlargefactory": "ra1_soviets_largefactory",
    "ra1_soviets_sovietradardome": "ra1_soviets_radardome",
    "ra1_soviets_sovietairfield": "ra1_soviets_airfield",
    "ra1_soviets_soviettechcenter": "ra1_soviets_techcenter",
    "ra1_soviets_sovietservicedepot": "ra1_soviets_servicedepot",
    "ra1_soviets_sovietmissilesilo": "ra1_soviets_missilesilo",
    "ra1_soviets_sovietsamsite": "ra1_soviets_samsite",
    "ra1_soviets_actordogname": "ra1_soviets_dog",
    "ra1_soviets_sovietgrenadier": "ra1_soviets_grenadier",
    "ra1_soviets_sovietmortarsoldier": "ra1_soviets_mortarsoldier",
    "ra1_soviets_sovietrocketsoldier": "ra1_soviets_rocketsoldier",
    "ra1_soviets_sovietflamethrower": "ra1_soviets_flamethrower",
    "ra1_soviets_sovietheavyindustrialminer": "ra1_soviets_heavyindustrialminer",
    "ra1_soviets_sovietheavytank": "ra1_soviets_heavytank",
    "ra1_soviets_sovietmammothtank": "ra1_soviets_mammothtank",
    "ra1_soviets_doctrine_conscriptiondoctrine": "ra1_soviets_doctrine_conscription",
    "ra1_soviets_doctrine_industrialefficiencydoctrine":
        "ra1_soviets_doctrine_industrialefficiency",
    "ra1_soviets_doctrine_infernodoctrine": "ra1_soviets_doctrine_inferno",
    "ra1_soviets_doctrine_teslaandexperimentaltechdoctrine":
        "ra1_soviets_doctrine_teslaandexperimentaltech",
    "ra1_soviets_doctrine_heavyarmordoctrine": "ra1_soviets_doctrine_heavyarmor",
    "ra1_soviets_doctrine_nuclearwardoctrine": "ra1_soviets_doctrine_nuclearwar",
    "ra1_soviets_upgrade_shtoradefensesystemupgrade":
        "ra1_soviets_upgrade_shtoradefensesystem",
    "ra1_soviets_upgrade_hammertankupgrade": "ra1_soviets_upgrade_hammertank",
    "ra1_soviets_upgrade_heavyteslatankupgrade":
        "ra1_soviets_upgrade_heavyteslatank",
    "ra1_soviets_upgrade_kotinnucleartankupgrade":
        "ra1_soviets_upgrade_kotinnucleartank",
    "ra1_soviets_sovietoretruck": "ra1_soviets_oretruck",
    "ra1_soviets_sovietmobileconstructionvehicle":
        "ra1_soviets_mobileconstructionvehicle",
    "ra2_allies_attackdog": "ra2_allies_dog",
    "ra2_soviets_attackdog": "ra2_soviets_dog",
    "ra1_soviets_sovietmammothtank.colorpicker":
        "ra1_soviets_mammothtank.colorpicker",
}
DOG_ONLY = {"ra1_soviets_actordogname", "ra2_allies_attackdog", "ra2_soviets_attackdog"}

# Token-level translation of post-repair strings back onto pre-repair ids;
# longest first so compound ids (upgrades containing shorter ids) survive.
# Boundary guards prevent lossy substring hits inside compound ids
# (e.g. 'heavyindustrialminer' inside 'sovietheavyindustrialminer').
_RETRANSLATE = sorted(RENAMES.values(), key=len, reverse=True)
RENAMES_INV = {v.lower(): k for k, v in RENAMES.items()}
_TIME = re.compile(
    r"(?<![a-z0-9_])(" + "|".join(re.escape(d) for d in _RETRANSLATE) + r")(?![a-z0-9_])",
    re.IGNORECASE)


def translate(text):
    if not isinstance(text, str):
        return text
    return _TIME.sub(lambda m: RENAMES_INV[m.group(0).lower()], text)


ASSET_FIELDS = {"Image", "ImageByFullness", "Filename", "Icon", "SmallIcon",
                "MissileImage", "Sequence", "Palette", "PlayerPalette"}
IDENTITY_FIELDS = {
    "Actor", "Actors", "ActorTypes", "Types", "Type", "Units", "Unit",
    "Prerequisite", "Prerequisites", "Condition", "RequiresCondition",
    "PauseOnCondition", "Upgrades", "Produces", "ProducedActors", "IntoActor",
    "ReplacementActor", "TransformActors", "HarvesterTypes", "RefineryTypes",
    "McvTypes", "ConstructionYardTypes", "ConstructionMcvTypes", "McvFactoryTypes",
    "BuildingTypes", "NavalUnitsTypes", "InitialUnits", "InitialActor",
    "RepairActors", "DropItems",
}


def canonical(obj, field=None, identity=False):
    """Retranslate a resolved dump back onto pre-repair vocabulary."""
    # Actor IDs and asset IDs are different namespaces, even when their strings
    # happen to match. Keep the complete asset subtree outside normalization.
    if field in ASSET_FIELDS:
        return obj
    identity = identity or field in IDENTITY_FIELDS
    if isinstance(obj, dict):
        out = {}
        for k, v in obj.items():
            key = k if k == "__value" else translate(k)
            out[key] = canonical(v, k, identity)
        return out
    if identity:
        return translate(obj)
    if field in {"Name", "Description"} and isinstance(obj, str):
        # Only explicitly renamed Fluent references, not arbitrary display text.
        if any(obj in (name + ".name", name + ".description") for name in _RETRANSLATE):
            return translate(obj)
    return obj


class SovietRenameRepairTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rules = miniyaml.Ruleset(ROOT)
        cls.baseline = json.loads(FIXTURE.read_text(encoding="utf-8-sig"))

    def node_to_obj(self, node):
        if not node.children:
            return node.value
        obj = {}
        for c in sorted(node.children, key=lambda n: n.key):
            obj[c.key] = self.node_to_obj(c)
        if node.value:
            obj["__value"] = node.value
        return obj

    def test_inventory_exact(self):
        # 31 Soviet roots + 1 colorpicker variant + 2 RA2 dogs
        self.assertEqual(len(RENAMES), 34, "identity inventory drifted")

    def test_no_destination_collisions(self):
        seen = set()
        for new in RENAMES.values():
            self.assertNotIn(new.lower(), seen, "collision on " + new)
            seen.add(new.lower())

    def test_destinations_absent_from_complete_namespace(self):
        stub = ROOT / "tools/tests/fixtures/soviet_rename_baseline_allkeys.json"
        self.assertTrue(stub.exists(), "required baseline-key fixture missing")
        keys = {k.lower() for k in json.loads(stub.read_text(encoding="utf-8-sig"))}
        self.assertEqual(sorted(keys & {v.lower() for v in RENAMES.values()}), [])

    def test_old_ids_absent_all_new_exist(self):
        for old, new in RENAMES.items():
            self.assertIsNone(self.rules.resolve(old), f"old id {old} still defined")
            self.assertIsNotNone(self.rules.resolve(new), f"missing destination {new}")

    def test_image_field_sequence_keys_resolve(self):
        for new in RENAMES.values():
            node = self.rules.resolve(new)
            for child in node.children:
                if child.key.startswith("WithHarvesterSpriteBody") \
                        or child.key == "RenderSprites":
                    for leaf in child.children:
                        if leaf.key == "Image":
                            key = leaf.value.strip()
                            self.assertIsNotNone(
                                self.rules.sequence_image(key),
                                f"{new}.RenderSprites.Image -> missing sequence {key}")
                        if leaf.key == "ImageByFullness":
                            # every comma-separated entry, not only the first
                            for key in [s.strip() for s in leaf.value.split(",") if s.strip()]:
                                self.assertIsNotNone(
                                    self.rules.sequence_image(key),
                                    f"{new}.{child.key}.ImageByFullness entry "
                                    f"-> missing sequence {key}")

    def test_resolved_payload_equivalence(self):
        diffs_seen = []
        for old, new in RENAMES.items():
            before = canonical(self.baseline[old])
            after = canonical(restore_chained_identity_fields(self.node_to_obj(self.rules.resolve(new)),
                {'ra1_soviets_heavytank_105mmthermobaric': '105mmThermobaric'}))
            diffs = self._collect(before, after)
            diffs = self._authorize(diffs, old, new)
            diffs_seen += [(new,) + d for d in diffs]
        self.assertEqual(diffs_seen, [], "unexplained resolved differences")

    def _authorize(self, diffs, old, new):
        out = []
        for path, b, a in diffs:
            if path == ("RenderSprites", "Image"):
                # image preservation: the AFTER value must equal the exact
                # BEFORE effective image — explicit before image, else the
                # old actor-ID default. No unconditional pass-through.
                effective_before = b if b != "<missing>" else old
                if a == effective_before:
                    continue
                out.append((path, b, a))
                continue
            if path == ("Tooltip", "GenericName") and old in DOG_ONLY:
                if a == "Attack Dog":
                    continue
            if path == ("Armament", "Weapon") and old in DOG_ONLY:
                # exactly three DogJaw -> bite references, nothing else
                if b == "DogJaw" and a == f"{new}_bite":
                    continue
            if (old == "ra1_soviets_sovietsamsite"
                    and new == "ra1_soviets_samsite"
                    and path == ("Armament", "Weapon")
                    and b == "Nike" and a == "ra1_soviets_samsite_missile_AA"):
                # Later owner-only rename; its complete resolved weapon is
                # independently pinned by test_additional_owned_names.
                continue
            if (old == "ra1_soviets_sovietgrenadier"
                    and new == "ra1_soviets_grenadier"
                    and path in (("Armament", "Weapon"), ("Armament@GARRISONED", "Weapon"))
                    and b == "GrenadeRA" and a == "ra1_soviets_grenadier_grenade"):
                # Exact later owner identity; thermobaric upgrade slots excluded.
                continue
            out.append((path, b, a))
        return out

    def test_sam_weapon_authorization_is_exact(self):
        old, new = "ra1_soviets_sovietsamsite", "ra1_soviets_samsite"
        allowed = (("Armament", "Weapon"), "Nike", "ra1_soviets_samsite_missile_AA")
        self.assertEqual(self._authorize([allowed], old, new), [])
        for change in (
                (("Armament", "Weapon"), "OtherWeapon", allowed[2]),
                (("Armament", "Weapon"), "Nike", "OtherWeapon"),
                (("Armament@SECONDARY", "Weapon"), "Nike", allowed[2])):
            self.assertEqual(self._authorize([change], old, new), [change])
        self.assertEqual(self._authorize([allowed], "other_actor", new), [allowed])

    def test_grenadier_weapon_authorization_is_exact(self):
        old, new = "ra1_soviets_sovietgrenadier", "ra1_soviets_grenadier"
        for slot in ("Armament", "Armament@GARRISONED"):
            allowed = ((slot, "Weapon"), "GrenadeRA", new + "_grenade")
            self.assertEqual(self._authorize([allowed], old, new), [])
            self.assertEqual(self._authorize([allowed], "other_actor", new), [allowed])
            self.assertEqual(self._authorize([allowed], old, "other_actor"), [allowed])
        for change in (
                (("Armament@Upgrade", "Weapon"), "GrenadeRA", new + "_grenade"),
                (("Armament@UpgradeGARRISONED", "Weapon"), "GrenadeRA", new + "_grenade"),
                (("Armament", "Weapon"), "OtherWeapon", new + "_grenade"),
                (("Armament", "Weapon"), "GrenadeRA", "OtherWeapon")):
            self.assertEqual(self._authorize([change], old, new), [change])

    def test_image_authorization_is_exact(self):
        # negative test: an arbitrary RenderSprites.Image change must NOT
        # be normalized away by the authorizer
        self.assertEqual(
            self._authorize([(("RenderSprites", "Image"), "<missing>",
                              "some_other_sprite")],
                            "ra1_soviets_actordogname", "ra1_soviets_dog"),
            [(("RenderSprites", "Image"), "<missing>", "some_other_sprite")])
        kept = self._authorize([(("RenderSprites", "Image"),
                                 "ra1_soviets_sovietbarracks",
                                 "ra1_soviets_sovietairfield")],
                               "ra1_soviets_sovietbarracks",
                               "ra1_soviets_barracks")
        self.assertEqual(kept, [(("RenderSprites", "Image"),
                                 "ra1_soviets_sovietbarracks",
                                 "ra1_soviets_sovietairfield")],
                         "explicit before-image drift must stay visible")

    def test_translation_never_touches_asset_namespace(self):
        # A NEW actor ID is the dangerous case: unrestricted normalization
        # would turn this wrong image back into the valid OLD image.
        new_id = "ra1_soviets_barracks"
        for field in ASSET_FIELDS:
            obj = {"SomeTrait": {field: new_id}}
            self.assertEqual(canonical(obj), obj)
        # Compare at the trait level to exercise the same leaf path as live data.
        diffs = self._collect({"RenderSprites": {}},
                              canonical({"RenderSprites": {"Image": new_id}}))
        self.assertTrue(self._authorize(diffs, "ra1_soviets_sovietbarracks", new_id))
        self.assertEqual(canonical({"SoundTrait": {"Report": new_id}}),
                         {"SoundTrait": {"Report": new_id}})
        # substrings in other namespaces must survive canonical()
        for asset in ("ra1_soviets_sovietmammothtank_icon.shp",
                      "ra1_soviets_sovietheavyindustrialminer.shp",
                      "ra1_soviets_actordogname_ra1_soviets_attackdog_electdog.shp"):
            self.assertEqual(translate(asset), asset)

    def test_image_by_fullness_pinned(self):
        # the miner's ImageByFullness keeps its ORIGINAL (pre-repair) value
        before = canonical(self.baseline["ra1_soviets_sovietheavyindustrialminer"])
        after = canonical(self.node_to_obj(
            self.rules.resolve("ra1_soviets_heavyindustrialminer")))
        self.assertEqual(before["WithHarvesterSpriteBody"]["ImageByFullness"],
                         after["WithHarvesterSpriteBody"]["ImageByFullness"])

    def _collect(self, a, b, path=()):
        out = []
        if isinstance(a, dict) and isinstance(b, dict):
            for k in sorted(set(a) | set(b)):
                if k not in a:
                    if b[k] == "<missing>":
                        continue
                    out.append((path + (k,), "<missing>", b[k]))
                elif k not in b:
                    if a[k] == "<missing>":
                        continue
                    out.append((path + (k,), a[k], "<missing>"))
                else:
                    out.extend(self._collect(a[k], b[k], path + (k,)))
        elif a != b:
            out.append((path, a, b))
        return out

    def test_fluent_keys_follow_identity(self):
        text = (ROOT / "mods/cameo/fluent/rules/en.ftl").read_text(encoding="utf-8-sig")
        checked = 0
        for old, new in RENAMES.items():
            self.assertFalse(re.search(r"(?m)^" + re.escape(old) + r"\s*(\.|$| =)", text),
                             f"pre-repair Fluent key {old} still defined")
            if re.search(r"(?m)^" + re.escape(new) + r"\s*(\.| =)", text):
                count = len(re.findall(r"(?m)^" + re.escape(new) + r"\s*(\.| =)", text))
                self.assertEqual(count, 1, f"Fluent key {new} duplicated")
                checked += 1

    def test_dog_display_repair_shape(self):
        for new in ("ra1_soviets_dog", "ra2_allies_dog", "ra2_soviets_dog"):
            node = next(c for c in self.rules.resolve(new).children
                        if c.key == "Tooltip")
            got = {c.key: c.value for c in node.children}
            self.assertEqual(got.get("GenericName"), "Attack Dog",
                             f"{new} GenericName not the verified literal")
            # Name: verified Fluent key (RA1) or the accepted literal (RA2);
            # a raw actor id must never come back as the display name.
            self.assertIn(got.get("Name"), ("actor_dog.name", "Attack Dog"),
                          f"{new} Tooltip.Name is not a validated display name")


if __name__ == "__main__":
    unittest.main()
