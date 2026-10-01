# Mechanism diagnostics and analysis

Executed 2026-09-30 for the immediate-next-steps checklist. The core width
and bandwidth experiments were reused. New simulations are bounded
mechanism/repeated-call diagnostics, not replacements for historical cohorts.

## Evidence and findings

- [Graph-to-interface analysis](../results/diagnostics/graph_n24/ANALYSIS.md):
  all widths retain source-level A-load reduction in the connected optimized
  graph, but accept/return 36 A loads, 36 B loads and 576 C stores each.
  Reference/observer full correctness, every simulated statistics block, and
  effective configurations match. Full effective configurations are also
  compared across widths within each stage.
- [Cache-counter analysis](../results/analysis/cache/ANALYSIS.md): definitions
  are checked against retained pinned implementation files. Demand misses
  include store upgrades; no compulsory/capacity/conflict/coherence partition
  is reported. This completes task 2's aggregate-analysis alternative. A
  line/event observer and shadow classifier were skipped under that alternative.
- [Historical provenance](../results/provenance/historical_20260930/README.md):
  each main point is inventoried. Three N=32 traces were recovered by matching
  retained historical hashes. Missing source/binary/CACTI identities and the
  malformed historical simulator hash remain explicit.
- [Repeated-call analysis](../results/diagnostics/warm_n24/ANALYSIS.md):
  matched and unchanged inputs, widths 1/2/4, three calls, separate checked and
  timed harnesses, all per-call counters and modeled resource peaks.
- [Width summary](../results/analysis/WIDTH_SUMMARY.md): N=24 published and
  N=32 recovered cohorts remain separate. Vector figures show latency,
  same-kernel CPU speedup and FU/memory area; no universally best width is claimed.
- [Final paper](../paper/final_paper.pdf) and its [source](../paper/final_paper.tex).
  The existing [bandwidth figures and timing decomposition](CACHE_BANDWIDTH.md)
  are carried forward. Optional extensions were not added to this bounded study.

## Observer definitions

The passive [patch](../patches/passive_graph_counters.patch) applies after
`bounded_queue_gemm_pilot.patch` to pinned Aladdin. Graph counters read node
and edge state before/after optimization. Array attribution follows recorded
address ranges and a read-only address-parent traversal; it does not run an
extra optimization pass. All graph objects and connected operations are
separate counts. The GEMM value slice is rooted at C-store value operands,
stops at memory/address nodes, and excludes control/memory dependencies.
Arithmetic outside that slice includes index/address work, not MACs.

Cache counters distinguish initially accepted data requests, successfully
accepted retries, returned data requests, rejected initial sends, first node
joins to existing queue entries, queue allocations, and blocked node polls.
The finish/control packet is excluded. Successful retry sends are counted;
retry notifications which remain blocked are not counted. Distinct blocked
accelerator ticks are counted separately from attempts. No counter is read
by a scheduling decision. Observer hash/source patch and reference executable
identity are retained; the original simulator was preserved in its own build.

## Reproduction

Use the pinned container and a prepared original source/build as described
in [BUILD.md](BUILD.md). Build the observer in a **separate copy** of that
source/build; never apply its patch to the reference simulator checkout:

```bash
cp -a --reflink=auto /path/to/reference-source /path/to/diagnostic-source
git -C /path/to/diagnostic-source/src/aladdin apply "$PWD/patches/passive_graph_counters.patch"
# In the pinned toolchain container, mount the diagnostic copy at /worksrc:
# cd /worksrc && scons build/X86/gem5.opt -j16 PROTOCOL=MESI_Two_Level_aladdin
export COHERENT_GEMM_SOURCE=/path/to/reference-source
export COHERENT_GEMM_DIAGNOSTIC_SOURCE=/path/to/diagnostic-source
bash scripts/run_mechanism_diagnostic.sh graph graph_n24_fresh
bash scripts/run_mechanism_diagnostic.sh warm warm_n24_fresh
```

`COHERENT_GEMM_CONTAINER_ENGINE` can select Docker or a configured rootless
Podman wrapper. The runner refuses existing output directories and supplies
isolated benchmark work directories. Graph diagnostics reuse the retained
bandwidth traces for widths 1/4 and generate one width-2 trace. Each kernel's
trace is reused across reference/observer stages. Warm diagnostics build one
three-call trace per input-case/width and share it between checker/timed runs.
The `UNCHANGED_INPUT=1` macro disables inter-call mutations in both trace and
runtime harnesses; its default is zero and preserves existing behavior.

Regenerate checks and analysis without a simulator:

```bash
python3 -m unittest discover -s tests
python3 scripts/summarize_graph_diagnostic.py
python3 scripts/summarize_warm_diagnostic.py
python3 scripts/analyze_cache_counters.py
python3 scripts/summarize_widths.py
python3 scripts/summarize_repeated.py results/diagnostics/repeated_n24_reps3_base --expected-calls 3
# This must exit 1; it remains a failed correctness experiment:
python3 scripts/summarize_repeated.py results/diagnostics/repeated_n24_reps3_base_independent --expected-calls 3
python3 scripts/plot_width_analysis.py  # requires Matplotlib
python3 scripts/build_paper_tables.py
# Compile paper/final_paper.tex with a TeX distribution (e.g. Tectonic).
```

New `run_repeated.sh` outputs declare their expected count in `run.json` and
invoke the strict validator. Historical fixtures require `--expected-calls`
so truncated evidence cannot set its own expected count. Hash metadata alone
is labeled unverified unless trace bytes exist; diagnostic cohort validators
also verify compressed and logical trace bytes and guest identities.

The timed three-call harnesses have identical `.text` sections across widths
within each input case. The full checker runs CPU GEMM and reads A/B/C between
calls, affecting cache/coherence state. It is explicitly a different history
from the timed harness. Passing paired checks and a timed final checksum do
not independently prove every timed intermediate output. Per-call resource
peaks are diagnostic pre-RTL estimates, not steady-state physical area.

The warm runner's final timestamp command failed after all twelve simulations
and model copies completed because its file was edited during Bash execution.
The original error remains in `runner.log`; `provenance/finalization.json`
records exit 127 and the recovery. Independent full validation with
`--finalize` created `validated-at.txt`. No simulations were restarted.
Future wrapper runs execute the retained runner snapshot to avoid that issue.
