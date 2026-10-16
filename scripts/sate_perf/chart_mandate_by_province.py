"""نمودار جدید (جغرافیایی) - توزیع اعتبار تکلیفی به تفکیک استان محل مشمول.

Source: ``services.financial_engine.get_mandate_by_employer_raw`` (سطح
واقعی هر مشمول، بدون تجمیع مادر/زیرمجموعه) برای آخرین سال موجود.
"""

import os
import sys

import numpy as np
import pandas as pd
from matplotlib.ticker import FuncFormatter
from sqlalchemy import func

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from core.database import SessionLocal
from models.deposits import AnnualMandate
from services.financial_engine import get_mandate_by_employer_raw
from style import (
    CATEGORY_PALETTE, HIGHLIGHT_COLOR, TEXT_COLOR,
    add_source_note, add_title, fp, new_figure, rial_to_billion,
    save_fig, style_axes, to_fa_num,
)

TOP_N = 8
UNKNOWN_LABEL = "نامشخص"
OTHER_LABEL = "سایر استان‌ها"


def fetch_latest_year(db) -> int:
    return db.query(func.max(AnnualMandate.fiscal_year)).filter(
        AnnualMandate.is_deleted == False  # noqa: E712
    ).scalar()


def main():
    db = SessionLocal()
    try:
        year = fetch_latest_year(db)
        df = get_mandate_by_employer_raw(db, fiscal_years=[year])
    finally:
        db.close()

    df["province"] = df["province"].replace({"Unknown": UNKNOWN_LABEL}).fillna(UNKNOWN_LABEL)
    by_province = (
        df.groupby("province", as_index=False)["mandated_amount"]
        .sum()
        .sort_values("mandated_amount", ascending=False)
    )
    total = by_province["mandated_amount"].sum()

    top = by_province.head(TOP_N)
    rest_total = by_province["mandated_amount"].iloc[TOP_N:].sum()

    labels = top["province"].tolist()
    values = top["mandated_amount"].apply(rial_to_billion).to_numpy()
    if rest_total > 0:
        labels.append(OTHER_LABEL)
        values = np.append(values, rial_to_billion(rest_total))
    shares = values / rial_to_billion(total) * 100

    fig, ax = new_figure(figsize=(12.5, 7.5))
    fig.subplots_adjust(left=0.24, right=0.93, top=0.80, bottom=0.15)

    add_title(
        fig,
        f"توزیع اعتبار تکلیفی به تفکیک استان محل مشمول — سال {to_fa_num(int(year))}",
        "بر حسب میلیارد ریال؛ استان بر اساس نشانی ثبتی مشمول (employers.province)",
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
    ax.set_xlabel(fp("میلیارد ریال"), fontsize=11, labelpad=10)

    style_axes(ax)
    ax.grid(axis="x", color="#E5E7EB", linewidth=0.9, alpha=0.85, zorder=0)
    ax.tick_params(axis="y", length=0)

    add_source_note(
        fig,
        "منبع داده: services.financial_engine.get_mandate_by_employer_raw (پایگاه داده ساتع). "
        "استان «نامشخص» به معنای نبود این فیلد در پروندهٔ مشمول است.",
    )

    save_fig(fig, "chart16_mandate_by_province")


if __name__ == "__main__":
    main()
