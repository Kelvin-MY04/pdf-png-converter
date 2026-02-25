"""Coordinates the full PDF-to-PNG conversion pipeline."""

import logging
from pathlib import Path

from pdf_png_converter.config.conversion_config import ConversionConfig
from pdf_png_converter.models.conversion_job import ConversionJob
from pdf_png_converter.models.conversion_status import ConversionStatus
from pdf_png_converter.reporting.conversion_reporter import ConversionReporter
from pdf_png_converter.services.directory_builder import DirectoryBuilder
from pdf_png_converter.services.path_resolver import PathResolver
from pdf_png_converter.services.pdf_renderer import PdfRenderer
from pdf_png_converter.services.pdf_scanner import PdfScanner

logger = logging.getLogger(__name__)


class ConversionOrchestrator:
    """Coordinates scanning, path resolution, directory creation, rendering, and reporting."""

    def __init__(
        self,
        scanner: PdfScanner,
        path_resolver: PathResolver,
        directory_builder: DirectoryBuilder,
        renderer: PdfRenderer,
        reporter: ConversionReporter,
        config: ConversionConfig,
    ) -> None:
        self._scanner = scanner
        self._path_resolver = path_resolver
        self._directory_builder = directory_builder
        self._renderer = renderer
        self._reporter = reporter
        self._config = config

    def execute(self) -> list[ConversionJob]:
        """Scan import directory, convert all PDFs, report results."""
        jobs = self._scanner.scan(self._config.import_dir)
        completed = [self._process_job(job) for job in jobs]
        self._reporter.report(completed)
        return completed

    def _process_job(self, job: ConversionJob) -> ConversionJob:
        """Process one ConversionJob: open, render all pages, handle errors."""
        try:
            job.page_count = self._renderer.get_page_count(job.source_path)
            return self._render_all_pages(job)
        except Exception as exc:
            logger.error("Skipping %s: %s", job.source_path, exc)
            job.status = ConversionStatus.SKIPPED
            job.error_message = str(exc)
            return job

    def _render_all_pages(self, job: ConversionJob) -> ConversionJob:
        """Render every page of the PDF and collect output paths."""
        total = job.page_count or 1
        for page_number in range(1, total + 1):
            output_path = self._path_resolver.resolve_output_path(
                source_path=job.source_path,
                import_dir=self._config.import_dir,
                export_dir=self._config.export_dir,
                page_number=page_number,
                total_pages=total,
            )
            self._directory_builder.ensure_directory_exists(output_path.parent)
            result = self._renderer.render_page(
                job.source_path, page_number, output_path, self._config
            )
            job.output_paths.append(result.output_path)

        job.status = ConversionStatus.SUCCESS
        return job
