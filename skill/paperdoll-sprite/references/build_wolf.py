"""Wolf paperdoll from the Epochs sample (mirrored to face left). Geometry is extracted from the reference
(trace.py). Dead side-on: far legs are exact copies of the near legs (same shapes, same pivots). Legs pivot from
the shoulder/hip with round caps; two fur tones only; every joint has a forced-tone disc so caps blend."""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))        # builds are relocatable: everything is found relative to this file
SRC = os.path.join(HERE, 'sources')
sys.path.insert(0, os.path.join(HERE, '..', 'scripts')); sys.path.insert(0, HERE)
import json, sys

import numpy as np
from scipy import ndimage as ndi
import pathutil as PU, trace as T

W, H = 64, 54
R = T.Ref(os.path.join(SRC, 'wolf_flip.png'), 0.034, -18.4, -0.74, levels=[152.5])      # 2 fur tones: 0 dark, 1 light
TONE = dict(eye='#0b0b0b', hoof='#242424', nose='#484848', far='#636363', dark='#757575', mid='#b5b5b5', bone='#dbdbdb', light='#dcdcdc')
NEAR = {0: 'dark', 1: 'mid'}
FAR = {0: 'far', 1: 'dark'}         # far-side limbs: one step darker (depth cue); same shapes
TOL = 0.14
layers, hier = {}, {}

def path(layer, tone, subs):
    return '<path style="fill:%s;fill-opacity:1;stroke:none" d="%s" inkscape:label="%s-shade-%s"/>' % (TONE[tone], PU.to_d(subs if isinstance(subs, list) else [subs], 2), layer, tone)

def ell(layer, tone, cx, cy, rx, ry):
    return '<ellipse style="fill:%s;fill-opacity:1;stroke:none" cx="%g" cy="%g" rx="%g" ry="%g" inkscape:label="%s-shade-%s"/>' % (TONE[tone], cx, cy, rx, ry, layer, tone)

def spl(pts, corners):
    return PU.spline(pts, True, corners)

def part_shapes(layer, mask, cmap=NEAR, tol=TOL, blobs=False, force=(), min_tone=0.9):
    """gap-free tone tiling of the part: every tone region traced on its own, largest first"""
    parts = R.tone_partition(mask, min_area=min_tone, force=force)
    out = []
    for k in sorted(parts, key=lambda k: -parts[k].sum()):
        for pts, cor in R.paths(parts[k], tol=tol, min_area=0.15)[:8]:
            out.append(path(layer, cmap[k], spl(pts, cor)))
    if blobs:
        for bm in R.dark_blobs(mask, open_units=0.34, min_area=0.6):
            for pts, cor in R.paths(bm, tol=0.08, min_area=0.2, sigma=1.5)[:1]:
                out.append(path(layer, 'eye', spl(pts, cor)))
    return out

def interior_lines(layer, mask, tone='far', inset=0.45, min_area=0.1, tol=0.05):
    m = (R.lum < 75) & R.inset(mask, inset)
    return [path(layer, tone, spl(p, c)) for p, c in R.paths(m, tol=tol, min_area=min_area, sigma=1.2)[:12]]

M = lambda poly, grow=0.35: R.part_mask([poly], (), grow)

# ---------- cut polygons (sprite units) ----------
HEAD = [(-2,8.6),(18.6,8.6),(16.6,13),(14.6,17.5),(12.6,21.8),(-2,21.8)]
EAR_R = [(8.4,2),(13.4,2),(13.4,10.2),(8.4,10.2)]
EAR_L = [(13.2,2),(18.8,2),(18.8,11.2),(13.2,11.2)]
NECK = [(18.6,8.6),(26,8.6),(33,13.5),(32,17),(27,24),(22.5,32.9),(20,32.2),(16.5,30.8),(13.5,28.5),(11.5,25),(12.6,21.8),(14.6,17.5),(16.6,13)]
BODY = [(33,12),(47.6,12),(47.8,19),(49.2,24),(50,29),(50.4,34.6),(44,32.8),(38,31.2),(34,33.0),(28,33.8),(22.5,33.4),(22.5,32.9),(27,24),(32,17)]
TAIL = [(46.4,17),(66,17),(66,44),(51,44),(50.4,38.5),(49.9,34.6),(49.6,29),(48.8,24),(47.4,19)]
# one leg shape per limb pair (near legs); far legs reuse it
FRONT = [(22.2,21.5),(28.2,21.5),(28.8,30),(30.5,34),(30.5,51),(20.5,51),(20.5,46.4),(22.1,44.5),(22.6,38),(22.4,33),(22.0,29)]
HIND = [(41.4,22.4),(48.4,22.4),(49.0,28),(49.5,34.6),(50.1,38.5),(51,40),(51,51),(43.4,51),(43.4,46.5),(44.2,45.5),(45.4,42),(45,38.5),(43.5,36),(41.7,33.2),(40.2,30)]
FBOX = [(21,20),(30,20),(30,37.6),(21,37.6)]      # inside the torso: flat tone so nothing has to line up
HBOX = [(39,20),(52,20),(52,36.0),(39,36.0)]
SHOULDER, HIP = (25.2, 25.0), (45.2, 26.2)
HEADP, HEADR = (15.2, 15.0), 3.2        # head joint: pivot and cap radius
NECKP, NECKR = (26.0, 22.0), 4.5        # neck base joint

