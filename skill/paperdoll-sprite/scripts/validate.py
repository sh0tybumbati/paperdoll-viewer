#!/usr/bin/env python3
"""Validate a paperdoll sprite SVG. usage: validate.py sprite.svg [--size 64 | --size 76x66]
Checks: canvas size, layers have labels, every pivot appears as a matched
pair (<child>-pivot in parent layer, <parent>-pivot in child layer, same
point), pivots lie within the canvas, all fills/strokes are neutral grey,
no gradients/filters/images. Exit 1 on any error."""
import os, re, sys
import xml.etree.ElementTree as ET
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pathutil as PU

IL = '{http://www.inkscape.org/namespaces/inkscape}label'
GM = '{http://www.inkscape.org/namespaces/inkscape}groupmode'


def main():
    path = sys.argv[1]
    sz = sys.argv[sys.argv.index('--size') + 1] if '--size' in sys.argv else '64'
    sw, sh = (int(v) for v in (sz.split('x') if 'x' in sz else (sz, sz)))
    size = max(sw, sh)
    root = ET.parse(path).getroot()
    errs, warns = [], []
    w, h = root.get('width'), root.get('height')
    if (w, h) != (str(sw), str(sh)) or root.get('viewBox') != '0 0 %d %d' % (sw, sh):
        errs.append('canvas must be %dx%d with matching viewBox, got %s x %s %s' % (sw, sh, w, h, root.get('viewBox')))
    layers = [l for l in root if l.get(GM) == 'layer']
    names = [l.get(IL) for l in layers]
    if None in names or len(set(names)) != len(names):
        errs.append('layers need unique inkscape:label')
    piv = {}
    for l in layers:
        ln = l.get(IL)
        for e in l.iter():
            tag = e.tag.split('}')[1]
            if tag in ('image', 'filter', 'linearGradient', 'radialGradient'):
                errs.append('%s: %s not allowed' % (ln, tag))
            st = e.get('style', '')
            for kind, col in re.findall(r'(fill|stroke):(#[0-9a-fA-F]{3,6})', st):
                col = col.lstrip('#')
                if len(col) == 3:
                    col = ''.join(c * 2 for c in col)
                if not (col[0:2] == col[2:4] == col[4:6]) and not (kind == 'stroke' and col.lower() == 'ff0000'):
                    errs.append('%s/%s: non-grey %s #%s' % (ln, e.get(IL), kind, col))
            lab = e.get(IL) or ''
            if lab.endswith('-pivot') and tag == 'ellipse':
                pt = (float(e.get('cx')), float(e.get('cy')))
                if not (0 <= pt[0] <= sw and 0 <= pt[1] <= sh):
                    errs.append('%s/%s: pivot off canvas %s' % (ln, lab, pt))
                piv[(ln, lab[:-6])] = pt
    for (host, other), pt in piv.items():
        mate = piv.get((other, host))
        if mate is None:
            errs.append('pivot %s-pivot in %s has no mate "%s-pivot" in %s' % (other, host, host, other))
        elif abs(mate[0] - pt[0]) > 0.05 or abs(mate[1] - pt[1]) > 0.05:
            errs.append('pivot pair %s<->%s differs: %s vs %s' % (host, other, pt, mate))
    for l in layers:
        if l.get(IL) not in ('shadow',) and not any((e.get(IL) or '').endswith('-pivot') for e in l) and l.get(IL) != 'body':
            warns.append('layer %s has no pivot' % l.get(IL))
    # limb joints: each segment needs a round cap past the pivot, and the upper must not run on past it (duplicate limb)
    by = {l.get(IL): l for l in layers}
    def span(layer):
        ys = []
        for e in layer.iter('{http://www.w3.org/2000/svg}path'):
            try:
                b = PU.bbox(PU.shape_subs(e)); ys += [b[1], b[3]]
            except Exception:
                pass
        return (min(ys), max(ys)) if ys else None
    for n, up in by.items():
        m = re.match(r'^((?:leg|arm)-(?:[fb])?[lr])-u$', n or '')
        if not m or m.group(1) + '-l' not in by:
            continue
        pv = piv.get((n, m.group(1) + '-l'))
        su, sl = span(up), span(by[m.group(1) + '-l'])
        if not (pv and su and sl):
            continue
        h = su[1] - su[0]
        if su[1] - pv[1] < 0.5:
            warns.append('%s: no cap below the joint (ends %.1f past the pivot); round it so the limb never opens when bent' % (n, su[1] - pv[1]))
        elif su[1] - pv[1] > max(5.0, 0.35 * h):
            errs.append('%s runs %.1f past its joint (looks like a whole limb): it will show as a second leg when the lower segment moves' % (n, su[1] - pv[1]))
        if pv[1] - sl[0] < 0.5:
            warns.append('%s-l: no cap above the joint (starts %.1f above the pivot)' % (m.group(1), pv[1] - sl[0]))
    # dead side-on: left and right legs must be the same shape with the same pivots
    def box(layer):
        pts = []
        for e in layer.iter('{http://www.w3.org/2000/svg}path'):
            try:
                pts.append(PU.bbox(PU.shape_subs(e)))
            except Exception:
                pass
        return (min(p[0] for p in pts), min(p[1] for p in pts), max(p[2] for p in pts), max(p[3] for p in pts)) if pts else None
    pairs = [('leg-%sl' % fb, 'leg-%sr' % fb) for fb in ('f', 'b')] + [('leg-l', 'leg-r'), ('arm-l', 'arm-r')]
    for left, right in pairs:
        for seg in ('u', 'l'):
            a, b = by.get('%s-%s' % (left, seg)), by.get('%s-%s' % (right, seg))
            if a is None or b is None:
                continue
            ba, bb = box(a), box(b)
            if ba and bb and max(abs(x - y) for x, y in zip(ba, bb)) > 0.3:
                errs.append('%s-%s and %s-%s differ in shape/position: left/right limbs must be identical copies (dead side-on)' % (left, seg, right, seg))
            pa = sorted(v for (h, o), v in piv.items() if h == a.get(IL))
            pb = sorted(v for (h, o), v in piv.items() if h == b.get(IL))
            if not (len(pa) == len(pb) and all(abs(x[0] - y[0]) < 0.3 and abs(x[1] - y[1]) < 0.3 for x, y in zip(pa, pb))):
                errs.append('%s-%s and %s-%s have different pivots' % (left, seg, right, seg))
    for m in warns:
        print('WARN', m)
    for m in errs:
        print('ERROR', m)
    print('%d layers, %d pivots, %d errors' % (len(layers), len(piv), len(errs)))
    sys.exit(1 if errs else 0)


main()
