"""Single small official-data request; never prints keys, URLs or raw responses."""
import json
import argparse
import sys
from pathlib import Path
import httpx
from dotenv import dotenv_values

parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--unfiltered',action='store_true',help='Request one record without state or commodity filters')
args=parser.parse_args()
values=dotenv_values(Path(__file__).resolve().parents[1]/'.env')
key=values.get('DATA_GOV_API_KEY')
if not key:
    print('DATA_GOV_API_KEY is missing from the project .env file.')
    sys.exit(1)
resource=values.get('AGMARKNET_RESOURCE_ID') or '9ef84268-d588-465a-a308-a864a43d0070'
params={'api-key':key,'format':'json','limit':1,'offset':0}
if not args.unfiltered: params.update({'filters[state.keyword]':'Punjab','filters[commodity]':'Tomato'})
print('Checking HTTPS and requesting one '+('unfiltered' if args.unfiltered else 'Punjab tomato')+' record (no retries)...',flush=True)
phases=[]
def trace(event,info):
    # Record protocol phase names only, never headers, URLs, payloads or exceptions.
    phases.append(event)
try:
    with httpx.Client(timeout=httpx.Timeout(25,connect=10),follow_redirects=False) as client:
        response=client.get('https://api.data.gov.in/resource/'+resource,params=params,headers={'Accept':'application/json','User-Agent':'MandiMitra/1.0'},extensions={'trace':trace})
    result={'http_status':response.status_code,'content_type':response.headers.get('content-type','')}
    try:
        body=response.json()
        if isinstance(body,dict):
            records=body.get('records')
            result['records_returned']=len(records) if isinstance(records,list) else None
            result['has_error_field']=bool(body.get('error'))
        else: result['json_object']=False
    except ValueError: result['valid_json']=False
    print(json.dumps(result,indent=2))
except httpx.RequestError as exc:
    # Exception messages may contain the credential-bearing URL, so output types only.
    chain=[]
    current=exc
    while current is not None and len(chain)<5:
        chain.append(type(current).__name__)
        current=current.__cause__
    print(json.dumps({'request_failed':type(exc).__name__,'error_types':chain,'request_phases':phases[-12:]},indent=2))
    sys.exit(1)
