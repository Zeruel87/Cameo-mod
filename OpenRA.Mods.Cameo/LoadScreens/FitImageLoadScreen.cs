#region Copyright & License Information

/*
 * Copyright 2007-2020 The OpenRA Developers (see AUTHORS)
 * This file is part of OpenRA, which is free software. It is made
 * available to you under the terms of the GNU General Public License
 * as published by the Free Software Foundation, either version 3 of
 * the License, or (at your option) any later version. For more
 * information, see COPYING.
 */

#endregion

using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Linq;
using System.Numerics;
using OpenRA.FileSystem;
using OpenRA.Graphics;
using OpenRA.Mods.Cameo.Traits;
using OpenRA.Mods.Common.LoadScreens;
using OpenRA.Primitives;

namespace OpenRA.Mods.Cameo.LoadScreens
{
	public sealed class FitImageLoadScreen : SheetLoadScreen
	{
		const double NewSessionGapSeconds = 5.0;

		// On the very first load the splash plays a short intro, then hands off to the normal randomized loading
		// screen: FadingIn -> Holding -> (hard cut: retire splash, swap image at full) -> Done. The hand-off is a
		// CUT, not a fade: the random screen is held STATIC through the heavy blocking-load window
		// (LoadSequences/LoadSprites, ~17s) where Display() isn't called for 1-2s — a static image can't stall,
		// but a fade there freezes mid-ramp. The fade-IN is smooth only because it runs in the early, checkpoint-
		// dense phase before that window. After Done it behaves like any normal loadscreen. Non-splash: start Done.
		enum IntroPhase { FadingIn, Holding, Done }

		// Fade-IN is wall-clock based and deliberately long: at startup the OS/compositor shows the freshly-
		// created window as black for the first ~1-2.5s before it presents our composited frames. A short fade
		// is entirely consumed inside that invisible cold-start window, so the splash appears to "pop" to full.
		// A longer fade keeps the tail ramping once the window is actually visible. Spec-robust: cold-start
		// latency is roughly OS-fixed (not CPU-scaled), and slower machines load longer => more fade time.
		// NOTE: this is ~2s longer than the *visible* fade-in. The first ~2s is spent inside the cold-start black,
		// so 4.0 here yields a ~2s visible ramp. For a literal 2s fade-in, set this to 2.0 (it will mostly pop).
		const double SplashFadeSeconds = 4.0;

		// Hold the fully-lit splash for a beat before cutting to the loading screen.
		const double SplashHoldSeconds = 4.0;

		// Cap how much alpha can advance per painted frame so a single long blocking load between paints
		// can't skip the fade-in in one step — keeps it visibly stepping even if checkpoints are sparse.
		const float MaxAlphaStepPerFrame = 0.06f;

		readonly Stopwatch phaseTimer = new Stopwatch();
		IntroPhase phase = IntroPhase.Done;
		float introAlpha;

		// True once the initial shellmap (menu background) has finished loading — i.e. the first, cold load is
		// over. Re-randomization is suppressed entirely until then, because that cold load has several
		// multi-second blocking gaps (LoadSequences, LoadSprites) that the gap heuristic would otherwise mistake
		// for new sessions and flip the screen mid-load (the "two loading screens on startup" bug). Set from
		// Game.OnShellmapLoaded, which fires right after the shellmap load completes. Warm later loads re-randomize.
		bool shellmapLoaded;

		Vector2 scale;
		Vector2 logoPos;
		Sprite logo;

		Sheet lastSheet;
		int lastDensity;
		Size lastResolution;

		// Owned sheet — we bypass the base class's private sheet cache so we can swap images per session.
		string[] images;
		string splashImage;
		string currentImage;
		Sheet ownSheet;

		static bool splashShown;

		readonly Stopwatch timeSinceLastDisplay = new Stopwatch();
		readonly Stopwatch sinceLastPaint = new Stopwatch();

		[FluentReference]
		const string Loading = "loadscreen-loading";
		string[] messages = Array.Empty<string>();
		string text;

