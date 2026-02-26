"""Unit tests for ConfigLoader."""

import logging
from pathlib import Path
import pytest

from pdf_png_converter.config.config_loader import ConfigLoader
from pdf_png_converter.config.conversion_config import ConversionConfig


@pytest.fixture
def loader():
    return ConfigLoader()


class TestConfigLoaderMissingFile:
    def test_missing_file_returns_defaults(self, loader, tmp_path):
        config = loader.load(tmp_path / "nonexistent.toml")
        assert config.dpi == 200
        assert config.min_width_px == 3000
        assert config.min_height_px == 2000

    def test_missing_file_logs_warning(self, loader, tmp_path, caplog):
        with caplog.at_level(logging.WARNING):
            loader.load(tmp_path / "nonexistent.toml")
        assert any("not found" in msg.lower() or "missing" in msg.lower() for msg in caplog.messages)


class TestConfigLoaderMalformedToml:
    def test_malformed_toml_returns_defaults(self, loader, tmp_path):
        bad_file = tmp_path / "bad.toml"
        bad_file.write_text("this is not valid toml [[[")
        config = loader.load(bad_file)
        assert config.dpi == 200

    def test_malformed_toml_logs_warning(self, loader, tmp_path, caplog):
        bad_file = tmp_path / "bad.toml"
        bad_file.write_text("this is not valid toml [[[")
        with caplog.at_level(logging.WARNING):
            loader.load(bad_file)
        assert len(caplog.messages) > 0


class TestConfigLoaderPartialConfig:
    def test_partial_conversion_section_merges_with_defaults(self, loader, tmp_path):
        cfg_file = tmp_path / "config.toml"
        cfg_file.write_text("[conversion]\ndpi = 300\n")
        config = loader.load(cfg_file)
        assert config.dpi == 300
        assert config.min_width_px == 3000  # default preserved
        assert config.min_height_px == 2000  # default preserved

    def test_only_paths_section_keeps_conversion_defaults(self, loader, tmp_path):
        cfg_file = tmp_path / "config.toml"
        cfg_file.write_text('[paths]\nimport_dir = "in"\nexport_dir = "out"\n')
        config = loader.load(cfg_file)
        assert config.dpi == 200
        assert config.import_dir == Path("in")
        assert config.export_dir == Path("out")

    def test_empty_file_returns_defaults(self, loader, tmp_path):
        cfg_file = tmp_path / "config.toml"
        cfg_file.write_text("")
        config = loader.load(cfg_file)
        assert config == ConversionConfig()


class TestConfigLoaderInvalidValues:
    def test_dpi_zero_uses_default_and_warns(self, loader, tmp_path, caplog):
        cfg_file = tmp_path / "config.toml"
        cfg_file.write_text("[conversion]\ndpi = 0\n")
        with caplog.at_level(logging.WARNING):
            config = loader.load(cfg_file)
        assert config.dpi == 200
        assert any("dpi" in msg.lower() for msg in caplog.messages)

    def test_dpi_negative_uses_default_and_warns(self, loader, tmp_path, caplog):
        cfg_file = tmp_path / "config.toml"
        cfg_file.write_text("[conversion]\ndpi = -10\n")
        with caplog.at_level(logging.WARNING):
            config = loader.load(cfg_file)
        assert config.dpi == 200

    def test_min_width_zero_uses_default_and_warns(self, loader, tmp_path, caplog):
        cfg_file = tmp_path / "config.toml"
        cfg_file.write_text("[conversion]\nmin_width_px = 0\n")
        with caplog.at_level(logging.WARNING):
            config = loader.load(cfg_file)
        assert config.min_width_px == 3000


