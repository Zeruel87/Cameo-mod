using System.Collections.Generic;
using System.Linq;
using OpenRA.Graphics;
using OpenRA.Mods.Cameo.Traits;
using OpenRA.Mods.Common.Traits;

namespace OpenRA.Mods.Cameo.Orders
{
	public enum ECustomFormationsAttackMoveMode
	{
		None,
		AttackMove,
		AssaultMove,
		Max
	}

	public class CustomFormationsAttackMoveOrderGenerator : CustomFormationsOrderGeneratorBase
	{
		TraitPair<AttackMove>[] subjects;

		readonly MouseButton expectedButton;

		protected ECustomFormationsAttackMoveMode CurrentAttackMoveMode = ECustomFormationsAttackMoveMode.None;

		protected PaletteReference AssaultMoveLineOrderTileMarkerPalette = null;
		protected ISpriteSequence AssaultMoveLineOrderTileMarkerSequence = null;
		protected Sprite AssaultMoveLineOrderTileMarkerSprite = null;
		protected Animation AssaultMoveLineOrderTileMarkerAnimation = null;
		protected bool bAssaultMoveLineOrderTileMarkerAnimates = false;

		protected PaletteReference AssaultMoveLineOrderMarkerPalette = null;
		protected ISpriteSequence AssaultMoveLineOrderMarkerSequence = null;
		protected Sprite AssaultMoveLineOrderMarkerSprite = null;
		protected Animation AssaultMoveLineOrderMarkerAnimation = null;
		protected bool bAssaultMoveLineOrderMarkerAnimates = false;

		protected PaletteReference AttackMoveLineOrderTileMarkerPalette = null;
		protected ISpriteSequence AttackMoveLineOrderTileMarkerSequence = null;
		protected Sprite AttackMoveLineOrderTileMarkerSprite = null;
		protected Animation AttackMoveLineOrderTileMarkerAnimation = null;
		protected bool bAttackMoveLineOrderTileMarkerAnimates = false;

		protected PaletteReference AttackMoveLineOrderMarkerPalette = null;
		protected ISpriteSequence AttackMoveLineOrderMarkerSequence = null;
		protected Sprite AttackMoveLineOrderMarkerSprite = null;
		protected Animation AttackMoveLineOrderMarkerAnimation = null;
		protected bool bAttackMoveLineOrderMarkerAnimates = false;

		public CustomFormationsAttackMoveOrderGenerator(IEnumerable<Actor> subjects, MouseButton button)
		{
			expectedButton = button;

			this.subjects = subjects.Where(a => !a.IsDead)
				.SelectMany(a => a.TraitsImplementing<AttackMove>()
					.Select(am => new TraitPair<AttackMove>(a, am)))
				.ToArray();
		}

		public override string GetCursor(World world, CPos cell, int2 worldPixel, MouseInput mi)
		{
			var isAssaultMove = mi.Modifiers.HasModifier(Modifiers.Ctrl);

			if (bInitialized && (CurrentMode == ECustomFormationsMode.CommandLine))
			{
				ChangeAttackMoveMode(isAssaultMove);
			}

			var subject = subjects.FirstOrDefault();
			if (subject.Actor != null)
			{
				var info = subject.Trait.Info;
				if (world.Map.Contains(cell))
				{
					var explored = subject.Actor.Owner.Shroud.IsExplored(cell);
					var cannotMove = subjects.FirstOrDefault(a => !a.Trait.Info.MoveIntoShroud).Trait;
					var blocked = !explored && cannotMove != null;

					if (isAssaultMove)
					{
						return blocked ? cannotMove.Info.AssaultMoveBlockedCursor : info.AssaultMoveCursor;
					}

					return blocked ? cannotMove.Info.AttackMoveBlockedCursor : info.AttackMoveCursor;
				}

				if (isAssaultMove)
				{
					return info.AssaultMoveBlockedCursor;
				}
				else
				{
					return info.AttackMoveBlockedCursor;
				}
			}

			return null;
		}

