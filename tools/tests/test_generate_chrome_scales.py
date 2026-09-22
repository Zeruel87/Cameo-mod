"""THE SCALE GENERATOR MUST NEVER EAT THE ART MASTER.

⛔ TWO REAL HAZARDS, BOTH HIT WHILE BUILDING THE TOOL, BOTH NOW GUARDED.

1. **Self-overwrite.** Cameo's 4x master is *named* `flags_3x.png`. The first version of the tool
   happily ran `--emit 3` and replaced the highest-resolution source with its own downscale. The
   4x artwork would have been gone, silently, with a cheerful "wrote ..." line. It actually
   happened during testing and was only recoverable because of a manual backup.

2. **Padded masters.** Upstream OpenRA and Combined Arms pad 3x artwork into a power-of-two canvas
   (3 x 256 = 768 -> a 1024 file). Uniform-resizing such a master produces the right artwork ratio
   inside a nonsense canvas. Cameo's own `glyphs_3x.png` is exactly this shape, so the tool has to
   recognise and refuse it rather than "fix" a sheet that is already correct.

Both are the same underlying error — trusting the CANVAS or the FILENAME instead of measuring the
ARTWORK — which is the error that produced the original bug this whole thread is about.
"""

from __future__ import annotations

import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
TOOL = ROOT / "tools" / "art" / "generate_chrome_scales.py"
sys.path.insert(0, str(TOOL.parent))

import generate_chrome_scales as g  # noqa: E402


def test_the_tool_exists_and_measures_artwork_not_canvas():
    src = TOOL.read_text(encoding="utf-8")
    assert "def artwork(" in src
    assert "CANVAS IS NOT SCALE" in src


def test_it_refuses_to_overwrite_the_master():
    """Hazard 1. The message must name the master, not fail silently or half-write."""
    src = TOOL.read_text(encoding="utf-8")
    assert "dst.resolve() == master.resolve()" in src
    assert "REFUSED" in src


def test_it_refuses_a_padded_master():
    """Hazard 2 — Cameo's own glyphs_3x is padded, so this fires on the real tree."""
    src = TOOL.read_text(encoding="utf-8")
    assert "Refusing" in src and "PADDED" in src


def test_the_master_need_not_be_declared_in_chrome_yaml():
    """A 4x master is an ART SOURCE. The engine ladder stops at 3x, so it is never in the yaml."""
    src = TOOL.read_text(encoding="utf-8")
    assert '"--master"' in src


def test_it_reads_real_png_dimensions():
    flags = ROOT / "mods" / "cameo" / "uibits" / "flags.png"
    if not flags.exists():
        return
    assert g.png_size(flags) == (512, 512)


def test_artwork_finds_the_real_extent_of_the_generated_flag_sheets():
    """The 4x master and every generated variant remain at their declared density."""
    uibits = ROOT / "mods" / "cameo" / "uibits"
    cases = {
        "flags.png": (512, 512, 387, 512),
        "flags_2x.png": (1024, 1024, 771, 1024),
        "flags_3x.png": (2048, 2048, 1153, 1536),
        "flags_4x.png": (2048, 2048, 1536, 2048),
        "glyphs_3x.png": (1024, 1024, 768, 768),   # 3x artwork in a padded canvas -- correct
    }
    for name, want in cases.items():
        p = uibits / name
        if not p.exists():
            continue
        assert g.artwork(p) == want, name


def test_declared_flag_variant_canvases_are_power_of_two():
    """The renderer rejects a 1536x1536 sheet before any flag can be judged visually."""
    uibits = ROOT / "mods" / "cameo" / "uibits"
    for name in ("flags.png", "flags_2x.png", "flags_3x.png"):
        width, height = g.png_size(uibits / name)
        assert width & (width - 1) == 0, (name, width)
        assert height & (height - 1) == 0, (name, height)


def test_the_collection_names_are_matched_case_insensitively():
    """The yaml templates are ^Flags / ^Glyphs; nobody types the capital."""
    assert "lookup = {k.lower(): k for k in decl}" in TOOL.read_text(encoding="utf-8")


