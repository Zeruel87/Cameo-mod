# Candidate runtime probe — 12 September 2026

## Candidate and build

- Candidate commit: `50962e6d5e000bdf47cf2b5377dbb74049ddb78a`
- Engine pin: `462fc1fc4bfc490c42b88b429670c7f0c64c7aca`
- DLL: `engine/bin/OpenRA.Mods.Cameo.dll`
- DLL SHA-256: `F33C1248C9085A0FDA9BE6ED5F4635EB5ACB861E58C11FC43D9F309EB02E5887`
- The active YAML startup-repair batch removed stale duplicate inheritance and
  invalid nested-removal nodes across 16 weapon files. Static checks report
  `invalid_top=0` and `invalid_fields=0`; all 2,995 existing weapon definitions
  resolve identically to the pre-repair tree except for the intentional
  projectile/effect-only `^AsianRA2MediumMissile` template.

## Probe

The existing `heaviness_probe_20260910` map was launched with the candidate DLL.
The Lua receipt completed with:

```text
HEAVINESS_PROBE_COMPLETED all_lanes_hit=true all_expected=true
```

Measured totals matched every expected value: legacy Light/Medium/Heavy
`3860/4560/4660`; shared Medium h0/h1000/h2000 `2720/3960/5520`; Shield
h0/h1000/h2000 `2880/6480/11520`; Forgotten follow-up lanes
`40800/54400/65280`; and Freedom boundary pairs `108000/81000/54000/0` for
enemy distances 0/16/32/33 plus `40500/0` for allied distances 16/17.

The owned OpenRA process was stopped after completion. No new exception log was
created during this successful run. This is direct-hit and boundary-path
runtime evidence for the probe lanes; it is not a whole-roster balance,
shield-pool, matchup, or playtest certification.
