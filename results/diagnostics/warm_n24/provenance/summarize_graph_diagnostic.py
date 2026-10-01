"""Prove observer equivalence, then link source, connected graph and requests."""
import configparser
import argparse
import csv
import hashlib
import gzip
import json
import re
from pathlib import Path
from summarize_widths import blocks, single, stat
from diagnostic_common import normalized_configuration

ROOT=Path(__file__).resolve().parents[1]
COHORT=ROOT/'results/diagnostics/graph_n24'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def counters(log):
    graph={}
    for stage,key,value in re.findall(r'(?m)^DIAG graph (before|after) (\S+) (\d+)$',log):
        if (stage,key) in graph:
            raise ValueError('Duplicate graph counter')
        graph[stage,key]=int(value)
    requests={}
    for key,value in re.findall(r'(?m)^DIAG request (\S+) (\d+)$',log):
        if key in requests:
            raise ValueError('Duplicate request counter')
        requests[key]=int(value)
    if not graph or not requests:
        raise ValueError('Missing observer counters')
    return graph,requests


def normalized_stats(text):
    return {m[0]:m[1] for m in re.findall(r'(?m)^(\S+)\s+(.+?)\s*(?:#.*)?$',text)
            if not m[0].startswith(('host','#','----------'))}


def configs(path, output):
    c=configparser.ConfigParser(interpolation=None); c.read(path)
    return {(s,k):v.replace(str(output).replace(str(ROOT),'/project'),'@OUTPUT@')
            for s in c.sections() for k,v in c[s].items()}


