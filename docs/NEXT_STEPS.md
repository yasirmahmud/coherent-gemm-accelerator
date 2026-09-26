# Next steps and decision gates

## Gate 1: dynamic input correctness

Reproduce the N=24 repeated-invocation failure in a small test, then inspect
Aladdin's trace address/value handling and gem5-Aladdin host mapping. Change
one mechanism at a time. A fix is accepted only when the CPU modifies an
input between calls and every accelerator output matches a fresh CPU GEMM
reference. Keep both the failing and passing logs. If this cannot be solved in
the course window, constrain the approved proposal to a fixed-trace dataflow
study and state that limit explicitly.

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
