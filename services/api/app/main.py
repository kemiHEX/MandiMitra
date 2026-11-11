import asyncio
import hmac
import json
import logging
import re
import time
import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timezone, timedelta
from decimal import Decimal
import httpx
from fastapi import FastAPI, Request, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError
from .config import settings, ROOT
from .schemas import FarmerState, CostAssumptions, Observation, ChatRequest, CostRequest, SpeechRequest
from .storage import Store
from .decision import compare
from .conversation import offline_extract, apply_extraction, say, reply, normalized, UNIT, unit_name
from .integrations import agmarknet, gnani_stt, gnani_tts, groq_client, response_plan
from .integrations.common import ProviderError

log = logging.getLogger('mandimitra')
logging.basicConfig(level=logging.INFO, format='%(message)s')
logging.getLogger('httpx').setLevel(logging.WARNING)  # URLs may carry data.gov.in keys.
logging.getLogger('httpcore').setLevel(logging.WARNING)
store = Store(settings.database_path)
# Single-process deployment serializes session turns and Gnani account requests.
locks: dict[str, asyncio.Lock] = {}
gnani_lock = asyncio.Lock()

@asynccontextmanager
async def lifespan(app):
    settings.validate()
    async with httpx.AsyncClient(timeout=httpx.Timeout(35, connect=10), follow_redirects=False) as client:
        app.state.client = client
        yield

app = FastAPI(title='MandiMitra API', version='1.0.0', lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=settings.cors, allow_credentials=False, allow_methods=['GET','POST','PATCH','DELETE'], allow_headers=['Authorization','Content-Type','X-Session-ID'])

@app.middleware('http')
async def safety(request: Request, call_next):
    request_id, start = uuid.uuid4().hex, time.monotonic()
    if request.url.path not in ('/health','/docs','/openapi.json','/redoc'):
        token = request.headers.get('authorization', '').removeprefix('Bearer ')
        if not hmac.compare_digest(token, settings.internal_token): return JSONResponse({'error':'Unauthorized'},status_code=401)
        sid = request.headers.get('x-session-id','')
        if not re.fullmatch(r'[a-f0-9]{64}',sid): return JSONResponse({'error':'Invalid session'},status_code=401)
        request.state.sid = sid
        try: size = int(request.headers.get('content-length','0'))
        except ValueError: return JSONResponse({'error':'Invalid request size'},status_code=400)
        if size > 2_100_000: return JSONResponse({'error':'Request is too large'},status_code=413)
        if not store.allowed(sid): return JSONResponse({'error':'Please wait a minute before trying again.'},status_code=429)
        if request.url.path in ('/stt','/tts','/chat') and settings.mode == 'live':
            if not store.allowed('provider-session:'+sid, 50, 3600) or not store.allowed('provider-global',200,3600):
                return JSONResponse({'error':'The hourly provider allowance is reached. Please use the manual form.'},status_code=429)
    try:
        response = await call_next(request)
    except Exception as exc:
        log.error(json.dumps({'event':'request_error','request_id':request_id,'type':type(exc).__name__}))
        response = JSONResponse({'error':'Something went wrong. Your previous inputs are safe. Please try again.','request_id':request_id},status_code=500)
    response.headers['X-Request-ID'] = request_id
    response.headers['Cache-Control'] = 'no-store'
    response.headers['X-Content-Type-Options'] = 'nosniff'
    log.info(json.dumps({'event':'request','id':request_id,'path':request.url.path,'status':response.status_code,'ms':round((time.monotonic()-start)*1000)}))
    return response

@app.exception_handler(ProviderError)
async def provider_error(_, exc): return JSONResponse({'error':exc.message},status_code=exc.status)

@app.exception_handler(RequestValidationError)
async def validation_error(_, exc):
    return JSONResponse({'error':'Please check the entered values and units. Negative or invalid amounts are not allowed.','fields':['.'.join(str(p) for p in e['loc']) for e in exc.errors()]},status_code=422)

def session_lock(sid):
    if len(locks)>1000:
        for key in list(locks):
            if not locks[key].locked(): del locks[key]
    return locks.setdefault(sid, asyncio.Lock())

def add_message(data, role, text, language, **metadata):
    data['messages'].append({'id':uuid.uuid4().hex,'role':role,'text':text,'language':language,'created_at':datetime.now(timezone.utc).isoformat(),**metadata})
    data['messages'] = data['messages'][-30:]

def load_session(sid):
    data=store.get(sid)
    if data.get('data_mode',settings.mode)!=settings.mode:
        data.update(comparison=None,observations=[],costs={},messages=[],notes=['Data mode changed. Please refresh the references and reconfirm costs.'])
    data['data_mode']=settings.mode
    return data

def public(data):
    state = FarmerState.model_validate(data['state'])
    return {**data,'state':state.model_dump(mode='json'),'missing_fields':state.missing,'mode':settings.mode,'providers':{'stt':settings.mode=='live' and bool(settings.gnani_key),'tts':settings.mode=='live' and bool(settings.gnani_key),'llm':settings.mode=='live' and bool(settings.groq_key),'markets':settings.mode=='live' and bool(settings.data_key)}}

