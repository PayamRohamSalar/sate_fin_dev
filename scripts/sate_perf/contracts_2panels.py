# -*- coding: utf-8 -*-

from pathlib import Path
import math

import numpy as np
import pandas as pd
import matplotlib as mpl
import matplotlib.patches as mpatches
from matplotlib.ticker import MultipleLocator, FuncFormatter

# ---------------------------------------------------------
# استفاده از تنظیمات پروژه
# ---------------------------------------------------------
from chart_config import (
    BASE_DIR,
    CHARTS_DIR,
    fp,
    fmt_num,
    to_fa_num,
    plt,
)


# =========================================================
# تنظیم مسیر فایل‌ها
# =========================================================

DATA_PATH = BASE_DIR / "data" / "Contracts.xlsx"

OUTPUT_PNG = CHARTS_DIR / "contracts_dashboard_2panel.png"
OUTPUT_SVG = CHARTS_DIR / "contracts_dashboard_2panel.svg"

CHARTS_DIR.mkdir(parents=True, exist_ok=True)


# =========================================================
# تنظیمات عمومی Matplotlib
# =========================================================

mpl.rcParams["axes.unicode_minus"] = False

# فونت Vazirmatn در chart_config.py بارگذاری شده است.
# بنابراین در این فایل نیازی به استفاده از IRANSans نیست.


# =========================================================
# بارگذاری داده‌ها
# =========================================================

df = pd.read_excel(DATA_PATH)

# حذف فاصله‌های احتمالی از نام ستون‌ها
df.columns = [str(column).strip() for column in df.columns]


# نام ستون‌های فایل Contracts.xlsx
YEAR_COL = "سال قرارداد"
COUNT_COL = "تعداد قراردادها"
AMOUNT_COL = "مجموع مبالغ قراردادها_میلیارد ریال"


# بررسی وجود ستون‌های موردنیاز
required_columns = [
    YEAR_COL,
    COUNT_COL,
    AMOUNT_COL,
]

missing_columns = [
    column for column in required_columns
    if column not in df.columns
]

if missing_columns:
    raise ValueError(
        "ستون‌های زیر در فایل Contracts.xlsx پیدا نشدند:\n"
        + "\n".join(missing_columns)
    )


# انتخاب ستون‌های موردنیاز
df = df[required_columns].copy()


# تبدیل مقادیر عددی
df[YEAR_COL] = pd.to_numeric(
    df[YEAR_COL],
    errors="coerce"
)

df[COUNT_COL] = pd.to_numeric(
    df[COUNT_COL],
    errors="coerce"
)

df[AMOUNT_COL] = pd.to_numeric(
    df[AMOUNT_COL],
    errors="coerce"
)


# حذف ردیف‌های ناقص
df = df.dropna(
    subset=[
        YEAR_COL,
        COUNT_COL,
        AMOUNT_COL,
    ]
)


# مرتب‌سازی بر اساس سال
df = df.sort_values(YEAR_COL)


# استخراج داده‌ها
years = df[YEAR_COL].astype(int).tolist()
counts = df[COUNT_COL].astype(float).to_numpy()
amounts = df[AMOUNT_COL].astype(float).to_numpy()

x = np.arange(len(years))


# =========================================================
# توابع کمکی
# =========================================================

def format_axis_number(value, position=None):
    """
    قالب نمایش اعداد محورهای عمودی با ارقام فارسی.
    """
    try:
        return fp(fmt_num(value, 0))
    except Exception:
        return fp(str(value))


def format_amount(value):
    """
    قالب نمایش مبلغ قراردادها.
    """
    try:
        return fp(fmt_num(value, 0))
    except Exception:
        return fp(str(value))


def format_count(value):
    """
    قالب نمایش تعداد قراردادها.
    """
    try:
        return fp(fmt_num(value, 0))
    except Exception:
        return fp(str(value))


def calculate_axis_limit(values, step, extra_steps=1):
    """
    تعیین سقف محور به‌صورت پویا و رُند.

    مثال:
    اگر بیشترین مبلغ 5120 باشد و step برابر 1000 باشد،
    سقف محور 6000 در نظر گرفته می‌شود.
    """
    max_value = float(np.nanmax(values))

    if max_value <= 0:
        return step

    limit = math.ceil(max_value / step) * step

    # فضای اضافه برای برچسب‌های بالای نمودار
    limit += extra_steps * step

    return limit


