from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib as mpl
from matplotlib.ticker import FuncFormatter

from chart_config import fp, fmt_num, to_fa_num, plt


# =========================================================
# مسیرها
# =========================================================
DATA_PATH = Path("data/Contracts.xlsx")
OUT_DIR = Path("charts")
OUT_DIR.mkdir(parents=True, exist_ok=True)

OUT_PNG = OUT_DIR / "contracts_dashboard.png"
OUT_SVG = OUT_DIR / "contracts_dashboard.svg"


# =========================================================
# تنظیمات عمومی
# =========================================================
# فونت از chart_config.py بارگذاری می‌شود.
# بنابراین اینجا نام فونت‌های دیگر مثل IRANSans را ننویسید.
mpl.rcParams["axes.unicode_minus"] = False


# =========================================================
# خواندن داده
# =========================================================
df = pd.read_excel(DATA_PATH)
df.columns = [str(c).strip() for c in df.columns]

year_col = "سال قرارداد"
count_col = "تعداد قراردادها"
amount_col = "مجموع مبالغ قراردادها_میلیارد ریال"

df = df[[year_col, count_col, amount_col]].copy()
df = df.dropna(subset=[year_col])
df = df.sort_values(year_col)

years = df[year_col].astype(int).astype(str).tolist()
counts = df[count_col].astype(float).to_numpy()
amounts = df[amount_col].astype(float).to_numpy()

x = np.arange(len(years))


# =========================================================
# قالب‌بندی محورهای عددی
# =========================================================
def fa_axis_number(x, pos=None):
    try:
        return fp(to_fa_num(f"{x:,.0f}"))
    except Exception:
        return fp(str(x))


def amount_label(v):
    """
    برچسب مبلغ بالای ستون‌ها.
    برای اعداد بزرگ، بدون اعشار نمایش داده می‌شود.
    """
    try:
        return fp(fmt_num(v, 0))
    except Exception:
        return fp(str(v))


# =========================================================
# رنگ‌ها
# =========================================================
bg = "#F8FAFC"
axis_bg = "#FFFFFF"

bar_color = "#F97316"       # نارنجی برای مبلغ، چون شاخص اصلی است
bar_light = "#FDBA74"
line_color = "#2563EB"      # آبی برای تعداد قراردادها

text_dark = "#111827"
text_muted = "#6B7280"
grid = "#E5E7EB"


# =========================================================
# ساخت شکل
# =========================================================
fig, ax = plt.subplots(
    figsize=(14, 7.5),
    dpi=180,
    constrained_layout=False
)

fig.patch.set_facecolor(bg)
ax.set_facecolor(axis_bg)

fig.subplots_adjust(
    left=0.08,
    right=0.86,
    top=0.80,
    bottom=0.16
)


# =========================================================
# عنوان‌ها
# =========================================================
fig.text(
    0.5,
    0.925,
    fp("روند مبالغ و تعداد قراردادهای منعقد شده"),
    ha="center",
    va="center",
    fontsize=21,
    fontweight="bold",
    color=text_dark
)

fig.text(
    0.5,
    0.875,
    fp("مقایسه سالانه مجموع مبالغ قراردادها و تعداد قراردادهای منعقد شده"),
    ha="center",
    va="center",
    fontsize=12,
    color=text_muted
)


# =========================================================
# نمودار ستونی: مجموع مبالغ قراردادها
# =========================================================
bar_width = 0.50

bars = ax.bar(
    x,
    amounts,
    width=bar_width,
    color=bar_color,
    edgecolor="none",
    zorder=3,
    label=fp("مجموع مبالغ قراردادها")
)

# لایه روشن داخل ستون‌ها برای جلوه بصری بهتر
ax.bar(
    x,
    amounts,
    width=bar_width * 0.45,
    color=bar_light,
    alpha=0.55,
    edgecolor="none",
    zorder=4
)


