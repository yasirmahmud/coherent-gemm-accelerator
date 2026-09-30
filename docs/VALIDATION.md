# Package validation record

## 2026-09-30: completed cache-bandwidth sensitivity study

The isolated N=24 cohort in `results/cache_bandwidth/n24_20260930/` covers
widths 1/4 and issue limits 1/2/4. All 18 accelerator stages and both
full-check CPU executions completed successfully. The final summarizer
verified all six points, full output checks, checksums, matching host
instruction counts, retained trace hashes, graph sizes, and stage-specific
binary hashes. All effective gem5 configuration entries match within each
stage after normalization of generated names/paths and exclusion of the
intentionally varied `cacheBandwidth`. The simulator binary's SHA-256
matches the recorded pre-run hash.

Offload reductions for width 4 are 4.669%, 7.268%, and 12.033% as bandwidth
increases from 1 to 2 to 4. The issue-limit sensitivity is measured; unique
bottleneck attribution is not established. Eight validator tests passed,
including rejection of incomplete, failed, altered-trace, wrong-bandwidth,
and uncontrolled-CPU evidence. Raw artifacts, CSV, standalone figures, and
a SHA-256 manifest are retained. The proposal was rebuilt and visually
checked at two pages. See [CACHE_BANDWIDTH.md](CACHE_BANDWIDTH.md).

## Earlier package validation

Validated on 2026-09-25/26 in Linux under WSL2:

| Check | Outcome |
| --- | --- |
| `bash scripts/setup.sh` in a fresh Docker volume | Passed: pinned sources fetched, patch applied, `build/X86/gem5.opt` compiled |
| `bash scripts/run.sh 24 full` against that fresh build | Passed: both accelerator and CPU full-output checks |
| `bash scripts/run.sh 24 all` against the earlier patched simulator volume | Passed: full, ROI, and invocation stages for both kernels |
| `python3 scripts/summarize.py` on shipped N=24/N=32 raw files | Passed all full-check, checksum, instruction-count, and invocation-label validations; reproduced the committed CSV |
| `python3 scripts/plot_results.py` | Generated the committed figure from the CSV |
| Bash syntax checks on all shell scripts | Passed |

An additional N=32 package rerun reached and passed the original kernel's
full-output stage, reproducing 177,381,000 whole-program ticks. The remaining
N=32 stages were stopped after the already saved complete N=32 raw results
passed the validator. This distinction matters: the package's end-to-end N=32
runner was not repeated to completion in this validation session. The saved
N=32 full, ROI, and invocation results are included and auditable.

The repeated-input diagnostic is intentionally **not** a pass: accelerator
outputs differ from the CPU reference after CPU-side input modification. See
[RESULTS.md](RESULTS.md) and the diagnostic logs.

## 2026-09-26 revalidation on a different host (rootless Podman, no Docker)

Re-ran on a separate Linux server with no Docker daemon available, using
rootless Podman as a drop-in engine for the same pinned image by digest (see
`scripts/setup.sh`; no script changes were needed — Podman's CLI covers the
`pull`/`volume create`/`run` calls used here).

| Check | Outcome |
| --- | --- |
| `bash scripts/setup.sh` (Podman) | Passed: same pinned image/digest, patch applied, `build/X86/gem5.opt` compiled |
| `bash scripts/run.sh 24 full`, run twice back-to-back, no rebuild between | Both passed (0 mismatches, both kernels); the two runs' simulated stats (`final_tick`, `sim_ticks`, all `system.cpu.*` counters) were **bit-identical** to each other, confirming this environment is internally deterministic |
| Same run vs. the originally shipped `results/fair_results/{base,tiled4}_n24` in this repo | Functional correctness matched (0 mismatches both sides), but simulated timing/microarchitectural stats did **not** match bit-for-bit (e.g. `final_tick` 111480500 vs 111683500 for base_n24 CPU; branch-predictor counters also differed by small amounts). Only host-machine meta-stats (`host_seconds`, `host_inst_rate`, etc.) were expected/known to differ. |

