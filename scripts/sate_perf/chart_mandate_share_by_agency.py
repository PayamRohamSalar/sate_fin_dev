"""نمودار 2 - سهم هر یک از دستگاه‌های اجرایی از اعتبار تکلیفی سال هدف.

Source: ``annual_mandates`` joined to ``employers`` (grouped on
``employers.upper_organization``, i.e. دستگاه اجرایی مرتبط).

TARGET_YEAR defaults to the most recent fiscal year present in the data;
override below if a specific year (matching the 1404 report) is wanted
instead.
"""

import os
import sys

import numpy as np
from matplotlib.ticker import FuncFormatter
from sqlalchemy import func, select

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from core.database import SessionLocal
from models.employer import Employer
from models.deposits import AnnualMandate
from style import (
    CATEGORY_PALETTE, HIGHLIGHT_COLOR, TEXT_COLOR, MUTED_TEXT_COLOR,
    add_source_note, add_title, fp, new_figure, rial_to_billion,
    save_fig, style_axes, to_fa_num,
)

TARGET_YEAR = None  # None = latest year available; set an int (e.g. 1404) to pin it
TOP_N = 6


def fetch_latest_year(db) -> int:
    return db.query(func.max(AnnualMandate.fiscal_year)).filter(
        AnnualMandate.is_deleted == False  # noqa: E712
    ).scalar()


def fetch_share_by_agency(year: int):
    db = SessionLocal()
    try:
        rows = (
            db.execute(
                select(Employer.upper_organization, func.sum(AnnualMandate.mandated_amount))
                .select_from(AnnualMandate)
                .join(Employer, AnnualMandate.employer_code == Employer.classification_code)
                .where(
                    AnnualMandate.is_deleted == False,  # noqa: E712
                    Employer.is_deleted == False,  # noqa: E712
                    AnnualMandate.fiscal_year == year,
                )
                .group_by(Employer.upper_organization)
            )
            .all()
        )
    finally:
        db.close()
    return [(agency or "نامشخص", rial_to_billion(total)) for agency, total in rows if total]


def main():
    db = SessionLocal()
    try:
        year = TARGET_YEAR or fetch_latest_year(db)
    finally:
        db.close()

    data = fetch_share_by_agency(year)
    data.sort(key=lambda r: r[1], reverse=True)

    top = data[:TOP_N]
    rest_total = sum(v for _, v in data[TOP_N:])
    if rest_total > 0:
        top.append(("سایر دستگاه‌های اجرایی", rest_total))

    total = sum(v for _, v in top)
    labels = [name for name, _ in top]
    values = np.array([v for _, v in top])
    shares = values / total * 100

    fig, ax = new_figure(figsize=(12.5, 7.5))
    fig.subplots_adjust(left=0.28, right=0.93, top=0.82, bottom=0.12)

    add_title(
        fig,
        f"سهم دستگاه‌های اجرایی از اعتبار تکلیفی سال {to_fa_num(year)}",
        "بر حسب میلیارد ریال و درصد از کل اعتبار تکلیفی",
    )

    y = np.arange(len(labels))
    colors = [HIGHLIGHT_COLOR if i == 0 else CATEGORY_PALETTE[i % len(CATEGORY_PALETTE)]
              for i in range(len(labels))]

    bars = ax.barh(y, values, color=colors, height=0.62, zorder=3)
    ax.invert_yaxis()

    for bar, value, share in zip(bars, values, shares):
        ax.text(
            bar.get_width() + total * 0.012, bar.get_y() + bar.get_height() / 2,
            fp(f"{to_fa_num(f'{value:,.0f}')} ({to_fa_num(f'{share:.1f}')}٪)"),
            ha="left", va="center", fontsize=10.5, fontweight="bold", color=TEXT_COLOR,
        )

    ax.set_yticks(y)
    ax.set_yticklabels([fp(name) for name in labels], fontsize=11.5)
    ax.set_xlim(0, values.max() * 1.28)
    ax.xaxis.set_major_formatter(FuncFormatter(lambda v, _: fp(to_fa_num(f"{v:,.0f}"))))
    ax.set_xlabel(fp("میلیارد ریال"), fontsize=11, labelpad=10)

    style_axes(ax)
    ax.grid(axis="x", color="#E5E7EB", linewidth=0.9, alpha=0.85, zorder=0)
    ax.tick_params(axis="y", length=0)

    add_source_note(fig, "منبع داده: annual_mandates + employers (پایگاه داده ساتع)")

    save_fig(fig, "chart02_mandate_share_by_agency")


if __name__ == "__main__":
    main()
