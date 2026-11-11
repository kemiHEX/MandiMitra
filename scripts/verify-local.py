"""Exercise running local services with a disposable session. Never calls providers."""
import json
import os
from pathlib import Path
from urllib.parse import urlparse
import httpx
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[1]/'.env')
base=os.getenv('VERIFY_BASE_URL') or os.getenv('APP_PUBLIC_URL') or 'http://127.0.0.1:3000'
if urlparse(base).hostname not in ('localhost','127.0.0.1','::1'):
    raise SystemExit('This test is restricted to your local demo server.')
checks=[]
def check(name,condition):
    assert condition,name
    checks.append(name)

with httpx.Client(base_url=base,headers={'Origin':base.rstrip('/')},timeout=15) as client:
    check('Production frontend serves HTML',client.get('/').status_code==200)
    check('Private API rejects unauthenticated access',httpx.get('http://127.0.0.1:8000/session').status_code==401)
    response=client.get('/api/session')
    check('Frontend proxy reaches backend in demo mode',response.status_code==200 and response.json()['mode']=='demo')
    cookie=response.headers['set-cookie'].lower()
    check('HttpOnly and SameSite strict cookie','httponly' in cookie and 'samesite=strict' in cookie)
    check('Cross-origin writes rejected',client.post('/api/demo',headers={'Origin':'https://untrusted.example'}).status_code==403)
    check('Oversized body rejected',client.post('/api/chat',content='x'*32001).status_code==413)
    check('Malformed JSON rejected',client.post('/api/chat',content='{',headers={'Content-Type':'application/json'}).status_code==422)
    data=client.post('/api/demo').json()
    check('Demonstration provenance explicit',all(o['observation']['kind']=='demonstration_fixture' for o in data['comparison']['options']))
    check('Brief sample calculation',data['comparison']['options'][0]['net']=='41000.00')
    costs=data['costs']['demo-khanna'];costs['transport']='4000'
    data=client.patch('/api/costs',json={'market_id':'demo-khanna','costs':costs}).json()
    check('Cost edit recomputes',data['comparison']['options'][0]['net']=='42500.00')
    saved=client.post('/api/decisions').json()
    data=client.post('/api/chat',json={'text':'Chali nahi, chaudah quintal.','language':'pa'}).json()
    check('Punjabi correction',data['state']['quantity']=='14.0' and data['comparison']['trader']['net']=='12600.00')
    check('Saved snapshot immutable',client.get('/api/decisions').json()[0]['comparison']==saved['comparison'])
    with httpx.Client(base_url=base,timeout=15) as other:
        check('Session isolation',other.get('/api/session').json()['state']['crop'] is None and other.get('/api/decisions').json()==[])
    check('Own test session cleanup',client.delete('/api/session?everything=true').status_code==200)

print(json.dumps({'checks_passed':len(checks),'checks':checks,'providers_called':False},indent=2))
