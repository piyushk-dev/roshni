"""Turns one household's bill history into a sized, priced, honest solar recommendation."""

from __future__ import annotations

import math
from dataclasses import asdict, dataclass, field

from .scheme import SCHEME, central_subsidy, emi, loan_for, system_cost
from .solar import SolarYield
from .tariff import Tariff

ECON = SCHEME["economics"]
EMISSION_T_PER_MWH = SCHEME["grid_emission_t_per_mwh"]
FY_ORDER = (4, 5, 6, 7, 8, 9, 10, 11, 12, 1, 2, 3)  # surplus units are banked across one financial year
MIN_YEARLY_SAVING_RS = 3000
EXPORT_HEAVY_SHARE = 0.10


@dataclass
class Household:
    discom: str
    sanctioned_kw: float
    monthly_units: dict[int, float]  # calendar month (1-12) -> units, from the bill's usage history
    roof_sqft: float | None = None
    last_bill_rs: float | None = None
    last_bill_units: float | None = None
    last_bill_energy_rs: float | None = None  # the bill's printed energy charge: more reliable than its total


@dataclass
class Option:
    kw: float
    gross_cost: float
    subsidy: float
    net_cost: float
    generation_kwh: float
    export_kwh: float
    savings_rs: float
    savings_optimistic_rs: float
    payback_years: float | None
    savings_25y_rs: float
    npv_rs: float
    loan_rate_pct: float
    emi_rs: float
    emi_after_subsidy_rs: float
    co2_t_per_year: float
    roof_sqft_needed: float
    needs_load_increase: bool


@dataclass
class Analysis:
    verdict: str  # "go" or "skip"
    reason: str  # a key into format.REASONS
    recommended: Option | None
    options: list[Option]
    discom_name: str
    sanctioned_kw: float
    roof_sqft: float | None
    bill_now_rs_per_year: float
    usage_units_per_year: float
    yield_kwh_per_kw: float
    yield_optimistic_kwh_per_kw: float
    calibration: float
    estimated_months: list[int]
    usage_by_month: list[float]  # Jan..Dec, with estimated months filled in
    yield_by_month: list[float]  # Jan..Dec units per kW, conservative
    free_units: float
    export_rate: float
    notes: list[str] = field(default_factory=list)  # keys into format.NOTES

    def to_dict(self) -> dict:
        return asdict(self)


def fill_months(monthly_units: dict) -> tuple[list[float], list[int]]:
    known = {int(m): float(u) for m, u in monthly_units.items() if u is not None}
    if not known:
        raise ValueError("need at least one month of electricity usage")
    if any(not 1 <= m <= 12 for m in known):
        raise ValueError("months must be numbered 1-12")
    mean = sum(known.values()) / len(known)
    return [known.get(m, mean) for m in range(1, 13)], [m for m in range(1, 13) if m not in known]


def calibration_factor(h: Household, tariff: Tariff) -> float:
    """Scale the modelled bill to the household's real one, so tariff changes we haven't caught are counted."""
    if not h.last_bill_units:
        return 1.0
    if h.last_bill_energy_rs:
        actual, modelled = h.last_bill_energy_rs, tariff.energy_charge(h.last_bill_units)
    elif h.last_bill_rs:
        actual, modelled = h.last_bill_rs, tariff.bill(h.last_bill_units, h.sanctioned_kw).net
    else:
        return 1.0
    return min(max(actual / modelled, 0.7), 1.4) if modelled > 0 else 1.0


def year_with_solar(units: list[float], generation: list[float], tariff: Tariff, load_kw: float) -> tuple[float, float]:
    """A year of net-metered bills, and the units still banked at year end."""
    bank, total = 0.0, 0.0
    for m in FY_ORDER:
        net = units[m - 1] - generation[m - 1]
        if net < 0:
            bank -= net
            billed = 0.0
        else:
            used = min(bank, net)
            bank -= used
            billed = net - used
        total += tariff.bill(billed, load_kw).net
    return total, bank


def _year(kw, year, units, monthly_yield, tariff, load_kw, bill_now, calib) -> tuple[float, float, float]:
    fade = (1 - ECON["degradation_pct_per_year"] / 100) ** (year - 1)
    generation = [y * kw * fade for y in monthly_yield]
    with_solar, banked = year_with_solar(units, generation, tariff, load_kw)
    saving = (bill_now - with_solar) * calib + banked * tariff.export_rate
    return saving, sum(generation), banked


