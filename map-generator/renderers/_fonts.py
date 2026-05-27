"""Font loading with project-local and system fallbacks."""
from __future__ import annotations
from pathlib import Path

from PIL import ImageFont

_FONT_DIR = Path(__file__).parent.parent.parent / "fonts"

_CANDIDATES: list[Path] = [
    _FONT_DIR / "DejaVuSansMono.ttf",
    Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"),
    Path("/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"),
]


def load(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    for path in _CANDIDATES:
        if path.exists():
            return ImageFont.truetype(str(path), size)
    return ImageFont.load_default()
