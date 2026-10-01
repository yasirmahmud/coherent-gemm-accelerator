# Repeated-call diagnostics

N=24, three calls, issue limit 4, cache/queue/clocks fixed. Each case/width shares one trace between correctness and timed harnesses.
Every correctness call passes a full output check. Timed runs omit per-call checks and pass a final checksum; their instruction sections are byte-identical across widths within each input case.
Mutation is pre-agreed at trace time; unchanged input is a separate trace/case. Each invocation resets statistics before the call and dumps after host return.

| Input | Width | Mode | Call | Datapath (cycles) | Offload (ticks) | Returned loads/stores | Access mean (ticks) | Queue mean (ticks) | Ruby hits/misses | FU area (µm²) | Multipliers/registers (32-bit) |
| --- | ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| matched | 1 | correctness | 0 | 1452 | 2620000 | 72/576 | 27518.8 | 30077.1 | 49/108 | 598362 | 72/737 |
| matched | 1 | correctness | 1 | 624 | 1257000 | 72/582 | 12025.7 | 14500.0 | 131/38 | 652684 | 49/1784 |
| matched | 1 | correctness | 2 | 628 | 1178000 | 72/583 | 12088.2 | 14435.0 | 135/37 | 744821 | 62/1834 |
| matched | 1 | timed | 0 | 1452 | 2886000 | 72/576 | 27518.8 | 30077.1 | 49/108 | 598362 | 72/737 |
| matched | 1 | timed | 1 | 246 | 772000 | 72/576 | 1140.3 | 8180.8 | 236/2 | 832260 | 72/1959 |
| matched | 1 | timed | 2 | 229 | 608000 | 72/576 | 658.8 | 7882.7 | 236/1 | 832260 | 72/1959 |
| matched | 2 | correctness | 0 | 1257 | 2425000 | 72/576 | 22432.1 | 25617.3 | 96/108 | 598362 | 72/737 |
| matched | 2 | correctness | 1 | 666 | 1299000 | 72/582 | 13195.8 | 15091.8 | 105/38 | 608870 | 55/1356 |
| matched | 2 | correctness | 2 | 666 | 1216000 | 72/584 | 13148.1 | 15114.5 | 99/37 | 446902 | 32/1273 |
| matched | 2 | timed | 0 | 1257 | 2833000 | 72/576 | 22432.1 | 25617.3 | 96/108 | 598362 | 72/737 |
| matched | 2 | timed | 1 | 246 | 772000 | 72/576 | 1112.7 | 8244.2 | 196/2 | 729858 | 72/1424 |
| matched | 2 | timed | 2 | 229 | 608000 | 72/576 | 640.5 | 7941.4 | 194/1 | 729858 | 72/1424 |
| matched | 4 | correctness | 0 | 1133 | 2301000 | 72/576 | 19915.2 | 21778.5 | 151/108 | 593769 | 72/713 |
| matched | 4 | correctness | 1 | 683 | 1316000 | 72/582 | 13616.5 | 15270.1 | 102/38 | 556964 | 54/1118 |
| matched | 4 | correctness | 2 | 687 | 1237000 | 72/590 | 13483.7 | 15438.6 | 100/37 | 453307 | 40/1041 |
| matched | 4 | timed | 0 | 1133 | 2612000 | 72/576 | 19915.2 | 21778.5 | 151/108 | 593769 | 72/713 |
| matched | 4 | timed | 1 | 246 | 772000 | 72/576 | 1109.7 | 8234.9 | 195/2 | 695788 | 72/1246 |
| matched | 4 | timed | 2 | 228 | 607000 | 72/576 | 635.8 | 7929.0 | 194/1 | 695405 | 72/1244 |
| unchanged | 1 | correctness | 0 | 1452 | 2620000 | 72/576 | 27518.8 | 30077.1 | 49/108 | 598362 | 72/737 |
| unchanged | 1 | correctness | 1 | 630 | 1264000 | 72/593 | 11921.3 | 14272.2 | 165/36 | 739811 | 72/1476 |
| unchanged | 1 | correctness | 2 | 627 | 1226000 | 72/584 | 12057.3 | 14429.5 | 163/36 | 743257 | 72/1494 |
| unchanged | 1 | timed | 0 | 1452 | 2681000 | 72/576 | 27518.8 | 30077.1 | 49/108 | 598362 | 72/737 |
| unchanged | 1 | timed | 1 | 227 | 819000 | 72/576 | 780.7 | 7734.6 | 272/1 | 759909 | 72/1581 |
| unchanged | 1 | timed | 2 | 227 | 669000 | 72/576 | 684.9 | 7827.2 | 276/0 | 759909 | 72/1581 |
| unchanged | 2 | correctness | 0 | 1257 | 2425000 | 72/576 | 22432.1 | 25617.3 | 96/108 | 598362 | 72/737 |
| unchanged | 2 | correctness | 1 | 679 | 1313000 | 72/579 | 13673.1 | 15508.9 | 98/36 | 446902 | 32/1273 |
| unchanged | 2 | correctness | 2 | 679 | 1278000 | 72/579 | 13673.1 | 15508.9 | 98/36 | 446902 | 32/1273 |
| unchanged | 2 | timed | 0 | 1257 | 2486000 | 72/576 | 22432.1 | 25617.3 | 96/108 | 598362 | 72/737 |
| unchanged | 2 | timed | 1 | 227 | 819000 | 72/576 | 970.8 | 7630.5 | 195/1 | 731198 | 72/1431 |
| unchanged | 2 | timed | 2 | 227 | 669000 | 72/576 | 598.8 | 7925.9 | 196/0 | 731198 | 72/1431 |
| unchanged | 4 | correctness | 0 | 1133 | 2301000 | 72/576 | 19915.2 | 21778.5 | 151/108 | 593769 | 72/713 |
| unchanged | 4 | correctness | 1 | 696 | 1330000 | 72/576 | 14153.1 | 15723.1 | 96/36 | 403262 | 32/1045 |
| unchanged | 4 | correctness | 2 | 696 | 1295000 | 72/576 | 14153.1 | 15723.1 | 96/36 | 403262 | 32/1045 |
| unchanged | 4 | timed | 0 | 1133 | 2362000 | 72/576 | 19915.2 | 21778.5 | 151/108 | 593769 | 72/713 |
| unchanged | 4 | timed | 1 | 246 | 838000 | 72/593 | 1027.3 | 8076.8 | 194/1 | 683921 | 72/1184 |
| unchanged | 4 | timed | 2 | 228 | 670000 | 72/576 | 601.9 | 7950.6 | 195/0 | 696554 | 72/1250 |

1 tick = 1 ps. Complete histogram sample counts, graph sizes, offload segments and memory area are in `summary.csv`.
The full checker reads A/B/C and performs CPU GEMM between calls. It changes cache/coherence state even though its runtime lies outside the measured invocation intervals.
The timed harness supplies the controlled across-width comparison; the correctness harness supplies every-call validation. They are distinct cache histories, so timed checksums alone do not prove every intermediate output.
First/later-call differences are associated with cache requests, queue subsets and resource peaks directly. They do not isolate warmth from scheduler/node ordering, input mutation or CPU work.
The historical independent-mutation fixture remains rejected with 20/24/19 mismatches and is excluded from timing comparisons.
Resource peaks are per-call pre-RTL model estimates, not a physical hardware reconfiguration or a steady-state area claim.
