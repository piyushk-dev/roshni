# Demo video: 3 minutes

Judges see only this video, and a feature that isn't shown doesn't count. Show AWS on screen, not just in narration.

## Before recording

- **Blur personal details on the real bill:** CA number, name and address. Or use a family member's bill with their OK.
- **Phone:** WhatsApp joined to the Twilio sandbox. Send "hi" once so the 24-hour window is open.
- **Tabs to have open:**
  - the website
  - the Step Functions console, on the journey state machine
  - the Lambda list
  - the DynamoDB knowledge table
- **Files on the phone:** the sample quote image (`web/sample-quote.png`) and an inverter screenshot.
- **Screen capture:** record the phone with a screen mirror (scrcpy or similar) next to the laptop.
- **Captions:** Hindi parts get English captions.

## Shot list

| Time | On screen | Voiceover |
|---|---|---|
| 0:00–0:12 | Black screen, then three numbers: 41 lakh homes · 1 crore target · March 2027 | "India wants a crore homes on rooftop solar by March. About 41 lakh are there. A national survey found most families stop before they even apply: they can't tell if it pays, or who to trust." |
| 0:12–0:20 | Phone: WhatsApp chat with Surya Saathi | "So we built a companion that walks the whole way. It's on WhatsApp, in Hindi, and starts with a photo." |
| 0:20–0:45 | Send the bill photo → "Reading your photo…" → the estimate in Hindi | "Three readings in parallel on Amazon Bedrock, kept only where they agree. 2 kilowatts, ₹70,000 after subsidy, paid back in under five years, from conservative sunlight data." |
| 0:45–0:58 | The bill check-up and the Delhi bonus message | "Before any solar, the bill doctor finds ₹5,500 a year: the sanctioned load is double the actual peak. And this home qualifies for Delhi's new ₹0-upfront scheme, which almost nobody knows about." |
| 0:58–1:18 | Forward the sample quote → "Don't sign yet" | "Then the vendor's quote. These panels aren't made-in-India, so the whole ₹78,000 subsidy would be lost. It's ₹50,000 over local prices, and the inverter is too small." |
| 1:18–1:50 | Type APPLY DEMO → step 1 checklist → DONE → step 2 → cut to a nudge ⏰ → STUCK → drafted complaint. Cut to the Step Functions console: the execution graph waiting on a task token | "Applying has eight steps. Each one is a Step Functions task that waits for the family to say done. If a step runs long, they get a nudge. If someone else is holding it up, STUCK writes the complaint for the right office. The family sends it." |
| 1:50–2:08 | Record a Hindi voice note: "सब्सिडी कब आएगी?" → text reply → voice-note reply plays | "Not everyone types. Voice notes go through Amazon Transcribe, the answer is grounded in their own stage, and Polly replies in Hindi." |
| 2:08–2:20 | Send the inverter screenshot → output check | "After installation, a screenshot of the inverter shows whether the panels make what they should. Delhi dust alone costs ten percent a month." |
| 2:20–2:42 | Website: the Rates & rules board, Still true, Report a change; then the DynamoDB table with TARIFF# and PRICE# items | "Rates change every month, so the knowledge updates itself. Every bill teaches its provider's tariff, which makes any state's bill work. Every quote teaches local prices. People confirm facts, and an EventBridge Scheduler job flags any official page that changes." |
| 2:42–2:55 | Architecture diagram from the website | "All of it is serverless on AWS, deployed with SAM in Mumbai: Lambda, API Gateway, Bedrock, Step Functions, EventBridge Scheduler, DynamoDB, Transcribe, Polly and Amplify." |
| 2:55–3:00 | Logo + website URL | "Surya Saathi. From the bill to the subsidy, and after." |

## If time runs short

Cut the inverter check first, then the voice note. Keep the bill, the quote and the journey: those three carry the idea.