		protected override bool OnInitialize(WorldRenderer inWorldRenderer, World inWorld)
		{
			if (base.OnInitialize(inWorldRenderer, inWorld))
			{
				CustomFormationsModOptions modoptions = OwningWorld.LocalPlayer.PlayerActor.Trait<CustomFormationsModOptions>();

				bAttackMoveLineOrderTileMarkerAnimates = modoptions.PlaysAttackMoveOrderTileMarkerAnimation;
				AttackMoveLineOrderTileMarkerPalette = OwningWorldRenderer.Palette(modoptions.AttackMoveOrderTileMarkerPaletteName);
				AttackMoveLineOrderTileMarkerSequence = OwningWorld.Map.Sequences.GetSequence(modoptions.AttackMoveOrderTileMarkerImageName, modoptions.AttackMoveOrderTileMarkerSequenceName);
				if (bAttackMoveLineOrderTileMarkerAnimates)
				{
					AttackMoveLineOrderTileMarkerAnimation = new Animation(OwningWorld, modoptions.AttackMoveOrderTileMarkerImageName);
					//AttackMoveLineOrderTileMarkerAnimation.ChangeImage(modoptions.AttackMoveOrderTileMarkerImageName, modoptions.AttackMoveOrderTileMarkerSequenceName);
				}
				else
				{
					AttackMoveLineOrderTileMarkerSprite = AttackMoveLineOrderTileMarkerSequence.GetSprite(0);
				}

				bAttackMoveLineOrderMarkerAnimates = modoptions.PlaysAttackMoveOrderMarkerAnimation;
				AttackMoveLineOrderMarkerPalette = OwningWorldRenderer.Palette(modoptions.AttackMoveOrderMarkerPaletteName);
				AttackMoveLineOrderMarkerSequence = OwningWorld.Map.Sequences.GetSequence(modoptions.AttackMoveOrderMarkerImageName, modoptions.AttackMoveOrderMarkerSequenceName);
				if (bAttackMoveLineOrderMarkerAnimates)
				{
					AttackMoveLineOrderMarkerAnimation = new Animation(OwningWorld, modoptions.AttackMoveOrderMarkerImageName);
					//AttackMoveLineOrderMarkerAnimation.ChangeImage(modoptions.AttackMoveOrderMarkerImageName, modoptions.AttackMoveOrderMarkerSequenceName);
				}
				else
				{
					AttackMoveLineOrderMarkerSprite = AttackMoveLineOrderMarkerSequence.GetSprite(0);
				}

				bAssaultMoveLineOrderTileMarkerAnimates = modoptions.PlaysAssaultMoveOrderTileMarkerAnimation;
				AssaultMoveLineOrderTileMarkerPalette = OwningWorldRenderer.Palette(modoptions.AssaultMoveOrderTileMarkerPaletteName);
				AssaultMoveLineOrderTileMarkerSequence = OwningWorld.Map.Sequences.GetSequence(modoptions.AssaultMoveOrderTileMarkerImageName, modoptions.AssaultMoveOrderTileMarkerSequenceName);
				if (bAssaultMoveLineOrderTileMarkerAnimates)
				{
					AssaultMoveLineOrderTileMarkerAnimation = new Animation(OwningWorld, modoptions.AssaultMoveOrderTileMarkerImageName);
					//AssaultMoveLineOrderTileMarkerAnimation.ChangeImage(modoptions.AssaultMoveOrderTileMarkerImageName, modoptions.AssaultMoveOrderTileMarkerSequenceName);
				}
				else
				{
					AssaultMoveLineOrderTileMarkerSprite = AssaultMoveLineOrderTileMarkerSequence.GetSprite(0);
				}

				bAssaultMoveLineOrderMarkerAnimates = modoptions.PlaysAssaultMoveOrderMarkerAnimation;
				AssaultMoveLineOrderMarkerPalette = OwningWorldRenderer.Palette(modoptions.AssaultMoveOrderMarkerPaletteName);
				AssaultMoveLineOrderMarkerSequence = OwningWorld.Map.Sequences.GetSequence(modoptions.AssaultMoveOrderMarkerImageName, modoptions.AssaultMoveOrderMarkerSequenceName);
				if (bAssaultMoveLineOrderMarkerAnimates)
				{
					AssaultMoveLineOrderMarkerAnimation = new Animation(OwningWorld, modoptions.AssaultMoveOrderMarkerImageName);
					//AssaultMoveLineOrderMarkerAnimation.ChangeImage(modoptions.AssaultMoveOrderMarkerImageName, modoptions.AssaultMoveOrderMarkerSequenceName);
				}
				else
				{
					AssaultMoveLineOrderMarkerSprite = AssaultMoveLineOrderMarkerSequence.GetSprite(0);
				}

				ChangeAttackMoveMode();

				return true;
			}

			return false;
		}

		protected override IEnumerable<Order> OnLMBDown(CPos inCell, int2 inWorldPixel, MouseInput inMouseInput)
		{
			if (expectedButton == MouseButton.Left)
			{
				StartCommandLine(inCell);
			}

			yield break;
		}

		protected override IEnumerable<Order> OnLMBUp(CPos inCell, int2 inWorldPixel, MouseInput inMouseInput)
		{
			if (expectedButton != MouseButton.Left)
			{
				OwningWorld.CancelInputMode();
			}
			else
			{
				string orderName = inMouseInput.Modifiers.HasModifier(Modifiers.Ctrl) ? "AssaultMove" : "AttackMove";

				if (IsTap)
				{
					// tapped
					IEnumerable<Order> results = TapOrder(inCell, inWorldPixel, inMouseInput, orderName);
					foreach (Order o in results)
					{
						yield return o;
					}
				}
				else
				{
					IEnumerable<Order> orders = EndCommandLine(inCell, inWorldPixel, inMouseInput, orderName);
					foreach (Order o in orders)
					{
						yield return o;
					}
				}

				if (!inMouseInput.Modifiers.HasModifier(Modifiers.Shift))
				{
					OwningWorld.CancelInputMode();
				}
			}

			yield break;
		}

