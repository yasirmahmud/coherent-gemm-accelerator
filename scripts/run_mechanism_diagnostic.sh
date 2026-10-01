#!/usr/bin/env bash
# Isolated bounded cohorts. Graph requires the separately built diagnostic simulator.
set -euo pipefail
kind=${1:?Use graph or warm}
[[ "$kind" == graph || "$kind" == warm ]] || { echo 'Use graph or warm.' >&2; exit 2; }
cohort=${2:-${kind}_n24_$(date -u +%Y%m%dT%H%M%SZ)}
[[ "$cohort" =~ ^[a-zA-Z0-9_-]+$ ]] || { echo 'Use a simple cohort name.' >&2; exit 2; }
root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
target="$root/results/diagnostics/$cohort"
[[ ! -e "$target" ]] || { echo "Refusing to overwrite $target" >&2; exit 2; }
engine=${COHERENT_GEMM_CONTAINER_ENGINE:-docker}
source_dir=$(cd "${COHERENT_GEMM_SOURCE:-$root/.artifacts/source}" && pwd -P)
image='docker.io/xyzsam/gem5-aladdin@sha256:03b405408f17ceab194b08e03c986fcffd3ed10486d3443bd17eda87b33bee92'
mounts=(-v "$source_dir:/worksrc:ro" -v "$root:/project")
if [[ "$kind" == graph ]]; then
  diag_dir=$(cd "${COHERENT_GEMM_DIAGNOSTIC_SOURCE:-$root/.artifacts/diagnostic-source}" && pwd -P)
  mounts+=(-v "$diag_dir:/diagnostic:ro")
fi
mkdir -p "$target/provenance"
cp "$root/scripts/run_mechanism_diagnostic.sh" "$root/scripts/run_${kind}_diagnostic_inside.sh" \
   "$root/scripts/summarize_${kind}_diagnostic.py" "$target/provenance/"
cp "$root/patches/passive_graph_counters.patch" "$target/provenance/"
printf '%s\n' "$image" > "$target/provenance/container-image.txt"
git -C "$root" rev-parse HEAD > "$target/provenance/project-commit.txt"
git -C "$root" diff --binary > "$target/provenance/project-working.diff"
"$engine" run --rm "${mounts[@]}" -e ALADDIN_HOME=/worksrc/src/aladdin \
  -e TRACER_HOME=/workspace/LLVM-Tracer -e LLVM_HOME=/usr/local \
  -e "GEMM_DIAG_ROOT=/project/results/diagnostics/$cohort" \
  -e "GEMM_DIAG_SCRATCH=/project/.artifacts/$cohort/integration-test" \
  "$image" bash "/project/results/diagnostics/$cohort/provenance/run_${kind}_diagnostic_inside.sh" 2>&1 | tee "$target/runner.log"
python3 "$root/scripts/summarize_${kind}_diagnostic.py" "$target"
