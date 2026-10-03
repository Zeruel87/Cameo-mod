using System;
using System.Collections.Generic;
using OpenRA;
using OpenRA.Mods.Common.Pathfinder;

namespace OpenRA.Mods.Common.Traits
{
	// Pure, production-used policy primitives. Keeping these separate makes the
	// activation and exact-target rules directly testable without a live match.
	internal static class RoutineLandNegativeUnionPolicy
	{
		public const int ActivationNativeEmptyResults = 2;
		public const int MinimumRemainingObjectives = 4;

		public static bool ShouldAttemptPreparation(int ordinaryNativeEmptyResults,
			int remainingCandidateUpperBound, bool preparationAttempted)
		{
			return !preparationAttempted &&
				ordinaryNativeEmptyResults >= ActivationNativeEmptyResults &&
				remainingCandidateUpperBound >= MinimumRemainingObjectives;
		}

		public static bool SupportsTargets(IReadOnlyList<CPos> targets)
		{
			if (targets == null || targets.Count < 2)
				return false;
			var first = targets[0];
			for (var i = 1; i < targets.Count; i++)
				if (targets[i] != first)
					return true;
			return false;
		}

		public static CPos[] BuildDeterministicUnion(IEnumerable<IReadOnlyList<CPos>> orderedTargetArrays)
		{
			var seen = new HashSet<CPos>();
			var union = new List<CPos>();
			foreach (var targets in orderedTargetArrays)
				foreach (var target in targets)
					if (seen.Add(target))
						union.Add(target);
			return union.ToArray();
		}

		public static bool OrderedTargetsEqual(IReadOnlyList<CPos> left, IReadOnlyList<CPos> right)
		{
			if (left == null || right == null || left.Count != right.Count)
				return false;
			for (var i = 0; i < left.Count; i++)
				if (left[i] != right[i])
					return false;
			return true;
		}

		public static string ContractMismatch(object expectedActor, uint expectedActorId, object expectedOwner,
			object expectedMobile, object expectedLocomotor, CPos expectedSource, int expectedWorldTick,
			int expectedRiskRevision, int expectedTerrainKnowledgeVersion,
			object currentActor, uint currentActorId, object currentOwner, object currentMobile,
			object currentLocomotor, CPos currentSource, int currentWorldTick,
			int currentRiskRevision, int currentTerrainKnowledgeVersion)
		{
			if (!ReferenceEquals(expectedActor, currentActor) || expectedActorId != currentActorId)
				return "McvIdentityChanged";
			if (!ReferenceEquals(expectedOwner, currentOwner))
				return "OwnerChanged";
			if (!ReferenceEquals(expectedMobile, currentMobile) || !ReferenceEquals(expectedLocomotor, currentLocomotor))
				return "MovementContractChanged";
			if (expectedSource != currentSource)
				return "SourceChanged";
			if (expectedWorldTick != currentWorldTick)
				return "WorldTickChanged";
			if (expectedRiskRevision != currentRiskRevision)
				return "RiskRevisionChanged";
			if (expectedTerrainKnowledgeVersion != currentTerrainKnowledgeVersion)
				return "TerrainKnowledgeVersionChanged";
			return null;
		}
	}

	// This is the exact scan contract frozen by the production RoutineLand caller.
	// Reference identity is deliberate: replacing an actor, owner, Mobile, or Locomotor
	// invalidates every negative certificate even if its value-like fields happen to match.
	internal readonly record struct RoutineLandNegativeUnionContract(
		object Actor, uint ActorId, object Owner, object Mobile, object Locomotor,
		CPos Source, int WorldTick, int RiskRevision, int TerrainKnowledgeVersion,
		bool ActorAvailable)
	{
		public string Mismatch(RoutineLandNegativeUnionContract current)
		{
			var mismatch = RoutineLandNegativeUnionPolicy.ContractMismatch(
				Actor, ActorId, Owner, Mobile, Locomotor, Source, WorldTick,
				RiskRevision, TerrainKnowledgeVersion,
				current.Actor, current.ActorId, current.Owner, current.Mobile,
				current.Locomotor, current.Source, current.WorldTick,
				current.RiskRevision, current.TerrainKnowledgeVersion);
			if (mismatch != null)
				return mismatch;
			return current.ActorAvailable ? null : "McvUnavailable";
		}
	}

	internal readonly record struct RoutineLandNegativeUnionObjective(CPos Objective, CPos[] Targets);

	internal readonly record struct RoutineLandNativePathResult(
		List<CPos> Path, long PathCostCallbacks, long RiskPathCostCalls);

	internal enum RoutineLandNegativeUnionPreparationOutcome
	{
		NotAttempted,
		Unknown,
		Positive,
		Negative
	}

	internal readonly record struct RoutineLandNegativeUnionPreparationResult(
		RoutineLandNegativeUnionPreparationOutcome Outcome,
		string ActivationReason,
		string FallbackReason,
		int EligibleObjectives,
		CPos[] UnionTargets,
		RoutineLandNativePathResult NativeResult,
		bool NativeCallExecuted);

