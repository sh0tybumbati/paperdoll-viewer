"""Boar paperdoll built from the user's boar.svg layer layout, retraced against the embedded reference.
Coordinates below are in the user's original frame; OFF shifts x so the canvas starts at 0."""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))        # builds are relocatable: everything is found relative to this file
SRC = os.path.join(HERE, 'sources')
sys.path.insert(0, os.path.join(HERE, '..', 'scripts')); sys.path.insert(0, HERE)
import json, math, sys

import pathutil as PU

OFF, W, H = 19.5, 79, 66
SNOUT_EXT = 2.4   # how far the muzzle is stretched forward (units); pad/nostril move rigidly
TONE = dict(eye='#0b0b0b', hoof='#242424', nose='#484848', far='#636363', dark='#757575', mid='#b5b5b5', bone='#dbdbdb', light='#dcdcdc')
layers = []
hier = {}

def _w(x):
    t = max(0.0, min(1.0, (-7.5 - x) / 2.7))
    return t * t * (3 - 2 * t)

def wp(subs):
    """stretch the muzzle: x < -10.2 shifts by the full SNOUT_EXT (rigid), x > -7.5 not at all, smooth between"""
    return PU.xform(subs if isinstance(subs, list) else [subs], lambda p: (p[0] - SNOUT_EXT * _w(p[0]), p[1]))

def sp(pts, corners=(), closed=True, k=1.0):
    return PU.spline([(x, y) for x, y in pts], closed, corners, k)

def d_of(subs):
    return PU.to_d(PU.translate(subs, OFF, 0), 2)

def shape(layer, tone, subs, name=None):
    return '<path style="fill:%s;fill-opacity:1;stroke:none" d="%s" inkscape:label="%s-shade-%s"/>' % (TONE[tone], d_of(subs if isinstance(subs, list) else [subs]), layer, tone)

def ellipse(layer, tone, cx, cy, rx, ry):
    return '<ellipse style="fill:%s;fill-opacity:1;stroke:none" cx="%g" cy="%g" rx="%g" ry="%g" inkscape:label="%s-shade-%s"/>' % (TONE[tone], cx + OFF, cy, rx, ry, layer, tone)

def L(label, shapes):
    layers.append((label, shapes))

def spikes(base, heights, lean=0.8):
    """crest polyline with a bristle tip between each pair of base points; returns pts, corner indices"""
    pts, corners = [base[0]], []
    for i in range(len(base) - 1):
        (x0, y0), (x1, y1) = base[i], base[i + 1]
        dx, dy = x1 - x0, y1 - y0; n = math.hypot(dx, dy); ux, uy = dx / n, dy / n
        h = heights[i % len(heights)]
        tip = ((x0 + x1) / 2 + uy * h + ux * lean, (y0 + y1) / 2 - ux * h + uy * lean)
        corners.append(len(pts)); pts.append(tip); pts.append(base[i + 1])
    return pts, corners

def leg_pair(name, pts, corners, cut, tone, hoof_pts, hoof_corners, hoof_tone, parent, top_pivot, ov=0.9):
    full = sp(pts, corners)
    up, lo, (px, _) = PU.cap_split(full, cut)
    L(name + '-u', [shape(name + '-u', tone, up)])
    L(name + '-l', [shape(name + '-l', tone, lo), shape(name + '-l', hoof_tone, sp(hoof_pts, hoof_corners))])
    hier[name + '-u'] = (parent, top_pivot[0], top_pivot[1])
    hier[name + '-l'] = (name + '-u', round(px, 2), cut)

# ---------- shapes ----------
shadow = '<ellipse style="fill:#000000;fill-opacity:0.4;stroke:none" cx="%g" cy="61.4" rx="24" ry="3.3" inkscape:label="shadow"/>' % (31.5 + OFF)
L('shadow', [shadow])

