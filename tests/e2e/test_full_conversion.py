"""End-to-end tests: full CLI pipeline with real PDF fixtures."""

import shutil
import struct
import subprocess
import sys
from pathlib import Path

import pytest


def read_png_dimensions(png_path: Path) -> tuple[int, int]:
    """Read actual pixel dimensions from a PNG file's IHDR chunk."""
    with png_path.open("rb") as f:
        f.read(8)   # PNG signature
        f.read(4)   # chunk length
        f.read(4)   # "IHDR"
        width = struct.unpack(">I", f.read(4))[0]
        height = struct.unpack(">I", f.read(4))[0]
    return width, height


FIXTURES_DIR = Path(__file__).parent.parent / "fixtures" / "pdfs"


def run_cli(import_dir: Path, export_dir: Path, extra_args: list[str] | None = None) -> subprocess.CompletedProcess:
    """Run the pdf-png-converter CLI and return the completed process."""
    cmd = [
        sys.executable, "-m", "pdf_png_converter.cli.main",
        "--import-dir", str(import_dir),
        "--export-dir", str(export_dir),
    ]
    if extra_args:
        cmd.extend(extra_args)
    return subprocess.run(cmd, capture_output=True, text=True)


class TestE2ESinglePageConversion:
    def test_single_page_pdf_converts_to_png(self, tmp_import_dir, tmp_export_dir):
        shutil.copy(FIXTURES_DIR / "single_page.pdf", tmp_import_dir / "plan.pdf")
        result = run_cli(tmp_import_dir, tmp_export_dir)
        assert result.returncode == 0
        assert (tmp_export_dir / "plan.png").exists()

    def test_output_png_meets_minimum_resolution(self, tmp_import_dir, tmp_export_dir):
        shutil.copy(FIXTURES_DIR / "single_page.pdf", tmp_import_dir / "plan.pdf")
        run_cli(tmp_import_dir, tmp_export_dir)
        png_path = tmp_export_dir / "plan.png"
        width, height = read_png_dimensions(png_path)
        long_side = max(width, height)
        short_side = min(width, height)
        assert long_side >= 3000
        assert short_side >= 2000

    def test_exit_code_zero_on_success(self, tmp_import_dir, tmp_export_dir):
        shutil.copy(FIXTURES_DIR / "single_page.pdf", tmp_import_dir / "plan.pdf")
        result = run_cli(tmp_import_dir, tmp_export_dir)
        assert result.returncode == 0

    def test_empty_import_exits_zero(self, tmp_import_dir, tmp_export_dir):
        result = run_cli(tmp_import_dir, tmp_export_dir)
        assert result.returncode == 0


class TestE2EMultiPageConversion:
    def test_multi_page_pdf_creates_3_pngs(self, tmp_import_dir, tmp_export_dir):
        shutil.copy(FIXTURES_DIR / "multi_page.pdf", tmp_import_dir / "levels.pdf")
        run_cli(tmp_import_dir, tmp_export_dir)
        assert (tmp_export_dir / "levels_page1.png").exists()
        assert (tmp_export_dir / "levels_page2.png").exists()
        assert (tmp_export_dir / "levels_page3.png").exists()

    def test_multi_page_output_files_are_valid_images(self, tmp_import_dir, tmp_export_dir):
        shutil.copy(FIXTURES_DIR / "multi_page.pdf", tmp_import_dir / "levels.pdf")
        run_cli(tmp_import_dir, tmp_export_dir)
        for page_num in range(1, 4):
            png = tmp_export_dir / f"levels_page{page_num}.png"
            assert png.stat().st_size > 1000  # non-trivial file size


class TestE2EFolderStructureMirroring:
    def test_nested_directory_structure_mirrored(self, tmp_import_dir, tmp_export_dir):
        (tmp_import_dir / "project-a" / "floor-1").mkdir(parents=True)
        (tmp_import_dir / "project-b").mkdir()
        shutil.copy(FIXTURES_DIR / "single_page.pdf", tmp_import_dir / "project-a" / "floor-1" / "plan.pdf")
        shutil.copy(FIXTURES_DIR / "single_page.pdf", tmp_import_dir / "project-b" / "site.pdf")

        run_cli(tmp_import_dir, tmp_export_dir)

        assert (tmp_export_dir / "project-a" / "floor-1" / "plan.png").exists()
        assert (tmp_export_dir / "project-b" / "site.png").exists()

    def test_three_level_nesting_mirrored(self, tmp_import_dir, tmp_export_dir):
        deep = tmp_import_dir / "a" / "b" / "c"
        deep.mkdir(parents=True)
        shutil.copy(FIXTURES_DIR / "single_page.pdf", deep / "drawing.pdf")

        run_cli(tmp_import_dir, tmp_export_dir)
        assert (tmp_export_dir / "a" / "b" / "c" / "drawing.png").exists()

    def test_png_count_equals_pdf_count(self, tmp_import_dir, tmp_export_dir):
        (tmp_import_dir / "sub").mkdir()
        shutil.copy(FIXTURES_DIR / "single_page.pdf", tmp_import_dir / "plan1.pdf")
        shutil.copy(FIXTURES_DIR / "single_page.pdf", tmp_import_dir / "sub" / "plan2.pdf")

        run_cli(tmp_import_dir, tmp_export_dir)
        pngs = list(tmp_export_dir.rglob("*.png"))
        assert len(pngs) == 2


class TestE2EConfigAndCorruption:
    def test_corrupted_pdf_skipped_valid_converted(self, tmp_import_dir, tmp_export_dir):
        shutil.copy(FIXTURES_DIR / "single_page.pdf", tmp_import_dir / "valid.pdf")
        shutil.copy(FIXTURES_DIR / "corrupted.pdf", tmp_import_dir / "corrupted.pdf")

        result = run_cli(tmp_import_dir, tmp_export_dir)
        assert result.returncode == 0
        assert (tmp_export_dir / "valid.png").exists()
        assert not (tmp_export_dir / "corrupted.png").exists()

    def test_dpi_override_produces_larger_output(self, tmp_import_dir, tmp_export_dir):
        shutil.copy(FIXTURES_DIR / "single_page.pdf", tmp_import_dir / "plan.pdf")

        export_200 = tmp_export_dir / "dpi200"
        export_300 = tmp_export_dir / "dpi300"

        run_cli(tmp_import_dir, export_200, ["--dpi", "200"])
        run_cli(tmp_import_dir, export_300, ["--dpi", "300"])

        w200, h200 = read_png_dimensions(export_200 / "plan.png")
        w300, h300 = read_png_dimensions(export_300 / "plan.png")
        assert (w300 * h300) > (w200 * h200)

    def test_missing_config_file_uses_defaults(self, tmp_import_dir, tmp_export_dir):
        shutil.copy(FIXTURES_DIR / "single_page.pdf", tmp_import_dir / "plan.pdf")
        result = run_cli(
            tmp_import_dir, tmp_export_dir,
            ["--config", str(tmp_import_dir / "nonexistent.toml")]
        )
        assert result.returncode == 0
        assert (tmp_export_dir / "plan.png").exists()
        # Warning about missing config should appear on stderr
        assert "warning" in result.stderr.lower() or "not found" in result.stderr.lower()
