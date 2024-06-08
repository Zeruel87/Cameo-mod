using OpenRA.Graphics;
using OpenRA.Primitives;

namespace OpenRA.Mods.Cameo.Graphics
{
	public class UILineAnnotationRenderable : IFinalizedRenderable
	{
		readonly int2 end;
		readonly float width;
		readonly Color startColor;
		readonly Color endColor;

		public UILineAnnotationRenderable(int2 start, int2 end, float width, Color color)
		{
			Pos = start;
			this.end = end;
			this.width = width;
			startColor = endColor = color;
		}

		public UILineAnnotationRenderable(int2 start, int2 end, float width, Color startColor, Color endColor)
		{
			Pos = start;
			this.end = end;
			this.width = width;
			this.startColor = startColor;
			this.endColor = endColor;
		}

		public int2 Pos { get; }

		public void Render(WorldRenderer wr)
		{
			Game.Renderer.RgbaColorRenderer.DrawLine(
				wr.Viewport.WorldToViewPx(Pos),
				wr.Viewport.WorldToViewPx(end),
				width, startColor, endColor);
		}

		public void RenderDebugGeometry(WorldRenderer wr) { }
		public Rectangle ScreenBounds(WorldRenderer wr) { return Rectangle.Empty; }
	}

	public class UIRectangleAnnotationRenderable : IRenderable, IFinalizedRenderable
	{
		readonly int2 start;
		readonly int2 end;
		readonly float width;
		readonly Color drawColor;

		public UIRectangleAnnotationRenderable(int2 start, int2 end, float width, Color color, WPos worldAnchorPos)
		{
			this.start = start;
			this.end = end;
			this.width = width;
			drawColor = color;
			Pos = worldAnchorPos;
		}

		void IFinalizedRenderable.Render(WorldRenderer wr)
		{
			Game.Renderer.RgbaColorRenderer.DrawRect(
				start,
				end,
				width, drawColor);
		}

		void IFinalizedRenderable.RenderDebugGeometry(WorldRenderer wr) { }
		Rectangle IFinalizedRenderable.ScreenBounds(WorldRenderer wr) { return Rectangle.Empty; }

		public WPos Pos { get; }
		public int ZOffset { get; }
		public bool IsDecoration => true;

		IRenderable IRenderable.WithZOffset(int newOffset) { return this; }
		IRenderable IRenderable.OffsetBy(in WVec offset) { return this; }
		IRenderable IRenderable.AsDecoration() { return this; }

		IFinalizedRenderable IRenderable.PrepareRender(WorldRenderer wr) { return this; }
	}
}
