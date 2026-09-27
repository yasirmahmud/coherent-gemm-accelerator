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

## Gate 3 addendum: N=8 and N=16 (exploratory, not in the validated set)

Added 2026-09-26 as the first Gate 3 data points (`docs/NEXT_STEPS.md`: "Try
additional valid tile widths and input sizes"). **Not** run through
`scripts/run.sh`, which intentionally restricts to the two validated sizes
("Validated sizes are 24 and 32" — new sizes need their own correctness
check, per `docs/BUILD.md`); run directly via `scripts/run_inside.sh {8,16}
all` instead. Summarized with
[`scripts/explore_size.py`](../scripts/explore_size.py) — a parameterized
version of `scripts/summarize.py`'s exact row logic for arbitrary N, kept as
a separate script so the validated pipeline (`scripts/summarize.py`,
`results/validated_summary.csv`, `scripts/plot_results.py`,
`results/offload_comparison.png`) stays untouched and scoped to N=24/32
only. Exploratory sizes go in `results/exploratory_summary.csv` instead
(run `python3 scripts/explore_size.py 8 16` to regenerate, or add more
sizes: `python3 scripts/explore_size.py 8 16 40`). Raw results live at
`results/{fair,invocation,roi}_results/{base,tiled4}_n{8,16}/`, same layout
as N=24/32.

![Offload intervals including exploratory sizes](../results/offload_comparison_exploratory.png)

(Generate/refresh with `python3 scripts/plot_results_exploratory.py`, which
reads both CSVs; separate from the validated-only
`results/offload_comparison.png`.)

All the same checks passed at both sizes: full-output CPU and accelerator
checks (0 mismatches, both kernels), ROI checksums agree across all four
runs, accelerator-host instruction counts match between variants.

| N | Base cycles | Four-column cycles | Cycle reduction | Base offload ticks | Four-column offload ticks | Offload reduction | Whole-program reduction | Four-col vs same-kernel CPU |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 8 | 276 | 250 | 9.42% | 1,370,000 | 1,344,000 | 1.90% | 0.00% | 0.869x |
| 16 | 765 | 575 | 24.84% | 2,016,000 | 1,826,000 | 9.43% | 0.45% | 0.957x |
| 24 (validated) | 1,452 | 1,133 | 21.97% | 2,680,000 | 2,361,000 | 11.90% | 0.47% | 1.173x |
| 32 (validated) | 2,827 | 1,984 | 29.82% | 4,132,000 | 3,200,000 | 22.56% | 1.18% | 1.524x |

**Correction (2026-09-27):** offload-interval reduction is cleanly monotonic
across all four sizes (1.9% → 9.4% → 11.9% → 22.6%). The **CPU-relative
speedup column is also monotonically increasing** (0.869x → 0.957x →
1.173x → 1.524x) — an earlier version of this doc incorrectly called this
column non-monotonic too; it is not. What **is** non-monotonic is the raw
*cycle-reduction percentage*: N=16 (24.84%) is numerically higher than N=24
(21.97%), even though N=16's CPU-relative speedup (0.957x) is still lower
than N=24's (1.173x) — cycle reduction and CPU-relative speedup are
different metrics and can rank sizes differently; neither is "the" size
trend on its own.

N=8 is the weakest point: cycles improve (9.42% reduction) and offload
improves (1.90% reduction), but whole-program time is unchanged (exactly
0.00% — `base_accel_ticks` and `tiled_accel_ticks` are tick-for-tick
identical, 48,694,000 both) and CPU-relative speedup is below 1x (0.869x,
i.e. the four-column accelerator is slower than an OoO CPU running the same
four-column kernel at this size). At N=8, area even decreases very slightly
for the four-column variant (1,004,980 → 1,003,450 µm², −0.15%) instead of
growing. Read together: the four-column reuse benefit is genuinely
size-dependent, not a single clean scaling trend across every metric, and is
weakest at small N — most plausibly because fixed per-invocation overhead
(host wake-up, queue/cache warm-up, program startup) dominates when there's
little actual work to amortize it over. This should be stated precisely in
any report (which metric, at which size) rather than as a single blanket
"benefit grows with size" claim.

Area: at N=16, 1.1926 million µm² (base) vs 1.20335 million µm² (four-column)
— a 0.90% increase, much smaller than N=32's 27.7%; area growth is not
monotonic in N either.

## Gate 3 addendum: tile-width ablation (N=24, exploratory)

Added 2026-09-26, per the README's own "what to do next" #3: "include an
ablation of output tile width." The N-sweep above confounds tile width with
problem size (bigger N means both more reuse *and* more fixed overhead to
amortize); this ablation holds N=24 fixed and only varies tile width (1, 2,
4 output columns per inner-loop iteration), isolating the tiling effect
cleanly. Added [`benchmarks/gemm_tiled2/`](../benchmarks/gemm_tiled2/) — a
2-column variant, otherwise identical in structure and hardware config
(`.cfg` files copied verbatim from `gemm_tiled4/`) to the existing 1-column
base and 4-column extension. Not wired into `scripts/run.sh`'s two-variant
loop (`base`/`tiled4` only); built and run manually via the same
`make ... run-trace` / `gem5-accel`/`gem5-cpu` / `aladdin_se.py` invocations
`scripts/run_inside.sh` uses, at N=24. Passed the same checks: 0 mismatches
(accelerator and CPU), accelerator-host instruction count matches the other
two variants exactly (21,600).

**Correction (2026-09-27):** the tile-1 "vs. same-kernel CPU" value below was
previously (incorrectly) shown as "1.000x (reference)" as if tile-1 were a
trivial normalization point. It is an actual measured ratio like the other
two rows (70,973,000 CPU ticks / 60,962,000 accelerator ticks = **1.164x**)
and is corrected below. Do not read any row in this column as a fixed
reference — every row is an independently measured same-kernel CPU
comparison.

| Tile width | Cycles | Cycle reduction vs. tile-1 | Offload ticks | Offload reduction vs. tile-1 | Area (µm²) | Area change vs. tile-1 | vs. same-kernel CPU |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 (base) | 1,452 | — | 2,680,000 | — | 1,401,340 | — | 1.164x |
| 2 | 1,257 | 13.43% | 2,508,000 | 6.42% | 1,401,340 | 0.00% | 1.164x |
| 4 | 1,133 | 21.97% | 2,361,000 | 11.90% | 1,396,750 | −0.33% | 1.173x |

With N held fixed, the benefit is clean, monotonic, and shows textbook
diminishing returns: cycle count drops by a smaller *relative* amount on
each width-doubling (1,452→1,257 is −13.43%; 1,257→1,133 is a further
−9.86%), consistent with a fixed per-inner-loop-iteration overhead being
amortized across more accumulators each time, with less overhead left to
amortize at each step. Area is flat: tile-width 2 costs exactly the same
area as tile-width 1 (0.00% change — likely still within the same resource
bucket the synthesis tool allocates), and even tile-width 4 costs *less*
area than tile-width 1 here (−0.33%), sharply unlike N=32's 27.7% area
growth for the same tile-width-4 kernel. Put together with the N-sweep
above: area cost is driven far more by problem size (N) than by tile width
in this design, at least across the widths and sizes tested so far — a
useful, non-obvious distinction for framing the "hardware cost" question in
Gate 2/Gate 4. This is a single N; whether the diminishing-returns shape
holds at other N (e.g. does tile-width 8 continue the pattern, or does it
invert like N=8 did in the size sweep?) is unexplored.

**Queue/cache traffic** (Gate 3 in `docs/NEXT_STEPS.md` explicitly asks for
this, not covered above). From each accelerator datapath's gem5 stats
(`system.gemm_*_datapath.*` in the fair-stage `m5out-accel`/`m5out-cache`
`stats.txt`):

| Tile width | dcache loads | dcache stores | TLB hits | TLB misses | TLB hit rate | Mean dcache access latency (ticks) |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 (base) | 72 | 576 | 648 | 64 | 0.9101 | 27,518.8 |
| 2 | 72 | 576 | 648 | 64 | 0.9101 | 22,432.1 |
| 4 | 72 | 576 | 648 | 64 | 0.9101 | 19,915.2 |

**Correction (2026-09-27): stated as an observation, not yet a verified
causal explanation.** Raw access **counts** (loads, stores, TLB hits/misses,
`total_dcache_loads`/`total_dcache_stores` as reported by Aladdin) are
exactly identical across all three tile widths, and the mean per-access
dcache latency drops monotonically: 27,518.8 → 22,432.1 → 19,915.2 ticks as
tile width goes 1→2→4, tracking the same diminishing-returns shape as the
cycle/offload numbers above. These two observations are solid. What is
**not** yet verified is *why*: an earlier version of this doc asserted this
means reuse "reduces contention per access, not data volume" as if that
were confirmed. It is a plausible reading, not a demonstrated mechanism —
the request-count fields checked so far are access counts, not raw byte
counts, and no controlled instrumentation has isolated queueing/contention
as the specific cause of the latency drop (as opposed to, say, a scheduling
artifact of the kind discussed just above for the repeated-invocation FU
Area/cycle findings). Treat "equal traffic, lower mean latency" as the
finding, and "reduced contention" as a hypothesis for it, until byte counts
and a specific causal mechanism are checked.
`total_acp_loads`/`total_acp_stores`/`cache_queue_reads`/`cache_queue_writes`
are all 0 in every run here — this benchmark's `memory_type = cache`
configuration routes accesses through the TLB+dcache path, not the separate
ACP queue path, so those particular counters aren't populated for any tile
width and shouldn't be read as "no queueing happened."

## How to audit the numbers

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

**Update — "N=24 varied across otherwise matched reruns" partially resolved,
partially corrected (2026-09-27).** Auditing every base_n24 area report on
record shows `fair_results`, `invocation_results`, and the pre-fix
repeated-input diagnostic (which only ever traced one real invocation, see
below) all agree exactly: Total Area 1.40134e+06 µm², FU Area 598362 µm².
Same-stage, same-input reruns of the single-invocation (REPS=1) case are
area-stable, including across independent from-scratch rebuilds on a
different host (see `docs/VALIDATION.md`'s 2026-09-26 entry). Power has not
been validated.

However, the explanation previously given here for `roi_results/base_n24`'s
different area (1.33128e+06 µm², MEM Area 732,920 vs 802,977 — a 70,057 µm²
gap) was **wrong and is retracted**: it claimed the ROI stage runs a
"genuinely different, shorter ROI-bounded trace." It does not. The `fair`
and `roi` gem5-cache.log for base_n24 report the **identical** trace: Num of
Nodes 198290, Num of Edges 451248, Total connected nodes 170042, and
identical Aladdin Cycle count (1452) — same DDDG, same accelerator config
(`gem5_cache.cfg` is not mode-dependent), yet different MEM Area. **The
actual cause is unresolved.** Candidates not yet ruled out: some
order/caching effect in how Aladdin's CACTI-based area modeling is invoked
across the `full`→`roi`→`invocation` mode loop sharing one `work_dir`
(`scripts/run_inside.sh` builds the trace once and reuses `work_dir` for all
three modes), or a genuine tool nondeterminism unrelated to trace content.
Until this is isolated with a controlled pair (matching trace SHA-256,
configs, and CACTI inputs/outputs saved side-by-side), **treat MEM Area for
base_n24 as having two disagreeing measurements on record, not a single
validated number** — the `fair_results` value (802,977 µm², matching every
other independent measurement) is the one used in the headline area numbers
above, but the discrepancy itself is not explained away.

**New, separate finding — neither area nor cycle count is stable across
repeated invocations within one run, and this must not be read as "the
per-call cost."** The Gate 1 fix (below) made a second real accelerator
invocation possible for the first time. Comparing invocation 1 to invocation
2 of the *same* kernel in the *same* gem5 process
(`results/diagnostics/repeated_input_n24_fixed/`): MEM Area stays exactly
constant (802977 µm² both times, both kernels), but FU Area jumps
substantially — base_n24: 598362→832260 µm² (+39%); tiled4_n24:
593769→695405 µm² (+17%). **More strikingly, invocation 2's Aladdin cycle
count collapses relative to invocation 1**, despite an *identical* DDDG
(same Num of Nodes 198290, Num of Edges 451248, Total connected nodes
170042 in both invocations — confirmed by direct inspection, this is not a
truncated or partial re-trace): base_n24 1452→**229** cycles; tiled4_n24
1133→**228** cycles. That is an 84%/80% cycle-count drop for structurally
the same computation. First-call cycle/area numbers must not be assumed to
carry over to a "warm" second call — they are a different measurement, not
a steady-state per-call cost, and neither the fast cycle count nor the
larger area from invocation 2 should be cited as a repeated-call figure
until this is understood.

Traced this one level further in `src/aladdin/common/BaseDatapath.cpp`:
`fu_area` is driven by per-function peak concurrent resource counts
(`max_add`, `max_mul`, `max_reg`, ...), computed by `writePerCycleActivity()`
from `func_max_activity` — a map that is freshly constructed and populated
from scratch on every call (not a class member, not carried over from a
prior invocation), so this is not a stale-accumulator bug. The peak
concurrency itself genuinely differs between the two invocations' resource-
constrained schedules, even though both invocations run the identical static
loop nest and identical DDDG.

Two candidate mechanisms, neither confirmed:
1. Aladdin's dynamic trace and DDDG node numbering is one continuous count
   across the whole run, not reset per invocation — so invocation 2's nodes
   carry a different (larger) absolute ID range than invocation 1's
   structurally-identical nodes. If the scheduler's ready-list tie-breaking
   or partition/bank assignment depends on absolute node ID, an isomorphic
   DDDG could still legitimately schedule differently.
2. **Cache/queue warmth.** This is a *coherent private-cache* accelerator,
   and invocation 2 reuses the same array addresses invocation 1 just
   accessed. If Aladdin's memory-latency model treats those addresses as
   already resident (lower modeled latency on the second access), the
   scheduler would face far less memory-stall pressure on invocation 2 —
   which would independently explain *both* new findings together: fewer
   cycles (less stalling) and higher peak concurrent resource usage (more
   ops become schedulable per cycle once memory is no longer the
   bottleneck). This would make the invocation-2 numbers a genuine
   "warm-cache" measurement, not a bug — but it still means invocation-1
   ("cold") and invocation-2 ("warm") are two different operating points
   that must be labeled and reported separately, never averaged or treated
   as one steady-state per-call cost.

Distinguishing these (or finding both partially responsible) needs the
per-call memory-latency breakdown from a proper `INVOCATION_STATS`-instrumented
REPS=2 rerun (segmenting `dcache_latency`/TLB stats per call) and/or reading
Aladdin's scheduler (`Scheduler`/`schedule()` in the same directory) directly
— not yet done. This does not affect any number published above (all are
REPS=1, single-invocation), but it means area *and* cycle count are not yet
trustworthy metrics for any future repeated-invocation or "dynamic" study —
that would need its own repeatability check and a resolved mechanism before
being reported.

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
not just between calls) are still out of scope. **A further, more specific
limit**: the fix works by making the trace generator apply the exact same
predetermined mutation (`A[rep % (N*N)] += 1`) that the runtime harness
also applies — tracer and harness are synchronized on an identical,
hardcoded pattern, not on an arbitrary runtime CPU write. Correctness has
only been demonstrated for *that* pre-agreed mutation, not for an
independent/unpredictable CPU-side change decided at runtime. See also the
invocation-2 cycle-count anomaly above (1452→229, 1133→228 cycles) — the
fix makes the accelerator do *real, structurally-identical* work on
invocation 2 (verified: same DDDG), and the final output is verified
correct, but the invocation-2 *timing* itself is not yet understood and
should not be read as "the" per-call cost. See `docs/NEXT_STEPS.md`.

The pilot has two N values and deterministic inputs. It establishes a
reproducible positive result in the model; it does not establish generality,
statistical confidence over workloads, dynamic coherence, or silicon behavior.
