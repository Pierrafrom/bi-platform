"""Centralised logging configuration for the bi-platform pipeline.

Configure once at the entry point of a DAG or script:

    from airflow.utils.logging_config import configure_logging
    configure_logging(level=logging.DEBUG)

Then in every module, just get the module logger:

    import logging
    logger = logging.getLogger(__name__)
"""

from __future__ import annotations

import logging
import sys
from typing import TextIO

# Log format — designed to be machine-parseable and human-readable:
#   2026-05-26 14:32:01,123 | INFO     | airflow.dags.load_staging | Loaded 643 rows into STAGING.PATIENT
_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def configure_logging(
    level: int = logging.INFO,
    stream: TextIO = sys.stdout,
    include_file: str | None = None,
) -> None:
    """Configure the root logger for the bi-platform pipeline.

    Call this exactly once, at the top of a DAG file or pipeline entry point.
    All child loggers (``logging.getLogger(__name__)``) inherit this config.

    Args:
        level: Minimum log level (e.g. ``logging.DEBUG``, ``logging.INFO``).
        stream: Output stream for the console handler (default: stdout).
        include_file: Optional path to a log file. If given, a FileHandler
            is added in addition to the stream handler.

    Example:
        >>> configure_logging(level=logging.DEBUG, include_file="/tmp/pipeline.log")
    """
    formatter = logging.Formatter(fmt=_FORMAT, datefmt=_DATE_FORMAT)

    handlers: list[logging.Handler] = [_make_stream_handler(stream, formatter)]

    if include_file is not None:
        handlers.append(_make_file_handler(include_file, formatter))

    logging.basicConfig(level=level, handlers=handlers, force=True)

    # Silence overly verbose third-party loggers
    for noisy in ("snowflake.connector", "urllib3", "botocore", "boto3"):
        logging.getLogger(noisy).setLevel(logging.WARNING)


def _make_stream_handler(stream: TextIO, formatter: logging.Formatter) -> logging.StreamHandler:  # type: ignore[type-arg]
    """Create a stream handler with the given formatter.

    Args:
        stream: Target output stream.
        formatter: Log record formatter.

    Returns:
        Configured StreamHandler.
    """
    handler: logging.StreamHandler[TextIO] = logging.StreamHandler(stream)
    handler.setFormatter(formatter)
    return handler


def _make_file_handler(path: str, formatter: logging.Formatter) -> logging.FileHandler:
    """Create a rotating-friendly file handler.

    Args:
        path: Absolute or relative path to the log file. Parent directory must exist.
        formatter: Log record formatter.

    Returns:
        Configured FileHandler (append mode).
    """
    handler = logging.FileHandler(path, encoding="utf-8")
    handler.setFormatter(formatter)
    return handler
