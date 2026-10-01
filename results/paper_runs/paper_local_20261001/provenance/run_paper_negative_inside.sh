#!/usr/bin/env bash
# Retain a fresh independent-input failure as correctness evidence only.
set -euo pipefail
variant=${1:?Variant required}
target=${GEMM_NEGATIVE_ROOT:?Output root required}/$variant
scratch=${GEMM_PAPER_SCRATCH:?Scratch root required}
case "$variant" in
  base) bench=gemm_acp_pilot; cfg=gem5_cache.cfg ;;
  tiled2|tiled4) bench=gemm_$variant; cfg=gem5.cfg ;;
  *) exit 2 ;;
esac
mkdir -p "$scratch/common" "$scratch/with-cpu/$variant" "$target/m5out-accel"
cp -a /worksrc/src/aladdin/integration-test/common/. "$scratch/common/"
work="$scratch/with-cpu/$variant"
cp -a "/project/benchmarks/$bench/." "$work/"
cp -a "/project/benchmarks/$bench/." "$target/"
cd "$work"
make BMARK_SPECIFIC_CFLAGS='-DN=24 -DREPS=3' -B run-trace > "$target/trace-build.log" 2>&1
grep -qx 'GEMM passed: 0 mismatches' "$target/trace-build.log"
cp dynamic_trace.gz "$target/"
sha256sum dynamic_trace.gz > "$target/trace.sha256"
gzip -cd dynamic_trace.gz | sha256sum > "$target/logical-trace.sha256"
make BMARK_SPECIFIC_CFLAGS='-DN=24 -DREPS=3 -DFAST_CHECK -DINVOCATION_STATS -DPER_CALL_CHECK -DINDEPENDENT_MUTATION' gem5-accel > "$target/build-record.log" 2>&1
cp "$bench-gem5-accel" "$target/guest"
sha256sum "$target/guest" > "$target/binary.sha256"
printf '{"expected_calls":3,"variant":"%s","input_case":"independent"}\n' "$variant" > "$target/run.json"
args=(/worksrc/build/X86/gem5.opt "--outdir=$target/m5out-accel" /worksrc/configs/aladdin/aladdin_se.py
  --enable-stats-dump-and-resume --ruby --num-cpus=1 --num-l2caches=1 --num-dirs=1
  --cpu-type=DerivO3CPU --mem-size=1GB --mem-type=DDR3_1600_8x8 --sys-clock=1GHz
  --ruby-clock=1GHz --cacheline_size=64 "--accel_cfg_file=$work/$cfg" -c "$work/$bench-gem5-accel")
printf '%q ' "${args[@]}" > "$target/command.txt"; printf '\n' >> "$target/command.txt"
set +e
timeout 1200 "${args[@]}" > "$target/gem5-accel.log" 2>&1
status=$?
set -e
printf '%s\n' "$status" > "$target/simulator-exit-code.txt"
[[ "$status" == 0 || "$status" == 1 ]]
grep -q '^Exiting @ tick .* because exiting with last active thread context$' "$target/gem5-accel.log"
[[ $(grep -Ec '^GEMM call [0-2] (passed|FAILED):' "$target/gem5-accel.log") == 3 ]]
echo "Completed independent-mutation check: $variant"
