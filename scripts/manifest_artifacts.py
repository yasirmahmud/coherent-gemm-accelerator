"""Fingerprint all retained bytes in the completed next-steps artifact groups."""
import hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
GROUPS=('results/diagnostics/graph_n24','results/diagnostics/warm_n24',
        'results/provenance/historical_20260930','results/analysis','paper')


def digest(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for data in iter(lambda:f.read(1024*1024),b''):h.update(data)
    return h.hexdigest()


def main():
    for group in GROUPS:
        root=ROOT/group
        files=sorted(p for p in root.rglob('*') if p.is_file() and p.name!='SHA256SUMS')
        (root/'SHA256SUMS').write_text(''.join(f'{digest(p)}  {p.relative_to(root)}\n' for p in files))
        print(f'{group}: {len(files)} files')


if __name__=='__main__':main()
