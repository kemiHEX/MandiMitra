import hashlib
import io
import re
import time
import wave
from .common import ProviderError, request
from ..speech_numbers import normalize

V3_VOICES = {'Shivani', 'Lakshmi', 'Kalpana', 'Chetana', 'Vasudha', 'Riyaa', 'Tarika', 'Avinash', 'Shubham', 'Prakash', 'Devansh', 'Yashraj', 'Harshad'}
# Bounded process-memory cache; audio is never persisted to disk.
_cache: dict[str, tuple[float, bytes]] = {}

def spoken_text(text: str, language: str):
    return normalize(text, language)

async def synthesize(client, settings, text: str, language: str) -> bytes:
    if settings.mode != 'live' or not settings.gnani_key:
        raise ProviderError('Spoken replies need a Gnani key and live mode. The written answer remains available.')
    if settings.tts_model != 'timbre-v3.0' or settings.tts_voice not in V3_VOICES:
        raise ProviderError('Choose a verified Timbre v3.0 voice in the server settings.')
    text = spoken_text(text, language)
    key = hashlib.sha256(f'{settings.tts_model}:{settings.tts_voice}:{language}:{text}'.encode()).hexdigest()
    now = time.monotonic()
    for k in list(_cache):
        if now - _cache[k][0] > 900: del _cache[k]
    if key in _cache: return _cache[key][1]
    response = await request(client, 'POST', 'https://api.vachana.ai/api/v1/tts/inference', headers={'X-API-Key-ID': settings.gnani_key}, json={'text': text[:2500], 'voice': settings.tts_voice, 'model': settings.tts_model, 'language': {'pa': 'pa-IN', 'hi': 'hi-IN', 'en': 'en-IN'}[language], 'speed': 1.0, 'audio_config': {'sample_rate': 48000, 'num_channels': 1, 'sample_width': 2, 'encoding': 'linear_pcm', 'container': 'wav'}})
    audio = response.content
    if len(audio) > 20_000_000: raise ProviderError('The audio response was too large.')
    try:
        with wave.open(io.BytesIO(audio), 'rb') as wav:
            if wav.getnframes() == 0 or wav.getnchannels() != 1 or wav.getsampwidth() != 2: raise ValueError()
    except (wave.Error, EOFError, ValueError):
        raise ProviderError('The speech service returned invalid audio. Please use the written answer.') from None
    if len(_cache) >= 12: _cache.pop(next(iter(_cache)))
    _cache[key] = (now, audio)
    return audio
