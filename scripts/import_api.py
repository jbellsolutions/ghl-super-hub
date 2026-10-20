#!/usr/bin/env python3
"""Pin and archive official API sources, then generate the operation catalog."""
import io
import json
from pathlib import Path
import sys
import zipfile
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from ghl_hub.knowledge import DATA, fetch, rebuild

def main():
    DATA.mkdir(exist_ok=True)
    meta=json.loads(fetch('https://api.github.com/repos/GoHighLevel/highlevel-api-docs/commits/main'))
    sha=meta['sha']; archive=fetch('https://codeload.github.com/GoHighLevel/highlevel-api-docs/zip/'+sha)
    count=0
    with zipfile.ZipFile(io.BytesIO(archive)) as z:
        for name in z.namelist():
            p=Path(*Path(name).parts[1:])
            if '..' in p.parts or name.endswith('/'): continue
            if p.suffix not in ('.json','.md') and str(p) != 'LICENSE': continue
            if not (str(p).startswith(('apps/','docs/','common/')) or str(p) in ('LICENSE','README.md')): continue
            out=DATA/'upstream'/p; out.parent.mkdir(parents=True,exist_ok=True); out.write_bytes(z.read(name)); count+=1
    (DATA/'api-source.json').write_text(json.dumps(dict(repository='https://github.com/GoHighLevel/highlevel-api-docs',revision=sha,files=count),indent=2))
    from ghl_hub.catalog import build
    print(json.dumps(dict(source_files=count,operations=build(),indexed=rebuild())))
if __name__=='__main__': main()
