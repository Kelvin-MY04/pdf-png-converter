# Contract: Configuration File Schema

**Branch**: `001-pdf-png-converter` | **Date**: 2026-02-25

---

## File Location

Default: `config.toml` in the project root directory.
Override: `--config PATH` CLI flag.

---

## Format

TOML (Tom's Obvious Minimal Language). Edit with any text editor.

---

## Full Schema

```toml
# ─────────────────────────────────────────────────
# PDF to PNG Converter — config.toml
# ─────────────────────────────────────────────────

[conversion]
# Target rendering resolution in dots per inch.
# Higher values produce sharper output and larger file sizes.
# Default: 200 — produces ≥3000×2000 px for all standard AutoCAD sheet sizes.
# The converter will automatically raise DPI if the output would fall below
# min_width_px × min_height_px.
dpi = 200                 # integer, positive, required

# Minimum acceptable pixel count on the long dimension of the output PNG.
min_width_px = 3000       # integer, positive, required

# Minimum acceptable pixel count on the short dimension of the output PNG.
min_height_px = 2000      # integer, positive, required

[paths]
# Directory to scan for PDF files. Subdirectories are scanned recursively.
# Accepts relative paths (resolved from the working directory) or absolute paths.
import_dir = "import"     # string, must be a valid directory path

# Directory to write PNG files. Created automatically if it does not exist.
# The directory tree under import_dir is mirrored exactly under export_dir.
export_dir = "export"     # string, must be a valid directory path
```

---

## Field Reference

### `[conversion]` section

| Key | Type | Required | Default | Constraints |
|---|---|---|---|---|
| `dpi` | integer | No | `200` | Must be > 0. Converter auto-raises if output falls below minimum pixel dimensions. |
| `min_width_px` | integer | No | `3000` | Must be > 0. Long-side pixel floor. |
| `min_height_px` | integer | No | `2000` | Must be > 0. Short-side pixel floor. |

### `[paths]` section

| Key | Type | Required | Default | Constraints |
|---|---|---|---|---|
| `import_dir` | string | No | `"import"` | Relative or absolute path. Does not need to exist when the config file is loaded. |
| `export_dir` | string | No | `"export"` | Relative or absolute path. Created automatically if absent. |

---

## Partial Config

Any section or key may be omitted. Omitted values fall back to the built-in defaults listed above. Example minimal config:

```toml
[conversion]
dpi = 300
```

---

## Error Handling

| Condition | Behaviour |
|---|---|
| Config file not found | Warning to stderr; all built-in defaults used; processing continues |
| Config file is not valid TOML | Warning to stderr with parse error detail; all built-in defaults used; processing continues |
| `dpi` value is ≤ 0 | Warning to stderr; built-in default (`200`) used |
| `min_width_px` or `min_height_px` ≤ 0 | Warning to stderr; built-in defaults (`3000`, `2000`) used |
| Unknown keys in config | Silently ignored (forward-compatible) |

---

## Example: High-Resolution Archival Run

```toml
[conversion]
dpi = 300
min_width_px = 6000
min_height_px = 4000

[paths]
import_dir = "/mnt/nas/autocad-exports/2026-Q1"
export_dir = "/mnt/nas/pngs/2026-Q1"
```

## Example: Screen Preview Run

```toml
[conversion]
dpi = 150

[paths]
import_dir = "import"
export_dir = "export/preview"
```
