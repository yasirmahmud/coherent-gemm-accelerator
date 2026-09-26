# Next steps and decision gates

## Gate 1: dynamic input correctness — RESOLVED (2026-09-26)

Reproduced the N=24 repeated-invocation failure in a small test (REPS=2,
`-DN=24`, both kernels). Root cause was not Aladdin's trace address/value
handling or gem5-Aladdin host mapping, but the trace-generation build path:
`LLVM_TRACE` in `benchmarks/*/​*.c` called `gemm_kernel()` once regardless of
`REPS`, so the recorded `dynamic_trace.gz` only ever covered one accelerator
invocation. The simulated harness (`GEM5_HARNESS`) called
`invokeAcceleratorAndBlock()` `REPS` times against CPU-modified input, so
invocation 2+ replayed against an exhausted trace, did zero real work, and
silently compared stale invocation-1 output against a fresh CPU reference
computed on the updated input.

Fix: made `LLVM_TRACE` loop `REPS` times with the same input mutation as the
harness (`benchmarks/gemm_acp_pilot/gemm_acp_pilot.c`,
`benchmarks/gemm_tiled4/gemm_tiled4.c`). Both failing and passing logs are
kept: `results/diagnostics/repeated_input_n24/` (pre-fix, 19 mismatches on
both kernels) and `results/diagnostics/repeated_input_n24_fixed/` (post-fix,
0 mismatches on both kernels, real second-invocation DDDG confirmed). The
fix does not change any `REPS=1` (default) behavior — verified bit-identical
against a pre-fix rebuild on the same host, excluding host wall-clock stats.

Remaining scope note: this validates CPU-modified input *between* discrete
accelerator calls with a full re-trace per call. It does not by itself
validate input changing *during* a single accelerator invocation, or a
design where re-tracing per call is impractical (e.g. very large/variable
inputs) — if the course proposal wants a stronger "fully dynamic" claim,
that gap should be stated explicitly rather than assumed closed.

## Gate 2: hardware cost — partially resolved (2026-09-26)

"Repeat the N=24/N=32 area estimates ... identify why N=24 changed despite
reproducible timing": **it didn't, on closer audit.** Every true same-stage,
same-input rerun of base_n24 on record (`fair_results`, `invocation_results`,
the pre-fix repeated-input diagnostic, and an independent from-scratch
rebuild on a different host) reports identical area. The only differing
number came from `roi_results`, which runs a genuinely different (shorter,
ROI-bounded) trace — comparing it to `fair`/`invocation` was never a fair
same-config rerun. So area for the published REPS=1 N=24/N=32 numbers is not
exploratory on repeatability grounds; see `docs/RESULTS.md` for the full
audit.

New, separate, still-open finding: area is *not* stable across repeated
invocations of the same kernel within one gem5 run — FU Area grows
substantially from invocation 1 to invocation 2 (base_n24: +39%, tiled4_n24:
+17%) while MEM Area stays constant (`results/diagnostics/repeated_input_n24_fixed/`).
This only became visible once Gate 1's fix made a real second invocation
possible, and does not affect any already-published number (all REPS=1).
Before any future work reports an area number from a repeated-invocation or
"dynamic" scenario, isolate this mechanism (candidates: Aladdin's
per-invocation resource-scheduling state not resetting between calls, or the
finite-queue patch's cross-call queue/state bookkeeping) and confirm it's
either fixed or bounded.

Add power only after its tool output has been checked for repeatability. A
four-column design that only wins by excessive hardware cost is not a
strong result.

## Gate 3: broader experiment

Try additional valid tile widths and input sizes, or one representative
inference layer that the trace/scheduler can finish within the deadline.
Measure offload ticks, accelerator cycles, CPU comparator ticks, queue/cache
traffic, and area. Use identical CPU and memory settings and note any tool
limits. Repeat key points and produce plots with units and raw-data links.

## Gate 4: course deliverables

Agree the bounded research question and deliverables with the instructor.
Write a proposal that names the exact CPU, coherence protocol, accelerator,
baseline, mechanism, overhead, and outcome metrics. The final report must
include figures, explanation of why the latency changed, failed variants,
reproducibility instructions, and an honest account of the dynamic-input
limitation if unresolved. Confirm deadline and submission instructions in
Canvas rather than relying on the lecture's approximate date.

Suggested safe proposal scope: **GEMM output-column reuse in the existing
gem5-Aladdin coherent private-cache accelerator**, with offload latency and
area tradeoff as the primary study. A general OoO CPU plus dynamically
coherent AI accelerator co-design remains a stretch goal pending Gate 1.
