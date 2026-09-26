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
- Ran a repeated-invocation diagnostic with CPU-modified input. It **failed**
  with 19 accelerator output mismatches at N=24, so dynamic input coherence is
  **not established** by this package.

## 3. What to do next

1. Fix or redesign tracing so repeated accelerator calls consume CPU-updated
   input correctly. Gate any claim about dynamic coherence on a full output
   check after each call.
2. Investigate Aladdin area-report variation, then quantify area and power
   costs against latency under identical settings.
3. Expand to more matrix shapes or a representative inference kernel, include
   an ablation of output tile width, and repeat/plot the comparisons.
4. Write the final research report with the bottleneck, mechanism, cost,
   methodology, figures, explanation of results, and limitations.

The [next-steps plan](docs/NEXT_STEPS.md) gives testable milestones and stop
conditions. The current evidence supports a narrowly scoped dataflow study;
it does **not** yet validate a broad dynamic CPU/AI accelerator co-design.

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
| `benchmarks/gemm_tiled4/` | Four-column C kernel and matched configs |
| `patches/` | Aladdin finite-queue/retry patch |
| `scripts/` | Pinned setup, runs, and evidence validator |
| `results/` | Raw logs, stats/config files, summary CSV, diagnostic |
| `docs/` | Build, results, course scope, next steps, upstream notes |

This package contains our benchmark, patch, scripts, and recorded results. It
fetches upstream source at pinned commits and does not redistribute course
lectures or transcripts. See [UPSTREAM.md](docs/UPSTREAM.md) for provenance and
upstream license links.
