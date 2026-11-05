# Authoring the MASTER chart

The generator (`scripts/zoom_subchart.py`) emits the zoom CHILDREN from specs. Masters used to be
hand-written in SVG, which is where mistakes creep in: the head/CSS must stay identical to the
family's design system, chips must line up, and the footer must state a canvas height that only
exists after layout.

`scripts/emit_master.py` fixes that: it imports the generator and reuses its CSS and geometry
helpers, so a master and its children cannot drift apart.

## Run it

    python scripts/emit_master.py spec-master.json --out-dir <folder>

Spec shape (see the module docstring): `slug`, `eyebrow`, `h1`, `sub_lines`, `desc`, `bands[]`,
`legend[]`, `legend_note`, `cards[]`, `footer[]`. Each band: `tag`, `title`, `lines[]`, optional
`focal`, optional `chip` (`{label, href, hermes}`), optional `loop`. Output is
`<slug>-structure-flowchart.html` - the name children use as `parent_file`.

Band height is derived (`96 + 20 x lines`), connectors and the legend strip are drawn for you, and
text overflow is reported the same way the generator reports it.

## Pitfalls that cost real time

- **`FONT_LINK` is a bare URL, not a tag.** The generator interpolates it into
  `<link href="%(font)s" rel="stylesheet">`. Emitting the constant on its own puts raw URL text in
  `<head>`; the parser then closes `<head>` early, the URL renders as visible text above the chart,
  and the `<style>` block silently lands in `<body>`. Always wrap it.
- **The 5.4 px/char width rule is ASCII-only.** Greek and maths glyphs (omega, theta-bar, Phi,
  arrows, <=, +/-, section signs) are wider in the mono face, so a line that passes the character
  count can still overrun x=840. Measure with `pixel_audit.js` in a browser; do not trust the count.
- **Canvas height is only known after layout.** Never hardcode "canvas 880 x N" in a footer: rewrite
  it from the computed height as the page is assembled, or the footer contradicts the viewBox.
- **Long lines: split, do not cut.** Keep the keyword label on the first line and prefix the
  continuation with an arrow glyph; re-word so both halves carry content. A naive split at the
  widest separator leaves dangling fragments like "THE ANSWER -" alone on a line.
- **Editing a shared generator from a script: check the call sites.** Injecting a helper that changes
  a function's return arity breaks every caller. Run the generator once after editing it.

## Measured width ceilings (the emitter's warnings are optimistic)

The generator warns above ~142 characters, but a 9 px mono line starting at x=56 hits x=840 at about
135 characters. Trim anything over 135; the pixel audit catches the rest. Per-box ceilings, measured:

- master band line: <=135 chars (142 warns but still overruns by ~12 px)
- zoom `rows` node, 3 nodes across: ~40 chars per line; 4 nodes: ~28; 6 nodes: ~14, with titles ~12
- hand-off `next[].text` and `terminator_sub`: <=58 chars, or the chip collides with the terminator text
  (both are drawn at the same baseline; the terminator box ends near x=474)

## Zoom spec traps

- **`rows` is a LIST of blocks**, each `{header, nodes[]}` - a bare dict fails in `build_svg` with
  `TypeError: string indices must be integers`.
- Renaming a zoom file means editing the master spec's `chip.href` too; run `verify_links.py` after any
  rename (it reports `DEAD LINK <master> -> <missing file>`).
- Chip/next labels are sentences, so trim them by re-wording, not by cutting at a word boundary - a
  truncated clause reads as a bug on a page whose whole job is clarity.

## Verify before shipping (in this order)

1. `diagram-design/scripts/self_check.py <all files>` - structure and accessibility gate.
2. `scripts/verify_links.py` - the link graph: every child back to its master, every chip to a file
   that exists, no orphans.
3. `scripts/pixel_audit.js` per page in a real browser: `offCanvas = pastContentEdge =
   textCollisions = 0`. Await `document.fonts.ready` first, or fallback font metrics produce phantom
   collisions; where several pages run in one session, load the first page twice if a page reports
   text touching the edge.

Then look at one screenshot per master with an image-capable check: boxes full, arrows visible, no
band reading as a wall of text.
