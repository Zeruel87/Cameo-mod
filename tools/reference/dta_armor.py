"""Resolve named DTA armor modifiers using reviewed Vinifera precedence.

This models supplied configuration, not an identification of the installed DLL.
Keep resolved coefficients separate from raw declared Versus evidence.
"""
from fractions import Fraction

VANILLA = ('none', 'wood', 'light', 'heavy', 'concrete')


def percent(value):
    value = str(value).strip()
    return Fraction(value[:-1]) if value.endswith('%') else Fraction(value) * 100


class ArmorResolver:
    def __init__(self, ini):
        self.ini = {name.lower(): {k.lower(): v for k, v in fields.items()}
                    for name, fields in ini.items()}
        if len(self.ini) != len(ini):
            raise ValueError('case-colliding sections')
        self.armors = list(dict.fromkeys((*VANILLA, *(
            v.lower() for v in self.ini.get('armortypes', {}).values()))))

    def resolve(self, warhead, armor, route=()):
        warhead, armor = warhead.lower(), armor.lower()
        if warhead not in self.ini or armor not in self.armors:
            raise ValueError('unknown warhead or armor')
        fields = self.ini[warhead]
        if fields.get('verses'):
            raise ValueError('positional Verses is outside this named-field adapter')
        key = 'modifier.' + armor
        if key in fields:
            return {'percent': float(percent(fields[key])),
                    'basis': 'warhead override', 'resolved_armor': armor,
                    'route': [*route, armor]}
        if armor in route:
            raise ValueError('BaseArmor cycle: ' + ' -> '.join((*route, armor)))
        definition = self.ini.get(armor, {})
        parent = definition.get('basearmor', '').strip().lower()
        if parent and parent != armor:
            return self.resolve(warhead, parent, (*route, armor))
        return {'percent': float(percent(definition.get('modifier', '100%'))),
                'basis': 'armor default' if 'modifier' in definition else 'engine armor default',
                'resolved_armor': armor, 'route': [*route, armor]}

    def profile(self, warhead):
        return {armor: self.resolve(warhead, armor) for armor in self.armors}
