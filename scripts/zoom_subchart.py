#!/usr/bin/env python3
"""
zoom_subchart.py -- generate zoom sub-charts (and placeholder pages) for a
zoomable learning map: the zoom-in / zoom-out framework.

The master chart carries one anchor chip (`Z1`, `Z2`, ...) per concept. Each
anchor names a chart file. This script emits those files in the same design
system as the master, with the return convention baked in:

  * the child repeats its own anchor chip top-left, as a link back to the master
  * the child names the master node it re-enters, top-right
  * the child closes with a hand-off row: a terminator ("zoom back out") plus a
    dashed box listing the next zooms

usage:
    python zoom_subchart.py spec.json --out-dir <dir>
    python zoom_subchart.py spec.json --out-dir <dir> --check-only

spec.json is either one object or a list of objects. Each object:

{
  "slug": "topic-z3-<concept-slug>-zoom",   # file stem + id prefix, written verbatim as <slug>.html
  "anchor": "Z3", "zoom_index": 3, "zoom_total": 8, "section": "\u00a73.1\u20133.2",
  "parent_file": "topic-structure-flowchart.html",
  "parent_node": "\u00a73.1\u20133.2 \u00b7 <the master block this page re-enters>",
  "h1": "...", "sub_lines": ["...", "..."], "desc": "...",
  "chain":  [{"tag": "3.1", "title": "...", "lines": ["..."], "focal": false, "chip": false}],
  "loop_after": 1, "loop_label": "ITERATE",
  "rows":   [{"header": "...", "incoming": true, "connect": false,
              "nodes": [{"title": "...", "lines": ["..."]}]}],
  "handoff": {"terminator_title": "ZOOM BACK OUT", "terminator_sub": "...",
              "next_title": "NEXT ZOOMS \u2014 one concept at a time",
              "next": [{"anchor": "Z4", "text": "...", "file": "...", "built": true}]},
  "legend": [{"kind": "node|focal|arrow|dashed", "label": "..."}],
  "legend_note": "...",
  "cards": [{"n": "01", "t": "...", "b": "...", "focal": false, "list": ["..."]}],
  "footer": ["...", "..."],
  "placeholder": false,            # true -> HTML-only "what this zoom covers" page
  "placeholder_bullets": ["..."],  # used when placeholder is true
  "placeholder_note": "..."
}
"""

import argparse
import json
import os
import re
import sys

# ---------------------------------------------------------------- geometry ---
W, MARGIN = 880, 40
CW = W - 2 * MARGIN          # 800
CHAIN_X = 200                # vertical spine inside the canvas
LOOP_X0, LOOP_X1 = 260, 340  # accent self-loop attach points
LINE_PITCH = 20
GAP = 40
GAP_LOOP = 64
ROW_GAP = 24

# font metrics for the overflow check (advance width per character, px)
MONO9 = 5.4
TITLE12 = 6.65
MONO85 = 5.1
TAG8 = 6.2

INK, MUTED, SOFT = "#f5f5f5", "#bfc0c0", "#8e98ac"
PAPER, PAPER2 = "#2d3142", "#393e53"
ACCENT, ACCENT_TINT = "#f08a59", "rgba(240,138,89,0.10)"
RULE = "rgba(245,245,245,0.12)"

CSS = """
  :root{
    --paper:#2d3142; --paper-2:#393e53; --ink:#f5f5f5; --muted:#bfc0c0; --soft:#8e98ac;
    --rule:rgba(245,245,245,0.12); --accent:#f08a59; --accent-tint:rgba(240,138,89,0.10);
  }
  *{box-sizing:border-box}
  html,body{margin:0;padding:0}
  body{
    background:var(--paper); color:var(--muted);
    font-family:'Geist',system-ui,-apple-system,'Segoe UI',sans-serif;
    font-size:14px; line-height:1.6; -webkit-font-smoothing:antialiased;
  }
  .wrap{max-width:960px;margin:0 auto;padding:44px 32px 64px}
  .eyebrow{
    font-family:'Geist Mono',ui-monospace,'Cascadia Mono',Consolas,monospace;
    font-size:9px;letter-spacing:0.18em;text-transform:uppercase;color:var(--soft);margin:0 0 10px
  }
  h1{
    font-family:'Instrument Serif',Georgia,serif;font-weight:400;font-size:38px;line-height:1.1;
    color:var(--ink);margin:0 0 10px;letter-spacing:-0.01em
  }
  .sub{
    font-family:'Geist Mono',ui-monospace,'Cascadia Mono',Consolas,monospace;
    font-size:9.5px;line-height:1.7;letter-spacing:0.04em;color:var(--soft);margin:0
  }
  hr.rule{border:0;border-top:0.5px solid var(--rule);margin:22px 0 0}
  .canvas{margin:26px 0 0;border:0.5px solid var(--rule);border-radius:2px;overflow:hidden}
  svg{display:block;width:100%;height:auto}
  .cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(250px,1fr));gap:20px;margin:34px 0 0}
  .card{border:0.5px solid var(--rule);border-radius:2px;padding:18px 18px 16px}
  .card .tag{
    font-family:'Geist Mono',ui-monospace,monospace;font-size:8.5px;letter-spacing:0.16em;
    text-transform:uppercase;color:var(--soft);display:block;margin-bottom:10px
  }
  .card h3{font-size:15px;font-weight:600;color:var(--ink);margin:0 0 8px;line-height:1.35}
  .card p{margin:0;font-size:14px;line-height:1.62}
  .card ol,.card ul{margin:0;padding-left:18px;font-size:14px;line-height:1.7}
  .card li{margin-bottom:5px}
  .card li:last-child{margin-bottom:0}
  .card code{font-family:'Geist Mono',ui-monospace,monospace;font-size:12.5px;color:var(--ink)}
  .focal{border-left:2px solid var(--accent);padding-left:16px}
  footer{
    margin:34px 0 0;padding-top:14px;border-top:0.5px solid var(--rule);
    font-family:'Geist Mono',ui-monospace,monospace;font-size:9px;line-height:1.8;
    letter-spacing:0.04em;color:var(--soft)
  }
  a{text-decoration:none;cursor:pointer}
  a:hover .chipbox{stroke:rgba(240,138,89,0.95)}
  a:hover .chiptxt{fill:#f5f5f5}
  a:hover .lnkln{fill:#f5f5f5}
  a:hover .lnkrule{stroke:rgba(240,138,89,0.95)}
"""

