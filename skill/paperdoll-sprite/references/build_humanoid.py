"""Humanoid paperdoll (side view, facing left) built procedurally: every limb segment is a tapered capsule whose round
caps sit exactly on the joint pivots (ball joints by construction), left/right limbs are identical copies (dead
side-on), far-side limbs are one tone step darker. A template for non-quadrupeds: copy it, move the joint
coordinates, swap the torso/head splines. Writes humanoid_raw.svg + humanoid.hierarchy.json in the current directory;
then run scripts/normalize.py and scripts/validate.py --size 40x64."""
import os, sys, json
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'scripts'))
import pathutil as PU

W, H = 40, 64
TONE = dict(eye='#0b0b0b', hoof='#242424', nose='#484848', far='#636363', dark='#757575', mid='#b5b5b5', bone='#dbdbdb', light='#dcdcdc')
SHIFT = {'hoof': 'nose', 'dark': 'far', 'mid': 'dark', 'light': 'mid', 'far': 'far'}      # far-side limbs: one step darker

# joints (x, y): hip, knee, ankle, shoulder, elbow, wrist, neck base, head base
HIP, KNEE, ANKLE = (20.0, 34.5), (20.3, 46.8), (20.0, 57.2)
SHO, ELB, WRI = (20.5, 19.5), (21.8, 28.4), (21.0, 36.0)
NECKB, HEADB = (20.2, 16.8), (20.4, 13.4)

def shape(layer, tone, subs):
    return '<path style="fill:%s;fill-opacity:1;stroke:none" d="%s" inkscape:label="%s-shade-%s"/>' % (TONE[tone], PU.to_d(subs if isinstance(subs, list) else [subs], 2), layer, tone)

def blob(layer, tone, pts, corners=()):
    return shape(layer, tone, PU.spline(pts, True, corners))

layers, hier = {}, {}

def limb(prefix, far):
    t = (lambda k: SHIFT[k]) if far else (lambda k: k)
    # legs: trousers + shoe; arms: sleeve + bare forearm and hand
    layers[prefix.replace('X', 'leg') + '-u'] = [shape(prefix.replace('X', 'leg') + '-u', t('dark'), PU.capsule(HIP, KNEE, 3.9, 3.1))]
    layers[prefix.replace('X', 'leg') + '-l'] = [shape(prefix.replace('X', 'leg') + '-l', t('dark'), PU.capsule(KNEE, ANKLE, 3.1, 2.2)),
        blob(prefix.replace('X', 'leg') + '-l', t('hoof'), [(17.8, 56.4), (22.4, 56.4), (23.0, 59.2), (14.0, 59.8), (13.6, 58.4), (16.0, 57.6)], (2, 3))]
    layers[prefix.replace('X', 'arm') + '-u'] = [shape(prefix.replace('X', 'arm') + '-u', t('mid'), PU.capsule(SHO, ELB, 2.9, 2.4))]
    layers[prefix.replace('X', 'arm') + '-l'] = [shape(prefix.replace('X', 'arm') + '-l', t('light'), PU.capsule(ELB, WRI, 2.4, 1.8)),
        blob(prefix.replace('X', 'arm') + '-l', t('light'), [(19.2, 36.6), (21.0, 35.4), (22.8, 36.6), (23.0, 38.8), (21.0, 40.0), (19.2, 38.8)])]
    for seg, par, p in (('leg-%s-u', 'body', HIP), ('leg-%s-l', None, KNEE), ('arm-%s-u', 'body', SHO), ('arm-%s-l', None, ELB)):
        pass

for side, far in (('l', False), ('r', True)):
    pre = 'X-%s' % side
    limb(pre, far)
    hier['leg-%s-u' % side] = ('body',) + HIP
    hier['leg-%s-l' % side] = ('leg-%s-u' % side,) + KNEE
    hier['arm-%s-u' % side] = ('body',) + SHO
    hier['arm-%s-l' % side] = ('arm-%s-u' % side,) + ELB

layers['shadow'] = ['<ellipse style="fill:#000000;fill-opacity:0.4;stroke:none" cx="20" cy="59.7" rx="11" ry="1.6" inkscape:label="shadow"/>']
layers['body'] = [
    blob('body', 'mid', [(15.8, 17.0), (19.0, 15.2), (23.0, 15.6), (25.0, 18.0), (25.6, 25.0), (24.8, 32.0), (25.0, 36.0), (16.0, 36.0), (15.2, 31.0), (15.6, 25.0), (15.0, 21.0)]),
    blob('body', 'dark', [(15.2, 34.6), (25.4, 34.6), (25.6, 38.2), (24.4, 40.2), (16.0, 40.2), (15.0, 38.0)])]
layers['neck'] = [shape('neck', 'light', PU.capsule(NECKB, HEADB, 2.2, 1.9))]; hier['neck'] = ('body',) + NECKB
layers['head'] = [
    blob('head', 'light', [(16.8, 4.6), (19.5, 2.6), (23.0, 2.6), (25.6, 4.8), (26.2, 8.0), (25.0, 11.4), (22.5, 13.6), (19.5, 14.0), (17.4, 13.0), (16.2, 11.6), (15.5, 10.6), (15.3, 9.6), (14.4, 8.8), (15.4, 7.6), (15.6, 6.2)], (12,)),
    blob('head', 'far', [(16.6, 5.0), (19.5, 2.2), (23.5, 2.0), (26.6, 4.6), (26.8, 9.6), (25.6, 12.2), (24.2, 9.0), (22.5, 6.2), (19.5, 5.0)]),
    '<ellipse style="fill:#0b0b0b;fill-opacity:1;stroke:none" cx="17.6" cy="7.6" rx="0.55" ry="0.45" inkscape:label="head-shade-eye"/>']
hier['head'] = ('neck',) + HEADB

order = ['shadow', 'arm-r-u', 'arm-r-l', 'leg-r-u', 'leg-r-l', 'body', 'neck', 'head', 'leg-l-u', 'leg-l-l', 'arm-l-u', 'arm-l-l']
out = ['<?xml version="1.0" encoding="UTF-8" standalone="no"?>',
       '<svg width="%d" height="%d" viewBox="0 0 %d %d" version="1.1" xmlns:inkscape="http://www.inkscape.org/namespaces/inkscape" xmlns="http://www.w3.org/2000/svg">' % (W, H, W, H)]
for i, n in enumerate(order):
    out.append('<g inkscape:groupmode="layer" id="layer%d" inkscape:label="%s" style="display:inline">' % (i, n)); out += layers[n]; out.append('</g>')
out.append('</svg>')
open('humanoid_raw.svg', 'w').write('\n'.join(out))
json.dump({'pivots': {k: dict(parent=p, x=x, y=y) for k, (p, x, y) in hier.items()}}, open('humanoid.hierarchy.json', 'w'), indent=1)
print('ok')
