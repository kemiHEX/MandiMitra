# Data sources and provider verification

Documentation was checked on **9 November 2026**. No authenticated live provider calls succeeded or were claimed: credentials were not supplied, and the owner explicitly chose to proceed without keys.

| Integration | Implemented contract | Evidence / verification status |
|---|---|---|
| Groq | `POST https://api.groq.com/openai/v1/chat/completions`; Bearer key; `openai/gpt-oss-120b`; strict JSON Schema | Official API and strict structured-output documentation read; simulated contract tests pass; live call pending |
| Gnani Prisma | `POST https://api.vachana.ai/stt/v3`; `X-API-Key-ID`; multipart `audio_file`, `model=prisma-v3.0`, `language_code=indic-auto` | Current REST documentation identifies `success`, string `transcript`, optional `detected_language_code` and `truncated`; tested with simulated responses, not a successful authenticated account response |
| Gnani Timbre | `POST https://api.vachana.ai/api/v1/tts/inference`; V3 model; Prakash; Punjabi `pa-IN` or Hindi `hi-IN`; WAV binary | Official V3 catalog lists Prakash for all ten supported languages including Punjabi; request and binary response tested with simulated responses; actual voice audition pending |
| AGMARKNET | data.gov.in resource `9ef84268-d588-465a-a308-a864a43d0070`; API key, JSON, offset/limit and Punjab/commodity filters | Adapter implemented against the commonly published daily-resource contract. Dataset page returned HTTP 503 through web retrieval; direct unauthenticated API request timed out after 20 seconds. Resource access, field contract, entitlement and current observations still require a successful live verification |

Official documentation:

- [Groq API reference](https://console.groq.com/docs/api-reference)
- [Groq strict structured outputs](https://console.groq.com/docs/structured-outputs)
- [Prisma REST transcription](https://docs.gnani.ai/api/STT/speech-to-text)
- [Prisma limits](https://docs.gnani.ai/api/STT/limits)
- [Timbre voice catalog](https://docs.gnani.ai/api/TTS/available-voices)
- [Timbre REST synthesis](https://docs.gnani.ai/api/TTS/tts-inference)
- [AGMARKNET daily dataset](https://www.data.gov.in/resource/current-daily-price-various-commodities-various-markets-mandi)
- [OGD API help guide](https://event.data.gov.in/wp-content/uploads/2019/12/CPGRAMS_accessing_API_HelpGuide_User.pdf)
- [AGMARKNET](https://agmarknet.gov.in/) and [eNAM](https://www.enam.gov.in/) are reference portals, not implemented secondary price feeds.

The government adapter requests Punjab records, validates commodity, state, district, market, variety, arrival date and positive coherent minimum/modal/maximum prices, and preserves retrieval time. Default units for this resource are assumed INR/quintal; an explicit incompatible unit is rejected. **Verify that unit contract against a successful official response before enabling farmer use.** No retail-price or unrelated secondary feed is substituted.

For initial scope, canonical mappings are Tomato, Wheat and Potato. Live commodity coverage is conditional on available source records; only Tomato has offline fixtures. Location matching uses exact district/market names; otherwise it shows a clearly disclosed Punjab-wide set. It does not calculate road distances or assert that the options are the closest mandis. Pagination is bounded at 1,000 records, with a completeness warning at the bound. Malformed rows are excluded and counted.

Every observation retains source name and link, commodity, variety, optional grade, market/district/state, observation date, min/max/modal values, unit and retrieval timestamp. Separate types distinguish official observations, illustrative fixtures and farmer offers. Costs remain independent farmer-confirmed estimates.

The sample dataset in `data/samples/markets.json` is **entirely invented for demonstration**. It is not a historical government download. Its fixed date is 8 November 2026 and is deliberately not rolled forward. It will become stale and then age out under the same safety rules. The sample amounts are ₹1,200/q for Khanna, ₹1,100/q for Ludhiana and ₹1,050/q for Jagraon; these are not market recommendations. No real transaction outcomes, testimonials or performance claims are included.