# =========================================================
# رنگ‌ها و تنظیمات ظاهری
# =========================================================

BACKGROUND_COLOR = "#F7F9FC"
PANEL_COLOR = "#FFFFFF"

AMOUNT_COLOR = "#F97316"
AMOUNT_EDGE_COLOR = "#EA580C"

COUNT_COLOR = "#2563EB"
COUNT_FILL_COLOR = "#93C5FD"

TEXT_COLOR = "#111827"
MUTED_TEXT_COLOR = "#6B7280"
GRID_COLOR = "#E5E7EB"


# =========================================================
# تعیین مقیاس محورها
# =========================================================

# با توجه به داده‌های موجود:
# مبلغ‌ها در بازه چند هزار میلیارد ریال هستند.
# تعداد قراردادها در بازه چند صد قرارداد است.

amount_tick_step = 1000
count_tick_step = 100

amount_axis_limit = calculate_axis_limit(
    amounts,
    step=amount_tick_step,
    extra_steps=1
)

count_axis_limit = calculate_axis_limit(
    counts,
    step=count_tick_step,
    extra_steps=1
)


# =========================================================
# ایجاد شکل دوپنلی
# =========================================================

fig, (ax_amount, ax_count) = plt.subplots(
    nrows=2,
    ncols=1,
    figsize=(14, 9),
    dpi=180,
    sharex=True,
    gridspec_kw={
        "height_ratios": [2.15, 1.15],
        "hspace": 0.08,
    }
)

fig.patch.set_facecolor(BACKGROUND_COLOR)

ax_amount.set_facecolor(PANEL_COLOR)
ax_count.set_facecolor(PANEL_COLOR)


# تنظیم حاشیه‌ها
fig.subplots_adjust(
    left=0.105,
    right=0.91,
    top=0.83,
    bottom=0.15,
)


# =========================================================
# عنوان اصلی
# =========================================================

fig.text(
    0.5,
    0.935,
    fp("روند مبالغ و تعداد قراردادهای منعقد شده"),
    ha="center",
    va="center",
    fontsize=21,
    fontweight="bold",
    color=TEXT_COLOR,
)

fig.text(
    0.5,
    0.895,
    fp("مقایسه سالانه مجموع مبالغ قراردادها و تعداد قراردادهای منعقد شده"),
    ha="center",
    va="center",
    fontsize=11.5,
    color=MUTED_TEXT_COLOR,
)


# =========================================================
# پنل اول: مجموع مبالغ قراردادها
# =========================================================

bars = ax_amount.bar(
    x,
    amounts,
    width=0.52,
    color=AMOUNT_COLOR,
    edgecolor=AMOUNT_EDGE_COLOR,
    linewidth=0.7,
    zorder=3,
)


# برچسب مبلغ بالای هر ستون
for bar, amount in zip(bars, amounts):

    bar_height = bar.get_height()

    ax_amount.annotate(
        format_amount(amount),
        xy=(
            bar.get_x() + bar.get_width() / 2,
            bar_height,
        ),
        xytext=(0, 7),
        textcoords="offset points",
        ha="center",
        va="bottom",
        fontsize=10,
        fontweight="bold",
        color=TEXT_COLOR,
        zorder=8,
    )


# عنوان محور مبلغ
ax_amount.set_ylabel(
    fp("مجموع مبالغ قراردادها\n(میلیارد ریال)"),
    fontsize=11,
    color=TEXT_COLOR,
    labelpad=16,
)


# مقیاس محور مبلغ
ax_amount.set_ylim(
    0,
    amount_axis_limit
)

ax_amount.yaxis.set_major_locator(
    MultipleLocator(amount_tick_step)
)

ax_amount.yaxis.set_major_formatter(
    FuncFormatter(format_axis_number)
)

ax_amount.tick_params(
    axis="y",
    labelsize=9.5,
    colors=MUTED_TEXT_COLOR,
)


# =========================================================
# پنل دوم: تعداد قراردادها
# =========================================================

ax_count.plot(
    x,
    counts,
    color=COUNT_COLOR,
    linewidth=3,
    marker="o",
    markersize=8,
    markerfacecolor="white",
    markeredgecolor=COUNT_COLOR,
    markeredgewidth=2,
    zorder=5,
)


# ناحیه بسیار کم‌رنگ زیر خط برای زیبایی بصری
ax_count.fill_between(
    x,
    counts,
    0,
    color=COUNT_FILL_COLOR,
    alpha=0.16,
    zorder=1,
)


