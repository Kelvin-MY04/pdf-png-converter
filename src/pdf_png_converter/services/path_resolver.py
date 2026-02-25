"""Maps source PDF paths to their corresponding output PNG paths."""

from pathlib import Path


class PathResolver:
    """Computes the correct export file path for a given source path and page number."""

    def resolve_output_path(
        self,
        source_path: Path,
        import_dir: Path,
        export_dir: Path,
        page_number: int,
        total_pages: int,
    ) -> Path:
        """Compute the absolute export path for one page of a PDF file."""
        relative_source = source_path.relative_to(import_dir)
        relative_output = self._build_relative_output_path(relative_source, page_number, total_pages)
        return export_dir / relative_output

    def _build_relative_output_path(
        self, relative_source: Path, page_number: int, total_pages: int
    ) -> Path:
        """Build the relative output path, applying page suffix and extension change."""
        stem = relative_source.stem
        output_name = self._build_output_filename(stem, page_number, total_pages)
        return relative_source.parent / output_name

    def _build_output_filename(self, stem: str, page_number: int, total_pages: int) -> str:
        """Return the PNG filename, with _pageN suffix only for multi-page PDFs."""
        if total_pages > 1:
            return f"{stem}_page{page_number}.png"
        return f"{stem}.png"
