"""Mutable entity tracking the full state of converting one PDF file."""

from dataclasses import dataclass, field
from pathlib import Path

from pdf_png_converter.models.conversion_status import ConversionStatus


@dataclass
class ConversionJob:
    """Tracks the full lifecycle of converting one PDF file.

    Created by PdfScanner, updated by ConversionOrchestrator,
    read by ConversionReporter.
    """

    source_path: Path
    relative_path: Path
    status: ConversionStatus = ConversionStatus.PENDING
    output_paths: list[Path] = field(default_factory=list)
    error_message: str | None = None
    page_count: int | None = None
