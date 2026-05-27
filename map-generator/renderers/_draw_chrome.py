"""Title banner and legend drawing for the Rusting Reach style."""
from __future__ import annotations

from PIL import ImageDraw

from core.map_graph import MapGraph
from renderers._colors import (
    SLAB_DARK, TITLE_GOLD, SUBTITLE_GREY, LEGEND_TEXT, NODE_COLORS, MARKER_OUTLINE
)
from renderers._fonts import load as load_font

_LEGEND_LABELS: dict[str, str] = {
    # Area map
    "entry":         "Entry Point",
    "encounter":     "Encounter",
    "environmental": "Environmental Hazard",
    "scrap_guarded": "Scrap (Guarded)",
    "scrap_open":    "Scrap (Open)",
    "special":       "Special",
    # Region map
    "settlement":    "Settlement",
    "threat":        "Threat",
    "area":          "Area",
}


def draw_title(
    draw: ImageDraw.ImageDraw,
    graph: MapGraph,
    scale: float,
) -> None:
    title_font = load_font(max(12, int(34 * scale)))
    subtitle_font = load_font(max(8, int(20 * scale)))
    pad = max(4, int(12 * scale))

    t_bbox = draw.textbbox((0, 0), graph.title, font=title_font)
    s_bbox = draw.textbbox((0, 0), graph.subtitle, font=subtitle_font)
    slab_w = max(t_bbox[2], s_bbox[2]) + pad * 2
    slab_h = (t_bbox[3] - t_bbox[1]) + (s_bbox[3] - s_bbox[1]) + pad * 3

    draw.rectangle([pad // 2, pad // 2, pad // 2 + slab_w, pad // 2 + slab_h], fill=SLAB_DARK)
    draw.text((pad, pad), graph.title, font=title_font, fill=TITLE_GOLD)
    title_h = t_bbox[3] - t_bbox[1]
    draw.text((pad, pad + title_h + pad // 2), graph.subtitle, font=subtitle_font, fill=SUBTITLE_GREY)


def draw_legend(
    draw: ImageDraw.ImageDraw,
    graph: MapGraph,
    width: int,
    height: int,
    scale: float,
) -> None:
    present_types = graph.present_types()
    if not present_types:
        return

    header_font = load_font(max(8, int(20 * scale)))
    row_font = load_font(max(7, int(18 * scale)))
    pad = max(3, int(10 * scale))
    dot_r = max(4, int(9 * scale))
    row_h = max(14, int(28 * scale))

    header_bbox = draw.textbbox((0, 0), "LEGEND", font=header_font)
    header_h = header_bbox[3] - header_bbox[1]

    max_label = max((_LEGEND_LABELS.get(t, t) for t in present_types), key=len)
    label_bbox = draw.textbbox((0, 0), max_label, font=row_font)
    label_w = label_bbox[2] - label_bbox[0]

    slab_w = dot_r * 2 + pad * 3 + label_w + pad
    slab_h = header_h + pad + len(present_types) * row_h + pad * 2

    x0 = width - slab_w - pad
    y0 = height - slab_h - pad

    draw.rectangle([x0, y0, x0 + slab_w, y0 + slab_h], fill=SLAB_DARK)
    draw.text((x0 + pad, y0 + pad), "LEGEND", font=header_font, fill=TITLE_GOLD)

    for i, node_type in enumerate(present_types):
        row_y = y0 + pad + header_h + pad + i * row_h
        cx = x0 + pad + dot_r
        cy = row_y + row_h // 2
        color = NODE_COLORS.get(node_type, NODE_COLORS["scrap_open"])
        draw.ellipse([cx - dot_r, cy - dot_r, cx + dot_r, cy + dot_r], fill=color, outline=MARKER_OUTLINE)
        label = _LEGEND_LABELS.get(node_type, node_type)
        draw.text((cx + dot_r + pad, cy - row_h // 4), label, font=row_font, fill=LEGEND_TEXT)
