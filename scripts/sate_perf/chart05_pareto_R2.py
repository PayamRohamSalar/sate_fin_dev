# chart05_pareto.py
from chart_config import (
    load_data, fp, fmt_num, to_fa_num, CHARTS_DIR,
    COLORS, CATEGORY_PALETTE, plt
)
import matplotlib.ticker as mticker
from matplotlib.patches import Patch
from matplotlib.lines import Line2D
import numpy as np

df = load_data()

years = sorted(df["سال"].unique())

for year in years:
    df_year = df[df["سال"] == year].copy()

    # ── آماده‌سازی داده ──────────────────────────────────────────────────────
    by_item = (
        df_year.groupby("نام مشمول")["اعتبار"]
        .sum()
        .sort_values(ascending=False)
        .reset_index()
    )

    by_item["سهم"] = by_item["اعتبار"] / by_item["اعتبار"].sum() * 100
    by_item["سهم_تجمعی"] = by_item["سهم"].cumsum()

    cutoff = (by_item["سهم_تجمعی"] <= 80).sum()
    n = len(by_item)
    x = np.arange(n)

    # ── رسم ──────────────────────────────────────────────────────────────────
    fig, ax1 = plt.subplots(figsize=(13, 6))
    ax2 = ax1.twinx()

    colors = [COLORS["primary"] if i < cutoff else COLORS["neutral"] for i in range(n)]
    ax1.bar(x, by_item["اعتبار"], color=colors, width=0.7, zorder=2)

    ax2.plot(x, by_item["سهم_تجمعی"], color=COLORS["danger"],
             linewidth=2, marker="o", markersize=4, zorder=3)

    ax2.axhline(80, color=COLORS["secondary"], linewidth=1.2,
                linestyle="--", alpha=0.8)
    ax2.text(n * 0.02, 81.5, fp("۸۰٪"), color=COLORS["secondary"], fontsize=9)

    ax1.axvline(cutoff - 0.5, color=COLORS["accent"], linewidth=1.2,
                linestyle="--", alpha=0.8)
    ax1.text(cutoff - 0.4, ax1.get_ylim()[1] * 0.95,
             fp(f"۲۰٪ شرکت مشمول ({to_fa_num(cutoff)} مورد)"),
             color=COLORS["accent"], fontsize=8, va="top")

    # ── محورها ───────────────────────────────────────────────────────────────
    ax1.set_xticks([])
    ax1.yaxis.set_major_formatter(
        mticker.FuncFormatter(lambda v, _: fp(fmt_num(v, 0)))
    )
    ax1.set_ylabel(fp("اعتبار تکلیفی (میلیارد ریال)"), labelpad=10)

    ax2.set_ylim(0, 110)
    ax2.yaxis.set_major_formatter(
        mticker.FuncFormatter(lambda v, _: fp(f"{fmt_num(v, 0)}٪"))
    )
    ax2.set_ylabel(fp("درصد تجمعی"), labelpad=10)

    # ── راهنما ───────────────────────────────────────────────────────────────
    legend_elements = [
        Patch(facecolor=COLORS["primary"], label=fp("۲۰٪ شرکت‌های برتر (۸۰٪ اعتبار)")),
        Patch(facecolor=COLORS["neutral"], label=fp("سایر شرکت‌های مشمول")),
        Line2D([0], [0], color=COLORS["danger"], linewidth=2, label=fp("درصد تجمعی")),
    ]
    ax1.legend(handles=legend_elements, loc="center right", fontsize=9)

    # ── عنوان ────────────────────────────────────────────────────────────────
    ax1.set_title(
        fp(f"تحلیل پارتو (۸۰-۲۰) اعتبارات تکلیفی — سال {to_fa_num(year)}"),
        pad=16, fontsize=14
    )
    ax1.grid(axis="y", linestyle="--", alpha=0.4)
    ax1.set_axisbelow(True)

    fig.tight_layout()

    # ── ذخیره ────────────────────────────────────────────────────────────────
    out = CHARTS_DIR / f"chart05_pareto_{year}.png"
    fig.savefig(out, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"ذخیره شد: {out}")
