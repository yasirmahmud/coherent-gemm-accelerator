"""Generate final-paper tables from verified analysis CSVs."""
import csv
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'paper'


def read(path):
    with (ROOT/path).open() as f: return list(csv.DictReader(f))


def table(name,header,rows,columns,caption):
    text='\\begin{table}[htbp]\\centering\\small\n\\begin{tabular}{'+columns+'}\\toprule\n'
    text+=header+' \\\\ \\midrule\n'
    text+='\n'.join(' & '.join(row)+' \\\\' for row in rows)
    text+='\n\\bottomrule\\end{tabular}\n\\caption{'+caption+'}\n\\end{table}\n'
    (OUT/name).write_text(text)


def main():
    width=read('results/analysis/width_summary.csv')
    graph=read('results/diagnostics/graph_n24/summary.csv')
    warm=read('results/diagnostics/warm_n24/summary.csv')
    table('width_table.tex',r'$N$ & $w$ & Datapath (ns) & Offload (ns) & CPU speedup & FU (mm$^2$) & Memory (mm$^2$)',
        [[r['n'],r['width'],r['datapath_cycles'],f"{float(r['offload_ns']):.0f}",
          f"{float(r['cpu_speedup']):.3f}",f"{float(r['fu_area_um2'])/1e6:.3f}",
          f"{float(r['mem_area_um2'])/1e6:.3f}"] for r in width], 'rrrrrrr',
        'Main width comparison: published $N=24$, recovered ece-lnx-10 cohort $N=32$. Memory and FU estimates are separate.')
    table('graph_table.tex',r'$w$ & Source $A$ loads & Optimized $A/B$ loads & Accepted $A/B$ loads & Accepted $C$ stores',
        [[r['width'],r['source_A_loads'],r['after_connected_Load_A']+'/'+r['after_connected_Load_B'],
          r['accepted_A_load']+'/'+r['accepted_B_load'],r['accepted_C_store']] for r in graph],'rrrrr',
        'Passive diagnostic, $N=24$, issue limit 4. Returned requests equal accepted requests per array.')
    rows=[]
    for case in ('matched','unchanged'):
        for w in ('1','2','4'):
            checked=[r for r in warm if r['input_case']==case and r['width']==w and r['mode']=='correctness']
            timed=[r for r in warm if r['input_case']==case and r['width']==w and r['mode']=='timed']
            if len(checked)!=3 or len(timed)!=3: raise ValueError('Missing paper call evidence')
            rows.append([case,w,'/'.join(f"{float(r['datapath_cycles']):.0f}" for r in checked),
                         '/'.join(f"{float(r['datapath_cycles']):.0f}" for r in timed),
                         '/'.join(f"{int(r['offload_ticks'])/1000:.0f}" for r in timed)])
    table('warm_table.tex',r'Input & $w$ & Checked cycles (0/1/2) & Timed cycles (0/1/2) & Timed offload (ns; 0/1/2)',
          rows,'lrrrr','Three-call $N=24$ diagnostics. Checker and timed harnesses have different cache histories; full per-call checks pass in the checker runs.')
    print(OUT)


if __name__=='__main__': main()
