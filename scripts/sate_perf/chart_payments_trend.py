"""نمودار 9 - مجموع مبالغ پرداخت‌شده از طریق سامانه ساتع به تفکیک سال پرداخت.

Source: ``payments`` table, grouped by ``payment_year`` (سال پرداخت --
cash-flow year), matching the field the project's own regulatory report
(scripts/generate_regulatory_report_1404.py) uses for the same concept.

The ``payments`` table only has records from fiscal year 1403 onward.
Payam supplied the pre-DB yearly totals for 1398-1402 (file ``Payments.xlsx``,
2026-09-07); ``LEGACY_PAYMENT_BILLION_RIAL`` below is a manual fallback for
exactly those years, already in میلیارد ریال. Delete it once 1398-1402
payments are itemized in the database.
"""

import os
import sys

import numpy as np
from matplotlib.ticker import FuncFormatter

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from core.database import SessionLocal
from models.contract import Contract  # noqa: F401 -- registers ORM relationship target
from models.payment import Payment
from sqlalchemy import func
from style import (
    COLORS, HIGHLIGHT_COLOR, TEXT_COLOR,
    add_source_note, add_title, fp, new_figure, rial_to_billion,
    save_fig, style_axes, to_fa_num,
)

LEGACY_PAYMENT_BILLION_RIAL = {
    1398: 379.117971,
    1399: 2268.173436,
    1400: 1909.041879,
    1401: 2028.0,
    1402: 545.0,
}


def fetch_yearly_totals(min_year: int = 1398):
    db = SessionLocal()
    try:
        rows = (
            db.query(Payment.payment_year, func.sum(Payment.amount))
            .filter(Payment.is_deleted == False, Payment.payment_year.isnot(None))  # noqa: E712
            .group_by(Payment.payment_year)
            .all()
        )
    finally:
        db.close()
    totals = {int(y): rial_to_billion(total) for y, total in rows if total}
    for year, value in LEGACY_PAYMENT_BILLION_RIAL.items():
        totals.setdefault(year, value)
    return [(y, totals[y]) for y in sorted(totals) if y >= min_year]


def main():
    data = fetch_yearly_totals(min_year=1398)
    years = [y for y, _ in data]
    amounts = np.array([v for _, v in data])
    x = np.arange(len(years))

    fig, ax = new_figure(figsize=(13, 7.5))
    fig.subplots_adjust(left=0.09, right=0.95, top=0.80, bottom=0.16)

    add_title(fig, "روند مبالغ پرداختی سالانه از طریق سامانه ساتع", "بر حسب میلیارد ریال")

    bars = ax.bar(x, amounts, width=0.5, color=COLORS["accent"], zorder=3)
    ax.plot(x, amounts, color="#0F172A", linewidth=2.6, marker="o", markersize=7,
            markerfacecolor="white", markeredgecolor="#0F172A", markeredgewidth=2, zorder=6)

    max_amount = amounts.max() if len(amounts) else 0
    for bar, value in zip(bars, amounts):
        ax.annotate(fp(to_fa_num(f"{value:,.0f}")), xy=(bar.get_x() + bar.get_width() / 2, value),
                    xytext=(0, 8), textcoords="offset points", ha="center", va="bottom",
                    fontsize=11, fontweight="bold", color=TEXT_COLOR, zorder=8)

    if len(amounts):
        max_i = int(np.argmax(amounts))
        ax.scatter(x[max_i], amounts[max_i], s=110, color=HIGHLIGHT_COLOR,
                   edgecolor="white", linewidth=1.8, zorder=7)

    ax.set_xticks(x)
    ax.set_xticklabels([fp(to_fa_num(y)) for y in years], fontsize=11)
    ax.set_ylim(0, max_amount * 1.25 if max_amount else 1)
    ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: fp(to_fa_num(f"{v:,.0f}"))))
    ax.set_ylabel(fp("میلیارد ریال"), fontsize=11, labelpad=14)

    style_axes(ax)

    note = (
        "منبع داده: جدول payments (پایگاه داده ساتع) از سال ۱۴۰۳ به بعد؛ "
        "سال‌های ۱۳۹۸ تا ۱۴۰۲ از گزارش تطبیقی قبلی (هنوز در پایگاه داده ثبت نشده)"
    )
    if years and max(years) == 1405:
        note += ". عدد سال ۱۴۰۵ فقط تا پایان مرداد است"
    add_source_note(fig, note)

    save_fig(fig, "chart09_payments_trend")


if __name__ == "__main__":
    main()