def test_it_prefers_pillow_but_says_which_resampler_ran():
    """A silent quality difference between machines is worse than a slow one."""
    src = TOOL.read_text(encoding="utf-8")
    assert "Pillow LANCZOS" in src and "pure-python box filter" in src
    assert "from PIL import Image" in src


def test_generated_files_are_flagged_as_engine_content():
    """They land under mods/, so they carry the boot gate (CLAUDE.md rule 1)."""
    src = TOOL.read_text(encoding="utf-8")
    assert "BOOT GATE" in src and "engine content" in src


def test_it_reports_a_mis_declared_master_instead_of_nothing_to_do():
    """⛔ THE THIRD HAZARD, AND THE WORST: silence on the very collection that is broken.

    `--check` compares each derived sheet against the master. When the master IS the mis-declared
    sheet — `flags_3x.png` holding 4x artwork — there is nothing left to compare it to, so the
    report ended with "Nothing to do" on the one collection this whole tool exists for. The check
    has to ask whether the master belongs in the slot it is declared in, which is the question the
    original bug turned on.
    """
    src = TOOL.read_text(encoding="utf-8")
    assert "FIELD_DENSITY[best] != master_density" in src
    assert "Broken collection" in src
    # It must hand over the remedy, not just the diagnosis.
    assert "git mv" in src and "--emit" in src


def test_a_padded_master_is_only_fatal_when_generating():
    """`glyphs_3x.png` is a correctly padded 3x sheet. A plain --check on it must not go red.

    Refusing to GENERATE from a padded master is right; reporting a healthy collection as broken
    is the same false positive that the first diagnosis of this bug made by reading canvases.
    """
    src = TOOL.read_text(encoding="utf-8")
    assert "Not a generation source" in src
    assert re.search(r"if generating:\s*\n\s*return 1", src), \
        "the padded-master refusal must exit non-zero whenever generation is requested"


def test_write_refuses_an_auto_selected_padded_master(monkeypatch):
    """A repair run must not resize the padded 3x runtime sheet as though it were a master."""
    calls = []
    monkeypatch.setattr(g, "resize", lambda *args: calls.append(args))
    monkeypatch.setattr(sys, "argv", [str(TOOL), "flags", "--write"])
    assert g.main() == 1
    assert calls == []


def test_pillow_resize_pads_without_moving_the_artwork(tmp_path):
    from PIL import Image

    src, dst = tmp_path / "source.png", tmp_path / "derived.png"
    image = Image.new("RGBA", (3, 2))
    image.putdata([
        (255, 0, 0, 255), (0, 255, 0, 255), (0, 0, 255, 255),
        (1, 2, 3, 255), (4, 5, 6, 255), (7, 8, 9, 255),
    ])
    image.save(src)
    original = image.tobytes()

    assert g.resize(src, dst, 3, 2) == "Pillow LANCZOS"
    with Image.open(dst) as got:
        assert got.size == (4, 2)
        assert got.crop((0, 0, 3, 2)).tobytes() == original
        assert got.crop((3, 0, 4, 2)).tobytes() == bytes(8)


def test_pure_python_resize_pads_without_moving_the_artwork(tmp_path, monkeypatch):
    import builtins

    src, dst = tmp_path / "source.png", tmp_path / "derived.png"
    source_rows = [bytearray(range(12)), bytearray(range(12, 24))]
    g._write_png(src, 3, 2, source_rows)
    real_import = builtins.__import__

    def no_pillow(name, *args, **kwargs):
        if name == "PIL":
            raise ImportError("forced fallback")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", no_pillow)
    assert g.resize(src, dst, 3, 2) == "pure-python box filter"
    width, height, rows = g._read_png(dst)
    assert (width, height) == (4, 2)
    assert [row[:12] for row in rows] == source_rows
    assert all(row[12:] == bytes(4) for row in rows)


