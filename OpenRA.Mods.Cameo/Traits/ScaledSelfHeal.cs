#region Copyright & License Information
/*
 * Copyright (c) The OpenRA Developers and Contributors
 * This file is part of OpenRA, which is free software. It is made
 * available to you under the terms of the GNU General Public License
 * as published by the Free Software Foundation, either version 3 of
 * the License, or (at your option) any later version. For more
 * information, see COPYING.
 */
#endregion

using OpenRA.Mods.Common.Traits;
using OpenRA.Primitives;
using OpenRA.Traits;

namespace OpenRA.Mods.Cameo.Traits
{
	[Desc("Regenerates health as a FRACTION OF MAX HEALTH every tick, ramping up after damage.",
		"",
		"DESIGN.md 'Regeneration' (maintainer 2026-09-07). The rate is stated as TICKS TO FULL",
		"— 2500 for vehicles/aircraft/ships/defenses (100 s), 1250 for infantry (50 s) — so one",
		"number describes the whole rule and no actor carries a self-heal figure of its own.",
		"",
		"WHY THIS EXISTS INSTEAD OF ChangesHealth. `ChangesHealth.PercentageStep` is an int with",
		"a floor of 1% per step, and the design needs 1/25 of a percent PER TICK (0.04%). The old",
		"encoding reached that only by writing `Step = HP/2500` on every single actor — 883 of",
		"them — which is also what forced HP onto a 2500 grid, because a step that does not divide",
		"evenly heals at the wrong rate. Deriving the amount from MaxHP frees the HP grid to 1000",
		"and deletes all 883 overrides.",
		"",
		"THE FRACTION IS CARRIED, NOT TRUNCATED. At 0.04%/tick a 1,000 HP unit earns 0.4 HP per",
		"tick; `Damage` is an int, so a naive implementation heals it ZERO forever while a 100,000",
		"HP tank heals correctly. The remainder is accumulated, so the rate is exact at every HP",
		"value and small units are not silently excluded.",
		"",
		"THE RAMP REPLACES A HARD COOLDOWN. Regeneration is never switched off — it resumes the",
		"instant damage stops, at zero, and climbs linearly to full over RampTicks. A unit under",
		"sustained fire therefore heals almost nothing without needing a separate cooldown timer,",
		"and a unit that disengages recovers smoothly instead of snapping on at full rate.")]
	public class ScaledSelfHealInfo : ConditionalTraitInfo, Requires<IHealthInfo>
	{
		[Desc("Ticks to regenerate from zero to full health. The per-tick amount is",
			"MaxHP / TicksToFull, carried as a fraction. 2500 = 100 seconds at 25 ticks/s.")]
		public readonly int TicksToFull = 2500;

		[Desc("Ticks after taking damage over which the rate climbs linearly from 0 to full.",
			"125 = 5 seconds. Shields use twice this.")]
		public readonly int RampTicks = 125;

		[Desc("Only regenerate while health is below this percentage of maximum.",
			"100 means 'always heal when damaged at all'.")]
		public readonly int StartIfBelow = 100;

		[Desc("Damage types applied by the heal. Leave empty for untyped healing.")]
		public readonly BitSet<DamageType> DamageTypes = default;

		public override object Create(ActorInitializer init) { return new ScaledSelfHeal(this); }

		public override void RulesetLoaded(Ruleset rules, ActorInfo ai)
		{
			base.RulesetLoaded(rules, ai);

			// A zero or negative rate is silently NO healing at all, which looks identical to a
			// working trait until someone measures it. Fail at load instead.
			if (TicksToFull < 1)
				throw new YamlException($"{nameof(TicksToFull)} must be at least 1.");

			if (RampTicks < 1)
				throw new YamlException($"{nameof(RampTicks)} must be at least 1 (use 1 for no ramp).");
		}
	}

	public class ScaledSelfHeal : ConditionalTrait<ScaledSelfHealInfo>, ITick, INotifyDamage
	{
		readonly ScaledSelfHealInfo info;
		IHealth health;

		// HP x ticks, waiting to become whole HP. `long` because MaxHP reaches the millions on a
		// slab and this is multiplied by RampTicks before it is divided back down.
		long accumulator;
		int ticksSinceDamage;

		public ScaledSelfHeal(ScaledSelfHealInfo info)
			: base(info)
		{
			this.info = info;
			ticksSinceDamage = info.RampTicks;
		}

		protected override void Created(Actor self)
		{
			health = self.Trait<IHealth>();
			base.Created(self);
		}

		void INotifyDamage.Damaged(Actor self, AttackInfo e)
		{
			// Healing counts as negative damage and must not reset its own ramp.
			if (e.Damage.Value > 0)
			{
				ticksSinceDamage = 0;
				accumulator = 0;
			}
		}

		void ITick.Tick(Actor self)
		{
			if (IsTraitDisabled || health == null || health.HP <= 0)
				return;

			if (ticksSinceDamage < info.RampTicks)
				ticksSinceDamage++;

			if (health.HP >= health.MaxHP)
			{
				accumulator = 0;
				return;
			}

			if (info.StartIfBelow < 100 && health.HP * 100 >= health.MaxHP * info.StartIfBelow)
				return;

			// rate = MaxHP / TicksToFull, scaled by the ramp fraction ticksSinceDamage/RampTicks.
			// Both divisions are deferred into one so nothing is lost to integer truncation.
			accumulator += (long)health.MaxHP * ticksSinceDamage;

			var divisor = (long)info.TicksToFull * info.RampTicks;
			var heal = (int)(accumulator / divisor);
			if (heal <= 0)
				return;

			accumulator -= (long)heal * divisor;
			self.InflictDamage(self, new Damage(-heal, info.DamageTypes));
		}
	}
}
