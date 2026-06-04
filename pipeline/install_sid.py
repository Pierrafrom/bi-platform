"""Install the hospital SID (Snowflake Information System) schema.

Runs the three idempotent DDL scripts in order against the Snowflake account
configured via environment variables:

    1. 00_create_databases.sql — databases and warehouses (idempotent)
    2. 01_create_stg_tables.sql — STG tables (always recreated)
    3. 06_create_tch_tables.sql — TCH tracking tables (never recreated)

Usage:
    python pipeline/install_sid.py

Snowflake credentials are read from environment variables (or a .env file):
    SNOWFLAKE_USER, SNOWFLAKE_PASSWORD, SNOWFLAKE_ACCOUNT,
    SNOWFLAKE_WAREHOUSE, SNOWFLAKE_ROLE
"""

from __future__ import annotations

import logging
import os
from pathlib import Path

import snowflake.connector
from dotenv import load_dotenv

from pipeline.utils.logging_config import configure_logging

_SQL_DIR = Path(__file__).resolve().parent.parent / "snowflake"

_SCRIPT_ORDER: tuple[str, ...] = (
    "00_create_databases.sql",
    "01_create_stg_tables.sql",
    "06_create_tch_tables.sql",
)

load_dotenv()
configure_logging()
logger = logging.getLogger(__name__)


def connect_to_snowflake() -> snowflake.connector.SnowflakeConnection:
    """Establish a Snowflake connection from environment variables.

    Returns:
        An open Snowflake connection.

    Raises:
        snowflake.connector.errors.DatabaseError: If the connection cannot be
            established (bad credentials, unreachable account, etc.).
    """
    conn = snowflake.connector.connect(
        user=os.getenv("SNOWFLAKE_USER"),
        password=os.getenv("SNOWFLAKE_PASSWORD"),
        account=os.getenv("SNOWFLAKE_ACCOUNT"),
        warehouse=os.getenv("SNOWFLAKE_WAREHOUSE"),
        role=os.getenv("SNOWFLAKE_ROLE"),
    )
    logger.info("Connected to Snowflake.")
    return conn


def execute_sql_file(
    conn: snowflake.connector.SnowflakeConnection,
    file_path: Path,
) -> None:
    """Execute every statement in a SQL file against an open connection.

    Statements are split on semicolons; blank segments are skipped.

    Args:
        conn: Open Snowflake connection.
        file_path: Path to the .sql file to execute.

    Raises:
        snowflake.connector.errors.ProgrammingError: If any statement fails.
    """
    logger.info("Executing script: %s", file_path.name)
    sql_content = file_path.read_text(encoding="utf-8")

    statements = [stmt.strip() for stmt in sql_content.split(";") if stmt.strip()]

    with conn.cursor() as cursor:
        for i, stmt in enumerate(statements, start=1):
            cursor.execute(stmt)
            logger.info(
                "Statement %d/%d executed successfully in %s.",
                i,
                len(statements),
                file_path.name,
            )

    logger.info("Script completed: %s", file_path.name)


def run_installation() -> None:
    """Run all DDL scripts in order to install or refresh the SID schema.

    Iterates over ``_SCRIPT_ORDER`` and executes each SQL file. Raises
    immediately if a script file is missing — no silent skips.

    Raises:
        FileNotFoundError: If any expected SQL script is absent from
            ``_SQL_DIR``.
        snowflake.connector.errors.DatabaseError: If a Snowflake error occurs
            during execution.
    """
    logger.info("Starting SID installation.")

    for script_name in _SCRIPT_ORDER:
        script_path = _SQL_DIR / script_name
        if not script_path.exists():
            raise FileNotFoundError(f"Required SQL script not found: {script_path}")

    conn = connect_to_snowflake()
    try:
        for script_name in _SCRIPT_ORDER:
            execute_sql_file(conn, _SQL_DIR / script_name)
        logger.info("All scripts executed successfully.")
    finally:
        conn.close()
        logger.info("Snowflake connection closed.")


if __name__ == "__main__":
    run_installation()
