"""Run the calculator from the terminal against live sunlight data.

    python scripts/try_it.py --discom BRPL --load 5 --units 380,350,420,560,720,780,690,610,560,470,390,400
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
sys.stdout.reconfigure(encoding="utf-8")

from surya.calculator import Household, analyze  # noqa: E402
from surya.format import inr, message  # noqa: E402
from surya.solar import fetch_sources, solar_yield  # noqa: E402
from surya.tariff import Tariff  # noqa: E402

p = argparse.ArgumentParser()
p.add_argument("--discom", default="BRPL")
p.add_argument("--load", type=float, default=3, help="sanctioned load in kW")
p.add_argument("--units", required=True, help="units per month, Jan..Dec, comma-separated (blank = unknown)")
p.add_argument("--roof", type=float, help="shade-free roof area in sq ft")
p.add_argument("--lat", type=float)
p.add_argument("--lon", type=float)
p.add_argument("--lang", default="en")
args = p.parse_args()

tariff = Tariff.for_discom(args.discom)
units = {m: float(u) for m, u in enumerate(args.units.split(","), start=1) if u.strip()}
sy = solar_yield(fetch_sources(args.lat or tariff.default_lat, args.lon or tariff.default_lon))
a = analyze(Household(args.discom, args.load, units, roof_sqft=args.roof), sy, tariff)

print(f"Yield: {sy.annual:.0f} units/kW/yr (PVGIS alone: {sy.annual_optimistic:.0f})")
for o in a.options:
    payback = f"{o.payback_years:.1f}y" if o.payback_years else "never"
    print(f"  {o.kw:g} kW  net {inr(o.net_cost):>10}  saves {inr(o.savings_rs):>9}/yr  payback {payback:>6}  NPV {inr(o.npv_rs):>10}")
print()
print(message(a, args.lang))
