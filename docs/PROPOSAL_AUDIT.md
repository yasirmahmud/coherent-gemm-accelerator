# Audit of the current proposal: 2026-09-30

**Execution update:** the audit below records the pre-implementation state.
The [immediate checklist](IMMEDIATE_NEXT_STEPS.md) and
[diagnostic evidence](MECHANISM_DIAGNOSTICS.md) now supersede its remaining-work
statuses. Graph attribution, validator hardening, repeated-call diagnostics,
width reporting and the final paper are complete. Miss-cause classification
uses the explicitly permitted aggregate alternative; historical provenance
gaps are inventoried rather than filled with inferred identities. The revised
proposal PDF remains two pages and contains planned work without measurements.

This audit checks `proposal/proposal.tex` against current code and retained
raw evidence. It does not change the proposal or disclose measurements in
the proposal PDF. Completion and a favorable performance outcome are
separate questions: a completed diagnostic can produce a negative result.

The core width and bandwidth experiments are complete. Every promise in the
proposal is not yet complete, and the measured results are not uniformly
positive. The outstanding items are mostly analysis, graphics, and writing.

## Claim-by-claim assessment

| Proposal location | Claim or commitment | Current completion evidence | Outcome / limitation |
| --- | --- | --- | --- |
| Lines 34–38 | Separate datapath, host-offload, and whole-program effects | Complete: full/ROI/invocation logs and summaries retain all three metrics | Tiling reduces datapath/offload time; whole-program benefit is much smaller and zero at N=8 |
| Line 38 | Baseline has `2N^3` source-level input loads and a serial accumulation per output | Established by the baseline C loop; no simulation is needed for this source-level count | This is not an issued-cache-request count or proof of the unique performance bottleneck |
| Lines 38, 87 | Test interaction between tile width and request issue capacity | Complete: six N=24 bandwidth points; final raw-evidence validator passes | Positive support for sensitivity: width-4 offload benefit increases from 4.669% to 7.268% to 12.033% at limits 1/2/4 |
| Lines 45–60, 93 | Specified CPU/cache/memory/clocks and bounded interface | Effective bandwidth configurations confirm CPU widths 8, ROB 192, LQ/SQ 32, CPU 2 GHz, system/Ruby/accelerator 1 GHz, L1D/L1I 64/32 kB, L2 2 MB, accelerator cache 32 kB/four-way/64-byte lines/32-entry queue; pinned runner requests 1 GB DDR3-1600 and verifies the common patch | A methodological control, not a performance result |
| Line 64 | Width-2/4 kernels share A across independent accumulators; source A loads become `N^3/w`; MAC count stays `N^3` | Established by all three kernel implementations; successful full checks confirm equivalent outputs at tested sizes | Positive implementation/correctness result; source counts do not establish physical traffic savings |
| Line 64 | Inspect optimized graph operations and establish which changes reach the interface | Partial: pre/post graph totals and optimization logs are retained, along with returned cache-operation counters | Operand-specific optimized load/MAC counts and the precise A-reuse-to-request mechanism are not established by the available analysis |
| Lines 84, 87, 128 | Assess concurrent-resource and area tradeoffs | Complete measurements: FU/MEM/total area in raw logs for main width points and bandwidth points | Mixed: width 4 has about 0.33% lower total modeled area at N=24 but about 27.69% higher at N=32; wider tiles are not uniformly cheaper |
| Lines 91, 134 | Pinned open-source tools, patch, source identities and reproduction commands | Complete: setup scripts, recorded revisions, image digest, patch, and cohort provenance | A reproducibility control; silicon performance is not demonstrated |
| Line 95 / Figure 3 | Main matrix: N=24/32 × widths 1/2/4 at issue limit 4 | Complete raw evidence: N=24 all widths in the published cohort; N=32 all widths in the recovered cohort | Positive internal/offload timing trends at both sizes; cohorts must be compared separately |
| Line 95 / Figure 3 | Bandwidth matrix: N=24 × widths 1/4 × issue limits 1/2/4 | Complete: 18 accelerator stages and two independent full-check CPU runs | Width 4 wins on offload time at all three limits; benefit shrinks under the tighter limit |
| Lines 60, 95 | Hold other hardware settings fixed; compare against the matching cohort baseline | Bandwidth validator compares all effective entries after names/paths are normalized. This audit also checked the named CPU/clock/cache/queue controls for all ten main/small-size points | Supported controls; the historical width/size configuration audit did not compare every effective entry |
| Line 95 | One trace per kernel shared across bandwidth settings | Complete: retained compressed traces, compressed/logical hashes, shared runner paths, and equal graph sizes across each kernel's bandwidth/stage runs | A valid control; traces are distinct between kernels |
| Line 121 | N=32 matrices occupy 12 kB, below 32 kB cache capacity | Established arithmetically: three arrays × 32² elements × four bytes | Does not imply absence of compulsory/conflict/coherence effects |
| Line 121 | Measure compulsory, conflict, and coherence effects | Partial: raw Ruby/cache statistics exist | No completed classification or controlled isolation of these three causes was found; aggregate misses are not that classification |
| Line 121 | N=8/16 comparisons and OoO CPU reference to test crossover | Complete: both widths have full/ROI/invocation and CPU evidence at both sizes; CSV also covers N=24/32 | Mixed: same-kernel CPU-relative speedup is 0.869× at N=8, 0.957× at N=16, about 1.173× at N=24 and 1.524× at N=32; crossover is bracketed, not precisely located |
| Lines 118, 121 | Full output checks at every single-invocation point; lightweight checks outside offload timing | Complete: this audit verified all ten size/width points and the six bandwidth points, including full CPU/accelerator checks and timing-stage checksum agreement | Positive correctness result within the fixed-trace input scope |
| Line 123 | Retain logs, effective configs, identities, hashes and automated validation | Complete for the new bandwidth cohort; historical cohorts retain varying subsets | Broader historical provenance retention is partial: some exact earlier rebuild artifacts were discarded, and compressed traces are not available for every old point |
| Line 123 | Bandwidth validator rejects incomplete/failed/altered/uncontrolled evidence | Implemented; eight rejection/acceptance tests passed in the implementation session; final validator re-run succeeds in this audit | Positive validation result. This does not fix the separate historical repeated-call summarizer's permissive validation |
| Line 123 | Matched-mutation repeated calls; check every output and distinguish first/later calls | Complete for saved N=24 base REPS=3: call indices 0/1/2 each have zero mismatches and paired timing blocks | Positive narrow correctness result. Cycles 1452/628/628 and changing offload ticks show different first/later operating points; warm timing remains harness-sensitive |
| Line 123 | Independent runtime mutation diagnostic to establish replay limits | Complete: three calls and timing records retained; summarizer exits with failure | Negative correctness result: 20/24/19 mismatches. This supports a fixed-trace limitation, not arbitrary runtime-input correctness |
| Line 123 | Paired rebuilds assess repeatability of modeled area | Supported within tested single-invocation cases: published/recovered N=24 FU/MEM/total area agree for both kernels; controlled full/ROI order test also agrees | Positive scoped repeatability; old baseline ROI MEM area remains discrepant and repeated-call resource estimates differ. Not a universal stability claim |
| Line 126 | Completion and return segments, 1 ns datapath conversion, residual and stability test | Complete for bandwidth cohort; all six measured residuals are 728 ns and return segments 471 ns | Positive support for constant measured non-datapath intervals in this cohort only; component causes are not separately isolated |
| Lines 126, 128 | Explain whether local gains survive in whole-program time | Measurements and bounded interpretation are available | Mixed: original width-4 whole-program reductions are 0%/0.446%/0.474%/1.178% at N=8/16/24/32; the new bandwidth cohort stays below 1% |
| Line 128 | Cache counts, mean latency, queue time, histogram samples, graph totals, area breakdown | Complete for bandwidth cohort: all are in raw logs/stats and summary CSV | Mixed counters: mean queue time falls with increasing issue limit, while mean access latency rises; request counts vary at tighter limits. No uniform traffic reduction is established |
| Lines 87, 128 | Latency–area comparison and interpretation of the preferred width | Partial: tables support comparisons, but the complete plotted analysis and final explanatory prose are unfinished | N=32 width 4 is faster and slightly smaller than width 2; width 1 has lower modeled area. No universal winner follows |
| Line 128 | Plots for bandwidth, CPU-by-size, and latency–area tradeoffs | Partial: bandwidth PNG/PDF/SVG and size-based offload PNGs exist | Missing completed width-1/2/4 plots at both sizes, CPU-speedup-versus-size plot, and latency–area plot |
| Lines 128, 131 | Distinguish associations from verified causes; explain all constraints | Partially written in notes; proposal correctly avoids a unique-bottleneck assertion | Issue-limit sensitivity is demonstrated. Precise causes of changed latency, merging counts, and warm-call behavior are not fully isolated |
| Line 131 | Kernels, runners, validation records, comparison tables and vector plots | Mostly complete: core code/data and bandwidth vector figures exist | Full all-width reporting/graphics remain incomplete |
| Line 131 | Final paper explaining results, cost and model limits | Not complete: `docs/REPORT_SKELETON.md` is explicitly a scaffold | Pending deliverable, with no final-paper result to assess |

