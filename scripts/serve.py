"""Run the private production demo. Keep the separate tunnel running."""
import argparse
import os
import shutil
import socket
import subprocess
import sys
import time
from pathlib import Path
from urllib.parse import urlparse
from dotenv import dotenv_values

ROOT=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--check',action='store_true')
args=parser.parse_args()
env=os.environ.copy()
env.update({k:v for k,v in dotenv_values(ROOT/'.env').items() if v is not None})
origin=env.get('APP_PUBLIC_URL','').rstrip('/')
parsed=urlparse(origin)
if parsed.scheme!='https' or not parsed.hostname or parsed.path or parsed.query or parsed.fragment or parsed.username:
    sys.exit('Set APP_PUBLIC_URL to the exact HTTPS tunnel origin in .env.')
for field in ('APP_SESSION_SECRET','API_INTERNAL_TOKEN','APP_ACCESS_CODE'):
    if len(env.get(field,'')) < (16 if field=='APP_ACCESS_CODE' else 32):
        sys.exit('Missing or short private settings. Run scripts/prepare-env.py --private first.')
node=shutil.which('node')
next_bin=ROOT/'apps/web/node_modules/next/dist/bin/next'
if not node or not next_bin.exists(): sys.exit('Node.js or frontend dependencies are missing.')
if not (ROOT/'apps/web/.build/BUILD_ID').exists(): sys.exit('Run npm.cmd run build in apps/web first.')
env.update(DEPLOYMENT_ENV='production',NODE_ENV='production',NEXT_TELEMETRY_DISABLED='1',
           APP_PUBLIC_URL=origin,CORS_ORIGINS=origin,API_BASE_URL='http://127.0.0.1:8000',PYTHONPATH=str(ROOT/'services/api'))
if args.check:
    print('Private settings and production build checks passed. No servers started; no provider requests sent.')
    sys.exit(0)
for port in (3000,8000):
    with socket.socket() as sock:
        if sock.connect_ex(('127.0.0.1',port))==0:
            sys.exit(f'Port {port} is already in use. Stop the previous app before starting this launcher.')
processes=[]
try:
    processes.append(subprocess.Popen([sys.executable,'-m','uvicorn','app.main:app','--host','127.0.0.1','--port','8000','--no-access-log'],cwd=ROOT,env=env))
    processes.append(subprocess.Popen([node,str(next_bin),'start','--hostname','127.0.0.1','--port','3000'],cwd=ROOT/'apps/web',env=env))
    print('Open '+origin+' after both services are ready. Sign in with your access code.',flush=True)
    print('Keep this window and the tunnel window open. Ctrl+C stops this app.',flush=True)
    while all(p.poll() is None for p in processes): time.sleep(.5)
except KeyboardInterrupt: pass
finally:
    for process in processes:
        if process.poll() is None: process.terminate()
    for process in processes:
        try: process.wait(timeout=10)
        except subprocess.TimeoutExpired: process.kill()