def test_scale_audit_rejects_a_non_power_of_two_runtime_sheet(tmp_path, monkeypatch):
    audit_dir = ROOT / "tools" / "audit"
    sys.path.insert(0, str(audit_dir))
    import audit_chrome_scale_variants as audit

    uibits = tmp_path / "uibits"
    uibits.mkdir()
    g._write_png(uibits / "base.png", 2, 2, [bytearray([255] * 8) for _ in range(2)])
    g._write_png(uibits / "three.png", 6, 6, [bytearray([255] * 24) for _ in range(6)])
    chrome = tmp_path / "chrome.yaml"
    chrome.write_text(
        "^Flags:\n\tImage: base.png\n\tImage3x: three.png\n\n"
        "flags:\n\tInherits: ^Flags\n\tRegions:\n\t\tgdi: 0, 0, 2, 2\n",
        encoding="utf-8")
    monkeypatch.setattr(audit, "CHROME", chrome)
    monkeypatch.setattr(audit, "UIBITS", uibits)
    assert audit.main() == 1


def test_the_broken_collection_check_does_not_fire_for_a_supplied_master():
    """`--master flags_4x.png` is the fix being applied; it must not trip the diagnosis.

    A supplied master is a path, not a chrome.yaml slot, so there is no declared density to
    disagree with — and route E runs exactly this way (docs/patches/chrome_10_*.sh).
    """
    src = TOOL.read_text(encoding="utf-8")
    assert "if not args.master and best is not None" in src


def test_the_4x_master_is_never_declared_as_a_chrome_variant():
    """⛔ THE INVARIANT THAT KEEPS THE FIX FIXED.

    `flags_4x.png` is the editable art source. The engine's density ladder stops at 3x, so
    declaring the master in `chrome.yaml` cannot help — and `FieldLoader.Load` drops an `Image4x`
    key the type does not declare *in silence* (CLAUDE.md rule 8b), so flags would quietly fall
    back to the 2x sheet and look like nothing happened. The master stays out of chrome.yaml.
    """
    chrome = (ROOT / "mods" / "cameo" / "chrome.yaml").read_text(encoding="utf-8")
    # A COMMENT naming the master is wanted — it tells the next artist which file to edit. A
    # DECLARATION is the thing that must not exist.
    declared = [ln for ln in chrome.splitlines()
                if "flags_4x.png" in ln and not ln.lstrip().startswith("#")]
    assert not declared, declared
    assert (ROOT / "mods" / "cameo" / "uibits" / "flags_4x.png").exists(), \
        "the master must be committed — it is the only flags file anyone should edit"


def test_the_pytest_dependency_is_written_down_where_the_runner_is():
    """⛔ `unittest discover` runs ZERO of seven files here and still prints OK.

    Six `import pytest` (one _FailedTest each); the seventh — this file — is bare functions and
    disappears in silence. `audit_test_coverage.py` counts `def test_*` by regex, so nothing else
    can notice. The README has to say so, or the next person "fixes" a missing-pytest failure by
    switching to the documented stdlib command and turns a loud failure into a silent pass.
    """
    readme = (ROOT / "tools" / "tests" / "README.md").read_text(encoding="utf-8")
    assert "python -m pytest" in readme
    assert "does NOT run the whole suite" in readme
    for named in ("test_bot_insurance_model", "test_generate_chrome_scales", "test_band_law"):
        assert named in readme, f"{named} is pytest-style and must be listed"


def test_the_check_tolerance_scales_with_the_sheet():
    """⛔ A FLAT ±2px TOLERANCE FAILS THE TOOL'S OWN OUTPUT.

    Resampling bleeds alpha outward, so a downscaled sheet's bounding box lands a few pixels off
    the exact ratio: the shipped 2x flags sheet measures 771 where 387 x 2 = 774. `--check` was
    telling you to regenerate a file this very tool had just generated — and a check that cries
    wolf on correct art gets ignored on incorrect art.
    """
    src = TOOL.read_text(encoding="utf-8")
    assert "want_art[0] // 200" in src, "the tolerance must scale with the sheet, not be flat"
    assert "abs(got[2] - want_art[0]) <= tol[0]" in src
