# Surya Saathi ☀️

**A rooftop-solar companion for Indian households, from the electricity bill to the subsidy in the bank, and after.** It works on WhatsApp in Hindi and English, by photo, text or voice note.

Built for the WeMakeDevs × AWS **Bharat Builds Tour: Environmental Hacks** · Track 3, Waste and Energy.

- **Website:** https://main.d3frlgja2w8q15.amplifyapp.com
- **WhatsApp:** Twilio sandbox, +1 415 523 8886 (send the join code first)
- **API:** https://26iznf3yc7.execute-api.ap-south-1.amazonaws.com

## The problem

India wants **1 crore** solar homes by March 2027 under PM Surya Ghar. About **41 lakh** were done by June 2026. A national survey of 17,000 homes (CEEW, June 2026) found that once people apply, most go on to install. **The drop-off happens before they apply**: they can't tell if it pays, who to trust, or what to do next. Three in four people who think solar is expensive don't know collateral-free loans exist.

The people who do go ahead hit traps:
- **Vendor traps:** non-DCR panels void the whole subsidy, and subsidy promises run above the scheme cap.
- **Paperwork rejections:** names that don't match across Aadhaar, the bill and the bank account.
- **Stalled steps:** net meters stuck for weeks, and subsidies held up by an unredeemed e-token.
- **After installation:** export units never credited on the bill (MNRE flagged this in July 2026), and output quietly lost to Delhi's dust and smog.

Delhi's newest deal goes unnoticed too. Homes using up to 400 units a month can now get **3 kW at ₹0 upfront** (Cabinet, Sep 2026), yet only about 10,000 of 2.3 lakh target homes are done.

## What it does

| Stage | What Surya Saathi does |
|---|---|
| **Decide** | **Bill photo → right size, cost after subsidy, EMI, payback, CO₂**, or an honest "skip". Months missing from the bill are estimated from local temperature. A smaller system wins when it gets within 10% of the best 25-year value. Delhi's ₹0-upfront and state top-up are flagged when they apply |
| **Save now** | **Bill doctor**: flags sanctioned load far above your actual peak (₹5,500/yr on our test bill), estimated readings, one-off charges, and missing export credit |
| **Know your help** | **Schemes**: the central subsidy for all 36 states and UTs (higher in hill and North-East states), each state's top-up shown separately with its conditions and source (Delhi: ₹26,000/kW up to ₹78,000, from solar.delhi.gov.in), the 5.75% collateral-free loan, and a **budget planner** for the months of EMI before the subsidy arrives |
| **Choose** | **Get quotes**: one request; every vendor's quote is checked by the same rules and compared by what you pay **after subsidy**, so a cheap quote with imported panels shows up as the most expensive. Requests from one PIN code pool into a group price at five homes. The **quote checker** reads quotes you already have, and the **scam check** flags forwarded offers (fees, look-alike portals, OTP requests, subsidy over the cap, "free solar", pressure to decide today). On the **vendor side**, installers see open requests by area (never the full PIN) and send a quote that the same rules check before it goes out |
| **Apply** | **8-step plan on Step Functions**, starting with a pre-flight check for the common rejections. A nudge when a step runs long. **STUCK** drafts a complaint for whoever is holding things up: helpline, then nodal officer, then grievance portal, then RTI. The household sends it |
| **Install** | **Is this the panel you paid for?** A photo of a panel's back label is read for the maker, wattage, serial and origin, and flagged when the module or its cells are imported, the DCR mark is missing, the wattage differs from the quote, or the serial was already checked at another home. The portal flags repeated serials, and since May 2026 a vendor's undertaking no longer clears them, so this runs before the final payment |
| **Get paid** | E-token and claim-deadline reminders inside the same plan |
| **Keep it running** | **Dust this week**: a live CAMS forecast (via Open-Meteo) rates each day by India's AQI bands for PM10 and picks the day to clean the panels, after the dust settles. A **solar passport** of signing and handover checks, **promised vs actual** generation with a note for the installer, the **first bill's energy flow** (generation is not export), and **support requests** with the evidence to attach. On WhatsApp, an inverter photo is checked against what the panels should make |
| **No roof of your own** | **Flats and societies**: common-area solar at ₹18,000/kW, a calculator, and a ready message for the RWA |
| **Any question** | Typed or spoken, in Hindi or English. A Bedrock tool-use loop works the answer out with the product's own tools: the scheme list for a state, a rough estimate from a typed bill, the scam check, the dust forecast and the household's application step. Places are found with Amazon Location Service, and every answer says which tools it used. Voice note in (Transcribe), voice note out (Polly) |

