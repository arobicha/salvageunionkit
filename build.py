#!/usr/bin/env python3
"""
Salvage Union Playkit — Markdown to PDF generator.

Reads worksheet markdown files (with YAML front matter), performs the
structural transforms our worksheets need, and renders to print-ready PDF
using WeasyPrint.

USAGE
-----
    # Render a single worksheet
    python build.py worksheets/session-zero.md

    # Render all worksheets in a directory
    python build.py worksheets/

    # Specify output directory (defaults to ./output)
    python build.py worksheets/ --output dist/

    # Specify the number of pilots when rendering pilots-and-crew.md
    # (composes pilot-block.md the given number of times into the
    # insertion point)
    python build.py worksheets/pilots-and-crew.md --pilots 4

    # Specify a different CSS file
    python build.py worksheets/ --css css/playkit.css


WORKSHEET CONVENTIONS HONORED
-----------------------------
- YAML front matter is parsed and used for metadata (title, etc.)
- `<!-- page-break -->` comments become hard page breaks
- The first H1 + paragraphs before the first H2 are wrapped as a cover page
- `> _` blockquotes (empty answer slots) become writing slots
- Italic paragraphs starting with "Mediator note:" become callout boxes
- `# << PILOT BLOCKS INSERTED HERE >>` triggers fragment composition

DEPENDENCIES
------------
    pip install weasyprint markdown python-frontmatter pymdown-extensions
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Optional

import frontmatter
import markdown
from weasyprint import HTML, CSS
from weasyprint.text.fonts import FontConfiguration


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

ROOT = Path(__file__).resolve().parent
DEFAULT_CSS = ROOT / "css" / "playkit.css"
DEFAULT_OUTPUT = ROOT / "output"
PILOT_BLOCK_PATH = ROOT / "worksheets" / "pilot-block.md"

# Marker that the pilots-and-crew worksheet uses to indicate
# where per-pilot blocks should be stitched in.
PILOT_INSERTION_RE = re.compile(
    r"^#\s*<<\s*PILOT BLOCKS INSERTED HERE\s*>>\s*$",
    re.MULTILINE,
)

# Matches our HTML-comment page break markers
PAGE_BREAK_RE = re.compile(r"<!--\s*page-break\s*-->", re.IGNORECASE)

# Matches the empty-slot blockquote pattern: `> _` (possibly with whitespace)
WRITING_SLOT_RE = re.compile(r"^>\s*_\s*$", re.MULTILINE)

# Matches paragraphs that should become Mediator notes.
# In source: an italic paragraph starting with *Mediator note:*
# After markdown rendering: a <p> containing an <em> that starts with
# "Mediator note:" — we match the rendered HTML.
MEDIATOR_NOTE_RE = re.compile(
    r"<p>(<em>Mediator note:.*?</em>)</p>",
    re.IGNORECASE | re.DOTALL,
)

# The TEMPLATE INSERTION POINT HTML comment block in pilots-and-crew.md
# spans multiple lines; we strip the whole block on render
TEMPLATE_COMMENT_RE = re.compile(
    r"<!--\s*TEMPLATE INSERTION POINT.*?-->\s*",
    re.IGNORECASE | re.DOTALL,
)
TEMPLATE_COMMENT_END_RE = re.compile(
    r"<!--\s*END TEMPLATE INSERTION POINT\s*-->\s*",
    re.IGNORECASE,
)

# ---------------------------------------------------------------------------
# Pipeline stages
# ---------------------------------------------------------------------------

def load_markdown(path: Path) -> tuple[dict, str]:
    """Load a markdown file, returning (metadata, body)."""
    post = frontmatter.load(path)
    return post.metadata, post.content


def compose_fragments(body: str, source_path: Path, *, pilots: int = 4) -> str:
    """
    If the body contains a pilot block insertion marker, replace it with
    `pilots` copies of pilot-block.md's body (with a heading numbered per
    pilot).
    """
    if not PILOT_INSERTION_RE.search(body):
        return body

    if not PILOT_BLOCK_PATH.exists():
        print(
            f"  ! Insertion marker found in {source_path.name} "
            f"but {PILOT_BLOCK_PATH.name} not found — leaving placeholder.",
            file=sys.stderr,
        )
        return body

    _, block_body = load_markdown(PILOT_BLOCK_PATH)

    # Strip any leading HTML comments from the fragment (the explanatory
    # block at the top of pilot-block.md)
    block_body = re.sub(r"^<!--.*?-->\s*", "", block_body, count=1, flags=re.DOTALL)

    composed_chunks: list[str] = []
    pilot_labels = ["One", "Two", "Three", "Four", "Five", "Six", "Seven", "Eight"]

    for i in range(pilots):
        label = pilot_labels[i] if i < len(pilot_labels) else str(i + 1)
        # Each pilot block gets its own page-break before, and we
        # substitute "Pilot —" with "Pilot N —" in section headers
        chunk = block_body.replace("## Pilot —", f"## Pilot {label} —")
        # Add a page-break before every pilot block after the first,
        # so each pilot starts on a fresh page
        if i > 0:
            chunk = "<!-- page-break -->\n\n" + chunk
        composed_chunks.append(chunk)

    composed = "\n\n".join(composed_chunks)
    return PILOT_INSERTION_RE.sub(composed, body)


def strip_template_comments(body: str) -> str:
    """Remove the multi-line TEMPLATE INSERTION POINT HTML comments."""
    body = TEMPLATE_COMMENT_RE.sub("", body)
    body = TEMPLATE_COMMENT_END_RE.sub("", body)
    return body


def transform_writing_slots(body: str) -> str:
    """
    Replace `> _` blockquote-with-underscore patterns with explicit HTML
    placeholders that survive markdown rendering and become styled
    writing slots in the final document.

    We do this BEFORE markdown rendering by replacing the line with an
    HTML comment marker, then post-process after rendering.
    """
    # Convert every `> _` line to a magic placeholder.
    # We use a string that the markdown parser will keep intact in a
    # paragraph or which we can easily find after rendering.
    return WRITING_SLOT_RE.sub(
        '<div class="writing-slot"></div>',
        body,
    )


def transform_page_breaks(body: str) -> str:
    """Convert <!-- page-break --> HTML comments into <hr class="page-break">."""
    return PAGE_BREAK_RE.sub('<hr class="page-break">', body)


def render_markdown(body: str) -> str:
    """Convert the prepared markdown to HTML."""
    md = markdown.Markdown(
        extensions=[
            "extra",          # tables, fenced code, abbreviations, etc.
            "sane_lists",
            "smarty",         # smart quotes, en/em dashes
            "attr_list",      # allows {.class} syntax if we want it later
        ],
    )
    return md.convert(body)


def transform_mediator_notes(html: str) -> str:
    """Wrap Mediator note paragraphs in a styled class."""
    def replace(match: re.Match) -> str:
        # We keep the inner <em>...</em> so italics are preserved
        inner = match.group(1)
        return f'<p class="mediator-note">{inner}</p>'

    return MEDIATOR_NOTE_RE.sub(replace, html)


def wrap_cover_section(html: str) -> str:
    """
    Wrap everything from the start of the document up to (but not
    including) the first <h2> in <section class="cover">. Wrap the
    remainder in <section class="content-columns"> so column-based
    stylesheets have a container to target.

    Also detects:
    - The subtitle paragraph (first <em>-only paragraph after h1)
    - "Meta fields" paragraphs (those with underscored blanks)
    """
    # Find the first <h2> position
    h2_match = re.search(r"<h2[\s>]", html)
    if not h2_match:
        # No sections — wrap the whole doc as cover (degenerate case)
        return f'<section class="cover">{html}</section>'

    cover_html = html[:h2_match.start()]
    rest_html = html[h2_match.start():]

    # Tag the subtitle (first <em>-only paragraph right after h1)
    cover_html = re.sub(
        r"(<h1[^>]*>.*?</h1>)\s*<p><em>(.*?)</em></p>",
        r'\1\n<p class="subtitle">\2</p>',
        cover_html,
        count=1,
        flags=re.DOTALL,
    )

    # Tag meta-fields paragraphs (those with underscored blanks)
    meta_field_pattern = re.compile(
        r"((?:<p>[^<]*_{3,}[^<]*</p>\s*)+)",
        re.MULTILINE,
    )
    cover_html = meta_field_pattern.sub(
        r'<div class="meta-fields">\1</div>',
        cover_html,
    )

    return (
        f'<section class="cover">{cover_html}</section>'
        f'<section class="content-columns">{rest_html}</section>'
    )


def build_full_html(meta: dict, body_html: str) -> str:
    """Wrap the rendered body in a full HTML document."""
    title = meta.get("title", "Salvage Union Worksheet")
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <title>{title}</title>
</head>
<body>
{body_html}
</body>
</html>"""


