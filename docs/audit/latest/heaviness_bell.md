# audit_heaviness_bell — would the continuous-heaviness bell invert any family?

DESIGN §12.0i: `LO` 0.667 (swing 1.50x), `sigma` 0.75, mu = (h + centre_of_mass) / 2, x-axis = one global 13-slot scale 0..2. Simulated at h = 0.0, 0.5, 1.0, 1.5, 2.0.

| | |
|---|--:|
| families measured | 50 |
| with NO gradient the bell could preserve | 2 |
| ladder ORDERINGS changed by the bell | 0 |
| weighted-mean drift beyond 1e-6 | 0 |

## Flat families — no gradient to preserve

§9.2 predicted SIX of these; four (Cryo, Railgun, Waveforce, Storm) have since been given real gradients, so the prediction is stale and only these remain. The bell cannot help a family with no gradient — they need real profiles authored (§9.4). Lower `INVERT_BASELINE` as that happens, never by widening the bell.

  Magic
  Sonic

WARN 2 flat families (ratchet 2) · 0 inversions (must be 0) · 0 mean drifts (must be 0)
Lower `INVERT_BASELINE` as flat families get real profiles; never raise it.
