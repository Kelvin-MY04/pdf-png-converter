"""Immutable configuration container for the PDF-to-PNG conversion pipeline."""

from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class ConversionConfig:
    """Immutable, typed container of all conversion parameters.

    Populated from the TOML config file; falls back to built-in defaults
    for any absent key.
    """

    dpi: int = 200
    min_width_px: int = 3000
    min_height_px: int = 2000
    import_dir: Path = field(default_factory=lambda: Path("import"))
    export_dir: Path = field(default_factory=lambda: Path("export"))