async def refresh(data, client):
    state = FarmerState.model_validate(data['state'])
    data['comparison'] = None
    if state.missing: return
    observations, notes = await agmarknet.observations(client,settings,state.crop,state.location)
    data['observations'] = [o.model_dump(mode='json') for o in observations]
    data['notes'] = notes
    data['comparison'] = compare(state,observations,{k:CostAssumptions.model_validate(v) for k,v in data['costs'].items()},datetime.now(timezone(timedelta(hours=5,minutes=30))).date())

@app.get('/health')
async def health(): return {'status':'ok','mode':settings.mode,'version':'1.0.0'}

@app.get('/session')
async def get_session(request: Request): return public(load_session(request.state.sid))

@app.delete('/session')
async def reset(request: Request, everything: bool=False):
    async with session_lock(request.state.sid): store.delete(request.state.sid,everything)
    return {'ok':True}

@app.post('/demo')
async def demo(request: Request):
    if settings.mode != 'demo': raise HTTPException(409,'Demo fixtures are disabled in live mode')
    async with session_lock(request.state.sid):
        data = load_session(request.state.sid)
        language = data['state'].get('preferred_language','en')
        data.update(state=FarmerState(crop='tomato',crop_term='tamatar',crop_variety='Local',quantity=40,trader_offer=900,location='Ludhiana',preferred_language=language,baseline_confirmed=True).model_dump(mode='json'),messages=[],costs={})
        fixture = json.loads((ROOT/'data/samples/markets.json').read_text(encoding='utf-8'))
        for r in fixture['markets']:
            data['costs'][r['id']] = CostAssumptions(transport=r['transport'],loading=r['loading'],other=r['other'],confirmed=True).model_dump(mode='json')
        data['active_market_id']='demo-khanna'
        await refresh(data,request.app.state.client)
        add_message(data,'user','Mere kol 40 quintal tamatar ne. Vyapari 900 rupaye prati quintal de reha hai. Main Ludhiana ton haan.',language,source='illustrative_sample')
        add_message(data,'assistant',reply(FarmerState.model_validate(data['state']),data['comparison'],True),language)
        store.put(request.state.sid,data)
        return public(data)

@app.patch('/inputs')
async def inputs(request: Request, body: FarmerState):
    async with session_lock(request.state.sid):
        data=load_session(request.state.sid)
        old=FarmerState.model_validate(data['state'])
        if old.crop != body.crop or old.location != body.location:
            data['costs']={}
        data['state']=body.model_dump(mode='json')
        try: await refresh(data,request.app.state.client)
        except ProviderError as exc: data['notes']=[exc.message]
        add_message(data,'assistant',reply(body,data['comparison'],settings.mode=='demo'),body.preferred_language)
        store.put(request.state.sid,data)
        return public(data)

@app.post('/chat')
async def chat(request: Request, body: ChatRequest):
    async with session_lock(request.state.sid):
        data=load_session(request.state.sid)
        state=FarmerState.model_validate(data['state'])
        state.preferred_language=body.language
        original=next((s for s in data.get('transcripts',[]) if s['id']==body.transcript_id),None)
        if body.transcript_id and not original: raise HTTPException(422,'Transcript does not belong to this session')
        last=next((m['text'] for m in reversed(data['messages']) if m['role']=='assistant'),'')
        extraction = offline_extract(body.text,state) if settings.mode=='demo' else await groq_client.extract(request.app.state.client,settings,body.text,state,last)
        pending=data.get('pending_offer')
        pending_unit=re.fullmatch(r'(?:per |prati |ਪ੍ਰਤੀ |प्रति |/)?'+UNIT+r'[.!।]?',normalized(body.text).strip())
        if pending is not None and pending_unit:
            extraction.intent='compare'
            extraction.trader_offer=pending
            extraction.offer_unit=unit_name(pending_unit[1])
            extraction.clarification=None
            data.pop('pending_offer',None)
        add_message(data,'user',body.text,body.language,source='reviewed_voice' if original else 'text',**({'original_transcript':original['text']} if original else {}))
        answer=None
        if extraction.intent in ('unsupported','unknown','explain'):
            answer=say(extraction.intent,body.language)
        elif extraction.clarification:
            answer=extraction.clarification
            if extraction.trader_offer is not None and extraction.offer_unit is None:
                data['pending_offer']=extraction.trader_offer
                extraction.trader_offer=None
            try: state=apply_extraction(state,extraction)
            except ValueError: pass
            data['comparison']=None
        else:
            try: state=apply_extraction(state,extraction)
            except ValueError:
                answer={'en':'Please check the quantity and offer. Use positive weights and nonnegative prices.','pa':'ਮਾਤਰਾ ਅਤੇ ਭਾਅ ਦੀ ਜਾਂਚ ਕਰੋ। ਮਾਤਰਾ ਸਿਫ਼ਰ ਤੋਂ ਵੱਧ ਹੋਣੀ ਚਾਹੀਦੀ ਹੈ।','hi':'मात्रा और भाव की जाँच करें। मात्रा शून्य से अधिक होनी चाहिए।'}[body.language]
            if extraction.transport is not None and not answer:
                matching=[o for o in data['observations'] if extraction.market_name and o['market'].casefold()==extraction.market_name.casefold()]
                target=matching[0]['id'] if len(matching)==1 else data.get('active_market_id') if not extraction.market_name else None
                if target and target in data['costs']:
                    try:
                        c=CostAssumptions.model_validate({**data['costs'][target],'transport':str(extraction.transport)})
                        data['costs'][target]=c.model_dump(mode='json')
                    except ValidationError: answer='Please enter a valid, nonnegative transport estimate.'
                else: answer={'en':'Which market is that transport estimate for? Enter its costs in the comparison card.','pa':'ਇਹ ਢੋਆਈ ਦਾ ਖਰਚਾ ਕਿਹੜੀ ਮੰਡੀ ਲਈ ਹੈ? ਉਸ ਮੰਡੀ ਦੇ ਕਾਰਡ ਵਿੱਚ ਭਰੋ।','hi':'यह ढुलाई का खर्च किस मंडी के लिए है? उस मंडी के कार्ड में भरें।'}[body.language]
        old=FarmerState.model_validate(data['state'])
        if state.crop != old.crop or state.location != old.location:
            data['costs']={}
        data['state']=state.model_dump(mode='json')
        if answer is None:
            try:
                await refresh(data,request.app.state.client)
                answer=reply(state,data['comparison'],settings.mode=='demo')
                if settings.mode=='live' and data['comparison'] and data['comparison']['best_option_id']:
                    try:
                        focus=await response_plan.choose(request.app.state.client,settings,body.text,data['comparison'])
                        answer=response_plan.emphasis(focus,data['comparison'],body.language)+answer
                    except ProviderError:
                        data['notes'].append('The explanation planner was unavailable; using the reviewed localized explanation.')
            except ProviderError as exc:
                data['notes']=[exc.message]
                answer=exc.message
        add_message(data,'assistant',answer,body.language)
        store.put(request.state.sid,data)
        return public(data)

