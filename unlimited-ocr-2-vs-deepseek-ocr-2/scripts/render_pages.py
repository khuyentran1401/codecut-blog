"""Render a page range of a PDF to 150 dpi PNGs: render_pages.py PDF FIRST-LAST OUT_DIR"""
import sys
from pathlib import Path

import pymupdf

pdf_path, page_range, out_dir = sys.argv[1], sys.argv[2], Path(sys.argv[3])
first, last = map(int, page_range.split("-"))
out_dir.mkdir(parents=True, exist_ok=True)
doc = pymupdf.open(pdf_path)
for page_number in range(first, last + 1):
    doc[page_number - 1].get_pixmap(dpi=150).save(out_dir / f"p{page_number:03d}.png")
