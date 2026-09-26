"""Plot offload intervals for validated sizes plus exploratory Gate 3 sizes.

Reads results/validated_summary.csv (N=24, N=32) and, if present,
results/exploratory_summary.csv (any additional sizes from
scripts/explore_size.py) and plots them together, sorted by N. Output is
kept separate from scripts/plot_results.py's results/offload_comparison.png
(which stays validated-only, unmodified) so the two are never confused.
"""

import csv
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]

rows = []
with (ROOT / "results/validated_summary.csv").open(newline="") as file:
    rows.extend(csv.DictReader(file))

exploratory_path = ROOT / "results/exploratory_summary.csv"
if exploratory_path.exists():
    with exploratory_path.open(newline="") as file:
        rows.extend(csv.DictReader(file))

rows.sort(key=lambda row: int(row["n"]))

sizes = [f"N={row['n']}" for row in rows]
base = [int(row["base_offload_ticks"]) / 1e6 for row in rows]
tiled = [int(row["tiled_offload_ticks"]) / 1e6 for row in rows]
x = range(len(rows))
width = 0.35

fig, ax = plt.subplots(figsize=(7.5, 4.2), layout="constrained")
ax.bar([i - width / 2 for i in x], base, width, label="One-column base", color="#5271a3")
ax.bar([i + width / 2 for i in x], tiled, width, label="Four-column extension", color="#e68a40")
ax.set_xticks(list(x), sizes)
ax.set_ylabel("Offload interval (million gem5 ticks)")
ax.set_ylim(0, max(base) * 1.22)
ax.set_title("Single GEMM invocation: reset to host return\n(includes exploratory Gate 3 sizes, not just the validated set)")
ax.legend(frameon=False)
ax.spines[["top", "right"]].set_visible(False)
for i, row in enumerate(rows):
    pct = float(row["offload_time_reduction_pct"])
    label = f"{pct:.1f}% lower" if pct >= 0 else f"{-pct:.1f}% higher"
    ax.text(
        i,
        max(base[i], tiled[i]) + 0.08,
        label,
        ha="center",
        fontsize=9,
    )

target = ROOT / "results/offload_comparison_exploratory.png"
fig.savefig(target, dpi=180)
print(target)
