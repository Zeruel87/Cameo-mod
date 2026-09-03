# Mandatory recurring audits

Six code-health checks are mandatory on a cadence. The registry is
`docs/audit/periodic.json`; `tools/audit/audit_periodic_freshness.py` (last
step of `tools/audit/run_all.sh`) turns "we should re-run that sometime" into a
gate:

| state | condition | effect |
|---|---|---|
| ok | age <= cadence | — |
| DUE | cadence < age <= cadence + grace (7 d) | listed in the report |
| OVERDUE | age > cadence + grace | listed loudly; **exits 1 in the strict form** |
| BROKEN | the script or its evidence file is gone | **always exits 1**, including `--warn-only` |

**Two severities, on purpose (2026-08-11).** `run_all.sh` is the PER-COMMIT gate, so
it invokes this audit with `--warn-only`: a *calendar* fact ("a scheduled scan is
late") must never turn a commit red for a reason unrelated to that commit — that
ambushes whoever happens to be working the day the timer expires. BROKEN is
different: a registered script or evidence file is actually missing from the tree
right now, so it blocks unconditionally.

Enforce the calendar in a scheduled run (not the commit gate):

```sh
python tools/audit/audit_periodic_freshness.py     # no flag -> exit 1 when overdue
```

The *scripted* part of each track still runs on every `run_all.sh` — but as of the
**2026-08-24 maintainer ruling it is ADVISORY there and does not set the suite's exit code.**
Each script writes its full report and still exits 1 on its own findings, so a scheduled or CI
run may gate on one deliberately; the per-commit suite does not.

⛔ **Why the change.** These five were being run as per-commit gates. `test_coverage` alone drifted **223 -> 235 -> 249 ->
257 -> 270** untested modules against a baseline of 224 between 2026-08-16 and 2026-08-24, so
— and a scheduled scan's findings must not mix into the same signal as a defect in the commit being
made. That is the argument this file already made for `--warn-only`, applied one level down. The
cadence is still enforced, by the strict form above.

⚠ **This does NOT make the suite exit 0, and it was never meant to.** Eight further audits gate on
real content defects (`inherits`, `upgrades`, `sequences`, `fluent`, `basebuilder_crates`,
`buildable_order`, `weapon_suffixes`, `impact_glow_preservation`) — the bounded-bug backlog in
`HANDOFF.md` §3.3. The suite still exits 1, correctly. Nor is a green suite the commit gate:
CLAUDE.md's gate is booting to the main menu with no new `exception-*.log`.

⚠ Advisory is not permission to let them rot. The ratchets still only go down, and the calendar
still bites in the scheduled run.

The *periodic* run below is the wider pass that a script cannot do — network queries, the real
test suites, and human review of the report — and it is what `last_run` tracks.

Stamp a completed periodic run (never stamp without doing the steps):

```sh
python tools/audit/audit_periodic_freshness.py --record <id> --evidence <path-or-url>
```

⚠ **Not everything that guards the docs is on a cadence.** `audit_doc_claims.py` (numeric
claims) and `audit_doc_health.py` (structural defects: control characters, mojibake, broken
links and anchors, references to moved documents, duplicate DESIGN section ids) both run on
**every** `run_all.sh`, because both are cheap and both catch corruption rather than staleness.

Baselines live at the top of each script. Lowering a baseline after fixing
findings is the point; raising one needs a note in the commit message saying
why the debt was accepted.

---

## code-duplication

Cadence 30 d · `python tools/audit/audit_code_duplication.py`

1. Run the script (C1 python clones, C2 C# clones, C3 duplicated constant tables).
2. Pick at least one clone group and fold it into a shared helper —
   `tools/audit/scanning.py` (file walking), `tools/audit/miniyaml.py` (parsing),
   `tools/audit/report.py` (markdown). C3 groups are the cheapest wins.
3. Lower the baseline in the script to the new count and commit both.

## test-coverage

Cadence 30 d · `python tools/audit/audit_test_coverage.py`

1. Run the script (T1 NUnit floor, T2 python-test floor, T3 untested modules).
2. Run the real suites and paste the summary lines into the evidence file:
   ```sh
   dotnet test OpenRA.Mods.Cameo.Test/OpenRA.Mods.Cameo.Test.csproj -c Release
   python -m unittest discover -s tools/tests -t tools/tests
   ```
3. Add tests for at least one T3 module, then raise T1/T2 and lower T3.

## recent-changes-review

Cadence 14 d · `python tools/audit/audit_recent_changes.py --days 30`

1. Run the script: R1 balance yaml edited without the ledger, R2 audits not
   wired into `run_all.sh`, R3 commits without provenance, R4 engine/config
   changes needing a boot gate, R5 churn ranking.
2. Work the reviewer checklist at the end of the report against R5's files.
3. R1/R3 only block for commits on or after `ENFORCED_FROM` in the script;
   older findings are history. Move `ENFORCED_FROM` forward only after the
   window is clean.

## error-handling

Cadence 30 d · `python tools/audit/audit_error_handling.py`

1. Run the script (E1 bare except, E2 swallowed error, E3 `open()` without
   `encoding=`, E4 `subprocess` without `check=`).
2. Fix at least the E1/E2 findings in code touched since the last run — a
   swallowed exception in an audit means the audit silently under-reports.
3. Lower the baselines.

## security-scan

Cadence 14 d · `python tools/audit/audit_security.py`

1. Run the script (S1 credential shapes, S2 code execution from data, S3
   plaintext downloads, S4 unpinned actions, S5 unpinned NuGet, S6 installer
   download without a SHA).
2. The script is offline; the periodic run adds the advisory queries:
   ```sh
   dotnet list CameoMod.sln package --vulnerable --include-transitive
   dotnet list CameoMod.sln package --deprecated
   ```
3. Re-check that every content download still resolves over https and that its
   `SHA1` still matches what the mirror serves (mirrors die quietly —
   `openra.mirror.haffdata.com` was returning a 16-byte Cloudflare error page
   for all four music packages until 2026-08-10):
   ```sh
   curl -sSL -o /tmp/p.zip <url> && sha1sum /tmp/p.zip
   ```
4. Paste the results into the evidence file and stamp the run.

## armor-exposure

Cadence 30 d · `python tools/balance/armor_exposure.py`

Exposure is not a fixed property of an armor type — it is a property of the
WEAPON ROSTER, so it moves every time a weapon is added, retuned or repointed
onto a different `^Warhead_*` family. A number derived from it (the effective-HP
factor in the price formula) is therefore stale the moment the roster changes,
and stale in a direction nobody notices, because nothing else in the pipeline
reads `Versus` in aggregate.

1. Run the script; write the output to `docs/audit/latest/armor_exposure.md`.
2. Compare the `EXPOSURE` column with the previous run. A shift of more than
   ~10% on any armor means a weapon change moved the balance of the whole
   roster against that armor — worth understanding before it is priced on.
3. Sanity-check the two factors separately. **coverage** should only move when
   weapons gain or lose `ValidTargets` (the air classes sit near 45%, ground
   near 80%); **intensity** moves with every `Versus` edit. If coverage moved
   and no `ValidTargets` was touched, something is resolving differently.
4. Re-run it immediately after the W13 warhead rebuild lands, and again before
   any price factor is derived from it — the current numbers describe the
   profiles W13 replaces.
