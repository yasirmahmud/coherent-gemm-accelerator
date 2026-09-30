# Completed cache-bandwidth cohort: 2026-09-30

Six fresh N=24 points: widths 1/4 × cache issue limits 1/2/4 requests per
accelerator cycle. All 18 accelerator stages and both full-check CPU
references completed. See [SUMMARY.md](SUMMARY.md) for the generated table,
[summary.csv](summary.csv) for measurements, and
[the study description](../../../docs/CACHE_BANDWIDTH.md) for interpretation.

Each `points/<variant>_bw<limit>/` contains the requested accelerator
configuration and `full`, `roi`, and `invocation` directories. Each stage
retains its command, build log, binary hash, simulator log, effective
configuration, raw statistics, and Aladdin model outputs. `inputs/` retains
both benchmark source snapshots, one compressed trace per kernel, compressed
and logical trace hashes, trace-build logs, and full CPU checks.

`provenance/` retains the actual runner snapshots, final summarizer/plotter
and validation test, image digest, source revisions/diffs, simulator hash,
common build/CACTI inputs, host/timestamp records, and plotting dependencies.
The simulator hash was independently checked against the existing binary
after completion. The source checkout was read-only throughout the run.
The gem5 working diff was captured afterward from that unchanged checkout;
the Aladdin working diff was captured before the runs.

The local engine was rootless Podman using its existing image store and
the prebuilt source checkout. The portable entry point is
`bash scripts/run_cache_bandwidth.sh`; its source and engine overrides are
documented in the study description. The recorded public runner predates
the extra gem5 working-diff capture added after the study; that logging
addition changes no simulation arguments or measurements.

The final validator rejects missing points/stages, missing or failed output
checks, altered traces, wrong effective issue limits, uncontrolled hardware
configuration changes, differing stage-specific binaries, mismatched output
checksums, and invalid invocation timing blocks. Eight tests exercise the
passing cohort and several malformed-evidence cases.

Run from the repository root:

```bash
python3 scripts/summarize_cache_bandwidth.py results/cache_bandwidth/n24_20260930
python3 -m unittest discover -s tests -p 'test_cache_bandwidth.py'
```

Run `sha256sum -c SHA256SUMS` from this directory to check the retained
artifact hashes. Generated filesystem redirect trees (`fs/`) are excluded
from the manifest and versioned evidence. The summarizer and plotter update
the manifest after regenerating their artifacts.

Figures are supplied in PNG, PDF, and SVG formats. Raw area estimates are
diagnostic only: unchanged CACTI inputs do not model physical cache-port cost
across issue limits. These results are a separate cohort and must not be
mixed with historical baseline ticks or host instruction counts.
