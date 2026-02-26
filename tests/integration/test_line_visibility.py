"""Integration tests for line visibility in exported PNG images.

Verifies that vector stroke pixels meet WCAG AA contrast ratio (4.5:1)
against a white background when rendered with graphics anti-aliasing disabled.
"""

from pathlib import Path

import pymupdf
import pytest

from pdf_png_converter.config.conversion_config import ConversionConfig
from pdf_png_converter.models.rendering_options import RenderingOptions
from pdf_png_converter.services.pdf_renderer import PdfRenderer
from tests.fixtures.create_fixtures import (
    THIN_LINE_Y_PT,
    STANDARD_LINE_Y_PT,
    LINE_X_START_PT,
    LINE_X_END_PT,
)


FIXTURES_DIR = Path(__file__).parent.parent / "fixtures" / "pdfs"
LINES_PDF = FIXTURES_DIR / "lines.pdf"

# WCAG AA minimum contrast ratio for graphical elements
WCAG_AA_CONTRAST_THRESHOLD = 4.5

# Fraction of sampled pixels along a line that must pass the contrast check
PASS_RATE_THRESHOLD = 0.80


def _relative_luminance(r: int, g: int, b: int) -> float:
    """Compute WCAG 2.1 relative luminance from 0-255 RGB values."""
    def linearise(c: int) -> float:
        v = c / 255.0
        return v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4

    return 0.2126 * linearise(r) + 0.7152 * linearise(g) + 0.0722 * linearise(b)


def wcag_contrast_ratio(pixel_rgb: tuple[int, int, int], background_rgb: tuple[int, int, int]) -> float:
    """Return WCAG 2.1 contrast ratio between pixel and background (always >= 1.0)."""
    l1 = _relative_luminance(*pixel_rgb)
    l2 = _relative_luminance(*background_rgb)
    lighter = max(l1, l2)
    darker = min(l1, l2)
    return (lighter + 0.05) / (darker + 0.05)


def _find_line_y_px(pix: pymupdf.Pixmap, nominal_y_px: int, mid_x_px: int) -> int:
    """Search ±5 rows from the nominal position and return the darkest row's y.

    MuPDF's sub-pixel placement means the darkest row may differ from the
    simple rounded coordinate by 1-2 pixels depending on DPI.
    """
    best_y = nominal_y_px
    darkest = 255
    for dy in range(-5, 6):
        y = max(0, min(pix.height - 1, nominal_y_px + dy))
        r, _g, _b = pix.pixel(mid_x_px, y)
        if r < darkest:
            darkest = r
            best_y = y
    return best_y


def _sample_line_pixels(
    pix: pymupdf.Pixmap, line_y_pt: int, dpi: int, x_start_pt: int, x_end_pt: int
) -> list[tuple[int, int, int]]:
    """Return RGB tuples for pixels sampled along the actual (darkest) line row."""
    scale = dpi / 72.0
    y_nom = int(round(line_y_pt * scale))
    x_start_px = max(0, min(int(round(x_start_pt * scale)), pix.width - 1))
    x_end_px = max(0, min(int(round(x_end_pt * scale)), pix.width - 1))
    mid_x_px = (x_start_px + x_end_px) // 2

    y_actual = _find_line_y_px(pix, y_nom, mid_x_px)

    # Sample every 10th pixel to keep the test fast while covering the line
    return [pix.pixel(x, y_actual) for x in range(x_start_px, x_end_px, 10)]


def _render_lines_pdf(dpi: int, graphics_aa_level: int) -> pymupdf.Pixmap:
    """Render page 1 of lines.pdf at the given DPI and AA level."""
    config = ConversionConfig(
        dpi=dpi,
        rendering_options=RenderingOptions(graphics_aa_level=graphics_aa_level, text_aa_level=8),
    )
    renderer = PdfRenderer()
    renderer._apply_rendering_options(config.rendering_options)
    with pymupdf.open(str(LINES_PDF)) as doc:
        page = doc[0]
        pix = page.get_pixmap(dpi=dpi)
    return pix


WHITE = (255, 255, 255)


