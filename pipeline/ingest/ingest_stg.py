"""Load daily hospital flat files into Snowflake STG tables.

The script reads the seven source files for one batch date, stages raw values
in temporary Snowflake tables, then loads the real STG tables with typed SQL.

Usage:
    python pipeline/ingest/ingest_stg.py --batch-date 2026-04-29
"""

from __future__ import annotations

import argparse
import logging
import os
import re
import sys
import time
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path

import snowflake.connector
from dotenv import load_dotenv
from snowflake.connector import SnowflakeConnection
from snowflake.connector.cursor import SnowflakeCursor

sys.path.append(str(Path(__file__).resolve().parents[2]))

from pipeline.utils.logging_config import configure_logging
from pipeline.utils.source_reader import ALL_TABLES, EXPECTED_COLUMNS, read_batch, validate_batch

_LOG_DIR = Path(__file__).resolve().parents[1] / "logs"
_LOG_DIR.mkdir(exist_ok=True)
configure_logging(include_file=str(_LOG_DIR / "ingest_stg.log"))
logger = logging.getLogger(__name__)

_DATABASE = os.getenv("SNOWFLAKE_DATABASE", "HOPITAL_DW")
_SCHEMA = "STG"
_IDENTIFIER_PATTERN = re.compile(r"^[A-Z][A-Z0-9_]*$")
_FULL_LOAD_TABLES = {"CHAMBRE", "MEDICAMENT", "PERSONNEL"}

_PRIMARY_KEYS: dict[str, tuple[str, ...]] = {
    "CHAMBRE": ("NO_CHAMBRE",),
    "MEDICAMENT": ("CD_MEDICAMENT", "CATG_MEDICAMENT", "MARQUE_FABRI"),
    "PERSONNEL": ("ID_PERSONNEL",),
    "PATIENT": ("ID_PATIENT",),
    "CONSULTATION": ("ID_CONSULT",),
    "TRAITEMENT": ("ID_TRAITEMENT",),
    "HOSPITALISATION": ("ID_HOSPI",),
}

_COLUMN_TYPES: dict[str, dict[str, str]] = {
    "CHAMBRE": {
        "NO_CHAMBRE": "integer",
        "NO_ETAGE": "integer",
        "PRIX_JOUR": "integer",
        "DT_CREATION": "date",
    },
    "PERSONNEL": {
        "ID_PERSONNEL": "integer",
        "TS_DEBUT_ACTIVITE": "timestamp",
        "TS_FIN_ACTIVITE": "timestamp",
        "TS_CREATION_PERSONNEL": "timestamp",
        "TS_MAJ_PERSONNEL": "timestamp",
    },
    "PATIENT": {
        "ID_PATIENT": "integer",
        "DT_NAISS": "date",
        "TS_CREATION_PATIENT": "timestamp",
        "TS_MAJ_PATIENT": "timestamp",
    },
    "CONSULTATION": {
        "ID_CONSULT": "integer",
        "ID_PERSONNEL": "integer",
        "ID_PATIENT": "integer",
        "TS_DEBUT_CONSULT": "timestamp",
        "TS_FIN_CONSULT": "timestamp",
        "POIDS_PATIENT": "integer",
        "TEMP_PATIENT": "decimal",
        "TENSION_PATIENT": "integer",
        "INDIC_DIABETE": "boolean",
        "ID_TRAITEMENT": "integer",
        "INDIC_HOSPI": "boolean",
    },
    "TRAITEMENT": {
        "ID_TRAITEMENT": "integer",
        "QTE_MEDICAMENT": "integer",
        "ID_CONSULT": "integer",
        "TS_CREATION_TRAITEMENT": "timestamp",
    },
    "HOSPITALISATION": {
        "ID_HOSPI": "integer",
        "ID_CONSULT": "integer",
        "NO_CHAMBRE": "integer",
        "TS_DEBUT_HOSPI": "timestamp",
        "TS_FIN_HOSPI": "timestamp",
        "COUT_HOSPI": "decimal",
        "ID_PERSONNEL_RESP": "integer",
    },
}

_SOURCE_TO_TARGET: dict[str, dict[str, str]] = {
    table: {column: column for column in EXPECTED_COLUMNS[table]} for table in ALL_TABLES
}
_SOURCE_TO_TARGET["HOSPITALISATION"] = {
    "ID_HOSPI": "ID_HOSPI",
    "ID_CONSULT_hospi": "ID_CONSULT",
    "NO_CHAMBRE_hospi": "NO_CHAMBRE",
    "TS_DEBUT_HOSPI": "TS_DEBUT_HOSPI",
    "TS_FIN_HOSPI": "TS_FIN_HOSPI",
    "COUT_HOSPI": "COUT_HOSPI",
    "ID_PERSONNEL_RESP": "ID_PERSONNEL_RESP",
}

