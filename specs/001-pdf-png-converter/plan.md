# Implementation Plan: PDF to PNG Converter

**Branch**: `001-pdf-png-converter` | **Date**: 2026-02-25 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/001-pdf-png-converter/spec.md`

---

## Summary

A command-line tool that recursively converts AutoCAD-exported PDF floor plan files in an `/import` directory to high-resolution PNG images in an `/export` directory, mirroring the source folder structure. Output resolution is user-configurable via a TOML config file, with a hard minimum of 3000×2000 pixels. Built in Python 3.14 using PyMuPDF for rendering, with an Object-Oriented architecture following SOLID/DRY principles and a full TDD test suite (unit, integration, end-to-end).

---

## Technical Context

**Language/Version**: Python 3.14.3
**Primary Dependencies**: `pymupdf>=1.25.0` (PDF rendering), `tomllib` (stdlib, TOML config)
**Storage**: Local filesystem (`import/` → `export/`); no database
**Testing**: `pytest>=8.0`, `pytest-cov>=5.0` via `uv run pytest`
**Target Platform**: Single Linux/macOS workstation
**Project Type**: CLI tool
**Performance Goals**: Batch of 50 single-page A3 PDFs at 200 DPI completes without crash or manual restart; peak RAM per page ≤ 100 MB
**Constraints**: One page in memory at a time; no concurrent multi-process rendering required; no network access
**Scale/Scope**: Single workstation; 50+ PDF files per batch; standard AutoCAD sheet sizes (A4 through A0)

---

## Constitution Check

*The project constitution is unpopulated (template only). The following gates are derived from the user-specified architecture constraints instead.*

| Gate | Status | Notes |
|---|---|---|
| OOP with SOLID principles | PASS | All classes have single, clear responsibilities; dependencies injected via constructor |
| DRY | PASS | Path resolution logic, directory creation, and rendering are each implemented once and reused |
| Single Responsibility per method | PASS | Each method performs exactly one action; no compound methods |
| Declarative naming | PASS | All classes and methods named by role: `scan`, `resolve_output_path`, `ensure_directory_exists`, `render_page`, `report` |
| TDD enforced | PASS | Tests are defined before implementation; Red → Green → Refactor cycle required |
| Memory safety | PASS | PyMuPDF pixmap released (`del pix`) immediately after saving; one page in memory at a time |
| No implementation leakage to spec | PASS | Spec is technology-agnostic; technical decisions confined to plan and research |

---

## Project Structure

### Documentation (this feature)

```text
specs/001-pdf-png-converter/
├── plan.md              # This file (/speckit.plan output)
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/
│   ├── cli.md           # CLI invocation contract
│   └── config-schema.md # Configuration file schema
└── tasks.md             # Phase 2 output (/speckit.tasks — not yet created)
```

### Source Code (repository root)

```text
pdf-png-converter/
├── config.toml                             # User-editable conversion settings
├── config.toml.example                     # Example/documented config template
├── pyproject.toml                          # Project metadata + tool configuration
├── uv.lock                                 # Locked dependency graph (committed)
├── import/                                 # Source PDF drop zone (gitignored)
├── export/                                 # PNG output zone (gitignored)
│
├── src/
│   └── pdf_png_converter/
│       ├── __init__.py
│       │
│       ├── cli/
│       │   ├── __init__.py
│       │   └── main.py                     # CLI entry point; wires all dependencies
│       │
│       ├── config/
│       │   ├── __init__.py
│       │   ├── config_loader.py            # ConfigLoader: reads TOML, merges defaults
│       │   └── conversion_config.py        # ConversionConfig: frozen dataclass
│       │
│       ├── models/
│       │   ├── __init__.py
│       │   ├── conversion_job.py           # ConversionJob: mutable entity per PDF
│       │   ├── conversion_result.py        # ConversionResult: immutable per-page outcome
│       │   └── conversion_status.py        # ConversionStatus: enum (PENDING/SUCCESS/SKIPPED/ERROR)
│       │
│       ├── services/
│       │   ├── __init__.py
│       │   ├── pdf_scanner.py              # PdfScanner: discovers PDFs recursively
│       │   ├── path_resolver.py            # PathResolver: import path → export path mapping
│       │   ├── directory_builder.py        # DirectoryBuilder: ensures output dirs exist
│       │   ├── pdf_renderer.py             # PdfRenderer: renders one page to PNG (PyMuPDF)
│       │   └── conversion_orchestrator.py  # ConversionOrchestrator: pipeline coordinator
│       │
│       └── reporting/
│           ├── __init__.py
│           └── conversion_reporter.py      # ConversionReporter: prints summary
│
└── tests/
    ├── conftest.py                         # Shared fixtures (tmp paths, sample configs)
    ├── fixtures/
    │   └── pdfs/
    │       ├── single_page.pdf             # Valid 1-page PDF fixture
    │       ├── multi_page.pdf              # Valid 3-page PDF fixture
    │       └── corrupted.pdf               # Invalid PDF fixture
    │
    ├── unit/
    │   ├── config/
    │   │   ├── test_config_loader.py
    │   │   └── test_conversion_config.py
    │   ├── models/
    │   │   ├── test_conversion_job.py
    │   │   └── test_conversion_result.py
    │   ├── services/
    │   │   ├── test_pdf_scanner.py
    │   │   ├── test_path_resolver.py
    │   │   ├── test_directory_builder.py
    │   │   ├── test_pdf_renderer.py
    │   │   └── test_conversion_orchestrator.py
    │   └── reporting/
    │       └── test_conversion_reporter.py
    │
    ├── integration/
    │   ├── test_scan_and_resolve.py        # Scanner + PathResolver together
    │   └── test_pipeline_integration.py   # Orchestrator + real filesystem (no render)
    │
    └── e2e/
        └── test_full_conversion.py         # Full pipeline: PDF in → PNG out
