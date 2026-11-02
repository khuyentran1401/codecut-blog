"""Score how many table page breaks Unlimited-OCR-2 labeled as continuations.

A page counts as a table break when its top 30% reads "Table X—continued".
For each break inside a run's window, the page's first table block should be
labeled append_table.

Usage: score_merges.py PDF RAW_OUTPUT:FIRST-LAST ...
"""
import re
import sys

import pymupdf

CONTINUED = re.compile(r"Table [A-Z]?\.?\d+[A-Z]?(?:\.\d+)?\s*[—-]\s*continued")
TABLE_LABEL = re.compile(r"<BLOCK>([a-z_]*table)")


def continued_table_pages(pdf_path):
    doc = pymupdf.open(pdf_path)
    pages = {}
    for index, page in enumerate(doc):
        top = " ".join(b[4] for b in page.get_text("blocks") if b[1] < page.rect.height * 0.3)
        match = CONTINUED.search(top)
        if match:
            pages[index + 1] = " ".join(match.group().split())
    return pages


def first_table_labels(raw_path, first_page):
    raw = open(raw_path).read()
    pages = raw[raw.index("<PAGE>"):].split("<PAGE>")[1:]
    labels = {}
    for offset, page in enumerate(pages):
        found = TABLE_LABEL.findall(page)
        labels[first_page + offset] = found[0] if found else "no table"
    return labels


pdf_path, *runs = sys.argv[1:]
breaks = continued_table_pages(pdf_path)
for run in runs:
    raw_path, page_range = run.rsplit(":", 1)
    first, last = map(int, page_range.split("-"))
    labels = first_table_labels(raw_path, first)
    inside = [p for p in breaks if first < p <= last]
    merged = sum(labels.get(p) == "append_table" for p in inside)
    print(f"{raw_path} (pages {first}-{last}): {merged}/{len(inside)} breaks labeled append_table")
    for page in inside:
        print(f"    p{page} {breaks[page]:24s} {labels.get(page, 'missing page')}")
