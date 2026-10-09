# From a bill photo to a subsidy: building Surya Saathi on AWS in four days

*Draft for AWS Builder Center. Edit freely before publishing.*

India wants one crore homes on rooftop solar by March 2027 under PM Surya Ghar. By June 2026 about 41 lakh were there. A CEEW survey of 17,000 households explains the gap: once families apply, most go on to install. The drop-off happens before they apply. They can't tell whether solar pays for their home, who to trust, or what to do next.

Surya Saathi is a WhatsApp-first companion for that whole path. A family sends a photo of their electricity bill and gets an honest answer in Hindi or English: the right size, the cost after subsidy, the EMI and the payback, or "skip it" when solar won't pay. From there it:

- compares vendor quotes by what the family pays after subsidy;
- lists the central subsidy and the state's own help, each with its source;
- walks them through the eight application steps, and drafts the complaint when someone else is holding things up;
- checks that the panels on the roof are the ones in the quote;
- after installation, picks the day to clean the panels and checks the first bill.

## The stack

Everything is serverless in ap-south-1, defined in one AWS SAM template:

- **Amazon Bedrock (Nova 2 Lite)** reads bills, quotes, inverter screens and panel labels. Questions go through a tool-use loop over the product's own calculators.
- **Amazon Location Service** finds the places people name in a question, and the state they're in.
- **AWS Step Functions** runs each household's application as a long-lived workflow. Every stage is a task that waits on a task token until the family replies DONE. A stage that runs past its usual length times out into a nudge, then waits again.
- **Amazon EventBridge Scheduler** runs a weekly watcher over official sources.
- **Amazon Transcribe and Amazon Polly** handle Hindi voice notes in and out.
- **Amazon DynamoDB** stores sessions, a sunlight cache, the knowledge layer and the quote marketplace, which expires old requests with TTL.
- **AWS Lambda, API Gateway and Amplify Hosting** serve WhatsApp (through Twilio) and the website.

## What fought back

**Reading real bills.** My first bill reader was correct on a clean synthetic bill and wrong on a real phone photo. The model read every units value correctly, then scrambled the dates in the skewed history table. It read Indian DD-MM dates as MM-DD, mistook the "number of days" column for units, and once used the bill total as the energy charge. The fix had three parts:

1. The model only transcribes. Code anchors on the current billing period and counts months back in printed order.
2. Plain sanity checks reject impossible values, such as an energy charge of ₹16 a unit.
3. Every bill is read three times in parallel, keeping only what the readings agree on.

Parallel reads cost about the same time as one. The real bill, WhatsApp-compressed or not, now gives the same answer every time.

**Comparing quotes honestly.** The sticker price misleads. A quote with imported panels can't get the subsidy, so the cheapest quote on paper can cost the most. The comparison board ranks every quote by the price after subsidy, and runs the same checks on each: DCR panels, subsidy promises above the cap, large advances, undersized inverters, missing net meter or earthing. The four vendors in the demo are fictional, labelled on every screen, and each shows a different trap. I didn't want any real company shown with prices it never quoted. Real installers get a vendor page instead. It shows open requests by area (only the first three digits of the PIN), and a quote passes the same checks before it's sent, so the installer sees what the family will see.

**Is this the panel you paid for?** The subsidy needs Indian cells and an Indian module, and those DCR panels cost more than imported ones. The portal also flags a module serial it has already seen, and since May 2026 a vendor's undertaking no longer clears that flag. None of this is easy for a family to check from the ground. So a photo of a panel's back label is read with a Bedrock tool schema: maker, wattage, serial, where the module and its cells were made, and whether it carries the DCR mark. Two details mattered:

1. **Missing fields.** The model sometimes writes "null" or "not visible" instead of leaving a field out, which once produced "cells from null". Those values are now cleaned before any rule runs.
2. **Duplicate serials.** Each serial is hashed with SHA-256 and written to DynamoDB with a conditional put (`attribute_not_exists`). The first home to check a serial owns it, a second home gets a warning, and there's no read-then-write race.

**Dust.** Dust and smog in Delhi can cut output by 0.3–0.6% a day, so cleaning after a dusty spell pays more than cleaning during one. A live CAMS forecast from Open-Meteo rates each day by India's AQI bands for PM10 and picks the first low day after the dust settles. One morning the forecast still started on the previous day: a response cached just before midnight was served after it. The cache now keys on the date in India, and days before today are dropped.

**Letting the model do arithmetic.** The first version of the assistant pasted the facts into the prompt and let the model answer. Asked about 3 kW in Lucknow, it multiplied Uttar Pradesh's ₹15,000 per kW by three and promised ₹45,000, past the state's ₹30,000 cap. Now questions go through a Bedrock tool-use loop. The model can call the scheme list for a state, a rough estimate from a typed bill, the scam check, the dust forecast and the household's application step. The tools hand back finished amounts, caps applied and written the Indian way (₹1,08,000), and the prompt says to quote them as given. Amazon Location Service turns "Saket, Delhi" or "Jaipur" into coordinates and a state code, so the right scheme and the local forecast come back. Every answer says which tools it used. One more catch: a test that patched the old function let the new one reach Bedrock with my own credentials. The test suite now refuses any real AWS client.

**WhatsApp.** Meta's Cloud API integration was finished in an afternoon: signed webhooks, an async worker, de-duplication of retries. Then Meta restricted the account until the business is verified, and a student project isn't a registered business. Twilio's WhatsApp sandbox took about an hour to add behind the same bot logic. Its quirks: a different signature scheme, media links that redirect to signed storage, and a 1,600-character limit per message.

**Knowing the rules.** Fuel surcharges change monthly, and state top-ups change with budgets. Instead of chasing every number, the system learns:

- **From bills:** every bill prints its slab rates, so each bill read updates that provider's tariff. That's also how a bill from any state works on day one. From one BSES photo it recovered the regulator's exact 200 and 400-unit slabs.
- **From quotes:** each quote checked becomes a local price data point.
- **From people:** facts on a public board can be confirmed, or reported as changed with evidence.
- **From a watcher:** a weekly job flags official pages that changed.

**Being honest.** Sunlight comes from PVGIS, scaled down wherever NASA's satellite data is lower, which matters in north India's smoggy winters. The calculator prefers a smaller system when it gets within 10% of the best 25-year value, and says "don't" when solar won't pay. On a real Delhi bill it found ₹5,500 a year of savings before any solar: the sanctioned load was double the actual peak.

## Try it

- Website: https://main.d3frlgja2w8q15.amplifyapp.com
- Code: https://github.com/piyushk-dev/surya-saathi

## AI tools used

- **Claude Code (Anthropic)** and **Codex (OpenAI)** as coding assistants, for research, code and writing.
- **Amazon Bedrock (Nova 2 Lite)** inside the product, to read bills, quotes, inverter screens and panel labels, and to answer questions with the product's own tools.
