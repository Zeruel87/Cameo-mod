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

using OpenRA.Traits;

namespace OpenRA.Mods.Cameo.Traits
{
	[Desc("Added to build order when the actor is created.")]
	public class UpdatesBuildOrderInfo : TraitInfo
	{
		[Desc("Won't add more than this number to the build order. Zero for unlimited.")]
		public readonly int Limit = 0;

		[Desc("If true, ignores the maximum.")]
		public readonly bool IgnoreMaxItems = false;

		public override object Create(ActorInitializer init) { return new UpdatesBuildOrder(init, this); }
	}

	public class UpdatesBuildOrder : INotifyCreated
	{
		public readonly UpdatesBuildOrderInfo Info;
		readonly ProductionTracker productionTracker;

		public UpdatesBuildOrder(ActorInitializer init, UpdatesBuildOrderInfo info)
		{
			Info = info;
			productionTracker = init.Self.Owner.PlayerActor.Trait<ProductionTracker>();
		}

		void INotifyCreated.Created(Actor self)
		{
			productionTracker.BuildOrderItemCreated(self.Info.Name, Info.Limit, Info.IgnoreMaxItems);
		}
	}
}
