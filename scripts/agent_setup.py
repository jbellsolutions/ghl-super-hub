#!/usr/bin/env python3
"""Verified release installation for Claude Code plugins and Hermes skills/MCP."""
import argparse
import hashlib
import getpass
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
import warnings

REPO='jbellsolutions/ghl-super-hub'

def hermes_home():
    return Path(os.environ.get('HERMES_HOME') or str(Path.home()/'.hermes')).expanduser()

def find_agent(name):
    override=os.environ.get('GHL_'+name.upper()+'_BIN')
    if override:return override if Path(override).is_file() and os.access(override,os.X_OK) else None
    found=shutil.which(name)
    if found or name!='hermes':return found
    for path in (Path('/opt/hermes/.venv/bin/hermes'),hermes_home()/'hermes-agent/.venv/bin/hermes',Path.home()/'.local/bin/hermes'):
        if path.is_file() and os.access(path,os.X_OK):return str(path)
    return None

def hermes_python(exe):
    override=os.environ.get('GHL_HERMES_PYTHON')
    candidates=[Path(override)] if override else [Path(exe).parent/'python',Path(exe).resolve().parent/'python']
    if not override:
        try:
            first=Path(exe).read_text().splitlines()[0]
            if first.startswith('#!/') and len(shlex.split(first[2:]))==1 and Path(first[2:]).name.startswith('python'):candidates.append(Path(first[2:]))
        except (OSError,UnicodeError):pass
    for path in candidates:
        if path.is_file() and os.access(path,os.X_OK):
            try:result=subprocess.run([str(path),'-c','import sys,yaml; assert sys.version_info >= (3,10)'],capture_output=True,timeout=15)
            except (OSError,subprocess.TimeoutExpired):continue
            if result.returncode==0:return path
    return None

def check_hermes(exe):
    python=hermes_python(exe)
    if not python:return ['Set GHL_HERMES_PYTHON to the Hermes Python interpreter (with its existing PyYAML dependency).']
    helper=Path(__file__).with_name('hermes_setup.py')
    try:result=subprocess.run([str(python),str(helper),'--check','--home',str(hermes_home())],text=True,capture_output=True,timeout=20)
    except (OSError,subprocess.TimeoutExpired):return ['Hermes profile inspection could not run; check GHL_HERMES_PYTHON and profile access.']
    try:
        report=json.loads(result.stdout)
        if result.returncode and not report.get('problems'):return ['Hermes profile inspection did not complete.']
        return report.get('problems',[])
    except ValueError:return ['Hermes profile inspection failed; check the interpreter and configuration access.']

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
    found={name:find_agent(name) for name in names}
    if target=='auto':found={name:exe for name,exe in found.items() if exe}
    if not found or any(not exe for exe in found.values()):raise ValueError('Install Claude Code or Hermes first, or run this in the agent’s terminal. Select --agent claude, hermes, or both.')
    return found

def credential_file():
    return Path(os.environ.get('GHL_ENV_FILE') or str(Path(os.environ.get('XDG_CONFIG_HOME') or str(Path.home()/'.config'))/'ghl-super-hub/credentials.env')).expanduser()

def has_credentials():
    values={}
    path=credential_file()
    try:lines=path.read_text().splitlines() if path.is_file() else []
    except OSError:lines=[]
    if lines:
        for line in lines:
            line=line.strip()
            if not line or line.startswith('#') or '=' not in line:continue
            key,value=line.split('=',1);values[key.strip()]=value.strip().strip('"\'')
    for key in ('GHL_API_KEY','GHL_LOCATION_ID'):
        if os.environ.get(key):values[key]=os.environ[key]
    return all(values.get(key,'').strip() and values[key]!='pit-xxxxxxxx' for key in ('GHL_API_KEY','GHL_LOCATION_ID'))

