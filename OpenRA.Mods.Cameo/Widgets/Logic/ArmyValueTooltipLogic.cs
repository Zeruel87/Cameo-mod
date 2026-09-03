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

using System;
using OpenRA.Mods.Common.Traits;
using OpenRA.Mods.Common.Widgets;
using OpenRA.Widgets;

namespace OpenRA.Mods.Cameo.Widgets.Logic
{
	// Very similar to ArmyTooltipLogic
	public class ArmyValueTooltipLogic : ChromeLogic
	{
		[ObjectCreator.UseCtor]
		public ArmyValueTooltipLogic(Widget widget, TooltipContainerWidget tooltipContainer, Func<ArmyUnit> getTooltipUnit, Func<string> getDesc = null)
		{
			widget.IsVisible = () => getTooltipUnit() != null;
			var nameLabel = widget.Get<LabelWidget>("NAME");
			var descLabel = widget.Get<LabelWidget>("DESC");

			var font = Game.Renderer.Fonts[nameLabel.Font];
			var descFont = Game.Renderer.Fonts[descLabel.Font];

			ArmyUnit lastArmyUnit = null;
			var descLabelPadding = descLabel.Bounds.Height;

			tooltipContainer.BeforeRender = () =>
			{
				var armyUnit = getTooltipUnit();

				if (armyUnit == null || armyUnit == lastArmyUnit)
					return;

				var tooltip = armyUnit.TooltipInfo;
				var name = tooltip?.Name ?? armyUnit.ActorInfo.Name;
				nameLabel.Text = name;
				var nameSize = font.Measure(name);

				if (getDesc != null)
				{
					descLabel.Text = getDesc();
				}
				else
				{
					var buildable = armyUnit.BuildableInfo;
					descLabel.Text = buildable.Description.Replace("\\n", "\n");
				}

				var descSize = descFont.Measure(descLabel.Text);
				descLabel.Bounds.Width = descSize.X;
				descLabel.Bounds.Height = descSize.Y + descLabelPadding;

				var leftWidth = Math.Max(nameSize.X, descSize.X);

				widget.Bounds.Width = leftWidth + 2 * nameLabel.Bounds.X;

				// Set the bottom margin to match the left margin
				var leftHeight = descLabel.Bounds.Bottom + descLabel.Bounds.X;

				widget.Bounds.Height = leftHeight;

				lastArmyUnit = armyUnit;
			};
		}
	}
}
