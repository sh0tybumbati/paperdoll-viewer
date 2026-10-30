"""Bull paperdoll from the Epochs sample (mirrored to face left). Same rules as the wolf: dead side-on identical legs,
shoulder/hip pivots with round caps, two fur tones (+ horn tone), forced-tone joint discs."""
import json, sys
sys.path.insert(0, '/home/ad/.claude/skills/paperdoll-sprite/scripts')
import numpy as np
from scipy import ndimage as ndi
import pathutil as PU, trace as T

W, H = 74, 54
R = T.Ref('/home/ad/Projects/paperdoll-tests/epochs/bull_flip.png', 0.034, -10.24, -0.75, line_lum=60, levels=[89, 135])
TONE = dict(eye='#0b0b0b', hoof='#242424', nose='#484848', far='#636363', dark='#757575', mid='#b5b5b5', bone='#dbdbdb', light='#dcdcdc')
NEAR = {0: 'dark', 1: 'mid', 2: 'bone'}
FAR = {0: 'far', 1: 'dark', 2: 'mid'}
TOL = 0.14
layers, hier = {}, {}

def path(layer, tone, subs):
    return '<path style="fill:%s;fill-opacity:1;stroke:none" d="%s" inkscape:label="%s-shade-%s"/>' % (TONE[tone], PU.to_d(subs if isinstance(subs, list) else [subs], 2), layer, tone)

def spl(pts, corners):
    return PU.spline(pts, True, corners)

def part_shapes(layer, mask, cmap=NEAR, tol=TOL, blobs=None, force=(), min_tone=0.9):
    parts = R.tone_partition(mask, min_area=min_tone, force=force)
    out = []
    for k in sorted(parts, key=lambda k: -parts[k].sum()):
        for pts, cor in R.paths(parts[k], tol=tol, min_area=0.15)[:8]:
            out.append(path(layer, cmap[k], spl(pts, cor)))
    for zone in (blobs or ()):         # dark features only inside small zones: elsewhere the thick outline stroke would match
        for bm in R.dark_blobs(mask & R.poly_mask([zone]), lum_max=60, open_units=0.16, min_area=0.12):
            for pts, cor in R.paths(bm, tol=0.08, min_area=0.1, sigma=1.5)[:1]:
                out.append(path(layer, 'eye', spl(pts, cor)))
    return out

def interior_lines(layer, mask, tone='far', inset=0.45, min_area=0.1, tol=0.05):
    m = (R.lum < 75) & R.inset(mask, inset)
    return [path(layer, tone, spl(p, c)) for p, c in R.paths(m, tol=tol, min_area=min_area, sigma=1.2)[:12]]

M = lambda poly, grow=0.35: R.part_mask([poly], (), grow)
cap = lambda c, r: R.disc_mask(c[0], c[1], r) & R.fg

# ---------- cut polygons (sprite units) ----------
HEAD = [(2,9.5),(21.2,9.5),(21.2,17),(20.4,22),(18.8,25.4),(18,28),(2,28)]
EAR_R = [(5,13),(10.5,13),(10.5,17.8),(5,17.8)]
EAR_L = [(15.5,12.8),(24,12.8),(24,19),(15.5,19)]
HORN_R = [(1,1),(8.9,1),(11.8,6),(14.0,9.8),(14.0,15),(1,15)]
HORN_L = [(8.9,1),(25,1),(25,15),(14.0,15),(14.0,9.8),(11.8,6)]
NECK = [(21,8.5),(40,7),(38,16),(36,26),(34.6,33.5),(30,34.4),(26,33.4),(22.5,30),(19,26.5),(21,19)]
BODY = [(38,6.5),(66.4,6.5),(66.3,18),(65.9,24),(66.0,30),(66.6,36.5),(65.6,39.0),(62.0,38.6),(59.0,36.0),(57.0,32.0),(54,31.5),(50,33.5),(46,34.6),(36,34.4),(34.6,33.5),(36,26),(38,16)]      # includes the whole haunch, so a swinging hind leg leaves a rounded rump, not a bite
TAIL = [(66.2,12),(72,12),(72,42),(66.8,42),(66.4,36),(65.8,30),(65.8,24),(66,18)]
FRONT = [(29.8,19),(36.5,19),(36.5,34),(35.8,41),(35.6,51),(29,51),(29.6,45),(30.6,38),(30.2,29)]
HIND = [(55,16),(65.6,16),(66.4,26),(67.2,34),(68,40),(68,51),(61,51),(61.6,45),(62,40),(60,35),(57,30)]
SHOULDER, HIP = (32.7, 23.5), (60.8, 22.5)
HEADP, HEADR = (20.5, 17.5), 3.4
NECKP, NECKR = (37.0, 18.0), 6.5

