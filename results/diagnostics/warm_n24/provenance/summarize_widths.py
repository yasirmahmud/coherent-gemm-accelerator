"""Validate and summarize main widths without mixing historical cohorts."""
import configparser
import csv
import json
import re
from pathlib import Path

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


def collect():
    rows = []
    evidence = {}
    for n, (cohort, base) in COHORTS.items():
        group = []
        check_controls = {}
        checksums = []
        for width, variant in ((1,'base'), (2,'tiled2'), (4,'tiled4')):
            tag = 'cache' if width == 1 else 'accel'
            bench = 'gemm_acp_pilot' if width == 1 else 'gemm_' + variant
            dirs = {stage: base / folder / f'{variant}_n{n}' for stage, folder in
                    (('full','fair_results'),('roi','roi_results'),('invocation','invocation_results'))}
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
                raw_root=str(base.relative_to(ROOT)), provenance='historical; see results/provenance/historical_20260930/inventory.csv'))
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
                               comparison_scope='selected architecture fields; historical provenance limits retained')
    return rows, evidence


def main():
    rows, evidence = collect()
    OUT.mkdir(parents=True, exist_ok=True)
    with (OUT/'width_summary.csv').open('w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=rows[0].keys(), lineterminator='\n')
        w.writeheader(); w.writerows(rows)
    (OUT/'width_validation.json').write_text(json.dumps(evidence, indent=2)+'\n')
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
    (OUT/'WIDTH_SUMMARY.md').write_text('\n'.join(lines))
    print(OUT/'width_summary.csv')


if __name__ == '__main__':
    main()
