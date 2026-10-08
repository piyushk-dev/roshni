"use strict";

const API = window.SURYA_API;
const MAX_EDGE_PX = 2000; // keeps bill text legible while staying far under the 6 MB Lambda payload limit
const SAMPLE = {
  discom: "BRPL",
  sanctioned_kw: 5,
  monthly_units: { 1: 380, 2: 350, 3: 420, 4: 560, 5: 720, 6: 780, 7: 690, 8: 610, 9: 560, 10: 470, 11: 390, 12: 400 },
};

const T = {
  en: {
    brand: "Surya Saathi",
    switchTo: "हिंदी",
    title: "Is rooftop solar worth it for your home?",
    sub: "Upload your electricity bill. In seconds you get an honest answer: the right size, the PM Surya Ghar subsidy, your EMI and the payback.",
    upload: "Upload a bill photo or PDF",
    uploadHint: "Delhi bills for now: BSES Rajdhani, BSES Yamuna, Tata Power-DDL",
    location: "📍 Use my location",
    locationOn: "📍 Using your location",
    locationOff: "📍 Location unavailable",
    roof: "Shade-free roof (sq ft, optional)",
    privacy: "Your name, address and consumer number are never read, and the bill isn't stored.",
    sample: "No bill handy? See a sample home →",
    reading: "Reading your bill…",
    analyzing: "Working out the numbers…",
    go: (kw) => `Go solar: ${kw} kW`,
    skip: "Honest answer: skip solar for now",
    billNow: (x) => `Your bill now: about ${x} a month.`,
    costAfter: "Cost after subsidy",
    costSub: (gross, subsidy) => `${gross} − ${subsidy} subsidy`,
    saves: "Saves every year",
    savesSub: (m) => `about ${m} a month`,
    payback: "Pays for itself in",
    years: (y) => `${y} years`,
    emi: "Loan EMI, 10 years",
    emiSub: (rate) => `at ${rate}%`,
    emiNote: (after) => `Or ${after} a month once the subsidy is used to prepay the loan.`,
    co2: (t) => `${t} t of CO₂ avoided every year`,
    chartTitle: "Your usage vs solar, month by month",
    usage: "Your usage",
    solar: "Solar",
    whyTitle: "Why this size",
    whySub: "Every size compared over 25 years. Net value today is 25 years of savings minus the cost, discounted at 8% a year. Bigger isn't always better.",
    cols: ["Size", "After subsidy", "Saves / yr", "Payback", "Net value today"],
    never: "never",
    readTitle: "What we read from your bill",
    provider: "Provider",
    load: "Sanctioned load",
    months: "Months of usage",
    amount: "This month's charges",
    conservative: "We use the lower of two sunlight datasets (PVGIS and NASA), so real savings should be at or above this.",
    again: "← Check another bill",
    error: "Something went wrong. Please try again.",
    tooBig: "That file is too big. Please send a photo or a PDF under 4 MB.",
    footer: "Built on AWS for WeMakeDevs × AWS Environmental Hacks",
    privacyLink: "Privacy",
    kw: (k) => `${k} kW`,
  },
  hi: {
    brand: "सूर्य साथी",
    switchTo: "English",
    title: "क्या आपके घर के लिए रूफ़टॉप सोलर फ़ायदेमंद है?",
    sub: "अपना बिजली बिल अपलोड करें। कुछ ही सेकंड में सच्चा जवाब पाएँ: सही साइज़, PM सूर्य घर सब्सिडी, आपकी EMI और कितने साल में लागत वसूल होगी।",
    upload: "बिल की फोटो या PDF अपलोड करें",
    uploadHint: "अभी दिल्ली के बिल: BSES राजधानी, BSES यमुना, टाटा पावर-DDL",
    location: "📍 मेरी लोकेशन लें",
    locationOn: "📍 आपकी लोकेशन ली गई",
    locationOff: "📍 लोकेशन नहीं मिली",
    roof: "छाया-रहित छत (वर्ग फुट, वैकल्पिक)",
    privacy: "आपका नाम, पता और कंज़्यूमर नंबर कभी नहीं पढ़ा जाता, और बिल सेव नहीं होता।",
    sample: "बिल पास नहीं है? एक सैंपल घर देखें →",
    reading: "आपका बिल पढ़ा जा रहा है…",
    analyzing: "हिसाब लगाया जा रहा है…",
    go: (kw) => `सोलर लगाएँ: ${kw} kW`,
    skip: "सच कहें तो: अभी सोलर न लगाएँ",
    billNow: (x) => `अभी आपका बिल: लगभग ${x} महीना।`,
    costAfter: "सब्सिडी के बाद लागत",
    costSub: (gross, subsidy) => `${gross} − ${subsidy} सब्सिडी`,
    saves: "हर साल बचत",
    savesSub: (m) => `लगभग ${m} महीना`,
    payback: "लागत वसूल",
    years: (y) => `${y} साल में`,
    emi: "लोन EMI, 10 साल",
    emiSub: (rate) => `${rate}% ब्याज`,
    emiNote: (after) => `या सब्सिडी से लोन घटाने पर ${after} महीना।`,
    co2: (t) => `हर साल ${t} टन CO₂ कम`,
    chartTitle: "हर महीने: आपकी खपत बनाम सोलर",
    usage: "आपकी खपत",
    solar: "सोलर",
    whyTitle: "यही साइज़ क्यों",
    whySub: "हर साइज़ की 25 साल की तुलना। आज का कुल फ़ायदा = 25 साल की बचत में से लागत घटाकर, 8% सालाना डिस्काउंट के साथ। बड़ा हमेशा बेहतर नहीं होता।",
    cols: ["साइज़", "सब्सिडी के बाद", "सालाना बचत", "वसूल", "आज का कुल फ़ायदा"],
    never: "कभी नहीं",
    readTitle: "आपके बिल से हमने क्या पढ़ा",
    provider: "बिजली कंपनी",
    load: "स्वीकृत लोड",
    months: "कितने महीनों की खपत",
    amount: "इस महीने का बिल",
    conservative: "हम धूप के दो डेटा (PVGIS और NASA) में से कम वाला लेते हैं, इसलिए असली बचत इससे कम नहीं होनी चाहिए।",
    again: "← दूसरा बिल जाँचें",
    error: "कुछ गड़बड़ हो गई। कृपया फिर कोशिश करें।",
    tooBig: "फ़ाइल बहुत बड़ी है। कृपया 4 MB से छोटी फोटो या PDF भेजें।",
    footer: "AWS पर बना, WeMakeDevs × AWS Environmental Hacks के लिए",
    privacyLink: "प्राइवेसी",
    kw: (k) => `${k} kW`,
  },
};

