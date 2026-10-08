# Surya Saathi: product plan

Goal: win Track 3 (Waste and Energy) of WeMakeDevs × AWS Environmental Hacks, Oct 8–11 2026.
Judges see only the 3-minute video (rules: "a feature shown only in the writeup, and not in the video, does not count").

## What real households struggle with (research, 8 Oct)

| Pain | Evidence | What we do about it |
|---|---|---|
| Don't know if it pays, or how to start | CEEW 2026 survey of 17,000 homes: the drop-off is *before* applying; 3 in 4 who think it's expensive don't know about loans | Bill photo → honest answer with EMI ✅ |
| Delhi's new deal is invisible | Cabinet 2 Sep 2026: ≤400 units/month → up to 3 kW at **₹0 upfront**; others get **+₹78,000** from Delhi; only 10,073 of 2.3 lakh target done ([ANI via DesiTalk](https://desitalkchicago.com/delhi-solar-policy-gets-major-push-2-30-lakh-rooftops-targeted-by-march-2027/), [Bridgeway](https://bridgewaypower.in/delhi-solar-policy-2026)) | Delhi bonus check on every Delhi bill |
| Vendor traps | Non-DCR panels void the subsidy; cash outside the portal; non-empanelled vendors | Quote checker ✅, then side-by-side quote comparison |
| Paperwork rejections | Name mismatch across Aadhaar / bill / bank, Aadhaar not seeded to bank, bill older than 90 days, pending dues, rented roof without NOC, size above sanctioned load ([guide](https://righttoinformation.wiki/practical-guides/rooftop-solar-subsidy-not-credited-application-rejected)) | Pre-flight checklist before applying |
| Stuck at net meter | Slowest step; 3–6 week backlogs at BSES/TPDDL ([guide](https://bridgewaypower.in/blog/pm-surya-ghar-yojana-2026-guide)) | Step tracker with nudges and an escalation ladder |
| Subsidy never arrives | E-token must be redeemed; bank name mismatch; Phase II claims must reach MNRE by **30 Nov 2026** ([Energetica](https://www.energetica-india.net/news/mnre-extends-pm-surya-ghar-cfa-claim-deadline-to-november-30-2026)) | Reminders, plus drafted complaints (DISCOM nodal officer, portal grievance, 15555, CPGRAMS, RTI) |
| Output quietly drops | Delhi dust costs 0.3–0.6%/day, ~10%/month uncleaned; smog another ~6–12% ([Renewable Watch](https://renewablewatch.in/2018/12/22/soiling-analysis/), [PMC study](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC12658225/)) | Monthly performance check against expected output, plus cleaning reminders |

Patterns from winners we reuse: one decision at one moment (AeroZee), work with existing systems (Kabadiwalla Connect), an agent that acts with the human in control (First Commit winners Suraksha and Beacon), voice in Indian languages, a live link anyone can open, real data and tests.

## The product: from bill to subsidy, and after

1. **Decide.** Bill photo → size, cost, subsidy, EMI, payback, an honest "skip". ✅ Delhi bonus check.
2. **Choose a vendor.** Quote checker ✅. Compare up to 3 quotes side by side.
3. **Apply.** Pre-flight checklist. Step-by-step tracker for the 8 portal stages (Step Functions), with nudges when a stage stalls (EventBridge Scheduler).
4. **Get paid.** E-token reminder, the CFA claim deadline, and a drafted complaint for whoever is holding things up. The household sends it; we never act for them.
5. **Keep it running.** Monthly check: photo of the inverter's monthly units vs what the panels should make that month; cleaning reminders.

Channels: WhatsApp (Twilio Sandbox live; Meta Cloud API built, blocked on business verification), website on Amplify, Hindi voice notes (Transcribe in, Polly out).

## Build order and status

- [x] Calculator, Delhi tariff from a real bill, conservative sunlight, honest skip, size tie-break
- [x] Bill reader: 3 parallel reads + consensus; temperature-based fill for missing months
- [x] Quote checker (API, web, WhatsApp)
- [x] WhatsApp via Twilio Sandbox, website on Amplify
- [ ] Delhi bonus (zero-upfront eligibility, state top-up scenario)
- [ ] Journey: pre-flight checklist, stage tracker (Step Functions + EventBridge), escalation drafts
- [ ] Website redesign: landing, how it works, live impact counter, shareable result
- [ ] Hindi voice notes + questions answered from the household's own result and a scheme FAQ
- [ ] Compare quotes side by side
- [ ] Monthly performance check + cleaning reminders
- [ ] README, architecture diagram, Builder Center blog draft, video script; make repo public

## AWS used

Lambda, API Gateway (HTTP), DynamoDB, Bedrock (Nova 2 Lite), Amplify Hosting, SSM Parameter Store, CloudWatch Logs, AWS SAM (open source). Planned: Step Functions, EventBridge Scheduler, Transcribe, Polly, S3.
