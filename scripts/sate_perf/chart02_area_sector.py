# chart02_area_sector.py
from chart_config import (
    load_data, fp, fmt_num, CHARTS_DIR,
    CATEGORY_PALETTE, plt
)
import numpy as np

df = load_data()

# ── آماده‌سازی داده ──────────────────────────────────────────────────────────
# مجموع اعتبار به تفکیک سال و عنوان امور
pivot = (
    df.groupby(["سال", "عنوان امور"])["اعتبار"]
    .sum()
    .unstack(fill_value=0)
)

# تبدیل به درصد (سهم از کل هر سال)
pivot_pct = pivot.div(pivot.sum(axis=1), axis=0) * 100

years = pivot_pct.index.tolist()
categories = pivot_pct.columns.tolist()

# محور X: ایندکس مصنوعی برای فاصله یکنواخت
x_pos = list(range(len(years)))

FA_DIGITS = str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹")
def to_fa(n):
    return str(n).translate(FA_DIGITS)

x_labels = [to_fa(y) for y in years]

# جایگاه ۱۴۰۳ بین ۱۴۰۲ و ۱۴۰۴
idx_1402 = years.index(1402)
x_1403 = (x_pos[idx_1402] + x_pos[idx_1402 + 1]) / 2

# ── رسم نمودار ───────────────────────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(12, 7))

# رنگ‌ها از CATEGORY_PALETTE؛ اگر تعداد دسته‌ها بیشتر بود، چرخش رنگ
colors = (CATEGORY_PALETTE * ((len(categories) // len(CATEGORY_PALETTE)) + 1))[
    : len(categories)
]

# رسم stacked area
ax.stackplot(
    x_pos,
    [pivot_pct[cat].values for cat in categories],
    labels=[fp(cat) for cat in categories],
    colors=colors,
    alpha=0.85,
)

# ── خط نقطه‌چین ۱۴۰۳ ─────────────────────────────────────────────────────────
from chart_config import COLORS
ax.axvline(x=x_1403, color=COLORS["neutral"], linewidth=1,
           linestyle="--", alpha=0.6, zorder=5)

ax.figure.canvas.draw()
ymin, ymax = ax.get_ylim()
ax.text(
    x_1403 + 0.05, ymin + (ymax - ymin) * 0.03,
    fp("۱۴۰۳\n(اطلاعات\nموجود نیست)"),
    ha="left", va="bottom", fontsize=8,
    color=COLORS["neutral"],
    linespacing=1.5,
)

# ── برچسب درصد روی بزرگ‌ترین ناحیه‌ها (اختیاری، فقط سهم‌های > 10%) ──────────
for i, cat in enumerate(categories):
    for xi, yr in zip(x_pos, years):
        pct = pivot_pct.loc[yr, cat]
        if pct > 10:
            # مرکز عمودی این ناحیه در این نقطه
            bottom = pivot_pct[categories[:i]].loc[yr].sum()
            mid = bottom + pct / 2
            ax.text(
                xi, mid,
                fp(f"{fmt_num(pct, 1)}٪"),
                ha="center", va="center",
                fontsize=7.5, color="white",
                fontweight="bold",
            )

# ── محورها ───────────────────────────────────────────────────────────────────
ax.set_xticks(x_pos)
ax.set_xticklabels(x_labels, fontsize=10)
ax.set_ylim(0, 100)
ax.yaxis.set_major_formatter(
    __import__("matplotlib.ticker", fromlist=["FuncFormatter"])
    .FuncFormatter(lambda v, _: fp(f"{int(v)}٪"))
)
ax.set_ylabel(fp("سهم از کل اعتبارات (درصد)"), labelpad=10)

# ── راهنما (legend) ───────────────────────────────────────────────────────────
handles, labels = ax.get_legend_handles_labels()
ax.legend(
    handles[::-1], labels[::-1],          # ترتیب معکوس = منطبق با ترتیب بصری
    loc="upper left",
    bbox_to_anchor=(1.01, 1),
    borderaxespad=0,
    fontsize=9,
    framealpha=0.8,
    title=fp("عنوان امور"),
    title_fontsize=9,
)

# ── عنوان و گرید ─────────────────────────────────────────────────────────────
ax.set_title(
    fp("سهم هر عنوان امور از کل اعتبارات تکلیفی (۱۳۹۸–۱۴۰۵)"),
    pad=16, fontsize=14,
)
ax.grid(axis="y", linestyle="--", alpha=0.4)
ax.grid(axis="x", linestyle=":", alpha=0.2)
ax.set_axisbelow(True)
ax.margins(x=0.03)

fig.tight_layout()

# ── ذخیره ────────────────────────────────────────────────────────────────────
out = CHARTS_DIR / "chart02_amoor_share.png"
fig.savefig(out, dpi=150, bbox_inches="tight")
plt.close(fig)
print(f"ذخیره شد: {out}")
