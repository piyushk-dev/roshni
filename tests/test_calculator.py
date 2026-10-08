import pytest
from conftest import HEAVY_AC, LOW, MODERATE, months

from surya.calculator import Household, analyze, calibration_factor, fill_months, year_with_solar
from surya.tariff import Tariff


def test_heavy_ac_home_should_go_solar(delhi_yield):
    a = analyze(Household("BRPL", 5, months(HEAVY_AC)), delhi_yield)
    assert a.verdict == "go"
    assert 3 <= a.recommended.kw <= 5
    assert a.recommended.payback_years < 6
    assert "dcr" in a.notes


def test_low_usage_home_is_told_to_skip(delhi_yield):
    a = analyze(Household("BYPL", 2, months(LOW)), delhi_yield)
    assert a.verdict == "skip"
    assert a.reason == "subsidy_covers"
    assert a.recommended is None


def test_bigger_is_not_always_better(delhi_yield):
    """The 3rd kW mostly offsets cheap, subsidised units, so 2 kW wins for a moderate home."""
    a = analyze(Household("TPDDL", 3, months(MODERATE)), delhi_yield)
    assert a.recommended.kw < 3


def test_smaller_size_wins_when_value_is_nearly_the_same(delhi_yield):
    """Real BRPL bill: 3 kW is worth only ~10% more than 2 kW over 25 years, for Rs 47,000 more upfront."""
    a = analyze(Household("BRPL", 6, REAL_BILL), delhi_yield)
    top = max(o.npv_rs for o in a.options)
    assert a.recommended.kw == 2
    assert a.recommended.npv_rs >= 0.9 * top and a.recommended.npv_rs < top


def test_small_roof_caps_the_size(delhi_yield):
    a = analyze(Household("BRPL", 5, months(HEAVY_AC), roof_sqft=250), delhi_yield)
    assert a.recommended.kw == 2


def test_tiny_roof_is_a_skip(delhi_yield):
    a = analyze(Household("BRPL", 5, months(HEAVY_AC), roof_sqft=60), delhi_yield)
    assert (a.verdict, a.reason) == ("skip", "roof_too_small")


def test_load_increase_is_flagged(delhi_yield):
    a = analyze(Household("BRPL", 2, months(HEAVY_AC)), delhi_yield)
    assert a.recommended.kw > 2
    assert "load_increase" in a.notes


def test_net_metering_banks_surplus_into_later_months():
    tariff = Tariff.for_discom("BRPL")
    units = [300] * 12
    generation = [0.0] * 12
    generation[3] = 500  # April surplus of 200 units...
    total, banked = year_with_solar(units, generation, tariff, 3)
    may_bill = tariff.bill(100, 3).net  # ...covers 200 of May's 300
    rest = 10 * tariff.bill(300, 3).net
    assert total == pytest.approx(tariff.bill(0, 3).net + may_bill + rest)
    assert banked == 0


def test_missing_months_take_the_average_without_temperature():
    units, missing, method = fill_months({1: 300, 2: 500})
    assert units[5] == 400 and method == "average"
    assert missing == list(range(3, 13))
    with pytest.raises(ValueError):
        fill_months({})


# the real BRPL bill: December to June, no July to November
REAL_BILL = {12: 68, 1: 78, 2: 85, 3: 155, 4: 178, 5: 560, 6: 611}


def test_missing_months_follow_temperature(delhi_yield):
    units, missing, method = fill_months(REAL_BILL, delhi_yield.temp_c)
    assert method == "temperature" and missing == [7, 8, 9, 10, 11]
    assert [units[m - 1] for m in REAL_BILL] == list(REAL_BILL.values())  # the bill's own months stay
    jul, aug, sep, octo, nov = (units[m - 1] for m in missing)
    assert jul > aug > sep > octo > nov  # Delhi cools from July to November
    assert jul > 350 and nov < 120


def test_too_little_temperature_spread_falls_back_to_average(delhi_yield):
    _, _, method = fill_months({12: 70, 1: 80, 2: 90}, delhi_yield.temp_c)  # all cool months
    assert method == "average"


def test_real_bill_estimate_uses_temperature(delhi_yield):
    a = analyze(Household("BRPL", 6, REAL_BILL), delhi_yield)
    assert "estimated_months_temp" in a.notes
    assert a.usage_by_month[6] > a.usage_by_month[10]  # July estimated above November


def test_calibration_is_clamped():
    tariff = Tariff.for_discom("BRPL")
    modelled = tariff.bill(500, 3).net
    assert calibration_factor(Household("BRPL", 3, {}, last_bill_rs=modelled * 1.1, last_bill_units=500), tariff) == pytest.approx(1.1)
    assert calibration_factor(Household("BRPL", 3, {}, last_bill_rs=modelled * 5, last_bill_units=500), tariff) == 1.4
    assert calibration_factor(Household("BRPL", 3, {}), tariff) == 1.0
