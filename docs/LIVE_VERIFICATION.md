# Live verification update — 10 November 2026

This update supersedes the earlier delivery report's statement that no authenticated provider calls have succeeded.

- User-run Groq smoke test passed validated extraction after clarifying the prompt's intent and price-unit rules.
- User-run Gnani Timbre smoke test returned audio; the user subsequently confirmed browser voice input and spoken playback worked. These are user-observed checks, not a measured speech-quality evaluation.
- The official portal returned a Punjab Tomato record for Sahnewal APMC, Ludhiana, dated 10 November 2026. Its displayed state filter is `filters[state.keyword]`; the adapter was aligned accordingly.
- Local HTTPX requests timed out waiting for response headers, while a Windows curl request to the same resource with the saved key returned HTTP 200 and one matching record.
- An HTTPX request with explicit `Accept: application/json` and `User-Agent: MandiMitra/1.0` then succeeded. Both headers were added to the adapter and diagnostic. This establishes a working request configuration; it does not establish the government's internal reason for the earlier failures.
- The actual adapter smoke test `scripts/live-smoke.py --allow-paid --only markets` returned `status: success`, `observations: 1`. The two focused mocked market-contract/cache tests passed after the change.

No keys were printed. Following these checks, the owner confirmed live comparisons, editable costs, saved decisions, access-code sign-in through a temporary HTTPS Cloudflare tunnel, and mobile-browser access. These are owner-observed demonstrations, not independent production certification. Missing potato observations were reproduced; coverage depends on the daily feed. Farmer-specific costs and variety/grade suitability must still be reviewed for each decision. The temporary shared demo requires the host laptop and services to remain running; permanent hosting has not been verified.
