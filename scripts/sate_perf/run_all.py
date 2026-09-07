"""Run every SATE performance-report chart script in order.

Usage: python3 scripts/sate_perf/run_all.py
"""

import runpy
from pathlib import Path

CHART_SCRIPTS = [
    "chart_mandate_trend.py",
    "chart_mandate_share_by_agency.py",
    "chart_top5_agencies_trend.py",
    "chart_top10_companies.py",
    "chart_mandate_vs_deposit.py",
    "chart_priorities_proposals_trend.py",
    "chart_priorities_proposals_trend_1403.py",
    "chart_contracts_trend.py",
    "chart_contracts_trend_2panel.py",
    "chart_payments_trend.py",
    "chart_demand_top_applicants.py",
    "chart_demand_share_by_agency.py",
    "chart_university_top_by_count.py",
    "chart_university_contract_vs_payment.py",
    "chart_researcher_top_by_count.py",
    "chart_researcher_contract_vs_payment.py",
]

HERE = Path(__file__).resolve().parent

for script_name in CHART_SCRIPTS:
    print(f"\n=== {script_name} ===")
    runpy.run_path(str(HERE / script_name), run_name="__main__")