# ---------------------------------------------------------------------------
# Main pipeline
# ---------------------------------------------------------------------------

def render_worksheet(
    source: Path,
    output: Path,
    css_path: Path,
    *,
    pilots: int = 4,
) -> None:
    """Render a single worksheet to PDF."""
    print(f"  • {source.name}")

    # 1. Load
    meta, body = load_markdown(source)

    # 2. Compose fragments (e.g. insert pilot blocks)
    body = compose_fragments(body, source, pilots=pilots)

    # 3. Strip template-housekeeping HTML comments
    body = strip_template_comments(body)

    # 4. Transform structural markers PRE-render
    body = transform_writing_slots(body)
    body = transform_page_breaks(body)

    # 5. Render markdown → HTML
    html = render_markdown(body)

    # 6. Post-render transforms
    html = transform_mediator_notes(html)
    html = wrap_cover_section(html)

    # 7. Wrap in full HTML document
    full_html = build_full_html(meta, html)

    # 8. Render to PDF
    font_config = FontConfiguration()
    stylesheet = CSS(filename=str(css_path), font_config=font_config)
    HTML(string=full_html, base_url=str(ROOT)).write_pdf(
        target=str(output),
        stylesheets=[stylesheet],
        font_config=font_config,
    )
    # Pretty-print the output path: relative to ROOT if it's under it,
    # else just absolute.
    try:
        display = output.resolve().relative_to(ROOT)
    except ValueError:
        display = output.resolve()
    print(f"      → {display}")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Render Salvage Union playkit markdown to PDF.",
    )
    parser.add_argument(
        "source",
        type=Path,
        help="Markdown file or directory of markdown files.",
    )
    parser.add_argument(
        "--output", "-o",
        type=Path,
        default=DEFAULT_OUTPUT,
        help=f"Output directory (default: {DEFAULT_OUTPUT.name}/)",
    )
    parser.add_argument(
        "--css", "-c",
        type=Path,
        default=DEFAULT_CSS,
        help=f"CSS stylesheet (default: {DEFAULT_CSS.relative_to(ROOT)})",
    )
    parser.add_argument(
        "--pilots", "-p",
        type=int,
        default=4,
        help="Number of pilot blocks to compose when rendering pilots-and-crew (default: 4)",
    )
    parser.add_argument(
        "--include-fragments",
        action="store_true",
        help="Also render fragment files standalone (e.g. pilot-block.md). "
             "By default these are skipped, since they're composed into "
             "their parent worksheet.",
    )
    args = parser.parse_args()

    args.output.mkdir(parents=True, exist_ok=True)

    # Gather source files
    if args.source.is_file():
        sources = [args.source]
    elif args.source.is_dir():
        sources = sorted(args.source.glob("*.md"))
    else:
        print(f"Error: {args.source} not found.", file=sys.stderr)
        return 1

    if not sources:
        print(f"Error: no markdown files found in {args.source}.", file=sys.stderr)
        return 1

    print(f"Rendering {len(sources)} worksheet(s):")
    try:
        css_display = args.css.resolve().relative_to(ROOT)
    except ValueError:
        css_display = args.css.resolve()
    print(f"  CSS: {css_display}")
    print()

    rendered = 0
    skipped = 0
    for src in sources:
        # Check fragment status
        meta, _ = load_markdown(src)
        if meta.get("fragment") and not args.include_fragments:
            print(f"  · {src.name} (fragment — skipped)")
            skipped += 1
            continue

        out_path = args.output / f"{src.stem}.pdf"
        render_worksheet(src, out_path, args.css, pilots=args.pilots)
        rendered += 1

    print()
    print(f"Done. Rendered {rendered}, skipped {skipped}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
