# AI squad-forming gate

Same skeleton as `ai_phase2_runtime_gate_20260913`, but the `hard` bot starts
with an eight-unit army — including `ts_nod_attackbuggy`, which carries two
`AttackBase`-derived traits (the multi-trait lookup that crashed #554) — facing
a defended `Player` base. Squads must form before tick 1200.

Run `python tools/tests/ai_squad_gate.py`. It asserts exit code 0, no new
`exception-*.log`, and `squad_count >= 1` in the appended
`cameo-ai-situations.jsonl` records.
