"""Rabbit paperdoll from the Epochs sample (mirrored to face left). Same rules as the wolf/bull: dead side-on identical
legs (the standing near foreleg and near hind leg are reused for the far side), shoulder/hip pivots with round caps,
two fur tones (+ pink inner ear, cream bib), forced-tone joint discs."""
import os, sys, json
HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, 'sources') if os.path.isdir(os.path.join(HERE, 'sources')) else HERE
sys.path.insert(0, os.path.join(HERE, '..', 'scripts')); sys.path.insert(0, os.path.expanduser('~/.claude/skills/paperdoll-sprite/scripts')); sys.path.insert(0, HERE)
import numpy as np
from scipy import ndimage as ndi
import pathutil as PU, trace as T

W, H = 50, 50
R = T.Ref(os.path.join(SRC, 'rabbit_flip.png'), 0.032, -19.44, -0.5, line_lum=70, levels=[80, 150, 195], thick_px=12)
TONE = dict(eye='#0b0b0b', hoof='#242424', nose='#484848', far='#636363', dark='#757575', mid='#b5b5b5', bone='#dbdbdb', light='#dcdcdc')
NEAR = {0: 'far', 1: 'dark', 2: 'mid', 3: 'bone'}
FAR = {0: 'nose', 1: 'far', 2: 'dark', 3: 'mid'}
TOL = 0.12
layers, hier = {}, {}

def path(layer, tone, subs):
    return '<path style="fill:%s;fill-opacity:1;stroke:none" d="%s" inkscape:label="%s-shade-%s"/>' % (TONE[tone], PU.to_d(subs if isinstance(subs, list) else [subs], 2), layer, tone)

def spl(pts, corners):
    return PU.spline(pts, True, corners)

def part_shapes(layer, mask, cmap=NEAR, tol=TOL, blobs=None, force=(), min_tone=0.9, open_px=3):
    parts = R.tone_partition(mask, min_area=min_tone, force=force, open_px=open_px)
    out = []
    for k in sorted(parts, key=lambda k: -parts[k].sum()):
        for pts, cor in R.paths(parts[k], tol=tol, min_area=0.12)[:8]:
            out.append(path(layer, cmap[k], spl(pts, cor)))
    for zone in (blobs or ()):       # dark features only inside small zones (the outline stroke would match elsewhere)
        for bm in R.dark_blobs(mask & R.poly_mask([zone]), lum_max=60, open_units=0.14, min_area=0.1):
            for pts, cor in R.paths(bm, tol=0.07, min_area=0.08, sigma=1.4)[:1]:
                out.append(path(layer, 'eye', spl(pts, cor)))
    return out

def interior_lines(layer, mask, tone='far', inset=0.4, min_area=0.08, tol=0.05):
    m = (R.lum < 75) & R.inset(mask, inset)
    return [path(layer, tone, spl(p, c)) for p, c in R.paths(m, tol=tol, min_area=min_area, sigma=1.2)[:10]]

M = lambda poly, grow=0.35: R.part_mask([poly], (), grow)
cap = lambda c, r: R.disc_mask(c[0], c[1], r) & R.fg

# ---------- cut polygons (sprite units) ----------
HEAD = [(0, 12.8), (14.8, 12.8), (15.6, 17), (15.2, 23.5), (9.5, 24.8), (0, 24.6)]
EAR_R = [(8.5, 1.5), (13.4, 1.5), (13.4, 14.8), (8.5, 14.8)]
EAR_L = [(12.8, 1.5), (19.2, 1.5), (19.2, 15.6), (12.8, 15.6)]
NECK = [(14, 14.5), (21, 16.5), (20.4, 24), (21.4, 31), (19, 33.5), (14.5, 32.6), (11, 28), (9.5, 24.8), (15.2, 23.5), (15.6, 17)]
BODY = [(16, 13), (42, 12.5), (44.2, 22), (43.8, 30), (41, 34.5), (35, 33), (30, 32.4), (24, 33.6), (21.4, 33), (19.6, 29), (20.4, 24), (21, 16.5)]
TAIL = [(43.3, 21), (48.5, 21), (48.5, 30.5), (43.6, 30.5), (43.2, 26)]
FRONT = [(18.6, 25), (25.2, 25), (25.4, 33), (25, 41), (24.8, 48), (16.8, 48), (18.2, 43), (19.2, 38), (19.0, 31)]
HIND = [(33.5, 20), (45.2, 20), (46.4, 28), (47.4, 35), (47.6, 48), (40.4, 48), (41, 44), (42.4, 40), (43, 37), (39.2, 35.4), (34, 30.6)]
SHOULDER, HIP = (21.8, 28.0), (39.4, 27.0)
HEADP, HEADR = (14.8, 19.5), 3.0
NECKP, NECKR = (19.8, 25.5), 3.6

