# Next steps and decision gates

Updated 2026-09-30. `[x]` means completed work; `[ ]` means pending or
unconfirmed. Evidence availability is recorded separately in
[EXPERIMENT_INVENTORY.md](EXPERIMENT_INVENTORY.md), including recovered local
results that were absent from the published directories. A focused proposal
can proceed while validation continues. Do not present an unchecked claim
as an established result.

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

- [ ] Harden `scripts/summarize_repeated.py` and enforce its checks in the
  runner. Require the expected number of calls, consecutive call indices,
  complete timing intervals, and trace-hash metadata. The 2026-09-30 audit
  reproduced a false pass with only one of three calls and no timing blocks
  or trace hash. This is a code issue independent of where runs took place.
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

- [x] Isolate the N=24 baseline MEM Area discrepancy with a controlled pair:
  save trace SHA-256, effective configs, Aladdin/CACTI inputs and outputs,
  and both raw logs. Determine whether configuration/input differences or
  tool behavior cause the 70,057 µm² difference. **Result: does not
  reproduce.** A controlled full/roi × order test
  (`results/diagnostics/mem_area_order_test/`) shows all four combinations
  producing identical area (802,977 µm² MEM). The committed discrepancy
  likely reflects the original files' build provenance, not the pipeline
  itself. See `docs/RESULTS.md`.
- [x] Investigate why REPS=2 invocation 2 increases FU Area by about 39%
  (base) and 17% (tile-4) despite an isomorphic datapath graph. Check
  scheduler/resource peaks before citing repeated-call area. **Confirmed by
  elimination**: read `BaseDatapath.cpp` directly — all internal scheduling
  state (`num_cycles`, `executedNodes`, queues) is explicitly reset per
  invocation, and the scheduler has no node-ID-based logic, ruling out an
  Aladdin-side bug. The only remaining source is gem5's own simulated
  memory system (deliberately not reset between calls) — i.e. genuine
  cache/queue warmth. Matches the REPS=3 finding (cycles stabilize after
  one repeat) precisely. See `docs/RESULTS.md`.
- [x] Re-run paired baseline and tile-4 experiments on the second host,
  retain raw outputs, and compare **within-host percentage gains** as well
  as absolute ticks. Its prior rebuild passed correctness but did not
  reproduce every timing counter bit-for-bit. **Result: percentages
  reproduce (2 exact, 2 within a few hundredths) despite absolute ticks
  still differing slightly.** Cycle reduction 21.970% (published 21.97%,
  exact), whole-program reduction 0.474% (published 0.474%, exact), offload
  reduction 11.802% (published 11.90%), CPU-relative speedup 1.179x
  (published 1.173x). See `docs/VALIDATION.md`'s 2026-09-27 entry.
- [x] Report area or power as a cost conclusion only after relevant model
  outputs are repeatable and explained. Otherwise label them exploratory
  and make latency the primary measured outcome. Followed throughout this
  pass: area is now stated as resolved where the controlled test showed it
  (single-invocation REPS=1, and the `fair`/`roi` order test), and
  explicitly unresolved/exploratory where it isn't (repeated-invocation
  area/cycle behavior); power was never cited as a conclusion anywhere,
  consistent with it never having been measured.

### Breadth and repeatable tooling

- [x] Implement and run the N=24 cache-bandwidth sensitivity study: widths
  1/4 × issue limits 1/2/4, all six fresh points with full/ROI/invocation
  stages, shared per-kernel traces, CPU checks, complete configuration
  comparisons, CSV, figures, and validator rejection tests. Offload gains
  are 4.669/7.268/12.033%, showing that width benefit depends on issue
  bandwidth. See [CACHE_BANDWIDTH.md](CACHE_BANDWIDTH.md). The proposal
  includes this extension; physical cache-port cost remains outside its scope.

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
- [x] Recover and validate tile-width 2 at N=32. All three stages were found
  in `.artifacts/results/` and preserved with the paired local baseline and
  tile-width-4 results under `results/reproductions/ece-lnx-10_2026-09-30/`.
  Width 2 passes full CPU/accelerator checks, takes 2,268 datapath cycles,
  and reduces offload ticks by 15.102% against that cohort's baseline.
  This completes the proposal's raw width-1/2/4 experiment matrix at both
  sizes; N=24 and N=32 are separate cohorts. See the inventory for details.
- [ ] Add automated summaries and plots covering widths 1/2/4 at both sizes,
  and validate the proposal's modeled energy/energy-delay analysis.
- [ ] If time permits, test one representative inference workload or width
  8. No evidence is available here; execution on the unavailable device is
  unconfirmed. Hold CPU, cache, coherence, clock, and input fixed within each
  comparison. Report negative and mixed results.

## 4. Final report and completion check

- [~] Include the research question, architecture diagram, baseline and
  mechanism, exact simulator configuration, controlled comparisons,
  correctness evidence, latency plots, hardware-cost evidence, causal
  analysis, reproducibility commands, and limitations. **Scaffolded, not
  written**: `docs/REPORT_SKELETON.md` has every required section with
  exact pointers to its evidence, and `docs/ARCHITECTURE.md` has the
  diagram. The actual report prose is deliberately not written here — per
  `docs/COURSE_ELIGIBILITY.md`, "Team members must understand and defend
  the code and methodology themselves," and this is graded coursework. Use
  the skeleton as a checklist while writing the real thing, don't submit it
  as-is.
- [x] Explain small whole-program gains and the weak N=8 result; distinguish
  cold single-call behavior from repeated warm calls. Do not infer a general
  or silicon speedup from these simulator points. Written out explicitly in
  `docs/REPORT_SKELETON.md` §9 and throughout `docs/RESULTS.md`'s N=8/16 and
  Gate 1 sections — ready to cite/adapt directly into the report.
- [x] Regenerate summaries from committed raw logs, verify figures and
  units, and ensure README, results, proposal, and report make consistent
  claims before submission. Done 2026-09-27: `python3 scripts/summarize.py`
  regenerated fresh from the committed raw logs — byte-identical to the
  committed `results/validated_summary.csv`, no drift. `scripts/plot_results.py`
  regenerated too — visually identical (only PNG metadata/timestamp
  differed, as expected for any regenerated image). README.md,
  docs/RESULTS.md, docs/COURSE_ELIGIBILITY.md, and docs/REPORT_SKELETON.md
  were kept in sync with every correction made this session (no leftover
  contradictions between them going into a proposal/report).
