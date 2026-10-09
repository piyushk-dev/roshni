"""Get quotes from vendors, compared on one basis and checked before the household sees them.

A household asks once (size from the bill, state, pin code). Every quote goes through the same
checker as an uploaded quote and is shown with the price after subsidy, because a cheap quote with
imported panels is the most expensive one once the subsidy is lost.

The demo vendors are fictional (data/vendors.json); each shows a different trap. Their replies,
scorecards and group prices are simulated and never touch the live impact counters. Real vendors
can answer requests through the vendor form; their scorecards come only from quotes they sent.
Requests pooled by pin code unlock a group price at five homes, like a Solarize campaign.

Everything lives in one DynamoDB table (pk, sk). Without MARKET_TABLE it falls back to memory.
Requests expire after 30 days and can be deleted at any time.
"""

from __future__ import annotations

import json
import math
import os
import re
import secrets
import time

from . import knowledge, load_data, quote
from .format import inr
from .scheme import SCHEME, central_subsidy
from .product import number, state_code

TTL_DAYS = 30
GROUP_WINDOW_DAYS = 30
GROUP_TIERS = ((15, 10), (10, 8), (5, 5))  # homes -> % off the demo vendors' price
_table = None
_mem: dict[str, dict[str, dict]] = {}


# --- storage ---------------------------------------------------------------------------------

def _t():
    global _table
    if not os.environ.get("MARKET_TABLE"):
        return None
    if _table is None:
        import boto3

        _table = boto3.resource("dynamodb").Table(os.environ["MARKET_TABLE"])
    return _table


def _put(pk: str, sk: str, data: dict) -> None:
    item = {"pk": pk, "sk": sk, "data": json.dumps(data, ensure_ascii=False), "expires": int(time.time()) + TTL_DAYS * 86400}
    t = _t()
    if t:
        t.put_item(Item=item)
    else:
        _mem.setdefault(pk, {})[sk] = item


def _get(pk: str, sk: str) -> dict | None:
    t = _t()
    item = t.get_item(Key={"pk": pk, "sk": sk}).get("Item") if t else _mem.get(pk, {}).get(sk)
    return json.loads(item["data"]) if item and item.get("expires", 0) > time.time() else None


def _query(pk: str, prefix: str = "", since: int | None = None) -> list[dict]:
    t = _t()
    if t:
        from boto3.dynamodb.conditions import Key

        cond = Key("pk").eq(pk)
        if since is not None:
            cond &= Key("sk").gte(f"{since:010d}")
        elif prefix:
            cond &= Key("sk").begins_with(prefix)
        result = t.query(KeyConditionExpression=cond)
        items = result["Items"]
        while result.get("LastEvaluatedKey"):
            result = t.query(KeyConditionExpression=cond, ExclusiveStartKey=result["LastEvaluatedKey"])
            items.extend(result["Items"])
    else:
        items = [i for sk, i in sorted(_mem.get(pk, {}).items())
                 if sk.startswith(prefix) and (since is None or sk >= f"{since:010d}")]
    return [json.loads(i["data"]) for i in items if i.get("expires", 0) > time.time()]


def _delete(pk: str, sk: str) -> None:
    t = _t()
    if t:
        t.delete_item(Key={"pk": pk, "sk": sk})
    else:
        _mem.get(pk, {}).pop(sk, None)


def forget(rid: str) -> None:
    req = _get(f"REQ#{rid}", "META")
    if not req:
        raise KeyError(rid)
    key = f"{req['created']:010d}#{rid}"
    for row in _query(f"REQ#{rid}", "QUOTE#"):
        _delete(f"REQ#{rid}", f"QUOTE#{row['vendor_id']}")
    _delete(f"REQ#{rid}", "META")
    _delete(f"OPEN#{req['state']}", key)
    if req.get("pincode"):
        _delete(f"GROUP#{req['state']}#{req['pincode']}", key)
    if req.get("wa_id"):
        _delete(f"USER#{req['wa_id']}", rid)


