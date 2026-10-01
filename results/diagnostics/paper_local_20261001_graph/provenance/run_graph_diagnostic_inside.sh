#!/usr/bin/env bash
# Mount original pinned source at /worksrc and separately built observer at /diagnostic.
set -euo pipefail
target=${GEMM_DIAG_ROOT:-/project/results/diagnostics/graph_n24}
scratch=${GEMM_DIAG_SCRATCH:-/project/.artifacts/graph_n24/integration-test}
mkdir -p "$scratch/common" "$scratch/with-cpu"
cp -a /worksrc/src/aladdin/integration-test/common/. "$scratch/common/"
if [[ ! -d "$target/provenance/common" ]]; then cp -a "$scratch/common" "$target/provenance/common"; fi
sha256sum /worksrc/build/X86/gem5.opt /diagnostic/build/X86/gem5.opt > "$target/provenance/simulators.sha256"
git -C /worksrc rev-parse HEAD > "$target/provenance/gem5-commit.txt"
git -C /worksrc/src/aladdin rev-parse HEAD > "$target/provenance/aladdin-commit.txt"
for variant in ${GEMM_DIAG_VARIANTS:-base tiled2 tiled4}; do
  case "$variant" in
    base) bench=gemm_acp_pilot; cfg=gem5_cache.cfg ;;
    tiled2) bench=gemm_tiled2; cfg=gem5.cfg ;;
    tiled4) bench=gemm_tiled4; cfg=gem5.cfg ;;
  esac
  work="$scratch/with-cpu/$variant"
  inputs="$target/$variant/inputs"
  mkdir -p "$work" "$inputs"
  cp -a "/project/benchmarks/$bench/." "$work/"
  cp -a "/project/benchmarks/$bench/." "$inputs/"
  cd "$work"
  make BMARK_SPECIFIC_CFLAGS='-DN=24' -B run-trace > "$inputs/trace-build.log" 2>&1
  grep -qx 'GEMM passed: 0 mismatches' "$inputs/trace-build.log"
  cp dynamic_trace.gz "$inputs/"
  sha256sum dynamic_trace.gz > "$inputs/trace.sha256"
  gzip -cd dynamic_trace.gz | sha256sum > "$inputs/logical-trace.sha256"
  for stage in full invocation; do
    flags='-DN=24'
    [[ "$stage" == full ]] || flags+=' -DFAST_CHECK -DINVOCATION_STATS'
    make BMARK_SPECIFIC_CFLAGS="$flags" gem5-accel > "$inputs/$stage-build.log" 2>&1
    cp "$bench-gem5-accel" "$inputs/$stage-guest"
    sha256sum "$inputs/$stage-guest" > "$inputs/$stage-binary.sha256"
    for mode in reference instrumented; do
      sim=/worksrc/build/X86/gem5.opt
      [[ "$mode" == reference ]] || sim=/diagnostic/build/X86/gem5.opt
      output="$target/$variant/$stage/$mode"
      mkdir -p "$output/m5out" outputs outputs-cache
      args=("$sim" "--outdir=$output/m5out" /worksrc/configs/aladdin/aladdin_se.py)
      [[ "$stage" == full ]] || args+=(--enable-stats-dump-and-resume)
      args+=(--ruby --num-cpus=1 --num-l2caches=1 --num-dirs=1 --cpu-type=DerivO3CPU
        --mem-size=1GB --mem-type=DDR3_1600_8x8 --sys-clock=1GHz --ruby-clock=1GHz
        --cacheline_size=64 "--accel_cfg_file=$work/$cfg" -c "$work/$bench-gem5-accel")
      printf '%q ' "${args[@]}" > "$output/command.txt"
      printf '\n' >> "$output/command.txt"
      echo "$(date -u +%FT%TZ) $variant $stage $mode"
      timeout 900 "${args[@]}" > "$output/gem5.log" 2>&1
      if [[ "$stage" == full ]]; then grep -qx 'GEMM passed: 0 mismatches' "$output/gem5.log"; fi
      mkdir -p "$output/model"
      cp -a outputs outputs-cache "$output/model/"
    done
  done
done
if [[ ${GEMM_DIAG_PARTIAL:-0} != 1 ]]; then date -u +%FT%TZ > "$target/provenance/completed-at.txt"; fi
