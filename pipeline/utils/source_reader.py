"""Read and validate hospital source flat files from the daily batch folders.

File layout::

    inputs/Data Hospital/BDD_HOSPITAL_YYYYMMDD/TABLE_YYYYMMDD.txt

All files are semicolon-delimited, UTF-8, with a header row.

Usage::

    from datetime import date
    from pipeline.utils.source_reader import read_batch, validate_batch

    rows = read_batch(date(2026, 4, 29), "PATIENT")
    summary = validate_batch(date(2026, 4, 29), "PATIENT")
    print(summary)  # [OK] PATIENT @ 2026-04-29 — 643 rows
"""

from __future__ import annotations

import csv
import logging
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

logger = logging.getLogger(__name__)

# Root of the source data — two levels up from this file (repo root / inputs)
_INPUTS_ROOT: Path = Path(__file__).parents[2] / "inputs" / "Data Hospital"
_DELIMITER: str = ";"
_ENCODING: str = "utf-8"

# Structural contract with the upstream system: expected columns per table.
# Used by validate_batch() to detect schema drift between daily batches.
EXPECTED_COLUMNS: dict[str, tuple[str, ...]] = {
    "PATIENT": (
        "ID_PATIENT",
        "NOM_PATIENT",
        "PRENOM_PATIENT",
        "DT_NAISS",
        "VILLE_NAISS",
        "PAYS_NAISS",
        "NUM_SECU",
        "IND_PAYS_NUM_TELP",
        "NUM_TELEPHONE",
        "NUM_VOIE",
        "DSC_VOIE",
        "CMPL_VOIE",
        "CD_POSTAL",
        "VILLE",
        "PAYS",
        "TS_CREATION_PATIENT",
        "TS_MAJ_PATIENT",
    ),
    "PERSONNEL": (
        "ID_PERSONNEL",
        "NOM_PERSONNEL",
        "PRENOM_PERSONNEL",
        "FONCTION_PERSONNEL",
        "TS_DEBUT_ACTIVITE",
        "TS_FIN_ACTIVITE",
        "RAISON_FIN_ACTIVITE",
        "TS_CREATION_PERSONNEL",
        "TS_MAJ_PERSONNEL",
        "CD_STATUT_PERSONNEL",
    ),
    "CHAMBRE": (
        "NO_CHAMBRE",
        "NOM_CHAMBRE",
        "NO_ETAGE",
        "NOM_BATIMENT",
        "TYPE_CHAMBRE",
        "PRIX_JOUR",
        "DT_CREATION",
    ),
    "MEDICAMENT": (
        "CD_MEDICAMENT",
        "NOM_MEDICAMENT",
        "CONDIT_MEDICAMENT",
        "CATG_MEDICAMENT",
        "MARQUE_FABRI",
    ),
    "CONSULTATION": (
        "ID_CONSULT",
        "ID_PERSONNEL",
        "ID_PATIENT",
        "TS_DEBUT_CONSULT",
        "TS_FIN_CONSULT",
        "POIDS_PATIENT",
        "TEMP_PATIENT",
        "UNIT_TEMP",
        "TENSION_PATIENT",
        "DSC_PATHO",
        "INDIC_DIABETE",
        "ID_TRAITEMENT",
        "INDIC_HOSPI",
    ),
    "TRAITEMENT": (
        "ID_TRAITEMENT",
        "CD_MEDICAMENT",
        "CATG_MEDICAMENT",
        "MARQUE_FABRI",
        "QTE_MEDICAMENT",
        "DSC_POSOLOGIE",
        "ID_CONSULT",
        "TS_CREATION_TRAITEMENT",
    ),
    "HOSPITALISATION": (
        "ID_HOSPI",
        "ID_CONSULT_hospi",
        "NO_CHAMBRE_hospi",
        "TS_DEBUT_HOSPI",
        "TS_FIN_HOSPI",
        "COUT_HOSPI",
        "ID_PERSONNEL_RESP",
    ),
}

ALL_TABLES: tuple[str, ...] = tuple(EXPECTED_COLUMNS)


