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
    whySub: "Every size compared over 25 years. Net value today is 25 years of savings minus the cost, discounted at 8% a year. If a smaller size comes within 10% of the best value, we recommend it: nearly the same gain for less money upfront.",
    cols: ["Size", "After subsidy", "Saves / yr", "Payback", "Net value today"],
    never: "never",
    readTitle: "What we read from your bill",
    provider: "Provider",
    load: "Sanctioned load",
    months: "Months of usage",
    amount: "This month's charges",
    conservative: "Sunlight uses the lower estimate from PVGIS and NASA. Real output and savings still vary with weather, outages, shading, maintenance and your tariff.",
    again: "← Start again",
    error: "Something went wrong. Please try again.",
    tooBig: "That file is too big. Please send a photo or a PDF under 4 MB.",
    footer: "Built on AWS for WeMakeDevs × AWS Environmental Hacks",
    privacyLink: "Privacy",
    quoteTitle: "Got a vendor's quote? Check it before you sign",
    quoteSub: "Catches the traps that cost households their subsidy: non-DCR panels, inflated subsidy promises, high prices, short warranties.",
    quoteUpload: "Upload the quote photo or PDF",
    sampleQuote: "No quote handy? Check a sample quote →",
    checkingQuote: "Checking the quote…",
    viewSample: "See the sample quote that was checked",
    checkQuoteCta: "🧾 Next: check a vendor's quote before you sign →",
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
    whySub: "हर साइज़ की 25 साल की तुलना। आज का कुल फ़ायदा = 25 साल की बचत में से लागत घटाकर, 8% सालाना डिस्काउंट के साथ। अगर छोटा साइज़ सबसे अच्छे फ़ायदे के 10% के अंदर हो, तो हम वही सुझाते हैं: लगभग उतना ही फ़ायदा, कम पैसे में।",
    cols: ["साइज़", "सब्सिडी के बाद", "सालाना बचत", "वसूल", "आज का कुल फ़ायदा"],
    never: "कभी नहीं",
    readTitle: "आपके बिल से हमने क्या पढ़ा",
    provider: "बिजली कंपनी",
    load: "स्वीकृत लोड",
    months: "कितने महीनों की खपत",
    amount: "इस महीने का बिल",
    conservative: "धूप के लिए PVGIS और NASA में से कम अनुमान लेते हैं। असली उत्पादन और बचत मौसम, कटौती, छाया, रखरखाव और बिजली दर से बदल सकते हैं।",
    again: "← फिर से शुरू करें",
    error: "कुछ गड़बड़ हो गई। कृपया फिर कोशिश करें।",
    tooBig: "फ़ाइल बहुत बड़ी है। कृपया 4 MB से छोटी फोटो या PDF भेजें।",
    footer: "AWS पर बना, WeMakeDevs × AWS Environmental Hacks के लिए",
    privacyLink: "प्राइवेसी",
    quoteTitle: "वेंडर का कोटेशन मिला? साइन करने से पहले जाँचें",
    quoteSub: "उन गलतियों को पकड़ता है जिनसे सब्सिडी डूबती है: बिना DCR पैनल, बढ़ा-चढ़ाकर सब्सिडी का वादा, ज़्यादा कीमत, कम वारंटी।",
    quoteUpload: "कोटेशन की फोटो या PDF अपलोड करें",
    sampleQuote: "कोटेशन पास नहीं है? एक सैंपल कोटेशन जाँचें →",
    checkingQuote: "कोटेशन जाँचा जा रहा है…",
    viewSample: "जाँचा गया सैंपल कोटेशन देखें",
    checkQuoteCta: "🧾 आगे: साइन करने से पहले वेंडर का कोटेशन जाँचें →",
    kw: (k) => `${k} kW`,
  },
};


