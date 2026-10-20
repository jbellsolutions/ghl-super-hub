#!/usr/bin/env python3
"""Build a portable checkout archive from an explicit, secret-free allowlist."""
from pathlib import Path
import zipfile
ROOT=Path(__file__).resolve().parents[1]
TOP={'README.md','setup.py','install.sh','ghl','.env.example','.gitignore'}
TREES={'ghl_hub','cli_anything','skills','scripts','tests','config','knowledge','site','.github'}
DOCS={'INSTALL.md','INTEGRATIONS.md','ACCEPTANCE.md','CAPABILITIES.md','API-INVENTORY.md','BUILD-STATUS.md','SOURCES.md','SHARING.md'}

def main():
    output=ROOT/'dist'/'ghl-super-hub.zip';output.parent.mkdir(exist_ok=True)
    with zipfile.ZipFile(output,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as archive:
        for p in sorted(ROOT.rglob('*')):
            rel=p.relative_to(ROOT)
            if not p.is_file() or p.is_symlink(): continue
            if any(part in {'.venv','.git','.cloudroom','__pycache__','.pytest_cache','dist'} or part.endswith('.egg-info') for part in rel.parts): continue
            if p.name.startswith('.env') and rel.as_posix()!='.env.example': continue
            include=rel.as_posix() in TOP or rel.parts[0] in TREES or (rel.parts[0]=='docs' and (p.name in DOCS or 'assets' in rel.parts))
            if not include or p.suffix in {'.pyc','.tmp','.log'}:continue
            # Personalized account examples are not generic deployment resources.
            if rel.parts[0]=='cli_anything' and 'skills' in rel.parts: continue
            archive.write(p,Path('ghl-super-hub')/rel)
    print(output)
    print(f'{output.stat().st_size:,} bytes')
if __name__=='__main__':main()
