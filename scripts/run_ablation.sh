#!/usr/bin/env bash
# Reproducible runner for exploratory variants beyond the validated base/
# tiled4 pair -- e.g. the tile-width ablation's gemm_tiled2. Mirrors
# scripts/run_inside.sh's per-variant logic exactly (same file layout, same
# correctness checks, same flags), just for one variant at a time and not
# restricted to base/tiled4. Kept separate from scripts/run.sh /
# scripts/run_inside.sh so the validated two-variant pipeline is never
# touched by this. See docs/NEXT_STEPS.md section 3 ("give tile-width-2
# documented, repeatable run commands; it was run manually").
#
# Usage (run from repo root, on the host):
#   bash scripts/run_ablation.sh <variant> <N> <all|full|roi|invocation>
#     variant: any benchmarks/gemm_<variant>/ directory, e.g. base, tiled2,
#              tiled4, or a new one you add the same way. "base" maps to
#              benchmarks/gemm_acp_pilot; anything else maps to
#              benchmarks/gemm_<variant>.
#
# Output layout matches scripts/run_inside.sh exactly:
#   results/{fair,roi,invocation}_results/<variant>_n<N>/
# so scripts/explore_size.py-style summarization can read it the same way
# (that script currently assumes base/tiled4 specifically -- extend it, or
# read the raw logs/stats.txt directly, for other variants).
set -euo pipefail

variant=${1:?usage: scripts/run_ablation.sh <variant> <N> <all|full|roi|invocation>}
n=${2:?usage: scripts/run_ablation.sh <variant> <N> <all|full|roi|invocation>}
requested_mode=${3:?usage: scripts/run_ablation.sh <variant> <N> <all|full|roi|invocation>}
case "$requested_mode" in all|full|roi|invocation) ;; *) echo 'Unknown mode.' >&2; exit 2 ;; esac

if [[ "$variant" == base ]]; then
  benchmark=gemm_acp_pilot
  config=gem5_cache.cfg
  accel_log=gem5-cache.log
  accel_out=m5out-cache
else
  benchmark="gemm_${variant}"
  config=gem5.cfg
  accel_log=gem5-accel.log
  accel_out=m5out-accel
fi
[[ -d "$(dirname "${BASH_SOURCE[0]}")/../benchmarks/$benchmark" ]] || {
  echo "No benchmarks/$benchmark directory." >&2; exit 2;
}

project_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
image='xyzsam/gem5-aladdin@sha256:03b405408f17ceab194b08e03c986fcffd3ed10486d3443bd17eda87b33bee92'
volume=${COHERENT_GEMM_VOLUME:-coherent-gemm-source}
command -v docker >/dev/null || { echo 'Docker (or a docker-shimmed Podman) is required.' >&2; exit 1; }

docker run --rm \
  -e ALADDIN_HOME=/worksrc/src/aladdin \
  -e TRACER_HOME=/workspace/LLVM-Tracer \
  -e LLVM_HOME=/usr/local \
  -v "$volume:/worksrc" \
  -v "$project_root:/project" \
  "$image" bash -c "
set -euo pipefail
gem5_root=/worksrc
sim=\$gem5_root/build/X86/gem5.opt
test -x \"\$sim\" || { echo 'Run scripts/setup.sh first.' >&2; exit 1; }

common_args=(--ruby --num-cpus=1 --num-l2caches=1 --num-dirs=1
  --cpu-type=DerivO3CPU --mem-size=1GB --mem-type=DDR3_1600_8x8
  --sys-clock=1GHz --ruby-clock=1GHz --cacheline_size=64)

work_dir=\"\$gem5_root/src/aladdin/integration-test/with-cpu/package_${variant}_n${n}\"
mkdir -p \"\$work_dir\"
cp -a \"/project/benchmarks/${benchmark}/.\" \"\$work_dir/\"
cd \"\$work_dir\"
make BMARK_SPECIFIC_CFLAGS=\"-DN=${n}\" -B run-trace > trace-build.log 2>&1
grep -q 'GEMM passed: 0 mismatches' trace-build.log
sha256sum dynamic_trace.gz > \"/project/results/${variant}_n${n}_trace.sha256\"

for mode in full roi invocation; do
  if [[ '${requested_mode}' != all && '${requested_mode}' != \"\$mode\" ]]; then
    continue
  fi
  case \"\$mode\" in
    full) root=/project/results/fair_results; flags=\"-DN=${n}\" ;;
    roi) root=/project/results/roi_results; flags=\"-DN=${n} -DFAST_CHECK\" ;;
    invocation) root=/project/results/invocation_results
                flags=\"-DN=${n} -DFAST_CHECK -DINVOCATION_STATS\" ;;
  esac
  output=\"\$root/${variant}_n${n}\"
  mkdir -p \"\$output/${accel_out}\"
  make BMARK_SPECIFIC_CFLAGS=\"\$flags\" gem5-accel gem5-cpu > \"\$output/build.log\" 2>&1
  gem5_cmd=(\"\$sim\" \"--outdir=\$output/${accel_out}\" \"\$gem5_root/configs/aladdin/aladdin_se.py\")
  if [[ \"\$mode\" == invocation ]]; then
    gem5_cmd+=(--enable-stats-dump-and-resume)
  fi
  \"\${gem5_cmd[@]}\" \"\${common_args[@]}\" \\
    --accel_cfg_file=\"\$work_dir/${config}\" \\
    -c \"\$work_dir/${benchmark}-gem5-accel\" \\
    > \"\$output/${accel_log}\" 2>&1
  if [[ \"\$mode\" == full ]]; then
    grep -q 'GEMM passed: 0 mismatches' \"\$output/${accel_log}\"
  else
    grep -q 'GEMM checksum:' \"\$output/${accel_log}\"
  fi
  if [[ \"\$mode\" == invocation ]]; then
    grep -q '# Stats desc: gemm invocation' \"\$output/${accel_out}/stats.txt\"
    continue
  fi
  mkdir -p \"\$output/m5out-cpu\"
  \"\$sim\" --outdir=\"\$output/m5out-cpu\" \"\$gem5_root/configs/example/se.py\" \\
    \"\${common_args[@]}\" -c \"\$work_dir/${benchmark}-gem5\" \\
    > \"\$output/gem5-cpu.log\" 2>&1
  if [[ \"\$mode\" == full ]]; then
    grep -q 'GEMM passed: 0 mismatches' \"\$output/gem5-cpu.log\"
  else
    grep -q 'GEMM checksum:' \"\$output/gem5-cpu.log\"
  fi
done
echo \"Completed ${variant} N=${n} mode=${requested_mode}. See results/.\"
"
