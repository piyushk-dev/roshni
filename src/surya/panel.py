"""Is this the panel you paid for? Read a panel's back label and check it against the subsidy rules.

Under PM Surya Ghar the subsidy needs panels with Indian cells and an Indian module (DCR), and the
installer's 16-digit DCR certificate must list the serial numbers on the roof. Vendors have swapped
in imported panels after quoting, and the portal now rejects duplicate serials. A photo of each
label is checked for an imported origin, a missing DCR mark, a wattage that doesn't match the quote,
and a serial already checked at another home. Serials are kept only as hashes.
"""

from __future__ import annotations

import hashlib
import json
import re
import time

from . import bill_reader, knowledge

SEEN_TTL_DAYS = 730
_mem_seen: dict[str, str] = {}

PROMPT = (
    "This should be a photo of the back label (nameplate sticker) of a solar PV module. Read it exactly as printed. "
    "Never guess a value that is not visible. If the image is not a module's label, set is_panel_label to false. "
    "Record what you read with record_panel_label."
)
TOOL = {"toolSpec": {"name": "record_panel_label", "description": "Record a solar module's nameplate.", "inputSchema": {"json": {
    "type": "object",
    "properties": {
        "is_panel_label": {"type": "boolean"},
        "manufacturer": {"type": "string"},
        "model": {"type": "string"},
        "pmax_w": {"type": "number", "description": "rated maximum power (Pmax) in watts"},
        "serial": {"type": "string", "description": "serial number exactly as printed"},
        "dcr_marked": {"type": "string", "enum": ["yes", "no", "not_visible"],
                       "description": "yes only if the label says DCR or Domestic Content Requirement"},
        "origin": {"type": "string", "description": "country where the module was made, as printed; empty if not printed"},
        "cell_origin": {"type": "string", "description": "country of the cells, if printed"},
    },
    "required": ["is_panel_label"]}}}}

TEXT = {
    "en": {
        "head": "🔍 Panel label: {name}, {pmax} W, serial {serial}",
        "red": "🔴 Don't accept these panels yet.", "amber": "🟠 Check this before the final payment.",
        "ok": "✅ This label fits the subsidy rules.",
        "not_label": "This doesn't look like a panel's back label. Photograph the sticker on the back of a panel, up close.",
        "imported": "The label says made in {origin}. Imported panels don't get the PM Surya Ghar subsidy.",
        "cells_imported": "The cells are from {origin}. The subsidy needs Indian cells as well as an Indian module.",
        "dcr_missing": "The label doesn't show DCR. Ask the installer for the 16-digit DCR certificate that lists this serial.",
        "watt_mismatch": "The label says {pmax:g} W, but your quote says {expect:g} W per panel.",
        "serial_missing": "No serial number is readable. Photograph the label again, closer.",
        "serial_seen": "This serial was already checked at another home. The portal rejects duplicate serials, so ask the installer before you pay.",
        "next": "Next: match this serial with your DCR certificate and the invoice, and check the model on MNRE's ALMM list.",
    },
    "hi": {
        "head": "🔍 पैनल लेबल: {name}, {pmax} W, सीरियल {serial}",
        "red": "🔴 अभी ये पैनल स्वीकार न करें।", "amber": "🟠 आख़िरी भुगतान से पहले यह जाँच लें।",
        "ok": "✅ यह लेबल सब्सिडी के नियमों पर खरा है।",
        "not_label": "यह पैनल के पीछे का लेबल नहीं लगता। पैनल के पीछे लगे स्टिकर की पास से फोटो लें।",
        "imported": "लेबल पर {origin} में बना लिखा है। विदेशी पैनल पर PM सूर्य घर सब्सिडी नहीं मिलती।",
        "cells_imported": "सेल {origin} के हैं। सब्सिडी के लिए मॉड्यूल के साथ सेल भी भारत में बने होने चाहिए।",
        "dcr_missing": "लेबल पर DCR नहीं दिखता। इंस्टॉलर से 16 अंकों का DCR प्रमाणपत्र माँगें जिसमें यह सीरियल हो।",
        "watt_mismatch": "लेबल पर {pmax:g} W है, पर आपके कोटेशन में हर पैनल {expect:g} W का है।",
        "serial_missing": "सीरियल नंबर पढ़ा नहीं जा सका। लेबल की फोटो फिर से, पास से लें।",
        "serial_seen": "यह सीरियल पहले किसी और घर पर जाँचा जा चुका है। पोर्टल एक जैसे सीरियल नामंज़ूर करता है, इसलिए भुगतान से पहले इंस्टॉलर से पूछें।",
        "next": "आगे: यह सीरियल DCR प्रमाणपत्र और बिल से मिलाएँ, और मॉडल MNRE की ALMM सूची में देखें।",
    },
}
LEVEL = {"not_label": "red", "imported": "red", "cells_imported": "red", "serial_seen": "red",
         "dcr_missing": "amber", "watt_mismatch": "amber", "serial_missing": "amber"}


