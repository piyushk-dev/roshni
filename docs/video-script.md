# Demo video: 3 minutes

Published: https://youtu.be/owERy3rFx-o

Judges see only this video, and a feature that isn't shown doesn't count. Show AWS on screen, not just in narration.

## Before recording

- **Recording after dark?** Open the site as `https://main.d3frlgja2w8q15.amplifyapp.com/?at=10.5`: the widget, both iPhones and the app show today's simulated panels at 10:30. `?at=13` lands on a simulated "grid voltage too high" event for the inverter-events shot (open `/app/?at=13`).
- **The bill:** "See an example" reads the fictional `web/sample-bill.png` on Bedrock, with the scan and the AWS timing line, so no personal bill is needed. If you use a real one, blur the CA number, name and address.
- **Phone:** WhatsApp joined to the Twilio sandbox. Send "hi" once so the 24-hour window is open.
- **Tabs to have open:**
  - the website, on the home page
  - the Step Functions console, on the journey state machine
  - the DynamoDB knowledge table
- **Files on the phone:** the sample quote image (`web/sample-quote.png`).
- **Screen capture:** record the phone with a screen mirror (scrcpy or similar) next to the laptop.
- **Captions:** Hindi parts get English captions.
- **On the website:** run "Get quotes" once before recording so the API is warm, then delete the comparison. Run the panel check once too, so Bedrock is warm.

## Shot list

| Time | On screen | Voiceover |
|---|---|---|
| 0:00–0:10 | The home page loads: pixel Delhi skyline; the hero iPhone opens WhatsApp from its home screen, the bill goes in and the estimate comes back | "India wants a crore homes on rooftop solar by March. About 41 lakh are there. Most families stop before they apply: they can't tell if it pays, or who to trust." |
| 0:10–0:32 | Phone: send the real bill photo → the estimate in Hindi, then the bill check-up | "So we built Roshni, on WhatsApp, in Hindi. A bill photo is read three times in parallel on Amazon Bedrock and kept only where the readings agree: 2 kilowatts, ₹70,000 after subsidy, paid back in under five years. And the bill doctor finds ₹5,500 a year before any solar." |
| 0:32–0:58 | Website, Get quotes: four quotes arrive one by one; each bar shrinks to the price after subsidy; the cheapest stays full; "Best fit" lands on Dhoop | "Then the hard part: which vendor. One request, and every quote is checked by the same rules and compared by what you really pay. The cheapest one uses imported panels, so the subsidy is lost and it costs the most in the end. These demo vendors are fictional; each shows a real trap." |
| 0:58–1:10 | Scam check: "Try an example" → red flags: registration fee, look-alike portal, OTP | "Families also get calls and forwards. Paste one in: a fee to register, a fake portal, a request for the OTP. Three red flags." |
| 1:10–1:30 | Schemes: Delhi, then Uttar Pradesh; the stacked bar; then drag the subsidy wait from 1 to 6 months and watch the EMI chart | "Every scheme, for every state, each with its source. And because the subsidy arrives after installation, this shows the cash a family needs while they wait." |
| 1:30–1:58 | Phone: APPLY DEMO → step 1 → DONE → a nudge ⏰ → STUCK → drafted complaint. Cut to the Step Functions execution waiting on a task token | "Applying has eight steps. Each is a Step Functions task that waits for the family to say done. A step that runs long sends a nudge, and STUCK writes the complaint for whoever is holding it up." |
| 1:58–2:12 | Record a Hindi voice note: "लखनऊ में 3 kW पर कितनी सब्सिडी मिलेगी?" → the text reply, then the voice reply plays. Cut to the website's Ask box showing "Worked out with the scheme list for Uttar Pradesh" | "Not everyone types. Amazon Transcribe hears the question, and a Bedrock agent works it out with the same tools as the website: ₹78,000 from the centre, ₹30,000 from UP. Polly answers in Hindi." |
| 2:12–2:22 | Website, After install: "Try an imported one" on the panel check, the label is read, red verdict (made in China, no DCR) | "Before the last payment, photograph a panel's label. Bedrock reads it, and an imported panel or a missing DCR mark is caught in time." |
| 2:22–2:34 | The My solar app on a phone (or the home page's iPhone): the sky and live kW, the energy flow dots, drag along today's curve so the sky moves to noon; tap an inverter event, "Grid voltage too high", with who fixes it and its evidence | "After installation it becomes the app for your panels: live output, where the power goes, the next three days, and every inverter event explained, with evidence for the installer." |
| 2:34–2:50 | Rates & rules board, then the DynamoDB table with TARIFF# and PRICE# items; then the architecture diagram | "Rates change every month, so the knowledge updates itself: bills teach tariffs, quotes teach prices, people confirm facts, and EventBridge Scheduler re-reads official pages weekly. All serverless on AWS, deployed with SAM in Mumbai." |
| 2:50–3:00 | Home page hero (the iPhone goes from WhatsApp to the panels' notification to the My solar app) + URL | "Roshni. From the bill to the subsidy, and after." |

## Optional shot (5 seconds)

Home page, "Add your location or roof size", then "Measure it on the map": search the area, tap the roof's four corners, "Use 650 sq ft". Voiceover: "Not sure the roof fits? Trace it on Amazon Location's satellite map."

## If time runs short

Cut the voice note first, then the scam check. Keep the bill, the quote comparison and the journey: those three carry the idea.