# =========================================================
# محور دوم: تعداد قراردادها به صورت خطی
# =========================================================
ax2 = ax.twinx()

ax2.plot(
    x,
    counts,
    color=line_color,
    linewidth=3,
    marker="o",
    markersize=7,
    markerfacecolor="white",
    markeredgecolor=line_color,
    markeredgewidth=2,
    zorder=6,
    label=fp("تعداد قراردادها")
)


# =========================================================
# برچسب مبلغ بالای ستون‌ها
# =========================================================
max_amount = np.nanmax(amounts)
max_count = np.nanmax(counts)

for i, bar in enumerate(bars):
    value = bar.get_height()

    ax.text(
        bar.get_x() + bar.get_width() / 2,
        value + max_amount * 0.025,
        amount_label(value),
        ha="center",
        va="bottom",
        fontsize=10,
        fontweight="bold",
        color=text_dark,
        zorder=8
    )


# =========================================================
# محور X
# =========================================================
ax.set_xticks(x)
ax.set_xticklabels(
    [fp(to_fa_num(y)) for y in years],
    fontsize=10.5,
    color=text_dark
)

ax.tick_params(axis="x", length=0, pad=10)


# =========================================================
# محور Y چپ: مبلغ قراردادها
# =========================================================
ax.set_ylabel(
    fp("مجموع مبالغ قراردادها، میلیارد ریال"),
    fontsize=11.5,
    color=text_dark,
    labelpad=18
)

ax.set_ylim(0, max_amount * 1.18)
ax.yaxis.set_major_formatter(FuncFormatter(fa_axis_number))
ax.tick_params(axis="y", labelsize=9.5, colors=text_muted)


# =========================================================
# محور Y راست: تعداد قراردادها
# =========================================================
ax2.set_ylabel(
    fp("تعداد قراردادها"),
    fontsize=11.5,
    color=text_dark,
    labelpad=20
)

ax2.set_ylim(0, max_count * 1.20)
ax2.yaxis.set_major_formatter(FuncFormatter(fa_axis_number))
ax2.tick_params(axis="y", labelsize=9.5, colors=text_muted)


# =========================================================
# گرید و قاب‌ها
# =========================================================
ax.grid(
    axis="y",
    color=grid,
    linewidth=0.9,
    alpha=0.85,
    zorder=0
)

ax.set_axisbelow(True)

for spine in ax.spines.values():
    spine.set_visible(False)

for spine in ax2.spines.values():
    spine.set_visible(False)


# =========================================================
# راهنمای نمودار
# =========================================================
legend_items = [
    mpl.patches.Patch(
        facecolor=bar_color,
        edgecolor="none",
        label=fp("مجموع مبالغ قراردادها")
    ),
    mpl.lines.Line2D(
        [0],
        [0],
        color=line_color,
        marker="o",
        markersize=6,
        linewidth=3,
        markerfacecolor="white",
        markeredgecolor=line_color,
        label=fp("تعداد قراردادها")
    )
]

ax.legend(
    handles=legend_items,
    loc="upper center",
    bbox_to_anchor=(0.5, 1.045),
    frameon=False,
    fontsize=10.5,
    ncol=2,
    columnspacing=2.5,
    handlelength=2.4
)


# =========================================================
# توضیح منبع
# =========================================================
fig.text(
    0.5,
    0.075,
    fp("منبع داده: فایل Contracts.xlsx | مبلغ قراردادها بر حسب میلیارد ریال نمایش داده شده است."),
    ha="center",
    va="center",
    fontsize=9.5,
    color=text_muted
)


# =========================================================
# ذخیره خروجی
# =========================================================
fig.savefig(
    OUT_PNG,
    dpi=300,
    facecolor=bg
)

fig.savefig(
    OUT_SVG,
    facecolor=bg
)

plt.close(fig)

print(f"Saved: {OUT_PNG}")
print(f"Saved: {OUT_SVG}")
