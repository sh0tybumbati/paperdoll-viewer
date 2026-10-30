#!/usr/bin/env python3
"""Extract part geometry from a flat-colour reference (line art + fills on a plain background).
Library; import with sys.path.insert(0, '<skill>/scripts').

    R = Ref('ref.png', scale=0.034, ox=-18.4, oy=-0.74)   # sprite = px*scale + (ox, oy); mirror the file first if needed
    m = R.part_mask([[(x, y), ...], ...])                   # silhouette clipped by polygon(s) given in sprite units
    for pts, corners in R.paths(m): ...                     # closed outlines in sprite units, simplified (tol units)
    tones = R.tone_masks(m)                                 # {0: mask, 1: mask, 2: mask} fill levels, dark to light

The silhouette is the outer edge of the drawing's line work (outline centre-line); fur and tufts survive when
`tol` is small. Everything is exact to the reference: only RDP simplification error (tol) remains."""
import sys, os
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage as ndi
import contourpy


def rdp(pts, tol):
    pts = np.asarray(pts, float)
    keep = np.zeros(len(pts), bool); keep[0] = keep[-1] = True
    stack = [(0, len(pts) - 1)]
    while stack:
        i, j = stack.pop()
        if j <= i + 1:
            continue
        a, b = pts[i], pts[j]; ab = b - a; L = np.hypot(*ab)
        seg = pts[i + 1:j]
        d = np.hypot(*(seg - a).T) if L < 1e-9 else np.abs(ab[0] * (seg[:, 1] - a[1]) - ab[1] * (seg[:, 0] - a[0])) / L
        k = int(np.argmax(d))
        if d[k] > tol:
            keep[i + 1 + k] = True; stack += [(i, i + 1 + k), (i + 1 + k, j)]
    return pts[keep]


