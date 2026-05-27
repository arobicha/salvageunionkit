"""Two-pass road drawing for the Rusting Reach style."""
from __future__ import annotations

from PIL import ImageDraw

from core.map_graph import MapGraph
from renderers._colors import ROAD_UNDERLAY, ROAD_OVERLAY


def draw_roads(
    draw: ImageDraw.ImageDraw,
    graph: MapGraph,
    width: int,
    height: int,
    scale: float,
) -> None:
    node_px = {n.id: (int(n.x * width), int(n.y * height)) for n in graph.nodes}

    for edge in graph.edges:
        src = node_px.get(edge.source_id)
        dst = node_px.get(edge.target_id)
        if src is None or dst is None:
            continue

        underlay_width = max(1, int(11 * scale))
        draw.line([src, dst], fill=ROAD_UNDERLAY, width=underlay_width)

    for edge in graph.edges:
        src = node_px.get(edge.source_id)
        dst = node_px.get(edge.target_id)
        if src is None or dst is None:
            continue

        _dashed_line(draw, src, dst, scale)


def _dashed_line(
    draw: ImageDraw.ImageDraw,
    start: tuple[int, int],
    end: tuple[int, int],
    scale: float,
) -> None:
    import math

    dx = end[0] - start[0]
    dy = end[1] - start[1]
    length = math.hypot(dx, dy)
    if length == 0:
        return

    dash = int(16 * scale)
    gap = int(12 * scale)
    step = dash + gap
    ux, uy = dx / length, dy / length
    overlay_w = max(1, int(5 * scale))

    pos = 0.0
    while pos < length:
        d_start = pos
        d_end = min(pos + dash, length)
        x1 = int(start[0] + ux * d_start)
        y1 = int(start[1] + uy * d_start)
        x2 = int(start[0] + ux * d_end)
        y2 = int(start[1] + uy * d_end)
        draw.line([(x1, y1), (x2, y2)], fill=ROAD_OVERLAY, width=overlay_w)
        pos += step
