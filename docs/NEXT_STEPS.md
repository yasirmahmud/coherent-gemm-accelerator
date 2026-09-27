# Next steps and decision gates

Updated 2026-09-27. `[x]` means completed with saved evidence; `[ ]` means
pending. A focused proposal can proceed while validation continues. Do not
present an unchecked claim as an established result.

## 1. Proposal and course requirements — do first

- [x] Select an accessible open-source base: pinned gem5-Aladdin/Aladdin,
  x86 `DerivO3CPU`, Ruby `MESI_Two_Level_aladdin`, and its coherent
  private-cache accelerator path. See [BUILD.md](BUILD.md) and
  [UPSTREAM.md](UPSTREAM.md).
- [x] Establish one-column baseline and four-column extension at N=24/32
  with full correctness checks, raw stats, and a reproducible summary.
  Offload-time reductions are 11.90% and 22.56%; whole-program reductions
  are only 0.47% and 1.18%.
- [ ] Confirm the exact proposal deadline, submission route, team rules,
  and required format in Canvas. The lecture's approximate October 1 date
  is not an official deadline.
- [ ] Submit one focused proposal and agree its scope with the instructor:
  **How does output-column tile width affect coherent GEMM accelerator
  offload latency and modeled hardware cost?** Name the baseline, mechanism,
  CPU/coherence configuration, overhead, measurements, expected outcome, and
  deliverables. Treat general dynamic AI accelerator co-design as a stretch
  goal rather than a promised deliverable.

## 2. Correct the published record — before using figures in the proposal

- [ ] Correct [RESULTS.md](RESULTS.md) and
  [SESSION_SUMMARY.md](../SESSION_SUMMARY.md): the N=24
  baseline full and ROI logs have the same 170,042 connected nodes, 392,999
  edges, 1,452 cycles, and gem5 hardware settings, yet different MEM Area
  (802,977 vs 732,920 µm²). The claim that a *shorter ROI trace* explains
  the difference is unsupported. Mark the cause unresolved.
- [ ] Correct the size-sweep interpretation: CPU-relative speedup increases
  across N=8/16/24/32 (0.869/0.957/1.173/1.524×). Cycle-reduction
  percentage is non-monotonic. At N=8, cycles and offload time improve,
  while whole-program time is unchanged and CPU-relative speedup is below 1×.
- [ ] Correct the N=24 tile-width table's tile-1 “vs same-kernel CPU” value
  to 1.164× (70,973,000 CPU ticks / 60,962,000 accelerator ticks), rather
  than 1.000×. Label any baseline-normalized column separately.
- [ ] Update [README.md](../README.md) and
  [COURSE_ELIGIBILITY.md](COURSE_ELIGIBILITY.md) with the passing REPS=2
  diagnostic, N=8/16 and tile-width-2 results, and their limits. Retain the
  original failing diagnostic as historical evidence.
- [ ] Present equal dcache request counts and lower mean latency/queue time
  as observations. Verify byte counts and a causal mechanism before claiming
  unchanged data volume or reduced contention as the explanation.

## 3. Experimental validation

### Trace correctness and repeated use

- [x] Fix the REPS=2 trace/harness mismatch: both N=24 accelerator kernels
  now produce a second datapath graph and pass the full output check after
  a CPU input update. See `results/diagnostics/repeated_input_n24_fixed/`.
- [ ] Add a reproducible REPS=2 (or higher) runner that saves the trace hash,
  checks the output after **each** call, and records per-call offload intervals.
  Current second-call datapath counts are 229 cycles (base) and 228 cycles
  (tile-4); first-call gains must not be assumed to persist when warm.
- [ ] Test at least one CPU-side input change that is not merely the same
  predetermined mutation in both tracer and host harness. Until then,
  claim correctness only for the tested pre-traced repeated-call scenario,
  not arbitrary runtime coherence.

### Hardware cost and reproducibility

- [ ] Isolate the N=24 baseline MEM Area discrepancy with a controlled pair:
  save trace SHA-256, effective configs, Aladdin/CACTI inputs and outputs,
  and both raw logs. Determine whether configuration/input differences or
  tool behavior cause the 70,057 µm² difference.
- [ ] Investigate why REPS=2 invocation 2 increases FU Area by about 39%
  (base) and 17% (tile-4) despite an isomorphic datapath graph. Check
  scheduler/resource peaks before citing repeated-call area.
- [ ] Re-run paired baseline and tile-4 experiments on the second host,
  retain raw outputs, and compare **within-host percentage gains** as well
  as absolute ticks. Its prior rebuild passed correctness but did not
  reproduce every timing counter bit-for-bit.
- [ ] Report area or power as a cost conclusion only after relevant model
  outputs are repeatable and explained. Otherwise label them exploratory
  and make latency the primary measured outcome.

### Breadth and repeatable tooling

- [x] Add N=8/16 exploratory sizes with full checks and raw logs. The
  offload-time reduction rises from 1.90% at N=8 to 22.56% at N=32, while
  N=8 has no whole-program benefit.
- [x] Add a tile-width-2 N=24 point with full checks and raw logs. The
  N=24 tile-1/2/4 cycle counts are 1,452/1,257/1,133.
- [ ] Give N=8/16 and tile-width-2 documented, repeatable run commands and
  an automated summary check; tile-width 2 was run manually.
- [ ] If time permits after proposal approval, test tile-width 2 at N=32 or
  one representative inference workload. Hold CPU, cache, coherence, clock,
  and input fixed within each comparison. Report negative and mixed results.

## 4. Final report and completion check

- [ ] Include the research question, architecture diagram, baseline and
  mechanism, exact simulator configuration, controlled comparisons,
  correctness evidence, latency plots, hardware-cost evidence, causal
  analysis, reproducibility commands, and limitations.
- [ ] Explain small whole-program gains and the weak N=8 result; distinguish
  cold single-call behavior from repeated warm calls. Do not infer a general
  or silicon speedup from these simulator points.
- [ ] Regenerate summaries from committed raw logs, verify figures and
  units, and ensure README, results, proposal, and report make consistent
  claims before submission.
