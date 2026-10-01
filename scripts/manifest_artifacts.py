"""Fingerprint all retained bytes in the completed next-steps artifact groups."""
import hashlib
import json
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
    groups=list(GROUPS)
    selection=ROOT/'paper/experiment_data.json'
    if selection.exists():
        groups+=json.loads(selection.read_text()).get('artifact_groups',[])
    for group in dict.fromkeys(groups):
        root=ROOT/group
        legacy_fs=group in ('results/diagnostics/graph_n24','results/diagnostics/warm_n24')
        files=sorted(p for p in root.rglob('*') if p.is_file() and p.name!='SHA256SUMS'
                     and (legacy_fs or 'fs' not in p.relative_to(root).parts))
        (root/'SHA256SUMS').write_text(''.join(f'{digest(p)}  {p.relative_to(root)}\n' for p in files))
        print(f'{group}: {len(files)} files')


if __name__=='__main__':main()
