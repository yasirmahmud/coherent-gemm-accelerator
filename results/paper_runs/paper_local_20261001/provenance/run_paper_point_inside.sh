#!/usr/bin/env bash
# Fresh trace, CPU controls, and all measurement stages for one size/width point.
set -euo pipefail
n=${1:?Matrix size required}
variant=${2:?Variant required}
target=${GEMM_PAPER_ROOT:?Output root required}
scratch=${GEMM_PAPER_SCRATCH:?Scratch root required}
case "$variant" in
  base) bench=gemm_acp_pilot; cfg=gem5_cache.cfg; tag=cache ;;
  tiled2|tiled4) bench=gemm_$variant; cfg=gem5.cfg; tag=accel ;;
  *) exit 2 ;;
esac
sim=/worksrc/build/X86/gem5.opt
git -C /worksrc/src/aladdin apply --reverse --check /project/patches/bounded_queue_gemm_pilot.patch
mkdir -p "$scratch/common" "$scratch/with-cpu/$variant"
cp -a /worksrc/src/aladdin/integration-test/common/. "$scratch/common/"
work="$scratch/with-cpu/$variant"
inputs="$target/inputs/${variant}_n${n}"
mkdir -p "$inputs"
cp -a "/project/benchmarks/$bench/." "$work/"
cp -a "/project/benchmarks/$bench/." "$inputs/"
cp -a "$scratch/common" "$inputs/"
cd "$work"
make BMARK_SPECIFIC_CFLAGS="-DN=$n" -B run-trace > "$inputs/trace-build.log" 2>&1
grep -qx 'GEMM passed: 0 mismatches' "$inputs/trace-build.log"
cp dynamic_trace.gz "$inputs/"
sha256sum dynamic_trace.gz > "$inputs/trace.sha256"
gzip -cd dynamic_trace.gz | sha256sum > "$inputs/logical-trace.sha256"
common=(--ruby --num-cpus=1 --num-l2caches=1 --num-dirs=1 --cpu-type=DerivO3CPU
  --mem-size=1GB --mem-type=DDR3_1600_8x8 --sys-clock=1GHz --ruby-clock=1GHz --cacheline_size=64)
for stage in full roi invocation; do
  case "$stage" in
    full) folder=fair_results; flags="-DN=$n" ;;
    roi) folder=roi_results; flags="-DN=$n -DFAST_CHECK" ;;
    invocation) folder=invocation_results; flags="-DN=$n -DFAST_CHECK -DINVOCATION_STATS" ;;
  esac
  output="$target/$folder/${variant}_n${n}"
  mkdir -p "$output/m5out-$tag" outputs outputs-cache
  make BMARK_SPECIFIC_CFLAGS="$flags" gem5-accel gem5-cpu > "$output/build-record.log" 2>&1
  cp "$bench-gem5-accel" "$output/guest-accel"
  cp "$bench-gem5" "$output/guest-cpu"
  sha256sum "$output/guest-accel" "$output/guest-cpu" > "$output/binaries.sha256"
  args=("$sim" "--outdir=$output/m5out-$tag" /worksrc/configs/aladdin/aladdin_se.py)
  [[ "$stage" != invocation ]] || args+=(--enable-stats-dump-and-resume)
  args+=("${common[@]}" "--accel_cfg_file=$work/$cfg" -c "$work/$bench-gem5-accel")
  printf '%q ' "${args[@]}" > "$output/command-accel.txt"; printf '\n' >> "$output/command-accel.txt"
  timeout 1200 "${args[@]}" > "$output/gem5-$tag.log" 2>&1
  if [[ "$stage" == full ]]; then grep -qx 'GEMM passed: 0 mismatches' "$output/gem5-$tag.log";
  else grep -q '^GEMM checksum:' "$output/gem5-$tag.log"; fi
  mkdir -p "$output/model"
  cp -a outputs outputs-cache "$output/model/"
  if [[ "$stage" != invocation ]]; then
    mkdir -p "$output/m5out-cpu"
    args=("$sim" "--outdir=$output/m5out-cpu" /worksrc/configs/example/se.py "${common[@]}" -c "$work/$bench-gem5")
    printf '%q ' "${args[@]}" > "$output/command-cpu.txt"; printf '\n' >> "$output/command-cpu.txt"
    timeout 1200 "${args[@]}" > "$output/gem5-cpu.log" 2>&1
    if [[ "$stage" == full ]]; then grep -qx 'GEMM passed: 0 mismatches' "$output/gem5-cpu.log";
    else grep -q '^GEMM checksum:' "$output/gem5-cpu.log"; fi
  fi
  echo "Completed $variant N=$n $stage"
done
