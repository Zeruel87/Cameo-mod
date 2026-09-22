# TD Rocket Soldier playtest batch

This is the first applied slice of the classic-four reference programme. It is intentionally
limited to the GDI and Nod Rocket Soldiers because both have the same verified singleton baseline,
the same three role-paired reference weapons, and no unresolved charge or multi-armament state.
It does not sign off the full Rocket Trooper class or the wider classic-four candidate.

## Evidence and applied values

The immutable Cameo self-vote is bound by
`docs/reference/cameo_singleton_armament_self_votes_20260914.json`. Each actor receives one vote
from Combined Arms, DTA Enhanced, OpenRA Tiberian Dawn, and the frozen Cameo baseline. The three
peer weapons are `Dragon.TD`, `70mmMsl`, and `Rockets`; the actor-fold `RedEye` AA selection is not
used.

| Field | Previous | Applied | Unsnapped paired target |
|---|---:|---:|---:|
| HP | 9,000 | 15,000 | 14,580.660 |
| Speed | 50 | 45 | 45.333 |
| Self-heal step | 9 | 15 | derived from HP |
| Weapon range | 6,368 | 6,264 | 6,264.360 |
| Main damage | 18,000 | 16,341 | 16,341.255 |
| Reload | 63 | 56 | 55.651 |
| Burst | 1 | 1 | 1 |
| Cost | 300 | 420 | 422.748 formula price |

The applied weapon components produce `16,341 / 56 = 291.804` damage per tick, close to the
independent `294.238` DPS verifier. The separate actor cost projection is `433.157`; the batch uses
the existing Rocket Trooper formula on final snapped stats and its 10-credit grid, giving 420.

GDI's Advanced Missile Targeting clone receives the same scalars while retaining its projectile
behavior. Garrison slots follow the owned weapons. The `E3` map-import alias keeps its former
9,000 HP, 50 speed, 300 cost, self-heal 9, and shared `Rockets`/`RocketsAMT` weapons.

## Passenger-sum closure

Raising each soldier from 300 to 420 changes every valid authored full load that contains one.

| Carrier | Applied cost |
|---|---:|
| GDI APC | 1,640 |
| GDI Assault APC | 4,050 |
| GDI Chinook | 4,050 |
| GDI Humvee Mk. II | 820 |
| Nod Buggy Mk. II | 720 |

The Nod Chinook remains outside this Rocket Soldier batch, but its current
authored load is now valid at 3,853: the eight listed passengers resolve to a
full 11/11 weight load and the cost equals their passenger sum. No cargo field
is changed here.

The full derived-sidecar refresh is retained. Raising the two actors' HP shifts the shared
`shield_damage_share` context slightly, so untouched derived values can move by 0.01; the
69-artifact determinism check reproduces those bytes across separate hash seeds and time zones.
The refresh also repairs the already-authored UTF-8 name `NaxiWW2KübelwagenMachinegun` in the Naxis
sidecar. Raw gameplay-ledger changes remain confined to the two Tiberian Dawn faction ledgers.

## Playtest focus

- Compare GDI and Nod Rocket Soldiers against infantry, vehicles, and aircraft at factory state.
- Confirm GDI Advanced Missile Targeting changes delivery only and does not change the base scalar
  budget.
- Check that the increased durability and lower movement speed still leave rifle infantry able to
  screen them.
- Confirm each listed carrier still feels correctly priced for its full authored passenger load.
