# Credits

## This repo

MIT, © 2026 Chen Bin — see `LICENSE`. I wrote the code and the documents in this repo with Hermes Agent
under my direction, which the `author:` field of `SKILL.md` records.

## `diagram-design` — the design approach this method builds on

**Credited by name, and it is the source of the diagram design approach every chart here inherits.** The
palette, the type ramp, the font metrics, the geometry grammar, the chip anatomy and the accessible-SVG
contract all come from that skill. `references/design-system.md` is that system written down as the
constants this generator emits, and `scripts/zoom_subchart.py` and `scripts/emit_master.py` reproduce it.
Nothing in those two documents is original to me.

**Not redistributed.** The earlier package of this skill vendored two files from `diagram-design` —
`scripts/self_check.py` and `assets/template-motion.html`. They are **not** in this repo. That skill's
`SKILL.md` frontmatter declares `license: MIT`, but it ships no `LICENSE` file and names no copyright
holder, and `self_check.py` refers to "the repository gates … which remain the authority for
contributions to the repository itself" — an upstream repository that is not mine. Redistributing under
MIT requires a copyright notice I do not have, so I left the files out rather than ship them with a
notice I cannot name. `docs/owner-todos.md` records what is needed to bring them back: the upstream repo
URL and its copyright line, at which point they can be re-vendored under `vendor/diagram-design/`
together with that project's own `LICENSE` file.

The consequences are stated in the README: the static gate is an optional external step, and
`scripts/verify_links.py` re-checks the same structural rules so a failure is still diagnosable without
it.

## `paper-structure-maps` — the reading doctrine

Credited by name, no files copied. This repo's workflow uses these parts of it:

- **pick argument beats, not headings** — the master chart's blocks come from the paper's argument, and
  two outline entries that make the same argument at two depths merge into one block;
- **one stable anchor chip per concept, and never renumber it** — the `Z1`, `Z2`, … id is the join
  between the master and the child page, so a renumber silently invalidates every page built against it;
- **every value on a canvas is grepped out of the extracted source text, never recalled**;
- **fix the return convention before the second chart exists** — the child repeats its own chip and names
  the block it re-enters, or zooming back out is guesswork;
- **measure the rendered SVG, not the markup** — the static check does not tell you where text lands.

`SKILL.md` names it as the authoring doctrine; nothing in this repo is derived from its text, so no
licence obligation attaches.

## `visual-artifact-verification` — the measurement rule

Credited by name, no files copied. The principle taken from it: a generated artifact is not finished until
the rendered pixels have been measured. `scripts/pixel_audit.js` is that principle applied to these
pages, and `scripts/audit_headless.py` is how it runs without a browser tool.

## `interactive-concept-widgets` — named, not used

Credited by name, no files copied, and **not used by this generator or by this repo**. It is listed
because it is the sibling skill for the case where a concept needs an interactive widget instead of a
static canvas.

## Fonts

Geist, Geist Mono and Instrument Serif are loaded by URL from Google Fonts, which is the only remote
reference any generated page carries. No font file is in this repo, so there is nothing to relicense
here; each family keeps its own terms upstream. Offline, the pages render on system fallbacks.

## The worked example

**No worked example is published in this repo.** The map I built as the test case was charted from a
paper that is not mine and that I do not have the authors' permission to republish in that detail, so it
is not included and is not named anywhere in this repo — not its title, authors, DOI or numbers. No
figure, table or text block from it is reproduced here; the charts I made were redrawn from the extracted
text. A worked example rebuilt against a public CC-BY paper is an open to-do in `docs/owner-todos.md`.

The two spec files in `examples/` are my own illustrative content, not findings from any source. Their
text says so on the page and in the spec.

## Third-party code and assets, summarised

| Item | Status |
|---|---|
| `diagram-design` — `self_check.py`, `template-motion.html` | excluded, credited by name, re-vendoring blocked on the upstream URL and copyright line |
| `paper-structure-maps`, `visual-artifact-verification`, `interactive-concept-widgets` | doctrine only, no files copied, credited by name |
| Geist / Geist Mono / Instrument Serif | served by URL from Google Fonts, no binaries shipped |
| The paper the worked example was built on | not reproduced, not named, not included |
| Vendored JavaScript (GSAP, Lenis or similar) | none — this repo has no vendored JS library and needs none |
