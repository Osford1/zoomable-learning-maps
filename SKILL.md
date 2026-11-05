---
name: zoomable-learning-maps
description: "Use when building a zoom-in/zoom-out learning map."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [diagrams, learning, html, generators, verification]
    category: note-taking
    related_skills: [paper-structure-maps, diagram-design, visual-artifact-verification]
---

# Zoomable learning maps

The build side of the zoom-in / zoom-out framework: one master chart taken in at a glance, one chip on
every block, one generated page per chip, and a return path from every page back into the master. The
reader holds one canvas at a time and never loses their place.

`paper-structure-maps` is the authoring doctrine (what belongs on a chart, how to verify the claims).
`diagram-design` is the visual language. This skill is the machinery: the level model, the generator
that emits zoom pages in the master's own design system, and the rendered-pixel audit that catches what
the static gate cannot.

## Level model

| Level | File | Job | Holds |
|---|---|---|---|
| 0 master | `<topic>-structure-flowchart.html` | the whole argument at a glance | one block per argument beat, 6–9 blocks, one chip each |
| 1 zoom | `<topic>-z<N>-<slug>-zoom.html` | exactly one concept | the beat's real content: formulas, settings, numbers |
| 2 zoom | a chip inside a level-1 page | only when level 1 stopped being atomic | rare — prefer splitting level 1 |
| planned | same naming, `placeholder: true` | a zoom already promised by a peer page | what it will answer + which source section it comes from |

Rules that keep the model honest:

- **One concept per canvas.** If a level-1 page has to be scrolled to be read as a whole, it is two concepts — split it, never shrink the type.
- **Never fabricate a zoom's content to fill a page.** A not-yet-built zoom ships as a stated placeholder, and its parent labels it "still to build". Plausible filler destroys the trust the whole map runs on.
- **Never renumber anchors.** Append `Z8` after `Z7`; renumbering silently invalidates every page already linked to an id.
- **Placeholders are real pages:** they carry an accessible `<svg>` too, or they fail the gate.
- **Every page exits the way it entered:** the child repeats its own anchor chip as a link back to the master and names the master node it re-enters, top-right ("re-enters the master chart at §3.3").

## Build order

1. **Extract the source text once** to a plain-text working copy and keep it for the session. A direct `read_file` on a PDF returns a few hundred bytes of binary noise — render with PyMuPDF (`fitz`) to `full.txt` instead. Every number that reaches a canvas is then grepped out of that text, never recalled.
2. **Inventory the sections** from that text and pick beats, not headings: `grep -n -E "^[0-9]+(\.[0-9]+)*\.[[:space:]]+[A-Z]"` finds numbered headings in most journal layouts.
3. **Write the master by hand.** Read the precedent chart for this document family and inherit its CSS and geometry grammar, then write a fresh accessible `<svg>` opening (`<title>` + `<desc>` + `aria-labelledby`). Never copy a precedent's `<head>`: installed precedent charts predate `self_check.py` and fail it on stray `<link rel="preconnect">` tags and a title-less `<svg>`.
4. **Write one JSON spec per zoom anchor** — see `references/spec-format.md`.
5. **Generate:** `python scripts/zoom_subchart.py spec.json --out-dir <target-folder>`. Use `--check-only` for a dry run.
6. **Run the gate:** `python <diagram-design>/scripts/self_check.py *.html` — file arguments, not a bare directory, and native `C:/...` paths (an MSYS `/c/...` path makes it report a bogus "no such file"). It is a separate skill and is not bundled here; see "The static gate (not bundled)" in the README.
7. **Run the pixel audit:** `scripts/pixel_audit.js` against every file in a real browser. The static gate does not measure where text lands. With no browser tool available, `python scripts/audit_headless.py <folder>` drives a headless Chrome and prints the same violation counts.
8. **Fix in the generator or the spec, never in the generated file.** Regenerate, re-gate, re-audit — an edit applied to one page is lost the next time the batch runs.
9. **Report counts, not impressions:** N charts, N chips, N links resolved, gate result, audit violations.

## Why the pixel audit is mandatory

`self_check.py` validates structure and accessibility (svg first, title/desc, no remote references). It
knows nothing about where text lands. Two defect classes passed the gate and only appeared when the
rendered `getBBox()` was measured:

- **Text past the content edge.** The canvas is 880 wide with a 40 px margin, so boxes end at 840. A line can sit inside the canvas (880) and still spill out of its own box. At 9 px mono the advance is ~5.4 px/char, so ~138 characters is the ceiling for a line starting at `x="56"` — trim the wording or split the line; never shrink the type to fit, and never treat the canvas edge as the boundary.
- **Text colliding with text.** Two labels on one baseline, legend items wrapping into each other, a right-aligned note meeting a left-aligned label. Check every pair.

Audit checks, all in `getBBox()` units so scaling cannot distort them: `x1 < 0` or `x2 > 880` = off-canvas; `x2 > 840` = past its box edge; any pairwise text overlap = collision. Report the tightest margin, not just pass/fail.

The audit is also why the vision pass is secondary: a vision read of a 0.6-scale PNG will invent
legible-looking labels that are not on the page and judge "fits the width" against the crop instead of
the canvas. Use vision at ≥1.5 scale on crops to confirm nothing looks broken, and settle every
disagreement with `getBBox()`.

## Generator pitfalls

Each of these produced a visibly broken page that the gate still passed:

