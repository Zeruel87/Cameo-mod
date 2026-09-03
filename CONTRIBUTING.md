# Contributing

## Contributing to Cameo (this repository)

**Start here: [`docs/HANDOFF.md`](docs/HANDOFF.md)** — current state, the priority-ordered work
queue, and the rules that are actually enforced. Then:

| | |
|---|---|
| The hard rules, loaded every session | [`CLAUDE.md`](CLAUDE.md) |
| Traps that have already cost someone a day | [`docs/LESSONS_LEARNED.md`](docs/LESSONS_LEARNED.md) |
| Workflow, evidence rules, commit gate | [`docs/AGENT_WORKSPACE.md`](docs/AGENT_WORKSPACE.md) |
| Binding design contract (read before editing yaml) | [`docs/DESIGN.md`](docs/DESIGN.md) |
| Which document owns which topic | [`docs/README.md`](docs/README.md) |

Four things trip up every newcomer, so they are worth stating here:

1. **Boot-gate before you commit.** `launch-game.cmd` must reach the main menu — `perf.log`
   ending with `MenuPostProcessEffect.PostWorldLoaded`, and no new `exception-*.log` in
   `%APPDATA%/OpenRA/Logs`. Snapshot the log list *before* launching. A great many bug classes
   in this tree are invisible to yaml linting and visible only to the engine.
2. **Stage your files by name.** `git add <files>`, never `-A` or `.` — other contributors
   routinely have uncommitted work in this tree.
3. **Never hand-edit a balance number.** They flow through a pipeline
   (`extract_stats` → ledger → `apply_balance`), and `audit_balance_drift` goes red if yaml and
   ledger disagree. Commit the yaml and the ledger together.
4. **`engine/` is not part of this repository.** It is a `.gitignore`d build output with no
   `.git` of its own; edits there cannot be committed and are deleted by the next `make all`.
   The engine lives in a separate repo — see [`docs/HANDOFF.md`](docs/HANDOFF.md) §5.

Run the audit suite with `bash tools/audit/run_all.sh` (**bash only** — a PowerShell `>`
redirect writes UTF-16 and corrupts every report).

Bugs and crashes in the released mod: report them on
[Discord](https://discord.gg/Xn2eSpS).

---

## OpenRA Mod SDK Contributing Guidelines

_The section below is the upstream OpenRA Mod SDK's guidance, which covers the build scripts and
SDK infrastructure this repository is built on — not Cameo's own content._

Thank you for your interest in OpenRA, OpenRA modding, and the OpenRA Mod SDK.  OpenRA is an open source project, and our community members – you – are the driving force behind it.  There are many ways to contribute, from writing tutorials or blog posts, improving the documentation, submitting bug reports and feature requests or writing code which can be incorporated into OpenRA, the Mod SDK, or our other sub-projects.

Please note that this repository is specifically for the scripts and infrastructure used to develop and build mods; bugs and feature requests against OpenRA itself should be directed to [the main OpenRA/OpenRA repository](https://github.com/OpenRA/OpenRA).  If you do come across a bug with the Mod SDK, or would like to request a new feature, then please take a look at the issue tracker first to see if it has already been reported.

When developing new features, it is important to make sure that they work on all our supported platforms.  Right now, this means Windows >= 7 (with PowerShell >= 3), macOS >= 10.7, and Linux.  We would like to also support *BSD, but do not currently have a means to test this.

Some issues to be aware of include:
* Use http://www.shellcheck.net/ to confirm POSIX compatibility of *.sh scripts.
* Avoid non-standard gnu extensions to common Unix tools (e.g. the `-f` flag from GNU `readlink`)

While your pull-request is in review it will be helpful if you join IRC to discuss the changes.

See also the in-depth guide on [contributing](https://github.com/OpenRA/OpenRA/wiki/Contributing) on the main OpenRA project wiki.  Most of the content on this page also applies to the Mod SDK.