## Checks performed for this audit

- Re-ran the bandwidth verifier against all six points and 18 stages.
- Independently checked ten retained main/small-size points for full CPU
  and accelerator passes, labeled invocation blocks, checksum agreement,
  cycles, area, graph totals, and timing metrics. Main N=24 all-width
  comparisons use the published cohort; main N=32 use the recovered cohort.
- Compared the named hardware controls across those ten points and
  inspected CPU pipeline/cache/memory settings in the effective bandwidth
  configuration.
- Verified both artifact manifests: 250 files in the bandwidth cohort and
  106 files in the recovered cohort.
- Read the actual matched and independent repeated-call logs; the matched
  summarizer reports three passing calls, while the independent diagnostic
  reports 63 total mismatches and exits nonzero.
- Compared N=24 area breakdowns across published and recovered cohorts.
- Inspected plotting scripts/artifacts and final-report files, rather than
  inferring completion from older checklist entries.

## What to tighten if every experiment promise must already be backed

1. Replace operand-specific graph/traffic attribution with the narrower
   commitment to compare graph totals and measured cache counters.
2. Replace the promise to measure compulsory/conflict/coherence causes with
   a promise to report aggregate cache/coherence counters and their limits.
3. Scope retained source/binary/trace provenance to the bandwidth cohort,
   with the existing artifacts supplied for historical comparisons.
4. Complete the promised all-width, CPU-versus-size, and latency–area plots
   before describing those graphics as already achieved.
5. Keep the final paper clearly identified as remaining writing work.

The independent mutation failure, small-N CPU losses, and modeled-area
increase should remain part of the research story. They do not undo the
positive core latency result; they constrain its scope.
