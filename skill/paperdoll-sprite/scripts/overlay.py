#!/usr/bin/env python3
"""Overlay a sprite on its reference to check geometry. usage:
  overlay.py sprite.svg ref.png out.png --ref-box X Y SCALE [--crop X0 Y0 X1 Y1] [--zoom 12] [--opacity 0.55] [--solo A,B] [--outline]
--ref-box: where the reference's top-left lands in sprite units (X,Y) and sprite-units-per-reference-pixel SCALE
(same as the <image x y width/1024> in the working file). The sprite is drawn over the reference at the given
opacity; --outline additionally draws the sprite as 0.15-unit red outlines (fills off) so edges can be read against the art.
Coordinates outside the 64x64 canvas are fine: pick any --crop."""
import os, re, subprocess, sys, tempfile
import xml.etree.ElementTree as ET
from PIL import Image

a = sys.argv[1:]
def opt(n, k=1, d=None):
    return a[a.index(n) + 1:a.index(n) + 1 + k] if n in a else d
src, ref, out = a[0], a[1], a[2]
bx, by, bs = [float(v) for v in opt('--ref-box', 3)]
zoom = float(opt('--zoom', 1, ['12'])[0]); op = float(opt('--opacity', 1, ['0.55'])[0])
IL = '{http://www.inkscape.org/namespaces/inkscape}label'; GM = '{http://www.inkscape.org/namespaces/inkscape}groupmode'
ET.register_namespace('', 'http://www.w3.org/2000/svg')
for p, u in (('inkscape', 'http://www.inkscape.org/namespaces/inkscape'), ('sodipodi', 'http://sodipodi.sourceforge.net/DTD/sodipodi-0.dtd'), ('xlink', 'http://www.w3.org/1999/xlink')):
    ET.register_namespace(p, u)
root = ET.parse(src).getroot()
im = Image.open(ref).convert('RGB')
c = opt('--crop', 4)
if c:
    x0, y0, x1, y1 = [float(v) for v in c]
else:
    x0, y0, x1, y1 = 0, 0, float(root.get('width')), float(root.get('height'))
solo = set((opt('--solo', 1, [''])[0]).split(',')) - {''}
for el in list(root):
    if el.tag.endswith('}image'):
        root.remove(el)
    elif el.get(GM) == 'layer' and solo and el.get(IL) not in solo:
        el.set('style', 'display:none')
for e in root.iter():
    lab = e.get(IL) or ''
    if lab.endswith('-pivot'):
        e.set('style', 'display:none')
    if '--outline' in a and e.tag.split('}')[1] in ('path', 'ellipse', 'circle'):
        st = e.get('style', '')
        if 'display:none' not in st and not lab.endswith('-pivot'):
            e.set('style', 'fill:none;stroke:#ff2020;stroke-width:0.15;opacity:1')
W, H = int((x1 - x0) * zoom), int((y1 - y0) * zoom)
root.set('viewBox', '%g %g %g %g' % (x0, y0, x1 - x0, y1 - y0)); root.set('width', str(W)); root.set('height', str(H))
tmp = tempfile.mkdtemp(); t = os.path.join(tmp, 's.svg'); p = os.path.join(tmp, 's.png')
ET.ElementTree(root).write(t)
subprocess.run(['rsvg-convert', t, '-o', p], check=True)
sp = Image.open(p).convert('RGBA')
r = im.resize((int(im.width * bs * zoom), int(im.height * bs * zoom)), Image.LANCZOS)
base = Image.new('RGB', (W, H), 'white')
base.paste(r, (int((bx - x0) * zoom), int((by - y0) * zoom)))
if op < 1 and '--outline' not in a:
    al = sp.getchannel('A').point(lambda v: int(v * op)); sp.putalpha(al)
base = base.convert('RGBA'); base.alpha_composite(sp)
base.convert('RGB').save(out); print(out, W, H)
