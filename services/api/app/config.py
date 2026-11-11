import os
from dataclasses import dataclass, field
from pathlib import Path
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[3]
load_dotenv(ROOT / '.env')

@dataclass
class Settings:
    mode: str = field(default_factory=lambda: os.getenv('APP_MODE', 'demo'))
    gnani_key: str = field(default_factory=lambda: os.getenv('GNANI_API_KEY', ''))
    groq_key: str = field(default_factory=lambda: os.getenv('GROQ_API_KEY', ''))
    groq_model: str = field(default_factory=lambda: os.getenv('GROQ_MODEL', 'openai/gpt-oss-120b'))
    data_key: str = field(default_factory=lambda: os.getenv('DATA_GOV_API_KEY', ''))
    resource_id: str = field(default_factory=lambda: os.getenv('AGMARKNET_RESOURCE_ID', '9ef84268-d588-465a-a308-a864a43d0070'))
    tts_voice: str = field(default_factory=lambda: os.getenv('GNANI_TTS_VOICE', 'Prakash'))
    tts_model: str = field(default_factory=lambda: os.getenv('GNANI_TTS_MODEL', 'timbre-v3.0'))
    database_path: str = field(default_factory=lambda: os.getenv('DATABASE_PATH', str(ROOT / 'runtime/mandimitra.db')))
    internal_token: str = field(default_factory=lambda: os.getenv('API_INTERNAL_TOKEN') or 'local-demo-only')
    production: bool = field(default_factory=lambda: os.getenv('DEPLOYMENT_ENV') == 'production')
    cors: list[str] = field(default_factory=lambda: os.getenv('CORS_ORIGINS', 'http://localhost:3000,http://127.0.0.1:3000').split(','))

    def validate(self):
        if self.mode not in ('demo', 'live'):
            raise ValueError('APP_MODE must be demo or live')
        if self.production and (len(self.internal_token) < 32 or not os.getenv('APP_ACCESS_CODE') or len(os.getenv('APP_SESSION_SECRET', '')) < 32):
            raise ValueError('Production requires a private API token, application access code, and session secret')
        if self.mode == 'live' and self.internal_token == 'local-demo-only':
            raise ValueError('Set a private API_INTERNAL_TOKEN before enabling live providers')

settings = Settings()
