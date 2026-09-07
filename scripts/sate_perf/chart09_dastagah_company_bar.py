# chart09_dastagah_company_bar.py
from chart_config import (
    load_data, fp, to_fa_num, CHARTS_DIR,
    CATEGORY_PALETTE, plt
)
import matplotlib.ticker as mticker
from matplotlib.patches import Patch
import numpy as np

df = load_data()
df_1405 = df[df["سال"] == 1405].copy()
df_1405 = df_1405.dropna(subset=["دستگاه اجرایی مرتبط", "نام مشمول", "اعتبار"])

# ── آماده‌سازی داده ──────────────────────────────────────────────────────────
by_company = (
    df_1405.groupby(["دستگاه اجرایی مرتبط", "نام مشمول"])["اعتبار"]
    .sum()
    .reset_index()
)

dastagah_totals = (
    by_company.groupby("دستگاه اجرایی مرتبط")["اعتبار"]
    .sum()
    .sort_values(ascending=False)
)
dastagah_totals = dastagah_totals[dastagah_totals > 0]
dastagah_order = dastagah_totals.index.tolist()

rows = []
for dastagah in dastagah_order:
    group = (
        by_company[by_company["دستگاه اجرایی مرتبط"] == dastagah]
        .sort_values("اعتبار", ascending=False)
        .reset_index(drop=True)
    )
    total = dastagah_totals.loc[dastagah]
    top_companies = group.head(4)

    for rank, row in enumerate(top_companies.itertuples(index=False), start=1):
        rows.append({
            "دستگاه اجرایی مرتبط": dastagah,
            "نام مشمول": row[1],
            "رتبه": rank,
            "اعتبار": row[2],
            "سهم": row[2] / total * 100,
        })

    other_total = group.iloc[4:]["اعتبار"].sum()
    rows.append({
        "دستگاه اجرایی مرتبط": dastagah,
        "نام مشمول": "سایرین",
        "رتبه": 5,
        "اعتبار": other_total,
        "سهم": other_total / total * 100,
    })

segments = {rank: np.zeros(len(dastagah_order)) for rank in range(1, 6)}
for row in rows:
    index = dastagah_order.index(row["دستگاه اجرایی مرتبط"])
    segments[row["رتبه"]][index] = row["سهم"]

# ── رسم ──────────────────────────────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(14, 8))
y = np.arange(len(dastagah_order))
left = np.zeros(len(dastagah_order))
colors = [
    CATEGORY_PALETTE[0],
    CATEGORY_PALETTE[1],
    CATEGORY_PALETTE[2],
    CATEGORY_PALETTE[3],
    CATEGORY_PALETTE[7],
]

for rank, color in zip(range(1, 6), colors):
    widths = segments[rank]
    ax.barh(y, widths, left=left, color=color, height=0.72, zorder=2)

    for y_pos, segment_left, width in zip(y, left, widths):
        if width > 6:
            ax.text(
                segment_left + width / 2,
                y_pos,
                fp(f"{to_fa_num(f'{width:.0f}')}٪"),
                ha="center",
                va="center",
                color="white",
                fontsize=10,
                fontweight="bold",
                zorder=3,
            )

    left += widths

# ── محورها و چیدمان ─────────────────────────────────────────────────────────
ax.set_yticks(y)
ax.set_yticklabels([fp(name) for name in dastagah_order], fontsize=11)
ax.invert_yaxis()

ax.set_xlim(0, 100)
ax.set_xlabel(fp("درصد اعتبار"), fontsize=11, labelpad=10)
ax.xaxis.set_major_formatter(
    mticker.FuncFormatter(lambda value, _: fp(f"{to_fa_num(int(value))}٪"))
)

ax.set_title(
    fp("سهم شرکت‌ها در هر دستگاه اجرایی — ۱۴۰۵"),
    fontsize=18,
    fontweight="bold",
    pad=16,
)
ax.grid(axis="y", linestyle="-", linewidth=0.6, alpha=0.3, zorder=0)
ax.set_axisbelow(True)

# ── راهنما ───────────────────────────────────────────────────────────────────
legend_elements = [
    Patch(facecolor=CATEGORY_PALETTE[0], label=fp("اول")),
    Patch(facecolor=CATEGORY_PALETTE[1], label=fp("دوم")),
    Patch(facecolor=CATEGORY_PALETTE[2], label=fp("سوم")),
    Patch(facecolor=CATEGORY_PALETTE[3], label=fp("چهارم")),
    Patch(facecolor=CATEGORY_PALETTE[7], label=fp("سایرین")),
]
ax.legend(
    handles=legend_elements,
    loc="upper left",
    bbox_to_anchor=(1.01, 1),
    title=fp("رتبه شرکت در دستگاه"),
    fontsize=11,
    title_fontsize=12,
    framealpha=0.8,
)

fig.tight_layout()

# ── ذخیره ────────────────────────────────────────────────────────────────────
out = CHARTS_DIR / "chart09_dastagah_company_bar.png"
fig.savefig(out, dpi=150, bbox_inches="tight")
plt.close(fig)
print("Chart 09 saved.")
