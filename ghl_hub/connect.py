"""One-time hidden terminal credential entry; never pass a token as a command argument."""
import json
import os
from pathlib import Path
import tempfile
import click

def credentials_path():
    return Path(os.environ.get('XDG_CONFIG_HOME',str(Path.home()/'.config')))/'ghl-super-hub'/'credentials.env'

def save_credentials(token,location,path=None):
    token=token.strip();location=location.strip()
    if not token or not location or any(c in token+location for c in '\r\n\x00'):raise ValueError('A nonempty, single-line token and location ID are required')
    path=Path(path or credentials_path());path.parent.mkdir(parents=True,exist_ok=True,mode=0o700)
    fd,temp=tempfile.mkstemp(prefix='.credentials-',dir=path.parent)
    try:
        with os.fdopen(fd,'w') as handle:
            handle.write('GHL_API_KEY='+token+'\nGHL_LOCATION_ID='+location+'\n')
        Path(temp).replace(path);path.chmod(0o600)
    finally:
        if Path(temp).exists():Path(temp).unlink()
    return path

@click.command('connect')
@click.option('--credentials-file',type=click.Path(path_type=Path),help='Optional separate protected tenant profile')
def connect_command(credentials_file):
    """Save a GHL token with a hidden terminal prompt; makes no API requests."""
    token=click.prompt('GHL Private Integration or OAuth access token',hide_input=True)
    location=click.prompt('GHL location / sub-account ID')
    try:path=save_credentials(token,location,credentials_file)
    except ValueError as exc:raise click.ClickException(str(exc))
    click.echo('Credentials saved privately to '+str(path))
    click.echo('Reconnect the agent’s MCP tools to load them. No GHL API requests were made.')
