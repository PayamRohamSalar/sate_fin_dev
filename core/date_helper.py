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


def to_jalali_date(gregorian_date: date) -> jdatetime.date:
    """
    Convert a Gregorian date to its exact Jalali equivalent.

    The sanctioned reverse-direction counterpart to
    ``parse_strict_jalali_date``/``parse_strict_jalali_iso`` above. Use this
    instead of repeating the inline ``jdatetime.date.fromgregorian(...)``
    conversion already present in ``dashboard/views/contract_edit_page.py``
    — a second call site (the stagnant-contracts dashboard) needing the same
    conversion is exactly the trigger the Living Documentation flagged for
    promoting it here.

    Args:
        gregorian_date: A Gregorian ``datetime.date``. Callers must check
            for ``None`` themselves (e.g. a nullable ``contract_date``)
            before calling.

    Returns:
        The equivalent ``jdatetime.date``.

    Raises:
        TypeError: If ``gregorian_date`` is not a ``datetime.date``.
    """
    if not isinstance(gregorian_date, date):
        raise TypeError("gregorian_date must be a datetime.date instance.")
    return jdatetime.date.fromgregorian(date=gregorian_date)


def format_jalali(gregorian_date: date | None, *, empty: str = "—") -> str:
    """
    Format a Gregorian date as a ``YYYY/MM/DD`` Jalali string for display.

    Args:
        gregorian_date: A Gregorian ``datetime.date``, or ``None``.
        empty: Text returned when ``gregorian_date`` is ``None``.

    Returns:
        The Jalali-formatted date string, or ``empty`` if no date was given.
    """
    if gregorian_date is None:
        return empty
    return to_jalali_date(gregorian_date).strftime("%Y/%m/%d")
