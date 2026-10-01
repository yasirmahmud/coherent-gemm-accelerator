"""Inventory and report aggregate Ruby evidence, without classifying miss causes."""
import argparse
import csv
import json
import re
from pathlib import Path
from summarize_widths import blocks, stat

ROOT = Path(__file__).resolve().parents[1]
COHORT = ROOT / 'results/cache_bandwidth/n24_20260930'
OUT = ROOT / 'results/analysis/cache'


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cohort',type=Path,default=COHORT)
    parser.add_argument('--out',type=Path,default=OUT)
    args=parser.parse_args()
    cohort=args.cohort.resolve();out=args.out.resolve()
    out.mkdir(parents=True, exist_ok=True)
    rows = []
    inventory = {}
    for width, variant in ((1, 'base'), (4, 'tiled4')):
        bench = 'gemm_acp_pilot' if width == 1 else 'gemm_tiled4'
        for bw in (1, 2, 4):
            path = cohort / 'points' / f'{variant}_bw{bw}' / 'invocation/m5out/stats.txt'
            data = blocks(path)
            if 'datapath completed.' not in data[0] or '# Stats desc: gemm invocation' not in data[1]:
                raise ValueError('Unmatched measurement intervals')
            b = data[0]
            p = f'system.{bench}_datapath'
            ruby = 'system.ruby.l1_cntrl_acc0.L1Dcache'
            rows.append(dict(cohort=cohort.name, n=24, width=width, bandwidth=bw,
                completion_ticks=int(stat(b,'sim_ticks')),
                returned_loads=int(stat(b,p+'.total_dcache_loads')),
                returned_stores=int(stat(b,p+'.total_dcache_stores')),
                latency_samples=int(stat(b,p+'.dcache_latency::samples')),
                latency_mean_ticks=stat(b,p+'.dcache_latency::mean'),
                queue_samples=int(stat(b,p+'.dcache_queue_time::samples')),
                queue_mean_ticks=stat(b,p+'.dcache_queue_time::mean'),
                ruby_demand_hits=int(stat(b,ruby+'.demand_hits')),
                ruby_demand_misses=int(stat(b,ruby+'.demand_misses')),
                ruby_demand_accesses=int(stat(b,ruby+'.demand_accesses')),
                host_return_demand_hits=int(stat(data[1],ruby+'.demand_hits')),
                host_return_demand_misses=int(stat(data[1],ruby+'.demand_misses')),
                raw=str(path.relative_to(ROOT))))
            r = rows[-1]
            if r['latency_samples'] != r['returned_loads'] + r['returned_stores']:
                raise ValueError('Returned-operation histogram mismatch')
            if r['ruby_demand_accesses'] != r['ruby_demand_hits'] + r['ruby_demand_misses']:
                raise ValueError('Ruby demand counters inconsistent')
            for name, value, description in re.findall(r'(?m)^(system\.[\w.:]+)\s+(\S+)\s+# (.*)$', b):
                if ('ruby' in name and re.search(r'hit|miss|prefetch|invalid|coher|alias',name,re.I)) or 'conflict' in name.lower():
                    inventory[name] = description
    with (out/'aggregate.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=rows[0].keys(),lineterminator='\n'); w.writeheader();w.writerows(rows)
    (out/'counter_inventory.json').write_text(json.dumps(inventory,indent=2,sort_keys=True)+'\n')
    lines=['# Aggregate accelerator cache analysis','',
        'Pinned protocol counter definitions are retained in `implementation/`. Statistics are from the reset-to-datapath-completion block only; host return is separate.', '',
        '| Width | Issue limit | Returned loads/stores | Ruby demand hits/misses | Access latency (ticks) | Queue samples | Queue mean (ticks) |',
        '| ---: | ---: | ---: | ---: | ---: | ---: | ---: |']
    for r in rows:
        lines.append(f'| {r["width"]} | {r["bandwidth"]} | {r["returned_loads"]}/{r["returned_stores"]} | {r["ruby_demand_hits"]}/{r["ruby_demand_misses"]} | {r["latency_mean_ticks"]:.1f} | {r["queue_samples"]} | {r["queue_mean_ticks"]:.1f} |')
    lines += ['', '1 tick = 1 ps. Demand misses include a store upgrade from Shared to Modified; they are not solely absent-line misses.',
        'The L1 controller profiles mandatory protocol actions. The sequencer can alias multiple requests to a cache line, so controller actions need not equal datapath returned operations.',
        'Latency samples equal returned loads plus stores; demand accesses equal demand hits plus misses at every point.',
        'Queue samples omit successful retry issuance in this pinned implementation; their means describe that subset.',
        'The unused ACP sequencer cache and accelerator instruction cache report zeros; these do not establish an absence of data-cache misses.',
        'Global Ruby latency histograms include CPU traffic and cannot be treated as accelerator-only samples.', '',
        'No retained line-level demand sequence with invalidation/ownership events or fully-associative shadow replay exists for this cohort.',
        'We therefore report no compulsory/capacity/conflict/coherence partition. The 108 demand misses at N=24 do not prove any such partition, even though they equal the three matrices’ nominal cache-line count.',
        'CPU conflicting-load counters describe CPU load/store ordering, not accelerator cache conflicts.',
        'A shadow classifier and event observer are skipped under task 2’s aggregate-analysis alternative; the proposal promises aggregate measurements and states the attribution limit.',
        'No timing instrumentation or simulator changes were needed for this analysis; original raw evidence and validation remain intact.', '']
    (out/'ANALYSIS.md').write_text('\n'.join(lines))
    print(out/'aggregate.csv')


if __name__ == '__main__':
    main()
