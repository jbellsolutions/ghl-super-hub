"""Discover operations from the official versioned OpenAPI files."""
import json
from .knowledge import DATA

METHODS={'get','post','put','patch','delete','head','options'}

def build():
    operations=[]
    for file in sorted((DATA/'upstream'/'apps').rglob('*.json')):
        spec=json.loads(file.read_text())
        domain=('v3/'+file.stem.removesuffix('-v3')) if file.parent.name=='v3' else file.stem
        for path, item in spec.get('paths',{}).items():
            for method, op in item.items():
                if method not in METHODS: continue
                parameters=item.get('parameters',[])+op.get('parameters',[])
                versions=[p.get('schema',{}).get('enum',['2021-07-28'])[0] for p in parameters if p.get('name','').lower()=='version']
                operations.append(dict(id=domain+':'+op.get('operationId',method+path),domain=domain,method=method.upper(),path=path,summary=op.get('summary',''),description=op.get('description',''),parameters=parameters,requestBody=op.get('requestBody'),security=op.get('security',spec.get('security',[])),version=versions[0] if versions else '2021-07-28',source=str(file.relative_to(DATA)),servers=spec.get('servers',[])))
    (DATA/'operations.json').write_text(json.dumps(operations,indent=2)); return len(operations)

def all_operations():
    p=DATA/'operations.json'
    if not p.exists(): build()
    return json.loads(p.read_text())

def find(query='',domain=None):
    terms=query.lower().split()
    return [o for o in all_operations() if (domain is None or o['domain']==domain) and all(t in (o['id']+' '+o['path']+' '+o['summary']).lower() for t in terms)]

def get(operation_id):
    matches=[o for o in all_operations() if o['id']==operation_id]
    if len(matches)!=1: raise ValueError('Unknown operation ID. Search with: ghl hub operations QUERY')
    return matches[0]

def schema(operation_id):
    op=get(operation_id); spec=json.loads((DATA/op['source']).read_text())
    original=spec['paths'][op['path']][op['method'].lower()]
    operation={**op,'responses':original.get('responses',{}),'externalDocs':original.get('externalDocs',{})}
    # Return only reachable schemas so a single operation does not load an entire API manual.
    schemas={}; pending=[operation]; seen=set()
    while pending:
        node=pending.pop()
        if isinstance(node,list): pending.extend(node)
        elif isinstance(node,dict):
            ref=node.get('$ref','')
            if ref.startswith('#/components/schemas/') and ref not in seen:
                seen.add(ref); name=ref.rsplit('/',1)[-1]
                if name in spec.get('components',{}).get('schemas',{}):
                    schemas[name]=spec['components']['schemas'][name]; pending.append(schemas[name])
            pending.extend(node.values())
    return dict(operation=operation,components=dict(schemas=schemas,securitySchemes=spec.get('components',{}).get('securitySchemes',{})),external_reference_base=str((DATA/op['source']).parent))