		protected override IEnumerable<Order> OnRMBDown(CPos inCell, int2 inWorldPixel, MouseInput inMouseInput)
		{
			if (expectedButton == MouseButton.Right)
			{
				StartCommandLine(inCell);
			}
			yield break;
		}

		protected override IEnumerable<Order> OnRMBUp(CPos inCell, int2 inWorldPixel, MouseInput inMouseInput)
		{
			if (expectedButton != MouseButton.Right)
			{
				OwningWorld.CancelInputMode();
			}
			else
			{
				string orderName = inMouseInput.Modifiers.HasModifier(Modifiers.Ctrl) ? "AssaultMove" : "AttackMove";

				if (IsTap)
				{
					IEnumerable<Order> results = TapOrder(inCell, inWorldPixel, inMouseInput, orderName);
					foreach (Order o in results)
					{
						yield return o;
					}
				}
				else
				{
					IEnumerable<Order> orders = EndCommandLine(inCell, inWorldPixel, inMouseInput, orderName);
					foreach (Order o in orders)
					{
						yield return o;
					}
				}

				if (!inMouseInput.Modifiers.HasModifier(Modifiers.Shift))
				{
					OwningWorld.CancelInputMode();
				}
			}
		}

		protected void ChangeAttackMoveMode(bool bIsAssault = false)
		{
			if (bIsAssault)
			{
				if (CurrentAttackMoveMode == ECustomFormationsAttackMoveMode.AssaultMove)
				{
					return;
				}
				CurrentAttackMoveMode = ECustomFormationsAttackMoveMode.AssaultMove;
				LineOrderTileMarkerSequence = AssaultMoveLineOrderTileMarkerSequence;
				LineOrderTileMarkerSprite = AssaultMoveLineOrderTileMarkerSprite;
				LineOrderTileMarkerPalette = AssaultMoveLineOrderTileMarkerPalette;
				LineOrderTileMarkerAnimation = AssaultMoveLineOrderTileMarkerAnimation;
				bLineOrderTileMarkerAnimates = bAssaultMoveLineOrderTileMarkerAnimates;

				LineOrderMarkerSequence = AssaultMoveLineOrderMarkerSequence;
				LineOrderMarkerSprite = AssaultMoveLineOrderMarkerSprite;
				LineOrderMarkerPalette = AssaultMoveLineOrderMarkerPalette;
				LineOrderMarkerAnimation = AssaultMoveLineOrderMarkerAnimation;
				bLineOrderMarkerAnimates = bAssaultMoveLineOrderMarkerAnimates;

				if (bLineOrderTileMarkerAnimates && (CurrentMode == ECustomFormationsMode.CommandLine))
				{
					LineOrderTileMarkerAnimation.PlayRepeating(LineOrderTileMarkerSequence.Name);
				}

				if (bLineOrderMarkerAnimates && (CurrentMode == ECustomFormationsMode.CommandLine))
				{
					LineOrderMarkerAnimation.PlayRepeating(LineOrderMarkerSequence.Name);
				}

				LineOrderTileMarkerRenderableArray.Clear();
				LineOrderMarkerRenderableArray.Clear();
			}
			else
			{
				if (CurrentAttackMoveMode == ECustomFormationsAttackMoveMode.AttackMove)
				{
					return;
				}
				CurrentAttackMoveMode = ECustomFormationsAttackMoveMode.AttackMove;
				LineOrderTileMarkerSequence = AttackMoveLineOrderTileMarkerSequence;
				LineOrderTileMarkerSprite = AttackMoveLineOrderTileMarkerSprite;
				LineOrderTileMarkerPalette = AttackMoveLineOrderTileMarkerPalette;
				LineOrderTileMarkerAnimation = AttackMoveLineOrderTileMarkerAnimation;
				bLineOrderTileMarkerAnimates = bAttackMoveLineOrderTileMarkerAnimates;

				LineOrderMarkerSequence = AttackMoveLineOrderMarkerSequence;
				LineOrderMarkerSprite = AttackMoveLineOrderMarkerSprite;
				LineOrderMarkerPalette = AttackMoveLineOrderMarkerPalette;
				LineOrderMarkerAnimation = AttackMoveLineOrderMarkerAnimation;
				bLineOrderMarkerAnimates = bAttackMoveLineOrderMarkerAnimates;

				if (bLineOrderTileMarkerAnimates && (CurrentMode == ECustomFormationsMode.CommandLine))
				{
					LineOrderTileMarkerAnimation.PlayRepeating(LineOrderTileMarkerSequence.Name);
				}

				if (bLineOrderMarkerAnimates && (CurrentMode == ECustomFormationsMode.CommandLine))
				{
					LineOrderMarkerAnimation.PlayRepeating(LineOrderMarkerSequence.Name);
				}

				LineOrderTileMarkerRenderableArray.Clear();
				LineOrderMarkerRenderableArray.Clear();
			}
		}
	}
}
