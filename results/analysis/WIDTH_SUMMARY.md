# Main width comparison

N=24 uses the published cohort; N=32 uses the recovered cohort.
All CPU and accelerator full checks pass; ROI/invocation checksums and host work match within each size.
Historical identity limits are in the provenance inventory. Area is from the full correctness stage.

| N | Width | Datapath (ns) | Offload (ns) | CPU speedup, whole program | FU (µm²) | Memory (µm²) | Dominated in offload/total area? |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 24 | 1 | 1452 | 2680 | 1.164× | 598,362 | 802,977 | True |
| 24 | 2 | 1257 | 2508 | 1.164× | 598,362 | 802,977 | True |
| 24 | 4 | 1133 | 2361 | 1.173× | 593,769 | 802,977 | False |
| 32 | 1 | 2827 | 4132 | 1.500× | 443,981 | 802,977 | False |
| 32 | 2 | 2268 | 3508 | 1.492× | 793,287 | 802,977 | True |
| 32 | 4 | 1984 | 3224 | 1.524× | 789,267 | 802,977 | False |

Dominance is assessed within each size/cohort with printed modeled total area and offload ticks.
At N=24 width 4 dominates widths 1 and 2. At N=32 widths 1 and 4 remain choices:
width 1 uses less modeled area; width 4 is faster. Width 2 is dominated by width 4.
These are pre-RTL estimates with characterization and historical provenance limits, not universal rankings.
