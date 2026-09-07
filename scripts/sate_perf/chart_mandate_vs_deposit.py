"""نمودار 5 - مجموع اعتبار تکلیفی مشمولین به همراه میزان اعتبار واریز شده به خزانه.

Sources: ``annual_mandates`` (SUM per fiscal_year) and ``deposit_receipts``
(SUM per fiscal_year) -- two independent tables, merged on fiscal_year.

``deposit_receipts`` only has itemized (per-employer) rows from fiscal year
1402 onward -- 1398-1401 were never entered at that grain. Payam supplied
the pre-DB yearly totals for those years (reconciliation file
``تکلیفی_واریزی.xlsx``, 2026-09-07); ``LEGACY_DEPOSIT_BILLION_RIAL`` below
is a manual fallback for exactly those years, already in میلیارد ریال.
Once 1398-1401 deposits are itemized in the database, delete this fallback.
"""

import os
import sys

import numpy as np
from matplotlib.ticker import FuncFormatter
from sqlalchemy import func

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from core.database import SessionLocal
from models.employer import Employer  # noqa: F401 -- registers ORM relationship target
from models.deposits import AnnualMandate, DepositReceipt
from style import (
    COLORS, TEXT_COLOR, MUTED_TEXT_COLOR,
    add_source_note, add_title, fp, new_figure, rial_to_billion,
    save_fig, style_axes, to_fa_num,
)


LEGACY_DEPOSIT_BILLION_RIAL = {
    1398: 1402,
    1399: 1803,
    1400: 2175,
    1401: 1650,
}


def fetch_series():
    db = SessionLocal()
    try:
        mandated = dict(
            db.query(AnnualMandate.fiscal_year, func.sum(AnnualMandate.mandated_amount))
            .filter(AnnualMandate.is_deleted == False)  # noqa: E712
            .group_by(AnnualMandate.fiscal_year)
            .all()
        )
        deposited = dict(
            db.query(DepositReceipt.fiscal_year, func.sum(DepositReceipt.deposit_amount))
            .filter(DepositReceipt.is_deleted == False)  # noqa: E712
            .group_by(DepositReceipt.fiscal_year)
            .all()
        )
    finally:
        db.close()
    deposited_billion = {int(y): rial_to_billion(v or 0) for y, v in deposited.items()}
    for year, value in LEGACY_DEPOSIT_BILLION_RIAL.items():
        deposited_billion.setdefault(year, value)

    years = sorted(set(mandated) | set(deposited_billion))
    mandated_series = [rial_to_billion(mandated.get(y, 0) or 0) for y in years]
    deposited_series = [deposited_billion.get(y, 0) for y in years]
    return [int(y) for y in years], mandated_series, deposited_series


def main():
    years, mandated, deposited = fetch_series()
    x = np.arange(len(years))
    width = 0.36

    fig, ax = new_figure(figsize=(13, 7.5))
    fig.subplots_adjust(left=0.08, right=0.96, top=0.80, bottom=0.14)

    add_title(
        fig,
        "اعتبار تکلیفی مشمولین در برابر اعتبار واریز شده به خزانه",
        "بر حسب میلیارد ریال",
    )

    bars1 = ax.bar(x - width / 2, mandated, width=width, color=COLORS["primary"],
                    label=fp("اعتبار تکلیفی"), zorder=3)
    bars2 = ax.bar(x + width / 2, deposited, width=width, color=COLORS["accent"],
                    label=fp("اعتبار واریز شده"), zorder=3)

    for bars in (bars1, bars2):
        for bar in bars:
            h = bar.get_height()
            if h <= 0:
                continue
            ax.annotate(fp(to_fa_num(f"{h:,.0f}")), xy=(bar.get_x() + bar.get_width() / 2, h),
                        xytext=(0, 6), textcoords="offset points", ha="center", va="bottom",
                        fontsize=8.5, color=TEXT_COLOR)

    ax.set_xticks(x)
    ax.set_xticklabels([fp(to_fa_num(y)) for y in years], fontsize=11)
    ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: fp(to_fa_num(f"{v:,.0f}"))))
    ax.set_ylabel(fp("میلیارد ریال"), fontsize=11, labelpad=14)
    ax.margins(y=0.15)

    style_axes(ax)
    ax.legend(loc="upper left", frameon=False, fontsize=10.5, ncol=2,
              bbox_to_anchor=(0.0, 1.08))

    add_source_note(
        fig,
        "منبع داده: annual_mandates و deposit_receipts (پایگاه داده ساتع)؛ "
        "واریزی سال‌های ۱۳۹۸ تا ۱۴۰۱ از گزارش تطبیقی قبلی (هنوز در پایگاه داده ثبت نشده). "
        "عدد واریزی سال ۱۴۰۵ فقط تا پایان مرداد است و با اعتبار تکلیفی کل‌سال قابل مقایسه مستقیم نیست.",
    )

    save_fig(fig, "chart05_mandate_vs_deposit")


if __name__ == "__main__":
    main()
