# Experiment inventory and evidence recovery

Reconciled 2026-09-30 against published results, recorded validation notes,
and the workspace's ignored `.artifacts/results/`. The other device is
unavailable. Missing files in one directory do not establish that an
experiment was never run; statuses below distinguish execution from evidence
availability. No simulator runs were launched during this reconciliation.

## Available experiment cohorts

| Experiment | Published evidence | Recovered 2026-09-30 evidence | Status |
| --- | --- | --- | --- |
| N=24, widths 1 and 4 | Full, ROI, invocation; CPU controls | Full, ROI, invocation; CPU controls | Complete in both cohorts |
| N=32, widths 1 and 4 | Full, ROI, invocation; CPU controls | Full, ROI, invocation; CPU controls | Complete in both cohorts; fresh-build rerun now recorded |
| N=24, width 2 | Full, ROI, invocation; CPU control | Absent | Complete in published cohort |
| N=32, width 2 | Absent | Full, ROI, invocation; CPU control | Complete; recovered from ignored local artifacts |
| N=8/16, widths 1 and 4 | Full, ROI, invocation; CPU controls | Absent | Complete exploratory points |
| N=24, REPS=2, matched mutation, widths 1 and 4 | Passing CPU/accelerator logs | Absent | Correctness evidence available; dedicated timing/config files absent |
| N=24, REPS=3, matched mutation, width 1 | Per-call log, stats, config, trace hash | Absent | All three calls pass |
| N=24, REPS=3, independent mutation, width 1 | Per-call log, stats, config, trace hash | Absent | Completed negative result: 20/24/19 mismatches |
| N=24, MEM-area full/ROI order test | Four logs and two trace hashes | Absent | Completed; area discrepancy did not reproduce; effective configs and CACTI artifacts not retained here |
| N=24, widths 1/4 × cache issue limits 1/2/4 | New isolated cohort under `results/cache_bandwidth/n24_20260930/` | Not a recovered experiment | Complete: all six full/ROI/invocation points, two CPU checks, retained traces/configs, CSV, figures, and validation tests; see [CACHE_BANDWIDTH.md](CACHE_BANDWIDTH.md) |

Published evidence remains in `results/{fair,roi,invocation}_results/` and
`results/diagnostics/`. The recovered files are preserved separately under
[`results/reproductions/ece-lnx-10_2026-09-30/`](../results/reproductions/ece-lnx-10_2026-09-30/README.md).
They include raw logs, stats, configurations, available trace hashes, local
runner records, a [summary CSV](../results/reproductions/ece-lnx-10_2026-09-30/summary.csv),
and a SHA-256 manifest. Historical failures remain as recorded evidence.

## Recovered N=32 tile-width comparison

These rows use the same dated local build cohort, including its own baseline.
Both CPU and accelerator full-output checks report zero mismatches. ROI and
invocation checksums equal 1 for every width, and accelerator-host instruction
counts equal 30,046. CPU type, accelerator cycle time, cache size,
associativity, line size, queue capacity, and bandwidth match across all
recovered accelerator stages. Other configuration fields were not exhaustively
compared during this recovery.

| Width | Datapath cycles | Cycle reduction vs. width 1 | Offload ticks | Offload reduction vs. width 1 | Total modeled area (µm²) | Area change vs. width 1 |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | 2,827 | 0.000% | 4,132,000 | 0.000% | 1,246,960 | 0.000% |
| 2 | 2,268 | 19.774% | 3,508,000 | 15.102% | 1,596,260 | +28.012% |
| 4 | 1,984 | 29.820% | 3,224,000 | 21.975% | 1,592,240 | +27.690% |

The recovered width-4 offload reduction is 21.975%, compared with the
published cohort's 22.556%. At N=24 the corresponding reductions are
11.802% and 11.903%. These differences are recorded rather than silently
replacing published figures. Cycle counts and whole-program reduction
percentages match the published baseline/width-4 summaries. Do not calculate
width comparisons by combining a baseline from one cohort with a variant
from another. N=24's complete width-1/2/4 ablation is in the published cohort;
N=32's complete ablation is in the recovered cohort.

## Remaining work after reconciliation

1. Fix repeated-run validation: require every expected correctness record,
   consecutive call indices, corresponding timing intervals, and valid trace
   hash metadata. The current summarizer accepts incomplete evidence.
2. Generate repeatable all-width summary and plotting tools. Both N=24 and
   N=32 ablations now have raw evidence; rerunning them is unnecessary merely
   because a published directory lacks one point.
3. Validate modeled power/energy/energy-delay calculations promised in the
   proposal, including cycle duration and the 10 ns characterization fallback.
   Raw power reports exist; derived energy analysis is not established by
   these files. Completion on the unavailable device cannot be confirmed.
4. Directly measure the cause of cache-latency and warm-invocation changes.
   Separate measurement/checker effects from accelerator behavior. Preserve
   the independent-mutation failure as a limit on correctness claims.
5. Write the final report and align its claims with each named cohort. Course
   submission/approval status remains unconfirmed by repository evidence.

The 2026-09-26/27 cross-host checks are documented in `VALIDATION.md`, which
states their raw results were discarded or not committed. This recovery
preserves the separate 2026-09-30 local reproduction; it does not recover
those exact historical files. Width 8, larger sizes, and inference workloads
have no evidence here and remain optional extensions with unconfirmed
execution elsewhere. Reproduce additional points locally only when their
evidence is needed and cannot be recovered.
