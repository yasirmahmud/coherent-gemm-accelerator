"""Validate fresh paper evidence and select only that suite for paper generation."""
import argparse
import csv
import gzip
import hashlib
import json
from pathlib import Path
import subprocess
import sys
from summarize_cache_bandwidth import verify, write_summary
from summarize_repeated import validate_run, per_call_correctness, invocation_blocks, interval_ticks

ROOT=Path(__file__).resolve().parents[1]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('suite',type=Path)
    args=parser.parse_args();suite=args.suite.resolve()
    run=json.loads((suite/'run.json').read_text())
    if run.get('status')!='complete' or len(run['jobs'])!=25 or any(j.get('exit_code')!=0 for j in run['jobs'].values()):
        raise ValueError('Paper experiment jobs are incomplete or failed')
    paths={name:ROOT/run[name] for name in ('main','graph','warm','bandwidth','negative')}
    analysis=suite/'analysis'
    subprocess.run([sys.executable,str(ROOT/'scripts/summarize_widths.py'),'--main',str(paths['main']),
                    '--out',str(analysis)],check=True)
    subprocess.run([sys.executable,str(ROOT/'scripts/summarize_graph_diagnostic.py'),str(paths['graph'])],check=True)
    subprocess.run([sys.executable,str(ROOT/'scripts/summarize_warm_diagnostic.py'),str(paths['warm'])],check=True)
    bandwidth=verify(paths['bandwidth']);write_summary(paths['bandwidth'],bandwidth)
    subprocess.run([sys.executable,str(ROOT/'scripts/analyze_cache_counters.py'),'--cohort',str(paths['bandwidth']),
                    '--out',str(analysis/'cache')],check=True)
    negatives=[]
    for width,variant in ((1,'base'),(2,'tiled2'),(4,'tiled4')):
        point=paths['negative']/variant
        log=(point/'gem5-accel.log').read_text()
        records=per_call_correctness(log)
        try:
            validate_run(point,3)
            outcome='passed'
        except ValueError as error:
            if not str(error).startswith('Failed correctness:'): raise
            outcome='rejected for incorrect output'
        if digest(point/'guest')!=(point/'binary.sha256').read_text().split()[0]:
            raise ValueError('Independent-mutation guest identity mismatch')
        with gzip.open(point/'dynamic_trace.gz','rb') as f: logical=hashlib.sha256(f.read()).hexdigest()
        if logical!=(point/'logical-trace.sha256').read_text().split()[0]:
            raise ValueError('Independent-mutation logical trace mismatch')
        negatives.append(dict(width=width,outcome=outcome,expected_calls=3,
                              mismatch_counts=[m for _,m in records],raw=str(point.relative_to(ROOT))))
    (analysis/'independent_mutation.json').write_text(json.dumps(negatives,indent=2)+'\n')
    # Reconcile actual raw invocations against the runner's intended experiment grid.
    commands=sum(len(list(path.rglob('command*.txt'))) for path in paths.values())
    if commands!=107: raise ValueError('Expected 107 retained simulator commands; got '+str(commands))
    report=dict(status='validated',simulator_processes=commands,main_points=12,
                sizes=[8,16,24,32],widths=[1,2,4],bandwidth_points=6,
                graph_pairs=6,warm_pairs=6,independent_mutation_runs=3,
                fresh_traces_and_guests=True,independent_mutation=negatives,
                suite=str(suite.relative_to(ROOT)))
    (analysis/'suite_validation.json').write_text(json.dumps(report,indent=2)+'\n')
    selection=dict(status='validated',suite=str(suite.relative_to(ROOT)),
                   files={name:str(path.relative_to(ROOT)) for name,path in {
                       'width':analysis/'width_summary.csv','graph':paths['graph']/'summary.csv',
                       'warm':paths['warm']/'summary.csv','bandwidth':paths['bandwidth']/'summary.csv',
                       'cache':analysis/'cache/aggregate.csv','negative':analysis/'independent_mutation.json',
                       'validation':analysis/'suite_validation.json'}.items()},
                   artifact_groups=[str(path.relative_to(ROOT)) for path in
                                    (suite,paths['graph'],paths['warm'],paths['bandwidth'])])
    (ROOT/'paper/experiment_data.json').write_text(json.dumps(selection,indent=2)+'\n')
    print('Validated and selected fresh paper data: '+str(suite))


if __name__=='__main__':main()
