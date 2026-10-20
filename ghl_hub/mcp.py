"""Small stdio MCP server (JSON-RPC, newline framing, no SDK dependency)."""
import json
import sys
from . import catalog, knowledge
from .executor import call

TOOLS=[
 dict(name='ghl_operations',description='Search documented HighLevel API operations and scopes.',inputSchema=dict(type='object',properties=dict(query=dict(type='string'),domain=dict(type='string')),additionalProperties=False)),
 dict(name='ghl_schema',description='Read operation parameters, request schema, security and component schemas.',inputSchema=dict(type='object',properties=dict(operation_id=dict(type='string')),required=['operation_id'],additionalProperties=False)),
 dict(name='ghl_call',description='Prepare or execute a documented HighLevel API request. execute defaults false; inspect a plan before writes. Does not bypass account permissions.',inputSchema=dict(type='object',properties=dict(operation_id=dict(type='string'),path_params=dict(type='object'),query=dict(type='object'),body={},files=dict(type='object'),execute=dict(type='boolean',default=False)),required=['operation_id'],additionalProperties=False)),
 dict(name='ghl_docs_search',description='Search archived official help and API documentation.',inputSchema=dict(type='object',properties=dict(query=dict(type='string'),limit=dict(type='integer',minimum=1,maximum=50)),required=['query'],additionalProperties=False)),
 dict(name='ghl_docs_read',description='Read a locally archived help article by numeric article ID.',inputSchema=dict(type='object',properties=dict(article_id=dict(type='string',pattern='^[0-9]+$')),required=['article_id'],additionalProperties=False)),
 dict(name='ghl_doctor',description='Report local configuration and coverage without disclosing tokens or making live API calls.',inputSchema=dict(type='object',properties={},additionalProperties=False))
]

def invoke(name,args):
    if not isinstance(args,dict): raise ValueError('arguments must be an object')
    tool=next((t for t in TOOLS if t['name']==name),None)
    if tool is None: raise ValueError('Unknown tool')
    schema=tool['inputSchema']
    if set(args)-set(schema['properties']): raise ValueError('Unknown arguments')
    for key in schema.get('required',[]):
        if key not in args: raise ValueError('Missing argument: '+key)
    for key,value in args.items():
        kind=schema['properties'][key].get('type')
        expected={'string':str,'integer':int,'boolean':bool,'object':dict}.get(kind)
        if expected and (not isinstance(value,expected) or (kind=='integer' and isinstance(value,bool))): raise ValueError('Invalid argument type: '+key)
    if name=='ghl_operations':
        rows=catalog.find(**args); return {'total':len(rows),'operations':rows[:50]}
    if name=='ghl_schema': return catalog.schema(**args)
    if name=='ghl_call': return call(**args)
    if name=='ghl_docs_search': return knowledge.search(**args)
    if name=='ghl_docs_read':
        article_id=args['article_id']
        if not article_id.isdigit(): raise ValueError('Numeric article ID required')
        return json.loads((knowledge.DATA/'articles'/(article_id+'.json')).read_text())
    if name=='ghl_doctor':
        from .cli import doctor
        return doctor()

def dispatch(message):
    if not isinstance(message,dict) or message.get('jsonrpc')!='2.0': return dict(jsonrpc='2.0',id=None,error=dict(code=-32600,message='Invalid Request'))
    method=message.get('method'); identifier=message.get('id')
    if method=='initialize':
        version=message.get('params',{}).get('protocolVersion')
        result=dict(protocolVersion=version if version in ('2024-11-05','2025-03-26','2025-06-18') else '2024-11-05',capabilities={'tools':{'listChanged':False}},serverInfo={'name':'ghl-super-hub','version':'2.2.0'})
    elif method=='ping': result={}
    elif method=='tools/list': result={'tools':TOOLS}
    elif method=='tools/call':
        try:
            params=message.get('params',{}); value=invoke(params.get('name'),params.get('arguments',{}))
            result={'content':[{'type':'text','text':json.dumps(value,ensure_ascii=False)}],'isError':False}
        except Exception as exc:
            # Avoid URLs, headers, or provider bodies in tool errors, which can contain credentials.
            import requests
            error='API request failed'
            if isinstance(exc,requests.HTTPError): error+=' (HTTP '+str(exc.response.status_code)+')'
            elif isinstance(exc,(ValueError,KeyError,FileNotFoundError)): error=str(exc)
            result={'content':[{'type':'text','text':error}],'isError':True}
    elif method and method.startswith('notifications/'): return None
    else: return dict(jsonrpc='2.0',id=identifier,error=dict(code=-32601,message='Method not found')) if 'id' in message else None
    return dict(jsonrpc='2.0',id=identifier,result=result) if 'id' in message else None

def main():
    for line in sys.stdin:
        try: response=dispatch(json.loads(line))
        except Exception: response=dict(jsonrpc='2.0',id=None,error=dict(code=-32700,message='Parse error'))
        if response is not None: print(json.dumps(response,ensure_ascii=False),flush=True)

if __name__=='__main__': main()
