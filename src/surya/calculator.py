"""Turns one household's bill history into a sized, priced, honest solar recommendation."""

from __future__ import annotations

import math
from dataclasses import asdict, dataclass, field

from .scheme import SCHEME, central_subsidy, emi, loan_for, system_cost
from .solar import DAYS, SolarYield
from .tariff import Tariff

ECON = SCHEME["economics"]
EMISSION_T_PER_MWH = SCHEME["grid_emission_t_per_mwh"]
FY_ORDER = (4, 5, 6, 7, 8, 9, 10, 11, 12, 1, 2, 3)  # surplus units are banked across one financial year
MIN_YEARLY_SAVING_RS = 3000
COOLING_BASE_C = 24.0
SMALLER_IF_WITHIN = 0.90  # a smaller size within 10% of the best 25-year value wins  # above this monthly mean, Delhi homes run fans and ACs
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
    bonus: dict | None = None  # state scheme on top of PM Surya Ghar, not counted in the numbers above

    def to_dict(self) -> dict:
        return asdict(self)


def cooling_degree_days(temps: tuple[float, ...]) -> list[float]:
    return [max(0.0, t - COOLING_BASE_C) * d for t, d in zip(temps, DAYS)]


def _cooling_fit(known: dict[int, float], temps: tuple[float, ...]) -> tuple[float, float] | None:
    """Least squares of units = base + per_degree_day × cooling degree days, over the months on the bill."""
    cdd = cooling_degree_days(temps)
    xs, ys = [cdd[m - 1] for m in known], list(known.values())
    if len(xs) < 3 or max(xs) - min(xs) < 50:  # not enough temperature spread to learn the AC load
        return None
    mx, my = sum(xs) / len(xs), sum(ys) / len(ys)
    sxx = sum((x - mx) ** 2 for x in xs)
    per_dd = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / sxx
    if per_dd <= 0:
        return None
    return my - per_dd * mx, per_dd


def fill_months(monthly_units: dict, temps: tuple[float, ...] | None = None) -> tuple[list[float], list[int], str]:
    """12 months of usage: the bill's months as read, the rest estimated from the household's own
    usage against local temperature when possible, otherwise its average."""
    known = {int(m): float(u) for m, u in monthly_units.items() if u is not None}
    if not known:
        raise ValueError("need at least one month of electricity usage")
    if any(not 1 <= m <= 12 for m in known):
        raise ValueError("months must be numbered 1-12")
    missing = [m for m in range(1, 13) if m not in known]
    fit = _cooling_fit(known, temps) if temps and missing else None
    if fit:
        base, per_dd = fit
        floor = 0.8 * min(known.values())
        cdd = cooling_degree_days(temps)
        return [known.get(m, max(floor, base + per_dd * cdd[m - 1])) for m in range(1, 13)], missing, "temperature"
    mean = sum(known.values()) / len(known)
    return [known.get(m, mean) for m in range(1, 13)], missing, "average"


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


def evaluate(kw: float, h: Household, units: list[float], sy: SolarYield, tariff: Tariff, bill_now: float, calib: float,
             extra_subsidy: float = 0.0) -> Option:
    gross = system_cost(kw)
    subsidy = central_subsidy(kw, tariff.state) + extra_subsidy
    net_cost = max(0.0, gross - subsidy)

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


def state_bonus(h: Household, units: list[float], sy: SolarYield, tariff: Tariff, bill_now: float, calib: float,
                recommended: Option | None) -> dict | None:
    """What a state scheme adds. Shown separately: these schemes are new and their guidelines still moving."""
    scheme = SCHEME.get("state_schemes", {}).get(tariff.state)
    if not scheme:
        return None
    avg = sum(units) / 12
    zero = scheme.get("zero_upfront")
    out = {"name": scheme["name"], "status": scheme["status"], "apply_at": scheme["apply_at"], "avg_units": avg}
    if zero and avg <= zero["max_avg_units_per_month"]:
        kw = zero["max_kw"]
        o = evaluate(kw, h, units, sy, tariff, bill_now, calib, extra_subsidy=system_cost(kw))
        out["zero_upfront"] = {"kw": kw, "savings_rs": o.savings_rs, "savings_25y_rs": o.savings_25y_rs,
                               "free_maintenance_years": zero["free_maintenance_years"], "needs_load_increase": kw > h.sanctioned_kw}
    elif recommended and scheme.get("top_up_per_kw"):
        extra = min(recommended.kw * scheme["top_up_per_kw"], scheme["top_up_cap"], recommended.net_cost)
        o = evaluate(recommended.kw, h, units, sy, tariff, bill_now, calib, extra_subsidy=extra)
        out["top_up"] = {"kw": o.kw, "net_cost": o.net_cost, "net_cost_central_only": recommended.net_cost,
                         "payback_years": o.payback_years, "extra_subsidy": o.subsidy - recommended.subsidy}
    return out if ("zero_upfront" in out or "top_up" in out) else None


def analyze(h: Household, sy: SolarYield, tariff: Tariff | None = None) -> Analysis:
    tariff = tariff or Tariff.for_discom(h.discom)
    units, estimated, fill = fill_months(h.monthly_units, sy.temp_c)
    calib = calibration_factor(h, tariff)
    bill_now = sum(tariff.bill(u, h.sanctioned_kw).net for u in units)
    usage = sum(units)

    top = min(ECON["max_kw"], max(1, math.ceil(usage / sy.annual * 1.3)))
    options = [evaluate(kw, h, units, sy, tariff, bill_now, calib) for kw in range(1, top + 1)]
    fits = [o for o in options if h.roof_sqft is None or o.roof_sqft_needed <= h.roof_sqft]
    best = max(fits, key=lambda o: o.npv_rs, default=None)
    if best and best.npv_rs > 0:
        # nearly the same value for less money upfront: recommend the smaller system
        best = min((o for o in fits if o.npv_rs >= SMALLER_IF_WITHIN * best.npv_rs), key=lambda o: o.kw)
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
        notes.append("estimated_months_temp" if fill == "temperature" else "estimated_months")
    if tariff.learned:
        notes.append("tariff_learned")

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
        bonus=state_bonus(h, units, sy, tariff, bill_now, calib, best),
    )
