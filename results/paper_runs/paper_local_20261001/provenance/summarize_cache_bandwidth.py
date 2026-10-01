"""Validate a complete cache-bandwidth cohort and derive its CSV and tables.

No simulator execution or historical results are used by this program.
"""

import argparse
import configparser
import csv
import gzip
import hashlib
import json
import math
import re
from pathlib import Path


VARIANTS = {"base": "gemm_acp_pilot", "tiled4": "gemm_tiled4"}
BANDWIDTHS = (1, 2, 4)
STAGES = ("full", "roi", "invocation")
PINNED_COMMITS = {"gem5-commit.txt": "d4efbee56d71f9609eab85393eff58f5dbf7763c",
                  "aladdin-commit.txt": "448b8f41865003e20eee0bdbd7a73febb5c3abe3"}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def single(text, pattern, source):
    matches = re.findall(pattern, text, re.MULTILINE)
    require(len(matches) == 1, f"Expected exactly one {pattern!r} in {source}")
    return matches[0]


def sha256(path):
    with path.open("rb") as handle:
        digest = hashlib.sha256()
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def check_hash(path, record):
    expected = record.read_text().split()[0]
    require(re.fullmatch(r"[0-9a-f]{64}", expected), f"Invalid hash: {record}")
    require(sha256(path) == expected, f"Hash mismatch: {path}")
    return expected


def stats_blocks(path):
    blocks = re.findall(
        r"---------- Begin Simulation Statistics ----------(.*?)"
        r"---------- End Simulation Statistics\s*----------",
        path.read_text(), re.DOTALL,
    )
    require(blocks, f"Missing complete statistics: {path}")
    return blocks


def stat(block, name):
    value = single(block, rf"^{re.escape(name)}\s+(\S+)", name)
    number = float(value)
    require(math.isfinite(number), f"Nonfinite counter: {name}")
    return number


def configuration(path):
    parser = configparser.ConfigParser(interpolation=None)
    parser.optionxform = str
    parser.read_string(path.read_text())
    return parser


def normalized_config(parser, benchmark):
    """Compare every effective config entry, allowing only documented paths/names."""
    datapath = f"system.{benchmark}_datapath"
    # Outputs are absolute in fs redirect rules; their cohort/point/stage varies.
    result = {}
    for section in parser.sections():
        for key, value in parser[section].items():
            if key == "cacheBandwidth" and section == datapath:
                continue
            value = value.replace(benchmark, "@KERNEL@")
            value = re.sub(r"/project/\.artifacts/cache_bandwidth/[^/]+/integration-test/with-cpu/(base|tiled4)",
                           "@WORK@", value)
            if key == "outputPrefix" and section == datapath:
                value = "@MODEL_OUTPUT@"
            value = re.sub(r"/project/results/cache_bandwidth/[^/]+/points/[^/]+/(full|roi|invocation)",
                           "@OUTPUT@", value)
            value = value.replace("gemm_cache_pilot.cfg", "@KERNEL_CONFIG@")
            value = value.replace("gemm_tiled4.cfg", "@KERNEL_CONFIG@")
            value = value.replace("@KERNEL@.cfg", "@KERNEL_CONFIG@")
            result[(section.replace(benchmark, "@KERNEL@"), key)] = value
    return result


