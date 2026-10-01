# Immediate next steps to strengthen the proposal

Updated 2026-09-30. Execution is complete for steps 0–5 under the documented
alternatives. Checked items are implemented unless explicitly labeled skipped
or conditional; skips are recorded without claiming the underlying experiment
was performed. See [execution evidence](MECHANISM_DIAGNOSTICS.md) and the
[completion audit](IMMEDIATE_COMPLETION_AUDIT.md). The [proposal audit](PROPOSAL_AUDIT.md) preserves the pre-execution
claim review. The core width and bandwidth experiments are already complete;
do not rerun them merely to obtain a more favorable result.

Keep measured results out of the proposal and present its scope as planned
work. Keep actual results, including negative findings, in the experiment
records. A useful experiment need not improve every metric.

## Recommended order

| Priority | Task | Purpose | Effort / risk | Proposal status |
| --- | --- | --- | --- | --- |
| 0 | Tighten the two unverified mechanism claims | Align promises with existing evidence immediately | Small writing change / low | Existing commitments |
| 1 | Count optimized operations and accepted memory requests | Explain what the tiling transformation changes | Bounded instrumentation / moderate | Closes the graph-to-interface gap |
| 2 | Investigate cache-miss origins | Support or narrow the promised cache/coherence explanation | Instrumentation and controlled diagnostics / moderate | Closes the miss-classification gap |
| 3 | Recover missing historical provenance | Make all comparisons independently auditable | Recovery first / low; selective reruns only if needed | Existing reproducibility commitment |
| 4 | Harden repeated-call validation and isolate warm-call effects | Prevent false passes and unsupported warm-timing claims | Small validator fix, then diagnostics / low–moderate | Supports repeated-call diagnostics |
| 5 | Complete promised summaries and figures | Present existing evidence consistently | Analysis only / low | Can follow the technical work |

### 0. Align the proposal before adding experiments

- [x] For the graph claim, either perform task 1 or change the commitment to
  comparing optimized graph totals and measured cache counters. Do not claim
  an established operand-specific causal mechanism yet.
- [x] For compulsory/conflict/coherence effects, either perform task 2 or
  promise aggregate cache/coherence measurements with explicit attribution
  limits. Existing aggregate misses do not classify their causes.
- [x] Scope complete retained source/binary/trace provenance to the new
  bandwidth cohort until historical gaps are recovered.

**Execution evidence:** graph/counter claims are scoped; cache-miss categories
are remaining diagnostic work rather than promised established causes.
Historical provenance scope is explicit. `proposal/proposal.pdf` rebuilds to
two pages with no measured-result disclosures.

**Done when:** every technical promise has completed supporting evidence
or is explicitly identified as remaining analysis. Rebuild the PDF and
verify that it remains two pages without measured-result disclosures.

### 1. Resolve graph-to-memory attribution

**Question:** which source-level reuse changes survive optimization, and
which become different cache requests?

- [x] Inspect retained optimization logs and model outputs first. Record
  what they already expose and what requires instrumentation.
- [x] Add passive counters around graph optimization: loads/stores by array
  A/B/C, arithmetic operations, and live/connected operation counts before
  and after optimization. Distinguish GEMM accumulation from index/address
  arithmetic; do not interpret every integer add as a MAC.
- [x] Count accepted cache requests separately from returned requests,
  retries, and merged operations, with per-array labels where available.
  Existing `total_dcache_loads/stores` count returned cache operations.
- [x] Record issue-limit blocked attempts and blocked cycles separately;
  multiple node polls in one cycle must not inflate a cycle count.
- [x] Use one N=24 cohort with widths 1/2/4 at issue limit 4. Reuse each
  kernel's trace across the instrumented and reference runs where possible.
  Preserve the existing simulator and build the diagnostic version separately.
- [x] Confirm that adding counters preserves full correctness, datapath
  cycles, and the controlled simulated timing. Save the source patch,
  executable identity, trace identities, configurations, and raw counters.

**Deliverable:** a table connecting source operations, optimized graph
operations, and accepted/returned memory operations for each width.

