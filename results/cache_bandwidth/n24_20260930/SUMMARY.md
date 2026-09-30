# Cache-bandwidth sensitivity: N=24

One cohort; widths 1/4; 1/2/4 issued cache requests per accelerator cycle.

All six full accelerator checks and both CPU reference checks pass.
One trace per kernel is reused across bandwidth settings. Effective configurations
are compared across all six points within each measurement stage.

| Bandwidth | Width | Datapath cycles | Offload ticks | Offload reduction vs width 1 | Mean cache latency (ticks) | Mean queue time (ticks) |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | 1 | 1,714 | 2,913,000 | 0.000% | 23627.001 | 37070.513 |
| 1 | 4 | 1,578 | 2,777,000 | 4.669% | 18522.404 | 40055.911 |
| 2 | 1 | 1,539 | 2,738,000 | 0.000% | 26563.165 | 33790.460 |
| 2 | 4 | 1,340 | 2,539,000 | 7.268% | 19624.777 | 31941.275 |
| 4 | 1 | 1,452 | 2,651,000 | 0.000% | 27518.756 | 30077.055 |
| 4 | 4 | 1,133 | 2,332,000 | 12.033% | 19915.231 | 21778.535 |

Offload ticks sum the reset-to-accelerator-completion and completion-to-host-return segments.
Cache counters come from full-output runs; the host return segment is reported separately in CSV.
Bandwidth is an issue limit, not DRAM bandwidth. Queue capacity remains 32 entries.
Area fields are retained as raw model diagnostics. Fixed CACTI inputs do not model the physical cost
of changing cache ports; do not use this sweep to claim hardware area or energy savings.
