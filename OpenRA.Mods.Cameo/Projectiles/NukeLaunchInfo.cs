#region Copyright & License Information
/*
 * Copyright 2015- OpenRA.Mods.AS Developers (see AUTHORS)
 * This file is a part of a third-party plugin for OpenRA, which is
 * free software. It is made available to you under the terms of the
 * GNU General Public License as published by the Free Software
 * Foundation. For more information, see COPYING.
 */
#endregion

using System.Linq;
using OpenRA.GameRules;
using OpenRA.Graphics;
using OpenRA.Mods.Common.Effects;
using OpenRA.Traits;

namespace OpenRA.Mods.Cameo.Projectiles
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

			return new NukeLaunch(args.SourceActor.Owner, MissileImage, WeaponInfo, palette, MissileUp, MissileDown, args.Source, args.PassiveTarget,
				DetonationAltitude, RemoveMissileOnDetonation, FlightVelocity, 0, FlightDelay, SkipAscent,
				TrailImage, TrailSequences, TrailPalette, TrailUsePlayerPalette, TrailDelay, TrailInterval);
		}
	}
}
