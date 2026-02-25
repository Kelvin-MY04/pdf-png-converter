"""Unit tests for ConversionJob mutable dataclass."""

from pathlib import Path
import pytest
from pdf_png_converter.models.conversion_job import ConversionJob
from pdf_png_converter.models.conversion_status import ConversionStatus


class TestConversionJobDefaults:
    def test_default_status_is_pending(self):
        job = ConversionJob(
            source_path=Path("/import/plan.pdf"),
            relative_path=Path("plan.pdf"),
        )
        assert job.status == ConversionStatus.PENDING

    def test_default_output_paths_is_empty_list(self):
        job = ConversionJob(
            source_path=Path("/import/plan.pdf"),
            relative_path=Path("plan.pdf"),
        )
        assert job.output_paths == []

    def test_default_error_message_is_none(self):
        job = ConversionJob(
            source_path=Path("/import/plan.pdf"),
            relative_path=Path("plan.pdf"),
        )
        assert job.error_message is None

    def test_default_page_count_is_none(self):
        job = ConversionJob(
            source_path=Path("/import/plan.pdf"),
            relative_path=Path("plan.pdf"),
        )
        assert job.page_count is None


class TestConversionJobMutability:
    def test_status_can_be_changed_to_success(self):
        job = ConversionJob(
            source_path=Path("/import/plan.pdf"),
            relative_path=Path("plan.pdf"),
        )
        job.status = ConversionStatus.SUCCESS
        assert job.status == ConversionStatus.SUCCESS

    def test_status_can_be_changed_to_skipped(self):
        job = ConversionJob(
            source_path=Path("/import/plan.pdf"),
            relative_path=Path("plan.pdf"),
        )
        job.status = ConversionStatus.SKIPPED
        assert job.status == ConversionStatus.SKIPPED

    def test_output_paths_can_accumulate(self):
        job = ConversionJob(
            source_path=Path("/import/plan.pdf"),
            relative_path=Path("plan.pdf"),
        )
        job.output_paths.append(Path("/export/plan_page1.png"))
        job.output_paths.append(Path("/export/plan_page2.png"))
        assert len(job.output_paths) == 2

    def test_error_message_can_be_set(self):
        job = ConversionJob(
            source_path=Path("/import/plan.pdf"),
            relative_path=Path("plan.pdf"),
        )
        job.error_message = "File is corrupted"
        assert job.error_message == "File is corrupted"

    def test_page_count_can_be_set(self):
        job = ConversionJob(
            source_path=Path("/import/plan.pdf"),
            relative_path=Path("plan.pdf"),
        )
        job.page_count = 3
        assert job.page_count == 3


class TestConversionJobOutputPathsIndependence:
    def test_separate_jobs_have_independent_output_path_lists(self):
        """Verify default_factory creates separate lists per instance."""
        job1 = ConversionJob(source_path=Path("/import/a.pdf"), relative_path=Path("a.pdf"))
        job2 = ConversionJob(source_path=Path("/import/b.pdf"), relative_path=Path("b.pdf"))
        job1.output_paths.append(Path("/export/a.png"))
        assert job2.output_paths == []
