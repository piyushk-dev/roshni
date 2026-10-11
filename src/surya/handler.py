"""Lambda entry point behind API Gateway: POST /bill, POST /analyze, GET /health."""

from __future__ import annotations

import base64
import json
from dataclasses import asdict
from importlib import resources

from . import doctor, knowledge, market, panel, pipeline, places, product, quote, scam, trace
from .format import BillProblem, bonus_text, explain, message


def _response(status: int, payload: dict) -> dict:
    return {
        "statusCode": status,
        "headers": {"content-type": "application/json; charset=utf-8"},
        "body": json.dumps(payload, ensure_ascii=False),
    }


def _fact_route(route: str) -> tuple[str, str] | None:
    parts = route.split(" ", 1)[1].strip("/").split("/")
    if route.startswith("POST ") and len(parts) == 3 and parts[0] == "facts" and parts[2] in ("confirm", "report"):
        return parts[1], parts[2]
    return None


def _fact_action(fact: tuple[str, str], event: dict) -> dict:
    fact_id, action = fact
    if fact_id not in {f["id"] for f in knowledge.facts()}:
        return _response(404, {"error": f"no fact {fact_id}"})
    if action == "confirm":
        return _response(200, knowledge.confirm(fact_id))
    body = json.loads(event.get("body") or "{}")
    if not str(body.get("value", "")).strip():
        return _response(400, {"error": "say what the new value is"})
    return _response(200, knowledge.report(fact_id, str(body["value"]), str(body.get("evidence", ""))))


