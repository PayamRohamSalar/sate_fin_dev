"""Shared strict date conversion helpers."""

from datetime import date

import jdatetime


def parse_strict_jalali_date(date_str: str) -> date:
    """
    Parse a Jalali date using strict calendar validation.

    Both ``YYYY/MM/DD`` and ``YYYY-MM-DD`` inputs are accepted. Invalid month
    lengths, leap-day values, and malformed inputs raise ``ValueError``.

    Args:
        date_str: Jalali date text entered by a user or loaded from a file.

    Returns:
        The equivalent Gregorian ``date`` value.

    Raises:
        TypeError: If ``date_str`` is not a string.
        ValueError: If the input is empty, malformed, or invalid in the Jalali
            calendar.
    """
    if not isinstance(date_str, str):
        raise TypeError("Jalali date value must be a string.")

    clean_str = date_str.strip().replace("-", "/")
    if not clean_str:
        raise ValueError("Jalali date value cannot be empty.")

    parsed_date = jdatetime.datetime.strptime(clean_str, "%Y/%m/%d").date()
    return parsed_date.togregorian()


def parse_strict_jalali_iso(date_str: str) -> str:
    """
    Parse a Jalali date securely and return Gregorian ISO format.

    Args:
        date_str: Jalali date text in ``YYYY/MM/DD`` or ``YYYY-MM-DD`` format.

    Returns:
        Gregorian date text in ISO ``YYYY-MM-DD`` format.
    """
    return parse_strict_jalali_date(date_str).isoformat()
