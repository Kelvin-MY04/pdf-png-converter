# Data Model: Fix Faint Lines in Exported PNG Images

**Branch**: `001-fix-faint-lines` | **Date**: 2026-02-26

This document describes only the **changes and additions** to the existing data model established in `001-pdf-png-converter`. Unchanged entities are referenced but not re-documented here.

---

## New Entity: `RenderingOptions` — Value Object

Immutable, typed container of rendering quality parameters. Controls how PyMuPDF rasterises vector content during PDF-to-PNG conversion.

| Field | Type | Default | Description |
|---|---|---|---|
| `graphics_aa_level` | `int` | `0` | Anti-aliasing level for vector graphics (lines, curves, paths). Range 0–8; 0 = no AA (pixel-exact strokes), 8 = maximum smoothing. Default 0 fixes the faint line defect. |
| `text_aa_level` | `int` | `8` | Anti-aliasing level for text glyphs. Range 0–8; 8 = maximum smoothing (preserves readable text in dimension labels and annotations). |

**Validation rules**:
- Both fields must be integers in the range 0–8 (inclusive)
- If an out-of-range value is supplied in config, warn and fall back to the default

**Immutability**: Implemented as `@dataclass(frozen=True)`.

**Relationships**:
- One `RenderingOptions` → embedded in one `ConversionConfig`
- One `RenderingOptions` → consumed by `PdfRenderer.render_page()` before each pixmap call

---

## Modified Entity: `ConversionConfig` — Value Object

Adds one field to the existing value object. All existing fields are unchanged.

| Field | Type | Default | Description | Status |
|---|---|---|---|---|
| `dpi` | `int` | `200` | Target rendering resolution | Unchanged |
| `min_width_px` | `int` | `3000` | Minimum long-dimension pixel count | Unchanged |
| `min_height_px` | `int` | `2000` | Minimum short-dimension pixel count | Unchanged |
| `import_dir` | `Path` | `Path("import")` | Source PDF directory | Unchanged |
| `export_dir` | `Path` | `Path("export")` | Output PNG directory | Unchanged |
| `rendering_options` | `RenderingOptions` | `RenderingOptions()` | Rendering quality settings | **NEW** |

---

## Modified Configuration Schema (`config.toml`)

The `[conversion.rendering]` section is new. All existing sections are unchanged.

```toml
[conversion]
dpi = 200
min_width_px = 3508
min_height_px = 4961

[conversion.rendering]
# Anti-aliasing level for vector lines and paths (0 = none, 8 = maximum).
# Default 0 ensures all strokes render as fully opaque pixel-exact marks.
graphics_aa_level = 0

# Anti-aliasing level for text glyphs (0 = none, 8 = maximum).
# Default 8 preserves smooth rendering of dimension labels and annotations.
text_aa_level = 8

[paths]
import_dir = "import"
export_dir = "export"
```

---

## Service Interface Changes

### `PdfRenderer` — Modified

The `render_page()` method gains pre-render rendering configuration. The method signature is **unchanged**; the change is internal to the implementation.

**Before** (current):
```
render_page(source_path, page_number, output_path, config) -> ConversionResult
  → calls page.get_pixmap(dpi=dpi_used)  [AA level = 8 by default]
```

**After** (fixed):
```
render_page(source_path, page_number, output_path, config) -> ConversionResult
  → applies config.rendering_options.graphics_aa_level to PyMuPDF global AA
  → applies config.rendering_options.text_aa_level to PyMuPDF global text AA
  → calls page.get_pixmap(dpi=dpi_used)  [AA level = 0 for graphics]
```

**Note**: The DPI auto-raise logic in `_calculate_required_dpi()` also calls `get_pixmap()` for probe renders. These probe renders must also use the correct AA level to produce consistent dimension measurements. The AA settings are applied at the start of `render_page()`, before any probe renders, so this is handled correctly.

### `ConfigLoader` — Modified

Gains parsing logic for the `[conversion.rendering]` TOML section to populate `RenderingOptions`.

```
load(config_path: Path) -> ConversionConfig
  → parses [conversion.rendering].graphics_aa_level  (default: 0)
  → parses [conversion.rendering].text_aa_level      (default: 8)
  → validates both in range 0–8
  → constructs RenderingOptions
  → embeds RenderingOptions in ConversionConfig
```

---

## Updated Class Relationship Diagram

```
RenderingOptions (Value Object)          [NEW]
  └── embedded in: ConversionConfig

ConversionConfig (Value Object)          [MODIFIED — adds rendering_options]
  └── used by: ConfigLoader, PdfRenderer, ConversionOrchestrator

ConversionJob (Entity)                   [Unchanged]
ConversionResult (Value Object)          [Unchanged]
ConversionOrchestrator (Service)         [Unchanged]
ConversionReporter (Service)             [Unchanged]
PdfScanner (Service)                     [Unchanged]
PathResolver (Service)                   [Unchanged]
DirectoryBuilder (Service)               [Unchanged]

CLI main()
  ├── constructs: ConfigLoader → ConversionConfig (with RenderingOptions)
  └── constructs + runs: ConversionOrchestrator
```
