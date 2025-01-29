#region Copyright & License Information
/*
 * Copyright 2015- OpenRA.Mods.AS Developers (see AUTHORS)
 * This file is a part of a third-party plugin for OpenRA, which is
 * free software. It is made available to you under the terms of the
 * GNU General Public License as published by the Free Software
 * Foundation. For more information, see COPYING.
 */
#endregion

using System.Collections.Generic;
using System.Linq;
using OpenRA.Effects;
using OpenRA.GameRules;
using OpenRA.Graphics;
using OpenRA.Mods.Common.Effects;
using OpenRA.Traits;

namespace OpenRA.Mods.CA.Projectiles
{
	public class NukeLaunchInfo : IProjectileInfo, IRulesetLoaded<WeaponInfo>
	{
		// HACK: This should be self but there's no way to a weapon to cache it's own name.
		[WeaponReference]
		[FieldLoader.Require]
		[Desc("Weapon to use for the impact.")]
		public readonly string MissileWeapon = "";

		[FieldLoader.Require]
		[Desc("Image to use for the missile.")]
		public readonly string MissileImage = "";

		[SequenceReference(nameof(MissileImage))]
		[Desc("Sprite sequence for the ascending missile.")]
		public readonly string MissileUp = "up";

		[SequenceReference(nameof(MissileImage))]
		[Desc("Sprite sequence for the descending missile.")]
		public readonly string MissileDown = "down";

		[PaletteReference("IsPlayerPalette")]
		[Desc("Palette to use for the missile weapon image.")]
		public readonly string MissilePalette = "effect";

		[Desc("Custom palette is a player palette BaseName.")]
		public readonly bool IsPlayerPalette = false;

		[Desc("Altitude offset from the target position at which the warhead should detonate.")]
		public readonly WDist DetonationAltitude = WDist.Zero;

		[Desc("Should nuke missile projectile be removed on detonation above ground.",
			"'False' will make the missile continue until it hits the ground and disappears (without triggering another explosion).")]
		public readonly bool RemoveMissileOnDetonation = true;

		[Desc("Travel time - split equally between ascent and descent.")]
		public readonly int FlightDelay = 400;

		[Desc("Visual ascent velocity in WDist / tick.")]
		public readonly WDist FlightVelocity = new WDist(512);

		[Desc("Descend immediately on the target.")]
		public readonly bool SkipAscent = false;

		[Desc("Trail animation.")]
		public readonly string TrailImage = null;

		[SequenceReference(nameof(TrailImage), allowNullImage: true)]
		[Desc("Loop a randomly chosen sequence of TrailImage from this list while this projectile is moving.")]
		public readonly string[] TrailSequences = System.Array.Empty<string>();

		[Desc("Interval in ticks between each spawned Trail animation.")]
		public readonly int TrailInterval = 1;

		[Desc("Delay in ticks until trail animation is spawned.")]
		public readonly int TrailDelay = 1;

		[PaletteReference("TrailUsePlayerPalette")]
		[Desc("Palette used to render the trail sequence.")]
		public readonly string TrailPalette = "effect";

		[Desc("Use the Player Palette to render the trail sequence.")]
		public readonly bool TrailUsePlayerPalette = false;

		public WeaponInfo WeaponInfo { get; private set; }

		void IRulesetLoaded<WeaponInfo>.RulesetLoaded(Ruleset rules, WeaponInfo info)
		{
			if (!string.IsNullOrEmpty(TrailImage) && !TrailSequences.Any())
				throw new YamlException("At least one entry in TrailSequences must be defined when TrailImage is defined.");

			WeaponInfo weapon;
			var weaponToLower = (MissileWeapon ?? string.Empty).ToLowerInvariant();
			if (!rules.Weapons.TryGetValue(weaponToLower, out weapon))
				throw new YamlException($"Weapons Ruleset does not contain an entry '{weaponToLower}'");

			WeaponInfo = weapon;
		}

		public IProjectile Create(ProjectileArgs args)
		{
			var palette = IsPlayerPalette ? MissilePalette + args.SourceActor.Owner.InternalName : MissilePalette;

			return new NukeLaunchCA(args.SourceActor.Owner, MissileImage, WeaponInfo, palette, MissileUp, MissileDown, args.Source, args.PassiveTarget,
				DetonationAltitude, RemoveMissileOnDetonation, FlightVelocity, 0, FlightDelay, SkipAscent,
				TrailImage, TrailSequences, TrailPalette, TrailUsePlayerPalette, TrailDelay, TrailInterval, args.SourceActor);
		}
	}

	public class NukeLaunchCA : IProjectile, ISpatiallyPartitionable
	{
		readonly Player firedBy;
		readonly Animation anim;
		readonly WeaponInfo weapon;
		readonly string weaponPalette;
		readonly string upSequence;
		readonly string downSequence;

