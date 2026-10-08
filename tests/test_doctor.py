from surya import bill_reader, doctor
from surya.tariff import Tariff


def reading(**kw):
    base = dict(is_electricity_bill=True, discom="BRPL", sanctioned_load_kw=6, max_demand_kw=3.1)
    return bill_reader.BillReading(**{**base, **kw})


def test_the_real_bill_is_paying_for_unused_load():
    """6 kW sanctioned, 3.1 kW peak: drop to 4 kW and Delhi's fixed charge falls from Rs 100/kW to Rs 50/kW."""
    found = doctor.check(reading(), Tariff.for_discom("BRPL"))
    load = next(f for f in found if f.code == "load")
    assert load.values["new"] == 4
    assert 5000 < load.saves_rs < 7000  # (600 - 200) a month, plus the surcharges and tax on it


def test_one_off_charges_and_estimated_readings_are_flagged():
    found = doctor.check(reading(max_demand_kw=None, other_charges_rs=4797.14, reading_type="estimated"), Tariff.for_discom("BRPL"))
    assert {f.code for f in found} == {"other", "estimated"}
    assert "₹4,797" in doctor.message(found, "en")


def test_net_metered_bill_without_exports():
    found = doctor.check(reading(max_demand_kw=None, net_metered=True, export_units=0), Tariff.for_discom("BRPL"))
    assert [f.code for f in found] == ["export_missing"]


def test_a_clean_bill_has_nothing_to_say():
    found = doctor.check(reading(sanctioned_load_kw=4, max_demand_kw=3.4), Tariff.for_discom("BRPL"))
    assert found == [] and doctor.message(found) is None
    assert doctor.render(found, "hi")["none"]


def test_hindi_renders():
    found = doctor.check(reading(other_charges_rs=500, reading_type="estimated"), Tariff.for_discom("BRPL"))
    text = doctor.message(found, "hi")
    assert "{" not in text and "बिल की जाँच" in text
