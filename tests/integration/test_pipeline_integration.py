"""Integration tests: full orchestrator pipeline with real filesystem and fixture PDFs."""

import shutil
from pathlib import Path
import pytest

from pdf_png_converter.config.conversion_config import ConversionConfig
from pdf_png_converter.models.conversion_status import ConversionStatus
from pdf_png_converter.reporting.conversion_reporter import ConversionReporter
from pdf_png_converter.services.conversion_orchestrator import ConversionOrchestrator
from pdf_png_converter.services.directory_builder import DirectoryBuilder
from pdf_png_converter.services.path_resolver import PathResolver
from pdf_png_converter.services.pdf_renderer import PdfRenderer
from pdf_png_converter.services.pdf_scanner import PdfScanner


def build_orchestrator(config: ConversionConfig) -> ConversionOrchestrator:
    return ConversionOrchestrator(
        scanner=PdfScanner(),
        path_resolver=PathResolver(),
        directory_builder=DirectoryBuilder(),
        renderer=PdfRenderer(),
        reporter=ConversionReporter(),
        config=config,
    )


class TestPipelineIntegrationBasic:
    def test_single_page_pdf_produces_success_job(
        self, tmp_import_dir, tmp_export_dir, single_page_pdf_path
    ):
        shutil.copy(single_page_pdf_path, tmp_import_dir / "plan.pdf")
        config = ConversionConfig(import_dir=tmp_import_dir, export_dir=tmp_export_dir)
        orchestrator = build_orchestrator(config)

        jobs = orchestrator.execute()
        assert len(jobs) == 1
        assert jobs[0].status == ConversionStatus.SUCCESS

    def test_single_page_job_has_one_output_path(
        self, tmp_import_dir, tmp_export_dir, single_page_pdf_path
    ):
        shutil.copy(single_page_pdf_path, tmp_import_dir / "plan.pdf")
        config = ConversionConfig(import_dir=tmp_import_dir, export_dir=tmp_export_dir)
        jobs = build_orchestrator(config).execute()
        assert len(jobs[0].output_paths) == 1

    def test_export_directory_auto_created(
        self, tmp_import_dir, tmp_export_dir, single_page_pdf_path
    ):
        shutil.copy(single_page_pdf_path, tmp_import_dir / "plan.pdf")
        assert not tmp_export_dir.exists()
        config = ConversionConfig(import_dir=tmp_import_dir, export_dir=tmp_export_dir)
        build_orchestrator(config).execute()
        assert tmp_export_dir.exists()

    def test_empty_import_returns_empty_jobs(self, tmp_import_dir, tmp_export_dir):
        config = ConversionConfig(import_dir=tmp_import_dir, export_dir=tmp_export_dir)
        jobs = build_orchestrator(config).execute()
        assert jobs == []


class TestPipelineIntegrationMultiPage:
    def test_multi_page_pdf_produces_3_output_paths(
        self, tmp_import_dir, tmp_export_dir, multi_page_pdf_path
    ):
        shutil.copy(multi_page_pdf_path, tmp_import_dir / "levels.pdf")
        config = ConversionConfig(import_dir=tmp_import_dir, export_dir=tmp_export_dir)
        jobs = build_orchestrator(config).execute()
        assert len(jobs[0].output_paths) == 3

    def test_multi_page_output_files_have_page_suffixes(
        self, tmp_import_dir, tmp_export_dir, multi_page_pdf_path
    ):
        shutil.copy(multi_page_pdf_path, tmp_import_dir / "levels.pdf")
        config = ConversionConfig(import_dir=tmp_import_dir, export_dir=tmp_export_dir)
        jobs = build_orchestrator(config).execute()
        names = sorted(p.name for p in jobs[0].output_paths)
        assert names == ["levels_page1.png", "levels_page2.png", "levels_page3.png"]


class TestPipelineIntegrationErrorHandling:
    def test_corrupted_pdf_produces_skipped_job(
        self, tmp_import_dir, tmp_export_dir, corrupted_pdf_path
    ):
        shutil.copy(corrupted_pdf_path, tmp_import_dir / "corrupted.pdf")
        config = ConversionConfig(import_dir=tmp_import_dir, export_dir=tmp_export_dir)
        jobs = build_orchestrator(config).execute()
        assert jobs[0].status == ConversionStatus.SKIPPED

    def test_corrupted_pdf_does_not_stop_valid_files(
        self, tmp_import_dir, tmp_export_dir, single_page_pdf_path, corrupted_pdf_path
    ):
        shutil.copy(single_page_pdf_path, tmp_import_dir / "valid.pdf")
        shutil.copy(corrupted_pdf_path, tmp_import_dir / "corrupted.pdf")
        config = ConversionConfig(import_dir=tmp_import_dir, export_dir=tmp_export_dir)
        jobs = build_orchestrator(config).execute()

        statuses = {j.source_path.name: j.status for j in jobs}
        assert statuses["valid.pdf"] == ConversionStatus.SUCCESS
        assert statuses["corrupted.pdf"] == ConversionStatus.SKIPPED


class TestPipelineIntegrationNestedStructure:
    def test_nested_pdf_mirrors_directory_structure(
        self, tmp_import_dir, tmp_export_dir, single_page_pdf_path
    ):
        nested = tmp_import_dir / "project-a" / "floor-1"
        nested.mkdir(parents=True)
        shutil.copy(single_page_pdf_path, nested / "plan.pdf")

        config = ConversionConfig(import_dir=tmp_import_dir, export_dir=tmp_export_dir)
        jobs = build_orchestrator(config).execute()

        expected_output = tmp_export_dir / "project-a" / "floor-1" / "plan.png"
        assert expected_output.exists()

    def test_multiple_nested_pdfs_all_mirrored(
        self, tmp_import_dir, tmp_export_dir, single_page_pdf_path
    ):
        (tmp_import_dir / "project-a" / "floor-1").mkdir(parents=True)
        (tmp_import_dir / "project-b").mkdir()
        shutil.copy(single_page_pdf_path, tmp_import_dir / "project-a" / "floor-1" / "plan.pdf")
        shutil.copy(single_page_pdf_path, tmp_import_dir / "project-b" / "site.pdf")

        config = ConversionConfig(import_dir=tmp_import_dir, export_dir=tmp_export_dir)
        build_orchestrator(config).execute()

        assert (tmp_export_dir / "project-a" / "floor-1" / "plan.png").exists()
        assert (tmp_export_dir / "project-b" / "site.png").exists()

    def test_no_extra_directories_created_in_export(
        self, tmp_import_dir, tmp_export_dir, single_page_pdf_path
    ):
        (tmp_import_dir / "project-a").mkdir()
        shutil.copy(single_page_pdf_path, tmp_import_dir / "project-a" / "plan.pdf")

        config = ConversionConfig(import_dir=tmp_import_dir, export_dir=tmp_export_dir)
        build_orchestrator(config).execute()

        # Only project-a should exist under export, not extra dirs
        export_subdirs = [d.name for d in tmp_export_dir.iterdir() if d.is_dir()]
        assert export_subdirs == ["project-a"]
