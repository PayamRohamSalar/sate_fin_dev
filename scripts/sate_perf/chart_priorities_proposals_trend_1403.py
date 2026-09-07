"""نمودار 7 (نسخه کوتاه) - تعداد اولویت‌ها و پیشنهاده‌ها، فقط از سال 1403 به بعد.

Reuses chart_priorities_proposals_trend.main() with a later start year --
see that module for the data source and its caveats.
"""

import chart_priorities_proposals_trend as base

if __name__ == "__main__":
    base.main(
        min_year=1403,
        output_name="chart07_priorities_proposals_trend_1403",
        subtitle="به تفکیک سال (از ۱۴۰۳)",
    )
