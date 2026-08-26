#!/usr/bin/env python3
"""
Build a single self-contained ff-sidekick-standalone.html.

The output is ONE file with no external dependencies: the player data, every
headshot / team logo, and the Inter font are all embedded.

It stays online-first at runtime. When the machine has a network connection the
page behaves exactly like index.html -- it fetches data.json, pulls headshots
from a.espncdn.com and Inter from Google Fonts. The embedded copies are only
used when one of those requests actually fails, so an offline (or Google-Fonts-
is-down, or ESPN-is-down) load still renders identically.

Usage:
    python3 build_standalone.py                 # build from ./index.html + ./data.json
    python3 build_standalone.py --no-images     # skip image embedding (small file, needs net for photos)

Downloaded assets are cached in .asset_cache/ so re-runs after a data refresh
are fast. Delete that folder to force a re-download.
"""

import argparse
import base64
import concurrent.futures
import io
import json
import os
import re
import sys
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
SRC_HTML = os.path.join(HERE, "index.html")
SRC_DATA = os.path.join(HERE, "data.json")
OUT_HTML = os.path.join(HERE, "ff-sidekick-standalone.html")
CACHE = os.path.join(HERE, ".asset_cache")

UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/126.0 Safari/537.36"

HEADSHOT = "https://a.espncdn.com/i/headshots/nfl/players/full/{id}.png"
TEAMLOGO = "https://a.espncdn.com/i/teamlogos/nfl/500/{team}.png"
# Inter, latin subset, static weights matching the <link> in index.html.
FONT_CSS = ("https://fonts.googleapis.com/css2"
            "?family=Inter:wght@400;500;600;700;800&display=swap")

# Rendered sizes: .hs is 40x29, .chip img 22x22, .cmp-player img 64x47.
# 128px wide covers the largest at 2x on a retina display.
HEADSHOT_W = 128
LOGO_W = 96


def fetch(url, headers=None):
    req = urllib.request.Request(url, headers={"User-Agent": UA, **(headers or {})})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read()


def cached(name, url):
    """Download url once, keep the raw bytes in .asset_cache/."""
    os.makedirs(CACHE, exist_ok=True)
    path = os.path.join(CACHE, name)
    if os.path.exists(path) and os.path.getsize(path) > 0:
        with open(path, "rb") as f:
            return f.read()
    try:
        blob = fetch(url)
    except Exception as e:
        print("  ! {}: {}".format(name, e), file=sys.stderr)
        return None
    with open(path, "wb") as f:
        f.write(blob)
    return blob


def to_webp(blob, width, quality=82):
    """Downscale and re-encode as WebP, which is 5-10x smaller than the source PNG."""
    from PIL import Image
    im = Image.open(io.BytesIO(blob))
    im = im.convert("RGBA")
    if im.width > width:
        h = max(1, round(im.height * width / im.width))
        im = im.resize((width, h), Image.LANCZOS)
    buf = io.BytesIO()
    im.save(buf, "WEBP", quality=quality, method=6)
    return buf.getvalue()


def data_uri(blob, mime):
    return "data:{};base64,{}".format(mime, base64.b64encode(blob).decode("ascii"))


def build_image_maps(players):
    """-> ({player_id: dataURI}, {team_abbrev: dataURI})"""
    ids = sorted({str(p["id"]) for p in players if p.get("pos") != "D/ST" and p.get("id")})
    teams = sorted({(p.get("team") or "").lower() for p in players if p.get("team")})
    teams = [t for t in teams if t and t != "fa"]

    print("Downloading {} headshots and {} team logos...".format(len(ids), len(teams)))
    jobs = ([("hs", i, HEADSHOT.format(id=i)) for i in ids] +
            [("tl", t, TEAMLOGO.format(team=t)) for t in teams])

    raw = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=16) as ex:
        futs = {ex.submit(cached, "{}-{}.png".format(kind, key), url): (kind, key)
                for kind, key, url in jobs}
        done = 0
        for fut in concurrent.futures.as_completed(futs):
            kind, key = futs[fut]
            blob = fut.result()
            if blob:
                raw[(kind, key)] = blob
            done += 1
            if done % 50 == 0:
                print("  {}/{}".format(done, len(jobs)))

    print("Re-encoding to WebP...")
    imgs, logos = {}, {}
    for (kind, key), blob in raw.items():
        # Cache the encoded result too -- WebP method=6 is slow, and without this
        # every rebuild would re-encode all 310 images from scratch.
        enc_path = os.path.join(CACHE, "{}-{}.webp".format(kind, key))
        if os.path.exists(enc_path):
            with open(enc_path, "rb") as f:
                small = f.read()
        else:
            try:
                small = to_webp(blob, HEADSHOT_W if kind == "hs" else LOGO_W)
            except Exception as e:
                print("  ! encode {}-{}: {}".format(kind, key, e), file=sys.stderr)
                continue
            with open(enc_path, "wb") as f:
                f.write(small)
        (imgs if kind == "hs" else logos)[key] = data_uri(small, "image/webp")
    return imgs, logos


def build_font_css():
    """Fetch the Google Fonts CSS and inline every woff2 it points at as a data URI."""
    print("Embedding Inter font...")
    try:
        css = cached("inter.css", FONT_CSS).decode("utf-8")
    except Exception as e:
        print("  ! font css: {}".format(e), file=sys.stderr)
        return ""
    # Keep only the latin subset -- latin-ext/cyrillic/greek would triple the size.
    blocks = re.findall(r"/\*\s*([\w-]+)\s*\*/\s*(@font-face\s*\{[^}]*\})", css)
    keep = [b for name, b in blocks if name == "latin"] or [b for _, b in blocks]
    out = []
    for block in keep:
        m = re.search(r"url\((https://[^)]+\.woff2)\)", block)
        if not m:
            continue
        url = m.group(1)
        blob = cached("font-" + url.rsplit("/", 1)[-1], url)
        if not blob:
            continue
        block = block.replace(url, data_uri(blob, "font/woff2"))
        # Rename the family so the live Google Fonts copy still wins when online.
        block = re.sub(r"font-family:\s*'Inter'", "font-family:'InterOffline'", block)
        out.append(block)
    print("  {} faces embedded".format(len(out)))
    return "\n".join(out)


