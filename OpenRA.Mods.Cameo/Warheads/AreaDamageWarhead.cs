#region Copyright & License Information
/*
 * Copyright 2015- OpenRA.Mods.AS Developers (see AUTHORS)
 * This file is a part of a third-party plugin for OpenRA, which is
 * free software. It is made available to you under the terms of the
 * GNU General Public License as published by the Free Software
 * Foundation. For more information, see COPYING.
 */
#endregion

using System;
using System.Collections.Generic;
using System.Collections.Immutable;
using System.Linq;
using OpenRA.Effects;
using OpenRA.GameRules;
using OpenRA.Mods.Cameo.Traits;
using OpenRA.Mods.Common;
using OpenRA.Mods.Common.Traits;
using OpenRA.Mods.Common.Warheads;
using OpenRA.Mods.D2k.Traits;
using OpenRA.Traits;

namespace OpenRA.Mods.Cameo.Warheads
{
	[Desc("Area-of-effect damage that can expand outward over several ticks (a shockwave or a",
		"damage-over-time cloud) and bakes in friendly fire (allies take reduced damage within a",
		"reduced radius). At defaults (Ticks: 1, MaxRadius: 0, no scheduling) it behaves exactly",
		"like SpreadDamage plus baked friendly fire. The authored Damage is the TOTAL dealt across",
		"ALL ticks, so the balance pipeline reads a single number. Replaces the SpreadDamage main",
		"warhead + its _FriendlyFire twin on the AoE families; the _Percentage and per-weapon",
		"_ExtraDamage warheads keep their own bespoke Versus and stay separate.")]
	public enum ArmorCombination
	{
		Multiply,
		Average,
		Lowest,
		Highest,
	}

	[Desc("How a warhead's CONTINUOUS-HEAVINESS scalar (Heaviness) parameterises its armor",
		"profiles. Legacy (default, today's behaviour): the folded percentage half keeps its",
		"own PercentageVersus / PercentageVersusLight/Heavy anchor tables. SharedVersus",
		"(the approved §12.0i shared profile, Aedis 2026-09-10 03:17): BOTH halves share",
		"the flat Versus's belled table — percentage tables and endpoints must be absent,",
		"the percentage magnitude follows Damage x PercentageScale x h with h/2, and the",
		"Shield row's coefficient scales once by (2000 + h) / 2000 (100% at h=0, 200% at",
		"h=2) while h = 0 keeps the flat profile with a ZERO percentage half. Requires an",
		"active Heaviness (0..2000).")]
	public enum HeavinessMode
	{
		Legacy,
		SharedVersus,
	}

	public class AreaDamageWarhead : DamageWarhead, IRulesetLoaded<WeaponInfo>
	{
		[Desc("How a victim's MULTIPLE enabled CLASS armors combine into one Versus value.",
			"⚠ This governs the CLASS armors only. A PLATING is a separate layer and always",
			"MULTIPLIES on top of the result (maintainer 2026-08-17: \"the hybrid armors ... should",
			"be averaged while the armor layer on top should be multiplied ... That gives both",
			"their own game mechanic\"). Two rules in one field, which is why the plating set is",
			"matched by NAME below.",
			"Only affects actors wearing more than one armor (armor-plated units and the legacy",
			"dual-armor cyborgs and droids) — over a single armor every rule returns that armor,",
			"which is why a SHIELDED unit is unaffected: its body armor is gated off while the",
			"shield holds, so only the Shield row is ever read (W21 R5).",
			"Average: the Cameo law. 40% and 30% -> 35%, so the two bodies meet in the middle —",
			"  anti-infantry fire is never useless against a dual-armor cyborg and AP fire is",
			"  never oppressive against one.",
			"Multiply: the ENGINE's rule, and the reason this field exists. 40% x 30% = 12%, so a",
			"  second armor does not average a weapon's profile, it SQUARES it — a 17:1 weapon",
			"  becomes ~289:1 against these units. Never use it for CLASS armors.",
			"Lowest / Highest: the unit is as tough as its best / worst protected aspect.",
			"⚠ Only warheads that ROUTE THROUGH AreaDamage obey this. The ~878 legacy warhead",
			"nodes still declaring inline Versus on SpreadDamage keep multiplying until they are",
			"retired onto ^Warhead_* templates.")]
		public readonly ArmorCombination MultiArmorCombination = ArmorCombination.Average;

		[Desc("Range between falloff steps.")]
		public readonly WDist Spread = new(43);

		[Desc("Damage percentage at each range step.")]
		public readonly ImmutableArray<int> Falloff = [100, 37, 14, 5, 0];

		[Desc("Ranges at which each Falloff step is defined. Overrides Spread.")]
		public readonly ImmutableArray<WDist> Range = default;

		[Desc("Controls the way damage is calculated. Possible values are 'HitShape',",
			"'ClosestTargetablePosition' and 'CenterPosition'.")]
		public readonly DamageCalculationType DamageCalculationType = DamageCalculationType.HitShape;

		[Desc("Number of damage applications. 1 = a single instant hit (identical to SpreadDamage).",
			">1 spreads the TOTAL Damage across that many applications (damage over time).")]
		public readonly int Ticks = 1;

		[Desc("Delay in engine ticks between each application. 0 = every tick lands instantly.")]
		public readonly int TickDelay = 0;

		[Desc("Inner radius of the FIRST ring, used only when MaxRadius is set (the shockwave origin).")]
		public readonly WDist MinRadius = WDist.Zero;

		[Desc("Outer radius of the FINAL ring. When 0 every tick covers the full Falloff range (a",
			"static DoT cloud); when set, the damaged radius grows from MinRadius to MaxRadius across",
			"the ticks (an expanding shockwave).")]
		public readonly WDist MaxRadius = WDist.Zero;

		[Desc("Percentage of Damage dealt to ALLIED actors (baked-in friendly fire; Cameo law: 50).",
			"0 disables friendly fire entirely (allies are never hit).")]
		public readonly int FriendlyFireDamage = 50;