L('tail', [
  shape('tail', 'dark', sp([(50.3,31.6),(51.7,32.6),(53.0,35.0),(54.2,38.4),(55.2,41.8),(56.0,45.0),(56.3,46.6),(55.2,46.9),(54.6,44.5),(53.6,41.0),(52.5,37.5),(51.2,35.0),(50.2,34.0)], corners=(0, 6))),
  shape('tail', 'far', sp([(54.7,43.4),(55.6,42.9),(56.5,45.0),(56.6,47.0),(55.5,47.1),(54.9,45.5)], corners=(3,)))])

# far legs (behind the body), tone far

# body: mane (fringe + dark band), torso, belly shadow
tips = [(-3.0,26.6),(-1.8,24.5),(-0.2,23.3),(1.4,22.6),(3.0,21.8),(4.6,21.0),(6.2,20.4),(7.8,19.5),(9.9,18.25),(11.2,18.6),(12.4,18.0),(13.7,17.6),(15.0,16.2),(16.2,17.4),(17.6,17.3),(19.2,17.2),(20.8,17.0),(22.6,17.8),(24.4,18.3),(26.2,19.2),(28.0,20.2),(30.0,21.2),(32.0,22.2),(34.2,23.3),(36.4,24.2),(38.8,25.0),(41.0,25.6)]
depth = [0.7, 1.6, 0.6, 1.1, 0.8, 1.9, 0.7, 1.0, 1.5, 0.7, 1.2, 0.6, 2.0, 0.8, 1.0, 1.6, 0.7, 0.9, 1.3, 0.7, 1.1, 0.8, 1.2, 0.7, 0.9, 0.6, 0.8]
fp, fc = [], []
for i, (x, y) in enumerate(tips):
    fc.append(len(fp)); fp.append((x, y))
    if i + 1 < len(tips):
        (x1, y1) = tips[i + 1]; dx, dy = x1 - x, y1 - y; n = math.hypot(dx, dy)
        t = 0.22; dd = depth[i % len(depth)]
        fp.append((x + dx * t - dy / n * -dd * 0 + (dy / n) * dd, y + dy * t - (dx / n) * dd))   # inward (below the crest line)
fp += [(41.0,27.2),(30,28),(20,27.5),(10,28.5),(3,31),(-2.5,31.8),(-3.7,30.6),(-3.0,29.7),(-3.8,28.5),(-3.0,27.7)]
fc += [len(fp) - 4, len(fp) - 2]
def jag(line, amp, phase=1):
    out = []
    for i, (x, y) in enumerate(line):
        out.append((x, y + amp * (phase if i % 2 else -phase)))
    return out
band_top = [(-0.2,27.2),(2.25,24.5),(6,22.4),(9,21.3),(12.25,20.3),(16,19.8),(20,19.7),(24,20.4),(28,21.4),(32,22.6),(36,24.0),(39,25.2)]
band_bot = jag([(36.5,25.8),(32.5,25.0),(28.5,24.0),(24.5,23.1),(20.5,22.3),(16.5,22.2),(13.5,22.5),(10.5,23.3),(8.0,24.3),(5.5,25.6),(3.2,26.6),(1.2,27.4)], 0.35)
band = band_top + band_bot
L('body', [
  shape('body', 'dark', sp(fp, corners=tuple(fc))),
  shape('body', 'far', sp(band, corners=tuple(range(len(band_top) + 1, len(band))))),
  shape('body', 'dark', sp([(2,27.5),(8,25.4),(16,23.5),(24,23.4),(32,25.0),(40,26.3),(46.2,28.1),(48.4,29.6),(50.5,32),(51.5,35.2),(50.8,40),(50.4,44.5),(49.5,49.5),(46,51),(42,50.8),(36,50.6),(30,50.4),(24,51.2),(18,52.6),(12.7,53.3),(6.8,51.7),(1,49.5),(-3.8,48.2),(-3,40),(-2,33)])),
  shape('body', 'far', sp([(24.4,41.5),(27.5,40.4),(31,41.8),(34.8,41.2),(37.9,35.0),(38.7,42.0),(40.2,47.0),(41.5,50.7),(36,50.6),(30,50.4),(24,51.2),(22,51.4)], corners=(4,)))])

