/* pixel_audit.js — measured layout audit for zoomable learning maps.
 *
 * The static gate (diagram-design/scripts/self_check.py) checks structure and accessibility.
 * It does not know where text lands. This audit measures the rendered SVG instead, which is
 * the only way to catch text escaping its box or two labels colliding.
 *
 * HOW TO RUN
 *   Browser tool / CDP, one file per page:
 *       goto_url("file:///.../chart.html"); wait_for_load();
 *       print(js("(() => { <contents of this file> ; return zoomAudit(); })()"))
 *   Devtools: open the chart, paste this file, then call zoomAudit().
 *   Pass condition: violations.offCanvas + pastContentEdge + textCollisions === 0 on every file.
 *
 * All numbers are in SVG user units (getBBox), so page scaling and window size cannot
 * distort the result. The family's design system: canvas is 880 wide, margin 40,
 * so every content box ends at x = 840 — that is the boundary text must respect.
 */
function zoomAudit(opts) {
  opts = opts || {};
  var CONTENT_RIGHT = opts.contentRight || 840;   // boxes end here
  var svg = document.querySelector('svg');
  if (!svg) return {file: location.href.split('/').pop(), fatal: 'no <svg> on the page'};

  var vb = (svg.getAttribute('viewBox') || '0 0 880 0').trim().split(/[\s,]+/).map(Number);
  var vx = vb[0], vy = vb[1], vw = vb[2], vh = vb[3];

  var items = [];
  var texts = svg.querySelectorAll('text');
  for (var i = 0; i < texts.length; i++) {
    var t = texts[i];
    var b = t.getBBox();
    if (b.width <= 0 && b.height <= 0) continue;                     // empty/degenerate
    items.push({
      s: t.textContent.trim().replace(/\s+/g, ' '),
      x1: b.x, y1: b.y, x2: b.x + b.width, y2: b.y + b.height
    });
  }

  function tag(a) {
    return a.s.slice(0, 62) + '  @x' + Math.round(a.x1) + '..' + Math.round(a.x2) +
           ' y' + Math.round(a.y1) + '..' + Math.round(a.y2);
  }

  var offCanvas = [], pastEdge = [];
  for (i = 0; i < items.length; i++) {
    var a = items[i];
    if (a.x1 < vx - 0.5 || a.x2 > vx + vw + 0.5 || a.y1 < vy - 0.5 || a.y2 > vy + vh + 0.5) offCanvas.push(a);
    if (a.x2 > CONTENT_RIGHT + 0.5) pastEdge.push(a);
  }

  // pairwise text collisions: more than 1px of overlap on both axes is a real collision,
  // not two labels that merely share a baseline tightly
  var collisions = [];
  for (i = 0; i < items.length; i++) {
    for (var j = i + 1; j < items.length; j++) {
      var p = items[i], q = items[j];
      var dx = Math.min(p.x2, q.x2) - Math.max(p.x1, q.x1);
      var dy = Math.min(p.y2, q.y2) - Math.max(p.y1, q.y1);
      if (dx > 1 && dy > 1) collisions.push(tag(p) + '   ||   ' + tag(q));
    }
  }

  var tight = Infinity;
  for (i = 0; i < items.length; i++) tight = Math.min(tight, CONTENT_RIGHT - items[i].x2);

  return {
    file: location.href.split('/').pop(),
    canvas: {viewBox: svg.getAttribute('viewBox'), height: Math.round(vh)},
    counts: {
      texts: items.length,
      links: svg.querySelectorAll('a').length,
      chips: svg.querySelectorAll('.chipbox').length
    },
    violations: {
      offCanvas: offCanvas.map(tag),
      pastContentEdge: pastEdge.map(tag),
      textCollisions: collisions
    },
    tightestRightMarginPx: isFinite(tight) ? Math.round(tight) : null,
    pass: offCanvas.length + pastEdge.length + collisions.length === 0
  };
}

/* Report shape (one object per file):
 *   {file, canvas:{viewBox,height}, counts:{texts,links,chips},
 *    violations:{offCanvas:[], pastContentEdge:[], textCollisions:[]},
 *    tightestRightMarginPx, pass}
 *
 * Reading it:
 *   pastContentEdge  -> a line is wider than the box it sits in. Shorten the wording, split the
 *                       line, or widen the box. At 9px mono the advance is ~5.4px/char, so a line
 *                       at x=56 tops out near 138 characters.
 *   textCollisions   -> two labels in the same place (usually a row node drawn twice, or a legend
 *                       that did not wrap). Fix it in the generator, never in the generated file.
 *   offCanvas        -> a label bigger than the canvas; almost always the same root cause.
 *   tightestRightMarginPx < 6 -> the page is legal but crowded; expect the next wording edit to break it.
 */
