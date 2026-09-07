"""نمودار جدید (سمت عرضه) - ده دانشگاه/موسسه دارای بیشترین تعداد قرارداد.

Source: ``services.financial_engine.get_employer_university_fund_flow`` --
the same authoritative aggregation the "رتبه‌بندی دانشگاه‌ها" live dashboard
uses, re-grouped here from (employer, university) pairs up to university
level, and filtered to the report's own window (from 1403) rather than the
dashboard's default (since 1402).
"""

import os
import sys

import numpy as np
from matplotlib.ticker import FuncFormatter

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from core.database import SessionLocal
from services.financial_engine import get_employer_university_fund_flow
from style import (
    CATEGORY_PALETTE, HIGHLIGHT_COLOR, TEXT_COLOR,
    add_source_note, add_title, fp, new_figure, save_fig, style_axes, to_fa_num,
)

SINCE_JALALI_YEAR = 1403
TOP_N = 10


def fetch_university_totals():
    db = SessionLocal()
    try:
        df, meta = get_employer_university_fund_flow(db, since_jalali_year=SINCE_JALALI_YEAR)
    finally:
        db.close()
    by_university = (
        df.groupby("university_name", as_index=False)
        .agg(contracts_count=("contracts_count", "sum"))
        .sort_values("contracts_count", ascending=False)
    )
    return by_university, meta


def main():
    by_university, meta = fetch_university_totals()
    total = by_university["contracts_count"].sum()
    top = by_university.head(TOP_N)

    labels = top["university_name"].tolist()
    values = top["contracts_count"].to_numpy()
    shares = values / total * 100

    fig, ax = new_figure(figsize=(13, 8))
    fig.subplots_adjust(left=0.34, right=0.92, top=0.80, bottom=0.11)

    add_title(
        fig,
        f"دانشگاه‌ها/موسسات دارای بیشترین تعداد قرارداد از سال {to_fa_num(SINCE_JALALI_YEAR)}",
        f"از مجموع {to_fa_num(f'{int(total):,}')} قرارداد منعقدشده در این بازه",
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
    ax.set_yticklabels([fp(name) for name in labels], fontsize=10.5)
    ax.set_xlim(0, values.max() * 1.3)
    ax.xaxis.set_major_formatter(FuncFormatter(lambda v, _: fp(to_fa_num(f"{v:,.0f}"))))
    ax.set_xlabel(fp("تعداد قرارداد"), fontsize=11, labelpad=10)

    style_axes(ax)
    ax.grid(axis="x", color="#E5E7EB", linewidth=0.9, alpha=0.85, zorder=0)
    ax.tick_params(axis="y", length=0)

    note = "منبع داده: services.financial_engine.get_employer_university_fund_flow (پایگاه داده ساتع)"
    if meta["excluded_no_contract_date"] > 0:
        note += f"؛ {to_fa_num(meta['excluded_no_contract_date'])} قرارداد فاقد تاریخ از تحلیل کنار گذاشته شد"
    add_source_note(fig, note)

    save_fig(fig, "chart12_university_top_by_count")


if __name__ == "__main__":
    main()
