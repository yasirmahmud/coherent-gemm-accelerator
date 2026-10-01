# Four-column GEMM on a coherent gem5-Aladdin accelerator

A reproducible **fixed-trace** study of a GEMM accelerator attached to an
out-of-order x86 CPU through gem5-Aladdin's Ruby coherent memory system. The
base kernel computes one output column at a time. The extension computes four
adjacent outputs together so one load from A feeds four accumulators.

The reported single-invocation runs passed full output checks at N=24 and N=32.
The extension reduced modeled accelerator cycles by **21.97% and 29.82%** and
the measured host offload interval by **11.90% and 22.56%**, respectively.
Whole-program improvement over the original accelerator was **0.47% and
1.18%**. These are simulator measurements on two small workloads, not a
general or silicon speedup claim. See [results and limitations](docs/RESULTS.md).

## 1. How to build and run

Requirements: Linux or WSL2 with a working Docker daemon, Git, Python 3, an
x86-64 host, Internet access for the first setup, and roughly 40 GB free disk
(the uncompressed container image alone is about 32 GB).
The container supplies LLVM, SCons, gem5, Aladdin, and their dependencies.
There are no proprietary EDA tools. The Docker image is pinned by digest;
upstream source and submodule commits are pinned in `scripts/setup_inside.sh`.

```bash
git clone https://github.com/yasirmahmud/coherent-gemm-accelerator.git
cd coherent-gemm-accelerator
bash scripts/setup.sh
bash scripts/run.sh 24 all
bash scripts/run.sh 32 all
python3 scripts/summarize.py
```

`run.sh` writes logs and `stats.txt` into `results/` and validates the expected
correctness markers. `all` performs full output checks, performance ROI runs,
and segmented invocation timing for both kernels. N=32 `all` can take tens of
minutes because Aladdin schedules a large graph for each stage; the initial
gem5 compilation can also take a while. The last command
checks the raw evidence and rewrites `results/validated_summary.csv`. For a
shorter smoke test, use `bash scripts/run.sh 24 full`. Windows users should run
these commands **inside WSL**, from the cloned repository's `/mnt/...` path.

See [BUILD.md](docs/BUILD.md) for exact versions, individual stages,
troubleshooting, and measurement boundaries. The
[validation record](docs/VALIDATION.md) distinguishes clean-build checks from
previously saved N=32 evidence.

## 2. What has been done

