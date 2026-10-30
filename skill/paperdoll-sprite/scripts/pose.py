#!/usr/bin/env python3
"""Pose a rigged sprite to prove the pivots work. usage:
  pose.py sprite.svg hierarchy.json out.png layer=deg [layer=deg ...] [--scale 10] [--solo layerA,layerB]
Rotates each named layer about its own pivot (the "<parent>-pivot" inside it); descendants follow.
Positive degrees = clockwise. Example: pose.py boar.svg boar.hierarchy.json p.png leg-fl-u=-25 leg-fl-l=20 head=8"""
import json, subprocess, sys, tempfile, os
import xml.etree.ElementTree as ET
a = sys.argv[1:]
src, hj, out = a[0], a[1], a[2]
angles = {k: float(v) for k, v in (x.split('=') for x in a[3:] if '=' in x and not x.startswith('--'))}
solo = set(a[a.index('--solo') + 1].split(',')) if '--solo' in a else set()
scale = float(a[a.index('--scale') + 1]) if '--scale' in a else 10
hier = json.load(open(hj))['pivots']
IL = '{http://www.inkscape.org/namespaces/inkscape}label'; GM = '{http://www.inkscape.org/namespaces/inkscape}groupmode'
ET.register_namespace('', 'http://www.w3.org/2000/svg')
ET.register_namespace('inkscape', 'http://www.inkscape.org/namespaces/inkscape')
root = ET.parse(src).getroot()
def chain(n):
    c = []
    while n in hier:
        c.append(n); n = hier[n]['parent']
    return c[::-1]
for l in root:
    if l.get(GM) != 'layer':
        continue
    n = l.get(IL)
    if solo and n not in solo:
        l.set('style', 'display:none')
    t = ''
    for anc in chain(n):
        if angles.get(anc):
            p = hier[anc]
            t += 'rotate(%g %g %g) ' % (angles[anc], p['x'], p['y'])
    if t:
        l.set('transform', t.strip())
    for e in list(l):
        if (e.get(IL) or '').endswith('-pivot'):
            l.remove(e)
tmp = os.path.join(tempfile.mkdtemp(), 'p.svg'); ET.ElementTree(root).write(tmp)
subprocess.run(['rsvg-convert', '-z', str(scale), '-b', 'white', tmp, '-o', out], check=True)
print(out)
