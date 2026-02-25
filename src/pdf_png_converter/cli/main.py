"""CLI entry point for the PDF-to-PNG converter."""

import argparse
import logging
import sys
from pathlib import Path

from pdf_png_converter.config.config_loader import ConfigLoader
from pdf_png_converter.config.conversion_config import ConversionConfig
from pdf_png_converter.models.conversion_status import ConversionStatus
from pdf_png_converter.reporting.conversion_reporter import ConversionReporter
from pdf_png_converter.services.conversion_orchestrator import ConversionOrchestrator
from pdf_png_converter.services.directory_builder import DirectoryBuilder
from pdf_png_converter.services.path_resolver import PathResolver
from pdf_png_converter.services.pdf_renderer import PdfRenderer
from pdf_png_converter.services.pdf_scanner import PdfScanner

__version__ = "0.1.0"

logging.basicConfig(
    level=logging.WARNING,
    format="%(levelname)s: %(message)s",
    stream=sys.stderr,
)


def main() -> None:
    """Parse arguments, load config, build and execute the conversion pipeline."""
    args = _parse_arguments()
    config = _load_config(args)

    if not config.import_dir.exists():
        print(f"ERROR: Import directory not found: {config.import_dir}", file=sys.stderr)
        sys.exit(1)

    orchestrator = _build_orchestrator(config)
    jobs = orchestrator.execute()

    if jobs and all(j.status in (ConversionStatus.SKIPPED, ConversionStatus.ERROR) for j in jobs):
        sys.exit(2)


def _parse_arguments() -> argparse.Namespace:
    """Parse and return CLI arguments."""
    parser = argparse.ArgumentParser(
        prog="pdf-png-converter",
        description="Convert AutoCAD-exported PDF floor plans to high-resolution PNG images.",
    )
    parser.add_argument(
        "--version", "-V",
        action="version",
        version=f"%(prog)s {__version__}",
    )
    parser.add_argument(
        "--config", "-c",
        type=Path,
        default=Path("config.toml"),
        metavar="PATH",
        help="Path to TOML configuration file (default: config.toml)",
    )
    parser.add_argument(
        "--import-dir", "-i",
        type=Path,
        default=None,
        metavar="PATH",
        help="Override import directory from config",
    )
    parser.add_argument(
        "--export-dir", "-e",
        type=Path,
        default=None,
        metavar="PATH",
        help="Override export directory from config",
    )
    parser.add_argument(
        "--dpi", "-d",
        type=int,
        default=None,
        metavar="INT",
        help="Override rendering DPI from config",
    )
    return parser.parse_args()


def _load_config(args: argparse.Namespace) -> ConversionConfig:
    """Load config from file and apply CLI overrides (CLI > config > defaults)."""
    loader = ConfigLoader()
    config = loader.load(args.config)

    overrides: dict = {}
    if args.import_dir is not None:
        overrides["import_dir"] = args.import_dir
    if args.export_dir is not None:
        overrides["export_dir"] = args.export_dir
    if args.dpi is not None:
        overrides["dpi"] = args.dpi

    if overrides:
        config = ConversionConfig(
            dpi=overrides.get("dpi", config.dpi),
            min_width_px=config.min_width_px,
            min_height_px=config.min_height_px,
            import_dir=overrides.get("import_dir", config.import_dir),
            export_dir=overrides.get("export_dir", config.export_dir),
        )

    return config


def _build_orchestrator(config: ConversionConfig) -> ConversionOrchestrator:
    """Construct all service dependencies and return a ready-to-run orchestrator."""
    return ConversionOrchestrator(
        scanner=PdfScanner(),
        path_resolver=PathResolver(),
        directory_builder=DirectoryBuilder(),
        renderer=PdfRenderer(),
        reporter=ConversionReporter(),
        config=config,
    )


if __name__ == "__main__":
    main()
