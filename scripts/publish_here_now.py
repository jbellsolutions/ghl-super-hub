#!/usr/bin/env python3
"""Publish only site/ to here.now; keep claim/update credentials in ignored private state."""
import argparse
import hashlib
import json
import mimetypes
import os
from pathlib import Path
from urllib.parse import urlsplit
import requests

ROOT=Path(__file__).resolve().parents[1]
STATE=ROOT/'.publish'/'here-now.json'
API='https://here.now'

def save(value):
    STATE.parent.mkdir(exist_ok=True,mode=0o700)
    with open(STATE,'w',opener=lambda path,flags:os.open(path,flags,0o600)) as handle:json.dump(value,handle,indent=2)

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--update',action='store_true');args=parser.parse_args()
    if STATE.exists() and not args.update:parser.error('A publication already exists. Use --update to update the saved Site instead of duplicating it.')
    if args.update and not STATE.exists():parser.error('No saved publication to update')
    paths={p.relative_to(ROOT/'site').as_posix():p for p in (ROOT/'site').rglob('*') if p.is_file() and not any(part.startswith('.') for part in p.relative_to(ROOT/'site').parts)}
    headers={'X-HereNow-Client':'codex/direct-api'}
    key=os.environ.get('HERENOW_API_KEY','').strip();credential=Path.home()/'.herenow'/'credentials'
    if not key and credential.is_file():key=credential.read_text().strip()
    if key:headers['Authorization']='Bearer '+key
    body=dict(displayName='HighLevel Super Hub',displayDescription='Give your agent the keys to HighLevel: nine skills, CLI, MCP, API discovery and dashboard playbooks.',files=[dict(path=name,size=p.stat().st_size,hash=hashlib.sha256(p.read_bytes()).hexdigest(),contentType=mimetypes.guess_type(name)[0] or 'application/octet-stream') for name,p in paths.items()])
    previous=json.loads(STATE.read_text()) if STATE.exists() else {}
    if args.update:
        if previous.get('claimToken'):body['claimToken']=previous['claimToken']
        body['baseVersionId']=previous['live']['currentVersionId']
        result=requests.put(API+'/api/v1/publish/'+previous['slug'],headers=headers,json=body,timeout=60)
    else:result=requests.post(API+'/api/v1/publish',headers=headers,json=body,timeout=60)
    result.raise_for_status();pending=result.json();state={**previous,**pending};save(state)
    for upload in pending['upload']['uploads']:
        p=paths[upload['path']]
        hostname=urlsplit(upload['url']).hostname or ''
        if not hostname.endswith('.r2.cloudflarestorage.com'):raise ValueError('Unexpected upload host; inspect provider response before uploading')
        with p.open('rb') as handle:
            result=requests.put(upload['url'],headers=upload['headers'],data=handle,timeout=60,allow_redirects=False)
            result.raise_for_status()
    finalize=pending['upload']['finalizeUrl']
    if finalize.startswith('/'):finalize=API+finalize
    if urlsplit(finalize).netloc!='here.now':raise ValueError('Unexpected finalize host')
    result=requests.post(finalize,headers=headers,json={'versionId':pending['upload']['versionId']},timeout=60)
    result.raise_for_status();live=result.json();state['live']=live;save(state)
    if not live.get('success'):raise RuntimeError('here.now did not report a successful finalize')
    print(json.dumps(dict(siteUrl=live['siteUrl'],primaryUrl=live.get('primaryUrl'),publishStatus=live.get('publishStatus'),claimUrl=state.get('claimUrl'),warnings=live.get('warnings',[])),indent=2))
if __name__=='__main__':main()
