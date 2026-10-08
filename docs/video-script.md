# Demo video: 3 minutes

Judges see only this video, and a feature that isn't shown doesn't count. Show AWS on screen, not just in narration.

## Before recording

- **Blur personal details on the real bill:** CA number, name and address. Or use a family member's bill with their OK.
- **Phone:** WhatsApp joined to the Twilio sandbox. Send "hi" once so the 24-hour window is open.
- **Tabs to have open:**
  - the website, on the home page
  - the Step Functions console, on the journey state machine
  - the DynamoDB knowledge table
- **Files on the phone:** the sample quote image (`web/sample-quote.png`).
- **Screen capture:** record the phone with a screen mirror (scrcpy or similar) next to the laptop.
- **Captions:** Hindi parts get English captions.
- **On the website:** run "Get quotes" once before recording so the API is warm, then delete the comparison.

## Shot list

| Time | On screen | Voiceover |
|---|---|---|
| 0:00–0:10 | The home page loads: pixel Delhi skyline, the phone chat plays (bill in, estimate back) | "India wants a crore homes on rooftop solar by March. About 41 lakh are there. Most families stop before they apply: they can't tell if it pays, or who to trust." |
| 0:10–0:32 | Phone: send the real bill photo → the estimate in Hindi, then the bill check-up | "So we built Surya Saathi, on WhatsApp, in Hindi. A bill photo is read three times in parallel on Amazon Bedrock and kept only where the readings agree: 2 kilowatts, ₹70,000 after subsidy, paid back in under five years. And the bill doctor finds ₹5,500 a year before any solar." |
| 0:32–0:58 | Website, Get quotes: four quotes arrive one by one; each bar shrinks to the price after subsidy; the cheapest stays full; "Best fit" lands on Dhoop | "Then the hard part: which vendor. One request, and every quote is checked by the same rules and compared by what you really pay. The cheapest one uses imported panels, so the subsidy is lost and it costs the most in the end. These demo vendors are fictional; each shows a real trap." |
| 0:58–1:10 | Scam check: "Try an example" → red flags: registration fee, look-alike portal, OTP | "Families also get calls and forwards. Paste one in: a fee to register, a fake portal, a request for the OTP. Three red flags." |
| 1:10–1:30 | Schemes: Delhi, then Uttar Pradesh; the stacked bar; then drag the subsidy wait from 1 to 6 months and watch the EMI chart | "Every scheme, for every state, each with its source. And because the subsidy arrives after installation, this shows the cash a family needs while they wait." |
| 1:30–1:58 | Phone: APPLY DEMO → step 1 → DONE → a nudge ⏰ → STUCK → drafted complaint. Cut to the Step Functions execution waiting on a task token | "Applying has eight steps. Each is a Step Functions task that waits for the family to say done. A step that runs long sends a nudge, and STUCK writes the complaint for whoever is holding it up." |
| 1:58–2:12 | Record a Hindi voice note: "सब्सिडी कब आएगी?" → the voice reply plays | "Not everyone types. Amazon Transcribe hears the question and Polly answers in Hindi." |
| 2:12–2:30 | Website, After install: "Dust this week" with Monday outlined to clean; then the first-bill flow showing 50 export units to query | "After installation: Delhi's dust costs up to half a percent of output a day, so a live air-quality forecast picks the day to clean. And the first bill is checked, because generation isn't the same as export." |
| 2:30–2:48 | Rates & rules board, then the DynamoDB table with TARIFF# and PRICE# items; then the architecture diagram | "Rates change every month, so the knowledge updates itself: bills teach tariffs, quotes teach prices, people confirm facts, and EventBridge Scheduler re-reads official pages weekly. All serverless on AWS, deployed with SAM in Mumbai." |
| 2:48–3:00 | Home page hero + URL | "Surya Saathi. From the bill to the subsidy, and after." |

## If time runs short

Cut the voice note first, then the scam check. Keep the bill, the quote comparison and the journey: those three carry the idea.
