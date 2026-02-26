"""Unit tests for PdfRenderer."""

from pathlib import Path
from unittest.mock import MagicMock, patch, call
import pytest

from pdf_png_converter.config.conversion_config import ConversionConfig
from pdf_png_converter.models.conversion_result import ConversionResult
from pdf_png_converter.models.rendering_options import RenderingOptions
from pdf_png_converter.services.pdf_renderer import PdfRenderer


FIXTURES_DIR = Path(__file__).parent.parent.parent / "fixtures" / "pdfs"
SINGLE_PAGE_PDF = FIXTURES_DIR / "single_page.pdf"
MULTI_PAGE_PDF = FIXTURES_DIR / "multi_page.pdf"
CORRUPTED_PDF = FIXTURES_DIR / "corrupted.pdf"


@pytest.fixture
def renderer():
    return PdfRenderer()


@pytest.fixture
def config():
    return ConversionConfig(dpi=200, min_width_px=3000, min_height_px=2000)


class TestPdfRendererGetPageCount:
    def test_single_page_pdf_returns_1(self, renderer):
        assert renderer.get_page_count(SINGLE_PAGE_PDF) == 1

    def test_multi_page_pdf_returns_3(self, renderer):
        assert renderer.get_page_count(MULTI_PAGE_PDF) == 3

    def test_corrupted_pdf_raises(self, renderer):
        with pytest.raises(Exception):
            renderer.get_page_count(CORRUPTED_PDF)


class TestPdfRendererMeetsMinimumDimensions:
    def test_returns_true_when_both_dimensions_exceed_minimum(self, renderer, config):
        assert renderer._meets_minimum_dimensions(4678, 6622, config) is True

    def test_returns_true_when_dimensions_exactly_at_minimum(self, renderer, config):
        assert renderer._meets_minimum_dimensions(3000, 2000, config) is True

    def test_returns_false_when_short_side_below_minimum(self, renderer, config):
        # 1800 < 2000 (min_height_px when landscape: short side check)
        assert renderer._meets_minimum_dimensions(3500, 1800, config) is False

    def test_returns_false_when_long_side_below_minimum(self, renderer, config):
        assert renderer._meets_minimum_dimensions(2500, 1500, config) is False

    def test_handles_landscape_orientation(self, renderer, config):
        # landscape: width=6622, height=4678 — both exceed 3000×2000
        assert renderer._meets_minimum_dimensions(6622, 4678, config) is True


class TestPdfRendererCalculateRequiredDpi:
    def test_returns_higher_dpi_when_dimensions_insufficient(self, renderer, config):
        """Simulate a page that renders too small at 200 DPI — expect auto-raise."""
        mock_page = MagicMock()
        # First pixmap: too small
        small_pix = MagicMock()
        small_pix.width = 1800
        small_pix.height = 2500
        # Second pixmap: large enough
        large_pix = MagicMock()
        large_pix.width = 4678
        large_pix.height = 6622
        mock_page.get_pixmap.side_effect = [small_pix, large_pix]

        result_dpi = renderer._calculate_required_dpi(mock_page, config, initial_dpi=200)
        assert result_dpi > 200

    def test_returns_initial_dpi_when_dimensions_sufficient(self, renderer, config):
        """When first render already meets minimum, no DPI raise needed."""
        mock_page = MagicMock()
        ok_pix = MagicMock()
        ok_pix.width = 4678
        ok_pix.height = 6622
        mock_page.get_pixmap.return_value = ok_pix

        result_dpi = renderer._calculate_required_dpi(mock_page, config, initial_dpi=200)
        assert result_dpi == 200


class TestPdfRendererRenderPage:
    def test_corrupted_pdf_raises_exception(self, renderer, config, tmp_path):
        output_path = tmp_path / "out.png"
        with pytest.raises(Exception):
            renderer.render_page(CORRUPTED_PDF, 1, output_path, config)

    def test_renders_single_page_pdf_to_png(self, renderer, config, tmp_path):
        output_path = tmp_path / "output.png"
        result = renderer.render_page(SINGLE_PAGE_PDF, 1, output_path, config)
        assert output_path.exists()
        assert isinstance(result, ConversionResult)

    def test_result_dimensions_meet_minimum(self, renderer, config, tmp_path):
        output_path = tmp_path / "output.png"
        result = renderer.render_page(SINGLE_PAGE_PDF, 1, output_path, config)
        long_side = max(result.width_px, result.height_px)
        short_side = min(result.width_px, result.height_px)
        assert long_side >= config.min_width_px
        assert short_side >= config.min_height_px

    def test_result_dpi_used_reflects_actual_dpi(self, renderer, config, tmp_path):
        output_path = tmp_path / "output.png"
        result = renderer.render_page(SINGLE_PAGE_PDF, 1, output_path, config)
        assert result.dpi_used >= config.dpi

    def test_result_page_number_is_set_correctly(self, renderer, config, tmp_path):
        output_path = tmp_path / "output.png"
        result = renderer.render_page(SINGLE_PAGE_PDF, 1, output_path, config)
        assert result.page_number == 1


class TestPdfRendererApplyRenderingOptions:
    def test_apply_rendering_options_calls_set_graphics_aa_level(self, renderer):
        opts = RenderingOptions(graphics_aa_level=0, text_aa_level=8)
        with patch("pymupdf.mupdf.fz_set_graphics_aa_level") as mock_graphics, \
             patch("pymupdf.mupdf.fz_set_text_aa_level"):
            renderer._apply_rendering_options(opts)
            mock_graphics.assert_called_once_with(0)

    def test_apply_rendering_options_calls_set_text_aa_level(self, renderer):
        opts = RenderingOptions(graphics_aa_level=0, text_aa_level=8)
        with patch("pymupdf.mupdf.fz_set_graphics_aa_level"), \
             patch("pymupdf.mupdf.fz_set_text_aa_level") as mock_text:
            renderer._apply_rendering_options(opts)
            mock_text.assert_called_once_with(8)

    def test_apply_rendering_options_uses_values_from_options(self, renderer):
        opts = RenderingOptions(graphics_aa_level=4, text_aa_level=2)
        with patch("pymupdf.mupdf.fz_set_graphics_aa_level") as mock_graphics, \
             patch("pymupdf.mupdf.fz_set_text_aa_level") as mock_text:
            renderer._apply_rendering_options(opts)
            mock_graphics.assert_called_once_with(4)
            mock_text.assert_called_once_with(2)

    def test_render_page_applies_rendering_options_before_pixmap(self, renderer, config, tmp_path):
        output_path = tmp_path / "output.png"
        call_order = []

        def record_graphics(level):
            call_order.append(("set_graphics_aa_level", level))

        def record_text(level):
            call_order.append(("set_text_aa_level", level))

        with patch("pymupdf.mupdf.fz_set_graphics_aa_level", side_effect=record_graphics), \
             patch("pymupdf.mupdf.fz_set_text_aa_level", side_effect=record_text):
            renderer.render_page(SINGLE_PAGE_PDF, 1, output_path, config)

        # AA settings must have been applied (at least once)
        assert any(name == "set_graphics_aa_level" for name, _ in call_order)
        assert any(name == "set_text_aa_level" for name, _ in call_order)
        # They must appear before any get_pixmap calls
        # Verify the AA calls use values from config.rendering_options
        graphics_calls = [(n, v) for n, v in call_order if n == "set_graphics_aa_level"]
        assert graphics_calls[0][1] == config.rendering_options.graphics_aa_level