L('neck', [shape('neck', 'far', sp([(1.5,27.0),(6,25.0),(11,24.6),(13.0,27.2),(12.2,28.6),(14.0,31.0),(12.6,32.6),(14.2,36.0),(12.4,38.0),(13.4,41.6),(12.2,43.6),(14.2,46.6),(13.2,48.4),(15.0,51.0),(13.8,53.0),(8,52.0),(3,50.5),(0.5,45),(0.8,36),(0.5,30)], corners=(3,4,5,6,7,8,9,10,11,12,13,14)))])
hier['neck'] = ('body', 13.0, 40.0)

# near legs
# far-side copy: identical geometry and pivot (dead side-on), one step darker
leg_pair('leg-br', [(40.0,30.4),(44.5,29.0),(47.8,30.0),(50.4,32.2),(51.4,35.2),(50.7,39.5),(50.4,44.0),(50.9,47.2),(52.0,49.3),(52.5,51.8),(53.0,55.4),(52.9,58.9),(48.5,59.8),(49.6,57.5),(49.9,55.2),(49.5,52.8),(47.5,50.8),(45.0,49.2),(42.8,46.8),(41.0,43.5),(39.6,39.2),(38.4,34.5),(37.8,31.0)], (11, 12), 50.2, 'far',
         [(48.2,59.8),(50.0,58.9),(52.4,58.7),(53.2,60.0),(52.8,61.6),(50.6,62.2),(48.6,62.0)], (0, 3), 'nose', 'body', (44.0, 33.0))
leg_pair('leg-bl', [(40.0,30.4),(44.5,29.0),(47.8,30.0),(50.4,32.2),(51.4,35.2),(50.7,39.5),(50.4,44.0),(50.9,47.2),(52.0,49.3),(52.5,51.8),(53.0,55.4),(52.9,58.9),(48.5,59.8),(49.6,57.5),(49.9,55.2),(49.5,52.8),(47.5,50.8),(45.0,49.2),(42.8,46.8),(41.0,43.5),(39.6,39.2),(38.4,34.5),(37.8,31.0)], (11, 12), 50.2, 'dark',
         [(48.2,59.8),(50.0,58.9),(52.4,58.7),(53.2,60.0),(52.8,61.6),(50.6,62.2),(48.6,62.0)], (0, 3), 'hoof', 'body', (44.0, 33.0))
# far-side copy: identical geometry and pivot (dead side-on), one step darker
leg_pair('leg-fr', [(15.5,37.0),(16.1,41.5),(16.6,45.5),(17.3,49.2),(18.3,52.6),(19.0,55.2),(19.1,57.4),(18.6,59.2),(18.3,60.6),(22.6,60.6),(22.4,58.0),(22.8,55.3),(23.6,52.2),(24.3,48.5),(24.1,44.0),(23.6,40.0),(23.4,36.6),(19.5,35.5)], (0, 8, 9, 16), 53.6, 'far',
         [(18.2,60.2),(21.9,59.8),(22.6,61.2),(21.3,62.8),(18.0,62.8),(17.0,61.8)], (1, 3, 4), 'nose', 'body', (19.5, 38.0))
leg_pair('leg-fl', [(15.5,37.0),(16.1,41.5),(16.6,45.5),(17.3,49.2),(18.3,52.6),(19.0,55.2),(19.1,57.4),(18.6,59.2),(18.3,60.6),(22.6,60.6),(22.4,58.0),(22.8,55.3),(23.6,52.2),(24.3,48.5),(24.1,44.0),(23.6,40.0),(23.4,36.6),(19.5,35.5)], (0, 8, 9, 16), 53.6, 'dark',
         [(18.2,60.2),(21.9,59.8),(22.6,61.2),(21.3,62.8),(18.0,62.8),(17.0,61.8)], (1, 3, 4), 'hoof', 'body', (19.5, 38.0))