// Landing-page copy. Kept apart from the result copy above so each stays readable.
Object.assign(T.en, {
  skip: "Skip to content",
  navHow: "How it works", navQuote: "Check a quote", navApply: "Apply", navRules: "Rates & rules", navAws: "Built on AWS",
  eyebrow: "PM Surya Ghar · rooftop solar, from bill to subsidy",
  title: "Your electricity bill already knows if solar pays.",
  sub: "Send a photo of it. In about ten seconds you get the right size, the subsidy, your EMI and the payback, or an honest skip. Then help with the vendor, the paperwork and the subsidy.",
  upload: "Upload your bill",
  uploadHint: "Photo or PDF. Any Indian electricity provider; Delhi has the most detail.",
  slipSlab: "Slab", slipUnits: "Units this month", slipSun: "Sunlight here",
  answerTag: "The answer", answerBig: "Go solar: 2 kW", answerSub: "₹70,000 after subsidy · pays back in 4.9 years",
  sBills: "bills read", sKw: "kW of rooftop solar recommended", sCo2: "tonnes of CO₂ a year those systems avoid", sFlags: "red flags caught in vendor quotes",
  sNote: "Live, counted since 8 October 2026. Sample homes and sample quotes aren't counted.",
  howTitle: "From bill to subsidy, and after",
  howSub: "Most households stop before they apply: they can't tell if it pays, who to trust, or what to do next. Surya Saathi walks the whole way with them.",
  st1: "Decide", st1d: "Bill photo → the right size, subsidy, EMI and payback. An honest skip when solar won't pay.",
  st2: "Choose", st2d: "Quote check: non-DCR panels, inflated subsidy promises, overpricing, weak warranties.",
  st3: "Apply", st3d: "A pre-flight check for the usual rejections, then the portal's steps one at a time.",
  st4: "Get paid", st4d: "Reminders when a step stalls, and a complaint drafted for whoever is holding it up.",
  st5: "Keep it running", st5d: "Check your first bills after solar, and the panels' output against what they should make.",
  dlEyebrow: "New in Delhi · September 2026",
  dlTitle: "Using up to 400 units a month? You may get 3 kW at ₹0 upfront.",
  dlSub: "Delhi's new policy also adds up to ₹78,000 on top of the central subsidy for everyone else. Send your bill to see which applies to you.",
  dlCta: "Check my bill",
  trap1: "Panels without DCR (made-in-India cells): the whole subsidy is lost.",
  trap2: "A subsidy promise above the scheme's maximum.",
  trap3: "A price per kW far above what nearby households were quoted.",
  trap4: "Fewer panels than the size you're paying for, a small inverter, short warranties, a big advance.",
  applyTitle: "The 8 steps to your subsidy",
  applySub: "On WhatsApp, Surya Saathi keeps your place, nudges you when a step runs long, and writes the complaint when someone else is holding it up. You send it.",
  who: { you: "you", vendor: "vendor", discom: "electricity provider", mnre: "ministry" },
  usual: (d) => `usually ${d} day${d === 1 ? "" : "s"}`,
  chatHead: "Here's a message to send to the provider's nodal officer (email):",
  chatBody: "Subject: rooftop solar application pending at \"Net meter and inspection\" for 41 days. Please tell me what is pending and by when it will be completed…",
  chatNext: "No reply within 7 days? Next: the PM Surya Ghar grievance portal.",
  rulesTitle: "Rates and rules, checked by people",
  rulesSub: "Fuel surcharges, state top-ups and prices change every few months. Instead of a table that quietly goes stale, every fact shows its source, when it was last confirmed, and whether anyone has reported a change.",
  l1: "Bills teach tariffs", l1d: "Every bill prints its slab rates. Each one read updates that provider's tariff, which is how bills from any state work.",
  l2: "Quotes teach prices", l2d: "Every quote checked adds a price per kW for its state. The fair range comes from real local quotes.",
  l3: "People confirm facts", l3d: "Confirm what's still true, or report a change with evidence. Three reports flag a fact for review.",
  l4: "Watchers check sources", l4d: "Every week, official pages are re-read. If one changes, its facts are marked for review.",
  fAll: "All India", factsLoading: "Loading the latest facts…", factsError: "Couldn't load the facts right now.",
  factStill: "Still true", factChange: "Report a change", factThanks: "Thanks, confirmed.",
  factNew: "What is it now?", factEvidence: "Evidence: a link, or where you saw it", factSend: "Send report",
  factSent: "Thanks. Three matching reports flag it for review.",
  factMeta: (n, d) => `${n} confirmation${n === 1 ? "" : "s"} · last confirmed ${d}`,
  factReports: (n) => `${n} change report${n === 1 ? "" : "s"}`,
  factSource: "source",
  status: { current: "current", reported_changed: "change reported", source_changed: "source page changed" },
  scope: { IN: "All India", DL: "Delhi", UP: "Uttar Pradesh", HR: "Haryana" },
  waTitle: "Use it on WhatsApp",
  waSub: "Send a bill or quote photo, in Hindi or English. During the hackathon the bot runs on Twilio's WhatsApp sandbox, so message the number below with the join code first.",
  waJoin: (code) => `Send “${code}” first`,
  c1: "Bill photo", c1d: "the full solar answer", c2: "Quote photo", c2d: "red flags and questions to ask",
  c3d: "start the 8-step application plan", c4d: "finish the current step", c5d: "get a complaint drafted for whoever is holding things up",
  c6d: "switch language", c7d: "erase everything stored about you",
  applyCta: "📋 Start the application plan on WhatsApp →",
});
Object.assign(T.hi, {
  skip: "सीधे सामग्री पर जाएँ",
  navHow: "कैसे काम करता है", navQuote: "कोटेशन जाँचें", navApply: "आवेदन", navRules: "रेट और नियम", navAws: "AWS पर बना",
  eyebrow: "PM सूर्य घर · रूफ़टॉप सोलर, बिल से सब्सिडी तक",
  title: "आपका बिजली बिल पहले से जानता है कि सोलर फ़ायदेमंद है या नहीं।",
  sub: "उसकी फोटो भेजें। लगभग दस सेकंड में सही साइज़, सब्सिडी, EMI और लागत वसूली का समय पता चलेगा, या साफ़ बताया जाएगा कि अभी न लगाएँ। फिर वेंडर, कागज़ात और सब्सिडी में भी मदद।",
  upload: "अपना बिल अपलोड करें",
  uploadHint: "फोटो या PDF। भारत की किसी भी बिजली कंपनी का बिल; दिल्ली के लिए सबसे ज़्यादा जानकारी।",
  slipSlab: "स्लैब", slipUnits: "इस महीने की यूनिट", slipSun: "यहाँ की धूप",
  answerTag: "जवाब", answerBig: "सोलर लगाएँ: 2 kW", answerSub: "सब्सिडी के बाद ₹70,000 · 4.9 साल में वसूल",
  sBills: "बिल पढ़े गए", sKw: "kW रूफ़टॉप सोलर सुझाया गया", sCo2: "टन CO₂ हर साल कम", sFlags: "वेंडर कोटेशन में पकड़ी गई गड़बड़ियाँ",
  sNote: "लाइव, 8 अक्टूबर 2026 से गिनती। सैंपल घर और सैंपल कोटेशन नहीं गिने जाते।",
  howTitle: "बिल से सब्सिडी तक, और उसके बाद भी",
  howSub: "ज़्यादातर लोग आवेदन से पहले ही रुक जाते हैं: पता नहीं होता कि फ़ायदा होगा या नहीं, किस पर भरोसा करें, आगे क्या करें। सूर्य साथी पूरे रास्ते साथ चलता है।",
  st1: "फ़ैसला", st1d: "बिल की फोटो → सही साइज़, सब्सिडी, EMI और लागत वसूली। फ़ायदा न हो तो साफ़ मना।",
  st2: "वेंडर चुनें", st2d: "कोटेशन जाँच: बिना DCR पैनल, बढ़ा-चढ़ाकर सब्सिडी का वादा, ज़्यादा कीमत, कमज़ोर वारंटी।",
  st3: "आवेदन", st3d: "आम गलतियों से बचने की जाँच, फिर पोर्टल के कदम एक-एक करके।",
  st4: "सब्सिडी पाएँ", st4d: "कोई कदम अटके तो याद दिलाना, और ज़िम्मेदार दफ़्तर के लिए तैयार शिकायत।",
  st5: "चलता रहे", st5d: "सोलर के बाद के बिल जाँचें, और पैनल की बिजली को अनुमान से मिलाएँ।",
  dlEyebrow: "दिल्ली में नया · सितंबर 2026",
  dlTitle: "महीने में 400 यूनिट तक खपत? आपको 3 kW बिना शुरुआती खर्च के मिल सकता है।",
  dlSub: "बाकी सबके लिए दिल्ली की नई नीति केंद्र की सब्सिडी के ऊपर ₹78,000 तक और देती है। बिल भेजें, पता चलेगा कि आप पर क्या लागू होता है।",
  dlCta: "मेरा बिल जाँचें",
  trap1: "बिना DCR (भारत में बने सेल) के पैनल: पूरी सब्सिडी डूब जाती है।",
  trap2: "योजना की सीमा से ज़्यादा सब्सिडी का वादा।",
  trap3: "आसपास के घरों को मिले रेट से बहुत ज़्यादा कीमत प्रति kW।",
  trap4: "जितने का पैसा उतने से कम पैनल, छोटा इन्वर्टर, कम वारंटी, बड़ा एडवांस।",
  applyTitle: "सब्सिडी तक के 8 कदम",
  applySub: "WhatsApp पर सूर्य साथी याद रखता है कि आप कहाँ हैं, कोई कदम लंबा खिंचे तो याद दिलाता है, और देरी किसी और की हो तो शिकायत लिख देता है। भेजते आप हैं।",
  who: { you: "आप", vendor: "वेंडर", discom: "बिजली कंपनी", mnre: "मंत्रालय" },
  usual: (d) => `आम तौर पर ${d} दिन`,
  chatHead: "बिजली कंपनी के नोडल ऑफ़िसर को भेजने के लिए मैसेज (ईमेल):",
  chatBody: "विषय: रूफ़टॉप सोलर आवेदन \"नेट मीटर और जाँच\" पर 41 दिन से लंबित। कृपया बताएँ कि क्या बाकी है और कब तक पूरा होगा…",
  chatNext: "7 दिन में जवाब न आए? अगला: PM सूर्य घर शिकायत पोर्टल।",
  rulesTitle: "रेट और नियम, लोगों द्वारा जाँचे गए",
  rulesSub: "फ़्यूल सरचार्ज, राज्य की सब्सिडी और कीमतें कुछ महीनों में बदल जाती हैं। चुपचाप पुरानी पड़ने वाली टेबल की जगह, हर जानकारी के साथ उसका स्रोत, आखिरी पुष्टि की तारीख और बदलाव की रिपोर्ट दिखती है।",
  l1: "बिल से टैरिफ", l1d: "हर बिल पर स्लैब रेट छपे होते हैं। हर पढ़ा गया बिल उस कंपनी का टैरिफ अपडेट करता है, इसी से किसी भी राज्य का बिल चलता है।",
  l2: "कोटेशन से कीमतें", l2d: "हर जाँचा गया कोटेशन उस राज्य की प्रति kW कीमत जोड़ता है। सही रेंज असली स्थानीय कोटेशन से बनती है।",
  l3: "लोग पुष्टि करते हैं", l3d: "जो सही है उसकी पुष्टि करें, या सबूत के साथ बदलाव बताएँ। तीन रिपोर्ट पर जानकारी जाँच के लिए चिह्नित होती है।",
  l4: "स्रोतों पर नज़र", l4d: "हर हफ़्ते सरकारी पेज दोबारा पढ़े जाते हैं। कोई बदले तो उससे जुड़ी जानकारी जाँच के लिए चिह्नित होती है।",
  fAll: "पूरा भारत", factsLoading: "ताज़ा जानकारी आ रही है…", factsError: "अभी जानकारी लोड नहीं हो सकी।",
  factStill: "अब भी सही", factChange: "बदलाव बताएँ", factThanks: "धन्यवाद, पुष्टि हो गई।",
  factNew: "अब क्या है?", factEvidence: "सबूत: लिंक, या कहाँ देखा", factSend: "रिपोर्ट भेजें",
  factSent: "धन्यवाद। तीन मिलती-जुलती रिपोर्ट पर इसे जाँच के लिए चिह्नित किया जाता है।",
  factMeta: (n, d) => `${n} पुष्टि · आखिरी पुष्टि ${d}`,
  factReports: (n) => `${n} बदलाव रिपोर्ट`,
  factSource: "स्रोत",
  status: { current: "मौजूदा", reported_changed: "बदलाव रिपोर्ट", source_changed: "स्रोत पेज बदला" },
  scope: { IN: "पूरा भारत", DL: "दिल्ली", UP: "उत्तर प्रदेश", HR: "हरियाणा" },
  waTitle: "WhatsApp पर इस्तेमाल करें",
  waSub: "हिंदी या अंग्रेज़ी में बिल या कोटेशन की फोटो भेजें। हैकथॉन के दौरान बॉट Twilio के WhatsApp सैंडबॉक्स पर चलता है, इसलिए पहले नीचे दिए नंबर पर जॉइन कोड भेजें।",
  waJoin: (code) => `पहले “${code}” भेजें`,
  c1: "बिल की फोटो", c1d: "पूरा सोलर जवाब", c2: "कोटेशन की फोटो", c2d: "गड़बड़ियाँ और पूछने लायक सवाल",
  c3d: "8 कदम का आवेदन प्लान शुरू", c4d: "मौजूदा कदम पूरा", c5d: "देरी करने वाले के लिए तैयार शिकायत",
  c6d: "भाषा बदलें", c7d: "आपकी सारी जानकारी मिटाएँ",
  applyCta: "📋 WhatsApp पर आवेदन प्लान शुरू करें →",
});


