# Session summary: environment recovery + Gate 1–3 work (2026-09-26)

This documents a single engineering session's work on this package, picking
up from the state recorded in `docs/VALIDATION.md`'s original entry. It's
written for anyone (the team, an instructor, a future session) who needs to
understand what changed, why, and what's still open — the commit history
has the mechanical detail; this is the narrative.

Commit range: `a1c8fe2` (prior state) → `1cc4c71` (end of this session), all
on `origin/main`. Referenced commits below are all in that range.

## 1. Environment: this server has no Docker

The package's entire build/run pipeline (`scripts/setup.sh`, `scripts/run.sh`)
is hard-wired to Docker: a pinned image (`xyzsam/gem5-aladdin` by SHA-256
digest), `docker pull` / `docker volume create` / `docker run`. The shared
Linux server this session ran on (`ece-lnx-10`) has no Docker daemon, no
Docker binary, and no systemd unit for it — a hard blocker for any of Gates
1–4 before anything else.

**Fix: rootless Podman**, already installed on the machine, used as a
drop-in replacement with zero changes to this repo's own scripts. Three
one-time, user-space environment changes (all outside this repo, in
`~/.config/containers/` and `~/bin/`) made it work:

1. Relocated Podman's overlay storage off the NFS-backed home directory
   onto local disk (`/var/tmp/...`) — the NFS mount doesn't support the
   xattrs overlay storage needs.
2. Set `ignore_chown_errors = "true"` for the same storage driver — this
   account has no `/etc/subuid`/`/etc/subgid` ranges, so rootless Podman
   can't remap non-root file ownership inside a real multi-UID image
   without this flag.
