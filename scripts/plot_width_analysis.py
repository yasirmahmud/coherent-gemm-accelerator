"""Generate labeled vector figures from validated historical width summaries."""
import csv
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'results/analysis'
COLORS = {1:'#355C7D',2:'#C06C36',4:'#26735E'}


def save(fig, name):
    fig.tight_layout()
    for ext in ('svg','pdf','png'):
        fig.savefig(str(OUT/(name+'.'+ext)), dpi=180, bbox_inches='tight')
    plt.close(fig)


def main():
    with (OUT/'width_summary.csv').open() as f:
        rows = list(csv.DictReader(f))
    fig, axes = plt.subplots(1,2,figsize=(9,3.5))
    for ax,n in zip(axes,(24,32)):
        group=[r for r in rows if int(r['n'])==n]
        ax.plot([int(r['width']) for r in group], [float(r['offload_ns']) for r in group],
                'o-',color='#355C7D',label='CPU-observed offload')
        ax.plot([int(r['width']) for r in group], [float(r['datapath_ns']) for r in group],
                's--',color='#26735E',label='Datapath')
        ax.set(title=f'N={n}: {group[0]["cohort"]}',xlabel='Output-column width',ylabel='Latency (ns)',xticks=[1,2,4])
        ax.grid(alpha=.2);ax.legend(fontsize=8)
    save(fig,'width_latency')

    with (ROOT/'results/exploratory_summary.csv').open() as f:
        small=list(csv.DictReader(f))
    fig,ax=plt.subplots(figsize=(8,4))
    for width in (1,2,4):
        if width !=2:
            prefix='base' if width==1 else 'tiled'
            ax.plot([int(r['n']) for r in small],
                    [float(r[prefix+'_cpu_ticks'])/float(r[prefix+'_accel_ticks']) for r in small],
                    'o:',color=COLORS[width],label=f'w={width}, published exploratory N=8/16')
        for n, marker in ((24,'o'),(32,'s')):
            r=next(r for r in rows if int(r['width'])==width and int(r['n'])==n)
            ax.scatter(n,float(r['cpu_speedup']),color=COLORS[width],marker=marker,s=60,
                       label=f'w={width}, N={n} {r["cohort"]}')
    ax.axhline(1,color='gray',lw=1)
    ax.set(xlabel='Matrix size N',ylabel='Whole-program CPU / accelerator time (×)',xticks=[8,16,24,32],
           title='Same-kernel CPU comparison; timing includes process setup and host work')
    ax.grid(alpha=.2);ax.legend(fontsize=7,ncol=2,loc='upper left')
    save(fig,'cpu_speedup_size')

    fig,axes=plt.subplots(2,2,figsize=(10,7))
    for col,n in enumerate((24,32)):
        group=[r for r in rows if int(r['n'])==n]
        ax=axes[0,col]
        for r in group:
            width=int(r['width']); dominated=r['dominated']=='True'
            ax.scatter(float(r['total_area_um2'])/1e6,float(r['offload_ns']),
                       color=COLORS[width],marker='x' if dominated else 'o',s=80,
                       label=f'w={width}'+(' (dominated)' if dominated else ''))
        ax.set(title=f'N={n}: {group[0]["cohort"]}',xlabel='Total modeled area (mm²)',ylabel='Offload latency (ns)')
        ax.legend(fontsize=8);ax.grid(alpha=.2)
        ax=axes[1,col]
        x=list(range(3))
        fu=[float(r['fu_area_um2'])/1e6 for r in group]
        mem=[float(r['mem_area_um2'])/1e6 for r in group]
        ax.bar(x,fu,label='Functional units',color='#355C7D')
        ax.bar(x,mem,bottom=fu,label='Memory model',color='#C6D7E5')
        ax.set(xlabel='Output-column width',ylabel='Modeled area (mm²)',xticks=x,xticklabels=['1','2','4'])
        ax.legend(fontsize=8)
    save(fig,'latency_area')
    print(OUT)


if __name__=='__main__':
    main()
