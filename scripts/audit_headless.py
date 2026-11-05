#!/usr/bin/env python3
"""Run pixel_audit.js over chart pages with headless Chrome, no browser tool required.

Usage:
    python audit_headless.py <folder-or-file> [<file> ...]

Prints one line per page (canvas, text/link/chip counts, tightest right margin) and the full text of
any violation: text off-canvas, text past the 840 content edge, or two labels colliding. Exit code 1
when any page has a violation, so it can gate a build.

The pass condition matches the skill: offCanvas + pastContentEdge + textCollisions == 0 on every file.
"""
import json, os, pathlib, re, subprocess, sys, tempfile

HERE = pathlib.Path(__file__).resolve().parent
AUDIT = HERE / "pixel_audit.js"

BROWSERS = [
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    "/usr/bin/google-chrome", "/usr/bin/chromium", "/usr/bin/chromium-browser",
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
]

RUNNER = """
<script>
%s
function __dump(){
  var out = zoomAudit();
  var pre = document.createElement('pre'); pre.id = 'TESTOUT';
  pre.textContent = 'MEASURE_JSON:' + JSON.stringify(out);
  document.body.appendChild(pre);
}
window.addEventListener('load', function(){
  (document.fonts && document.fonts.ready ? document.fonts.ready : Promise.resolve()).then(__dump);
});
</script>
"""


def unescape(s):
    for a, b in (("&quot;", '"'), ("&lt;", "<"), ("&gt;", ">"), ("&#39;", "'"), ("&amp;", "&")):
        s = s.replace(a, b)
    return s


def main(argv):
    if not argv:
        print(__doc__)
        return 2
    if not AUDIT.exists():
        print("missing pixel_audit.js next to this script")
        return 3
    browser = next((p for p in BROWSERS if os.path.exists(p)), None)
    if not browser:
        print("no chrome or edge found; pass the audit through a browser tool instead")
        return 3

    targets = []
    for a in argv:
        p = pathlib.Path(a)
        if p.is_dir():
            targets += sorted(p.glob("*.html"))
        elif p.exists():
            targets.append(p)
        else:
            print("not found:", a)
    js = AUDIT.read_text(encoding="utf-8")
    prof = pathlib.Path(tempfile.gettempdir()) / "zoom_audit_profile"
    stage = pathlib.Path(tempfile.gettempdir()) / "zoom_audit_pages"
    stage.mkdir(exist_ok=True)

    bad = 0
    for src in targets:
        page = src.read_text(encoding="utf-8").replace("</body>", RUNNER % js + "</body>")
        tmp = stage / src.name
        tmp.write_text(page, encoding="utf-8")
        cmd = [browser, "--headless=new", "--disable-gpu", "--hide-scrollbars", "--no-first-run",
               "--user-data-dir=" + str(prof), "--window-size=1300,3200",
               "--virtual-time-budget=9000", "--dump-dom", tmp.as_uri()]
        run = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8",
                             errors="replace", timeout=300)
        m = re.search(r'<pre id="TESTOUT">(.*?)</pre>', run.stdout or "", re.S)
        if not m:
            print("FAIL", src.name, "(no measurement; stderr: %s)" % (run.stderr or "")[:160].replace("\n", " "))
            bad += 1
            continue
        data = json.loads(unescape(m.group(1)).replace("MEASURE_JSON:", ""))
        v = data["violations"]
        n = len(v["offCanvas"]) + len(v["pastContentEdge"]) + len(v["textCollisions"])
        print("%s %-52s canvas=%-16s texts=%-4d links=%-3d chips=%-3d tight=%s" % (
            "OK  " if n == 0 else "FAIL", src.name, data["canvas"]["viewBox"],
            data["counts"]["texts"], data["counts"]["links"], data["counts"]["chips"],
            data["tightestRightMarginPx"]))
        for kind in ("offCanvas", "pastContentEdge", "textCollisions"):
            for item in v[kind]:
                print("       %s: %s" % (kind, item[:150]))
        bad += 1 if n else 0
    print("\nPAGES_BAD:", bad)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
