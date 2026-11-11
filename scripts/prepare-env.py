"""Create local settings and fill only missing app secrets. Never prints secrets."""
import argparse
import os
import re
import secrets
from pathlib import Path

parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--private',action='store_true',help='Also generate an access code if missing')
args=parser.parse_args()
root=Path(__file__).resolve().parents[1]
target=root/'.env'
text=(target if target.exists() else root/'.env.example').read_text(encoding='utf-8-sig')
names=['API_INTERNAL_TOKEN','APP_SESSION_SECRET']+(['APP_ACCESS_CODE'] if args.private else [])
changed=[]
for name in names:
    pattern=re.compile(r'^'+re.escape(name)+r'\s*=(.*)$',re.MULTILINE)
    match=pattern.search(text)
    if match and match.group(1).strip().strip('\"\''):
        continue
    line=name+'='+secrets.token_hex(32 if name!='APP_ACCESS_CODE' else 16)
    text=pattern.sub(lambda _:line,text,count=1) if match else text.rstrip()+'\n'+line+'\n'
    changed.append(name)
if not target.exists():
    fd=os.open(target,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
    with os.fdopen(fd,'w',encoding='utf-8',newline='\n') as file: file.write(text)
elif changed:
    target.write_text(text,encoding='utf-8',newline='\n')
if os.name!='nt': target.chmod(0o600)
print('Settings ready in the project .env file. Existing nonempty values were preserved.')
print('Generated: '+(', '.join(changed) if changed else 'nothing; values already present'))
if args.private: print('Read APP_ACCESS_CODE locally in .env to sign in. Do not post the file or secrets in chat.')
