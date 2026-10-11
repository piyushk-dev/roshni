"use strict";
// My solar: the app for a home's panels. Data comes from the simulated inverter cloud at /plant.

(() => {
  const API = window.SURYA_API || "/api";
  const $ = (id) => document.getElementById(id);
  const C = { solar: "#c27c00", clean: "#3f6fc4", save: "#22905a", ink: "#14233f", muted: "#6b7890", line: "#e4e9f0", grid: "#eef1f5" };

  const STR = {
    en: {
      appName: "My solar", tToday: "Today", tAhead: "Forecast", tMoney: "Savings", tCare: "Care",
      site: (kw, place, model, time) => `${kw} kW in ${place}. Simulated inverter ${model}, updated ${time}.`,
      nowAt: (time) => `Now, ${time}`, at: (time) => `At ${time}`, sunrise: (x) => `Sunrise ${x}`, sunset: (x) => `Sunset ${x}`,
      madeToday: "units made today",
      producing: (pct) => `Producing, ${pct}% of capacity`, forecastAt: (pct) => `Forecast, ${pct}% of capacity`,
      night: (u) => `Asleep for the night. Today: ${u} units`, idle: "Not producing",
      st_overvoltage: "Paused: grid voltage too high", st_undervoltage: "Paused: supply voltage too low",
      st_outage: "Off: there's a power cut", st_offline: "Producing, but the monitoring is offline",
      liveWhy: "What this means",
      flowTitle: "Where your power is going", fSolar: "from the panels", fHome: "used at home",
      toGrid: "sent to the grid", fromGrid: "bought from the grid", gridIdle: "grid",
      todayTitle: "Today's output", scrubHint: "Touch the curve to see any moment of the day.",
      kYours: "Your panels", kAhead: "Forecast", kClean: "If the panels were clean",
      cSoFar: "units so far", cSaved: "saved today", cDay: "units expected today",
      splitLine: (self, out) => `Of today's solar, ${self} units were used at home and ${out} went to the grid.`,
      splitSelf: "used at home", splitOut: "sent to the grid", splitBuy: (u) => `${u} units bought from the grid so far`,
      dustTitle: (pct) => `Dust is taking ${pct}% of your output`, dustBody: (u, rs) => `About ${u} units today, worth ₹${rs}. Rain or a clean brings it back.`,
      dustClean: "Panels are clean", dustCleanBody: "No dust loss to speak of today.",
      eventsTitle: "Inverter events", eventsSub: "What happened this week, in plain words.", noEvents: "Nothing unusual this week.",
      howToFix: "What to do", evidence: "For the installer or the DISCOM", copy: "Copy", sendWa: "Send on WhatsApp", copied: "Copied",
      historyTitle: "The last 14 days", historyAvg: (u) => `Average ${u} units a day`,
      aheadFoot: "Forecast from Open-Meteo's sunlight, cloud and temperature for your roof, less the dust building up on the panels.",
      rainWash: "Rain may wash the panels", dustLevel: { clear: "Low dust", dusty: "Dusty", high: "Very dusty" },
      sky: { sun: "Sunny", part: "Partly cloudy", cloud: "Cloudy", haze: "Hazy", rain: "Rain", storm: "Storms" },
      monthTitle: "Saved this month", monthUnits: (u) => `${u} units made this month`,
      onTrack: (pct, p, proj) => `On track for ${proj} units, ${pct}% of the ${p} promised.`,
      below: (pct, p, proj) => `Heading for ${proj} units, ${pct}% of the ${p} promised. Check it with the vendor.`,
      noPromise: "Add the vendor's promised monthly units in settings to check them.",
      lifeRs: "saved since installation", lifeUnits: "units made", lifeCo2: "tonnes of CO₂ avoided", lifeTrees: "trees would take a year to soak up that CO₂",
      yearsTitle: "The next 25 years", yearsSub: "Panels lose about half a percent a year. The warranty promises at least 80% at year 25.",
      yearTip: (y, u, s) => `${y}: ${u} units, ${s}% of year one`, floor: "Warranty floor",
      inverterNote: "Most inverters need replacing once, around year 10 to 12. Put aside about ₹25,000 for it.",
      cleanTitle: { rain: (d) => `Rain on ${d} should wash the panels`, clean: (d) => `Clean on ${d}, after the dust settles`,
        wait: "Dust stays high this week", fine: "Low dust: clean as usual" },
      cleanBody: { rain: "Skip the bucket this time.", clean: "Plain water, early morning; never spray the inverter.",
        wait: "Wait for a clear day, or the panels just get dusty again.", fine: "Every two to three weeks is enough in this weather." },
      lastCleaned: (n) => `Last cleaned ${n} day${n === 1 ? "" : "s"} ago.`, cleanedToday: "I cleaned them today", markedClean: "Marked as cleaned today",
      calTitle: "Coming up", inDays: (n) => (n <= 0 ? "today" : n === 1 ? "tomorrow" : n < 60 ? `in ${n} days` : n < 730 ? `in ${Math.round(n / 30)} months` : `in ${Math.round(n / 365)} years`),
      cal: { bill_check: "Check the bill against the app", earthing: "Check the earthing pit and isolators", inspection: "Yearly inspection by the installer",
        workmanship_warranty: "Workmanship warranty ends" },
      warrantyTitle: "Warranties", w: [["Panel output", 25], ["Panel product", 12], ["Inverter", 8], ["Workmanship", 5]],
      wEnds: (y) => `to ${y}`,
      helpTitle: "Help", helpSupport: "Something wrong? Prepare a request", helpBill: "Read the first bill after solar",
      helpPanel: "Check a panel's label", helpConnect: "Connect your real inverter",
      install: "Install the app",
      settingsTitle: "Your system", cancel: "Cancel", save: "Save", setupTitle: "Set up your panels",
      setupNote: "These shape how your panels are modelled: size, place, install date and what the vendor promised. Change them any time.",
      sKw: "System size (kW)", sPlace: "Area and city", sInstalled: "Installed on", sCleaned: "Last cleaned on",
      sUse: "Electricity used a month (units)", sPromised: "Vendor's promised units a month", sRate: "Your rate (₹ a unit)", sLang: "Language",
      settingsNote: "Saved on this phone only. Location is kept to about a kilometre.", placeNotFound: "Couldn't find that place; kept the old one.",
      connectTitle: "Connect your real inverter",
      connectBody: "Each brand has its own cloud, and reading it needs the installer to share access. Until then, a simulator stands in: it follows the real sunlight, cloud, temperature and dust where you live.",
      connectWhat: "What connecting needs", connectSteps: "The brand of your inverter, the logger's serial number, and the installer adding Surya Saathi to the plant in the brand's app.",
      down: "Couldn't reach the panels' cloud. Showing the last reading.", now: "Now", noData: "no data",
      unitShort: "units", kwh: (u) => `${u} units`,
    },
    hi: {
      appName: "मेरा सोलर", tToday: "आज", tAhead: "पूर्वानुमान", tMoney: "बचत", tCare: "देखभाल",
      site: (kw, place, model, time) => `${place} में ${kw} kW। सिम्युलेटेड इन्वर्टर ${model}, ${time} पर अपडेट।`,
      nowAt: (time) => `अभी, ${time}`, at: (time) => `${time} पर`, sunrise: (x) => `सूर्योदय ${x}`, sunset: (x) => `सूर्यास्त ${x}`,
      madeToday: "यूनिट आज बनीं",
      producing: (pct) => `बिजली बन रही है, क्षमता का ${pct}%`, forecastAt: (pct) => `अनुमान, क्षमता का ${pct}%`,
      night: (u) => `रात में बंद। आज: ${u} यूनिट`, idle: "अभी नहीं बन रही",
      st_overvoltage: "रुका: ग्रिड वोल्टेज बहुत ज़्यादा", st_undervoltage: "रुका: सप्लाई वोल्टेज बहुत कम",
      st_outage: "बंद: बिजली कटी है", st_offline: "बिजली बन रही है, पर निगरानी ऑफ़लाइन है",
      liveWhy: "इसका मतलब",
      flowTitle: "आपकी बिजली कहाँ जा रही है", fSolar: "पैनल से", fHome: "घर में इस्तेमाल",
      toGrid: "ग्रिड को भेजी", fromGrid: "ग्रिड से ली", gridIdle: "ग्रिड",
      todayTitle: "आज का उत्पादन", scrubHint: "दिन का कोई भी पल देखने के लिए कर्व छुएँ।",
      kYours: "आपके पैनल", kAhead: "अनुमान", kClean: "अगर पैनल साफ़ होते",
      cSoFar: "यूनिट अब तक", cSaved: "आज की बचत", cDay: "यूनिट आज अपेक्षित",
      splitLine: (self, out) => `आज की सोलर बिजली में से ${self} यूनिट घर में लगीं और ${out} ग्रिड को गईं।`,
      splitSelf: "घर में लगी", splitOut: "ग्रिड को गई", splitBuy: (u) => `अब तक ग्रिड से ${u} यूनिट ली`,
      dustTitle: (pct) => `धूल आपका ${pct}% उत्पादन ले रही है`, dustBody: (u, rs) => `आज लगभग ${u} यूनिट, ₹${rs} की। बारिश या सफ़ाई से वापस आएगी।`,
      dustClean: "पैनल साफ़ हैं", dustCleanBody: "आज धूल से कोई ख़ास नुकसान नहीं।",
      eventsTitle: "इन्वर्टर की घटनाएँ", eventsSub: "इस हफ़्ते क्या हुआ, आसान शब्दों में।", noEvents: "इस हफ़्ते कुछ असामान्य नहीं।",
      howToFix: "क्या करें", evidence: "इंस्टॉलर या DISCOM के लिए", copy: "कॉपी करें", sendWa: "WhatsApp पर भेजें", copied: "कॉपी हो गया",
      historyTitle: "पिछले 14 दिन", historyAvg: (u) => `औसत ${u} यूनिट रोज़`,
      aheadFoot: "Open-Meteo की आपकी छत की धूप, बादल और तापमान के अनुमान से, पैनल पर जमती धूल घटाकर।",
      rainWash: "बारिश पैनल धो सकती है", dustLevel: { clear: "धूल कम", dusty: "धूल", high: "बहुत धूल" },
      sky: { sun: "धूप", part: "हल्के बादल", cloud: "बादल", haze: "धुंध", rain: "बारिश", storm: "आँधी-तूफ़ान" },
      monthTitle: "इस महीने की बचत", monthUnits: (u) => `इस महीने ${u} यूनिट बनीं`,
      onTrack: (pct, p, proj) => `${proj} यूनिट की राह पर, वादा की गई ${p} का ${pct}%।`,
      below: (pct, p, proj) => `${proj} यूनिट की ओर, वादा की गई ${p} का ${pct}%। वेंडर से बात करें।`,
      noPromise: "जाँचने के लिए सेटिंग में वेंडर की वादा की गई मासिक यूनिट डालें।",
      lifeRs: "लगने के बाद से बचत", lifeUnits: "यूनिट बनीं", lifeCo2: "टन CO₂ बची", lifeTrees: "पेड़ इतनी CO₂ एक साल में सोखते",
      yearsTitle: "अगले 25 साल", yearsSub: "पैनल हर साल लगभग आधा प्रतिशत घटते हैं। वारंटी 25वें साल कम से कम 80% की है।",
      yearTip: (y, u, s) => `${y}: ${u} यूनिट, पहले साल का ${s}%`, floor: "वारंटी की न्यूनतम सीमा",
      inverterNote: "ज़्यादातर इन्वर्टर 10 से 12 साल में एक बार बदलने पड़ते हैं। इसके लिए लगभग ₹25,000 अलग रखें।",
      cleanTitle: { rain: (d) => `${d} की बारिश पैनल धो देगी`, clean: (d) => `${d} को साफ़ करें, धूल बैठने के बाद`,
        wait: "इस हफ़्ते धूल ज़्यादा रहेगी", fine: "धूल कम: सामान्य सफ़ाई ठीक है" },
      cleanBody: { rain: "इस बार बाल्टी की ज़रूरत नहीं।", clean: "सुबह-सुबह सादा पानी; इन्वर्टर पर कभी पानी न डालें।",
        wait: "साफ़ दिन का इंतज़ार करें, वरना पैनल फिर धूल से भर जाएँगे।", fine: "इस मौसम में दो-तीन हफ़्ते में एक बार काफ़ी है।" },
      lastCleaned: (n) => `आख़िरी सफ़ाई ${n} दिन पहले।`, cleanedToday: "मैंने आज साफ़ किए", markedClean: "आज साफ़ किया दर्ज हुआ",
      calTitle: "आगे क्या", inDays: (n) => (n <= 0 ? "आज" : n === 1 ? "कल" : n < 60 ? `${n} दिन में` : n < 730 ? `${Math.round(n / 30)} महीने में` : `${Math.round(n / 365)} साल में`),
      cal: { bill_check: "बिल को ऐप से मिलाएँ", earthing: "अर्थिंग पिट और आइसोलेटर जाँचें", inspection: "इंस्टॉलर से सालाना जाँच",
        workmanship_warranty: "काम की वारंटी ख़त्म" },
      warrantyTitle: "वारंटी", w: [["पैनल उत्पादन", 25], ["पैनल प्रोडक्ट", 12], ["इन्वर्टर", 8], ["काम (वर्कमैनशिप)", 5]],
      wEnds: (y) => `${y} तक`,
      helpTitle: "मदद", helpSupport: "कुछ गड़बड़? अनुरोध तैयार करें", helpBill: "सोलर के बाद पहला बिल पढ़ें",
      helpPanel: "पैनल का लेबल जाँचें", helpConnect: "अपना असली इन्वर्टर जोड़ें",
      install: "ऐप इंस्टॉल करें",
      settingsTitle: "आपका सिस्टम", cancel: "रद्द करें", save: "सेव करें", setupTitle: "अपने पैनल सेट करें",
      setupNote: "इनसे आपके पैनल का मॉडल बनता है: साइज़, जगह, लगने की तारीख़ और वेंडर का वादा। कभी भी बदल सकते हैं।",
      sKw: "सिस्टम साइज़ (kW)", sPlace: "इलाका और शहर", sInstalled: "लगने की तारीख़", sCleaned: "आख़िरी सफ़ाई",
      sUse: "महीने की बिजली खपत (यूनिट)", sPromised: "वेंडर की वादा की गई मासिक यूनिट", sRate: "आपकी दर (₹ प्रति यूनिट)", sLang: "भाषा",
      settingsNote: "सिर्फ़ इसी फ़ोन पर सेव। लोकेशन लगभग एक किलोमीटर तक ही रखी जाती है।", placeNotFound: "यह जगह नहीं मिली; पुरानी रखी गई।",
      connectTitle: "अपना असली इन्वर्टर जोड़ें",
      connectBody: "हर ब्रांड का अपना क्लाउड है, और उसे पढ़ने के लिए इंस्टॉलर को एक्सेस देना होता है। तब तक एक सिम्युलेटर काम करता है: वह आपके इलाके की असली धूप, बादल, तापमान और धूल के हिसाब से चलता है।",
      connectWhat: "जोड़ने के लिए क्या चाहिए", connectSteps: "इन्वर्टर का ब्रांड, लॉगर का सीरियल नंबर, और इंस्टॉलर ब्रांड के ऐप में सूर्य साथी को प्लांट से जोड़े।",
      down: "पैनल के क्लाउड तक नहीं पहुँच पाए। आख़िरी रीडिंग दिख रही है।", now: "अभी", noData: "डेटा नहीं",
      unitShort: "यूनिट", kwh: (u) => `${u} यूनिट`,
    },
  };

  let lang = (() => {
    const q = new URLSearchParams(location.search).get("lang");
    if (q === "en" || q === "hi") return q;
    try { const l = localStorage.getItem("lang"); if (l === "en" || l === "hi") return l; } catch (_) { /* storage blocked */ }
    return (navigator.language || "").toLowerCase().startsWith("hi") ? "hi" : "en";
  })();
  const t = (k, ...a) => { const v = STR[lang][k] ?? STR.en[k]; return typeof v === "function" ? v(...a) : v; };
  const read = (k, d) => { try { const v = localStorage.getItem(k); return v ? JSON.parse(v) : d; } catch (_) { return d; } };
  const write = (k, v) => { try { localStorage.setItem(k, JSON.stringify(v)); } catch (_) { /* storage blocked */ } };
  const day = (offset = 0) => { const d = new Date(Date.now() + offset * 864e5); return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`; };
  const hhmm = (h) => `${String(Math.floor(h)).padStart(2, "0")}:${String(Math.round((h % 1) * 60) % 60).padStart(2, "0")}`;
  const fmt = (n, d = 0) => Number(n).toLocaleString("en-IN", { maximumFractionDigits: d, minimumFractionDigits: d });
  const dayName = (iso, opts) => new Date(`${iso}T00:00:00`).toLocaleDateString(lang === "hi" ? "hi-IN" : "en-IN", opts);
  const el = (tag, cls, text) => { const e = document.createElement(tag); if (cls) e.className = cls; if (text !== undefined) e.textContent = text; return e; };

  const DEFAULTS = { kw: 3, place: "Malviya Nagar, Delhi", lat: 28.53, lon: 77.21, installed: day(-190), cleaned: day(-10), use: 300, promised: 360, rate: 7 };
  let cfg = { ...DEFAULTS, ...read("surya-plant", {}) };
  let data = read("surya-plant-last", null);
  let scrub = null;
  const charts = {};

  // --- data ------------------------------------------------------------------------------------
  async function load() {
    const q = new URLSearchParams({ kw: cfg.kw, lat: cfg.lat, lon: cfg.lon, installed: cfg.installed, cleaned: cfg.cleaned,
      use: cfg.use, rate: cfg.rate, lang, ...(cfg.promised ? { promised: cfg.promised } : {}) });
    try {
      const r = await fetch(`${API}/plant?${q}`);
      if (!r.ok) throw new Error(r.status);
      data = await r.json();
      write("surya-plant-last", data);
    } catch (_) {
      if (data) toast(t("down"));
    }
    if (data) render();
  }

  function at(h) {
    const pts = data.today.points;
    if (!pts.length || h < pts[0].h || h > pts[pts.length - 1].h) return { h, kw: 0, clean: 0, home: homeAt(h), ahead: h > data.now.hour };
    let i = pts.findIndex((p) => p.h >= h);
    if (i <= 0) i = 1;
    const a = pts[i - 1], b = pts[i], f = (h - a.h) / (b.h - a.h || 1);
    return { h, kw: a.kw + (b.kw - a.kw) * f, clean: a.clean_kw + (b.clean_kw - a.clean_kw) * f, home: a.home_kw + (b.home_kw - a.home_kw) * f, ahead: h > data.now.hour };
  }
  function homeAt(h) {  // outside daylight the points don't cover the home's use; it's the evening or night shape
    const shape = [0.3, 0.25, 0.25, 0.25, 0.3, 0.45, 0.7, 0.9, 0.85, 0.6, 0.5, 0.55, 0.6, 0.6, 0.55, 0.55, 0.6, 0.8, 1.1, 1.3, 1.35, 1.2, 0.9, 0.5];
    return (data.use * 12 / 365) * shape[Math.floor(h) % 24] / shape.reduce((s, x) => s + x, 0);
  }

  // --- today: the sky ----------------------------------------------------------------------------
  function renderMoment() {
    const live = scrub === null;
    const h = live ? data.now.hour : scrub;
    const m = live ? { kw: data.now.power_kw, home: data.now.home_kw ?? homeAt(h), ahead: false } : at(h);
    const { sunrise: rise, sunset: set } = data.today;
    const phase = h < rise - 0.4 || h > set + 0.4 ? "night" : h < rise + 1.1 ? "dawn" : h > set - 1.1 ? "dusk" : "day";
    $("sky").dataset.phase = phase;
    const path = $("arc-path"), len = path.getTotalLength(), f = Math.min(1, Math.max(0, (h - rise) / (set - rise)));
    const p = path.getPointAtLength(f * len);
    $("sun-mark").setAttribute("transform", `translate(${p.x} ${p.y})`);
    $("arc-done").style.strokeDasharray = `${f * len} ${len}`;
    $("sky-when").textContent = live ? t("nowAt", data.now.time) : t("at", hhmm(h));
    const kw = $("sky-kw");
    const status = $("sky-status");
    const pct = Math.round((m.kw / data.device.kw) * 100);
    if (live && data.now.status === "night") {
      kw.textContent = fmt(data.today.day_kwh, 1);
      kw.nextElementSibling.textContent = t("unitShort");
      status.textContent = t("madeToday");
    } else {
      kw.textContent = fmt(m.kw, 2);
      kw.nextElementSibling.textContent = "kW";
      status.textContent = live && data.now.status !== "producing" ? t(`st_${data.now.status}`)
        : m.kw <= 0.01 ? t("idle") : m.ahead ? t("forecastAt", pct) : t("producing", pct);
    }
    $("sky-rise").textContent = t("sunrise", hhmm(rise));
    $("sky-set").textContent = t("sunset", hhmm(set));
    renderFlow(phase === "night" && live ? 0 : m.kw, m.home);
  }

  // --- today: where the power goes ------------------------------------------------------------------
  let lastFlow = "";
  function renderFlow(solar, home) {
    const toHome = Math.min(solar, home), toGrid = Math.max(0, solar - home), fromGrid = Math.max(0, home - solar);
    $("f-solar").textContent = `${fmt(solar, 2)} kW`;
    $("f-home").textContent = `${fmt(home, 2)} kW`;
    $("f-grid").textContent = `${fmt(toGrid > 0.005 ? toGrid : fromGrid, 2)} kW`;
    $("f-grid-label").textContent = toGrid > 0.005 ? t("toGrid") : fromGrid > 0.005 ? t("fromGrid") : t("gridIdle");
    const key = [toHome, toGrid, fromGrid].map((x) => x.toFixed(1)).join("|");
    if (key === lastFlow) return;
    lastFlow = key;
    const lanes = [["p-sh", toHome, ""], ["p-sg", toGrid, ""], ["p-gh", fromGrid, "blue"]];
    const dots = $("dots");
    dots.innerHTML = "";
    for (const [id, kw, tone] of lanes) {
      $(id).classList.toggle("on", kw > 0.02);
      $(id).classList.toggle("blue", tone === "blue");
      if (kw <= 0.02) continue;
      const dur = Math.max(1.1, 4.2 - kw * 1.1).toFixed(2);
      for (let i = 0; i < 3; i++) {
        dots.insertAdjacentHTML("beforeend", `<circle r="4" class="dot ${tone}"><animateMotion dur="${dur}s" begin="-${(dur * i / 3).toFixed(2)}s" repeatCount="indefinite"><mpath href="#${id}"/></animateMotion></circle>`);
      }
    }
    document.querySelector(".node.solar").classList.toggle("on", solar > 0.02);
    document.querySelector(".node.grid").classList.toggle("on", toGrid > 0.02 || fromGrid > 0.02);
  }

  // --- charts ------------------------------------------------------------------------------------------
  const axisText = { color: C.muted, fontSize: 11, fontFamily: "Inter, Mukta, sans-serif" };
  const tip = { backgroundColor: C.ink, borderWidth: 0, padding: [8, 10], textStyle: { color: "#fff", fontSize: 12, fontFamily: "Inter, Mukta, sans-serif" },
    extraCssText: "border-radius:10px;box-shadow:0 8px 20px -8px rgba(0,0,0,.4);" };
  function chart(id) {
    if (!window.echarts) return null;
    const box = $(id);
    if (!box.clientWidth) return null;  // its tab isn't showing yet; drawn when it is
    if (!charts[id]) charts[id] = echarts.init(box, null, { renderer: "svg" });
    return charts[id];
  }

  function renderToday() {
    const c = chart("chart-today");
    if (!c) return;
    const pts = data.today.points, now = data.now.hour;
    $("chart-today").setAttribute("aria-label", `${t("todayTitle")}: ${t("kwh", fmt(data.today.so_far_kwh, 1))} ${t("cSoFar")}, ${t("kwh", fmt(data.today.day_kwh, 1))} ${t("cDay")}`);
    const past = pts.filter((p) => p.h <= now).map((p) => [p.h, +p.kw.toFixed(3)]);
    const ahead = pts.filter((p) => p.h >= now - 0.17).map((p) => [p.h, +p.kw.toFixed(3)]);
    const gaps = (data.today.gaps || []).map((g) => [{ xAxis: g.start, name: t("noData") }, { xAxis: g.end }]);
    c.setOption({
      animationDuration: 700, grid: { left: 36, right: 18, top: 22, bottom: 24 },
      xAxis: { type: "value", min: Math.floor(data.today.sunrise), max: Math.ceil(data.today.sunset), interval: 3,
        axisLabel: { ...axisText, formatter: (v) => hhmm(v), alignMaxLabel: "right", alignMinLabel: "left" },
        axisLine: { lineStyle: { color: C.line } }, axisTick: { show: false }, splitLine: { show: false } },
      // a round top a little above the clean-panel peak, in half-kW steps
      yAxis: { type: "value", min: 0, max: Math.max(0.5, Math.ceil(Math.max(...pts.map((p) => p.clean_kw)) * 1.15 * 2) / 2), splitNumber: 3,
        name: "kW", nameGap: 8, nameTextStyle: { ...axisText, align: "right" },
        axisLabel: { ...axisText, formatter: (v) => `${fmt(v, v % 1 ? 1 : 0)}` }, splitLine: { lineStyle: { color: C.grid } } },
      tooltip: { ...tip, trigger: "axis", axisPointer: { type: "line", lineStyle: { color: C.ink, width: 1, opacity: 0.5 } },
        formatter: (ps) => { const h = ps[0].value[0], m = at(h); return `<b>${hhmm(h)}</b><br>${t(m.ahead ? "kAhead" : "kYours")}: ${fmt(m.kw, 2)} kW<br>${t("kClean")}: ${fmt(m.clean, 2)} kW`; } },
      series: [
        { name: "clean", type: "line", data: pts.map((p) => [p.h, +p.clean_kw.toFixed(3)]), showSymbol: false, smooth: true,
          lineStyle: { color: C.clean, width: 2, type: "dashed" }, z: 1 },
        { name: "yours", type: "line", data: past, showSymbol: false, smooth: 0.2, lineStyle: { color: C.solar, width: 2.5 }, z: 3,
          areaStyle: { color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [{ offset: 0, color: "rgba(242,165,22,0.42)" }, { offset: 1, color: "rgba(242,165,22,0.02)" }]) },
          markLine: { symbol: "none", silent: true, data: [{ xAxis: now }], lineStyle: { color: C.ink, type: "solid", width: 1, opacity: 0.35 },
            label: { formatter: t("now"), color: C.muted, fontSize: 10, position: "end" } },
          markArea: gaps.length ? { silent: true, itemStyle: { color: "rgba(107,120,144,0.12)" }, label: { color: C.muted, fontSize: 10 }, data: gaps } : undefined },
        { name: "ahead", type: "line", data: ahead, showSymbol: false, smooth: true, lineStyle: { color: C.solar, width: 2, type: "dashed", opacity: 0.7 }, z: 2 },
      ],
    }, true);
    if (!c.__scrub) {
      c.__scrub = true;
      c.on("updateAxisPointer", (e) => { const v = e.axesInfo && e.axesInfo[0] && e.axesInfo[0].value; if (v != null) { scrub = v; renderMoment(); } });
      c.on("hideTip", () => { scrub = null; renderMoment(); });
      c.getZr().on("globalout", () => { scrub = null; renderMoment(); });
    }
  }

  function renderHistory() {
    const c = chart("chart-history");
    if (!c) return;
    const hist = data.history;
    const avg = hist.reduce((s, d) => s + d.kwh, 0) / (hist.length || 1);
    $("history-avg").textContent = t("historyAvg", fmt(avg, 1));
    c.setOption({
      grid: { left: 30, right: 8, top: 14, bottom: 24 },
      xAxis: { type: "category", data: hist.map((d) => dayName(d.date, { day: "numeric" })), axisLabel: axisText, axisTick: { show: false }, axisLine: { lineStyle: { color: C.line } } },
      yAxis: { type: "value", splitNumber: 3, axisLabel: axisText, splitLine: { lineStyle: { color: C.grid } } },
      tooltip: { ...tip, trigger: "item", formatter: (p) => `<b>${dayName(hist[p.dataIndex].date, { weekday: "short", day: "numeric", month: "short" })}</b><br>${t("kwh", fmt(p.value, 1))}` },
      series: [{ type: "bar", data: hist.map((d) => d.kwh), barWidth: "62%", itemStyle: { color: C.solar, borderRadius: [4, 4, 0, 0] },
        emphasis: { itemStyle: { color: "#a86b00" } },
        markLine: { symbol: "none", silent: true, data: [{ yAxis: +avg.toFixed(1) }], lineStyle: { color: C.ink, type: "dashed", opacity: 0.4 }, label: { show: false } } }],
    }, true);
  }

  function renderYears() {
    const c = chart("chart-years");
    if (!c) return;
    const ys = data.years, first = ys[0].units;
    c.setOption({
      grid: { left: 44, right: 10, top: 14, bottom: 24 },
      xAxis: { type: "category", data: ys.map((y) => y.year), axisLabel: { ...axisText, interval: 5 }, axisTick: { show: false }, axisLine: { lineStyle: { color: C.line } } },
      yAxis: { type: "value", min: Math.round(first * 0.7 / 100) * 100, splitNumber: 3, axisLabel: { ...axisText, formatter: (v) => fmt(v) }, splitLine: { lineStyle: { color: C.grid } } },
      tooltip: { ...tip, trigger: "axis", axisPointer: { type: "line", lineStyle: { color: C.ink, opacity: 0.4 } },
        formatter: (ps) => { const y = ys[ps[0].dataIndex]; return t("yearTip", y.year, fmt(y.units), Math.round(y.share * 100)); } },
      series: [{ type: "line", data: ys.map((y) => y.units), showSymbol: false, smooth: true, lineStyle: { color: C.save, width: 2.5 },
        areaStyle: { color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [{ offset: 0, color: "rgba(34,144,90,0.22)" }, { offset: 1, color: "rgba(34,144,90,0.01)" }]) },
        markLine: { symbol: "none", silent: true, data: [{ yAxis: Math.round(first * 0.8) }], lineStyle: { color: C.muted, type: "dashed" },
          label: { formatter: t("floor"), color: C.muted, fontSize: 10, position: "insideStartTop" } } }],
    }, true);
  }

  // --- today: the rest ---------------------------------------------------------------------------------
  function renderTodayCards() {
    const d = data;
    $("site").textContent = t("site", fmt(d.device.kw, 1).replace(/\.0$/, ""), cfg.place, d.device.model, d.now.time);
    const live = $("live-event");
    live.hidden = !d.now.event;
    if (d.now.event) {
      live.innerHTML = "";
      const ic = el("ion-icon"); ic.setAttribute("name", d.now.event.code === "offline" ? "wifi-outline" : "warning-outline");
      const box = el("div");
      box.append(el("h3", null, d.now.event.title), el("p", null, d.now.event.meaning));
      const b = el("ion-button", null, t("liveWhy")); b.setAttribute("size", "small"); b.setAttribute("fill", "outline");
      b.addEventListener("click", () => openEvent(d.now.event));
      box.append(b);
      live.append(ic, box);
    }
    $("t-sofar").textContent = fmt(d.today.so_far_kwh, 1);
    $("t-saved").textContent = `₹${fmt(d.today.saved_rs)}`;
    $("t-day").textContent = fmt(d.today.day_kwh, 1);
    const split = $("t-split"), self = d.today.self_used_kwh, out = d.today.exported_kwh, total = self + out;
    split.innerHTML = "";
    if (total > 0.05) {
      const bar = el("div", "split-bar");
      const a = el("i", "self"); a.style.width = `${(self / total) * 100}%`;
      const b = el("i", "out"); b.style.width = `${(out / total) * 100}%`;
      bar.append(a, b);
      const keys = el("div", "split-keys");
      for (const [cls, label, v] of [["self", t("splitSelf"), self], ["out", t("splitOut"), out]]) {
        const s = el("span"); const i = el("i"); i.style.background = cls === "self" ? C.solar : C.clean;
        s.append(i, `${t("kwh", fmt(v, 1))} ${label}`); keys.append(s);
      }
      split.append(bar, keys, el("p", "cap", t("splitBuy", fmt(d.today.imported_kwh, 1))));
    }
    const dust = $("dust-card");
    dust.innerHTML = "";
    const lossy = d.today.soiling_pct >= 1;
    const ic = el("div", `badge-ic ${lossy ? "sun" : "green"}`); const i2 = el("ion-icon"); i2.setAttribute("name", lossy ? "partly-sunny-outline" : "sparkles-outline"); ic.append(i2);
    const box = el("div");
    box.append(el("h3", null, lossy ? t("dustTitle", fmt(d.today.soiling_pct, 1)) : t("dustClean")),
      el("p", null, lossy ? t("dustBody", fmt(d.today.dust_loss_kwh, 1), fmt(d.today.dust_loss_rs)) : t("dustCleanBody")));
    dust.append(ic, box);
    renderEvents();
  }

  const EVENT_ICON = { overvoltage: ["trending-up-outline", "sun"], undervoltage: ["trending-down-outline", "sun"], outage: ["power-outline", "grey"], offline: ["wifi-outline", "blue"] };
  function renderEvents() {
    const list = $("events");
    list.innerHTML = "";
    if (!data.events.length) { list.append(el("p", "empty", t("noEvents"))); return; }
    for (const e of data.events.slice(0, 6)) {
      const item = el("ion-item"); item.button = true; item.detail = true;
      const [icon, tone] = EVENT_ICON[e.code] || ["alert-circle-outline", "grey"];
      const b = el("div", `badge-ic ${tone}`); b.setAttribute("slot", "start"); b.style.cssText = "width:36px;height:36px;font-size:19px;border-radius:11px;margin-inline-end:12px";
      const ic = el("ion-icon"); ic.setAttribute("name", icon); b.append(ic);
      const label = el("ion-label");
      label.append(el("div", "ev-title", e.title), el("div", "ev-when", `${dayName(e.day, { weekday: "short", day: "numeric", month: "short" })}, ${e.start}–${e.end}`));
      item.append(b, label);
      item.addEventListener("click", () => openEvent(e));
      list.append(item);
    }
  }

  function openEvent(e) {
    const body = $("event-body");
    body.innerHTML = "";
    body.append(el("h3", null, e.title), el("p", "when", `${dayName(e.day, { weekday: "long", day: "numeric", month: "long" })}, ${e.start}–${e.end}${e.volts ? `, ${e.volts} V` : ""}`),
      el("p", null, e.meaning), el("h4", null, t("howToFix")), el("p", null, e.todo), el("h4", null, t("evidence")), el("div", "evidence", e.evidence));
    const row = el("div", "row");
    const copy = el("ion-button", null, t("copy")); copy.setAttribute("fill", "outline");
    copy.addEventListener("click", async () => { try { await navigator.clipboard.writeText(e.evidence); toast(t("copied")); } catch (_) { /* clipboard blocked */ } });
    const wa = el("ion-button", null, t("sendWa")); wa.setAttribute("href", `https://wa.me/?text=${encodeURIComponent(e.evidence)}`); wa.setAttribute("target", "_blank");
    row.append(copy, wa);
    body.append(row);
    $("event-sheet").present();
  }

  // --- forecast ------------------------------------------------------------------------------------------
  const SKY_ICON = { sun: "sunny", part: "partly-sunny", cloud: "cloudy", haze: "cloudy-outline", rain: "rainy", storm: "thunderstorm" };
  function renderAhead() {
    const box = $("days");
    box.innerHTML = "";
    for (const a of data.ahead) {
      const c = el("div", "day");
      const ic = el("ion-icon", `sky-${a.sky}`); ic.setAttribute("name", SKY_ICON[a.sky] || "sunny");
      const u = el("p", "units", fmt(a.kwh, 1)); u.append(el("small", null, t("unitShort")));
      const meta = [t("sky")[a.sky], `${Math.round(a.max_c)}°C`, a.dust ? t("dustLevel")[a.dust] : null].filter(Boolean).join(", ");
      c.append(el("p", "dname", dayName(a.date, { weekday: "long" })), el("p", "ddate", dayName(a.date, { day: "numeric", month: "short" })), ic, u,
        el("p", "rs", `₹${fmt(a.rs)}`), el("p", "meta", meta));
      if (a.rain_mm >= 3) c.append(el("p", "meta", t("rainWash")));
      box.append(c);
    }
    renderHistory();
  }

  // --- savings ---------------------------------------------------------------------------------------------
  function renderMoney() {
    const m = data.month;
    $("m-rs").textContent = `₹${fmt(m.rs)}`;
    $("m-kwh").textContent = t("monthUnits", fmt(m.kwh));
    const pr = $("promise");
    pr.innerHTML = "";
    if (m.promised_kwh) {
      const ok = m.on_track_pct >= 92;
      const track = el("div", `track${ok ? "" : " low"}`); const fill = el("i"); fill.style.width = `${Math.min(100, m.on_track_pct)}%`; track.append(fill);
      pr.append(track, el("p", null, t(ok ? "onTrack" : "below", m.on_track_pct, fmt(m.promised_kwh), fmt(m.projected_kwh))));
    } else pr.append(el("p", null, t("noPromise")));
    const life = $("life");
    life.innerHTML = "";
    const L = data.lifetime;
    for (const [icon, color, v, cap] of [["wallet-outline", C.save, `₹${fmt(L.rs)}`, t("lifeRs")], ["flash-outline", C.solar, fmt(L.kwh), t("lifeUnits")],
      ["leaf-outline", C.save, fmt(L.co2_t, 2), t("lifeCo2")], ["earth-outline", C.clean, fmt(L.trees), t("lifeTrees")]]) {
      const tile = el("div", "tile"); const ic = el("ion-icon"); ic.setAttribute("name", icon); ic.style.color = color;
      tile.append(ic, el("p", "fig", v), el("p", "cap", cap));
      life.append(tile);
    }
    renderYears();
  }

  // --- care ----------------------------------------------------------------------------------------------------
  function renderCare() {
    const care = data.care;
    const kind = care.rain_wash ? "rain" : care.clean_on ? "clean" : care.dust_advice === "dusty_week" ? "wait" : "fine";
    const dayLabel = (iso) => dayName(iso, { weekday: "long", day: "numeric", month: "short" });
    const card = $("clean-card");
    card.innerHTML = "";
    const ic = el("div", `badge-ic ${kind === "wait" ? "sun" : kind === "rain" ? "blue" : "green"}`); const i2 = el("ion-icon");
    i2.setAttribute("name", kind === "rain" ? "rainy-outline" : "water-outline"); ic.append(i2);
    const box = el("div");
    const title = STR[lang].cleanTitle[kind];
    const since = Math.max(0, Math.round((Date.now() - new Date(`${cfg.cleaned}T00:00:00`)) / 864e5));
    box.append(el("h3", null, typeof title === "function" ? title(dayLabel(care.rain_wash || care.clean_on)) : title),
      el("p", null, STR[lang].cleanBody[kind]), el("p", null, t("lastCleaned", since)));
    const b = el("ion-button", null, t("cleanedToday")); b.setAttribute("size", "small");
    b.addEventListener("click", () => { cfg.cleaned = day(0); write("surya-plant", cfg); toast(t("markedClean")); load(); });
    box.append(b);
    card.append(ic, box);

    const cal = $("calendar");
    cal.innerHTML = "";
    for (const n of care.next) {
      const item = el("ion-item");
      const d = new Date(`${n.on}T00:00:00`);
      const when = el("div", "when", String(d.getDate())); when.setAttribute("slot", "start");
      when.append(el("small", null, d.toLocaleDateString(lang === "hi" ? "hi-IN" : "en-IN", { month: "short", year: n.in_days > 300 ? "numeric" : undefined })));
      const label = el("ion-label"); label.append(el("div", "cal-what", t("cal")[n.what] || n.what), el("div", "cal-in", t("inDays", n.in_days)));
      item.append(when, label);
      cal.append(item);
    }
    const w = $("warranty");
    w.innerHTML = "";
    const start = new Date(`${data.device.installed}T00:00:00`), years = (Date.now() - start) / (365.25 * 864e5);
    for (const [name, span] of t("w")) {
      const row = el("div", "w-row");
      const p = el("p"); p.append(el("span", null, name), el("span", null, t("wEnds", start.getFullYear() + span)));
      const track = el("div", "w-track"); const fill = el("i"); fill.style.width = `${(span / 25) * 100}%`;
      const nowMark = el("b"); nowMark.style.left = `${Math.min(100, (years / 25) * 100)}%`;
      track.append(fill, nowMark);
      row.append(p, track);
      w.append(row);
    }
  }

  // --- everything ------------------------------------------------------------------------------------------------
  function applyLang() {
    document.documentElement.lang = lang;
    document.querySelectorAll("[data-t]").forEach((e) => { e.textContent = t(e.dataset.t); });
    document.querySelectorAll("[data-label]").forEach((e) => { e.label = t(e.dataset.label); });
    document.title = `${t("appName")} – Surya Saathi`;
  }
  function render() {
    renderTodayCards();
    renderMoment();
    renderToday();
    renderAhead();
    renderMoney();
    renderCare();
  }
  function toast(message) { const tt = $("toast"); tt.message = message; tt.present(); }

  // settings
  function openSettings(first) {
    $("settings").querySelector("ion-title").textContent = t(first === true ? "setupTitle" : "settingsTitle");
    $("s-kw").value = cfg.kw; $("s-place").value = cfg.place; $("s-installed").value = cfg.installed; $("s-cleaned").value = cfg.cleaned;
    $("s-use").value = cfg.use; $("s-promised").value = cfg.promised || ""; $("s-rate").value = cfg.rate; $("s-lang").value = lang;
    $("settings-note").textContent = first === true ? `${t("setupNote")} ${t("settingsNote")}` : t("settingsNote");
    $("settings").present();
  }
  async function saveSettings() {
    const num = (id, d) => { const v = parseFloat($(id).value); return Number.isFinite(v) ? v : d; };
    const next = { ...cfg, kw: num("s-kw", cfg.kw), installed: $("s-installed").value || cfg.installed, cleaned: $("s-cleaned").value || cfg.cleaned,
      use: num("s-use", cfg.use), promised: num("s-promised", 0) || null, rate: num("s-rate", cfg.rate) };
    const place = String($("s-place").value || "").trim();
    if (place && place !== cfg.place) {
      try {
        const r = await fetch(`${API}/places?q=${encodeURIComponent(place)}`);
        if (!r.ok) throw new Error(r.status);
        const p = await r.json();
        // two decimals is about a kilometre: enough for sunlight and dust, not an address
        Object.assign(next, { place: p.name.split(",").slice(0, 2).join(",").trim(), lat: Math.round(p.lat * 100) / 100, lon: Math.round(p.lon * 100) / 100 });
      } catch (_) { toast(t("placeNotFound")); }
    }
    const newLang = $("s-lang").value;
    if (newLang && newLang !== lang) { lang = newLang; try { localStorage.setItem("lang", lang); } catch (_) { /* blocked */ } applyLang(); }  // shared with the website
    cfg = next;
    write("surya-plant", cfg);
    $("settings").dismiss();
    load();
  }
  function openConnect() {
    const body = $("connect-body");
    body.innerHTML = "";
    const brands = el("div", "brands");
    for (const b of ["Growatt", "Sungrow", "Solis", "GoodWe", "Havells", "Luminous", "Waaree", "Deye", "Enphase"]) brands.append(el("span", null, b));
    body.append(el("h3", null, t("connectTitle")), el("p", null, t("connectBody")), brands, el("h4", null, t("connectWhat")), el("p", null, t("connectSteps")));
    $("connect").present();
  }

  // install as an app
  let installEvent = null;
  window.addEventListener("beforeinstallprompt", (e) => { e.preventDefault(); installEvent = e; $("install").hidden = false; });
  function wire() {
    $("open-settings").addEventListener("click", openSettings);
    $("settings-cancel").addEventListener("click", () => { write("surya-plant", cfg); $("settings").dismiss(); });
    $("settings-save").addEventListener("click", saveSettings);
    $("open-connect").addEventListener("click", openConnect);
    $("install").addEventListener("click", async () => { if (!installEvent) return; installEvent.prompt(); await installEvent.userChoice; installEvent = null; $("install").hidden = true; });
    document.querySelector(".refresher").addEventListener("ionRefresh", async (e) => { await load(); e.target.complete(); });
    $("tabs").addEventListener("ionTabsDidChange", () => { setTimeout(() => { if (data) { renderToday(); renderHistory(); renderYears(); } Object.values(charts).forEach((c) => c.resize()); }, 60); });
    window.addEventListener("resize", () => Object.values(charts).forEach((c) => c.resize()));
    document.addEventListener("visibilitychange", () => { if (!document.hidden) load(); });
    setInterval(() => { if (!document.hidden && scrub === null) load(); }, 60000);
  }

  async function start() {
    await customElements.whenDefined("ion-tabs");
    applyLang();
    wire();
    if (data) render();
    await load();
    // the first time the installed app opens, set the system up; the website's iPhone keeps the demo home
    if (!new URLSearchParams(location.search).has("embed") && !read("surya-plant", null)) setTimeout(() => openSettings(true), 600);
    // charts wait for their container's size, which Ionic sets after its first layout
    setTimeout(() => { if (data) { renderToday(); renderHistory(); renderYears(); } }, 400);
    if ("serviceWorker" in navigator && location.protocol === "https:") navigator.serviceWorker.register("sw.js").catch(() => {});
  }
  start();
})();
