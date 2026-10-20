#!/usr/bin/env python3
"""Generate auditable API inventory and missing-help manifest from local artifacts."""
from collections import Counter
import json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from ghl_hub import catalog,knowledge

def main():
    operations=catalog.all_operations(); matrix={}
    for op in operations: matrix.setdefault(op['domain'],Counter())[op['method']]+=1
    report=knowledge.refresh_coverage()
    lines=['# Documented API inventory','','Generated from the pinned upstream specs; these are documented operations, not live-tested permissions.','Versioned variants are counted separately. The generic executor supports JSON, URL-encoded forms and multipart uploads.','', '| Domain | GET | POST | PUT | PATCH | DELETE | Total |','| --- | ---: | ---: | ---: | ---: | ---: | ---: |']
    for domain,counts in sorted(matrix.items()): lines.append('| '+domain+' | '+' | '.join(str(counts[k]) for k in ('GET','POST','PUT','PATCH','DELETE'))+' | '+str(sum(counts.values()))+' |')
    lines+=['','For scopes and exact schemas use `ghl hub operations --domain DOMAIN` and `ghl hub schema OPERATION_ID`.','This inventory does not assert dashboard feature completeness. See CAPABILITIES.md and ACCEPTANCE.md.','']
    (knowledge.ROOT/'docs'/'API-INVENTORY.md').write_text('\n'.join(lines))
    print(json.dumps({k:v for k,v in report.items() if k!='missing_urls'},indent=2))
if __name__=='__main__':main()
