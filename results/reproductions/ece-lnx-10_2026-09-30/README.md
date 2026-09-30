# Recovered reproduction evidence: ece-lnx-10, 2026-09-30

Copied from the workspace's ignored `.artifacts/results/` on 2026-09-30.
The original published `results/{fair,roi,invocation}_results/` are retained.
This archive contains five complete experiment points: base and tiled4 at
N=24, and base, tiled2, and tiled4 at N=32. Each point has full-output,
ROI, and segmented invocation evidence. The N=32 width-2 run is complete;
its absence from the published directories did not mean it was unrun.

`summary.csv` was extracted from these archived logs and stats. Full CPU
and accelerator checks passed; all ROI/invocation checksums match within
each size; accelerator-host instruction counts match across widths.
All accelerator stages have matching CPU type, cycle time, cache size,
associativity, line size, queue capacity, and bandwidth in `config.ini`.
Configuration comparison covered those named settings, not every parameter.

Compare widths using the baseline from this same archive. Absolute offload
timing differs from the original published cohort; do not combine its
baseline with these measurements. This archive contains no tiled2 N=24
run. That point exists in the original published cohort.

`SOURCE_RECORD.md` is the original local reproduction note, copied without
rewriting its historical paths. `provenance/` retains the actual runner
copies used locally; they depend on the original container mounts and are
records, not standalone reproduction commands. Original build logs (named `build-record.log` to survive the repository
ignore rules) and trace hashes are retained where present. The simulator build, image store,
and full trace files were not copied. The source record's executable hash
is recorded provenance and was not independently rehashed during recovery.

`SHA256SUMS` fingerprints every archived file except itself. Verify from
this directory with `sha256sum -c SHA256SUMS`. Compressed-trace hashes
identify the original `.gz` files; without those files they cannot prove
logical trace equality between different runs.