def evaluate(kw: float, h: Household, units: list[float], sy: SolarYield, tariff: Tariff, bill_now: float, calib: float) -> Option:
    gross = system_cost(kw)
    subsidy = central_subsidy(kw, tariff.state)
    net_cost = gross - subsidy

    flows = []
    for year in range(1, ECON["lifetime_years"] + 1):
        saving, generation, banked = _year(kw, year, units, sy.monthly, tariff, h.sanctioned_kw, bill_now, calib)
        if year == 1:
            first = (saving, generation, banked)
        if year == ECON["inverter_replacement_year"]:
            saving -= kw * ECON["inverter_replacement_rs_per_kw"]
        flows.append(saving)

    payback, cumulative = None, 0.0
    for year, f in enumerate(flows, start=1):
        if f > 0 and cumulative + f >= net_cost:
            payback = year - 1 + (net_cost - cumulative) / f
            break
        cumulative += f

    rate = ECON["discount_rate_pct"] / 100
    loan = loan_for(gross)
    optimistic, _, _ = _year(kw, 1, units, sy.optimistic, tariff, h.sanctioned_kw, bill_now, calib)
    return Option(
        kw=kw,
        gross_cost=gross,
        subsidy=subsidy,
        net_cost=net_cost,
        generation_kwh=first[1],
        export_kwh=first[2],
        savings_rs=first[0],
        savings_optimistic_rs=optimistic,
        payback_years=payback,
        savings_25y_rs=sum(flows) - net_cost,
        npv_rs=sum(f / (1 + rate) ** y for y, f in enumerate(flows, start=1)) - net_cost,
        loan_rate_pct=loan.rate_pct,
        emi_rs=emi(loan.principal, loan.rate_pct, loan.years),
        emi_after_subsidy_rs=emi(max(0.0, loan.principal - subsidy), loan.rate_pct, loan.years),
        co2_t_per_year=first[1] / 1000 * EMISSION_T_PER_MWH,
        roof_sqft_needed=kw * ECON["roof_sqft_per_kw"],
        needs_load_increase=kw > h.sanctioned_kw,
    )


def analyze(h: Household, sy: SolarYield, tariff: Tariff | None = None) -> Analysis:
    tariff = tariff or Tariff.for_discom(h.discom)
    units, estimated = fill_months(h.monthly_units)
    calib = calibration_factor(h, tariff)
    bill_now = sum(tariff.bill(u, h.sanctioned_kw).net for u in units)
    usage = sum(units)

    top = min(ECON["max_kw"], max(1, math.ceil(usage / sy.annual * 1.3)))
    options = [evaluate(kw, h, units, sy, tariff, bill_now, calib) for kw in range(1, top + 1)]
    fits = [o for o in options if h.roof_sqft is None or o.roof_sqft_needed <= h.roof_sqft]
    best = max(fits, key=lambda o: o.npv_rs, default=None)
    free = (tariff.subsidy or {}).get("free_upto_units", 0)

    notes = []
    if best is None:
        verdict, reason = "skip", "roof_too_small"
    elif best.npv_rs <= 0 or best.savings_rs < MIN_YEARLY_SAVING_RS:
        within_free = free and sum(u <= free for u in units) > 6
        verdict, reason, best = "skip", "subsidy_covers" if within_free else "low_savings", None
    else:
        verdict, reason = "go", "covers"
        notes.append("dcr")
        if best.needs_load_increase:
            notes.append("load_increase")
        if best.export_kwh > EXPORT_HEAVY_SHARE * best.generation_kwh:
            notes.append("export_heavy")
    if estimated:
        notes.append("estimated_months")

    return Analysis(
        verdict=verdict,
        reason=reason,
        recommended=best,
        options=options,
        discom_name=tariff.discom_name,
        sanctioned_kw=h.sanctioned_kw,
        roof_sqft=h.roof_sqft,
        bill_now_rs_per_year=bill_now * calib,
        usage_units_per_year=usage,
        yield_kwh_per_kw=sy.annual,
        yield_optimistic_kwh_per_kw=sy.annual_optimistic,
        calibration=calib,
        estimated_months=estimated,
        usage_by_month=units,
        yield_by_month=list(sy.monthly),
        free_units=free,
        export_rate=tariff.export_rate,
        notes=notes,
    )
