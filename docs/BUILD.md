# Build and reproduction

## Environment

- Linux x86-64, or Windows with WSL2 and Docker available from WSL.
- Docker, Git, Python 3, Internet access for setup, about 40 GB free disk.
  The uncompressed container image is about 32 GB.
- The container image is `xyzsam/gem5-aladdin` at SHA-256 digest
  `03b405408f17ceab194b08e03c986fcffd3ed10486d3443bd17eda87b33bee92`.
- `scripts/setup_inside.sh` checks out gem5-Aladdin commit
  `d4efbee56d71f9609eab85393eff58f5dbf7763c` and asserts its Aladdin
  submodule commit `448b8f41865003e20eee0bdbd7a73febb5c3abe3`.
- The simulator is compiled as `build/X86/gem5.opt` with
  `PROTOCOL=MESI_Two_Level_aladdin`; the finite queue patch is applied first.

The Docker volume `coherent-gemm-source` holds the upstream checkout/build.
Set `COHERENT_GEMM_VOLUME` to use another volume. `setup.sh` can be rerun.
The repository itself is mounted for benchmark input and result output.

## Commands

From the repository root in a Bash shell:

```bash
bash scripts/setup.sh
bash scripts/run.sh 24 all
bash scripts/run.sh 32 all
python3 scripts/summarize.py
```

Optional figure generation uses open-source Matplotlib:

```bash
python3 -m pip install matplotlib
python3 scripts/plot_results.py
```

For a single stage use `bash scripts/run.sh 24 full`, `roi`, or `invocation`.
The allowed matrix sizes are 24 and 32, since those are the validated study
points. New sizes require revisiting trace-generation time and correctness.

The `full` stage does a complete CPU and accelerator element-by-element check.
The `roi` stage uses a lightweight checksum after GEMM so the expensive
reference check does not dominate timing. The `invocation` stage resets gem5
stats immediately before the accelerator call and dumps after host return.
`run_inside.sh` validates output markers before accepting each stage.
At N=32, `all` can take tens of minutes because the legacy Aladdin scheduler
rebuilds a large datapath graph in each stage. Start with N=24 for a smoke
test.

Each run recreates the trace for the selected kernel and N in the Docker
volume, then compiles the guest programs and writes gem5 output under
`results/{fair_results,roi_results,invocation_results}/{base,tiled4}_nN/`.
Its `build.log` and trace hashes are local byproducts. The versioned raw
`gem5-*.log`, `stats.txt`, and `config.ini` are sufficient to inspect and
recompute the published summary. Running again overwrites the corresponding
raw result directories; commit or copy old outputs first if comparing reruns.

To validate shipped outputs without Docker:

```bash
python3 scripts/summarize.py
```

This checks full output correctness, checksum equality across CPU and
accelerator runs, equal host instruction counts, and labeled invocation
intervals. It then regenerates `results/validated_summary.csv`.

## What is measured

Both kernels use an OoO `DerivO3CPU`, 1 GHz system/Ruby clocks, 1 GB
DDR3_1600_8x8, one CPU, Ruby MESI two-level coherence, a 32 kB accelerator
cache, 64-byte cache lines, queue size 32, and bandwidth 4. Config files and
saved gem5 `config.ini` permit checking these settings. The primary changed
variable is output columns computed per inner loop iteration (one versus
four). The patch is present for both variants.

The Aladdin `Cycle` line is accelerator datapath cycles. `sim_ticks` in the
ROI stats includes process startup and shutdown. The offload interval sums
Aladdin's datapath-completion stats segment and the subsequent host-return
segment, after a pre-invocation reset. This includes command/coherent-memory
traffic and host wake-up but excludes startup and output checks. The same
four-column kernel on OoO CPU is a secondary comparator, not the baseline
for the main improvement claim.

## Troubleshooting

- If Docker reports an unavailable daemon, start Docker Engine in Linux/WSL
  and retry from the same shell.
- If `run.sh` says to run setup first, run `bash scripts/setup.sh` using the
  same `COHERENT_GEMM_VOLUME`.
- For a failed benchmark compilation, inspect the benchmark's
  `trace-build.log` in the Docker volume or the result's `build.log`.
- If `summarize.py` fails, retain the raw output and inspect its named path.
  A failed correctness or matching-stat check must not be treated as a speedup.
- This is a legacy simulator stack pinned for reproducibility. Do not silently
  substitute a current gem5 release or LLVM version.
