# Tasks: PDF to PNG Converter

**Input**: Design documents from `/specs/001-pdf-png-converter/`
**Prerequisites**: plan.md ✓, spec.md ✓, research.md ✓, data-model.md ✓, contracts/ ✓

**Tests**: TDD explicitly requested — test tasks are written **before** implementation tasks in every phase. Each test MUST fail (Red) before implementation begins.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story?] Description`

- **[P]**: Can run in parallel (different files, no dependencies on each other)
- **[Story]**: Which user story this task belongs to (US1, US2, US3)
- Exact file paths are included in every task description

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project scaffolding, dependency installation, test fixture creation. Must complete before any implementation.

- [x] T001 Create complete directory structure: `src/pdf_png_converter/{cli,config,models,services,reporting}/`, `tests/{unit/{config,models,services,reporting},integration,e2e,fixtures/pdfs}/` with `__init__.py` in each package
- [x] T002 Configure `pyproject.toml` with `requires-python = ">=3.14"`, `pymupdf>=1.25.0` runtime dependency, `pytest>=8.0` and `pytest-cov>=5.0` dev dependencies, `pdf-png-converter = "pdf_png_converter.cli.main:main"` entry point, and `[tool.pytest.ini_options]` testpaths and addopts
- [x] T003 [P] Run `uv sync` to install all dependencies and verify `uv run pdf-png-converter --help` can be invoked (will fail until main.py exists — acceptable at this stage)
- [x] T004 [P] Create `config.toml` at project root with documented default settings per `contracts/config-schema.md` (dpi=200, min_width_px=3000, min_height_px=2000, import_dir="import", export_dir="export")
- [x] T005 [P] Create `config.toml.example` as a fully-commented reference copy of `config.toml` matching the schema in `contracts/config-schema.md`
- [x] T006 [P] Add `import/`, `export/`, `.pytest_cache/`, `htmlcov/`, `__pycache__/`, `*.pyc`, and `.coverage` to `.gitignore`; create `import/.gitkeep` and `export/.gitkeep`
- [x] T007 Generate three test fixture PDFs in `tests/fixtures/pdfs/` using PyMuPDF: `single_page.pdf` (1 A3 page with sample floor plan content), `multi_page.pdf` (3 pages), and `corrupted.pdf` (invalid byte sequence); create `tests/fixtures/create_fixtures.py` as the generator script

**Checkpoint**: Repository structure exists, `uv sync` succeeds, fixture PDFs are in place.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: All data model classes and the config loading service that every user story depends on. TDD: write tests first, verify they fail, then implement.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

### Tests First — Models & Config

- [x] T008 [P] Write unit tests for `ConversionStatus` enum in `tests/unit/models/test_conversion_status.py`: verify all four values (PENDING, SUCCESS, SKIPPED, ERROR) exist and have correct string values
- [x] T009 [P] Write unit tests for `ConversionConfig` frozen dataclass in `tests/unit/config/test_conversion_config.py`: verify default field values, frozen (immutable) behavior raises `FrozenInstanceError`, and `Path` types for directory fields
- [x] T010 [P] Write unit tests for `ConversionJob` mutable dataclass in `tests/unit/models/test_conversion_job.py`: verify default status is PENDING, output_paths accumulates, error_message starts as None, page_count starts as None, status transitions are writable
- [x] T011 [P] Write unit tests for `ConversionResult` frozen dataclass in `tests/unit/models/test_conversion_result.py`: verify all fields stored correctly, frozen behavior, and that `dpi_used` captures the actual DPI applied

### Verify Tests Fail (Red)

- [x] T012 Run `uv run pytest tests/unit/` and confirm all model/config tests fail with `ModuleNotFoundError` or `ImportError`

### Implement Models & Config

- [x] T013 [P] Implement `ConversionStatus` enum in `src/pdf_png_converter/models/conversion_status.py` (after T012 confirms T008 fails)
- [x] T014 [P] Implement `ConversionConfig` frozen dataclass in `src/pdf_png_converter/config/conversion_config.py` (after T012 confirms T009 fails)
- [x] T015 Implement `ConversionJob` mutable dataclass in `src/pdf_png_converter/models/conversion_job.py` — import `ConversionStatus` from models package (depends on T013)
- [x] T016 [P] Implement `ConversionResult` frozen dataclass in `src/pdf_png_converter/models/conversion_result.py` (after T012 confirms T011 fails)

### Config Loader — TDD

- [x] T017 Write unit tests for `ConfigLoader.load()` in `tests/unit/config/test_config_loader.py`: test missing config file → warning + full defaults; malformed TOML → warning + full defaults; partial config → merged with defaults; DPI ≤ 0 → warning + default DPI; all keys present → values used as-is
- [x] T018 Implement `ConfigLoader` in `src/pdf_png_converter/config/config_loader.py`: `load(config_path: Path) -> ConversionConfig` using `tomllib`, deep-merge with defaults, log warnings via `logging` module (depends on T014, T017)

### Shared Test Infrastructure

- [x] T019 Create `tests/conftest.py` with shared pytest fixtures: `sample_config` (ConversionConfig with test paths), `tmp_import_dir` and `tmp_export_dir` (pytest `tmp_path` sub-directories), `single_page_pdf_path` and `multi_page_pdf_path` and `corrupted_pdf_path` (pointing to `tests/fixtures/pdfs/`)
- [x] T020 Verify all foundational tests pass: run `uv run pytest tests/unit/` — all T008–T011 and T017 tests must be Green before proceeding

**Checkpoint**: All model and config tests pass. Foundation ready — user story phases can proceed.

---

## Phase 3: User Story 1 — Core PDF Conversion Pipeline (Priority: P1) 🎯 MVP

**Goal**: Convert any PDF file placed in `/import` to a PNG in `/export` at or above the minimum configured resolution. Handles single-page PDFs, corrupted files (skip + log), and auto-creates the export directory.

**Independent Test**: Place `tests/fixtures/pdfs/single_page.pdf` in a temp `/import` directory, run the converter, verify a `.png` appears in the temp `/export` directory with dimensions ≥ 3000×2000.

### Unit Tests — US1 Services (Write First, Verify Fail, Then Implement)

- [x] T021 [P] [US1] Write unit tests for `PdfScanner.scan()` in `tests/unit/services/test_pdf_scanner.py`: empty directory → empty list; directory with 2 PDFs → 2 ConversionJobs; `.PDF` uppercase extension matched; non-PDF files ignored; each job has correct `source_path` and `relative_path`; jobs start with PENDING status
- [x] T022 [P] [US1] Write unit tests for `PathResolver.resolve_output_path()` in `tests/unit/services/test_path_resolver.py`: single-page (total=1) → no `_pageN` suffix, `.pdf` → `.png` extension; multi-page (total=3) → `_page1.png`, `_page2.png`, `_page3.png` suffixes; export dir prepended correctly; nested path (import/a/b/c.pdf → export/a/b/c.png)
- [x] T023 [P] [US1] Write unit tests for `DirectoryBuilder.ensure_directory_exists()` in `tests/unit/services/test_directory_builder.py`: creates missing directory; creates all missing intermediate parents; is a no-op if directory already exists (idempotent); propagates `PermissionError`
- [x] T024 [P] [US1] Write unit tests for `PdfRenderer` in `tests/unit/services/test_pdf_renderer.py`: `get_page_count()` returns correct count for single and multi-page fixture PDFs; `render_page()` raises when source is corrupted; pixmap is freed after save (no memory leak — mock `del` behavior); `_meets_minimum_dimensions()` returns True above threshold and False below; `_calculate_required_dpi()` returns higher DPI when initial render is too small
- [x] T025 [P] [US1] Write unit tests for `ConversionOrchestrator.execute()` in `tests/unit/services/test_conversion_orchestrator.py`: all mocked — verify `scanner.scan()` called once; `renderer.render_page()` called once per page; corrupted PDF job transitions to SKIPPED; one error does not stop batch; `reporter.report()` called once with completed jobs list
- [x] T026 [P] [US1] Write unit tests for `ConversionReporter.report()` in `tests/unit/reporting/test_conversion_reporter.py`: correct success count in output; correct skip count; correct error count; skipped/errored job error messages appear in output; summary separator line printed; empty job list produces zero counts

### Verify Unit Tests Fail (Red)

- [x] T027 [US1] Run `uv run pytest tests/unit/services/ tests/unit/reporting/` — confirm all T021–T026 tests fail before implementation begins

### Implement US1 Services (Green)

- [x] T028 [US1] Implement `PdfScanner` in `src/pdf_png_converter/services/pdf_scanner.py`: `scan(import_dir: Path) -> list[ConversionJob]` walks directory recursively, matches `.pdf` case-insensitively, creates one `ConversionJob` per file with `relative_path = source_path.relative_to(import_dir)` (depends on T015, T027)
- [x] T029 [US1] Implement `PathResolver` in `src/pdf_png_converter/services/path_resolver.py`: `resolve_output_path(source, import_dir, export_dir, page_number, total_pages) -> Path`; `_build_relative_output_path()` handles suffix and extension logic; single-page omits `_pageN` suffix (depends on T027)
- [x] T030 [US1] Implement `DirectoryBuilder` in `src/pdf_png_converter/services/directory_builder.py`: `ensure_directory_exists(directory: Path) -> None` calls `directory.mkdir(parents=True, exist_ok=True)` (depends on T027)
- [x] T031 [US1] Implement `PdfRenderer` in `src/pdf_png_converter/services/pdf_renderer.py` using `pymupdf`: `get_page_count()` opens doc and returns `len(doc)`; `render_page()` opens doc, renders page at target DPI via `page.get_pixmap(dpi=dpi)`, calls `_meets_minimum_dimensions()`, calls `_calculate_required_dpi()` if needed (retries up to 3 times at +50 DPI increments), saves to `output_path`, runs `del pix` immediately (depends on T014, T027)
- [x] T032 [US1] Implement `ConversionOrchestrator` in `src/pdf_png_converter/services/conversion_orchestrator.py`: `execute() -> list[ConversionJob]`; `_process_job(job)` catches all exceptions, sets SKIPPED/ERROR status; `_render_all_pages(job)` iterates pages; all 6 dependencies injected via `__init__` (depends on T028–T031, T027)
- [x] T033 [US1] Implement `ConversionReporter` in `src/pdf_png_converter/reporting/conversion_reporter.py`: `report(jobs)` prints per-job `[OK]`/`[SKIP]` lines to stdout and summary block; `_print_summary()` prints separator and counts (depends on T015, T016, T027)
- [x] T034 [US1] Implement CLI `main()` in `src/pdf_png_converter/cli/main.py`: parse `--config`, `--import-dir`, `--export-dir`, `--dpi`, `--help`, `--version` using `argparse`; load config via `ConfigLoader`; apply CLI overrides; construct all services; call `orchestrator.execute()` with exit code mapping per `contracts/cli.md` (depends on T018, T028–T033)

### Integration Tests — US1

- [x] T035 [US1] Write integration test in `tests/integration/test_scan_and_resolve.py`: create real temp directory tree with 2 PDF fixtures at different paths; call `PdfScanner.scan()` on it; call `PathResolver.resolve_output_path()` for each job; assert output paths are under `export_dir` and extensions are `.png`
- [x] T036 [US1] Write integration test in `tests/integration/test_pipeline_integration.py`: use real filesystem with fixture PDFs; `corrupted.pdf` → job status is SKIPPED after `execute()`; `multi_page.pdf` → 3 output path entries in `job.output_paths`; `single_page.pdf` → 1 output path entry; export directory auto-created

### End-to-End Test — US1

- [x] T037 [US1] Write E2E test in `tests/e2e/test_full_conversion.py`: copy `single_page.pdf` fixture to temp import dir; call `uv run pdf-png-converter --import-dir <tmp> --export-dir <tmp_export>`; assert PNG file exists in tmp_export; open PNG with `pymupdf` or `PIL` and assert dimensions ≥ 3000×2000; assert exit code is 0

### Verify US1 Complete

- [x] T038 [US1] Run full test suite: `uv run pytest` — all unit, integration, and E2E tests must pass (Green)

**Checkpoint**: User Story 1 is fully functional and independently testable. MVP delivered.

---

## Phase 4: User Story 2 — Folder Structure Mirroring (Priority: P2)

**Goal**: The directory tree under `/export` exactly mirrors the tree under `/import`. Running the converter on nested subdirectories produces the same hierarchy in `/export` with no missing or extra directories.

**Independent Test**: Place fixture PDFs in two levels of nested subdirectories under a temp `/import`; run converter; verify the same directory tree (with PNGs) appears under temp `/export`.

> **Note**: `PathResolver` (implemented in T029) and `DirectoryBuilder` (T030) already contain the core mirroring logic. This phase adds edge-case tests and dedicated E2E verification for nested scenarios.

### Tests — US2

- [x] T039 [P] [US2] Extend unit tests in `tests/unit/services/test_path_resolver.py` with nested path edge cases: 3-level deep path `a/b/c/plan.pdf` → `a/b/c/plan.png`; path with spaces `project a/floor 1/plan.pdf` → correctly resolved; special characters in directory names; path with only root-level file (no subdirectory)
- [x] T040 [P] [US2] Write integration test in `tests/integration/test_pipeline_integration.py` for nested structure: create `tmp_import/project-a/floor-1/plan.pdf` and `tmp_import/project-b/site.pdf` from fixtures; run orchestrator; assert `tmp_export/project-a/floor-1/plan.png` and `tmp_export/project-b/site.png` exist; assert no extra directories exist in `tmp_export`

### E2E Test — US2

- [x] T041 [US2] Write E2E test in `tests/e2e/test_full_conversion.py` for mirrored structure: create 3-level nested import directory with 3 fixture PDFs; run CLI; verify export tree exactly mirrors import tree; verify PNG count equals PDF count (no extras, no missing)

### Verify US2 Complete

- [x] T042 [US2] Run `uv run pytest tests/ -k "nested or structure or mirror"` and then full `uv run pytest` — all tests must pass

**Checkpoint**: User Stories 1 AND 2 are independently functional. Nested directory mirroring verified.

---

## Phase 5: User Story 3 — Configurable Resolution (Priority: P3)

**Goal**: Users control output resolution by editing `config.toml` only. Converter warns and enforces the 3000×2000 minimum if configured DPI would produce undersized output. Absent or malformed config falls back to built-in defaults.

**Independent Test**: Set `dpi = 300` in config; run converter on a fixture PDF; open output PNG; assert dimensions are larger than those produced with `dpi = 200`.

### Tests — US3 (Write First)

- [x] T043 [P] [US3] Extend unit tests in `tests/unit/config/test_config_loader.py` with resolution-specific cases: config with `dpi = 50` (below practical minimum) → warning emitted; config with `min_width_px = 0` → warning + default applied; config with valid `dpi = 400` → `ConversionConfig.dpi == 400`; partial `[paths]` section only → conversion defaults remain; missing entire `[conversion]` section → all conversion defaults remain
- [x] T044 [P] [US3] Extend unit tests in `tests/unit/services/test_pdf_renderer.py` with DPI auto-raise cases: mock page where DPI=150 renders 1800×2500 (fails height minimum) → `_calculate_required_dpi()` raises DPI; mock page where DPI=200 renders 4678×6622 (passes) → no DPI raise; assert `ConversionResult.dpi_used` reflects the actual DPI applied, not the configured DPI

### Implement US3 Behaviour

- [x] T045 [US3] Verify DPI auto-raise loop in `PdfRenderer._calculate_required_dpi()` in `src/pdf_png_converter/services/pdf_renderer.py` correctly increments by 50 DPI up to 3 retries before raising an error (review T031 implementation — add retry logic if not yet present)
- [x] T046 [US3] Verify CLI overrides `--dpi`, `--import-dir`, `--export-dir`, and `--config` in `src/pdf_png_converter/cli/main.py` all correctly override config file values per `contracts/cli.md` precedence rules (CLI > config > defaults)

### Integration Tests — US3

- [x] T047 [US3] Write integration test in `tests/integration/test_config_integration.py`: create a `config.toml` in temp dir with `dpi = 300`; run `ConfigLoader.load()` on it; assert resulting `ConversionConfig.dpi == 300`; create second config with `dpi = 0`; assert warning is logged and default DPI is used

### E2E Tests — US3

- [x] T048 [US3] Write E2E test in `tests/e2e/test_full_conversion.py` for config override: run CLI with `--dpi 300` on `single_page.pdf`; open output PNG; assert pixel dimensions are strictly larger than those from a `--dpi 200` run on the same file; assert exit code 0
- [x] T049 [US3] Write E2E test in `tests/e2e/test_full_conversion.py` for missing config: run CLI without `--config` flag and with no `config.toml` present; assert run completes with exit code 0 using default settings; assert WARNING line appears in stderr output

### Verify US3 Complete

- [x] T050 [US3] Run `uv run pytest` — full suite must be Green; spot-check config tests with `uv run pytest tests/ -k "config or dpi or resolution"`

**Checkpoint**: All three user stories are independently functional.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Full-suite validation, coverage, clean code pass.

- [x] T051 [P] Run `uv run pytest --cov=pdf_png_converter --cov-report=term-missing` and confirm overall coverage ≥ 90%; document any uncovered lines in a comment in `tests/conftest.py`
- [x] T052 [P] Add public-method docstrings to all service classes: `PdfScanner`, `PathResolver`, `DirectoryBuilder`, `PdfRenderer`, `ConversionOrchestrator`, `ConversionReporter`, `ConfigLoader` — one-line summary per method
- [x] T053 Validate `quickstart.md` end-to-end: follow every command in `specs/001-pdf-png-converter/quickstart.md` from a clean checkout (`uv sync` → place fixture PDF in import/ → run converter → verify PNG in export/)
- [x] T054 [P] Verify `config.toml.example` matches all fields documented in `specs/001-pdf-png-converter/contracts/config-schema.md`; update either if they diverge
- [x] T055 Final smoke test: run `uv run pdf-png-converter --help` and `uv run pdf-png-converter --version` and verify both print expected output without error

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately
- **Foundational (Phase 2)**: Depends on Phase 1 completion (fixture PDFs required for TDD validation)
- **User Story Phases (3–5)**: All depend on Phase 2 completion — BLOCKED until T020 passes
  - Phase 3 (US1) is the primary blocker; US2 and US3 can begin in parallel after US1 completes
- **Polish (Phase 6)**: Depends on all three user story phases passing

### User Story Dependencies

- **US1 (P1)**: Starts after Phase 2 — no dependency on US2 or US3
- **US2 (P2)**: Starts after Phase 2 — extends US1 tests but is independently testable; does not depend on US3
- **US3 (P3)**: Starts after Phase 2 — can extend US1 implementation; does not depend on US2

### Within Each User Story (TDD Cycle)

1. Write unit tests → verify they FAIL (Red)
2. Implement to make tests pass (Green)
3. Write integration tests → verify they pass
4. Write E2E tests → verify they pass
5. Run full suite before marking story complete

### Parallel Opportunities

- T003, T004, T005, T006, T007 — all Phase 1 tasks except T001, T002 are parallelizable
- T008, T009, T010, T011 — all model/config test writing tasks are parallelizable
- T013, T014, T016 — model implementations are parallelizable (no cross-dependencies)
- T021–T026 — all US1 unit test writing is parallelizable
- T039, T040 — US2 tests are parallelizable
- T043, T044 — US3 test writing is parallelizable

---

## Parallel Example: User Story 1 Unit Tests

```bash
# Write all US1 unit tests in parallel (different files, no dependencies):
Task: "Write PdfScanner unit tests in tests/unit/services/test_pdf_scanner.py"       # T021
Task: "Write PathResolver unit tests in tests/unit/services/test_path_resolver.py"   # T022
Task: "Write DirectoryBuilder unit tests in tests/unit/services/test_directory_builder.py" # T023
Task: "Write PdfRenderer unit tests in tests/unit/services/test_pdf_renderer.py"     # T024
Task: "Write ConversionOrchestrator unit tests"                                       # T025
Task: "Write ConversionReporter unit tests"                                           # T026

