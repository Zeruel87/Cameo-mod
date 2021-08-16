#region Copyright & License Information
/*
* Modded by Boolbada of Over Powered Mod.
* Contains some copy and paste code from OpenRA base mod.
* (Erm... hardly any by now but using OpenRA API ofcourse)
*
* Copyright 2007-2017 The OpenRA Developers (see AUTHORS)
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
using OpenRA.Activities;
using OpenRA.Mods.Common.Activities;
using OpenRA.Mods.Common.Traits;
using OpenRA.Mods.Common.Traits.Render;

using OpenRA.Primitives;
using OpenRA.Traits;

/* Works without base engine modification */

namespace OpenRA.Mods.CA.Traits
{
[Desc("Transforms cargo inside when some predefined combination is met.")]
public class CargoTransformerInfo : ITraitInfo, Requires<CargoInfo>
{
  [Desc("Unit type to emit when the combination is met")]
  public readonly Dictionary<string, string[]> Combinations;

  [Desc("The sound played when the transform stars.")]
  public readonly string[] TransformSound = null;

  [Desc("The animation sequence to play when transforming.")]
  [SequenceReference]
  public readonly string ActiveSequence = "active";

  [Desc("Radius to search for a load/unload location if the ordered cell is blocked.")]
  public readonly WDist UnloadRange = WDist.FromCells(5);

  public object Create(ActorInitializer init) { return new CargoTransformer(init.Self, this); }
}

public class CargoTransformer : INotifyPassengerEntered, INotifyPassengerExited
{
  public readonly CargoTransformerInfo Info;
  readonly Lazy<RallyPoint> rp;
  Cargo cargo;

  public CargoTransformer(Actor self, CargoTransformerInfo info)
  {
    Info = info;
    cargo = self.Trait<Cargo>(); // I required CargoInfo so this will always work.
    rp = Exts.Lazy(() => self.IsDead ? null : self.TraitOrDefault<RallyPoint>());
  }

  void SpawnUnit(Actor self, string unit)
  {
    // Play transformation sound
    Game.Sound.Play(SoundType.World, Info.TransformSound.Random(self.World.SharedRandom), self.CenterPosition);

    // Kill cargo and spawn new unit
    while (!cargo.IsEmpty(self))
    {
      var c = cargo.Unload(self);
      c.Dispose();
    }

    /*
    // I attempted "production" but it wasn't a good idea.
    // When the exit is blocked, the unit disappears.
    // Blocking is better handled by unload.
    */

    var td = new TypeDictionary
    {
      new OwnerInit(self.Owner),
    };
    var newUnit = self.World.CreateActor(false, unit.ToLowerInvariant(), td);
    cargo.Load(self, newUnit);

    var wsb = self.TraitOrDefault<WithSpriteBody>();
    if (wsb != null && wsb.DefaultAnimation.HasSequence(Info.ActiveSequence))
      wsb.PlayCustomAnimation(self, Info.ActiveSequence, () => self.QueueActivity(new UnloadCargo(self, Info.UnloadRange, true)));
  }

  void INotifyPassengerExited.OnPassengerExited(Actor self, Actor passenger)
  {
    var exitLocations = new List<CPos>();

    // Make the unloaded passenger move to rally point.
    self.World.AddFrameEndTask(w1 =>
    {
      if (passenger.Disposed)
        return;

      if (rp.Value != null && rp.Value.Path.Count > 0)
      {
          exitLocations = rp.Value.Path;

          var move = passenger.TraitOrDefault<IMove>();
          if (move != null)
            foreach (var cell in exitLocations)
              passenger.QueueActivity(new AttackMoveActivity(passenger, () => move.MoveTo(cell, 1, evaluateNearestMovableCell: true, targetLineColor: Color.OrangeRed)));
      }
    });
  }

  void INotifyPassengerEntered.OnPassengerEntered(Actor self, Actor passenger)
  {
    // get rules entry name for each passenger.
    var names = cargo.Passengers.OrderBy(x => x.Info.Name).Select(x => x.Info.Name).ToArray();

    // Lets examine the contents.
    foreach (var kv in Info.Combinations)
    {
      if (Enumerable.SequenceEqual(names, kv.Value))
      {
        SpawnUnit(self, kv.Key);
        return; // no need to examine any other combination.
      }
    }
  }
}
}