def forget_user(wa_id: str) -> None:
    for row in _query(f"USER#{wa_id}"):
        try:
            forget(row["id"])
        except KeyError:
            _delete(f"USER#{wa_id}", row["id"])


# --- vendors ---------------------------------------------------------------------------------

def demo_vendors() -> list[dict]:
    return load_data("vendors.json")["vendors"]


def _vendor(vendor_id: str) -> dict | None:
    for v in demo_vendors():
        if v["id"] == vendor_id:
            return v
    return _get(f"VENDOR#{vendor_id}", "PROFILE")


def serves(v: dict, state: str) -> bool:
    return "*" in v.get("areas", []) or state in v.get("areas", [])


def register_vendor(name: str, state: str) -> dict:
    """A vendor answering requests for the first time. Unverified until checked against the national portal."""
    name = re.sub(r"\s+", " ", name).strip()[:80]
    if len(name) < 3:
        raise ValueError("vendor name is too short")
    vid = knowledge.slug(name)[:40]
    state = state_code(state)
    if any(vid in (d["id"], knowledge.slug(d["name"])[:40]) for d in demo_vendors()):
        raise ValueError("that name belongs to a demo vendor")
    v = _vendor(vid)
    if not v:
        v = {"id": vid, "name": name, "demo": False, "areas": [state], "since": None, "verified": False}
        _put(f"VENDOR#{vid}", "PROFILE", v)
        _put("VENDORS", vid, {"id": vid})
    return v


def scorecard(v: dict) -> dict:
    """Outcome-based score: the demo vendors carry sample figures; everyone gets live quote stats."""
    sent = _query(f"VQ#{v['id']}")
    card: dict = {"demo": bool(v.get("demo")), "quotes_sent": len(sent), "outcomes_available": False}
    if sent:
        card["flagged_quotes_pct"] = round(100 * sum(1 for s in sent if s["verdict"] != "ok") / len(sent))
        card["price_vs_typical_pct"] = round(100 * sum(s["per_kw"] / s["typical"] for s in sent) / len(sent) - 100)
    if v.get("demo"):
        card.update(v["scorecard"])
    return card


def vendors_for(state: str) -> list[dict]:
    state = state_code(state)
    real = [_vendor(i["id"]) for i in _query("VENDORS")]
    out = []
    for v in demo_vendors() + [r for r in real if r]:
        if serves(v, state):
            out.append({"id": v["id"], "name": v["name"], "demo": bool(v.get("demo")), "since": v.get("since"),
                        "verified": bool(v.get("verified")), "scorecard": scorecard(v)})
    return out


# --- groups ----------------------------------------------------------------------------------

def group_discount(homes: int) -> int:
    for need, pct in GROUP_TIERS:
        if homes >= need:
            return pct
    return 0


def group(state: str, pincode: str) -> dict | None:
    if not pincode:
        return None
    since = int(time.time()) - GROUP_WINDOW_DAYS * 86400
    homes = len(_query(f"GROUP#{state}#{pincode}", since=since))
    return {"pincode": pincode, "homes": homes, "needed": GROUP_TIERS[-1][0], "discount_pct": group_discount(homes)}


# --- quotes ----------------------------------------------------------------------------------

def demo_quote(v: dict, req: dict, band: dict, discount_pct: int = 0) -> dict:
    """The quote a demo vendor would send for this request; each persona shows a different trap."""
    tpl, kw, state = v["quote"], req["kw"], req["state"]
    per_kw = band[tpl["price"]["of"]] * tpl["price"]["x"] * (1 - discount_pct / 100)
    max_sub = central_subsidy(kw, state)
    subsidy = {"max": max_sub, "over": round(max_sub * 1.25, -3)}[tpl["subsidy"]]
    fields = {k: tpl[k] for k in ("dcr", "module_watt", "module_performance_warranty_years", "inverter_warranty_years",
                                  "system_warranty_years", "advance_pct", "timeline_days", "net_meter_included",
                                  "structure_included", "earthing_included")}
    return {
        **fields,
        "is_solar_quote": True, "vendor_name": v["name"], "state": state, "system_kw": kw,
        "total_price_rs": round(per_kw * kw, -3), "gst_included": "yes", "subsidy_promised_rs": subsidy,
        "module_count": math.ceil(kw * 1000 / tpl["module_watt"]), "inverter_kw": round(kw * tpl["inverter_ratio"], 1),
        "promised_units_per_year": round(tpl["promised_units_per_kw"] * kw, -1), "group_discount_pct": discount_pct,
    }


