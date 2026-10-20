#!/usr/bin/env python3
"""Compatibility installer for Hermes skills + its documented mcp_servers config.

Run with Hermes's Python (which already supplies PyYAML), never install a dependency
into the agent. No agent process is launched and no credential values are serialized.
"""
import argparse
import fcntl
import json
import os
from pathlib import Path
import shutil
import tempfile
import time

OWNER='jbellsolutions/ghl-super-hub'
SKILLS=('operator','api','browser','workflows','sites','email','affiliates','memberships','courses')
SERVER='ghl-super-hub'

def load_profile(home,load):
    config=home/'config.yaml'
    try:data=load(config.read_text()) if config.exists() else {}
    except Exception:raise ValueError('Hermes config.yaml could not be parsed. Fix its YAML before installing; its contents were not logged.') from None
    if data is None:data={}
    if not isinstance(data,dict) or not isinstance(data.get('mcp_servers',{}),dict):raise ValueError('Hermes config and mcp_servers must be mappings.')
    return data

def inspect_profile(home,load):
    problems=[]
    try:data=load_profile(home,load)
    except ValueError as exc:return [str(exc)]
    receipt=home/'.ghl-super-hub-install.json'
    try:owned=json.loads(receipt.read_text()) if receipt.is_file() else {}
    except (ValueError,OSError):owned={}
    current=data.get('mcp_servers',{}).get(SERVER)
    if current is not None and (owned.get('owner')!=OWNER or current!=owned.get('server')):
        problems.append('Existing mcp_servers.ghl-super-hub is not managed by this installer or was customized; preserve/review it before installing.')
    for name in SKILLS:
        path=home/'skills'/('ghl-'+name)
        if not path.exists() and not path.is_symlink():continue
        stamp=path/'.ghl-super-hub.json'
        try:managed=json.loads(stamp.read_text()).get('owner')==OWNER
        except (ValueError,OSError):managed=False
        if path.is_symlink() or not managed:problems.append('Existing skill '+str(path)+' is not managed by this installer; preserve/review it first.')
    return problems

def write_private(path,content):
    path.parent.mkdir(parents=True,exist_ok=True,mode=0o700)
    fd,name=tempfile.mkstemp(prefix='.ghl-write-',dir=path.parent)
    try:
        with os.fdopen(fd,'w') as handle:handle.write(content)
        Path(name).replace(path)  # mkstemp mode 0600; no permissive-file window
    finally:
        if Path(name).exists():Path(name).unlink()

def configure(root,home,credentials,load,dump):
    home.mkdir(parents=True,exist_ok=True,mode=0o700)
    with open(home/'.ghl-super-hub-install.lock','a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX)
        problems=inspect_profile(home,load)
        if problems:raise ValueError('\n'.join(problems))
        data=load_profile(home,load)
        env={}
        # A protected file pins the tenant without copying token values into config.
        if credentials.is_file():env['GHL_ENV_FILE']=str(credentials)
        else:env['XDG_CONFIG_HOME']=str(credentials.parent.parent)
        server={'command':str(root/'ghl'),'args':['hub','mcp'],'env':env}
        data.setdefault('mcp_servers',{})[SERVER]=server
        config=home/'config.yaml';before=config.read_text() if config.exists() else None
        encoded=dump(data)
        backup=None
        if before is not None and before!=encoded:
            backup=home/('config.yaml.ghl-backup-'+str(time.time_ns()))
            write_private(backup,before)
        # Validate/stage every skill before publishing any of them.
        skills=home/'skills';skills.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(prefix='.ghl-staging-',dir=home) as staging:
            for name in SKILLS:
                source=root/'skills'/('ghl-'+name)
                if not (source/'SKILL.md').is_file():raise ValueError('Release is missing skill '+name)
                target=Path(staging)/source.name;shutil.copytree(source,target)
                (target/'.ghl-super-hub.json').write_text(json.dumps({'owner':OWNER}))
                ref=target/'references/installation.md'
                ref.write_text(ref.read_text()+'\nInstalled CLI: `'+str(root/'ghl')+'`\n')
            for name in SKILLS:
                target=skills/('ghl-'+name)
                if target.exists():shutil.rmtree(target)  # only installer-owned paths passed inspection
                (Path(staging)/target.name).rename(target)
        write_private(config,encoded)
        write_private(home/'.ghl-super-hub-install.json',json.dumps({'owner':OWNER,'server':server}))
        # Read back the actual config and discoverable skill paths, not just the staging data.
        if load_profile(home,load).get('mcp_servers',{}).get(SERVER)!=server:raise ValueError('Hermes MCP configuration readback failed')
        if any(not (skills/('ghl-'+name)/'SKILL.md').is_file() for name in SKILLS):raise ValueError('Hermes skill discovery paths are incomplete')
        return {'status':'configured','skills':len(SKILLS),'server':SERVER,'config':str(config),'backup':str(backup) if backup else None}

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check',action='store_true');parser.add_argument('--home',required=True,type=Path)
    parser.add_argument('--root',type=Path);parser.add_argument('--credentials',type=Path)
    args=parser.parse_args()
    try:
        import yaml  # supplied by the existing Hermes environment
        if args.check:
            problems=inspect_profile(args.home,yaml.safe_load)
            print(json.dumps({'status':'needs_input' if problems else 'ready','problems':problems}));return 2 if problems else 0
        result=configure(args.root,args.home,args.credentials,yaml.safe_load,lambda data:yaml.safe_dump(data,sort_keys=False))
        print(json.dumps(result));return 0
    except ImportError:
        print(json.dumps({'status':'needs_input','problems':['Use the Hermes Python interpreter with its existing PyYAML dependency; set GHL_HERMES_PYTHON.']}));return 2
    except ValueError as exc:
        print(json.dumps({'status':'needs_input','problems':[str(exc)]}));return 2

if __name__=='__main__':raise SystemExit(main())
