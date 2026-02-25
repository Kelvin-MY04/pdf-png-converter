"""Recursively discovers all PDF files within a directory tree."""

from pathlib import Path

from pdf_png_converter.models.conversion_job import ConversionJob


class PdfScanner:
    """Scans an import directory and creates a ConversionJob for each PDF found."""

    def scan(self, import_dir: Path) -> list[ConversionJob]:
        """Recursively scan import_dir and return one ConversionJob per PDF file."""
        return [
            self._create_job(path, import_dir)
            for path in import_dir.rglob("*")
            if self._is_pdf_file(path)
        ]

    def _is_pdf_file(self, path: Path) -> bool:
        """Return True if the path is a file with a .pdf extension (case-insensitive)."""
        return path.is_file() and path.suffix.lower() == ".pdf"

    def _create_job(self, source_path: Path, import_dir: Path) -> ConversionJob:
        """Create a ConversionJob with the file's absolute and relative paths."""
        return ConversionJob(
            source_path=source_path,
            relative_path=source_path.relative_to(import_dir),
        )