QUOTE_FIELDS = {
    "total_price_rs": float, "system_kw": float, "module_watt": float, "module_count": int, "inverter_kw": float,
    "module_performance_warranty_years": float, "inverter_warranty_years": float, "system_warranty_years": float,
    "advance_pct": float, "timeline_days": int, "promised_units_per_year": float, "subsidy_promised_rs": float,
}
YES_NO = ("dcr", "gst_included", "net_meter_included", "structure_included", "earthing_included")


def clean_quote(raw: dict, vendor_name: str, state: str) -> dict:
    q: dict = {"is_solar_quote": True, "vendor_name": vendor_name, "state": state}
    limits = {"total_price_rs": (10000, 5e7), "system_kw": (.5, 500), "advance_pct": (0, 100),
              "module_watt": (100, 1000), "module_count": (1, 10000), "inverter_kw": (.1, 1000),
              "timeline_days": (1, 730), "subsidy_promised_rs": (0, 5e7), "promised_units_per_year": (0, 1e7)}
    for k, cast in QUOTE_FIELDS.items():
        if raw.get(k) not in (None, ""):
            val = number(raw[k], k, *limits.get(k, (0, 100)))
            if cast is int and int(val) != val:
                raise ValueError(f"{k} must be a whole number")
            q[k] = cast(val)
    for k in YES_NO:
        q[k] = raw.get(k) if raw.get(k) in ("yes", "no") else "not_stated"
    if not q.get("total_price_rs") or not q.get("system_kw"):
        raise ValueError("a quote needs a total price and a system size")
    if not (0.5 <= q["system_kw"] <= 500 and 10000 <= q["total_price_rs"] <= 5e7):
        raise ValueError("price or size looks wrong")
    return q


def assess(q: dict, band: dict) -> dict:
    """The checker's verdict plus the numbers a household compares on."""
    flags = quote.check(q, q["state"], band)
    total = q["total_price_rs"] * (1 + quote.GST_ON_SYSTEMS if q.get("gst_included") == "no" else 1)
    kw = q["system_kw"]
    subsidy = central_subsidy(kw, q["state"]) if q.get("dcr") == "yes" else 0
    return {
        "verdict": quote.verdict(flags),
        "flags": quote.flags_dict(flags),
        "views": {lang: quote.render(q, flags, lang, band) for lang in ("en", "hi")},
        "total_rs": round(total), "per_kw": round(total / kw), "subsidy_rs": subsidy, "net_rs": round(max(0, total - subsidy)),
        "pay_upfront_rs": round(total * q["advance_pct"] / 100) if q.get("advance_pct") is not None else None,
        "subsidy_status": "subject_to_approval" if q.get("dcr") == "yes" else "not_eligible" if q.get("dcr") == "no" else "evidence_needed",
        "gst_unknown": q.get("gst_included") not in ("yes", "no"),
        "budget_ready": all(q.get(field) == "yes" for field in
                            ("gst_included", "net_meter_included", "structure_included", "earthing_included")),
    }


RANK = {"ok": 0, "amber": 1, "red": 2}


