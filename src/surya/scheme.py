"""PM Surya Ghar rules: the central subsidy, collateral-free loans, and market prices."""

from __future__ import annotations

from dataclasses import dataclass

from . import load_data

SCHEME = load_data("scheme.json")
PMSGY = SCHEME["pmsgy"]


@dataclass(frozen=True)
class Loan:
    principal: float
    rate_pct: float
    years: int


def central_subsidy(kw: float, state: str) -> float:
    special = state in PMSGY["special_category_states"]
    rule = PMSGY["central_subsidy"]["special_category" if special else "general"]
    first_two = min(kw, 2) * rule["per_kw_first_2"]
    third = max(0.0, min(kw, 3) - 2) * rule["per_kw_3rd"]
    return min(first_two + third, rule["cap"])


def system_cost(kw: float, level: str = "typical") -> float:
    band = "upto_3kw" if kw <= 3 else "above_3kw"
    return kw * SCHEME["cost_rs_per_kw"][band][level]


def loan_for(gross_cost: float) -> Loan:
    terms = PMSGY["loan"]
    principal = gross_cost * (1 - terms["margin_pct"] / 100)
    low = principal <= terms["low_rate_upto_rs"]
    rate = terms["low_rate_pct"] if low else terms["standard_rate_pct"]
    return Loan(principal, rate, terms["tenure_years"])


def emi(principal: float, rate_pct: float, years: int) -> float:
    n, r = years * 12, rate_pct / 1200
    if principal <= 0:
        return 0.0
    if r == 0:
        return principal / n
    return principal * r * (1 + r) ** n / ((1 + r) ** n - 1)
