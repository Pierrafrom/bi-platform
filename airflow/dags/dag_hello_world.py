"""Hello-world DAG — validates the full stack configuration.

Reads all 7 source tables from the most recent available batch, validates
their column structure, and logs a summary. No data is written anywhere.

Trigger: manual only (schedule=None).
"""

from __future__ import annotations

import logging
from datetime import date, timedelta

from airflow.decorators import dag, task

from pipeline.utils.logging_config import configure_logging
from pipeline.utils.source_reader import validate_all_tables

logger = logging.getLogger(__name__)

_HELLO_WORLD_BATCH = date(2026, 4, 29)


@dag(
    dag_id="hello_world",
    schedule=None,
    start_date=date(2026, 5, 21),  # type: ignore[arg-type]
    catchup=False,
    tags=["hello-world", "staging"],
    default_args={
        "retries": 1,
        "retry_delay": timedelta(minutes=5),
        "depends_on_past": False,
    },
    doc_md="""
    ## Hello World DAG

    Validates the bi-platform stack configuration end-to-end:

    1. **validate_sources** — reads all 7 hospital source tables from the first
       available batch (2026-04-29) and checks column structure against the
       expected schema contract.
    2. **log_summary** — logs a pass/fail summary for each table.

    No data is written. Safe to run at any time.
    """,
)
def hello_world_dag() -> None:
    """Entry point — wires the two tasks together."""

    @task(task_id="validate_sources")
    def validate_sources() -> list[dict[str, object]]:
        """Read and validate all source tables for the reference batch.

        Returns:
            List of serialisable dicts representing each BatchSummary.
        """
        configure_logging()
        logger.info("Starting source validation for batch %s", _HELLO_WORLD_BATCH)

        summaries = validate_all_tables(_HELLO_WORLD_BATCH)
        return [
            {
                "table": s.table,
                "batch_date": str(s.batch_date),
                "row_count": s.row_count,
                "is_valid": s.is_valid,
                "missing_columns": list(s.missing_columns),
                "extra_columns": list(s.extra_columns),
            }
            for s in summaries
        ]

    @task(task_id="log_summary")
    def log_summary(results: list[dict[str, object]]) -> None:
        """Log a human-readable pass/fail report for each table.

        Args:
            results: Serialised BatchSummary dicts from validate_sources.
        """
        configure_logging()
        passed = [r for r in results if r["is_valid"]]
        failed = [r for r in results if not r["is_valid"]]

        logger.info("=" * 60)
        logger.info("Hello-world validation report — batch %s", _HELLO_WORLD_BATCH)
        logger.info("=" * 60)

        for r in results:
            status = "OK  " if r["is_valid"] else "FAIL"
            logger.info("[%s] %-20s %d rows", status, r["table"], r["row_count"])

        logger.info("-" * 60)
        logger.info("Result: %d/%d tables passed", len(passed), len(results))

        if failed:
            for r in failed:
                logger.warning(
                    "FAIL %s — missing=%s extra=%s",
                    r["table"],
                    r["missing_columns"],
                    r["extra_columns"],
                )

    summaries = validate_sources()
    log_summary(summaries)


hello_world_dag()
