"""Unit tests for ConversionOrchestrator (all dependencies mocked)."""

from pathlib import Path
from unittest.mock import MagicMock, patch, call
import pytest

from pdf_png_converter.config.conversion_config import ConversionConfig
from pdf_png_converter.models.conversion_job import ConversionJob
from pdf_png_converter.models.conversion_result import ConversionResult
from pdf_png_converter.models.conversion_status import ConversionStatus
from pdf_png_converter.services.conversion_orchestrator import ConversionOrchestrator


@pytest.fixture
def config():
    return ConversionConfig(
        dpi=200,
        import_dir=Path("/import"),
        export_dir=Path("/export"),
    )


def make_job(name: str, pages: int = 1) -> ConversionJob:
    return ConversionJob(
        source_path=Path(f"/import/{name}.pdf"),
        relative_path=Path(f"{name}.pdf"),
        page_count=pages,
    )


def make_result(name: str, page: int = 1) -> ConversionResult:
    return ConversionResult(
        output_path=Path(f"/export/{name}_page{page}.png"),
        width_px=4678,
        height_px=6622,
        page_number=page,
        dpi_used=200,
    )


@pytest.fixture
def mocks(config):
    scanner = MagicMock()
    path_resolver = MagicMock()
    directory_builder = MagicMock()
    renderer = MagicMock()
    reporter = MagicMock()
    orchestrator = ConversionOrchestrator(
        scanner=scanner,
        path_resolver=path_resolver,
        directory_builder=directory_builder,
        renderer=renderer,
        reporter=reporter,
        config=config,
    )
    return {
        "orchestrator": orchestrator,
        "scanner": scanner,
        "path_resolver": path_resolver,
        "directory_builder": directory_builder,
        "renderer": renderer,
        "reporter": reporter,
    }


class TestConversionOrchestratorScanning:
    def test_scanner_scan_called_once(self, mocks, config):
        mocks["scanner"].scan.return_value = []
        mocks["orchestrator"].execute()
        mocks["scanner"].scan.assert_called_once_with(config.import_dir)

    def test_returns_empty_list_when_no_pdfs(self, mocks):
        mocks["scanner"].scan.return_value = []
        result = mocks["orchestrator"].execute()
        assert result == []


class TestConversionOrchestratorRendering:
    def test_render_page_called_once_for_single_page_pdf(self, mocks):
        job = make_job("plan", pages=1)
        mocks["scanner"].scan.return_value = [job]
        mocks["renderer"].get_page_count.return_value = 1
        mocks["renderer"].render_page.return_value = make_result("plan")
        mocks["path_resolver"].resolve_output_path.return_value = Path("/export/plan.png")

        mocks["orchestrator"].execute()
        assert mocks["renderer"].render_page.call_count == 1

    def test_render_page_called_three_times_for_3_page_pdf(self, mocks):
        job = make_job("plan", pages=3)
        mocks["scanner"].scan.return_value = [job]
        mocks["renderer"].get_page_count.return_value = 3
        mocks["renderer"].render_page.side_effect = [
            make_result("plan", 1),
            make_result("plan", 2),
            make_result("plan", 3),
        ]
        mocks["path_resolver"].resolve_output_path.return_value = Path("/export/plan.png")

        mocks["orchestrator"].execute()
        assert mocks["renderer"].render_page.call_count == 3


class TestConversionOrchestratorErrorHandling:
    def test_corrupted_pdf_job_becomes_skipped(self, mocks):
        job = make_job("corrupted")
        mocks["scanner"].scan.return_value = [job]
        mocks["renderer"].get_page_count.side_effect = Exception("Invalid PDF")

        result = mocks["orchestrator"].execute()
        assert result[0].status == ConversionStatus.SKIPPED

    def test_error_in_one_job_does_not_stop_batch(self, mocks):
        job1 = make_job("corrupted")
        job2 = make_job("valid")
        mocks["scanner"].scan.return_value = [job1, job2]
        mocks["renderer"].get_page_count.side_effect = [
            Exception("Invalid PDF"),
            1,
        ]
        mocks["renderer"].render_page.return_value = make_result("valid")
        mocks["path_resolver"].resolve_output_path.return_value = Path("/export/valid.png")

        result = mocks["orchestrator"].execute()
        assert len(result) == 2
        assert result[0].status == ConversionStatus.SKIPPED
        assert result[1].status == ConversionStatus.SUCCESS

    def test_error_message_recorded_on_skipped_job(self, mocks):
        job = make_job("bad")
        mocks["scanner"].scan.return_value = [job]
        mocks["renderer"].get_page_count.side_effect = Exception("File corrupt")

        result = mocks["orchestrator"].execute()
        assert result[0].error_message is not None
        assert len(result[0].error_message) > 0


class TestConversionOrchestratorReporter:
    def test_reporter_called_once_at_end(self, mocks):
        mocks["scanner"].scan.return_value = []
        mocks["orchestrator"].execute()
        mocks["reporter"].report.assert_called_once()

    def test_reporter_receives_completed_jobs(self, mocks):
        job = make_job("plan")
        mocks["scanner"].scan.return_value = [job]
        mocks["renderer"].get_page_count.return_value = 1
        mocks["renderer"].render_page.return_value = make_result("plan")
        mocks["path_resolver"].resolve_output_path.return_value = Path("/export/plan.png")

        mocks["orchestrator"].execute()
        args = mocks["reporter"].report.call_args[0][0]
        assert len(args) == 1
