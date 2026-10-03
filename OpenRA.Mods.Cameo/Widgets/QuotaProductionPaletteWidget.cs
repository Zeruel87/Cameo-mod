#region Copyright & License Information
/*
 * Cameo mod
 */
#endregion

using System.Linq;
using System.Numerics;
using OpenRA;
using OpenRA.Graphics;
using OpenRA.Mods.CA.Widgets;
using OpenRA.Mods.Cameo.Traits;
using OpenRA.Mods.Common.Traits;
using OpenRA.Mods.Common.Widgets;
using OpenRA.Network;
using OpenRA.Primitives;
using OpenRA.Widgets;

namespace OpenRA.Mods.Cameo.Widgets
{
	public class QuotaProductionPaletteWidget : ProductionPaletteCAWidget
	{
		public readonly string MainStructureProductionGroup = "Building";
		public readonly Color StructureCountColor = Color.Lime;
		public readonly int2 StructureCountMargin = new(5, 4);
		public readonly int HoverHeaderHeight = 12;
		public readonly Color HoverHeaderBackgroundColor = Color.FromArgb(224, 24, 24, 24);
		public readonly Color HoverHeaderBorderColor = Color.FromArgb(255, 194, 160, 64);
		public readonly Color HoverHeaderTextColor = Color.FromArgb(255, 255, 224, 128);
		public readonly string HoverHeaderFont = "TinyBold";
		public readonly float MutualExclusionOutlineWidth = 2f;

		SpriteFont quotaFont;
		SpriteFont hoverHeaderFont;
		SpriteFont symbolFont;
		readonly CameoSettings cameoSettings;

		[ObjectCreator.UseCtor]
		public QuotaProductionPaletteWidget(ModData modData, OrderManager orderManager, World world, WorldRenderer worldRenderer)
			: base(modData, orderManager, world, worldRenderer)
		{
			cameoSettings = modData.GetSettings<CameoSettings>();
		}

		public override void Initialize(WidgetArgs args)
		{
			base.Initialize(args);
			quotaFont = Game.Renderer.Fonts[OverlayFont];
			hoverHeaderFont = Game.Renderer.Fonts[HoverHeaderFont];
			Game.Renderer.Fonts.TryGetValue(SymbolsFont, out symbolFont);
		}

		public override bool HandleMouseInput(MouseInput mi)
		{
			var quotaManager = World.LocalPlayer?.PlayerActor?.TraitOrDefault<QuotaProductionManager>();
			if (quotaManager == null || !quotaManager.Enabled || CurrentQueue == null)
				return base.HandleMouseInput(mi);

			if (mi.Event == MouseInputEvent.Move || mi.Event == MouseInputEvent.Scroll)
				return base.HandleMouseInput(mi);

			var icon = icons.Where(i => i.Key.Contains(mi.Location))
				.Select(i => i.Value).FirstOrDefault();

			if (icon == null)
				return false;

			if (mi.Event != MouseInputEvent.Down)
				return true;

			var buildable = CurrentQueue.BuildableItems().FirstOrDefault<ActorInfo>(a => a.Name == icon.Name);
			if (buildable == null)
			{
				Game.Sound.PlayNotification(World.Map.Rules, World.LocalPlayer, "Sounds", ClickDisabledSound, null);
				return true;
			}

			if (!buildable.HasTraitInfo<MobileInfo>() && !buildable.HasTraitInfo<AircraftInfo>())
				return base.HandleMouseInput(mi);

			var count = mi.Modifiers.HasModifier(Modifiers.Shift) ? 5 : 1;

			if (mi.Button == MouseButton.Left)
			{
				quotaManager.AdjustQuota(icon.Name, count);
				Game.Sound.PlayNotification(World.Map.Rules, World.LocalPlayer, "Sounds", ClickSound, null);
				return true;
			}

			if (mi.Button == MouseButton.Right)
			{
				quotaManager.AdjustQuota(icon.Name, -count);
				Game.Sound.PlayNotification(World.Map.Rules, World.LocalPlayer, "Sounds", ClickSound, null);
				return true;
			}

			return base.HandleMouseInput(mi);
		}