# برچسب تعداد قراردادها روی نقاط
for i, (x_value, count) in enumerate(zip(x, counts)):

    # برای جلوگیری از تراکم بیش از حد،
    # محل برچسب‌ها به‌صورت متناوب تغییر می‌کند.
    if i % 2 == 0:
        offset_y = 10
        vertical_alignment = "bottom"
    else:
        offset_y = -12
        vertical_alignment = "top"

    ax_count.annotate(
        format_count(count),
        xy=(x_value, count),
        xytext=(0, offset_y),
        textcoords="offset points",
        ha="center",
        va=vertical_alignment,
        fontsize=9.5,
        fontweight="bold",
        color=COUNT_COLOR,
        zorder=8,
        bbox=dict(
            boxstyle="round,pad=0.22",
            facecolor="white",
            edgecolor="none",
            alpha=0.90,
        ),
    )


# عنوان محور تعداد
ax_count.set_ylabel(
    fp("تعداد قراردادها"),
    fontsize=11,
    color=TEXT_COLOR,
    labelpad=16,
)


# مقیاس محور تعداد
ax_count.set_ylim(
    0,
    count_axis_limit
)

ax_count.yaxis.set_major_locator(
    MultipleLocator(count_tick_step)
)

ax_count.yaxis.set_major_formatter(
    FuncFormatter(format_axis_number)
)

ax_count.tick_params(
    axis="y",
    labelsize=9.5,
    colors=MUTED_TEXT_COLOR,
)


# =========================================================
# محور افقی مشترک
# =========================================================

ax_count.set_xticks(x)

ax_count.set_xticklabels(
    [
        fp(to_fa_num(year))
        for year in years
    ],
    fontsize=10.5,
    color=TEXT_COLOR,
)

ax_count.tick_params(
    axis="x",
    length=0,
    pad=10,
)

ax_amount.tick_params(
    axis="x",
    bottom=False,
    labelbottom=False,
)


# =========================================================
# شبکه و ظاهر محورها
# =========================================================

for ax in [ax_amount, ax_count]:

    ax.grid(
        axis="y",
        color=GRID_COLOR,
        linewidth=0.85,
        alpha=0.9,
        zorder=0,
    )

    ax.set_axisbelow(True)

    # حذف قاب‌های غیرضروری
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_visible(False)
    ax.spines["bottom"].set_visible(False)


# =========================================================
# راهنمای نمودار
# =========================================================

amount_legend = mpatches.Patch(
    color=AMOUNT_COLOR,
    label=fp("مجموع مبالغ قراردادها"),
)

count_legend = mpl.lines.Line2D(
    [0],
    [0],
    color=COUNT_COLOR,
    linewidth=3,
    marker="o",
    markersize=7,
    markerfacecolor="white",
    markeredgecolor=COUNT_COLOR,
    label=fp("تعداد قراردادها"),
)


fig.legend(
    handles=[
        amount_legend,
        count_legend,
    ],
    loc="upper center",
    bbox_to_anchor=(0.5, 0.865),
    ncol=2,
    frameon=False,
    fontsize=10.5,
    columnspacing=2.5,
    handlelength=2.5,
)


# =========================================================
# توضیح منبع
# =========================================================

fig.text(
    0.5,
    0.055,
    fp(
        "منبع داده: فایل Contracts.xlsx | "
        "مبالغ بر حسب میلیارد ریال نمایش داده شده‌اند."
    ),
    ha="center",
    va="center",
    fontsize=9.5,
    color=MUTED_TEXT_COLOR,
)


# =========================================================
# ذخیره خروجی
# =========================================================

fig.savefig(
    OUTPUT_PNG,
    dpi=300,
    facecolor=BACKGROUND_COLOR,
    bbox_inches="tight",
)

fig.savefig(
    OUTPUT_SVG,
    facecolor=BACKGROUND_COLOR,
    bbox_inches="tight",
)

plt.close(fig)

print("نمودار دوپنلی با موفقیت ذخیره شد:")
print(f"PNG: {OUTPUT_PNG}")
print(f"SVG: {OUTPUT_SVG}")
print(f"بازه مبلغ: 0 تا {amount_axis_limit:,.0f}")
print(f"بازه تعداد: 0 تا {count_axis_limit:,.0f}")