- **Emit a node in exactly one pass.** Collecting row nodes into the geometry plan *and* drawing them from the row branch draws each twice — the text overlaps itself and reads as smeared bold.
- **Measure monospace advance, don't estimate it.** The legend sizes each item from `MONO_ADV` (5.4–5.6 px/char at 8 px Geist Mono with tracking); an average 10 % low overflows the canvas on a five-item legend.
- **Wrap legend items into rows, and keep a standalone note on its own row.** One-line legends grow past 840 px as soon as a source adds a fifth item, and the right-aligned note then collides with them.
- **Pass all text through `esc()`, and put real Unicode in the spec** (`§`, `·`, `×`, `⁻¹`, `Δ`). Writing `&sect;` in the spec prints the literal entity, because the writer escapes the ampersand.
- **No thin spaces, no duplicated section labels.** `\u2009` survives JSON and renders as a gap that reads like a typo; a child header printing its section twice is a spec bug, not a layout bug.
- **A chip's target needs ≥24 px in both axes.** A 12 px-tall badge is unreadable as a hit target however neat it looks.
- **Keep chip labels and anchor ids joined in one place** — the spec's `anchor` is that join. A chip pointing at a slug that does not exist is a dead end the reader hits first; `scripts/verify_links.py` resolves every href.
- **Keep `parent_node` under ~40 characters.** It is drawn on the same top line as the right-aligned "re-enters the master chart at <section>" note, so a long parent label collides with it exactly when the section range is also long. The pixel audit catches it; the overflow check does not, because both strings are short enough to pass on their own.
- **Wrap the spec's lines before emitting (≤112 chars for chain nodes).** The generator's overflow check models a full-width box (~142 chars at 9 px), but a chain node's text sits in a narrower column, so a line the check passes can still crowd the box. A wrap pass in the spec builder is cheaper than hand-splitting a dozen lines, and it leaves deliberately short lines untouched.
- **`emit_master.py` writes immediately** (no `--check-only`), and `{H}` is substituted only by the master emitter, so a zoom footer must not carry `{H}`.
- **A return-chip fragment must open the target itself, not just its ancestors.** Opening the ancestor chain leaves the branch collapsed, so the reader lands at the top of a tree that looks like it ignored the link. Set the target's own open flag too, then mark and scroll it into view.
- **Filter visibility is "is a match OR is an ancestor of a match".** Writing it as "an ancestor is a match" inverts it and hides the matches inside a hidden branch — every filter click then empties the page. Assert the filtered view's counts (matches, visible boxes, hidden boxes) in the audit, not just that the click did not error.
- **When an HTML-driven page replaces the 880-wide static canvas, the skills' pixel audit is the wrong instrument** (its `pixel_audit.js` measures SVG `<text>`). Substitute a measured audit in the rendered page: `getBoundingClientRect()` for pairwise box intersection, `scrollWidth > clientWidth` plus rect-vs-parent-rect for text overflow, `documentElement.scrollWidth - innerWidth` for page overflow, and `window.onerror` + a `console.error` hook for script errors. Run it at every required width, in both colour schemes, and once more with `localStorage` redefined to throw (a `try/catch` claim is only verified when the getter actually throws).
- **Hide the harness on the page it measures.** A measurement `<pre>` injected into a staged copy shows up in the screenshot, and tightening its read regex to `<pre id="X">` breaks as soon as the element carries a `style` attribute. Hide it with `display:none` (the DOM dump still carries the text) and match `[^>]*>` in the reader.
- **A master page has no hand-off block.** To carry a link up to a parent document (a course map, a project index), give a band a chip whose href points at that file with a short label (`MAP`), and repeat the target in the page footer so the relationship survives a copy of the file.

## Files

- `scripts/zoom_subchart.py` — the generator: master's design system, geometry plan, overflow checks, chip/back-out/hand-off conventions, placeholder pages.
- `scripts/emit_master.py` — the master emitter: reuses the generator's CSS and geometry helpers so a master and its children cannot drift apart.
- `scripts/verify_links.py <folder>` — resolves every href, counts chips/sends per file, re-checks structural rules.
- `scripts/pixel_audit.js` — the measured audit (paste into the page, or drive it per file over CDP).
- `scripts/audit_headless.py` — runs `pixel_audit.js` over a folder of charts with headless Chrome and prints per-file violations (use when no browser tool is reachable).
- `references/spec-format.md` — every spec field, its type, and what the generator does with it.
- `references/design-system.md` — palette, geometry constants, font metrics, page anatomy.
- `references/master-authoring.md` — the master's spec shape, the pitfalls that cost real time, and the measured per-box width ceilings.
- `examples/spec-demo.json` — a two-page illustrative spec (one chart, one placeholder), so the generator can be run before a real one exists.
- `examples/spec-master-demo.json` — the matching master spec, so the demo set is closed and both emitters are runnable from the repo.

## Filing

Mirror the precedent: `<notes-root>/<topic-slug>/` holds the master plus its
`<topic>-z<N>-<slug>-zoom.html` pages. This repo ships the machinery and a two-page demo spec
(`examples/spec-demo.json`). A worked example is not published here; see "Worked example" in the README.

When the document already belongs to a family that lives elsewhere (a course folder such as
`<notes-root>/<course>/diagrams/` holding that family's master, lecture charts and a course map), file the new
master and its zooms **there** instead. Two reasons: the family's existing files are the precedent you
inherited the design system from, and relative links between master, zooms and the family's parent
chart only resolve when they sit in one folder. Note the numbering the parent uses if it differs from
the source's own (a deck labelled Lecture 5 filed as course entry 06), and print both on the chart so
the two systems can be reconciled.
