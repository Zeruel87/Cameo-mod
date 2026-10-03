# FireShrapnel scenario receipt

**SCENARIO ONLY.** This receipt exposes recursive child emissions and explicit target-availability assumptions. It is not a price, DPS vote, armor result or gameplay recommendation.

## Coverage

- FireShrapnel weapons: **200**; bound weapon definitions: **110**; actor bindings: **160**.
- Reachable FireShrapnel edges: **369**; maximum observed chain depth: **5**.
- Target-mask statuses: `{'CUSTOM_TAG_REVIEW': 92, 'MATCH': 245, 'MISMATCH': 32}`.
- Direct payload statuses: `{'FLAT_ONLY': 30, 'FLAT_PLUS_PERCENTAGE_UNRESOLVED': 39, 'PERCENTAGE_COMPONENT_UNRESOLVED': 66, 'UNRESOLVED_CHANNEL': 65}`; percentage-limited roots: **170**.

## Scenarios

- Random-hit credit: **0.50** for an untargeted attempt.
- `abundant_targets`: unlimited eligible targets; aimed and fallback emissions are credited by the helper.
- `no_eligible_targets`: zero eligible actors; `ThrowWithoutTarget:false` contributes no child emission, while the default true remains a random-position scenario.
- Child `Burst` and `ReloadDelay` are not multiplied into an emission; the parent firing cycle remains outside this receipt.

## Review boundaries

- Parent, emitter and fragment masks, raw tokens and source locations are retained in the JSON.
- Flat damage is shown separately from percentage/folded channels; target HP, armor, falloff, geometry and status effects remain unresolved.
- No row authorizes repricing, YAML edits, Versus changes, runtime claims or publication.

Full per-weapon and per-edge evidence is in the paired JSON receipt.
