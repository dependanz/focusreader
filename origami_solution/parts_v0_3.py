"""Single source of truth for the origami_solution v0.3 frame reader geometry.

v0.3 keeps v0.2's parts and joints and changes which rails are outside at the corners, so that the top and
bottom shutters can hang off the page instead of being trapped on it. All millimetres.

Why. In v0.2 the top and bottom rails were the outside rails, clipping over the side rails' ends. A shutter
riding in the side rails' pockets then passes through the corner inside the top rail's clip, and the top
rail's wall stands in its way: it can never leave the page. Extending the side rails with a second sheet
does not help either, because any fold-only splice stacks one sheet on the other and puts a step in the
pocket floor that a sliding shutter end would catch on. v0.3 turns the corner around: the side rails are the
outside rails, their pockets run above the top and bottom rails, and a top or bottom shutter can slide as
far off the page as it likes while the part of its ends still on the page stays gripped in the side rails'
pockets. The top and bottom rails must then fit between the side rails' walls, so they are folded across the
other way, 210 mm long with eleven body layers and a tuck.

Parts, every one a whole A4 sheet folded:
    side rail x2     v0.2's rail: 297 mm long, a 12 mm lip, a 2 mm wall, eight 24.5 mm body layers; outside
                     at the corners
    end rail x2      210 mm long, the same lip and wall, eleven 24.5 mm body layers and a 13.5 mm tuck; the
                     top and bottom rails, inside the side rails' clips at the corners
    top/bottom shutter x2   A4 folded in half across, 210 x 148.5 mm, 3 mm hem, ends in the side rails' pockets
    side shutter x2  optional: A4 folded in quarters along its length, 297 x 52.5 mm, 3 mm hem, ends in the
                     end rails' pockets; they cannot leave the page, so they are narrow and can be left out

Shutter travel. A top or bottom shutter holds as long as at least ENGAGE_MIN of its ends is still on the
page inside the side rails' pockets. The bottom shutter can therefore cover from any reading line down to
the page's bottom with the rest hanging off, and the top shutter can retract until only the top margin is
covered. Whether ENGAGE_MIN is enough is for the simulation and then paper to say.

Nothing here has been folded. Every number is a design value, and SHEET_THICKNESS is assumed.
"""
from parts_v0_2 import (BODY, FULL, LIP, N_LAYERS, POCKET_DEPTH, POCKET_LAYERS, RIGHT, SHEET_H,
                        SHEET_THICKNESS, SHEET_W, SHUTTER_HEM, TEXT_MARGIN, WALL, rail_creases)

PAGE_W, PAGE_H = SHEET_W, SHEET_H
END_RAIL_LEN = SHEET_W                                  # 210, folded across the other way
END_RAIL_LAYERS = 11
END_RAIL_TUCK = SHEET_H - LIP - WALL - END_RAIL_LAYERS * BODY   # 13.5
SIDE_SHUTTER_FOLDS = 3                                  # quarters: 4 layers of 52.5 mm
ENGAGE_MIN = 20.0                                       # the least of a shutter end that must stay in a pocket


def side_rail_creases():
    return rail_creases()


def end_rail_creases():
    """Like the side rail but folded across the 297 mm side: eleven body layers and a tuck folded onto the
    stack. The pocket is still between body layers 2 and 3."""
    creases = [(LIP, "M", -RIGHT, "wall"), (LIP + WALL, "M", -RIGHT, "wall")]
    for k in range(1, END_RAIL_LAYERS):
        y = LIP + WALL + k * BODY
        if k % 2 == 1:
            creases.append((round(y, 6), "V", FULL, "inner_fold"))
        elif k == POCKET_LAYERS[0]:
            creases.append((round(y, 6), "M", -FULL, "pocket"))
        else:
            creases.append((round(y, 6), "M", -FULL, "outer_fold"))
    y = LIP + WALL + END_RAIL_LAYERS * BODY
    creases.append((round(y, 6), "V", FULL, "tuck"))    # layer 11 heads inward, so its inner end folds a valley
    return creases


def end_rail_layers():
    return {k: (round(LIP + WALL + (k - 1) * BODY, 6), round(LIP + WALL + k * BODY, 6)) for k in range(1, END_RAIL_LAYERS + 1)}


def top_shutter_creases():
    return SHEET_W, SHEET_H, [(SHEET_H / 2.0, "V", FULL, "double_fold")]


def side_shutter_creases():
    """Folded in quarters along the length: three creases 52.5 mm apart, alternating so the four layers stack."""
    w, h = SHEET_H, SHEET_W
    pitch = h / (SIDE_SHUTTER_FOLDS + 1)
    return w, h, [(round(pitch * (k + 1), 6), "V" if k % 2 == 0 else "M", FULL if k % 2 == 0 else -FULL, "quarter_fold")
                  for k in range(SIDE_SHUTTER_FOLDS)]


def corner_stack_nominal_mm():
    """What the side rail's clip must take at a corner: the end rail's lip, its body layers and the page."""
    return (1 + END_RAIL_LAYERS + 1) * SHEET_THICKNESS


