"""Knowledge that keeps itself current.

- Every bill read leaves a tariff observation for its provider (no personal data).
- Every quote checked leaves a ₹/kW price observation for its state.
- Facts (state schemes, deadlines, rates) start from data/facts.json; people confirm them or
  report changes, and a weekly watcher flags facts whose official source page changed.
- Running counters feed the live impact numbers.

All of it lives in one DynamoDB table (pk, sk). Without KNOWLEDGE_TABLE every function is a no-op
that returns the seed data, so tests and local runs need no AWS.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import time
import urllib.request
import uuid
from decimal import Decimal
from statistics import median

from . import load_data
from .scheme import SCHEME

MIN_QUOTES_FOR_LIVE_PRICE = 5
PRICE_WINDOW_DAYS = 180
REPORTS_TO_FLAG = 3
TTL_DAYS = 730
_table = None


def _t():
    global _table
    if not os.environ.get("KNOWLEDGE_TABLE"):
        return None
    if _table is None:
        import boto3

        _table = boto3.resource("dynamodb").Table(os.environ["KNOWLEDGE_TABLE"])
    return _table


def _put(pk: str, data: dict) -> None:
    t = _t()
    if t:
        now = int(time.time())
        t.put_item(Item={"pk": pk, "sk": f"{now}#{uuid.uuid4().hex[:8]}", "data": json.dumps(data), "expires": now + TTL_DAYS * 86400})


def _recent(pk: str, days: int, limit: int = 100) -> list[dict]:
    t = _t()
    if not t:
        return []
    from boto3.dynamodb.conditions import Key

    since = f"{int(time.time()) - days * 86400}"
    items = t.query(KeyConditionExpression=Key("pk").eq(pk) & Key("sk").gte(since), ScanIndexForward=False, Limit=limit)["Items"]
    return [json.loads(i["data"]) for i in items]


def slug(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", (name or "unknown").lower()).strip("-")


# --- bills teach tariffs -------------------------------------------------------------------

def record_tariff(state: str, provider: str, slabs: list, fixed_per_kw: float | None, multiplier: float | None, month: str | None) -> None:
    _put(f"TARIFF#{state}#{slug(provider)}", {"slabs": slabs, "fixed_per_kw": fixed_per_kw, "multiplier": multiplier, "month": month})


def learned_tariff(state: str, provider: str) -> dict | None:
    """The most recent tariff seen on a bill from this provider, with how many bills taught it."""
    seen = _recent(f"TARIFF#{state}#{slug(provider)}", days=120, limit=20)
    if not seen:
        return None
    return {**seen[0], "bills": len(seen)}


# --- quotes teach prices -------------------------------------------------------------------

def record_price(state: str, kw: float, per_kw_incl_gst: float) -> None:
    if kw and 20000 <= per_kw_incl_gst <= 150000:  # outside this it's a misread, not a price
        _put(f"PRICE#{state}", {"kw": kw, "per_kw": round(per_kw_incl_gst)})


def price_band(state: str, kw: float) -> dict:
    """Live band from recent quotes in the state once there are enough, otherwise the seed band."""
    seed = SCHEME["cost_rs_per_kw"]["upto_3kw" if kw <= 3 else "above_3kw"]
    prices = sorted(p["per_kw"] for p in _recent(f"PRICE#{state}", PRICE_WINDOW_DAYS) if (p["kw"] <= 3) == (kw <= 3))
    if len(prices) < MIN_QUOTES_FOR_LIVE_PRICE:
        return {**seed, "quotes": len(prices), "live": False}
    q = lambda f: prices[min(len(prices) - 1, int(f * len(prices)))]
    return {"low": q(0.25), "typical": median(prices), "high": q(0.75), "quotes": len(prices), "live": True}


# --- people verify facts -------------------------------------------------------------------

def _fact_state(fact_id: str) -> dict:
    t = _t()
    item = t.get_item(Key={"pk": f"FACT#{fact_id}", "sk": "state"}).get("Item") if t else None
    return json.loads(item["data"]) if item else {}


def _save_fact_state(fact_id: str, state: dict) -> None:
    t = _t()
    if t:
        t.put_item(Item={"pk": f"FACT#{fact_id}", "sk": "state", "data": json.dumps(state)})


def facts(scope: str | None = None) -> list[dict]:
    out = []
    for f in load_data("facts.json"):
        if scope and f["scope"] not in ("IN", scope):
            continue
        st = _fact_state(f["id"])
        reports = st.get("reports", [])
        status = st.get("status") or ("reported_changed" if len(reports) >= REPORTS_TO_FLAG else "current")
        out.append({**f, "confirmations": st.get("confirmations", 0), "last_confirmed": st.get("last_confirmed", f["verified"]),
                    "reports": reports[-5:], "report_count": len(reports), "status": status,
                    "source_changed_on": st.get("source_changed_on")})
    return out


def confirm(fact_id: str) -> dict:
    st = _fact_state(fact_id)
    st["confirmations"] = st.get("confirmations", 0) + 1
    st["last_confirmed"] = time.strftime("%Y-%m-%d")
    _save_fact_state(fact_id, st)
    return st


def report(fact_id: str, value: str, evidence: str = "") -> dict:
    st = _fact_state(fact_id)
    st.setdefault("reports", []).append({"value": value[:300], "evidence": evidence[:500], "on": time.strftime("%Y-%m-%d")})
    _save_fact_state(fact_id, st)
    return st


def watch(fetch=None) -> list[str]:
    """Weekly: re-read every official source; mark the facts whose page changed. Returns their ids."""
    fetch = fetch or (lambda url: urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "surya-saathi-watcher"}), timeout=20).read())
    changed = []
    for f in load_data("facts.json"):
        if not f.get("official"):
            continue
        try:
            text = re.sub(rb"\s+", b" ", re.sub(rb"<[^>]+>", b" ", fetch(f["source"])))
        except Exception:
            continue
        digest = hashlib.sha256(text).hexdigest()
        st = _fact_state(f["id"])
        if st.get("source_hash") and st["source_hash"] != digest:
            st["status"] = "source_changed"
            st["source_changed_on"] = time.strftime("%Y-%m-%d")
            changed.append(f["id"])
        st["source_hash"] = digest
        _save_fact_state(f["id"], st)
    return changed


# --- journeys teach how long each step really takes -------------------------------------------

def record_stage(provider: str, stage: str, days: float) -> None:
    _put(f"STAGE#{slug(provider)}#{stage}", {"provider": provider, "stage": stage, "days": round(days, 1)})


def stage_times() -> list[dict]:
    """Median days per provider and stage, from households that finished the step."""
    t = _t()
    if not t:
        return []
    from boto3.dynamodb.conditions import Attr

    items = t.scan(FilterExpression=Attr("pk").begins_with("STAGE#"))["Items"]
    groups: dict[tuple[str, str], list[float]] = {}
    for item in items:
        d = json.loads(item["data"])
        groups.setdefault((d["provider"], d["stage"]), []).append(d["days"])
    return [{"provider": p, "stage": s, "median_days": median(v), "households": len(v)} for (p, s), v in sorted(groups.items())]


# --- live impact ---------------------------------------------------------------------------

def count(**increments: float) -> None:
    t = _t()
    if t and increments:
        names = {f"#{k}": k for k in increments}
        values = {f":{k}": Decimal(str(round(v, 2))) for k, v in increments.items()}
        t.update_item(Key={"pk": "STATS", "sk": "all"}, UpdateExpression="ADD " + ", ".join(f"#{k} :{k}" for k in increments),
                      ExpressionAttributeNames=names, ExpressionAttributeValues=values)


def stats() -> dict:
    t = _t()
    item = t.get_item(Key={"pk": "STATS", "sk": "all"}).get("Item") if t else None
    return {k: float(v) for k, v in (item or {}).items() if k not in ("pk", "sk")}


def watch_handler(event: dict, context) -> dict:
    return {"source_changed": watch()}