	// Shared by the ordinary and union production paths. Validation calls this same
	// source-built wrapper against the real OpenRA PathFinder and supplies the same
	// prepared-risk callback contract as FransRiskModelBotModule.
	internal static class RoutineLandNativePathInvoker
	{
		public static RoutineLandNativePathResult FindPathToTargetCells(
			Actor actor, PathFinder pathFinder, CPos source, IReadOnlyList<CPos> targets,
			Func<Func<Func<CPos, int>, List<CPos>>, List<CPos>> executeWithPreparedPathCost,
			Action<RoutineLandNativePathResult> performanceObserver = null)
		{
			long pathCostCallbacks = 0;
			long riskPathCostCalls = 0;
			var path = executeWithPreparedPathCost(preparedPathCost =>
			{
				int CustomCost(CPos cell)
				{
					pathCostCallbacks++;
					if (cell == source)
						return 0;

					riskPathCostCalls++;
					return preparedPathCost(cell);
				}

				return pathFinder.FindPathToTargetCells(actor, source, targets,
					BlockedByActor.Immovable, CustomCost, laneBias: false);
			});
			var result = new RoutineLandNativePathResult(path, pathCostCallbacks, riskPathCostCalls);
			performanceObserver?.Invoke(result);
			return result;
		}
	}

	// Scan-local production coordinator. It owns activation, the sole union attempt,
	// certificate creation, exact contract checks, and exact target consumption.
	internal sealed class RoutineLandNegativeUnionScan
	{
		readonly RoutineLandNegativeUnionContract contract;
		readonly Dictionary<CPos, CPos[]> negativeCertificates = [];

		public int OrdinaryNativeEmptyResults { get; private set; }
		public bool PreparationAttempted { get; private set; }
		public int CertificateCount => negativeCertificates.Count;

		public RoutineLandNegativeUnionScan(RoutineLandNegativeUnionContract contract)
		{
			this.contract = contract;
		}

		public void RecordOrdinaryNativeResult(RoutineLandNativePathResult result)
		{
			if (result.Path != null && result.Path.Count == 0)
				OrdinaryNativeEmptyResults++;
		}

		public RoutineLandNegativeUnionPreparationResult TryPrepare(
			int remainingCandidateUpperBound,
			bool supportedTerrainHeight,
			Func<RoutineLandNegativeUnionContract> currentContract,
			IReadOnlyList<RoutineLandNegativeUnionObjective> eligibleObjectives,
			Func<CPos[], RoutineLandNativePathResult> nativeCall)
		{
			const string activationReason = "TwoOrdinaryNativeEmptyAndFourRemainingBound";
			if (PreparationAttempted || OrdinaryNativeEmptyResults < RoutineLandNegativeUnionPolicy.ActivationNativeEmptyResults)
				return NotAttempted(null);
			if (!RoutineLandNegativeUnionPolicy.ShouldAttemptPreparation(
				OrdinaryNativeEmptyResults, remainingCandidateUpperBound, PreparationAttempted))
				return NotAttempted("InsufficientRemainingCandidateUpperBound");

			PreparationAttempted = true;
			if (!supportedTerrainHeight)
				return Unknown("UnsupportedTerrainHeight");

			var mismatch = contract.Mismatch(currentContract());
			if (mismatch != null)
				return Unknown(mismatch);

			var eligibleCount = eligibleObjectives?.Count ?? 0;
			if (eligibleCount < RoutineLandNegativeUnionPolicy.MinimumRemainingObjectives)
				return Unknown("InsufficientRemainingSupportedObjectives", eligibleCount);

			var targetArrays = new IReadOnlyList<CPos>[eligibleCount];
			for (var i = 0; i < eligibleCount; i++)
				targetArrays[i] = eligibleObjectives[i].Targets;
			var unionTargets = RoutineLandNegativeUnionPolicy.BuildDeterministicUnion(targetArrays);
			if (!RoutineLandNegativeUnionPolicy.SupportsTargets(unionTargets))
				return Unknown("UnsupportedUnionTargets", eligibleCount, unionTargets);

			var nativeResult = nativeCall(unionTargets);
			if (nativeResult.Path == null)
				return Unknown("UnionReturnedNull", eligibleCount, unionTargets, nativeResult, true);
			if (nativeResult.Path.Count > 0)
				return new RoutineLandNegativeUnionPreparationResult(
					RoutineLandNegativeUnionPreparationOutcome.Positive, activationReason, null,
					eligibleCount, unionTargets, nativeResult, true);

			mismatch = contract.Mismatch(currentContract());
			if (mismatch != null)
				return Unknown(mismatch, eligibleCount, unionTargets, nativeResult, true);

			for (var i = 0; i < eligibleCount; i++)
			{
				var objective = eligibleObjectives[i];
				negativeCertificates[objective.Objective] = (CPos[])objective.Targets.Clone();
			}

			return new RoutineLandNegativeUnionPreparationResult(
				RoutineLandNegativeUnionPreparationOutcome.Negative, activationReason, null,
				eligibleCount, unionTargets, nativeResult, true);

			RoutineLandNegativeUnionPreparationResult NotAttempted(string reason) =>
				new(RoutineLandNegativeUnionPreparationOutcome.NotAttempted,
					reason == null ? null : activationReason, reason, 0, [], default, false);
			RoutineLandNegativeUnionPreparationResult Unknown(string reason, int eligible = 0,
				CPos[] union = null, RoutineLandNativePathResult native = default, bool called = false) =>
				new(RoutineLandNegativeUnionPreparationOutcome.Unknown, activationReason, reason,
					eligible, union ?? [], native, called);
		}

		public bool HasCertificate(CPos objective) => negativeCertificates.ContainsKey(objective);

		public bool TryUseCertificate(CPos objective, IReadOnlyList<CPos> targets,
			RoutineLandNegativeUnionContract current, out string mismatch)
		{
			mismatch = null;
			if (!negativeCertificates.TryGetValue(objective, out var certifiedTargets))
				return false;

			mismatch = contract.Mismatch(current);
			if (mismatch == null && !RoutineLandNegativeUnionPolicy.OrderedTargetsEqual(certifiedTargets, targets))
				mismatch = "OrderedTargetsChanged";
			return mismatch == null;
		}
	}
}
