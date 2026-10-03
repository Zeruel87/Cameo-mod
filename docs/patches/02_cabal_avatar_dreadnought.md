# `cabal_avatar` → `^DreadnoughtTemplate`

**Maintainer ruling 2026-09-03:** *"Genuine dreadnought — move it"*.

⛔ **Delivered as a patch, not a commit: it is engine content and this session cannot boot-gate.**
CLAUDE.md rule 1 requires `launch-game.cmd` to reach the main menu with no new `exception-*.log`
before any yaml change lands. Apply on a machine that can boot:

```sh
git apply docs/patches/02_cabal_avatar_dreadnought.patch
# boot-gate, then commit the yaml
```

## Why — re-verified against the CORRECTED frontal test

⚠ The sweep that first flagged this unit used turret PRESENCE, which was the wrong test (see
`CLASS_STATUS_BOARD.md` §11). Re-checked against the attack trait, the case is stronger:

| | hp | speed | range | dmg | frontal |
|---|--:|--:|--:|--:|--:|
| **`cabal_avatar`** | **1,000,000** | **25** | 6,332 | **81,000** | **`AttackFrontal`**, no turret |
| `dreadnought` median (n=5) | 300,000 | 45 | 7,156 | 32,000 | **4/5 frontal** |
| `high_tech_tank` median (n=26) | 202,500 | 60 | 6,398 | 24,012 | **5/26 frontal** |

* **Mechanism:** `AttackFrontal` with no `Turreted` at all — the dreadnought class is 4/5 frontal,
  `high_tech_tank` is 81% **turreted**. On the discriminator that actually separates the two
  classes, the avatar is unambiguously a dreadnought.
* **Shape:** 3.3× the dreadnought median HP at **half** its speed and 2.5× its damage — heavy, slow,
  hard-hitting, which is the definition.
* **Not an epic:** it has no `BuildLimit` and an ordinary tech-gated prerequisite
  (`~cabal_mechfactory, cabal_techcenter, !cabal_promotion_widow`), so it is genuinely buildable and
  the epic exemption correctly does not catch it.

⚠ **One axis does not fit:** its range (6,332) is *below* both class medians. That is not a
counter-argument — `CLASS_STATUS_BOARD.md` §10 records that dreadnought range is a deliberate
playtest nerf and is not the class discriminator.

## Expected effect

`dreadnought` gains its heaviest member by a wide margin (1,000,000 vs a 300,000 median), which
**will move the class fit** — `anchor_readiness.py` should be re-run after the ledger refresh, and
the anchor re-read before the class is signed.
