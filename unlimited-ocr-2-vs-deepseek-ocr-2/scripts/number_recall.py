"""Share of the numbers printed on PDF pages that appear in a model output: number_recall.py PDF FIRST-LAST OUTPUT..."""
import re
import sys
from collections import Counter

import pymupdf

NUM = re.compile(r"[-−–]?\d[\d,]*\.?\d*")
DEEPSEEK_BOX = re.compile(r"<\|det\|>.*?<\|/det\|>")
UNLIMITED_BOX = re.compile(r"\[\d+, \d+, \d+, \d+\]")


def numbers(text):
    text = text.replace("−", "-").replace("–", "-")
    found = (n.replace(",", "") for n in NUM.findall(text))
    return Counter(n for n in found if len(n.lstrip("-")) >= 2)


def page_numbers(pdf, pages):
    doc = pymupdf.open(pdf)
    return sum((numbers(doc[p - 1].get_text()) for p in pages), Counter())


def model_text(path):
    text = open(path).read()
    for marker in ("<PAGE>", "<|ref|>"):
        if marker in text:
            text = text[text.index(marker):]
            break
    return UNLIMITED_BOX.sub(" ", DEEPSEEK_BOX.sub(" ", text))


if __name__ == "__main__":
    pdf, pages, *outputs = sys.argv[1:]
    first, last = map(int, pages.split("-"))
    truth = page_numbers(pdf, range(first, last + 1))
    total = sum(truth.values())
    for out in outputs:
        got = numbers(model_text(out))
        hit = sum((truth & got).values())
        missed = dict(truth - got)
        print(f"{out.rsplit('/', 1)[-1]:24s} {hit}/{total} ({hit / total:.0%})  extra: {sum((got - truth).values())}  missed: {missed if len(missed) < 8 else str(len(missed)) + ' values'}")
