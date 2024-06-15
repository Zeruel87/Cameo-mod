using OpenRA.Traits;

namespace OpenRA.Mods.Cameo.Traits
{
	[TraitLocation(SystemActors.Player)]
	[Desc("Player trait storing mod options for Custom Formations")]
	public class CustomFormationsModOptionsInfo : TraitInfo
	{
		[PaletteDefinition]
		[FieldLoader.Require]
		[Desc("Palette name for move order tile markers.")]
		public readonly string MoveOrderTileMarkerPalette = null;

		[SequenceReference]
		[FieldLoader.Require]
		[Desc("Sprite sequence name for attack move order tile markers.")]
		public readonly string MoveOrderTileMarkerImage = "gpsdot";

		[Desc("Animation name within MoveOrderTileMarkerSequence to use as move order tile markers")]
		[FieldLoader.Require]
		public readonly string MoveOrderTileMarkerSequence = "Communications";

		[Desc("Whether to play the animation for move order tile markers (true) or use it paused (false)")]
		public readonly bool PlaysMoveOrderTileMarkerAnimation = false;

		[PaletteDefinition]
		[FieldLoader.Require]
		[Desc("Palette name for move order markers.")]
		public readonly string MoveOrderMarkerPalette = null;

		[SequenceReference]
		[FieldLoader.Require]
		[Desc("Sprite sequence name for attack move order markers.")]
		public readonly string MoveOrderMarkerImage = "gpsdot";

		[Desc("Animation name within MoveOrderTileMarkerSequence to use as move order markers")]
		[FieldLoader.Require]
		public readonly string MoveOrderMarkerSequence = "Communications";

		[Desc("Whether to play the animation for move order markers (true) or use it paused (false)")]
		public readonly bool PlaysMoveOrderMarkerAnimation = false;

		[PaletteDefinition]
		[FieldLoader.Require]
		[Desc("Palette name for attack move order tile markers.")]
		public readonly string AttackMoveOrderTileMarkerPalette = null;

		[SequenceReference]
		[FieldLoader.Require]
		[Desc("Sprite sequence name for attack move order tile markers.")]
		public readonly string AttackMoveOrderTileMarkerImage = "gpsdot";

		[Desc("Animation name within AttackMoveOrderTileMarkerSequence to use as attack move order tile markers")]
		[FieldLoader.Require]
		public readonly string AttackMoveOrderTileMarkerSequence = "Communications";

		[Desc("Whether to play the animation for attack move order tile markers (true) or use it paused (false)")]
		public readonly bool PlaysAttackMoveOrderTileMarkerAnimation = false;

		[PaletteDefinition]
		[FieldLoader.Require]
		[Desc("Palette name for attack move order markers.")]
		public readonly string AttackMoveOrderMarkerPalette = null;

		[SequenceReference]
		[FieldLoader.Require]
		[Desc("Sprite sequence name for attack move order markers.")]
		public readonly string AttackMoveOrderMarkerImage = "gpsdot";

		[Desc("Animation name within AttackMoveOrderTileMarkerSequence to use as attack move order markers")]
		[FieldLoader.Require]
		public readonly string AttackMoveOrderMarkerSequence = "Communications";

		[Desc("Whether to play the animation for attack move order markers (true) or use it paused (false)")]
		public readonly bool PlaysAttackMoveOrderMarkerAnimation = false;

		[PaletteDefinition]
		[FieldLoader.Require]
		[Desc("Palette name for assault move order tile markers.")]
		public readonly string AssaultMoveOrderTileMarkerPalette = null;

		[SequenceReference]
		[FieldLoader.Require]
		[Desc("Sprite sequence name for assault move order tile markers.")]
		public readonly string AssaultMoveOrderTileMarkerImage = "gpsdot";

		[Desc("Animation name within AssaultMoveOrderTileMarkerSequence to use as assault move order tile markers")]
		[FieldLoader.Require]
		public readonly string AssaultMoveOrderTileMarkerSequence = "Communications";

		[Desc("Whether to play the animation for assault move order tile markers (true) or use it paused (false)")]
		public readonly bool PlaysAssaultMoveOrderTileMarkerAnimation = false;

		[PaletteDefinition]
		[FieldLoader.Require]
		[Desc("Palette name for assault move order markers.")]
		public readonly string AssaultMoveOrderMarkerPalette = null;

		[SequenceReference]
		[FieldLoader.Require]
		[Desc("Sprite sequence name for assault move order markers.")]
		public readonly string AssaultMoveOrderMarkerImage = "gpsdot";

		[Desc("Animation name within AssaultMoveOrderTileMarkerSequence to use as assault move order markers")]
		[FieldLoader.Require]
		public readonly string AssaultMoveOrderMarkerSequence = "Communications";

		[Desc("Whether to play the animation for assault move order markers (true) or use it paused (false)")]
		public readonly bool PlaysAssaultMoveOrderMarkerAnimation = false;

		[PaletteDefinition]
		[FieldLoader.Require]
		[Desc("Palette name for force fire order tile markers.")]
		public readonly string ForceFireOrderTileMarkerPalette = null;

		[SequenceReference]
		[FieldLoader.Require]
		[Desc("Sprite sequence name for force fire order tile markers.")]
		public readonly string ForceFireOrderTileMarkerImage = "gpsdot";

		[Desc("Animation name within ForeceFireOrderTileMarkerSequence to use as force fire order tile markers")]
		[FieldLoader.Require]
		public readonly string ForceFireOrderTileMarkerSequence = "Communications";

