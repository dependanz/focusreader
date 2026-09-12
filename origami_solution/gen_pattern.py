"""Emit the origami_solution pleat-shutter crease pattern as a true-scale A4 SVG.

Geometry comes from pattern.py; this module only draws. Run it from this directory:
    python gen_pattern.py
"""
import pathlib

from pattern import (SHEET_W as W, SHEET_H as H, PITCH, FIELD_TOP, FIELD_BOT,
                     BAND_BOT, pleat_creases)

VALLEY = "#1a56db"
MOUNTAIN = "#c81e1e"
INK = "#111827"
FAINT = "#9ca3af"

creases = pleat_creases()

parts = []
a = parts.append

a(f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}mm" height="{H}mm" '
  f'viewBox="0 0 {W} {H}">')
a('<title>FocusReader origami_solution - pleat shutter v0.1 crease pattern</title>')
a('<style>'
  'text{font-family:Helvetica,Arial,sans-serif;fill:#111827}'
  '.t{font-size:4.4px;font-weight:700}'
  '.s{font-size:2.5px}'
  '.n{font-size:2.2px}'
  '.idx{font-size:2px;fill:#6b7280}'
  '.zn{font-size:2.6px;font-weight:700;fill:#374151;letter-spacing:0.4px}'
  '</style>')
a(f'<rect x="0" y="0" width="{W}" height="{H}" fill="#ffffff"/>')

# --- sheet outline and corner marks ---
a(f'<rect x="0.15" y="0.15" width="{W-0.3}" height="{H-0.3}" fill="none" '
  f'stroke="{FAINT}" stroke-width="0.3"/>')

# --- pleat creases ---
a('<g stroke-linecap="butt">')
for yy, kind in creases:
    if kind == "V":
        a(f'<line x1="0" y1="{yy}" x2="{W}" y2="{yy}" stroke="{VALLEY}" '
          f'stroke-width="0.25" stroke-dasharray="3.2 2.2"/>')
    else:
        a(f'<line x1="0" y1="{yy}" x2="{W}" y2="{yy}" stroke="{MOUNTAIN}" '
          f'stroke-width="0.25" stroke-dasharray="5 1.6 0.9 1.6"/>')
a('</g>')

# --- every 10th crease indexed, both margins ---
for i, (yy, kind) in enumerate(creases, start=1):
    if i % 10 == 0:
        for xx, anch in ((3.2, "start"), (W - 3.2, "end")):
            a(f'<rect x="{xx-2.6 if anch=="start" else xx-4.4}" y="{yy-3.1}" width="7" '
              f'height="3" fill="#ffffff"/>')
            a(f'<text class="idx" x="{xx}" y="{yy-0.9}" text-anchor="{anch}">'
              f'{i} &#183; {yy:.0f}mm</text>')

# --- reading edge callout ---
a(f'<rect x="58" y="0.6" width="94" height="3.6" fill="#ffffff"/>')
a(f'<text class="s" x="105" y="3.4" text-anchor="middle" fill="{INK}">'
  'READING EDGE when fully extended</text>')

# --- zone labels, rotated in the right margin ---
a(f'<text class="zn" transform="translate(206.4,128) rotate(-90)" '
  f'text-anchor="middle">PLEAT FIELD 250 mm &#183; 50 CREASES &#183; 5.0 mm PITCH</text>')

# --- band / flap zones ---
a(f'<line x1="0" y1="{FIELD_BOT}" x2="{W}" y2="{FIELD_BOT}" stroke="{MOUNTAIN}" '
  f'stroke-width="0.25" stroke-dasharray="5 1.6 0.9 1.6"/>')
a(f'<text class="zn" x="5" y="{FIELD_BOT+4.6}">FRONT BAND 27 mm &#183; lies flat on the page</text>')

# --- title block inside the front band ---
a(f'<text class="t" x="5" y="{FIELD_BOT+10.5}">FocusReader &#183; origami_solution &#183; '
  'pleat shutter v0.1</text>')
a(f'<text class="s" x="5" y="{FIELD_BOT+14.6}" fill="#b91c1c">'
  'UNTESTED &#183; 2026-09-08 &#183; nothing has been folded, timed or measured</text>')