def frame_layout():
    rails = {
        "left": {"part": "side_rail", "runs_along": "y", "page_edge": "x = 0", "span_mm": [0.0, PAGE_H],
                 "body_over_page_mm": BODY, "corner_role": "outside", "length_mm": SHEET_H, "body_layers": N_LAYERS},
        "right": {"part": "side_rail", "runs_along": "y", "page_edge": f"x = {PAGE_W:g}", "span_mm": [0.0, PAGE_H],
                  "body_over_page_mm": BODY, "corner_role": "outside", "length_mm": SHEET_H, "body_layers": N_LAYERS},
        "top": {"part": "end_rail", "runs_along": "x", "page_edge": "y = 0", "span_mm": [0.0, PAGE_W],
                "body_over_page_mm": BODY, "corner_role": "inside", "length_mm": END_RAIL_LEN, "body_layers": END_RAIL_LAYERS},
        "bottom": {"part": "end_rail", "runs_along": "x", "page_edge": f"y = {PAGE_H:g}", "span_mm": [0.0, PAGE_W],
                   "body_over_page_mm": BODY, "corner_role": "inside", "length_mm": END_RAIL_LEN, "body_layers": END_RAIL_LAYERS},
    }
    corner = {
        "joint": "the end rail's end sits inside the side rail's clip, between its lip and body layer 1, over the "
                 "page's corner",
        "depth_mm": BODY,
        "stack_from_below": ["side rail lip", "end rail lip", "page", f"end rail body, {END_RAIL_LAYERS} layers",
                             "side rail body"],
        "stack_nominal_mm": corner_stack_nominal_mm(),
        "clip_opening_mm": WALL,
        "assembly_order": "clip the top and bottom rails onto the page first, then the side rails over their ends",
    }
    shutters = {
        "top": {"ends_in": ["left", "right"], "span_between_pocket_mouths_mm": PAGE_W - 2 * BODY,
                "sheet_length_mm": SHEET_W, "hem_mm": SHUTTER_HEM, "length_mm": SHEET_W - SHUTTER_HEM,
                "cover_mm": SHEET_H / 2.0, "layers": 2, "may_leave_page": True, "engage_min_mm": ENGAGE_MIN},
        "side": {"ends_in": ["top", "bottom"], "span_between_pocket_mouths_mm": PAGE_H - 2 * BODY,
                 "sheet_length_mm": SHEET_H, "hem_mm": SHUTTER_HEM, "length_mm": SHEET_H - SHUTTER_HEM,
                 "cover_mm": SHEET_W / (SIDE_SHUTTER_FOLDS + 1), "layers": SIDE_SHUTTER_FOLDS + 1,
                 "may_leave_page": False, "optional": True},
    }
    travel = {
        "reading_line_range_mm": [0.0, PAGE_H - ENGAGE_MIN],
        "window_top_range_mm": [ENGAGE_MIN, PAGE_H],
        "side_cover_min_mm": shutters["side"]["cover_mm"],
    }
    return {"version": "0.3", "page_mm": [PAGE_W, PAGE_H], "footprint_mm": [PAGE_W, PAGE_H], "rails": rails,
            "corner": corner, "shutters": shutters, "travel": travel}


def check_layout():
    layout = frame_layout()
    assert BODY <= TEXT_MARGIN
    assert abs(END_RAIL_TUCK - 13.5) < 1e-9 and LIP + WALL + END_RAIL_LAYERS * BODY + END_RAIL_TUCK == SHEET_H
    for name, s in layout["shutters"].items():
        assert abs(s["span_between_pocket_mouths_mm"] + 2 * POCKET_DEPTH - s["sheet_length_mm"]) < 1e-9, name
        assert s["length_mm"] == s["sheet_length_mm"] - s["hem_mm"]
    # Two top or bottom shutters cover the page's height between them, and the bottom margin lies within reach.
    assert 2 * layout["shutters"]["top"]["cover_mm"] >= PAGE_H
    assert layout["travel"]["reading_line_range_mm"][1] >= PAGE_H - TEXT_MARGIN
    assert layout["travel"]["window_top_range_mm"][0] <= TEXT_MARGIN
    # The corner stack fits the clip with room to spare.
    assert layout["corner"]["stack_nominal_mm"] <= 0.75 * WALL, (layout["corner"]["stack_nominal_mm"], WALL)
    # End rails fit exactly between the side rails' walls.
    assert layout["rails"]["top"]["length_mm"] == PAGE_W
    return layout


def summary():
    return {
        "sheets_per_device": 6, "sheets_with_side_shutters": 8,
        "side_rail": f"297 mm, {N_LAYERS} layers", "end_rail": f"210 mm, {END_RAIL_LAYERS} layers, {END_RAIL_TUCK:g} mm tuck",
        "top_bottom_shutter_mm": (SHEET_W, SHEET_H / 2.0), "side_shutter_mm": (SHEET_H, SHEET_W / (SIDE_SHUTTER_FOLDS + 1)),
        "folds_per_device": 2 * len(side_rail_creases()) + 2 * len(end_rail_creases()) + 2 * 1,
        "folds_with_side_shutters": 2 * len(side_rail_creases()) + 2 * len(end_rail_creases()) + 2 * 1 + 2 * SIDE_SHUTTER_FOLDS,
        "frame_footprint_mm": (PAGE_W, PAGE_H), "corner_stack_nominal_mm": corner_stack_nominal_mm(),
        "engage_min_mm": ENGAGE_MIN, "reading_line_range_mm": (0.0, PAGE_H - ENGAGE_MIN),
    }


if __name__ == "__main__":
    check_layout()
    for key, value in summary().items():
        print(f"{key:30} {value}")
    print("end rail creases from the lip edge:")
    for y, kind, angle, role in end_rail_creases():
        print(f"  {y:7.2f} mm  {kind}  {angle:+6.1f}  {role}")
