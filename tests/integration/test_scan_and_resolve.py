"""Integration tests: PdfScanner + PathResolver working together."""

import shutil
from pathlib import Path
import pytest

from pdf_png_converter.services.pdf_scanner import PdfScanner
from pdf_png_converter.services.path_resolver import PathResolver


@pytest.fixture
def scanner():
    return PdfScanner()


@pytest.fixture
def resolver():
    return PathResolver()


class TestScanAndResolveIntegration:
    def test_scanned_jobs_resolve_to_png_extensions(
        self, scanner, resolver, tmp_import_dir, tmp_export_dir, single_page_pdf_path, multi_page_pdf_path
    ):
        shutil.copy(single_page_pdf_path, tmp_import_dir / "plan.pdf")
        shutil.copy(multi_page_pdf_path, tmp_import_dir / "multi.pdf")

        jobs = scanner.scan(tmp_import_dir)
        assert len(jobs) == 2

        for job in jobs:
            output = resolver.resolve_output_path(
                job.source_path, tmp_import_dir, tmp_export_dir, 1, 1
            )
            assert output.suffix == ".png"
            assert str(output).startswith(str(tmp_export_dir))

    def test_nested_pdfs_resolve_to_correct_subpaths(
        self, scanner, resolver, tmp_import_dir, tmp_export_dir, single_page_pdf_path
    ):
        nested = tmp_import_dir / "project-a" / "floor-1"
        nested.mkdir(parents=True)
        shutil.copy(single_page_pdf_path, nested / "plan.pdf")

        jobs = scanner.scan(tmp_import_dir)
        assert len(jobs) == 1

        output = resolver.resolve_output_path(
            jobs[0].source_path, tmp_import_dir, tmp_export_dir, 1, 1
        )
        assert output == tmp_export_dir / "project-a" / "floor-1" / "plan.png"

    def test_multi_page_pdf_resolves_with_page_suffixes(
        self, scanner, resolver, tmp_import_dir, tmp_export_dir, multi_page_pdf_path
    ):
        shutil.copy(multi_page_pdf_path, tmp_import_dir / "levels.pdf")
        jobs = scanner.scan(tmp_import_dir)
        assert len(jobs) == 1

        outputs = [
            resolver.resolve_output_path(
                jobs[0].source_path, tmp_import_dir, tmp_export_dir, page, 3
            )
            for page in range(1, 4)
        ]
        assert outputs[0].name == "levels_page1.png"
        assert outputs[1].name == "levels_page2.png"
        assert outputs[2].name == "levels_page3.png"