const $ = (id) => document.getElementById(id);
const state = { lang: initialLang(), lat: null, lon: null, last: null, lastBody: null };

function initialLang() {
  try {
    const saved = localStorage.getItem("lang");
    if (saved === "en" || saved === "hi") return saved;
  } catch (_) { /* storage blocked: fall through */ }
  return (navigator.language || "").toLowerCase().startsWith("hi") ? "hi" : "en";
}

const t = (key, ...args) => {
  const v = T[state.lang][key];
  return typeof v === "function" ? v(...args) : v;
};
const rupees = (x) => "₹" + Math.round(x).toLocaleString("en-IN");
const hundreds = (x) => rupees(Math.round(x / 100) * 100);

function applyLang() {
  document.documentElement.lang = state.lang;
  document.querySelectorAll("[data-t]").forEach((el) => { el.textContent = t(el.dataset.t); });
  $("lang").textContent = t("switchTo");
  if (state.lat !== null) $("locate").textContent = t("locationOn");
  if (state.last) render(state.last);
}

function show(id) {
  for (const s of ["start", "busy", "problem", "result"]) $(s).hidden = s !== id;
  window.scrollTo({ top: 0 });
}

async function post(path, body) {
  const r = await fetch(API + path, { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify({ ...body, lang: state.lang }) });
  const data = await r.json().catch(() => ({}));
  if (!r.ok) throw new Error(data.error || t("error"));
  return data;
}

function extras() {
  const out = {};
  if (state.lat !== null) Object.assign(out, { lat: state.lat, lon: state.lon });
  const roof = parseFloat($("roof").value);
  if (roof > 0) out.roof_sqft = roof;
  return out;
}

