#!/usr/bin/env bash
set -euo pipefail

n=${1:?usage: scripts/run.sh N [all|full|roi|invocation]}
mode=${2:-all}
case "$n" in 24|32) ;; *) echo 'Validated sizes are 24 and 32.' >&2; exit 2 ;; esac
case "$mode" in all|full|roi|invocation) ;; *) echo 'Unknown mode.' >&2; exit 2 ;; esac

project_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
image='xyzsam/gem5-aladdin@sha256:03b405408f17ceab194b08e03c986fcffd3ed10486d3443bd17eda87b33bee92'
volume=${COHERENT_GEMM_VOLUME:-coherent-gemm-source}
command -v docker >/dev/null || { echo 'Docker is required.' >&2; exit 1; }

docker run --rm \
  -e ALADDIN_HOME=/worksrc/src/aladdin \
  -e TRACER_HOME=/workspace/LLVM-Tracer \
  -e LLVM_HOME=/usr/local \
  -v "$volume:/worksrc" \
  -v "$project_root:/project" \
  "$image" bash /project/scripts/run_inside.sh "$n" "$mode"
