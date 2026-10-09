"use strict";

// The three tool pages: Get quotes, Schemes, After installation.
// Shares T, t(), state, $, post(), getJSON(), rupees() and route() with app.js.

Object.assign(T.en, {
  navQuotes: "Get quotes", navSchemes: "Schemes", navApply: "Apply", navCare: "After install",
  u1t: "Compare quotes before you sign",
  u1d: "Ask once. Every vendor's quote is checked and compared by what you'll really pay after subsidy.",
  u1reply: "🧾 Quotes for 3 kW, compared after subsidy:\n1. Jhatpat Solar (demo): ₹1,32,000, you pay ₹1,32,000 after subsidy. 🔴 Imported panels: no subsidy.\n2. Dhoop Rooftop Co. (demo): ₹1,95,000, you pay ₹1,17,000 after subsidy. ✅ No problems found.",
  u1a: "Compare quotes",
  u4t: "Every subsidy for your state", u4d: "The central subsidy, your state's top-up and the 5.75% loan, each with its source and the date it was checked.",
  u4a: "See your schemes", msCentral: "Central subsidy, 3 kW", msCentralShort: "Central subsidy", msTop: "Delhi top-up, if you qualify",
  u5t: "Clean the panels on the right day", u5d: "Dust and smog cut solar output. A live air-quality forecast picks the day to clean, after the dust settles.",
  u5a: "See this week's forecast",
  plTitle: "Is this the panel you paid for?",
  plSub: "Photograph the label on the back of a panel. It's read for the maker, wattage, serial and where it was made, then checked against the subsidy rules and serials already checked at other homes.",
  plWatt: "Panel wattage on your quote (W, optional)", plUpload: "Photograph a label", plSampleOk: "Try a made-in-India label",
  plSampleBad: "Try an imported one", plReading: "Reading the label…",
  plWhere: "Every panel has a label like this on its back. Photograph it close enough to read the serial number.",
  plAlt: "A sample panel label: maker, model, 545 W, serial number, made in India, DCR",
  spWho: (w) => `Contact: ${w}`, spSoon: "Add the dates and press Prepare request for a note you can send.",
  navVendors: "For vendors", qVendor: "Are you a registered vendor?", qVendorLink: "Answer requests",
  vTitle: "Answer quote requests", vSub: "Households near you have asked for quotes, sized from their bills. You see the size and the area, never their name or number. Your quote is checked the way the household will see it.",
  vName: "Company name", vShow: "Show requests", vNoName: "Enter your company name first.",
  vOpen: (n) => `${n} open request${n === 1 ? "" : "s"}`, vNone: "No open requests here right now.",
  vSample: "Sample request from the website demo", vSampleOnly: "No real requests here yet. Here's the website's sample, so you can try it.",
  vArea: (a) => (a ? `Area ${a}` : "Area not given"), vQuotes: (n) => `${n} quote${n === 1 ? "" : "s"} so far`,
  vAgo: (m) => (m < 1 ? "just now" : m < 60 ? `${m} min ago` : m < 1440 ? `${Math.round(m / 60)} h ago` : `${Math.round(m / 1440)} days ago`),
  vQuote: "Quote", vQuoted: "Quoted", vQuoteTitle: (kw, d) => `Your quote for ${kw} kW${d ? `, ${d}` : ""}`,
  vTotal: "Total price (₹)", vGst: "GST included?", vDcr: "Made-in-India (DCR) panels?", vWatt: "Each panel (W)", vCount: "Panel count",
  vInverter: "Inverter (kW)", vAdvance: "Advance (%)", vDays: "Install time (days)", vPanelW: "Panel warranty (yrs)", vInvW: "Inverter warranty (yrs)",
  vSysW: "System warranty (yrs)", vMeter: "Net meter included?", vStructure: "Structure included?", vEarthing: "Earthing included?",
  vPreview: "Preview what they'll see", vSend: "Send quote", vSent: "Sent. It's in the household's comparison now.",
  vAfter: "what the household pays after subsidy",
  fState: "State", fSize: "System size (kW)", fPin: "PIN code (optional)", fDcr: "Panels made in India (DCR)?",
  dcrYes: "Yes", dcrUnsure: "Not sure", dcrNo: "No",
  qTitle: "Compare quotes by what you'll really pay",
  qSub: "Ask once. Every quote is checked and shown after subsidy, so a cheap quote with imported panels can't fool you.",
  qGo: "Get quotes", qBadPin: "A PIN code has 6 digits and doesn't start with 0.", qBadKw: "Choose a size between 1 and 10 kW.",
  qWaiting: (n) => `Waiting for ${n} more vendor${n === 1 ? "" : "s"} to reply`,
  qDone: (n) => `${n} quotes in, compared after subsidy`,
  qDemo: "Demo: these four vendors are fictional, and each one shows a different trap.",
  qWait: "Waiting for a reply", qBest: "Best fit", qDemoTag: "Demo",
  qGrade: (g) => `Grade ${g}`, qOnTime: (p) => `${p}% on time`, qSent: (n) => `${n} quote${n === 1 ? "" : "s"} sent`,
  qQuotedL: "Quoted", qSubsidyL: "Subsidy",
  qAfter: "you pay after subsidy", qQuoted: (x) => `Quoted ${x}`, qSubsidy: (x) => `Subsidy −${x}`, qNoSubsidy: "No subsidy",
  qOk: "No problems found", qAmber: (k) => `${k} thing${k === 1 ? "" : "s"} to negotiate`,
  qRedDcr: "Imported panels lose the subsidy", qRedOver: "Promises more subsidy than the scheme pays", qRed: "Don't sign as it stands",
  qPanels: "Panels", qMadeIn: "Made in India", qImported: "Imported", qUnstated: "Not stated",
  qAdvance: "Advance", qInstall: "Install time", qDays: (d) => `${d} days`, qWarranty: "Warranty",
  qYears: (m, i, s) => `${m} / ${i} / ${s} yrs`, qNetMeter: "Net meter", qIncluded: "Included", qNotIncluded: "Not included",
  qChoose: "Choose", qChosen: "Chosen",
  qChosenNote: "Saved. Demo vendors aren't contacted; a real vendor would call you to fix a site visit. When they upload your agreement on pmsuryaghar.gov.in, approve it there.",
  qTrap: (cheap, best) => `${cheap} looks cheapest, but its imported panels lose the subsidy. ${best} costs less in the end.`,
  qGroup: (homes, needed, pin) => `${homes} of ${needed} homes in ${pin} this month. At ${needed}, vendors give a group price.`,
  qGroupOn: (homes, pin, pct) => `${homes} homes in ${pin} this month: group price, ${pct}% off.`,
  qDelete: "Delete this comparison", qDeleted: "Comparison deleted.",
  qOwnTitle: "Already have a quote?", qOwnSub: "Upload the quotation. It's read and checked the same way, in about ten seconds.",
  qChk1: "Made-in-India panels", qChk2: "Subsidy within the cap", qChk3: "A fair price per kW",
  qChk4: "Panel count matches kW", qChk5: "Inverter and warranties", qChk6: "Advance and payments",
  scamTitle: "Got a suspicious offer?", scamSub: "Paste the message, ad or call script you received.",
  scamGo: "Check it", scamExample: "Try an example", scamEmpty: "Paste the offer first.",
  scamSample: "Congratulations! You are selected for FREE solar under PM Surya Ghar. Pay ₹1,500 registration fee today only to book your ₹1,20,000 subsidy. Limited slots. Register at pmsuryaghar-yojana.com and share the OTP you receive.",
  sTitle: "Government help for your rooftop",
  sSub: "What the central government pays, what your state adds, and the low-interest loan. Every amount links to its source.",
  sCentralFor: (kw) => `Central subsidy for ${kw} kW`, sTopUp: (st) => `${st} top-up, if you qualify`,
  sTogether: (x) => `Together, up to ${x} if you qualify for both.`,
  sNoTopUp: (st) => `No general state top-up found for ${st}.`, sNotReviewed: (st) => `We haven't reviewed ${st}'s top-ups yet; ask your electricity company.`,
  sNoDcr: "Imported panels get no central subsidy.", sUnsure: "Counted once your vendor shows made-in-India (DCR) certificates for the panels.",
  sZero: "Homes using up to 400 units a month may get up to 3 kW with nothing to pay upfront.",
  sAcross: "Across India", sIn: (st) => `In ${st}`,
  sChecked: (d) => `Checked ${d}`, sOfficial: "Official source", sSource: "Source",
  sSourcesNote: "People confirm these amounts or report changes, and official pages are re-read every week.", sSourcesLink: "See every source",
  pTitle: "Can you carry the EMI until the subsidy arrives?",
  pSub: "The subsidy is paid after the system is commissioned, sometimes months later. Move the wait and see what it costs.",
  pCost: "Quoted price (₹)", pSaving: "Bill saving a month (₹)", pOwn: "Your share upfront (%)", pRate: "Loan interest (%)",
  pWait: "Months until the subsidy arrives",
  pCash: "Cash before installation", pWaitCash: "Cash until the subsidy arrives", pEmiBefore: "EMI before the subsidy", pEmiAfter: "EMI after, if the bank recasts",
  pInterest: (x) => `Interest paid while waiting: ${x}.`, pArrives: "Subsidy arrives", pEmiLegend: "EMI", pAfterLegend: "EMI after the subsidy", pSaveLegend: "Bill saving",
  pNote: "Illustration: floating rate, monthly EMIs, and an approved central subsidy used to prepay the loan. Ask your bank to recast the EMI after prepayment.",
  pBad: "Check the numbers above.",
  cTitle: "After the panels go up",
  cSub: "Keep the records that protect you, check the panels make what was promised, and read your first bill right.",
  ppTitle: "Your solar passport", ppDone: (n, total) => `${n} of ${total} done`, ppLocal: "Saved on this device only",
  ppCopy: "Copy checklist", ppCopied: "Copied", ppCopyFallback: "Select and copy the text",
  backupTitle: "Power cuts?", backupBody: "Ordinary on-grid solar switches off during a power cut, for safety. If backup matters, ask for a hybrid design with a battery and price it separately.",
  gTitle: "Are the panels making enough?", gSub: "Use a full month and the vendor's written monthly estimate.",
  gMonth: "Month", gActual: "Generated (kWh)", gPromised: "Promised (kWh)", gClean: "Last cleaned (optional)", gGo: "Check generation",
  gOf: (a, p) => `${a} of ${p} kWh promised`, gShort: (k) => `${k} kWh short`, gOnTrack: "On track", gReview: "Worth a review with your installer",
  gDust: "In Delhi, dust can cut output by 0.3–0.6% a day. Clean every two to four weeks in the dry season, and rule out outages and shade first.",
  gDraft: "Note for your installer",
  bTitle: "Read your first bill after solar", bSub: "Generation isn't the same as export. Use readings for the same billing dates.",
  bGen: "Solar generated (kWh)", bImport: "Taken from grid (kWh)", bExport: "Sent to grid, meter (kWh)", bBillExport: "Export on the bill (kWh)", bGo: "Explain my bill",
  bSolar: "Solar", bHome: "Home", bGrid: "Grid",
  bSelf: "Used at home, straight from solar", bTotal: "Home used in total", bNet: "Net taken from grid", bDiff: "Export units to ask about", bMatched: "The bill's export matches the meter.",
  spTitle: "Something wrong? Prepare a clear request",
  spSub: "Pick the problem. You get the evidence to attach and a note to send through the installer's or electricity company's official channel.",
  spKind: "Problem", spNoticed: "First noticed", spContacted: "Last contacted (optional)", spGo: "Prepare request",
  spEvidence: "Attach", spDraft: "Your note", spDays: (d) => `${d} days since you last contacted them.`,
  copy: "Copy", copied: "Copied", toolError: "That didn't work. Check the numbers and try again.",
  dTitle: "Dust this week", dSub: "Dust and smog cut solar output. A live forecast for your area, and the best day to clean.",
  dLocate: "Use my location", dClean: "Clean", dLevels: { clear: "Low", dusty: "Dusty", high: "Very dusty" },
  dAdvice: { clean_after: (day) => `Clean the panels on ${day}, after the dust settles. Plain water, early morning; never spray the inverter.`,
    dusty_week: () => "Dust stays high all week. Wait for a clear day, or the panels just get dusty again.",
    clean_lull: (day) => `Dust dips on ${day}, then rises again. If the panels look dirty, clean that morning; otherwise wait for a settled spell.`,
    clear_week: () => "Low dust this week, so your usual cleaning schedule is fine." },
  dWhy: "In Delhi, dust can cut output by 0.3–0.6% a day.", dSource: "Bars show the day's average PM10 in µg/m³; above 100 is over India's limit. Forecast by CAMS via", dDown: "The dust forecast isn't available right now.",
});