# ---------- legs ----------
legs = {}
for key, poly, piv, rtop, cut in (('f', FRONT, SHOULDER, 3.0, 40.0), ('b', HIND, HIP, 5.0, 37.4)):
    base = ndi.binary_opening(M(poly, 0.0), iterations=12)
    full = R.top_cap(base, piv, rtop)
    up, lo, px = R.limb_cap(full, cut)
    py = int(round(R.px(0, cut)[1])); xs = np.nonzero(full[py])[0]
    r = (xs.max() - xs.min()) / 2 * R.s
    R.force_tone_disc(px, cut, r)
    kp = R.force_tone_disc(piv[0], piv[1], rtop)
    box = R.poly_mask([[(piv[0] - 9, piv[1] - 6), (piv[0] + 9, piv[1] - 6), (piv[0] + 9, cut - r - 0.6), (piv[0] - 9, cut - r - 0.6)]])
    legs[key] = dict(up=up, lo=lo, px=px, piv=piv, cut=cut, box=box, kp=kp)
for cx, cy, r in ((HEADP[0], HEADP[1], HEADR), (NECKP[0], NECKP[1], NECKR), (44, 25, 2.4), (14.6, 14.6, 1.8), (11, 13.6, 1.8)):
    R.force_tone_disc(cx, cy, r)

yy = np.arange(R.shape[0])[:, None]
paw_zone = yy > R.px(0, 43.0)[1]
for key, names in (('f', ('leg-fr', 'leg-fl')), ('b', ('leg-br', 'leg-bl'))):
    g = legs[key]
    for nm in names:
        cm = FAR if nm.endswith('r') else NEAR
        layers[nm + '-u'] = part_shapes(nm + '-u', g['up'], cm, force=[(g['box'], g['kp'])], min_tone=2.0)
        layers[nm + '-l'] = part_shapes(nm + '-l', g['lo'], cm, min_tone=1.2) + interior_lines(nm + '-l', g['lo'] & paw_zone)
        hier[nm + '-u'] = ('body', g['piv'][0], g['piv'][1])
        hier[nm + '-l'] = (nm + '-u', round(g['px'], 2), g['cut'])

layers['shadow'] = ['<ellipse style="fill:#000000;fill-opacity:0.4;stroke:none" cx="25" cy="46.2" rx="22" ry="2.2" inkscape:label="shadow"/>']
layers['tail'] = part_shapes('tail', M(TAIL), min_tone=0.8); hier['tail'] = ('body', 44.0, 25.0)
layers['body'] = part_shapes('body', M(BODY, 0.8) | cap(NECKP, NECKR), min_tone=2.0)
layers['neck'] = part_shapes('neck', M(NECK, 0.8) | cap(HEADP, HEADR) | cap(NECKP, NECKR), min_tone=1.6); hier['neck'] = ('body', NECKP[0], NECKP[1])
layers['ear-r'] = part_shapes('ear-r', M(EAR_R), NEAR, min_tone=1.6, open_px=8); hier['ear-r'] = ('head', 11.0, 13.6)
layers['head'] = part_shapes('head', M(HEAD) | cap(HEADP, HEADR), blobs=[[(7.0, 15.2), (11.6, 15.2), (11.6, 19.2), (7.0, 19.2)]], min_tone=0.5, open_px=5); hier['head'] = ('neck', HEADP[0], HEADP[1])
layers['ear-l'] = part_shapes('ear-l', M(EAR_L), min_tone=1.6, open_px=8); hier['ear-l'] = ('head', 14.6, 14.6)

order = ['shadow','tail','leg-br-u','leg-br-l','leg-fr-u','leg-fr-l','body','neck','leg-bl-u','leg-bl-l','leg-fl-u','leg-fl-l','ear-r','head','ear-l']
out = ['<?xml version="1.0" encoding="UTF-8" standalone="no"?>',
       '<svg width="%d" height="%d" viewBox="0 0 %d %d" version="1.1" xmlns:inkscape="http://www.inkscape.org/namespaces/inkscape" xmlns="http://www.w3.org/2000/svg">' % (W, H, W, H)]
for i, name in enumerate(order):
    out.append('<g inkscape:groupmode="layer" id="layer%d" inkscape:label="%s" style="display:inline">' % (i, name))
    out += layers[name]; out.append('</g>')
out.append('</svg>')
open('rabbit_raw.svg', 'w').write('\n'.join(out))
json.dump({'pivots': {k: dict(parent=p, x=x, y=y) for k, (p, x, y) in hier.items()}}, open('rabbit.hierarchy.json', 'w'), indent=1)
print('shapes per layer:', {k: len(v) for k, v in layers.items()})
