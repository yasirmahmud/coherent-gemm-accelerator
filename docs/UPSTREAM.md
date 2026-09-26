# Upstream and licensing

- Simulator: [Harvard gem5-Aladdin](https://github.com/harvard-acc/gem5-aladdin),
  commit `d4efbee56d71f9609eab85393eff58f5dbf7763c`.
- Accelerator submodule: [Harvard Aladdin](https://github.com/harvard-acc/ALADDIN),
  commit `448b8f41865003e20eee0bdbd7a73febb5c3abe3`.
- Container: `xyzsam/gem5-aladdin` at the digest recorded in
  [BUILD.md](BUILD.md), supplying the legacy open-source LLVM/SCons stack.
- The simulator sources are fetched by `scripts/setup.sh`; they are not
  vendored. The pinned gem5-Aladdin tree contains BSD-style `LICENSE` and
  `COPYING` terms. The pinned Aladdin `LICENSE.txt` identifies Apache 2.0
  terms with BSD-covered code in its `gem5/` directory. Read those upstream
  files for terms governing the imported source and modifications. Our
  independently packaged scripts, benchmarks, and documentation use the
  root MIT license.

The patch under `patches/` is an explicit source modification against the
pinned Aladdin commit. It enforces a finite memory queue and retries one
fine-grained ACP path. It is applied to both comparison variants. It does not
establish dynamic input coherence and does not repair the separate ACP
host-burst path. This experiment uses the accelerator's coherent private
cache path for its reported comparison.
