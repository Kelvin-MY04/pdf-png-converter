"""Lifecycle states for a single PDF conversion job."""

from enum import Enum


class ConversionStatus(Enum):
    """Represents the processing state of one PDF conversion job."""

    PENDING = "pending"
    SUCCESS = "success"
    SKIPPED = "skipped"
    ERROR = "error"
