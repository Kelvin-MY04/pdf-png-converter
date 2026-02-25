"""Unit tests for DirectoryBuilder."""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from pdf_png_converter.services.directory_builder import DirectoryBuilder


@pytest.fixture
def builder():
    return DirectoryBuilder()


class TestDirectoryBuilderCreation:
    def test_creates_missing_directory(self, builder, tmp_path):
        target = tmp_path / "new_dir"
        assert not target.exists()
        builder.ensure_directory_exists(target)
        assert target.exists()

    def test_creates_nested_missing_directories(self, builder, tmp_path):
        target = tmp_path / "a" / "b" / "c"
        assert not target.exists()
        builder.ensure_directory_exists(target)
        assert target.exists()
        assert target.is_dir()

    def test_no_op_if_directory_already_exists(self, builder, tmp_path):
        target = tmp_path / "existing"
        target.mkdir()
        # Should not raise
        builder.ensure_directory_exists(target)
        assert target.exists()

    def test_idempotent_when_called_twice(self, builder, tmp_path):
        target = tmp_path / "idempotent"
        builder.ensure_directory_exists(target)
        builder.ensure_directory_exists(target)  # second call must not raise
        assert target.exists()


class TestDirectoryBuilderPermissionError:
    def test_propagates_permission_error(self, builder, tmp_path):
        target = tmp_path / "restricted"
        with patch.object(Path, "mkdir", side_effect=PermissionError("Access denied")):
            with pytest.raises(PermissionError):
                builder.ensure_directory_exists(target)
