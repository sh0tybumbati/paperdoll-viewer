#!/usr/bin/env python3
"""Build the doll viewer: a single self-contained HTML file.
usage: make_viewer.py out.html [sprite.svg ...]    (default samples: every references/*.svg of this skill)
Open the result in a browser; drop any rigged sprite .svg onto it. Joint hierarchy is read from the paired
pivot markers, so no JSON is needed. Cycles: idle, walk, trot, run, plus a manual pose mode."""
import json, os, sys, glob
here = os.path.dirname(os.path.abspath(__file__))
out, svgs = sys.argv[1], sys.argv[2:]
if not svgs:
    svgs = sorted(glob.glob(os.path.join(here, '..', 'references', '*.svg')))
samples = {}
for p in svgs:
    samples[os.path.splitext(os.path.basename(p))[0]] = open(p, encoding='utf-8').read()
html = open(os.path.join(here, 'viewer_template.html'), encoding='utf-8').read()
html = html.replace('/*SAMPLES*/{}', json.dumps(samples).replace('</', '<\\/'))
open(out, 'w', encoding='utf-8').write(html)
print('wrote %s (%d samples: %s)' % (out, len(samples), ', '.join(samples)))
