"""Immutable record of a successfully converted single PDF page."""

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ConversionResult:
    """Immutable outcome of rendering one PDF page to a PNG file."""

    output_path: Path
    width_px: int
    height_px: int
    page_number: int
    dpi_used: int
