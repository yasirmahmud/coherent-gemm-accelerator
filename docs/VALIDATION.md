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
