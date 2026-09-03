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
using System.Linq;
using OpenRA.Mods.Common.Traits;
using OpenRA.Primitives;
using OpenRA.Traits;

namespace OpenRA.Mods.Cameo.Traits
{
	[Desc("Displays a named PhysicalState as a selection bar only while the actor is selected.")]
	public class SelectedPhysicalStateBarInfo : ConditionalTraitInfo, Requires<PhysicalStateInfo>
	{
		[FieldLoader.Require]
		[Desc("Name of the PhysicalState to display.")]
		public readonly string PhysicalStateName = null;

		[Desc("Color for values above RelaxedValue.")]
		public readonly Color PositiveColor = Color.Red;

		[Desc("Color for values below RelaxedValue.")]
		public readonly Color NegativeColor = Color.Blue;

		[Desc("Color for the relaxed value.")]
		public readonly Color NeutralColor = Color.Gray;

		[Desc("Whether to display the bar when the value equals RelaxedValue.")]
		public readonly bool DisplayWhenRelaxed = false;

		[Desc("Show the absolute position within the min/max range instead of deviation from RelaxedValue.")]
		public readonly bool ShowAbsoluteValues = false;

		public override object Create(ActorInitializer init)
		{
			return new SelectedPhysicalStateBar(init.Self, this);
		}

		public override void RulesetLoaded(Ruleset rules, ActorInfo ai)
		{
			base.RulesetLoaded(rules, ai);

			if (ai.TraitInfos<PhysicalStateInfo>().Count(ps => ps.Name == PhysicalStateName) != 1)
				throw new YamlException(
					$"{nameof(SelectedPhysicalStateBar)} requires exactly one PhysicalState with matching Name.");
		}
	}

	public class SelectedPhysicalStateBar : ConditionalTrait<SelectedPhysicalStateBarInfo>, ISelectionBar
	{
		readonly Actor self;
		readonly PhysicalState physicalState;

		public SelectedPhysicalStateBar(Actor self, SelectedPhysicalStateBarInfo info)
			: base(info)
		{
			this.self = self;
			physicalState = self.TraitsImplementing<PhysicalState>()
				.Single(ps => ps.Name == info.PhysicalStateName);
		}

		internal static float BarValue(
			int value, int minValue, int maxValue, int relaxedValue, bool showAbsoluteValues)
		{
			if (showAbsoluteValues)
			{
				var range = (long)maxValue - minValue;
				return range <= 0 ? 0f :
					(float)Math.Clamp(((long)value - minValue) / (double)range, 0d, 1d);
			}

			var deviation = Math.Abs((long)value - relaxedValue);
			var maxDeviation = Math.Max((long)maxValue - relaxedValue, (long)relaxedValue - minValue);
			return maxDeviation <= 0 ? 0f :
				(float)Math.Clamp(deviation / (double)maxDeviation, 0d, 1d);
		}

		float ISelectionBar.GetValue()
		{
			if (IsTraitDisabled || !self.World.Selection.Contains(self))
				return 0f;

			var relaxedValue = ((PhysicalStateInfo)physicalState.Info).RelaxedValue;
			if (physicalState.Value == relaxedValue && !Info.DisplayWhenRelaxed)
				return 0f;

			return BarValue(
				physicalState.Value,
				physicalState.MinValue,
				physicalState.MaxValue,
				relaxedValue,
				Info.ShowAbsoluteValues);
		}

		Color ISelectionBar.GetColor()
		{
			var relaxedValue = ((PhysicalStateInfo)physicalState.Info).RelaxedValue;
			return physicalState.Value > relaxedValue ? Info.PositiveColor :
				physicalState.Value < relaxedValue ? Info.NegativeColor : Info.NeutralColor;
		}

		bool ISelectionBar.DisplayWhenEmpty
		{
			get
			{
				if (IsTraitDisabled || !Info.DisplayWhenRelaxed || !self.World.Selection.Contains(self))
					return false;

				return physicalState.Value == ((PhysicalStateInfo)physicalState.Info).RelaxedValue;
			}
		}
	}
}