**Execution evidence:** [diagnostic cohort](../results/diagnostics/graph_n24/ANALYSIS.md),
CSV, validation, source patch, simulator/guest identities, shared traces,
configurations, raw counters and manifest. All simulated statistics and
per-array accepted/returned totals reconcile. Counters distinguish successful
retry sends from rejected initial sends; unsuccessful retry notifications
are outside that reported count.

**Done when:** the table explains what is observed without assuming fewer
source loads imply fewer requests. Unchanged traffic is a valid result.
If passive instrumentation changes scheduling, fix that before interpreting
the new counters. Do not require a unique-bottleneck conclusion.

### 2. Investigate cache-miss origins

**Question:** what cache behavior contributes to latency when the matrices
are smaller than the nominal cache capacity?

- [x] Inventory actual Ruby hit/miss and coherence-event counters and check
  their definitions in the pinned implementation. CPU conflicting-load
  counters are not accelerator cache-conflict classifications.
- [x] **Skipped: separate miss attribution was not retained; aggregate alternative selected.** If the proposal retains separate miss attribution, record accelerator
  demand requests at cache-line granularity together with invalidation and
  ownership events. Separate demand traffic from prefetch/control traffic.
- [x] **Skipped under the aggregate alternative.** Use first-touch tracking and an appropriate same-capacity,
  fully-associative shadow cache to distinguish compulsory, capacity, and
  conflict behavior. Account for coherence events separately and document
  the classification policy when causes overlap.
- [x] **Skipped: no event observer was added; aggregate analysis reuses existing width-1/4 evidence.** Begin with N=24, width 1, bandwidth 4; compare width 4 only after the
  observer is checked. Preserve cache/queue size, clocks, trace input, and
  invocation boundaries.
- [x] **Completed for aggregate counters; event-observer checks skipped with that alternative.** Validate request/event totals against existing raw counters and
  confirm that the observer preserves correctness and timing.

**Deliverable:** a documented classification or, if the available evidence
cannot support it, an aggregate-counter analysis with explicit limits and
narrower proposal wording.

**Execution evidence:** [aggregate analysis](../results/analysis/cache/ANALYSIS.md)
and pinned counter implementation snapshots. Ruby demand/response definitions
and histogram totals are checked. No miss-cause categories are reported;
line/event/shadow instrumentation is skipped under this section's explicit
aggregate-counter alternative. The original raw cohort is preserved.

**Done when:** each reported category has a reproducible definition and
supporting trace/event evidence. A cold-versus-warm timing difference alone
does not separate compulsory, conflict, and coherence causes.

### 3. Close historical provenance gaps

- [x] Inventory each main width-1/2/4 point at N=24/32 for source snapshots,
  simulator/guest binary hashes, compressed and logical trace hashes,
  effective configurations, CACTI inputs, commands, and stage logs.
- [x] Recover available ignored/local artifacts before running anything.
  Record a missing artifact as missing; do not infer that an experiment was
  never executed merely because one published directory lacks it.
- [x] **Completed using the historical-comparison alternative; no replacement core cohort needed.** For unrecoverable evidence, either retain the comparison as historical
  with its stated provenance limit or rerun the required comparison in a
  fresh cohort. If a fresh width point is needed, include the matched
  baseline/other widths needed for the comparison instead of mixing cohorts.
- [x] Apply the bandwidth study's strict checks to any new cohort and retain
  its traces, source/binary identities, effective configurations, and manifest.

**Execution evidence:** [six-point inventory](../results/provenance/historical_20260930/README.md).
All three recovered N=32 traces match historical hashes. Missing per-stage
identities and the malformed historical simulator hash remain explicit.
N=24 published and N=32 recovered comparisons are separate. New diagnostics
verify traces/binaries, full configuration controls, output checks and manifests.

**Done when:** every comparison names one consistent cohort and the claimed
provenance can be verified from retained files. New artifacts cannot recreate
the exact identity of an unavailable historical trace or binary.

### 4. Harden repeated-call diagnostics