Object.assign(T.hi, {
  navQuotes: "कोटेशन लें", navSchemes: "योजनाएँ", navApply: "आवेदन", navCare: "लगने के बाद",
  u1t: "साइन करने से पहले कोटेशन मिलाएँ",
  u1d: "एक बार माँगें। हर वेंडर का कोटेशन जाँचा जाता है और सब्सिडी के बाद असली कीमत पर मिलाया जाता है।",
  u1reply: "🧾 3 kW के कोटेशन, सब्सिडी के बाद की तुलना:\n1. Jhatpat Solar (डेमो): ₹1,32,000, सब्सिडी के बाद आप देंगे ₹1,32,000। 🔴 विदेशी पैनल: सब्सिडी नहीं मिलेगी।\n2. Dhoop Rooftop Co. (डेमो): ₹1,95,000, सब्सिडी के बाद आप देंगे ₹1,17,000। ✅ कोई दिक्कत नहीं।",
  u1a: "कोटेशन मिलाएँ",
  u4t: "आपके राज्य की हर सब्सिडी", u4d: "केंद्रीय सब्सिडी, राज्य की अतिरिक्त सब्सिडी और 5.75% वाला लोन, हर एक के स्रोत और जाँच की तारीख के साथ।",
  u4a: "अपनी योजनाएँ देखें", msCentral: "केंद्रीय सब्सिडी, 3 kW", msCentralShort: "केंद्रीय सब्सिडी", msTop: "दिल्ली की अतिरिक्त सब्सिडी, अगर पात्र हों",
  u5t: "सही दिन पैनल साफ़ करें", u5d: "धूल और स्मॉग से सोलर उत्पादन घटता है। हवा की गुणवत्ता का लाइव अनुमान सफ़ाई का दिन चुनता है, धूल बैठने के बाद।",
  u5a: "इस हफ़्ते का अनुमान देखें",
  plTitle: "क्या यही पैनल है जिसका पैसा दिया?",
  plSub: "पैनल के पीछे लगे लेबल की फोटो लें। उसमें कंपनी, वॉट, सीरियल और कहाँ बना, यह पढ़ा जाता है, फिर सब्सिडी के नियमों और दूसरे घरों पर जाँचे गए सीरियल से मिलाया जाता है।",
  plWatt: "कोटेशन में पैनल का वॉट (W, वैकल्पिक)", plUpload: "लेबल की फोटो लें", plSampleOk: "भारत में बना लेबल आज़माएँ",
  plSampleBad: "विदेशी लेबल आज़माएँ", plReading: "लेबल पढ़ा जा रहा है…",
  plWhere: "हर पैनल के पीछे ऐसा लेबल होता है। इतने पास से फोटो लें कि सीरियल नंबर पढ़ा जा सके।",
  plAlt: "पैनल लेबल का नमूना: कंपनी, मॉडल, 545 W, सीरियल नंबर, भारत में बना, DCR",
  spWho: (w) => `संपर्क: ${w}`, spSoon: "तारीख़ें भरें और अनुरोध तैयार करें दबाएँ, भेजने लायक नोट मिलेगा।",
  navVendors: "वेंडर के लिए", qVendor: "क्या आप रजिस्टर्ड वेंडर हैं?", qVendorLink: "अनुरोधों का जवाब दें",
  vTitle: "कोटेशन अनुरोधों का जवाब दें", vSub: "आपके आस-पास के घरों ने बिल के हिसाब से कोटेशन माँगे हैं। आपको साइज़ और इलाका दिखता है, नाम या नंबर कभी नहीं। आपका कोटेशन वैसे ही जाँचा जाता है जैसे घर वाले देखेंगे।",
  vName: "कंपनी का नाम", vShow: "अनुरोध देखें", vNoName: "पहले अपनी कंपनी का नाम लिखें।",
  vOpen: (n) => `${n} खुले अनुरोध`, vNone: "अभी यहाँ कोई खुला अनुरोध नहीं है।",
  vSample: "वेबसाइट डेमो का नमूना अनुरोध", vSampleOnly: "यहाँ अभी कोई असली अनुरोध नहीं है। आज़माने के लिए वेबसाइट का नमूना दिखाया गया है।",
  vArea: (a) => (a ? `इलाका ${a}` : "इलाका नहीं बताया"), vQuotes: (n) => `अब तक ${n} कोटेशन`,
  vAgo: (m) => (m < 1 ? "अभी" : m < 60 ? `${m} मिनट पहले` : m < 1440 ? `${Math.round(m / 60)} घंटे पहले` : `${Math.round(m / 1440)} दिन पहले`),
  vQuote: "कोटेशन दें", vQuoted: "कोटेशन दिया", vQuoteTitle: (kw, d) => `${kw} kW के लिए आपका कोटेशन${d ? `, ${d}` : ""}`,
  vTotal: "कुल कीमत (₹)", vGst: "GST शामिल?", vDcr: "भारत में बने (DCR) पैनल?", vWatt: "हर पैनल (W)", vCount: "पैनलों की संख्या",
  vInverter: "इन्वर्टर (kW)", vAdvance: "एडवांस (%)", vDays: "लगने में समय (दिन)", vPanelW: "पैनल वारंटी (साल)", vInvW: "इन्वर्टर वारंटी (साल)",
  vSysW: "सिस्टम वारंटी (साल)", vMeter: "नेट मीटर शामिल?", vStructure: "स्ट्रक्चर शामिल?", vEarthing: "अर्थिंग शामिल?",
  vPreview: "देखें कि घर वालों को क्या दिखेगा", vSend: "कोटेशन भेजें", vSent: "भेज दिया। यह घर वालों की तुलना में अब दिख रहा है।",
  vAfter: "सब्सिडी के बाद घर वाले इतना देंगे",
  fState: "राज्य", fSize: "सिस्टम साइज़ (kW)", fPin: "पिन कोड (वैकल्पिक)", fDcr: "भारत में बने पैनल (DCR)?",
  dcrYes: "हाँ", dcrUnsure: "पता नहीं", dcrNo: "नहीं",
  qTitle: "कोटेशन को असली खर्च से मिलाएँ",
  qSub: "एक बार माँगें। हर कोटेशन जाँचा जाता है और सब्सिडी के बाद दिखाया जाता है, ताकि विदेशी पैनल वाला सस्ता कोटेशन धोखा न दे सके।",
  qGo: "कोटेशन लें", qBadPin: "पिन कोड 6 अंकों का होता है और 0 से शुरू नहीं होता।", qBadKw: "1 से 10 kW के बीच साइज़ चुनें।",
  qWaiting: (n) => `${n} और वेंडर के जवाब का इंतज़ार`,
  qDone: (n) => `${n} कोटेशन आ गए, सब्सिडी के बाद की तुलना`,
  qDemo: "डेमो: ये चारों वेंडर काल्पनिक हैं, और हर एक अलग धोखा दिखाता है।",
  qWait: "जवाब का इंतज़ार", qBest: "सबसे सही", qDemoTag: "डेमो",
  qGrade: (g) => `ग्रेड ${g}`, qOnTime: (p) => `${p}% समय पर`, qSent: (n) => `${n} कोटेशन भेजे`,
  qQuotedL: "कोटेशन", qSubsidyL: "सब्सिडी",
  qAfter: "सब्सिडी के बाद आप देंगे", qQuoted: (x) => `कोटेशन ${x}`, qSubsidy: (x) => `सब्सिडी −${x}`, qNoSubsidy: "सब्सिडी नहीं",
  qOk: "कोई दिक्कत नहीं", qAmber: (k) => `${k} बातों पर मोलभाव करें`,
  qRedDcr: "विदेशी पैनल पर सब्सिडी नहीं मिलती", qRedOver: "योजना से ज़्यादा सब्सिडी का वादा", qRed: "ऐसे ही साइन न करें",
  qPanels: "पैनल", qMadeIn: "भारत में बने", qImported: "विदेशी", qUnstated: "नहीं बताया",
  qAdvance: "एडवांस", qInstall: "लगने में समय", qDays: (d) => `${d} दिन`, qWarranty: "वारंटी",
  qYears: (m, i, s) => `${m} / ${i} / ${s} साल`, qNetMeter: "नेट मीटर", qIncluded: "शामिल", qNotIncluded: "शामिल नहीं",
  qChoose: "चुनें", qChosen: "चुना गया",
  qChosenNote: "सेव हो गया। डेमो वेंडर से संपर्क नहीं होता; असली वेंडर साइट विज़िट के लिए कॉल करेगा। जब वे pmsuryaghar.gov.in पर एग्रीमेंट अपलोड करें, वहीं मंज़ूर करें।",
  qTrap: (cheap, best) => `${cheap} सबसे सस्ता दिखता है, पर विदेशी पैनल से सब्सिडी चली जाती है। आखिर में ${best} सस्ता पड़ता है।`,
  qGroup: (homes, needed, pin) => `इस महीने ${pin} से ${needed} में से ${homes} घर। ${needed} होने पर वेंडर ग्रुप रेट देते हैं।`,
  qGroupOn: (homes, pin, pct) => `इस महीने ${pin} से ${homes} घर: ग्रुप रेट, ${pct}% छूट।`,
  qDelete: "यह तुलना मिटाएँ", qDeleted: "तुलना मिटा दी।",
  qOwnTitle: "कोटेशन पहले से है?", qOwnSub: "कोटेशन अपलोड करें। इसे भी लगभग दस सेकंड में इसी तरह पढ़ा और जाँचा जाता है।",
  qChk1: "भारत में बने पैनल", qChk2: "सब्सिडी सीमा के भीतर", qChk3: "प्रति kW सही कीमत",
  qChk4: "पैनल कुल kW के बराबर", qChk5: "इन्वर्टर और वारंटी", qChk6: "एडवांस और भुगतान",
  scamTitle: "कोई संदिग्ध ऑफ़र मिला?", scamSub: "मिला हुआ मैसेज, विज्ञापन या कॉल की बात यहाँ चिपकाएँ।",
  scamGo: "जाँचें", scamExample: "उदाहरण आज़माएँ", scamEmpty: "पहले ऑफ़र चिपकाएँ।",
  scamSample: "बधाई हो! PM सूर्य घर में आपको मुफ्त सोलर के लिए चुना गया है। अपनी ₹1,20,000 सब्सिडी बुक करने के लिए आज ही ₹1,500 रजिस्ट्रेशन फीस दें। सीमित स्लॉट। pmsuryaghar-yojana.com पर रजिस्टर करें और आया हुआ OTP बताएँ।",
  sTitle: "आपकी छत के लिए सरकारी मदद",
  sSub: "केंद्र सरकार कितना देती है, आपका राज्य कितना जोड़ता है, और कम ब्याज वाला लोन। हर राशि का स्रोत साथ है।",
  sCentralFor: (kw) => `${kw} kW पर केंद्रीय सब्सिडी`, sTopUp: (st) => `${st} की अतिरिक्त सब्सिडी, अगर आप पात्र हैं`,
  sTogether: (x) => `दोनों के पात्र हों तो कुल ${x} तक।`,
  sNoTopUp: (st) => `${st} के लिए कोई सामान्य राज्य सब्सिडी नहीं मिली।`, sNotReviewed: (st) => `${st} की राज्य सब्सिडी अभी नहीं जाँची; अपनी बिजली कंपनी से पूछें।`,
  sNoDcr: "विदेशी पैनल पर केंद्रीय सब्सिडी नहीं मिलती।", sUnsure: "वेंडर के भारत में बने (DCR) पैनल के प्रमाणपत्र दिखाने पर ही गिनी जाएगी।",
  sZero: "महीने में 400 यूनिट तक खपत वाले घरों को 3 kW तक बिना शुरुआती भुगतान के मिल सकता है।",
  sAcross: "पूरे भारत में", sIn: (st) => `${st} में`,
  sChecked: (d) => `जाँचा: ${d}`, sOfficial: "आधिकारिक स्रोत", sSource: "स्रोत",
  sSourcesNote: "लोग इन राशियों की पुष्टि करते हैं या बदलाव बताते हैं, और सरकारी पेज हर हफ़्ते दोबारा पढ़े जाते हैं।", sSourcesLink: "सारे स्रोत देखें",
  pTitle: "क्या सब्सिडी आने तक EMI भर पाएँगे?",
  pSub: "सब्सिडी सिस्टम चालू होने के बाद मिलती है, कभी-कभी महीनों बाद। इंतज़ार बदलकर देखें कि इसका खर्च कितना है।",
  pCost: "कोटेशन की कीमत (₹)", pSaving: "हर महीने बिल में बचत (₹)", pOwn: "आपका शुरुआती हिस्सा (%)", pRate: "लोन का ब्याज (%)",
  pWait: "सब्सिडी आने में महीने",
  pCash: "लगने से पहले नकद", pWaitCash: "सब्सिडी आने तक नकद", pEmiBefore: "सब्सिडी से पहले EMI", pEmiAfter: "बाद की EMI, अगर बैंक दोबारा तय करे",
  pInterest: (x) => `इंतज़ार में ब्याज: ${x}।`, pArrives: "सब्सिडी आई", pEmiLegend: "EMI", pAfterLegend: "सब्सिडी के बाद EMI", pSaveLegend: "बिल में बचत",
  pNote: "उदाहरण: बदलती ब्याज दर, मासिक EMI, और मंज़ूर केंद्रीय सब्सिडी से लोन घटाना। सब्सिडी जमा होने के बाद बैंक से EMI दोबारा तय करने को कहें।",
  pBad: "ऊपर की संख्याएँ जाँचें।",
  cTitle: "पैनल लगने के बाद",
  cSub: "अपनी सुरक्षा वाले कागज़ात रखें, जाँचें कि पैनल वादे जितनी बिजली बना रहे हैं, और पहला बिल सही पढ़ें।",
  ppTitle: "आपका सोलर पासपोर्ट", ppDone: (n, total) => `${total} में से ${n} पूरे`, ppLocal: "सिर्फ़ इसी डिवाइस पर सेव",
  ppCopy: "सूची कॉपी करें", ppCopied: "कॉपी हो गया", ppCopyFallback: "टेक्स्ट चुनकर कॉपी करें",
  backupTitle: "बिजली कटौती?", backupBody: "सामान्य ऑन-ग्रिड सोलर सुरक्षा के लिए बिजली जाने पर बंद हो जाता है। बैकअप चाहिए तो बैटरी वाला हाइब्रिड सिस्टम माँगें और उसकी कीमत अलग पूछें।",
  gTitle: "क्या पैनल पूरी बिजली बना रहे हैं?", gSub: "पूरा महीना और वेंडर का लिखित मासिक अनुमान लें।",
  gMonth: "महीना", gActual: "बनी बिजली (kWh)", gPromised: "वादा (kWh)", gClean: "आखिरी सफ़ाई (वैकल्पिक)", gGo: "उत्पादन जाँचें",
  gOf: (a, p) => `${p} kWh के वादे में से ${a}`, gShort: (k) => `${k} kWh कम`, gOnTrack: "ठीक चल रहा है", gReview: "इंस्टॉलर के साथ जाँच कराएँ",
  gDust: "दिल्ली में धूल से उत्पादन रोज़ 0.3–0.6% घट सकता है। सूखे मौसम में हर दो-चार हफ़्ते में सफ़ाई करें, पर पहले कटौती और छाया की जाँच करें।",
  gDraft: "इंस्टॉलर के लिए नोट",
  bTitle: "सोलर के बाद पहला बिल पढ़ें", bSub: "उत्पादन और निर्यात अलग चीज़ें हैं। एक ही बिल अवधि की रीडिंग लें।",
  bGen: "सोलर से बनी (kWh)", bImport: "ग्रिड से ली (kWh)", bExport: "ग्रिड को भेजी, मीटर (kWh)", bBillExport: "बिल पर निर्यात (kWh)", bGo: "मेरा बिल समझाएँ",
  bSolar: "सोलर", bHome: "घर", bGrid: "ग्रिड",
  bSelf: "सोलर से सीधे घर में इस्तेमाल", bTotal: "घर में कुल इस्तेमाल", bNet: "ग्रिड से कुल ली", bDiff: "निर्यात की यूनिट जिन पर पूछें", bMatched: "बिल का निर्यात मीटर से मेल खाता है।",
  spTitle: "कुछ गड़बड़ है? साफ़ अनुरोध तैयार करें",
  spSub: "समस्या चुनें। साथ लगाने वाले प्रमाण और भेजने के लिए नोट मिलेगा, जिसे इंस्टॉलर या बिजली कंपनी के आधिकारिक माध्यम से भेजें।",
  spKind: "समस्या", spNoticed: "पहली बार कब देखा", spContacted: "आखिरी बार कब संपर्क किया (वैकल्पिक)", spGo: "अनुरोध तैयार करें",
  spEvidence: "साथ लगाएँ", spDraft: "आपका नोट", spDays: (d) => `आखिरी संपर्क को ${d} दिन हुए।`,
  copy: "कॉपी करें", copied: "कॉपी हो गया", toolError: "यह नहीं चला। संख्याएँ जाँचकर फिर कोशिश करें।",
  dTitle: "इस हफ़्ते धूल", dSub: "धूल और स्मॉग से सोलर उत्पादन घटता है। आपके इलाके का लाइव अनुमान, और सफ़ाई का सबसे अच्छा दिन।",
  dLocate: "मेरी लोकेशन लें", dClean: "सफ़ाई", dLevels: { clear: "कम", dusty: "धूल", high: "बहुत धूल" },
  dAdvice: { clean_after: (day) => `${day} को पैनल साफ़ करें, धूल बैठने के बाद। सुबह-सुबह सादे पानी से; इन्वर्टर पर कभी पानी न डालें।`,
    dusty_week: () => "पूरे हफ़्ते धूल ज़्यादा रहेगी। साफ़ दिन का इंतज़ार करें, वरना पैनल फिर धूल से भर जाएँगे।",
    clean_lull: (day) => `${day} को धूल कुछ कम होगी, फिर बढ़ेगी। पैनल गंदे दिखें तो उस सुबह साफ़ करें; वरना धूल थमने का इंतज़ार करें।`,
    clear_week: () => "इस हफ़्ते धूल कम है, सफ़ाई का सामान्य समय ठीक है।" },
  dWhy: "दिल्ली में धूल से उत्पादन रोज़ 0.3–0.6% घट सकता है।", dSource: "बार दिन का औसत PM10 µg/m³ में दिखाते हैं; 100 से ऊपर भारत की सीमा से ज़्यादा है। अनुमान CAMS का, स्रोत", dDown: "धूल का अनुमान अभी उपलब्ध नहीं है।",
});

