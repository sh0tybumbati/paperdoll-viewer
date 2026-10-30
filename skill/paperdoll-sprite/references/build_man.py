"""Male human paperdoll from the Epochs sample (mirrored to face left). Traced: head (hair, beard, face), torso, loincloth
(own layer so it hangs over the legs), hand and foot. Rebuilt: arms and legs as ball-jointed capsules hanging straight
down (the sample is a stride pose, which cannot be a dead-side-on rest pose), left/right limbs identical, far side one
tone step darker. Same layer names as references/humanoid.svg."""
import os, sys, json
HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, 'sources') if os.path.isdir(os.path.join(HERE, 'sources')) else HERE
sys.path.insert(0, os.path.join(HERE, '..', 'scripts')); sys.path.insert(0, os.path.expanduser('~/.claude/skills/paperdoll-sprite/scripts')); sys.path.insert(0, HERE)
import numpy as np
from PIL import Image
from scipy import ndimage as ndi
import pathutil as PU, trace as T

W, H = 40, 64
IMG = os.path.join(SRC, 'man_flip.png')
R = T.Ref(IMG, 0.04, -35.88, -0.2, line_lum=70, levels=[110, 150], class_sigma=7)         # 0 hair/beard, 1 leaf, 2 skin
TONE = dict(eye='#0b0b0b', hoof='#242424', nose='#484848', far='#636363', dark='#757575', mid='#b5b5b5', bone='#dbdbdb', light='#dcdcdc')
NEAR = {0: 'far', 1: 'light', 2: 'light'}          # shaded skin (class 1) is skin; the leaf class is only used in the cloth layer
CLOTH = {0: 'far', 1: 'dark', 2: 'mid'}
LEGSKIN = 'mid'          # legs share the torso's step so the (lighter) hands read against them
LEGMAP = {0: 'far', 1: 'mid', 2: 'mid'}
TORSO = {0: 'far', 1: 'mid', 2: 'mid'}              # torso one step darker than limbs/head so the near arm reads against it
SHIFT = {'light': 'mid', 'dark': 'far', 'far': 'nose', 'mid': 'dark', 'hoof': 'nose', 'nose': 'nose'}
layers, hier = {}, {}

def path(layer, tone, subs):
    return '<path style="fill:%s;fill-opacity:1;stroke:none" d="%s" inkscape:label="%s-shade-%s"/>' % (TONE[tone], PU.to_d(subs if isinstance(subs, list) else [subs], 2), layer, tone)

def spl(pts, corners):
    return PU.spline(pts, True, corners)

def part_shapes(layer, mask, cmap=NEAR, tol=0.1, blobs=None, min_tone=0.5, open_px=3, shift=None, dx=0.0, dy=0.0):
    parts = R.tone_partition(mask, min_area=min_tone, open_px=open_px)
    out = []
    for k in sorted(parts, key=lambda k: -parts[k].sum()):
        tone = cmap[k] if not shift else SHIFT[cmap[k]]
        for pts, cor in R.paths(parts[k], tol=tol, min_area=0.1)[:8]:
            out.append(path(layer, tone, PU.translate([spl(pts, cor)], dx, dy)))
    for zone in (blobs or ()):
        for bm in R.dark_blobs(mask & R.poly_mask([zone]), lum_max=62, open_units=0.1, min_area=0.05):
            for pts, cor in R.paths(bm, tol=0.05, min_area=0.04, sigma=1.2)[:1]:
                out.append(path(layer, 'eye', PU.translate([spl(pts, cor)], dx, dy)))
    return out

M = lambda poly, grow=0.35: R.part_mask([poly], (), grow)

# cloth: leaf + vine are the only green pixels
rgb = np.array(Image.open(IMG).convert('RGB')).astype(int)
green = (rgb[..., 1] - rgb[..., 0] > 8) & R.fg
green = ndi.binary_opening(green, iterations=2)
lab, n = ndi.label(ndi.binary_dilation(green, iterations=8))
big = [i for i in range(1, n + 1) if (lab == i).sum() > 2500]
cloth = ndi.binary_dilation(green & np.isin(lab, big), iterations=7) & R.fg

# ---------- joints (sprite units) ----------
HIP, KNEE, ANKLE = (20.6, 34.0), (20.6, 46.2), (20.6, 56.2)
SHO, ELB, WRI = (21.5, 20.4), (21.6, 27.8), (21.4, 34.4)
NECKB, HEADB = (21.0, 17.8), (21.4, 13.9)
SKIN = 'light'

