#!/usr/bin/env python3
"""emit_master.py -- emit a MASTER structure map for a zoomable learning map.

The skill's zoom_subchart.py generates the zoom CHILDREN from specs. Masters are
hand-authored in the same design system; this helper removes the hand-editing risk
by reusing the generator's own geometry helpers and CSS verbatim, so a master and
its children cannot drift apart.

usage:
    python emit_master.py spec.json --out-dir <dir>

spec.json:
{
  "slug": "jms-dualarm",                       # file -> <slug>-structure-flowchart.html
  "eyebrow": "...", "h1": "...", "sub_lines": ["..."], "desc": "...",
  "bands": [{"tag": "1-2", "title": "...", "lines": ["..."],
             "focal": false, "chip": {"label": "Z1", "href": "...", "hermes": "..."},
             "loop": "ITERATE"}],
  "legend": [{"kind": "focal|node|arrow|iteration|dashed", "label": "..."}],
  "legend_note": "...",
  "cards": [{"n": "01", "t": "...", "b": "...", "focal": false}],
  "footer": ["...", "..."]
}
"""
import argparse
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)  # zoom_subchart.py sits beside this file
import zoom_subchart as z  # noqa: E402

INK, MUTED, SOFT = z.INK, z.MUTED, z.SOFT
PAPER, PAPER2, ACCENT, ACCENT_TINT, RULE = z.PAPER, z.PAPER2, z.ACCENT, z.ACCENT_TINT, z.RULE


def defs_and_style():
    out = []
    out.append('    <defs>')
    out.append('      <marker id="mp-ar" markerWidth="8" markerHeight="6" refX="7.5" refY="3" orient="auto" markerUnits="userSpaceOnUse">')
    out.append('        <polygon points="1.6,0 6.2,0 8,3 6.2,6 1.6,6 0,4.2 0,1.8" fill="%s"/>' % MUTED)
    out.append('      </marker>')
    out.append('      <marker id="mp-ar-acc" markerWidth="8" markerHeight="6" refX="7.5" refY="3" orient="auto" markerUnits="userSpaceOnUse">')
    out.append('        <polygon points="1.6,0 6.2,0 8,3 6.2,6 1.6,6 0,4.2 0,1.8" fill="%s"/>' % ACCENT)
    out.append('      </marker>')
    out.append('    </defs>')
    out.append('    <g class="zstyles"><style>')
    out.append("      .ntitle{font-family:'Geist',system-ui,sans-serif;font-size:12px;font-weight:600;fill:%s}" % INK)
    out.append("      .nline{font-family:'Geist Mono',ui-monospace,Consolas,monospace;font-size:9px;letter-spacing:0.02em;fill:%s}" % MUTED)
    out.append("      .tagtxt{font-family:'Geist Mono',ui-monospace,Consolas,monospace;font-size:7.5px;letter-spacing:0.08em;fill:%s;text-anchor:middle}" % SOFT)
    out.append("      .chiptxt{font-family:'Geist Mono',ui-monospace,Consolas,monospace;font-size:8px;letter-spacing:0.10em;fill:%s;text-anchor:middle}" % SOFT)
    out.append("      .alabel{font-family:'Geist Mono',ui-monospace,Consolas,monospace;font-size:8px;letter-spacing:0.10em;fill:%s;text-anchor:middle}" % SOFT)
    out.append("      .alabel-acc{font-family:'Geist Mono',ui-monospace,Consolas,monospace;font-size:8px;letter-spacing:0.10em;fill:%s;text-anchor:middle}" % ACCENT)
    out.append("      .hlabel{font-family:'Geist Mono',ui-monospace,Consolas,monospace;font-size:8px;letter-spacing:0.10em;fill:%s}" % SOFT)
    out.append("      .lgtitle{font-family:'Geist Mono',ui-monospace,Consolas,monospace;font-size:8px;letter-spacing:0.18em;fill:%s}" % SOFT)
    out.append("      .lgitem{font-family:'Geist Mono',ui-monospace,Consolas,monospace;font-size:8px;letter-spacing:0.06em;fill:%s}" % SOFT)
    out.append("      .lnkrule{stroke:rgba(245,245,245,0.18);stroke-width:0.6}")
    out.append('    </style></g>')
    return "\n".join(out)


