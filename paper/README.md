# Final paper

[`final_paper.pdf`](final_paper.pdf) is the completed IEEE conference paper;
[`final_paper.tex`](final_paper.tex) is its editable source. It uses
[`IEEEtran`](https://ctan.org/pkg/ieeetran) conference mode on US Letter paper,
with two columns, Times body text, IEEE author blocks, an abstract and index
terms, table captions above the tables, figure captions below the figures,
and numbered citations and references. No venue-specific page limit or
submission metadata has been supplied.

The paper uses only the validated fresh experiment suite selected by
[`experiment_data.json`](experiment_data.json). All 107 simulator executions
were run for this suite. See [experiment coverage and reproduction instructions](../docs/PAPER_EXPERIMENTS.md).

Regenerate the numerical claims, tables, and figures, then compile from the
repository root:

```bash
python3 scripts/validate_paper_suite.py results/paper_runs/paper_local_20261001
python3 scripts/build_paper_numbers.py
python3 scripts/build_paper_tables.py
python3 scripts/plot_ieee_paper.py  # requires Matplotlib
tectonic paper/final_paper.tex --outdir paper
python3 scripts/manifest_artifacts.py
```

For the local tools retained in this workspace, use
`.artifacts/plot-venv/bin/python` for plotting and
`XDG_CACHE_HOME="$PWD/.artifacts/tectonic/cache" .artifacts/tectonic/tectonic`
in place of `tectonic`. A LaTeX distribution with `IEEEtran`, `fontenc`,
`cite`, `amsmath`, `amssymb`, `booktabs`, `graphicx`, and `hyperref`
can also compile the source.

Tables and plots read the selected size/width, graph, repeated-call, and
issue-limit summaries. Figure 4 includes every width at N=8,16,24,32.
Paper-sized vector figures and PNG previews are in `figures/`. The architecture diagram
shows the host, trace-driven datapath, request queue, private coherent cache,
and shared memory system, based on the retained simulator configuration.
The same plotting script generates this vector schematic. Plot series use
distinct colors, line styles, and markers; area components also use hatching.
Axes leave room around plotted points and legends. The original result
figures remain in their cohorts. `generation-scripts/` retains copies of
the numerical, table, and figure generators and their data selector; run the working versions under `scripts/`.
The proposal remains a separate two-page planned-work document.

The final paper reports actual results, negative outcomes, model
limits, aggregate miss-attribution limits, and checker/cache-history effects.
Full software revisions, host identifiers, and validation bookkeeping remain
in the artifact documentation. It does
not claim physical cache-port area/energy costs or general runtime-input
correctness. `SHA256SUMS` fingerprints all paper files except itself.
