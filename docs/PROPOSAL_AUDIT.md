# Proposal completion review

Reviewed on 2026-09-30 against the current proposal source/PDF, final IEEE
paper, implementation, validators, and fresh suite selected by
`paper/experiment_data.json`.

**Verdict: the main experiments and deliverables are complete, but literal
completion of every promise is not yet demonstrated.** Two items remain
partial: complete main-grid cache-counter reporting in the paper, and a
retained, controlled paired-rebuild assessment of modeled area using the
current local setup.

This replaces the earlier audit's obsolete statuses. The proposal and paper
are unchanged by this review. Negative results count as completed experiments
when their intended checks and interpretation are present.

## Commitment-by-commitment assessment

Locations refer to current `proposal/proposal.tex` line numbers.

| Proposal lines | Commitment | Status | Evidence and limits |
| --- | --- | --- | --- |
| 34–38, 87 | Test when reuse helps, issue-limit sensitivity, and datapath/offload/whole-program effects | Complete | Fresh main and bandwidth CSVs retain all timing measures. Width-4 offload benefits are 4.587%, 7.133%, and 11.802% at issue limits 1/2/4. Paper distinguishes local and whole-program gains. |
| 38, 64 | Baseline and widths 2/4 share A without changing GEMM arithmetic | Complete | All three kernels implement the loops; full output checks pass at every main point. Source and connected optimized A loads at N=24 are 13,824/6,912/3,456; products and accumulation adds stay 13,824. |
| 64, 128 | Compare optimized graph totals and measured cache requests | Complete within diagnostic scope | Fresh passive observer covers N=24, all widths. Reference/observer stats, configurations, cycles, and FU/MEM area agree. All widths accept/return 36 A loads, 36 B loads, and 576 C stores. Full graph/request counters are retained. Operand-specific attribution at N=32 was not explicitly promised. |
| 91, 93, 134 | Pinned tools, specified architecture, common queue/retry patch, retained identities/commands | Complete | Setup scripts and suite provenance retain revisions, image, diffs, patches, simulator fingerprints, source snapshots, guest identities, commands, and effective configurations. Detailed identities remain in artifacts rather than paper prose. |
| 95, Figure 3 | N=24/32 × widths 1/2/4 at issue limit 4 | Complete | All six promised points are in the fresh 12-point main sweep, with all five simulation stages per point. |
| 95, Figure 3 | N=24 × widths 1/4 × issue limits 1/2/4 | Complete | All six points have correctness, program timing, and segmented invocation timing; two CPU correctness controls are retained. |
| 60, 95 | Fixed controls, matched baselines, shared trace per kernel across issue limits | Complete | Validators compare effective configurations and trace identities. Main and bandwidth offload times agree at N=24, issue limit 4. |
| 121 | N=8/16 same-kernel OoO CPU comparisons for widths 1/4 | Complete; coverage expanded | Width 2 is also included. Figure 4 covers all 12 points. Width-4 CPU speedups are 0.875×/0.953×/1.171×/1.509× for N=8/16/24/32, bracketing crossover between N=16 and N=24. |
| 118, 121 | Full elementwise checks at every point; lightweight checks outside timed intervals | Complete | Full CPU/accelerator checks and matched timing-stage checksums are validated. Source places checksum after invocation statistics dump. Repeated timed runs receive a final checksum, without independently checked intermediate outputs. |
| 118, 121, 128 | Cache analysis at every main point; report loads/stores, access/queue means, samples, and N=32 aggregate evidence | Partial in paper; measurements exist | Bandwidth CSV contains the promised fields for six points. This review checked all six main N=24/32 invocation records and reconciled latency samples with returned loads plus stores. Paper presents detailed traffic at N=24 and bandwidth means but omits the complete main-grid counter table, N=32 aggregate discussion, and histogram sample counts. Checked values appear below. |
| 121 | Explain compulsory/capacity/conflict/coherence attribution limits | Complete as scoped | Proposal explicitly leaves separate attribution as diagnostic work. Paper reports aggregates and explains why they cannot partition miss causes. A complete miss classifier is not an outstanding core promise. |
| 123 | Retain provenance; reject missing stages, failed checks, trace/checksum mismatches, configuration changes | Complete for current suite | Suite validation records 107 simulator processes and verified fresh traces/guests. Main/graph/warm/bandwidth validators check intended evidence. Existing 22 validator tests passed. Current paper excludes historical measurements. |
| 123 | Matched repeated calls, first/later timing, independent mutation test | Complete, including negative result | All widths have matched/unchanged three-call checker/timed pairs. Eighteen checked calls pass. Independent mutation fails with 20/24/19 mismatches at every width, exits normally, and is excluded from performance comparisons. Paper states the replay limit. |
| 123 | Paired rebuilds assess modeled-area repeatability | Partial for current local evidence | All six main N=24/32 points have identical FU/MEM/total area across full/ROI/invocation stages. Reference/observer builds also agree at N=24. These check stage consistency and observer neutrality, rather than controlled repetition of the same clean build. Older notes describe rebuild agreement and an order test, but some original rebuild records were discarded. Selected suite has no dedicated two-clean-build comparison under identical revision/patch/toolchain/trace controls. |
| 126 | Completion/return segments, 1 ns conversion, residual and bandwidth stability | Complete | All six bandwidth points have a 757 ns completion residual and 494 ns return segment. Paper reports the 1.251 μs offset without uniquely assigning its cause. |
| 87, 128 | FU/memory/total area, latency–area tradeoffs, separate queue/access analysis | Complete | Width table and Figures 2/3 show latency/area, splits, and dominated points. Figure 5 distinguishes access/queue means. N=24 width 4 dominates; N=32 widths 1/4 remain alternatives. |
| 128 | Avoid physical port-cost/energy claims; distinguish associations from verified causes | Complete | Paper states pre-RTL cost, aggregate-counter, issue-limit cost-model, and repeated-call confounding limits. No physical port-cost or energy saving is claimed. |
| 131 | Kernels, runners, validation, comparison tables, vector plots, final explanatory paper | Complete | All exist. Five-page IEEE paper includes architecture, width, CPU-size, latency–area, and issue-limit figures. Scientific plots are vector PDFs generated from fresh selected records. |

