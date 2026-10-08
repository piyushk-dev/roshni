import pytest

from surya.tariff import Tariff


@pytest.fixture
def brpl():
    return Tariff.for_discom("BRPL")


def test_slabs_are_telescopic(brpl):
    assert brpl.energy_charge(0) == 0
    assert brpl.energy_charge(200) == 600
    assert brpl.energy_charge(450) == 200 * 3 + 200 * 4.5 + 50 * 6.5
    assert brpl.energy_charge(1300) == 600 + 900 + 2600 + 2800 + 800


def test_fixed_charge_uses_the_band_of_the_whole_load(brpl):
    assert brpl.fixed_charge(1.5) == 30
    assert brpl.fixed_charge(2) == 40
    assert brpl.fixed_charge(3) == 150
    assert brpl.fixed_charge(6) == 600


def test_delhi_subsidy_bands(brpl):
    assert brpl.bill(180, 2).net == 0
    mid = brpl.bill(350, 3)
    assert mid.subsidy == pytest.approx(min(mid.gross / 2, 800))
    assert brpl.bill(450, 3).subsidy == 0


def test_fppas_differs_by_provider():
    assert Tariff.for_discom("TPDDL").bill(500, 3).gross > Tariff.for_discom("BYPL").bill(500, 3).gross


def test_matches_a_real_brpl_bill(brpl):
    """BRPL, 09-06-2026 to 06-07-2026, 562 units, 6 kW. Energy 2634.00 is printed; fixed 556.10 is derived
    from the printed 8% surcharge. The bill's own lines: surcharge 255.21, pension 223.31, tax 165.49;
    total before its one-off "other charges" 4397.44."""
    b = brpl.bill_from_charges(562, 2634.00, 556.10)
    assert b.surcharge == pytest.approx(255.21, abs=0.05)
    assert b.pension == pytest.approx(223.31, abs=0.05)
    assert b.tax == pytest.approx(165.49, rel=0.02)
    assert b.gross == pytest.approx(4397.44, rel=0.03)


def test_unknown_provider():
    with pytest.raises(KeyError):
        Tariff.for_discom("NOPE")
