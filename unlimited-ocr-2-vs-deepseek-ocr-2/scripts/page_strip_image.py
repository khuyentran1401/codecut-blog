"""Place several full pages side by side with labels: page_strip_image.py PDF FIRST LAST OUT "label1|label2|..."."""
import io, sys
import pymupdf
from PIL import Image, ImageDraw, ImageFont

pdf, first, last, out = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), sys.argv[4]
labels = sys.argv[5].split("|")
doc = pymupdf.open(pdf)
pages = [Image.open(io.BytesIO(doc[n - 1].get_pixmap(dpi=70).tobytes("png"))) for n in range(first, last + 1)]
font = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial Bold.ttf", 16)
gap, top = 30, 34
w = sum(p.width for p in pages) + gap * (len(pages) - 1)
canvas = Image.new("RGB", (w, pages[0].height + top), "white")
draw = ImageDraw.Draw(canvas)
x = 0
for i, (page, label) in enumerate(zip(pages, labels)):
    canvas.paste(page, (x, top))
    draw.rectangle([x, top, x + page.width - 1, top + page.height - 1], outline="#999999")
    tw = draw.textlength(label, font=font)
    draw.text((x + (page.width - tw) / 2, 8), label, fill="black", font=font)
    x += page.width
    if i < len(pages) - 1:
        mid = x + gap // 2
        for y in range(top, canvas.height, 14):
            draw.line([(mid, y), (mid, y + 8)], fill="black", width=2)
        x += gap
canvas.save(out)
print(out, canvas.size)
