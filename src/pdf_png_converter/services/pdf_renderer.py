"""Renders PDF pages to high-resolution PNG files using PyMuPDF."""

import logging
from pathlib import Path

import pymupdf
import pymupdf.mupdf as _mupdf

from pdf_png_converter.config.conversion_config import ConversionConfig
from pdf_png_converter.models.conversion_result import ConversionResult
from pdf_png_converter.models.rendering_options import RenderingOptions

logger = logging.getLogger(__name__)

_DPI_RAISE_STEP = 50
_MAX_DPI_RETRIES = 3


class PdfRenderer:
    """Renders one PDF page to a PNG file at the configured resolution."""

    def get_page_count(self, source_path: Path) -> int:
        """Return the number of pages in the PDF document."""
        with pymupdf.open(str(source_path)) as doc:
            return len(doc)

    def render_page(
        self,
        source_path: Path,
        page_number: int,
        output_path: Path,
        config: ConversionConfig,
    ) -> ConversionResult:
        """Render a single PDF page to a PNG file.

        Applies rendering options (anti-aliasing settings) before rasterisation.
        Automatically raises DPI if the rendered image falls below the configured
        minimum pixel dimensions.
        """
        self._apply_rendering_options(config.rendering_options)
        with pymupdf.open(str(source_path)) as doc:
            page = doc[page_number - 1]
            dpi_used = self._calculate_required_dpi(page, config, initial_dpi=config.dpi)
            pix = page.get_pixmap(dpi=dpi_used)
            width, height = pix.width, pix.height
            pix.save(str(output_path))
            del pix

        return ConversionResult(
            output_path=output_path,
            width_px=width,
            height_px=height,
            page_number=page_number,
            dpi_used=dpi_used,
        )

    def _apply_rendering_options(self, options: RenderingOptions) -> None:
        """Apply anti-aliasing levels to the PyMuPDF global rendering context.

        Sets graphics AA independently from text AA so that vector strokes
        render as pixel-exact fully opaque marks (graphics_aa_level=0) while
        text glyphs remain smoothly rendered (text_aa_level=8 by default).
        """
        _mupdf.fz_set_graphics_aa_level(options.graphics_aa_level)
        _mupdf.fz_set_text_aa_level(options.text_aa_level)

    def _meets_minimum_dimensions(self, width: int, height: int, config: ConversionConfig) -> bool:
        """Return True if the pixel dimensions satisfy the configured minimum floor."""
        long_side = max(width, height)
        short_side = min(width, height)
        return long_side >= config.min_width_px and short_side >= config.min_height_px

    def _calculate_required_dpi(
        self, page: pymupdf.Page, config: ConversionConfig, initial_dpi: int
    ) -> int:
        """Determine the DPI needed for this page to meet the minimum pixel dimensions.

        Renders a probe pixmap at the current DPI. If dimensions are insufficient,
        raises DPI by _DPI_RAISE_STEP and retries up to _MAX_DPI_RETRIES times.
        """
        dpi = initial_dpi
        for attempt in range(_MAX_DPI_RETRIES + 1):
            pix = page.get_pixmap(dpi=dpi)
            width, height = pix.width, pix.height
            del pix

            if self._meets_minimum_dimensions(width, height, config):
                return dpi

            if attempt < _MAX_DPI_RETRIES:
                new_dpi = dpi + _DPI_RAISE_STEP
                logger.warning(
                    "DPI %d renders %dx%d — below minimum %dx%d. Raising to %d.",
                    dpi,
                    width,
                    height,
                    config.min_width_px,
                    config.min_height_px,
                    new_dpi,
                )
                dpi = new_dpi

        logger.warning(
            "Could not meet minimum dimensions after %d retries. Using DPI %d.",
            _MAX_DPI_RETRIES,
            dpi,
        )
        return dpi
