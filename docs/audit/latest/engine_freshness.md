# audit_engine_freshness — Cameo's engine vs the upstreams it tracks

| | |
|---|---|
| `mod.config` pins | `d5d8b2a6853bff3b5a00cc5db7d86b03d4f30684` |
| `engine/VERSION` (what is built) | `d5d8b2a6853bff3b5a00cc5db7d86b03d4f30684` |

Clone: `C:\Users\AedisToru\Documents\GitHub\cameo-engine`

| upstream | ref last seen | commits it has that we lack | what it is |
|---|---|--:|---|
| OpenRA bleed | `upstream/bleed` @ 2026-09-25 | 0 | the engine everything descends from |
| MustaphaTR rv-engine | `mtr/rv-engine` @ 2026-07-25 | 8 | our direct parent branch; Generals Alpha pins its tip |

⚠ **The ref dates above are that commit's own date, NOT when the clone last fetched.** A number here is only as fresh as the last `git -C <clone> fetch upstream mtr --no-tags`.

### Behind MustaphaTR rv-engine by 8 commits

```
40065d3e58 2026-07-25 Mustafa Alperen Seki | Try to fix ProductionQueue.Build chosing the wrong queue.
57d48afbbe 2026-07-23 Mustafa Alperen Seki | Style warning fixes.
6cbd098ed1 2026-07-23 Mustafa Alperen Seki | Update OpenRA.slnx
4cd5422b75 2026-07-12 Mustafa Alperen Seki | Check for the correct place for FluentReferences in SupportPowerInfo>Names.
793dd6c7ef 2026-07-12 Mustafa Alperen Seki | Remove unnecessary ISyncs in AS dll.
bc375399b2 2026-07-12 Mustafa Alperen Seki | This exists in downstream now.
ab443403df 2026-07-12 Mustafa Alperen Seki | Didn't wait for everything to copy.
edbd6b0e05 2026-07-12 Mustafa Alperen Seki | Post rebase mess.
```

_Informational: catching up is the `cameo-engine` pipeline in docs/LESSONS_LEARNED.md, and a maintainer decision._
