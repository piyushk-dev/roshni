# From a bill photo to a subsidy: building Surya Saathi on AWS in four days

*Draft for AWS Builder Center. Edit freely before publishing.*

India wants one crore homes on rooftop solar by March 2027 under PM Surya Ghar. By June 2026 about 41 lakh were there. A CEEW survey of 17,000 households explains the gap: once families apply, most go on to install. The drop-off happens before they apply. They can't tell whether solar pays for their home, who to trust, or what to do next.

Surya Saathi is a WhatsApp-first companion for that whole path. A family sends a photo of their electricity bill and gets an honest answer in Hindi or English: the right size, the cost after subsidy, the EMI and the payback, or "skip it" when solar won't pay. From there it checks vendor quotes, walks them through the eight application steps with reminders, drafts the complaint when someone else is holding things up, and after installation checks the panels' output against what they should make.

## The stack

Everything is serverless in ap-south-1, defined in one AWS SAM template:

- **Amazon Bedrock (Nova 2 Lite)** reads bills, quotes and inverter screens, and answers questions.
- **AWS Step Functions** runs each household's application as a long-lived workflow. Every stage is a task that waits on a task token until the family replies DONE. A stage that runs past its usual length times out into a nudge, then waits again.
- **Amazon EventBridge Scheduler** runs a weekly watcher over official sources.
- **Amazon Transcribe and Amazon Polly** handle Hindi voice notes in and out.
- **Amazon DynamoDB** stores sessions, a sunlight cache, and the knowledge layer.
- **AWS Lambda, API Gateway and Amplify Hosting** serve WhatsApp (through Twilio) and the website.

## What fought back

**Reading real bills.** My first bill reader was correct on a clean synthetic bill and wrong on a real phone photo. The model read every units value correctly, then scrambled the dates in the skewed history table. It read Indian DD-MM dates as MM-DD, mistook the "number of days" column for units, and once used the bill total as the energy charge. The fix had three parts:

1. The model only transcribes. Code anchors on the current billing period and counts months back in printed order.
2. Plain sanity checks reject impossible values, such as an energy charge of ₹16 a unit.
3. Every bill is read three times in parallel, keeping only what the readings agree on.

Parallel reads cost about the same time as one. The real bill, WhatsApp-compressed or not, now gives the same answer every time.

**WhatsApp.** Meta's Cloud API integration was finished in an afternoon: signed webhooks, an async worker, de-duplication of retries. Then Meta restricted the account until the business is verified, and a student project isn't a registered business. Twilio's WhatsApp sandbox took about an hour to add behind the same bot logic. Its quirks: a different signature scheme, media links that redirect to signed storage, and a 1,600-character limit per message.

**Knowing the rules.** Fuel surcharges change monthly, and state top-ups change with budgets. Instead of chasing every number, the system learns:

- **From bills:** every bill prints its slab rates, so each bill read updates that provider's tariff. That's also how a bill from any state works on day one. From one BSES photo it recovered the regulator's exact 200 and 400-unit slabs.
- **From quotes:** each quote checked becomes a local price data point.
- **From people:** facts on a public board can be confirmed, or reported as changed with evidence.
- **From a watcher:** a weekly job flags official pages that changed.

**Being honest.** Sunlight comes from PVGIS, scaled down wherever NASA's satellite data is lower, which matters in north India's smoggy winters. The calculator prefers a smaller system when it gets within 10% of the best 25-year value, and says "don't" when solar won't pay. On my own family's bill it found ₹5,500 a year of savings before any solar: the sanctioned load was double the actual peak.

## Try it

- Website: https://main.d3frlgja2w8q15.amplifyapp.com
- Code: https://github.com/piyushk-dev/surya-saathi

Built with Claude Code as a coding assistant.
