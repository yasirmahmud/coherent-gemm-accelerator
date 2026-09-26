#!/usr/bin/env bash
set -euo pipefail

project_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
image='xyzsam/gem5-aladdin@sha256:03b405408f17ceab194b08e03c986fcffd3ed10486d3443bd17eda87b33bee92'
volume=${COHERENT_GEMM_VOLUME:-coherent-gemm-source}

command -v docker >/dev/null || { echo 'Docker is required.' >&2; exit 1; }
docker pull "$image"
docker volume create "$volume" >/dev/null
docker run --rm \
  -v "$volume:/worksrc" \
  -v "$project_root:/project:ro" \
  "$image" bash /project/scripts/setup_inside.sh

echo "Built gem5-Aladdin in Docker volume: $volume"