BLANK = {"", "null", "none", "n/a", "na", "-", "unknown", "not visible", "not_visible", "not printed", "not stated"}


def clean(f: dict) -> dict:
    """Models sometimes write "null" or "not visible" for a missing field; treat those as missing."""
    out = {}
    for k, v in (f or {}).items():
        if isinstance(v, str) and k != "dcr_marked":
            v = v.strip()
            if v.lower() in BLANK:
                continue
        out[k] = v
    return out


def read_label(data: bytes, media_type: str, client=None) -> tuple[dict, str]:
    import boto3

    client = client or boto3.client("bedrock-runtime", region_name=bill_reader.REGION)
    fields, model = bill_reader.call_first_enabled(client, bill_reader.tool_request(data, media_type, PROMPT, TOOL, max_tokens=800))
    return clean(fields), model


def normal_serial(serial: str | None) -> str:
    return re.sub(r"[^A-Z0-9]", "", (serial or "").upper())


def seen_elsewhere(serial: str, owner: str | None) -> bool:
    """Record this serial for this home; True when a different home already checked the same serial."""
    key = hashlib.sha256(normal_serial(serial).encode()).hexdigest()
    who = hashlib.sha256((owner or "anonymous").encode()).hexdigest()[:16]
    t = knowledge._t()
    if not t:
        return _mem_seen.setdefault(key, who) != who
    from botocore.exceptions import ClientError

    item = {"pk": f"SERIAL#{key}", "sk": "first", "data": json.dumps({"owner": who}),
            "expires": int(time.time()) + SEEN_TTL_DAYS * 86400}
    try:
        t.put_item(Item=item, ConditionExpression="attribute_not_exists(pk)")
        return False
    except ClientError as e:
        if e.response["Error"]["Code"] != "ConditionalCheckFailedException":
            raise
    first = t.get_item(Key={"pk": f"SERIAL#{key}", "sk": "first"}).get("Item")
    return bool(first) and json.loads(first["data"]).get("owner") != who


def check(f: dict, expect_watt: float | None = None, owner: str | None = None, sample: bool = False) -> list[dict]:
    if not f.get("is_panel_label"):
        return [{"code": "not_label", "level": "red", "values": {}}]
    flags = []

    def add(code, **values):
        flags.append({"code": code, "level": LEVEL[code], "values": values})

    origin, cells = (f.get("origin") or "").strip(), (f.get("cell_origin") or "").strip()
    if origin and "india" not in origin.lower():
        add("imported", origin=origin)
    if cells and "india" not in cells.lower():
        add("cells_imported", origin=cells)
    if f.get("dcr_marked") != "yes":
        add("dcr_missing")
    pmax = f.get("pmax_w")
    if expect_watt and pmax and abs(pmax - float(expect_watt)) > 5:
        add("watt_mismatch", pmax=pmax, expect=float(expect_watt))
    serial = normal_serial(f.get("serial"))
    if not serial:
        add("serial_missing")
    elif not sample and seen_elsewhere(serial, owner):  # the bundled samples never record a serial
        add("serial_seen")
    return flags


def verdict(flags: list[dict]) -> str:
    levels = {f["level"] for f in flags}
    return "red" if "red" in levels else "amber" if "amber" in levels else "ok"


def render(f: dict, flags: list[dict], lang: str = "en") -> dict:
    t = TEXT[lang if lang in TEXT else "en"]
    v = verdict(flags)
    name = " ".join(x for x in (f.get("manufacturer"), f.get("model")) if x) or "panel"
    head = t["head"].format(name=name, pmax=f"{f['pmax_w']:g}" if f.get("pmax_w") else "?", serial=f.get("serial") or "?")
    order = {"red": 0, "amber": 1}
    lines = [t[x["code"]].format(**x["values"]) for x in sorted(flags, key=lambda x: order[x["level"]])]
    return {"verdict": v, "title": t[v], "head": head if f.get("is_panel_label") else "", "lines": lines,
            "levels": [x["level"] for x in sorted(flags, key=lambda x: order[x["level"]])],
            "next": t["next"] if f.get("is_panel_label") else ""}


def message(f: dict, flags: list[dict], lang: str = "en") -> str:
    r = render(f, flags, lang)
    parts = [p for p in (r["head"], r["title"]) if p] + [f"• {x}" for x in r["lines"]]
    if r["next"]:
        parts += ["", r["next"]]
    return "\n".join(parts)
