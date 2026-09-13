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
# A shutter's sheet is exactly as long as the page edge it spans, and the pockets close at the page's edges,
# so an unhemmed shutter would have no room to slide. One end is folded back by SHUTTER_HEM to give it some.
SHUTTER_HEM = 3.0

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


# ---------------------------------------------------------------------------------------------------
# Frame layout and the corner joint.
#
# Every rail is a clip: its lip goes under the page's edge and its body layers go over it, with the wall
# standing at the edge. Four rails clip onto the page's four edges, and the four shutters tie opposite rails
# together through their pockets. The corner joint needs no extra fold: at each corner the side rail's end,
# lip and body together, sits inside the top or bottom rail's clip, between that rail's lip and its body
# layer 1, over the page's corner, for the clip's full depth. The side rails therefore run the page's full
# height, and the top and bottom rails, being the same 297 mm part, overhang the page's sides by
# OVERHANG on each side. The overhangs are where the frame is picked up.
#
# Page coordinates: x across from the left edge, y down from the top edge, millimetres.

PAGE_W, PAGE_H = SHEET_W, SHEET_H
RAIL_LEN = SHEET_H                          # one A4 folded across its width
OVERHANG = (RAIL_LEN - PAGE_W) / 2.0        # 43.5 mm each side for the top and bottom rails
TEXT_MARGIN = 25.0                          # the margin of an A4 page with a 25 mm border


def frame_layout():
    rails = {
        "left": {"runs_along": "y", "page_edge": "x = 0", "span_mm": [0.0, PAGE_H], "body_over_page_mm": BODY,
                 "corner_role": "inside", "length_mm": RAIL_LEN},
        "right": {"runs_along": "y", "page_edge": f"x = {PAGE_W:g}", "span_mm": [0.0, PAGE_H], "body_over_page_mm": BODY,
                  "corner_role": "inside", "length_mm": RAIL_LEN},
        "top": {"runs_along": "x", "page_edge": "y = 0", "span_mm": [-OVERHANG, PAGE_W + OVERHANG],
                "body_over_page_mm": BODY, "corner_role": "outside", "length_mm": RAIL_LEN},
        "bottom": {"runs_along": "x", "page_edge": f"y = {PAGE_H:g}", "span_mm": [-OVERHANG, PAGE_W + OVERHANG],
                   "body_over_page_mm": BODY, "corner_role": "outside", "length_mm": RAIL_LEN},
    }
    corner = {
        "joint": "the side rail's end sits inside the top or bottom rail's clip, between its lip and body layer 1, "
                 "over the page's corner",
        "depth_mm": BODY,
        "stack_from_below": ["outside rail lip", "inside rail lip", "page", f"inside rail body, {N_LAYERS} layers",
                             "outside rail body"],
        "stack_nominal_mm": corner_stack_nominal_mm(),
        "clip_opening_mm": WALL,
        "assembly_order": "clip the side rails onto the page first, then the top and bottom rails over their ends",
    }
    shutters = {
        "side": {"ends_in": ["top", "bottom"], "span_between_pocket_mouths_mm": PAGE_H - 2 * BODY,
                 "sheet_length_mm": SHEET_H, "hem_mm": SHUTTER_HEM, "length_mm": SHEET_H - SHUTTER_HEM,
                 "max_cover_mm": SHEET_W / 2.0},
        "top": {"ends_in": ["left", "right"], "span_between_pocket_mouths_mm": PAGE_W - 2 * BODY,
                "sheet_length_mm": SHEET_W, "hem_mm": SHUTTER_HEM, "length_mm": SHEET_W - SHUTTER_HEM,
                "max_cover_mm": SHEET_H / 2.0},
    }
    return {"page_mm": [PAGE_W, PAGE_H], "footprint_mm": [PAGE_W + 2 * OVERHANG, PAGE_H], "rails": rails,
            "corner": corner, "shutters": shutters}


def corner_stack_nominal_mm():
    """Thickness the outside rail's clip must take at a corner: the inside rail's lip and body layers plus
    the page, with the folds pressed flat. Nominal, from the assumed sheet thickness."""
    return (1 + N_LAYERS + 1) * SHEET_THICKNESS


def check_layout():
    layout = frame_layout()
    # Every rail's body stays inside the page's text margin.
    assert BODY <= TEXT_MARGIN, (BODY, TEXT_MARGIN)
    # A shutter's sheet is exactly long enough to span between opposite pockets and enter both by POCKET_DEPTH;
    # the hem is what gives it room to slide.
    for name, s in layout["shutters"].items():
        assert abs(s["span_between_pocket_mouths_mm"] + 2 * POCKET_DEPTH - s["sheet_length_mm"]) < 1e-9, name
        assert 0 < s["hem_mm"] < POCKET_DEPTH / 2 and s["length_mm"] == s["sheet_length_mm"] - s["hem_mm"], name
    # Two shutters from opposite sides can cover the whole page between them.
    assert 2 * layout["shutters"]["side"]["max_cover_mm"] >= PAGE_W
    assert 2 * layout["shutters"]["top"]["max_cover_mm"] >= PAGE_H
    # The corner stack fits the clip with room to spare.
    assert layout["corner"]["stack_nominal_mm"] <= 0.75 * WALL, (layout["corner"]["stack_nominal_mm"], WALL)
    # Side rails run the page's full height; top and bottom rails overhang symmetrically.
    assert layout["rails"]["left"]["span_mm"] == [0.0, PAGE_H]
    assert abs(layout["rails"]["top"]["span_mm"][0] + OVERHANG) < 1e-9
    return layout


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
        "frame_footprint_mm": (PAGE_W + 2 * OVERHANG, PAGE_H),
        "top_and_bottom_rail_overhang_mm": OVERHANG,
        "corner_stack_nominal_mm": corner_stack_nominal_mm(),
        "corner_clip_opening_mm": WALL,
    }


if __name__ == "__main__":
    check_layout()
    for key, value in summary().items():
        print(f"{key:32} {value}")
    print("rail creases from the lip edge:")
    for y, kind, angle, role in rail_creases():
        print(f"  {y:7.2f} mm  {kind}  {angle:+6.1f}  {role}")
    print("corner joint:", frame_layout()["corner"]["joint"])
