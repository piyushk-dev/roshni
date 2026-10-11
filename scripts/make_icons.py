"""Draws the home-screen icon: the site's pixel sun on the hero's sky. Run once: python scripts/make_icons.py

The link-preview image (web/og.png) is a capture of the hero, made with scripts/og_image.mjs.
"""
from pathlib import Path

from PIL import Image, ImageDraw

WEB = Path(__file__).resolve().parents[1] / "web"
SUN = [(5, 5, 6, 6), (7, 1, 2, 2), (7, 13, 2, 2), (1, 7, 2, 2), (13, 7, 2, 2),
       (3, 3, 1, 1), (12, 3, 1, 1), (3, 12, 1, 1), (12, 12, 1, 1)]  # x, y, w, h on a 16-pixel grid, as in the logo


def icon(size: int, path: Path, scale: float = 0.8) -> None:
    img = Image.new("RGB", (size, size), (142, 200, 242))
    d = ImageDraw.Draw(img)
    cell = size * scale / 16
    off = size * (1 - scale) / 2
    for x, y, w, h in SUN:
        d.rectangle((off + x * cell, off + y * cell, off + (x + w) * cell - 1, off + (y + h) * cell - 1), fill=(242, 165, 22))
    img.save(path, optimize=True)
    print("wrote", path)


icon(180, WEB / "icon-180.png")
icon(192, WEB / "app" / "icon-192.png")
icon(512, WEB / "app" / "icon-512.png")
icon(512, WEB / "app" / "icon-maskable.png", scale=0.56)  # inside the safe zone launchers crop to
