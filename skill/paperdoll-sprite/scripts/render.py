#!/usr/bin/env python3
"""Render a sprite for inspection. usage:
  render.py sprite.svg out.png [--scale 12] [--no-pivots] [--hide LAYER,...] [--solo LAYER,...] [--ref ref.png]
--ref puts the reference image beside the render (same height). Needs rsvg-convert;
--ref needs python3 + PIL (falls back to render-only if missing)."""
import re, subprocess, sys, tempfile, os
import xml.etree.ElementTree as ET

a = sys.argv[1:]
src, out = a[0], a[1]
def opt(n, d=None):
    return a[a.index(n) + 1] if n in a else d
scale = float(opt('--scale', 12))
hide = set((opt('--hide') or '').split(',')) - {''}
solo = set((opt('--solo') or '').split(',')) - {''}
text = open(src).read()
IL = '{http://www.inkscape.org/namespaces/inkscape}label'
GM = '{http://www.inkscape.org/namespaces/inkscape}groupmode'
ET.register_namespace('', 'http://www.w3.org/2000/svg')
for p, u in (('inkscape', 'http://www.inkscape.org/namespaces/inkscape'), ('sodipodi', 'http://sodipodi.sourceforge.net/DTD/sodipodi-0.dtd'), ('xlink', 'http://www.w3.org/1999/xlink')):
    ET.register_namespace(p, u)
root = ET.fromstring(text)
for l in root:
    if l.get(GM) != 'layer':
        continue
    n = l.get(IL)
    if (solo and n not in solo) or n in hide:
        l.set('style', 'display:none')
    if '--no-pivots' in a:
        for e in list(l):
            if (e.get(IL) or '').endswith('-pivot'):
                l.remove(e)
tmp = tempfile.mkdtemp()
t = os.path.join(tmp, 'r.svg')
ET.ElementTree(root).write(t)
w = int(float(root.get('width')) * scale)
subprocess.run(['rsvg-convert', '-w', str(w), '-b', 'white', t, '-o', out], check=True)
ref = opt('--ref')
if ref:
    try:
        from PIL import Image
        r, s = Image.open(ref).convert('RGB'), Image.open(out).convert('RGB')
        r = r.resize((int(r.width * s.height / r.height), s.height))
        c = Image.new('RGB', (r.width + s.width, s.height), 'white')
        c.paste(r, (0, 0)); c.paste(s, (r.width, 0)); c.save(out)
    except ImportError:
        print('PIL missing; wrote render only')
print(out)