const tools = { states: null, q: { rid: null, view: null, timer: null, ran: false, chosen: null, seen: new Set() },
  s: { kw: 3, dcr: "yes", data: null }, plan: { timer: null, last: null }, care: { lists: null, gen: null, bill: null, support: null } };

// --- small helpers -------------------------------------------------------------------------------
function el(tag, cls, text) {
  const n = document.createElement(tag);
  if (cls) n.className = cls;
  if (text !== undefined && text !== null) n.textContent = text;
  return n;
}
function tx(v) { return v && typeof v === "object" ? (v[state.lang] || v.en) : v; }
function estimate() { return state.last || state.estimate || null; }
function host(url) { try { return new URL(url).hostname.replace(/^www\./, ""); } catch (_) { return url; } }
function niceDate(iso) {
  const d = new Date(iso + "T00:00:00");
  return isNaN(d) ? iso : d.toLocaleDateString(state.lang === "hi" ? "hi-IN" : "en-IN", { day: "numeric", month: "short", year: "numeric" });
}
async function copyText(text, btn, done) {
  try { await navigator.clipboard.writeText(text); btn.textContent = done; }
  catch (_) { btn.textContent = t("ppCopyFallback"); }
}
async function postJSON(path, body) {
  const r = await fetch(API + path, { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify(body) });
  const data = await r.json().catch(() => ({}));
  if (!r.ok) throw new Error(data.error || t("toolError"));
  return data;
}
async function loadStates() {
  if (tools.states) return tools.states;
  const data = await getJSON("/schemes?state=DL&kw=3");
  tools.states = data.states;
  return tools.states;
}
function fillStates(select, chosen) {
  const names = Object.entries(tools.states).map(([code, n]) => [code, tx(n)]).sort((a, b) => a[1].localeCompare(b[1]));
  select.innerHTML = "";
  for (const [code, name] of names) { const o = el("option", null, name); o.value = code; select.append(o); }
  select.value = chosen && tools.states[chosen] ? chosen : "DL";
}
function seg(id, value) {
  document.querySelectorAll(`#${id} button`).forEach((b) => b.setAttribute("aria-pressed", String(b.dataset.v === String(value))));
}

