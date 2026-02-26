# pdf-png-converter Development Guidelines

Auto-generated from all feature plans. Last updated: 2026-02-25

## Active Technologies
- Filesystem only — PDF input, PNG output (001-fix-faint-lines)

- Python 3.14.3 + `pymupdf>=1.25.0` (PDF rendering), `tomllib` (stdlib, TOML config) (001-pdf-png-converter)

## Project Structure

```text
src/
tests/
```

## Commands

```bash
uv sync                        # Install all dependencies (runtime + dev)
uv run pdf-png-converter       # Run the converter
uv run pytest                  # Run all tests
uv run pytest tests/unit/      # Unit tests only
uv run pytest tests/integration/ # Integration tests only
uv run pytest tests/e2e/       # End-to-end tests only
```

## Code Style

Python 3.14.3: Follow standard conventions

## Recent Changes
- 001-fix-faint-lines: Added Python 3.14.3 + `pymupdf>=1.25.0` (PDF rendering), `tomllib` (stdlib, TOML config)

- 001-pdf-png-converter: Added Python 3.14.3 + `pymupdf>=1.25.0` (PDF rendering), `tomllib` (stdlib, TOML config)

<!-- MANUAL ADDITIONS START -->
<!-- MANUAL ADDITIONS END -->
