# Projectile travel comparison

This is an additional comparison axis. It does not modify nominal DPS votes or
apply projectile speeds to Cameo. The requested all-source comparison is unfinished.

`projectile_travel_evidence.json` currently contains 598 weapon records from the
five pinned OpenRA peer corpora: 190 nominal Bullet/BulletCA records, 183 first-update instant records, five
constructor-impact records and 220 explicitly unresolved records. It also contains
343 current Cameo armament weapons: 124 bullets, 122 instant weapons, two source
impacts, 94 unresolved missiles/bombs and one targeting-only entry with no projectile. These are weapon records, not independent
source votes or a completion percentage for the four-faction roster.

The reference map exposes each source actor's slots, including conditions. It does
not sum mutually exclusive slots. No matching record is shown as unavailable.

## Reviewed calculation

The fixed endpoint separation is 4096 world units (four cells), with no scatter,
blockers or projectile speed modifiers. Samples outside the authored weapon range
are marked; they are mathematical comparisons, not legal firing scenarios.

For ordinary `Bullet`, both reviewed engine versions calculate the interpolation
length as `max(integer_distance / integer_speed, 1)`. The first projectile update
uses interpolation position zero, and the impact check compares `ticks++` with
that length. Thus the number of projectile update calls is `length + 1`.
For a two-value speed interval, the engine's random upper bound is excluded.
Bouncing bullets are not modeled here.

For `InstantHit`, supported laser/tesla/railgun/radiation beams and Cameo fake-bullet
guns, the first impact opportunity occurs on the first projectile update. CA
ElectricBolt instead impacts during construction, before any projectile update.
Beam damage durations of zero suppress impact; visual duration is not travel time.
Later repeated impacts remain a separate weapon-rate concern.

For `InstantHit`, impact occurs on its first projectile update. This is distinct
from zero elapsed firing-order latency. Warhead delays, firing animation, network
order latency and damage application scheduling are outside this measurement.

Example: both CA and OpenRA RA `25mm` declare Speed 853. At four cells each has
four interpolation intervals and five projectile update calls. This does not
make their weapon damage, cadence, or total combat behavior identical.

Current Cameo streak-enabled Bullet uses ceiling division for interpolation
length, unlike the reference engines. For Speed 853 over four cells this gives
six projectile updates instead of five. The local source hashes are bound in
`cameo_projectile_engine_review.json`; this is not a claim about the built DLL.
Cameo fake-bullet speed is shown separately because it affects cosmetics without
delaying damage. InstantExplode impacts at the firing source, not the sampled
destination. Entries with no authored armament projectile are explicitly N/A.

Seconds depend on the chosen game speed and on the event used as time zero.
The source GameSpeeds declarations are retained: the five peer mods and Cameo
all declare 40 ms/update at their default speed, but actual lobby settings were
not observed. The current artifact reports update counts, without treating those
counts as a fire-order-to-damage stopwatch measurement.

## Provenance and remaining work

`tools/reference/projectile_evidence.py` reuses the manifest-aware MiniYAML
resolver and verifies both the checkout commit and complete input digest against
the selected immutable peer corpus. It checks that source inputs remain unchanged
across extraction. Existing corpora and frozen Cameo baselines are not regenerated.

The JSON records the matching source commits, declaration-file hashes and reviewed
engine source hashes. CA uses its pinned `ca-engine/1.09`; ordinary OpenRA peers use
`bbd36d9e6a2d7f0d3b24f102858af6dc8caf8a78`. Custom CA source can be read from its Git
objects even when the working checkout is sparse.

Guided missiles and custom beams still need their own movement/impact models.
Do not approximate their real travel using distance divided by maximum speed and
present that as an engine result. Acceleration, launch angle, cruise altitude,
turn rate, target movement and repeated impacts can matter.

DTA travel and unmodeled guided/bomb/other classes remain outstanding. In particular,
OpenTS source includes ballistic speed initialization from range and gravity,
and a distinct missile launch/acceleration phase. Its applicability to the supplied
DTA build is not established; raw INI Speed values must not be presented as a
verified DTA travel calculation. The supplied DTA Rules and Enhance files now pass generated parent-key closure
checks; see `dta_preprocessing_evidence.json`. This resolves the earlier blanket
BaseSection warning, while exact runtime behavior remains unverified.

The combined artifact contains 1,064 weapon records: 598 peer OpenRA, 343 Cameo
and 123 DTA. Timing models cover 624 records; this is not a completion percentage.
DTA's 63 decoded motion parameter records expose engine-unit conversions and
ballistic initialization constraints, without certifying arrival times or the
installed DTA frame period. Guided missiles retain reviewed launch speed and
acceleration parameters where supported; these are not travel-time predictions.

Eight focused tests in `tools/tests/test_projectile_travel.py` cover interpolation
tick ordering, integer truncation/minimum duration, random upper bounds and the
distinctions between instant hits and unsupported guided projectiles, constructor
impacts, visual beam duration, disabled impacts, Cameo streak rounding and
cosmetic tracer speed. These are
static model checks, not in-game validation. One separate DTA decoding test covers
the integer Speed conversion and its limits.
