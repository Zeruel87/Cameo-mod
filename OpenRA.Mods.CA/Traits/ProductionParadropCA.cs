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
using OpenRA.Activities;
using OpenRA.Mods.Common;
using OpenRA.Mods.Common.Activities;
using OpenRA.Mods.Common.Traits;
using OpenRA.Primitives;
using OpenRA.Traits;

namespace OpenRA.Mods.CA.Traits
{
	[Desc("Deliver the unit in production via paradrop.")]
	public class ProductionParadropCAInfo : ProductionInfo, Requires<ExitInfo>
	{
		[ActorReference(typeof(AircraftInfo))]
		[Desc("Cargo aircraft used. Must have Aircraft trait.")]
		public readonly string ActorType = "badr";

		[Desc("How the spawn location/direction is calculated for the delivering actor.",
			"Standard: Spawn 1/2 map distance east, in line with the destination.",
			"ClosestEdgeToHome: Spawn from direction of map edge closest to the player spawn at a distance proportional to map size.",
			"ClosestEdgeToDestination: Spawn 1/2 map distance in the direction of closest map edge to the destination.")]
		public readonly string SpawnType = "Standard";

		[Desc("Direction the aircraft should face to land.")]
		public readonly WAngle Facing = new WAngle(256);

		[Desc("If true, the actor's speed will be adjusted based on the distance it needs to travel to deliver its cargo.")]
		public readonly bool ProportionalSpeed = false;

		[Desc("Distance to base the proportional speed multiplier around.")]
		public readonly WDist ProportionalSpeedBaseDistance = WDist.FromCells(50);

		[Desc("Minimum speed modifier.")]
		public readonly int ProportionalSpeedMinimum = 80;

		[Desc("Maximum speed modifier.")]
		public readonly int ProportionalSpeedMaximum = 200;

		[Desc("Sound to play when dropping the unit.")]
		public readonly string ChuteSound = null;

		[NotificationReference("Speech")]
		[Desc("Speech notification to play when dropping the unit.")]
		public readonly string ReadyAudio = null;

		[FluentReference]
		[Desc("Text notification to display when dropping the unit.")]
		public readonly string ReadyTextNotification = null;

		public override object Create(ActorInitializer init) { return new ProductionParadropCA(init, this); }
	}

	sealed class ProductionParadropCA : Production
	{
		readonly Lazy<RallyPoint> rp;

		public ProductionParadropCA(ActorInitializer init, ProductionParadropCAInfo info)
			: base(init, info)
		{
			rp = Exts.Lazy(() => init.Self.IsDead ? null : init.Self.TraitOrDefault<RallyPoint>());
		}

