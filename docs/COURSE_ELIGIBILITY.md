# Course-project eligibility checklist

The local course lecture notes describe a roughly one-month project, worth
40% of the course grade, with one proposal per team. The professor calls
OoO CPU plus coherent accelerator co-design an ambitious topic and expects
scope to be agreed before work is graded. The lecture's approximate October 1
proposal date must be checked against Canvas. Completion of an agreed proposal
can earn a good grade; no source promises full marks for this particular idea.

| Course expectation | Current evidence | Before submission/final report |
| --- | --- | --- |
| Accessible open-source base and tools | Harvard gem5-Aladdin and Aladdin source at pinned commits; Docker/LLVM/SCons/Python scripts | Verify instructor accepts this older toolchain and cite upstream licenses |
| Focused research question | Whether four-column A reuse reduces coherent GEMM offload latency enough to justify area | Agree fixed-trace scope or solve dynamic input correctness |
| Defined baseline, change one thing | One-column vs four-column kernels, same OoO CPU/Ruby/cache/clock and patch | Add controlled tile-width ablations and document all config differences |
| Specific mechanism and overhead | Share each A load across four accumulators; N=32 area estimate rises 27.7% | Resolve area repeatability; discuss resource and power cost |
| Empirical method and objective comparison | N=24/32 full checks, ROI stats, invocation intervals, same-kernel CPU comparator | Broaden workloads, repeat key points, plot data with units |
| Explain results and negative outcomes | Core and offload gains versus small whole-program gains; dynamic-input failure documented | Inspect queue/cache statistics and explain bottleneck/cost causally |
| Honest achievable deliverables | Build, run, raw logs, validator all in repo | Keep proposed work bounded to course time and available compute |

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
