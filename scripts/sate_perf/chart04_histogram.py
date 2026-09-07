# chart04_histogram.py
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from chart_config import (
    load_data, CHARTS_DIR, COLORS, fp, fmt_num, to_fa_num
)

df = load_data()

YEARS = sorted(df["سال"].unique())
n_cols = 4
n_rows = -(-len(YEARS) // n_cols)  # ceiling division

fig, axes = plt.subplots(n_rows, n_cols, figsize=(16, n_rows * 4))
axes = axes.flatten()

for i, year in enumerate(YEARS):
    ax = axes[i]
    data = df[df["سال"] == year]["اعتبار"]

    ax.hist(
        data,
        bins=30,
        color=COLORS["primary"],
        edgecolor="white",
        linewidth=0.5,
        log=True,
    )

    # خط میانه
    median_val = data.median()
    ax.axvline(median_val, color=COLORS["danger"], linestyle="--", linewidth=1.2)
    ax.text(
        median_val, ax.get_ylim()[1] * 0.9,
        fp(f"میانه: {fmt_num(median_val, 0)}"),
        color=COLORS["danger"], fontsize=8, ha="left", va="top",
    )

    ax.set_title(fp(f"سال {to_fa_num(year)}"), fontsize=12)
    ax.set_xlabel(fp("اعتبار (میلیارد ریال)"), fontsize=9)
    ax.set_ylabel(fp("تعداد مشمول (log)"), fontsize=9)# فرمت محور x با نماد علمی فارسی
    ax.xaxis.set_major_formatter(
        mticker.FuncFormatter(lambda v, _: fp(fmt_num(v, 0)))
    )
    plt.setp(ax.get_xticklabels(), rotation=30, ha="right", fontsize=8)

# پنهان کردن محورهای اضافه
for j in range(len(YEARS), len(axes)):
    axes[j].set_visible(False)

fig.suptitle(
    fp("توزیع فراوانی اعتبارات تکلیفی به تفکیک سال"),
    fontsize=15, y=1.01,
)
plt.tight_layout()
plt.savefig(CHARTS_DIR / "chart04_histogram.png")
plt.close()
print("chart04_histogram.png ذخیره شد.")
