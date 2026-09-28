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

- [x] Correct [RESULTS.md](RESULTS.md) and
  [SESSION_SUMMARY.md](../SESSION_SUMMARY.md): the N=24
  baseline full and ROI logs have the same 170,042 connected nodes, 392,999
  edges, 1,452 cycles, and gem5 hardware settings, yet different MEM Area
  (802,977 vs 732,920 µm²). The claim that a *shorter ROI trace* explains
  the difference is unsupported. Mark the cause unresolved. Done in both
  files (2026-09-27); see RESULTS.md's "Cost and validity limits".
- [x] Correct the size-sweep interpretation: CPU-relative speedup increases
  across N=8/16/24/32 (0.869/0.957/1.173/1.524×). Cycle-reduction
  percentage is non-monotonic. At N=8, cycles and offload time improve,
  while whole-program time is unchanged and CPU-relative speedup is below 1×.
  Corrected in RESULTS.md's N=8/16 addendum and SESSION_SUMMARY.md.
- [x] Correct the N=24 tile-width table's tile-1 “vs same-kernel CPU” value
  to 1.164× (70,973,000 CPU ticks / 60,962,000 accelerator ticks), rather
  than 1.000×. Label any baseline-normalized column separately. Done in the
  tile-width ablation table in RESULTS.md.
- [x] Update [README.md](../README.md) and
  [COURSE_ELIGIBILITY.md](COURSE_ELIGIBILITY.md) with the passing REPS=2
  diagnostic, N=8/16 and tile-width-2 results, and their limits. Retain the
  original failing diagnostic as historical evidence (still at
  `results/diagnostics/repeated_input_n24/`, untouched).
- [x] Present equal dcache request counts and lower mean latency/queue time
  as observations. Verify byte counts and a causal mechanism before claiming
  unchanged data volume or reduced contention as the explanation. Reworded
  in RESULTS.md's queue/cache traffic section: access counts confirmed
  identical, latency drop confirmed, "reduces contention" downgraded from
  stated-as-fact to explicitly-unverified hypothesis. Byte counts (as
  opposed to access counts) still not separately checked — noted as an
  open gap in the same section rather than silently left implied-done.

## 3. Experimental validation

### Trace correctness and repeated use

- [x] Fix the REPS=2 trace/harness mismatch: both N=24 accelerator kernels
  now produce a second datapath graph and pass the full output check after
  a CPU input update. See `results/diagnostics/repeated_input_n24_fixed/`.
- [x] Add a reproducible REPS≥2 runner that saves the trace hash, checks
  the output after **each** call, and records per-call offload intervals.
  See `scripts/run_repeated.sh` + `scripts/summarize_repeated.py`. A REPS=3
  base_n24 run confirms the warm state stabilizes rather than drifting
  further: per-call cycles 1452 → 628 → 628 (calls 1 and 2 byte-identical).
  The exact warm-state number is measurement-setup-sensitive (differs from
  the earlier ad-hoc REPS=2 test's 229 cycles); first-call gains must still
  not be assumed to persist when warm, and neither should any single warm
  number be assumed stable across different measurement harnesses.
- [x] Test at least one CPU-side input change that is not merely the same
  predetermined mutation in both tracer and host harness. **Result: it
  fails.** `scripts/run_repeated.sh base 24 3 --independent-mutation`
  (runtime mutation with a different index/delta pattern than the trace)
  produces 20/24/19 mismatches across the 3 calls
  (`results/diagnostics/repeated_n24_reps3_base_independent/`). This
  disproves this repo's own earlier (untested) prediction that Aladdin's
  replay would be value-independent. **Claim correctness only for the
  tested case: runtime mutation exactly matching the trace-time mutation.**
  Not established: arbitrary/unpredictable runtime coherence.

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
- [x] Give N=8/16 and tile-width-2 documented, repeatable run commands and
  an automated summary check. N=8/16:
  `bash scripts/run_inside.sh {8,16} all` (same script as validated N=24/32,
  just bypassing `scripts/run.sh`'s size guard), summarized with
  `python3 scripts/explore_size.py 8 16`. Tile-width-2 (previously run
  manually): now `bash scripts/run_ablation.sh tiled2 24 all` — a new,
  committed, generic single-variant runner (any `benchmarks/gemm_<variant>/`
  directory, not just base/tiled4), matching `scripts/run_inside.sh`'s exact
  build/check logic. Verified by rerunning it and reproducing the existing
  committed tiled2_n24 numbers exactly (1,257 cycles, 0 mismatches).
- [ ] If time permits after proposal approval, test tile-width 2 at N=32 or
  one representative inference workload. Hold CPU, cache, coherence, clock,
  and input fixed within each comparison. Report negative and mixed results.
  **Not started** — explicitly gated on proposal approval (section 1, still
  open), so deliberately left undone rather than run ahead of that.

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
