"""Unit tests for CLI main module functions."""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch
import argparse
import pytest

from pdf_png_converter.cli.main import _parse_arguments, _load_config, _build_orchestrator
from pdf_png_converter.config.conversion_config import ConversionConfig


class TestParseArguments:
    def test_default_config_path(self):
        with patch("sys.argv", ["pdf-png-converter"]):
            args = _parse_arguments()
        assert args.config == Path("config.toml")

    def test_custom_config_path(self):
        with patch("sys.argv", ["pdf-png-converter", "--config", "/tmp/custom.toml"]):
            args = _parse_arguments()
        assert args.config == Path("/tmp/custom.toml")

    def test_short_config_flag(self):
        with patch("sys.argv", ["pdf-png-converter", "-c", "my.toml"]):
            args = _parse_arguments()
        assert args.config == Path("my.toml")

    def test_import_dir_default_is_none(self):
        with patch("sys.argv", ["pdf-png-converter"]):
            args = _parse_arguments()
        assert args.import_dir is None

    def test_import_dir_override(self):
        with patch("sys.argv", ["pdf-png-converter", "--import-dir", "/tmp/in"]):
            args = _parse_arguments()
        assert args.import_dir == Path("/tmp/in")

    def test_export_dir_override(self):
        with patch("sys.argv", ["pdf-png-converter", "--export-dir", "/tmp/out"]):
            args = _parse_arguments()
        assert args.export_dir == Path("/tmp/out")

    def test_dpi_default_is_none(self):
        with patch("sys.argv", ["pdf-png-converter"]):
            args = _parse_arguments()
        assert args.dpi is None

    def test_dpi_override(self):
        with patch("sys.argv", ["pdf-png-converter", "--dpi", "300"]):
            args = _parse_arguments()
        assert args.dpi == 300

    def test_short_dpi_flag(self):
        with patch("sys.argv", ["pdf-png-converter", "-d", "150"]):
            args = _parse_arguments()
        assert args.dpi == 150


class TestLoadConfig:
    def _make_args(
        self,
        config: Path = Path("config.toml"),
        import_dir: Path | None = None,
        export_dir: Path | None = None,
        dpi: int | None = None,
    ) -> argparse.Namespace:
        return argparse.Namespace(config=config, import_dir=import_dir, export_dir=export_dir, dpi=dpi)

    def test_no_overrides_uses_config_file_values(self, tmp_path):
        cfg = tmp_path / "config.toml"
        cfg.write_text("[conversion]\ndpi = 250\n")
        args = self._make_args(config=cfg)
        result = _load_config(args)
        assert result.dpi == 250

    def test_dpi_override_takes_precedence(self, tmp_path):
        cfg = tmp_path / "config.toml"
        cfg.write_text("[conversion]\ndpi = 200\n")
        args = self._make_args(config=cfg, dpi=400)
        result = _load_config(args)
        assert result.dpi == 400

    def test_import_dir_override_takes_precedence(self, tmp_path):
        cfg = tmp_path / "config.toml"
        cfg.write_text("")
        args = self._make_args(config=cfg, import_dir=Path("/custom/import"))
        result = _load_config(args)
        assert result.import_dir == Path("/custom/import")

    def test_export_dir_override_takes_precedence(self, tmp_path):
        cfg = tmp_path / "config.toml"
        cfg.write_text("")
        args = self._make_args(config=cfg, export_dir=Path("/custom/export"))
        result = _load_config(args)
        assert result.export_dir == Path("/custom/export")

    def test_returns_conversion_config_instance(self, tmp_path):
        cfg = tmp_path / "config.toml"
        cfg.write_text("")
        result = _load_config(self._make_args(config=cfg))
        assert isinstance(result, ConversionConfig)


class TestBuildOrchestrator:
    def test_returns_orchestrator(self):
        from pdf_png_converter.services.conversion_orchestrator import ConversionOrchestrator
        config = ConversionConfig()
        orchestrator = _build_orchestrator(config)
        assert isinstance(orchestrator, ConversionOrchestrator)