def main():
    global COHORT
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("cohort", nargs="?", type=Path, default=COHORT)
    COHORT = parser.parse_args().cohort.resolve()
    if not (COHORT/'provenance/completed-at.txt').exists():
        raise ValueError('Diagnostic runner has not completed')
    rows=[]; audit={}; stage_configs={}
    for width,variant in ((1,'base'),(2,'tiled2'),(4,'tiled4')):
        bench='gemm_acp_pilot' if width==1 else 'gemm_'+variant
        point=COHORT/variant; inputs=point/'inputs'
        if sha(inputs/'dynamic_trace.gz') != (inputs/'trace.sha256').read_text().split()[0]:
            raise ValueError('Trace hash mismatch')
        with gzip.open(inputs/'dynamic_trace.gz', 'rb') as handle:
            logical = hashlib.sha256(handle.read()).hexdigest()
        if logical != (inputs/'logical-trace.sha256').read_text().split()[0]:
            raise ValueError('Logical trace identity mismatch')
        for stage in ('full','invocation'):
            if sha(inputs/(stage+'-guest')) != (inputs/(stage+'-binary.sha256')).read_text().split()[0]:
                raise ValueError('Guest binary identity mismatch')
        retained_graph=None; retained_requests=None
        for stage in ('full','invocation'):
            reference=point/stage/'reference'; instrumented=point/stage/'instrumented'
            ref_log=(reference/'gem5.log').read_text(); obs_log=(instrumented/'gem5.log').read_text()
            if stage=='full':
                single(ref_log,r'^GEMM passed: (0) mismatches$');single(obs_log,r'^GEMM passed: (0) mismatches$')
            else:
                if single(ref_log,r'^GEMM checksum: (-?\d+)$') != single(obs_log,r'^GEMM checksum: (-?\d+)$'):
                    raise ValueError('Observer checksum changed')
            for metric in (r'^Cycle : (\d+) cycles$', r'^FU Area: ([\deE+.-]+) uM\^2$',
                           r'^MEM Area: ([\deE+.-]+) uM\^2$'):
                if single(ref_log,metric)!=single(obs_log,metric):
                    raise ValueError('Observer changed datapath timing or cost')
            ref=blocks(reference/'m5out/stats.txt'); obs=blocks(instrumented/'m5out/stats.txt')
            if len(ref)!=len(obs) or any(normalized_stats(a)!=normalized_stats(b) for a,b in zip(ref,obs)):
                raise ValueError(f'Observer changed simulated statistics: {variant}/{stage}')
            if configs(reference/'m5out/config.ini',reference)!=configs(instrumented/'m5out/config.ini',instrumented):
                raise ValueError('Effective configuration changed')
            controlled = normalized_configuration(reference/'m5out/config.ini',bench,reference)
            if stage in stage_configs and controlled != stage_configs[stage]:
                differences = [k for k in controlled if controlled.get(k) != stage_configs[stage].get(k)]
                raise ValueError('Across-width effective configuration changed: ' + str(differences))
            stage_configs[stage] = controlled
            graph,requests=counters(obs_log)
            if retained_graph is not None and (graph!=retained_graph or requests!=retained_requests):
                raise ValueError('Counters changed across correctness/invocation harnesses')
            retained_graph,retained_requests=graph,requests
            loads=sum(requests.get(f'returned.{a}.load',0) for a in ('A','B','C'))
            stores=sum(requests.get(f'returned.{a}.store',0) for a in ('A','B','C'))
            if loads!=stat(obs[0],f'system.{bench}_datapath.total_dcache_loads') or stores!=stat(obs[0],f'system.{bench}_datapath.total_dcache_stores'):
                raise ValueError('Observer returned counters disagree with raw stats')
            audit[f'{variant}/{stage}']=dict(simulated_stats_identical=True,config_identical=True,all_fields_controlled_across_widths=True,
                cycles=int(single(ref_log,r'^Cycle : (\d+) cycles$')),trace_sha256=sha(inputs/'dynamic_trace.gz'))
        g,r=retained_graph,retained_requests
        row=dict(width=width,n=24,issue_limit=4,source_A_loads=24**3//width,source_B_loads=24**3,
                 source_C_stores=24**2,source_products=24**3,source_accumulations=24**3)
        for stage in ('before','after'):
            for scope in ('all','connected'):
                row[f'{stage}_{scope}_nodes']=g[stage,scope+'.nodes']
                for array in ('A','B','C'):
                    for op in ('Load','Store'):
                        row[f'{stage}_{scope}_{op}_{array}']=g.get((stage,scope+'.'+op+'.'+array),0)
                for op in ('Add.gemm_value','Mul.gemm_value','Add.other','Mul.other','IndexAdd','GetElementPtr','Shl'):
                    row[f'{stage}_{scope}_{op}']=g.get((stage,scope+'.'+op),0)
        for array,op in (('A','load'),('B','load'),('C','store')):
            accepted=sum(r.get(f'{kind}.{array}.{op}',0) for kind in ('accepted_initial','accepted_retry'))
            returned=r.get(f'returned.{array}.{op}',0)
            if accepted!=returned:
                raise ValueError('Accepted requests differ from returned requests')
            for kind in ('accepted_initial','accepted_retry','returned','send_rejected','queue_allocations','queue_join_nodes'):
                row[f'{kind}_{array}_{op}']=r.get(f'{kind}.{array}.{op}',0)
            row[f'accepted_{array}_{op}']=accepted
        for metric in ('issue_blocked_attempts','issue_blocked_cycles','queue_full_attempts','queue_full_cycles'):
            row[metric]=r.get(metric,0)
        if row['issue_blocked_cycles']>audit[f'{variant}/full']['cycles'] or row['issue_blocked_cycles']>row['issue_blocked_attempts']:
            raise ValueError('Invalid blocked-cycle count')
        rows.append(row)
    with (COHORT/'summary.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=rows[0].keys(),lineterminator='\n'); w.writeheader();w.writerows(rows)
    (COHORT/'validation.json').write_text(json.dumps(audit,indent=2)+'\n')
    lines=['# Source → graph → memory attribution', '',
        'N=24, widths 1/2/4, issue limit 4. Reference and diagnostic runs reuse each kernel’s trace and each stage’s guest binary.',
        'Full elementwise checks pass; every simulated statistics block and effective configuration matches the reference. Host wall-time/rate/memory statistics are excluded from equality checks.', '',
        '| Width | Source A/B loads | Before connected A/B loads | After connected A/B loads | GEMM products/adds after | Accepted A/B loads | Accepted C stores | Returned loads/stores |',
        '| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |']
    for r in rows:
        lines.append(f'| {r["width"]} | {r["source_A_loads"]}/{r["source_B_loads"]} | {r["before_connected_Load_A"]}/{r["before_connected_Load_B"]} | {r["after_connected_Load_A"]}/{r["after_connected_Load_B"]} | {r["after_connected_Mul.gemm_value"]}/{r["after_connected_Add.gemm_value"]} | {r["accepted_A_load"]}/{r["accepted_B_load"]} | {r["accepted_C_store"]} | {r["returned_A_load"]+r["returned_B_load"]}/{r["returned_C_store"]} |')
    lines+=['', 'Full arithmetic/opcode and all/connected node totals, retries, queue joins, blocked attempts and blocked cycles are in `summary.csv`.',
        'GEMM arithmetic is the backward value slice rooted at C-store value operands, stopping at loads and GEPs and excluding control/memory edges. Address computation is counted separately; integer adds are not all MACs.',
        'All nodes are retained graph objects; connected nodes have at least one edge. Connected counts describe graph liveness, not a count of packets.',
        'Accepted = successful initial sends plus successful retry sends, excluding the finish/control packet. Returned means data-cache response callbacks; both reconcile per array.',
        'Queue-join nodes count each node’s first successful association with an already existing entry. Loads merge by cache-line address; repeated polls of a node do not increase this count.',
        'Rejected initial sends are separate from successful retry sends. Blocked attempts count node polls; blocked cycles count distinct accelerator ticks per invocation.',
        'The queue merges accesses after graph optimization. Fewer A loads at wider source/graph width do not imply fewer accepted requests in this cohort.', '']
    (COHORT/'ANALYSIS.md').write_text('\n'.join(lines))
    print(COHORT/'summary.csv')


if __name__=='__main__':
    main()
