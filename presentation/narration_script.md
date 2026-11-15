# Presentation narration (~5:00)

Narration used for `GEMM_Accelerator_Presentation.mp4`. Timestamps are where each slide starts in the video.

## Slide 1 — Title  `[0:00]`

Hi, we are Yasir, Rasin and Mohyeu. Our project studies output-column reuse in a coherent GEMM accelerator: how computing several output columns at once changes accelerator latency and cost, and how the memory system shapes that benefit.

## Slide 2 — The problem and why it matters  `[0:15]`

The problem: matrix multiplication, or GEMM, is the core of machine learning and scientific computing, and accelerators are built to speed it up. But an accelerator does not run alone. It shares caches, memory and the host CPU, so a speedup inside the accelerator may not survive at the system level. Pre-RTL simulation lets us study this before building hardware. As a preview: our improvement cuts offload time by 25 percent at N equals 32, yet whole-program time falls by under half a percent.

## Slide 3 — The architecture  `[0:47]`

We modeled the system in gem5-Aladdin, which couples full CPU and coherent memory simulation with Aladdin's pre-RTL accelerator model. An out-of-order x86 host invokes a trace-driven GEMM accelerator, whose requests pass through a 32-entry queue into a 32 kilobyte coherent cache that shares a MESI memory system with the CPU. We vary two things: the output tile width, and how many cache requests the accelerator may issue per cycle.

## Slide 4 — What we studied  `[1:16]`

We ran four controlled experiments: a width and size study, four matrix sizes by three widths, each compared against the CPU; an issue-limit study at N equals 24; a passive observer linking graph operations to actual cache requests; and a repeated-call study. Every result is checked element by element against a CPU reference, and all 107 simulator runs were validated.

## Slide 5 — Our improvement: wider output tiles  `[1:41]`

Our improvement is the wider output tile. Every output needs values from matrix A. With width 1, the accelerator computes one output at a time, fetching the same A value again for every output. With width 4, it computes four neighbouring outputs together and fetches A only once. The benefits: fewer loads, more parallel work, and exactly the same answer. The costs: more multipliers and chip area, more simultaneous requests that a narrow memory interface may not keep up with, and diminishing returns, because the fixed cost of calling the accelerator does not shrink. We measured when the benefits outweigh the costs.

## Slide 6 — Result 1: wider tiles cut offload latency  `[2:18]`

First result: wider tiles reduce offload latency at every size, and the benefit grows with the matrix. Width 4 cuts offload latency by about 12 percent at N equals 24, and 25 percent at N equals 32. Most of the gain comes from going from width 1 to width 2.

## Slide 7 — Result 2: fewer loads ≠ fewer cache requests  `[2:37]`

Second, our most surprising result. Width 4 really does cut A loads by four times, in the source and in the dependence graph. But the cache requests are identical for every width: 36 A loads, 36 B loads and 576 C stores, because the request queue already merges loads to the same cache line. So the speedup comes not from less memory traffic, but from better scheduling: fewer cycles stalled at the issue limit and at a full queue.

## Slide 8 — Result 3: the memory interface limits the gain  `[3:04]`

Third, the memory interface matters. With one cache request per cycle, width 4 is only 4.6 percent faster than width 1. With two, 7.1 percent; with four, 11.8 percent. A narrow interface cannot serve the extra parallel requests. We also found that offload time always equals datapath time plus about 1.25 microseconds of fixed overhead.

## Slide 9 — Result 4: workload size decides the payoff  `[3:29]`

Fourth, the system view. Against the CPU, the accelerator loses at N equals 8 and 16, and wins at 24 and 32, with speedups of 1.17 and 1.51. At whole-program level, width 4 saves under half a percent, because setup and host work dominate. And area depends on size: at 24, width 4 is fastest and no larger; at 32, width 1 is smallest while width 4 is fastest.

## Slide 10 — Proposal vs. what we delivered  `[3:57]`

Compared with our proposal, every planned experiment was completed: the width study, the issue-limit study, the CPU comparison, and the timing and area analysis. We went further with CPU comparisons for all widths, the passive observer, and the repeated-call study. Our main hypothesis was revised, since fewer loads did not mean less traffic. For the final report, we will add the complete cache-counter table and a controlled rebuild check of area repeatability.

## Slide 11 — Conclusions  `[4:25]`

To conclude: output-column reuse works, cutting offload latency by up to 25 percent. But it works by improving request scheduling, not by reducing memory traffic. A narrow memory interface removes most of the benefit, and whole-program gains are far smaller than local ones. So tile width should be chosen together with workload size, the memory interface, and whole-program performance. Our study is limited to small integer GEMM in a pre-RTL model. Thank you, and we look forward to your questions in the discussion thread.