3. Restricted `unqualified-search-registries` to `docker.io` (skips Red Hat's
   registries, which don't host this image, before falling through).
4. A one-line `docker` → `podman` shim on `PATH`, since the scripts only
   check `command -v docker` and use basic `pull`/`volume create`/`run` —
   Podman's CLI covers exactly that.

Verified end-to-end: `build/X86/gem5.opt` compiles and runs correctly
through this path, matching the pinned image/digest and patched Aladdin
submodule the repo specifies.

**Push access**: `origin` is the upstream author's repo
(`yasirmahmud/coherent-gemm-accelerator`), not a fork; this session's SSH
key authenticates as a different GitHub account. The user confirmed
collaborator access before any push was attempted.

## 2. Gate 1 — dynamic input correctness: fixed (`c854ea2`)

**Prior state**: the repeated-input diagnostic (`results/diagnostics/repeated_input_n24/`)
showed 19/24 full-output mismatches on both kernels when the CPU modified
the input matrix between two accelerator invocations. This was the
project's central open problem — nothing about "dynamic" coherence could be
claimed until it was understood.

**Root cause** (not a coherence bug): Aladdin replays a pre-recorded
instruction trace rather than re-executing C code. The trace-generation
build path (`LLVM_TRACE`, in both `benchmarks/*/*.c`) called `gemm_kernel()`
exactly once regardless of `REPS`, while the actual simulated harness
(`GEM5_HARNESS`) looped `REPS` times against CPU-modified input. On
invocation 2+, Aladdin replayed a trace with nothing left in it ("Reached
end of trace." — no new DDDG generated), so the accelerator did zero real
work; the diagnostic was silently comparing invocation-1's stale output
against a fresh CPU reference computed on the *updated* input.

Verified arithmetically before touching any code: with N=24 and a single
`A[1] += 1` mutation, only row 0 of the base kernel's output depends on that
element, and of that row's 24 entries, exactly 5 have a zero multiplier from
B — leaving exactly 19 differing entries, matching the observed mismatch
count precisely.

**Fix**: made the `LLVM_TRACE` path loop `REPS` times with the same input
mutation as the harness, in both `benchmarks/gemm_acp_pilot/gemm_acp_pilot.c`
and `benchmarks/gemm_tiled4/gemm_tiled4.c`. Verified via a REPS=2, N=24
repro for both kernels: invocation 2 now produces a real DDDG (matching
invocation 1's node count) and `GEMM passed: 0 mismatches`
(`results/diagnostics/repeated_input_n24_fixed/`, kept alongside the
original failing logs as before/after evidence).

**No regression**: the fix is a no-op when `REPS=1` (every published result).
Confirmed by rebuilding the standard N=24 `full` case post-fix and diffing
every simulated stat (excluding host wall-clock fields) against a pre-fix
rebuild on the same host — bit-identical.

**Scope note** (in `docs/NEXT_STEPS.md`): this validates input changing
*between* discrete accelerator calls with a full retrace per call. It does
not validate input changing *mid-invocation*, or a design where per-call
retracing is impractical — worth stating explicitly in any report rather
than treating "dynamic input" as fully solved in general.

## 3. Gate 2 — hardware cost: mostly resolved (`8b49795`, `33eaa93`)

**"N=24 area reports varied across otherwise matched reruns" — audited and
found false as originally stated.** Every true same-stage rerun of base_n24
on record (`fair_results`, `invocation_results`, the pre-fix diagnostic, and
an independent from-scratch Podman rebuild on a different host) reports
identical area (Total Area 1.40134e+06 µm², FU Area 598362 µm²). The only
number that ever differed was `roi_results/base_n24`, which runs a
genuinely different (shorter, ROI-bounded) trace and a checksum-only check —
comparing it to `fair`/`invocation` was never a fair same-config rerun.
Same-stage, single-invocation (REPS=1) area is repeatable, including
cross-host.

**New, separate, still-open finding**: using the Gate 1 fix (which made a
real second invocation possible for the first time), invocation 2 of the
same kernel in the same gem5 run reports a substantially different FU Area
than invocation 1 — base_n24: 598362→832260 µm² (+39%); tiled4_n24:
593769→695405 µm² (+17%) — while MEM Area stays exactly constant. Traced one
level into Aladdin's source (`src/aladdin/common/BaseDatapath.cpp`): the
resource-peak accounting (`func_max_activity`) is freshly built on every
call, ruling out a stale-accumulator bug — the *scheduling result itself*
genuinely differs for an isomorphic DDDG. Leading hypothesis, not yet
confirmed: Aladdin's dynamic trace/DDDG node numbering runs continuously
across the whole run rather than resetting per invocation, so invocation 2's
nodes carry different absolute IDs than invocation 1's — if the scheduler's
tie-breaking or partition/bank assignment depends on absolute node ID, that
alone could produce a different valid schedule with a different concurrency
peak. Doesn't affect any published REPS=1 number; blocks any future
repeated-invocation/"dynamic" area claim until resolved.

## 4. Gate 3 — broader experiment: started (`0d8b58d` … `1cc4c71`)

Two independent dimensions explored, both built on new reusable tooling
(`scripts/explore_size.py`, `scripts/plot_results_exploratory.py`) that
mirrors `scripts/summarize.py`'s exact verification logic for
not-yet-validated sizes, kept completely separate from the validated
pipeline (`results/validated_summary.csv`, `scripts/summarize.py`,
`scripts/plot_results.py` are all untouched).

**Size sweep** (N=8, 16, added; N=24, 32 already validated): offload-interval
reduction is cleanly monotonic across all four sizes (1.9% → 9.4% → 11.9% →
22.6%), but cycle reduction and CPU-relative speedup are **not** monotonic —
N=16 beats N=24 on raw cycle reduction while losing on the CPU-relative
metric, and N=8 is weak-to-negative on every metric (whole-program reduction
is exactly 0.00%, tick-for-tick identical between kernels; area even
decreases slightly for the four-column variant). Most plausible explanation:
fixed per-invocation overhead dominates when there's little real work to
amortize it over. **This means "the four-column extension wins" cannot be
stated as a general claim — it's size-dependent, and the weak/negative
result at small N should be reported, not dropped.**

**Tile-width ablation** (new `benchmarks/gemm_tiled2/`, a 2-column variant;
compared against the existing 1-column base and 4-column extension, all at
fixed N=24 to isolate tile width from problem-size effects): the benefit
scales cleanly and monotonically with tile width, with textbook diminishing
returns per doubling (0% → 13.43% → 21.97% cycle reduction). Area is flat to
slightly negative at this N (0.00%, then −0.33%), sharply unlike N=32's
27.7% area growth for the identical tile-width-4 kernel — **suggesting area
cost in this design tracks problem size far more than tile width.**
Queue/cache traffic data (explicitly requested by Gate 3): raw access counts
(dcache loads/stores, TLB hits/misses) are exactly identical across all
three tile widths — same total data volume moved — but mean dcache access
latency drops monotonically with tile width (27,518.8 → 22,432.1 → 19,915.2
ticks), tracking the same diminishing-returns shape as cycle/offload
reduction. Reads as: reuse reduces per-access contention, not data volume.

Full detail, tables, and formulas for all of the above are in
`docs/RESULTS.md`; gate-by-gate status is in `docs/NEXT_STEPS.md`.

## 5. What's still open

- **Gate 2**: the multi-invocation FU Area mechanism (node-numbering
  hypothesis, not yet confirmed against Aladdin's scheduler source).
- **Gate 3**: tile-width ablation at other N (does N=8's inversion also show
  up in tile-width scaling at small N?), tile-width 8, larger N (40+), a
  representative inference layer (per the README's own suggestions).
- **Gate 4**: entirely untouched. Needs the instructor's sign-off on scope
  and the actual Canvas deadline — neither is something a coding session can
  determine; both need to come from the user/course directly.

## 6. Honesty note

Every finding above that turned out negative or mixed (N=8's weak results,
the FU Area mechanism not being fully nailed down, the original Gate 2 claim
being wrong) is reported as such rather than smoothed over, per this
project's own stated principle (`docs/COURSE_ELIGIBILITY.md`: "Negative or
mixed results should be reported rather than discarded"). Team members
should still read and be able to defend the actual mechanism behind each
finding — this file and the docs it points to are meant to make that easier,
not to substitute for it.
