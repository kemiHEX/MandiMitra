import io
import wave
from pydantic import BaseModel, ConfigDict, StrictBool, StrictStr
from .common import ProviderError, request, json_body

class PrismaResponse(BaseModel):
    model_config = ConfigDict(extra='ignore')
    success: StrictBool
    transcript: StrictStr
    detected_language_code: str | None = None
    truncated: bool = False

def validate_wav(data: bytes) -> float:
    if not 44 < len(data) <= 2_000_000:
        raise ProviderError('Use a WAV recording smaller than 2 MB.', 422)
    try:
        with wave.open(io.BytesIO(data), 'rb') as audio:
            if audio.getnchannels() != 1 or audio.getsampwidth() != 2 or audio.getframerate() != 16000 or audio.getcomptype() != 'NONE':
                raise ValueError()
            frames = audio.getnframes()
            duration = frames / audio.getframerate()
            if len(audio.readframes(frames)) != frames * 2: raise ValueError()
            if not .1 <= duration <= 30: raise ValueError()
            return duration
    except (wave.Error, EOFError, ValueError):
        raise ProviderError('Record 0.1–30 seconds of mono, 16-bit, 16 kHz WAV audio.', 422) from None

async def transcribe(client, settings, audio: bytes):
    duration = validate_wav(audio)
    if settings.mode != 'live' or not settings.gnani_key:
        raise ProviderError('Voice transcription needs a Gnani key and live mode. Your recording was not sent or saved. You can type your question.')
    response = await request(client, 'POST', 'https://api.vachana.ai/stt/v3', headers={'X-API-Key-ID': settings.gnani_key}, files={'audio_file': ('recording.wav', audio, 'audio/wav')}, data={'model': 'prisma-v3.0', 'language_code': 'indic-auto'})
    try:
        parsed = PrismaResponse.model_validate(json_body(response))
    except ValueError:
        raise ProviderError('Unexpected Prisma response. Check the current response schema before continuing.') from None
    if not parsed.success: raise ProviderError('Speech recognition could not complete. Please type or record again.')
    if parsed.truncated: raise ProviderError('The transcript was cut short. Please record a shorter message.')
    if not parsed.transcript.strip(): raise ProviderError('No speech was detected. Please try again.', 422)
    return {'transcript': parsed.transcript, 'language': parsed.detected_language_code, 'duration_seconds': duration, 'provider': 'Gnani Prisma v3.0'}
