"""نمودار 1 - روند کل اعتبار تکلیفی مشمولین بند (ث) تبصره (4) به تفکیک سال.

Source: ``annual_mandates`` (SUM(mandated_amount) GROUP BY fiscal_year).
"""

import os
import sys

import numpy as np
from matplotlib.ticker import FuncFormatter
from sqlalchemy import func

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from core.database import SessionLocal
from models.employer import Employer  # noqa: F401 -- registers the ORM relationship target used by models.deposits
from models.deposits import AnnualMandate
from style import (
    COLORS, HIGHLIGHT_COLOR, TEXT_COLOR, MUTED_TEXT_COLOR,
    add_source_note, add_title, fp, new_figure, rial_to_billion,
    save_fig, style_axes, to_fa_num,
)


def fetch_yearly_totals():
    db = SessionLocal()
    try:
        rows = (
            db.query(AnnualMandate.fiscal_year, func.sum(AnnualMandate.mandated_amount))
            .filter(AnnualMandate.is_deleted == False)  # noqa: E712
            .group_by(AnnualMandate.fiscal_year)
            .order_by(AnnualMandate.fiscal_year)
            .all()
        )
    finally:
        db.close()
    return [(int(y), rial_to_billion(total)) for y, total in rows if total]


def main():
    data = fetch_yearly_totals()
    years = [y for y, _ in data]
    values = np.array([v for _, v in data])
    x = np.arange(len(years))

    yoy = [None] + [
        (values[i] - values[i - 1]) / values[i - 1] * 100 if values[i - 1] else None
        for i in range(1, len(values))
    ]

    fig, ax = new_figure(figsize=(12.5, 7))
    fig.subplots_adjust(left=0.09, right=0.95, top=0.80, bottom=0.16)

    add_title(
        fig,
        "روند اعتبار تکلیفی مشمولین بند (ث) تبصره (4)",
        "مجموع اعتبار تکلیفی سالانه بر حسب میلیارد ریال",
    )

    ax.plot(x, values, color=COLORS["primary"], linewidth=2.8, marker="o",
            markersize=8, markerfacecolor="white", markeredgecolor=COLORS["primary"],
            markeredgewidth=2, zorder=4)
    ax.fill_between(x, values, alpha=0.12, color=COLORS["primary"], zorder=2)

    for xi, y, g in zip(x, values, yoy):
        ax.annotate(fp(fmt_num_label(y)), xy=(xi, y), xytext=(0, 14),
                    textcoords="offset points", ha="center", va="bottom",
                    fontsize=10, fontweight="bold", color=TEXT_COLOR)
        if g is not None:
            sign = "+" if g >= 0 else ""
            color = COLORS["accent"] if g >= 0 else COLORS["danger"]
            ax.annotate(fp(f"{sign}{g:.0f}٪"), xy=(xi, y), xytext=(0, -18),
                        textcoords="offset points", ha="center", va="top",
                        fontsize=8.5, color=color)

    # Gap marker for years missing from the mandate (e.g. 1403, when the
    # 60% clause briefly lapsed before being restored in the budget law).
    all_years = list(range(min(years), max(years) + 1))
    missing = [y for y in all_years if y not in years]
    for m in missing:
        prev_years = [y for y in years if y < m]
        if prev_years:
            idx = years.index(max(prev_years))
            ax.axvline(x=idx + 0.5, color=MUTED_TEXT_COLOR, linewidth=1,
                       linestyle="--", alpha=0.6, zorder=1)
            ax.text(idx + 0.55, values.min(), fp(f"{to_fa_num(m)}\n(حذف از قانون بودجه)"),
                    ha="left", va="bottom", fontsize=8, color=MUTED_TEXT_COLOR,
                    linespacing=1.4)

    ax.set_xticks(x)
    ax.set_xticklabels([fp(to_fa_num(y)) for y in years], fontsize=11)
    ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: fp(to_fa_num(f"{v:,.0f}"))))
    ax.set_ylabel(fp("میلیارد ریال"), fontsize=11, labelpad=14)
    ax.margins(y=0.18)

    style_axes(ax)
    add_source_note(fig, "منبع داده: جدول annual_mandates (پایگاه داده ساتع)")

    save_fig(fig, "chart01_mandate_trend")


def fmt_num_label(v: float) -> str:
    formatted = f"{v:,.0f}"
    fa_digits = str.maketrans("0123456789,", "۰۱۲۳۴۵۶۷۸۹،")
    return formatted.translate(fa_digits)


if __name__ == "__main__":
    main()
