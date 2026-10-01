#!/usr/bin/env bash
# Bounded N=24 three-call diagnostic, correctness and timed harnesses.
set -euo pipefail
target=${GEMM_DIAG_ROOT:-/project/results/diagnostics/warm_n24}
scratch=${GEMM_DIAG_SCRATCH:-/project/.artifacts/warm_n24/integration-test}
mkdir -p "$scratch/common" "$scratch/with-cpu" "$target/provenance"
cp -a /worksrc/src/aladdin/integration-test/common/. "$scratch/common/"
cp -a "$scratch/common" "$target/provenance/"
sha256sum /worksrc/build/X86/gem5.opt > "$target/provenance/simulator.sha256"
for case_name in matched unchanged; do
  mutation_flags=''
  [[ "$case_name" == matched ]] || mutation_flags='-DUNCHANGED_INPUT=1'
  for variant in base tiled2 tiled4; do
    case "$variant" in
      base) bench=gemm_acp_pilot; cfg=gem5_cache.cfg ;;
      tiled2) bench=gemm_tiled2; cfg=gem5.cfg ;;
      tiled4) bench=gemm_tiled4; cfg=gem5.cfg ;;
    esac
    work="$scratch/with-cpu/${case_name}_$variant"
    point="$target/${case_name}_$variant"
    mkdir -p "$work" "$point/inputs"
    cp -a "/project/benchmarks/$bench/." "$work/"
    cp -a "/project/benchmarks/$bench/." "$point/inputs/"
    cd "$work"
    make BMARK_SPECIFIC_CFLAGS="-DN=24 -DREPS=3 $mutation_flags" -B run-trace > "$point/inputs/trace-build.log" 2>&1
    grep -qx 'GEMM passed: 0 mismatches' "$point/inputs/trace-build.log"
    cp dynamic_trace.gz "$point/inputs/"
    sha256sum dynamic_trace.gz > "$point/inputs/trace.sha256"
    gzip -cd dynamic_trace.gz | sha256sum > "$point/inputs/logical-trace.sha256"
    for mode in correctness timed; do
      flags="-DN=24 -DREPS=3 -DINVOCATION_STATS $mutation_flags"
      if [[ "$mode" == correctness ]]; then flags+=' -DPER_CALL_CHECK'; else flags+=' -DFAST_CHECK'; fi
      output="$point/$mode"
      mkdir -p "$output/m5out-accel" outputs outputs-cache
      make BMARK_SPECIFIC_CFLAGS="$flags" gem5-accel > "$output/build-record.log" 2>&1
      cp "$bench-gem5-accel" "$output/guest"
      sha256sum "$output/guest" > "$output/binary.sha256"
      cp "$point/inputs/trace.sha256" "$output/"
      printf '{"expected_calls":3,"mode":"%s","input_case":"%s","variant":"%s"}\n' "$mode" "$case_name" "$variant" > "$output/run.json"
      args=(/worksrc/build/X86/gem5.opt "--outdir=$output/m5out-accel"
        /worksrc/configs/aladdin/aladdin_se.py --enable-stats-dump-and-resume
        --ruby --num-cpus=1 --num-l2caches=1 --num-dirs=1 --cpu-type=DerivO3CPU
        --mem-size=1GB --mem-type=DDR3_1600_8x8 --sys-clock=1GHz --ruby-clock=1GHz
        --cacheline_size=64 "--accel_cfg_file=$work/$cfg" -c "$work/$bench-gem5-accel")
      printf '%q ' "${args[@]}" > "$output/command.txt"; printf '\n' >> "$output/command.txt"
      echo "$(date -u +%FT%TZ) $case_name $variant $mode"
      timeout 1200 "${args[@]}" > "$output/gem5-accel.log" 2>&1
      if [[ "$mode" == correctness ]]; then
        grep -qx 'GEMM per-call total: 0 mismatches across 3 calls' "$output/gem5-accel.log"
        grep -qx 'GEMM passed: 0 mismatches' "$output/gem5-accel.log"
      fi
      mkdir -p "$output/model"
      cp -a outputs outputs-cache "$output/model/"
    done
  done
done
date -u +%FT%TZ > "$target/provenance/completed-at.txt"
