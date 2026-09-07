# chart03_dastagah_share.py
from chart_config import (
    load_data, fp, fmt_num, CHARTS_DIR,
    CATEGORY_PALETTE, COLORS, plt,
)
import matplotlib.ticker as mticker
import numpy as np

df = load_data()

# ── آماده‌سازی داده ──────────────────────────────────────────────────────────
pivot = (
    df.groupby(["سال", "دستگاه اجرایی مرتبط"])["اعتبار"]
    .sum()
    .unstack(fill_value=0)
)

# مرتب‌سازی دستگاه‌ها بر اساس میانگین سهم (بزرگ‌ترین پایین‌ترین ناحیه)
mean_share = pivot.div(pivot.sum(axis=1), axis=0).mean()
ordered_cols = mean_share.sort_values(ascending=False).index.tolist()
pivot = pivot[ordered_cols]

pivot_pct = pivot.div(pivot.sum(axis=1), axis=0) * 100

years = pivot_pct.index.tolist()
categories = pivot_pct.columns.tolist()

x_pos = list(range(len(years)))

FA_DIGITS = str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹")
def to_fa(n):
    return str(n).translate(FA_DIGITS)

x_labels = [to_fa(y) for y in years]

# جایگاه ۱۴۰۳ بین ۱۴۰۲ و ۱۴۰۴
idx_1402 = years.index(1402)
x_1403 = (x_pos[idx_1402] + x_pos[idx_1402 + 1]) / 2

# ── رسم نمودار ───────────────────────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(13, 7))

colors = (CATEGORY_PALETTE * ((len(categories) // len(CATEGORY_PALETTE)) + 1))[
    : len(categories)
]

ax.stackplot(
    x_pos,
    [pivot_pct[cat].values for cat in categories],
    labels=[fp(cat) for cat in categories],
    colors=colors,
    alpha=0.85,
)

# ── خط نقطه‌چین ۱۴۰۳ ─────────────────────────────────────────────────────────
ax.axvline(
    x=x_1403,
    color=COLORS["neutral"],
    linewidth=1,
    linestyle="--",
    alpha=0.6,
    zorder=5,
)
ax.text(
    x_1403 + 0.05, 2,
    fp("۱۴۰۳\n(اطلاعات\nموجود نیست)"),
    ha="left", va="bottom",
    fontsize=8,
    color=COLORS["neutral"],
    linespacing=1.5,
)

# ── برچسب درصد (فقط سهم‌های > 8%) ───────────────────────────────────────────
for i, cat in enumerate(categories):
    for xi, yr in zip(x_pos, years):
        pct = pivot_pct.loc[yr, cat]
        if pct > 8:
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
    mticker.FuncFormatter(lambda v, _: fp(f"{int(v)}٪"))
)
ax.set_ylabel(fp("سهم از کل اعتبارات (درصد)"), labelpad=10)

# ── راهنما (legend) ───────────────────────────────────────────────────────────
handles, labels = ax.get_legend_handles_labels()
ax.legend(
    handles[::-1], labels[::-1],
    loc="upper left",
    bbox_to_anchor=(1.01, 1),
    borderaxespad=0,
    fontsize=8.5,
    framealpha=0.8,
    title=fp("دستگاه اجرایی"),
    title_fontsize=9,
)

# ── عنوان و گرید ─────────────────────────────────────────────────────────────
ax.set_title(
    fp("سهم هر دستگاه اجرایی از کل اعتبارات تکلیفی (۱۳۹۸–۱۴۰۵)"),
    pad=16, fontsize=14,
)
ax.grid(axis="y", linestyle="--", alpha=0.4)
ax.grid(axis="x", linestyle=":", alpha=0.2)
ax.set_axisbelow(True)
ax.margins(x=0.03)

fig.tight_layout()

# ── ذخیره ────────────────────────────────────────────────────────────────────
out = CHARTS_DIR / "chart03_dastagah_share.png"
fig.savefig(out, dpi=150, bbox_inches="tight")
plt.close(fig)
print(f"ذخیره شد: {out}")
