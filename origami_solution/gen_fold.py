"""Emit the pleat-shutter crease pattern as a FOLD file.

FOLD is the JSON interchange format for origami crease patterns. Emitting it makes this
pattern loadable by Origami Simulator (which imports FOLD directly), Rabbit Ear, and
bar-and-hinge structural solvers.

This buys interoperability and a kinematic sanity check. It is NOT functional evidence.
Every crease here spans the full sheet width, so the pattern has no interior vertices and
flat-foldability is automatic -- a simulator will confirm only that a parallel accordion
opens and closes, which is already known. The failure modes that matter (spring-back,
inter-layer friction, crease fatigue) are not represented by any of those tools.

Run from this directory:
    python gen_fold.py
"""
import json
import pathlib

from pattern import SHEET_W, SHEET_H, all_creases, zone_summary

OUT = pathlib.Path(__file__).resolve().parent / \
    "focusreader_origami_pleat_shutter_v0_1.fold"

# FOLD fold angles in degrees: valleys positive, mountains negative.
# +/-180 is the fully collapsed target state. Origami Simulator's fold-percent slider
# interpolates from flat, so the partially collapsed operating states come for free.
FOLD_ANGLE = {"V": 180.0, "M": -180.0}


def build():
    creases = all_creases()
    # Distinct horizontal lines: sheet edges plus every crease.
    ys = sorted({0.0, SHEET_H} | {y for y, _ in creases})
    assignment_at = {y: kind for y, kind in creases}

    # Two vertices per horizontal line, at the left and right sheet edges.
    vertices, index = [], {}
    for y in ys:
        for x in (0.0, SHEET_W):
            index[(x, y)] = len(vertices)
            vertices.append([x, y])

    edges, assigns, angles = [], [], []

    def add(v1, v2, kind):
        edges.append([v1, v2])
        assigns.append(kind)
        angles.append(FOLD_ANGLE.get(kind, 0.0))

    # Horizontal edges: creases in the interior, boundary at the sheet edges.
    for y in ys:
        left, right = index[(0.0, y)], index[(SHEET_W, y)]
        add(left, right, assignment_at.get(y, "B"))

    # Vertical boundary edges, split at every horizontal line.
    for x in (0.0, SHEET_W):
        for lower, upper in zip(ys, ys[1:]):
            add(index[(x, lower)], index[(x, upper)], "B")

    # Faces: one rectangle per strip, counter-clockwise in a y-down frame.
    faces = []
    for lower, upper in zip(ys, ys[1:]):
        faces.append([
            index[(0.0, lower)],
            index[(0.0, upper)],
            index[(SHEET_W, upper)],
            index[(SHEET_W, lower)],
        ])

    return {
        "file_spec": 1.1,
        "file_creator": "focusreader origami_solution gen_fold.py",
        "file_classes": ["singleModel"],
        "frame_title": "FocusReader pleat shutter v0.1 crease pattern",
        "frame_classes": ["creasePattern"],
        "frame_attributes": ["2D"],
        "frame_description": (
            "Fold-only paper reading guard, A4 210x297 mm. Untested: nothing has been "
            "printed or folded. No interior vertices, so flat-foldability is automatic "
            "and carries no information. Position holding depends on inter-layer "
            "friction, which no bar-and-hinge model represents."
        ),
        "vertices_coords": vertices,
        "edges_vertices": edges,
        "edges_assignment": assigns,
        "edges_foldAngle": angles,
        "faces_vertices": faces,
    }


def check(fold):
    """Structural checks on the emitted file, so a malformed export cannot pass as valid."""
    nv = len(fold["vertices_coords"])
    ne = len(fold["edges_vertices"])
    assert len(fold["edges_assignment"]) == ne
    assert len(fold["edges_foldAngle"]) == ne
    for v in fold["vertices_coords"]:
        assert 0.0 <= v[0] <= SHEET_W and 0.0 <= v[1] <= SHEET_H, v
    for a, b in fold["edges_vertices"]:
        assert 0 <= a < nv and 0 <= b < nv and a != b
    for f in fold["faces_vertices"]:
        assert len(f) == 4 and len(set(f)) == 4
    # Every interior crease must be a fold; every sheet-edge run must be boundary.
    folds = [k for k in fold["edges_assignment"] if k in ("M", "V")]
    assert len(folds) == len(all_creases()), (len(folds), len(all_creases()))
    # Adjacent pleat creases must alternate, or the accordion cannot zigzag.
    pleats = [k for y, k in all_creases()][:-1]
    assert all(x != y for x, y in zip(pleats, pleats[1:])), "pleat creases do not alternate"
    return nv, ne, len(fold["faces_vertices"]), len(folds)


if __name__ == "__main__":
    fold = build()
    nv, ne, nf, nfolds = check(fold)
    OUT.write_text(json.dumps(fold, indent=1) + "\n", encoding="utf-8")
    s = zone_summary()
    print(f"vertices={nv} edges={ne} faces={nf} folds={nfolds}")
    print(f"expected folds={s['total_folds']} "
          f"(valley={s['valley']} mountain={s['mountain']})")
    print(f"wrote {OUT.name} ({OUT.stat().st_size} bytes)")
