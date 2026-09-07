"""نمودار جدید - سهم دستگاه‌های اجرایی از فراخوان‌های ثبت‌شده در سامانه (1403-1405).

Source: results/sate_perf/data/All_Demands.xlsx, joined (best-effort,
normalized-name match -- see demand_data.py) to employers.upper_organization.
"""

import os
import sys

import numpy as np
from matplotlib.ticker import FuncFormatter

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from demand_data import COL_APPLICANT, UNMATCHED_LABEL, build_employer_lookup, load_demands, match_agency
from style import (
    CATEGORY_PALETTE, HIGHLIGHT_COLOR, MUTED_TEXT_COLOR, TEXT_COLOR,
    add_source_note, add_title, fp, new_figure, save_fig, style_axes, to_fa_num,
)

TOP_N = 7
MIN_YEAR, MAX_YEAR = 1403, 1405


def main():
    df = load_demands(MIN_YEAR, MAX_YEAR)
    exact_lookup, normalized_lookup = build_employer_lookup()
    df["agency"] = df[COL_APPLICANT].apply(lambda a: match_agency(a, exact_lookup, normalized_lookup))

    total = len(df)
    matched = (df["agency"] != UNMATCHED_LABEL).sum()
    match_rate = matched / total * 100

    counts = df["agency"].value_counts()
    top = counts.head(TOP_N)
    rest = counts.iloc[TOP_N:]
    # Fold the unmatched bucket and the long tail together under "سایر / نامشخص"
    other_total = rest.sum() + (top.pop(UNMATCHED_LABEL) if UNMATCHED_LABEL in top.index else 0)
    if other_total > 0:
        top[UNMATCHED_LABEL] = top.get(UNMATCHED_LABEL, 0) + other_total

    top = top.sort_values(ascending=False)
    labels = top.index.tolist()
    values = top.values
    shares = values / total * 100

    fig, ax = new_figure(figsize=(12.5, 7.5))
    fig.subplots_adjust(left=0.3, right=0.93, top=0.80, bottom=0.14)

    add_title(
        fig,
        f"سهم دستگاه‌های اجرایی از فراخوان‌های ثبت‌شده — {to_fa_num(MIN_YEAR)} تا {to_fa_num(MAX_YEAR)}",
        f"از مجموع {to_fa_num(f'{total:,}')} فراخوان؛ درصد از کل",
    )

    y = np.arange(len(labels))
    colors = []
    for i, label in enumerate(labels):
        if label == UNMATCHED_LABEL:
            colors.append(MUTED_TEXT_COLOR)
        elif i == 0:
            colors.append(HIGHLIGHT_COLOR)
        else:
            colors.append(CATEGORY_PALETTE[i % len(CATEGORY_PALETTE)])

    bars = ax.barh(y, values, color=colors, height=0.62, zorder=3)
    ax.invert_yaxis()

    for bar, value, share in zip(bars, values, shares):
        ax.text(
            bar.get_width() + values.max() * 0.015, bar.get_y() + bar.get_height() / 2,
            fp(f"{to_fa_num(f'{value:,.0f}')} ({to_fa_num(f'{share:.1f}')}٪)"),
            ha="left", va="center", fontsize=10.5, fontweight="bold", color=TEXT_COLOR,
        )

    ax.set_yticks(y)
    ax.set_yticklabels([fp(name) for name in labels], fontsize=11)
    ax.set_xlim(0, values.max() * 1.28)
    ax.xaxis.set_major_formatter(FuncFormatter(lambda v, _: fp(to_fa_num(f"{v:,.0f}"))))
    ax.set_xlabel(fp("تعداد فراخوان"), fontsize=11, labelpad=10)

    style_axes(ax)
    ax.grid(axis="x", color="#E5E7EB", linewidth=0.9, alpha=0.85, zorder=0)
    ax.tick_params(axis="y", length=0)

    add_source_note(
        fig,
        "منبع داده: results/sate_perf/data/All_Demands.xlsx + employers (تطبیق نام به‌صورت تقریبی). "
        f"{to_fa_num(f'{match_rate:.0f}')}٪ فراخوان‌ها به یک دستگاه بالادست مشخص متصل شدند؛ باقی در «سایر / نامشخص».",
    )

    save_fig(fig, "chart11_demand_share_by_agency")


if __name__ == "__main__":
    main()
