# PDF-PNG Converter

Convert AutoCAD-exported PDF floor plans to high-resolution PNG images.

## Description

`pdf-png-converter` is a command-line tool that recursively scans an `import/` directory for PDF files and renders each page as a high-resolution PNG image under a mirrored directory tree in `export/`. Key features:

- **Recursive scanning** — processes every PDF in `import/`, including nested subdirectories.
- **High-resolution output** — renders at a configurable DPI with a hard minimum of 3000 × 2000 px, suitable for AutoCAD floor plans.
- **Structure mirroring** — reproduces the `import/` directory hierarchy exactly under `export/`.
- **Multi-page support** — produces one PNG per page, named `<filename>_page1.png`, `<filename>_page2.png`, etc.
- **Configurable** — all resolution and path settings are controlled via `config.toml`; no code changes required.
- **Rendering quality control** — independently configurable anti-aliasing levels for vector graphics and text via `[conversion.rendering]`; default settings fix the faint-line defect common in AutoCAD-exported PDFs while keeping text smooth.
- **Resilient** — skips corrupted or unreadable PDFs, logs errors, and continues processing the rest of the batch.

## Installation

### Prerequisites

- [Python 3.14+](https://www.python.org/downloads/)
- [uv](https://docs.astral.sh/uv/) — fast Python package manager

  ```bash
  curl -LsSf https://astral.sh/uv/install.sh | sh
  ```

### Setup

```bash
# 1. Clone the repository
git clone https://github.com/Kelvin-MY04/pdf-png-converter.git
cd pdf-png-converter

# 2. Install all dependencies (runtime + dev)
uv sync

# 3. Verify installation
uv run pdf-png-converter --version
```

## Step-by-Step Usage Guide

### Step 1 — Configure settings (optional)

Copy the example config and edit it to suit your needs:

```bash
cp config.toml.example config.toml
```

Edit `config.toml`:

```toml
[conversion]
dpi = 200            # Rendering resolution (200 DPI is the default)
min_width_px = 3000  # Minimum pixel count on the long dimension
min_height_px = 2000 # Minimum pixel count on the short dimension

[conversion.rendering]
graphics_aa_level = 0  # Anti-aliasing for vector lines (0 = off, 8 = maximum)
text_aa_level = 8      # Anti-aliasing for text glyphs (0 = off, 8 = maximum)

[paths]
import_dir = "import"   # Directory to scan for PDF files
export_dir = "export"   # Directory to write PNG files
```

> If `config.toml` is absent, the converter uses the built-in defaults shown above.

> **Rendering quality:** `graphics_aa_level = 0` disables anti-aliasing for vector strokes, making lines render as fully opaque pixel-exact marks (fixes the faint-line defect in AutoCAD PDFs). `text_aa_level = 8` keeps dimension labels and annotations smooth. Both values accept integers from 0 (off) to 8 (maximum).

### Step 2 — Place PDF files in the import directory

```bash
mkdir -p import
cp /path/to/your/floor-plans/*.pdf import/

# Subdirectories are supported and their structure will be preserved
cp /path/to/project-a/floor-1/*.pdf import/project-a/floor-1/
```

### Step 3 — Run the converter

```bash
uv run pdf-png-converter
```

The converter will:
1. Scan `import/` recursively for PDF files.
2. Render each page to a PNG at the configured resolution.
3. Write output files to the mirrored path under `export/`.
4. Print a summary of files converted, skipped, and any errors.

### Step 4 — Inspect the output

```bash
ls export/
```

The output mirrors the folder structure of `import/`. Example:

```
import/project-a/level-1/plan.pdf  →  export/project-a/level-1/plan.png
import/project-a/level-2/plan.pdf  →  export/project-a/level-2/plan.png
import/project-b/site.pdf          →  export/project-b/site.png
```

Multi-page PDFs produce one file per page:

```
import/drawings.pdf  →  export/drawings_page1.png
                         export/drawings_page2.png
                         export/drawings_page3.png
```

### Runtime overrides

You can override config values at runtime without editing `config.toml`:

```bash
# Use a different config file
uv run pdf-png-converter --config /path/to/custom-config.toml

# Override DPI on the fly
uv run pdf-png-converter --dpi 300

# Use different import/export directories
uv run pdf-png-converter --import-dir /mnt/nas/pdfs --export-dir /mnt/nas/pngs
```

## Project Structure

```
pdf-png-converter/
├── config.toml             # User-editable conversion settings
├── config.toml.example     # Annotated example configuration
├── pyproject.toml          # Project metadata and tool configuration
├── import/                 # Place PDF files here (gitignored)
├── export/                 # Output PNG files appear here (gitignored)
├── src/
│   └── pdf_png_converter/
│       ├── cli/            # CLI entry point
│       ├── config/         # Config loading and validation
│       ├── models/         # Conversion job and result models
│       ├── services/       # Core pipeline (scan, render, resolve paths)
│       └── reporting/      # Conversion summary output
└── tests/
    ├── unit/               # Isolated unit tests
    ├── integration/        # Real-filesystem integration tests
    └── e2e/                # Full end-to-end pipeline tests
```

## Running Tests

```bash
uv run pytest                          # All tests
uv run pytest tests/unit/              # Unit tests only
uv run pytest tests/integration/       # Integration tests only
uv run pytest tests/e2e/               # End-to-end tests only
```

## Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| `import/` directory not found | Directory was not created | Run `mkdir import` at the project root |
| Output PNG is too small | DPI too low for sheet size | Increase `dpi` in `config.toml` |
| Lines appear faint or washed-out | Anti-aliasing enabled for vector graphics | Set `graphics_aa_level = 0` under `[conversion.rendering]` in `config.toml` (this is the default) |
| `WARNING: Config file not found` | `config.toml` is missing | Copy from `config.toml.example` |
| File shows `[SKIP]` in output | PDF is corrupted or password-protected | Verify the PDF opens in a viewer; remove password protection before export |
| `PermissionError` on export directory | Write access denied | Check filesystem permissions on the `export/` path |

## License

See [LICENSE](LICENSE).
