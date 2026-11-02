"""Screenshots for the article: the bottom of page N stacked on the top of page N+1 with a
labeled page-break line. Usage: page_break_image.py PDF PAGE TOP_SLICE BOTTOM_SLICE OUT"""
import io, sys
import pymupdf
from PIL import Image, ImageDraw, ImageFont

pdf, page, top_frac, bottom_frac, out = sys.argv[1], int(sys.argv[2]), sys.argv[3], sys.argv[4], sys.argv[5]
doc = pymupdf.open(pdf)

def crop(n, y0, y1):
    p = doc[n - 1]
    r = p.rect
    clip = pymupdf.Rect(r.x0 + r.width * 0.1, r.height * y0, r.x1 - r.width * 0.1, r.height * y1)
    return Image.open(io.BytesIO(p.get_pixmap(dpi=130, clip=clip).tobytes("png")))

a0, a1 = map(float, top_frac.split("-"))     # slice of page N
b0, b1 = map(float, bottom_frac.split("-"))  # slice of page N+1
first, second = crop(page, a0, a1), crop(page + 1, b0, b1)

gap = 44
w = max(first.width, second.width)
canvas = Image.new("RGB", (w, first.height + gap + second.height), "white")
canvas.paste(first, (0, 0))
canvas.paste(second, (0, first.height + gap))
draw = ImageDraw.Draw(canvas)
y = first.height + gap // 2
for x in range(0, w, 18):
    draw.line([(x, y), (x + 10, y)], fill="black", width=3)
font = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial Bold.ttf", 18)
label = f" page {page} ends | page {page + 1} starts "
tw = draw.textlength(label, font=font)
draw.rectangle([(w - tw) / 2 - 4, y - 13, (w + tw) / 2 + 4, y + 13], fill="white")
draw.text(((w - tw) / 2, y - 11), label, fill="black", font=font)
canvas.save(out)
print(out, canvas.size)
