# Salvage Union Playkit — PDF Generator

Converts the `.md` worksheets in `worksheets/` to print-ready PDFs.

## Setup

```bash
pip install weasyprint markdown python-frontmatter pymdown-extensions
```

WeasyPrint also needs system libraries (Pango, Cairo, GDK-PixBuf). On Debian/Ubuntu:

```bash
sudo apt install libpango-1.0-0 libpangoft2-1.0-0
```

On macOS:

```bash
brew install pango
```

## Two stylesheets, two purposes

Same worksheets, two visual treatments. Pick at render time with `--css`.

### `css/playkit.css` — color portrait (the "display" version)

Rusted utility document aesthetic. Paper cream background, oxide red accents,
warm near-black ink. Single column, portrait Letter. Designed to look good
on screen and as a presentation artifact.

```bash
python build.py worksheets/ --css css/playkit.css --output output/color
```

### `css/playkit-bw.css` — black & white landscape (the "print and fill in" version)

Pure black on white, no background fill. Two-column landscape Letter. Inline
page-break markers become column breaks instead, so a section's content flows
across columns on a single page rather than spawning half-empty pages.
Designed for laser/inkjet at home and writing in by hand.

```bash
python build.py worksheets/ --css css/playkit-bw.css --output output/bw
```

You can render both versions from the same markdown source — the worksheets
don't change.

## Usage

```bash
# Render every worksheet (uses default color stylesheet)
python build.py worksheets/

# One worksheet, B&W landscape
python build.py worksheets/session-zero.md --css css/playkit-bw.css

# Pilots-and-Crew: specify number of pilots (default 4)
python build.py worksheets/pilots-and-crew.md --pilots 6

# Custom output directory
python build.py worksheets/ --output dist/
```

Fragment files (those with `fragment: true` in their YAML front matter,
like `pilot-block.md`) are skipped when rendering directories — they're
composed into their parent worksheet automatically.

## Project layout

```
playkit-pdf/
├── build.py                # The generator
├── css/
│   ├── playkit.css         # Color, portrait, single-column
│   └── playkit-bw.css      # B&W, landscape, two-column
├── fonts/                  # OFL fonts (Source Sans Pro + DejaVu Sans Mono)
├── worksheets/             # Source markdown
│   ├── session-zero.md
│   ├── pilots-and-crew.md
│   └── pilot-block.md      # Fragment, composed into pilots-and-crew
└── output/                 # Rendered PDFs
```

## Visual identity

The aesthetic is **rusted utility document** — a field manual for a piece
of industrial equipment that's been in service forty years. Design tokens
live in each stylesheet at the top under `:root`. Tweak a variable to
retune. Typography is Source Sans Pro for display/body and DejaVu Sans Mono
for Mediator-note callouts.

The B&W stylesheet drops all background fills and reduces the rust accent
to plain black, but keeps the same fonts, type hierarchy, and structural
hooks. So changes you make to one (e.g., a new section type, a different
question style) port to the other easily.

## How worksheet conventions map to PDF

| Markdown source              | Color version            | B&W landscape version       |
|------------------------------|--------------------------|-----------------------------|
| `# Title`                    | Cover document title     | Same                        |
| `## Section`                 | New page + section rule  | New page, spans both cols   |
| `### Question`               | Bold question            | Same                        |
| `> _`                        | Ruled writing slot       | Same (narrower in 2-col)    |
| `*Mediator note: ...*`       | Mono callout, rust rule  | Mono callout, hairline box  |
| `<!-- page-break -->`        | Forced page break        | Forced **column** break     |
| `# << PILOT BLOCKS ... >>`   | Inserts N copies         | Same                        |

YAML front matter is read for `title` and metadata but does not appear
in the rendered output.
