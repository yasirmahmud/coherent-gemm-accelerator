# Immediate checklist completion audit

Audited against the current worktree on 2026-09-30. The original steps and
allowed alternatives remain in `IMMEDIATE_NEXT_STEPS.md`; this audit does not
substitute a smaller objective. The table covers each explicit checkbox,
deliverable and completion rule.

| Step | Requirements checked | Authoritative evidence and disposition |
| --- | --- | --- |
| 0 | Scope graph claims, aggregate miss attribution, historical provenance; two-page planned-work PDF with no measured disclosures | Revised proposal source/PDF; PDF page count 2; extracted-text review. Technical promises are supported or explicitly scoped as remaining causal analysis. `results/analysis/proposal_validation.json` identifies the reviewed artifacts. |
| 1 | Inspect old logs; pre/post all/connected operation counts; A/B/C loads/stores; GEMM versus address arithmetic; accepted/returned/retry/join counters; blocked attempts versus cycles; N=24 widths 1/2/4 at limit 4; preserve simulator; compare correctness/timing; retain provenance; explain observed requests | `results/diagnostics/graph_n24/`: all six reference/observer stage pairs pass full checks or matching checksums, identical simulated statistics and effective configurations; cross-width configs match. Per-array accepted/returned counts reconcile with raw stats. Source/trace/guest identities, patch, simulator build/identity, CACTI inputs, commands, raw/model outputs, CSV, analysis and manifest retained. Successful retries are defined explicitly; unsuccessful retry notifications are outside that count. |
| 2 | Check pinned Ruby definitions and aggregate/coherence attribution limits; controlled N=24 analysis; totals reconciliation; classified evidence or permitted aggregate alternative | `results/analysis/cache/`: pinned implementation snapshots, inventory, six-point aggregate CSV and documented identities. Returned counts match histogram samples and Ruby demand totals equal hits plus misses. No observer changes were applied to this retained cohort. Separate miss categories were removed from the proposal commitment. Line/event tracking, first-touch/shadow replay and observer comparisons are explicitly skipped under the permitted aggregate alternative. |
| 3 | Six main-point artifact inventory; ignored/local recovery first; consistent named cohorts; truthful historical limits or matched fresh rerun; strict checks on new cohorts | `results/provenance/historical_20260930/`: N=24 published and N=32 recovered point inventories; three N=32 traces match historical compressed hashes and have recomputed logical hashes. Candidate identities and missing historical source/guest/CACTI identities remain labeled. Historical simulator hash is invalid (62 digits); the current binary fingerprint is separate. Historical-comparison alternative selected; no core reruns needed. New diagnostics verify trace/binary identities, configuration controls, correctness and manifests. |
| 4 | Expected call count, ordered/consecutive indices, all checks, paired intervals and valid hashes; rejection fixtures; preserve independent failure; bounded matched/unchanged width diagnostics; separate checker/timing boundaries; per-call counters/peaks | 14 rejection/passing repeated-validator tests and 8 existing bandwidth tests pass. Historical independent fixture exits validation 1 with 20/24/19 mismatches. `results/diagnostics/warm_n24/` retains all 36 call records in twelve runs; eighteen full checked calls pass. Shared traces and guest hashes verify; full effective configs match; timed instruction sections match across widths. Cache/queue counts/means/samples, cycles, completion/return ticks and resource peaks are reported. Checker effects and runner finalization recovery are explicit. No timed intermediate output is claimed independently checked. |
| 5 | Automated both-size all-width summaries; width latency, CPU speedup, latency/area figures with provenance/units; FU/memory split; dominated/remaining choices; retain bandwidth/decomposition; write final paper after scope resolution | `results/analysis/`: raw-evidence derived width CSV/validation and SVG/PDF/PNG figures. N=24 uses published data and N=32 recovered data; no mixed baselines. N=24 width 4 dominates; N=32 widths 1/4 remain choices. Existing bandwidth figures/decomposition and fixed-CACTI limits are retained. `paper/final_paper.tex`, generated tables and six-page PDF present all measurements and limits. |

No optional extension was selected. Optional studies are not reported as
executed. Separate miss classification and unrecoverable historical identities
are not represented as completed experiments; the checklist's explicit
alternatives resolve their reporting requirements.

Verification commands: both diagnostic summarizers, aggregate-cache and width
summarizers, the strict bandwidth validator, legacy main/exploratory summary
regeneration, Python compilation, shell syntax checks, `git diff --check`,
22 unit tests, PDF builds/page counts, and SHA-256 verification of every
retained new artifact group plus both original cohort manifests. Test output
is retained in `results/analysis/tests.log`. Build and finalization records
remain with their respective artifacts. No external publication or course
submission was performed or implied by this repository checklist.
