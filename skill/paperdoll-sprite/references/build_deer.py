"""Deer with the head, ears and antlers from the Epochs stag. The rest of the deer (body, neck, legs, tail) is the
skill's reference deer shifted down DY so the tall antlers fit; canvas grows from 64x64 to 64x73."""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))        # builds are relocatable: everything is found relative to this file
SRC = os.path.join(HERE, 'sources')
sys.path.insert(0, os.path.join(HERE, '..', 'scripts')); sys.path.insert(0, HERE)
import json, sys

import xml.etree.ElementTree as ET
import pathutil as PU
import deer_head_epochs as D

DY = D.DY
SK = HERE + '/'
IL = '{http://www.inkscape.org/namespaces/inkscape}label'; GM = '{http://www.inkscape.org/namespaces/inkscape}groupmode'
root = ET.parse(os.path.join(SRC, 'deer_orig_fixed.svg')).getroot()
layers = {}
for l in root:
    if l.get(GM) != 'layer':
        continue
    n = l.get(IL); shapes = []
    for e in l:
        lab = e.get(IL) or ''
        if lab.endswith('-pivot'):
            continue
        tag = e.tag.split('}')[1]
        if tag == 'path':
            subs = PU.translate(PU.shape_subs(e), 0, DY)
            if n == 'neck':     # trim the old neck's top so it starts under the new head (no bow-tie, no spike)
                cut = {'light': 32.4}.get(lab.rsplit('-', 1)[-1])
                if cut:
                    big = max(subs, key=lambda q: (lambda b: (b[2] - b[0]) * (b[3] - b[1]))(PU.bbox([q])))
                    subs = [PU.split_y(big, cut)[1]]
            d = PU.to_d(subs, 2)
            shapes.append('<path style="%s" d="%s" inkscape:label="%s"/>' % (e.get('style'), d, lab))
        elif tag == 'ellipse':
            shapes.append('<ellipse style="%s" cx="%s" cy="%.3f" rx="%s" ry="%s" inkscape:label="%s"/>' % (e.get('style'), e.get('cx'), float(e.get('cy')) + DY, e.get('rx'), e.get('ry'), lab))
    layers[n] = shapes
o = D.build()
for k in ('head', 'ear-l', 'ear-r', 'antlers'):
    layers[k] = o[k]
order = ['shadow','tail','leg-br-u','leg-br-l','leg-fr-u','leg-fr-l','body','neck','leg-bl-u','leg-bl-l','leg-fl-u','leg-fl-l','ear-r','head','ear-l','antlers']
W, H = 64, 64 + int(DY)
out = ['<?xml version="1.0" encoding="UTF-8" standalone="no"?>',
       '<svg width="%d" height="%d" viewBox="0 0 %d %d" version="1.1" xmlns:inkscape="http://www.inkscape.org/namespaces/inkscape" xmlns="http://www.w3.org/2000/svg">' % (W, H, W, H)]
for i, n in enumerate(order):
    out.append('<g inkscape:groupmode="layer" id="layer%d" inkscape:label="%s" style="display:inline">' % (i, n)); out += layers[n]; out.append('</g>')
out.append('</svg>')
open('deer2_raw.svg', 'w').write('\n'.join(out))
h = json.load(open(os.path.join(SRC, 'deer_orig.hierarchy.json')))['pivots']
for k, v in h.items():
    v['y'] = round(v['y'] + DY, 3)
h['ear-l'] = dict(parent='head', x=round(o['pivots']['ear-l'][0], 2), y=round(o['pivots']['ear-l'][1], 2))
h['ear-r'] = dict(parent='head', x=round(o['pivots']['ear-r'][0], 2), y=round(o['pivots']['ear-r'][1], 2))
h['antlers'] = dict(parent='head', x=round(o['pivots']['antlers'][0], 2), y=round(o['pivots']['antlers'][1], 2))
json.dump({'pivots': h}, open('deer2.hierarchy.json', 'w'), indent=1)
print('ok', W, H)
