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

using System.Collections.Generic;
using System.Linq;
using OpenRA.Mods.CA.Traits;
using OpenRA.Mods.Common.Traits;
using OpenRA.Traits;

namespace OpenRA.Mods.Cameo.Traits.BotModules
{
	[TraitLocation(SystemActors.Player)]
	[Desc("CN3 (AI_MASTER_PLAN §3, crystallized-nexus port): the stealth-doctrine provider.",
		"Publishes the DetectCloaked carriers this bot has actually seen (fog memory, plus",
		"the observed type's public ruleset range) as IBotStealthDoctrine — the squad",
		"manager's stealth drafting and the stealth states' coverage checks read it.",
		"Off on master: armed by the `cn3_stealth_squads` condition (switch group",
		"Y_cn3_stealth_squads). With no enabled provider nothing drafts stealth squads",
		"and every coverage check reads empty - bit-identical to before.")]
	public class StealthDoctrineBotModuleInfo : ConditionalTraitInfo
	{
		[Desc("World ticks a remembered detector keeps covering its last-seen cell.",
			"Matches the fog-memory sighting scale (IntelStaleTicks order), not the",
			"30000-tick ObservationTimeoutTicks a building keeps - a mobile detector",
			"that drove off should stop covering ground it left.")]
		public readonly int DetectorMemoryTicks = 2500;

		public override object Create(ActorInitializer init) { return new StealthDoctrineBotModule(init.Self, this); }
	}

	public class StealthDoctrineBotModule : ConditionalTrait<StealthDoctrineBotModuleInfo>, IBotStealthDoctrine
	{
		readonly OpenRA.Player player;

		public StealthDoctrineBotModule(Actor self, StealthDoctrineBotModuleInfo info)
			: base(info)
		{
			player = self.Owner;
		}

		public IEnumerable<BotKnownDetector> RememberedDetectors()
		{
			// The master AI is itself a ConditionalTrait (genericbot), so resolve
			// per call and never permanently cache the instance (the LC4 rule).
			var master = player.PlayerActor.TraitsImplementing<MasterAiBotModule>().FirstEnabledTraitOrDefault();
			return master?.KnownDetectors(Info.DetectorMemoryTicks) ?? Enumerable.Empty<BotKnownDetector>();
		}
	}
}