Object.assign(T.en, {
  flatTitle: "Live in a flat? Your society can go solar.",
  flatSub: "PM Surya Ghar pays ₹18,000 per kW for a housing society's common areas (lifts, water pumps, lights, EV charging), up to 500 kW. Enter what your society pays for common-area electricity.",
  flatInput: "Society's common-area bill per month (₹)",
  flatNote: "Estimates: ₹7.50 a unit for common areas, ₹58,000 per kW installed, 1,480 units per kW a year. Some states, Delhi among them, also allow virtual net metering so one system can credit every flat's bill.",
  flatMsgTitle: "A message for your RWA",
  socKw: "Size", socNet: "Cost after subsidy", socSaves: "Saves every year", socPayback: "Pays for itself in",
  rwaMsg: (kw, net, saves) => `Dear Committee, PM Surya Ghar gives our society ₹18,000 per kW for rooftop solar on common areas, up to 500 kW. A ${kw} kW system would cost about ${net} after subsidy and could cut our common-area electricity bill by about ${saves} a year. Can we discuss this at the next meeting and invite two registered vendors to quote?`,
  copy: "Copy message", copied: "Copied", copyFallback: "Select the text above to copy it",
  c8: "Inverter screenshot", c8d: "check output against what the panels should make",
  c9: "Voice note", c9d: "ask anything in Hindi or English; the answer comes back as a voice note",
  c10d: "solar for your housing society's common areas", c11d: "set your system's real size for output checks",
});
Object.assign(T.hi, {
  flatTitle: "फ़्लैट में रहते हैं? आपकी सोसाइटी सोलर लगा सकती है।",
  flatSub: "PM सूर्य घर हाउसिंग सोसाइटी के कॉमन एरिया (लिफ़्ट, पानी के पंप, लाइटें, EV चार्जिंग) के लिए ₹18,000 प्रति kW देता है, 500 kW तक। आपकी सोसाइटी कॉमन एरिया की बिजली के लिए जितना देती है, वह डालें।",
  flatInput: "सोसाइटी का कॉमन एरिया का मासिक बिल (₹)",
  flatNote: "अनुमान: कॉमन एरिया के लिए ₹7.50 प्रति यूनिट, ₹58,000 प्रति kW लगवाने का खर्च, हर kW से सालाना 1,480 यूनिट। कुछ राज्यों में, जिनमें दिल्ली भी है, वर्चुअल नेट मीटरिंग से एक सिस्टम हर फ़्लैट के बिल में क्रेडिट दे सकता है।",
  flatMsgTitle: "आपकी RWA के लिए मैसेज",
  socKw: "साइज़", socNet: "सब्सिडी के बाद लागत", socSaves: "हर साल बचत", socPayback: "लागत वसूल",
  rwaMsg: (kw, net, saves) => `माननीय समिति, PM सूर्य घर योजना में हमारी सोसाइटी को कॉमन एरिया पर रूफ़टॉप सोलर के लिए ₹18,000 प्रति kW मिलते हैं, 500 kW तक। ${kw} kW सिस्टम सब्सिडी के बाद लगभग ${net} का पड़ेगा और हमारे कॉमन एरिया के बिजली बिल में सालाना लगभग ${saves} की बचत कर सकता है। क्या अगली बैठक में इस पर चर्चा करके दो रजिस्टर्ड वेंडर से कोटेशन मँगवा सकते हैं?`,
  copy: "मैसेज कॉपी करें", copied: "कॉपी हो गया", copyFallback: "कॉपी करने के लिए ऊपर का टेक्स्ट चुनें",
  c8: "इन्वर्टर का स्क्रीनशॉट", c8d: "पैनल को जितना बनाना चाहिए, उससे उत्पादन मिलाएँ",
  c9: "वॉइस नोट", c9d: "हिंदी या अंग्रेज़ी में कुछ भी पूछें; जवाब वॉइस नोट में आएगा",
  c10d: "हाउसिंग सोसाइटी के कॉमन एरिया के लिए सोलर", c11d: "उत्पादन जाँच के लिए सिस्टम का असली साइज़",
});


Object.assign(T.en, {
  share: "Share on WhatsApp",
  shareGo: (kw, net, payback, url) => `Our home could go solar: ${kw} kW, ${net} after the PM Surya Ghar subsidy, paying for itself in ${payback} years. Check yours with a photo of your electricity bill: ${url}`,
  shareSkip: (url) => `Checked rooftop solar for our home with Surya Saathi. Check yours with a photo of your electricity bill: ${url}`,
  askTitle: "Ask anything about rooftop solar",
  askSub: "Loans, the subsidy, vendors, net metering, what to do when a step is stuck. Answers stick to the scheme's facts and say so when they don't know. On WhatsApp you can ask by voice note, in Hindi.",
  askSend: "Ask", askEmpty: "Your answer will appear here.", askThinking: "Thinking…",
  askExamples: ["Can I get a loan without collateral?", "My vendor wants 70% advance. Is that normal?", "Is my rented flat eligible?"],
});
Object.assign(T.hi, {
  share: "WhatsApp पर शेयर करें",
  shareGo: (kw, net, payback, url) => `हमारे घर पर सोलर लग सकता है: ${kw} kW, PM सूर्य घर सब्सिडी के बाद ${net}, ${payback} साल में लागत वसूल। अपने बिजली बिल की फोटो से अपना भी जाँचें: ${url}`,
  shareSkip: (url) => `सूर्य साथी से अपने घर के लिए रूफ़टॉप सोलर जाँचा। अपने बिजली बिल की फोटो से अपना भी जाँचें: ${url}`,
  askTitle: "रूफ़टॉप सोलर के बारे में कुछ भी पूछें",
  askSub: "लोन, सब्सिडी, वेंडर, नेट मीटरिंग, कोई कदम अटके तो क्या करें। जवाब योजना की जानकारी पर टिके रहते हैं, और पता न हो तो साफ़ बताते हैं। WhatsApp पर हिंदी में वॉइस नोट से भी पूछ सकते हैं।",
  askSend: "पूछें", askEmpty: "जवाब यहाँ दिखेगा।", askThinking: "सोचा जा रहा है…",
  askExamples: ["क्या बिना गारंटी के लोन मिलेगा?", "वेंडर 70% एडवांस माँग रहा है, क्या यह ठीक है?", "क्या किराए के फ़्लैट पर सोलर लग सकता है?"],
});


