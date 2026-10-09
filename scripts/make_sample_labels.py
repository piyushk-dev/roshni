"""Draws the two sample panel labels the website offers: a made-in-India DCR module and an imported one.

The brands are fictional and every label says SAMPLE. Run once: python scripts/make_sample_labels.py
"""
import random
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

WEB = Path(__file__).resolve().parents[1] / "web"
FONTS = Path("C:/Windows/Fonts")


def font(name, size):
    return ImageFont.truetype(str(FONTS / name), size)


def label(path, brand, model, pmax, serial, made_in, dcr, seed):
    W, H = 900, 640
    img = Image.new("RGB", (W, H), (226, 229, 233))  # the panel's grey backsheet behind the sticker
    d = ImageDraw.Draw(img)
    x0, y0, x1, y1 = 60, 40, W - 60, H - 40
    d.rounded_rectangle((x0, y0, x1, y1), radius=10, fill=(252, 252, 250), outline=(180, 184, 190), width=2)
    d.rectangle((x0, y0, x1, y0 + 64), fill=(24, 54, 102))
    d.text((x0 + 24, y0 + 14), brand, font=font("arialbd.ttf", 30), fill=(255, 255, 255))
    d.text((x1 - 24, y0 + 22), "PHOTOVOLTAIC MODULE", font=font("arialbd.ttf", 18), fill=(200, 214, 236), anchor="ra")
    d.text((x0 + 24, y0 + 84), f"Model: {model}", font=font("arialbd.ttf", 24), fill=(20, 20, 20))
    rows = [("Maximum power (Pmax)", f"{pmax} W"), ("Open-circuit voltage (Voc)", "49.6 V"), ("Short-circuit current (Isc)", "13.92 A"),
            ("Voltage at Pmax (Vmp)", "41.7 V"), ("Current at Pmax (Imp)", "13.07 A"), ("Maximum system voltage", "1500 V DC"),
            ("Module efficiency", "21.1 %")]
    y = y0 + 130
    for k, v in rows:
        d.text((x0 + 24, y), k, font=font("arial.ttf", 20), fill=(60, 60, 60))
        d.text((x0 + 470, y), v, font=font("arialbd.ttf", 20), fill=(20, 20, 20))
        d.line((x0 + 24, y + 30, x0 + 620, y + 30), fill=(222, 222, 222))
        y += 38
    d.text((x0 + 24, y + 6), "STC: 1000 W/m², AM 1.5, 25 °C   IEC 61215 / IEC 61730", font=font("arial.ttf", 16), fill=(90, 90, 90))
    d.text((x0 + 24, y + 34), f"Made in {made_in}", font=font("arialbd.ttf", 22), fill=(20, 20, 20))
    if dcr:
        d.rectangle((x0 + 24, y + 66, x0 + 420, y + 98), outline=(18, 105, 58), width=2)
        d.text((x0 + 36, y + 71), "DCR: Indian cells and module", font=font("arialbd.ttf", 18), fill=(18, 105, 58))
    # serial with a barcode
    bx, by = x0 + 650, y0 + 130
    rnd = random.Random(seed)
    xx = bx
    while xx < x1 - 30:
        w = rnd.choice((2, 2, 3, 4))
        d.rectangle((xx, by, xx + w - 1, by + 90), fill=(15, 15, 15))
        xx += w + rnd.choice((2, 3))
    d.text(((bx + x1 - 30) // 2, by + 100), serial, font=font("arialbd.ttf", 18), fill=(15, 15, 15), anchor="ma")
    d.text(((bx + x1 - 30) // 2, by + 126), "Serial No.", font=font("arial.ttf", 14), fill=(90, 90, 90), anchor="ma")
    # a light SAMPLE mark so nobody mistakes it for a real product
    mark = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    m = ImageDraw.Draw(mark)
    m.text((W - 90, H - 76), "SAMPLE", font=font("arialbd.ttf", 34), fill=(194, 65, 43, 170), anchor="ra")
    img = Image.alpha_composite(img.convert("RGBA"), mark).convert("RGB")
    img.save(path, optimize=True)
    print("wrote", path)


label(WEB / "sample-panel-ok.png", "Prakash PV Modules", "PPV-545M-DCR", 545, "PPV26A0912345", "India", True, 7)
label(WEB / "sample-panel-imported.png", "Hexa Solar Co.", "HX-550M", 550, "HX2604C77810", "China", False, 11)
