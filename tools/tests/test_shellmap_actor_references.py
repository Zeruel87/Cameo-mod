"""Packaged shellmaps must not retain missing actor IDs after faction renames.

This validates placements and Soviet script literals, not full Lua execution.
Archive content goes through the shared MiniYAML parser, never a second parser.
"""
import pathlib
import re
import sys
import unittest
import zipfile

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools/audit"))
import miniyaml


def nodes(text, source):
    return {n.key: n for n in miniyaml.load_text(text, source)}


class ShellmapReferencesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rules = miniyaml.Ruleset(ROOT)
        cls.maps = []
        for path in sorted((ROOT / "mods/cameo/maps").glob("*.oramap")):
            with zipfile.ZipFile(path) as archive:
                if "map.yaml" not in archive.namelist():
                    continue
                data = archive.read("map.yaml").decode("utf-8-sig")
                meta = nodes(data, f"{path.name}/map.yaml")
                visibility = meta.get("Visibility")
                if visibility and "Shellmap" in visibility.value.split(", "):
                    cls.maps.append((path, meta))

    def test_all_packaged_shellmap_placed_actors_exist(self):
        self.assertTrue(self.maps, "no shellmaps inspected")
        for path, meta in self.maps:
            local = set()
            extra = meta.get("Rules")
            if extra:
                local.update(n.key.lower() for n in extra.children)
                # Same comma-separated file-list shape consumed by MiniYaml.Load.
                for name in filter(None, (s.strip() for s in extra.value.split(","))):
                    with zipfile.ZipFile(path) as archive:
                        self.assertIn(name, archive.namelist(),
                                      f"uninspected map rules file {path.name}/{name}")
                        if name in archive.namelist():
                            local.update(n.lower() for n in nodes(
                                archive.read(name).decode("utf-8-sig"), f"{path.name}/{name}"))
            for actor in meta.get("Actors", miniyaml.Node("Actors", "")).children:
                with self.subTest(map=path.name, placement=actor.key, actor=actor.value):
                    if actor.value.lower() not in local:
                        self.assertIsNotNone(self.rules.resolve(actor.value),
                                             f"missing actor {actor.value}")

    def test_soviet_script_actor_literals_resolve_after_rename(self):
        paths = {p for p, _ in self.maps} | {ROOT / "mods/cameo/maps/survival.oramap"}
        for path in sorted(paths):
            with zipfile.ZipFile(path) as archive:
                for name in archive.namelist():
                    if not name.endswith(".lua"):
                        continue
                    text = archive.read(name).decode("utf-8-sig")
                    for actor in sorted(set(re.findall(r'''["'](ra1_soviets_[a-z0-9_]+)["']''', text))):
                        with self.subTest(map=path.name, member=name, actor=actor):
                            self.assertIsNotNone(self.rules.resolve(actor))


if __name__ == "__main__":
    unittest.main()
