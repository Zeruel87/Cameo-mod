#region Copyright & License Information
/*
 * Ported to Cameo from OpenRA Combined Arms (github.com/Inq8/CAmod), which is
 * free software under the GNU General Public License. See COPYING.
 *
 * Cameo changes: namespace OpenRA.Mods.CA.* -> OpenRA.Mods.Cameo.*.
 */
#endregion

using System;
using System.Collections.Generic;
using OpenRA.Mods.Common.Widgets;
using OpenRA.Network;
using OpenRA.Widgets;

namespace OpenRA.Mods.Cameo.Widgets.Logic
{
	public class ReplayControlBarLogicCameo : ChromeLogic
	{
		// ⭐ ONE TABLE, ONE LOOP. The CA original repeats an identical eight-line block per
		// speed, so adding a step there means editing the enum, the dictionary AND the body.
		// Here a speed is one row.
		//
		// ⚠ THE NUMBER IS A TIMESTEP MULTIPLIER, SO SMALLER IS FASTER. It scales
		// `world.Timestep`, which is the milliseconds per tick — 2x playback is 0.5, not 2.
		// Getting this backwards silently makes every button do the opposite.
		//
		// Only four replay hotkeys exist engine-side (Slow/Regular/Fast/Max), so the four new
		// intermediate steps are mouse-only. `ReplaySpeedFast` stays on 2x — its long-standing
		// meaning — rather than moving to 1.33x.
		// ⭐ THE SAME FIVE STEPS AS COMBINED ARMS, deliberately — maintainer 2026-08-22:
		// *"let us just use the same buttons and settings as CA! No need to have more buttons
		// than them."* An eight-step ladder was built first and reverted; 1.25x and 1.33x sat
		// 6.7% apart, which is not a distinction anyone can act on.
		//
		// ⚠ THE NUMBER IS A TIMESTEP MULTIPLIER, SO SMALLER IS FASTER. It scales
		// `world.Timestep`, the milliseconds per tick — 2x playback is 0.5, not 2. Getting this
		// backwards silently makes every button do the opposite.
		//
		// Kept as a table rather than CA's enum + dictionary + five copy-pasted click handlers,
		// so a step is one row and the loop below is the only place that binds a button.
		// `BUTTON_FASTER` has no hotkey in CA either: the engine defines only four
		// (Slow/Regular/Fast/Max).
		// ⛔ NEVER FASTER THAN THE "INSANE" GAME SPEED. Maintainer 2026-08-22: *"Max needs to be
		// changed so it doesn't use the max game speed but the insane game speed instead (max is
		// too fast and lags the computer so nobody can run it)."*
		//
		// mod.yaml's GameSpeeds table: Normal is Timestep 40, Insane 10, Maximum 1. The MAX row's
		// 0.001 multiplier resolved to Timestep 1 — the `maximum` speed — which is the one that
		// lags. 10 is `insane`.
		//
		// ⚠ Applied to the COMPUTED timestep, not just to the MAX row. A replay recorded at a
		// faster game speed has a smaller originalTimestep, so a plain multiplier on one row
		// would let 2x slip under the floor on a "Fastest" (20) replay. Clamping at the point of
		// computation is the only version that holds for every row and every recording speed.
		//
		// ⚠ Keep in step with mod.yaml — if the Insane speed's Timestep changes, this must too.
		const int InsaneTimestep = 10;

		static int TimestepFor(int original, float multiplier)
		{
			return Math.Max(InsaneTimestep, (int)Math.Ceiling(original * multiplier));
		}

		static readonly (string Button, float Timestep, string Label)[] Speeds =
		{
			("BUTTON_SLOW",    2f,     "0.5x"),
			("BUTTON_REGULAR", 1f,     "1x"),
			("BUTTON_FAST",    0.75f,  "1.33x"),
			("BUTTON_FASTER",  0.5f,   "2x"),
			("BUTTON_MAXIMUM", 0.001f, "MAX"),
		};

		[ObjectCreator.UseCtor]
		public ReplayControlBarLogicCameo(Widget widget, World world, OrderManager orderManager)
		{
			if (world.IsReplay)
			{
				var container = widget.Get("REPLAY_PLAYER");
				var connection = (ReplayConnection)orderManager.Connection;
				var replayNetTicks = connection.TickCount;

				var background = widget.Parent.GetOrNull("OBSERVER_CONTROL_BG");
				if (background != null)
					background.Bounds.Height += container.Bounds.Height;

				container.Visible = true;
				// index into Speeds; 1 is the 1x row
				var speed = 1;
				var originalTimestep = world.Timestep;

				// In the event the replay goes out of sync, it becomes no longer usable. For polish we permanently pause the world.
				bool IsWidgetDisabled() => orderManager.IsOutOfSync || orderManager.NetFrameNumber >= replayNetTicks;

				var pauseButton = widget.Get<ButtonWidget>("BUTTON_PAUSE");
				pauseButton.IsVisible = () => world.ReplayTimestep != 0 && !IsWidgetDisabled();
				pauseButton.OnClick = () => world.ReplayTimestep = 0;

				var playButton = widget.Get<ButtonWidget>("BUTTON_PLAY");
				playButton.IsVisible = () => world.ReplayTimestep == 0 || IsWidgetDisabled();
				playButton.OnClick = () => world.ReplayTimestep = TimestepFor(originalTimestep, Speeds[speed].Timestep);
				playButton.IsDisabled = IsWidgetDisabled;

				for (var i = 0; i < Speeds.Length; i++)
				{
					var index = i;                          // capture per iteration, not the loop var
					var button = widget.GetOrNull<ButtonWidget>(Speeds[i].Button);
					if (button == null)
						continue;                           // a chrome that omits a step still works

					button.IsHighlighted = () => speed == index;
					button.IsDisabled = IsWidgetDisabled;
					button.OnClick = () =>
					{
						speed = index;
						if (world.ReplayTimestep != 0)
							world.ReplayTimestep = TimestepFor(originalTimestep, Speeds[index].Timestep);
					};
				}
			}
		}
	}
}
