"""Color constants for the Rusting Reach map style."""
from typing import Final

RGBA = tuple[int, int, int, int]

BACKGROUND: Final[RGBA] = (18, 16, 14, 255)
SLAB_DARK: Final[RGBA] = (15, 15, 15, 210)
TITLE_GOLD: Final[RGBA] = (220, 180, 80, 255)
SUBTITLE_GREY: Final[RGBA] = (200, 200, 200, 255)
LEGEND_TEXT: Final[RGBA] = (220, 220, 220, 255)
MARKER_OUTLINE: Final[RGBA] = (20, 20, 20, 255)
MARKER_NUMERAL: Final[RGBA] = (240, 235, 225, 255)
MARKER_HALO: Final[RGBA] = (0, 0, 0, 140)
ROAD_UNDERLAY: Final[RGBA] = (255, 240, 210, 90)
ROAD_OVERLAY: Final[RGBA] = (60, 40, 25, 220)
LABEL_SLAB: Final[RGBA] = (15, 15, 15, 200)

NODE_COLORS: Final[dict[str, RGBA]] = {
    # ── Area map types ───────────────────────────────────────────────────
    "entry":         (100, 130, 155, 255),   # steel blue-grey
    "encounter":     (185,  45,  35, 255),   # blood red
    "environmental": (155, 175,  45, 255),   # toxic yellow-green
    "scrap_guarded": (200, 145,  35, 255),   # amber
    "scrap_open":    (165, 155, 110, 255),   # dusty tan
    "special":       (120,  75, 175, 255),   # purple
    # ── Region map types ─────────────────────────────────────────────────
    "settlement":    (210, 175,  55, 255),   # gold   (original SU overlay style)
    "threat":        (190,  50,  50, 255),   # blood red
    "area":          (180, 180, 185, 255),   # steel grey
}