## Knowledge that keeps itself current

Fuel surcharges, state top-ups and prices change every few months, so a hand-made table goes stale. Instead:

1. **Bills teach tariffs.** Every bill prints its own slab rates. Each one read updates that provider's tariff anonymously, and **a bill from any state works on day one**. On our real BSES Rajdhani photo, the reader recovers DERC's exact 200/400-unit slabs.
2. **Quotes teach prices.** Each quote checked adds a ₹/kW price for its state. The fair range becomes the middle half of recent local quotes.
3. **People verify facts.** The public "Rates & rules" board shows each fact's source, last confirmation and change reports. Anyone can confirm a fact or report a change with evidence, and three reports flag it for review.
4. **Watchers check sources.** An EventBridge Scheduler job re-reads official pages weekly and flags facts whose source changed.

## Architecture

```mermaid
flowchart LR
  WA[WhatsApp<br/>Twilio · Meta] --> GW[API Gateway<br/>HTTP API]
  WEB[Website<br/>Amplify Hosting] --> GW
  GW --> HOOK[Lambda<br/>webhook] -->|async| WORK[Lambda<br/>worker]
  GW --> API[Lambda<br/>bill · quote · facts API]
  WORK --> BR[Bedrock<br/>Nova 2 Lite]
  API --> BR
  WORK --> TR[Transcribe] & PO[Polly] & S3[(S3 voice<br/>1-day TTL)]
  WORK --> SF[Step Functions<br/>8-stage journey] --> JL[Lambda<br/>nudges]
  WORK & API --> DDB[(DynamoDB<br/>knowledge · sessions · sunlight · marketplace)]
  API --> AQ[Open-Meteo<br/>dust forecast]
  WORK & API --> LOC[Amazon Location<br/>places]
  SCH[EventBridge Scheduler<br/>weekly] --> WATCH[Lambda<br/>watcher] --> DDB
  API --> SUN[PVGIS + NASA POWER]
```

- **AWS services:** Lambda, API Gateway, Bedrock, Step Functions, EventBridge Scheduler, DynamoDB, S3, Transcribe, Polly, Amazon Location Service, Amplify Hosting, SSM Parameter Store, CloudWatch.
- **AWS open source:** deployed with **AWS SAM**, one template ([`template.yaml`](template.yaml)) in ap-south-1.
- **Reliable bill reading:** every bill is read **three times in parallel** and only what the readings agree on is kept. Phone photos of skewed tables otherwise drift, so this matters.

## How the numbers work

