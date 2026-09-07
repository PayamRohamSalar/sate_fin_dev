"""نمودار 8 - تعداد و مجموع مبالغ قراردادهای منعقد شده در سامانه ساتع به تفکیک سال.

Source: ``contracts`` table. ``contract_date`` is stored as a Gregorian date
(converted from the Jalali value entered at import time -- see
``core.date_helper``); it is converted back to its Jalali year here since
the report groups by fiscal (Persian-calendar) year, not calendar year.
"""

import os
import sys
from collections import defaultdict

import numpy as np
from matplotlib.ticker import FuncFormatter, MultipleLocator

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from core.database import SessionLocal
from core.date_helper import to_jalali_date
from models.employer import Employer  # noqa: F401 -- registers ORM relationship target
from models.university import University  # noqa: F401
from models.researchers import Researcher  # noqa: F401
from models.contract import Contract
from style import (
    COLORS, TEXT_COLOR,
    add_source_note, add_title, fp, new_figure, rial_to_billion,
    save_fig, style_axes, to_fa_num,
)


def fetch_yearly_contracts(min_year: int = 1398):
    db = SessionLocal()
    try:
        rows = (
            db.query(Contract.contract_date, Contract.total_amount)
            .filter(Contract.is_deleted == False, Contract.contract_date.isnot(None))  # noqa: E712
            .all()
        )
    finally:
        db.close()

    counts = defaultdict(int)
    amounts = defaultdict(float)
    for contract_date, total_amount in rows:
        year = to_jalali_date(contract_date).year
        if year < min_year:
            continue
        counts[year] += 1
        amounts[year] += rial_to_billion(total_amount)

    years = sorted(counts)
    return years, [counts[y] for y in years], [amounts[y] for y in years]


def main():
    years, counts, amounts = fetch_yearly_contracts(min_year=1398)
    x = np.arange(len(years))

    fig, ax = new_figure(figsize=(13, 7.5))
    ax2 = ax.twinx()
    fig.subplots_adjust(left=0.08, right=0.9, top=0.80, bottom=0.14)

    add_title(
        fig,
        "روند تعداد و مبالغ قراردادهای منعقدشده در سامانه ساتع",
        "بر حسب میلیارد ریال (ستون) و تعداد قرارداد (خط)",
    )

    bars = ax.bar(x, amounts, width=0.5, color=COLORS["secondary"], zorder=3,
                  label=fp("مجموع مبالغ قراردادها"))
    ax2.plot(x, counts, color=COLORS["primary"], linewidth=2.8, marker="o",
             markersize=7, markerfacecolor="white", markeredgecolor=COLORS["primary"],
             markeredgewidth=2, zorder=6, label=fp("تعداد قراردادها"))

    max_amount = max(amounts) if amounts else 0
    for bar, value in zip(bars, amounts):
        ax.text(bar.get_x() + bar.get_width() / 2, value + max_amount * 0.02,
                fp(to_fa_num(f"{value:,.0f}")), ha="center", va="bottom",
                fontsize=10, fontweight="bold", color=TEXT_COLOR, zorder=8)

    ax.set_xticks(x)
    ax.set_xticklabels([fp(to_fa_num(y)) for y in years], fontsize=11)
    ax.set_ylim(0, max_amount * 1.2 if max_amount else 1)
    ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: fp(to_fa_num(f"{v:,.0f}"))))
    ax.set_ylabel(fp("میلیارد ریال"), fontsize=11, labelpad=14)

    max_count = max(counts) if counts else 0
    ax2.set_ylim(0, max_count * 1.2 if max_count else 1)
    ax2.yaxis.set_major_formatter(FuncFormatter(lambda v, _: fp(to_fa_num(f"{v:,.0f}"))))
    ax2.set_ylabel(fp("تعداد قراردادها"), fontsize=11, labelpad=16)
    for spine in ax2.spines.values():
        spine.set_visible(False)

    style_axes(ax)

    handles = [bars, ax2.lines[0]]
    labels = [fp("مجموع مبالغ قراردادها"), fp("تعداد قراردادها")]
    ax.legend(handles, labels, loc="upper left", frameon=False, fontsize=10.5, ncol=2,
              bbox_to_anchor=(0.0, 1.08))

    add_source_note(
        fig,
        "منبع داده: جدول contracts (پایگاه داده ساتع) -- سال معادل شمسی تاریخ قرارداد، از سال ۱۳۹۸. "
        "عدد سال ۱۴۰۵ فقط تا پایان مرداد است.",
    )

    save_fig(fig, "chart08_contracts_trend")


if __name__ == "__main__":
    main()
