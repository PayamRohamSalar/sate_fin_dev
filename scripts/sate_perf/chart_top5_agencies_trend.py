"""نمودار 3 - روند اعتبار تکلیفی پنج دستگاه اجرایی دارای بیشترین سهم.

Source: ``annual_mandates`` joined to ``employers``, grouped by
(fiscal_year, upper_organization). The top-5 agencies are chosen by their
total mandated amount across all years, then plotted as a multi-line trend.
"""

import os
import sys

import numpy as np
from matplotlib.ticker import FuncFormatter
from sqlalchemy import func, select

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from core.database import SessionLocal
from models.employer import Employer
from models.deposits import AnnualMandate
from style import (
    CATEGORY_PALETTE, TEXT_COLOR, MUTED_TEXT_COLOR,
    add_source_note, add_title, fp, new_figure, rial_to_billion,
    save_fig, style_axes, to_fa_num,
)

TOP_N = 5


def fetch_agency_year_matrix():
    db = SessionLocal()
    try:
        rows = db.execute(
            select(
                AnnualMandate.fiscal_year,
                Employer.upper_organization,
                func.sum(AnnualMandate.mandated_amount),
            )
            .select_from(AnnualMandate)
            .join(Employer, AnnualMandate.employer_code == Employer.classification_code)
            .where(
                AnnualMandate.is_deleted == False,  # noqa: E712
                Employer.is_deleted == False,  # noqa: E712
            )
            .group_by(AnnualMandate.fiscal_year, Employer.upper_organization)
        ).all()
    finally:
        db.close()
    return [(int(y), agency or "نامشخص", rial_to_billion(total)) for y, agency, total in rows if total]


def main():
    rows = fetch_agency_year_matrix()
    years = sorted({y for y, _, _ in rows})

    totals_by_agency = {}
    for _, agency, value in rows:
        totals_by_agency[agency] = totals_by_agency.get(agency, 0) + value
    top_agencies = sorted(totals_by_agency, key=totals_by_agency.get, reverse=True)[:TOP_N]

    series = {agency: {y: 0.0 for y in years} for agency in top_agencies}
    for y, agency, value in rows:
        if agency in series:
            series[agency][y] = value

    x = np.arange(len(years))

    fig, ax = new_figure(figsize=(13, 7.5))
    fig.subplots_adjust(left=0.08, right=0.98, top=0.82, bottom=0.14)

    add_title(
        fig,
        "روند اعتبار تکلیفی پنج دستگاه اجرایی دارای بیشترین سهم",
        "بر حسب میلیارد ریال",
    )

    for i, agency in enumerate(top_agencies):
        values = [series[agency][y] for y in years]
        color = CATEGORY_PALETTE[i % len(CATEGORY_PALETTE)]
        ax.plot(x, values, color=color, linewidth=2.6, marker="o", markersize=7,
                markerfacecolor="white", markeredgecolor=color, markeredgewidth=2,
                label=fp(agency), zorder=3)

    ax.set_xticks(x)
    ax.set_xticklabels([fp(to_fa_num(y)) for y in years], fontsize=11)
    ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: fp(to_fa_num(f"{v:,.0f}"))))
    ax.set_ylabel(fp("میلیارد ریال"), fontsize=11, labelpad=14)
    ax.margins(y=0.12)

    style_axes(ax)
    ax.legend(loc="upper left", frameon=False, fontsize=10.5, ncol=1)

    add_source_note(fig, "منبع داده: annual_mandates + employers (پایگاه داده ساتع)")

    save_fig(fig, "chart03_top5_agencies_trend")


if __name__ == "__main__":
    main()
