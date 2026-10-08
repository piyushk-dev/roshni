import pytest

from surya.scheme import central_subsidy, emi, loan_for


@pytest.mark.parametrize("kw, expected", [(1, 30000), (2, 60000), (2.5, 69000), (3, 78000), (5, 78000)])
def test_central_subsidy_general(kw, expected):
    assert central_subsidy(kw, "DL") == expected


def test_central_subsidy_special_category():
    assert central_subsidy(3, "HP") == 85800


def test_emi_matches_the_textbook_case():
    assert emi(100000, 12, 1) == pytest.approx(8884.88, abs=0.01)
    assert emi(0, 7, 10) == 0


def test_low_rate_only_up_to_two_lakh():
    assert loan_for(195000).rate_pct == 5.75  # 90% financed = 1.755 lakh
    assert loan_for(232000).rate_pct == 7.90
