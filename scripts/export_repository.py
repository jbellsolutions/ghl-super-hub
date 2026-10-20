#!/usr/bin/env python3
"""Export the portable bundle into a fresh Git checkout without private workspace history."""
import argparse
from pathlib import Path
import zipfile
ROOT=Path(__file__).resolve().parents[1]

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('destination',type=Path)
    args=parser.parse_args();destination=args.destination.resolve()
    if destination.exists() and any(destination.iterdir()):parser.error('Destination must be new or empty; existing files are never overwritten')
    archive=ROOT/'dist'/'ghl-super-hub.zip'
    if not archive.is_file():parser.error('Run python scripts/build_bundle.py first')
    destination.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(archive) as z:
        for item in z.infolist():
            rel=Path(*Path(item.filename).parts[1:])
            if not rel.parts or '..' in rel.parts or rel.is_absolute():raise ValueError('Invalid archive member')
            out=destination/rel
            if item.is_dir():out.mkdir(parents=True,exist_ok=True)
            else:
                out.parent.mkdir(parents=True,exist_ok=True);out.write_bytes(z.read(item))
                mode=item.external_attr>>16
                if mode:out.chmod(mode & 0o777)
    print(destination)
if __name__=='__main__':main()
