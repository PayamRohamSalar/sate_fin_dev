# chart_config.py
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import matplotlib.ticker as mticker
import arabic_reshaper
from bidi.algorithm import get_display

# ── مسیرها ──────────────────────────────────────────────────────────────────
BASE_DIR   = Path(r"D:\OneDrive\AI-Project\SATE_Perf_1405")
DATA_FILE  = BASE_DIR / "data" / "budget_data.xlsx"
CHARTS_DIR = BASE_DIR / "charts"
FONT_PATH  = BASE_DIR / "fonts" / "Vazirmatn-Regular.ttf"

CHARTS_DIR.mkdir(parents=True, exist_ok=True)

# ── فونت ────────────────────────────────────────────────────────────────────
_font_entry = fm.FontEntry(fname=str(FONT_PATH), name="Vazirmatn")
fm.fontManager.ttflist.append(_font_entry)

plt.rcParams.update({
    "font.family":       "Vazirmatn",
    "axes.titlesize":    14,
    "axes.labelsize":    12,
    "xtick.labelsize":   10,
    "ytick.labelsize":   10,
    "figure.dpi":        150,
    "savefig.dpi":       150,
    "savefig.bbox":      "tight",
})

# ── رنگ‌ها ───────────────────────────────────────────────────────────────────
COLORS = {
    "primary":   "#1F77B4",
    "secondary": "#FF7F0E",
    "accent":    "#2CA02C",
    "danger":    "#D62728",
    "neutral":   "#7F7F7F",
}
CATEGORY_PALETTE = [
    "#1F77B4","#FF7F0E","#2CA02C","#D62728","#9467BD",
    "#8C564B","#E377C2","#7F7F7F","#BCBD22","#17BECF",
]

# ── توابع متن فارسی ──────────────────────────────────────────────────────────
def fp(text: str) -> str:
    """متن فارسی را برای matplotlib آماده می‌کند."""
    return get_display(arabic_reshaper.reshape(str(text)))

def to_fa_num(n) -> str:
    fa_digits = str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹")
    return str(n).translate(fa_digits)

def fmt_num(val: float, decimals: int = 1) -> str:
    """عدد را با جداکننده هزارگان فارسی فرمت می‌کند."""
    formatted = f"{val:,.{decimals}f}"
    fa_digits = str.maketrans("0123456789,.", "۰۱۲۳۴۵۶۷۸۹،.")
    return formatted.translate(fa_digits)

def fa_year_formatter(val, pos=None) -> str:
    return to_fa_num(int(val))

def make_y_formatter(unit: str = "میلیارد ریال"):
    def _fmt(val, pos=None):
        return fp(f"{fmt_num(val)} {unit}")
    return _fmt

# ── تنظیم RTL ────────────────────────────────────────────────────────────────
def set_rtl_labels(ax):
    ax.set_xticklabels([fp(t.get_text()) for t in ax.get_xticklabels()], ha="center")
    ax.set_yticklabels([fp(t.get_text()) for t in ax.get_yticklabels()], ha="right")

# ── بارگذاری و تبدیل داده ────────────────────────────────────────────────────
YEAR_COLS = [f"سال {y}" for y in [1398, 1399, 1400, 1401, 1402, 1404, 1405]]
ID_VARS   = ["شماره طبقه بندی", "نام مشمول", "عنوان امور", "دستگاه اجرایی مرتبط"]

def load_data() -> pd.DataFrame:
    df_wide = pd.read_excel(DATA_FILE)

    # تبدیل Wide → Long
    df = df_wide.melt(
        id_vars=ID_VARS,
        value_vars=YEAR_COLS,
        var_name="سال_متن",
        value_name="اعتبار",
    )

    # استخراج عدد سال
    df["سال"] = df["سال_متن"].str.extract(r"(\d{4})").astype(int)
    df = df.drop(columns=["سال_متن"])

    # حذف ردیف‌های بدون اعتبار
    df = df[df["اعتبار"].notna() & (df["اعتبار"] > 0)].copy()
    df["اعتبار"] = pd.to_numeric(df["اعتبار"], errors="coerce")

    return df.reset_index(drop=True)
