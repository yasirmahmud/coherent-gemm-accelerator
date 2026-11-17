# Five-minute presentation speaker notes

Present slides 1–9 in **5:00**. Slides 10–12 are Q&A backups, excluded from the recording.

Narration is also embedded in the PowerPoint. Rehearse to the target times.

| Slide | Time | Topic |
| --- | --- | --- |
| 1 | 0:00–0:15 | A complete framework for coherent GEMM tradeoffs |
| 2 | 0:15–1:00 | The tradeoff: useful parallelism versus resource cost |
| 3 | 1:00–1:30 | Notation: matrix size, tile width, and issue limit |
| 4 | 1:30–2:15 | We built the complete experimental framework |
| 5 | 2:15–2:45 | A completed study across five experiment families |
| 6 | 2:45–3:25 | The latency–area tradeoff changes with workload size |
| 7 | 3:25–4:00 | A wider design can also take longer to execute |
| 8 | 4:00–4:35 | The memory interface and host set the useful gain |
| 9 | 4:35–5:00 | What our completed study established |

## 1. A complete framework for coherent GEMM tradeoffs

We built a complete framework for coherent matrix-multiplication accelerators: kernels, host harnesses, simulator extensions, automated experiments, and validation. Our study measures performance gains against hardware cost and application behavior.

Sources:

- [paper/final_paper.tex](../paper/final_paper.tex)
- [docs/PAPER_EXPERIMENTS.md](../docs/PAPER_EXPERIMENTS.md)

## 2. The tradeoff: useful parallelism versus resource cost

A narrow accelerator computes one output at a time. A wider design shares one input across several output sums, reducing repeated operations and exposing parallel arithmetic. The other side is concurrent resource demand: more live sums and different scheduling can require more hardware. The cache interface and host still have to support the work. We therefore measure three outcomes together: offload latency, modeled area, and application execution time. Our objective is to identify useful designs, rather than maximize width. The measurements show both sides: lower first-call latency, higher area in some workloads, and a repeated-call case where the wider design is slower.

Sources:

- [proposal/proposal.tex](../proposal/proposal.tex)
- [paper/final_paper.tex](../paper/final_paper.tex)
- [results/paper_runs/paper_local_20261001/analysis/width_summary.csv](../results/paper_runs/paper_local_20261001/analysis/width_summary.csv)
- [results/diagnostics/paper_local_20261001_warm/summary.csv](../results/diagnostics/paper_local_20261001_warm/summary.csv)

## 3. Notation: matrix size, tile width, and issue limit

Capital A and B are the input matrices; C is their product. N is the number of rows and columns in each square matrix. The picture uses eight. Lowercase w counts adjacent outputs computed together: four highlighted cells mean width four. Lowercase b limits requests issued per accelerator cycle. Two arrows illustrate b equal to two. Uppercase B is a matrix, while lowercase b is an interface setting.

Sources:

- [proposal/proposal.tex](../proposal/proposal.tex)
- [docs/ARCHITECTURE.md](../docs/ARCHITECTURE.md)

## 4. We built the complete experimental framework

We implemented every project-specific layer, using gem5-Aladdin as the simulation engine. We wrote the baseline and two wider GEMM kernels, integrated CPU invocation and reference checking, and enforced a bounded request queue with retry handling. We added a passive observer that links optimized graph operations to accepted memory requests. On top of that system, we built isolated experiment runners, segmented timing, configuration and artifact checks, and automated analysis. The observer was verified against the reference simulator. The result is a reproducible framework that connects source code, the coherent memory interface, correctness, latency, and modeled resource cost.

Sources:

- [docs/PAPER_EXPERIMENTS.md](../docs/PAPER_EXPERIMENTS.md)
- [docs/MECHANISM_DIAGNOSTICS.md](../docs/MECHANISM_DIAGNOSTICS.md)
- [patches/bounded_queue_gemm_pilot.patch](../patches/bounded_queue_gemm_pilot.patch)
- [patches/passive_graph_counters.patch](../patches/passive_graph_counters.patch)

## 5. A completed study across five experiment families

We completed one hundred seven simulator executions across five experiment families. Sixty runs evaluate kernel width and matrix size. Twenty test memory-interface capacity. Twelve verify the graph observer, and twelve examine repeated invocations. Three independent-input tests establish the trace model’s correctness boundary. Together, these experiments separate arithmetic reuse, system latency, resource cost, and execution history. The framework retains the programs, traces, configurations, checks, and generated results.

Sources:

- [docs/PAPER_EXPERIMENTS.md](../docs/PAPER_EXPERIMENTS.md)
- [results/paper_runs/paper_local_20261001/analysis/suite_validation.json](../results/paper_runs/paper_local_20261001/analysis/suite_validation.json)

## 6. The latency–area tradeoff changes with workload size

