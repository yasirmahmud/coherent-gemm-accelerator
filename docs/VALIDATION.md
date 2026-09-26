# Package validation record

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