		[Desc("Percentage of the tick radius within which allied actors can be hit (Cameo law: 50).")]
		public readonly int FriendlyFireSpread = 50;

		[Desc("FOLDED-IN PERCENTAGE HALF, in HUNDREDTHS of a 0.01%-unit of the victim's MAX",
			"HEALTH per 2000 flat Damage. 10000 reproduces the old convention of 1% per 2000 and",
			"is the per-family dial: a chemical family scales harder, a kinetic one softer,",
			"without touching a single weapon. 0 disables the percentage half entirely.",
			"This replaces the separate AreaDamagePercentage twin — one warhead, one Damage",
			"number inline, and the percentage follows from it instead of being hand-typed",
			"alongside and drifting.",
			"⚠ WHY HUNDREDTHS AND NOT WHOLE UNITS. A whole-unit dial cannot express the ratio",
			"some weapons already have: TSMechRailgunII needs exactly 2.5 and would round to 2,",
			"a 20% error on its percentage half. 47 weapons were rounding-limited that way. In",
			"hundredths every ratio in the tree lands exactly.")]
		public readonly int PercentageScale = 0;

		[Desc("The percentage half's radius as a PERCENTAGE of the main one (Cameo law: 50 —",
			"the same halving FriendlyFireSpread uses, and what 2381 of 2487 hand-typed twins",
			"already did).")]
		public readonly int PercentageSpread = 50;

		[Desc("Denominator the derived percentage is read against. 10000 = basis points (0.01%",
			"steps), which is what PercentageScale is expressed in.")]
		public readonly int PercentageDenominator = 10000;

		[Desc("Continuous heaviness scalar h, in THOUSANDTHS (-1 or omitted = disabled / today's",
			"behaviour, 0 = active h = 0.0, 1000 = h = 1.0, 2000 = h = 2.0). When disabled the",
			"warhead uses its authored Versus, Spread and Range verbatim; when active the profile",
			"is passed through the §12.0i bell at runtime once. Spread, explicit Range and",
			"MinRadius/MaxRadius scale linearly 2/3 -> 1 -> 4/3 as h goes 0 -> 1 -> 2 (Light/",
			"Medium/Heavy); Super and Trace are outside the currently ruled h range and are not",
			"yet reproduced.")]
		public readonly int Heaviness = -1;

		[Desc("How Heaviness parameterises the armor profiles. Legacy (default): the",
			"percentage half keeps its own anchored Endpoint tables. SharedVersus: the",
			"opt-in shared profile — the percentage half follows the SAME belled table",
			"as the flat half (percentage tables/endpoints must be absent), its",
			"magnitude is heavy-scaled by h/2 (h=0 -> 0x, h=2 -> 1x), and the flat",
			"Shield row's coefficient scales ONCE by (2000 + h) / 2000 while the",
			"percentage half still reads zero at h = 0. Requires an active Heaviness;")]
		public readonly HeavinessMode HeavinessMode = HeavinessMode.Legacy;

		[Desc("The percentage half's armor table at the h = 0 (Light) endpoint. Optional; when",
			"BOTH this and PercentageVersusHeavy are authored, each must carry exactly the key set",
			"of the explicit PercentageVersus (which is the h = 1 medium anchor), and the half's",
			"per-armor magnitude is interpolated piecewise L->M for h in [0,1] and M->H for h in",
			"[1,2] (round ties-even) BEFORE the bell runs once over the result. Requires an active",
			"Heaviness; endpoints on a disabled warhead are rejected.")]
		public readonly Dictionary<string, int> PercentageVersusLight = new();

		[Desc("The percentage half's armor table at the h = 2 (Heavy) endpoint. See",
			"PercentageVersusLight for the activation and key-set rules.")]
		public readonly Dictionary<string, int> PercentageVersusHeavy = new();

		[Desc("The percentage half's own armor table. EMPTY falls back to Versus, which is the",
			"common case; a family whose percentage half should favour different armor states",
			"its own here.")]
		public readonly Dictionary<string, int> PercentageVersus = new();

		[Desc("Also damage D2k concrete slabs, 1:1 with everything else the weapon does to",
			"concrete: slab damage = Damage x Versus[Concrete] / 100. There is deliberately NO",
			"scale knob (maintainer 2026-08-19: a wall, a building and a slab all take the same",
			"Concrete damage). Replaces the separate DamagesConcrete warhead — leaving one of",
			"those alongside this would hit the slab TWICE.")]
		public readonly bool DamagesConcrete = false;

		[Desc("Optional PhysicalState (e.g. Temperature, Corrosion) to change on hit, SCALED BY the damage",
			"this warhead deals (unlike ApplyPhysicalStateWarhead's fixed Amount). Empty = off.")]
		public readonly string PhysicalStateName = null;

		[Desc("PhysicalState change = damage dealt x this percentage (signed): 100 = full heat/corrosion,",
			"-100 = full cold, 50 = half. 0 disables. Put on the main + _Percentage warheads, NOT the",
			"_ExtraDamage chip, so the chip is excluded and the %-twin also feeds the meter.")]
		public readonly int PhysicalStateScale = 0;

		[Desc("Multiple PhysicalState changes on one warhead, {StateName: Scale%}, applied IN ADDITION to",
			"the single PhysicalStateName/Scale above. For a blend, e.g. Plasma: Temperature: 50, Corrosion: 50.")]
		public readonly Dictionary<string, int> PhysicalStates = new();

		[Desc("Drain the victim's Integrity ELECTRONICS pool by the damage this warhead deals x this",
			"percentage, SCALED exactly like PhysicalStateScale (auto-tracks the real post-armor/falloff",
			"damage, so no flat EMP number is hand-set). Cameo Tesla-content law: Tesla 100, Storm 50,",
			"Quantum 33 (Tesla-parents / total-parents). 0 = off. Put it on the main + _Percentage warheads,",
			"NOT the _ExtraDamage chip. Stack a flat AffectsIntegrity warhead on top for upgrade bonuses,",
			"or give the upgraded weapon a higher IntegrityScale so its bonus EMP scales too.")]
		public readonly int IntegrityScale = 0;

