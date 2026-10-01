# Aggregate accelerator cache analysis

Pinned protocol counter definitions are retained in `implementation/`. Statistics are from the reset-to-datapath-completion block only; host return is separate.

| Width | Issue limit | Returned loads/stores | Ruby demand hits/misses | Access latency (ticks) | Queue samples | Queue mean (ticks) |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | 1 | 74/610 | 123/108 | 23627.0 | 624 | 37070.5 |
| 1 | 2 | 72/576 | 80/108 | 26563.2 | 587 | 33790.5 |
| 1 | 4 | 72/576 | 49/108 | 27518.8 | 584 | 30077.1 |
| 4 | 1 | 74/602 | 306/108 | 18522.4 | 626 | 40055.9 |
| 4 | 2 | 72/577 | 166/108 | 19624.8 | 596 | 31941.3 |
| 4 | 4 | 72/576 | 151/108 | 19915.2 | 587 | 21778.5 |

1 tick = 1 ps. Demand misses include a store upgrade from Shared to Modified; they are not solely absent-line misses.
The L1 controller profiles mandatory protocol actions. The sequencer can alias multiple requests to a cache line, so controller actions need not equal datapath returned operations.
Latency samples equal returned loads plus stores; demand accesses equal demand hits plus misses at every point.
Queue samples omit successful retry issuance in this pinned implementation; their means describe that subset.
The unused ACP sequencer cache and accelerator instruction cache report zeros; these do not establish an absence of data-cache misses.
Global Ruby latency histograms include CPU traffic and cannot be treated as accelerator-only samples.

No retained line-level demand sequence with invalidation/ownership events or fully-associative shadow replay exists for this cohort.
We therefore report no compulsory/capacity/conflict/coherence partition. The 108 demand misses at N=24 do not prove any such partition, even though they equal the three matrices’ nominal cache-line count.
CPU conflicting-load counters describe CPU load/store ordering, not accelerator cache conflicts.
A shadow classifier and event observer are skipped under task 2’s aggregate-analysis alternative; the proposal promises aggregate measurements and states the attribution limit.
No timing instrumentation or simulator changes were needed for this analysis; original raw evidence and validation remain intact.
