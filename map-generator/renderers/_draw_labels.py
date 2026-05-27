"""Location label drawing with multi-direction collision avoidance."""
from __future__ import annotations

from PIL import ImageDraw

from core.map_graph import MapGraph
from core.node import LocationNode
from renderers._colors import NODE_COLORS, LABEL_SLAB
from renderers._fonts import load as load_font

_SCRAP_LABEL_TYPES: frozenset[str] = frozenset({"scrap_guarded", "scrap_open", "area"})

_Rect = tuple[int, int, int, int]  # x1, y1, x2, y2


def _rects_overlap(a: _Rect, b: _Rect) -> bool:
    return a[0] < b[2] and a[2] > b[0] and a[1] < b[3] and a[3] > b[1]


_ROAD_BLEED = 8  # px extra slab overhang toward the node to cover road underlay


def _candidate_rects(
    cx: int,
    cy: int,
    tw: int,
    th: int,
    radius: int,
    pad: int,
) -> list[_Rect]:
    """Ordered placements: right, left, below-right, above-right, below-left, above-left.
    Each slab extends _ROAD_BLEED px toward the node to cover the road underlay line."""
    rw = tw + pad * 2
    rh = th + pad * 2
    gap = radius + 6
    b = _ROAD_BLEED
    return [
        (cx + gap - b,          cy - rh // 2, cx + gap + rw,              cy + rh // 2),  # right
        (cx - gap - rw,         cy - rh // 2, cx - gap + b,               cy + rh // 2),  # left
        (cx + gap - b,          cy,           cx + gap + rw,              cy + rh),        # below-right
        (cx + gap - b,          cy - rh,      cx + gap + rw,              cy),             # above-right
        (cx - gap - rw,         cy,           cx - gap + b,               cy + rh),        # below-left
        (cx - gap - rw,         cy - rh,      cx - gap + b,               cy),             # above-left
    ]


def _clamp_rect(rect: _Rect, width: int, height: int) -> _Rect:
    x1, y1, x2, y2 = rect
    rw = x2 - x1
    rh = y2 - y1
    x1 = max(4, min(width - rw - 4, x1))
    y1 = max(4, min(height - rh - 4, y1))
    return (x1, y1, x1 + rw, y1 + rh)


def _label_text(node: LocationNode) -> str:
    if node.type in _SCRAP_LABEL_TYPES and node.scrap_value > 0:
        return f"{node.name} [{node.scrap_value}sc]"
    return node.name


def draw_labels(
    draw: ImageDraw.ImageDraw,
    graph: MapGraph,
    width: int,
    height: int,
    radius: int,
    scale: float,
) -> None:
    font = load_font(max(8, int(20 * scale)))
    pad = max(2, int(6 * scale))

    # Reserve the legend zone (bottom-right ~32% × 26%) as a blocked rect
    legend_w = int(width * 0.32)
    legend_h = int(height * 0.26)
    blocked: list[_Rect] = [
        (width - legend_w - pad, height - legend_h - pad, width - pad, height - pad)
    ]
    placed: list[_Rect] = []

    for node in graph.nodes:
        cx = int(node.x * width)
        cy = int(node.y * height)
        color = NODE_COLORS.get(node.type, NODE_COLORS["scrap_open"])
        label = _label_text(node)

        bbox = draw.textbbox((0, 0), label, font=font)
        tw = bbox[2] - bbox[0]
        th = bbox[3] - bbox[1]

        chosen = _pick_rect(cx, cy, tw, th, radius, pad, width, height, placed + blocked)
        placed.append(chosen)

        draw.rectangle(list(chosen), fill=LABEL_SLAB)
        # Text starts at pad + bleed from the slab left edge; compensate for font bearing
        draw.text(
            (chosen[0] + pad + _ROAD_BLEED - bbox[0], chosen[1] + pad - bbox[1]),
            label,
            font=font,
            fill=color,
        )


def _pick_rect(
    cx: int,
    cy: int,
    tw: int,
    th: int,
    radius: int,
    pad: int,
    width: int,
    height: int,
    occupied: list[_Rect],
) -> _Rect:
    for candidate in _candidate_rects(cx, cy, tw, th, radius, pad):
        clamped = _clamp_rect(candidate, width, height)
        if not any(_rects_overlap(clamped, r) for r in occupied):
            return clamped
    # All positions conflict — use clamped right-side as fallback
    fallback = _candidate_rects(cx, cy, tw, th, radius, pad)[0]
    return _clamp_rect(fallback, width, height)
