"""Loads and validates TOML configuration, merging with built-in defaults."""

import logging
import tomllib
from pathlib import Path

from pdf_png_converter.config.conversion_config import ConversionConfig

logger = logging.getLogger(__name__)

_DEFAULTS: dict = {
    "conversion": {
        "dpi": 200,
        "min_width_px": 3000,
        "min_height_px": 2000,
    },
    "paths": {
        "import_dir": "import",
        "export_dir": "export",
    },
}


class ConfigLoader:
    """Reads a TOML config file, merges with defaults, and returns a ConversionConfig."""

    def load(self, config_path: Path) -> ConversionConfig:
        """Load config from path, fall back to defaults on missing or malformed file."""
        raw = self._read_toml(config_path)
        merged = self._merge_with_defaults(raw)
        return self._build_config(merged)

    def _read_toml(self, config_path: Path) -> dict:
        """Read and parse TOML file; return empty dict on any error."""
        try:
            with config_path.open("rb") as fh:
                return tomllib.load(fh)
        except FileNotFoundError:
            logger.warning("Config file not found at %s — using built-in defaults.", config_path)
            return {}
        except tomllib.TOMLDecodeError as exc:
            logger.warning("Malformed config file at %s: %s — using built-in defaults.", config_path, exc)
            return {}

    def _merge_with_defaults(self, user_values: dict) -> dict:
        """Deep-merge user values over built-in defaults."""
        result: dict = {}
        for section, defaults in _DEFAULTS.items():
            user_section = user_values.get(section, {})
            result[section] = {**defaults, **user_section}
        return result

    def _build_config(self, merged: dict) -> ConversionConfig:
        """Validate merged values and construct an immutable ConversionConfig."""
        conversion = merged["conversion"]
        paths = merged["paths"]

        dpi = self._validated_positive_int(conversion["dpi"], "dpi", _DEFAULTS["conversion"]["dpi"])
        min_width_px = self._validated_positive_int(
            conversion["min_width_px"], "min_width_px", _DEFAULTS["conversion"]["min_width_px"]
        )
        min_height_px = self._validated_positive_int(
            conversion["min_height_px"], "min_height_px", _DEFAULTS["conversion"]["min_height_px"]
        )

        return ConversionConfig(
            dpi=dpi,
            min_width_px=min_width_px,
            min_height_px=min_height_px,
            import_dir=Path(paths["import_dir"]),
            export_dir=Path(paths["export_dir"]),
        )

    def _validated_positive_int(self, value: int, field_name: str, default: int) -> int:
        """Return value if positive; warn and return default otherwise."""
        if not isinstance(value, int) or value <= 0:
            logger.warning(
                "Config value '%s' must be a positive integer (got %r) — using default %d.",
                field_name,
                value,
                default,
            )
            return default
        return value
