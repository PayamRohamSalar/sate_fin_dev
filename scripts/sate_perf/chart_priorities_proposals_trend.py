"""نمودار 7 - تعداد اولویت‌های ثبت‌شده توسط مشمولین و پیشنهاده‌های ارسالی از سوی دانشگاه‌ها.

Source: ``results/sate_perf/data/demand_proposals.xlsx`` -- a manually staged
file (see its header) because priorities/proposals are not yet modeled in
the database. Swap this loader for a DB query once that data is imported.
"""

import os
import sys

import numpy as np
import pandas as pd
from matplotlib.ticker import FuncFormatter

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from style import (
    COLORS, DATA_DIR, TEXT_COLOR,
    add_source_note, add_title, fp, new_figure, save_fig, style_axes, to_fa_num,
)

DATA_PATH = DATA_DIR / "demand_proposals.xlsx"
COL_YEAR = "سال"
COL_PRIORITIES = "تعداد اولویت‌های ثبت‌شده توسط مشمولین"
COL_PROPOSALS = "تعداد پیشنهاده‌های ارسال‌شده توسط دانشگاه‌ها"


def fetch_series(min_year: int = 1398):
    df = pd.read_excel(DATA_PATH)
    df = df.dropna(subset=[COL_PRIORITIES, COL_PROPOSALS], how="all")
    df = df[df[COL_YEAR] >= min_year]
    df = df.sort_values(COL_YEAR)
    years = df[COL_YEAR].astype(int).tolist()
    priorities = df[COL_PRIORITIES].tolist()
    proposals = df[COL_PROPOSALS].tolist()
    return years, priorities, proposals


def main(min_year: int = 1398, output_name: str = "chart07_priorities_proposals_trend",
          subtitle: str = "به تفکیک سال (از ۱۳۹۸)"):
    years, priorities, proposals = fetch_series(min_year)
    x = np.arange(len(years))

    fig, ax = new_figure(figsize=(13, 7))
    fig.subplots_adjust(left=0.08, right=0.96, top=0.80, bottom=0.14)

    add_title(
        fig,
        "تعداد اولویت‌های ثبت‌شده و پیشنهاده‌های ارسالی در سامانه ساتع",
        subtitle,
    )

    ax.plot(x, priorities, color=COLORS["primary"], linewidth=2.6, marker="o",
            markersize=7, markerfacecolor="white", markeredgecolor=COLORS["primary"],
            markeredgewidth=2, label=fp("تعداد اولویت‌های ثبت‌شده"), zorder=3)
    ax.plot(x, proposals, color=COLORS["secondary"], linewidth=2.6, marker="s",
            markersize=7, markerfacecolor="white", markeredgecolor=COLORS["secondary"],
            markeredgewidth=2, label=fp("تعداد پیشنهاده‌های ارسالی"), zorder=3)

    for xi, p, s in zip(x, priorities, proposals):
        for value, color, offset in ((p, COLORS["primary"], 12), (s, COLORS["secondary"], -18)):
            if pd.notna(value):
                ax.annotate(fp(to_fa_num(f"{int(value):,}")), xy=(xi, value),
                            xytext=(0, offset), textcoords="offset points",
                            ha="center", va="bottom" if offset > 0 else "top",
                            fontsize=8.5, color=color)

    ax.set_xticks(x)
    ax.set_xticklabels([fp(to_fa_num(y)) for y in years], fontsize=11)
    ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: fp(to_fa_num(f"{v:,.0f}"))))
    ax.set_ylabel(fp("تعداد"), fontsize=11, labelpad=14)
    ax.margins(y=0.18)

    style_axes(ax)
    ax.legend(loc="upper left", frameon=False, fontsize=10.5, ncol=2,
              bbox_to_anchor=(0.0, 1.08))

    note = (
        "منبع داده: results/sate_perf/data/demand_proposals.xlsx "
        "(فایل موقت دستی -- تا زمان ورود این داده به پایگاه داده)"
    )
    if years and years[-1] == 1405:
        note += ". عدد سال ۱۴۰۵ فقط تا پایان مرداد است"
    add_source_note(fig, note)

    save_fig(fig, output_name)


if __name__ == "__main__":
    main()