async function prepare(file) {
  if (file.type === "application/pdf") {
    if (file.size > 4e6) throw new Error(t("tooBig"));
    return { b64: await toBase64(file), type: "application/pdf" };
  }
  try {
    const img = await createImageBitmap(file);
    const scale = Math.min(1, MAX_EDGE_PX / Math.max(img.width, img.height));
    const canvas = document.createElement("canvas");
    canvas.width = Math.round(img.width * scale);
    canvas.height = Math.round(img.height * scale);
    canvas.getContext("2d").drawImage(img, 0, 0, canvas.width, canvas.height);
    const blob = await new Promise((ok) => canvas.toBlob(ok, "image/jpeg", 0.85));
    return { b64: await toBase64(blob), type: "image/jpeg" };
  } catch (_) {
    if (file.size > 4e6) throw new Error(t("tooBig"));
    return { b64: await toBase64(file), type: file.type || "image/jpeg" };
  }
}

function toBase64(blob) {
  return new Promise((ok, fail) => {
    const r = new FileReader();
    r.onload = () => ok(String(r.result).split(",")[1]);
    r.onerror = fail;
    r.readAsDataURL(blob);
  });
}

async function run(label, work) {
  $("busy-text").textContent = t(label);
  show("busy");
  try {
    state.last = await work();
    render(state.last);
    show("result");
  } catch (e) {
    $("problem-text").textContent = e.message || t("error");
    show("problem");
  }
}

function render(data) {
  const a = data.analysis;
  const o = a.recommended;
  const v = $("verdict");
  v.className = "verdict " + a.verdict;
  v.innerHTML = "";
  const big = document.createElement("div");
  big.className = "big";
  big.textContent = a.verdict === "go" ? t("go", o.kw) : t("skip");
  const why = document.createElement("p");
  why.textContent = a.verdict === "go" ? data.reason : `${data.reason} ${t("billNow", hundreds(a.bill_now_rs_per_year / 12))}`;
  v.append(big, why);

  const tiles = $("tiles");
  tiles.innerHTML = "";
  $("emi-note").textContent = "";
  if (o) {
    const high = Math.max(o.savings_rs, o.savings_optimistic_rs);
    tiles.append(
      tile(t("costAfter"), rupees(o.net_cost), t("costSub", rupees(o.gross_cost), rupees(o.subsidy))),
      tile(t("saves"), `${hundreds(o.savings_rs)}–${hundreds(high).slice(1)}`, t("savesSub", hundreds(o.savings_rs / 12))),
      tile(t("payback"), t("years", o.payback_years.toFixed(1)), t("co2", o.co2_t_per_year.toFixed(1))),
      tile(t("emi"), rupees(o.emi_rs), t("emiSub", o.loan_rate_pct)),
    );
    $("emi-note").textContent = t("emiNote", rupees(o.emi_after_subsidy_rs));
  }

  $("chart").innerHTML = chart(a.usage_by_month, o ? a.yield_by_month.map((y) => y * o.kw) : null);

  const notes = $("notes");
  notes.innerHTML = "";
  for (const n of data.notes) {
    const li = document.createElement("li");
    li.textContent = n;
    notes.append(li);
  }

  optionsTable(a);
  billRead(data.bill);
}

function tile(label, value, sub) {
  const d = document.createElement("div");
  d.className = "tile";
  for (const [cls, text] of [["label", label], ["value", value], ["sub", sub]]) {
    const s = document.createElement("div");
    s.className = cls;
    s.textContent = text;
    d.append(s);
  }
  return d;
}

