"""نمودار جدید (سمت عرضه) - ده دانشگاه/موسسه برتر: مبلغ قرارداد در برابر مبلغ
دریافتی (پرداخت‌شده واقعی).

Source: همان services.financial_engine.get_employer_university_fund_flow،
رتبه‌بندی‌شده بر اساس مبلغ دریافتی (معیار «جذب موفق بودجه»).
"""

import os
import sys

import numpy as np
from matplotlib.ticker import FuncFormatter

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from core.database import SessionLocal
from services.financial_engine import get_employer_university_fund_flow
from style import (
    COLORS, TEXT_COLOR,
    add_source_note, add_title, fp, new_figure, rial_to_billion,
    save_fig, style_axes, to_fa_num,
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
        .agg(contracts_amount=("contracts_amount", "sum"), payments_amount=("payments_amount", "sum"))
        .sort_values("payments_amount", ascending=False)
    )
    return by_university, meta


def main():
    by_university, meta = fetch_university_totals()
    top = by_university.head(TOP_N)

    labels = top["university_name"].tolist()
    contracted = top["contracts_amount"].apply(rial_to_billion).to_numpy()
    paid = top["payments_amount"].apply(rial_to_billion).to_numpy()

    y = np.arange(len(labels))
    height = 0.36

    fig, ax = new_figure(figsize=(13, 8))
    fig.subplots_adjust(left=0.34, right=0.92, top=0.80, bottom=0.11)

    add_title(
        fig,
        f"مبلغ قرارداد در برابر مبلغ دریافتی — دانشگاه‌ها/موسسات برتر از سال {to_fa_num(SINCE_JALALI_YEAR)}",
        "بر حسب میلیارد ریال؛ رتبه‌بندی بر اساس مبلغ دریافتی",
    )

    bars1 = ax.barh(y + height / 2, contracted, height=height, color=COLORS["primary"],
                    label=fp("مبلغ قرارداد (تعهدشده)"), zorder=3)
    bars2 = ax.barh(y - height / 2, paid, height=height, color=COLORS["accent"],
                    label=fp("مبلغ دریافتی (واقعی)"), zorder=3)
    ax.invert_yaxis()

    max_val = max(contracted.max(), paid.max())
    for bars in (bars1, bars2):
        for bar in bars:
            w = bar.get_width()
            if w <= 0:
                continue
            ax.text(w + max_val * 0.012, bar.get_y() + bar.get_height() / 2,
                    fp(to_fa_num(f"{w:,.0f}")), ha="left", va="center",
                    fontsize=9, fontweight="bold", color=TEXT_COLOR)

    ax.set_yticks(y)
    ax.set_yticklabels([fp(name) for name in labels], fontsize=10.5)
    ax.set_xlim(0, max_val * 1.28)
    ax.xaxis.set_major_formatter(FuncFormatter(lambda v, _: fp(to_fa_num(f"{v:,.0f}"))))
    ax.set_xlabel(fp("میلیارد ریال"), fontsize=11, labelpad=10)

    style_axes(ax)
    ax.grid(axis="x", color="#E5E7EB", linewidth=0.9, alpha=0.85, zorder=0)
    ax.tick_params(axis="y", length=0)
    ax.legend(loc="lower right", frameon=False, fontsize=10.5)

    note = "منبع داده: services.financial_engine.get_employer_university_fund_flow (پایگاه داده ساتع)"
    if meta["excluded_no_contract_date"] > 0:
        note += f"؛ {to_fa_num(meta['excluded_no_contract_date'])} قرارداد فاقد تاریخ از تحلیل کنار گذاشته شد"
    add_source_note(fig, note)

    save_fig(fig, "chart13_university_contract_vs_payment")


if __name__ == "__main__":
    main()
