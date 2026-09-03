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

using System;
using System.Collections.Generic;
using System.Linq;
using OpenRA.Mods.Common.Traits;
using OpenRA.Traits;

namespace OpenRA.Mods.Cameo.Traits
{
	[Desc("Scales reload, range, movement/turn speed, firepower, and damage taken with a PhysicalState meter.",
		"The framework's missing half: every stock proportional trait only makes things WORSE",
		"(SlowsProportionalToPhysicalState, DamageMultiplierProportionalToPhysicalState), so a",
		"spin-UP meter had no way to express itself. This one is signed — put the better number",
		"in `To` and the meter is a buff, put it in `From` and it is a penalty. The gatling",
		"ladder is the motivating case: the longer it fires, the faster it fires.",
		"",
		"Lives in OpenRA.Mods.Cameo rather than Mods.Common because `engine/` is a build output",
		"that `make all` deletes; assembly order (AS, CA, Cameo, Cnc, D2k, Common) resolves this",
		"name from here regardless.")]
	public class ModifiesCombatProportionalToPhysicalStateInfo : ConditionalTraitInfo
	{
		[FieldLoader.Require]
		[Desc("Name of the PhysicalState to monitor.")]
		public readonly string PhysicalStateName = null;

		[Desc("Reload-delay modifier at the meter's low end (percentage; lower = faster).")]
		public readonly int ReloadDelayFrom = 100;

		[Desc("Reload-delay modifier at the meter's high end (percentage; lower = faster).")]
		public readonly int ReloadDelayTo = 100;

		[Desc("Range modifier at the meter's low end (percentage).")]
		public readonly int RangeFrom = 100;

		[Desc("Range modifier at the meter's high end (percentage).")]
		public readonly int RangeTo = 100;

		[Desc("Movement-speed modifier at the meter's low end (percentage).")]
		public readonly int SpeedFrom = 100;

		[Desc("Movement-speed modifier at the meter's high end (percentage).")]
		public readonly int SpeedTo = 100;

		[Desc("Body turn-speed modifier at the meter's low end (percentage).")]
		public readonly int TurnSpeedFrom = 100;

		[Desc("Body turn-speed modifier at the meter's high end (percentage).")]
		public readonly int TurnSpeedTo = 100;

		[Desc("Turret turn-speed modifier at the meter's low end (percentage).")]
		public readonly int TurretTurnSpeedFrom = 100;

		[Desc("Turret turn-speed modifier at the meter's high end (percentage).")]
		public readonly int TurretTurnSpeedTo = 100;

		[Desc("Firepower modifier at the meter's low end (percentage).")]
		public readonly int FirepowerFrom = 100;

		[Desc("Firepower modifier at the meter's high end (percentage).")]
		public readonly int FirepowerTo = 100;

		[Desc("Damage-TAKEN modifier at the meter's low end (percentage; lower = tougher).")]
		public readonly int DamageTakenFrom = 100;

		[Desc("Damage-TAKEN modifier at the meter's high end (percentage; lower = tougher).",
			"The gatling 'special unit' ladder uses this: a spun-up gatling is harder to",
			"kill as well as faster-firing, so the meter has to carry a defensive term or",
			"those actors cannot be converted without losing a stat.")]
		public readonly int DamageTakenTo = 100;

		[Desc("Audio pitch at the meter's low end (percentage of normal).",
			"Folded into this trait rather than a separate one (maintainer's option C): the",
			"readability hook and the effect it advertises are driven by the same meter, so",
			"splitting them lets them drift out of step.")]
		public readonly int PitchFrom = 100;

		[Desc("Audio pitch at the meter's high end (percentage of normal).")]
		public readonly int PitchTo = 100;

		[Desc("Armament names to affect. Empty affects all of them.")]
		public readonly HashSet<string> ArmamentNames = new();

		[Desc("Use the deviation from RelaxedValue instead of the absolute meter value.")]
		public readonly bool UseDeviationFromRelaxed = false;

		public override object Create(ActorInitializer init)
		{
			return new ModifiesCombatProportionalToPhysicalState(init.Self, this);
		}
	}