```

**Structure Decision**: Single-project OOP layout with `src/` packaging. Domain packages (`config/`, `models/`, `services/`, `reporting/`, `cli/`) enforce package-level Single Responsibility. The `src/` layout prevents test runs from accidentally importing uninstalled source. Tests mirror the source tree for discoverability.

---

## Class Design

### `ConversionConfig` — `src/pdf_png_converter/config/conversion_config.py`

```python
@dataclass(frozen=True)
class ConversionConfig:
    dpi: int = 200
    min_width_px: int = 3000
    min_height_px: int = 2000
    import_dir: Path = Path("import")
    export_dir: Path = Path("export")
```

### `ConfigLoader` — `src/pdf_png_converter/config/config_loader.py`

```python
class ConfigLoader:
    def load(self, config_path: Path) -> ConversionConfig: ...
    def _merge_with_defaults(self, user_values: dict) -> ConversionConfig: ...
    def _validate(self, config: ConversionConfig) -> ConversionConfig: ...
```

### `ConversionStatus` — `src/pdf_png_converter/models/conversion_status.py`

```python
class ConversionStatus(Enum):
    PENDING = "pending"
    SUCCESS = "success"
    SKIPPED = "skipped"
    ERROR = "error"
```

### `ConversionJob` — `src/pdf_png_converter/models/conversion_job.py`

```python
@dataclass
class ConversionJob:
    source_path: Path
    relative_path: Path
    status: ConversionStatus = ConversionStatus.PENDING
    output_paths: list[Path] = field(default_factory=list)
    error_message: str | None = None
    page_count: int | None = None
```

### `ConversionResult` — `src/pdf_png_converter/models/conversion_result.py`

```python
@dataclass(frozen=True)
class ConversionResult:
    output_path: Path
    width_px: int
    height_px: int
    page_number: int
    dpi_used: int
```

### `PdfScanner` — `src/pdf_png_converter/services/pdf_scanner.py`

```python
class PdfScanner:
    def scan(self, import_dir: Path) -> list[ConversionJob]: ...
    def _is_pdf_file(self, path: Path) -> bool: ...
```

### `PathResolver` — `src/pdf_png_converter/services/path_resolver.py`

```python
class PathResolver:
    def resolve_output_path(
        self,
        source_path: Path,
        import_dir: Path,
        export_dir: Path,
        page_number: int,
        total_pages: int,
    ) -> Path: ...
    def _build_relative_output_path(self, relative_source: Path, page_number: int, total_pages: int) -> Path: ...
```

### `DirectoryBuilder` — `src/pdf_png_converter/services/directory_builder.py`

```python
class DirectoryBuilder:
    def ensure_directory_exists(self, directory: Path) -> None: ...
```

### `PdfRenderer` — `src/pdf_png_converter/services/pdf_renderer.py`

```python
class PdfRenderer:
    def get_page_count(self, source_path: Path) -> int: ...
    def render_page(
        self,
        source_path: Path,
        page_number: int,
        output_path: Path,
        config: ConversionConfig,
    ) -> ConversionResult: ...
    def _meets_minimum_dimensions(self, width: int, height: int, config: ConversionConfig) -> bool: ...
    def _calculate_required_dpi(self, page, config: ConversionConfig) -> int: ...
```

### `ConversionOrchestrator` — `src/pdf_png_converter/services/conversion_orchestrator.py`

```python
class ConversionOrchestrator:
    def __init__(
        self,
        scanner: PdfScanner,
        path_resolver: PathResolver,
        directory_builder: DirectoryBuilder,
        renderer: PdfRenderer,
        reporter: ConversionReporter,
        config: ConversionConfig,
    ) -> None: ...

    def execute(self) -> list[ConversionJob]: ...
    def _process_job(self, job: ConversionJob) -> ConversionJob: ...
    def _render_all_pages(self, job: ConversionJob) -> ConversionJob: ...
