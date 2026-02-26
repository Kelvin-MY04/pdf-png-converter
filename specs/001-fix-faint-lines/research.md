# Research: Fix Faint Lines in Exported PNG Images

**Branch**: `001-fix-faint-lines` | **Date**: 2026-02-26

---

## Decision 1: Root Cause of Faint Lines

**Decision**: The faint line defect is caused by PyMuPDF's default anti-aliasing (AA) level of 8 (maximum) during rasterisation.

**Rationale**:
PyMuPDF uses MuPDF's rendering engine, which applies anti-aliasing to all vector graphics by default. AA blends stroke pixels with adjacent background pixels to produce smooth-looking curves and diagonal lines. For thin vector strokes common in AutoCAD exports (0.1–0.35 mm lines that rasterise to 1–3 pixels at 200 DPI), this blending produces semi-opaque grey pixels rather than fully opaque black strokes. The result is visually faint lines that fail the 4.5:1 contrast ratio requirement.

The defect appears at all resolution settings because AA is applied proportionally to the rendered pixel grid regardless of DPI — a 0.5-pixel-wide line is anti-aliased at 200 DPI and 400 DPI alike.

**Evidence**:
- `PdfRenderer.render_page()` calls `page.get_pixmap(dpi=dpi_used)` with no rendering configuration
- `get_pixmap()` uses PyMuPDF defaults: AA level 8 for both graphics and text
- At AA level 8, a 1-pixel-wide black line on a white background renders as a spread of pixels with luminance values from pure black to near-white (e.g., RGB 180, 180, 180 at the edge), reducing contrast below the 4.5:1 threshold

**Alternatives considered**:
- **Alpha channel compositing error**: `get_pixmap()` defaults to `alpha=False`, so no alpha channel is present — not the cause
- **Colorspace mismatch**: Default colorspace is `csRGB`, matching PNG output — not the cause
- **DPI too low**: The DPI auto-raise mechanism correctly handles minimum pixel dimensions; the problem is quality of rendering at any DPI, not resolution

---

## Decision 2: Fix — Disable Graphics Anti-Aliasing, Preserve Text Anti-Aliasing

**Decision**: Call `pymupdf.TOOLS.set_graphics_aa_level(0)` before each `get_pixmap()` call to disable anti-aliasing for vector graphics (lines, curves, paths) while retaining AA for text via `pymupdf.TOOLS.set_text_aa_level(8)`.

**Rationale**:
- PyMuPDF ≥ 1.18.0 (and the required ≥ 1.25.0) exposes two independent AA controls:
  - `pymupdf.TOOLS.set_graphics_aa_level(n)` — affects vector strokes and fills; range 0–8
  - `pymupdf.TOOLS.set_text_aa_level(n)` — affects text glyph rendering; range 0–8
- Setting graphics AA to 0 forces all stroke pixels to be fully opaque with hard edges — directly satisfies FR-007 and SC-002
- Keeping text AA at level 8 preserves the smooth rendering of dimension text and annotation labels — satisfies FR-006 ("fix MUST NOT alter rendering of text, filled shapes, or images")
- Raster images embedded in the PDF are not affected by AA level settings (images are composited as-is)
- The fix is applied immediately before each `get_pixmap()` call and does not require changes to the DPI auto-raise logic

**AA level semantics**:
| Level | Effect |
|-------|--------|
| 0     | No anti-aliasing — fully opaque pixel-exact strokes |
| 1–3   | Minimal smoothing |
| 4–6   | Moderate smoothing |
| 7–8   | Maximum smoothing (PyMuPDF default) |

**Alternatives considered**:
- **`pymupdf.TOOLS.set_aa_level(0)`** (combined setting): Sets both graphics and text AA to 0, which would make text jaggy. Rejected because FR-006 prohibits altering text rendering.
- **Supersampling** (render at 2× DPI, downscale to target): Produces smooth anti-aliased result — opposite of what's needed. Also adds significant memory and time overhead. Rejected.
- **Post-processing contrast enhancement** (increase contrast of rendered PNG): Fragile; does not work for coloured lines. Rejected.
- **`page.get_pixmap(matrix=pymupdf.Matrix(scale, 0, 0, scale, 0, 0))`**: Matrix scaling is equivalent to DPI scaling; does not control AA. Rejected.

---

## Decision 3: Thread Safety and Global State

**Decision**: Global PyMuPDF AA state is acceptable for this single-threaded CLI tool; no additional synchronisation is needed.

**Rationale**:
`pymupdf.TOOLS.set_graphics_aa_level()` modifies MuPDF's global rendering context. This is safe in the current architecture because:
- `ConversionOrchestrator.execute()` processes jobs sequentially in a single thread
- No parallelism is introduced in this fix
- The AA level is set before every `get_pixmap()` call, so even if state were contaminated (e.g., by a future parallel change), each render call would reset it correctly

If future work introduces threading or multiprocessing, this decision should be revisited. At that point, per-context AA configuration or a rendering lock should be evaluated.

---

## Decision 4: New `RenderingOptions` Value Object

**Decision**: Introduce a `RenderingOptions` frozen dataclass in `models/` to carry graphics and text AA level settings, and embed it in `ConversionConfig`.

**Rationale**:
- Follows the established pattern in this codebase: all configuration is typed, immutable, and carried in value objects
- Satisfies OCP: `ConversionConfig` gains `rendering_options` field without modifying existing fields
- `RenderingOptions` is independently testable and independently versioned in `config.toml`
- Decouples `PdfRenderer` from the specific PyMuPDF `TOOLS` API — `PdfRenderer` reads `config.rendering_options.graphics_aa_level`, not `pymupdf.TOOLS` directly in configuration logic

**Alternatives considered**:
- **Add `graphics_aa_level` directly to `ConversionConfig`**: Works for now but mixes rendering quality settings with dimensional/path settings, reducing cohesion. Rejected.
- **Pass AA level as a parameter to `render_page()`**: Breaks the existing `render_page()` signature and all callers. Rejected in favour of using the existing `config` parameter.

---

## Decision 5: TOML Configuration Surface

**Decision**: Add a `[conversion.rendering]` section to `config.toml` with explicit `graphics_aa_level` and `text_aa_level` keys; defaults are `0` and `8` respectively.

**Rationale**:
- Exposes the fix as a user-visible, documented setting so advanced users can adjust AA levels if needed
- Follows the existing pattern of all conversion parameters being present in `config.toml`
- Defaults of `graphics_aa_level = 0` and `text_aa_level = 8` implement the correct behaviour out-of-the-box with no user action required

---

## Decision 6: Pixel Contrast Test Fixture

**Decision**: Create a programmatic PDF test fixture containing a black vector line on a white background using PyMuPDF's drawing API, stored at `tests/fixtures/pdfs/lines.pdf`.

**Rationale**:
- The existing fixtures (`single_page.pdf`, `multi_page.pdf`) are not guaranteed to contain thin vector strokes suitable for contrast measurement
- A programmatic fixture is deterministic: line position, width, and colour are known exactly, enabling precise pixel-coordinate contrast assertions
- The fixture is small (< 5 KB) and generated once via `tests/fixtures/create_fixtures.py`; it can be committed to the repository like the existing fixtures

**Fixture contents**:
- Page size: A4 (595×842 pt)
- Line 1: black (`(0,0,0)`), width 0.5 pt, horizontal across page centre — represents a thin dimension line
- Line 2: black (`(0,0,0)`), width 1.0 pt, horizontal — represents a standard wall line
- White background (default page background in PyMuPDF)
