"""Single source of truth for the origami_solution v0.2 frame reader geometry.

v0.2 is a paper version of physical_reader_tool's frame and four shutters, made from several A4
sheets by folding alone. Four identical rails grip the page on all four edges; four shutters slide
with their ends in pockets folded into the rails. This file defines the parts. gen_parts_v0_2.py
writes them out as FOLD files with a sidecar naming each crease's role.

Every part is a strip of panels separated by parallel creases, so each is fully described by the
crease positions across the sheet and the fold at each crease. All millimetres.

Rail: one A4 sheet folded across its 210 mm width into a 297 mm long strip. Measured from the sheet
edge that goes under the page:
    lip      LIP mm, lies under the page's edge
    wall     two 90-degree creases WALL mm apart, standing at the page's edge
    body     N_LAYERS panels of BODY mm, folded back and forth on top of the page's edge
The body folds alternate between the inner edge (toward the page's centre) and the outer edge. The
fold between body layers 2 and 3 is at the outer edge, so the pocket between those layers opens
toward the page's centre; a shutter's end slides into it by up to POCKET_DEPTH.

Shutter: one A4 sheet folded in half for opacity, with the fold at the window edge and the two open
ends inside the pockets of the rails it spans. Side shutters fold along the long side, giving a
297 x 105 mm panel; top and bottom shutters fold across it, giving 210 x 148.5 mm.

Nothing here has been folded. Every number is a design value, and SHEET_THICKNESS is assumed.
"""

SHEET_W = 210.0
SHEET_H = 297.0
SHEET_THICKNESS = 0.10      # assumed nominal caliper of 80 gsm office paper, not measured

LIP = 12.0
WALL = 2.0
N_LAYERS = 8
BODY = (SHEET_W - LIP - WALL) / N_LAYERS      # 24.5 mm
POCKET_LAYERS = (2, 3)      # the shutter end slides between these body layers, counted from the page
POCKET_DEPTH = BODY

# A crease is (position across the sheet, assignment, FOLD fold angle, role). Walking away from the
# lip edge, a valley turns toward the sheet's front face and a mountain away from it; the front face
# is the one that ends up on top of body layer 1.
FULL = 180.0
RIGHT = 90.0


def rail_creases():
    creases = [
        (LIP, "M", -RIGHT, "wall"),
        (LIP + WALL, "M", -RIGHT, "wall"),
    ]
    for k in range(1, N_LAYERS):
        y = LIP + WALL + k * BODY
        if k % 2 == 1:
            creases.append((round(y, 6), "V", FULL, "inner_fold"))
        elif k == POCKET_LAYERS[0]:
            creases.append((round(y, 6), "M", -FULL, "pocket"))
        else:
            creases.append((round(y, 6), "M", -FULL, "outer_fold"))
    return creases


def rail_layers():
    """Body layer k spans [start, end] across the sheet, counted from the page side."""
    out = {}
    for k in range(1, N_LAYERS + 1):
        start = LIP + WALL + (k - 1) * BODY
        out[k] = (round(start, 6), round(start + BODY, 6))
    return out


def shutter_creases(orientation):
    """One valley fold across the middle of the sheet. Side shutters fold the 297 mm side in half; top
    and bottom shutters fold the 210 mm side. The crease is given in a frame where it runs along x."""
    if orientation == "side":
        w, h = SHEET_H, SHEET_W
    elif orientation == "top":
        w, h = SHEET_W, SHEET_H
    else:
        raise ValueError(orientation)
    return w, h, [(h / 2.0, "V", FULL, "double_fold")]


def summary():
    rail = rail_creases()
    return {
        "sheets_per_device": 8,
        "rails": 4,
        "shutters": 4,
        "rail_creases": len(rail),
        "rail_body_layers": N_LAYERS,
        "rail_body_mm": BODY,
        "lip_mm": LIP,
        "wall_mm": WALL,
        "pocket_layers": POCKET_LAYERS,
        "pocket_depth_mm": POCKET_DEPTH,
        "page_covered_by_each_rail_mm": BODY,
        "side_shutter_panel_mm": (SHEET_H, SHEET_W / 2.0),
        "top_shutter_panel_mm": (SHEET_W, SHEET_H / 2.0),
        "folds_per_device": 4 * len(rail) + 4,
    }


if __name__ == "__main__":
    for key, value in summary().items():
        print(f"{key:30} {value}")
    print("rail creases from the lip edge:")
    for y, kind, angle, role in rail_creases():
        print(f"  {y:7.2f} mm  {kind}  {angle:+6.1f}  {role}")
