"""Load dotenv as data, never shell code; explicit files support tenant isolation."""
import os
from pathlib import Path
import re
import sys

ROOT=Path(__file__).resolve().parent.parent

def load_env(path,override=False):
    for number,line in enumerate(path.read_text().splitlines(),1):
        line=line.strip()
        if not line or line.startswith('#'): continue
        if line.startswith('export '): line=line[7:]
        key,separator,value=line.partition('=')
        key=key.strip(); value=value.strip()
        if not separator or not re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]*',key): raise ValueError(f'Invalid dotenv entry on line {number}')
        if value.startswith(('"',"'")):
            if len(value)<2 or value[-1]!=value[0]: raise ValueError(f'Unclosed dotenv quote on line {number}')
            value=value[1:-1]
        else: value=value.split(' #',1)[0].rstrip()
        if override or not os.environ.get(key): os.environ[key]=value

def main():
    args=sys.argv[1:]; explicit=None
    if '--env-file' in args:
        index=args.index('--env-file')
        if index+1>=len(args): sys.exit('--env-file requires a path')
        explicit=Path(args[index+1]).expanduser(); del args[index:index+2]
    default=ROOT/'.env'
    if not default.exists(): default=Path(os.environ.get('XDG_CONFIG_HOME',str(Path.home()/'.config')))/'ghl-super-hub'/'credentials.env'
    path=explicit or Path(os.environ.get('GHL_ENV_FILE') or str(default)).expanduser()
    if explicit or os.environ.get('GHL_ENV_FILE'):
        # Prevent accidental token reuse from the parent tenant when a profile omits a key.
        for key in ('GHL_API_KEY','GHL_LOCATION_ID','GHL_FIREBASE_TOKEN','GHL_FIREBASE_REFRESH_TOKEN'): os.environ.pop(key,None)
    if path.exists():
        load_env(path,override=bool(explicit or os.environ.get('GHL_ENV_FILE')))
        if not explicit and not os.environ.get('GHL_ENV_FILE'):
            token=os.environ.get('GHL_API_KEY','')
            shared=Path(os.environ.get('XDG_CONFIG_HOME',str(Path.home()/'.config')))/'ghl-super-hub'/'credentials.env'
            if (not token or token.startswith('pit-xxxxxxxx')) and shared.exists() and shared!=path:load_env(shared,override=True)
    elif explicit or os.environ.get('GHL_ENV_FILE'): sys.exit('Environment file does not exist: '+str(path))
    from cli_anything.gohighlevel.gohighlevel_cli import cli
    cli(args=args,prog_name='ghl')

if __name__=='__main__': main()
