# audit_family_uniqueness — 148 family templates (147 legacy level templates + 1 active level-less base(s))

Shape checks use authored implicit-range geometry, not heaviness-scaled runtime geometry.

  Heavy     47 distinct shapes   OK
  Light     48 distinct shapes   OK
  Medium    47 distinct shapes   OK
  Super      4 distinct shapes   OK
  Trace      1 distinct shapes   OK

  level-less bases (continuous heaviness):

      CannonAP       radius    120  100,0                              Shield 144

  RAW Shield duplicate groups — 2 (base/Medium compatibility is approved and stays visible):

      Shield    144  ->  CannonAP (^Warhead_CannonAP), CannonAP (^Warhead_CannonAP_Medium)
      Shield    155  ->  MissileThermobaric (^Warhead_MissileThermobaric_Light), Nuclear (^Warhead_Nuclear_Super)
          ⚠ DISTINCT legacy families share a Shield value — fewer than two NEW bases are involved; reported, not failed.

OK — no two families share both a radius and a curve at any level (bases incl.), and no distinct NEW family bases share a Shield value. Raw compatibility and legacy duplicates remain listed above.
