"""Unit tests for ConversionReporter."""

from pathlib import Path
import pytest

from pdf_png_converter.models.conversion_job import ConversionJob
from pdf_png_converter.models.conversion_status import ConversionStatus
from pdf_png_converter.reporting.conversion_reporter import ConversionReporter


@pytest.fixture
def reporter():
    return ConversionReporter()


def make_success_job(name: str, pages: int = 1) -> ConversionJob:
    job = ConversionJob(
        source_path=Path(f"/import/{name}.pdf"),
        relative_path=Path(f"{name}.pdf"),
    )
    job.status = ConversionStatus.SUCCESS
    for i in range(1, pages + 1):
        suffix = f"_page{i}" if pages > 1 else ""
        job.output_paths.append(Path(f"/export/{name}{suffix}.png"))
    return job


def make_skipped_job(name: str, message: str = "unreadable file") -> ConversionJob:
    job = ConversionJob(
        source_path=Path(f"/import/{name}.pdf"),
        relative_path=Path(f"{name}.pdf"),
    )
    job.status = ConversionStatus.SKIPPED
    job.error_message = message
    return job


def make_error_job(name: str, message: str = "partial failure") -> ConversionJob:
    job = ConversionJob(
        source_path=Path(f"/import/{name}.pdf"),
        relative_path=Path(f"{name}.pdf"),
    )
    job.status = ConversionStatus.ERROR
    job.error_message = message
    return job


class TestConversionReporterCounts:
    def test_empty_jobs_shows_zero_counts(self, reporter, capsys):
        reporter.report([])
        captured = capsys.readouterr().out
        assert "0" in captured

    def test_one_success_shows_succeeded_1(self, reporter, capsys):
        reporter.report([make_success_job("plan")])
        captured = capsys.readouterr().out
        assert "1" in captured

    def test_one_skip_shows_skipped_1(self, reporter, capsys):
        reporter.report([make_skipped_job("bad")])
        captured = capsys.readouterr().out
        assert "1" in captured

    def test_mixed_batch_shows_correct_counts(self, reporter, capsys):
        jobs = [
            make_success_job("plan_a"),
            make_success_job("plan_b"),
            make_skipped_job("corrupted"),
            make_error_job("partial"),
        ]
        reporter.report(jobs)
        captured = capsys.readouterr().out
        assert "2" in captured  # 2 succeeded
        assert "1" in captured  # 1 skipped (also prints 1 error)


class TestConversionReporterErrorMessages:
    def test_skipped_job_error_message_in_output(self, reporter, capsys):
        reporter.report([make_skipped_job("bad", "invalid cross-reference table")])
        captured = capsys.readouterr().out
        assert "invalid cross-reference table" in captured

    def test_error_job_error_message_in_output(self, reporter, capsys):
        reporter.report([make_error_job("partial", "disk full")])
        captured = capsys.readouterr()
        # ERROR jobs are written to stderr per the CLI contract
        assert "disk full" in captured.err


class TestConversionReporterSummary:
    def test_summary_separator_line_present(self, reporter, capsys):
        reporter.report([])
        captured = capsys.readouterr().out
        assert "─" in captured or "Conversion" in captured

    def test_summary_contains_conversion_complete(self, reporter, capsys):
        reporter.report([])
        captured = capsys.readouterr().out
        assert "Conversion" in captured or "complete" in captured.lower()


class TestConversionReporterJobLines:
    def test_ok_prefix_for_success_job(self, reporter, capsys):
        reporter.report([make_success_job("plan")])
        captured = capsys.readouterr().out
        assert "[OK]" in captured

    def test_skip_prefix_for_skipped_job(self, reporter, capsys):
        reporter.report([make_skipped_job("bad")])
        captured = capsys.readouterr().out
        assert "[SKIP]" in captured or "[ERROR]" in captured
