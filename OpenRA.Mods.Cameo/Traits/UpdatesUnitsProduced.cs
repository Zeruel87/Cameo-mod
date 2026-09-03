#region Copyright & License Information
/*
 * Ported to Cameo from OpenRA Combined Arms (OpenRA.Mods.CA), which is free
 * software under the GNU General Public License. See COPYING.
 *
 * Cameo changes: namespace OpenRA.Mods.CA.* -> OpenRA.Mods.Cameo.*, so the type
 * resolves out of the Cameo assembly (mod.yaml lists AS, CA, Cameo, Cnc, D2k,
 * Common and ObjectCreator.FindType takes the FIRST match).
 */
#endregion

using OpenRA.Mods.Common.Traits;
using OpenRA.Traits;

namespace OpenRA.Mods.Cameo.Traits
{
	[Desc("Attach to producer actors. Updates units produced.")]
	public class UpdatesUnitsProducedInfo : TraitInfo
	{
		public override object Create(ActorInitializer init) { return new UpdatesUnitsProduced(init, this); }
	}

	public class UpdatesUnitsProduced : INotifyCreated, INotifyOwnerChanged, INotifyProduction
	{
		public readonly UpdatesUnitsProducedInfo Info;
		ProductionTracker productionTracker;

		public UpdatesUnitsProduced(ActorInitializer init, UpdatesUnitsProducedInfo info)
		{
			Info = info;
			productionTracker = init.Self.Owner.PlayerActor.Trait<ProductionTracker>();
		}

		void INotifyCreated.Created(Actor self)
		{
			productionTracker = self.Owner.PlayerActor.Trait<ProductionTracker>();
		}

		// ⚠ FULLY QUALIFIED ON PURPOSE. `FactionCA.cs` declares the nested namespace
		// OpenRA.Mods.Cameo.Traits.Player, which shadows the OpenRA.Player TYPE for every
		// file in OpenRA.Mods.Cameo.Traits — a bare `Player` here is a namespace.
		void INotifyOwnerChanged.OnOwnerChanged(Actor self, OpenRA.Player oldOwner, OpenRA.Player newOwner)
		{
			productionTracker = newOwner.PlayerActor.Trait<ProductionTracker>();
		}

		void INotifyProduction.UnitProduced(Actor self, Actor other, CPos exit)
		{
			var valued = other.Info.TraitInfoOrDefault<ValuedInfo>();
			var name = other.Info.Name.EndsWith(".ai") ? other.Info.Name[..^3] : other.Info.Name;

			if (valued != null && valued.Cost > 0)
				productionTracker.UnitCreated(name, valued.Cost);
		}
	}
}