def recommend(quotes: list[dict]) -> dict | None:
    """No red flags first, then the fewest warnings, then the lowest price after subsidy."""
    usable = [q for q in quotes if q["check"]["verdict"] != "red"]
    if not usable:
        return None
    key = lambda q: (RANK[q["check"]["verdict"]], sum(f["level"] == "amber" for f in q["check"]["flags"]), q["check"]["net_rs"])
    best = min(usable, key=key)
    cheapest = min(quotes, key=lambda q: q["check"]["total_rs"])
    return {"vendor_id": best["vendor_id"], "cheapest_vendor_id": cheapest["vendor_id"],
            "cheapest_is_trap": cheapest["vendor_id"] != best["vendor_id"] and cheapest["check"]["verdict"] == "red"}


# --- requests --------------------------------------------------------------------------------

def _clean_request(body: dict) -> dict:
    kw = number(body.get("kw", 3), "system size", .5, 10)
    state = state_code(body.get("state", "DL"))
    pincode = str(body.get("pincode") or "").strip()
    if pincode and not re.fullmatch(r"[1-9]\d{5}", pincode):
        raise ValueError("PIN code must be 6 digits and cannot start with zero")
    return {"kw": round(kw, 1), "state": state, "discom": str(body.get("discom") or "")[:20], "pincode": pincode,
            "sanctioned_kw": body.get("sanctioned_kw"), "source": body.get("source", "web"),
            "sample": bool(body.get("sample"))}


def create_request(body: dict, wa_id: str | None = None, now: float | None = None) -> dict:
    now = now or time.time()
    req = _clean_request(body)
    rid = secrets.token_hex(16)
    band = knowledge.price_band(req["state"], req["kw"])
    if req["pincode"]:
        _put(f"GROUP#{req['state']}#{req['pincode']}", f"{int(now):010d}#{rid}", {"id": rid})
    g = group(req["state"], req["pincode"])
    req.update({"id": rid, "created": int(now), "status": "open", "wa_id": wa_id, "band": band, "group": g})
    _put(f"REQ#{rid}", "META", req)
    if wa_id:
        _put(f"USER#{wa_id}", rid, {"id": rid})
    _put(f"OPEN#{req['state']}", f"{int(now):010d}#{rid}", {"id": rid})
    discount = g["discount_pct"] if g else 0
    for v in demo_vendors():
        if serves(v, req["state"]):
            q = demo_quote(v, req, band, discount)
            _put(f"REQ#{rid}", f"QUOTE#{v['id']}", {"vendor_id": v["id"], "quote": q, "ready_at": now + v["reply_after_s"]})
    # Simulations must not inflate the live impact counters.
    return view(rid, now)


def view(rid: str, now: float | None = None, for_vendor: bool = False) -> dict:
    now = now or time.time()
    req = _get(f"REQ#{rid}", "META")
    if not req:
        raise KeyError(rid)
    all_quotes = _query(f"REQ#{rid}", prefix="QUOTE#")
    ready = []
    for row in all_quotes:
        if row["ready_at"] > now:
            continue
        v = _vendor(row["vendor_id"]) or {"id": row["vendor_id"], "name": row["quote"].get("vendor_name", "vendor")}
        ready.append({"vendor_id": v["id"], "vendor": {"name": v["name"], "demo": bool(v.get("demo")),
                                                        "verified": bool(v.get("verified")), "scorecard": scorecard(v)},
                      "quote": row["quote"], "check": assess(row["quote"], req["band"]), "ready_at": row["ready_at"]})
    ready.sort(key=lambda r: r["ready_at"])
    waiting = [r["ready_at"] - now for r in all_quotes if r["ready_at"] > now]
    public = {k: req[k] for k in ("id", "kw", "state", "discom", "pincode", "created", "status", "band", "group")}
    if req.get("chosen"):
        public["chosen"] = req["chosen"]
    out = {"request": public, "quotes": ready, "pending": len(waiting),
           "next_in": round(min(waiting), 1) if waiting else None,
           "recommendation": recommend(ready) if ready else None}
    if for_vendor:
        out["quotes"] = [{"vendor_id": r["vendor_id"]} for r in ready]
    return out