def build_canvas(spec):
    bands = spec["bands"]
    slug = spec["slug"]

    plan, y = [], 40
    for i, nd in enumerate(bands):
        h = z.band_h(len(nd.get("lines", [])))
        plan.append((nd, y, h, i))
        y += h + (z.GAP_LOOP if nd.get("loop") else z.GAP)
    legend_y = y
    legend_h = z.legend_height(spec.get("legend", []), spec.get("legend_note", ""))
    canvas_h = int(round((legend_y + legend_h + 34) / 4.0) * 4)

    chunks = []
    chunks.append('  <svg viewBox="0 0 %d %d" role="img" aria-labelledby="%s-title %s-desc">' % (z.W, canvas_h, slug, slug))
    chunks.append('    <title id="%s-title">%s</title>' % (slug, z.esc(spec["h1"])))
    chunks.append('    <desc id="%s-desc">%s</desc>' % (slug, z.esc(spec["desc"])))
    chunks.append(defs_and_style())
    chunks.append('    <rect width="%d" height="%d" fill="%s"/>' % (z.W, canvas_h, PAPER))

    # connectors first, never over a box
    conns = []
    prev_bottom = None
    for nd, ny, h, i in plan:
        if prev_bottom is not None:
            conns.append(z.arrow_line(z.CHAIN_X, prev_bottom, z.CHAIN_X, ny,
                                      accent=bool(nd.get("focal"))))
        prev_bottom = ny + h
        if nd.get("loop"):
            conns.append(z.self_loop(ny + h, nd["loop"]))
    chunks.append('    <!-- connectors, drawn before the boxes -->')
    chunks.append('    <g fill="none" stroke="%s" stroke-width="1.2">' % MUTED)
    chunks.extend(conns)
    chunks.append('    </g>')

    chunks.append('  <!-- content boxes -->')
    for nd, ny, h, i in plan:
        m, _ = z.draw_band(nd, z.MARGIN, ny, z.CW, slug, None)
        chunks.append(m)

    lm, _ = z.legend_strip(spec.get("legend", []), spec.get("legend_note", ""), legend_y, slug)
    chunks.append(lm)
    chunks.append('  </svg>')
    return "\n".join(chunks), canvas_h


def _fix_h(html, h):
    """The canvas height is only known after layout: force the footer to agree."""
    return re.sub(r"canvas 880 \u00d7 \d+", "canvas 880 \u00d7 %d" % h, html)


def build_page(spec):
    svg, h = build_canvas(spec)
    p = []
    p.append('<!DOCTYPE html>')
    p.append('<html lang="en">')
    p.append('<head>')
    p.append('<meta charset="utf-8">')
    p.append('<meta name="viewport" content="width=device-width, initial-scale=1">')
    p.append('<title>%s</title>' % z.esc(spec["h1"]))
    p.append('<link href="%s" rel="stylesheet">' % z.FONT_LINK)
    p.append('<style>')
    p.append(z.CSS)
    p.append('</style>')
    p.append('</head>')
    p.append('<body>')
    p.append('<div class="wrap">')
    p.append('')
    p.append('  <header>')
    p.append('    <p class="eyebrow">%s</p>' % z.esc(spec["eyebrow"]))
    p.append('    <h1>%s</h1>' % z.esc(spec["h1"]))
    p.append('    <p class="sub">')
    for i, ln in enumerate(spec.get("sub_lines", [])):
        tail = '' if i == len(spec["sub_lines"]) - 1 else '<br>'
        p.append('      %s%s' % (ln, tail))
    p.append('    </p>')
    p.append('    <hr class="rule">')
    p.append('  </header>')
    p.append('')
    p.append('  <div class="canvas">')
    p.append(svg)
    p.append('  </div>')
    p.append('')
    p.append('  <div class="cards">')
    for c in spec.get("cards", []):
        p.append('    <div class="card%s">' % (' focal' if c.get('focal') else ''))
        p.append('      <span class="tag">%s</span>' % z.esc(c["n"]))
        p.append('      <h3>%s</h3>' % z.esc(c["t"]))
        if c.get("list"):
            p.append('      <ul>')
            for li in c["list"]:
                p.append('        <li>%s</li>' % li)
            p.append('      </ul>')
        else:
            p.append('      <p>%s</p>' % c["b"])
        p.append('    </div>')
    p.append('  </div>')
    p.append('')
    p.append('  <footer>')
    for i, ln in enumerate(spec.get("footer", [])):
        tail = '' if i == len(spec["footer"]) - 1 else '<br>'
        p.append('    %s%s' % (ln.replace('{H}', str(h)), tail))
    p.append('  </footer>')
    p.append('</div>')
    p.append('</body>')
    p.append('</html>')
    return _fix_h("\n".join(p), h), h


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("spec")
    ap.add_argument("--out-dir", required=True)
    args = ap.parse_args()
    with open(args.spec, "r", encoding="utf-8") as fh:
        specs = json.load(fh)
    if isinstance(specs, dict):
        specs = [specs]
    os.makedirs(args.out_dir, exist_ok=True)
    for spec in specs:
        html, h = build_page(spec)
        name = spec["slug"] + "-structure-flowchart.html"
        with open(os.path.join(args.out_dir, name), "w", encoding="utf-8", newline="\n") as fh:
            fh.write(html)
        print("%-58s %6d bytes  canvas 880 x %d" % (name, len(html.encode("utf-8")), h))
    if z.WARNINGS:
        print("\nOVERFLOW WARNINGS (%d):" % len(z.WARNINGS))
        for w in z.WARNINGS:
            print("  - " + w)
    else:
        print("\nno text-overflow warnings")


if __name__ == "__main__":
    main()