```

### `ConversionReporter` — `src/pdf_png_converter/reporting/conversion_reporter.py`

```python
class ConversionReporter:
    def report(self, jobs: list[ConversionJob]) -> None: ...
    def _print_job_line(self, job: ConversionJob) -> None: ...
    def _print_summary(self, jobs: list[ConversionJob]) -> None: ...
```

### `main` — `src/pdf_png_converter/cli/main.py`

```python
def main() -> None:
    args = _parse_arguments()
    config = _load_config(args)
    orchestrator = _build_orchestrator(config)
    orchestrator.execute()
```

---

## TDD Test Plan

### Unit Tests

Each unit test mocks all external dependencies (filesystem, PyMuPDF). Tests are written **before** implementation.

| Test File | What It Tests |
|---|---|
| `test_config_loader.py` | Missing file → defaults; malformed TOML → defaults + warning; partial config → merged; DPI ≤ 0 → warning + default |
| `test_conversion_config.py` | Frozen (immutable); correct defaults; field types |
| `test_conversion_job.py` | Default status is PENDING; status transitions; output_paths accumulation |
| `test_conversion_result.py` | Immutable; all fields stored correctly |
| `test_pdf_scanner.py` | Empty dir → []; PDFs in subdirs discovered; non-PDF files ignored; `.PDF` (uppercase) matched |
| `test_path_resolver.py` | Single-page: no suffix; multi-page: `_page1`, `_page2`; nested paths; export dir prepended |
| `test_directory_builder.py` | Creates missing dir; creates nested missing dirs; idempotent on existing dir |
| `test_pdf_renderer.py` | Page count returned; DPI auto-raised when dimensions insufficient; pixmap freed after save |
| `test_conversion_orchestrator.py` | All jobs processed; corrupted PDF → SKIPPED; one error does not stop batch; output_paths populated |
| `test_conversion_reporter.py` | Success count correct; skip count correct; error messages printed to stderr |

### Integration Tests

Use real filesystem (pytest `tmp_path`) and small fixture PDFs. PyMuPDF is **not** mocked.

| Test File | What It Tests |
|---|---|
| `test_scan_and_resolve.py` | Scanner finds fixtures; PathResolver produces correct mirrored paths |
| `test_pipeline_integration.py` | Orchestrator creates export dirs; corrupted.pdf produces SKIPPED job; multi_page.pdf produces 3 output paths |

### End-to-End Tests

Full pipeline, real PDFs in `tests/fixtures/pdfs/`, real output in `tmp_path`.

| Test File | What It Tests |
|---|---|
| `test_full_conversion.py` | single_page.pdf → PNG ≥ 3000×2000; multi_page.pdf → 3 PNGs with correct suffixes; folder structure mirrored; corrupted.pdf skipped, others processed; config DPI override applied to output dimensions |

---

## pyproject.toml

```toml
[project]
name = "pdf-png-converter"
version = "0.1.0"
description = "Convert AutoCAD-exported PDF floor plans to high-resolution PNG images"
requires-python = ">=3.14"
dependencies = [
    "pymupdf>=1.25.0",
]

[project.scripts]
pdf-png-converter = "pdf_png_converter.cli.main:main"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.uv]
dev-dependencies = [
    "pytest>=8.0",
    "pytest-cov>=5.0",
]

[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = "--cov=pdf_png_converter --cov-report=term-missing"

[tool.hatch.build.targets.wheel]
packages = ["src/pdf_png_converter"]
```

---

## Complexity Tracking

No constitution violations. All design choices align with stated OOP/SOLID/DRY/TDD constraints.

---

## Implementation Sequence (for `/speckit.tasks`)

Tasks will be generated in dependency order by `/speckit.tasks`. The natural implementation sequence is:

1. Project scaffolding (pyproject.toml, src layout, test layout, fixture PDFs)
2. Models layer — TDD: `ConversionStatus` → `ConversionConfig` → `ConversionJob` → `ConversionResult`
3. Config layer — TDD: `ConfigLoader` (unit tests first, then implementation)
4. Services layer — TDD order by dependency:
   - `PdfScanner`
   - `PathResolver`
   - `DirectoryBuilder`
   - `PdfRenderer`
   - `ConversionOrchestrator`
5. Reporting layer — TDD: `ConversionReporter`
6. CLI layer — `main.py` wiring
7. Integration tests
8. End-to-end tests
9. config.toml + config.toml.example
10. README / quickstart validation