def verify(cohort):
    require((cohort / "provenance/completed-at.txt").is_file(), "Runner did not complete")
    for name in ("simulator.sha256", "container-image.txt", "gem5-commit.txt",
                 "aladdin-commit.txt", "run_cache_bandwidth_inside.sh"):
        require((cohort / "provenance" / name).is_file(), f"Missing provenance: {name}")
    for name, expected in PINNED_COMMITS.items():
        require((cohort / "provenance" / name).read_text().strip() == expected,
                f"Source revision differs from pinned build: {name}")
    expected_points = {f"{variant}_bw{bandwidth}" for variant in VARIANTS for bandwidth in BANDWIDTHS}
    require({p.name for p in (cohort / "points").iterdir() if p.is_dir()} == expected_points,
            "Expected exactly six width/bandwidth points")
    rows = []
    configs = {stage: [] for stage in STAGES}
    for variant, benchmark in VARIANTS.items():
        inputs = cohort / "inputs" / variant
        trace_hash = check_hash(inputs / "dynamic_trace.gz", inputs / "trace.sha256")
        with gzip.open(inputs / "dynamic_trace.gz", "rb") as handle:
            digest = hashlib.sha256()
            for block in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(block)
        logical_hash = digest.hexdigest()
        require(logical_hash == (inputs / "logical-trace.sha256").read_text().split()[0],
                f"Logical trace hash mismatch: {variant}")
        for check in (inputs / "trace-build.log", inputs / "cpu/gem5.log"):
            single(check.read_text(), r"^GEMM passed: (0) mismatches$", check)
            require("GEMM FAILED" not in check.read_text(), f"Failed output check: {check}")
        graph_sizes = []
        stage_binary_hashes = {stage: set() for stage in STAGES}
        for bandwidth in BANDWIDTHS:
            point = cohort / "points" / f"{variant}_bw{bandwidth}"
            requested = configuration(point / "accelerator.cfg")
            require(requested[benchmark]["cache_bandwidth"] == str(bandwidth),
                    f"Wrong requested bandwidth: {point}")
            require(requested.defaults()["cache_bandwidth"] == str(bandwidth),
                    f"Wrong default bandwidth: {point}")
            row = dict(n=24, variant=variant, width=1 if variant == "base" else 4,
                       bandwidth=bandwidth, full_check_zero_mismatches=True,
                       trace_sha256=trace_hash, logical_trace_sha256=logical_hash)
            cycles = []
            for stage in STAGES:
                output = point / stage
                log = (output / "gem5.log").read_text()
                require("GEMM FAILED" not in log and "fatal:" not in log and "panic:" not in log,
                        f"Simulator/check failure: {output}")
                if stage == "full":
                    single(log, r"^GEMM passed: (0) mismatches$", output)
                else:
                    row[f"{stage}_checksum"] = int(single(log, r"^GEMM checksum: (-?\d+)$", output))
                cycle = int(single(log, r"^Cycle : (\d+) cycles$", output))
                require(cycle > 0, f"Empty schedule: {output}")
                cycles.append(cycle)
                graph_sizes.append((int(single(log, r"^Num of Nodes: (\d+)$", output)),
                                    int(single(log, r"^\s*Total connected nodes: (\d+)$", output))))
                stage_binary_hashes[stage].add((output / "binary.sha256").read_text().split()[0])
                effective = configuration(output / "m5out/config.ini")
                section = effective[f"system.{benchmark}_datapath"]
                require(section["cacheBandwidth"] == str(bandwidth), f"Wrong effective bandwidth: {output}")
                for key, expected in {"cacheQueueSize": "32", "cacheSize": "32kB",
                                      "cacheAssoc": "4", "cacheLineSize": "64", "cycleTime": "1"}.items():
                    require(section[key] == expected, f"Changed {key}: {output}")
                require(effective["system.cpu"]["type"] == "DerivO3CPU", f"Changed CPU: {output}")
                configs[stage].append((output, normalized_config(effective, benchmark)))
                blocks = stats_blocks(output / "m5out/stats.txt")
                if stage == "invocation":
                    require(len(blocks) == 3, f"Expected three timing blocks: {output}")
                    require(f"# Stats desc: {benchmark}_datapath completed." in blocks[0],
                            f"Missing accelerator completion: {output}")
                    require("# Stats desc: gemm invocation" in blocks[1], f"Missing host completion: {output}")
                    first = int(stat(blocks[0], "sim_ticks"))
                    returned = int(stat(blocks[1], "sim_ticks"))
                    require(first > 0 and returned > 0, f"Empty timing interval: {output}")
                    require(int(stat(blocks[1], "final_tick") - stat(blocks[0], "final_tick")) == returned,
                            f"Host return block did not reset timing: {output}")
                    # --enable-stats-dump-and-resume dumps AND resets at accelerator completion.
                    row.update(completion_ticks=first, return_segment_ticks=returned,
                               offload_ticks=first + returned, sim_freq=int(stat(blocks[0], "sim_freq")))
                else:
                    require(len(blocks) == 1, f"Unexpected timing blocks: {output}")
                if stage == "roi":
                    row["whole_program_ticks"] = int(stat(blocks[0], "sim_ticks"))
                    row["accel_host_insts"] = int(stat(blocks[0], "sim_insts"))
                if stage == "full":
                    prefix = f"system.{benchmark}_datapath."
                    for label, counter in {"dcache_loads": "total_dcache_loads", "dcache_stores": "total_dcache_stores",
                                           "dcache_latency_ticks": "dcache_latency::mean",
                                           "dcache_queue_time_ticks": "dcache_queue_time::mean",
                                           "dcache_latency_samples": "dcache_latency::samples",
                                           "dcache_queue_samples": "dcache_queue_time::samples"}.items():
                        row[label] = stat(blocks[0], prefix + counter)
                    row["fu_area_um2"] = float(single(log, r"^FU Area: (\S+) uM\^2$", output))
                    row["mem_area_um2"] = float(single(log, r"^MEM Area: (\S+) uM\^2$", output))
                    row["total_area_um2"] = float(single(log, r"^Total Area: (\S+) uM\^2$", output))
                    require(row["dcache_latency_samples"] == row["dcache_loads"] + row["dcache_stores"],
                            f"Cache histogram/count disagreement: {output}")
            require(len(set(cycles)) == 1, f"Stage-dependent schedule: {point}: {cycles}")
            row["datapath_cycles"] = cycles[0]
            require(row["roi_checksum"] == row["invocation_checksum"], f"Checksum mismatch: {point}")
            rows.append(row)
        require(len(set(graph_sizes)) == 1, f"Different input graph across bandwidth/stage: {variant}")
        for stage, hashes in stage_binary_hashes.items():
            require(len(hashes) == 1 and all(re.fullmatch(r"[0-9a-f]{64}", h) for h in hashes),
                    f"Different binaries across bandwidth: {variant}, {stage}")
    require(len({row["roi_checksum"] for row in rows}) == 1, "Output checksums differ across points")
    require(len({row["accel_host_insts"] for row in rows}) == 1, "Host work differs across points")
    require(len({row["sim_freq"] for row in rows}) == 1, "Simulator tick frequency differs")
    for stage, entries in configs.items():
        reference = entries[0][1]
        for output, current in entries[1:]:
            changed = {key: (reference.get(key), current.get(key)) for key in reference.keys() | current.keys()
                       if reference.get(key) != current.get(key)}
            require(not changed, f"Uncontrolled configuration changes ({stage}): {output}: {changed}")
    for row in rows:
        base = next(r for r in rows if r["variant"] == "base" and r["bandwidth"] == row["bandwidth"])
        for field, label in (("datapath_cycles", "cycle_reduction_pct"), ("offload_ticks", "offload_reduction_pct")):
            row[label] = round(100 * (base[field] - row[field]) / base[field], 6)
    return rows


