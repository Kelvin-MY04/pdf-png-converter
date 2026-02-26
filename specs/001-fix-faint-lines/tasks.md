# Tasks: Fix Faint Lines in Exported PNG Images

**Input**: Design documents from `/specs/001-fix-faint-lines/`
**Prerequisites**: plan.md ✓, spec.md ✓, research.md ✓, data-model.md ✓, contracts/ ✓, quickstart.md ✓

**Tests**: Included — spec explicitly requires automated pixel contrast ratio verification (SC-001, SC-004).

**Organization**: Tasks are grouped by user story to enable independent implementation and testing.

## Format: `[ID] [P?] [Story?] Description`

- **[P]**: Can run in parallel (different files, no shared dependencies)
- **[US1]**: User Story 1 — Export PDF with Clear, Visible Lines (P1)
- **[US2]**: User Story 2 — Consistent Line Clarity Across Output Resolutions (P2)

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Create the new test fixture needed by integration tests in both user stories.

- [x] T001 Add `create_lines_pdf()` function to `tests/fixtures/create_fixtures.py` that draws a 0.5 pt black horizontal line and a 1.0 pt black horizontal line on a white A4 page, then regenerate `tests/fixtures/pdfs/lines.pdf`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core model and config changes that both user stories depend on. Must be complete before any user story work begins.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [x] T002 Create `RenderingOptions` frozen dataclass with `graphics_aa_level: int = 0` and `text_aa_level: int = 8` fields in `src/pdf_png_converter/models/rendering_options.py`
- [x] T003 [P] Export `RenderingOptions` from `src/pdf_png_converter/models/__init__.py` (depends on T002)
- [x] T004 [P] Add `rendering_options: RenderingOptions = field(default_factory=RenderingOptions)` to `ConversionConfig` in `src/pdf_png_converter/config/conversion_config.py` (depends on T002)

**Checkpoint**: `RenderingOptions` exists, `ConversionConfig` carries it — user story implementation can now begin.

---

## Phase 3: User Story 1 — Export PDF with Clear, Visible Lines (Priority: P1) 🎯 MVP

**Goal**: Fix the faint line defect by disabling anti-aliasing for vector graphics in `PdfRenderer`, wiring the AA level through `ConversionConfig`, and surfacing it in `config.toml`.

**Independent Test**: Run `uv run pytest tests/integration/test_line_visibility.py` — all stroke pixels in the rendered `lines.pdf` must achieve ≥ 4.5:1 WCAG contrast ratio against the white background.

### Tests for User Story 1

> **Write these tests FIRST and verify they FAIL before implementing.**

- [x] T005 [P] [US1] Write unit tests for `RenderingOptions` defaults (`graphics_aa_level==0`, `text_aa_level==8`) and frozen immutability in `tests/unit/models/test_rendering_options.py`
- [x] T006 [P] [US1] Add `TestConversionConfigRenderingOptions` class to `tests/unit/config/test_conversion_config.py` with tests: default `rendering_options` uses `RenderingOptions()`, custom `rendering_options` stored correctly
- [x] T007 [P] [US1] Add `TestConfigLoaderRenderingSection` class to `tests/unit/config/test_config_loader.py` with tests: loads `graphics_aa_level` from TOML, loads `text_aa_level` from TOML, missing section uses defaults, out-of-range value (e.g. 9) falls back to default with warning
- [x] T008 [P] [US1] Add `TestPdfRendererApplyRenderingOptions` class to `tests/unit/services/test_pdf_renderer.py` with tests: `_apply_rendering_options()` calls `pymupdf.TOOLS.set_graphics_aa_level` with correct value, calls `pymupdf.TOOLS.set_text_aa_level` with correct value, `render_page()` calls `_apply_rendering_options()` before `get_pixmap()` (use `unittest.mock.patch` for both TOOLS methods)

### Implementation for User Story 1

- [x] T009 [US1] Add `[conversion.rendering]` entry to `_DEFAULTS` dict (`graphics_aa_level: 0`, `text_aa_level: 8`) and extend `_merge_with_defaults()` to deep-merge the rendering sub-section in `src/pdf_png_converter/config/config_loader.py`
- [x] T010 [US1] Add `_validated_aa_level()` private method (validates int in 0–8, warns and falls back to default on invalid) and extend `_build_config()` to parse rendering options and construct `RenderingOptions` embedded in `ConversionConfig` in `src/pdf_png_converter/config/config_loader.py`
- [x] T011 [US1] Add `_apply_rendering_options(options: RenderingOptions) -> None` private method (calls `pymupdf.TOOLS.set_graphics_aa_level` and `pymupdf.TOOLS.set_text_aa_level`) and call it at the top of `render_page()` before the DPI calculation in `src/pdf_png_converter/services/pdf_renderer.py`
- [x] T012 [US1] Add `[conversion.rendering]` section with `graphics_aa_level = 0` and `text_aa_level = 8` (with inline comments) to `config.toml`
- [x] T013 [US1] Create `tests/integration/test_line_visibility.py` with: `wcag_contrast_ratio()` helper (WCAG 2.1 relative luminance formula), `test_thin_line_meets_contrast_threshold()` (renders `lines.pdf` at 200 DPI with `graphics_aa_level=0`, samples pixels along the 0.5 pt line y-coordinate, asserts ≥ 80% of sampled pixels achieve 4.5:1 contrast ratio against white background)
- [x] T014 [US1] Add to `tests/integration/test_line_visibility.py`: `test_standard_line_meets_contrast_threshold()` (same for 1.0 pt line) and `test_anti_aliased_render_fails_contrast_threshold()` (renders with `graphics_aa_level=8`, asserts ≥ 20% of sampled pixels FAIL the threshold — regression guard confirming fixture sensitivity)

