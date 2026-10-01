"""Render retained results at IEEE column sizes without changing raw data."""
import csv
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch
from paper_data import data_paths

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'paper/figures'
COLORS={1:'#0072B2',2:'#8A3FA0',4:'#D55E00'}
STYLES={1:'-',2:':',4:'--'}
MARKERS={1:'o',2:'^',4:'D'}
plt.rcParams.update({'font.family':'serif','font.size':9,'axes.titlesize':9,
                     'axes.labelsize':9,'xtick.labelsize':8,'ytick.labelsize':8,
                     'legend.fontsize':8,'pdf.fonttype':42,'ps.fonttype':42})


def read(path):
    with (ROOT/path).open() as f:return list(csv.DictReader(f))


def save(fig,name):
    fig.tight_layout(pad=.6)
    for ext in ('pdf','png'):
        fig.savefig(str(OUT/(name+'.'+ext)),dpi=200)
    plt.close(fig)


def architecture():
    fig,ax=plt.subplots(figsize=(7.16,3.35))
    ax.set(xlim=(0,7.16),ylim=(0,3.35));ax.axis('off')

    def box(x,y,w,h,label,fill='#F3F4F5',edge='#39434D',size=9):
        ax.add_patch(FancyBboxPatch((x,y),w,h,boxstyle='round,pad=0.025,rounding_size=0.045',
                                   facecolor=fill,edgecolor=edge,linewidth=1,zorder=2))
        ax.text(x+w/2,y+h/2,label,ha='center',va='center',fontsize=size,zorder=3)

    def arrow(start,end,style='<->',color='#39434D',dashed=False):
        ax.add_patch(FancyArrowPatch(start,end,arrowstyle=style,mutation_scale=9,
                                    linewidth=1.1,color=color,linestyle='--' if dashed else '-',
                                    shrinkA=2,shrinkB=2,zorder=4))

    ax.add_patch(FancyBboxPatch((3.05,1.12),3.82,1.68,
                               boxstyle='round,pad=0.025,rounding_size=0.06',
                               facecolor='#FFF5EA',edgecolor=COLORS[4],linewidth=1,zorder=1))
    ax.text(5.4,2.64,'Trace-driven accelerator',ha='center',fontsize=9)
    box(.25,2.08,1.8,.48,'Host CPU\nOut-of-order x86',fill='#E8F3FA',edge=COLORS[1])
    box(.25,1.28,1.8,.48,'Private L1 caches\n64 kB data · 32 kB instruction',fill='#E8F3FA',edge=COLORS[1],size=8)
    box(3.22,2.05,1.52,.45,'GEMM datapath\nw = 1, 2, or 4',fill='white',edge=COLORS[4])
    box(5.16,2.05,1.5,.45,'Request queue\n32 entries',fill='white',edge=COLORS[4])
    box(5.16,1.26,1.5,.47,'Coherent cache\n32 kB · four-way',fill='white',edge=COLORS[4])
    box(3.22,2.97,1.52,.3,'Kernel trace',fill='#F2ECF7',edge=COLORS[2])
    arrow((3.98,2.97),(3.98,2.5),style='->',color=COLORS[2],dashed=True)
    arrow((2.05,2.32),(3.22,2.32),color=COLORS[2],dashed=True)
    ax.text(2.64,2.49,'Invoke / return',ha='center',fontsize=8,color=COLORS[2])
    arrow((1.15,2.08),(1.15,1.76))
    arrow((4.74,2.27),(5.16,2.27))
    arrow((5.91,2.05),(5.91,1.73))
    ax.text(3.97,1.57,'A reuse across w columns\nMultiply–accumulate → C',
            ha='center',va='center',fontsize=8)
    ax.text(6.05,1.89,'Issue limit:\n1 / 2 / 4',ha='left',va='center',fontsize=7.5)
    box(.25,.57,6.41,.42,'Ruby MESI coherence  ·  Shared L2 cache (2 MB)',fill='#EDF0F2')
    arrow((1.15,1.28),(1.15,.99))
    arrow((5.91,1.26),(5.91,.99))
    box(2.23,.03,2.45,.32,'Main memory (1 GB DDR3)',fill='#EDF0F2')
    arrow((3.455,.57),(3.455,.35))
    # Keep the native page size while leaving the schematic's outer boxes clear.
    fig.subplots_adjust(left=.02,right=.98,bottom=.03,top=.98)
    for ext in ('pdf','png'):
        fig.savefig(str(OUT/('architecture.'+ext)),dpi=200)
    plt.close(fig)


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    architecture()
    data=data_paths()
    rows=read(data['width'])
    fig,axes=plt.subplots(1,2,figsize=(7.16,2.55))
    for ax,n in zip(axes,(24,32)):
        group=[r for r in rows if int(r['n'])==n]
        x=[int(r['width']) for r in group]
        ax.plot(x,[float(r['offload_ns']) for r in group],'o-',color=COLORS[1],label='Offload')
        ax.plot(x,[float(r['datapath_ns']) for r in group],'D--',color=COLORS[4],label='Datapath')
        ax.set(title=f'N={n}',
               xlabel='Output-column width',ylabel='Latency (ns)',xticks=[1,2,4])
        ax.margins(x=.08,y=.15);ax.legend();ax.grid(alpha=.2)
    save(fig,'width_latency')

    fig,ax=plt.subplots(figsize=(3.5,2.65))
    for width in (1,2,4):
        group=sorted([r for r in rows if int(r['width'])==width],key=lambda r:int(r['n']))
        x=[int(r['n']) for r in group]
        y=[float(r['cpu_speedup']) for r in group]
        ax.plot(x,y,marker=MARKERS[width],linestyle=STYLES[width],color=COLORS[width],
                label=f'w={width}',markersize=5,markerfacecolor='white',
                markeredgewidth=1.2,linewidth=1.6,zorder=5-width/4)
    ax.axhline(1,color='gray',lw=.8)
    ax.set(xlabel='Matrix size N',ylabel='CPU speedup (×)',xticks=[8,16,24,32])
    ax.margins(x=.09,y=.15);ax.grid(alpha=.2);ax.legend(loc='upper left')
    save(fig,'cpu_speedup_size')

    fig,axes=plt.subplots(2,2,figsize=(7.16,3.65))
    for col,n in enumerate((24,32)):
        group=[r for r in rows if int(r['n'])==n]
        ax=axes[0,col]
        for r in group:
            width=int(r['width']);dominated=r['dominated']=='True'
            ax.scatter(float(r['total_area_um2'])/1e6,float(r['offload_ns']),
                       color=COLORS[width],marker='x' if dominated else MARKERS[width],s=36,
                       label=f'w={width}'+(' (dominated)' if dominated else ''))
        ax.set(title=f'N={n}',
               xlabel='Total modeled area (mm²)',ylabel='Offload latency (ns)')
        ax.margins(x=.15,y=.18);ax.legend();ax.grid(alpha=.2)
        ax=axes[1,col]
        fu=[float(r['fu_area_um2'])/1e6 for r in group]
        memory=[float(r['mem_area_um2'])/1e6 for r in group]
        ax.bar(range(3),fu,color=COLORS[1],edgecolor='#243746',linewidth=.6,label='Functional units')
        ax.bar(range(3),memory,bottom=fu,color='#F0C75E',edgecolor='#695322',
               linewidth=.6,hatch='///',label='Memory')
        ax.set(xlabel='Output-column width',ylabel='Modeled area (mm²)',
               xticks=[0,1,2],xticklabels=['1','2','4'])
        ax.set_ylim(0,max(a+b for a,b in zip(fu,memory))*1.3)
        ax.legend(loc='upper center',ncol=2,fontsize=7,handlelength=1.2,columnspacing=.8)
    save(fig,'latency_area')

    bandwidth=read(data['bandwidth'])
    fig,axes=plt.subplots(2,2,figsize=(7.16,3.3))
    panels=[('offload_ticks','Offload time (µs)',1e-6),
            ('datapath_cycles','Datapath cycles',None),
            ('dcache_latency_ticks','Cache access latency (ns)',1e-9),
            ('dcache_queue_time_ticks','Cache queue time (ns)',1e-9)]
    for ax,(metric,ylabel,duration) in zip(axes.flat,panels):
        peak=0
        for width in (1,4):
            group=sorted([r for r in bandwidth if int(r['width'])==width],
                         key=lambda r:int(r['bandwidth']))
            values=[float(r[metric]) if duration is None else
                    float(r[metric])/float(r['sim_freq'])/duration for r in group]
            peak=max(peak,max(values))
            ax.plot([int(r['bandwidth']) for r in group],values,
                    marker=MARKERS[width],linestyle=STYLES[width],color=COLORS[width],label=f'w={width}')
        ax.set(xlabel='Issue limit (requests/cycle)',ylabel=ylabel,xticks=[1,2,4])
        ax.margins(x=.08,y=.16)
        ax.set_ylim(0,peak*1.18)
        ax.grid(axis='y',alpha=.2)
    axes[0,0].legend()
    save(fig,'bandwidth_sensitivity')
    print(OUT)


if __name__=='__main__':main()
