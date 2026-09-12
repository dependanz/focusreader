# origami_solution — fold-only paper reading guard

Design source for the FocusReader `origami_solution` subproject: a reading guard anyone can make
from one sheet of ordinary paper by folding alone — no cuts, tears, adhesive, or tools.

Authoritative plan, quantitative ledger, and decision log live in devbrain at
`C:/dev/devbrain/projects/focusreader/`. This directory holds design source only. Do not record
results here; record them in `NUMBERS.md`.

## Status

**Nothing has been printed, folded, timed, or measured.** The v0.1 crease pattern is a drawn
candidate whose geometry has been checked against its generating source. That verifies the drawing,
not the device.

Unlike the `physical_reader_tool` subproject, this one has no simulation screening stage. The
pattern has no interior vertices, so flat-foldability and rigid-foldability checks have nothing to
test, and crease spring-back, inter-layer friction, and crease fatigue depend on creased-paper
constants that must not be assumed. Its first real evidence requires a person folding paper.

## Files

| File | Role |
|---|---|
| `gen_pattern.py` | Source. Emits the true-scale A4 crease pattern. Dependency-free. |
| `focusreader_origami_pleat_shutter_v0_1.svg` | Generated output. Git-ignored; regenerate it. |

Regenerate with:

```
python gen_pattern.py
```

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
