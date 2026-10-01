# Suggestions from the verification and re-run (rasin_claude_suggestion.md)

Date: 2026-10-01. Written after pulling `main` at `0191380`, checking the current
`proposal/proposal.tex` against the project, and re-running the simulator.

This file records what was tested, what was found, and which changes I suggest and
why. Nothing in the proposal, paper, README or results was edited; this file is the
only change.

## 1. Short version

1. The commitments in the current `proposal.tex` are implemented and backed by
   retained evidence. Cycle counts, correctness checks, area, the bandwidth sweep,
   and the repeated-call and mutation diagnostics all reproduced when re-run.
2. One thing did not reproduce: the **N=32 baseline offload time**. The paper uses
   4,306,000 ticks. A re-run gives 4,132,000.
3. I traced this to a simulation artifact. **The same binary gives different
   host-side timing depending on the directory path it is run from.** Datapath
   cycles are not affected. Offload time and offload-reduction percentages are.
4. This changes how the proposal should describe its primary metric and its
   controls. I suggest the proposal state the sensitivity and the control as work
   we intend to do, and that the paper report ranges, not single percentages.

## 2. What was checked first (no simulator)

- `git pull` brought `main` from `7b4bd88` to `0191380` (4 commits). The pull
  replaced `proposal.tex` with a rewritten version that adds the issue-limit
  (requests per cycle) study, the timing breakdown, and a third group member.
- Re-ran the project validators: the bandwidth validator and the fresh paper-suite
  validator pass. All 22 unit tests pass. `SHA256SUMS` for the paper and analysis
  artifacts verify.
- Checked the proposal's configuration claims against the effective gem5 configs
  in the raw evidence: CPU 2 GHz, 8-wide, 192-entry ROB, 32-entry load/store
  queues; L1D 64 kB, L1I 32 kB, L2 2 MB; accelerator cache 32 kB, 4-way, 64 B
  lines, 32-entry queue; DDR3-1600, 1 GB; system, Ruby and accelerator clocks at
  1 GHz.
- Regenerated the paper numbers and tables from the retained data. The numbers
  were identical. The regenerated figures differ only at the byte level.

## 3. Getting the simulator to run

Podman works on this account, as in the earlier session, but the image is stored
per host in `/var/tmp`, so it had to be pulled again on ece-lnx-03. The existing
config (`storage.conf`, `containers.conf` with `keyring = false`, `~/bin/docker`)
was still in place, and the built simulator in
`~/persistent-gem5-aladdin-build` was intact with the finite-queue patch applied.

All runs used a scratch copy of the project at `/var/tmp/r.ihtemam-verify/`, so the
committed `results/` were never overwritten.

## 4. What was re-run and what matched

| Re-run | Result |
|---|---|
| N=24 and N=32, baseline and width 4, full / ROI / invocation stages | Cycles 1452 / 1133 and 2827 / 1984. All full checks: 0 mismatches. ROI and invocation checksums match. |
| Width 2 and N=8, 16 for all widths | Cycles 276 / 260 / 250, 765 / 636 / 575, 1257, 2268 match the committed data. All checks pass. |
| Area at N=24 and N=32 | Matches. |
| Bandwidth sweep (N=24, widths 1 and 4, limits 1, 2, 4) | Identical to the published cohort: offload reductions 4.669%, 7.268%, 12.033%. Validator passes. |
| Repeated calls, matched mutation (N=24, 3 calls, baseline and width 4) | 0 mismatches on all calls. |
| Repeated calls, independent mutation | Rejected with 20 / 24 / 19 mismatches, as the proposal expects (a fixed-trace limit). |
| Offload ticks, 12 points vs the paper's fresh suite | 11 of 12 match exactly. The exception is the N=32 baseline. |

I did not re-run the paper's full 107-run suite. It needs the observer-patched
build, a reference build and the `.artifacts` runner from another machine.

## 5. The mismatch and how it was traced

Offload time is the completion segment plus the return segment. For the N=32
baseline:

| | Completion | Return | Offload | Datapath cycles |
|---|---|---|---|---|
| Paper's fresh suite | 3,610,000 | 696,000 | 4,306,000 | 2,827 |
| Re-run | 3,610,000 | 522,000 | 4,132,000 | 2,827 |

Steps taken:

1. **Repeated the run 10 times** (5 baseline and 5 width-4 runs, same path). Every
   run was identical. The simulator is deterministic, so this is not noise.
2. **Compared guest binaries.** My binary and the suite's have identical SHA-256
   hashes. So the compiled code is the same.
3. **Compared the return-segment stats.** The host CPU executed slightly different
   instruction streams (24,214 vs 24,179 simulated instructions, different load and
   instruction-fetch counts, 671 vs 497 CPU cycles). The difference is host-side.
