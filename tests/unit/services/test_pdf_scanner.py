"""Unit tests for PdfScanner."""

from pathlib import Path
import pytest

from pdf_png_converter.models.conversion_status import ConversionStatus
from pdf_png_converter.services.pdf_scanner import PdfScanner


@pytest.fixture
def scanner():
    return PdfScanner()


class TestPdfScannerEmptyDirectory:
    def test_empty_directory_returns_empty_list(self, scanner, tmp_path):
        result = scanner.scan(tmp_path)
        assert result == []


class TestPdfScannerDiscovery:
    def test_finds_pdf_at_root_level(self, scanner, tmp_path):
        (tmp_path / "plan.pdf").touch()
        result = scanner.scan(tmp_path)
        assert len(result) == 1

    def test_finds_two_pdfs(self, scanner, tmp_path):
        (tmp_path / "plan_a.pdf").touch()
        (tmp_path / "plan_b.pdf").touch()
        result = scanner.scan(tmp_path)
        assert len(result) == 2

    def test_finds_pdfs_in_subdirectory(self, scanner, tmp_path):
        sub = tmp_path / "project-a"
        sub.mkdir()
        (sub / "floor_1.pdf").touch()
        result = scanner.scan(tmp_path)
        assert len(result) == 1

    def test_finds_pdfs_in_nested_subdirectories(self, scanner, tmp_path):
        nested = tmp_path / "project" / "level-1" / "drawings"
        nested.mkdir(parents=True)
        (nested / "plan.pdf").touch()
        result = scanner.scan(tmp_path)
        assert len(result) == 1

    def test_finds_multiple_pdfs_across_directories(self, scanner, tmp_path):
        (tmp_path / "a.pdf").touch()
        sub = tmp_path / "sub"
        sub.mkdir()
        (sub / "b.pdf").touch()
        result = scanner.scan(tmp_path)
        assert len(result) == 2


class TestPdfScannerCaseInsensitivity:
    def test_uppercase_pdf_extension_is_matched(self, scanner, tmp_path):
        (tmp_path / "plan.PDF").touch()
        result = scanner.scan(tmp_path)
        assert len(result) == 1

    def test_mixed_case_pdf_extension_is_matched(self, scanner, tmp_path):
        (tmp_path / "plan.Pdf").touch()
        result = scanner.scan(tmp_path)
        assert len(result) == 1


class TestPdfScannerFiltering:
    def test_non_pdf_files_are_ignored(self, scanner, tmp_path):
        (tmp_path / "notes.txt").touch()
        (tmp_path / "image.png").touch()
        (tmp_path / "drawing.dwg").touch()
        result = scanner.scan(tmp_path)
        assert result == []

    def test_pdf_and_non_pdf_mixed(self, scanner, tmp_path):
        (tmp_path / "plan.pdf").touch()
        (tmp_path / "notes.txt").touch()
        result = scanner.scan(tmp_path)
        assert len(result) == 1


class TestPdfScannerJobAttributes:
    def test_job_source_path_is_absolute(self, scanner, tmp_path):
        (tmp_path / "plan.pdf").touch()
        result = scanner.scan(tmp_path)
        assert result[0].source_path.is_absolute()

    def test_job_source_path_points_to_file(self, scanner, tmp_path):
        pdf = tmp_path / "plan.pdf"
        pdf.touch()
        result = scanner.scan(tmp_path)
        assert result[0].source_path == pdf

    def test_job_relative_path_excludes_import_dir(self, scanner, tmp_path):
        sub = tmp_path / "project"
        sub.mkdir()
        (sub / "plan.pdf").touch()
        result = scanner.scan(tmp_path)
        assert result[0].relative_path == Path("project/plan.pdf")

    def test_job_starts_with_pending_status(self, scanner, tmp_path):
        (tmp_path / "plan.pdf").touch()
        result = scanner.scan(tmp_path)
        assert result[0].status == ConversionStatus.PENDING
