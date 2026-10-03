namespace OpenRA.Mods.Common.Traits
{
	public enum FransGroundDefendForcePreservationAction
	{
		AcceptedUnchanged,
		Reduced,
		EmergencyOverride
	}

	public readonly record struct FransGroundDefendForcePreservationDecision(
		FransGroundDefendForcePreservationAction Action,
		int PackageCount,
		int ProposedCommitPercent,
		int ProposedReserveCount,
		int ProposedReservePercent);

	public static class FransGroundDefendForcePreservationGuard
	{
		public static FransGroundDefendForcePreservationDecision Evaluate(
			int proposedPackageCount,
			int eligibleFreeForceCount,
			int utility,
			int estimatedEtaTicks,
			int minimumPackageUnits,
			int triggerCommitPercent,
			int lowReservePercent,
			int minimumReserveUnits,
			int targetReservePercent,
			int longEtaMinimumTicks)
		{
			var eligibleFree = System.Math.Max(0, eligibleFreeForceCount);
			var proposed = System.Math.Clamp(proposedPackageCount, 0, eligibleFree);
			if (eligibleFree == 0 || proposed == 0)
				return new FransGroundDefendForcePreservationDecision(
					FransGroundDefendForcePreservationAction.AcceptedUnchanged, proposed, 0, eligibleFree, 100);

			var reserve = eligibleFree - proposed;
			var commitPercent = (int)System.Math.Clamp(((long)proposed * 100L + eligibleFree - 1L) / eligibleFree, 0L, 100L);
			var reservePercent = (int)System.Math.Clamp((long)reserve * 100L / eligibleFree, 0L, 100L);
			var largeOrHighCommitPackage = proposed >= minimumPackageUnits || commitPercent >= triggerCommitPercent;
			var lowReservePackage = largeOrHighCommitPackage &&
				(reserve < minimumReserveUnits || reservePercent < lowReservePercent);

			if (!lowReservePackage)
				return new FransGroundDefendForcePreservationDecision(
					FransGroundDefendForcePreservationAction.AcceptedUnchanged, proposed, commitPercent, reserve, reservePercent);

			var emergencyOverride = utility >= 0 || estimatedEtaTicks < longEtaMinimumTicks;
			if (emergencyOverride)
				return new FransGroundDefendForcePreservationDecision(
					FransGroundDefendForcePreservationAction.EmergencyOverride, proposed, commitPercent, reserve, reservePercent);

			var targetReserve = System.Math.Max(minimumReserveUnits,
				(int)System.Math.Clamp(((long)eligibleFree * targetReservePercent + 99L) / 100L, 0L, eligibleFree));
			var reducedPackage = System.Math.Max(0, System.Math.Min(proposed, eligibleFree - targetReserve));
			return new FransGroundDefendForcePreservationDecision(
				FransGroundDefendForcePreservationAction.Reduced, reducedPackage, commitPercent, reserve, reservePercent);
		}
	}
}
