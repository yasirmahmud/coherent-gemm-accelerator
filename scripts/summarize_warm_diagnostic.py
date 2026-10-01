"""Validate paired three-call evidence, retaining checker-induced state differences."""
import argparse
import csv
from datetime import datetime
import gzip
import hashlib
import json
import re
import subprocess
import tempfile
from pathlib import Path
from summarize_repeated import validate_run, invocation_blocks, interval_ticks
from summarize_widths import single, stat, controls
from diagnostic_common import normalized_configuration

ROOT=Path(__file__).resolve().parents[1]
COHORT=ROOT/'results/diagnostics/warm_n24'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def expected_checksum(case):
    n=24
    a=[i%7-3 for i in range(n*n)]; b=[i%5-2 for i in range(n*n)]
    if case=='matched':
        for rep in range(3): a[rep]+=1
    return sum(a[i*n+k]*b[k*n+j] for i in range(n) for j in range(n) for k in range(n))


def text_digest(binary):
    with tempfile.TemporaryDirectory() as directory:
        output=Path(directory)/'text'
        subprocess.run(['objcopy','--dump-section','.text='+str(output),str(binary),str(Path(directory)/'guest')],check=True)
        return sha(output)


def main():
    global COHORT
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("cohort", nargs="?", type=Path, default=COHORT)
    parser.add_argument("--finalize", action="store_true", help="Validate completed stage files after runner finalization failed")
    args = parser.parse_args()
    COHORT = args.cohort.resolve()
    if not args.finalize and not any((COHORT/'provenance'/name).exists() for name in ('completed-at.txt','validated-at.txt')):
        raise ValueError('Warm diagnostic runner has not completed')
    rows=[]; validations={}; common_controls=None; host_text={}; effective_controls=None
    for case in ('matched','unchanged'):
        for width,variant in ((1,'base'),(2,'tiled2'),(4,'tiled4')):
            point=COHORT/f'{case}_{variant}'; inputs=point/'inputs'
            trace_hash=sha(inputs/'dynamic_trace.gz')
            if trace_hash!=(inputs/'trace.sha256').read_text().split()[0]: raise ValueError('Trace identity mismatch')
            with gzip.open(inputs/'dynamic_trace.gz','rb') as f:
                logical=hashlib.sha256(f.read()).hexdigest()
            if logical!=(inputs/'logical-trace.sha256').read_text().split()[0]: raise ValueError('Logical trace mismatch')
            correctness=validate_run(point/'correctness',3)
            for mode in ('correctness','timed'):
                run=point/mode; metadata=json.loads((run/'run.json').read_text())
                if metadata!=dict(expected_calls=3,mode=mode,input_case=case,variant=variant):
                    raise ValueError('Unexpected run metadata')
                if (run/'trace.sha256').read_text().split()[0]!=trace_hash: raise ValueError('Mode trace mismatch')
                if sha(run/'guest')!=(run/'binary.sha256').read_text().split()[0]: raise ValueError('Guest identity mismatch')
                log=(run/'gem5-accel.log').read_text()
                single(log,r'^Exiting @ tick (\d+) because exiting with last active thread context$')
                if mode=='correctness': single(log,r'^GEMM passed: (0) mismatches$')
                else:
                    if int(single(log,r'^GEMM checksum: (-?\d+)$'))!=expected_checksum(case):
                        raise ValueError('Timed final checksum differs from deterministic reference')
                    if 'GEMM call ' in log: raise ValueError('Checker is present in timed run')
                    digest=text_digest(run/'guest')
                    if case in host_text and host_text[case]!=digest:
                        raise ValueError('Timed guest instruction sections differ across widths')
                    host_text[case]=digest
                pairs=invocation_blocks(run/'m5out-accel/stats.txt')
                if len(pairs)!=3: raise ValueError('Missing per-call intervals')
                metrics={name:re.findall(pattern,log,re.MULTILINE) for name,pattern in {
                    'datapath_cycles':r'^Cycle : (\d+) cycles$',
                    'fu_area_um2':r'^FU Area: ([\deE+.-]+) uM\^2$',
                    'mem_area_um2':r'^MEM Area: ([\deE+.-]+) uM\^2$',
                    'multipliers32':r'^Num of Multipliers \(32-bit\): (\d+)$',
                    'registers32':r'^Num of Registers \(32-bit\): (\d+)$',
                    'graph_nodes':r'^Num of Nodes: (\d+)$'}.items()}
                if any(len(v)!=3 for v in metrics.values()): raise ValueError('Missing per-call resource/graph reports')
                bench='gemm_acp_pilot' if width==1 else 'gemm_'+variant
                config=controls(run/'m5out-accel/config.ini',bench)
                if common_controls is not None and config!=common_controls: raise ValueError('Warm controls differ')
                common_controls=config
                effective = normalized_configuration(run/'m5out-accel/config.ini',bench,run)
                if effective_controls is not None and effective != effective_controls:
                    differences = [k for k in effective if effective.get(k) != effective_controls.get(k)]
                    raise ValueError('Unintended effective config change: ' + str(differences))
                effective_controls = effective
                for i,(completion,returned) in enumerate(pairs):
                    p=f'system.{bench}_datapath'; ruby='system.ruby.l1_cntrl_acc0.L1Dcache'
                    row=dict(input_case=case,width=width,mode=mode,call=i,trace_sha256=trace_hash,
                        completion_ticks=interval_ticks(completion),return_ticks=interval_ticks(returned),
                        offload_ticks=interval_ticks(completion)+interval_ticks(returned),
                        **{name:float(values[i]) for name,values in metrics.items()})
                    for name in ('total_dcache_loads','total_dcache_stores','dcache_latency::mean',
                                 'dcache_latency::samples','dcache_queue_time::mean','dcache_queue_time::samples'):
                        row[name.replace('::','_')]=stat(completion,p+'.'+name)
                    for name in ('demand_hits','demand_misses'):
                        row['ruby_'+name]=stat(completion,ruby+'.'+name)
                    row['raw']=str((run/'m5out-accel/stats.txt').relative_to(ROOT))
                    rows.append(row)
                validations[f'{case}/{variant}/{mode}']=dict(trace_sha256=trace_hash,
                    logical_trace_sha256=logical,guest_sha256=sha(run/'guest'),
                    expected_calls=3,correctness_checked_in_paired_run=True)
    with (COHORT/'summary.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=rows[0].keys(),lineterminator='\n'); w.writeheader();w.writerows(rows)
    (COHORT/'validation.json').write_text(json.dumps(dict(runs=validations,controls=common_controls,
        all_effective_configuration_fields_match=True,timed_text_sha256=host_text,policy='timed checksums are supplemental; every call checked in paired correctness run'),indent=2)+'\n')
    lines=['# Repeated-call diagnostics', '',
        'N=24, three calls, issue limit 4, cache/queue/clocks fixed. Each case/width shares one trace between correctness and timed harnesses.',
        'Every correctness call passes a full output check. Timed runs omit per-call checks and pass a final checksum; their instruction sections are byte-identical across widths within each input case.',
        'Mutation is pre-agreed at trace time; unchanged input is a separate trace/case. Each invocation resets statistics before the call and dumps after host return.', '',
        '| Input | Width | Mode | Call | Datapath (cycles) | Offload (ticks) | Returned loads/stores | Access mean (ticks) | Queue mean (ticks) | Ruby hits/misses | FU area (µm²) | Multipliers/registers (32-bit) |',
        '| --- | ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |']
    for r in rows:
        lines.append(f'| {r["input_case"]} | {r["width"]} | {r["mode"]} | {r["call"]} | {r["datapath_cycles"]:.0f} | {r["offload_ticks"]} | {r["total_dcache_loads"]:.0f}/{r["total_dcache_stores"]:.0f} | {r["dcache_latency_mean"]:.1f} | {r["dcache_queue_time_mean"]:.1f} | {r["ruby_demand_hits"]:.0f}/{r["ruby_demand_misses"]:.0f} | {r["fu_area_um2"]:.0f} | {r["multipliers32"]:.0f}/{r["registers32"]:.0f} |')
    lines+=['', '1 tick = 1 ps. Complete histogram sample counts, graph sizes, offload segments and memory area are in `summary.csv`.',
        'The full checker reads A/B/C and performs CPU GEMM between calls. It changes cache/coherence state even though its runtime lies outside the measured invocation intervals.',
        'The timed harness supplies the controlled across-width comparison; the correctness harness supplies every-call validation. They are distinct cache histories, so timed checksums alone do not prove every intermediate output.',
        'First/later-call differences are associated with cache requests, queue subsets and resource peaks directly. They do not isolate warmth from scheduler/node ordering, input mutation or CPU work.',
        'Independent-mutation correctness checks are separate from these paired trace-matched runs and must not be included in passing timing comparisons.',
        'Resource peaks are per-call pre-RTL model estimates, not a physical hardware reconfiguration or a steady-state area claim.', '']
    (COHORT/'ANALYSIS.md').write_text('\n'.join(lines))
    if args.finalize:
        (COHORT/'provenance/validated-at.txt').write_text(datetime.utcnow().isoformat()+'Z\n')
    print(COHORT/'summary.csv')


if __name__=='__main__':
    main()
