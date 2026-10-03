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
using OpenRA.Traits;

namespace OpenRA.Mods.Cameo.Traits
{
	// A Cameo SHADOW of the engine trait (CLAUDE.md rule 7): ObjectCreator takes the first assembly holding the name,
	// and Cameo comes before Common, so every `UpdatesPlayerStatistics:` node (1,243 actors) builds this one with no
	// yaml change. The Info SUBCLASSES the engine Info so the engine's own lookups by type (the spectator army tab's
	// ArmyUnit, the encyclopedia) still find it, and the trait WRAPS the engine trait so the statistics behave exactly
	// as before; the only addition is the arsenal ledger booking (AI_ARCHITECTURE.md §12.3).
	[Desc("Attach this to a unit to update observer stats. Cameo: also books it in the owners' BotArsenalLedger.")]
	public class UpdatesPlayerStatisticsInfo : OpenRA.Mods.Common.Traits.UpdatesPlayerStatisticsInfo
	{
		[Desc("Cameo: book this actor's creation, loss and kills in the players' BotArsenalLedger.",
			"A field the engine Info lacks, so a boot with it set proves the shadow is the type in use.")]
		public readonly bool RecordInArsenalLedger = true;

		public override object Create(ActorInitializer init) { return new UpdatesPlayerStatistics(this, init.Self); }
	}

	public class UpdatesPlayerStatistics : INotifyKilled, INotifyCreated, INotifyOwnerChanged, INotifyActorDisposing
	{
		readonly UpdatesPlayerStatisticsInfo info;
		readonly OpenRA.Mods.Common.Traits.UpdatesPlayerStatistics inner;
		readonly string type;
		readonly int cost;

		public UpdatesPlayerStatistics(UpdatesPlayerStatisticsInfo info, Actor self)
		{
			this.info = info;
			inner = new OpenRA.Mods.Common.Traits.UpdatesPlayerStatistics(info, self);
			type = info.OverrideActor ?? self.Info.Name;
			cost = self.Info.TraitInfoOrDefault<ValuedInfo>()?.Cost ?? 0;
		}

		static BotArsenalLedger LedgerOf(OpenRA.Player player) =>
			player == null || player.PlayerActor == null || player.PlayerActor.Disposed ? null : player.PlayerActor.TraitOrDefault<BotArsenalLedger>();

		void INotifyCreated.Created(Actor self)
		{
			((INotifyCreated)inner).Created(self);
			if (info.RecordInArsenalLedger)
				LedgerOf(self.Owner)?.RecordCreated(type);
		}

		void INotifyKilled.Killed(Actor self, AttackInfo e)
		{
			// The engine skips a player who already won or lost; so does the ledger.
			var counts = info.RecordInArsenalLedger && self.Owner.WinState == WinState.Undefined;
			((INotifyKilled)inner).Killed(self, e);
			if (!counts)
				return;

			LedgerOf(self.Owner)?.RecordLost(type, cost);
			if (e.Attacker != null && e.Attacker != self && !self.Owner.NonCombatant && e.Attacker.Owner != self.Owner)
				LedgerOf(e.Attacker.Owner)?.RecordKill(e.Attacker.Info.Name, type, cost);
		}

		void INotifyOwnerChanged.OnOwnerChanged(Actor self, OpenRA.Player oldOwner, OpenRA.Player newOwner) =>
			((INotifyOwnerChanged)inner).OnOwnerChanged(self, oldOwner, newOwner);

		void INotifyActorDisposing.Disposing(Actor self) => ((INotifyActorDisposing)inner).Disposing(self);
	}
}
