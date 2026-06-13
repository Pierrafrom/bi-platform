"""Daily hospital data pipeline DAG.

Orchestrates the full ETL chain for one batch date:

    start_run      — inserts a T_SUIV_RUN tracking row (status ENC) and
                     returns the generated RUN_ID via XCom.
        │
        ├── ingest_stg — loads all seven STG tables from flat files; wraps
        │                the execution in a T_SUIV_TRMT tracking row.
        │
        ├── dbt_run    — runs all dbt models for the batch date.
        │
        └── dbt_test   — runs all dbt data tests.

    end_run        — updates T_SUIV_RUN to OK or KO depending on upstream
                     task outcomes; always runs (trigger_rule=ALL_DONE).

Snowflake credentials are read from environment variables:
    SNOWFLAKE_USER, SNOWFLAKE_PASSWORD, SNOWFLAKE_ACCOUNT,
    SNOWFLAKE_WAREHOUSE, SNOWFLAKE_ROLE, SNOWFLAKE_DATABASE

The dbt project directory defaults to /opt/airflow/dbt but can be
overridden with the DBT_PROJECT_DIR environment variable.
"""

from __future__ import annotations

import logging
import os
from datetime import datetime, timedelta

import snowflake.connector
from airflow.decorators import dag, task
from airflow.operators.bash import BashOperator
from airflow.utils.state import TaskInstanceState
from airflow.utils.trigger_rule import TriggerRule

from pipeline.ingest.ingest_stg import ingest_batch
from pipeline.utils.logging_config import configure_logging

logger = logging.getLogger(__name__)

_DBT_DIR = os.getenv("DBT_PROJECT_DIR", "/opt/airflow/dbt")
_DATABASE = os.getenv("SNOWFLAKE_DATABASE", "HOPITAL_DW")
_TCH_SCHEMA = "TCH"

# Log file path — configurable via PIPELINE_LOG_DIR (must exist at runtime).
_LOG_FILE = os.path.join(
    os.getenv("PIPELINE_LOG_DIR", "/opt/airflow/logs/pipeline"),
    "daily_pipeline.log",
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
    dag_id="daily_pipeline",
    schedule="@daily",
    start_date=datetime(2026, 4, 29),
    catchup=False,
    tags=["pipeline", "staging", "dbt"],
    default_args={
        "retries": 1,
        "retry_delay": timedelta(minutes=5),
        "depends_on_past": False,
    },
    doc_md="""
    ## Daily Hospital Pipeline

    Runs the full ETL chain for one batch date:

    1. **start_run** — opens a tracking row in ``TCH.T_SUIV_RUN`` (status ENC).
    2. **ingest_stg** — loads all seven hospital source files into ``STG`` tables.
    3. **dbt_run** — transforms STG data through Travail and Socle layers.
    4. **dbt_test** — runs dbt data quality tests.
    5. **end_run** — closes the tracking row with OK or KO.
    """,
)
def daily_pipeline_dag() -> None:
    """Wire the pipeline tasks together."""

    @task(task_id="start_run")
    def start_run(ds: str | None = None) -> int:
        """Insert a T_SUIV_RUN row with status ENC and return the RUN_ID.

        Args:
            ds: Airflow logical date (YYYY-MM-DD), injected automatically.

        Returns:
            The generated RUN_ID (IDENTITY column value).
        """
        configure_logging(include_file=_LOG_FILE)
        logger.info("Opening tracking run for batch_date=%s", ds)

        conn = _get_snowflake_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO TCH.T_SUIV_RUN
                        (RUN_STRT_DTTM, RUN_STTS_CD, RUN_TYP, BATCH_DT)
                    VALUES
                        (CURRENT_TIMESTAMP(), 'ENC', 'DAILY', %s::DATE)
                    """,
                    (ds,),
                )
                cur.execute("SELECT MAX(RUN_ID) FROM TCH.T_SUIV_RUN")
                row = cur.fetchone()
                run_id: int = row[0] if row else 0
            conn.commit()
        finally:
            conn.close()

        logger.info("Tracking run started: run_id=%d", run_id)
        return run_id

    @task(task_id="ingest_stg")
    def ingest_stg_task(run_id: int, ds: str | None = None) -> int:
        """Load all STG tables and record the execution in T_SUIV_TRMT.

        Args:
            run_id: Parent RUN_ID from T_SUIV_RUN.
            ds: Airflow logical date (YYYY-MM-DD), injected automatically.

        Returns:
            The generated EXEC_ID from T_SUIV_TRMT.
        """
        configure_logging(include_file=_LOG_FILE)
        logger.info("Starting STG ingestion for batch_date=%s run_id=%d", ds, run_id)

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
                        (%s, 'ingest_stg', CURRENT_TIMESTAMP(), 'ENC')
                    """,
                    (run_id,),
                )
                cur.execute("SELECT MAX(EXEC_ID) FROM TCH.T_SUIV_TRMT")
                row = cur.fetchone()
                exec_id = row[0] if row else 0
            conn.commit()
        finally:
            conn.close()

        try:
            from datetime import date as _date

            batch_date = _date.fromisoformat(ds) if ds else _date.today()
            ingest_batch(batch_date)
            status = "OK"
            logger.info("STG ingestion succeeded for batch_date=%s", ds)
        except Exception as exc:
            err_msg = str(exc)
            logger.error("STG ingestion failed for batch_date=%s: %s", ds, exc)
            raise
        finally:
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

        return exec_id

    @task(task_id="end_run", trigger_rule=TriggerRule.ALL_DONE)
    def end_run(run_id: int, **context: object) -> None:
        """Update T_SUIV_RUN with the final status (OK or KO).

        Inspects the upstream task states to determine the outcome.

        Args:
            run_id: RUN_ID of the row to close.
            **context: Airflow context dictionary (injected automatically).
        """
        configure_logging(include_file=_LOG_FILE)
        ti = context["ti"]

        upstream_states = ti.xcom_pull(task_ids=["ingest_stg", "dbt_run", "dbt_test"])
        failed = any(s is None for s in upstream_states)

        # Also check task instance states for bash operators (they push nothing on failure)
        dag_run = context.get("dag_run")
        if dag_run is not None:
            for task_instance in dag_run.get_task_instances():
                if task_instance.task_id in ("dbt_run", "dbt_test") and task_instance.state not in (
                    "success",
                    TaskInstanceState.SUCCESS,
                ):
                    failed = True
                    break

        final_status = "KO" if failed else "OK"
        logger.info("Closing run_id=%d with status=%s", run_id, final_status)

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

        logger.info("Run closed: run_id=%d status=%s", run_id, final_status)

    run_id = start_run()
    exec_id = ingest_stg_task(run_id)

    _dbt_run_vars = (
        '\'{"batch_date": "{{ ds }}", "exec_id": {{ ti.xcom_pull(task_ids=\'ingest_stg\') }}}\''
    )
    dbt_run = BashOperator(
        task_id="dbt_run",
        bash_command="cd {{ params.dbt_dir }} && dbt run --vars " + _dbt_run_vars,
        params={"dbt_dir": _DBT_DIR},
    )

    dbt_test = BashOperator(
        task_id="dbt_test",
        bash_command="cd {{ params.dbt_dir }} && dbt test",
        params={"dbt_dir": _DBT_DIR},
    )

    end_run_task = end_run.override(trigger_rule=TriggerRule.ALL_DONE)(run_id)

    exec_id >> dbt_run >> dbt_test >> end_run_task


daily_pipeline_dag()
