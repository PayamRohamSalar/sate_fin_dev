# -*- coding: utf-8 -*-

from pathlib import Path
import math

import numpy as np
import pandas as pd
import matplotlib as mpl
from matplotlib.ticker import MultipleLocator, FuncFormatter

from chart_config import (
    BASE_DIR,
    CHARTS_DIR,
    fp,
    fmt_num,
    to_fa_num,
    plt,
)


# =========================================================
# مسیر فایل‌ها
# =========================================================

DATA_PATH = BASE_DIR / "data" / "Payments.xlsx"

OUTPUT_PNG = CHARTS_DIR / "payments_trend.png"
OUTPUT_SVG = CHARTS_DIR / "payments_trend.svg"

CHARTS_DIR.mkdir(parents=True, exist_ok=True)


# =========================================================
# تنظیمات عمومی
# =========================================================

mpl.rcParams["axes.unicode_minus"] = False


# =========================================================
# خواندن داده‌ها
# =========================================================

df = pd.read_excel(DATA_PATH)

# حذف فاصله‌های احتمالی از نام ستون‌ها
df.columns = [str(column).strip() for column in df.columns]


YEAR_COL = "سال پرداخت"
AMOUNT_COL = "مجموع مبالغ پرداختی_میلیارد ریال"


required_columns = [
    YEAR_COL,
    AMOUNT_COL,
]

missing_columns = [
    column for column in required_columns
    if column not in df.columns
]

if missing_columns:
    raise ValueError(
        "ستون‌های زیر در فایل Payments.xlsx پیدا نشدند:\n"
        + "\n".join(missing_columns)
    )


# انتخاب ستون‌های موردنیاز
df = df[required_columns].copy()


# تبدیل داده‌ها به عدد
df[YEAR_COL] = pd.to_numeric(
    df[YEAR_COL],
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
        AMOUNT_COL,
    ]
)


# مرتب‌سازی بر اساس سال پرداخت
df = df.sort_values(YEAR_COL)


# استخراج مقادیر
years = df[YEAR_COL].astype(int).tolist()
amounts = df[AMOUNT_COL].astype(float).to_numpy()

x = np.arange(len(years))


# =========================================================
# توابع کمکی
# =========================================================

def format_axis_number(value, position=None):
    """
    قالب نمایش اعداد محور عمودی با ارقام فارسی.
    """
    try:
        return fp(fmt_num(value, 0))
    except Exception:
        return fp(str(value))


def format_amount_label(value):
    """
    قالب نمایش برچسب مبلغ روی نمودار.
    اگر مقدار اعشاری ناچیز باشد، بدون اعشار نمایش داده می‌شود.
    """
    try:
        if abs(value - round(value)) < 0.05:
            return fp(fmt_num(value, 0))
        return fp(fmt_num(value, 1))
    except Exception:
        return fp(str(value))


def calculate_axis_limit(values, step, extra_steps=1):
    """
    تعیین سقف محور عمودی به صورت رُند و پویا.
    """
    max_value = float(np.nanmax(values))

    if max_value <= 0:
        return step

    limit = math.ceil(max_value / step) * step
    limit += extra_steps * step

    return limit


# =========================================================
# رنگ‌ها و ظاهر نمودار
# =========================================================

BACKGROUND_COLOR = "#F7F9FC"
PANEL_COLOR = "#FFFFFF"

BAR_COLOR = "#10B981"
BAR_EDGE_COLOR = "#059669"

LINE_COLOR = "#0F172A"
MARKER_FACE_COLOR = "#FFFFFF"

TEXT_COLOR = "#111827"
MUTED_TEXT_COLOR = "#6B7280"
GRID_COLOR = "#E5E7EB"

HIGHLIGHT_COLOR = "#F97316"


# =========================================================
# تعیین مقیاس محور عمودی
# =========================================================

# با توجه به اینکه مقادیر حدود چند صد تا چند هزار میلیارد ریال هستند،
# گام 500 برای محور عمودی خوانایی مناسبی ایجاد می‌کند.
amount_tick_step = 500

amount_axis_limit = calculate_axis_limit(
    amounts,
    step=amount_tick_step,
    extra_steps=1
)


# =========================================================
# ایجاد شکل
# =========================================================

fig, ax = plt.subplots(
    figsize=(13.5, 7.5),
    dpi=180,
)

fig.patch.set_facecolor(BACKGROUND_COLOR)
ax.set_facecolor(PANEL_COLOR)

fig.subplots_adjust(
    left=0.095,
    right=0.94,
    top=0.80,
    bottom=0.18,
)


# =========================================================
# عنوان و زیرعنوان
# =========================================================

fig.text(
    0.5,
    0.92,
    fp("روند مبالغ پرداختی سالانه"),
    ha="center",
    va="center",
    fontsize=21,
    fontweight="bold",
    color=TEXT_COLOR,
)

fig.text(
    0.5,
    0.875,
    fp("مجموع مبالغ پرداخت‌شده بر حسب میلیارد ریال"),
    ha="center",
    va="center",
    fontsize=12,
    color=MUTED_TEXT_COLOR,
)


# =========================================================
# نمودار ستونی
# =========================================================

