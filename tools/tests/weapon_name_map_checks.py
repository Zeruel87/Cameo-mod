"""Shared bounded map scan for weapon-identity regressions."""
import re
import zipfile


def assert_owned_dependency_consumers(test, rules, routes):
    """Follow all resolved actor references, inheritance and nested weapon links."""
    keys = set(rules.weapons)
    owners = {weapon: set() for weapon in keys}

    def references(node):
        for child in node.children:
            yield from (value.strip() for value in child.value.split(',') if value.strip() in keys)
            yield from references(child)

    graph = {weapon: set(references(node)) for weapon, node in rules.weapons.items()}
    for actor in rules.actors:
        if not actor.startswith('^'):
            for weapon in references(rules.resolve(actor)):
                owners[weapon].add(actor)
    while True:
        count = sum(map(len, owners.values()))
        for weapon, dependencies in graph.items():
            for dependency in dependencies:
                owners[dependency].update(owners[weapon])
        if count == sum(map(len, owners.values())):
            break
    for actor, route in routes.items():
        for weapon in route.values():
            test.assertEqual(owners[weapon], {actor}, weapon)


def assert_owned_weapon_consumers(test, rules, routes):
    """Check concrete ownership and every raw active value, including abstracts."""
    owners = {new: actor for actor, route in routes.items() for new in route.values()}
    old = {name.casefold() for route in routes.values() for name in route}
    test.assertTrue(old, "Owner routes must not be empty")
    for actor in rules.actors:
        if actor.startswith('^'):
            continue
        for trait in rules.resolve(actor).children:
            name = trait.get('Weapon')
            test.assertNotIn((name or '').casefold(), old)
            if name in owners:
                test.assertEqual(actor, owners[name])

    def walk(node):
        test.assertFalse(old & {v.strip().casefold() for v in node.value.split(',')}, node.key)
        for child in node.children:
            walk(child)

    for node in list(rules.actors.values()) + list(rules.weapons.values()):
        walk(node)


def assert_no_old_weapon_names(test, root, names):
    names = tuple(names)
    test.assertTrue(names, "Weapon-name inventory must not be empty")
    pattern = re.compile(r'(?i)(?<![A-Za-z0-9_])(?:' + '|'.join(re.escape(n) for n in names) + r')(?![A-Za-z0-9_])')
    directory = root / 'mods/cameo/maps'
    maps = list(directory.rglob('*.oramap'))
    test.assertTrue(maps, "Expected bundled map archives")
    for path in maps:
        with zipfile.ZipFile(path) as archive:
            for entry in archive.infolist():
                if entry.filename.lower().endswith(('.yaml', '.lua')):
                    test.assertLessEqual(entry.file_size, 10_000_000)
                    test.assertIsNone(pattern.search(archive.read(entry).decode('utf-8-sig')), str(path))
    for path in directory.rglob('*'):
        if path.is_file() and path.suffix.lower() in ('.yaml', '.lua'):
            test.assertIsNone(pattern.search(path.read_text(encoding='utf-8-sig')), str(path))
