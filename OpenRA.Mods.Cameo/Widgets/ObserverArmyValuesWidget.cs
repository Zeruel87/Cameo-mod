#region Copyright & License Information
/*
 * Ported to Cameo from OpenRA Combined Arms (github.com/Inq8/CAmod), which is
 * free software under the GNU General Public License. See COPYING.
 *
 * Cameo changes: namespace OpenRA.Mods.CA.* -> OpenRA.Mods.Cameo.*.
 *
 * Draws the total `Valued.Cost` of the CURRENT SELECTION, broken down per owning
 * player and sorted by value. Because it groups by owner rather than assuming one,
 * a spectator can box-select both armies at once and read both totals — which is
 * the whole point of it for observers.
 */
#endregion

using System.Collections.Generic;
using System.Linq;
using OpenRA.Graphics;
using OpenRA.Mods.Common.Traits;
using OpenRA.Mods.Common.Widgets;
using OpenRA.Primitives;
using OpenRA.Widgets;

namespace OpenRA.Mods.Cameo.Widgets
{
	public class ObserverArmyValuesWidget : Widget
	{
		public readonly string HeadingText = "Selected Unit Values";
		public readonly string HeadingFont = "Regular";
		public readonly string Font = "Bold";
		public readonly TextAlign Align = TextAlign.Right;
		public readonly int ReplayYPosModifier = 0;

		readonly SpriteFont font;
		readonly SpriteFont headingFont;
		readonly Color bgDark;
		List<ArmyValue> armyValues;

		int selectionHash;
		readonly World world;

		[ObjectCreator.UseCtor]
		public ObserverArmyValuesWidget(World world)
		{
			bgDark = ChromeMetrics.Get<Color>("TextContrastColorDark");
			font = Game.Renderer.Fonts[Font];
			headingFont = Game.Renderer.Fonts[HeadingFont];
			this.world = world;
			armyValues = new List<ArmyValue>();
		}

		public override void Initialize(WidgetArgs args)
		{
			base.Initialize(args);

			if (world.IsReplay)
				Bounds.Y += ReplayYPosModifier;
		}

		class ArmyValue
		{
			public string PlayerName;
			public Color Color;
			public int Value;
		}

		public override void Tick()
		{
			if (selectionHash == world.Selection.Hash)
				return;

			Update();
			selectionHash = world.Selection.Hash;
		}

		void Update()
		{
			armyValues.Clear();

			var selectedActorPlayers = world.Selection.Actors.GroupBy(a => a.Owner).Select(g => g.First().Owner);

			foreach (var p in selectedActorPlayers)
			{
				var valuedTraits = world.Selection.Actors.Where(a => a.Owner == p).SelectMany(a => a.Info.TraitInfos<ValuedInfo>());
				var totalValue = 0;
				foreach (var v in valuedTraits)
					totalValue += v.Cost;

				var value = new ArmyValue
				{
					PlayerName = p.ResolvedPlayerName,
					Color = p.Color,
					Value = totalValue
				};

				armyValues.Add(value);
			}

			armyValues = armyValues.OrderByDescending(v => v.Value).ToList();
		}

		public override void Draw()
		{
			if (!IsVisible() || !armyValues.Any())
				return;

			var y = 0;
			var headingTextSize = headingFont.Measure(HeadingText);
			var headingLocation = CalcTextLocation(y, headingTextSize);
			headingFont.DrawTextWithShadow(HeadingText, headingLocation, Color.White, bgDark, bgDark, 1);
			y += (headingTextSize.Y + 6);

			foreach (var v in armyValues)
			{
				var text = v.PlayerName + ": $" + v.Value.ToString();
				var textSize = font.Measure(text);
				var location = CalcTextLocation(y, textSize);

				font.DrawTextWithShadow(text, location, v.Color, bgDark, bgDark, 1);
				y += (font.Measure(text).Y + 5);
			}
		}

		float2 CalcTextLocation(int y, int2 textSize)
		{
			var location = new float2(Bounds.X, Bounds.Y + y);

			if (Align == TextAlign.Center)
				location += new int2((Bounds.Width - textSize.X) / 2, 0);

			if (Align == TextAlign.Right)
				location += new int2(Bounds.Width - textSize.X, 0);

			return location;
		}
	}
}