// --- Get quotes -----------------------------------------------------------------------------------
function verdictText(c) {
  if (c.verdict === "ok") return t("qOk");
  if (c.verdict === "amber") return t("qAmber", c.flags.filter((f) => f.level === "amber").length);
  if (c.flags.some((f) => f.code === "not_dcr" || f.code === "dcr_unstated")) return t("qRedDcr");
  if (c.flags.some((f) => f.code === "subsidy_overpromised")) return t("qRedOver");
  return t("qRed");
}

function term(dl, label, value, cls) {
  dl.append(el("dt", null, label));
  const dd = el("dd", cls || null, value);
  dl.append(dd);
}

function quoteCard(r, maxTotal, isBest, chosen) {
  const q = r.quote, c = r.check, sc = r.vendor.scorecard || {};
  const card = el("article", "qcard" + (isBest ? " best" : "") + (tools.q.seen.has(r.vendor_id) ? " revealed" : ""));
  card.style.animation = tools.q.seen.has(r.vendor_id) ? "none" : "";
  if (isBest) card.append(el("span", "ribbon", t("qBest")));
  const head = el("div", "q-name");
  const h3 = el("h3", null, r.vendor.name);
  if (r.vendor.demo) h3.append(el("span", "q-tag", t("qDemoTag")));
  head.append(h3);
  const meta = el("p", "q-meta");
  if (sc.portal_grade) meta.append(el("span", null, t("qGrade", sc.portal_grade)));
  if (sc.on_time_pct !== undefined) meta.append(el("span", null, t("qOnTime", sc.on_time_pct)));
  if (!r.vendor.demo) meta.append(el("span", null, t("qSent", sc.quotes_sent || 0)));
  head.append(meta);

  const price = el("div", "q-price");
  price.append(el("span", "q-net", rupees(c.net_rs)), el("span", "q-net-label", t("qAfter")));

  const bar = el("div", "pbar");
  bar.style.setProperty("--total", `${(100 * c.total_rs / maxTotal).toFixed(1)}%`);
  bar.style.setProperty("--net", `${(100 * c.net_rs / maxTotal).toFixed(1)}%`);
  bar.append(el("i", "net"), el("i", "sub"));
  bar.setAttribute("role", "img");
  bar.setAttribute("aria-label", `${t("qQuoted", rupees(c.total_rs))}, ${rupees(c.net_rs)} ${t("qAfter")}`);

  const split = el("dl", "q-split");
  term(split, t("qQuotedL"), rupees(c.total_rs));
  term(split, t("qSubsidyL"), c.subsidy_rs ? `−${rupees(c.subsidy_rs)}` : t("qNoSubsidy"), c.subsidy_rs ? "gain" : "loss");

  const verdict = el("p", "q-verdict");
  verdict.append(el("span", "sq " + c.verdict), el("span", null, verdictText(c)));

  const dl = el("dl", "q-terms");
  const dcr = q.dcr === "yes" ? [t("qMadeIn")] : q.dcr === "no" ? [t("qImported"), "bad"] : [t("qUnstated"), "bad"];
  term(dl, t("qPanels"), dcr[0], dcr[1]);
  if (q.advance_pct !== undefined && q.advance_pct !== null) {
    term(dl, t("qAdvance"), `${q.advance_pct}% (${rupees(c.pay_upfront_rs || 0)})`, q.advance_pct > 30 ? "warn" : null);
  }
  if (q.timeline_days) term(dl, t("qInstall"), t("qDays", q.timeline_days));
  if (q.module_performance_warranty_years) {
    term(dl, t("qWarranty"), t("qYears", q.module_performance_warranty_years, q.inverter_warranty_years || "–", q.system_warranty_years || "–"),
      (q.system_warranty_years || 0) < 5 ? "warn" : null);
  }
  term(dl, t("qNetMeter"), q.net_meter_included === "yes" ? t("qIncluded") : t("qNotIncluded"), q.net_meter_included === "yes" ? null : "warn");

  const btn = el("button", "btn " + (chosen === r.vendor_id ? "btn-primary" : "btn-line"), chosen === r.vendor_id ? t("qChosen") : t("qChoose"));
  btn.type = "button";
  btn.addEventListener("click", () => chooseVendor(r.vendor_id));

  card.append(head, price, bar, split, verdict, dl, btn);
  return card;
}

function waitCard() {
  const card = el("article", "qcard wait");
  card.append(el("div", "q-name"));
  const body = el("div", "wait-body");
  const dots = el("span", "dots");
  dots.append(el("i"), el("i"), el("i"));
  body.append(dots, el("span", null, t("qWait")));
  card.append(body);
  return card;
}

function house(on) {
  const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
  svg.setAttribute("viewBox", "0 0 16 16");
  svg.setAttribute("shape-rendering", "crispEdges");
  svg.innerHTML = '<path d="M8 1l7 6h-2v8H3V7H1z"/>';
  svg.setAttribute("class", on ? "on" : "off");
  return svg;
}

