# Completed analysis artifacts

`width_summary.csv`, `width_validation.json` and `WIDTH_SUMMARY.md` use
published N=24 and recovered N=32 cohorts separately. The latency, CPU-speedup
and latency/area figures are available as SVG, PDF and PNG. Figure provenance
and units are labeled; functional-unit and memory area are separate.

`cache/` inventories aggregate cache counters and retains the pinned source
implementation used to check their definitions. It reports no unsupported
miss-cause classifications. `repeated_historical_validation.json` records the
passing matched fixture; the independent mutation is intentionally excluded.

Generation commands are in `docs/MECHANISM_DIAGNOSTICS.md`. Historical identity
limits are in `results/provenance/historical_20260930/`. The original bandwidth
figures and timing decomposition remain in their existing isolated cohort.
`SHA256SUMS` covers retained analysis artifacts except itself.