		[Desc("Relative damage weight per tick. Length must equal Ticks (omit for an even split).",
			"Weights are NORMALISED so the total across all ticks always equals the authored Damage,",
			"keeping the balance figure a single number. For the nuclear shockwave use a DECREASING",
			"profile (e.g. 5, 4, 3, 2, 1) together with MinRadius/MaxRadius: the first ring is small",
			"and hits hard, later rings are larger and weaker. An INCREASING profile builds up instead.")]
		public readonly ImmutableArray<int> TickDamage = default;

		WDist effectiveSpread;
		WDist effectiveMinRadius;
		WDist effectiveMaxRadius;
		ImmutableArray<WDist> effectiveRange;
		int tickDamageTotal;

		IReadOnlyDictionary<string, int> effectiveVersus;
		IReadOnlyDictionary<string, int> effectivePercentageVersus;

		// Whether this warhead's PRIMARY hit may use the folded-in percentage half. The
		// AreaDamagePercentage subclass is ITSELF a percentage weapon: it forbids the extra
		// folded hit, so the PercentageVersusLight/Heavy endpoints (which parameterise that
		// folded half) are meaningless on it and are rejected in its own validation hook.
		protected virtual bool SupportsPercentageBands => true;

		bool sharedMode;

		void IRulesetLoaded<WeaponInfo>.RulesetLoaded(Ruleset rules, WeaponInfo info)
		{
			if (PercentageDenominator <= 0)
				throw new YamlException("PercentageDenominator must be positive.");

			if (Heaviness < -1 || Heaviness > 2000)
				throw new YamlException(
					$"Heaviness must be -1 (disabled) or 0..2000 (thousandths of h), got {Heaviness}.");

			// THE SHARED-PROFILE MODE (approved Aedis 2026-09-10 03:17; independent
			// review follow-up 2026-09-10). Explicit opt-in; everything the mode
			// cannot express fails clear HERE, at rules load — not first on impact.
			// Item 1 (review): a numeric or otherwise undefined member parses through
			// FieldLoader/Enum, so the IsDefined check is the real rejection gate.
			if (!Enum.IsDefined(typeof(HeavinessMode), HeavinessMode))
				throw new YamlException(
					$"Unknown HeavinessMode '{HeavinessMode}': must be one of " +
					$"{HeavinessMode.Legacy} or {HeavinessMode.SharedVersus}.");
			sharedMode = HeavinessMode == HeavinessMode.SharedVersus;
			if (sharedMode)
			{
				if (Heaviness < 0)
					throw new YamlException(
						"HeavinessMode SharedVersus requires an active Heaviness (0..2000); " +
						"omitting Heaviness disables heaviness entirely.");
				if (PercentageVersus.Count > 0 || PercentageVersusLight.Count > 0 ||
					PercentageVersusHeavy.Count > 0)
					throw new YamlException(
						"HeavinessMode SharedVersus rejects PercentageVersus and the " +
						"PercentageVersusLight/Heavy endpoints: the percentage half follows " +
						"the SAME belled table as the flat half.");

				// Item 3 (review): the approved half-up formula is nonnegative —
				// a negative Damage, PercentageScale or Shield coefficient is a
				// configuration error even at h = 0 (where the percentage units
				// happen to be zero). All legacy paths are untouched.
				if (Damage < 0)
					throw new YamlException(
						$"HeavinessMode SharedVersus rejects a negative Damage ({Damage}); " +
						"the approved conversion is nonnegative.");
				if (PercentageScale < 0)
					throw new YamlException(
						$"HeavinessMode SharedVersus rejects a negative PercentageScale " +
						$"({PercentageScale}); the approved conversion is nonnegative.");
				if (Versus.TryGetValue("Shield", out var shield) && shield < 0)
					throw new YamlException(
						"HeavinessMode SharedVersus rejects a negative Shield coefficient " +
						$"({shield}); the approved (2000 + h) / 2000 scaling is nonnegative.");

				// Item 2 (review): the shared percentage conversion is computed and
				// validated AT RULES LOAD — an Int32-bound overflow must fail clear
				// here, not first on impact. h = 0 passes (zero units IS the approved
				// value), so no magnitude gate on the number itself.
				try
				{
					SharedFoldedPercentageUnits(Damage, PercentageScale, Heaviness);
				}
				catch (OverflowException)
				{
					throw new YamlException(
						"HeavinessMode SharedVersus: percentage units Damage " +
						$"{Damage} x PercentageScale {PercentageScale} x Heaviness " +
						$"{Heaviness} overflow Int32.");
				}
			}

			var bands = PercentageVersusLight.Count > 0 || PercentageVersusHeavy.Count > 0;
			if (Heaviness < 0 && bands)
				throw new YamlException(
					"PercentageVersusLight/Heavy endpoints require an active Heaviness (0..2000); " +
					"omitting Heaviness disables heaviness entirely.");

			// §12.0i — continuous heaviness. Heaviness = -1 (or omitted) keeps authored values verbatim.
			if (Heaviness >= 0)
			{
				var h = Heaviness / 1000.0;

				// Radius scale: linear interpolation of the existing LEVEL_RADIUS_SCALE points
				// Light h=0 -> 2/3, Medium h=1 -> 1, Heavy h=2 -> 4/3. Applied consistently to
				// Spread, explicit Range and MinRadius/MaxRadius via the bounded helper.
				// Super/Trace are outside the currently ruled h range and stay unhandled
				// until the maintainer rules them.
				effectiveSpread = new WDist(ScaledRadiusLength(Spread.Length, Heaviness));
				effectiveMinRadius = new WDist(ScaledRadiusLength(MinRadius.Length, Heaviness));
				effectiveMaxRadius = new WDist(ScaledRadiusLength(MaxRadius.Length, Heaviness));

				effectiveVersus = HeavinessBell.Transform(Versus, h);

				// THE SHARED-PROFILE BRANCH: the bell ran ONCE above over the flat
				// Versus; the Shield row's coefficient is then scaled ONCE by
				// (2000 + h) / 2000. The percentage half reads that SAME resulting
				// table by reference — never a second bell, never a second Shield
				// scaling, and no percentage tables of its own.
				if (sharedMode)
				{
					effectiveVersus = ScaleShieldCoefficient(effectiveVersus, Heaviness);
					effectivePercentageVersus = effectiveVersus;
				}
				// The percentage half's ADDITIVE PER-ARMOR BANDS: interpolate between the
				// authored anchor tables piecewise (L->M on h in [0,1], M->H on h in (1,2]),
				// round ties-even per armor, then pass the interpolated table through the
				// bell ONCE. PercentageScale itself stays the scalar dial it always was.
				// Gated on SupportsPercentageBands: the AreaDamagePercentage subclass carries
				// these FIELDS by inheritance but forbids the folded half it applies to, so
				// its branch must never compute with them (it rejects the endpoints in its
				// own ValidateFields).
				if (bands && SupportsPercentageBands)
				{
					if (PercentageVersusLight.Count == 0 || PercentageVersusHeavy.Count == 0)
						throw new YamlException(
							"PercentageVersusLight and PercentageVersusHeavy must both be set.");
					if (PercentageVersus.Count == 0)
						throw new YamlException(
							"PercentageVersusLight/Heavy require an explicit PercentageVersus " +
							"(the h=1 medium anchor).");
					if (!SameKeys(PercentageVersusLight, PercentageVersus) ||
						!SameKeys(PercentageVersusHeavy, PercentageVersus))
						throw new YamlException(
							"PercentageVersusLight/Heavy keys must match PercentageVersus exactly.");
					if (PercentageVersus.Any(kv => kv.Value < 0) ||
						PercentageVersusLight.Any(kv => kv.Value < 0) ||
						PercentageVersusHeavy.Any(kv => kv.Value < 0))
						throw new YamlException(
							"PercentageVersus anchor values must be non-negative.");

					var interpolated = InterpolatePercentageBands(
						PercentageVersusLight, PercentageVersus, PercentageVersusHeavy, Heaviness);
					effectivePercentageVersus = HeavinessBell.Transform(interpolated, h);
				}
				else
				{
					effectivePercentageVersus = PercentageVersus.Count > 0
						? HeavinessBell.Transform(PercentageVersus, h)
						: effectiveVersus;
				}
			}
			else
			{
				effectiveSpread = Spread;
				effectiveMinRadius = MinRadius;
				effectiveMaxRadius = MaxRadius;
				effectiveVersus = Versus;
				effectivePercentageVersus = PercentageVersus.Count > 0 ? PercentageVersus : Versus;
			}

			if (Range != null)
			{
				if (Range.Length != 1 && Range.Length != Falloff.Length)
					throw new YamlException("Number of range values must be 1 or equal to the number of Falloff values.");

				for (var i = 0; i < Range.Length - 1; i++)
					if (Range[i] > Range[i + 1])
						throw new YamlException("Range values must be specified in an increasing order.");

				effectiveRange = Range
					.Select(r => new WDist(ScaledRadiusLength(r.Length, Heaviness)))
					.ToImmutableArray();

				// ⚠ CONTROL-FLOW VERIFIED (review 2026-09-10): GetDamageFalloff USES a
				// duplicate segment only when it is the FIRST segment — the loop enters
				// segment i with span `outer - inner`; for i >= 2 entering implies
				// distance >= Range[i-1] while the segment is used only when
				// distance < Range[i], impossible for a duplicate, so later duplicates
				// are dynamically SKIPPED and harmless. Segment i = 1 is entered only
				// when `outer > distance`; a front at ZERO (0 == 0) never satisfies
				// `outer > distance` for any distance >= 0, so a zero front (e.g.
				// authored 0,1 truncating to 0,0) is HARMLESS and must NOT be rejected.
				// Reject only a POSITIVE collapsed front — authored strictly-increasing
				// positive radii truncating to an equal positive pair — which calls
				// int2.Lerp with span 0 for every in-range victim. Fail clear at load;
				// an already-collapsing authored Range keeps today's behaviour.
				if (Heaviness >= 0 && Range.Length >= 2 &&
					Range[0] < Range[1] &&
					effectiveRange[0] == effectiveRange[1] && effectiveRange[0].Length > 0)
					throw new YamlException(
						"Scaled Range front collapsed to a positive duplicate " +
						$"(authored {Range[0].Length} / {Range[1].Length}, scaled " +
						$"{effectiveRange[0].Length} / {effectiveRange[1].Length}).");
			}
			else
				effectiveRange = Exts.MakeArray(Falloff.Length, i => i * effectiveSpread).ToImmutableArray();

			if (TickDamage != null)
			{
				if (TickDamage.Length != Ticks)
					throw new YamlException("Number of TickDamage weights must equal Ticks.");

				tickDamageTotal = TickDamage.Sum();
			}

			ValidateFields();
		}

