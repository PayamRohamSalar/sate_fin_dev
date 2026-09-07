# chart04_histogram.py
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from chart_config import load_data, CHARTS_DIR, COLORS, fp, fmt_num, to_fa_num

df = load_data()
YEARS = sorted(df["سال"].unique())

for year in YEARS:
    fig, ax = plt.subplots(figsize=(8, 5))
    data = df[df["سال"] == year]["اعتبار"]

    ax.hist(data, bins=30, color=COLORS["primary"], edgecolor="white", linewidth=0.5)

    median_val = data.median()
    ax.axvline(median_val, color=COLORS["danger"], linestyle="--", linewidth=1.2)
    ax.text(
        median_val, ax.get_ylim()[1] * 0.95,
        fp(f"میانه: {fmt_num(median_val, 0)}"),
        color=COLORS["danger"], fontsize=9, ha="left", va="top",
    )

    ax.set_title(fp(f"توزیع فراوانی اعتبارات — سال {to_fa_num(year)}"), fontsize=13)
    ax.set_xlabel(fp("اعتبار (میلیارد ریال)"), fontsize=10)
    ax.set_ylabel(fp("تعداد مشمول"), fontsize=10)
    ax.xaxis.set_major_formatter(
        mticker.FuncFormatter(lambda v, _: fp(fmt_num(v, 0)))
    )
    plt.setp(ax.get_xticklabels(), rotation=30, ha="right", fontsize=8)

    plt.tight_layout()
    out = CHARTS_DIR / f"chart04_histogram_{year}.png"
    plt.savefig(out)
    plt.close()
    print(f"{out.name} ذخیره شد.")
