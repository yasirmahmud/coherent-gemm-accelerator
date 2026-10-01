# Passive graph/cache diagnostic cohort

N=24, widths 1/2/4, issue limit 4. This separate diagnostic does not replace
published width or bandwidth points. Read `ANALYSIS.md`, `summary.csv`, and
`validation.json`; original raw evidence is under each variant/stage/mode.

Reference and instrumented stages use the same guest binary and trace for a
kernel. Widths 1/4 reuse bandwidth-cohort traces; width 2 generates one trace.
`trace-generation-source.c` for reused traces preserves the original source
rather than attributing their generation to a later benchmark snapshot.
The original reference simulator remains untouched. The separate diagnostic
build's complete Aladdin working diff, passive patch, build log, pinned
commits, executable fingerprints and CACTI inputs are retained in provenance.

The first observer attempt exposed pointer-temporary labels before
optimization. It was stopped, preserved locally in
`.artifacts/graph_n24_initial_labels/`, and not used for results. The final
observer uses read-only address-parent traversal to label pre-optimization
operations; the entire final width cohort was run and validated together.

`SHA256SUMS` fingerprints every retained file except itself. See
`docs/MECHANISM_DIAGNOSTICS.md` for definitions and fresh reproduction commands.
