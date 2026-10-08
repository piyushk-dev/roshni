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
| Save now, solar or not | Paying for unused sanctioned load (fixed charges track it); estimated readings; unexplained "other charges" | **Bill doctor**: right-size sanctioned load from the bill's max demand, flag estimated readings, odd charges, missing subsidy |
| Choose | Non-DCR panels void the subsidy; inflated subsidy promises; overpricing | Quote checker ✅, live price benchmark, compare quotes side by side |
| Apply | Rejections from name mismatches, Aadhaar not seeded to bank, old bill, dues, no NOC | Pre-flight checklist |
| Apply | Net meter is the slowest step | Step tracker (Step Functions) with nudges when a stage stalls |
| Get paid | E-token not redeemed, bank mismatch, claim deadline 30 Nov 2026 | Reminders + drafted complaint for whoever is holding it up (DISCOM nodal officer, portal grievance, 15555, CPGRAMS, RTI). The household sends it |
| Live with it | Dust and smog cut output 10%+ a month; export credits not applied (installer complaints) | Monthly check: inverter reading vs expected output; post-solar bill check for export credit; cleaning reminders |
| No roof of your own | Most city homes are flats | Apartment / RWA mode: common-area solar (₹18,000/kW), virtual net metering explainer, a message to send the RWA |

Channels: WhatsApp (Twilio Sandbox live; Meta Cloud API built, waiting on business verification), website on Amplify, Hindi voice notes.

## Build order

- [x] Calculator, bill reader (3-read consensus), quote checker, WhatsApp, website, Delhi bonus
- [ ] Self-updating knowledge: bill-derived tariffs (any state), price observations, facts registry with confirm/report, weekly watcher
- [ ] Journey: checklist, stage tracker with nudges, escalation drafts
- [ ] Bill doctor
- [ ] Website redesign around the whole journey, rates & rules page, live impact counter, share card
- [ ] Hindi voice notes + answers to questions
- [ ] Apartment / RWA mode, post-install monthly check
- [ ] README, architecture diagram, blog draft, video script; make repo public

## AWS

Live: Lambda, API Gateway, DynamoDB, Bedrock (Nova 2 Lite), Amplify Hosting, SSM Parameter Store, CloudWatch, AWS SAM.
Adding: Step Functions (journey), EventBridge Scheduler (nudges, watcher), Transcribe + Polly (voice), S3 (voice audio).
