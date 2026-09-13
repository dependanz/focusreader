# origami_solution — fold-only paper reading guard

Design source for the FocusReader `origami_solution` subproject: a reading guard anyone can make
from a few sheets of ordinary paper by folding alone — no cuts, tears, adhesive, or tools. Since
2026-09-12 the target is v0.2, a paper version of the printed reader's frame and four sliding
shutters; the single-sheet pleat shutter v0.1 is kept only as a candidate for the bottom shutter.

Authoritative plan, quantitative ledger, and decision log live in devbrain at
`C:/dev/devbrain/projects/focusreader/`. This directory holds design source only. Do not record
results here; record them in `NUMBERS.md`.

## Status

**Nothing has been printed, folded, timed, or measured.** The v0.1 pleat pattern and the v0.2 part
patterns are drawn candidates whose geometry is checked against their generating source. That
verifies the drawings, not the device.

Simulation screening exists through the separate `foldsim` project, which folds these patterns with
contact between paper layers. Its material is uncalibrated, so its results rank designs and predict
nothing about real paper; the first real evidence still requires a person folding paper.

## Files

| File | Role |
|---|---|
| `parts_v0_2.py` | Source for v0.2: the rail and shutter geometry. Dependency-free. |
| `gen_parts_v0_2.py` | Writes the v0.2 rail and shutters as FOLD files, each with a `.parts.json` sidecar naming its creases' roles. |
| `pattern.py` | Source for v0.1: the pleat-shutter geometry shared by the generators below. |
| `gen_pattern.py` | Emits the v0.1 true-scale A4 crease pattern as SVG. |
| `gen_fold.py` | Emits the v0.1 pattern as FOLD. |
| `kinematics.py` | The v0.1 closed-form collapse kinematics. |
| `*.fold`, `*.parts.json`, `*.svg`, `*.csv` | Generated output. Git-ignored; regenerate it. |

Regenerate with:

```
python gen_parts_v0_2.py
python gen_pattern.py
python gen_fold.py
```

## Frame reader v0.2 geometry

Eight A4 sheets: four rails and four shutters.

A rail is one sheet folded across its 210 mm width into a 297 mm strip. From the edge that goes
under the page: a 12 mm lip, a wall of two 90° creases 2 mm apart standing at the page's edge, then
eight 24.5 mm body layers folded back and forth on top of the page's edge. The fold between body
layers 2 and 3 is at the outer edge, so the pocket between them opens toward the page's centre; a
shutter's end slides into it by up to 24.5 mm. Each rail covers 24.5 mm of the page, inside a
25 mm margin. Rails join at the corners by the same pockets; that joint is not yet drawn.

A shutter is one sheet folded in half for opacity, with the fold at the window edge and its two open
ends in the pockets of the rails it spans. Side shutters fold along the long side (297 × 105 mm);
top and bottom shutters fold across it (210 × 148.5 mm). Sliding a shutter in shrinks the window
from that side; pulling the top, left and right shutters fully out leaves bottom-only mode.

What holds a shutter in place is the pocket's grip on its end: paper-on-paper friction under
whatever squeeze the pocket's creases give. That is the design's open question, and the first thing
`foldsim` tests.

## Pleat shutter v0.1 geometry

A4 portrait, 210 × 297 mm, measured from the sheet top:

| Zone | Span | Role |
|---|---|---|
| Pleat field | 0–250 mm | 50 creases at 5.0 mm pitch, alternating valley/mountain |
| Front band | 250–277 mm | Lies flat on the page below the pleats |
| Hinge (mountain) | 277 mm | Wraps the page's bottom edge |
| Tuck flap | 277–297 mm | Goes behind the page |

51 folds total. The device anchors at the page's bottom edge only, because an accordion changes
length and cannot be attached along its whole side to a fixed-length page. The free top edge is the
reading line; collapsing one pleat advances it by roughly one line of 12 pt text at 1.15 spacing.

Predicted reading-edge range is about 32–277 mm above the page's bottom edge, which spans the
25–272 mm text block of an A4 page with 25 mm margins. Predicted, not measured.

## Before taking any measurement

1. Print at 100% / Actual size with Fit to Page **off**.
2. Measure the sheet's own 200 mm reference line with a steel rule. If it is not 200 mm, the print
   scaled and every reading taken from that sheet is wrong by that factor. Reprint.
3. Record relative humidity, temperature, and the ream's paper grain direction. Paper stiffness and
   crease behaviour move with humidity, and folds along versus across the machine direction behave
   differently, so specimens folded in different conditions are not comparable.

To find grain direction, tear a scrap both ways: it tears straighter along the grain.

## Known open risks

- **Spring-back.** Fifty creases each want to return toward flat. Over-crease so each rests folded.
  If the field will not hold a commanded line, try the sliding folded pocket and then a bistable
  Kresling or waterbomb pattern before relaxing the fold-only constraint.
- **Cracking across the grain.** These creases run across the machine direction on common
  long-grain A4, the crackier way.
- **Stiffness.** Fifty layers of friction may be too much to nudge one pleat at a time one-handed.
  A coarser two-line pitch relieves this but stands about twice as proud of the page.