def js_json(obj):
    """JSON safe to drop inside a <script> block."""
    return (json.dumps(obj, separators=(",", ":"))
            .replace("<", "\\u003c").replace(">", "\\u003e")
            .replace("\u2028", "\\u2028").replace("\u2029", "\\u2029"))


# The runtime shim. Everything here is a *fallback* -- it only does anything
# once a live request has already failed.
RUNTIME = """
<script>
/* ---- offline fallbacks (only fire when a live request fails) ---- */
(function(){
  var IMG = window.__FF_IMG__ || {}, LOGO = window.__FF_LOGO__ || {};
  function swap(el){
    var s = el.getAttribute('src') || '', m;
    if ((m = s.match(/players\\/full\\/(\\d+)\\.png/)) && IMG[m[1]]) { el.src = IMG[m[1]]; return true; }
    if ((m = s.match(/teamlogos\\/nfl\\/500\\/([a-z]+)\\.png/i)) && LOGO[m[1].toLowerCase()]) { el.src = LOGO[m[1].toLowerCase()]; return true; }
    return false;
  }
  /* Capture phase on document, so this runs before the inline onerror="" that
     would otherwise hide the image. stopPropagation keeps that handler from
     firing when we have a replacement. */
  document.addEventListener('error', function(e){
    var el = e.target;
    if (!el || el.tagName !== 'IMG' || el.dataset.ffTried) return;
    el.dataset.ffTried = '1';
    if (swap(el)) { e.stopPropagation(); e.preventDefault(); }
  }, true);
})();
</script>
"""

LOADER = """
/* Online: read the live data.json exactly as before.
   Offline (or opened as a file:// double-click, where fetch is blocked):
   fall back to the snapshot embedded in this file. */
(function(){
  function embedded(){
    var el = document.getElementById('ff-embedded-data');
    return el ? JSON.parse(el.textContent) : null;
  }
  function fail(){
    document.getElementById('tbody').innerHTML =
      '<tr><td colspan="12"><div class="empty"><b>Couldn\\'t load player data</b>Refresh to try again.</div></td></tr>';
  }
  var live;
  try { live = fetch('data.json').then(function(r){
    if (!r.ok) throw new Error('HTTP ' + r.status);
    return r.json();
  }); } catch (e) { live = Promise.reject(e); }
  live.then(init).catch(function(){
    var d = embedded();
    if (d) { init(d); } else { fail(); }
  });
})();
"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-images", action="store_true",
                    help="skip embedding headshots/logos (smaller file, photos need network)")
    ap.add_argument("--no-font", action="store_true", help="skip embedding the Inter font")
    args = ap.parse_args()

    with open(SRC_HTML, encoding="utf-8") as f:
        html = f.read()
    with open(SRC_DATA, encoding="utf-8") as f:
        data = json.load(f)

    players = data.get("players", [])
    print("Source: {} players, generated {}".format(len(players), data.get("generated")))

    imgs, logos = ({}, {}) if args.no_images else build_image_maps(players)
    font_css = "" if args.no_font else build_font_css()

    # 1. Embedded font faces + a fallback family in the body stack.
    if font_css:
        html = html.replace("</style>", font_css + "\n</style>", 1)
        html = html.replace("font-family:'Inter',-apple-system",
                            "font-family:'Inter','InterOffline',-apple-system", 1)

    # 2. Embedded data snapshot + image maps, injected right before the app script.
    payload = (
        '<script id="ff-embedded-data" type="application/json">'
        + js_json(data) + "</script>\n"
        + "<script>window.__FF_IMG__=" + js_json(imgs)
        + ";window.__FF_LOGO__=" + js_json(logos) + ";</script>\n"
        + RUNTIME
    )
    marker = "<script>\n"
    idx = html.rindex(marker)
    html = html[:idx] + payload + html[idx:]

    # 3. Swap the bare fetch() for the online-first loader.
    old = re.search(r"fetch\('data\.json'\)\.then\(r=>r\.json\(\)\)\.then\(init\)"
                    r"\.catch\(\(\)=>\{.*?\}\);", html, re.S)
    if not old:
        sys.exit("ERROR: could not find the data.json fetch call in index.html -- "
                 "it may have been rewritten. Update build_standalone.py.")
    html = html[:old.start()] + LOADER.strip() + html[old.end():]

    # 4. Note the provenance in the <title> region so a stray copy is identifiable.
    html = html.replace("<title>FF Sidekick</title>",
                        "<title>FF Sidekick</title>\n"
                        "<!-- Standalone build. Data snapshot: {} -->".format(
                            data.get("generated", "unknown")), 1)

    with open(OUT_HTML, "w", encoding="utf-8") as f:
        f.write(html)

    mb = os.path.getsize(OUT_HTML) / 1e6
    print("\nWrote {} ({:.1f} MB)".format(os.path.basename(OUT_HTML), mb))
    print("  {} headshots, {} logos, font: {}".format(
        len(imgs), len(logos), "embedded" if font_css else "no"))
    print("  Open it by double-clicking. No server, no network required.")


if __name__ == "__main__":
    main()
