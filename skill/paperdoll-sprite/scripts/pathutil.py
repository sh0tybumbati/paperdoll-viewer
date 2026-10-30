#!/usr/bin/env python3
"""SVG path toolkit for sprite geometry. Import or use as CLI.
  pathutil.py info FILE            per-shape node counts and bboxes (absolute coords, transforms applied)
  pathutil.py split D Y            split path data D at horizontal line y=Y -> prints upper and lower d
A subpath is {'segs': [('L',p0,p1)|('C',p0,c1,c2,p1)], 'closed': bool}; points are (x, y)."""
import math, re, sys

TOK = re.compile(r'([MmLlHhVvCcSsQqZzAa])|(-?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?)')


def parse(d):
    toks = [(m.group(1), m.group(2)) for m in TOK.finditer(d)]
    i, cmd, subs, cur, start, last_c = 0, None, [], None, None, None
    pos = (0.0, 0.0)

    def num():
        nonlocal i
        v = float(toks[i][1]); i += 1
        return v
    while i < len(toks):
        if toks[i][0]:
            cmd = toks[i][0]; i += 1
            if cmd in 'Zz':
                if cur is not None:
                    if pos != start:
                        cur['segs'].append(('L', pos, start))
                    cur['closed'] = True
                    pos = start
                continue
        rel = cmd.islower(); c = cmd.upper()
        ox, oy = pos if rel else (0.0, 0.0)
        if c == 'M':
            pos = (num() + ox, num() + oy); start = pos
            cur = {'segs': [], 'closed': False}; subs.append(cur)
            cmd = 'l' if rel else 'L'; last_c = None
        elif c == 'L':
            p = (num() + ox, num() + oy); cur['segs'].append(('L', pos, p)); pos = p; last_c = None
        elif c == 'H':
            p = (num() + ox, pos[1]); cur['segs'].append(('L', pos, p)); pos = p; last_c = None
        elif c == 'V':
            p = (pos[0], num() + oy); cur['segs'].append(('L', pos, p)); pos = p; last_c = None
        elif c == 'C':
            c1 = (num() + ox, num() + oy); c2 = (num() + ox, num() + oy); p = (num() + ox, num() + oy)
            cur['segs'].append(('C', pos, c1, c2, p)); pos = p; last_c = c2
        elif c == 'S':
            c1 = (2 * pos[0] - last_c[0], 2 * pos[1] - last_c[1]) if last_c else pos
            c2 = (num() + ox, num() + oy); p = (num() + ox, num() + oy)
            cur['segs'].append(('C', pos, c1, c2, p)); pos = p; last_c = c2
        elif c == 'Q':
            q = (num() + ox, num() + oy); p = (num() + ox, num() + oy)
            c1 = (pos[0] + 2 / 3 * (q[0] - pos[0]), pos[1] + 2 / 3 * (q[1] - pos[1]))
            c2 = (p[0] + 2 / 3 * (q[0] - p[0]), p[1] + 2 / 3 * (q[1] - p[1]))
            cur['segs'].append(('C', pos, c1, c2, p)); pos = p; last_c = None
        else:
            raise ValueError('unsupported command ' + cmd)
    return subs


def fmt(v, dec):
    s = ('%.*f' % (dec, v)).rstrip('0').rstrip('.')
    return '0' if s in ('-0', '') else s


def to_d(subs, dec=2):
    out = []
    for s in subs:
        if not s['segs']:
            continue
        p0 = s['segs'][0][1]
        out.append('M %s,%s' % (fmt(p0[0], dec), fmt(p0[1], dec)))
        for seg in s['segs']:
            if seg[0] == 'L':
                out.append('L %s,%s' % (fmt(seg[2][0], dec), fmt(seg[2][1], dec)))
            else:
                out.append('C ' + ' '.join('%s,%s' % (fmt(p[0], dec), fmt(p[1], dec)) for p in seg[2:]))
        if s['closed']:
            out.append('Z')
    return ' '.join(out)


def xform(subs, fn):
    return [{'closed': s['closed'], 'segs': [(sg[0],) + tuple(fn(p) for p in sg[1:]) for sg in s['segs']]} for s in subs]


def translate(subs, dx, dy):
    return xform(subs, lambda p: (p[0] + dx, p[1] + dy))


def apply_matrix(subs, m):
    a, b, c, d, e, f = m
    return xform(subs, lambda p: (a * p[0] + c * p[1] + e, b * p[0] + d * p[1] + f))


