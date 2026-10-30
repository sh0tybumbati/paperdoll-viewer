"""Boar head, ears, tusks, eye and brow extracted from the Epochs boar sample (mirrored to face left).
Returns SVG shape strings in the boar's frame coordinates (+OFF in x), plus ear pivots."""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))        # builds are relocatable: everything is found relative to this file
SRC = os.path.join(HERE, 'sources')
sys.path.insert(0, os.path.join(HERE, '..', 'scripts')); sys.path.insert(0, HERE)
import sys

import numpy as np
import pathutil as PU, trace as T

S = 0.049
OX, OY = 5 - (540 + 416) * S, 38 - (470 + 250) * S       # crop (540,470) = head pivot (5, 38)
R = T.Ref(os.path.join(SRC, 'boar_flip.png'), S, OX, OY, line_lum=52, levels=[48, 85, 170], thick_px=14)
TONE = dict(eye='#0b0b0b', nose='#484848', far='#636363', dark='#757575', mid='#b5b5b5', bone='#dbdbdb', light='#dcdcdc')
HEAD_C = {0: 'eye', 1: 'far', 2: 'dark', 3: 'bone'}
EAR_C = {0: 'nose', 1: 'far', 2: 'dark', 3: 'bone'}
C = lambda pts: [R.units(x + 416, y + 250) for x, y in pts]          # crop px -> sprite units

def build(OFF, wp=None):
    def path(layer, tone, subs):
        subs = PU.translate(subs if isinstance(subs, list) else [subs], OFF, 0)
        return '<path style="fill:%s;fill-opacity:1;stroke:none" d="%s" inkscape:label="%s-shade-%s"/>' % (TONE[tone], PU.to_d(subs, 2), layer, tone)
    def shapes(layer, mask, cmap, tol=0.12, min_tone=0.5):
        out = []
        parts = R.tone_partition(mask, min_area=min_tone, overlap=0.1)
        for k in sorted(parts, key=lambda k: -parts[k].sum()):
            for pts, cor in R.paths(parts[k], tol=tol, min_area=0.12)[:8]:
                out.append(path(layer, cmap[k], PU.spline(pts, True, cor)))
        return out
    HEAD = C([(40, 235), (385, 235), (385, 140), (440, 140), (440, 330), (600, 330), (600, 560), (580, 610), (520, 660), (450, 700), (380, 745), (40, 745)])
    EARR = C([(280, 90), (400, 90), (400, 250), (280, 250)])
    EARL = C([(425, 70), (610, 70), (610, 345), (425, 345)])
    m_head = R.part_mask([HEAD], (), 0.2)
    out = {}
    out['ear-r'] = shapes('ear-r', R.part_mask([EARR], (), 0.2), EAR_C)
    out['ear-l'] = shapes('ear-l', R.part_mask([EARL], (), 0.2), EAR_C)
    head = shapes('head', m_head, HEAD_C)
    # brow arc (thin stroke in the sample): drawn from measurements
    head.append(path('head', 'nose', PU.spline(C([(330, 392), (342, 376), (360, 364), (382, 360), (402, 366), (416, 380), (404, 378), (390, 372), (372, 372), (356, 382), (344, 396)]), True, (0, 5))))
    out['head'] = head
    out['pivots'] = {'ear-l': C([(505, 300)])[0], 'ear-r': C([(330, 225)])[0], 'pad': C([(126, 662)])[0]}
    return out