def limb(side, far):
    sh = (lambda t: SHIFT[t]) if far else (lambda t: t)
    L = lambda base: base + '-' + side
    layers['leg-%s-u' % side] = [path('leg-%s-u' % side, sh(LEGSKIN), PU.capsule(HIP, KNEE, 3.7, 2.9))]
    layers['leg-%s-l' % side] = [path('leg-%s-l' % side, sh(LEGSKIN), PU.capsule(KNEE, ANKLE, 2.9, 1.9))]
    layers['arm-%s-u' % side] = [path('arm-%s-u' % side, sh(SKIN), PU.capsule(SHO, ELB, 2.8, 2.4))]
    layers['arm-%s-l' % side] = [path('arm-%s-l' % side, sh(SKIN), PU.capsule(ELB, WRI, 2.4, 1.8))]
    # foot and hand traced from the sample (the leading foot, the leading hand), re-placed on the joint
    foot = R.part_mask([[(8.2, 55.2), (17.8, 55.2), (17.8, 59.6), (8.2, 59.6)]], (), 0.0)
    layers['leg-%s-l' % side] += part_shapes('leg-%s-l' % side, foot, LEGMAP, min_tone=0.3, shift=far, dx=ANKLE[0] - 15.9, dy=ANKLE[1] - 56.0)
    hand = R.part_mask([[(9.4, 33.0), (14.8, 33.0), (14.8, 39.8), (9.4, 39.8)]], (), 0.0)
    for pts, cor in R.paths(hand, tol=0.05, min_area=0.3, sigma=1.6)[:1]:        # whole-hand silhouette in one shape (tone tiling shredded it)
        layers['arm-%s-l' % side].append(path('arm-%s-l' % side, sh(SKIN), PU.translate([spl(pts, cor)], WRI[0] - 11.8, WRI[1] - 34.4)))
    hier['leg-%s-u' % side] = ('body',) + HIP
    hier['leg-%s-l' % side] = ('leg-%s-u' % side,) + KNEE
    hier['arm-%s-u' % side] = ('body',) + SHO
    hier['arm-%s-l' % side] = ('arm-%s-u' % side,) + ELB

limb('l', False)
limb('r', True)

layers['shadow'] = ['<ellipse style="fill:#000000;fill-opacity:0.4;stroke:none" cx="20.5" cy="58.8" rx="11" ry="1.6" inkscape:label="shadow"/>']
BODY = [(17.2, 15.4), (26.6, 15.4), (26.8, 22), (26.2, 30), (25.8, 34.2), (17.2, 34.2), (17.0, 30), (16.8, 22)]      # side-on torso width: the 3/4 drawing is much wider and drags the sample's own arm masses in
TORSO_PTS = [(17.9, 16.8), (20.0, 15.5), (23.4, 15.4), (25.6, 16.6), (26.5, 19.8), (26.4, 25.0), (25.7, 30.0), (25.9, 34.9), (17.4, 34.9), (17.3, 30.0), (17.2, 24.0), (17.2, 19.6)]
layers['body'] = [path('body', 'mid', spl(TORSO_PTS, ()))]       # drawn: the traced torso kept the sample's arm masses and a ragged top
layers['neck'] = [path('neck', SKIN, PU.capsule(NECKB, HEADB, 2.2, 1.9))]; hier['neck'] = ('body',) + NECKB
HEAD = [(14.4, 2), (27.2, 2), (27.2, 12.8), (25.5, 13.5), (23.6, 14.1), (18.8, 14.1), (16.0, 14.0), (14.6, 13.2)]      # stops at the beard line; a lower box drags a collar of shoulder skin into the head
layers['head'] = part_shapes('head', M(HEAD, 0.3), blobs=[[(16.5, 7.6), (21.0, 7.6), (21.0, 9.8), (16.5, 9.8)]], min_tone=0.3, open_px=2, tol=0.08)
for a, b in (((17.9, 8.6), (17.5, 9.9)), ((17.5, 9.9), (17.25, 10.4)), ((17.25, 10.4), (17.4, 10.75)), ((17.4, 10.75), (18.2, 10.85)), ((18.2, 10.85), (18.85, 10.7)), ((17.3, 11.95), (19.1, 11.95))):
    layers['head'].append(path('head', 'far', PU.capsule(a, b, 0.11, 0.11, arc=4)))      # nose line and mouth
hier['head'] = ('neck',) + HEADB

order = ['shadow', 'arm-r-u', 'arm-r-l', 'leg-r-u', 'leg-r-l', 'body', 'neck', 'head', 'leg-l-u', 'leg-l-l', 'arm-l-u', 'arm-l-l']
out = ['<?xml version="1.0" encoding="UTF-8" standalone="no"?>',
       '<svg width="%d" height="%d" viewBox="0 0 %d %d" version="1.1" xmlns:inkscape="http://www.inkscape.org/namespaces/inkscape" xmlns="http://www.w3.org/2000/svg">' % (W, H, W, H)]
for i, name in enumerate(order):
    out.append('<g inkscape:groupmode="layer" id="layer%d" inkscape:label="%s" style="display:inline">' % (i, name))
    out += layers[name]; out.append('</g>')
out.append('</svg>')
open('man_raw.svg', 'w').write('\n'.join(out))
json.dump({'pivots': {k: dict(parent=p, x=x, y=y) for k, (p, x, y) in hier.items()}}, open('man.hierarchy.json', 'w'), indent=1)
print('shapes per layer:', {k: len(v) for k, v in layers.items()})