# Then implement services (sequential where dependencies exist):
Task: "Implement PdfScanner"     # T028
Task: "Implement PathResolver"   # T029 — parallel with T028
Task: "Implement DirectoryBuilder" # T030 — parallel with T028, T029
# T031 (PdfRenderer) → T032 (Orchestrator, depends on T028-T031) → T033 (Reporter)
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001–T007)
2. Complete Phase 2: Foundational (T008–T020) — **required, unblockable**
3. Complete Phase 3: User Story 1 (T021–T038)
4. **STOP and VALIDATE**: `uv run pdf-png-converter` converts a real AutoCAD PDF to PNG ≥ 3000×2000
5. Demo / use immediately

### Incremental Delivery

1. Setup + Foundational → skeleton ready
2. User Story 1 → core conversion working → **MVP demo**
3. User Story 2 → nested structure verified → batch project folders work
4. User Story 3 → resolution control → print-quality runs
5. Polish → coverage and docs complete

### Solo Developer Sequence

```
Phase 1 → Phase 2 → Phase 3 (US1) → Phase 4 (US2) → Phase 5 (US3) → Phase 6
```

Total: **55 tasks** across 6 phases.

---

## Notes

- `[P]` tasks touch different files — they can be executed concurrently by separate agents or developers
- `[US1/2/3]` labels map directly to user stories in `specs/001-pdf-png-converter/spec.md`
- **TDD is mandatory**: every implementation task has a corresponding test task that precedes it
- **Red before Green**: always run and confirm tests fail before writing implementation
- Commit after each checkpoint (end of each phase) for clean rollback points
- Memory safety: `del pix` after every `render_page()` call is a hard requirement — verify in T024 unit test
- AGPL license (PyMuPDF) is safe for this internal CLI use case — see `research.md` Decision 1
