"""Validate and summarize main widths without mixing historical cohorts."""
import argparse
import configparser
import csv
import gzip
import hashlib
import json
import re
from pathlib import Path
from diagnostic_common import normalized_configuration

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'results/analysis'
COHORTS = {24: ('published', ROOT / 'results'),
           32: ('ece-lnx-10_2026-09-30', ROOT / 'results/reproductions/ece-lnx-10_2026-09-30')}


def single(text, pattern):
    values = re.findall(pattern, text, re.MULTILINE)
    if len(values) != 1:
        raise ValueError(f'Expected one {pattern!r}; got {len(values)}')
    return values[0]


def stat(text, name):
    return float(single(text, rf'^{re.escape(name)}\s+(\S+)'))


def blocks(path):
    text = path.read_text()
    result = re.findall(r'---------- Begin Simulation Statistics ----------(.*?)'
                        r'---------- End Simulation Statistics\s*----------', text, re.DOTALL)
    if len(result) != text.count('---------- Begin Simulation Statistics ----------'):
        raise ValueError(f'Truncated stats: {path}')
    return result


def controls(path, bench):
    c = configparser.ConfigParser(interpolation=None)
    c.read(path)
    selections = {'system.cpu': ['type', 'numROBEntries', 'LQEntries', 'SQEntries',
                                  'fetchWidth', 'decodeWidth', 'issueWidth', 'commitWidth'],
                  f'system.{bench}_datapath': ['cycleTime', 'cacheSize', 'cacheAssoc',
                      'cacheLineSize', 'cacheQueueSize', 'cacheBandwidth'],
                  'system.clk_domain': ['clock'], 'system.cpu_clk_domain': ['clock']}
    return {f'{section.replace(bench, "KERNEL")}.{key}': c[section][key]
            for section, keys in selections.items() for key in keys}


