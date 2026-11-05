"""verify_links.py <folder> -- audit a zoomable learning map folder.

Checks, per HTML file in the folder:
  * every local href resolves to a file that exists (dead chip == dead end for the reader)
  * how many chips, hrefs and data-hermes-send prompts each file carries
  * the structural rules the diagram-design gate enforces, so a failure here is diagnosable
    without re-running the gate: <title id>, lang attribute, aria-labelledby, no remote
    dependency other than the fonts.googleapis.com/css2 stylesheet, no embedded raster/xlink

usage:
    python verify_links.py ./out/demo

Exit code 0 means no problems; 1 means at least one problem was printed.
"""
import os
import re
import sys

if len(sys.argv) < 2:
    print(__doc__)
    sys.exit(2)

D = sys.argv[1]
files = sorted(f for f in os.listdir(D) if f.endswith(".html"))
if not files:
    print("no .html files in", D)
    sys.exit(1)

problems = []

for f in files:
    path = os.path.join(D, f)
    html = open(path, encoding="utf-8").read()

    hrefs = sorted(set(re.findall(r'href="([^"]+)"', html)))
    for h in hrefs:
        if h.startswith("http") or h.startswith("#"):
            continue
        if not os.path.exists(os.path.join(D, h)):
            problems.append("DEAD LINK    %s -> %s" % (f, h))

    chips = len(re.findall(r'class="chipbox"', html))
    sends = len(re.findall(r'data-hermes-send="', html))
    print("%-48s %6d bytes  hrefs=%-2d chips=%-2d sends=%-2d" %
          (f, os.path.getsize(path), len(hrefs), chips, sends))

    if "<svg" in html:
        slug_checks = [
            ("<title id=", "NO SVG TITLE  "),
            ('<html lang=', "NO LANG       "),
            ("aria-labelledby", "NO ARIA       "),
        ]
        for needle, label in slug_checks:
            if needle not in html:
                problems.append(label + f)
        remote = set(re.findall(r'(?:src|href)="(https?://[^"]+)"', html))
        for r in remote:
            if "fonts.googleapis.com/css2" not in r:
                problems.append("REMOTE DEP   %s -> %s" % (f, r))
        if "<image" in html or "xlink:href" in html:
            problems.append("SVG IMAGE REF  " + f)
    else:
        problems.append("NO SVG        " + f)

print()
if problems:
    print("PROBLEMS (%d):" % len(problems))
    for p in problems:
        print("  " + p)
    sys.exit(1)
print("PROBLEMS: none")