		public override void Draw()
		{
			base.Draw();

			DrawHoverHeader();
			DrawMutualExclusionOutlines();

			var localPlayer = World.LocalPlayer;
			if (localPlayer == null || CurrentQueue == null)
				return;

			if (cameoSettings.ShowBuildingCounts && CurrentQueue.Info.Group == MainStructureProductionGroup)
			{
				var structureCounts = World.ActorsHavingTrait<Building>()
					.Where(a => a.Owner == localPlayer && !a.IsDead)
					.GroupBy(a => a.Info.Name)
					.ToDictionary(g => g.Key, g => g.Count());

				foreach (var icon in icons.Values)
				{
					if (!structureCounts.TryGetValue(icon.Name, out var count))
						continue;

					var text = count.ToStringInvariant();
					var textSize = quotaFont.Measure(text);
					var pos = icon.Pos + new Vector2(
						IconSize.X - textSize.X - StructureCountMargin.X,
						IconSize.Y - textSize.Y - StructureCountMargin.Y);
					quotaFont.DrawTextWithContrast(text, pos, StructureCountColor, Color.Black, 1);
				}
			}

			var quotaManager = localPlayer.PlayerActor.TraitOrDefault<QuotaProductionManager>();
			if (quotaManager == null || !quotaManager.Enabled)
				return;

			foreach (var icon in icons.Values)
			{
				var quota = quotaManager.GetQuota(icon.Name);
				if (quota <= 0)
					continue;

				var alive = quotaManager.GetAliveCount(icon.Name);
				var text = $"{alive}/{quota}";
				var textSize = quotaFont.Measure(text);
				var pos = icon.Pos + new Vector2(IconSize.X - textSize.X - 1, IconSize.Y - textSize.Y - 1);
				quotaFont.DrawTextWithContrast(text, pos, Color.Cyan, Color.Black, 1);
			}
		}

		void DrawMutualExclusionOutlines()
		{
			if (CurrentQueue == null)
				return;

			var hoveredIcon = icons.Where(i => i.Key.Contains(Viewport.LastMousePos))
				.Select(i => i.Value).FirstOrDefault();
			var hoveredGroup = hoveredIcon?.Actor.TraitInfoOrDefault<ProductionIconMutualExclusionInfo>()?.Group;
			if (string.IsNullOrEmpty(hoveredGroup))
				return;

			var inset = MutualExclusionOutlineWidth / 2f;
			foreach (var icon in icons.Values)
			{
				var mutualExclusion = icon.Actor.TraitInfoOrDefault<ProductionIconMutualExclusionInfo>();
				if (mutualExclusion == null || mutualExclusion.Group != hoveredGroup)
					continue;

				var topLeft = icon.Pos + new Vector2(inset, inset);
				var bottomRight = icon.Pos + IconSize.ToVector2() - new Vector2(inset + 1f, inset + 1f);
				Game.Renderer.RgbaColorRenderer.DrawRect(
					new Vector3(topLeft, 0f),
					new Vector3(bottomRight, 0f),
					MutualExclusionOutlineWidth,
					mutualExclusion.OutlineColor);
			}
		}

		void DrawHoverHeader()
		{
			if (CurrentQueue == null)
				return;

			var hoveredIcon = icons.Where(i => i.Key.Contains(Viewport.LastMousePos))
				.Select(i => i.Value).FirstOrDefault();
			if (hoveredIcon == null)
				return;

			var header = hoveredIcon.Actor.TraitInfoOrDefault<ProductionIconHoverHeaderInfo>();
			if (header == null || string.IsNullOrEmpty(header.Text))
				return;

			var headerRect = new Rectangle(
				(int)hoveredIcon.Pos.X,
				(int)hoveredIcon.Pos.Y,
				IconSize.X,
				HoverHeaderHeight);
			WidgetUtils.FillRectWithColor(headerRect, HoverHeaderBackgroundColor);
			WidgetUtils.FillRectWithColor(
				new Rectangle(headerRect.Left, headerRect.Bottom - 1, headerRect.Width, 1),
				HoverHeaderBorderColor);

			var textSize = hoverHeaderFont.Measure(header.Text);
			var textPos = hoveredIcon.Pos + new Vector2(
				(IconSize.X - textSize.X) / 2,
				(HoverHeaderHeight - textSize.Y) / 2);
			hoverHeaderFont.DrawTextWithContrast(header.Text, textPos, HoverHeaderTextColor, Color.Black, 1);

			RedrawQueueIndicator(hoveredIcon);
		}

		void RedrawQueueIndicator(ProductionIcon hoveredIcon)
		{
			var total = hoveredIcon.Queued.Count;
			if (total == 0)
				return;

			var first = hoveredIcon.Queued[0];
			var waiting = !CurrentQueue.IsProducing(first) && !first.Done;
			if (first.Infinite && symbolFont != null)
				symbolFont.DrawTextWithContrast(
					InfiniteSymbol,
					hoveredIcon.Pos + QueuedOffset,
					TextColor,
					Color.Black,
					1);
			else if (total > 1 || waiting)
				quotaFont.DrawTextWithContrast(
					total.ToStringInvariant(),
					hoveredIcon.Pos + QueuedOffset,
					TextColor,
					Color.Black,
					1);
		}
	}
}
