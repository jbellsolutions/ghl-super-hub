import json
import os
from pathlib import Path
import click
from . import catalog, knowledge
from .executor import call

def output(data): click.echo(json.dumps(data,indent=2,ensure_ascii=False,default=str))

def doctor():
    report={'token_configured':bool(os.environ.get('GHL_API_KEY')) and not os.environ.get('GHL_API_KEY','').startswith('pit-xxxxxxxx'), 'location_configured':bool(os.environ.get('GHL_LOCATION_ID')) and os.environ.get('GHL_LOCATION_ID')!='YOUR_LOCATION_ID','api_operations':len(catalog.all_operations()),'knowledge_index':(knowledge.DATA/'search.sqlite3').exists(),'live_account_verified':False}
    status=knowledge.DATA/'help-status.json'
    if status.exists(): report['help_archive']=json.loads(status.read_text())
    else: report['help_archive']={'complete':False}
    return report

@click.group()
def hub():
    """API discovery, knowledge search, MCP, and account diagnostics."""

@hub.command('doctor')
def doctor_command(): output(doctor())

@hub.command('operations')
@click.argument('query',default='')
@click.option('--domain')
@click.option('--limit',default=30,type=click.IntRange(1,1000))
def operations_command(query,domain,limit):
    rows=catalog.find(query,domain); output(dict(total=len(rows),operations=[{k:o[k] for k in ('id','method','path','summary','security')} for o in rows[:limit]]))

@hub.command('schema')
@click.argument('operation_id')
def schema_command(operation_id):
    try: output(catalog.schema(operation_id))
    except ValueError as exc: raise click.ClickException(str(exc))

@hub.command('call')
@click.argument('operation_id')
@click.option('--path', 'path_json',default='{}',help='JSON object with path parameters')
@click.option('--query',default='{}',help='JSON object with query parameters')
@click.option('--body',default=None,help='JSON body or @filename')
@click.option('--files',default='{}',help='Multipart file fields as JSON: field to path or list of paths')
@click.pass_context
@click.option('--execute',is_flag=True,help='Send the prepared request. Default only prints the plan.')
def call_command(ctx,operation_id,path_json,query,body,execute,files):
    try:
        data=json.loads(Path(body[1:]).read_text() if body.startswith('@') else body) if body is not None else None
        output(call(operation_id,json.loads(path_json),json.loads(query),data,execute,files=json.loads(files),location_id=ctx.find_root().obj.get("location_id")))
    except Exception as exc:
        from cli_anything.gohighlevel.gohighlevel_cli import _handle_error
        _handle_error(exc)

@hub.group('docs')
def docs_command(): """Search, read, refresh, and inspect the official documentation archive."""

@docs_command.command('search')
@click.argument('query')
@click.option('--limit',default=8,type=click.IntRange(1,50))
def search_command(query,limit): output(knowledge.search(query,limit))

@docs_command.command('read')
@click.argument('article_id')
def read_command(article_id):
    if not article_id.isdigit(): raise click.ClickException('Use the numeric article ID from a search result URL')
    p=knowledge.DATA/'articles'/(article_id+'.json')
    if not p.exists(): raise click.ClickException('Article is not archived')
    output(json.loads(p.read_text()))

@docs_command.command('sync')
@click.option('--workers',default=6,type=click.IntRange(1,8))
@click.option('--limit',type=click.IntRange(1))
@click.option('--refresh',is_flag=True)
def sync_command(workers,limit,refresh): output(knowledge.sync_help(workers,limit,refresh))

@docs_command.command('reindex')
def reindex_command(): output({'indexed':knowledge.rebuild()})

@hub.command('mcp')
def mcp_command():
    from .mcp import main
    main()
