# API reference

Interactive schemas: `http://127.0.0.1:8000/docs`. Health is public. Every data/provider route requires `Authorization: Bearer <API_INTERNAL_TOKEN>` and a 64-character lowercase hexadecimal `X-Session-ID`, supplied by the Next.js server. Do not put the token in browser code.

| Method | Route | Purpose |
|---|---|---|
| GET | `/health` | Status, mode and application version |
| GET | `/session` | Validated farmer state, missing fields, messages, observations, costs, comparison and provider configuration flags |
| DELETE | `/session` | Clear current conversation/profile; retain saved decisions |
| DELETE | `/session?everything=true` | Clear all data belonging to this session |
| POST | `/demo` | Load the explicitly labelled tomato fixture scenario; rejected in live mode |
| PATCH | `/inputs` | Replace validated farmer details; changing crop/location clears market cost assumptions |
| POST | `/chat` | `{text, language, transcript_id?}`; update state, clarify missing inputs, recalculate |
| PATCH | `/costs` | `{market_id, costs}`; validate session-owned market, update assumptions, recalculate |
| POST | `/compare` | Refresh observations and recalculate from saved structured inputs |
| GET | `/decisions` | List up to 50 saved session-owned snapshots |
| POST | `/decisions` | Save current computed comparison with state, references and costs |
| DELETE | `/decisions/{id}` | Delete a snapshot owned by the session |
| POST | `/stt` | Multipart `audio_file`; returns transcript, transcript ID, detected language and validated duration |
| POST | `/tts` | `{message_id}`; synthesizes only an assistant message belonging to this session; returns `audio/wav` |

Frontend equivalents are under `/api/…`. `/api/auth` accepts the configured private demonstration access code and sets a signed HttpOnly cookie. There is no arbitrary proxy or open TTS text relay. Provider status flags mean credentials are configured, not that a live test passed.

Money and calculated values are decimal strings. Quantity units: `quintal`, `kg`, `tonne`. Price input units use the same identifiers; source market observations are `INR/quintal`. Languages: `en`, `pa`, `hi`.

Typical cost payload:

```json
{
  "market_id": "demo-khanna",
  "costs": {
    "transport": "4000", "loading": "1000", "other": "500",
    "market_fee_percent": "0", "loss_percent": "0", "confirmed": true
  }
}
```

Errors return an `error` message for provider/validation/middleware failures or a FastAPI `detail` for route-specific failures. HTTP 401 denotes authorization, 413 excessive payload, 422 invalid input, 429 rate limiting and 503 unavailable providers. Responses carry `X-Request-ID` after request handling and `Cache-Control: no-store`. Clients must retain the last valid data when a mutation fails and display the error.