4. **Compared the commands.** The suite ran the binary from
   `/project/.artifacts/paper_local_20261001_main_32_base/integration-test/...`.
   Mine ran from `/worksrc/src/aladdin/integration-test/...`.
5. **Replayed my binary from the suite's exact path.** Result: 696,000 return and
   4,306,000 offload, exactly the paper's value. From two other paths the offload
   total was 4,132,000.
6. **Swept path length.** 72 runs: base, width 2, width 4 at N=24 and N=32, with
   the directory path padded by 0, 1, 2, 3, 4, 5, 6, 7, 8, 12, 16 and 24 extra
   characters.

I believe the mechanism is that the program path is placed on the simulated stack
in syscall-emulation mode, which shifts memory layout and host-side timing. I did
not trace this inside gem5, so treat the mechanism as the likely explanation, not
a verified one. The path dependence itself is measured.

## 6. Sweep results

Datapath cycles were identical at every path length (1452 / 1257 / 1133 at N=24,
2827 / 2268 / 1984 at N=32).

Offload ticks for the baseline, by padding length (0, 1, 2, 3, 4, 5, 6, 7, 8, 12,
16, 24):

- N=24: 2,678,000 for padding 0 to 5; 2,703,000 for 6 to 12 and 16; 2,680,000 for 24.
- N=32: 4,312,000 for padding 0 to 5; 4,306,000 for 6 to 12; 4,132,000 for 16 and 24.

Offload reduction versus the baseline:

| | N=24 | N=32 |
|---|---|---|
| Width 2 | 6.35% to 7.28% | 15.10% to 19.25% |
| Width 4 | 10.98% to 11.91% | 21.97% to 25.83% |

Every previously seen number is one point on this range: the README's 11.90% and
22.56%, the paper's 11.80% and 25.13%, and my first re-run's 11.80% and 21.97%.
The ordering (width 4 beats width 2 beats width 1) held at every path length.
At N=32 the width-4 reduction moves by about 3.9 percentage points from layout
alone.

## 7. Suggested changes and why

The proposal describes planned work, so each item is worded as something we intend
to do.

### 7.1 Proposal (`proposal/proposal.tex`)

- **Keep offload latency as the primary metric, and add datapath cycles as the
  layout-independent result.** Why: cycles were identical in all 72 sweep runs and
  in every re-run, while offload time moved by up to about 4%.
- **Add a control sentence to Methodology.** Suggested wording: "We will run every
  measurement from one pinned program path and environment, and will record that
  path with each result." Why: the path changes the result, so a comparison is only
  fair if it is held fixed.
- **Add a sensitivity sentence.** Suggested wording: "We will repeat each size and
  width at several program placements and report offload reductions as ranges."
  Why: a single percentage hides a spread that can be larger than some of the
  differences we want to discuss.
- **Scope the claim in Metrics and Analysis.** Suggested wording: "We will claim
  the ordering of widths and the cycle reductions; offload percentages will be
  reported with their sensitivity to host-side program placement." Why: this
  matches what the evidence supports.
- **Keep the completion and return segments separate.** The proposal already does
  this. Why it matters: the sweep shows the layout effect lands in these two
  segments, so the breakdown is what makes it visible. It also supports the
  existing sentence about testing whether the non-datapath intervals are stable:
  at N=32 they are not.

### 7.2 Paper (`paper/`)

- The N=32 tables use a 4,306,000-tick baseline from one path. Suggest regenerating
  the N=32 rows from one documented, pinned path, and adding a range table like
  section 6. Why: the paper's 25.1% at N=32 is the top of a 22.0% to 25.8% range.
- Add a limitation paragraph about program-placement sensitivity.

### 7.3 README and docs

- The README headline (11.90% and 22.56%) comes from another point on the same
  range. Suggest stating the range or the pinned path next to it. Why: three
  documents currently show three different values for the same experiment, and a
  reader could take it as an error.

## 8. Limits of this work

- The mechanism (stack layout from the program path) is likely, not verified.
- The sweep varied path length only. I did not vary environment variables or
  other placement inputs.
- The bandwidth sweep and the repeated-call runs used one path each. I did not
  test whether placement changes them.
- The re-runs used the plain reference build on one host, not the paper's
  observer-patched build.

## 9. Where the evidence is

Scratch data, not committed: `/var/tmp/r.ihtemam-verify/` (`reps/` for the 10
repeats, `project/pt/` for the three-path test, `project/sw/` for the 72-run sweep,
`project/results/` for the main re-runs). `/var/tmp` is host-local and may be
cleaned, so copy anything worth keeping.

Reproduce the three-path test and the sweep with the scripts `pathtest.sh` and
`sweep.sh` in that scratch project. Each takes a variant, a size and a padding
length, copies the packaged benchmark to
`/project/.artifacts/sw<padding>/<variant>_<N>/`, and runs gem5 with
`--enable-stats-dump-and-resume` from that path.