def preflight(args):
    """Read-only inventory; never install, save secrets, or launch an agent."""
    needs=[];found={}
    if sys.platform not in ('darwin','linux'):needs.append({'id':'platform','action':'Use macOS, Linux, Orgo, or a WSL terminal.'})
    if not shutil.which('git'):needs.append({'id':'git','action':'Install Git using your operating system package manager, then retry.'})
    try:found=agents(args.agent)
    except ValueError:
        needs.append({'id':'agent','action':'Install the selected Claude Code or Hermes CLI, or run this in its terminal; then retry. Select --agent claude, hermes, or both.'})
    paths=[Path(os.environ.get('XDG_DATA_HOME') or str(Path.home()/'.local/share'))/'ghl-super-hub',Path.home()/'.local/bin']
    if 'hermes' in found:
        paths.extend([hermes_home(),hermes_home()/'skills'])
        for problem in check_hermes(found['hermes']):needs.append({'id':'hermes_setup','action':problem})
    # Credentials are data files: directory traversal permission is checked on the
    # parent, never execute permission on the file itself (0600 is correct).
    if not args.docs_only and not has_credentials():paths.append(credential_file().parent)
    for path in paths:
        parent=path
        while not parent.exists() and parent!=parent.parent:parent=parent.parent
        if not os.access(parent,os.W_OK|os.X_OK):needs.append({'id':'writable_path','action':'Choose a writable user directory for '+str(path)})
    configured=has_credentials()
    if not configured and not args.docs_only:
        needs.append({'id':'ghl_connection','action':'Provide GHL_API_KEY and GHL_LOCATION_ID through a secure secret tool or hidden terminal prompt, or explicitly choose --docs-only.'})
    return {'status':'needs_input' if needs else 'ready','agents':list(found),'account_configured':configured,'mode':'documentation-only' if args.docs_only else 'connected','needs':needs},found

def terminal_prompt(terminal,message,default=None):
    sys.stderr.write(message);sys.stderr.flush()
    value=terminal.readline()
    if not value:raise EOFError('Setup paused: no input received. Run again in an interactive terminal.')
    return value.strip() or default

def save_connection(token,location):
    if not token or not location or any(c in token+location for c in '\r\n\x00'):raise ValueError('Use a nonempty single-line token and location ID')
    path=credential_file();path.parent.mkdir(parents=True,exist_ok=True,mode=0o700)
    fd,name=tempfile.mkstemp(prefix='.credentials-',dir=path.parent)
    try:
        with os.fdopen(fd,'w') as out:out.write('GHL_API_KEY='+token+'\nGHL_LOCATION_ID='+location+'\n')
        Path(name).replace(path);path.chmod(0o600)
    finally:
        if Path(name).exists():Path(name).unlink()
    # Reuse the same connection during this install; never place secrets in subprocess arguments.
    os.environ['GHL_API_KEY']=token;os.environ['GHL_LOCATION_ID']=location

def prepare(args):
    report,found=preflight(args)
    if args.preflight:
        print(json.dumps(report,indent=2));return None if report['needs'] else found
    if not report['needs']:return found
    if args.non_interactive:
        print(json.dumps(report,indent=2));return None
    try:terminal=open('/dev/tty','r')
    except OSError:
        print(json.dumps(report,indent=2))
        print('Setup needs input before installation. Run in an interactive terminal, or let your agent resolve this checklist using a secure secret tool. Never paste tokens into chat.',file=sys.stderr)
        return None
    with terminal:
        while True:
            report,found=preflight(args)
            if not report['needs']:return found
            print('Before installation:')
            for item in report['needs']:print('- '+item['action'])
            blockers=[item for item in report['needs'] if item['id']!='ghl_connection']
            if blockers:
                answer=terminal_prompt(terminal,'Resolve the items above, then [r]echeck, or [q]uit for now [q]: ','q')
                if answer.lower()!='r':return None
                continue
            choice=terminal_prompt(terminal,'Connect GHL now [c], install documentation only [d], or quit [q]? [c]: ','c').lower()
            if choice=='d':args.docs_only=True;return found
            if choice!='c':return None
            # getpass opens /dev/tty even when this script was downloaded through a pipe.
            # Refuse its echoing fallback: a token must never be visible in a log.
            with warnings.catch_warnings():
                warnings.simplefilter('error',getpass.GetPassWarning)
                token=getpass.getpass('GHL Private Integration / OAuth access token (hidden): ',stream=sys.stderr).strip()
            location=terminal_prompt(terminal,'GHL location / sub-account ID: ','')
            if not token or not location or any(c in token+location for c in '\r\n\x00'):
                print('Both values must be nonempty and single-line. Please try again.');continue
            save_connection(token,location)
            print('Connection saved privately. Token permissions and location access still require a live read.')
            return found