# ---------- legs ----------
legs = {}
for key, poly, piv, rtop, cut in (('f', FRONT, SHOULDER, 3.2, 41.0), ('b', HIND, HIP, 4.2, 40.5)):
    base = ndi.binary_opening(M(poly, 0.0), iterations=13)
    full = R.top_cap(base, piv, rtop)
    up, lo, px = R.limb_cap(full, cut)
    py = int(round(R.px(0, cut)[1])); xs = np.nonzero(full[py])[0]
    r = (xs.max() - xs.min()) / 2 * R.s
    R.force_tone_disc(px, cut, r)
    kp = R.force_tone_disc(piv[0], piv[1], rtop)                  # whatever the body is at this joint
    box = R.poly_mask([[(piv[0] - 8, piv[1] - 5), (piv[0] + 8, piv[1] - 5), (piv[0] + 8, cut - r - 0.6), (piv[0] - 8, cut - r - 0.6)]])
    legs[key] = dict(up=up, lo=lo, px=px, piv=piv, cut=cut, box=box, kp=kp)
for cx, cy, r in ((HEADP[0], HEADP[1], HEADR), (NECKP[0], NECKP[1], NECKR), (66, 14, 2.6), (19.5, 15.3, 2.0), (8, 15.2, 2.0), (19.5, 11.5, 2.0), (12.4, 11.8, 2.0)):
    R.force_tone_disc(cx, cy, r)

yy = np.arange(R.shape[0])[:, None]
paw_zone = yy > R.px(0, 46.0)[1]
for key, names in (('f', ('leg-fr', 'leg-fl')), ('b', ('leg-br', 'leg-bl'))):
    g = legs[key]
    for nm in names:
        cm = FAR if nm.endswith('r') else NEAR
        layers[nm + '-u'] = part_shapes(nm + '-u', g['up'], cm, force=[(g['box'], g['kp'])], min_tone=2.4)
        layers[nm + '-l'] = part_shapes(nm + '-l', g['lo'], cm, min_tone=1.6) + interior_lines(nm + '-l', g['lo'] & paw_zone)
        hier[nm + '-u'] = ('body', g['piv'][0], g['piv'][1])
        hier[nm + '-l'] = (nm + '-u', round(g['px'], 2), g['cut'])

layers['shadow'] = ['<ellipse style="fill:#000000;fill-opacity:0.4;stroke:none" cx="37.5" cy="49.9" rx="31" ry="2.5" inkscape:label="shadow"/>']
TUFT = [(66.0, 30.5), (71.5, 30.5), (71.5, 41), (66.0, 41)]      # black fur in the sample: outline-dark, traced as one silhouette
TAILROOT, TAILMID, TAILLOW = (66.5, 14.3), (67.5, 24.0), (67.7, 31.0)
layers['tail'] = [path('tail', 'dark', PU.capsule(TAILROOT, TAILMID, 0.75, 0.6)), path('tail', 'dark', PU.capsule(TAILMID, TAILLOW, 0.6, 0.7))]   # drawn: round root cap on the pivot
for pts, cor in R.paths(M(TUFT, 0.2), tol=0.1, min_area=0.3, sigma=1.5)[:2]:
    layers['tail'].append(path('tail', 'dark', spl(pts, cor)))
hier['tail'] = ('body', TAILROOT[0], TAILROOT[1])
layers['body'] = part_shapes('body', M(BODY, 1.0) | cap(NECKP, NECKR), min_tone=2.4)
layers['neck'] = part_shapes('neck', M(NECK, 1.0) | cap(HEADP, HEADR) | cap(NECKP, NECKR), min_tone=2.0); hier['neck'] = ('body', NECKP[0], NECKP[1])
layers['ear-r'] = part_shapes('ear-r', M(EAR_R)); hier['ear-r'] = ('head', 8.0, 15.2)
layers['horn-r'] = part_shapes('horn-r', M(HORN_R), FAR); hier['horn-r'] = ('head', 12.4, 11.8)
layers['head'] = part_shapes('head', M(HEAD) | cap(HEADP, HEADR), blobs=[[(11.5,15.0),(16.2,15.0),(16.2,18.8),(11.5,18.8)], [(7.2,21.2),(9.7,21.2),(9.7,23.0),(7.2,23.0)]]); hier['head'] = ('neck', HEADP[0], HEADP[1])
layers['ear-l'] = part_shapes('ear-l', M(EAR_L)); hier['ear-l'] = ('head', 19.5, 15.3)
layers['horn-l'] = part_shapes('horn-l', M(HORN_L)); hier['horn-l'] = ('head', 19.5, 11.5)

order = ['shadow','tail','leg-br-u','leg-br-l','leg-fr-u','leg-fr-l','body','neck','leg-bl-u','leg-bl-l','leg-fl-u','leg-fl-l','ear-r','horn-r','head','ear-l','horn-l']
out = ['<?xml version="1.0" encoding="UTF-8" standalone="no"?>',
       '<svg width="%d" height="%d" viewBox="0 0 %d %d" version="1.1" xmlns:inkscape="http://www.inkscape.org/namespaces/inkscape" xmlns="http://www.w3.org/2000/svg">' % (W, H, W, H)]
for i, name in enumerate(order):
    out.append('<g inkscape:groupmode="layer" id="layer%d" inkscape:label="%s" style="display:inline">' % (i, name))
    out += layers[name]; out.append('</g>')
out.append('</svg>')
open('bull_raw.svg', 'w').write('\n'.join(out))
json.dump({'pivots': {k: dict(parent=p, x=x, y=y) for k, (p, x, y) in hier.items()}}, open('bull.hierarchy.json', 'w'), indent=1)
print('shapes per layer:', {k: len(v) for k, v in layers.items()})
