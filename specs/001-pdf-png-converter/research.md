# Research: PDF to PNG Converter

**Branch**: `001-pdf-png-converter` | **Date**: 2026-02-25

## Decision 1: PDF Rendering Library

**Decision**: PyMuPDF (`pymupdf`)

**Rationale**:
- MuPDF's Fitz renderer produces the highest-quality vector rasterisation of any open-source PDF engine — critical for AutoCAD floor plans with 0.1 mm construction lines, dense hatching, and small annotation text
- Approximately 1.76×–2× faster than Poppler/pdf2image and pypdfium2 in page rendering benchmarks; material for 50+ file batches
- Simplest DPI API: `page.get_pixmap(dpi=200)` — DPI is automatically embedded in PNG metadata
- Python 3.14 officially supported via CPython Stable ABI; Artifex publishes pre-built wheels for 3.14
- Self-contained wheel: MuPDF is statically linked, so `uv add pymupdf` is the entire installation — no OS-level dependencies
- Memory model: allocates RAM for exactly one page at a time; `del pix` immediately after saving releases memory before the next page

**Alternatives considered**:
- **pypdfium2** (Apache-2.0, PDFium engine): Very capable and permissive license, but ~2× slower rendering, requires `scale=dpi/72` (indirect) DPI control, needs careful explicit `del` ordering to avoid non-deterministic memory issues, does not auto-embed DPI in PNG metadata
- **pdf2image** (MIT + Poppler): Requires OS-level Poppler installation (`apt install poppler-utils`), has documented whole-document memory loading risk on large files, adds subprocess overhead per invocation
- **Pillow alone**: Cannot render vector PDFs — only reads raster-embedded PDFs; disqualified immediately

**License note**: PyMuPDF is AGPL-3.0. AGPL's distribution obligation applies only when software is distributed or offered as a networked service. The spec explicitly states the tool runs on a single internal workstation. Internal use does not trigger AGPL. If the tool is ever distributed externally, open-source under AGPL or obtain a commercial license from Artifex.

---

## Decision 2: Configuration File Format

**Decision**: TOML via `tomllib` (Python standard library)

**Rationale**:
- `tomllib` ships in the Python standard library since 3.11 (PEP 680). Python 3.14 includes it — zero additional dependencies
- TOML supports comments (`#`), allowing config files to be self-documenting for non-technical users
- Less ambiguous than YAML (no significant-whitespace rules, no implicit type coercion)
- Consistent with `pyproject.toml` — the format users already see in the project root
- `tomllib` is intentionally read-only (by design); appropriate for a config file users edit manually

**Alternatives considered**:
- **YAML** (via `pyyaml`): Adds a dependency; type-coercion gotchas (e.g., `yes` parsed as boolean); less familiar to non-Python users
- **JSON**: No comment support; users editing config manually cannot annotate values
- **INI** (via `configparser`): No types (everything is a string); awkward for nested configuration
- **`.env` files**: No structure; unsuitable for grouped parameters (paths, resolution, etc.)

---

## Decision 3: Default DPI and Resolution Enforcement

**Decision**: Default DPI = 200; enforce by validating rendered pixel dimensions, not by enforcing a minimum DPI value

**Rationale**:
- At 200 DPI: A3 sheets → ~2338×3308 px; A1 sheets → ~4678×6622 px — both comfortably exceed 3000×2000 px
- At 200 DPI, A3 peak memory per page is ~45 MB; A1 is ~88 MB — acceptable for single-workstation batch processing
- Enforcing `min(width, height) >= 2000` and `max(width, height) >= 3000` (orientation-aware check) correctly handles both landscape and portrait layouts regardless of sheet size
- If rendered dimensions fall short, increase DPI in 50-DPI increments until they pass, then re-render — handles non-standard AutoCAD sheet sizes automatically

**Alternatives considered**:
- **Default DPI = 300**: Higher quality but A1 pages consume ~200 MB RAM per page; less practical for batch processing without explicit user opt-in
- **Enforce minimum by DPI value alone**: Fails for non-standard sheet sizes where the same DPI yields different pixel dimensions
- **Enforce by scaling up the rendered image**: Introduces bicubic interpolation artifacts that degrade fine line quality in floor plans

---

## Decision 4: OOP Project Structure

**Decision**: `src/` layout with domain-oriented packages (`config/`, `models/`, `services/`, `reporting/`, `cli/`)

**Rationale**:
- `src/` layout prevents test runs from accidentally importing the local source directory instead of the installed package, catching import errors early
- Domain packages enforce Single Responsibility Principle at the module level — each package has one clear purpose
- Enables independent unit testing of each service without importing the entire application
- Consistent with modern Python packaging recommendations (Hatchling, uv)

**Structure**:
```
src/pdf_png_converter/
├── config/      # ConfigLoader, ConversionConfig
├── models/      # ConversionJob, ConversionResult, ConversionStatus
├── services/    # PdfScanner, PathResolver, DirectoryBuilder, PdfRenderer, ConversionOrchestrator
├── reporting/   # ConversionReporter
└── cli/         # CLI entry point (main.py)
```

---

## Decision 5: Testing Framework

**Decision**: pytest, run via `uv run pytest`

**Rationale**:
- pytest is the industry standard for Python; rich plugin ecosystem (pytest-cov for coverage)
- `uv run pytest` executes in the project virtual environment without activation boilerplate
- Three-layer test suite: unit (mocked dependencies), integration (real filesystem, small PDFs), end-to-end (full pipeline with actual AutoCAD-style PDFs in fixtures/)
- Test fixtures (sample PDFs) stored in `tests/fixtures/` and never gitignored — required for integration and e2e tests

---

## Decision 6: Python Version Targeting

**Decision**: `requires-python = ">=3.14"`

**Rationale**:
- User explicitly specified Python 3.14.3
- Python 3.14 was released October 2025; 3.14.x patch releases follow
- `tomllib`, `dataclasses`, `pathlib`, `logging` are all stdlib — no version-gated workarounds needed
- PyMuPDF's Stable ABI wheel strategy guarantees compatibility with 3.14+
