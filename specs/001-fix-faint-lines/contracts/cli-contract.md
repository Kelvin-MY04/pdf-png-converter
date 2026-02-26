# CLI Contract: pdf-png-converter

**Branch**: `001-fix-faint-lines` | **Date**: 2026-02-26

## Contract Status: No Breaking Changes

The faint line bug fix is an internal rendering quality change. The CLI interface, config file schema, and output file format are unchanged from the `001-pdf-png-converter` baseline. No existing call sites or user workflows are broken.

---

## CLI Invocation (unchanged)

```
uv run pdf-png-converter
```

No arguments. Reads `config.toml` from the current working directory.

## Exit Codes (unchanged)

| Code | Meaning |
|------|---------|
| 0    | All PDFs converted successfully |
| 1    | One or more PDFs were skipped or errored |

## Config File Additions (non-breaking)

A new optional section `[conversion.rendering]` is added to `config.toml`. It is fully optional — omitting it applies the correct default values (`graphics_aa_level = 0`, `text_aa_level = 8`) automatically.

Existing config files with no `[conversion.rendering]` section continue to work without modification.

## Output Files (unchanged)

PNG files are written to `export_dir` mirroring the `import_dir` directory tree. File naming, format, and metadata are unchanged.
