"""Unit tests for RenderingOptions."""

import pytest

from pdf_png_converter.models.rendering_options import RenderingOptions


class TestRenderingOptionsDefaults:
    def test_default_graphics_aa_level_is_0(self):
        opts = RenderingOptions()
        assert opts.graphics_aa_level == 0

    def test_default_text_aa_level_is_8(self):
        opts = RenderingOptions()
        assert opts.text_aa_level == 8

    def test_custom_graphics_aa_level_stored(self):
        opts = RenderingOptions(graphics_aa_level=4)
        assert opts.graphics_aa_level == 4

    def test_custom_text_aa_level_stored(self):
        opts = RenderingOptions(text_aa_level=0)
        assert opts.text_aa_level == 0


class TestRenderingOptionsImmutability:
    def test_is_frozen_dataclass(self):
        opts = RenderingOptions()
        with pytest.raises(Exception):
            opts.graphics_aa_level = 8  # type: ignore[misc]

    def test_two_identical_instances_are_equal(self):
        assert RenderingOptions() == RenderingOptions()

    def test_different_instances_are_not_equal(self):
        assert RenderingOptions(graphics_aa_level=0) != RenderingOptions(graphics_aa_level=4)
