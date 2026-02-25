# Data Model: PDF to PNG Converter

**Branch**: `001-pdf-png-converter` | **Date**: 2026-02-25

---

## Entities and Value Objects

### `ConversionConfig` — Value Object

Immutable, typed container of all conversion parameters. Populated from the TOML config file; falls back to built-in defaults for any absent key.

| Field | Type | Default | Description |
|---|---|---|---|
| `dpi` | `int` | `200` | Target rendering resolution in dots per inch |
| `min_width_px` | `int` | `3000` | Minimum required pixel count on the long dimension |
| `min_height_px` | `int` | `2000` | Minimum required pixel count on the short dimension |
| `import_dir` | `Path` | `Path("import")` | Root directory to scan for PDF files |
| `export_dir` | `Path` | `Path("export")` | Root directory to write PNG files |
| `overwrite_existing` | `bool` | `True` | Whether to overwrite existing PNG files in export |

**Validation rules**:
- `dpi` must be a positive integer; if below the DPI required to meet minimum pixel dimensions, emit a warning and increase DPI automatically
- `import_dir` must be a directory path (need not exist at config-load time — existence is checked at scan time)
- `export_dir` path is created automatically if it does not exist

**Immutability**: Implemented as a `@dataclass(frozen=True)`.

---

### `ConversionStatus` — Enumeration

Represents the lifecycle state of a single PDF conversion job.

| Value | Meaning |
|---|---|
| `PENDING` | Discovered, not yet processed |
| `SUCCESS` | All pages converted successfully |
| `SKIPPED` | File could not be read or had no renderable pages |
| `ERROR` | Processing started but failed partway through |

---

### `ConversionJob` — Entity

Tracks the full state of converting one PDF file. Created by `PdfScanner`, updated by `ConversionOrchestrator`, read by `ConversionReporter`.

| Field | Type | Description |
|---|---|---|
| `source_path` | `Path` | Absolute path to the PDF file in `import_dir` |
| `relative_path` | `Path` | Path relative to `import_dir` (used to compute export location) |
| `status` | `ConversionStatus` | Current lifecycle state |
| `output_paths` | `list[Path]` | Absolute paths of successfully written PNG files |
| `error_message` | `str \| None` | Human-readable error detail; `None` when status is SUCCESS |
| `page_count` | `int \| None` | Total pages in the PDF; `None` until the file is opened |

**State transitions**:
```
PENDING → SUCCESS   (all pages rendered and saved)
PENDING → SKIPPED   (file unreadable, zero bytes, or no renderable pages)
PENDING → ERROR     (file opened but partial failure during page rendering)
```

**Relationships**:
- One `ConversionJob` → zero or more `ConversionResult` (one per page)
- One `ConversionJob` → one `ConversionConfig` (shared across all jobs in a run)

---

### `ConversionResult` — Value Object

Immutable record of a successfully converted single page. Produced by `PdfRenderer`.

| Field | Type | Description |
|---|---|---|
| `output_path` | `Path` | Absolute path of the written PNG file |
| `width_px` | `int` | Actual width of the output PNG in pixels |
| `height_px` | `int` | Actual height of the output PNG in pixels |
| `page_number` | `int` | 1-based page index within the source PDF |
| `dpi_used` | `int` | Actual DPI used for rendering (may exceed configured value if auto-raised to meet minimum pixel dimensions) |

---

## Service Interfaces

### `PdfScanner`

**Responsibility**: Recursively discover all PDF files within a directory tree and create a `ConversionJob` for each.

```
scan(import_dir: Path) -> list[ConversionJob]
```

- Walks `import_dir` recursively (depth-first)
- Matches files with `.pdf` extension (case-insensitive)
- Returns an empty list (not an error) when no PDFs are found
- Does not open or validate PDF content — that is `PdfRenderer`'s responsibility

---

### `PathResolver`

**Responsibility**: Compute the correct export file path for a given source path and page number.

```
resolve_output_path(
    source_path: Path,
    import_dir: Path,
    export_dir: Path,
    page_number: int,
    total_pages: int
) -> Path
```

- Strips `import_dir` prefix from `source_path` to get the relative path
- Replaces `.pdf` extension with `.png`
- For `total_pages > 1`, appends `_page{N}` before the extension: `plan_page1.png`, `plan_page2.png`
- For `total_pages == 1`, no page suffix is added: `plan.png`
- Prepends `export_dir` to produce the absolute output path

