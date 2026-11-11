"""Explicit opt-in live verification. Never prints secrets or raw provider bodies."""
import argparse
import asyncio
import json
import sys
from pathlib import Path
import httpx
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'services/api'))
from app.config import settings
from app.schemas import FarmerState
from app.integrations import agmarknet,gnani_stt,gnani_tts,groq_client
from app.integrations.common import ProviderError

async def main(args):
    if not args.allow_paid:
        print('No requests sent. Use --allow-paid to test configured live providers. This may consume your provider credits.')
        return 2
    settings.mode='live'
    report={}
    async with httpx.AsyncClient(timeout=35) as client:
        cases={
            'groq':lambda:groq_client.extract(client,settings,'Mere kol 40 quintal tamatar ne. Vyapari 900 rupaye prati quintal de reha hai. Main Ludhiana ton haan.',FarmerState(preferred_language='pa'),''),
            'markets':lambda:agmarknet.observations(client,settings,'tomato','Ludhiana'),
            'tts':lambda:gnani_tts.synthesize(client,settings,'ਇਹ ਇੱਕ ਜਾਂਚ ਹੈ। ਮੰਡੀ ਦਾ ਭਾਅ ਪੱਕੀ ਪੇਸ਼ਕਸ਼ ਨਹੀਂ ਹੈ।','pa')
        }
        if args.wav: cases['stt']=lambda:gnani_stt.transcribe(client,settings,Path(args.wav).read_bytes())
        elif not args.only: report['stt']={'status':'not_run','reason':'Pass --wav with a real 0.1–30 second 16 kHz mono PCM WAV.'}
        if args.only: cases={name:call for name,call in cases.items() if name==args.only}
        for name,call in cases.items():
            try:
                result=await call()
                report[name]={'status':'success'}
                if name=='markets': report[name]['observations']=len(result[0])
                if name=='groq':
                    report[name]['extracted']=result.model_dump()
                    expected={'intent':'compare','crop':'tomato','quantity':40,'quantity_unit':'quintal','trader_offer':900,'offer_unit':'quintal','location':'Ludhiana'}
                    mismatches=[field for field,value in expected.items() if getattr(result,field)!=value]
                    if mismatches:
                        report[name].update(status='failed',reason='Connected, but sample interpretation failed validation.',mismatched_fields=mismatches)
                if name=='tts': report[name]['audio_bytes']=len(result)
                if name=='stt': report[name]['transcript']=result['transcript']
            except ProviderError as exc: report[name]={'status':'failed','reason':exc.message}
    print(json.dumps(report,ensure_ascii=False,indent=2))
    return 0 if all(v['status']=='success' for v in report.values()) else 1

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--allow-paid',action='store_true');parser.add_argument('--wav');parser.add_argument('--only',choices=['groq','tts','markets'])
    sys.exit(asyncio.run(main(parser.parse_args())))
