#!/usr/bin/env python3
"""Install portable skill directories without overwriting existing skills implicitly."""
import argparse
from pathlib import Path
import shutil

ROOT=Path(__file__).resolve().parents[1]

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--destination',type=Path,default=Path.home()/'.hermes'/'skills')
    parser.add_argument('--replace',action='store_true',help='Explicitly replace this bundle\'s existing skill directories')
    parser.add_argument('--dry-run',action='store_true')
    args=parser.parse_args(); sources=sorted((ROOT/'skills').glob('ghl-*'))
    for source in sources:
        target=args.destination/source.name
        if target.exists() and not args.replace: parser.error(str(target)+' exists; inspect before using --replace')
    for source in sources:
        target=args.destination/source.name
        print(str(source)+' -> '+str(target))
        if args.dry_run: continue
        if target.exists(): shutil.rmtree(target)
        shutil.copytree(source,target)
        ref=target/'references'/'installation.md'; ref.parent.mkdir(exist_ok=True)
        ref.write_text(f'# Installed HighLevel Hub\n\nCLI: `{ROOT}/ghl`\n\nRepository: `{ROOT}`\n\nUse the absolute CLI path if `ghl` is not on PATH. Keep the repository and its knowledge directory together.\n')
if __name__=='__main__': main()