# ears + head
L('ear-r', [shape('ear-r', 'far', sp([(7.6,28.0),(8.2,25.6),(9.6,24.6),(10.6,25.8),(10.7,28.6),(9.6,30.4)]))])
def hs(tone, pts, corners=()):
    return shape('head', tone, wp(sp(pts, corners)))

L('head', [
  hs('bone', [(-11.2,39.6),(-10.8,40.8),(-10.7,42.0),(-11.2,43.0),(-11.5,43.7),(-11.7,42.6),(-11.7,41.0)], (0,)),
  hs('dark', [(-3.6,32.3),(-5.5,34.0),(-6.5,36.2),(-7.3,38.2),(-8.3,39.7),(-9.75,41.3),(-10.8,42.4),(-11.6,43.9),(-12.5,45.1),(-13.9,46.4),(-14.9,46.8),(-14.8,47.7),(-14.2,48.6),(-13.3,49.6),(-12.4,50.6),(-11.5,50.9),(-10.2,50.85),(-8.6,50.7),(-6.0,50.6),(-2.5,50.3),(1.5,50.2),(5.0,49.0),(6.2,44.0),(6.0,38.0),(5.0,32.5),(3.0,30.2),(0.0,30.0),(-2.0,31.0)], (10,)),
  hs('mid', [(-10.2,49.6),(-8.4,49.3),(-6.4,48.5),(-3.8,48.0),(-2.2,48.9),(-2.6,50.0),(-6,50.3),(-8.6,50.5),(-10.2,50.55)]),
  shape('head', 'far', sp([(-6.4,44.8),(-5.2,44.7),(-3.9,45.4),(-3.5,46.4),(-4.7,46.2),(-5.9,46.6)])),
  hs('nose', [(-14.9,46.8),(-14.2,46.6),(-12.8,47.1),(-11.5,47.9),(-10.6,48.9),(-10.2,49.8),(-10.2,50.6),(-11.5,50.85),(-12.4,50.6),(-13.3,49.6),(-14.2,48.5),(-14.75,47.6)], (0,)),
  hs('dark', [(-14.8,46.85),(-14.1,46.7),(-12.8,47.2),(-11.5,48.0),(-10.7,49.0),(-11.3,49.0),(-12.2,48.4),(-13.4,47.8),(-14.3,47.6)], (0,)),
  hs('eye', [(-13.4,48.7),(-12.6,48.8),(-11.6,49.5),(-11.2,50.1),(-11.9,50.2),(-12.8,49.6)]),
  # eye: shadowed socket, almond ball slanted up at the rear corner, pale sliver, catch-lights
  shape('head', 'far', sp([(-4.0,37.0),(-3.9,36.0),(-3.2,35.5),(-2.3,35.8),(-1.2,35.9),(-0.5,36.1),(-0.6,36.7),(-0.8,37.4),(-1.6,38.0),(-2.6,38.2),(-3.5,38.4),(-4.0,37.8)])),
  shape('head', 'eye', sp([(-2.75,37.1),(-2.35,36.45),(-1.6,36.1),(-0.85,36.4),(-1.25,37.0),(-1.85,37.35),(-2.5,37.4)], (0, 3))),
  shape('head', 'mid', sp([(-1.45,36.55),(-0.95,36.45),(-1.15,36.95),(-1.5,37.15),(-1.55,36.8)], (1,))),
  ellipse('head', 'light', -1.75, 36.7, 0.28, 0.3),
  ellipse('head', 'light', -2.45, 37.28, 0.14, 0.1),
  shape('head', 'far', sp([(-5.3,35.0),(-2.5,34.0),(0.6,34.8),(0.2,35.6),(-2.4,35.3),(-4.8,36.0)])),
  shape('head', 'bone', sp([(-7.15,41.0),(-7.7,42.6),(-7.75,44.1),(-7.4,45.5),(-6.35,46.9),(-5.3,47.6),(-4.75,47.3),(-4.9,46.75),(-5.6,45.9),(-6.3,44.8),(-6.5,43.4),(-6.7,41.75)], corners=(0,)))])
