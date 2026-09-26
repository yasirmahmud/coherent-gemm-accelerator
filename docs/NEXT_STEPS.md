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

## Gate 2: hardware cost

Repeat the N=24/N=32 area estimates under identical builds and inputs;
identify why N=24 changed despite reproducible timing. Report area alongside
offload latency. Add power only after its tool output has been checked for
repeatability. A four-column design that only wins by excessive hardware
cost is not a strong result.

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