This plot shows the design tradeoff directly: lower latency and lower area are preferable. At size twenty-four, width four reduces offload latency by eleven point eight percent and slightly reduces modeled area. At size thirty-two, width four reduces latency by twenty-five point one percent, but increases modeled area by twenty-seven point seven percent. The compact width-one design and the faster width-four design therefore remain distinct choices. Width two is dominated by width four at size thirty-two. These results show why we evaluate complete design points instead of treating additional width as a free improvement.

Sources:

- [results/paper_runs/paper_local_20261001/analysis/width_summary.csv](../results/paper_runs/paper_local_20261001/analysis/width_summary.csv)
- [paper/width_table.tex](../paper/width_table.tex)

## 7. A wider design can also take longer to execute

The repeated-call experiment gives a direct reversal. These are unchanged inputs at size twenty-four in the timed harness. Width four reduces first-invocation time by eleven point nine percent. On the second invocation, widths one and two take eight hundred nineteen nanoseconds, while width four takes eight hundred thirty-eight: two point three percent slower. Execution history and scheduling change the result, so the fastest first-call design need not win on a later call.

Sources:

- [results/diagnostics/paper_local_20261001_warm/summary.csv](../results/diagnostics/paper_local_20261001_warm/summary.csv)
- [paper/warm_table.tex](../paper/warm_table.tex)

## 8. The memory interface and host set the useful gain

Our system measurements show two constraints. At size twenty-four, tightening the request interface reduces the width-four benefit from eleven point eight percent to four point six percent. The observer confirms that merged loads can keep cache traffic unchanged. At size thirty-two, a twenty-nine point eight percent datapath reduction becomes twenty-five point one percent offload reduction and only zero point four one percent whole-program improvement. Local improvements must therefore be measured at the application boundary.

Sources:

- [results/cache_bandwidth/paper_local_20261001_bandwidth/summary.csv](../results/cache_bandwidth/paper_local_20261001_bandwidth/summary.csv)
- [results/paper_runs/paper_local_20261001/analysis/width_summary.csv](../results/paper_runs/paper_local_20261001/analysis/width_summary.csv)
- [results/diagnostics/paper_local_20261001_graph/summary.csv](../results/diagnostics/paper_local_20261001_graph/summary.csv)

## 9. What our completed study established

We delivered a complete validated framework and evaluated three accelerator designs across workloads, memory interfaces, and invocation histories. We measured faster offloads, workload-dependent area costs, and a case where wider execution is slower. The design rule is to choose width for the workload and system, using latency, modeled area, and application benefit together.

Sources:

- [paper/final_paper.tex](../paper/final_paper.tex)
- [docs/PAPER_EXPERIMENTS.md](../docs/PAPER_EXPERIMENTS.md)

## 10. Fewer graph loads do not imply fewer cache requests (Q&A backup)

At N equal to twenty-four and issue limit four, optimized A loads decrease from thirteen thousand eight hundred twenty-four to three thousand four hundred fifty-six. Accepted requests remain thirty-six A loads, thirty-six B loads, and five hundred seventy-six C stores for each width. Cache-line merging explains why graph-load reduction does not imply request reduction. The passive observer and reference simulator produce matching simulated statistics.

Sources:

- [results/diagnostics/paper_local_20261001_graph/summary.csv](../results/diagnostics/paper_local_20261001_graph/summary.csv)
- [paper/graph_table.tex](../paper/graph_table.tex)

## 11. Appendix: measurement definitions (Q&A backup)

Offload time covers the reset before invocation through accelerator completion and host return. Datapath time is the modeled cycle count times one nanosecond. Area combines functional-unit and memory estimates before RTL. Whole-program comparisons include setup and host work. Within each workload, effective configurations are controlled. The issue limit changes allowed requests per accelerator cycle, not modeled physical cache ports. The one hundred seven executions represent experiment coverage, not statistical repetitions.

Sources:

- [paper/final_paper.tex](../paper/final_paper.tex)
- [results/paper_runs/paper_local_20261001/analysis/suite_validation.json](../results/paper_runs/paper_local_20261001/analysis/suite_validation.json)
- [paper/experiment_data.json](../paper/experiment_data.json)

## 12. Appendix: repeated-call correctness and scope (Q&A backup)

All per-call checker outputs pass when inputs match trace generation. Timed repeated runs use the paired traces and a final checksum; their intermediate outputs are not individually checked. Independent mutations produce twenty, twenty-four, and nineteen mismatches across calls at every width and are excluded from performance comparisons. Checking between calls changes cache history, so checker timing is distinct from timed-harness timing. The second-invocation slowdown on the main slide uses unchanged inputs in the timed harness.

Sources:

- [results/diagnostics/paper_local_20261001_warm/summary.csv](../results/diagnostics/paper_local_20261001_warm/summary.csv)
- [results/paper_runs/paper_local_20261001/analysis/independent_mutation.json](../results/paper_runs/paper_local_20261001/analysis/independent_mutation.json)
- [paper/warm_table.tex](../paper/warm_table.tex)