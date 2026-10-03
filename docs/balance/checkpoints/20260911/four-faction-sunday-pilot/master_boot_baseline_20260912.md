# Master startup baseline — 12 September 2026

This receipt records maintainer-provided startup evidence from AedisToru. It is
not a Codex build, does not certify the draft candidate, and does not replace
the representative Sunday gameplay scenarios.

## Evidence supplied

- Checkout: dedicated clean `master-boot-test` worktree.
- Commit: `ae02eedc0`.
- Fresh C# build: 0 errors.
- Launch: menu reached.
- `perf.log`: one `MenuPostProcessEffect.PostWorldLoaded` marker from this run;
  the check observed zero hits before launch and one afterward.
- New exception logs after the cutoff: 0.
- Process was stopped after the startup check.

## Interpretation

This establishes a clean master startup baseline for the Sunday package. It
does not establish target behavior, promotion/cargo behavior, player balance,
or runtime equivalence for draft PR #345. The draft branch is still static
review evidence until Blackrobe authorizes its exact build and launch.

The ordinary Aedis checkout must not be used for packaging: it was reported as
branch `devin/aurora/naming-ra1_allies`, 157 commits behind master and 8 ahead,
with 364 dirty files and a four-day-old `engine/bin/OpenRA.Mods.Cameo.dll`.
That state is preserved as live work and was not touched.
