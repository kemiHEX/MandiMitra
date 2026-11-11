# Architecture and engineering decisions

The browser records no more than 29.5 seconds. MediaRecorder output is decoded locally, mixed to mono and resampled to 16 kHz PCM WAV using Web Audio. FastAPI independently validates the WAV header, complete payload, sample rate, channel count, sample width, byte size and 0.1–30 second duration. Only valid audio reaches Prisma. Raw audio is never written to the database or disk.

Prisma's documented `success`/`transcript` response is validated. Empty or truncated transcripts are rejected for correction rather than silently accepted. The original transcript is retained with the reviewed text; a transcript ID is bound to the same private session. Nothing changes the decision until the farmer sends the reviewed text.

Groq receives the short current message, the latest question and a validated state object. Its strict JSON Schema specifies intent, crop, original crop term, variety, quantity and units, trader offer and units, location, transport correction and clarification. All structured results are revalidated. Missing fields are derived by Python. Ambiguous new units are not defaulted silently. Unknown tools, prices, fees and locations are never executed from model output.

The response planner receives a computed comparison and can select only `net_comparison`, `break_even` or `cost_breakdown`. Reviewed English, Punjabi and Hindi wording then inserts exact backend results. This is a deliberate safety tradeoff: natural language variation is constrained, while numbers and recommendations cannot be fabricated by a generative response.

The financial engine uses Decimal internally and serializes money as decimal strings with two places. Client-side numbers are formatting and bar widths only. The frontend never decides rankings or monetary outcomes.

Let Q be normalized quintals, L an alternative loss fraction, P the reference price, F the fixed transport/handling/other expenses, r the fee fraction, and B the local trader net proceeds:

```text
Saleable quantity S = Q × (1 − L)
Gross G = S × P
Fees = G × r
Total costs = F + G × r
Net N = G − Total costs
Difference = N − B
Break-even P* = max(0, (B + F) / (S × (1 − r)))
```

The fee-adjusted break-even formula solves for a percentage fee at the new price. Treating fees at the original modal price as a fixed amount would give an incorrect break-even. The displayed minimum rounds up to the next paise so it never falls below the actual break-even. Other monetary outputs round half-up to two decimal places. Local trader losses and expenses are modelled independently. Negative net proceeds are permitted and displayed; negative input amounts are rejected. Equal returns do not produce a winning alternative.

Unknown costs result in `costs_needed`. Unconfirmed trader costs suppress the best-option badge. Explicit crop, variety or grade mismatches are excluded. The newest duplicate for the same market/variety/grade is retained. Observations over two days old are flagged and cannot receive a best-option badge; over seven days old are excluded. These freshness thresholds are conservative product rules, not a guarantee of adequacy for perishable crops.

The server-side proxy issues HMAC-signed HttpOnly, SameSite=Strict session cookies. Next.js forwards an unguessable session ID and a private internal API credential. Browser-supplied session headers are ignored. Mutations require the configured exact browser origin; request bodies are read with byte limits. Production requires an access code, signing secret and internal token. Raw provider errors, requests, credentials and farmer messages are not logged. Logs contain only request IDs, route, status, duration and error type.

SQLite stores structured state, up to 30 recent messages, up to five original transcripts and up to 50 saved decisions per session. State expires after 30 days; decisions after 90. Expired data is deleted on subsequent state writes. Sessions are isolated by the signed browser cookie; this is a private-demo identity model, not a farmer account system. Per-session locks serialize turns; a Gnani lock prevents simultaneous speech calls. Run a single API process. Rate limits persist in SQLite, including session and global hourly allowances for provider routes.

Provider requests have timeouts. Safe GET retries and provider-rejected 429 retries use bounded backoff; potentially billable POST requests are not retried blindly after ambiguous timeouts. TTS uses a small bounded 15-minute in-memory cache. Market data uses a 15-minute in-memory cache; source dates and retrieval times are preserved. Live failure never falls back to invented prices.
