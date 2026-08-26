#!/usr/bin/env python3
"""Generate FF Sidekick icons (red rounded square + white uptrend line).

Mirrors the inline SVG logo in index.html so the extension, favicon and Web
Store listing all share one mark. Run: python3 scripts/make_icons.py
"""
import os

from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT_EXT = os.path.join(ROOT, "extension", "icons")
OUT_STORE = os.path.join(ROOT, "store")

RED = (204, 0, 0, 255)
WHITE = (255, 255, 255, 255)


def rounded(size, radius, fill):
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([0, 0, size - 1, size - 1], radius=radius, fill=fill)
    return img


def icon(size):
    # Supersample 4x for clean edges, then downscale.
    S = size * 4
    img = rounded(S, int(S * 0.22), RED)
    d = ImageDraw.Draw(img)
    # Uptrend polyline scaled from the 32px SVG: 8,22 -> 13,15 -> 17,18 -> 24,9
    pts = [(8, 22), (13, 15), (17, 18), (24, 9)]
    scaled = [(x / 32 * S, y / 32 * S) for x, y in pts]
    d.line(scaled, fill=WHITE, width=max(2, int(S * 0.085)), joint="curve")
    # Round the endpoints so the stroke reads like the SVG's linecap:round.
    r = S * 0.055
    for x, y in (scaled[0], scaled[-1]):
        d.ellipse([x - r, y - r, x + r, y + r], fill=WHITE)
    # The trailing dot at the top of the trend line.
    cx, cy = scaled[-1]
    rr = S * 0.085
    d.ellipse([cx - rr, cy - rr, cx + rr, cy + rr], fill=WHITE)
    return img.resize((size, size), Image.LANCZOS)


def main():
    os.makedirs(OUT_EXT, exist_ok=True)
    os.makedirs(OUT_STORE, exist_ok=True)
    for s in (16, 48, 128):
        icon(s).save(os.path.join(OUT_EXT, "icon%d.png" % s))
        print("wrote extension/icons/icon%d.png" % s)
    # A larger mark for the site favicon / store listing.
    icon(512).save(os.path.join(OUT_STORE, "icon512.png"))
    print("wrote store/icon512.png")


if __name__ == "__main__":
    main()
