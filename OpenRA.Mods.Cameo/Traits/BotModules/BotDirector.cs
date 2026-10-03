#region Copyright & License Information
/*
 * Copyright (c) OpenRA Developers and Contributors
 * This file is part of OpenRA, which is free software. It is made
 * available to you under the terms of the GNU General Public License
 * as published by the Free Software Foundation, either version 3 of
 * the License, or (at your option) any later version.
 */
#endregion

using System;
using OpenRA.Mods.CA.Traits;

namespace OpenRA.Mods.Cameo.Traits.BotModules
{
	/// <summary>
	/// DI-1 (AI_DEEP_RESEARCH.md §7, DESIGN.md §19.2, AI_ARCHITECTURE.md §12.16): the
	/// L4D-Director-style pacing wave, adapted to an RTS bot — a tension value in
	/// [0,100] and a <see cref="DirectorPhase"/> advanced once per situation snapshot.
	///
	/// BuildUp: tension rises with the massed idle army (own value at or above
	/// DirectorArmyMassValue) plus impatience — one point per
	/// DirectorImpatienceTicksPerPoint ticks since the last delivered attack (since
	/// game start when none was ever launched), capped per snapshot. A thin army
	/// decays tension instead. Pressure (tension at DirectorPressureThreshold): the
	/// attack is overdue. Climax (tension at DirectorClimaxThreshold, or a launch
	/// while already Pressure): the wave is delivering. Relief: the post-attack kill
	/// window flattened (no launches and no fresh kill delta for
	/// DirectorReliefQuietTicks) or a heavy own-loss spike (DirectorLossSpikeValue)
	/// broke the wave early — tension resets to DirectorReliefTension and re-arms to
	/// BuildUp at DirectorReliefExitThreshold.
	///
	/// Every threshold crossing carries hysteresis: Pressure only relaxes
	/// DirectorHysteresis below its entry threshold, and Relief's exit sits above the
	/// reset level — the phase cannot flutter on a boundary value. Inputs are
	/// fog-honest snapshot scalars only (own army/attacks/losses, remembered
	/// windows); nothing here enumerates enemy actors. Record-only — DI-2 decides
	/// which attack-timing knob reads it.
	/// </summary>
	internal sealed class BotDirector
	{
		internal int Tension { get; private set; }
		internal DirectorPhase Phase { get; private set; } = DirectorPhase.BuildUp;

		// Last snapshot tick that launched attacks (-1 = none yet — the impatience
		// clock then runs from game start), and the last tick with attack or kill
		// action inside the current Climax (armed at entry).
		int lastAttackTick = -1;
		int climaxActionTick = -1;

		internal void Observe(int tick, int ownArmyValue, int attacksDelta, int freshKillDelta,
			int freshLossDelta, MasterAiBotModuleInfo info)
		{
			if (attacksDelta > 0)
				lastAttackTick = tick;

			var tension = Tension;
			if (ownArmyValue >= info.DirectorArmyMassValue)
			{
				tension += info.DirectorTensionRisePerSnapshot;
				var idleTicks = lastAttackTick < 0 ? Math.Max(0, tick) : Math.Max(0, tick - lastAttackTick);
				if (info.DirectorImpatienceTicksPerPoint > 0)
					tension += (int)Math.Min((long)Math.Max(0, info.DirectorImpatienceMaxPerSnapshot),
						idleTicks / info.DirectorImpatienceTicksPerPoint);
			}
			else
			{
				tension -= info.DirectorTensionDecayPerSnapshot;
			}

			tension = Math.Clamp(tension, 0, 100);
			var lossSpike = freshLossDelta >= Math.Max(0, info.DirectorLossSpikeValue);
			var phase = Phase;
			switch (phase)
			{
				case DirectorPhase.Climax:
					if (attacksDelta > 0 || freshKillDelta > 0)
						climaxActionTick = tick;
					if (lossSpike || tick - climaxActionTick >= Math.Max(0, info.DirectorReliefQuietTicks))
						EnterRelief(ref phase, ref tension, info);
					break;
				case DirectorPhase.Pressure:
					if (tension >= info.DirectorClimaxThreshold || attacksDelta > 0)
						phase = DirectorPhase.Climax;
					else if (lossSpike)
						EnterRelief(ref phase, ref tension, info);
					else if (tension < info.DirectorPressureThreshold - Math.Max(0, info.DirectorHysteresis))
						phase = DirectorPhase.BuildUp;
					break;
				case DirectorPhase.Relief:
					if (tension >= info.DirectorReliefExitThreshold)
						phase = DirectorPhase.BuildUp;
					break;
				default: // BuildUp
					if (tension >= info.DirectorClimaxThreshold)
						phase = DirectorPhase.Climax;
					else if (tension >= info.DirectorPressureThreshold)
						phase = DirectorPhase.Pressure;
					break;
			}

			if (phase == DirectorPhase.Climax && Phase != DirectorPhase.Climax)
				climaxActionTick = tick;

			Phase = phase;
			Tension = tension;
		}

		static void EnterRelief(ref DirectorPhase phase, ref int tension, MasterAiBotModuleInfo info)
		{
			phase = DirectorPhase.Relief;
			tension = Math.Clamp(info.DirectorReliefTension, 0, 100);
		}
	}
}