		public override bool Produce(Actor self, ActorInfo producee, string productionType, TypeDictionary inits, int refundableValue)
		{
			if (IsTraitDisabled || IsTraitPaused)
				return false;

			var owner = self.Owner;
			var map = owner.World.Map;

			var exit = SelectExit(self, producee, productionType);
			var dropPos = exit != null ? self.Location + exit.Info.ExitCell : self.Location;

			CPos unadjustedStartPos;
			CPos startPos;
			CPos endPos;
			WAngle spawnFacing;

			var info = (ProductionParadropCAInfo)Info;

			if (info.SpawnType == "ClosestEdgeToHome" || info.SpawnType == "ClosestEdgeToDestination")
			{
				var bounds = map.Bounds;
				var center = new MPos(bounds.Left + bounds.Width / 2, bounds.Top + bounds.Height / 2).ToCPos(map);
				var spawnVec = owner.HomeLocation - center;

				if (info.SpawnType == "ClosestEdgeToDestination")
				{
					var distFromTopEdge = self.Location.Y;
					var distFromLeftEdge = self.Location.X;
					var distFromBottomEdge = bounds.Height - self.Location.Y;
					var distFromRightEdge = bounds.Width - self.Location.X;
					var halfMapHeight = bounds.Height / 2;
					var halfMapWidth = bounds.Width / 2;

					if (distFromTopEdge <= distFromLeftEdge && distFromTopEdge <= distFromBottomEdge && distFromTopEdge <= distFromRightEdge)
					{
						unadjustedStartPos = new CPos(self.Location.X, self.Location.Y - halfMapHeight);
						startPos = new CPos(unadjustedStartPos.X, unadjustedStartPos.Y - 10);
					}
					else if (distFromRightEdge <= distFromBottomEdge && distFromRightEdge <= distFromLeftEdge)
					{
						unadjustedStartPos = new CPos(self.Location.X + halfMapWidth, self.Location.Y);
						startPos = new CPos(unadjustedStartPos.X + 29, unadjustedStartPos.Y);
					}
					else if (distFromBottomEdge <= distFromLeftEdge)
					{
						unadjustedStartPos = new CPos(self.Location.X, self.Location.Y + halfMapHeight);
						startPos = new CPos(unadjustedStartPos.X, unadjustedStartPos.Y + 10);
					}
					else
					{
						unadjustedStartPos = new CPos(self.Location.X - halfMapWidth, self.Location.Y);
						startPos = new CPos(unadjustedStartPos.X, unadjustedStartPos.Y);
					}
				}
				else
				{
					unadjustedStartPos = startPos = owner.HomeLocation + spawnVec * (Exts.ISqrt((bounds.Height * bounds.Height + bounds.Width * bounds.Width) / (4 * spawnVec.LengthSquared)));
				}

				endPos = startPos;

				var spawnDirection = new WVec((self.Location - startPos).X, (self.Location - startPos).Y, 0);
				spawnFacing = spawnDirection.Yaw;
			}
			else
			{
				// Start a fixed distance away: the width of the map.
				// This makes the production timing independent of spawnpoint
				unadjustedStartPos = startPos = dropPos + new CVec(owner.World.Map.Bounds.Width, 0);
				endPos = new CPos(owner.World.Map.Bounds.Left - 5, dropPos.Y);
				spawnFacing = info.Facing;
			}
			
			foreach (var notify in self.TraitsImplementing<INotifyDelivery>())
				notify.IncomingDelivery(self);

			var actorType = info.ActorType;

			owner.World.AddFrameEndTask(w =>
			{
				if (!self.IsInWorld || self.IsDead)
				{
					owner.PlayerActor.Trait<PlayerResources>().GiveCash(refundableValue);
					return;
				}

				var altitude = self.World.Map.Rules.Actors[actorType].TraitInfo<AircraftInfo>().CruiseAltitude;
				var actor = w.CreateActor(actorType, new TypeDictionary
				{
					new CenterPositionInit(w.Map.CenterOfCell(startPos) + new WVec(WDist.Zero, WDist.Zero, altitude)),
					new OwnerInit(owner),
					new FacingInit(spawnFacing),
				});

				var dynamicSpeedMultiplier = actor.TraitOrDefault<DynamicSpeedMultiplier>();

				if (info.ProportionalSpeed && info.ProportionalSpeedBaseDistance.Length > 0 && dynamicSpeedMultiplier != null)
				{
					var travelDistance = (float)((w.Map.CenterOfCell(unadjustedStartPos) - self.CenterPosition).Length);

					var baseDistance = (float)info.ProportionalSpeedBaseDistance.Length;
					var multiplier = (int)Math.Round(travelDistance / baseDistance * 100);

					if (multiplier > info.ProportionalSpeedMaximum)
						multiplier = info.ProportionalSpeedMaximum;
					else if (multiplier < info.ProportionalSpeedMinimum)
						multiplier = info.ProportionalSpeedMinimum;

					dynamicSpeedMultiplier.SetModifier(multiplier);
				}

				actor.QueueActivity(new Fly(actor, Target.FromCell(w, dropPos)));
				actor.QueueActivity(new CallFunc(() =>
				{
					if (!self.IsInWorld || self.IsDead)
					{
						owner.PlayerActor.Trait<PlayerResources>().GiveCash(refundableValue);
						return;
					}

					foreach (var cargo in self.TraitsImplementing<INotifyDelivery>())
						cargo.Delivered(self);

					self.World.AddFrameEndTask(ww => DoProduction(self, producee, exit?.Info, productionType, inits));
					Game.Sound.Play(SoundType.World, info.ChuteSound, self.CenterPosition);
					Game.Sound.PlayNotification(self.World.Map.Rules, self.Owner, "Speech", info.ReadyAudio, self.Owner.Faction.InternalName);
					TextNotificationsManager.AddTransientLine(self.Owner, info.ReadyTextNotification);
				}));

				actor.QueueActivity(new Fly(actor, Target.FromCell(w, endPos)));
				actor.QueueActivity(new RemoveSelf());
			});

			return true;
		}

		public override void DoProduction(Actor self, ActorInfo producee, ExitInfo exitinfo, string productionType, TypeDictionary inits)
		{
			var exit = CPos.Zero;
			var exitLocations = new List<CPos>();

			var info = (ProductionParadropCAInfo)Info;
			var actorType = info.ActorType;

			var altitude = self.World.Map.Rules.Actors[actorType].TraitInfo<AircraftInfo>().CruiseAltitude;

			// Clone the initializer dictionary for the new actor
			var td = new TypeDictionary();
			foreach (var init in inits)
				td.Add(init);

			if (self.OccupiesSpace != null)
			{
				exit = self.Location;
				if (exitinfo != null)
					exit += exitinfo.ExitCell;

				var spawn = self.World.Map.CenterOfCell(exit) + new WVec(WDist.Zero, WDist.Zero, altitude);
				var to = self.World.Map.CenterOfCell(exit);

				var initialFacing = (exitinfo != null && exitinfo.Facing.HasValue) ? exitinfo.Facing.Value : (to - spawn).Yaw;

				exitLocations = rp.Value != null && rp.Value.Path.Count > 0 ? rp.Value.Path : new List<CPos> { exit };

				td.Add(new LocationInit(exit));
				td.Add(new CenterPositionInit(spawn));
				td.Add(new FacingInit(initialFacing));
				td.Add(new CreationActivityDelayInit(exitinfo == null ? 0 : exitinfo.ExitDelay));
			}

			self.World.AddFrameEndTask(w =>
			{
				var newUnit = self.World.CreateActor(producee.Name, td);
				newUnit.Trait<Parachutable>().IgnoreActor = self;

				var move = newUnit.TraitOrDefault<IMove>();
				if (move != null)
					foreach (var cell in exitLocations)
						newUnit.QueueActivity(new AttackMoveActivity(newUnit, () => move.MoveTo(cell, 1, evaluateNearestMovableCell: true, targetLineColor: Color.OrangeRed)));

				if (!self.IsDead)
					foreach (var t in self.TraitsImplementing<INotifyProduction>())
						t.UnitProduced(self, newUnit, exit);

				var notifyOthers = self.World.ActorsWithTrait<INotifyOtherProduction>();
				foreach (var notify in notifyOthers)
					notify.Trait.UnitProducedByOther(notify.Actor, self, newUnit, productionType, td);
			});
		}
	}
}
