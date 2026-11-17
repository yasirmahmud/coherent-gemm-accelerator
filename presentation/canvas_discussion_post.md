# Project Presentation: Group 13: Output-Column Reuse in a Coherent GEMM Accelerator

UNIVERSITY OF FLORIDA | EEL 5764 | GROUP 13

## Output-Column Reuse in a Coherent GEMM Accelerator

### Project Presentation

**[Click Here to Watch Video Presentation / Embed Video]**  
*(Duration: 4:59 | 11 Slides)*

*Group 13 | EEL 5764 Computer Architecture | University of Florida*

> How much faster does a coherent GEMM accelerator run when we eliminate redundant memory fetches through output-column reuse, and what system limits govern that gain?

We designed and implemented a tightly-coupled coherent GEMM accelerator integrated with an out-of-order x86 host CPU and a shared MESI cache hierarchy in **gem5-Aladdin**. To overcome the memory overhead of the baseline design, which repeatedly re-fetches the same matrix *A* elements, we enhanced the architecture with **output-column reuse ($w = 2, 4$)**, sharing loaded operands across parallel accumulators to eliminate redundant memory loads and unlock concurrent arithmetic.

Across **107 validated simulator runs** spanning matrix sizes $N = 8, 16, 24, 32$, we evaluate offload latency, memory request traffic, interface bandwidth limits ($b = 1, 2, 4$ requests/cycle), and modeled hardware cost. Our architectural improvement delivers up to a **25.1% offload latency reduction**, demonstrating that the speedup stems from **superior request scheduling** in the queue, while identifying the exact interface bandwidth required to translate local acceleration into end-to-end system performance.

### Project Team

**Yasir Mahmud** • **Rasin Mohammed Ihtemam** • **Mohyeu Hussain**

### Code, Results & Documentation

[https://github.com/yasirmahmud/coherent-gemm-accelerator](https://github.com/yasirmahmud/coherent-gemm-accelerator)
