#!/usr/bin/env python3
"""Prepare a persistent sidecar runtime, then launch the CLI/MCP without stdout noise."""
import fcntl
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]

def fingerprint(root):
    digest=hashlib.sha256()
    paths=[root/'setup.py',root/'scripts/plugin_runtime.py',root/'scripts/python-run.sh']
    for folder in ['ghl_hub','cli_anything/gohighlevel']:
        paths.extend(sorted((root/folder).rglob('*.py')))
    for p in paths:
        digest.update(p.relative_to(root).as_posix().encode());digest.update(p.read_bytes())
    digest.update((root/'knowledge/operations.json').read_bytes())
    return digest.hexdigest()

def snapshot(root,destination):
    destination.mkdir(parents=True,exist_ok=True)
    shutil.copy2(root/'setup.py',destination/'setup.py')
    for folder in ['ghl_hub','cli_anything']:
        shutil.copytree(root/folder,destination/folder,dirs_exist_ok=True,ignore=shutil.ignore_patterns('__pycache__','*.pyc','*.egg-info'))
    return destination

def data_home():return Path(os.environ.get('XDG_DATA_HOME',str(Path.home()/'.local/share')))/'ghl-super-hub'

def prepare(root=ROOT):
    root=Path(root).resolve();signature=fingerprint(root)
    shared=data_home()/'releases'
    # The one-command installer prewarms a verified release. Native plugins can reuse it.
    if shared.exists():
        for candidate in sorted(shared.iterdir(),reverse=True):
            marker=candidate/'.ghl-runtime.json';python=candidate/'.venv/bin/python'
            if marker.is_file() and python.is_file():
                saved=json.loads(marker.read_text())
                if saved.get('fingerprint')==signature:return python,candidate/'knowledge'
    local=root/'.venv/bin/python'
    if local.is_file() and not (root/'.claude-plugin').exists():return local,root/'knowledge'
    runtime=data_home()/'runtimes'/signature[:20];runtime.mkdir(parents=True,exist_ok=True)
    with (runtime/'install.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX)
        python=runtime/'.venv/bin/python';ready=runtime/'ready.json'
        if not python.is_file() or not ready.is_file():
            print('Preparing the HighLevel runtime (first run only)…',file=sys.stderr,flush=True)
            subprocess.run([sys.executable,'-m','venv',str(runtime/'.venv')],check=True,stdout=sys.stderr)
            source=snapshot(root,runtime/'source')
            subprocess.run([str(python),'-m','pip','install','--quiet','-e',str(source)],check=True,stdout=sys.stderr)
            if not (runtime/'knowledge').exists():
                shutil.copytree(root/'knowledge',runtime/'knowledge',ignore=shutil.ignore_patterns('*.sqlite3','*.sqlite3-*','*.tmp'))
            ready.write_text(json.dumps({'fingerprint':signature,'source':str(root)}))
        return python,runtime/'knowledge'

def main():
    python,knowledge=prepare()
    env={**os.environ,'GHL_KNOWLEDGE_DIR':str(knowledge)}
    os.execve(str(python),[str(python),'-m','ghl_hub.bootstrap',*sys.argv[1:]],env)

if __name__=='__main__':main()
