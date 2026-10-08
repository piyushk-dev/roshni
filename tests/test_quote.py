from surya import quote

FAIR = {
    "is_solar_quote": True, "vendor_name": "Fair Solar", "system_kw": 3, "total_price_rs": 189000, "gst_included": "yes",
    "subsidy_promised_rs": 78000, "module_watt": 550, "module_count": 6, "dcr": "yes", "inverter_kw": 3,
    "module_performance_warranty_years": 25, "inverter_warranty_years": 8, "system_warranty_years": 5,
    "net_meter_included": "yes", "structure_included": "yes", "earthing_included": "yes", "advance_pct": 20,
}


def codes(q):
    return [f.code for f in quote.check(q)]


def test_a_fair_quote_passes():
    assert codes(FAIR) == []
    assert quote.verdict(quote.check(FAIR)) == "ok"
    assert "looks fair" in quote.message(FAIR, quote.check(FAIR), "en")


def test_non_dcr_panels_cost_the_whole_subsidy():
    flags = quote.check({**FAIR, "dcr": "no"})
    assert flags[0].code == "not_dcr" and flags[0].values["subsidy"] == "₹78,000"
    assert quote.verdict(flags) == "red"


def test_silence_on_dcr_is_also_red():
    assert "dcr_unstated" in codes({**FAIR, "dcr": "not_stated"})


def test_subsidy_promise_above_the_scheme_cap():
    assert "subsidy_overpromised" in codes({**FAIR, "subsidy_promised_rs": 94800})
    assert "subsidy_overpromised" not in codes({**FAIR, "system_kw": 2, "module_count": 4, "subsidy_promised_rs": 60000})


def test_price_is_compared_including_gst():
    assert "price_high" not in codes({**FAIR, "total_price_rs": 200000})
    flags = quote.check({**FAIR, "total_price_rs": 200000, "gst_included": "no"})  # 2.18 lakh with GST
    assert {"gst_excluded", "price_high"} <= {f.code for f in flags}
    assert "price_low" in codes({**FAIR, "total_price_rs": 120000})


def test_fewer_panels_than_quoted_is_flagged_more_is_fine():
    assert "capacity_mismatch" in codes({**FAIR, "module_count": 5})
    assert "capacity_mismatch" not in codes({**FAIR, "module_count": 7})


def test_hardware_warranty_and_payment_terms():
    found = codes({**FAIR, "inverter_kw": 2, "module_performance_warranty_years": 10, "inverter_warranty_years": 2,
                   "system_warranty_years": 1, "advance_pct": 70})
    assert {"inverter_small", "short_module_warranty", "short_inverter_warranty", "short_system_warranty", "big_advance"} <= set(found)
    text = quote.message(FAIR, quote.check({**FAIR, "system_warranty_years": 1}), "en")
    assert "only 1 year;" in text


def test_missing_inclusions_become_questions():
    flags = quote.check({**FAIR, "net_meter_included": "no", "earthing_included": "not_stated"})
    assert [f.code for f in flags if f.level == "ask"] == ["net_meter", "earthing"]
    assert quote.verdict(flags) == "ok"


def test_hindi_renders_without_placeholders():
    flags = quote.check({**FAIR, "dcr": "no", "module_count": 5, "system_warranty_years": 1, "gst_included": "no", "total_price_rs": 230000})
    text = quote.message({**FAIR, "dcr": "no"}, flags, "hi")
    assert "{" not in text and "अभी साइन न करें" in text


def test_not_a_quote():
    assert "doesn't look like a solar quotation" in quote.message({"is_solar_quote": False}, [], "en")
