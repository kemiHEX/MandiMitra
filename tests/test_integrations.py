import asyncio
import io
import json
import wave
from datetime import datetime,timezone
import httpx
import pytest
from app.config import Settings
from app.schemas import Extraction,FarmerState
from app.integrations import agmarknet,gnani_stt,gnani_tts,groq_client
from app.integrations.common import ProviderError

def wav(seconds=1,rate=16000):
    stream=io.BytesIO()
    with wave.open(stream,'wb') as f:
        f.setparams((1,2,rate,0,'NONE','not compressed'));f.writeframes(b'\0\0'*int(rate*seconds))
    return stream.getvalue()
def test_valid_wav(): assert gnani_stt.validate_wav(wav())==1
@pytest.mark.parametrize('audio',[b'junk',wav(31),wav(.05),wav(1,48000),wav()[:-100]],ids=['not-wav','too-long','too-short','wrong-rate','truncated'])
def test_invalid_audio(audio):
    with pytest.raises(ProviderError): gnani_stt.validate_wav(audio)
def test_documented_stt_contract():
    def handler(req):
        assert req.url.path=='/stt/v3' and req.headers['X-API-Key-ID']=='test-key'
        assert b'prisma-v3.0' in req.content and b'indic-auto' in req.content and b'audio_file' in req.content
        return httpx.Response(200,json={'success':True,'transcript':'ਮੇਰੇ ਕੋਲ ਚਾਲੀ ਕੁਇੰਟਲ ਟਮਾਟਰ ਹਨ।','model':'prisma-v3.0','detected_language_code':'pa-IN'})
    async def run():
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            return await gnani_stt.transcribe(client,Settings(mode='live',gnani_key='test-key'),wav())
    assert asyncio.run(run())['language']=='pa-IN'
@pytest.mark.parametrize('body',[{'text':'invented schema'}, {'success':True,'transcript':''},{'success':True,'transcript':'cut','truncated':True}])
def test_stt_bad_response(body):
    async def run():
        async with httpx.AsyncClient(transport=httpx.MockTransport(lambda _:httpx.Response(200,json=body))) as client:
            await gnani_stt.transcribe(client,Settings(mode='live',gnani_key='key'),wav())
    with pytest.raises(ProviderError): asyncio.run(run())
def test_tts_binary_and_cache():
    gnani_tts._cache.clear();calls=[]
    def handler(req):
        body=json.loads(req.content);calls.append(body)
        assert body['model']=='timbre-v3.0' and body['voice']=='Prakash' and body['language']=='pa-IN'
        return httpx.Response(200,content=wav(1,48000),headers={'content-type':'audio/wav'})
    async def run():
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            settings=Settings(mode='live',gnani_key='key')
            a=await gnani_tts.synthesize(client,settings,'₹5000','pa')
            b=await gnani_tts.synthesize(client,settings,'₹5000','pa')
            assert a==b
    asyncio.run(run());assert len(calls)==1
def test_wrong_voice_rejected():
    async def run(): await gnani_tts.synthesize(None,Settings(mode='live',gnani_key='key',tts_voice='Nalini'),'Hello','en')
    with pytest.raises(ProviderError): asyncio.run(run())
def test_groq_structured_contract():
    extraction={k:None for k in Extraction.model_fields};extraction.update(intent='compare',crop='tomato',quantity=40,quantity_unit='quintal')
    def handler(req):
        body=json.loads(req.content)
        assert body['response_format']['json_schema']['strict'] is True
        assert body['model']=='openai/gpt-oss-120b'
        return httpx.Response(200,json={'choices':[{'message':{'content':json.dumps(extraction)}}]})
    async def run():
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            return await groq_client.extract(client,Settings(groq_key='key'),'40 quintal tomato',FarmerState(),'')
    assert asyncio.run(run()).quantity==40
def test_invalid_groq_json():
    async def run():
        async with httpx.AsyncClient(transport=httpx.MockTransport(lambda _:httpx.Response(200,json={'choices':[{'message':{'content':'not json'}}]}))) as client:
            await groq_client.extract(client,Settings(groq_key='key'),'test',FarmerState(),'')
    with pytest.raises(ProviderError): asyncio.run(run())
def record(): return {'state':'Punjab','district':'Ludhiana','market':'Khanna','commodity':'Tomato','variety':'Local','arrival_date':'08/11/2026','min_price':'1,000','max_price':'1,300','modal_price':'1,200'}
def test_official_parser():
    o=agmarknet.parse_record(record(),datetime.now(timezone.utc))
    assert o.modal_price==1200 and o.kind=='official_observation' and o.source_url.startswith('https://www.data.gov.in/')
@pytest.mark.parametrize('key,value',[('variety',''),('arrival_date','bad'),('modal_price','NaN'),('price_unit','INR/kg')])
def test_invalid_official_record(key,value):
    r=record();r[key]=value
    with pytest.raises(ValueError): agmarknet.parse_record(r,datetime.now(timezone.utc))
def test_no_key_never_falls_back():
    async def run(): return await agmarknet.observations(None,Settings(mode='live',data_key=''),'tomato','Ludhiana')
    with pytest.raises(ProviderError,match='No demonstration prices'): asyncio.run(run())
def test_demo_crop_unavailable(): assert agmarknet.demo_records('wheat')==[]
def test_live_market_contract():
    agmarknet._cache.clear()
    def handler(req):
        assert req.url.params['filters[state.keyword]']=='Punjab' and req.url.params['api-key']=='test-key'
        assert req.headers['user-agent']=='MandiMitra/1.0' and req.headers['accept']=='application/json'
        return httpx.Response(200,json={'records':[record()]})
    async def run():
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            return await agmarknet.observations(client,Settings(mode='live',data_key='test-key'),'tomato','Ludhiana')
    records,_=asyncio.run(run());assert len(records)==1 and records[0].kind=='official_observation'

def test_market_cache_keeps_coverage_warnings():
    agmarknet._cache.clear();calls=[]
    def handler(req):
        calls.append(req)
        return httpx.Response(200,json={'records':[record(),{}]})
    async def run():
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            settings=Settings(mode='live',data_key='test-key')
            _,first=await agmarknet.observations(client,settings,'tomato','Patiala')
            _,cached=await agmarknet.observations(client,settings,'tomato','Patiala')
            assert all(note in cached for note in first)
            assert any('No exact location match' in note for note in cached)
    asyncio.run(run());assert len(calls)==1