Object.assign(T.en, {
  timesTitle: "How long steps really take",
  timesEmpty: "Every household that finishes a step adds its time here, by electricity provider, so slow offices become visible. No real applications have finished a step yet.",
  timesCols: ["Provider", "Step", "Usual", "Median so far", "Households"],
});
Object.assign(T.hi, {
  timesTitle: "कदमों में असल में कितना समय लगता है",
  timesEmpty: "हर घर जो कोई कदम पूरा करता है, उसका समय यहाँ बिजली कंपनी के हिसाब से जुड़ता है, ताकि धीमे दफ़्तर सबको दिखें। अभी तक किसी असली आवेदन ने कोई कदम पूरा नहीं किया है।",
  timesCols: ["बिजली कंपनी", "कदम", "आम तौर पर", "अब तक का औसत", "घर"],
});


// Copy for the redesigned page. Plain words: say what it does and who it's for.
Object.assign(T.en, {
  skipLink: "Skip to content",
  skip: "Solar won't pay for you yet",
  navAws: "How it's built",
  title: "Is rooftop solar worth it for your home?",
  sub: "Surya Saathi is a free WhatsApp assistant for families applying under the PM Surya Ghar scheme. Send a photo of your electricity bill and in about ten seconds it tells you the system size to buy, the subsidy you'll get, the EMI, and how many years it takes to pay for itself. If solar won't pay for you yet, it says so.",
  sub2: "After that, it checks vendor quotes, takes you through the eight application steps, and follows up when the subsidy is late.",
  upload: "Upload your bill",
  sample: "See an example result",
  uploadHint: "A photo or PDF works. Bills from any Indian electricity company can be read, and Delhi bills get the most detail.",
  location: "Use my location", locationOn: "Using your location", locationOff: "Location not available",
  dlLead: "In Delhi:",
  dlTitle: "homes using up to 400 units a month may now get up to 3 kW with nothing to pay upfront, under a state decision from September 2026. Upload a Delhi bill to see if yours qualifies.",
  devSent: "My bill for September", devVerdict: "Go solar",
  devNote: "Reply APPLY to start your application. I'll take you through all 8 steps.",
  devFoot: "An example reply for a home in Delhi",
  yrs: "years", emiShort: "EMI a month", co2Short: "CO₂ avoided a year",
  chatSub: "online",
  whyNowTitle: "Why most families haven't applied yet",
  whyNowBody: "PM Surya Ghar pays up to ₹78,000 towards a home rooftop system and aims to reach 1 crore homes by March 2027. About 41 lakh have one so far. In a June 2026 survey by CEEW, most households dropped out before applying: they couldn't tell whether solar would pay, which vendor to trust, or how the process works. Surya Saathi is built to answer those three questions.",
  cellsNote: "Each square is 1 lakh homes. The 41 filled squares already have rooftop solar under the scheme; the target is all 100.",
  sBills: "bills read", sKw: "kW of solar recommended", sCo2: "tonnes of CO₂ a year those systems would avoid", sFlags: "problems caught in vendor quotes",
  howTitle: "From your first bill to the subsidy",
  howSub: "Deciding is only the start. Then come a vendor, an online application, an inspection and a wait for the money. Surya Saathi helps at each stage.",
  st1: "Decide", st1d: "Send your bill. You get the system size, the subsidy, the EMI and the payback, or a clear no if solar won't pay.",
  st2: "Pick a vendor", st2d: "Send the vendor's quote. It flags panels that lose the subsidy, prices above what others paid nearby, short warranties and large advances.",
  st3: "Apply", st3d: "It checks for the usual reasons applications get rejected, then gives you the portal steps one at a time.",
  st4: "Get the subsidy", st4d: "If a step runs late, it reminds you and drafts a complaint to whoever is holding it up.",
  st5: "After installation", st5d: "Send an inverter screenshot or a new bill to check the panels are producing what they should.",
  quoteTitle: "Check a vendor's quote before you sign",
  quoteSub: "Upload the quotation. Surya Saathi reads it the same way it reads a bill and looks for these problems:",
  quoteUpload: "Upload the quote", quoteHint: "A photo or PDF of the quotation", sampleQuote: "Try it on a sample quote",
  applySub: "On WhatsApp, Surya Saathi remembers where you are, reminds you when a step runs long, and writes the complaint when someone else is holding it up. You decide whether to send it.",
  askTitle: "Ask a question about rooftop solar",
  askSub: "Loans, the subsidy, vendors, net metering, or a step that's stuck. Answers come from the scheme rules listed further down this page, and it tells you when it doesn't know. On WhatsApp you can also ask with a voice note in Hindi.",
  askTry: "Or try one of these:",
  rulesTitle: "Where the numbers come from",
  rulesSub: "Tariffs, state top-ups and vendor prices change every few months. Each figure below shows its source and when someone last confirmed it. If one has changed, report it with proof.",
  factMeta: (n, d) => `Confirmed ${n} time${n === 1 ? "" : "s"}, most recently on ${d}`,
  checkQuoteCta: "Check a vendor's quote", applyCta: "Start the application on WhatsApp",
  again: "Start again",
  footer: "Built on AWS for the WeMakeDevs × AWS Environmental Hacks, October 2026",
  pixelCredit: "Skyline drawn in code",
});
Object.assign(T.hi, {
  skipLink: "सीधे सामग्री पर जाएँ",
  skip: "अभी सोलर से आपको फ़ायदा नहीं होगा",
  navAws: "कैसे बना है",
  title: "क्या आपके घर के लिए रूफ़टॉप सोलर फ़ायदेमंद है?",
  sub: "सूर्य साथी PM सूर्य घर योजना में आवेदन करने वाले परिवारों के लिए एक मुफ़्त WhatsApp सहायक है। अपने बिजली बिल की फोटो भेजें, और लगभग दस सेकंड में पता चलेगा कि कितने kW का सिस्टम लें, कितनी सब्सिडी मिलेगी, EMI कितनी होगी और लागत कितने साल में वसूल होगी। अगर अभी सोलर से फ़ायदा नहीं है, तो यह साफ़ बता देगा।",
  sub2: "इसके बाद यह वेंडर के कोटेशन जाँचता है, आवेदन के आठ कदमों में साथ चलता है, और सब्सिडी में देरी हो तो पीछा करता है।",
  upload: "अपना बिल अपलोड करें",
  sample: "एक उदाहरण देखें",
  uploadHint: "फोटो या PDF, दोनों चलेंगे। भारत की किसी भी बिजली कंपनी का बिल पढ़ा जा सकता है; दिल्ली के बिलों से सबसे ज़्यादा जानकारी मिलती है।",
  location: "मेरी लोकेशन लें", locationOn: "आपकी लोकेशन ली गई", locationOff: "लोकेशन नहीं मिली",
  dlLead: "दिल्ली में:",
  dlTitle: "सितंबर 2026 के राज्य सरकार के फ़ैसले के तहत, महीने में 400 यूनिट तक खपत वाले घरों को अब 3 kW तक का सिस्टम बिना शुरुआती खर्च के मिल सकता है। दिल्ली का बिल अपलोड करके देखें कि आप पात्र हैं या नहीं।",
  devSent: "सितंबर का मेरा बिल", devVerdict: "सोलर लगाएँ",
  devNote: "आवेदन शुरू करने के लिए APPLY लिखें। मैं आठों कदमों में साथ रहूँगा।",
  devFoot: "दिल्ली के एक घर के लिए उदाहरण जवाब",
  yrs: "साल", emiShort: "महीने की EMI", co2Short: "हर साल CO₂ कम",
  chatSub: "ऑनलाइन",
  whyNowTitle: "ज़्यादातर परिवारों ने अब तक आवेदन क्यों नहीं किया",
  whyNowBody: "PM सूर्य घर घर की छत के सोलर सिस्टम के लिए ₹78,000 तक देता है और मार्च 2027 तक 1 करोड़ घरों तक पहुँचना चाहता है। अब तक लगभग 41 लाख घरों में यह लग चुका है। CEEW के जून 2026 के सर्वे में ज़्यादातर परिवार आवेदन से पहले ही रुक गए: उन्हें पता नहीं था कि सोलर से फ़ायदा होगा या नहीं, किस वेंडर पर भरोसा करें, या प्रक्रिया क्या है। सूर्य साथी इन्हीं तीन सवालों का जवाब देने के लिए बना है।",
  cellsNote: "हर खाना 1 लाख घर है। भरे हुए 41 खानों वाले घरों में योजना के तहत सोलर लग चुका है; लक्ष्य पूरे 100 का है।",
  sBills: "बिल पढ़े गए", sKw: "kW सोलर सुझाया गया", sCo2: "टन CO₂ हर साल, जो ये सिस्टम बचाएँगे", sFlags: "वेंडर कोटेशन में पकड़ी गई गड़बड़ियाँ",
  howTitle: "पहले बिल से सब्सिडी तक",
  howSub: "फ़ैसला तो बस शुरुआत है। फिर वेंडर, ऑनलाइन आवेदन, जाँच और पैसे का इंतज़ार आता है। सूर्य साथी हर पड़ाव पर मदद करता है।",
  st1: "फ़ैसला", st1d: "अपना बिल भेजें। सिस्टम का साइज़, सब्सिडी, EMI और लागत वसूली का समय मिलेगा, या साफ़ मना, अगर सोलर से फ़ायदा न हो।",
  st2: "वेंडर चुनें", st2d: "वेंडर का कोटेशन भेजें। यह बताएगा कि पैनल से सब्सिडी तो नहीं डूबेगी, कीमत आसपास से ज़्यादा तो नहीं, और वारंटी कम या एडवांस ज़्यादा तो नहीं।",
  st3: "आवेदन", st3d: "आवेदन खारिज होने की आम वजहें पहले जाँचता है, फिर पोर्टल के कदम एक-एक करके बताता है।",
  st4: "सब्सिडी पाएँ", st4d: "कोई कदम देर से चले तो याद दिलाता है, और देरी करने वाले के लिए शिकायत लिख देता है।",
  st5: "लगने के बाद", st5d: "इन्वर्टर का स्क्रीनशॉट या नया बिल भेजें, यह जाँचने के लिए कि पैनल उतनी बिजली बना रहे हैं जितनी बनानी चाहिए।",
  quoteTitle: "साइन करने से पहले वेंडर का कोटेशन जाँचें",
  quoteSub: "कोटेशन अपलोड करें। सूर्य साथी इसे बिल की तरह पढ़ता है और इन गड़बड़ियों को खोजता है:",
  quoteUpload: "कोटेशन अपलोड करें", quoteHint: "कोटेशन की फोटो या PDF", sampleQuote: "एक सैंपल कोटेशन पर आज़माएँ",
  applySub: "WhatsApp पर सूर्य साथी याद रखता है कि आप कहाँ तक पहुँचे, कोई कदम लंबा खिंचे तो याद दिलाता है, और देरी किसी और की हो तो शिकायत लिख देता है। भेजनी है या नहीं, यह आप तय करते हैं।",
  askTitle: "रूफ़टॉप सोलर के बारे में सवाल पूछें",
  askSub: "लोन, सब्सिडी, वेंडर, नेट मीटरिंग, या अटका हुआ कोई कदम। जवाब इसी पेज पर नीचे दिए योजना के नियमों से आते हैं, और पता न हो तो यह साफ़ कहता है। WhatsApp पर आप हिंदी में वॉइस नोट से भी पूछ सकते हैं।",
  askTry: "या इनमें से कोई पूछें:",
  rulesTitle: "ये आँकड़े कहाँ से आते हैं",
  rulesSub: "टैरिफ़, राज्य की अतिरिक्त सब्सिडी और वेंडर की कीमतें कुछ महीनों में बदल जाती हैं। नीचे हर आँकड़े के साथ उसका स्रोत और आखिरी पुष्टि की तारीख है। कुछ बदल गया हो तो सबूत के साथ बताएँ।",
  factMeta: (n, d) => `${n} बार पुष्टि, आखिरी बार ${d} को`,
  checkQuoteCta: "वेंडर का कोटेशन जाँचें", applyCta: "WhatsApp पर आवेदन शुरू करें",
  again: "फिर से शुरू करें",
  footer: "WeMakeDevs × AWS Environmental Hacks, अक्टूबर 2026 के लिए AWS पर बना",
  pixelCredit: "स्काईलाइन कोड से बनी",
});