def write_summary(cohort, rows):
    with (cohort / "summary.csv").open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    lines = ["# Cache-bandwidth sensitivity: N=24", "",
             "One cohort; widths 1/4; 1/2/4 issued cache requests per accelerator cycle.", "",
             "All six full accelerator checks and both CPU reference checks pass.",
             "One trace per kernel is reused across bandwidth settings. Effective configurations",
             "are compared across all six points within each measurement stage.", "",
             "| Bandwidth | Width | Datapath cycles | Offload ticks | Offload reduction vs width 1 | Mean cache latency (ticks) | Mean queue time (ticks) |",
             "| ---: | ---: | ---: | ---: | ---: | ---: | ---: |"]
    for row in sorted(rows, key=lambda r: (r["bandwidth"], r["width"])):
        lines.append(f'| {row["bandwidth"]} | {row["width"]} | {row["datapath_cycles"]:,} | {row["offload_ticks"]:,} | '
                     f'{row["offload_reduction_pct"]:.3f}% | {row["dcache_latency_ticks"]:.3f} | {row["dcache_queue_time_ticks"]:.3f} |')
    lines += ["", "Offload ticks sum the reset-to-accelerator-completion and completion-to-host-return segments.",
              "Cache counters come from full-output runs; the host return segment is reported separately in CSV.",
              "Bandwidth is an issue limit, not DRAM bandwidth. Queue capacity remains 32 entries.",
              "Area fields are retained as raw model diagnostics. Fixed CACTI inputs do not model the physical cost",
              "of changing cache ports; do not use this sweep to claim hardware area or energy savings.", ""]
    (cohort / "SUMMARY.md").write_text("\n".join(lines))
    report = dict(points=len(rows), full_accelerator_checks=6, cpu_checks=2,
                  effective_config_comparison="all entries; names/paths normalized; cacheBandwidth varied",
                  shared_traces_verified=True, stage_cycles_agree=True, checksums_agree=True,
                  host_instruction_counts_agree=True)
    (cohort / "validation.json").write_text(json.dumps(report, indent=2) + "\n")
    print("\n".join(lines))


def write_manifest(cohort):
    files = sorted(p for p in cohort.rglob("*") if p.is_file() and "fs" not in p.relative_to(cohort).parts
                   and p.name != "SHA256SUMS")
    (cohort / "SHA256SUMS").write_text("".join(
        "{}  {}\n".format(sha256(path), path.relative_to(cohort)) for path in files))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("cohort", type=Path)
    args = parser.parse_args()
    rows = verify(args.cohort)
    write_summary(args.cohort, rows)
    write_manifest(args.cohort)


if __name__ == "__main__":
    main()
