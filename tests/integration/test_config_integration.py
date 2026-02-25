"""Integration tests: ConfigLoader with real TOML files and full validation."""

import logging
from pathlib import Path
import pytest

from pdf_png_converter.config.config_loader import ConfigLoader
from pdf_png_converter.config.conversion_config import ConversionConfig


@pytest.fixture
def loader():
    return ConfigLoader()


class TestConfigLoaderWithRealFiles:
    def test_valid_dpi_300_config_file(self, loader, tmp_path):
        cfg = tmp_path / "config.toml"
        cfg.write_text("[conversion]\ndpi = 300\n")
        result = loader.load(cfg)
        assert result.dpi == 300

    def test_valid_full_config_file(self, loader, tmp_path):
        cfg = tmp_path / "config.toml"
        cfg.write_text(
            "[conversion]\n"
            "dpi = 250\n"
            "min_width_px = 4000\n"
            "min_height_px = 3000\n"
            "[paths]\n"
            'import_dir = "pdfs"\n'
            'export_dir = "images"\n'
        )
        result = loader.load(cfg)
        assert result.dpi == 250
        assert result.min_width_px == 4000
        assert result.min_height_px == 3000
        assert result.import_dir == Path("pdfs")
        assert result.export_dir == Path("images")

    def test_dpi_zero_triggers_warning_and_default(self, loader, tmp_path, caplog):
        cfg = tmp_path / "config.toml"
        cfg.write_text("[conversion]\ndpi = 0\n")
        with caplog.at_level(logging.WARNING):
            result = loader.load(cfg)
        assert result.dpi == 200  # built-in default
        assert any("dpi" in m.lower() for m in caplog.messages)

    def test_missing_file_triggers_warning_and_default(self, loader, tmp_path, caplog):
        with caplog.at_level(logging.WARNING):
            result = loader.load(tmp_path / "nonexistent.toml")
        assert result == ConversionConfig()  # all defaults
        assert len(caplog.messages) > 0

    def test_partial_conversion_section_preserves_path_defaults(self, loader, tmp_path):
        cfg = tmp_path / "config.toml"
        cfg.write_text("[conversion]\ndpi = 400\n")
        result = loader.load(cfg)
        assert result.import_dir == Path("import")
        assert result.export_dir == Path("export")

    def test_absolute_path_strings_loaded_as_path_objects(self, loader, tmp_path):
        cfg = tmp_path / "config.toml"
        cfg.write_text(
            '[paths]\nimport_dir = "/mnt/nas/pdfs"\nexport_dir = "/mnt/nas/pngs"\n'
        )
        result = loader.load(cfg)
        assert result.import_dir == Path("/mnt/nas/pdfs")
        assert result.export_dir == Path("/mnt/nas/pngs")

    def test_returns_frozen_conversion_config(self, loader, tmp_path):
        cfg = tmp_path / "config.toml"
        cfg.write_text("")
        result = loader.load(cfg)
        assert isinstance(result, ConversionConfig)
        # Verify frozen
        from dataclasses import FrozenInstanceError
        with pytest.raises(FrozenInstanceError):
            result.dpi = 999  # type: ignore[misc]
