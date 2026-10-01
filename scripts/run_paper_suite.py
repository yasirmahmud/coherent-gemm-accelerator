"""Run every paper experiment locally with isolated work directories and retained evidence."""
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import threading

ROOT = Path(__file__).resolve().parents[1]
IMAGE = 'docker.io/xyzsam/gem5-aladdin@sha256:03b405408f17ceab194b08e03c986fcffd3ed10486d3443bd17eda87b33bee92'
VARIANTS = ('base', 'tiled2', 'tiled4')


def now():
    return datetime.utcnow().isoformat() + 'Z'


def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(1024*1024), b''): h.update(chunk)
    return h.hexdigest()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--engine', default='docker')
    p.add_argument('--source', type=Path, default=ROOT/'.artifacts/source')
    p.add_argument('--diagnostic-source', type=Path, default=ROOT/'.artifacts/diagnostic-source')
    p.add_argument('--workers', type=int, default=6)
    p.add_argument('--cohort', default='paper_'+datetime.utcnow().strftime('%Y%m%dT%H%M%SZ'))
    args = p.parse_args()
    if not re.fullmatch('[A-Za-z0-9_-]+', args.cohort) or args.workers < 1: p.error('Invalid cohort/workers')
    source = args.source.resolve(); diagnostic = args.diagnostic_source.resolve()
    for path in (source/'build/X86/gem5.opt', diagnostic/'build/X86/gem5.opt'):
        if not path.is_file(): p.error('Missing simulator: '+str(path))
    base = ROOT/'results/paper_runs'/args.cohort
    graph = ROOT/'results/diagnostics'/(args.cohort+'_graph')
    warm = ROOT/'results/diagnostics'/(args.cohort+'_warm')
    bandwidth = ROOT/'results/cache_bandwidth'/(args.cohort+'_bandwidth')
    for path in (base, graph, warm, bandwidth):
        if path.exists(): p.error('Refusing to overwrite '+str(path))
    for path in (base, graph, warm, bandwidth): (path/'provenance').mkdir(parents=True)
    scripts = ('run_paper_suite.py', 'run_paper_point_inside.sh', 'run_paper_negative_inside.sh',
               'run_graph_diagnostic_inside.sh', 'run_warm_diagnostic_inside.sh', 'run_cache_bandwidth_inside.sh')
    for name in scripts: shutil.copyfile(ROOT/'scripts'/name, base/'provenance'/name)
    for path, script in ((graph,'run_graph_diagnostic_inside.sh'),(warm,'run_warm_diagnostic_inside.sh'),
                         (bandwidth,'run_cache_bandwidth_inside.sh')):
        shutil.copyfile(ROOT/'scripts'/script,path/'provenance'/script)
        shutil.copytree(source/'src/aladdin/integration-test/common',path/'provenance/common')
        (path/'provenance/container-image.txt').write_text(IMAGE+'\n')
    metadata = dict(started_at=now(), suite=args.cohort, sizes=[8,16,24,32], widths=[1,2,4],
                    main=str((base/'main').relative_to(ROOT)), graph=str(graph.relative_to(ROOT)),
                    warm=str(warm.relative_to(ROOT)), bandwidth=str(bandwidth.relative_to(ROOT)),
                    negative=str((base/'negative').relative_to(ROOT)), container_image=IMAGE,
                    reference_simulator_sha256=digest(source/'build/X86/gem5.opt'),
                    observer_simulator_sha256=digest(diagnostic/'build/X86/gem5.opt'), jobs={})
    # Execution identity stays in the artifacts, not the paper prose.
    metadata['execution_host'] = subprocess.check_output(['hostname'], universal_newlines=True).strip()
    (base/'provenance/project-commit.txt').write_bytes(subprocess.check_output(['git','rev-parse','HEAD'],cwd=str(ROOT)))
    (base/'provenance/project-working.diff').write_bytes(subprocess.check_output(['git','diff','--binary'],cwd=str(ROOT)))
    lock = threading.Lock()
    local = Path('/var/tmp/coherent-paper-runs')/args.cohort
    local.mkdir(parents=True)
    def container(path): return '/project/'+str(path.relative_to(ROOT))
    def execute(name, script, parameters=(), environment=None, observer=False, cache=False):
        scratch = local/name; scratch.mkdir()
        mount = '/project/.artifacts/'+args.cohort+'_'+name
        if cache: mount = '/project/.artifacts/cache_bandwidth/'+bandwidth.name
        command = [args.engine,'run','--rm','-v',str(source)+':/worksrc:ro',
                   '-v',str(ROOT)+':/project','-v',str(scratch)+':'+mount,
                   '-e','ALADDIN_HOME=/worksrc/src/aladdin','-e','TRACER_HOME=/workspace/LLVM-Tracer',
                   '-e','LLVM_HOME=/usr/local']
        if observer: command += ['-v',str(diagnostic)+':/diagnostic:ro']
        env = dict(environment or {}, GEMM_PAPER_SCRATCH=mount+'/integration-test')
        for key,value in env.items(): command += ['-e',key+'='+value]
        command += [IMAGE,'bash',container(base/'provenance'/script)]+list(parameters)
        with lock:
            metadata['jobs'][name] = dict(started_at=now(), command=command, status='running')
            (base/'run.json').write_text(json.dumps(metadata,indent=2)+'\n')
            print(now()+' START '+name,flush=True)
        with (base/(name+'.log')).open('w') as log:
            completed = subprocess.run(command,stdout=log,stderr=subprocess.STDOUT)
        with lock:
            metadata['jobs'][name].update(completed_at=now(),exit_code=completed.returncode,
                                         status='complete' if completed.returncode==0 else 'failed')
            (base/'run.json').write_text(json.dumps(metadata,indent=2)+'\n')
            print(now()+' '+('DONE ' if completed.returncode==0 else 'FAILED ')+name,flush=True)
        return completed.returncode
    jobs=[]
    for n in (32,24,16,8):
        for variant in VARIANTS:
            jobs.append(('main_{}_{}'.format(n,variant),'run_paper_point_inside.sh',(str(n),variant),
                         dict(GEMM_PAPER_ROOT=container(base/'main'))))
    # Interleave the longer studies so they run alongside the size sweep.
    jobs.insert(3,('bandwidth','run_cache_bandwidth_inside.sh',(),dict(GEMM_COHORT=bandwidth.name),False,True))
    for variant in VARIANTS:
        name='graph_'+variant
        jobs.insert(4, (name,'run_graph_diagnostic_inside.sh',(),dict(GEMM_DIAG_ROOT=container(graph),
                    GEMM_DIAG_SCRATCH='/project/.artifacts/'+args.cohort+'_'+name+'/integration-test',
                    GEMM_DIAG_VARIANTS=variant,GEMM_DIAG_PARTIAL='1'),True))
    for case in ('matched','unchanged'):
        for variant in VARIANTS:
            name='warm_'+case+'_'+variant
            jobs.insert(7,(name,'run_warm_diagnostic_inside.sh',(),dict(GEMM_DIAG_ROOT=container(warm),
                        GEMM_DIAG_SCRATCH='/project/.artifacts/'+args.cohort+'_'+name+'/integration-test',
                        GEMM_DIAG_VARIANTS=variant,GEMM_DIAG_CASES=case,GEMM_DIAG_PARTIAL='1')))
    for variant in VARIANTS:
        jobs.append(('negative_'+variant,'run_paper_negative_inside.sh',(variant,),
                     dict(GEMM_NEGATIVE_ROOT=container(base/'negative'))))
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = [pool.submit(execute,*job) for job in jobs]
        statuses = [f.result() for f in as_completed(futures)]
    metadata['completed_at']=now();metadata['status']='complete' if not any(statuses) else 'failed'
    (base/'run.json').write_text(json.dumps(metadata,indent=2)+'\n')
    if any(statuses): raise SystemExit('Some jobs failed; see '+str(base))
    for path in (base,graph,warm): (path/'provenance/completed-at.txt').write_text(now()+'\n')
    print('All experiments completed: '+str(base),flush=True)


if __name__=='__main__': main()
