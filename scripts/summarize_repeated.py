"""Summarize a scripts/run_repeated.sh output directory: per-call
correctness and per-call offload intervals for REPS>=2 runs.

Usage: python3 scripts/summarize_repeated.py results/diagnostics/repeated_n24_reps3_base
"""

import re
import sys
from pathlib import Path


def per_call_correctness(log_text):
    """Returns list of (call_index, mismatches) from 'GEMM call K ...' lines."""
    return [
        (int(m.group(1)), int(m.group(2)))
        for m in re.finditer(r"GEMM call (\d+) \S+: (\d+) mismatches", log_text)
    ]


def per_call_offload_intervals(stats_path):
    """Generalizes scripts/summarize.py's invocation_intervals to REPS>=2:
    each accelerator call produces one 'datapath completed' block followed
    by one 'gemm invocation' block; returns a list of (completion_ticks,
    offload_ticks) pairs, one per call, in order."""
    text = stats_path.read_text()
    blocks = re.findall(
        r"---------- Begin Simulation Statistics ----------(.*?)"
        r"---------- End Simulation Statistics\s*----------",
        text,
        re.DOTALL,
    )
    intervals = []
    i = 0
    while i + 1 < len(blocks):
        if re.search(r"# Stats desc: .*datapath completed\.", blocks[i]):
            if "# Stats desc: gemm invocation" in blocks[i + 1]:
                completion = int(
                    re.search(r"(?m)^sim_ticks\s+(\d+)\b", blocks[i]).group(1)
                )
                host_return = int(
                    re.search(r"(?m)^sim_ticks\s+(\d+)\b", blocks[i + 1]).group(1)
                )
                intervals.append((completion, completion + host_return))
                i += 2
                continue
        i += 1
    return intervals


def main():
    if len(sys.argv) != 2:
        print("usage: python3 scripts/summarize_repeated.py <run_repeated.sh output dir>", file=sys.stderr)
        raise SystemExit(2)
    output_dir = Path(sys.argv[1])
    log_text = (output_dir / "gem5-accel.log").read_text()

    correctness = per_call_correctness(log_text)
    if not correctness:
        print("No 'GEMM call K ...' lines found -- was this built with -DPER_CALL_CHECK?", file=sys.stderr)
        raise SystemExit(1)

    stats_candidates = list(output_dir.glob("m5out-*/stats.txt"))
    if not stats_candidates:
        print("No m5out-*/stats.txt found.", file=sys.stderr)
        raise SystemExit(1)
    intervals = per_call_offload_intervals(stats_candidates[0])

    trace_hash = ""
    trace_hash_path = output_dir / "trace.sha256"
    if trace_hash_path.exists():
        trace_hash = trace_hash_path.read_text().split()[0]

    print(f"Trace SHA-256: {trace_hash}")
    print(f"{'call':>4} {'mismatches':>10} {'completion_ticks':>17} {'offload_ticks':>13}")
    any_failed = False
    for idx, mismatches in correctness:
        completion, offload = intervals[idx] if idx < len(intervals) else (None, None)
        if mismatches:
            any_failed = True
        print(f"{idx:>4} {mismatches:>10} {str(completion):>17} {str(offload):>13}")

    total_mismatches = sum(m for _, m in correctness)
    print()
    print(f"Total: {len(correctness)} calls, {total_mismatches} mismatches")
    if any_failed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
