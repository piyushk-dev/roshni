# Surya Saathi: product plan

Goal: win Track 3 (Waste and Energy) of WeMakeDevs × AWS Environmental Hacks, Oct 8–11 2026.
Judges see only the 3-minute video, so every feature below has to be showable.

## One line

A WhatsApp-first companion that takes an Indian household from "is solar worth it?" to panels on the roof, money in the bank and output that stays high. It gets more accurate with every bill and quote it sees.

## Principle: knowledge that keeps itself current

Exact rates change every month (fuel surcharges, state top-ups, prices), so hand-verified tables go stale. Instead:

| Source | What it teaches | How |
|---|---|---|
| **Every bill** | The provider's live tariff: slabs, surcharges, fixed charges | Bills print their own rates. An unknown provider uses its own bill's rates, so **any state works on day one** |
| **Every quote** | Real ₹/kW prices by city | The "fair price" is a rolling median of recent quotes, with a seed value until enough arrive |
| **People** | State schemes, deadlines, rule changes | Public "rates & rules" page: each fact shows source, last confirmed, confirmations. Anyone can confirm or report a change with evidence; changes go live after several confirmations or moderator review |
| **Watchers** | Changes on official pages (MNRE, regulators, state portals) | Weekly scheduled check (EventBridge Scheduler); a changed page marks its facts "may be outdated" for review |

Every number shown carries where it came from and how fresh it is. No personal data is kept, only rates and prices.

## Problems → features

| Stage | Real problem (research) | Feature |
|---|---|---|
| Decide | Don't know if it pays; drop-off happens before applying (CEEW 2026) | Bill photo → honest answer ✅ |
| Decide | Delhi's ₹0-upfront deal is unknown; only 10k of 2.3 lakh homes done | State bonus check ✅ (Delhi), more states via community facts |
| Decide | State help differs and is scattered across portals | **Schemes** for all 36 states and UTs, each with its source ✅; budget planner for the EMI months before the subsidy arrives ✅ |
| Save now, solar or not | Paying for unused sanctioned load (fixed charges track it); estimated readings; unexplained "other charges" | **Bill doctor**: right-size sanctioned load from the bill's max demand, flag estimated readings, odd charges, missing subsidy |
| Choose | Non-DCR panels void the subsidy; inflated subsidy promises; overpricing; scam calls and forwards | Quote checker ✅; **Get quotes** board ranked by price after subsidy, with PIN-code group pricing ✅ (fictional demo vendors, labelled); vendor page where real installers answer requests ✅; scam check ✅ |
| Apply | Rejections from name mismatches, Aadhaar not seeded to bank, old bill, dues, no NOC | Pre-flight checklist |
| Apply | Net meter is the slowest step | Step tracker (Step Functions) with nudges when a stage stalls |
| Install | Cheaper panels are hard to spot on the roof; the portal flags repeated serials (May 2026) | **Panel label check** from a photo: origin of module and cells, DCR mark, wattage vs quote, serial already checked at another home ✅ |
| Get paid | E-token not redeemed, bank mismatch, claim deadline 30 Nov 2026 | Reminders + drafted complaint for whoever is holding it up (DISCOM nodal officer, portal grievance, 15555, CPGRAMS, RTI). The household sends it |
| Live with it | Dust and smog cut output 10%+ a month; export credits not applied (installer complaints) | Inverter photo vs expected output ✅; first-bill energy flow ✅; **Dust this week** picks the cleaning day from a live forecast ✅; solar passport and support requests ✅ |
| No roof of your own | Most city homes are flats | Apartment / RWA mode: common-area solar (₹18,000/kW), virtual net metering explainer, a message to send the RWA |

Channels: WhatsApp (Twilio Sandbox live; Meta Cloud API built, waiting on business verification), website on Amplify, Hindi voice notes.

## Build order

- [x] Calculator, bill reader (3-read consensus), quote checker, WhatsApp, website, Delhi bonus
- [x] Self-updating knowledge: bill-derived tariffs (any state), price observations, facts registry with confirm/report, weekly watcher
- [x] Journey: checklist, stage tracker with nudges, escalation drafts (verified live, incl. nudge on timeout)
- [x] Bill doctor (sanctioned load vs peak, estimated readings, one-off charges, missing exports)
- [x] Website redesign around the whole journey, rates & rules board, live impact counter (share card still open)
- [x] Hindi voice notes (Transcribe/Polly) + grounded answers, also on the website (POST /ask)
- [x] Flats/RWA mode with calculator; post-install output check from an inverter photo; photo classifier
- [x] README, architecture diagram, blog draft (docs/blog.md), video script (docs/video-script.md)
- [x] Share result on WhatsApp; accountability board (real step times by provider)
- [x] Get quotes: one request, quotes compared after subsidy, group pricing by PIN code, demo vendors that each show a trap; vendor page for real installers
- [x] Schemes for all 36 states with sources, budget planner, scam check
- [x] After install: dust this week (live CAMS forecast), solar passport, promised vs actual, first bill, support requests, panel label check
- [ ] Make the repo public before submitting; record the video; publish the blog

## AWS

Live: Lambda, API Gateway, DynamoDB (with TTL and conditional writes), Bedrock (Nova 2 Lite), Step Functions (journey), EventBridge Scheduler (watcher), Transcribe + Polly (voice), S3 (voice audio), Amplify Hosting, SSM Parameter Store, CloudWatch, AWS SAM.
