"""Monthly domestic electricity bill, from the regulator's published tariff."""

from __future__ import annotations

from dataclasses import dataclass

from . import load_data


@dataclass(frozen=True)
class Bill:
    units: float
    energy: float
    fixed: float
    ppac: float
    pension: float
    tax: float
    subsidy: float

    @property
    def gross(self) -> float:
        return self.energy + self.fixed + self.ppac + self.pension + self.tax

    @property
    def net(self) -> float:
        return self.gross - self.subsidy


@dataclass(frozen=True)
class Tariff:
    state: str
    discom: str
    discom_name: str
    ppac_pct: float
    slabs: tuple[tuple[float | None, float], ...]
    fixed_bands: tuple[tuple[float | None, float], ...]
    pension_pct: float
    tax_pct: float
    subsidy: dict | None
    export_rate: float
    default_lat: float
    default_lon: float

    @classmethod
    def for_discom(cls, discom: str) -> Tariff:
        for state, t in load_data("tariffs.json").items():
            if discom in t["discoms"]:
                d = t["discoms"][discom]
                return cls(
                    state=state,
                    discom=discom,
                    discom_name=d["name"],
                    ppac_pct=d["ppac_pct"],
                    slabs=tuple(map(tuple, t["energy_slabs"])),
                    fixed_bands=tuple(map(tuple, t["fixed_charge_bands"])),
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
        ppac = (energy + fixed) * self.ppac_pct / 100
        pension = (energy + fixed) * self.pension_pct / 100
        tax = (energy + fixed + ppac + pension) * self.tax_pct / 100
        gross = energy + fixed + ppac + pension + tax
        return Bill(units, energy, fixed, ppac, pension, tax, self._subsidy(units, gross))

    def _subsidy(self, units: float, gross: float) -> float:
        s = self.subsidy
        if not s:
            return 0.0
        if units <= s["free_upto_units"]:
            return gross
        if units <= s["half_upto_units"]:
            return min(gross * 0.5, s["half_cap_rs"])
        return 0.0