		public override void Init(Manifest manifest, IReadOnlyFileSystem fileSystem)
		{
			base.Init(manifest, fileSystem);

			// Re-apply the "random" UI colour theme on every boot, before ChromeProvider loads the
			// chrome sheets, so a fresh colour shows this session. Concrete themes are already the
			// active files (copied when chosen in Settings), so they need no per-boot work.
			if (Game.Settings.GetOrCreate<CameoSettings>(null).UITheme == CyberintelThemes.Random)
				CyberintelThemes.Apply(CyberintelThemes.Random, fileSystem);

			var info = Info;

			if (info.TryGetValue("SplashImage", out var splash))
				splashImage = splash.Trim();

			if (info.TryGetValue("Image", out var raw))
			{
				images = raw.Contains(',')
					? raw.Split(',').Select(x => x.Trim()).ToArray()
					: new[] { raw };

				// Prevent the base class from loading + caching its own sheet; we manage one ourselves.
				info.Remove("Image");

				// Show splash on the very first load ever; fall back to random if none defined or already shown.
				if (!splashShown && splashImage != null)
				{
					currentImage = splashImage;
					splashShown = true;

					// Kick off the splash intro state machine. Non-splash loads stay at Done (no intro).
					phase = IntroPhase.FadingIn;
				}
				else
					currentImage = images[Game.CosmeticRandom.Next(images.Length)];
			}

			messages = FluentProvider.GetMessage(Loading).Split('$').Select(x => x.Trim()).ToArray();

			if (messages.Length > 0)
				text = messages.Random(Game.CosmeticRandom);

			// Fires once the initial shellmap finishes loading; until then we keep one loading screen (see field).
			Game.OnShellmapLoaded += MarkShellmapLoaded;
		}

		void MarkShellmapLoaded()
		{
			shellmapLoaded = true;
		}

		public override void Display()
		{
			if (Game.Renderer == null)
				return;

			// The base SheetLoadScreen caps load-screen repaints at 5 FPS to avoid stealing CPU from loading,
			// which makes a fade visibly step ~once per 200ms. While the splash fade-in is in progress, repaint as
			// fast as loading checkpoints allow (up to 60 FPS) so the ramp is smooth; during the static hold and
			// once the intro is Done (or this isn't the splash) fall back to the lazy 5 FPS. We reimplement rather
			// than call base because this screen manages its own sheet and ignores the base's cached one.
			var fading = phase == IntroPhase.FadingIn;
			var minInterval = fading ? 1 / 60.0 : 0.2;
			if (sinceLastPaint.IsRunning && sinceLastPaint.Elapsed.TotalSeconds < minInterval)
				return;

			sinceLastPaint.Restart();

			Game.Renderer.BeginUI();
			DisplayInner(Game.Renderer, null, 1);
			Game.Renderer.EndFrame(new NullInputHandler());
		}