// The short home page: a working chat up top, three uses, the gap, WhatsApp. Everything else is a page.
Object.assign(T.en, {
  navQuote: "Check a quote", navApply: "Application guide", navRules: "Rates & rules", navAws: "How it's built",
  sub: "Send a photo of your electricity bill. In about 10 seconds you'll know the right solar size, your PM Surya Ghar subsidy, the EMI and how fast it pays for itself.",
  heroNote: "Free, in Hindi and English. Your name and address are never read or stored.",
  sample: "See an example", tune: "Add your location or roof size",
  today: "Today", message: "Message", readMore: "Read more", chatSub: "online", typing: "typing…",
  demoReply: "☀️ Solar estimate for your BSES Rajdhani connection\n\nBest size: 2 kW (needs about 200 sq ft of shade-free roof)\nCost: ₹1,30,000 − ₹60,000 subsidy = ₹70,000\nSaves ₹14,300–15,600 a year, about ₹1,200 a month\nPays for itself in 4.9 years",
  demoApply: "APPLY",
  demoPlan: "🚀 Your application plan has 8 steps, from a pre-flight check to the subsidy in your account. If a step takes longer than usual, you'll get a reminder here.",
  usesTitle: "It stays with you after the estimate",
  u1t: "Check a vendor's quote",
  u1d: "Send the quotation before you sign. It catches the problems that cost families their subsidy or overcharge them.",
  docMeta: "2 pages · PDF",
  u1reply: "🔴 Don't sign yet. Fix these first:\n• These panels are not DCR (made with Indian cells). Under PM Surya Ghar that means no subsidy: you'd lose ₹78,000.\n• 60% advance is a lot. Tie payments to installation milestones.",
  quoteUpload: "Upload a quote", sampleQuote: "Try a sample quote",
  u2t: "Chase a stuck application",
  u2d: "It knows the usual time for each of the 8 steps. When one runs late, it writes the complaint for you to send.",
  u2nudge: "⏰ It's been 41 days at \"Net meter and inspection\", longer than the usual 20.",
  u2reply: "✉️ Here's a message to send to the provider's nodal officer (email). Fill in the parts in [brackets]:\n\nSubject: PM Surya Ghar rooftop solar application [application number], pending at \"Net meter and inspection\" for 41 days…",
  u2a: "See all 8 steps",
  u3t: "Ask by voice, in Hindi",
  u3d: "Send a voice note with any question about loans, the subsidy or vendors. The answer comes back as a voice note too.",
  u3a: "Ask a question",
  whyNowTitle: "41 lakh homes have rooftop solar. The goal is 1 crore.",
  whyNowBody: "Most families stop before they apply. They can't tell if solar will pay, which vendor to trust, or what to do next (CEEW survey, June 2026). Surya Saathi answers all three.",
  cellsNote: "Each square is 1 lakh homes.",
  waTitle: "Try it on WhatsApp",
  waSub: "Send a bill or quote photo, or ask with a voice note, in Hindi or English. During the hackathon the bot runs on Twilio's WhatsApp sandbox, so send the join code first.",
  waOpen: "Open WhatsApp",
  cmdTitle: "Everything you can send on WhatsApp",
  applyCta: "See the application guide",
});
Object.assign(T.hi, {
  navQuote: "कोटेशन जाँचें", navApply: "आवेदन गाइड", navRules: "रेट और नियम", navAws: "कैसे बना है",
  sub: "अपने बिजली बिल की फोटो भेजें। लगभग 10 सेकंड में पता चलेगा कि कितने kW का सोलर लें, PM सूर्य घर में कितनी सब्सिडी मिलेगी, EMI कितनी होगी और लागत कितनी जल्दी वसूल होगी।",
  heroNote: "मुफ़्त, हिंदी और अंग्रेज़ी में। आपका नाम और पता न पढ़ा जाता है, न सेव होता है।",
  sample: "उदाहरण देखें", tune: "लोकेशन या छत का साइज़ जोड़ें",
  today: "आज", message: "मैसेज", readMore: "और पढ़ें", chatSub: "ऑनलाइन", typing: "टाइप कर रहा है…",
  demoReply: "☀️ आपके BSES Rajdhani कनेक्शन के लिए सोलर अनुमान\n\nसही साइज़: 2 kW (लगभग 200 वर्ग फुट छाया-रहित छत चाहिए)\nलागत: ₹1,30,000 − ₹60,000 सब्सिडी = ₹70,000\nबचत: सालाना ₹14,300–15,600, यानी लगभग ₹1,200 महीना\n4.9 साल में पूरी लागत वसूल",
  demoApply: "आवेदन",
  demoPlan: "🚀 आपके आवेदन प्लान में 8 कदम हैं, प्री-फ़्लाइट जाँच से लेकर खाते में सब्सिडी आने तक। कोई कदम सामान्य से ज़्यादा समय ले, तो यहीं याद दिलाया जाएगा।",
  usesTitle: "अनुमान के बाद भी साथ रहता है",
  u1t: "वेंडर का कोटेशन जाँचें",
  u1d: "साइन करने से पहले कोटेशन भेजें। यह उन गड़बड़ियों को पकड़ता है जिनसे सब्सिडी डूबती है या ज़्यादा पैसे लगते हैं।",
  docMeta: "2 पेज · PDF",
  u1reply: "🔴 अभी साइन न करें। पहले ये ठीक करवाएँ:\n• ये पैनल DCR (भारत में बने सेल) नहीं हैं। PM सूर्य घर में इसका मतलब है कोई सब्सिडी नहीं: आपके ₹78,000 चले जाएँगे।\n• 60% एडवांस बहुत ज़्यादा है। भुगतान काम के चरणों से जोड़ें।",
  quoteUpload: "कोटेशन अपलोड करें", sampleQuote: "सैंपल कोटेशन आज़माएँ",
  u2t: "अटके आवेदन का पीछा",
  u2d: "इसे पता है कि 8 में से हर कदम में आम तौर पर कितना समय लगता है। कोई कदम देर से चले, तो यह आपके भेजने के लिए शिकायत लिख देता है।",
  u2nudge: "⏰ \"नेट मीटर और जाँच\" पर 41 दिन हो गए, जबकि आम तौर पर 20 लगते हैं।",
  u2reply: "✉️ बिजली कंपनी के नोडल ऑफ़िसर को भेजने के लिए मैसेज (ईमेल)। [ब्रैकेट] वाली जगहें भरें:\n\nविषय: PM सूर्य घर रूफ़टॉप सोलर आवेदन [आवेदन नंबर], \"नेट मीटर और जाँच\" पर 41 दिन से लंबित…",
  u2a: "आठों कदम देखें",
  u3t: "हिंदी में बोलकर पूछें",
  u3d: "लोन, सब्सिडी या वेंडर के बारे में कोई भी सवाल वॉइस नोट में भेजें। जवाब भी वॉइस नोट में आता है।",
  u3a: "सवाल पूछें",
  whyNowTitle: "41 लाख घरों में रूफ़टॉप सोलर लग चुका है। लक्ष्य 1 करोड़ का है।",
  whyNowBody: "ज़्यादातर परिवार आवेदन से पहले ही रुक जाते हैं। उन्हें पता नहीं होता कि सोलर से फ़ायदा होगा या नहीं, किस वेंडर पर भरोसा करें, या आगे क्या करें (CEEW सर्वे, जून 2026)। सूर्य साथी इन तीनों का जवाब देता है।",
  cellsNote: "हर खाना 1 लाख घर है।",
  waTitle: "WhatsApp पर आज़माएँ",
  waSub: "हिंदी या अंग्रेज़ी में बिल या कोटेशन की फोटो भेजें, या वॉइस नोट से पूछें। हैकथॉन के दौरान बॉट Twilio के WhatsApp सैंडबॉक्स पर चलता है, इसलिए पहले जॉइन कोड भेजें।",
  waOpen: "WhatsApp खोलें",
  cmdTitle: "WhatsApp पर क्या-क्या भेज सकते हैं",
  applyCta: "आवेदन गाइड देखें",
});