function chart(usage, solar) {
  const W = 360, H = 170, top = 10, bottom = 22, left = 4;
  const max = Math.max(...usage, ...(solar || [0])) * 1.08;
  const slot = (W - left) / 12;
  const bw = solar ? slot * 0.36 : slot * 0.6;
  const y = (v) => top + (H - top - bottom) * (1 - v / max);
  const fmt = new Intl.DateTimeFormat(state.lang === "hi" ? "hi-IN" : "en-IN", { month: "narrow" });
  let bars = "";
  for (let m = 0; m < 12; m++) {
    const x = left + m * slot + slot * 0.12;
    const label = fmt.format(new Date(2026, m, 1));
    bars += `<rect x="${x.toFixed(1)}" y="${y(usage[m]).toFixed(1)}" width="${bw.toFixed(1)}" height="${(H - bottom - y(usage[m])).toFixed(1)}" rx="2" fill="var(--usage)"><title>${Math.round(usage[m])} kWh</title></rect>`;
    if (solar) {
      bars += `<rect x="${(x + bw + 1).toFixed(1)}" y="${y(solar[m]).toFixed(1)}" width="${bw.toFixed(1)}" height="${(H - bottom - y(solar[m])).toFixed(1)}" rx="2" fill="var(--sun)"><title>${Math.round(solar[m])} kWh</title></rect>`;
    }
    bars += `<text x="${(x + (solar ? bw : bw / 2)).toFixed(1)}" y="${H - 6}" text-anchor="middle">${label}</text>`;
  }
  return `<svg viewBox="0 0 ${W} ${H}" role="img" aria-label="${t("chartTitle")}"><line x1="0" x2="${W}" y1="${H - bottom}" y2="${H - bottom}" stroke="var(--line)"/>${bars}</svg>`;
}

function optionsTable(a) {
  const table = $("options");
  table.innerHTML = "";
  const head = table.createTHead().insertRow();
  for (const c of t("cols")) {
    const th = document.createElement("th");
    th.textContent = c;
    head.append(th);
  }
  const body = table.createTBody();
  for (const o of a.options) {
    const row = body.insertRow();
    if (a.recommended && o.kw === a.recommended.kw) row.className = "best";
    const cells = [t("kw", o.kw), rupees(o.net_cost), rupees(o.savings_rs), o.payback_years ? t("years", o.payback_years.toFixed(1)) : t("never"), rupees(o.npv_rs)];
    for (const c of cells) row.insertCell().textContent = c;
  }
}

function billRead(bill) {
  $("read").hidden = !bill;
  if (!bill) return;
  const dl = $("read-list");
  dl.innerHTML = "";
  const rows = [
    [t("provider"), bill.discom_name || bill.discom],
    [t("load"), bill.sanctioned_load_kw ? t("kw", bill.sanctioned_load_kw) : "—"],
    [t("months"), String(Object.keys(bill.monthly_units || {}).length)],
    [t("amount"), bill.amount_rs ? rupees(bill.amount_rs) : "—"],
  ];
  for (const [k, val] of rows) {
    const dt = document.createElement("dt");
    dt.textContent = k;
    const dd = document.createElement("dd");
    dd.textContent = val;
    dl.append(dt, dd);
  }
}

$("file").addEventListener("change", (e) => {
  const file = e.target.files[0];
  e.target.value = "";
  if (!file) return;
  run("reading", async () => {
    const { b64, type } = await prepare(file);
    const data = await post("/bill", { file_base64: b64, media_type: type, ...extras() });
    const b = data.bill;
    state.lastBody = { discom: b.discom, sanctioned_kw: b.sanctioned_load_kw, monthly_units: b.monthly_units, last_bill_rs: b.amount_rs, last_bill_units: b.units_billed, ...extras() };
    return data;
  });
});

$("sample").addEventListener("click", () => {
  state.lastBody = { ...SAMPLE, ...extras() };
  run("analyzing", () => post("/analyze", state.lastBody));
});

$("locate").addEventListener("click", () => {
  if (!navigator.geolocation) return;
  navigator.geolocation.getCurrentPosition(
    (p) => {
      // two decimals (~1 km) is plenty for sunlight and keeps the exact address private
      state.lat = Math.round(p.coords.latitude * 100) / 100;
      state.lon = Math.round(p.coords.longitude * 100) / 100;
      $("locate").textContent = t("locationOn");
    },
    () => { $("locate").textContent = t("locationOff"); },
    { timeout: 10000 },
  );
});

$("lang").addEventListener("click", () => {
  state.lang = state.lang === "en" ? "hi" : "en";
  try { localStorage.setItem("lang", state.lang); } catch (_) { /* fine without it */ }
  applyLang();
  // reasons and notes come from the API in the chosen language; re-run the sums, not the bill reading
  if (state.last && state.lastBody) {
    const bill = state.last.bill;
    run("analyzing", async () => ({ ...(await post("/analyze", state.lastBody)), bill }));
  }
});

document.querySelectorAll(".again").forEach((b) => b.addEventListener("click", () => { state.last = null; show("start"); }));
$("privacy-link").href = API + "/privacy";
applyLang();
