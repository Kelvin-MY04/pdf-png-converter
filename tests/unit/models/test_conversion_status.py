"""Unit tests for ConversionStatus enum."""

import pytest
from pdf_png_converter.models.conversion_status import ConversionStatus


class TestConversionStatus:
    def test_all_four_values_exist(self):
        assert ConversionStatus.PENDING
        assert ConversionStatus.SUCCESS
        assert ConversionStatus.SKIPPED
        assert ConversionStatus.ERROR

    def test_pending_string_value(self):
        assert ConversionStatus.PENDING.value == "pending"

    def test_success_string_value(self):
        assert ConversionStatus.SUCCESS.value == "success"

    def test_skipped_string_value(self):
        assert ConversionStatus.SKIPPED.value == "skipped"

    def test_error_string_value(self):
        assert ConversionStatus.ERROR.value == "error"

    def test_enum_membership(self):
        statuses = list(ConversionStatus)
        assert len(statuses) == 4

    def test_string_lookup(self):
        assert ConversionStatus("pending") == ConversionStatus.PENDING
        assert ConversionStatus("success") == ConversionStatus.SUCCESS
        assert ConversionStatus("skipped") == ConversionStatus.SKIPPED
        assert ConversionStatus("error") == ConversionStatus.ERROR