---

### `DirectoryBuilder`

**Responsibility**: Ensure an output directory (and all parent directories) exists.

```
ensure_directory_exists(directory: Path) -> None
```

- Creates the directory and all missing intermediate parents (`mkdir -p` equivalent)
- Is a no-op if the directory already exists (idempotent)
- Raises `PermissionError` (propagated) if the filesystem denies creation

---

### `PdfRenderer`

**Responsibility**: Open one PDF file, render one page to a PNG at the target resolution, and write the PNG to disk.

```
render_page(
    source_path: Path,
    page_number: int,
    output_path: Path,
    config: ConversionConfig
) -> ConversionResult
```

- Opens the PDF document (read-only)
- Renders the specified page (0-based index internally; `page_number` is 1-based externally)
- Validates that rendered dimensions meet `min_width_px` × `min_height_px`
- If dimensions are insufficient, increases DPI by 50 and re-renders (up to 3 retries)
- Writes the PNG to `output_path` (creates parent directories via `DirectoryBuilder`)
- Releases pixmap memory immediately after saving (`del pix`)
- Returns a `ConversionResult` with actual dimensions and DPI used

```
get_page_count(source_path: Path) -> int
```

- Opens the PDF document and returns its page count without rendering
- Used by `ConversionOrchestrator` to determine single-page vs. multi-page naming

---

### `ConversionOrchestrator`

**Responsibility**: Coordinate the complete conversion pipeline for a batch of jobs.

```
execute() -> list[ConversionJob]
```

- Calls `PdfScanner.scan()` to discover all jobs
- For each job: resolves paths, ensures directories, renders all pages
- Catches and records errors per job without halting the batch
- Returns the completed list of `ConversionJob` objects for reporting

**Constructor dependencies** (injected, not constructed internally):
- `scanner: PdfScanner`
- `path_resolver: PathResolver`
- `directory_builder: DirectoryBuilder`
- `renderer: PdfRenderer`
- `reporter: ConversionReporter`
- `config: ConversionConfig`

---

### `ConfigLoader`

**Responsibility**: Load a TOML config file, merge with defaults, and return a validated `ConversionConfig`.

```
load(config_path: Path) -> ConversionConfig
```

- Reads `config_path` using `tomllib`
- Deep-merges user values over built-in defaults
- Warns (does not raise) for missing file or malformed TOML — falls back to defaults
- Validates logical constraints (positive DPI, valid directory path format)

---

### `ConversionReporter`

**Responsibility**: Produce a human-readable conversion summary to stdout/stderr.

```
report(jobs: list[ConversionJob]) -> None
```

- Prints total counts: succeeded, skipped, errored
- Lists each errored/skipped job with its error message
- Output format: structured text suitable for terminal reading; no machine-parseable format required

---

## Class Relationship Diagram

```
ConversionConfig (Value Object)
  └── used by: ConfigLoader, PdfRenderer, ConversionOrchestrator

ConversionJob (Entity)
  ├── created by: PdfScanner
  ├── updated by: ConversionOrchestrator
  └── read by: ConversionReporter

ConversionResult (Value Object)
  └── produced by: PdfRenderer, collected in ConversionJob.output_paths

ConversionOrchestrator (Service — Coordinator)
  ├── depends on: PdfScanner
  ├── depends on: PathResolver
  ├── depends on: DirectoryBuilder
  ├── depends on: PdfRenderer
  ├── depends on: ConversionReporter
  └── depends on: ConversionConfig

CLI main()
  ├── constructs: ConfigLoader → ConversionConfig
  └── constructs + runs: ConversionOrchestrator
```

---

## Configuration Schema

Stored in `config.toml` at the project root.

```toml
# PDF to PNG Converter — Configuration File
# Edit this file to adjust conversion parameters.

[conversion]
# Rendering resolution. Higher = sharper output and larger files.
# Default: 200 DPI (produces ~4678×6622 px for A1, ~2338×3308 px for A3).
dpi = 200

# Minimum output dimensions in pixels. Converter will raise DPI automatically
# if rendered output falls below these values.
min_width_px = 3000
min_height_px = 2000

[paths]
# Directory containing source PDF files (relative to project root or absolute).
import_dir = "import"

# Directory for output PNG files (created automatically if absent).
export_dir = "export"
```
