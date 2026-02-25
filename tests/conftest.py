"""Shared pytest fixtures for the pdf-png-converter test suite."""

from pathlib import Path
import shutil

import pytest

from pdf_png_converter.config.conversion_config import ConversionConfig


FIXTURES_DIR = Path(__file__).parent / "fixtures" / "pdfs"


@pytest.fixture
def sample_config(tmp_path) -> ConversionConfig:
    """ConversionConfig pointing at tmp_path subdirectories."""
    return ConversionConfig(
        dpi=200,
        min_width_px=3000,
        min_height_px=2000,
        import_dir=tmp_path / "import",
        export_dir=tmp_path / "export",
    )


@pytest.fixture
def tmp_import_dir(tmp_path) -> Path:
    """Temporary import directory."""
    d = tmp_path / "import"
    d.mkdir()
    return d


@pytest.fixture
def tmp_export_dir(tmp_path) -> Path:
    """Temporary export directory (not pre-created — converter must create it)."""
    return tmp_path / "export"


@pytest.fixture
def single_page_pdf_path() -> Path:
    """Path to the single-page PDF fixture."""
    return FIXTURES_DIR / "single_page.pdf"


@pytest.fixture
def multi_page_pdf_path() -> Path:
    """Path to the multi-page (3-page) PDF fixture."""
    return FIXTURES_DIR / "multi_page.pdf"


@pytest.fixture
def corrupted_pdf_path() -> Path:
    """Path to the corrupted PDF fixture."""
    return FIXTURES_DIR / "corrupted.pdf"


@pytest.fixture
def single_page_pdf_in_import(tmp_import_dir, single_page_pdf_path) -> Path:
    """Copy single_page.pdf into the temp import directory; return its path."""
    dest = tmp_import_dir / "single_page.pdf"
    shutil.copy(single_page_pdf_path, dest)
    return dest


@pytest.fixture
def multi_page_pdf_in_import(tmp_import_dir, multi_page_pdf_path) -> Path:
    """Copy multi_page.pdf into the temp import directory; return its path."""
    dest = tmp_import_dir / "multi_page.pdf"
    shutil.copy(multi_page_pdf_path, dest)
    return dest


@pytest.fixture
def corrupted_pdf_in_import(tmp_import_dir, corrupted_pdf_path) -> Path:
    """Copy corrupted.pdf into the temp import directory; return its path."""
    dest = tmp_import_dir / "corrupted.pdf"
    shutil.copy(corrupted_pdf_path, dest)
    return dest
