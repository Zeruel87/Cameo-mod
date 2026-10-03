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

using System;
using System.Collections.Generic;

namespace OpenRA.Mods.Common.Traits
{
	readonly record struct FransGroundSecurePackageCandidate(
		uint ActorId,
		bool IsInfantry,
		int CombatValue,
		int DistanceSquared);

	readonly record struct FransGroundSecurePackageSelection(
		int[] CandidateIndexes,
		long InfantryValue,
		int InfantryCount,
		long OtherValue,
		int OfferedValue);

	delegate int FransGroundTacticalValueEvaluator(long infantryValue, int infantryCount, long otherValue);
	delegate int FransGroundSecureSurplusCostEvaluator(int selectedValue, int requiredValue);

	static class FransGroundSecurePackageSelector
	{
		public static FransGroundSecurePackageSelection Select(
			IReadOnlyList<FransGroundSecurePackageCandidate> candidates,
			int requiredValue,
			FransGroundTacticalValueEvaluator tacticalValue,
			FransGroundSecureSurplusCostEvaluator surplusCost)
		{
			ArgumentNullException.ThrowIfNull(candidates);
			ArgumentNullException.ThrowIfNull(tacticalValue);
			ArgumentNullException.ThrowIfNull(surplusCost);

			if (candidates.Count == 0)
				return new FransGroundSecurePackageSelection(Array.Empty<int>(), 0, 0, 0, 0);

			var firstInfantryIndex = -1;
			var firstOtherIndex = -1;
			for (var i = 0; i < candidates.Count && (firstInfantryIndex < 0 || firstOtherIndex < 0); i++)
			{
				if (candidates[i].IsInfantry)
					firstInfantryIndex = firstInfantryIndex < 0 ? i : firstInfantryIndex;
				else
					firstOtherIndex = firstOtherIndex < 0 ? i : firstOtherIndex;
			}

			var selectedIndexes = new List<int>(candidates.Count);
			long infantryValue = 0;
			long otherValue = 0;
			var infantryCount = 0;

			void AddCandidate(int index)
			{
				selectedIndexes.Add(index);
				var candidate = candidates[index];
				if (candidate.IsInfantry)
				{
					infantryCount++;
					infantryValue += candidate.CombatValue;
				}
				else
					otherValue += candidate.CombatValue;
			}

			// Preserve the original seed order: infantry first, then non-infantry,
			// independent of their proximity order in the candidate list.
			if (firstInfantryIndex >= 0)
				AddCandidate(firstInfantryIndex);
			if (firstOtherIndex >= 0)
				AddCandidate(firstOtherIndex);

			var offeredValue = tacticalValue(infantryValue, infantryCount, otherValue);
			if (offeredValue >= requiredValue || selectedIndexes.Count == candidates.Count)
				return BuildSelection();

			// Before the final completing actor, the original selector always consumes the
			// first remaining candidate. Those fallback choices therefore form an ordered
			// prefix (excluding the two seeds). Suffix maxima prove in O(1) whether any
			// remaining actor can complete the package; only the final choice needs a scan.
			var infantrySuffixMaximum = new int[candidates.Count + 1];
			var otherSuffixMaximum = new int[candidates.Count + 1];
			Array.Fill(infantrySuffixMaximum, -1);
			Array.Fill(otherSuffixMaximum, -1);
			for (var i = candidates.Count - 1; i >= 0; i--)
			{
				infantrySuffixMaximum[i] = infantrySuffixMaximum[i + 1];
				otherSuffixMaximum[i] = otherSuffixMaximum[i + 1];
				if (IsSeed(i))
					continue;

				var candidate = candidates[i];
				if (candidate.IsInfantry)
					infantrySuffixMaximum[i] = Math.Max(infantrySuffixMaximum[i], candidate.CombatValue);
				else
					otherSuffixMaximum[i] = Math.Max(otherSuffixMaximum[i], candidate.CombatValue);
			}

			var nextFallbackIndex = 0;
			AdvancePastSeeds();
			while (offeredValue < requiredValue && selectedIndexes.Count < candidates.Count)
			{
				var infantryCanComplete = infantrySuffixMaximum[nextFallbackIndex] >= 0 &&
					tacticalValue(infantryValue + infantrySuffixMaximum[nextFallbackIndex], infantryCount + 1, otherValue) >= requiredValue;
				var otherCanComplete = otherSuffixMaximum[nextFallbackIndex] >= 0 &&
					tacticalValue(infantryValue, infantryCount, otherValue + otherSuffixMaximum[nextFallbackIndex]) >= requiredValue;

				if (!infantryCanComplete && !otherCanComplete)
				{
					AddCandidate(nextFallbackIndex++);
					offeredValue = tacticalValue(infantryValue, infantryCount, otherValue);
					AdvancePastSeeds();
					continue;
				}

				var bestIndex = -1;
				var bestSurplusCost = int.MaxValue;
				var bestDistanceSquared = int.MaxValue;
				var bestActorId = uint.MaxValue;
				for (var i = nextFallbackIndex; i < candidates.Count; i++)
				{
					if (IsSeed(i))
						continue;

					var candidate = candidates[i];
					var projectedValue = candidate.IsInfantry
						? tacticalValue(infantryValue + candidate.CombatValue, infantryCount + 1, otherValue)
						: tacticalValue(infantryValue, infantryCount, otherValue + candidate.CombatValue);
					if (projectedValue < requiredValue)
						continue;

					var candidateSurplusCost = surplusCost(projectedValue, requiredValue);
					if (candidateSurplusCost > bestSurplusCost ||
						(candidateSurplusCost == bestSurplusCost && candidate.DistanceSquared > bestDistanceSquared) ||
						(candidateSurplusCost == bestSurplusCost && candidate.DistanceSquared == bestDistanceSquared && candidate.ActorId >= bestActorId))
						continue;

					bestIndex = i;
					bestSurplusCost = candidateSurplusCost;
					bestDistanceSquared = candidate.DistanceSquared;
					bestActorId = candidate.ActorId;
				}

				if (bestIndex < 0)
					throw new InvalidOperationException("A SECURE package suffix maximum proved completion, but no completing candidate was found.");

				AddCandidate(bestIndex);
				offeredValue = tacticalValue(infantryValue, infantryCount, otherValue);
			}

			return BuildSelection();

			bool IsSeed(int index) => index == firstInfantryIndex || index == firstOtherIndex;

			void AdvancePastSeeds()
			{
				while (nextFallbackIndex < candidates.Count && IsSeed(nextFallbackIndex))
					nextFallbackIndex++;
			}

			FransGroundSecurePackageSelection BuildSelection()
			{
				return new FransGroundSecurePackageSelection(
					selectedIndexes.ToArray(), infantryValue, infantryCount, otherValue, offeredValue);
			}
		}
	}
}