	public class ModifiesCombatProportionalToPhysicalState
		: ConditionalTrait<ModifiesCombatProportionalToPhysicalStateInfo>,
			IReloadModifier, IRangeModifier, ISpeedModifier, ITurnSpeedModifier,
			ITurretTurnSpeedModifier, IFirepowerModifier,
			IDamageModifier, INotifyPhysicalStateChanged
	{
		readonly PhysicalState physicalState;

		int reload = 100;
		int range = 100;
		int speed = 100;
		int turnSpeed = 100;
		int turretTurnSpeed = 100;
		int firepower = 100;
		int damageTaken = 100;
		int pitch = 100;

		/// <summary>Current audio pitch percentage, for sound-playing traits to read.</summary>
		public int PitchPercentage => IsTraitDisabled ? 100 : pitch;

		/// <summary>How far along the meter is, 0..1 — the hook a glow/overlay reads.</summary>
		public float Intensity { get; private set; }

		public ModifiesCombatProportionalToPhysicalState(
			Actor self, ModifiesCombatProportionalToPhysicalStateInfo info)
			: base(info)
		{
			physicalState = self.TraitsImplementing<PhysicalState>()
				.FirstOrDefault(ps => ps.Name == info.PhysicalStateName);

			// A missing meter leaves every modifier at 100. Failing loudly here would
			// break actors that legitimately gain the meter from a conditional trait.
			if (physicalState != null)
				Update(physicalState.Value);
		}

		void Update(int value)
		{
			if (physicalState == null)
				return;

			Intensity = Normalize(value);
			reload = Interpolate(Info.ReloadDelayFrom, Info.ReloadDelayTo, Intensity);
			range = Interpolate(Info.RangeFrom, Info.RangeTo, Intensity);
			speed = Interpolate(Info.SpeedFrom, Info.SpeedTo, Intensity);
			turnSpeed = Interpolate(Info.TurnSpeedFrom, Info.TurnSpeedTo, Intensity);
			turretTurnSpeed = Interpolate(Info.TurretTurnSpeedFrom, Info.TurretTurnSpeedTo, Intensity);
			firepower = Interpolate(Info.FirepowerFrom, Info.FirepowerTo, Intensity);
			damageTaken = Interpolate(Info.DamageTakenFrom, Info.DamageTakenTo, Intensity);
			pitch = Interpolate(Info.PitchFrom, Info.PitchTo, Intensity);
		}

		float Normalize(int value)
		{
			var min = physicalState.MinValue;
			var max = physicalState.MaxValue;

			if (Info.UseDeviationFromRelaxed)
			{
				var relaxed = ((PhysicalStateInfo)physicalState.Info).RelaxedValue;
				var span = value >= relaxed ? max - relaxed : relaxed - min;
				if (span == 0)
					return 0f;
				return Math.Abs(value - relaxed) / (float)span;
			}

			var range_ = max - min;
			return range_ == 0 ? 0f : (value - min) / (float)range_;
		}

		// Clamped at 1 rather than 0: a modifier of 0 means "no damage" / "no range" /
		// "cannot move", which is a far bigger statement than any meter should make by
		// interpolation alone. A yaml author who wants zero must write zero.
		static int Interpolate(int from, int to, float t)
		{
			return Math.Max(1, (int)Math.Round(from + (to - from) * t));
		}

		bool Affects(string armamentName)
		{
			return Info.ArmamentNames.Count == 0
				|| (!string.IsNullOrEmpty(armamentName) && Info.ArmamentNames.Contains(armamentName));
		}

		int IReloadModifier.GetReloadModifier(string armamentName)
		{
			return IsTraitDisabled || !Affects(armamentName) ? 100 : reload;
		}

		int IRangeModifier.GetRangeModifier()
		{
			return IsTraitDisabled ? 100 : range;
		}

		int ISpeedModifier.GetSpeedModifier()
		{
			return IsTraitDisabled ? 100 : speed;
		}

		int ITurnSpeedModifier.GetTurnSpeedModifier()
		{
			return IsTraitDisabled ? 100 : turnSpeed;
		}

		int ITurretTurnSpeedModifier.GetTurretTurnSpeedModifier(string turretName)
		{
			return IsTraitDisabled ? 100 : turretTurnSpeed;
		}

		int IFirepowerModifier.GetFirepowerModifier(string armamentName)
		{
			return IsTraitDisabled || !Affects(armamentName) ? 100 : firepower;
		}

		int IDamageModifier.GetDamageModifier(Actor attacker, Damage damage)
		{
			return IsTraitDisabled ? 100 : damageTaken;
		}

		void INotifyPhysicalStateChanged.PhysicalStateChanged(
			Actor self, PhysicalState state, int oldValue, int newValue)
		{
			if (state == physicalState)
				Update(newValue);
		}
	}
}
