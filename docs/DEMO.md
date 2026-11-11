# Challenge demo and submission copy

## Project description

MandiMitra helps Indian farmers compare crop-selling options in their own language. A farmer can describe the crop, quantity and local trader offer, then compare reported mandi references after editable transport, handling, fee and produce-loss assumptions. A deterministic Python engine calculates net proceeds and break-even prices. Gnani Prisma v3.0 handles speech recognition, Groq GPT-OSS 120B extracts structured context and selects a grounded explanation focus, and Gnani Timbre v3.0 produces spoken replies.

The problem is practical: the highest displayed crop price may leave the farmer with less money after the journey and selling costs. MandiMitra makes those assumptions visible and correctable, and distinguishes an official reported observation from a buyer's actual offer.

## Differentiators

- Punjabi/Hindi voice workflow with reviewable original transcription and numerical corrections.
- Deterministic money arithmetic, including percentage fees and saleable quantity loss.
- Source dates, freshness exclusions and explicit demo/official/offer/expense categories.
- Per-market editable assumptions, break-even price and clearly hypothetical sensitivity scenarios.
- Private sessions, saved decision snapshots and summaries that retain the limitations.

## A 60-second demonstration

Use the **live** sequence only after the provider checks succeed. With no keys, use the offline alternative and state that it is a full-stack illustrative demonstration; do not imitate successful Gnani/Groq calls.

| Time | Screen / action | Suggested narration |
|---|---|---|
| 0–7 s | Welcome; choose Punjabi | “The mandi with the highest price is not always the best sale.” |
| 7–18 s | Record: “Mere kol 40 quintal tamatar ne. Vyapari 900 rupaye prati quintal de reha hai. Main Ludhiana ton haan.” | “Tell MandiMitra what you have and the offer you've received.” |
| 18–25 s | Review the actual Prisma transcription and send it | “Speech becomes checked, structured crop information.” |
| 25–36 s | Show dated official references and pre-entered, clearly confirmed costs | “The Python engine compares what remains after selling costs.” |
| 36–44 s | Open the break-even and expense breakdown; play Timbre reply | “These are conditional proceeds, not a guaranteed buyer price.” |
| 44–53 s | Correct: “Chali nahi, chaudah quintal.” | “Corrections change the saved state and recalculate the decision.” |
| 53–60 s | Save and open the summary | “Confirm the achievable price before travelling. Har Fasal Ka Sahi Sauda.” |

If official records or voice providers are unavailable, record the honest alternative: choose **Try a tomato example**, show the banner, use text corrections and say “illustrative sample prices and costs.” Show that the frontend, backend and financial engine work together. Do not call this a live end-to-end AI demonstration.

## Recording notes

Use a quiet room, visible observation dates, readable phone/desktop scaling and a prepared crop/cost scenario. Do not edit a failed API call to appear successful. Actual live prices and results may differ from the supplied illustrative scenario. Redact keys, access codes, private logs and personal data. No testimonials, farmer transaction claims or accuracy percentages are provided.

## Technology list

Next.js 16, React 19, TypeScript, Tailwind CSS 4, browser MediaRecorder/Web Audio, Python, FastAPI, Pydantic, HTTPX, SQLite, Decimal, pytest, Gnani Prisma v3.0, Groq-hosted GPT-OSS 120B and Gnani Timbre v3.0.

## Suggested repository presentation

Use the main README as the landing page, followed by a real UI screenshot, a recording of the verified workflow, the architecture diagram, test results and the explicit live-integration status. Keep `.env`, runtime databases, original audio and dependency/build folders out of the repository. The supplied GitHub workflow can run tests/build after the owner chooses to publish a repository. No repository or competition form has been submitted by this build.