		readonly WPos ascendSource;
		readonly WPos ascendTarget;
		readonly WPos descendSource;
		readonly WPos descendTarget;
		readonly WDist detonationAltitude;
		readonly bool removeOnDetonation;
		readonly int impactDelay;
		readonly int turn;
		readonly string trailImage;
		readonly string[] trailSequences;
		readonly string trailPalette;
		readonly int trailInterval;
		readonly int trailDelay;

		WPos pos;
		int ticks, trailTicks;
		int launchDelay;
		bool isLaunched;
		bool detonated;

		Actor SourceActor;

		public NukeLaunchCA(Player firedBy, string image, WeaponInfo weapon, string weaponPalette, string upSequence, string downSequence,
			WPos launchPos, WPos targetPos, WDist detonationAltitude, bool removeOnDetonation, WDist velocity, int launchDelay, int impactDelay,
			bool skipAscent,
			string trailImage, string[] trailSequences, string trailPalette, bool trailUsePlayerPalette, int trailDelay, int trailInterval,
			Actor sourceActor = null)
		{
			this.firedBy = firedBy;
			this.weapon = weapon;
			this.weaponPalette = weaponPalette;
			this.upSequence = upSequence;
			this.downSequence = downSequence;
			this.launchDelay = launchDelay;
			this.impactDelay = impactDelay;
			turn = skipAscent ? 0 : impactDelay / 2;
			this.trailImage = trailImage;
			this.trailSequences = trailSequences;
			this.trailPalette = trailPalette;
			if (trailUsePlayerPalette)
				this.trailPalette += firedBy.InternalName;

			this.trailInterval = trailInterval;
			this.trailDelay = trailDelay;
			trailTicks = trailDelay;

			var offset = new WVec(WDist.Zero, WDist.Zero, velocity * (impactDelay - turn));
			ascendSource = launchPos;
			ascendTarget = launchPos + offset;
			descendSource = targetPos + offset;
			descendTarget = targetPos;
			this.detonationAltitude = detonationAltitude;
			this.removeOnDetonation = removeOnDetonation;

			if (!string.IsNullOrEmpty(image))
				anim = new Animation(firedBy.World, image);

			pos = skipAscent ? descendSource : ascendSource;

			this.SourceActor = sourceActor;
		}

		public void Tick(World world)
		{
			if (launchDelay-- > 0)
				return;

			if (!isLaunched)
			{
				if (weapon.Report != null && weapon.Report.Length > 0)
					if (weapon.AudibleThroughFog || (!world.ShroudObscures(pos) && !world.FogObscures(pos)))
						Game.Sound.Play(SoundType.World, weapon.Report, world, pos, null, weapon.SoundVolume);

				if (anim != null)
				{
					anim.PlayRepeating(upSequence);
					world.ScreenMap.Add(this, pos, anim.Image);
				}

				isLaunched = true;
			}

			if (anim != null)
			{
				anim.Tick();

				if (ticks == turn)
					anim.PlayRepeating(downSequence);
			}

			var isDescending = ticks >= turn;
			if (!isDescending)
				pos = WPos.LerpQuadratic(ascendSource, ascendTarget, WAngle.Zero, ticks, turn);
			else
				pos = WPos.LerpQuadratic(descendSource, descendTarget, WAngle.Zero, ticks - turn, impactDelay - turn);

			if (!string.IsNullOrEmpty(trailImage) && --trailTicks < 0)
			{
				var trailPos = !isDescending ? WPos.LerpQuadratic(ascendSource, ascendTarget, WAngle.Zero, ticks - trailDelay, turn)
					: WPos.LerpQuadratic(descendSource, descendTarget, WAngle.Zero, ticks - turn - trailDelay, impactDelay - turn);
				var trailFacing = isDescending ? new WAngle(512) : WAngle.Zero;

				world.AddFrameEndTask(w => w.Add(new SpriteEffect(trailPos, trailFacing, w, trailImage, trailSequences.Random(world.SharedRandom),
					trailPalette)));

				trailTicks = trailInterval;
			}

			var dat = world.Map.DistanceAboveTerrain(pos);
			if (ticks == impactDelay || (isDescending && dat <= detonationAltitude))
				Explode(world, ticks == impactDelay || removeOnDetonation);

			if (anim != null)
				world.ScreenMap.Update(this, pos, anim.Image);

			ticks++;
		}

		void Explode(World world, bool removeProjectile)
		{
			if (removeProjectile)
				world.AddFrameEndTask(w => { w.Remove(this); w.ScreenMap.Remove(this); });

			if (detonated)
				return;

			var target = Target.FromPos(pos);
			var warheadArgs = new WarheadArgs
			{
				Weapon = weapon,
				Source = target.CenterPosition,
				SourceActor = SourceActor ??= firedBy.PlayerActor,
				WeaponTarget = target
			};

			weapon.Impact(target, warheadArgs);

			detonated = true;
		}

		public IEnumerable<IRenderable> Render(WorldRenderer wr)
		{
			if (!isLaunched || anim == null)
				return Enumerable.Empty<IRenderable>();

			return anim.Render(pos, wr.Palette(weaponPalette));
		}

		public float FractionComplete => ticks * 1f / impactDelay;
	}
}
