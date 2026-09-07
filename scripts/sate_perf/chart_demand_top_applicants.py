"""نمودار جدید - مشمولانی که بیشترین تعداد فراخوان/تقاضا را در سامانه ثبت کرده‌اند (1403-1405).

Source: results/sate_perf/data/All_Demands.xlsx (خروجی خام سامانه؛ نگاه کنید
demand_data.py برای جزئیات).
"""

import os
import sys

import numpy as np
from matplotlib.ticker import FuncFormatter

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from demand_data import COL_APPLICANT, load_demands
from style import (
    CATEGORY_PALETTE, HIGHLIGHT_COLOR, TEXT_COLOR,
    add_source_note, add_title, fp, new_figure, save_fig, style_axes, to_fa_num,
)

TOP_N = 10
MIN_YEAR, MAX_YEAR = 1403, 1405


def main():
    df = load_demands(MIN_YEAR, MAX_YEAR)
    total = len(df)

    counts = df[COL_APPLICANT].value_counts()
    top = counts.head(TOP_N)

    labels = top.index.tolist()
    values = top.values
    shares = values / total * 100

    fig, ax = new_figure(figsize=(13, 8))
    fig.subplots_adjust(left=0.34, right=0.92, top=0.80, bottom=0.11)

    add_title(
        fig,
        f"مشمولان دارای بیشترین تعداد فراخوان ثبت‌شده — {to_fa_num(MIN_YEAR)} تا {to_fa_num(MAX_YEAR)}",
        f"از مجموع {to_fa_num(f'{total:,}')} فراخوان ثبت‌شده در این بازه",
    )

    y = np.arange(len(labels))
    colors = [HIGHLIGHT_COLOR if i == 0 else CATEGORY_PALETTE[i % len(CATEGORY_PALETTE)]
              for i in range(len(labels))]

    bars = ax.barh(y, values, color=colors, height=0.62, zorder=3)
    ax.invert_yaxis()

    for bar, value, share in zip(bars, values, shares):
        ax.text(
            bar.get_width() + values.max() * 0.015, bar.get_y() + bar.get_height() / 2,
            fp(f"{to_fa_num(f'{value:,.0f}')} ({to_fa_num(f'{share:.1f}')}٪)"),
            ha="left", va="center", fontsize=10, fontweight="bold", color=TEXT_COLOR,
        )

    ax.set_yticks(y)
    ax.set_yticklabels([fp(name) for name in labels], fontsize=10.5)
    ax.set_xlim(0, values.max() * 1.3)
    ax.xaxis.set_major_formatter(FuncFormatter(lambda v, _: fp(to_fa_num(f"{v:,.0f}"))))
    ax.set_xlabel(fp("تعداد فراخوان ثبت‌شده"), fontsize=11, labelpad=10)

    style_axes(ax)
    ax.grid(axis="x", color="#E5E7EB", linewidth=0.9, alpha=0.85, zorder=0)
    ax.tick_params(axis="y", length=0)

    add_source_note(fig, "منبع داده: results/sate_perf/data/All_Demands.xlsx (خروجی خام سامانه ساتع)")

    save_fig(fig, "chart10_demand_top_applicants")


if __name__ == "__main__":
    main()
