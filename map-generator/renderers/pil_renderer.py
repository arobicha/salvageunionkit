"""PNG export renderer — Rusting Reach map style."""
from __future__ import annotations

from PIL import Image, ImageDraw

from core.map_graph import MapGraph
from renderers.base import AbstractRenderer
from renderers._colors import BACKGROUND
from renderers._draw_roads import draw_roads
from renderers._draw_nodes import draw_halos, draw_markers
from renderers._draw_labels import draw_labels
from renderers._draw_chrome import draw_title, draw_legend


class PilRenderer(AbstractRenderer):
    def render(self, graph: MapGraph, width: int = 2048, height: int = 2048) -> Image.Image:
        scale = width / 1024.0
        radius = max(8, int(30 * scale))

        canvas = Image.new("RGBA", (width, height), BACKGROUND)
        draw = ImageDraw.Draw(canvas, "RGBA")

        draw_roads(draw, graph, width, height, scale)
        draw_halos(draw, graph, width, height, radius)
        draw_markers(draw, graph, width, height, radius, scale)
        draw_labels(draw, graph, width, height, radius, scale)
        draw_title(draw, graph, scale)
        draw_legend(draw, graph, width, height, scale)

        return canvas.convert("RGB")
