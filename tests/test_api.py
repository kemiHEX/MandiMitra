import pytest
from fastapi.testclient import TestClient
from app import main
from app.storage import Store

@pytest.fixture
def client(tmp_path,monkeypatch):
    monkeypatch.setattr(main,'store',Store(str(tmp_path/'test.db')))
    monkeypatch.setattr(main.settings,'mode','demo')
    monkeypatch.setattr(main.settings,'internal_token','local-demo-only')
    monkeypatch.setattr(main.settings,'production',False)
    with TestClient(main.app) as c:
        c.headers.update({'Authorization':'Bearer local-demo-only','X-Session-ID':'a'*64})
        yield c
def test_health(client): assert client.get('/health').json()['status']=='ok'
def test_auth_required(client):
    client.headers.pop('Authorization')
    assert client.get('/session').status_code==401
def test_isolation(client):
    client.post('/demo');client.headers['X-Session-ID']='b'*64
    assert client.get('/session').json()['state']['crop'] is None
    assert client.get('/decisions').json()==[]
def test_full_text_flow_and_saved_snapshot(client):
    assert client.post('/chat',json={'text':'Mere kol 40 quintal tamatar ne.','language':'pa'}).json()['missing_fields']==['trader_offer','location']
    assert client.post('/chat',json={'text':'900 rupaye','language':'pa'}).json()['state']['trader_offer']=='900.0'
    r=client.post('/chat',json={'text':'Ludhiana','language':'pa'}).json()
    assert r['comparison']['options'][0]['status']=='costs_needed'
    sample=client.post('/demo').json()
    assert sample['comparison']['options'][0]['net']=='41000.00'
    saved=client.post('/decisions').json()
    changed=client.post('/chat',json={'text':'Chali nahi, chaudah quintal.','language':'pa'}).json()
    assert changed['state']['quantity']=='14.0'
    assert changed['comparison']['trader']['net']=='12600.00'
    assert client.get('/decisions').json()[0]['comparison']==saved['comparison']
def test_transport_correction(client):
    client.post('/demo')
    r=client.post('/chat',json={'text':'Khanna transport 5500 nahi, 4000 laguga.','language':'en'}).json()
    assert r['comparison']['options'][0]['net']=='42500.00'
def test_inputs_validation(client):
    assert client.patch('/inputs',json={'quantity':-10}).status_code==422
def test_invalid_json(client):
    assert client.post('/chat',content=b'{',headers={'Content-Type':'application/json'}).status_code==422
def test_demo_does_not_fake_speech(client):
    from test_integrations import wav
    r=client.post('/stt',files={'audio_file':('test.wav',wav(),'audio/wav')})
    assert r.status_code==503 and 'not sent or saved' in r.json()['error']
def test_tts_scoped_to_message(client):
    assert client.post('/tts',json={'message_id':'doesnotexist'}).status_code==404
def test_reset_and_delete(client):
    client.post('/demo');client.post('/decisions');client.delete('/session')
    assert client.get('/session').json()['state']['crop'] is None
    assert len(client.get('/decisions').json())==1
    client.delete('/session?everything=true')
    assert client.get('/decisions').json()==[]
def test_rate_limit(client):
    for _ in range(30): assert client.get('/session').status_code==200
    assert client.get('/session').status_code==429
def test_unsupported_preserves_state(client):
    client.post('/demo');r=client.post('/chat',json={'text':'Diagnose crop disease','language':'en'}).json()
    assert r['state']['quantity']=='40' and 'crop-selling' in r['messages'][-1]['text']
def test_costs_validate_market_identity(client):
    assert client.patch('/costs',json={'market_id':'invented','costs':{}}).status_code==404
def test_location_change_clears_costs(client):
    r=client.post('/demo').json();state=r['state'];state['location']='Patiala'
    changed=client.patch('/inputs',json=state).json()
    assert changed['costs']=={}
def test_ambiguous_offer_clarification_keeps_details(client):
    first=client.post('/chat',json={'text':'40 quintal tomato offer 900 Ludhiana','language':'en'}).json()
    assert first['state']['quantity']=='40.0' and first['state']['trader_offer'] is None
    clarified=client.post('/chat',json={'text':'per quintal','language':'en'}).json()
    assert clarified['state']['trader_offer']=='900.0' and clarified['missing_fields']==[]
def test_mode_switch_discards_demo_results(client,monkeypatch):
    client.post('/demo')
    monkeypatch.setattr(main.settings,'mode','live')
    r=client.get('/session').json()
    assert r['comparison'] is None and r['costs']=={}

def test_reviewed_voice_preserves_original_and_is_session_bound(client,monkeypatch):
    from test_integrations import wav
    async def fake_transcribe(*_):
        return {'transcript':'Mere kol 40 quintal tamatar ne.','language':'pa-IN','duration_seconds':1,'provider':'mock'}
    monkeypatch.setattr(main.gnani_stt,'transcribe',fake_transcribe)
    speech=client.post('/stt',files={'audio_file':('test.wav',wav(),'audio/wav')}).json()
    r=client.post('/chat',json={'text':'Mere kol 14 quintal tamatar ne.','language':'pa','transcript_id':speech['transcript_id']}).json()
    assert r['state']['quantity']=='14.0'
    assert r['messages'][0]['original_transcript']=='Mere kol 40 quintal tamatar ne.'
    assert r['messages'][0]['source']=='reviewed_voice'
    client.headers['X-Session-ID']='b'*64
    assert client.post('/chat',json={'text':'14 quintal tomato','transcript_id':speech['transcript_id']}).status_code==422

def test_invalid_transcript_rejected_before_paid_extraction(client,monkeypatch):
    monkeypatch.setattr(main.settings,'mode','live')
    async def never_call(*_): raise AssertionError('Must validate ownership before calling Groq')
    monkeypatch.setattr(main.groq_client,'extract',never_call)
    assert client.post('/chat',json={'text':'test','transcript_id':'c'*32}).status_code==422

def test_tts_failure_leaves_text_answer(client):
    r=client.post('/demo').json()
    answer=r['messages'][-1]
    assert client.post('/tts',json={'message_id':answer['id']}).status_code==503
    assert client.get('/session').json()['messages'][-1]==answer
