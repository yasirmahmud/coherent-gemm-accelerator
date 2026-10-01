# Three-call N=24 diagnostic cohort

Six case/width points: matched pre-agreed mutation and unchanged input, each
at widths 1/2/4. Each point has paired full per-call correctness and timed
harnesses sharing one three-invocation trace. All eighteen checked outputs
pass. Timed guest instruction sections are identical across widths within
each case; final checksums supplement the paired correctness evidence.
All effective configuration fields match after documented path/kernel-name
normalization. `summary.csv` contains all 36 call records and direct counters.

Read `ANALYSIS.md` for checker/cache-history limits and `validation.json` for
trace/guest identities and controls. Source/configs/traces live in `inputs/`;
stage build records, guest binaries, commands, logs, configs, stats and model
reports are retained for each mode. CACTI inputs and simulator identity are
under `provenance/`.

The runner exited 127 after the simulations and model copies completed,
because an edited runner file shifted Bash's final command read offset.
`runner.log` retains the error and `provenance/finalization.json` documents it.
Independent validation of every completed run with `--finalize` produced
`validated-at.txt`; no simulation was restarted. Re-running the summarizer
revalidates the raw evidence. Fresh wrapper runs execute a saved runner snapshot.

The historical independent-mutation failure is preserved in its own directory
and remains a rejected correctness experiment, not a timing comparator.
`SHA256SUMS` fingerprints every retained byte except itself.
