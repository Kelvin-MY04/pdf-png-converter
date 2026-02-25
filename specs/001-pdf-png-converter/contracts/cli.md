# Contract: CLI Interface

**Branch**: `001-pdf-png-converter` | **Date**: 2026-02-25

---

## Invocation

```
pdf-png-converter [OPTIONS]
```

Or directly via uv:

```
uv run pdf-png-converter [OPTIONS]
```

---

## Options

| Option | Short | Type | Default | Description |
|---|---|---|---|---|
| `--config PATH` | `-c` | path | `config.toml` | Path to TOML configuration file |
| `--import-dir PATH` | `-i` | path | from config | Override import directory |
| `--export-dir PATH` | `-e` | path | from config | Override export directory |
| `--dpi INT` | `-d` | integer | from config | Override rendering DPI |
| `--help` | `-h` | flag | — | Print usage and exit |
| `--version` | `-V` | flag | — | Print version string and exit |

**Precedence**: CLI flags > config file values > built-in defaults

---

## Standard Output (stdout)

Progress is written to stdout one line per converted page:

```
[OK]   export/project-a/floor-1/plan.png  (3508x4961 px, 300 DPI)
[OK]   export/project-b/reception.png     (4678x6622 px, 200 DPI)
[SKIP] import/corrupted.pdf               (unreadable PDF: invalid cross-reference table)
[OK]   export/building-c/roof_page1.png   (4678x6622 px, 200 DPI)
[OK]   export/building-c/roof_page2.png   (4678x6622 px, 200 DPI)
```

**Summary block** (always printed at end, even if zero files processed):

```
──────────────────────────────────────────
Conversion complete.
  Succeeded : 4 file(s) → 5 page(s)
  Skipped   : 1 file(s)
  Errors    : 0 file(s)
──────────────────────────────────────────
```

---

## Standard Error (stderr)

Warnings and non-fatal errors are written to stderr:

```
WARNING: Config file not found at config.toml — using built-in defaults.
WARNING: Configured DPI (150) too low for A3 page — raised to 183 DPI to meet 3000×2000 minimum.
ERROR:   Failed to write export/floor-2/plan.png — [Errno 28] No space left on device.
```

---

## Exit Codes

| Code | Meaning |
|---|---|
| `0` | All discovered PDF files processed (including partial batches with some skipped/errored) |
| `1` | Fatal startup error: import directory not found, config file malformed and unrecoverable, or missing required arguments |
| `2` | All files in the batch were skipped or errored (zero successful conversions) |

---

## Behaviour Contracts

- **Idempotent**: Running the converter twice on the same input produces identical output files (existing PNGs are overwritten without prompting)
- **Non-destructive on source**: The converter never modifies or deletes files in `import_dir`
- **Atomic per page**: Each PNG is written completely before the next page begins; no partial PNG files are left on disk (incomplete writes are deleted on error)
- **Isolation**: A failure on one PDF file does not prevent processing of subsequent files
- **Empty input**: If `import_dir` contains no PDF files, the converter prints an informational message, exits with code `0`, and writes nothing to `export_dir`
