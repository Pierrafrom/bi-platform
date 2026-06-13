"""Installation DAG — runs install_sid.py once to set up the SID schema.

This DAG is triggered manually (no schedule) and must be run exactly once
at deployment time, before any daily pipeline run.

It executes the four DDL scripts in order:
    1. 00_create_databases.sql — databases, schemas, warehouses
    2. 01_create_stg_tables.sql — STG tables (recreated)
    3. 02_create_soc_tables.sql — SOC tables (CREATE IF NOT EXISTS)
    4. 06_create_tch_tables.sql — TCH tracking tables (CREATE IF NOT EXISTS)

A T_SUIV_RUN tracking row is inserted with RUN_TYP='INSTALL' and closed
with OK or KO depending on the outcome.

Snowflake credentials are read from environment variables:
    SNOWFLAKE_USER, SNOWFLAKE_PASSWORD, SNOWFLAKE_ACCOUNT,
    SNOWFLAKE_WAREHOUSE, SNOWFLAKE_ROLE, SNOWFLAKE_DATABASE
"""

from __future__ import annotations

import logging
import os
from datetime import datetime

import snowflake.connector
from airflow.decorators import dag, task
from airflow.utils.state import TaskInstanceState
from airflow.utils.trigger_rule import TriggerRule

from pipeline.install_sid import run_installation
from pipeline.utils.logging_config import configure_logging

logger = logging.getLogger(__name__)

_DATABASE = os.getenv("SNOWFLAKE_DATABASE", "HOPITAL_DW")
_TCH_SCHEMA = "TCH"
_LOG_FILE = os.path.join(
    os.getenv("PIPELINE_LOG_DIR", "/opt/airflow/logs/pipeline"),
    "install.log",
)


def _get_snowflake_connection() -> snowflake.connector.SnowflakeConnection:
    """Open a Snowflake connection from environment variables.

    Returns:
        An open Snowflake connection targeting the TCH schema.
    """
    return snowflake.connector.connect(
        user=os.getenv("SNOWFLAKE_USER"),
        password=os.getenv("SNOWFLAKE_PASSWORD"),
        account=os.getenv("SNOWFLAKE_ACCOUNT"),
        warehouse=os.getenv("SNOWFLAKE_WAREHOUSE"),
        role=os.getenv("SNOWFLAKE_ROLE"),
        database=_DATABASE,
        schema=_TCH_SCHEMA,
    )


@dag(
    dag_id="install_sid",
    schedule=None,
    start_date=datetime(2026, 1, 1),
    catchup=False,
    tags=["install", "sid"],
    default_args={
        "retries": 0,
        "depends_on_past": False,
    },
    doc_md="""
    ## Installation SID

    Triggered manually. Runs the four DDL scripts to initialise the Snowflake
    schema (databases, STG tables, SOC tables, TCH tracking tables).

    **Run once at deployment — idempotent but not reversible.**
    """,
)
def install_sid_dag() -> None:
    """Wire the installation tasks together."""

    @task(task_id="start_run")
    def start_run() -> int:
        """Insert a T_SUIV_RUN row with RUN_TYP='INSTALL' and status ENC.

        Returns:
            The generated RUN_ID.
        """
        configure_logging(include_file=_LOG_FILE)
        logger.info("Starting SID installation run.")

        conn = _get_snowflake_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO TCH.T_SUIV_RUN
                        (RUN_STRT_DTTM, RUN_STTS_CD, RUN_TYP)
                    VALUES
                        (CURRENT_TIMESTAMP(), 'ENC', 'INSTALL')
                    """
                )
                cur.execute('SELECT "RUN_ID" FROM TABLE(RESULT_SCAN(LAST_QUERY_ID()))')
                row = cur.fetchone()
                run_id: int = row[0] or 0
            conn.commit()
        finally:
            conn.close()

        logger.info("Installation run opened: run_id=%d", run_id)
        return run_id

    @task(task_id="install_sid")
    def install_sid_task(run_id: int) -> None:
        """Execute install_sid.run_installation() and track in T_SUIV_TRMT.

        Args:
            run_id: Parent RUN_ID from T_SUIV_RUN.
        """
        configure_logging(include_file=_LOG_FILE)
        logger.info("Running SID installation for run_id=%d", run_id)

        conn = _get_snowflake_connection()
        exec_id: int = 0
        status = "KO"
        err_msg: str | None = None

        try:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO TCH.T_SUIV_TRMT
                        (RUN_ID, SCRPT_NAME, EXEC_STRT_DTTM, EXEC_STTS_CD)
                    VALUES
                        (%s, 'install_sid', CURRENT_TIMESTAMP(), 'ENC')
                    """,
                    (run_id,),
                )
                cur.execute('SELECT "EXEC_ID" FROM TABLE(RESULT_SCAN(LAST_QUERY_ID()))')
                row = cur.fetchone()
                exec_id = row[0] or 0
            conn.commit()
        finally:
            conn.close()

        try:
            run_installation()
            status = "OK"
            logger.info("SID installation succeeded.")
        except Exception as exc:
            err_msg = str(exc)
            logger.error("SID installation failed: %s", exc)
            raise
        finally:
            try:
                conn2 = _get_snowflake_connection()
                try:
                    with conn2.cursor() as cur:
                        cur.execute(
                            """
                            UPDATE TCH.T_SUIV_TRMT
                            SET EXEC_END_DTTM = CURRENT_TIMESTAMP(),
                                EXEC_STTS_CD  = %s,
                                ERR_MSG       = %s
                            WHERE EXEC_ID = %s
                            """,
                            (status, err_msg, exec_id),
                        )
                    conn2.commit()
                finally:
                    conn2.close()
            except Exception as tracking_exc:
                logger.warning("Failed to update T_SUIV_TRMT tracking: %s", tracking_exc)

    @task(task_id="end_run", trigger_rule=TriggerRule.ALL_DONE)
    def end_run(run_id: int, **context: object) -> None:
        """Close the T_SUIV_RUN row with OK or KO.

        Args:
            run_id: RUN_ID of the row to close.
            **context: Airflow context dictionary.
        """
        configure_logging(include_file=_LOG_FILE)
        final_status = "KO"
        dag_run = context.get("dag_run")
        if dag_run is not None:
            for task_instance in dag_run.get_task_instances():
                if task_instance.task_id == "install_sid" and task_instance.state in (
                    "success",
                    TaskInstanceState.SUCCESS,
                ):
                    final_status = "OK"
                    break

        logger.info("Closing installation run_id=%d with status=%s", run_id, final_status)

        conn = _get_snowflake_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE TCH.T_SUIV_RUN
                    SET RUN_END_DTTM = CURRENT_TIMESTAMP(),
                        RUN_STTS_CD  = %s
                    WHERE RUN_ID = %s
                    """,
                    (final_status, run_id),
                )
            conn.commit()
        finally:
            conn.close()

        logger.info("Installation run closed: run_id=%d status=%s", run_id, final_status)

    run_id = start_run()
    install = install_sid_task(run_id)
    install >> end_run(run_id)


install_sid_dag()