class Ref:
    def __init__(self, path, scale, ox, oy, bg_thr=40.0, line_lum=70.0, levels=None, thick_px=0, class_sigma=0):
        im = np.array(Image.open(path).convert('RGB')).astype(float)
        self.shape = im.shape[:2]; self.s, self.ox, self.oy = scale, ox, oy
        bg = np.median(np.concatenate([im[:12].reshape(-1, 3), im[-12:].reshape(-1, 3)]), axis=0)
        lum = im.mean(axis=2); self.lum = lum
        fg = np.linalg.norm(im - bg, axis=2) > bg_thr
        self.fg_raw = ndi.binary_closing(fg, iterations=2)          # no hole filling: enclosed gaps (between antler tines) stay empty
        fg = ndi.binary_fill_holes(self.fg_raw)
        lab, n = ndi.label(fg)
        if n > 1:
            fg = lab == (1 + int(np.argmax(ndi.sum(fg, lab, range(1, n + 1)))))
        self.fg = fg
        fill = fg & (lum > line_lum)
        if thick_px:      # dark fills as dark as the outline: thick regions are fill, thin strokes are line work
            dark = fg & (lum <= line_lum)
            fill |= ndi.binary_dilation(ndi.binary_opening(dark, iterations=thick_px), iterations=thick_px) & dark
        # fill level classes by luminance thresholds (default: split the fill histogram into 3 by its valleys)
        vals = ndi.gaussian_filter(lum, 2)
        if levels is None:
            h, e = np.histogram(vals[fill], bins=64, range=(line_lum, 230))
            levels = self._valleys(h, e)
        self.levels = levels
        cls = np.digitize(vals, levels)
        # only trust the interior of each fill (blur and anti-aliasing darken pixels beside the line work);
        # edge and outline pixels take the class of the nearest interior pixel
        if class_sigma:    # textured dark regions (hair): classify by the local mean of the non-stroke pixels
            f = fill.astype(float)
            num = ndi.gaussian_filter(lum * f, class_sigma); den = ndi.gaussian_filter(f, class_sigma)
            self.cls = np.digitize(np.where(den > 0.04, num / np.maximum(den, 1e-6), lum), levels)
            self.cls[~fg] = -1
        else:
            core = ndi.binary_erosion(fill, iterations=6)
            d, (iy, ix) = ndi.distance_transform_edt(~core, return_indices=True)
            self.cls = cls[iy, ix]; self.cls[~fg] = -1

    @staticmethod
    def _valleys(h, e, k=3):
        h = ndi.gaussian_filter1d(h.astype(float), 1.5)
        peaks = [i for i in range(1, len(h) - 1) if h[i] >= h[i - 1] and h[i] > h[i + 1] and h[i] > h.max() * 0.08]
        peaks = sorted(sorted(peaks, key=lambda i: -h[i])[:k])
        cuts = []
        for a, b in zip(peaks, peaks[1:]):
            cuts.append(e[a + int(np.argmin(h[a:b + 1]))])
        return cuts

    def px(self, x, y):
        return ((x - self.ox) / self.s, (y - self.oy) / self.s)

    def units(self, px, py):
        return (px * self.s + self.ox, py * self.s + self.oy)

    def poly_mask(self, polys):
        img = Image.new('L', (self.shape[1], self.shape[0]), 0)
        dr = ImageDraw.Draw(img)
        for p in polys:
            dr.polygon([self.px(*q) for q in p], fill=255)
        return np.array(img) > 0

    def part_mask(self, polys, minus=(), grow=0.0, holes=False):
        """silhouette clipped to polygon(s). grow (sprite units) pushes the cut edges outward only (the
        silhouette edge is untouched), so adjacent parts overlap instead of leaving an antialiasing seam"""
        pm = self.poly_mask(polys)
        if grow > 0:
            pm = ndi.binary_dilation(pm, iterations=max(1, int(round(grow / self.s))))
        m = (self.fg_raw if holes else self.fg) & pm
        for p in minus:
            m &= ~self.poly_mask([p])
        return m

    def paths(self, mask, tol=0.15, min_area=0.4, corner_deg=55, sigma=2.5, holes=False):
        """closed outlines of mask as [(pts, corner_indices)] in sprite units, largest first"""
        z = ndi.gaussian_filter(mask.astype(float), sigma)
        gen = contourpy.contour_generator(z=z, name='serial')
        out = []
        for line in gen.lines(0.5):
            if len(line) < 8:
                continue
            u = np.array([self.units(x, y) for x, y in line])
            area = 0.5 * abs(np.dot(u[:, 0], np.roll(u[:, 1], 1)) - np.dot(u[:, 1], np.roll(u[:, 0], 1)))
            if area < min_area:
                continue
            if np.allclose(u[0], u[-1]):
                u = u[:-1]
            # simplify the closed curve: split at the two most distant points
            i0 = 0; j0 = int(np.argmax(np.hypot(*(u - u[0]).T)))
            a = rdp(np.vstack([u[i0:j0 + 1]]), tol); b = rdp(np.vstack([u[j0:], u[:1]]), tol)
            P = np.vstack([a[:-1], b[:-1]])
            corners = []
            for i in range(len(P)):
                v1 = P[i] - P[i - 1]; v2 = P[(i + 1) % len(P)] - P[i]
                n1, n2 = np.hypot(*v1), np.hypot(*v2)
                if n1 < 1e-6 or n2 < 1e-6:
                    continue
                ang = np.degrees(np.arccos(np.clip(np.dot(v1, v2) / (n1 * n2), -1, 1)))
                if ang > corner_deg:
                    corners.append(i)
            out.append(([tuple(p) for p in P], tuple(corners), area))
        out.sort(key=lambda t: -t[2])
        return [(p, c) for p, c, _ in out]

    def limb_cap(self, mask, cut, fit=True):
        """Split a limb mask at y=cut (sprite units) into (upper, lower, pivot_x) with round 'ball joint' caps: each half
        also keeps the disc centred on the joint, clipped to the limb silhouette, so the rest pose is unchanged but a
        rotated half turns its cap inside the other one. fit=True shrinks the disc until it lies fully inside the limb
        (a disc wider than the limb gets clipped into square corners that stick out when bent)."""
        py = int(round(self.px(0, cut)[1])); xs = np.nonzero(mask[py])[0]
        if len(xs) == 0:
            raise ValueError('no limb at y=%g' % cut)
        cx, hc = (xs.min() + xs.max()) / 2.0, (xs.max() - xs.min()) / 2.0
        r = hc
        if fit:
            rows = {}
            for dy in range(-int(hc) - 1, int(hc) + 2):
                y = py + dy
                if 0 <= y < self.shape[0]:
                    xr = np.nonzero(mask[y])[0]
                    if len(xr):
                        rows[dy] = (xr.min(), xr.max())
            while r > 0.45 * hc:
                ok = True
                for dy in range(-int(r), int(r) + 1):
                    if dy not in rows:
                        ok = False; break
                    w = (r * r - dy * dy) ** 0.5
                    if cx - w < rows[dy][0] - 1 or cx + w > rows[dy][1] + 1:
                        ok = False; break
                if ok:
                    break
                r *= 0.97
        yy, xx = np.mgrid[0:self.shape[0], 0:self.shape[1]]
        disc = (xx - cx) ** 2 + (yy - py) ** 2 <= r * r
        return mask & ((yy <= py) | disc), mask & ((yy >= py) | disc), self.units(cx, 0)[0]

    def disc_mask(self, cx, cy, r):
        """boolean disc, centre and radius in sprite units"""
        px, py = self.px(cx, cy)
        yy, xx = np.ogrid[:self.shape[0], :self.shape[1]]
        return (xx - px) ** 2 + (yy - py) ** 2 <= (r / self.s) ** 2

    def force_tone_disc(self, cx, cy, r, k=None):
        """make the fill tone uniform inside a disc (for every part that touches it). Put one on each joint so the
        round caps on both sides of a pivot have the same tone and blend when posed. k=None: the dominant class."""
        d = self.disc_mask(cx, cy, r) & self.fg
        if k is None:
            c = self.cls[d]; c = c[c >= 0]
            k = int(np.bincount(c).argmax())
        self.cls[d] = k
        return k

    def top_cap(self, mask, pivot, r):
        """round the top end of a limb mask on the pivot (sprite units): keep rows below the pivot, plus a disc of
        radius r around it. Used for shoulder/hip joints whose upper end sits inside the body."""
        px, py = self.px(*pivot)
        yy = np.arange(self.shape[0])[:, None]
        return mask & ((yy >= py) | self.disc_mask(pivot[0], pivot[1], r))

    def inset(self, mask, units=0.12):
        """mask eroded a little so overlay shapes stay inside the base silhouette"""
        return ndi.binary_erosion(mask, iterations=max(1, int(round(units / self.s))))

    def dark_blobs(self, mask, lum_max=60, open_units=0.22, min_area=0.25):
        """thick very dark features (nose, pupil) as masks; thin outline strokes vanish in the opening"""
        d = mask & (self.lum < lum_max)
        d = ndi.binary_opening(d, iterations=max(1, int(round(open_units / self.s))))
        lab, n = ndi.label(d)
        out = []
        for i in range(1, n + 1):
            m = lab == i
            if m.sum() * self.s * self.s >= min_area:
                out.append(m)
        return out

    def tone_partition(self, mask, min_area=0.9, open_px=3, overlap=0.05, force=()):
        """{class: mask} that tiles `mask` exactly: speckle regions are absorbed by the nearest kept class, then each
        region grows by `overlap` units (inside mask) so neighbouring shapes overlap and no hairline seams appear.
        Tracing every region separately (no 'base + overlays') keeps cut edges tone-exact between parts."""
        cls0 = self.cls.copy()
        for fm, fk in force:                      # force=[(bool mask, class)]: flatten areas for this part only
            cls0[fm & mask] = fk
        tm = self.tone_masks(mask, min_area=min_area, open_px=open_px, cls=cls0)
        keep = np.zeros(self.shape, bool); cls = np.full(self.shape, -1, np.int8)
        for k, m in tm.items():
            keep |= m; cls[m] = k
        if not keep.any():
            return {}
        d, (iy, ix) = ndi.distance_transform_edt(~keep, return_indices=True)
        full = np.where(keep, cls, cls[iy, ix]); full[~mask] = -1
        g = max(1, int(round(overlap / self.s)))
        out = {}
        for k in np.unique(full[full >= 0]):
            m = full == k
            out[int(k)] = ndi.binary_dilation(m, iterations=g) & mask
        return out

    def tone_masks(self, mask, min_area=1.2, open_px=3, cls=None):
        """{class: mask} for each fill level inside mask, speckle removed. class 0 darkest."""
        res = {}
        px_area = self.s * self.s
        for k in range(len(self.levels) + 1):
            m = mask & ((self.cls if cls is None else cls) == k)
            m = ndi.binary_opening(m, iterations=open_px)
            lab, n = ndi.label(m)
            if n:
                sizes = ndi.sum(m, lab, range(1, n + 1))
                keep = np.zeros(n + 1, bool); keep[1:] = sizes * px_area >= min_area
                m = keep[lab]
            res[k] = m
        return res
