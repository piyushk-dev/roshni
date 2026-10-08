# Surya Saathi: product research and decisions

Research conducted 8 October 2026. Implementation branch: `codex/product-expansion`, based on `4e92684`. The Desktop `main` checkout is separate.

## Product thesis

Help a household make a suitable solar purchase, get it commissioned, and retain the evidence needed to keep it performing. The defensible opportunity is an independent, Hindi-friendly buyer companion across installers and inverter brands. A general solar chatbot or another output dashboard is a weaker proposition: installers and manufacturers already offer both guidance and monitoring.

The proposed **solar passport** connects the written quote, installation checks, monthly generation promise, service records and first bill. The implementation currently offers quote preview, checklist progress, monthly generation review, a drafted service note and energy reconciliation. Saving is explicit and local to the browser; a text export travels with the household. It does not connect to government records or inverter telemetry.

## What the evidence says

Reddit is qualitative discovery. These posts are self-reported, may have missing context and do not establish prevalence, legal fault or the quality of any named company. Official rules and technical documentation inform calculations; enterprise pages establish what competitors publish, not independent proof of their performance.

| Household job | Evidence and interpretation | Product response |
|---|---|---|
| “Will this solve the problem I actually have?” | A [29 September Assam post](https://www.reddit.com/r/LegalAdviceIndia/comments/1wtemme/solar_installation_went_ahead_without_a_site/) describes buying solar for power cuts without understanding the on-grid limitation or receiving a proper survey and written plan. This suggests an expectation gap before purchase. | Explain the outage limitation before signing; require a written survey, component scope and a separate backup design when needed. |
| “Can I afford the period before the subsidy?” | A [31 July Lucknow post](https://www.reddit.com/r/lucknow/comments/1vbofle/solar_panel_subsidy/) describes a functioning plant, continued EMIs and a long subsidy wait. A [loan discussion](https://www.reddit.com/r/Chhattisgarh/comments/1vbc14c/solar_surya_ghar_loan_subsidy_doubt/) raises the distinction between reducing tenure and EMI. | Show gross funding, own contribution, EMIs and interest during a selectable wait. Label reduced EMI as conditional on bank recasting. Do not subtract unverified state help from cash required. |
| “What exactly is covered after installation?” | A [warranty discussion](https://www.reddit.com/r/delhi/comments/1vzoj5n/which_solar_panels_and_brands_offer_the_best/) asks about inspection and replacement timelines. A [service-contract discussion](https://www.reddit.com/r/gwalior/comments/1qdlb2w/rooftop_solar_system_suggestions/) highlights verbal maintenance promises and warranty ambiguity. | Capture service frequency, response commitments and exclusions before signing. Preserve invoice, serials, monitoring access and written warranties at handover. |
| “Why am I still getting a bill?” | [Kerala discussions](https://www.reddit.com/r/Kerala/comments/1cib2s3/did_kseb_already_implemented_gross_metering/) show confusion between total generation and grid export. | Explain self-consumption = generation − export; household use = self-consumption + import. Compare meter export with the bill for the same dates. Do not claim every state nets money in the same way. |
| “Who should I choose?” | An [Odisha homeowner](https://www.reddit.com/r/Odisha/comments/1tovz54/how_do_i_select_a_good_rooftop_solar_vendor_for/) asks how to assess an installer and an unusually large subsidy promise. [CEEW’s national consumer study](https://www.ceew.in/publications/what-shapes-rooftop-solar-decisions-in-indian-households) examines adoption bottlenecks across the customer journey. | Compare scope, DCR, advance and net cost on one basis. Use current official vendor lists. A directory entry is not certification or a star rating. |
| “Is low output dust, weather or a fault?” | [CEEW’s maintenance study](https://www.ceew.in/publications/how-big-is-india-residential-rooftop-solar-maintenance-market) describes service and maintenance gaps. | Compare a completed month against a written monthly estimate, then ask for outage, weather, inverter and service evidence. A cleaning reminder is a scheduling prompt, not a dust diagnosis. |

## Enterprise products: what to learn and what to add

| Product | Published capability | Implication for Surya Saathi |
|---|---|---|
| [SolarSquare GoodZero](https://www.solarsquare.in/know-more-solar/) | Monitoring, maintenance and a savings proposition. | Promised versus actual generation is a familiar customer workflow. Extend it into portable evidence that works across installers. |
| [SolarSquare Blue maintenance agreement](https://www.solarsquare.in/blue-tnc/) | Detailed eligibility, visits, service and exclusion terms, including third-party installations. | “Five years maintenance” is not enough information. Ask which agreement, number of visits, response commitment and exclusions apply. |
| [Assure by SolarSquare](https://play.google.com/store/apps/details?hl=en_US&id=com.assure.sse) | Maintenance and repair for rooftop owners, including other installers’ customers. | A neutral service handoff can be useful after the original installer stops responding. Booking requires a real service integration and consent; the prototype only drafts the request. |
| [Freyr SunPro](https://freyrenergy.com/solar-system-for-home-in-eluru/) | Monitoring and maintenance described as part of the customer experience. | Show an actionable next step alongside a generation number. Avoid presenting a dashboard alone as novel. |
| [Enphase Care](https://enphase.com/homeowners/enphase-care) | Monitoring, remote troubleshooting and service/claim support. Its published service geography differs from India. | Borrow the detect → investigate → document → service loop; do not imply Enphase Care is available here or integrate equipment without access. |
| [Enphase billing guidance](https://enphase.com/learn/home-energy/explore-your-system/utility-bill-and-enphase-app) | Explains consumption, production and grid import/export. | Add a clear energy balance before blaming the DISCOM. Distinguish system production from settlement on the bill. |
| [Tata Power Solaroof](https://www.tatapower.com/solaroof) | An installation and service network with a national enquiry channel. | Route households to real businesses and official local registration checks. National marketing reach does not guarantee service at every PIN code. |

## Priority decisions

These are qualitative PM judgments, not invented RICE scores. Reach needs a pilot baseline; confidence reflects evidence quality, and effort reflects this codebase.

| Priority | Slice | Reason | Boundary |
|---|---|---|---|
| P0 | Real directory + comparable quote terms | Existing quote checker makes this inexpensive; reduces the gap between learning and choosing. | Profiles are sourced. Instant offers, prices and discounts are explicitly sample data. Risk examples are anonymous. |
| P0 | Cash needed while subsidy is pending | High-cost decision, strong qualitative pain and bank terms that can be checked. | Illustrative floating-rate amortisation, no moratorium, central assistance only; no loan application or approval claim. |
| P0 | Signing + handover passport | Prevents missing evidence when a dispute occurs; an accessible mobile demo. | User ticks observed evidence; no identity uploads or automatic DCR certificate. |
| P1 | Promise review + service note | Retention beyond installation and a direct environmental connection to sustained generation. | Full comparable month, no automatic fault diagnosis or warranty payout. |
| P1 | First-bill energy reconciliation | Explains a recurring confusion cheaply and across DISCOMs. | No monetary settlement engine for unreviewed states; no battery flow model. |
| P1 | 36-region schemes selector | Extends the useful national component without pretending all tariffs and top-ups are identical. | Unreviewed state support is explicitly unknown, not “none”. |

## Hackathon narrative

**“From an attractive solar quote to a purchase you can verify.”** Show one household through three moments: avoid a subsidy/advance trap, plan the wait without assuming free cash, then compare production and billing evidence after installation. Switch to Hindi once. Finish with an exported passport and the next action the household can take.

This is a demo strategy, not a promise of winning. Its strengths are a concrete user, explainable calculations, visible failure handling, existing AWS infrastructure and continuity across purchase stages. Show a small number of decisions end to end instead of narrating every screen.

The [official Environmental Hacks page](https://www.wemakedevs.org/aws/env) lists impact, AWS use, usability, execution and the recorded demo as judging criteria. The [organiser's announcement](https://www.wemakedevs.org/blogs/announcing-environmental-hacks) specifically encourages a clear action beyond a dashboard. The proposed passport story is a PM inference from those criteria, not a reported winning formula.

| Judging criterion | Evidence to show in the video |
|---|---|
| Environmental impact | Explain how a suitable purchase and documented service help sustain rooftop generation. Label CO₂ estimates as modelled potential, not measured impact. |
| AWS | Show the existing architecture and SAM validation of the new routes/table. Distinguish the live original backend from this locally reviewed branch. |
| Usability | Complete one household journey, show Hindi and a phone layout, and explain the next action. |
| Execution | Calculate, compare, save and export real UI results; keep unconnected government/vendor integrations out of the claim. |
| Demo | Use the three-minute script, capture the actual working product and verify the video link before submission. |

The [tour rules](https://www.wemakedevs.org/aws/rules) require a new build during the event, a public repository, a video under three minutes, an AWS demonstration and a short write-up including AI tools used. Verify the event start and repository history before submitting; extending an old project does not by itself establish eligibility. Submission and publishing are outside this implementation task.

## Expand responsibly across states

The branch supports central-assistance lookup in all **28 states and 8 union territories**, including the existing higher-rate state list. It does not claim audited savings calculations or researched local vendors everywhere.

Maintain independent records for state, DISCOM, tariff period, settlement method, top-up conditions, application route and effective dates. A state selector alone cannot capture multiple utilities, consumer categories, net-billing versus banking, or policy transitions. Where bills teach tariffs, show the bill-derived provenance and estimated surcharges. Never use a Delhi settlement assumption as an all-India guarantee.

Next rollout: Delhi for the existing bill pipeline, UP for a sourced top-up, Assam for special-rate assistance and utility-led differences, and Kerala for energy-flow comprehension. For each, interview at least five households, one installer and one support/nodal contact; these interviews have not been conducted. Verify the live policy source before broadening automated calculations.

## Official rules checked and incorporated

- [MNRE residential CFA guidelines](https://mnre.gov.in/notice/operational-guidelines-for-implementation-of-the-component-central-financial-assistance-to-residential-consumers-of-pm-surya-ghar-muft-bijli-yojana/): use conditional residential assistance, not a universal cash entitlement.
- [MNRE DCR verification notice](https://mnre.gov.in/en/notice/solar-dcr-verification-portal-reg/): retain evidence for domestic **cells and modules**, delivered serial numbers and invoice. A label image or ALMM listing alone is insufficient.
- [SBI loan page](https://sbi.bank.in/web/sbi-green/green-loans/personal/pm-surya-ghar-loan-for-solar-roof-top): published 5.75%/7.90% floating rates, minimum 10% margin, maximum ₹6 lakh and 120 months. Check rate and sanction terms with the lender.
- [Delhi state subsidy](https://solar.delhi.gov.in/page/state-subsidy): up to ₹26,000/kW within the first 3 kW, with the ₹78,000 and trusteeship bid-cost-minus-central-assistance caps. Replaced the previous automatic central-matching assumption.
- [Delhi consumer consent](https://solar.delhi.gov.in/consumer-consents): utility-led installation assigns the vendor and redeems assistance through the implementing agency. Do not describe that route as an unrestricted consumer-chosen cash subsidy.
- [Delhi vendor page](https://solar.delhi.gov.in/page/empaneled-vendors): points to the current DISCOM-specific national lists. Published installer websites do not establish current empanelment.
- [UPNEDA brochure](https://upneda.org.in/MediaGallery/Documents/GridConnected_RSS.pdf): ₹15,000/kW state help capped at ₹30,000, separate from central assistance.
- [APDCL ULA bidding document](https://apdcl.org/website/docs/tender_2024_25/BidDocumentRTSPMSGMBY.pdf): identifies special-category central rates and a state assistance component. Display route conditions separately.

## Real business profiles

[SolarSquare Delhi](https://www.solarsquare.in/rooftop-solar-in-delhi/), [Alien Energy Delhi NCR](https://alienenergy.in/solar-energy-company-delhi/), [Bridgeway Power](https://bridgewaypower.in/), [Freyr Energy Hyderabad](https://freyrenergy.com/hyderabad/) and [Tata Power Solaroof](https://www.tatapower.com/solaroof). Profiles describe published offerings and enquiry regions. There is no partnership, contact exchange, verified registration, imported-panel allegation, fabricated portal grade or invented customer outcome.

## Pilot and business model

North-star proposal: households that complete a verified commissioning **and** understand their first bill. Track estimate → actual written quote → documented handover → first-bill review, plus median unresolved service time. Measure false-positive warning rate, time to understand import/export and unsupported subsidy claims. These are proposed metrics, not measured impact.

Run task-based interviews with quote-owning households. Ask them to explain their upfront requirement, backup behaviour, DCR evidence and export credit in their own words. Compare comprehension and completion against a simple calculator. Do not count sample requests as real conversions or inferred CO₂ as realised reductions.

Possible revenue: disclosed service coordination fees or an installer workflow subscription for evidence packs and service tickets. Keep household advice and warning logic independent of payment; do not sell a “best vendor” position. Validate willingness to pay before building a transaction marketplace.

## Next bets after the hackathon

1. **Serial evidence capture:** extract label fields, match invoice and official DCR evidence, preserve uncertainty. Manual/official verification remains necessary until authorised access exists.
2. **Service ticket and SLA timeline:** homeowner-owned issue history, installer acknowledgement, visit evidence and closure confirmation. Authenticate installers before exposing requests or personal contact details.
3. **Seasonal promise tracker:** import an actual monthly contract schedule, track rolling comparable periods and outages, then model documented guarantee clauses. Do not divide an annual guarantee uniformly across months.
4. **Source change diffs:** show which clause changed and affected households, with review before changing a financial estimate. A page hash change alone is not a rule change.
5. **RWA buying brief:** aggregate roof rights, common-area demand, resident permissions and a vendor-approved group offer. Current group discounts are demonstrations, not committed savings.
6. **Solar self-consumption coach:** use measured daytime consumption to suggest appliance scheduling. Without those measurements, recommendations and rupee savings would be assumptions.

Live government submissions, lender underwriting, real vendor bidding, autonomous equipment control and paid bookings remain outside this branch. They require authenticated integrations and explicit household consent.
