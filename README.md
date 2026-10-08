# Surya Saathi ☀️

**Send a photo of your electricity bill. Get an honest answer about rooftop solar in a few seconds, in Hindi or English.**

Surya Saathi is a copilot for households considering rooftop solar under India's PM Surya Ghar scheme. It reads the bill and sizes the system from the household's own usage and the sunlight at their location. It works out the subsidy, loan EMI and payback, and it says *"don't"* when solar won't pay.

Built for the WeMakeDevs × AWS **Bharat Builds Tour: Environmental Hacks** (Track 3: Waste and Energy).

## The problem

- PM Surya Ghar aims for **1 crore solar homes by 31 March 2027**. About **41 lakh** were done by June 2026.
- CEEW's national survey of 17,000 households (June 2026) found that once a household applies, nearly two-thirds go on to install. **The drop-off happens before people apply.** They don't know how to start, can't judge whether it pays, and don't trust vendors.
- Among people who think solar is too expensive, **almost 3 in 4 don't know collateral-free loans exist.**
- **The subsidy only applies to made-in-India (DCR) panels.** If a vendor installs other panels, the claim fails at inspection, and no appeal fixes it.

Households that do install report **71% lower bills on average**. The value is real; getting people to the starting line is the hard part.

## What works today

| | Status |
|---|---|
| Solar calculator: sunlight → units → bill savings → payback, EMI, CO₂, plus an honest "skip" | ✅ live, 34 tests |
| Bill reader: photo or PDF → usage history, sanctioned load, provider (Bedrock vision) | ✅ live |
| Delhi providers: BSES Rajdhani, BSES Yamuna, Tata Power-DDL | ✅ |
| WhatsApp bot with Hindi voice notes | in progress |
| Quote checker: DCR panels, price per watt, missing items | next |
| Application guide through the PM Surya Ghar portal | next |

**Live API:** `https://26iznf3yc7.execute-api.ap-south-1.amazonaws.com`

```bash
curl -X POST https://26iznf3yc7.execute-api.ap-south-1.amazonaws.com/analyze \
  -H "content-type: application/json" \
  -d '{"discom":"TPDDL","sanctioned_kw":3,"lang":"hi","monthly_units":{"1":300,"2":280,"3":320,"4":420,"5":520,"6":560,"7":500,"8":450,"9":420,"10":360,"11":300,"12":310}}'
```

`POST /bill` takes `{"file_base64": "...", "media_type": "image/jpeg" | "image/png" | "application/pdf", "lang": "en" | "hi"}`.

## How the numbers work

Every estimate leans conservative on purpose. Bad vendors overpromise; this tool doesn't.

1. **Sunlight, month by month.** PVGIS (EU JRC, ERA5 data) models a tilted, south-facing system with 14% losses. ERA5 under-counts north India's winter smog, so each month is scaled down wherever NASA POWER's satellite data measures less sunlight. Delhi works out to **1,482 units per kW per year** (PVGIS alone says 1,623), and December drops about 20%.
2. **The bill.** The full DERC tariff: telescopic slabs, fixed charge per kW, each provider's PPAC, surcharges, electricity tax, and Delhi's subsidy (0–200 units free, 201–400 at half up to ₹800). The model is then adjusted to match the household's real bill amount, so charges we don't model are still counted.
3. **Net metering.** A month's surplus is banked against later months within the financial year. Anything left at year end earns only the export rate.
4. **Every size from 1 kW upward.** For each size: market cost (₹55–70k per kW), the central subsidy (₹30k per kW for the first 2 kW, ₹18k for the 3rd, capped at ₹78k), the collateral-free loan EMI (repo + 0.5%, 5.75% up to ₹2 lakh), 0.5% panel ageing a year, an inverter replacement in year 12, and 25 years of cash flow discounted at 8%. The best value wins, which often means a smaller system than a vendor would sell.
5. **CO₂.** CEA CO₂ Baseline Database v22.0: 0.675 t per MWh for FY 2025-26.

Assumptions not yet verified against primary sources are listed under `estimates` in [`src/surya/data/tariffs.json`](src/surya/data/tariffs.json).

## Privacy

The bill reader asks the model for usage, load, provider, amount and pincode only. **Name, address, phone and consumer number are never requested** (see [`bill_reader.py`](src/surya/bill_reader.py)). Bills are not stored.

## Architecture

```
            ┌──────────────── AWS (ap-south-1) ───────────────────────────────┐
 client ──► │ API Gateway (HTTP) ──► Lambda (Python 3.13, arm64)             │
            │                          ├─► Bedrock: Claude Haiku 5.5 / Nova 2 Lite (vision)
            │                          ├─► DynamoDB: sunlight cache per 0.1° cell
            │                          └─► CloudWatch Logs                    │
            └─────────────────────────────┬───────────────────────────────────┘
                                          └─► PVGIS (EU JRC) + NASA POWER
```

Infrastructure as code with **AWS SAM** ([`template.yaml`](template.yaml)).

## Run it yourself

```bash
python -m venv .venv
.venv/Scripts/pip install pytest boto3        # macOS/Linux: .venv/bin/pip
.venv/Scripts/python -m pytest                # offline, uses saved Delhi sunlight data

python scripts/try_it.py --discom BRPL --load 5 --units 380,350,420,560,720,780,690,610,560,470,390,400 --lang hi

pip install aws-sam-cli
sam build && sam deploy --guided
```

## Honest limits

- **Delhi only for now.** UP's published tariffs disagree across sources, so it's left out until checked against the UPERC order.
- **The PM Surya Ghar portal has no API.** Surya Saathi guides and tracks the application but can't submit it.
- **System prices are market estimates.** Always compare at least two vendor quotes.

## Data sources

- Sunlight: [PVGIS](https://re.jrc.ec.europa.eu/pvg_tools/en/), [NASA POWER](https://power.larc.nasa.gov/)
- Delhi tariff: [DERC PPAC order](https://www.derc.gov.in/sites/default/files/Order%20in%20Petition%20No.%2032_2025_PPAC_Q4_BRPL%20-11.08.2025.pdf), [rate summary](https://bridgewaypower.in/delhi-electricity-rate-2026)
- Scheme: [PM Surya Ghar overview](https://www.drishtiias.com/important-government-schemes/ministry-of-new-and-renewable-energy/pm-surya-ghar-muft-bijli-yojana-1), [DCR rule](https://www.securedengineers.com/insights/pm-surya-ghar-almm-non-dcr-module-exemption-explained/), [loan rates](https://www.solarsquare.in/blog/solar-loan-interest-rates/)
- Adoption: [CEEW rooftop solar study, June 2026](https://www.ceew.in/sites/default/files/final-ceew-rts-study-press-release-4june26.pdf)
- Emissions: [CEA CO₂ Baseline Database v22.0](https://cea.nic.in/wp-content/uploads/baseline/2026/09/User_Guide__Version_22.0.pdf)

## Built with

AWS Lambda, API Gateway, DynamoDB, Amazon Bedrock, CloudWatch, and AWS SAM. AI tools: Claude Code (Anthropic) assisted with research and code.

MIT licensed.
