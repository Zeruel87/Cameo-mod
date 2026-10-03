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

using OpenRA.Mods.CA.Traits;
using OpenRA.Mods.Common.Traits;
using OpenRA.Traits;

namespace OpenRA.Mods.Cameo.Traits
{
	[TraitLocation(SystemActors.Player)]
	public class ParallelProductionBotModuleInfo : ConditionalTraitInfo
	{
		public override object Create(ActorInitializer init) { return new ParallelProductionBotModule(this); }

		[Desc("Idle queues of one category a BuildUnit call may fill per pass. 4 means a bot with four war "
			+ "factories can keep all of them producing instead of serialising on the first free one.")]
		public readonly int MaxQueuesPerCategory = 4;
	}

	/// <summary>
	/// PP-1 (AI_ARCHITECTURE §12.21): the parallel-production provider — settings only, no orders.
	/// UnitBuilderBotModuleCA asks how many idle queues of a category it may fill per call; this module
	/// exists so the width lives behind a condition (`genericbot && parallel_production`) instead of a
	/// field the shared `@generic` instance would also hand to classic — the A/B control stays upstream.
	/// </summary>
	public class ParallelProductionBotModule : ConditionalTrait<ParallelProductionBotModuleInfo>, IBotProductionWidth
	{
		public ParallelProductionBotModule(ParallelProductionBotModuleInfo info)
			: base(info)
		{
		}

		public int MaxQueuesPerCategory => Info.MaxQueuesPerCategory;
	}
}