_TYPE_EXPRESSIONS = {
    "varchar": "{value}",
    "integer": "TRY_TO_NUMBER({value})",
    "decimal": "TRY_TO_DECIMAL({value})",
    "date": "TRY_TO_DATE({value})",
    "timestamp": "TRY_TO_TIMESTAMP({value})",
    "boolean": "TRY_TO_BOOLEAN({value})",
}


@dataclass(frozen=True)
class LoadResult:
    """Counters produced by one table load."""

    table: str
    strategy: str
    read_rows: int
    affected_rows: int
    rejected_rows: int
    duration_seconds: float


def parse_batch_date(value: str) -> date:
    """Parse a CLI batch date.

    Args:
        value: Date formatted as YYYY-MM-DD.

    Returns:
        Parsed date.

    Raises:
        argparse.ArgumentTypeError: If the value is not a valid date.
    """
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError as exc:
        raise argparse.ArgumentTypeError("batch date must use YYYY-MM-DD format") from exc


def connect_to_snowflake() -> SnowflakeConnection:
    """Create a Snowflake connection from `.env` variables.

    Returns:
        Open Snowflake connection.
    """
    load_dotenv()
    connection = snowflake.connector.connect(
        user=os.getenv("SNOWFLAKE_USER"),
        password=os.getenv("SNOWFLAKE_PASSWORD"),
        account=os.getenv("SNOWFLAKE_ACCOUNT"),
        warehouse=os.getenv("SNOWFLAKE_WAREHOUSE"),
        role=os.getenv("SNOWFLAKE_ROLE"),
        database=os.getenv("SNOWFLAKE_DATABASE", "HOPITAL_DW"),
        schema=_SCHEMA,
    )
    logger.info("Connected to Snowflake.")
    return connection


def ingest_batch(batch_date: date) -> list[LoadResult]:
    """Load all STG tables for one batch date.

    Args:
        batch_date: Source batch date.

    Returns:
        One load result per table.
    """
    logger.info("Starting STG ingestion for batch_date=%s", batch_date)
    connection = connect_to_snowflake()

    try:
        with connection.cursor() as cursor:
            cursor.execute(f"USE DATABASE {_safe_identifier(_DATABASE)}")
            cursor.execute(f"USE SCHEMA {_SCHEMA}")

        results = [ingest_table(connection, batch_date, table) for table in ALL_TABLES]
        logger.info("STG ingestion completed successfully for batch_date=%s", batch_date)
        return results
    finally:
        connection.close()
        logger.info("Snowflake connection closed.")


def ingest_table(connection: SnowflakeConnection, batch_date: date, table: str) -> LoadResult:
    """Load one source file into one STG table.

    Args:
        connection: Open Snowflake connection.
        batch_date: Source batch date.
        table: Source and STG table name.

    Returns:
        Load counters.
    """
    started_at = time.perf_counter()
    summary = validate_batch(batch_date, table)

    if not summary.is_valid:
        logger.error("Rejected file for table=%s summary=%s", table, summary)
        raise ValueError(f"Invalid source file structure for {table}: {summary}")

    rows = read_batch(batch_date, table)
    temp_table = f"TMP_{table}_{batch_date:%Y%m%d}"

    with connection.cursor() as cursor:
        _create_temp_table(cursor, temp_table, EXPECTED_COLUMNS[table])
        _insert_temp_rows(cursor, temp_table, EXPECTED_COLUMNS[table], rows)
        affected_rows = (
            _load_full(cursor, temp_table, table)
            if _is_full(table)
            else _load_delta(
                cursor,
                temp_table,
                table,
            )
        )

    result = LoadResult(
        table=table,
        strategy="full" if _is_full(table) else "delta",
        read_rows=len(rows),
        affected_rows=affected_rows,
        rejected_rows=0,
        duration_seconds=time.perf_counter() - started_at,
    )
    _log_result(result)
    return result


def _create_temp_table(
    cursor: SnowflakeCursor,
    temp_table: str,
    source_columns: Sequence[str],
) -> None:
    column_sql = ", ".join(f"{_safe_identifier(column)} VARCHAR" for column in source_columns)
    cursor.execute(
        f"CREATE OR REPLACE TEMPORARY TABLE {_safe_identifier(temp_table)} ({column_sql})"
    )


def _insert_temp_rows(
    cursor: SnowflakeCursor,
    temp_table: str,
    source_columns: Sequence[str],
    rows: list[dict[str, str]],
) -> None:
    if not rows:
        return

    placeholders = ", ".join(["%s"] * len(source_columns))
    columns_sql = ", ".join(_safe_identifier(column) for column in source_columns)
    values = [tuple(_empty_to_none(row[column]) for column in source_columns) for row in rows]
    cursor.executemany(
        f"INSERT INTO {_safe_identifier(temp_table)} ({columns_sql}) VALUES ({placeholders})",
        values,
    )