# ---------- legs: masks first, joint tone discs next, shapes last ----------
legs = {}
for key, poly, piv, rtop, cut, box in (('f', FRONT, SHOULDER, 3.0, 40.5, FBOX), ('b', HIND, HIP, 3.8, 39.0, HBOX)):
    base = ndi.binary_opening(M(poly, 0.0), iterations=13)       # drop thin fur spikes (they hang off the joint with a gap)
    full = R.top_cap(base, piv, rtop)
    up, lo, px = R.limb_cap(full, cut)
    py = int(round(R.px(0, cut)[1])); xs = np.nonzero(full[py])[0]
    R.force_tone_disc(px, cut, (xs.max() - xs.min()) / 2 * R.s)       # knee/hock: same tone both sides
    R.force_tone_disc(piv[0], piv[1], rtop, 0)                        # shoulder/hip: dark, like the body
    legs[key] = dict(up=up, lo=lo, px=px, piv=piv, cut=cut, box=R.poly_mask([box]))
# other joints. Head/neck/body get ball-joint caps: both parts keep the disc around the pivot, tone forced uniform
for cx, cy, r in ((HEADP[0], HEADP[1], HEADR), (NECKP[0], NECKP[1], NECKR), (49, 23, 2.6), (15.6, 9.8, 2.2), (11, 9.8, 2.2)):
    R.force_tone_disc(cx, cy, r)
cap = lambda c, r: R.disc_mask(c[0], c[1], r) & R.fg

yy = np.arange(R.shape[0])[:, None]
paw_zone = yy > R.px(0, 44.2)[1]
for key, names in (('f', ('leg-fr', 'leg-fl')), ('b', ('leg-br', 'leg-bl'))):
    g = legs[key]
    for nm in names:
        far = nm.endswith('r')
        cm = FAR if far else NEAR
        layers[nm + '-u'] = part_shapes(nm + '-u', g['up'], cm, force=[(g['box'], 0)], min_tone=2.4)
        layers[nm + '-l'] = part_shapes(nm + '-l', g['lo'], cm, min_tone=1.6) + interior_lines(nm + '-l', g['lo'] & paw_zone)
        hier[nm + '-u'] = ('body', g['piv'][0], g['piv'][1])
        hier[nm + '-l'] = (nm + '-u', round(g['px'], 2), g['cut'])

layers['shadow'] = ['<ellipse style="fill:#000000;fill-opacity:0.4;stroke:none" cx="32.5" cy="49.9" rx="27" ry="2.4" inkscape:label="shadow"/>']
layers['tail'] = part_shapes('tail', M(TAIL), min_tone=2.0); hier['tail'] = ('body', 49.0, 23.0)
layers['body'] = part_shapes('body', M(BODY, 0.2) | cap(NECKP, NECKR), min_tone=2.4)
layers['neck'] = part_shapes('neck', M(NECK) | cap(HEADP, HEADR) | cap(NECKP, NECKR)); hier['neck'] = ('body', NECKP[0], NECKP[1])
layers['ear-r'] = part_shapes('ear-r', M(EAR_R)); hier['ear-r'] = ('head', 11.0, 9.8)
face = [
  path('head', 'eye', spl([(8.5,13.45),(9.3,12.9),(10.4,12.55),(11.5,12.75),(11.1,13.15),(10.2,13.1),(9.4,13.5),(8.8,13.7)], (0, 3))),
  path('head', 'eye', spl([(9.4,11.7),(10.2,11.3),(11.2,11.4),(11.8,11.9),(11.5,12.0),(10.9,11.65),(10.2,11.6),(9.6,11.95)], (2, 3))),
  ell('head', 'light', 10.05, 13.12, 0.55, 0.42), ell('head', 'eye', 10.12, 13.1, 0.25, 0.32), ell('head', 'light', 9.95, 12.98, 0.1, 0.1),
  path('head', 'eye', spl([(4.9,18.4),(6.5,18.2),(8.5,17.9),(10.1,17.55),(10.15,17.95),(8.8,18.35),(6.8,18.75),(5.0,18.85)], (3, 4))),
] + [ell('head', 'eye', x, y, 0.17, 0.17) for x, y in ((5.57,17.05),(6.25,16.8),(6.07,17.6),(6.8,17.3))]
layers['head'] = part_shapes('head', M(HEAD) | cap(HEADP, HEADR), blobs=True) + face; hier['head'] = ('neck', HEADP[0], HEADP[1])
layers['ear-l'] = part_shapes('ear-l', M(EAR_L)); hier['ear-l'] = ('head', 15.6, 9.8)

order = ['shadow','tail','leg-br-u','leg-br-l','leg-fr-u','leg-fr-l','body','neck','leg-bl-u','leg-bl-l','leg-fl-u','leg-fl-l','ear-r','head','ear-l']
out = ['<?xml version="1.0" encoding="UTF-8" standalone="no"?>',
       '<svg width="%d" height="%d" viewBox="0 0 %d %d" version="1.1" xmlns:inkscape="http://www.inkscape.org/namespaces/inkscape" xmlns="http://www.w3.org/2000/svg">' % (W, H, W, H)]
for i, name in enumerate(order):
    out.append('<g inkscape:groupmode="layer" id="layer%d" inkscape:label="%s" style="display:inline">' % (i, name))
    out += layers[name]; out.append('</g>')
out.append('</svg>')
open('wolf_raw.svg', 'w').write('\n'.join(out))
json.dump({'pivots': {k: dict(parent=p, x=x, y=y) for k, (p, x, y) in hier.items()}}, open('wolf.hierarchy.json', 'w'), indent=1)
print('shapes per layer:', {k: len(v) for k, v in layers.items()})
