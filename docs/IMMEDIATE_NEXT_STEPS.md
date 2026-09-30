# Immediate next steps to strengthen the proposal

Updated 2026-09-30. This is an execution plan, not a record of completed
experiments. The [proposal audit](PROPOSAL_AUDIT.md) identifies the remaining
commitments. The core width and bandwidth experiments are already complete;
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

- [ ] For the graph claim, either perform task 1 or change the commitment to
  comparing optimized graph totals and measured cache counters. Do not claim
  an established operand-specific causal mechanism yet.
- [ ] For compulsory/conflict/coherence effects, either perform task 2 or
  promise aggregate cache/coherence measurements with explicit attribution
  limits. Existing aggregate misses do not classify their causes.
- [ ] Scope complete retained source/binary/trace provenance to the new
  bandwidth cohort until historical gaps are recovered.

**Done when:** every technical promise has completed supporting evidence
or is explicitly identified as remaining analysis. Rebuild the PDF and
verify that it remains two pages without measured-result disclosures.

### 1. Resolve graph-to-memory attribution

**Question:** which source-level reuse changes survive optimization, and
which become different cache requests?

- [ ] Inspect retained optimization logs and model outputs first. Record
  what they already expose and what requires instrumentation.
- [ ] Add passive counters around graph optimization: loads/stores by array
  A/B/C, arithmetic operations, and live/connected operation counts before
  and after optimization. Distinguish GEMM accumulation from index/address
  arithmetic; do not interpret every integer add as a MAC.
- [ ] Count accepted cache requests separately from returned requests,
  retries, and merged operations, with per-array labels where available.
  Existing `total_dcache_loads/stores` count returned cache operations.
- [ ] Record issue-limit blocked attempts and blocked cycles separately;
  multiple node polls in one cycle must not inflate a cycle count.
- [ ] Use one N=24 cohort with widths 1/2/4 at issue limit 4. Reuse each
  kernel's trace across the instrumented and reference runs where possible.
  Preserve the existing simulator and build the diagnostic version separately.
- [ ] Confirm that adding counters preserves full correctness, datapath
  cycles, and the controlled simulated timing. Save the source patch,
  executable identity, trace identities, configurations, and raw counters.

**Deliverable:** a table connecting source operations, optimized graph
operations, and accepted/returned memory operations for each width.

**Done when:** the table explains what is observed without assuming fewer
source loads imply fewer requests. Unchanged traffic is a valid result.
If passive instrumentation changes scheduling, fix that before interpreting
the new counters. Do not require a unique-bottleneck conclusion.

### 2. Investigate cache-miss origins

**Question:** what cache behavior contributes to latency when the matrices
are smaller than the nominal cache capacity?

- [ ] Inventory actual Ruby hit/miss and coherence-event counters and check
  their definitions in the pinned implementation. CPU conflicting-load
  counters are not accelerator cache-conflict classifications.
- [ ] If the proposal retains separate miss attribution, record accelerator
  demand requests at cache-line granularity together with invalidation and
  ownership events. Separate demand traffic from prefetch/control traffic.
- [ ] Use first-touch tracking and an appropriate same-capacity,
  fully-associative shadow cache to distinguish compulsory, capacity, and
  conflict behavior. Account for coherence events separately and document
  the classification policy when causes overlap.
- [ ] Begin with N=24, width 1, bandwidth 4; compare width 4 only after the
  observer is checked. Preserve cache/queue size, clocks, trace input, and
  invocation boundaries.
- [ ] Validate request/event totals against existing raw counters and
  confirm that the observer preserves correctness and timing.

**Deliverable:** a documented classification or, if the available evidence
cannot support it, an aggregate-counter analysis with explicit limits and
narrower proposal wording.

**Done when:** each reported category has a reproducible definition and
supporting trace/event evidence. A cold-versus-warm timing difference alone
does not separate compulsory, conflict, and coherence causes.

### 3. Close historical provenance gaps

- [ ] Inventory each main width-1/2/4 point at N=24/32 for source snapshots,
  simulator/guest binary hashes, compressed and logical trace hashes,
  effective configurations, CACTI inputs, commands, and stage logs.
- [ ] Recover available ignored/local artifacts before running anything.
  Record a missing artifact as missing; do not infer that an experiment was
  never executed merely because one published directory lacks it.
- [ ] For unrecoverable evidence, either retain the comparison as historical
  with its stated provenance limit or rerun the required comparison in a
  fresh cohort. If a fresh width point is needed, include the matched
  baseline/other widths needed for the comparison instead of mixing cohorts.
- [ ] Apply the bandwidth study's strict checks to any new cohort and retain
  its traces, source/binary identities, effective configurations, and manifest.

**Done when:** every comparison names one consistent cohort and the claimed
provenance can be verified from retained files. New artifacts cannot recreate
the exact identity of an unavailable historical trace or binary.

### 4. Harden repeated-call diagnostics

- [ ] Fix `scripts/summarize_repeated.py` to require the expected call count,
  consecutive indices, every correctness record, matching completion/return
  intervals, and valid trace-hash metadata. The current implementation can
  accept incomplete evidence; the strict bandwidth validator does not fix it.
- [ ] Add rejection tests for a missing call, duplicate/out-of-order index,
  missing interval, invalid/missing hash, and nonzero mismatches.
- [ ] Use the retained matched-mutation and independent-mutation runs as
  initial fixtures. The independent mutation must continue to be recorded
  as a failed correctness test, rather than treated as a timing benchmark.
- [ ] For warm-timing analysis, run a bounded matched-input diagnostic at
  N=24 with three calls for each width. Check every output in a correctness
  run; keep the timed run's host work and measurement boundaries identical
  across widths. If checks alter cache state, state that difference explicitly.
- [ ] Collect per-call cache counts/latencies, queue times, datapath cycles,
  offload segments, and resource peaks. Include an unchanged-input case to
  help separate input mutation from repeated-call state.

**Done when:** incomplete traces/runs cannot pass, and first/later-call
differences are documented with direct per-call counters. Do not assume that
warmth is the only cause merely because some scheduler state is reset.

### 5. Complete analysis using existing data

- [ ] Add automated width-1/2/4 summaries at both sizes, using the published
  N=24 cohort and recovered N=32 cohort separately.
- [ ] Generate width-versus-latency, CPU-speedup-versus-size, and latency–area
  figures with units and provenance labels. Show FU and memory area separately.
- [ ] Identify dominated points and the latency/area choices that remain;
  do not declare one universally best tile width.
- [ ] Carry forward the already completed bandwidth figures and timing
  decomposition. Do not present diagnostic area under fixed CACTI inputs as
  the physical cost of changing cache ports.
- [ ] Write the final paper after the technical gaps are scoped or resolved.

These are reporting tasks rather than missing core simulations.

## Optional experiments after the proposal gaps are addressed

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
