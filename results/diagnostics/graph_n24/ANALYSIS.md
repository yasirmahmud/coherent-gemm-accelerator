# Source → graph → memory attribution

N=24, widths 1/2/4, issue limit 4. Reference and diagnostic runs reuse each kernel’s trace and each stage’s guest binary.
Full elementwise checks pass; every simulated statistics block and effective configuration matches the reference. Host wall-time/rate/memory statistics are excluded from equality checks.

| Width | Source A/B loads | Before connected A/B loads | After connected A/B loads | GEMM products/adds after | Accepted A/B loads | Accepted C stores | Returned loads/stores |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | 13824/13824 | 13824/13824 | 13824/13824 | 13824/13824 | 36/36 | 576 | 72/576 |
| 2 | 6912/13824 | 6912/13824 | 6912/13824 | 13824/13824 | 36/36 | 576 | 72/576 |
| 4 | 3456/13824 | 3456/13824 | 3456/13824 | 13824/13824 | 36/36 | 576 | 72/576 |

Full arithmetic/opcode and all/connected node totals, retries, queue joins, blocked attempts and blocked cycles are in `summary.csv`.
GEMM arithmetic is the backward value slice rooted at C-store value operands, stopping at loads and GEPs and excluding control/memory edges. Address computation is counted separately; integer adds are not all MACs.
All nodes are retained graph objects; connected nodes have at least one edge. Connected counts describe graph liveness, not a count of packets.
Accepted = successful initial sends plus successful retry sends, excluding the finish/control packet. Returned means data-cache response callbacks; both reconcile per array.
Queue-join nodes count each node’s first successful association with an already existing entry. Loads merge by cache-line address; repeated polls of a node do not increase this count.
Rejected initial sends are separate from successful retry sends. Blocked attempts count node polls; blocked cycles count distinct accelerator ticks per invocation.
The queue merges accesses after graph optimization. Fewer A loads at wider source/graph width do not imply fewer accepted requests in this cohort.
