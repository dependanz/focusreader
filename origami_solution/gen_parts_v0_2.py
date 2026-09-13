"""Emit the v0.2 frame reader parts as FOLD files, each with a sidecar naming its creases' roles.

FOLD carries the crease pattern: vertices, edges, mountain/valley assignments and fold angles. It has
no field for what a crease is for, and the simulation bridge needs to know which fold is the shutter
pocket, so that goes in a sidecar JSON beside each FOLD file rather than in a private FOLD dialect.

Run from this directory:
    python gen_parts_v0_2.py

Writes rail_v0_2.fold, shutter_side_v0_2.fold, shutter_top_v0_2.fold and a .parts.json beside each.
This is design output, not evidence: nothing has been folded.
"""
import json
import pathlib

from parts_v0_2 import (BODY, LIP, N_LAYERS, POCKET_DEPTH, POCKET_LAYERS, SHEET_H, SHEET_W, WALL,
                        check_layout, rail_creases, rail_layers, shutter_creases, summary)

HERE = pathlib.Path(__file__).resolve().parent


def parallel_crease_fold(w, h, creases, title, description):
    """A FOLD file for a sheet whose creases all run parallel to x across the full width."""
    ys = sorted({0.0, h} | {y for y, _, _, _ in creases})
    at = {y: (kind, angle) for y, kind, angle, _ in creases}
    vertices, index = [], {}
    for y in ys:
        for x in (0.0, w):
            index[(x, y)] = len(vertices)
            vertices.append([x, y])
    edges, assigns, angles = [], [], []

    def add(a, b, kind, angle):
        edges.append([a, b])
        assigns.append(kind)
        angles.append(angle)

    for y in ys:
        kind, angle = at.get(y, ("B", 0.0))
        add(index[(0.0, y)], index[(w, y)], kind, angle)
    for x in (0.0, w):
        for lower, upper in zip(ys, ys[1:]):
            add(index[(x, lower)], index[(x, upper)], "B", 0.0)
    faces = [[index[(0.0, lo)], index[(0.0, up)], index[(w, up)], index[(w, lo)]]
             for lo, up in zip(ys, ys[1:])]
    return {
        "file_spec": 1.1,
        "file_creator": "focusreader origami_solution gen_parts_v0_2.py",
        "file_classes": ["singleModel"],
        "frame_title": title,
        "frame_classes": ["creasePattern"],
        "frame_attributes": ["2D"],
        "frame_description": description,
        "vertices_coords": vertices,
        "edges_vertices": edges,
        "edges_assignment": assigns,
        "edges_foldAngle": angles,
        "faces_vertices": faces,
    }


def check(fold, w, h, creases):
    nv, ne = len(fold["vertices_coords"]), len(fold["edges_vertices"])
    assert len(fold["edges_assignment"]) == ne and len(fold["edges_foldAngle"]) == ne
    for v in fold["vertices_coords"]:
        assert 0.0 <= v[0] <= w and 0.0 <= v[1] <= h, v
    for a, b in fold["edges_vertices"]:
        assert 0 <= a < nv and 0 <= b < nv and a != b
    for f in fold["faces_vertices"]:
        assert len(f) == 4 and len(set(f)) == 4
    folds = [(k, a) for k, a in zip(fold["edges_assignment"], fold["edges_foldAngle"]) if k in "MV"]
    assert len(folds) == len(creases), (len(folds), len(creases))
    assert all((a > 0) == (k == "V") for k, a in folds), "fold angle sign disagrees with assignment"
    return nv, ne, len(fold["faces_vertices"]), len(folds)


def write(name, w, h, creases, title, description, sidecar):
    fold = parallel_crease_fold(w, h, creases, title, description)
    nv, ne, nf, nfolds = check(fold, w, h, creases)
    path = HERE / f"{name}.fold"
    path.write_text(json.dumps(fold, indent=1) + "\n", encoding="utf-8")
    sidecar = dict(sidecar)
    sidecar["fold_file"] = path.name
    sidecar["creases"] = [{"y_mm": y, "assignment": k, "fold_angle_deg": a, "role": r}
                          for y, k, a, r in creases]
    (HERE / f"{name}.parts.json").write_text(json.dumps(sidecar, indent=1) + "\n", encoding="utf-8")
    print(f"{path.name}: {nv} vertices, {ne} edges, {nf} faces, {nfolds} folds; sidecar written")


if __name__ == "__main__":
    rail = rail_creases()
    write("rail_v0_2", SHEET_H, SHEET_W, [(y, k, a, r) for y, k, a, r in rail],
          "FocusReader frame reader v0.2 rail",
          "One A4 sheet folded across its width into a 297 mm rail: a lip under the page, a two-crease "
          "wall at the page's edge, and eight body layers folded back and forth. The fold between "
          "body layers 2 and 3 is at the outer edge, so their pocket opens toward the page's centre "
          "for a shutter end. Design only; nothing folded or measured.",
          {"part": "rail", "sheet_mm": [SHEET_H, SHEET_W], "lip_mm": LIP, "wall_mm": WALL,
           "body_layers": N_LAYERS, "body_mm": BODY, "layers_mm": rail_layers(),
           "pocket_layers": list(POCKET_LAYERS), "pocket_depth_mm": POCKET_DEPTH,
           "crease_axis": "creases run along the 297 mm length; positions are measured from the lip edge"})
    for orientation in ("side", "top"):
        w, h, creases = shutter_creases(orientation)
        write(f"shutter_{orientation}_v0_2", w, h, creases,
              f"FocusReader frame reader v0.2 {orientation} shutter",
              "One A4 sheet folded in half for opacity. The fold is the window edge; the two open ends "
              "slide into rail pockets. Design only; nothing folded or measured.",
              {"part": f"shutter_{orientation}", "sheet_mm": [w, h], "panel_mm": [w, h / 2.0],
               "end_in_pocket_mm": POCKET_DEPTH})
    # The frame is an assembly of the parts above, not a sheet, so it has no FOLD file: the layout sidecar
    # says where each rail sits, how the corners join, and which pockets each shutter's ends use.
    layout = check_layout()
    layout["part"] = "frame"
    (HERE / "frame_v0_2.parts.json").write_text(json.dumps(layout, indent=1) + "\n", encoding="utf-8")
    print("frame_v0_2.parts.json: layout checked and written")
    for key, value in summary().items():
        print(f"{key:32} {value}")