**Checkpoint**: Run `uv run pytest tests/unit/ tests/integration/test_line_visibility.py` — all pass. User Story 1 is fully functional and independently verified.

---

## Phase 4: User Story 2 — Consistent Line Clarity Across Output Resolutions (Priority: P2)

**Goal**: Confirm that the faint line fix holds at all supported DPI settings, not only the default 200 DPI. US1 fixes the root cause; US2 verifies the fix is resolution-independent.

**Independent Test**: Run `uv run pytest tests/integration/test_line_visibility.py::TestMultiResolutionConsistency` — all tested DPI settings (200, 250, 300) must produce contrast-passing output.

### Tests for User Story 2

> **Write this test FIRST and verify it FAILS (or verify it passes with the US1 fix in place) before proceeding.**

- [x] T015 [P] [US2] Add `TestMultiResolutionConsistency` class to `tests/integration/test_line_visibility.py` with `test_line_clarity_consistent_at_all_resolutions()`: renders `lines.pdf` three times using `RenderingOptions(graphics_aa_level=0)` at DPI values 200, 250, and 300; for each render, asserts that sampled stroke pixels achieve ≥ 4.5:1 contrast ratio; asserts no DPI setting produces a lower pass-rate than any other (consistency check)

### Implementation for User Story 2

- [x] T016 [US2] Verify `_calculate_required_dpi()` probe renders in `src/pdf_png_converter/services/pdf_renderer.py` inherit the AA level set by `_apply_rendering_options()` (called before the probe loop) — confirm by reading the call order in the method; no code change expected if T011 is implemented correctly; document finding in a comment if needed

**Checkpoint**: Run `uv run pytest tests/integration/test_line_visibility.py` — all tests including multi-resolution pass. User Stories 1 and 2 are both independently verified.

---

## Phase 5: Polish & Cross-Cutting Concerns

**Purpose**: Full regression verification and housekeeping.

- [x] T017 Run full test suite via `uv run pytest` and confirm all previously passing tests continue to pass with no new failures (SC-005 regression requirement)
- [x] T018 [P] Update `specs/001-fix-faint-lines/checklists/requirements.md` to reflect implementation complete and all acceptance criteria verified

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately
- **Foundational (Phase 2)**: Depends on Phase 1 (T001 for fixture path awareness); BLOCKS all user story work
- **User Story 1 (Phase 3)**: Depends on Phase 2 completion — tests and implementation can then start in parallel
- **User Story 2 (Phase 4)**: Depends on Phase 3 completion (uses the same integration test file and `RenderingOptions`)
- **Polish (Phase 5)**: Depends on both Phase 3 and Phase 4

### User Story Dependencies

- **US1 (P1)**: Starts after Phase 2 — no dependency on US2
- **US2 (P2)**: Starts after US1 — adds tests to the same integration file created in US1

### Within Phase 3 (US1)

- T005–T008 (tests): all [P], can run in parallel — write tests first, confirm they FAIL
- T009–T010 (ConfigLoader): sequential — both modify `config_loader.py`
- T011 (PdfRenderer): depends on T002 (RenderingOptions) being importable
- T012 (config.toml): independent, can run in parallel with T009–T011
- T013–T014 (integration tests): sequential — both write to `test_line_visibility.py`
- Implementation depends on test tasks preceding them

### Parallel Opportunities

- T003 and T004 can run in parallel (different files, both depend only on T002)
- T005, T006, T007, T008 can all run in parallel (different test files)
- T012 can run in parallel with T009–T011 (different file: `config.toml`)
- T015 can run in parallel with T016 (test vs. code review task)
- T017 and T018 can run in parallel

---

## Parallel Example: User Story 1 Tests

```bash
# Launch all test tasks for US1 together (write and verify they FAIL):
Task: "Write tests/unit/models/test_rendering_options.py"           # T005
Task: "Extend tests/unit/config/test_conversion_config.py"         # T006
Task: "Extend tests/unit/config/test_config_loader.py"             # T007
Task: "Extend tests/unit/services/test_pdf_renderer.py"            # T008

# After tests are failing, launch implementation in order:
Task: "Extend config_loader.py — defaults + _validated_aa_level()" # T009 → T010
Task: "Fix pdf_renderer.py — _apply_rendering_options()"           # T011
Task: "Update config.toml"                                          # T012 [P with T009-T011]
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Create `lines.pdf` fixture (T001)
2. Complete Phase 2: `RenderingOptions` model + `ConversionConfig` field (T002–T004)
3. Write failing tests for US1 (T005–T008)
4. Implement US1 fix (T009–T014)
5. **STOP and VALIDATE**: `uv run pytest tests/unit/ tests/integration/test_line_visibility.py`
6. Confirm lines in exported PNGs are now clearly visible

### Incremental Delivery

1. Setup + Foundational (T001–T004) → Models and config ready
2. US1 Tests fail (T005–T008) → Red
3. US1 Implementation (T009–T014) → Green; MVP delivered
4. US2 Test (T015–T016) → Confirms fix is resolution-independent
5. Polish (T017–T018) → Full regression verified; done

---

## Notes

- [P] tasks = different files, no conflicting dependencies — safe to run concurrently
- Story labels [US1]/[US2] map directly to user stories in `spec.md`
- Test tasks MUST be written and confirmed FAILING before their implementation tasks
- T016 (US2 implementation) is likely a no-op verification task — if `_apply_rendering_options()` is called before the probe loop in T011, US2 is automatically satisfied
- Commit after each phase checkpoint to preserve working state
- `uv run pytest` is the canonical test command per `CLAUDE.md`
