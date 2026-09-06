#region Copyright & License Information
/*
 * Copyright 2015- OpenRA.Mods.AS Developers (see AUTHORS)
 * This file is a part of a third-party plugin for OpenRA, which is
 * free software. It is made available to you under the terms of the
 * GNU General Public License as published by the Free Software
 * Foundation. For more information, see COPYING.
 */
#endregion

using System.Linq;
using OpenRA.GameRules;
using OpenRA.Mods.Common;
using OpenRA.Mods.Common.Traits;
using OpenRA.Traits;

namespace OpenRA.Mods.Cameo.Warheads
{
	[Desc("Percentage-of-max-health version of AreaDamage: the SAME expanding-ring / damage-over-time",
		"/ baked friendly-fire spatial pass, but each hit removes a PERCENTAGE of the victim's maximum",
		"health instead of a flat amount (Damage is the percentage, scaled by Falloff, per-tick weight",
		"and Versus). One of these with a Falloff gradient replaces a whole stack of concentric",
		"HealthPercentageDamage rings (the old nuke '% big bang' bandaid). Set UpdatesUnitStatistics:",
		"false so it is not counted for unit damage stats.")]
	public class AreaDamagePercentageWarhead : AreaDamageWarhead
	{
		[Desc("DENOMINATOR the Damage value is read against — NOT a multiplier (unlike the",
			"IntegrityScale / PhysicalStateScale fields it sits next to, which scale UP).",
			"100 = Damage is a whole percent of max health, the engine convention and the",
			"default, so existing weapons are unaffected.",
			"10000 = Damage is in BASIS POINTS, i.e. 0.01% steps: Damage 160 removes 1.60%",
			"of max health.",
			"The finer unit exists so a percentage twin can track its weapon's flat Damage",
			"exactly instead of rounding: on the 100-damage grid one flat step is worth",
			"exactly one basis point (100 flat damage = 0.01% of max health), and the",
			"percentage warhead's Versus values move in clean steps of 5.")]
		public new readonly int PercentageDenominator = 100;

		// Extends the BASE class's validation through its hook. Implementing
		// IRulesetLoaded<WeaponInfo> here instead would REPLACE the base's explicit
		// implementation, so `effectiveRange` would never be built and every ring would
		// be empty — a silent break, not a compile error.
		protected override void ValidateFields()
		{
			if (PercentageDenominator <= 0)
				throw new YamlException("PercentageDenominator must be positive: 100 = Damage is "
					+ "a whole percent of max health, 10000 = basis points (0.01% steps).");

			if (PercentageScale > 0)
				throw new YamlException("AreaDamagePercentage cannot also set PercentageScale: "
					+ "this would apply two percentage hits from one warhead.");
		}

		protected override void InflictPrimaryDamage(Actor victim, Actor firedBy, HitShape shape, WarheadArgs args)
		{
			var healthInfo = victim.Info.TraitInfo<HealthInfo>();
			var damage = Util.ApplyPercentageModifiers(healthInfo.HP, args.DamageModifiers.Append(Damage, DamageVersus(victim, shape, args)));

			// ApplyPercentageModifiers already divided by 100 for the Damage modifier, so a
			// finer unit only needs the remaining factor. Applied LAST, on the largest
			// intermediate, so the extra division costs the least precision.
			damage = ApplyPercentageDenominator(damage, PercentageDenominator);
			victim.InflictDamage(firedBy, new Damage(damage, DamageTypes, GetProjectileType(args)));
			ApplyPhysicalState(victim, firedBy, damage);
			ApplyIntegrityScale(victim, firedBy, damage);
		}
	}
}