FONT_LINK = (
    "https://fonts.googleapis.com/css2?family=Geist:wght@400;500;600"
    "&family=Geist+Mono:wght@400;500&family=Instrument+Serif:ital@0;1&display=swap"
)

WARNINGS = []


def warn(msg):
    WARNINGS.append(msg)


def esc(s):
    return (s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


def r4(v):
    """snap to the 4 px grid"""
    return int(round(v / 4.0)) * 4


def tag_w(tag):
    return max(30, r4(len(tag) * TAG8 + 12))


def band_h(n_lines):
    """76 + 20 per line: title at +44, lines from +66, 30 px bottom pad"""
    return 76 + LINE_PITCH * n_lines


def check_text(kind, text, box_w, where):
    avail = box_w - 32
    per_char = MONO9 if kind == "line" else TITLE12
    limit = int(avail / per_char)
    if len(text) > limit:
        warn("%s: %d chars in a %d px box (max ~%d): %r" % (where, len(text), box_w, limit, text))


def wrap_tspans(text, x, y, cls, width_chars):
    """centred single-line text; every tspan carries x so XML/edit-round-trips hold"""
    return '  <text x="%s" y="%s" class="%s">%s</text>' % (x, y, cls, esc(text))


def wrap_lines(text, max_chars):
    """greedy word wrap, for bullets drawn inside a full-width band"""
    words, lines, cur = text.split(), [], ""
    for w in words:
        cand = (cur + " " + w).strip()
        if len(cand) <= max_chars:
            cur = cand
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


# ------------------------------------------------------------------ pieces ---
def draw_band(node, x, y, w, slug, chip_map, focal_ok=True):
    """a full-width or row-width node. returns (markup, height)"""
    lines = node.get("lines", [])
    h = band_h(len(lines))
    focal = bool(node.get("focal")) and focal_ok
    fill = ACCENT_TINT if focal else PAPER2
    stroke = ACCENT if focal else INK
    out = []
    out.append('    <rect x="%d" y="%d" width="%d" height="%d" fill="%s" stroke="%s" stroke-width="1"/>'
               % (x, y, w, h, fill, stroke))
    tag = node.get("tag")
    if tag:
        tw = tag_w(tag)
        out.append('    <rect class="tagbox" x="%d" y="%d" width="%d" height="12" rx="2" fill="%s" stroke="rgba(245,245,245,0.28)" stroke-width="0.6"/>'
                   % (x + 8, y + 6, tw, PAPER))
        out.append('    <text x="%.1f" y="%d" class="tagtxt">%s</text>'
                   % (x + 8 + tw / 2.0, y + 15, esc(tag)))
    title = node.get("title", "")
    out.append('    <text x="%d" y="%d" class="ntitle">%s</text>' % (x + 16, y + 44, esc(title)))
    check_text("title", title, w, "%s node title" % slug)
    for i, ln in enumerate(lines):
        out.append('    <text x="%d" y="%d" class="nline">%s</text>' % (x + 16, y + 66 + i * LINE_PITCH, esc(ln)))
        check_text("line", ln, w, "%s node line" % slug)
    chip = node.get("chip")
    if chip:
        r = x + w
        out.append('    <a href="%s" class="zlink" data-hermes-send="%s">'
                   % (chip["href"], esc(chip["hermes"])))
        out.append('      <rect x="%d" y="%d" width="36" height="24" rx="3" fill="transparent"/>' % (r - 38, y))
        out.append('      <rect class="chipbox" x="%d" y="%d" width="24" height="12" rx="2" fill="%s" stroke="rgba(245,245,245,0.30)" stroke-width="0.6"/>'
                   % (r - 32, y + 6, PAPER))
        out.append('      <text class="chiptxt" x="%d" y="%d" text-anchor="middle">%s</text>'
                   % (r - 20, y + 15, esc(chip["label"])))
        out.append('    </a>')
    return "\n".join(out), h


def arrow_line(x1, y1, x2, y2, accent=False):
    marker = "mp-ar-acc" if accent else "mp-ar"
    stroke = ACCENT if accent else MUTED
    return ('    <line x1="%s" y1="%s" x2="%s" y2="%s" stroke="%s" marker-end="url(#%s)"/>'
            % (x1, y1, x2, y2, stroke, marker))


def self_loop(y_bottom, label):
    y = y_bottom
    path = ("M%d %d V%d A8 8 0 0 0 %d %d H%d A8 8 0 0 0 %d %d V%d"
            % (LOOP_X0, y, y + 6, LOOP_X0 + 8, y + 14, LOOP_X1 - 8, LOOP_X1, y + 6, y))
    out = ['    <path d="%s" stroke="%s" fill="none" marker-end="url(#mp-ar-acc)"/>' % (path, ACCENT)]
    if label:
        h = 12
        lx = LOOP_X1 + 8
        lw = r4(len(label) * MONO85 + 10)
        out.append('    <rect x="%d" y="%d" width="%d" height="%d" rx="2" fill="%s"/>'
                   % (lx + 2, y + 5, lw, h, PAPER))
        out.append('    <text x="%.1f" y="%d" class="alabel-acc">%s</text>'
                   % (lx + 2 + lw / 2.0, y + 14, esc(label)))
    return "\n".join(out)


MONO_ADV = 5.6   # px per char, 8 px Geist Mono with 0.06em tracking (measured in-browser)
LEG_X0 = 100     # legend items start clear of the LEGEND label


def legend_item_w(it):
    icon = 26 if it["kind"] in ("node", "focal", "dashed") else 30
    return icon + int(len(it["label"]) * MONO_ADV) + 22


def legend_layout(items):
    """items left to right, wrapped into as many rows as the canvas needs"""
    rows, cur, x = [], [], LEG_X0
    for it in items:
        w = legend_item_w(it)
        if cur and x + w > MARGIN + CW:
            rows.append(cur)
            cur, x = [], LEG_X0
        cur.append((x, it))
        x += w
    if cur:
        rows.append(cur)
    return rows


def legend_note_own_line(rows, note):
    if not note:
        return False
    if not rows or not rows[-1]:
        return True
    x, it = rows[-1][-1]
    return x + legend_item_w(it) + int(len(note) * MONO_ADV) + 16 > MARGIN + CW


def legend_height(items, note):
    rows = legend_layout(items)
    h = 34 + 20 * max(0, len(rows) - 1)
    if legend_note_own_line(rows, note):
        h += 20
    return h


def legend_strip(items, note, y_top, slug):
    """returns (markup, bottom_y)"""
    rows = legend_layout(items)
    out = []
    y = y_top
    out.append('  <line x1="40" y1="%d" x2="840" y2="%d" stroke="%s" stroke-width="0.5"/>' % (y, y, RULE))
    out.append('  <text x="40" y="%d" class="lgtitle">LEGEND</text>' % (y + 18))
    for ri, row in enumerate(rows):
        ly = y + 18 + 20 * ri
        for x, it in row:
            kind, label = it["kind"], it["label"]
            if kind in ("node", "focal"):
                fill, stroke = (ACCENT_TINT, ACCENT) if kind == "focal" else (PAPER2, INK)
                out.append('  <rect x="%d" y="%d" width="20" height="10" fill="%s" stroke="%s" stroke-width="1"/>'
                           % (x, ly - 9, fill, stroke))
                x += 26
            elif kind in ("arrow", "accent", "iteration"):
                stroke = ACCENT if kind in ("accent", "iteration") else MUTED
                marker = "mp-ar-acc" if kind in ("accent", "iteration") else "mp-ar"
                out.append('  <line x1="%d" y1="%d" x2="%d" y2="%d" stroke="%s" stroke-width="1.2" marker-end="url(#%s)"/>'
                           % (x, ly - 4, x + 22, ly - 4, stroke, marker))
                x += 30
            elif kind == "dashed":
                out.append('  <rect x="%d" y="%d" width="20" height="10" fill="none" stroke="%s" stroke-width="1" stroke-dasharray="3 3"/>'
                           % (x, ly - 9, SOFT))
                x += 26
            else:
                warn("%s legend: unknown kind %r (drawn label-only)" % (slug, kind))
            out.append('  <text x="%d" y="%d" class="lgitem">%s</text>' % (x, ly, esc(label)))
    ly = y + 18 + 20 * max(0, len(rows) - 1)
    if note:
        if legend_note_own_line(rows, note):
            out.append('  <text x="40" y="%d" class="lgitem">%s</text>' % (ly + 20, esc(note)))
        else:
            out.append('  <text x="840" y="%d" class="lgitem" text-anchor="end">%s</text>' % (ly, esc(note)))
    return "\n".join(out), y_top + legend_height(items, note)


# ------------------------------------------------------------------- chart ---
def build_svg(spec):
    slug, anchor = spec["slug"], spec["anchor"]
    chain = spec.get("chain", [])
    rows = spec.get("rows", [])
    handoff = spec.get("handoff", {})
    loop_after = spec.get("loop_after")
    loop_label = spec.get("loop_label", "")

    # ---- pass 1: geometry
    plan = []
    y = 104
    for i, node in enumerate(chain):
        h = band_h(len(node.get("lines", [])))
        plan.append(("band", node, MARGIN, y, CW, h, i))
        y += h + (GAP_LOOP if loop_after == i else GAP)
    for r in rows:
        n = len(r["nodes"])
        w = r4((CW - (n - 1) * ROW_GAP) / float(n))
        total = n * w + (n - 1) * ROW_GAP
        ox = MARGIN + r4((CW - total) / 2.0)
        rowh = band_h(max(len(nd.get("lines", [])) for nd in r["nodes"]))
        plan.append(("row", r, ox, y, w, rowh, n))
        y += rowh + GAP
    hh = 96
    if handoff:
        hh = max(band_h(1), 60 + 20 * len(handoff.get("next", [])))
    handoff_y = y
    y += hh + 44
    legend_y = y
    legend_bottom = legend_y + legend_height(spec.get("legend", []), spec.get("legend_note", ""))
    canvas_h = int(round(legend_bottom + 34) / 4.0 * 4)

    # ---- pass 2: markup
    chunks = []
    chunks.append('  <svg viewBox="0 0 %d %d" role="img" aria-labelledby="%s-title %s-desc">'
                  % (W, canvas_h, slug, slug))
    chunks.append('    <title id="%s-title">%s</title>' % (slug, esc(spec["h1"])))
    chunks.append('    <desc id="%s-desc">%s</desc>' % (slug, esc(spec["desc"])))
    chunks.append('    <defs>')
    chunks.append('      <marker id="mp-ar" markerWidth="8" markerHeight="6" refX="7.5" refY="3" orient="auto" markerUnits="userSpaceOnUse">')
    chunks.append('        <polygon points="1.6,0 6.2,0 8,3 6.2,6 1.6,6 0,4.2 0,1.8" fill="%s"/>' % MUTED)
    chunks.append('      </marker>')
    chunks.append('      <marker id="mp-ar-acc" markerWidth="8" markerHeight="6" refX="7.5" refY="3" orient="auto" markerUnits="userSpaceOnUse">')
    chunks.append('        <polygon points="1.6,0 6.2,0 8,3 6.2,6 1.6,6 0,4.2 0,1.8" fill="%s"/>' % ACCENT)
    chunks.append('      </marker>')
    chunks.append('    </defs>')
    chunks.append('    <rect width="%d" height="%d" fill="%s"/>' % (W, canvas_h, PAPER))
    chunks.append('    <g class="zstyles"><style>')
    chunks.append('      .ntitle{font-family:\'Geist\',system-ui,sans-serif;font-size:12px;font-weight:600;fill:%s}' % INK)
    chunks.append('      .nline{font-family:\'Geist Mono\',ui-monospace,Consolas,monospace;font-size:9px;letter-spacing:0.02em;fill:%s}' % MUTED)
    chunks.append('      .tagtxt{font-family:\'Geist Mono\',ui-monospace,Consolas,monospace;font-size:7.5px;letter-spacing:0.08em;fill:%s;text-anchor:middle}' % SOFT)
    chunks.append('      .chiptxt{font-family:\'Geist Mono\',ui-monospace,Consolas,monospace;font-size:8px;letter-spacing:0.10em;fill:%s}' % SOFT)
    chunks.append('      .alabel{font-family:\'Geist Mono\',ui-monospace,Consolas,monospace;font-size:8px;letter-spacing:0.10em;fill:%s;text-anchor:middle}' % SOFT)
    chunks.append('      .alabel-acc{font-family:\'Geist Mono\',ui-monospace,Consolas,monospace;font-size:8px;letter-spacing:0.10em;fill:%s;text-anchor:middle}' % ACCENT)
    chunks.append('      .hlabel{font-family:\'Geist Mono\',ui-monospace,Consolas,monospace;font-size:8px;letter-spacing:0.10em;fill:%s}' % SOFT)
    chunks.append('      .rowhead{font-family:\'Geist Mono\',ui-monospace,Consolas,monospace;font-size:8.5px;letter-spacing:0.16em;fill:%s;text-transform:uppercase}' % SOFT)
    chunks.append('      .lgtitle{font-family:\'Geist Mono\',ui-monospace,Consolas,monospace;font-size:8px;letter-spacing:0.18em;fill:%s}' % SOFT)
    chunks.append('      .lgitem{font-family:\'Geist Mono\',ui-monospace,Consolas,monospace;font-size:8px;letter-spacing:0.06em;fill:%s}' % SOFT)
    chunks.append('      .lnkln{font-family:\'Geist Mono\',ui-monospace,Consolas,monospace;font-size:8.5px;letter-spacing:0.04em;fill:%s}' % MUTED)
    chunks.append('      .lnkrule{stroke:rgba(245,245,245,0.18);stroke-width:0.6}')
    chunks.append('    </style></g>')

    # ---- connectors first (never over a box)
    conns = []
    prev_bottom = None
    for item in plan:
        # bands and rows share the tuple layout (kind, _, x, y, w, h, idx)
        ny, h = item[3], item[5]
        idx = item[6] if item[0] == "band" else None
        if prev_bottom is not None:
            conns.append(arrow_line(CHAIN_X, prev_bottom, CHAIN_X, ny))
        prev_bottom = ny + h
        if item[0] == "band" and loop_after == idx:
            chunks_loop = self_loop(ny + h, loop_label)
            conns.append(chunks_loop)
            prev_bottom = ny + h
    # row internals + handoff arrow
    row_conns = []
    for item in plan:
        if item[0] == "row":
            _, r, ox, ry, w, rh, n = item
            if r.get("connect"):
                for j in range(n - 1):
                    row_conns.append(arrow_line(ox + j * (w + ROW_GAP) + w, ry + 40,
                                                ox + (j + 1) * (w + ROW_GAP), ry + 40))
    last_bottom = max(p[3] + p[5] for p in plan) if plan else 104
    conns.append(arrow_line(CHAIN_X, last_bottom, CHAIN_X, handoff_y))

    chunks.append('    <!-- connectors, drawn before the boxes -->')
    chunks.append('    <g fill="none" stroke="%s" stroke-width="1.2">' % MUTED)
    chunks.extend(conns)
    chunks.extend(row_conns)
    chunks.append('    </g>')

    # re-entry marker: the accent tick that says "this is where the zoom came from"
    chunks.append('  <rect x="40" y="40" width="34" height="18" rx="2" fill="%s" stroke="%s" stroke-width="0.8"/>' % (PAPER, ACCENT))
    chunks.append('  <text x="57" y="53" class="chiptxt" text-anchor="middle" style="fill:%s">%s</text>' % (ACCENT, esc(anchor)))
    chunks.append('  <a href="%s" class="zlink" data-hermes-send="Zoom back out: open %s">'
                  % (spec["parent_file"], esc(spec["parent_file"])))
    chunks.append('    <rect x="40" y="40" width="34" height="18" rx="2" fill="transparent"/>')
    chunks.append('  </a>')
    chunks.append('  <text x="86" y="53" class="hlabel">ZOOM %d of %d &#183; %s &#183; %s</text>'
                  % (spec["zoom_index"], spec["zoom_total"], esc(spec["section"]), esc(spec["parent_node"])))
    chunks.append('  <text x="840" y="53" class="hlabel" text-anchor="end">re-enters the master chart at %s</text>'
                  % esc(spec["section"]))

    # ---- boxes, in plan order
    chunks.append('  <!-- content boxes -->')
    for item in plan:
        if item[0] == "band":
            _, node, x, ny, w, h, idx = item
            m, _ = draw_band(node, x, ny, w, slug, None)
            chunks.append(m)
        else:
            _, r, ox, ry, w, rh, n = item
            if r.get("header"):
                chunks.append('  <text x="%d" y="%d" class="rowhead">%s</text>' % (MARGIN, ry - 14, esc(r["header"])))
            for j, nd in enumerate(r["nodes"]):
                m, _ = draw_band(nd, ox + j * (w + ROW_GAP), ry, w, slug, None)
                chunks.append(m)

    # ---- hand-off row
    if handoff:
        hh2 = max(band_h(1), 60 + 20 * len(handoff.get("next", [])))
        hy = handoff_y
        chunks.append('  <!-- hand-off: back out, and on to the next zoom -->')
        chunks.append('    <rect x="40" y="%d" width="384" height="%d" rx="2" fill="%s" stroke="%s" stroke-width="1"/>'
                      % (hy, hh2, PAPER2, INK))
        chunks.append('    <text x="56" y="%d" class="ntitle">%s</text>' % (hy + 44, esc(handoff.get("terminator_title", "ZOOM BACK OUT"))))
        chunks.append('    <text x="56" y="%d" class="nline">%s</text>' % (hy + 66, esc(handoff.get("terminator_sub", ""))))
        chunks.append('    <a href="%s" class="zlink" data-hermes-send="Zoom back out: open %s">' % (spec["parent_file"], esc(spec["parent_file"])))
        chunks.append('      <rect x="40" y="%d" width="384" height="%d" rx="2" fill="transparent"/>' % (hy, hh2))
        chunks.append('    </a>')
        dx = 456
        chunks.append('    <rect x="%d" y="%d" width="384" height="%d" rx="2" fill="none" stroke="%s" stroke-width="1" stroke-dasharray="3 3"/>'
                      % (dx, hy, hh2, SOFT))
        chunks.append('    <text x="%d" y="%d" class="hlabel">%s</text>'
                      % (dx + 16, hy + 22, esc(handoff.get("next_title", "NEXT ZOOMS"))))
        ly = hy + 48
        for it in handoff.get("next", []):
            colour = MUTED if it.get("built") else SOFT
            chunks.append('    <a href="%s" class="zlink" data-hermes-send="%s">' % (it["file"], esc(it.get("hermes", "Open zoom %s" % it["anchor"]))))
            chunks.append('      <rect x="%d" y="%d" width="352" height="16" fill="transparent"/>' % (dx + 16, ly - 11))
            chunks.append('      <line class="lnkrule" x1="%d" y1="%d" x2="%d" y2="%d" stroke="rgba(245,245,245,0.18)" stroke-width="0.6"/>' % (dx + 16, ly + 6, dx + 368, ly + 6))
            chunks.append('      <text class="lnkln" x="%d" y="%d" style="fill:%s">%s &#183; %s</text>'
                          % (dx + 18, ly, colour, esc(it["anchor"]), esc(it["text"])))
            chunks.append('    </a>')
            ly += 20

    lm, legend_bottom_calc = legend_strip(spec.get("legend", []), spec.get("legend_note", ""), legend_y, slug)
    chunks.append(lm)
    chunks.append('  </svg>')
    return "\n".join(chunks), canvas_h


# -------------------------------------------------------------------- page ---
def build_page(spec):
    svg, canvas_h = build_svg(spec)
    sub = "<br>\n      ".join(esc(s) for s in spec.get("sub_lines", []))
    cards = []
    for c in spec.get("cards", []):
        cls = ' class="card focal"' if c.get("focal") else ' class="card"'
        body = ""
        if c.get("list"):
            body = "<ol>" + "".join("<li>%s</li>" % esc(x) for x in c["list"]) + "</ol>"
        else:
            body = "<p>%s</p>" % c.get("b", "")
        cards.append('  <div%s>\n    <span class="tag">%s</span>\n    <h3>%s</h3>\n    %s\n  </div>'
                     % (cls, esc(c.get("n", "")), esc(c.get("t", "")), body))
    footer = "".join("<br>\n  " + esc(l) for l in spec.get("footer", []))
    return """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>%(h1)s</title>
<link href="%(font)s" rel="stylesheet">
<!--
  zoom sub-chart -- %(slug)s
  anchor %(anchor)s of the master chart %(parent_file)s
  canvas: %(W)d x %(H)d
  return convention: the chip top-left links back; the hand-off row closes the chart
-->
<style>%(css)s</style>
</head>
<body>
<div class="wrap">

  <header>
    <p class="eyebrow">%(eyebrow)s</p>
    <h1>%(h1)s</h1>
    <p class="sub">
      zoomed out of <code>%(parent_file)s</code> &#183; node %(parent_node)s, chip %(anchor)s<br>
      %(sub)s
    </p>
    <hr class="rule">
  </header>

<div class="canvas">
%(svg)s
</div>

<div class="cards">
%(cards)s
</div>

<footer>
  %(footer)s
</footer>

</div>
</body>
</html>
""" % dict(h1=esc(spec["h1"]), font=FONT_LINK, slug=spec["slug"], anchor=spec["anchor"],
           parent_file=esc(spec["parent_file"]), parent_node=esc(spec["parent_node"]),
           W=W, H=canvas_h, css=CSS, eyebrow=esc(spec.get("eyebrow", "")), sub=sub,
           svg=svg, cards="\n".join(cards), footer=footer)


def build_planned_svg(spec):
    """A planned zoom still needs a real canvas: one accessible SVG, dashed and empty.

    self-check requires every diagram file to carry an accessible SVG, so the
    placeholder draws the frame it will eventually fill instead of shipping bare HTML.
    """
    slug, anchor = spec["slug"], spec["anchor"]
    parent = spec["parent_file"]
    parent_node = spec.get("parent_node", "")
    section = spec.get("section", "")
    bullets = spec.get("placeholder_bullets", [])
    wrapped = [wrap_lines(b, 130) for b in bullets]
    n_text = sum(len(w) for w in wrapped)

    band_y = 104
    band_h = 96 + 22 * (n_text + len(wrapped))
    term_y = band_y + band_h + 44
    canvas_h = int(round((term_y + 152) / 4.0) * 4)

    o = []
    o.append('  <svg viewBox="0 0 %d %d" role="img" aria-labelledby="%s-title %s-desc">'
             % (W, canvas_h, slug, slug))
    o.append('    <title id="%s-title">%s</title>' % (slug, esc(spec["h1"])))
    o.append('    <desc id="%s-desc">%s</desc>' % (slug, esc(spec["desc"])))
    o.append('    <defs>')
    o.append('      <marker id="mp-ar" markerWidth="8" markerHeight="6" refX="7.5" refY="3" orient="auto" markerUnits="userSpaceOnUse">')
    o.append('        <polygon points="1.6,0 6.2,0 8,3 6.2,6 1.6,6 0,4.2 0,1.8" fill="%s"/>' % MUTED)
    o.append('      </marker>')
    o.append('    </defs>')
    o.append('    <rect width="%d" height="%d" fill="%s"/>' % (W, canvas_h, PAPER))
    o.append('    <g class="zstyles"><style>')
    o.append("      .ntitle{font-family:'Geist',system-ui,sans-serif;font-size:12px;font-weight:600;fill:%s}" % INK)
    o.append("      .nline{font-family:'Geist Mono',ui-monospace,Consolas,monospace;font-size:9px;letter-spacing:0.02em;fill:%s}" % MUTED)
    o.append("      .tagtxt{font-family:'Geist Mono',ui-monospace,Consolas,monospace;font-size:7.5px;letter-spacing:0.08em;fill:%s;text-anchor:middle}" % SOFT)
    o.append("      .chiptxt{font-family:'Geist Mono',ui-monospace,Consolas,monospace;font-size:8px;letter-spacing:0.10em;fill:%s}" % SOFT)
    o.append("      .hlabel{font-family:'Geist Mono',ui-monospace,Consolas,monospace;font-size:8px;letter-spacing:0.10em;fill:%s}" % SOFT)
    o.append("      .lnkln{font-family:'Geist Mono',ui-monospace,Consolas,monospace;font-size:8.5px;letter-spacing:0.04em;fill:%s}" % MUTED)
    o.append('      .lnkrule{stroke:rgba(245,245,245,0.18);stroke-width:0.6}')
    o.append("      .lgitem{font-family:'Geist Mono',ui-monospace,Consolas,monospace;font-size:8px;letter-spacing:0.06em;fill:%s}" % SOFT)
    o.append('    </style></g>')
    # header: the chip that brought the reader here, repeated as a link home
    o.append('  <rect x="40" y="40" width="34" height="18" rx="2" fill="%s" stroke="%s" stroke-width="0.8"/>' % (PAPER2, ACCENT))
    o.append('  <text x="57" y="53" class="chiptxt" text-anchor="middle" style="fill:%s">%s</text>' % (ACCENT, esc(anchor)))
    o.append('  <a href="%s" class="zlink" data-hermes-send="Zoom back out: open %s">' % (parent, esc(parent)))
    o.append('    <rect x="40" y="40" width="34" height="18" fill="transparent"/>')
    o.append('  </a>')
    o.append('  <text x="86" y="53" class="hlabel">ZOOM %d of %d · %s · %s</text>'
             % (spec["zoom_index"], spec["zoom_total"], esc(section), esc(parent_node)))
    o.append('  <text x="840" y="53" class="hlabel" text-anchor="end">re-enters the master chart at %s</text>' % esc(section))
    # the plan itself: dashed, because nothing here is drawn yet
    o.append('    <rect x="40" y="%d" width="800" height="%d" fill="%s" stroke="%s" stroke-width="1" stroke-dasharray="4 4"/>'
             % (band_y, band_h, PAPER2, MUTED))
    o.append('    <rect class="tagbox" x="48" y="%d" width="60" height="12" rx="2" fill="%s" stroke="rgba(245,245,245,0.28)" stroke-width="0.6"/>'
             % (band_y + 6, PAPER))
    o.append('    <text x="78" y="%d" class="tagtxt">PLANNED</text>' % (band_y + 15))
    o.append('    <text x="56" y="%d" class="ntitle">%s</text>' % (band_y + 44, esc(spec["h1"])))
    o.append('    <text x="56" y="%d" class="nline">not drawn yet · what opening this chip will have to cover</text>' % (band_y + 66))
    yy = band_y + 90
    for wl in wrapped:
        for j, ln in enumerate(wl):
            prefix = "\u00b7  " if j == 0 else "   "
            o.append('    <text x="56" y="%d" class="nline">%s</text>' % (yy, esc(prefix + ln)))
            yy += 20
        yy += 4
    # hand-off: back out, and sideways to the zooms that already exist
    o.append('    <rect x="40" y="%d" width="384" height="96" rx="2" fill="%s" stroke="%s" stroke-width="1"/>' % (term_y, PAPER2, INK))
    o.append('    <text x="56" y="%d" class="ntitle">ZOOM BACK OUT</text>' % (term_y + 44))
    o.append('    <text x="56" y="%d" class="nline">re-enters the master chart at %s (chip %s)</text>'
             % (term_y + 66, esc(section), esc(anchor)))
    o.append('  <a href="%s" class="zlink" data-hermes-send="Zoom back out: open %s">' % (parent, esc(parent)))
    o.append('    <rect x="40" y="%d" width="384" height="96" rx="2" fill="transparent"/>' % term_y)
    o.append('  </a>')
    o.append('    <rect x="456" y="%d" width="384" height="96" rx="2" fill="none" stroke="%s" stroke-width="1" stroke-dasharray="3 3"/>'
             % (term_y, SOFT))
    o.append('    <text x="472" y="%d" class="hlabel">ADJACENT ZOOMS \u2014 already drawn</text>' % (term_y + 22))
    ly = term_y + 46
    for item in spec.get("next_links", []):
        o.append('  <a href="%s" class="zlink" data-hermes-send="Open zoom %s">' % (item["file"], esc(item["anchor"])))
        o.append('    <rect x="472" y="%d" width="352" height="16" fill="transparent"/>' % (ly - 11))
        o.append('    <line class="lnkrule" x1="472" y1="%d" x2="824" y2="%d"/>' % (ly + 3, ly + 3))
        o.append('    <text x="476" y="%d" class="lnkln">%s \u00b7 %s</text>' % (ly, esc(item["anchor"]), esc(item["text"])))
        o.append('  </a>')
        ly += 22
    o.append('    <text x="40" y="%d" class="lgitem">the chip is live in the master chart \u2014 the dashed plan above is what opening it will produce</text>'
             % (term_y + 132))
    o.append('  </svg>')
    return "\n".join(o), canvas_h


def build_placeholder(spec):
    svg, canvas_h = build_planned_svg(spec)
    bullets = "".join("<li>%s</li>" % esc(b) for b in spec.get("placeholder_bullets", []))
    note = esc(spec.get("placeholder_note", ""))
    sub = "<br>\n      ".join(esc(s) for s in spec.get("sub_lines", []))
    footer = "".join("<br>\n  " + esc(l) for l in spec.get("footer", []))
    return """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>%(h1)s</title>
<link href="%(font)s" rel="stylesheet">
<!-- placeholder page: %(slug)s -- anchor %(anchor)s has no chart yet; this page states what it will cover -->
<style>%(css)s</style>
</head>
<body>
<div class="wrap">

  <header>
    <p class="eyebrow">%(eyebrow)s</p>
    <h1>%(h1)s</h1>
    <p class="sub">
      zoomed out of <code>%(parent_file)s</code> &#183; node %(parent_node)s, chip %(anchor)s<br>
      %(sub)s
    </p>
    <hr class="rule">
  </header>

  <div class="canvas">
%(svg)s
  </div>

  <div class="cards">
    <div class="card">
      <span class="tag">zoom %(anchor)s &#183; not built yet</span>
      <h3>What this zoom will cover</h3>
      <ul>
        %(bullets)s
      </ul>
    </div>
    <div class="card focal">
      <span class="tag">how to open it</span>
      <h3>Zoom back out, or ask for this one</h3>
      <p>%(note)s</p>
    </div>
  </div>

<footer>
  %(footer)s
</footer>

</div>
</body>
</html>
""" % dict(h1=esc(spec["h1"]), font=FONT_LINK, slug=spec["slug"], anchor=spec["anchor"],
           parent_file=esc(spec["parent_file"]), parent_node=esc(spec["parent_node"]),
           css=CSS, eyebrow=esc(spec.get("eyebrow", "")), sub=sub,
           bullets=bullets, note=note, footer=footer,
           svg=svg)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("spec")
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--check-only", action="store_true")
    args = ap.parse_args()

    with open(args.spec, "r", encoding="utf-8") as fh:
        specs = json.load(fh)
    if isinstance(specs, dict):
        specs = [specs]

    os.makedirs(args.out_dir, exist_ok=True)
    for spec in specs:
        if spec.get("placeholder"):
            html = build_placeholder(spec)
        else:
            html = build_page(spec)
        path = os.path.join(args.out_dir, spec["slug"] + ".html")
        if not args.check_only:
            with open(path, "w", encoding="utf-8", newline="\n") as fh:
                fh.write(html)
        print("%-58s %6d bytes  %s" % (spec["slug"] + ".html", len(html.encode("utf-8")),
                                       "placeholder" if spec.get("placeholder") else "chart"))
    if WARNINGS:
        print("\nOVERFLOW WARNINGS (%d):" % len(WARNINGS))
        for w in WARNINGS:
            print("  - " + w)
    else:
        print("\nno text-overflow warnings")


if __name__ == "__main__":
    main()
