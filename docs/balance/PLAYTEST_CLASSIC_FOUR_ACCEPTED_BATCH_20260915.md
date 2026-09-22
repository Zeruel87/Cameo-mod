# Classic-four accepted balance batch — 2026-09-15

## Scope

This is the first broad gameplay application of the four-faction reference work.
The maintainer explicitly accepted the available numerical proposals as a
playtest gamble on 2026-09-15.

The batch applies 27 current reference-complete proposal rows, retains the newer
TD GDI/Nod Rocket Soldier values from PR #398, and adds the separately accepted
GDI Battle Tank and Mammoth Tank sample proposals. In total, 29 additional
actors receive live YAML changes:

- RA Allies: Artillery, Light Tank, Medium Tank, Rocket Soldier, Rifle Infantry,
  and Ranger.
- RA Soviets: V2, Tesla Tank, Grenadier, Shock Trooper, Heavy Tank, Rifle
  Infantry, and Rocket Soldier.
- TD GDI: Grenadier, Humvee, Battle Tank, Mammoth Tank, MLRS, and Minigunner.
- TD Nod: Artillery, SSM Launcher, Chemical Warrior, Flamethrower, Light Tank,
  Flame Tank, Recon Bike, Stealth Tank, Minigunner, and Buggy.

The other 122 routed/excluded rows have no complete numerical target. Accepting
their disposition means retaining their current gameplay values; this batch does
not invent replacements for air/naval classes, static defenses, economy units,
limited units, support actors, cargo chassis, or incomplete reference rows.

## Application rule

- HP is rounded to the 1,000-point grid; speed, weapon range and flat damage use
  their integer grids; prices use the 10-credit candidate grid.
- Existing targeting, armor relationships, cadence, burst timing, percentage
  damage, status effects and EMP effects are preserved.
- Actor-owned baseline damage is scaled to the accepted nominal DPS. Exclusive
  upgrade families retain the same proportional relationship.
- The GDI Battle Tank and Mammoth Tank retain their existing cannon/missile DPS
  split; the accepted actor total is distributed proportionally across both.
- The existing TD Rocket Soldier pair remains at the newer per-armament result
  from PR #398 instead of being replaced by the older actor-fold projection.
- Eleven valid authored-load carriers are repriced to the sum of their accepted
  passenger prices. The TD Nod Chinook is now also valid at 3,853: its eight
  authored passengers resolve to a full 11/11 weight load.

## Evidence

- `test_accepted_ra_allies_balance_batch.py`
- `test_accepted_ra_soviets_balance_batch.py`
- `test_accepted_td_gdi_balance_batch.py`
- `test_accepted_td_nod_balance_batch.py`
- `test_accepted_classic_four_cargo_prices.py`
- `test_td_rocket_soldier_playtest.py`

The focused balance/cargo contracts and armament-pairing tests pass. Fresh raw
and derived ledgers are committed with the YAML and report zero drift. The
upgrade audit reports no strictly weaker replacement introduced by the batch.
The final launcher check reached `MenuPostProcessEffect.PostWorldLoaded` with no
new `exception-*.log` files.

Known repository-wide generator/template and weapon-shape ratchet failures are
pre-existing baseline debt. They are outside this actor-owned application and
are not presented as passing gates.