def choose(rid: str, vendor_id: str) -> dict:
    req = _get(f"REQ#{rid}", "META")
    if not req:
        raise KeyError(rid)
    row = _get(f"REQ#{rid}", f"QUOTE#{vendor_id}")
    if not row or row["ready_at"] > time.time():
        raise ValueError("that vendor hasn't quoted on this request")
    v = _vendor(vendor_id)
    req.update({"status": "chosen", "chosen": vendor_id, "chosen_at": int(time.time())})
    _put(f"REQ#{rid}", "META", req)
    if not v.get("demo"):
        knowledge.count(vendor_choices=1)
    return {"vendor": {"id": vendor_id, "name": v["name"], "demo": bool(v.get("demo"))}, "request": rid,
            "contact_shared": False, "website": v.get("website")}


def open_requests(state: str, vendor_id: str | None = None, limit: int = 20) -> list[dict]:
    """What a vendor sees: size, provider and pin code area, never the household.

    The website runs a sample comparison when someone opens Get quotes. Those samples stay out of
    a vendor's list while real requests exist; with none, the latest sample shows, labelled, so the
    vendor side can still be tried."""
    since = int(time.time()) - TTL_DAYS * 86400
    real, samples = [], []
    for row in reversed(_query(f"OPEN#{state}", since=since)):
        req = _get(f"REQ#{row['id']}", "META")
        if not req or req["status"] != "open":
            continue
        # requests from before the flag existed were the website's automatic samples
        sample = req.get("sample", not req.get("wa_id"))
        if sample and samples:
            continue
        quoted = {q["vendor_id"] for q in _query(f"REQ#{req['id']}", prefix="QUOTE#")}
        (samples if sample else real).append({
            "id": req["id"], "kw": req["kw"], "state": req["state"], "discom": req["discom"],
            "area": (req["pincode"][:3] + "xxx") if req["pincode"] else "", "created": req["created"],
            "quotes": len(quoted), "you_quoted": bool(vendor_id and vendor_id in quoted), "sample": bool(sample),
            # the group size helps a vendor price; the exact PIN code stays with the household
            "group": {k: v for k, v in (req.get("group") or {}).items() if k != "pincode"} or None})
        if len(real) >= limit:
            break
    return real or samples


def submit_quote(rid: str, vendor_name: str, raw: dict) -> dict:
    """A real vendor answers a request; they see exactly what the household will see."""
    req = _get(f"REQ#{rid}", "META")
    if not req:
        raise KeyError(rid)
    if req["status"] != "open":
        raise ValueError("this request is closed")
    v = register_vendor(vendor_name, req["state"])
    q = clean_quote(raw, v["name"], req["state"])
    check = assess(q, req["band"])
    _put(f"REQ#{rid}", f"QUOTE#{v['id']}", {"vendor_id": v["id"], "quote": q, "ready_at": time.time()})
    _put(f"VQ#{v['id']}", f"{int(time.time()):010d}#{rid}",
         {"per_kw": check["per_kw"], "typical": req["band"]["typical"], "verdict": check["verdict"]})
    return {"vendor": v, "check": check}


# --- WhatsApp --------------------------------------------------------------------------------