# --- 200 mm print-scale reference line ---
ry = FIELD_BOT + 18.0
a(f'<line x1="5" y1="{ry}" x2="205" y2="{ry}" stroke="{INK}" stroke-width="0.4"/>')
for xx in (5, 205):
    a(f'<line x1="{xx}" y1="{ry-1.8}" x2="{xx}" y2="{ry+1.8}" stroke="{INK}" '
      f'stroke-width="0.4"/>')
a(f'<rect x="64" y="{ry-2.9}" width="82" height="3.4" fill="#ffffff"/>')
a(f'<text class="s" x="105" y="{ry-0.4}" text-anchor="middle" font-weight="700">'
  'MEASURE THIS &#8594; must be exactly 200 mm</text>')
a(f'<text class="n" x="105" y="{ry+3.6}" text-anchor="middle" fill="#6b7280">'
  'If it is not, the print scaled. Reprint at 100% / Actual size, Fit to Page OFF.</text>')

# --- hinge crease ---
a(f'<line x1="0" y1="{BAND_BOT}" x2="{W}" y2="{BAND_BOT}" stroke="{MOUNTAIN}" '
  f'stroke-width="0.7" stroke-dasharray="7 2 1.2 2"/>')
a(f'<rect x="52" y="{BAND_BOT-3.3}" width="106" height="2.9" fill="#ffffff"/>')
a(f'<text class="s" x="105" y="{BAND_BOT-1.1}" text-anchor="middle" font-weight="700" '
  f'fill="{MOUNTAIN}">HINGE &#183; mountain-fold, wraps the page&#8217;s bottom edge</text>')

# --- legend and notes in the tuck flap, 277..297 mm ---
a(f'<text class="zn" x="5" y="280.2">TUCK FLAP 20 mm &#183; goes BEHIND the page</text>')

a(f'<line x1="5" y1="283.0" x2="15" y2="283.0" stroke="{VALLEY}" stroke-width="0.5" '
  f'stroke-dasharray="3.2 2.2"/>')
a(f'<text class="n" x="17" y="283.8">VALLEY 25</text>')
a(f'<line x1="40" y1="283.0" x2="50" y2="283.0" stroke="{MOUNTAIN}" stroke-width="0.5" '
  f'stroke-dasharray="5 1.6 0.9 1.6"/>')
a(f'<text class="n" x="52" y="283.8">MOUNTAIN 26 incl. hinge</text>')
a(f'<text class="n" x="112" y="283.8">51 folds &#183; 1 sheet &#183; 80 gsm A4 &#8776; 5 g</text>')

a(f'<text class="n" x="5" y="287.2">'
  'FOLD ORDER 1 Hinge first; tuck the flap behind the page. '
  '2 Pre-crease all 50 pleats, alternating from the top. '
  '3 Over-crease each so it rests folded.</text>')
a(f'<text class="n" x="5" y="290.6">'
  '4 Set the reading edge by collapsing pleats from the top. '
  'PITCH 5.0 mm &#8776; one 12 pt line at 1.15 spacing, so one pleat &#8776; one line.</text>')
a(f'<text class="n" x="5" y="294.0" fill="#6b7280">'
  'GRAIN These creases run ACROSS the machine direction on common long-grain A4, the crackier '
  'way. Tear a scrap both ways: it tears straighter along the grain.</text>')

a('</svg>')

out = pathlib.Path(__file__).resolve().parent /     "focusreader_origami_pleat_shutter_v0_1.svg"
out.write_text("\n".join(parts), encoding="utf-8")

valleys = sum(1 for _, k in creases if k == "V")
mountains = sum(1 for _, k in creases if k == "M")
print(f"pleat creases={len(creases)} valley={valleys} mountain={mountains}")
print(f"first={creases[0]} last={creases[-1]}")
print(f"field={FIELD_BOT:.0f} mm covered by {len(creases)} creases, "
      f"segments={int(FIELD_BOT/PITCH)}")
print(f"wrote {out.name} ({out.stat().st_size} bytes)")