class TestThinLineVisibility:
    """Tests for the 0.5 pt thin line (representative of dimension lines)."""

    def test_thin_line_meets_contrast_threshold_with_aa_disabled(self):
        pix = _render_lines_pdf(dpi=200, graphics_aa_level=0)
        pixels = _sample_line_pixels(pix, THIN_LINE_Y_PT, 200, LINE_X_START_PT, LINE_X_END_PT)
        assert pixels, "No pixels sampled along thin line"
        passing = sum(
            1 for p in pixels if wcag_contrast_ratio(p, WHITE) >= WCAG_AA_CONTRAST_THRESHOLD
        )
        pass_rate = passing / len(pixels)
        assert pass_rate >= PASS_RATE_THRESHOLD, (
            f"Only {pass_rate:.0%} of thin line pixels meet {WCAG_AA_CONTRAST_THRESHOLD}:1 contrast "
            f"({passing}/{len(pixels)} pixels passed)"
        )

    def test_standard_line_meets_contrast_threshold_with_aa_disabled(self):
        pix = _render_lines_pdf(dpi=200, graphics_aa_level=0)
        pixels = _sample_line_pixels(pix, STANDARD_LINE_Y_PT, 200, LINE_X_START_PT, LINE_X_END_PT)
        assert pixels, "No pixels sampled along standard line"
        passing = sum(
            1 for p in pixels if wcag_contrast_ratio(p, WHITE) >= WCAG_AA_CONTRAST_THRESHOLD
        )
        pass_rate = passing / len(pixels)
        assert pass_rate >= PASS_RATE_THRESHOLD, (
            f"Only {pass_rate:.0%} of standard line pixels meet {WCAG_AA_CONTRAST_THRESHOLD}:1 contrast "
            f"({passing}/{len(pixels)} pixels passed)"
        )


class TestAntiAliasingRegressionGuard:
    """Confirms the fixture is sensitive to AA setting changes.

    Verifies that rendering with AA=8 produces grey (intermediate) pixels
    adjacent to the line, while AA=0 produces only pure black and white.
    This proves the fix is not a false positive.
    """

    def test_aa_disabled_produces_no_grey_pixels_near_line(self):
        pix = _render_lines_pdf(dpi=200, graphics_aa_level=0)
        scale = 200 / 72.0
        y_nom = int(round(THIN_LINE_Y_PT * scale))
        x_mid = int(round((LINE_X_START_PT + LINE_X_END_PT) / 2 * scale))
        for dy in range(-5, 6):
            y = max(0, min(pix.height - 1, y_nom + dy))
            r, g, b = pix.pixel(x_mid, y)
            assert r in (0, 255), (
                f"AA=0 produced a grey pixel (R={r}) at y={y} — expected only black or white"
            )

    def test_aa_enabled_produces_grey_pixels_near_line(self):
        pix = _render_lines_pdf(dpi=200, graphics_aa_level=8)
        scale = 200 / 72.0
        y_nom = int(round(THIN_LINE_Y_PT * scale))
        x_mid = int(round((LINE_X_START_PT + LINE_X_END_PT) / 2 * scale))
        has_grey = any(
            0 < pix.pixel(x_mid, max(0, min(pix.height - 1, y_nom + dy)))[0] < 255
            for dy in range(-5, 6)
        )
        assert has_grey, (
            "AA=8 should produce grey (anti-aliased) pixels near the line edge, "
            "but only pure black/white pixels were found"
        )


class TestMultiResolutionConsistency:
    """User Story 2 — Consistent Line Clarity Across Output Resolutions."""

    @pytest.mark.parametrize("dpi", [200, 250, 300])
    def test_thin_line_meets_contrast_threshold_at_all_resolutions(self, dpi):
        pix = _render_lines_pdf(dpi=dpi, graphics_aa_level=0)
        pixels = _sample_line_pixels(pix, THIN_LINE_Y_PT, dpi, LINE_X_START_PT, LINE_X_END_PT)
        assert pixels, f"No pixels sampled at {dpi} DPI"
        passing = sum(
            1 for p in pixels if wcag_contrast_ratio(p, WHITE) >= WCAG_AA_CONTRAST_THRESHOLD
        )
        pass_rate = passing / len(pixels)
        assert pass_rate >= PASS_RATE_THRESHOLD, (
            f"At {dpi} DPI: only {pass_rate:.0%} of thin line pixels meet "
            f"{WCAG_AA_CONTRAST_THRESHOLD}:1 contrast ({passing}/{len(pixels)} passed)"
        )

    def test_pass_rate_consistent_across_resolutions(self):
        results = {}
        for dpi in [200, 250, 300]:
            pix = _render_lines_pdf(dpi=dpi, graphics_aa_level=0)
            pixels = _sample_line_pixels(pix, THIN_LINE_Y_PT, dpi, LINE_X_START_PT, LINE_X_END_PT)
            passing = sum(
                1 for p in pixels if wcag_contrast_ratio(p, WHITE) >= WCAG_AA_CONTRAST_THRESHOLD
            )
            results[dpi] = passing / len(pixels)

        pass_rates = list(results.values())
        max_rate = max(pass_rates)
        min_rate = min(pass_rates)
        assert (max_rate - min_rate) <= 0.10, (
            f"Pass rate varies too much across resolutions: {results} "
            f"(max spread: {max_rate - min_rate:.0%})"
        )