function renderBoard() {
  const v = tools.q.view;
  if (!v) return;
  const board = $("q-board");
  const quotes = v.quotes;
  const maxTotal = Math.max(1, ...quotes.map((r) => r.check.total_rs));
  const rec = v.pending === 0 ? v.recommendation : null;
  board.innerHTML = "";
  for (const r of quotes) board.append(quoteCard(r, maxTotal, rec && rec.vendor_id === r.vendor_id, tools.q.chosen || v.request.chosen));
  for (let i = 0; i < v.pending; i++) board.append(waitCard());
  // reveal the after-subsidy price a beat after each card lands
  for (const r of quotes) {
    if (tools.q.seen.has(r.vendor_id)) continue;
    tools.q.seen.add(r.vendor_id);
    const card = [...board.children].find((c) => c.querySelector("h3") && c.querySelector("h3").firstChild.textContent === r.vendor.name);
    if (card) requestAnimationFrame(() => setTimeout(() => card.classList.add("revealed"), 120));
  }
  $("q-head").hidden = false;
  const status = $("q-status");
  status.textContent = v.pending ? t("qWaiting", v.pending) : t("qDone", quotes.length);
  status.classList.toggle("waiting", v.pending > 0);

  const old = document.getElementById("q-trap");
  if (old) old.remove();
  const note = document.getElementById("q-chosen-note");
  if (note) note.remove();
  if (rec && rec.cheapest_is_trap) {
    const cheap = quotes.find((r) => r.vendor_id === rec.cheapest_vendor_id), best = quotes.find((r) => r.vendor_id === rec.vendor_id);
    const trap = el("p", "trap-note");
    trap.id = "q-trap";
    trap.append(el("span", "sq red"), el("span", null, t("qTrap", cheap.vendor.name, best.vendor.name)));
    board.after(trap);
  }
  if (tools.q.chosen || v.request.chosen) {
    const p = el("p", "trap-note");
    p.id = "q-chosen-note";
    p.classList.add("ok-note");
    p.append(el("span", "sq ok"), el("span", null, t("qChosenNote")));
    (document.getElementById("q-trap") || board).after(p);
  }
  const g = v.request.group;
  $("q-foot").hidden = false;
  const meter = $("q-group");
  meter.innerHTML = "";
  if (g) {
    const houses = el("span", "houses");
    for (let i = 0; i < g.needed; i++) houses.append(house(i < g.homes));
    meter.append(houses, el("span", null, g.discount_pct ? t("qGroupOn", g.homes, g.pincode, g.discount_pct) : t("qGroup", Math.min(g.homes, g.needed), g.needed, g.pincode)));
  }
}

async function pollQuotes() {
  clearTimeout(tools.q.timer);
  if (!tools.q.rid) return;
  try {
    tools.q.view = await getJSON(`/market/requests/${tools.q.rid}`);
  } catch (_) { return; }
  renderBoard();
  if (tools.q.view.pending) tools.q.timer = setTimeout(pollQuotes, Math.max(700, (tools.q.view.next_in || 1) * 1000 + 150));
}

async function requestQuotes(e) {
  if (e) e.preventDefault();
  const err = $("q-error");
  err.hidden = true;
  const kw = parseFloat($("q-kw").value), pin = $("q-pin").value.trim();
  if (!(kw >= 1 && kw <= 10)) { err.textContent = t("qBadKw"); err.hidden = false; return; }
  if (pin && !/^[1-9]\d{5}$/.test(pin)) { err.textContent = t("qBadPin"); err.hidden = false; return; }
  clearTimeout(tools.q.timer);
  tools.q.seen = new Set();
  tools.q.chosen = null;
  try {
    tools.q.view = await postJSON("/market/requests", { state: $("q-state").value, kw, pincode: pin, sample: !e });
    tools.q.rid = tools.q.view.request.id;
    renderBoard();
    tools.q.timer = setTimeout(pollQuotes, Math.max(700, (tools.q.view.next_in || 1) * 1000 + 150));
  } catch (ex) { err.textContent = ex.message; err.hidden = false; }
}

async function chooseVendor(vendorId) {
  try {
    await postJSON(`/market/requests/${tools.q.rid}/choose`, { vendor_id: vendorId });
    tools.q.chosen = vendorId;
    renderBoard();
  } catch (ex) { $("q-error").textContent = ex.message; $("q-error").hidden = false; }
}

async function deleteComparison() {
  if (!tools.q.rid) return;
  clearTimeout(tools.q.timer);
  await fetch(`${API}/market/requests/${tools.q.rid}`, { method: "DELETE" }).catch(() => null);
  tools.q = { ...tools.q, rid: null, view: null, chosen: null, seen: new Set() };
  $("q-board").innerHTML = "";
  ["q-trap", "q-chosen-note"].forEach((id) => { const n = document.getElementById(id); if (n) n.remove(); });
  $("q-head").hidden = false;
  $("q-status").textContent = t("qDeleted");
  $("q-status").classList.remove("waiting");
  $("q-foot").hidden = true;
}

async function openQuotes() {
  await loadStates();
  const est = estimate();
  if (!$("q-state").options.length) fillStates($("q-state"), "DL");
  if (est && est.analysis && est.analysis.recommended) $("q-kw").value = Math.min(10, Math.max(1, est.analysis.recommended.kw));
  if (!tools.q.ran) { tools.q.ran = true; requestQuotes(); }
  else if (tools.q.rid) pollQuotes();  // pick up quotes vendors sent while the household was away
}

// scam check
function renderScam(data) {
  const out = $("scam-out");
  const v = data.views[state.lang] || data.views.en;
  const order = { red: 0, amber: 1, note: 2 };
  const levels = data.flags.map((f) => f.level).sort((a, b) => order[a] - order[b]);
  out.innerHTML = "";
  const title = el("p", "scam-title");
  title.append(el("span", "sq " + v.verdict), el("span", null, v.title));
  const ul = el("ul");
  v.signs.forEach((s, i) => { const li = el("li"); li.append(el("span", "sq " + (levels[i] || "note")), el("span", null, s)); ul.append(li); });
  out.append(title);
  if (v.signs.length) out.append(ul);
  out.append(el("p", "hint", v.always));
  out.hidden = false;
}
async function checkScam(e) {
  if (e) e.preventDefault();
  const text = $("scam-text").value.trim();
  if (!text) { $("scam-out").hidden = false; $("scam-out").textContent = t("scamEmpty"); return; }
  try { tools.scam = await postJSON("/scam-check", { text }); renderScam(tools.scam); }
  catch (ex) { $("scam-out").hidden = false; $("scam-out").textContent = ex.message; }
}

// --- Schemes --------------------------------------------------------------------------------------
function topUpFor(scheme, kw) {
  const c = scheme.calc || {};
  if (c.type === "per_kw") return Math.min(kw * c.per_kw, c.cap || Infinity, c.max_kw ? c.max_kw * c.per_kw : Infinity);
  if (c.type === "flat") return c.amount;
  return 0;
}

function renderSchemes() {
  const d = tools.s.data;
  if (!d) return;
  const stateName = tx(d.states[d.state]);
  const out = $("s-out");
  out.innerHTML = "";
  const central = d.dcr === "no" ? 0 : d.potential_central_rs;
  const stateCards = d.schemes.filter((s) => s.scope === d.state && s.kind === "state");
  const topups = stateCards.map((s) => ({ s, amount: topUpFor(s, d.kw) })).filter((x) => x.amount > 0);
  const topup = topups.length ? Math.max(...topups.map((x) => x.amount)) : 0;

  out.append(el("p", "big-label", t("sCentralFor", d.kw)));
  out.append(el("p", "big-amount" + (central ? "" : " zero"), rupees(central)));
  const total = central + topup || 1;
  const bar = el("div", "sbar");
  const ci = el("i", "c"); ci.style.width = `${(100 * central / total).toFixed(1)}%`;
  const si = el("i", "s"); si.style.width = `${(100 * topup / total).toFixed(1)}%`;
  bar.append(ci, si);
  out.append(bar);
  const rows = el("dl", "legend-rows");
  const row = (cls, label, value) => { const r = el("div"); r.append(el("span", "sw " + cls), el("dt", null, label), el("dd", null, value)); rows.append(r); };
  row("c", t("sCentralFor", d.kw), rupees(central));
  if (topup) row("s", t("sTopUp", stateName), rupees(topup));
  out.append(rows);
  const notes = [];
  if (d.dcr === "no") notes.push(t("sNoDcr"));
  else if (d.dcr === "not_stated") notes.push(t("sUnsure"));
  if (topup && central) notes.push(t("sTogether", rupees(central + topup)));
  if (stateCards.some((s) => (s.calc || {}).type === "zero_upfront")) notes.push(t("sZero"));
  if (!topup && !stateCards.some((s) => (s.calc || {}).type === "zero_upfront")) {
    notes.push(d.topup_reviewed ? t("sNoTopUp", stateName) : t("sNotReviewed", stateName));
  }
  for (const n of notes) out.append(el("p", "calc-note", n));

  // national help first, then the selected state's; rows keep amounts and sources aligned
  const nation = d.schemes.filter((s) => s.scope !== d.state), local = d.schemes.filter((s) => s.scope === d.state);
  const wrap = $("s-cards");
  wrap.innerHTML = "";
  for (const [title, list] of [[t("sAcross"), nation], [t("sIn", stateName), local]]) {
    if (!list.length) continue;
    const sec = el("section", "scheme-group");
    sec.append(el("h2", null, title));
    const rows = el("div", "scheme-list");
    for (const s of list) {
      const row = el("article", "srow" + (s.kind === "none" ? " none" : ""));
      const main = el("div", "srow-main");
      main.append(el("h3", null, tx(s.title)), el("p", "who", tx(s.who)));
      const src = el("p", "src");
      const a = el("a", null, s.official ? t("sOfficial") : `${t("sSource")}: ${host(s.source)}`);
      a.href = s.source; a.target = "_blank"; a.rel = "noopener";
      src.append(a, el("span", null, t("sChecked", niceDate(s.checked_on))));
      row.append(main, el("p", "amt", tx(s.amount)), src);
      rows.append(row);
    }
    sec.append(rows);
    wrap.append(sec);
  }
}

