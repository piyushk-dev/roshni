from datetime import date

import pytest

from surya import knowledge, market, product, scam
from test_product_expansion import api


@pytest.fixture(autouse=True)
def fixed_date(monkeypatch):
    monkeypatch.setattr(product, "today_india", lambda: date(2026, 10, 8))


@pytest.mark.parametrize("kind", ["monitoring", "generation", "billing", "documents", "maintenance"])
def test_support_pack_is_bilingual_routed_and_not_submitted(kind):
    status, result = api("POST", "/care/support", {"kind":kind, "first_noticed":"2026-09-29", "contacted_on":"2026-10-01"})
    assert status == 200
    assert result["id"] == kind
    assert result["days_since_contact"] == 7
    assert result["prepared_on"] == "2026-10-08"
    assert "2026-09-29" in result["draft"]["en"] and "2026-10-01" in result["draft"]["hi"]
    assert result["evidence"] and result["who"]["hi"]
    assert "does not open a service ticket" in result["note"]["en"]
    assert "not an official response deadline" in result["note"]["en"]
    assert result["source"].startswith("https://")


def test_monitoring_loss_is_not_treated_as_zero_production():
    result = product.support({"kind":"monitoring", "first_noticed":"2026-10-08"})
    assert "does not prove" in result["next"]["en"]
    assert result["days_since_contact"] is None
    assert "not recorded" in result["draft"]["en"]


def test_billing_request_goes_to_discom_and_asks_for_statement_not_equipment_warranty():
    result = product.support({"kind":"billing", "first_noticed":"2026-10-08"})
    assert "DISCOM" in result["who"]["en"]
    assert "import/export statement" in result["draft"]["en"]
    assert "warranty" not in result["draft"]["en"]


@pytest.mark.parametrize("changes", [
    {"kind":"random"}, {"kind":[]}, {"first_noticed":"2999-01-01"},
    {"first_noticed":"2026-02-30"}, {"first_noticed":"20261001"},
    {"contacted_on":"2999-01-01"}, {"contacted_on":"2026-09-01"},
])
def test_support_rejects_invalid_or_inconsistent_dates(changes):
    body = {"kind":"billing", "first_noticed":"2026-10-01", **changes}
    assert api("POST", "/care/support", body)[0] == 400


def test_support_topic_catalog_keeps_existing_checklist_structure():
    catalog = api("GET", "/care/checklists")[1]
    assert len(catalog["support_topics"]) == 5
    assert sum(len(g["items"]) for g in catalog["groups"]) == 12


def test_incomplete_prices_cannot_become_final_budget_prices():
    q = market.clean_quote({"total_price_rs":195000,"system_kw":3,"gst_included":"yes",
                           "net_meter_included":"yes","structure_included":"yes","earthing_included":"yes"}, "Written quote", "DL")
    assert market.assess(q,knowledge.price_band("DL",3))["budget_ready"]
    for field in ("gst_included","net_meter_included","structure_included","earthing_included"):
        for value in ("no","not_stated"):
            assert not market.assess({**q,field:value},knowledge.price_band("DL",3))["budget_ready"]


def test_ordinary_business_or_state_links_do_not_get_called_fake_portals():
    assert scam.check("Read solar.delhi.gov.in or mnre.gov.in.") == []
    flags = scam.check("Solar offer details at suryahub.com and sbi.bank.in")
    assert {f["code"] for f in flags} == {"check_site"}
    text = " ".join(scam.render(flags)["signs"])
    assert "may be legitimate" in text and "only official website" not in text
    # Matching an ending without the preceding dot must not bypass the domain check.
    assert scam.check("Read fakegov.in")[0]["code"] == "check_site"


def test_a_later_fake_scheme_link_is_not_hidden_by_an_earlier_business_link():
    flags = scam.check("Details at example.com. Apply at pmsuryaghar-offer.com. More example.com")
    assert len(flags) == 2
    assert scam.verdict(flags) == "red"
    assert any(f["code"] == "lookalike" for f in flags)


def test_survey_fees_are_scope_questions_not_proof_of_fraud():
    flags = scam.check("Written site survey fee Rs 500, refundable against project price.")
    assert {f["code"] for f in flags} == {"service_fee"}
    assert scam.verdict(flags) == "amber"
    assert "not proof of fraud" in scam.render(flags)["signs"][0]


@pytest.mark.parametrize("text", ["Processing fee: 0. Survey fee: nil.", "No booking fee. No processing fee."])
def test_zero_and_negated_fees_do_not_raise_fee_flags(text):
    assert not {"fee","service_fee"} & {f["code"] for f in scam.check(text)}


def test_nonzero_small_fee_does_not_match_zero_fee_rule():
    assert any(f["code"] == "fee" for f in scam.check("Processing fee: 0.50 INR"))


def test_an_unverified_business_link_does_not_hijack_a_long_whatsapp_question():
    question = "I am comparing solar monitoring and maintenance options. Please explain which service records I should keep after installation. I read an article on suryahub.com and want to understand my handover checklist."
    assert {f["code"] for f in scam.check(question)} == {"check_site"}
    assert not scam.looks_like_offer(question)
    assert scam.looks_like_offer("Solar offer, send OTP and pay a processing fee today. "*4)
