# chart05_pareto.py
from chart_config import (
    load_data, fp, fmt_num, CHARTS_DIR,
    COLORS, CATEGORY_PALETTE, plt
)
import matplotlib.ticker as mticker
import numpy as np

df = load_data()

# ── آماده‌سازی داده ──────────────────────────────────────────────────────────
# جمع کل اعتبار به تفکیک «نام مشمول» در همه سال‌ها
by_item = (
    df.groupby("نام مشمول")["اعتبار"]
    .sum()
    .sort_values(ascending=False).reset_index()
)

by_item["سهم"] = by_item["اعتبار"] / by_item["اعتبار"].sum() * 100
by_item["سهم_تجمعی"] = by_item["سهم"].cumsum()

# مرز ۸۰٪
cutoff = (by_item["سهم_تجمعی"] <= 80).sum()
n = len(by_item)
x = np.arange(n)

# ── رسم ─────────────────────────────────────────────────────────────────────
fig, ax1 = plt.subplots(figsize=(13, 6))
ax2 = ax1.twinx()

# میله‌ها
colors = [COLORS["primary"] if i < cutoff else COLORS["neutral"] for i in range(n)]
ax1.bar(x, by_item["اعتبار"], color=colors, width=0.7, zorder=2)

# خط تجمعی
ax2.plot(x, by_item["سهم_تجمعی"], color=COLORS["danger"],
         linewidth=2, marker="o", markersize=4, zorder=3)

# خط ۸۰٪
ax2.axhline(80, color=COLORS["secondary"], linewidth=1.2,
            linestyle="--", alpha=0.8)
ax2.text(n * 0.02, 81.5, fp("۸۰٪"), color=COLORS["secondary"], fontsize=9)

# خط عمودی مرز
ax1.axvline(cutoff - 0.5, color=COLORS["accent"], linewidth=1.2,
            linestyle="--", alpha=0.8)
ax1.text(cutoff - 0.4, ax1.get_ylim()[1] * 0.95,
         fp(f"۲۰٪ شرکت ({cutoff} مورد)"),
         color=COLORS["accent"], fontsize=8, va="top")

# ── محورها ───────────────────────────────────────────────────────────────────
ax1.set_xticks([])          # برچسب‌های x شلوغ می‌شوند؛ حذف می‌شوند
ax1.yaxis.set_major_formatter(
    mticker.FuncFormatter(lambda v, _: fp(fmt_num(v, 0)))
)
ax1.set_ylabel(fp("اعتبار تکلیفی (میلیارد ریال)"), labelpad=10)

ax2.set_ylim(0, 110)
ax2.yaxis.set_major_formatter(
    mticker.FuncFormatter(lambda v, _: fp(f"{fmt_num(v, 0)}٪"))
)
ax2.set_ylabel(fp("درصد تجمعی"), labelpad=10)

# ── راهنما ───────────────────────────────────
from matplotlib.patches import Patch
from matplotlib.lines import Line2D
legend_elements = [
    Patch(facecolor=COLORS["primary"],  label=fp("۲۰٪ شرکت برتر (۸۰٪ اعتبار)")),
    Patch(facecolor=COLORS["neutral"],  label=fp("سایر شرکت")),
    Line2D([0], [0], color=COLORS["danger"], linewidth=2, label=fp("درصد تجمعی")),
]
ax1.legend(handles=legend_elements, loc="center right", fontsize=9)

# ── عنوان و گرید ─────────────────────────────────────────────────────────────
ax1.set_title(fp("تحلیل پارتو (۸۰-۲۰) اعتبارات تکلیفی پیوست ۳ قانون بودجه"),
              pad=16, fontsize=14)
ax1.grid(axis="y", linestyle="--", alpha=0.4)
ax1.set_axisbelow(True)

fig.tight_layout()

# ── ذخیره ────────────────────────────────────────────────────────────────────
out = CHARTS_DIR / "chart05_pareto.png"
fig.savefig(out, dpi=150, bbox_inches="tight")
plt.close(fig)
print(f"ذخیره شد: {out}")
