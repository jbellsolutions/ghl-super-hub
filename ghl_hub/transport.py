"""Bounded, fixed-origin API transport; mutations are never automatically replayed."""
from contextlib import ExitStack
import json
import mimetypes
from pathlib import Path
import os
import re
import time
from urllib.parse import urlsplit
import requests

BASE_URL='https://services.leadconnectorhq.com'

def validate_path(path):
    parsed=urlsplit(path)
    if not path.startswith('/') or path.startswith('//') or parsed.scheme or parsed.netloc or parsed.query or parsed.fragment or '\\' in path or any(x in path.lower() for x in ('..','%2e','%2f','%5c','\r','\n')):
        raise ValueError('Use an API path on services.leadconnectorhq.com without query strings or traversal')

def request(method,path,params=None,body=None,version='2021-07-28',content_type='application/json',files=None,auth_required=True):
    validate_path(path)
    token=os.environ.get('GHL_API_KEY','').strip()
    if auth_required and (not token or token.startswith('pit-xxxxxxxx')): raise ValueError('Configure GHL_API_KEY with a real Private Integration or OAuth access token')
    headers={'Version':version,'Accept':'application/json'}
    if auth_required: headers['Authorization']='Bearer '+token
    options=dict(headers=headers,params=params,timeout=(10,60),allow_redirects=False)
    if content_type=='multipart/form-data':
        fields={k:json.dumps(v) if isinstance(v,(bool,dict,list)) else str(v) for k,v in (body or {}).items()}
        with ExitStack() as stack:
            parts=[]
            for key,paths in (files or {}).items():
                for path_file in paths:
                    p=Path(path_file); handle=stack.enter_context(p.open('rb'))
                    parts.append((key,(p.name,handle,mimetypes.guess_type(p.name)[0] or 'application/octet-stream')))
            # requests must set the multipart boundary itself; None parts encode fields without files.
            parts.extend((key,(None,value)) for key,value in fields.items())
            if not parts: raise ValueError('Multipart request needs body fields or files')
            options['files']=parts
            response=requests.request(method,BASE_URL+path,**options)
            return decode(response)
    if body is not None:
        if content_type=='application/x-www-form-urlencoded': options['data']=body
        else: options['json']=body
    for attempt in range(4):
        response=requests.request(method,BASE_URL+path,**options)
        if method in ('GET','HEAD') and response.status_code in (429,502,503,504) and attempt<3:
            delay=response.headers.get('Retry-After','')
            time.sleep(min(30,float(delay)) if re.fullmatch(r'\d+(\.\d+)?',delay) else 2**attempt)
            continue
        return decode(response)

def decode(response):
    if 300<=response.status_code<400: raise ValueError('API redirect refused; check the documented operation path')
    response.raise_for_status()
    if not response.content: return {'statusCode':response.status_code}
    try: return response.json()
    except ValueError: return {'statusCode':response.status_code,'text':response.text}
