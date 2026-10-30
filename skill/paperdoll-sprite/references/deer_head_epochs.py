"""Deer head, ears and antlers extracted from the Epochs stag sample (mirrored to face left).
Frame: the deer sprite after a +DY vertical shift. Returns SVG shape strings and pivots."""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))        # builds are relocatable: everything is found relative to this file
SRC = os.path.join(HERE, 'sources')
sys.path.insert(0, os.path.join(HERE, '..', 'scripts')); sys.path.insert(0, HERE)
import sys

import numpy as np
import pathutil as PU, trace as T

DY = 13.0
S = 0.046
HP = (16.72, 16.0 + DY)                              # existing head pivot, shifted
OX, OY = HP[0] - (470 + 416) * S, HP[1] - 640 * S     # crop (470, 640) = head pivot
R = T.Ref(os.path.join(SRC, 'stag_flip.png'), S, OX, OY, line_lum=52, levels=[85, 170], thick_px=8)
TONE = dict(eye='#0b0b0b', nose='#484848', far='#636363', dark='#757575', mid='#b5b5b5', bone='#dbdbdb', light='#dcdcdc')
CM = {0: 'dark', 1: 'mid', 2: 'light'}
CMF = {0: 'far', 1: 'dark', 2: 'mid'}
C = lambda pts: [R.units(x + 416, y) for x, y in pts]

def path(layer, tone, subs):
    return '<path style="fill:%s;fill-opacity:1;stroke:none" d="%s" inkscape:label="%s-shade-%s"/>' % (TONE[tone], PU.to_d(subs if isinstance(subs, list) else [subs], 2), layer, tone)

def ring_path(layer, tone, subs):
    return '<path style="fill:%s;fill-opacity:1;fill-rule:evenodd;stroke:none" d="%s" inkscape:label="%s-shade-%s"/>' % (TONE[tone], PU.to_d(subs, 2), layer, tone)

def shapes(layer, mask, cmap, tol=0.1, min_tone=0.4):
    out = []
    parts = R.tone_partition(mask, min_area=min_tone, overlap=0.1)
    for k in sorted(parts, key=lambda k: -parts[k].sum()):
        for pts, cor in R.paths(parts[k], tol=tol, min_area=0.1)[:10]:
            out.append(path(layer, cmap[k], PU.spline(pts, True, cor)))
    return out

def build(shift_far_ear=(-2.4, -0.3)):
    HEAD = C([(120, 470), (440, 470), (480, 500), (480, 640), (440, 690), (380, 712), (120, 740)])
    EAR = C([(425, 395), (592, 395), (592, 470), (560, 530), (500, 552), (425, 570)])
    ANT = C([(150, 20), (850, 20), (850, 500), (150, 500)])
    out = {}
    m_head = R.part_mask([HEAD], (), 0.2)
    head = shapes('head', m_head, {0: 'dark', 1: 'mid', 2: 'mid'})     # no light region in the head: a throat fragment would show as a stray bar
    for poly, tone in (([(305, 548), (390, 548), (390, 610), (305, 610)], 'eye'), ([(135, 625), (205, 625), (205, 695), (135, 695)], 'nose')):
        for bm in R.dark_blobs(R.part_mask([C(poly)], (), 0.0), lum_max=60, open_units=0.12, min_area=0.15):
            for pts, cor in R.paths(bm, tol=0.06, min_area=0.1, sigma=1.4)[:1]:
                head.append(path('head', tone, PU.spline(pts, True, cor)))
    out['head'] = head
    ear_mask = R.part_mask([EAR], (), 0.2)
    out['ear-l'] = shapes('ear-l', ear_mask, CM)
    # far ear: same shapes, one tone step darker, nudged forward
    far = []
    parts = R.tone_partition(ear_mask, min_area=0.4, overlap=0.1)
    for k in sorted(parts, key=lambda k: -parts[k].sum()):
        for pts, cor in R.paths(parts[k], tol=0.1, min_area=0.1)[:10]:
            sub = PU.translate([PU.spline(pts, True, cor)], shift_far_ear[0], shift_far_ear[1])
            far.append(path('ear-r', CMF[k], sub))
    out['ear-r'] = far
    from scipy import ndimage as ndi
    am_raw = R.part_mask([ANT], (), 0.25, holes=True)                 # silhouette WITHOUT filling the gaps between tines
    cream = ndi.binary_opening(am_raw & (R.lum > 140), iterations=2)
    lab, n = ndi.label(cream)
    ant = []
    pieces = []
    for i in range(1, n + 1):
        if (lab == i).sum() < 300:
            continue
        cx = np.nonzero(lab == i)[1].mean() - 416
        pieces.append((0 if cx > 500 else 1, i, 'bone' if cx > 500 else 'mid'))     # the big right antler is in front
    # draw the pieces behind first (mid), the front antler (bone) last
    for _, i, tone in sorted(pieces, key=lambda p: -p[0]):
        m = ndi.binary_dilation(lab == i, iterations=5) & am_raw       # fill + half the outline stroke = outline centre line
        for pts, cor in R.paths(m, tol=0.08, min_area=0.1, sigma=1.6)[:3]:
            ant.append(path('antlers', tone, PU.spline(pts, True, cor)))
    out['antlers'] = ant
    out['pivots'] = {'ear-l': C([(500, 545)])[0], 'ear-r': (C([(500, 545)])[0][0] + shift_far_ear[0], C([(500, 545)])[0][1] + shift_far_ear[1]), 'antlers': C([(400, 485)])[0]}
    return out
