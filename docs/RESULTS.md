# Validated pilot results

The main comparison is the original one-column accelerator versus the
four-column accelerator on the **same** OoO CPU, cache/coherence system,
memory, clock, matrix input, and host invocation. Both use the same patched
gem5-Aladdin source. Each listed size passed separate full-output CPU and
accelerator checks with zero mismatches; the ROI checksums agreed. The
accelerator-host instruction counts matched between variants (21,600 at N=24;
30,046 at N=32).

| N | Base cycles | Four-column cycles | Cycle reduction | Base offload ticks | Four-column offload ticks | Offload reduction | Whole-program reduction |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 24 | 1,452 | 1,133 | 21.97% | 2,680,000 | 2,361,000 | 11.90% | 0.47% |
| 32 | 2,827 | 1,984 | 29.82% | 4,132,000 | 3,200,000 | 22.56% | 1.18% |

![Offload intervals for the two validated sizes](../results/offload_comparison.png)

The four-column accelerator versus an OoO CPU running the **same four-column
kernel** was 1.173x at N=24 and 1.524x at N=32 on whole-program ticks. This
is a secondary comparison. The original accelerator also outperformed its
own CPU version, so the baseline-to-extension columns above are the evidence
for the extension.

Full-check runs include a CPU reference GEMM after the accelerator and show
smaller whole-program differences: 136,062,000 versus 135,753,000 ticks at
N=24; 177,381,000 versus 176,575,000 at N=32. In the lightweight-check ROI,
the corresponding values are 60,962,000 versus 60,673,000 and 70,877,000
versus 70,042,000 ticks. Program startup and setup dilute the single-call
whole-program gain.

## Gate 3 addendum: N=16 (exploratory, not in the validated set)

