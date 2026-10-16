"""نمودار جدید (جغرافیایی) - تعداد قراردادها به تفکیک استان محل کارفرما.

Source: ``contracts`` join ``employers`` (استان کارفرما، نه دانشگاه مجری).
Contracts may only be held by Mother/Independent employers (business rule
enforced elsewhere), so no Mother/Subsidiary roll-up ambiguity applies here.
"""

import os
import sys

import numpy as np
from matplotlib.ticker import FuncFormatter
from sqlalchemy import func, select

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from core.database import SessionLocal
from models.employer import Employer
from models.contract import Contract
from style import (
    CATEGORY_PALETTE, HIGHLIGHT_COLOR, TEXT_COLOR,
    add_source_note, add_title, fp, new_figure, save_fig, style_axes, to_fa_num,
)

TOP_N = 8
UNKNOWN_LABEL = "نامشخص"
OTHER_LABEL = "سایر استان‌ها"


def fetch_by_province():
    db = SessionLocal()
    try:
        rows = db.execute(
            select(Employer.province, func.count(Contract.tracking_code))
            .select_from(Contract)
            .join(Employer, Contract.employer_code == Employer.classification_code)
            .where(Contract.is_deleted == False, Employer.is_deleted == False)  # noqa: E712
            .group_by(Employer.province)
        ).all()
    finally:
        db.close()
    return [(province or UNKNOWN_LABEL, count) for province, count in rows]


def main():
    rows = fetch_by_province()
    rows = [(UNKNOWN_LABEL if p == "Unknown" else p, c) for p, c in rows]
    rows.sort(key=lambda r: r[1], reverse=True)

    total = sum(c for _, c in rows)
    top = rows[:TOP_N]
    rest_total = sum(c for _, c in rows[TOP_N:])

    labels = [p for p, _ in top]
    values = np.array([c for _, c in top], dtype=float)
    if rest_total > 0:
        labels.append(OTHER_LABEL)
        values = np.append(values, rest_total)
    shares = values / total * 100

    fig, ax = new_figure(figsize=(12.5, 7.5))
    fig.subplots_adjust(left=0.24, right=0.93, top=0.80, bottom=0.11)

    add_title(
        fig,
        "تعداد قراردادهای منعقدشده به تفکیک استان محل کارفرما",
        "استان بر اساس نشانی ثبتی کارفرما (employers.province)، نه دانشگاه مجری",
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
    ax.set_yticklabels([fp(name) for name in labels], fontsize=11)
    ax.set_xlim(0, values.max() * 1.3)
    ax.xaxis.set_major_formatter(FuncFormatter(lambda v, _: fp(to_fa_num(f"{v:,.0f}"))))
    ax.set_xlabel(fp("تعداد قرارداد"), fontsize=11, labelpad=10)

    style_axes(ax)
    ax.grid(axis="x", color="#E5E7EB", linewidth=0.9, alpha=0.85, zorder=0)
    ax.tick_params(axis="y", length=0)

    add_source_note(fig, "منبع داده: contracts + employers (پایگاه داده ساتع)")

    save_fig(fig, "chart18_contracts_by_province")


if __name__ == "__main__":
    main()