		public override void DisplayInner(Renderer r, Sheet s, int density)
		{
			// Re-randomize when DisplayInner hasn't fired for a while — i.e. the player was at the menu between loads.
			// Gated to Done AND shellmapLoaded: the first (cold) load has several multi-second blocking gaps
			// (LoadSequences, LoadSprites) that would otherwise look like new sessions and flip the screen mid-load,
			// so we suppress re-randomization entirely until the initial shellmap has loaded (see shellmapLoaded).
			// Warm later loads re-randomize normally.
			var isNewSession = phase == IntroPhase.Done && shellmapLoaded && timeSinceLastDisplay.Elapsed.TotalSeconds > NewSessionGapSeconds;
			timeSinceLastDisplay.Restart();

			if (isNewSession)
			{
				if (messages.Length > 0)
					text = messages.Random(Game.CosmeticRandom);

				if (images != null && images.Length > 0)
				{
					var pick = images[Game.CosmeticRandom.Next(images.Length)];

					// Only churn the sheet when the pick actually changes — same image = zero I/O, zero GPU upload.
					if (pick != currentImage)
					{
						// Dispose first to keep peak GPU memory at exactly 1 sheet (no brief 2-sheet overlap).
						ownSheet?.Dispose();
						ownSheet = null;
						currentImage = pick;
					}
				}
			}

			// Drive the splash intro BEFORE loading the sheet, so the hand-off (which swaps currentImage at the end
			// of the hold) takes effect this same frame: the new image loads just below and its logo is rebuilt, so
			// we never draw a sprite backed by a sheet we just disposed (that would flash recycled GPU memory —
			// e.g. garbage glyphs). The fade-in uses a wall-clock target clamped by a per-frame cap so a long
			// blocking load between paints can't jump the ramp. Done => full alpha.
			var alpha = 1f;
			switch (phase)
			{
				case IntroPhase.FadingIn:
					if (!phaseTimer.IsRunning)
						phaseTimer.Start();

					// Ramp toward 1 over SplashFadeSeconds, but no faster than the per-frame cap.
					var target = (float)Math.Min(1.0, phaseTimer.Elapsed.TotalSeconds / SplashFadeSeconds);
					introAlpha = Math.Min(target, introAlpha + MaxAlphaStepPerFrame);
					alpha = introAlpha;
					if (introAlpha >= 1f)
					{
						phase = IntroPhase.Holding;
						phaseTimer.Restart();
					}

					break;

				case IntroPhase.Holding:
					if (phaseTimer.Elapsed.TotalSeconds >= SplashHoldSeconds)
					{
						// Hard-cut hand-off: retire the splash and swap to a random loading screen, shown at full.
						// A cut, not a fade — the random screen is then held static through the heavy blocking-load
						// window, where a fade would freeze. The new sheet loads and the logo rebuilds just below
						// this same frame, so the cut is one clean frame: no black gap, no disposed-sheet draw.
						ownSheet?.Dispose();
						ownSheet = null;

						if (images != null && images.Length > 0)
							currentImage = images[Game.CosmeticRandom.Next(images.Length)];

						phase = IntroPhase.Done;
					}

					break;
			}

			if (ownSheet == null && currentImage != null)
			{
				using (var stream = fileSystem.Open(Platform.ResolvePath(currentImage)))
				{
					ownSheet = new Sheet(SheetType.BGRA, stream);
					ownSheet.GetTexture().ScaleFilter = TextureScaleFilter.Linear;
				}
			}

			var sheet = ownSheet ?? s;
			if (sheet == null)
				return;

			if (sheet != lastSheet || density != lastDensity)
			{
				lastSheet = sheet;
				lastDensity = density;

				var rect = new Rectangle(0, 0, sheet.Size.Width, sheet.Size.Height);
				scale = new Vector2(r.Resolution.Width / (float)sheet.Size.Width,
					(float)r.Resolution.Height / (float)sheet.Size.Height);

				logo = scale.X > scale.Y
					? new Sprite(sheet, rect, TextureChannel.RGBA, scale.Y)
					: new Sprite(sheet, rect, TextureChannel.RGBA, scale.X);

				// Force logo position recompute now that the sheet (and therefore size) may have changed.
				lastResolution = default;
			}

			if (r.Resolution != lastResolution)
			{
				lastResolution = r.Resolution;

				logoPos = scale.X > scale.Y
					? new Vector2((r.Resolution.Width - sheet.Size.Width * scale.Y) / 2, 0)
					: new Vector2(0, (-sheet.Size.Height * scale.X + r.Resolution.Height) / 2);
			}

			// Fade by scaling the tint RGB (darkening toward black), NOT the tint alpha. The sprite shader uses
			// premultiplied-alpha blending (GL_ONE, GL_ONE_MINUS_SRC_ALPHA) and does c *= vTint, so reducing only
			// the alpha channel leaves the colour at full brightness over the black background — no visible fade.
			if (logo != null)
				r.RgbaSpriteRenderer.DrawSprite(logo, new Vector3(logoPos, 0), 1f, new Vector3(alpha, alpha, alpha), 1f);

			// Tips belong to the loading screen, not the branding splash — only draw them once we've cut to the
			// random screen (Done). Keeps the splash clean and shows each tip exactly once.
			var showTips = phase == IntroPhase.Done;
			if (r.Fonts != null && messages.Length > 0 && showTips)
			{
				// Same reasoning for text: scale the colour toward black rather than dropping its alpha.
				var lit = (int)(255 * alpha);
				var textSize = r.Fonts["Bold"].Measure(text);
				r.Fonts["Bold"].DrawTextWithContrast(text,
					new Vector2(r.Resolution.Width - textSize.X - 20, r.Resolution.Height - textSize.Y - 20),
					Color.FromArgb(lit, lit, lit), Color.Black, 2);
			}
		}

		protected override void Dispose(bool disposing)
		{
			if (disposing)
			{
				Game.OnShellmapLoaded -= MarkShellmapLoaded;
				ownSheet?.Dispose();
			}

			base.Dispose(disposing);
		}
	}
}