const $ = (id) => document.getElementById(id);
const state = { lang: initialLang(), lat: null, lon: null, last: null, lastBody: null, lastQuote: null };

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
  if (state.lastQuote) renderQuote(state.lastQuote);
  if (typeof renderSteps === "function") { renderSteps(); renderFacts(); renderWhatsApp(); renderSociety(); renderAskExamples(); renderTimes(); }
  if (window.renderProduct) window.renderProduct();
}

function show(id) {
  for (const s of ["start", "busy", "problem", "result", "quote-result", "guide", "rules", "built", "quotes", "schemes", "care", "vendors"]) if ($(s)) $(s).hidden = s !== id;
  window.scrollTo({ top: 0, behavior: "instant" });
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
    state.lastQuote = null;
    render(state.last);
    show("result");
  } catch (e) {
    $("problem-text").textContent = e.message || t("error");
    show("problem");
  }
}

async function runQuote(work, isSample) {
  $("busy-text").textContent = t("checkingQuote");
  show("busy");
  try {
    state.lastQuote = await work();
    state.last = null;
    $("q-sample-link").hidden = !isSample;
    renderQuote(state.lastQuote);
    show("quote-result");
  } catch (e) {
    $("problem-text").textContent = e.message || t("error");
    show("problem");
  }
}

function fillList(id, items) {
  const ul = $(id);
  ul.innerHTML = "";
  for (const text of items) {
    const li = document.createElement("li");
    li.textContent = text;
    ul.append(li);
  }
}

function renderQuote(data) {
  const v = data.views[state.lang];
  $("q-head").textContent = v.head;
  const box = $("q-verdict");
  box.className = "verdict " + v.verdict;
  box.innerHTML = "";
  const big = document.createElement("div");
  big.className = "big";
  big.textContent = v.title;
  box.append(big);
  fillList("q-issues", [...v.red, ...v.amber]);
  fillList("q-notes", v.note);
  fillList("q-ask", v.ask);
  $("q-ask-title").textContent = v.ask_title;
  $("q-ask-card").hidden = v.ask.length === 0;
  $("q-foot").textContent = v.foot;
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
  $("share").href = shareLink(data);
  $("bonus").hidden = !data.bonus;
  $("bonus").textContent = data.bonus || "";
  renderDoctor(data.doctor);
}