bars = ax.bar(
    x,
    amounts,
    width=0.52,
    color=BAR_COLOR,
    edgecolor=BAR_EDGE_COLOR,
    linewidth=0.8,
    zorder=3,
)


# =========================================================
# خط روند روی ستون‌ها
# =========================================================

ax.plot(
    x,
    amounts,
    color=LINE_COLOR,
    linewidth=2.8,
    marker="o",
    markersize=8,
    markerfacecolor=MARKER_FACE_COLOR,
    markeredgecolor=LINE_COLOR,
    markeredgewidth=2,
    zorder=5,
)


# =========================================================
# برچسب مقادیر روی ستون‌ها
# =========================================================

for i, (bar, amount) in enumerate(zip(bars, amounts)):

    bar_height = bar.get_height()

    ax.annotate(
        format_amount_label(amount),
        xy=(
            bar.get_x() + bar.get_width() / 2,
            bar_height,
        ),
        xytext=(0, 8),
        textcoords="offset points",
        ha="center",
        va="bottom",
        fontsize=12,
        fontweight="bold",
        color=TEXT_COLOR,
        zorder=8,
    )


# =========================================================
# برجسته‌سازی بیشترین و کمترین مقدار
# =========================================================

max_index = int(np.argmax(amounts))
min_index = int(np.argmin(amounts))

max_value = amounts[max_index]
min_value = amounts[min_index]

# نقطه بیشینه
ax.scatter(
    x[max_index],
    max_value,
    s=105,
    color=HIGHLIGHT_COLOR,
    edgecolor="white",
    linewidth=1.8,
    zorder=7,
)

ax.annotate(
    fp("بیشترین پرداخت"),
    xy=(x[max_index], max_value),
    xytext=(0, 34),
    textcoords="offset points",
    ha="center",
    va="bottom",
    fontsize=9.5,
    fontweight="bold",
    color=HIGHLIGHT_COLOR,
    zorder=9,
    bbox=dict(
        boxstyle="round,pad=0.28",
        facecolor="white",
        edgecolor="none",
        alpha=0.95,
    ),
)

# نقطه کمینه
ax.scatter(
    x[min_index],
    min_value,
    s=85,
    color="#64748B",
    edgecolor="white",
    linewidth=1.6,
    zorder=7,
)

ax.annotate(
    fp("کمترین پرداخت"),
    xy=(x[min_index], min_value),
    xytext=(0, -32),
    textcoords="offset points",
    ha="center",
    va="top",
    fontsize=9.2,
    fontweight="bold",
    color="#475569",
    zorder=9,
    bbox=dict(
        boxstyle="round,pad=0.25",
        facecolor="white",
        edgecolor="none",
        alpha=0.95,
    ),
)


# =========================================================
# تنظیم محور افقی
# =========================================================

ax.set_xticks(x)

ax.set_xticklabels(
    [
        fp(to_fa_num(year))
        for year in years
    ],
    fontsize=11,
    color=TEXT_COLOR,
)

ax.tick_params(
    axis="x",
    length=0,
    pad=10,
)


# =========================================================
# تنظیم محور عمودی
# =========================================================

ax.set_ylabel(
    fp("مجموع مبالغ پرداختی\n(میلیارد ریال)"),
    fontsize=11,
    color=TEXT_COLOR,
    labelpad=18,
)

ax.set_ylim(
    0,
    amount_axis_limit
)

ax.yaxis.set_major_locator(
    MultipleLocator(amount_tick_step)
)

ax.yaxis.set_major_formatter(
    FuncFormatter(format_axis_number)
)

ax.tick_params(
    axis="y",
    labelsize=9.5,
    colors=MUTED_TEXT_COLOR,
)


# =========================================================
# شبکه و قاب نمودار
# =========================================================

ax.grid(
    axis="y",
    color=GRID_COLOR,
    linewidth=0.85,
    alpha=0.9,
    zorder=0,
)

ax.set_axisbelow(True)

ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.spines["left"].set_visible(False)
ax.spines["bottom"].set_visible(False)


# =========================================================
# راهنمای نمودار
# =========================================================

bar_proxy = mpl.patches.Patch(
    color=BAR_COLOR,
    label=fp("مبلغ پرداختی سالانه"),
)

line_proxy = mpl.lines.Line2D(
    [0],
    [0],
    color=LINE_COLOR,
    linewidth=2.8,
    marker="o",
    markersize=7,
    markerfacecolor=MARKER_FACE_COLOR,
    markeredgecolor=LINE_COLOR,
    label=fp("روند پرداخت‌ها"),
)

fig.legend(
    handles=[
        bar_proxy,
        line_proxy,
    ],
    loc="upper center",
    bbox_to_anchor=(0.5, 0.835),
    ncol=2,
    frameon=False,
    fontsize=10.5,
    columnspacing=2.5,
    handlelength=2.6,
)


# =========================================================
# پانویس
# =========================================================

fig.text(
    0.5,
    0.075,
    fp(
        "منبع داده: فایل Payments.xlsx | "
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

print("نمودار مبالغ پرداختی سالانه با موفقیت ذخیره شد:")
print(f"PNG: {OUTPUT_PNG}")
print(f"SVG: {OUTPUT_SVG}")
print(f"بازه محور مبلغ: 0 تا {amount_axis_limit:,.0f} میلیارد ریال")
