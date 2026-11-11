import hashlib
import json
import time
from datetime import datetime, timezone
from decimal import Decimal
from ..config import ROOT
from ..schemas import Observation
from .common import ProviderError, request, json_body

SOURCE_URL = 'https://www.data.gov.in/resource/current-daily-price-various-commodities-various-markets-mandi'
CROPS = {'tomato': 'Tomato', 'wheat': 'Wheat', 'potato': 'Potato'}
_cache = {}

def demo_records(crop: str):
    if crop != 'tomato': return []
    fixture = json.loads((ROOT / 'data/samples/markets.json').read_text(encoding='utf-8'))
    return [Observation(id=r['id'], source='MandiMitra illustrative fixture', source_url='local:data/samples/markets.json', kind='demonstration_fixture', commodity='tomato', variety='Local', grade=None, market=r['market'], district=r['district'], state='Punjab', observation_date=fixture['observation_date'], min_price=r['min_price'], max_price=r['max_price'], modal_price=r['modal_price'], retrieved_at=datetime.now(timezone.utc)) for r in fixture['markets']]

def parse_record(row: dict, retrieved_at: datetime) -> Observation:
    required = ['state','district','market','commodity','variety','arrival_date','min_price','max_price','modal_price']
    if any(not str(row.get(k, '')).strip() for k in required): raise ValueError('Incomplete source record')
    crop = next((k for k,v in CROPS.items() if v.casefold() == row['commodity'].strip().casefold()), None)
    if not crop: raise ValueError('Unsupported commodity')
    if row.get('price_unit', 'INR/quintal') not in ('INR/quintal', 'Rs/Quintal'): raise ValueError('Unverified price unit')
    day = datetime.strptime(row['arrival_date'], '%d/%m/%Y').date()
    identity = '|'.join(str(row[k]) for k in ['state','district','market','commodity','variety']) + '|' + str(row.get('grade', ''))
    return Observation(id='ogd-' + hashlib.sha256(identity.encode()).hexdigest()[:16], source='AGMARKNET / Directorate of Marketing & Inspection via data.gov.in', source_url=SOURCE_URL, kind='official_observation', commodity=crop, variety=row['variety'], grade=row.get('grade') or None, market=row['market'], district=row['district'], state=row['state'], observation_date=day, min_price=Decimal(str(row['min_price']).replace(',', '')), modal_price=Decimal(str(row['modal_price']).replace(',', '')), max_price=Decimal(str(row['max_price']).replace(',', '')), retrieved_at=retrieved_at)

async def observations(client, settings, crop: str, location: str):
    if settings.mode == 'demo':
        return demo_records(crop), ['Illustrative demo dataset. No live market feed is connected.']
    if not settings.data_key: raise ProviderError('Official market data needs a data.gov.in API key. No demonstration prices have been substituted.')
    key = (settings.resource_id, crop, location.casefold())
    cached = _cache.get(key)
    if cached and time.monotonic() - cached[0] < 900:
        return cached[1], [*cached[2], 'Official observations cached for up to 15 minutes; observation dates are unchanged.']
    records, skipped, total = [], 0, 0
    retrieved = datetime.now(timezone.utc)
    for offset in range(0, 1000, 100):
        params = {'api-key': settings.data_key, 'format': 'json', 'limit': 100, 'offset': offset, 'filters[state.keyword]': 'Punjab', 'filters[commodity]': CROPS[crop]}
        response = await request(client, 'GET', f'https://api.data.gov.in/resource/{settings.resource_id}', params=params, headers={'Accept':'application/json','User-Agent':'MandiMitra/1.0'})
        payload = json_body(response)
        if not isinstance(payload.get('records'), list): raise ProviderError('Official data returned an unexpected format. No prices were used.')
        page = payload['records']
        for row in page:
            try:
                o = parse_record(row, retrieved)
                if o.state.casefold() == 'punjab' and o.commodity == crop: records.append(o)
            except (ValueError, TypeError, KeyError): skipped += 1
        total += len(page)
        if len(page) < 100: break
    notes = [f'{skipped} incomplete or incompatible records excluded.'] if skipped else []
    if total >= 1000: notes.append('Results limited to 1,000 Punjab records; coverage may be incomplete.')
    # Do not pretend to know distances. Prefer exact district matches; otherwise explain state-wide coverage.
    local = [r for r in records if r.district.casefold() == location.casefold() or r.market.casefold() == location.casefold()]
    if local: records = local
    elif records: notes.append('No exact location match. Showing Punjab references; distances and route costs are not verified.')
    if len(_cache) >= 500: _cache.pop(next(iter(_cache)))
    _cache[key] = (time.monotonic(), records, notes)
    return records, notes