function renderDoctor(doc) {
  const box = $("doctor");
  if (doc) state.doctor = doc;  // a language switch re-runs only the sums, so keep the check-up
  doc = doc || state.doctor;
  box.hidden = !doc || !doc.findings.length;
  if (box.hidden) return;
  const v = doc.views[state.lang] || doc.views.en;
  box.innerHTML = "";
  const h = document.createElement("h2");
  h.textContent = v.head;
  box.append(h);
  if (v.total) {
    const total = document.createElement("p");
    total.className = "total";
    total.textContent = v.total;
    box.append(total);
  }
  const ul = document.createElement("ul");
  for (const item of v.items) {
    const li = document.createElement("li");
    li.className = item.level;
    li.textContent = item.text;
    ul.append(li);
  }
  box.append(ul);
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
    state.lastBody = { discom: b.discom, sanctioned_kw: b.sanctioned_load_kw, monthly_units: b.monthly_units, last_bill_units: b.units_billed, last_bill_energy_rs: b.energy_charge_rs, ...extras() };
    return data;
  });
});

$("quote-file").addEventListener("change", (e) => {
  const file = e.target.files[0];
  e.target.value = "";
  if (!file) return;
  runQuote(async () => {
    const { b64, type } = await prepare(file);
    return post("/quote", { file_base64: b64, media_type: type });
  }, false);
});

$("sample-quote").addEventListener("click", () => runQuote(async () => {
  const blob = await (await fetch("sample-quote.png")).blob();
  return post("/quote", { file_base64: await toBase64(blob), media_type: "image/png", sample: true });
}, true));

$("to-quote").addEventListener("click", () => {
  history.pushState(null, "", "#quote-card");
  route("#quote-card", true);
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

document.querySelectorAll(".again").forEach((b) => b.addEventListener("click", () => { state.last = null; state.lastQuote = null; state.doctor = null; show("start"); }));

// --- landing page: live counters, the 8 steps, the facts board, WhatsApp details ---------
const landing = { journey: null, facts: null, scope: "" };
const num = (x, digits = 0) => Number(x || 0).toLocaleString("en-IN", { maximumFractionDigits: digits });

async function getJSON(path) {
  const r = await fetch(API + path);
  if (!r.ok) throw new Error(String(r.status));
  return r.json();
}

async function loadStats() {
  try {
    const s = await getJSON("/stats");
    $("s-bills").textContent = num(s.bills_read);
    $("s-kw").textContent = num(s.kw_recommended);
    $("s-co2").textContent = num(s.co2_t_per_year, 1);
    $("s-flags").textContent = num(s.red_flags);
    $("stats").hidden = !(s.bills_read > 0);  // nothing to show until real bills have been read
  } catch (_) { /* the strip stays hidden */ }
}

function renderSteps() {
  const list = $("steps");
  if (!landing.journey) return;
  list.innerHTML = "";
  for (const st of landing.journey.stages) {
    const li = document.createElement("li");
    const title = document.createElement("span");
    title.textContent = st.title[state.lang] || st.title.en;
    const who = document.createElement("span");
    who.className = "who";
    const b = document.createElement("b");
    b.textContent = t("who")[st.who];
    who.append(b, ", " + t("usual", st.days));
    li.append(title, who);
    list.append(li);
  }
}

async function loadJourney() {
  try { landing.journey = await getJSON("/journey"); renderSteps(); } catch (_) { /* the list stays empty */ }
}

function pill(cls, text) {
  const p = document.createElement("span");
  p.className = "pill " + cls;
  p.textContent = text;
  return p;
}

function renderFacts() {
  const list = $("facts");
  list.innerHTML = "";
  if (!landing.facts) {
    const li = document.createElement("li");
    li.className = "fact-empty";
    li.textContent = t("factsLoading");
    list.append(li);
    return;
  }
  for (const f of landing.facts) {
    const li = document.createElement("li");
    li.className = "fact";
    const top = document.createElement("div");
    top.className = "fact-top";
    const statusCls = f.status === "current" ? "ok" : "warn";
    top.append(pill("", t("scope")[f.scope] || f.scope), pill(statusCls, t("status")[f.status] || f.status));
    const title = document.createElement("span");
    title.className = "fact-title";
    title.textContent = f.title;
    top.append(title);
    const value = document.createElement("p");
    value.className = "fact-value";
    value.textContent = f.value;
    const meta = document.createElement("p");
    meta.className = "fact-meta";
    const conf = document.createElement("span");
    conf.textContent = t("factMeta", f.confirmations, f.last_confirmed);
    const src = document.createElement("a");
    src.href = f.source;
    src.target = "_blank";
    src.rel = "noopener";
    src.textContent = `${t("factSource")}: ${new URL(f.source).hostname.replace(/^www\./, "")}`;
    meta.append(conf, src);
    if (f.report_count) {
      const rep = document.createElement("span");
      rep.textContent = t("factReports", f.report_count);
      meta.append(rep);
    }
    const actions = document.createElement("div");
    actions.className = "fact-actions";
    const yes = document.createElement("button");
    yes.className = "chip";
    yes.type = "button";
    yes.textContent = t("factStill");
    yes.addEventListener("click", async () => {
      yes.disabled = true;
      try {
        const r = await fetch(`${API}/facts/${f.id}/confirm`, { method: "POST" });
        const st = await r.json();
        f.confirmations = st.confirmations;
        f.last_confirmed = st.last_confirmed;
        conf.textContent = `${t("factMeta", f.confirmations, f.last_confirmed)}. ${t("factThanks")}`;
      } catch (_) { yes.disabled = false; }
    });
    const change = document.createElement("button");
    change.className = "chip";
    change.type = "button";
    change.textContent = t("factChange");
    change.addEventListener("click", () => {
      change.disabled = true;
      li.append(reportForm(f));
    });
    actions.append(yes, change);
    li.append(top, value, meta, actions);
    list.append(li);
  }
}

function reportForm(f) {
  const form = document.createElement("form");
  form.className = "fact-form";
  const value = document.createElement("input");
  value.id = `report-${f.id}-value`;
  value.required = true;
  value.placeholder = t("factNew");
  value.setAttribute("aria-label", t("factNew"));
  const evidence = document.createElement("input");
  evidence.id = `report-${f.id}-evidence`;
  evidence.placeholder = t("factEvidence");
  evidence.setAttribute("aria-label", t("factEvidence"));
  const send = document.createElement("button");
  send.className = "chip";
  send.type = "submit";
  send.textContent = t("factSend");
  const done = document.createElement("p");
  done.className = "small";
  form.append(value, evidence, send, done);
  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    send.disabled = true;
    try {
      await fetch(`${API}/facts/${f.id}/report`, { method: "POST", headers: { "content-type": "application/json" },
        body: JSON.stringify({ value: value.value, evidence: evidence.value }) });
      done.textContent = t("factSent");
    } catch (_) { send.disabled = false; }
  });
  return form;
}

async function loadFacts() {
  landing.facts = null;
  renderFacts();
  try {
    landing.facts = (await getJSON("/facts" + (landing.scope ? `?scope=${landing.scope}` : ""))).facts
      .filter((f) => !landing.scope || f.scope === landing.scope || f.scope === "IN");
  } catch (_) {
    landing.facts = [];
    $("facts").innerHTML = `<li class="fact-empty">${t("factsError")}</li>`;
    return;
  }
  renderFacts();
}

