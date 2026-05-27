"""Node marker drawing (halos, filled circles, numerals)."""
from __future__ import annotations

from PIL import ImageDraw

from core.map_graph import MapGraph
from renderers._colors import NODE_COLORS, MARKER_HALO, MARKER_OUTLINE, MARKER_NUMERAL
from renderers._fonts import load as load_font


def draw_halos(
    draw: ImageDraw.ImageDraw,
    graph: MapGraph,
    width: int,
    height: int,
    radius: int,
) -> None:
    halo_r = radius + max(1, int(5 * radius / 30))
    for node in graph.nodes:
        cx = int(node.x * width)
        cy = int(node.y * height)
        draw.ellipse(
            [cx - halo_r, cy - halo_r, cx + halo_r, cy + halo_r],
            fill=MARKER_HALO,
        )


def draw_markers(
    draw: ImageDraw.ImageDraw,
    graph: MapGraph,
    width: int,
    height: int,
    radius: int,
    scale: float,
) -> None:
    numeral_font = load_font(max(8, int(28 * scale)))
    outline_w = max(1, int(3 * scale))

    for idx, node in enumerate(graph.nodes, start=1):
        cx = int(node.x * width)
        cy = int(node.y * height)
        color = NODE_COLORS.get(node.type, NODE_COLORS["scrap_open"])

        draw.ellipse(
            [cx - radius, cy - radius, cx + radius, cy + radius],
            fill=color,
            outline=MARKER_OUTLINE,
            width=outline_w,
        )

        numeral = str(idx)
        bbox = draw.textbbox((0, 0), numeral, font=numeral_font)
        tw = bbox[2] - bbox[0]
        th = bbox[3] - bbox[1]
        draw.text(
            (cx - tw // 2 - bbox[0], cy - th // 2 - bbox[1]),
            numeral,
            font=numeral_font,
            fill=MARKER_NUMERAL,
        )
