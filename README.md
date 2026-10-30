# Paperdoll viewer

A single-page tester for layered, greyscale, pivot-rigged paperdoll sprites.

**Live viewer:** https://sh0tybumbati.github.io/paperdoll-viewer/

- Pick a doll (boar, bull, deer, man, rabbit, wolf) or drop any rigged `.svg` onto the page.
- Idle, walk, trot and run cycles, plus a Pose mode with a slider for every joint.
- Mirror, tint test (recolour the greyscale), pivot display and a scrolling ground.
- Keys: `space` pause, `.` step, `1`-`5` animations.

The joint hierarchy is read from the paired pivot markers in each SVG, so no extra data is needed.

## Files

- `index.html`: the viewer (self-contained, the approved dolls are embedded).
- `dolls/`: the approved dolls as SVG, each with its `*.hierarchy.json`.

No licence has been chosen yet, so all rights are reserved until one is added.