		[Desc("Subclass validation hook, called once the base fields are checked.")]
		protected virtual void ValidateFields() { }

		// THE ARMOR-PLATING LAYER (maintainer, 2026-08-16).
		//
		// A plating is a MUTUALLY EXCLUSIVE upgrade — a unit picks one — and while it is on, the
		// plating is what the shot actually hits. So it REPLACES the class armor rather than
		// combining with it: "shield active -> shield armor, armor plating active -> that plating's
		// armor type, otherwise -> the armor type from the unit class."
		//
		// ⚠ **Combining instead of replacing is what made an upgrade able to HURT you.** While
		// platings were averaged with the class armor, `effective = (class + plating) / 2` rose
		// above `class` whenever the plating row did — measured at 98 of 1152 cells, up to 1.84x
		// MORE damage, worst on heavy units because they are the ones with the low class rows.
		// Selection removes the whole failure mode: only one row is ever read.
		//
		// This is deliberately NOT the same as being strictly better. Each plating is strong against
		// one damage axis and WEAK against the next (the cycle: thermochemical -> kinetic -> blast
		// -> energy -> thermochemical), so picking one is a trade, not a free upgrade. That is only
		// safe BECAUSE selection replaced averaging: under averaging a "weak" row would have been an
		// unconditional penalty stacked on top of the class armor.
		//
		// `Shield` is absent here on purpose — it already does exactly this in yaml
		// (`Armor: RequiresCondition: !shielded` in defaults.yaml), and it sits ABOVE plating in the
		// layer stack, so its own condition takes it out of the running before this code runs.
		//
		// ⚠ Keep in step with `gen_weapon_template.PLATING_CYCLE`, which generates the columns.
		// A name here with no column would select an armor the warheads have no row for, which
		// `DamageVersus` answers with 100 — i.e. the plating would REMOVE the unit's armor.
		static readonly string[] PlatingArmors =
		{
			"HAZMAT",     // sealed / filtered envelope — vs fire, chemical, radiation
			"COMPOSITE",  // ceramic matrix + ERA       — vs kinetic penetrators AND shaped charges
			"BLAST",      // spall liner / V-hull       — vs HE, demolition, concussion
			"REFLECTOR",  // ablative / mirrored        — vs directed energy
			// The GENERIC plating: flat against everything, so it counters nothing and is
			// punished by nothing. Home for every non-branching "+armor" upgrade (Yuri scrap,
			// Forgotten junk armor, the StarCraft/Warcraft armor and carapace levels), which
			// were never designed with a counter-play identity.
			"ARMOR",
		};

