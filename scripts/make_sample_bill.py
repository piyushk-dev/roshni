"""Draws web/sample-bill.png: a fictional household's Delhi electricity bill, for "See an example".

The charges follow the app's own BRPL tariff (src/surya/data/tariffs.json), so the reader and the sums agree.

    python scripts/make_sample_bill.py
"""

import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from surya.tariff import Tariff  # noqa: E402

OUT = Path(__file__).resolve().parents[1] / "web" / "sample-bill.png"


def font(name: str, size: int):
    try:
        return ImageFont.truetype(name, size)
    except OSError:
        return ImageFont.load_default()


regular, bold, big, small = font("arial.ttf", 21), font("arialbd.ttf", 21), font("arialbd.ttf", 30), font("arial.ttf", 17)
INK, MUTED, LINE, BLUE = "#0f172a", "#475569", "#cbd5e1", "#1f4e8c"
img = Image.new("RGB", (1000, 1490), "white")
d = ImageDraw.Draw(img)


def money(x: float) -> str:
    whole, frac = f"{x:.2f}".split(".")
    head, tail = whole[:-3], whole[-3:]
    groups = []
    while len(head) > 2:
        groups.insert(0, head[-2:])
        head = head[:-2]
    return ",".join(([head] if head else []) + groups + [tail]) + "." + frac


d.rectangle([0, 0, 1000, 56], fill="#b91c1c")
d.text((24, 15), "SAMPLE BILL FOR DEMONSTRATION - FICTIONAL CONSUMER, NOT A REAL BILL", fill="white", font=bold)
d.rectangle([0, 56, 1000, 132], fill=BLUE)
d.text((40, 70), "ELECTRICITY BILL", fill="white", font=big)
d.text((40, 106), "BSES Rajdhani Power Limited (BRPL), New Delhi", fill="#dbe7f7", font=regular)
d.text((700, 76), "Bill date: 14-09-2026", fill="white", font=bold)
d.text((700, 104), "Due date: 28-09-2026", fill="#dbe7f7", font=regular)

y = 156
for label, value in (("Consumer", "Sample Household (fictional)"), ("Address", "Malviya Nagar, New Delhi 110017"),
                     ("Tariff category", "Domestic"), ("Sanctioned Load", "5.000 kW"), ("Maximum demand (MDI)", "3.20 kW"),
                     ("Reading type", "Actual")):
    d.text((40, y), label, fill=MUTED, font=regular)
    d.text((330, y), value, fill=INK, font=bold if label == "Sanctioned Load" else regular)
    y += 32

y += 10
d.rectangle([40, y, 960, y + 64], fill="#eef4fb", outline="#bcd0ea")
d.text((56, y + 10), "Billing period: 12-08-2026 to 11-09-2026 (31 days)", fill=INK, font=regular)
d.text((56, y + 36), "Units consumed: 642 kWh", fill=INK, font=bold)
y += 92

# the slab-wise energy charge
d.text((40, y), "Slab-wise energy charge", fill=INK, font=bold)
y += 34
cols = (56, 330, 540, 780)
d.rectangle([40, y, 960, y + 34], fill="#e2e8f0")
for x, h in zip(cols, ("Slab (units)", "Units", "Rate (Rs/unit)", "Amount (Rs)")):
    d.text((x, y + 7), h, fill=INK, font=bold)
y += 34
slabs = (("0 - 200", 200, 3.00), ("201 - 400", 200, 4.50), ("401 - 800", 242, 6.50))
energy = 0.0
for name, units, rate in slabs:
    energy += units * rate
    for x, v in zip(cols, (name, str(units), f"{rate:.2f}", money(units * rate))):
        d.text((x, y + 8), v, fill=INK, font=regular)
    y += 36
    d.line([40, y, 960, y], fill=LINE)
d.text((56, y + 8), "Energy charge", fill=INK, font=bold)
d.text((780, y + 8), money(energy), fill=INK, font=bold)
y += 56

# the rest of the bill, the way a Delhi bill prints it
bill = Tariff.for_discom("BRPL").bill(642, 5)
assert abs(bill.energy - energy) < 0.01, (bill.energy, energy)
fixed, fppas, surcharge, pension, tax = bill.fixed, bill.fppas, bill.surcharge, bill.pension, bill.tax
total = energy + fixed + fppas + surcharge + pension + tax
d.text((40, y), "Current charges", fill=INK, font=bold)
y += 34
for label, value in (("Fixed charge (5 kW x Rs 50)", fixed), ("Energy charge", energy), ("PPAC / FPPAS (17.94%)", fppas),
                     ("Regulatory surcharge (8%)", surcharge), ("Pension trust surcharge (7%)", pension), ("Electricity tax (5%)", tax)):
    d.text((56, y), label, fill=INK, font=regular)
    d.text((780, y), money(value), fill=INK, font=regular)
    y += 31
d.line([40, y + 4, 960, y + 4], fill=INK, width=2)
d.text((56, y + 14), "Total current charges", fill=INK, font=bold)
d.text((780, y + 14), money(total), fill=INK, font=bold)
y += 52
d.rectangle([600, y, 960, y + 66], fill="#fff4d6", outline="#e2b54a", width=2)
d.text((620, y + 8), "AMOUNT PAYABLE", fill="#7a5a10", font=small)
d.text((620, y + 30), f"Rs {round(total):,}", fill=INK, font=big)
y += 92

# twelve months of history, newest first, the current period not repeated
d.text((40, y), "Consumption history", fill=INK, font=bold)
y += 34
hist = [("12-07-2026", "11-08-2026", 31, 698), ("12-06-2026", "11-07-2026", 30, 781), ("12-05-2026", "11-06-2026", 31, 744),
        ("12-04-2026", "11-05-2026", 30, 612), ("12-03-2026", "11-04-2026", 31, 455), ("12-02-2026", "11-03-2026", 28, 362),
        ("12-01-2026", "11-02-2026", 31, 341), ("12-12-2025", "11-01-2026", 31, 389), ("12-11-2025", "11-12-2025", 30, 376),
        ("12-10-2025", "11-11-2025", 31, 448), ("12-09-2025", "11-10-2025", 30, 590)]
hcols = (56, 250, 450, 560)
d.rectangle([40, y, 700, y + 32], fill="#e2e8f0")
for x, h in zip(hcols, ("From", "To", "Days", "Units (kWh)")):
    d.text((x, y + 6), h, fill=INK, font=bold)
y += 32
top = y
for a, b, days, units in hist:
    for x, v in zip(hcols, (a, b, str(days), str(units))):
        d.text((x, y + 5), v, fill=INK, font=small)
    y += 27
# a small bar chart beside the table, as many bills print one
d.text((740, top - 30), "Units by month", fill=MUTED, font=small)
bars = [u for *_, u in reversed(hist)] + [642]
for i, u in enumerate(bars):
    h = u / 800 * 230
    x = 740 + i * 18
    d.rectangle([x, top + 260 - h, x + 12, top + 260], fill=BLUE if i == len(bars) - 1 else "#8fb0d9")

d.text((40, 1452), "Generated for Roshni's demo. No real person, meter or account.", fill=MUTED, font=small)
img.save(OUT, optimize=True)
print(OUT, round(total, 2))
