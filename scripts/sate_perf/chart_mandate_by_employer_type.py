"""نمودار جدید (ساختاری) - سهم شرکت‌های مادر، زیرمجموعه و مستقل از اعتبار
تکلیفی.

Source: ``services.financial_engine.get_mandate_by_employer_raw`` (هر
شرکت/بانک/موسسه با نوع ساختاری واقعی خودش -- بدون تجمیع زیرمجموعه‌ها زیر
شرکت مادر؛ برخلاف دیدگاه ترکیبی «مادر + زیرمجموعه‌ها» که در سایر بخش‌های
سامانه استفاده می‌شود، چون اینجا هدف دقیقاً دیدن سهم واقعی هر رده است).
"""

import os
import sys

import numpy as np
from matplotlib.ticker import FuncFormatter
from sqlalchemy import func

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from core.database import SessionLocal
from models.deposits import AnnualMandate
from services.financial_engine import get_mandate_by_employer_raw
from style import (
    COLORS, TEXT_COLOR,
    add_source_note, add_title, fp, new_figure, rial_to_billion,
    save_fig, style_axes, to_fa_num,
)

TYPE_LABELS = {
    "Mother": "شرکت مادر",
    "Subsidiary": "شرکت زیرمجموعه",
    "Independent": "شرکت/بانک/موسسه مستقل",
}
TYPE_ORDER = ["Mother", "Subsidiary", "Independent"]
TYPE_COLORS = {
    "Mother": COLORS["primary"],
    "Subsidiary": COLORS["secondary"],
    "Independent": COLORS["accent"],
}


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

    by_type = df.groupby("employer_type")["mandated_amount"].agg(["sum", "count"])
    by_type = by_type.reindex(TYPE_ORDER).fillna(0)
    total = by_type["sum"].sum()

    values = by_type["sum"].apply(rial_to_billion).to_numpy()
    counts = by_type["count"].to_numpy()
    shares = values / rial_to_billion(total) * 100
    labels = [TYPE_LABELS[t] for t in TYPE_ORDER]
    colors = [TYPE_COLORS[t] for t in TYPE_ORDER]

    y = np.arange(len(labels))

    fig, ax = new_figure(figsize=(12, 6.5))
    fig.subplots_adjust(left=0.26, right=0.92, top=0.78, bottom=0.13)

    add_title(
        fig,
        f"سهم شرکت‌های مادر، زیرمجموعه و مستقل از اعتبار تکلیفی — سال {to_fa_num(int(year))}",
        "بر حسب میلیارد ریال؛ هر واحد در جایگاه ساختاری واقعی خودش (بدون تجمیع زیرمجموعه زیر مادر)",
    )

    bars = ax.barh(y, values, color=colors, height=0.5, zorder=3)
    ax.invert_yaxis()

    for bar, value, share, count in zip(bars, values, shares, counts):
        ax.text(
            bar.get_width() + values.max() * 0.015, bar.get_y() + bar.get_height() / 2,
            fp(f"{to_fa_num(f'{value:,.0f}')} میلیارد ریال ({to_fa_num(f'{share:.1f}')}٪) — {to_fa_num(int(count))} واحد"),
            ha="left", va="center", fontsize=10.5, fontweight="bold", color=TEXT_COLOR,
        )

    ax.set_yticks(y)
    ax.set_yticklabels([fp(name) for name in labels], fontsize=12)
    ax.set_xlim(0, values.max() * 1.55)
    ax.xaxis.set_major_formatter(FuncFormatter(lambda v, _: fp(to_fa_num(f"{v:,.0f}"))))
    ax.set_xlabel(fp("میلیارد ریال"), fontsize=11, labelpad=10)

    style_axes(ax)
    ax.grid(axis="x", color="#E5E7EB", linewidth=0.9, alpha=0.85, zorder=0)
    ax.tick_params(axis="y", length=0)

    add_source_note(
        fig,
        "منبع داده: services.financial_engine.get_mandate_by_employer_raw (پایگاه داده ساتع)",
    )

    save_fig(fig, "chart17_mandate_by_employer_type")


if __name__ == "__main__":
    main()