- [x] Fix `scripts/summarize_repeated.py` to require the expected call count,
  consecutive indices, every correctness record, matching completion/return
  intervals, and valid trace-hash metadata. The current implementation can
  accept incomplete evidence; the strict bandwidth validator does not fix it.
- [x] Add rejection tests for a missing call, duplicate/out-of-order index,
  missing interval, invalid/missing hash, and nonzero mismatches.
- [x] Use the retained matched-mutation and independent-mutation runs as
  initial fixtures. The independent mutation must continue to be recorded
  as a failed correctness test, rather than treated as a timing benchmark.
- [x] For warm-timing analysis, run a bounded matched-input diagnostic at
  N=24 with three calls for each width. Check every output in a correctness
  run; keep the timed run's host work and measurement boundaries identical
  across widths. If checks alter cache state, state that difference explicitly.
- [x] Collect per-call cache counts/latencies, queue times, datapath cycles,
  offload segments, and resource peaks. Include an unchanged-input case to
  help separate input mutation from repeated-call state.

**Execution evidence:** 14 repeated-validator tests; the historical independent
mutation is rejected with 20/24/19 mismatches. [New diagnostics](../results/diagnostics/warm_n24/ANALYSIS.md)
retain all 36 call records across twelve checked/timed runs. Every checked call
passes, timed host instruction sections match across widths, and full effective
configurations match. Checker cache effects and final-timestamp recovery are
explicit; no simulations were restarted after the finalization error.

**Done when:** incomplete traces/runs cannot pass, and first/later-call
differences are documented with direct per-call counters. Do not assume that
warmth is the only cause merely because some scheduler state is reset.

### 5. Complete analysis using existing data

- [x] Add automated width-1/2/4 summaries at both sizes, using the published
  N=24 cohort and recovered N=32 cohort separately.
- [x] Generate width-versus-latency, CPU-speedup-versus-size, and latency–area
  figures with units and provenance labels. Show FU and memory area separately.
- [x] Identify dominated points and the latency/area choices that remain;
  do not declare one universally best tile width.
- [x] Carry forward the already completed bandwidth figures and timing
  decomposition. Do not present diagnostic area under fixed CACTI inputs as
  the physical cost of changing cache ports.
- [x] Write the final paper after the technical gaps are scoped or resolved.

**Execution evidence:** [automated width summary](../results/analysis/WIDTH_SUMMARY.md),
CSV/validation, three figures in SVG/PDF/PNG, separate FU/memory estimates,
within-cohort dominance, and [final paper](../paper/final_paper.pdf).
Existing bandwidth figures/decomposition are carried forward with their
fixed-CACTI limits.

**Done:** reporting, figures and the final paper are complete.

These are reporting tasks rather than missing core simulations.

## Optional experiments after the proposal gaps are addressed

**Deferred optional work:** no extension was selected for this execution.
The six required steps are complete; these optional studies are outside the
bounded core scope. They are not marked as executed.

Pick one bounded extension, rather than adding all three to the core scope.

| Experiment | Minimum controlled design | What it adds | Main limitation |
| --- | --- | --- | --- |
| Bandwidth sensitivity at N=32 | Widths 1/4 × issue limits 1/4, four fresh points in one cohort | Tests whether the interaction survives the second main workload size | Larger traces and longer simulations; no automatic generality beyond two sizes |
| Cache-capacity sensitivity | N=24, widths 1/4 × caches 4/32 kB; queue and bandwidth fixed | Tests whether reuse remains useful under cache pressure | Capacity/associativity/coherence effects still require attribution; update characterization inputs before making cost claims |
| A 2×2 output tile | Compare 1×4 and 2×2 at N=24, both with four accumulators | Tests sharing both A and B against sharing A across four columns | New kernel/trace required; access order and scheduling also change, so equal accumulator count is not equal hardware cost |

For every new experiment: full output checks first; fresh matched cohorts;
identical timing boundaries; retained traces/configurations; report negative
or unchanged outcomes. Add the extension to the proposal only after its
scope and evidence are established.