async function loadSchemes() {
  const st = $("s-state").value || "DL";
  try {
    const d = await getJSON(`/schemes?state=${encodeURIComponent(st)}&kw=${tools.s.kw}&dcr=${tools.s.dcr}`);
    tools.s.data = { ...d, dcr: tools.s.dcr };
    renderSchemes();
    planSoon();
  } catch (_) { $("s-out").textContent = t("toolError"); }
}

function planChart(p) {
  const W = 360, H = 150, top = 12, bottom = 22, n = 12, slot = (W - 8) / n;
  const max = Math.max(p.emi_before_rs, p.monthly_saving_rs, 1) * 1.15;
  const y = (v) => top + (H - top - bottom) * (1 - v / max);
  let s = `<line x1="0" x2="${W}" y1="${H - bottom}" y2="${H - bottom}" stroke="var(--line-strong)"/>`;
  for (let m = 1; m <= n; m++) {
    const emi = m <= p.delay_months ? p.emi_before_rs : p.emi_after_rs;
    const x = 4 + (m - 1) * slot + slot * 0.18, w = slot * 0.64;
    s += `<rect x="${x.toFixed(1)}" y="${y(emi).toFixed(1)}" width="${w.toFixed(1)}" height="${(H - bottom - y(emi)).toFixed(1)}" fill="${m <= p.delay_months ? "var(--panel)" : "var(--green)"}"><title>${rupees(emi)}</title></rect>`;
    s += `<text x="${(x + w / 2).toFixed(1)}" y="${H - 7}" text-anchor="middle">${m}</text>`;
  }
  if (p.monthly_saving_rs) {
    const ys = y(p.monthly_saving_rs).toFixed(1);
    s += `<line x1="0" x2="${W}" y1="${ys}" y2="${ys}" stroke="var(--sun)" stroke-width="2" stroke-dasharray="6 4"/>`;
  }
  if (p.delay_months > 0 && p.delay_months < n) {
    const xm = (4 + p.delay_months * slot).toFixed(1);
    s += `<line x1="${xm}" x2="${xm}" y1="${top - 4}" y2="${H - bottom}" stroke="var(--ink)" stroke-width="1"/>`;
    s += `<text x="${(+xm + 4).toFixed(1)}" y="${top + 6}" style="fill:var(--ink);font-weight:600">${t("pArrives")}</text>`;
  }
  return `<svg viewBox="0 0 ${W} ${H}" role="img" aria-label="${t("pTitle")}">${s}</svg>`;
}

function renderPlan() {
  const p = tools.plan.last, out = $("p-out");
  if (!p) return;
  out.innerHTML = "";
  const figs = el("dl", "figs");
  const fig = (label, value, cls) => { const d = el("div"); d.append(el("dt", null, label), el("dd", cls || null, value)); figs.append(d); };
  fig(t("pCash"), rupees(p.cash_before_install_rs));
  fig(t("pWaitCash"), rupees(p.cash_during_wait_rs), p.delay_months >= 6 ? "bad" : null);
  fig(t("pEmiBefore"), rupees(p.emi_before_rs), p.net_monthly_before_rs < 0 ? "bad" : null);
  fig(t("pEmiAfter"), rupees(p.emi_after_rs), "good");
  const chart = el("div", "cash-chart");
  chart.innerHTML = planChart(p);
  const legend = el("p", "chart-legend");
  const key = (color, label) => { const s = el("span"); const i = el("i"); i.style.background = color; s.append(i, document.createTextNode(label)); legend.append(s); };
  key("var(--panel)", t("pEmiLegend"));
  key("var(--green)", t("pAfterLegend"));
  key("var(--sun)", t("pSaveLegend"));
  out.append(figs, chart, legend, el("p", "calc-note", `${t("pInterest", rupees(p.interest_during_wait_rs))} ${t("pNote")}`));
}

async function runPlan() {
  const d = tools.s.data;
  const body = {
    cost_rs: parseFloat($("p-cost").value), monthly_saving_rs: parseFloat($("p-saving").value) || 0,
    margin_pct: parseFloat($("p-own").value), rate_pct: parseFloat($("p-rate").value), years: 10,
    delay_months: parseInt($("p-wait").value, 10), kw: tools.s.kw, state: d ? d.state : "DL", dcr: tools.s.dcr,
  };
  $("p-wait-v").textContent = body.delay_months;
  try { tools.plan.last = await postJSON("/finance/plan", body); renderPlan(); }
  catch (ex) { $("p-out").textContent = ex.message || t("pBad"); }
}
function planSoon() { clearTimeout(tools.plan.timer); tools.plan.timer = setTimeout(runPlan, 200); }

async function openSchemes() {
  await loadStates();
  if (!$("s-state").options.length) fillStates($("s-state"), "DL");
  const est = estimate();
  if (est && est.analysis && est.analysis.recommended && !tools.s.prefilled) {
    const o = est.analysis.recommended;
    tools.s.prefilled = true;
    tools.s.kw = o.kw <= 1 ? 1 : o.kw <= 2 ? 2 : o.kw <= 3 ? 3 : 5;
    seg("s-kw", tools.s.kw);
    $("p-cost").value = Math.round(o.gross_cost / 1000) * 1000;
    $("p-saving").value = Math.round(o.savings_rs / 12 / 100) * 100;
  }
  if (!tools.s.data) loadSchemes();
}

// --- After installation ---------------------------------------------------------------------------
const PASSPORT_KEY = "surya-passport";
function passportTicks() { try { return new Set(JSON.parse(localStorage.getItem(PASSPORT_KEY) || "[]")); } catch (_) { return new Set(); } }
function savePassport(ticks) { try { localStorage.setItem(PASSPORT_KEY, JSON.stringify([...ticks])); } catch (_) { /* fine without it */ } }

function renderPassport() {
  const lists = tools.care.lists;
  if (!lists) return;
  const ticks = passportTicks();
  const wrap = $("pp-groups");
  wrap.innerHTML = "";
  let total = 0;
  for (const g of lists.groups) {
    const box = el("div", "pp-group");
    box.append(el("h3", null, tx(g.title)));
    for (const item of g.items) {
      total++;
      const id = `${g.id}.${item.id}`;
      const label = el("label", "pp-item");
      const cb = el("input");
      cb.type = "checkbox";
      cb.checked = ticks.has(id);
      cb.addEventListener("change", () => { const s = passportTicks(); cb.checked ? s.add(id) : s.delete(id); savePassport(s); updateRing(); });
      label.append(cb, el("span", null, tx(item.text)));
      box.append(label);
    }
    wrap.append(box);
  }
  tools.care.total = total;
  updateRing();
}
function updateRing() {
  const done = passportTicks().size, total = tools.care.total || 1;
  $("pp-count").textContent = t("ppDone", Math.min(done, total), total);
  $("pp-ring").style.strokeDashoffset = (113.1 * (1 - Math.min(done, total) / total)).toFixed(1);
}
function passportText() {
  const ticks = passportTicks();
  return [t("ppTitle"), ""].concat(tools.care.lists.groups.flatMap((g) => [tx(g.title), ...g.items.map((i) => `${ticks.has(`${g.id}.${i.id}`) ? "✓" : "☐"} ${tx(i.text)}`), ""])).join("\n");
}

function gauge(pct, status) {
  const r = 52, len = Math.PI * r, shown = Math.min(pct, 120) / 120;
  const color = status === "on_track" ? "var(--green)" : pct >= 75 ? "var(--sun)" : "var(--stop)";
  return `<svg viewBox="0 0 132 76" aria-hidden="true"><path class="gauge-track" d="M14 66a52 52 0 0 1 104 0"/>` +
    `<path class="gauge-fill" d="M14 66a52 52 0 0 1 104 0" stroke="${color}" stroke-dasharray="${len.toFixed(1)}" stroke-dashoffset="${(len * (1 - shown)).toFixed(1)}"/></svg>`;
}
function renderGen() {
  const g = tools.care.gen, out = $("g-out");
  if (!g) return;
  out.innerHTML = "";
  const box = el("div", "gauge");
  const svgWrap = el("div");
  svgWrap.innerHTML = gauge(g.pct, g.status);
  const text = el("div");
  text.append(el("p", "gauge-num", `${g.pct}%`), el("p", "gauge-sub", t("gOf", g.actual_kwh, g.promised_kwh)));
  const v = el("p", "q-verdict");
  v.append(el("span", "sq " + (g.status === "on_track" ? "ok" : "amber")), el("span", null, g.status === "on_track" ? t("gOnTrack") : `${t("gReview")}: ${t("gShort", g.shortfall_kwh)}`));
  text.append(v);
  box.append(svgWrap, text);
  out.append(box);
  if (g.status !== "on_track") {
    out.append(el("p", "calc-note", t("gDust")));
    out.append(el("p", "panel-title", t("gDraft")));
    const ta = el("textarea", "draft");
    ta.value = tx(g.draft);
    ta.readOnly = true;
    const btn = el("button", "btn btn-line btn-sm", t("copy"));
    btn.type = "button";
    btn.addEventListener("click", () => copyText(ta.value, btn, t("copied")));
    out.append(ta, btn);
  }
  out.hidden = false;
}

