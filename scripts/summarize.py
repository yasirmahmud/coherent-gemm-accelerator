"""Summarize paired coherent GEMM experiments after validating raw logs."""

import csv
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1] / "results"


def match(path, pattern):
    found = re.search(pattern, path.read_text(), re.MULTILINE)
    if found is None:
        raise ValueError(f"Missing {pattern!r} in {path}")
    return found.group(1)


def ticks(path):
    return int(match(path, r"^sim_ticks\s+(\d+)\b"))


def insts(path):
    return int(match(path, r"^sim_insts\s+(\d+)\b"))


def full_check(path):
    if "GEMM passed: 0 mismatches" not in path.read_text():
        raise ValueError(f"Full output check failed: {path}")


def checksum(path):
    return int(match(path, r"GEMM checksum: (-?\d+)"))


def invocation_intervals(path):
    blocks = re.findall(
        r"---------- Begin Simulation Statistics ----------(.*?)"
        r"---------- End Simulation Statistics\s*----------",
        path.read_text(),
        re.DOTALL,
    )
    if len(blocks) < 3:
        raise ValueError(f"Expected three stats intervals in {path}")
    if not re.search(r"# Stats desc: .*datapath completed\.", blocks[0]):
        raise ValueError(f"First interval is not datapath completion: {path}")
    if "# Stats desc: gemm invocation" not in blocks[1]:
        raise ValueError(f"Second interval is not host completion: {path}")
    first = int(re.search(r"(?m)^sim_ticks\s+(\d+)\b", blocks[0]).group(1))
    second = int(re.search(r"(?m)^sim_ticks\s+(\d+)\b", blocks[1]).group(1))
    return first, first + second


rows = []
for n in (24, 32):
    fair_base = ROOT / "fair_results" / f"base_n{n}"
    fair_tiled = ROOT / "fair_results" / f"tiled4_n{n}"
    roi_base = ROOT / "roi_results" / f"base_n{n}"
    roi_tiled = ROOT / "roi_results" / f"tiled4_n{n}"
    invocation_base = ROOT / "invocation_results" / f"base_n{n}"
    invocation_tiled = ROOT / "invocation_results" / f"tiled4_n{n}"

    for directory, accel in ((fair_base, "cache"), (fair_tiled, "accel")):
        full_check(directory / f"gem5-{accel}.log")
        full_check(directory / "gem5-cpu.log")

    values = [
        checksum(directory / f"gem5-{variant}.log")
        for directory, variant in (
            (roi_base, "cache"),
            (roi_base, "cpu"),
            (roi_tiled, "accel"),
            (roi_tiled, "cpu"),
        )
    ]
    if len(set(values)) != 1:
        raise ValueError(f"N={n}: ROI checksums differ: {values}")

    base_stats = roi_base / "m5out-cache" / "stats.txt"
    tiled_stats = roi_tiled / "m5out-accel" / "stats.txt"
    base_cpu_stats = roi_base / "m5out-cpu" / "stats.txt"
    tiled_cpu_stats = roi_tiled / "m5out-cpu" / "stats.txt"
    if insts(base_stats) != insts(tiled_stats):
        raise ValueError(f"N={n}: accelerator host instruction counts differ")

    base_completion, base_offload = invocation_intervals(
        invocation_base / "m5out-cache" / "stats.txt"
    )
    tiled_completion, tiled_offload = invocation_intervals(
        invocation_tiled / "m5out-accel" / "stats.txt"
    )
    if checksum(invocation_base / "gem5-cache.log") != values[0] or checksum(
        invocation_tiled / "gem5-accel.log"
    ) != values[0]:
        raise ValueError(f"N={n}: instrumented invocation output differs")

    base_ticks = ticks(base_stats)
    tiled_ticks = ticks(tiled_stats)
    tiled_cpu_ticks = ticks(tiled_cpu_stats)
    base_cycles = int(match(fair_base / "gem5-cache.log", r"^Cycle : (\d+) cycles"))
    tiled_cycles = int(match(fair_tiled / "gem5-accel.log", r"^Cycle : (\d+) cycles"))
    rows.append(
        dict(
            n=n,
            checksum=values[0],
            full_check_zero_mismatches=True,
            accel_host_insts=insts(base_stats),
            base_accel_cycles=base_cycles,
            tiled_accel_cycles=tiled_cycles,
            accel_cycle_reduction_pct=round(
                100 * (base_cycles - tiled_cycles) / base_cycles, 3
            ),
            base_completion_ticks=base_completion,
            tiled_completion_ticks=tiled_completion,
            base_offload_ticks=base_offload,
            tiled_offload_ticks=tiled_offload,
            offload_time_reduction_pct=round(
                100 * (base_offload - tiled_offload) / base_offload, 3
            ),
            base_accel_ticks=base_ticks,
            tiled_accel_ticks=tiled_ticks,
            whole_program_reduction_vs_base_pct=round(
                100 * (base_ticks - tiled_ticks) / base_ticks, 3
            ),
            base_cpu_ticks=ticks(base_cpu_stats),
            tiled_cpu_ticks=tiled_cpu_ticks,
            tiled_speedup_vs_same_kernel_cpu=round(
                tiled_cpu_ticks / tiled_ticks, 3
            ),
            base_area_um2=float(
                match(fair_base / "gem5-cache.log", r"^Total Area: ([\deE+.-]+) uM\^2")
            ),
            tiled_area_um2=float(
                match(fair_tiled / "gem5-accel.log", r"^Total Area: ([\deE+.-]+) uM\^2")
            ),
        )
    )

output = ROOT / "validated_summary.csv"
with output.open("w", newline="") as file:
    writer = csv.DictWriter(file, fieldnames=rows[0].keys())
    writer.writeheader()
    writer.writerows(rows)
print(output)