def parse_transform(t):
    """returns matrix (a,b,c,d,e,f) for translate/scale/rotate/matrix chains"""
    import math
    M = (1, 0, 0, 1, 0, 0)

    def mul(A, B):
        return (A[0]*B[0]+A[2]*B[1], A[1]*B[0]+A[3]*B[1], A[0]*B[2]+A[2]*B[3], A[1]*B[2]+A[3]*B[3],
                A[0]*B[4]+A[2]*B[5]+A[4], A[1]*B[4]+A[3]*B[5]+A[5])
    for name, args in re.findall(r'(\w+)\s*\(([^)]*)\)', t or ''):
        v = [float(x) for x in re.split(r'[,\s]+', args.strip()) if x]
        if name == 'translate':
            m = (1, 0, 0, 1, v[0], v[1] if len(v) > 1 else 0)
        elif name == 'scale':
            m = (v[0], 0, 0, v[-1], 0, 0)
        elif name == 'rotate':
            a = math.radians(v[0]); c, s = math.cos(a), math.sin(a)
            m = (c, s, -s, c, 0, 0)
            if len(v) == 3:
                m = mul(mul((1, 0, 0, 1, v[1], v[2]), m), (1, 0, 0, 1, -v[1], -v[2]))
        elif name == 'matrix':
            m = tuple(v)
        else:
            continue
        M = mul(M, m)
    return M


def bez(seg, t):
    if seg[0] == 'L':
        p0, p1 = seg[1], seg[2]
        return (p0[0] + (p1[0] - p0[0]) * t, p0[1] + (p1[1] - p0[1]) * t)
    p0, c1, c2, p1 = seg[1:]
    u = 1 - t
    return tuple(u**3 * p0[k] + 3 * u**2 * t * c1[k] + 3 * u * t**2 * c2[k] + t**3 * p1[k] for k in (0, 1))


def bbox(subs, n=24):
    pts = [bez(sg, i / n) for s in subs for sg in s['segs'] for i in range(n + 1)]
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]
    return min(xs), min(ys), max(xs), max(ys)


def nodes(subs):
    return sum(len(s['segs']) for s in subs)


def subdivide(seg, t):
    if seg[0] == 'L':
        m = bez(seg, t)
        return ('L', seg[1], m), ('L', m, seg[2])
    p0, c1, c2, p1 = seg[1:]
    L = lambda a, b: (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)
    a, b, c = L(p0, c1), L(c1, c2), L(c2, p1)
    d, e = L(a, b), L(b, c)
    f = L(d, e)
    return ('C', p0, a, d, f), ('C', f, e, c, p1)


def crossings(seg, y):
    out, prev, n = [], seg[1][1] - y, 48
    for i in range(1, n + 1):
        t1 = i / n; cur = bez(seg, t1)[1] - y
        if prev == 0 or prev * cur < 0:
            lo, hi = (i - 1) / n, t1
            for _ in range(40):
                mid = (lo + hi) / 2
                if (bez(seg, lo)[1] - y) * (bez(seg, mid)[1] - y) <= 0:
                    hi = mid
                else:
                    lo = mid
            out.append((lo + hi) / 2)
        prev = cur
    return [t for t in out if 1e-6 < t < 1 - 1e-6]


def split_y(sub, y):
    """split one closed subpath at y=const. Returns (upper, lower) subpaths (upper = smaller y).
    Curves are subdivided exactly (no flattening). Uses first and last crossing if more than two."""
    segs = []
    for sg in sub['segs']:
        ts = crossings(sg, y)
        prev_t, rest = 0.0, sg
        for t in ts:
            tt = (t - prev_t) / (1 - prev_t)
            a, rest = subdivide(rest, tt); segs.append(a); prev_t = t
        segs.append(rest)
    idx = [i for i, sg in enumerate(segs) if abs(sg[-1][1] - y) < 1e-6]
    if len(idx) < 2:
        raise ValueError('path does not cross y=%g twice' % y)
    a, b = idx[0], idx[-1]
    loop1 = segs[a + 1:b + 1]
    loop2 = segs[b + 1:] + segs[:a + 1]
    pa, pb = loop1[-1][-1], loop2[-1][-1]
    loop1.append(('L', pa, loop1[0][1])); loop2.append(('L', pb, loop2[0][1]))
    s1, s2 = {'segs': loop1, 'closed': True}, {'segs': loop2, 'closed': True}
    my = lambda s: sum(bez(sg, .5)[1] for sg in s['segs']) / len(s['segs'])
    return (s1, s2) if my(s1) < my(s2) else (s2, s1)


def spline(pts, closed=True, corners=(), k=1.0):
    """Catmull-Rom through pts -> cubic subpath. corners = indices that stay sharp (straight handles).
    Few well-placed points + a few corners is the intended way to draw a part: ~10-20 points per part."""
    n = len(pts)
    segs = []
    last = n if closed else n - 1
    P = lambda i: pts[i % n] if closed else pts[max(0, min(n - 1, i))]
    for i in range(last):
        p0, p1, p2, p3 = P(i - 1), P(i), P(i + 1), P(i + 2)
        if i % n in corners:
            c1 = (p1[0] + (p2[0] - p1[0]) / 3, p1[1] + (p2[1] - p1[1]) / 3)
        else:
            c1 = (p1[0] + (p2[0] - p0[0]) / 6 * k, p1[1] + (p2[1] - p0[1]) / 6 * k)
        if (i + 1) % n in corners:
            c2 = (p2[0] - (p2[0] - p1[0]) / 3, p2[1] - (p2[1] - p1[1]) / 3)
        else:
            c2 = (p2[0] - (p3[0] - p1[0]) / 6 * k, p2[1] - (p3[1] - p1[1]) / 6 * k)
        segs.append(('C', p1, c1, c2, p2))
    return {'segs': segs, 'closed': closed}


