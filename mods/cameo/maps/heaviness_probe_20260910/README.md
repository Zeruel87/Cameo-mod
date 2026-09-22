# CannonAP runtime probe

Launch with `Launch.Map=heaviness_probe_20260910` in the isolated worktree.
Twenty-four invisible, stationary shooters fire once at independent one-million-HP
targets. Three use legacy Light/Medium/Heavy templates against Medium armor;
three use the shared continuous base at Heaviness 0/1000/2000 against Medium;
three repeat those shared weapons against Shield armor. Lua prints damage events,
health loss and exact expected totals to lua.log. Three additional lanes use the
actual Forgotten Tank Killer, Warrior Tank and Broken Warrior Tank Turret weapons
against Medium armor, with only reload extended to isolate one shot.
Six additional old/new pairs measure the Freedom elite percentage cutoff at
enemy distances0/16/32/33 and allied distances16/17. Their test-only targetable
offsets supply exact integer distances; positional InstantHit impacts exercise
the spatial path rather than the direct-Actor bypass.
The script stops shooters at tick 100. No interaction is required.

This isolates real runtime damage, not visual behavior, splash at nonzero distance,
matchup balance, shield-pool absorption/depletion, veterancy, or pricing. Legacy and continuous profiles are
intentionally different; equality between lanes is not the pass criterion.
The script requires every lane to hit and every measured total to match its
independently calculated expectation (`all_lanes_hit=true all_expected=true`).
Terrain and preview are reused from the existing TD GDI/Nod balance-test map.

## Forgotten follow-up, 10 September 2026

The actual Bullet projectiles produced exactly 40800, 54400 and 65280 damage:
30000/40000/48000 authored damage times the shared h0 Medium coefficient 136%.
Each produced one flat event and no percentage event. All nine original control
lanes also retained their exact expectations. Peak sampled system RAM was65.34%;
the owned game process was closed and no new exception log appeared. This proves
the selected direct-hit runtime path, not whole-unit matchup balance or upgrades.

## Verified checkpoint, 10 September 2026

The corrected probe produced two damage events per lane and these exact totals:
legacy Light 3860, Medium 4560, Heavy 4660; continuous h=0 4120, h=1 4440,
h=2 5160. All matched the effective-profile model. Peak sampled system RAM was
69.26%; the owned game process was closed afterward. This checkpoint uses the
endpoint-based percentage implementation, not the later proposed shared-table mode.

Earlier setup attempts did not establish damage parity: two had no visible targets,
one failed map rule loading because this engine lacks AlwaysVisibleInfo (then failed
default spawn assignment), and one fell back to default rules and timed out. The
final map uses the verified HiddenUnderShroud trait with explicit relationships.

## Shared-mode calculation and measured checkpoint, 04:11 Jakarta

The probe lanes ProbeH0/H1000/H2000 now inherit `^Warhead_CannonAP` in the
SHARED-PROFILE mode (`HeavinessMode: SharedVersus`, `PercentageScale: 2000`).
The flat component is unchanged by the mode: the base table's belled Medium row
is 136 / 132 / 138 at h = 0 / 1000 / 2000, so the flats stay exactly the
verified checkpoint values 2720 / 2640 / 2760. The percentage component is the
h/2-scaled combined fraction — Damage 2000 x Scale 2000 x h / 400000000, ONE
half-up rounding, h = 1000 -> TEN basis-point units (0.10% of max HP before
Versus), h = 2000 -> TWENTY units — which on the 1,000,000-HP target is
1000 / 2000 HP before the shared table's Medium row, hence:

| lane | flat | percentage | expected and measured total |
|---|---:|---:|---:|
| h = 0   | 2720 | 0             | **2720** |
| h = 1   | 2640 | 1000 x 132% = 1320 | **3960** |
| h = 2   | 2760 | 2000 x 138% = 2760 | **5520** |
| Shield h = 0 | 2880 | 0 | **2880** |
| Shield h = 1 | 4320 | 1000 x 216% = 2160 | **6480** |
| Shield h = 2 | 5760 | 2000 x 288% = 5760 | **11520** |

The h = 0 lane MUST read zero percentage damage even though the flat Shield
coefficient floor is (2000 + h) / 2000 there (the Shield row scales to
144 / 216 / 288 — that row is not the Medium row these lanes hit). The legacy
lanes are UNAFFECTED by the mode and stay exactly 3860 / 4560 / 4660 — their
resolved template nodes are byte-identical Legacy-mode warheads.
The rebuilt game produced every expected total exactly, including unchanged legacy
controls 3860/4560/4660. h=0 produced only one flat damage event; other lanes had
separate flat and percentage events. Peak sampled system RAM was76.39%; the owned
game process closed afterward. No new exception log was produced. This is measured
shared-mode direct-hit evidence, separate from the historical endpoint run above.
The loaded Cameo DLL had SHA256
`79FB7B6826E2A1F118883F1EDDA1CE0418446ED49561B5E2B521F89013B301A1`;
the new validation marker was verified in its UTF-16 bytes before launch.
