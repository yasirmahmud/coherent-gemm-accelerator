# MEM Area order-dependence test (2026-09-27)

Tests whether the base_n24 `fair` vs. `roi` MEM Area discrepancy on record
(802,977 vs. 732,920 µm²) is caused by build/run **order** in a shared
`work_dir` (both stages normally reuse the same trace/`work_dir` in
`scripts/run_inside.sh`'s loop) or is inherent to the `roi` mode's build
flags themselves.

- **Test A**: one `work_dir`, `full` built+run first, then `roi` second
  (matches `run_inside.sh`'s normal mode order).
- **Test B**: a separate, fresh `work_dir`, `roi` built+run first, then
  `full` second (reversed order).

## Result

All four runs — both modes, both orders — report **identical** area:
Total 1.40134e+06 µm², FU 598362 µm², MEM 802977 µm². See `order_test_A_full.log`,
`order_test_A_roi.log`, `order_test_B_roi.log`, `order_test_B_full.log`
(`grep 'Area' *.log` to confirm).

Trace hashes differ between Test A and B (`order_test_A_trace.sha256` vs.
`order_test_B_trace.sha256`) despite both reproducing the same area —
expected, since gzip embeds non-deterministic metadata (timestamps) even
for byte-identical logical content; this confirms area depends on the
trace's logical content, not exact file identity.

## Conclusion

The `fair`-vs-`roi` MEM Area discrepancy does **not** reproduce in a
controlled, clean, same-host, same-build test, in either order. This means
the discrepancy on record between the committed `results/fair_results/base_n24`
(802,977 µm²) and `results/roi_results/base_n24` (732,920 µm²) most likely
does not come from an inherent difference between the `full` and `roi`
build flags/modes — it more likely reflects something about how/when those
two specific committed files were originally generated (e.g. a different
build session, or leftover state from the original author's broader
multi-run workflow spanning N=24/N=32 and multiple reruns, per
`docs/VALIDATION.md`'s original validation record) rather than a
reproducible property of this codebase's `full` vs. `roi` logic itself.

See `docs/RESULTS.md`'s "Cost and validity limits" section for how this
folds into the published record.
