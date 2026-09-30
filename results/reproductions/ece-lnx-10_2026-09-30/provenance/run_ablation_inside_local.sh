#!/usr/bin/env bash
set -euo pipefail

n=$1
requested_mode=$2
gem5_root=/worksrc
sim=$gem5_root/build/X86/gem5.opt
test -x "$sim" || { echo 'Run scripts/setup.sh first.' >&2; exit 1; }
git -C "$gem5_root/src/aladdin" apply --reverse --check \
  /project/patches/bounded_queue_gemm_pilot.patch >/dev/null || {
    echo 'Finite-queue simulator patch is missing.' >&2; exit 1;
  }

common_args=(
  --ruby --num-cpus=1 --num-l2caches=1 --num-dirs=1
  --cpu-type=DerivO3CPU --mem-size=1GB --mem-type=DDR3_1600_8x8
  --sys-clock=1GHz --ruby-clock=1GHz --cacheline_size=64
)

for variant in ${COHERENT_GEMM_VARIANTS:-base tiled4}; do
  if [[ $variant == base ]]; then
    benchmark=gemm_acp_pilot
    config=gem5_cache.cfg
    accel_log=gem5-cache.log
    accel_out=m5out-cache
  else
    benchmark=gemm_$variant
    config=gem5.cfg
    accel_log=gem5-accel.log
    accel_out=m5out-accel
  fi
  work_dir="$gem5_root/src/aladdin/integration-test/with-cpu/package_${variant}_n${n}"
  mkdir -p "$work_dir"
  cp -a "/project/benchmarks/$benchmark/." "$work_dir/"
  cd "$work_dir"
  make BMARK_SPECIFIC_CFLAGS="-DN=$n" -B run-trace > trace-build.log 2>&1
  grep -q 'GEMM passed: 0 mismatches' trace-build.log
  sha256sum dynamic_trace.gz > "/artifacts/results/${variant}_n${n}_trace.sha256"
  if [[ $variant == base ]]; then mkdir -p outputs-cache; else mkdir -p outputs; fi

  for mode in full roi invocation; do
    if [[ $requested_mode != all && $requested_mode != "$mode" ]]; then
      continue
    fi
    case "$mode" in
      full) root=/artifacts/results/fair_results; flags="-DN=$n" ;;
      roi) root=/artifacts/results/roi_results; flags="-DN=$n -DFAST_CHECK" ;;
      invocation) root=/artifacts/results/invocation_results
                  flags="-DN=$n -DFAST_CHECK -DINVOCATION_STATS" ;;
    esac
    output="$root/${variant}_n${n}"
    mkdir -p "$output/$accel_out"
    make BMARK_SPECIFIC_CFLAGS="$flags" gem5-accel gem5-cpu > "$output/build.log" 2>&1
    gem5_cmd=("$sim" "--outdir=$output/$accel_out"
      "$gem5_root/configs/aladdin/aladdin_se.py")
    if [[ $mode == invocation ]]; then
      gem5_cmd+=(--enable-stats-dump-and-resume)
    fi
    "${gem5_cmd[@]}" "${common_args[@]}" \
      --accel_cfg_file="$work_dir/$config" \
      -c "$work_dir/$benchmark-gem5-accel" \
      > "$output/$accel_log" 2>&1
    if [[ $mode == full ]]; then
      grep -q 'GEMM passed: 0 mismatches' "$output/$accel_log"
    else
      grep -q 'GEMM checksum:' "$output/$accel_log"
    fi
    if [[ $mode == invocation ]]; then
      grep -q '# Stats desc: gemm invocation' "$output/$accel_out/stats.txt"
      continue
    fi
    mkdir -p "$output/m5out-cpu"
    "$sim" --outdir="$output/m5out-cpu" \
      "$gem5_root/configs/example/se.py" \
      "${common_args[@]}" \
      -c "$work_dir/$benchmark-gem5" \
      > "$output/gem5-cpu.log" 2>&1
    if [[ $mode == full ]]; then
      grep -q 'GEMM passed: 0 mismatches' "$output/gem5-cpu.log"
    else
      grep -q 'GEMM checksum:' "$output/gem5-cpu.log"
    fi
  done
done

echo "Completed N=$n mode=$requested_mode. See results/."
