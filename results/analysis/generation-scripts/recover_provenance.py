"""Inventory main width cohorts and recover local traces only by historical hash.

Candidate work-directory sources/binaries/configs are kept as recovery records;
they do not establish missing stage-specific historical identities.
"""
import csv
import gzip
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / '.artifacts/source'
OUT = ROOT / 'results/provenance/historical_20260930'
RECOVERED = ROOT / 'results/reproductions/ece-lnx-10_2026-09-30'


def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    rows = []
    simulator = SOURCE / 'build/X86/gem5.opt'
    if simulator.exists():
        (OUT / 'current-simulator.sha256').write_text(digest(simulator) + '  local-source/build/X86/gem5.opt\n')
    for n in (24, 32):
        cohort = ROOT / 'results' if n == 24 else RECOVERED
        for variant in ('base', 'tiled2', 'tiled4'):
            name = f'{variant}_n{n}'
            bench = 'gemm_acp_pilot' if variant == 'base' else f'gemm_{variant}'
            point = OUT / name
            point.mkdir(exist_ok=True)
            work = SOURCE / 'src/aladdin/integration-test/with-cpu' / f'package_{name}'
            historical_hash = RECOVERED / f'{name}_trace.sha256'
            trace = work / 'dynamic_trace.gz'
            trace_status = 'missing'
            if n == 32 and historical_hash.exists() and trace.exists():
                expected = historical_hash.read_text().split()[0]
                if digest(trace) == expected:
                    (point / 'dynamic_trace.gz').write_bytes(trace.read_bytes())
                    (point / 'trace.sha256').write_text(f'{expected}  dynamic_trace.gz\n')
                    with gzip.open(trace, 'rb') as f:
                        h = hashlib.sha256()
                        for block in iter(lambda: f.read(1024 * 1024), b''):
                            h.update(block)
                    (point / 'logical-trace.sha256').write_text(h.hexdigest() + '\n')
                    trace_status = 'recovered; historical compressed hash matches; logical hash recomputed'
                else:
                    trace_status = 'missing; local candidate does not match historical hash'
            candidate = []
            if work.exists():
                for filename in (f'{bench}.c', f'{bench}-gem5', f'{bench}-gem5-accel',
                                 'gem5_cache.cfg' if variant == 'base' else 'gem5.cfg',
                                 'gemm_cache_pilot.cfg' if variant == 'base' else f'{bench}.cfg', 'trace-build.log'):
                    p = work / filename
                    if p.exists():
                        (point / ('candidate-' + filename)).write_bytes(p.read_bytes())
                        candidate.append(dict(name=filename, sha256=digest(p)))
                (point / 'candidate-identities.json').write_text(json.dumps(candidate, indent=2) + '\n')
            counts = {kind: len(list(cohort.glob(f'{kind}/{name}/m5out-*/config.ini')))
                      for kind in ('fair_results', 'roi_results', 'invocation_results')}
            logs = sum(len(list(cohort.glob(f'{kind}/{name}/gem5-*.log')))
                       for kind in counts)
            rows.append(dict(n=n, width={'base':1,'tiled2':2,'tiled4':4}[variant],
                cohort='published' if n == 24 else 'ece-lnx-10_2026-09-30',
                trace=trace_status,
                stage_source_identity='missing; candidates are not historical identity proof',
                simulator_identity='missing exact published identity' if n == 24 else 'historical source-record hash malformed (62 hex digits); current candidate fingerprint retained',
                guest_binary_identity='missing stage hashes; candidates retained where available',
                effective_configs=json.dumps(counts, sort_keys=True), stage_logs=logs,
                cacti='missing historical inputs; current copies cannot recreate identity',
                commands='runner records available' if n == 32 else 'documented runners; exact per-stage commands missing'))
    with (OUT / 'inventory.csv').open('w', newline='') as f:
        writer=csv.DictWriter(f, fieldnames=rows[0].keys(), lineterminator='\n')
        writer.writeheader(); writer.writerows(rows)
    (OUT / 'SHA256SUMS').write_text(''.join(f'{digest(p)}  {p.relative_to(OUT)}\n'
        for p in sorted(OUT.rglob('*')) if p.is_file() and p.name != 'SHA256SUMS'))
    print(OUT / 'inventory.csv')


if __name__ == '__main__':
    main()
