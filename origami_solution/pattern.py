"""Single source of truth for the origami_solution pleat-shutter geometry.

Every generator and analysis imports from here so the SVG, the FOLD export, and the
kinematics curve cannot drift apart. Editing a number here changes all of them.

Geometry, y measured from the SHEET TOP, all millimetres:
    y = 0                       free top edge = reading edge when fully extended
    y = FIELD_TOP..FIELD_BOT    pleat creases at PITCH, alternating valley/mountain
    y = FIELD_BOT..BAND_BOT     front band, lies flat on the page
    y = BAND_BOT                hinge crease (mountain), wraps the page's bottom edge
    y = BAND_BOT..SHEET_H       tuck flap, goes behind the page
"""

SHEET_W = 210.0
SHEET_H = 297.0

PITCH = 5.0
FIELD_TOP = 5.0
FIELD_BOT = 250.0
BAND_BOT = 277.0

# Assumed, not measured: nominal caliper of 80 gsm office paper.
SHEET_THICKNESS = 0.10

# 12 pt type at 1.15 line spacing. The indexing target for one pleat = one line.
TEXT_PITCH = 4.9


def pleat_creases(pitch=PITCH, first=FIELD_TOP, last=FIELD_BOT):
    """Pleat creases top-to-bottom as (y, 'V'|'M'). The first is a valley so the free
    top edge sits slightly proud of the page and casts a shadow at the reading line."""
    out = []
    y, k = first, 0
    while y <= last + 1e-9:
        out.append((round(y, 6), "V" if k % 2 == 0 else "M"))
        y = first + pitch * (k + 1)
        k += 1
    return out


def hinge_crease():
    """The hinge wraps the page's bottom edge. Seen from the reader's side the visible
    face lies on the outside of the fold, so it is a mountain."""
    return (BAND_BOT, "M")


def all_creases(pitch=PITCH):
    return pleat_creases(pitch) + [hinge_crease()]


def field_length(pitch=PITCH):
    """In-page extent of the fully extended pleat field."""
    return len(pleat_creases(pitch)) * pitch


def front_band_height():
    return BAND_BOT - FIELD_BOT


def tuck_flap_height():
    return SHEET_H - BAND_BOT


def zone_summary(pitch=PITCH):
    creases = pleat_creases(pitch)
    return {
        "sheet": (SHEET_W, SHEET_H),
        "pitch": pitch,
        "pleat_creases": len(creases),
        "valley": sum(1 for _, k in creases if k == "V"),
        "mountain": sum(1 for _, k in creases if k == "M") + 1,
        "total_folds": len(creases) + 1,
        "field_length": field_length(pitch),
        "front_band": front_band_height(),
        "tuck_flap": tuck_flap_height(),
    }


if __name__ == "__main__":
    for key, value in zone_summary().items():
        print(f"{key:16} {value}")