Added 2026-09-26 as a first Gate 3 data point (`docs/NEXT_STEPS.md`: "Try
additional valid tile widths and input sizes"). **Not** run through
`scripts/run.sh`, which intentionally restricts to the two validated sizes
("Validated sizes are 24 and 32" — new sizes need their own correctness
check, per `docs/BUILD.md`); run directly via `scripts/run_inside.sh 16
{full,invocation,roi}` instead. Summarized with
[`scripts/explore_size.py`](../scripts/explore_size.py) — a parameterized
version of `scripts/summarize.py`'s exact row logic for arbitrary N, kept as
a separate script so the validated pipeline (`scripts/summarize.py`,
`results/validated_summary.csv`, `scripts/plot_results.py`,
`results/offload_comparison.png`) stays untouched and scoped to N=24/32
only. Exploratory sizes go in `results/exploratory_summary.csv` instead
(run `python3 scripts/explore_size.py 16` to regenerate, or add more sizes:
`python3 scripts/explore_size.py 16 40`). Raw results live at
`results/{fair,invocation,roi}_results/{base,tiled4}_n16/`, same layout as
N=24/32.

![Offload intervals including exploratory sizes](../results/offload_comparison_exploratory.png)

(Generate/refresh with `python3 scripts/plot_results_exploratory.py`, which
reads both CSVs; separate from the validated-only
`results/offload_comparison.png`.)

All the same checks passed: full-output CPU and accelerator checks (0
mismatches, both kernels), ROI checksums agree across all four runs
(checksum 8), accelerator-host instruction counts match between variants
(15,466).

| N | Base cycles | Four-column cycles | Cycle reduction | Base offload ticks | Four-column offload ticks | Offload reduction | Whole-program reduction |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 16 | 765 | 575 | 24.84% | 2,016,000 | 1,826,000 | 9.43% | 0.45% |

Area: 1.1926 million µm² (base) vs 1.20335 million µm² (four-column) — a
**0.90% increase**, much smaller than N=32's 27.7%. Cost/benefit at this size
looks different from N=24/32: the four-column accelerator is only 0.957x the
speed of an OoO CPU running the *same* four-column kernel (i.e. slightly
*slower* than its own CPU comparator) — versus 1.173x at N=24 and 1.524x at
N=32. Reported as-is; a negative/mixed result at one size doesn't invalidate
the positive results at the other two, but it does mean "the extension wins"
is size-dependent and should be stated that way in any report, not
generalized from N=24/32 alone.

Run `python3 scripts/summarize.py`; it derives
[`validated_summary.csv`](../results/validated_summary.csv) from the raw logs
and stats in `results/`. For example, N=32 full correctness is in
`results/fair_results/{base_n32,tiled4_n32}/gem5-*.log`; whole-program
`sim_ticks` are in `results/roi_results/.../m5out-*/stats.txt`; two labeled
invocation segments are in `results/invocation_results/.../m5out-*/stats.txt`.
The saved `config.ini` files provide the effective gem5 configurations.

The ratio formulas are `(base - four_column) / base` for reductions and
`same_kernel_cpu_ticks / four_column_accel_ticks` for CPU-relative speedup.
Ticks are gem5 simulation ticks, not wall-clock execution time.

## Cost and validity limits

The N=32 Aladdin area report increased from 1.247 to 1.592 million µm²
(27.7%).

**Update — "N=24 varied across otherwise matched reruns" resolved: it did
not.** Auditing every base_n24 area report on record shows `fair_results`,
`invocation_results`, and the pre-fix repeated-input diagnostic (which only
ever traced one real invocation, see below) all agree exactly: Total Area
1.40134e+06 µm², FU Area 598362 µm². The only base_n24 area report that ever
differed is `roi_results/base_n24` (1.33128e+06 µm²) — but that stage runs a
genuinely different, shorter ROI-bounded trace and a checksum-only check,
not a same-config rerun, so it was never a fair comparison. Same-stage,
same-input reruns of the single-invocation (REPS=1) case are area-stable,
including across independent from-scratch rebuilds on a different host (see
`docs/VALIDATION.md`'s 2026-09-26 entry) — so the area numbers reported
above for N=24/N=32 are not exploratory on repeatability grounds. Power has
not been validated.

**New, separate finding — area is not stable across repeated invocations
within one run.** The Gate 1 fix (below) made a second real accelerator
invocation possible for the first time. Comparing invocation 1 to invocation
2 of the *same* kernel in the *same* gem5 process
(`results/diagnostics/repeated_input_n24_fixed/`): MEM Area stays exactly
constant (802977 µm² both times, both kernels), but FU Area jumps
substantially — base_n24: 598362→832260 µm² (+39%); tiled4_n24:
593769→695405 µm² (+17%).

Traced this one level further in `src/aladdin/common/BaseDatapath.cpp`:
`fu_area` is driven by per-function peak concurrent resource counts
(`max_add`, `max_mul`, `max_reg`, ...), computed by `writePerCycleActivity()`
from `func_max_activity` — a map that is freshly constructed and populated
from scratch on every call (not a class member, not carried over from a
prior invocation), so this is not a stale-accumulator bug. The peak
concurrency itself genuinely differs between the two invocations' resource-
constrained schedules, even though both invocations run the identical static
loop nest. Leading hypothesis (not yet confirmed): Aladdin's dynamic trace
and DDDG node numbering is one continuous count across the whole run, not
reset per invocation — so invocation 2's nodes carry a different (larger)
absolute ID range than invocation 1's structurally-identical nodes. If the
scheduler's ready-list tie-breaking or partition/bank assignment depends on
absolute node ID (directly, or via a hash/modulo), an isomorphic DDDG could
still legitimately schedule differently on invocation 2, producing a
different concurrency peak without any bug in the accounting itself. Not yet
confirmed against the actual scheduler code (`Scheduler`/`schedule()` in the
same directory) — that would be the next step for anyone picking this up.
This does not affect any number published above (all are REPS=1,
single-invocation), but it means area is not yet a trustworthy metric for
any future repeated-invocation or "dynamic" area study — that would need its
own repeatability check, and likely a fix or normalization for the node-
numbering effect, before being reported.

**Update — Gate 1 dynamic-input failure root-caused and fixed.** The
repeated-input diagnostic originally changed A on the CPU between
invocations and found, at N=24, 19 full-output mismatches on both
accelerator variants while the CPU variants passed (raw logs in
`results/diagnostics/repeated_input_n24/`, kept as historical evidence). The
cause was a trace/harness mismatch, not a coherence bug: the `LLVM_TRACE`
build path in `benchmarks/*/​*.c` (used to generate `dynamic_trace.gz`) called
`gemm_kernel()` exactly once regardless of `REPS`, while the simulated
`GEM5_HARNESS` path called `invokeAcceleratorAndBlock()` `REPS` times against
CPU-modified input. On invocation 2+, Aladdin replayed a trace with no
remaining data ("Reached end of trace." with no new DDDG), so the
accelerator did zero work and the stale invocation-1 output was compared
against a CPU reference computed on the updated input — arithmetically this
explains the exact 19/24 mismatch count (only the row touched by the
single-element input change differs, minus the 5 columns where that row's
multiplier happens to be zero). Fixed by making the `LLVM_TRACE` path loop
`REPS` times with the same input mutation as the harness. Verified with a
REPS=2, N=24 repro for both kernels: invocation 2 now produces a full DDDG
(matching invocation 1's node count) and `GEMM passed: 0 mismatches` for both
accelerator and CPU variants (`results/diagnostics/repeated_input_n24_fixed/`).
The fix is a no-op for `REPS=1` (the default, used by every published
N=24/N=32 result above): the loop body is unchanged when `REPS=1` and the
input-mutation branch is gated on `REPS > 1`; confirmed by rebuilding N=24
`full` after the fix and diffing every simulated stat (excluding host
wall-clock fields) against a pre-fix rebuild on the same host — bit-identical.
This resolves Gate 1 for the fixed-trace-plus-repeat-invocation case tested
here; broader dynamic-input scenarios (e.g. input changing mid-computation,
not just between calls) are still out of scope. See `docs/NEXT_STEPS.md`.

The pilot has two N values and deterministic inputs. It establishes a
reproducible positive result in the model; it does not establish generality,
statistical confidence over workloads, dynamic coherence, or silicon behavior.
