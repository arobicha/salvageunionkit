# Salvage Union Region Map Overlay — Style Prompt

Paste this into a new chat along with the source topo map and the region's
contents (areas, settlements, threats, road connections). Claude will produce
an annotated overlay in the consistent campaign style.

---

## PROMPT

You are annotating a topographical map for a **Salvage Union** campaign in the
**Rusting Reach overlay style**. Use Python + PIL only (no external image
generation). Output a single PNG to `/mnt/user-data/outputs/`. Read the source
image first to confirm dimensions before placing anything.

### Visual design rules

**Title banner (top-left).**
- Solid dark slab `(15, 15, 15, 210)` with ~12px padding.
- Title in **gold** `(220, 180, 80)` using DejaVu Sans Bold, size ~34px at 1024px wide (scale proportionally for other sizes).
- Subtitle directly underneath in light grey `(200, 200, 200)`, size ~20px.
- Subtitle is always a short tag describing the region's core feature (e.g. "A Drowned Coast Region", "Reactor Country").

**Markers.**
- Filled circles, radius ~30px at 1024px (scale with image width).
- Each circle has a soft dark halo behind it: same center, radius +5px, fill `(0, 0, 0, 140)`. This is what makes them pop against the topo.
- Outline `(20, 20, 20)`, width 3px.
- Centered numeral inside the circle, DejaVu Sans Bold ~28px, fill `(15, 15, 15)` (dark on the colored circle, not white).
- Number the points 1–N in **rough reading order** (coast → interior, or settlement-first then outward).

**Marker color = location type.** Use these exact RGBA values:
- Settlement → gold `(210, 175, 55, 255)`
- Area Salvage Point → rust orange `(200, 90, 50, 255)`
- Travel Area / linking node → steel grey `(180, 180, 185, 255)`
- Threat / Lair → blood red `(190, 50, 50, 255)`
- Open / Empty space → muted green `(130, 150, 130, 255)`

**Labels.**
- DejaVu Sans Bold ~20px.
- Dark slab background `(15, 15, 15, 200)`, 6px padding.
- Label text is colored to **match its marker's category color** (gold settlement label, rust salvage label, etc.) — this is the signature of the style.
- Place labels with a per-point offset; default is `(+40, 0)` from the marker center. Flip to `(-tw - 40, 0)` for markers on the right edge or anywhere a right-side label would collide with another label, the legend, or run off the map.
- After placement, mentally check: does any label overlap another label, a marker, the title slab, or the legend? If yes, flip its offset or nudge the marker. Re-render and re-check.

**Roads.**
- Draw *under* the markers.
- Two-pass for legibility:
  1. Soft cream underlay: solid line, color `(255, 240, 210, 90)`, width 11px.
  2. Dark dashed overlay on top: color `(60, 40, 25, 220)`, width 5px, 16px dash, 12px gap.
- Roads connect points along sensible terrain — follow valleys, river channels, and low ground where the topo permits; avoid drawing straight lines across obvious ridges or peaks if a slight bend would route around them. Straight dashed segments are fine when the terrain is open.
- Brinehead-style hub patterns are encouraged: one settlement is usually the natural junction.

**Legend (bottom-right).**
- Dark slab `(15, 15, 15, 210)` with ~10px padding, roughly 250×190px at 1024.
- Header "LEGEND" in gold `(220, 180, 80)`, size ~20px.
- Each row: 18px filled circle with `(20,20,20)` outline + category name in light grey `(220, 220, 220)`, size ~20px.
- Include only the categories actually present on this map.
- Place the legend in the corner with the least terrain detail; if bottom-right is busy, bottom-left is the fallback. Never place it where it covers a marker.

### Layout & placement logic

1. **Read the terrain first.** Identify: water bodies, prominent peaks/massifs, valleys, river channels, crater/depression features, open flats. Place each point on terrain that justifies its function:
   - Settlements → near water, junctions, or sheltered low ground.
   - Salvage points → ruins, drainages, craters, coastal shelves.
   - Threat lairs → highlands, isolated peaks, dead-end valleys.
   - Travel/linking nodes → choke points, river confluences, passes.
   - Empty space → open flats with little detail.
2. **Spread points across the map.** No two markers closer than ~120px at 1024. If the supplied content has more points than fit comfortably, push back rather than crowd.
3. **Draw order:** roads → marker halos → markers → numerals → labels → title → legend.
4. **Composite via an RGBA overlay** (`Image.new("RGBA", size, (0,0,0,0))`) and `Image.alpha_composite` against the source, then save as RGB PNG.

### Font fallback

Try in order, fall back to PIL default:
1. `/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf`
2. `/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf`

### Required inputs from the user

When invoking this prompt, the user will provide:
- The source topo map (a PNG, any square or rectangular size).
- The region's **name** and **subtitle tag**.
- A list of points: `(name, category, suggested location description)` — e.g. *"Brinehead, settlement, at the head of the estuary"*. Translate descriptions into pixel coordinates by reading the source image.
- A list of road connections: pairs of point names.

### Output

- File path: `/mnt/user-data/outputs/<region_slug>_region_map.png`
- Same pixel dimensions as the source.
- Verify the final image renders cleanly (no label collisions, no markers off-map, legend not covering content). If anything collides, adjust offsets and re-render before presenting.

### Tone & narrative pairing

The map is half the deliverable. Alongside the image, write the region brief
in prose: name + core feature, three threats (using the Tyrant / Torment /
Environmental / Brute / Aberration categories from the Salvage Union campaign
rules), each numbered area with 2–4 sentences of flavor, a d6 random
encounter table, and a short scrap-math note confirming the region offers
enough salvage for a starting crew to pay upkeep and upgrade. Keep the prose
grounded in the Salvage Union setting — corpos, wasters, Mechs as the
ambient technology, hope-in-the-rust tone.
