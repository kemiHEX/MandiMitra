"""Cross-platform local launcher. Starts only this application's child processes."""
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path
from urllib.request import urlopen
from dotenv import load_dotenv

ROOT=Path(__file__).resolve().parents[1]
load_dotenv(ROOT/'.env')
python=ROOT/('.venv/Scripts/python.exe' if os.name=='nt' else '.venv/bin/python')
if not python.exists(): python=Path(sys.executable)
node=shutil.which('node')
next_bin=ROOT/'apps/web/node_modules/next/dist/bin/next'
if not node or not next_bin.exists(): sys.exit('Install Node.js and run npm ci in apps/web first. See README.md.')
try:
    urlopen('http://127.0.0.1:8000/health',timeout=1)
    sys.exit('Port 8000 is already serving an application. Use the existing app or stop it before starting another copy.')
except OSError: pass
env=os.environ.copy();env['PYTHONPATH']=str(ROOT/'services/api');env['NEXT_TELEMETRY_DISABLED']='1'
processes=[]
try:
    processes.append(subprocess.Popen([str(python),'-m','uvicorn','app.main:app','--host','127.0.0.1','--port','8000','--no-access-log'],cwd=ROOT,env=env))
    processes.append(subprocess.Popen([node,str(next_bin),'dev','--webpack','--hostname','127.0.0.1','--port','3000'],cwd=ROOT/'apps/web',env=env))
    print('MandiMitra: open http://localhost:3000 when Ready appears. Press Ctrl+C here to stop.')
    while all(p.poll() is None for p in processes): time.sleep(1)
except KeyboardInterrupt: pass
finally:
    for process in processes:
        if process.poll() is None: process.terminate()
    for process in processes:
        try: process.wait(timeout=10)
        except subprocess.TimeoutExpired: process.kill()
