"""
Generate test fixture PDFs for the pdf-png-converter test suite.

Run directly with: uv run python tests/fixtures/create_fixtures.py
"""

from pathlib import Path

import pymupdf


FIXTURES_DIR = Path(__file__).parent / "pdfs"


def create_single_page_pdf(output_path: Path) -> None:
    """Create a valid single-page A3 PDF simulating a floor plan."""
    doc = pymupdf.open()
    # A3 page in points (420mm x 297mm at 72 pt/in = 1190.55 x 841.89)
    page = doc.new_page(width=1190, height=842)

    # Draw a simple floor plan outline
    rect = pymupdf.Rect(50, 50, 1140, 792)
    page.draw_rect(rect, color=(0, 0, 0), width=2)

    # Inner rooms
    page.draw_line(pymupdf.Point(400, 50), pymupdf.Point(400, 792), color=(0, 0, 0), width=1)
    page.draw_line(pymupdf.Point(50, 400), pymupdf.Point(1140, 400), color=(0, 0, 0), width=1)
    page.draw_line(pymupdf.Point(700, 400), pymupdf.Point(700, 792), color=(0, 0, 0), width=1)

    # Title block
    page.insert_text(
        pymupdf.Point(60, 80),
        "FLOOR PLAN — LEVEL 1",
        fontsize=16,
        color=(0, 0, 0),
    )
    page.insert_text(
        pymupdf.Point(60, 100),
        "AutoCAD 2023 Export — Test Fixture",
        fontsize=10,
        color=(0.3, 0.3, 0.3),
    )

    # Room labels
    page.insert_text(pymupdf.Point(100, 200), "LIVING ROOM", fontsize=12)
    page.insert_text(pymupdf.Point(450, 200), "BEDROOM 1", fontsize=12)
    page.insert_text(pymupdf.Point(100, 550), "KITCHEN", fontsize=12)
    page.insert_text(pymupdf.Point(450, 550), "BATHROOM", fontsize=12)
    page.insert_text(pymupdf.Point(750, 550), "BEDROOM 2", fontsize=12)

    # Dimension lines
    for x in range(100, 1100, 100):
        page.draw_line(
            pymupdf.Point(x, 820), pymupdf.Point(x + 90, 820),
            color=(0.5, 0.5, 0.5), width=0.5,
        )

    doc.save(str(output_path))
    doc.close()


def create_multi_page_pdf(output_path: Path) -> None:
    """Create a valid 3-page PDF simulating multiple floor levels."""
    doc = pymupdf.open()

    for level in range(1, 4):
        page = doc.new_page(width=1190, height=842)
        rect = pymupdf.Rect(50, 50, 1140, 792)
        page.draw_rect(rect, color=(0, 0, 0), width=2)

        # Different layout per level
        if level == 1:
            page.draw_line(pymupdf.Point(400, 50), pymupdf.Point(400, 792), color=(0, 0, 0), width=1)
        elif level == 2:
            page.draw_line(pymupdf.Point(595, 50), pymupdf.Point(595, 792), color=(0, 0, 0), width=1)
        else:
            page.draw_rect(pymupdf.Rect(200, 200, 900, 650), color=(0, 0, 0), width=1)

        page.insert_text(
            pymupdf.Point(60, 80),
            f"FLOOR PLAN — LEVEL {level}",
            fontsize=16,
            color=(0, 0, 0),
        )
        page.insert_text(
            pymupdf.Point(60, 100),
            "AutoCAD 2023 Export — Multi-Page Test Fixture",
            fontsize=10,
            color=(0.3, 0.3, 0.3),
        )

    doc.save(str(output_path))
    doc.close()


def create_lines_pdf(output_path: Path) -> None:
    """Create a PDF with known black vector lines for contrast testing.

    Page: A4 (595×842 pt), white background.
    - Thin line:     0.5 pt wide, black, horizontal at y=300 pt
    - Standard line: 1.0 pt wide, black, horizontal at y=350 pt

    Constants exported for test use:
      THIN_LINE_Y_PT = 300
      STANDARD_LINE_Y_PT = 350
      LINE_X_START_PT = 50
      LINE_X_END_PT = 545
    """
    doc = pymupdf.open()
    page = doc.new_page(width=595, height=842)  # A4 in points

    # Thin dimension line (0.5 pt) — representative of AutoCAD dimension strokes
    page.draw_line(
        pymupdf.Point(50, 300), pymupdf.Point(545, 300),
        color=(0, 0, 0),
        width=0.5,
    )

    # Standard wall line (1.0 pt) — representative of AutoCAD wall strokes
    page.draw_line(
        pymupdf.Point(50, 350), pymupdf.Point(545, 350),
        color=(0, 0, 0),
        width=1.0,
    )

    doc.save(str(output_path))
    doc.close()


# Known coordinates for test assertions
THIN_LINE_Y_PT: int = 300
STANDARD_LINE_Y_PT: int = 350
LINE_X_START_PT: int = 50
LINE_X_END_PT: int = 545


def create_corrupted_pdf(output_path: Path) -> None:
    """Create a file with random non-PDF bytes that PyMuPDF cannot open."""
    corrupted_bytes = (
        b"\x00\x01\x02\x03NOTAPDF\xff\xfe\xfd"
        b"This is not a valid PDF file.\n"
        b"\x80\x81\x82\x83\x84\x85\x86\x87\x88\x89"
    )
    output_path.write_bytes(corrupted_bytes)


def main() -> None:
    FIXTURES_DIR.mkdir(parents=True, exist_ok=True)

    print(f"Creating fixtures in {FIXTURES_DIR}")

    single = FIXTURES_DIR / "single_page.pdf"
    create_single_page_pdf(single)
    print(f"  Created: {single.name}")

    multi = FIXTURES_DIR / "multi_page.pdf"
    create_multi_page_pdf(multi)
    print(f"  Created: {multi.name}")

    corrupted = FIXTURES_DIR / "corrupted.pdf"
    create_corrupted_pdf(corrupted)
    print(f"  Created: {corrupted.name}")

    lines = FIXTURES_DIR / "lines.pdf"
    create_lines_pdf(lines)
    print(f"  Created: {lines.name}")

    print("Done.")


if __name__ == "__main__":
    main()
