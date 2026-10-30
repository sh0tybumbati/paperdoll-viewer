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
- `skill/paperdoll-sprite/`: the Claude Code skill that builds these dolls: `SKILL.md` (the rules and workflow), `scripts/` (tracing, validation, pose and viewer tools) and `references/` (the worked examples and their `build_*.py` generators).

### Using the build scripts

The generators in `skill/paperdoll-sprite/references/` read their reference drawings from `references/sources/`. Those reference images (AI-generated art the dolls were traced from) are not published in this repo, so the `build_*.py` scripts will not run until you put the images back there (`boar_flip.png`, `stag_flip.png`, `wolf_flip.png`, `bull_flip.png`, `rabbit_flip.png`, `man_flip.png`: the originals, mirrored to face left). The finished dolls in `dolls/` and the viewer do not need them.

No licence has been chosen yet, so all rights are reserved until one is added.
