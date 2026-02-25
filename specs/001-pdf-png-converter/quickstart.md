# Quickstart: PDF to PNG Converter

**Branch**: `001-pdf-png-converter` | **Date**: 2026-02-25

---

## Prerequisites

- Python 3.14+ installed
- [uv](https://docs.astral.sh/uv/) installed (`curl -LsSf https://astral.sh/uv/install.sh | sh`)

---

## Setup

```bash
# 1. Clone the repository
git clone <repo-url>
cd pdf-png-converter

# 2. Install all dependencies (runtime + dev)
uv sync

# 3. Verify installation
uv run pdf-png-converter --version
```

---

## Basic Usage

```bash
# 1. Place PDF files in the import directory
cp /path/to/your/floor-plans/*.pdf import/

# 2. Run the converter with default settings
uv run pdf-png-converter

# 3. Find PNG output in the export directory
ls export/
```

Output mirrors the folder structure of `import/`. Example:
```
import/project-a/level-1/plan.pdf  →  export/project-a/level-1/plan.png
import/project-a/level-2/plan.pdf  →  export/project-a/level-2/plan.png
import/project-b/site.pdf          →  export/project-b/site.png
```

---

## Configuration

Edit `config.toml` in the project root to adjust settings:

```toml
[conversion]
dpi = 200           # Rendering resolution (200 DPI recommended for floor plans)
min_width_px = 3000 # Minimum pixel count on the long dimension
min_height_px = 2000 # Minimum pixel count on the short dimension

[paths]
import_dir = "import"
export_dir = "export"
```

No restart required — config is read at the start of each run.

---

## Override Config at Runtime

```bash
# Use a different config file
uv run pdf-png-converter --config /path/to/custom-config.toml

# Override DPI without editing config
uv run pdf-png-converter --dpi 300

# Use different import/export directories
uv run pdf-png-converter --import-dir /mnt/nas/pdfs --export-dir /mnt/nas/pngs
```

---

## Run Tests

```bash
# Run all tests
uv run pytest

# Run only unit tests
uv run pytest tests/unit/

# Run only integration tests
uv run pytest tests/integration/

# Run only end-to-end tests
uv run pytest tests/e2e/

# Run with coverage report
uv run pytest --cov=pdf_png_converter --cov-report=term-missing
```

---

## Project Structure

```
pdf-png-converter/
├── config.toml                     # User-editable conversion settings
├── pyproject.toml                  # Project metadata and tool configuration
├── uv.lock                         # Locked dependency graph
├── import/                         # Place PDF files here (gitignored)
├── export/                         # Output PNG files appear here (gitignored)
├── src/
│   └── pdf_png_converter/
│       ├── cli/
│       │   └── main.py             # CLI entry point
│       ├── config/
│       │   ├── config_loader.py    # Reads and merges config.toml
│       │   └── conversion_config.py # Typed config dataclass
│       ├── models/
│       │   ├── conversion_job.py   # Tracks one PDF's conversion state
│       │   ├── conversion_result.py # Outcome of one page conversion
│       │   └── conversion_status.py # Status enum (PENDING/SUCCESS/SKIPPED/ERROR)
│       ├── services/
│       │   ├── conversion_orchestrator.py # Coordinates the full pipeline
│       │   ├── directory_builder.py       # Creates output directories
│       │   ├── path_resolver.py           # Maps import paths → export paths
│       │   ├── pdf_renderer.py            # Renders PDF pages to PNG via PyMuPDF
│       │   └── pdf_scanner.py             # Discovers PDF files in import/
│       └── reporting/
│           └── conversion_reporter.py     # Prints conversion summary
└── tests/
    ├── fixtures/
    │   └── pdfs/
    │       ├── single_page.pdf     # Test fixture: valid single-page PDF
    │       ├── multi_page.pdf      # Test fixture: valid 3-page PDF
    │       └── corrupted.pdf       # Test fixture: invalid/corrupted PDF
    ├── unit/                       # Isolated unit tests (mocked dependencies)
    ├── integration/                # Real filesystem, small fixture PDFs
    └── e2e/                        # Full pipeline with fixture PDFs
```

---

## Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| `import/` directory not found | Directory was not created | Run `mkdir import` at project root |
| Output PNG is too small | DPI too low for sheet size | Increase `dpi` in `config.toml`; converter auto-raises if below minimum |
| `WARNING: Config file not found` | `config.toml` is missing | Copy from `config.toml.example` or create using the schema in `specs/001-pdf-png-converter/contracts/config-schema.md` |
| File shows `[SKIP]` in output | PDF is corrupted or password-protected | Verify the PDF opens in a PDF viewer; remove password protection in AutoCAD before export |
| `PermissionError` on export directory | Write access denied | Check filesystem permissions on the `export/` path |