@app.patch('/costs')
async def costs(request: Request, body: CostRequest):
    async with session_lock(request.state.sid):
        data=load_session(request.state.sid)
        if body.market_id not in [o['id'] for o in data['observations']]: raise HTTPException(404,'Market not found in this session')
        data['costs'][body.market_id]=body.costs.model_dump(mode='json')
        data['active_market_id']=body.market_id
        await refresh(data,request.app.state.client)
        state=FarmerState.model_validate(data['state'])
        add_message(data,'assistant',reply(state,data['comparison'],settings.mode=='demo'),state.preferred_language)
        store.put(request.state.sid,data)
        return public(data)

@app.post('/compare')
async def recalculate(request: Request):
    async with session_lock(request.state.sid):
        data=load_session(request.state.sid)
        await refresh(data,request.app.state.client)
        store.put(request.state.sid,data)
        return public(data)

@app.get('/decisions')
async def decisions(request: Request): return store.decisions(request.state.sid)

@app.post('/decisions')
async def save(request: Request):
    async with session_lock(request.state.sid):
        data=load_session(request.state.sid)
        if not data.get('comparison') or not any(o['status']=='calculated' for o in data['comparison']['options']): raise HTTPException(422,'Calculate a comparison before saving')
        decision={'id':uuid.uuid4().hex,'saved_at':datetime.now(timezone.utc).isoformat(),'state':data['state'],'comparison':data['comparison'],'mode':settings.mode,'notes':data['notes']}
        store.save_decision(request.state.sid,decision)
        return decision

@app.delete('/decisions/{decision_id}')
async def delete_decision(request: Request, decision_id: str):
    store.delete_decision(request.state.sid,decision_id)
    return {'ok':True}

@app.post('/stt')
async def stt(request: Request, audio_file: UploadFile=File(...)):
    if audio_file.content_type not in ('audio/wav','audio/x-wav','audio/wave'): raise HTTPException(422,'Upload WAV audio')
    audio=await audio_file.read(2_000_001)
    await audio_file.close()
    async with gnani_lock: result=await gnani_stt.transcribe(request.app.state.client,settings,audio)
    async with session_lock(request.state.sid):
        data=load_session(request.state.sid)
        transcript_id=uuid.uuid4().hex
        data['transcripts']=(data.get('transcripts',[])+[{'id':transcript_id,'text':result['transcript']}])[-5:]
        store.put(request.state.sid,data)
    return {**result,'transcript_id':transcript_id}

@app.post('/tts')
async def tts(request: Request, body: SpeechRequest):
    data=load_session(request.state.sid)
    message=next((m for m in data['messages'] if m['id']==body.message_id and m['role']=='assistant'),None)
    if not message: raise HTTPException(404,'Answer not found in this session')
    async with gnani_lock: audio=await gnani_tts.synthesize(request.app.state.client,settings,message['text'],message['language'])
    return Response(audio,media_type='audio/wav')