class TestConfigLoaderValidConfig:
    def test_valid_full_config_uses_all_values(self, loader, tmp_path):
        cfg_file = tmp_path / "config.toml"
        cfg_file.write_text(
            "[conversion]\ndpi = 400\nmin_width_px = 6000\nmin_height_px = 4000\n"
            '[paths]\nimport_dir = "pdfs"\nexport_dir = "images"\n'
        )
        config = loader.load(cfg_file)
        assert config.dpi == 400
        assert config.min_width_px == 6000
        assert config.min_height_px == 4000
        assert config.import_dir == Path("pdfs")
        assert config.export_dir == Path("images")

    def test_returns_conversion_config_instance(self, loader, tmp_path):
        cfg_file = tmp_path / "config.toml"
        cfg_file.write_text("")
        config = loader.load(cfg_file)
        assert isinstance(config, ConversionConfig)


class TestConfigLoaderRenderingSection:
    def test_missing_rendering_section_uses_default_graphics_aa_level(self, loader, tmp_path):
        cfg_file = tmp_path / "config.toml"
        cfg_file.write_text("")
        config = loader.load(cfg_file)
        assert config.rendering_options.graphics_aa_level == 0

    def test_missing_rendering_section_uses_default_text_aa_level(self, loader, tmp_path):
        cfg_file = tmp_path / "config.toml"
        cfg_file.write_text("")
        config = loader.load(cfg_file)
        assert config.rendering_options.text_aa_level == 8

    def test_loads_graphics_aa_level_from_toml(self, loader, tmp_path):
        cfg_file = tmp_path / "config.toml"
        cfg_file.write_text("[conversion.rendering]\ngraphics_aa_level = 4\n")
        config = loader.load(cfg_file)
        assert config.rendering_options.graphics_aa_level == 4

    def test_loads_text_aa_level_from_toml(self, loader, tmp_path):
        cfg_file = tmp_path / "config.toml"
        cfg_file.write_text("[conversion.rendering]\ntext_aa_level = 0\n")
        config = loader.load(cfg_file)
        assert config.rendering_options.text_aa_level == 0

    def test_partial_rendering_section_merges_with_defaults(self, loader, tmp_path):
        cfg_file = tmp_path / "config.toml"
        cfg_file.write_text("[conversion.rendering]\ngraphics_aa_level = 2\n")
        config = loader.load(cfg_file)
        assert config.rendering_options.graphics_aa_level == 2
        assert config.rendering_options.text_aa_level == 8  # default preserved

    def test_out_of_range_graphics_aa_level_falls_back_to_default_and_warns(
        self, loader, tmp_path, caplog
    ):
        cfg_file = tmp_path / "config.toml"
        cfg_file.write_text("[conversion.rendering]\ngraphics_aa_level = 9\n")
        with caplog.at_level(logging.WARNING):
            config = loader.load(cfg_file)
        assert config.rendering_options.graphics_aa_level == 0
        assert any("graphics_aa_level" in msg for msg in caplog.messages)

    def test_out_of_range_text_aa_level_falls_back_to_default_and_warns(
        self, loader, tmp_path, caplog
    ):
        cfg_file = tmp_path / "config.toml"
        cfg_file.write_text("[conversion.rendering]\ntext_aa_level = -1\n")
        with caplog.at_level(logging.WARNING):
            config = loader.load(cfg_file)
        assert config.rendering_options.text_aa_level == 8
        assert any("text_aa_level" in msg for msg in caplog.messages)

    def test_boundary_value_0_is_valid_for_graphics_aa_level(self, loader, tmp_path):
        cfg_file = tmp_path / "config.toml"
        cfg_file.write_text("[conversion.rendering]\ngraphics_aa_level = 0\n")
        config = loader.load(cfg_file)
        assert config.rendering_options.graphics_aa_level == 0

    def test_boundary_value_8_is_valid_for_graphics_aa_level(self, loader, tmp_path):
        cfg_file = tmp_path / "config.toml"
        cfg_file.write_text("[conversion.rendering]\ngraphics_aa_level = 8\n")
        config = loader.load(cfg_file)
        assert config.rendering_options.graphics_aa_level == 8
