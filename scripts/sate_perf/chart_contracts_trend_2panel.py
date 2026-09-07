"""نمودار 8 (نسخه دوپنلی) - همان داده chart_contracts_trend.py، در قالب دو پنل
عمودی (ستون مبلغ در بالا، خط تعداد در پایین) -- مطابق سبک قدیمی
``contracts_2panels.py`` که پیش‌تر برای گزارش نوشته شده بود، این‌بار متصل به
دیتابیس به‌جای Contracts.xlsx.
"""

import math
import os
import sys

import numpy as np
import matplotlib as mpl
import matplotlib.patches as mpatches
from matplotlib.ticker import FuncFormatter, MultipleLocator

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from chart_contracts_trend import fetch_yearly_contracts
from style import (
    CHARTS_DIR, TEXT_COLOR, MUTED_TEXT_COLOR, GRID_COLOR,
    fp, plt, save_fig, to_fa_num,
)

mpl.rcParams["axes.unicode_minus"] = False

AMOUNT_COLOR = "#F97316"
AMOUNT_EDGE_COLOR = "#EA580C"
COUNT_COLOR = "#2563EB"
COUNT_FILL_COLOR = "#93C5FD"
BACKGROUND_COLOR = "#F7F9FC"
PANEL_COLOR = "#FFFFFF"


def calculate_axis_limit(values, step, extra_steps=1):
    max_value = float(np.nanmax(values)) if len(values) else 0
    if max_value <= 0:
        return step
    return math.ceil(max_value / step) * step + extra_steps * step


def main():
    years, counts, amounts = fetch_yearly_contracts(min_year=1398)
    counts = np.array(counts, dtype=float)
    amounts = np.array(amounts, dtype=float)
    x = np.arange(len(years))

    amount_tick_step = 1000
    count_tick_step = 100
    amount_axis_limit = calculate_axis_limit(amounts, amount_tick_step)
    count_axis_limit = calculate_axis_limit(counts, count_tick_step)

    fig, (ax_amount, ax_count) = plt.subplots(
        nrows=2, ncols=1, figsize=(14, 9), dpi=180, sharex=True,
        gridspec_kw={"height_ratios": [2.15, 1.15], "hspace": 0.08},
    )
    fig.patch.set_facecolor(BACKGROUND_COLOR)
    ax_amount.set_facecolor(PANEL_COLOR)
    ax_count.set_facecolor(PANEL_COLOR)
    fig.subplots_adjust(left=0.105, right=0.91, top=0.83, bottom=0.15)

    fig.text(0.5, 0.935, fp("روند مبالغ و تعداد قراردادهای منعقد شده"),
              ha="center", va="center", fontsize=21, fontweight="bold", color=TEXT_COLOR)
    fig.text(0.5, 0.895, fp("مقایسه سالانه مجموع مبالغ قراردادها و تعداد قراردادهای منعقد شده (از ۱۳۹۸)"),
              ha="center", va="center", fontsize=11.5, color=MUTED_TEXT_COLOR)

    # پنل مبلغ
    bars = ax_amount.bar(x, amounts, width=0.52, color=AMOUNT_COLOR,
                         edgecolor=AMOUNT_EDGE_COLOR, linewidth=0.7, zorder=3)
    for bar, amount in zip(bars, amounts):
        ax_amount.annotate(fp(to_fa_num(f"{amount:,.0f}")),
                            xy=(bar.get_x() + bar.get_width() / 2, bar.get_height()),
                            xytext=(0, 7), textcoords="offset points", ha="center", va="bottom",
                            fontsize=10, fontweight="bold", color=TEXT_COLOR, zorder=8)

    ax_amount.set_ylabel(fp("مجموع مبالغ قراردادها\n(میلیارد ریال)"), fontsize=11,
                          color=TEXT_COLOR, labelpad=16)
    ax_amount.set_ylim(0, amount_axis_limit)
    ax_amount.yaxis.set_major_locator(MultipleLocator(amount_tick_step))
    ax_amount.yaxis.set_major_formatter(FuncFormatter(lambda v, _: fp(to_fa_num(f"{v:,.0f}"))))
    ax_amount.tick_params(axis="y", labelsize=9.5, colors=MUTED_TEXT_COLOR)

    # پنل تعداد
    ax_count.plot(x, counts, color=COUNT_COLOR, linewidth=3, marker="o", markersize=8,
                  markerfacecolor="white", markeredgecolor=COUNT_COLOR, markeredgewidth=2, zorder=5)
    ax_count.fill_between(x, counts, 0, color=COUNT_FILL_COLOR, alpha=0.16, zorder=1)

    for i, (xi, count) in enumerate(zip(x, counts)):
        offset_y, va = (10, "bottom") if i % 2 == 0 else (-12, "top")
        ax_count.annotate(fp(to_fa_num(f"{count:,.0f}")), xy=(xi, count),
                           xytext=(0, offset_y), textcoords="offset points",
                           ha="center", va=va, fontsize=9.5, fontweight="bold", color=COUNT_COLOR,
                           zorder=8, bbox=dict(boxstyle="round,pad=0.22", facecolor="white",
                                               edgecolor="none", alpha=0.90))

    ax_count.set_ylabel(fp("تعداد قراردادها"), fontsize=11, color=TEXT_COLOR, labelpad=16)
    ax_count.set_ylim(0, count_axis_limit)
    ax_count.yaxis.set_major_locator(MultipleLocator(count_tick_step))
    ax_count.yaxis.set_major_formatter(FuncFormatter(lambda v, _: fp(to_fa_num(f"{v:,.0f}"))))
    ax_count.tick_params(axis="y", labelsize=9.5, colors=MUTED_TEXT_COLOR)

    ax_count.set_xticks(x)
    ax_count.set_xticklabels([fp(to_fa_num(y)) for y in years], fontsize=10.5, color=TEXT_COLOR)
    ax_count.tick_params(axis="x", length=0, pad=10)
    ax_amount.tick_params(axis="x", bottom=False, labelbottom=False)

    for ax in (ax_amount, ax_count):
        ax.grid(axis="y", color=GRID_COLOR, linewidth=0.85, alpha=0.9, zorder=0)
        ax.set_axisbelow(True)
        for spine in ax.spines.values():
            spine.set_visible(False)

    fig.legend(
        handles=[
            mpatches.Patch(color=AMOUNT_COLOR, label=fp("مجموع مبالغ قراردادها")),
            mpl.lines.Line2D([0], [0], color=COUNT_COLOR, linewidth=3, marker="o",
                              markersize=7, markerfacecolor="white", markeredgecolor=COUNT_COLOR,
                              label=fp("تعداد قراردادها")),
        ],
        loc="upper center", bbox_to_anchor=(0.5, 0.865), ncol=2, frameon=False,
        fontsize=10.5, columnspacing=2.5, handlelength=2.5,
    )

    fig.text(0.5, 0.055, fp(
        "منبع داده: جدول contracts (پایگاه داده ساتع) -- سال معادل شمسی تاریخ قرارداد، از سال ۱۳۹۸. "
        "عدد سال ۱۴۰۵ فقط تا پایان مرداد است."
    ), ha="center", va="center", fontsize=9.5, color=MUTED_TEXT_COLOR)

    save_fig(fig, "chart08_contracts_trend_2panel")


if __name__ == "__main__":
    main()
