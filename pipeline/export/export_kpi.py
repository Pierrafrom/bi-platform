"""Export KPI views from Snowflake to CSV files.

Queries the six VW-schema views and writes one CSV file per view into the
output directory (default: outputs/kpi/).

Views exported:
    - VW.VW_AVG_AGE_BY_PATHOLOGY
    - VW.VW_TOP_MEDICATION_BY_PATHOLOGY
    - VW.VW_ROOMS_BY_PATHOLOGY
    - VW.VW_DOCTOR_SPECIALITY_BY_PATHOLOGY
    - VW.VW_PATIENTS_ONE_NIGHT
    - VW.VW_EMPTY_ROOMS

Usage:
    python pipeline/export/export_kpi.py [--output-dir outputs/kpi]

Snowflake credentials are read from environment variables (or a .env file):
    SNOWFLAKE_USER, SNOWFLAKE_PASSWORD, SNOWFLAKE_ACCOUNT,
    SNOWFLAKE_WAREHOUSE, SNOWFLAKE_ROLE, SNOWFLAKE_DATABASE
"""

from __future__ import annotations

import argparse
import csv
import logging
import os
import sys
from pathlib import Path

import snowflake.connector
from dotenv import load_dotenv

sys.path.append(str(Path(__file__).resolve().parents[2]))

from pipeline.utils.logging_config import configure_logging

_LOG_DIR = Path(__file__).resolve().parent.parent / "logs"
_DEFAULT_OUTPUT_DIR = Path(__file__).resolve().parents[2] / "outputs" / "kpi"
_DATABASE = os.getenv("SNOWFLAKE_DATABASE", "HOPITAL_DW")
_VW_SCHEMA = "VW"

_KPI_VIEWS: tuple[str, ...] = (
    "VW_AVG_AGE_BY_PATHOLOGY",
    "VW_TOP_MEDICATION_BY_PATHOLOGY",
    "VW_ROOMS_BY_PATHOLOGY",
    "VW_DOCTOR_SPECIALITY_BY_PATHOLOGY",
    "VW_PATIENTS_ONE_NIGHT",
    "VW_EMPTY_ROOMS",
)

load_dotenv()
_LOG_DIR.mkdir(exist_ok=True)
configure_logging(include_file=str(_LOG_DIR / "export_kpi.log"))
logger = logging.getLogger(__name__)


def _get_snowflake_connection() -> snowflake.connector.SnowflakeConnection:
    """Open a Snowflake connection from environment variables.

    Returns:
        An open Snowflake connection targeting the VW schema.

    Raises:
        snowflake.connector.errors.DatabaseError: On connection failure.
    """
    conn = snowflake.connector.connect(
        user=os.getenv("SNOWFLAKE_USER"),
        password=os.getenv("SNOWFLAKE_PASSWORD"),
        account=os.getenv("SNOWFLAKE_ACCOUNT"),
        warehouse=os.getenv("SNOWFLAKE_WAREHOUSE"),
        role=os.getenv("SNOWFLAKE_ROLE"),
        database=_DATABASE,
        schema=_VW_SCHEMA,
    )
    logger.info("Connected to Snowflake (database=%s, schema=%s).", _DATABASE, _VW_SCHEMA)
    return conn


def export_view(
    conn: snowflake.connector.SnowflakeConnection,
    view_name: str,
    output_dir: Path,
) -> int:
    """Export a single Snowflake view to a CSV file.

    Args:
        conn: Open Snowflake connection.
        view_name: Unqualified view name (e.g. 'VW_AVG_AGE_BY_PATHOLOGY').
        output_dir: Directory where the CSV file will be written.

    Returns:
        Number of rows written (excluding the header row).

    Raises:
        snowflake.connector.errors.ProgrammingError: If the query fails.
        OSError: If the output file cannot be written.
    """
    qualified = f"{_VW_SCHEMA}.{view_name}"
    output_path = output_dir / f"{view_name.lower()}.csv"

    logger.info("Exporting %s → %s", qualified, output_path)

    with conn.cursor() as cur:
        cur.execute(f"SELECT * FROM {qualified}")
        columns = [col[0] for col in cur.description]
        rows = cur.fetchall()

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8-sig") as fh:
        writer = csv.writer(fh, delimiter=";")
        writer.writerow(columns)
        writer.writerows(rows)

    logger.info("Exported %d rows from %s.", len(rows), qualified)
    return len(rows)


def run_export(output_dir: Path) -> dict[str, int]:
    """Export all KPI views to CSV files in output_dir.

    Args:
        output_dir: Target directory for the CSV files.

    Returns:
        Mapping of view_name → row_count for each exported view.

    Raises:
        snowflake.connector.errors.DatabaseError: On connection or query failure.
    """
    logger.info("Starting KPI export to %s.", output_dir)
    results: dict[str, int] = {}

    conn = _get_snowflake_connection()
    try:
        for view_name in _KPI_VIEWS:
            row_count = export_view(conn, view_name, output_dir)
            results[view_name] = row_count
    finally:
        conn.close()
        logger.info("Snowflake connection closed.")

    total = sum(results.values())
    logger.info("Export complete. %d views, %d total rows.", len(results), total)
    return results


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse command-line arguments.

    Args:
        argv: Argument list (defaults to sys.argv[1:]).

    Returns:
        Parsed namespace with output_dir attribute.
    """
    parser = argparse.ArgumentParser(description="Export Snowflake KPI views to CSV.")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=_DEFAULT_OUTPUT_DIR,
        help="Directory where CSV files are written (default: outputs/kpi/).",
    )
    return parser.parse_args(argv)


if __name__ == "__main__":
    args = _parse_args()
    run_export(args.output_dir)
