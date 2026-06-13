"""Quality-control rules for the WRK (Travail) layer.

Each function mirrors the CASE expression in the corresponding dbt WRK model,
providing a testable Python reference for the SQL business logic.

Return value convention: ``(wrk_stts_cd, rej_cod)``
    - ``('OK', None)``  — row passes all checks
    - ``('REJ', code)`` — row is rejected; code is one of
      ``'NULL_MANDATORY'`` or ``'WRONG_FORMAT'``
"""

from __future__ import annotations

from datetime import datetime


def check_consultation(row: dict[str, object]) -> tuple[str, str | None]:
    """Apply quality rules for a CONSULTATION row.

    Rules (in priority order):
    1. consultation_id must be non-null and > 0
    2. patient_id must be non-null
    3. staff_id must be non-null
    4. started_at must be a non-null datetime
    5. If ended_at is provided, it must be a datetime and >= started_at

    Args:
        row: Dict with keys matching stg_consultation column names.

    Returns:
        Tuple of (wrk_stts_cd, rej_cod). wrk_stts_cd is 'OK' or 'REJ'.
    """
    cid = row.get("consultation_id")
    if cid is None:
        return ("REJ", "NULL_MANDATORY")
    if not _is_numeric(cid) or _to_float(cid) <= 0:
        return ("REJ", "WRONG_FORMAT")
    if row.get("patient_id") is None:
        return ("REJ", "NULL_MANDATORY")
    if row.get("staff_id") is None:
        return ("REJ", "NULL_MANDATORY")
    started = row.get("started_at")
    if started is None:
        return ("REJ", "NULL_MANDATORY")
    if not isinstance(started, datetime):
        return ("REJ", "WRONG_FORMAT")
    ended = row.get("ended_at")
    if ended is None:
        return ("REJ", "NULL_MANDATORY")
    if not isinstance(ended, datetime):
        return ("REJ", "WRONG_FORMAT")
    if ended < started:
        return ("REJ", "WRONG_FORMAT")
    return ("OK", None)


def check_traitement(row: dict[str, object]) -> tuple[str, str | None]:
    """Apply quality rules for a TRAITEMENT row.

    Rules (in priority order):
    1. treatment_id must be non-null and > 0
    2. consultation_id must be non-null
    3. medicine_code must be non-null
    4. medicine_category must be non-null
    5. manufacturer_brand must be non-null

    Args:
        row: Dict with keys matching stg_traitement column names.

    Returns:
        Tuple of (wrk_stts_cd, rej_cod).
    """
    tid = row.get("treatment_id")
    if tid is None:
        return ("REJ", "NULL_MANDATORY")
    if not _is_numeric(tid) or _to_float(tid) <= 0:
        return ("REJ", "WRONG_FORMAT")
    for mandatory in (
        "consultation_id",
        "medicine_code",
        "medicine_category",
        "manufacturer_brand",
        "dosage_description",
    ):
        if row.get(mandatory) is None:
            return ("REJ", "NULL_MANDATORY")
    return ("OK", None)


def check_hospitalisation(row: dict[str, object]) -> tuple[str, str | None]:
    """Apply quality rules for a HOSPITALISATION row.

    Rules (in priority order):
    1. hospi_id must be non-null and > 0
    2. consultation_id must be non-null
    3. room_number must be non-null
    4. started_at must be a non-null datetime
    5. If ended_at is provided, it must be a datetime and >= started_at
    6. If cost is provided, it must be >= 0

    Args:
        row: Dict with keys matching stg_hospitalisation column names.

    Returns:
        Tuple of (wrk_stts_cd, rej_cod).
    """
    hid = row.get("hospi_id")
    if hid is None:
        return ("REJ", "NULL_MANDATORY")
    if not _is_numeric(hid) or _to_float(hid) <= 0:
        return ("REJ", "WRONG_FORMAT")
    if row.get("consultation_id") is None:
        return ("REJ", "NULL_MANDATORY")
    if row.get("room_number") is None:
        return ("REJ", "NULL_MANDATORY")
    if row.get("responsible_staff_id") is None:
        return ("REJ", "NULL_MANDATORY")
    started = row.get("started_at")
    if started is None:
        return ("REJ", "NULL_MANDATORY")
    if not isinstance(started, datetime):
        return ("REJ", "WRONG_FORMAT")
    ended = row.get("ended_at")
    if ended is not None:
        if not isinstance(ended, datetime):
            return ("REJ", "WRONG_FORMAT")
        if ended < started:
            return ("REJ", "WRONG_FORMAT")
    cost = row.get("cost")
    if cost is not None and _is_numeric(cost) and _to_float(cost) < 0:
        return ("REJ", "WRONG_FORMAT")
    return ("OK", None)


def _is_numeric(value: object) -> bool:
    """Return True if value can be coerced to float (bool excluded).

    Args:
        value: Any value to check.

    Returns:
        True if numeric, False otherwise.
    """
    try:
        _to_float(value)
        return True
    except (TypeError, ValueError):
        return False


def _to_float(value: object) -> float:
    """Coerce value to float; raises TypeError / ValueError if impossible.

    bool is explicitly excluded: True/False are not valid numeric IDs.

    Args:
        value: Value to coerce.

    Returns:
        The float representation of value.

    Raises:
        TypeError: If value is bool or cannot be converted.
        ValueError: If value is a non-numeric string.
    """
    if isinstance(value, bool):
        raise TypeError(f"bool is not a valid numeric value: {value!r}")
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        return float(value)
    raise TypeError(f"Cannot convert {type(value).__name__} to float")
