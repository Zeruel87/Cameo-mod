# AI Raid mission gate

This fog-enabled fixture gives `HardBot` a reachable remembered enemy refinery
and two harvesters. A nearby bot construction vehicle provides the initial
legitimate sightline without replacing the attack army. The runtime gate asserts that a situation snapshot
publishes a Raid mission and that the squad manager subsequently forms a Rush
squad with a target assignment in one of those mission regions.

The gate does not assert a successful `FrozenActorLayer` assignment. A
remembered frozen target is not reproducibly retained through squad target
validation on this map; assignment telemetry records whether the observed
target was live or frozen.

Run `python tools/tests/ai_raid_gate.py` after moving the shared situation log
aside. Do not run this gate concurrently with the other AI runtime gates.
