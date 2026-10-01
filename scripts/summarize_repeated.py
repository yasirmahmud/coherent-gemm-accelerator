"""Strict validation of repeated correctness diagnostics and paired timing blocks.

Historical runs require --expected-calls; new runs may declare it in run.json.
A recorded hash validates metadata only unless the trace itself is retained.
"""
import argparse
import hashlib
import json
import re
from pathlib import Path


BLOCK = (r"---------- Begin Simulation Statistics ----------(.*?)"
         r"---------- End Simulation Statistics\s*----------")


def per_call_correctness(log_text):
    records = re.findall(r"(?m)^GEMM call (\d+) (passed|FAILED): (\d+) mismatches$", log_text)
    for _, status, mismatches in records:
        if (status == "passed") != (int(mismatches) == 0):
            raise ValueError("Correctness status contradicts mismatch count")
    return [(int(i), int(m)) for i, _, m in records]


def invocation_blocks(stats_path):
    text = stats_path.read_text()
    blocks = re.findall(BLOCK, text, re.DOTALL)
    if len(blocks) != text.count("---------- Begin Simulation Statistics ----------"):
        raise ValueError("Truncated statistics block")
    pairs = []
    i = 0
    while i < len(blocks):
        block = blocks[i]
        if re.search(r"(?m)^# Stats desc: .*datapath completed\.$", block):
            if i + 1 >= len(blocks) or not re.search(r"(?m)^# Stats desc: gemm invocation$", blocks[i + 1]):
                raise ValueError("Completion interval lacks matching host return")
            pairs.append((block, blocks[i + 1]))
            i += 2
        else:
            if "# Stats desc:" in block:
                raise ValueError("Unexpected or out-of-order labeled interval")
            # gem5's one final process-exit block is allowed only at the end.
            if i != len(blocks) - 1:
                raise ValueError("Unlabeled interval inside call sequence")
            i += 1
    return pairs


def interval_ticks(block):
    values = re.findall(r"(?m)^sim_ticks\s+(\d+)\b", block)
    if len(values) != 1 or int(values[0]) <= 0:
        raise ValueError("Interval needs exactly one positive sim_ticks value")
    return int(values[0])


def per_call_offload_intervals(stats_path):
    return [(interval_ticks(a), interval_ticks(a) + interval_ticks(b))
            for a, b in invocation_blocks(stats_path)]


def validate_run(output_dir, expected_calls=None):
    output_dir = Path(output_dir)
    metadata_path = output_dir / "run.json"
    if metadata_path.exists():
        declared = json.loads(metadata_path.read_text())["expected_calls"]
        if expected_calls is not None and declared != expected_calls:
            raise ValueError("Expected count disagrees with run metadata")
        expected_calls = declared
    if type(expected_calls) is not int or expected_calls < 2:
        raise ValueError("Declare expected calls >=2 in run.json or --expected-calls")
    text = (output_dir / "gem5-accel.log").read_text()
    exits = re.findall(r"(?m)^Exiting @ tick (\d+) because exiting with last active thread context$", text)
    if len(exits) != 1:
        raise ValueError("Run lacks a single normal simulator exit")
    correctness = per_call_correctness(text)
    if [i for i, _ in correctness] != list(range(expected_calls)):
        raise ValueError("Missing, duplicate, or out-of-order correctness records")
    totals = re.findall(r"(?m)^GEMM per-call total: (\d+) mismatches across (\d+) calls$", text)
    if totals != [(str(sum(m for _, m in correctness)), str(expected_calls))]:
        raise ValueError("Missing or inconsistent per-call summary")
    stats = list(output_dir.glob("m5out-*/stats.txt"))
    if len(stats) != 1:
        raise ValueError("Require exactly one repeated-run statistics file")
    intervals = per_call_offload_intervals(stats[0])
    if len(intervals) != expected_calls:
        raise ValueError("Expected one completion/return pair per call")
    hash_text = (output_dir / "trace.sha256").read_text()
    hash_match = re.fullmatch(r"([0-9a-fA-F]{64})\s+\*?dynamic_trace\.gz\s*", hash_text)
    if not hash_match:
        raise ValueError("Missing or invalid trace SHA-256 metadata")
    trace_hash = hash_match.group(1).lower()
    trace_path = output_dir / "dynamic_trace.gz"
    if trace_path.exists() and hashlib.sha256(trace_path.read_bytes()).hexdigest() != trace_hash:
        raise ValueError("Retained trace hash does not match")
    if any(m for _, m in correctness):
        raise ValueError("Failed correctness: " + str(correctness))
    return dict(expected_calls=expected_calls, trace_sha256=trace_hash,
                trace_verified=trace_path.exists(),
                calls=[dict(call=i, mismatches=m, completion_ticks=c, offload_ticks=o)
                       for (i, m), (c, o) in zip(correctness, intervals)])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    parser.add_argument("--expected-calls", type=int)
    args = parser.parse_args()
    try:
        print(json.dumps(validate_run(args.directory, args.expected_calls), indent=2))
    except (ValueError, OSError, KeyError, TypeError) as error:
        parser.exit(1, f"Validation failed: {error}\n")


if __name__ == "__main__":
    main()
