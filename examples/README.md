# examples

Two spec files, both illustrative. Every string in them is invented to show the format; nothing in them
is a finding from any source. They exist so you can run both emitters end to end before writing a spec
against a real document.

## Run the demo set

From the repo root:

```bash
python scripts/emit_master.py   examples/spec-master-demo.json --out-dir ./out/demo
python scripts/zoom_subchart.py examples/spec-demo.json        --out-dir ./out/demo
```

`spec-master-demo.json` emits the master, `spec-demo.json` emits its two zoom pages. The emitted files,
as measured on this tree:

```
demo-structure-flowchart.html        9886 bytes  canvas 880 x 560
demo-z1-the-workflow-zoom.html      12055 bytes  chart        canvas 880 x 900
demo-z2-still-to-build-zoom.html     8242 bytes  placeholder  canvas 880 x 528
```

Both commands printed `no text-overflow warnings`. Open the master in a browser first, then the chart
page, then the placeholder. The pages read from `file://` with no build step; `./out/` is ignored by
git, so nothing in it is published.

One page is a chart, the other is the placeholder variant: a zoom that is promised but not built ships
as a real, accessible page saying what it will answer, never as filler.

## Check the demo set

```bash
python scripts/verify_links.py ./out/demo      # expect: PROBLEMS: none, exit 0
python scripts/audit_headless.py ./out/demo    # expect: PAGES_BAD: 0, exit 0
```

`verify_links.py` resolves every href, so the demo set is closed: the two zoom pages name
`demo-structure-flowchart.html` as their parent, and that master exists once you have run the master
emitter. Emit the zoom pages alone and you get one `DEAD LINK` per page — the generator makes zoom pages,
not masters, so the link home has nothing to point at until the master is emitted too.

The static gate (`diagram-design/scripts/self_check.py`) is a separate skill and is not bundled here.
See "The static gate (not bundled)" in the README.

## Worked example

Not published yet. The map I built as the test case was charted from a paper I do not have permission to
republish, so it is not in this repo and is not named here. A worked example rebuilt against a public
CC-BY paper is coming; the plan for it is in `docs/owner-todos.md`.

Read `SKILL.md` before your first real chart. The demo proves the machinery runs; it does not teach the
craft.
