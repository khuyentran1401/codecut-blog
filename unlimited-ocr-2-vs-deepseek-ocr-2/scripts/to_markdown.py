"""Turn a case folder's raw outputs into Markdown.

unlimited-raw.txt     -> unlimited.md   (Baidu's converter)
deepseek-raw-p*.txt   -> deepseek.md    (location tags stripped, pages joined in order)
"""
import re
import sys
from pathlib import Path

from process_unlimitedOCR2 import convert

DEEPSEEK_TAGS = re.compile(r"<\|ref\|>.*?<\|/ref\|><\|det\|>.*?<\|/det\|>\n?")


def unlimited_text(path):
    raw = path.read_text()
    return raw[raw.index("<PAGE>"):]


def deepseek_page(path):
    raw = path.read_text()
    raw = raw[raw.index("<|ref|>"):]
    return f"<!-- {path.stem.removeprefix('deepseek-raw-')} -->\n\n" + DEEPSEEK_TAGS.sub("", raw).strip()


case_dir = Path(sys.argv[1])
(case_dir / "unlimited.md").write_text(convert(unlimited_text(case_dir / "unlimited-raw.txt")))
pages = sorted(case_dir.glob("deepseek-raw-p*.txt"))
(case_dir / "deepseek.md").write_text("\n\n".join(deepseek_page(p) for p in pages) + "\n")
