#!/usr/bin/env bash
# Reusable REPS>=2 repeated-invocation runner. Unlike results/diagnostics/
# repeated_input_n24{,_fixed}/ (produced by one-off manual commands during
# development), this is a committed, parameterized tool: any variant, N, and
# REPS count, with per-call correctness checking (not just a final check)
# and an optional runtime mutation independent of the one the trace was
# built with. See docs/NEXT_STEPS.md section 3.
#
# Usage (run from repo root, on the host -- this script execs into the
# Podman/Docker container itself, matching scripts/run.sh's pattern):
#   scripts/run_repeated.sh <variant> <N> <REPS> [--independent-mutation]
#     variant: base | tiled2 | tiled4
#
# Output goes to results/diagnostics/repeated_n<N>_reps<REPS>_<variant>[_independent]/:
#   trace.sha256   - trace file hash (same trace reused for all REPS calls)
#   build.log      - trace + accelerator + CPU build log
#   gem5-accel.log - full gem5 output: per-call "GEMM call K passed/FAILED"
#                    lines, per-call labeled stats-dump blocks, final summary
#   m5out-accel/   - gem5 --outdir (stats.txt has one labeled block per call)
#
# Then run: python3 scripts/summarize_repeated.py <that output dir>
set -euo pipefail

variant=${1:?usage: scripts/run_repeated.sh <base|tiled2|tiled4> <N> <REPS> [--independent-mutation]}
n=${2:?usage: scripts/run_repeated.sh <base|tiled2|tiled4> <N> <REPS> [--independent-mutation]}
reps=${3:?usage: scripts/run_repeated.sh <base|tiled2|tiled4> <N> <REPS> [--independent-mutation]}
independent=${4:-}

case "$variant" in
  base) bench=gemm_acp_pilot; cfg=gem5_cache.cfg; accel_out=m5out-cache ;;
  tiled2) bench=gemm_tiled2; cfg=gem5.cfg; accel_out=m5out-accel ;;
  tiled4) bench=gemm_tiled4; cfg=gem5.cfg; accel_out=m5out-accel ;;
  *) echo "variant must be base, tiled2, or tiled4" >&2; exit 2 ;;
esac

extra_flags=""
suffix=""
if [[ "$independent" == "--independent-mutation" ]]; then
  extra_flags="-DINDEPENDENT_MUTATION"
  suffix="_independent"
fi

project_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
image='xyzsam/gem5-aladdin@sha256:03b405408f17ceab194b08e03c986fcffd3ed10486d3443bd17eda87b33bee92'
volume=${COHERENT_GEMM_VOLUME:-coherent-gemm-source}
command -v docker >/dev/null || { echo 'Docker (or a docker-shimmed Podman) is required.' >&2; exit 1; }

output_name="repeated_n${n}_reps${reps}_${variant}${suffix}"

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
work_dir=\"\$gem5_root/src/aladdin/integration-test/with-cpu/${output_name}\"
rm -rf \"\$work_dir\"
mkdir -p \"\$work_dir\"
cp -a \"/project/benchmarks/${bench}/.\" \"\$work_dir/\"
cd \"\$work_dir\"

output=\"/project/results/diagnostics/${output_name}\"
mkdir -p \"\$output/${accel_out}\"

make BMARK_SPECIFIC_CFLAGS=\"-DN=${n} -DREPS=${reps}\" -B run-trace > \"\$output/build.log\" 2>&1
grep -q 'GEMM passed: 0 mismatches' \"\$output/build.log\"
sha256sum dynamic_trace.gz > \"\$output/trace.sha256\"

make BMARK_SPECIFIC_CFLAGS=\"-DN=${n} -DREPS=${reps} -DFAST_CHECK -DINVOCATION_STATS -DPER_CALL_CHECK ${extra_flags}\" gem5-accel gem5-cpu >> \"\$output/build.log\" 2>&1

\"\$sim\" --outdir=\"\$output/${accel_out}\" \\
  \"\$gem5_root/configs/aladdin/aladdin_se.py\" \\
  --enable-stats-dump-and-resume \\
  --ruby --num-cpus=1 --num-l2caches=1 --num-dirs=1 \\
  --cpu-type=DerivO3CPU --mem-size=1GB --mem-type=DDR3_1600_8x8 \\
  --sys-clock=1GHz --ruby-clock=1GHz --cacheline_size=64 \\
  --accel_cfg_file=\"\$work_dir/${cfg}\" \\
  -c \"\$work_dir/${bench}-gem5-accel\" \\
  > \"\$output/gem5-accel.log\" 2>&1

echo \"=== per-call results ===\"
grep -E 'GEMM (call|per-call)' \"\$output/gem5-accel.log\" || true
echo \"Completed ${variant} N=${n} REPS=${reps}${suffix}. See \$output/\"
"