document.querySelectorAll(".filters .chip").forEach((b) => b.addEventListener("click", () => {
  document.querySelectorAll(".filters .chip").forEach((x) => x.setAttribute("aria-pressed", String(x === b)));
  landing.scope = b.dataset.scope;
  loadFacts();
}));

function renderWhatsApp() {
  const wa = window.SURYA_WA || {};
  $("wa-number").textContent = wa.number || "";
  $("wa-join").hidden = !wa.join;
  if (wa.join) $("wa-join").textContent = t("waJoin", wa.join);
  const digits = (wa.number || "").replace(/\D/g, "");
  $("wa-open").hidden = !digits;
  if (digits) $("wa-open").href = "https://wa.me/" + digits + (wa.join ? "?text=" + encodeURIComponent(wa.join) : "");
}

// One document, several pages: #guide, #rules and #built are views of their own; other links scroll.
function route(hash, smooth) {
  const id = (hash || "").replace(/^#/, "");
  const target = id && id !== "top" ? document.getElementById(id) : null;
  const view = (target && target.closest("[data-view]")) || $("start");
  const changedView = view.hidden;
  if (changedView) { if (state.last) state.estimate = state.last; state.last = null; state.lastQuote = null; show(view.id); }
  const behavior = changedView ? "instant" : smooth ? "smooth" : "auto";
  if (target && target !== view) target.scrollIntoView({ behavior });
  else window.scrollTo({ top: 0, behavior });
  document.querySelectorAll(".nav a").forEach((a) => {
    if (a.getAttribute("href") === "#" + view.id) a.setAttribute("aria-current", "page");
    else a.removeAttribute("aria-current");
  });
  if (window.productRoute) window.productRoute(view.id);
}

document.addEventListener("click", (e) => {
  const a = e.target.closest('a[href^="#"]');
  if (!a || a.classList.contains("skip")) return;
  e.preventDefault();
  const hash = a.getAttribute("href");
  history.pushState(null, "", hash === "#top" ? location.pathname + location.search : hash);
  route(hash, true);
});
window.addEventListener("popstate", () => route(location.hash));



// --- flats: a society's common areas -----------------------------------------------------
const SOCIETY = { ratePerUnit: 7.5, costPerKw: 58000, subsidyPerKw: 18000, maxKw: 500, yieldPerKw: 1480 };

function renderSociety() {
  const bill = Math.max(0, parseFloat($("society-bill").value) || 0);
  const kw = Math.min(SOCIETY.maxKw, Math.max(1, Math.round((bill / SOCIETY.ratePerUnit) * 12 / SOCIETY.yieldPerKw)));
  const net = kw * (SOCIETY.costPerKw - SOCIETY.subsidyPerKw);
  const saves = Math.min(bill * 12, kw * SOCIETY.yieldPerKw * SOCIETY.ratePerUnit);
  const rows = [[t("socKw"), t("kw", kw)], [t("socNet"), rupees(Math.round(net / 1000) * 1000)],
    [t("socSaves"), rupees(Math.round(saves / 1000) * 1000)], [t("socPayback"), t("years", (net / saves).toFixed(1))]];
  const dl = $("society");
  dl.innerHTML = "";
  for (const [k, v] of rows) {
    const wrap = document.createElement("div");
    const dt = document.createElement("dt");
    dt.textContent = k;
    const dd = document.createElement("dd");
    dd.textContent = v;
    wrap.append(dt, dd);
    dl.append(wrap);
  }
  $("rwa-msg").textContent = t("rwaMsg", kw, rupees(Math.round(net / 1000) * 1000), rupees(Math.round(saves / 1000) * 1000));
}

$("society-bill").addEventListener("input", renderSociety);
$("copy-rwa").addEventListener("click", async () => {
  const btn = $("copy-rwa");
  try {
    await navigator.clipboard.writeText($("rwa-msg").textContent);
    btn.textContent = t("copied");
  } catch (_) {
    const range = document.createRange();
    range.selectNodeContents($("rwa-msg"));
    const sel = window.getSelection();
    sel.removeAllRanges();
    sel.addRange(range);
    btn.textContent = t("copyFallback");
  }
  setTimeout(() => { btn.textContent = t("copy"); }, 2500);
});


// --- share a result; ask a question ------------------------------------------------------
function shareLink(data) {
  const a = data.analysis;
  const o = a.recommended;
  const url = location.origin + location.pathname;
  const text = o ? t("shareGo", o.kw, rupees(o.net_cost), o.payback_years.toFixed(1), url) : t("shareSkip", url);
  return "https://wa.me/?text=" + encodeURIComponent(text);
}

function renderAskExamples() {
  const box = $("ask-examples");
  box.innerHTML = "";
  for (const q of t("askExamples")) {
    const b = document.createElement("button");
    b.type = "button";
    b.className = "chip";
    b.textContent = q;
    b.addEventListener("click", () => { $("ask-input").value = q; ask(q); });
    box.append(b);
  }
}

async function ask(question) {
  $("ask-q").hidden = false;
  $("ask-q").textContent = question;
  $("ask-a").textContent = t("askThinking");
  try {
    const last = state.last && state.last.analysis.recommended
      ? { verdict: state.last.analysis.verdict, kw: state.last.analysis.recommended.kw, discom: state.last.analysis.discom_name } : undefined;
    const r = await post("/ask", { question, last });
    $("ask-a").textContent = r.answer;
  } catch (e) {
    $("ask-a").textContent = e.message || t("error");
  }
}

$("ask-form").addEventListener("submit", (e) => {
  e.preventDefault();
  const q = $("ask-input").value.trim();
  if (q) ask(q);
});


// --- the accountability table: real step durations by provider ----------------------------
landing.times = [];

function renderTimes() {
  const table = $("times");
  const rows = landing.times || [];
  $("times-empty").hidden = rows.length > 0;
  table.hidden = rows.length === 0;
  if (!rows.length || !landing.journey) return;
  const byId = Object.fromEntries(landing.journey.stages.map((s) => [s.id, s]));
  table.innerHTML = "";
  const head = table.createTHead().insertRow();
  for (const c of t("timesCols")) { const th = document.createElement("th"); th.textContent = c; head.append(th); }
  const body = table.createTBody();
  for (const r of rows) {
    const st = byId[r.stage];
    const row = body.insertRow();
    for (const c of [r.provider, st ? st.title[state.lang] || st.title.en : r.stage, st ? t("usual", st.days) : "",
                     t("usual", Math.round(r.median_days)), String(r.households)]) row.insertCell().textContent = c;
  }
}

async function loadTimes() {
  try { landing.times = (await getJSON("/stats/stages")).stages; } catch (_) { landing.times = []; }
  renderTimes();
}

// the gap, to scale: one square per lakh homes, filled where rooftop solar is already up
for (let i = 0; i < 100; i++) {
  const c = document.createElement("i");
  if (i < 41) c.className = "on";
  $("cells").append(c);
}

$("privacy-link").href = API + "/privacy";
applyLang();
loadStats();
loadJourney().then(loadTimes);
loadFacts();

// the hero chat plays once: the bill goes out, the bot types, the real reply comes back
function playDemo() {
  const phone = $("demo");
  if (!phone || (window.matchMedia && matchMedia("(prefers-reduced-motion: reduce)").matches)) return;
  phone.classList.add("playing");
  const status = $("demo-status");
  phone.querySelectorAll("[data-at]").forEach((el) => {
    setTimeout(() => {
      el.classList.add("shown");
      if (el.classList.contains("typing")) status.textContent = t("typing");
    }, +el.dataset.at);
    if (el.dataset.until) setTimeout(() => { el.classList.add("gone"); status.textContent = t("chatSub"); }, +el.dataset.until);
  });
}
playDemo();
if (location.hash) route(location.hash);
