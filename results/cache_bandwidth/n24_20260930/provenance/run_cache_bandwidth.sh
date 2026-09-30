#!/usr/bin/env bash
# Six fresh, isolated points: N=24, widths 1/4, cache bandwidth 1/2/4.
set -euo pipefail
project_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
cohort=${1:-n24_$(date -u +%Y%m%dT%H%M%SZ)}
[[ "$cohort" =~ ^[a-zA-Z0-9_-]+$ ]] || { echo 'Use a simple cohort name.' >&2; exit 2; }
target="$project_root/results/cache_bandwidth/$cohort"
[[ ! -e "$target" ]] || { echo "Refusing to overwrite $target" >&2; exit 2; }
engine=${COHERENT_GEMM_CONTAINER_ENGINE:-docker}
command -v "$engine" >/dev/null || { echo "Missing container engine: $engine" >&2; exit 1; }
image='xyzsam/gem5-aladdin@sha256:03b405408f17ceab194b08e03c986fcffd3ed10486d3443bd17eda87b33bee92'
source_mount=${COHERENT_GEMM_SOURCE:-${COHERENT_GEMM_VOLUME:-coherent-gemm-source}}
if [[ "$source_mount" == */* ]]; then source_mount=$(cd "$source_mount" && pwd -P); fi
mkdir -p "$target/provenance"
cp "$project_root/scripts/run_cache_bandwidth.sh" "$project_root/scripts/run_cache_bandwidth_inside.sh" \
  "$project_root/scripts/summarize_cache_bandwidth.py" "$target/provenance/"
git -C "$project_root" rev-parse HEAD > "$target/provenance/project-commit.txt"
git -C "$project_root" diff --binary > "$target/provenance/project-working.diff"
printf '%s\n' "$image" > "$target/provenance/container-image.txt"
"$engine" run --rm \
  -e ALADDIN_HOME=/worksrc/src/aladdin -e TRACER_HOME=/workspace/LLVM-Tracer \
  -e LLVM_HOME=/usr/local -e GEMM_COHORT="$cohort" \
  -v "$source_mount:/worksrc:ro" -v "$project_root:/project" \
  "$image" bash /project/scripts/run_cache_bandwidth_inside.sh \
  2>&1 | tee "$target/runner.log"
python3 "$project_root/scripts/summarize_cache_bandwidth.py" "$target"
echo "Validated study: $target"