Read together, these two rows mean: the gap is not run-to-run flakiness on
either side (each environment reproduces itself exactly) and is not a
Docker-vs-Podman correctness issue (functional output still matches) — but a
fresh from-scratch build+run on a different host does not currently
reproduce the original's cycle-accurate numbers bit-for-bit. Root cause not
yet isolated; candidates include guest-kernel-compilation sensitivity to
build-host differences (core count, environment) rather than the container
engine itself. This directly bears on Gate 2 (hardware-cost repeatability)
and is worth resolving or explicitly scoping around before citing area/cycle
numbers from a rebuild as directly comparable to the numbers already in this
repo. No repo files were changed by this revalidation; the rebuilt results
were discarded after comparison (see `claude_session_rasin.md`, gitignored,
for the working notes).

## 2026-09-27: within-host percentage gains reproduce, even though absolute ticks don't

Per `docs/NEXT_STEPS.md` §3 ("re-run paired baseline and tile-4 experiments
on the second host... compare within-host percentage gains as well as
absolute ticks"): re-ran the paired N=24 base/tiled4 comparison end-to-end
(full, invocation, and roi stages) on this session's rebuild host and
computed every headline percentage/ratio metric using **only this host's
own numbers** (not mixing with the originally-shipped values), then compared
those percentages against the originally published ones:

| Metric | This host | Published | Match |
| --- | ---: | ---: | --- |
| Cycle reduction | 21.970% | 21.97% | Exact |
| Offload-interval reduction | 11.802% | 11.90% | Close (Δ0.1pp) |
| Whole-program reduction | 0.474% | 0.474% | Exact |
| CPU-relative speedup | 1.179x | 1.173x | Close (Δ0.006) |

Absolute tick values themselves still differ from the originally shipped
numbers by small amounts (e.g. offload ticks 2,703,000/2,384,000 here vs.
2,680,000/2,361,000 published) — consistent with the 2026-09-26 entry above
(cross-host absolute-tick differences are real and not yet root-caused).
**But the percentage-based comparisons — which are what every headline claim
in `docs/RESULTS.md` and `README.md` actually reports — reproduce closely or
exactly.** This means the cross-host absolute-tick sensitivity does not
undermine the pipeline's actual conclusions: two exact matches and two
matches within a few hundredths, despite a fully independent rebuild on a
different host. Cycle count (an Aladdin-internal, not gem5-CPU-model,
measurement) has been observed to match bit-for-bit across every independent
rebuild performed this session and the one before it — the small absolute-
tick drift is confined to gem5's own CPU-timing model, not Aladdin's
datapath scheduling.

Raw logs from this check were not committed (they were generated solely to
compute these ratios against the already-committed reference numbers, not
to replace them); the working tree was restored to the committed state
afterward via `git checkout`.

## 2026-09-30: recovered complete local reproduction and N=32 width-2 evidence

Repository reconciliation found a dated local rebuild in the ignored
`.artifacts/results/` directory. It contains full, ROI, and invocation stages
for base/tiled4 at both N=24 and N=32, plus tiled2 at N=32. Thus the earlier
incomplete N=32 rerun record above describes that historical session, not
the current availability of a complete local N=32 reproduction.

Recovered files were copied into
[`results/reproductions/ece-lnx-10_2026-09-30/`](../results/reproductions/ece-lnx-10_2026-09-30/README.md)
with separate provenance, a raw-derived summary, and a SHA-256 manifest.
Original published results were retained. This reconciliation checked saved
outputs; it did not rerun the simulator or independently rehash the build
executable identified by the original local reproduction note.

All five points pass full CPU and accelerator checks, ROI/invocation checksum
agreement, and within-size accelerator-host instruction matching. The
invocation stats contain the expected completion and host-return intervals.
CPU type and accelerator cycle/cache/queue settings match across all recovered
accelerator stages. At N=32, width 2 has 2,268 cycles and 3,508,000 offload
ticks, a 15.102% reduction against the recovered baseline's 4,132,000 ticks.

Recovered baseline/width-4 offload reductions are 11.802% at N=24 and
21.975% at N=32, compared with published 11.903% and 22.556%. Datapath-cycle
and whole-program reduction percentages match. Keep cohort provenance when
comparing widths; do not combine baseline and variant timings from different
cohorts. See [EXPERIMENT_INVENTORY.md](EXPERIMENT_INVENTORY.md) for the full
availability table and remaining work. The unavailable other device's exact
2026-09-26/27 files have not been recovered.
