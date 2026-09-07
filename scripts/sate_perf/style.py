"""Shared Persian-chart styling for the SATE performance report (1403-1405).

Carries forward the RTL/Persian-digit rendering helpers proven in the old
SATE_Perf_1405 scripts (``fp``, ``to_fa_num``, ``fmt_num``) plus the visual
language used in the project's newer, more polished charts
(``scripts/sate_perf`` legacy ``contracts.py`` / ``payments.py``): soft panel
background, bold title + muted subtitle via ``fig.text``, value callouts,
and a source footnote.

Amount unit convention
-----------------------
All monetary columns in the database (``AnnualMandate.mandated_amount``,
``DepositReceipt.deposit_amount``, ``Contract.total_amount``,
``Payment.amount``) are stored in base Rials. Every chart here divides by
``RIAL_TO_BILLION`` before plotting so figures read in the report's native
unit, میلیارد ریال (billion Rials).
"""

from pathlib import Path

import arabic_reshaper
import matplotlib.ft2font as _ft2font
import matplotlib.font_manager as fm
import matplotlib.pyplot as plt
from bidi.algorithm import get_display

# Matplotlib wheels built with libraqm (matplotlib >= ~3.8 on Windows/Mac)
# do their own Arabic/Persian shaping and bidi reordering at render time.
# Pre-shaping the text ourselves (arabic_reshaper + python-bidi) in that case
# double-processes it and produces garbled output. Older matplotlib without
# raqm renders complex scripts "dumbly" in logical order, so it still needs
# the manual pre-shape/reorder step. Detect via the raqm-only attribute
# rather than hardcoding a version cutoff.
_MATPLOTLIB_HAS_RAQM = hasattr(_ft2font, "__libraqm_version__")

# ── Paths ──────────────────────────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parents[2]
CHARTS_DIR = PROJECT_ROOT / "results" / "sate_perf" / "charts"
DATA_DIR = PROJECT_ROOT / "results" / "sate_perf" / "data"
FONT_PATH = Path(__file__).resolve().parent / "fonts" / "Vazirmatn-Regular.ttf"

CHARTS_DIR.mkdir(parents=True, exist_ok=True)

RIAL_TO_BILLION = 1_000_000_000

# ── Font ───────────────────────────────────────────────────────────────────
_font_entry = fm.FontEntry(fname=str(FONT_PATH), name="Vazirmatn")
fm.fontManager.ttflist.append(_font_entry)

plt.rcParams.update({
    "font.family": "Vazirmatn",
    "axes.unicode_minus": False,
    "axes.titlesize": 14,
    "axes.labelsize": 12,
    "xtick.labelsize": 10,
    "ytick.labelsize": 10,
    "figure.dpi": 150,
    "savefig.dpi": 300,
    "savefig.bbox": "tight",
})

# ── Colors ───────────────────────────────────────────────────────────────────
COLORS = {
    "primary": "#1F77B4",
    "secondary": "#FF7F0E",
    "accent": "#2CA02C",
    "danger": "#D62728",
    "neutral": "#7F7F7F",
}
CATEGORY_PALETTE = [
    "#1F77B4", "#FF7F0E", "#2CA02C", "#D62728", "#9467BD",
    "#8C564B", "#E377C2", "#7F7F7F", "#BCBD22", "#17BECF",
]

BACKGROUND_COLOR = "#F7F9FC"
PANEL_COLOR = "#FFFFFF"
TEXT_COLOR = "#111827"
MUTED_TEXT_COLOR = "#6B7280"
GRID_COLOR = "#E5E7EB"
HIGHLIGHT_COLOR = "#F97316"


# ── Persian text / number helpers ───────────────────────────────────────────
def fp(text) -> str:
    """Prepare Persian text for matplotlib rendering.

    With a raqm-enabled matplotlib, the raw string is returned as-is --
    matplotlib shapes and bidi-reorders it correctly on its own. Without
    raqm, pre-shape and pre-reorder it manually (see
    ``_MATPLOTLIB_HAS_RAQM`` above).
    """
    text = str(text)
    if _MATPLOTLIB_HAS_RAQM:
        return text
    return get_display(arabic_reshaper.reshape(text))


def to_fa_num(n) -> str:
    fa_digits = str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹")
    return str(n).translate(fa_digits)


def fmt_num(val: float, decimals: int = 1) -> str:
    """Format a number with Persian-digit thousands separators."""
    formatted = f"{val:,.{decimals}f}"
    fa_digits = str.maketrans("0123456789,.", "۰۱۲۳۴۵۶۷۸۹،.")
    return formatted.translate(fa_digits)


def rial_to_billion(value) -> float:
    return float(value) / RIAL_TO_BILLION


# ── Shared figure chrome ─────────────────────────────────────────────────────
def new_figure(figsize=(13, 7.5), dpi=180):
    """Create a figure/axes pair with the shared soft panel background."""
    fig, ax = plt.subplots(figsize=figsize, dpi=dpi)
    fig.patch.set_facecolor(BACKGROUND_COLOR)
    ax.set_facecolor(PANEL_COLOR)
    return fig, ax


def add_title(fig, title: str, subtitle: str | None = None):
    fig.text(0.5, 0.94, fp(title), ha="center", va="center",
              fontsize=20, fontweight="bold", color=TEXT_COLOR)
    if subtitle:
        fig.text(0.5, 0.895, fp(subtitle), ha="center", va="center",
                  fontsize=11.5, color=MUTED_TEXT_COLOR)


def add_source_note(fig, text: str):
    fig.text(0.5, 0.02, fp(text), ha="center", va="center",
              fontsize=9, color=MUTED_TEXT_COLOR)


def style_axes(ax, *, y_grid=True):
    if y_grid:
        ax.grid(axis="y", color=GRID_COLOR, linewidth=0.9, alpha=0.85, zorder=0)
    ax.set_axisbelow(True)
    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.tick_params(axis="x", length=0, pad=8)


def save_fig(fig, name: str):
    """Save a figure as both PNG and SVG under CHARTS_DIR."""
    png_path = CHARTS_DIR / f"{name}.png"
    svg_path = CHARTS_DIR / f"{name}.svg"
    fig.savefig(png_path, facecolor=fig.get_facecolor())
    fig.savefig(svg_path, facecolor=fig.get_facecolor())
    plt.close(fig)
    print(f"Saved: {png_path}")
    print(f"Saved: {svg_path}")