TEXT = {
    "en": {
        "ask_pin": "To ask vendors near you for quotes, reply with your 6-digit pin code. Your name and number stay private until you choose a vendor.",
        "waiting": "📨 Asked {n} vendors in your area for a {kw:g} kW quote. Reply QUOTES in a minute to compare them.",
        "group": "👥 {who} in {pincode} asked this month. At {needed}, vendors give a group price.",
        "group_on": "👥 {who} in {pincode} asked this month, so vendors are giving a group price: {pct}% off.",
        "homes": lambda n: "1 home" if n == 1 else f"{n} homes",
        "no_quotes_yet": "No quotes have arrived yet. Reply QUOTES in a minute to see them.",
        "head": "🧾 Quotes for {kw:g} kW, compared after subsidy:",
        "row": "{n}. {name}{demo}: {total}, you pay {net} after subsidy. {verdict}",
        "ok": "✅ No problems found.", "amber": "🟠 {k} thing{s} to negotiate.", "red": "🔴 {reason}",
        "red_dcr": "Imported panels: no subsidy.", "red_other": "Don't sign as it stands.",
        "demo": " (demo)",
        "best": "Best fit: {name}. Reply CHOOSE {n} to share your number with them, or CHOOSE with another number.",
        "trap": "The cheapest quote loses the subsidy, so it costs the most in the end.",
        "pending": "{n} more vendor{s} still quoting. Reply QUOTES again to refresh.",
        "none": "No quotes yet. Reply QUOTES again in a minute.",
        "chosen": "✅ Shared your request with {name}{demo}. They'll call you to fix a site visit.\nNext: when they upload your agreement on pmsuryaghar.gov.in, approve it there. Reply APPLY for the step-by-step plan.",
        "no_request": "You haven't asked for quotes yet. Send your bill first, then reply QUOTES.",
        "bad_choice": "Reply CHOOSE with the number of a quote from the list.",
    },
    "hi": {
        "ask_pin": "आस-पास के वेंडर से कोटेशन मँगाने के लिए अपना 6 अंकों का पिन कोड भेजें। वेंडर चुनने तक आपका नाम और नंबर निजी रहेगा।",
        "waiting": "📨 आपके इलाके के {n} वेंडर से {kw:g} kW का कोटेशन माँगा है। तुलना के लिए एक मिनट बाद QUOTES लिखें।",
        "group": "👥 इस महीने {pincode} से {who} कोटेशन माँगे। {needed} होने पर वेंडर ग्रुप रेट देते हैं।",
        "group_on": "👥 इस महीने {pincode} से {who} कोटेशन माँगे, इसलिए वेंडर ग्रुप रेट दे रहे हैं: {pct}% छूट।",
        "homes": lambda n: "1 घर ने" if n == 1 else f"{n} घरों ने",
        "no_quotes_yet": "अभी कोई कोटेशन नहीं आया है। एक मिनट बाद QUOTES लिखकर देखें।",
        "head": "🧾 {kw:g} kW के कोटेशन, सब्सिडी के बाद की तुलना:",
        "row": "{n}. {name}{demo}: {total}, सब्सिडी के बाद आप देंगे {net}। {verdict}",
        "ok": "✅ कोई दिक्कत नहीं।", "amber": "🟠 {k} बातों पर मोलभाव करें।", "red": "🔴 {reason}",
        "red_dcr": "विदेशी पैनल: सब्सिडी नहीं मिलेगी।", "red_other": "ऐसे ही साइन न करें।",
        "demo": " (डेमो)",
        "best": "सबसे सही: {name}। उन्हें अपना नंबर देने के लिए CHOOSE {n} लिखें, या किसी और नंबर के साथ CHOOSE।",
        "trap": "सबसे सस्ता कोटेशन सब्सिडी गँवा देता है, इसलिए आखिर में सबसे महँगा पड़ता है।",
        "pending": "{n} और वेंडर अभी कोटेशन बना रहे हैं। ताज़ा करने के लिए फिर QUOTES लिखें।",
        "none": "अभी कोई कोटेशन नहीं आया। एक मिनट बाद फिर QUOTES लिखें।",
        "chosen": "✅ आपका अनुरोध {name}{demo} को भेज दिया। वे साइट विज़िट के लिए कॉल करेंगे।\nआगे: जब वे pmsuryaghar.gov.in पर आपका एग्रीमेंट अपलोड करें, तो वहीं उसे मंज़ूर करें। कदम-दर-कदम प्लान के लिए APPLY लिखें।",
        "no_request": "आपने अभी कोटेशन नहीं माँगे। पहले बिल भेजें, फिर QUOTES लिखें।",
        "bad_choice": "सूची में से किसी कोटेशन का नंबर लिखकर CHOOSE भेजें।",
    },
}


