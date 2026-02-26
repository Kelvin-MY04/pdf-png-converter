"""Unit tests for ConversionConfig frozen dataclass."""

import pytest
from dataclasses import FrozenInstanceError
from pathlib import Path
from pdf_png_converter.config.conversion_config import ConversionConfig
from pdf_png_converter.models.rendering_options import RenderingOptions


class TestConversionConfigDefaults:
    def test_default_dpi(self):
        config = ConversionConfig()
        assert config.dpi == 200

    def test_default_min_width_px(self):
        config = ConversionConfig()
        assert config.min_width_px == 3000

    def test_default_min_height_px(self):
        config = ConversionConfig()
        assert config.min_height_px == 2000

    def test_default_import_dir(self):
        config = ConversionConfig()
        assert config.import_dir == Path("import")

    def test_default_export_dir(self):
        config = ConversionConfig()
        assert config.export_dir == Path("export")


class TestConversionConfigImmutability:
    def test_frozen_raises_on_dpi_change(self):
        config = ConversionConfig()
        with pytest.raises(FrozenInstanceError):
            config.dpi = 300  # type: ignore[misc]

    def test_frozen_raises_on_import_dir_change(self):
        config = ConversionConfig()
        with pytest.raises(FrozenInstanceError):
            config.import_dir = Path("other")  # type: ignore[misc]


class TestConversionConfigCustomValues:
    def test_custom_dpi(self):
        config = ConversionConfig(dpi=300)
        assert config.dpi == 300

    def test_custom_dirs_as_paths(self):
        config = ConversionConfig(
            import_dir=Path("/tmp/import"),
            export_dir=Path("/tmp/export"),
        )
        assert config.import_dir == Path("/tmp/import")
        assert config.export_dir == Path("/tmp/export")

    def test_import_dir_is_path_type(self):
        config = ConversionConfig()
        assert isinstance(config.import_dir, Path)

    def test_export_dir_is_path_type(self):
        config = ConversionConfig()
        assert isinstance(config.export_dir, Path)


class TestConversionConfigRenderingOptions:
    def test_default_rendering_options_is_rendering_options_instance(self):
        config = ConversionConfig()
        assert isinstance(config.rendering_options, RenderingOptions)

    def test_default_rendering_options_uses_rendering_options_defaults(self):
        config = ConversionConfig()
        assert config.rendering_options == RenderingOptions()

    def test_default_graphics_aa_level_is_0(self):
        config = ConversionConfig()
        assert config.rendering_options.graphics_aa_level == 0

    def test_default_text_aa_level_is_8(self):
        config = ConversionConfig()
        assert config.rendering_options.text_aa_level == 8

    def test_custom_rendering_options_stored_correctly(self):
        custom = RenderingOptions(graphics_aa_level=4, text_aa_level=4)
        config = ConversionConfig(rendering_options=custom)
        assert config.rendering_options.graphics_aa_level == 4
        assert config.rendering_options.text_aa_level == 4

    def test_two_configs_with_same_rendering_options_are_equal(self):
        config1 = ConversionConfig(rendering_options=RenderingOptions())
        config2 = ConversionConfig(rendering_options=RenderingOptions())
        assert config1.rendering_options == config2.rendering_options