## Main-grid cache evidence checked during review

Values are from reset-to-datapath-completion blocks in fresh main invocation
runs. Durations convert 1 ps ticks to ns. Loads/stores count returned datapath
operations. Demand misses are aggregate accelerator L1 Ruby protocol counts,
without miss-cause partition. Queue samples exclude successfully retried
issuance in the pinned implementation.

| N | Width | Loads / stores | Access mean (ns) | Queue mean (ns) | Access / queue samples | Demand misses |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 24 | 1 | 72 / 576 | 27.519 | 30.077 | 648 / 584 | 108 |
| 24 | 2 | 72 / 576 | 22.432 | 25.617 | 648 / 588 | 108 |
| 24 | 4 | 72 / 576 | 19.915 | 21.779 | 648 / 587 | 108 |
| 32 | 1 | 128 / 1,039 | 33.194 | 31.686 | 1,167 / 1,049 | 192 |
| 32 | 2 | 128 / 1,039 | 24.925 | 25.560 | 1,167 / 1,051 | 192 |
| 32 | 4 | 128 / 1,039 | 20.642 | 21.621 | 1,167 / 1,053 | 192 |

Raw files follow
`results/paper_runs/paper_local_20261001/main/invocation_results/{base,tiled2,tiled4}_n{24,32}/m5out-{cache,accel}/stats.txt`.
Baseline uses `m5out-cache`; tiled variants use `m5out-accel`.

## Remaining work before claiming every promise is fulfilled

1. Add the main-grid cache-counter breakdown, sample-count context, and N=32
   aggregate discussion to the paper or an explicitly linked report table.
   Existing measurements suffice; no additional simulation is needed.
2. Retain a controlled paired-clean-rebuild area assessment on the current
   device, with matching source/patch/toolchain/trace controls and comparison
   results. Stage agreement and observer neutrality alone should not be
   presented as clean-rebuild repeatability.

Larger N, width 8, inference, RTL synthesis, energy measurements, arbitrary
runtime-input correctness, exact crossover identification, and a full miss
classifier are not core deliverables promised by this proposal. Independent
mutation failure and small-size CPU losses do not make their experiments
incomplete.

## Documentation consistency

Paper data selection and generated numerical macros are current. Root README
still leads with historical headline measurements and a next-steps list
containing completed work. Other historical notes retain earlier statuses.
These documentation issues should be refreshed before presenting the
repository as one current completion record; they are separate from missing
experiments.

## Evidence reviewed

- [Proposal source](../proposal/proposal.tex) and rendered two-page PDF.
- [Final IEEE paper](../paper/final_paper.pdf), TeX, and generated result macros.
- [Experiment coverage](PAPER_EXPERIMENTS.md), selected CSVs, suite/run records,
  graph equivalence checks, warm and independent-mutation outcomes.
- Raw cache statistics and all three stage area reports for all six main
  N=24/32 points; histogram totals reconcile and stage areas agree.
- Kernel timing/check boundaries, validators, and retained 22-test result.
- Historical rebuild/order-test records, distinguishing their limitations
  from current selected evidence.

This review did not rerun experiments, change proposal/manuscript, or
commit/push the updated audit.