def capsule(p0, p1, r0, r1, arc=7):
    """Closed outline of a tapered limb segment from p0 (radius r0) to p1 (radius r1) with round caps centred exactly
    on the end points. Build ball-jointed limbs from these: the lower end of an upper segment and the top of the lower
    segment use the SAME centre and radius, so either half can rotate about the joint with no gap or notch."""
    dx, dy = p1[0] - p0[0], p1[1] - p0[1]
    n = math.hypot(dx, dy) or 1.0
    ux, uy = dx / n, dy / n
    nx, ny = -uy, ux
    pts = []
    base = math.atan2(ny, nx)
    for i in range(arc + 1):                               # cap around p1, sweeping from the +normal side to the -normal side
        a = base - math.pi * i / arc
        pts.append((p1[0] + r1 * math.cos(a), p1[1] + r1 * math.sin(a)))
    for i in range(arc + 1):                               # cap around p0
        a = base + math.pi - math.pi * i / arc
        pts.append((p0[0] + r0 * math.cos(a), p0[1] + r0 * math.sin(a)))
    return spline(pts, True, ())


def xs_at(sub, y):
    """x positions where the closed subpath crosses the horizontal line at y"""
    out = []
    for sg in sub['segs']:
        for t in crossings(sg, y):
            out.append(bez(sg, t)[0])
    return sorted(out)


def _cap_depth(full, cut, cx, hc, dirn, tol=0.25):
    """deepest round cap (semi-ellipse hc wide) that stays inside the limb outline on its side of the cut"""
    d = hc
    while d >= 0.4 * hc:
        ok = True
        for i in range(1, 9):
            t = d * i / 8.0
            w = hc * math.sqrt(max(0.0, 1 - (t / d) ** 2))
            xs = xs_at(full, cut + dirn * t)
            if len(xs) < 2 or xs[0] > cx - w + tol or xs[-1] < cx + w - tol:
                ok = False; break
        if ok:
            return d
        d *= 0.92
    return 0.4 * hc


def cap_split(sub, cut):
    """Split a limb outline at y=cut into (upper, lower) like split_y, but close each half with a round cap
    (semi-ellipse, half the limb width at the cut, centred on the joint) instead of a flat edge. This is the
    'ball joint': when either half rotates about (cx, cut) its cap turns inside the other half, so the silhouette
    never opens or notches. Returns (upper, lower, (cx, cut))."""
    if len(xs_at(sub, cut)) < 2:
        cut += 1e-3                                   # a node sits exactly on the cut line
    up, lo = split_y(sub, cut)
    xs = xs_at(sub, cut)
    cx, hc = (xs[0] + xs[-1]) / 2, (xs[-1] - xs[0]) / 2
    k = 0.5523
    res = []
    for part, dirn in ((up, 1), (lo, -1)):
        segs = part['segs'][:-1]                      # drop the flat chord
        S, E = part['segs'][-1][1], part['segs'][-1][2]
        d = _cap_depth(sub, cut, cx, hc, dirn)
        ss = 1 if S[0] > cx else -1
        M = (cx, cut + dirn * d)
        segs += [('C', S, (S[0], S[1] + dirn * k * d), (M[0] + ss * k * hc, M[1]), M),
                 ('C', M, (M[0] - ss * k * hc, M[1]), (E[0], E[1] + dirn * k * d), E)]
        res.append({'segs': segs, 'closed': True})
    return res[0], res[1], (cx, cut)


def shape_subs(el, ns_inkscape=None):
    """parse a <path> element's d with its own transform applied"""
    d = el.get('d')
    subs = parse(d)
    m = parse_transform(el.get('transform'))
    return apply_matrix(subs, m) if m != (1, 0, 0, 1, 0, 0) else subs


if __name__ == '__main__':
    import xml.etree.ElementTree as ET
    if sys.argv[1] == 'split':
        subs = parse(sys.argv[2]); y = float(sys.argv[3])
        up, lo = split_y(subs[0], y)
        print('UPPER', to_d([up])); print('LOWER', to_d([lo]))
    elif sys.argv[1] == 'info':
        IL = '{http://www.inkscape.org/namespaces/inkscape}label'
        root = ET.parse(sys.argv[2]).getroot()
        for el in root.iter('{http://www.w3.org/2000/svg}path'):
            subs = shape_subs(el)
            b = bbox(subs)
            print('%-24s nodes=%-3d bbox=(%.1f,%.1f)-(%.1f,%.1f)' % (el.get(IL) or el.get('id'), nodes(subs), *b))
