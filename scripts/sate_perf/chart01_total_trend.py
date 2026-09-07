# chart01_total_trend.py
from chart_config import (
    load_data, fp, fmt_num, fa_year_formatter, CHARTS_DIR,
    COLORS, plt
)
import matplotlib.ticker as mticker
import numpy as np

df = load_data()

# ── آماده‌سازی داده ──────────────────────────────────────────────────────────
yearly = (
    df.groupby("سال")["اعتبار"]
    .sum()
    .reset_index()
    .sort_values("سال")
)

years  = yearly["سال"].tolist()
values = yearly["اعتبار"].tolist()

# رشد سال به سال (YoY)
yoy = [None] + [
    (values[i] - values[i-1]) / values[i-1] * 100
    for i in range(1, len(values))
]

# ── محور X: ایندکس مصنوعی برای فاصله یکنواخت ────────────────────────────────
# به جای مقادیر واقعی سال، از ایندکس 0,1,2,... استفاده می‌کنیم
# تا فاصله بین همه سال‌ها یکسان باشد
x_pos = list(range(len(years)))

# برچسب‌های فارسی سال + نشانگر ۱۴۰۳
FA_DIGITS = str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹")
def to_fa(n):
    return str(n).translate(FA_DIGITS)

x_labels = [to_fa(y) for y in years]

# جایگاه ۱۴۰۳ بین ۱۴۰۲ و ۱۴۰۴
idx_1402 = years.index(1402)
x_1403 = (x_pos[idx_1402] + x_pos[idx_1402 + 1]) / 2  # دقیقاً وسط

# ── رسم نمودار ───────────────────────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(11, 6))

# خط اصلی
ax.plot(x_pos, values, color=COLORS["primary"], linewidth=2.5,
        marker="o", markersize=8, zorder=3)

# سایه زیر خط
ax.fill_between(x_pos, values, alpha=0.12, color=COLORS["primary"])

# برچسب مقدار و رشد روی هر نقطه
for xi, y, g in zip(x_pos, values, yoy):
    ax.annotate(
        fp(f"{fmt_num(y, 1)}"),
        xy=(xi, y),
        xytext=(0, 14),
        textcoords="offset points",
        ha="center", va="bottom",
        fontsize=9,
        color=COLORS["primary"],
    )
    if g is not None:
        sign  = "+" if g >= 0 else ""
        color = COLORS["accent"] if g >= 0 else COLORS["danger"]
        ax.annotate(
            fp(f"{sign}{fmt_num(g, 1)}٪"),
            xy=(xi, y),
            xytext=(0, -18),
            textcoords="offset points",
            ha="center", va="top",
            fontsize=8,
            color=color,
        )

# ── محورها ───────────────────────────────────────────────────────────────────
ax.set_xticks(x_pos)
ax.set_xticklabels(x_labels, fontsize=10)

ax.yaxis.set_major_formatter(
    mticker.FuncFormatter(lambda v, _: fp(fmt_num(v, 0)))
)
ax.set_ylabel(fp("اعتبار تکلیفی (میلیارد ریال)"), labelpad=10)

# ── خط نقطه‌چین ۱۴۰۳ ─────────────────────────────────────────────────────────
ax.axvline(x=x_1403, color=COLORS["neutral"], linewidth=1,
           linestyle="--", alpha=0.6, zorder=1)

# برچسب ۱۴۰۳ — بعد از رسم همه چیز، ylim را می‌گیریم
ax.figure.canvas.draw()  # محدوده Y را نهایی می‌کند
ymin, ymax = ax.get_ylim()
ax.text(
    x_1403 + 0.05, ymin + (ymax - ymin) * 0.03,
    fp("حذف بند قانونی\nدر سال 1403"),
    ha="left", va="bottom", fontsize=8,
    color=COLORS["neutral"],
    linespacing=1.5,
)

# ── عنوان و گرید ─────────────────────────────────────────────────────────────
ax.set_title(fp("روند کل اعتبارات تکلیفی پیوست ۳ قانون بودجه (۱۳۹۸–۱۴۰۵)"),
             pad=16, fontsize=14)
ax.grid(axis="y", linestyle="--", alpha=0.4)
ax.grid(axis="x", linestyle=":", alpha=0.2)
ax.set_axisbelow(True)

# کمی فضای اضافه در بالا برای برچسب‌ها
ax.margins(x=0.06, y=0.15)  # به جای ax.margins(x=0.06)

fig.tight_layout()

# ── ذخیره ────────────────────────────────────────────────────────────────────
out = CHARTS_DIR / "chart01_total_trend.png"
fig.savefig(out, dpi=150, bbox_inches="tight")
plt.close(fig)
print(f"ذخیره شد: {out}")
