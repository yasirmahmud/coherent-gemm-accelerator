"""Plot a cache-bandwidth cohort after validating its raw evidence."""

import argparse
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from summarize_cache_bandwidth import BANDWIDTHS, verify, write_manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("cohort", type=Path)
    args = parser.parse_args()
    rows = verify(args.cohort)
    fig, axes = plt.subplots(2, 2, figsize=(9, 6.5), constrained_layout=True)
    panels = [("offload_ticks", "CPU-observed offload interval (µs)", 1e-6),
              ("datapath_cycles", "Aladdin datapath cycles", 1),
              ("dcache_latency_ticks", "Mean cache access latency (ns)", 1e-9),
              ("dcache_queue_time_ticks", "Mean cache queue time (ns)", 1e-9)]
    for ax, (metric, ylabel, duration) in zip(axes.flat, panels):
        for variant, label, color, marker in [("base", "Width 1", "#5271a3", "o"),
                                             ("tiled4", "Width 4", "#e68a40", "s")]:
            points = sorted([r for r in rows if r["variant"] == variant], key=lambda r: r["bandwidth"])
            values = [r[metric] if metric == "datapath_cycles" else r[metric] / r["sim_freq"] / duration
                      for r in points]
            ax.plot(BANDWIDTHS, values, marker=marker, color=color, label=label, linewidth=1.8)
        ax.set_xticks(BANDWIDTHS)
        ax.set_xlabel("Cache issue limit (requests per accelerator cycle)")
        ax.set_ylabel(ylabel)
        ax.grid(axis="y", alpha=0.2)
        ax.set_ylim(bottom=0)
        for spine in ("top", "right"):
            ax.spines[spine].set_visible(False)
    axes[0, 0].legend(frameon=False)
    fig.suptitle("N=24 GEMM: cache-bandwidth sensitivity\n32 kB cache; 32-entry queue; one fixed trace per kernel")
    for extension in ("png", "pdf", "svg"):
        target = args.cohort / ("bandwidth_sensitivity." + extension)
        fig.savefig(str(target), dpi=180)
        print(target)
    plt.close(fig)
    write_manifest(args.cohort)


if __name__ == "__main__":
    main()