function flowSvg(b) {
  const max = Math.max(b.generation_kwh, b.import_kwh, 1), w = (v) => Math.max(2, 26 * v / max);
  const self = b.self_consumed_kwh, exp = b.export_kwh, imp = b.import_kwh;
  return `<svg viewBox="0 0 360 172" role="img" aria-label="${t("bSelf")}: ${self} kWh">` +
    `<path d="M92 104 H140" stroke="var(--green)" stroke-width="${w(self).toFixed(1)}"/>` +
    `<path d="M60 82 C60 18, 300 18, 300 82" stroke="var(--sun)" stroke-width="${w(exp).toFixed(1)}"/>` +
    `<path d="M268 104 H220" stroke="var(--panel)" stroke-width="${w(imp).toFixed(1)}"/>` +
    `<rect class="node" x="12" y="82" width="80" height="46" rx="6"/><rect class="node" x="140" y="82" width="80" height="46" rx="6"/><rect class="node" x="268" y="82" width="80" height="46" rx="6"/>` +
    `<text x="52" y="102">${t("bSolar")}</text><text x="52" y="119" class="v">${b.generation_kwh} kWh</text>` +
    `<text x="180" y="102">${t("bHome")}</text><text x="180" y="119" class="v">${b.household_use_kwh} kWh</text>` +
    `<text x="308" y="102">${t("bGrid")}</text><text x="308" y="119" class="v">−${exp} / +${imp}</text>` +
    `<text x="180" y="30" class="v">${exp} kWh</text><text x="116" y="150" class="v">${self} kWh</text><text x="244" y="150" class="v">${imp} kWh</text></svg>`;
}
function renderBill() {
  const b = tools.care.bill, out = $("b-out");
  if (!b) return;
  out.innerHTML = "";
  const flow = el("div", "flow");
  flow.innerHTML = flowSvg(b);
  const dl = el("dl", "balance");
  const row = (label, value, flag) => { const d = el("div"); d.style.display = "contents"; if (flag) d.className = "flag"; d.append(el("dt", null, label), el("dd", null, value)); dl.append(d); };
  row(t("bSelf"), `${b.self_consumed_kwh} kWh`);
  row(t("bTotal"), `${b.household_use_kwh} kWh`);
  row(t("bNet"), `${b.net_grid_kwh} kWh`);
  if (b.status === "review") row(t("bDiff"), `${b.meter_bill_difference_kwh} kWh`, true);
  out.append(flow, dl);
  if (b.status !== "review") out.append(el("p", "calc-note", t("bMatched")));
  out.hidden = false;
}

function renderSupport() {
  const r = tools.care.support, out = $("sp-out");
  out.innerHTML = "";
  if (!r || r.kind !== $("sp-kind").value) {
    // before the note is prepared: who to contact and what to attach for the chosen problem
    const topic = tools.care.lists && tools.care.lists.support_topics.find((x) => x.id === $("sp-kind").value);
    if (!topic) return;
    out.append(el("h3", null, tx(topic.title)), el("p", "sp-who", t("spWho", tx(topic.who))), el("p", "panel-title", t("spEvidence")));
    const ul = el("ul", "evidence");
    for (const e of topic.evidence) { const li = el("li"); li.append(el("span", "sq"), el("span", null, tx(e))); ul.append(li); }
    out.append(ul, el("p", "hint", t("spSoon")));
    return;
  }
  out.append(el("h3", null, tx(r.title)));
  if (r.days_since_contact !== null && r.days_since_contact !== undefined) out.append(el("p", "hint", t("spDays", r.days_since_contact)));
  out.append(el("p", "panel-title", t("spEvidence")));
  const ul = el("ul", "evidence");
  for (const e of r.evidence) { const li = el("li"); li.append(el("span", "sq"), el("span", null, tx(e))); ul.append(li); }
  out.append(ul, el("p", "panel-title", t("spDraft")));
  const ta = el("textarea", "draft");
  ta.value = tx(r.draft);
  ta.readOnly = true;
  const btn = el("button", "btn btn-line btn-sm", t("copy"));
  btn.type = "button";
  btn.addEventListener("click", () => copyText(ta.value, btn, t("copied")));
  out.append(ta, btn);
  out.hidden = false;
}

function fillSupportKinds() {
  const sel = $("sp-kind"), current = sel.value;
  sel.innerHTML = "";
  for (const topic of tools.care.lists.support_topics) { const o = el("option", null, tx(topic.title)); o.value = topic.id; sel.append(o); }
  if (current) sel.value = current;
}

async function openCare() {
  if (!tools.care.dust) loadDust(state.lat, state.lon);
  if (!tools.care.lists) {
    try { tools.care.lists = await getJSON("/care/checklists"); } catch (_) { return; }
    renderPassport();
    fillSupportKinds();
    renderSupport();
    const now = new Date();
    const prev = new Date(now.getFullYear(), now.getMonth() - 1, 1);
    $("g-month").value = `${prev.getFullYear()}-${String(prev.getMonth() + 1).padStart(2, "0")}`;
    $("g-month").max = $("g-month").value;
    const week = new Date(now - 7 * 864e5);
    $("sp-noticed").value = week.toISOString().slice(0, 10);
    $("sp-noticed").max = $("sp-contacted").max = $("g-clean").max = now.toISOString().slice(0, 10);
    const est = estimate();
    if (est && est.analysis && est.analysis.recommended) $("g-kw").value = est.analysis.recommended.kw;
  }
}


// --- dust this week -------------------------------------------------------------------------------
function dayName(iso, opts) { return new Date(iso + "T00:00:00").toLocaleDateString(state.lang === "hi" ? "hi-IN" : "en-IN", opts); }
function renderDust() {
  const d = tools.care.dust, wrap = $("d-days"), advice = $("d-advice");
  if (!d) return;
  wrap.innerHTML = "";
  // bars and numbers show the day's PM10 average, the same measure that sets its level
  const val = (x) => x.pm10 ?? 0;
  const max = Math.max(300, ...d.days.map(val));
  for (const day of d.days) {
    const box = el("div", `dday ${day.level}` + (day.date === d.clean_on ? " clean" : ""));
    if (day.date === d.clean_on) box.append(el("span", "tag-clean", t("dClean")));
    const bar = el("i", "dbar");
    bar.style.height = `${Math.max(6, Math.round(100 * val(day) / max))}%`;
    bar.title = `PM10 ${day.pm10 ?? "–"} µg/m³, desert dust up to ${day.dust_max ?? "–"} µg/m³`;
    box.append(el("span", "dname", dayName(day.date, { weekday: "short" })), el("span", "ddate", dayName(day.date, { day: "numeric", month: "short" })),
      bar, el("span", "dlevel", t("dLevels")[day.level]), el("span", "dval", String(val(day))));
    wrap.append(box);
  }
  advice.innerHTML = "";
  const when = d.clean_on ? dayName(d.clean_on, { weekday: "long", day: "numeric", month: "long" }) : "";
  advice.append(el("span", "sq " + (d.advice === "dusty_week" || d.advice === "clean_lull" ? "amber" : "ok")), el("span", null, t("dAdvice")[d.advice](when)));
}
async function loadDust(lat, lon) {
  const q = lat !== null && lat !== undefined ? `?lat=${lat}&lon=${lon}` : "";
  try { tools.care.dust = await getJSON(`/care/dust${q}`); renderDust(); renderHomeDust(); }
  catch (_) { $("d-advice").textContent = t("dDown"); }
}
$("d-locate").addEventListener("click", () => {
  if (!navigator.geolocation) return;
  navigator.geolocation.getCurrentPosition((p) => {
    state.lat = Math.round(p.coords.latitude * 100) / 100;
    state.lon = Math.round(p.coords.longitude * 100) / 100;
    loadDust(state.lat, state.lon);
  }, () => { $("d-advice").textContent = t("locationOff"); }, { timeout: 10000 });
});


// the home page's mini forecast: the same live data, bars only
function renderHomeDust() {
  const d = tools.care.dust, wrap = document.getElementById("home-dust");
  if (!d || !wrap) return;
  wrap.innerHTML = "";
  const val = (x) => x.pm10 ?? 0, max = Math.max(300, ...d.days.map(val));
  for (const day of d.days) {
    const box = el("div", `dday ${day.level}` + (day.date === d.clean_on ? " clean" : ""));
    if (day.date === d.clean_on) box.append(el("span", "tag-clean", t("dClean")));
    const bar = el("i", "dbar");
    bar.style.height = `${Math.max(6, Math.round(100 * val(day) / max))}%`;
    box.append(el("span", "dname", dayName(day.date, { weekday: "short" })), bar, el("span", "dlevel", t("dLevels")[day.level]));
    wrap.append(box);
  }
}