def _load_full(cursor: SnowflakeCursor, temp_table: str, table: str) -> int:
    cursor.execute(f"TRUNCATE TABLE {_qualified_table(table)}")
    cursor.execute(_insert_select_sql(temp_table, table))
    return _affected_row_count(cursor)


def _load_delta(cursor: SnowflakeCursor, temp_table: str, table: str) -> int:
    cursor.execute(_merge_sql(temp_table, table))
    return _affected_row_count(cursor)


def _insert_select_sql(temp_table: str, table: str) -> str:
    columns = _target_columns(table)
    expressions = ", ".join(f"{_typed_expression(table, column)} AS {column}" for column in columns)
    return (
        f"INSERT INTO {_qualified_table(table)} ({', '.join(columns)}) "
        f"SELECT {expressions} FROM {_safe_identifier(temp_table)}"
    )


def _merge_sql(temp_table: str, table: str) -> str:
    columns = _target_columns(table)
    source_select = ", ".join(
        f"{_typed_expression(table, column)} AS {column}" for column in columns
    )
    join_condition = " AND ".join(
        f"target.{column} = source.{column}" for column in _PRIMARY_KEYS[table]
    )
    update_columns = [column for column in columns if column not in _PRIMARY_KEYS[table]]
    update_set = ", ".join(f"target.{column} = source.{column}" for column in update_columns)
    update_condition = (
        " AND source.TS_MAJ_PATIENT > target.TS_MAJ_PATIENT" if table == "PATIENT" else ""
    )

    return (
        f"MERGE INTO {_qualified_table(table)} AS target "
        f"USING (SELECT {source_select} FROM {_safe_identifier(temp_table)}) AS source "
        f"ON {join_condition} "
        f"WHEN MATCHED{update_condition} THEN UPDATE SET {update_set} "
        f"WHEN NOT MATCHED THEN INSERT ({', '.join(columns)}) "
        f"VALUES ({', '.join(f'source.{column}' for column in columns)})"
    )


def _typed_expression(table: str, target_column: str) -> str:
    source_column = _source_column_for(table, target_column)
    raw_value = f"NULLIF({_safe_identifier(source_column)}, '')"
    column_type = _COLUMN_TYPES.get(table, {}).get(target_column, "varchar")
    return _TYPE_EXPRESSIONS[column_type].format(value=raw_value)


def _source_column_for(table: str, target_column: str) -> str:
    for source_column, mapped_target in _SOURCE_TO_TARGET[table].items():
        if mapped_target == target_column:
            return source_column
    raise ValueError(f"No source column mapped to {table}.{target_column}")


def _target_columns(table: str) -> tuple[str, ...]:
    return tuple(_safe_identifier(column) for column in _SOURCE_TO_TARGET[table].values())


def _affected_row_count(cursor: SnowflakeCursor) -> int:
    try:
        row = cursor.fetchone()
    except snowflake.connector.errors.ProgrammingError:
        return _rowcount(cursor)

    if row is None:
        return _rowcount(cursor)

    numeric_values = [value for value in row if isinstance(value, int)]
    return sum(numeric_values) if numeric_values else _rowcount(cursor)


def _rowcount(cursor: SnowflakeCursor) -> int:
    rowcount = cursor.rowcount
    if rowcount is None:
        return 0
    return max(rowcount, 0)


def _safe_identifier(identifier: str) -> str:
    normalized = identifier.upper()
    if not _IDENTIFIER_PATTERN.match(normalized):
        raise ValueError(f"Unsafe Snowflake identifier: {identifier}")
    return normalized


def _qualified_table(table: str) -> str:
    return f"{_SCHEMA}.{_safe_identifier(table)}"


def _empty_to_none(value: str | None) -> str | None:
    return None if value == "" else value


def _is_full(table: str) -> bool:
    return table in _FULL_LOAD_TABLES


def _log_result(result: LoadResult) -> None:
    logger.info(
        "Loaded table=%s strategy=%s read_rows=%d affected_rows=%d rejected_rows=%d duration=%.2fs",
        result.table,
        result.strategy,
        result.read_rows,
        result.affected_rows,
        result.rejected_rows,
        result.duration_seconds,
    )


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line parser.

    Returns:
        Configured parser.
    """
    parser = argparse.ArgumentParser(description="Load daily hospital files into Snowflake STG.")
    parser.add_argument("--batch-date", required=True, type=parse_batch_date)
    return parser


def main() -> None:
    """Run the STG ingestion CLI."""
    args = build_parser().parse_args()
    ingest_batch(args.batch_date)


if __name__ == "__main__":
    main()
