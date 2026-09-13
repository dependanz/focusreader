"""Emit the v0.3 frame reader parts as FOLD files with sidecars, and the frame layout sidecar.

Run from this directory:
    python gen_parts_v0_3.py

Writes side_rail_v0_3.fold, end_rail_v0_3.fold, shutter_top_v0_3.fold, shutter_side_v0_3.fold, a .parts.json
beside each, and frame_v0_3.parts.json. Design output, not evidence: nothing has been folded.
"""
import json
import pathlib

from gen_parts_v0_2 import check, parallel_crease_fold
from parts_v0_2 import BODY, LIP, N_LAYERS, POCKET_DEPTH, POCKET_LAYERS, SHEET_H, SHEET_W, WALL, rail_layers
from parts_v0_3 import (END_RAIL_LAYERS, END_RAIL_LEN, END_RAIL_TUCK, check_layout, end_rail_creases, end_rail_layers,
                        side_rail_creases, side_shutter_creases, summary, top_shutter_creases)

HERE = pathlib.Path(__file__).resolve().parent


def write(name, w, h, creases, title, description, sidecar):
    fold = parallel_crease_fold(w, h, creases, title, description)
    nv, ne, nf, nfolds = check(fold, w, h, creases)
    path = HERE / f"{name}.fold"
    path.write_text(json.dumps(fold, indent=1) + "\n", encoding="utf-8")
    sidecar = dict(sidecar)
    sidecar["fold_file"] = path.name
    sidecar["creases"] = [{"y_mm": y, "assignment": k, "fold_angle_deg": a, "role": r} for y, k, a, r in creases]
    (HERE / f"{name}.parts.json").write_text(json.dumps(sidecar, indent=1) + "\n", encoding="utf-8")
    print(f"{path.name}: {nv} vertices, {ne} edges, {nf} faces, {nfolds} folds; sidecar written")


if __name__ == "__main__":
    write("side_rail_v0_3", SHEET_H, SHEET_W, side_rail_creases(),
          "FocusReader frame reader v0.3 side rail",
          "v0.2's rail: one A4 folded across its width into a 297 mm rail with a lip, a two-crease wall and eight "
          "body layers. Outside at the corners in v0.3. Design only; nothing folded or measured.",
          {"part": "rail", "rail_kind": "side", "sheet_mm": [SHEET_H, SHEET_W], "lip_mm": LIP, "wall_mm": WALL,
           "body_layers": N_LAYERS, "body_mm": BODY, "layers_mm": rail_layers(), "pocket_layers": list(POCKET_LAYERS),
           "pocket_depth_mm": POCKET_DEPTH, "length_mm": SHEET_H,
           "crease_axis": "creases run along the 297 mm length; positions are measured from the lip edge"})
    write("end_rail_v0_3", END_RAIL_LEN, SHEET_H, end_rail_creases(),
          "FocusReader frame reader v0.3 end rail",
          "One A4 folded across its length into a 210 mm rail with the same lip and wall, eleven body layers and a "
          "13.5 mm tuck folded onto the stack. The top and bottom rails, inside the side rails' clips at the "
          "corners. Design only; nothing folded or measured.",
          {"part": "rail", "rail_kind": "end", "sheet_mm": [END_RAIL_LEN, SHEET_H], "lip_mm": LIP, "wall_mm": WALL,
           "body_layers": END_RAIL_LAYERS, "body_mm": BODY, "layers_mm": end_rail_layers(), "tuck_mm": END_RAIL_TUCK,
           "pocket_layers": list(POCKET_LAYERS), "pocket_depth_mm": POCKET_DEPTH, "length_mm": END_RAIL_LEN,
           "crease_axis": "creases run along the 210 mm length; positions are measured from the lip edge"})
    w, h, creases = top_shutter_creases()
    write("shutter_top_v0_3", w, h, creases, "FocusReader frame reader v0.3 top or bottom shutter",
          "One A4 folded in half across, with a 3 mm hem at one end. Its ends ride in the side rails' pockets and "
          "it may hang off the page. Design only; nothing folded or measured.",
          {"part": "shutter_top", "sheet_mm": [w, h], "panel_mm": [w, h / 2.0], "layers": 2, "end_in_pocket_mm": POCKET_DEPTH})
    w, h, creases = side_shutter_creases()
    write("shutter_side_v0_3", w, h, creases, "FocusReader frame reader v0.3 side shutter",
          "Optional. One A4 folded in quarters along its length, with a 3 mm hem at one end. Its ends ride in the "
          "top and bottom rails' pockets between the side rails' walls. Design only; nothing folded or measured.",
          {"part": "shutter_side", "sheet_mm": [w, h], "panel_mm": [w, h / 4.0], "layers": 4, "end_in_pocket_mm": POCKET_DEPTH})
    layout = check_layout()
    layout["part"] = "frame"
    (HERE / "frame_v0_3.parts.json").write_text(json.dumps(layout, indent=1) + "\n", encoding="utf-8")
    print("frame_v0_3.parts.json: layout checked and written")
    for key, value in summary().items():
        print(f"{key:30} {value}")
