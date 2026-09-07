# chart08_dastagah_pie_1405.py
import numpy as np

from chart_config import (
    load_data, fp, fmt_num, to_fa_num, CHARTS_DIR, CATEGORY_PALETTE, COLORS, plt
)


def _fa_pct(pct):
    if pct >= 5:
        return fp(f"{to_fa_num(f'{pct:.1f}')}٪")
    return ""


df = load_data()
df_1405 = df[df["سال"] == 1405]

budget_by_agency = (
    df_1405.groupby("دستگاه اجرایی مرتبط")["اعتبار"]
    .sum()
    .sort_values(ascending=False)
)

total_budget = budget_by_agency.sum()
shares = budget_by_agency / total_budget * 100

small_agencies = shares[shares < 2].index
if len(small_agencies) > 0:
    other_total = budget_by_agency.loc[small_agencies].sum()
    budget_by_agency = budget_by_agency.drop(index=small_agencies)
    budget_by_agency.loc["سایر"] = other_total
    budget_by_agency = budget_by_agency.sort_values(ascending=False)

labels = budget_by_agency.index.tolist()
values = budget_by_agency.to_numpy()
percentages = values / values.sum() * 100
colors = (CATEGORY_PALETTE * ((len(labels) // len(CATEGORY_PALETTE)) + 1))[
    : len(labels)
]

fig, ax = plt.subplots(figsize=(11, 8))

wedges, _, autotexts = ax.pie(
    values,
    colors=colors,
    startangle=90,
    counterclock=False,
    autopct=_fa_pct,
    pctdistance=0.72,
    wedgeprops=dict(width=0.55, edgecolor="white", linewidth=1.5),
)

for autotext in autotexts:
    autotext.set_color("white")
    autotext.set_fontsize(13)
    autotext.set_fontweight("bold")

for wedge, label, pct in zip(wedges, labels, percentages):
    if pct >= 5:
        continue

    angle = (wedge.theta1 + wedge.theta2) / 2
    x = np.cos(np.deg2rad(angle))
    y = np.sin(np.deg2rad(angle))
    ha = "left" if x >= 0 else "right"

    ax.annotate(
        fp(f"{label} — {fmt_num(pct, 1)}٪"),
        xy=(0.78 * x, 0.78 * y),
        xytext=(1.18 * x, 1.18 * y),
        ha=ha,
        va="center",
        fontsize=10,
        color=COLORS["neutral"],
        arrowprops=dict(arrowstyle="-", color="gray"),
    )

ax.text(
    0,
    0.08,
    fp("سال"),
    ha="center",
    fontsize=13,
    color=COLORS["neutral"],
)
ax.text(
    0,
    -0.15,
    fp("۱۴۰۵"),
    ha="center",
    fontsize=22,
    fontweight="bold",
    color=COLORS["primary"],
)

labels_fp = [
    fp(f"{name} — {fmt_num(pct, 1)}٪")
    for name, pct in zip(labels, percentages)
]
ax.legend(
    wedges,
    labels_fp,
    loc="center left",
    bbox_to_anchor=(1.05, 0.5),
    fontsize=11,
    framealpha=0.8,
    title=fp("دستگاه اجرایی"),
    title_fontsize=12,
)

ax.set_title(
    fp("توزیع اعتبارات تکلیفی بر اساس دستگاه اجرایی — سال ۱۴۰۵"),
    fontsize=18,
    pad=20,
)
ax.set_aspect("equal")

fig.tight_layout()

out = CHARTS_DIR / "chart08_dastagah_pie_1405.png"
fig.savefig(out, dpi=150, bbox_inches="tight")
plt.close(fig)
print(f"ذخیره شد: {out}")
