"""Unit tests for ConversionResult frozen dataclass."""

import pytest
from dataclasses import FrozenInstanceError
from pathlib import Path
from pdf_png_converter.models.conversion_result import ConversionResult


class TestConversionResultFields:
    def test_all_fields_stored_correctly(self):
        result = ConversionResult(
            output_path=Path("/export/plan.png"),
            width_px=4678,
            height_px=6622,
            page_number=1,
            dpi_used=200,
        )
        assert result.output_path == Path("/export/plan.png")
        assert result.width_px == 4678
        assert result.height_px == 6622
        assert result.page_number == 1
        assert result.dpi_used == 200

    def test_dpi_used_captures_actual_dpi(self):
        result = ConversionResult(
            output_path=Path("/export/plan.png"),
            width_px=7016,
            height_px=9933,
            page_number=1,
            dpi_used=300,
        )
        assert result.dpi_used == 300


class TestConversionResultImmutability:
    def test_frozen_raises_on_output_path_change(self):
        result = ConversionResult(
            output_path=Path("/export/plan.png"),
            width_px=4678,
            height_px=6622,
            page_number=1,
            dpi_used=200,
        )
        with pytest.raises(FrozenInstanceError):
            result.output_path = Path("/other/plan.png")  # type: ignore[misc]

    def test_frozen_raises_on_width_change(self):
        result = ConversionResult(
            output_path=Path("/export/plan.png"),
            width_px=4678,
            height_px=6622,
            page_number=1,
            dpi_used=200,
        )
        with pytest.raises(FrozenInstanceError):
            result.width_px = 9999  # type: ignore[misc]


class TestConversionResultPageNumbers:
    def test_page_number_for_first_page(self):
        result = ConversionResult(
            output_path=Path("/export/plan_page1.png"),
            width_px=4678,
            height_px=6622,
            page_number=1,
            dpi_used=200,
        )
        assert result.page_number == 1

    def test_page_number_for_later_pages(self):
        result = ConversionResult(
            output_path=Path("/export/plan_page3.png"),
            width_px=4678,
            height_px=6622,
            page_number=3,
            dpi_used=200,
        )
        assert result.page_number == 3