def collect(cohorts=None, strict=False):
    rows = []
    evidence = {}
    for n, (cohort, base) in (cohorts or COHORTS).items():
        group = []
        check_controls = {}
        checksums = []
        effective_controls = {}
        for width, variant in ((1,'base'), (2,'tiled2'), (4,'tiled4')):
            tag = 'cache' if width == 1 else 'accel'
            bench = 'gemm_acp_pilot' if width == 1 else 'gemm_' + variant
            dirs = {stage: base / folder / f'{variant}_n{n}' for stage, folder in
                    (('full','fair_results'),('roi','roi_results'),('invocation','invocation_results'))}
            if strict:
                inputs=base/'inputs'/f'{variant}_n{n}'
                trace=inputs/'dynamic_trace.gz'
                if hashlib.sha256(trace.read_bytes()).hexdigest()!=(inputs/'trace.sha256').read_text().split()[0]:
                    raise ValueError('Main trace identity mismatch')
                with gzip.open(trace,'rb') as f: logical=hashlib.sha256(f.read()).hexdigest()
                if logical!=(inputs/'logical-trace.sha256').read_text().split()[0]:
                    raise ValueError('Main logical trace identity mismatch')
                for stage,output in dirs.items():
                    records=(output/'binaries.sha256').read_text().splitlines()
                    if len(records)!=2: raise ValueError('Missing guest identities')
                    for record in records:
                        expected,name=record.split(None,1)
                        guest=output/Path(name).name
                        if hashlib.sha256(guest.read_bytes()).hexdigest()!=expected:
                            raise ValueError('Main guest identity mismatch')
                    for suffix in ((tag,'cpu') if stage!='invocation' else (tag,)):
                        single((output/f'gem5-{suffix}.log').read_text(),r'^Exiting @ tick (\d+) because exiting with last active thread context$')
                        effective=normalized_configuration(output/f'm5out-{suffix}/config.ini',bench,output/f'm5out-{suffix}')
                        key=(stage,'cpu' if suffix=='cpu' else 'accelerator')
                        if key in effective_controls and effective!=effective_controls[key]:
                            changed=[k for k in effective if effective.get(k)!=effective_controls[key].get(k)]
                            raise ValueError(f'Uncontrolled main configuration changes: N={n}, {variant}, {key}: {changed}')
                        effective_controls[key]=effective
            full = (dirs['full'] / f'gem5-{tag}.log').read_text()
            for name in (f'gem5-{tag}.log', 'gem5-cpu.log'):
                t = (dirs['full'] / name).read_text()
                single(t, r'^GEMM passed: (0) mismatches$')
                if 'GEMM FAILED' in t:
                    raise ValueError(f'Failed check: {dirs["full"] / name}')
            for stage in ('roi', 'invocation'):
                for suffix in ((tag, 'cpu') if stage == 'roi' else (tag,)):
                    checksums.append(int(single((dirs[stage]/f'gem5-{suffix}.log').read_text(),
                                                r'^GEMM checksum: (-?\d+)$')))
            for stage in dirs:
                check_controls[f'{variant}/{stage}'] = controls(dirs[stage]/f'm5out-{tag}/config.ini', bench)
            roi = blocks(dirs['roi']/f'm5out-{tag}/stats.txt')
            cpu = blocks(dirs['roi']/'m5out-cpu/stats.txt')
            inv = blocks(dirs['invocation']/f'm5out-{tag}/stats.txt')
            if len(roi) != 1 or len(cpu) != 1 or len(inv) != 3:
                raise ValueError('Wrong stage statistics block counts')
            if not re.search(r'# Stats desc: .*datapath completed\.', inv[0]) or '# Stats desc: gemm invocation' not in inv[1]:
                raise ValueError('Invocation labels missing/out of order')
            freq = stat(inv[0], 'sim_freq')
            cycles = int(single(full, r'^Cycle : (\d+) cycles$'))
            if cycles != int(single((dirs['invocation']/f'gem5-{tag}.log').read_text(), r'^Cycle : (\d+) cycles$')):
                raise ValueError('Datapath changed between stages')
            completion = stat(inv[0], 'sim_ticks')
            host_return = stat(inv[1], 'sim_ticks')
            area = {kind.lower()+'_area_um2': float(single(full, rf'^{kind} Area: ([\deE+.-]+) uM\^2$'))
                    for kind in ('Total','FU','MEM')}
            if abs(area['total_area_um2'] - area['fu_area_um2'] - area['mem_area_um2']) > 10:
                raise ValueError('Area components do not sum within printed rounding')
            group.append(dict(n=n,width=width,cohort=cohort,datapath_cycles=cycles,
                datapath_ns=cycles,completion_ticks=int(completion),host_return_ticks=int(host_return),
                offload_ticks=int(completion+host_return),offload_ns=(completion+host_return)/freq*1e9,
                completion_residual_ns=completion/freq*1e9-cycles,
                whole_program_ticks=int(stat(roi[0],'sim_ticks')),cpu_ticks=int(stat(cpu[0],'sim_ticks')),
                cpu_speedup=stat(cpu[0],'sim_ticks')/stat(roi[0],'sim_ticks'),
                host_insts=int(stat(roi[0],'sim_insts')),**area,
                raw_root=str(base.relative_to(ROOT)), provenance='fresh local suite' if strict else 'historical; see results/provenance/historical_20260930/inventory.csv'))
        if len(set(checksums)) != 1 or len({r['host_insts'] for r in group}) != 1:
            raise ValueError(f'Unmatched checksums or host work at N={n}')
        if any(c != next(iter(check_controls.values())) for c in check_controls.values()):
            raise ValueError(f'Controlled configurations differ at N={n}')
        baseline = group[0]
        for row in group:
            row['offload_reduction_pct'] = 100*(1-row['offload_ticks']/baseline['offload_ticks'])
            row['dominated'] = any(other['offload_ticks'] <= row['offload_ticks'] and
                other['total_area_um2'] <= row['total_area_um2'] and
                (other['offload_ticks'] < row['offload_ticks'] or other['total_area_um2'] < row['total_area_um2'])
                for other in group)
        rows.extend(group)
        evidence[str(n)] = dict(cohort=cohort, checksum=checksums[0], controls=check_controls,
                               comparison_scope='all effective configuration entries within each stage, with output paths/kernel names normalized' if strict else 'selected architecture fields; historical provenance limits retained',
                               retained_trace_and_guests_verified=strict)
    return rows, evidence


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--main',type=Path,help='Fresh suite main directory; validate all four sizes and three widths')
    parser.add_argument('--out',type=Path,default=OUT)
    args=parser.parse_args()
    fresh={n:(args.main.parent.name,args.main.resolve()) for n in (8,16,24,32)} if args.main else None
    rows, evidence = collect(fresh,strict=bool(fresh))
    out=args.out.resolve()
    out.mkdir(parents=True, exist_ok=True)
    with (out/'width_summary.csv').open('w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=rows[0].keys(), lineterminator='\n')
        w.writeheader(); w.writerows(rows)
    (out/'width_validation.json').write_text(json.dumps(evidence, indent=2)+'\n')
    lines = ['# Main width comparison', '', 'N=24 uses the published cohort; N=32 uses the recovered cohort.',
             'All CPU and accelerator full checks pass; ROI/invocation checksums and host work match within each size.',
             'Historical identity limits are in the provenance inventory. Area is from the full correctness stage.', '',
             '| N | Width | Datapath (ns) | Offload (ns) | CPU speedup, whole program | FU (µm²) | Memory (µm²) | Dominated in offload/total area? |',
             '| ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |']
    for r in rows:
        lines.append(f'| {r["n"]} | {r["width"]} | {r["datapath_ns"]} | {r["offload_ns"]:.0f} | {r["cpu_speedup"]:.3f}× | {r["fu_area_um2"]:,.0f} | {r["mem_area_um2"]:,.0f} | {r["dominated"]} |')
    lines += ['', 'Dominance is assessed within each size/cohort with printed modeled total area and offload ticks.',
              'At N=24 width 4 dominates widths 1 and 2. At N=32 widths 1 and 4 remain choices:',
              'width 1 uses less modeled area; width 4 is faster. Width 2 is dominated by width 4.',
              'These are pre-RTL estimates with characterization and historical provenance limits, not universal rankings.', '']
    if fresh:
        lines[2]='One fresh suite covers N=8/16/24/32 and widths 1/2/4; all traces and guests were generated for this suite.'
        lines[4]='All effective configurations match within each stage/size after normalizing output paths and kernel names. Retained trace and guest identities are verified.'
        lines[-2]='These are pre-RTL estimates for the tested trace-driven workloads, not universal rankings.'
    (out/'WIDTH_SUMMARY.md').write_text('\n'.join(lines))
    print(out/'width_summary.csv')


if __name__ == '__main__':
    main()