		[Desc("Whether to play the animation for force fire order tile markers (true) or use it paused (false)")]
		public readonly bool PlaysForceFireOrderTileMarkerAnimation = false;

		[PaletteDefinition]
		[FieldLoader.Require]
		[Desc("Palette name for force fire order markers.")]
		public readonly string ForceFireOrderMarkerPalette = null;

		[SequenceReference]
		[FieldLoader.Require]
		[Desc("Sprite sequence name for force fire order markers.")]
		public readonly string ForceFireOrderMarkerImage = "gpsdot";

		[Desc("Animation name within ForceFireOrderTileMarkerSequence to use as force fire order markers")]
		[FieldLoader.Require]
		public readonly string ForceFireOrderMarkerSequence = "Communications";

		[Desc("Whether to play the animation for force fire order markers (true) or use it paused (false)")]
		public readonly bool PlaysForceFireOrderMarkerAnimation = false;

		public override object Create(ActorInitializer init) { return new CustomFormationsModOptions(this); }
	}

	public class CustomFormationsModOptions
	{
		readonly CustomFormationsModOptionsInfo Info;

		public CustomFormationsModOptions(CustomFormationsModOptionsInfo info)
		{
			Info = info;
		}

		public string MoveOrderTileMarkerPaletteName { get { return Info.MoveOrderTileMarkerPalette; } set { } }

		public string MoveOrderTileMarkerImageName { get { return Info.MoveOrderTileMarkerImage; } set { } }

		public string MoveOrderTileMarkerSequenceName { get { return Info.MoveOrderTileMarkerSequence; } set { } }

		public bool PlaysMoveOrderTileMarkerAnimation { get { return Info.PlaysMoveOrderTileMarkerAnimation; } set { } }

		public string MoveOrderMarkerPaletteName { get { return Info.MoveOrderMarkerPalette; } set { } }

		public string MoveOrderMarkerImageName { get { return Info.MoveOrderMarkerImage; } set { } }

		public string MoveOrderMarkerSequenceName { get { return Info.MoveOrderMarkerSequence; } set { } }

		public bool PlaysMoveOrderMarkerAnimation { get { return Info.PlaysMoveOrderMarkerAnimation; } set { } }

		public string AttackMoveOrderTileMarkerPaletteName { get { return Info.AttackMoveOrderTileMarkerPalette; } set { } }

		public string AttackMoveOrderTileMarkerImageName { get { return Info.AttackMoveOrderTileMarkerImage; } set { } }

		public string AttackMoveOrderTileMarkerSequenceName { get { return Info.AttackMoveOrderTileMarkerSequence; } set { } }

		public bool PlaysAttackMoveOrderTileMarkerAnimation { get { return Info.PlaysAttackMoveOrderTileMarkerAnimation; } set { } }

		public string AttackMoveOrderMarkerPaletteName { get { return Info.AttackMoveOrderMarkerPalette; } set { } }

		public string AttackMoveOrderMarkerImageName { get { return Info.AttackMoveOrderMarkerImage; } set { } }

		public string AttackMoveOrderMarkerSequenceName { get { return Info.AttackMoveOrderMarkerSequence; } set { } }

		public bool PlaysAttackMoveOrderMarkerAnimation { get { return Info.PlaysAttackMoveOrderMarkerAnimation; } set { } }

		public string AssaultMoveOrderTileMarkerPaletteName { get { return Info.AssaultMoveOrderTileMarkerPalette; } set { } }

		public string AssaultMoveOrderTileMarkerImageName { get { return Info.AssaultMoveOrderTileMarkerImage; } set { } }

		public string AssaultMoveOrderTileMarkerSequenceName { get { return Info.AssaultMoveOrderTileMarkerSequence; } set { } }

		public bool PlaysAssaultMoveOrderTileMarkerAnimation { get { return Info.PlaysAssaultMoveOrderTileMarkerAnimation; } set { } }

		public string AssaultMoveOrderMarkerPaletteName { get { return Info.AssaultMoveOrderMarkerPalette; } set { } }

		public string AssaultMoveOrderMarkerImageName { get { return Info.AssaultMoveOrderMarkerImage; } set { } }

		public string AssaultMoveOrderMarkerSequenceName { get { return Info.AssaultMoveOrderMarkerSequence; } set { } }

		public bool PlaysAssaultMoveOrderMarkerAnimation { get { return Info.PlaysAssaultMoveOrderMarkerAnimation; } set { } }

		public string ForceFireOrderTileMarkerPaletteName { get { return Info.ForceFireOrderTileMarkerPalette; } set { } }

		public string ForceFireOrderTileMarkerImageName { get { return Info.ForceFireOrderTileMarkerImage; } set { } }

		public string ForceFireOrderTileMarkerSequenceName { get { return Info.ForceFireOrderTileMarkerSequence; } set { } }

		public bool PlaysForceFireOrderTileMarkerAnimation { get { return Info.PlaysForceFireOrderTileMarkerAnimation; } set { } }

		public string ForceFireOrderMarkerPaletteName { get { return Info.ForceFireOrderMarkerPalette; } set { } }

		public string ForceFireOrderMarkerImageName { get { return Info.ForceFireOrderMarkerImage; } set { } }

		public string ForceFireOrderMarkerSequenceName { get { return Info.ForceFireOrderMarkerSequence; } set { } }

		public bool PlaysForceFireOrderMarkerAnimation { get { return Info.PlaysForceFireOrderMarkerAnimation; } set { } }
	}
}