- Built the open-source [gem5-Aladdin](https://github.com/harvard-acc/gem5-aladdin)
  simulator with x86 `DerivO3CPU`, Ruby `MESI_Two_Level_aladdin`, Aladdin
  `HybridDatapath`, and a 32 kB coherent accelerator cache.
- Implemented the original one-column GEMM and the four-column kernel under
  `benchmarks/`. Kept CPU, clock, memory, cache, matrix input, and host
  invocation protocol fixed across the main comparison.
- Applied the finite queue/retry simulator patch in `patches/`, ran full
  correctness checks, matched ROI checksums, compared host instruction counts,
  and saved raw logs/configurations for both N=24 and N=32.
- Measured accelerator cycles, whole-program ticks, and reset-to-return
  offload ticks. `scripts/summarize.py` derives the CSV directly from logs.
- Ran a repeated-invocation diagnostic with CPU-modified input. It
  originally **failed** with 19 accelerator output mismatches at N=24
  (`results/diagnostics/repeated_input_n24/`, kept as historical evidence).
  Root-caused to a trace/harness mismatch (the trace generator only ever
  recorded one accelerator invocation, not `REPS`); fixed, and now passes
  with 0 mismatches for both kernels at REPS=2
  (`results/diagnostics/repeated_input_n24_fixed/`). This validates input
  changing *between* discrete accelerator calls with a full retrace per
  call, using a predetermined mutation known at trace time — not an
  arbitrary runtime CPU write, and not input changing mid-invocation.
  Invocation 2's *timing* (cycle count, area) is not yet understood — see
  [RESULTS.md](docs/RESULTS.md) — and must not be read as a steady-state
  per-call cost.
- Added exploratory data beyond the validated N=24/N=32 pair: N=8 and N=16
  (same correctness checks, kept separate from the validated pipeline), and
  a tile-width-2 variant at N=24 for a controlled 1-vs-2-vs-4 ablation.
  Findings are mixed, not uniformly positive: the four-column benefit is
  size-dependent (weak-to-negative at N=8) and area cost tracks problem size
  more than tile width. Full detail, corrected interpretations, and open
  questions in [RESULTS.md](docs/RESULTS.md).

## 3. What to do next

The added [cache-bandwidth sensitivity study](docs/CACHE_BANDWIDTH.md) is
complete at N=24: widths 1/4 at issue limits 1/2/4, with all six full checks
passing. Four-column offload reductions are **4.67%, 7.27%, and 12.03%**
within the new cohort. Reproduce with `bash scripts/run_cache_bandwidth.sh`;
raw evidence, validated tables, and figures are in
[`results/cache_bandwidth/n24_20260930/`](results/cache_bandwidth/n24_20260930/SUMMARY.md).
The bandwidth extension is included in the two-page proposal.

1. Harden repeated-run validation to reject missing calls, timing intervals,
   and trace-hash metadata. The independent runtime-mutation test has already
   failed (20/24/19 mismatches at N=24); retain that correctness limit. Direct
   measurement of warm-call behavior remains useful before citing its cost.
2. Preserve cohort provenance in cost comparisons. A controlled N=24
   full/ROI order test did not reproduce the historical MEM Area discrepancy;
   the original differing files' cause remains unknown. Validate modeled
   energy/energy-delay analysis before reporting it as a cost result.
3. Generate summaries and plots for the complete width-1/2/4 study. N=32
   width-2 results and a complete local N=24/N=32 reproduction were recovered
   from ignored artifacts on 2026-09-30 and preserved separately. See the
   [experiment inventory](docs/EXPERIMENT_INVENTORY.md) for available evidence
   and remaining tasks. Width 8, larger N, and inference remain extensions.
4. Write the final research report with the bottleneck, mechanism, cost,
   methodology, figures, explanation of results, and limitations.

The [next-steps plan](docs/NEXT_STEPS.md) gives testable milestones and stop
conditions. The current evidence supports a narrowly scoped dataflow study;
it does **not** yet validate a broad dynamic CPU/AI accelerator co-design.

The [immediate next steps](docs/IMMEDIATE_NEXT_STEPS.md) prioritize the
remaining proposal gaps and bounded experiments that could strengthen its
mechanism and reproducibility evidence.

## 4. Course eligibility and proposal scope

The course asks for one focused empirical question, a well-defined baseline,
a specific mechanism, hardware overhead, named tools/configuration, statistics,
plots, and an explanation of why the result occurred. The proposed question
here is: **Can output-column reuse reduce the offload latency of a coherent
GEMM accelerator enough to justify the extra hardware cost?**

This repo supplies accessible open-source designs/tools and preliminary
positive evidence. [COURSE_ELIGIBILITY.md](docs/COURSE_ELIGIBILITY.md) maps
the course requirements to current evidence and remaining work. The professor
must agree to the proposal scope; this repository cannot guarantee a grade.
Confirm the official proposal deadline and submission route on Canvas.

## Repository map

| Path | Contents |
| --- | --- |
| `benchmarks/gemm_acp_pilot/` | One-column baseline C kernel and configs |
| `benchmarks/gemm_tiled2/` | Two-column C kernel and matched configs (tile-width ablation) |
| `benchmarks/gemm_tiled4/` | Four-column C kernel and matched configs |
| `patches/` | Aladdin finite-queue/retry patch |
| `scripts/` | Pinned setup, runs, and evidence validator |
| `results/` | Raw logs, stats/config files, summary CSV, diagnostic |
| `docs/` | Build, results, course scope, next steps, upstream notes |

This package contains our benchmark, patch, scripts, and recorded results. It
fetches upstream source at pinned commits and does not redistribute course
lectures or transcripts. See [UPSTREAM.md](docs/UPSTREAM.md) for provenance and
upstream license links.

Completed the [immediate execution checklist](docs/IMMEDIATE_NEXT_STEPS.md).
The [mechanism diagnostics](docs/MECHANISM_DIAGNOSTICS.md) link the passive
observer, strict repeated-call checks, aggregate cache analysis, historical
provenance inventory and reproducible width figures. The [final paper](paper/final_paper.pdf)
retains negative findings and uses the fresh experiment suite described below.

The [final IEEE paper](paper/final_paper.pdf) uses the freshly executed
[complete paper experiment suite](docs/PAPER_EXPERIMENTS.md), including all
three widths at all four matrix sizes. Its data selection and numerical
claims are generated from validated retained evidence.
