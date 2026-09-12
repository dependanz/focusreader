"""Closed-form kinematics of the pleat-shutter field.

These are exact consequences of the geometry in pattern.py. They need no material
constants, so unlike anything involving crease stiffness or friction they are predictions
a folded specimen can be checked against directly.

Two distinct collapse modes, with very different behaviour:

  UNIFORM   every crease sits at the same angle t from the page plane. The whole field is
            corrugated, so the covered region stands proud of the page.
                in-page pleat extent  = n * p * cos(t)
                standing height       = p * sin(t)

  SEQUENTIAL the lower k creases are closed flat and the remainder lies flat on the page.
            The covered region is genuinely flat; only the stack at the bottom stands up.
                in-page pleat extent  = (n - k) * p
                stack thickness       = (k + 1) * sheet thickness

Sequential is the mode the device wants. Closing one crease removes exactly one pitch of
in-page extent, which is what makes the pleat count a line counter.

Run from this directory:
    python kinematics.py
"""
import math
import pathlib

from pattern import (PITCH, SHEET_THICKNESS, TEXT_PITCH, front_band_height,
                     pleat_creases)

OUT_CSV = pathlib.Path(__file__).resolve().parent / "kinematics_v0_1.csv"
OUT_SVG = pathlib.Path(__file__).resolve().parent / "kinematics_v0_1.svg"

N = len(pleat_creases())
BAND = front_band_height()


def uniform(theta_deg, pitch=PITCH, n=N):
    """Reading-line height above the page's bottom edge, and standing height."""
    t = math.radians(theta_deg)
    return BAND + n * pitch * math.cos(t), pitch * math.sin(t)


def sequential(k, pitch=PITCH, n=N, thickness=SHEET_THICKNESS):
    """Reading-line height above the page's bottom edge, and collapsed stack thickness."""
    return BAND + (n - k) * pitch, (k + 1) * thickness


def indexing_drift(pitch=PITCH, text_pitch=TEXT_PITCH, n=N):
    """Closing one crease advances the reading line by exactly one pitch. If the pitch is
    not the document's line pitch, the index drifts by their difference, every line."""
    per_line = pitch - text_pitch
    return per_line, per_line * n, (per_line * n) / text_pitch


def write_csv():
    rows = ["mode,parameter,reading_line_mm,second_mm"]
    for deg in range(0, 91, 5):
        line, stand = uniform(deg)
        rows.append(f"uniform,{deg},{line:.3f},{stand:.3f}")
    for k in range(0, N + 1):
        line, stack = sequential(k)
        rows.append(f"sequential,{k},{line:.3f},{stack:.3f}")
    OUT_CSV.write_text("\n".join(rows) + "\n", encoding="utf-8")


def write_svg():
    """Reading-line height against collapse, for both modes, on one axis."""
    w, h, m = 520, 300, 44
    px = lambda f: m + f * (w - 2 * m)
    lo, hi = BAND, BAND + N * PITCH
    py = lambda v: h - m - (v - lo) / (hi - lo) * (h - 2 * m)

    uni = " ".join(f"{px(d / 90):.1f},{py(uniform(d)[0]):.1f}"
                   for d in range(0, 91))
    seq = " ".join(f"{px(k / N):.1f},{py(sequential(k)[0]):.1f}"
                   for k in range(N + 1))

    p = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" '
         f'viewBox="0 0 {w} {h}">',
         '<style>text{font-family:Helvetica,Arial,sans-serif;font-size:11px;fill:#374151}'
         '.ttl{font-size:13px;font-weight:700;fill:#111827}</style>',
         f'<rect width="{w}" height="{h}" fill="#ffffff"/>',
         f'<text class="ttl" x="{m}" y="24">Reading-line height vs collapse '
         f'(pleat shutter v0.1, predicted)</text>',
         f'<line x1="{m}" y1="{h-m}" x2="{w-m}" y2="{h-m}" stroke="#9ca3af"/>',
         f'<line x1="{m}" y1="{m}" x2="{m}" y2="{h-m}" stroke="#9ca3af"/>']
    for frac, lab in ((0, "0"), (0.5, "50%"), (1, "100%")):
        p.append(f'<text x="{px(frac):.0f}" y="{h-m+16}" text-anchor="middle">{lab}</text>')
    for v in (lo, (lo + hi) / 2, hi):
        p.append(f'<text x="{m-6}" y="{py(v)+4:.0f}" text-anchor="end">{v:.0f}</text>')
    p.append(f'<text x="{(w)/2:.0f}" y="{h-8}" text-anchor="middle">collapse '
             f'(uniform: angle/90&#176; &#183; sequential: creases closed/{N})</text>')
    p.append(f'<text transform="translate(14,{h/2:.0f}) rotate(-90)" '
             f'text-anchor="middle">mm above page bottom</text>')
    p.append(f'<polyline points="{seq}" fill="none" stroke="#1a56db" stroke-width="2"/>')
    p.append(f'<polyline points="{uni}" fill="none" stroke="#c81e1e" stroke-width="2" '
             f'stroke-dasharray="5 3"/>')
    p.append(f'<line x1="{w-m-120}" y1="{m+6}" x2="{w-m-100}" y2="{m+6}" '
             f'stroke="#1a56db" stroke-width="2"/>')
    p.append(f'<text x="{w-m-95}" y="{m+10}">sequential (linear)</text>')
    p.append(f'<line x1="{w-m-120}" y1="{m+24}" x2="{w-m-100}" y2="{m+24}" '
             f'stroke="#c81e1e" stroke-width="2" stroke-dasharray="5 3"/>')
    p.append(f'<text x="{w-m-95}" y="{m+28}">uniform (cosine)</text>')
    p.append('</svg>')
    OUT_SVG.write_text("\n".join(p), encoding="utf-8")


if __name__ == "__main__":
    print(f"n={N} pleat creases, pitch={PITCH} mm, front band={BAND} mm\n")

    print("SEQUENTIAL mode - the operating mode")
    print(f"{'creases closed':>14} {'reading line mm':>16} {'stack mm':>9}")
    for k in (0, 1, 10, 25, 40, N):
        line, stack = sequential(k)
        print(f"{k:>14} {line:>16.1f} {stack:>9.2f}")
    print(f"  advance per closed crease = {PITCH:.1f} mm, exactly one pitch\n")

    print("UNIFORM mode - the corrugated failure mode")
    print(f"{'angle deg':>14} {'reading line mm':>16} {'stands mm':>10}")
    for d in (0, 30, 45, 60, 75, 90):
        line, stand = uniform(d)
        print(f"{d:>14} {line:>16.1f} {stand:>10.2f}")
    print(f"  standing height peaks at the full pitch, {PITCH:.1f} mm, not half of it\n")

    per, total, lines = indexing_drift()
    print("INDEXING DRIFT")
    print(f"  pitch {PITCH} mm vs text pitch {TEXT_PITCH} mm -> {per:+.1f} mm per line,")
    print(f"  {total:+.1f} mm over {N} lines = {lines:+.2f} lines of drift per page.")
    print(f"  Setting pitch = the document's actual line pitch removes this entirely.\n")

    write_csv()
    write_svg()
    print(f"wrote {OUT_CSV.name} and {OUT_SVG.name}")