// --- for vendors ----------------------------------------------------------------------------------
tools.v = { list: [], rid: null };
function vendorQuote() {
  const num = (id) => { const v = parseFloat($(id).value); return Number.isFinite(v) ? v : undefined; };
  return {
    total_price_rs: num("vq-total"), gst_included: $("vq-gst").value, system_kw: num("vq-kw"), dcr: $("vq-dcr").value,
    module_watt: num("vq-watt"), module_count: num("vq-count"), inverter_kw: num("vq-inv"), advance_pct: num("vq-adv"),
    timeline_days: num("vq-days"), module_performance_warranty_years: num("vq-pw"), inverter_warranty_years: num("vq-iw"),
    system_warranty_years: num("vq-sw"), net_meter_included: $("vq-meter").value, structure_included: $("vq-structure").value,
    earthing_included: $("vq-earthing").value,
  };
}
function renderVendorCheck(res, sent) {
  const out = $("vq-out"), c = res.check, v = c.views[state.lang] || c.views.en;
  out.innerHTML = "";
  const title = el("p", "q-verdict");
  title.append(el("span", "sq " + c.verdict), el("span", null, v.title.replace(/^[^\p{L}\p{N}]+/u, "")));
  out.append(title, el("p", "q-net", rupees(c.net_rs)), el("p", "hint", t("vAfter")));
  const issues = [...v.red, ...v.amber];
  if (issues.length) {
    const ul = el("ul", "evidence");
    for (const i of issues) { const li = el("li"); li.append(el("span", "sq " + (v.red.includes(i) ? "red" : "amber")), el("span", null, i)); ul.append(li); }
    out.append(ul);
  }
  if (sent) out.append(el("p", "trap-note ok-note", t("vSent")));
  out.hidden = false;
}
function renderVendorList() {
  const list = $("v-list");
  list.innerHTML = "";
  const st = $("v-status");
  st.hidden = false;
  const real = tools.v.list.filter((r) => !r.sample).length;
  st.textContent = real ? t("vOpen", real) : tools.v.list.length ? t("vSampleOnly") : t("vNone");
  for (const r of tools.v.list) {
    const row = el("div", "vrow" + (r.id === tools.v.rid ? " active" : ""));
    const where = el("div", "vwhere");
    where.append(el("b", null, r.discom || tx(tools.states && tools.states[r.state]) || r.state), el("span", null, t("vArea", r.area)));
    if (r.sample) where.append(el("span", "vsample", t("vSample")));
    const mins = Math.max(0, Math.round((Date.now() / 1000 - r.created) / 60));
    const btn = el("button", "btn " + (r.you_quoted ? "btn-quiet" : "btn-line"), r.you_quoted ? t("vQuoted") : t("vQuote"));
    btn.type = "button";
    btn.disabled = r.you_quoted;
    btn.addEventListener("click", () => openVendorQuote(r));
    const count = el("span", "vcount");
    count.append(el("span", null, t("vQuotes", r.quotes)), el("span", null, t("vAgo", mins)));
    row.append(el("span", "vkw", `${r.kw} kW`), where, count, btn);
    list.append(row);
  }
}
async function loadVendorRequests(e) {
  if (e) e.preventDefault();
  const err = $("v-error");
  err.hidden = true;
  const name = $("v-name").value.trim();
  try {
    const d = await getJSON(`/market/open?state=${encodeURIComponent($("v-state").value)}` + (name ? `&vendor=${encodeURIComponent(name)}` : ""));
    tools.v.list = d.requests;
    renderVendorList();
  } catch (ex) { err.textContent = ex.message; err.hidden = false; }
}
function openVendorQuote(r) {
  tools.v.rid = r.id;
  $("v-quote").hidden = false;
  $("vq-out").hidden = true;
  $("v-quote-title").textContent = t("vQuoteTitle", r.kw, r.discom);
  $("vq-kw").value = r.kw;
  $("vq-inv").value = r.kw;
  $("vq-count").value = Math.ceil(r.kw * 1000 / (parseFloat($("vq-watt").value) || 545));
  if (!$("vq-total").value) $("vq-total").value = Math.round(r.kw * 65000 / 1000) * 1000;
  renderVendorList();
  $("v-quote").scrollIntoView({ behavior: "smooth", block: "start" });
}
$("v-form").addEventListener("submit", loadVendorRequests);
$("v-state").addEventListener("change", () => loadVendorRequests());
$("vq-preview").addEventListener("click", async () => {
  try { renderVendorCheck(await postJSON("/market/preview", { state: $("v-state").value, name: $("v-name").value.trim() || "Your quote", quote: vendorQuote() }), false); }
  catch (ex) { $("vq-out").hidden = false; $("vq-out").textContent = ex.message; }
});
$("vq-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  if (!tools.v.rid) return;
  if (!$("v-name").value.trim()) {
    $("vq-out").hidden = false;
    $("vq-out").textContent = t("vNoName");
    $("v-name").focus();
    return;
  }
  try {
    const res = await postJSON(`/market/requests/${tools.v.rid}/quotes`, { vendor_name: $("v-name").value.trim(), quote: vendorQuote() });
    renderVendorCheck(res, true);
    const row = tools.v.list.find((x) => x.id === tools.v.rid);
    if (row) { row.you_quoted = true; row.quotes += 1; }
    renderVendorList();
  } catch (ex) { $("vq-out").hidden = false; $("vq-out").textContent = ex.message; }
});
async function openVendors() {
  await loadStates();
  if (!$("v-state").options.length) fillStates($("v-state"), "DL");
  loadVendorRequests();
}


// --- panel label check ----------------------------------------------------------------------------
function deviceId() {
  try {
    let id = localStorage.getItem("surya-device");
    if (!id) { id = Array.from(crypto.getRandomValues(new Uint8Array(12)), (b) => b.toString(16).padStart(2, "0")).join(""); localStorage.setItem("surya-device", id); }
    return id;
  } catch (_) { return tools.sessionId || (tools.sessionId = String(Math.random()).slice(2)); }
}
function renderPanel() {
  const p = tools.care.panel, out = $("pl-out");
  out.innerHTML = "";
  if (!p) {
    const img = el("img", "pl-thumb");
    img.src = "sample-panel-ok.png";
    img.alt = t("plAlt");
    out.append(img, el("p", "hint", t("plWhere")));
    return;
  }
  const img = el("img", "pl-thumb");
  img.src = p.url;
  img.alt = "";
  out.append(img);
  const v = p.res.views[state.lang] || p.res.views.en;
  if (v.head) out.append(el("p", "pl-head", v.head.replace(/^[^\p{L}\p{N}]+/u, "")));
  const title = el("p", "q-verdict");
  title.append(el("span", "sq " + v.verdict), el("span", null, v.title.replace(/^[^\p{L}\p{N}]+/u, "")));
  out.append(title);
  if (v.lines.length) {
    const ul = el("ul", "evidence");
    v.lines.forEach((line, i) => { const li = el("li"); li.append(el("span", "sq " + (v.levels[i] || "amber")), el("span", null, line)); ul.append(li); });
    out.append(ul);
  }
  if (v.next) out.append(el("p", "calc-note", v.next));
  out.hidden = false;
}
async function checkPanel(b64, type, url, sample) {
  const out = $("pl-out");
  out.hidden = false;
  out.innerHTML = "";
  out.append(el("p", "board-status waiting", t("plReading")));
  try {
    const watt = parseFloat($("pl-watt").value);
    const res = await postJSON("/panel", { file_base64: b64, media_type: type, owner: deviceId(), expect_watt: Number.isFinite(watt) ? watt : undefined, sample });
    tools.care.panel = { res, url };
    renderPanel();
  } catch (ex) { out.textContent = ex.message; }
}
async function samplePanel(name) {
  const blob = await (await fetch(name)).blob();
  checkPanel(await toBase64(blob), "image/png", name, true);
}
$("pl-ok").addEventListener("click", () => samplePanel("sample-panel-ok.png"));
$("pl-bad").addEventListener("click", () => samplePanel("sample-panel-imported.png"));
$("pl-file").addEventListener("change", async (e) => {
  const file = e.target.files[0];
  e.target.value = "";
  if (!file) return;
  try { const { b64, type } = await prepare(file); checkPanel(b64, type, URL.createObjectURL(file), false); }
  catch (ex) { $("pl-out").hidden = false; $("pl-out").textContent = ex.message; }
});

// --- wiring ---------------------------------------------------------------------------------------
$("q-form").addEventListener("submit", requestQuotes);
$("q-delete").addEventListener("click", deleteComparison);
$("scam-form").addEventListener("submit", checkScam);
$("scam-example").addEventListener("click", () => { $("scam-text").value = t("scamSample"); checkScam(); });
$("s-state").addEventListener("change", loadSchemes);
document.querySelectorAll("#s-kw button").forEach((b) => b.addEventListener("click", () => { tools.s.kw = +b.dataset.v; seg("s-kw", tools.s.kw); loadSchemes(); }));
document.querySelectorAll("#s-dcr button").forEach((b) => b.addEventListener("click", () => { tools.s.dcr = b.dataset.v; seg("s-dcr", tools.s.dcr); loadSchemes(); }));
$("p-form").addEventListener("input", planSoon);
$("p-form").addEventListener("submit", (e) => e.preventDefault());
$("pp-copy").addEventListener("click", () => copyText(passportText(), $("pp-copy"), t("ppCopied")));
$("g-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  try {
    tools.care.gen = await postJSON("/care/check", { month: $("g-month").value, kw: parseFloat($("g-kw").value), actual_kwh: parseFloat($("g-actual").value),
      promised_kwh: parseFloat($("g-promised").value), last_cleaned: $("g-clean").value || undefined });
    renderGen();
  } catch (ex) { $("g-out").hidden = false; $("g-out").textContent = ex.message; }
});
$("b-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  try {
    tools.care.bill = await postJSON("/care/bill", { generation_kwh: parseFloat($("b-gen").value), import_kwh: parseFloat($("b-import").value),
      export_kwh: parseFloat($("b-export").value), bill_export_kwh: parseFloat($("b-billexport").value) });
    renderBill();
  } catch (ex) { $("b-out").hidden = false; $("b-out").textContent = ex.message; }
});
$("sp-kind").addEventListener("change", renderSupport);
$("sp-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  try {
    const kind = $("sp-kind").value;
    tools.care.support = { ...await postJSON("/care/support", { kind, first_noticed: $("sp-noticed").value, contacted_on: $("sp-contacted").value || undefined }), kind };
    renderSupport();
  } catch (ex) { $("sp-out").hidden = false; $("sp-out").textContent = ex.message; }
});

window.productRoute = (view) => {
  if (view === "quotes") openQuotes();
  else if (view === "schemes") openSchemes();
  else if (view === "care") openCare();
  else if (view === "vendors") openVendors();
};
window.renderProduct = () => {
  if (tools.states) { fillStates($("q-state"), $("q-state").value); fillStates($("s-state"), $("s-state").value); if ($("v-state").options.length) fillStates($("v-state"), $("v-state").value); }
  if (tools.v && tools.v.list.length) renderVendorList();
  if (tools.q.view) renderBoard();
  if (tools.scam) renderScam(tools.scam);
  renderSchemes();
  renderPlan();
  if (tools.care.lists) { renderPassport(); fillSupportKinds(); }
  renderGen(); renderBill(); renderSupport(); renderDust(); renderHomeDust(); renderPanel();
};
loadDust(state.lat, state.lon);  // feeds the home page's mini forecast and the After install page
const firstView = (location.hash || "").replace("#", "");
if (["quotes", "schemes", "care", "vendors"].includes(firstView)) window.productRoute(firstView);

applyLang();  // app.js applied the language before these strings existed
