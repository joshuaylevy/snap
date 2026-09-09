#!/usr/bin/env python3
"""2612_assemble_artifact.py — inline everything into the one-file waiver-map page.

Substitutes the fixed markers in 2612a with: the embedded fonts (2612e, vendored
OFL-licensed latin WOFF2 subsets, base64 data URIs), the stylesheet (2612c), the viz
payload (610, minified), the us-atlas topology (minified), the vendored
topojson-client, and the app (2612b). Output is a single self-contained HTML file
that opens from file:// and publishes as a Claude Artifact (strict CSP: the
assembled page must reference nothing over the network — asserted below). JSON is
embedded in <script type="application/json"> blocks with '</' escaped to '<\\/' so
document text can never terminate the block early.

Usage (from project root, snap env):
    python 2_scripts/26_present/261_waiver_map/2612_assemble_artifact.py
"""
from __future__ import annotations

import base64
import json
import pathlib
import re
import sys

# --- explicit path globals, composed from the project root ---
VIZ_SCRIPTS = pathlib.Path("2_scripts") / "26_present" / "261_waiver_map"
TEMPLATE = VIZ_SCRIPTS / "2612a_waiver_map_template.html"
APP_JS = VIZ_SCRIPTS / "2612b_waiver_map_app.js"
STYLES = VIZ_SCRIPTS / "2612c_waiver_map_styles.css"
RULES_TAB = VIZ_SCRIPTS / "2612f_rules_tab.html"
PACK_TAB = VIZ_SCRIPTS / "2612g_pack_tab.html"
PACK_JS = VIZ_SCRIPTS / "2612h_pack_demo_app.js"
TOPO_LIB = VIZ_SCRIPTS / "2612d_topojson-client.v3.1.0.min.js"
FONTS_DIR = VIZ_SCRIPTS / "2612e_fonts"

# (filename, family, style, weight) — the serif file is a variable font, hence
# the weight range; all files are Google-served latin subsets (SIL OFL 1.1)
FONTS = [
    ("SourceSerif4-latin.woff2", "Source Serif 4", "normal", "400 700"),
    ("SourceSerif4-Italic-latin.woff2", "Source Serif 4", "italic", "400"),
    ("IBMPlexMono-400-latin.woff2", "IBM Plex Mono", "normal", "400"),
    ("IBMPlexMono-500-latin.woff2", "IBM Plex Mono", "normal", "500"),
]

DATA_DIR = pathlib.Path("1_data")
US_ATLAS_JSON = DATA_DIR / "10_raw" / "103_geo" / "1031_us_atlas" / "counties-10m.json"

OUT_DIR = pathlib.Path("6_present") / "61_waiver_map"
VIZ_DATA = OUT_DIR / "610_waiver_map_data.json"
OUT_HTML = OUT_DIR / "611_waiver_map.html"

# The artifact hard cap is 16MB. The budget is a tripwire against accidental bloat,
# not a target. The payload + national topology are ~97% of the page (10.9MB + 0.8MB
# at 36 states / 694 documents); the rules and set-packing tabs add only ~0.1MB of
# text/JS. Raised 10MB -> 13MB on 2026-09-09 when NJ/VA/AZ/MA landed and the corpus
# grew to 694 documents; the page is 11.7MB, so the remaining headroom is ~4MB against
# the hard cap and the payload is growing ~0.017MB per document. The last 14 states
# will not fit: before they land, the lever named here has to be pulled — subset the
# topology to the states actually in the payload (the national mesh is the largest
# fixed cost and most of it is never drawn), then compress the per-unit records.
SOFT_BUDGET_BYTES = 13 * 1024 * 1024

# marker -> how its replacement is produced
MARKERS = ["/*__FONTS__*/", "/*__CSS__*/", "__DATA__", "__TOPOLOGY__",
           "/*__TOPOJSON_LIB__*/", "/*__APP__*/",
           "<!--__RULES_TAB__-->", "<!--__PACK_TAB__-->", "/*__PACK_APP__*/"]

# anything that would make the page reach for the network (the topojson-client
# banner comment contains a plain https URL; comments don't fetch, so the check
# targets fetching CONSTRUCTS, not URL strings)
_NETWORK_RE = re.compile(
    r"""<link\b | @import\b | url\(\s*['"]?https?: | \bfetch\s*\( |
        XMLHttpRequest | \bimport\s*\( | src\s*=\s*['"]https?:""",
    re.VERBOSE,
)


def fonts_css() -> str:
    rules = []
    for fname, family, style, weight in FONTS:
        b64 = base64.b64encode((FONTS_DIR / fname).read_bytes()).decode("ascii")
        rules.append(
            f'@font-face{{font-family:"{family}";font-style:{style};'
            f"font-weight:{weight};font-display:swap;"
            f'src:url(data:font/woff2;base64,{b64}) format("woff2")}}'
        )
    return "\n".join(rules)


def inline_json(path: pathlib.Path) -> str:
    obj = json.loads(path.read_text(encoding="utf-8"))
    s = json.dumps(obj, separators=(",", ":"), ensure_ascii=False)
    return s.replace("</", "<\\/")


def main():
    template = TEMPLATE.read_text(encoding="utf-8")
    for m in MARKERS:
        if template.count(m) != 1:
            sys.exit(f"[assemble] template must contain {m!r} exactly once")

    app = APP_JS.read_text(encoding="utf-8")
    css = STYLES.read_text(encoding="utf-8")
    lib = TOPO_LIB.read_text(encoding="utf-8")
    rules_tab = RULES_TAB.read_text(encoding="utf-8")
    pack_tab = PACK_TAB.read_text(encoding="utf-8")
    pack_js = PACK_JS.read_text(encoding="utf-8")
    for name, src in [("app", app), ("styles", css), ("lib", lib), ("pack app", pack_js)]:
        if "</script" in src.lower():
            sys.exit(f"[assemble] {name} contains a literal </script> — would truncate")

    html = (template
            .replace("/*__FONTS__*/", fonts_css())
            .replace("/*__CSS__*/", css)
            .replace("__DATA__", inline_json(VIZ_DATA))
            .replace("__TOPOLOGY__", inline_json(US_ATLAS_JSON))
            .replace("/*__TOPOJSON_LIB__*/", lib)
            .replace("/*__APP__*/", app)
            .replace("<!--__RULES_TAB__-->", rules_tab)
            .replace("<!--__PACK_TAB__-->", pack_tab)
            .replace("/*__PACK_APP__*/", pack_js))

    for m in MARKERS:
        if m in html:
            sys.exit(f"[assemble] marker {m!r} survived substitution")

    for name, src in [("template", template), ("styles", css), ("app", app),
                      ("rules tab", rules_tab), ("pack tab", pack_tab), ("pack app", pack_js)]:
        hit = _NETWORK_RE.search(src)
        if hit:
            sys.exit(f"[assemble] {name} reaches for the network: {hit.group(0)!r}")

    n = len(html.encode("utf-8"))
    if n > SOFT_BUDGET_BYTES:
        sys.exit(f"[assemble] {n:,} bytes exceeds the {SOFT_BUDGET_BYTES:,} soft budget")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_HTML.write_text(html, encoding="utf-8")
    print(f"[assemble] wrote {OUT_HTML} ({n:,} bytes)")


if __name__ == "__main__":
    main()