		protected override int DamageVersus(Actor victim, HitShape shape, WarheadArgs args)
		{
			return VersusFrom(effectiveVersus, victim, shape);
		}

		/// <summary>
		/// The armor lookup, parameterised by TABLE. The flat half passes `Versus` and the
		/// folded-in percentage half passes `PercentageVersus`; sharing one body is deliberate,
		/// because the plating layer rule and the multi-armor combination must never differ
		/// between a weapon's two halves.
		/// </summary>
		int VersusFrom(IReadOnlyDictionary<string, int> table, Actor victim, HitShape shape)
		{
			if (table.Count == 0)
				return 100;

			// Same selection as the base: enabled armors this warhead has a Versus row for,
			// filtered by the hit shape's own armor restriction. Only the COMBINATION differs.
			var matched = victim.TraitsImplementing<Armor>()
				.Where(a => !a.IsTraitDisabled && a.Info.Type != null && table.ContainsKey(a.Info.Type) &&
					(shape.Info.ArmorTypes.IsEmpty || shape.Info.ArmorTypes.Contains(a.Info.Type)))
				.ToList();

			// A PLATING is a LAYER, not an armor class: it sits on top of whatever the unit already
			// is. If several are somehow active at once the most protective wins rather than an
			// average — stacking platings must never be worse than wearing one. (`X1` in
			// audit_plating_exclusivity keeps it to one in practice.)
			var plating = matched
				.Where(a => PlatingArmors.Contains(a.Info.Type))
				.Select(a => table[a.Info.Type])
				.ToList();

			var armor = matched
				.Where(a => !PlatingArmors.Contains(a.Info.Type))
				.Select(a => table[a.Info.Type])
				.ToList();

			// No matching class armor means no class modifier, exactly as the base's empty product
			// does — the plating (if any) then applies alone.
			var classRow = armor.Count == 0
				? 100
				: MultiArmorCombination switch
				{
					ArmorCombination.Average => armor.Sum() / armor.Count,
					ArmorCombination.Lowest => armor.Min(),
					ArmorCombination.Highest => armor.Max(),
					_ => Util.ApplyPercentageModifiers(100, armor),
				};

			// ⭐ THE LAYER RULE (maintainer 2026-08-17). The plating MULTIPLIES the class row
			// instead of REPLACING it. Selection erased the class armor outright, so installing an
			// upgrade switched off the unit-class ladder — a plated Heroic stopped being Heroic and
			// a Superheavy tank took the same damage as a Scout car wearing the same plate. Both
			// axes now stay live.
			//
			// Safe here in a way the engine's blanket Multiply is not: a plating row is a SHALLOW
			// modifier (35..106, mean 70), not a second full ladder, so the compounded spread is
			// 5.32:1 — inside the documented 2-8x band — where multiplying two CLASS ladders is
			// W20's squaring bug (40% x 30% = 12%). That is exactly why the class armors keep
			// combining by MultiArmorCombination above and only the layer multiplies.
			//
			// ⚠ Deliberately NO clamp at 100. The five cells that exceed it (Arrow/Concussion 106,
			// Prism 103, Bullet/Toxic 102) ARE the closed cycle's weaknesses; clamping would make
			// every plating a strict upgrade, which is the "free upgrade" the cycle exists to
			// prevent. A +6% penalty against your counter-weapon is a trade a player can read.
			return plating.Count > 0
				? classRow * plating.Min() / 100
				: classRow;
		}

		protected override void DoImpact(WPos pos, Actor firedBy, WarheadArgs args)
		{
			var world = firedBy.World;

			// The folded-in concrete half. ONCE per impact, not once per victim — a slab is
			// terrain, not an actor, so it is not in the victim loop at all. Damage is 1:1 with
			// what the weapon does to any other concrete (maintainer 2026-08-19: a wall, a
			// building and a slab all take the same Concrete damage), so it reads the same
			// Versus[Concrete] row and has no scale knob of its own.
			if (DamagesConcrete)
				HitConcrete(world, pos);

			for (var tick = 0; tick < Ticks; tick++)
			{
				// Copy the loop variable so each scheduled lambda captures its own tick index.
				var t = tick;
				if (t == 0 || TickDelay <= 0)
					ApplyRing(world, pos, firedBy, args, t);
				else
					world.AddFrameEndTask(w => w.Add(new DelayedAction(t * TickDelay, () => ApplyRing(world, pos, firedBy, args, t))));
			}
		}