def register(found):
    for name,exe in found.items():
        if name=='claude':
            run([exe,'plugin','marketplace','add',REPO],already_ok=True)
            run([exe,'plugin','install','ghl-super-hub@ghl-super-hub','--scope','user'],already_ok=True)
        else:raise ValueError('Hermes requires register_hermes(root, exe), not the version-dependent plugin manager')

def register_hermes(root,exe):
    python=hermes_python(exe)
    if not python:raise ValueError('Hermes interpreter was unavailable after preflight; set GHL_HERMES_PYTHON and retry')
    run([str(python),str(root/'scripts/hermes_setup.py'),'--home',str(hermes_home()),'--root',str(root),'--credentials',str(credential_file())])

def verify(python):
    messages=[{'jsonrpc':'2.0','id':1,'method':'initialize','params':{'protocolVersion':'2024-11-05','capabilities':{},'clientInfo':{'name':'installer','version':'1'}}},{'jsonrpc':'2.0','id':2,'method':'tools/list'}]
    result=subprocess.run([str(python),'-m','ghl_hub.bootstrap','hub','mcp'],input=''.join(json.dumps(m)+'\n' for m in messages),text=True,capture_output=True,timeout=45,check=True)
    responses=[json.loads(line) for line in result.stdout.splitlines()]
    if len(responses)!=2 or 'serverInfo' not in responses[0].get('result',{}) or len(responses[1].get('result',{}).get('tools',[]))!=6:raise ValueError('MCP verification did not discover all six tools')

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--agent',choices=['auto','claude','hermes','both'],default='auto');parser.add_argument('--version',help='GitHub release tag; default is the latest published release')
    parser.add_argument('--credentials-file',type=Path,help='Existing protected tenant profile (path only; never put a token in arguments)')
    parser.add_argument('--preflight',action='store_true',help='Read-only JSON checklist; exit 2 when input is needed')
    parser.add_argument('--non-interactive',action='store_true',help='Return a checklist instead of prompting when something is missing')
    parser.add_argument('--docs-only',action='store_true',help='Explicitly install local knowledge/tools without an account connection')
    args=parser.parse_args()
    if args.credentials_file:os.environ['GHL_ENV_FILE']=str(args.credentials_file.expanduser().resolve())
    if args.version and not re.fullmatch(r'v\d+\.\d+\.\d+',args.version):raise ValueError('Use a release tag such as v2.2.0')
    found=prepare(args)
    if found is None:return 2
    if args.preflight:return 0
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
    register({name:exe for name,exe in found.items() if name!='hermes'})
    if 'hermes' in found:register_hermes(root,found['hermes'])
    launcher=Path.home()/'.local/bin/ghl';launcher.parent.mkdir(parents=True,exist_ok=True)
    content='#!/bin/sh\n# Managed by ghl-super-hub installer\nexec bash '+shlex.quote(str(root/'ghl'))+' "$@"\n'
    if not launcher.exists() and not launcher.is_symlink() or launcher.is_file() and not launcher.is_symlink() and '# Managed by ghl-super-hub installer' in launcher.read_text():
        launcher.write_text(content);launcher.chmod(0o755)
    else:print('Existing ghl command preserved. CLI: '+str(root/'ghl'))
    print('\nInstalled for '+', '.join(found)+'. Verified all six MCP tools.')
    print('CLI: '+str(root/'ghl'))
    print('Next: start a new agent session, then use the ghl-operator skill.')
    if args.docs_only:print('Documentation-only mode. To connect later: '+shlex.quote(str(root/'ghl'))+' hub connect')
    else:print('GHL connection configured. Verify the intended location with a read before any mutation.')
    print('No GHL data was changed. Agent trust/permission prompts still apply.')

if __name__=='__main__':
    try:sys.exit(main())
    except (EOFError,KeyboardInterrupt):sys.exit('Setup paused. Run again when ready; never share tokens in chat.')
    except Exception as exc:sys.exit('Installation stopped: '+str(exc))