def wa_started(view_: dict, lang: str) -> str:
    t = TEXT[lang if lang in TEXT else "en"]
    req = view_["request"]
    parts = [t["waiting"].format(n=len(view_["quotes"]) + view_["pending"], kw=req["kw"])]
    g = req.get("group")
    if g:
        who = t["homes"](g["homes"])
        parts.append(t["group_on"].format(who=who, pincode=g["pincode"], pct=g["discount_pct"]) if g["discount_pct"]
                     else t["group"].format(who=who, pincode=g["pincode"], needed=g["needed"]))
    return "\n".join(parts)


def wa_compare(view_: dict, lang: str) -> str:
    t = TEXT[lang if lang in TEXT else "en"]
    quotes = view_["quotes"]
    if not quotes:
        return t["none"]
    lines = [t["head"].format(kw=view_["request"]["kw"]), ""]
    for n, r in enumerate(quotes, start=1):
        c = r["check"]
        if c["verdict"] == "red":
            reason = t["red_dcr"] if any(f["code"] in ("not_dcr", "dcr_unstated") for f in c["flags"]) else t["red_other"]
            verdict = t["red"].format(reason=reason)
        elif c["verdict"] == "amber":
            k = sum(f["level"] == "amber" for f in c["flags"])
            verdict = t["amber"].format(k=k, s="" if k == 1 else "s")
        else:
            verdict = t["ok"]
        lines.append(t["row"].format(n=n, name=r["vendor"]["name"], demo=t["demo"] if r["vendor"]["demo"] else "",
                                     total=inr(c["total_rs"]), net=inr(c["net_rs"]), verdict=verdict))
    rec = view_.get("recommendation")
    if rec:
        best_n = next(n for n, r in enumerate(quotes, start=1) if r["vendor_id"] == rec["vendor_id"])
        lines += ["", t["best"].format(name=quotes[best_n - 1]["vendor"]["name"], n=best_n)]
        if rec["cheapest_is_trap"]:
            lines.append(t["trap"])
    if view_["pending"]:
        lines += ["", t["pending"].format(n=view_["pending"], s="" if view_["pending"] == 1 else "s")]
    return "\n".join(lines)


def wa_chosen(result: dict, lang: str) -> str:
    t = TEXT[lang if lang in TEXT else "en"]
    v = result["vendor"]
    reply = t["chosen"].format(name=v["name"].rstrip(" ."), demo=t["demo"] if v["demo"] else "")
    return reply + ("\n" + result["website"] if result.get("website") else "")


# The hackathon demo's vendors are fictional; say so wherever a reply could be mistaken for a real offer.
TEXT["en"].update(
    waiting="📨 Asked {n} vendors for a {kw:g} kW quote. Reply QUOTES in a minute to compare them. (Demo: these vendors are fictional.)",
    best="Best fit: {name}. Reply CHOOSE {n} to pick it.",
    chosen="✅ Saved {name}{demo} as your choice. Demo vendors aren't contacted; a real vendor would call you to fix a site visit.\n"
           "Next: when the vendor uploads your agreement on pmsuryaghar.gov.in, approve it there. Reply APPLY for the step-by-step plan, PASSPORT for the handover checks.",
)
TEXT["hi"].update(
    waiting="📨 {n} वेंडर से {kw:g} kW का कोटेशन माँगा है। तुलना के लिए एक मिनट बाद QUOTES लिखें। (डेमो: ये वेंडर काल्पनिक हैं।)",
    best="सबसे सही: {name}। चुनने के लिए CHOOSE {n} लिखें।",
    chosen="✅ {name}{demo} को आपकी पसंद के रूप में सेव किया। डेमो वेंडर से संपर्क नहीं होता; असली वेंडर साइट विज़िट के लिए कॉल करेगा।\n"
           "आगे: जब वेंडर pmsuryaghar.gov.in पर एग्रीमेंट अपलोड करे, वहीं मंज़ूर करें। कदम-दर-कदम प्लान के लिए APPLY, जाँच सूची के लिए PASSPORT लिखें।",
)