		void HitConcrete(World world, WPos pos)
		{
			var layer = world.WorldActor.TraitOrDefault<BuildableTerrainLayer>();
			if (layer == null)
				return;                                  // no concrete on this map — nothing to hit

			// Versus has no Concrete row on most families; 100 then means "full damage", the same
			// default every other armor lookup uses.
			var slab = effectiveVersus.TryGetValue("Concrete", out var v) ? Damage * v / 100 : Damage;
			if (slab > 0)
				layer.HitTile(world.Map.CellContaining(pos), slab);
		}

		void ApplyRing(World world, WPos pos, Actor firedBy, WarheadArgs args, int tick)
		{
			// Expanding shockwave: grow the damaged radius from MinRadius to MaxRadius across the ticks.
			// Static DoT cloud (MaxRadius == 0): every tick covers the full Falloff range.
			// The BRANCH decision reads the AUTHORED MaxRadius: a tiny positive radius that
			// scales/truncates to zero must stay a shockwave (rings at zero), not degrade
			// into a static cloud. The interpolated endpoints are the effective radii.
			var outer = effectiveRange[^1];
			if (MaxRadius.Length > 0 && Ticks > 1)
				outer = new WDist(effectiveMinRadius.Length +
					(effectiveMaxRadius.Length - effectiveMinRadius.Length) * (tick + 1) / Ticks);

			// The authored Damage is the TOTAL across all ticks. Split it by the per-tick weights
			// (TickDamage) when given, otherwise evenly. Normalised so the ticks always sum to Damage.
			var perTickModifier = Ticks > 1 ? 100 / Ticks : 100;
			if (TickDamage != null && tickDamageTotal > 0)
				perTickModifier = 100 * TickDamage[tick] / tickDamageTotal;

			foreach (var victim in world.FindActorsOnCircle(pos, outer))
			{
				if (!IsValidAgainst(victim, firedBy))
					continue;

				var isAlly = victim.Owner.RelationshipWith(firedBy.Owner) == PlayerRelationship.Ally;
				if (isAlly && FriendlyFireDamage <= 0)
					continue;

				// Friendly fire covers only a fraction of the tick radius.
				var victimOuter = isAlly ? new WDist(outer.Length * FriendlyFireSpread / 100) : outer;

				// PERF: Avoid using TraitsImplementing<HitShape> that needs to find the actor in the trait dictionary.
				HitShape closestActiveShape = null;
				var closestDistance = int.MaxValue;

				foreach (var targetPos in victim.EnabledTargetablePositions)
				{
					if (targetPos is HitShape h)
					{
						var distance = h.DistanceFromEdge(victim, pos).Length;
						if (distance < closestDistance)
						{
							closestDistance = distance;
							closestActiveShape = h;
						}
					}
				}

				// Cannot be damaged without an active HitShape.
				if (closestActiveShape == null)
					continue;

				var falloffDistance = 0;
				switch (DamageCalculationType)
				{
					case DamageCalculationType.HitShape:
						falloffDistance = closestDistance;
						break;
					case DamageCalculationType.ClosestTargetablePosition:
						falloffDistance = victim.GetTargetablePositions().Min(x => (x - pos).Length);
						break;
					case DamageCalculationType.CenterPosition:
						falloffDistance = (victim.CenterPosition - pos).Length;
						break;
				}

				// Outside this tick's (friendly-fire-adjusted) radius: no damage.
				if (falloffDistance > victimOuter.Length)
					continue;

				var localModifiers = args.DamageModifiers.Append(GetDamageFalloff(falloffDistance)).Append(perTickModifier);
				if (isAlly)
					localModifiers = localModifiers.Append(FriendlyFireDamage);

				var impactOrientation = args.ImpactOrientation;

				// If a warhead lands outside the victim's HitShape, we need to calculate the vertical and horizontal impact angles
				// from impact position, rather than last projectile facing/angle.
				if (falloffDistance > 0)
				{
					var towardsTargetYaw = (victim.CenterPosition - args.ImpactPosition).Yaw;
					var impactAngle = Util.GetVerticalAngle(args.ImpactPosition, victim.CenterPosition);
					impactOrientation = new WRot(WAngle.Zero, impactAngle, towardsTargetYaw);
				}

				var updatedWarheadArgs = new WarheadArgs(args)
				{
					DamageModifiers = localModifiers.ToArray(),
					ImpactOrientation = impactOrientation,
				};

				InflictPrimaryDamage(victim, firedBy, closestActiveShape, updatedWarheadArgs);

				// The folded-in percentage half: a SECOND application on the same victim, with
				// its own (smaller) radius and its own armor table. Applied here rather than as a
				// separate warhead so an inline weapon carries one Damage number and nothing else.
				if (PercentageScale > 0 && falloffDistance <= victimOuter.Length * PercentageSpread / 100)
					InflictPercentage(victim, firedBy, closestActiveShape, updatedWarheadArgs);
			}
		}

		void InflictPercentage(Actor victim, Actor firedBy, HitShape shape, WarheadArgs args)
		{
			var healthInfo = victim.Info.TraitInfoOrDefault<HealthInfo>();
			if (healthInfo == null)
				return;

			// Basis points of max health = Damage/2000 x PercentageScale/100, i.e. Scale 10000 on
			// a 2000-damage weapon is 100bp = 1.00%, exactly what the old twin dealt. The extra
			// factor of 100 is the hundredths granularity — see PercentageScale's [Desc].
			// ROUND, do not truncate: integer division biases every weapon DOWNWARD by up to
			// one basis point, which showed up as a systematic 0.99% where 1.00% was meant.
			// THE SHARED MODE: the percentage magnitude is heavy-scaled by h/2
			// (h=0 -> 0x, h=2 -> 1x of the base Scale) — ONE rounded combined fraction
			// (SharedFoldedPercentageUnits), never a legacy rounding then a multiply.
			// h = 0 yields ZERO units: the percentage half stays zero at h=0 even though
			// the flat Shield coefficient floor is (2000 + h) / 2000 there.
			var basisPoints = sharedMode
				? SharedFoldedPercentageUnits(Damage, PercentageScale, Heaviness)
				: FoldedPercentageUnits(Damage, PercentageScale);
			if (basisPoints <= 0)
				return;

			var versus = PercentageVersus.Count > 0
				? PercentageDamageVersus(victim, shape, args)
				: DamageVersus(victim, shape, args);

			var damage = Util.ApplyPercentageModifiers(healthInfo.HP,
				args.DamageModifiers.Append(basisPoints, versus));

			// ApplyPercentageModifiers already divided by 100 for the basisPoints modifier, so
			// only the remaining factor is left. Applied LAST, on the largest intermediate, so the
			// extra division costs the least precision.
			damage = ApplyPercentageDenominator(damage, PercentageDenominator);

			if (damage <= 0)
				return;

			victim.InflictDamage(firedBy, new Damage(damage, DamageTypes, GetProjectileType(args)));
			ApplyPhysicalState(victim, firedBy, damage);
			ApplyIntegrityScale(victim, firedBy, damage);
		}

