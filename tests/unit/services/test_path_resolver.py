"""Unit tests for PathResolver."""

from pathlib import Path
import pytest

from pdf_png_converter.services.path_resolver import PathResolver


@pytest.fixture
def resolver():
    return PathResolver()


@pytest.fixture
def import_dir(tmp_path):
    return tmp_path / "import"


@pytest.fixture
def export_dir(tmp_path):
    return tmp_path / "export"


class TestPathResolverSinglePage:
    def test_single_page_has_no_page_suffix(self, resolver, import_dir, export_dir):
        source = import_dir / "plan.pdf"
        result = resolver.resolve_output_path(source, import_dir, export_dir, 1, 1)
        assert result.name == "plan.png"

    def test_single_page_extension_is_png(self, resolver, import_dir, export_dir):
        source = import_dir / "drawing.pdf"
        result = resolver.resolve_output_path(source, import_dir, export_dir, 1, 1)
        assert result.suffix == ".png"

    def test_single_page_is_under_export_dir(self, resolver, import_dir, export_dir):
        source = import_dir / "plan.pdf"
        result = resolver.resolve_output_path(source, import_dir, export_dir, 1, 1)
        assert str(result).startswith(str(export_dir))


class TestPathResolverMultiPage:
    def test_first_page_of_multi_has_page1_suffix(self, resolver, import_dir, export_dir):
        source = import_dir / "plan.pdf"
        result = resolver.resolve_output_path(source, import_dir, export_dir, 1, 3)
        assert result.name == "plan_page1.png"

    def test_second_page_has_page2_suffix(self, resolver, import_dir, export_dir):
        source = import_dir / "plan.pdf"
        result = resolver.resolve_output_path(source, import_dir, export_dir, 2, 3)
        assert result.name == "plan_page2.png"

    def test_third_page_has_page3_suffix(self, resolver, import_dir, export_dir):
        source = import_dir / "plan.pdf"
        result = resolver.resolve_output_path(source, import_dir, export_dir, 3, 3)
        assert result.name == "plan_page3.png"


class TestPathResolverNestedPaths:
    def test_nested_single_level_preserved(self, resolver, import_dir, export_dir):
        source = import_dir / "project-a" / "plan.pdf"
        result = resolver.resolve_output_path(source, import_dir, export_dir, 1, 1)
        assert result == export_dir / "project-a" / "plan.png"

    def test_nested_two_levels_preserved(self, resolver, import_dir, export_dir):
        source = import_dir / "project-a" / "floor-1" / "plan.pdf"
        result = resolver.resolve_output_path(source, import_dir, export_dir, 1, 1)
        assert result == export_dir / "project-a" / "floor-1" / "plan.png"

    def test_nested_three_levels_preserved(self, resolver, import_dir, export_dir):
        source = import_dir / "a" / "b" / "c" / "plan.pdf"
        result = resolver.resolve_output_path(source, import_dir, export_dir, 1, 1)
        assert result == export_dir / "a" / "b" / "c" / "plan.png"

    def test_path_with_spaces_in_directory(self, resolver, import_dir, export_dir):
        source = import_dir / "project a" / "floor 1" / "plan.pdf"
        result = resolver.resolve_output_path(source, import_dir, export_dir, 1, 1)
        assert result == export_dir / "project a" / "floor 1" / "plan.png"

    def test_root_level_file_no_subdir(self, resolver, import_dir, export_dir):
        source = import_dir / "site.pdf"
        result = resolver.resolve_output_path(source, import_dir, export_dir, 1, 1)
        assert result == export_dir / "site.png"
