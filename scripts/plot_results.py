"""Plot the validated single-invocation offload intervals from the CSV."""

import csv
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt


ROOT = Path(__file__).resolve().parents[1]
with (ROOT / "results/validated_summary.csv").open(newline="") as file:
    rows = list(csv.DictReader(file))

sizes = [f"N={row['n']}" for row in rows]
base = [int(row["base_offload_ticks"]) / 1e6 for row in rows]
tiled = [int(row["tiled_offload_ticks"]) / 1e6 for row in rows]
x = range(len(rows))
width = 0.35

fig, ax = plt.subplots(figsize=(6.5, 4.2), layout="constrained")
ax.bar([i - width / 2 for i in x], base, width, label="One-column base", color="#5271a3")
ax.bar([i + width / 2 for i in x], tiled, width, label="Four-column extension", color="#e68a40")
ax.set_xticks(list(x), sizes)
ax.set_ylabel("Offload interval (million gem5 ticks)")
ax.set_ylim(0, max(base) * 1.22)
ax.set_title("Single GEMM invocation: reset to host return")
ax.legend(frameon=False)
ax.spines[["top", "right"]].set_visible(False)
for i, row in enumerate(rows):
    ax.text(
        i,
        max(base[i], tiled[i]) + 0.08,
        f"{float(row['offload_time_reduction_pct']):.1f}% lower",
        ha="center",
        fontsize=9,
    )

target = ROOT / "results/offload_comparison.png"
fig.savefig(target, dpi=180)
print(target)
