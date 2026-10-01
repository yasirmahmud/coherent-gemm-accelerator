# Paper experiment suite

The final paper uses only the fresh `paper_local_20261001` suite selected by
[`paper/experiment_data.json`](../paper/experiment_data.json). Its 107 simulator
executions completed successfully and passed the suite validator. Traces and
CPU/accelerator programs were generated for these runs; no older measurements
are used by the paper generators.

| Experiment | Coverage | Simulator executions |
| --- | --- | ---: |
| Main size/width sweep | N=8,16,24,32; widths 1,2,4; full accelerator/CPU checks, accelerator/CPU program timing, segmented offload timing | 60 |
| Issue-limit sweep | N=24; widths 1/4; limits 1/2/4; three accelerator stages and two CPU controls | 20 |
| Passive graph observer | N=24; all widths; full and invocation stages, reference/observer pairs | 12 |
| Repeated calls | N=24; all widths; three matched-mutation or unchanged-input calls; checker/timed pairs | 12 |
| Independent-input checks | N=24; all widths; three independently mutated calls | 3 |

The independent-input checks complete normally but fail their output checks
at every width. Their 20/24/19 per-call mismatch counts are retained as
correctness evidence and excluded from performance comparisons. All intended
passing checks pass, including every call in the paired checker runs. Timed
repeated runs receive a final checksum rather than an intermediate check.

[Suite validation](../results/paper_runs/paper_local_20261001/analysis/suite_validation.json)
records the grid and outcomes. The main validator checks every effective
configuration entry within each size/stage, normalizing kernel names and output
paths, and verifies retained traces and guest identities. The graph validator
requires exact simulated-statistics equivalence between observer and reference.
The warm validator checks all call intervals and identical timed program
instruction sections across widths within each input case. The bandwidth
validator permits only its intended issue-limit change.

The main sweep, negative checks, commands, and runner records are in
[`results/paper_runs/paper_local_20261001/`](../results/paper_runs/paper_local_20261001/).
The selected graph, warm, and bandwidth directories are listed in the paper's
data-selection file. Older archives remain available for historical comparison;
they are not sources for the final paper.

To regenerate the paper from the retained evidence:

```bash
python3 scripts/validate_paper_suite.py results/paper_runs/paper_local_20261001
python3 scripts/build_paper_numbers.py
python3 scripts/build_paper_tables.py
python3 scripts/plot_ieee_paper.py  # Matplotlib required
tectonic paper/final_paper.tex --outdir paper
python3 scripts/manifest_artifacts.py
```

The numerical prose is generated in `paper/result_macros.tex`; tables and plots
read the same selected CSVs. Figure 4 contains all four sizes for every width,
including the new N=8/16 width-2 measurements, and connects each width's series.

To execute a new suite, supply a container engine with the pinned toolchain
image and built reference/observer source directories. The existing build
procedure and observer patch are described in
[`MECHANISM_DIAGNOSTICS.md`](MECHANISM_DIAGNOSTICS.md). The runner refuses to
overwrite a previous suite and uses isolated local scratch directories:

```bash
python3 scripts/run_paper_suite.py --engine podman \
  --source .artifacts/source --diagnostic-source .artifacts/diagnostic-source \
  --cohort paper_new_run --workers 6
python3 scripts/validate_paper_suite.py results/paper_runs/paper_new_run
```

The current workspace used `.artifacts/paper-suite/podman-local` as the engine
wrapper for its existing local container store. Execution host identity, source
revisions, simulator fingerprints, and full commands are retained with the
artifacts. The paper discusses the simulated architecture and measurements.
