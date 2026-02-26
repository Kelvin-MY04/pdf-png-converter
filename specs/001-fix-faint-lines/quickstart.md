# Developer Quickstart: Fix Faint Lines

**Branch**: `001-fix-faint-lines`

## What This Fix Does

Disables anti-aliasing for vector graphics during PDF rasterisation so that thin lines (wall lines, dimension lines, hatching) render as fully opaque, pixel-exact strokes rather than blended semi-transparent marks.

## Setup

```bash
uv sync
```

## Reproducing the Bug

Before the fix, running any PDF with thin lines will produce a PNG where lines appear faint:

```bash
uv run pdf-png-converter
# Open export/<file>.png — lines are faint/grey at 100% zoom
```

## Verifying the Fix

After implementing the changes described in `plan.md`:

```bash
uv run pytest tests/unit/models/test_rendering_options.py   # new unit tests
uv run pytest tests/unit/services/test_pdf_renderer.py      # AA settings applied
uv run pytest tests/unit/config/                            # config parsing
uv run pytest tests/integration/test_line_visibility.py     # contrast ratio check
uv run pytest                                               # full suite
```

All tests should pass. The integration test `test_line_visibility.py` is the definitive acceptance test — it renders the `lines.pdf` fixture and asserts that stroke pixels achieve ≥ 4.5:1 contrast ratio against the white background.

## Key Files Changed

| File | Change |
|------|--------|
| `src/pdf_png_converter/models/rendering_options.py` | **NEW** — `RenderingOptions` dataclass |
| `src/pdf_png_converter/config/conversion_config.py` | Add `rendering_options` field |
| `src/pdf_png_converter/config/config_loader.py` | Parse `[conversion.rendering]` TOML section |
| `src/pdf_png_converter/services/pdf_renderer.py` | Apply AA settings before `get_pixmap()` |
| `config.toml` | Add `[conversion.rendering]` section |
| `tests/fixtures/pdfs/lines.pdf` | **NEW** — test fixture with black vector lines |
| `tests/fixtures/create_fixtures.py` | Add `lines.pdf` generation |
| `tests/unit/models/test_rendering_options.py` | **NEW** |
| `tests/unit/config/test_conversion_config.py` | Add `rendering_options` field tests |
| `tests/unit/config/test_config_loader.py` | Add rendering section parsing tests |
| `tests/unit/services/test_pdf_renderer.py` | Add AA settings application tests |
| `tests/integration/test_line_visibility.py` | **NEW** — pixel contrast acceptance test |

## AA Level Reference

| `graphics_aa_level` | Effect |
|---------------------|--------|
| `0` | No AA — pixel-exact fully opaque strokes **(use this)** |
| `8` | Maximum smoothing — faint blended strokes **(current broken default)** |

## Config (`config.toml`)

```toml
[conversion.rendering]
graphics_aa_level = 0  # fix: fully sharp lines
text_aa_level = 8      # keep text smooth
```