- **Sunlight:** PVGIS models a tilted system with losses, scaled down month by month wherever NASA POWER's satellite data is lower (north India's winter smog). That gives Delhi 1,482 units per kW a year, against 1,623 from PVGIS alone.
- **Bill:** built the way the bill prints it (slabs, fixed charge, fuel surcharge, 8% surcharge, pension surcharge, tax, Delhi's 200-unit subsidy). It reproduces a real BRPL bill within 3%, then gets calibrated on the bill's own energy charge.
- **Value:** every size is evaluated over 25 years: subsidy, collateral-free loan EMI, 0.5%/yr panel ageing, an inverter in year 12, discounted at 8%.
- **Estimates are labelled as estimates.** The aim is a trustworthy direction for a household, not a bank-grade valuation.

## Privacy

- **Bills:** the reader never asks for name, address, phone or consumer number, and bill images aren't stored.
- **Voice:** voice notes are deleted after a day.
- **Panel serials** are kept only as SHA-256 hashes, for two years, so a serial seen at a second home can be flagged.
- **What we keep:** the WhatsApp number, language, last estimate and journey stage, deleted automatically after 90 days. Sample comparisons expire after 30 days and are excluded from real impact counters and price learning.
- **Deleting:** **DELETE MY DATA** deletes the WhatsApp-linked comparison as well as the session. Website comparisons have a delete control. Passport records stay in browser storage only when explicitly saved; use its clear control and delete exported copies separately.

## Run it

```bash
python -m venv .venv && .venv/Scripts/pip install pytest boto3 aws-sam-cli
.venv/Scripts/python -m pytest            # 205 tests, offline
sam build && sam deploy --guided          # the whole backend
python scripts/deploy_web.py              # the website, to Amplify
```

For a local review without cloud credentials:

```bash
python scripts/serve_local.py --port 8765
# Open http://127.0.0.1:8765
```

The local server runs the deterministic tools and uses captured Delhi sunlight for the sample estimate. Bill/quote image reading and AI answers return a clear cloud-backend requirement. It binds to localhost; production URLs and deployments are separate. Run `sam validate --lint --region ap-south-1` to validate the new API routes, market table, TTL and IAM policy before deploying.

## Honest limits

- **The PM Surya Ghar portal has no API.** The journey guides and tracks the application; the household submits it.
- **WhatsApp commands:** `QUOTES` and `CHOOSE 1` (compare and pick), `SCAM <offer>`, `SCHEMES UP`, `PASSPORT`, `DUST`, plus `APPLY`, `DONE`, `STUCK`, `FLAT`, `SYSTEM 3.3` and `DELETE MY DATA`. Photos are sorted automatically: a bill, a quote, an inverter screen or a panel label.
- **WhatsApp:** Meta's Cloud API integration is built, but Meta only lets verified businesses reply, so the demo runs on Twilio's sandbox.
- **Nudges days apart** would need an approved WhatsApp template in production. Demo mode (`APPLY DEMO`) shortens a day to 4 seconds.
- **State assistance needs local confirmation.** The schemes selector covers central rules for all 36 states and union territories. Delhi, Uttar Pradesh and Assam have government source links; other reviewed entries distinguish secondary reports from official guidance. Unreviewed local support is shown as unknown.
- **The demo vendors are fictional.** The marketplace's four vendors, their replies and scorecards are sample data, labelled on every screen, each showing a different trap. Real vendors can answer requests, and their scores come only from the quotes they actually send. No real company is shown with prices it didn't quote. The comparison that runs when someone opens Get quotes is a sample: vendors see one, labelled, only when an area has no real requests.
- **A typed-bill estimate is rough.** It sizes by the rule of thumb that 1 kW makes about 4 units a day and prices at the typical local rate per kW; a bill photo gives the full estimate.
- **Ownership checks are evidence aids.** They do not certify equipment safety, DCR compliance, warranty liability or a monetary bill settlement. Generation review is manual and uses a completed month; low output alone does not diagnose dust.
- **The panel check reads what's printed.** It can't spot a forged label, and the duplicate-serial check only knows serials checked through Surya Saathi. The DCR certificate and MNRE's ALMM list remain the proof.
- **Support packs prepare the next conversation.** They distinguish monitoring, generation, billing, documents and maintenance, record dates and list relevant evidence. They do not submit tickets. Elapsed days are dated records, not regulatory deadlines.

## Built with

**AWS**, as above.

**AI tools:** Claude Code (Anthropic) and Codex (OpenAI) helped with research, code and writing. Amazon Bedrock (Nova 2 Lite) runs inside the product.

**Data sources:**
- Sunlight: [PVGIS](https://re.jrc.ec.europa.eu/pvg_tools/en/) and [NASA POWER](https://power.larc.nasa.gov/)
- Grid emissions: [CEA CO₂ database v22](https://cea.nic.in/wp-content/uploads/baseline/2026/09/User_Guide__Version_22.0.pdf)
- Adoption: [CEEW rooftop solar study](https://www.ceew.in/sites/default/files/final-ceew-rts-study-press-release-4june26.pdf)
- Dust and smog forecast: [Open-Meteo air quality](https://open-meteo.com/en/docs/air-quality-api) (CAMS); soiling losses from the Delhi study summarised by [Renewable Watch](https://renewablewatch.in/2018/12/22/soiling-analysis/)
- Scheme and policy facts: listed with their sources in [`facts.json`](src/surya/data/facts.json)

MIT licensed.