L('ear-l', [
  shape('ear-l', 'dark', sp([(3.6,31.8),(3.5,29.5),(4.0,27.2),(5.0,25.8),(6.4,25.0),(7.4,25.9),(7.9,28.2),(7.7,30.8),(6.6,32.0),(5.0,32.4)], corners=(4,))),
  shape('ear-l', 'far', sp([(4.5,31.3),(4.5,28.2),(5.6,26.3),(6.7,26.6),(7.2,29),(6.8,31),(5.6,31.7)]))])
hier['head'] = ('neck', 5.0, 38.0)
hier['ear-l'] = ('head', 5.3, 31.8)
hier['ear-r'] = ('head', 9.0, 29.5)
hier['tail'] = ('body', 50.6, 32.3)

# ---- head, ears, tusks, eye, brow from the Epochs boar sample; pad + nostril detail kept from the earlier design ----

import boar_head_epochs as BH
_o = BH.build(OFF)
_pc = _o['pivots']['pad']; _dx, _dy = _pc[0] - (-14.95), _pc[1] - 48.7
def _pad(tone, pts, corners=()):
    return shape('head', tone, sp([(x - 2.4 + _dx, y + _dy) for x, y in pts], corners))
_padshapes = [
  _pad('nose', [(-14.9,46.8),(-14.2,46.6),(-12.8,47.1),(-11.5,47.9),(-10.6,48.9),(-10.2,49.8),(-10.2,50.6),(-11.5,50.85),(-12.4,50.6),(-13.3,49.6),(-14.2,48.5),(-14.75,47.6)], (0,)),
  _pad('dark', [(-14.8,46.85),(-14.1,46.7),(-12.8,47.2),(-11.5,48.0),(-10.7,49.0),(-11.3,49.0),(-12.2,48.4),(-13.4,47.8),(-14.3,47.6)], (0,)),
  _pad('eye', [(-13.4,48.7),(-12.6,48.8),(-11.6,49.5),(-11.2,50.1),(-11.9,50.2),(-12.8,49.6)]),
]
L('ear-r', _o['ear-r']); L('ear-l', _o['ear-l']); L('head', _o['head'] + _padshapes)
hier['ear-l'] = ('head',) + _o['pivots']['ear-l']
hier['ear-r'] = ('head',) + _o['pivots']['ear-r']

# reorder: z-order back to front
order = ['shadow','tail','leg-br-u','leg-br-l','leg-fr-u','leg-fr-l','body','neck','leg-bl-u','leg-bl-l','leg-fl-u','leg-fl-l','ear-r','head','ear-l']
byname = dict(layers)
out = ['<?xml version="1.0" encoding="UTF-8" standalone="no"?>',
       '<svg width="%d" height="%d" viewBox="0 0 %d %d" version="1.1" xmlns:inkscape="http://www.inkscape.org/namespaces/inkscape" xmlns="http://www.w3.org/2000/svg">' % (W, H, W, H)]
for i, name in enumerate(order):
    out.append('<g inkscape:groupmode="layer" id="layer%d" inkscape:label="%s" style="display:inline">' % (i, name))
    out += byname[name]
    out.append('</g>')
out.append('</svg>')
open('boar2_raw.svg', 'w').write('\n'.join(out))
json.dump({'pivots': {k: dict(parent=p, x=x + OFF, y=y) for k, (p, x, y) in hier.items()}}, open('boar2.hierarchy.json', 'w'), indent=1)
print('layers', len(order), 'nodes per shape:', 'see svg')
