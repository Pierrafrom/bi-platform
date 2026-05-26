"""Tests for airflow.utils.source_reader.

Uses real batch data from inputs/Data Hospital/ — no mocks needed
since the files are committed to the repo.

Reference batch: 2026-04-29 (first available day).
"""

from __future__ import annotations

import logging
from datetime import date
from pathlib import Path

import pytest

from pipeline.utils.source_reader import (
    ALL_TABLES,
    EXPECTED_COLUMNS,
    BatchSummary,
    batch_file_path,
    batch_folder_path,
    read_batch,
    validate_all_tables,
    validate_batch,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

FIRST_BATCH = date(2026, 4, 29)


# ---------------------------------------------------------------------------
# Path helpers
# ---------------------------------------------------------------------------


class TestBatchFolderPath:
    """batch_folder_path() returns a deterministic path."""

    def test_returns_path_object(self) -> None:
        result = batch_folder_path(FIRST_BATCH)
        assert isinstance(result, Path)

    def test_folder_name_format(self) -> None:
        result = batch_folder_path(FIRST_BATCH)
        assert result.name == "BDD_HOSPITAL_20260429"

    def test_folder_exists_for_first_batch(self) -> None:
        assert batch_folder_path(FIRST_BATCH).is_dir()

    def test_folder_does_not_exist_for_future_date(self) -> None:
        assert not batch_folder_path(date(2099, 1, 1)).exists()


class TestBatchFilePath:
    """batch_file_path() returns the correct file path."""

    def test_filename_format(self) -> None:
        result = batch_file_path(FIRST_BATCH, "PATIENT")
        assert result.name == "PATIENT_20260429.txt"

    def test_file_exists_for_known_table(self) -> None:
        assert batch_file_path(FIRST_BATCH, "PATIENT").is_file()

    def test_file_inside_batch_folder(self) -> None:
        file_path = batch_file_path(FIRST_BATCH, "CONSULTATION")
        assert file_path.parent == batch_folder_path(FIRST_BATCH)


# ---------------------------------------------------------------------------
# read_batch()
# ---------------------------------------------------------------------------


class TestReadBatch:
    """read_batch() loads rows from a real source file."""

    def test_returns_non_empty_list(self) -> None:
        rows = read_batch(FIRST_BATCH, "PATIENT")
        assert len(rows) > 0

    def test_rows_are_dicts(self) -> None:
        rows = read_batch(FIRST_BATCH, "PATIENT")
        assert all(isinstance(row, dict) for row in rows)

    def test_patient_has_expected_columns(self) -> None:
        rows = read_batch(FIRST_BATCH, "PATIENT")
        assert set(EXPECTED_COLUMNS["PATIENT"]).issubset(set(rows[0].keys()))

    def test_patient_id_is_not_empty(self) -> None:
        rows = read_batch(FIRST_BATCH, "PATIENT")
        assert all(row["ID_PATIENT"] for row in rows)

    def test_raises_on_missing_file(self) -> None:
        with pytest.raises(FileNotFoundError):
            read_batch(date(2099, 1, 1), "PATIENT")

    def test_logs_row_count(self, caplog: pytest.LogCaptureFixture) -> None:
        with caplog.at_level(logging.INFO, logger="pipeline.utils.source_reader"):
            read_batch(FIRST_BATCH, "PATIENT")
        assert any("PATIENT" in msg for msg in caplog.messages)


# ---------------------------------------------------------------------------
# validate_batch()
# ---------------------------------------------------------------------------


class TestValidateBatch:
    """validate_batch() checks column structure against the contract."""

    @pytest.mark.parametrize("table", ALL_TABLES)
    def test_all_tables_pass_validation(self, table: str) -> None:
        """Every table in the first batch must have exactly the expected columns."""
        summary = validate_batch(FIRST_BATCH, table)
        assert summary.is_valid, str(summary)

    def test_returns_batch_summary(self) -> None:
        result = validate_batch(FIRST_BATCH, "CONSULTATION")
        assert isinstance(result, BatchSummary)

    def test_correct_batch_date_in_summary(self) -> None:
        summary = validate_batch(FIRST_BATCH, "PATIENT")
        assert summary.batch_date == FIRST_BATCH

    def test_correct_table_in_summary(self) -> None:
        summary = validate_batch(FIRST_BATCH, "PATIENT")
        assert summary.table == "PATIENT"

    def test_row_count_is_positive(self) -> None:
        summary = validate_batch(FIRST_BATCH, "PATIENT")
        assert summary.row_count > 0

    def test_raises_on_unknown_table(self) -> None:
        with pytest.raises(ValueError, match="Unknown table"):
            validate_batch(FIRST_BATCH, "NOT_A_TABLE")


# ---------------------------------------------------------------------------
# validate_all_tables()
# ---------------------------------------------------------------------------


class TestValidateAllTables:
    """validate_all_tables() validates every table in one call."""

    def test_returns_one_summary_per_table(self) -> None:
        summaries = validate_all_tables(FIRST_BATCH)
        assert len(summaries) == len(ALL_TABLES)

    def test_all_summaries_are_valid(self) -> None:
        summaries = validate_all_tables(FIRST_BATCH)
        failures = [str(s) for s in summaries if not s.is_valid]
        assert not failures, "Validation failures:\n" + "\n".join(failures)

    def test_tables_in_definition_order(self) -> None:
        summaries = validate_all_tables(FIRST_BATCH)
        assert [s.table for s in summaries] == list(ALL_TABLES)


# ---------------------------------------------------------------------------
# BatchSummary
# ---------------------------------------------------------------------------


class TestBatchSummary:
    """Unit tests for the BatchSummary dataclass."""

    def test_is_valid_when_no_discrepancies(self) -> None:
        s = BatchSummary(batch_date=FIRST_BATCH, table="PATIENT", row_count=100)
        assert s.is_valid

    def test_is_invalid_when_missing_columns(self) -> None:
        s = BatchSummary(
            batch_date=FIRST_BATCH,
            table="PATIENT",
            row_count=100,
            missing_columns=("ID_PATIENT",),
        )
        assert not s.is_valid

    def test_str_contains_ok_status(self) -> None:
        s = BatchSummary(batch_date=FIRST_BATCH, table="PATIENT", row_count=100)
        assert "[OK]" in str(s)

    def test_str_contains_invalid_status(self) -> None:
        s = BatchSummary(
            batch_date=FIRST_BATCH,
            table="PATIENT",
            row_count=0,
            missing_columns=("ID_PATIENT",),
        )
        assert "[INVALID]" in str(s)

    def test_str_mentions_row_count(self) -> None:
        s = BatchSummary(batch_date=FIRST_BATCH, table="PATIENT", row_count=42)
        assert "42" in str(s)
