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
    best = a.recommended
    assert all(best.npv_rs >= o.npv_rs for o in a.options)
    assert best.kw < 3


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


def test_missing_months_take_the_average():
    units, missing = fill_months({1: 300, 2: 500})
    assert units[5] == 400
    assert missing == list(range(3, 13))
    with pytest.raises(ValueError):
        fill_months({})


def test_calibration_is_clamped():
    tariff = Tariff.for_discom("BRPL")
    modelled = tariff.bill(500, 3).net
    assert calibration_factor(Household("BRPL", 3, {}, last_bill_rs=modelled * 1.1, last_bill_units=500), tariff) == pytest.approx(1.1)
    assert calibration_factor(Household("BRPL", 3, {}, last_bill_rs=modelled * 5, last_bill_units=500), tariff) == 1.4
    assert calibration_factor(Household("BRPL", 3, {}), tariff) == 1.0
