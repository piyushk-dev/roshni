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


def test_ppac_differs_by_provider():
    assert Tariff.for_discom("BYPL").bill(500, 3).gross > Tariff.for_discom("BRPL").bill(500, 3).gross


def test_unknown_provider():
    with pytest.raises(KeyError):
        Tariff.for_discom("NOPE")
