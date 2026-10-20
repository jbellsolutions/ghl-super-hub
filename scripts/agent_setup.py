#!/usr/bin/env python3
"""Verified release installation plus native Claude Code / Hermes plugin registration."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shlex
import shutil
import stat
import subprocess
import sys
import tempfile
import urllib.request
import zipfile

REPO='jbellsolutions/ghl-super-hub'

def download(url,path=None):
    request=urllib.request.Request(url,headers={'User-Agent':'ghl-super-hub-installer','Accept':'application/vnd.github+json'})
    with urllib.request.urlopen(request,timeout=90) as response:
        if path is None:return response.read()
        with open(path,'wb') as handle:shutil.copyfileobj(response,handle)

def unpack(archive,destination):
    with zipfile.ZipFile(archive) as z:
        for item in z.infolist():
            parts=Path(item.filename).parts
            if not parts or parts[0]!='ghl-super-hub' or '..' in parts or Path(item.filename).is_absolute() or stat.S_ISLNK(item.external_attr>>16):raise ValueError('Unsafe archive member')
            rel=Path(*parts[1:])
            if not rel.parts:continue
            out=destination/rel
            if item.is_dir():out.mkdir(parents=True,exist_ok=True)
            else:
                out.parent.mkdir(parents=True,exist_ok=True);out.write_bytes(z.read(item))
                out.chmod((item.external_attr>>16)&0o777 or 0o644)

def run(command,already_ok=False):
    result=subprocess.run(command,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
    if result.returncode:
        lowered=result.stdout.lower()
        if already_ok and any(term in lowered for term in ('already installed','already exists','already registered','already added')):return
        # A failed provider command is surfaced, never worked around by changing trust settings.
        raise RuntimeError('Command failed: '+shlex.join(command)+'\n'+result.stdout[-2500:])
    print(result.stdout.strip() or 'Completed '+shlex.join(command),flush=True)

def agents(target):
    names=['claude','hermes'] if target in ('auto','both') else [target]
    found={name:shutil.which(name) for name in names}
    if target=='auto':found={name:exe for name,exe in found.items() if exe}
    if not found or any(not exe for exe in found.values()):raise ValueError('Install Claude Code or Hermes first, or run this in the agent’s terminal. Select --agent claude, hermes, or both.')
    return found

def register(found):
    for name,exe in found.items():
        if name=='claude':
            run([exe,'plugin','marketplace','add',REPO],already_ok=True)
            run([exe,'plugin','install','ghl-super-hub@ghl-super-hub','--scope','user'],already_ok=True)
        else:
            run([exe,'plugins','install',REPO,'--enable'],already_ok=True)
            run([exe,'plugins','enable','ghl-super-hub'],already_ok=True)

def verify(python):
    messages=[{'jsonrpc':'2.0','id':1,'method':'initialize','params':{'protocolVersion':'2024-11-05','capabilities':{},'clientInfo':{'name':'installer','version':'1'}}},{'jsonrpc':'2.0','id':2,'method':'tools/list'}]
    result=subprocess.run([str(python),'-m','ghl_hub.bootstrap','hub','mcp'],input=''.join(json.dumps(m)+'\n' for m in messages),text=True,capture_output=True,timeout=45,check=True)
    responses=[json.loads(line) for line in result.stdout.splitlines()]
    if len(responses)!=2 or 'serverInfo' not in responses[0].get('result',{}) or len(responses[1].get('result',{}).get('tools',[]))!=6:raise ValueError('MCP verification did not discover all six tools')

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--agent',choices=['auto','claude','hermes','both'],default='auto');parser.add_argument('--version',help='GitHub release tag; default is the latest published release');args=parser.parse_args()
    found=agents(args.agent)
    if args.version and not re.fullmatch(r'v\d+\.\d+\.\d+',args.version):raise ValueError('Use a release tag such as v2.2.0')
    release_url='https://github.com/'+REPO+'/releases/'+('download/'+args.version if args.version else 'latest/download')
    base=Path(os.environ.get('XDG_DATA_HOME',str(Path.home()/'.local/share')))/'ghl-super-hub'
    releases=base/'releases';releases.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='.staging-',dir=releases) as staging:
        archive=Path(staging)/'bundle.zip';download(release_url+'/ghl-super-hub.zip',archive)
        expected=download(release_url+'/ghl-super-hub.zip.sha256').decode().split()[0]
        if not re.fullmatch(r'[a-fA-F0-9]{64}',expected) or hashlib.sha256(archive.read_bytes()).hexdigest()!=expected.lower():raise ValueError('Release checksum mismatch; nothing installed')
        with zipfile.ZipFile(archive) as package:
            tag='v'+json.loads(package.read('ghl-super-hub/plugin.json'))['version']
        if not re.fullmatch(r'v\d+\.\d+\.\d+',tag) or (args.version and args.version!=tag):raise ValueError('Release version does not match the package')
        root=releases/tag
        if root.is_symlink():raise ValueError('Release destination must not be a symbolic link')
        if root.exists():
            stamp=root/'.ghl-download.json'
            if not stamp.is_file() or json.loads(stamp.read_text()).get('sha256')!=expected:raise ValueError('Existing release directory is not owned by this installer or has a different checksum')
        else:
            candidate=Path(staging)/'source';candidate.mkdir();unpack(archive,candidate)
            (candidate/'.ghl-download.json').write_text(json.dumps({'sha256':expected,'tag':tag}));candidate.rename(root)
    python=root/'.venv/bin/python'
    if not python.is_file() or not (root/'.ghl-runtime.json').exists():
        subprocess.run([sys.executable,'-m','venv',str(root/'.venv')],check=True)
        subprocess.run([str(python),'-m','pip','install','--quiet','-e',str(root)],check=True)
    # Use the release's own code to fingerprint the sidecar shared with native plugin installs.
    code='import sys,json;sys.path.insert(0,sys.argv[1]);from scripts.plugin_runtime import fingerprint;from pathlib import Path;print(json.dumps({"fingerprint":fingerprint(Path(sys.argv[1]))}))'
    marker=subprocess.check_output([str(python),'-c',code,str(root)],text=True)
    (root/'.ghl-runtime.json').write_text(marker)
    verify(python)
    register(found)
    launcher=Path.home()/'.local/bin/ghl';launcher.parent.mkdir(parents=True,exist_ok=True)
    content='#!/bin/sh\n# Managed by ghl-super-hub installer\nexec bash '+shlex.quote(str(root/'ghl'))+' "$@"\n'
    if not launcher.exists() and not launcher.is_symlink() or launcher.is_file() and not launcher.is_symlink() and '# Managed by ghl-super-hub installer' in launcher.read_text():
        launcher.write_text(content);launcher.chmod(0o755)
    else:print('Existing ghl command preserved. CLI: '+str(root/'ghl'))
    print('\nInstalled for '+', '.join(found)+'. Verified all six MCP tools.')
    print('CLI: '+str(root/'ghl'))
    print('Next: start a new agent session, then use the ghl-operator skill.')
    print('Connect GHL once with: '+shlex.quote(str(root/'ghl'))+' hub connect')
    print('No GHL data was changed. Agent trust/permission prompts still apply.')

if __name__=='__main__':
    try:main()
    except Exception as exc:sys.exit('Installation stopped: '+str(exc))
