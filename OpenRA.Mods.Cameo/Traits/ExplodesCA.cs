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

using System.Linq;
using OpenRA.GameRules;
using OpenRA.Primitives;
using OpenRA.Mods.Common.Traits;
using OpenRA.Traits;
using OpenRA.Mods.CA.Traits;

namespace OpenRA.Mods.Cameo.Traits
{
	[Desc("This actor explodes when killed with firepower multipliers applied to the weapon.")]
	public class FireWarheadsOnDeathCAInfo : FireWarheadsOnDeathInfo
	{
		[Desc("Name of armament")]
		public readonly string WeaponName = null;

		public override object Create(ActorInitializer init) { return new FireWarheadsOnDeathCA(this, init.Self); }
	}

	public class FireWarheadsOnDeathCA : ConditionalTrait<FireWarheadsOnDeathCAInfo>, INotifyKilled, INotifyDamage
	{
		readonly IHealth health;
		BuildingInfo buildingInfo;
		Armament[] armaments;

		public FireWarheadsOnDeathCA(FireWarheadsOnDeathCAInfo info, Actor self)
			: base(info)
		{
			health = self.Trait<Health>();
		}

		protected override void Created(Actor self)
		{
			buildingInfo = self.Info.TraitInfoOrDefault<BuildingInfo>();
			armaments = self.TraitsImplementing<Armament>().ToArray();

			base.Created(self);
		}

		void INotifyKilled.Killed(Actor self, AttackInfo e)
		{
			if (IsTraitDisabled || !self.IsInWorld)
				return;

			if (self.World.SharedRandom.Next(100) > Info.Chance)
				return;

			if (!Info.DeathTypes.IsEmpty && !e.Damage.DamageTypes.Overlaps(Info.DeathTypes))
				return;

			var weapon = ChooseWeaponForExplosion(self);
			if (weapon == null)
				return;

			var args = new WarheadArgs
			{
				Weapon = weapon,
				DamageModifiers = self.TraitsImplementing<IFirepowerModifier>().Select(a => a.GetFirepowerModifier(Info.WeaponName)).ToArray(),
				Source = self.CenterPosition,
				SourceActor = Info.DamageSource == DamageSource.Self ? self : e.Attacker,
				WeaponTarget = Target.FromPos(self.CenterPosition + Info.Offset)
			};

			if (weapon.Report != null && weapon.Report.Length > 0)
			{
				var pos = self.CenterPosition;
				if (weapon.AudibleThroughFog || (!self.World.ShroudObscures(pos) && !self.World.FogObscures(pos)))
					Game.Sound.Play(SoundType.World, weapon.Report, self.World, pos, null, weapon.SoundVolume);
			}

			if (Info.Type == ExplosionType.Footprint && buildingInfo != null)
			{
				var cells = buildingInfo.OccupiedTiles(self.Location);
				foreach (var c in cells)
					weapon.Impact(Target.FromPos(self.World.Map.CenterOfCell(c) + Info.Offset), args);

				return;
			}

			// Use .FromPos since this actor is killed. Cannot use Target.FromActor
			weapon.Impact(Target.FromPos(self.CenterPosition + Info.Offset), args);
		}

		WeaponInfo ChooseWeaponForExplosion(Actor self)
		{
			if (armaments.Length == 0)
				return Info.WeaponInfo;
			else if (self.World.SharedRandom.Next(100) > Info.LoadedChance)
				return Info.EmptyWeaponInfo;

			// PERF: Avoid LINQ
			foreach (var a in armaments)
				if (!a.IsReloading)
					return Info.WeaponInfo;

			return Info.EmptyWeaponInfo;
		}

		void INotifyDamage.Damaged(Actor self, AttackInfo e)
		{
			if (Info.DamageThreshold == 0 || IsTraitDisabled || !self.IsInWorld)
				return;

			if (!Info.DeathTypes.IsEmpty && !e.Damage.DamageTypes.Overlaps(Info.DeathTypes))
				return;

			// Cast to long to avoid overflow when multiplying by the health
			var source = Info.DamageSource == DamageSource.Self ? self : e.Attacker;
			if (health.HP * 100L < Info.DamageThreshold * (long)health.MaxHP)
				self.World.AddFrameEndTask(w => self.Kill(source, e.Damage.DamageTypes));
		}
	}
}
