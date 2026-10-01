# Main width comparison

One fresh suite covers N=8/16/24/32 and widths 1/2/4; all traces and guests were generated for this suite.
All CPU and accelerator full checks pass; ROI/invocation checksums and host work match within each size.
All effective configurations match within each stage/size after normalizing output paths and kernel names. Retained trace and guest identities are verified.

| N | Width | Datapath (ns) | Offload (ns) | CPU speedup, whole program | FU (µm²) | Memory (µm²) | Dominated in offload/total area? |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 8 | 1 | 276 | 1370 | 0.871× | 202,006 | 802,977 | True |
| 8 | 2 | 260 | 1354 | 0.895× | 197,030 | 802,977 | False |
| 8 | 4 | 250 | 1344 | 0.875× | 200,475 | 802,977 | False |
| 16 | 1 | 765 | 2016 | 0.973× | 389,622 | 802,977 | False |
| 16 | 2 | 636 | 1887 | 0.981× | 397,313 | 802,977 | False |
| 16 | 4 | 575 | 1826 | 0.953× | 400,376 | 802,977 | False |
| 24 | 1 | 1452 | 2703 | 1.163× | 598,362 | 802,977 | True |
| 24 | 2 | 1257 | 2508 | 1.163× | 598,362 | 802,977 | True |
| 24 | 4 | 1133 | 2384 | 1.171× | 593,769 | 802,977 | False |
| 32 | 1 | 2827 | 4306 | 1.499× | 443,981 | 802,977 | False |
| 32 | 2 | 2268 | 3508 | 1.491× | 793,287 | 802,977 | True |
| 32 | 4 | 1984 | 3224 | 1.509× | 789,267 | 802,977 | False |

Dominance is assessed within each size/cohort with printed modeled total area and offload ticks.
At N=24 width 4 dominates widths 1 and 2. At N=32 widths 1 and 4 remain choices:
width 1 uses less modeled area; width 4 is faster. Width 2 is dominated by width 4.
These are pre-RTL estimates for the tested trace-driven workloads, not universal rankings.
