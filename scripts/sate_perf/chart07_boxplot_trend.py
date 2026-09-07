# chart07_boxplot_trend.py
import matplotlib.ticker as mticker
from matplotlib.lines import Line2D
from matplotlib.patches import Patch

from chart_config import (
    load_data, fp, fmt_num, to_fa_num, CHARTS_DIR, COLORS, plt
)


df = load_data()

grouped = df.groupby("سال")["اعتبار"]
years = sorted(grouped.groups.keys())
data_per_year = [grouped.get_group(year).to_numpy() for year in years]

positions = list(range(len(years)))

fig, ax = plt.subplots(figsize=(13, 7))

violin_parts = ax.violinplot(
    data_per_year,
    positions=positions,
    widths=0.7,
    showmedians=False,
    showextrema=False,
)
for body in violin_parts["bodies"]:
    body.set_facecolor(COLORS["primary"])
    body.set_alpha(0.25)
    body.set_edgecolor("none")

ax.boxplot(
    data_per_year,
    positions=positions,
    widths=0.35,
    patch_artist=True,
    showfliers=True,
    boxprops={
        "facecolor": COLORS["primary"],
        "alpha": 0.6,
        "linewidth": 1.2,
    },
    medianprops={
        "color": COLORS["danger"],
        "linewidth": 2,
    },
    whiskerprops={
        "color": COLORS["neutral"],
        "linewidth": 1,
    },
    capprops={
        "color": COLORS["neutral"],
        "linewidth": 1,
    },
    flierprops={
        "marker": "o",
        "markerfacecolor": COLORS["secondary"],
        "markersize": 4,
        "alpha": 0.5,
        "linestyle": "none",
    },
)

ax.set_xticks(positions)
ax.set_xticklabels([to_fa_num(year) for year in years])
ax.yaxis.set_major_formatter(
    mticker.FuncFormatter(lambda value, _: fp(fmt_num(value, decimals=0)))
)

ax.set_title(fp("توزیع اعتبارات مشمولین به تفکیک سال"), pad=16)
ax.set_ylabel(fp("اعتبار (میلیارد ریال)"), labelpad=10)
ax.set_xlabel(fp("سال"), labelpad=10)

ax.spines[["top", "right"]].set_visible(False)
ax.grid(axis="y", linestyle="--", alpha=0.3, linewidth=0.7)
ax.set_axisbelow(True)

legend_handles = [
    Patch(
        facecolor=COLORS["primary"],
        alpha=0.4,
        edgecolor="none",
        label=fp("محدوده توزیع"),
    ),
    Line2D(
        [0],
        [0],
        color=COLORS["danger"],
        linewidth=2,
        label=fp("میانه"),
    ),
    Line2D(
        [0],
        [0],
        marker="o",
        color="none",
        markerfacecolor=COLORS["secondary"],
        markersize=4,
        alpha=0.5,
        linestyle="none",
        label=fp("مقادیر پرت"),
    ),
]
ax.legend(handles=legend_handles, loc="best", framealpha=0.85)

fig.tight_layout()

out = CHARTS_DIR / "chart07_boxplot_trend.png"
fig.savefig(out, dpi=150, bbox_inches="tight")
plt.close(fig)
print(f"ذخیره شد: {out}")
