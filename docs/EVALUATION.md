# Executed validation — 9 November 2026

## Result

**108 automated tests passed.** TypeScript checking and the Next.js production build passed. A running production Next.js server and a separately running FastAPI server passed **14 additional HTTP checks**. Browser interactions covered English, Punjabi, Hindi, editable costs, saved decisions, microphone start/stop, audio conversion, provider-unavailable fallbacks and a 390 × 844 mobile layout.

This verifies the local full-stack demonstration. It does **not** verify an authenticated live Gnani, Groq or government request, real transcription quality, synthesized speech playback, Docker deployment or a hosted production service.

## Environment and commands

Executed on Windows with Python 3.10.6 in an isolated virtual environment, Node.js 24.22.1, Next.js 16.4.5 and React 19.3.1. Dependencies are pinned in `requirements.txt` and `package-lock.json`.

```text
python -m pytest                         PASS — 108 tests
npm run typecheck                       PASS
npm run build                           PASS — optimized production build
npm start + uvicorn app.main:app         PASS — both services started
python scripts/verify-local.py          PASS — 14 running-service checks
```

The Python suite emitted one Starlette TestClient deprecation warning about its HTTPX test transport. No test failed. The build initially encountered a Windows nested standalone-output permission problem; switching to normal Next.js server packaging with `.build` resolved it. Docker was not installed, and the supplied CI workflow has not run on a remote repository.

## Automated coverage

| Area | Verified scenarios |
|---|---|
| Financial engine | Brief's ₹41,000 example; zero/negative/NaN/infinite inputs; missing quantity; kg/quintal/tonne conversions; invalid units; transport changes; equal and negative returns; separate trader costs/loss; percentage fees; minimum break-even rounding; sensitivity |
| Source suitability | No records; missing source; malformed prices; invalid units; stale references; over-seven-day exclusion; newest duplicate; crop/variety/grade mismatch; different crop cannot hide a valid observation |
| Conversation | 16 multilingual corpus cases; Punjabi/Hindi/Romanized words and digits; correction 40 → 14; transport correction; missing/ambiguous units; unsupported requests; follow-up offer clarification |
| Session API | Authorization; isolation; invalid JSON; input validation; cost identity; location changes clear assumptions; saved snapshots remain immutable; reset/deletion; rate limits; demo/live state separation |
| Voice ownership | Reviewed voice keeps original transcription; transcript ID belongs to its session; invalid transcript rejected before a paid extraction; TTS failure preserves written response |
| Provider contracts | Documented Prisma multipart request and validated response; malformed/empty/truncated STT responses; invalid WAVs; Timbre V3 voice/model/language and raw WAV contract; synthesis cache; Groq strict schema and invalid JSON handling |
| Grounding and speech | Explanation planner accepts only reviewed focus values; exact computed amounts inserted; Punjabi/Hindi currency number wording |
| Government adapter | Simulated official records; field/unit validation; Punjab commodity filtering; unavailable-key errors; cache preserves coverage warnings; demo never silently replaces live data |

Provider contract tests use `httpx.MockTransport` or injected test functions. Passing those tests is not evidence of provider authentication, availability or model accuracy.

## Running production server checks

The 14-check script verified HTML serving, backend authorization, frontend-to-backend communication, HttpOnly/SameSite session cookies, cross-origin mutation rejection, body size enforcement, malformed JSON rejection, explicit demo provenance, the sample calculation, cost editing, Punjabi correction, immutable snapshots, independent session isolation and cleanup of its own test session. These were real local HTTP requests, not mocked endpoints.

Run it only with this application in demo mode. It refuses to continue unless the server reports demo mode, creates its own session and deletes only that session's test records. It uses no provider keys.

## Observed browser journeys

1. Loaded the real frontend and selected the labelled tomato sample: trader ₹36,000; Khanna ₹41,000; difference ₹5,000; break-even ₹1,075/q.
2. Changed Khanna transport from ₹5,500 to ₹4,000 in the cost dialog: net proceeds became ₹42,500 and break-even ₹1,037.50/q.
3. Corrected 40 to 14 quintals: trader became ₹12,600; the alternative no longer received a highest-estimate badge.
4. Saved and reopened a snapshot. Later state changes did not rewrite the saved figures.
5. Started and stopped the actual browser recorder. The browser-produced recording passed the backend's strict WAV validation and reached the honest missing-Gnani-key error. No recording was sent to Gnani or persisted.
6. Requested spoken output without a key: the written answer stayed available and the page explained why speech was unavailable.
7. Typed Punjabi after that failure; the app recovered and recomputed. Entered a Hindi word-number query in the production build: quantity changed to 14 with a Hindi response.
8. Inspected mobile Punjabi controls, navigation, comparison cards and saved view. At 390 px viewport width, document width was 375 px (no horizontal overflow). Reset the temporary viewport after testing.
9. Captured final desktop and mobile screenshots. The inspected final browser console contained no warning/error entries.

Audio playback controls are implemented, but successful playback of actual Timbre output remains untested. No synthetic test audio is represented as Gnani speech. Native phone permissions, Safari decoding, screen-reader navigation and native-speaker comprehension need their own checks.

## Live verification status

| Integration | Documentation/contract status | Actual live result |
|---|---|---|
| Gnani Prisma v3.0 | Endpoint, multipart fields and documented `success`/`transcript` response implemented | Not called with credentials |
| Groq GPT-OSS 120B | Official chat API and strict JSON Schema implemented | Not called with credentials |
| Gnani Timbre v3.0 / Prakash | Official V3 voice catalog, Punjabi/Hindi identifiers and binary WAV contract implemented | No synthesis or pronunciation audition |
| AGMARKNET via data.gov.in | Configurable resource adapter, attribution, timestamps and record normalization implemented | Unauthenticated endpoint timed out; no official prices retrieved |

The owner requested continuing without keys. `scripts/live-smoke.py` has an explicit `--allow-paid` guard and reports each provider separately. Invoking it without that flag was checked to send no requests. Once credentials are configured, test real Punjabi and Hindi WAVs, inspect the actual returned schemas, audition currency pronunciation, and verify the official resource's units and recent Punjab coverage.

The 16-query corpus is a small regression fixture for the offline parser. No general language-understanding accuracy, latency benchmark, farmer outcome, profitability claim or probability score is inferred from it.

## Setup-guide follow-up

Added a numbered Windows-to-private-HTTPS guide, a non-overwriting environment helper, and a separate three-service hosted Compose configuration with Caddy. The helper was executed in a disposable directory: file creation, repeated runs, preservation of a sentinel provider key and existing app secrets, optional access-code generation, and absence of secrets in printed output passed. The hosted YAML parsed successfully; service paths, required settings, persistent volumes and absence of public app-service ports were checked. Docker/Caddy execution and cloud HTTPS still need their first real server verification. The application code and its 108-test result are unchanged.
