#!/usr/bin/env python3
"""chrome_density_reach — which chrome sheet does a given display actually load?

    python tools/art/chrome_density_reach.py
    python tools/art/chrome_density_reach.py 3840x2160 5120x2880

⭐ WHY A SCRIPT AND NOT A TABLE IN A DOC. The first hand-written version of this table got two of
its five rows wrong — 1920x1080 was quoted as 1.87 (that is the WIDTH term; the height term binds
at 1.50) and a 3456x2234 Retina panel was quoted as 3.00 when it actually reaches 3.06 and would
therefore USE a 4x sheet. Two ceilings multiply and a min() picks between four terms; that is one
step past what is safe to do in your head, so it is code.

⛔ EVERY CONSTANT HERE IS COPIED FROM ENGINE SOURCE, and each is cited. Re-derive them against
`cameo-mod/OpenRA` if the engine is bumped — this file is a MODEL of the engine, not the engine.

    ChromeProvider.cs:117           if (dpiScale > 2 && Image3x) density = 3;
                                    else if (dpiScale > 1 && Image2x) density = 2;
    Renderer.cs:386                 WindowScale => Window.EffectiveWindowScale
    Sdl2PlatformWindow.cs:77-82     EffectiveWindowScale = windowScale * scaleModifier
                                      windowScale  = OS display scale (SDL_GetDisplayDPI/96,
                                                     Xft.dpi/96, GDK_SCALE, or the GL points ratio
                                                     on macOS) -- forceable via OPENRA_DISPLAY_SCALE
                                      scaleModifier = the game's Graphics.UIScale setting
    Sdl2PlatformWindow.cs:280       windowSize = surfaceSize / windowScale   <-- LOGICAL, not pixels
    DisplaySettingsLogic.cs:628     validScales = {1, 1.25, 1.5, 1.75, 2} filtered by
                                    maxScale = NativeResolution / MinEffectiveResolution
    WorldViewportSizes.cs:27        MinEffectiveResolution = 1024x720 (Cameo does not override it;
                                    mod.yaml:523 sets only DefaultScale/MaxZoom*)

⚠ BECAUSE `NativeWindowSize` IS LOGICAL, THE OS SCALE CANCELS in the dropdown's own limit — so the
reachable dpiScale is bounded by the PHYSICAL panel alone, and separately by 2 x the OS scale.
Both bounds bind in practice, which is why 4K stops at exactly 3.00 and a 4x rung would be dead
there while a smaller-but-denser Retina panel reaches it.

⚠ The UI Scale DROPDOWN caps at 2.0; the SETTING does not. `Graphics.UIScale` written straight
into settings.yaml is clamped only by BlankLoadScreen.cs:117, and only to reset to 1.0 below the
minimum resolution. That plus OPENRA_DISPLAY_SCALE is how to exercise a 4x path without owning a
5K display.
"""
from __future__ import annotations

import sys

UI_SCALES = (1.0, 1.25, 1.5, 1.75, 2.0)      # DisplaySettingsLogic.cs:628
MIN_W, MIN_H = 1024, 720                      # WorldViewportSizes.cs:27
# OS display scales worth modelling: Windows/GNOME offer 100..300% in 25% steps; macOS Retina is 2.
OS_SCALES = (1.0, 1.25, 1.5, 1.75, 2.0, 2.25, 2.5, 2.75, 3.0)

PANELS = [
    ("1366x768   laptop", 1366, 768),
    ("1920x1080  the common case", 1920, 1080),
    ("2560x1440  1440p", 2560, 1440),
    ("3440x1440  ultrawide", 3440, 1440),
    ("3456x2234  16in Retina", 3456, 2234),
    ("3840x2160  4K", 3840, 2160),
    ("3840x2400  4K 16:10", 3840, 2400),
    ("5120x2880  5K", 5120, 2880),
    ("7680x4320  8K", 7680, 4320),
]


def sheet_for(dpi_scale: float, have_4x: bool = False) -> str:
    """ChromeProvider.cs:117 — plus the 4x rung the engine patch would add (`dpiScale > 3`)."""
    if have_4x and dpi_scale > 3:
        return "4x"
    if dpi_scale > 2:
        return "3x"
    if dpi_scale > 1:
        return "2x"
    return "1x"


def reach(phys_w: int, phys_h: int):
    """(best dpiScale, the OS scale and UI Scale that get there)."""
    best, how = 0.0, (1.0, 1.0)
    for os_scale in OS_SCALES:
        # Sdl2PlatformWindow.cs:280 — the dropdown measures the LOGICAL window, not the panel.
        logical_w, logical_h = int(phys_w / os_scale), int(phys_h / os_scale)
        cap = min(logical_w / MIN_W, logical_h / MIN_H)
        for ui in UI_SCALES:
            if ui <= cap and os_scale * ui > best:
                best, how = os_scale * ui, (os_scale, ui)
    return best, how


def main() -> int:
    # Windows PowerShell commonly exposes cp1252 stdout; keep the report's visible markers
    # portable instead of crashing when the Retina rows reach the 4x annotation.
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    args = sys.argv[1:]
    panels = PANELS
    if args:
        panels = []
        for a in args:
            w, _, h = a.lower().partition("x")
            panels.append((a, int(w), int(h)))

    print("# chrome_density_reach — the highest sheet each panel can actually load\n")
    print("Derived from engine source; see this file's docstring for every citation.")
    print("`4x with patch` assumes the `Image4x` rung (`dpiScale > 3`).\n")
    print("| panel | max dpiScale | at OS scale x UI Scale | today | with Image4x |")
    print("|---|--:|---|---|---|")
    reaches_4x = []
    for name, w, h in panels:
        best, (os_s, ui) = reach(w, h)
        now, then = sheet_for(best), sheet_for(best, have_4x=True)
        mark = " ⭐" if then == "4x" else ""
        if then == "4x":
            reaches_4x.append(name)
        print(f"| {name} | {best:.2f} | {os_s:.0%} x {ui:.0%} | {now} | {then}{mark} |")

    print()
    if reaches_4x:
        print(f"⭐ **{len(reaches_4x)} of {len(panels)} reach a 4x rung:** "
              + ", ".join(n.split()[0] for n in reaches_4x) + ".")
    else:
        print("⛔ **No modelled panel reaches a 4x rung** — the engine change would be dead code.")
    print("\n⚠ A 4x rung needs `dpiScale > 3`, which needs BOTH `min(w/1024, h/720) > 3` AND an OS")
    print("scale above 150%. 4K satisfies neither ceiling with room to spare — it lands on exactly")
    print("3.00 — so a 4x sheet would never load on the most common high-DPI setup there is.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
