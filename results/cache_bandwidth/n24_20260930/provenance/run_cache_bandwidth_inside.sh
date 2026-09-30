#!/usr/bin/env bash
set -euo pipefail
cohort=${GEMM_COHORT:?Set GEMM_COHORT through run_cache_bandwidth.sh}
target="/project/results/cache_bandwidth/$cohort"
scratch="/project/.artifacts/cache_bandwidth/$cohort"
sim=/worksrc/build/X86/gem5.opt
test -x "$sim" || { echo 'Build the simulator using scripts/setup.sh first.' >&2; exit 1; }
git -C /worksrc/src/aladdin apply --reverse --check \
  /project/patches/bounded_queue_gemm_pilot.patch
mkdir -p "$scratch/integration-test/common" "$scratch/integration-test/with-cpu"
cp -a /worksrc/src/aladdin/integration-test/common/. "$scratch/integration-test/common/"
cp -a "$scratch/integration-test/common" "$target/provenance/common"
git -C /worksrc rev-parse HEAD > "$target/provenance/gem5-commit.txt"
git -C /worksrc/src/aladdin rev-parse HEAD > "$target/provenance/aladdin-commit.txt"
git -C /worksrc/src/aladdin diff --binary > "$target/provenance/aladdin-working.diff"
sha256sum "$sim" > "$target/provenance/simulator.sha256"
uname -a > "$target/provenance/host.txt"
date -u +%FT%TZ > "$target/provenance/started-at.txt"
common_args=(--ruby --num-cpus=1 --num-l2caches=1 --num-dirs=1
  --cpu-type=DerivO3CPU --mem-size=1GB --mem-type=DDR3_1600_8x8
  --sys-clock=1GHz --ruby-clock=1GHz --cacheline_size=64)

for variant in base tiled4; do
  if [[ "$variant" == base ]]; then
    benchmark=gemm_acp_pilot; config=gem5_cache.cfg; width=1
  else
    benchmark=gemm_tiled4; config=gem5.cfg; width=4
  fi
  work="$scratch/integration-test/with-cpu/$variant"
  inputs="$target/inputs/$variant"
  mkdir -p "$work" "$inputs"
  cp -a "/project/benchmarks/$benchmark/." "$work/"
  cp -a "/project/benchmarks/$benchmark/." "$inputs/"
  cd "$work"
  echo "$(date -u +%FT%TZ) Build one shared N=24 trace: $variant"
  make BMARK_SPECIFIC_CFLAGS='-DN=24' -B run-trace > "$inputs/trace-build.log" 2>&1
  grep -qx 'GEMM passed: 0 mismatches' "$inputs/trace-build.log"
  cp dynamic_trace.gz "$inputs/"
  sha256sum dynamic_trace.gz > "$inputs/trace.sha256"
  gzip -cd dynamic_trace.gz | sha256sum > "$inputs/logical-trace.sha256"
  mkdir -p outputs outputs-cache
  for bandwidth in 1 2 4; do
    point="$target/points/${variant}_bw${bandwidth}"
    mkdir -p "$point"
    cp "$inputs/$config" "$config"
    # The pinned toolchain image supplies Python 2, while the host summarizer uses Python 3.
    python - "$config" "$bandwidth" <<'PY'
import re, sys
path, bandwidth = sys.argv[1:]
with open(path) as f:
    content = f.read()
content, count = re.subn(r'(?m)^cache_bandwidth\s*=.*$',
                        'cache_bandwidth = ' + bandwidth, content)
if count != 2:
    raise SystemExit('Expected bandwidth in DEFAULT and accelerator sections')
with open(path, 'w') as f:
    f.write(content)
PY
    cp "$config" "$point/accelerator.cfg"
    for stage in full roi invocation; do
      output="$point/$stage"
      mkdir -p "$output/m5out"
      case "$stage" in
        full) flags='-DN=24' ;;
        roi) flags='-DN=24 -DFAST_CHECK' ;;
        invocation) flags='-DN=24 -DFAST_CHECK -DINVOCATION_STATS' ;;
      esac
      make BMARK_SPECIFIC_CFLAGS="$flags" gem5-accel gem5-cpu > "$output/build.log" 2>&1
      sha256sum "$benchmark-gem5-accel" > "$output/binary.sha256"
      args=("$sim" "--outdir=$output/m5out" /worksrc/configs/aladdin/aladdin_se.py)
      if [[ "$stage" == invocation ]]; then args+=(--enable-stats-dump-and-resume); fi
      args+=("${common_args[@]}" "--accel_cfg_file=$work/$config" -c "$work/$benchmark-gem5-accel")
      printf '%q ' "${args[@]}" > "$output/command.txt"
      printf '\n' >> "$output/command.txt"
      echo "$(date -u +%FT%TZ) Run width=$width bandwidth=$bandwidth stage=$stage"
      timeout 900 "${args[@]}" > "$output/gem5.log" 2>&1
      if [[ "$stage" == full ]]; then
        grep -qx 'GEMM passed: 0 mismatches' "$output/gem5.log"
        # One independent CPU execution per kernel; CPU is unchanged across bandwidths.
        if [[ "$bandwidth" == 1 ]]; then
          mkdir -p "$inputs/cpu/m5out"
          cpu_args=("$sim" "--outdir=$inputs/cpu/m5out" /worksrc/configs/example/se.py
            "${common_args[@]}" -c "$work/$benchmark-gem5")
          printf '%q ' "${cpu_args[@]}" > "$inputs/cpu/command.txt"
          printf '\n' >> "$inputs/cpu/command.txt"
          timeout 900 "${cpu_args[@]}" > "$inputs/cpu/gem5.log" 2>&1
          grep -qx 'GEMM passed: 0 mismatches' "$inputs/cpu/gem5.log"
        fi
      else
        grep -q '^GEMM checksum:' "$output/gem5.log"
      fi
      # Preserve model outputs before the next run overwrites them.
      for model_dir in outputs outputs-cache; do
        if compgen -G "$model_dir/*" >/dev/null; then
          mkdir -p "$output/model/$model_dir"
          cp -a "$model_dir/." "$output/model/$model_dir/"
        fi
      done
      echo "$(date -u +%FT%TZ) Passed width=$width bandwidth=$bandwidth stage=$stage"
    done
  done
done
date -u +%FT%TZ > "$target/provenance/completed-at.txt"
echo 'All six points completed with full output checks.'