@dataclass(frozen=True)
class BatchSummary:
    """Outcome of reading and validating one source table from a daily batch.

    Attributes:
        batch_date: Date of the batch folder (e.g. 2026-04-29).
        table: Source table name in uppercase (e.g. ``"PATIENT"``).
        row_count: Number of data rows read (header excluded).
        missing_columns: Expected columns absent from the file header.
        extra_columns: Columns present in the file but not in the contract.
    """

    batch_date: date
    table: str
    row_count: int
    missing_columns: tuple[str, ...] = field(default_factory=tuple)
    extra_columns: tuple[str, ...] = field(default_factory=tuple)

    @property
    def is_valid(self) -> bool:
        """Return True when the file has exactly the contracted columns."""
        return not self.missing_columns and not self.extra_columns

    def __str__(self) -> str:
        status = "OK" if self.is_valid else "INVALID"
        parts = [f"[{status}] {self.table} @ {self.batch_date} — {self.row_count} rows"]
        if self.missing_columns:
            parts.append(f"missing={self.missing_columns}")
        if self.extra_columns:
            parts.append(f"extra={self.extra_columns}")
        return " | ".join(parts)


def batch_folder_path(batch_date: date) -> Path:
    """Return the path to a daily batch folder.

    Args:
        batch_date: Date of the batch.

    Returns:
        Path to ``inputs/Data Hospital/BDD_HOSPITAL_YYYYMMDD/``.
    """
    return _INPUTS_ROOT / batch_date.strftime("BDD_HOSPITAL_%Y%m%d")


def batch_file_path(batch_date: date, table: str) -> Path:
    """Return the path to one source file within a daily batch folder.

    Args:
        batch_date: Date of the batch.
        table: Source table name in uppercase (e.g. ``"PATIENT"``).

    Returns:
        Path to ``TABLE_YYYYMMDD.txt``.
    """
    filename = f"{table}_{batch_date.strftime('%Y%m%d')}.txt"
    return batch_folder_path(batch_date) / filename


def read_batch(batch_date: date, table: str) -> list[dict[str, str]]:
    """Read all rows from one source table for the given batch date.

    Args:
        batch_date: Date of the batch folder.
        table: Source table name in uppercase (e.g. ``"PATIENT"``).

    Returns:
        List of rows as dicts mapping column name to raw string value.

    Raises:
        FileNotFoundError: If the batch folder or file does not exist.
    """
    path = batch_file_path(batch_date, table)
    logger.debug("Reading %s from %s", table, path)

    if not path.exists():
        logger.error("Batch file not found: %s", path)
        raise FileNotFoundError(f"Batch file not found: {path}")

    with path.open(encoding=_ENCODING) as fh:
        rows = list(csv.DictReader(fh, delimiter=_DELIMITER))

    logger.info("Read %d rows — table=%s date=%s", len(rows), table, batch_date)
    return rows


def validate_batch(batch_date: date, table: str) -> BatchSummary:
    """Read a source file and validate its column structure against the contract.

    Args:
        batch_date: Date of the batch folder.
        table: Source table name in uppercase (e.g. ``"PATIENT"``).

    Returns:
        :class:`BatchSummary` with row count and any column discrepancies.

    Raises:
        FileNotFoundError: If the batch file does not exist.
        ValueError: If ``table`` is not in :data:`EXPECTED_COLUMNS`.
    """
    if table not in EXPECTED_COLUMNS:
        raise ValueError(f"Unknown table {table!r}. Valid tables: {list(ALL_TABLES)}")

    rows = read_batch(batch_date, table)

    actual: set[str] = set(rows[0].keys()) if rows else set()
    expected: set[str] = set(EXPECTED_COLUMNS[table])

    summary = BatchSummary(
        batch_date=batch_date,
        table=table,
        row_count=len(rows),
        missing_columns=tuple(sorted(expected - actual)),
        extra_columns=tuple(sorted(actual - expected)),
    )

    if summary.is_valid:
        logger.info("Validation passed — %s", summary)
    else:
        logger.warning("Validation failed  — %s", summary)

    return summary


def validate_all_tables(batch_date: date) -> list[BatchSummary]:
    """Validate all source tables for the given batch date.

    Args:
        batch_date: Date of the batch folder.

    Returns:
        One :class:`BatchSummary` per table, in definition order.
    """
    logger.info("Validating all tables for batch %s", batch_date)
    summaries = [validate_batch(batch_date, table) for table in ALL_TABLES]

    passed = sum(1 for s in summaries if s.is_valid)
    logger.info(
        "Batch %s validation complete — %d/%d tables OK",
        batch_date,
        passed,
        len(summaries),
    )
    return summaries