def _handle(event: dict, context) -> dict:
    route = f"{event['requestContext']['http']['method']} {event['rawPath']}"
    trace.start()
    params = event.get("queryStringParameters") or {}
    body = json.loads(event.get("body") or "{}")
    if route == "GET /vendors":
        return _response(200, {"vendors": market.vendors_for(params.get("state", "DL"))})
    if route == "GET /schemes":
        return _response(200, product.schemes(params.get("state", "DL"), params.get("kw", 3), params.get("dcr", "yes")))
    if route == "POST /finance/plan":
        return _response(200, product.finance(body))
    if route == "GET /care/dust":
        try:
            return _response(200, product.dust(params.get("lat"), params.get("lon")))
        except ValueError:
            raise
        except Exception:  # the forecast service is down or slow; the rest of the page still works
            return _response(502, {"error": "dust forecast unavailable right now"})
    if route == "GET /care/checklists":
        return _response(200, product.checklists())
    if route == "POST /care/check":
        return _response(200, product.care(body))
    if route == "POST /care/bill":
        return _response(200, product.bill_balance(body))
    if route == "POST /care/support":
        return _response(200, product.support(body))
    if route == "POST /scam-check":
        text = body.get("text", "")
        if not isinstance(text, str) or not text.strip() or len(text) > 10000:
            raise ValueError("paste an offer of 1–10,000 characters")
        flags = scam.check(text)
        return _response(200, {"flags": flags, "views": {lang: scam.render(flags, lang) for lang in ("en", "hi")}})
    if route == "POST /panel":
        data = base64.b64decode(body.get("file_base64") or "", validate=True)
        if not data:
            raise ValueError("send a photo of the panel's label")
        media_type = pipeline._media_type(body.get("media_type", "image/jpeg"))
        with trace.step("bedrock", "panel"):
            fields, _ = panel.read_label(data, media_type)
        expect = body.get("expect_watt")
        flags = panel.check(fields, float(expect) if expect not in (None, "") else None, str(body.get("owner") or "")[:64] or None,
                            sample=bool(body.get("sample")))
        return _response(200, {"fields": fields, "flags": flags, "views": {code: panel.render(fields, flags, code) for code in ("en", "hi")},
                                "trace": trace.steps()})
    if route == "GET /plant":
        from . import plant

        num = lambda k, d: params.get(k) if params.get(k) not in (None, "") else d
        try:
            return _response(200, plant.simulate(num("kw", 3), num("lat", 28.61), num("lon", 77.21), params.get("cleaned") or None,
                                                 params.get("installed") or None, num("rate", 7), float(params["promised"]) if params.get("promised") else None,
                                                 num("use", 300), lang=params.get("lang", "en")))
        except ValueError:
            raise
        except Exception:  # the weather service is down or slow
            return _response(502, {"error": "the panel simulator can't reach the weather service right now"})
    if route == "GET /places":
        found = places.find(str(params.get("q", ""))[:120])
        return _response(200, found) if found else _response(404, {"error": "couldn't find that place in India"})
    if route == "GET /market/open":
        return _response(200, {"requests": market.open_requests(product.state_code(params.get("state", "DL")),
                                                                 knowledge.slug(params["vendor"]) if params.get("vendor") else None)})
    if route == "POST /market/requests":
        return _response(201, market.create_request(body))
    if route == "POST /market/preview":
        state = product.state_code(body.get("state", "DL"))
        raw = body.get("quote")
        if not isinstance(raw, dict):
            raise ValueError("quote fields are required")
        name = str(body.get("name", "Your quote"))[:80]
        q = market.clean_quote(raw, name, state)
        band = knowledge.price_band(state, q["system_kw"])
        return _response(200, {"quote": q, "check": market.assess(q, band), "band": band})
    parts = event["rawPath"].strip("/").split("/")
    if len(parts) in (3, 4) and parts[:2] == ["market", "requests"]:
        rid = parts[2]
        method = event["requestContext"]["http"]["method"]
        if method == "GET" and len(parts) == 3:
            return _response(200, market.view(rid))
        if method == "DELETE" and len(parts) == 3:
            market.forget(rid)
            return _response(200, {"deleted": True})
        if method == "POST" and len(parts) == 4 and parts[3] == "choose":
            return _response(200, market.choose(rid, str(body.get("vendor_id", ""))))
        if method == "POST" and len(parts) == 4 and parts[3] == "quotes":
            raw = body.get("quote")
            if not isinstance(raw, dict):
                raise ValueError("quote fields are required")
            return _response(201, market.submit_quote(rid, str(body.get("vendor_name", "")), raw))
    if route == "GET /health":
        return _response(200, {"ok": True})
    if route == "GET /privacy":
        page = resources.files("surya").joinpath("privacy.html").read_text(encoding="utf-8")
        return {"statusCode": 200, "headers": {"content-type": "text/html; charset=utf-8"}, "body": page}
    if route == "GET /stats":
        return _response(200, knowledge.stats())
    if route == "GET /stats/stages":
        return _response(200, {"stages": knowledge.stage_times()})
    if route == "GET /journey":
        from .journey import J

        return _response(200, J)
    if route == "GET /facts":
        scope = (event.get("queryStringParameters") or {}).get("scope")
        return _response(200, {"facts": knowledge.facts(scope)})
    fact = _fact_route(route)
    if fact:
        return _fact_action(fact, event)
    if route == "POST /ask":
        from . import qa
        from .bot import DEVANAGARI

        body = json.loads(event.get("body") or "{}")
        question = str(body.get("question", "")).strip()
        if not question:
            return _response(400, {"error": "ask a question"})
        context = {"last": body["last"]} if isinstance(body.get("last"), dict) else {}
        lang = "hi" if DEVANAGARI.search(question) else body.get("lang", "en")  # answer in the question's script
        out = qa.answer_full(question[:500], context, lang)
        return _response(200, {"answer": out["text"], "used": out["used"]})
    if route not in ("POST /analyze", "POST /bill", "POST /quote"):
        return _response(404, {"error": f"no route {route}"})

    raw = event.get("body") or "{}"
    if event.get("isBase64Encoded"):
        raw = base64.b64decode(raw).decode("utf-8")
    lang = "en"
    try:
        body = json.loads(raw)
        lang = body.get("lang", "en")
        reading = None
        if route == "POST /quote":
            q, flags, band = pipeline.check_quote(base64.b64decode(body["file_base64"]), body.get("media_type", "image/jpeg"), bool(body.get("sample")))
            if not q.get("is_solar_quote"):
                return _response(422, {"error": quote.message(q, flags, lang), "code": "not_a_quote"})
            return _response(200, {
                "quote": q,
                "flags": quote.flags_dict(flags),
                "band": band,
                "views": {code: quote.render(q, flags, code, band) for code in ("en", "hi")},
                "message": quote.message(q, flags, lang, band),
                "trace": trace.steps(),
            })
        sample = bool(body.get("sample"))  # the bundled sample bill moves no counters
        if route == "POST /bill":
            request, reading = pipeline.request_from_bill(base64.b64decode(body["file_base64"]), body.get("media_type", "image/jpeg"), sample)
            body = {**{k: body[k] for k in ("lat", "lon", "roof_sqft") if k in body}, **request}
        a = pipeline.run(body)
        if reading and not sample:
            pipeline.count_analysis(a)
    except BillProblem as p:
        return _response(422, {"error": p.text(lang), "code": p.code})
    except (KeyError, ValueError, TypeError) as e:
        return _response(400, {"error": str(e)})
    reason, notes = explain(a, lang)
    result = {"analysis": a.to_dict(), "reason": reason, "notes": notes, "bonus": bonus_text(a, lang), "message": message(a, lang),
              "trace": trace.steps()}
    if reading:
        result["bill"] = asdict(reading)
        found = pipeline.bill_checkup(reading, body, sample)
        result["doctor"] = {"findings": doctor.to_dict(found), "views": {code: doctor.render(found, code) for code in ("en", "hi")}}
    return _response(200, result)


def lambda_handler(event: dict, context) -> dict:
    """Validate the envelope consistently, including the new deterministic routes."""
    try:
        raw = event.get("body") or "{}"
        if event.get("isBase64Encoded"):
            raw = base64.b64decode(raw, validate=True).decode("utf-8")
        body = json.loads(raw)
        if not isinstance(body, dict):
            raise ValueError("body must be a JSON object")
        return _handle({**event, "body": json.dumps(body), "isBase64Encoded": False}, context)
    except KeyError:
        return _response(404, {"error": "request not found or expired"})
    except (ValueError, TypeError, OverflowError, UnicodeDecodeError) as e:
        return _response(400, {"error": str(e)})
