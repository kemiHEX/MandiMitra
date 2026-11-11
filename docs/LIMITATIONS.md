# Current limitations and acceptance status

## Required before claiming the complete live P0 journey

1. Supply valid Gnani, Groq and data.gov.in credentials, configure private access, and run the explicit live smoke script.
2. Verify an actual successful Prisma response with real Punjabi and Hindi recordings. The parser is based on current documentation; mocked responses do not prove account access or speech quality.
3. Audition Prakash/Timbre v3.0 in Punjabi and Hindi, including currency amounts. Catalog support is verified; real synthesis and pronunciation quality are not.
4. Obtain a successful official government response and verify resource ID, fields, units, date parsing and Punjab coverage. The endpoint timed out in this environment; no current market prices were retrieved.
5. Repeat microphone permission, recording and audio decoding checks on the exact demo phone/browser, and verify actual spoken playback. Start/stop recording, WAV processing and graceful missing-key handling passed in the in-app browser; this does not establish real-device or synthesized-audio quality.

The implemented product is a working full-stack demo with live adapters, **not a certified production deployment or a fully verified live P0 submission**. No public URL or source repository has been published.

## Deliberate scope

- Demo language understanding is a limited deterministic parser with a compact 16-case evaluation corpus. It is not general Punjabi/Hindi comprehension. Live mode requires Groq instead of quietly falling back to that parser.
- Core controls, clarifications and comparisons are localized. Some technical source/help/privacy text, place names and unit labels remain English. A native-language usability and accessibility review is still recommended before farmer rollout.
- Reviewed response templates constrain Groq's explanation choices. This favours factual reliability over open-ended conversation.
- One SQLite database and one API worker support local and small private demonstrations. There is no cross-device account recovery, PostgreSQL migration, distributed session lock, multi-instance cache or public registration system.
- No confirmed buyer quotes, distance/routing integration, live transport quotes, statutory fee schedule, production-cost accounting, weather, forecasting, disease diagnosis, alerts or WhatsApp integration.
- Unknown variety/grade is flagged. An explicit mismatch is excluded; the user must still confirm quality and buyer acceptance.
- Expenses are estimates manually supplied by the farmer. A sample's assumptions apply only to that illustrative scenario. No farmer-specific costs are inferred from a location alone.
- Historical observations may differ from the price actually achievable. Even a recent modal price is not a buy offer. Perishable-crop suitability requires judgment beyond a generic freshness window.
- The API cache is process-local, capped at 500 request scopes and expires entries after 15 minutes; official pagination stops at 1,000 records with a warning. Cached results retain coverage warnings. Resilience does not create missing data.
- Sessions require cookies. Clearing cookies loses access. Stored data expires and is purged on later writes; physical backups need their own retention controls.
- Rate limits and the access code limit credit use for a private demo. Public rollout requires stronger account authorization, edge abuse controls, operational monitoring, backups and a reviewed privacy policy.
- WAV input is intentionally narrow: PCM 16-bit, mono, 16 kHz. The browser converts its own recordings; arbitrary uploaded formats are not accepted by this application.
- Docker manifests and CI workflow are supplied. They have not been executed here because Docker is not installed and no repository has been published.
