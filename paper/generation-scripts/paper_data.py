"""Resolve the paper's explicitly selected experiment files."""
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


def data_paths():
    selection=ROOT/'paper/experiment_data.json'
    if not selection.exists(): raise ValueError('Validate and select a fresh paper suite first')
    data=json.loads(selection.read_text())
    if data.get('status')!='validated': raise ValueError('Paper experiment suite is not validated')
    paths={name:ROOT/path for name,path in data['files'].items()}
    for name,path in paths.items():
        if not path.is_file(): raise ValueError('Missing paper data: '+name+' '+str(path))
    return paths
