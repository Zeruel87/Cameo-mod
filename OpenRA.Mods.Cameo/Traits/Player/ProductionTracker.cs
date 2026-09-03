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

using System.Collections.Generic;
using System.Linq;
using OpenRA.Traits;

namespace OpenRA.Mods.Cameo.Traits
{
	[TraitLocation(SystemActors.Player)]
	[Desc("Keeps track of player's initial build order and units produced for observer stats.")]
	public class ProductionTrackerInfo : TraitInfo
	{
		[Desc("Maximum number of build order items to track.")]
		public readonly int MaxBuildOrderItems = 18;

		public override object Create(ActorInitializer init) { return new ProductionTracker(init.Self, this); }
	}

	public class ProductionTracker
	{
		readonly ProductionTrackerInfo info;
		List<ProductionTrackerBuildOrderItem> buildOrder;
		Dictionary<string, ProductionTrackerUnitValueItem> unitValues;
		int totalValue;
		public int BuildOrderCount => buildOrder.Count;
		public List<ProductionTrackerBuildOrderItem> BuildOrder => buildOrder;
		public Dictionary<string, ProductionTrackerUnitValueItem> UnitValues => unitValues;
		public int TotalValue => totalValue;
		readonly World world;

		public ProductionTracker(Actor self, ProductionTrackerInfo info)
		{
			this.info = info;
			buildOrder = new List<ProductionTrackerBuildOrderItem>();
			unitValues = new Dictionary<string, ProductionTrackerUnitValueItem>();
			totalValue = 0;
			world = self.World;
		}

		public void BuildOrderItemCreated(string type, int limit, bool ignoreMaxItems = false)
		{
			if (!ignoreMaxItems && BuildOrderCount >= info.MaxBuildOrderItems)
				return;

			if (limit > 0 && buildOrder.Count(i => i.Name == type) >= limit)
				return;

			buildOrder.Add(new ProductionTrackerBuildOrderItem { Name = type, Ticks = world.WorldTick });
		}

		public void UnitCreated(string type, int value)
		{
			totalValue += value;

			if (unitValues.ContainsKey(type))
			{
				unitValues[type].Value += value;
				unitValues[type].Count++;
			}
			else
				unitValues[type] = new ProductionTrackerUnitValueItem { Count = 1, Value = value };
		}
	}

	public class ProductionTrackerBuildOrderItem
	{
		public string Name;
		public int Ticks;
	}

	public class ProductionTrackerUnitValueItem
	{
		public int Value;
		public int Count;
	}
}