		/// <summary>The percentage half's armor lookup: its own table, or Versus when it has none.</summary>
		int PercentageDamageVersus(Actor victim, HitShape shape, WarheadArgs args)
		{
			return VersusFrom(effectivePercentageVersus, victim, shape);
		}


		protected override void InflictDamage(Actor victim, Actor firedBy, HitShape shape, WarheadArgs args)
		{
			// DamageWarhead routes direct Actor impacts here instead of through DoImpact.
			// Keep the folded hit in this wrapper so direct weapons receive it exactly once;
			// positional impacts call InflictPrimaryDamage from ApplyRing and add their own
			// radius-gated folded hit there.
			InflictPrimaryDamage(victim, firedBy, shape, args);
			if (PercentageScale > 0)
				InflictPercentage(victim, firedBy, shape, args);
		}

		protected virtual void InflictPrimaryDamage(Actor victim, Actor firedBy, HitShape shape, WarheadArgs args)
		{
			var damage = Util.ApplyPercentageModifiers(Damage, args.DamageModifiers.Append(DamageVersus(victim, shape, args)));
			victim.InflictDamage(firedBy, new Damage(damage, DamageTypes, GetProjectileType(args)));
			ApplyPhysicalState(victim, firedBy, damage);
			ApplyIntegrityScale(victim, firedBy, damage);
		}

		// Scale a named PhysicalState by the damage just dealt (heat / cold / corrosion meters). Shared
		// with the _Percentage subclass so both the flat main and the %HP twin feed the meter; the
		// separate _ExtraDamage chip warhead never calls this, so it is excluded (maintainer rule).
		// ApplyChange(..., true) lets the TARGET apply its own damage modifiers, so the meter tracks the
		// final effective damage (armor + falloff already baked into `damage`).
		protected void ApplyPhysicalState(Actor victim, Actor firedBy, int damage)
		{
			if (damage == 0)
				return;

			if (!string.IsNullOrEmpty(PhysicalStateName) && PhysicalStateScale != 0)
				ApplyOneState(victim, firedBy, PhysicalStateName, ScaleDamage(damage, PhysicalStateScale));

			foreach (var kv in PhysicalStates)
				if (kv.Value != 0)
					ApplyOneState(victim, firedBy, kv.Key, ScaleDamage(damage, kv.Value));
		}

		static void ApplyOneState(Actor victim, Actor firedBy, string name, int change)
		{
			if (change == 0)
				return;

			var physicalState = victim.TraitsImplementing<PhysicalState>()
				.FirstOrDefault(ps => ps.Name == name);
			physicalState?.ApplyChange(change, firedBy, true);
		}

		// Drain the victim's Integrity ELECTRONICS pool proportional to the damage just dealt, the same
		// way ApplyPhysicalState scales a heat/corrosion meter. Auto-tracks the final effective damage
		// (armor + falloff already baked into `damage`), so the "EMP" self-adjusts with the weapon's
		// output and never needs a hand-set number. Shared with the _Percentage subclass so both the flat
		// main and the %HP twin drain the pool; the _ExtraDamage chip never calls this (excluded). No
		// Integrity trait on the victim (most units have no electronics pool) => a harmless no-op.
		//
		// ⚠ INTEGRITY IS NOT A SHIELD. It absorbs NOTHING — `INotifyDamage` runs after the damage has
		// already landed on health — so draining it buys the attacker no extra damage, only the EMP
		// DISABLE when it reaches zero. The shield is `Shielded` (OpenRA.Mods.AS), a separate trait and
		// a separate layer. `Integrity.cs` had every [Desc] copied verbatim from `Shielded.cs` and this
		// file inherited the same wrong word; corrected 2026-08-17 on the maintainer's report.
		protected void ApplyIntegrityScale(Actor victim, Actor firedBy, int damage)
		{
			if (damage == 0 || IntegrityScale == 0)
				return;

			var change = ScaleDamage(damage, IntegrityScale);
			if (change == 0)
				return;

			victim.TraitsImplementing<Integrity>()
				.FirstOrDefault(t => !t.IsTraitPaused && !t.IsTraitDisabled)
				?.Regenerate(victim, -change);
		}

		// Keep authored fields and final engine damage as Int32, but use Int64 for
		// intermediate products so valid large weapons cannot wrap before division.
		internal static int FoldedPercentageUnits(int damage, int percentageScale)
		{
			return checked((int)(((long)damage * percentageScale + 100000L) / 200000L));
		}

		/// <summary>
		/// THE SHARED-PROFILE percentage conversion (HeavinessMode SharedVersus):
		/// ONE rounded combined fraction
		/// <c>Damage * PercentageScale * Heaviness / (200000 * 2000)</c> — the h/2
		/// heaviness factor is INSIDE the fraction, so the legacy-unit rounding is
		/// not performed first and then multiplied by h (that would compound two
		/// quantisations). Int128 (net8) intermediates keep the full product
		/// (an Int32 Damage x Int32 Scale x h already exceeds Int64's range),
		/// and the result is rounded HALF-UP over the (nonnegative) input and must
		/// fit Int32 — checked cast fails clear instead of wrapping.
		/// </summary>
		internal static int SharedFoldedPercentageUnits(int damage, int percentageScale, int heaviness)
		{
			checked
			{
				Int128 numerator = (Int128)damage * percentageScale * heaviness;
				Int128 denominator = (Int128)200000L * 2000L;
				Int128 rounded = (numerator + denominator / 2) / denominator;
				return (int)rounded;
			}
		}

