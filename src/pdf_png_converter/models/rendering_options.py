"""Immutable rendering quality options for PDF rasterisation."""

from dataclasses import dataclass


@dataclass(frozen=True)
class RenderingOptions:
    """Immutable container of rendering quality parameters.

    Controls how PyMuPDF rasterises vector content during PDF-to-PNG conversion.
    Both fields map directly to MuPDF anti-aliasing levels (0–8).

    Attributes:
        graphics_aa_level: Anti-aliasing level for vector graphics (lines, curves,
            paths). 0 = no anti-aliasing (pixel-exact, fully opaque strokes);
            8 = maximum smoothing. Default 0 fixes the faint line defect.
        text_aa_level: Anti-aliasing level for text glyphs. 8 = maximum smoothing,
            preserving readable rendering of dimension labels and annotations.
    """

    graphics_aa_level: int = 0
    text_aa_level: int = 8
