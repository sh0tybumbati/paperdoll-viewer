#!/usr/bin/env python3
"""Normalize a layered paperdoll SVG: rebuild pivots from a hierarchy spec,
rename shade paths to <layer>-<tone>, and snap fills to neutral grey.

usage: normalize.py in.svg hierarchy.json out.svg
hierarchy.json: {"pivots": {"<child-layer>": {"parent": "<parent-layer>", "x": 1.0, "y": 2.0}}}
Each pivot is written twice at the same point: "<child>-pivot" in the parent
layer, "<parent>-pivot" in the child layer.
"""
import json, re, sys
import xml.etree.ElementTree as ET

NS = {'': 'http://www.w3.org/2000/svg',
      'inkscape': 'http://www.inkscape.org/namespaces/inkscape',
      'sodipodi': 'http://sodipodi.sourceforge.net/DTD/sodipodi-0.dtd',
      'xlink': 'http://www.w3.org/1999/xlink'}
for k, v in NS.items():
    ET.register_namespace(k, v)
SVG = '{%s}' % NS['']
IL = '{%s}label' % NS['inkscape']
GM = '{%s}groupmode' % NS['inkscape']
TONES = ('dark', 'light', 'hoof', 'far', 'mid', 'nose', 'eye', 'bone')
PIVOT_STYLE = ('display:inline;fill:none;stroke:#ff0000;stroke-width:0.1;'
               'stroke-linecap:round;stroke-opacity:1')


def snap(m):
    h = m.group(1)
    if len(h) == 3:
        h = ''.join(c * 2 for c in h)
    r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
    v = round((r + g + b) / 3)
    return 'fill:#%02x%02x%02x' % (v, v, v)


def main(src, spec_path, out):
    tree = ET.parse(src)
    root = tree.getroot()
    spec = json.load(open(spec_path))['pivots']
    layers = {l.get(IL): l for l in root if l.get(GM) == 'layer'}
    for name, layer in layers.items():
        for e in list(layer):
            lab = e.get(IL) or ''
            if lab.endswith('-pivot'):
                layer.remove(e)
                continue
            st = e.get('style')
            if st:
                e.set('style', re.sub(r'fill:#([0-9a-fA-F]{6}|[0-9a-fA-F]{3})\b', snap, st))
            for t in TONES:
                if lab.endswith('-shade-' + t) or lab == t:
                    e.set(IL, '%s-shade-%s' % (name, t))
    n = 0
    for child, p in spec.items():
        for host, label in ((p['parent'], child + '-pivot'), (child, p['parent'] + '-pivot')):
            if host not in layers:
                sys.exit('layer missing: ' + host)
            el = ET.SubElement(layers[host], SVG + 'ellipse', {
                'style': PIVOT_STYLE, 'cx': str(p['x']), 'cy': str(p['y']),
                'rx': '0.343', 'ry': '0.343', IL: label,
                'id': 'pivot-%s-in-%s' % (child, host)})
            n += 1
    tree.write(out, xml_declaration=True, encoding='UTF-8')
    print('wrote %s (%d pivots)' % (out, n))


if __name__ == '__main__':
    if len(sys.argv) != 4:
        sys.exit(__doc__)
    main(*sys.argv[1:])
