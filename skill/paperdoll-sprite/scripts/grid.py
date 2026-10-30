#!/usr/bin/env python3
"""Crop a reference with a labelled grid in sprite units, so coordinates can be read straight off it.
usage: grid.py ref.png out.png --ref-box X Y SCALE --crop X0 Y0 X1 Y1 [--zoom 20] [--step 1] [--label 2]
Thin lines every --step units, bold + numbered every --label units. Optional --pts "x,y x,y ..." draws
numbered markers (use to check traced nodes against the art)."""
import sys
from PIL import Image, ImageDraw
a = sys.argv[1:]
def opt(n, k=1, d=None):
    return a[a.index(n) + 1:a.index(n) + 1 + k] if n in a else d
ref, out = a[0], a[1]
bx, by, bs = [float(v) for v in opt('--ref-box', 3)]
x0, y0, x1, y1 = [float(v) for v in opt('--crop', 4)]
z = float(opt('--zoom', 1, ['20'])[0]); st = float(opt('--step', 1, ['1'])[0]); lb = float(opt('--label', 1, ['2'])[0])
im = Image.open(ref).convert('RGB')
W, H = int((x1 - x0) * z), int((y1 - y0) * z)
r = im.resize((int(im.width * bs * z), int(im.height * bs * z)), Image.LANCZOS)
base = Image.new('RGB', (W, H), 'white'); base.paste(r, (int((bx - x0) * z), int((by - y0) * z)))
d = ImageDraw.Draw(base, 'RGBA')
import math
v = math.ceil(x0 / st) * st
while v <= x1:
    bold = abs(v / lb - round(v / lb)) < 1e-6
    px = (v - x0) * z
    d.line([(px, 0), (px, H)], fill=(255, 255, 0, 150 if bold else 45), width=1)
    if bold: d.text((px + 2, 2), '%g' % v, fill=(255, 255, 0, 255))
    v += st
v = math.ceil(y0 / st) * st
while v <= y1:
    bold = abs(v / lb - round(v / lb)) < 1e-6
    py = (v - y0) * z
    d.line([(0, py), (W, py)], fill=(0, 255, 255, 150 if bold else 45), width=1)
    if bold: d.text((2, py + 2), '%g' % v, fill=(0, 255, 255, 255))
    v += st
pts = opt('--pts', 1, [''])[0].split()
for i, p in enumerate(pts):
    x, y = [float(c) for c in p.split(',')]
    px, py = (x - x0) * z, (y - y0) * z
    d.ellipse([px - 3, py - 3, px + 3, py + 3], outline=(255, 0, 0, 255), width=2); d.text((px + 5, py - 5), str(i), fill=(255, 60, 60, 255))
base.save(out); print(out, W, H)
