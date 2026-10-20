"""Prepare documented operations, validate required inputs, and execute explicitly."""
import json
import os
from pathlib import Path
import re
from urllib.parse import quote
from . import catalog, transport
from .knowledge import DATA

def resolve_context(node, spec, source, seen=None):
    seen=set() if seen is None else seen
    if not isinstance(node,dict) or '$ref' not in node: return node,spec,source
    ref=node['$ref']
    if ref in seen: return node,spec,source
    seen.add(ref); file,_,pointer=ref.partition('#')
    if file:
        path=(source.parent/file).resolve()
        if not path.is_relative_to((DATA/'upstream').resolve()): raise ValueError('Schema reference outside API archive')
        spec=json.loads(path.read_text()); source=path
    value=spec
    for part in pointer.strip('/').split('/') if pointer.strip('/') else []: value=value[part.replace('~1','/').replace('~0','~')]
    return resolve_context(value,spec,source,seen)

def resolve(node,spec,source):
    return resolve_context(node,spec,source)[0]

def validate(value,schema,spec,source,label='body',depth=0):
    if depth>30: return
    schema,spec,source=resolve_context(schema,spec,source)
    if not isinstance(schema,dict): return
    for sub in schema.get('allOf',[]): validate(value,sub,spec,source,label,depth+1)
    if value is None and schema.get('nullable'): return
    types={'object':dict,'array':list,'string':str,'integer':int,'number':(int,float),'boolean':bool}
    kind=schema.get('type')
    if kind in types and (not isinstance(value,types[kind]) or (kind in ('integer','number') and isinstance(value,bool))): raise ValueError(label+' must be '+kind)
    if 'enum' in schema and value not in schema['enum']: raise ValueError(label+' must be one of '+str(schema['enum']))
    if isinstance(value,dict):
        for key in schema.get('required',[]):
            if key not in value: raise ValueError(label+'.'+key+' is required')
        for key,sub in schema.get('properties',{}).items():
            if key in value: validate(value[key],sub,spec,source,label+'.'+key,depth+1)
    if isinstance(value,list) and 'items' in schema:
        for i,item in enumerate(value): validate(item,schema['items'],spec,source,f'{label}[{i}]',depth+1)

def prepare(operation_id,path_params=None,query=None,body=None,files=None,location_id=None):
    if path_params is not None and not isinstance(path_params,dict): raise ValueError('path_params must be an object')
    if query is not None and not isinstance(query,dict): raise ValueError('query must be an object')
    if files is not None and not isinstance(files,dict): raise ValueError('files must be an object')
    op=catalog.get(operation_id); path_params=dict(path_params or {}); query=dict(query or {})
    source=DATA/op['source']; spec=json.loads(source.read_text()); path=op['path']
    for param in op['parameters']:
        param=resolve(param,spec,source); name=param['name']; where=param['in']
        values=path_params if where=='path' else query if where=='query' else None
        if values is None: continue
        if name=='locationId' and name not in values and (location_id or os.environ.get('GHL_LOCATION_ID')): values[name]=location_id or os.environ['GHL_LOCATION_ID']
        if param.get('required') and name not in values: raise ValueError(f'Required {where} parameter: {name}')
        if name in values: validate(values[name],param.get('schema',{}),spec,source,f'{where}.{name}')
    for key in re.findall(r'\{([^}]+)\}',path):
        if key not in path_params: raise ValueError('Required path parameter: '+key)
        if not str(path_params[key]): raise ValueError('Empty path parameter: '+key)
        path=path.replace('{'+key+'}',quote(str(path_params[key]),safe=''))
    transport.validate_path(path)
    request_body=resolve(op.get('requestBody') or {},spec,source)
    if request_body.get('required') and body is None and not files: raise ValueError('Request body is required')
    content=request_body.get('content',{}); content_type='application/json'
    if content and content_type not in content: content_type=next(iter(content))
    if content_type not in ('application/json','application/x-www-form-urlencoded','multipart/form-data'): raise ValueError('Unsupported content type: '+content_type)
    if files and content_type!='multipart/form-data': raise ValueError('Files require a documented multipart operation')
    file_paths={}
    for key,paths in (files or {}).items():
        if not isinstance(paths,(str,list)) or (isinstance(paths,list) and not all(isinstance(p,str) for p in paths)): raise ValueError('Each files value must be a path string or a list of path strings')
        entries=paths if isinstance(paths,list) else [paths]
        if not entries: raise ValueError('File list cannot be empty')
        file_paths[key]=[]
        for entry in entries:
            path_file=Path(entry).expanduser().resolve()
            if not path_file.is_file(): raise ValueError('Upload file does not exist: '+entry)
            file_paths[key].append(str(path_file))
    if content_type=='multipart/form-data' and not isinstance(body or {},dict): raise ValueError('Multipart body must be an object')
    validation_body=body
    if file_paths:
        if body is not None and not isinstance(body,dict): raise ValueError('Multipart body must be an object')
        validation_body=dict(body or {})
        for key,paths in file_paths.items():
            if key in validation_body: raise ValueError('Field supplied in both body and files: '+key)
            validation_body[key]=[Path(p).name for p in paths] if isinstance(files[key],list) else Path(paths[0]).name
    if validation_body is not None:
        if not request_body: raise ValueError('This operation does not document a request body')
        validate(validation_body,content.get(content_type,{}).get('schema',{}),spec,source)
    return dict(operation=operation_id,method=op['method'],path=path,query=query,body=body,version=op['version'],content_type=content_type,files=file_paths,auth_required=bool(op['security']) or any(p.get('in')=='header' and p.get('name','').lower()=='authorization' for p in op['parameters']))

def call(operation_id,path_params=None,query=None,body=None,execute=False,files=None,location_id=None):
    plan=prepare(operation_id,path_params,query,body,files,location_id)
    if not execute: return dict(dry_run=True,request=plan)
    result=transport.request(plan['method'],plan['path'],params=plan['query'],body=plan['body'],version=plan['version'],content_type=plan['content_type'],files=plan['files'],auth_required=plan['auth_required'])
    return dict(dry_run=False,result=result)
