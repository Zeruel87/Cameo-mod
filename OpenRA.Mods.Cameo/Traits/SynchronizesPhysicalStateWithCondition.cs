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
	[Desc("Synchronizes a PhysicalState value with the number of granted condition instances.")]
	public class SynchronizesPhysicalStateWithConditionInfo : TraitInfo, Requires<PhysicalStateInfo>,
		IObservesVariablesInfo, IRulesetLoaded
	{
		[FieldLoader.Require]
		[ConsumedConditionReference]
		[Desc("Condition whose instance count drives the PhysicalState.")]
		public readonly string Condition = null;

		[FieldLoader.Require]
		[Desc("Name of the PhysicalState to update.")]
		public readonly string PhysicalStateName = null;

		[Desc("PhysicalState value contributed by each condition instance.")]
		public readonly int ValuePerInstance = 1;

		[Desc("PhysicalState value when no condition instances are granted.")]
		public readonly int BaseValue = 0;

		public override object Create(ActorInitializer init)
		{
			return new SynchronizesPhysicalStateWithCondition(init.Self, this);
		}

		public void RulesetLoaded(Ruleset rules, ActorInfo ai)
		{
			if (ai.TraitInfos<PhysicalStateInfo>().Count(ps => ps.Name == PhysicalStateName) != 1)
				throw new YamlException(
					$"{nameof(SynchronizesPhysicalStateWithCondition)} requires exactly one PhysicalState with matching Name.");
		}
	}

	public class SynchronizesPhysicalStateWithCondition : IObservesVariables
	{
		readonly SynchronizesPhysicalStateWithConditionInfo info;
		readonly PhysicalState physicalState;

		public SynchronizesPhysicalStateWithCondition(
			Actor self, SynchronizesPhysicalStateWithConditionInfo info)
		{
			this.info = info;
			physicalState = self.TraitsImplementing<PhysicalState>()
				.Single(ps => ps.Name == info.PhysicalStateName);
		}

		IEnumerable<VariableObserver> IObservesVariables.GetVariableObservers()
		{
			yield return new VariableObserver(ConditionsChanged, [info.Condition]);
		}

		void ConditionsChanged(Actor self, IReadOnlyDictionary<string, int> conditions)
		{
			conditions.TryGetValue(info.Condition, out var level);
			physicalState.Value = ValueForConditionLevel(level, info.BaseValue, info.ValuePerInstance);
		}

		internal static int ValueForConditionLevel(int level, int baseValue, int valuePerInstance)
		{
			return checked(baseValue + Math.Max(0, level) * valuePerInstance);
		}
	}
}
