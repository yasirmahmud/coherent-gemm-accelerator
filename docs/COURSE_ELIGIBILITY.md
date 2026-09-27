# Course-project eligibility checklist

The local course lecture notes describe a roughly one-month project, worth
40% of the course grade, with one proposal per team. The professor calls
OoO CPU plus coherent accelerator co-design an ambitious topic and expects
scope to be agreed before work is graded. The lecture's approximate October 1
proposal date must be checked against Canvas. Completion of an agreed proposal
can earn a good grade; no source promises full marks for this particular idea.

| Course expectation | Current evidence | Before submission/final report |
| --- | --- | --- |
| Accessible open-source base and tools | Harvard gem5-Aladdin and Aladdin source at pinned commits; Docker (or rootless Podman, see [BUILD.md](BUILD.md))/LLVM/SCons/Python scripts | Verify instructor accepts this older toolchain and cite upstream licenses |
| Focused research question | Whether four-column A reuse reduces coherent GEMM offload latency enough to justify area; a tile-width-focused framing ("How does output-column tile width affect offload latency and modeled hardware cost?") is also supported by new N=24 tile-1/2/4 data | Agree exact scope/wording with the instructor (see `docs/NEXT_STEPS.md` §1); confirm deadline on Canvas |
| Defined baseline, change one thing | One-column vs four-column kernels, same OoO CPU/Ruby/cache/clock and patch; **new:** a controlled tile-1/2/4 ablation at fixed N=24, isolating tile width from problem size | Document the tile-2 run as a repeatable command, not a manual one-off (`docs/NEXT_STEPS.md` §3) |
| Specific mechanism and overhead | Share each A load across four accumulators; N=32 area estimate rises 27.7%, but at N=24 tile-width alone barely moves area (0.00%, −0.33%) — area cost tracks problem size more than tile width | Resolve the still-unexplained base_n24 `fair` vs `roi` MEM Area discrepancy (802,977 vs 732,920 µm², identical trace) before citing area as settled; discuss power cost (not yet measured) |
| Empirical method and objective comparison | N=8/16/24/32 full checks, ROI stats, invocation intervals, same-kernel CPU comparator; CPU-relative speedup increases monotonically with N (0.869x→0.957x→1.173x→1.524x) | Broaden workloads (representative inference layer), repeat key points, plot data with units |
| Explain results and negative outcomes | Core and offload gains versus small/zero whole-program gains at small N (N=8: exactly 0.00%); dynamic-input diagnostic now passes for the tested (predetermined-mutation, between-call) case, with its remaining scope limits stated explicitly | Test an independent/unpredictable runtime input mutation, not just the predetermined one; explain the repeated-invocation cycle-count/area anomaly (1452→229 cycles) before citing repeated-call numbers |
| Honest achievable deliverables | Build, run, raw logs, validator all in repo; exploratory sizes/tile-widths kept clearly separate from the validated N=24/32 pipeline | Keep proposed work bounded to course time and available compute |

## Four proposal questions

1. **Research question:** Does reusing each A element across four neighboring
   output columns reduce the accelerator offload interval on a coherent
   private-cache path enough to outweigh extra arithmetic/state?
2. **Mechanism:** Four independent sums are updated per loaded A value. The
   host, CPU model, coherence configuration, and cache settings remain fixed.
3. **Overhead:** Additional live accumulators and parallel arithmetic; the
   N=32 area report suggests a substantial cost. Area estimates and power
   require further validation.
4. **Method:** Pinned gem5-Aladdin, x86 `DerivO3CPU`, Ruby
   `MESI_Two_Level_aladdin`, Aladdin `HybridDatapath`, 32 kB accelerator
   cache; full correctness, segmented offload ticks, accelerator cycles,
   whole-program ticks, CPU comparator, area, and queue/cache statistics.

Expected outcome: lower accelerator cycles and offload latency when reuse
dominates, but limited whole-program gain for a single small invocation.
Negative or mixed results should be reported rather than discarded. Team
members must understand and defend the code and methodology themselves.
