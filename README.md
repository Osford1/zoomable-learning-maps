# zoomable-learning-maps

**A generator and a written method for zoomable learning maps — one master chart, a chip on every block,
one generated page per chip — for anyone reading long technical documents who keeps losing their place.**

A zoomable learning map is one master chart you can take in at a glance, with a small chip on every
block. Each chip opens a generated page about exactly one concept, and each of those pages names the
block it returns to. You read one canvas at a time and you never lose your place.

This repo is the machinery for building them: a JSON spec format, a Python generator that emits the zoom
pages in the master's own design system, a second generator for the master itself, two checks that have
to come back clean, and a demo spec you can run in one command. The visual language the pages inherit is
the `diagram-design` skill's, credited in `CREDITS.md`.

State: finished at v1.0.0 (the version in the `SKILL.md` frontmatter) and used end to end once, on one
real paper. The map I built for that paper is not in this repo — see
[Worked example (not published)](#worked-example-not-published). Masters are emitted from a spec, never
inferred from a source. I wrote this with Hermes Agent under my direction, which the `SKILL.md`
frontmatter records. I built it for my own studying and I am learning as I go; it is a working tool, not
a product.

Every generated page opens straight from `file://` in a browser. There is no build step, no bundler and
no server.

<!-- TODO(owner): add the two README screenshots once they exist. docs/screenshots/README.md lists the shots needed. Do not add image links before the files are there. -->

## What is in here

| Path | What it is | Mine |
|---|---|---|
| `SKILL.md` | the workflow an agent reads: the level model, the build order, the craft rules | yes, written with Hermes Agent |
| `scripts/` | 5 scripts: 2 generators, 1 link checker, 1 paste-in pixel audit, 1 headless wrapper | yes |
| `references/` | 3 documents: the spec format, the design system, master authoring | yes, except the design system itself — see `CREDITS.md` |
| `examples/` | 2 demo specs (a master and a pair of zoom pages) and how to run them | yes |
| `docs/` | the verification output I got, the owner to-dos, the screenshot list | yes |

Full tree, with inline notes: [File tree](#file-tree).

## Run it

```bash
python scripts/emit_master.py   examples/spec-master-demo.json --out-dir ./out/demo
# demo-structure-flowchart.html    9886 bytes  canvas 880 x 560
# no text-overflow warnings

python scripts/zoom_subchart.py examples/spec-demo.json        --out-dir ./out/demo
# demo-z1-the-workflow-zoom.html      12055 bytes  chart        canvas 880 x 900
# demo-z2-still-to-build-zoom.html     8242 bytes  placeholder  canvas 880 x 528
# no text-overflow warnings

python scripts/verify_links.py ./out/demo
# PROBLEMS: none   (exit code 0)
```

Three commands, nothing to install beyond Python 3.9+ and the standard library. The generated pages open
from `file://` with no bundler and no server. Every number above is from the run recorded in
`docs/verification.md`, on the files in this repo; `./out/` is ignored by git.

## The idea

One loop: **master → chip → page → back out.** The master chart is the index and holds the whole
argument. A chip on a block opens one page about one concept. That page repeats its own chip as a link
back to the master and names the block it re-enters, so the reader returns to the same place they left.

| Level | File | Job | Holds |
|---|---|---|---|
| 0 master | `<topic>-structure-flowchart.html` | the whole argument at a glance | one block per argument beat, 6–9 blocks, one chip each |
| 1 zoom | `<topic>-z<N>-<slug>-zoom.html` | exactly one concept | the beat's real content: formulas, settings, numbers |
| 2 zoom | a chip inside a level-1 page | only when level 1 stopped being atomic | rare — prefer splitting level 1 |
| planned | same naming, `placeholder: true` | a zoom already promised by a peer page | what it will answer + which source section it comes from |

The rules that keep the model honest are in `SKILL.md`: one concept per canvas, never fabricate a zoom's
content to fill a page, never renumber anchors, and every page exits the way it entered. A zoom that does
not exist yet ships as a stated placeholder page — the demo emits one of each, so you can see both.

## Worked example (not published)

I built this method against one real paper: a master chart with the zoom pages off it, some built and
some left as stated placeholders. That paper is not mine, I do not have the authors' permission to
republish its structure at that level of detail, and it is not named in this repo.

No figure or text block from it is reproduced anywhere in this repo, and none ever was — the pages were
redrawn from the extracted text. The map itself is not included, and `examples/` holds no copy of it.

A worked example rebuilt against a public CC-BY paper is coming, so the pages ship next to a source
anyone can check. That is an open to-do, not a promise with a date: `docs/owner-todos.md`. Until then the
demo specs in `examples/` are the only runnable set.

## Writing a map

1. Extract the source text once and grep every number out of it — never recall a number.
2. Pick **beats, not headings** (6–9 for a master) and write one master spec.
3. Write one JSON spec per chip, then generate.
4. Gate it against the structural rules, then **audit the rendered pixels** — both must come back clean.
5. Fix in the generator or the spec, never in a generated file, then regenerate and re-check.

### Spec format

Every field, its type, and what the generator does with it: `references/spec-format.md`.

### Design system

The palette, the type ramp, the geometry constants and the font metrics the overflow check uses:
`references/design-system.md`. None of it is original to me — it is `diagram-design`'s system.

### Authoring the master

A master is emitted from a spec by `scripts/emit_master.py`, which reuses the generator's own CSS and
geometry helpers so a master and its children cannot drift apart: `references/master-authoring.md`.

## The two checks

Both checks exist because each one is blind where the other sees. Run both after every edit.

| Check | Command | Pass condition | What it cannot see |
|---|---|---|---|
| `scripts/verify_links.py` | `python scripts/verify_links.py ./out/demo` | no `DEAD LINK`, `REMOTE DEP`, `SVG IMAGE REF` or missing-title lines, exit 0 | where text lands inside a box, and whether a page reads well |
| `scripts/pixel_audit.js` | in a browser, `zoomAudit()` | `offCanvas + pastContentEdge + textCollisions === 0` | meaning, wording, and any defect the generator and the spec share |
| `scripts/audit_headless.py` | `python scripts/audit_headless.py ./out/demo` | `PAGES_BAD: 0`, exit 0 | the same as the audit it wraps; it only adds headless Chrome |

### `verify_links.py`

`python scripts/verify_links.py <folder>` walks every `.html` file in the folder. It prints one line per
file — bytes, `hrefs`, `chips`, `sends` — then the problems it found. Exit code 0 means clean, 1 means at
least one problem, 2 means it was called with no argument. For the demo set it prints
`PROBLEMS: none`, exit 0.

It resolves every local `href`, which is why it is the check that finds a chip pointing at a page that
does not exist. It also re-checks the structural rules the external gate enforces (`<svg>` present,
`<title id=…>`, `lang`, `aria-labelledby`, no remote dependency other than the one Google Fonts
stylesheet, no embedded image), so a gate failure is diagnosable without the gate.

### `pixel_audit.js`

This one is not a CLI. It is a function, `zoomAudit()`, that measures the rendered SVG with `getBBox()`.
Run it one of three ways: paste the file into devtools on an open page and call `zoomAudit()`; load the
page over CDP and call it through a JS eval; or let `audit_headless.py` inject it and read the result
back. It reports three violation classes — text off the canvas, text past the 840 px content edge, two
labels overlapping — plus the tightest right margin.

The pass condition is `offCanvas + pastContentEdge + textCollisions === 0` on every file. It must run
after `document.fonts.ready`: before the webfont arrives, the system fallback metrics are wider and the
audit reports collisions that are not on the finished page. `audit_headless.py` waits for it.

### `audit_headless.py`

`python scripts/audit_headless.py <folder-or-file> …` wraps `pixel_audit.js` in headless Chrome, so it
needs no browser tool. It looks for Chrome or Edge at the standard install paths on Windows, Linux and
macOS and reports which one is missing if it finds none. It prints one line per page (canvas size, text,
link and chip counts, tightest right margin), the text of any violation, and a final `PAGES_BAD:` count.
Exit code 1 when any page has a violation, so it can gate a build.

## The static gate (not bundled)

`diagram-design/scripts/self_check.py` is the static gate this method was built against: it validates the
accessible-SVG contract (the `<svg>` is the first SVG-bearing element, `<title>` and `<desc>` come first,
ids are derived from the slug, `aria-labelledby` points at them, no remote reference except the one
Google Fonts stylesheet, no embedded raster). It runs before the pixel audit: structure first, then where
the text lands.

It is **not** in this repo. It belongs to a different skill and the copyright holder is not stated
anywhere I could find it, so I cannot redistribute it under MIT — see `CREDITS.md` and
`docs/owner-todos.md`. The generator, `verify_links.py` and the pixel audit all run without it, and
`verify_links.py` re-checks the same structural rules.

## Install as an agent skill

This folder is an Agent Skill: `SKILL.md` at the root, no build step. Drop the folder named
`zoomable-learning-maps` into whichever directory your agent scans.

| Agent | Drop the `zoomable-learning-maps` folder into |
|---|---|
| Claude Code (you) | `~/.claude/skills/` |
| Claude Code (project) | `.claude/skills/` |
| Codex | `~/.agents/skills/` |
| OpenCode | `~/.config/opencode/skills/` (also reads the two above) |
| Antigravity | `~/.gemini/antigravity/skills/` |
| Hermes | `~/AppData/Local/hermes/skills/note-taking/` (Windows) or `~/.hermes/skills/note-taking/` |
| Anything else reading Agent Skills | any folder the tool scans for `SKILL.md` |

Restart the agent, or reload skills, if it does not show up. Its description triggers on "zoomable
learning map" and "zoom-in zoom-out map" without being named.

## Requirements

| Need | For | Notes |
|---|---|---|
| Python 3.9+ | both generators, `verify_links.py`, `audit_headless.py` | standard library only, nothing to `pip install` |
| A browser | `pixel_audit.js` | the audit is JavaScript; paste it in or drive it over CDP |
| Chrome or Edge | `audit_headless.py` | the four standard Windows paths, three Linux paths and one macOS path are searched |
| PyMuPDF (`pip install pymupdf`) | reading a **PDF** source | only for step 1 of the workflow; a plain-text source needs nothing |
| A network connection | the webfont | the only remote reference any page carries |

Offline, the pages still open and read: every font has a system fallback. The one consequence is the
`pixel_audit.js` rule above — await `document.fonts.ready`, or fallback metrics produce phantom
collisions. The prompt text on each chip (`data-hermes-send`) is read by the Hermes preview pane and
ignored by every other viewer; the chip's `href` carries the actual navigation.

## File tree

```
zoomable-learning-maps/
├── README.md                       this file
├── LICENSE                         MIT, © 2026 Chen Bin
├── CREDITS.md                      third-party attribution, including the design system
├── .gitignore                      __pycache__/, *.pyc, /out/, .DS_Store, Thumbs.db
├── SKILL.md                        the workflow an agent reads
├── references/
│   ├── spec-format.md              every spec field, its type, what the generator does with it
│   ├── design-system.md            palette, geometry constants, font metrics, page anatomy
│   └── master-authoring.md         the master's spec shape, its traps, the width ceilings
├── scripts/
│   ├── zoom_subchart.py            the generator: spec JSON in, zoom pages out
│   ├── emit_master.py              the master emitter: same CSS and geometry helpers
│   ├── verify_links.py             resolves every href, counts chips, re-checks structure
│   ├── pixel_audit.js              the measured getBBox() audit — paste it into a live page
│   └── audit_headless.py           runs pixel_audit.js over a folder with headless Chrome
├── examples/
│   ├── README.md                   how to run the demo set, and what a worked example will be
│   ├── spec-master-demo.json       a demo MASTER spec (illustrative content)
│   └── spec-demo.json              two demo zoom specs: one chart, one placeholder
└── docs/
    ├── verification.md             the commands I ran and their real output
    ├── owner-todos.md              what still needs the owner
    └── screenshots/README.md       the screenshots the README still needs
```

## What works and what does not

**Works.** Both emitters on the two demo specs; `verify_links.py` on the generated set; the pixel audit,
which ran 3 of 3 demo pages clean with 0 violations and a tightest right margin of 0 px (Chrome headless,
measured output in `docs/verification.md`). The pages open from `file://` and navigate between each other.

**Not tried.** Any source that is not a paper; a light theme; right-to-left text; a canvas width other
than 880 px; a legend with more items than the demo's four. Masters are emitted from a spec — nothing
infers one from a source document, so the first step is always a spec you write.

**Known limits.** The font metrics in `references/design-system.md` are the numbers the overflow check
uses, and the check is optimistic for non-ASCII text: Greek and mathematical glyphs are wider in the
same mono face, so a line that passes the character count can still overrun the content edge. The pixel
audit is the authority. A generated file is never the place to fix a defect: edit the spec and
regenerate, or the fix is lost on the next batch run.

<!-- TODO(owner): version tag — the frontmatter says 1.0.0; decide whether the public repo carries a v1.0.0 tag. -->

## Licence

MIT — see `LICENSE`, © 2026 Chen Bin. `SKILL.md` keeps `license: MIT` in its frontmatter so the folder is
still self-describing when installed on its own.

## Credits

- **`diagram-design`** (Hermes skill) — the source of the diagram design approach this method builds on:
  the palette, the type ramp, the geometry grammar, the chip anatomy and the static `self_check.py` gate.
  None of `references/design-system.md` is original to me; it is that skill's system recorded as the
  constants this generator emits. Not redistributed here — its licence terms and copyright holder could
  not be established, which `CREDITS.md` records.
- **`paper-structure-maps`** (Hermes skill) — the authoring doctrine this workflow uses for its reading
  side: pick argument beats rather than headings, one stable anchor chip per concept that is never
  renumbered, grep every number out of the extracted text instead of recalling it, and fix the return
  convention before the second chart exists.
- **`visual-artifact-verification`** (Hermes skill) — the rule that a generated artifact is not finished
  until the rendered pixels have been measured, which `pixel_audit.js` implements.
- **`interactive-concept-widgets`** (Hermes skill) — not used by this generator. Named in `CREDITS.md`
  only as the sibling skill for a concept that needs a widget instead of a static canvas.
- **Hermes Agent** — I wrote this with it under my direction; it is the `author:` field of `SKILL.md`.
- Geist, Geist Mono and Instrument Serif are loaded by URL from Google Fonts. No font file is in this
  repo and each family keeps its own terms upstream.

`CREDITS.md` carries the same list with the redistribution status of each item.
