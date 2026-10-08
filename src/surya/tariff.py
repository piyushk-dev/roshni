"""Monthly domestic electricity bill, from the regulator's published tariff."""

from __future__ import annotations

from dataclasses import dataclass

from . import load_data

# rough population centres, used for sunlight when a bill comes from a provider we have no data for
STATE_CENTRES = {
    "DL": (28.61, 77.21), "UP": (26.85, 80.95), "MH": (19.08, 72.88), "KA": (12.97, 77.59), "TN": (13.08, 80.27),
    "GJ": (23.02, 72.57), "RJ": (26.91, 75.79), "HR": (28.46, 77.03), "PB": (30.90, 75.85), "WB": (22.57, 88.36),
    "TS": (17.39, 78.49), "AP": (16.51, 80.65), "KL": (9.93, 76.27), "MP": (23.26, 77.41), "BR": (25.59, 85.14),
    "OD": (20.30, 85.82), "JH": (23.34, 85.31), "CG": (21.25, 81.63), "UK": (30.32, 78.03), "HP": (31.10, 77.17),
    "JK": (32.73, 74.86), "AS": (26.14, 91.74), "GA": (15.49, 73.83), "CH": (30.73, 76.78),
}
LEARNED_MULTIPLIER = 1.15  # surcharges and taxes on top of energy + fixed charges, when a bill doesn't say


@dataclass(frozen=True)
class Bill:
    units: float
    energy: float
    fixed: float
    fppas: float
    surcharge: float
    pension: float
    tax: float
    subsidy: float

    @property
    def gross(self) -> float:
        return self.energy + self.fixed + self.fppas + self.surcharge + self.pension + self.tax

    @property
    def net(self) -> float:
        return self.gross - self.subsidy


@dataclass(frozen=True)
class Tariff:
    state: str
    discom: str
    discom_name: str
    fppas_pct: float
    slabs: tuple[tuple[float | None, float], ...]
    fixed_bands: tuple[tuple[float | None, float], ...]
    surcharge_pct: float
    pension_pct: float
    tax_pct: float
    subsidy: dict | None
    export_rate: float
    default_lat: float
    default_lon: float
    learned: bool = False  # built from a bill's own rates rather than a regulator's order

    @classmethod
    def from_spec(cls, spec: dict) -> Tariff:
        """A tariff learned from a bill: its slab rates, its fixed charge, a typical surcharge."""
        state = (spec.get("state") or "IN").upper()
        lat, lon = STATE_CENTRES.get(state, (22.0, 79.0))
        return cls(
            state=state, discom=spec.get("provider", "unknown"), discom_name=spec.get("provider") or "your provider",
            fppas_pct=0.0, slabs=tuple(tuple(x) for x in spec["slabs"]),
            fixed_bands=((None, spec.get("fixed_per_kw") or 0.0),),
            surcharge_pct=((spec.get("multiplier") or LEARNED_MULTIPLIER) - 1) * 100, pension_pct=0.0, tax_pct=0.0,
            subsidy=None, export_rate=3.0, default_lat=lat, default_lon=lon, learned=True,
        )

    @classmethod
    def for_discom(cls, discom: str) -> Tariff:
        for state, t in load_data("tariffs.json").items():
            if discom in t["discoms"]:
                d = t["discoms"][discom]
                return cls(
                    state=state,
                    discom=discom,
                    discom_name=d["name"],
                    fppas_pct=d["fppas_pct"],
                    slabs=tuple(map(tuple, t["energy_slabs"])),
                    fixed_bands=tuple(map(tuple, t["fixed_charge_bands"])),
                    surcharge_pct=t["regulatory_surcharge_pct"],
                    pension_pct=t["pension_surcharge_pct"],
                    tax_pct=t["electricity_tax_pct"],
                    subsidy=t.get("subsidy"),
                    export_rate=t["export_rate_rs_per_kwh"],
                    default_lat=t["default_location"]["lat"],
                    default_lon=t["default_location"]["lon"],
                )
        raise KeyError(f"no tariff for electricity provider {discom!r}")

    def energy_charge(self, units: float) -> float:
        charge, floor = 0.0, 0.0
        for ceiling, rate in self.slabs:
            top = units if ceiling is None else min(units, ceiling)
            if top > floor:
                charge += (top - floor) * rate
            if ceiling is None or units <= ceiling:
                break
            floor = ceiling
        return charge

    def fixed_charge(self, load_kw: float) -> float:
        for ceiling, rate in self.fixed_bands:
            if ceiling is None or load_kw <= ceiling:
                return rate * load_kw
        return 0.0

    def bill(self, units: float, load_kw: float) -> Bill:
        energy = self.energy_charge(units)
        fixed = self.fixed_charge(load_kw)
        return self.bill_from_charges(units, energy, fixed)

    def bill_from_charges(self, units: float, energy: float, fixed: float) -> Bill:
        """The rest of the bill, built the way a Delhi bill prints it, from its energy and fixed charges."""
        fppas = energy * self.fppas_pct / 100
        surcharge = (energy + fixed) * self.surcharge_pct / 100
        pension = (energy + fixed) * self.pension_pct / 100
        tax = (energy + fppas + surcharge) * self.tax_pct / 100
        gross = energy + fixed + fppas + surcharge + pension + tax
        return Bill(units, energy, fixed, fppas, surcharge, pension, tax, self._subsidy(units, gross))

    def _subsidy(self, units: float, gross: float) -> float:
        s = self.subsidy
        if not s:
            return 0.0
        if units <= s["free_upto_units"]:
            return gross
        if units <= s["half_upto_units"]:
            return min(gross * 0.5, s["half_cap_rs"])
        return 0.0
