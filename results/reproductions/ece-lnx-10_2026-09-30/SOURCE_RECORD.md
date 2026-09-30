# Reproduction on ece-lnx-10 (2026-09-30)

This Git-ignored `.artifacts` directory holds the validation results, logs, and local runner copies. Its `source`, `storage`, and `run` entries link to `/var/tmp/cg-753049473` on the device's local XFS disk for faster compilation and container extraction. The source/build and container image links depend on local storage that may be removed by system cleanup; the copied validation results and logs remain in the project directory.

## Environment and build

- No sudo was used. Rootless Podman 4.9.4-rhel ran the pinned `docker.io/xyzsam/gem5-aladdin@sha256:03b405408f17ceab194b08e03c986fcffd3ed10486d3443bd17eda87b33bee92` image.
- Source: gem5-Aladdin `d4efbee56d71f9609eab85393eff58f5dbf7763c`; Aladdin submodule `448b8f41865003e20eee0bdbd7a73febb5c3abe3`; repository finite-queue patch applied.
- Build: `scons build/X86/gem5.opt -j128 PROTOCOL=MESI_Two_Level_aladdin` using `.artifacts/setup_inside_fast.sh` in the pinned container. `setup.log` ends with `scons: done building targets.`
- Executable: `source/build/X86/gem5.opt`; SHA-256 `e02200e483483a363527a947301c4cf71a7c6800af5cc2c756ad654f237bc3`.
- The image, source, build, runner copies, run logs, and outputs are accessible under `.artifacts`.

## Runs

Four independent containers ran `.artifacts/run_inside_local.sh N all`, one for each `(N, variant)` pair: `(24, base)`, `(24, tiled4)`, `(32, base)`, `(32, tiled4)`. Each runner executed full-output, ROI, and invocation stages. Runner logs: `run_n24_base.log`, `run_n24_tiled4.log`, `run_n32_base.log`, `run_n32_tiled4.log`. Raw results are in `results/{fair,roi,invocation}_results/`.

`python3 .artifacts/summarize.py` passed all full-output, checksum, accelerator-host instruction-count, and labeled invocation checks. Its output is `results/validated_summary.csv` in this artifact folder.

| N | Base cycles | Four-column cycles | Cycle reduction | Base offload ticks | Four-column offload ticks | Offload reduction | Whole-program reduction |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 24 | 1,452 | 1,133 | 21.97% | 2,703,000 | 2,384,000 | 11.802% | 0.474% |
| 32 | 2,827 | 1,984 | 29.82% | 4,132,000 | 3,224,000 | 21.975% | 1.178% |

Both sizes have zero full-output mismatches for both kernels. The within-size ROI checksums match, and the accelerator-host instruction counts match between variants (21,600 at N=24; 30,046 at N=32). Published cycle and whole-program reduction percentages match exactly. Published offload reductions are 11.903% and 22.556%; the absolute offload ticks differ modestly in this rebuild, consistent with the cross-host timing sensitivity documented in `docs/VALIDATION.md`. Do not treat the new offload numbers as a bit-for-bit reproduction of the committed reference.
