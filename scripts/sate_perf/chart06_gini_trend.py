# chart06_gini_trend.py
import numpy as np
import matplotlib.ticker as mticker
from chart_config import (
    load_data, fp, fmt_num, to_fa_num, CHARTS_DIR, COLORS, plt
)


def calculate_gini(data):
    """Calculate the Gini coefficient for a one-dimensional sequence."""
    values = np.asarray(data, dtype=float)
    values = values[np.isfinite(values)]
    values = values[values >= 0]

    if len(values) == 0:
        return np.nan

    total = values.sum()
    if total == 0:
        return 0.0

    sorted_values = np.sort(values)
    n = len(sorted_values)
    index = np.arange(1, n + 1)
    return np.sum((2 * index - n - 1) * sorted_values) / (n * total)


df = load_data()

# محاسبه ضریب جینی برای هر سال
gini_by_year = df.groupby("سال")["اعتبار"].apply(calculate_gini).sort_index()

# محور سال پیوسته است، اما مقدار سال ۱۴۰۳ عمداً خالی می‌ماند.
years = list(range(int(gini_by_year.index.min()), int(gini_by_year.index.max()) + 1))
gini_series = gini_by_year.reindex(years)

x = np.arange(len(years))
y = gini_series.to_numpy(dtype=float)
valid = np.isfinite(y)

fig, ax = plt.subplots(figsize=(10, 6))

ax.plot(
    x,
    y,
    color=COLORS["primary"],
    linewidth=2.5,
    marker="o",
    markersize=7,
    label=fp("ضریب جینی"),
    zorder=3,
)
ax.fill_between(
    x,
    y,
    0,
    where=valid,
    color=COLORS["primary"],
    alpha=0.1,
    interpolate=True,
)

base_year = 1398
base_gini = gini_by_year.get(base_year, np.nan)
if np.isfinite(base_gini):
    ax.axhline(
        base_gini,
        color=COLORS["secondary"],
        linewidth=1.5,
        linestyle="--",
        alpha=0.85,
        label=fp(f"سال پایه {to_fa_num(base_year)}"),
    )

    ax.annotate(
        fp(f"{fmt_num(base_gini, 3)}"),
        xy=(x[-1], base_gini),
        xytext=(8, 0),
        textcoords="offset points",
        ha="left",
        va="center",
        fontsize=9,
        color=COLORS["secondary"],
    )

for xi, yi in zip(x[valid], y[valid]):
    ax.annotate(
        fp(to_fa_num(f"{yi:.3f}")),
        xy=(xi, yi),
        xytext=(0, 10),
        textcoords="offset points",
        ha="center",
        va="bottom",
        fontsize=9,
        color=COLORS["primary"],
    )

if 1403 in years:
    gap_x = years.index(1403)
    ax.axvline(gap_x, color=COLORS["neutral"], linewidth=1, linestyle=":", alpha=0.5)
    y_min, y_max = ax.get_ylim()
    ax.text(
        gap_x,
        y_min + (y_max - y_min) * 0.08,
        fp("حذف بندی قانونی"),
        ha="center",
        va="bottom",
        fontsize=9,
        color=COLORS["neutral"],
    )

ax.set_xticks(x)
ax.set_xticklabels([to_fa_num(year) for year in years])
ax.yaxis.set_major_formatter(
    mticker.FuncFormatter(lambda value, _: fp(to_fa_num(f"{value:.2f}")))
)

ax.set_title(fp("روند ضریب جینی توزیع اعتبارات (شاخص نابرابری)"), pad=16)
ax.set_xlabel(fp("سال"), labelpad=10)
ax.set_ylabel(fp("ضریب جینی"), labelpad=10)

ax.spines[["top", "right"]].set_visible(False)
ax.grid(axis="y", linestyle="--", alpha=0.3)
ax.set_axisbelow(True)
ax.margins(x=0.06, y=0.18)
ax.legend(loc="best", framealpha=0.85)

fig.tight_layout()

out = CHARTS_DIR / "chart06_gini_trend.png"
fig.savefig(out, dpi=150, bbox_inches="tight")
plt.close(fig)
print(f"ذخیره شد: {out}")
