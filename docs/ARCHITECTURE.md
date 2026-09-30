# System architecture

Referenced by `docs/REPORT_SKELETON.md` §2. Parameters here are pulled
directly from `benchmarks/*/gem5*.cfg` and `docs/BUILD.md`'s "What is
measured" — cross-check against those files if this drifts.

```mermaid
flowchart TB
    subgraph CPU_side["Host: out-of-order CPU"]
        CPU["x86 DerivO3CPU<br/>2 GHz"]
    end

    subgraph Coherence["Ruby coherent memory system"]
        MESI["MESI_Two_Level_aladdin protocol"]
        DRAM["1 GB DDR3_1600_8x8"]
    end

    subgraph Accel["Aladdin accelerator (HybridDatapath)"]
        direction TB
        Sched["Resource-constrained scheduler<br/>(BaseDatapath: DDDG replay,<br/>dependency-driven, 1 cycle = 1 ns)"]
        AccelCache["32 kB private coherent cache<br/>(memory_type = cache)<br/>64B lines, queue size 32, bandwidth 4"]
        Sched <--> AccelCache
    end

    CPU -- "mapArrayToAccelerator (A, B, C)<br/>invokeAcceleratorAndBlock" --> Accel
    CPU <-- "Ruby coherence traffic" --> MESI
    MESI <--> DRAM
    AccelCache <-- "Ruby coherence traffic<br/>(accelerator_id 16777216)" --> MESI

    style CPU_side fill:#e8f0fe,stroke:#5271a3
    style Coherence fill:#fdf3e7,stroke:#e68a40
    style Accel fill:#eafaf1,stroke:#2e8b57
```

## What differs between kernel variants

The **only** changed variable across `benchmarks/gemm_acp_pilot/` (1
column), `benchmarks/gemm_tiled2/` (2 columns), and `benchmarks/gemm_tiled4/`
(4 columns) is how many output columns share each loaded A element inside
the accelerator's inner loop (`gemm_kernel()`'s `loop_j` step size and
accumulator count). CPU model, Ruby coherence protocol, cache size/config,
clock, DRAM, and host invocation protocol (`mapArrayToAccelerator` /
`invokeAcceleratorAndBlock`) are held identical across every variant and
every N — see the `.cfg` files, which are copied verbatim between variants
specifically to hold this fixed.

## What "repeated invocation" means in this diagram

For the Gate 1 dynamic-input tests (`scripts/run_repeated.sh`), the CPU
calls `invokeAcceleratorAndBlock()` more than once in a loop, mutating array
`A` between calls. The accelerator's *private cache* (top box above) is not
reset between these calls — so a second call can find data already resident
from the first call's accesses. This is the physical basis for the
"cold vs. warm invocation" distinction throughout `docs/RESULTS.md`: it is
a real property of this coherent-cache design, not a simulation artifact.
