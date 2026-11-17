# Speaker 1 timed script

**Slides 1–4. Target recording duration: 1 minute 41 seconds.**

Start your recording clock at zero. Each timestamp is elapsed time in your own recording. Read only the quoted text, starting at its cue and finishing before the next cue. The [recording plan](README.md) has file and pronunciation guidance.

## Slide 1 Introduction

**0:00.0**

*Start recording. Wait briefly for the first speaking cue.*

**0:00.5**

> Hi, we are Yasir, Rasin, and Mohyeu. Our project studies output-column reuse in a coherent GEMM accelerator: how computing several output columns together changes latency and hardware cost, and how the memory system affects those gains.

**0:14.7**

*Pause until the next speaking cue.*

## Slide 2 Why the problem matters

**0:16.2**

> Matrix multiplication, or GEMM, is central to machine learning and scientific computing. Accelerators speed it up, but they share caches, memory, and the host CPU. A faster accelerator therefore does not guarantee a faster application.

**0:30.5**

> Pre-RTL simulation lets us explore this before building hardware. As a preview, our improvement cuts offload time by about twenty-five percent at N equals thirty-two, while whole-program time falls by less than half a percent.

**0:46.5**

*Pause until the next speaking cue.*

## Slide 3 Architecture

**0:48.1**

> We modeled the system in gem5-Aladdin, which combines CPU and coherent memory simulation with a pre-RTL accelerator model. An out-of-order x eighty-six host invokes a trace-driven GEMM accelerator.

**1:01.0**

> Its requests pass through a thirty-two-entry queue into a thirty-two-kilobyte coherent cache, sharing a MESI memory system with the CPU. We vary output tile width and the number of cache requests allowed per accelerator cycle.

**1:15.7**

*Pause until the next speaking cue.*

## Slide 4 Experiments and handoff

**1:17.0**

> We studied four matrix sizes and three tile widths, memory issue limits, graph operations versus cache requests, and repeated accelerator calls. We used a CPU reference for correctness and validated configurations and outcomes across one hundred seven simulator runs.

**1:32.0**

> With that setup established, the next question is how wider output tiles improve execution, and what they cost.

**1:40.0**

*Remain quiet.*

**1:41.0**

*Your section is complete. Leave about one extra second of quiet, then stop recording.*
