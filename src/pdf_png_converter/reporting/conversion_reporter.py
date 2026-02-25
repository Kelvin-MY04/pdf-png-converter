"""Produces a human-readable conversion summary to stdout."""

import sys
from pathlib import Path

from pdf_png_converter.models.conversion_job import ConversionJob
from pdf_png_converter.models.conversion_status import ConversionStatus

_SEPARATOR = "─" * 50


class ConversionReporter:
    """Prints per-job status lines and a final summary block."""

    def report(self, jobs: list[ConversionJob]) -> None:
        """Print status for each job and a completion summary."""
        for job in jobs:
            self._print_job_line(job)
        self._print_summary(jobs)

    def _print_job_line(self, job: ConversionJob) -> None:
        """Print one status line per job."""
        if job.status == ConversionStatus.SUCCESS:
            for output_path in job.output_paths:
                print(f"[OK]   {output_path}")
        elif job.status == ConversionStatus.SKIPPED:
            print(f"[SKIP] {job.source_path}  ({job.error_message})")
        else:
            print(f"[ERROR] {job.source_path}  ({job.error_message})", file=sys.stderr)

    def _print_summary(self, jobs: list[ConversionJob]) -> None:
        """Print the final summary block with success/skip/error counts."""
        succeeded = sum(1 for j in jobs if j.status == ConversionStatus.SUCCESS)
        skipped = sum(1 for j in jobs if j.status == ConversionStatus.SKIPPED)
        errors = sum(1 for j in jobs if j.status == ConversionStatus.ERROR)
        total_pages = sum(len(j.output_paths) for j in jobs if j.status == ConversionStatus.SUCCESS)

        print(_SEPARATOR)
        print("Conversion complete.")
        print(f"  Succeeded : {succeeded} file(s) \u2192 {total_pages} page(s)")
        print(f"  Skipped   : {skipped} file(s)")
        print(f"  Errors    : {errors} file(s)")
        print(_SEPARATOR)