		/// <summary>
		/// THE SHARED-PROFILE Shield scaling: the Shield row's coefficient scales
		/// ONCE by <c>(2000 + h) / 2000</c> — 100% at h=0, 200% at h=2 — with a
		/// defined HALF-UP rounding over the nonnegative belled value. Every OTHER
		/// row is returned verbatim; the percentage half reuses this exact table
		/// (no second scaling — see the shared branch in RulesetLoaded).
		/// </summary>
		internal static IReadOnlyDictionary<string, int> ScaleShieldCoefficient(
			IReadOnlyDictionary<string, int> table, int heaviness)
		{
			return table.ToDictionary(
				kv => kv.Key,
				kv => kv.Key == "Shield"
					? checked((int)((kv.Value * (2000L + heaviness) + 1000L) / 2000L))
					: kv.Value);
		}

		/// <summary>
		/// One bounded radius scale shared by C# and Python (effective_heaviness.scale_length):
		/// <c>length * (h + 2) / 3</c> must fit Int32 BEFORE the cast. Both bounds are
		/// checked (review 2026-09-10): a NEGATIVE authored WDist scales MORE negative, so
		/// h=2' 4/3 can UNDERFLOW below Int32.MinValue exactly like h=0 can overflow above
		/// Int32.MaxValue — an unchecked cast would wrap silently. Fail clear on either
		/// bound, ACTIVE heaviness only.
		/// ⚠ DISABLED EARLY RETURN (P1, review 2026-09-10): a disabled warhead (-1/omitted)
		/// must keep its AUTHORED length — without this guard the negative sentinel fell
		/// into the formula and scaled every inactive Explicit-Range coordinate to about
		/// 2/3 of authored (h = -0.001 gives (h + 2) / 3 = 0.666333), breaking the
		/// byte-equivalence the disabled path promises; disabled NEGATIVE radii stay
		/// legacy-verbatim too. The Python mirror always had it. Callers on the active
		/// path guarantee Heaviness >= 0 already; the Explicit-Range block runs in BOTH
		/// branches, so the guard lives HERE.
		/// </summary>
		internal static int ScaledRadiusLength(int length, int heaviness)
		{
			if (heaviness < 0)
				return length;
			var h = heaviness / 1000.0;
			var scale = (h + 2.0) / 3.0;
			var scaled = (double)length * scale;
			if (scaled > int.MaxValue || scaled < int.MinValue)
				throw new YamlException(
					$"Scaled radius {scaled:F0} (authored {length} x {scale:F3} at " +
					$"h={h}) overflows Int32.");
			return (int)scaled;
		}

		/// <summary>
		/// Integer numerator/denominator rounded HALF-TO-EVEN (ties-even), truncating toward
		/// zero on non-ties. The single rounding rule shared by the percentage-band
		/// interpolation and its Python mirror (tools/balance/effective_heaviness.py), so both
		/// runtimes land on the same armor table.
		/// </summary>
		internal static int RoundHalfEven(long numerator, long denominator)
		{
			if (denominator == 0)
				throw new DivideByZeroException();
			var negative = (numerator < 0) != (denominator < 0);
			var n = Math.Abs(numerator);
			var d = Math.Abs(denominator);
			var q = n / d;
			var twice = 2 * (n % d);
			if (twice > d || (twice == d && (q & 1) != 0))
				q++;
			return checked((int)(negative ? -q : q));
		}

		/// <summary>
		/// Piecewise per-armor interpolation between the three authored anchor tables:
		/// L->M for h in [0,1] and M->H for h in (1,2], h in thousandths. Exact integer
		/// arithmetic, ties-even per armor (RoundHalfEven). Anchors share one key set
		/// (validated at RulesetLoaded), so `medium` drives the iteration order.
		/// </summary>
		internal static IReadOnlyDictionary<string, int> InterpolatePercentageBands(
			IReadOnlyDictionary<string, int> light,
			IReadOnlyDictionary<string, int> medium,
			IReadOnlyDictionary<string, int> heavy,
			int heaviness)
		{
			var interpolated = new Dictionary<string, int>();
			foreach (var (armor, mediumValue) in medium)
			{
				long product;
				if (heaviness <= 1000)
				{
					var lightValue = light[armor];
					product = (long)lightValue * (1000 - heaviness) + (long)mediumValue * heaviness;
				}
				else
				{
					var heavyValue = heavy[armor];
					product = (long)mediumValue * (2000 - heaviness) + (long)heavyValue * (heaviness - 1000);
				}

				interpolated[armor] = RoundHalfEven(product, 1000);
			}

			return interpolated;
		}

		static bool SameKeys(IReadOnlyDictionary<string, int> a, IReadOnlyDictionary<string, int> b)
		{
			return a.Count == b.Count && a.Keys.All(b.ContainsKey);
		}

		internal static int ApplyPercentageDenominator(int damage, int denominator)
		{
			return denominator == 100
				? damage
				: checked((int)((long)damage * 100 / denominator));
		}

		internal static int ScaleDamage(int damage, int percentage)
		{
			return checked((int)((long)damage * percentage / 100));
		}

		int GetDamageFalloff(int distance)
		{
			var inner = effectiveRange[0].Length;
			for (var i = 1; i < effectiveRange.Length; i++)
			{
				var outer = effectiveRange[i].Length;
				if (outer > distance)
					return int2.Lerp(Falloff[i - 1], Falloff[i], distance - inner, outer - inner);

				inner = outer;
			}

			return 0;
		}
	}
}
